/* Regressions from the expert content audit, using canonical rows and the real dossier loader. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),base=path.join(root,'original-reader/site/business_insight/cloud_core');
const rows=name=>fs.readFileSync(path.join(root,'data/compression/tables',name,'rows.jsonl'),'utf8').trim().split('\n').map(JSON.parse).filter(x=>!x.deleted).map(x=>x.row);
const tables=Object.fromEntries(['ic_compression_topics','ic_compression_topic_cards','ic_compression_topic_card_refs','ic_compression_research_routes','ic_compression_mechanism_steps','ic_compression_research_frames','cloud_core_sources'].map(t=>[t,rows(t)]));
const context={URL,globalThis:null};context.globalThis=context;vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(base,'topic-dossier.js'),'utf8'),context);
const api={
  async loadTablePage(name,o){const all=tables[name].filter(r=>r[o.filterField]===o.filterValue),records=all.slice(o.offset,o.offset+o.limit),next=o.offset+records.length;return {revision:'audit',records,page:{total:all.length,offset:o.offset,truncated:next<all.length,nextOffset:next}};},
  async loadRowsByKeys(name,keys){return {revision:'audit',records:tables[name].filter(r=>keys.includes(r.source_id))};}
};
(async()=>{
  for(const topic of tables.ic_compression_topics){
    const id=topic.compression_topic_id,d=await context.LRITopicDossier.load(id,'audit',api);
    assert(d.routes.length>0,'Topic without a concrete cited technical route: '+id);
    if(id==='parameters-precision')continue;
    const challenge=d.cards.find(c=>c.section_kind==='challenges');
    assert(challenge,'Missing explicit challenge/method/gap map: '+id);
    assert.equal((challenge.body_zh.match(/^挑战\d+：/gm)||[]).length,3,id);
    const verdict=d.cards.find(c=>c.card_id===id+'__dossier_5'),plan=d.cards.find(c=>c.card_id===id+'__dossier_6');
    assert.equal(verdict.claim_kind,'research_analysis');
    assert.equal((verdict.body_zh.match(/^改判条件：/gm)||[]).length,3,id);
    assert.equal((plan.body_zh.match(/^技术对照\d+：/gm)||[]).length,2,id);
    assert(plan.body_zh.includes('对齐条件：')&&plan.body_zh.includes('可证实的成功：'),id);
  }
  for(const c of tables.ic_compression_topic_cards.filter(c=>/__dossier_[56]$/.test(c.card_id))){
    const cited=tables.ic_compression_topic_card_refs.filter(r=>r.card_id===c.card_id);
    assert.equal(new Set(cited.map(r=>r.source_id)).size,cited.length,'Repeated source within one rewritten argument: '+c.card_id);
  }
  const pruneRefs=tables.ic_compression_topic_card_refs.filter(r=>r.card_id==='parameters-selection__dossier_5');
  assert(pruneRefs.every(r=>!tables.cloud_core_sources.find(s=>s.source_id===r.source_id).title.includes('Qwen3.8-27B')),'A rewritten pruning judgment must not inherit unrelated business-example citations');
  const get=id=>tables.ic_compression_topic_cards.find(c=>c.card_id===id);
  assert(get('parameters-selection__dossier_6').body_zh.includes('固定相同mask'),'Compensation attribution requires a controlled mask');
  assert(get('kv_cache-kv_eviction__dossier_5').body_zh.includes('连续缓存可压紧或重分配'),'Do not equate physical reclamation with paged caches only');
  assert(get('activations-selection__dossier_6').body_zh.includes('新增C个token'),'SparseVLM recycling changes the final budget');
  assert(get('parameters-factorization__case_svd_llm').body_zh.includes('v5'),'SVD-LLM recovery must be version-bound');
  const kv=get('kv_cache-precision__case_kvquant'),turbo=get('kv_cache-precision__case_turboquant');
  assert(kv.body_zh.includes('容量估算')&&kv.body_zh.includes('内核微测'),'Do not upgrade KV estimates/kernels to service results');
  assert(turbo.body_zh.includes('数值矛盾')&&turbo.body_zh.includes('未核对正式会议版本'),'Retain primary-source conflicts and version boundary');
  console.log('PASS: all 16 real dossiers load; explicit challenges/judgments/comparisons; controlled attribution, source versions and metric boundaries');
})().catch(e=>{console.error(e);process.exitCode=1;});
