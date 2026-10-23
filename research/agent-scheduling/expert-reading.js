/* Lightweight reading assistance; all research content is already in the HTML. */
(() => {
  const bar = document.querySelector('.reading-progress span');
  const isTopic = document.body.dataset.pageKind === 'topic';
  const links = isTopic ? [...document.querySelectorAll('[aria-label="本页章节"] a')] : [];
  const sections = links.map(a => document.getElementById(a.hash.slice(1))).filter(Boolean);
  let scheduled = false;
  function update() {
    scheduled = false;
    const extent = Math.max(0, document.documentElement.scrollHeight - innerHeight);
    if (bar) bar.style.transform = `scaleX(${extent ? Math.min(1, scrollY / extent) : 0})`;
    if (!sections.length) return;
    const active = [...sections].reverse().find(s => s.getBoundingClientRect().top <= 160) || sections[0];
    for (const link of links) {
      if (link.hash === '#' + active.id) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    }
  }
  function requestUpdate() {
    if (!scheduled) { scheduled = true; requestAnimationFrame(update); }
  }
  window.addEventListener('scroll', requestUpdate, {passive: true});
  window.addEventListener('resize', requestUpdate, {passive: true});
  document.addEventListener('toggle', requestUpdate, true);
  document.addEventListener('reportviewchange', requestUpdate);
  window.addEventListener('hashchange', requestUpdate);
  update();
})();
