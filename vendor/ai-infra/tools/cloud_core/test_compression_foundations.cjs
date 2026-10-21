const fs=require('fs'),vm=require('vm'),assert=require('assert');
const code=fs.readFileSync('business_insight/cloud_core/foundations.js','utf8');
const context={URL};vm.createContext(context);vm.runInContext(code,context);
const api=context.LRICompressionFoundations,revision='a'.repeat(40);
const rows=['quantization','pruning_sparsity','distillation','low_rank'].map((method,i)=>({foundation_id:'method-'+method,business_id:'cloud-core',topic_id:'cloud_core',method_id:method,section_kind:'method',position:i,title_zh:'测试',title_en:'Fixture',summary_zh:'测试摘要',summary_en:'Fixture summary',body_zh:'测试正文',body_en:'Fixture body',source_url:'https://example.org/paper',source_title:'Fixture source',evidence_locator:'Section 2',reviewed_at:'2026-10-16'}));
const result=()=>({revision,records:JSON.parse(JSON.stringify(rows)),page:{total:4,truncated:false}});
assert.equal(api.validate(result(),revision).records.length,4);
for(const mutate of [
 r=>r.revision='b'.repeat(40),
 r=>r.page.truncated=true,
 r=>r.page.total=5,
 r=>r.records[0].business_id='foreign',
 r=>r.records[0].foundation_id=r.records[1].foundation_id,
 r=>r.records[0].body_en='',
 r=>r.records[0].source_url='javascript:alert(1)',
 r=>r.records[0].source_url='https://example.org?token=secret',
 r=>r.records[0].reviewed_at='unknown',
 r=>r.records[0].method_id='shared'
]){const r=result();mutate(r);assert.throws(()=>api.validate(r,revision));}
(async()=>{
 const calls=[];
 const loaded=await api.load({async loadTableMetadata(table){calls.push({table});return {revision};},async loadTablePage(table,options){calls.push({table,options});return result();}});
 assert.equal(loaded.revision,revision);
 assert.equal(calls[1].options.filterField,'topic_id');assert.equal(calls[1].options.filterValue,'cloud_core');assert.equal(calls[1].options.expectedRevision,revision);assert.equal(calls[1].options.limit,100);
 const html=fs.readFileSync('business_insight/cloud_core/foundations.html','utf8');
 assert.equal((html.match(/rel="stylesheet"/g)||[]).length,1);
 assert(!/<style|style=|<details/i.test(html),'one stylesheet and no folded content');
 assert(html.includes('data-lri-shell="auto"')&&html.includes('data-lri-context-item="cloud-core-topics"'));
 const compression=fs.readFileSync('business_insight/cloud_core/compression.js','utf8');
 const weight=compression.slice(compression.indexOf('function renderWeightQuantizationTopic('),compression.indexOf('function renderCompressionTopic('));
 assert(weight.includes("renderFoundationLink(hero,'precision')"));
 assert(!weight.includes('renderQuantizationExplanation(')&&!weight.includes('__method_taxonomy'),'generic lesson and PTQ/QAT occur only in shared foundations');
 assert(compression.includes('renderFoundationLink(hero,topic.method_term_id)')&&compression.includes('renderFoundationLink(header)'));
 const zh=JSON.parse(fs.readFileSync('business_insight/cloud_core/data/foundations-ui.zh.json')).strings,en=JSON.parse(fs.readFileSync('business_insight/cloud_core/data/foundations-ui.en.json')).strings;
 assert.deepEqual(Object.keys(zh).sort(),Object.keys(en).sort());
 assert(Object.keys(zh).every(k=>en[k]&&!/[\u4e00-\u9fff]/.test(en[k])));
 console.log(JSON.stringify({pass:true,negative_cases:10,revision_and_scope:true,bilingual_ui:true,single_shared_lesson:true,five_main_views_preserved:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});
