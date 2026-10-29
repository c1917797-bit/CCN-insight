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
 assert.deepEqual([...primary.matchAll(/data-view="([^"]+)"/g)].map(m=>m[1]),['sources','topics','updates','library','reports']);
 const period=html.match(/<section id="period-navigation"[\s\S]*?<\/section>/)[0];
 assert.deepEqual([...period.matchAll(/data-view="([^"]+)"/g)].map(m=>m[1]),['updates','home']);
 assert(html.includes('id="topic-catalog"'),'The topic directory has a real content destination');
}
const foundationNavigation=extract(shell,"    if (document.body.dataset.compressionFoundations === 'true'",'    const sourcePanel =');
for(const locale of ['zh','en']){
 const items=vm.runInNewContext('(function(){const cloudViewItems=[];'+foundationNavigation+'return cloudViewItems;}).call({locale:'+JSON.stringify(locale)+'})',{document:{body:{dataset:{compressionFoundations:'true'}}}});
 assert.deepEqual(Array.from(items,item=>item.view),['sources','topics','updates','library','reports']);
 assert.equal(items.find(item=>item.current).view,'library','Foundations remain part of research topics');
}
const peers=[{id:'map',top:-500,bottom:3000},{id:'precision',top:100,bottom:1200},{id:'selection',top:100,bottom:1200}];
assert.equal(sandbox.chooseCurrentSection(peers,'precision'),'precision','Right-hand peer must not steal a quantization deep link');
assert.equal(sandbox.chooseCurrentSection(peers,'selection'),'selection');
assert.equal(sandbox.chooseCurrentSection(peers,''),'precision','Stable DOM order breaks equal-height ties');
assert.equal(sandbox.chooseCurrentSection([{id:'precision',top:-1000,bottom:-20},{id:'distillation',top:90,bottom:900}],'precision'),'distillation','A stale hash must not lock the outline after leaving a section');
assert.equal(sandbox.chooseCurrentSection([],''),'');

const rows=name=>fs.readFileSync(path.join(root,'data/compression/tables',name,'rows.jsonl'),'utf8').trim().split('\n').map(JSON.parse).filter(x=>!x.deleted).map(x=>x.row);
const dossier={routes:rows('ic_compression_research_routes').filter(x=>x.compression_topic_id==='parameters-precision'),cards:rows('ic_compression_topic_cards').filter(x=>x.compression_topic_id==='parameters-precision')};
const element=(tag,text='',cls='')=>{
 const node={tagName:tag.toUpperCase(),ownText:text,className:cls,id:'',dataset:{},children:[],parentElement:null,open:false,events:{},attributes:{},
  get textContent(){return this.ownText+this.children.map(child=>child.textContent).join('');},
  append(...nodes){for(const child of nodes){child.parentElement=this;this.children.push(child);}},
  setAttribute(name,value){this.attributes[name]=String(value);},
  addEventListener(name,callback){this.events[name]=callback;}};
 node.classList={add(...names){node.className=[...new Set([...node.className.split(/\s+/).filter(Boolean),...names])].join(' ');},contains(name){return node.className.split(/\s+/).includes(name);}};
 return node;
};
Object.assign(sandbox.state,{disclosureOpen:new Map()});
Object.assign(sandbox,{element,researchDossier:()=>dossier,URLSearchParams,location:{search:''},mapText:zh=>zh,title:row=>row.title_zh||row.name_zh,textOf:(row,key)=>row[key+'_zh']||'',expertCardTools(){},appendWeightStructuredText(node,text){node.append(element('p',text));},weightTopicCitations(){},renderTopicSourceStrip(){},researchHref:()=>''});
vm.runInContext(extract(source,'function configureWeightCase(','function compressionFoundationHref('),sandbox);
const container=element('div');sandbox.weightTopicRoutes(container);
const additional=sandbox.weightAdditionalCaseIds(dossier);
for(const card of dossier.cards.filter(c=>c.card_kind==='case'&&c.section_kind==='papers')){
 assert(dossier.routes.some(r=>r.supporting_card_id===card.card_id)||additional.includes(card.card_id),'Every indexed paper case must have a rendered destination');
}
assert(!additional.some(id=>dossier.routes.some(r=>r.supporting_card_id===id)),'Additional cases must not duplicate route evidence');
for(const route of dossier.routes){
 const card=container.children.find(n=>n.id==='research-card-'+route.supporting_card_id);
 assert(card&&card.tagName==='DETAILS','Evidence navigation must land on the complete expandable method card');
 assert.equal(card.open,false,'Representative methods must start collapsed');
 assert.equal(card.children[0].tagName,'SUMMARY','The method name must be the native disclosure control');
 assert.equal(card.children[0].children[0].tagName,'H4');
 assert.equal(card.children[0].textContent,sandbox.title(route),'The collapsed row must retain the method title');
 assert(card.children.some(n=>n.id==='weight-route-'+route.route_id),'Retain old route bookmarks');
 const box=card.children.find(n=>n.className==='quant-route-result');assert(box&&!box.id,'Do not duplicate the stable evidence anchor inside the result');
 const evidence=dossier.cards.find(row=>row.card_id===route.supporting_card_id);
 assert(box.textContent.includes(evidence.body_zh),'Collapsed methods must keep their complete evidence mounted');
}
sandbox.weightTopicCards(container,additional);
const disclosures=container.children.filter(node=>node.classList.contains('quant-case-disclosure'));
assert.equal(disclosures.length,dossier.routes.length+additional.length,'Additional paper cases use the same disclosure group');
assert(disclosures.every(node=>node.open===false),'Every representative paper starts collapsed');
assert(disclosures.every(node=>node.attributes.name==='weight-quantization-cases'),'Native disclosure grouping must cover every representative paper');
for(const id of additional){
 const node=disclosures.find(node=>node.dataset.researchCard===id),row=dossier.cards.find(row=>row.card_id===id);
 assert.equal(node.children[0].textContent,sandbox.title(row),'Additional papers retain clickable titles');
 assert(node.textContent.includes(row.body_zh),'Additional paper evidence must remain searchable while collapsed');
}
const first=disclosures[0],second=disclosures[1];
first.open=true;first.events.toggle();
second.open=true;second.events.toggle();
assert.equal(first.open,false,'Opening another method must close its sibling');
assert.equal(second.open,true);
assert.equal(disclosures.filter(node=>node.open).length,1);
const last=disclosures.at(-1);last.open=true;last.events.toggle();
assert.equal(second.open,false,'Opening an additional paper must also close the prior method');
assert.equal(disclosures.filter(node=>node.open).length,1);
last.open=false;last.events.toggle();
assert(disclosures.every(node=>node.open===false),'Readers can close the active case without opening a replacement');
for(const route of dossier.routes){
 sandbox.location.search='?route='+encodeURIComponent(route.route_id);
 const selected=element('div');sandbox.weightTopicRoutes(selected);
 const cases=selected.children.filter(node=>node.classList.contains('quant-case-disclosure'));
 assert.equal(cases.length,1,'A route-specific URL must render only its selected route');
 assert.equal(cases[0].id,'research-card-'+route.supporting_card_id);
 assert.equal(cases[0].open,true,'A route-specific URL must open the complete selected method');
}
sandbox.location.search='';
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
