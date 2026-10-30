// The acquisition inventory, domain review and maintained map are different sets.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.join(root,'original-reader/site/business_insight/cloud_core/monthly-corpus.js'),'utf8');
class Node{
 constructor(tag='',text=''){this.tagName=tag;this.textContent=text;this.children=[];this.dataset={};this.hidden=false;this.value='';this.listeners={};}
 append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}setAttribute(){}
 addEventListener(event,action){this.listeners[event]=action;}click(){this.listeners.click?.();}focus(){}scrollIntoView(){}
}
const flatten=node=>[node,...node.children.flatMap(flatten)],host=new Node('section'),errors=[];
const sandbox={document:{createElement:tag=>new Node(tag),createTextNode:text=>new Node('',text),getElementById:id=>id==='monthly-paper-matrix'?host:flatten(host).find(n=>n.id===id),dispatchEvent(){},querySelector(){return null;}},location:{hash:'',search:''},Event:class{},console:{error(...args){errors.push(args);}},LRITableGit:{}};
vm.createContext(sandbox);vm.runInContext(source,sandbox);const api=sandbox.LRICompressionMonthlyCorpus;
const snapshot={snapshot_id:'funnel-fixture',business_id:'cloud-core',topic_id:'cloud_core',period_id:'2026-10',window_start:'2026-10-01',cutoff:'2026-10-29',month_basis:'first_publication',diffusion_policy:'excluded',source_family_ids_json:'["registered-arxiv"]',candidate_count:9,query:'saved fixture query',acquired_at:'2026-10-29T08:15:13Z',reviewed_at:'2026-10-30',abstract_snapshot_sha256:'b'.repeat(64),decisions_sha256:'c'.repeat(64),domain_policy:'inference-compression-nondiffusion-v1',acquisition_window_start:'2026-08-01',acquisition_window_end:'2026-10-29',acquired_unique_count:4843,acquired_query_count:4825,acquired_seed_count:18,acquired_outside_period_count:4834,acquisition_verified_pages:26};
const make=(n,topics,status,domain)=>{const id='2610.'+String(n).padStart(5,'0');return {snapshot_id:snapshot.snapshot_id,period_id:snapshot.period_id,business_id:'cloud-core',topic_id:'cloud_core',paper_id:id,canonical_url:'https://arxiv.org/abs/'+id,versioned_id:id+'v1',first_published:'2026-10-10T00:00:00Z',source_family_id:'registered-arxiv',review_basis:'original_abstract',reviewed_at:'2026-10-30',abstract_sha256:'a'.repeat(64),classification_status:status,topic_ids_json:JSON.stringify(topics),basis_zh:'原始摘要中的对象与方法',title:'Paper '+id,reason_code:'',uncertainties_zh:'',domain_status:domain,domain_basis_zh:'摘要明确说明领域贡献',domain_review_basis:'original_abstract',domain_reviewed_at:'2026-10-30',domain_uncertainties_zh:''};};
const records=[
 make(1,['parameters-precision','activations-precision'],'classified','in_scope'),
 make(2,['parameters-precision','parameters-factorization'],'classified','in_scope'),
 make(3,[],'pending','unresolved'),
 make(4,[],'related_unmapped','in_scope'),
 {...make(5,[],'excluded','out_of_scope'),reason_code:'diffusion_out_of_scope'},
 make(6,['activations-merging','kv_cache-kv_eviction'],'classified','in_scope'),
 make(7,['kv_cache-precision','kv_cache-kv_eviction'],'classified','in_scope'),
 make(8,[],'related_unmapped','adjacent'),
 make(9,[],'pending','in_scope')
];
const ids=set=>[...set].sort(),registered=new Set(['registered-arxiv']);
const m=api.aggregate(records,snapshot,registered);
assert.equal(m.domain.confirmed.size,6);assert.equal(m.classifiedUnion.size,4);assert.equal(m.rootUnion.size,3);
assert.deepEqual(ids(m.domain.outsideMap),['2610.00004','2610.00009'],'A confirmed domain paper can remain outside all sixteen maintained topics');
assert.deepEqual(ids(m.domain.routePending),['2610.00009'],'An uncertain route does not imply uncertain domain relevance');
function assertPartition(model){
 const groups=[...model.domain.byStatus.values()],all=groups.flatMap(group=>[...group]);
 assert.equal(all.length,model.papers.size);assert.equal(new Set(all).size,all.length,'Domain review statuses are disjoint');
 assert.deepEqual([...new Set(all)].sort(),ids(model.papers.keys()));
 assert([...model.classifiedUnion].every(id=>model.domain.confirmed.has(id)),'Every map assignment must belong to the confirmed domain');
 assert.equal(model.domain.confirmed.size,model.classifiedUnion.size+model.domain.outsideMap.size);
 assert([...model.rootUnion].every(id=>model.classifiedUnion.has(id)));
}
assertPartition(m);
for(const patch of [{domain_status:''},{domain_status:'inference'},{domain_basis_zh:''},{domain_review_basis:'title_only'},{domain_reviewed_at:''},{domain_status:'adjacent'}]){
 assert.throws(()=>api.aggregate([{...records[0],...patch},...records.slice(1)],snapshot,registered),'Missing domain evidence or a map paper outside the domain must fail');
}
assert.throws(()=>api.aggregate(records.map(r=>r.reason_code==='diffusion_out_of_scope'?{...r,domain_status:'in_scope'}:r),snapshot,registered),/Diffusion/);
assert.throws(()=>api.aggregate(records,{...snapshot,domain_policy:'invented-policy'},registered),/policy/);
for(const patch of [{acquired_unique_count:4842},{acquired_query_count:4824},{acquired_seed_count:19},{acquired_outside_period_count:4833},{acquisition_verified_pages:-1},{acquisition_verified_pages:1.5},{acquired_query_count:undefined}]){
 assert.throws(()=>api.aggregate(records,{...snapshot,...patch},registered),/acquisition|Acquisition/,'Broken acquisition arithmetic must not produce a smaller-looking funnel');
}
for(const patch of [{domain_status:'adjacent'},{domain_basis_zh:'different rationale'},{domain_review_basis:'derived_from_map_review'},{domain_reviewed_at:'2026-10-29'},{domain_uncertainties_zh:'new uncertainty'}]){
 assert.throws(()=>api.aggregate([...records,{...records[0],...patch}],snapshot,registered),/Conflicting/,'Duplicate identities with conflicting domain decisions must not silently keep the first row');
}
function install(s,rows){
 sandbox.LRITableGit.loadTablePage=async(table,args)=>{const result=table==='ic_monthly_corpus_snapshots'?[s]:rows;return {revision:args.expectedRevision,records:result,page:{offset:0,total:result.length,truncated:false}};};
 sandbox.LRITableGit.loadRowsByKeys=async(_table,families,revision)=>({revision,records:families.map(family_id=>({family_id,business_id:'cloud-core',topic_id:'cloud_core',ui_group:'academic'}))});
}
function renderedPaperIds(){
 const list=sandbox.document.getElementById('monthly-corpus-papers'),found=[];
 assert(list&&!list.hidden,'A funnel click must open its paper list');
 for(let page=0;page<1000;page++){
  const nodes=flatten(list);for(const n of nodes){const match=n.href?.match(/^https:\/\/arxiv\.org\/abs\/(\d{4}\.\d{4,5})v\d+$/);if(match)found.push(match[1]);}
  const next=nodes.find(n=>n.tagName==='button'&&n.textContent==='下一页');
  if(!next||next.disabled)break;next.click();assert(page<999,'Paper-list pagination must terminate');
 }
 assert.equal(new Set(found).size,found.length,'List pagination must not repeat papers');return found.sort();
}
function assertStageSets(model){
 const stages=flatten(host).filter(n=>n.dataset.funnelStage),expected={candidates:new Set(model.papers.keys()),domain:model.domain.confirmed,map:model.classifiedUnion,root:model.rootUnion};
 assert.deepEqual(stages.map(n=>n.dataset.funnelStage),Object.keys(expected));
 for(const b of stages){const wanted=expected[b.dataset.funnelStage];assert(flatten(b).some(n=>n.tagName==='strong'&&n.textContent===wanted.size.toLocaleString('en-US')));b.click();assert.deepEqual(renderedPaperIds(),ids(wanted),b.dataset.funnelStage+' must open exactly its independently derived identity set');}
}
(async()=>{
 install(snapshot,records);await api.refresh({period:'2026-10',revision:'complete-fixture',locale:'zh'});assertStageSets(m);
 let nodes=flatten(host),acquisition=nodes.find(n=>n.dataset.acquisitionCount==='4843');
 assert(acquisition);assert(flatten(acquisition).some(n=>n.textContent.includes('4,825 篇；另有 18 篇显式经典种子')));
 assert(flatten(acquisition).some(n=>n.textContent.includes('9 篇在 2026-10 首发，4,834 篇属于其他首发月份')));
 assert(nodes.some(n=>n.textContent.includes('本月候选 9 = 推理压缩 6 + 相邻研究 1 + 领域待核 1 + 本轮范围外 1')));
 assert(nodes.some(n=>n.textContent.includes('推理压缩 6 = 地图已归类 4 + 尚未归入现有地图 2')));
 assert(nodes.some(n=>n.textContent.includes('不能把下面既有研读集合当作从本轮候选中优选出的最终名单')),'The earlier editorial collection must not be fabricated as the last funnel stage');
 const unknown={...snapshot};delete unknown.domain_policy;
 assert.equal(api.aggregate(records,unknown,registered).domain,null);
 install(unknown,records);await api.refresh({period:'2026-10',revision:'unknown-domain',locale:'zh'});nodes=flatten(host);
 assert(!nodes.some(n=>n.dataset.funnelStage),'A legacy snapshot cannot imply that the unreviewed domain has zero papers');
 assert(nodes.some(n=>n.textContent.includes('尚未单独核对推理压缩领域归属')));
 const invalid={...snapshot,acquired_outside_period_count:1};install(invalid,records);await api.refresh({period:'2026-10',revision:'invalid-funnel',locale:'zh'});nodes=flatten(host);
 assert(nodes.some(n=>n.textContent==='本月论文统计暂不可用'));assert(nodes.some(n=>n.textContent.includes('没有把读取失败显示为零篇')));assert(!nodes.some(n=>n.dataset.funnelStage||n.dataset.acquisitionCount),'Invalid inventory must not leak partial counts');assert.equal(errors.length,1);
 api.reset();
 const folder=path.join(root,'data/compression/tables'),snapshotPath=path.join(folder,'ic_monthly_corpus_snapshots/rows.jsonl');
 if(fs.existsSync(snapshotPath)){
  const read=name=>fs.readFileSync(path.join(folder,name,'rows.jsonl'),'utf8').trim().split('\n').filter(Boolean).map(JSON.parse).filter(r=>!r.deleted).map(r=>r.row);
  const registry=new Set(read('ic_source_families').map(r=>r.family_id)),canonical=read('ic_monthly_paper_corpus');
  for(const s of read('ic_monthly_corpus_snapshots')){
   if(!s.domain_policy){console.log('SKIP canonical domain funnel: '+s.snapshot_id+' has no separately reviewed domain layer yet');continue;}
   const rows=canonical.filter(r=>r.snapshot_id===s.snapshot_id),model=api.aggregate(rows,s,registry);assertPartition(model);
   const oracle=new Set(rows.filter(r=>r.domain_status==='in_scope').map(r=>r.paper_id));assert.deepEqual(ids(model.domain.confirmed),ids(oracle));
   assert.equal(s.acquired_unique_count,s.acquired_query_count+s.acquired_seed_count);assert.equal(s.acquired_unique_count,rows.length+s.acquired_outside_period_count);
   const hashFields=JSON.parse(s.decision_hash_fields_json);for(const key of ['domain_status','domain_basis_zh','domain_review_basis','domain_reviewed_at','domain_uncertainties_zh'])assert(hashFields.includes(key),'The decision hash must bind '+key);
   install(s,rows);await api.refresh({period:s.period_id,revision:'canonical-funnel:'+s.snapshot_id,locale:'zh'});assertStageSets(model);
   const live=flatten(host),details=live.find(n=>n.dataset.acquisitionCount===String(s.acquired_unique_count));assert(details);
   if(s.snapshot_id==='corpus-2026-10-arxiv-20261029-abstract-v1'){
    assert.equal(s.acquired_unique_count,4843);assert.equal(s.acquired_query_count,4825);assert.equal(s.acquired_seed_count,18);assert.equal(s.acquired_outside_period_count,3115);assert.equal(s.acquisition_verified_pages,26);assert.equal(model.papers.size,1728);
    assert(flatten(details).some(n=>n.textContent.includes('1,728 篇在 2026-10 首发，3,115 篇属于其他首发月份')));
   }
   console.log(JSON.stringify({snapshot:s.snapshot_id,acquired:s.acquired_unique_count,candidates:model.papers.size,domain:model.domain.confirmed.size,map:model.classifiedUnion.size,root:model.rootUnion.size,domain_outside_map:model.domain.outsideMap.size}));api.reset();
  }
 }
 console.log('PASS: acquisition arithmetic, separate domain and map sets, unknown-domain fallback, disjoint domain decisions, exact clickable funnel subsets and failure-not-zero');
})().catch(error=>{console.error(error);process.exitCode=1;});
