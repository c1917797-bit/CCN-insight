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

check('Weight background retains its full explanation and hardware without another scope block', () => {
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
});

const weightGroups = {
  representation: ['representation', 'codes', 'float'],
  quality: ['calibration', 'joint', 'recovery'],
  execution: ['execution'],
};
const weightFrame = rows('ic_compression_research_frames').find(row => row.compression_topic_id === 'parameters-precision');
const weightLandscape = cards.filter(card => card.card_id.startsWith('parameters-precision__landscape_'));
function renderWeightThreads(locale, view = 'overview') {
  const dossier = {frames: [weightFrame], cards: cards.filter(card => card.compression_topic_id === 'parameters-precision'), refs, sources};
  const page = new URL('http://localhost/business_insight/cloud_core/topic.html?topic=parameters-precision&month=2026-10&scope=ic-2026-10-model-reviewed-20261029-v1&view=' + view);
  const local = {
    element, URL, URLSearchParams, document: {createTextNode: text => element('#text', text)},
    location: {href: page.href, search: page.search},
    state: {period: page.searchParams.get('month'), scope: page.searchParams.get('scope')},
    compressionTopicId: () => 'parameters-precision',
    mapText: (zh, en) => locale === 'en' ? en : zh,
    title: row => row['title_' + locale] || row.title_zh || '',
    textOf: (row, field) => row?.[field + '_' + locale] || row?.[field + '_zh'] || '',
    researchDossier: () => dossier, safeUrl: value => value,
    bindResearchJump: (link, id) => { link.href = '#' + id; },
    renderTopicSourceStrip: context.renderTopicSourceStrip,
  };
  vm.createContext(local);
  vm.runInContext([
    extract('function researchView(', 'function researchNav('),
    extract('function appendResearchText(', 'function renderGroupedKnowledge('),
    extract('function weightTopicCitations(', 'function configureWeightCase('),
    extract('function weightTopicCards(', 'function weightTopicRoutes('),
    extract('function renderWeightResearchBackground(', 'function renderWeightQuantizationTopic('),
  ].join('\n'), local);
  const root = element('main'), challenges = element('section'), landscape = element('section');
  local.renderWeightChallenges(challenges, dossier);
  local.renderWeightRouteLandscape(landscape, dossier);
  root.append(challenges, landscape);
  return {root, challenges, landscape, local, dossier};
}

check('Real weight research data covers three questions and all seven approaches once in both languages', () => {
  assert(weightFrame, 'Keep the maintained weight research frame');
  const expectedIds = Object.values(weightGroups).flat().map(slug => 'parameters-precision__landscape_' + slug);
  assert.equal(weightLandscape.length, 7);
  assert.deepEqual(weightLandscape.map(card => card.card_id).sort(), [...expectedIds].sort());
  for (const [group, slugs] of Object.entries(weightGroups)) {
    for (const slug of slugs) {
      assert.equal(weightLandscape.find(card => card.card_id === 'parameters-precision__landscape_' + slug).challenge_group, group, 'Wrong primary contribution group: ' + slug);
    }
  }
  for (const locale of ['zh', 'en']) {
    assert.equal(weightFrame['challenge_' + locale].split(/\n+/).filter(Boolean).length, 3, 'Do not restore a fourth research route: ' + locale);
    assert(weightFrame['technical_summary_' + locale]?.trim(), 'Keep the technical thesis: ' + locale);
    assert(weightFrame['comparison_basis_' + locale]?.trim(), 'Keep shared complete-cost conditions: ' + locale);
    const {local, dossier} = renderWeightThreads(locale), threads = local.weightResearchThreads(dossier);
    assert.deepEqual(Array.from(threads, thread => thread.key), Object.keys(weightGroups));
    assert.deepEqual(Array.from(threads, thread => thread.cards.length), [3, 3, 1]);
    assert.deepEqual(Array.from(threads, thread => thread.number), ['01', '02', '03']);
    const expectedTitles = locale === 'zh' ? ['表示与编码', '误差与质量', '执行协同'] : ['Representation and coding', 'Error and quality', 'Execution co-design'];
    assert.deepEqual(Array.from(threads, thread => thread.title), expectedTitles);
    assert(threads.every(thread => thread.problem.trim()), 'Each question must retain its explanation');
    assert.deepEqual(Array.from(threads, thread => Array.from(thread.cards, card => card.card_id)).flat().sort(), [...expectedIds].sort());
  }
});

