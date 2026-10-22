import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const siteManifest = JSON.parse(fs.readFileSync(new URL('../../.mcpgit/site.json', import.meta.url), 'utf8'));
const expectedTables = [
  'academic_resource_institution_profiles',
  'academic_text_localizations',
  'challenge_analysis_dimensions',
  'challenge_analysis_profiles',
  'challenge_analysis_relations',
  'challenge_analysis_requirements',
  'challenge_capability_demands',
  'challenge_catalog',
  'challenge_catalog_facets',
  'challenge_catalog_latest',
  'challenge_program_contexts',
  'challenge_registry',
  'challenge_resource_enrichments',
  'challenge_resource_matches',
  'challenge_source_tag_links',
  'challenge_source_tags',
  'challenge_sources',
  'challenge_top_resource_audits',
  'conference_atomic_insight_reviews',
  'conference_cross_event_findings',
  'conference_cross_event_lenses',
  'conference_cross_event_reviews',
  'conference_events',
  'conference_flywheel_feedback',
  'conference_flywheel_runs',
  'conference_lens_memberships',
  'conference_promotion_candidate_reviews',
  'conference_promotion_candidates',
  'conference_promotion_review_queue',
  'content_identifiers',
  'content_locations',
  'contents',
  'google_io_catalog_snapshots',
  'knowledge_gain_lineage',
  'legacy_profile_asset_bindings',
  'match_classifications',
  'match_contents',
  'match_engagement_profiles',
  'match_evidence_arguments',

  'resource_capabilities',
  'resource_card_readiness',
  'resource_catalog',
  'resource_catalog_facets',
  'resource_collections',
  'resource_contact_points',
  'resource_contents',
  'resource_discovery_links',
  'resource_evidence_atoms',
  'resource_localizations',
  'resource_portraits',
  'resources',
  'russian_ai_professor_enrichments',
  'russian_ai_professors',
  'technical_capabilities',
  'technical_capability_family_memberships',
  'topic_entity_refs',
  'topic_workbench_items',
  'topic_workbench_objects',
  'topic_workbench_profiles',
  'wwdc_claim_evidence_relations',
  'wwdc_session_reviews',
  'wwdc_session_theme_relations',
  'wwdc_sessions',
  'wwdc_theme_claims',
  'wwdc_themes',
];
assert.equal(siteManifest.host, 'works');
// Hosting can register additional independent product tables over time. Keep
// the required academic contract strict without freezing the global manifest.
for (const table of expectedTables) assert.ok(siteManifest.tables[table], `missing required Hosted table: ${table}`);
for (const table of expectedTables) {
  const config = siteManifest.tables[table];
  const expectedPath = table === 'challenge_registry' ? 'data/tables/challenge_registry_v3' : `data/tables/${table}`;
  assert.equal(config.path, expectedPath);
  assert.equal(config.topic_id, 'main');
  assert.equal(config.writable, false);
  const maxRows = ['wwdc_claim_evidence_relations','wwdc_session_theme_relations'].includes(table) ? 300 : 200;
  assert.ok(Number.isInteger(config.max_rows) && config.max_rows >= 20 && config.max_rows <= maxRows);
  assert.match(config.person_id, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
}

globalThis.location = new URL('https://lrigit.example/academic_resources/resource_registry/');
const calls = [];
let retryAttempts = 0;
globalThis.fetch = async (value, init = {}) => {
  const url = String(value);
  calls.push(url);
  if (url === '/__mcpgit/tables/items') {
    return response({schema: 'mcpgit/hosted-table/v1', table: 'items', max_rows: 2, status: {revision: 'abc'}});
  }
  if (url === '/__mcpgit/tables/items/rows?offset=0&limit=2') {
    return response({revision: 'abc', rows: [row('a', {id: 'a'}), row('deleted', {id: 'deleted'}, true)], truncated: true});
  }
  if (url === '/__mcpgit/tables/items/rows?offset=2&limit=2') {
    return response({revision: 'abc', rows: [row('b', {id: 'b'})], truncated: false});
  }
  if (url === '/__mcpgit/tables/paged') {
    return response({schema: 'mcpgit/hosted-table/v1', table: 'paged', max_rows: 100, status: {revision: 'page-rev', row_count: 3}});
  }
  if (url === '/__mcpgit/tables/paged/rows?offset=1&limit=2') {
    return response({revision: 'page-rev', rows: [row('b', {id: 'b'}), row('c', {id: 'c'})], truncated: false, total: 3});
  }
  if (url === '/__mcpgit/tables/retry') {
    retryAttempts += 1;
    return retryAttempts === 1
      ? response({}, 503)
      : response({schema: 'mcpgit/hosted-table/v1', table: 'retry', max_rows: 100, status: {revision: 'retry-rev'}});
  }
  if (url === '/__mcpgit/tables/retry/rows?offset=0&limit=100') {
    return response({revision: 'retry-rev', rows: [row('ok', {id: 'ok'})], truncated: false});
  }
  if (url === '/__mcpgit/tables/duplicate') {
    return response({schema: 'mcpgit/hosted-table/v1', table: 'duplicate', max_rows: 100, status: {revision: 'duplicate-rev'}});
  }
  if (url === '/__mcpgit/tables/duplicate/rows?offset=0&limit=100') {
    return response({revision: 'duplicate-rev', rows: [row('same', {id: 1}), row('same', {id: 2})], truncated: false});
  }
  if (url === '/__mcpgit/tables/missing') {
    return response({schema: 'mcpgit/hosted-table/v1', table: 'missing', max_rows: 100, status: {revision: 'missing-rev'}});
  }
  if (url === '/__mcpgit/tables/missing/rows?offset=0&limit=100') {
    return response({revision: 'missing-rev', rows: [{key: 'empty', deleted: false}], truncated: false});
  }
  if (url === '/__mcpgit/tables/bad-metadata') {
    return response({schema: 'wrong/v1', table: 'bad-metadata', max_rows: 100});
  }
  if (url === '/__mcpgit/tables/topic_workbench_profiles') {
    return response({schema: 'mcpgit/hosted-table/v1', table: 'topic_workbench_profiles', max_rows: 100, filter_fields: ['topic_id'], status: {revision: 'topic-rev'}});
  }
  if (url === '/__mcpgit/tables/topic_workbench_profiles/rows?offset=0&limit=100&filter_field=topic_id&filter_value=intent_recognition') {
    return response({revision: 'topic-rev', rows: [row('intent_recognition', {
      topic_id: 'intent_recognition', schema_id: 'topic/v1', status: 'ready', last_verified: '2026-08-13', source_boundary: 'public',
      payload_zh: {title: '意图'}, payload_en: {title: 'Intent'},
    })], truncated: false});
  }
  if (url === '/__mcpgit/tables/topic_workbench_items') {
    return response({schema: 'mcpgit/hosted-table/v1', table: 'topic_workbench_items', max_rows: 2, filter_fields: ['topic_id'], status: {revision: 'topic-rev'}});
  }
  if (url === '/__mcpgit/tables/topic_workbench_items/rows?offset=0&limit=2&filter_field=topic_id&filter_value=intent_recognition') {
    return response({revision: 'topic-rev', rows: [
      row('intent_recognition/tracks/0002', {item_id: 'intent_recognition/tracks/0002', topic_id: 'intent_recognition', collection_key: 'tracks', collection_shape: 'array', item_key: '', ordinal: 2, payload_zh: {name: '工具'}, payload_en: {name: 'Tools'}}),
      row('intent_recognition/tracks/0001', {item_id: 'intent_recognition/tracks/0001', topic_id: 'intent_recognition', collection_key: 'tracks', collection_shape: 'array', item_key: '', ordinal: 1, payload_zh: {name: '任务'}, payload_en: {name: 'Tasks'}}),
    ], truncated: true});
  }
  if (url === '/__mcpgit/tables/topic_workbench_items/rows?offset=2&limit=2&filter_field=topic_id&filter_value=intent_recognition') {
    return response({revision: 'topic-rev', rows: [
      row('intent_recognition/risks/0001', {item_id: 'intent_recognition/risks/0001', topic_id: 'intent_recognition', collection_key: 'risks', collection_shape: 'array', item_key: '', ordinal: 1, payload_zh: {risk: '误执行'}, payload_en: null}),
    ], truncated: false});
  }
  if (url === '/__mcpgit/tables/topic_workbench_objects') {
    return response({schema: 'mcpgit/hosted-table/v1', table: 'topic_workbench_objects', max_rows: 100, filter_fields: ['topic_id'], status: {revision: 'topic-rev'}});
  }
  if (url === '/__mcpgit/tables/topic_workbench_objects/rows?offset=0&limit=100&filter_field=topic_id&filter_value=intent_recognition') {
    return response({revision: 'topic-rev', rows: [], truncated: false});
  }
  if (url === '/__mcpgit/tables/topic_entity_refs') {
    return response({schema: 'mcpgit/hosted-table/v1', table: 'topic_entity_refs', max_rows: 100, filter_fields: ['topic_id'], status: {revision: 'topic-rev'}});
  }
  if (url === '/__mcpgit/tables/topic_entity_refs/rows?offset=0&limit=100&filter_field=topic_id&filter_value=intent_recognition') {
    return response({revision: 'topic-rev', rows: [row('ref-1', {
      ref_id: 'ref-1', topic_id: 'intent_recognition', item_id: 'intent_recognition/risks/0001',
      entity_kind: 'resource', entity_id: 'resource-1', relation_role: 'candidate_or_primary', ordinal: 1,
    })], truncated: false});
  }
  if (url === '/__mcpgit/tables/resources') {
    return response({schema: 'mcpgit/hosted-table/v1', table: 'resources', max_rows: 200, filter_fields: ['resource_id'], status: {revision: 'topic-rev'}});
  }
  if (url === '/__mcpgit/tables/resources/rows?offset=0&limit=200&filter_field=resource_id&filter_value=resource-1') {
    return response({revision: 'topic-rev', rows: [row('resource-1', {
      resource_id: 'resource-1', resource_kind: 'lab', display_name: 'Lab One',
    })], truncated: false});
  }
  if (url === '/__mcpgit/tables/resources/rows/get') {
    assert.equal(init.method, 'POST');
    const body = JSON.parse(init.body);
    assert.deepEqual(body, {keys: ['resource-1']});
    return response({
      revision: 'topic-rev',
      rows: [row('resource-1', {resource_id: 'resource-1', resource_kind: 'lab', display_name: 'Lab One'})],
      missing_keys: [],
      excluded_deleted_keys: [],
      requested_count: 1,
      returned_count: 1,
    });
  }
  if (url === '/__mcpgit/tables/resource_localizations') {
    return response({schema: 'mcpgit/hosted-table/v1', table: 'resource_localizations', max_rows: 100, filter_fields: ['resource_id'], status: {revision: 'topic-rev'}});
  }
  if (url === '/__mcpgit/tables/resource_localizations/rows?offset=0&limit=100&filter_field=resource_id&filter_value=resource-1') {
    return response({revision: 'topic-rev', rows: [
      row('loc-zh', {localization_id: 'loc-zh', resource_id: 'resource-1', locale: 'zh-CN', display_name: '一号实验室', summary: '资源身份', translation_status: 'complete'}),
      row('loc-en', {localization_id: 'loc-en', resource_id: 'resource-1', locale: 'en', display_name: 'Lab One', summary: 'Resource identity', translation_status: 'complete'}),
    ], truncated: false});
  }
  if (url === '/__mcpgit/tables/resource_localizations/rows/by-values') {
    assert.equal(init.method, 'POST');
    const body = JSON.parse(init.body);
    assert.deepEqual(body, {
      expected_revision: 'topic-rev', filter_field: 'resource_id', filter_values: ['resource-1'], offset: 0, limit: 100,
    });
    return response({revision: 'topic-rev', rows: [
      row('loc-zh', {localization_id: 'loc-zh', resource_id: 'resource-1', locale: 'zh-CN', display_name: '一号实验室', summary: '资源身份', translation_status: 'complete'}),
      row('loc-en', {localization_id: 'loc-en', resource_id: 'resource-1', locale: 'en', display_name: 'Lab One', summary: 'Resource identity', translation_status: 'complete'}),
    ], truncated: false});
  }
  if (url === '/__mcpgit/content/related?owner_kind=resource&owner_id=resource-1&limit=1&role=official_profile&role=supporting_evidence&revision=content-rev') {
    return response({
      schema: 'mcpgit/hosted-related-content/v1',
      revision: 'content-rev',
      links: [{link_id: 'link-1', resource_id: 'resource-1', content_id: 'content-1', role: 'official_profile', position: 0}],
      contents: [{
        content_id: 'content-1',
        title: 'Profile',
        primary_locations: [{location_id: 'location-1', content_id: 'content-1', url: 'https://example.test/profile', is_primary: true}],
      }],
      next_cursor: 'cursor-1',
    });
  }
  if (url === '/__mcpgit/content/related?owner_kind=resource&owner_id=resource-html&limit=1') {
    return response('<!doctype html>', 200, 'text/html; charset=utf-8');
  }
  for (const table of ['unversioned-page', 'drifted-page']) {
    if (url === '/__mcpgit/tables/' + table) {
      return response({schema: 'mcpgit/hosted-table/v1', table, max_rows: 100, status: {revision: 'pinned-rev'}});
    }
    if (url === '/__mcpgit/tables/' + table + '/rows?offset=0&limit=100') {
      return response({...table === 'drifted-page' ? {revision: 'other-rev'} : {}, rows: [row('fenced', {id: 'fenced'})], truncated: false});
    }
  }
  throw new Error(`unexpected fetch ${url}`);
};

function response(payload, status = 200, contentType = 'application/json') {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: {get: (name) => name.toLowerCase() === 'content-type' ? contentType : null},
    json: async () => payload,
  };
}

