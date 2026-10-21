const $ = id => document.getElementById(id);
const state = {
  locale:document.querySelector('lri-shell')?.locale || (localStorage.getItem('lri_locale')==='en'?'en':'zh'), revision:'', profile:null, data:{
  }, packs:{
  }, stage:'sense', sourceOffset:0, sourcePage:null, documents:[], sourceRows:[], request:0, sourceRequest:0, documentRequest:0
};
const language = () => state.locale;
const label = key => state.packs[language()]?.strings?.[key] || state.packs.zh?.strings?.[key] || key;
function node(tag, text='', className='') {
  const result=document.createElement(tag);
  result.textContent=String(text);
  if(className) result.className=className;
  return result;
} function field(parent, key, value) {
  const p=node('p');
  p.append(node('strong',label(key)+': '),document.createTextNode(value===''||value==null?label('unknown'):String(value)));
  parent.append(p);
} function card(parent,title,copy=''){
  const el=node('article','','card');
  el.append(node('h3',title));
  if(copy)el.append(node('p',copy));
  parent.append(el);
  return el;
} function action(parent,key,handler){
  const button=node('button',label(key));
  button.type='button';
  button.addEventListener('click',handler);
  parent.append(button);
  return button;
} function clearViews(){
  for(const id of ['module-cards','stage-buttons','stage-detail','document-cards','document-detail','source-cards','source-detail','constraint-cards','metric-cards','experiment-cards','governance-cards'])$(id).replaceChildren();
  $('document-detail').hidden=true;
  $('source-detail').hidden=true;
  $('source-page').textContent='';
  $('measurement-state').textContent='';
} function fail(error){
  state.revision='';
  state.profile=null;
  state.data={
  };
  state.documents=[];
  state.sourceRows=[];
  state.sourcePage=null;
  state.request++;
  state.sourceRequest++;
  state.documentRequest++;
  clearViews();
  $('runtime-status').textContent=label('failed');
  $('runtime-status').setAttribute('role','alert');
  $('sources-prev').disabled=true;
  $('sources-next').disabled=true;
  console.error('Cloud Core data load failed',error);
} function checkRows(records){
  for(const row of records)if(row.business_id!=='cloud-core')throw new Error('Cross-business record');
  return records;
} async function page(name,options={
}){
  if(!state.revision)throw new Error('No pinned revision');
  const result=await LRITableGit.loadTablePage('cloud_core_'+name,{
    filterField:'business_id',filterValue:'cloud-core',limit:100,expectedRevision:state.revision,...options
  });
  checkRows(result.records);
  return result;
} async function small(name){
  const result=await page(name);
  if(result.page.truncated)throw new Error('Unexpected unbounded collection: '+name);
  return result.records;
} function renderModules(){
  const parent=$('module-cards');
  parent.replaceChildren();
  const options=$('module-filter');
  const selected=options.value;
  options.replaceChildren(node('option',label('all')));
  options.options[0].value='';
  for(const row of [...state.data.modules].sort((a,b)=>a.order-b.order)){
    card(parent,language()==='en'?row.name_en:row.name_zh,row.purpose);
    const option=node('option',language()==='en'?row.name_en:row.name_zh);
    option.value=row.module_id;
    options.append(option);
  }options.value=selected;
} function renderStage(){
  const buttons=$('stage-buttons');
  buttons.replaceChildren();
  for(const row of [...state.data.flywheel_stages].sort((a,b)=>a.order-b.order)){
    const b=node('button',`${row.order}. ${language()==='en'?row.name_en:row.name_zh}`);
    b.type='button';
    b.setAttribute('aria-pressed',String(row.stage_id===state.stage));
    b.addEventListener('click',()=>{
      state.stage=row.stage_id;
      renderStage();
    });
    buttons.append(b);
  }const row=state.data.flywheel_stages.find(x=>x.stage_id===state.stage);
  const detail=$('stage-detail');
  detail.replaceChildren();
  if(!row)return;
  detail.append(node('h3',language()==='en'?row.name_en:row.name_zh),node('p',label('proposed')));
  field(detail,'inputs',row.inputs);
  field(detail,'outputs',row.outputs);
  field(detail,'cadence',row.cadence);
  for(const gate of state.data.stage_gates.filter(x=>x.stage_id===row.stage_id)){
    field(detail,'gate',gate.rule);
    field(detail,'failure_action',gate.failure_action);
  }const target=state.data.flywheel_stages.find(x=>x.stage_id===row.feedback_stage_id);
  if(target){
    const b=action(detail,'feedback',()=>{
      state.stage=target.stage_id;
      renderStage();
    });
    b.append(document.createTextNode(' → '+(language()==='en'?target.name_en:target.name_zh)));
  }
} function renderMetrics(){
  for(const [name,parentId]of [['constraints','constraint-cards'],['metrics','metric-cards']]){
    $(parentId).replaceChildren();
    for(const row of state.data[name]){
      const el=card($(parentId),row.name,row.requirement||row.measurement_contract);
      field(el,'scenario',row.scenario_id);
      field(el,'review_status',label('proposed'));
      if(name==='metrics'){
        field(el,'unit',row.unit);
        field(el,'target',row.target_rule);
      }if(row.source_document_id)action(el,'original',()=>openDocument(row.source_document_id));
    }
  }
} function renderExperiments(){
  $('experiment-cards').replaceChildren();
  for(const row of state.data.experiments){
    const el=card($('experiment-cards'),row.metric_id,row.hypothesis);
    field(el,'acceptance',row.acceptance_rule);
    field(el,'review_status',label('proposed'));
  }const metadata=state.data.measurementMetadata;
  $('measurement-state').textContent=Number(metadata.tablegit?.status?.row_count??0)===0?label('no_measurements'):label('measurements_available');
} function renderGovernance(){
  $('governance-cards').replaceChildren();
  for(const run of state.data.import_runs){
    const el=card($('governance-cards'),run.batch_id);
    for(const [key,value]of [['documents',run.document_count],['sources',run.source_count],['references',run.reference_count],['excluded_names',run.excluded_name_count],['excluded_content',run.excluded_content_count],['retained_local',run.retained_local_count]])field(el,key,value);
    field(el,'review_status',run.status);
    field(el,'migration_policy',run.source_policy);
  }const issue=state.data.issueMetadata;
  field($('governance-cards'),'issue_count',issue.tablegit?.status?.row_count??0);
} function renderDocuments(){
  $('document-cards').replaceChildren();
  for(const row of state.documents){
    const el=card($('document-cards'),row.title);
    field(el,'review_status',label('unverified'));
    field(el,'origin_note',row.logical_path);
    action(el,'original',()=>openDocument(row.document_id));
  }if(!state.documents.length)$('document-cards').append(node('p',label('empty')));
} async function documents(){
  const request=++state.documentRequest;
  try{
    const module=$('module-filter').value;
    const result=await page('documents',module?{
      filterField:'module_id',filterValue:module
    }:{
    });
    if(request!==state.documentRequest)return;
    if(result.page.truncated)throw new Error('Document pagination required');
    state.documents=result.records;
    renderDocuments();
  }catch(error){
    if(request===state.documentRequest)fail(error);
  }
} async function openDocument(id){
  const request=++state.documentRequest;
  try{
    if(!/^note-[a-f0-9]{24}$/.test(id))throw new Error('Invalid document id');
    const result=await LRITableGit.loadRowsByKeys('cloud_core_documents',[id],state.revision);
    if(request!==state.documentRequest)return;
    checkRows(result.records);
    if(result.records.length!==1||typeof result.records[0].body!=='string')throw new Error('Document body requires bounded Content access');
    const row=result.records[0];
    const detail=$('document-detail');
    detail.replaceChildren(node('h3',row.title),node('p',label('unverified')),node('p',label('source_language')),node('pre',row.body));
    detail.hidden=false;
    detail.scrollIntoView({
      block:'start'
    });
    history.replaceState(null,'','#document/'+encodeURIComponent(id));
  }catch(error){
    if(request===state.documentRequest)fail(error);
  }
} function safeLink(url){
  const parsed=new URL(url);
  if(!['https:','http:'].includes(parsed.protocol)||parsed.username||parsed.password)throw new Error('Unsafe source URL');
  return parsed.href;
} function renderSources(){
  $('source-cards').replaceChildren();
  for(const row of state.sourceRows){
    const el=card($('source-cards'),row.title);
    const link=node('a',row.canonical_url);
    link.href=safeLink(row.canonical_url);
    link.target='_blank';
    link.rel='noopener noreferrer';
    el.append(link);
    field(el,'review_status',row.verification_status==='invalid_identifier'?label('invalid_identifier'):label('not_checked'));
    action(el,'provenance',()=>openSource(row));
  }if(!state.sourceRows.length)$('source-cards').append(node('p',label('empty')));
  const p=state.sourcePage;
  if(p){
    $('source-page').textContent=`${state.sourceRows.length ? state.sourceOffset+1 : 0}–${state.sourceOffset+state.sourceRows.length} / ${p.page.total}`;
    $('sources-prev').disabled=state.sourceOffset===0;
    $('sources-next').disabled=!p.page.truncated;
  }
} async function sources(offset=0){
  const request=++state.sourceRequest;
  try{
    const kind=$('source-kind').value;
    const result=await page('sources',{
      offset,limit:50,...(kind?{
        filterField:'source_kind',filterValue:kind
      }:{
      })
    });
    if(request!==state.sourceRequest)return;
    state.sourceOffset=offset;
    state.sourcePage=result;
    state.sourceRows=result.records;
    renderSources();
  }catch(error){
    if(request===state.sourceRequest)fail(error);
  }
} async function openSource(source){
  const request=++state.sourceRequest;
  try{
    const result=await page('source_refs',{
      filterField:'source_id',filterValue:source.source_id,limit:20
    });
    if(request!==state.sourceRequest)return;
    const detail=$('source-detail');
    detail.replaceChildren(node('h3',source.title));
    field(detail,'not_checked',source.verification_status);
    for(const row of result.records){
      const el=card(detail,row.origin_title);
      field(el,'origin_note',row.origin_note);
      field(el,'found',row.discovered_at);
      field(el,'version',row.observed_version);
      const a=node('a',label('observed_url'));
      a.href=safeLink(row.observed_url);
      a.target='_blank';
      a.rel='noopener noreferrer';
      el.append(a);
      if(row.document_id)action(el,'original',()=>openDocument(row.document_id));
    }if(result.page.truncated)detail.append(node('p',label('bounded_provenance')));
    detail.hidden=false;
    detail.scrollIntoView({
      block:'start'
    });
  }catch(error){
    if(request===state.sourceRequest)fail(error);
  }
} function render(){
  if(!state.profile)return;
  $('topic-title').textContent=label('archive_title');
  $('topic-summary').textContent=label('archive_summary');
  renderModules();
  renderStage();
  renderMetrics();
  renderExperiments();
  renderGovernance();
  if(state.documents.length)renderDocuments();
  if(state.sourcePage)renderSources();
  $('runtime-status').textContent=label('ready')+' · '+state.revision.slice(0,12);
} async function start(){
  const request=++state.request;
  state.sourceRequest++;
  state.documentRequest++;
  state.revision='';
  state.profile=null;
  state.sourceRows=[];
  state.sourcePage=null;
  state.documents=[];
  clearViews();
  $('runtime-status').setAttribute('role','status');
  $('runtime-status').textContent=label('loading');
  try{
    if(!state.packs.zh){
      const responses=await Promise.all(['zh','en'].map(lang=>fetch(`data/ui.${lang}.json?v=cloud-core-governance-v1`).then(r=>{
        if(!r.ok)throw new Error('UI locale load failed');
        return r.json();
      })));
      state.packs={
        zh:responses[0],en:responses[1]
      };
    }const profileResult=await LRITableGit.loadTablePage('topic_workbench_profiles',{filterField:'topic_id',filterValue:'cloud_core',limit:2});
    if(profileResult.records.length!==1||profileResult.records[0].topic_id!=='cloud_core')throw new Error('Invalid cloud-core library profile');
    const snapshot={revision:profileResult.revision,profile:profileResult.records[0]};
    if(request!==state.request)return;
    state.revision=snapshot.revision;
    const names=['modules','flywheel_stages','stage_gates','constraints','metrics','experiments','import_runs'];
    const records=await Promise.all(names.map(small));
    const metadata=await Promise.all(['cloud_core_measurements','cloud_core_import_issues'].map(name=>LRITableGit.loadTableMetadata(name,{expectedRevision:state.revision})));
    if(request!==state.request)return;
    for(const item of metadata)if((item.status?.revision||item.revision)!==state.revision)throw new Error('Metadata revision mismatch');
    state.data=Object.fromEntries(names.map((name,i)=>[name,records[i]]));
    state.data.measurementMetadata=metadata[0];
    state.data.issueMetadata=metadata[1];
    state.profile=snapshot.profile;
    render();
    const match=location.hash.match(/^#document\/(note-[a-f0-9]{24})$/);
    if(match)await openDocument(match[1]);
  }catch(error){
    if(request===state.request)fail(error);
  }
} $('reload').addEventListener('click',()=>{
  LRITableGit.invalidate();
  start();
});
$('load-documents').addEventListener('click',documents);
$('module-filter').addEventListener('change',documents);
$('load-sources').addEventListener('click',()=>sources(0));
$('source-kind').addEventListener('change',()=>sources(0));
$('sources-next').addEventListener('click',()=>sources(state.sourcePage?.page.nextOffset||0));
$('sources-prev').addEventListener('click',()=>sources(Math.max(0,state.sourceOffset-50)));
document.addEventListener('lri:locale-change',event=>{state.locale=event.detail.locale==='en'?'en':'zh';render();});
document.addEventListener('lri:force-refresh-ready',()=>{
  LRITableGit.invalidate();
  start();
});
window.addEventListener('hashchange',()=>{
  const match=location.hash.match(/^#document\/(note-[a-f0-9]{24})$/);
  if(match)openDocument(match[1]);
});
start();

