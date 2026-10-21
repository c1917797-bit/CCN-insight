const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('business_insight/cloud_core/compression.js','utf8');
class Node{
 constructor(tag,text='',cls=''){this.tagName=tag.toUpperCase();this.textContent=text;this.className=cls;this.children=[];this.dataset={};this.hidden=false;}
 append(...nodes){for(const node of nodes){if(node.parent){node.parent.children=node.parent.children.filter(x=>x!==node);}node.parent=this;this.children.push(node);}}
 querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
 querySelectorAll(selector){let nodes=[];const visit=n=>{for(const child of n.children){nodes.push(child);visit(child);}};visit(this);
 if(selector.startsWith(':scope>')){nodes=this.children;selector=selector.slice(7);}
 return nodes.filter(n=>selector.split(',').some(s=>s.startsWith('#')?n.id===s.slice(1):s.startsWith('.')?n.className.split(' ').includes(s.slice(1)):n.tagName===s.toUpperCase()));}
 replaceWith(other){const i=this.parent.children.indexOf(this);this.parent.children[i]=other;other.parent=this.parent;}
}
let view='overview';
const context={element:(...args)=>new Node(...args),mapText:(zh,en)=>zh,researchView:()=>view,document:{createTextNode:text=>new Node('text',text)}};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function researchBlock('),source.indexOf('function renderTopicReportOutline(')),context);
const root=new Node('article');
context.renderTopicOverview(root,{},{});const originals={};
for(const key of ['scope','value','challenges','industry','mechanism','routes','papers','sources','comparison','boundary','implications','watch']){
 const node=new Node('section','','direction-section');node.id='direction-'+key;node.hidden=true;node.append(new Node('h2','99 · '+key));originals[key]=node;root.append(node);}
context.composeResearchOverview(root);
const groups=root.querySelector('.research-overview').children;
assert.equal(groups.length,6);
assert.deepEqual(groups.map(n=>n.dataset.readingLayer),['facts','facts','facts','facts','analysis','conclusion']);
for(const [key,node] of Object.entries(originals)){assert.equal(root.querySelectorAll('#direction-'+key).length,1);assert.equal(node.hidden,false);assert.equal(node.children[0].tagName,'H3');assert.equal(node.children[0].textContent,key);}
assert.equal(root.children.length,1,'move original sections without duplication');
assert.equal(root.querySelectorAll('details').length,0);
const body=new Node('article');context.appendResearchText(body,'研究结论：A\n适用条件：B\n暂缓条件：C');
assert.equal(body.children.length,3);assert.equal(body.children[0].children[0].tagName,'STRONG');
const block=context.researchBlock('proof','原始证据');assert.equal(block.tagName,'SECTION');assert.equal(block.children[0].tagName,'H4');
view='industry';const focus=new Node('article'),original=new Node('section');original.id='direction-industry';focus.append(original);context.composeResearchOverview(focus);assert.equal(focus.children[0],original);
for(const name of ['renderDossierCards','renderResearchRoutes','renderRouteEvidence','renderTopicIndustry','renderCompressionTopic','renderTopicCatalogue']){
 const start=source.indexOf('function '+name+'('),end=source.indexOf('\nfunction ',start+10);const body=source.slice(start,end<0?undefined:end);
 assert(!body.includes('disclosure('),name+' has no concealed research body');
}
console.log(JSON.stringify({pass:true,continuous_groups:6,canonical_nodes_preserved:12,conditional_conclusions:true,folded_research:false}));

const shell=fs.readFileSync('assets/lri-shell.js','utf8');
const method=shell.slice(shell.indexOf('  isExactCurrentLocation(path) {'),shell.indexOf('  currentRepoPath() {'));
const navContext={URL,repoRootUrl:new URL('https://example.test/'),document:{location:{href:'https://example.test/topic.html?topic=a#research-overview-facts'}}};
vm.createContext(navContext);vm.runInContext('class Shell {'+method+'}; this.shell=new Shell()',navContext);
assert(navContext.shell.isExactCurrentLocation('topic.html?topic=a#research-overview-facts'));
assert(!navContext.shell.isExactCurrentLocation('topic.html?topic=a#research-overview-problem'));
assert(!navContext.shell.isExactCurrentLocation('topic.html?topic=b#research-overview-facts'));
assert(source.includes("requestAnimationFrame(()=>$(id)?.scrollIntoView({block:'start'}))"),'scroll to the current DOM after view rerender');
console.log(JSON.stringify({reader_section_highlight:true,post_render_anchor_scroll:true}));