function row(key, value, deleted = false) {
  return {key, deleted, row: value};
}

vm.runInThisContext(fs.readFileSync(new URL('../../assets/lri-tablegit.js', import.meta.url), 'utf8'));
assert.equal(globalThis.LRITableGit.loadJson, undefined);

const hosted = await globalThis.LRITableGit.loadTableSnapshot('items');
assert.deepEqual(hosted.records, [{id: 'a'}, {id: 'b'}]);
assert.equal(hosted.tablegit.status.revision, 'abc');
assert.deepEqual(globalThis.LRITableGit.source('items'), {kind: 'tablegit', revision: 'abc', rows: 2});
await globalThis.LRITableGit.loadTableSnapshot('items');
assert.equal(calls.filter((url) => url === '/__mcpgit/tables/items').length, 2);

const metadataOnly = await globalThis.LRITableGit.loadTableMetadata('items');
assert.equal(metadataOnly.revision, 'abc');
assert.equal(metadataOnly.tablegit.table, 'items');
assert.equal(calls.filter((url) => url === '/__mcpgit/tables/items').length, 3);
await globalThis.LRITableGit.loadTableMetadata('items');
assert.equal(calls.filter((url) => url === '/__mcpgit/tables/items').length, 3);

const paged = await globalThis.LRITableGit.loadTablePage('paged', {offset: 1, limit: 2});
assert.deepEqual(paged.records, [{id: 'b'}, {id: 'c'}]);
assert.deepEqual(paged.page, {offset: 1, limit: 2, truncated: false, nextOffset: null, total: 3});
assert.equal(paged.revision, 'page-rev');

