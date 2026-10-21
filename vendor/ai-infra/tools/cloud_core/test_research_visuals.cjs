/* Geometry-independent SVG safety and semantic preservation gate. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Element{constructor(tag){this.tag=tag;this.attrs={};this.children=[];this.textContent='';}setAttribute(k,v){this.attrs[k]=v;}append(...v){this.children.push(...v);}}
const box={document:{createElementNS:(_,tag)=>new Element(tag),createElement:tag=>new Element(tag)}};
box.globalThis=box;vm.runInNewContext(fs.readFileSync('business_insight/cloud_core/research-visuals.js','utf8'),box);
const api=box.LRICompressionVisuals;
for(const locale of ['zh','en']){
 const labels=locale==='zh'?['权重校准与异常值分离','按分组编码量化数值并保存尺度','低比特表示进入真实矩阵执行','同时测量任务质量、总字节和端到端代价']:['Calibrate weights and separate outliers','Encode grouped values and retain metadata','Execute using the compressed representation','Compare task quality, total bytes and execution cost'];
 const host=api.flow(labels,{locale,title:'Research mechanism',description:'Illustrative, not measured'});
 assert.equal(host.children.length,2);
 for(const svg of host.children){
  assert.equal(svg.attrs.role,'img');assert(svg.children.some(x=>x.tag==='desc'));
  const stages=svg.children.filter(x=>x.tag==='g');assert.equal(stages.length,labels.length);
  stages.forEach((g,i)=>{const text=g.children.find(x=>x.tag==='text'&&x.children.length);const joined=text.children.map(x=>x.textContent).join(locale==='zh'?'':' ');assert.equal(joined.replace(/\s+/g,''),labels[i].replace(/\s+/g,''));});
 }
}
const malicious=api.flow(['<script>alert(1)</script>']);assert.equal(malicious.children[0].children.filter(x=>x.tag==='script').length,0);
for(const kind of ['precision','selection','distillation','factorization'])assert.equal(api.icon(kind).attrs['aria-hidden'],'true');
assert.throws(()=>api.flow([]));
console.log(JSON.stringify({pass:true,layouts:2,locales:2,semanticStagesPreserved:true,noActiveSvg:true}));
