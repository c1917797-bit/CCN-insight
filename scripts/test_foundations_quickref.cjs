/* Static reference must preserve canonical formulas and the existing lessons. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const site = path.join(root, 'original-reader/site/business_insight/cloud_core');
const rows = table => fs.readFileSync(path.join(root, 'data/compression/tables', table, 'rows.jsonl'), 'utf8').trim().split('\n').map(JSON.parse).filter(entry => !entry.deleted).map(entry => entry.row);
const records = rows('ic_compression_foundations'), steps = rows('ic_foundation_lesson_steps'), values = rows('ic_foundation_lesson_values'), topics = new Set(rows('ic_compression_topics').map(topic => topic.compression_topic_id));
class Node {
  constructor(tag, text = '') { this.tagName = tag.toUpperCase(); this.ownText = String(text); this.children = []; this.dataset = {}; this.attributes = {}; this.events = {}; this.parentElement = null; this.className = ''; this.id = ''; }
  get textContent() { return this.ownText + this.children.map(child => child.textContent).join(''); }
  set textContent(value) { this.ownText = String(value); this.children = []; }
  append(...children) { for (const child of children) { child.parentElement = this; this.children.push(child); } }
  replaceChildren(...children) { this.children = []; this.ownText = ''; this.append(...children); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] ?? this[name] ?? null; }
  addEventListener(name, callback) { this.events[name] = callback; }
  descendants() { return this.children.flatMap(child => [child, ...child.descendants()]); }
  querySelectorAll(selector) {
    if (selector.startsWith('.')) return this.descendants().filter(node => node.className.split(/\s+/).includes(selector.slice(1)));
    assert(/^[a-z][\w-]*$/i.test(selector), 'Unsupported test selector: ' + selector);
    return this.descendants().filter(node => node.tagName.toLowerCase() === selector.toLowerCase());
  }
  querySelector(selector) { if (selector === 'p:last-of-type') return this.querySelectorAll('p').at(-1) || null; return this.querySelectorAll(selector)[0] || null; }
}
const create = tag => new Node(tag), roots = new Map(['foundations-content', 'foundations-reading-nav', 'foundations-status', 'foundations-refresh'].map(id => { const node = create('div'); node.id = id; return [id, node]; }));
const all = () => [...roots.values()].flatMap(node => [node, ...node.descendants()]);
const document = {
  body: {dataset: {compressionFoundations: 'true'}}, documentElement: {}, createElement: create,
  getElementById: id => all().find(node => node.id === id) || null,
  querySelectorAll(selector) { assert(['[data-i18n-key]', 'a[data-preserve-scope]'].includes(selector)); return []; },
  querySelector(){return null;}, addEventListener() {}, dispatchEvent() {},
};
const context = {document, location: {href: 'https://ccn.example/business_insight/cloud_core/foundations.html?month=2026-10&scope=reference-test', search: '?month=2026-10&scope=reference-test', hash: ''}, URL, URLSearchParams, Event: function Event() {}, requestAnimationFrame() {}, LRICloudFoundationUIPacks: Object.fromEntries(['zh', 'en'].map(locale => [locale, JSON.parse(fs.readFileSync(path.join(site, 'data/foundations-ui.' + locale + '.json'), 'utf8'))]))};
const source = fs.readFileSync(path.join(site, 'foundations.js'), 'utf8');
const instrumented = source.replace(/ start\(\);\s*\}\)\(\);\s*$/, ' globalThis.foundationQuickrefTest={renderFixture(data,language){snapshot=data;locale=language;render()}};\n})();');
assert.notEqual(instrumented, source, 'Replace only startup; exercise the actual maintained renderer');
vm.createContext(context); vm.runInContext(instrumented, context);
const revision = 'a'.repeat(40), result = data => ({revision, records: data, page: {total: data.length, truncated: false}});
const snapshot = context.LRICompressionFoundations.validate(result(records), revision);
snapshot.lessons = context.LRICompressionFoundations.validateLessons(result(steps), result(values), revision, records);
const methods = snapshot.records.filter(row => row.section_kind === 'method'), methodIds = {quantization: 'precision', pruning_sparsity: 'selection', distillation: 'distillation', low_rank: 'factorization'};
let checks = 0;
for (const locale of ['zh', 'en']) {
  context.foundationQuickrefTest.renderFixture(snapshot, locale);
  const page = roots.get('foundations-content'), quickrefs = page.querySelectorAll('.foundation-quickref'), players = page.querySelectorAll('lri-foundation-lesson');
  assert.equal(quickrefs.length, 4);
  assert.equal(players.length, 4, 'Keep all four existing animation players');
  for (const method of methods) {
    const quick = quickrefs.find(node => node.dataset.foundationMethod === method.method_id), player = players.find(node => node.lesson.method === method.method_id), section = player.parentElement;
    assert(quick && section.children.indexOf(quick) < section.children.indexOf(player), 'Definition and formula must precede the animation');
    assert(quick.textContent.includes(method.formula), 'Do not rewrite the canonical formula');
    for (const paragraph of method['body_' + locale].split(/\n+/).filter(Boolean)) assert(quick.textContent.includes(paragraph), 'Canonical definition, conditions or notation are missing');
    assert.equal(quick.querySelectorAll('details').length, 0, 'Quick reference must not require expansion');
    const links = quick.querySelectorAll('.foundation-topic-links')[0].querySelectorAll('a');
    assert.equal(links.length, 3);
    for (const [i, target] of ['parameters', 'activations', 'kv_cache'].entries()) {
      const id = target + '-' + methodIds[method.method_id], link = links[i], url = new URL(link.href, context.location.href);
      assert(topics.has(id), 'Quick-reference link invents a topic: ' + id);
      assert.equal(url.searchParams.get('topic'), id);
      assert.equal(url.pathname, '/business_insight/cloud_core/topic.html');
      assert.equal(url.searchParams.get('month'), '2026-10');
      assert.equal(url.searchParams.get('scope'), 'reference-test');
      if (method.method_id === 'distillation') {
        assert.equal(link.dataset.topicRelation, target === 'parameters' ? 'main' : 'related');
        if (target !== 'parameters') assert(link.textContent.includes(locale === 'en' ? 'Related case' : '关联案例'), 'Distillation must not imply a generic direct tensor-compression method');
      }
    }
    const before = steps.filter(step => step.method_id === method.method_id).sort((a, b) => a.position - b.position);
    assert.deepEqual(player.lesson.steps.map(step => step.step_id), before.map(step => step.step_id), 'Keep the same lesson and ordering');
    const cite = quick.querySelectorAll('.foundation-cite').at(-1).querySelector('a'), reference = document.getElementById(cite.href.slice(1));
    assert(reference && reference.querySelector('a').href === method.source_url, 'Quick-reference citation must resolve to its own source');
  }
  checks++;
  const tableRows = page.querySelectorAll('tr').filter(node => node.dataset.lessonStep);
  assert.equal(tableRows.length, 18, 'All eighteen example stages must be available without playback');
  for (const step of steps) {
    const row = tableRows.find(node => node.dataset.lessonStep === step.step_id);
    assert(row.textContent.includes(step['title_' + locale]));
    assert(row.textContent.includes(step.formula || '—'));
    assert(row.textContent.includes(step['takeaway_' + locale]));
    const cite = row.querySelectorAll('.foundation-cite')[0].querySelector('a'), reference = document.getElementById(cite.href.slice(1));
    assert(reference && reference.querySelector('a').href === step.source_url, 'Worked example borrowed another source');
  }
  assert.equal(page.querySelectorAll('details').length, 0);
  assert.equal(page.dataset.foundationReady, 'true');
  checks++;
}
const html = fs.readFileSync(path.join(site, 'foundations.html'), 'utf8');
assert(html.includes('href="foundations-quickref.css?'));
assert(fs.statSync(path.join(site, 'foundations-quickref.css')).size > 0);
checks++;
console.log(`PASS: ${checks} foundation reference contracts; zh/en canonical definitions/formulas, eighteen static stages, four unchanged players and twelve real scoped topic links`);
