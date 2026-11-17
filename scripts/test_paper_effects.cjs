/* Exercise canonical paper experiments and the actual reader component without a browser. */
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'original-reader/site/business_insight/cloud_core/compression.js'), 'utf8');
const read = name => fs.readFileSync(path.join(root, 'data/compression/tables', name, 'rows.jsonl'), 'utf8')
  .split('\n').filter(Boolean).map(JSON.parse).filter(row => !row.deleted).map(row => row.row);
const experiments = read('ic_paper_experiments');
const topics = read('ic_compression_topics');
const cards = read('ic_compression_topic_cards');
const refs = read('ic_compression_topic_card_refs');
const sources = read('cloud_core_sources');
const revision = 'paper-effects-regression';
const clone = value => JSON.parse(JSON.stringify(value));
const extract = (start, end) => {
  const from = source.indexOf(start), to = source.indexOf(end, from);
  assert(from >= 0 && to > from, 'Missing maintained code: ' + start);
  return source.slice(from, to);
};
const experimentCode = extract('// Experiments are maintained once', 'const routeEvidenceReaders=');
const dossier = topic => {
  const ownRefs = refs.filter(row => row.compression_topic_id === topic);
  const sourceIds = new Set(ownRefs.map(row => row.source_id));
  return {revision, topic, refs: ownRefs, cards: cards.filter(row => row.compression_topic_id === topic),
    sources: sources.filter(row => sourceIds.has(row.source_id))};
};
const expected = topic => experiments.filter(row => JSON.parse(row.topic_ids_json).includes(topic));
const ids = rows => Array.from(rows, row => row.experiment_id).sort();
const walk = node => [node, ...node.children.flatMap(walk)];
class Node {
  constructor(tag, text = '', cls = '') {
    this.tagName = tag.toUpperCase(); this.ownText = String(text); this.className = cls;
    this.children = []; this.parentElement = null; this.dataset = {}; this.attributes = {};
    this.id = ''; this.value = ''; this.hidden = false; this.open = false; this.listeners = new Map();
    this.classList = {
      contains: name => this.className.split(/\s+/).includes(name),
      add: (...names) => { this.className = [...new Set([...this.className.split(/\s+/).filter(Boolean), ...names])].join(' '); },
      toggle: (name, enabled) => { const current = new Set(this.className.split(/\s+/).filter(Boolean));
        const on = enabled === undefined ? !current.has(name) : enabled;
        on ? current.add(name) : current.delete(name); this.className = [...current].join(' '); return on; },
    };
  }
  get textContent() { return this.ownText + this.children.map(node => node.textContent).join(''); }
  set textContent(text) { this.ownText = String(text); this.replaceChildren(); }
  get hash() { return this.href ? new URL(this.href, 'https://reader.test/').hash : ''; }
  append(...nodes) { for (const node of nodes) { node.parentElement = this; this.children.push(node); } }
  replaceChildren(...nodes) { for (const node of this.children) node.parentElement = null; this.children = []; this.append(...nodes); }
  setAttribute(key, value) { this.attributes[key] = String(value); if (key === 'id') this.id = String(value); }
  getAttribute(key) { return key === 'href' ? this.href : this.attributes[key] ?? null; }
  addEventListener(type, action) { if (!this.listeners.has(type)) this.listeners.set(type, []); this.listeners.get(type).push(action); }
  emit(type, init = {}) { const event = {target: this, button: 0, preventDefault() { this.defaultPrevented = true; }, stopPropagation() {}, ...init};
    for (const action of this.listeners.get(type) || []) action(event); return event; }
  click(init) { return this.emit('click', init); }
  matches(selector) {
    if (selector === '[hidden]') return this.hidden;
    if (selector.startsWith('#')) return this.id === selector.slice(1);
    if (selector.startsWith('.')) return this.classList.contains(selector.slice(1));
    if (/^[a-z]+$/i.test(selector)) return this.tagName === selector.toUpperCase();
    throw Error('Unsupported fixture selector: ' + selector);
  }
  closest(selector) { for (let node = this; node; node = node.parentElement) if (node.matches(selector)) return node; return null; }
  querySelectorAll(selector) { return walk(this).slice(1).filter(node => node.matches(selector)); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  scrollIntoView() { this.scrolled = true; }
  focus() { this.focused = true; }
}
const node = (tag, text = '', cls = '') => new Node(tag, text, cls);
function fixture({topic = 'parameters-precision', locale = 'zh', view = 'overview', route = '', api} = {}) {
  const host = node('main'), frames = [], calls = [], current = dossier(topic);
  const box = {
    URL, URLSearchParams, console, state: {epoch: 1, revision, locale, directionMode: true,
      period: '2026-10', scope: 'ic-reviewed-scope', data: {compression_topics: topics}},
    location: new URL('https://reader.test/business_insight/cloud_core/topic.html?topic=' + topic +
      '&month=2026-10&scope=ic-reviewed-scope&view=' + view + (route ? '&route=' + route : '')),
    document: {getElementById: id => walk(host).find(node => node.id === id) || null},
    element: node, button: (text, action) => { const control = node('button', text); control.addEventListener('click', action); return control; },
    external: (parent, href, text) => { const link = node('a', text); link.href = href; link.target = '_blank'; parent.append(link); },
    mapText: (zh, en) => box.state.locale === 'en' ? en : zh,
    textOf: (row, key) => row?.[key + '_' + box.state.locale] || row?.[key + '_zh'] || '',
    topicPage: () => true, compressionTopicId: () => current.topic, researchDossier: () => current,
    renderDirectionDetail: () => { box.renders++; }, renders: 0,
    requestAnimationFrame: action => { frames.push(action); },
    $: id => box.document.getElementById(id), showView() {}, viewForTarget: () => 'topics', ensureOpenedDisclosuresLoaded() {},
    LRITableGit: api || {
      async loadRowsByValuesPage(table, field, values, pinned, options) {
        calls.push({table, field, values, pinned, ...options});
        const all = experiments.filter(row => values.includes(row.source_id));
        const records = all.slice(options.offset, options.offset + options.limit), next = options.offset + records.length;
        return {revision: pinned, records, page: {offset: options.offset, total: all.length,
          truncated: next < all.length, nextOffset: next < all.length ? next : null}};
      },
    },
  };
  box.history = {replaceState(_, __, href) { box.location = new URL(href, box.location.href); },
    pushState(_, __, href) { box.location = new URL(href, box.location.href); }};
  vm.createContext(box);
  for (const [start, end] of [
    ['function openResearchTarget(', 'function disclosure('],
    ['function bindResearchJump(', '// Topic facts stay'],
    ['function researchView(', 'function researchNav('],
    ['function researchSectionView(', 'function applyResearchView('],
  ]) vm.runInContext(extract(start, end), box);
  vm.runInContext(experimentCode, box);
  const setSnapshot = rows => {
    box.injected = {revision, topic: current.topic, rows: box.validatePaperExperiments(rows, current)};
    vm.runInContext('paperEffectReaders.set(injected.revision+"__"+injected.topic,injected)', box);
  };
  const render = rows => { if (rows !== undefined) setSnapshot(rows); host.replaceChildren(); box.renderPaperEffectTable(host, current); return host; };
  const flushFrames = () => { let limit = 20; while (frames.length) { assert(limit-- > 0, 'Unbounded animation-frame loop'); frames.shift()(); } };
  return {box, host, current, calls, setSnapshot, render, flushFrames};
}
const tableRows = host => walk(host).filter(node => node.dataset.paperExperiment);
const controls = host => ({query: walk(host).find(node => node.tagName === 'INPUT'),
  model: walk(host).filter(node => node.tagName === 'SELECT')[0], format: walk(host).filter(node => node.tagName === 'SELECT')[1],
  clear: walk(host).find(node => node.tagName === 'BUTTON' && /清除筛选|Clear filters/.test(node.textContent))});
const checks = [];
function check(name, run) { checks.push({name, run}); }

check('Every canonical experiment is projected to exactly its explicit topics across all 16 real dossiers', async () => {
  assert.equal(experiments.length, 8, 'This release contains eight explicitly reviewed experiments');
  assert.equal(topics.length, 16); assert.equal(new Set(ids(experiments)).size, experiments.length);
  const observed = new Map(experiments.map(row => [row.experiment_id, []]));
  for (const topic of topics) {
    const f = fixture({topic: topic.compression_topic_id});
    const snapshot = await f.box.loadPaperExperiments(f.current);
    assert.deepEqual(ids(snapshot.rows), ids(expected(f.current.topic)), f.current.topic);
    for (const row of snapshot.rows) observed.get(row.experiment_id).push(f.current.topic);
    for (const call of f.calls) {
      assert.equal(call.table, 'ic_paper_experiments'); assert.equal(call.field, 'source_id'); assert.equal(call.pinned, revision);
      assert(call.values.every(id => f.current.refs.some(ref => ref.source_id === id)), 'Do not borrow another topic\'s sources');
    }
  }
  for (const row of experiments) assert.deepEqual(observed.get(row.experiment_id).sort(), JSON.parse(row.topic_ids_json).sort());
  assert(experiments.some(row => JSON.parse(row.topic_ids_json).length >= 3), 'Use the real joint W/A/KV experiment');
});

check('A paper retains distinct quality and system experiments without duplicating canonical records', async () => {
  const align = experiments.filter(row => row.method === 'AlignQuant');
  assert.equal(align.length, 2); assert.equal(new Set(align.map(row => row.source_id)).size, 1);
  assert.deepEqual(align.map(row => row.experiment_kind).sort(), ['quality', 'system']);
  const f = fixture(); const snapshot = await f.box.loadPaperExperiments(f.current);
  assert.deepEqual(ids(snapshot.rows.filter(row => row.method === 'AlignQuant')), ids(align));
  assert.throws(() => f.box.validatePaperExperiments([experiments[0], experiments[0]], f.current), /duplicate experiment/);
});

check('Indexed source reads retrieve 103 experiment rows with exact, revision-bound pagination', async () => {
  const f = fixture(), records = Array.from({length: 103}, (_, i) => ({...experiments[0], experiment_id: 'pagination_' + i, position: i})), offsets = [];
  const api = {async loadRowsByValuesPage(table, field, values, pinned, {offset, limit}) {
    assert.equal(table, 'ic_paper_experiments'); assert.equal(field, 'source_id'); assert.equal(pinned, revision); assert.equal(limit, 100);
    offsets.push(offset); const page = records.slice(offset, offset + limit), next = offset + page.length;
    return {revision, records: page, page: {offset, total: records.length, truncated: next < records.length, nextOffset: next}};
  }};
  const snapshot = await f.box.loadPaperExperiments(f.current, api);
  assert.equal(snapshot.rows.length, 103); assert.deepEqual(offsets, [0, 100]);
});

check('Wrong revisions, incomplete pages, duplicate rows, foreign sources and stalled cursors are rejected', async () => {
  const f = fixture(), row = experiments[0];
  const envelope = (records, extra = {}) => ({revision, records, page: {offset: 0, total: records.length, truncated: false}, ...extra});
  const rejected = payload => assert.rejects(f.box.loadPaperExperiments(f.current, {loadRowsByValuesPage: async () => payload}));
  await rejected(envelope([row], {revision: 'other'}));
  await rejected(envelope([row], {page: {offset: 0, total: 2, truncated: false}}));
  await rejected(envelope([row], {page: {offset: 0, total: 2, truncated: true, nextOffset: 0}}));
  await rejected(envelope([row, row]));
  await rejected(envelope([{...row, source_id: 'foreign-source'}]));
  await rejected(envelope([], {page: {offset: 0, total: 2, truncated: true, nextOffset: 0}}));
});

check('Numeric status arrays, pinned paper identity/version, real dates and explicit topic assignments fail closed', () => {
  const f = fixture(), row = experiments[0], metric = JSON.parse(row.quality_metrics_json)[0];
  const patches = [
    {quality_status: 'not_reported'}, {quality_metrics_json: '[]'}, {quality_metrics_json: '{}'},
    {quality_metrics_json: JSON.stringify([{...metric, result: true}])},
    {quality_metrics_json: JSON.stringify([{...metric, result: null}])},
    {quality_metrics_json: JSON.stringify([{...metric, unit: ''}])},
    {source_url: row.source_url.replace(/v\d+/, 'v99')},
    {source_url: 'https://arxiv.org/pdf/9999.12345v6'}, {source_url: 'javascript:alert(1)'},
    {checked_at: '2026-02-30'}, {checked_at: 'not-a-date'},
    {topic_ids_json: '["missing-topic"]'}, {topic_ids_json: '["parameters-precision","parameters-precision"]'},
  ];
  for (const patch of patches) assert.throws(() => f.box.validatePaperExperiments([{...row, ...patch}], f.current), JSON.stringify(patch));
});

check('The real seven-column table is bilingual and each method expands its own full conditions', () => {
  for (const locale of ['zh', 'en']) {
    const f = fixture({locale}); f.render(expected(f.current.topic));
    const header = walk(f.host).find(node => node.tagName === 'THEAD').children[0];
    assert.deepEqual(header.children.map(node => node.textContent), locale === 'zh'
      ? ['方法', '模型', '具体格式', '质量变化', '性能', '内存', '条件与来源']
      : ['Method', 'Model', 'Exact formats', 'Quality', 'Performance', 'Memory', 'Conditions and sources']);
    assert.equal(tableRows(f.host).length, expected(f.current.topic).length);
    for (const tr of tableRows(f.host)) {
      assert.equal(tr.children.length, 7); const original = experiments.find(row => row.experiment_id === tr.dataset.paperExperiment);
      const toggle = walk(tr).find(node => node.tagName === 'BUTTON'), detail = f.box.$(toggle.getAttribute('aria-controls'));
      assert.equal(toggle.textContent, original.method); assert.equal(detail.hidden, true); assert.equal(toggle.getAttribute('aria-expanded'), 'false');
      toggle.click(); assert.equal(detail.hidden, false); assert.equal(toggle.getAttribute('aria-expanded'), 'true');
      assert.equal(detail.children[0].colSpan, 7);
      for (const key of ['config', 'baseline', 'dataset', 'hardware', 'runtime', 'workload', 'protocol', 'locator'])
        assert(detail.textContent.includes(original[key + '_' + locale]), 'Lost ' + key + ' for ' + original.experiment_id);
      assert(detail.textContent.includes(original.observed_version) && detail.textContent.includes(original.checked_at));
      assert(walk(tr).some(link => link.tagName === 'A' && link.href === original.source_url));
      toggle.click(); assert.equal(detail.hidden, true); f.box.openResearchTarget(tr); assert.equal(detail.hidden, false);
    }
  }
});

check('Long format summaries preserve complete values in conditions and exact filter options', () => {
  const f = fixture(); f.render(expected(f.current.topic));
  assert.equal(typeof f.box.paperEffectFormatSummary, 'function');
  for (const row of expected(f.current.topic)) {
    const tr = tableRows(f.host).find(node => node.dataset.paperExperiment === row.experiment_id);
    const detail = f.box.$('experiment-conditions-' + row.experiment_id), format = controls(f.host).format;
    for (const key of ['w_format', 'a_format', 'k_format', 'v_format']) {
      assert(format.children.some(option => option.value === JSON.stringify([key, row[key]])), 'Filter must retain exact format');
      assert(detail.textContent.includes(row[key]), 'Full ' + key + ' must remain readable in conditions');
    }
    assert(tr.children[2].textContent.length < ['w_format', 'a_format', 'k_format', 'v_format'].map(key => row[key]).join('').length + 100,
      'Summary should not duplicate all long descriptions');
  }
});

check('Search, model and exact-format filters work together and clear/no-match states are accurate', () => {
  const f = fixture(); f.render(expected(f.current.topic)); const fields = controls(f.host), all = expected(f.current.topic);
  fields.query.value = 'resident_allocated_gpu_memory'; fields.query.emit('input');
  assert.deepEqual(tableRows(f.host).map(node => node.dataset.paperExperiment).sort(), ids(all.filter(row => row.memory_metrics_json.includes('resident_allocated_gpu_memory'))));
  fields.clear.click(); assert.equal(tableRows(f.host).length, all.length);
  const selectedModel = all.find(row => row.method === 'AlignQuant').model;
  fields.model.value = selectedModel; fields.model.emit('change');
  assert.deepEqual(tableRows(f.host).map(node => node.dataset.paperExperiment).sort(), ids(all.filter(row => row.model === selectedModel)));
  const selected = all.find(row => row.model === selectedModel);
  fields.format.value = JSON.stringify(['w_format', selected.w_format]); fields.format.emit('change');
  assert.deepEqual(tableRows(f.host).map(node => node.dataset.paperExperiment).sort(), ids(all.filter(row => row.model === selectedModel && row.w_format === selected.w_format)));
  fields.query.value = 'there-is-no-such-experiment'; fields.query.emit('input');
  assert.equal(tableRows(f.host).length, 0); assert(f.host.textContent.includes('没有符合当前筛选的实验'));
  fields.clear.click(); assert.equal(fields.query.value, ''); assert.equal(fields.model.value, ''); assert.equal(fields.format.value, '');
  assert.equal(tableRows(f.host).length, all.length);
  const title = sources.find(source => source.source_id === selected.source_id).title;
  fields.query.value = title; fields.query.emit('input');
  assert(tableRows(f.host).some(node => node.dataset.paperExperiment === selected.experiment_id), 'Search includes canonical paper titles');
});

check('Missing experiment data and all missing-metric statuses are distinct from zero-valued results', () => {
  for (const locale of ['zh', 'en']) {
    const f = fixture({locale, topic: 'parameters-distillation'}); f.render([]);
    assert.equal(tableRows(f.host).length, 0); assert.equal(walk(f.host).filter(node => node.tagName === 'TABLE').length, 0);
    assert(f.host.textContent.includes(locale === 'zh' ? '尚未整理规范实验对照' : 'have not yet been compiled'));
    const metricFixture = fixture({locale});
    const row = {...experiments[0], quality_status: 'not_checked', quality_metrics_json: '[]', memory_status: 'not_applicable'};
    metricFixture.render([row]); const missing = walk(metricFixture.host).filter(node => node.classList.contains('paper-effect-missing')).map(node => node.textContent);
    assert.deepEqual(missing, locale === 'zh' ? ['尚未核对', '本实验未报告', '不适用'] : ['Not checked', 'Not reported for this experiment', 'Not applicable']);
  }
});

check('PPL deltas, percentage points and small/precise numbers retain their metric meaning', () => {
  const f = fixture(), format = (metric, kind = 'quality') => f.box.paperEffectMetricText(metric, kind);
  assert(format({metric: 'PPL', baseline: 5.47, result: 5.60, unit: 'PPL'}).endsWith('Δ +0.13 PPL'));
  assert(format({metric: 'GSM8K', baseline: 13.5, result: 12.74, unit: '%'}).endsWith('Δ -0.76 个百分点'));
  assert(format({metric: 'arithmetic', baseline: 0.1, result: 0.3, unit: 'score'}).endsWith('Δ +0.2 score'));
  assert(format({metric: 'latency', baseline: 1e-8, result: 2e-8, unit: 's'}, 'performance').includes('1e-8 s → 2e-8 s · Δ +1e-8 s'));
  assert(format({metric: 'PPL', baseline: 12.74123456789, result: 12.74012345678, unit: 'PPL'}).includes('12.74123456789 PPL → 12.74012345678 PPL'));
  assert(format({metric: 'TPOT', baseline: 17.19, result: 7.54, unit: 'ms/token'}, 'performance').startsWith('TPOT ·'));
  f.box.state.locale = 'en'; assert(format({metric: 'Accuracy', baseline: 50, result: 49, unit: '%'}).endsWith('Δ -1 percentage points'));
});

check('A same-topic epoch restart reuses its pending read and still repaints the current reader', async () => {
  let release, reads = 0; const gate = new Promise(resolve => { release = resolve; });
  const f = fixture({api: {async loadRowsByValuesPage(_, __, values, pinned) {
    reads++; await gate; const records = experiments.filter(row => values.includes(row.source_id));
    return {revision: pinned, records, page: {offset: 0, total: records.length, truncated: false}};
  }}});
  f.box.ensurePaperEffects(f.current); f.box.state.epoch++;
  f.box.ensurePaperEffects(f.current); assert.equal(reads, 1);
  const pending = vm.runInContext('paperEffectPending.get(state.revision+"__"+compressionTopicId())', f.box);
  release(); await pending;
  assert.equal(f.box.renders, 1, 'A cached result must repaint even after the same-topic reader restarts');
  assert.equal(vm.runInContext('paperEffectPending.size', f.box), 0);
  assert.deepEqual(ids(vm.runInContext('paperEffectReaders.get(state.revision+"__"+compressionTopicId()).rows', f.box)), ids(expected(f.current.topic)));
});

check('Partial-view case links preserve month/scope and select a visible target without leaking route', () => {
  const f = fixture({view: 'comparison', route: 'old-route'});
  for (const row of expected(f.current.topic)) {
    const link = f.box.paperEffectCaseLink(row, f.current); assert(link, row.experiment_id);
    const url = new URL(link.href, f.box.location.href);
    assert.equal(url.searchParams.get('month'), '2026-10'); assert.equal(url.searchParams.get('scope'), 'ic-reviewed-scope');
    assert.equal(url.searchParams.has('route'), false); assert(url.hash.startsWith('#research-card-'));
    const card = f.box.paperEffectCase(row, f.current);
    if (card) {
      const expectedView = card.section_kind === 'papers' ? 'literature' : f.box.researchSectionView(card.section_kind === 'implication' ? 'implications' : card.section_kind);
      assert.equal(url.searchParams.get('view'), expectedView); assert.equal(url.hash, '#research-card-' + card.card_id);
    } else assert.equal(url.searchParams.get('topic'), row.card_id.split('__')[0]);
  }
  const foreign = experiments.find(row => row.method === 'SmoothQuant'), foreignDossier = {...f.current, cards: []};
  const fallback = new URL(f.box.paperEffectCaseLink(foreign, foreignDossier).href, f.box.location.href);
  assert.equal(fallback.searchParams.get('topic'), foreign.card_id.split('__')[0]); assert.equal(fallback.hash, '#research-card-' + foreign.card_id);
});

check('The effect shortcut and deep-link restoration select comparison while preserving month/scope', () => {
  const f = fixture({view: 'mechanism', route: 'old-route'});
  assert.equal(typeof f.box.paperEffectShortcut, 'function'); const shortcut = f.box.paperEffectShortcut();
  assert.equal(shortcut.dataset.paperEffectsLink, 'true'); const url = new URL(shortcut.href, f.box.location.href);
  assert.equal(url.searchParams.get('view'), 'comparison'); assert.equal(url.hash, '#direction-paper-effects');
  assert.equal(url.searchParams.get('month'), '2026-10'); assert.equal(url.searchParams.get('scope'), 'ic-reviewed-scope'); assert.equal(url.searchParams.has('route'), false);
  const target = 'research-card-experiment-' + experiments[0].experiment_id;
  f.box.location.hash = target; f.box.revealHashTarget();
  assert.equal(f.box.location.searchParams.get('view'), 'comparison'); assert.equal(f.box.location.searchParams.has('route'), false);
  assert.equal(f.box.location.hash, '#' + target); assert.equal(f.box.renders, 1);
  f.render(expected(f.current.topic)); const row = f.box.$(target);
  assert(row); assert.equal(f.box.$('experiment-conditions-' + row.dataset.paperExperiment).hidden, false);
});

(async () => {
  const failed = [];
  for (const {name, run} of checks) {
    try { await run(); console.log('PASS: ' + name); }
    catch (error) { failed.push(name); console.error('FAIL: ' + name + '\n' + error.stack); }
  }
  assert.equal(failed.length, 0, failed.join('\n'));
  console.log(`PASS: ${checks.length} paper-effect contracts; ${experiments.length} canonical experiments across ${topics.length} topics`);
})().catch(error => { console.error(error); process.exitCode = 1; });
