'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const reader=fs.readFileSync('business_insight/cloud_core/compression.js','utf8'),body=reader.slice(reader.indexOf('async function loadTopicReferenceSupplement('),reader.indexOf('async function startTopicReader('));
const tables=['techniques','placements','source_refs','lineages','lineage_nodes','lineage_relations','lineage_cells','map_assignments'];
function fixture(mode=''){
 let renders=0,joins=0;const state={epoch:1,revision:'rev',referencePending:true,referenceError:'',data:{sentinel:true,source_refs:[],lineage_nodes:[],lineage_relations:[]}};
 const sandbox={Map,Set,Promise,state,topicPage:()=>true,performance:{mark:()=>{}},renderDirectionDetail:()=>renders++,
 boundedRead:async(names,read,concurrency)=>{assert.equal(concurrency,3);assert.deepEqual(Array.from(names),tables);return Promise.all(names.map(read))},
 small:async(name,revision)=>{assert.equal(revision,'rev');return name==='source_refs'?[{source_id:'s'}]:[]},
 validateEnrichment:d=>assert(d.sentinel),validateScientificTaxonomy:d=>assert(Array.isArray(d.map_assignments)),validateEvidenceRevision:(r,v)=>{if(r.revision!==v)throw new Error('mismatch')},must:(ok,m)=>{if(!ok)throw new Error(m)},safeUrl:u=>{if(!u.startsWith('https://'))throw new Error('unsafe')},
 LRITableGit:{loadRowsByKeys:async(table,ids,revision)=>{joins++;assert.equal(table,'cloud_core_sources');assert.equal(ids.join(','),'s');assert.equal(revision,'rev');if(mode==='stale')state.epoch++;return {revision:mode==='revision'?'other':revision,records:mode==='missing'?[]:[{source_id:'s',business_id:mode==='owner'?'other':'cloud-core',title:'Fixture',canonical_url:mode==='unsafe'?'file:///private':'https://example.org/paper'}]}}}
 };
 vm.createContext(sandbox);vm.runInContext(body,sandbox);return {sandbox,get renders(){return renders},get joins(){return joins}};
}
(async()=>{
 const ok=fixture();await ok.sandbox.loadTopicReferenceSupplement(1,'rev');assert.equal(ok.renders,1);assert.equal(ok.joins,1);assert(!ok.sandbox.state.referencePending);assert.equal(ok.sandbox.state.data.primarySources.length,1);
 for(const mode of ['missing','revision','owner','unsafe']){const f=fixture(mode);await f.sandbox.loadTopicReferenceSupplement(1,'rev');assert(f.sandbox.state.referencePending,'failure cannot masquerade as zero evidence');assert(f.sandbox.state.referenceError);assert(f.sandbox.state.data.sentinel);assert(!f.sandbox.state.data.primarySources,'failed join cannot project new facts');}
 const late=fixture('stale');await late.sandbox.loadTopicReferenceSupplement(1,'rev');assert.equal(late.renders,0);assert(late.sandbox.state.referencePending);assert(!late.sandbox.state.data.primarySources);
 console.log(JSON.stringify({pass:true,tests:6,fixture_only:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