check('Every weight challenge reaches its own approach cards and each group returns to the matching challenge', () => {
  for (const locale of ['zh', 'en']) {
    const {root, challenges, landscape} = renderWeightThreads(locale);
    const map = challenges.querySelector('.weight-thread-map'), groups = landscape.querySelectorAll('.weight-route-thread');
    assert.equal(map.children.length, 3);
    assert.equal(groups.length, 3);
    for (const [key, slugs] of Object.entries(weightGroups)) {
      const question = root.querySelector('#weight-challenge-' + key), group = root.querySelector('#weight-thread-' + key);
      assert(question && group, 'Missing stable question/group destination: ' + key);
      assert.equal(question.dataset.challengeGroup, key);
      assert.equal(group.dataset.challengeGroup, key);
      const destinations = slugs.map(slug => '#research-card-parameters-precision__landscape_' + slug);
      assert.deepEqual(question.querySelectorAll('a[href]').map(link => link.href), destinations);
      for (const href of destinations) {
        const target = root.querySelector(href);
        assert(target, 'A challenge link lost its existing card anchor: ' + href);
        assert.equal(target.parentElement, group, 'A challenge linked to the wrong contribution group: ' + href);
        assert.equal(root.descendants().filter(node => node.id === href.slice(1)).length, 1, 'Do not duplicate the canonical card to create navigation');
      }
      const back = group.children[0].querySelector('a[href]');
      assert.equal(back.href, '#' + question.id);
      assert.equal(root.querySelector(back.href), question);
    }
    const cost = challenges.querySelector('#weight-comparison-basis');
    assert(cost, 'Do not discard complete-cost accounting when merging four challenges into three');
    assert.equal(cost.tagName, 'ASIDE');
    assert.equal(cost.parentElement, challenges, 'Complete cost belongs outside the three-question map');
    assert.equal(cost.dataset.challengeGroup, undefined, 'Complete cost is a common constraint, not a fourth route');
    assert.equal(root.querySelectorAll('.weight-common-cost').length, 1);
    for (const line of weightFrame['comparison_basis_' + locale].split(/\n+/).filter(Boolean)) assert(cost.textContent.includes(line), 'Lost a shared cost condition: ' + line);
    assert(challenges.querySelector('.weight-technical-thesis').textContent.includes(weightFrame['technical_summary_' + locale]));
  }
});

check('Partial weight views switch to the destination chapter without losing topic, month or scope', () => {
  for (const locale of ['zh', 'en']) {
    for (const view of ['background', 'mechanism']) {
      const {root, challenges, landscape, local} = renderWeightThreads(locale, view);
      const forward = challenges.querySelector('.weight-thread-map').querySelectorAll('a[href]');
      const backward = landscape.querySelectorAll('.weight-route-thread').map(group => group.children[0].querySelector('a[href]'));
      assert.equal(forward.length, 7, 'Every approach remains reachable from its challenge');
      assert.equal(backward.length, 3, 'Every contribution group has a return to its own challenge');
      for (const [links, destinationView, prefix] of [[forward, 'mechanism', '#research-card-parameters-precision__landscape_'], [backward, 'background', '#weight-challenge-']]) {
        for (const link of links) {
          const url = new URL(link.href, local.location.href);
          assert.equal(link.dataset.compressionResearchView, destinationView, 'The reader must switch views before restoring a hidden-chapter anchor');
          assert.equal(url.pathname, '/business_insight/cloud_core/topic.html');
          assert.equal(url.searchParams.get('view'), destinationView);
          assert.equal(url.searchParams.get('topic'), 'parameters-precision');
          assert.equal(url.searchParams.get('month'), local.state.period);
          assert.equal(url.searchParams.get('scope'), local.state.scope);
          assert(url.hash.startsWith(prefix), 'The target must retain its exact card or challenge anchor');
          assert(root.querySelector(url.hash), 'Partial-view navigation must resolve to an existing destination: ' + url.hash);
        }
      }
    }
  }
});

check('Real landscape cards keep group h4, card h5 and structured-part h6 headings with their own citations', () => {
  for (const locale of ['zh', 'en']) {
    const {landscape} = renderWeightThreads(locale);
    for (const group of landscape.querySelectorAll('.weight-route-thread')) {
      assert.equal(group.children[0].tagName, 'HEADER');
      assert.equal(group.children[0].children[0].tagName, 'H4');
      const ownCards = group.children.filter(node => node.dataset.researchCard);
      for (const card of ownCards) {
        const original = weightLandscape.find(row => row.card_id === card.dataset.researchCard);
        assert(original, 'Grouped content must use an existing maintained card');
        assert.equal(card.children[0].tagName, 'H5');
        assert.equal(card.children[0].textContent, original['title_' + locale]);
        assert.equal(card.querySelectorAll('h4').length, 0, 'A nested card must not jump back to its group heading level');
        const parts = card.querySelectorAll('.weight-explanation-part');
        if (locale === 'zh') assert(parts.length > 0, 'Render the real structured paragraphs, not a replacement summary');
        for (const part of parts) assert.equal(part.children[0].tagName, 'H6', 'Structured paragraph headings must sit below the card title');
        assert(card.descendants().every(node => !node.hidden));
        assert.equal(card.querySelectorAll('details').length, 0, 'Route explanations stay readable; only representative paper cases fold');
        const expectedSources = [...new Set(refs.filter(ref => ref.card_id === original.card_id).map(ref => findSource(ref.source_id).canonical_url))].sort();
        assert(expectedSources.length > 0, 'Every landscape approach must retain its own evidence');
        assert.deepEqual(card.querySelectorAll('.topic-dossier-citations a[href]').map(link => link.href).sort(), expectedSources);
      }
    }
  }
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
