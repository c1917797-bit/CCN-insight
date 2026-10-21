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
function mapHeading(tag,title,ids){const h=el(tag,title),labels=[...new Set(ids)].map(id=>{const topic=current.topics.find(x=>x.compression_topic_id===id);check(topic,'Unresolved map topic');return pick(topic,'title');});if(labels.length)h.append(el('span',(current.locale==='en'?' (':'（')+labels.join(' · ')+(current.locale==='en'?')':'）'),'monthly-route-map-label'));return h;}
function field(parent,key,value){const p=el('p');p.append(el('strong',ui(key)+': '),document.createTextNode(value));parent.append(p);}
function owned(rows){check(rows.every(r=>r.business_id==='cloud-core'&&r.topic_id==='cloud_core'),'Insight scope mismatch');return rows;}
async function read(context){
 const b=await LRICloudSemanticRead('synthesis',context.revision,{scope:context.scope,period:context.period});
 check(b.revision===context.revision,'Insight revision drift');const g=b.groups;Object.values(g).forEach(owned);
 const stories=new Map(g.monthly_route_insights.map(r=>[r.story_id,r])),topicIds=new Set(context.topics.map(r=>r.compression_topic_id));
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
 return {...g,sources:new Map(s.records.map(r=>[r.source_id,r])),paperSummaries:new Map(summaries.records.map(r=>[r.summary_id,r])),stories};
}
function selected(model,story){return !current.topicId||model.monthly_route_evidence.some(r=>r.story_id===story&&r.compression_topic_id===current.topicId);}
function routePriority(row){return row.priority_zh==='优先穿刺'?ui('analysis_priority_research'):pick(row,'priority');}
function paperProbeCandidates(parent,m,assessment,refs,probe){
 const papers=[...new Map(refs.map(r=>[r.summary_id,r])).values()];
 const section=el('section','','analysis-paper-probes');section.append(el('h6',ui('paper_probe_candidates')),el('p',ui('paper_probe_scope'),'meta'));
 for(const ref of papers){
  const p=m.paperSummaries.get(ref.summary_id),source=m.sources.get(ref.source_id),card=el('details','','analysis-paper-probe');card.dataset.paperProbe=ref.summary_id;
  card.append(el('summary',source.title+' · '+ref.observed_version));const body=el('div','','analysis-paper-probe-body');
  const link=el('a',source.title+' ↗');link.href=url(p.evidence_url);link.target='_blank';link.rel='noopener noreferrer';body.append(link);
  topics(body,refs.filter(r=>r.summary_id===ref.summary_id).map(r=>r.compression_topic_id));
  body.append(el('p',ui('probe_not_run'),'paper-probe-status'));field(body,'paper_probe_claim',pick(p,'one_sentence'));field(body,'paper_probe_method',pick(p,'innovation'));field(body,'paper_probe_conditions',pick(p,'results'));
  body.append(el('p',ui(p.review_status==='method_results_checked'?'paper_probe_review_sections':'paper_probe_review_abstract')+' · '+p.evidence_locator+' · '+p.reviewed_at,'meta'));
  if(probe){const protocol=el('details','','analysis-probe');protocol.append(el('summary',ui('paper_probe_protocol')));field(protocol,'paper_probe_hypothesis',pick(probe,'hypothesis'));for(const key of ['design','metrics','decision_rule'])field(protocol,'probe_'+key,pick(probe,key));protocol.append(el('p',ui('probe_not_run'),'meta'));body.append(protocol);}
  card.append(body);section.append(card);
 }parent.append(section);
}
// Research-entry candidates follow the published report; route evidence remains complete.
function reportPrioritySources(m){
 const report=(m.insight_reports||[]).filter(r=>r.status==='published'&&r.scope_id===current.scope&&r.period_id===current.period).sort((a,b)=>b.reviewed_at.localeCompare(a.reviewed_at)||b.report_id.localeCompare(a.report_id))[0];
 if(!report)return null;
 const papers=(m.insight_report_papers||[]).filter(p=>p.report_id===report.report_id);
 // Existing reports used route-level priority; keep their display until cutover.
 if(!papers.some(p=>p.priority_zh==='条件优先'))return null;
 return new Set(papers.filter(p=>p.priority_zh==='条件优先').map(p=>p.source_id));
}
function priorityRouteRefs(assessment,refs,prioritySources){
 return prioritySources?refs.filter(r=>prioritySources.has(r.source_id)):(assessment.priority_zh==='优先穿刺'?refs:[]);
}
function renderResearchFocus(m,rows){
 const root=document.getElementById('analysis-focus-cards');if(!root)return;root.replaceChildren();
 const prioritySources=reportPrioritySources(m);
 const priorities=rows.filter(a=>priorityRouteRefs(a,m.monthly_route_evidence.filter(r=>r.story_id===a.story_id),prioritySources).length);
 if(!priorities.length){root.append(el('p',ui('analysis_focus_empty'),'reader-note'));return;}
 for(const a of priorities){
  const refs=priorityRouteRefs(a,m.monthly_route_evidence.filter(r=>r.story_id===a.story_id),prioritySources),card=el('article','','card analysis-focus-card');
  card.dataset.assessmentId=a.assessment_id;card.dataset.claimKind='analyst_recommendation';card.append(el('h4',pick(a,'title')));
  const map=el('div','','analysis-route-map');topics(map,refs.map(r=>r.compression_topic_id));card.append(map);
  const links=el('ul');
  for(const ref of [...new Map(refs.map(r=>[r.summary_id,r])).values()]){
   const source=m.sources.get(ref.source_id),summary=m.paperSummaries.get(ref.summary_id);
   check(source&&summary&&summary.source_id===ref.source_id&&summary.observed_version===ref.observed_version,'Unbound priority paper');
   const li=el('li'),a=el('a',source.title),url=new URL('monthly.html',location.href);url.searchParams.set('month',current.period);url.searchParams.set('scope',current.scope);url.searchParams.set('paper',ref.summary_id);url.hash='monthly-route-report';a.href=url.pathname+url.search+url.hash;li.append(a);links.append(li);
  }card.append(links);
  const detail=el('a',ui('analysis_focus_argument'),'analysis-evidence-link');detail.href='#'+a.assessment_id;detail.addEventListener('click',()=>{const appendix=document.getElementById('ascend');if(appendix?.tagName==='DETAILS')appendix.open=true;const target=document.getElementById(a.assessment_id);if(target)target.open=true;});card.append(detail);root.append(card);
 }
}

