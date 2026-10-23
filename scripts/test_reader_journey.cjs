/* Regress the actual navigation bugs observed in the public reader journey. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),base=path.join(root,'original-reader/site');
const shell=fs.readFileSync(path.join(base,'assets/lri-shell.js'),'utf8');
const source=fs.readFileSync(path.join(base,'business_insight/cloud_core/compression.js'),'utf8');
const extract=(s,a,b)=>{const from=s.indexOf(a),to=s.indexOf(b,from);assert(from>=0&&to>from);return s.slice(from,to);};
const sandbox={URL,document:{location:{href:'https://example.test/business_insight/cloud_core/topic?topic=parameters-precision&month=2026-10&scope=review&route=old'}}};
vm.createContext(sandbox);
vm.runInContext(extract(shell,'function cloudViewHref(','function collectPageSections('),sandbox);
for(const filename of ['topic','topic.html','monthly','monthly.html','foundations','foundations.html']){
 const href='https://example.test/business_insight/cloud_core/'+filename+'?topic=parameters-precision&month=2026-10&scope=review&route=old';
 assert(sandbox.isCloudDetailPage(new URL(href).pathname));
 for(const view of ['sources','topics','updates','home','reports']){
  const next=new URL(sandbox.cloudViewHref(view,href));
  assert.equal(next.pathname,'/business_insight/cloud_core/index.html');
  assert.equal(next.hash,'#view-'+view);
  assert.equal(next.search,'?month=2026-10&scope=review','Do not leak topic or research-mode parameters into the main reader');
 }
}
assert(!sandbox.isCloudDetailPage('/business_insight/cloud_core/index.html'));
const peers=[{id:'map',top:-500,bottom:3000},{id:'precision',top:100,bottom:1200},{id:'selection',top:100,bottom:1200}];
assert.equal(sandbox.chooseCurrentSection(peers,'precision'),'precision','Right-hand peer must not steal a quantization deep link');
assert.equal(sandbox.chooseCurrentSection(peers,'selection'),'selection');
assert.equal(sandbox.chooseCurrentSection(peers,''),'precision','Stable DOM order breaks equal-height ties');
assert.equal(sandbox.chooseCurrentSection([{id:'precision',top:-1000,bottom:-20},{id:'distillation',top:90,bottom:900}],'precision'),'distillation','A stale hash must not lock the outline after leaving a section');
assert.equal(sandbox.chooseCurrentSection([],''),'');

const rows=name=>fs.readFileSync(path.join(root,'data/compression/tables',name,'rows.jsonl'),'utf8').trim().split('\n').map(JSON.parse).filter(x=>!x.deleted).map(x=>x.row);
const dossier={routes:rows('ic_compression_research_routes').filter(x=>x.compression_topic_id==='parameters-precision'),cards:rows('ic_compression_topic_cards').filter(x=>x.compression_topic_id==='parameters-precision')};
const element=(tag,text='',cls='')=>({tagName:tag.toUpperCase(),textContent:text,className:cls,id:'',dataset:{},children:[],append(...nodes){this.children.push(...nodes);},setAttribute(){}});
Object.assign(sandbox,{element,researchDossier:()=>dossier,URLSearchParams,location:{search:''},mapText:zh=>zh,title:row=>row.title_zh||row.name_zh,textOf:(row,key)=>row[key+'_zh']||'',expertCardTools(){},appendWeightStructuredText(node,text){node.append(element('p',text));},weightTopicCitations(){},researchHref:()=>''});
vm.runInContext(extract(source,'function weightTopicRoutes(','function compressionFoundationHref('),sandbox);
const container=element('div');sandbox.weightTopicRoutes(container);
for(const route of dossier.routes){
 const card=container.children.find(n=>n.id==='research-card-'+route.supporting_card_id);
 assert(card&&card.tagName==='ARTICLE','Evidence navigation must land on the complete method card');
 assert(card.children.some(n=>n.id==='weight-route-'+route.route_id),'Retain old route bookmarks');
 assert(card.children.some(n=>n.tagName==='H4'&&n.textContent===sandbox.title(route)),'Case title must precede the result');
 const box=card.children.find(n=>n.className==='quant-route-result');assert(box&&!box.id,'Do not duplicate the stable evidence anchor inside the result');
}
for(const name of ['index.html','topic.html','monthly.html']){
 const html=fs.readFileSync(path.join(base,'business_insight/cloud_core',name),'utf8');
 const bootstrap=fs.readFileSync(path.join(base,'business_insight/cloud_core/reader-bootstrap.js'),'utf8').trim();
 assert(html.includes(bootstrap),'Inline startup routing must match the maintained source');
 assert(html.includes('dataset.cloudInitialView=view'),'Initial loading must retain the requested view');
}
console.log('PASS: all five view destinations from HTML and clean URLs; query isolation; parallel-section highlighting; complete canonical method anchors; consistent startup routing');