await assert.rejects(
  globalThis.LRITableGit.loadTableSnapshot('items', {fallbackUrl: './fallback.json', allowFallback: true}),
  /Works fallback options are removed/
);
assert.equal(calls.filter((url) => url.endsWith('/fallback.json')).length, 0);

await assert.rejects(globalThis.LRITableGit.loadTableSnapshot('retry'), /load failed: 503/);
const retried = await globalThis.LRITableGit.loadTableSnapshot('retry');
assert.deepEqual(retried.records, [{id: 'ok'}]);
assert.equal(retryAttempts, 3);

await assert.rejects(globalThis.LRITableGit.loadTableSnapshot('duplicate'), /duplicate Hosted Table key/);
await assert.rejects(globalThis.LRITableGit.loadTableSnapshot('missing'), /missing Hosted Table row payload/);
await assert.rejects(globalThis.LRITableGit.loadTableSnapshot('bad-metadata'), /invalid Hosted Table metadata/);
await assert.rejects(globalThis.LRITableGit.loadTableSnapshot('contents'), /full Content table snapshots are forbidden/);
assert.equal(calls.filter((url) => url === '/__mcpgit/tables/contents').length, 0);

// A valid fixture must carry the pinned revision on every page. Reject omissions and drift.
for (const table of ['unversioned-page', 'drifted-page']) {
  await assert.rejects(globalThis.LRITableGit.loadTableSnapshot(table), error => error.code === 'revision_mismatch');
  assert.equal(globalThis.LRITableGit.source(table), null);
}

