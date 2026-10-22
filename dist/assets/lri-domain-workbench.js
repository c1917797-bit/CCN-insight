import {readSelectedLanguage, subscribeSelectedLanguage, normalizeSelectedLanguage} from './lri-selected-language.js';
import {createReaderLane, validateSceneManifest} from './lri-reader-lane.js?v=1';
import {readReaderLocation, patchReaderURL} from './lri-reader-location.js?v=1';
import './lri-motion-scene.js';

// Shared interaction grammar, not a universal research narrative.
// The topic config contains only reader routes and UI labels; business rows stay in TableGit.
const UI={
 zh:{loading:'正在读取 TableGit 证据…',error:'证据暂不可用，未回退到旧数据。',retry:'重新读取',home:'返回首页',refresh:'刷新工作台',snapshot:'证据核验日期',boundary:'历史证据快照；本轮仅优化展示，不代表最新核验或实测。',source:'来源与边界',sourceOnly:'源语言记录 · 暂无完整英文',frozen:'原理示意 / 非实测回放',original:'独立 SVG 原图',detail:'当前阅读资料',rows:'条记录',all:'完整资料索引',missing:'该项资料尚未建立，不表示已验证。',references:'引用标识',open:'打开来源',allowed:'允许的结论',forbidden:'不能推导',status:'状态',unknown:'未提供',verificationUnknown:'核验日期未记录',notPass:'这里列出的是要求与研究记录，不是执行通过记录。',read:'阅读路径',sceneError:'图解加载失败；可查看独立 SVG。',reset:'清除筛选',filter:'在当前视图筛选',animation:'动画解释',verified:'核验日',locale:'显示原文而不是隐藏未译记录。',linked:'规范化关联',notes:'证据说明',figures:'图解与证据'},
 en:{loading:'Loading TableGit evidence…',error:'Evidence is unavailable. No legacy data fallback was used.',retry:'Retry read',home:'Home',refresh:'Refresh workbench',snapshot:'Evidence verified on',boundary:'Historical evidence snapshot. This iteration changes presentation, not verification or experimental results.',source:'Sources and boundaries',sourceOnly:'Source-language record · full English unavailable',frozen:'Conceptual illustration / not measured playback',original:'Standalone SVG',detail:'Reading material',rows:'records',all:'Complete record index',missing:'No record exists for this section. This is not a validation result.',references:'Reference identifiers',open:'Open source',allowed:'Supported wording',forbidden:'Unsupported inference',status:'Status',unknown:'Not provided',verificationUnknown:'Verification date not recorded',notPass:'These are requirements and research records, not successful test-run receipts.',read:'Reading path',sceneError:'Illustration unavailable. Open the standalone SVG.',reset:'Clear filter',filter:'Filter this view',animation:'Animated explanation',verified:'Reviewed',locale:'Untranslated records remain visible and labeled.',linked:'Canonical associations',notes:'Evidence notes',figures:'Illustrations and evidence'}
};
const FIELD={statement:['主张','Statement'],claim:['判断','Claim'],description:['说明','Description'],summary:['摘要','Summary'],grade:['证据等级','Evidence grade'],status:['状态','Status'],gap:['缺口','Gap'],track:['研究主线','Track'],exit:['退出条件','Exit criteria'],required:['所需证据','Required evidence'],environment:['验证环境','Environment'],minimum_evidence:['最小证据','Minimum evidence'],question:['验证问题','Question'],upgrade:['升级条件','Upgrade condition'],decision_use:['决策用途','Decision use'],evidence_refs:['引用标识','Reference identifiers'],allowed_wording:['允许的结论','Supported wording'],forbidden_wording:['不能推导','Unsupported inference'],risk:['风险','Risk'],impact:['影响','Impact'],mitigation:['应对','Mitigation'],severity:['优先级','Priority'],next_action:['下一步','Next action'],first_check:['优先检查','First check'],signal:['故障信号','Failure signal'],confidence:['置信度','Confidence'],boundary:['证据边界','Evidence boundary'],include:['纳入','Included'],exclude:['排除','Excluded'],type:['类型','Type'],class:['故障分类','Failure class']};
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function safeURL(value){if(typeof value!=='string'||!value.trim())return '';try{const u=new URL(value,location.href);return ['https:','http:'].includes(u.protocol)?u.href:'';}catch{return '';}}

