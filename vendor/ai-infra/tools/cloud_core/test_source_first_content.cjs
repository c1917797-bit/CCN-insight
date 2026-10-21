'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const reader=fs.readFileSync('business_insight/cloud_core/compression.js','utf8');
const source=reader.slice(reader.indexOf('async function loadSourcePreview('),reader.indexOf('\nasync function loadDirectory('));
const names=reader.match(/const collectionNames=(\[[^;]+\]);/)[1],directory=reader.match(/const directoryNames=(\[[^;]+\]);/)[1];
const family={business_id:'cloud-core',topic_id:'cloud_core',family_id:'family',title_zh:'测试信源',title_en:'Fixture',summary_zh:'测试用途',summary_en:'Fixture role',ui_group:'hotspot',category_key:'media'};
const channel={business_id:'cloud-core',topic_id:'cloud_core',channel_id:'channel',source_id:'source',ui_group:'hotspot'};
const membership={business_id:'cloud-core',topic_id:'cloud_core',membership_id:'link',family_id:'family',channel_id:'channel',entry_kind:'homepage',position:0};
function fixture(mode=''){
 let renders=0;
 const sandbox={URL,Map,Set,performance:{mark:()=>{}},collectionNames:JSON.parse(names.replace(/'/g,'"')),directoryNames:JSON.parse(directory.replace(/'/g,'"')),state:{epoch:1,domain:'hotspot',data:{sentinel:true}},$:(id)=>({textContent:''}),renderChannels:()=>renders++,mapText:(zh)=>zh,
 must:(ok,message)=>{if(!ok)throw new Error(message)},assertBusiness:rows=>assert(rows.every(r=>r.business_id==='cloud-core')),validateEvidenceRevision:(r,v)=>assert.equal(r.revision,v),safeUrl:u=>{assert.equal(new URL(u).protocol,'https:');return u},
 LRITableGit:{loadTablePage:async(table,o)=>{assert.equal(o.filterField,'ui_group');assert.equal(o.filterValue,'hotspot');assert.equal(o.expectedRevision,'rev');return {revision:'rev',records:[table==='ic_channels'?channel:family],page:{truncated:mode==='truncated'}}},
 loadRowsByValues:async(table,field,keys,revision)=>{assert.equal(table,'ic_channel_families');assert.equal(field,'family_id');assert.equal(keys.join(','),'family');assert.equal(revision,'rev');return {revision:'rev',records:[{...membership,channel_id:mode==='dangling'?'foreign':'channel'}]}},
 loadRowsByKeys:async(table,keys,revision)=>{if(mode==='stale')sandbox.state.epoch++;return {revision:'rev',records:mode==='missing'?[]:[{business_id:'cloud-core',source_id:'source',title:'Fixture',canonical_url:'https://example.org/fixture'}]}}}};
 vm.createContext(sandbox);vm.runInContext(fs.readFileSync('business_insight/cloud_core/source-directory.js','utf8'),sandbox);vm.runInContext(source,sandbox);
 return {sandbox,get renders(){return renders}};
}
(async()=>{
 const f=fixture();await f.sandbox.loadSourcePreview(1,'rev');assert.equal(f.renders,1);assert(f.sandbox.state.directoryPartial);assert.equal(f.sandbox.state.data.primarySources.length,1);
 for(const mode of ['truncated','dangling','missing']){const f=fixture(mode);await assert.rejects(f.sandbox.loadSourcePreview(1,'rev'));assert.equal(f.renders,0,'invalid subset must never be rendered')}
 const stale=fixture('stale');await stale.sandbox.loadSourcePreview(1,'rev');assert.equal(stale.renders,0);assert(stale.sandbox.state.data.sentinel,'late preview must preserve newer view');
 console.log(JSON.stringify({pass:true,tests:5,fixture_only:true}));
})().catch(error=>{console.error(error);process.exitCode=1});