const topicSnapshot = await globalThis.LRITableGit.loadTopicWorkbench('intent_recognition');
assert.equal(topicSnapshot.revision, 'topic-rev');
assert.equal(topicSnapshot.items.length, 3);
const topicZh = globalThis.LRITableGit.materializeTopicWorkbench(topicSnapshot, 'zh');
assert.equal(topicZh.topic.title, '意图');
assert.deepEqual(topicZh.collections.tracks.map((item) => item.name), ['任务', '工具']);
assert.equal(topicZh.collections.risks[0].risk, '误执行');
assert.equal(topicZh.facts.schema, 'topic/v1');
const topicEn = globalThis.LRITableGit.materializeTopicWorkbench(topicSnapshot, 'en');
assert.deepEqual(topicEn.collections.tracks.map((item) => item.name), ['Tasks', 'Tools']);
assert.deepEqual(topicEn.collections.risks[0].$refs, {resources: ['resource-1']});
assert.equal(topicEn.entities.resources['resource-1'].name, 'Lab One');
assert.equal(topicZh.entities.resources['resource-1'].name, '一号实验室');
assert.equal(calls.filter((url) => url === '/__mcpgit/tables/resources/rows/get').length, 1);
assert.equal(calls.filter((url) => url === '/__mcpgit/tables/resource_localizations/rows/by-values').length, 1);
assert.equal(calls.filter((url) => url.includes('/resources/rows?') && url.includes('filter_value=resource-1')).length, 0);
assert.equal(calls.filter((url) => url.includes('/resource_localizations/rows?') && url.includes('filter_value=resource-1')).length, 0);
assert.deepEqual(globalThis.LRITableGit.source('topic-workbench:intent_recognition'), {kind: 'tablegit', revision: 'topic-rev', topicId: 'intent_recognition', rows: 8});

