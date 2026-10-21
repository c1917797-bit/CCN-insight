'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('business_insight/cloud_core/reader-bootstrap.js','utf8'),revision='a'.repeat(40);
async function run(mode='sources',fault='',elementTiming=false){
 const calls=[],marks=[],mounted=[],loaded=[],timings=[];
 class Element{constructor(tag){this.tag=tag;this.dataset={};this.children=[];}setAttribute(k,v){this[k]=v;}querySelector(s){return this.children.find(n=>n.tag===s);}append(...nodes){this.children.push(...nodes);}remove(){this.removed=true;}}
 const nav={after:n=>mounted.push(n)},placeholder={dataset:{lriReader:'reader-entry.js?v=test'},replaceWith:n=>loaded.push(n)};
 const c={navigator:{},crypto:{randomUUID:()=>'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'},URL,URLSearchParams,Map,Set,JSON,Date,Math,AbortSignal,Promise,setTimeout:()=>{},performance:{mark:(n,o)=>{marks.push(n);timings.push(o)}},requestAnimationFrame:f=>f(),addEventListener:()=>{},MutationObserver:class{observe(){}disconnect(){}},location:{search:'?month=2026-10&scope=s',hash:'#view-'+mode,href:'https://example.org/business_insight/cloud_core/index.html',pathname:'/business_insight/cloud_core/index.html'},document:{documentElement:{lang:'zh-CN'},body:{},createElement:t=>new Element(t),querySelector:s=>s==='script[data-lri-reader]'?placeholder:s==='.wb-view-tabs'?nav:null,querySelectorAll:()=>[]},fetch:async(_,o)=>{
  const p=JSON.parse(o.body).params.arguments;calls.push(p);const respond=v=>({ok:true,json:async()=>({result:{structuredContent:v}})});
  if(!p.arguments)return respond({skill:{summary:{skill_id:'table.query',skill_version:fault==='contract'?'9':'2.3.0'},operations:[{name:'table_query',access_lane:'read'}]}});
  if(fault==='permission')return {ok:false};
  if(p.operation==='table_relation_query'){
   assert.equal(p.arguments.bindings.length,3);assert.equal(p.arguments.limits.max_result_rows,20);assert(p.arguments.sql.includes('GROUP BY f.key'));for(const b of p.arguments.bindings)assert(b.source_query.filters.some(f=>f.field==='business_id'&&f.value==='cloud-core'));
   const record={business_id:fault==='foreign'?'other':'cloud-core',topic_id:'cloud_core',ui_group:'hotspot',family_id:'f',title_zh:'真实信源',summary_zh:'真实登记介绍'};
   const rows=[[{type:'text',value:'f'},{type:'integer',value:1},{type:'text',value:JSON.stringify(record)}]];if(fault==='duplicate')rows.push(rows[0]);
   return respond({skill_id:'table.query',skill_version:fault==='contract'?'9':'2.3.0',operation:'table_relation_query',outcome:'executed',result:{bindings:p.arguments.bindings.map((b,i)=>({...b,path:fault==='path'?'wrong':b.path,revision:fault==='mixed'&&i===1?'b'.repeat(40):revision})),columns:['key','row_version','row_json'],rows,output_bytes:1000,truncated:fault==='truncated'}});
  }
  assert.equal(p.operation,'table_query');assert(p.arguments.limit<=400);assert(p.arguments.filters.some(f=>f.field==='business_id'&&f.value==='cloud-core'));
  const table=p.arguments.path.split('/').at(-1);let row={business_id:'cloud-core',topic_id:'cloud_core'};
  for(const f of p.arguments.filters)row[f.field]=f.op==='in'?f.value[0]:f.value;
  if(table==='ic_source_families')Object.assign(row,{title_zh:'真实信源',summary_zh:'真实登记介绍',family_id:'f'});
  if(table==='ic_channels')Object.assign(row,{channel_id:'c',enabled:true,priority:'P0'});if(table==='ic_channel_families')Object.assign(row,{channel_id:'c',family_id:'f',membership_id:'m',position:1});
  const rows=['ic_source_families','ic_channels','ic_channel_families'].includes(table)?[{key:'r',row,row_version:1,deleted:false}]:[];
  if(fault==='foreign'&&rows.length)rows[0].row.business_id='other';
  if(fault==='duplicate'&&rows.length)rows.push(rows[0]);
  return respond({skill_id:'table.query',skill_version:fault==='contract'?'9':'2.3.0',operation:'table_query',outcome:'executed',result:{repo:'works',path:fault==='path'?'wrong':p.arguments.path,revision:fault==='mixed'&&table==='ic_compression_topic_concepts'?'b'.repeat(40):revision,rows,truncated:fault==='truncated'}});
 }};if(elementTiming)c.PerformanceObserver=class{static supportedEntryTypes=['element'];constructor(callback){this.callback=callback;}observe(){setImmediate(()=>this.callback({getEntries:()=>[{identifier:'cloud-core-native-first',renderTime:1234}]}));}disconnect(){}};vm.createContext(c);vm.runInContext(source,c);
 let error;try{await c.LRICloudFirstRead;}catch(e){error=e;}await new Promise(r=>setImmediate(r));
 assert.equal(loaded.length,1,'Full reader starts even when the optional first-content read fails');
 if(fault){assert(error,'Invalid authority must reject');assert.equal(mounted.length,0,'Invalid facts must never appear');}
 else{assert.equal(mounted.length,1);assert.equal(marks[0],'cloud-core-first-readable-content');assert.equal(mounted[0].dataset.revision,revision);if(elementTiming){assert.equal(marks[1],'cloud-core-first-readable-paint');assert.equal(timings[1].startTime,1234,'Use actual text render timestamp, never callback timing');}assert.equal(mounted[0].children[1].children[0].children[1].elementtiming,'cloud-core-native-first');c.LRICloudFirstRetire();assert(mounted[0].removed);}
 return calls.length;
}
(async()=>{assert.equal(await run(),2,'One authorized bounded source join plus live workbench discovery');await run('sources','',true);for(const fault of ['permission','contract','foreign','duplicate','path','truncated'])await run('sources',fault);await run('topics','mixed');await run('sources','mixed');console.log(JSON.stringify({pass:true,tests:10,fixture_only:true,contract:'live permission, exact business/path/revision, no stale fallback, readable native content'}));})().catch(e=>{console.error(e);process.exitCode=1;});