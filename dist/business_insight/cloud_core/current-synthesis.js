(() => {
'use strict';
const cache=new Map();let current=null;
const check=(ok,msg)=>{if(!ok)throw new Error(msg);};
const pick=(r,k)=>r[k+'_'+current.locale]||r[k+'_zh']||'';
const ui=k=>current.strings[k]||k;
const el=(tag,text='',cls='')=>{const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n;};
function url(value){const u=new URL(value,location.href);check(u.protocol==='https:'&&!u.username&&!u.password,'Unsafe insight reference');return u.href;}
function primary(parent,source,label){const a=el('a',label||source.title);a.href=url(source.canonical_url);a.target='_blank';a.rel='noopener noreferrer';parent.append(a);}
function topics(parent,ids,relations=[]){const group=el('div','','monthly-route-topics');for(const id of [...new Set(ids)]){const t=current.topics.find(x=>x.compression_topic_id===id);check(t,'Unresolved map topic');const relation=relations.find(r=>r.compression_topic_id===id),relationText=relation?(current.locale==='en'?(relation.relation_kind==='research_context'?' · Research context':' · Implementation example'):(relation.relation_kind==='research_context'?' · 研究背景':' · 实现示例')):'';const a=el('a',pick(t,'title')+relationText);const target=new URL('topic.html',location.href);target.searchParams.set('topic',id);target.searchParams.set('month',current.period);target.searchParams.set('scope',current.scope);a.href=target.pathname+target.search;group.append(a);}parent.append(group);}
function mapHeading(tag,title,ids,contextOnly=false){const h=el(tag,title),labels=[...new Set(ids)].map(id=>{const topic=current.topics.find(x=>x.compression_topic_id===id);check(topic,'Unresolved map topic');return pick(topic,'title');});if(labels.length)h.append(el('span',(current.locale==='en'?' (':'（')+(contextOnly?(current.locale==='en'?'Context: ':'相关背景：'):'')+labels.join(' · ')+(current.locale==='en'?')':'）'),'monthly-route-map-label'));return h;}
function field(parent,key,value){const p=el('p');p.append(el('strong',ui(key)+': '),document.createTextNode(value));parent.append(p);}
function owned(rows){check(rows.every(r=>r.business_id==='cloud-core'&&r.topic_id==='cloud_core'),'Insight scope mismatch');return rows;}
async function read(context){
 const b=await LRICloudSemanticRead('synthesis',context.revision,{scope:context.scope,period:context.period});
 check(b.revision===context.revision,'Insight revision drift');const g=b.groups;Object.values(g).forEach(owned);
 const stories=new Map(g.monthly_route_insights.map(r=>[r.story_id,r])),topicIds=new Set(context.topics.map(r=>r.compression_topic_id));
 check(stories.size===g.monthly_route_insights.length,'Duplicate insight narrative');
 for(const r of g.monthly_route_insights){
  check(r.scope_id===context.scope&&r.period_id===context.period&&r.claim_status==='analyst_synthesis','Insight narrative scope mismatch');
  if(r.selection_tier){
   check(['key_progress','technical_watch','boundary_case'].includes(r.selection_tier)&&/^\d{4}-\d{2}-\d{2}$/.test(r.checked_at),'Invalid editorial insight tier or review date');
   check(['title','question','synthesis','viewpoint','implication','boundary','selection_reason'].every(k=>['zh','en'].every(locale=>typeof r[k+'_'+locale]==='string'&&r[k+'_'+locale].trim())),'Incomplete editorial insight');
  }
 }
 for(const a of g.ascend_route_assessments){check(stories.has(a.story_id)&&a.scope_id===context.scope&&a.period_id===context.period&&a.claim_status==='analyst_recommendation','Unbound analyst judgment');}
 for(const p of g.ascend_validation_probes)check(g.ascend_route_assessments.some(a=>a.assessment_id===p.assessment_id)&&p.status==='proposed_not_measured'&&p.scope_id===context.scope&&p.period_id===context.period,'Unbound or promoted proposed probe');
 for(const r of g.monthly_route_evidence)check(stories.has(r.story_id)&&topicIds.has(r.compression_topic_id)&&r.scope_id===context.scope&&r.period_id===context.period,'Invalid judgment evidence/map relation');
 for(const r of g.current_signals)check(r.period_id===context.period&&r.claim_status==='primary_text_checked'&&r.publication_date.startsWith(context.period)&&r.locator,'Unreviewed current signal');
 for(const r of g.signal_topics)check(topicIds.has(r.compression_topic_id)&&['research_context','implementation_example'].includes(r.relation_kind),'Invalid signal/map relation');
 const ids=[...new Set([...g.monthly_route_evidence.map(r=>r.source_id),...g.current_signals.flatMap(r=>[r.source_id,r.discovery_source_id])])];
 const summaryIds=[...new Set(g.monthly_route_evidence.map(r=>r.summary_id))];
 const [s,summaries]=await Promise.all([LRITableGit.loadRowsByKeys('cloud_core_sources',ids,context.revision,['source_id','business_id','title','canonical_url']),LRITableGit.loadRowsByKeys('ic_paper_summaries',summaryIds,context.revision,['summary_id','source_id','business_id','topic_id','observed_version','evidence_url','one_sentence_zh','one_sentence_en','innovation_zh','innovation_en','results_zh','results_en','review_status','evidence_locator','reviewed_at'])]);
 check(s.revision===context.revision&&s.records.length===ids.length&&s.records.every(r=>r.business_id==='cloud-core'),'Incomplete exact insight sources');s.records.forEach(r=>url(r.canonical_url));
 for(const r of g.insight_reports)check(r.scope_id===context.scope&&r.period_id===context.period,'Report scope mismatch');
 check(summaries.revision===context.revision&&summaries.records.length===summaryIds.length,'Incomplete paper probe evidence');owned(summaries.records);for(const p of summaries.records)check(['primary_abstract_checked','method_results_checked'].includes(p.review_status)&&p.evidence_locator&&/^\d{4}-\d{2}-\d{2}$/.test(p.reviewed_at)&&['one_sentence','innovation','results'].every(k=>typeof p[k+'_zh']==='string'&&p[k+'_zh'].trim()),'Incomplete paper review provenance');
 for(const r of g.monthly_route_evidence){const p=summaries.records.find(p=>p.summary_id===r.summary_id);check(p&&p.source_id===r.source_id&&p.observed_version===r.observed_version,'Paper probe version/source mismatch');url(p.evidence_url);}
 check(g.monthly_route_insights.every(r=>g.monthly_route_evidence.some(ref=>ref.story_id===r.story_id)),'Insight narrative without direct evidence');
 const sourceRows=[...s.records];let reportScope=context.scope,reportFallback=false;
 // A new evidence batch does not imply that a new report/PPT was published.
 // Keep the latest published report from the same month, with its own cutoff.
 if(!g.insight_reports.some(r=>r.status==='published')){
  const available=await LRITableGit.loadTablePage('ic_insight_reports',{filterField:'period_id',filterValue:context.period,expectedRevision:context.revision,limit:100,offset:0});
  check(available.revision===context.revision&&!available.page.truncated,'Incomplete period report index');owned(available.records);
  const latest=available.records.filter(r=>r.status==='published'&&r.period_id===context.period).sort((a,b)=>b.reviewed_at.localeCompare(a.reviewed_at)||b.report_id.localeCompare(a.report_id))[0];
  if(latest){
   reportScope=latest.scope_id;reportFallback=true;g.insight_reports=available.records.filter(r=>r.scope_id===reportScope&&r.period_id===context.period);
   const reportIds=g.insight_reports.map(r=>r.report_id),[assets,papers]=await Promise.all([LRITableGit.loadRowsByValues('ic_insight_report_assets','report_id',reportIds,context.revision),LRITableGit.loadRowsByValues('ic_insight_report_papers','report_id',reportIds,context.revision)]);
   check(assets.revision===context.revision&&papers.revision===context.revision,'Fallback report revision drift');owned(assets.records);owned(papers.records);
   check([...assets.records,...papers.records].every(r=>reportIds.includes(r.report_id)),'Unbound fallback report asset');g.insight_report_assets=assets.records;g.insight_report_papers=papers.records;
   const extraIds=[...new Set(papers.records.map(r=>r.source_id))].filter(id=>!sourceRows.some(r=>r.source_id===id));
   if(extraIds.length){const extra=await LRITableGit.loadRowsByKeys('cloud_core_sources',extraIds,context.revision,['source_id','business_id','title','canonical_url']);check(extra.revision===context.revision&&extra.records.length===extraIds.length&&extra.records.every(r=>r.business_id==='cloud-core'),'Incomplete fallback report sources');extra.records.forEach(r=>url(r.canonical_url));sourceRows.push(...extra.records);}
  }
 }
 return {...g,reportScope,reportFallback,sources:new Map(sourceRows.map(r=>[r.source_id,r])),paperSummaries:new Map(summaries.records.map(r=>[r.summary_id,r])),stories};
}
function selected(model,story){return !current.topicId||model.monthly_route_evidence.some(r=>r.story_id===story&&r.compression_topic_id===current.topicId);}
function routePriority(row){return row.priority_zh==='优先穿刺'?ui('analysis_priority_research'):pick(row,'priority');}
function paperProbeCandidates(parent,m,assessment,refs,probe){
 const papers=[...new Map(refs.map(r=>[r.summary_id,r])).values()];
 const section=el('section','','analysis-paper-probes');section.dataset.sectionOutline='false';section.append(el('h6',ui('paper_probe_candidates')),el('p',ui('paper_probe_scope'),'meta'));
 for(const ref of papers){
  const p=m.paperSummaries.get(ref.summary_id),source=m.sources.get(ref.source_id),card=el('article','','analysis-paper-probe');card.id=assessment.assessment_id+'--'+ref.summary_id;card.dataset.sectionOutline='false';card.dataset.paperProbe=ref.summary_id;if(probe)card.dataset.probeStatus=probe.status;
  card.append(el('h6',source.title+' · '+ref.observed_version,'analysis-paper-heading'));const body=el('div','','analysis-paper-probe-body');
  const link=el('a',source.title+' ↗');link.href=url(p.evidence_url);link.target='_blank';link.rel='noopener noreferrer';body.append(link);
  topics(body,refs.filter(r=>r.summary_id===ref.summary_id).map(r=>r.compression_topic_id));
  body.append(el('p',ui('probe_not_run'),'paper-probe-status'));const facts=el('a',current.locale==='en'?'Read the paper facts in current updates →':'在本期动态查阅原文事实 →','analysis-facts-link');facts.href=reportFactsHref(ref);body.append(facts);
  body.append(el('p',ui(p.review_status==='method_results_checked'?'paper_probe_review_sections':'paper_probe_review_abstract')+' · '+p.evidence_locator+' · '+p.reviewed_at,'meta'));
  if(probe){const protocol=el('section','','analysis-probe');protocol.dataset.sectionOutline='false';protocol.dataset.probeStatus=probe.status;protocol.append(el('h6',ui('decision_probe_details')));field(protocol,'paper_probe_hypothesis',pick(probe,'hypothesis'));const grid=el('div','','analysis-protocol-grid');for(const key of ['design','metrics','decision_rule']){const block=el('section','','analysis-protocol-field');block.dataset.sectionOutline='false';block.append(el('h6',ui('probe_'+key)),el('p',pick(probe,key)));grid.append(block);}protocol.append(grid);body.append(protocol);}else body.append(el('p',ui('analysis_focus_probe_pending'),'meta'));
  card.append(body);section.append(card);
 }parent.append(section);
}
// Research-entry candidates follow the published report; route evidence remains complete.
function reportPrioritySelection(m){
 const report=(m.insight_reports||[]).filter(r=>r.status==='published'&&r.scope_id===current.scope&&r.period_id===current.period).sort((a,b)=>b.reviewed_at.localeCompare(a.reviewed_at)||b.report_id.localeCompare(a.report_id))[0];
 if(!report)return null;
 const papers=(m.insight_report_papers||[]).filter(p=>p.report_id===report.report_id);
 // Existing reports used route-level priority; keep their display until cutover.
 if(!papers.some(p=>p.priority_zh==='条件优先'))return null;
 return {report,papers:papers.filter(p=>p.priority_zh==='条件优先').sort((a,b)=>a.position-b.position)};
}
function reportPrioritySources(m){
 const selection=reportPrioritySelection(m);
 return selection?new Set(selection.papers.map(p=>p.source_id+'|'+p.observed_version)):null;
}
function priorityRouteRefs(assessment,refs,prioritySources){
 return prioritySources?refs.filter(r=>prioritySources.has(r.source_id+'|'+r.observed_version)):(assessment.priority_zh==='优先穿刺'?refs:[]);
}
function reportResearchChoices(m,rows){
 const selection=reportPrioritySelection(m),prioritySources=reportPrioritySources(m),candidates=[];
 for(const assessment of rows){for(const ref of priorityRouteRefs(assessment,m.monthly_route_evidence.filter(r=>r.story_id===assessment.story_id),prioritySources)){const paper=selection?.papers.find(p=>p.source_id===ref.source_id&&p.observed_version===ref.observed_version);candidates.push({assessment,ref,paper});}}
 const priorities=[...new Map(candidates.map(candidate=>[candidate.ref.summary_id,candidate])).values()].sort((a,b)=>(a.paper?.position??a.assessment.position)-(b.paper?.position??b.assessment.position));
 return {selection,priorities};
}
function reportFactsHref(ref){const target=new URL('monthly.html',location.href);target.searchParams.set('month',current.period);target.searchParams.set('scope',current.scope);target.searchParams.set('paper',ref.summary_id);target.hash='monthly-route-report';return target.pathname+target.search+target.hash;}
function bindReportArgumentJump(link,id){
 link.href='#'+id;link.addEventListener('click',event=>{if(event.ctrlKey||event.metaKey||event.shiftKey||event.altKey||event.button)return;const target=document.getElementById(id);if(!target)return;event.preventDefault();event.stopPropagation();const appendix=document.getElementById('ascend');if(appendix?.tagName==='DETAILS')appendix.open=true;history.replaceState(null,'',location.pathname+location.search+'#'+id);target.tabIndex=-1;target.scrollIntoView({block:'start'});target.focus({preventScroll:true});});
}
function reportExcerpt(value){const text=value.trim(),end=text.search(/[。！？]|[.!?](?=\s|$)/);return end<0?text:text.slice(0,end+1);}
// A later evidence selection can have a current web synthesis before a new
// slide report exists. Keep its revisioned judgments separate from old files.
function editorialSelection(m){
 if((m.insight_reports||[]).some(r=>r.status==='published'&&r.scope_id===current.scope&&r.period_id===current.period))return null;
 const rows=(m.monthly_route_insights||[...(m.stories?.values()||[])]).filter(r=>r.scope_id===current.scope&&r.period_id===current.period&&r.selection_tier);
 return rows.length?{rows:rows.filter(r=>selected(m,r.story_id)).sort((a,b)=>a.position-b.position||a.story_id.localeCompare(b.story_id))}:null;
}
function editorialRefs(m,story){return [...new Map(m.monthly_route_evidence.filter(r=>r.story_id===story.story_id).map(r=>[r.summary_id,r])).values()];}
function editorialReview(summary){return ui(summary.review_status==='method_results_checked'?'editorial_review_sections':'editorial_review_abstract')+' · '+summary.evidence_locator+' · '+summary.reviewed_at;}
function analysisFrame(editorial){
 const labels=[
  ['#insight-report-presentation [data-i18n-key="deck_title"]','deck_title'],
  ['#insight-report-presentation [data-i18n-key="analysis_report_hint"]','analysis_report_hint'],
  ['#insight-report-presentation [data-i18n-key="deck_relation"]','deck_relation'],
  ['.analysis-reading-navigation a[href="#insight-report-presentation"]','analysis_report_link'],
  ['.analysis-reading-navigation a[href="#analysis-focus"]','analysis_overview_link'],
  ['.analysis-reading-navigation a[href="#ascend"]','analysis_decisions_link'],
  ['#ascend .analysis-section-heading h3','analysis_route_title'],
  ['#ascend .analysis-section-note','analysis_route_note']
 ];
 const replacements={deck_title:'editorial_attachment_title',analysis_report_hint:'editorial_attachment_hint',deck_relation:'editorial_attachment_relation',analysis_report_link:'editorial_attachment_title',analysis_overview_link:'editorial_source_index',analysis_decisions_link:'editorial_judgments',analysis_route_title:'editorial_judgments',analysis_route_note:'editorial_judgments_help'};
 for(const [selector,key] of labels){const node=document.querySelector?.('[data-analysis-frame-key="'+key+'"]')||document.querySelector?.(selector);if(node){node.dataset.analysisFrameKey=key;node.setAttribute('data-i18n-key',editorial?replacements[key]:key);node.textContent=ui(editorial?replacements[key]:key);}}
 const section=document.getElementById('insight-report-presentation');if(section){section.dataset.sectionLabel=editorial?'历史演示附件':'洞察报告';section.dataset.sectionLabelEn=editorial?'Historical presentation files':'Current insight report';}
}
function renderEditorialAnalysis(m,rows){
 const root=document.getElementById('ascend-cards'),overview=document.getElementById('analysis-summary'),focus=document.getElementById('analysis-focus-cards'),meta=document.getElementById('analysis-meta');
 root.replaceChildren();overview?.replaceChildren();focus?.replaceChildren();if(overview)delete overview.dataset.reportId;
 const priorities=rows.filter(r=>r.selection_tier==='key_progress'),uniqueRefs=[...new Map(rows.flatMap(r=>editorialRefs(m,r)).map(r=>[r.summary_id,r])).values()];
 const title=document.getElementById('home-judgement');if(title){title.textContent=ui('editorial_report_title');title.dataset.synthesisContext=[current.revision,current.scope,current.period,current.locale].join('|');}
 const intro=document.querySelector?.('#insight-overview .analysis-intro');if(intro){intro.removeAttribute('data-i18n-key');intro.textContent=ui('editorial_report_intro');}
 const reviewed=rows.map(r=>r.checked_at).sort().at(-1)||'';
 if(meta)meta.textContent=current.period+' · '+ui('analysis_reviewed')+' '+reviewed+' · '+uniqueRefs.length+' '+ui('editorial_selected_papers')+' · '+['key_progress','technical_watch','boundary_case'].map(tier=>rows.filter(r=>r.selection_tier===tier).length+' '+ui('editorial_tier_'+tier)).join(' / ');
 const focusHeading=document.querySelector?.('#analysis-focus>h3'),focusHelp=document.querySelector?.('#analysis-focus>.reader-note');if(focusHeading){focusHeading.textContent=ui('editorial_source_index');focusHeading.setAttribute('data-i18n-key','editorial_source_index');}if(focusHelp){focusHelp.textContent=ui('editorial_source_help');focusHelp.setAttribute('data-i18n-key','editorial_source_help');}
 if(!rows.length){root.append(el('p',ui('editorial_empty'),'reader-note'));return;}
 if(overview){
  const header=el('header','','analysis-choice-heading');header.append(el('h3',ui('editorial_key_choices')),el('p',ui('editorial_key_help')));overview.append(header);
  const grid=el('div','','analysis-choice-grid');
  for(const [index,story] of priorities.entries()){
   const refs=editorialRefs(m,story),card=el('article','','analysis-choice-card');card.dataset.sectionOutline='false';card.dataset.storyId=story.story_id;card.dataset.claimKind='analyst_synthesis';
   const identity=el('div','','analysis-choice-identity');identity.append(el('p',String(index+1).padStart(2,'0')+' · '+ui('editorial_tier_key_progress'),'analysis-choice-meta'));const heading=el('h4'),link=el('a',pick(story,'title'));bindReportArgumentJump(link,story.story_id);heading.append(link);identity.append(heading);card.append(identity);
   const reason=el('div','','analysis-choice-why');reason.append(el('strong',ui('editorial_selection_reason')),el('p',pick(story,'selection_reason'),'analysis-choice-reason'));card.append(reason);
   const gate=el('p','','analysis-choice-gate');gate.append(el('strong',ui('editorial_viewpoint')+'：'),document.createTextNode(pick(story,'viewpoint')));card.append(gate);
   const reviews=[...new Set(refs.map(ref=>ui(m.paperSummaries.get(ref.summary_id).review_status==='method_results_checked'?'editorial_review_sections':'editorial_review_abstract')))];card.append(el('p',reviews.join(' · '),'meta'));
   const links=el('div','','analysis-choice-links'),detail=el('a',ui('editorial_read_argument'));bindReportArgumentJump(detail,story.story_id);links.append(detail);for(const ref of refs){const facts=el('a',ui('editorial_read_facts'));facts.href=reportFactsHref(ref);links.append(facts);}card.append(links);grid.append(card);
  }overview.append(grid);
 }
 if(focus){
  if(!priorities.length)focus.append(el('p',ui('editorial_focus_empty'),'reader-note'));
  const seen=new Set();for(const story of priorities)for(const ref of editorialRefs(m,story)){
   if(seen.has(ref.summary_id))continue;seen.add(ref.summary_id);const summary=m.paperSummaries.get(ref.summary_id),source=m.sources.get(ref.source_id),card=el('article','','analysis-focus-card analysis-source-index-row');card.dataset.sectionOutline='false';card.dataset.storyId=story.story_id;card.dataset.sourceId=ref.source_id;card.dataset.summaryId=ref.summary_id;card.dataset.claimKind='analyst_synthesis';
   const heading=el('h4'),link=el('a',source.title);link.href=url(summary.evidence_url);link.target='_blank';link.rel='noopener noreferrer';heading.append(link);card.append(heading,el('span',ref.observed_version,'analysis-source-index-version'),el('p',editorialReview(summary),'meta'));
   const actions=el('div','','analysis-source-index-links'),facts=el('a',ui('editorial_read_facts')),argument=el('a',ui('editorial_read_argument'));facts.href=reportFactsHref(ref);bindReportArgumentJump(argument,story.story_id);actions.append(facts,argument);card.append(actions);focus.append(card);
  }
 }
 let groupIndex=0;
 for(const tier of ['key_progress','technical_watch','boundary_case']){
  const stories=rows.filter(r=>r.selection_tier===tier);if(!stories.length)continue;
  const group=el('section','','analysis-route-group');group.id='analysis-priority-'+(++groupIndex);group.dataset.sectionLabel=({key_progress:'重点研究',technical_watch:'技术观察',boundary_case:'边界案例'})[tier];group.dataset.sectionLabelEn=({key_progress:'Key research',technical_watch:'Technical watch',boundary_case:'Boundary cases'})[tier];group.dataset.sectionLevel='3';
  const heading=el('div','','analysis-group-heading');heading.append(el('h4',ui('editorial_tier_'+tier)),el('span',String(stories.length),'analysis-count'));group.append(heading);
  for(const story of stories){
   const refs=editorialRefs(m,story),allRefs=m.monthly_route_evidence.filter(r=>r.story_id===story.story_id),shell=el('article','','analysis-route-shell'),card=el('section','','analysis-route');shell.dataset.sectionOutline='false';card.id=story.story_id;card.dataset.sectionOutline='false';card.dataset.storyId=story.story_id;card.dataset.editorialTier=tier;card.dataset.claimKind='analyst_synthesis';
   const header=el('header','','analysis-route-summary'),headline=el('div','','analysis-route-headline');headline.append(el('h5',pick(story,'title')));header.append(el('span',String(story.position+1).padStart(2,'0'),'analysis-route-number'),headline);card.append(header);
   const body=el('div','','analysis-route-body'),grid=el('div','','analysis-reason-grid');
   for(const [key,value] of [['editorial_mechanism',pick(story,'synthesis')],['editorial_viewpoint',pick(story,'viewpoint')]]){const block=el('section','','analysis-reason-block');block.dataset.sectionOutline='false';block.append(el('h6',ui(key)),el('p',value));grid.append(block);}body.append(grid);
   if(pick(story,'implication')!==pick(story,'viewpoint')){const next=el('section','','analysis-reason-block');next.dataset.sectionOutline='false';next.append(el('h6',ui('editorial_next_check')),el('p',pick(story,'implication')));body.append(next);}
   const boundary=el('div','','analysis-boundary');boundary.append(el('h6',ui('decision_boundary')),el('p',pick(story,'boundary')));body.append(boundary);
   const evidence=el('section','','analysis-proof');evidence.dataset.sectionOutline='false';evidence.append(el('h6',ui('editorial_evidence_depth')));
   for(const ref of refs){const summary=m.paperSummaries.get(ref.summary_id),source=m.sources.get(ref.source_id),entry=el('article','','analysis-paper-probe');entry.id=story.story_id+'--'+ref.summary_id;entry.dataset.sectionOutline='false';entry.dataset.sourceId=ref.source_id;entry.dataset.summaryId=ref.summary_id;entry.dataset.reviewStatus=summary.review_status;entry.append(el('h6',source.title+' · '+ref.observed_version,'analysis-paper-heading'));const link=el('a',ui('signal_primary'));link.href=url(summary.evidence_url);link.target='_blank';link.rel='noopener noreferrer';const facts=el('a',ui('editorial_read_facts'));facts.href=reportFactsHref(ref);const actions=el('div','','analysis-choice-links');actions.append(link,facts);entry.append(el('p',editorialReview(summary),'meta'),actions);evidence.append(entry);}body.append(evidence);card.append(body);shell.append(card);
   const map=el('div','','analysis-route-map');topics(map,allRefs.map(r=>r.compression_topic_id));shell.append(map);group.append(shell);
  }root.append(group);
 }
 notify();
}
function renderReportChoices(m,rows,root){
 if(!root)return;const word=(zh,en)=>current.locale==='en'?en:zh,{selection,priorities}=reportResearchChoices(m,rows);root.replaceChildren();
 if(selection)root.dataset.reportId=selection.report.report_id;else delete root.dataset.reportId;
 const intro=document.querySelector?.('#insight-overview .analysis-intro');if(intro){intro.removeAttribute('data-i18n-key');intro.textContent=word('本期动态保存事件与论文事实；这里说明研究选择、判断理由，以及继续或停止验证的条件。','Current updates retain event and paper facts. This report explains research choices, the reasoning behind them, and the conditions for continuing or stopping validation.');}
 if(!priorities.length){const link=el('a',word('查看本期研究判断与验证条件 →','Read this period’s assessments and validation gates →'),'analysis-evidence-link');bindReportArgumentJump(link,'ascend');root.append(link);return;}
 const reportSummary=selection?pick(selection.report,'summary'):'';if(reportSummary){const headline=reportExcerpt(reportSummary),title=document.getElementById('home-judgement');if(title){title.textContent=headline;title.dataset.synthesisContext=[current.revision,current.scope,current.period,current.locale].join('|');}if(intro){const rest=reportSummary.slice(headline.length).trim(),first=reportExcerpt(rest),second=reportExcerpt(rest.slice(first.length).trim());intro.textContent=first+' '+second;}}
 const header=el('header','','analysis-choice-heading');header.append(el('h3',word('本期研究选择','Research choices this period')),el('p',word('先看研究价值与继续条件，再按需查看原文和详细论证。以下均为研究建议。','Compare research value and continuation criteria before opening the source and detailed reasoning. These are research recommendations.')));root.append(header);
 const grid=el('div','','analysis-choice-grid');
 priorities.forEach(({assessment,ref,paper},index)=>{
  const probe=m.ascend_validation_probes.find(p=>p.assessment_id===assessment.assessment_id),card=el('article','','analysis-choice-card');card.dataset.sectionOutline='false';card.dataset.claimKind='analyst_recommendation';card.dataset.sourceId=ref.source_id;card.dataset.summaryId=ref.summary_id;card.dataset.assessmentId=assessment.assessment_id;if(selection)card.dataset.reportId=selection.report.report_id;if(probe)card.dataset.probeStatus=probe.status;
  const identity=el('div','','analysis-choice-identity');identity.append(el('p',String(index+1).padStart(2,'0')+' · '+(paper?pick(paper,'priority'):routePriority(assessment))+' · '+ref.observed_version,'analysis-choice-meta'));
  const heading=el('h4'),title=el('a',pick(assessment,'title'));bindReportArgumentJump(title,assessment.assessment_id);heading.append(title);identity.append(heading);card.append(identity);const reason=el('div','','analysis-choice-why');reason.append(el('strong',word('研究价值','Research value')),el('p',reportExcerpt(paper?pick(paper,'reason'):pick(assessment,'rationale')),'analysis-choice-reason'));card.append(reason);
  const gate=el('p','','analysis-choice-gate');gate.append(el('strong',word('推进门槛：','Validation gate: ')),document.createTextNode(probe?reportExcerpt(pick(probe,'decision_rule')):word('尚未登记完整条件，先补充验证设计。','Complete the validation design before treating this as an actionable recommendation.')));card.append(gate);
  const links=el('div','','analysis-choice-links'),argument=el('a',word('论证与验证条件 ↓','Reasoning and validation gates ↓')),facts=el('a',word('本期动态中的原文事实 →','Paper facts in current updates →'));bindReportArgumentJump(argument,assessment.assessment_id);facts.href=reportFactsHref(ref);links.append(argument,facts);card.append(links);grid.append(card);
 });root.append(grid);const all=el('a',word('查看全部 '+rows.length+' 条研究判断 →','Read all '+rows.length+' research assessments →'),'analysis-all-assessments');bindReportArgumentJump(all,'ascend');root.append(all);
}
function renderResearchFocus(m,rows){
 const root=document.getElementById('analysis-focus-cards');if(!root)return;root.replaceChildren();
 root.dataset.sectionOutline='false';
 const word=(zh,en)=>current.locale==='en'?en:zh,chapter=document.getElementById('analysis-focus'),heading=chapter?.querySelector?.('h3'),note=chapter?.querySelector?.('.reader-note');if(heading){heading.removeAttribute('data-i18n-key');heading.textContent=word('重点论文原文索引','Selected-paper source index');}if(note){note.removeAttribute('data-i18n-key');note.textContent=word('查阅同一版本的原文事实，或直达对应论证与验证建议。','Read facts for the cited paper version, or jump to its reasoning and proposed validation.');}
 const {selection,priorities}=reportResearchChoices(m,rows);
 if(!priorities.length){root.append(el('p',ui('analysis_focus_empty'),'reader-note'));return;}
 for(const {assessment:a,ref,paper} of priorities){
  const source=m.sources.get(ref.source_id),summary=m.paperSummaries.get(ref.summary_id),card=el('article','','analysis-focus-card analysis-source-index-row');
  check(source&&summary&&summary.source_id===ref.source_id&&summary.observed_version===ref.observed_version,'Unbound priority paper');
  card.dataset.sectionOutline='false';card.dataset.assessmentId=a.assessment_id;card.dataset.claimKind='analyst_recommendation';card.dataset.sourceId=ref.source_id;card.dataset.summaryId=ref.summary_id;if(selection)card.dataset.reportId=selection.report.report_id;
  const title=el('h4'),link=el('a',source.title);link.href=url(summary.evidence_url);link.target='_blank';link.rel='noopener noreferrer';title.append(link);card.append(title,el('span',ref.observed_version,'analysis-source-index-version'));
  const actions=el('div','','analysis-source-index-links'),facts=el('a',word('本期事实 →','Paper facts →')),detail=el('a',word('论证与验证 ↓','Reasoning and validation ↓'),'analysis-evidence-link');facts.href=reportFactsHref(ref);bindReportArgumentJump(detail,a.assessment_id+'--'+ref.summary_id);actions.append(facts,detail);card.append(actions);root.append(card);
 }
}

function renderAnalysis(m){
 const root=document.getElementById('ascend-cards');if(!root)return;
 root.dataset.sectionOutline='false';root.dataset.sectionLabel='研究取舍与论证';root.dataset.sectionLabelEn='Research decisions and reasoning';
 const appendix=document.getElementById('ascend');if(appendix){appendix.dataset.sectionId=appendix.id;appendix.dataset.sectionLabel='研究取舍与论证';appendix.dataset.sectionLabelEn='Research decisions and reasoning';appendix.dataset.sectionLevel='2';}
 const editorial=editorialSelection(m);analysisFrame(Boolean(editorial));if(editorial){renderEditorialAnalysis(m,editorial.rows);return;}
 root.replaceChildren();
 const rows=m.ascend_route_assessments.filter(a=>selected(m,a.story_id)).sort((a,b)=>a.position-b.position);
 const overview=document.getElementById('analysis-summary'),meta=document.getElementById('analysis-meta'),prioritySources=reportPrioritySources(m);overview?.replaceChildren();renderResearchFocus(m,rows);
 if(!rows.length){root.append(el('p',ui('ascend_decision_empty')));if(meta)meta.textContent=current.period;return;}
 renderReportChoices(m,rows,overview);
 const reviewed=rows.map(r=>r.reviewed_at).sort().at(-1),refsAll=m.monthly_route_evidence.filter(r=>rows.some(a=>a.story_id===r.story_id));
 if(meta)meta.textContent=current.period+' / '+ui('analysis_reviewed')+' '+reviewed+' / '+new Set(refsAll.map(r=>r.source_id)).size+' '+ui('analysis_sources');
 const groups=new Map();for(const a of rows){if(!groups.has(a.priority_zh))groups.set(a.priority_zh,[]);groups.get(a.priority_zh).push(a);}
 let groupIndex=0;
 for(const list of groups.values()){
  const groupId='analysis-priority-'+(++groupIndex),group=el('section','','analysis-route-group');group.id=groupId;group.dataset.sectionLabel=list[0].priority_zh==='优先穿刺'?'优先研究':list[0].priority_zh;group.dataset.sectionLabelEn=list[0].priority_zh==='优先穿刺'?'Priority research':list[0].priority_en;group.dataset.sectionLevel='3';
  const heading=el('div','','analysis-group-heading');heading.append(el('h4',routePriority(list[0])),el('span',list.length+' '+ui('analysis_routes'),'analysis-count'));group.append(heading);
  for(const a of list){
   const story=m.stories.get(a.story_id),refs=m.monthly_route_evidence.filter(r=>r.story_id===a.story_id),routeShell=el('article','','analysis-route-shell'),card=el('section','','analysis-route');card.id=a.assessment_id;card.dataset.sectionOutline='false';routeShell.dataset.sectionOutline='false';card.dataset.claimKind='analyst_recommendation';
   const summary=el('header','','analysis-route-summary'),number=el('span',String(a.position).padStart(2,'0'),'analysis-route-number'),headline=el('div','','analysis-route-headline');
   headline.append(el('h5',pick(a,'title')));
   summary.append(number,headline);card.append(summary);
   const map=el('div','','analysis-route-map');topics(map,refs.map(r=>r.compression_topic_id));routeShell.append(map);
   const candidateRefs=priorityRouteRefs(a,refs,prioritySources);
   if(candidateRefs.length){
    const candidates=el('ul','','analysis-route-paper-links');candidates.setAttribute('aria-label',ui('paper_probe_candidates_short'));
    for(const ref of [...new Map(candidateRefs.map(r=>[r.summary_id,r])).values()]){const li=el('li'),link=el('a',m.sources.get(ref.source_id).title+' · '+ref.observed_version),href=new URL('monthly.html',location.href);href.searchParams.set('month',current.period);href.searchParams.set('scope',current.scope);href.searchParams.set('paper',ref.summary_id);href.hash='monthly-route-report';link.href=href.pathname+href.search+href.hash;li.append(link);candidates.append(li);}routeShell.append(el('p',ui('paper_probe_candidates_short'),'analysis-candidate-label'),candidates);
   }
   const body=el('div','','analysis-route-body'),grid=el('div','','analysis-reason-grid');
   for(const [key,value] of [['decision_reason',pick(a,'rationale')],['decision_choice',pick(a,'recommendation')]]){const block=el('section','','analysis-reason-block');block.dataset.sectionOutline='false';block.append(el('h6',ui(key)),el('p',value));grid.append(block);}body.append(grid);
   const boundary=el('div','','analysis-boundary');boundary.append(el('h6',ui('decision_boundary')),el('p',pick(story,'boundary')));body.append(boundary);
   const proof=el('section','','analysis-proof');proof.dataset.sectionOutline='false';proof.append(el('h6',ui('decision_sources')+' · '+new Set(refs.map(r=>r.source_id)).size));const sources=el('ul');for(const id of [...new Set(refs.map(r=>r.source_id))]){const li=el('li');primary(li,m.sources.get(id));sources.append(li);}proof.append(sources);body.append(proof);
   const probe=m.ascend_validation_probes.find(p=>p.assessment_id===a.assessment_id);
   const probeRefs=prioritySources?candidateRefs:refs;
   if(probeRefs.length)paperProbeCandidates(body,m,a,probeRefs,probe);
   const detail=el('a',ui('decision_read_route'),'analysis-evidence-link'),target=new URL('monthly.html',location.href);target.searchParams.set('month',current.period);target.searchParams.set('scope',current.scope);target.searchParams.set('route',a.story_id);target.hash='monthly-route-report';detail.href=target.pathname+target.search+target.hash;body.append(detail);card.append(body);routeShell.prepend(card);group.append(routeShell);
  }
  root.append(group);
 }
 notify();
}
// Restore a cold report link after its asynchronous content has been mounted.
// A later render at the same location must preserve the reader's scroll position.
const restoredReportAnchors=new Set();
function restoreReportAnchor(m){
 if(current?.view!=='home')return;
 const hash=location.hash;let id;
 try{id=decodeURIComponent(hash.slice(1));}catch{return;}
 const ownedAnchor=id==='analysis-focus'||id==='ascend'||/^analysis-priority-\d+$/.test(id)||(m.ascend_route_assessments||[]).some(a=>id===a.assessment_id||m.monthly_route_evidence.some(r=>r.story_id===a.story_id&&id===a.assessment_id+'--'+r.summary_id))||(m.monthly_route_insights||[]).some(story=>id===story.story_id||m.monthly_route_evidence.some(ref=>ref.story_id===story.story_id&&id===story.story_id+'--'+ref.summary_id));
 if(!ownedAnchor||!document.getElementById(id))return;
 const contextKey=current.key||[current.revision,current.scope,current.period].join('|'),key=contextKey+'|'+hash;
 if(restoredReportAnchors.has(key))return;
 restoredReportAnchors.add(key);if(restoredReportAnchors.size>48)restoredReportAnchors.delete(restoredReportAnchors.values().next().value);
 const active=()=>{
  const activeKey=current?.key||[current?.revision,current?.scope,current?.period].join('|');
  return current?.view==='home'&&activeKey===contextKey&&location.hash===hash;
 };
 requestAnimationFrame(()=>{
  if(!active()){restoredReportAnchors.delete(key);return;}
  requestAnimationFrame(()=>{
   if(!active()){restoredReportAnchors.delete(key);return;}
   const target=document.getElementById(id);if(target)target.scrollIntoView({block:'start',behavior:'auto'});else restoredReportAnchors.delete(key);
  });
 });
}
// Reader state is presentation-only; evidence and asset validation stay with renderReports.
const reportPositions=new Map();
function mountReportReader(viewer,slides,title,assetUrl,stateKey,figures=[],pageTitles=[]){
 const saved=reportPositions.get(stateKey)||{page:0,zoom:'fit'};
 let page=Math.min(saved.page,slides.length-1),zoom=saved.zoom,activeFigure=null,returnFocus=null;
 const remember=()=>{reportPositions.set(stateKey,{page,zoom});if(reportPositions.size>24)reportPositions.delete(reportPositions.keys().next().value);};
 const dialog=el('dialog','','analysis-reader-dialog');dialog.setAttribute('aria-label',title);
 const header=el('header','','analysis-reader-header'),heading=el('p',title,'analysis-reader-title'),close=el('button',ui('deck_reader_close'),'analysis-reader-close');close.type='button';header.append(heading,close);
 const stage=el('div','','analysis-report-stage'),canvas=el('figure','','analysis-report-canvas'),large=el('img'),status=el('p','','analysis-reader-status');status.setAttribute('role','status');
 large.decoding='async';canvas.append(large);stage.append(canvas,status);stage.tabIndex=0;stage.setAttribute('aria-label',ui('deck_zoom_help'));
 const controls=(expanded)=>{
  const bar=el('div','',expanded?'analysis-reader-toolbar':'analysis-slide-controls'),previous=el('button',ui('deck_previous'),'analysis-reader-nav'),next=el('button',ui('deck_next'),'analysis-reader-nav'),counter=el('span','','analysis-reader-counter'),jump=el('select','','analysis-slide-select');
  previous.type=next.type='button';jump.setAttribute('aria-label',ui('analysis_slide_jump'));if(!expanded){counter.setAttribute('role','status');counter.setAttribute('aria-live','polite');}
  for(let i=0;i<slides.length;i++){const option=el('option',ui('deck_slide')+' '+(i+1)+(pageTitles[i]?' · '+pageTitles[i]:''));option.value=String(i);jump.append(option);}
  previous.addEventListener('click',()=>move(-1));next.addEventListener('click',()=>move(1));jump.addEventListener('change',()=>{const value=Number(jump.value);check(Number.isInteger(value)&&value>=0&&value<slides.length,'Invalid presentation page');page=value;activeFigure=null;show();});
  bar.append(previous,counter,next,jump);return {bar,previous,next,counter,jump};
 };
 const inline=controls(false),expanded=controls(true),zoomLabel=el('label',ui('deck_zoom'),'analysis-reader-zoom-label'),zoomSelect=el('select','','analysis-reader-zoom');zoomSelect.setAttribute('aria-label',ui('deck_zoom'));
 for(const [value,label] of [['fit',ui('deck_zoom_fit')],['native',ui('deck_zoom_native')],['125','125%'],['150','150%'],['200','200%'],['300','300%']]){const option=el('option',label);option.value=value;zoomSelect.append(option);}
 zoomSelect.value=zoom;zoomLabel.append(zoomSelect);expanded.bar.append(zoomLabel);
 const help=el('p',ui('deck_zoom_help'),'analysis-reader-help');dialog.append(header,expanded.bar,help,stage);
 const open=el('button',ui('deck_open_reader'),'analysis-reader-open');open.type='button';open.setAttribute('aria-haspopup','dialog');inline.bar.append(open);
 const preview=el('button','','analysis-preview-open'),image=el('img');preview.type='button';preview.setAttribute('aria-label',ui('deck_open_reader'));image.decoding='async';preview.append(image);
 const previewStatus=el('p','','analysis-reader-status');previewStatus.setAttribute('role','status');
 const imageState=(img,label)=>{img.addEventListener('load',()=>{label.textContent='';label.hidden=true;});img.addEventListener('error',()=>{label.textContent=ui('deck_image_error');label.hidden=false;});};imageState(image,previewStatus);imageState(large,status);
 const originals=[];
 function addOriginalControls(bar,isInline){for(const [kind,key] of [['tech','deck_tech_figure'],['results','deck_results_figure']]){const button=el('button',ui(key),'analysis-reader-nav');button.type='button';if(isInline)button.setAttribute('aria-haspopup','dialog');button.addEventListener('click',()=>{const asset=figureAsset(kind);if(asset)launch(asset,button);});bar.append(button);originals.push({kind,button});}}
 addOriginalControls(inline.bar,true);
 const figureAsset=kind=>figures.find(a=>a.format==='figure-'+String(page+1).padStart(2,'0')+'-'+kind);
 const whole=el('button',ui('deck_whole_slide'),'analysis-reader-nav');whole.type='button';whole.addEventListener('click',()=>launch());expanded.bar.append(whole);addOriginalControls(expanded.bar,false);
 function move(delta){const value=page+delta;if(value<0||value>=slides.length)return;page=value;activeFigure=null;show();}
 function show(){
  remember();for(const bar of [inline,expanded]){bar.counter.textContent=(page+1)+' / '+slides.length;bar.jump.value=String(page);bar.previous.disabled=page===0;bar.next.disabled=page===slides.length-1;}
  for(const {kind,button} of originals)button.hidden=!figureAsset(kind);
  whole.hidden=!activeFigure;help.textContent=ui(activeFigure?'deck_original_figure_help':'deck_zoom_help');
  const src=assetUrl(slides[page]),alt=title+' · '+ui('deck_slide')+' '+(page+1)+(pageTitles[page]?' · '+pageTitles[page]:'');
  const largeSrc=activeFigure?assetUrl(activeFigure):src,largeAlt=activeFigure?alt+' · '+ui(activeFigure.format.endsWith('-tech')?'deck_tech_figure':'deck_results_figure'):alt;
  heading.textContent=largeAlt;
  if(image.getAttribute('src')!==src){previewStatus.hidden=false;previewStatus.textContent=ui('deck_image_loading');image.alt=alt;image.src=src;}
  if(dialog.open&&large.getAttribute('src')!==largeSrc){status.hidden=false;status.textContent=ui('deck_image_loading');large.alt=largeAlt;large.src=largeSrc;stage.scrollTop=stage.scrollLeft=0;}
 }
 const launch=(asset=null,trigger=open)=>{activeFigure=asset;if(!dialog.open){returnFocus=trigger;dialog.showModal();}canvas.dataset.zoom=zoom;zoomSelect.value=zoom;show();stage.focus();};open.addEventListener('click',()=>launch());preview.addEventListener('click',()=>launch(null,preview));
 close.addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>{remember();(returnFocus&&!returnFocus.hidden?returnFocus:open).focus();});
 zoomSelect.addEventListener('change',()=>{zoom=zoomSelect.value;canvas.dataset.zoom=zoom;remember();});
 dialog.addEventListener('keydown',e=>{if(e.target.closest('select,input,textarea')||e.altKey||e.ctrlKey||e.metaKey)return;if(['ArrowRight','ArrowLeft','PageDown','PageUp','Home','End'].includes(e.key)){e.preventDefault();if(e.key==='Home'||e.key==='End'){page=e.key==='Home'?0:slides.length-1;activeFigure=null;show();}else move(['ArrowRight','PageDown'].includes(e.key)?1:-1);}});
 viewer.append(inline.bar,preview,previewStatus,dialog);show();
 const dispose=()=>{if(dialog.open)dialog.close();remember();viewer.replaceChildren();};
 dispose.goTo=value=>{check(Number.isInteger(value)&&value>=0&&value<slides.length,'Invalid presentation page');page=value;activeFigure=null;show();launch();};return dispose;
}


function renderReports(m){
 const archive=current.view==='reports',word=(zh,en)=>current.locale==='en'?en:zh,version=r=>r.report_id.match(/-v\d+$/)?.[0].slice(1)||'',byDate=(a,b)=>b.reviewed_at.localeCompare(a.reviewed_at)||(Number(version(b).slice(1))||0)-(Number(version(a).slice(1))||0)||b.report_id.localeCompare(a.report_id);
 for(const id of archive?['insight-deck-archive']:['insight-deck-content']){
  const root=document.getElementById(id);if(!root)continue;for(const d of root.querySelectorAll('dialog[open]'))d.close();root.replaceChildren();
  const scoped=m.insight_reports.filter(r=>r.scope_id===(m.reportScope||current.scope)&&r.period_id===current.period&&(!archive||r.period_id>='2026-10')),rows=scoped.filter(r=>r.status==='published').sort(byDate),history=archive?scoped.filter(r=>r.status==='superseded').sort(byDate):[];
  if(!rows.length&&!history.length){root.append(el('p',ui('deck_not_available'),'meta'));continue;}
  const assetUrl=a=>{check(a,'Missing report asset');const target=new URL(a.public_path,location.origin);check(target.origin===location.origin&&target.pathname.startsWith('/business_insight/cloud_core/reports/')&&/^[a-f0-9]{64}$/.test(a.content_sha256)&&a.binary_sha256===a.content_sha256,'Invalid report asset');return target.href;};
  if(m.reportFallback&&rows.length&&!archive){
   root.append(el('p',ui('editorial_attachment_relation'),'reader-note'));
   for(const r of rows){
    const card=el('article','','analysis-archive-version');card.dataset.reportId=r.report_id;card.dataset.reportStatus=r.status;card.dataset.historicalAttachment='true';card.dataset.reportScope=r.scope_id;card.append(el('p',ui('editorial_attachment_title')+' · '+r.reviewed_at+' · '+version(r),'analysis-archive-badge'),el('h3',pick(r,'title')),el('p',pick(r,'summary'),'analysis-archive-summary'));
    const assets=m.insight_report_assets.filter(a=>a.report_id===r.report_id&&['pdf','pptx'].includes(a.format));check(assets.length===2&&new Set(assets.map(a=>a.format)).size===2,'Incomplete historical report files');
    const actions=el('div','','analysis-archive-links');for(const format of ['pdf','pptx']){const asset=assets.find(a=>a.format===format),link=el('a',ui(format==='pdf'?'editorial_historical_pdf':'editorial_historical_pptx'));link.href=assetUrl(asset);link.target='_blank';link.rel='noopener noreferrer';if(format==='pptx')link.download=asset.public_path.split('/').pop();actions.append(link);}
    const archiveLink=el('a',ui('editorial_open_archive'));const target=new URL('index.html',location.href);target.searchParams.set('month',current.period);target.searchParams.set('scope',r.scope_id);target.hash='view-reports';archiveLink.href=target.pathname+target.search+target.hash;actions.append(archiveLink);card.append(actions);root.append(card);
   }continue;
  }
  const currentHost=archive?el('section','','analysis-archive-current'):root;
  if(archive&&rows.length){currentHost.append(el('h3',m.reportFallback?ui('editorial_latest_saved_files'):word('当前报告','Current report')),el('p',m.reportFallback?ui('editorial_attachment_relation'):word('本期采用的版本。历史版本保留在下方，供回看当时的内容；不作为当前结论。','The version used for this period. Earlier versions below preserve their original content and are not the current assessment.'),'analysis-archive-note'));root.append(currentHost);}
  for(const r of rows){
   const papers=m.insight_report_papers.filter(p=>p.report_id===r.report_id).sort((a,b)=>a.position-b.position);
   const assets=m.insight_report_assets.filter(a=>a.report_id===r.report_id),figures=assets.filter(a=>/^figure-\d{2}-(tech|results)$/.test(a.format));
   check(new Set(figures.map(a=>a.format)).size===figures.length,'Duplicate report figures');
   if(figures.length)check(papers.filter(p=>p.selection_status==='illustrated').every(p=>['tech','results'].every(kind=>figures.some(a=>a.format==='figure-'+String(p.slide_number).padStart(2,'0')+'-'+kind))),'Incomplete original figures');
   check(r.status==='published'&&papers.length===r.candidate_count&&papers.filter(p=>p.selection_status==='illustrated').length===r.paper_count,'Incomplete report selection');
   const slides=assets.filter(a=>/^slide-\d{2}$/.test(a.format)).sort((a,b)=>a.format.localeCompare(b.format));check(slides.length===r.page_count&&['pdf','pptx'].every(f=>assets.some(a=>a.format===f)),'Incomplete report assets');
   const card=el('article','','card analysis-report-card');card.dataset.reportId=r.report_id;card.dataset.reportStatus=r.status;if(archive)card.append(el('p',(m.reportFallback?ui('editorial_latest_saved_files'):word('当前版本','Current version'))+(version(r)?' · '+version(r):''),'analysis-archive-badge'));card.append(el('h3',pick(r,'title')));const reportScope=el('details','','analysis-report-scope');reportScope.append(el('summary',ui('deck_report_scope')),el('p',pick(r,'summary')));card.append(reportScope,el('p',r.reviewed_at+' · '+r.paper_count+' '+ui('deck_papers')+' / '+r.candidate_count+' '+ui('deck_candidates')+' · '+r.page_count+' '+ui('deck_pages')+' · '+ui('deck_zh'),'meta'));
   const actions=el('div','','actions analysis-report-actions'),viewer=el('div','','analysis-report-viewer');
   const pdf=assets.find(a=>a.format==='pdf'),ppt=assets.find(a=>a.format==='pptx');
   const pageTitles=slides.map((_,i)=>{const p=papers.find(p=>p.selection_status==='illustrated'&&p.slide_number===i+1);return p?m.sources.get(p.source_id).title:'';});
   const stateKey=r.report_id+'|'+current.scope+'|'+current.period+'|'+slides.map(a=>a.content_sha256).join('|');let dispose=null;
   const button=el('button',ui('deck_open'),'btn');button.type='button';button.setAttribute('aria-expanded','false');button.addEventListener('click',()=>{if(dispose){dispose();dispose=null;button.textContent=ui('deck_open');button.setAttribute('aria-expanded','false');return;}dispose=mountReportReader(viewer,slides,pick(r,'title'),assetUrl,stateKey,figures,pageTitles);button.textContent=ui('deck_close');button.setAttribute('aria-expanded','true');});actions.append(button);
   for(const [a,label] of [[pdf,'deck_fullscreen'],[ppt,'deck_download']]){const link=el('a',ui(label),'btn analysis-report-secondary');link.href=assetUrl(a);link.target='_blank';link.rel='noopener noreferrer';if(a.format==='pptx')link.download=a.public_path.split('/').pop();actions.append(link);}card.append(actions,el('p',ui('deck_lazy_help'),'reader-note'),viewer);
   const selection=el('details','','analysis-report-selection');selection.append(el('summary',ui('deck_selection')));const list=el('ol');for(const p of papers){const li=el('li');primary(li,m.sources.get(p.source_id));li.append(el('p',pick(p,'priority')+' · '+pick(p,'reason'),'meta'));if(p.slide_number>0){const jumpTo=el('button',ui('deck_slide')+' '+p.slide_number+' ↗','analysis-reader-nav');jumpTo.type='button';jumpTo.addEventListener('click',()=>{if(!dispose)button.click();dispose.goTo(p.slide_number-1);});li.append(jumpTo);}topics(li,m.monthly_route_evidence.filter(e=>e.source_id===p.source_id).map(e=>e.compression_topic_id));list.append(li);}selection.append(list);card.append(selection);currentHost.append(card);if(id==='insight-deck-content'&&current.view==='home')button.click();
  }
  if(history.length){
   const section=el('section','','analysis-archive-history');section.append(el('h3',word('历史版本','Earlier versions')),el('p',word('以下版本已被替代，各项保留当时的摘要与原始文件。当前结论以本期报告为准。','These versions have been superseded. Their recorded summaries and original files remain available; use the current report for this period’s assessment.'),'analysis-archive-note'));
   const timeline=el('ol','','analysis-archive-timeline');
   for(const r of history){
    const item=el('li','','analysis-archive-version');item.id='report-version-'+r.report_id;item.dataset.reportId=r.report_id;item.dataset.reportStatus=r.status;
    const header=el('header','','analysis-archive-version-head'),date=el('time',r.reviewed_at);date.dateTime=r.reviewed_at;header.append(el('span',word('已被替代','Superseded')+(version(r)?' · '+version(r):''),'analysis-archive-badge'),date);item.append(header,el('h4',pick(r,'title')),el('p',word('该版摘要','Recorded summary'),'analysis-archive-summary-label'),el('p',pick(r,'summary'),'analysis-archive-summary'));
    const actions=el('div','','analysis-archive-links'),assets=m.insight_report_assets.filter(a=>a.report_id===r.report_id&&['pdf','pptx'].includes(a.format));check(assets.length===2&&new Set(assets.map(a=>a.format)).size===2,'Incomplete archived report files');
    for(const format of ['pdf','pptx']){const asset=assets.find(a=>a.format===format),link=el('a',format==='pdf'?word('阅读该版 PDF ↗','Read this PDF ↗'):word('下载该版 PPTX','Download this PPTX'));link.href=assetUrl(asset);link.target='_blank';link.rel='noopener noreferrer';if(format==='pptx')link.download=asset.public_path.split('/').pop();actions.append(link);}item.append(actions);timeline.append(item);
   }section.append(timeline);root.append(section);
  }
 }
 notify();
}

function renderMonthlyFrame(){
 const word=(zh,en)=>current.locale==='en'?en:zh;
 const set=(selector,zh,en)=>{const n=document.querySelector(selector);if(n)n.textContent=word(zh,en);};
 set('#monthly>h3',current.period+' · 本期动态',current.period+' · Current updates');
 set('.monthly-overview-intro','先看新方法与实验结果，再看实现条件和需求变化。论文按首投或修订日期归入本月；既有产业能力另列。','Read new methods and results, implementation conditions, then demand signals. Papers follow submission or revision dates; existing capabilities are listed separately.');
 const labels=[['既有研读论文','Previously reviewed papers'],['已收录的本月产业发布','Monthly releases included'],['热点信号','Market signals']];
 document.querySelectorAll('.monthly-stream-metrics>a>span').forEach((n,i)=>{n.textContent=word(...labels[i]);});
 set('.current-updates-navigation a[href="#current-streams"]','本月速览','Month at a glance');
 set('.current-updates-navigation a[href="#monthly-appendix"]','补充资料','Further reading');
 set('#current-hotspots>header>h2','热点信号','Market signals');
 set('#monthly-appendix>h2','补充资料','Further reading');
 set('#monthly-appendix>.reader-note','补充研读与候选目录保留在这里，不与本月已核实进展混计。','Supplemental reviews and candidates are kept separate from verified monthly developments.');
}
function renderSignals(m){
 renderMonthlyFrame();
 const root=document.getElementById('current-hotspot-cards');if(!root)return;root.replaceChildren();
 const rows=m.current_signals.filter(r=>(!current.windowStart||r.publication_date>=current.windowStart)&&(!current.windowEnd||r.publication_date<=current.windowEnd)&&(!current.topicId||m.signal_topics.some(l=>l.signal_id===r.signal_id&&l.compression_topic_id===current.topicId))).sort((a,b)=>a.position-b.position);
 const metric=document.getElementById('monthly-signal-metric');if(metric)metric.textContent=String(rows.length);root.append(el('p',current.locale==='en'?'Events that change deployment requirements; these are not compression benchmarks.':'影响部署需求的事件；与压缩算法的实测效果分开阅读。','reader-note'));
 for(const r of rows){const card=el('article','','card'),mappings=m.signal_topics.filter(l=>l.signal_id===r.signal_id);card.append(el('p',r.publication_date+' · '+ui('signal_date_'+r.date_kind)+' · '+ui('primary_text_checked'),'meta'),el('h3',pick(r,'title')));topics(card,mappings.map(l=>l.compression_topic_id),mappings);field(card,'signal_fact',pick(r,'fact'));field(card,'signal_relevance',pick(r,'relevance'));field(card,'decision_boundary',pick(r,'boundary'));const refs=el('div','','actions');primary(refs,m.sources.get(r.source_id),ui('signal_primary'));if(r.discovery_source_id!==r.source_id)primary(refs,m.sources.get(r.discovery_source_id),ui('signal_discovery'));card.append(refs,el('p',r.locator+' · '+r.reviewed_at,'meta'));root.append(card);}
 if(!rows.length)root.append(el('p',ui('current_signal_empty')));
 const count=document.getElementById('current-hotspot-count');if(count)count.textContent=rows.length+' · '+ui('reviewed_signals');notify();
}
function renderIndustry(reader){
 const root=document.getElementById('current-industry-cards');if(!root)return;
 root.replaceChildren();const {snapshot,directory}=reader;
 const verified=new Set(snapshot.assessments.filter(r=>r.review_status==='verified').map(r=>r.link_id));
 const links=snapshot.links.filter(r=>verified.has(r.link_id)&&(!current.topicId||r.compression_topic_id===current.topicId)),ids=new Set(links.map(r=>r.update_id));
 const rows=snapshot.updates.filter(r=>ids.has(r.update_id)&&r.release_date.startsWith(current.period)&&(!current.windowStart||r.release_date>=current.windowStart)&&(!current.windowEnd||r.release_date<=current.windowEnd)).sort((a,b)=>b.release_date.localeCompare(a.release_date)||a.update_id.localeCompare(b.update_id));
 const published=rows.filter(r=>r.release_date.startsWith(current.period)),existing=rows.filter(r=>!r.release_date.startsWith(current.period));
 const metric=document.getElementById('monthly-release-metric');if(metric)metric.textContent=String(published.length);
 const word=(zh,en)=>current.locale==='en'?en:zh;
 root.append(el('p',word('发布日期与核对日期分开记录；文档核对不计为本月新发布。','Publication and review dates are separate; checking documentation is not a new release.'),'reader-note'));
 if(!published.length)root.append(el('p',word('当前收录范围内，尚无已核实发布日期的本月产业发布。','No industry release with a verified date in this month is recorded in the current scope.'),'monthly-empty-state'));
 const build=(entries,isNew)=>{
  if(!entries.length)return;const group=el('section','','monthly-industry-group');
  group.append(el('h3',word(isNew?'本月新发布':'本月复核的既有能力',isNew?'Released this month':'Existing capabilities reviewed this month')));
  for(const r of entries){
   const family=directory.source_families.find(x=>x.family_id===r.family_id);check(family,'Unresolved industry source family');
   const card=el('article','','current-industry-entry monthly-industry-brief');card.dataset.industryKey=r.update_id;card.dataset.releaseBucket=isNew?'published':'reviewed-existing';
   card.append(el('p',pick(family,'title')+' · '+r.version_label,'eyebrow'),el('h4',pick(r,'title')),el('p',pick(r,'summary')));
   card.append(el('p',word('发布：','Published: ')+(r.release_date||word('未确认','unconfirmed'))+' · '+word('核对：','Reviewed: ')+r.checked_at,'meta'));
   const changes=snapshot.changes.filter(c=>c.update_id===r.update_id&&links.some(l=>l.change_id===c.change_id)).sort((a,b)=>a.position-b.position);
   const facts=el('dl','','monthly-industry-facts');
   for(const c of changes){const item=el('div');item.dataset.industryChange=c.change_id;item.append(el('dt',pick(c,'title')),el('dd',pick(c,'fact')));facts.append(item);}
   card.append(facts);field(card,'implementation_conditions',pick(r,'scope'));field(card,'implementation_dependencies',pick(r,'dependencies'));field(card,'decision_boundary',pick(r,'boundary'));
   const refs=el('div','','actions');const sourceIds=[...new Set([r.source_id,...changes.map(c=>c.source_id)])];
   for(const id of sourceIds)primary(refs,snapshot.sources.find(x=>x.source_id===id),word('官方原文 ↗','Official source ↗'));card.append(refs);
   topics(card,links.filter(l=>l.update_id===r.update_id).map(l=>l.compression_topic_id));group.append(card);
  }root.append(group);
 };
 build(published,true);build(existing,false);
 const count=document.getElementById('current-industry-count');if(count)count.textContent=word(`${published.length} 条本月发布 · ${existing.length} 条既有能力复核`,`${published.length} monthly releases · ${existing.length} existing capabilities reviewed`);notify();
}
function notify(){document.dispatchEvent(new Event('lri:sections-changed'));}
function failure(id,error){const root=document.getElementById(id);if(!root)return;root.replaceChildren(el('p',ui('synthesis_read_failed')+' · '+error.message));const b=el('button',ui('retry'),'btn');b.type='button';b.addEventListener('click',()=>refresh(current,true));root.append(b);}
function refresh(context,force=false){
 if(!context?.revision||!context.scope||!context.period||!['updates','home','reports'].includes(context.view))return;
 const key=[context.revision,context.scope,context.period].join('|');current={...context,key};
 if(force)cache.delete(key);let e=cache.get(key);
 if(!e){e={promise:read(context),model:null,industry:null,industryPending:null};cache.set(key,e);if(cache.size>3)cache.delete(cache.keys().next().value);e.promise.then(m=>{e.model=m;if(current.key===key)render();}).catch(error=>{if(cache.get(key)===e)cache.delete(key);if(current?.key===key){failure('ascend-cards',error);failure('analysis-focus-cards',error);failure('analysis-summary',error);failure('current-hotspot-cards',error);failure('insight-deck-content',error);failure('insight-deck-archive',error);}});}
 const render=()=>{if(e.model){if(current.view==='home'){renderAnalysis(e.model);renderReports(e.model);restoreReportAnchor(e.model);}else if(current.view==='reports')renderReports(e.model);else renderSignals(e.model);}else{for(const id of current.view==='home'?['analysis-focus-cards','analysis-summary','ascend-cards','insight-deck-content']:current.view==='reports'?['insight-deck-archive']:['current-hotspot-cards'])document.getElementById(id)?.replaceChildren(el('p',ui('loading')));}
 if(current.view==='updates'){if(e.industry)renderIndustry(e.industry);else if(!e.industryPending){document.getElementById('current-industry-cards')?.replaceChildren(el('p',ui('loading')));e.industryPending=context.loadIndustry().then(reader=>{e.industry=reader;if(current?.key===key)renderIndustry(reader);}).catch(error=>{if(current?.key===key)failure('current-industry-cards',error);}).finally(()=>{e.industryPending=null;});}}};
 render();
}
globalThis.LRICompressionSynthesis=Object.freeze({refresh});
})();

