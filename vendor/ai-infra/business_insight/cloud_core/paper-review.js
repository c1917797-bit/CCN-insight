/* Reviewed imports remain separate from publication-month news. */
(() => {
'use strict';
let context=null,key='',epoch=0,tab='candidates',offset=0,term='';
const check=(ok,message)=>{if(!ok)throw Error(message);};
const date=v=>/^\d{4}-\d{2}-\d{2}$/.test(v||'')&&!Number.isNaN(Date.parse(v))&&new Date(v).toISOString().slice(0,10)===v;
const ui=k=>context?.strings[k]||k;
const pick=(row,name)=>row[name+'_'+context.locale]||row[name+'_zh']||'';
const el=(tag,text='',cls='')=>{const node=document.createElement(tag);node.textContent=String(text);if(cls)node.className=cls;return node;};
function safe(value){const u=new URL(value,location.href);check(u.protocol==='https:'&&!u.username&&!u.password,'Invalid paper URL');return u.href;}
function link(text,url){const a=el('a',text);a.href=safe(url);a.target='_blank';a.rel='noopener noreferrer';return a;}
function button(text,action){const b=el('button',text,'btn');b.type='button';b.addEventListener('click',action);return b;}
function owned(row){return row?.business_id==='cloud-core'&&row?.topic_id==='cloud_core';}
function validateReview(intake,summary,source,period,events){
 check(owned(intake)&&owned(summary)&&source?.business_id==='cloud-core','Cross-business paper review');
 check(intake.intake_id&&intake.review_period_id===period&&/^[0-9]{4}-[0-9]{2}$/.test(period),'Review period mismatch');
 check(intake.source_id===source.source_id&&intake.summary_id===summary.summary_id&&summary.source_id===source.source_id,'Unbound review source/summary');
 check(date(intake.publication_date)&&date(intake.reviewed_at)&&intake.publication_date<=intake.reviewed_at&&intake.reviewed_at.startsWith(period)&&summary.reviewed_at===intake.reviewed_at,'Publication/review date mismatch');
 check(source.source_kind==='paper'&&['primary_full_text_reviewed','primary_text_checked'].includes(source.verification_status)&&source.title&&source.title!==source.external_id,'Paper metadata not reviewed');
 check(['primary_abstract_checked','method_results_checked'].includes(summary.review_status)&&/^v[1-9][0-9]*$/.test(summary.observed_version||'')&&summary.evidence_locator,'Paper review/version provenance missing');
 check(['adjacent_research','direct_topic'].includes(intake.relation_kind)&&Number.isSafeInteger(intake.position),'Invalid research relation');
 for(const name of ['direction','selection_reason','next_step','applicability_boundary'])for(const locale of ['zh','en'])check(typeof intake[name+'_'+locale]==='string'&&intake[name+'_'+locale].trim(),'Missing review decision');
 for(const name of ['one_sentence_zh','background_zh','innovation_zh','results_zh'])check(typeof summary[name]==='string'&&summary[name].trim(),'Incomplete paper summary');
 check(Array.isArray(events)&&events.some(e=>owned(e)&&e.source_id===source.source_id&&e.publication_date===intake.publication_date&&e.event_date===intake.publication_date&&e.date_kind==='first_submission'&&e.date_precision==='day'&&e.status==='primary_text_checked'&&date(e.verified_at)&&e.verified_at<=intake.reviewed_at),'Original publication event not verified');
 check(events.some(e=>owned(e)&&e.source_id===source.source_id&&e.observed_version===summary.observed_version&&e.publication_date===intake.publication_date&&date(e.event_date)&&e.event_date>=intake.publication_date&&e.event_date<=intake.reviewed_at&&e.date_kind===(summary.observed_version==='v1'?'first_submission':'revision')&&e.date_precision==='day'&&e.status==='primary_text_checked'&&date(e.verified_at)&&e.verified_at<=intake.reviewed_at),'Reviewed version event not verified');
 safe(source.canonical_url);safe(summary.evidence_url);
 if(/^\d{4}\.\d{4,5}$/.test(source.external_id||''))check(new URL(summary.evidence_url).pathname.includes(source.external_id+summary.observed_version),'Review URL lacks exact paper version');
 const versionEvent=events.find(e=>owned(e)&&e.source_id===source.source_id&&e.observed_version===summary.observed_version&&e.date_kind===(summary.observed_version==='v1'?'first_submission':'revision')&&e.status==='primary_text_checked');
 return {intake,summary,source,publicationBucket:versionEvent?.event_date.startsWith(period)?'current':'background'};
}
async function reviewed(ctx){
 const page=await LRITableGit.loadTablePage('ic_paper_review_intakes',{filterField:'review_period_id',filterValue:ctx.period,expectedRevision:ctx.revision,limit:100,offset:0});
 check(page.revision===ctx.revision&&!page.page.truncated&&page.records.length<=100,'Incomplete reviewed-paper selection');
 const ids=[...new Set(page.records.map(r=>r.source_id))],sids=[...new Set(page.records.map(r=>r.summary_id))];
 check(new Set(page.records.map(r=>r.intake_id)).size===page.records.length,'Duplicate review intake');
 if(!ids.length)return [];
 const [sources,summaries,evidence]=await Promise.all([
  LRITableGit.loadRowsByKeys('cloud_core_sources',ids,ctx.revision,['source_id','business_id','source_kind','external_id','title','canonical_url','verification_status']),
  LRITableGit.loadRowsByKeys('ic_paper_summaries',sids,ctx.revision),
  LRITableGit.loadRowsByValues('ic_evidence_items','source_id',ids,ctx.revision)
 ]);
 check(sources.revision===ctx.revision&&summaries.revision===ctx.revision&&evidence.revision===ctx.revision&&sources.records.length===ids.length&&summaries.records.length===sids.length,'Incomplete or mixed review joins');
 return page.records.sort((a,b)=>a.position-b.position||a.intake_id.localeCompare(b.intake_id)).map(r=>validateReview(r,summaries.records.find(s=>s.summary_id===r.summary_id),sources.records.find(s=>s.source_id===r.source_id),ctx.period,evidence.records));
}
function renderReviewCard(model,compact=false){
 const {intake:r,summary:s,source}=model,card=el('article','','card');card.id='paper-review-'+r.intake_id;card.dataset.paperReview=r.intake_id;card.dataset.publicationDate=r.publication_date;card.dataset.reviewDate=r.reviewed_at;
 card.append(el('p',ui(r.relation_kind==='adjacent_research'?'paper_review_adjacent':'paper_review_direct')+' · '+pick(r,'direction'),'eyebrow'));
 const h=el('h4');h.append(link(source.title,s.evidence_url));card.append(h);
 card.append(el('p',ui(model.publicationBucket==='current'?'funnel_current_badge':'funnel_background_badge'),'reader-note'));
 card.append(el('p',ui('paper_review_published')+' '+r.publication_date+' · '+ui('paper_review_reviewed')+' '+r.reviewed_at+' · '+s.observed_version,'meta'));
 if(context.locale==='en'&&!s.one_sentence_en)card.append(el('p',ui('paper_review_source_language'),'meta'));
 card.append(el('p',pick(s,'one_sentence')));
 if(compact){const a=el('a',ui('paper_review_read'));const target=new URL('index.html',location.href);target.searchParams.set('month',r.review_period_id);target.searchParams.set('paper_review',r.intake_id);if(context.scope)target.searchParams.set('scope',context.scope);target.hash='supplementary-paper-reviews';a.href=target.href;card.append(a);return card;}
 const field=(label,value,cls='')=>{const section=el('section','',cls);section.append(el('h5',ui(label)),el('p',value));card.append(section);};
 field('paper_review_problem',pick(s,'background'));field('paper_review_method',pick(s,'innovation'));field('paper_review_results',pick(s,'results'));
 field('paper_review_value',pick(r,'selection_reason'));field('paper_review_next',pick(r,'next_step'));field('paper_review_limits',pick(r,'applicability_boundary'),'reader-note');
 card.append(el('p',ui(s.review_status==='method_results_checked'?'paper_review_checked':'paper_review_abstract')+' · '+s.evidence_locator,'meta'));
 return card;
}
async function fillReviews(root,ctx,ticket,compact=false){
 root.replaceChildren(el('p',ui('paper_review_loading'),'meta'));
 try{const rows=await reviewed(ctx);if(ticket!==epoch)return;root.replaceChildren();if(!rows.length)root.append(el('p',ui('paper_review_empty'),'reader-note'));else {const selected=new URLSearchParams(location.search).get('paper_review');const ordered=compact?rows:[...rows].sort((a,b)=>Number(b.intake.intake_id===selected)-Number(a.intake.intake_id===selected));for(const row of ordered)root.append(renderReviewCard(row,compact));}document.dispatchEvent(new Event('lri:sections-changed'));if(!compact)settleInitialAnchor();}
 catch(error){if(ticket!==epoch)return;root.replaceChildren(el('p',ui('paper_review_failed'),'reader-note'),button(ui('paper_review_retry'),()=>fillReviews(root,ctx,++epoch,compact)));console.error('Reviewed-paper intake unavailable',error);}
}
async function fillPending(root,ctx,ticket){
 root.replaceChildren(el('p',ui('paper_review_loading'),'meta'));
 try{const page=await LRICloudPaperQueueRead({revision:ctx.revision,offset,term});if(ticket!==epoch)return;
 root.replaceChildren(el('p',(page.rows.length?offset+1:0)+'–'+(offset+page.rows.length)+' / '+page.total+' · '+ui('paper_review_pending_count'),'meta'));
 const wrap=el('div','','table-wrap'),table=el('table'),head=el('thead'),tr=el('tr');for(const k of ['paper_review_paper','paper_review_identifier','paper_review_status'])tr.append(el('th',ui(k)));head.append(tr);table.append(head);const body=el('tbody');
 for(const r of page.rows){const row=el('tr'),name=el('td');name.append(r.sourceURLValid===false?el('span',r.title||r.external_id||r.source_id):link(r.title||r.external_id||r.source_id,r.canonical_url));row.append(name,el('td',r.external_id||'—'),el('td',ui('paper_review_unchecked')));body.append(row);}table.append(body);wrap.append(table);root.append(wrap);
 if(!page.rows.length)root.append(el('p',ui('paper_review_no_match'),'reader-note'));
 const actions=el('div','','actions'),prev=button(ui('paper_review_previous'),()=>{offset=Math.max(0,offset-10);fillPending(root,ctx,++epoch);}),next=button(ui('paper_review_next_page'),()=>{offset+=10;fillPending(root,ctx,++epoch);});prev.disabled=offset===0;next.disabled=!page.truncated;actions.append(prev,next);root.append(actions);
 }catch(error){if(ticket!==epoch)return;root.replaceChildren(el('p',ui('paper_review_failed'),'reader-note'),button(ui('paper_review_retry'),()=>fillPending(root,ctx,++epoch)));console.error('Imported paper queue unavailable',error);}
}
const pipelineTabs=[
 ['candidates','paper_pipeline_candidates'],['metadata','paper_pipeline_metadata'],
 ['manual','paper_pipeline_manual'],['issues','paper_pipeline_errors'],
 ['linkage','paper_pipeline_linkage'],['pending','paper_pipeline_raw'],['reviewed','paper_pipeline_reviewed']
];
const stageLabels={
 candidate_direct:'paper_pipeline_direct',candidate_adjacent:'paper_pipeline_adjacent',
 metadata_needed:'paper_pipeline_metadata',needs_relevance_review:'paper_pipeline_manual',
 blocked_invalid:'paper_pipeline_invalid',retryable_failure:'paper_pipeline_retryable',
 reviewed_unpublished:'paper_pipeline_unpublished',reconciliation_needed:'paper_pipeline_reconcile',
 reviewed_visible:'paper_pipeline_visible',excluded_manual:'paper_pipeline_excluded'
};
const evidenceLabels={
 primary_method_results_reviewed:'paper_review_checked',
 existing_review_unreconciled:'paper_pipeline_evidence_unreconciled',
 primary_abstract_reviewed:'paper_review_abstract',
 identity_unverified:'paper_pipeline_evidence_identity_pending',
 unreconciled_review_marker:'paper_pipeline_evidence_marker',
 identity_only:'paper_pipeline_evidence_identity',
 title_only:'paper_pipeline_evidence_title',
 metadata_acquisition_failed:'paper_pipeline_evidence_retry'
};
function queueCount(run,name){
 const fields={candidates:['candidate_direct','candidate_adjacent'],metadata:['metadata_needed'],manual:['needs_relevance_review'],issues:['blocked_invalid','retryable_failure'],linkage:['reviewed_unpublished','reconciliation_needed']}[name];
 return fields?fields.reduce((n,k)=>n+run[k],0):null;
}
function runSummary(root,run){
 root.replaceChildren();
 if(!run){root.append(el('p',ui('paper_pipeline_no_run'),'reader-note'));return;}
 const complete=run.status==='completed_audit_not_research_review';
 root.append(el('p',ui('paper_pipeline_run')+' · '+(run.completed_at||run.started_at),'eyebrow'));
 root.append(el('p',ui('paper_pipeline_coverage')+'：'+run.processed_sources.toLocaleString(context.locale)+' / '+run.total_sources.toLocaleString(context.locale)+' '+ui('paper_pipeline_population'),'reader-note'));
 root.append(el('p',ui(complete?'paper_pipeline_processed':'paper_pipeline_not_complete'),'meta'));
 root.append(el('p',ui('paper_pipeline_visible')+' '+run.reviewed_visible.toLocaleString(context.locale)+' · '+ui('paper_pipeline_excluded')+' '+run.excluded_manual.toLocaleString(context.locale),'meta'));
}
function renderPipelineCard(model){
 const r=model.pipeline,s=model.source,card=el('article','','card');card.dataset.sourcePipeline=r.source_id;card.dataset.pipelineStage=r.stage;
 card.append(el('p',ui(stageLabels[r.stage]||'paper_pipeline_unknown'),'eyebrow'));
 const title=el('h4'),label=s?.title||s?.external_id||r.source_id;
 title.append(model.sourceURLValid?link(label,s.canonical_url):el('span',label));card.append(title);
 if(!model.sourceURLValid)card.append(el('p',ui('paper_pipeline_unresolved'),'reader-note'));
 card.append(el('p',ui('paper_pipeline_key')+'：'+r.source_id+(s?.external_id?' · '+s.external_id:''),'meta'));
 if(context.locale==='en'&&(!r.reason_en||!r.next_action_en))card.append(el('p',ui('paper_pipeline_source_language'),'meta'));
 for(const [label,field] of [['paper_pipeline_reason','reason'],['paper_pipeline_next','next_action']]){
  const section=el('section');section.append(el('h5',ui(label)),el('p',pick(r,field)||ui('paper_pipeline_unknown')));card.append(section);
 }
 card.append(el('p',ui('paper_pipeline_evidence')+' · '+ui(evidenceLabels[r.evidence_level]||'paper_pipeline_unknown'),'meta'));
 return card;
}
async function fillPipeline(root,ctx,ticket){
 root.replaceChildren(el('p',ui('paper_review_loading'),'meta'));
 try{
  const page=await LRICloudPipelineRead({revision:ctx.revision,queue:tab,offset,term});
  if(ticket!==epoch)return;
  root.replaceChildren(el('p',(page.rows.length?offset+1:0)+'–'+(offset+page.rows.length)+' / '+page.total+' · '+ui('paper_pipeline_found'),'meta'));
  if(!page.rows.length)root.append(el('p',ui('paper_pipeline_empty'),'reader-note'));
  for(const model of page.rows)root.append(renderPipelineCard(model));
  const actions=el('div','','actions');
  const prev=button(ui('paper_review_previous'),()=>{offset=Math.max(0,offset-10);fillPipeline(root,ctx,++epoch);});
  const next=button(ui('paper_review_next_page'),()=>{offset+=10;fillPipeline(root,ctx,++epoch);});
  prev.disabled=offset===0;next.disabled=!page.truncated;actions.append(prev,next);root.append(actions);
  document.dispatchEvent(new Event('lri:sections-changed'));
 }catch(error){
  if(ticket!==epoch)return;
  root.replaceChildren(el('p',ui('paper_review_failed'),'reader-note'),button(ui('paper_review_retry'),()=>fillPipeline(root,ctx,++epoch)));
  console.error('System paper queue unavailable',error);
 }
}

function renderFunnel(root){
 if(!document.getElementById('paper-funnel-style')){const style=el('style',"\n/* A reading funnel, with explicit knowledge and period outputs. */\n.paper-funnel{padding:24px;border:1px solid #dbe3ed;border-radius:18px;background:linear-gradient(145deg,#f8fafc,#fff);margin:20px 0 28px;color:#172b45}.paper-funnel-steps{list-style:none;padding:0;display:grid;gap:10px}.paper-funnel-steps li{box-sizing:border-box;margin:auto;padding:14px 20px;width:100%;border-left:4px solid #b91c24;background:#fff;border-radius:8px;box-shadow:0 2px 8px #182c4510}.paper-funnel-steps li:nth-child(2){width:94%}.paper-funnel-steps li:nth-child(3){width:88%}.paper-funnel-steps li:nth-child(4){width:82%}.paper-funnel-steps li:nth-child(5){width:76%;background:#fff5f5}.paper-funnel-steps p{margin:6px 0 0;line-height:1.65;font-size:15px}.paper-funnel-outputs{border-top:1px solid #dbe3ed;margin-top:20px;padding-top:10px}.paper-funnel-outputs a{font-weight:700}.paper-funnel-outputs p{line-height:1.7}@media(max-width:640px){.paper-funnel{padding:16px}.paper-funnel-steps li:nth-child(n){width:100%;padding:12px}.paper-funnel-steps p{font-size:14px}}\n");style.id='paper-funnel-style';document.head.append(style);}
 const box=el('section','','paper-funnel');box.setAttribute('aria-label',ui('funnel_title'));
 box.append(el('h4',ui('funnel_title')));
 const list=el('ol','','paper-funnel-steps');
 for(let i=1;i<=5;i++){const item=el('li');item.append(el('strong',ui('funnel_step_'+i)),el('p',ui('funnel_detail_'+i)));list.append(item);}
 box.append(list);
 const outputs=el('div','','paper-funnel-outputs');
 for(const [key,hash] of [['funnel_topics','view-topics'],['funnel_month','view-updates'],['funnel_decisions','view-home']]){
  const p=el('p'),a=el('a',ui(key));a.href='#'+hash;p.append(a,el('span',ui(key+'_detail')));outputs.append(p);
 }
 box.append(outputs,el('p',ui('funnel_gate'),'reader-note'));root.append(box);
}

function sourcePanel(root,ctx){
 const ticket=++epoch;
 root.replaceChildren(el('h3',ui('paper_pipeline_title')),el('p',ui('paper_pipeline_help'),'reader-note'));
 renderFunnel(root);
 const summary=el('div');summary.append(el('p',ui('paper_review_loading'),'meta'));root.append(summary);
 const nav=el('nav','','actions'),buttons=new Map();
 nav.setAttribute('aria-label',ui('paper_pipeline_title'));
 for(const [name,label] of pipelineTabs){
  const b=button(ui(label),()=>{tab=name;offset=0;sourcePanel(root,ctx);});
  b.setAttribute('aria-pressed',String(tab===name));buttons.set(name,b);nav.append(b);
 }
 root.append(nav);
 const result=el('div','','wb-reading-list');result.setAttribute('aria-live','polite');
 if(tab!=='reviewed'){
  const form=el('form','','wb-filters'),label=el('label',ui('paper_review_search')),input=el('input');
  input.type='search';input.id='imported-paper-search';input.value=term;input.maxLength=120;label.htmlFor=input.id;
  const field=el('div');field.append(label,input);const submit=el('button',ui('paper_review_search_button'),'btn');submit.type='submit';
  form.append(field,submit);form.addEventListener('submit',event=>{event.preventDefault();term=input.value.trim();offset=0;sourcePanel(root,ctx);});root.append(form);
 }
 if(tab==='pending')root.append(el('p',ui('paper_pipeline_raw_help'),'reader-note'));
 if(tab==='reviewed')root.append(el('p',ctx.period+' · '+ui('paper_review_history_help'),'reader-note'));
 root.append(result);
 // The original imports and supplemental reviews remain available even if a scan is unavailable.
 if(tab==='reviewed')fillReviews(result,ctx,ticket,true);
 else result.append(el('p',ui('paper_review_loading'),'meta'));
 (async()=>{
  try{
   const {run}=await LRICloudPipelineRunRead(ctx.revision);if(ticket!==epoch)return;
   runSummary(summary,run);
   if(run)for(const [name,label] of pipelineTabs){const n=queueCount(run,name);if(n!==null)buttons.get(name).textContent=ui(label)+' · '+n.toLocaleString(ctx.locale);}
   if(tab!=='reviewed'){
    if(run?.status==='completed_audit_not_research_review')fillPipeline(result,ctx,ticket);
    else if(tab==='pending'){result.append(el('p',ui('paper_pipeline_raw_fallback'),'reader-note'));fillPending(result,ctx,ticket);}
    else result.replaceChildren(el('p',ui('paper_pipeline_no_run'),'reader-note'));
   }
  }catch(error){
   if(ticket!==epoch)return;
   summary.replaceChildren(el('p',ui('paper_pipeline_scan_failed'),'reader-note'),button(ui('paper_review_retry'),()=>sourcePanel(root,ctx)));
   if(tab==='pending')fillPending(result,ctx,ticket);else if(tab!=='reviewed')result.replaceChildren();
   console.error('System paper scan unavailable',error);
  }
 })();
}

function scrollReviewTarget(){
 const target=document.getElementById('supplementary-paper-reviews');if(!target||target.closest('[hidden]')||location.hash!=='#supplementary-paper-reviews')return;
 const header=document.querySelector('lri-site-shell')?.shadowRoot?.querySelector('header');
 const top=Math.max(0,header?.getBoundingClientRect().bottom||64)+20;
 window.scrollTo({top:Math.max(0,window.scrollY+target.getBoundingClientRect().top-top),behavior:'instant'});
}
function settleInitialAnchor(){
 const navigation=globalThis.LRICloudInitialNavigation;
 if(!navigation||navigation.hash!=='#supplementary-paper-reviews'||navigation.canceled||navigation.settling)return;
 navigation.settling=true;const started=performance.now();let previous=null,stableSince=started,lastAligned=null;
 const tick=()=>{
  if(navigation.canceled||location.hash!==navigation.hash||performance.now()-started>15000)return;
  const target=document.getElementById('supplementary-paper-reviews'),report=document.getElementById('monthly-route-report');
  if(!target||target.closest('[hidden]')){setTimeout(tick,150);return;}
  const y=target.getBoundingClientRect().top+window.scrollY,now=performance.now();
  if(previous===null||Math.abs(y-previous)>1){previous=y;stableSince=now;}
  const ready=Boolean(target.querySelector('[data-paper-review]')&&report?.querySelector('article')&&!document.getElementById('first-readable-content'));
  if(ready&&now-stableSince>650&&(lastAligned===null||Math.abs(y-lastAligned)>1)){scrollReviewTarget();lastAligned=y;}
  setTimeout(tick,150);
 };tick();
}
if(typeof document!=='undefined')document.addEventListener('click',event=>{
 const anchor=(event.composedPath?.()||[event.target]).find(n=>n?.tagName==='A'&&n.getAttribute('href')==='#supplementary-paper-reviews');
 if(anchor&&!event.ctrlKey&&!event.metaKey&&!event.shiftKey&&!event.altKey)setTimeout(scrollReviewTarget,0);
});

function reset(){epoch++;key='';context=null;for(const id of ['imported-paper-review','supplementary-paper-reviews'])document.getElementById(id)?.replaceChildren();}
function update(ctx){
 const source=document.getElementById('imported-paper-review'),target=document.getElementById('supplementary-paper-reviews');if(!source&&!target)return;
 if(!ctx.revision||!['sources','updates'].includes(ctx.view)){if(key){key='';epoch++;}return;}
 const newKey=JSON.stringify([ctx.revision,ctx.period,ctx.locale,ctx.view,ctx.scope]);if(key===newKey)return;key=newKey;context=ctx;epoch++;
 if(ctx.view==='sources'&&source)sourcePanel(source,ctx);
 if(ctx.view==='updates'&&target){target.replaceChildren(el('h3',ui('paper_review_supplementary')),el('p',ui('paper_review_history_help'),'reader-note'));const body=el('div','','wb-reading-list');target.append(body);fillReviews(body,ctx,++epoch);}
}
globalThis.LRIImportedPaperReview=Object.freeze({update,reset,validateReview,read:reviewed});
})();
