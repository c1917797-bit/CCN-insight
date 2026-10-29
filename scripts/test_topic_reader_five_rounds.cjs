/* Topic-reader regressions. These checks do not replace browser or scientific review. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const reader = fs.readFileSync(path.join(root, 'original-reader/site/business_insight/cloud_core/compression.js'), 'utf8');
const rows = name => fs.readFileSync(path.join(root, 'data/compression/tables', name, 'rows.jsonl'), 'utf8')
  .trim().split('\n').map(JSON.parse).filter(entry => !entry.deleted).map(entry => entry.row);
const topics = rows('ic_compression_topics');
const cards = rows('ic_compression_topic_cards');
const refs = rows('ic_compression_topic_card_refs');
const sources = rows('cloud_core_sources');
const findSource = id => sources.find(source => source.source_id === id);
const extract = (start, end) => {
  const from = reader.indexOf(start), to = reader.indexOf(end, from);
  assert(from >= 0 && to > from, `Missing maintained function: ${start}`);
  return reader.slice(from, to);
};

// Deliberately small semantic DOM, sufficient for these maintained functions.
// Unsupported selectors fail, so a test cannot silently skip the target node.
class Node {
  constructor(tag, text = '', cls = '') {
    this.tagName = tag.toUpperCase(); this.ownText = String(text); this.className = cls;
    this.children = []; this.dataset = {}; this.attributes = {}; this.events = {};
    this.parentElement = null; this.id = ''; this.hidden = false;
    this.classList = {
      contains: name => this.className.split(/\s+/).includes(name),
      add: name => { if (!this.classList.contains(name)) this.className += ' ' + name; },
      toggle: (name, force) => { const active = force === undefined ? !this.classList.contains(name) : force; if (active) this.classList.add(name); else this.className = this.className.split(/\s+/).filter(value => value !== name).join(' '); return active; },
    };
  }
  get textContent() { return this.ownText + this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this.ownText = String(value); this.children = []; }
  get innerText() { return this.textContent; }
  get isConnected() { return true; }
  get childElementCount() { return this.children.filter(child => child.tagName !== '#TEXT').length; }
  get previousElementSibling() {
    const siblings = this.parentElement?.children || [];
    return siblings[siblings.indexOf(this) - 1] || null;
  }
  append(...items) {
    for (const item of items) {
      if (item.parentElement) item.remove();
      item.parentElement = this; this.children.push(item);
    }
  }
  prepend(...items) { for (const item of items.reverse()) { if (item.parentElement) item.remove(); item.parentElement = this; this.children.unshift(item); } }
  replaceChildren(...items) { this.children.forEach(item => { item.parentElement = null; }); this.children = []; this.ownText = ''; this.append(...items); }
  remove() { const parent = this.parentElement; if (parent) parent.children.splice(parent.children.indexOf(this), 1); this.parentElement = null; }
  replaceWith(item) { const parent = this.parentElement; const i = parent.children.indexOf(this); this.remove(); item.parentElement = parent; parent.children.splice(i, 0, item); }
  setAttribute(name, value) { this.attributes[name] = String(value); if (name === 'class') this.className = String(value); }
  getAttribute(name) { return this.attributes[name] ?? this[name] ?? null; }
  addEventListener(name, callback) { this.events[name] = callback; }
  matches(selector) {
    if (selector.includes(',')) return selector.split(',').some(part => this.matches(part.trim()));
    if (selector.startsWith('#')) return this.id === selector.slice(1);
    if (selector.startsWith('.')) return this.classList.contains(selector.slice(1));
    if (selector === 'section[id]') return this.tagName === 'SECTION' && !!this.id;
    if (selector === 'a[href]') return this.tagName === 'A' && !!this.href;
    if (selector === '[data-research-card]') return !!this.dataset.researchCard;
    if (/^[a-z][\w-]*$/i.test(selector)) return this.tagName.toLowerCase() === selector.toLowerCase();
    if (selector === 'p.meta') return this.tagName === 'P' && this.classList.contains('meta');
    throw Error('Unsupported test selector: ' + selector);
  }
  descendants() { return this.children.flatMap(child => [child, ...child.descendants()]); }
  querySelectorAll(selector) {
    if (selector === '.topic-report-sources > li') return this.descendants().filter(node => node.tagName === 'LI' && node.parentElement?.classList.contains('topic-report-sources'));
    if (selector === '.topic-dossier-citations a[href]') return this.descendants().filter(node => node.tagName === 'A' && node.href && node.parentElement?.classList.contains('topic-dossier-citations'));
    if (selector === ':scope > p.meta') return this.children.filter(node => node.matches('p.meta'));
    return this.descendants().filter(node => node.matches(selector));
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
}
const element = (tag, text = '', cls = '') => new Node(tag, text, cls);
const timers = new Map(), documentListeners = new Map();
let nextTimer = 0, currentDossier = null, currentTopic = null, currentView = 'overview';
const context = {
  element, mapText: (zh, en) => zh, title: row => row.title_zh || row.title || '',
  textOf: (row, field) => row[field + '_zh'] || '',
  document: {
    createTextNode: text => element('#text', text), createElementNS: (ns, tag) => element(tag),
    addEventListener(name, callback) { documentListeners.set(name, callback); },
    removeEventListener(name, callback) { if (documentListeners.get(name) === callback) documentListeners.delete(name); }, hidden: false,
  },
  location: {href: 'http://localhost/business_insight/cloud_core/topic.html?topic=kv_cache-precision', origin: 'http://localhost', pathname: '/business_insight/cloud_core/topic.html', search: '?topic=kv_cache-precision'},
  URL, URLSearchParams, Map, Set, topicExpertQueries: new Map(), requestAnimationFrame() {},
  state: {data: {compression_topics: topics}}, compressionTopicId: () => currentTopic,
  ordered: values => [...values].sort((a, b) => a.position - b.position),
  researchDossier: () => currentDossier, safeUrl: value => value,
  external(parent, url, label) { const a = element('a', label); a.href = url; parent.append(a); },
  researchHref: () => '/business_insight/cloud_core/topic.html?topic=' + currentTopic + '&view=mechanism',
  bindResearchJump: (link, id) => { link.href = '#' + id; },
  appendWeightStructuredText: (parent, text) => parent.append(element('p', text)),
  button(label, callback) { const control = element('button', label); control.addEventListener('click', callback); return control; },
  window: {matchMedia: () => ({matches: false})},
  setTimeout(callback) { const id = ++nextTimer; timers.set(id, callback); return id; },
  clearTimeout(id) { timers.delete(id); },
  renderExpertTopicEntry: () => false, weightTopicCitations() {}, researchView: () => currentView,
};
vm.createContext(context);
vm.runInContext([
  extract('function researchBlock(', 'function renderValidationPlan('),
  extract('function expertEvidenceScope(', 'function expertCardTools('),
  extract('function reviewedSourceUrl(', 'function renderDossierCards('),
  extract('function renderTopicOverview(', 'function renderTopicReportOutline('),
  extract('let topicMechanismDisposer=', 'function renderResearchFraming('),
  extract('function renderResearchFraming(', 'function renderResearchRoutes('),
  extract('function renderWeightResearchBackground(', 'function renderWeightQuantizationTopic('),
  extract('function renderResearchRoutes(', 'const routeEvidenceReaders='),
  extract('function compactResearchCitations(', 'function weightTopicCitations('),
].join('\n'), context);

const failures = [];
let checks = 0;
function check(name, run) {
  try { run(); checks++; }
  catch (error) { failures.push(`${name}: ${error.message}`); }
}

check('Keep every existing compression topic and its cited expert brief', () => {
  assert.equal(topics.length, 16);
  for (const topic of topics) {
    const brief = cards.find(card => card.card_id === topic.compression_topic_id + '__expert_brief');
    assert(brief && brief.claim_kind === 'research_analysis', topic.compression_topic_id);
    const own = refs.filter(ref => ref.card_id === brief.card_id);
    assert(own.length && own.every(ref => findSource(ref.source_id)), 'Unbound brief: ' + brief.card_id);
  }
});

check('Research blocks expose their content without details disclosure', () => {
  const block = context.researchBlock('regression-key', 'Visible evidence');
  assert.equal(block.tagName, 'SECTION');
  assert.equal(block.dataset.researchBlock, 'regression-key');
  assert.equal(block.querySelector('h4').textContent, 'Visible evidence');
  assert.equal(block.querySelectorAll('details').length, 0);
});

check('Weight background retains its explanation and hardware; scope remains a separate complete block', () => {
  currentTopic='parameters-precision';
  const frame=rows('ic_compression_research_frames').find(r=>r.compression_topic_id===currentTopic);
  currentDossier={frames:[frame],refs:refs.filter(r=>r.compression_topic_id===currentTopic),sources};
  context.weightTopicCards=(host,ids)=>ids.forEach(id=>{const card=cards.find(c=>c.card_id===id);assert(card,'Missing background card '+id);host.append(element('article',card.body_zh));});
  context.scientificLink=(target,method,label)=>{const a=element('a',label);a.href='topic.html?topic='+target+'-'+method;return a;};
  const host=element('section');
  const sub=(parent,id,zh)=>{const section=element('section');section.id='direction-'+id;section.append(element('h3',zh));parent.append(section);return section;};
  context.renderWeightResearchBackground(host,sub);
  assert.deepEqual(host.children.map(n=>n.id),['direction-background-overview','direction-value','direction-hardware-formats']);
  const intro=host.children[0];
  for(const paragraph of frame.why_zh.split('\n'))assert(intro.textContent.includes(paragraph),'Missing background paragraph');
  assert(intro.textContent.includes('舍入与裁剪造成的偏差'));
  assert.equal(host.querySelectorAll('details').length,0);
  assert(host.descendants().every(n=>!n.hidden),'Background should not be individually hidden');
  assert(intro.querySelector('.topic-dossier-citations').children.length>0,'Keep literature attribution');
  const scope=element('section');context.renderWeightResearchScope(scope,sub);
  assert.equal(scope.children[0].id,'direction-scope');
  assert(!scope.textContent.includes(frame.why_zh),'Do not repeat the introduction in scope');
});

check('Generic full topics keep seven readable chapters and mark analysis correctly', () => {
  for (const topic of topics.filter(topic => topic.compression_topic_id !== 'parameters-precision')) {
    const parent = element('main');
    const dossier = {cards: cards.filter(card => card.compression_topic_id === topic.compression_topic_id), refs: [], sources: []};
    context.renderTopicOverview(parent, topic, dossier);
    const chapters = parent.querySelectorAll('.research-overview-section');
    assert.equal(chapters.length, 7, topic.compression_topic_id);
    assert(chapters.every(chapter => !chapter.hidden), 'Hidden chapter in ' + topic.compression_topic_id);
    assert.equal(parent.querySelector('#research-overview-comparison').dataset.readingLayer, 'analysis', 'Comparison must not be labeled as primary facts');
    assert.equal(parent.querySelector('#research-overview-implications').dataset.readingLayer, 'conclusion');
  }
});

check('Evidence scope is card-local and never borrows a neighbour full review', () => {
  const own = {card_id: 'own'}, neighbour = {card_id: 'neighbour'};
  const dossier = {refs: [{card_id: own.card_id, source_id: 'a', review_depth: 'abstract_review'}, {card_id: neighbour.card_id, source_id: 'b', review_depth: 'section_review'}]};
  assert.equal(context.expertEvidenceScope(own, dossier).section, 0);
  assert.equal(context.expertEvidenceScope(own, dossier).refs.length, 1);
  assert.equal(context.expertEvidenceScope(neighbour, dossier).section, 1);
});

check('Visible case source strips bind their own source, version and review depth', () => {
  const kivi={canonical_url:'https://arxiv.org/abs/2402.02750'};
  assert.equal(context.reviewedSourceUrl(kivi,{observed_version:'2402.02750v2'}),'https://arxiv.org/html/2402.02750v2');
  assert.equal(context.reviewedSourceUrl(kivi,{observed_version:'v2'}),'https://arxiv.org/html/2402.02750v2');
  assert.equal(context.reviewedSourceUrl(kivi,{observed_version:'current_abstract'}),kivi.canonical_url);
  const sourceById = new Map(sources.map(source => [source.source_id, source]));
  for (const row of cards.filter(card => card.card_kind === 'case')) {
    const ownRefs = refs.filter(ref => ref.card_id === row.card_id), card = element('article');
    assert(ownRefs.length, 'Case without own references: ' + row.card_id);
    context.renderTopicSourceStrip(card, row, {refs, sources});
    const lines = card.querySelectorAll('.topic-source-line');
    assert.equal(lines.length, ownRefs.length, row.card_id);
    lines.forEach((line, i) => {
      const ref = ownRefs[i], source = sourceById.get(ref.source_id), link = line.querySelector('a[href]');
      assert.equal(line.dataset.sourceId, ref.source_id);
      const pinned = /(?:arXiv:\s*)?(\d{4}\.\d{4,5}v\d+)/i.exec(ref.observed_version || '');
      const paperId = /arxiv\.org\/(?:abs|html|pdf)\/(\d{4}\.\d{4,5})/.exec(source.canonical_url)?.[1];
      const bare = /^v\d+$/.test(ref.observed_version || '') && paperId ? paperId + ref.observed_version : '';
      assert.equal(link.href, pinned ? 'https://arxiv.org/html/' + pinned[1] : bare ? 'https://arxiv.org/html/' + bare : source.canonical_url,
        'Primary link must match its reviewed version when pinned');
      assert.equal(link.textContent, source.title);
      assert(line.textContent.includes(ref.observed_version === 'current_abstract' ? '摘要记录' : ref.observed_version));
      assert(line.textContent.includes(ref.checked_at));
      assert(line.textContent.includes(ref.review_depth === 'section_review' ? '指定章节核对' : '摘要级记录'));
    });
    assert.equal(card.querySelectorAll('details').length, 0);
  }
  const notCase = element('article');
  context.renderTopicSourceStrip(notCase, {card_id: 'not-a-case', card_kind: 'analysis'}, {refs, sources});
  assert.equal(notCase.childElementCount, 0, 'Do not add a primary-case banner to editorial analysis');
});

check('Mechanism walkthrough keeps every canonical step readable before playback', () => {
  const allSteps = rows('ic_compression_mechanism_steps');
  for (const topic of topics) {
    currentTopic = topic.compression_topic_id;
    const steps = allSteps.filter(step => step.compression_topic_id === currentTopic);
    currentDossier = {steps, refs: refs.filter(ref => ref.card_id.startsWith(currentTopic + '__')), sources};
    const parent = element('main'); context.renderMechanismDiagram(parent);
    if (!steps.length) {
      assert.equal(parent.childElementCount, 0, 'Do not manufacture mechanism stages when the maintained source has none');
      continue;
    }
    assert.equal(steps.length, 4, 'Use the maintained four-step contract: ' + currentTopic);
    const figure = parent.querySelector('.topic-mechanism-lab');
    assert(figure, currentTopic);
    assert.equal(figure.querySelectorAll('.topic-lab-step').length, steps.length);
    assert.equal(figure.querySelectorAll('details').length, 0);
    assert.equal(figure.querySelector('svg').getAttribute('aria-hidden'), 'true', 'Decorative glyphs must not replace accessible mechanism text');
    for (const step of steps) {
      assert(figure.textContent.includes(step.label_zh), 'Missing step title: ' + step.step_id);
      assert(figure.textContent.includes(step.body_zh), 'Missing mechanism text: ' + step.step_id);
    }
    assert(figure.querySelectorAll('li').every(item => !item.hidden), 'Playback must not conceal the other steps');
    assert(figure.querySelector('figcaption').textContent.includes('不表示实测压缩比例'), 'Abstract glyph size must not imply a measured ratio');
  }
});

check('Walkthrough controls select, pause and dispose timers without hiding evidence', () => {
  currentTopic = 'kv_cache-precision';
  currentDossier = {steps: rows('ic_compression_mechanism_steps').filter(step => step.compression_topic_id === currentTopic), refs, sources};
  const parent = element('main'); context.renderMechanismDiagram(parent);
  const figure = parent.querySelector('.topic-mechanism-lab'), buttons = figure.querySelectorAll('.topic-lab-step'), toggle = figure.querySelector('.topic-lab-toggle');
  buttons[2].events.click();
  assert.equal(buttons[2].getAttribute('aria-pressed'), 'true');
  assert.equal(buttons[0].getAttribute('aria-pressed'), 'false');
  assert(figure.querySelector('.topic-lab-progress').textContent.startsWith('03 / 04'));
  toggle.events.click();
  assert.equal(figure.dataset.playing, 'true');
  assert.equal(timers.size, 1);
  toggle.events.click();
  assert.equal(figure.dataset.playing, 'false');
  assert.equal(timers.size, 0);
  toggle.events.click();
  context.renderMechanismDiagram(element('main'));
  assert.equal(timers.size, 0, 'Rerender left the previous player timer running');
  assert.equal(documentListeners.size, 1, 'Rerender duplicated document listeners');
});

check('An unverified mechanism remains a research question in text and data', () => {
  currentDossier = {...currentDossier, steps: currentDossier.steps.map((step, i) => i === 0 ? {...step, claim_status: 'research_question'} : step)};
  const parent = element('main'); context.renderMechanismDiagram(parent);
  const figure = parent.querySelector('.topic-mechanism-lab');
  assert(figure.querySelector('h3').textContent.includes('待建立证据'));
  assert(figure.querySelector('figcaption').textContent.includes('待验证'));
  assert(figure.querySelector('figcaption').textContent.includes('不代表已实现的算子、压缩率或性能'));
  assert.equal(figure.querySelector('li').dataset.claimKind, 'research_analysis');
});

check('Full topics link to the one evidence card while individual routes retain full text', () => {
  const allRoutes = rows('ic_compression_research_routes').filter(route => route.compression_topic_id !== 'parameters-precision');
  for (const topicId of new Set(allRoutes.map(route => route.compression_topic_id))) {
    currentTopic = topicId;
    const routes = allRoutes.filter(route => route.compression_topic_id === topicId);
    currentDossier = {routes, cards: cards.filter(card => card.compression_topic_id === topicId), refs, sources};
    currentView = 'overview';
    const complete = element('main'); context.renderResearchRoutes(complete);
    for (const route of routes) {
      const original = cards.find(card => card.card_id === route.supporting_card_id);
      assert(original, 'No maintained supporting card: ' + route.route_id);
      const links = complete.querySelectorAll('a[href]');
      assert(links.some(link => link.href === '#research-card-' + original.card_id), 'Full topic must link to its already displayed supporting card: ' + route.route_id);
      assert(!complete.textContent.includes(original.body_zh), 'Full topic repeated the supporting card body: ' + route.route_id);
    }
    currentView = 'mechanism';
    const individual = element('main'); context.renderResearchRoutes(individual);
    for (const route of routes) assert(individual.textContent.includes(cards.find(card => card.card_id === route.supporting_card_id).body_zh), 'Individual route lost its supporting evidence: ' + route.route_id);
  }
  currentView = 'overview';
});

check('Numbered citations resolve by source identity and retain a return path', () => {
  const topic = topics.find(topic => topic.compression_topic_id === 'kv_cache-precision');
  const ownCards = cards.filter(card => card.compression_topic_id === topic.compression_topic_id && card.card_kind === 'case');
  const referenced = [...new Set(refs.filter(ref => ownCards.some(card => card.card_id === ref.card_id)).map(ref => ref.source_id))].map(findSource);
  assert(referenced.length >= 2, 'Use two real independent sources');
  const parent = element('main');
  for (const source of referenced.slice(0, 2)) {
    const article = element('article'), note = element('p', 'Source-grounded result', 'meta'), group = element('div', '', 'topic-dossier-citations');
    const citation = element('a', source.title); citation.href = source.canonical_url; citation.title = source.title;
    group.append(citation); article.append(note, group); parent.append(article);
  }
  const bibliography = element('ol', '', 'topic-report-sources');
  for (const source of referenced.slice(0, 2).reverse()) {
    const li = element('li'), link = element('a', source.title); link.href = source.canonical_url; li.append(link); bibliography.append(li);
  }
  parent.append(bibliography); context.compactResearchCitations(parent);
  const citations = parent.querySelectorAll('.research-citation-link');
  assert.equal(citations.length, 2);
  citations.forEach((citation, i) => {
    const destination = parent.querySelector(citation.href);
    assert(destination, 'Citation target is absent');
    assert.equal(destination.querySelector('a[href]').href, referenced[i].canonical_url, 'Citation points to the neighbouring source');
    assert.equal(destination.querySelector('.research-citation-return').href, '#' + citation.id);
  });
});

assert.equal(failures.length, 0, failures.join('\n'));
console.log(`PASS: ${checks} topic-reader contracts; inventory, open content, chapter semantics, source identity, walkthrough accessibility and citations`);
