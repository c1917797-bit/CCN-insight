'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Node{
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.attrs={};this.events={};this.textContent='';}
 append(...children){this.children.push(...children);}replaceChildren(...children){this.children=children;}
 setAttribute(k,v){this.attrs[k]=v;}addEventListener(k,f){this.events[k]=f;}
}
const root=new Node('div'),argument=new Node('details');
const document={createElement:tag=>new Node(tag),createTextNode:text=>({textContent:text}),getElementById:id=>id==='analysis-focus-cards'?root:id==='assessment'?argument:null,dispatchEvent(){}};
const code=fs.readFileSync('business_insight/cloud_core/current-synthesis.js','utf8').replace('globalThis.LRICompressionSynthesis=Object.freeze({refresh});','globalThis.testFocus={renderResearchFocus,setContext:v=>current=v};');
const box={document,URL,Map,Set,location:{href:'https://example.org/business_insight/cloud_core/index.html'},Event:class{}};
vm.createContext(box);vm.runInContext(code,box);
const row={assessment_id:'assessment',story_id:'story',priority_zh:'优先穿刺',position:1,title_zh:'Fixture research priority',title_en:'English priority',rationale_zh:'Reviewed reason',rationale_en:'English reason',recommendation_zh:'Conditional action',recommendation_en:'English action'};
const ref={story_id:'story',compression_topic_id:'parameters-precision',summary_id:'paper__v1',source_id:'paper',observed_version:'v1'};
const model={monthly_route_evidence:[ref,{...ref,compression_topic_id:'activations-precision'}],ascend_validation_probes:[{assessment_id:'assessment',hypothesis_zh:'Proposed question',hypothesis_en:'English question'}],sources:new Map([['paper',{title:'Canonical paper',canonical_url:'https://example.org/abs/latest'}]]),paperSummaries:new Map([['paper__v1',{source_id:'paper',observed_version:'v1',evidence_url:'https://example.org/abs/v1'}]])};
const nodes=n=>[n,...(n.children||[]).flatMap(nodes)],text=n=>nodes(n).map(x=>x.textContent).join('|');
const context=lang=>({locale:lang,scope:'scope',period:'2026-10',topics:['parameters-precision','activations-precision'].map(id=>({compression_topic_id:id,title_zh:id,title_en:id})),strings:JSON.parse(fs.readFileSync('business_insight/cloud_core/data/focus-ui.'+lang+'.json','utf8')).strings});
box.testFocus.setContext(context('zh'));box.testFocus.renderResearchFocus(model,[row,{...row,priority_zh:'条件研究',title_zh:'Excluded conditional'}]);
assert.equal(root.children.length,1,'Only priority rows appear in focus cards');
assert.equal(root.children[0].dataset.claimKind,'analyst_recommendation');
assert(text(root).includes('Fixture research priority'));
assert(!text(root).includes('Reviewed reason')&&!text(root).includes('Proposed question')&&!text(root).includes('Conditional action'),'Research index does not duplicate report reasoning');
assert(!text(root).includes('Excluded conditional'));
const anchors=nodes(root).filter(n=>n.tag==='a');
assert.equal(anchors.filter(n=>n.href.includes('paper=paper__v1')).length,1,'Deduplicate paper versions and preserve reviewed reader identity');
assert(anchors.some(n=>n.href.includes('topic=parameters-precision'))&&anchors.some(n=>n.href.includes('topic=activations-precision')),'Keep exact map associations');
anchors.find(n=>n.href==='#assessment').events.click();assert(argument.open,'Full argument link expands the matching assessment');
box.testFocus.setContext(context('en'));box.testFocus.renderResearchFocus(model,[row]);
assert(text(root).includes('English priority')&&!text(root).includes('English reason'),'English index is concise too');
box.testFocus.renderResearchFocus({...model,ascend_validation_probes:[]},[row]);assert.equal(root.children.length,1,'Compact index does not depend on repeated probe text');
box.testFocus.renderResearchFocus(model,[]);assert(text(root).includes(context('en').strings.analysis_focus_empty));
assert.throws(()=>box.testFocus.renderResearchFocus({...model,paperSummaries:new Map([['paper__v1',{source_id:'paper',observed_version:'v2'}]])},[row]),/Unbound priority paper/);
console.log(JSON.stringify({pass:true,compactResearchIndex:true,exactMapAndVersion:true,deduplication:true,argumentOpening:true,locales:2,emptyAndProbeIndependence:true,versionMismatchRejected:true}));
