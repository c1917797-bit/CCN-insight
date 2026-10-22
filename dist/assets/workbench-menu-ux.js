(function () {
  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  ready(function () {
    const shell = document.querySelector('lri-site-shell') || document.querySelector('.topic-shell');
    if (!shell) return;
    const center = document.querySelector('.topic-shell-center');
    const links = Array.from(document.querySelectorAll('.topic-shell-left .topic-path-link[data-path-main="1"][href^="#"]'));
    const sections = links.map((link) => {
      const id = decodeURIComponent(link.getAttribute('href') || '').slice(1);
      const section = id ? document.getElementById(id) : null;
      return section ? { id, link, section } : null;
    }).filter(Boolean);
    if (!sections.length) return;
    let manualId = '';
    let manualUntil = 0;

    function sectionMeta(link) {
      const raw = (link.querySelector('b')?.textContent || link.textContent || '').trim();
      const label = (link.dataset.sectionLabel || raw.replace(/^\d+\s*[·.]\s*/, '').replace(/专题工作台路径/g, '').replace(/当前段落/g, '').replace(/当前/g, '').trim() || '总览').trim();
      const index = (link.dataset.sectionIndex || raw.match(/^(\d+)/)?.[1] || '').trim();
      const group = (link.dataset.sectionGroup || '').trim();
      const position = Math.max(1, sections.findIndex((item) => item.link === link) + 1);
      const total = Math.max(1, sections.length);
      const progress = position + '/' + total;
      const percent = Math.round((position / total) * 100);
      const compact = [index ? index + ' · ' + label : label, group ? ' / ' + group : ''].join('');
      return { label, index, group, compact, position, total, progress, percent };
    }

    function mirrorCurrent(link) {
      const meta = sectionMeta(link);
      shell.setAttribute('data-current-section', meta.label);
      shell.setAttribute('data-current-section-index', meta.index);
      shell.setAttribute('data-current-section-group', meta.group);
      shell.setAttribute('data-current-section-position', String(meta.position));
      shell.setAttribute('data-current-section-total', String(meta.total));
      shell.style.setProperty('--topic-menu-progress', meta.percent + '%');
      document.querySelectorAll('[data-topic-current-section]').forEach((el) => { el.textContent = '当前：' + meta.progress + ' · ' + meta.compact; });
      document.querySelectorAll('[data-topic-current-section-footer]').forEach((el) => { el.textContent = 'section=' + meta.progress + ' · ' + meta.compact.replace(' · ', ' '); });
      document.querySelectorAll('[data-topic-progress-meter]').forEach((el) => {
        el.setAttribute('aria-label', '专题路径进度 ' + meta.progress);
        el.setAttribute('title', '专题路径进度 ' + meta.progress);
      });
    }

    function setCurrent(id) {
      sections.forEach(({ id: sectionId, link }) => {
        const active = sectionId === id;
        link.classList.toggle('is-current', active);
        if (active) {
          link.setAttribute('aria-current', 'location');
          mirrorCurrent(link);
        } else {
          link.removeAttribute('aria-current');
        }
      });
    }

    function currentByPosition() {
      if (manualId && Date.now() < manualUntil) {
        setCurrent(manualId);
        return;
      }
      const rootTop = center ? center.getBoundingClientRect().top : 0;
      let current = sections[0];
      for (const item of sections) {
        const top = item.section.getBoundingClientRect().top - rootTop;
        if (top <= 90) current = item;
        else break;
      }
      setCurrent(current.id);
    }

    links.forEach((link) => {
      link.addEventListener('click', function (event) {
        const id = decodeURIComponent(link.getAttribute('href') || '').slice(1);
        const target = id ? document.getElementById(id) : null;
        if (!target) return;
        event.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        history.replaceState(null, '', '#' + id);
        manualId = id;
        manualUntil = Date.now() + 1400;
        setCurrent(id);
      });
    });

    const initialId = (location.hash || '').slice(1);
    if (initialId && sections.some((x) => x.id === initialId)) setCurrent(initialId);
    else setCurrent(sections[0].id);

    let ticking = false;
    const onScroll = function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        ticking = false;
        currentByPosition();
      });
    };
    if (center) center.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('scroll', onScroll, { passive: true });
  });
})();

