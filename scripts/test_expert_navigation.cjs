/* A reachable asynchronous card anchor must also become the scroll destination. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'original-reader/site/business_insight/cloud_core/compression.js'), 'utf8');
const rows = name => fs.readFileSync(path.join(root, 'data/compression/tables', name, 'rows.jsonl'), 'utf8')
  .trim().split('\n').map(JSON.parse).filter(row => !row.deleted).map(row => row.row);
const topic = rows('ic_compression_topics').find(row => row.compression_topic_id === 'parameters-selection');
const card = rows('ic_compression_topic_cards').find(row => row.compression_topic_id === topic.compression_topic_id && row.card_kind === 'case');
assert(topic && card, 'Use an actual generic-topic case as the navigation regression');
const targetId = 'research-card-' + card.card_id;

function extract(start, end) {
  const from = source.indexOf(start), to = source.indexOf(end, from);
  assert(from >= 0 && to > from, 'Missing maintained function: ' + start);
  return source.slice(from, to);
}
function element(tag, text = '') {
  return {
    tagName: tag.toUpperCase(), textContent: text, id: '', dataset: {}, children: [],
    hidden: false, parentElement: null, scrollCount: 0, focusCount: 0, events: {}, classList: {add() {}},
    append(...items) { for (const item of items) { item.parentElement = this; this.children.push(item); } },
    insertBefore(item, before) { item.parentElement = this; this.children.splice(this.children.indexOf(before), 0, item); },
    setAttribute() {},
    addEventListener(name, callback) { this.events[name] = callback; },
    querySelector(selector) {
      const data = /^\[data-([a-z-]+)="([^"]*)"\]$/.exec(selector);
      assert(data, 'Fixture selector not implemented: ' + selector);
      const key = data[1].replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
      const walk = node => node.children.flatMap(child => [child, ...walk(child)]);
      return walk(this).find(node => node.dataset[key] === data[2]) || null;
    },
    closest() { return null; },
    scrollIntoView(options) { this.scrollCount++; this.scrollOptions = options; },
    focus(options) { this.focusCount++; this.focusOptions = options; },
  };
}
const parent = element('div'), target = element('article');
target.id = targetId;
target.dataset.researchCard = card.card_id;
const state = {
  revision: 'test-revision', locale: 'zh', period: '2026-10', scope: '',
  focusTarget: topic.target_term_id, focusMechanism: topic.method_term_id,
  referencePending: false,
  data: {compression_topics: [topic], compression_topic_concepts: [], source_refs: []},
};
const context = {
  state, location: {pathname: '/business_insight/cloud_core/topic.html', search: '?topic=' + topic.compression_topic_id, hash: '#' + targetId},
  document: {dispatchEvent() {}, title: ''}, Event: function Event() {},
  history: {replaceState(state, title, url) { this.url = url; }},
  $: id => id === targetId ? target : null,
  element, title: row => row?.title_zh || row?.name_zh || '',
  textOf: (row, field) => row?.[field + '_zh'] || '', mapText: (zh, en) => zh,
  compressionTopicId: () => topic.compression_topic_id,
  topicPage: () => true, researchView: () => 'overview',
  researchHref: () => '#direction-routes', viewForTarget: () => 'topics',
  researchDossier: () => ({cards: [card], sources: [], refs: [], frames: [], routes: []}),
  topicSectionRow: () => ({evidence_url: 'https://example.com/taxonomy'}),
  techniquesForCell: () => [], linkedLineages: () => [], ordered: values => values,
  mapTerm: id => ({name_zh: id}), scientificLink: () => element('a'),
  researchBlock: () => element('div'),
  renderDossierCards(host, kind) { if (kind === 'papers') host.append(target); },
  renderRouteEvidence: () => null,
  requestAnimationFrame(callback) { callback(); },
  showView() {}, ensureOpenedDisclosuresLoaded() {}, ensureResearchDossier() {},
  renderFoundationLink() {}, researchNav() {}, renderTopicOverview() {},
  renderResearchFraming() {}, renderTopicTargetDiagram() {}, renderMechanismDiagram() {},
  renderResearchRoutes() {}, renderTopicIndustry() {}, external() {},
  composeResearchOverview() {}, renderTopicCatalogue() {}, compactResearchCitations() {}, applyResearchView() {},
};
vm.createContext(context);
vm.runInContext([
  extract('function revealHashTarget(', 'function disclosure('),
  extract('function bindResearchJump(', '// Topic facts stay'),
  extract('function renderCompressionTopic(', 'function validateTopicEvent('),
].join('\n'), context);

const failures = [];
function check(name, run) {
  try { run(); }
  catch (error) { failures.push(name + ': ' + error.message); }
}
check('Generic topic render restores the exact card after asynchronous content load', () => {
  target.scrollCount = 0;
  context.renderCompressionTopic(parent, {cell_id: 'canonical-navigation-context'});
  assert(target.parentElement, 'The source card must be rendered before scrolling');
  assert(target.scrollCount > 0, 'Card exists but generic renderer did not scroll to the research-card hash');
  assert.equal(target.scrollOptions.block, 'start');
});
check('Hash restoration also supports a visible research-card target', () => {
  target.scrollCount = 0;
  context.revealHashTarget(targetId);
  assert(target.scrollCount > 0, 'revealHashTarget ignored the research-card hash');
  assert.equal(target.scrollOptions.block, 'start');
});
check('A same-page evidence jump reaches and focuses the exact real source card', () => {
  const link = element('a');
  context.bindResearchJump(link, targetId);
  assert.equal(link.href, '#' + targetId);
  assert.equal(typeof link.events.click, 'function', 'The real jump helper must bind navigation');
  target.scrollCount = 0; target.focusCount = 0;
  let prevented = false, stopped = false;
  link.events.click({button: 0, preventDefault() { prevented = true; }, stopPropagation() { stopped = true; }});
  assert(prevented && stopped, 'Internal jump must be handled once');
  assert(target.scrollCount > 0, 'Same-page link did not scroll to its source card');
  assert.equal(target.scrollOptions.block, 'start');
  assert.equal(target.focusCount, 1, 'Jump must transfer keyboard focus');
  assert.equal(target.focusOptions.preventScroll, true);
  assert(context.history.url.endsWith('#' + targetId));
});

// A full reader can already hold map data while still showing another view.
// showView must mount the library after setting state.view to topics; testing
// only a cold map load misses the sources -> reports -> updates -> topics path.
const viewNodes = new Map(['reading-controls', 'reading-context', 'judgment-basis', 'scientific-map']
  .map(id => [id, element('div')]));
let hasLibrary = false, mapRenderCount = 0, standaloneTopic = false;
viewNodes.get('scientific-map').querySelector = selector => selector === '.expert-library' && hasLibrary ? element('section') : null;
const viewState = {
  view: 'updates', revision: 'loaded-revision', readerMode: 'full', directionMode: false,
  focusTarget: '', data: {map_facets: [{}]}, profile: {}, scopeReady: true,
  evidencePage: {}, evidenceBusy: false, directoryDeferred: false,
};
const viewContext = {
  state: viewState, viewIds: {sources: [], topics: [], updates: [], home: [], reports: []},
  topicPage: () => standaloneTopic,
  $: id => viewNodes.get(id),
  document: {body: {dataset: {}}, querySelector: () => null, querySelectorAll: () => [], dispatchEvent() {}},
  location: {hash: '#view-updates'}, Event: function Event() {},
  refreshSynthesis() {}, refreshImportedPapers() {}, renderViewPurpose() {},
  mapText: (zh, en) => zh,
  renderScientificMap() { mapRenderCount++; hasLibrary = true; },
  start() { throw Error('Already loaded full reader should not restart'); },
  loadEvidence() { throw Error('View switch should reuse loaded evidence'); },
};
vm.createContext(viewContext);
vm.runInContext(extract('function showView(', 'function renderReadingGuide('), viewContext);
check('Switching loaded updates to topics mounts the missing research library', () => {
  hasLibrary = false;
  mapRenderCount = 0;
  viewContext.showView('topics');
  assert.equal(viewState.view, 'topics');
  assert.equal(mapRenderCount, 1, 'Loaded map appeared without mounting the research library');
  assert(hasLibrary);
});
check('Returning to topics preserves an already mounted research library', () => {
  const before = mapRenderCount;
  hasLibrary = true;
  viewContext.showView('topics');
  assert.equal(mapRenderCount, before, 'Existing research library must not be rebuilt on every showView call');
});
check('Sources view does not mount or request the research library', () => {
  const before = mapRenderCount;
  hasLibrary = false;
  viewContext.showView('sources');
  assert.equal(viewState.view, 'sources');
  assert.equal(mapRenderCount, before, 'Sources must not initialize the expert index');
  assert.equal(hasLibrary, false);
});
check('Focused topic and unloaded taxonomy do not rebuild the map', () => {
  const before = mapRenderCount;
  viewState.directionMode = true;
  viewContext.showView('topics');
  viewState.directionMode = false;
  viewState.focusTarget = topic.target_term_id;
  viewContext.showView('topics');
  viewState.focusTarget = '';
  viewState.data.map_facets = [];
  viewContext.showView('topics');
  assert.equal(mapRenderCount, before);
  viewState.data.map_facets = [{}];
  standaloneTopic = true;
  viewContext.showView('topics');
  assert.equal(mapRenderCount, before, 'Standalone topic reader must not initialize the map library');
});
assert.equal(failures.length, 0, failures.join('\n'));
console.log('PASS: exact card hash navigation; library mounts after view changes, reuses existing content and stays isolated from sources');
