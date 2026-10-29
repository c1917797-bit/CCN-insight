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
 for(const view of ['sources','topics','library','updates','home','reports']){
  const next=new URL(sandbox.cloudViewHref(view,href));
  assert.equal(next.pathname,'/business_insight/cloud_core/index.html');
  assert.equal(next.hash,'#view-'+view);
  assert.equal(next.search,'?month=2026-10&scope=review','Do not leak topic or research-mode parameters into the main reader');
 }
}
assert(!sandbox.isCloudDetailPage('/business_insight/cloud_core/index.html'));
// A topic directory is a distinct destination; two period views share one
// primary navigation group without changing their existing deep-link URLs.
Object.assign(sandbox,{state:{view:'sources'},topicPage:()=>false,$:()=>null});
vm.runInContext(extract(source,'const viewIds=','function revealHashTarget('),sandbox);
vm.runInContext(extract(source,'function primaryView(','function showView('),sandbox);
for(const view of ['sources','topics','library','updates','home','reports'])assert.equal(sandbox.viewForTarget('view-'+view),view);
assert.equal(sandbox.viewForTarget('expert-library'),'library','Retain the old research-search bookmark');
for(const view of ['updates','home'])assert.equal(sandbox.primaryView(view),'updates');
assert.equal(sandbox.primaryView('reports'),'reports','Archive remains an independent primary entry');
assert.equal(sandbox.primaryView('topics'),'topics');assert.equal(sandbox.primaryView('library'),'library');
sandbox.topicPage=()=>true;assert.equal(sandbox.primaryView('topics'),'library','A topic detail belongs to the topic directory');sandbox.topicPage=()=>false;
for(const filename of ['index.html','topic.html','monthly.html']){
 const html=fs.readFileSync(path.join(base,'business_insight/cloud_core',filename),'utf8');
 const primary=html.match(/<nav class="wb-view-tabs"[\s\S]*?<\/nav>/)[0];
 assert.deepEqual([...primary.matchAll(/data-view="([^"]+)"/g)].map(m=>m[1]),['sources','topics','library','updates','reports']);
 const period=html.match(/<section id="period-navigation"[\s\S]*?<\/section>/)[0];
 assert.deepEqual([...period.matchAll(/data-view="([^"]+)"/g)].map(m=>m[1]),['updates','home']);
 assert(html.includes('id="topic-catalog"'),'The topic directory has a real content destination');
}
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
const additional=sandbox.weightAdditionalCaseIds(dossier);
for(const card of dossier.cards.filter(c=>c.card_kind==='case'&&c.section_kind==='papers')){
 assert(dossier.routes.some(r=>r.supporting_card_id===card.card_id)||additional.includes(card.card_id),'Every indexed paper case must have a rendered destination');
}
assert(!additional.some(id=>dossier.routes.some(r=>r.supporting_card_id===id)),'Additional cases must not duplicate route evidence');
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
// Browsers execute the delivery bundle. Checking only its editable source can
// miss a corrected module that was never included in the actual reader.
for(const bundleName of ['reader-entry.js','topic-entry.js']){
 const bundle=fs.readFileSync(path.join(base,'business_insight/cloud_core',bundleName),'utf8').replace(/\r\n/g,'\n');
 for(const name of ['current-synthesis.js','industry-updates.js','compression.js',...(bundleName==='reader-entry.js'?['paper-review.js','monthly-routes.js']:[])]){
  const module=fs.readFileSync(path.join(base,'business_insight/cloud_core',name),'utf8').replace(/\r\n/g,'\n').trim();
  assert(bundle.includes(module),'Delivery bundle must include current source: '+bundleName+' / '+name);
 }
}
const frames=[],scrolls=[];
Object.assign(sandbox,{state:{view:'home'},location:{hash:'#view-home'},topicPage:()=>false,$:id=>({hidden:false}),window:{scrollTo:options=>scrolls.push(options.top)},requestAnimationFrame:fn=>frames.push(fn)});
vm.runInContext(extract(source,'function scrollViewStart(','function showView('),sandbox);
sandbox.scrollViewStart('home');while(frames.length)frames.shift()();
assert.deepEqual(scrolls,[0],'Main navigation must not inherit an unrelated column scroll');
sandbox.scrollViewStart('home');sandbox.location.hash='#research-card-awq';while(frames.length)frames.shift()();
assert.equal(scrolls.length,1,'A deferred top reset must never override an evidence deep link');
const overviewNodes=new Map(['insight-observation','insight-boundary','insight-freshness','home-judgement','home-period'].map(id=>[id,{dataset:{},textContent:'',replaceChildren(){this.textContent=''},append(){}}]));
const judgement=overviewNodes.get('home-judgement');judgement.textContent='Canonical report conclusion';judgement.dataset.synthesisContext='revision|scope|2026-10|zh';
Object.assign(sandbox,{state:{revision:'revision',scope:'scope',period:'2026-10',locale:'zh',profile:{last_verified:'2026-10-15'},data:{trend_periods:[]}},$:id=>overviewNodes.get(id),currentScope:()=>null,label:key=>key,renderFindings(){}});
vm.runInContext(extract(source,'function renderOverview()','function visibleFindings('),sandbox);
sandbox.renderOverview();assert.equal(judgement.textContent,'Canonical report conclusion','Late evidence render must preserve the same-context report conclusion');
sandbox.state.period='2026-11';sandbox.renderOverview();assert.equal(judgement.textContent,'conclusion_from_checked_facts','A new period must not inherit a stale conclusion');
console.log('PASS: destinations, query isolation, complete method anchors, startup routing, scroll reset, deep links and asynchronous conclusion ownership');
