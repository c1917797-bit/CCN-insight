/* Reader contract checks: lazy queue access and complete, proposed experiment plans. */
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(root,'original-reader/site/business_insight/cloud_core/compression.js'),'utf8');
const start=source.indexOf('function refreshImportedPapers(){');
const end=source.indexOf('async function startSourceReader',start);
assert(start>=0&&end>start);
const queue={hidden:false},calls=[];
const context={document:{getElementById:id=>id==='imported-paper-review'?queue:null},location:{hash:'#view-sources',search:'?month=2026-10'},URLSearchParams,Date,state:{revision:'a'.repeat(40),period:'2026-10',locale:'zh',view:'sources',scope:'test',packs:{zh:{strings:{}}}},LRIImportedPaperReview:{update:ctx=>calls.push(ctx)}};
vm.createContext(context);vm.runInContext(source.slice(start,end),context);
context.refreshImportedPapers();assert.equal(queue.hidden,true);assert.equal(calls.at(-1).view,'idle');
context.location.hash='#imported-paper-review';context.refreshImportedPapers();assert.equal(queue.hidden,false);assert.equal(calls.at(-1).view,'sources');
context.state.view='updates';context.location.hash='#view-updates';context.refreshImportedPapers();assert.equal(queue.hidden,true);assert.equal(calls.at(-1).view,'updates');
const rows=fs.readFileSync(path.join(root,'data/compression/tables/ic_compression_topic_cards/rows.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const plans=rows.filter(r=>!r.deleted&&r.row.card_id.endsWith('__dossier_6')&&r.row.section_kind==='watch');
assert.equal(plans.length,16);
for(const {row} of plans){
 assert.equal(row.claim_kind,'research_analysis');
 const parts=row.body_zh.split('\n');
 if(parts[0].startsWith('技术对照1：')){
  assert.equal(parts.length,10,row.card_id);
  for(let group=0;group<2;group++)for(const [i,label]of ['技术对照'+(group+1),'为什么比','对齐条件','观测对象','可证实的成功'].entries())assert(parts[group*5+i].startsWith(label+'：')&&parts[group*5+i].length>label.length+12,row.card_id+' '+label);
  continue;
 }
 assert.equal(parts.length,5,row.card_id);
 for(const [i,label] of ['验证对象','对照方案','测量指标','继续条件','停止条件'].entries())assert(parts[i].startsWith(label+'：')&&parts[i].length>label.length+12,row.card_id+' '+label);
 if(row.compression_topic_id==='parameters-precision'){
  assert(/所选约束/.test(parts[3])&&/知识库/.test(parts[4]),'research-first conditional selection must preserve technical coverage');
 }else assert(/证据|知识|技术|质量|误差|成本|对照|收益/.test(parts[3]),row.card_id+' evidence-led continuation criterion');
}
assert(!/eval\(|innerHTML/.test(source.slice(source.indexOf('function renderValidationPlan('),source.indexOf('function appendResearchText('))));
console.log('PASS: directory queue isolation; all 16 proposed protocols contain explicit alternatives, controls and decision criteria');
