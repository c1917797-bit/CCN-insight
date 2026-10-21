'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
// Input: a private directory of revision-pinned committed-record exports; never a production fallback.
const dir=process.argv[2],revision=process.argv[3];
const bundles=fs.readdirSync(dir).filter(n=>n.endsWith('.json')).sort().map(n=>JSON.parse(fs.readFileSync(require('node:path').join(dir,n),'utf8')));
assert.equal(bundles.length,12,'expected all twelve matrix dossiers');
const box={URL,Map,Set};vm.createContext(box);
vm.runInContext(fs.readFileSync('business_insight/cloud_core/topic-dossier.js','utf8'),box);
(async()=>{const results=[];
for(const b of bundles){
 assert.equal(b.revision,revision,'export revision must match the pinned reader revision');
 const api={loadTablePage:async(table,opt)=>{assert.equal(opt.filterField,'compression_topic_id');assert.equal(opt.filterValue,b.id);assert.equal(opt.expectedRevision,revision);const rows=b[table];assert(rows);return{revision,records:rows,page:{total:rows.length,truncated:false,offset:0}};},loadRowsByKeys:async(table,keys,rev)=>{assert.equal(table,'cloud_core_sources');assert.equal(rev,revision);const rows=b[table].filter(r=>keys.includes(r.source_id));assert.equal(rows.length,keys.length);return{revision,records:rows};}};
 const d=await box.LRITopicDossier.load(b.id,revision,api);
 assert.equal(d.steps.length,4);assert(d.routes.length>=1);assert(d.cards.some(c=>c.card_kind==='case'));
 for(const c of d.cards)assert(d.refs.some(r=>r.card_id===c.card_id));
 if(['activations-distillation','activations-factorization','kv_cache-distillation'].includes(b.id)){
  assert.equal(d.cards.length,8);assert.equal(d.routes.length,2);assert.equal(d.cards.filter(c=>c.card_kind==='case').length,2);
  assert(d.routes.every(r=>r.claim_status==='literature_mechanism'));
  assert(d.frames.every(r=>r.claim_status==='mechanism_based_analysis'));
  assert(d.steps.every(r=>r.claim_status==='mechanism_schematic'));
  assert(!d.cards.some(c=>/当前缺直接代表作|尚未证明激活压缩|direct representative work is missing/i.test(c.body_zh+' '+c.body_en)));
 }
 results.push({topic:b.id,cards:d.cards.length,routes:d.routes.length,sources:d.sources.length});
}
console.log(JSON.stringify({pass:true,revision,actual_committed_records:true,topics:results}));
})().catch(e=>{console.error(e);process.exitCode=1});
