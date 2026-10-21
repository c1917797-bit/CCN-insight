const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('business_insight/cloud_core/compression.js','utf8');
class Node{constructor(tag,text='',cls=''){this.tagName=tag;this.textContent=text;this.className=cls;this.children=[];this.dataset={};this.attrs={};this.events={};}append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}setAttribute(k,v){this.attrs[k]=String(v);}addEventListener(k,fn){this.events[k]=fn;}}
const root=new Node('section');let target;
const context={element:(...a)=>new Node(...a),mapText:(zh,en)=>zh,$:id=>id==='reading-guide'?root:null,topicPage:()=>false,state:{view:'home',locale:'zh'},document:{body:{dataset:{}},createElementNS:(_,tag)=>new Node(tag)},showView:view=>{target=view;}};
vm.createContext(context);vm.runInContext(source.slice(source.indexOf('function renderReadingGuide('),source.indexOf('function renderViewPurpose(')),context);
context.renderReadingGuide();
assert.equal(root.children[1].children.length,5);
const initial=root.children[1];context.state.view='updates';context.renderReadingGuide();
assert.strictEqual(root.children[1],initial,'directory explanation remains one static opening introduction');
assert(!JSON.stringify(root).includes('svg'),'no decorative animation');
context.topicPage=()=>true;context.renderReadingGuide();assert(root.hidden);
const html=fs.readFileSync('business_insight/cloud_core/index.html','utf8');
assert(html.indexOf('id="insight-report-presentation"')<html.indexOf('id="analysis-focus"'));
assert(/<section id="insight-report-presentation"/.test(html),'report body has no enclosing collapse');
assert(/<details class="section" id="ascend"/.test(html),'reasoning is one report appendix');
for(const [locale,label] of [['zh','洞察报告'],['en','Insight report']]){const pack=JSON.parse(fs.readFileSync('business_insight/cloud_core/data/focus-ui.'+locale+'.json','utf8'));assert.equal(pack.strings.view_home,label);}
console.log(JSON.stringify({pass:true,five_orthogonal_sections:true,one_time_introduction:true,one_report_body:true,report_before_research_links:true}));

const readerContext={state:{readerMode:'sources',view:'home'}};vm.createContext(readerContext);
vm.runInContext(source.slice(source.indexOf('function readerMatchesView('),source.indexOf('async function start(')),readerContext);
assert.equal(readerContext.readerMatchesView(),false,'a late source hydration cannot leave report view unhydrated');
readerContext.state={readerMode:'current',view:'home'};assert(readerContext.readerMatchesView());
readerContext.state={readerMode:'current',view:'updates'};assert(readerContext.readerMatchesView(),'same-family switching reuses current reader');
readerContext.state={readerMode:'map',view:'reports'};assert.equal(readerContext.readerMatchesView(),false);
assert(source.includes("if(request===state.epoch&&!readerMatchesView())start(state.view)"),'finish pending hydration then honor latest requested view');
console.log(JSON.stringify({latest_view_after_hydration:true,same_family_reuse:true}));


assert(html.indexOf('id=\"reading-guide\"')<html.indexOf('<nav class=\"wb-view-tabs'),'introduction precedes chapter navigation');
