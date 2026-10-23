/* Report reading contracts against canonical data; no build or browser required. */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const sourcePath = path.join(root, 'original-reader/site/business_insight/cloud_core/current-synthesis.js');
const source = fs.readFileSync(sourcePath, 'utf8');
// Check the maintained HTML as well as generated children: an outer closed
// disclosure can hide every otherwise-expanded argument on first entry.
function reportShell(page, htmlFixture = null) {
  const html = (htmlFixture ?? fs.readFileSync(path.join(path.dirname(sourcePath), page), 'utf8'))
    .replace(/<script\b[^>]*>[\s\S]*?<\/script\s*>/gi, '')
    .replace(/<style\b[^>]*>[\s\S]*?<\/style\s*>/gi, '')
    .replace(/<!--[\s\S]*?-->/g, '');
  const stack = [], found = new Map();
  const voidTags = new Set(['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']);
  for (const match of html.matchAll(/<(\/?)([a-z][\w:-]*)([^>]*?)>/gi)) {
    const tag = match[2].toLowerCase();
    if (match[1]) {
      const last = stack.findLastIndex(node => node.tag === tag);
      if (last >= 0) stack.length = last;
      continue;
    }
    const attrs = match[3], id = /\bid\s*=\s*["']([^"']+)["']/i.exec(attrs)?.[1];
    const node = {tag, id, open: /(?:^|\s)open(?:\s|=|$)/i.test(attrs), hidden: /(?:^|\s)hidden(?:\s|=|$)/i.test(attrs), ancestors: [...stack]};
    if (id) found.set(id, node);
    if (!voidTags.has(tag) && !/\/\s*$/.test(attrs)) stack.push(node);
  }
  const wrapper = found.get('ascend'), argumentsRoot = found.get('ascend-cards');
  assert(wrapper && argumentsRoot, page + ': preserve the report argument entry');
  assert(argumentsRoot.ancestors.some(node => node.id === wrapper.id), page + ': arguments belong to their report chapter');
  assert(!argumentsRoot.ancestors.some(node => node.tag === 'details' && !node.open), page + ': report reasoning must be visible before any expand click');
  const chapterPath = [...argumentsRoot.ancestors.slice(argumentsRoot.ancestors.indexOf(wrapper)), argumentsRoot];
  assert(!chapterPath.some(node => node.hidden), page + ': report chapter and argument containers must not be hidden');
  return wrapper;
}
assert.throws(() => reportShell('closed-wrapper regression', '<main><details id="ascend"><div id="ascend-cards"></div></details></main>'), /visible before any expand click/);
assert.throws(() => reportShell('hidden-wrapper regression', '<main><section id="ascend" hidden><div id="ascend-cards"></div></section></main>'), /must not be hidden/);
const shells = ['index.html', 'topic.html', 'monthly.html'].map(page => reportShell(page));
const readRows = table => fs.readFileSync(path.join(root, 'data/compression/tables', table, 'rows.jsonl'), 'utf8')
  .trim().split('\n').map(JSON.parse).filter(entry => !entry.deleted).map(entry => entry.row);
const report = readRows('ic_insight_reports').find(row => row.report_id === 'ascend-2026-10-20261015-v6');
assert(report && report.status === 'published');
const reportPapers = readRows('ic_insight_report_papers');
const expected = reportPapers.filter(row => row.report_id === report.report_id && row.priority_zh === '条件优先')
  .sort((a, b) => a.position - b.position);
