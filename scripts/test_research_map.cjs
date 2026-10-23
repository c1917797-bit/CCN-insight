/* Research-map contracts: topic reachability, isolated filters and history restoration. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'original-reader/site/business_insight/cloud_core/compression.js'), 'utf8');
const bootstrap = fs.readFileSync(path.join(root, 'original-reader/site/business_insight/cloud_core/reader-bootstrap.js'), 'utf8');
const readRows = table => fs.readFileSync(path.join(root, 'data/compression/tables', table, 'rows.jsonl'), 'utf8')
  .trim().split('\n').map(JSON.parse).filter(entry => !entry.deleted).map(entry => entry.row);
const topics = readRows('ic_compression_topics');
const terms = readRows('ic_map_terms');
const routes = ['precision', 'selection', 'distillation', 'factorization'];
assert.equal(topics.length, 16, 'Preserve the complete topic inventory');

function extract(start, end) {
  const from = source.indexOf(start), to = source.indexOf(end, from);
  assert(from >= 0 && to > from, `Missing maintained function range: ${start}`);
  return source.slice(from, to);
}
function walk(node) {
  return [node, ...node.children.flatMap(walk)];
}
function node(tag, text = '', cls = '') {
  return {
    tagName: tag.toUpperCase(), textContent: String(text), className: cls,
    dataset: {}, attributes: {}, children: [], events: {}, hidden: false,
    parentElement: null, focusCount: 0, scrollCount: 0, isConnected: true,
    append(...items) {
      for (const item of items) { item.parentElement = this; this.children.push(item); }
    },
    replaceChildren(...items) { this.children = []; this.append(...items); },
    prepend(...items) { for (const item of items.reverse()) { item.parentElement = this; this.children.unshift(item); } },
    querySelectorAll(selector) { return selector === '[data-map-topic]' ? walk(this).filter(item => item.dataset.mapTopic) : selector === '[data-map-knowledge]' ? walk(this).filter(item => item.dataset.mapKnowledge) : []; },
    setAttribute(name, value) { this.attributes[name] = String(value); },
    addEventListener(name, handler) { this.events[name] = handler; },
    focus() { this.focusCount++; },
    scrollIntoView() { this.scrollCount++; },
    closest() { return {dataset: {viewPanel: 'topics'}}; },
    querySelector(selector) {
      if (selector === '[data-map-knowledge]') return walk(this).find(item => item.dataset.mapKnowledge) || null;
      const match = /^\[data-map-target-filter="([^"]*)"\]$/.exec(selector);
      return match ? walk(this).find(item => item.dataset.mapTargetFilter === match[1]) || null : null;
    }
  };
}
const map = node('div');
map.id = 'scientific-map';
const counts = {selectors: 0, map: 0, selection: 0, sections: 0};
const state = {
  data: {map_facets: [{}], map_terms: terms, compression_topics: topics},
  locale: 'zh', revision: 'reviewed', scopeReady: false, scope: 'unchanged-scope', period: '2026-10',
  mapTargetFilter: '', directionMode: false, focusTarget: '', focusMechanism: '', focusCells: [],
  object: 'legacy-object', cell: 'legacy-cell', method: 'legacy-method', all: false,
  view: 'topics', evidence: [{evidence_id: 'unchanged-evidence'}]
};
const context = {
  state, URL, location: {hash: '#view-topics', href: 'http://localhost/business_insight/cloud_core/index.html?month=2026-10'},
  expertLibraryRead: async () => JSON.parse(fs.readFileSync(path.join(root, 'dist/business_insight/cloud_core/local-content/expert-index.json'), 'utf8')),
  renderExpertLibrary() {},
  viewIds: {topics: ['map', 'knowledge'], sources: []},
  $: id => id === 'scientific-map' || id === 'map' ? map : walk(map).find(item => item.id === id) || null,
  ordered: rows => [...rows].sort((a, b) => (a.position || 0) - (b.position || 0)),
  title: row => row?.name_zh || row?.title_zh || '',
  textOf: (row, field) => row?.[field + '_zh'] || '',
  mapText: (zh, en) => zh,
  mapTerm: id => terms.find(term => term.term_id === id),
  element: node,
  renderFoundationLink() {},
  external(parent, url, label) { const link = node('a', label); link.href = url; parent.append(link); },
  LRICompressionVisuals: {icon: () => node('svg')},
  document: {dispatchEvent() { counts.sections++; }},
  Event: function Event() {},
  topicPage: () => false,
  showView(view) { state.view = view; },
  ensureOpenedDisclosuresLoaded() {},
  requestAnimationFrame(callback) { callback(); },
  renderSelectors() { counts.selectors++; },
  renderMap() { counts.map++; context.renderScientificMap(); map.hidden = state.directionMode; },
  renderSelection() { counts.selection++; },
  resetEvidence() { throw Error('Map filtering must not reset evidence'); },
  loadEvidence() { throw Error('Map filtering must not retrieve evidence'); },
  renderEvidence() { throw Error('Map filtering must not rerender evidence'); }
};
vm.createContext(context);
vm.runInContext([
  extract('function button(', 'function safeUrl('),
  extract('function scientificLink(', 'function selectScientificFocus('),
  extract('function mapTopicLabel(', 'function renderSelectors('),
  extract('function viewForTarget(', 'function disclosure(')
].join('\n'), context);
// The library has its own fetch/identity suite. Isolate map rendering from that
// independent component while hydrating real canonical-derived index data.
context.expertLibraryRead=async()=>JSON.parse(fs.readFileSync(path.join(root,'dist/business_insight/cloud_core/local-content/expert-index.json'),'utf8'));
context.renderExpertLibrary=()=>{};

context.renderScientificMap();
const topicLinks = () => walk(map).filter(item => item.dataset.compressionTopicRoute);
const byTopic = new Map(topicLinks().map(link => [link.dataset.compressionTopicRoute, link]));
assert.equal(topicLinks().length, 16);
assert.equal(byTopic.size, 16, 'Every legacy topic must have one reachable entry');
for (const topic of topics) {
  const link = byTopic.get(topic.compression_topic_id);
  assert(link, `Missing topic: ${topic.compression_topic_id}`);
  const url = new URL(link.href, 'https://ccn.example/business_insight/cloud_core/index.html');
  assert.equal(url.pathname, '/business_insight/cloud_core/topic.html');
  assert.equal(url.searchParams.get('topic'), topic.compression_topic_id);
  assert.equal(url.searchParams.get('month'), state.period);
  assert.equal(url.searchParams.get('scope'), state.scope);
}
assert.equal(walk(map).filter(item => item.className.split(' ').includes('research-map-primary')).length, 1);
assert.equal(walk(map).find(item => item.className.split(' ').includes('research-map-primary')).dataset.compressionTopicRoute, 'parameters-distillation');
assert(byTopic.has('activations-distillation') && byTopic.has('kv_cache-distillation'));
for (const route of routes) {
  assert(walk(map).some(item => item.id === 'route-' + route));
  assert.equal(context.viewForTarget('route-' + route), 'topics', 'Cold route hash must select the topic reader before DOM lookup');
  const from = bootstrap.indexOf('const params=new URLSearchParams(');
  const to = bootstrap.indexOf('const en=', from);
  assert(from >= 0 && to > from, 'Missing first-paint view selection');
  const cold = {location: {search: '?month=2026-10', hash: '#route-' + route,
    pathname: '/business_insight/cloud_core/index.html'}, URLSearchParams, Date};
  vm.createContext(cold);
  vm.runInContext(bootstrap.slice(from, to) + '\nglobalThis.selectedView = view;', cold);
  assert.equal(cold.selectedView, 'topics', 'First-paint bootstrap must request map data for cold route links');
}
assert(!walk(map).some(item => item.tagName === 'DETAILS'), 'Core and extended map routes must stay expanded');

// Changing any map filter must leave evidence, monthly scope and legacy filters intact.
for (const target of ['parameters', 'activations', 'kv_cache', '']) {
  const button = map.querySelector('[data-map-target-filter="' + target + '"]');
  assert(button, `Missing map filter: ${target}`);
  assert.equal(button.disabled, false, 'Map filter must work without a monthly scope');
  assert(!Object.hasOwn(button.dataset, 'scopeDependent'));
  const before = JSON.parse(JSON.stringify(state));
  const countBefore = {...counts};
  button.events.click();
  before.mapTargetFilter = target;
  assert.deepEqual(JSON.parse(JSON.stringify(state)), before, 'Filter must only change mapTargetFilter');
  assert.equal(counts.selectors, countBefore.selectors);
  assert.equal(counts.map, countBefore.map);
  assert.equal(counts.selection, countBefore.selection);
  assert(counts.sections > countBefore.sections, 'Filter must redraw the map and refresh its outline');
  const selected = map.querySelector('[data-map-target-filter="' + target + '"]');
  assert.equal(selected.attributes['aria-pressed'], 'true');
  assert.equal(selected.focusCount, 1, 'Redraw must restore keyboard focus to the active filter');
  if (target) {
    for (const link of topicLinks()) {
      assert(link.dataset.scientificTarget === target || link.dataset.compressionTopicRoute === 'parameters-distillation',
        'Filtering may retain the cross-target distillation main topic, but no unrelated cases');
    }
  }
}

// Simulate the state left by SPA topic navigation, followed by browser back.
for (const hash of ['view-topics', 'map', ...routes.map(route => 'route-' + route)]) {
  Object.assign(state, {directionMode: true, focusTarget: 'parameters', focusMechanism: 'precision',
    focusCells: ['legacy-cell'], object: 'legacy-object', cell: 'legacy-cell', method: 'legacy-method', all: false});
  state.mapTargetFilter = 'activations';
  map.hidden = true;
  context.location.hash = '#' + hash;
  const before = {...counts};
  context.revealHashTarget();
  assert.equal(state.directionMode, false, `Direction must close on return to ${hash}`);
  for (const field of ['focusTarget', 'focusMechanism', 'object', 'cell', 'method']) assert.equal(state[field], '', `${hash}: ${field}`);
  assert.equal(state.focusCells.length, 0);
  assert.equal(state.all, true);
  assert.equal(map.hidden, false, 'Restored map must be visible');
  assert.equal(counts.selectors, before.selectors + 1);
  assert.equal(counts.map, before.map + 1);
  assert.equal(counts.selection, before.selection + 1);
  assert.equal(state.scope, 'unchanged-scope');
  assert.equal(state.evidence[0].evidence_id, 'unchanged-evidence');
  if (hash.startsWith('route-')) {
    assert.equal(state.mapTargetFilter, '', 'Direct route navigation must reveal all related entries');
    assert.equal(walk(map).find(item => item.id === hash).scrollCount, 1);
  }
}

(async()=>{
 state.mapTargetFilter='';context.renderScientificMap();
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(map.dataset.mapKnowledgeReady,'true','Map evidence must be hydrated from the revision-bound index');
 const index=await context.expertLibraryRead();
 for(const item of map.querySelectorAll('[data-map-topic]')){
  const expected=index.cards.filter(c=>c.topic===item.dataset.mapTopic&&c.kind==='case');
  const coverage=walk(item).find(n=>n.className==='map-topic-coverage');
  assert(coverage&&coverage.textContent.startsWith(String(expected.length)+' '),'Case count must come from actual topic evidence');
  const shortcuts=walk(item).filter(n=>n.tagName==='A'&&n.parentElement?.className==='map-topic-methods');
  assert.equal(shortcuts.length,Math.min(3,expected.length));
  for(const link of shortcuts){const url=new URL(link.href,'http://localhost');assert.equal(url.searchParams.get('topic'),item.dataset.mapTopic);assert.equal(url.searchParams.get('scope'),state.scope);assert(expected.some(c=>url.hash==='#'+c.anchor),'Shortcut must land on an existing case');}
 }
 console.log('PASS: 16 reachable topics, four cold routes, isolated filters, history restoration and source-derived map shortcuts');
})().catch(error=>{console.error(error);process.exitCode=1;});
