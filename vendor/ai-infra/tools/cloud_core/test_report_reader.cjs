const fs=require('fs'),vm=require('vm'),assert=require('assert');
class Node {
 constructor(tag,text='',cls=''){this.tag=tag;this.textContent=text;this.className=cls;this.children=[];this.attrs={};this.events={};this.dataset={};this.open=false;this.value='';this.scrollTop=this.scrollLeft=0;}
 append(...xs){this.children.push(...xs);xs.forEach(x=>x.parent=this);}
 setAttribute(k,v){this.attrs[k]=v;}getAttribute(k){return this.attrs[k]??null;}
 set src(v){this.attrs.src=v;}get src(){return this.attrs.src;}
 addEventListener(k,fn){(this.events[k]??=[]).push(fn);}fire(k,e={}){for(const f of this.events[k]||[])f(e);}
 showModal(){this.open=true;}close(){this.open=false;this.fire('close');}focus(){this.focused=true;}replaceChildren(){this.children=[];}
 closest(selector){return selector.split(',').includes(this.tag)?this:null;}
}
const code=fs.readFileSync('business_insight/cloud_core/current-synthesis.js','utf8');
const helper=code.slice(code.indexOf('// Reader state is'),code.indexOf('function renderReports(m)'));
const box={el:(...args)=>new Node(...args),ui:k=>k,check:(x,m)=>assert(x,m)};vm.createContext(box);vm.runInContext(helper,box);
const slides=[0,1,2].map(x=>({url:'slide-'+x})),viewer=new Node('div'),calls=[];
const mount=()=>box.mountReportReader(viewer,slides,'Verified report',a=>{calls.push(a.url);return a.url;},'report-digest');
let dispose=mount();const [inline,preview,previewStatus,dialog]=viewer.children,[header,expanded,help,stage]=dialog.children;
const [prev,counter,next,jump,open]=inline.children,[largeFigure,largeStatus]=stage.children,large=largeFigure.children[0],zoom=expanded.children[4].children[0];
assert.equal(preview.children[0].src,'slide-0');assert.equal(large.src,undefined,'No hidden full-window image request');assert(prev.disabled);assert(!next.disabled);
next.fire('click');assert.equal(counter.textContent,'2 / 3');open.fire('click');assert(dialog.open);assert.equal(large.src,'slide-1');assert.equal(largeFigure.dataset.zoom,'fit');
zoom.value='200';zoom.fire('change');assert.equal(largeFigure.dataset.zoom,'200');
dialog.fire('keydown',{key:'ArrowRight',target:stage,preventDefault(){}});assert.equal(large.src,'slide-2');assert(next.disabled);next.fire('click');assert.equal(counter.textContent,'3 / 3');
dialog.fire('keydown',{key:'ArrowLeft',target:zoom,preventDefault(){throw Error('Native select hijacked');}});assert.equal(counter.textContent,'3 / 3');
header.children[1].fire('click');assert(!dialog.open);assert(open.focused);preview.fire('click');assert.equal(large.src,'slide-2');assert.equal(largeFigure.dataset.zoom,'200');
large.fire('error');assert.equal(largeStatus.textContent,'deck_image_error');large.fire('load');assert(largeStatus.hidden);
jump.value='99';assert.throws(()=>jump.fire('change'),/Invalid presentation page/);jump.value='1';jump.fire('change');
dispose();assert.equal(viewer.children.length,0);dispose=mount();assert.equal(viewer.children[0].children[1].textContent,'2 / 3','Position survives rerender');viewer.children[0].children[4].fire('click');assert.equal(viewer.children[3].children[3].children[0].dataset.zoom,'200');dispose();
console.log(JSON.stringify({pass:true,onlyCurrentPage:true,bounds:true,keyboard:true,stateRetention:true,imageError:true}));


const figureViewer=new Node('div'),figureCalls=[],figures=[{format:'figure-01-tech',url:'original-tech'},{format:'figure-01-results',url:'original-results'}];
box.mountReportReader(figureViewer,slides,'Original figures',a=>{figureCalls.push(a.url);return a.url;},'original-digest',figures);
const figureBar=figureViewer.children[0],figureDialog=figureViewer.children[3],figureLarge=figureDialog.children[3].children[0].children[0];
assert(!figureCalls.includes('original-tech'),'No original-figure prefetch');
assert(!figureBar.children[5].hidden);assert(!figureBar.children[6].hidden);
figureBar.children[5].fire('click');assert.equal(figureLarge.src,'original-tech');assert(figureDialog.open);
figureDialog.children[1].children[5].fire('click');assert.equal(figureLarge.src,'slide-0');
figureBar.children[6].fire('click');assert.equal(figureLarge.src,'original-results');
figureDialog.children[1].children[2].fire('click');assert.equal(figureLarge.src,'slide-1');assert(figureBar.children[5].hidden);
assert(!figureCalls.includes(undefined),'All figure URLs resolved');
console.log(JSON.stringify({originalFigures:true,lazy:true,pageCorrespondence:true,backToSlide:true}));

const titleViewer=new Node('div');
const titleDispose=box.mountReportReader(titleViewer,slides,'Named pages',a=>a.url,'named-digest',figures,['Verified paper A','','Verified paper B']);
const titleBar=titleViewer.children[0],titleDialog=titleViewer.children[3],titleStage=titleDialog.children[3],titleLarge=titleStage.children[0].children[0];
assert.equal(titleBar.children[3].children[0].textContent,'deck_slide 1 · Verified paper A');
assert.equal(titleBar.children[1].attrs['aria-live'],'polite');
titleBar.children[4].fire('click');assert(titleStage.focused);
titleDialog.children[1].children[6].fire('click');assert.equal(titleLarge.src,'original-tech');
titleDialog.children[1].children[7].fire('click');assert.equal(titleLarge.src,'original-results');
titleDialog.fire('keydown',{key:'End',target:titleStage,preventDefault(){}});assert.equal(titleLarge.src,'slide-2');assert(titleDialog.children[1].children[6].hidden);
titleDialog.fire('keydown',{key:'Home',target:titleStage,preventDefault(){}});assert.equal(titleLarge.src,'slide-0');
titleDialog.fire('keydown',{key:'PageDown',target:titleStage,preventDefault(){}});assert.equal(titleLarge.src,'slide-1');
titleDialog.fire('keydown',{key:'PageUp',target:titleStage,preventDefault(){}});assert.equal(titleLarge.src,'slide-0');
titleDispose.goTo(2);assert.equal(titleLarge.src,'slide-2');assert(titleDialog.open&&titleStage.focused,'Selection jump opens a focused reader');
assert.throws(()=>titleDispose.goTo(-1),/Invalid presentation page/);
titleDialog.children[0].children[1].fire('click');
titleViewer.children[1].fire('click');titleDialog.children[0].children[1].fire('click');assert(titleViewer.children[1].focused,'Close returns to invoking preview');
titleDispose();
console.log(JSON.stringify({usability:true,namedPages:true,defaultFit:true,modalOriginalSwitch:true,keyboardJump:true,focusReturn:true}));
