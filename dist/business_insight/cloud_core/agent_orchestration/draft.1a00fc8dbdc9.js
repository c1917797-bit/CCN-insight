(() => {
  // A citation can point inside a collapsed evidence block; expose its ancestors.
  function revealAnchoredDetails() {
    if (!/^#[a-zA-Z][\w-]*$/.test(location.hash)) return;
    const target = document.querySelector(location.hash);
    let parent = target && target.parentElement;
    let opened = false;
    while (parent) {
      if (parent.tagName === 'DETAILS' && !parent.open) { parent.open = true; opened = true; }
      parent = parent.parentElement;
    }
    if (opened && target) target.scrollIntoView({block:'start', behavior:'auto'});
  }
  window.addEventListener('hashchange', revealAnchoredDetails);
  revealAnchoredDetails();
  function revealScopeIndex() {
    const hash = location.hash;
    const scope = document.querySelector('#scope-index');
    const isScope = /^#(?:scope-index|decision-scope|decision-(?:admission|ordering|dispatch|allocation)|scheduling-(?:directions|roots|feedback|dimensions)|root-[a-z-]+)$/.test(hash);
    if (scope && isScope) {
      const wasClosed = !scope.open;
      scope.open = true;
      const target = document.querySelector(hash);
      if (target && target.tagName === 'DETAILS') target.open = true;
      if (wasClosed && target) target.scrollIntoView({block: 'start', behavior: 'auto'});
    }
  }
  window.addEventListener('hashchange', revealScopeIndex);
  revealScopeIndex();
  const demoDisclosure = document.querySelector('#demo-section');
  function revealDemo() {
    const hash = location.hash;
    if (demoDisclosure && (hash === '#agent-demo' || hash === '#demo-coverage' || /^#point-[a-z-]+$/.test(hash))) {
      const wasClosed = !demoDisclosure.open;
      demoDisclosure.open = true;
      const target = document.querySelector(hash);
      if (wasClosed && target) target.scrollIntoView({block: 'start', behavior: 'auto'});
    }
  }
  window.addEventListener('hashchange', revealDemo);
  revealDemo();

  function revealPublication() {
    if (!/^#publication-[a-z0-9-]+$/.test(location.hash)) return;
    const entry = document.querySelector(location.hash);
    const details = entry && entry.querySelector('.literature-details');
    if (details) details.open = true;
  }
  window.addEventListener('hashchange', revealPublication);
  revealPublication();
  function mark() {
    const hash = location.hash || '#map';
    const isTopic = document.body && document.body.dataset.pageKind === 'topic';
    let section = /^#[a-zA-Z][\w-]*$/.test(hash) ? document.querySelector(hash) : null;
    while (section && section.tagName !== 'SECTION') section = section.parentElement;
    const localKey = section && section.id ? '#' + section.id : hash;
    const key = hash.startsWith('#analysis-') ? '#analysis' : hash.startsWith('#channel-') || hash.startsWith('#sources-') ? '#sources' : hash.startsWith('#publication-') || hash.startsWith('#updates-') ? '#updates' : hash.startsWith('#point-') || hash.startsWith('#root-') || hash.startsWith('#decision-') || hash.startsWith('#research-') || hash === '#scope-index' || ['#runtime-loop','#coffee-task','#north-star','#scheduling-essence','#research-directions','#demo-coverage','#agent-demo','#scheduling-roots','#scheduling-directions','#scheduling-decisions','#scheduling-feedback','#scheduling-dimensions'].includes(hash) ? '#map' : hash;
    document.querySelectorAll('.rail nav a').forEach(a => {
      const current = a.dataset.navScope === 'primary' ? (isTopic ? '#map' : key) : (isTopic ? localKey : key);
      if (a.hash === current || (!isTopic && a.hash === hash)) a.setAttribute('aria-current', 'location');
      else a.removeAttribute('aria-current');
    });
  }
  window.addEventListener('hashchange', mark);
  mark();
  document.querySelectorAll('[data-coffee-policy]').forEach(button => {
    button.addEventListener('click', () => {
      const policy = button.dataset.coffeePolicy;
      document.querySelectorAll('[data-coffee-policy]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
      document.querySelectorAll('[data-coffee-plan]').forEach(plan => { plan.hidden = plan.dataset.coffeePlan !== policy; });
    });
  });
  // The figure and all its descriptions are rendered before JS runs.
  const figure = document.querySelector('.agent-map');
  if (!figure) return;
  const points = [...document.querySelectorAll('[data-point-detail]')];
  const selectors = [...document.querySelectorAll('[data-point-select]')];
  function selectPoint(id, scroll) {
    const point = points.find(p => p.dataset.pointDetail === id);
    if (!point) return;
    points.forEach(p => { p.open = p === point; });
    selectors.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.pointSelect === id)));
    figure.querySelectorAll('[data-map-point]').forEach(n => {
      n.classList.toggle('point-selected', n.dataset.mapPoint === id);
    });
    if (scroll) point.scrollIntoView({block: 'start', behavior: 'auto'});
  }
  selectors.forEach(b => b.addEventListener('click', () => selectPoint(b.dataset.pointSelect, true)));
  points.forEach(point => point.addEventListener('toggle', () => {
    // Native summary clicks must keep the selector's accessible state truthful.
    selectors.forEach(b => {
      const panel = points.find(p => p.dataset.pointDetail === b.dataset.pointSelect);
      b.setAttribute('aria-pressed', String(panel.open));
    });
    figure.querySelectorAll('[data-map-point]').forEach(n => {
      const panel = points.find(p => p.dataset.pointDetail === n.dataset.mapPoint);
      n.classList.toggle('point-selected', panel.open);
    });
  }));
  figure.querySelectorAll('[data-map-point]').forEach(n => {
    n.addEventListener('click', () => selectPoint(n.dataset.mapPoint, false));
  });
  function pointFromHash() {
    if (location.hash.startsWith('#point-')) selectPoint(location.hash.slice(7), false);
  }
  window.addEventListener('hashchange', pointFromHash);
  selectPoint('workflow', false);
  pointFromHash();

  const steps = [...document.querySelectorAll('[data-map-step]')];
  const playButton = document.querySelector('[data-map-action="play"]');
  const previous = document.querySelector('[data-map-action="previous"]');
  const next = document.querySelector('[data-map-action="next"]');
  const message = document.querySelector('[data-map-message]');
  const progress = document.querySelector('[data-map-progress]');
  const timeline = [...document.querySelectorAll('[data-step-select]')];
  const zoom = document.querySelector('[data-map-action="zoom"]');
  const reducedMotion = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)').matches : false;
  const tokens = [...figure.querySelectorAll('[data-flow-token]')];
  const routes = [...figure.querySelectorAll('[data-map-edge]')];
  const svgStatus = figure.querySelector('[data-map-svg-status]');
  const phaseBits = [...figure.querySelectorAll('[data-phase-bit]')];
  const initialMessage = message.textContent;
  let step = -1;
  let timer = null;
  let animation = null;
  let activePackets = [];
  function stopMotion() {
    if (animation !== null) window.cancelAnimationFrame(animation);
    animation = null;
  }
  function placePacket(packet, fraction) {
    const p = packet.route.getPointAtLength(packet.length * fraction);
    packet.token.setAttribute('transform', `translate(${p.x} ${p.y})`);
    packet.trails.forEach(trail => {
      const behind = packet.route.getPointAtLength(Math.max(0, packet.length*fraction - Number(trail.dataset.packetTrail)*10));
      trail.setAttribute('cx',String(behind.x-p.x));
      trail.setAttribute('cy',String(behind.y-p.y));
    });
  }
  function startMotion() {
    stopMotion();
    if (reducedMotion || !activePackets.length || !window.requestAnimationFrame) return;
    let started = null;
    function frame(time) {
      if (timer === null || document.hidden) { animation = null; return; }
      if (started === null) started = time;
      activePackets.forEach((packet,i) => placePacket(packet, ((time-started+i*180)%1800)/1800));
      animation = window.requestAnimationFrame(frame);
    }
    animation = window.requestAnimationFrame(frame);
  }
  function pause() {
    if (timer !== null) window.clearInterval(timer);
    timer = null;
    stopMotion();
    figure.classList.toggle('is-playing', false);
    playButton.textContent = '播放演示';
    playButton.setAttribute('aria-pressed', 'false');
  }
  function show(index) {
    stopMotion();
    step = Math.max(-1, Math.min(index, steps.length - 1));
    const current = steps[step];
    const nodes = current ? current.dataset.nodes.split(' ') : [];
    const edges = current ? current.dataset.edges.split(' ') : [];
    figure.querySelectorAll('[data-map-node]').forEach(n => n.classList.toggle('flow-active', nodes.includes(n.dataset.mapNode)));
    figure.querySelectorAll('[data-map-edge]').forEach(n => n.classList.toggle('flow-active', edges.includes(n.dataset.mapEdge)));
    activePackets = [];
    tokens.forEach(token => {
      const route = routes.find(p => p.dataset.mapEdge === token.dataset.flowToken);
      const active = edges.includes(token.dataset.flowToken) && route && typeof route.getTotalLength === 'function';
      token.classList.toggle('packet-active', Boolean(active));
      if (active) {
        const packet = {token, route, length:route.getTotalLength(), trails:token.querySelectorAll ? [...token.querySelectorAll('[data-packet-trail]')] : []};
        placePacket(packet, .08);
        activePackets.push(packet);
      }
    });
    timeline.forEach(b => b.setAttribute('aria-pressed',String(Number(b.dataset.stepSelect)===step)));
    if (svgStatus) svgStatus.textContent = current ? current.querySelector('strong').textContent.slice(3) : '等待播放';
    phaseBits.forEach(bit => {
      bit.classList.toggle('phase-active', Number(bit.dataset.phaseBit)===step);
      bit.classList.toggle('phase-done', Number(bit.dataset.phaseBit)<step);
    });
    steps.forEach((s, i) => s.classList.toggle('step-current', i === step));
    message.textContent = current ? current.querySelector('p').textContent : initialMessage;
    progress.textContent = current ? `${step + 1} / ${steps.length} · ${current.querySelector('strong').textContent.slice(3)}` : '系统结构 · 尚未播放';
    previous.disabled = step < 0;
    next.disabled = step === steps.length - 1;
    if (timer !== null) startMotion();
  }
  playButton.addEventListener('click', () => {
    if (timer !== null) { pause(); return; }
    if (step === steps.length - 1) show(-1);
    show(step + 1);
    playButton.textContent = '暂停演示';
    playButton.setAttribute('aria-pressed', 'true');
    figure.classList.toggle('is-playing', true);
    timer = window.setInterval(() => {
      if (step === steps.length - 1) { pause(); return; }
      show(step + 1);
    }, 5000);
    startMotion();
  });
  previous.addEventListener('click', () => { pause(); show(step - 1); });
  next.addEventListener('click', () => { pause(); show(step + 1); });
  document.querySelector('[data-map-action="reset"]').addEventListener('click', () => { pause(); show(-1); });
  timeline.forEach(b => b.addEventListener('click', () => { pause(); show(Number(b.dataset.stepSelect)); }));
  if (zoom) zoom.addEventListener('click', () => {
    const expanded = zoom.getAttribute('aria-pressed') !== 'true';
    figure.classList.toggle('map-zoomed', expanded);
    zoom.setAttribute('aria-pressed',String(expanded));
    zoom.textContent = expanded ? '适配宽度' : '放大图';
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
  window.addEventListener('pagehide', pause);
  if (demoDisclosure) demoDisclosure.addEventListener('toggle', () => {
    if (!demoDisclosure.open) pause();
  });
  // Never autoplay. Manual steps also work when reduced motion is requested.
  show(-1);
})();
/* Source directory controls: progressive enhancement of the complete HTML registry. */
(() => {
  const root=document.querySelector('[data-source-directory]');
  if(!root)return;
  const one=s=>root.querySelector(s), all=s=>[...root.querySelectorAll(s)];
  const cards=all('.source-table-row'),tabs=all('[data-source-tab]');
  const category=one('#channel-category'),priority=one('#channel-priority'),query=one('#channel-query'),ecosystem=one('#channel-ecosystem');
  const offsets={news:0,industry:0,academic:0};
  let domain='news';
  function reset(){for(const k of Object.keys(offsets))offsets[k]=0;}
  function inDomain(){return cards.filter(c=>c.dataset.sourceDomain===domain);}
  function matches(c){return (priority.value!=='important'||c.dataset.sourcePriority==='core')&&(!category.value||category.value===c.dataset.sourceCategory)&&(domain!=='industry'||!ecosystem.value||ecosystem.value===c.dataset.sourceEcosystem)&&c.dataset.sourceSearch.toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase());}
  function categories(){
    const previous=category.value;
    category.replaceChildren();
    const option=(value,label)=>{const o=document.createElement('option');o.value=value;o.textContent=label;category.append(o);};
    option('','全部子类');
    const names=[...new Set(inDomain().map(c=>c.dataset.sourceCategory))];
    for(const name of names)option(name,name+' · '+inDomain().filter(c=>c.dataset.sourceCategory===name).length);
    category.value=names.includes(previous)?previous:'';
  }
  function render(){
    const rows=inDomain().filter(matches),size=20;
    offsets[domain]=Math.min(offsets[domain],Math.max(0,Math.floor((rows.length-1)/size)*size));
    tabs.forEach(t=>{const selected=t.dataset.sourceTab===domain;t.setAttribute('aria-selected',String(selected));t.tabIndex=selected?0:-1;});
    one('#channel-cards').setAttribute('aria-labelledby','source-tab-'+domain);
    one('#channel-ecosystem-field').hidden=domain!=='industry';
    all('[data-source-panel]').forEach(p=>p.hidden=p.dataset.sourcePanel!==domain);
    cards.forEach(c=>c.hidden=true);
    rows.slice(offsets[domain],offsets[domain]+size).forEach(c=>c.hidden=false);
    all('[data-source-subcategory]').forEach(g=>{
      const count=[...g.querySelectorAll('.source-table-row')].filter(c=>!c.hidden).length;
      g.hidden=count===0;
      g.querySelector('[data-source-group-count]').textContent=count+' 个信息源';
    });
    all('[data-source-group-link]').forEach(a=>{if(a.dataset.sourceGroupLink===category.value)a.setAttribute('aria-current','true');else a.removeAttribute('aria-current');});
    one('#channel-empty').hidden=rows.length>0;
    one('#channel-pagination').hidden=rows.length<=size;
    one('#channel-range').textContent=`${rows.length?offsets[domain]+1:0}–${Math.min(offsets[domain]+size,rows.length)} / ${rows.length}`;
    one('#channel-prev').disabled=offsets[domain]===0;
    one('#channel-next').disabled=offsets[domain]+size>=rows.length;
    const label=tabs.find(t=>t.dataset.sourceTab===domain).textContent;
    one('#channel-status').textContent=`${label} · ${rows.length} 个信源 · 人工整理，具体进展见本期动态`;
  }
  function choose(key){domain=key;category.value='';ecosystem.value='';query.value='';reset();categories();render();}
  tabs.forEach((tab,index)=>{
    tab.addEventListener('click',()=>choose(tab.dataset.sourceTab));
    tab.addEventListener('keydown',event=>{
      let i;if(event.key==='ArrowRight')i=(index+1)%tabs.length;else if(event.key==='ArrowLeft')i=(index+tabs.length-1)%tabs.length;else if(event.key==='Home')i=0;else if(event.key==='End')i=tabs.length-1;else return;
      event.preventDefault();choose(tabs[i].dataset.sourceTab);tabs[i].focus();
    });
  });
  for(const control of [category,priority,query,ecosystem])control.addEventListener(control===query?'input':'change',()=>{reset();render();});
  for(const direction of ['prev','next'])one('#channel-'+direction).addEventListener('click',()=>{offsets[domain]+=direction==='prev'?-20:20;render();one('#channel-status').scrollIntoView({block:'nearest'});});
  function deepLink(){
    const hash=location.hash,target=cards.find(c=>'#'+c.id===hash);
    if(target){
      if(target.dataset.sourcePriority!=='core')priority.value='all';
      choose(target.dataset.sourceDomain);
      offsets[domain]=Math.floor(inDomain().filter(matches).indexOf(target)/20)*20;
      render();target.scrollIntoView({block:'start'});return;
    }
    const layer=all('[data-source-subcategory]').find(g=>'#'+g.id===hash||g.dataset.sourceLegacyAnchor&&'#'+g.dataset.sourceLegacyAnchor===hash);
    if(layer){
      choose(layer.closest('[data-source-panel]').dataset.sourcePanel);
      category.value=layer.dataset.sourceSubcategory;
      if(!inDomain().some(matches))priority.value='all';
      render();layer.scrollIntoView({block:'start'});return;
    }
    const legacy=hash==='#industry-sources-ascend'?'ascend':hash==='#industry-sources-general'?'general':null;
    if(legacy){choose('industry');ecosystem.value=legacy;render();one('#sources-industry').scrollIntoView({block:'start'});return;}
    const tab=tabs.find(t=>hash==='#sources-'+t.dataset.sourceTab);
    if(tab){choose(tab.dataset.sourceTab);one('#sources-'+domain).scrollIntoView({block:'start'});}
  }
  categories();render();deepLink();window.addEventListener('hashchange',deepLink);
})();

/* Deterministic teaching simulator. Ticks are illustrative, never benchmarks. */
(function (host) {
  const definitions = [
    {id:'menu',code:'C01.1',name:'查菜单',deps:[],service:'tool',duration:2,why:'门店已确定，可直接查询菜单。'},
    {id:'offer',code:'C01.2',name:'查优惠',deps:[],service:'tool',duration:4,why:'本例优惠查询不依赖菜单，可与菜单并行。'},
    {id:'compare',code:'C01.3',name:'比较方案',deps:['menu','offer'],service:'model',duration:3,why:'汇合点：必须拿到菜单和优惠两份结果。'},
    {id:'authorize',code:'C01.4',name:'确认授权',deps:['compare'],service:'human',duration:0,why:'等待用户同意方案；等待期间不占执行名额。'},
    {id:'order',code:'C01.5',name:'提交订单',deps:['authorize'],service:'tool',duration:2,why:'只有授权已完成，才能发起购买操作。'},
    {id:'verify',code:'C01.6',name:'核验订单',deps:['order'],service:'tool',duration:2,why:'读取订单状态，核对商品、金额及订单标识。'},
    {id:'receipt',code:'C01.7',name:'返回回执',deps:['verify'],service:'local',duration:1,why:'核验通过后，把回执交回原任务 C01。'}
  ];
  class Simulation {
    constructor(slots=2,slow=false){this.slots=slots;this.slow=slow;this.reset();}
    reset(){this.time=0;this.phase='incoming';this.nodes=definitions.map(d=>({...d,deps:[...d.deps],state:'unplanned',elapsed:0,duration:d.duration+(d.id==='offer'&&this.slow?4:0)}));this.events=[];this.record('收到委托 C01：帮我点一杯咖啡。');}
    record(text){this.events.push({time:this.time,text});}
    get done(){return this.phase==='done';}
    get authorizationRequired(){return this.nodes.find(n=>n.id==='authorize').state==='waiting';}
    get running(){return this.nodes.filter(n=>n.state==='running');}
    refresh(){for(const n of this.nodes){if(n.state!=='blocked')continue;if(n.deps.every(id=>this.nodes.find(p=>p.id===id).state==='success')){n.state=n.service==='human'?'waiting':'ready';n.readyAt=this.time;this.record(n.code+' '+n.name+(n.state==='waiting'?'：等待用户确认，不占执行名额。':'：依赖已满足，进入就绪集合。'));}}}
    tick(){
      if(this.done||this.authorizationRequired)return false;
      this.time++;
      if(this.phase==='incoming'){this.phase='assigned';this.record('S1：委托交给能力与权限匹配的 Agent A（本例固定选择）。');return true;}
      if(this.phase==='assigned'){this.phase='planned';this.nodes.forEach(n=>n.state='blocked');this.record('Agent 将 C01 拆成七个步骤，建立依赖图；规划给出调度输入。');this.refresh();return true;}
      this.phase='running';
      for(const n of this.running){n.elapsed++;if(n.elapsed>=n.duration){n.state='success';this.record(n.code+' '+n.name+'完成，结果写回 C01。');}}
      this.refresh();
      let free=this.slots-this.running.length;
      for(const n of [...this.nodes].sort((a,b)=>(a.readyAt??Infinity)-(b.readyAt??Infinity))){if(n.state==='ready'&&free>0){n.state='running';n.started=this.time;free--;this.record('S2：启动 '+n.code+' '+n.name+'，占用一个执行名额。');}}
      if(this.nodes.every(n=>n.state==='success')){this.phase='done';this.record('C01 完成：订单回执已核验；不代表咖啡已经送达。');}
      return true;
    }
    authorize(){if(!this.authorizationRequired)return false;const n=this.nodes.find(n=>n.id==='authorize');n.state='success';this.record('演示用户确认方案；下单获授权。');this.refresh();return true;}
  }
  const api={Simulation,definitions};if(typeof module!=='undefined'&&module.exports)module.exports=api;else host.CoffeeSimulation=api;
})(globalThis);

/* State-driven controls for the coffee DAG. No external requests or purchases. */
(() => {
 const root=document.querySelector('[data-coffee-scene]');if(!root)return;
 const q=s=>root.querySelector(s), all=s=>[...root.querySelectorAll(s)];
 const labels={unplanned:'尚未生成',blocked:'等待依赖',ready:'就绪待排程',running:'执行中',waiting:'等待用户授权',success:'已完成'};
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 let sim=new CoffeeSimulation.Simulation(),timer=null,selected=null,selectedGate=null;
 const text=(s,t)=>{q(s).textContent=t;};
 function render(){
   for(const n of sim.nodes){const el=q(`[data-dag-node="${n.id}"]`);el.dataset.state=n.state;el.setAttribute('aria-label',`${n.code} ${n.name}，${labels[n.state]}，查看步骤说明`);el.setAttribute('aria-pressed',String(selected===n.id));text(`[data-node-state="${n.id}"]`,labels[n.state]);q(`[data-node-progress="${n.id}"]`).setAttribute('width',n.state==='success'?126:n.state==='running'?Math.max(8,126*n.elapsed/n.duration):0);}
   all('[data-dag-from]').forEach(e=>{const done=sim.nodes.find(n=>n.id===e.dataset.dagFrom).state==='success';e.classList.toggle('is-satisfied',done);e.classList.toggle('is-active',done&&sim.nodes.find(n=>n.id===e.dataset.dagTo).state==='running');});
   all('[data-origin]').forEach(e=>e.classList.toggle('is-reached',e.dataset.origin==='incoming'||(e.dataset.origin==='assigned'&&sim.phase!=='incoming')||(e.dataset.origin==='planned'&&!['incoming','assigned'].includes(sim.phase))));
   const ready=sim.nodes.filter(n=>n.state==='ready');
   const modelWork=sim.running.find(n=>n.service==='model');
   const currentGate=sim.phase==='assigned'?'S1':ready.length?'S2':modelWork?['M1','S3','S4'][Math.min(modelWork.elapsed,2)]:sim.running.some(n=>n.service==='tool')?'S5':null;
   all('[data-card-link]').forEach(e=>e.classList.toggle('is-active',!!modelWork&&modelWork.elapsed===2&&e.dataset.cardLink==='A'));
   all('[data-model-stage]').forEach(e=>e.classList.toggle('is-active',!!modelWork&&e.dataset.modelStage===['semantic','replica','batch'][Math.min(modelWork.elapsed,2)]));
   const shownGate=selectedGate||currentGate||'S2';
   all('[data-scheduling-gate]').forEach(e=>{e.classList.toggle('is-current',e.dataset.schedulingGate===currentGate);e.classList.toggle('is-selected',e.dataset.schedulingGate===selectedGate);e.setAttribute('aria-pressed',String(e.dataset.schedulingGate===shownGate));});
   all('[data-decision-select]').forEach(e=>e.setAttribute('aria-pressed',String(e.dataset.decisionSelect===shownGate)));
   all('[data-decision-panel]').forEach(e=>e.hidden=e.dataset.decisionPanel!==shownGate);

   text('[data-global-queue]',`${sim.running.length} / ${sim.slots} 个名额占用 · ${ready.length} 步就绪待选`);
   text('[data-global-running]',sim.running.length?'执行：'+sim.running.map(n=>n.code+' '+n.name).join(' / '):sim.authorizationRequired?'等待用户授权 · 不占执行名额':sim.done?'C01 已核验完成':'等待可执行步骤');
   all('[data-call-node]').forEach(e=>e.classList.toggle('is-active',sim.nodes.find(n=>n.id===e.dataset.callNode).state==='running'));
   all('[data-assignment-flow]').forEach(e=>e.classList.toggle('is-active',sim.phase==='assigned'));
   q('[data-agent-instance="A"]').classList.toggle('is-active',sim.phase!=='incoming');
   q('[data-final-return]').classList.toggle('is-active',sim.done);
   all('[data-resource]').forEach(e=>e.classList.toggle('is-active',e.dataset.resource==='model'?sim.running.some(n=>n.service==='model'):e.dataset.resource==='cpu'?sim.phase!=='incoming':e.dataset.resource==='network'?sim.running.some(n=>n.service==='tool'):false));
   text('[data-ready-list]',ready.length?'就绪集合：'+ready.map(n=>n.code+' '+n.name).join('、'):(sim.phase==='incoming'||sim.phase==='assigned'?'执行计划尚未生成。':'就绪集合：暂无可启动步骤。'));
   text('[data-slot-state]',`正在执行 ${sim.running.length} / ${sim.slots} · ${sim.running.map(n=>n.name).join('、')||'无占用'}（授权等待不占名额）`);
   let caption=sim.phase==='incoming'?'准备就绪：先把整项委托交给 Agent。':sim.phase==='assigned'?'Agent A 已接手 C01，下一步先形成执行计划。':sim.phase==='planned'?'计划已生成：两项查询已就绪，比较方案还在等输入。':sim.done?'C01 已完成：核验回执后返回用户，未模拟咖啡送达。':sim.authorizationRequired?'方案已生成：等待你模拟授权，下单尚未开始。':sim.nodes.find(n=>n.id==='menu').state==='success'&&sim.nodes.find(n=>n.id==='offer').state!=='success'?'菜单已返回，优惠还没回来：比较方案不能提前开始。':sim.running.length?'正在执行：'+sim.running.map(n=>n.name).join('、')+'；完成后才解锁后续步骤。':'已获得授权，下一个调度拍将安排提交订单。';
   text('[data-cs-caption]',caption);text('[data-cs-progress]',`演示时钟 T+${sim.time} · 完成 ${sim.nodes.filter(n=>n.state==='success').length} / 7 · 非实测时间`);
   q('[data-authorization]').hidden=!sim.authorizationRequired;
   q('[data-cs-action="next"]').disabled=sim.authorizationRequired||sim.done;
   q('[data-cs-action="play"]').disabled=sim.authorizationRequired;
   for(const service of ['tool','model']){
     const running=sim.running.filter(n=>n.service===service), active=running.length>0;
     q(`[data-service="${service}"]`).classList.toggle('is-active',active);
     q(`[data-service-flow="${service}"]`).classList.toggle('is-active',active&&running.some(n=>n.elapsed===0));
     q(`[data-response-flow="${service}"]`).classList.toggle('is-active',active&&running.some(n=>n.elapsed===n.duration-1));
     text(`[data-${service}-flow]`,active?running.map(n=>n.code).join(' / ')+' · '+(service==='model'?['语义路由：示例选模型 R','副本路由：示例选 R1','R1 排批次 → A0/A1 协同执行 → 返回方案'][Math.min(running[0].elapsed,2)]:running.some(n=>n.elapsed===0)?'发出请求 → 商家 API':running.some(n=>n.elapsed===n.duration-1)?'响应返回 → Agent C01':'等待商家接口响应'):'当前无在途请求');
   }
   if(selected){const n=sim.nodes.find(n=>n.id===selected);text('[data-inspector-code]',n.code+' · '+labels[n.state]);text('[data-inspector-title]',n.name);const missing=n.deps.filter(id=>sim.nodes.find(p=>p.id===id).state!=='success').map(id=>sim.nodes.find(p=>p.id===id).name);text('[data-inspector-body]',n.why+(missing.length?' 尚未完成的前置步骤：'+missing.join('、')+'。':'')+(n.state==='ready'?' 依赖已满足，等待 S2 分配执行名额。':''));}
   const log=q('[data-cs-log]');log.replaceChildren(...[...sim.events].reverse().map(e=>{const li=document.createElement('li');li.textContent=`T+${e.time} · ${e.text}`;return li;}));
   q('[data-cs-action="play"]').textContent=timer?'暂停演示':sim.done?'再看一遍':sim.time?'继续演示':'开始演示';q('[data-cs-action="play"]').setAttribute('aria-pressed',String(!!timer));
 }
 function stop(){if(timer)clearInterval(timer);timer=null;root.classList.remove('is-playing');}
 function advance(){sim.tick();if(sim.done||sim.authorizationRequired)stop();render();}
 function reset(){stop();sim=new CoffeeSimulation.Simulation(Number(q('[data-cs-slots]').value),q('[data-cs-slow]').checked);selected=null;selectedGate=null;text('[data-inspector-code]','C01 · 整项委托');text('[data-inspector-title]','运行时负责把选中的步骤真正执行');text('[data-inspector-body]','它读取输入、调用模型或工具、记录结果；不是另一个替用户点单的 Agent。');render();}
 q('[data-cs-action="play"]').addEventListener('click',()=>{if(timer){stop();render();return;}if(sim.done)reset();timer=setInterval(advance,1400);root.classList.add('is-playing');advance();});
 q('[data-cs-action="next"]').addEventListener('click',()=>{stop();advance();});
 q('[data-cs-action="reset"]').addEventListener('click',reset);
 q('[data-cs-action="authorize"]').addEventListener('click',()=>{if(!sim.authorize())return;timer=setInterval(advance,1400);root.classList.add('is-playing');advance();});
 q('[data-cs-slots]').addEventListener('change',reset);q('[data-cs-slow]').addEventListener('change',reset);
 all('[data-dag-node]').forEach(el=>{const select=()=>{selected=el.dataset.dagNode;render();};el.addEventListener('click',select);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}});});
 all('[data-scheduling-gate], [data-decision-select]').forEach(el=>{const select=()=>{selectedGate=el.dataset.schedulingGate||el.dataset.decisionSelect;render();};el.addEventListener('click',select);if(el.dataset.schedulingGate)el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}});});
 q('[data-cs-action="contention"]').addEventListener('click',()=>{q('[data-cs-slots]').value='1';reset();selectedGate='S2';for(let i=0;i<3;i++)sim.tick();render();if(q('.cs-console').classList.contains('is-expanded'))q('.cs-console').scrollTop=0;else q('.cs-viewport').scrollIntoView({block:'start'});});
 q('[data-cs-action="model-tour"]').addEventListener('click',()=>{reset();for(let i=0;i<20&&!sim.running.some(n=>n.service==='model');i++)sim.tick();render();if(q('.cs-console').classList.contains('is-expanded'))q('.cs-console').scrollTop=0;else q('.cs-viewport').scrollIntoView({block:'start'});});
 document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();render();}});reduced.addEventListener('change',()=>{if(reduced.matches){stop();render();}});
 if('IntersectionObserver' in window)new IntersectionObserver(entries=>{if(!entries[0].isIntersecting){stop();render();}},{threshold:0}).observe(q('.cs-console'));
 const consolePanel=q('.cs-console'), expand=q('[data-cs-action="expand"]'), zoom=q('[data-cs-action="zoom"]'), overview=q('[data-cs-action="overview"]');
 let expanded=false,zoomed=false,overviewMode=false;
 function expandView(value){expanded=value;consolePanel.classList.toggle('is-expanded',value);expand.textContent=value?'收起全景 ×':'展开全景 ↗';expand.setAttribute('aria-pressed',String(value));if(value)consolePanel.scrollTop=0;}
 expand.addEventListener('click',()=>expandView(!expanded));
 function syncView(){
  consolePanel.classList.toggle('is-zoomed',zoomed);consolePanel.classList.toggle('is-overview',overviewMode);
  zoom.textContent=zoomed?'恢复宽度':'放大细节';zoom.setAttribute('aria-pressed',String(zoomed));
  overview.textContent=overviewMode?'按宽度阅读':'查看全图';overview.setAttribute('aria-pressed',String(overviewMode));
  q('.cs-viewport').scrollLeft=0;
 }
 zoom.addEventListener('click',()=>{zoomed=!zoomed;overviewMode=false;syncView();});
 overview.addEventListener('click',()=>{overviewMode=!overviewMode;zoomed=false;syncView();});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&expanded)expandView(false);});
 render();
})();

