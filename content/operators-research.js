(() => {
  const header = document.querySelector('.op-header');
  const outline = [...document.querySelectorAll('.op-outline nav a')];
  const sections = outline.map(link => document.getElementById(link.getAttribute('href').slice(1))).filter(Boolean);
  let scheduled = false;
  function updateReading() {
    scheduled = false;
    const available = document.documentElement.scrollHeight - innerHeight;
    header?.style.setProperty('--reading', `${available > 0 ? Math.min(100,scrollY / available * 100) : 0}%`);
    const boundary = (header?.getBoundingClientRect().height || 68) + 35;
    const current = sections.filter(section => section.getBoundingClientRect().top <= boundary).sort((a,b) => b.getBoundingClientRect().top-a.getBoundingClientRect().top)[0];
    for (const link of outline) {
      const active = current && link.getAttribute('href') === `#${current.id}`;
      link.classList.toggle('is-active', !!active);
      if (active) link.setAttribute('aria-current','location');
      else link.removeAttribute('aria-current');
    }
  }
  addEventListener('scroll', () => {
    if (!scheduled) { scheduled = true; requestAnimationFrame(updateReading); }
  }, {passive:true});
  addEventListener('resize',updateReading,{passive:true});
  updateReading();
  const search = document.querySelector('[data-operator-search]');
  if (search) {
    const items = [...document.querySelectorAll('[data-route-search]')];
    const count = document.querySelector('[data-search-count]');
    search.addEventListener('input', () => {
      const query = search.value.trim().toLocaleLowerCase();
      let visible = 0;
      for (const item of items) {
        const matches = !query || item.dataset.routeSearch.toLocaleLowerCase().includes(query);
        item.hidden = !matches;
        if (matches) visible++;
      }
      for (const family of document.querySelectorAll('.op-family')) family.hidden = ![...family.querySelectorAll('[data-route-search]')].some(item => !item.hidden);
      if (count) count.textContent = `${visible} / ${items.length} 项机制`;
      const empty = document.querySelector('.op-filter-empty');
      if (empty) empty.hidden = visible > 0;
    });
  }
  const libraryQuery = document.querySelector('[data-library-query]');
  if (libraryQuery) {
    const records = [...document.querySelectorAll('[data-library-record]')];
    const filters = [...document.querySelectorAll('[data-library-filter]')];
    const count = document.querySelector('[data-library-count]');
    const empty = document.querySelector('.op-library-empty');
    const params = new URL(location.href).searchParams;
    libraryQuery.value = params.get('opq') || '';
    for (const filter of filters) {
      const value = params.get(`op_${filter.dataset.libraryFilter}`) || '';
      filter.value = [...filter.options].some(option => option.value === value) ? value : '';
    }
    function filterLibrary(syncUrl = true) {
      const query = libraryQuery.value.trim().toLocaleLowerCase();
      let visible = 0;
      for (const record of records) {
        const matches = (!query || record.dataset.search.includes(query)) && filters.every(filter => {
          if (!filter.value) return true;
          const key = filter.dataset.libraryFilter;
          const value = record.dataset[key] || '';
          return key === 'hardware' || key === 'metric' ? value.split(' ').includes(filter.value) : value === filter.value;
        });
        record.hidden = !matches;
        if (matches) visible++;
      }
      if (count) count.textContent = `${visible} / ${records.length} 条记录；硬件标签表示材料范围，适配情况请看原始条件。`;
      if (empty) empty.hidden = visible > 0;
      if (syncUrl) {
        const url = new URL(location.href);
        const entries = [['opq',libraryQuery.value.trim()], ...filters.map(filter => [`op_${filter.dataset.libraryFilter}`,filter.value])];
        for (const [key,value] of entries) {
          if (value) url.searchParams.set(key,value);
          else url.searchParams.delete(key);
        }
        history.replaceState(null,'',url);
      }
    }
    libraryQuery.addEventListener('input',()=>filterLibrary());
    for (const filter of filters) filter.addEventListener('change',()=>filterLibrary());
    document.querySelector('[data-library-reset]')?.addEventListener('click',()=>{
      libraryQuery.value = '';
      for (const filter of filters) filter.value = '';
      filterLibrary();
      libraryQuery.focus({preventScroll:true});
    });
    addEventListener('popstate',()=>{
      const restored = new URL(location.href).searchParams;
      libraryQuery.value = restored.get('opq') || '';
      for (const filter of filters) {
        const value = restored.get(`op_${filter.dataset.libraryFilter}`) || '';
        filter.value = [...filter.options].some(option => option.value === value) ? value : '';
      }
      filterLibrary(false);
    });
    filterLibrary(false);
  }
  const motion = document.querySelector('[data-motion-toggle]');
  if (motion) {
    const preference = matchMedia('(prefers-reduced-motion: reduce)');
    let paused = preference.matches;
    const apply = () => {
      if (preference.matches) paused=true;
      document.body.classList.toggle('op-motion-paused',paused);
      motion.setAttribute('aria-pressed',String(paused));
      motion.disabled = preference.matches;
      motion.textContent = preference.matches ? '静态显示' : (paused ? '播放动效' : '暂停动效');
    };
    motion.addEventListener('click',()=>{ paused=!paused; apply(); });
    preference.addEventListener('change',apply);
    apply();
  }
})();
