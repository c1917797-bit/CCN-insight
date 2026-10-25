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
    if (event.defaultPrevented || !link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
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
