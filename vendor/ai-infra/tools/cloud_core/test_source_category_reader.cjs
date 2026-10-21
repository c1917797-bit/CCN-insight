'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const reader=fs.readFileSync('business_insight/cloud_core/compression.js','utf8');
const source=reader.slice(reader.indexOf('function emptyReaderData()'),reader.indexOf('async function startSourceReader('));
const names=reader.match(/const collectionNames=(\[[^;]+\]);/)[1],directory=reader.match(/const directoryNames=(\[[^;]+\]);/)[1];
function fixture(mode=''){
 let renders=0;const calls=[],storage=new Map();
 const family={business_id:'cloud-core',topic_id:'cloud_core',family_id:'family',title_zh:'测试信源',title_en:'Fixture',summary_zh:'定位与选择理由',summary_en:'Role',ui_group:'hotspot',category_key:'media'};
 const channels=[0,1].map(i=>({business_id:'cloud-core',topic_id:'cloud_core',channel_id:'channel'+i,source_id:'source'+i,ui_group:'hotspot'}));
 const memberships=channels.map((r,i)=>({business_id:'cloud-core',topic_id:'cloud_core',membership_id:'link'+i,family_id:'family',channel_id:r.channel_id,entry_kind:i?'rss':'homepage',position:i}));
 const state={epoch:1,revision:'rev',domain:'hotspot',readerMode:'sources',sourceGroups:new Map(),sourcePending:new Map(),sourceStatusReady:false,data:{sentinel:true},channelOffset:0,channelTotal:1};
 const sandbox={URL,Map,Set,Promise,performance:{mark:()=>{}},collectionNames:JSON.parse(names.replace(/'/g,'"')),directoryNames:JSON.parse(directory.replace(/'/g,'"')),state,
 $:id=>storage.get(id)||(()=>{const el={textContent:'',disabled:false};storage.set(id,el);return el;})(),label:k=>k,controls:()=>{},renderChannels:()=>renders++,ordered:r=>r,mapText:zh=>zh,
 must:(ok,m)=>{if(!ok)throw new Error(m)},assertBusiness:rows=>assert(rows.every(r=>r.business_id==='cloud-core'&&r.topic_id==='cloud_core')),validateEvidenceRevision:(r,v)=>assert.equal(r.revision,v),safeUrl:u=>assert.equal(new URL(u).protocol,'https:'),
 LRITableGit:{
 loadTablePage:async(table,o)=>{calls.push(table);assert.equal(o.filterField,'ui_group');assert.equal(o.expectedRevision,'rev');
 const isChannel=table==='ic_channels';const rows=isChannel?channels:[family];const paged=mode==='pagination'&&isChannel;
 const records=paged?rows.slice(o.offset,o.offset+1):rows;return {revision:mode==='revision'?'foreign':'rev',records:mode==='foreign'?records.map(r=>({...r,ui_group:'academic'})):records,page:{total:rows.length,truncated:paged&&o.offset===0,nextOffset:mode==='cursor'?0:o.offset+records.length,...(mode==='cursor'?{truncated:true}: {})}}},
 loadRowsByValues:async(table,field,ids,revision)=>{calls.push(table);assert.equal(revision,'rev');return {revision,records:mode==='dangling'?memberships.map(r=>({...r,channel_id:'foreign'})):memberships}},
 loadRowsByKeys:async(table,ids,revision)=>{calls.push(table);if(mode==='stale')state.epoch++;return {revision,records:mode==='missing'?[]:channels.map(r=>({business_id:'cloud-core',source_id:r.source_id,title:'Fixture',canonical_url:mode==='unsafe'?'file:///private':'https://example.org/'+r.source_id}))}}
 }};
 vm.createContext(sandbox);vm.runInContext(fs.readFileSync('business_insight/cloud_core/source-directory.js','utf8'),sandbox);vm.runInContext(source,sandbox);
 return {sandbox,calls,get renders(){return renders}};
}
(async()=>{
 for(const mode of ['', 'pagination']){const f=fixture(mode);await f.sandbox.showSourceGroup('hotspot');assert.equal(f.renders,1);assert.equal(f.sandbox.state.data.channels.length,2);assert(f.sandbox.state.directoryPartial);assert(!f.calls.some(t=>/workbench|technique|collection_runs/.test(t)));const count=f.calls.length;await f.sandbox.showSourceGroup('hotspot');assert.equal(f.calls.length,count,'repeat category uses verified pinned data');}
 for(const mode of ['revision','foreign','cursor','dangling','missing','unsafe']){const f=fixture(mode);await assert.rejects(f.sandbox.showSourceGroup('hotspot'));assert.equal(f.renders,0,'invalid category must not render');}
 const late=fixture('stale');await late.sandbox.showSourceGroup('hotspot');assert.equal(late.renders,0);assert(late.sandbox.state.data.sentinel,'late read cannot overwrite refreshed state');
 const inactive=fixture();inactive.sandbox.state.domain='academic';await inactive.sandbox.showSourceGroup('hotspot');assert.equal(inactive.renders,0);assert(inactive.sandbox.state.sourceGroups.size===1,'inactive verified category may be reused later');
 console.log(JSON.stringify({pass:true,tests:10,fixture_only:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
