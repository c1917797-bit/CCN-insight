import { readSelectedLanguage, subscribeSelectedLanguage, normalizeSelectedLanguage } from './lri-selected-language.js';

/* LRI Motion Scene: instance-owned clock, responsive layout and lifecycle.
 * SVG files remain declarative assets. Shadow DOM is not a security sandbox.
 */
const WORDS = {
  zh: {play:'继续动画',pause:'暂停动画',restart:'重播',detail:'查看完整图',fit:'适应屏幕',speed:'速度',progress:'动画进度',loading:'正在加载',playing:'播放中',paused:'已暂停',offscreen:'离屏暂停',hidden:'页面隐藏，已暂停',reduced:'减少动态效果 · 完整静态图',error:'动态图加载失败，显示备用内容',static:'静态图',source:'打开原图',hint:'左右滑动查看完整图；点击“适应屏幕”返回纵向阅读。'},
  en: {play:'Play',pause:'Pause',restart:'Replay',detail:'Full diagram',fit:'Fit screen',speed:'Speed',progress:'Animation progress',loading:'Loading',playing:'Playing',paused:'Paused',offscreen:'Paused offscreen',hidden:'Paused while page is hidden',reduced:'Reduced motion · complete static view',error:'Diagram unavailable; fallback shown',static:'Static diagram',source:'Open SVG',hint:'Scroll sideways for the full diagram; select Fit screen to return.'}
};
const CSS = `
:host{display:block;contain:content;min-width:0;max-width:100%;scroll-margin-block-start:var(--lri-motion-scroll-offset,96px);color:#172b46;font:14px Arial,"Microsoft YaHei",sans-serif}
.frame{border:1px solid #d7e2ee;border-radius:16px;overflow:hidden;max-width:100%;background:#f5f8fc}
.toolbar,.timeline{display:flex;align-items:center;flex-wrap:wrap;gap:8px;padding:10px 12px;background:#fff}
.toolbar{border-bottom:1px solid #d7e2ee}
.toolbar,.scroll,button,select,input,.source{scroll-margin-block-start:var(--lri-motion-scroll-offset,96px)}
button,select,.source{box-sizing:border-box;min-height:44px;border:1px solid #bdcde0;border-radius:9px;background:#fff;color:#172b46;font:inherit;padding:8px 11px;cursor:pointer}
button:disabled,select:disabled{opacity:.5;cursor:default}
button:focus-visible,select:focus-visible,input:focus-visible,.scroll:focus-visible,.source:focus-visible{outline:3px solid #176acc;outline-offset:-3px}
button[aria-pressed=true]{background:#edf5ff;border-color:#176acc}
.rate{display:inline-flex;align-items:center;gap:7px}
.scroll{overflow:auto;max-width:100%;overscroll-behavior-inline:contain;touch-action:pan-x pan-y}
.stage{width:100%;margin-inline:auto}.stage[data-layout=mobile]{max-width:480px}
.stage svg{display:block;width:100%;height:auto;max-width:100%}
.stage[data-mode=detail] svg{max-width:none}
.timeline{flex-wrap:nowrap;border-top:1px solid #d7e2ee}
.timeline input{flex:1;min-width:0;min-height:36px;accent-color:#176acc}
.timeline output{font-size:13px;font-variant-numeric:tabular-nums;white-space:nowrap;color:#526984}
.status{margin:0;padding:8px 14px;font-size:13px;color:#526984}
.hint{margin:0;padding:8px 14px;font-size:13px;color:#526984}
.source{display:inline-flex;align-items:center;text-decoration:none;font-size:13px}
.fallback{padding:12px}.fallback ::slotted(img){display:block;max-width:100%;height:auto}
[hidden]{display:none!important}
/* Lessons own one toolbar; standalone scene behavior remains unchanged. */
:host([data-lesson-player]) .toolbar,:host([data-lesson-player]) .timeline,:host([data-lesson-player]) .hint{display:none}
:host([data-lesson-player]) .frame{border:0;border-radius:0;background:transparent}
:host([data-lesson-player]) .status{display:none}
:host([data-lesson-player][data-scene-state=loading]) .status,:host([data-lesson-player][data-scene-state=error]) .status{display:block;background:#fff}
:host([data-lesson-player]) .fallback{padding:0}
@media(max-width:440px){.toolbar{gap:6px;padding:8px}.toolbar .rate span{display:none}button,select{padding:8px 10px}.timeline{gap:8px}}
@media print{.toolbar,.timeline,.hint,.status{display:none}.scroll{overflow:visible}.stage{width:100%!important}.stage svg{max-width:100%}}
`;
function finite(value, fallback) { const n=Number(value); return Number.isFinite(n)?n:fallback; }
function validViewBox(value) { const a=(value||'').trim().split(/[ ,]+/).map(Number); return a.length===4&&a.every(Number.isFinite)&&a[2]>0&&a[3]>0; }

