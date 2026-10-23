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
