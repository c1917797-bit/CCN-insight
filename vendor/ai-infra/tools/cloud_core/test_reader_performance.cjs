'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('business_insight/cloud_core/runtime/mcp-table-read.js','utf8');
const storage=new Map();
const sessionStorage={get length(){return storage.size},key:i=>[...storage.keys()][i],getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)};
let revision='r1',reads=0,contracts=0,wrong=false,fail=false,gate=null;
function context(store=sessionStorage){
 const sandbox={URL,Map,Set,JSON,AbortSignal,setTimeout,location:{href:'https://example.org/business_insight/cloud_core/topic.html',origin:'https://example.org'},sessionStorage:store,fetch:async(url,options)=>{
  const args=JSON.parse(options.body).params.arguments;
  if(args.skill_id==='table.query'&&!args.arguments){contracts++;return {ok:true,json:async()=>({result:{structuredContent:{skill:{summary:{skill_id:'table.query',skill_version:'2.3.0'},operations:[{name:'table_query',access_lane:'read'}]}}}})}}
  reads++;if(fail)throw new Error('fixture offline');if(gate)await gate.promise;
  const a=args.arguments,rev=a.view?.revision||revision;
  return {ok:true,json:async()=>({result:{structuredContent:{outcome:'executed',result:{revision:wrong?'wrong':rev,definition:{fields:{topic_id:{}}},row_count:1,deleted_count:0,matched_count:1,truncated:false,returned_count:1,rows:a.limit===0?[]:[{key:'s1',row:{topic_id:'cloud_core',source_id:'s1',title:'fixture',canonical_url:'https://example.org/paper'},deleted:false}]}}}})};
 }};
 vm.createContext(sandbox);vm.runInContext(code,sandbox);return sandbox;
}
const meta='/__mcpgit/tables/cloud_core_sources';
const page=rev=>meta+'/rows?offset=0&limit=100&filter_field=topic_id&filter_value=cloud_core&expected_revision='+rev;
(async()=>{
 let c=context();await c.LRICloudTableRead(meta);const base=reads;
 await Promise.all([c.LRICloudTableRead(page('r1')),c.LRICloudTableRead(page('r1'))]);assert.equal(reads,base+1,'deduplicate identical inflight reads');
 c=context();await c.LRICloudTableRead(meta);let before=reads;await c.LRICloudTableRead(page('r1'));assert.equal(reads,before,'same-session reload reuses committed read');
 revision='r2';await c.LRICloudTableRead(meta);assert(![...storage.keys()].some(k=>k.includes('r1')), 'fresh revision retires incompatible stored reads');before=reads;await c.LRICloudTableRead(page('r2'));assert.equal(reads,before+1,'new revision never consumes old rows');
 const old=await c.LRICloudTableRead(page('r1'));assert.equal(old.revision,'r1','explicit page revision survives metadata races');
 const exact=await c.LRICloudTableRead(meta+'/rows/get',{body:JSON.stringify({keys:['s1'],expected_revision:'r1',select:['source_id']})});assert.equal(exact.revision,'r1','exact-key joins stay pinned');
 wrong=true;await assert.rejects(c.LRICloudTableRead(page('r3')),/revision mismatch/);wrong=false;before=reads;await c.LRICloudTableRead(page('r3'));assert.equal(reads,before+1,'failed results cannot poison cache');
 let release;gate={promise:new Promise(r=>release=r)};const delayed=c.LRICloudTableRead(page('r4'));await new Promise(r=>setTimeout(r,0));c.LRICloudTableReadInvalidate();gate=null;release();await delayed;
 before=reads;await c.LRICloudTableRead(page('r4'));assert.equal(reads,before+1,'refresh fences late cache writers');
 const denied={get length(){throw new Error('disabled')}};c=context(denied);await c.LRICloudTableRead(meta);await c.LRICloudTableRead(page('r1'));
 c=context();
 for(let i=0;i<140;i++)await c.LRICloudTableRead(page('bounded-'+i));
 assert(storage.size<=128&&[...storage.values()].reduce((n,s)=>n+s.length*2,0)<=4*1024*1024,'bounded persisted rows');
 c=context();const metadataReads=reads;const combined=await c.LRICloudTableReadPage('cloud_core_sources',{offset:0,limit:100,expectedRevision:'combined',filterField:'topic_id',filterValue:'cloud_core'});assert.equal(reads,metadataReads+1,'definition and rows require one request');assert.equal(combined.metadata.status.revision,combined.page.revision);
 await assert.rejects(c.LRICloudTableReadPage('cloud_core_sources',{offset:0,limit:100,expectedRevision:'combined',filterField:'foreign',filterValue:'cloud_core'}),/filter unavailable/);
 const initialReads=reads;revision='fresh1';const initial=await c.LRICloudTableReadPage('ic_channels',{filterField:'topic_id',filterValue:'cloud_core',offset:0,limit:100});assert.equal(reads,initialReads+1,'fresh anchor includes its scoped first page');assert.equal(initial.page.revision,'fresh1');
 revision='fresh2';const fresh=await c.LRICloudTableReadPage('ic_channels',{filterField:'topic_id',filterValue:'cloud_core',offset:0,limit:100});assert.equal(fresh.page.revision,'fresh2','latest anchor is never served from immutable storage');
 c.LRICloudTableReadInvalidate();fail=true;await assert.rejects(c.LRICloudTableRead(meta),/offline/);fail=false;
 console.log(JSON.stringify({pass:true,tests:15,fixture_only:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
