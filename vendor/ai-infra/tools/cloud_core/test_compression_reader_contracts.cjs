'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('business_insight/cloud_core/topic-dossier.js','utf8');
const sandbox={URL,Map,Set};vm.createContext(sandbox);vm.runInContext(src,sandbox);
const topic='fixture-topic',rev='fixture-revision';
const card={business_id:'cloud-core',topic_id:'cloud_core',compression_topic_id:topic,card_id:'c1',section_kind:'mechanism',card_kind:'step',claim_kind:'literature_mechanism',position:0,title_zh:'测试',title_en:'test',body_zh:'测试',body_en:'test'};
const ref={business_id:'cloud-core',topic_id:'cloud_core',compression_topic_id:topic,card_id:'c1',reference_id:'r1',source_id:'s1',locator_zh:'摘要',locator_en:'abstract',review_depth:'abstract_review'};
const steps=Array.from({length:4},(_,position)=>({business_id:'cloud-core',topic_id:'cloud_core',compression_topic_id:topic,step_id:'s'+position,position,supporting_card_id:'c1',label_zh:'测试',label_en:'test',body_zh:'测试',body_en:'test',claim_status:'mechanism_schematic'}));
const frame={...card,frame_id:topic,supporting_card_id:'c1',why_zh:'测试',why_en:'test',value_zh:'测试',value_en:'test',challenge_zh:'测试',challenge_en:'test',claim_status:'mechanism_based_analysis'};
const route={...card,route_id:'route',supporting_card_id:'c1',source_id:'s1',claim_status:'literature_mechanism'};
for(const k of ['problem','principle','step_1','step_2','step_3','tradeoff']){route[k+'_zh']='测试';route[k+'_en']='test';}
function api(change={}){
 return {loadTablePage:async(table,options)=>{
  assert.equal(options.filterField,'compression_topic_id');assert.equal(options.filterValue,topic);assert.equal(options.expectedRevision,rev);
  let rows=table.endsWith('_refs')?[ref]:table.endsWith('_steps')?steps:table.endsWith('_frames')?[frame]:table.endsWith('_routes')?[route]:[card];
  if(change[table])rows=change[table](rows.map(r=>({...r})));
  return {revision:change.revision||rev,records:rows,page:{total:rows.length,truncated:false,offset:0}};
 },loadRowsByKeys:async(table,ids,revision)=>{assert.equal(revision,rev);assert.equal(table,'cloud_core_sources');return {revision:rev,records:[{source_id:'s1',business_id:'cloud-core',title:'Fixture only',canonical_url:'https://example.org/paper'}]};}};
}
const monthly=fs.readFileSync('business_insight/cloud_core/monthly-routes.js','utf8');
const diagramSource=monthly.slice(monthly.indexOf('  function renderRouteDiagram('),monthly.indexOf('  function chapter('));
const treeNode=(tag,text='',cls='')=>({tag,text,cls,children:[],append(...items){this.children.push(...items)},setAttribute(){}});
const diagramContext={node:treeNode,current:{locale:'zh'},t:(zh)=>zh,pick:(r,k)=>r[k+'_zh'],Map,citation:(p,s,label)=>{const a=treeNode('a',label);a.href=s.observed_url;p.append(a)}};
vm.createContext(diagramContext);vm.runInContext(diagramSource,diagramContext);
const figureRoot=treeNode('root'),summary={innovation_zh:'Fixture mechanism',results_zh:'Fixture conditions: model X, baseline Y',observed_url:'https://example.org/paper/v2'};
diagramContext.renderRouteDiagram(figureRoot,{question_zh:'Fixture question',boundary_zh:'Fixture boundary'},new Map([['test',{summary_id:'test',source_id:'s1',observed_version:'v2'}]]),{reviewMap:new Map([['test',summary]]),sourceMap:new Map([['s1',{title:'Fixture paper'}]])});
const flatten=n=>[n,...n.children.flatMap(flatten)],nodes=flatten(figureRoot);
assert.equal(figureRoot.children[0].tag,'figure');
assert(nodes.some(n=>n.text==='Fixture mechanism')&&nodes.some(n=>n.text===summary.results_zh),'method and experimental conditions must remain accessible together');
assert(nodes.some(n=>n.href===summary.observed_url)&&nodes.some(n=>n.text==='Fixture boundary'),'route diagram must retain versioned source and explicit evidence boundary');

(async()=>{
 const value=await sandbox.LRITopicDossier.load(topic,rev,api());assert.equal(value.steps.length,4);
 await assert.rejects(sandbox.LRITopicDossier.load(topic,rev,api({revision:'other'})),/revision mismatch/);
 await assert.rejects(sandbox.LRITopicDossier.load(topic,rev,api({ic_compression_mechanism_steps:r=>r.slice(0,3)})),/incomplete mechanism diagram/);
 await assert.rejects(sandbox.LRITopicDossier.load(topic,rev,api({ic_compression_mechanism_steps:r=>r.map(x=>({...x,supporting_card_id:'missing'}))})),/unbound diagram/);
 await assert.rejects(sandbox.LRITopicDossier.load(topic,rev,api({ic_compression_mechanism_steps:r=>r.map(x=>({...x,compression_topic_id:'foreign'}))})),/foreign or duplicate/);
 await assert.rejects(sandbox.LRITopicDossier.load(topic,rev,api({ic_compression_mechanism_steps:r=>r.map(x=>({...x,position:0}))})),/diagram order/);
 await assert.rejects(sandbox.LRITopicDossier.load(topic,rev,api({ic_compression_research_frames:()=>[]})),/incomplete research framing/);
 await assert.rejects(sandbox.LRITopicDossier.load(topic,rev,api({ic_compression_research_routes:r=>r.map(x=>({...x,source_id:'foreign'}))})),/unbound research route/);
 console.log(JSON.stringify({pass:true,tests:9,fixture_only:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
