/* Authored map translations. Text is changed in place; the simulator keeps its state. */
(() => {
  const map = document.getElementById('map');
  const button = document.getElementById('map-language-toggle');
  if (!map || !button) return;
  const dictionary = __MAP_EN__;
  const storageKey = 'agent-scheduling.map-language';
  const chinese = /[\u3400-\u9fff]/;
  const escape = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const phrases = new RegExp(Object.keys(dictionary).sort((a,b) => b.length-a.length).map(escape).join('|'), 'g');
  const translate = value => {
    if (!chinese.test(value)) return value;
    const trim = value.trim();
    const result = dictionary[trim] ?? trim.replace(phrases, key => dictionary[key]);
    return value.slice(0, value.indexOf(trim)) + result.replace(/，/g, ', ').replace(/：/g, ': ').replace(/。/g, '.').replace(/；/g, '; ').replace(/、/g, ', ').replace(/（/g, ' (').replace(/）/g, ')') + value.slice(value.indexOf(trim)+trim.length);
  };
  let language = 'zh';
  try { language = localStorage.getItem(storageKey) === 'en' ? 'en' : 'zh'; } catch (_) {}
  const requested = new URL(location.href).searchParams.get('lang');
  if (requested === 'en' || requested === 'zh') language = requested;
  const roots = [map, ...document.querySelectorAll('.rail,#report-top,.reading-flow,footer,.skip-link')];
  const originals = new WeakMap(), attributes = new WeakMap(), fitted = new WeakMap();
  const originalTitle = document.title;
  let queued = false, observer;
  function updateValue(node, property, memory, english) {
    const current = node[property];
    let saved = memory.get(node);
    if (!saved || (current !== saved.zh && current !== saved.en)) {
      saved = {zh: current, en: translate(current)};
      memory.set(node, saved);
    }
    const next = english ? saved.en : saved.zh;
    if (next !== current) node[property] = next;
  }
  function fitSvg(english) {
    for (const svg of map.querySelectorAll('svg')) {
      if (!svg.getBoundingClientRect().width) continue;
      const shapeBoxes = [...svg.querySelectorAll('rect,polygon')].filter(s => !s.closest('defs')).map(s => s.getBBox());
      for (const text of svg.querySelectorAll('text')) {
        if (!fitted.has(text)) fitted.set(text, {length:text.getAttribute('textLength'),adjust:text.getAttribute('lengthAdjust')});
        const original = fitted.get(text);
        for (const [key,value] of [['textLength',original.length],['lengthAdjust',original.adjust]]) {
          if (value === null) text.removeAttribute(key); else text.setAttribute(key,value);
        }
        if (!english || text.querySelector('tspan') || !text.textContent.trim()) continue;
        const x = Number(text.getAttribute('x')), y = Number(text.getAttribute('y'));
        if (!Number.isFinite(x+y)) continue;
        const boxes = shapeBoxes.filter(b=>b.width>40 && x>=b.x+4 && x<b.x+b.width-8 && y>b.y+3 && y<=b.y+b.height);
        if (!boxes.length) continue;
        const box = boxes.sort((a,b)=>a.width*a.height-b.width*b.height)[0];
        const width = Math.max(36, box.x+box.width-x-16);
        if (text.getComputedTextLength()>width) {text.setAttribute('textLength',String(width));text.setAttribute('lengthAdjust','spacingAndGlyphs');}
      }
    }
  }
  function apply() {
    queued = false;
    observer.disconnect();
    const active = document.body.dataset.reportView === 'map';
    const english = active && language === 'en';
    document.documentElement.lang = english ? 'en' : 'zh-CN';
    map.dataset.language = english ? 'en' : 'zh';
    document.body.classList.toggle('map-reading-english',english);
    document.title = english ? translate(originalTitle) : originalTitle;
    for (const root of roots) {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      let node;
      while ((node=walker.nextNode())) {
        if (node.parentElement.closest('[data-language-control],script,style')) continue;
        updateValue(node,'nodeValue',originals,english);
      }
      for (const el of [root,...root.querySelectorAll('[aria-label],[title],[alt]')]) {
        if (el.closest('[data-language-control]')) continue;
        let saved = attributes.get(el);
        if (!saved) {saved={};attributes.set(el,saved);}
        for (const key of ['aria-label','title','alt']) {
          const current = el.getAttribute(key);
          if (current === null) continue;
          if (!saved[key] || (current!==saved[key].zh && current!==saved[key].en)) saved[key]={zh:current,en:translate(current)};
          const value = english ? saved[key].en : saved[key].zh;
          if (value!==current) el.setAttribute(key,value);
        }
      }
    }
    button.textContent = language === 'en' ? '中文' : 'English';
    button.setAttribute('lang',language === 'en' ? 'zh-CN' : 'en');
    button.setAttribute('aria-label',english ? 'Switch technology map to Chinese' : '将技术地图切换为英文');
    button.setAttribute('aria-pressed',String(language==='en'));
    document.getElementById('map-language-status').textContent = english ? 'English' : '中文';
    fitSvg(english);
    for (const root of roots) observer.observe(root,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['aria-label','title','alt']});
  }
  function queue() {if (!queued) {queued=true;requestAnimationFrame(apply);}}
  observer = new MutationObserver(queue);
  button.addEventListener('click',()=>{
    language=language==='en'?'zh':'en';
    try {localStorage.setItem(storageKey,language);} catch (_) {}
    const url=new URL(location.href);url.searchParams.set('lang',language);
    history.replaceState(history.state,'',url);
    const top = document.querySelector('.map-section-top').getBoundingClientRect().top;
    apply();
    window.scrollBy({top:document.querySelector('.map-section-top').getBoundingClientRect().top-top,behavior:'instant'});
  });
  document.addEventListener('reportviewchange',queue);
  window.addEventListener('hashchange',queue);
  document.addEventListener('toggle',queue,true);
  window.addEventListener('resize',queue,{passive:true});
  apply();
})();
