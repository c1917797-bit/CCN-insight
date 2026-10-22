/* LRI motion player v2. SVG content is same-origin, validated, and isolated in Shadow DOM.
 * It never embeds object/iframe, modifies response security headers, or executes SVG script.
 */
const STYLE_URL = new URL('./insight-executive.css?v=lri-content-contract-v2-mobile-density&mhs-motion=v2', import.meta.url).href;
const SVG_NS = 'http://www.w3.org/2000/svg';
const ALLOWED = new Set(['svg','title','desc','defs','style','marker','path','rect','g','text','tspan','circle','line','ellipse','polygon','polyline','linearGradient','radialGradient','stop','clipPath','mask','filter','feDropShadow']);
const WORDS = {
  zh: {play:'播放',pause:'暂停',restart:'重播',fit:'查看全图',detail:'清晰模式',source:'打开 SVG',speed:'播放速度',seek:'动画进度',loading:'正在加载动态图',ready:'可交互示意图 · 非实测',reduced:'已按系统偏好停止动画',error:'交互图加载失败，保留图片与原图入口',scroll:'← 左右滑动看细节，或点击“查看全图” →'},
  en: {play:'Play',pause:'Pause',restart:'Replay',fit:'Fit overview',detail:'Readable detail',source:'Open SVG',speed:'Playback speed',seek:'Animation position',loading:'Loading diagram',ready:'Interactive illustration · not a measurement',reduced:'Motion disabled by system preference',error:'Interactive view unavailable; image and source remain available',scroll:'← Scroll for detail or choose Fit overview →'}
};
function validateSvg(source) {
  const doc = new DOMParser().parseFromString(source, 'image/svg+xml');
  const svg = doc.documentElement;
  if (doc.querySelector('parsererror') || svg.namespaceURI !== SVG_NS || svg.localName !== 'svg' || svg.getAttribute('data-motion-contract') !== 'lri-mhs-motion-v2') throw new Error('SVG contract mismatch');
  for (const el of [svg, ...svg.querySelectorAll('*')]) {
    if (el.namespaceURI !== SVG_NS || !ALLOWED.has(el.localName)) throw new Error('Unapproved SVG element');
    for (const a of el.attributes) {
      if (/^on/i.test(a.name) || a.name === 'style' || ((a.localName === 'href') && !/^#[\w-]+$/.test(a.value))) throw new Error('Unapproved SVG attribute');
      if (/url\s*\(/i.test(a.value) && !/^url\(#[\w-]+\)$/.test(a.value)) throw new Error('External SVG resource');
    }
  }
  for (const style of svg.querySelectorAll('style')) {
    const css = style.textContent;
    if (/@import|\\|expression\s*\(|javascript:/i.test(css)) throw new Error('Unapproved SVG CSS');
    for (const m of css.matchAll(/url\s*\(([^)]*)\)/gi)) if (!/^#[\w-]+$/.test(m[1])) throw new Error('External CSS resource');
  }
  return svg;
}
class LriMotion extends HTMLElement {
  connectedCallback() {
    if (this._connected) return;
    this._connected = true;
    this._abort = new AbortController();
    this._visible = false; this._paused = false; this._animations = [];
    this._reduced = matchMedia('(prefers-reduced-motion: reduce)');
    this._lang = (document.documentElement.lang || 'zh').startsWith('en') ? 'en' : 'zh';
    const w = this._words = WORDS[this._lang];
    const root = this.shadowRoot || this.attachShadow({mode:'open'});
    root.innerHTML = `<link rel="stylesheet" href="${STYLE_URL}"><section class="lri-motion-player"><div class="lri-motion-toolbar"><button type="button" data-action="play" disabled></button><button type="button" data-action="restart" disabled></button><label class="lri-motion-speed"><span></span><select><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option></select></label><button type="button" data-action="fit"></button><a class="lri-motion-source" target="_blank" rel="noopener"></a></div><p class="lri-motion-status" role="status"></p><div class="lri-motion-viewport" tabindex="0"><div class="lri-motion-canvas"></div><slot></slot></div><div class="lri-motion-timeline"><input type="range" min="0" max="12" step="0.1" value="0" disabled><output>0.0 / 12 s</output></div><p class="lri-motion-hint"></p></section>`;
    this._ui = Object.fromEntries(['play','restart','fit'].map(k=>[k,root.querySelector(`[data-action="${k}"]`)]));
    this._status=root.querySelector('[role="status"]'); this._viewport=root.querySelector('.lri-motion-viewport');
    this._canvas=root.querySelector('.lri-motion-canvas'); this._slider=root.querySelector('input');
    this._clock=root.querySelector('output'); this._select=root.querySelector('select');
    this._status.textContent=w.loading; this._ui.play.textContent=w.pause;
    this._ui.restart.textContent=w.restart; this._ui.fit.textContent=w.fit;
    root.querySelector('.lri-motion-speed span').textContent=w.speed;
    this._select.setAttribute('aria-label',w.speed); this._slider.setAttribute('aria-label',w.seek);
    this._viewport.setAttribute('aria-label',this.getAttribute('label')||'SVG diagram');
    root.querySelector('.lri-motion-hint').textContent=w.scroll;
    const url=new URL(this.getAttribute('src')||'',document.baseURI);
    const link=root.querySelector('.lri-motion-source'); link.textContent=w.source;
    if(url.origin!==location.origin || !url.pathname.endsWith('.svg')) {this._status.textContent=w.error;this.dataset.motionState='error';return;}
    link.href=url.href;
    const on=(el,type,fn)=>el.addEventListener(type,fn,{signal:this._abort.signal});
    on(this._ui.play,'click',()=>{this._paused=!this._paused;this._sync();});
    on(this._ui.restart,'click',()=>{this.seek(0);this._paused=false;this._sync();});
    on(this._ui.fit,'click',()=>{const fit=this._viewport.classList.toggle('is-fit');this._ui.fit.textContent=fit?w.detail:w.fit;this._ui.fit.setAttribute('aria-pressed',String(fit));});
    on(this._select,'change',()=>{for(const a of this._animations)a.updatePlaybackRate(Number(this._select.value));});
    on(this._slider,'input',()=>{this._paused=true;this.seek(Number(this._slider.value));this._sync();});
    on(document,'visibilitychange',()=>this._sync());
    on(this._reduced,'change',()=>requestAnimationFrame(()=>{this._collect();this._sync();}));
    on(root.querySelector('link'),'load',()=>requestAnimationFrame(()=>{this._collect();this._sync();}));
    this._observer=new IntersectionObserver(entries=>{
      this._visible=entries[0].isIntersecting;
      if(this._visible)requestAnimationFrame(()=>{this._collect();this._sync();});
      else this._sync();
    },{rootMargin:'80px 0px'});
    this._observer.observe(this);
    this._timer=setInterval(()=>this._updateClock(),250);
    this._load(url);
  }
  async _load(url) {
    try {
      const response=await fetch(url,{credentials:'same-origin',signal:this._abort.signal});
      if(!response.ok)throw new Error(`SVG HTTP ${response.status}`);
      const source=await response.text();
      const svg=validateSvg(source);
      if(!this._connected)return;
      this._svg=document.importNode(svg,true); this._canvas.replaceChildren(this._svg);
      this.shadowRoot.querySelector('slot').hidden=true;
      this._duration=Number(this._svg.dataset.cycle)||12;
      this._slider.max=String(this._duration);
      await new Promise(requestAnimationFrame);
      this._collect();this.seek(0);this._sync();this.dataset.motionLoaded='true';
    } catch(error) {
      if(error.name==='AbortError')return;
      this._status.textContent=this._words.error;this.dataset.motionState='error';
      this.dispatchEvent(new CustomEvent('lri-motion-error',{detail:{message:error.message}}));
    }
  }
  _collect(){
    this._animations=this._svg?.getAnimations({subtree:true})||[];
    this._master=this._animations.find(a=>a.effect.getTiming().duration===this._duration*1000)||this._animations[0];
    const disabled=this._reduced.matches||!this._animations.length;
    this._ui.play.disabled=disabled;this._ui.restart.disabled=disabled;this._slider.disabled=disabled;this._select.disabled=disabled;
  }
  _sync(){
    if(!this._svg)return;
    const running=!this._paused&&this._visible&&!document.hidden&&!this._reduced.matches;
    for(const a of this._animations)running?a.play():a.pause();
    this._ui.play.textContent=this._paused?this._words.play:this._words.pause;
    this._ui.play.setAttribute('aria-pressed',String(!this._paused));
    this._status.textContent=this._reduced.matches?this._words.reduced:this._words.ready;
    this.dataset.motionState=this._reduced.matches?'reduced':running?'playing':'paused';
    this._updateClock();
  }
  seek(seconds){
    const value=Math.min(this._duration||12,Math.max(0,seconds))*1000;
    for(const a of this._animations)a.currentTime=value;
    this._updateClock();
  }
  _updateClock(){
    if(!this._clock||!this._duration)return;
    const seconds=((this._master?.currentTime||0)/1000)%this._duration;
    if(this.shadowRoot.activeElement!==this._slider)this._slider.value=String(seconds);
    this._clock.textContent=`${seconds.toFixed(1)} / ${this._duration} s`;
  }
  disconnectedCallback(){
    this._connected=false;this._abort?.abort();this._observer?.disconnect();clearInterval(this._timer);
    for(const a of this._animations||[])a.pause();
  }
}
if(!customElements.get('lri-motion'))customElements.define('lri-motion',LriMotion);

