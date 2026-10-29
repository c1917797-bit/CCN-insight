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
  const node = {
    tagName: tag.toUpperCase(), textContent: text, id: '', dataset: {}, children: [],
    className: '', attributes: {}, open: false,
    hidden: false, parentElement: null, scrollCount: 0, focusCount: 0, events: {},
    append(...items) { for (const item of items) { item.parentElement = this; this.children.push(item); } },
    insertBefore(item, before) { item.parentElement = this; this.children.splice(this.children.indexOf(before), 0, item); },
    setAttribute(name, value) { this.attributes[name] = String(value); },
    addEventListener(name, callback) { this.events[name] = callback; },
    querySelector(selector) {
      const data = /^\[data-([a-z-]+)="([^"]*)"\]$/.exec(selector);
      assert(data, 'Fixture selector not implemented: ' + selector);
      const key = data[1].replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
      const walk = node => node.children.flatMap(child => [child, ...walk(child)]);
      return walk(this).find(node => node.dataset[key] === data[2]) || null;
    },
    closest() { return null; },
    scrollIntoView(options) {
      this.scrollCount++; this.scrollOptions = options; this.visibleAtScroll = true;
      for (let ancestor = this; ancestor; ancestor = ancestor.parentElement) {
        if (ancestor.tagName === 'DETAILS' && !ancestor.open) this.visibleAtScroll = false;
      }
    },
    focus(options) { this.focusCount++; this.focusOptions = options; },
  };
  node.classList = {
    add(...names) { node.className = [...new Set([...node.className.split(/\s+/).filter(Boolean), ...names])].join(' '); },
    contains(name) { return node.className.split(/\s+/).includes(name); },
  };
  return node;
}
const parent = element('div'), target = element('article');
target.id = targetId;
target.dataset.researchCard = card.card_id;
const state = {
  revision: 'test-revision', locale: 'zh', period: '2026-10', scope: '',
  focusTarget: topic.target_term_id, focusMechanism: topic.method_term_id,
  referencePending: false,
  disclosureOpen: new Map(),
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
  extract('function openResearchTarget(', 'function revealHashTarget('),
  extract('function revealHashTarget(', 'function disclosure('),
  extract('function bindResearchJump(', '// Topic facts stay'),
  extract('function configureWeightCase(', 'function weightTopicCards('),
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

// Use actual weight-route identities: an external bookmark, the evidence
// navigator and a citation return must all reveal the same complete case.
const weightRoutes = rows('ic_compression_research_routes').filter(row => row.compression_topic_id === 'parameters-precision');
assert(weightRoutes.length >= 2, 'Exercise two actual weight methods in one accordion');
const weightContainer = element('section'), weightTargets = new Map();
const weightCases = weightRoutes.slice(0, 2).map(route => {
  const node = element('details');
  node.id = 'research-card-' + route.supporting_card_id;
  node.dataset.researchCard = route.supporting_card_id;
  context.configureWeightCase(node, route.title_zh);
  const alias = element('span'); alias.id = 'weight-route-' + route.route_id; node.append(alias);
  const quote = element('a'); quote.id = 'research-cite-' + route.route_id; node.append(quote);
  weightContainer.append(node);
  for (const target of [node, alias, quote]) weightTargets.set(target.id, target);
  return {node, alias, quote};
});
context.$ = id => weightTargets.get(id) || (id === targetId ? target : null);
context.document.getElementById = context.$;
const resetWeightCases = () => {
  for (const {node, alias, quote} of weightCases) {
    node.open = false;
    for (const target of [node, alias, quote]) { target.scrollCount = 0; target.focusCount = 0; }
  }
};
for (const anchorKind of ['node', 'alias']) {
  check('A direct ' + (anchorKind === 'node' ? 'research-card' : 'weight-route') + ' hash opens the exact collapsed method before scrolling', () => {
    resetWeightCases();
    const [previous, current] = weightCases;
    previous.node.open = true;
    const destination = current[anchorKind];
    context.location.hash = '#' + destination.id;
    context.revealHashTarget();
    assert.equal(current.node.open, true, 'Hash destination remains inside a closed case');
    assert.equal(previous.node.open, false, 'Hash navigation must close the previously open sibling');
    assert.equal(destination.scrollCount, 1, 'Both old anchors must remain exact scroll destinations');
    assert.equal(destination.visibleAtScroll, true, 'Open the disclosure before attempting to scroll');
    assert.equal(destination.scrollOptions.block, 'start');
  });
}
check('Evidence and saved-case links reveal a collapsed weight method and transfer focus', () => {
  resetWeightCases();
  const [previous, current] = weightCases; previous.node.open = true;
  const link = element('a'); context.bindResearchJump(link, current.node.id);
  let prevented = false, stopped = false;
  link.events.click({button: 0, preventDefault() { prevented = true; }, stopPropagation() { stopped = true; }});
  assert(prevented && stopped, 'The evidence navigator must handle its jump once');
  assert.equal(current.node.open, true);
  assert.equal(previous.node.open, false);
  assert.equal(current.node.visibleAtScroll, true, 'Evidence navigation must reveal its destination before scrolling');
  assert.equal(current.node.scrollCount, 1);
  assert.equal(current.node.focusCount, 1);
  assert.equal(current.node.focusOptions.preventScroll, true);
  assert(context.history.url.endsWith('#' + current.node.id));
});
vm.runInContext('function handleCitationClick(event){\n' + extract(' const citation=(event.composedPath?.()', '  if(!event.defaultPrevented') + '\n}', context);
check('Returning from a bibliography entry opens the cited method before focusing its inline reference', () => {
  resetWeightCases();
  const [previous, current] = weightCases; previous.node.open = true;
  const back = element('a'); back.hash = '#' + current.quote.id; back.dataset.researchCitation = 'true';
  let prevented = false;
  context.handleCitationClick({button: 0, composedPath: () => [back], preventDefault() { prevented = true; }});
  assert(prevented, 'The real citation-return handler must intercept the internal reference');
  assert.equal(current.node.open, true);
  assert.equal(previous.node.open, false);
  assert.equal(current.quote.visibleAtScroll, true, 'The citation must be visible before it receives focus');
  assert.equal(current.quote.scrollCount, 1);
  assert.equal(current.quote.scrollOptions.block, 'center');
  assert.equal(current.quote.focusCount, 1);
});

// A full reader can already hold map data while still showing another view.
// showView must mount the library after setting state.view to topics; testing
// only a cold map load misses the sources -> reports -> updates -> topics path.
const viewNodes = new Map(['reading-controls', 'reading-context', 'judgment-basis', 'scientific-map']
  .map(id => [id, element('div')]));
let hasLibrary = false, mapRenderCount = 0, standaloneTopic = false;
viewNodes.get('scientific-map').querySelector = selector => selector === '.compression-map-heading' && hasLibrary ? element('section') : null;
const viewState = {
  view: 'updates', revision: 'loaded-revision', readerMode: 'full', directionMode: false,
  focusTarget: '', data: {map_facets: [{}]}, profile: {}, scopeReady: true,
  evidencePage: {}, evidenceBusy: false, directoryDeferred: false,
};
const viewContext = {
  state: viewState, viewIds: {sources: [], topics: [], updates: [], home: [], reports: []},
  topicPage: () => standaloneTopic,
  $: id => viewNodes.get(id),
  document: {documentElement:{dataset:{}}, body: {dataset: {}}, querySelector: () => null, querySelectorAll: () => [], dispatchEvent() {}},
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
console.log('PASS: exact card and legacy route hashes; collapsed evidence and citation returns; library mounts after view changes and stays isolated from sources');
