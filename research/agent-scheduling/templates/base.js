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