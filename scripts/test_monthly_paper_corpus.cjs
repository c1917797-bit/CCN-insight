// Regress the meaning of a monthly paper count, independent of editorial scopes.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),base=path.join(root,'original-reader/site/business_insight/cloud_core');
const source=fs.readFileSync(path.join(base,'monthly-corpus.js'),'utf8');
class Node{constructor(tag='',text=''){this.tagName=tag;this.textContent=text;this.children=[];this.dataset={};this.hidden=false;}append(...n){this.children.push(...n);}replaceChildren(...n){this.children=n;}setAttribute(){}addEventListener(){}focus(){}scrollIntoView(){}}
const host=new Node('section'),sandbox={document:{createElement:tag=>new Node(tag),createTextNode:t=>new Node('',t),getElementById:id=>id==='monthly-paper-matrix'?host:null,dispatchEvent(){},querySelector(){return null;}},Event:class{},console:{error(){}},LRITableGit:{}};
vm.createContext(sandbox);vm.runInContext(source,sandbox);const api=sandbox.LRICompressionMonthlyCorpus;
const snapshot={snapshot_id:'s',business_id:'cloud-core',topic_id:'cloud_core',period_id:'2026-10',window_start:'2026-10-01',cutoff:'2026-10-29',month_basis:'first_publication',diffusion_policy:'excluded',source_family_ids_json:'["registered-arxiv"]',candidate_count:5,query:'saved query',acquired_at:'2026-10-29T08:15:13Z',reviewed_at:'2026-10-29',abstract_snapshot_sha256:'b'.repeat(64),decisions_sha256:'c'.repeat(64)};
const make=(id,topics=[],status=topics.length?'classified':'pending')=>({snapshot_id:'s',period_id:'2026-10',business_id:'cloud-core',topic_id:'cloud_core',paper_id:id,canonical_url:'https://arxiv.org/abs/'+id,versioned_id:id+'v1',first_published:'2026-10-10T00:00:00Z',source_family_id:'registered-arxiv',review_basis:'original_abstract',abstract_sha256:'a'.repeat(64),classification_status:status,topic_ids_json:JSON.stringify(topics),basis_zh:'摘要明确的实际贡献',title:'Paper '+id,reason_code:'',uncertainties_zh:''});
const records=[make('2610.00001',['parameters-precision','activations-precision']),make('2610.00002',['parameters-precision','parameters-factorization']),make('2610.00003'),make('2610.00004',[],'related_unmapped'),{...make('2610.00005',[],'excluded'),reason_code:'diffusion_out_of_scope'}];
const model=api.aggregate(records,snapshot,new Set(['registered-arxiv']));
assert.equal(model.byTopic.get('parameters-precision').size,2);
assert.equal(model.objectTotals.get('parameters').size,2,'Multi-method paper is counted once in its object total');
assert.equal(model.rootUnion.size,2,'Multi-object and multi-method papers do not inflate the grand total');
assert.equal(model.byStatus.get('pending').size,1);assert.equal(model.byStatus.get('related_unmapped').size,1);
assert.equal(model.byTopic.get('kv_cache-precision').size,0,'A confirmed empty cell stays distinct from unresolved records');
assert.equal(api.aggregate([...records,{...records[0],versioned_id:'2610.00001v2'}],snapshot,new Set(['registered-arxiv'])).rootUnion.size,2,'Versions with identical abstract decisions deduplicate by paper identity');
assert.throws(()=>api.aggregate([...records,{...records[0],topic_ids_json:'["kv_cache-precision"]'}],snapshot,new Set(['registered-arxiv'])),/Conflicting versions/);
for(const patch of [{first_published:'2026-09-02T00:00:00Z'},{first_published:'2026-11-02T00:00:00Z'},{source_family_id:'new-unregistered-source'},{review_basis:'title_only'},{abstract_sha256:''},{reason_code:'diffusion_out_of_scope'},{classification_status:'pending'},{paper_id:'not-a-paper'}]){
 assert.throws(()=>api.aggregate([{...records[0],...patch},...records.slice(1)],snapshot,new Set(['registered-arxiv'])),'Invalid dates, source, title-only classification or unresolved status must fail instead of changing counts');
}
assert.throws(()=>api.aggregate(records.slice(1),snapshot,new Set(['registered-arxiv'])),/incomplete/,'A missing page must not become a lower monthly total');
assert.throws(()=>api.aggregate(records,snapshot,new Set()),/Unregistered/);
// A slow previous month must not overwrite the newly selected month.
const waits=new Map();sandbox.LRITableGit.loadTablePage=(_,args)=>new Promise(resolve=>waits.set(args.filterValue,()=>resolve({revision:args.expectedRevision,records:[],page:{offset:0,total:0,truncated:false}})));
const flatten=n=>[n,...n.children.flatMap(flatten)];
(async()=>{
 const old=api.refresh({period:'2026-09',revision:'r',locale:'zh'}),next=api.refresh({period:'2026-11',revision:'r',locale:'zh'});
 waits.get('2026-11')();await next;waits.get('2026-09')();await old;
 assert(flatten(host).some(n=>n.textContent==='2026-11 · 论文数量矩阵'));assert(!flatten(host).some(n=>n.textContent==='2026-09 · 论文数量矩阵'));
 api.reset();assert(host.hidden&&host.children.length===0,'Reader reset removes stale corpus results');
 const folder=path.join(root,'data/compression/tables');
 if(fs.existsSync(path.join(folder,'ic_monthly_paper_corpus/rows.jsonl'))){
  const read=name=>fs.readFileSync(path.join(folder,name,'rows.jsonl'),'utf8').trim().split('\n').map(JSON.parse).filter(r=>!r.deleted).map(r=>r.row);
  const registry=new Set(read('ic_source_families').map(r=>r.family_id)),topicIds=new Set(read('ic_compression_topics').map(r=>r.compression_topic_id));
  for(const s of read('ic_monthly_corpus_snapshots')){
   const rows=read('ic_monthly_paper_corpus').filter(r=>r.snapshot_id===s.snapshot_id),m=api.aggregate(rows,s,registry),allIds=new Set(rows.map(r=>r.paper_id));
   assert.equal(allIds.size,s.candidate_count);assert.equal(rows.length,allIds.size);
   assert(rows.every(r=>JSON.parse(r.topic_ids_json).every(id=>topicIds.has(id))),'Every assignment must resolve to a maintained topic');
   const fields=['paper_id','abstract_sha256','classification_status','topic_ids_json','basis_zh','uncertainties_zh','reason_code'].sort(),payload=[...rows].sort((a,b)=>a.paper_id.localeCompare(b.paper_id)).map(r=>Object.fromEntries(fields.map(k=>[k,r[k]])));
   assert.equal(crypto.createHash('sha256').update(JSON.stringify(payload)).digest('hex'),s.decisions_sha256,'Snapshot hash must identify the actual canonical classification decisions');
   assert.equal([...m.byStatus.values()].reduce((a,v)=>a+v.size,0),allIds.size,'All corpus decisions partition the candidate set');
   const oracle=new Set(rows.filter(r=>r.classification_status==='classified'&&JSON.parse(r.topic_ids_json).some(id=>/^\w+-(precision|selection|distillation|factorization)$/.test(id))).map(r=>r.paper_id));
   assert.equal(m.rootUnion.size,oracle.size,'Published aggregate must match independently derived canonical identity union');
   console.log(JSON.stringify({snapshot:s.snapshot_id,candidates:allIds.size,assigned:m.byStatus.get('classified').size,matrix_unique:m.rootUnion.size,unmapped:m.byStatus.get('related_unmapped').size,pending:m.byStatus.get('pending').size,excluded:m.byStatus.get('excluded').size}));
  }
 }
 const html=fs.readFileSync(path.join(base,'index.html'),'utf8');assert(html.indexOf('id="monthly-paper-matrix"')<html.indexOf('id="current-streams"'),'The monthly matrix leads the selected updates');
 assert(!source.includes('LRICloudSemanticRead')&&!source.includes('context.scope'),'Monthly counts cannot depend on the 16-paper editorial scope');
 console.log('PASS: first-publication dates, abstract/source provenance, version dedup, multi-cell totals, exclusions, incomplete reads and stale-month race');
})().catch(e=>{console.error(e);process.exitCode=1;});
