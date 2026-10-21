const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('business_insight/cloud_core/foundation-scenes.js','utf8').replace(/^export /gm,'');
const context={};vm.createContext(context);vm.runInContext(source+';globalThis.testAPI={lessonArithmetic,renderLessonSVG};',context);
const {lessonArithmetic,renderLessonSVG}=context.testAPI;
const row=(role,value,position=0,row_index=-1,column_index=-1,bit_pattern='')=>({role,numeric_value:value,position,row_index,column_index,bit_pattern,label_en:'C'+(position+1),label_zh:'类'+(position+1)});
const values={
 quantization:[row('original',-1,0,0,0,'1011110000000000'),row('original',.5,1,0,1,'0011100000000000'),...Object.entries({scale:.5,zero_point:2,input_bits:16,output_bits:2,scale_bits:16,zero_point_bits:8,clip_probe:.875}).map(([r,v])=>row(r,v))],
 pruning_sparsity:[row('original',2,0,0,0),row('original',.1,1,0,1),row('original',.2,2,1,0),row('original',3,3,1,1),row('mask',1,0,0,0),row('mask',0,1,0,1),row('mask',0,2,1,0),row('mask',1,3,1,1),row('input',1,0),row('input',2,1),row('threshold',.5)],
 low_rank:[row('original',2,0,0,0),row('original',4,1,0,1),row('original',3,2,1,0),row('original',6,3,1,1),row('factor_a',2,0,0,0),row('factor_a',3,1,1,0),row('factor_b',1,0,0,0),row('factor_b',2,1,0,1),row('input',1,0),row('input',2,1),row('perturbation',7,0,1,1)],
 distillation:[row('teacher',.6,0),row('teacher',.3,1),row('teacher',.1,2),row('student_logits',0,0),row('student_logits',0,1),row('student_logits',0,2),row('temperature',1),row('learning_rate',1)]
};
const plain=x=>JSON.parse(JSON.stringify(x)),q=lessonArithmetic('quantization',values.quantization);
assert.deepEqual(plain(q.encoded.map(r=>[r.q,r.code,r.reconstructed])),[[0,'00',-1],[3,'11',.5]]);
assert.equal(q.probeCode,3);assert.equal(q.probeReconstructed-q.probe,-.375);assert.equal(q.encodedPayload,4);
const invalid=plain(values.quantization);invalid[0].bit_pattern='0011100000000000';assert.throws(()=>lessonArithmetic('quantization',invalid),/does not encode/);
const prune=lessonArithmetic('pruning_sparsity',values.pruning_sparsity);assert.deepEqual(plain(prune.prunedOutput),[2,6]);assert.deepEqual(plain(prune.originalOutput),[2.2,6.2]);
const rank=lessonArithmetic('low_rank',values.low_rank);assert.deepEqual(plain(rank.factorOutput),[10,15]);assert.deepEqual(plain(rank.changedOutput),[10,17]);
const changed=plain(values.low_rank);changed.find(r=>r.role==='factor_a').numeric_value=1;const different=lessonArithmetic('low_rank',changed);assert.notDeepEqual(plain(different.factorOutput),plain(different.output),'AB output must be computed independently from W');
const distill=lessonArithmetic('distillation',values.distillation);assert(Math.abs(distill.final[0]-.4260125149)<1e-8);assert(Math.abs(distill.finalLoss-.9932866)<1e-6);assert(distill.finalLoss<distill.initialLoss);
const sceneMethods={quantization:['quant-original','quant-parameters','quant-encode','quant-pack','quant-reconstruct','quant-error'],pruning_sparsity:['prune-original','prune-mask','prune-storage','prune-execution'],low_rank:['rank-original','rank-factors','rank-compute','rank-error'],distillation:['distill-teacher','distill-target','distill-training','distill-student']};
let rendered=0;
for(const locale of ['zh','en']){
 const ui=JSON.parse(fs.readFileSync('business_insight/cloud_core/data/foundations-ui.'+locale+'.json')).strings;
 for(const [method,kinds]of Object.entries(sceneMethods))for(const kind of kinds)for(const narrow of [false,true]){
  const step={scene_kind:kind,title_zh:'测试 <script>',title_en:'Fixture <script>',narration_zh:'测试',narration_en:'Fixture',duration_ms:8500};
  const svg=renderLessonSVG({method,step,values:values[method],locale,ui,narrow});
  assert(svg.startsWith('<svg')&&svg.includes('id="'+kind+'"'));assert(!svg.includes('<script>'));assert(!/NaN|undefined|Infinity/.test(svg));rendered++;
  if(kind==='quant-error')assert(svg.includes('0.875')&&svg.includes('-0.375')&&svg.includes('clipBack'));
  if(kind==='quant-pack')assert(svg.includes('@keyframes pack0')&&svg.includes('82%,100%')&&svg.includes('opacity:0'));
  if(kind==='prune-mask')assert(svg.includes('W′')&&svg.includes('>M</text>'));
  if(kind==='rank-compute')assert(svg.includes('@keyframes intermediate'));
  if(kind==='distill-target')assert(svg.includes('@keyframes loss0'));
  if(kind==='distill-student')assert(svg.includes('@keyframes student0'));
 }
}
const loaderCode=fs.readFileSync('business_insight/cloud_core/foundations.js','utf8'),loaderContext={URL};vm.createContext(loaderContext);vm.runInContext(loaderCode,loaderContext);assert.equal(typeof loaderContext.LRICompressionFoundations.validateLessons,'function');
const player=fs.readFileSync('business_insight/cloud_core/foundation-player.js','utf8');assert(player.includes('selected>1×'));assert(player.includes("if(!this.#visible)this.pause('offscreen')"));assert(player.includes("on(window,'hashchange',()=>this.pause('chapter'))"));
console.log(JSON.stringify({pass:true,rendered_frames:rendered,mechanisms:4,canonical_fields_only:true,binary16_verified:true,independent_factor_compute:true}));