assert.equal(expected.length, 3, 'Published v6 selects three papers, rather than an entire technical route');
const inScope = row => row.scope_id === report.scope_id && row.period_id === report.period_id;
const model = {
  insight_reports: readRows('ic_insight_reports').filter(inScope),
  insight_report_papers: reportPapers.filter(inScope),
  ascend_route_assessments: readRows('ic_ascend_route_assessments').filter(inScope),
  ascend_validation_probes: readRows('ic_ascend_validation_probes').filter(inScope),
  monthly_route_evidence: readRows('ic_monthly_route_evidence').filter(inScope),
  sources: new Map(readRows('cloud_core_sources').map(row => [row.source_id, row])),
  paperSummaries: new Map(readRows('ic_paper_summaries').map(row => [row.summary_id, row])),
  stories: new Map(readRows('ic_monthly_route_insights').filter(inScope).map(row => [row.story_id, row]))
};
function walk(node) { return [node, ...node.children.flatMap(walk)]; }
function text(node) { return node.textContent + node.children.map(text).join(' '); }
const scrollEvents = [];
function element(tag, value = '', className = '') {
  return {
    tagName: tag.toUpperCase(), textContent: String(value), className, children: [], dataset: {}, attributes: {}, events: {}, focusCount: 0,
    append(...children) { this.children.push(...children); },
    prepend(...children) { this.children.unshift(...children); },
    replaceChildren(...children) { this.children = children; },
    addEventListener(name, handler) { this.events[name] = handler; },
    scrollIntoView(options) { scrollEvents.push({id: this.id, options}); },
    focus(options) { this.focusCount++; this.focusOptions = options; },
    setAttribute(name, value) { this.attributes[name] = String(value); },
    getAttribute(name) {
      if (name === 'id') return this.id || null;
      if (name.startsWith('data-')) return this.dataset[name.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] ?? null;
      return this.attributes[name] ?? null;
    }
  };
}
const roots = new Map(['analysis-focus-cards', 'ascend-cards', 'analysis-summary', 'analysis-meta', 'ascend'].map(id => {
  const node = element(id === 'ascend' ? shells[0].tag : 'div'); node.id = id;if (id === 'ascend') node.open = shells[0].open;return [id, node];
}));
const nodes = () => [...roots.values()].flatMap(walk);
const document = {
  createElement: element, createTextNode: value => element('#text', value),
  getElementById: id => nodes().find(node => node.id === id) || null,
  body: {dataset: {}},
  querySelectorAll: () => nodes().filter(node => (node.tagName === 'SECTION' && node.id) || node.dataset.sectionId),
  dispatchEvent() {}
};
const context = {document, location: {href: 'https://ccn.example/business_insight/cloud_core/index.html', pathname: '/business_insight/cloud_core/index.html', search: '?month=' + report.period_id}, history: {replaceState(state, title, value) { this.url = value; }}, URL, Event: function Event() {}};
const animationFrames = [];
context.requestAnimationFrame = callback => { animationFrames.push(callback); return animationFrames.length; };
vm.createContext(context);
const instrumented = source.replace('globalThis.LRICompressionSynthesis=Object.freeze({refresh});',
  'globalThis.reportTest={setCurrent(value){current=value},renderAnalysis,renderResearchFocus,reportPrioritySources,priorityRouteRefs,restoreReportAnchor,refresh,reportPositions,seedModel(value,model){cache.set([value.revision,value.scope,value.period].join("|"),{model})},setReportRenderer(renderer){renderReports=renderer}};');
