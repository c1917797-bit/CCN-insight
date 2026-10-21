(() => {
  'use strict';

  const cache = new Map();
  const latestTimes = new Map();
  const pageCache = new Map();
  const pageCacheMaxEntries = 64;
  const pageCacheMaxBytes = 4 * 1024 * 1024;
  let pageCacheBytes = 0;
  function removeCachedPage(key) {
    const entry = pageCache.get(key);
    if (!entry) return;
    pageCacheBytes -= entry.bytes;
    pageCache.delete(key);
  }
  function trimPageCache() {
    while (pageCache.size > pageCacheMaxEntries || pageCacheBytes > pageCacheMaxBytes) {
      removeCachedPage(pageCache.keys().next().value);
    }
  }
  const queries = new Map();
  const latestTtl = 30000;
  function expireLatest(key) {
    if (Date.now() - (latestTimes.get(key) || 0) >= latestTtl) cache.delete(key);
    if (!cache.has(key)) latestTimes.set(key, Date.now());
  }
  function queryOnce(key, read) {
    if (queries.has(key)) {
      const value = queries.get(key);
      queries.delete(key);
      queries.set(key, value);
      return value;
    }
    let request;
    request = Promise.resolve().then(read).then(result => {
      if ((result.records?.length > 1000 || JSON.stringify(result.records || []).length > 262144) && queries.get(key) === request) queries.delete(key);
      return result;
    }).catch(error => {
      if (queries.get(key) === request) queries.delete(key);
      throw error;
    });
    queries.set(key, request);
    while (queries.size > 128) queries.delete(queries.keys().next().value);
    return request;
  }
  async function mapBounded(values, read) {
    const results = new Array(values.length);
    let next = 0;
    let failed = false;
    async function worker() {
      while (!failed && next < values.length) {
        const index = next++;
        try {
          results[index] = await read(values[index]);
        } catch (error) {
          failed = true;
          throw error;
        }
      }
    }
    // Refill each free slot immediately instead of waiting for a whole wave.
    // Index assignment retains input order; a failure stops queued work.
    await Promise.all(Array.from({length: Math.min(4, values.length)}, worker));
    return results;
  }
  const sources = new Map();
  const contentTables = new Set([
    'contents',
    'content_identifiers',
    'content_locations',
    'resource_contents',
    'match_contents',
  ]);

  async function readJson(url, options = {}) {
    if (globalThis.LRICloudTableRead && new URL(url, location.href).pathname.startsWith('/__mcpgit/tables/')) return globalThis.LRICloudTableRead(url, options);
    const response = await fetch(url, options);
    if (!response.ok) throw new Error(`${new URL(url, location.href).pathname} load failed: ${response.status}`);
    const contentType = response.headers?.get?.('content-type') || '';
    if (contentType && !/^application\/(?:[a-z0-9.+-]*\+)?json(?:\s*;|$)/i.test(contentType)) {
      throw new Error(`${new URL(url, location.href).pathname} expected JSON, received ${contentType}`);
    }
    return response.json();
  }

  function revisionMismatch(expected, actual) {
    const error = new Error(`Hosted Table revision mismatch: expected ${expected}, received ${actual || '<missing>'}`);
    error.code = 'revision_mismatch';
    return error;
  }

  async function readHostedRows(table, {filterField = '', filterValue = '', expectedRevision = ''} = {}) {
    const endpoint = `/__mcpgit/tables/${encodeURIComponent(table)}`;
    const metadata = await readJson(endpoint + (expectedRevision ? `?expected_revision=${encodeURIComponent(expectedRevision)}` : ''));
    if (metadata.schema !== 'mcpgit/hosted-table/v1' || metadata.table !== table) {
      throw new Error(`invalid Hosted Table metadata: ${table}`);
    }
    const revision = metadata.status?.revision || metadata.revision || '';
    if (!revision) throw revisionMismatch(expectedRevision || '<required>', revision);
    if (expectedRevision && revision !== expectedRevision) throw revisionMismatch(expectedRevision, revision);
    if (filterField && !Array.isArray(metadata.filter_fields)) {
      throw new Error(`Hosted Table does not declare filter fields: ${table}`);
    }
    if (filterField && !metadata.filter_fields.includes(filterField)) {
      throw new Error(`Hosted Table filter is not enabled: ${table}/${filterField}`);
    }
    const limit = Math.max(1, Math.min(Number(metadata.max_rows) || 100, 200));
    const rows = [];
    // Only existing compact read models may use bounded concurrent snapshot reads.
    // Canonical Resources, evidence and Content keep their scoped/lazy contracts.
    const compactTables = new Set(['resource_catalog', 'resource_catalog_facets', 'challenge_catalog', 'challenge_catalog_facets']);
    const expectedRows = metadata.status?.row_count;
    const concurrent = !filterField && compactTables.has(table) &&
      Number.isSafeInteger(expectedRows) && expectedRows > 0 && expectedRows <= 20000 &&
      Number(metadata.status?.deleted_count || 0) === 0;
    let offset = 0;
    if (concurrent) {
      const offsets = Array.from({length: Math.ceil(expectedRows / limit)}, (_, i) => i * limit);
      for (let start = 0; start < offsets.length; start += 4) {
        const batch = await Promise.all(offsets.slice(start, start + 4).map(async (pageOffset) => {
          const params = new URLSearchParams({offset: String(pageOffset), limit: String(limit)});
          const page = await readJson(`${endpoint}/rows?${params}`);
          if (page.revision !== revision) throw revisionMismatch(revision, page.revision);
          const expectedLength = Math.min(limit, expectedRows - pageOffset);
          if (!Array.isArray(page.rows) || page.rows.length !== expectedLength ||
              Boolean(page.truncated) !== (pageOffset + expectedLength < expectedRows)) {
            throw new Error(`incomplete compact Hosted Table page: ${table}/${pageOffset}`);
          }
          return page.rows;
        }));
        for (const pageRows of batch) rows.push(...pageRows);
      }
    } else for (;;) {
      const params = new URLSearchParams({offset: String(offset), limit: String(limit)});
      if (filterField) {
        params.set('filter_field', filterField);
        params.set('filter_value', filterValue);
      }
      const page = await readJson(`${endpoint}/rows?${params}`);
      if (!Array.isArray(page.rows)) throw new Error(`invalid Hosted Table page: ${table}`);
      if (page.revision !== revision) throw revisionMismatch(revision, page.revision || '');
      rows.push(...page.rows);
      if (!page.truncated) break;
      if (!page.rows.length) throw new Error(`Hosted Table pagination stalled: ${table}`);
      offset += page.rows.length;
    }
    const keys = new Set();
    const records = [];
    for (const envelope of rows) {
      if (!envelope || typeof envelope.key !== 'string') throw new Error(`invalid Hosted Table row: ${table}`);
      if (keys.has(envelope.key)) throw new Error(`duplicate Hosted Table key: ${table}/${envelope.key}`);
      keys.add(envelope.key);
      if (envelope.deleted) continue;
      if (!Object.prototype.hasOwnProperty.call(envelope, 'row') || envelope.row === null || typeof envelope.row !== 'object') {
        throw new Error(`missing Hosted Table row payload: ${table}/${envelope.key}`);
      }
      records.push(envelope.row);
    }
    const confirmed = await readJson(endpoint + `?expected_revision=${encodeURIComponent(revision)}`);
    const confirmedRevision = confirmed.status?.revision || confirmed.revision || '';
    if (confirmedRevision !== revision) throw revisionMismatch(revision, confirmedRevision);
    return {metadata, records};
  }

  async function readHostedRowsByValues(table, filterField, filterValues, expectedRevision) {
    const values = [...new Set((filterValues || []).filter(value => typeof value === 'string' && value))].sort();
    if (!values.length) return {metadata: null, records: []};
    if (typeof expectedRevision !== 'string' || !expectedRevision) {
      throw revisionMismatch('<required>', expectedRevision);
    }
    const endpoint = `/__mcpgit/tables/${encodeURIComponent(table)}/rows/by-values`;
    const batches = [];
    for (let offset = 0; offset < values.length; offset += 100) batches.push(values.slice(offset, offset + 100));
    const keys = new Set();
    const pages = await mapBounded(batches, async batch => {
      const requested = new Set(batch);
      const records = [];
      let offset = 0;
      for (;;) {
        const page = await readJson(endpoint, {
          method: 'POST',
          headers: {'content-type': 'application/json'},
          body: JSON.stringify({
            expected_revision: expectedRevision,
            filter_field: filterField,
            filter_values: batch,
            offset,
            limit: 100,
          }),
        });
        if (!Array.isArray(page.rows) || page.rows.length > 100) throw new Error(`invalid Hosted Table multi-value page: ${table}`);
        if (page.revision !== expectedRevision) throw revisionMismatch(expectedRevision, page.revision || '');
        // Validate before another page or queued batch can start. Shared key
        // accounting catches duplicates across both pages and filter batches.
        for (const envelope of page.rows) {
          if (!envelope || typeof envelope.key !== 'string') throw new Error(`invalid Hosted Table row: ${table}`);
          if (keys.has(envelope.key)) throw new Error(`duplicate Hosted Table key: ${table}/${envelope.key}`);
          if (envelope.deleted) throw new Error(`unexpected deleted Hosted Table multi-value row: ${table}/${envelope.key}`);
          if (!Object.prototype.hasOwnProperty.call(envelope, 'row') || envelope.row === null || typeof envelope.row !== 'object') {
            throw new Error(`missing Hosted Table row payload: ${table}/${envelope.key}`);
          }
          if (!requested.has(envelope.row[filterField])) throw new Error(`Hosted Table multi-value row escaped its filter: ${table}/${envelope.key}`);
          keys.add(envelope.key);
          records.push(envelope.row);
        }
        if (!page.truncated) break;
        if (!page.rows.length) throw new Error(`Hosted Table multi-value pagination stalled: ${table}`);
        offset += page.rows.length;
      }
      return records;
    });
    const records = pages.flat();
    return {
      metadata: {table, status: {revision: expectedRevision}, by_values: true, max_filter_values: 100},
      records,
    };
  }

  async function readHostedRowsByKeys(table, rowKeys, expectedRevision, select = null) {
    const keys = [...new Set((rowKeys || []).filter(key => typeof key === 'string' && key))].sort();
    if (!keys.length) return {metadata: null, records: []};
    if (typeof expectedRevision !== 'string' || !expectedRevision) {
      throw revisionMismatch('<required>', expectedRevision);
    }
    if (select !== null && (!Array.isArray(select) || !select.every(field => typeof field === 'string' && field))) {
      throw new Error(`Hosted Table exact-row select is invalid: ${table}`);
    }
    const endpoint = `/__mcpgit/tables/${encodeURIComponent(table)}/rows/get`;
    const batches = [];
    for (let offset = 0; offset < keys.length; offset += 100) batches.push(keys.slice(offset, offset + 100));
    const pages = await mapBounded(batches, async batch => {
      const payload = await readJson(endpoint, {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify({keys: batch, expected_revision: expectedRevision, ...(select ? {select} : {})}),
      });
      // Validate before the worker refills its slot, not after every batch ends.
      if (!payload || payload.revision !== expectedRevision) {
        throw revisionMismatch(expectedRevision, payload?.revision || '');
      }
      if (!Array.isArray(payload.rows) || !Array.isArray(payload.missing_keys) || !Array.isArray(payload.excluded_deleted_keys)) {
        throw new Error(`invalid Hosted Table exact-row response: ${table}`);
      }
      if (payload.requested_count !== batch.length || payload.returned_count !== payload.rows.length) {
        throw new Error(`invalid Hosted Table exact-row counts: ${table}`);
      }
      const requested = new Set(batch);
      const accounted = new Set();
      const records = [];
      function account(key) {
        if (typeof key !== 'string' || !requested.has(key)) throw new Error(`invalid Hosted Table exact row: ${table}`);
        if (accounted.has(key)) throw new Error(`duplicate Hosted Table key accounting: ${table}/${key}`);
        accounted.add(key);
      }
      for (const envelope of payload.rows) {
        if (!envelope) throw new Error(`invalid Hosted Table exact row: ${table}`);
        account(envelope.key);
        if (envelope.deleted) throw new Error(`unexpected deleted Hosted Table exact row: ${table}/${envelope.key}`);
        if (!Object.prototype.hasOwnProperty.call(envelope, 'row') || envelope.row === null || typeof envelope.row !== 'object') {
          throw new Error(`missing Hosted Table row payload: ${table}/${envelope.key}`);
        }
        records.push(envelope.row);
      }
      for (const key of [...payload.missing_keys, ...payload.excluded_deleted_keys]) account(key);
      for (const key of batch) {
        if (!accounted.has(key)) throw new Error(`Hosted Table exact-row key is unaccounted: ${table}/${key}`);
      }
      return records;
    });
    const records = pages.flat();
    return {metadata: {table, status: {revision: expectedRevision}, exact_rows: true}, records};
  }

  function readPageMetadata(table, expectedRevision) {
    const read = async () => {
      const metadata = await readJson(`/__mcpgit/tables/${encodeURIComponent(table)}` + (expectedRevision ? `?expected_revision=${encodeURIComponent(expectedRevision)}` : ''));
      if (metadata.schema !== 'mcpgit/hosted-table/v1' || metadata.table !== table) {
        throw new Error(`invalid Hosted Table metadata: ${table}`);
      }
      const revision = metadata.status?.revision || metadata.revision || '';
      if (!revision || (expectedRevision && revision !== expectedRevision)) {
        throw revisionMismatch(expectedRevision || '<required>', revision);
      }
      return metadata;
    };
    // Reuse only a validated definition at an explicit revision, in the bounded
    // query cache. Latest reads still obtain fresh metadata; rows verify revision.
    return expectedRevision ? queryOnce(JSON.stringify(['page-metadata', table, expectedRevision]), read) : read();
  }

  async function readHostedPage(table, {offset = 0, limit = 50, filterField = '', filterValue = '', expectedRevision = ''} = {}) {
    const endpoint = `/__mcpgit/tables/${encodeURIComponent(table)}`;
    // Native queries return definition and scoped rows in one revision-bound response.
    // Validate both through the existing Hosted Table page contract below.
    const combined = globalThis.LRICloudTableReadPage
      ? await globalThis.LRICloudTableReadPage(table, {offset,limit,filterField,filterValue,expectedRevision}) : null;
    const metadata = combined?.metadata || await readPageMetadata(table, expectedRevision);
    if (metadata.schema !== 'mcpgit/hosted-table/v1' || metadata.table !== table) {
      throw new Error(`invalid Hosted Table metadata: ${table}`);
    }
    const revision = metadata.status?.revision || metadata.revision || '';
    if (expectedRevision && revision !== expectedRevision) throw revisionMismatch(expectedRevision, revision);
    if (filterField && (!Array.isArray(metadata.filter_fields) || !metadata.filter_fields.includes(filterField))) {
      throw new Error(`Hosted Table filter is not enabled: ${table}/${filterField}`);
    }
    const boundedLimit = Math.max(1, Math.min(Number(limit) || 50, Number(metadata.max_rows) || 200, 200));
    const boundedOffset = Math.max(0, Number(offset) || 0);
    const params = new URLSearchParams({offset: String(boundedOffset), limit: String(boundedLimit), expected_revision: revision});
    if (filterField) {
      params.set('filter_field', filterField);
      params.set('filter_value', filterValue);
    }
    const page = combined?.page || await readJson(`${endpoint}/rows?${params}`);
    if (!Array.isArray(page.rows) || page.rows.length > boundedLimit) throw new Error(`invalid Hosted Table page: ${table}`);
    if (page.truncated && !page.rows.length) throw new Error(`Hosted Table pagination stalled: ${table}`);
    if (page.revision !== revision) throw revisionMismatch(revision, page.revision);
    const keys = new Set();
    const records = [];
    for (const envelope of page.rows) {
      if (!envelope || typeof envelope.key !== 'string') throw new Error(`invalid Hosted Table row: ${table}`);
      if (keys.has(envelope.key)) throw new Error(`duplicate Hosted Table key: ${table}/${envelope.key}`);
      keys.add(envelope.key);
      if (envelope.deleted) continue;
      if (!Object.prototype.hasOwnProperty.call(envelope, 'row') || envelope.row === null || typeof envelope.row !== 'object') {
        throw new Error(`missing Hosted Table row payload: ${table}/${envelope.key}`);
      }
      records.push(envelope.row);
    }
    const total = Number(page.matched_count ?? page.total ?? page.row_count ?? metadata.status?.row_count ?? metadata.row_count ?? 0);
    if (!Number.isSafeInteger(total) || total < 0) throw new Error(`invalid Hosted Table page count: ${table}`);
    return {
      metadata,
      records,
      revision,
      offset: boundedOffset,
      limit: boundedLimit,
      truncated: Boolean(page.truncated),
      nextOffset: page.truncated ? boundedOffset + page.rows.length : null,
      total,
    };
  }

  function loadTablePage(table, options = {}) {
    if (contentTables.has(table)) {
      return Promise.reject(new Error(`paged Content table access is forbidden: ${table}`));
    }
    const normalized = {
      offset: Math.max(0, Number(options.offset) || 0),
      limit: Math.max(1, Math.min(Number(options.limit) || 50, 200)),
      filterField: typeof options.filterField === 'string' ? options.filterField : '',
      filterValue: typeof options.filterValue === 'string' ? options.filterValue : '',
      expectedRevision: typeof options.expectedRevision === 'string' ? options.expectedRevision : '',
    };
    const key = JSON.stringify(['page', table, normalized.offset, normalized.limit, normalized.filterField, normalized.filterValue, normalized.expectedRevision]);
    const existing = pageCache.get(key);
    if (existing && !normalized.expectedRevision && Date.now() - existing.createdAt >= latestTtl) removeCachedPage(key);
    if (pageCache.has(key)) {
      const entry = pageCache.get(key);
      pageCache.delete(key);
      pageCache.set(key, entry);
      return entry.promise;
    }
    const entry = {createdAt: Date.now(), bytes: 0, promise: null};
    {
      let request;
      request = readHostedPage(table, normalized).then((page) => {
        if (pageCache.get(key) === entry) sources.set(table, {kind: 'tablegit', revision: page.revision, rows: page.records.length, paged: true});
        return {
          schema: 'lri.tablegit-page/v1',
          generated_from: `tablegit:${table}`,
          count: page.records.length,
          records: page.records,
          tablegit: page.metadata,
          revision: page.revision,
          page: {
            offset: page.offset,
            limit: page.limit,
            truncated: page.truncated,
            nextOffset: page.nextOffset,
            total: page.total,
          },
        };
      }).then((result) => {
        if (pageCache.get(key) === entry) {
          // A conservative serialized UTF-16 budget, not a measurement of heap size.
          entry.bytes = JSON.stringify(result).length * 2;
          pageCacheBytes += entry.bytes;
          if (entry.bytes > pageCacheMaxBytes) removeCachedPage(key);
          else trimPageCache();
        }
        return result;
      }).catch((error) => {
        if (pageCache.get(key) === entry) removeCachedPage(key);
        throw error;
      });
      entry.promise = request;
      pageCache.set(key, entry);
      trimPageCache();
    }
    return entry.promise;
  }

  function loadRowsByKeys(table, rowKeys, expectedRevision, select = null) {
    if (select !== null && !Array.isArray(select)) return Promise.reject(new Error(`Hosted Table exact-row select is invalid: ${table}`));
    const key = JSON.stringify(['keys', table, expectedRevision, [...new Set(rowKeys || [])].sort(), select === null ? null : [...select].sort()]);
    return queryOnce(key, () => readHostedRowsByKeys(table, rowKeys, expectedRevision, select)).then(({metadata, records}) => ({
      schema: 'lri.tablegit-exact-rows/v1', records, tablegit: metadata, revision: expectedRevision, complete: select === null,
    }));
  }

  function loadRowsByValues(table, filterField, filterValues, expectedRevision) {
    const key = JSON.stringify(['values', table, expectedRevision, filterField, [...new Set(filterValues || [])].sort()]);
    return queryOnce(key, () => readHostedRowsByValues(table, filterField, filterValues, expectedRevision)).then(({metadata, records}) => ({
      schema: 'lri.tablegit-filtered-rows/v1', records, tablegit: metadata, revision: expectedRevision,
    }));
  }

  function loadRowsByValuesPage(table, filterField, filterValues, expectedRevision, {offset = 0, limit = 50} = {}) {
    const values = [...new Set(filterValues || [])].sort();
    if (!expectedRevision || !values.length || values.length > 100 || !values.every(x => typeof x === 'string' && x) ||
        !Number.isSafeInteger(offset) || offset < 0 || !Number.isSafeInteger(limit) || limit < 1 || limit > 100) {
      return Promise.reject(new Error('invalid indexed TableGit page request'));
    }
    const key = JSON.stringify(['values-page', table, expectedRevision, filterField, values, offset, limit]);
    return queryOnce(key, async () => {
      const page = await readJson(`/__mcpgit/tables/${encodeURIComponent(table)}/rows/by-values`, {
        method: 'POST', headers: {'content-type': 'application/json'},
        body: JSON.stringify({expected_revision: expectedRevision, filter_field: filterField, filter_values: values, offset, limit}),
      });
      if (page.revision !== expectedRevision) throw revisionMismatch(expectedRevision, page.revision);
      if (!Array.isArray(page.rows) || page.rows.length > limit || (page.truncated && !page.rows.length)) throw new Error('invalid indexed TableGit page');
      const keys = new Set();
      const records = page.rows.map(envelope => {
        if (!envelope || typeof envelope.key !== 'string' || keys.has(envelope.key) || envelope.deleted ||
            !envelope.row || typeof envelope.row !== 'object' || !values.includes(envelope.row[filterField])) {
          throw new Error('invalid indexed TableGit page row');
        }
        keys.add(envelope.key);
        return envelope.row;
      });
      const total = page.total ?? page.matched_count ?? null;
      if (total !== null && (!Number.isSafeInteger(total) || total < records.length)) throw new Error('invalid indexed TableGit page count');
      return {schema: 'lri.tablegit-page/v1', revision: expectedRevision, records,
        tablegit: {table, status: {revision: expectedRevision}},
        page: {offset, limit, truncated: Boolean(page.truncated), nextOffset: page.truncated ? offset + records.length : null, total}};
    });
  }

  function loadTableMetadata(table, {expectedRevision = ''} = {}) {
    if (contentTables.has(table)) {
      return Promise.reject(new Error(`Content table metadata must use the Content API: ${table}`));
    }
    if (expectedRevision) return readPageMetadata(table, expectedRevision).then(metadata => ({schema: 'lri.tablegit-metadata/v1', tablegit: metadata, revision: expectedRevision}));
    const key = `metadata:${table}`;
    expireLatest(key);
    if (!cache.has(key)) {
      let request;
      request = readJson(`/__mcpgit/tables/${encodeURIComponent(table)}`).then((metadata) => {
        if (metadata.schema !== 'mcpgit/hosted-table/v1' || metadata.table !== table) {
          throw new Error(`invalid Hosted Table metadata: ${table}`);
        }
        const revision = metadata.status?.revision || metadata.revision || '';
        if (!revision) throw new Error(`Hosted Table metadata missing revision: ${table}`);
        if (cache.get(key) === request) sources.set(table, {kind: 'tablegit', revision, rows: 0, metadataOnly: true});
        return {schema: 'lri.tablegit-metadata/v1', tablegit: metadata, revision};
      }).catch((error) => {
        if (cache.get(key) === request) cache.delete(key);
        throw error;
      });
      cache.set(key, request);
    }
    return cache.get(key);
  }

  function loadTableSnapshot(table, options) {
    if (options !== undefined) {
      return Promise.reject(new Error('Works fallback options are removed; Hosted TableGit is the only table source'));
    }
    if (contentTables.has(table)) {
      return Promise.reject(new Error(`full Content table snapshots are forbidden: ${table}`));
    }
    const key = `table:${table}`;
    expireLatest(key);
    if (!cache.has(key)) {
      let request;
      request = readHostedRows(table).then(({metadata, records}) => {
        if (cache.get(key) === request) sources.set(table, {kind: 'tablegit', revision: metadata.status?.revision || metadata.revision || '', rows: records.length});
        return {
          schema: 'lri.tablegit-snapshot/v1',
          generated_from: `tablegit:${table}`,
          count: records.length,
          records,
          tablegit: metadata,
        };
      }).catch((error) => {
        if (cache.get(key) === request) cache.delete(key);
        throw error;
      });
      cache.set(key, request);
    }
    return cache.get(key);
  }

  function source(table) {
    return sources.get(table) || null;
  }

  function queryRelatedContents(ownerKind, ownerId, roles = [], limit = 12, cursor = '', revision = '') {
    if (!['resource', 'match'].includes(ownerKind)) {
      return Promise.reject(new Error(`invalid related-Content owner kind: ${ownerKind}`));
    }
    if (typeof ownerId !== 'string' || !ownerId) {
      return Promise.reject(new Error('related-Content owner id is required'));
    }
    if (!Array.isArray(roles) || !roles.every((role) => typeof role === 'string' && role)) {
      return Promise.reject(new Error('related-Content roles must be non-empty strings'));
    }
    const boundedLimit = Math.max(1, Math.min(Number(limit) || 12, 50));
    const normalizedRoles = [...new Set(roles)].sort();
    const key = JSON.stringify(['related', ownerKind, ownerId, normalizedRoles, boundedLimit, cursor, revision]);
    if (!revision) expireLatest(key);
    if (!cache.has(key)) {
      let request;
      request = (async () => {
        const params = new URLSearchParams({
          owner_kind: ownerKind,
          owner_id: ownerId,
          limit: String(boundedLimit),
        });
        normalizedRoles.forEach((role) => params.append('role', role));
        if (cursor) params.set('cursor', cursor);
        if (revision) params.set('revision', revision);
        const payload = await readJson(`/__mcpgit/content/related?${params}`);
        if (payload.schema !== 'mcpgit/hosted-related-content/v1') {
          throw new Error('invalid Hosted related-Content response');
        }
        const pinnedRevision = payload.revision || '';
        if (!pinnedRevision) throw revisionMismatch(revision || '<required>', pinnedRevision);
        if (revision && pinnedRevision !== revision) throw revisionMismatch(revision, pinnedRevision);
        if (!Array.isArray(payload.links) || !Array.isArray(payload.contents)) {
          throw new Error('invalid Hosted related-Content rows');
        }
        for (const content of payload.contents) {
          if (!content || typeof content !== 'object' || typeof content.content_id !== 'string') {
            throw new Error('invalid Hosted related-Content metadata');
          }
          if (Object.prototype.hasOwnProperty.call(content, 'body') || Object.prototype.hasOwnProperty.call(content, 'data')) {
            throw new Error(`Hosted related-Content metadata leaked body payload: ${content.content_id}`);
          }
        }
        const source = {kind: 'tablegit', revision: pinnedRevision, ownerKind, ownerId, rows: payload.links.length};
        if (cache.get(key) === request) sources.set(`related:${ownerKind}:${ownerId}`, source);
        return {
          revision: pinnedRevision,
          links: payload.links,
          contents: payload.contents,
          nextCursor: payload.next_cursor || payload.nextCursor || '',
          source,
        };
      })().catch((error) => {
        if (cache.get(key) === request) cache.delete(key);
        throw error;
      });
      cache.set(key, request);
    }
    return cache.get(key);
  }

  function loadTopicWorkbench(topicId) {
    if (typeof topicId !== 'string' || !/^[a-z0-9_]+$/.test(topicId)) {
      return Promise.reject(new Error('valid topic workbench id is required'));
    }
    const key = `topic-workbench:${topicId}`;
    expireLatest(key);
    if (!cache.has(key)) {
      let request;
      request = (async () => {
        const profileResult = await readHostedRows('topic_workbench_profiles', {
          filterField: 'topic_id',
          filterValue: topicId,
        });
        if (profileResult.records.length !== 1) {
          throw new Error(`topic workbench profile count must be one: ${topicId}/${profileResult.records.length}`);
        }
        if (profileResult.records[0].topic_id !== topicId) throw new Error(`cross-topic workbench profile: ${topicId}/${profileResult.records[0].topic_id || '<missing>'}`);
        const revision = profileResult.metadata.status?.revision || profileResult.metadata.revision || '';
        if (!revision) throw revisionMismatch('<required>', revision);
        const [itemResult, objectResult, refResult] = await Promise.all([
          readHostedRows('topic_workbench_items', {
            filterField: 'topic_id',
            filterValue: topicId,
            expectedRevision: revision,
          }),
          readHostedRows('topic_workbench_objects', {
            filterField: 'topic_id',
            filterValue: topicId,
            expectedRevision: revision,
          }),
          readHostedRows('topic_entity_refs', {
            filterField: 'topic_id',
            filterValue: topicId,
            expectedRevision: revision,
          }),
        ]);
        for (const row of [...itemResult.records, ...objectResult.records, ...refResult.records]) {
          if (row.topic_id !== topicId) throw new Error(`cross-topic workbench row: ${topicId}/${row.topic_id || '<missing>'}`);
        }
        const refs = {
          resources: new Set(),
          capabilities: new Set(),
          resource_capabilities: new Set(),
          contents: new Set(),
          challenges: new Set(),
        };
        const pluralKinds = {
          resource: 'resources', capability: 'capabilities', resource_capability: 'resource_capabilities',
          content: 'contents', challenge: 'challenges',
        };
        const itemIds = new Set(itemResult.records.map(row => row.item_id));
        const refsByItem = new Map();
        for (const row of [...refResult.records].sort((a, b) => Number(a.ordinal) - Number(b.ordinal) || String(a.ref_id).localeCompare(String(b.ref_id)))) {
          const kind = pluralKinds[row.entity_kind];
          if (!kind) throw new Error(`unsupported topic entity ref kind: ${row.entity_kind}`);
          if (!itemIds.has(row.item_id)) throw new Error(`topic entity ref targets unknown item: ${topicId}/${row.item_id}`);
          if (typeof row.entity_id !== 'string' || !row.entity_id) throw new Error(`invalid topic entity ref: ${topicId}/${row.ref_id}`);
          if (!refsByItem.has(row.item_id)) refsByItem.set(row.item_id, {});
          const entityRefs = refsByItem.get(row.item_id);
          if (!Array.isArray(entityRefs[kind])) entityRefs[kind] = [];
          if (entityRefs[kind].includes(row.entity_id)) throw new Error(`duplicate topic entity ref: ${topicId}/${row.item_id}/${row.entity_id}`);
          entityRefs[kind].push(row.entity_id);
          refs[kind].add(row.entity_id);
        }
        const decoratedItems = itemResult.records.map(row => refsByItem.has(row.item_id) ? {...row, entity_refs: refsByItem.get(row.item_id)} : row);
        const [resourceResult, resourceLocalizationResult, capabilityResult, relationResult, contentResult, locationResult, challengeResult] = await Promise.all([
          readHostedRowsByKeys('resources', [...refs.resources], revision),
          readHostedRowsByValues('resource_localizations', 'resource_id', [...refs.resources], revision),
          readHostedRowsByKeys('technical_capabilities', [...refs.capabilities], revision),
          readHostedRowsByKeys('resource_capabilities', [...refs.resource_capabilities], revision),
          readHostedRowsByKeys('contents', [...refs.contents], revision),
          readHostedRowsByValues('content_locations', 'content_id', [...refs.contents], revision),
          readHostedRowsByKeys('challenge_registry', [...refs.challenges], revision),
        ]);
        const entityResults = {
          resources: resourceResult,
          resource_localizations: resourceLocalizationResult,
          capabilities: capabilityResult,
          resource_capabilities: relationResult,
          contents: contentResult,
          content_locations: locationResult,
          challenges: challengeResult,
        };
        for (const [kind, requested] of Object.entries(refs)) {
          const records = entityResults[kind].records;
          const keyField = kind === 'resources' ? 'resource_id'
            : kind === 'capabilities' ? 'capability_id'
            : kind === 'resource_capabilities' ? 'resource_capability_id'
            : kind === 'contents' ? 'content_id' : 'challenge_id';
          const resolved = new Set(records.map(row => row[keyField]));
          for (const id of requested) {
            if (!resolved.has(id)) throw new Error(`unresolved topic entity ref: ${topicId}/${kind}/${id}`);
          }
        }
        const entityRows = Object.values(entityResults).reduce((count, result) => count + result.records.length, 0);
        const source = {kind: 'tablegit', revision, topicId, rows: 1 + itemResult.records.length + objectResult.records.length + refResult.records.length + entityRows};
        // Only the current cache owner may publish shared diagnostics.
        if (cache.get(key) === request) {
          sources.set('topic_workbench_profiles', {...source, rows: 1});
          sources.set('topic_workbench_items', {...source, rows: itemResult.records.length});
          sources.set('topic_workbench_objects', {...source, rows: objectResult.records.length});
          sources.set('topic_entity_refs', {...source, rows: refResult.records.length});
          for (const [table, result] of Object.entries({
            resources: resourceResult,
            resource_localizations: resourceLocalizationResult,
            technical_capabilities: capabilityResult,
            resource_capabilities: relationResult,
            contents: contentResult,
            content_locations: locationResult,
            challenge_registry: challengeResult,
          })) {
            if (result.metadata) sources.set(table, {...source, rows: result.records.length});
          }
          sources.set(`topic-workbench:${topicId}`, source);
        }
        return {
          schema: 'lri.topic-workbench-snapshot/v1',
          topicId,
          revision,
          profile: profileResult.records[0],
          items: decoratedItems,
          objects: objectResult.records,
          entities: {
            resources: resourceResult.records,
            resource_localizations: resourceLocalizationResult.records,
            capabilities: capabilityResult.records,
            resource_capabilities: relationResult.records,
            contents: contentResult.records,
            content_locations: locationResult.records,
            challenges: challengeResult.records,
          },
          source,
        };
      })().catch((error) => {
        if (cache.get(key) === request) cache.delete(key);
        throw error;
      });
      cache.set(key, request);
    }
    return cache.get(key);
  }

  function materializeTopicWorkbench(snapshot, locale) {
    if (!snapshot || snapshot.schema !== 'lri.topic-workbench-snapshot/v1') {
      throw new Error('valid topic workbench snapshot is required');
    }
    const lang = locale === 'en' ? 'en' : 'zh';
    const payloadField = `payload_${lang}`;
    const topic = snapshot.profile[payloadField];
    if (!topic || typeof topic !== 'object' || Array.isArray(topic)) {
      throw new Error(`topic workbench profile is not localized: ${snapshot.topicId}/${lang}`);
    }
    const collections = {};
    const hasRefs = row => row.entity_refs && typeof row.entity_refs === 'object' &&
      Object.values(row.entity_refs).some(ids => Array.isArray(ids) && ids.length);
    const identityKeys = new Set(['id', 'speaker', 'name', 'organization']);
    const identityFields = row => {
      const fields = {};
      for (const payload of [row.payload_zh, row.payload_en]) {
        if (!payload || typeof payload !== 'object' || Array.isArray(payload)) continue;
        for (const [key, value] of Object.entries(payload)) {
          if ((identityKeys.has(key) || key.endsWith('_id')) && ['string', 'number'].includes(typeof value) && fields[key] == null) fields[key] = value;
        }
      }
      return fields;
    };
    const localizedPayload = row => {
      const payload = row[payloadField];
      if (payload == null && !hasRefs(row)) return null;
      if (payload != null && (typeof payload !== 'object' || Array.isArray(payload))) {
        return hasRefs(row) ? {value: payload, $refs: row.entity_refs} : payload;
      }
      const localized = {...identityFields(row), ...(payload || {})};
      return hasRefs(row) ? {...localized, $refs: row.entity_refs} : localized;
    };
    const ordered = [...snapshot.items].sort((a, b) =>
      String(a.collection_key).localeCompare(String(b.collection_key)) ||
      Number(a.ordinal) - Number(b.ordinal) ||
      String(a.item_id).localeCompare(String(b.item_id))
    );
    for (const row of ordered) {
      const payload = localizedPayload(row);
      if (row.collection_shape === 'array') {
        if (!Array.isArray(collections[row.collection_key])) collections[row.collection_key] = [];
        if (payload == null) continue;
        collections[row.collection_key].push(payload);
      } else if (row.collection_shape === 'map') {
        if (!row.item_key) throw new Error(`topic workbench map item lacks item_key: ${row.item_id}`);
        if (!collections[row.collection_key] || Array.isArray(collections[row.collection_key])) collections[row.collection_key] = {};
        if (payload == null) continue;
        if (Object.prototype.hasOwnProperty.call(collections[row.collection_key], row.item_key)) {
          throw new Error(`duplicate topic workbench map key: ${row.collection_key}/${row.item_key}`);
        }
        collections[row.collection_key][row.item_key] = payload;
      } else {
        throw new Error(`invalid topic workbench collection shape: ${row.item_id}/${row.collection_shape}`);
      }
    }
    const objects = {};
    for (const row of snapshot.objects) {
      const payload = localizedPayload(row);
      if (Object.prototype.hasOwnProperty.call(objects, row.object_key)) {
        throw new Error(`duplicate topic workbench object: ${row.object_key}`);
      }
      objects[row.object_key] = payload == null ? null : payload;
    }
    const localeKey = lang === 'en' ? 'en' : 'zh-CN';
    const localizedMap = (value, fallback = '') => value && typeof value === 'object' && !Array.isArray(value)
      ? (value[localeKey] || '') : fallback;
    const locations = new Map();
    for (const row of snapshot.entities?.content_locations || []) {
      if (!locations.has(row.content_id)) locations.set(row.content_id, []);
      locations.get(row.content_id).push(row);
    }
    const entities = {
      resources: Object.fromEntries((snapshot.entities?.resources || []).map(row => {
        const localization = (snapshot.entities?.resource_localizations || []).find(candidate => candidate.resource_id === row.resource_id && candidate.locale === localeKey);
        return [row.resource_id, {
          ...row,
          name: localization?.display_name || row.display_name || row.resource_id,
          summary: localization?.summary || '',
          translation_status: localization?.translation_status || 'source_only',
        }];
      })),
      capabilities: Object.fromEntries((snapshot.entities?.capabilities || []).map(row => [row.capability_id, {
        ...row,
        name: localizedMap(row.names, row.canonical_code || row.capability_id),
        description: localizedMap(row.descriptions, ''),
      }])),
      resource_capabilities: Object.fromEntries((snapshot.entities?.resource_capabilities || []).map(row => [row.resource_capability_id, {
        ...row,
        boundary: localizedMap(row.boundaries, ''),
      }])),
      contents: Object.fromEntries((snapshot.entities?.contents || []).map(row => [row.content_id, {
        ...row,
        locations: (locations.get(row.content_id) || []).sort((a, b) => Number(b.is_primary) - Number(a.is_primary)),
      }])),
      challenges: Object.fromEntries((snapshot.entities?.challenges || []).map(row => [row.challenge_id, row])),
    };
    return {
      topic,
      collections,
      objects,
      entities,
      facts: {
        schema: snapshot.profile.schema_id,
        topic: {
          id: snapshot.topicId,
          status: snapshot.profile.status,
          last_verified: snapshot.profile.last_verified,
          source_boundary: snapshot.profile.source_boundary,
        },
      },
      source: snapshot.source,
    };
  }

  function invalidate() {
    globalThis.LRICloudTableReadInvalidate?.();
    pageCache.clear();
    pageCacheBytes = 0;
    cache.clear();
    latestTimes.clear();
    queries.clear();
    sources.clear();
  }

  globalThis.LRITableGit = Object.freeze({
    loadTableSnapshot,
    loadTablePage,
    loadTableMetadata,
    loadRowsByKeys,
    loadRowsByValues,
    loadRowsByValuesPage,
    loadTopicWorkbench,
    materializeTopicWorkbench,
    queryRelatedContents,
    source,
    invalidate,
  });
})();


