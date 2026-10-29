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
const links=walk(map).filter(item=>item.tagName==='A');
assert.equal(links.length,1,'A map must not duplicate the topic directory or paper links');
assert.equal(links[0].href,'#view-library','The map has one clear onward destination');
assert.equal(walk(map).filter(item=>item.dataset.mapRoute).length,4);
assert(!walk(map).some(item=>['BUTTON','INPUT','SELECT','DETAILS'].includes(item.tagName)),'The complete map is readable without filters or disclosures');
assert(!walk(map).some(item=>item.dataset.mapTopic),'Detailed topic entries belong to the library');
const correspondence=walk(map).filter(item=>item.dataset.mapCorrespondence);
assert.equal(correspondence.length,topics.length,'Map includes every canonical topic once');
assert.deepEqual(correspondence.map(item=>item.dataset.mapCorrespondence).sort(),topics.map(topic=>topic.compression_topic_id).sort());
for(const topic of topics){
 const name=correspondence.find(item=>item.dataset.mapCorrespondence===topic.compression_topic_id);
 assert.equal(name.textContent,topic.title_zh,'Use the topic title without a second editable label');
 if(routes.includes(topic.method_term_id)){
  assert.equal(name.parentElement.dataset.mapObject,topic.target_term_id,'Do not transpose compression targets');
  assert.equal(name.parentElement.dataset.mapMethod,topic.method_term_id,'Do not transpose methods');
 }
}
const matrixRows=walk(map).filter(item=>item.tagName==='TR'&&item.dataset.mapObject);
assert.deepEqual(matrixRows.map(item=>item.dataset.mapObject),['parameters','activations','kv_cache']);
assert.equal(walk(map).filter(item=>item.tagName==='TD').length,12,'Three targets by four core techniques');
assert(walk(map).some(item=>item.textContent===terms.find(t=>t.term_id==='distillation').boundary_zh),'Explain the training/structure boundary for distillation');
assert(walk(map).some(item=>item.className==='compression-map-matrix-scroll'&&item.attributes.tabindex==='0'),'Allow keyboard scrolling on narrow screens');
for(const route of routes){
 const term=terms.find(t=>t.term_id===route),card=walk(map).find(n=>n.dataset.mapRoute===route);
 for(const field of ['map_summary_zh','map_caveat_zh','map_notation_zh'])assert(walk(card).some(n=>n.textContent===term[field]),'Map copy must come from the maintained taxonomy');
}
for (const route of routes) {
  assert(walk(map).some(item => item.id === 'route-' + route));
  assert.equal(context.viewForTarget('route-' + route), 'topics', 'Cold route hash must select the topic reader before DOM lookup');
  const from = bootstrap.indexOf('const params=new URLSearchParams(');
  const to = bootstrap.indexOf('const en=', from);
  assert(from >= 0 && to > from, 'Missing first-paint view selection');
  const cold = {location: {search: '?month=2026-10', hash: '#route-' + route,
    pathname: '/business_insight/cloud_core/index.html'}, URLSearchParams, Date, document:{documentElement:{dataset:{}}}};
  vm.createContext(cold);
  vm.runInContext(bootstrap.slice(from, to) + '\nglobalThis.selectedView = view;', cold);
  assert.equal(cold.selectedView, 'topics', 'First-paint bootstrap must request map data for cold route links');
}
assert(!walk(map).some(item => item.tagName === 'DETAILS'), 'Core and extended map routes must stay expanded');

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

// Legacy deep links to detailed references now belong to the topic library.
for(const id of ['expert-library','representative-routes','knowledge','map-references'])assert.equal(context.viewForTarget(id),'library');
for(const name of ['index.html','topic.html','monthly.html']){
 const html=fs.readFileSync(path.join(root,'original-reader/site/business_insight/cloud_core',name),'utf8');
 const mapPanel=html.split('<div data-view-panel="topics"')[1].split('<div data-view-panel="library"')[0];
 const libraryPanel=html.split('<div data-view-panel="library"')[1].split('<div data-view-panel="updates"')[0];
 assert(!mapPanel.includes('id="representative-routes"')&&!mapPanel.includes('id="knowledge"'),'Map contains no second research catalogue');
 assert(libraryPanel.includes('id="representative-routes"')&&libraryPanel.includes('id="knowledge"'),'Preserve detailed references in the library');
}
console.log('PASS: four routes, three compression targets, all 16 canonical topic names, distillation boundary, one onward link and legacy history');