const related = await globalThis.LRITableGit.queryRelatedContents(
  'resource', 'resource-1', ['supporting_evidence', 'official_profile'], 1, '', 'content-rev'
);
assert.equal(related.revision, 'content-rev');
assert.equal(related.links.length, 1);
assert.equal(related.links[0].link_id, 'link-1');
assert.equal(related.contents[0].content_id, 'content-1');
assert.equal(related.contents[0].primary_locations[0].url, 'https://example.test/profile');
assert.equal(related.nextCursor, 'cursor-1');
assert.equal(calls.filter((url) => url.startsWith('/__mcpgit/content/related?')).length, 1);
assert.equal(calls.filter((url) => url.startsWith('/__mcpgit/tables/contents')).length, 0);
assert.deepEqual(globalThis.LRITableGit.source('related:resource:resource-1'), {
  kind: 'tablegit', revision: 'content-rev', ownerKind: 'resource', ownerId: 'resource-1', rows: 1,
});
await assert.rejects(
  globalThis.LRITableGit.queryRelatedContents('resource', 'resource-html', [], 1),
  /expected JSON, received text\/html/
);

globalThis.LRITableGit.invalidate();
assert.equal(globalThis.LRITableGit.source('items'), null);
for (const file of [
  '../../assets/lri-tablegit.js',
  '../challenge_matching/page.js',
  '../resource_registry/page.js',
  '../resource_cards/page.js',
]) {
  const source = fs.readFileSync(new URL(file, import.meta.url), 'utf8');
  assert.doesNotMatch(source, /allowFallback|fallbackUrl|works-fallback/);
}

console.log(JSON.stringify({pass: true, configuredTables: expectedTables.length, hostedRows: hosted.records.length, retryAttempts, worksFallbackCapability: false}));
