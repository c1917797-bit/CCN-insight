const $ = id => document.getElementById(id);
const state = {
  industrySnapshot:null,industryRevision:'',industryEpoch:-1,industryBusy:false,industryError:'',
  focusTarget:"",focusMechanism:"",focusCells:[],directionMode:false, locale:'zh', revision:'', profile:null, data:{}, directoryReady:false, directoryPartial:false, directoryDeferred:false, directoryData:null, directoryRevision:'', packs:{}, object:'', method:'', cell:'', all:true, view:'sources', domain:'hotspot', channelQuery:'', channelImportant:true, channelOffset:0, channelTotal:0, channelCategory:'', industryOffsets:{ascend:0,general:0},
  period:'', scope:'', scopes:[], reviews:[], scopeReady:false, scopeBusy:false, scopeError:false,
  evidence:[], evidencePage:null, evidenceOffset:0, evidenceBusy:false, evidenceError:false, evidenceProgress:null, relatedCache:null, paperIndexCache:null, paperSummaryError:'',
  legacy:[], legacyPeriod:'', legacyBusy:false, document:null, documentListKey:'', documentPending:null, disclosureOpen:new Map(),
  referencePending:false,referenceError:'', readerMode:'', sourceGroups:new Map(), sourcePending:new Map(), sourceStatusPending:null, sourceScansPending:null, sourceStatusReady:false, sourceStatusError:'', epoch:0, periodEpoch:0, scopeEpoch:0, evidenceEpoch:0, legacyEpoch:0, listEpoch:0, detailEpoch:0,
  collectionEpoch:0,collectionCache:new Map(),collectionPending:new Map(),collectionOffsets:new Map(),collectionStates:new Map()
};
try { state.locale = localStorage.getItem('lri_locale') === 'en' ? 'en' : 'zh'; } catch (_) {}
const label = key => state.packs[state.locale]?.strings[key] || state.packs.zh?.strings[key] || key;
const enumLabel = (prefix,value) => state.packs[state.locale]?.strings[prefix+value] || state.packs.zh?.strings[prefix+value] || value || label('pending');
const title = row => row && ((state.locale === 'en' ? (row.name_en||row.title_en) : (row.name_zh||row.title_zh)) || row.name_zh || row.title_zh || row.name || row.title || row.task_id || row.note_id) || '';
const textOf = (row,key) => row?.[key+'_'+state.locale] || row?.[key+'_zh'] || '';
const ordered = rows => [...rows].sort((a,b)=>(a.position||0)-(b.position||0));
const topicPage=()=>document.body.dataset.compressionTopic==='true';
const requestedTopic=()=>new URLSearchParams(location.search).get('topic')||'';
function restoreTopicNodes(){$('reading-controls').hidden=topicPage();}
const collectionNames=['objects','methods','cells','techniques','placements','trend_periods','tasks','review_notes','evaluation_dimensions','source_refs','flywheel_stages','lineages','lineage_nodes','lineage_relations','lineage_cells','source_scans','source_screenings','channels','source_categories','channel_categories','channel_provenance','channel_checks','findings','finding_evidence','finding_cells','finding_techniques','finding_keywords','finding_scopes','map_facets','map_terms','map_assignments','compression_topics','compression_topic_sections','compression_topic_concepts'];
const directoryNames=['channels','source_categories','channel_categories','channel_provenance','channel_checks','source_families','channel_families','industry_source_scopes'];
async function boundedRead(names,read,concurrency=4) {
  const result=new Array(names.length);let next=0;
  await Promise.all(Array.from({length:Math.min(concurrency,names.length)},async()=>{for(;;){const index=next++;if(index>=names.length)return;result[index]=await read(names[index]);}}));return result;
}
function showLoadError(error,partial=false) {
  const message=String(error.message||error).replace(/https?:\/\/\S+/g,'[URL]').slice(0,500);
  $('runtime-status').textContent=label(partial?'directory_partial':'failed')+' · '+message;
  $('runtime-status').setAttribute('role','alert');
}
const element = (tag, text='', cls='') => { const el=document.createElement(tag); el.textContent=String(text); if(cls)el.className=cls; return el; };
const viewIds={sources:['judgment-basis','channels-panel'],updates:['monthly'],topics:['map','knowledge'],home:['insight-overview','ascend'],reports:['reports','evidence','source-panel','document-detail','validation','appendix','legacy','governance']};
function viewForTarget(id) {
  if(!id)return 'sources';
  if(/^direction-[A-Z]_[A-Z]$/.test(id)||/^focus-[a-z_]+-[a-z_]+$/.test(id))return 'topics';
  if(/^view-(home|updates|topics|sources|reports)$/.test(id))return id.slice(5);
  const panel=$(id)?.closest('[data-view-panel]');
  if(panel&&Object.hasOwn(viewIds,panel.dataset.viewPanel))return panel.dataset.viewPanel;
  return Object.keys(viewIds).find(key=>viewIds[key].includes(id))||state.view||'sources';
}
function viewFromHash() { return viewForTarget(location.hash.slice(1))||'sources'; }
function revealHashTarget(id=location.hash.slice(1)) {
  const focusMatch=/^focus-([a-z_]+)-([a-z_]+)$/.exec(id);if(focusMatch){if(state.revision)openScientificFocus(focusMatch[1],focusMatch[2],false);return;}
  if(/^direction-[A-Z]_[A-Z]$/.test(id)){if(state.revision)openDirection(id.slice(10),false);return;}
  if(id==='view-topics'&&state.directionMode){state.directionMode=false;state.focusTarget='';state.focusMechanism='';state.focusCells=[];state.object='';state.cell='';state.method='';state.all=true;renderSelectors();renderMap();}
  const target=$(id);if(!target)return;
  showView(viewForTarget(id));
  for(let node=target;node;node=node.parentElement)if(node.tagName==='DETAILS')node.open=true;
  ensureOpenedDisclosuresLoaded();
  if(topicPage()&&(/^(research-overview-|direction-)/.test(id)))requestAnimationFrame(()=>$(id)?.scrollIntoView({block:'start'}));
}
function disclosure(key,summary) {
  const node=element('details');node.dataset.disclosureKey=key;
  node.open=state.disclosureOpen.get(key)===true;node.append(element('summary',summary));return node;
}
function showView(view,updateHash=false) {
  state.view=topicPage()?'topics':document.body.dataset.compressionMonthly==='true'?'updates':Object.hasOwn(viewIds,view)?view:'sources';
  $('reading-controls').hidden=topicPage()||['topics','sources'].includes(state.view);$('reading-context').hidden=topicPage()||['topics','sources'].includes(state.view);
  $('judgment-basis').hidden=!['updates','topics','sources'].includes(state.view);
  $('judgment-basis').dataset.sectionOutline=state.view==='updates'?'false':'true';
  document.querySelectorAll('[data-view-panel]').forEach(panel=>{panel.hidden=panel.dataset.viewPanel!==state.view;});
  document.querySelectorAll('[data-view]').forEach(link=>{if(link.dataset.view===state.view)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current');});
  if(!topicPage()){if(state.view==='home'&&document.querySelector('.analysis-reading-navigation')){document.body.dataset.lriReaderNavigation='.analysis-reading-navigation';document.body.dataset.lriReaderNavigationLabel=mapText('洞察报告 · 阅读目录','Insight report · Reading contents');}else if(state.view==='updates'&&document.querySelector('.current-updates-navigation')){document.body.dataset.lriReaderNavigation='.current-updates-navigation';document.body.dataset.lriReaderNavigationLabel=mapText('本期动态 · 三类进展','Current updates · Three streams');}else{delete document.body.dataset.lriReaderNavigation;delete document.body.dataset.lriReaderNavigationLabel;}}
  document.body.dataset.compressionView=state.view;
  document.body.dataset.lriContextItem='cloud-core-'+state.view;refreshSynthesis();refreshImportedPapers();
  document.dispatchEvent(new Event('lri:sections-changed'));
  renderViewPurpose();
  if(updateHash&&location.hash!=='#view-'+state.view)history.pushState(null,'','#view-'+state.view);
  if(!topicPage()&&state.readerMode==='sources'&&state.view!=='sources'){start(state.view);return;}
  if(!topicPage()&&state.readerMode==='current'&&!['updates','home'].includes(state.view)){start(state.view);return;}
  if(!topicPage()&&state.readerMode==='map'&&state.view!=='topics'){start(state.view);return;}
  if(state.view==='sources'&&state.directoryDeferred&&state.profile){state.directoryDeferred=false;start('sources');return;}
  if((!topicPage()&&['updates','home'].includes(state.view))&&state.profile&&state.scopeReady&&!state.evidencePage&&!state.evidenceBusy)loadEvidence(0);
  if(updateHash&&location.hash!=='#view-'+state.view)history.pushState(null,'','#view-'+state.view);
}
function renderReadingGuide(){
 const root=$('reading-guide');if(!root)return;
 root.hidden=topicPage()||document.body.dataset.compressionMonthly==='true';if(root.hidden)return;
 if(root.dataset.locale===state.locale&&root.children.length)return;
 root.replaceChildren();root.dataset.locale=state.locale;root.className='';
 root.append(element('h3',mapText('阅读指南','Reading guide')));
 const rows=[
 ['信息来源：了解信源定位与选择理由。','Sources: source coverage and selection criteria.'],
 ['技术地图：查阅各专题的背景、挑战、原理与技术路线。','Technology map: background, challenges, mechanisms and research directions.'],
 ['本期动态：查看当月论文、产业进展与热点事件。','Current updates: this month’s papers, industry developments and news.'],
 ['洞察报告：阅读综合判断、技术取舍与业务落地建议。','Insight report: synthesis, technical priorities and business recommendations.'],
 ['洞察归档：回看历月报告与判断变化。','Archive: previous reports and changes in assessment.']
 ];
 const list=element('ul');for(const row of rows)list.append(element('li',mapText(...row)));root.append(list);
}
function renderViewPurpose(){renderReadingGuide();const parent=$('view-purpose');if(parent){parent.replaceChildren();parent.hidden=true;}}

function integrity(message) { const error=new Error(message); error.code='data_integrity'; return error; }
function must(condition,message) { if(!condition)throw integrity(message); }
function fatal(error) { return error.code==='revision_mismatch'||error.code==='data_integrity'||/revision mismatch|invalid Hosted Table|duplicate Hosted Table/i.test(error.message); }
function field(parent,key,value) { const p=element('p'); p.append(element('strong',label(key)+': '),document.createTextNode(value==null||value===''?label('pending'):String(value))); parent.append(p); return p; }
function button(text,handler,scopeDependent=false) { const el=element('button',text,'btn'); el.type='button'; el.dataset.dependent=''; if(scopeDependent)el.dataset.scopeDependent=''; el.disabled=!state.revision||(scopeDependent&&!state.scopeReady); el.addEventListener('click',handler); return el; }
function safeUrl(value) {
  let url; try { url=new URL(value); } catch (_) { throw integrity('Invalid public source URL'); }
  const host=url.hostname.toLowerCase();
  must(['http:','https:'].includes(url.protocol)&&!url.username&&!url.password&&host&&!['localhost','127.0.0.1','[::1]'].includes(host)&&!host.endsWith('.localhost'),'Unsafe source URL');
  for(const params of [url.searchParams,new URLSearchParams(url.hash.slice(1))])for(const key of params.keys()) {
    const normalized=key.toLowerCase().replace(/[^a-z0-9]/g,'');
    must(!['token','secret','password','credential','apikey','signature','bearer'].some(term=>normalized.includes(term))&&(!normalized.startsWith('auth')||normalized.startsWith('author')),'Authentication parameter in source URL');
  }
  return url.href;
}
function external(parent,url,text) { if(!url)return; const link=element('a',text,'btn'); link.href=safeUrl(url); link.target='_blank'; link.rel='noopener noreferrer'; parent.append(link); }
function controls(enabled) {
  document.querySelectorAll('[data-dependent]').forEach(el=>{
    el.disabled=!enabled || (el.hasAttribute('data-scope-dependent')&&!state.scopeReady) ||
      (el.dataset.pagination==='prev'&&(state.evidenceBusy||!state.evidencePage||state.evidenceOffset===0)) ||
      (el.dataset.pagination==='next'&&(state.evidenceBusy||!state.evidencePage?.truncated)) ||
      (el.id==='channel-prev'&&state.channelOffset===0) || (el.id==='channel-next'&&state.channelOffset+20>=state.channelTotal);
  });
  $('scope-filter').disabled=!enabled||state.scopeBusy||!state.scopes.length;
}
function assertBusiness(records) { for(const row of records)must(row.business_id==='cloud-core'&&row.topic_id==='cloud_core','Cross-business row'); return records; }
async function page(name,filterField,filterValue,revision,options={}) {
  const result=await LRITableGit.loadTablePage('ic_'+name,{filterField,filterValue,limit:100,expectedRevision:revision,...options});
  assertBusiness(result.records); return result;
}
async function small(name,revision) {
  const records=[]; let offset=0; let total=null;
  for(;;) {
    const result=await page(name,'topic_id','cloud_core',revision,{offset,limit:100});
    const meta=result.page;
    must(meta&&Number.isSafeInteger(meta.total)&&meta.total>=0&&Array.isArray(result.records),'Invalid compression collection page');
    if(total===null) total=meta.total; else must(total===meta.total,'Compression collection total changed');
    records.push(...result.records);
    if(!meta.truncated) { must(records.length===total,'Incomplete compression collection'); break; }
    must(result.records.length>0&&Number.isSafeInteger(meta.nextOffset)&&meta.nextOffset===offset+result.records.length,'Invalid compression collection cursor');
    offset=meta.nextOffset;
  }
  return ordered(records);
}
async function loadCatalog(name,revision) {
  const keys={channels:'channel_id',source_categories:'category_id',channel_categories:'membership_id',channel_provenance:'provenance_id',channel_checks:'check_id',source_families:'family_id',channel_families:'membership_id',industry_source_scopes:'family_id'},key=keys[name];
  must(Boolean(key),'Unknown source catalog');
  const request=state.epoch,records=[],seen=new Set(); let offset=0,total=null;
  for(;;) {
    const result=await page(name,'topic_id','cloud_core',revision,{offset,limit:100});
    if(request!==state.epoch)return []; validateEvidenceRevision(result,revision);
    const meta=result.page;
    must(meta&&Number.isSafeInteger(meta.total)&&meta.total>=0&&typeof meta.truncated==='boolean'&&Array.isArray(result.records)&&result.records.length<=100,'Invalid source catalog page');
    must(meta.total<=2000,'Catalog record limit exceeded (2000)');
    if(total===null)total=meta.total; else must(total===meta.total,'Source catalog total changed');
    if(meta.offset!==undefined)must(meta.offset===offset,'Source catalog offset drift');
    for(const row of result.records) { must(typeof row[key]==='string'&&row[key]&&!seen.has(row[key]),'Repeated or missing source catalog identity'); seen.add(row[key]); records.push(row); }
    must(records.length<=total&&(result.records.length>0||total===0),'Source catalog pagination made no progress');
    must(meta.truncated===(records.length<total),'Incomplete source catalog pagination');
    if(!meta.truncated) { must(records.length===total,'Incomplete source catalog total'); break; }
    must(Number.isSafeInteger(meta.nextOffset)&&meta.nextOffset===offset+result.records.length&&meta.nextOffset>offset&&meta.nextOffset<total,'Invalid source catalog pagination cursor');
    offset=meta.nextOffset;
  }
  return ordered(records);
}
function resetDetails() { state.documentListKey=''; state.listEpoch++; state.detailEpoch++; state.document=null; $('document-list').replaceChildren(); $('document-detail').replaceChildren(); $('document-detail').hidden=true; $('document-status').textContent=''; }
function resetCollection() {
  state.collectionEpoch++;state.collectionCache.clear();state.collectionPending.clear();state.collectionOffsets.clear();state.collectionStates.clear();
  $('collection-summary')?.replaceChildren();
}
async function loadCollectionRows(name,filterField,filterValue,revision,request=state.epoch) {
  const keyField={collection_runs:'run_id',channel_retrievals:'retrieval_id'}[name];must(Boolean(keyField),'Unknown discovery metadata collection');
  const cacheKey=[revision,name,filterField,filterValue].join('|'),pendingKey=request+'|'+cacheKey;
  if(state.collectionCache.has(cacheKey))return state.collectionCache.get(cacheKey);
  if(state.collectionPending.has(pendingKey))return state.collectionPending.get(pendingKey);
  const promise=(async()=>{
    const records=[],seen=new Set();let offset=0,total=null;
    for(;;) {
      const result=await page(name,filterField,filterValue,revision,{offset,limit:100});
      if(request!==state.epoch)return [];validateEvidenceRevision(result,revision);
      const meta=result.page;must(meta&&Number.isSafeInteger(meta.total)&&meta.total>=0&&meta.total<=2000&&typeof meta.truncated==='boolean'&&Array.isArray(result.records)&&result.records.length<=100,'Invalid bounded discovery metadata page');
      if(total===null)total=meta.total;else must(total===meta.total,'Discovery metadata total changed');
      if(meta.offset!==undefined)must(meta.offset===offset,'Discovery metadata offset drift');
      for(const row of result.records){must(typeof row[keyField]==='string'&&row[keyField]&&!seen.has(row[keyField]),'Repeated discovery metadata identity');seen.add(row[keyField]);records.push(row);}
      must(records.length<=total&&(result.records.length>0||total===0)&&meta.truncated===(records.length<total),'Incomplete discovery metadata page');
      if(!meta.truncated)break;
      must(Number.isSafeInteger(meta.nextOffset)&&meta.nextOffset===offset+result.records.length&&meta.nextOffset>offset&&meta.nextOffset<total,'Invalid discovery metadata cursor');offset=meta.nextOffset;
    }
    if(request!==state.epoch)return [];
    const rows=ordered(records);state.collectionCache.set(cacheKey,rows);return rows;
  })();
  state.collectionPending.set(pendingKey,promise);
  try{return await promise;}finally{if(state.collectionPending.get(pendingKey)===promise)state.collectionPending.delete(pendingKey);}
}
function currentCollectionRun() { return (state.data.collection_runs||[]).find(row=>row.run_id===state.data.collection_run_id); }
function currentCollectionRetrieval(channelId) { return (state.data.collection_retrievals||[]).find(row=>row.channel_id===channelId&&row.run_id===state.data.collection_run_id); }
function collectionDate(value) { const parsed=new Date(value+'T00:00:00Z');return /^\d{4}-\d{2}-\d{2}$/.test(value)&&!Number.isNaN(parsed.getTime())&&parsed.toISOString().slice(0,10)===value; }
function validateCollectionSnapshot(data) {
  const run=(data.collection_runs||[]).find(row=>row.run_id===data.collection_run_id),rows=data.collection_retrievals||[];
  if(!run){must(!rows.length,'Retrievals have no discovery run');return;}
  must(['running','completed','partial','failed'].includes(run.status),'Unknown discovery run status');
  const counts=['requested_channels','attempted_channels','successful_channels','failed_channels','dated_entries','undated_entries','candidate_entries'];
  for(const key of counts)must(Number.isSafeInteger(run[key])&&run[key]>=0,'Invalid discovery run count');
  must(run.requested_channels<=(data.channels||[]).length&&rows.length===run.requested_channels&&new Set(rows.map(row=>row.channel_id)).size===rows.length,'Discovery run channel counts disagree');
  for(const row of rows){const channel=(data.channels||[]).find(item=>item.channel_id===row.channel_id);must(channel&&row.source_id===channel.source_id&&row.run_id===run.run_id,'Discovery retrieval ownership drift');
    must(['success','failed','not_attempted','skipped'].includes(row.status),'Unknown retrieval status');
    for(const key of ['received_count','dated_count','undated_count','candidate_count'])must(Number.isSafeInteger(row[key])&&row[key]>=0,'Invalid retrieval count');
    must(row.received_count<=2000&&row.received_count===row.dated_count+row.undated_count&&row.candidate_count<=row.received_count,'Discovery retrieval counts disagree');
    must((row.status==='failed'?Boolean(row.failure_code):!row.failure_code)&&(row.status==='success'||row.received_count===0),'Discovery failure boundary missing');
  }
  const sum=key=>rows.reduce((total,row)=>total+row[key],0),attempted=rows.filter(row=>['success','failed'].includes(row.status));
  must(run.attempted_channels===attempted.length&&run.successful_channels===rows.filter(row=>row.status==='success').length&&run.failed_channels===rows.filter(row=>row.status==='failed').length&&run.dated_entries===sum('dated_count')&&run.undated_entries===sum('undated_count')&&run.candidate_entries===sum('candidate_count'),'Discovery run totals disagree');
}
function renderCollectionRun() {
  const parent=$('collection-summary');if(!parent)return;parent.replaceChildren();const run=currentCollectionRun();
  if(state.readerMode==='sources'&&!state.sourceStatusReady){parent.append(element('p',state.sourceStatusError||mapText('展开后读取采集状态；信源入口可直接访问。','Expand to read collection status; source links are available.')));return;}
  if(!run){parent.append(element('p',label('collection_run_none')));return;}
  parent.append(element('h3',label('collection_run')+' · '+enumLabel('collection_run_',run.status)),element('p',label('collection_run_cutoff')+': '+run.cutoff_date+' · '+label('collected_at')+': '+run.completed_at));
  field(parent,'collection_scope',textOf(run,'scope_note'));
  parent.append(element('p',label('collection_attempted')+': '+run.attempted_channels+' / '+run.requested_channels+' · '+label('collection_successful')+': '+run.successful_channels+' · '+label('collection_failed')+': '+run.failed_channels));
  parent.append(element('p',label('collection_dated')+': '+run.dated_entries+' · '+label('collection_undated')+': '+run.undated_entries+' · '+label('collection_candidates')+': '+run.candidate_entries));
}
function renderCollectionEntries(retrieval,parent) {
  parent.replaceChildren();const offset=state.collectionOffsets.get(retrieval.retrieval_id)||0,cacheKey=[state.revision,retrieval.retrieval_id,offset].join('|'),cached=state.collectionCache.get(cacheKey),status=state.collectionStates.get(cacheKey);
  parent.append(element('h4',label('collection_entries')),element('p',label('collection_entries_help'),'meta'));
  if(status==='failed'){parent.append(element('p',label('collection_entries_failed')),button(label('retry'),()=>loadCollectionEntries(retrieval.retrieval_id,offset,true)));return;}
  if(!cached){parent.append(element('p',label('collection_entries_loading')));return;}
  parent.append(element('p',label('collection_entries_range')+': '+(cached.rows.length?offset+1:0)+'–'+(offset+cached.rows.length)+' / '+cached.total,'meta'));
  if(!cached.rows.length)parent.append(element('p',label('collection_entries_empty')));
  const list=element('ol');
  for(const row of cached.rows){const source=cached.sources.find(item=>item.source_id===row.source_id),item=element('li');item.append(element('h4',source.title));
    field(item,'collection_page_date',(row.date_value||label('collection_date_unverified'))+' · '+enumLabel('collection_date_',row.date_kind));
    field(item,'collection_selection',enumLabel('collection_selection_',row.selection_status));item.append(element('p',enumLabel('collection_review_',row.review_status),'wb-evidence-note'));field(item,'collection_locator',row.locator);external(item,source.canonical_url,label('original_source'));list.append(item);}
  parent.append(list);const actions=element('div','','actions');
  if(offset>0)actions.append(button(label('previous'),()=>loadCollectionEntries(retrieval.retrieval_id,Math.max(0,offset-20))));
  if(cached.truncated)actions.append(button(label('next'),()=>loadCollectionEntries(retrieval.retrieval_id,cached.nextOffset)));parent.append(actions);
}
function refreshCollectionDetails(retrievalId) {
  const retrieval=(state.data.collection_retrievals||[]).find(row=>row.retrieval_id===retrievalId);if(!retrieval)return;
  document.querySelectorAll('[data-collection-retrieval]').forEach(node=>{if(node.open&&node.dataset.collectionRetrieval===retrievalId&&node.collectionContainer)renderCollectionEntries(retrieval,node.collectionContainer);});
}
async function loadCollectionEntries(retrievalId,offset=state.collectionOffsets.get(retrievalId)||0,force=false) {
  if(!state.revision)return;const retrieval=(state.data.collection_retrievals||[]).find(row=>row.retrieval_id===retrievalId&&row.run_id===state.data.collection_run_id);if(!retrieval)return;
  must(Number.isSafeInteger(offset)&&offset>=0,'Invalid discovery entry offset');state.collectionOffsets.set(retrievalId,offset);
  const revision=state.revision,request=state.epoch,collectionEpoch=state.collectionEpoch,cacheKey=[revision,retrievalId,offset].join('|'),pendingKey=[request,collectionEpoch,cacheKey].join('|');
  const active=()=>request===state.epoch&&collectionEpoch===state.collectionEpoch&&revision===state.revision&&retrieval.run_id===state.data.collection_run_id;
  if(!force&&state.collectionCache.has(cacheKey)){refreshCollectionDetails(retrievalId);return state.collectionCache.get(cacheKey);}
  if(state.collectionPending.has(pendingKey))return state.collectionPending.get(pendingKey);
  state.collectionStates.set(cacheKey,'loading');refreshCollectionDetails(retrievalId);
  const promise=(async()=>{
    try{
      const result=await page('collection_entries','retrieval_id',retrievalId,revision,{offset,limit:20});if(!active())return;validateEvidenceRevision(result,revision);
      const meta=result.page;must(meta&&Number.isSafeInteger(meta.total)&&meta.total>=0&&meta.total<=2000&&meta.total===retrieval.received_count&&typeof meta.truncated==='boolean'&&Array.isArray(result.records)&&result.records.length<=20,'Invalid discovery entry page');
      must(meta.offset===undefined||meta.offset===offset,'Discovery entry offset drift');must(offset+result.records.length<=meta.total&&meta.truncated===(offset+result.records.length<meta.total)&&(result.records.length>0||meta.total===0),'Incomplete discovery entry page');
      if(meta.truncated)must(Number.isSafeInteger(meta.nextOffset)&&meta.nextOffset===offset+result.records.length&&meta.nextOffset>offset,'Invalid discovery entry cursor');
      must(new Set(result.records.map(row=>row.entry_id)).size===result.records.length,'Duplicate discovery entry');
      const run=currentCollectionRun();for(const row of result.records){must(row.entry_id&&row.retrieval_id===retrievalId&&row.run_id===retrieval.run_id&&row.channel_id===retrieval.channel_id&&typeof row.source_id==='string'&&row.source_id,'Discovery entry ownership drift');
        must(row.review_status==='listing_metadata_not_primary_review'&&['title_match_pending_review','unmatched_title','reference'].includes(row.selection_status),'Discovery metadata promoted to reviewed fact');
        must(['published','updated','source_claimed_date','unverified'].includes(row.date_kind)&&typeof row.date_value==='string'&&(row.date_kind==='unverified'?row.date_value==='':collectionDate(row.date_value)&&row.date_value<=run.cutoff_date),'Unverified discovery date');
      }
      const ids=[...new Set(result.records.map(row=>row.source_id))],sources=ids.length?await LRITableGit.loadRowsByKeys('cloud_core_sources',ids,revision,['source_id','business_id','title','canonical_url']):{records:[],revision};
      if(!active())return;validateEvidenceRevision(sources,revision);must(sources.records.length===ids.length&&new Set(sources.records.map(row=>row.source_id)).size===ids.length&&sources.records.every(row=>ids.includes(row.source_id)&&row.business_id==='cloud-core'&&typeof row.title==='string'&&row.title),'Missing exact discovery canonical source');for(const source of sources.records)safeUrl(source.canonical_url);
      const value={rows:ordered(result.records),sources:sources.records,total:meta.total,truncated:meta.truncated,nextOffset:meta.nextOffset};state.collectionCache.set(cacheKey,value);state.collectionStates.set(cacheKey,'ready');if((state.collectionOffsets.get(retrievalId)||0)===offset)refreshCollectionDetails(retrievalId);return value;
    }catch(error){if(active()){if(fatal(error))fail(error);else{state.collectionStates.set(cacheKey,'failed');if((state.collectionOffsets.get(retrievalId)||0)===offset)refreshCollectionDetails(retrievalId);}}}
    finally{if(state.collectionPending.get(pendingKey)===promise)state.collectionPending.delete(pendingKey);}
  })();state.collectionPending.set(pendingKey,promise);return promise;
}
function resetEvidence() {
  globalThis.LRICompressionMonthly?.reset();
  state.evidenceEpoch++; state.paperSummaryError=''; state.evidence=[]; state.evidencePage=null; state.evidenceOffset=0; state.evidenceBusy=false; state.evidenceError=false; state.evidenceProgress=null;
  $('evidence-cards').replaceChildren(); $('evidence-status').textContent=''; $('paper-summary-status').textContent=''; $('evidence-retry').hidden=true;
}
function clear() {
  globalThis.LRIImportedPaperReview?.reset();
  state.relatedCache=null; state.paperIndexCache=null;
  resetCollection();
  for(const id of ['topic-title','topic-summary','reading-context','home-period','home-judgement','finding-cards','update-finding-cards','report-list','channel-status','insight-observation','insight-boundary','insight-freshness','channel-cards','ascend-cards','lineage-cards','source-scan-cards','direction-detail','monthly-directions','selection-title','selection-status','cell-review','scope-detail','monthly-status','monthly-rows','legacy-status','technique-cards','task-cards','benchmark-contract','measurement-status','review-notes','flywheel-path','flywheel-rules'])$(id).replaceChildren();
  $('direction-detail').hidden=true;
  $('cell-review').hidden=true; resetDetails(); resetEvidence();
}
function fail(error) {
  globalThis.LRICloudFirstRetire?.();
  const directory=state.directoryReady?state.directoryData:null,revision=state.directoryRevision;
  state.epoch++; state.periodEpoch++; state.scopeEpoch++; state.legacyEpoch++; state.revision=''; state.profile=null; state.data={}; state.scopeReady=false; state.scopes=[]; state.reviews=[];
  for(const key of state.disclosureOpen.keys())if(key.startsWith('channel:'))state.disclosureOpen.set(key,false);
  clear();controls(false);$('scope-retry').hidden=true;
  if(directory){state.data=directory;state.revision=revision;$('topic-title').textContent=label('eyebrow');renderChannels();showLoadError(error,true);}else{state.directoryReady=false;showLoadError(error);}
  console.error('Compression snapshot unavailable',error);
}
function currentScope() { return state.scopes.find(row=>row.scope_id===state.scope); }
function currentCell() { return state.data.cells?.find(row=>row.cell_id===state.cell); }
function cellTitle(cell) { return title(cell)||[title(state.data.objects.find(row=>row.object_id===cell?.object_id)),title(state.data.methods.find(row=>row.method_id===cell?.method_id))].join(' × '); }
function currentReview(cellId) { return state.reviews.find(row=>row.cell_id===cellId); }
function renderOverview() {
  const observation=$('insight-observation'),boundary=$('insight-boundary'),freshness=$('insight-freshness');
  observation.replaceChildren(); boundary.replaceChildren(); freshness.replaceChildren(); $('home-judgement').replaceChildren();
  if(!state.profile)return;
  const scope=currentScope();
  const period=state.data.trend_periods.find(row=>row.period_id===state.period);
  $('home-period').textContent=label('view_home')+(period?' · '+period.month:'')+' · '+label('latest_check_record')+': '+state.profile.last_verified;
  $('home-judgement').textContent=label('conclusion_from_checked_facts');
  if(state.scopeError)observation.append(element('p',label('scope_read_failed')));
  else if(state.scopeBusy)observation.append(element('p',label('loading')));
  else if(!scope||!state.scopeReady)observation.append(element('p',label('no_scope')));
  else {
    observation.append(element('p',scope.coverage_note||label('sample_boundary')),element('p',label('curation_scope_boundary'),'meta'));
    boundary.append(element('p',enumLabel('status_',scope.status)+' · '+label('validation_per_item')));
    boundary.append(element('p',label('source_collection_boundary'),'meta'));
  }
  if(scope)freshness.append(element('p',label('scope_window')+': '+scope.window_start+' — '+scope.window_end+' · '+label('collected_at')+': '+scope.collected_at));
  freshness.append(element('p',label('last_verified')+': '+state.profile.last_verified+' · '+label('snapshot_revision')+': '+state.revision.slice(0,12)));
  renderFindings();
}
function visibleFindings(currentOnly=false) {
  const period=state.data.trend_periods?.find(row=>row.period_id===state.period),scope=currentScope();
  const selectedCells=new Set(state.focusCells.length?state.focusCells:state.cell?[state.cell]:state.data.cells.filter(cell=>!state.object||cell.object_id===state.object).map(cell=>cell.cell_id));
  const relatedIds=new Set((state.data.finding_cells||[]).filter(link=>selectedCells.has(link.cell_id)).map(row=>row.finding_id));
  return ordered(state.data.findings||[]).filter(row=>{
    if((state.cell||state.object)&&!relatedIds.has(row.finding_id))return false;
    const event=row.kind==='current_event'&&row.recent_event_eligible===true;
    if(currentOnly&&!event)return false;
    if(event) {
      if(!state.scopeReady||!period||!scope||!row.change_date||!state.data.finding_scopes.some(link=>link.finding_id===row.finding_id&&link.scope_id===state.scope))return false;
      if(!row.change_date.startsWith(period.month)||row.change_date<scope.window_start||row.change_date>scope.window_end)return false;
    }
    return true;
  });
}
function findingCard(row,layer='conclusion') {
  const card=element('article','','card'); card.dataset.finding=row.finding_id;
  const links=state.data.finding_evidence.filter(item=>item.finding_id===row.finding_id);
  const sources=[...new Map(links.map(link=>[link.source_id,sourceById(link.source_id)])).values()];
  const facts=element('div');facts.dataset.readingLayer='facts';
  facts.append(element('p',enumLabel('finding_kind_',row.kind)+(row.change_date?' · '+row.change_date:''),'meta'),element('h3',sources.map(source=>source.title).join(' / ')));
  field(facts,'source_facts',textOf(row,'change'));
  if(textOf(row,'mechanism')&&textOf(row,'mechanism')!==textOf(row,'change'))field(facts,'reported_mechanism',textOf(row,'mechanism'));
  const keywords=element('div','','wb-keywords');
  for(const word of ordered(state.data.finding_keywords.filter(item=>item.finding_id===row.finding_id)))keywords.append(element('span',textOf(word,'keyword'),'wb-keyword'));
  if(keywords.children.length){keywords.setAttribute('aria-label',label('keywords'));facts.append(keywords);}
  const findingCells=new Set(state.data.finding_cells.filter(link=>link.finding_id===row.finding_id).map(link=>link.cell_id));
  field(facts,'related_directions',ordered(state.data.cells).filter(cell=>findingCells.has(cell.cell_id)).map(cellTitle).join(' · '));
  if(row.publication_date)field(facts,'publication_date',row.publication_date);
  else facts.append(element('p',label('no_verified_publication_date'),'meta'));
  field(facts,'date_kind',enumLabel('date_',row.date_kind));field(facts,'checked_at',row.checked_at);
  const depths=[...new Set(links.map(link=>enumLabel('depth_',link.checked_scope)))];
  facts.append(element('p',label('review_depth')+': '+depths.join(' / ')+' · '+label(links.some(link=>link.local_measurement)?'measurement_recorded':'no_local_validation'),'wb-evidence-note'));
  const originals=element('div','','actions');
  for(const source of sources)external(originals,source.canonical_url,label('original_source')+' · '+(source.external_id||source.title));facts.append(originals);card.append(facts);
  const more=disclosure('finding:'+layer+':'+row.finding_id+':analysis',label('read_in_detail'));more.dataset.readingLayer='analysis';
  field(more,'background',textOf(row,'background'));field(more,'innovation',textOf(row,'innovation'));field(more,'results',textOf(row,'results'));
  field(more,'boundary',textOf(row,'ascend_boundary'));
  for(const link of links) {
    const source=sourceById(link.source_id),evidence=element('div','','wb-finding-source');
    evidence.append(element('h4',source.title));field(evidence,'supported_claim',textOf(link,'supported_claim'));
    field(evidence,'review_depth',enumLabel('depth_',link.checked_scope));field(evidence,'evidence_locator',link.evidence_locator);
    field(evidence,'observed_version',link.observed_version);field(evidence,'checked_at',link.checked_at);
    more.append(evidence);
  }
  card.append(more);
  if(layer==='conclusion') {
    const conclusion=element('div','','wb-finding-conclusion');conclusion.dataset.readingLayer='conclusion';
    conclusion.append(element('h4',label('analyst_conclusion')),element('p',label('analyst_implication'),'meta'));
    field(conclusion,'one_sentence',textOf(row,'summary'));field(conclusion,'research_relevance',textOf(row,'relevance'));if(textOf(row,'implication')!==textOf(row,'relevance'))field(conclusion,'business_implication',textOf(row,'implication'));
    const advice=disclosure('finding:'+layer+':'+row.finding_id+':advice',label('next_action'));advice.append(element('p',textOf(row,'next_suggestion')));conclusion.append(advice);card.append(conclusion);
  }
  return card;
}
function renderFindings() {
  const archive=$('finding-cards'),updates=$('update-finding-cards');archive.replaceChildren();updates.replaceChildren();
  const current=visibleFindings(true),background=visibleFindings().filter(row=>row.kind!=='current_event');
  $('current-source-readings').hidden=current.length===0;
  if(background.length){archive.append(element('p',label('background_not_new'),'meta'));for(const row of background)archive.append(findingCard(row));}
  else archive.append(element('p',label(state.scopeBusy?'loading':'no_current_findings')));
  if(!current.length)updates.append(element('p',label(state.scopeBusy?'loading':'no_current_findings')));
  for(const row of current)updates.append(findingCard(row,'facts'));
}
function renderReports() {
  refreshSynthesis();
  const parent=$('report-list');parent.replaceChildren();
  parent.append(element('h3',label('archived_evidence_ranges')));
  const grid=element('div','','wb-archive-months');parent.append(grid);
  for(const row of state.data.trend_periods.filter(row=>row.month>='2026-10').sort((a,b)=>b.month.localeCompare(a.month))) {
    const card=element('article','','wb-archive-month');card.append(element('h4',row.month),element('p',enumLabel('period_',row.source_status),'meta'),button(mapText('回看本月证据 →','Open monthly evidence →'),()=>{state.focusTarget='';state.focusMechanism='';state.focusCells=[];state.cell='';state.object='';state.method='';state.directionMode=false;state.all=true;resetEvidence();showView('updates',true);loadPeriod(row.period_id);}));grid.append(card);
  }
}
function renderChannelEntry(row) {
    const card=element('article','','card');card.append(element('h6',title(row)),element('p',textOf(row,'focus'),'reader-note'));
    card.dataset.channelId=row.channel_id;
    const memberships=state.data.channel_categories.filter(link=>link.channel_id===row.channel_id);
    const paths=memberships.map(link=>categoryPath(link.category_id)),technical=paths.filter(path=>path[0]?.family_id==='technical'),other=paths.filter(path=>path[0]?.family_id!=='technical');
    if(other.length)card.append(element('p',label('original_category')+': '+other.map(path=>path.map(title).join(' / ')).join(' · '),'meta'));
    card.append(element('p',label('reference_types')+': '+(row.channel_role?enumLabel('channel_role_',row.channel_role):label('unknown')),'meta'));
    const checks=state.data.channel_checks.filter(check=>check.channel_id===row.channel_id).sort((a,b)=>b.checked_at.localeCompare(a.checked_at)),latest=checks[0];
    card.append(element('p',label('entrypoint_check')+': '+(latest?enumLabel('entrycheck_',latest.result)+(latest.checked_at?' · '+latest.checked_at:''):label('unknown')),'wb-evidence-note'));
    card.append(element('p',label('actual_collection')+': '+enumLabel('collection_',row.scan_status),'wb-evidence-note'));
    const retrieval=currentCollectionRetrieval(row.channel_id);
    if(retrieval){card.append(element('p',label('collection_current')+': '+enumLabel('collection_result_',retrieval.status)+' · '+label('collection_received')+': '+retrieval.received_count,'reader-note'));
      card.append(element('p',textOf(retrieval,'boundary'),'meta'));if(retrieval.failure_code)field(card,'collection_failed',retrieval.failure_code);
    }else card.append(element('p',label('collection_source_not_attempted'),'meta'));
    const actions=element('div','','actions');external(actions,sourceById(row.source_id).canonical_url,label('visit_channel'));card.append(actions);
    const details=disclosure('channel:'+row.channel_id,label('channel_details'));details.append(element('p',textOf(row,'focus')));
    if(technical.length)field(details,'original_technical_category',technical.map(path=>path.map(title).join(' / ')).join(' · '));
    field(details,'source_type',enumLabel('authority_',row.source_authority));field(details,'channel_review',textOf(row,'discovery_rule'));
    field(details,'review_depth',enumLabel('channeldepth_',row.verification_scope));details.append(element('p',label('entrypoint_not_research'),'meta'));
    for(const check of checks){field(details,'entrypoint_check',enumLabel('entrycheck_',check.result)+' · '+check.checked_at);field(details,'check_scope',enumLabel('checkscope_',check.verification_scope));if(textOf(check,'reason'))field(details,'check_reason',textOf(check,'reason'));}
    const provenance=state.data.channel_provenance.filter(item=>item.channel_id===row.channel_id);
    for(const proof of provenance)if(proof.origin_note)field(details,'original_note',proof.origin_note+(proof.origin_line?' · '+proof.origin_line:''));
    if(retrieval){details.dataset.collectionRetrieval=retrieval.retrieval_id;const container=element('div');details.collectionContainer=container;renderCollectionEntries(retrieval,container);details.append(container);}
    card.append(details);
    if(details.open&&retrieval)loadCollectionEntries(retrieval.retrieval_id);
    return card;
}

function sourceEntryList(entries,parent) {
  for(const entry of entries){
    const row=entry.channel,line=element('div','','reader-note');line.dataset.sourceEntry=row.channel_id;
    const actions=element('div','','actions');external(actions,sourceById(row.source_id).canonical_url,title(row));line.append(actions);
    const details=disclosure('source-entry:'+row.channel_id,label('source_entry_details'));
    const build=()=>{if(!details.entryBuilt){details.append(renderChannelEntry(row));details.entryBuilt=true;}};
    details.addEventListener('toggle',()=>{if(details.open)build();});if(details.open)build();line.append(details);parent.append(line);
  }
}
function ensureIndustryUpdates() {
  if(state.domain!=='industry'||!state.revision||!globalThis.LRIIndustryUpdates)return;
  const revision=state.revision,epoch=state.epoch;
  if(state.industryRevision===revision&&state.industryEpoch===epoch)return;
  state.industryRevision=revision;state.industryEpoch=epoch;state.industrySnapshot=null;state.industryError='';state.industryBusy=true;
  LRIIndustryUpdates.load(revision,state.directoryData||state.data).then(snapshot=>{
    if(state.epoch!==epoch||state.revision!==revision)return;
    state.industrySnapshot=snapshot;state.industryBusy=false;if(state.domain==='industry')renderChannels();
  }).catch(error=>{
    if(state.epoch!==epoch||state.revision!==revision)return;
    state.industryError=error.message;state.industryBusy=false;if(state.domain==='industry')renderChannels();
  });
}
function renderIndustryUpdates(card,familyId) {
  const snapshot=state.industrySnapshot;
  if(!snapshot||snapshot.revision!==state.revision)return;
  const updates=LRIIndustryUpdates.forFamily(snapshot,familyId);if(!updates.length)return;
  const area=element('section','','industry-updates');
  area.append(element('h6',mapText('近期版本与能力变化','Recent releases and capability changes')));
  const sourceLink=(parent,id)=>{
    const source=snapshot.sources.find(row=>row.source_id===id);external(parent,source.canonical_url,mapText('官方原文','Official source'));
  };
  const kindText={stable:['正式版','Stable release'],candidate:['候选版','Release candidate'],project_progress:['项目进展','Project progress'],main_change:['主干变更','Main-branch change'],version_documentation:['版本配套说明','Version compatibility notes']};
  for(const update of updates){
    const block=element('article','','industry-update');block.dataset.industryUpdate=update.update_id;
    const kind=kindText[update.release_kind];
    block.append(element('p',mapText(...kind)+' · '+update.version_label,'industry-update-kind'),element('h6',title(update)),element('p',textOf(update,'summary')));
    const date=update.release_date_kind==='unknown'?mapText('发布日期未确认','Publication date unconfirmed'):mapText(update.release_date_kind==='month_only'?'项目记录月份：':'版本说明日期：',update.release_date_kind==='month_only'?'Project log month: ':'Release-note date: ')+update.release_date;
    const meta=element('p',date+(update.platform_published_date?' · '+mapText('平台发布日期：','Platform publication: ')+update.platform_published_date:'')+' · '+mapText('核对：','Reviewed: ')+update.checked_at,'meta');
    sourceLink(meta,update.source_id);block.append(meta);
    const changes=ordered(snapshot.changes.filter(row=>row.update_id===update.update_id));
    const detail=disclosure('industry-update:'+update.update_id,mapText('查看具体变化与适用条件','Changes and applicability')+' · '+changes.length);
    for(const change of changes){
      const item=element('section','','industry-change');item.dataset.industryChange=change.change_id;
      item.append(element('h6',title(change)),element('p',textOf(change,'fact')),element('p',mapText('适用条件：','Conditions: ')+textOf(change,'conditions'),'reader-note'));
      const refs=element('p','','industry-change-links');sourceLink(refs,change.source_id);
      for(const link of LRIIndustryUpdates.reviewedLinks(snapshot).filter(row=>row.change_id===change.change_id)){
        const topic=snapshot.topics.find(row=>row.compression_topic_id===link.compression_topic_id),a=element('a',title(topic)+' · '+mapText(link.relation_kind==='compression_direct'?'压缩相关':'部署配套',link.relation_kind==='compression_direct'?'Compression':'Deployment'));
        a.href='topic.html?topic='+encodeURIComponent(topic.compression_topic_id);refs.append(a);
      }
      item.append(refs);detail.append(item);
    }
    for(const [key,zh,en] of [['scope','硬件与模型','Hardware and models'],['dependencies','版本依赖','Version dependencies'],['boundary','证据边界','Evidence boundary']]){
      const p=element('p');p.append(element('strong',mapText(zh,en)+'：'),document.createTextNode(textOf(update,key)));detail.append(p);
    }
    detail.append(element('p',update.date_locator,'meta'));block.append(detail);area.append(block);
  }
  const releases=disclosure('source-releases:'+familyId,mapText('已核对版本与能力变化','Reviewed releases and capabilities')+' · '+updates.length);releases.classList.add('source-release-list');releases.append(area);card.append(releases);
}

function renderChannels() {
  for(const tab of document.querySelectorAll('.wb-domain-tabs [role=tab]')){const active=tab.dataset.domain===state.domain;tab.tabIndex=active?0:-1;tab.setAttribute('aria-selected',String(active));}
  const panel=$('channel-cards');panel.setAttribute('role','tabpanel');const activeTab=document.querySelector('.wb-domain-tabs [data-domain="'+state.domain+'"]');if(activeTab){activeTab.id='source-tab-'+state.domain;panel.setAttribute('aria-labelledby',activeTab.id);}
  if(!state.directoryReady||!Array.isArray(state.data.source_families)||!Array.isArray(state.data.channel_families))return;
  ensureIndustryUpdates();
  const parent=$('channel-cards');parent.replaceChildren();renderCollectionRun();
  if(state.domain==='industry'&&(state.industryBusy||state.industryError)){
    const status=element('p',state.industryError?mapText('版本与算子数据暂不可用：','Release/operator data unavailable: ')+state.industryError:mapText('正在读取已核对的版本与算子变化…','Loading reviewed release and operator changes…'),'meta');status.setAttribute('role','status');parent.append(status);
    if(state.industryError){const retry=element('button',mapText('重试版本数据','Retry release data'));retry.type='button';retry.addEventListener('click',()=>{state.industryRevision='';renderChannels();});parent.append(retry);}
  }
  document.querySelectorAll('[data-domain]').forEach(tab=>{const active=tab.dataset.domain===state.domain;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;});
  const searchText=row=>{
    const paths=state.data.channel_categories.filter(link=>link.channel_id===row.channel_id).flatMap(link=>categoryPath(link.category_id));
    return [row.title_zh,row.title_en,row.focus_zh,row.focus_en,sourceById(row.source_id).canonical_url,...paths.flatMap(item=>[item.title_zh,item.title_en])].join(' ');
  };
  if(state.directoryPartial&&!state.data.source_families.some(row=>row.ui_group===state.domain)){
    parent.append(element('p',mapText('正在读取该类别的完整信源目录…','Loading this source category…'),'reader-note'));return;
  }
  const catalog=LRIGroupedSources.catalog(state.data,{domain:state.domain,important:state.channelImportant,query:state.channelQuery,category:state.channelCategory,searchText});
  const rows=catalog.rows,filteredEntrypoints=rows.reduce((total,group)=>total+group.entries.length,0);state.channelTotal=rows.length;state.channelOffset=rows.length?Math.min(state.channelOffset,Math.floor((rows.length-1)/20)*20):0;
  $('channel-query').value=state.channelQuery;$('channel-priority').value=state.channelImportant?'important':'all';
  const filter=$('channel-category');filter.replaceChildren();const option=element('option',label('source_category_all'));option.value='';filter.append(option);
  for(const category of catalog.categories){const item=element('option',enumLabel('source_category_'+state.domain+'_',category.key)+' · '+category.count);item.value=category.key;filter.append(item);}filter.value=state.channelCategory;
  const industry=state.domain==='industry';
  $('channel-prev').hidden=industry;$('channel-next').hidden=industry;
  $('channel-prev').disabled=!state.revision||state.channelOffset===0;$('channel-next').disabled=!state.revision||state.channelOffset+20>=rows.length;
  $('channel-status').textContent=(rows.length?state.channelOffset+1:0)+'–'+Math.min(state.channelOffset+20,rows.length)+' / '+rows.length+' '+label('source_subjects')+' · '+enumLabel('domain_',state.domain)+' · '+label('channel_important_total')+': '+catalog.core.length+' · '+label('source_entrypoints')+': '+state.data.channels.filter(row=>row.ui_group===state.domain).length+' · '+label('source_registry')+': '+catalog.totals.subjects+' / '+catalog.totals.entrypoints;
  if(state.readerMode==='sources')$('channel-status').textContent=enumLabel('domain_',state.domain)+' · '+rows.length+' '+label('source_subjects')+' · '+filteredEntrypoints+' '+label('source_entrypoints')+' · '+mapText('按类别读取，采集状态按需展开','Loaded by category; expand collection status on demand');
  const overview=$('source-subject-overview');overview.textContent=label(industry?'industry_scope_help':'source_grouping_help');
  const appendFamilies=(target,pageRows,headingLevel=4)=>{
  for(const category of catalog.categories){
    const selected=pageRows.filter(g=>g.family.category_key===category.key);if(!selected.length)continue;
    const section=element('section');section.dataset.sourceCategory=category.key;section.append(element('h'+headingLevel,enumLabel('source_category_'+state.domain+'_',category.key)));
    for(const group of selected){
      const row=group.family,card=element('article','','card');card.dataset.sourceFamily=row.family_id;
      const heading=element('h'+(headingLevel+1),'','source-family-title'),entry=group.entries.find(item=>item.entry_kind==='homepage')||group.entries[0],link=element('a',title(row));
      link.href=safeUrl(sourceById(entry.channel.source_id).canonical_url);heading.append(link);card.append(heading,element('p',textOf(row,'summary').replace(/[。；;]+\s*[；;]+/g,'；'),'reader-note'));
      const statuses=group.entries.map(e=>currentCollectionRetrieval(e.channel_id)),withContent=statuses.filter(r=>r?.status==='success'&&r.received_count>0).length,failed=statuses.filter(r=>r?.status==='failed').length,empty=statuses.filter(r=>r?.status==='success'&&r.received_count===0).length,unattempted=statuses.filter(r=>!r||['skipped','not_attempted'].includes(r.status)).length;
      const status=element('p',state.directoryPartial?mapText('查看采集状态','View collection status'):failed?mapText('部分入口采集失败','Some entries failed'):withContent?mapText('已有采集内容','Collected content available'):empty?mapText('本次未发现条目','No entries found in this run'):mapText('尚未采集','Not collected yet'),'source-family-status');
      const tooltip=state.directoryPartial?mapText('信源与原始链接已核对；展开后读取采集记录。','Source identity and original links checked; expand to read collection records.'):mapText('入口数 ','Entry points ')+group.entries.length+' · '+mapText('有内容 ','With content ')+withContent+' · '+mapText('失败 ','Failed ')+failed+' · '+mapText('无条目 ','No items ')+empty+' · '+mapText('未尝试 ','Not attempted ')+unattempted;status.title=tooltip;
      const reviewedUpdates=state.industrySnapshot?.revision===state.revision?LRIIndustryUpdates.forFamily(state.industrySnapshot,row.family_id):[];
      if(reviewedUpdates.length)status.textContent=mapText('已核对版本与能力变化','Release/operator changes reviewed')+' · '+reviewedUpdates.length+mapText(' 组',' groups');
      const more=disclosure('source-status-'+row.family_id,mapText('采集状态详情','Collection status details'));more.classList.add('source-family-health');more.append(element('p',tooltip,'meta'));card.append(status,more);
      renderIndustryUpdates(card,row.family_id);
      const alternateLinks=element('p','','source-family-links'),seenUrls=new Set([link.href]);
      for(const alternate of group.entries){
        const url=safeUrl(sourceById(alternate.channel.source_id).canonical_url);if(seenUrls.has(url))continue;seenUrls.add(url);
        const alternateLink=element('a',enumLabel('source_entry_kind_',alternate.entry_kind)+' · '+title(alternate.channel));alternateLink.href=url;alternateLink.dataset.sourceEntry=alternate.channel_id;alternateLinks.append(alternateLink);
      }
      if(alternateLinks.childElementCount){const entries=disclosure('source-links:'+row.family_id,mapText('其他关注入口','Additional source entries')+' · '+alternateLinks.childElementCount);entries.classList.add('source-family-entries');entries.append(alternateLinks);card.append(entries);}section.append(card);
    }target.append(section);
  }
  };
  if(industry){
    const sections=LRIGroupedSources.industrySections(catalog,state.industryOffsets,8),jump=element('div','','actions');
    for(const part of sections){
      state.industryOffsets[part.id]=part.offset;
      const name=label('industry_'+part.id+'_title'),section=element('section'),heading=element('h4',name+' · '+part.total+' '+label('source_subjects'));
      section.id='industry-sources-'+part.id;section.dataset.sourceEcosystem=part.id;
      section.append(heading,element('p',label('industry_'+part.id+'_help'),'reader-note'));
      const anchor=element('a',name+' · '+part.total,'btn');anchor.href='#'+section.id;jump.append(anchor);
      if(part.rows.length)appendFamilies(section,part.rows,5);
      else section.append(element('p',label('industry_filter_empty')));
      if(part.total>8){
        const controls=element('div','','actions'),range=element('p',(part.offset+1)+'–'+Math.min(part.offset+8,part.total)+' / '+part.total,'meta');
        range.setAttribute('role','status');section.append(range);
        for(const direction of ['prev','next']){
          const button=element('button',label(direction==='prev'?'previous':'next'),'btn');button.type='button';
          button.dataset.ecosystemPage=part.id+'-'+direction;button.setAttribute('aria-label',name+' · '+button.textContent);
          button.disabled=direction==='prev'?!part.hasPrev:!part.hasNext;
          button.addEventListener('click',()=>{state.industryOffsets[part.id]=part.offset+(direction==='prev'?-8:8);renderChannels();const updated=$('industry-sources-'+part.id);updated.scrollIntoView({block:'start'});updated.querySelector('h4').tabIndex=-1;updated.querySelector('h4').focus({preventScroll:true});});
          controls.append(button);
        }section.append(controls);
      }parent.append(section);
    }
    parent.prepend(jump);
    $('channel-status').textContent=sections.map(part=>label('industry_'+part.id+'_title')+': '+part.total+' '+label('source_subjects')).join(' · ')+' · '+label('channel_important_total')+': '+catalog.core.length+' · '+label('source_entrypoints')+': '+filteredEntrypoints;
  }else{
    if(!rows.length)parent.append(element('p',label(state.channelQuery?'search_empty':'channels_empty')));
    appendFamilies(parent,rows.slice(state.channelOffset,state.channelOffset+20));
  }
}

function categoryPath(id) {
  const path=[],seen=new Set();
  while(id){must(!seen.has(id),'Category cycle');seen.add(id);const row=state.data.source_categories.find(item=>item.category_id===id);must(Boolean(row),'Missing original category');path.unshift(row);id=row.parent_category_id;}
  return path;
}
function sourceById(id) { return state.data.primarySources.find(row=>row.source_id===id); }
function visibleLineages() {
  if(!state.cell&&!state.object)return state.data.lineages;
  const cells=new Set(state.data.cells.filter(row=>(!state.cell||row.cell_id===state.cell)&&(!state.object||row.object_id===state.object)).map(row=>row.cell_id));
  const ids=new Set(state.data.lineage_cells.filter(row=>cells.has(row.cell_id)).map(row=>row.lineage_id));
  return state.data.lineages.filter(row=>ids.has(row.lineage_id));
}
function renderLineages() {
  const parent=$('lineage-cards'); parent.replaceChildren();
  const rows=visibleLineages();
  if(!rows.length)parent.append(element('p',label('lineage_gap')));
  for(const row of rows) {
    const card=element('article','','card'); card.append(element('h4',title(row)));
    field(card,'lineage_summary',textOf(row,'summary')); field(card,'boundary',textOf(row,'boundary'));
    card.append(element('p',enumLabel('status_',row.status),'meta'));
    const detail=disclosure('lineage:'+row.lineage_id,label('lineage_details'));
    field(detail,'lineage_question',textOf(row,'question')); field(detail,'ascend',textOf(row,'ascend')); field(detail,'lineage_checked_at',row.checked_at);
    if(state.locale==='en')detail.append(element('p',label('mechanism_source_language'),'reader-note'));
    const nodes=ordered(state.data.lineage_nodes.filter(node=>node.lineage_id===row.lineage_id)),list=element('ol');
    for(const node of nodes) {
      const source=sourceById(node.source_id),technique=state.data.techniques.find(item=>item.technique_id===node.technique_id),li=element('li');
      li.append(element('h4',source.title)); field(li,'source_identifier',source.external_id); field(li,'first_submission_on',node.first_submitted_on);
      field(li,'observed_version',node.observed_version); field(li,'verified_at',node.checked_at);
      if(technique.mechanism.trim()!==textOf(node,'change').trim())field(li,'mechanism',technique.mechanism); field(li,'mechanism_change',textOf(node,'change')); field(li,'boundary',textOf(node,'boundary'));
      const actions=element('div','','actions'); external(actions,source.canonical_url,label('original_source')); li.append(actions); list.append(li);
    }detail.append(list,element('h4',label('lineage_relations')),element('p',label('lineage_relation_boundary'),'meta'));
    const relations=element('ul');
    for(const relation of state.data.lineage_relations.filter(item=>item.lineage_id===row.lineage_id)) {
      const from=state.data.lineage_nodes.find(node=>node.node_id===relation.from_node_id),to=state.data.lineage_nodes.find(node=>node.node_id===relation.to_node_id),li=element('li');
      li.append(element('p',sourceById(from.source_id).title+' → '+sourceById(to.source_id).title));
      field(li,'relation_kind',enumLabel('relation_',relation.relation_kind)); li.append(element('p',textOf(relation,'relation_note')));
      external(li,sourceById(relation.source_id).canonical_url,label('relation_source')); relations.append(li);
    }
    if(!relations.children.length)relations.append(element('li',label('no_lineage_relation')));
    detail.append(relations); card.append(detail); parent.append(card);
  }
}
function renderSourceScans() {
  const parent=$('source-scan-cards'); parent.replaceChildren();
  if(!state.data.source_scans.length)parent.append(element('p',label('source_scan_gap')));
  for(const scan of state.data.source_scans) {
    const card=element('article','','card'); card.append(element('h4',textOf(scan,'label')));
    card.append(element('p',enumLabel('scan_',scan.scan_status),'meta'));
    card.append(element('p',['received_count','title_candidate_count','selected_count','adjacent_count','excluded_count','pending_count','title_not_matched_count'].map(key=>label(key)+': '+scan[key]).join(' · ')));
    card.append(element('p',textOf(scan,'boundary'),'reader-note'));
    const detail=disclosure('scan:'+scan.scan_id,label('source_screening_details'));
    field(detail,'retrieved_at',scan.retrieved_at); field(detail,'listing_date',scan.listing_date); field(detail,'requested_limit',scan.requested_limit);
    field(detail,'scan_origin',enumLabel('origin_',scan.origin_kind)); field(detail,'title_rule',textOf(scan,'title_rule'));
    external(detail,sourceById(scan.channel_source_id).canonical_url,label('original_source'));
    const screenings=ordered(state.data.source_screenings.filter(row=>row.scan_id===scan.scan_id)),list=element('ul');
    for(const row of screenings) {
      const source=sourceById(row.source_id),li=element('li'); li.append(element('strong',source.title));
      field(li,'screening_status',enumLabel('screening_',row.screening_status)); li.append(element('p',textOf(row,'reason')));
      field(li,'screened_at',row.checked_at); external(li,source.canonical_url,label('original_source')); list.append(li);
    }
    if(!screenings.length)list.append(element('li',label('no_title_candidates')));
    detail.append(list); card.append(detail); parent.append(card);
  }
}
function validateEnrichment(data) {
  const map=(name,key)=>{ const rows=data[name],ids=new Map(rows.map(row=>[row[key],row])); must(ids.size===rows.length&&rows.every(row=>typeof row[key]==='string'&&row[key]),'Duplicate or missing enrichment identity'); return ids; };
  const lineages=map('lineages','lineage_id'),nodes=map('lineage_nodes','node_id'),relations=map('lineage_relations','relation_id'),links=map('lineage_cells','link_id'),scans=map('source_scans','scan_id'),screenings=map('source_screenings','screening_id');
  const techniques=new Set(data.techniques.map(row=>row.technique_id)),cells=new Set(data.cells.map(row=>row.cell_id));
  for(const node of nodes.values())must(lineages.has(node.lineage_id)&&techniques.has(node.technique_id)&&typeof node.source_id==='string'&&node.source_id,'Invalid lineage node association');
  for(const relation of relations.values())must(lineages.has(relation.lineage_id)&&relation.from_node_id!==relation.to_node_id&&nodes.get(relation.from_node_id)?.lineage_id===relation.lineage_id&&nodes.get(relation.to_node_id)?.lineage_id===relation.lineage_id&&['extends','generalizes','addresses_limitation','parallel','analyst_comparison'].includes(relation.relation_kind)&&typeof relation.source_id==='string'&&relation.source_id,'Invalid lineage relation');
  for(const link of links.values())must(lineages.has(link.lineage_id)&&cells.has(link.cell_id),'Invalid lineage cell association');
  must(new Set(data.lineage_cells.map(row=>row.lineage_id+'__'+row.cell_id)).size===data.lineage_cells.length,'Duplicate lineage cell placement');
  for(const lineage of lineages.values())must(data.lineage_nodes.some(row=>row.lineage_id===lineage.lineage_id)&&data.lineage_cells.some(row=>row.lineage_id===lineage.lineage_id),'Lineage missing nodes or canonical placement');
  for(const row of screenings.values())must(scans.has(row.scan_id)&&typeof row.source_id==='string'&&row.source_id&&['in_scope','adjacent','excluded','pending'].includes(row.screening_status),'Invalid source screening association');
  for(const scan of scans.values()) {
    const countKeys=['requested_limit','received_count','title_candidate_count','selected_count','adjacent_count','excluded_count','pending_count','title_not_matched_count'];
    must(typeof scan.channel_source_id==='string'&&scan.channel_source_id&&countKeys.every(key=>Number.isSafeInteger(scan[key])&&scan[key]>=0),'Invalid source scan counts');
    must(scan.received_count<=scan.requested_limit&&scan.title_candidate_count+scan.title_not_matched_count===scan.received_count&&scan.selected_count+scan.adjacent_count+scan.excluded_count+scan.pending_count===scan.title_candidate_count,'Inconsistent source scan scope');
    const rows=data.source_screenings.filter(row=>row.scan_id===scan.scan_id);
    must(rows.length===scan.title_candidate_count&&new Set(rows.map(row=>row.source_id)).size===rows.length,'Incomplete or duplicate screened candidates');
    for(const [status,key] of [['in_scope','selected_count'],['adjacent','adjacent_count'],['excluded','excluded_count'],['pending','pending_count']])must(rows.filter(row=>row.screening_status===status).length===scan[key],'Source screening count mismatch');
  }
}
function validateResearch(data) {
  const index=(name,key)=>{const rows=data[name],map=new Map(rows.map(row=>[row[key],row]));must(map.size===rows.length&&rows.every(row=>typeof row[key]==='string'&&row[key]),'Invalid research identity');return map;};
  const findings=index('findings','finding_id'),channels=index('channels','channel_id'),categories=index('source_categories','category_id'),proofs=index('channel_provenance','provenance_id');
  for(const [name,key] of [['finding_evidence','evidence_link_id'],['finding_cells','link_id'],['finding_techniques','link_id'],['finding_keywords','keyword_id'],['finding_scopes','link_id'],['channel_categories','membership_id'],['channel_checks','check_id']])index(name,key);
  const cells=new Set(data.cells.map(row=>row.cell_id)),techniques=new Set(data.techniques.map(row=>row.technique_id));
  for(const row of findings.values()){
    must(['current_event','foundational_review','implementation_reference'].includes(row.kind)&&typeof row.recent_event_eligible==='boolean','Invalid finding kind');
    must(['summary','implication','background','innovation','results'].every(key=>['zh','en'].every(locale=>typeof row[key+'_'+locale]==='string'&&row[key+'_'+locale])),'Missing finding reading fields');
    must(row.kind==='current_event'?row.recent_event_eligible&&/^\d{4}-\d{2}-\d{2}$/.test(row.change_date):!row.recent_event_eligible,'Historical knowledge cannot become a new event');
    must(data.finding_evidence.some(link=>link.finding_id===row.finding_id)&&data.finding_cells.some(link=>link.finding_id===row.finding_id),'Finding missing evidence or canonical placement');
    if(row.kind==='current_event')must(data.finding_scopes.some(link=>link.finding_id===row.finding_id),'Current event missing explicit evidence scope');
  }
  for(const row of data.finding_evidence)must(findings.has(row.finding_id)&&typeof row.source_id==='string'&&row.source_id&&typeof row.local_measurement==='boolean','Invalid finding evidence');
  for(const row of data.finding_cells)must(findings.has(row.finding_id)&&cells.has(row.cell_id),'Invalid finding cell');
  for(const row of data.finding_techniques)must(findings.has(row.finding_id)&&techniques.has(row.technique_id),'Invalid finding technique');
  for(const row of data.finding_keywords)must(findings.has(row.finding_id)&&row.keyword_zh&&row.keyword_en,'Invalid finding keyword');
  for(const row of data.finding_scopes)must(findings.get(row.finding_id)?.kind==='current_event'&&typeof row.scope_id==='string'&&row.scope_id&&typeof row.evidence_id==='string'&&row.evidence_id,'Invalid current finding scope');
  for(const row of channels.values())must(['academic','industry','hotspot'].includes(row.ui_group)&&typeof row.source_id==='string'&&row.source_id,'Invalid research channel');
  for(const row of categories.values()){
    const seen=new Set([row.category_id]);let id=row.parent_category_id;
    while(id){must(categories.has(id)&&!seen.has(id),'Invalid original category ancestry');seen.add(id);id=categories.get(id).parent_category_id;}
  }
  for(const row of proofs.values())must(channels.has(row.channel_id),'Unknown channel provenance');
  for(const row of data.channel_categories)must(channels.has(row.channel_id)&&categories.has(row.category_id)&&proofs.get(row.provenance_id)?.channel_id===row.channel_id,'Invalid channel classification provenance');
  for(const row of data.channel_checks){
    must(channels.get(row.channel_id)?.source_id===row.source_id&&typeof row.checked_at==='string'&&['checked','identity_only','pending'].includes(row.result),'Invalid channel entrypoint check');
    if(row.verification_scope==='not_checked')must(row.result==='pending'&&row.retrieval_method==='not_attempted','Unattempted source check cannot imply verification');
    if(row.verification_scope==='retrieval_attempt_failed')must(row.result==='pending'&&row.retrieval_method!=='not_attempted','Failed source check must record an attempted method');
  }
  for(const row of channels.values())must(data.channel_categories.some(link=>link.channel_id===row.channel_id),'Channel missing original classification');
}
function refreshSynthesis() {
 if(topicPage()||!state.scopeReady||!state.revision||!['updates','home','reports'].includes(state.view))return;
 const revision=state.revision,epoch=state.epoch;
 globalThis.LRICompressionSynthesis?.refresh({revision,period:state.period,scope:state.scope,locale:state.locale,strings:state.packs[state.locale].strings,topics:state.data.compression_topics,topicId:state.focusTarget?compressionTopicId():'',view:state.view,loadIndustry:async()=>{
 const reader=await LRIIndustryUpdates.loadReader(revision);must(state.revision===revision&&state.epoch===epoch,'Industry context changed');return reader;
 }});
}
function renderAscend() { refreshSynthesis(); }
function visibleTechniques() {
  if(!state.cell&&!state.object&&!state.all)return [];
  const cells=new Set(state.data.cells.filter(row=>(!state.cell||row.cell_id===state.cell)&&(!state.object||row.object_id===state.object)).map(row=>row.cell_id));
  const ids=new Set(state.data.placements.filter(row=>cells.has(row.cell_id)&&row.stage!=='training').map(row=>row.technique_id));
  return state.data.techniques.filter(row=>ids.has(row.technique_id)&&row.inference_scope!=='training_only');
}
function techniquesForCell(cell) {
  if(state.focusTarget&&cell.cell_id===state.cell){const targetIds=scientificTechniqueIds(state.focusTarget),methodIds=scientificTechniqueIds(state.focusMechanism);return ordered(state.data.techniques.filter(row=>targetIds.has(row.technique_id)&&methodIds.has(row.technique_id)&&row.inference_scope!=='training_only'));}
  const ids=new Set(state.data.placements.filter(row=>row.cell_id===cell.cell_id&&row.stage!=='training'&&row.applicability!=='training_only').map(row=>row.technique_id));
  return ordered(state.data.techniques.filter(row=>ids.has(row.technique_id)&&row.inference_scope!=='training_only'));
}
function appendMapReferences(parent,cell) {
  const rows=techniquesForCell(cell);
  if(!rows.length){parent.append(element('p',label('map_reference_gap'),'meta'));return;}
  const list=element('ul');list.className='wb-map-references';
  for(const row of rows.slice(0,3)) {
    const li=element('li');li.dataset.mapTechnique=row.technique_id;
    li.append(element('strong',title(row)),element('p',row.mechanism));
    const refs=state.data.source_refs.filter(ref=>ref.technique_id===row.technique_id);
    for(const ref of refs){const source=sourceById(ref.source_id);if(source)external(li,source.canonical_url,label('original_source'));}
    if(!refs.length)li.append(element('span',label('candidate'),'meta'));
    list.append(li);
  }
  parent.append(list);
  if(rows.length>3)parent.append(element('p',label('map_more_references')+': '+(rows.length-3),'meta'));
}
const mapText=(zh,en)=>state.locale==='en'?en:zh;
function directionLink(cell,text,cls='') {
  const link=element('a',text,cls);link.href='#direction-'+cell.cell_id;link.dataset.directionCell=cell.cell_id;return link;
}
function linkedLineages(cell) {
  if(state.focusTarget){const targetTerms=scientificDescendants(state.focusTarget),targetIds=new Set(state.data.map_assignments.filter(row=>row.subject_kind==='lineage'&&targetTerms.has(row.term_id)).map(row=>row.subject_id)),methodIds=new Set(state.data.map_assignments.filter(row=>row.subject_kind==='lineage'&&row.term_id===state.focusMechanism).map(row=>row.subject_id));return ordered(state.data.lineages.filter(row=>targetIds.has(row.lineage_id)&&methodIds.has(row.lineage_id)));}
  const ids=new Set(state.data.lineage_cells.filter(row=>row.cell_id===cell.cell_id).map(row=>row.lineage_id));
  return ordered(state.data.lineages.filter(row=>ids.has(row.lineage_id))).sort((a,b)=>state.data.lineage_cells.filter(row=>row.lineage_id===a.lineage_id).length-state.data.lineage_cells.filter(row=>row.lineage_id===b.lineage_id).length);
}
function openDirection(id,updateHash=true,preserveFocus=false) {
  if(!preserveFocus){state.focusTarget='';state.focusMechanism='';state.focusCells=[];}
  const cell=state.data.cells.find(row=>row.cell_id===id);
  if(!cell){$('direction-detail').hidden=false;$('direction-detail').replaceChildren(element('p',mapText('未找到这个技术方向，请返回技术地图选择。','Unknown direction. Please select one from the map.')));return;}
  state.directionMode=true;state.cell=id;state.object=cell.object_id;state.method=cell.method_id;state.all=false;
  resetDetails();resetEvidence();renderSelectors();renderMap();renderSelection();controls(true);showView('topics');
  if(updateHash)history.pushState(null,'','#direction-'+id);
  const detail=$('direction-detail');detail.setAttribute('tabindex','-1');detail.focus({preventScroll:true});detail.scrollIntoView({block:'start'});renderEvidence();
}
function renderDirectionDetail() {
  if(topicPage())restoreTopicNodes();
  const parent=$('direction-detail');parent.replaceChildren();parent.hidden=!state.directionMode;
  $('scientific-map').hidden=state.directionMode;
  $('representative-routes').hidden=state.directionMode;
  $('knowledge').hidden=state.directionMode;
  if(!state.directionMode)return;
  const cell=currentCell();if(!cell)return;
  if(state.focusTarget&&state.data.compression_topics?.some(row=>row.compression_topic_id===state.focusTarget+'-'+state.focusMechanism)){renderCompressionTopic(parent,cell);return;}
  const legacyObject=state.data.objects.find(row=>row.object_id===cell.object_id),legacyMethod=state.data.methods.find(row=>row.method_id===cell.method_id),object=state.focusTarget?{...mapTerm(state.focusTarget),description:textOf(mapTerm(state.focusTarget),'description')}:legacyObject,method=state.focusMechanism?{...mapTerm(state.focusMechanism),description:textOf(mapTerm(state.focusMechanism),'description')}:legacyMethod,rows=techniquesForCell(cell),routes=linkedLineages(cell);
  const back=element('a',mapText('← 返回技术地图','← Back to the technology map'),'direction-back');back.href='#view-topics';parent.append(back);
  const hero=element('header','','direction-hero'),badges=element('div','','direction-badges');
  badges.append(element('span',mapText('推理压缩 · 技术专题','Inference compression · Research topic')),element('span',state.focusTarget?mapText('按文献分类组织','Literature-based classification'):cell.cell_id),element('span',rows.length?mapText('已有技术资料','Technical references available'):mapText('研究入口 · 待积累','Research entry · Building evidence')));
  hero.append(badges,element('h2',scientificFocusTitle()||cellTitle(cell)),element('p',routes.length?textOf(routes[0],'question'):mapText('在'+title(object)+'上采用'+title(method)+'，需要减少什么成本，又必须保留什么能力？','What cost can '+title(method)+' reduce in '+title(object)+', and what capability must be retained?'),'direction-lead'));
  const sourceIds=new Set(state.data.source_refs.filter(ref=>rows.some(row=>row.technique_id===ref.technique_id)).map(ref=>ref.source_id));
  const stats=element('div','','direction-stats');
  for(const [value,caption] of [[rows.length,mapText('登记技术','Registered techniques')],[sourceIds.size,mapText('关联原文','Linked sources')],[routes.length,mapText('代表路线','Reviewed routes')]]){const box=element('div');box.append(element('strong',value),element('span',caption));stats.append(box);}hero.append(stats);parent.append(hero);
  parent.append(element('p',mapText("专题持续积累相关研究，不受月份筛选影响。文中区分技术原理、论文报告结果和昇腾实测，以便判断证据的适用范围。","The topic accumulates research independently of the month filter. Principles, author-reported results and Ascend measurements are distinguished so readers can assess applicability."),'direction-note'));
  const nav=element('nav','','direction-nav');nav.setAttribute('aria-label',mapText('专题阅读顺序','Topic reading order'));
  for(const [id,name] of [['scope',mapText('01 研究问题','01 Research question')],['routes',mapText('02 技术路线','02 Technical routes')],['papers',mapText('03 原文证据','03 Primary evidence')],['boundary',mapText('04 适用边界','04 Boundaries')],['implications',mapText('05 昇腾启示','05 Ascend implications')]]){const link=button(name,()=>{const section=$('direction-'+id);section.setAttribute('tabindex','-1');section.focus({preventScroll:true});section.scrollIntoView({block:'start'});});nav.append(link);}parent.append(nav);
  const section=(id,name)=>{const node=element('section','','direction-section');node.id='direction-'+id;node.append(element('h3',name));parent.append(node);return node;};
  const scope=section('scope',mapText('01 · 研究问题与压缩位置','01 · Research question and compression target'));
  const definitions=element('div','','direction-definition-grid');
  for(const [name,description] of [[title(object),object.description],[title(method),method.description]]){const box=element('article');box.append(element('h4',name),element('p',description));definitions.append(box);}scope.append(definitions);
  const flow=element('div','','direction-flow');for(const name of [title(object),title(method),mapText('质量与执行成本一起判断','Assess quality and execution cost together')])flow.append(element('span',name));scope.append(flow);
  const routeSection=section('routes',mapText('02 · 技术路线：如何解决问题','02 · Technical routes: how the problem is addressed'));
  if(!routes.length)routeSection.append(element('p',mapText("该专题的路线对比仍在整理。目前可先阅读压缩对象与方法的定义，具体方案将随原文审阅逐步补充。","A reviewed comparison is still being prepared. Target and method definitions are available; specific approaches will be added as primary sources are reviewed.")));
  for(const route of routes){const article=element('article','','direction-route');article.append(element('h4',title(route)),element('p',textOf(route,'question'),'direction-question'),element('p',textOf(route,'summary')),element('p',mapText('机制核对日期：','Mechanism review: ')+route.checked_at,'meta'));routeSection.append(article);}
  const papers=section('papers',mapText('03 · 代表技术与原文证据','03 · Representative techniques and primary evidence'));
  papers.append(element('p',mapText("以下介绍代表方法及其原始资料。比较效果时需结合模型、精度、硬件、基线与测试条件；最新论文摘要见“本期动态”。","Representative methods and their primary sources follow. Compare results alongside model, precision, hardware, baseline and test conditions; recent paper summaries appear in Current updates."),'meta'));
  if(!rows.length)papers.append(element('div',mapText("该专题暂未收录代表技术，相关候选资料可在“本期动态”中查看。","No representative techniques have been collected for this topic yet. Related candidates are available in Current updates."),'direction-gap'));
  for(const row of rows){const card=element('article','','direction-paper');card.dataset.directionTechnique=row.technique_id;card.append(element('h4',title(row)),element('p',row.mechanism));
    const refRows=state.data.source_refs.filter(ref=>ref.technique_id===row.technique_id),actions=element('div','','actions');
    for(const ref of refRows){const source=sourceById(ref.source_id);if(source){external(actions,source.canonical_url,source.title);card.append(element('p',mapText('核对范围：','Reviewed scope: ')+(ref.checked_scope==='mechanism_only'?mapText('机制原文核对','Primary mechanism review'):enumLabel('depth_',ref.checked_scope))+' · '+ref.checked_at,'meta'));}}
    if(!refRows.length&&row.primary_url)external(actions,row.primary_url,mapText('原始来源 · 待核对','Original source · Pending review'));
    card.append(actions);const more=element('details');more.append(element('summary',mapText('适用条件与限制','Conditions and limitations')),element('p',row.boundary));card.append(more);papers.append(card);}
  const boundary=section('boundary',mapText('04 · 适用边界与证据缺口','04 · Applicability and evidence gaps'));
  if(routes.length)for(const route of routes)boundary.append(element('p',textOf(route,'boundary')));
  else boundary.append(element('p',mapText("对象与方法的交叉组合用于组织研究。具体方案是否成熟，还需结合训练需求、推理实现和任务质量判断。","Target–method combinations organize the research. Maturity depends on training requirements, inference implementation and task quality.")));
  boundary.append(element('p',mapText("资料数量反映本库的收录范围。稀疏、剪枝等标签可能对应同一方案，比较收益时应按实际实现去重。","Counts reflect this library's coverage. Tags such as sparsity and pruning may describe the same approach; avoid counting its gains twice."),'meta'));
  const implications=section('implications',mapText('05 · 昇腾启示与持续关注','05 · Ascend implications and continuing research'));
  if(routes.length)for(const route of routes)implications.append(element('p',textOf(route,'ascend')));
  else implications.append(element('p',mapText("建议从业务瓶颈判断该方案的价值，并核对目标运行栈能否直接使用压缩后的数据。该方案在昇腾上的实际收益仍待验证。","Assess the approach against workload bottlenecks, then check whether the target runtime can use the compressed data directly. Practical Ascend gains remain unverified.")));
  const actions=element('div','','actions');const updates=button(mapText('查看该方向的本期论文与总结 →','Read current papers and summaries →'),()=>{showView('updates',true);loadEvidence(0);$('selection-title').focus({preventScroll:true});},true);updates.dataset.directionUpdates=cell.cell_id;actions.append(updates);implications.append(actions);
  const neighbors=element('details');neighbors.append(element('summary',mapText('继续浏览同一对象的其他方法','Explore other methods for this object')));const links=element('div','','direction-neighbors');if(state.focusTarget){for(const term of ordered(state.data.map_terms.filter(row=>['mechanism','construction'].includes(row.facet_id)&&row.term_id!==state.focusMechanism)))if([...scientificTechniqueIds(state.focusTarget)].some(id=>scientificTechniqueIds(term.term_id).has(id)))links.append(scientificLink(state.focusTarget,term.term_id,title(term)));}else for(const other of state.data.cells.filter(row=>row.object_id===cell.object_id&&row.cell_id!==cell.cell_id))links.append(directionLink(other,cellTitle(other)));neighbors.append(links);parent.append(neighbors);
}

function compressionTopicId(){return state.focusTarget?state.focusTarget+'-'+state.focusMechanism:'';}
function topicSectionRow(kind){return state.data.compression_topic_sections.find(row=>row.compression_topic_id===compressionTopicId()&&row.section_kind===kind);}
function topicEventsFor(id){return (state.topicScopeLinks||[]).filter(row=>row.compression_topic_id===id);}
function validateCompressionTopics(data){
 const terms=new Map(data.map_terms.map(row=>[row.term_id,row])),ids=new Set();
 for(const row of data.compression_topics){must(!ids.has(row.compression_topic_id)&&row.compression_topic_id===row.target_term_id+'-'+row.method_term_id&&terms.get(row.target_term_id)?.facet_id==='target'&&['mechanism','construction'].includes(terms.get(row.method_term_id)?.facet_id)&&row.route==='topic.html?topic='+row.compression_topic_id,'Invalid compression topic');ids.add(row.compression_topic_id);}
 must(data.compression_topics.filter(row=>row.catalog_kind==='matrix').length===12,'Incomplete literature topic matrix');
 const concepts=new Set();for(const row of data.compression_topic_concepts){must(row.business_id==='cloud-core'&&row.topic_id==='cloud_core'&&row.concept_id===row.compression_topic_id&&ids.has(row.compression_topic_id)&&!concepts.has(row.concept_id)&&row.summary_zh?.trim()&&row.summary_en?.trim()&&row.claim_kind==='editorial_definition','Invalid topic concept');safeUrl(row.source_url);concepts.add(row.concept_id);}
 must(concepts.size===12&&data.compression_topics.filter(row=>row.catalog_kind==='matrix').every(row=>concepts.has(row.compression_topic_id)),'Incomplete topic conceptual definitions');
 const sections=new Set();for(const row of data.compression_topic_sections){must(ids.has(row.compression_topic_id)&&!sections.has(row.section_id)&&row.body_zh&&['problem','mechanism','comparison','boundary','implication','watch'].includes(row.section_kind),'Broken topic section');sections.add(row.section_id);safeUrl(row.evidence_url);}
 for(const id of ids)must(data.compression_topic_sections.filter(row=>row.compression_topic_id===id).length===6,'Incomplete topic content');
}
const dossierRequests=new Map(),dossierErrors=new Map();
function researchDossier(){return LRITopicDossier.get(compressionTopicId(),state.revision);}
function dossierReadApi(groups,id,revision){
 return {
  loadRowsByKeys:(...args)=>LRITableGit.loadRowsByKeys(...args),
  loadTablePage:async(table,options)=>{
   const records=groups[table.replace(/^ic_/,'')];
   must(Array.isArray(records)&&options.filterField==='compression_topic_id'&&options.filterValue===id&&options.expectedRevision===revision,'Invalid dossier batch page');
   const offset=options.offset||0,limit=Math.min(options.limit||100,100),items=records.slice(offset,offset+limit),truncated=offset+items.length<records.length;
   return {revision,records:items,page:{total:records.length,offset,truncated,nextOffset:truncated?offset+items.length:null}};
  }
 };
}
async function loadResearchDossier(id,revision){
 const cached=LRITopicDossier.get(id,revision);if(cached)return cached;
 if(typeof globalThis.LRICloudSemanticRead!=='function')return LRITopicDossier.ensure(id,revision,LRITableGit);
 const batch=await LRICloudSemanticRead('dossier',revision,{topicId:id});validateEvidenceRevision(batch,revision);
 for(const rows of Object.values(batch.groups))assertBusiness(rows);
 return LRITopicDossier.ensure(id,revision,dossierReadApi(batch.groups,id,revision));
}
function ensureResearchDossier(){
 const id=compressionTopicId(),revision=state.revision,epoch=state.epoch,key=revision+'__'+id;
 if(!revision||researchDossier()||dossierRequests.has(key)||dossierErrors.has(key))return;
 const request=loadResearchDossier(id,revision).then(()=>{
  if(state.epoch===epoch&&state.revision===revision&&compressionTopicId()===id&&state.directionMode)renderDirectionDetail();
 }).catch(error=>{dossierErrors.set(key,error.message);if(state.epoch===epoch&&state.revision===revision&&compressionTopicId()===id&&state.directionMode)renderDirectionDetail();}).finally(()=>dossierRequests.delete(key));
 dossierRequests.set(key,request);
}

function renderQuantizationExample(parent,kind){
 const figure=element('figure','','research-mechanism-diagram');figure.dataset.quantizationIllustration=kind;
 const names={rounding:['舍入与裁剪：两个不同的误差来源','Rounding and clipping: distinct error sources'],groups:['量化粒度：哪些权重共享尺度？','Granularity: which weights share a scale?'],output:['权重误差如何被输入放大','How inputs amplify weight error']};
 const label=mapText(...names[kind]);figure.append(element('h4',label));
 if(kind==='rounding'){
  const scene=element('lri-motion-scene');scene.setAttribute('controls','');scene.setAttribute('lang',state.locale);
  scene.setAttribute('aria-label',mapText('量化六步演示：舍入与裁剪','Six-step quantization: rounding and clipping'));
  const base=new URL('assets/quantization-principle.'+(state.locale==='en'?'en':'zh'),location.href);
  scene.setAttribute('src',base.href+'.svg?v=3');
  const fallback=element('img');fallback.src=base.href+'.static.svg?v=3';fallback.alt=scene.getAttribute('aria-label');const picture=element('picture'),mobile=element('source');mobile.media='(max-width:640px)';mobile.srcset=base.href+'.mobile.static.svg?v=3';picture.append(mobile,fallback);scene.append(picture);
  const jump=element('label',mapText('逐步查看：','Step through: ')),select=element('select');select.setAttribute('aria-label',mapText('选择量化步骤','Select a quantization step'));
  const hint=element('option',mapText('选择一步（暂停定位）','Choose a step (pause and seek)'));hint.value='';select.append(hint);
  const steps=[['原始权重','Original weight'],['除以尺度','Divide by scale'],['取最近整数','Round to nearest'],['裁剪并保存整数码','Clip and store the code'],['反量化','Reconstruction'],['误差','Error']];
  steps.forEach(([zh,en],i)=>{const option=element('option',String(i+1)+' · '+mapText(zh,en));option.value=String(i);select.append(option);});
  select.addEventListener('change',()=>{if(select.value==='')return;const seek=()=>scene.seek(Number(select.value)*4000+1000);if(scene.duration)seek();else scene.addEventListener('scene-ready',seek,{once:true});});jump.append(select);
  figure.append(scene,jump,element('figcaption',mapText('数轴随反量化步骤移动：A为局部放大的舍入示例，B为裁剪示例。实线连接原值与还原值，均为教学数值。','The red outline follows six steps while all values remain visible. A illustrates rounding and B clipping. Pause, replay or seek through the timeline.')));
  parent.append(figure);
  import(new URL('../../assets/lri-motion-scene.js?v=weight-class-v6',location.href).href).catch(()=>{scene.replaceWith(picture);});
  return;
 }

 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');
 svg.setAttribute('viewBox','0 0 440 '+(kind==='groups'?390:290));svg.setAttribute('role','img');svg.setAttribute('aria-label',label);svg.setAttribute('width','100%');
 const add=(tag,attrs,text)=>{const n=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,String(v));if(text!==undefined)n.textContent=text;svg.append(n);return n;};
 const txt=(x,y,text,color='#24364b',size=18)=>add('text',{x,y,fill:color,'font-size':size,'font-family':'Arial,sans-serif'},text);
 const rect=(x,y,w,h,fill)=>add('rect',{x,y,width:w,height:h,rx:8,fill,stroke:'#d7e0eb'});
 const line=(x,y,x2,y2,color='#64748b')=>add('line',{x1:x,y1:y,x2,y2,stroke:color,'stroke-width':2});
 if(kind==='rounding'){
  txt(20,25,'s = 0.1 · z = 0 · q ∈ [−8, 7]');
  txt(20,58,mapText('局部放大：只展示非负区间','Zoom: non-negative interval only'), '#64748b',16);
  const xp=v=>30+v*380;
  line(xp(0),115,xp(1),115);
  for(let q=0;q<=7;q++){const x=xp(q*.1);line(x,108,x,122);txt(x-9,146,(q*.1).toFixed(1),'#64748b',16);}
  const original=.26,restored=Math.round(original/.1)*.1;
  line(xp(original),82,xp(original),106,'#b71c1c');
  add('circle',{cx:xp(original),cy:82,r:5,fill:'#b71c1c'});
  add('circle',{cx:xp(restored),cy:115,r:6,fill:'#087e8b'});
  txt(20,182,'0.26 → q = 3 → 0.30 · e = +0.04');
  line(xp(.96),115,xp(.7),115,'#b71c1c');
  add('circle',{cx:xp(.96),cy:115,r:5,fill:'#b71c1c'});
  txt(20,216,'0.96 → q = 7 → 0.70 · e = −0.26');
  txt(20,252,mapText('红：原值 / 裁剪   蓝绿：重建值','Red: original/clipping · Teal: reconstructed'), '#64748b',16);
 }else if(kind==='groups'){
  const colors=['#d6edf0','#e9e0f3','#ffe4d8','#e4edd5','#dbe6fa','#f4dce8','#f3edcc','#dcece8'];
  for(let mode=0;mode<3;mode++){
   const y=20+mode*120;
   txt(20,y+20,['per-tensor','per-channel','per-group'][mode]);
   for(let row=0;row<2;row++)for(let col=0;col<8;col++){
    const color=mode===0?0:mode===1?row:row*4+Math.floor(col/2);
    rect(20+col*49,y+35+row*28,43,23,colors[color]);
   }
   txt(20,y+108,mapText(...[
    ['整张量一套参数','One parameter set for the tensor'],
    ['每个输出通道一套参数','One set per output channel'],
    ['示意：每行连续2个权重一组','Example: blocks of 2 within each row']
   ][mode]),'#64748b',16);
  }
 }else{
  rect(20,20,400,95,'#f3f7fb');
  txt(35,50,mapText('原始计算','Original computation'));
  txt(35,88,'w × x = 0.26 × 10 = 2.6', '#24364b',22);
  rect(20,130,400,95,'#edf7f6');
  txt(35,160,mapText('量化重建后计算','After reconstruction'));
  txt(35,198,'ŵ × x = 0.30 × 10 = 3.0','#087e8b',22);
  txt(20,264,'Δy = e × x = 0.04 × 10 = 0.4');
 }
 figure.append(svg,element('figcaption',mapText('教学示意；由公式计算，不是模型实测。','Illustrative arithmetic, not a model measurement.')));parent.append(figure);
}
function renderQuantizationExplanation(parent,text){
 const parts=text.split(/\n+/).filter(x=>x.trim()),definition=parts.find(x=>/^(核心概念|Core idea)[：:]/.test(x));
 if(definition)parent.append(element('p',definition.replace(/^[^：:]+[：:]\s*/,''),'reader-note'));
 const groups=[];let current=null;
 for(const part of parts){if(/^0\d ·/.test(part)){current={title:part.replace(/^0\d ·\s*/,''),parts:[]};groups.push(current);}else if(current)current.parts.push(part);}
 if(groups.length!==5){renderQuantizationExplanationLegacy(parent,text);return;}
 const names=[['量化入门','Quantization essentials'],['计算公式','Equations'],['误差影响','Output error'],['量化粒度','Granularity'],['执行开销','Execution cost']];
 const chapters=groups.map((g,i)=>({title:mapText(...names[i]),frames:g.parts.filter(p=>!(/^(补充说明|Additional note|量化公式|反量化公式|原始输出|量化输出|输出误差|Quantization formula|Dequantization formula|Quantization|Dequantization|Original output|Quantized output|Output error)[：:]/.test(p))).map(part=>{const n=element('div');appendResearchText(n,part);return n;}),syncScene:true}));

 const dossier=researchDossier(),workedCard=dossier?.cards.find(row=>row.card_id==='parameters-precision__lesson_worked_example');
 const captions=workedCard?textOf(workedCard,'body').split(/\n+/).filter(x=>x.trim()):[];
 if(captions.length!==6){renderQuantizationExplanationLegacy(parent,text);return;}
 const example={title:mapText('整组示例','Group example'),syncScene:true,frames:captions.map(part=>{const n=element('div');appendResearchText(n,part);return n;})};
 chapters.splice(2,0,example);
 const makeVisual=(key,label)=>{
  const host=element('div'),scene=element('lri-motion-scene');scene.setAttribute('lang',state.locale);scene.setAttribute('aria-label',label);
  const stem=new URL('assets/quantization-class-'+key+'.'+(state.locale==='en'?'en':'zh'),location.href).href;
  scene.dataset.lessonDesktopSrc=stem+'.svg?v=17';scene.dataset.lessonMobileSrc=stem+'.mobile.svg?v=17';
  scene.setAttribute('src',matchMedia('(max-width:640px)').matches?scene.dataset.lessonMobileSrc:scene.dataset.lessonDesktopSrc);
  const fallback=element('picture'),source=element('source'),img=element('img');source.media='(max-width:640px)';source.srcset=stem+'.mobile.static.svg?v=17';img.src=stem+'.static.svg?v=17';img.alt=label;fallback.append(source,img);scene.append(fallback);host.append(scene);return host;
 };
 chapters[0].frameVisuals=['purpose','precision','concept','tradeoff'].map((key,i)=>makeVisual(key,chapters[0].frames[i]?.textContent||chapters[0].title));
 const keys=['formula','worked','error','groups','execution'];
 chapters.slice(1).forEach((c,i)=>{c.title=String(i+1)+' · '+c.title;c.visual=makeVisual(keys[i],c.title);const note=dossier?.cards.find(row=>row.card_id==='parameters-precision__lesson_guidance_'+(i+1));if(note)c.takeaway={title:title(note),body:textOf(note,'body')};});
 import(new URL('../../assets/lri-motion-scene.js?v=weight-class-v6',location.href).href);
 const intro=element('lri-quantization-lesson'),advanced=element('lri-quantization-lesson'),introData={chapters:[chapters[0]],lang:state.locale,mode:'intro'},advancedData={chapters:chapters.slice(1),lang:state.locale,mode:'advanced'};
 intro.lesson=introData;parent.append(intro);
 const more=element('section');more.append(element('h4',mapText('进阶计算：公式、误差与执行','Further study: equations, errors and execution')));
 more.append(element('p',mapText("下面通过公式与示例，说明量化编码、误差和执行过程。","The equations and examples below explain quantized encoding, error and execution."),'meta'));
 advanced.lesson=advancedData;more.append(advanced);parent.append(more);
 const notes=groups.flatMap(g=>g.parts.filter(p=>/^(补充说明|Additional note)[：:]/.test(p)));
 if(notes.length){const aside=element('aside','','reader-note');appendResearchText(aside,notes.join('\n'));more.append(aside);}
 import(new URL('../../assets/lri-quantization-lesson.js?v=15',location.href).href).then(()=>{for(const [node,data] of [[intro,introData],[advanced,advancedData]]){delete node.lesson;node.lesson=data;}}).catch(()=>{for(const [node,data] of [[intro,introData],[advanced,advancedData]])node.replaceWith(...data.chapters.flatMap(c=>[element('h4',c.title),...(c.frameVisuals||[c.visual]),...c.frames]));});
}

function renderQuantizationExplanationLegacy(parent,text){
 for(const part of text.split(/\n+/).filter(x=>x.trim())){
  if(/^0\d ·/.test(part)){parent.append(element('h4',part));continue;}
  const m=/^([^：:]{1,42})[：:]\s*(.*)$/.exec(part);
  if(m&&/公式$|^(Quantization|Dequantization|原始输出|量化输出|输出误差|Original output|Quantized output|Output error)$/.test(m[1])){
   parent.append(element('p',m[1],'meta'));
   const box=element('div','','reader-note'),ns='http://www.w3.org/1998/Math/MathML',math=document.createElementNS(ns,'math');math.setAttribute('display','block');math.setAttribute('mathsize','24px');math.setAttribute('aria-label',m[2]);
   const group=document.createElementNS(ns,'mrow');const leaf=(tag,text)=>{const n=document.createElementNS(ns,tag);n.textContent=text;return n;};
   for(const token of m[2].split(/(q_min|q_max|w \/ s)/)){
    if(token==='q_min'||token==='q_max'){const sub=document.createElementNS(ns,'msub');sub.append(leaf('mi','q'),leaf('mtext',token.slice(2)));group.append(sub);}
    else if(token==='w / s'){const frac=document.createElementNS(ns,'mfrac');frac.append(leaf('mi','w'),leaf('mi','s'));group.append(frac);}
    else if(token)group.append(leaf('mtext',token));
   }
   math.append(group);box.append(math);parent.append(box);continue;
  }
  appendResearchText(parent,part);
  if(/^(示例条件|Illustrative conditions)[：:]/.test(part))renderQuantizationExample(parent,'rounding');
  if(/^(量化粒度|Granularity)[：:]/.test(part))renderQuantizationExample(parent,'groups');
  if(/^(解释|Interpretation)[：:]/.test(part))renderQuantizationExample(parent,'output');
 }
}

function renderDossierCards(parent,kind,onlyIds=null){
 const dossier=researchDossier();if(!dossier)return;
 const rows=dossier.cards.filter(row=>row.section_kind===kind&&(!onlyIds||onlyIds.includes(row.card_id))),grid=element('div','',compressionTopicId()==='parameters-precision'?'wb-reading-list':'topic-dossier-grid'+(kind==='mechanism'?' topic-mechanism-flow':''));
 for(const row of rows){
  const card=element('article','','topic-dossier-card');card.dataset.researchCard=row.card_id;card.dataset.claimKind=row.claim_kind;
  card.append(element('p',row.claim_kind==='author_result'?mapText("论文实验结果","Author-reported results"):row.claim_kind==='research_analysis'?mapText("研究分析 · 待验证","Research analysis · Awaiting validation"):mapText("技术原理 · 原文依据","Technical principles · Primary sources"),'topic-dossier-type'));
  card.append(element(topicPage()?'h3':'h4',title(row)));if(row.card_id==='parameters-precision__dossier_1'){card.id='direction-quantization-principles';renderQuantizationExplanation(card,textOf(row,'body'));}else appendResearchText(card,textOf(row,'body'));
  const references=dossier.refs.filter(ref=>ref.card_id===row.card_id),links=element('div','','topic-dossier-citations');
  for(const ref of references){const source=dossier.sources.find(item=>item.source_id===ref.source_id),shortName=source.title.split(':')[0].slice(0,48),sourceUrl=new URL(source.canonical_url),paperId=sourceUrl.hostname==='arxiv.org'?sourceUrl.pathname.split('/').filter(Boolean).at(-1):'',link=element('a',shortName+(paperId?' ['+paperId+']':''));link.href=safeUrl(source.canonical_url);link.target='_blank';link.rel='noopener noreferrer';link.title=source.title+' · '+textOf(ref,'locator')+' · '+(ref.observed_version==='current_abstract'?mapText('摘要记录','Abstract record'):ref.observed_version)+' · '+ref.checked_at;links.append(link);}
  card.append(links);
  const proof=researchBlock('dossier-'+row.card_id,mapText("参考章节与图表","Referenced sections and figures"));
  for(const ref of references)proof.append(element('p',(ref.review_depth==='section_review'?mapText('指定章节核对','Selected-section review'):mapText('摘要审阅','Abstract review'))+' · '+textOf(ref,'locator')+' · '+(ref.observed_version==='current_abstract'?mapText('摘要记录','Abstract record'):ref.observed_version)+' · '+ref.checked_at,'meta'));
  card.append(proof);grid.append(card);
 }if(rows.length)parent.append(grid);
}

function researchBlock(key,label,cls=''){
 const node=element('section','',cls||'research-route-block');node.dataset.researchBlock=key;
 node.append(element('h4',label));return node;
}
function appendResearchText(parent,text,cls='topic-dossier-body'){
 for(const part of text.split(/\n+/).filter(x=>x.trim())){
  const p=element('p','',cls),match=/^([^：:。；，;,]{1,42})(?:：(?!\d)|:\s+)\s*(.*)$/.exec(part);
  if(match)p.append(element('strong',match[1]+mapText('：',': ')),document.createTextNode(match[2]));else p.textContent=part;
  parent.append(p);
 }
}
function renderTopicOverview(parent,topic,dossier){
 const root=element('section','','research-overview');root.id='research-overview';root.dataset.sectionLabel=mapText('完整专题洞察','Complete topic insight');
 if(!dossier){root.append(element('p',mapText('正在读取本专题的背景、路线与证据…','Loading the topic background, routes and evidence…'),'meta'));parent.append(root);return;}
 for(const [key,zh,en] of [
  ['problem','研究问题与挑战','Problem and challenges'],['industry','产业实现与条件','Industry implementation and conditions'],
  ['mechanism','学术原理与路线','Academic principles and routes'],['facts','代表成果与证据','Representative results and evidence'],
  ['analysis','路线比较与边界','Route comparison and boundaries'],['implications','研究结论与行动','Research conclusions and next actions']
 ]){
  const node=element('section','','research-overview-section');node.id='research-overview-'+key;node.dataset.sectionLabel=mapText(zh,en);node.dataset.sectionLevel='3';node.dataset.readingLayer=key==='analysis'?'analysis':key==='implications'?'conclusion':'facts';
  const quantLabels={problem:['背景、目标与挑战','Background, goals and challenges'],industry:['产业实现与适配','Industry implementation and adaptation'],mechanism:['量化原理与路线','Quantization principles and routes'],facts:['代表成果与证据','Representative results and evidence'],analysis:['路线比较与边界','Route comparison and boundaries'],implications:['研究判断与行动','Research judgment and actions']};
  const label=topic.compression_topic_id==='parameters-precision'?quantLabels[key]:[zh,en];
  node.append(element('h2',String(root.children.length+1).padStart(2,'0')+' · '+mapText(...label)));root.append(node);
 }
 parent.append(root);
}
function composeResearchOverview(parent){
 if(researchView()!=='overview')return;
 const groups={problem:['scope','value','challenges'],industry:['industry'],mechanism:['mechanism','routes'],facts:['papers','sources'],analysis:['comparison','boundary'],implications:['implications','watch']};
 for(const [key,sections] of Object.entries(groups)){
  const host=parent.querySelector('#research-overview-'+key);if(!host)continue;
  for(const name of sections){
   const node=parent.querySelector('#direction-'+name);if(!node)continue;
   const heading=node.querySelector('h2,h3');
   if(heading)heading.replaceWith(element('h3',heading.textContent.replace(/^\d+\s*·\s*/,'')));
   node.dataset.sectionLevel='4';node.hidden=false;host.append(node);
  }
 }
}
function renderTopicReportOutline(parent,sections){
 const nav=element('nav','','topic-report-outline');nav.setAttribute('aria-label',mapText('专题阅读顺序','Topic reading order'));
 const select=keys=>sections.filter(row=>keys.includes(row[0]));
 const groups=[
  [mapText("研究背景、目标与挑战","Background, goals and challenges"),select(['scope','value','challenges'])],
  [mapText("技术原理与研究路线","Principles and research approaches"),select(['mechanism','routes'])],
  [mapText("代表成果与实验依据","Representative results and evidence"),select(['papers','sources'])],
  [mapText("方案比较与研究建议","Comparison and research suggestions"),select(['comparison','boundary','implications','watch'])]
 ];
 groups.forEach(([name,items],index)=>{
  const group=element('div','','topic-report-outline-group');group.append(element('p',String(index+1).padStart(2,'0')+' · '+name));
  for(const [key,zh,en] of items){const link=element('a',mapText(zh,en));link.href='#direction-'+key;group.append(link);}nav.append(group);
 });parent.append(nav);
}
function renderTopicTargetDiagram(parent){
 const figure=element('figure','','topic-target-diagram');figure.setAttribute('aria-label',mapText("研究对象、方法与评估","Research target, method and evaluation"));
 const grid=element('div','','topic-target-grid');
 for(const [index,term] of [mapTerm(state.focusTarget),mapTerm(state.focusMechanism)].entries()){
  const node=element('div','','topic-target-node');node.append(element('p',index===0?mapText('压缩什么','What is compressed'):mapText('如何压缩','How it is compressed'),'topic-target-label'),element(topicPage()?'h3':'h4',title(term)),element('p',textOf(term,'description')));
  external(node,term.source_url,mapText('分类依据 →','Taxonomy source →'));grid.append(node);
 }
 const assessment=element('div','','topic-target-node topic-target-assessment');assessment.append(element('p',mapText('如何判断收益','How to assess gains'),'topic-target-label'),element(topicPage()?'h3':'h4',mapText('质量 × 实际成本','Quality × Actual cost')),element('p',mapText("评估应同时关注任务质量、数据存储和实际执行成本，不能仅凭位宽、稀疏率或秩判断收益。","Assess task quality, storage and execution cost together; bit width, sparsity or rank alone cannot establish practical gains.")));grid.append(assessment);
 figure.append(grid,element('figcaption',mapText("图中依次列出压缩对象、研究方法和评估要点。","The diagram shows the compression target, approach and evaluation criteria.")));parent.append(figure);
}
function renderTopicCatalogue(parent,currentId){
 const matrix=ordered(state.data.compression_topics.filter(row=>row.catalog_kind==='matrix'));
 const more=researchBlock('topic-report-catalogue',mapText('切换研究专题','Switch research topic')+' · '+matrix.length);
 more.classList.add('topic-report-catalogue');
 for(const target of [...new Set(matrix.map(row=>row.target_term_id))]){
  const group=element('div','','topic-catalogue-group');group.append(element('strong',title(mapTerm(target))));
  for(const row of matrix.filter(item=>item.target_term_id===target)){
   const link=scientificLink(row.target_term_id,row.method_term_id,title(mapTerm(row.method_term_id)));
   if(row.compression_topic_id===currentId)link.setAttribute('aria-current','page');group.append(link);
  }more.append(group);
 }parent.append(more);
}


function researchView(){
 const value=new URLSearchParams(location.search).get('view')||'overview';
 return ['overview','background','mechanism','industry','literature','comparison','implications'].includes(value)?value:'overview';
}
function researchHref(view,key=''){
 const url=new URL('topic.html',location.href);url.searchParams.set('topic',compressionTopicId());
 if(state.period)url.searchParams.set('month',state.period);if(state.scope)url.searchParams.set('scope',state.scope);
 url.searchParams.set('view',view);url.searchParams.set('v','58');if(key)url.hash='direction-'+key;
 return url.pathname+url.search+url.hash;
}
function researchNav(parent){
 const nav=element('nav','','research-reader-tabs');nav.setAttribute('aria-label',mapText('专题阅读顺序','Topic reading order'));
 const complete=researchView()==='overview';
 const items=complete?[['problem','研究问题','Problem'],['industry','产业实现','Industry'],['mechanism','学术路线','Academia'],['facts','原文事实','Evidence'],['analysis','路线比较','Comparison'],['implications','结论行动','Conclusions/actions']]:[['overview','完整洞察','Complete insight'],['background','背景挑战','Background'],['industry','产业实现','Industry'],['mechanism','学术路线','Academia'],['literature','代表文献','Literature'],['comparison','路线比较','Comparison'],['implications','结论行动','Conclusions/actions']];
 for(const [view,zh,en] of items){
  const a=element('a',mapText(zh,en));a.href=complete?'#research-overview-'+view:researchHref(view);
  if(!complete){a.dataset.compressionResearchView=view;if(view===researchView())a.setAttribute('aria-current','page');}nav.append(a);
 }parent.append(nav);
 document.body.dataset.lriReaderNavigation='.research-reader-tabs';
 document.body.dataset.lriReaderNavigationLabel=mapText('当前专题 · 阅读顺序','Current topic · Reading order');
}
function researchSectionView(key){
 return key==='industry'?'industry':['scope','value','challenges'].includes(key)?'background':['mechanism','routes'].includes(key)?'mechanism':['papers','sources'].includes(key)?'literature':['comparison','boundary'].includes(key)?'comparison':'implications';
}
function applyResearchView(parent){
 const view=researchView();parent.dataset.researchView=view;
 const overview=parent.querySelector(':scope>.research-overview');if(overview)overview.hidden=view!=='overview';
 for(const section of parent.querySelectorAll(':scope>.direction-section')){const key=section.id.replace('direction-','');section.hidden=new URLSearchParams(location.search).has('route')?key!=='routes':view==='overview'||researchSectionView(key)!==view;}
 let order=0;for(const section of parent.querySelectorAll(':scope>.direction-section'))if(!section.hidden){const h=section.querySelector('h2');if(h)h.textContent=String(++order).padStart(2,'0')+' · '+h.textContent.replace(/^\d+\s*·\s*/,'');}
 for(const a of parent.querySelectorAll('.topic-report-outline a,.topic-report-actions a')){
  const key=a.getAttribute('href')?.match(/#direction-([a-z]+)/)?.[1];
  if(key){if(view==='overview'){a.href='#direction-'+key;delete a.dataset.compressionResearchView;}else{const target=researchSectionView(key);a.href=researchHref(target,key);a.dataset.compressionResearchView=target;}}
 }
}
function renderMechanismDiagram(parent,{compact=false}={}){
 const dossier=researchDossier();if(!dossier?.steps?.length)return;
 const steps=dossier.steps.slice().sort((a,b)=>a.position-b.position),gap=steps.some(x=>x.claim_status==='research_question');
 const figure=element('figure','','research-mechanism-diagram');figure.dataset.mechanismTopic=compressionTopicId();
 const heading=element('h3',gap?mapText("待补充的原理依据","Mechanism evidence still needed"):mapText('从原始表示到实际执行','From original representation to execution'));figure.append(heading);
 const visual=LRICompressionVisuals.flow(steps.map(step=>textOf(step,'label')),{locale:state.locale,title:heading.textContent,description:gap?mapText('研究问题示意，尚待直接论文证据。','Research-question schematic requiring direct evidence.'):mapText("原理图依据所引文献整理，各路线需分别评估。","Mechanisms are summarized from cited literature; evaluate each approach separately.")});
 if(gap)for(const rect of visual.querySelectorAll('rect'))rect.setAttribute('stroke-dasharray','5 4');
 figure.append(visual);
 const notes=element('ol','','research-mechanism-notes');
 for(const step of steps){
  const li=element('li');li.append(element('strong',textOf(step,'label')),element('p',textOf(step,'body')));
  const links=element('div','','topic-dossier-citations');for(const ref of dossier.refs.filter(r=>r.card_id===step.supporting_card_id)){const source=dossier.sources.find(s=>s.source_id===ref.source_id);external(links,source.canonical_url,source.title.split(':')[0]+' ↗');}li.append(links);notes.append(li);
 }
 figure.append(notes);
 figure.append(element('figcaption',gap?mapText("虚线部分为待研究环节，尚缺直接文献支持。","Dashed stages indicate open questions without direct supporting literature."):mapText("示意图依据下方文献说明技术过程；不同论文的方案需分别评估，组合使用还需验证。","The diagram illustrates processes from the references below. Evaluate each paper's approach separately; combining approaches requires validation.")));parent.append(figure);
}


function renderResearchFraming(parent,field){
 const dossier=researchDossier(),frame=dossier?.frames?.[0];if(!frame)return;
 const box=element('article','','research-framing');box.dataset.researchFraming=field;
 if(compressionTopicId()==='parameters-precision')appendResearchText(box,textOf(frame,field));else box.append(element('p',textOf(frame,field)));
 const sourceNote=element('p',frame.claim_status==='research_question'?mapText('待建立直接证据的研究问题','Research question requiring direct evidence'):mapText("基于所引文献分析，实际收益取决于具体实现与测试条件。","Analysis based on the cited literature; practical gains depend on implementation and test conditions."),'meta');if(field==='why'&&compressionTopicId()!=='parameters-precision')box.append(sourceNote);
 const links=element('div','','topic-dossier-citations');for(const ref of dossier.refs.filter(r=>r.card_id===frame.supporting_card_id)){const source=dossier.sources.find(s=>s.source_id===ref.source_id);external(links,source.canonical_url,source.title.split(':')[0]+' ↗');}if(compressionTopicId()==='parameters-precision'&&field==='why'&&box.children.length>=2)box.insertBefore(links,box.children[2]||null);else box.append(links);parent.append(box);
}
function renderResearchRoutes(parent){
 const dossier=researchDossier();if(!dossier?.routes?.length)return;
 const selected=new URLSearchParams(location.search).get('route'),routes=dossier.routes.slice().sort((a,b)=>a.position-b.position);
 if(selected&&!routes.some(r=>r.route_id===selected)){parent.append(element('p',mapText('该路线不属于当前专题，请返回路线总览。','This route is outside the current topic; return to the route overview.'),'direction-gap'));return;}
 if(selected){const back=element('a',mapText('← 查看本专题全部技术路线','← All routes in this topic'),'direction-back');back.href=researchHref('mechanism','routes');back.dataset.compressionResearchView='mechanism';parent.append(back);}
 const grid=element('div','',compressionTopicId()==='parameters-precision'?'wb-reading-list':'research-route-grid');
 for(const route of routes.filter(r=>!selected||r.route_id===selected)){
  const card=element('article','','research-route-reader');card.dataset.researchRoute=route.route_id;
  const status=element('p',route.claim_status==='research_question'?mapText('研究路径 · 尚缺直接代表作','Research path · Direct evidence missing'):mapText('文献路线 · 原文机制','Literature route · Primary mechanism'),'topic-dossier-type');card.append(status,element('h3',title(route)));
  const block=(zh,en,field)=>{const box=element('div','','research-route-block');box.append(element('h4',mapText(zh,en)),element('p',textOf(route,field)));card.append(box);};
  block('解决什么问题','Problem addressed','problem');block('核心思路','Core principle','principle');
  const how=element('div','','research-route-block');how.append(element('h4',mapText('如何实现','Implementation steps')));const steps=element('ol','','research-route-steps');for(let i=1;i<=3;i++)steps.append(element('li',textOf(route,'step_'+i)));how.append(steps);card.append(how);
  block('代价与适用条件','Tradeoffs and conditions','tradeoff');
  const source=dossier.sources.find(s=>s.source_id===route.source_id),links=element('div','','topic-dossier-citations');external(links,source.canonical_url,(route.claim_status==='research_question'?mapText('相邻证据：','Adjacent evidence: '):mapText('原文：','Primary source: '))+source.title.split(':')[0]+' ↗');card.append(links);
  const ref=dossier.refs.find(r=>r.card_id===route.supporting_card_id&&r.source_id===route.source_id);const proof=researchBlock('research-route-proof-'+route.route_id,mapText('证据与审阅范围','Evidence and review scope'));proof.append(element('p',textOf(ref,'locator')+' · '+(ref.review_depth==='section_review'?mapText('章节核对','Section review'):mapText('摘要核对','Abstract review'))+' · '+ref.checked_at,'meta'));card.append(proof);
  if(!selected){const url=new URL(researchHref('mechanism','routes'),location.origin);url.searchParams.set('route',route.route_id);const detail=element('a',mapText('单独阅读此路线 →','Read this route →'),'research-route-open');detail.href=url.pathname+url.search+url.hash;detail.dataset.compressionResearchView='mechanism';card.append(detail);}grid.append(card);
 }parent.append(grid);
}

const routeEvidenceReaders=new Map(),routeEvidencePending=new Map(),routeEvidenceErrors=new Map();
function routeEvidenceKey(){return state.revision+'__'+compressionTopicId();}
function ensureRouteEvidence(){
 const dossier=researchDossier(),key=routeEvidenceKey(),epoch=state.epoch;
 if(researchView()!=='comparison'||!dossier||routeEvidenceReaders.has(key)||routeEvidencePending.has(key)||routeEvidenceErrors.has(key))return;
 const pending=LRIRouteEvidence.load(dossier,LRITableGit).then(snapshot=>{
  if(epoch!==state.epoch||key!==routeEvidenceKey())return;
  routeEvidenceReaders.set(key,snapshot);while(routeEvidenceReaders.size>12)routeEvidenceReaders.delete(routeEvidenceReaders.keys().next().value);
  if(researchView()==='comparison')renderDirectionDetail();
 }).catch(error=>{if(epoch===state.epoch&&key===routeEvidenceKey()){routeEvidenceErrors.set(key,error.message);if(researchView()==='comparison')renderDirectionDetail();}}).finally(()=>{if(routeEvidencePending.get(key)===pending)routeEvidencePending.delete(key);});
 routeEvidencePending.set(key,pending);
}
function renderRouteEvidence(parent){
 if(researchView()!=='comparison')return;
 ensureRouteEvidence();const key=routeEvidenceKey(),snapshot=routeEvidenceReaders.get(key),error=routeEvidenceErrors.get(key);
 const root=element('section','','research-overview-section');root.id='route-evidence-comparison';root.dataset.sectionLabel=mapText('原文证据与路线取舍','Primary evidence and route decisions');
 if(!snapshot){
  root.append(element('p',error?mapText('原文比较暂不可用：','Primary comparison unavailable: ')+error:mapText('正在读取本专题的原文比较…','Loading this topic’s primary comparison…'),'meta'));
  if(error)root.append(button(mapText('重试原文比较','Retry primary comparison'),()=>{routeEvidenceErrors.delete(key);renderDirectionDetail();}));
  parent.append(root);return;
 }
 if(!snapshot.rows.length)return;
 root.dataset.routeEvidenceCount=String(snapshot.rows.length);root.dataset.readingLayer='facts';
 root.append(element('h3',mapText("01 · 技术路线与方法差异","01 · Approaches and methodological differences")));
 const wrap=element('div','','table-wrap'),table=element('table','','topic-comparison-table'),head=element('thead'),tr=element('tr');
 for(const text of [mapText('论文路线','Paper route'),mapText('权重如何表示','Weight representation'),mapText('离线准备与训练预算','Preparation and training budget'),mapText('运行时付出什么','Runtime cost')]){const th=element('th',text);th.scope='col';tr.append(th);}head.append(tr);table.append(head);
 const body=element('tbody');
 for(const row of snapshot.rows){const tr=element('tr'),th=element('th');th.scope='row';const a=element('a',textOf(row,'label'));a.href='#route-evidence-'+row.assessment_id;th.append(a);tr.append(th);for(const field of ['representation','preparation','runtime'])tr.append(element('td',textOf(row,field)));body.append(tr);}table.append(body);wrap.append(table);root.append(wrap);
 root.append(element('h3',mapText("02 · 实验条件与原文结果","02 · Test conditions and reported results")));
 const dossier=researchDossier();
 for(const row of snapshot.rows){
  const card=element('article','','research-route-reader');card.id='route-evidence-'+row.assessment_id;card.dataset.routeEvidence=row.assessment_id;card.dataset.claimKind='author_result';
  const source=dossier.sources.find(s=>s.source_id===row.source_id);
  card.append(element('h4',textOf(row,'label')),element('p',source.title,'meta'));
  const facts=element('dl','','research-route-brief');for(const [field,zh,en] of [['conditions','实验条件','Conditions'],['result','作者结果','Author result'],['boundary','可比较范围','Comparison boundary']])facts.append(element('dt',mapText(zh,en)),element('dd',textOf(row,field)));card.append(facts);
  const links=element('div','','topic-dossier-citations');external(links,row.paper_url+'#'+row.result_locator,mapText('直达原文结果表 ↗','Original results table ↗'));card.append(links);
  const figureDetail=researchBlock('route-primary-figure-'+row.assessment_id,mapText('查看原论文方法图与图解','Original method figure and explanation'));figureDetail.dataset.primaryFigure=row.route_id;
  const figure=element('figure','','diagram'),img=element('img');img.alt=textOf(row,'figure_caption');img.loading='lazy';img.decoding='async';img.referrerPolicy='no-referrer';
  img.src=row.figure_url; // Browser-native lazy loading; the figure remains directly readable.
  img.addEventListener('error',()=>{img.hidden=true;figure.append(element('p',mapText('原图暂未加载，可用下方链接查看原文。','The figure is unavailable; use the primary-source link below.'),'meta'));},{once:true});
  figure.append(img,element('figcaption',textOf(row,'figure_caption')));figureDetail.append(figure);external(figureDetail,row.paper_url+'#'+row.figure_locator,mapText('直达原论文图 ↗','Original figure in the paper ↗'));card.append(figureDetail,element('p',mapText('正文与图表核对 · ','Sections and figures reviewed · ')+row.observed_version+' · '+row.reviewed_at,'meta'));root.append(card);
 }
 const decisions=element('section','','research-overview-section');decisions.dataset.readingLayer='analysis';decisions.append(element('h3',mapText("03 · 昇腾适配与研究建议","03 · Ascend adaptation and research suggestions")));
 decisions.append(element('p',mapText("以下建议结合目标业务选择可复现的方法。GPU 实验提供参考，昇腾收益需在目标设备上确认。","The suggestions below identify methods to reproduce for the target workload. GPU results provide context; Ascend gains require target-device measurements."),'reader-note'));
 for(const row of snapshot.rows){const card=element('article','','research-overview-card');card.dataset.claimKind='research_analysis';card.append(element('h4',textOf(row,'label')),element('p',textOf(row,'decision')));const probe=researchBlock('route-probe-'+row.assessment_id,mapText("建议验证的技术问题","Technical questions to validate"));probe.append(element('p',textOf(row,'probe')));card.append(probe);decisions.append(card);}const supplement=researchBlock('route-evidence-supplement',mapText("其他路线与比较条件","Other approaches and comparison conditions"));root.append(supplement);parent.append(root);return {supplement,decisions};
}

const topicIndustryReaders=new Map(),topicIndustryPending=new Map(),topicIndustryErrors=new Map();
function ensureTopicIndustryResearch(){
 const revision=state.revision,epoch=state.epoch;
 if(!['industry','overview'].includes(researchView())||!revision||topicIndustryReaders.has(revision)||topicIndustryPending.has(revision)||topicIndustryErrors.has(revision))return;
 const pending=(async()=>{
  const reader=await LRIIndustryUpdates.loadReader(revision);
  if(epoch!==state.epoch||revision!==state.revision)return;
  topicIndustryReaders.set(revision,reader);
  while(topicIndustryReaders.size>2)topicIndustryReaders.delete(topicIndustryReaders.keys().next().value);
  if(['industry','overview'].includes(researchView()))renderDirectionDetail();
 })().catch(error=>{if(epoch===state.epoch&&revision===state.revision){topicIndustryErrors.set(revision,error.message);if(['industry','overview'].includes(researchView()))renderDirectionDetail();}}).finally(()=>{if(topicIndustryPending.get(revision)===pending)topicIndustryPending.delete(revision);});
 topicIndustryPending.set(revision,pending);
}
function renderTopicIndustry(parent){
 const dossier=researchDossier(),frame=dossier?.frames?.[0];
 const premise=element('section','','research-route-block');
 premise.append(element('h3',mapText("01 · 工程问题与实现条件","01 · Engineering problem and implementation conditions")));
 if(frame&&compressionTopicId()!=='parameters-precision')premise.append(element('p',textOf(frame,'challenge')));
 premise.append(element('p',mapText("这里整理与本专题直接相关的工具和算子，以及部署所需的软件配套，并说明它们对技术选型的影响。","This section covers tools and operators directly relevant to the topic, deployment dependencies and their implications for technical choices."),'reader-note'));parent.append(premise);
 ensureTopicIndustryResearch();
 const reader=topicIndustryReaders.get(state.revision),error=topicIndustryErrors.get(state.revision);
 if(!reader){parent.append(element('p',error?mapText('产业资料暂不可用：','Industry references unavailable: ')+error:mapText('正在读取此专题已核查的实现与适用条件…','Loading reviewed implementations and conditions…'),'meta'));if(error)parent.append(button(mapText('重试产业资料','Retry industry references'),()=>{topicIndustryErrors.delete(state.revision);renderDirectionDetail();}));return;}
 const {snapshot,directory}=reader,entries=LRIIndustryUpdates.forTopic(snapshot,compressionTopicId());
 const weightTopic=compressionTopicId()==='parameters-precision';
 const direct=entries.filter(row=>row.link.relation_kind==='compression_direct'&&(!weightTopic||row.source.source_id==='source-msmodelslim-algorithms')),adjacent=weightTopic?[]:entries.filter(row=>row.link.relation_kind==='deployment_adjacent');
 const facts=element('section');facts.append(element('h3',mapText('02 · 直接相关的实现与能力','02 · Directly relevant implementations and capabilities')));
 if(!direct.length)facts.append(element('p',mapText("已审阅资料中尚未找到该路线的直接实现，现阶段仍需补充具体模型与算子支持依据。","Reviewed material has not yet established a direct implementation. Model and operator support still need to be documented."),'direction-gap'));
 const kindText={stable:['正式版','Stable release'],candidate:['候选 / 内测版','Candidate / internal test'],project_progress:['项目记录','Project log'],main_change:['主干变更','Main-branch change'],version_documentation:['官方文档','Official documentation']};
 const renderEntry=(host,entry)=>{
  const {assessment,update,source}=entry,card=element('article','','research-route-reader');card.dataset.industryAssessment=assessment.link_id;card.dataset.industryRelation=assessment.relation_kind;
  const family=directory.source_families.find(row=>row.family_id===update.family_id);
  const meta=element('p',title(family)+' · '+mapText(...kindText[update.release_kind])+' · '+update.version_label,'topic-dossier-type');card.append(meta);
  const heading=element('h4'),a=element('a',title(assessment));a.href=source.canonical_url;a.target='_blank';a.rel='noopener noreferrer';heading.append(a);card.append(heading);
  const brief=element('dl','','research-route-brief');
  for(const [zh,en,field] of [['原文事实','Primary fact','fact_focus'],['与本专题的关系','Relevance to this topic','relevance'],['对昇腾落地的影响（分析）','Ascend deployment impact (analysis)','impact']])brief.append(element('dt',mapText(zh,en)),element('dd',textOf(assessment,field)));
  card.append(brief,element('p',mapText('证据边界：','Evidence boundary: ')+textOf(assessment,'boundary'),'reader-note'));
  const stamp=element('p',mapText('核查：','Reviewed: ')+assessment.reviewed_at,'meta');
  const original=element('a',mapText('官方原文 ↗','Official source ↗'));original.href=source.canonical_url;original.target='_blank';original.rel='noopener noreferrer';stamp.append(document.createTextNode(' · '),original);card.append(stamp);
  const detail=researchBlock('research-industry-review:'+assessment.link_id,mapText('适用条件与原文定位','Conditions and source locator'));
  for(const [zh,en,value] of [['原文位置','Source locator',assessment.source_locator],['适用范围','Applicability',textOf(update,'scope')],['运行依赖','Runtime dependencies',textOf(update,'dependencies')],['针对本条的检查建议','Suggested check',textOf(assessment,'check')]]){const row=element('p');row.append(element('strong',mapText(zh,en)+'：'),document.createTextNode(value));detail.append(row);}card.append(detail);host.append(card);
 };
 direct.forEach(entry=>renderEntry(facts,entry));parent.append(facts);
 if(adjacent.length){
  const supporting=element('section');supporting.append(element('h3',mapText('03 · 部署配套与兼容性','03 · Deployment prerequisites and compatibility')));
  supporting.append(element('p',mapText("版本兼容与接口要求决定方案能否接入运行；模型质量和性能需另行测试。","Version compatibility and interface requirements determine whether integration is possible; model quality and performance require separate testing."),'reader-note'));
  const detail=researchBlock('research-industry-adjacent:'+compressionTopicId(),mapText('查看部署配套','View deployment prerequisites')+' · '+adjacent.length);
  adjacent.forEach(entry=>renderEntry(detail,entry));supporting.append(detail);parent.append(supporting);
 }
 const next=element('section');next.append(element('h3',mapText("04 · 实现条件对选型的影响","04 · How implementation conditions affect selection")));
 next.append(element('p',mapText("选择学术方案时，需要将数据表示与目标平台的模型、算子支持对应起来，并评估质量和执行成本。上述适配建议尚待本地验证。","Match each research approach's representation to model and operator support on the target platform, then assess quality and execution cost. The adaptation suggestions above await local validation."),'reader-note'));
 const link=element('a',mapText('继续：学术路线与原理 →','Continue: academic routes and principles →'),'science-route-link');link.href=researchHref('mechanism');link.dataset.compressionResearchView='mechanism';next.append(link);parent.append(next);
}

function compactResearchCitations(parent){
 const entries=[...parent.querySelectorAll('.topic-report-sources > li')],references=new Map();
 const appearance=new Map();for(const a of parent.querySelectorAll('.topic-dossier-citations a[href]')){const key=new URL(a.href,location.href).href;if(!appearance.has(key))appearance.set(key,appearance.size);}
 entries.sort((a,b)=>(appearance.get(new URL(a.querySelector('a').href,location.href).href)??9999)-(appearance.get(new URL(b.querySelector('a').href,location.href).href)??9999));
 for(const entry of entries)entry.parentElement.append(entry);
 entries.forEach((li,i)=>{const a=li.querySelector('a[href]');if(!a)return;const key=new URL(a.href,location.href).href;li.id='research-reference-'+(i+1);li.tabIndex=-1;references.set(key,{number:i+1,id:li.id,title:a.textContent,entry:li});});
 let count=0;
 for(const group of parent.querySelectorAll('.topic-dossier-citations')){
  const sup=element('sup','','research-citation');sup.setAttribute('aria-label',mapText('参考文献','References'));
  for(const old of group.querySelectorAll('a[href]')){
   const ref=references.get(new URL(old.href,location.href).href);if(!ref)continue;
   const a=element('a','['+ref.number+']','research-citation-link');a.href='#'+ref.id;a.dataset.researchCitation='true';a.id='research-cite-'+(++count);
   a.title=old.title||ref.title;a.setAttribute('aria-label',mapText('参考文献 '+ref.number+'：','Reference '+ref.number+': ')+ref.title);sup.append(a);
   if(!ref.entry.querySelector('.research-citation-return')){const back=element('a',mapText('返回引用处 ↑','Back to citation ↑'),'research-citation-return');back.href='#'+a.id;back.dataset.researchCitation='true';ref.entry.append(document.createTextNode(' '),back);}
  }
  if(!sup.childElementCount)continue;
  const block=group.parentElement,note=block.querySelector(':scope > p.meta'),previous=group.previousElementSibling;
  const target=block.matches?.('.quant-route-card')?block.querySelector('.quant-route-result p'):(note||(previous?.tagName==='P'?previous:null));
  if(target){target.append(document.createTextNode(' '),sup);group.remove();}else group.replaceWith(sup);
 }
}

function weightTopicCitations(parent,cardIds){
 const dossier=researchDossier(),links=element('div','','topic-dossier-citations'),seen=new Set();
 for(const ref of dossier.refs.filter(r=>cardIds.includes(r.card_id))){
  const source=dossier.sources.find(s=>s.source_id===ref.source_id);if(!source||seen.has(source.source_id))continue;seen.add(source.source_id);
  const a=element('a',source.title);a.href=safeUrl(source.canonical_url);a.title=source.title+' · '+textOf(ref,'locator')+' · '+(ref.observed_version==='current_abstract'?mapText('摘要记录','Abstract record'):ref.observed_version)+' · '+ref.checked_at;links.append(a);
 }if(links.childElementCount)parent.append(links);
}
function weightTopicCards(parent,ids){
 const dossier=researchDossier();
 for(const id of ids){
  const row=dossier.cards.find(c=>c.card_id===id);if(!row)continue;
  const card=element('article','','quant-article-card');card.dataset.researchCard=id;card.dataset.claimKind=row.claim_kind;
  card.append(element('h4',title(row)));appendResearchText(card,textOf(row,'body'));weightTopicCitations(card,[id]);parent.append(card);
 }
}
function weightTopicRoutes(parent){
 const dossier=researchDossier(),selected=new URLSearchParams(location.search).get('route'),all=dossier.routes.slice().sort((a,b)=>a.position-b.position);
 if(selected&&!all.some(r=>r.route_id===selected)){parent.append(element('p',mapText('该路线不属于当前专题。','This route is outside the current topic.'),'direction-gap'));return;}
 if(!selected){
  const index=element('nav','','quant-route-index');index.setAttribute('aria-label',mapText('学术路线索引','Academic route index'));
  for(const route of all){const a=element('a',title(route));a.href='#weight-route-'+route.route_id;index.append(a);}parent.append(index);
 }else{const a=element('a',mapText('← 本专题全部路线','← All routes'));a.href=researchHref('overview','routes');parent.append(a);}
 for(const route of all.filter(r=>!selected||r.route_id===selected)){
  const card=element('article','','quant-route-card');card.id='weight-route-'+route.route_id;card.dataset.researchRoute=route.route_id;
  card.append(element('p',mapText('学术路线 · 机制与原文结果','Academic route · Mechanism and reported result'),'meta'),element('h4',title(route)));
  const paragraph=(zh,en,text,cls='')=>{const p=element('p','',cls);p.append(element('strong',mapText(zh,en)+mapText('：',': ')),document.createTextNode(text));card.append(p);};
  paragraph('针对的挑战','Challenge',textOf(route,'problem'));
  paragraph('核心方法','Mechanism',textOf(route,'principle'));
  const steps=element('ol','','quant-route-steps');for(let i=1;i<=3;i++)steps.append(element('li',textOf(route,'step_'+i)));card.append(steps);
  const result=dossier.cards.find(c=>c.card_id===route.supporting_card_id);
  if(result){const box=element('div','','quant-route-result');box.dataset.claimKind=result.claim_kind;appendResearchText(box,textOf(result,'body'));card.append(box);}
  paragraph('研究启示','Research implication',textOf(route,'tradeoff'),'quant-route-implication');
  weightTopicCitations(card,[route.supporting_card_id]);parent.append(card);
 }
}

function compressionFoundationHref(method=''){
 const anchors={precision:'quantization',selection:'pruning-sparsity',distillation:'distillation',factorization:'low-rank'};
 const u=new URL('foundations.html',location.href);
 for(const [key,value]of [['month',state.period],['scope',state.scope]])if(value)u.searchParams.set(key,value);
 if(anchors[method])u.hash=anchors[method];
 return u.pathname+u.search+u.hash;
}
function renderFoundationLink(parent,method=''){
 const note=element('aside','','compression-foundation-link');
 note.append(element('p',mapText('量化、剪枝与稀疏、蒸馏、低秩分解的共同原理，集中在“压缩基础”中阅读。','Read the shared principles of quantization, pruning and sparsity, distillation and low-rank factorization in Compression foundations.')));
 const link=element('a',mapText('阅读压缩基础 →','Read compression foundations →'));link.href=compressionFoundationHref(method);note.append(link);parent.append(note);
}

function renderWeightQuantizationTopic(parent,topic,dossier){
 if(topicPage()&&['#research-overview-principles','#direction-quantization-principles'].includes(location.hash)){location.replace(compressionFoundationHref('precision'));return;}
 parent.classList.add('research-topic-report','weight-topic');
 const back=element('a',mapText('← 返回技术地图','← Technology map'),'direction-back');back.href='index.html'+(state.period?'?month='+state.period+(state.scope?'&scope='+state.scope:''):'')+'#view-topics';parent.append(back);
 const hero=element('header','','direction-hero compression-topic-hero');
 hero.append(element('p',mapText('推理压缩 · 持续研究专题','Inference compression · Living research topic'),'meta'),element('h1',title(topic)));
 const concept=state.data.compression_topic_concepts.find(row=>row.compression_topic_id===topic.compression_topic_id);if(concept)hero.append(element('p',textOf(concept,'summary'),'direction-lead'));
 const reviewed=dossier?dossier.cards.map(r=>r.reviewed_at).filter(Boolean).sort().at(-1):topic.reviewed_at;
 const status=element('p',dossier?mapText('资料核对至 ','Sources checked through ')+reviewed:mapText('正在读取本专题资料…','Loading the topic…'),'meta');status.dataset.dossierReady=String(Boolean(dossier));hero.append(status);parent.append(hero);renderFoundationLink(hero,'precision');
 const stages=[
 ['problem','研究背景','Research context',['background']],
 ['challenges','关键挑战','Key challenges',['background']],
 ['solutions','方案解析','Approaches and results',['mechanism','industry','literature']],
 ['comparison','选型判断','Selection decisions',['comparison']],
 ['implications','行动建议','Recommended actions',['implications']]
 ];
 const view=researchView(),complete=view==='overview',selected=new URLSearchParams(location.search).get('route'),nav=element('nav','','research-reader-tabs');nav.setAttribute('aria-label',mapText('权重量化阅读顺序','Weight quantization reading order'));
 if(!complete){const a=element('a',mapText('完整专题','Complete topic'));a.href=researchHref('overview');nav.append(a);}
 for(const [key,zh,en,views]of stages){const a=element('a',mapText(zh,en));a.href=complete?'#research-overview-'+key:researchHref(views[0],({problem:'scope',principles:'mechanism',challenges:'challenges',solutions:'routes',comparison:'comparison',implications:'implications'})[key]);if(!complete)a.dataset.compressionResearchView=views[0];nav.append(a);}parent.append(nav);
 document.body.dataset.lriReaderNavigation='.research-reader-tabs';document.body.dataset.lriReaderNavigationLabel=mapText('权重量化 · 阅读顺序','Weight quantization · Reading order');
 hero.append(element('p',mapText("围绕权重量化的关键挑战，比较产业实现和学术方案，再结合实验结果提出选型与研究建议。","Compare industry implementations and research approaches against the challenges of weight quantization, then use experimental evidence to inform selection and further study."),'reader-note'));
 if(!dossier){const error=dossierErrors.get(state.revision+'__'+compressionTopicId());if(error)parent.append(element('p',error,'direction-gap'),button(mapText('重试专题','Retry topic'),()=>{dossierErrors.delete(state.revision+'__'+compressionTopicId());renderDirectionDetail();}));return;}
 const sections={};
 for(const [key,zh,en,views]of stages){
  const section=element('section','','research-overview-section');section.id='research-overview-'+key;section.dataset.sectionLabel=mapText(zh,en);
  section.hidden=selected?key!=='solutions':!complete&&!views.includes(view);
  section.dataset.readingLayer=key==='implications'?'conclusion':key==='comparison'?'analysis':'facts';
  section.append(element('h2',String(stages.findIndex(r=>r[0]===key)+1).padStart(2,'0')+' · '+mapText(zh,en)));parent.append(section);sections[key]=section;
 }
 const sub=(host,id,zh,en)=>{const node=element('section','','quant-reader-section');node.id='direction-'+id;node.dataset.sectionOutline='false';node.append(element('h3',mapText(zh,en)));host.append(node);return node;};
 const context=sub(sections.problem,'scope','降低权重存储与访存开销','Reducing weight storage and memory traffic');renderResearchFraming(context,'why');
 const value=sub(sections.problem,'value','理论容量与实际性能','Theoretical capacity and measured performance');renderResearchFraming(value,'value');
 const challenge=sub(sections.challenges,'challenges',"量化方案面临的四类挑战","Four challenges in quantization");
 const frame=dossier.frames[0],challengeGrid=element('div','','quant-challenge-grid');
 textOf(frame,'challenge').split(/\n+/).filter(Boolean).forEach((text,i)=>{const m=/^([^：:]+)[：:]\s*(.*)$/.exec(text),box=element('article');box.append(element('span',String(i+1).padStart(2,'0'),'quant-challenge-number'),element('h4',m?m[1]:text));if(m)box.append(element('p',m[2]));challengeGrid.append(box);});challenge.append(challengeGrid);weightTopicCitations(challenge,[frame.supporting_card_id]);
 const industry=sub(sections.solutions,'industry',"产业实现与适配条件","Industry implementations and adaptation requirements");
 industry.hidden=!complete&&!selected&&view!=='industry';const industryAlias=element('span');industryAlias.id='research-overview-industry';industry.append(industryAlias);
 weightTopicCards(industry,['parameters-precision__industry_vllm','parameters-precision__msmodelslim_implementation','parameters-precision__industry_kernel','parameters-precision__industry_domain']);
 const routes=sub(sections.solutions,'routes',"学术方法与实验结果","Research methods and experimental results");routes.hidden=!complete&&!selected&&!['mechanism','literature'].includes(view);if(selected)industry.hidden=true;
 const routesAlias=element('span');routesAlias.id='research-overview-routes';routes.append(routesAlias);
 weightTopicRoutes(routes);
 const compare=sub(sections.comparison,'comparison',"方案比较与研究优先级","Approach comparison and research priorities");
 weightTopicCards(compare,['parameters-precision__dossier_3','parameters-precision__dossier_4']);
 const conclusion=sub(sections.implications,'implications',"重点研究方向与选择依据","Priority directions and selection rationale");
 weightTopicCards(conclusion,['parameters-precision__dossier_5']);
 const next=sub(sections.implications,'watch',"验证方案与预期目标","Validation plan and expected outcomes");
 weightTopicCards(next,['parameters-precision__dossier_6']);
 const sources=element('section','','quant-reader-section');sources.id='direction-sources';sources.dataset.sectionOutline='false';sources.append(element('h3',mapText("参考文献与章节","References and sections")));
 const list=element('ol','','topic-report-sources');
 for(const source of dossier.sources){const li=element('li');external(li,source.canonical_url,source.title);const refs=dossier.refs.filter(r=>r.source_id===source.source_id).sort((a,b)=>b.checked_at.localeCompare(a.checked_at)),preferred=refs.find(r=>r.card_id.includes('__case_')||r.card_id.includes('__industry_'))||refs[0];if(preferred)li.append(element('p',textOf(preferred,'locator')+' · '+preferred.observed_version+' · '+preferred.checked_at,'meta'));list.append(li);}sources.append(list);parent.append(sources);
 compactResearchCitations(parent);parent.dataset.researchView=view;
 if(topicPage())document.title=title(topic)+' · 推理压缩专题 · 云核';
 document.dispatchEvent(new Event('lri:sections-changed'));
 if(location.hash)requestAnimationFrame(()=>{const target=$(location.hash.slice(1));if(target&&!target.closest('[hidden]'))target.scrollIntoView({block:'start'});});
}


function renderCompressionTopic(parent,cell){
 parent.classList.add('research-topic-report');
 const id=compressionTopicId(),topic=state.data.compression_topics.find(row=>row.compression_topic_id===id),techniques=techniquesForCell(cell),routes=linkedLineages(cell),dossier=researchDossier();ensureResearchDossier();
 if(id==='parameters-precision'){renderWeightQuantizationTopic(parent,topic,dossier);return;}
 const back=element('a',mapText('← 技术地图 · 全部专题','← Technology map · All topics'),'direction-back');back.href='index.html'+(state.period?'?month='+state.period+(state.scope?'&scope='+state.scope:''):'')+'#view-topics';back.dataset.compressionTopicBack='true';parent.append(back);
 const hero=element('header','','direction-hero compression-topic-hero'),badges=element('div','','direction-badges');
 badges.append(element('span',mapText('推理压缩 · 持续研究专题','Inference compression · Living research topic')),element('span',topic.catalog_kind==='matrix'?mapText('技术地图 · 独立专题','Technology map · Independent topic'):mapText('扩展专题','Additional topic')));
 hero.append(badges,element(topicPage()?'h1':'h2',title(topic)),element('p',textOf(topic,'question'),'direction-lead'));
 const concept=state.data.compression_topic_concepts.find(row=>row.compression_topic_id===id);if(concept)hero.append(element('p',textOf(concept,'summary'),'research-concept'));
 const stats=element('div','','direction-stats topic-report-meta');for(const [value,name,en] of [[state.referencePending?'—':techniques.length,'代表技术','Representative methods'],[dossier?dossier.cards.filter(row=>row.card_kind==='case').length:'—','原文案例','Primary-source cases'],[dossier?dossier.sources.length:'—','关联原文','Primary sources']]){const box=element('div');box.append(element('strong',value),element('span',mapText(name,en)));stats.append(box);}const counts=researchBlock('research-metadata-'+id,mapText('资料覆盖与审阅状态','Coverage and review status'));counts.append(stats);hero.append(counts);
 hero.append(element('p',mapText("围绕该方向梳理技术原理、代表工作和适用条件，并据此比较方案、提出研究建议。","Explore principles, representative work and applicability, then compare approaches and identify further research."),'meta'));
 const status=element('p','','topic-dossier-status');status.setAttribute('role','status');
 if(dossier){status.textContent=mapText('专题资料已加载 · ','Research dossier loaded · ')+dossier.cards.length+mapText(' 条研究内容 · 整理日期 ',' research cards · Reviewed ')+topic.reviewed_at;status.dataset.dossierReady='true';}
 else {const error=dossierErrors.get(state.revision+'__'+id);status.textContent=error?mapText('专题资料读取失败：','Dossier read failed: ')+error:mapText('正在读取当前专题的研究资料…','Loading this topic’s research dossier…');if(error)status.append(button(mapText('重试专题资料','Retry dossier'),()=>{dossierErrors.delete(state.revision+'__'+id);renderDirectionDetail();}));}hero.append(status);
 const actions=element('div','','actions topic-report-actions');for(const [key,zh,en] of [['mechanism',"技术原理","Technical principles"],['papers',"代表工作","Representative work"],['comparison',"路线比较","Approach comparison"]]){const link=element('a',mapText(zh,en),'btn secondary');link.href='#direction-'+key;actions.append(link);}hero.append(actions);renderFoundationLink(hero,topic.method_term_id);parent.append(hero);researchNav(parent);
 const sections=[['scope','研究背景','Research background'],['value','价值目标','Value and goals'],['challenges','关键挑战','Key challenges'],['mechanism','学术原理','Academic principles'],['routes','学术路线详解','Academic routes explained'],['industry','产业实现与适配','Industry implementation and adaptation'],['papers','代表成果','Representative results'],['comparison','方法比较','Method comparison'],['boundary','适用边界','Applicability boundaries'],['implications','研究结论','Research conclusions'],['watch','下一步行动','Next actions'],['sources',"参考文献","References"]];
 // Shared Shell owns the reader path; avoid a second full outline above every subpage.
 renderTopicOverview(parent,topic,dossier);
 const section=key=>{const index=sections.findIndex(row=>row[0]===key),name=mapText(sections[index][1],sections[index][2]),node=element('section','','direction-section');node.id='direction-'+key;node.dataset.sectionLabel=name;node.dataset.sectionNumber=String(index+1).padStart(2,'0');node.dataset.readingLayer=['comparison','boundary'].includes(key)?'analysis':['implications','watch'].includes(key)?'conclusion':'facts';const heading=element(topicPage()?'h2':'h3',String(index+1).padStart(2,'0')+' · '+name);node.append(heading);if(['papers','comparison','implications'].includes(key)){const divider=element('p',key==='papers'?mapText('原文事实','Primary-source facts'):key==='comparison'?mapText('整合分析','Synthesis and analysis'):mapText('研究建议','Research suggestions'),'topic-report-part');node.insertBefore(divider,heading);}parent.append(node);return node;};
 const paragraph=(node,kind)=>{const row=topicSectionRow(kind);if(row)node.append(element('p',textOf(row,'body')));};
 const scope=section('scope');renderResearchFraming(scope,'why');if(id!=='parameters-precision')paragraph(scope,'problem');renderTopicTargetDiagram(scope);const value=section('value');renderResearchFraming(value,'value');const challenges=section('challenges');renderResearchFraming(challenges,'challenge');
 const paths=element('div','','direction-definition-grid');
 for(const [view,zh,en,bodyZh,bodyEn] of [['industry',"产业实现","Industry implementations",'先核对工具、算子与适配条件，明确哪些挑战已有实现。','Check tools, operators and conditions to identify implemented challenges.'],['mechanism',"学术路线","Research approaches",'针对工程缺口，比较文献中的表示、误差控制和成本取舍。','Compare representations, error control and cost tradeoffs against engineering gaps.']]){
  const box=element('article'),link=element('a',mapText(zh,en));link.href=researchHref(view);link.dataset.compressionResearchView=view;box.append(link,element('p',mapText(bodyZh,bodyEn)));paths.append(box);
 }challenges.append(paths);
 const mechanism=section('mechanism');if(id!=='parameters-precision')renderResearchFraming(mechanism,'challenge');renderMechanismDiagram(mechanism);renderDossierCards(mechanism,'mechanism');if(!dossier)paragraph(mechanism,'mechanism');
 const routeSection=section('routes');renderResearchRoutes(routeSection);if(!dossier)paragraph(routeSection,'mechanism');
 const industry=section('industry');if(['industry','overview'].includes(researchView()))renderTopicIndustry(industry);
 const papers=section('papers');papers.append(element('p',mapText("代表文献持续保留，实验结果附有原文的模型、任务、硬件和基线条件；各项资料注明已审阅的范围。","Representative papers remain available over time. Results retain the original model, task, hardware and baseline conditions, with the review scope stated for each source."),'meta'));renderDossierCards(papers,'papers');
 if(state.referencePending)papers.append(element('p',state.referenceError?mapText('补充技术索引暂不可用：','Supplementary technique index unavailable: ')+state.referenceError:mapText('专题原文已加载，正在补充跨专题的代表技术索引。','Topic sources are ready; supplementing the cross-topic technique index.'),'meta'));
 if(!techniques.length&&!state.referencePending)papers.append(element('div',mapText("该组合尚待补充直接文献。下方相关蒸馏或低秩工作用于解释相近原理，其适用性仍需进一步确认。","Direct references are still needed for this combination. Related distillation or low-rank work below explains adjacent principles; applicability requires further review."),'direction-gap'));
 for(const row of techniques){const card=researchBlock('topic-technique-'+row.technique_id,title(row)+mapText(' · 机制与原文',' · Mechanism and source'));card.classList.add('direction-paper');card.dataset.directionTechnique=row.technique_id;card.append(element('p',row.mechanism),element('p',row.boundary));for(const ref of state.data.source_refs.filter(ref=>ref.technique_id===row.technique_id)){const source=sourceById(ref.source_id);external(card,source.canonical_url,source.title+' →');}papers.append(card);}
 const comparison=section('comparison'),primaryComparison=renderRouteEvidence(comparison),comparisonContent=primaryComparison?.supplement||comparison;renderDossierCards(comparisonContent,'comparison');if(!dossier)paragraph(comparisonContent,'comparison');if(primaryComparison)comparison.querySelector('.topic-report-part').textContent=mapText('路线与原文证据','Routes and primary evidence');
 if(techniques.length){const wrap=element('div','','table-wrap'),table=element('table','','topic-comparison-table'),head=element('thead'),tr=element('tr');for(const text of [mapText('代表方法','Method'),mapText('机制差异','Mechanism'),mapText('适用条件与限制','Conditions and limits')])tr.append(element('th',text));head.append(tr);table.append(head);const body=element('tbody');for(const row of techniques){const tr=element('tr');tr.append(element('th',title(row)),element('td',row.mechanism),element('td',row.boundary));body.append(tr);}table.append(body);wrap.append(table);comparisonContent.append(wrap);}else if(!state.referencePending)comparisonContent.append(element('p',mapText("现有资料的实验条件尚不足以支持同条件排名。","Available evidence does not yet support a ranking under matched conditions."),'direction-gap'));
 comparisonContent.append(element('p',mapText("比较时需核对模型与任务、位宽或压缩配置、输入长度与批量、硬件和运行栈，并在一致的基线下评估质量与成本。","Check model and task, compression settings, input length, batch size, hardware and runtime, then compare quality and cost against a consistent baseline."),'topic-metric-contract'));
 const boundary=section('boundary');renderDossierCards(boundary,'boundary');if(!dossier)paragraph(boundary,'boundary');if(primaryComparison)boundary.append(primaryComparison.decisions);
 const implications=section('implications');renderDossierCards(implications,'implication');if(!dossier)paragraph(implications,'implication');implications.append(element('p',mapText("以上为昇腾研究建议，实际效果需在目标平台验证。","These are research suggestions for Ascend; practical results require target-platform validation."),'meta'));
 const watch=section('watch');renderDossierCards(watch,'watch');if(!dossier)paragraph(watch,'watch');
 const accumulation=section('sources'),sourceSet=new Set();const sourceList=element('ol','','topic-report-sources');const sourceRows=dossier?dossier.sources:state.data.source_refs.filter(ref=>techniques.some(t=>t.technique_id===ref.technique_id)).map(ref=>sourceById(ref.source_id));for(const source of sourceRows)if(source&&!sourceSet.has(source.source_id)){sourceSet.add(source.source_id);const entry=element('li');external(entry,source.canonical_url,source.title);sourceList.append(entry);}
 accumulation.append(sourceList);
 external(accumulation,topicSectionRow('problem').evidence_url,mapText('分类与边界综述 →','Taxonomy and boundaries survey →'));accumulation.append(element('p',mapText("本专题持续整理与该对象、方法相关的代表文献，按原始来源去重；当前收录范围尚非完整的系统综述。","This topic collects representative literature for the target and method, deduplicated by primary source. Coverage is not an exhaustive systematic review."),'meta'));
 const timelineLink=element('a',mapText('查看此专题相关的本期动态 →','View current updates related to this topic →'),'science-route-link');timelineLink.dataset.compressionTopicTimeline='true';timelineLink.href='index.html?topic='+id+(state.period?'&month='+state.period:'')+(state.scope?'&scope='+state.scope:'')+'#view-updates';accumulation.append(timelineLink);
 const more=researchBlock('topic-neighbors',mapText('同一对象的其他研究专题','Other topics for this target')),neighbors=element('div','','direction-neighbors');for(const row of ordered(state.data.compression_topics.filter(row=>row.target_term_id===state.focusTarget&&row.compression_topic_id!==id)))neighbors.append(scientificLink(row.target_term_id,row.method_term_id,title(row)));more.append(neighbors);accumulation.append(more);
 composeResearchOverview(parent);renderTopicCatalogue(parent,id);compactResearchCitations(parent);
 applyResearchView(parent);if(topicPage())document.title=title(topic)+' · 推理压缩专题 · 云核';document.dispatchEvent(new Event('lri:sections-changed'));
 if(topicPage()&&/^(research-overview-|direction-)/.test(location.hash.slice(1)))requestAnimationFrame(()=>{const target=$(location.hash.slice(1));if(target&&!target.closest('[hidden]'))target.scrollIntoView({block:'start'});});
}

function validateTopicEvent(row,scope,period,id){
 must(row.scope_id===scope&&row.period_id===period&&row.compression_topic_id===id&&row.scope_topic_key===scope+'__'+id&&row.evidence_id&&row.source_id&&['primary_review','title_candidate'].includes(row.review_status),'Invalid compression topic event');safeUrl(row.classification_basis);
}
async function topicScopeRows(scope,period,revision){
 const records=[];let offset=0,total=null;for(;;){const result=await page('compression_topic_events','scope_id',scope,revision,{offset,limit:100});validateEvidenceRevision(result,revision);const meta=result.page;must(meta&&Number.isSafeInteger(meta.total)&&meta.total<=2000&&typeof meta.truncated==='boolean','Invalid topic scope page');if(total===null)total=meta.total;else must(total===meta.total,'Topic scope total changed');for(const row of result.records){must(state.data.compression_topics.some(topic=>topic.compression_topic_id===row.compression_topic_id),'Unknown topic event');validateTopicEvent(row,scope,period,row.compression_topic_id);records.push(row);}must(records.length<=total&&meta.truncated===(records.length<total),'Incomplete topic associations');if(!meta.truncated)break;must(result.records.length>0&&meta.nextOffset===offset+result.records.length,'Invalid topic scope cursor');offset=meta.nextOffset;}must(new Set(records.map(row=>row.link_id)).size===records.length,'Repeated topic association');return records;
}
async function loadCompressionTopicEvidence(offset=0,allTopics=false){
 const request=++state.evidenceEpoch,revision=state.revision,scope=state.scope,period=state.period,id=allTopics?'':compressionTopicId(),object=state.object,cell=state.cell;const active=()=>request===state.evidenceEpoch&&revision===state.revision&&scope===state.scope&&period===state.period&&(allTopics?!state.focusTarget&&object===state.object&&cell===state.cell:id===compressionTopicId())&&state.scopeReady;
 state.evidenceBusy=true;state.evidenceError=false;state.paperSummaryError='';state.evidence=[];state.evidencePage=null;state.evidenceOffset=offset;renderEvidence();
 try{
  must(Number.isSafeInteger(offset)&&offset>=0,'Invalid topic offset');
  const catalog=new Set(state.data.compression_topics.map(row=>row.compression_topic_id));
  const associations=allTopics?state.topicScopeLinks:topicEventsFor(id);
  must(associations.every(row=>catalog.has(row.compression_topic_id)&&row.scope_id===scope&&row.period_id===period),'Invalid monthly topic scope');
  const unique=new Map();for(const row of associations){const previous=unique.get(row.evidence_id);if(previous)must(previous.source_id===row.source_id,'Cross-topic source mismatch');if(!previous||row.review_status==='primary_review')unique.set(row.evidence_id,row);}
  const records=(allTopics?[...unique.values()]:associations).sort((a,b)=>(a.review_status==='primary_review'?0:1)-(b.review_status==='primary_review'?0:1)||b.position-a.position||a.evidence_id.localeCompare(b.evidence_id));
  must(new Set(records.map(row=>row.evidence_id)).size===records.length,'Repeated event within topic');must(offset===0||offset<records.length,'Topic page outside scope');const selected=records.slice(offset,offset+20),ids=selected.map(row=>row.evidence_id);
  let evidence=[];if(ids.length){const items=await LRITableGit.loadRowsByKeys('ic_evidence_items',ids,revision);if(!active())return;validateEvidenceRevision(items,revision);assertBusiness(items.records);must(items.records.length===ids.length&&new Set(items.records.map(row=>row.evidence_id)).size===ids.length,'Missing topic evidence');const itemMap=new Map(items.records.map(row=>[row.evidence_id,row]));must(selected.every(row=>itemMap.get(row.evidence_id)?.source_id===row.source_id),'Topic evidence source mismatch');
   const sourceIds=[...new Set(selected.map(row=>row.source_id))],sources=await LRITableGit.loadRowsByKeys('cloud_core_sources',sourceIds,revision,['source_id','business_id','title','canonical_url']);if(!active())return;validateEvidenceRevision(sources,revision);must(sources.records.length===sourceIds.length&&new Set(sources.records.map(row=>row.source_id)).size===sourceIds.length&&sources.records.every(row=>row.business_id==='cloud-core'&&sourceIds.includes(row.source_id)),'Missing topic canonical source');const sourceMap=new Map(sources.records.map(row=>[row.source_id,row]));evidence=selected.map(row=>{const source=sourceMap.get(row.source_id);safeUrl(source.canonical_url);return {topicBinding:row,placements:[],placement:{},item:itemMap.get(row.evidence_id),source};});
   try{const index=await paperSummaryIndex(revision,period);if(!active())return;evidence=await hydratePaperSummaries(evidence,revision,index);}catch(error){if(!active())return;state.paperSummaryError=summaryReadError(error);}
  }
  if(!active())return;state.evidence=evidence;state.evidencePage={total:records.length,offset,limit:20,truncated:offset+evidence.length<records.length,nextOffset:offset+evidence.length};state.evidenceBusy=false;renderEvidence();
 }catch(error){if(!active())return;if(fatal(error))fail(error);else{state.evidenceBusy=false;state.evidenceError=true;renderEvidence();}}
}
function persistTopicScope(){const url=new URL(location.href);if(state.focusTarget&&state.focusMechanism)url.searchParams.set('topic',compressionTopicId());else url.searchParams.delete('topic');if(state.period)url.searchParams.set('month',state.period);if(state.scope)url.searchParams.set('scope',state.scope);history.replaceState(null,'',url.pathname+url.search+url.hash);document.dispatchEvent(new Event('lri:sections-changed'));}

function validateScientificTaxonomy(data){
 const facets=new Set(data.map_facets.map(row=>row.facet_id)),terms=new Map(data.map_terms.map(row=>[row.term_id,row]));
 must(facets.size===5&&facets.size===data.map_facets.length,'Invalid scientific facets');must(terms.size===data.map_terms.length,'Duplicate scientific term');
 for(const row of data.map_terms){must(facets.has(row.facet_id)&&(!row.parent_term_id||terms.has(row.parent_term_id)),'Broken scientific term');const seen=new Set([row.term_id]);let parent=row.parent_term_id;while(parent){must(!seen.has(parent),'Scientific term cycle');seen.add(parent);parent=terms.get(parent).parent_term_id;}safeUrl(row.source_url);}
 const domains={technique:new Set(data.techniques.map(row=>row.technique_id)),lineage:new Set(data.lineages.map(row=>row.lineage_id)),legacy_cell:new Set(data.cells.map(row=>row.cell_id)),legacy_object:new Set(data.objects.map(row=>row.object_id)),legacy_method:new Set(data.methods.map(row=>row.method_id))},seen=new Set();
 for(const row of data.map_assignments){must(!seen.has(row.assignment_id)&&terms.has(row.term_id)&&domains[row.subject_kind]?.has(row.subject_id),'Broken scientific assignment');seen.add(row.assignment_id);}
}
function mapTerm(id){return state.data.map_terms.find(row=>row.term_id===id);}
function scientificDescendants(id){const result=new Set([id]);let changed=true;while(changed){changed=false;for(const row of state.data.map_terms)if(result.has(row.parent_term_id)&&!result.has(row.term_id)){result.add(row.term_id);changed=true;}}return result;}
function scientificTechniqueIds(id){const terms=scientificDescendants(id);return new Set(state.data.map_assignments.filter(row=>row.subject_kind==='technique'&&terms.has(row.term_id)).map(row=>row.subject_id));}
function scientificFocusTitle(){return state.focusTarget?title(mapTerm(state.focusTarget))+' × '+title(mapTerm(state.focusMechanism)):'';}
function scientificLink(target,mechanism,text){const link=element('a',text,'science-route-link');link.href='topic.html?topic='+target+'-'+mechanism+(state.period?'&month='+state.period:'')+(state.scope?'&scope='+state.scope:'');link.dataset.compressionTopicRoute=target+'-'+mechanism;link.dataset.scientificTarget=target;link.dataset.scientificMechanism=mechanism;return link;}
function selectScientificFocus(target,mechanism){
  if(target==='persistent_state')target='kv_cache'; // Preserve links from the former state grouping.
  const targetTerm=mapTerm(target),methodTerm=mapTerm(mechanism);if(!targetTerm||!methodTerm||targetTerm.facet_id!=='target'||!['mechanism','construction'].includes(methodTerm.facet_id))return;
  const objectIds=new Set(state.data.map_assignments.filter(row=>row.subject_kind==='legacy_object'&&scientificDescendants(target).has(row.term_id)).map(row=>row.subject_id));
  const methodIds=new Set(state.data.map_assignments.filter(row=>row.subject_kind==='legacy_method'&&row.term_id===mechanism&&row.basis!=='review_required').map(row=>row.subject_id));
  if(['sharing','compact_architecture'].includes(mechanism))methodIds.add('G');if(mechanism==='merging')methodIds.add('P');
  const cells=ordered(state.data.cells.filter(row=>objectIds.has(row.object_id)&&methodIds.has(row.method_id)));if(!cells.length)return;
  state.focusTarget=target;state.focusMechanism=mechanism;state.focusCells=cells.map(row=>row.cell_id);
  return cells;
}
function openScientificFocus(target,mechanism,updateHash=true){
  const cells=selectScientificFocus(target,mechanism);if(!cells)return;
  openDirection(cells[0].cell_id,false,true);if(updateHash)history.pushState(null,'','#focus-'+target+'-'+mechanism);
  if(state.scopeReady){persistTopicScope();loadEvidence(0);}
}
function renderScientificMap(){
 const parent=$('scientific-map');parent.replaceChildren();if(!state.data.map_facets?.length)return;
 const targets=ordered(state.data.map_terms.filter(row=>row.facet_id==='target'&&!row.parent_term_id)),methods=ordered(state.data.map_terms.filter(row=>row.facet_id==='mechanism'));
 const header=element('header','','science-map-header');
 header.append(element('p',mapText('推理压缩 · 文献分类','Inference compression · Literature taxonomy'),'science-eyebrow'),element('h3',mapText('压缩对象 × 模型压缩方法','Compression targets × Model compression methods')),element('p',mapText("以权重、激活和 KV Cache 为压缩对象，按量化、剪枝、知识蒸馏和低秩分解组织专题。方法分类参考 TACL 2024 综述；点击专题可阅读原理、代表工作与适用条件。","Explore weights, activations and KV Cache through quantization, pruning, knowledge distillation and low-rank factorization. The method taxonomy follows the TACL 2024 survey; each topic covers principles, representative work and applicability.")));
 header.append(element('p',mapText("这12个专题用于导航，部分方法可以组合使用；各方向的成熟度与证据情况在专题中说明。","These 12 topics provide navigation. Some methods can be combined; each topic describes its maturity and evidence."),'science-map-contract'));
 external(header,'https://aclanthology.org/2024.tacl-1.85.pdf',mapText('分类依据：TACL 2024 · 图 1、表 1 →','Classification source: TACL 2024 · Figure 1, Table 1 →'));renderFoundationLink(header);parent.append(header);
 const wrap=element('div','','literature-matrix-wrap'),table=element('table','','literature-matrix');table.setAttribute('aria-label',mapText('压缩对象与文献方法矩阵','Compression target and literature method matrix'));
 const caption=element('caption',mapText("各格概述研究对象与方法。涉及蒸馏的专题会进一步区分训练中的特征匹配与推理时实际压缩的数据。","Each cell introduces a target and method. Distillation topics distinguish feature matching during training from data actually compressed during inference."));table.append(caption);
 const thead=element('thead'),head=element('tr'),corner=element('th',mapText('压缩对象','Target'));corner.setAttribute('scope','col');head.append(corner);
 for(const method of methods){const th=element('th');th.setAttribute('scope','col');th.append(LRICompressionVisuals.icon(method.term_id,28),document.createTextNode(title(method)));th.append(element('small',state.locale==='zh'?method.name_en:method.name_zh));head.append(th);}thead.append(head);table.append(thead);
 const tbody=element('tbody');
 for(const target of targets){const tr=element('tr');tr.dataset.scientificObject=target.term_id;const th=element('th',title(target));th.setAttribute('scope','row');th.append(element('small',textOf(target,'description')));tr.append(th);const ids=scientificTechniqueIds(target.term_id);
  for(const method of methods){const mids=scientificTechniqueIds(method.term_id),rows=state.data.techniques.filter(row=>ids.has(row.technique_id)&&mids.has(row.technique_id)&&row.inference_scope!=='training_only');const td=element('td'),link=scientificLink(target.term_id,method.term_id,'');link.className='literature-cell';link.setAttribute('aria-label',title(target)+' × '+title(method)+' · '+mapText('研究专题','Research topic'));const concept=state.data.compression_topic_concepts.find(row=>row.compression_topic_id===target.term_id+'-'+method.term_id);link.append(element('strong',title(target)+' × '+title(method)),element('span',textOf(concept,'summary'),'literature-cell-concept'),element('small',mapText('进入研究专题 →','Explore research topic →')));td.append(link);tr.append(td);}
  tbody.append(tr);
 }table.append(tbody);wrap.append(table);parent.append(wrap);
 const extensions=element('details','','science-strategy literature-extensions');extensions.append(element('summary',mapText("扩展研究方向","Additional research directions")));
 extensions.append(element('p',mapText("以下方向补充 KV Cache 管理等研究，名称沿用相关综述或原始论文。","These topics cover additional work such as KV Cache management, retaining terminology from the relevant surveys and papers.")));
 for(const method of ordered(state.data.map_terms.filter(row=>row.facet_id==='construction'))){const box=element('section');box.append(element('h4',title(method)),element('p',textOf(method,'description')));const tids=scientificTechniqueIds(method.term_id);for(const target of targets)if([...scientificTechniqueIds(target.term_id)].some(id=>tids.has(id)))box.append(scientificLink(target.term_id,method.term_id,title(target)+' × '+title(method)+' →'));external(box,method.source_url,mapText('术语与技术原文 →','Terminology and primary source →'));extensions.append(box);}parent.append(extensions);
 const facets=element('details','','science-facets');facets.append(element('summary',mapText('场景与评价条件','Workloads and evaluation conditions')));
 for(const facet of state.data.map_facets.filter(row=>['context','cost'].includes(row.facet_id))){const box=element('section');box.append(element('h4',title(facet)),element('p',textOf(facet,'description')));for(const term of state.data.map_terms.filter(row=>row.facet_id===facet.facet_id))box.append(element('span',title(term),'science-tag'));facets.append(box);}parent.append(facets);
 const basis=element('details','','science-basis');basis.append(element('summary',mapText('分类出处与归类规则','Classification sources and assignment rules')));
 const facts=element('ol');for(const text of [mapText('TACL 2024《A Survey on Model Compression for Large Language Models》图 1、正文第 3–6 节采用量化、剪枝、知识蒸馏、低秩分解四类方法；表 1 分列 Weights、Activations、KV Cache。','TACL 2024 Figure 1 and Sections 3–6 use Quantization, Pruning, Knowledge Distillation and Low-Rank Factorization; Table 1 lists Weights, Activations and KV Cache.'),mapText('KV Cache 管理综述分别讨论 selection、budget allocation、merging、quantization、low-rank decomposition；本页把 KV 淘汰作为扩展专题，保留具体文献术语。','The KV Cache management survey separately discusses selection, budget allocation, merging, quantization and low-rank decomposition. KV eviction is an additional named topic here.'),mapText('论文按实际方法归类，允许组合；稀疏性质不与剪枝重复计数。蒸馏使用的中间特征不自动视为被压缩对象。','Assign papers by actual intervention and allow combinations; do not double-count sparsity and pruning. Intermediate features used for distillation are not automatically compressed targets.'),mapText('对象 × 方法是页面导航视图；文献未规定必须是 3 × 4，也不保证每个交叉格都有成熟算法。没有原文依据的条目标为待核对。','The target × method matrix is a navigation view; the literature does not mandate 3 × 4 or mature algorithms in every cell. Entries without primary support remain pending review.')])facts.append(element('li',text));basis.append(facts);
 for(const [url,name] of [['https://aclanthology.org/2024.tacl-1.85.pdf','TACL 2024 · A Survey on Model Compression for Large Language Models'],['https://arxiv.org/abs/2412.19442','TMLR 2025 · A Survey on Large Language Model Acceleration based on KV Cache Management'],['https://arxiv.org/abs/2401.15347','A Comprehensive Survey of Compression Algorithms for Language Models']])external(basis,url,name);parent.append(basis);
}

function renderSelectors() {
  const periods=$('period-filter'); periods.replaceChildren();
  for(const row of state.data.trend_periods.filter(row=>row.month>='2026-10').sort((a,b)=>b.month.localeCompare(a.month))) { const option=element('option',row.month+(row.source_status==='ongoing'?' · '+label('ongoing'):'')); option.value=row.period_id; periods.append(option); }
  periods.value=state.period;
  const scopes=$('scope-filter'); scopes.replaceChildren();
  for(const row of ordered(state.scopes)) { const option=element('option',title(row)); option.value=row.scope_id; scopes.append(option); }
  scopes.value=state.scope;
  const objects=$('object-filter'); objects.replaceChildren(element('option',label('all_objects'))); objects.options[0].value='';
  for(const row of state.data.objects) { const option=element('option',title(row)); option.value=row.object_id; objects.append(option); }
  objects.value=state.object;
}
function renderScope() {
  renderOverview(); renderMonthlyDirections(); renderEvidence();
  const detail=$('scope-detail'); detail.replaceChildren(); const scope=currentScope();
  $('scope-retry').hidden=!state.scopeError;
  if(state.scopeError)$('monthly-status').textContent=label('scope_read_failed');
  else if(state.scopeBusy)$('monthly-status').textContent=label('loading');
  else if(!scope)$('monthly-status').textContent=label('no_scope');
  else $('monthly-status').textContent=title(scope)+' · '+label('sample_boundary')+' · '+label(state.scopeReady?'ready':'loading')+(scope.coverage_note?' · '+scope.coverage_note:'');
  if(!scope){detail.append(element('p',label(state.scopeError?'scope_read_failed':state.scopeBusy?'loading':'scope_empty_help'),'reader-note'));return;}
  field(detail,'scope_window',scope.window_start+' — '+scope.window_end);
  field(detail,'month_basis',enumLabel('basis_',scope.month_basis)); field(detail,'coverage',scope.coverage_note);
  field(detail,'source_pool',enumLabel('pool_',scope.source_pool)); field(detail,'selection_rule',scope.selection_rule); field(detail,'dedup_rule',scope.dedup_rule);
  field(detail,'collected_at',scope.collected_at); field(detail,'review_status',enumLabel('status_',scope.status));
}
function renderMap() {
  renderLineages();renderScientificMap();renderDirectionDetail();
}
function renderSelection() {
  renderOverview(); renderMonthlyDirections();renderReadingContext();
  const cell=currentCell(); $('selection-title').textContent=cell?(scientificFocusTitle()||cellTitle(cell)):label(state.all?'all_techniques':'choose_direction'); $('selection-status').textContent=label('candidate_boundary');if(state.focusTarget&&!topicPage()){const route=scientificLink(state.focusTarget,state.focusMechanism,'打开完整研究专题 →');$('selection-title').append(document.createTextNode(' · '),route);}
  const detail=$('cell-review'); detail.replaceChildren(); detail.hidden=!cell;
  if(cell) {
    const review=currentReview(cell.cell_id);
    if(state.scopeReady&&review) {
      if(state.focusTarget)detail.append(element('p',mapText('兼容细格复核：'+cellTitle(cell)+'。该记录不是新版专题的全部事件统计。','Legacy cell review: '+cellTitle(cell)+'. This record is not the event count for the entire scientific topic.'),'meta'));
      detail.append(element('h4',label('technical_analysis'))); field(detail,'highlight',review.highlight); field(detail,'samples',review.sample_count);
      detail.append(element('p',enumLabel('direction_',review.direction),'meta'));
      const more=element('details'); more.append(element('summary',label('review_details')));
      field(more,'change_kind',enumLabel('change_',review.change_kind)); field(more,'question',review.next_question); field(more,'review_status',enumLabel('status_',review.status)); detail.append(more);
    }
    else detail.append(element('p',label(state.scopeError?'scope_read_failed':state.scopeBusy?'loading':'no_scope')));
  }
  const parent=$('technique-cards'); parent.replaceChildren(); const rows=visibleTechniques();
  if(!rows.length)parent.append(element('p',label(state.cell||state.object||state.all?'no_candidates':'choose_help')));
  for(const row of rows) {
    const card=element('article','','card');card.dataset.techniqueId=row.technique_id; card.append(element('h3',title(row))); field(card,'mechanism',row.mechanism); field(card,'boundary',row.boundary); card.append(element('p',label(row.verification_status==='primary_mechanism_checked'?'mechanism_checked':'candidate'),'meta'));
    const actions=element('div','','actions');
    for(const reference of state.data.source_refs.filter(item=>item.technique_id===row.technique_id)){
      const source=sourceById(reference.source_id);external(actions,source?.canonical_url,label('primary_url'));
      field(card,'review_depth',enumLabel('depth_',reference.checked_scope));field(card,'checked_at',reference.checked_at);
    }
    if(row.source_document_id)actions.append(button(label('source_context'),()=>openDocument(row.source_document_id))); card.append(actions); parent.append(card);
  }
  renderDisclosureStatus();ensureOpenedDisclosuresLoaded();
}
function selectCell(id,view='topics') {
  if(!state.revision)return;state.focusTarget='';state.focusMechanism='';state.focusCells=[]; const cell=state.data.cells.find(row=>row.cell_id===id); must(Boolean(cell),'Unknown selected cell');
  state.cell=id; state.object=cell.object_id; state.method=cell.method_id; state.all=false; resetDetails(); resetEvidence();
  renderSelectors(); renderMap(); renderSelection(); controls(true); showView(view,true);
  if(view==='topics'){$('technique-disclosure').open=true;$('direction-detail').setAttribute('tabindex','-1');$('direction-detail').focus({preventScroll:true});$('direction-detail').scrollIntoView({block:'start'});}
  else{$('selection-title').setAttribute('tabindex','-1');$('selection-title').focus({preventScroll:true});}
  loadEvidence(0);
}
function renderMonthlyDirections() {
  const parent=$('monthly-directions'); parent.replaceChildren();parent.hidden=false;
  const targets=ordered(state.data.map_terms.filter(row=>row.facet_id==='target'&&!row.parent_term_id)),methods=ordered(state.data.map_terms.filter(row=>['mechanism','construction'].includes(row.facet_id)));
  const coverage=element('div','','topic-monthly-coverage');
  coverage.append(element('h4',state.period+mapText(' · 技术地图相关动态',' · Technology-map updates')),element('p',mapText("按压缩对象浏览已收录进展。跨对象的研究可关联多个专题，已审阅资料与待审阅候选分别展示。","Browse developments by compression target. Work spanning several targets may link to multiple topics; reviewed material and candidates are shown separately."),'meta'));
  if(state.scopeReady){const summary=element('div','','direction-stats');for(const target of targets){const rows=(state.topicScopeLinks||[]).filter(row=>row.compression_topic_id.startsWith(target.term_id+'-')),all=new Set(rows.map(row=>row.evidence_id)),reviewed=new Set(rows.filter(row=>row.review_status==='primary_review').map(row=>row.evidence_id));const card=element('div');card.append(element('strong',title(target)),element('span',all.size+mapText(' 项已收录 · ',' collected · ')+reviewed.size+mapText(' 项已审阅',' reviewed')));summary.append(card);}coverage.append(summary);}parent.append(coverage);
  const grid=element('div','','wb-direction-filters');
  for(const target of targets){const group=element('section');group.append(element('h4',title(target)));const ids=scientificTechniqueIds(target.term_id);for(const method of methods){if(!state.data.compression_topics?.some(row=>row.target_term_id===target.term_id&&row.method_term_id===method.term_id))continue;const select=button(title(method)+' · '+topicEventsFor(target.term_id+'-'+method.term_id).length,()=>{openScientificFocus(target.term_id,method.term_id,false);showView('updates',true);},true);select.dataset.monthlyScientific=target.term_id+'-'+method.term_id;select.setAttribute('aria-pressed',String(state.focusTarget===target.term_id&&state.focusMechanism===method.term_id));group.append(select);}grid.append(group);}parent.append(grid);
  const reset=button(mapText('清除技术筛选','Clear technical filter'),()=>{state.focusTarget='';state.focusMechanism='';state.focusCells=[];state.cell='';state.object='';state.method='';state.directionMode=false;state.all=true;resetEvidence();renderSelectors();renderMap();renderSelection();showView('updates',true);},true);parent.append(reset);
  if(state.cell)return;
  const legacy=disclosure('monthly-legacy-filter',mapText('旧版分类筛选','Legacy category filters'));parent.append(legacy);
  if(!state.scopeReady) { parent.append(element('p',label(state.scopeError?'scope_read_failed':state.scopeBusy?'loading':'no_scope'))); return; }
  const rows=ordered(state.data.cells).filter(cell=>!state.object||cell.object_id===state.object).map(cell=>({cell,review:currentReview(cell.cell_id)})).filter(row=>row.review?.sample_count>0);
  if(!rows.length) { parent.append(element('p',label('monthly_direction_gap'))); return; }
  const list=element('ul');
  // Canonical order preserves the taxonomy; sample counts are not a popularity ranking.
  for(const {cell,review} of rows) {
    const li=element('li'),select=button(cellTitle(cell),()=>selectCell(cell.cell_id,'updates'),true);
    select.dataset.monthlyCell=cell.cell_id; li.append(select,element('span',' — '+label('samples')+': '+review.sample_count)); list.append(li);
  }legacy.append(list);
}
function renderEvidence() {
  renderReadingContext();refreshSynthesis();
  if(!topicPage()&&state.scopeReady&&(!state.cell||Boolean(state.focusTarget)))globalThis.LRICompressionMonthly?.refresh({revision:state.revision,period:state.period,scope:state.scope,locale:state.locale,topicId:state.focusTarget?compressionTopicId():'',topics:state.data.compression_topics,associations:state.topicScopeLinks});
  else globalThis.LRICompressionMonthly?.reset();
  const parent=$('evidence-cards'); parent.replaceChildren(); $('evidence-retry').hidden=!(state.evidenceError||state.paperSummaryError);
  if(!state.scopeReady)$('evidence-status').textContent=label(state.scopeError?'scope_read_failed':state.scopeBusy?'loading':'no_scope');
  else if(state.evidenceBusy)$('evidence-status').textContent=state.evidenceProgress?label('related_read_progress')+' '+state.evidenceProgress.loaded+' / '+state.evidenceProgress.total:label('loading');
  else if(state.evidenceError)$('evidence-status').textContent=label(state.cell?'evidence_read_failed':'related_read_failed');
  else if(!state.evidence.length)$('evidence-status').textContent=state.focusTarget?mapText("本月暂未收录该专题的相关进展，可切换月份；专题中的原理与代表文献仍可阅读。","No related developments have been collected for this topic this month. Try another month; principles and representative papers remain available."):label(state.cell?'no_evidence_samples':'related_scope_empty');
  else $('evidence-status').textContent=(state.evidenceOffset+1)+'–'+(state.evidenceOffset+state.evidence.length)+' / '+state.evidencePage.total+' · '+label('evidence_events')+' · '+label('related_scope_only');
  const papers=state.evidence.filter(row=>/^https:\/\/arxiv\.org\/abs\//.test(row.source.canonical_url)),summarized=papers.filter(row=>row.paperSummary).length;
  $('paper-summary-status').textContent=state.paperSummaryError?label('paper_summary_failed')+' · '+state.paperSummaryError:papers.length?label('paper_summary_page')+' '+summarized+' / '+papers.length+' · '+label('paper_summary_order'):'';
  $('paper-summary-status').setAttribute('role',state.paperSummaryError?'alert':'status');
  for(const {placement,placements=[placement],item,source,paperSummary,summaryKeywords=[],topicBinding} of state.evidence) {
    const card=element('article','','card monthly-research-card');
    const mechanismHead=paperSummary?textOf(paperSummary,'innovation').split(/[；;。]/)[0]:'';
    const paperName=ordered(summaryKeywords).map(row=>textOf(row,'keyword'))[0]||'';
    card.dataset.evidenceId=item.evidence_id;card.dataset.reviewed=String(Boolean(paperSummary));
    card.append(element('h3',paperSummary?(paperName+'｜'+(mechanismHead.length>70?mechanismHead.slice(0,70)+'…':mechanismHead)):(source.title||source.canonical_url)));
    card.append(element('p',enumLabel('date_',item.date_kind)+' · '+(item.event_date||label('pending'))+(item.observed_version?' · '+item.observed_version:''),'meta'),element('p',paperSummary?enumLabel('paper_review_',paperSummary.review_status):enumLabel('status_',item.status),'meta'));
    const nativeTopics=(state.topicScopeLinks||[]).filter(row=>row.evidence_id===item.evidence_id);const topicTags=element('div','','direction-neighbors');for(const binding of nativeTopics){const topic=state.data.compression_topics.find(row=>row.compression_topic_id===binding.compression_topic_id);if(topic){const link=scientificLink(topic.target_term_id,topic.method_term_id,title(topic));link.dataset.evidenceTopic=topic.compression_topic_id;topicTags.append(link);}}if(nativeTopics.length)card.append(topicTags);
    if(topicBinding)card.append(element('p',(topicBinding.review_status==='primary_review'?'原文审阅后关联':'待审阅候选 · 标题 / 旧版本线索')+' · '+topicBinding.association_note,'topic-binding-label'+(topicBinding.review_status==='title_candidate'?' is-candidate':'')));
    const cellIds=new Set(placements.map(link=>link.cell_id));
    const isPaper=/^https:\/\/arxiv\.org\/abs\//.test(source.canonical_url);
    if(paperSummary) {
      const sentence=field(card,'paper_one_sentence',textOf(paperSummary,'one_sentence'));sentence.className='monthly-one-sentence';
      const cite=element('a',' ['+source.canonical_url.split('/').at(-1).replace(/v\d+$/,'')+paperSummary.observed_version+']');cite.href=safeUrl(paperSummary.evidence_url);cite.target='_blank';cite.rel='noopener noreferrer';cite.setAttribute('aria-label',label('paper_citation')+' '+paperSummary.observed_version);sentence.append(cite);
      field(card,'paper_keywords',ordered(summaryKeywords).map(row=>textOf(row,'keyword')).join(' · '));
      const read=disclosure('paper-'+paperSummary.summary_id,label('paper_read_more'));
      field(read,'paper_background',textOf(paperSummary,'background')).className='monthly-fact-field';
      field(read,'paper_innovation',textOf(paperSummary,'innovation')).className='monthly-fact-field';
      field(read,'paper_results',textOf(paperSummary,'results')).className='monthly-fact-field';
      read.append(element('p',enumLabel('paper_review_',paperSummary.review_status)+' · '+paperSummary.observed_version+' · '+paperSummary.reviewed_at+' · '+paperSummary.evidence_locator,'meta'));
      external(read,paperSummary.evidence_url,label('paper_review_source'));card.append(read);
    } else if(isPaper)card.append(element('p',label(state.paperSummaryError?'paper_summary_unavailable':'paper_summary_pending'),'meta'));
    else {
      field(card,item.status==='public_metadata_candidate'?'candidate_classification':'mechanism',[...new Set(placements.map(link=>link.mechanism_summary).filter(Boolean))].join('\n'));

    }
    const actions=element('div','','actions'); external(actions,source.canonical_url,label('primary_url')); if(item.source_document_id)actions.append(button(label('source_context'),()=>openDocument(item.source_document_id))); card.append(actions); parent.append(card);
    const more=element('details'); more.append(element('summary',label('evidence_details')));
    const legacyTags=element('p');legacyTags.append(element('strong',mapText('历史索引标签（待按文献分类复核）：','Historical index labels (pending literature classification review): ')),document.createTextNode(ordered(state.data.cells).filter(cell=>cellIds.has(cell.cell_id)).map(cellTitle).join(' · ')));if(cellIds.size)more.append(legacyTags);if(topicBinding){more.append(element('p',topicBinding.association_note));external(more,topicBinding.classification_basis,'专题归类依据 →');}
    field(more,item.status==='public_metadata_candidate'?'candidate_classification':'mechanism',[...new Set(placements.map(link=>link.mechanism_summary).filter(Boolean))].join('\n'));
    field(more,'boundary',[...new Set(placements.map(link=>link.limitation).filter(Boolean))].join('\n'));
    field(more,'paper_original_title',source.title||source.canonical_url);
    field(more,'evidence_status',enumLabel('status_',item.status)); field(more,'provenance_kind',enumLabel('provenance_',item.provenance_kind));
    field(more,'date_kind',enumLabel('date_',item.date_kind)); field(more,item.date_kind==='source_declared_date'?'publication_date_unverified':'publication_date',item.publication_date); field(more,'event_date',item.event_date); field(more,'date_precision',enumLabel('precision_',item.date_precision)); field(more,'observed_version',item.observed_version);
    field(more,item.status==='public_metadata_candidate'?'metadata_checked_at':'verified_at',item.verified_at); field(more,'source_revision',item.source_revision);
    for(const link of placements) {
      field(more,'stage',cellTitle(state.data.cells.find(cell=>cell.cell_id===link.cell_id))+' · '+enumLabel('stage_',link.stage));
      field(more,'placement_status',enumLabel('status_',link.status)); field(more,'question',link.validation_question);
    }card.append(more);
  }controls(Boolean(state.revision));
}
function validateEvidenceLink(row,scope,period) {
  must(row.scope_id===scope&&row.period_id===period&&typeof row.evidence_id==='string'&&row.evidence_id&&typeof row.link_id==='string'&&row.link_id&&state.data.cells.some(cell=>cell.cell_id===row.cell_id)&&row.scope_cell_key===scope+'__'+row.cell_id,'Invalid evidence placement scope');
  // TableGit stages are descriptive text, including "prefill/decode" and
  // profiling-to-deployment descriptions; reject empty and training-only rows.
  must(typeof row.stage==='string'&&row.stage.trim().length>0&&row.stage.length<=200&&!['training','training_only'].includes(row.stage.trim().toLowerCase().replace(/[ -]+/g,'_')),'Invalid inference evidence stage');
}
function validateEvidenceRevision(result,revision) {
  if(result.revision!==undefined)must(result.revision===revision,'Evidence revision mismatch');
}

// Reviews are independent of candidate metadata and tied to the observed version.
// Failure in this optional layer must not erase the underlying event list.
async function paperSummaryIndex(revision,period) {
  if(state.paperIndexCache?.revision===revision&&state.paperIndexCache.period===period)return state.paperIndexCache.index;
  const index=new Map();let offset=0,total=null;
  for(;;) {
    const result=await page('paper_summary_events','period_id',period,revision,{offset,limit:100});validateEvidenceRevision(result,revision);
    const meta=result.page;
    must(meta&&Number.isSafeInteger(meta.total)&&meta.total>=0&&meta.total<=2000&&typeof meta.truncated==='boolean'&&Array.isArray(result.records)&&result.records.length<=100,'Invalid paper-summary index page');
    if(total===null)total=meta.total;else must(total===meta.total,'Paper-summary index total changed');
    must(meta.offset===undefined||meta.offset===offset,'Paper-summary index offset drift');
    for(const row of result.records) {
      must(row.period_id===period&&row.evidence_id&&row.source_id&&/^v\d+$/.test(row.observed_version)&&row.summary_id===row.source_id+'__'+row.observed_version&&!index.has(row.evidence_id),'Invalid or repeated paper-summary binding');
      index.set(row.evidence_id,row);
    }
    must(index.size<=total&&meta.truncated===(index.size<total)&&(result.records.length>0||total===0),'Incomplete paper-summary index');
    if(!meta.truncated)break;
    must(Number.isSafeInteger(meta.nextOffset)&&meta.nextOffset===offset+result.records.length&&meta.nextOffset>offset,'Invalid paper-summary index cursor');offset=meta.nextOffset;
  }
  state.paperIndexCache={revision,period,index};return index;
}
async function hydratePaperSummaries(evidence,revision,index) {
  const bindings=evidence.map(row=>index.get(row.item.evidence_id)).filter(Boolean),ids=[...new Set(bindings.map(row=>row.summary_id))];
  if(!ids.length)return evidence;
  for(const row of evidence) {
    const binding=index.get(row.item.evidence_id);if(!binding)continue;
    must(binding.source_id===row.item.source_id&&binding.observed_version===row.item.observed_version&&binding.period_id===row.item.event_date.slice(0,7),'Paper-summary event version mismatch');
  }
  const result=await LRITableGit.loadRowsByKeys('ic_paper_summaries',ids,revision);validateEvidenceRevision(result,revision);assertBusiness(result.records);
  must(result.records.length===ids.length&&new Set(result.records.map(row=>row.summary_id)).size===ids.length&&result.records.every(row=>ids.includes(row.summary_id)),'Missing paper-summary record');
  const summaries=new Map(result.records.map(row=>[row.summary_id,row]));
  for(const row of result.records) {
    must(row.summary_id===row.source_id+'__'+row.observed_version&&Number.isSafeInteger(row.keyword_count)&&row.keyword_count>=1&&row.keyword_count<=8&&['primary_abstract_checked','method_results_checked'].includes(row.review_status),'Invalid paper-summary review contract');
    for(const key of ['one_sentence','background','innovation','results'])must(typeof row[key+'_zh']==='string'&&row[key+'_zh'].trim(),'Incomplete paper-summary text');
    safeUrl(row.evidence_url);must(row.evidence_locator&&/^\d{4}-\d{2}-\d{2}$/.test(row.reviewed_at),'Missing paper-summary provenance');
  }
  const keywordIds=result.records.flatMap(row=>Array.from({length:row.keyword_count},(_,i)=>row.summary_id+'__'+i));
  const keywords=await LRITableGit.loadRowsByKeys('ic_paper_summary_keywords',keywordIds,revision);validateEvidenceRevision(keywords,revision);assertBusiness(keywords.records);
  must(keywords.records.length===keywordIds.length&&new Set(keywords.records.map(row=>row.keyword_id)).size===keywordIds.length,'Missing paper-summary keywords');
  for(const row of keywords.records)must(summaries.has(row.summary_id)&&keywordIds.includes(row.keyword_id)&&Number.isSafeInteger(row.position)&&row.position>=0&&row.position<summaries.get(row.summary_id).keyword_count&&row.keyword_id===row.summary_id+'__'+row.position&&typeof row.keyword_zh==='string'&&row.keyword_zh.trim(),'Invalid paper-summary keyword');
  return evidence.map(row=>{const binding=index.get(row.item.evidence_id);if(!binding)return row;const summary=summaries.get(binding.summary_id);must(summary.source_id===row.item.source_id&&summary.observed_version===row.item.observed_version,'Paper-summary source mismatch');return {...row,paperSummary:summary,summaryKeywords:keywords.records.filter(word=>word.summary_id===summary.summary_id)};});
}
function summaryReadError(error) { return String(error.message||error).replace(/https?:\/\/\S+/g,'[URL]').slice(0,200); }

async function loadRelatedEvidence(offset=0) {
  if(!state.revision||!state.scopeReady||(state.cell&&!state.focusCells.length))return;
  const request=++state.evidenceEpoch,revision=state.revision,scope=state.scope,period=state.period,object=state.object,focusKey=JSON.stringify(state.focusCells);
  const active=()=>request===state.evidenceEpoch&&revision===state.revision&&scope===state.scope&&period===state.period&&object===state.object&&focusKey===JSON.stringify(state.focusCells)&&(!state.cell||state.focusCells.length>0)&&state.scopeReady;
  state.evidenceBusy=true; state.evidenceError=false; state.paperSummaryError=''; state.evidence=[]; state.evidencePage=null; state.evidenceOffset=offset; state.evidenceProgress=null; renderEvidence();
  try {
    must(Number.isSafeInteger(offset)&&offset>=0,'Invalid evidence event offset');
    must(!object||state.data.objects.some(row=>row.object_id===object),'Unknown evidence object');
    let links=state.relatedCache?.revision===revision&&state.relatedCache.scope===scope&&state.relatedCache.period===period?state.relatedCache.links:null;
    if(!links) {
      links=[]; let cursor=0,total=null; const seen=new Set();
      for(;;) {
        const result=await page('monthly_evidence_cells','scope_id',scope,revision,{offset:cursor,limit:100});
        if(!active())return; validateEvidenceRevision(result,revision);
        const meta=result.page;
        must(meta&&Number.isSafeInteger(meta.total)&&meta.total>=0&&typeof meta.truncated==='boolean'&&Array.isArray(result.records)&&result.records.length<=100,'Invalid scope evidence page');
        must(meta.total<=2000,'Scope evidence limit exceeded (2000)');
        if(total===null)total=meta.total; else must(meta.total===total,'Scope evidence total changed');
        if(meta.offset!==undefined)must(meta.offset===cursor,'Scope evidence offset drift');
        for(const link of result.records) { validateEvidenceLink(link,scope,period); must(!seen.has(link.link_id),'Repeated scope evidence placement'); seen.add(link.link_id); links.push(link); }
        must(links.length<=total&&(result.records.length>0||total===0),'Scope evidence pagination made no progress');
        state.evidenceProgress={loaded:links.length,total}; renderEvidence();
        must(meta.truncated===(links.length<total),'Incomplete scope evidence pagination');
        if(!meta.truncated) { must(links.length===total,'Incomplete scope evidence total'); break; }
        must(Number.isSafeInteger(meta.nextOffset)&&meta.nextOffset===cursor+result.records.length&&meta.nextOffset>cursor&&meta.nextOffset<total,'Invalid scope evidence pagination cursor');
        cursor=meta.nextOffset;
      }
      if(!active())return; state.relatedCache={revision,scope,period,links};
    }
    const grouped=new Map();
    for(const link of ordered(links)) {
      if(!grouped.has(link.evidence_id))grouped.set(link.evidence_id,{evidence_id:link.evidence_id,placements:[]});
      grouped.get(link.evidence_id).placements.push(link);
    }
    let paperIndex=null;
    try { paperIndex=await paperSummaryIndex(revision,period); }catch(error){if(!active())return;state.paperSummaryError=summaryReadError(error);}
    if(!active())return;
    const events=[...grouped.values()].filter(event=>state.focusCells.length?event.placements.some(link=>state.focusCells.includes(link.cell_id)):!object||event.placements.some(link=>state.data.cells.find(cell=>cell.cell_id===link.cell_id).object_id===object));
    if(paperIndex)events.sort((a,b)=>Number(paperIndex.has(b.evidence_id))-Number(paperIndex.has(a.evidence_id)));
    const selected=events.slice(offset,offset+20),ids=selected.map(event=>event.evidence_id);
    must(offset===0||offset<events.length,'Evidence event page is outside the selected scope');
    let evidence=[];
    if(ids.length) {
      const items=await LRITableGit.loadRowsByKeys('ic_evidence_items',ids,revision);
      if(!active())return; validateEvidenceRevision(items,revision); assertBusiness(items.records);
      must(items.records.length===ids.length&&new Set(items.records.map(row=>row.evidence_id)).size===ids.length&&items.records.every(row=>ids.includes(row.evidence_id)&&typeof row.source_id==='string'&&row.source_id),'Missing or mismatched evidence item');
      const sourceIds=[...new Set(items.records.map(row=>row.source_id))],sources=await LRITableGit.loadRowsByKeys('cloud_core_sources',sourceIds,revision,['source_id','business_id','title','canonical_url']);
      if(!active())return; validateEvidenceRevision(sources,revision);
      must(sources.records.length===sourceIds.length&&new Set(sources.records.map(row=>row.source_id)).size===sourceIds.length&&sources.records.every(row=>sourceIds.includes(row.source_id)&&row.business_id==='cloud-core'),'Missing or mismatched canonical source');
      const itemMap=new Map(items.records.map(row=>[row.evidence_id,row])),sourceMap=new Map(sources.records.map(row=>[row.source_id,row]));
      evidence=selected.map(event=>{const item=itemMap.get(event.evidence_id),source=sourceMap.get(item.source_id);safeUrl(source.canonical_url);return {placements:event.placements,placement:event.placements[0],item,source};});
    }
    if(!active())return;
    if(paperIndex)try { evidence=await hydratePaperSummaries(evidence,revision,paperIndex); }catch(error){if(!active())return;state.paperSummaryError=summaryReadError(error);}
    if(!active())return;
    state.evidence=evidence; state.evidencePage={total:events.length,offset,limit:20,truncated:offset+evidence.length<events.length,nextOffset:offset+evidence.length}; state.evidenceBusy=false; state.evidenceProgress=null; renderEvidence();
  } catch(error) { if(!active())return; if(fatal(error))fail(error); else { state.evidenceBusy=false; state.evidenceError=true; state.evidenceProgress=null; renderEvidence(); } }
}
async function loadEvidence(offset=0) {
  if(topicPage())return; // Period evidence belongs to the updates reader.
  if(!state.revision||!state.scopeReady)return;
  if(state.focusTarget)return loadCompressionTopicEvidence(offset);
  if(!state.cell&&!state.object&&state.data.compression_topics?.length&&Array.isArray(state.topicScopeLinks))return loadCompressionTopicEvidence(offset,true);
  if(!state.cell||state.focusCells.length)return loadRelatedEvidence(offset);
  const request=++state.evidenceEpoch,revision=state.revision,scope=state.scope,cell=state.cell,period=state.period,object=state.object;
  const active=()=>request===state.evidenceEpoch&&revision===state.revision&&scope===state.scope&&cell===state.cell&&period===state.period&&object===state.object&&state.scopeReady;
  state.evidenceBusy=true; state.evidenceError=false; state.paperSummaryError=''; state.evidence=[]; state.evidencePage=null; state.evidenceOffset=offset; renderEvidence();
  try {
    const result=await page('monthly_evidence_cells','scope_cell_key',scope+'__'+cell,revision,{offset,limit:20});
    if(!active())return; validateEvidenceRevision(result,revision);
    must(result.records.every(row=>row.scope_id===scope&&row.period_id===period&&row.cell_id===cell&&row.scope_cell_key===scope+'__'+cell),'Invalid evidence placement scope');
    for(const link of result.records)validateEvidenceLink(link,scope,period);
    const ids=[...new Set(result.records.map(row=>row.evidence_id))],items=await LRITableGit.loadRowsByKeys('ic_evidence_items',ids,revision); assertBusiness(items.records); must(items.records.length===ids.length,'Missing evidence item');
    if(!active())return; validateEvidenceRevision(items,revision); must(new Set(items.records.map(row=>row.evidence_id)).size===ids.length&&items.records.every(row=>ids.includes(row.evidence_id)&&typeof row.source_id==='string'&&row.source_id),'Mismatched evidence item');
    const sourceIds=[...new Set(items.records.map(row=>row.source_id))],sources=await LRITableGit.loadRowsByKeys('cloud_core_sources',sourceIds,revision,['source_id','business_id','title','canonical_url']);
    if(!active())return; validateEvidenceRevision(sources,revision);
    must(sources.records.length===sourceIds.length&&sources.records.every(row=>row.business_id==='cloud-core'),'Missing canonical source');
    must(new Set(sources.records.map(row=>row.source_id)).size===sourceIds.length&&sources.records.every(row=>sourceIds.includes(row.source_id)),'Mismatched canonical source');
    const itemMap=new Map(items.records.map(row=>[row.evidence_id,row])),sourceMap=new Map(sources.records.map(row=>[row.source_id,row]));
    let evidence=result.records.map(placement=>{ const item=itemMap.get(placement.evidence_id),source=sourceMap.get(item.source_id); safeUrl(source.canonical_url); return {placement,item,source}; });
    if(request!==state.evidenceEpoch||revision!==state.revision||scope!==state.scope||cell!==state.cell||period!==state.period||object!==state.object)return;
    try { const index=await paperSummaryIndex(revision,period);if(!active())return;evidence=await hydratePaperSummaries(evidence,revision,index); }catch(error){if(!active())return;state.paperSummaryError=summaryReadError(error);}
    if(!active())return;
    state.evidence=evidence; state.evidencePage=result.page; state.evidenceBusy=false; renderEvidence();
  }catch(error) { if(!active())return; if(fatal(error))fail(error); else { state.evidenceBusy=false; state.evidenceError=true; renderEvidence(); } }
}
function validateReviews(records,scope,period) {
  const cells=new Set(state.data.cells.map(row=>row.cell_id));
  must(records.length===cells.size&&new Set(records.map(row=>row.cell_id)).size===cells.size,'Monthly scope must cover canonical cells exactly once');
  for(const row of records)must(row.scope_id===scope&&row.period_id===period&&cells.has(row.cell_id)&&row.scope_cell_key===scope+'__'+row.cell_id&&Number.isSafeInteger(row.sample_count)&&row.sample_count>=0,'Invalid monthly review scope');
  return ordered(records);
}
async function scopeRows(period,revision) { const result=await page('monthly_scopes','period_id',period,revision); must(!result.page.truncated&&result.records.every(row=>row.period_id===period),'Invalid monthly scope list'); return ordered(result.records); }
async function reviewRows(scope,period,revision) { const result=await page('monthly_cell_reviews','scope_id',scope,revision); must(!result.page.truncated,'Monthly review pagination requires repair'); return validateReviews(result.records,scope,period); }
async function loadScope(scope=state.scope) {
  if(!state.revision||!scope)return; const request=++state.scopeEpoch,revision=state.revision,period=state.period;
  state.scope=scope; state.topicScopeLinks=[];state.scopeReady=false; state.scopeBusy=true; state.scopeError=false; state.reviews=[]; resetEvidence(); resetDetails(); renderSelectors(); renderScope(); renderMap(); renderSelection(); controls(true);
  try {
    const [records,topicLinks]=await Promise.all([reviewRows(scope,period,revision),topicScopeRows(scope,period,revision)]);
    if(request!==state.scopeEpoch||revision!==state.revision||scope!==state.scope||period!==state.period)return;
    state.reviews=records;state.topicScopeLinks=topicLinks;state.scopeReady=true;persistTopicScope(); state.scopeBusy=false; renderScope(); renderMap(); renderSelection(); controls(true); await loadEvidence(0);
  }catch(error) { if(request!==state.scopeEpoch||revision!==state.revision)return; if(fatal(error))fail(error); else { state.scopeBusy=false; state.scopeError=true; renderScope(); controls(true); } }
}
async function loadPeriod(period=state.period,preferredScope='') {
  if(!state.revision||!period)return; const request=++state.periodEpoch,revision=state.revision;
  state.scopeEpoch++; state.legacyEpoch++; state.period=period; state.scope=''; state.scopes=[]; state.reviews=[]; state.scopeReady=false; state.scopeBusy=true; state.scopeError=false; state.legacy=[]; state.legacyPeriod=''; state.legacyBusy=false; $('monthly-rows').replaceChildren(); $('legacy-status').textContent=''; resetEvidence(); resetDetails(); renderSelectors(); renderScope(); renderMap(); renderSelection(); controls(true);
  try {
    const scopes=await scopeRows(period,revision);
    if(request!==state.periodEpoch||revision!==state.revision||period!==state.period)return;
    state.scopes=scopes; state.scopeBusy=false; state.scope=scopes.some(row=>row.scope_id===preferredScope)?preferredScope:scopes[0]?.scope_id||'';
  if(state.readerMode==='sources'){renderViewPurpose();renderChannels();if(!state.sourceStatusError)$('runtime-status').textContent=mapText('当前分类信源已加载 · 其他类别按需读取','Current source category ready · Other categories load on demand');return;}
  renderSelectors(); renderScope(); controls(true); if(state.scope)await loadScope(state.scope);
  }catch(error) { if(request!==state.periodEpoch||revision!==state.revision)return; if(fatal(error))fail(error); else { state.scopeBusy=false; state.scopeError=true; renderScope(); controls(true); } }
}
async function chooseDefaultPeriod(revision,request) {
  const periods=[...state.data.trend_periods].sort((a,b)=>b.month.localeCompare(a.month));
  for(const period of periods.filter(row=>!/template|uncollected/i.test(row.source_status))) {
    const scopes=await scopeRows(period.period_id,revision); if(request!==state.epoch)return '';
    for(const scope of scopes) { const reviews=await reviewRows(scope.scope_id,period.period_id,revision); if(request!==state.epoch)return null; if(reviews.some(row=>row.sample_count>0))return {period:period.period_id,scope:scope.scope_id}; }
  }return {period:'',scope:''};
}
function renderLegacy() {
  const body=$('monthly-rows'); body.replaceChildren();
  const visible=state.data.cells.filter(cell=>(!state.object||cell.object_id===state.object)&&state.legacy.some(row=>row.cell_id===cell.cell_id));
  $('legacy-table').hidden=state.legacyBusy||visible.length===0;
  for(const cell of visible) {
    const row=state.legacy.find(item=>item.cell_id===cell.cell_id),tr=element('tr'),heading=element('th',cellTitle(cell)); heading.scope='row'; tr.append(heading);
    for(const key of ['month_start_count','month_end_count','monthly_added_count','growth_rate','accepted_count','github_added_count','stars_score'])tr.append(element('td',row?.[key]??'—'));
    tr.append(element('td',row?[row.trend_change||'—',row.status,row.review_note].filter(Boolean).join(' · '):label('pending'))); body.append(tr);
  }
  $('legacy-status').textContent=label(state.legacyBusy?'loading':state.legacyPeriod?(state.legacy.length?'observations_boundary':'legacy_empty_help'):'legacy_not_loaded');
}
async function loadLegacy() {
  if(!state.revision)return; const request=++state.legacyEpoch,revision=state.revision,period=state.period; state.legacyBusy=true; state.legacy=[]; renderLegacy();
  try {
    const result=await page('trend_observations','period_id',period,revision);
    const cells=new Set(state.data.cells.map(row=>row.cell_id));
    must(!result.page.truncated&&result.records.every(row=>row.period_id===period&&cells.has(row.cell_id))&&new Set(result.records.map(row=>row.cell_id)).size===result.records.length,'Invalid legacy observation scope');
    if(request!==state.legacyEpoch||revision!==state.revision||period!==state.period)return; state.legacy=result.records; state.legacyPeriod=period; state.legacyBusy=false; renderLegacy();
  }catch(error) { if(request!==state.legacyEpoch||revision!==state.revision)return; if(fatal(error))fail(error); else { state.legacyBusy=false; $('legacy-status').textContent=label('scope_read_failed'); } }
}
function renderTasks() {
  const stages=state.data.flywheel_stages; $('flywheel-path').textContent=stages.map(title).join(' → ')+(stages.length?' → '+title(stages[0]):'');
  const rules=$('flywheel-rules'); rules.replaceChildren(); for(const row of stages) { const li=element('li'); li.append(element('strong',title(row))); field(li,'entry',row.entry_rule); field(li,'exit',row.exit_rule); rules.append(li); }
  const parent=$('task-cards'); parent.replaceChildren(); for(const row of state.data.tasks) { const card=element('article','','card'); card.append(element('h3',title(row))); field(card,'question',row.question||row.hypothesis); field(card,'test_design',row.validation_plan||row.validation_contract); field(card,'metrics',row.metrics); field(card,'acceptance',row.acceptance_rule); card.append(element('p',label('proposed'),'meta')); parent.append(card); }
  $('measurement-status').textContent=label(state.data.measurementCount||state.data.decisionCount?'measurements_boundary':'no_measurements');
  const contract=$('benchmark-contract'); contract.replaceChildren(); for(const row of state.data.evaluation_dimensions)field(contract,title(row),row.contract);
}
function renderNotes() { const parent=$('review-notes'); parent.replaceChildren(); for(const row of state.data.review_notes) { const p=element('p'); p.append(element('strong',title(row)+': '),document.createTextNode(row.resolution||row.rule||row.detail||'')); parent.append(p); } }
function renderDocument(navigate=true) {
  if(!state.document)return; const row=state.document,detail=$('document-detail'),close=button(label('close'),()=>{state.detailEpoch++;state.document=null;detail.hidden=true;detail.replaceChildren();});
  detail.replaceChildren(close,element('h3',row.title),element('p',label('source_only'),'reader-note'),element('p',mapText("以下为历史笔记原文，其中统计、实验结果与观点尚需结合原始来源复核。","The following are original historical notes. Statistics, experimental results and interpretations still require review against their primary sources."),'direction-note'),element('pre',row.body)); detail.hidden=false; if(navigate)showView('reports',true);
}
function renderReadingContext() {
  const parent=$('reading-context');if(!state.profile){parent.textContent=label('loading');return;}
  const period=state.data.trend_periods.find(row=>row.period_id===state.period),scope=currentScope(),cell=currentCell();
  const object=state.data.objects.find(row=>row.object_id===state.object);
  const focus=scientificFocusTitle()||(cell?cellTitle(cell):object?title(object):label('all_directions'));
  const count=state.scopeReady&&state.evidencePage?state.evidencePage.total:state.scopeReady?mapText('按需读取本期事件','Read current events on demand'):label(state.scopeBusy?'loading':'pending');
  parent.textContent=label('period')+': '+(period?.month||label('pending'))+' · '+label('reading_focus')+': '+focus+' · '+label('registered_items')+': '+count+' · '+label('collected_at')+': '+(scope?.collected_at||label('pending'));
}
function renderDisclosureStatus() {
  if(!state.profile)return;
  const summary=(id,key,value)=>{const node=$(id)?.querySelector('summary');if(node)node.textContent=label(key)+' · '+value;};
  const count=n=>n+' '+label('entries_unit');
  summary('source-collection-details','actual_source_screening',count(state.data.source_scans.length));
  summary('representative-routes','historical_lineages',count(visibleLineages().length));
  summary('technique-disclosure','related_techniques',count(visibleTechniques().length));
  summary('current-source-readings','checked_source_details',count(visibleFindings(true).length));
  summary('scope-disclosure','scope_contract',label(state.scopeReady?'ready':state.scopeBusy?'loading':'no_scope'));
  summary('source-panel','source_documents',count(relevantDocumentIds().length)+(state.documentPending?' · '+label('loading'):''));
  summary('legacy-panel','legacy_statistics',label(state.legacyBusy?'loading':state.legacyPeriod?(state.legacy.length?'ready':'no_comparable_snapshots'):'expand_to_load'));
  summary('task-disclosure','suggested_tasks',count(state.data.tasks.length));
  summary('benchmark-disclosure','contract',count(state.data.evaluation_dimensions.length));
  summary('flywheel-disclosure','flywheel_rules',count(state.data.flywheel_stages.length));
  summary('governance-disclosure','governance',count(state.data.review_notes.length));
  if(state.documentListKey)$('document-status').textContent=$('document-list').children.length?$('document-list').children.length+' · '+label('source_only'):label('documents_empty_help');
  else if(!state.documentPending&&!$('document-status').textContent)$('document-status').textContent=label('documents_expand_help');
}
function documentContextKey() { return JSON.stringify([state.revision,state.object,state.cell,relevantDocumentIds().sort()]); }
async function loadExpandedDocuments(force=false) {
  if(!$('source-panel').open)return;
  if(!state.revision){$('document-status').textContent=label('loading');return;}
  const key=documentContextKey();
  if(!force&&state.documentListKey===key)return;
  if(state.documentPending?.key===key&&state.documentPending.ticket===state.listEpoch)return state.documentPending.promise;
  const promise=loadDocuments(),pending={key,ticket:state.listEpoch,promise};state.documentPending=pending;renderDisclosureStatus();
  try {await promise;if(pending.ticket===state.listEpoch&&key===documentContextKey()&&($('document-list').children.length||!relevantDocumentIds().length))state.documentListKey=key;}
  finally {if(state.documentPending===pending)state.documentPending=null;renderDisclosureStatus();}
}
async function loadExpandedLegacy(force=false) {
  if(!$('legacy-panel').open)return;
  if(!state.revision||!state.period){$('legacy-status').textContent=label(state.revision?'no_scope':'loading');return;}
  if(state.legacyBusy)return;
  if(!force&&state.legacyPeriod===state.period){renderLegacy();renderDisclosureStatus();return;}
  await loadLegacy();renderDisclosureStatus();
}
function ensureOpenedDisclosuresLoaded() {
  if($('source-panel').open)loadExpandedDocuments();
  if($('legacy-panel').open)loadExpandedLegacy();
}
function render() {
  document.querySelectorAll('[data-i18n-aria-label]').forEach(node=>node.setAttribute('aria-label',label(node.dataset.i18nAriaLabel)));
  if(!state.profile){if(state.directoryReady)renderChannels();return;} $('topic-title').textContent=state.profile['payload_'+state.locale].title; $('topic-summary').textContent=state.profile['payload_'+state.locale].summary;
  renderSelectors(); renderScope(); renderMap(); renderSelection(); renderEvidence(); if(state.legacyPeriod||state.legacyBusy)renderLegacy(); renderChannels(); renderSourceScans(); renderAscend(); renderTasks(); renderNotes(); renderReports(); renderDocument(false); showView(state.view);
  $('runtime-status').textContent=label('snapshot_ready'); controls(true);renderReadingContext();renderDisclosureStatus();ensureOpenedDisclosuresLoaded();
}
function relevantDocumentIds() {
  const filtered=state.cell||state.object,rows=filtered?visibleTechniques():state.data.techniques,ids=rows.map(row=>row.source_document_id).filter(Boolean);
  ids.push(...state.evidence.map(row=>row.item.source_document_id).filter(Boolean)); if(!filtered)ids.push(...state.data.review_notes.map(row=>row.source_document_id),...state.data.trend_periods.map(row=>row.source_document_id));
  return [...new Set(ids)].filter(Boolean);
}
async function loadDocuments() {
  if(!state.revision)return; resetDetails(); const request=++state.listEpoch,revision=state.revision; $('document-status').textContent=label('loading');
  try { const ids=relevantDocumentIds(); if(!ids.length){$('document-status').textContent=label('no_candidates');return;}
    const result=await LRITableGit.loadRowsByKeys('cloud_core_documents',ids,revision,['document_id','business_id','title','review_status','logical_path']);
    if(request!==state.listEpoch||revision!==state.revision)return; must(result.records.length===ids.length&&result.records.every(row=>row.business_id==='cloud-core'),'Missing source document');
    const list=$('document-list'); list.replaceChildren(); for(const row of result.records){const p=element('p');p.append(button(row.title,()=>openDocument(row.document_id)));list.append(p);} $('document-status').textContent=String(result.records.length)+' · '+label('source_only');
  }catch(error){if(request!==state.listEpoch||revision!==state.revision)return;if(fatal(error))fail(error);else $('document-status').textContent=label('read_failed');}
}
async function openDocument(id) {
  if(!state.revision)return; const request=++state.detailEpoch,revision=state.revision,detail=$('document-detail'); state.document=null; detail.hidden=true; detail.replaceChildren();
  try { const result=await LRITableGit.loadRowsByKeys('cloud_core_documents',[id],revision);
    if(request!==state.detailEpoch||revision!==state.revision)return; const row=result.records[0]; must(result.records.length===1&&row.business_id==='cloud-core'&&typeof row.body==='string','Missing source document');
    state.document=row; renderDocument(); detail.scrollIntoView({block:'start'});
  }catch(error){if(request!==state.detailEpoch||revision!==state.revision)return;if(fatal(error))fail(error);else $('document-status').textContent=label('read_failed');}
}
async function loadSourcePreview(request,revision) {
  const group=state.domain;
  if(group!=='hotspot')return; // Other groups retain their complete ecosystem contract.
  const read=async(table)=>{const result=await LRITableGit.loadTablePage(table,{filterField:'ui_group',filterValue:group,expectedRevision:revision,offset:0,limit:100});validateEvidenceRevision(result,revision);must(!result.page.truncated&&result.records.every(row=>row.ui_group===group),'Incomplete source preview');assertBusiness(result.records);return result.records;};
  const [channels,families]=await Promise.all([read('ic_channels'),read('ic_source_families')]);
  if(request!==state.epoch)return;
  const memberships=await LRITableGit.loadRowsByValues('ic_channel_families','family_id',families.map(row=>row.family_id),revision);
  validateEvidenceRevision(memberships,revision);assertBusiness(memberships.records);
  const ids=[...new Set(channels.map(row=>row.source_id))],sources=await LRITableGit.loadRowsByKeys('cloud_core_sources',ids,revision,['source_id','business_id','canonical_url','title','external_id']);
  if(request!==state.epoch)return;validateEvidenceRevision(sources,revision);
  must(sources.records.length===ids.length&&new Set(sources.records.map(row=>row.source_id)).size===ids.length&&sources.records.every(row=>row.business_id==='cloud-core'&&ids.includes(row.source_id)&&row.title),'Missing preview canonical source');
  for(const source of sources.records)safeUrl(source.canonical_url);
  const data={...Object.fromEntries(collectionNames.map(name=>[name,[]])),...Object.fromEntries(directoryNames.map(name=>[name,[]])),channels,source_families:families,channel_families:memberships.records,primarySources:sources.records,legacyChannels:[],ascendAssessments:[],collection_runs:[],collection_retrievals:[],collection_run_id:'',measurementCount:0,decisionCount:0};
  LRIGroupedSources.validate(data);
  state.data=data;state.revision=revision;state.directoryReady=true;state.directoryPartial=true;
  renderChannels();$('runtime-status').textContent=mapText('信源已显示，正在补充完整目录与采集状态…','Sources available; completing the catalog and collection status…');
  (globalThis.LRICloudFirstRetire?.(),performance.mark('cloud-core-source-content'));
}

async function loadDirectory(request) {
  $('runtime-status').textContent=label('directory_loading');
  const deferred=!topicPage()&&(document.body.dataset.compressionMonthly==='true'||state.view!=='sources');state.directoryDeferred=deferred;
  const metadata=await LRITableGit.loadTableMetadata(topicPage()||deferred?'ic_compression_topics':'ic_channels');if(request!==state.epoch)return null;
  const revision=metadata.revision;
  if(!topicPage()&&!deferred)await loadSourcePreview(request,revision);
  if(request!==state.epoch)return null;
  const rows=topicPage()||deferred?directoryNames.map(()=>[]):await boundedRead(directoryNames,name=>loadCatalog(name,revision));if(request!==state.epoch)return null;
  const data={...Object.fromEntries(collectionNames.map(name=>[name,[]])),...Object.fromEntries(directoryNames.map((name,i)=>[name,rows[i]])),legacyChannels:[],ascendAssessments:[],primarySources:[],collection_runs:[],collection_retrievals:[],collection_run_id:'',measurementCount:0,decisionCount:0};
  validateResearch(data); LRIGroupedSources.validate(data);
  const ids=[...new Set(data.channels.map(row=>row.source_id))],sources=await LRITableGit.loadRowsByKeys('cloud_core_sources',ids,revision,['source_id','business_id','canonical_url','title','external_id']);
  if(request!==state.epoch)return null;validateEvidenceRevision(sources,revision);
  must(sources.records.length===ids.length&&new Set(sources.records.map(row=>row.source_id)).size===ids.length&&sources.records.every(row=>row.business_id==='cloud-core'&&ids.includes(row.source_id)&&typeof row.title==='string'&&row.title),'Missing canonical channel source');
  for(const source of sources.records)safeUrl(source.canonical_url);
  data.primarySources=sources.records;state.data=data;state.revision=revision;state.directoryReady=!deferred;state.directoryPartial=false;state.directoryData=data;state.directoryRevision=revision;$('topic-title').textContent=label('eyebrow');
  renderChannels();if(!deferred)(globalThis.LRICloudFirstRetire?.(),performance.mark('cloud-core-source-content'));$('runtime-status').textContent=label('directory_ready');$('reading-context').textContent=label('directory_ready');
  return data;
}
async function topicRows(table,revision) {
  const rows=[];let offset=0;
  for(;;){const result=await LRITableGit.loadTablePage(table,{filterField:'topic_id',filterValue:'cloud_core',expectedRevision:revision,offset,limit:100});validateEvidenceRevision(result,revision);
    must(result.records.every(row=>row.topic_id==='cloud_core'),'Cross-topic workbench row');rows.push(...result.records);must(rows.length<=1000,'Topic workbench row limit exceeded');
    if(!result.page.truncated)return rows;must(result.records.length>0&&result.page.nextOffset===offset+result.records.length,'Invalid topic workbench cursor');offset=result.page.nextOffset;
  }
}
// Read only the active source category; research and historical audits are demand-loaded.
function emptyReaderData(){return {...Object.fromEntries(collectionNames.map(name=>[name,[]])),...Object.fromEntries(directoryNames.map(name=>[name,[]])),legacyChannels:[],ascendAssessments:[],primarySources:[],collection_runs:[],collection_retrievals:[],collection_run_id:'',measurementCount:0,decisionCount:0};}
async function readSourceGroup(group,revision,request,first=null){
  const read=async(name,seed=null)=>{
    const records=[],seen=new Set();let offset=0,total=null;
    for(;;){
      const result=seed||await LRITableGit.loadTablePage('ic_'+name,{filterField:'ui_group',filterValue:group,expectedRevision:revision,offset,limit:100});seed=null;
      if(request!==state.epoch)return null;validateEvidenceRevision(result,revision);assertBusiness(result.records);
      const meta=result.page;must(meta&&Number.isSafeInteger(meta.total)&&meta.total<=2000&&typeof meta.truncated==='boolean','Invalid source category page');
      if(total===null)total=meta.total;else must(total===meta.total,'Source category total changed');
      for(const row of result.records){const key=row[name==='channels'?'channel_id':'family_id'];must(row.ui_group===group&&key&&!seen.has(key),'Invalid source category identity');seen.add(key);records.push(row);}
      must(records.length<=total&&meta.truncated===(records.length<total),'Incomplete source category');
      if(!meta.truncated)return ordered(records);
      must(result.records.length>0&&meta.nextOffset===offset+result.records.length,'Invalid source category cursor');offset=meta.nextOffset;
    }
  };
  if(typeof globalThis.LRICloudSemanticRead==='function'){
    const channels=await read('channels',first);if(request!==state.epoch||!channels)return null;
    const batch=await LRICloudSemanticRead('sources',revision,{group,channels});if(request!==state.epoch)return null;
    validateEvidenceRevision(batch,revision);
    const g=batch.groups,ids=[...new Set(channels.map(row=>row.source_id))];
    assertBusiness(g.source_families);assertBusiness(g.channel_families);assertBusiness(g.industry_source_scopes||[]);
    must(g.profiles.length===1&&g.profiles[0].payload_zh?.title&&g.profiles[0].payload_en?.title,'Missing localized cloud-core profile');
    must(g.primarySources.length===ids.length&&new Set(g.primarySources.map(row=>row.source_id)).size===ids.length&&g.primarySources.every(row=>ids.includes(row.source_id)&&row.title),'Missing category canonical source');
    for(const source of g.primarySources)safeUrl(source.canonical_url);
    const data={...emptyReaderData(),...g,channels,industry_source_scopes:g.industry_source_scopes||[]};LRIGroupedSources.validate(data);return data;
  }
  const [channels,families]=await Promise.all([read('channels',first),read('source_families')]);if(request!==state.epoch||!channels||!families)return null;
  const ids=[...new Set(channels.map(row=>row.source_id))],fids=families.map(row=>row.family_id);
  const [memberships,sources,scopes]=await Promise.all([
    LRITableGit.loadRowsByValues('ic_channel_families','family_id',fids,revision),
    LRITableGit.loadRowsByKeys('cloud_core_sources',ids,revision,['source_id','business_id','canonical_url','title','external_id']),
    group==='industry'?LRITableGit.loadRowsByKeys('ic_industry_source_scopes',fids,revision):Promise.resolve({revision,records:[]})
  ]);if(request!==state.epoch)return null;
  for(const result of [memberships,sources,scopes])validateEvidenceRevision(result,revision);assertBusiness(memberships.records);assertBusiness(scopes.records);
  must(sources.records.length===ids.length&&new Set(sources.records.map(row=>row.source_id)).size===ids.length&&sources.records.every(row=>row.business_id==='cloud-core'&&ids.includes(row.source_id)&&row.title),'Missing category canonical source');
  for(const source of sources.records)safeUrl(source.canonical_url);
  const data={...emptyReaderData(),channels,source_families:families,channel_families:memberships.records,industry_source_scopes:scopes.records,primarySources:sources.records};LRIGroupedSources.validate(data);return data;
}
async function showSourceGroup(group,first=null){
  const request=state.epoch,revision=state.revision,key=revision+'__'+group;
  if(!state.sourceGroups.has(key)){
    if(!state.sourcePending.has(key)){const pending=readSourceGroup(group,revision,request,first).finally(()=>{if(state.sourcePending.get(key)===pending)state.sourcePending.delete(key);});state.sourcePending.set(key,pending);}
    const data=await state.sourcePending.get(key);if(!data||request!==state.epoch)return;state.sourceGroups.set(key,data);
  }
  if(request!==state.epoch||revision!==state.revision||state.readerMode!=='sources'||group!==state.domain)return;
  const data=state.sourceGroups.get(key),discovery={collection_runs:state.data.collection_runs||[],collection_run_id:state.data.collection_run_id||'',collection_retrievals:state.data.collection_retrievals||[]};
  state.data={...data,...discovery};if(data.profiles){state.profile=data.profiles[0];$('topic-summary').textContent=state.profile['payload_'+state.locale].summary;}state.directoryData=state.data;state.directoryRevision=revision;state.directoryReady=true;state.directoryPartial=!state.sourceStatusReady;
  renderChannels();$('channel-category').disabled=false;$('runtime-status').textContent=mapText('当前分类信源已加载 · 其他类别按需读取','Current source category ready · Other categories load on demand');$('topic-title').textContent=state.profile?state.profile['payload_'+state.locale].title:label('eyebrow');controls(false);
  $('channel-prev').disabled=state.channelOffset===0;$('channel-next').disabled=state.channelOffset+20>=state.channelTotal;
  (globalThis.LRICloudFirstRetire?.(),performance.mark('cloud-core-source-content'));
}
function refreshImportedPapers(){
 globalThis.LRIImportedPaperReview?.update({revision:state.revision,period:state.period||new URLSearchParams(location.search).get('month')||new Date().toISOString().slice(0,7),locale:state.locale,view:state.view,scope:state.scope||new URLSearchParams(location.search).get('scope')||'',strings:state.packs[state.locale]?.strings||{}});
}
async function startSourceReader(request,first){
  if(request!==state.epoch)return;
  state.readerMode='sources';state.revision=first.revision;state.sourceGroups.clear();state.sourcePending.clear();state.sourceStatusPending=null;state.sourceScansPending=null;state.sourceStatusReady=false;state.sourceStatusError='';state.data=emptyReaderData();
  const profile=typeof globalThis.LRICloudSemanticRead==='function'?null:topicRows('topic_workbench_profiles',first.revision).then(rows=>{
    if(request!==state.epoch||state.readerMode!=='sources')return;
    must(rows.length===1&&rows[0].payload_zh?.title&&rows[0].payload_en?.title,'Missing localized cloud-core profile');
    state.profile=rows[0];$('topic-title').textContent=state.profile['payload_'+state.locale].title;$('topic-summary').textContent=state.profile['payload_'+state.locale].summary;
  }).catch(error=>{if(request===state.epoch)showLoadError(error,true);});
  await showSourceGroup(state.domain,first.records.every(row=>row.ui_group===state.domain)?first:null);if(request!==state.epoch)return;refreshImportedPapers();
  if(document.querySelector('.wb-collection-audit')?.open)await ensureSourceStatus();
  if($('source-collection-details')?.open)await ensureSourceScans();
}
async function ensureSourceStatus(){
  if(state.readerMode!=='sources'||state.sourceStatusReady||!state.revision)return;
  if(state.sourceStatusPending)return state.sourceStatusPending;
  const request=state.epoch,revision=state.revision;
  const promise=(async()=>{
    state.sourceStatusError='';$('collection-summary').textContent=label('loading');
    const runs=await loadCollectionRows('collection_runs','topic_id','cloud_core',revision,request);if(request!==state.epoch)return;
    const run=[...runs].sort((a,b)=>(b.completed_at||b.started_at).localeCompare(a.completed_at||a.started_at))[0];
    const retrievals=run?await loadCollectionRows('channel_retrievals','run_id',run.run_id,revision,request):[];if(request!==state.epoch||revision!==state.revision)return;
    const discovery={collection_runs:runs,collection_run_id:run?.run_id||'',collection_retrievals:retrievals};const channels=await loadCatalog('channels',revision);if(request!==state.epoch)return;validateCollectionSnapshot({...state.data,...discovery,channels});
    Object.assign(state.data,discovery);state.sourceStatusReady=true;state.directoryPartial=false;renderChannels();
  })().catch(error=>{if(request===state.epoch){state.sourceStatusError=mapText('采集状态读取失败，收起后重新展开可重试：','Collection status failed; close and reopen to retry: ')+error.message;renderCollectionRun();}}).finally(()=>{if(state.sourceStatusPending===promise)state.sourceStatusPending=null;});
  state.sourceStatusPending=promise;return promise;
}
async function ensureSourceScans(){
  if(state.readerMode!=='sources'||!state.revision||state.sourceScansPending)return;
  const request=state.epoch,revision=state.revision;
  const promise=(async()=>{
    $('source-scan-cards').textContent=label('loading');
    const [scans,screenings]=await Promise.all([small('source_scans',revision),small('source_screenings',revision)]);if(request!==state.epoch)return;
    const data={...emptyReaderData(),source_scans:scans,source_screenings:screenings};validateEnrichment(data);
    const ids=[...new Set([...scans.map(row=>row.channel_source_id),...screenings.map(row=>row.source_id)])],sources=await LRITableGit.loadRowsByKeys('cloud_core_sources',ids,revision,['source_id','business_id','canonical_url','title','external_id']);
    if(request!==state.epoch)return;validateEvidenceRevision(sources,revision);must(sources.records.length===ids.length&&sources.records.every(row=>row.business_id==='cloud-core'&&ids.includes(row.source_id)),'Missing screening source');
    for(const row of sources.records)safeUrl(row.canonical_url);
    state.data.source_scans=scans;state.data.source_screenings=screenings;
    state.data.primarySources=[...new Map([...state.data.primarySources,...sources.records].map(row=>[row.source_id,row])).values()];renderSourceScans();
  })().catch(error=>{if(request===state.epoch)$('source-scan-cards').textContent=mapText('筛选记录读取失败，收起后重新展开可重试：','Screening records failed; close and reopen to retry: ')+error.message;}).finally(()=>{if(state.sourceScansPending===promise)state.sourceScansPending=null;});
  state.sourceScansPending=promise;return promise;
}
// The topic reader has its own critical path; directory and period evidence
// belong to index/monthly readers and must never delay research content.
async function loadTopicReferenceSupplement(request,revision){
  try{
    const names=['techniques','placements','source_refs','lineages','lineage_nodes','lineage_relations','lineage_cells','map_assignments'];
    const batch=typeof globalThis.LRICloudSemanticRead==='function'?await LRICloudSemanticRead('references',revision):null;
    if(batch){validateEvidenceRevision(batch,revision);for(const rows of Object.values(batch.groups))assertBusiness(rows);}
    const rows=batch?names.map(name=>ordered(batch.groups[name])):await boundedRead(names,name=>small(name,revision),3);
    if(request!==state.epoch||revision!==state.revision||!topicPage())return;
    const data={...state.data,...Object.fromEntries(names.map((name,i)=>[name,rows[i]]))};validateEnrichment(data);validateScientificTaxonomy(data);
    const ids=[...new Set([...data.source_refs,...data.lineage_nodes,...data.lineage_relations].map(row=>row.source_id))],sources=await LRITableGit.loadRowsByKeys('cloud_core_sources',ids,revision,['source_id','business_id','canonical_url','title','external_id']);
    if(request!==state.epoch||revision!==state.revision||!topicPage())return;validateEvidenceRevision(sources,revision);
    must(sources.records.length===ids.length&&new Set(sources.records.map(row=>row.source_id)).size===ids.length&&sources.records.every(row=>row.business_id==='cloud-core'&&ids.includes(row.source_id)&&row.title),'Missing supplementary topic source');
    for(const source of sources.records)safeUrl(source.canonical_url);
    state.data={...data,primarySources:sources.records};state.referencePending=false;state.referenceError='';renderDirectionDetail();performance.mark('cloud-core-topic-supplement');
  }catch(error){if(request===state.epoch&&revision===state.revision){state.referenceError=error.message;renderDirectionDetail();}}
}
async function startTopicReader(request,metadata) {
  state.readerMode=topicPage()?'topic':'map';
  metadata=metadata||await LRITableGit.loadTableMetadata('ic_compression_topics');
  if(request!==state.epoch)return;
  const revision=metadata.revision,id=requestedTopic(),params=new URLSearchParams(location.search);
  if(topicPage())must(/^([a-z_]+)-([a-z_]+)$/.test(id),'Select a topic from the technology map');
  const fast=topicPage(),names=fast?['objects','methods','cells','map_facets','map_terms','compression_topics','compression_topic_sections','compression_topic_concepts']:['objects','methods','cells','techniques','placements','source_refs','lineages','lineage_nodes','lineage_relations','lineage_cells','map_facets','map_terms','map_assignments','compression_topics','compression_topic_sections','compression_topic_concepts','trend_periods'];
  let profiles,rows,assignments=null,dossier;
  if(typeof globalThis.LRICloudSemanticRead==='function'){
    const batch=await LRICloudSemanticRead(fast?'topic':'map',revision,{topicId:id});if(request!==state.epoch)return;
    validateEvidenceRevision(batch,revision);const groups=batch.groups;
    for(const name of Object.keys(groups))if(name!=='profiles')assertBusiness(groups[name]);
    profiles=groups.profiles;rows=names.map(name=>ordered(groups[name]));
    if(fast)assignments={revision,records:groups.map_assignments};
    const api=dossierReadApi(groups,id,revision);
    dossier=fast?LRITopicDossier.ensure(id,revision,api).catch(error=>{dossierErrors.set(revision+'__'+id,error.message);return null;}):Promise.resolve(null);
  }else{
    dossier=id?LRITopicDossier.ensure(id,revision,LRITableGit).catch(error=>{dossierErrors.set(revision+'__'+id,error.message);return null;}):Promise.resolve(null);
    [profiles,rows,assignments]=await Promise.all([topicRows('topic_workbench_profiles',revision),boundedRead(names,name=>small(name,revision),4),fast?LRITableGit.loadRowsByValues('ic_map_assignments','subject_kind',['legacy_object','legacy_method'],revision):Promise.resolve(null)]);
  }
  if(assignments){validateEvidenceRevision(assignments,revision);assertBusiness(assignments.records);must(assignments.records.every(row=>['legacy_object','legacy_method'].includes(row.subject_kind)),'Invalid topic navigation assignment');}
  if(request!==state.epoch)return;
  must(profiles.length===1&&profiles[0].payload_zh?.title&&profiles[0].payload_en?.title,'Missing localized cloud-core profile');
  const data={...Object.fromEntries(collectionNames.map(name=>[name,[]])),...Object.fromEntries(directoryNames.map(name=>[name,[]])),...Object.fromEntries(names.map((name,i)=>[name,rows[i]])),legacyChannels:[],ascendAssessments:[],primarySources:[],collection_runs:[],collection_retrievals:[],collection_run_id:'',measurementCount:0,decisionCount:0};
  if(assignments)data.map_assignments=assignments.records;
  must(data.objects.length===7&&data.methods.length===6&&data.cells.length===42&&new Set(data.cells.map(row=>row.cell_id)).size===42,'Invalid canonical compression taxonomy');
  validateEnrichment(data);validateScientificTaxonomy(data);validateCompressionTopics(data);
  if(id)must(data.compression_topics.some(row=>row.compression_topic_id===id),'Unknown compression topic');
  const ids=[...new Set([...data.source_refs,...data.lineage_nodes,...data.lineage_relations].map(row=>row.source_id))];
  const sources=await LRITableGit.loadRowsByKeys('cloud_core_sources',ids,revision,['source_id','business_id','canonical_url','title','external_id']);
  if(request!==state.epoch)return;validateEvidenceRevision(sources,revision);
  must(sources.records.length===ids.length&&new Set(sources.records.map(row=>row.source_id)).size===ids.length&&sources.records.every(row=>row.business_id==='cloud-core'&&ids.includes(row.source_id)&&row.title),'Missing canonical topic source');
  for(const source of sources.records)safeUrl(source.canonical_url);
  if(fast)await dossier;if(request!==state.epoch)return;
  data.primarySources=sources.records;state.data=data;state.profile=profiles[0];state.revision=revision;state.referencePending=fast;
  $('topic-title').textContent=state.profile['payload_'+state.locale].title;$('topic-summary').textContent=state.profile['payload_'+state.locale].summary;
  state.period=params.get('month')||[...data.trend_periods].sort((a,b)=>b.month.localeCompare(a.month))[0]?.period_id||'';state.scope=params.get('scope')||'';
  if(id){const [target,method]=id.split('-');openScientificFocus(target,method,false);}else{renderSelectors();renderMap();renderSelection();showView('topics');(globalThis.LRICloudFirstRetire?.(),performance.mark('cloud-core-map-content'));}
  $('runtime-status').textContent=label('snapshot_ready');controls(true);
  performance.mark('cloud-core-topic-content');
  await dossier;
  if(id&&request===state.epoch&&state.revision===revision&&compressionTopicId()===id){renderDirectionDetail();(globalThis.LRICloudFirstRetire?.(),performance.mark('cloud-core-topic-dossier'));}
  if(fast&&request===state.epoch)loadTopicReferenceSupplement(request,revision);
}

async function startCurrentReader(request,metadata) {
  if(request!==state.epoch)return;
  const revision=metadata.revision,params=new URLSearchParams(location.search),period=params.get('month'),scope=params.get('scope');
  const boundedScope=/^\d{4}-\d{2}$/.test(period||'')&&scope?{period,scope}:{};
  if(boundedScope.scope&&typeof globalThis.LRICloudSemanticRead==='function')LRICloudSemanticRead('synthesis',revision,boundedScope).catch(()=>{});
  state.readerMode='current';state.directoryDeferred=true;state.directoryReady=false;
  const names=['objects','methods','cells','map_facets','map_terms','compression_topics','compression_topic_sections','compression_topic_concepts','trend_periods'];
  let groups;
  if(typeof globalThis.LRICloudSemanticRead==='function'){
    const batch=await LRICloudSemanticRead('current',revision,boundedScope);validateEvidenceRevision(batch,revision);groups=batch.groups;
  }else{
    const [profiles,rows,assignments]=await Promise.all([topicRows('topic_workbench_profiles',revision),boundedRead(names,name=>small(name,revision)),LRITableGit.loadRowsByValues('ic_map_assignments','subject_kind',['legacy_object','legacy_method'],revision)]);
    validateEvidenceRevision(assignments,revision);groups={...Object.fromEntries(names.map((name,i)=>[name,rows[i]])),profiles,map_assignments:assignments.records};
  }
  if(request!==state.epoch)return;
  for(const [name,rows] of Object.entries(groups))if(name!=='profiles')assertBusiness(rows);
  must(groups.profiles.length===1&&groups.profiles[0].payload_zh?.title&&groups.profiles[0].payload_en?.title,'Missing localized cloud-core profile');
  const data={...emptyReaderData(),...groups};
  must(data.objects.length===7&&data.methods.length===6&&data.cells.length===42,'Invalid canonical compression taxonomy');
  validateScientificTaxonomy(data);validateCompressionTopics(data);
  state.data=data;state.profile=groups.profiles[0];state.revision=revision;
  state.period=params.get('month')||[...data.trend_periods].filter(row=>!/template|uncollected/i.test(row.source_status)).sort((a,b)=>b.month.localeCompare(a.month))[0]?.period_id||'';
  state.scope=params.get('scope')||'';
  const requested=params.get('topic')||'';
  if(requested){must(data.compression_topics.some(row=>row.compression_topic_id===requested),'Unknown compression topic');const [target,method]=requested.split('-'),cells=selectScientificFocus(target,method);must(cells?.length,'Unavailable compression topic navigation');state.cell=cells[0].cell_id;state.object=cells[0].object_id;state.method=cells[0].method_id;state.all=false;}
  else{state.focusTarget='';state.focusMechanism='';state.focusCells=[];state.cell='';state.object='';state.method='';state.all=true;}
  state.directionMode=false;render();performance.mark('cloud-core-current-structure');
  if(groups.monthly_scopes&&boundedScope.scope){
    must(groups.monthly_scopes.every(row=>row.period_id===state.period),'Invalid monthly scope list');
    state.scopes=ordered(groups.monthly_scopes);must(state.scopes.some(row=>row.scope_id===state.scope),'Selected monthly scope unavailable');
    state.reviews=validateReviews(groups.monthly_cell_reviews,state.scope,state.period);
    const links=groups.compression_topic_events,topics=new Set(data.compression_topics.map(row=>row.compression_topic_id));
    for(const row of links){must(topics.has(row.compression_topic_id),'Unknown compression topic');validateTopicEvent(row,state.scope,state.period,row.compression_topic_id);}
    must(new Set(links.map(row=>row.link_id)).size===links.length,'Duplicate compression topic event');
    state.topicScopeLinks=links;state.scopeReady=true;state.scopeBusy=false;persistTopicScope();renderSelectors();renderScope();renderMap();renderSelection();controls(true);
  }else if(state.period)await loadPeriod(state.period,state.scope);
}

function readerMatchesView(){
 return state.readerMode==='sources'?state.view==='sources':state.readerMode==='map'?state.view==='topics':state.readerMode==='current'?['updates','home'].includes(state.view):true;
}
async function start(preferredView='') {
  state.view=preferredView||(topicPage()?'topics':document.body.dataset.compressionMonthly==='true'?'updates':viewFromHash());
  if(topicPage())restoreTopicNodes();
  state.readerMode='';state.referencePending=false;state.referenceError='';
  const openingView=state.view;
  const request=++state.epoch,preferredPeriod=state.period,preferredScope=state.scope; state.periodEpoch++; state.scopeEpoch++; state.legacyEpoch++; state.revision=''; state.profile=null; state.directoryReady=false;state.directoryPartial=false;state.directoryDeferred=false; state.directoryData=null;state.directoryRevision=''; state.scopeReady=false; state.scopeBusy=false; state.scopeError=false; state.scopes=[]; state.reviews=[]; state.legacy=[]; state.legacyPeriod=''; state.legacyBusy=false; clear(); $('topic-title').textContent=mapText('推理压缩洞察','Inference compression insights'); renderViewPurpose(); controls(false); $('scope-retry').hidden=true;$('runtime-status').setAttribute('role','status'); $('runtime-status').textContent=label('loading');
  try {
    const anchor=state.view==='sources'&&!topicPage()?LRITableGit.loadTablePage('ic_channels',{filterField:'ui_group',filterValue:state.domain,offset:0,limit:100}):['topics','updates','home'].includes(state.view)?(globalThis.LRICloudFirstRead?globalThis.LRICloudFirstRead.then(result=>({revision:result.revision})).catch(()=>LRITableGit.loadTableMetadata('ic_compression_topics')):LRITableGit.loadTableMetadata('ic_compression_topics')):null;
    if(anchor)anchor.catch(()=>{}); // The request is awaited below; prevent an early rejected promise.
    if(!state.packs.zh&&globalThis.LRICloudUIPacks)state.packs=globalThis.LRICloudUIPacks;
    if(!state.packs.zh) { const packs=await Promise.all(['zh','en'].map(async locale=>{const response=await fetch(document.querySelector('meta[name="lri-page-i18n"]').content.replace('{lang}',locale));if(!response.ok)throw new Error('UI locale unavailable');return response.json();})); state.packs={zh:packs[0],en:packs[1]}; }
    if(request!==state.epoch)return;
    if(state.view!==openingView){start(state.view);return;}
    if(topicPage()||state.view==='topics'){await startTopicReader(request,await anchor);if(request===state.epoch&&!readerMatchesView())start(state.view);return;}
    if(state.view==='sources'){await startSourceReader(request,await anchor);if(request===state.epoch&&!readerMatchesView())start(state.view);return;}
    if(['updates','home'].includes(state.view)){await startCurrentReader(request,await anchor);if(request===state.epoch&&!readerMatchesView())start(state.view);return;}
    state.readerMode='full';
    const directory=await loadDirectory(request);if(request!==state.epoch||!directory)return;
    const revision=state.revision;
    const collection_runs=topicPage()||state.directoryDeferred?[]:await loadCollectionRows('collection_runs','topic_id','cloud_core',revision,request);if(request!==state.epoch)return;
    const directoryRun=[...collection_runs].sort((a,b)=>(b.completed_at||b.started_at).localeCompare(a.completed_at||a.started_at))[0],collection_run_id=directoryRun?.run_id||'';
    const collection_retrievals=directoryRun?await loadCollectionRows('channel_retrievals','run_id',directoryRun.run_id,revision,request):[];if(request!==state.epoch)return;
    const discovery={collection_runs,collection_run_id,collection_retrievals};validateCollectionSnapshot({...directory,...discovery});Object.assign(directory,discovery);renderChannels();
    const names=collectionNames.filter(name=>!directoryNames.includes(name));
    const batch=typeof globalThis.LRICloudSemanticRead==='function'?await LRICloudSemanticRead('workbench',revision):null;
    if(batch){validateEvidenceRevision(batch,revision);for(const [name,rows] of Object.entries(batch.groups))if(!['profiles','items'].includes(name))assertBusiness(rows);}
    const [profiles,items]=batch?[batch.groups.profiles,batch.groups.items]:await boundedRead(['topic_workbench_profiles','topic_workbench_items'],name=>topicRows(name,revision));if(request!==state.epoch)return;
    must(profiles.length===1&&profiles[0].payload_zh?.title&&profiles[0].payload_en?.title,'Missing localized cloud-core profile');
    const snapshot={profile:profiles[0],items,revision};
    const data=batch?names.map(name=>ordered(batch.groups[name])):await boundedRead(names,name=>small(name,revision),8);if(request!==state.epoch)return;const collected={...directory,...Object.fromEntries(names.map((name,i)=>[name,data[i]]))};
    must(collected.objects.length===7&&collected.methods.length===6&&collected.cells.length===42&&new Set(collected.cells.map(row=>row.cell_id)).size===42,'Invalid canonical compression taxonomy');
    validateEnrichment(collected); validateResearch(collected);validateScientificTaxonomy(collected);validateCompressionTopics(collected);
    const channels=[...(snapshot.items||[])].filter(row=>row.collection_key==='information_channels').sort((a,b)=>(a.ordinal||0)-(b.ordinal||0));
    for(const row of channels) {
      const zh=row.payload_zh,en=row.payload_en;
      must(row.topic_id==='cloud_core'&&zh&&en&&typeof zh.channel_id==='string'&&zh.channel_id&&zh.channel_id===en.channel_id&&typeof zh.source_id==='string'&&zh.source_id&&zh.source_id===en.source_id,'Invalid information channel identity');
      for(const payload of [zh,en])must(['title','focus','review_rule'].every(key=>typeof payload[key]==='string'&&payload[key]),'Invalid information channel payload');
    }
    must(new Set(channels.map(row=>row.payload_zh.channel_id)).size===channels.length,'Duplicate information channel');
    const ascendAssessments=[...(snapshot.items||[])].filter(row=>row.collection_key==='ascend_assessments').sort((a,b)=>(a.ordinal||0)-(b.ordinal||0));
    for(const row of ascendAssessments) {
      const zh=row.payload_zh,en=row.payload_en;
      must(row.topic_id==='cloud_core'&&zh&&en&&['assessment_id','cell_id','source_id'].every(key=>typeof zh[key]==='string'&&zh[key]&&zh[key]===en[key])&&typeof zh.technique_id==='string'&&zh.technique_id===en.technique_id,'Invalid Ascend assessment identity');
      must(collected.cells.some(cell=>cell.cell_id===zh.cell_id)&&(!zh.technique_id||collected.techniques.some(technique=>technique.technique_id===zh.technique_id)),'Unknown Ascend assessment placement');
      for(const payload of [zh,en])must(['title','finding','boundary','next_action','status'].every(key=>typeof payload[key]==='string'&&payload[key]),'Invalid Ascend assessment payload');
    }
    must(new Set(ascendAssessments.map(row=>row.payload_zh.assessment_id)).size===ascendAssessments.length,'Duplicate Ascend assessment');
    const sourceIds=[...new Set([...collected.source_refs.map(row=>row.source_id),...channels.map(row=>row.payload_zh.source_id),...ascendAssessments.map(row=>row.payload_zh.source_id),...collected.lineage_nodes.map(row=>row.source_id),...collected.lineage_relations.map(row=>row.source_id),...collected.source_screenings.map(row=>row.source_id),...collected.source_scans.map(row=>row.channel_source_id),...collected.channels.map(row=>row.source_id),...collected.finding_evidence.map(row=>row.source_id)])],sources=await LRITableGit.loadRowsByKeys('cloud_core_sources',sourceIds,snapshot.revision,['source_id','business_id','canonical_url','title','external_id']);
    if(request!==state.epoch)return; validateEvidenceRevision(sources,snapshot.revision);
    must(sources.records.length===sourceIds.length&&new Set(sources.records.map(row=>row.source_id)).size===sourceIds.length&&sources.records.every(row=>row.business_id==='cloud-core'&&sourceIds.includes(row.source_id)&&typeof row.title==='string'&&row.title),'Missing canonical source');
    for(const source of sources.records)safeUrl(source.canonical_url);
    const outcomes=await Promise.all(['measurements','decisions'].map(name=>page(name,'topic_id','cloud_core',snapshot.revision,{limit:1}))); if(request!==state.epoch)return;
    state.data={...collected,legacyChannels:channels,ascendAssessments,primarySources:sources.records,measurementCount:outcomes[0].page.total,decisionCount:outcomes[1].page.total}; state.profile=snapshot.profile; state.revision=snapshot.revision;
    state.period=collected.trend_periods.some(row=>row.period_id===preferredPeriod)?preferredPeriod:''; render();if(state.view==='topics')(globalThis.LRICloudFirstRetire?.(),performance.mark('cloud-core-map-content'));
    const requested=requestedTopic(),match=/^([a-z_]+)-([a-z_]+)$/.exec(requested);if(match){must(collected.compression_topics.some(row=>row.compression_topic_id===requested),'Unknown compression topic');openScientificFocus(match[1],match[2],false);if(!topicPage())showView(viewFromHash());}else if(topicPage())throw integrity('Select a topic from the technology map');else revealHashTarget();
    const periodRequest=state.periodEpoch;
    const month=new URLSearchParams(location.search).get('month'),scope=new URLSearchParams(location.search).get('scope');const selected=month&&collected.trend_periods.some(row=>row.period_id===month)?{period:month,scope:scope||''}:state.period?{period:state.period,scope:preferredScope}:await chooseDefaultPeriod(snapshot.revision,request);
    if(request!==state.epoch||periodRequest!==state.periodEpoch)return; if(selected?.period)await loadPeriod(selected.period,selected.scope);
  }catch(error){if(request!==state.epoch)return;if(state.directoryReady){state.profile=null;state.scopeReady=false;controls(false);renderChannels();showLoadError(error,true);console.error('Compression research module unavailable',error);}else fail(error);}
}
$('reload').addEventListener('click',()=>{LRITableGit.invalidate();start();});
$('period-filter').addEventListener('change',()=>loadPeriod($('period-filter').value));
$('scope-filter').addEventListener('change',()=>loadScope($('scope-filter').value));
$('scope-retry').addEventListener('click',()=>state.scope?loadScope(state.scope):loadPeriod(state.period));
$('object-filter').addEventListener('change',()=>{if(!state.revision)return;state.directionMode=false;state.focusTarget='';state.focusMechanism='';state.focusCells=[];state.object=$('object-filter').value;state.cell='';state.method='';state.all=true;resetDetails();resetEvidence();renderMap();renderSelection();renderEvidence();if(state.legacyPeriod)renderLegacy();controls(true);loadEvidence(0);});
$('evidence-prev').addEventListener('click',()=>loadEvidence(Math.max(0,state.evidenceOffset-20)));
$('evidence-next').addEventListener('click',()=>loadEvidence(state.evidencePage?.nextOffset||0));
$('evidence-retry').addEventListener('click',()=>loadEvidence(state.evidenceOffset));
$('channel-category').addEventListener('change',()=>{state.channelCategory=$('channel-category').value;state.channelOffset=0;state.industryOffsets={ascend:0,general:0};renderChannels();});
document.querySelectorAll('.wb-domain-tabs [role=tab]').forEach(tab=>tab.setAttribute('aria-controls','channel-cards'));
$('channel-query').addEventListener('input',()=>{state.channelQuery=$('channel-query').value;state.channelOffset=0;state.industryOffsets={ascend:0,general:0};renderChannels();});
$('channel-priority').addEventListener('change',()=>{state.channelImportant=$('channel-priority').value==='important';state.channelOffset=0;state.industryOffsets={ascend:0,general:0};renderChannels();});
$('channel-prev').addEventListener('click',()=>{state.channelOffset=Math.max(0,state.channelOffset-20);renderChannels();});
$('channel-next').addEventListener('click',()=>{state.channelOffset=Math.min(Math.max(0,Math.floor((state.channelTotal-1)/20)*20),state.channelOffset+20);renderChannels();});
$('load-legacy').addEventListener('click',()=>loadExpandedLegacy(true)); $('load-documents').addEventListener('click',()=>loadExpandedDocuments(true));
$('source-panel').addEventListener('toggle',()=>{if($('source-panel').open)loadExpandedDocuments();});
$('legacy-panel').addEventListener('toggle',()=>{if($('legacy-panel').open)loadExpandedLegacy();});
document.addEventListener('toggle',event=>{const node=event.target;if(node.open&&state.readerMode==='sources'){if(node.matches('.wb-collection-audit')||node.dataset.disclosureKey?.startsWith('source-status-'))ensureSourceStatus();if(node.id==='source-collection-details')ensureSourceScans();}if(node.dataset?.disclosureKey)state.disclosureOpen.set(node.dataset.disclosureKey,node.open);if(node.open&&node.dataset.collectionRetrieval)loadCollectionEntries(node.dataset.collectionRetrieval);},true);
$('funnel-sources-link').addEventListener('click',()=>showView('sources'));
document.addEventListener('click',event=>{
 const citation=(event.composedPath?.()||[event.target]).find(n=>n?.tagName==='A'&&n.dataset.researchCitation);
 if(citation&&!event.ctrlKey&&!event.metaKey&&!event.shiftKey&&!event.altKey&&(event.button===undefined||event.button===0)){
  const target=document.getElementById(citation.hash.slice(1));
  if(target){event.preventDefault();if(citation.classList.contains('research-citation-link')){const back=target.querySelector('.research-citation-return');if(back)back.href='#'+citation.id;}history.replaceState(null,'',citation.hash);target.scrollIntoView({block:'center'});target.focus({preventScroll:true});return;}
 }

  if(!event.defaultPrevented&&!event.ctrlKey&&!event.metaKey&&!event.shiftKey&&!event.altKey&&(event.button===undefined||event.button===0)&&topicPage()){
    const anchor=(event.composedPath?.()||[event.target]).find(n=>n?.tagName==='A'&&n.getAttribute('href'));
    if(anchor&&(!anchor.target||anchor.target==='_self')&&!anchor.hasAttribute('download')){
      const url=new URL(anchor.getAttribute('href'),location.href),current=new URL(location.href);
      if(url.origin===current.origin&&url.pathname===current.pathname&&url.searchParams.get('topic')===requestedTopic()&&['month','scope'].every(k=>url.searchParams.get(k)===current.searchParams.get(k))){
        event.preventDefault();history.pushState(null,'',url.href);renderDirectionDetail();revealHashTarget();performance.mark('cloud-core-topic-navigation');return;
      }
    }
  }
  const research=(event.composedPath?.()||[event.target]).find(n=>n?.tagName==='A'&&n.dataset.compressionResearchView);if(research){event.preventDefault();history.pushState(null,'',research.getAttribute('href'));renderDirectionDetail();revealHashTarget();return;}
  const route=(event.composedPath?.()||[event.target]).find(node=>node?.tagName==='A'&&(node.dataset.compressionTopicRoute||node.dataset.compressionTopicBack||node.dataset.compressionTopicTimeline));
  if(route&&(route.dataset.compressionTopicTimeline||route.dataset.compressionTopicBack)&&location.pathname.endsWith('/topic.html'))return; // Load the separate main reader and its period module.
  if(route){event.preventDefault();if(route.dataset.compressionTopicTimeline){restoreTopicNodes();document.body.dataset.compressionTopic='false';document.title='推理压缩 · 云核 · LRI';history.pushState(null,'',route.getAttribute('href'));renderSelection();showView('updates');loadEvidence(0);document.dispatchEvent(new Event('lri:sections-changed'));}else if(route.dataset.compressionTopicBack){restoreTopicNodes();document.body.dataset.compressionTopic='false';document.title='推理压缩 · 云核 · LRI';history.pushState(null,'',route.getAttribute('href'));revealHashTarget('view-topics');showView('topics');document.dispatchEvent(new Event('lri:sections-changed'));}else{history.pushState(null,'',route.getAttribute('href'));document.body.dataset.compressionTopic='true';const [target,method]=route.dataset.compressionTopicRoute.split('-');openScientificFocus(target,method,false);}return;}
  const link=(event.composedPath?.()||[event.target]).find(node=>node?.tagName==='A'&&node.getAttribute('href')?.startsWith('#'));
  if(!link)return;const id=link.getAttribute('href').slice(1);
  if(link.dataset.scientificTarget){event.preventDefault();openScientificFocus(link.dataset.scientificTarget,link.dataset.scientificMechanism);return;}
  if(link.dataset.directionCell){event.preventDefault();openDirection(link.dataset.directionCell);return;}
  if(id==='view-topics'&&state.directionMode){state.directionMode=false;state.focusTarget='';state.focusMechanism='';state.focusCells=[];state.object='';state.cell='';state.method='';state.all=true;resetEvidence();renderSelectors();renderMap();renderSelection();}
  if(link.dataset.view){event.preventDefault();showView(link.dataset.view,true);}
  else if($(id)){showView(viewForTarget(id));revealHashTarget(id);}
});
window.addEventListener('hashchange',()=>{showView(viewFromHash());revealHashTarget();});
window.addEventListener('popstate',()=>{restoreTopicNodes();document.body.dataset.compressionTopic=String(location.pathname.endsWith('/topic.html'));const topic=requestedTopic();if(topic&&state.revision){const [target,method]=topic.split('-');openScientificFocus(target,method,false);if(!topicPage())showView(viewFromHash());}else{showView(viewFromHash());revealHashTarget();}document.dispatchEvent(new Event('lri:sections-changed'));});
document.querySelectorAll('[data-domain]').forEach(tab=>{
  tab.addEventListener('click',()=>{state.domain=tab.dataset.domain;state.channelCategory='';state.channelOffset=0;state.industryOffsets={ascend:0,general:0};if(state.readerMode==='sources'){if(!state.sourceGroups.has(state.revision+'__'+state.domain)){for(const item of document.querySelectorAll('[data-domain]')){const active=item.dataset.domain===state.domain;item.setAttribute('aria-selected',String(active));item.tabIndex=active?0:-1;}$('channel-cards').textContent=mapText('正在读取','Loading ')+enumLabel('domain_',state.domain)+mapText('信源…',' sources…');$('channel-status').textContent=enumLabel('domain_',state.domain)+' · '+mapText('读取中','Loading');$('channel-category').replaceChildren();$('channel-category').disabled=true;$('channel-prev').disabled=true;$('channel-next').disabled=true;}showSourceGroup(state.domain).catch(error=>showLoadError(error,true));}else renderChannels();});
  tab.addEventListener('keydown',event=>{
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
    event.preventDefault();const tabs=[...document.querySelectorAll('[data-domain]')],index=tabs.indexOf(tab);
    const target=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
    tabs.forEach((item,i)=>item.tabIndex=i===target?0:-1);tabs[target].focus();
  });
});
document.addEventListener('lri:locale-change',event=>{state.locale=event.detail.locale==='en'?'en':'zh';render();});
document.addEventListener('lri:force-refresh-ready',()=>{LRITableGit.invalidate();start();});
showView(viewFromHash());revealHashTarget();start();