function renderAnalysis(m){
 const root=document.getElementById('ascend-cards');if(!root)return;
 const openIds=new Set([...root.querySelectorAll('details.analysis-route[open]')].map(n=>n.id));root.replaceChildren();
 const rows=m.ascend_route_assessments.filter(a=>selected(m,a.story_id)).sort((a,b)=>a.position-b.position);
 const overview=document.getElementById('analysis-summary'),meta=document.getElementById('analysis-meta'),prioritySources=reportPrioritySources(m);overview?.replaceChildren();renderResearchFocus(m,rows);
 if(!rows.length){root.append(el('p',ui('ascend_decision_empty')));if(meta)meta.textContent=current.period;return;}
 const reviewed=rows.map(r=>r.reviewed_at).sort().at(-1),refsAll=m.monthly_route_evidence.filter(r=>rows.some(a=>a.story_id===r.story_id));
 if(meta)meta.textContent=current.period+' / '+ui('analysis_reviewed')+' '+reviewed+' / '+new Set(refsAll.map(r=>r.source_id)).size+' '+ui('analysis_sources');
 const groups=new Map();for(const a of rows){if(!groups.has(a.priority_zh))groups.set(a.priority_zh,[]);groups.get(a.priority_zh).push(a);}
 let groupIndex=0;
 for(const list of groups.values()){
  const groupId='analysis-priority-'+(++groupIndex),group=el('section','','analysis-route-group');group.id=groupId;group.dataset.sectionLabel=routePriority(list[0]);group.dataset.sectionLevel='3';
  const heading=el('div','','analysis-group-heading');heading.append(el('h4',routePriority(list[0])),el('span',list.length+' '+ui('analysis_routes'),'analysis-count'));group.append(heading);
  if(overview){const link=el('a','','analysis-priority-tile');link.href='#'+groupId;link.addEventListener('click',()=>{const appendix=document.getElementById('ascend');if(appendix?.tagName==='DETAILS')appendix.open=true;});link.append(el('span',routePriority(list[0])),el('strong',String(list.length)),el('span',ui('analysis_routes')+' ↗','analysis-tile-unit'));overview.append(link);}
  for(const a of list){
   const story=m.stories.get(a.story_id),refs=m.monthly_route_evidence.filter(r=>r.story_id===a.story_id),routeShell=el('article','','analysis-route-shell'),card=el('details','','analysis-route');card.id=a.assessment_id;card.dataset.claimKind='analyst_recommendation';if(openIds.has(card.id))card.open=true;
   const summary=el('summary'),number=el('span',String(a.position).padStart(2,'0'),'analysis-route-number'),headline=el('div','','analysis-route-headline');
   headline.append(el('h5',pick(a,'title')));
   const disclosure=el('span',ui(card.open?'analysis_collapse':'analysis_expand'),'analysis-route-disclosure');summary.append(number,headline,disclosure);card.append(summary);card.addEventListener('toggle',()=>{disclosure.textContent=ui(card.open?'analysis_collapse':'analysis_expand');});
   const map=el('div','','analysis-route-map');topics(map,refs.map(r=>r.compression_topic_id));routeShell.append(map);
   const candidateRefs=priorityRouteRefs(a,refs,prioritySources);
   if(candidateRefs.length){
    const candidates=el('ul','','analysis-route-paper-links');candidates.setAttribute('aria-label',ui('paper_probe_candidates_short'));
    for(const ref of [...new Map(candidateRefs.map(r=>[r.summary_id,r])).values()]){const li=el('li'),link=el('a',m.sources.get(ref.source_id).title+' · '+ref.observed_version),href=new URL('monthly.html',location.href);href.searchParams.set('month',current.period);href.searchParams.set('scope',current.scope);href.searchParams.set('paper',ref.summary_id);href.hash='monthly-route-report';link.href=href.pathname+href.search+href.hash;li.append(link);candidates.append(li);}routeShell.append(el('p',ui('paper_probe_candidates_short'),'analysis-candidate-label'),candidates);
   }
   const body=el('div','','analysis-route-body'),grid=el('div','','analysis-reason-grid');body.append(el('p',pick(story,'title'),'analysis-route-context'));
   for(const [key,value] of [['decision_reason',pick(a,'rationale')],['decision_choice',pick(a,'recommendation')]]){const block=el('section','','analysis-reason-block');block.append(el('h6',ui(key)),el('p',value));grid.append(block);}body.append(grid);
   const boundary=el('div','','analysis-boundary');boundary.append(el('h6',ui('decision_boundary')),el('p',pick(story,'boundary')));body.append(boundary);
   const proof=el('details','','analysis-proof');proof.append(el('summary',ui('decision_sources')+' · '+new Set(refs.map(r=>r.source_id)).size));const sources=el('ul');for(const id of [...new Set(refs.map(r=>r.source_id))]){const li=el('li');primary(li,m.sources.get(id));sources.append(li);}proof.append(sources);body.append(proof);
   const probe=m.ascend_validation_probes.find(p=>p.assessment_id===a.assessment_id);
   const probeRefs=prioritySources?candidateRefs:refs;
   if(probe&&probeRefs.length)paperProbeCandidates(body,m,a,probeRefs,probe);
   const detail=el('a',ui('decision_read_route'),'analysis-evidence-link'),target=new URL('monthly.html',location.href);target.searchParams.set('month',current.period);target.searchParams.set('scope',current.scope);target.searchParams.set('route',a.story_id);target.hash='monthly-route-report';detail.href=target.pathname+target.search+target.hash;body.append(detail);card.append(body);routeShell.prepend(card);group.append(routeShell);
  }
  root.append(group);
 }
 notify();
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
 for(const id of current.view==='reports'?['insight-deck-archive']:['insight-deck-content']){
  const root=document.getElementById(id);if(!root)continue;for(const d of root.querySelectorAll('dialog[open]'))d.close();root.replaceChildren();
  const rows=m.insight_reports.filter(r=>r.status==='published'&&r.scope_id===current.scope&&r.period_id===current.period);
  if(!rows.length){root.append(el('p',ui('deck_not_available'),'meta'));continue;}
  for(const r of rows){
   const papers=m.insight_report_papers.filter(p=>p.report_id===r.report_id).sort((a,b)=>a.position-b.position);
   const assets=m.insight_report_assets.filter(a=>a.report_id===r.report_id),figures=assets.filter(a=>/^figure-\d{2}-(tech|results)$/.test(a.format));
   check(new Set(figures.map(a=>a.format)).size===figures.length,'Duplicate report figures');
   if(figures.length)check(papers.filter(p=>p.selection_status==='illustrated').every(p=>['tech','results'].every(kind=>figures.some(a=>a.format==='figure-'+String(p.slide_number).padStart(2,'0')+'-'+kind))),'Incomplete original figures');
   check(r.status==='published'&&papers.length===r.candidate_count&&papers.filter(p=>p.selection_status==='illustrated').length===r.paper_count,'Incomplete report selection');
   const slides=assets.filter(a=>/^slide-\d{2}$/.test(a.format)).sort((a,b)=>a.format.localeCompare(b.format));check(slides.length===r.page_count&&['pdf','pptx'].every(f=>assets.some(a=>a.format===f)),'Incomplete report assets');
   const card=el('article','','card analysis-report-card');card.append(el('h3',pick(r,'title')));const reportScope=el('details','','analysis-report-scope');reportScope.append(el('summary',ui('deck_report_scope')),el('p',pick(r,'summary')));card.append(reportScope,el('p',r.reviewed_at+' · '+r.paper_count+' '+ui('deck_papers')+' / '+r.candidate_count+' '+ui('deck_candidates')+' · '+r.page_count+' '+ui('deck_pages')+' · '+ui('deck_zh'),'meta'));
   const actions=el('div','','actions analysis-report-actions'),viewer=el('div','','analysis-report-viewer');
   const assetUrl=a=>{const target=new URL(a.public_path,location.origin);check(target.origin===location.origin&&target.pathname.startsWith('/business_insight/cloud_core/reports/')&&/^[a-f0-9]{64}$/.test(a.content_sha256)&&a.binary_sha256===a.content_sha256,'Invalid report asset');return target.href;};
   const pdf=assets.find(a=>a.format==='pdf'),ppt=assets.find(a=>a.format==='pptx');
   const pageTitles=slides.map((_,i)=>{const p=papers.find(p=>p.selection_status==='illustrated'&&p.slide_number===i+1);return p?m.sources.get(p.source_id).title:'';});
   const stateKey=r.report_id+'|'+current.scope+'|'+current.period+'|'+slides.map(a=>a.content_sha256).join('|');let dispose=null;
   const button=el('button',ui('deck_open'),'btn');button.type='button';button.setAttribute('aria-expanded','false');button.addEventListener('click',()=>{if(dispose){dispose();dispose=null;button.textContent=ui('deck_open');button.setAttribute('aria-expanded','false');return;}dispose=mountReportReader(viewer,slides,pick(r,'title'),assetUrl,stateKey,figures,pageTitles);button.textContent=ui('deck_close');button.setAttribute('aria-expanded','true');});actions.append(button);
   for(const [a,label] of [[pdf,'deck_fullscreen'],[ppt,'deck_download']]){const link=el('a',ui(label),'btn analysis-report-secondary');link.href=assetUrl(a);link.target='_blank';link.rel='noopener noreferrer';if(a.format==='pptx')link.download=a.public_path.split('/').pop();actions.append(link);}card.append(actions,el('p',ui('deck_lazy_help'),'reader-note'),viewer);
   const selection=el('details','','analysis-report-selection');selection.append(el('summary',ui('deck_selection')));const list=el('ol');for(const p of papers){const li=el('li');primary(li,m.sources.get(p.source_id));li.append(el('p',pick(p,'priority')+' · '+pick(p,'reason'),'meta'));if(p.slide_number>0){const jumpTo=el('button',ui('deck_slide')+' '+p.slide_number+' ↗','analysis-reader-nav');jumpTo.type='button';jumpTo.addEventListener('click',()=>{if(!dispose)button.click();dispose.goTo(p.slide_number-1);});li.append(jumpTo);}topics(li,m.monthly_route_evidence.filter(e=>e.source_id===p.source_id).map(e=>e.compression_topic_id));list.append(li);}selection.append(list);card.append(selection);root.append(card);if(id==='insight-deck-content'&&current.view==='home')button.click();
  }
 }
 notify();
}