/* A report view contains one primary chapter. Hash links remain shareable. */
(() => {
  if (document.body.dataset.pageKind !== 'index') return;
  const ids = ['sources', 'map', 'updates', 'analysis', 'archive'];
  const chapters = ids.map(id => document.getElementById(id));
  if (chapters.some(node => !node)) return; // Complete document remains readable.
  const nav = document.querySelector('.reading-flow');
  const mapNav = document.querySelector('[aria-label="技术地图阅读"]');
  let previous = '';
  function show(scroll) {
    let key = '';
    try { key = decodeURIComponent(location.hash.slice(1)); } catch (_) {}
    const target = key ? document.getElementById(key) : null;
    const chapter = chapters.find(node => node === target || node.contains(target));
    const selected = chapter ? chapter.id : (key === 'main-content' || key === 'report-top' ? previous || 'sources' : 'sources');
    chapters.forEach(node => { node.hidden = node.id !== selected; });
    document.body.dataset.reportView = selected;
    if (mapNav) { mapNav.hidden = selected !== 'map'; if (mapNav.previousElementSibling) mapNav.previousElementSibling.hidden = selected !== 'map'; }
    document.querySelectorAll('[data-nav-scope="primary"],.reading-flow>a').forEach(link => {
      const active = link.hash === '#' + selected;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
    });
    if (selected !== previous) document.dispatchEvent(new CustomEvent('reportviewchange', {detail: selected}));
    previous = selected;
    if (target) {
      if (target.tagName === 'DETAILS') target.open = true;
      for (let parent = target.parentElement; parent; parent = parent.parentElement) if (parent.tagName === 'DETAILS') parent.open = true;
      if (scroll) requestAnimationFrame(() => target.scrollIntoView({block:'start',behavior:'instant'}));
    }
  }
  document.body.classList.add('report-views-ready');
  show(!!location.hash);
  window.addEventListener('hashchange', () => show(true));
  document.addEventListener('click', event => {
    const link=event.target.closest('a[href]');
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const url = new URL(link.href, location.href);
    if (url.origin === location.origin && url.pathname === location.pathname && url.hash && url.hash === location.hash) show(true);
  });
})();

