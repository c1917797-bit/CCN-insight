/* Archive regressions using existing report metadata; no build or asset fetching. */
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const sourcePath = path.join(root, 'original-reader/site/business_insight/cloud_core/current-synthesis.js');
const source = fs.readFileSync(sourcePath, 'utf8');
const rows = table => fs.readFileSync(path.join(root, 'data/compression/tables', table, 'rows.jsonl'), 'utf8')
  .trim().split('\n').map(JSON.parse).filter(entry => !entry.deleted).map(entry => entry.row);
const reports = rows('ic_insight_reports'), published = reports.find(report => report.status === 'published');
assert(published && published.period_id === '2026-10', 'Use the existing October report inventory');
const inScope = row => row.scope_id === published.scope_id && row.period_id === published.period_id;
const model = {
  insight_reports: reports.filter(inScope),
  insight_report_papers: rows('ic_insight_report_papers').filter(inScope),
  insight_report_assets: rows('ic_insight_report_assets').filter(inScope),
  monthly_route_evidence: rows('ic_monthly_route_evidence').filter(inScope),
  sources: new Map(rows('cloud_core_sources').map(row => [row.source_id, row])),
};
const oldReports = model.insight_reports.filter(report => report.status === 'superseded');
assert.equal(oldReports.length, 5, 'Keep the five real superseded versions');
const walk = node => [node, ...node.children.flatMap(walk)];
const text = node => node.textContent + node.children.map(text).join(' ');
function element(tag, value = '', className = '') {
  return {
    tagName: tag.toUpperCase(), textContent: String(value), className, children: [], dataset: {}, attributes: {}, events: {},
    append(...children) { this.children.push(...children); },
    replaceChildren(...children) { this.children = children; this.textContent = ''; },
    setAttribute(name, value) { this.attributes[name] = String(value); },
    addEventListener(name, handler) { this.events[name] = handler; },
    click() { this.events.click?.({target: this}); },
    querySelectorAll(selector) {
      assert.equal(selector, 'dialog[open]', 'Unexpected archive fixture selector');
      return walk(this).filter(node => node.tagName === 'DIALOG' && node.open);
    },
  };
}
const roots = new Map(['insight-deck-archive', 'insight-deck-content'].map(id => {
  const node = element('section'); node.id = id; return [id, node];
}));
const mounts = [];
const context = {
  document: {createElement: element, createTextNode: value => element('#text', value), getElementById: id => roots.get(id) || null, dispatchEvent() {}},
  location: {origin: 'https://ccn.example', href: 'https://ccn.example/business_insight/cloud_core/index.html'},
  URL, Event: function Event() {},
};
vm.createContext(context);
const instrumented = source.replace('globalThis.LRICompressionSynthesis=Object.freeze({refresh});',
  'globalThis.archiveTest={setCurrent(value){current=value},renderReports,setReader(reader){mountReportReader=reader}};');
