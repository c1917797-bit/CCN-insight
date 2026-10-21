import './foundation-player.js';
const response=await fetch('compression-lessons.json');
if(!response.ok)throw new Error('原理课程读取失败');
const data=await response.json();
for(const player of document.querySelectorAll('lri-foundation-lesson')){
 const method=player.dataset.method;
 player.lesson={method,locale:'zh',ui:data.ui,referenceNumbers:data.referenceNumbers,steps:data.steps.filter(x=>x.method_id===method).sort((a,b)=>a.position-b.position),values:data.values.filter(x=>x.method_id===method)};
}
