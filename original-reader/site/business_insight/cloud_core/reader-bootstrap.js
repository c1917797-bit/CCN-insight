(() => {
 'use strict';
 // Preserve an initial deep link through asynchronous layout only until the reader acts.
 const initialNavigation={hash:location.hash,canceled:false};globalThis.LRICloudInitialNavigation=initialNavigation;
 const cancelInitialNavigation=()=>{initialNavigation.canceled=true;};
 for(const event of ['wheel','touchstart','pointerdown'])addEventListener(event,cancelInitialNavigation,{passive:true,once:true});
 addEventListener('keydown',event=>{if(['ArrowUp','ArrowDown','PageUp','PageDown','Home','End',' '].includes(event.key))cancelInitialNavigation();});

 // First-paint reader. It fetches authorized TableGit rows; no facts are built into this file.
 const params=new URLSearchParams(location.search),topic=params.get('topic'),period=params.get('month')||new Date().toISOString().slice(0,7),scope=params.get('scope');
 const topicPage=location.pathname.endsWith('/topic.html'),monthly=location.pathname.endsWith('/monthly.html');
 const match=/^#view-(sources|topics|updates|home|reports)/.exec(location.hash),mapRoute=/^#(?:map$|route-(?:precision|selection|distillation|factorization)$)/.test(location.hash),view=topicPage||mapRoute?'topics':monthly?'updates':match?.[1]||(location.hash==='#analysis-focus'?'home':location.hash==='#supplementary-paper-reviews'?'updates':'sources');
 const en=document.documentElement.lang.startsWith('en'),pick=(r,k)=>r[k+(en?'_en':'_zh')]||r[k+'_zh']||r[k]||'',eq=(field,value)=>({field,op:'eq',value});
 const common=[eq('business_id','cloud-core'),eq('topic_id','cloud_core')];
 const table=(name,filters=[])=>({name,table:'ic_'+name,filters:[...common,...filters]});
 let plan;
 if(view==='sources')plan=[table('source_families',[eq('ui_group','hotspot')]),table('channels',[eq('ui_group','hotspot'),{field:'priority',op:'in',value:['P0','P1']}]),{...table('channel_families'),limit:400,select:['business_id','topic_id','membership_id','channel_id','family_id','position']}];
 else if(view==='topics')plan=topic?[table('compression_topic_sections',[eq('compression_topic_id',topic),{field:'section_kind',op:'in',value:['problem','mechanism','boundary']}])]:[table('map_terms',[eq('facet_id','mechanism')])];
 else if(view==='updates')plan=[table('paper_summary_events',[eq('period_id',period)]),table('paper_summaries')];
 else plan=[table('insight_reports',[eq('period_id',period),eq('status','published')])];
 const ensure=(test,message)=>{if(!test)throw Error(message);};
 async function call(name,args){
  const response=await fetch('/mcp',{method:'POST',credentials:'same-origin',priority:'high',headers:{'content-type':'application/json',accept:'application/json, text/event-stream','MCP-Protocol-Version':'2026-07-28','Mcp-Method':'tools/call','Mcp-Name':name},body:JSON.stringify({jsonrpc:'2.0',id:name==='skill_get'?8701:8702,method:'tools/call',params:{name,arguments:args,_meta:{'io.modelcontextprotocol/protocolVersion':'2026-07-28','io.modelcontextprotocol/clientCapabilities':{}}}}),signal:AbortSignal.timeout(15000)});
  ensure(response.ok,'First-content permission/request failed');const envelope=await response.json();ensure(!envelope.error,'First-content request rejected');const r=envelope.result,v=r?.structuredContent??JSON.parse(r?.content?.find(c=>c.type==='text')?.text||'null');ensure(v&&!r.isError&&!v.error&&v.outcome!=='failed','First-content authority unavailable');return v;
 }
 // The server enforces the pinned compiled read contract and permission on every native read.
 // Live discovery is shared with the complete reader; it is not a second permission grant.
 // Independent bounded native table reads start together; the resolved revisions must agree.
 let sourceBindings;
 async function sourceRelation(){
  const nonce=crypto.randomUUID().replace(/-/g,'');
  sourceBindings=plan.map((p,i)=>({alias:'first_'+nonce+i,repo:'works',path:'data/tables/'+p.table,include_deleted:false,source_query:{filters:p.filters,...(p.name==='channels'?{select:['business_id','topic_id','channel_id','priority','enabled']}:p.select?{select:p.select}:{})}}));
  const [f,c,m]=sourceBindings.map(b=>b.alias);
  const sql=`SELECT f.key,f.row_version,f.row_json FROM ${f} f JOIN ${m} m ON json_extract(m.row_json,'$.family_id')=json_extract(f.row_json,'$.family_id') JOIN ${c} c ON json_extract(c.row_json,'$.channel_id')=json_extract(m.row_json,'$.channel_id') WHERE json_extract(c.row_json,'$.enabled')=1 GROUP BY f.key ORDER BY MIN(CASE json_extract(c.row_json,'$.priority') WHEN 'P0' THEN 0 ELSE 1 END),MIN(json_extract(m.row_json,'$.position')),f.key LIMIT 20`;
  return call('skill_run_read',{skill_id:'table.query',skill_version:'2.3.0',operation:'table_relation_query',arguments:{bindings:sourceBindings,sql,limits:{max_source_rows:500,max_source_bytes:524288,max_result_rows:20,max_result_bytes:65536},wall_time_ms:2000}});
 }
 function decodeSources(value){
  const r=value.result;ensure(value.skill_id==='table.query'&&value.skill_version==='2.3.0'&&value.operation==='table_relation_query'&&value.outcome==='executed'&&r&&!r.truncated&&Array.isArray(r.bindings)&&r.bindings.length===3&&Array.isArray(r.rows)&&r.rows.length<=20&&JSON.stringify(r.columns)===JSON.stringify(['key','row_version','row_json'])&&Number.isSafeInteger(r.output_bytes)&&r.output_bytes<=65536,'Invalid first-source relation');
  const revision=r.bindings[0]?.revision;ensure(/^[a-f0-9]{40}$/.test(revision||''),'Missing first-source revision');
  const aliases=new Set();for(const b of r.bindings){const requested=sourceBindings.find(x=>x.alias===b.alias);ensure(requested&&!aliases.has(b.alias)&&b.repo===requested.repo&&b.path===requested.path&&b.revision===revision&&b.include_deleted===false&&requested.source_query.filters.every(f=>b.source_query?.filters?.some(v=>v.field===f.field&&v.op===f.op&&JSON.stringify(v.value)===JSON.stringify(f.value))),'First-source binding mismatch');aliases.add(b.alias);}
  const seen=new Set(),rows=r.rows.map(tuple=>{ensure(Array.isArray(tuple)&&tuple.length===3&&tuple[0].type==='text'&&tuple[1].type==='integer'&&Number.isSafeInteger(tuple[1].value)&&tuple[1].value>0&&tuple[2].type==='text','Invalid first-source row');const row=JSON.parse(tuple[2].value);ensure(row.family_id===tuple[0].value&&!seen.has(row.family_id)&&row.business_id==='cloud-core'&&row.topic_id==='cloud_core'&&row.ui_group==='hotspot'&&!row.deleted,'First-source row outside scope');seen.add(row.family_id);return row;});
  return {revision,groups:{source_families:rows},view,period,scope,topic};
 }
 const requests=view==='sources'?[sourceRelation()]:plan.map(spec=>call('skill_run_read',{skill_id:'table.query',skill_version:'2.3.0',operation:'table_query',arguments:{repo:'works',path:'data/tables/'+spec.table,filters:spec.filters,limit:spec.limit||100,offset:0,...(spec.select?{select:spec.select}:{})}}));
 for(const request of requests)request.catch(()=>{});
 const discover=()=>call('skill_get',{skill_id:'table.query',operation:'table_query'}).then(v=>{
  const s=v.skill?.summary;ensure(s?.skill_id==='table.query'&&s.skill_version==='2.3.0'&&v.skill.operations.some(op=>op.name==='table_query'&&op.access_lane==='read'),'First-content contract changed');return s.skill_version;
 });
 const permission=Promise.all(requests).then(discover,discover);permission.catch(()=>{});globalThis.LRICloudLiveContract=permission;
 globalThis.LRICloudFirstRead=Promise.all(requests).then(values=>{
  if(view==='sources')return decodeSources(values[0]);
  const revision=values[0]?.result?.revision;ensure(/^[a-f0-9]{40}$/.test(revision||''),'Missing first-content revision');
  const groups={},seen=new Set();let total=0;
  for(let i=0;i<plan.length;i++){
   const spec=plan[i],value=values[i],result=value.result;
   ensure(value.skill_id==='table.query'&&value.skill_version==='2.3.0'&&value.operation==='table_query'&&value.outcome==='executed'&&result&&result.repo==='works'&&result.path==='data/tables/'+spec.table&&result.revision===revision&&!result.truncated&&Array.isArray(result.rows)&&result.rows.length<=(spec.limit||100),'Invalid or mixed first-content envelope');
   total+=result.rows.length;ensure(total<=500,'First-content row budget exceeded');groups[spec.name]=[];
   for(const row of result.rows){const record=row.row,key=spec.name+'__'+row.key;ensure(row.key&&!row.deleted&&Number.isSafeInteger(row.row_version)&&row.row_version>0&&record&&!record.deleted&&!seen.has(key)&&spec.filters.every(f=>f.op==='in'?f.value.includes(record[f.field]):record[f.field]===f.value),'First-content row outside scope');seen.add(key);groups[spec.name].push(record);}
  }
  return {revision,groups,view,period,scope,topic};
 });globalThis.LRICloudFirstRead.catch(()=>{});
 // Give the small live first-content requests priority over the complete workbench bundle.
 function loadWorkbench(){const placeholder=document.querySelector('script[data-lri-reader]');if(!placeholder){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',loadWorkbench,{once:true});return;}const script=document.createElement('script');script.src=placeholder.dataset.lriReader;script.defer=true;placeholder.replaceWith(script);}
 globalThis.LRICloudFirstRead.finally(loadWorkbench).catch(()=>{});
 let mounted=false,retired=false,root,paintObserver,assetCacheStarted=false;
 globalThis.LRICloudFirstRetire=()=>{retired=true;const finalParagraph=document.querySelector(view==='sources'?'#channel-cards article p':view==='topics'?(topic?'.direction-lead':'#scientific-map p'):view==='updates'?'#monthly-route-report article p':'#insight-deck-content .analysis-report-card p, #insight-deck-archive .analysis-report-card p');if(finalParagraph)finalParagraph.setAttribute('elementtiming','cloud-core-native-first');root?.remove();if(mounted&&!assetCacheStarted&&'serviceWorker' in navigator){assetCacheStarted=true;navigator.serviceWorker.register('reader-ui-cache.js',{scope:'./',updateViaCache:'none'}).then(r=>r.update()).catch(()=>{});}};
 function node(tag,text,cls){const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n;}
 function link(text,url){const a=node('a',text);const target=new URL(url,location.href);ensure(['https:','http:'].includes(target.protocol),'Unsafe first-content URL');a.href=target.href;if(target.origin!==location.origin){a.target='_blank';a.rel='noopener noreferrer';}return a;}
 function mount(model){
  if(retired||mounted)return;const nav=document.querySelector('.wb-view-tabs');if(!nav)return false;
  const g=model.groups;root=node('section','','section');root.id='first-readable-content';root.dataset.sectionOutline='false';root.dataset.readingLayer=['home','reports'].includes(view)?'analysis':'facts';root.dataset.revision=model.revision;
  root.append(node('h2',en?'Read now':view==='sources'?'信息来源':view==='topics'?(topic?'研究问题与技术原理':'技术地图'):view==='updates'?'本期论文摘要':'本期洞察报告'));
  const grid=node('div','','grid');root.append(grid);let count=0;
  const card=(heading,paragraphs,url)=>{const article=node('article','','card');article.append(url?link(heading,url):node('h3',heading));for(const text of paragraphs.filter(Boolean)){const paragraph=node('p',text);if(count===0&&!article.querySelector?.('p'))paragraph.setAttribute('elementtiming','cloud-core-native-first');article.append(paragraph);}grid.append(article);count++;};
  if(view==='sources'){for(const f of g.source_families)card(pick(f,'title'),[pick(f,'summary')]);}
  else if(view==='topics'&&!topic){for(const id of ['precision','selection','distillation','factorization']){const term=g.map_terms.find(row=>row.term_id===id);ensure(term?.facet_id==='mechanism'&&term.description_zh&&term.name_zh,'Unbound core research route');const url=new URL('index.html',location.href);if(params.has('month'))url.searchParams.set('month',period);if(scope)url.searchParams.set('scope',scope);url.hash='route-'+id;card(pick(term,'name'),[pick(term,'description')],url.href);}}
  else if(view==='topics'){ensure(g.compression_topic_sections.length===3,'Incomplete first research sections');for(const kind of ['problem','mechanism','boundary']){const section=g.compression_topic_sections.find(s=>s.section_kind===kind);ensure(section&&section.claim_kind==='literature_synthesis'&&section.reviewed_at&&section.evidence_url&&section.section_id===topic+'__'+kind,'Unreviewed first research section');card(pick(section,'heading'),[pick(section,'body')],section.evidence_url);}}
  else if(view==='updates'){const events=new Map(g.paper_summary_events.map(e=>[e.summary_id,e]));for(const s of g.paper_summaries.filter(s=>events.has(s.summary_id)).slice(0,6)){const e=events.get(s.summary_id);ensure(e.source_id===s.source_id&&e.observed_version===s.observed_version&&['primary_abstract_checked','method_results_checked'].includes(s.review_status)&&s.evidence_url&&s.one_sentence_zh,'Unreviewed current paper');card((en?'Reviewed paper · ':'论文原文 · ')+new URL(s.evidence_url).pathname.split('/').at(-1),[pick(s,'one_sentence'),pick(s,'results')],s.evidence_url);}}
  else{for(const r of g.insight_reports)card(pick(r,'title'),[pick(r,'summary')],'index.html'+location.search+'#view-home');for(const r of (g.ascend_route_assessments||[]).sort((a,b)=>a.position-b.position).slice(0,3)){ensure(r.claim_status==='analyst_recommendation','Unsupported first-content recommendation');card(pick(r,'title'),[pick(r,'rationale'),pick(r,'recommendation')]);}}
  if(!count)return true;
  for(const panel of document.querySelectorAll('[data-view-panel]'))panel.hidden=panel.dataset.viewPanel!==view;
  const elementTiming=typeof PerformanceObserver!=='undefined'&&PerformanceObserver.supportedEntryTypes?.includes('element');
  if(elementTiming){paintObserver=new PerformanceObserver(list=>{const entry=list.getEntries().find(e=>e.identifier==='cloud-core-native-first'&&e.renderTime>0);if(entry){performance.mark('cloud-core-first-readable-paint',{startTime:entry.renderTime});paintObserver.disconnect();}});paintObserver.observe({type:'element',buffered:true});setTimeout(()=>paintObserver.disconnect(),5000);}
  nav.after(root);mounted=true;const monitor=new MutationObserver(()=>{if(retired){monitor.disconnect();return;}const target=document.querySelector(view==='sources'?'#channel-cards article':view==='topics'?(topic?'[data-dossier-ready="true"]':'#scientific-map a'):view==='updates'?'#monthly-route-report article':'#insight-deck-content .analysis-report-card, #insight-deck-archive .analysis-report-card');if(target){globalThis.LRICloudFirstRetire();monitor.disconnect();}});monitor.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['data-dossier-ready']});performance.mark('cloud-core-first-readable-content');if(!elementTiming)requestAnimationFrame(()=>requestAnimationFrame(()=>performance.mark('cloud-core-first-readable-paint-fallback')));return true;
 }
 globalThis.LRICloudFirstRead.then(model=>{if(mount(model)!==false)return;const observer=new MutationObserver(()=>{if(mount(model)!==false)observer.disconnect();});observer.observe(document.documentElement,{childList:true,subtree:true});}).catch(()=>globalThis.LRICloudFirstRetire());
 addEventListener('hashchange',()=>globalThis.LRICloudFirstRetire(),{once:true});
})();