function renderSignals(m){
 const root=document.getElementById('current-hotspot-cards');if(!root)return;root.replaceChildren();
 const rows=m.current_signals.filter(r=>!current.topicId||m.signal_topics.some(l=>l.signal_id===r.signal_id&&l.compression_topic_id===current.topicId)).sort((a,b)=>a.position-b.position);
 root.append(el('p',ui('current_signal_help'),'reader-note'));
 for(const r of rows){const card=el('article','','card'),mappings=m.signal_topics.filter(l=>l.signal_id===r.signal_id);card.append(el('p',r.publication_date+' · '+ui('signal_date_'+r.date_kind)+' · '+ui('primary_text_checked'),'meta'),mapHeading('h3',pick(r,'title'),mappings.map(l=>l.compression_topic_id)));topics(card,mappings.map(l=>l.compression_topic_id),mappings);field(card,'signal_fact',pick(r,'fact'));field(card,'signal_relevance',pick(r,'relevance'));field(card,'decision_boundary',pick(r,'boundary'));const refs=el('div','','actions');primary(refs,m.sources.get(r.source_id),ui('signal_primary'));if(r.discovery_source_id!==r.source_id)primary(refs,m.sources.get(r.discovery_source_id),ui('signal_discovery'));card.append(refs,el('p',r.locator+' · '+r.reviewed_at,'meta'));root.append(card);}
 if(!rows.length)root.append(el('p',ui('current_signal_empty')));
 const count=document.getElementById('current-hotspot-count');if(count)count.textContent=rows.length+' · '+ui('reviewed_signals');notify();
}
function renderIndustry(reader){
 const root=document.getElementById('current-industry-cards');if(!root)return;
 const opened=new Set([...root.querySelectorAll('details[open][data-industry-key]')].map(n=>n.dataset.industryKey));root.replaceChildren();const {snapshot,directory}=reader;
 const verified=new Map(snapshot.assessments.filter(r=>r.review_status==='verified').map(r=>[r.link_id,r]));const links=snapshot.links.filter(r=>verified.has(r.link_id)&&(!current.topicId||r.compression_topic_id===current.topicId)),ids=new Set(links.map(r=>r.update_id));
 const rows=snapshot.updates.filter(r=>ids.has(r.update_id)&&(r.release_date.startsWith(current.period)||r.checked_at.startsWith(current.period))).sort((a,b)=>b.checked_at.localeCompare(a.checked_at)||b.release_date.localeCompare(a.release_date)||a.update_id.localeCompare(b.update_id));
 const groups=new Map();for(const r of rows){if(!groups.has(r.family_id))groups.set(r.family_id,[]);groups.get(r.family_id).push(r);}
 let published=0;root.append(el('p',ui('current_industry_help'),'reader-note'));
 for(const [familyId,entries] of groups){
  const f=directory.source_families.find(x=>x.family_id===familyId),scope=directory.industry_source_scopes.find(x=>x.family_id===familyId);check(f,'Unresolved industry source family');
  const family=el('details','','card current-industry-card');family.dataset.industryKey=familyId;family.open=opened.has(familyId);
  const heading=el('summary'),name=el('span',pick(f,'title'),'current-industry-name'),count=el('span',entries.length+' '+ui('industry_progress_entries'),'current-industry-count');heading.append(name,count);family.append(heading);
  const area=el('div','','current-industry-entries');area.append(el('p',(scope?.ecosystem_id==='ascend'?ui('ascend_ecosystem'):ui('cross_platform_ecosystem')),'topic-dossier-type'));
  for(const r of entries){
   const isNew=r.release_date.startsWith(current.period);if(isNew)published++;
   const d=el('details','','current-industry-entry');d.dataset.industryKey=r.update_id;d.open=opened.has(r.update_id);
   d.append(mapHeading('summary',pick(r,'title'),links.filter(l=>l.update_id===r.update_id).map(l=>l.compression_topic_id)),el('p',isNew?ui('published_this_month'):ui('reviewed_existing_capability'),'topic-dossier-type'));
   d.append(el('p',pick(r,'summary')),el('p',r.version_label+' · '+ui('reviewed_on')+r.checked_at+' · '+ui('published_on')+(r.release_date||ui('unknown_publication_date')),'meta'));topics(d,links.filter(l=>l.update_id===r.update_id).map(l=>l.compression_topic_id));
   for(const c of snapshot.changes.filter(x=>x.update_id===r.update_id&&links.some(l=>l.change_id===x.change_id)).sort((a,b)=>a.position-b.position)){
    const box=el('div','','research-route-block');box.dataset.industryChange=c.change_id;box.append(el('h4',pick(c,'title')));field(box,'signal_fact',pick(c,'fact'));field(box,'implementation_conditions',pick(c,'conditions'));primary(box,snapshot.sources.find(x=>x.source_id===c.source_id),ui('signal_primary'));
    for(const link of links.filter(l=>l.change_id===c.change_id)){const a=verified.get(link.link_id),analysis=el('section');analysis.dataset.industryAssessment=a.link_id;analysis.dataset.readingLayer='analysis';analysis.append(mapHeading('h5',pick(a,'title'),[a.compression_topic_id]));field(analysis,'industry_topic_relation',pick(a,'relevance'));field(analysis,'industry_research_impact',pick(a,'impact'));const more=el('details');more.append(el('summary',ui('industry_research_details')));field(more,'industry_research_check',pick(a,'check'));field(more,'decision_boundary',pick(a,'boundary'));more.append(el('p',a.source_locator+' · '+ui('reviewed_on')+a.reviewed_at,'meta'));analysis.append(more);box.append(analysis);}
    d.append(box);
   }
   field(d,'implementation_dependencies',pick(r,'dependencies'));field(d,'decision_boundary',pick(r,'boundary'));area.append(d);
  }
  family.append(area);root.append(family);
 }
 if(!rows.length)root.append(el('p',ui('current_industry_empty')));const count=document.getElementById('current-industry-count');if(count)count.textContent=groups.size+' '+ui('industry_source_groups')+' / '+published+' '+ui('new_releases')+' / '+rows.length+' '+ui('reviewed_entries');notify();
}
function notify(){document.dispatchEvent(new Event('lri:sections-changed'));}
function failure(id,error){const root=document.getElementById(id);if(!root)return;root.replaceChildren(el('p',ui('synthesis_read_failed')+' · '+error.message));const b=el('button',ui('retry'),'btn');b.type='button';b.addEventListener('click',()=>refresh(current,true));root.append(b);}
function refresh(context,force=false){
 if(!context?.revision||!context.scope||!context.period||!['updates','home','reports'].includes(context.view))return;
 const key=[context.revision,context.scope,context.period].join('|');current={...context,key};
 if(force)cache.delete(key);let e=cache.get(key);
 if(!e){e={promise:read(context),model:null,industry:null,industryPending:null};cache.set(key,e);if(cache.size>3)cache.delete(cache.keys().next().value);e.promise.then(m=>{e.model=m;if(current.key===key)render();}).catch(error=>{if(cache.get(key)===e)cache.delete(key);if(current?.key===key){failure('ascend-cards',error);failure('analysis-focus-cards',error);failure('analysis-summary',error);failure('current-hotspot-cards',error);failure('insight-deck-content',error);failure('insight-deck-archive',error);}});}
 const render=()=>{if(e.model){if(current.view==='home'){renderAnalysis(e.model);renderReports(e.model);}else if(current.view==='reports')renderReports(e.model);else renderSignals(e.model);}else{for(const id of current.view==='home'?['analysis-focus-cards','analysis-summary','ascend-cards','insight-deck-content']:current.view==='reports'?['insight-deck-archive']:['current-hotspot-cards'])document.getElementById(id)?.replaceChildren(el('p',ui('loading')));}
 if(current.view==='updates'){if(e.industry)renderIndustry(e.industry);else if(!e.industryPending){document.getElementById('current-industry-cards')?.replaceChildren(el('p',ui('loading')));e.industryPending=context.loadIndustry().then(reader=>{e.industry=reader;if(current?.key===key)renderIndustry(reader);}).catch(error=>{if(current?.key===key)failure('current-industry-cards',error);}).finally(()=>{e.industryPending=null;});}}};
 render();
}
globalThis.LRICompressionSynthesis=Object.freeze({refresh});
})();
