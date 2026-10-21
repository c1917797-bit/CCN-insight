'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('business_insight/cloud_core/current-synthesis.js','utf8');
const turn=()=>new Promise(resolve=>setImmediate(resolve));
const context=view=>({revision:'r1',scope:'scope',period:'2026-10',locale:'zh',view,topics:[{compression_topic_id:'parameters-precision'}],strings:{},loadIndustry:async()=>({snapshot:{links:[],updates:[],assessments:[]},directory:{source_families:[],industry_source_scopes:[]}})});
function fixture(options={}){
 const touched=[],nodes=new Map(),calls=[];
 class Node{
  constructor(id=''){this.id=id;this.children=[];this.dataset={};this.textContent='';}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this.children=children;if(this.id)touched.push(this.id);}
  querySelectorAll(){return [];}
  setAttribute(){} addEventListener(){}
 }
 const source={source_id:'s',business_id:'cloud-core',title:'Fixture paper',canonical_url:'https://example.org/paper/v1'};
 const summary={summary_id:'s__v1',source_id:'s',business_id:'cloud-core',topic_id:'cloud_core',observed_version:'v1',evidence_url:source.canonical_url,review_status:options.reviewStatus||'method_results_checked',evidence_locator:'Table 1',reviewed_at:'2026-10-08',one_sentence_zh:'Reported claim',innovation_zh:'Method',results_zh:'Model and hardware conditions'};
 const groups={monthly_route_insights:[{story_id:'story',business_id:'cloud-core',topic_id:'cloud_core'}],monthly_route_evidence:[{story_id:'story',compression_topic_id:'parameters-precision',scope_id:'scope',period_id:'2026-10',summary_id:'s__v1',source_id:'s',observed_version:options.expectedVersion||'v1',business_id:'cloud-core',topic_id:'cloud_core'}],ascend_route_assessments:[],ascend_validation_probes:[],current_signals:[],signal_topics:[],insight_reports:[],insight_report_papers:[]};
 const sandbox={URL,Map,Set,console,location:{href:'https://example.org/business_insight/cloud_core/index.html'},Event:class{},document:{createElement:()=>new Node(),createTextNode:text=>({textContent:text}),dispatchEvent(){},getElementById:id=>{if(!nodes.has(id))nodes.set(id,new Node(id));return nodes.get(id);}},LRICloudSemanticRead:async(kind,revision)=>{calls.push({kind,revision});return {revision,groups};},LRITableGit:{loadRowsByKeys:async(table,keys,revision,select)=>{calls.push({table,keys:[...keys],revision,select});if(table==='cloud_core_sources'&&options.sourceGate)await options.sourceGate;return {revision:options.wrongRevision?'wrong':revision,records:table==='cloud_core_sources'?[source]:[summary]};}}};
 vm.createContext(sandbox);vm.runInContext(code,sandbox);
 return {api:sandbox.LRICompressionSynthesis,touched,nodes,calls};
}
(async()=>{
 let release;const gate=new Promise(r=>release=r),f=fixture({sourceGate:gate});
 f.api.refresh(context('updates'));await turn();
 assert.deepEqual(f.calls.filter(c=>c.table).map(c=>c.table),['cloud_core_sources','ic_paper_summaries'],'independent exact-key joins start together');
 release();await turn();
 assert(f.touched.includes('current-hotspot-cards')&&f.touched.includes('current-industry-cards'),'current streams render');
 assert(!f.touched.includes('ascend-cards')&&!f.touched.includes('insight-deck-content')&&!f.touched.includes('insight-deck-archive'),'updates never repaint hidden decisions or reports');
 const reads=f.calls.length;f.touched.length=0;f.api.refresh(context('home'));await turn();
 assert.equal(f.calls.length,reads,'switching view reuses the same revision-bound model');
 assert(f.touched.includes('ascend-cards')&&f.touched.includes('insight-deck-content'),'analysis renders decisions and its report');
 assert(!f.touched.includes('current-hotspot-cards')&&!f.touched.includes('insight-deck-archive'),'analysis does not repaint hidden current facts or archive');
 f.touched.length=0;f.api.refresh(context('reports'));await turn();
 assert(f.touched.includes('insight-deck-archive')&&!f.touched.includes('insight-deck-content')&&!f.touched.includes('ascend-cards'),'archive renders only its own report mount');
 f.api.refresh({...context('home'),revision:'r2'});await turn();
 assert.equal(f.calls.length,reads+3,'new revision is independently read');
 assert(f.calls.filter(c=>c.table).every(c=>c.keys.length===1&&c.select.length>0),'joins use exact keys and selected fields');
 for(const options of [{wrongRevision:true},{expectedVersion:'v2'},{reviewStatus:'unverified'}]){
  const bad=fixture(options);bad.api.refresh(context('home'));await turn();
  const errors=bad.nodes.get('ascend-cards').children;
  assert(errors.some(n=>/Incomplete|mismatch/.test(n.textContent)),'invalid revision, version or review provenance fails closed');
 }
 console.log(JSON.stringify({pass:true,tests:12,fixture_only:true}));
})().catch(error=>{console.error(error);process.exitCode=1;});