assert.notEqual(instrumented, source, 'Expected a narrow report test seam');
vm.runInContext(instrumented, context);
context.archiveTest.setReader((viewer, slides, title, assetUrl, key) => {
  mounts.push({viewer, slides, title, key});
  const dispose = () => {};
  dispose.goTo = () => {};
  return dispose;
});
const current = (locale, view = 'reports', period = published.period_id) => ({
  locale, view, scope: published.scope_id, period, topics: rows('ic_compression_topics'),
  strings: JSON.parse(fs.readFileSync(path.join(path.dirname(sourcePath), 'data/focus-ui.' + locale + '.json'), 'utf8')).strings,
});
const reportNodes = root => walk(root).filter(node => node.dataset.reportId);
let checks = 0;
for (const locale of ['zh', 'en']) {
  context.archiveTest.setCurrent(current(locale));
  mounts.length = 0;
  context.archiveTest.renderReports(model);
  const archive = roots.get('insight-deck-archive'), nodes = reportNodes(archive);
  assert.equal(nodes.length, 6, 'Archive must not reduce the six versions to only the current report');
  assert.equal(nodes[0].dataset.reportId, published.report_id);
  assert.equal(nodes[0].dataset.reportStatus, 'published');
  assert.deepEqual(nodes.slice(1).map(node => node.dataset.reportId.match(/-v\d+$/)[0]), ['-v5', '-v4', '-v3', '-v2', '-v1']);
  assert(nodes.slice(1).every(node => node.dataset.reportStatus === 'superseded'));
  assert(text(archive).includes(locale === 'en' ? 'Current report' : '当前报告'));
  assert(text(archive).includes(locale === 'en' ? 'Earlier versions' : '历史版本'));
  assert.equal(mounts.length, 0, 'Archive must not automatically mount any slide reader');
  for (const report of oldReports) {
    const node = nodes.find(node => node.dataset.reportId === report.report_id), descendants = walk(node);
    assert(node && text(node).includes(report['summary_' + locale]), 'Keep the exact recorded summary');
    assert(text(node).includes(locale === 'en' ? 'Recorded summary' : '该版摘要'));
    assert(text(node).includes(report.reviewed_at));
    assert(!descendants.some(node => ['IMG', 'IFRAME', 'OBJECT', 'EMBED', 'BUTTON', 'DETAILS'].includes(node.tagName)), 'Historical version must remain a readable metadata entry and original-file links');
    const links = descendants.filter(node => node.tagName === 'A');
    assert.equal(links.length, 2, 'Each historical entry provides PDF and PPTX');
    const assets = model.insight_report_assets.filter(asset => asset.report_id === report.report_id && ['pdf', 'pptx'].includes(asset.format));
    assert.deepEqual(links.map(link => link.href).sort(), assets.map(asset => new URL(asset.public_path, context.location.origin).href).sort());
    assert(links.every(link => link.target === '_blank' && link.rel === 'noopener noreferrer'));
  }
  checks++;

  context.archiveTest.setCurrent(current(locale, 'home'));
  mounts.length = 0;
  context.archiveTest.renderReports(model);
  const home = roots.get('insight-deck-content');
  assert.deepEqual(reportNodes(home).map(node => node.dataset.reportId), [published.report_id], 'Current report view must not acquire historical versions');
  assert.equal(mounts.length, 1, 'Current insight report must still open inline by default');
  assert.equal(mounts[0].slides.length, published.page_count);
  assert(walk(home).some(node => node.tagName === 'BUTTON' && node.attributes['aria-expanded'] === 'true'));
  checks++;
}

// Old versions only need their two original files. Their slide sets and paper
// lists are deliberately absent: browsing history must not force full readers.
context.archiveTest.setCurrent(current('zh'));
const lightweight = {
  ...model,
  insight_reports: oldReports,
  insight_report_papers: [],
  insight_report_assets: model.insight_report_assets.filter(asset => oldReports.some(report => report.report_id === asset.report_id) && ['pdf', 'pptx'].includes(asset.format)),
};
mounts.length = 0;
context.archiveTest.renderReports(lightweight);
assert.equal(reportNodes(roots.get('insight-deck-archive')).length, oldReports.length);
assert.equal(mounts.length, 0);
checks++;

const september = {...oldReports[0], report_id: 'archive-test-2026-09-v1', period_id: '2026-09'};
context.archiveTest.setCurrent(current('zh', 'reports', '2026-09'));
context.archiveTest.renderReports({...lightweight, insight_reports: [september]});
assert.equal(reportNodes(roots.get('insight-deck-archive')).length, 0, 'Do not restore pre-October archives');
checks++;

context.archiveTest.setCurrent(current('zh'));
const unsafe = {...lightweight, insight_report_assets: lightweight.insight_report_assets.map((asset, i) => i ? asset : {...asset, public_path: 'https://foreign.example/report.pdf'})};
assert.throws(() => context.archiveTest.renderReports(unsafe), /Invalid report asset/);
const outsideReports = {...lightweight, insight_report_assets: lightweight.insight_report_assets.map((asset, i) => i ? asset : {...asset, public_path: '/private/report.pdf'})};
assert.throws(() => context.archiveTest.renderReports(outsideReports), /Invalid report asset/);
checks++;

const html = fs.readFileSync(path.join(path.dirname(sourcePath), 'index.html'), 'utf8');
assert(html.indexOf('id="insight-report-presentation"') < html.indexOf('id="ascend"'), 'Keep the report before route decisions');
checks++;
console.log(`PASS: ${checks} report archive contracts; zh/en six-version timeline, exact summaries/assets, lightweight history, October boundary and default inline current report`);