const mountedReaders=new WeakMap();
export function mountDomain(config,options={}){
 const root=options.root||document.querySelector('[data-domain-workbench]');
 if(!root)throw new Error('Missing domain workbench root');
 mountedReaders.get(root)?.dispose();
 const host=root.querySelector('[data-domain-content]');
 const figure=root.querySelector('[data-domain-figure]');
 const rail=root.querySelector('[data-domain-navigation]');
 const search=root.querySelector('[data-domain-filter]');
 const routes=Object.fromEntries(config.routes.map(route=>[route.id,route]));
 let snapshot=null,pack=null,sceneManifest=null,view=config.routes[0].id,generation=0,drawGeneration=0,lang='zh',filter='';
 const timeoutMs=options.timeoutMs||15000;
 const evidenceLane=createReaderLane({timeoutMs}),diagramLane=createReaderLane({timeoutMs});
 const lifetime=new AbortController(),savedScenes=new Map();
 const assets=new URL(options.assetBase||'assets/',document.baseURI);
 const readTopic=options.readTopic||(()=>globalThis.LRITableGit.loadTopicWorkbench(config.topicId));
 const materialize=options.materialize||((snapshot,lang)=>globalThis.LRITableGit.materializeTopicWorkbench(snapshot,lang));
 const readManifest=options.readManifest||(async signal=>{
   const response=await fetch(new URL('scenes.json',assets),{credentials:'same-origin',cache:'no-cache',signal});
   if(!response.ok)throw new Error(`Scene manifest HTTP ${response.status}`);
   return response.json();
 });
 let disposed=false,suspended=false,manifestGeneration=0,manifestStatus='idle',manifestError='',dataStatus='idle',dataError='';
 let currentScene=null,sceneKey='',sceneId='',sceneTimer=null,sceneReady=false,userPaused=false,sceneEvents=null;
 const on=(target,type,handler)=>target.addEventListener(type,handler,{signal:lifetime.signal});

 const language=()=>readSelectedLanguage(document);
 const EXTRA={zh:{sceneLoading:'图解正在加载；下方研究资料可独立阅读。',diagramOnly:'图解暂不可用；研究资料未受影响。',diagramRetry:'仅重试图解',noMatches:'当前筛选无匹配记录，可清除筛选。',filterClear:'清除筛选',timedOut:'读取超时，请重试。'},en:{sceneLoading:'Loading illustration; research records can be read independently.',diagramOnly:'Illustration unavailable; research records are unaffected.',diagramRetry:'Retry illustration only',noMatches:'No records match this filter. Clear it to see all records.',filterClear:'Clear filter',timedOut:'Read timed out. Please retry.'}};
 const t=key=>EXTRA[lang][key]||UI[lang][key]||key;
 const label=key=>FIELD[key]?.[lang==='en'?1:0]||key.replaceAll('_',' ');
 const local=pair=>Array.isArray(pair)?pair[lang==='en'?1:0]:pair;
 const locationState=()=>readReaderLocation(location.href,{views:Object.keys(routes),defaultView:config.routes[0].id,aliases:config.aliases});
 const targetView=()=>locationState().view;
 function stateChange(){root.dataset.domainState=dataStatus;root.dataset.domainManifest=manifestStatus;root.dispatchEvent(new CustomEvent('domain-workbench:rendered',{bubbles:true,detail:{view,locale:lang,evidenceState:dataStatus,diagramState:manifestStatus,revision:snapshot?.source?.revision||'',rows:snapshot?.items?.length||0}}));}
 function rows(key){
   return [...(snapshot?.items||[])].filter(row=>row.collection_key===key).sort((a,b)=>a.ordinal-b.ordinal);
 }
 function payload(row){
   const chosen=row[`payload_${lang}`];
   const fallback=chosen==null;
   return {value:fallback?row.payload_zh:chosen,fallback:lang==='en'&&fallback};
 }
 function entities(row){
   const refs=row.entity_refs||{};
   return Object.entries(refs).flatMap(([kind,ids])=>(ids||[]).map(id=>({kind,entity:pack?.entities?.[kind]?.[id]})).filter(x=>x.entity));
 }
 function refLinks(row){
   return entities(row).filter(x=>x.kind==='contents').map(({entity})=>{
     const link=entity.locations?.find(x=>x.is_primary)||entity.locations?.[0];
     const href=safeURL(link?.url||entity.url||'');
     return href?`<a class="domain-source-link" href="${esc(href)}" target="_blank" rel="noopener noreferrer">${esc(entity.title||entity.name||t('open'))} ↗</a>`:'';
   }).join('');
 }
 function format(value,depth=0,key=''){
   if(value==null)return '—';
   if(typeof value==='string'&&/^(url|source_url|link|href)$/i.test(key)&&/^https?:\/\//i.test(value)&&safeURL(value))return `<a href="${esc(safeURL(value))}" target="_blank" rel="noopener noreferrer">${esc(value)}</a>`;
   if(typeof value!=='object')return esc(value);
   if(depth>5)return esc(JSON.stringify(value));
   if(Array.isArray(value))return `<ul>${value.map(item=>`<li>${format(item,depth+1)}</li>`).join('')}</ul>`;
   return `<dl class="domain-fields">${Object.entries(value).filter(([key])=>!key.startsWith('$')).map(([key,v])=>`<div><dt>${esc(label(key))}</dt><dd>${format(v,depth+1,key)}</dd></div>`).join('')}</dl>`;
 }
 function record(row,key){
   const {value,fallback}=payload(row);if(value==null)return '';
   const obj=typeof value==='object'&&!Array.isArray(value)?value:null;
   const id=row.item_id||row.object_id;
   const identity=entities(row).find(x=>x.kind==='capabilities')?.entity||entities(row).find(x=>x.kind==='resources')?.entity||entities(row).find(x=>x.kind==='contents')?.entity;
   const title=obj?(obj.statement||obj.claim||obj.name||obj.title||obj.environment||obj.risk||obj.gap||identity?.name||identity?.title||obj.class||obj.id||key):value;
   const code=obj?.id||obj?.level||String(row.ordinal??'');
   const entries=obj?Object.fromEntries(Object.entries(obj).filter(([k])=>!['statement','claim','name','title','id','level','allowed_wording','forbidden_wording'].includes(k)&&obj[k]!==title)):null;
   const wording=obj?.allowed_wording||obj?.forbidden_wording?`<div class="domain-contrast"><section><h4>${t('allowed')}</h4><p>${esc(obj.allowed_wording||'—')}</p></section><section><h4>${t('forbidden')}</h4><p>${esc(obj.forbidden_wording||'—')}</p></section></div>`:'';
   return `<article class="card domain-record" id="record-${esc(id)}" data-record-id="${esc(id)}" ${fallback?'lang="zh-CN"':''}><div class="domain-record-meta"><span>${esc(code)}</span>${fallback?`<span class="domain-source-only">${t('sourceOnly')}</span>`:''}</div><h3>${esc(title)}</h3>${wording}${entries?format(entries):''}${refLinks(row)}</article>`;
 }
 function rowMatches(row){return !filter||String(JSON.stringify(payload(row).value)||'').toLowerCase().includes(filter.toLowerCase())||entities(row).some(x=>JSON.stringify(x.entity).toLowerCase().includes(filter.toLowerCase()));}
 function renderRecords(){
   if(!snapshot)return;
   const route=routes[view];
   const sections=route.groups||[];
   const groups=view==='records'?[...new Set([...snapshot.items.map(x=>x.collection_key),...snapshot.objects.map(x=>x.object_key)])].map(key=>({key,title:[key.replaceAll('_',' '),key.replaceAll('_',' ')]})):sections;
   host.innerHTML=groups.map(({key,title})=>{
     const found=rows(key).filter(rowMatches);
     const objects=snapshot.objects.filter(row=>row.object_key===key).filter(rowMatches);
     const selected=[...found,...objects];
     return `<section class="domain-group" data-domain-collection="${esc(key)}"><header><h2>${esc(local(title))}</h2><span>${selected.length} ${t('rows')}</span></header><div class="domain-records">${selected.length?selected.map(row=>record(row,key)).join(''):`<p class="domain-empty">${t(filter?'noMatches':'missing')}${filter?` <button type="button" data-domain-clear>${t('filterClear')}</button>`:''}</p>`}</div></section>`;
   }).join('');
   root.querySelector('[data-domain-reading-title]').textContent=local(route.title);
   stateChange();
 }
 function rememberScene(){
   if(!currentScene||!sceneReady)return;
   const duration=currentScene.duration,time=currentScene.currentTime;
   savedScenes.set(sceneId,{time:duration>0?time%duration:0,paused:userPaused,rate:currentScene.playbackRate,fit:currentScene.getAttribute('fit')||'fit'});
 }
 function clearScenes(){
   rememberScene();++drawGeneration;clearTimeout(sceneTimer);sceneTimer=null;sceneEvents?.abort();sceneEvents=null;
   currentScene=null;sceneReady=false;sceneKey='';sceneId='';figure.removeAttribute('aria-busy');figure.replaceChildren();
   // The component owns offscreen, visibility, reduced-motion and disconnect behavior.
 }
 function diagramNotice(message,detail=''){
   clearScenes();figure.hidden=false;figure.removeAttribute('aria-busy');
   figure.innerHTML=`<div class="callout" role="status"><p>${esc(message)}</p>${detail?`<p>${esc(detail)}</p>`:''}<button type="button" data-domain-diagram-retry>${t('diagramRetry')}</button></div>`;
 }
 function scenes(force=false){
   if(disposed||suspended)return;
   const selected=routes[view].scene;
   if(!snapshot||!selected){clearScenes();figure.hidden=true;return;}
   if(manifestStatus==='loading'||manifestStatus==='idle'){
     clearScenes();figure.hidden=false;figure.setAttribute('aria-busy','true');figure.innerHTML=`<p role="status">${t('sceneLoading')}</p>`;return;
   }
   if(manifestStatus==='error'){diagramNotice(t('diagramOnly'),manifestError);return;}
   const item=sceneManifest?.scenes.find(scene=>scene.id===selected),choice=item?.locales?.[lang];
   if(!choice){diagramNotice(t('diagramOnly'));return;}
   const url=new URL(choice.file,assets);url.searchParams.set('v',sceneManifest.version||'1');
   const key=selected+'|'+url.href+'|'+lang;
   if(!force&&currentScene&&sceneKey===key)return;
   // Locale variants reuse the semantic scene host. Never detach a fullscreen host.
   const reuse=!force&&currentScene&&sceneId===selected;
   if(reuse){rememberScene();++drawGeneration;clearTimeout(sceneTimer);sceneEvents?.abort();sceneReady=false;}
   else clearScenes();
   figure.hidden=false;figure.setAttribute('aria-busy','true');
   const sequence=drawGeneration,restore=savedScenes.get(selected);
   const intro=reuse?figure.querySelector('.domain-figure-intro'):document.createElement('div');intro.className='domain-figure-intro';
   intro.innerHTML=`<span>${t('frozen')}</span><h2>${esc(choice.title)}</h2>`;
   const scene=reuse?currentScene:document.createElement('lri-motion-scene');
   sceneEvents=new AbortController();const signal=sceneEvents.signal;
   currentScene=scene;sceneKey=key;sceneId=selected;userPaused=restore?.paused||false;
   scene.setAttribute('mobile-viewbox',choice.mobile_viewbox);
   scene.setAttribute('aria-label',choice.title);scene.setAttribute('fit',restore?.fit||'fit');
   scene.setAttribute('controls','');scene.setAttribute('lang',lang);
   const current=()=>!disposed&&!suspended&&sequence===drawGeneration&&currentScene===scene&&scene.isConnected;
   scene.addEventListener('scene-state',event=>{
     if(!current())return;
     const status=event.detail.state;
     if(status==='paused')userPaused=true;
     else if(['playing','offscreen','hidden','static'].includes(status))userPaused=false;
   },{signal});
   scene.addEventListener('scene-ready',()=>{
     if(!current())return;clearTimeout(sceneTimer);sceneTimer=null;sceneReady=true;
     if(restore){scene.playbackRate=restore.rate;scene.seek(Math.min(restore.time,scene.duration||restore.time));if(!restore.paused)scene.play();}
     figure.removeAttribute('aria-busy');stateChange();
   },{once:true,signal});
   scene.addEventListener('scene-error',event=>{
     if(!current())return;diagramNotice(t('diagramOnly'),event.detail?.message||'');stateChange();
   },{once:true,signal});
   sceneTimer=setTimeout(()=>{if(current()&&!sceneReady){diagramNotice(t('diagramOnly'),t('timedOut'));stateChange();}},timeoutMs);
   scene.setAttribute('src',url.href);
   if(!reuse)figure.append(intro,scene);
 }
 function chrome(){
   document.documentElement.lang=lang==='en'?'en':'zh-CN';
   rail.innerHTML=config.routes.map((route,i)=>`<a class="topic-path-link" data-domain-route="${route.id}" href="${esc(patchReaderURL(location.href,{view:route.id,q:'',lang}))}"><b>${String(i+1).padStart(2,'0')} · ${esc(local(route.title))}</b><span>${esc(local(route.note||route.title))}</span></a>`).join('');
   for(const el of root.querySelectorAll('[data-domain-label]'))el.textContent=t(el.dataset.domainLabel);
   search.placeholder=t('filter');search.setAttribute('aria-label',t('filter'));
   if(!snapshot){
     root.querySelector('[data-domain-title]').textContent=config.code||config.topicId;
     root.querySelector('[data-domain-subtitle]').textContent='';
     for(const attr of ['freshness','status','revision','locale'])root.querySelector(`[data-domain-${attr}]`).textContent=attr==='status'?t(dataStatus==='error'?'error':'loading'):'';
     return;
   }
   const title=snapshot.profile[`payload_${lang}`]?.title||snapshot.profile.payload_zh.title;
   root.querySelector('[data-domain-title]').textContent=title;document.title=`${title} · LRI`;
   root.querySelector('[data-domain-subtitle]').textContent=snapshot.profile[`payload_${lang}`]?.subtitle||'';
   root.querySelector('[data-domain-freshness]').textContent=`${snapshot.profile.last_verified || t('verificationUnknown')} · ${t('boundary')}`;
   root.querySelector('[data-domain-status]').textContent=`${snapshot.profile.status} · ${snapshot.items.length} ${t('rows')} · ${snapshot.profile.last_verified || t('verificationUnknown')}`;
   const rawRevision=snapshot.source?.revision||snapshot.source?.tablegit?.revision||snapshot.source?.tablegit?.status?.revision||'';
   root.querySelector('[data-domain-revision]').textContent=rawRevision?`TableGit · ${rawRevision.slice(0,12)}`:'TableGit · revision-pinned snapshot';
   root.querySelector('[data-domain-locale]').textContent=`${lang==='en'?snapshot.items.filter(x=>x.payload_en==null).length:0} ${lang==='en'?t('sourceOnly'):''} ${t('locale')}`;
 }
 function renderDataState(){
   if(snapshot){renderRecords();return;}
   host.innerHTML=dataStatus==='error'?`<div class="callout" role="alert"><h2>${t('error')}</h2><p>${esc(dataError)}</p><button type="button" data-domain-retry>${t('retry')}</button></div>`:`<p role="status">${t('loading')}</p>`;
   root.querySelector('[data-domain-reading-title]').textContent=local(routes[view].title);
 }
 function navigate(next,push=false){
   if(disposed)return;
   view=routes[next]?next:config.routes[0].id;
   if(push)history.pushState({view},'',patchReaderURL(location.href,{view,q:filter,lang}));
   else filter=locationState().q;
   search.value=filter;
   for(const link of rail.querySelectorAll('[data-domain-route]')){
     const yes=link.dataset.domainRoute===view;link.toggleAttribute('data-current',yes);yes?link.setAttribute('aria-current','page'):link.removeAttribute('aria-current');
   }
   renderDataState();scenes();stateChange();
 }
 async function loadDiagrams(){
   if(disposed)return;
   const ticket=++manifestGeneration;manifestStatus='loading';manifestError='';sceneManifest=null;scenes();stateChange();
   try{
     const value=await diagramLane.run(readManifest);
     if(disposed||suspended||ticket!==manifestGeneration)return;
     sceneManifest=validateSceneManifest(value);manifestStatus='ready';
   }catch(error){
     if(disposed||suspended||ticket!==manifestGeneration||error.name==='AbortError')return;
     manifestStatus='error';manifestError=error.name==='TimeoutError'?t('timedOut'):error.message;
   }
   scenes();stateChange();
 }
 async function loadEvidence(refresh=false){
   const ticket=++generation;snapshot=null;pack=null;dataStatus='loading';dataError='';
   clearScenes();figure.hidden=true;root.setAttribute('aria-busy','true');chrome();navigate(targetView());
   try{
     if(refresh&&!options.readTopic)globalThis.LRITableGit?.invalidate();
     const next=await evidenceLane.run(readTopic);
     if(disposed||suspended||ticket!==generation)return;
     if(!next?.profile||!Array.isArray(next.items)||!Array.isArray(next.objects))throw new Error('Invalid TableGit topic snapshot');
     lang=language();pack=materialize(next,lang);snapshot=next;dataStatus='ready';
   }catch(error){
     if(disposed||suspended||ticket!==generation||error.name==='AbortError')return;
     snapshot=null;pack=null;dataStatus='error';dataError=error.name==='TimeoutError'?t('timedOut'):error.message;
   }finally{
     if(!disposed&&!suspended&&ticket===generation){root.removeAttribute('aria-busy');chrome();navigate(targetView());}
   }
 }
 function load(refresh=false){
   if(disposed)return Promise.resolve();suspended=false;
   // Two independent requests: artwork failure/latency must not gate evidence rendering.
   return Promise.allSettled([loadEvidence(refresh),loadDiagrams()]);
 }
 function setLanguage(next){
   next=normalizeSelectedLanguage(next);
   if(disposed||!next||lang===next)return;lang=next;
   if(snapshot)pack=materialize(snapshot,lang);
   chrome();navigate(view);
 }
 function restoreLocation(){
   if(disposed)return;
   const requested=normalizeSelectedLanguage(locationState().locale),shell=document.querySelector('lri-site-shell');
   // A history language is a request to its owner, not a second language authority.
   if(requested&&normalizeSelectedLanguage(shell?.locale)!==requested&&typeof shell?.applyLocale==='function')
     Promise.resolve().then(()=>shell.applyLocale(requested,{announce:true})).then(()=>{if(!disposed){setLanguage(language());navigate(targetView());}}).catch(()=>{});
   setLanguage(language());navigate(targetView());
 }
 on(rail,'click',event=>{
   const link=event.target instanceof Element?event.target.closest('a[data-domain-route]'):null;
   if(!link||event.button!==0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
   event.preventDefault();filter='';search.value='';navigate(link.dataset.domainRoute,true);
 });
 on(root,'click',event=>{
   const element=event.target instanceof Element?event.target:null;
   if(element?.closest('[data-domain-diagram-retry]')){if(manifestStatus==='ready')scenes(true);else loadDiagrams();}
   else if(element?.closest('[data-domain-retry]'))load(true);
   else if(element?.closest('[data-domain-clear]')){filter='';search.value='';history.replaceState(history.state,'',patchReaderURL(location.href,{q:''}));renderDataState();search.focus();}
 });
 on(search,'input',()=>{filter=search.value;history.replaceState(history.state,'',patchReaderURL(location.href,{q:filter}));if(snapshot)renderRecords();});
 on(window,'popstate',restoreLocation);on(window,'hashchange',restoreLocation);
 subscribeSelectedLanguage(next=>{
   if(disposed)return;
   history.replaceState(history.state,'',patchReaderURL(location.href,{lang:next}));setLanguage(next);
 },{signal:lifetime.signal,immediate:false});
 on(window,'pagehide',()=>{suspended=true;++generation;++manifestGeneration;evidenceLane.cancel();diagramLane.cancel();clearScenes();});
 on(window,'pageshow',event=>{if(event.persisted)load();});
 function dispose(){
   if(disposed)return;disposed=true;++generation;++manifestGeneration;
   lifetime.abort();evidenceLane.dispose();diagramLane.dispose();clearScenes();savedScenes.clear();root.removeAttribute('aria-busy');mountedReaders.delete(root);
 }
 lang=language();const api=Object.freeze({reload:()=>load(true),retryDiagram:loadDiagrams,dispose});mountedReaders.set(root,api);load();
 return api;
}

