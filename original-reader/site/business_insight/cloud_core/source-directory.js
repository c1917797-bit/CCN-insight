/* Source subjects and acquisition entrypoints are separate native TableGit rows. */
(() => {
  'use strict';
  const categories = {
    hotspot: ['media', 'newsletters', 'community'],
    academic: ['papers', 'reviews', 'venues', 'references'],
    industry: ['compression', 'runtimes', 'kernels', 'platforms', 'evaluation', 'organizations']
  };
  const kinds = ['homepage', 'subject_list', 'rss', 'repository', 'documentation', 'releases', 'tags', 'discussion', 'blog', 'archive', 'paper_reference'];
  const rank = row => ({P0:0, P1:1, P2:2})[row.priority] ?? 3;
  function validate(data) {
    const require = (ok, message) => { if (!ok) throw new Error('Source subject integrity: ' + message); };
    require(Array.isArray(data.source_families) && Array.isArray(data.channel_families), 'missing native tables');
    const channels = new Map(data.channels.map(c => [c.channel_id, c]));
    const families = new Map(data.source_families.map(f => [f.family_id, f]));
    require(channels.size === data.channels.length && families.size === data.source_families.length, 'duplicate identity');
    const assigned = new Set(), used = new Set(), ids = new Set();
    for (const f of families.values()) {
      require(f.business_id === 'cloud-core' && f.topic_id === 'cloud_core' && f.family_id && f.title_zh && f.title_en && f.summary_zh && f.summary_en, 'missing subject identity or reading fields');
      require(categories[f.ui_group]?.includes(f.category_key), 'unknown browsing category');
    }
    for (const link of data.channel_families) {
      const c = channels.get(link.channel_id), f = families.get(link.family_id);
      require(link.membership_id && !ids.has(link.membership_id) && !assigned.has(link.channel_id), 'duplicate entrypoint membership');
      require(c && f && c.ui_group === f.ui_group && link.business_id === 'cloud-core' && link.topic_id === 'cloud_core', 'dangling or cross-category entrypoint');
      require(kinds.includes(link.entry_kind) && Number.isSafeInteger(link.position), 'invalid entrypoint kind or order');
      assigned.add(link.channel_id); used.add(link.family_id); ids.add(link.membership_id);
    }
    require(assigned.size === channels.size && used.size === families.size, 'incomplete subject membership');
    require(Array.isArray(data.industry_source_scopes), 'missing ecosystem table');
    const scopes = new Map();
    for (const scope of data.industry_source_scopes) {
      const family = families.get(scope.family_id);
      require(family?.ui_group === 'industry' && !scopes.has(scope.family_id), 'duplicate or non-industry ecosystem');
      require(scope.business_id === 'cloud-core' && scope.topic_id === 'cloud_core' &&
        ['ascend','general'].includes(scope.ecosystem_id) && scope.reason_zh && scope.reason_en &&
        scope.classification_basis && /^\d{4}-\d{2}-\d{2}$/.test(scope.reviewed_at), 'invalid ecosystem classification');
      require(data.channel_families.some(link => link.family_id === scope.family_id &&
        channels.get(link.channel_id)?.source_id === scope.source_id), 'ecosystem source outside subject');
      scopes.set(scope.family_id, scope);
    }
    require(scopes.size === data.source_families.filter(f => f.ui_group === 'industry').length, 'incomplete ecosystem classification');
    return {subjects:families.size, entrypoints:channels.size};
  }
  function catalog(data, {domain, important, query='', category='', searchText=()=>''}) {
    const totals = validate(data), byId = new Map(data.channels.map(c => [c.channel_id, c]));
    const scopes = new Map(data.industry_source_scopes.map(s => [s.family_id,s]));
    const members = new Map();
    for (const link of data.channel_families) {
      if (!members.has(link.family_id)) members.set(link.family_id, []);
      members.get(link.family_id).push({...link, channel:byId.get(link.channel_id)});
    }
    const all = data.source_families.filter(f => f.ui_group === domain).map(family => {
      const entries = members.get(family.family_id).sort((a,b) => rank(a.channel)-rank(b.channel) || a.position-b.position || a.channel_id.localeCompare(b.channel_id));
      return {family, entries, ecosystem:scopes.get(family.family_id)?.ecosystem_id || '', rank:Math.min(...entries.map(e=>rank(e.channel))), ordinal:Math.min(...entries.map(e=>e.position))};
    });
    const core = all.filter(g => g.rank <= 1);
    const eligible = important ? core : all;
    const term = query.trim().toLocaleLowerCase();
    const rows = eligible.filter(g => (!category || g.family.category_key === category) && (!term || [g.family.title_zh,g.family.title_en,g.family.summary_zh,g.family.summary_en,...g.entries.map(e=>searchText(e.channel))].join(' ').toLocaleLowerCase().includes(term)))
      .sort((a,b)=>a.rank-b.rank || a.ordinal-b.ordinal || a.family.family_id.localeCompare(b.family.family_id));
    return {totals, all, core, rows, categories:categories[domain].map(key=>({key,count:eligible.filter(g=>g.family.category_key===key).length})).filter(c=>c.count)};
  }
  // Independent paging keeps a small hardware-specific group visible while browsing references.
  function industrySections(catalog, offsets={}, pageSize=8) {
    if (!Number.isSafeInteger(pageSize) || pageSize < 1) throw new Error('Invalid ecosystem page size');
    return ['ascend','general'].map(id => {
      const all = catalog.rows.filter(group => group.ecosystem === id);
      const requested = Number.isSafeInteger(offsets[id]) && offsets[id] >= 0 ? offsets[id] : 0;
      const offset = all.length ? Math.min(Math.floor(requested/pageSize)*pageSize, Math.floor((all.length-1)/pageSize)*pageSize) : 0;
      return {id, total:all.length, offset, rows:all.slice(offset,offset+pageSize), hasPrev:offset>0, hasNext:offset+pageSize<all.length};
    });
  }
  globalThis.LRIGroupedSources = Object.freeze({validate,catalog,industrySections,categories,kinds});
})();

