'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('business_insight/cloud_core/runtime/mcp-table-read.js','utf8');
const part=code.slice(code.indexOf('  const pipelineTables='),code.indexOf('  globalThis.LRICloudTableRead ='));
const revision='a'.repeat(40);let mode='',lastRelation;
const source={source_id:'s',business_id:'cloud-core',source_kind:'paper',title:'Quantization paper',canonical_url:'https://arxiv.org/abs/2601.07878',external_id:'2601.07878',verification_status:'not_checked'};
const state={source_id:'s',business_id:'cloud-core',topic_id:'cloud_core',stage:'candidate_direct',priority:10,reason_zh:'candidate only'};
const sandbox={URL,console,eq:(field,value)=>({field,op:'eq',value}),within:(field,value)=>({field,op:'in',value}),immutableRead:async(k,a,fn)=>fn(),readContract:async()=>'2.3.0',call:async(name,a)=>{
 if(name==='skill_get')return {skill:{summary:{skill_id:'table.query',skill_version:'2.3.0'},operations:[{name:a.operation,access_lane:'read'}]}};
 const arg=a.arguments;
 if(a.operation==='table_status')return {outcome:'executed',result:{repo:arg.path.endsWith('cloud_core_sources')?'works':'tablegit',path:arg.path,revision:arg.view.revision,definition:{key_field:'source_id'}}};
 if(a.operation==='table_query')return {outcome:'executed',result:{repo:'works',path:arg.path,revision,rows:[{key:'s',row_version:1,row:source}],matched_count:1,truncated:false}};
 if(a.operation==='table_relation_query'){
  lastRelation=arg;const cells=[{type:'text',value:'s'},{type:'text',value:JSON.stringify(state)},{type:'text',value:JSON.stringify(source)},{type:'integer',value:1}];
  if(mode==='count')cells[3].value=0;
  const bindings=arg.bindings.map(b=>({alias:b.alias,repo:b.repo,path:b.path,revision:mode==='revision'?'b'.repeat(40):b.revision,include_deleted:false}));
  return {outcome:'executed',result:{columns:['item_key','pipeline_json','source_json','total'],bindings,rows:mode==='empty'?[[{type:'null'},{type:'null'},{type:'null'},{type:'integer',value:0}]]:[cells]}};
 }
 throw Error('Unexpected operation');
}};vm.createContext(sandbox);vm.runInContext(part,sandbox);
(async()=>{
 let p=await sandbox.LRICloudPipelineRead({revision,term:"x' OR 1=1 --"});assert.equal(p.rows.length,1);assert.equal(p.total,1);
 assert(!lastRelation.sql.includes("x'"));assert.equal(lastRelation.bindings[1].source_query.text_search.query,"x' OR 1=1 --");assert.equal(lastRelation.bindings[0].repo,'tablegit');assert.equal(lastRelation.bindings[1].repo,'works');assert.equal(lastRelation.parameters[0].value,10);
 for(mode of ['count','revision'])await assert.rejects(sandbox.LRICloudPipelineRead({revision}));
 mode='empty';p=await sandbox.LRICloudPipelineRead({revision});assert.equal(p.total,0);assert.equal(p.rows.length,0);
 mode='';await assert.rejects(sandbox.LRICloudPipelineRead({revision,queue:'arbitrary_sql'}));await assert.rejects(sandbox.LRICloudPipelineRead({revision,offset:1}));await assert.rejects(sandbox.LRICloudPipelineRead({revision:'main'}));
 await sandbox.LRICloudPipelineRead({revision,queue:'pending'});const allowed=lastRelation.bindings[0].source_query.filters[2].value;assert(!allowed.includes('reconciliation_needed'));assert(!allowed.includes('reviewed_visible'));assert(allowed.includes('blocked_invalid'));
 const raw=await sandbox.LRICloudPaperQueueRead({revision});assert.equal(raw.rows[0].source_id,'s');
 console.log(JSON.stringify({pass:true,bounded_page:10,parameterized_search:true,actual_table_authority:true,conflicting_reviews_not_raw_pending:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
