/* Current web synthesis uses the real selection, independently of older files. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),base=path.join(root,'original-reader/site/business_insight/cloud_core');
const rows=table=>fs.readFileSync(path.join(root,'data/compression/tables',table,'rows.jsonl'),'utf8').trim().split('\n').map(JSON.parse).filter(r=>!r.deleted).map(r=>r.row);
const scope='ic-2026-10-model-reviewed-20261029-v1',period='2026-10',revision='current-report-test';
const tables=Object.fromEntries(['ic_monthly_route_insights','ic_monthly_route_evidence','ic_ascend_route_assessments','ic_ascend_validation_probes','ic_current_signals','ic_signal_topics','ic_insight_reports','ic_insight_report_assets','ic_insight_report_papers','ic_paper_summaries','cloud_core_sources'].map(name=>[name,rows(name)]));
const selectedStories=tables.ic_monthly_route_insights.filter(r=>r.scope_id===scope).sort((a,b)=>a.position-b.position),keyStories=selectedStories.filter(r=>r.selection_tier==='key_progress');
assert.equal(selectedStories.length,16);assert.equal(keyStories.length,6);
const currentRefs=tables.ic_monthly_route_evidence.filter(r=>r.scope_id===scope);
assert.equal(currentRefs.length,22,'Use actual cross-object associations, rather than assuming one row per paper');
assert.equal(new Set(currentRefs.map(r=>r.summary_id)).size,16);
const all=node=>[node,...node.children.flatMap(all)],text=node=>node.textContent+node.children.map(text).join(' ');
const scrolls=[],frames=[];
function element(tag,value='',className=''){
 return {
  tagName:tag.toUpperCase(),textContent:String(value),className,children:[],dataset:{},attributes:{},events:{},
  append(...nodes){this.children.push(...nodes);},prepend(...nodes){this.children.unshift(...nodes);},replaceChildren(...nodes){this.children=nodes;this.textContent='';},
  setAttribute(key,value){this.attributes[key]=String(value);},removeAttribute(key){delete this.attributes[key];},
  getAttribute(key){if(key.startsWith('data-'))return this.dataset[key.slice(5).replace(/-([a-z])/g,(_,x)=>x.toUpperCase())]??this.attributes[key]??null;return this.attributes[key]??null;},
  addEventListener(key,handler){this.events[key]=handler;},click(){this.events.click?.({target:this});},
  scrollIntoView(options){scrolls.push({id:this.id,options});},focus(options){this.focusOptions=options;},
  querySelectorAll(selector){assert.equal(selector,'dialog[open]');return all(this).filter(n=>n.tagName==='DIALOG'&&n.open);}
 };
}
const roots=new Map(['ascend-cards','analysis-summary','analysis-focus-cards','analysis-meta','home-judgement','ascend','insight-report-presentation','insight-deck-content','insight-deck-archive'].map(id=>{const n=element('div');n.id=id;return [id,n];}));
const selectors=new Map();
for(const [selector,key] of [
 ['#insight-overview .analysis-intro','analysis_intro'],
 ['#insight-report-presentation [data-i18n-key="deck_title"]','deck_title'],
 ['#insight-report-presentation [data-i18n-key="analysis_report_hint"]','analysis_report_hint'],
 ['#insight-report-presentation [data-i18n-key="deck_relation"]','deck_relation'],
 ['.analysis-reading-navigation a[href="#insight-report-presentation"]','analysis_report_link'],
 ['.analysis-reading-navigation a[href="#analysis-focus"]','analysis_overview_link'],
 ['.analysis-reading-navigation a[href="#ascend"]','analysis_decisions_link'],
 ['#ascend .analysis-section-heading h3','analysis_route_title'],
 ['#ascend .analysis-section-note','analysis_route_note'],
 ['#analysis-focus>h3','analysis_overview_link'],
 ['#analysis-focus>.reader-note','analysis_focus_help']
]){const n=element('p');n.setAttribute('data-i18n-key',key);selectors.set(selector,n);}
const focusChapter=element('section');focusChapter.id='analysis-focus';focusChapter.querySelector=selector=>selectors.get(selector==='h3'?'#analysis-focus>h3':'#analysis-focus>.reader-note');roots.set(focusChapter.id,focusChapter);
const nodes=()=>[...roots.values()].flatMap(all).concat([...selectors.values()]);
const requests=[],groupNames=['monthly_route_insights','monthly_route_evidence','ascend_route_assessments','ascend_validation_probes','current_signals','signal_topics','insight_reports','insight_report_assets','insight_report_papers'];
let mutateBatch=null;
const context={
 URL,Event:function Event(){},location:{origin:'https://ccn.example',href:'https://ccn.example/business_insight/cloud_core/index.html',pathname:'/business_insight/cloud_core/index.html',search:'?month='+period+'&scope='+scope,hash:'#view-home'},
 history:{replaceState(state,title,url){this.url=url;}},requestAnimationFrame(fn){frames.push(fn);},
 document:{createElement:element,createTextNode:value=>element('#text',value),dispatchEvent(){},getElementById:id=>nodes().find(n=>n.id===id)||null,querySelector(selector){
  const key=/^\[data-analysis-frame-key="([^"]+)"\]$/.exec(selector)?.[1];if(key)return nodes().find(n=>n.dataset.analysisFrameKey===key)||null;
  return selectors.get(selector)||null;
 }},
 async LRICloudSemanticRead(mode,requestedRevision,options){
  assert.equal(mode,'synthesis');assert.equal(requestedRevision,revision);assert.equal(options.scope,scope);
  const groups=Object.fromEntries(groupNames.map(name=>[name,tables['ic_'+name].filter(r=>name==='current_signals'?r.period_id===options.period:name==='signal_topics'?true:r.scope_id===options.scope).map(r=>({...r}))]));
  const result={revision,groups};if(mutateBatch)mutateBatch(result);return result;
 },
 LRITableGit:{
  async loadTablePage(name,options){requests.push({name,options});const records=tables[name].filter(r=>r[options.filterField]===options.filterValue);return {revision,records,page:{truncated:false,total:records.length}};},
  async loadRowsByValues(name,field,values,expectedRevision){assert.equal(expectedRevision,revision);return {revision,records:tables[name].filter(r=>values.includes(r[field]))};},
  async loadRowsByKeys(name,keys,expectedRevision){assert.equal(expectedRevision,revision);const key=name==='ic_paper_summaries'?'summary_id':'source_id';return {revision,records:tables[name].filter(r=>keys.includes(r[key]))};}
 }
};
vm.createContext(context);
const source=fs.readFileSync(path.join(base,'current-synthesis.js'),'utf8');
const instrumented=source.replace('globalThis.LRICompressionSynthesis=Object.freeze({refresh});','globalThis.currentReportTest={read,renderAnalysis,renderReports,restoreReportAnchor,setCurrent(value){current=value},setReader(reader){mountReportReader=reader}};');
assert.notEqual(instrumented,source);vm.runInContext(instrumented,context);
const api=context.currentReportTest,mounts=[];
api.setReader((...args)=>{mounts.push(args);const dispose=()=>{};dispose.goTo=()=>{};return dispose;});
const current=locale=>({revision,scope,period,locale,view:'home',topicId:'',topics:rows('ic_compression_topics'),strings:JSON.parse(fs.readFileSync(path.join(base,'data/focus-ui.'+locale+'.json'),'utf8')).strings});
function assertFactsLink(link,summaryId){const href=new URL(link.href,context.location.href);assert(href.pathname.endsWith('/monthly.html'));assert.equal(href.searchParams.get('scope'),scope);assert.equal(href.searchParams.get('month'),period);assert.equal(href.searchParams.get('paper'),summaryId);assert.equal(href.hash,'#monthly-route-report');}
(async()=>{
 const model=await api.read(current('zh'));
 assert.equal(model.monthly_route_insights.length,16);assert.equal(model.ascend_route_assessments.length,0,'The new selection must work without fabricated Ascend assessments');
 assert.equal(model.reportFallback,true);const saved=tables.ic_insight_reports.find(r=>r.status==='published');assert.equal(model.reportScope,saved.scope_id);assert.notEqual(model.reportScope,scope);
 assert.equal(requests.filter(r=>r.name==='ic_insight_reports').length,1,'Fallback is a bounded same-month index lookup');
 for(const locale of ['zh','en']){
  const state=current(locale);api.setCurrent(state);api.renderAnalysis(model);
  const choices=all(roots.get('analysis-summary')).filter(n=>n.className==='analysis-choice-card');
  assert.deepEqual(choices.map(n=>n.dataset.storyId),keyStories.map(r=>r.story_id),'Six choices follow current editorial order');
  assert(choices.every(n=>n.dataset.claimKind==='analyst_synthesis'&&!n.dataset.reportId&&!n.dataset.probeStatus),'Current editorial judgments are not old report selections or proposed experiments');
  choices.forEach((card,index)=>{
   const story=keyStories[index];assert(text(card).includes(story['selection_reason_'+locale]));assert(text(card).includes(story['viewpoint_'+locale]));
   const jump=all(card).find(n=>n.tagName==='A'&&n.href==='#'+story.story_id);let prevented=false,stopped=false;jump.events.click({button:0,preventDefault(){prevented=true;},stopPropagation(){stopped=true;}});assert(prevented&&stopped);assert.equal(scrolls.at(-1).id,story.story_id);assert.equal(context.history.url.endsWith('#'+story.story_id),true);
  });
  const argumentsList=all(roots.get('ascend-cards')).filter(n=>n.dataset.editorialTier);
  assert.equal(argumentsList.length,16);assert.deepEqual(['key_progress','technical_watch','boundary_case'].map(t=>argumentsList.filter(n=>n.dataset.editorialTier===t).length),[6,9,1]);
  assert.equal(new Set(argumentsList.map(n=>n.dataset.storyId)).size,16);
  for(const story of selectedStories){const card=argumentsList.find(n=>n.dataset.storyId===story.story_id);for(const field of ['synthesis','viewpoint','boundary','implication'])assert(text(card).includes(story[field+'_'+locale]),'Keep exact maintained '+field);}
  const evidence=all(roots.get('ascend-cards')).filter(n=>n.dataset.reviewStatus);
  assert.equal(evidence.length,16,'Cross-object relations must not duplicate papers');
  assert.equal(evidence.filter(n=>n.dataset.reviewStatus==='primary_abstract_checked').length,12);
  assert.equal(evidence.filter(n=>n.dataset.reviewStatus==='method_results_checked').length,4);
  for(const entry of evidence){const summary=model.paperSummaries.get(entry.dataset.summaryId);assert(text(entry).includes(summary.observed_version));assert(text(entry).includes(summary.evidence_locator));assert(text(entry).includes(summary.reviewed_at));const links=all(entry).filter(n=>n.tagName==='A');assert(links.some(n=>n.href===summary.evidence_url),'Versioned original remains directly accessible');assertFactsLink(links.find(n=>new URL(n.href,context.location.href).searchParams.has('paper')),summary.summary_id);}
  assert(!nodes().some(n=>n.dataset.probeStatus==='proposed_not_measured'),'Do not invent a new experimental protocol');
  const index=roots.get('analysis-focus-cards').children;assert.equal(index.length,6);
  assert.equal(index.filter(n=>model.paperSummaries.get(n.dataset.summaryId).review_status==='primary_abstract_checked').length,4);
  assert.equal(index.filter(n=>model.paperSummaries.get(n.dataset.summaryId).review_status==='method_results_checked').length,2);
  assert(text(roots.get('analysis-meta')).includes('16'));assert.equal(selectors.get('#insight-report-presentation [data-i18n-key="deck_title"]').textContent,state.strings.editorial_attachment_title);
  assert.equal(selectors.get('.analysis-reading-navigation a[href="#ascend"]').textContent,state.strings.editorial_judgments);
  api.renderReports(model);const files=roots.get('insight-deck-content');
  assert.equal(mounts.length,0,'Earlier-scope slides must never mount as the current web report');
  assert(!all(files).some(n=>['BUTTON','IMG','IFRAME','OBJECT','EMBED'].includes(n.tagName)),'Historical attachment is explicit text and original-file links');
  const attachment=all(files).find(n=>n.dataset.historicalAttachment==='true');assert(attachment);assert.equal(attachment.dataset.reportId,saved.report_id);assert.equal(attachment.dataset.reportScope,saved.scope_id);assert(text(attachment).includes(saved['summary_'+locale]));assert(text(files).includes(state.strings.editorial_attachment_relation));
  assert((locale==='zh'?text(attachment).includes('2026-10-09'):text(attachment).includes('October 9, 2026'))&&text(attachment).includes('2026-10-15'),'Keep recorded evidence cutoff and later metric-review date');
  const links=all(attachment).filter(n=>n.tagName==='A'),assets=tables.ic_insight_report_assets.filter(r=>r.report_id===saved.report_id&&['pdf','pptx'].includes(r.format));for(const asset of assets)assert(links.some(n=>n.href===new URL(asset.public_path,context.location.origin).href));
  const archive=links.map(n=>new URL(n.href,context.location.href)).find(u=>u.hash==='#view-reports');assert(archive);assert.equal(archive.searchParams.get('scope'),saved.scope_id);
  api.setCurrent({...state,view:'reports'});api.renderReports(model);assert.equal(all(roots.get('insight-deck-archive')).filter(n=>n.dataset.reportId).length,6,'All six saved file versions remain available');assert.equal(mounts.length,0);
 }
 api.setCurrent({...current('zh'),topicId:'activations-precision'});api.renderAnalysis(model);assert.equal(all(roots.get('ascend-cards')).filter(n=>n.dataset.editorialTier).length,1,'Topic filter follows real cross-object associations');assert.equal(roots.get('analysis-focus-cards').children.length,1);
 api.setCurrent(current('zh'));api.renderAnalysis(model);
 const evidenceId=all(roots.get('ascend-cards')).find(n=>n.dataset.reviewStatus).id;
 for(const id of [selectedStories[0].story_id,evidenceId]){context.location.hash='#'+id;api.restoreReportAnchor(model);assert.equal(frames.length,1);frames.shift()();assert.equal(frames.length,1);frames.shift()();assert.equal(scrolls.at(-1).id,id);api.restoreReportAnchor(model);assert.equal(frames.length,0,'Repeated draw preserves reader position');}
 const unsafe={...model,insight_report_assets:model.insight_report_assets.map(a=>a.report_id===saved.report_id&&a.format==='pdf'?{...a,public_path:'https://foreign.example/report.pdf'}:a)};assert.throws(()=>api.renderReports(unsafe),/Invalid report asset/);
 mutateBatch=batch=>{batch.groups.monthly_route_insights[0].boundary_en='';};await assert.rejects(()=>api.read(current('zh')),/Incomplete editorial insight/);
 mutateBatch=batch=>{batch.groups.monthly_route_insights[0].claim_status='primary_text_checked';};await assert.rejects(()=>api.read(current('zh')),/Insight narrative scope mismatch/);
 mutateBatch=batch=>{batch.groups.monthly_route_evidence[0].observed_version='v999';};await assert.rejects(()=>api.read(current('zh')),/Paper probe version\/source mismatch/);
 console.log('PASS: current selection reads and renders 16 unique papers as 6 key / 9 watch / 1 boundary; exact judgments, 12 abstract / 4 section reviews, versioned facts, working deep links, and six archived versions isolated from the current web report (zh/en)');
})().catch(error=>{console.error(error);process.exitCode=1;});
