/* Shared compression principles: immutable-revision TableGit content, no embedded facts. */
(() => {
 'use strict';
 const table='ic_compression_foundations',required=['quantization','pruning_sparsity','distillation','low_rank'];
 const anchors={quantization:'quantization',pruning_sparsity:'pruning-sparsity',distillation:'distillation',low_rank:'low-rank',shared:'reading-boundaries'};
 const check=(ok,message)=>{if(!ok)throw new Error(message);};
 function validate(result,revision){
  check(result.revision===revision&&/^[a-f0-9]{40}$/.test(revision),'Foundation revision mismatch');
  check(Array.isArray(result.records)&&result.records.length>0&&result.records.length<=100&&result.page?.truncated===false&&result.page.total===result.records.length,'Incomplete foundation collection');
  const ids=new Set();
  for(const row of result.records){
   check(row.business_id==='cloud-core'&&row.topic_id==='cloud_core'&&row.foundation_id&&!ids.has(row.foundation_id),'Foreign or duplicate foundation');ids.add(row.foundation_id);
   check([...required,'shared'].includes(row.method_id)&&['overview','method','quantization_step','setting','caveat'].includes(row.section_kind)&&Number.isSafeInteger(row.position),'Invalid foundation section');
   check(['title_zh','title_en','summary_zh','summary_en','body_zh','body_en'].every(k=>typeof row[k]==='string'&&row[k].trim()),'Incomplete bilingual foundation');
   check(/^\d{4}-\d{2}-\d{2}$/.test(row.reviewed_at)&&row.source_title&&row.evidence_locator,'Unreviewed foundation');
   const url=new URL(row.source_url);check(url.protocol==='https:'&&!url.username&&!url.password&&!['localhost','127.0.0.1'].includes(url.hostname),'Unsafe foundation source');
   for(const key of url.searchParams.keys())check(!/token|password|secret|credential|api.?key|signature|bearer/i.test(key),'Credential-bearing source');
  }
  for(const method of required)check(result.records.filter(r=>r.method_id===method&&r.section_kind==='method').length===1,'Missing or duplicate method foundation');
  return {revision,records:result.records.slice().sort((a,b)=>a.position-b.position)};
 }
 async function load(api){
  const meta=await api.loadTableMetadata(table),revision=meta.revision;
  const result=await api.loadTablePage(table,{filterField:'topic_id',filterValue:'cloud_core',expectedRevision:revision,offset:0,limit:100});
  return validate(result,revision);
 }
 const lessonTables={steps:'ic_foundation_lesson_steps',values:'ic_foundation_lesson_values'};
 const sceneMethods={quantization:['quant-original','quant-parameters','quant-encode','quant-pack','quant-reconstruct','quant-error'],pruning_sparsity:['prune-original','prune-mask','prune-storage','prune-execution'],low_rank:['rank-original','rank-factors','rank-compute','rank-error'],distillation:['distill-teacher','distill-target','distill-training','distill-student']};
 function validateLessons(steps,values,revision,foundations){
  const ids=new Set(),foundationIds=new Set(foundations.map(r=>r.foundation_id));
  for(const [collection,key]of [[steps,'step_id'],[values,'value_id']]){
   check(collection.revision===revision&&Array.isArray(collection.records)&&collection.records.length>0&&collection.records.length<=100&&collection.page?.truncated===false&&collection.page.total===collection.records.length,'Incomplete or mismatched lesson collection');
   for(const row of collection.records){check(row.business_id==='cloud-core'&&row.topic_id==='cloud_core'&&required.includes(row.method_id)&&row.example_id&&row[key]&&!ids.has(row[key])&&Number.isSafeInteger(row.position),'Invalid lesson identity');ids.add(row[key]);}
  }
  for(const row of steps.records){
   check(sceneMethods[row.method_id].includes(row.scene_kind)&&foundationIds.has(row.foundation_id)&&Number.isSafeInteger(row.duration_ms)&&row.duration_ms>=3000&&row.duration_ms<=30000,'Invalid lesson stage');
   check(['title_zh','title_en','narration_zh','narration_en','takeaway_zh','takeaway_en','source_title','evidence_locator'].every(k=>typeof row[k]==='string'&&row[k].trim())&&/^\d{4}-\d{2}-\d{2}$/.test(row.reviewed_at),'Incomplete lesson prose');
   const url=new URL(row.source_url);check(url.protocol==='https:'&&!url.username&&!url.password&&!/token|secret|password|credential|api.?key/i.test(url.search),'Unsafe lesson source');
  }
  for(const row of values.records)check(Number.isFinite(row.numeric_value)&&Number.isSafeInteger(row.row_index)&&Number.isSafeInteger(row.column_index)&&typeof row.bit_pattern==='string'&&/^[01]*$/.test(row.bit_pattern),'Invalid lesson number');
  for(const method of required){
   const subset=steps.records.filter(r=>r.method_id===method).sort((a,b)=>a.position-b.position),numbers=values.records.filter(r=>r.method_id===method);
   check(JSON.stringify(subset.map(r=>r.scene_kind))===JSON.stringify(sceneMethods[method])&&new Set(subset.map(r=>r.example_id)).size===1&&numbers.length>0&&numbers.every(r=>r.example_id===subset[0].example_id),'Incomplete or mixed lesson');
   const coordinate=new Set();for(const row of numbers){const key=[row.role,row.row_index,row.column_index,row.position].join(':');check(!coordinate.has(key),'Duplicate lesson value');coordinate.add(key);}
  }
  return {steps:steps.records,values:values.records,revision};
 }
 async function loadLessons(api,revision,foundations){
  const [steps,values]=await Promise.all(Object.values(lessonTables).map(table=>api.loadTablePage(table,{filterField:'topic_id',filterValue:'cloud_core',expectedRevision:revision,offset:0,limit:100})));
  return validateLessons(steps,values,revision,foundations);
 }
 globalThis.LRICompressionFoundations=Object.freeze({load,validate,loadLessons,validateLessons});
 if(!globalThis.document||document.body?.dataset.compressionFoundations!=='true')return;
 let locale='zh',snapshot=null,epoch=0,referenceNumbers=new Map();
 try{locale=localStorage.getItem('lri_locale')==='en'?'en':'zh';}catch(_){}
 const $=id=>document.getElementById(id),ui=key=>globalThis.LRICloudFoundationUIPacks[locale].strings[key],pick=(row,key)=>row[key+'_'+locale];
 const el=(tag,text='',cls='')=>{const n=document.createElement(tag);n.textContent=String(text);if(cls)n.className=cls;return n;};
 const body=(host,text)=>{for(const p of text.split(/\n+/).filter(v=>v.trim()))host.append(el('p',p));};
 function sourceLink(row,label){const a=el('a',label||row.source_title);a.href=row.source_url;a.target='_blank';a.rel='noopener noreferrer';return a;}

 function citation(row){
  const n=referenceNumbers.get(row.source_url),sup=el('sup','','foundation-cite'),a=el('a','['+n+']');
  a.href='#foundation-ref-'+n;a.title=row.source_title+' · '+row.evidence_locator;
  a.setAttribute('aria-label',ui('reference')+' '+n+': '+row.source_title+' · '+row.evidence_locator);sup.append(a);return sup;
 }
 function appendCitation(host,row){const last=host.querySelector('p:last-of-type');(last||host).append(citation(row));}

 function formula(host,row){if(!row.formula)return;const p=el('p',row.formula,'foundation-formula');p.setAttribute('aria-label',ui('formula')+': '+row.formula);host.append(p);}
 function addCard(host,row,{step=false}={}){
  const article=el('article','','foundation-card'+(step?' foundation-step':''));article.id=row.foundation_id;article.dataset.foundationId=row.foundation_id;
  article.append(el(step?'h4':'h3',pick(row,'title')));
  const layout=el('div','','foundation-explanation'),copy=el('div','','foundation-prose');
  copy.append(el('p',pick(row,'summary'),'foundation-lead'));formula(copy,row);body(copy,pick(row,'body'));
  appendCitation(copy,row);layout.append(copy);article.append(layout);host.append(article);
 }
 function addQuickReference(host,method){
  const word=(zh,en)=>locale==='en'?en:zh,parts=pick(method,'body').split(/\n+/).filter(v=>v.trim()),quick=el('section','','foundation-quickref');quick.dataset.foundationMethod=method.method_id;quick.dataset.sectionOutline='false';
  quick.append(el('h3',word('原理速查','Principle quick reference')));
  const list=el('dl','','foundation-quickref-list');
  const row=(zh,en)=>{const item=el('div','','foundation-quickref-row'),definition=el('dd');item.append(el('dt',word(zh,en)),definition);list.append(item);return definition;};
  const definition=row('定义','Definition');definition.append(el('p',parts[0]));
  const equation=row('公式','Formula');if(method.formula)formula(equation,method);else equation.append(el('p',word('当前条目未登记公式。','No formula is recorded for this entry.')));
  const conditions=row('成立条件与符号','Conditions and notation');body(conditions,parts.slice(1).join('\n'));appendCitation(conditions,method);quick.append(list);
  const topicMethods={quantization:'precision',pruning_sparsity:'selection',distillation:'distillation',low_rank:'factorization'},names={
   quantization:[['parameters','权重量化','Weight quantization'],['activations','激活量化','Activation quantization'],['kv_cache','KV Cache 量化','KV Cache quantization']],
   pruning_sparsity:[['parameters','权重剪枝','Weight pruning'],['activations','激活剪枝','Activation pruning'],['kv_cache','KV Cache 剪枝','KV Cache pruning']],
   low_rank:[['parameters','权重低秩分解','Low-rank weights'],['activations','激活低秩分解','Low-rank activations'],['kv_cache','KV Cache 低秩分解','Low-rank KV Cache']],
   distillation:[['parameters','知识蒸馏 · 主专题','Knowledge distillation · Main topic'],['activations','特征监督 · 关联案例','Feature supervision · Related case'],['kv_cache','紧凑 KV 结构 · 关联案例','Compact KV structures · Related case']]
  };
  const links=el('nav','','foundation-topic-links');links.setAttribute('aria-label',word('进入对应研究专题','Open related research topics'));
  for(const [target,zh,en]of names[method.method_id]){const id=target+'-'+topicMethods[method.method_id],a=el('a',word(zh,en)+' →'),url=new URL('topic.html',location.href),params=new URLSearchParams(location.search);url.searchParams.set('topic',id);for(const key of ['month','scope'])if(params.has(key))url.searchParams.set(key,params.get(key));a.href=url.pathname+url.search;a.dataset.foundationTopic=id;if(method.method_id==='distillation')a.dataset.topicRelation=target==='parameters'?'main':'related';links.append(a);}quick.append(links);host.append(quick);
 }
 function addLessonReference(host,method,steps){
  const word=(zh,en)=>locale==='en'?en:zh,section=el('section','','foundation-lesson-reference');section.dataset.sectionOutline='false';section.append(el('h3',word('算例公式与要点','Worked-example formulas and takeaways')));
  const scroll=el('div','','foundation-reference-scroll');scroll.tabIndex=0;scroll.setAttribute('role','region');scroll.setAttribute('aria-label',word('本方法全部算例步骤','All worked-example steps for this method'));
  const table=el('table','','foundation-reference-table');table.append(el('caption',word('与上方动画使用同一组算例；各步公式与要点可直接查阅。','The same worked example as the animation above, with every formula and takeaway available for reference.')));
  const head=el('thead'),heading=el('tr'),labels=[word('步骤','Step'),word('计算式','Formula'),word('理解要点','Takeaway')];for(const label of labels){const th=el('th',label);th.scope='col';heading.append(th);}head.append(heading);table.append(head);
  const tbody=el('tbody');for(const step of steps){const tr=el('tr');tr.dataset.lessonStep=step.step_id;const title=el('th',pick(step,'title'));title.scope='row';title.dataset.label=labels[0];const equation=el('td'),takeaway=el('td');equation.dataset.label=labels[1];takeaway.dataset.label=labels[2];equation.append(el('p',step.formula||'—','foundation-example-formula'));const text=el('p',pick(step,'takeaway'));text.append(citation(step));takeaway.append(text);tr.append(title,equation,takeaway);tbody.append(tr);}table.append(tbody);scroll.append(table);section.append(scroll);host.append(section);
 }
 function updateUI(){
  document.documentElement.lang=locale==='en'?'en':'zh-CN';document.title=ui('page_title')+' · 极智 AI Infra';
  for(const node of document.querySelectorAll('[data-i18n-key]')){const text=ui(node.dataset.i18nKey);if(text)node.textContent=text;}
  document.body.dataset.lriReaderNavigationLabel=ui('reading_order');
  for(const a of document.querySelectorAll('a[data-preserve-scope]')){const u=new URL(a.getAttribute('href'),location.href),p=new URLSearchParams(location.search);for(const key of ['month','scope'])if(p.has(key))u.searchParams.set(key,p.get(key));a.href=u.href;}
  const returnTopic=new URLSearchParams(location.search).get('return_topic'),back=document.querySelector('a[data-i18n-key="back"]');
  if(back&&/^(parameters|activations|kv_cache)-[a-z_]+$/.test(returnTopic||'')){
   const target=new URL('topic.html',location.href),params=new URLSearchParams(location.search);target.searchParams.set('topic',returnTopic);for(const key of ['month','scope'])if(params.has(key))target.searchParams.set(key,params.get(key));target.hash='research-overview-basics';back.href=target.href;back.textContent=locale==='en'?'← Return to the research topic':'← 返回刚才的研究专题';
  }
 }
 function render(){
  updateUI();if(!snapshot)return;
  const root=$('foundations-content');root.replaceChildren();root.dataset.revision=snapshot.revision;
  const rows=snapshot.records,methods=rows.filter(r=>r.section_kind==='method'),evidenceRows=[...rows,...snapshot.lessons.steps];referenceNumbers=new Map([...new Set(evidenceRows.map(r=>r.source_url))].map((url,i)=>[url,i+1]));
  const overview=el('section','','foundation-overview');overview.id='foundations-overview';overview.append(el('h2',ui('overview')));
  for(const row of rows.filter(r=>r.section_kind==='overview')){overview.append(el('h3',pick(row,'title')),el('p',pick(row,'summary'),'foundation-lead'));body(overview,pick(row,'body'));appendCitation(overview,row);}
  const scroll=el('div','','table-wrap foundation-comparison'),tableNode=el('table');tableNode.append(el('caption',ui('comparison_caption')));const head=el('thead'),tr=el('tr');for(const key of ['method','what_changes','formal_view']){const th=el('th',ui(key));th.scope='col';tr.append(th);}head.append(tr);tableNode.append(head);
  const tbody=el('tbody');for(const row of methods){const tr=el('tr'),th=el('th'),a=el('a',ui('nav_'+row.method_id));a.href='#'+anchors[row.method_id];th.scope='row';th.append(a);tr.append(th,el('td',pick(row,'summary')),el('td',row.formula||'—','foundation-table-formula'));tbody.append(tr);}tableNode.append(tbody);scroll.append(tableNode);overview.append(scroll);root.append(overview);
  const nav=$('foundations-reading-nav');nav.replaceChildren();const link=(id,title)=>{const a=el('a',title);a.href='#'+id;nav.append(a);};link(overview.id,ui('overview'));
  for(const method of methods){const section=el('section','','foundation-method');section.id=anchors[method.method_id];section.dataset.sectionLabel=pick(method,'title');section.append(el('h2',pick(method,'title')));
   const intro=el('p',pick(method,'summary'),'foundation-lead');intro.append(citation(method));section.append(intro);
   addQuickReference(section,method);const lessonSteps=snapshot.lessons.steps.filter(r=>r.method_id===method.method_id).sort((a,b)=>a.position-b.position);
   const player=document.createElement('lri-foundation-lesson');player.lesson={method:method.method_id,steps:lessonSteps,values:snapshot.lessons.values.filter(r=>r.method_id===method.method_id),locale,ui:globalThis.LRICloudFoundationUIPacks[locale].strings,referenceNumbers:Object.fromEntries(referenceNumbers)};section.append(player);addLessonReference(section,method,lessonSteps);
   for(const row of rows.filter(r=>r.method_id===method.method_id&&(!['method','overview','quantization_step'].includes(r.section_kind)||['quant-group','quant-execution'].includes(r.foundation_id))))addCard(section,row);
   root.append(section);link(section.id,ui('nav_'+method.method_id));
  }
  const shared=rows.filter(r=>r.method_id==='shared'&&r.section_kind!=='overview');if(shared.length){const section=el('section','','foundation-method');section.id='reading-boundaries';section.append(el('h2',ui('boundaries')));for(const row of shared)addCard(section,row);root.append(section);link(section.id,ui('boundaries'));}
  const refs=el('section','','foundation-method');refs.id='foundations-references';refs.append(el('h2',ui('references')));const list=el('ol','','foundation-references'),seen=new Set();for(const row of evidenceRows){if(seen.has(row.source_url))continue;seen.add(row.source_url);const li=el('li');li.id='foundation-ref-'+referenceNumbers.get(row.source_url);if(new URL(row.source_url).hostname.includes('zhihu.com'))li.append(el('span',ui('further_reading')+' · ','meta'));li.append(sourceLink(row));const locators=[...new Set(evidenceRows.filter(r=>r.source_url===row.source_url).map(r=>r.evidence_locator))];li.append(el('p',locators.join(' / ')+' · '+row.reviewed_at,'meta'));list.append(li);}refs.append(list);root.append(refs);link(refs.id,ui('references'));
  const checked=rows.map(r=>r.reviewed_at).sort().at(-1);$('foundations-status').textContent=ui('loaded')+' · '+ui('reviewed')+' '+checked;$('foundations-status').setAttribute('role','status');root.dataset.foundationReady='true';
  document.dispatchEvent(new Event('lri:sections-changed'));if(location.hash)requestAnimationFrame(()=>document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView({block:'start'}));
 }
 async function start(){
  const current=++epoch;updateUI();$('foundations-status').textContent=ui('loading');$('foundations-refresh').disabled=true;
  try{const data=await load(globalThis.LRITableGit);const [lessons]=await Promise.all([loadLessons(globalThis.LRITableGit,data.revision,data.records),import('./foundation-player.js?v=foundation-lessons-v5')]);if(current!==epoch)return;snapshot={...data,lessons};render();}
  catch(error){if(current!==epoch)return;snapshot=null;$('foundations-content').replaceChildren();$('foundations-content').removeAttribute('data-foundation-ready');$('foundations-status').textContent=ui('load_failed');$('foundations-status').setAttribute('role','alert');console.error('Compression foundations:',error);}
  finally{if(current===epoch)$('foundations-refresh').disabled=false;}
 }
 $('foundations-refresh').addEventListener('click',()=>{globalThis.LRITableGit.invalidate();start();});
 document.addEventListener('lri:locale-change',event=>{locale=event.detail.locale==='en'?'en':'zh';render();});
 document.addEventListener('lri:force-refresh-ready',()=>{globalThis.LRITableGit.invalidate();start();});
 start();
})();


