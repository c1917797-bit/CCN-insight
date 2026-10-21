const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('business_insight/cloud_core/compression.js','utf8');
const fn=source.slice(source.indexOf('function renderWeightQuantizationTopic('),source.indexOf('function renderCompressionTopic('));
class N{constructor(tag,text='',cls=''){this.tagName=tag;this.textContent=String(text);this.className=cls;this.children=[];this.dataset={};this.classList={add(){}};}append(...ns){this.children.push(...ns);}setAttribute(k,v){this[k]=v;}}
function run(view){
 const root=new N('main'),calls=[];
 const ctx={element:(...a)=>new N(...a),mapText:(zh,en)=>zh,title:r=>r.title_zh||'route',textOf:(r,k)=>r[k+'_zh']||'',researchView:()=>view,researchHref:(v,k='')=>'topic.html?view='+v+'#direction-'+k,
 state:{revision:'fixture',period:'2026-10',scope:'fixture',data:{compression_topic_concepts:[]}},location:{search:'',hash:''},URLSearchParams,Event:function(){},
 document:{body:{dataset:{}},dispatchEvent(){}},topicPage:()=>false,compressionTopicId:()=> 'parameters-precision',
 renderFoundationLink(){},renderResearchFraming(){},renderResearchRoutes(){},ensureTopicIndustryResearch(){},topicIndustryReaders:new Map(),
 renderRouteEvidence(){return null;},external(){},renderDossierCards:(host,kind,ids)=>calls.push({kind,ids}),weightTopicCards:(host,ids)=>calls.push({ids}),weightTopicRoutes(){},weightTopicCitations(){},compactResearchCitations(){},dossierErrors:new Map()};
 vm.createContext(ctx);vm.runInContext(fn,ctx);ctx.renderWeightQuantizationTopic(root,{title_zh:'权重 × 量化',reviewed_at:'2026-10-14'},{routes:[],sources:[],cards:[],refs:[],frames:[{challenge_zh:'挑战：示例'}]});
 return {sections:root.children.filter(n=>n.className==='research-overview-section'),calls,root};
}
const full=run('overview');
assert.deepEqual(full.sections.map(s=>s.children[0].textContent),['01 · 研究背景','02 · 关键挑战','03 · 方案解析','04 · 选型判断','05 · 行动建议']);
assert(full.sections.every(s=>!s.hidden));
assert.deepEqual(full.sections.map(s=>s.dataset.readingLayer),['facts','facts','facts','analysis','conclusion']);
for(const [view,count]of [['background',2],['mechanism',1],['industry',1],['literature',1],['comparison',1],['implications',1]])assert.equal(run(view).sections.filter(s=>!s.hidden).length,count);
const explicit=full.calls.flatMap(c=>c.ids||[]);assert.equal(explicit.length,new Set(explicit).size,'each selected semantic card has one location');
assert(source.includes("if(id==='parameters-precision'){renderWeightQuantizationTopic(parent,topic,dossier);return;}"),'other topics keep their renderer');
console.log(JSON.stringify({pass:true,views:7,stages:5,no_duplicate_explicit_cards:true,other_topics_preserved:true}));

const industry=run('industry').sections.find(s=>s.id==='research-overview-solutions');assert(industry.children.find(s=>s.id==='direction-routes').hidden,'industry reader isolates implementation');
const mechanism=run('mechanism').sections.find(s=>s.id==='research-overview-solutions');assert(mechanism.children.find(s=>s.id==='direction-industry').hidden,'mechanism reader isolates academic methods');
console.log(JSON.stringify({focused_sector_boundaries:true}));