assert.notEqual(instrumented, source, 'Expected test seam');
vm.runInContext(instrumented, context);
const shellSource = fs.readFileSync(path.join(root, 'original-reader/site/assets/lri-shell.js'), 'utf8');
vm.runInContext(shellSource.slice(shellSource.indexOf('function collectPageSections('), shellSource.indexOf('function renderSectionLinks(')), context);
for (const locale of ['zh', 'en']) {
  const strings = JSON.parse(fs.readFileSync(path.join(root, 'original-reader/site/business_insight/cloud_core/data/focus-ui.' + locale + '.json'), 'utf8')).strings;
  const current = {locale, scope: report.scope_id, period: report.period_id, topicId: '', strings, topics: readRows('ic_compression_topics')};
  context.reportTest.setCurrent(current);
  context.reportTest.renderAnalysis(model);
  const focus = roots.get('analysis-focus-cards').children;
  assert.deepEqual(focus.map(node => node.dataset.sourceId), expected.map(row => row.source_id), 'Focus must follow the selected paper order');
  const choices = walk(roots.get('analysis-summary')).filter(node => node.className === 'analysis-choice-card');
  assert.deepEqual(choices.map(node => node.dataset.sourceId), expected.map(row => row.source_id), 'Top research choices must follow the current canonical report, not route counts');
  assert(!walk(roots.get('analysis-summary')).some(node => node.className === 'analysis-priority-tile'), 'Replace count-only priority tiles with actual choices');
  choices.forEach((card, index) => {
    const paper = expected[index], assessment = model.ascend_route_assessments.find(row => row.assessment_id === card.dataset.assessmentId), probe = model.ascend_validation_probes.find(row => row.assessment_id === card.dataset.assessmentId);
    assert.equal(card.dataset.reportId, report.report_id);
    assert.equal(card.dataset.summaryId, paper.source_id + '__' + paper.observed_version);
    assert.equal(card.dataset.claimKind, 'analyst_recommendation');
    assert.equal(card.dataset.probeStatus, 'proposed_not_measured');
    assert(text(card).includes(assessment['title_' + locale]));
    const reason = walk(card).find(node => node.className === 'analysis-choice-reason');
    assert(reason.textContent && paper['reason_' + locale].startsWith(reason.textContent), 'Overview reason must be an exact excerpt of its own selection metadata');
    const gate = walk(card).find(node => node.className === 'analysis-choice-gate');
    assert(probe['decision_rule_' + locale].startsWith(gate.children.at(-1).textContent), 'Validation gate must come from the bound proposed experiment');
    const links = walk(card).filter(node => node.tagName === 'A'), facts = links.map(node => new URL(node.href, context.location.href)).find(url => url.searchParams.has('paper'));
    assert.equal(facts.searchParams.get('paper'), card.dataset.summaryId);
    assert.equal(facts.searchParams.get('month'), report.period_id);
    assert.equal(facts.searchParams.get('scope'), report.scope_id);
    const argument = links.find(node => node.href === '#' + card.dataset.assessmentId), target = document.getElementById(card.dataset.assessmentId), before = scrollEvents.length;
    let prevented = false, stopped = false;
    argument.events.click({button: 0, preventDefault() { prevented = true; }, stopPropagation() { stopped = true; }});
    assert(prevented && scrollEvents.at(-1).id === target.id, 'Overview must jump to its actual route reasoning');
    assert(stopped, 'A report jump must not bubble into the generic hash router and reset the current view');
    assert.equal(target.focusOptions.preventScroll, true);
    assert(context.history.url.endsWith('#' + target.id));
    scrollEvents.splice(before);
  });
  const analysis = walk(roots.get('ascend-cards'));
  assert(!analysis.some(node => node.tagName === 'DETAILS'), 'Core argument, evidence and proposed protocol must not be hidden in nested disclosures');
  const outline = context.collectPageSections(locale, {});
  assert(outline.every(item => item.id === 'ascend' || item.id.startsWith('analysis-priority-')), 'Outline includes the argument chapter and priority categories, not raw internal IDs');
  assert(outline.every(item => locale === 'zh' ? /[\u4e00-\u9fff]/.test(item.title) : !/[\u4e00-\u9fff]/.test(item.title)), 'Outline has explicit zh/en labels');
  const paperEvidence = analysis.filter(node => node.dataset.paperProbe);
  assert.equal(paperEvidence.length, 3, 'Other papers retain evidence links without inheriting priority');
  for (const [i, card] of focus.entries()) {
    const paper = expected[i];
    assert.equal(card.dataset.claimKind, 'analyst_recommendation');
    assert.equal(card.dataset.reportId, report.report_id);
    assert(card.className.includes('analysis-source-index-row'), 'The post-PPT entry is a compact paper index');
    assert(!text(card).includes(paper['reason_' + locale]), 'Do not repeat the top selection reason after the PPT');
    assert(!text(card).includes(strings.probe_not_run), 'The compact index must not repeat status paragraphs');
    assert(!walk(card).some(node => node.className === 'analysis-focus-decision'), 'No repeated decision card inside the source index');
    assert(text(card).includes(paper.observed_version), 'Keep the cited version visible');
    const links = walk(card).filter(node => node.tagName === 'A');
    const paperLink = links.map(node => new URL(node.href, context.location.href)).find(url => url.searchParams.has('paper'));
    assert.equal(paperLink.searchParams.get('paper'), card.dataset.summaryId);
    assert.equal(paperLink.searchParams.get('month'), report.period_id);
    assert.equal(paperLink.searchParams.get('scope'), report.scope_id);
    assert.equal(paperLink.hash, '#monthly-route-report');
    const evidenceLink = links.find(node => node.href.startsWith('#'));
    const evidence = document.getElementById(evidenceLink.href.slice(1));
    assert(evidence && evidence.dataset.paperProbe === card.dataset.summaryId, 'Each focus must reach its own visible evidence');
    assert.equal(evidence.dataset.probeStatus, 'proposed_not_measured');
    const summary = model.paperSummaries.get(card.dataset.summaryId);
    const facts = walk(evidence).filter(node => node.tagName === 'A').map(node => new URL(node.href, context.location.href)).find(url => url.searchParams.get('paper') === summary.summary_id);
    assert(facts && facts.pathname.endsWith('/monthly.html') && facts.hash === '#monthly-route-report', 'Detailed paper facts must remain directly reachable in current updates');
    assert.equal(facts.searchParams.get('month'), report.period_id);
    assert.equal(facts.searchParams.get('scope'), report.scope_id);
    assert(walk(evidence).some(node => node.tagName === 'A' && node.href === summary.evidence_url), 'Keep the versioned primary source');
    assert(text(evidence).includes(summary.evidence_locator), 'Preserve actual review depth and source locator');
    const probe = model.ascend_validation_probes.find(row => row.assessment_id === card.dataset.assessmentId);
    for (const key of ['hypothesis', 'design', 'metrics', 'decision_rule']) assert(text(evidence).includes(probe[key + '_' + locale]));
    assert(links.some(node => node.href === summary.evidence_url), 'The paper title must retain its versioned primary source');
    const beforeJump = scrollEvents.length;
    evidenceLink.events.click({button: 0, preventDefault() {}, stopPropagation() {}});
    assert.equal(scrollEvents.at(-1).id, evidence.id, 'Index link must jump to its own protocol');
    assert.equal(evidence.focusOptions.preventScroll, true);
    scrollEvents.splice(beforeJump);
    if (roots.get('ascend').tagName === 'DETAILS') assert.equal(roots.get('ascend').open, true, 'Reveal any permitted open disclosure before anchor navigation');
  }
  for (const assessment of model.ascend_route_assessments) {
    const card = document.getElementById(assessment.assessment_id);
    assert(card && card.dataset.claimKind === 'analyst_recommendation', 'Preserve route anchors and recommendation provenance');
    const refs = model.monthly_route_evidence.filter(row => row.story_id === assessment.story_id);
    for (const ref of refs) assert(walk(card).some(node => node.tagName === 'A' && node.href === model.sources.get(ref.source_id).canonical_url), 'Keep every source link');
  }
  const keys = context.reportTest.reportPrioritySources(model), assessment = model.ascend_route_assessments[0];
  const fakeVersion = {source_id: expected[0].source_id, observed_version: 'unreviewed-version'};
  assert.equal(context.reportTest.priorityRouteRefs(assessment, [fakeVersion], keys).length, 0, 'Priority belongs to a reviewed version, not every revision of a source');
  context.reportTest.setCurrent({...current, topicId: model.monthly_route_evidence.find(row => row.source_id === expected[0].source_id).compression_topic_id});
  context.reportTest.renderAnalysis(model);
  for (const card of roots.get('analysis-focus-cards').children.filter(node => node.dataset.sourceId)) assert(expected.some(row => row.source_id === card.dataset.sourceId));
}
// Cold deep links must wait until both asynchronous report surfaces are mounted,
// then scroll once. Locale/filter redraws at the same hash preserve reading.
const focusChapter = element('section');focusChapter.id = 'analysis-focus';roots.set(focusChapter.id, focusChapter);
const deepContext = {
  revision: 'd'.repeat(40), scope: report.scope_id, period: report.period_id, view: 'home', topicId: '', locale: 'zh',
  topics: readRows('ic_compression_topics'),
  strings: JSON.parse(fs.readFileSync(path.join(path.dirname(sourcePath), 'data/focus-ui.zh.json'), 'utf8')).strings
};
const pageState = {page: 5, zoom: 'native'};
context.reportTest.reportPositions.set('preserved-reader-position', pageState);
const pageStateBefore = JSON.stringify([...context.reportTest.reportPositions]);
let reportMounts = 0;
context.reportTest.setReportRenderer(() => { reportMounts++; });
context.reportTest.seedModel(deepContext, model);
context.location.hash = '#analysis-focus';
context.reportTest.refresh(deepContext);
assert.equal(reportMounts, 1, 'Mount the inline report before restoring its downstream anchor');
assert.equal(scrollEvents.length, 0, 'Wait for the render frame rather than scrolling during construction');
assert.equal(animationFrames.length, 1);
animationFrames.shift()();
assert.equal(scrollEvents.length, 0, 'Let the sections shell complete layout in the first frame');
assert.equal(animationFrames.length, 1);
animationFrames.shift()();
assert.equal(scrollEvents.at(-1).id, 'analysis-focus');
assert.equal(scrollEvents.at(-1).options.behavior, 'auto');
assert.equal(scrollEvents.at(-1).options.block, 'start');
context.reportTest.refresh({...deepContext, locale: 'en'});
assert.equal(animationFrames.length, 0, 'A redraw or locale change at the same hash must not reset the reading position');
assert.equal(scrollEvents.length, 1);
const paperAnchor = walk(roots.get('ascend-cards')).find(node => node.dataset.paperProbe).id;
for (const id of ['ascend', 'analysis-priority-1', model.ascend_route_assessments[0].assessment_id, paperAnchor]) {
  context.location.hash = '#' + id;
  context.reportTest.refresh(deepContext);
  assert.equal(animationFrames.length, 1, 'Restore a concrete report anchor once: ' + id);
  const beforeFrames = scrollEvents.length;
  animationFrames.shift()();
  assert.equal(scrollEvents.length, beforeFrames, 'The first frame settles layout without scrolling');
  assert.equal(animationFrames.length, 1);
  animationFrames.shift()();
  assert.equal(scrollEvents.at(-1).id, id);
  context.reportTest.refresh(deepContext);
  assert.equal(animationFrames.length, 0, 'Do not scroll again after a same-hash rerender');
}
for (const hash of ['#view-home', '#view-topics', '#analysis-priority-999', '#unrelated', '#%E0%A4%A']) {
  context.location.hash = hash;
  context.reportTest.refresh(deepContext);
  assert.equal(animationFrames.length, 0, 'Ignore root views, missing anchors and malformed hashes');
}
const nextContext = {...deepContext, revision: 'e'.repeat(40)};
context.reportTest.seedModel(nextContext, model);
context.location.hash = '#analysis-focus';
context.reportTest.refresh(nextContext);
assert.equal(animationFrames.length, 1, 'A new data context can restore its first deep link');
const priorScrolls = scrollEvents.length;
context.location.hash = '#view-home';
animationFrames.shift()();
assert.equal(scrollEvents.length, priorScrolls, 'Navigation before the queued frame cancels the old anchor restore');
context.location.hash = '#ascend';
context.reportTest.refresh(nextContext);
animationFrames.shift()();
assert.equal(animationFrames.length, 1);
context.location.hash = '#view-home';
animationFrames.shift()();
assert.equal(scrollEvents.length, priorScrolls, 'Navigation between the two frames also cancels restoration');
context.location.hash = '#ascend';
context.reportTest.setCurrent({...nextContext, view: 'reports'});
context.reportTest.restoreReportAnchor(model);
assert.equal(animationFrames.length, 0, 'The archive view never applies report-page anchor restoration');
assert.equal(JSON.stringify([...context.reportTest.reportPositions]), pageStateBefore, 'Anchor restoration preserves PPT page and zoom state');
assert(source.includes('function mountReportReader(') && source.includes('function renderReports(') && source.includes('dispose=mountReportReader('), 'Keep the inline report reader entry');
console.log('PASS: three visible HTML shells; zh/en canonical research choices and working jumps; facts linked to updates, complete proposed protocols; stable deep links and unchanged PPT state');
