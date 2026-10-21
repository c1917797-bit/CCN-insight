'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Node{
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.attrs={};this.textContent='';}
 append(...children){this.children.push(...children);}replaceChildren(...children){this.children=children;}
 querySelectorAll(){return [];}setAttribute(k,v){this.attrs[k]=v;}addEventListener(){}
}
const roots=new Map(['current-hotspot-cards','current-hotspot-count','current-industry-cards','current-industry-count'].map(id=>[id,new Node('div')]));
const document={createElement:tag=>new Node(tag),createTextNode:text=>({textContent:text}),getElementById:id=>roots.get(id),dispatchEvent(){}};
const code=fs.readFileSync('business_insight/cloud_core/current-synthesis.js','utf8').replace('globalThis.LRICompressionSynthesis=Object.freeze({refresh});','globalThis.testUpdates={renderSignals,renderIndustry,setContext:v=>current=v};');
const box={document,URL,Map,Set,location:{href:'https://example.org/business_insight/cloud_core/index.html'},Event:class{}};
vm.createContext(box);vm.runInContext(code,box);
const walk=n=>[n,...(n.children||[]).flatMap(walk)],text=n=>walk(n).map(x=>x.textContent).join('|');
const context=(locale,topicId='')=>({locale,topicId,scope:'scope',period:'2026-10',topics:[{compression_topic_id:'weight',title_zh:'权重 × 量化',title_en:'Weight × Quantization'},{compression_topic_id:'kv',title_zh:'KV Cache × 量化',title_en:'KV Cache × Quantization'}],strings:JSON.parse(fs.readFileSync('business_insight/cloud_core/data/focus-ui.'+locale+'.json','utf8')).strings});
const source={source_id:'s',title:'Primary release',canonical_url:'https://example.org/release'};
const signal={signal_id:'signal',title_zh:'A challenge and a mechanism',title_en:'An English mechanism',fact_zh:'Reviewed event',fact_en:'English event',relevance_zh:'Concrete choice and cost',relevance_en:'English conditional choice',boundary_zh:'Source scope',boundary_en:'English boundary',source_id:'s',discovery_source_id:'s',locator:'Primary passage',publication_date:'2026-10-01',reviewed_at:'2026-10-09',date_kind:'official_publication'};
const signals={current_signals:[signal],signal_topics:[{signal_id:'signal',compression_topic_id:'weight',relation_kind:'research_context'}],sources:new Map([['s',source]])};
box.testUpdates.setContext(context('zh'));box.testUpdates.renderSignals(signals);
const hotspot=roots.get('current-hotspot-cards');
assert(text(hotspot).includes('A challenge and a mechanism')&&text(hotspot).includes('（权重 × 量化）'),'Title includes exact canonical map name');
assert(text(hotspot).includes('研究背景')&&text(hotspot).includes('Concrete choice and cost'),'Background remains explicit, substantive implication visible');
assert.equal(walk(hotspot).filter(n=>n.tag==='a'&&n.href===source.canonical_url).length,1);
const updates=['u','excluded','pending'].map(id=>({update_id:id,family_id:'f',title_zh:'Release '+id,title_en:'English release '+id,release_date:'2026-10-01',checked_at:'2026-10-09',summary_zh:'Original scope',summary_en:'English scope',dependencies_zh:'Runtime',boundary_zh:'Release boundary',version_label:'v1'}));
const links=[{link_id:'lw',update_id:'u',change_id:'c',compression_topic_id:'weight'},{link_id:'lk',update_id:'u',change_id:'c',compression_topic_id:'kv'},{link_id:'le',update_id:'excluded',change_id:'ce',compression_topic_id:'weight'},{link_id:'lp',update_id:'pending',change_id:'cp',compression_topic_id:'weight'}];
const assessments=links.map((l,i)=>({...l,review_status:i===2?'excluded':i===3?'pending':'verified',title_zh:'Specific mechanism '+l.link_id,title_en:'English mechanism '+l.link_id,relevance_zh:'Relation '+l.link_id,relevance_en:'English relation '+l.link_id,impact_zh:'Conditional impact '+l.link_id,impact_en:'English impact '+l.link_id,check_zh:'Action '+l.link_id,boundary_zh:'No measured gain',source_locator:'Exact reviewed passage',reviewed_at:'2026-10-09'}));
const changes=[{change_id:'c',update_id:'u',title_zh:'Primary change',title_en:'English change',fact_zh:'Single factual statement',fact_en:'English fact',conditions_zh:'Supported conditions',source_id:'s',position:1}];
const reader={snapshot:{updates,links,assessments,changes,sources:[source]},directory:{source_families:[{family_id:'f',title_zh:'Project',title_en:'Project'}],industry_source_scopes:[{family_id:'f',ecosystem_id:'ascend'}]}};
box.testUpdates.renderIndustry(reader);const industry=roots.get('current-industry-cards');
assert(!text(industry).includes('Release excluded')&&!text(industry).includes('Release pending'),'Unsupported and pending links do not enter monthly topic progress');
assert(text(industry).includes('Conditional impact lw')&&text(industry).includes('Conditional impact lk'),'Each verified topic retains its own implications');
assert.equal(walk(industry).filter(n=>n.textContent==='Single factual statement').length,1,'A multi-topic change displays its source fact once');
assert(walk(industry).filter(n=>n.dataset?.industryAssessment).every(n=>n.dataset.readingLayer==='analysis'));
box.testUpdates.setContext(context('zh','weight'));box.testUpdates.renderIndustry(reader);
assert(text(industry).includes('Conditional impact lw')&&!text(industry).includes('Conditional impact lk'),'Topic filtering cannot leak another topic assessment');
assert(!text(industry).includes('KV Cache × 量化'),'Filtered release title contains only supported selected topic');
box.testUpdates.setContext(context('en','weight'));box.testUpdates.renderIndustry(reader);box.testUpdates.renderSignals(signals);
assert(text(industry).includes('English impact lw')&&text(industry).includes('Weight × Quantization'));
assert(text(hotspot).includes('An English mechanism')&&text(hotspot).includes('Research context'));
box.testUpdates.setContext(context('zh','kv'));box.testUpdates.renderSignals(signals);
assert(!text(hotspot).includes('Concrete choice and cost'),'Unrelated hotspot is not injected into another topic');
box.testUpdates.setContext({...context('zh'),topics:[]});assert.throws(()=>box.testUpdates.renderIndustry(reader),/Unresolved map topic/);
console.log(JSON.stringify({pass:true,canonicalTitleTopics:true,backgroundNotImplementation:true,reviewedIndustryOnly:true,conditionalImplications:true,multiTopicFactDeduplicated:true,filteredImplications:true,locales:2}));
