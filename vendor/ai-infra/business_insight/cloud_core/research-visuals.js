/* UI-only SVG primitives. Labels always come from the current reader snapshot. */
(() => {
  'use strict';
  const NS = 'http://www.w3.org/2000/svg';
  const node = (name, attributes = {}, text = '') => {
    const result = document.createElementNS(NS, name);
    for (const [key, value] of Object.entries(attributes)) result.setAttribute(key, String(value));
    if (text) result.textContent = text;
    return result;
  };
  function lines(value, limit, locale) {
    if (locale !== 'en') return Array.from(value).reduce((out, char, index) => {
      if (index % limit === 0) out.push('');
      out[out.length - 1] += char; return out;
    }, []);
    const out = []; let line = '';
    for (const word of value.split(/\s+/)) {
      if (line && line.length + word.length + 1 > limit) { out.push(line); line = ''; }
      if (word.length > limit) {
        if (line) { out.push(line); line = ''; }
        for (let i = 0; i < word.length; i += limit) out.push(word.slice(i, i + limit));
      } else line += (line ? ' ' : '') + word;
    }
    if (line) out.push(line); return out;
  }
  function icon(kind, size = 40) {
    const svg = node('svg', {viewBox:'0 0 48 48', width:size, height:size, 'aria-hidden':'true', focusable:'false', class:'research-mini-icon'});
    const stroke = {fill:'none', stroke:'currentColor', 'stroke-width':1.7, 'stroke-linecap':'round', 'stroke-linejoin':'round'};
    if (kind === 'precision') {
      for (let row = 0; row < 3; row++) for (let col = 0; col < 3; col++) svg.append(node('rect',{x:7+col*12,y:7+row*12,width:9,height:9,rx:2,...stroke,fill:row===1&&col===1?'currentColor':'none'}));
    } else if (kind === 'selection') {
      for (let row = 0; row < 3; row++) for (let col = 0; col < 3; col++) {
        const x=9+col*13,y=10+row*13; svg.append(node('circle',{cx:x,cy:y,r:3,...stroke}));
        if ((row+col)%2===0) svg.append(node('path',{d:`M ${x-4} ${y+4} l 8 -8`,...stroke}));
      }
    } else if (kind === 'distillation') {
      svg.append(node('rect',{x:4,y:10,width:16,height:28,rx:3,...stroke}),node('rect',{x:33,y:17,width:10,height:14,rx:2,...stroke}),node('path',{d:'M 23 24 H 30 M 27 21 l 3 3 -3 3',...stroke}));
      for(let i=0;i<3;i++)svg.append(node('path',{d:`M 8 ${16+i*8} h 8`,...stroke}));
    } else if (kind === 'factorization') {
      svg.append(node('rect',{x:3,y:10,width:16,height:28,rx:2,...stroke}),node('path',{d:'M 22 22 h 5 M 22 26 h 5',...stroke}),node('rect',{x:30,y:10,width:5,height:28,rx:1,...stroke}),node('rect',{x:39,y:10,width:6,height:9,rx:1,...stroke}));
    } else if (kind === 'cache') {
      for(let i=0;i<3;i++)svg.append(node('rect',{x:7+i*5,y:7+i*9,width:27,height:12,rx:3,...stroke,fill:'#fff'}));
    } else {
      for(let i=0;i<3;i++)svg.append(node('path',{d:`M 8 ${12+i*12} h ${18+i*5}`, ...stroke}));
      svg.append(node('path',{d:'M 34 8 v 30 m -4 -4 4 4 4 -4',...stroke}));
    }
    return svg;
  }
  function flow(labels, {locale='zh', title='', description=''} = {}) {
    if (!labels.length) throw new Error('SVG flow needs a semantic stage');
    const host = document.createElement('div'); host.className='research-visual-flow';
    for(const narrow of [false,true]) {
      const wrapped = labels.map(label => lines(label, narrow ? (locale==='en'?26:15) : (locale==='en'?16:7), locale));
      const heights = wrapped.map(row => Math.max(narrow?120:168, (narrow?64:86)+row.length*(narrow?25:28)));
      const rowHeight = Math.max(...heights), width = narrow?360:labels.length*260;
      const height = narrow?heights.reduce((a,b)=>a+b,0)+(labels.length-1)*38+16:rowHeight+28;
      const svg=node('svg',{viewBox:`0 0 ${width} ${height}`,role:'img','aria-label':title||labels.join(' → '),focusable:'false',class:narrow?'research-visual-narrow':'research-visual-wide'});
      svg.append(node('title',{},title||labels.join(' → ')),node('desc',{},description));
      let cursor=8;
      labels.forEach((label,index)=>{
        const x=narrow?8:8+index*260, y=narrow?cursor:8, w=narrow?344:224, h=narrow?heights[index]:rowHeight;
        const group=node('g',{'data-visual-stage':index+1});
        group.append(node('rect',{x,y,width:w,height:h,rx:12,fill:'#fff',stroke:'#d9e2ec','stroke-width':1.5}),node('path',{d:`M ${x+16} ${y+1} H ${x+w-16}`,stroke:'#a91f2b','stroke-width':3,fill:'none'}));
        group.append(node('text',{x:x+20,y:y+33,fill:'#a91f2b','font-size':narrow?16:19,'font-weight':700},String(index+1).padStart(2,'0')));
        const text=node('text',{x:x+20,y:y+(narrow?66:78),fill:'#20334c','font-size':narrow?20:24,'font-weight':600});
        wrapped[index].forEach((line,lineIndex)=>text.append(node('tspan',{x:x+20,dy:lineIndex?(narrow?25:28):0},line)));group.append(text);svg.append(group);
        if(index<labels.length-1){
          const d=narrow?`M 180 ${y+h+8} v 22 m -6 -6 6 6 6 -6`:`M ${x+w+6} ${y+h/2} h 22 m -6 -6 6 6 -6 6`;
          svg.append(node('path',{d,fill:'none',stroke:'#8494a9','stroke-width':2,'stroke-linecap':'round','stroke-linejoin':'round','aria-hidden':'true'}));
        }
        cursor+=h+38;
      });
      host.append(svg);
    }
    return host;
  }
  globalThis.LRICompressionVisuals=Object.freeze({icon,flow,lines});
})();