export class LriMotionScene extends HTMLElement {
  static observedAttributes=['src','fit','mobile-viewbox','mobile-breakpoint','controls','lang'];
  #root; #stage; #svg=null; #ui={}; #abort; #fetchAbort; #resize; #intersection; #motion;
  #connected=false; #ready=false; #visible=false; #paused=false; #running=false;
  #time=0; #anchor=0; #rate=1; #duration=0; #width=0; #desktop=''; #layout=''; #timer=0; #loadGeneration=0;
  #words=WORDS.zh; #loadedSource=null; #inlineMarkup=null; #unsubscribeLanguage;
  #responsiveHandler=()=>{this.#width=this.clientWidth;this.#applyLayout();};
  constructor(){
    super(); this.#root=this.attachShadow({mode:'open'});
    this.#root.innerHTML=`<style>${CSS}</style><section class="frame">
      <div class="toolbar"><button type="button" data-action="playback"></button><button type="button" data-action="restart"></button><button type="button" data-action="view"></button><label class="rate"><span></span><select aria-label="Speed"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label><a class="source" target="_blank" rel="noopener"></a></div>
      <div class="scroll" tabindex="0"><div class="stage"></div><div class="fallback"><slot></slot></div></div>
      <div class="timeline"><input type="range" min="0" max="1" step="0.1" value="0"><output>0.0 / 0.0 s</output></div>
      <p class="status" role="status"></p><p class="hint" hidden></p></section>`;
    this.#stage=this.#root.querySelector('.stage');
    for(const k of ['playback','restart','view'])this.#ui[k]=this.#root.querySelector(`[data-action=${k}]`);
    for(const k of ['scroll','fallback','timeline','status','hint','source'])this.#ui[k]=this.#root.querySelector('.'+k);
    this.#ui.range=this.#root.querySelector('input');this.#ui.output=this.#root.querySelector('output');this.#ui.rate=this.#root.querySelector('select');
  }
  connectedCallback(){
    if(this.#connected)return;
    this.#connected=true;this.#abort=new AbortController();this.#motion=matchMedia('(prefers-reduced-motion: reduce)');
    const on=(el,type,fn)=>el.addEventListener(type,fn,{signal:this.#abort.signal});
    on(this.#ui.playback,'click',()=>this.#paused?this.play():this.pause());
    on(this.#ui.restart,'click',()=>this.restart());
    on(this.#ui.view,'click',()=>this.setAttribute('fit',this.getAttribute('fit')==='detail'?'fit':'detail'));
    on(this.#ui.range,'input',()=>this.seek(Number(this.#ui.range.value)*1000));
    on(this.#ui.rate,'change',()=>{this.playbackRate=Number(this.#ui.rate.value);});
    on(this.#ui.scroll,'keydown',event=>this.#readingKey(event));
    on(document,'visibilitychange',()=>this.#sync());
    on(this.#motion,'change',()=>{this.#freeze();this.#sync();});
    this.#resize=new ResizeObserver(entries=>{const width=entries[0].contentRect.width;if(Math.abs(width-this.#width)>.5){this.#width=width;this.#applyLayout();}});
    this.#resize.observe(this);
    window.addEventListener('resize',this.#responsiveHandler,{passive:true,signal:this.#abort.signal});
    this.#intersection=new IntersectionObserver(entries=>{this.#visible=entries[0].isIntersecting;this.#sync();},{rootMargin:'0px'});
    this.#intersection.observe(this);
    this.#unsubscribeLanguage=subscribeSelectedLanguage(()=>{this.#localize();this.#sync();},
      {document:this.ownerDocument,immediate:false,signal:this.#abort.signal});
    this.#width=this.clientWidth;this.#localize();
    if(this.#ready&&this.#loadedSource===this.getAttribute('src')){this.#applyLayout();this.#sync();}else void this.load();
  }
  disconnectedCallback(){
    this.#freeze();this.#connected=false;this.#visible=false;this.#loadGeneration++;
    this.#fetchAbort?.abort();this.#abort?.abort();this.#resize?.disconnect();this.#intersection?.disconnect();this.#unsubscribeLanguage?.();this.#unsubscribeLanguage=null;
    clearInterval(this.#timer);this.#timer=0;
    for(const a of this.animations)a.pause();
    this.dataset.sceneState='disconnected';
  }
  attributeChangedCallback(name,oldValue,newValue){
    if(oldValue===newValue||!this.#connected)return;
    if(name==='src')void this.load();
    else if(name==='lang'||name==='controls'){this.#localize();this.#sync();}
    else this.#applyLayout();
  }
  // Generated scenes use the same parser and admission boundary as fetched SVGs.
  // The host provides declarative markup; no data/blob URL or unchecked DOM path.
  set sceneMarkup(value){
    if(typeof value!=='string'||!value.trim()||value.length>262144)throw new TypeError('Invalid inline scene markup');
    this.#inlineMarkup=value;
    if(this.#connected)void this.load();
  }
  get sceneMarkup(){return this.#inlineMarkup;}
  get animations(){return this.#stage.getAnimations({subtree:true});}
  get duration(){return this.#duration;}
  get currentTime(){return this.#time+(this.#running?(performance.now()-this.#anchor)*this.#rate:0);}
  get playbackRate(){return this.#rate;}
  set playbackRate(value){const rate=finite(value,1);if(rate<=0||rate>8)throw new RangeError('playbackRate must be > 0 and <= 8');this.#freeze();this.#rate=rate;this.#sync();}
  get reducedMotion(){return !!this.#motion?.matches;}
  play(){this.#paused=false;this.#sync();}
  pause(){this.#freeze();this.#paused=true;this.#sync();}
  restart(){this.#freeze();this.#time=0;this.#paused=false;this.#sync();}
  seek(ms){this.#freeze();this.#time=Math.min(this.#duration||Infinity,Math.max(0,finite(ms,0)));this.#paused=true;this.#sync();}
  #readingKey(event){
    // Canvas-only shortcuts: native inputs and horizontal detail scrolling keep
    // their own keys. Never register page-global keyboard handlers.
    if(event.target!==this.#ui.scroll||event.defaultPrevented||event.repeat||
       event.ctrlKey||event.altKey||event.metaKey||!this.hasAttribute('controls')||
       !this.#ready||this.reducedMotion||!this.#duration)return;
    const key=event.key.toLowerCase();
    if(![' ','r','home','end'].includes(key))return;
    event.preventDefault();
    if(key===' ')this.#paused?this.play():this.pause();
    else if(key==='r')this.restart();
    else this.seek(key==='home'?0:this.#duration);
  }
  #freeze(){this.#time=this.currentTime;this.#running=false;this.#anchor=0;}
  async load(){
    if(!this.#connected)return;
    this.#freeze();this.#ready=false;this.#svg=null;this.#layout='';this.#time=0;this.#duration=0;
    for(const a of this.animations)a.cancel();this.#stage.replaceChildren();
    this.#ui.fallback.hidden=false;this.#ui.source.removeAttribute('href');this.#setState('loading');this.#sync();
    const ticket=++this.#loadGeneration;this.#fetchAbort?.abort();this.#fetchAbort=new AbortController();
    try{
      const source=this.getAttribute('src'),inline=this.#inlineMarkup;
      if(!source&&!inline)throw new Error('Missing scene source');
      const url=new URL(source||document.baseURI,document.baseURI);
      if(!['http:','https:'].includes(url.protocol)||url.origin!==location.origin)throw new Error('Scene source must be same-origin');
      let body=inline;
      if(!inline){
        this.#ui.source.href=url.href;
        const response=await fetch(url,{credentials:'same-origin',signal:this.#fetchAbort.signal});
        if(!response.ok)throw new Error(`SVG HTTP ${response.status}`);
        if(new URL(response.url).origin!==location.origin)throw new Error('Cross-origin scene redirect');
        body=await response.text();
      }
      this.#ui.source.hidden=!!inline;
      if(ticket!==this.#loadGeneration||!this.#connected)return;
      const doc=new DOMParser().parseFromString(body,'image/svg+xml');
      if(doc.querySelector('parsererror')||doc.documentElement.localName!=='svg'||doc.documentElement.namespaceURI!=='http://www.w3.org/2000/svg')throw new Error('Invalid SVG');
      this.#admit(doc.documentElement,url);
      if(inline&&[...doc.querySelectorAll('style')].some(n=>/@import|url\s*\(/i.test(n.textContent)))throw new Error('Active inline SVG CSS rejected');
      if(ticket!==this.#loadGeneration||!this.#connected)return;
      this.#svg=document.importNode(doc.documentElement,true);this.#desktop=this.#svg.getAttribute('viewBox');
      if(!validViewBox(this.#desktop))throw new Error('Missing or invalid SVG viewBox');
      this.#svg.removeAttribute('width');this.#svg.removeAttribute('height');this.#svg.setAttribute('preserveAspectRatio','xMidYMid meet');
      this.#stage.replaceChildren(this.#svg);this.#ready=true;
      this.#duration=Math.max(0,finite(this.#svg.dataset.cycle,0)*1000);
      this.#applyLayout();
      if(!this.#duration)this.#duration=Math.max(0,...this.animations.map(a=>finite(a.effect?.getTiming().duration,0)));
      this.#loadedSource=source;this.#ui.fallback.hidden=true;this.#sync();
      this.dispatchEvent(new CustomEvent('scene-ready',{bubbles:true,composed:true,detail:{src:url.href,duration:this.duration}}));
    }catch(error){
      if(error.name==='AbortError'||ticket!==this.#loadGeneration)return;
      this.#ready=false;this.#stage.replaceChildren();this.#svg=null;this.#ui.fallback.hidden=false;this.#setState('error');this.#sync();
      this.dispatchEvent(new CustomEvent('scene-error',{bubbles:true,composed:true,detail:{message:error.message}}));
    }
  }
  #applyLayout(){
    if(!this.#svg)return;
    const detail=this.getAttribute('fit')==='detail';
    const breakpoint=Math.min(1200,Math.max(240,finite(this.getAttribute('mobile-breakpoint')||640,640)));
    const requestedBox=this.getAttribute('mobile-viewbox');
    const generatedBox=this.#svg.dataset.mobileViewbox;
    const mobileBox=validViewBox(requestedBox)?requestedBox:generatedBox;
    const narrow=window.innerWidth<=breakpoint||this.#width<=breakpoint;
    const mobile=!detail&&narrow&&!!this.#svg.querySelector('[data-responsive=mobile]')&&validViewBox(mobileBox);
    const layout=mobile?'mobile':'desktop';const key=layout+'|'+detail+'|'+(mobile?mobileBox:this.#desktop);
    if(key!==this.#layout){
      this.#freeze();this.#layout=key;
      this.#svg.setAttribute('viewBox',mobile?mobileBox:this.#desktop);
      for(const e of this.#svg.querySelectorAll('[data-responsive]'))e.style.display=(e.dataset.responsive===layout)?'inline':'none';
    }
    this.#stage.dataset.layout=layout;this.#stage.dataset.mode=detail?'detail':'fit';
    this.#stage.style.width=detail?Math.max(960,this.#width)+'px':'100%';
    this.#ui.view.textContent=detail?this.#words.fit:this.#words.detail;
    this.#ui.view.setAttribute('aria-pressed',String(detail));
    this.#ui.hint.hidden=!detail||this.#width>=960;
    if(!detail)this.#ui.scroll.scrollLeft=0;
    this.#sync();
  }
  #sync(){
    if(!this.#connected)return;
    this.#freeze();
    const effects=this.animations;
    // CSS effects may first appear after reduced-motion is turned off.
    if(this.#ready&&!this.#duration)
      this.#duration=Math.max(0,...effects.map(a=>finite(a.effect?.getTiming().duration,0)));
    const active=new Set(effects.filter(a=>{const group=a.effect?.target?.closest?.('[data-responsive]');return !group||group.dataset.responsive===this.#stage.dataset.layout;}));
    const canRun=this.#ready&&!this.#paused&&this.#visible&&!document.hidden&&!this.reducedMotion&&active.size>0;
    for(const a of effects){a.pause();a.playbackRate=this.#rate;a.currentTime=this.#time;if(canRun&&active.has(a))a.play();}
    this.#running=canRun;this.#anchor=performance.now();
    if(this.#ready)this.#setState(this.reducedMotion?'reduced':this.#paused?'paused':document.hidden?'hidden':!this.#visible?'offscreen':!active.size?'static':'playing');
    const disabled=!this.#ready||this.reducedMotion||!this.#duration;
    this.#ui.playback.disabled=this.#ui.restart.disabled=this.#ui.range.disabled=this.#ui.rate.disabled=disabled;
    this.#ui.playback.textContent=this.#paused?this.#words.play:this.#words.pause;
    this.#ui.playback.setAttribute('aria-pressed',String(!this.#paused));
    this.#ui.range.max=String(this.#duration/1000||1);this.#displayRate();
    this.#updateClock();
    if(canRun&&this.hasAttribute('controls')&&!this.#timer)this.#timer=setInterval(()=>this.#updateClock(),200);
    if((!canRun||!this.hasAttribute('controls'))&&this.#timer){clearInterval(this.#timer);this.#timer=0;}
  }
  #displayRate(){
    const value=String(this.#rate);
    for(const option of this.#ui.rate.querySelectorAll('[data-custom-rate]'))
      if(option.value!==value)option.remove();
    if(![...this.#ui.rate.options].some(option=>option.value===value)){
      const option=document.createElement('option');
      option.value=value;option.textContent=value+'×';option.dataset.customRate='true';
      this.#ui.rate.append(option);
    }
    this.#ui.rate.value=value;
  }
  #updateClock(){
    const t=this.currentTime;const ms=this.#duration?(t===this.#duration?this.#duration:t%this.#duration):0;
    // Input already seeks and pauses; keyboard focus alone must not freeze the thumb.
    this.#ui.range.value=String(ms/1000);
    this.#ui.output.textContent=`${(ms/1000).toFixed(1)} / ${(this.#duration/1000).toFixed(1)} s`;
    this.#ui.range.setAttribute('aria-valuetext',this.#ui.output.textContent);
  }
  #setState(state){
    this.#ui.status.textContent=this.#words[state]||state;
    if(this.dataset.sceneState===state)return;
    this.dataset.sceneState=state;
    this.dispatchEvent(new CustomEvent('scene-state',{bubbles:true,composed:true,detail:{state,currentTime:this.currentTime}}));
  }
  #localize(){
    const explicit=normalizeSelectedLanguage(this.getAttribute('lang'));
    this.#words=WORDS[explicit||readSelectedLanguage(this.ownerDocument)];
    this.#ui.restart.textContent=this.#words.restart;this.#ui.source.textContent=this.#words.source;
    this.#root.querySelector('.rate span').textContent=this.#words.speed;
    this.#ui.rate.setAttribute('aria-label',this.#words.speed);this.#ui.range.setAttribute('aria-label',this.#words.progress);
    this.#ui.hint.textContent=this.#words.hint;this.#ui.scroll.setAttribute('aria-label',this.getAttribute('aria-label')||'SVG diagram');
    const controls=this.hasAttribute('controls');
    if(controls)this.#ui.scroll.setAttribute('aria-keyshortcuts','Space R Home End');
    else this.#ui.scroll.removeAttribute('aria-keyshortcuts');
    this.#ui.playback.hidden=this.#ui.restart.hidden=this.#root.querySelector('.rate').hidden=this.#ui.timeline.hidden=!controls;
    this.#ui.view.textContent=this.getAttribute('fit')==='detail'?this.#words.fit:this.#words.detail;
    this.#ui.status.textContent=this.#words[this.dataset.sceneState]||this.#words.loading;
  }
  #admit(svg,baseUrl){
    const forbidden=new Set(['script','foreignobject','iframe','object','embed']);
    for(const el of [svg,...svg.querySelectorAll('*')]){
      if(forbidden.has(el.localName.toLowerCase()))throw new Error('Active SVG content rejected');
      for(const attr of el.attributes){
        const name=attr.name.toLowerCase();if(name.startsWith('on'))throw new Error('SVG event handler rejected');
        if(name==='href'||name==='xlink:href'){
          const value=attr.value.trim();if(value&&!value.startsWith('#')&&!value.startsWith('data:image/')){
            if(new URL(value,baseUrl).origin!==location.origin)throw new Error('External SVG reference rejected');
          }
        }
      }
    }
  }
}
if(!customElements.get('lri-motion-scene'))customElements.define('lri-motion-scene',LriMotionScene);
