'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const revision='a'.repeat(40),domain={business_id:'cloud-core',topic_id:'cloud_core'};
async function relations(){
 const active=new Map(),requests=[];
 const c={URL,Map,Set,JSON,AbortSignal,setTimeout,location:{href:'https://example.org'},sessionStorage:{length:0},fetch:async(_,o)=>{
  const p=JSON.parse(o.body).params.arguments,respond=x=>({ok:true,status:200,json:async()=>({result:{structuredContent:x}})});
  if(!p.arguments)return respond({skill:{summary:{skill_id:'table.query',skill_version:'2.3.0'},operations:[{name:'table_query',access_lane:'read'}]}});
  const a=p.arguments;assert.equal(p.operation,'table_relation_query');requests.push(a);
  for(const b of a.bindings){assert(!active.has(b.alias),'Different in-flight reads must not replace each other’s relation');active.set(b.alias,b.path);}
  await new Promise(r=>setImmediate(r));for(const b of a.bindings)active.delete(b.alias);
  const names=[...a.sql.matchAll(/SELECT '([^']+)' AS kind/g)].map(m=>m[1]);
  return respond({outcome:'executed',result:{bindings:a.bindings.map(b=>({...b,include_deleted:false})),columns:['kind','key','row_version','row_json'],output_bytes:100,rows:a.bindings.map((b,i)=>{
   const row={...domain};for(const f of b.source_query.filters)row[f.field]=f.op==='in'?f.value[0]:f.value;
   return [{type:'text',value:names[i]},{type:'text',value:'key'},{type:'integer',value:1},{type:'text',value:JSON.stringify(row)}];
  })}});
 }};vm.createContext(c);vm.runInContext(fs.readFileSync('business_insight/cloud_core/runtime/mcp-table-read.js','utf8'),c);
 await Promise.all([c.LRICloudSemanticRead('current',revision),c.LRICloudSemanticRead('industry',revision),c.LRICloudSemanticRead('topic',revision,{topicId:'parameters-precision'})]);
 assert.equal(requests.length,3);const current=requests.find(x=>x.bindings.some(b=>b.path.endsWith('ic_trend_periods')));
 assert(current.bindings.length<=12,'First-open foundation fits one bounded read');
 assert(!current.bindings.some(b=>/source_scans|lineage|review_notes|channel_checks/.test(b.path)),'Historical/audit records must not delay the current page');
 const before=requests.length;await c.LRICloudSemanticRead('current',revision);assert.equal(requests.length,before,'Validated committed foundation is reused');
}
async function industry(){
 require('../../business_insight/cloud_core/industry-updates.js');
 const both=names=>Object.fromEntries(names.flatMap(n=>[[n+'_zh','示例'],[n+'_en','Example']]));
 const update={...domain,...both(['title','summary','scope','dependencies','boundary']),update_id:'u',family_id:'f',channel_id:'c',source_id:'s',release_kind:'stable',release_date_kind:'release_note_heading',release_date:'2026-10-01',checked_at:'2026-10-07'};
 const change={...domain,...both(['title','fact','conditions']),change_id:'d',update_id:'u',family_id:'f',source_id:'s',position:1};
 const link={...domain,link_id:'l',change_id:'d',update_id:'u',compression_topic_id:'t',relation_kind:'compression_direct'};
 const groups={industry_updates:[update],industry_update_changes:[change],industry_change_topics:[link],compression_topics:[{compression_topic_id:'t'}]};let reads=0;const calls=[];
 globalThis.LRICloudSemanticRead=async(mode,rev)=>{assert.equal(mode,'industry');assert.equal(rev,revision);reads++;return {revision,groups};};
 globalThis.LRITableGit={loadRowsByKeys:async(table,keys,rev)=>{
  calls.push({table,keys});assert.equal(rev,revision);assert.equal(keys.length,1,'Hydrate only referenced identities');
  const rows={cloud_core_sources:[{source_id:'s',canonical_url:'https://example.org/release'}],ic_source_families:[{...domain,family_id:'f'}],ic_channels:[{...domain,channel_id:'c'}],ic_industry_source_scopes:[{...domain,family_id:'f',ecosystem_id:'ascend'}]};return {revision,records:rows[table]};
 },loadRowsByValues:async(table,field,ids,rev)=>{calls.push({table,ids});assert.equal(table,'ic_channel_families');assert.equal(field,'channel_id');assert.equal(rev,revision);return {revision,records:[{...domain,family_id:'f',channel_id:'c'}]};},loadTablePage:async()=>{throw Error('Entire industry catalog must not be read for updates');}};
 const [a,b]=await Promise.all([LRIIndustryUpdates.loadReader(revision),LRIIndustryUpdates.loadReader(revision)]);assert.equal(a,b);assert.equal(reads,1);assert.equal(a.snapshot.updates.length,1);assert.equal(a.directory.channels.length,1);assert.equal(calls.length,5);
}
(async()=>{await relations();await industry();console.log(JSON.stringify({pass:true,checks:['concurrent relation isolation','bounded first-open foundation','immutable cache reuse','minimal industry references','inflight deduplication'],fixture_only:true}));})().catch(e=>{console.error(e);process.exitCode=1;});
