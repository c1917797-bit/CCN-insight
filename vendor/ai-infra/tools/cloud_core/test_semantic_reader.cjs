'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('business_insight/cloud_core/runtime/mcp-table-read.js','utf8'),revision='a'.repeat(40);
const channel={channel_id:'c',source_id:'s',topic_id:'cloud_core',business_id:'cloud-core',ui_group:'hotspot'};
function fixture(storage=new Map()){
 let fault='',reads=0,contracts=0;
 const sandbox={URL,Map,Set,JSON,AbortSignal,setTimeout,location:{href:'https://example.org/index.html',origin:'https://example.org'},sessionStorage:{get length(){return storage.size},key:i=>[...storage.keys()][i],getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
 fetch:async(url,options)=>{
  const request=JSON.parse(options.body).params.arguments;
  if(!request.arguments){contracts++;return {ok:true,json:async()=>({result:{structuredContent:{skill:{summary:{skill_id:'table.query',skill_version:'2.3.0'},operations:[{name:'table_query',access_lane:'read'}]}}}})}}
  reads++;const a=request.arguments;assert.equal(request.operation,'table_relation_query');assert(a.bindings.length<=16);assert(!a.view);assert(a.bindings.every(b=>b.revision===revision&&b.repo==='works'&&b.source_query.filters.length));assert(a.limits.max_source_rows===1000);
  const names=Array.from(a.sql.matchAll(/SELECT '([^']+)' AS kind/g)).map(m=>m[1]);
  const rows=a.bindings.map((binding,i)=>{
   const record={business_id:'cloud-core',topic_id:'cloud_core',long_text:'x'.repeat(45000)};
   for(const filter of binding.source_query.filters)record[filter.field]=filter.op==='in'?filter.value[0]:filter.value;
   return [{type:'text',value:names[i]},{type:'text',value:'key-'+i},{type:'integer',value:1},{type:'text',value:JSON.stringify(record)}];
  });
  const result={bindings:a.bindings.map(b=>({...b,include_deleted:false})),columns:['kind','key','row_version','row_json'],rows,output_bytes:100,progress_callbacks:0};
  if(fault==='revision')result.bindings[0].revision='b'.repeat(40);
  if(fault==='path')result.bindings[0].path='data/tables/private';
  if(fault==='deleted')result.bindings[0].include_deleted=true;
  if(fault==='binding')result.bindings.push(result.bindings[0]);
  if(fault==='duplicate')result.rows.push(result.rows[0]);
  if(fault==='unknown')result.rows[0][0].value='private';
  if(fault==='owner'||fault==='scope'){const row=JSON.parse(rows[0][3].value);if(fault==='owner')row.business_id='other';else row.ui_group='industry';rows[0][3].value=JSON.stringify(row);}
  if(fault==='array')rows[0][3].value='[]';
  if(fault==='bytes')result.output_bytes=1048577;
  if(fault==='version')rows[0][2].value=0;
  if(fault==='columns')result.columns=['row_json'];
  return {ok:true,json:async()=>({result:{structuredContent:{outcome:'executed',result}}})};
 }};
 vm.createContext(sandbox);vm.runInContext(code,sandbox);
 return {sandbox,storage,get reads(){return reads},set fault(v){fault=v},get contracts(){return contracts}};
}
(async()=>{
 let tests=0;const f=fixture(),read=()=>f.sandbox.LRICloudSemanticRead('sources',revision,{group:'hotspot',channels:[channel]});
 const result=await read();assert.equal(result.revision,revision);assert.equal(result.groups.primarySources.length,1);assert.equal(f.reads,1);tests++;
 await read();assert.equal(f.reads,1,'same-revision native relations are reused');tests++;
 const reload=fixture(f.storage);await reload.sandbox.LRICloudSemanticRead('sources',revision,{group:'hotspot',channels:[channel]});assert.equal(reload.reads,0,'bounded large semantic rows survive same-session reload');assert([...f.storage.values()].reduce((n,s)=>n+s.length*2,0)<=4*1024*1024);tests++;
 for(const fault of ['revision','path','deleted','binding','duplicate','unknown','owner','scope','array','bytes','version','columns']){
  f.sandbox.LRICloudTableReadInvalidate();f.fault=fault;await assert.rejects(read());const before=f.reads;
  f.fault='';await read();assert.equal(f.reads,before+1,'invalid result must not enter cache');tests++;
 }
 const before=f.reads;await f.sandbox.LRICloudSemanticRead('workbench',revision);assert.equal(f.reads,before+2,'workbench respects 16-binding Service budget');tests++;
 await assert.rejects(f.sandbox.LRICloudSemanticRead('private',revision));await assert.rejects(f.sandbox.LRICloudSemanticRead('sources','latest',{group:'hotspot',channels:[channel]}));tests++;
 await assert.rejects(f.sandbox.LRICloudSemanticRead('sources',revision,{group:'private',channels:[channel]}));await assert.rejects(f.sandbox.LRICloudSemanticRead('sources',revision,{group:'hotspot',channels:[channel,channel]}));tests++;
 console.log(JSON.stringify({pass:true,tests,fixture_only:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