if(process.argv[2]){
 const fixture=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),revision='b'.repeat(40);
 const envelope=records=>({revision,records:plain(records),page:{total:records.length,truncated:false}});
 const foundations=[...new Set(fixture.steps.map(r=>r.foundation_id))].map(foundation_id=>({foundation_id}));
 const api=loaderContext.LRICompressionFoundations;
 assert.equal(api.validateLessons(envelope(fixture.steps),envelope(fixture.values),revision,foundations).steps.length,18);
 for(const mutate of [
  (a,b)=>a.revision='a'.repeat(40),
  (a,b)=>b.page.truncated=true,
  (a,b)=>a.records[0].narration_en='',
  (a,b)=>a.records[0].scene_kind='unrelated',
  (a,b)=>a.records[0].source_url='https://example.org?token=private',
  (a,b)=>b.records[0].example_id='foreign',
  (a,b)=>b.records[0].numeric_value=NaN,
  (a,b)=>a.records[0].foundation_id='missing'
 ]){const a=envelope(fixture.steps),b=envelope(fixture.values);mutate(a,b);assert.throws(()=>api.validateLessons(a,b,revision,foundations));}
 const facts={};for(const method of Object.keys(sceneMethods))facts[method]=lessonArithmetic(method,fixture.values.filter(r=>r.method_id===method));
 assert.deepEqual(plain(facts.quantization.encoded.map(r=>r.code)),['00','01','10','11']);
 assert.deepEqual(plain(facts.low_rank.factorOutput),[4,8,12,16]);
 assert.deepEqual(plain(facts.low_rank.changedOutput),[4,8,12,17]);
 const calls=[];api.loadLessons({async loadTablePage(table,options){calls.push({table,options});return envelope(table.endsWith('_steps')?fixture.steps:fixture.values);}},revision,foundations).then(()=>{
  assert.equal(calls.length,2);assert(calls.every(c=>c.options.expectedRevision===revision&&c.options.filterField==='topic_id'&&c.options.filterValue==='cloud_core'));
  console.log(JSON.stringify({canonical_fixture:true,steps:fixture.steps.length,values:fixture.values.length,invalid_contract_cases:8,one_revision:true}));
 }).catch(e=>{console.error(e);process.exitCode=1;});
}
