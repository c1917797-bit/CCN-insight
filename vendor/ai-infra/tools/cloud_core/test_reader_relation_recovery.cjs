'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const code=fs.readFileSync('business_insight/cloud_core/runtime/mcp-table-read.js','utf8'),revision='a'.repeat(40);
function fixture(fault){let relations=0,tables=0,active=0,maximum=0;
 const rowsFor=(filters)=>{let row={business_id:'cloud-core',topic_id:'cloud_core'};for(const f of filters||[])row[f.field]=f.op==='in'?f.value[0]:f.value;return row;};
 const sandbox={URL,Map,Set,JSON,AbortSignal,setTimeout:fn=>{fn();},location:{href:'https://example.org'},sessionStorage:{length:0},fetch:async(_,options)=>{
  const p=JSON.parse(options.body).params.arguments;
  const respond=x=>({ok:true,status:200,json:async()=>x});
  if(!p.arguments)return respond({result:{structuredContent:{skill:{summary:{skill_id:'table.query',skill_version:'2.3.0'},operations:[{name:'table_query',access_lane:'read'}]}}}});
  const a=p.arguments;
  if(p.operation==='table_query'){tables++;assert.equal(a.view.revision,revision);return respond({result:{structuredContent:{outcome:'executed',result:{revision:fault==='drift'?'b'.repeat(40):revision,rows:[{key:'key',row_version:1,row:rowsFor(a.filters)}],truncated:false}}}});}
  relations++;active++;maximum=Math.max(maximum,active);await new Promise(r=>setImmediate(r));active--;
  if(fault==='permission')return respond({error:{message:'permission denied'}});
  if(fault==='race'||fault==='drift'||(fault==='once'&&relations===1))return respond({error:{message:'validation error: SQL relation changed identity while being materialized'}});
  const names=Array.from(a.sql.matchAll(/SELECT '([^']+)' AS kind/g)).map(m=>m[1]);
  return respond({result:{structuredContent:{outcome:'executed',result:{bindings:a.bindings.map(b=>({...b,include_deleted:false})),columns:['kind','key','row_version','row_json'],rows:a.bindings.map((b,i)=>[{type:'text',value:names[i]},{type:'text',value:'key'},{type:'integer',value:1},{type:'text',value:JSON.stringify(rowsFor(b.source_query.filters))}]),output_bytes:100}}}});
 }};
 vm.createContext(sandbox);vm.runInContext(code,sandbox);
 return {read:()=>sandbox.LRICloudSemanticRead('workbench',revision),counts:()=>({relations,tables,maximum})};
}
(async()=>{
 let f=fixture('once');await f.read();assert.deepEqual(f.counts(),{relations:3,tables:0,maximum:1});
 f=fixture('race');let r=await f.read();assert.equal(r.revision,revision);assert.equal(f.counts().relations,6);assert(f.counts().tables>0);const before=f.counts();await f.read();assert.deepEqual(f.counts(),before,'validated exact reads must be reused');
 f=fixture('permission');await assert.rejects(f.read(),/permission denied/);assert.equal(f.counts().relations,1);assert.equal(f.counts().tables,0,'authorization errors must never retry or fall back');
 f=fixture('drift');await assert.rejects(f.read(),/revision mismatch/);
 console.log(JSON.stringify({pass:true,tests:4,fixture_only:true,scope:'Observed race recovery; permission and revision fail closed'}));
})().catch(e=>{console.error(e);process.exitCode=1;});
