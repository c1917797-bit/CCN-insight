/* Exact-revision, per-topic research cards. Business content lives in TableGit. */
(() => {
 'use strict';
 const check=(ok,text)=>{if(!ok)throw new Error('Topic dossier: '+text);};
 async function read(table,key,revision,api){
  const records=[],seen=new Set();let offset=0,total=null;
  for(;;){
   const result=await api.loadTablePage(table,{filterField:'compression_topic_id',filterValue:key,expectedRevision:revision,offset,limit:100});
   check(result.revision===revision,'revision mismatch');const p=result.page;
   check(p&&Number.isSafeInteger(p.total)&&p.total>=0&&p.total<=200&&Array.isArray(result.records)&&result.records.length<=100&&typeof p.truncated==='boolean','invalid pagination');
   if(total===null)total=p.total;else check(total===p.total,'total changed');
   check(p.offset===undefined||p.offset===offset,'offset changed');
   for(const row of result.records){const id=table==='ic_compression_mechanism_steps'?row.step_id:table==='ic_compression_research_frames'?row.frame_id:table==='ic_compression_research_routes'?row.route_id:row.card_id+(table.endsWith('_refs')?'__'+row.reference_id:'');check(row.business_id==='cloud-core'&&row.topic_id==='cloud_core'&&row.compression_topic_id===key&&!seen.has(id),'foreign or duplicate row');seen.add(id);records.push(row);}
   check(records.length<=total&&p.truncated===(records.length<total),'incomplete pagination');
   if(!p.truncated)break;
   check(result.records.length>0&&p.nextOffset===offset+result.records.length,'cursor stalled');offset=p.nextOffset;
  }return records;
 }
 async function load(key,revision,api){
  check(key&&revision,'missing topic/revision');
  const [cards,refs,steps,frames,routes]=await Promise.all([read('ic_compression_topic_cards',key,revision,api),read('ic_compression_topic_card_refs',key,revision,api),read('ic_compression_mechanism_steps',key,revision,api),read('ic_compression_research_frames',key,revision,api),read('ic_compression_research_routes',key,revision,api)]);
  check(cards.length>0,'no reviewed research content');const byId=new Map(cards.map(row=>[row.card_id,row]));
  for(const c of cards)check(['mechanism','papers','comparison','boundary','implication','watch'].includes(c.section_kind)&&['step','analysis','case'].includes(c.card_kind)&&['literature_mechanism','research_analysis','primary_mechanism','author_result'].includes(c.claim_kind)&&c.title_zh&&c.title_en&&c.body_zh&&c.body_en&&Number.isSafeInteger(c.position),'invalid research card');
  for(const ref of refs)check(byId.has(ref.card_id)&&ref.source_id&&ref.locator_zh&&ref.locator_en&&['abstract_review','section_review'].includes(ref.review_depth),'unresolved citation');
  for(const c of cards)check(refs.some(ref=>ref.card_id===c.card_id),'uncited research card');
  check(steps.length===0||steps.length===4,'incomplete mechanism diagram');check(!steps.length||(new Set(steps.map(s=>s.position)).size===4&&steps.every(s=>Number.isInteger(s.position)&&s.position>=0&&s.position<4)),'invalid diagram order');for(const step of steps)check(byId.has(step.supporting_card_id)&&step.label_zh&&step.label_en&&step.body_zh&&step.body_en&&['mechanism_schematic','research_question'].includes(step.claim_status),'unbound diagram operation');
  check(frames.length<=1&&(!steps.length||(frames.length===1&&routes.length>0)),'incomplete research framing');
  for(const f of frames)check(byId.has(f.supporting_card_id)&&['mechanism_based_analysis','research_question'].includes(f.claim_status)&&['why','value','challenge'].every(k=>f[k+'_zh']&&f[k+'_en']),'unbound research framing');
  for(const r of routes)check(Number.isSafeInteger(r.position)&&byId.has(r.supporting_card_id)&&refs.some(ref=>ref.card_id===r.supporting_card_id&&ref.source_id===r.source_id)&&['literature_mechanism','research_question'].includes(r.claim_status)&&['title','problem','principle','step_1','step_2','step_3','tradeoff'].every(k=>r[k+'_zh']&&r[k+'_en']),'unbound research route');
  const ids=[...new Set(refs.map(row=>row.source_id))];check(ids.length<=100,'source join too large');
  const result=await api.loadRowsByKeys('cloud_core_sources',ids,revision,['source_id','business_id','title','canonical_url']);
  check(result.revision===revision&&result.records.length===ids.length&&new Set(result.records.map(r=>r.source_id)).size===ids.length,'source revision/identity mismatch');
  for(const source of result.records){check(ids.includes(source.source_id)&&source.business_id==='cloud-core'&&source.title,'foreign canonical source');const url=new URL(source.canonical_url);check(url.protocol==='https:'&&!url.username&&!url.password&&!['localhost','127.0.0.1'].includes(url.hostname),'unsafe source');for(const k of url.searchParams.keys())check(!/token|password|secret|credential|api.?key|signature|bearer/i.test(k),'source contains credential parameter');}
  return {revision,topic:key,steps,frames,routes,cards:cards.sort((a,b)=>a.position-b.position),refs,sources:result.records};
 }
 const cache=new Map(),pending=new Map();
 function get(key,revision){return cache.get(revision+'__'+key);}
 function ensure(key,revision,api){const id=revision+'__'+key;if(cache.has(id))return Promise.resolve(cache.get(id));if(pending.has(id))return pending.get(id);const promise=load(key,revision,api).then(value=>{cache.set(id,value);return value;}).finally(()=>pending.delete(id));pending.set(id,promise);return promise;}
 globalThis.LRITopicDossier=Object.freeze({get,ensure,load});
})();
