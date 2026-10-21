'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const sandbox={Map,Set};vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('business_insight/cloud_core/source-directory.js','utf8'),sandbox);
const api=sandbox.LRIGroupedSources;
function fixture(){
 const data={channels:[],source_families:[],channel_families:[],industry_source_scopes:[]};
 for(let i=0;i<12;i++){
  const family_id=i===0?'vllm-ascend':i===1?'vllm':'reference-'+i,channel_id='entry-'+i,source_id='source-'+i;
  data.source_families.push({family_id,business_id:'cloud-core',topic_id:'cloud_core',title_zh:family_id,title_en:family_id,summary_zh:'介绍',summary_en:'Introduction',ui_group:'industry',category_key:'runtimes'});
  data.channels.push({channel_id,source_id,ui_group:'industry',priority:i<11?'P0':'P2'});
  data.channel_families.push({membership_id:'member-'+i,channel_id,family_id,business_id:'cloud-core',topic_id:'cloud_core',entry_kind:'repository',position:i});
  data.industry_source_scopes.push({family_id,source_id,business_id:'cloud-core',topic_id:'cloud_core',ecosystem_id:i===0?'ascend':'general',reason_zh:'项目范围',reason_en:'Project scope',classification_basis:'reviewed_source_subject_scope',reviewed_at:'2026-10-08'});
 }
 return data;
}
const data=fixture(),catalog=api.catalog(data,{domain:'industry',important:true});
const sections=api.industrySections(catalog);
assert.deepEqual(Array.from(sections,p=>p.total),[1,10]);
assert.equal(sections[0].rows[0].family.family_id,'vllm-ascend');
assert.equal(sections[1].rows[0].family.family_id,'vllm');
const next=api.industrySections(catalog,{general:8});
assert.equal(next[0].rows[0].family.family_id,'vllm-ascend');
assert.equal(next[1].rows.length,2);
assert.equal(next[1].hasNext,false);
const reached=[...sections[1].rows,...next[1].rows].map(g=>g.family.family_id);
assert.equal(new Set(reached).size,10);
const search=api.industrySections(api.catalog(data,{domain:'industry',important:true,query:'reference-2'}),{general:8});
assert.deepEqual(Array.from(search,p=>p.total),[0,1]);
assert.equal(search[1].offset,0);
assert.equal(api.industrySections(api.catalog(data,{domain:'industry',important:false}))[1].total,11);
for(const change of [
 d=>{d.industry_source_scopes.pop();},
 d=>{d.industry_source_scopes.push({...d.industry_source_scopes[0]});},
 d=>{d.industry_source_scopes[0].source_id='source-1';},
 d=>{d.industry_source_scopes[0].ecosystem_id='assumed';},
 d=>{delete d.industry_source_scopes;}
]){
 const bad=fixture();change(bad);assert.throws(()=>api.validate(bad),/Source subject integrity/);
}
if(process.argv[2]){
 const actual=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));api.validate(actual);
 const core=api.industrySections(api.catalog(actual,{domain:'industry',important:true}));
 assert.deepEqual(Array.from(core,p=>p.total),[6,32]);
 assert.equal(core[0].rows.some(g=>g.family.family_id==='source-family-msmodelslim'),true);
 const all=api.catalog(actual,{domain:'industry',important:false});
 assert.equal(all.rows.length,233);
 const allParts=api.industrySections(all);
 assert.deepEqual(Array.from(allParts,p=>p.total),[6,227]);
 console.log('Committed source partition: 233 subjects, 6 Ascend / 227 other; core 6 / 32');
}
console.log('Industry ecosystem integrity, filtering, disjointness and independent paging passed');

(async()=>{
 const calls=[],transport={URL,AbortSignal,location:{origin:'https://reader.test',href:'https://reader.test/business_insight/cloud_core/index.html'},fetch:async(url,options)=>{
  const request=JSON.parse(options.body);calls.push(request);
  const result=request.params.name==='skill_get'
   ?{skill:{summary:{skill_id:'table.query',skill_version:'2.3.0'},operations:[{name:'table_query',access_lane:'read'}]}}
   :{outcome:'executed',result:{revision:'fixture-revision',rows:[],row_count:233,deleted_count:0,definition:{fields:{family_id:{},topic_id:{}}}}};
  return {ok:true,status:200,json:async()=>({result:{structuredContent:result}})};
 }};
 vm.createContext(transport);vm.runInContext(fs.readFileSync('business_insight/cloud_core/runtime/mcp-table-read.js','utf8'),transport);
 const result=await transport.LRICloudTableRead('https://reader.test/__mcpgit/tables/ic_industry_source_scopes');
 assert.equal(result.status.row_count,233);
 assert.equal(calls[1].params.arguments.operation,'table_query');
 assert.equal(calls[1].params.arguments.arguments.path,'data/tables/ic_industry_source_scopes');
 assert.equal(calls[1].params.arguments.arguments.limit,0);
 assert.equal(Object.hasOwn(calls[1].params.arguments,'caller_person_id'),false);
 await assert.rejects(()=>transport.LRICloudTableRead('https://elsewhere.test/__mcpgit/tables/ic_industry_source_scopes'),/Unsupported/);
 await assert.rejects(()=>transport.LRICloudTableRead('https://reader.test/__mcpgit/tables/private_secrets'),/Unsupported/);
 console.log('Same-origin official read transport supports ecosystem table without caller impersonation');
})().catch(error=>{console.error(error);process.exitCode=1;});