/* Filter evidence by its existing, explicit research-area relationships. */
(() => {
  const root=document.getElementById('updates'), filter=document.getElementById('update-area');
  if (!root || !filter) return;
  const items=[...root.querySelectorAll('.literature-entry')];
  function apply(){
    const area=filter.value;
    items.forEach(item=>{item.hidden=!!area&&!item.dataset.updateAreas.split(' ').includes(area);});
    const visible=items.filter(item=>!item.hidden), current=visible.filter(item=>item.dataset.updateCurrent==='true');
    root.querySelector('#update-filter-status').textContent=`本期 ${current.length} 项 · 累计 ${visible.length} 项（含历史和能力资料）`;
    root.querySelectorAll('[data-update-group]').forEach(group=>{
      const count=[...group.querySelectorAll('.literature-entry')].filter(item=>!item.hidden).length;
      if(group.tagName==='DETAILS') {group.hidden=count===0;group.querySelector('[data-update-count]').textContent=count+' 项 · 展开阅读';}
      else group.querySelector('[data-update-group-empty]').hidden=count>0;
    });
  }
  function reveal(){
    const hash=location.hash.slice(1);
    const target=document.getElementById(hash);
    if(!target || !root.contains(target))return;
    if(target.classList.contains('literature-entry') || target.hasAttribute('data-update-group')){
      // Keep an explicit reader filter unless it conceals the requested citation.
      if(target.hidden){filter.value='';apply();}
      if(target.tagName==='DETAILS')target.open=true;
    }
  }
  filter.addEventListener('change',apply);
  document.getElementById('update-reset').addEventListener('click',()=>{filter.value='';apply();});
  window.addEventListener('hashchange',reveal);
  apply();reveal();
})();
