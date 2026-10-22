const assetUrl = new URL('.', import.meta.url);
const repoRootUrl = new URL('../', assetUrl);
const configUrl = new URL('lri-shell.config.json', assetUrl);
const localeStorageKey = 'lri_locale';
const leftRailStorageKeyBase = 'lri_shell_left_rail_v3';
const rightRailStorageKeyBase = 'lri_shell_right_rail_v1';
const leftRailDefaultWidth = 240;
const leftRailMinWidth = 180;
const leftRailMaxWidth = 520;
const leftRailCollapsedWidth = 44;
const rightRailDefaultWidth = 250;
const rightRailCollapsedWidth = 44;
const forceRefreshParam = '_lri_force_refresh';

let sharedConfigPromise;
let translationRuntimePromise;

function loadTranslationRuntime() {
  if (!translationRuntimePromise) translationRuntimePromise = import('./lri-translation-runtime.js?v=explicit-headings-v2');
  return translationRuntimePromise;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[ch]);
}

function loadSharedConfig() {
  if (!sharedConfigPromise) {
    sharedConfigPromise = fetch(configUrl, { cache: 'no-store' }).then((response) => {
      if (!response.ok) throw new Error(`LRI shell config load failed: ${response.status}`);
      return response.json();
    });
  }
  return sharedConfigPromise;
}

function ensureRuntimeStyle() {
  if (!document.querySelector('meta[name="wwdc-workbench-shell"]')) return;
  const runtimeStyle = 'conference_insights/wwdc_2026/runtime/wwdc-view-runtime.css?v=runtime-v12-native-progress-autoplay';
  if (document.querySelector(`link[data-lri-runtime-style="${runtimeStyle}"]`)) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = new URL(`../${runtimeStyle}`, assetUrl).href;
  link.dataset.lriRuntimeStyle = runtimeStyle;
  document.head.appendChild(link);
}

function pageTitle() {
  return document.querySelector('main h1, h1')?.textContent?.trim() || document.title || 'LRI Insight';
}

function pageLocaleTemplate() {
  const meta = document.querySelector('meta[name="lri-page-i18n"]');
  return document.body?.dataset?.lriI18nTemplate || meta?.content || '';
}

function pageTranslationLevel() {
  const meta = document.querySelector('meta[name="lri-page-translation"]');
  const value = document.body?.dataset?.lriPageTranslation || meta?.content || 'source';
  return value === 'content' || value === 'ui' ? value : 'source';
}

function directViewContract() {
  const node = document.querySelector('[data-lri-view-kind]');
  const kind = node?.getAttribute('data-lri-view-kind') || '';
  const policy = node?.getAttribute('data-view-data-policy') || '';
  const editable = Boolean(document.querySelector('[contenteditable="true"]'));
  const snapshotSource = node?.getAttribute('data-view-snapshot-source') || '';
  const verifiedAt = node?.getAttribute('data-view-verified-at') || '';
  const evidenceSource = node?.getAttribute('data-view-evidence-source') || '';
  const localSnapshot = Boolean(snapshotSource || document.querySelector('[data-source*="data/workbench.json"], a[href*="data/workbench.json"]'));
  return kind.startsWith('direct-') ? { kind, policy, editable, localSnapshot, snapshotSource, verifiedAt, evidenceSource } : null;
}

function collectPageSections(locale = 'zh', labels = {}) {
  const seen = new Set();
  const result = [];
  document.querySelectorAll('main section[id], main [data-section-id]').forEach((node) => {
    if (document.body.dataset.lriSectionVisibility === 'visible' && node.closest('[hidden]')) return;
    if (node.getAttribute('data-section-outline') === 'false') return;
    const id = node.id || node.getAttribute('data-section-id');
    if (!id || seen.has(id)) return;
    const rawTitle = node.querySelector?.('h1, h2, h3')?.textContent?.trim()
      || node.getAttribute('data-section-label')
      || id.replace(/[-_]/g, ' ');
    const explicitTitle = locale === 'en' ? node.getAttribute('data-section-label-en') : node.getAttribute('data-section-label');
    const title = explicitTitle || (locale === 'en' ? labels.section_titles?.[rawTitle] : null) || rawTitle;
    const level = Number(node.getAttribute('data-section-level') || 2);
    seen.add(id);
    const number = node.getAttribute('data-section-number') || '';
    const collapsible = node.getAttribute('data-section-collapsible') === 'true';
    result.push({ id, title, number, collapsible, level: Number.isFinite(level) ? level : 2 });
  });
  if (!result.length) result.push({ id: 'top', title: pageTitle() });
  return result.slice(0, 32);
}

function renderSectionLinks(items, openGroups = new Set(), start = 0, end = items.length) {
  let html = '';
  for (let index = start; index < end; index++) {
    const item = items[index];
    const number = item.number || String(index + 1).padStart(2, '0');
    let childEnd = index + 1;
    if (item.collapsible) {
      while (childEnd < end && (items[childEnd].level || 2) > (item.level || 2)) childEnd++;
    }
    if (item.collapsible && childEnd > index + 1) {
      html += `<details class="section-group" data-shell-section-group="${escapeHtml(item.id)}" ${openGroups.has(item.id) ? 'open' : ''}><summary data-shell-group-toggle="${escapeHtml(item.id)}"><b>${escapeHtml(number)}</b><span>${escapeHtml(item.title)}</span><i aria-hidden="true">›</i></summary><div class="section-children">${renderSectionLinks(items, openGroups, index + 1, childEnd)}</div></details>`;
      index = childEnd - 1;
    } else {
      html += `<a href="#${escapeHtml(item.id)}" data-shell-section="${escapeHtml(item.id)}" data-level="${escapeHtml(String(item.level || 2))}"><b>${escapeHtml(number)}</b><span>${escapeHtml(item.title)}</span></a>`;
    }
  }
  return html;
}

function collectContextLinks(locale = 'zh') {
  const links = [];
  const seen = new Set();
  document.querySelectorAll('main a[href]').forEach((anchor) => {
    const href = anchor.getAttribute('href') || '';
    let label = anchor.getAttribute(locale === 'en' ? 'data-i18n-en' : 'data-i18n-zh') || anchor.textContent?.trim();
    if (!label || !href || href.startsWith('#') || href.startsWith('javascript:')) return;
    if (!/(evidence|source|data|review|json|证据|来源|数据|复核)/i.test(`${label} ${href}`)) return;
    if (locale === 'en' && /[\u4e00-\u9fff]/.test(label)) {
      try {
        const target = new URL(href, document.location.href);
        const host = target.hostname.replace(/^www\./, '') || 'source';
        label = `Source · ${host}`;
      } catch (_) { label = 'External source'; }
    }
    const key = `${label}|${href}`;
    if (seen.has(key)) return;
    seen.add(key);
    links.push({ label, href });
  });
  return links.slice(0, 8);
}

function normalizeLocale(locale) {
  return locale === 'en' ? 'en' : 'zh';
}

function clampLeftRailWidth(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return leftRailDefaultWidth;
  return Math.max(leftRailMinWidth, Math.min(leftRailMaxWidth, Math.round(number)));
}

function railPreferenceScope() {
  const path = document.location.pathname;
  return /\/(?:technology_insight|technology_trends|ai_computing|software|terminal_hardware)(?:\/|$)|\/research\/ct-technology-trend-insight-2026(?:\/|$)/.test(path)
    ? 'techintel'
    : 'global';
}

function leftRailStorageKey() {
  return `${leftRailStorageKeyBase}:${railPreferenceScope()}`;
}

function rightRailStorageKey() {
  return `${rightRailStorageKeyBase}:${railPreferenceScope()}`;
}

function loadLeftRailPreference() {
  try {
    const value = JSON.parse(localStorage.getItem(leftRailStorageKey()) || '{}');
    return { width: clampLeftRailWidth(value.width), collapsed: value.collapsed === true };
  } catch (_) {
    return { width: leftRailDefaultWidth, collapsed: false };
  }
}

function loadRightRailPreference() {
  try {
    const value = JSON.parse(localStorage.getItem(rightRailStorageKey()) || '{}');
    return { collapsed: value.collapsed !== false };
  } catch (_) {
    return { collapsed: true };
  }
}

function consumeForceRefreshMarker() {
  try {
    const url = new URL(document.location.href);
    if (!url.searchParams.has(forceRefreshParam)) return;
    url.searchParams.delete(forceRefreshParam);
    history.replaceState(history.state, '', `${url.pathname}${url.search}${url.hash}`);
  } catch (_) {}
}

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function clearOriginCacheStorage() {
  if (!('caches' in window)) return 0;
  const keys = await caches.keys();
  await Promise.allSettled(keys.map((key) => caches.delete(key)));
  return keys.length;
}

async function resetOriginServiceWorkers() {
  if (!('serviceWorker' in navigator)) return 0;
  const registrations = await navigator.serviceWorker.getRegistrations();
  await Promise.allSettled(registrations.map(async (registration) => {
    try { await registration.update(); } catch (_) {}
    [registration.installing, registration.waiting, registration.active].forEach((worker) => {
      try { worker?.postMessage({ type: 'SKIP_WAITING', source: 'lri-force-refresh' }); } catch (_) {}
    });
    try { await registration.unregister(); } catch (_) {}
  }));
  return registrations.length;
}

consumeForceRefreshMarker();

class LRISiteShell extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    const storedLocale = localStorage.getItem(localeStorageKey);
    const documentLocale = (document.documentElement.lang || '').toLowerCase().startsWith('en') ? 'en' : 'zh';
    this.locale = normalizeLocale(storedLocale || documentLocale);
    const leftRailPreference = loadLeftRailPreference();
    this.leftRailWidth = leftRailPreference.width;
    this.leftRailCollapsed = leftRailPreference.collapsed;
    const rightRailPreference = loadRightRailPreference();
    this.rightRailCollapsed = rightRailPreference.collapsed;
    this.leftRailResize = null;
    this.config = null;
    this.sections = [];
    this.contextLinks = [];
    this.observer = null;
    this.mobileDrawer = null;
    this.lastDrawerTrigger = null;
    this.previousDocumentOverflow = '';
    this.localeRequestEpoch = 0;
    this.sourceDocumentLang = document.documentElement.lang || 'zh-CN';
    this.boundKeydown = (event) => this.onKeydown(event);
    this.boundResize = () => this.onResize();
    this.boundLightDomClick = (event) => this.onLightDomClick(event);
    this.boundSectionsChanged = () => this.refreshSections();
    this.forceRefreshActive = false;
  }

  async connectedCallback() {
    if (this.dataset.ready === 'true') return;
    this.dataset.ready = 'true';
    this.syncLeftRailState();
    this.syncRightRailState();
    this.sections = collectPageSections(this.locale, this.labels());
    this.contextLinks = collectContextLinks(this.locale);
    document.addEventListener('lri:sections-changed', this.boundSectionsChanged);
    // Keep slotted business content visible while the shared navigation contract loads.
    // An empty shadow root would hide the already-readable main for another network round trip.
    const pendingContent = document.createElement('slot');
    pendingContent.name = 'content';
    this.shadowRoot.replaceChildren(pendingContent);
    this.config = await loadSharedConfig();
    this.sections = collectPageSections(this.locale, this.labels());
    ensureRuntimeStyle();
    this.render();
    this.bind();
    this.updateDrawerState();
    await this.applyLocale(this.locale, { announce: false });
    this.observeSections();
    document.addEventListener('keydown', this.boundKeydown);
    window.addEventListener('resize', this.boundResize, { passive: true });
    this.addEventListener('click', this.boundLightDomClick);
  }

  disconnectedCallback() {
    this.observer?.disconnect();
    document.removeEventListener('keydown', this.boundKeydown);
    document.removeEventListener('lri:sections-changed', this.boundSectionsChanged);
    window.removeEventListener('resize', this.boundResize);
    this.removeEventListener('click', this.boundLightDomClick);
    this.unlockDocumentScroll();
  }

  labels() {
    return this.config?.locales?.[this.locale] || this.config?.locales?.zh || {};
  }

  leftRailLabels() {
    return this.locale === 'en'
      ? { collapse: 'Collapse navigation', expand: 'Expand navigation', reset: 'Reset navigation width', resize: 'Resize navigation' }
      : { collapse: '收起左栏', expand: '展开左栏', reset: '恢复默认宽度', resize: '调整左栏宽度' };
  }

  rightRailLabels() {
    return this.locale === 'en'
      ? { collapse: 'Collapse evidence rail', expand: 'Expand evidence rail' }
      : { collapse: '收起右栏', expand: '展开右栏' };
  }

  persistLeftRailPreference() {
    try { localStorage.setItem(leftRailStorageKey(), JSON.stringify({ width: this.leftRailWidth, collapsed: this.leftRailCollapsed })); } catch (_) {}
  }

  syncLeftRailState({ persist = false } = {}) {
    if (this.leftRailCollapsed) this.setAttribute('data-left-collapsed', 'true');
    else this.removeAttribute('data-left-collapsed');
    this.style.setProperty('--lri-left-track', `${this.leftRailCollapsed ? leftRailCollapsedWidth : this.leftRailWidth}px`);
    const labels = this.leftRailLabels();
    const toggle = this.shadowRoot?.querySelector('[data-left-rail-toggle]');
    if (toggle) {
      const label = this.leftRailCollapsed ? labels.expand : labels.collapse;
      toggle.setAttribute('aria-label', label);
      toggle.setAttribute('title', label);
      toggle.setAttribute('aria-expanded', String(!this.leftRailCollapsed));
      toggle.textContent = this.leftRailCollapsed ? '›' : '‹';
    }
    this.shadowRoot?.querySelector('[data-left-rail-resizer]')?.setAttribute('aria-valuenow', String(this.leftRailWidth));
    if (persist) this.persistLeftRailPreference();
  }

  setLeftRailWidth(width, { persist = true } = {}) {
    this.leftRailWidth = clampLeftRailWidth(width);
    if (!this.leftRailCollapsed) this.style.setProperty('--lri-left-track', `${this.leftRailWidth}px`);
    this.shadowRoot?.querySelector('[data-left-rail-resizer]')?.setAttribute('aria-valuenow', String(this.leftRailWidth));
    if (persist) this.persistLeftRailPreference();
  }

  setLeftRailCollapsed(collapsed) {
    this.leftRailCollapsed = Boolean(collapsed);
    this.syncLeftRailState({ persist: true });
  }

  persistRightRailPreference() {
    try { localStorage.setItem(rightRailStorageKey(), JSON.stringify({ collapsed: this.rightRailCollapsed })); } catch (_) {}
  }

  syncRightRailState({ persist = false } = {}) {
    if (this.rightRailCollapsed) this.setAttribute('data-right-collapsed', 'true');
    else this.removeAttribute('data-right-collapsed');
    this.style.setProperty('--lri-right-track', `${this.rightRailCollapsed ? rightRailCollapsedWidth : rightRailDefaultWidth}px`);
    const labels = this.rightRailLabels();
    const toggle = this.shadowRoot?.querySelector('[data-right-rail-toggle]');
    if (toggle) {
      const label = this.rightRailCollapsed ? labels.expand : labels.collapse;
      toggle.setAttribute('aria-label', label);
      toggle.setAttribute('title', label);
      toggle.setAttribute('aria-expanded', String(!this.rightRailCollapsed));
      toggle.textContent = this.rightRailCollapsed ? '‹' : '›';
    }
    if (persist) this.persistRightRailPreference();
  }

  setRightRailCollapsed(collapsed) {
    this.rightRailCollapsed = Boolean(collapsed);
    this.syncRightRailState({ persist: true });
  }

  beginLeftRailResize(event, handle) {
    if (this.drawerMode('left') || this.leftRailCollapsed || event.button !== 0) return;
    const left = this.shadowRoot.querySelector('.left');
    this.leftRailResize = { pointerId: event.pointerId, startX: event.clientX, startWidth: left?.getBoundingClientRect().width || this.leftRailWidth };
    this.setAttribute('data-left-resizing', 'true');
    handle.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  }

  moveLeftRailResize(event) {
    if (!this.leftRailResize || event.pointerId !== this.leftRailResize.pointerId) return;
    this.setLeftRailWidth(this.leftRailResize.startWidth + event.clientX - this.leftRailResize.startX, { persist: false });
  }

  finishLeftRailResize(event, handle) {
    if (!this.leftRailResize || event.pointerId !== this.leftRailResize.pointerId) return;
    handle.releasePointerCapture?.(event.pointerId);
    this.leftRailResize = null;
    this.removeAttribute('data-left-resizing');
    this.persistLeftRailPreference();
  }

  adjustLeftRailFromKeyboard(event) {
    if (this.drawerMode('left') || this.leftRailCollapsed) return;
    const step = event.shiftKey ? 50 : 20;
    let width = this.leftRailWidth;
    if (event.key === 'ArrowLeft') width -= step;
    else if (event.key === 'ArrowRight') width += step;
    else if (event.key === 'Home') width = leftRailMinWidth;
    else if (event.key === 'End') width = leftRailMaxWidth;
    else return;
    event.preventDefault();
    this.setLeftRailWidth(width);
  }

  absoluteRepoUrl(path) {
    return new URL(path, repoRootUrl).href;
  }

  isCurrentPath(path) {
    const current = new URL(document.location.href).pathname.replace(/\/$/, '/index.html');
    const target = new URL(path, repoRootUrl).pathname.replace(/\/$/, '/index.html');
    return current === target || (path !== 'index.html' && current.startsWith(target.replace(/index\.html$/, '')));
  }

  isExactCurrentPath(path) {
    const current = new URL(document.location.href).pathname.replace(/\/$/, '/index.html');
    const target = new URL(path, repoRootUrl).pathname.replace(/\/$/, '/index.html');
    return current === target;
  }

  isExactCurrentLocation(path) {
    const current = new URL(document.location.href);
    const target = new URL(path, repoRootUrl);
    const currentPath = current.pathname.replace(/\/$/, '/index.html');
    const targetPath = target.pathname.replace(/\/$/, '/index.html');
    if (currentPath !== targetPath) return false;
    if (target.hash && current.hash !== target.hash) return false;
    return target.search ? current.search === target.search : !current.search;
  }

  currentRepoPath() {
    const current = new URL(document.location.href).pathname.replace(/^\/+/, '');
    const root = repoRootUrl.pathname.replace(/^\/+|\/+$/g, '');
    return root && current.startsWith(`${root}/`) ? current.slice(root.length + 1) : current;
  }

  contextNavigation(labels) {
    const current = this.currentRepoPath();
    return (labels.context_nav || [])
      .filter((group) => group?.prefix && current.startsWith(group.prefix))
      .sort((a, b) => b.prefix.length - a.prefix.length)[0] || null;
  }

  currentPageLabel(labels) {
    const context = this.contextNavigation(labels);
    const currentItem = (context?.items || []).find((item) => item?.path && this.isExactCurrentPath(item.path));
    return currentItem?.label || pageTitle();
  }

  render() {
    const labels = this.labels();
    const leftRailLabels = this.leftRailLabels();
    const rightRailLabels = this.rightRailLabels();
    const navigation = (labels.nav || []).map((item) => {
      const current = this.isCurrentPath(item.path);
      return `<a href="${this.absoluteRepoUrl(item.path)}" ${current ? 'aria-current="page"' : ''}>${escapeHtml(item.label)}</a>`;
    }).join('');
    const openSectionGroups = new Set(Array.from(this.shadowRoot.querySelectorAll('[data-shell-section-group][open]')).map(node => node.dataset.shellSectionGroup));
    const sectionLinks = renderSectionLinks(this.sections, openSectionGroups);
    const contextNavigation = this.contextNavigation(labels);
    const currentPageLabel = this.currentPageLabel(labels);
    const renderWorkspaceLinks = (items = []) => items.map((item, index) => {
      const target = new URL(this.absoluteRepoUrl(item.path));
      const currentQuery = new URL(document.location.href).searchParams;
      (contextNavigation?.preserve_query || []).forEach((key) => { if (currentQuery.has(key)) target.searchParams.set(key, currentQuery.get(key)); });
      const current = item.current === true || document.body.dataset.lriContextItem === item.id || this.isExactCurrentLocation(item.path);
      return `<a href="${escapeHtml(target.href)}" ${current ? 'aria-current="page"' : ''}><b>${String(index + 1).padStart(2, '0')}</b><span>${escapeHtml(item.label)}</span></a>`;
    }).join('');
    const workspaceLinks = renderWorkspaceLinks(contextNavigation?.items || []);
    const readerSelector = document.body.dataset.lriReaderNavigation;
    const readerCandidate = readerSelector ? document.querySelector(readerSelector) : null;
    const readerNav = readerCandidate?.closest('[hidden]') ? null : readerCandidate;
    const readerItems = readerNav ? Array.from(readerNav.querySelectorAll('a[href]')).filter(a => !a.hidden).map(a => ({path:a.href,label:a.querySelector('strong')?.textContent?.trim() || a.firstChild?.textContent?.trim() || a.textContent.trim(),current:a.getAttribute('aria-current')==='page'})) : [];
    const readerGroups = readerItems.length ? [{label:document.body.dataset.lriReaderNavigationLabel || labels.on_this_page,items:readerItems}] : [];
    const workspaceGroups = [...(contextNavigation?.groups || []),...readerGroups].map((group) => {
      const groupLinks = renderWorkspaceLinks(group.items || []);
      return `<div class="workspace-block ${group.featured ? 'featured' : ''}"><div class="workspace-group-title">${escapeHtml(group.label || '')}</div><nav class="path workspace-path">${groupLinks}</nav></div>`;
    }).join('');
    const cloudReader = document.body.dataset.lriContextItem?.startsWith('cloud-core-') && readerItems.length > 0;
    const showSectionNavigation = !cloudReader && (contextNavigation?.section_navigation !== 'topic-only' || document.body.dataset.compressionTopic === 'true');
    const outlineOpen = this.shadowRoot.querySelector('[data-shell-outline]')?.open === true || (document.body.dataset.lriContextItem === 'cloud-core-updates' && this.lastOutlineContext !== 'cloud-core-updates');
    this.lastOutlineContext = document.body.dataset.lriContextItem;
    const sectionNavigation = showSectionNavigation ? (['topic-only','folded'].includes(contextNavigation?.section_navigation)
      ? `<details class="section-group" data-shell-outline ${outlineOpen ? 'open' : ''}><summary><b aria-hidden="true"></b><span>${escapeHtml(contextNavigation.section_label || labels.on_this_page || '')}</span><i aria-hidden="true">›</i></summary><nav class="path section-path">${sectionLinks}</nav></details>`
      : `<div class="rail-group-title">${escapeHtml(labels.on_this_page || labels.overview || '')}</div><nav class="path section-path">${sectionLinks}</nav>`) : '';
    const cloudPage = location.pathname.startsWith('/business_insight/cloud_core/');
    const sourcePanel = document.getElementById('view-sources');
    const sourceVisible = sourcePanel && !sourcePanel.closest('[hidden]');
    const localItems = sourceVisible
      ? Array.from(document.querySelectorAll('.wb-domain-tabs [data-domain]')).map(a => ({label:a.textContent.trim(), domain:a.dataset.domain, active:a.getAttribute('aria-selected')==='true'}))
      : this.sections.filter(item => { const el=document.getElementById(item.id); return el && !el.closest('[hidden]') && !['judgment-basis','reading-guide'].includes(item.id) && !item.id.startsWith('view-'); }).map(item => ({label:item.label || item.title || document.getElementById(item.id)?.querySelector('h2,h3,h4')?.textContent || item.id, id:item.id}));
    const cloudLocalNav = '<nav class="path cloud-local-path">' + localItems.map((item,i) => '<a href="#'+(item.id || 'channels-panel')+'" '+(item.domain?'data-cloud-domain="'+escapeHtml(item.domain)+'"':'data-shell-section="'+escapeHtml(item.id)+'"')+(item.active?' aria-current="page"':'')+'><b>'+String(i+1).padStart(2,'0')+'</b><span>'+escapeHtml(item.label)+'</span></a>').join('')+'</nav>';
    this.toggleAttribute('data-cloud-no-outline', cloudPage && localItems.length===0);
    const leftNavigation = cloudPage ? cloudLocalNav : contextNavigation
      ? `<div class="rail-group"><div class="rail-group-title">${escapeHtml(contextNavigation.label || labels.workspace_pages || '')}</div><nav class="path workspace-path">${workspaceLinks}</nav>${workspaceGroups}</div>${sectionNavigation ? `<div class="rail-group">${sectionNavigation}</div>` : ''}`
      : `<nav class="path section-path">${sectionLinks}</nav>`;
    const contextLinks = this.contextLinks.length
      ? `<ul>${this.contextLinks.map((item) => `<li><a href="${escapeHtml(item.href)}">${escapeHtml(item.label)}</a></li>`).join('')}</ul>`
      : `<p class="muted">${escapeHtml(labels.source_only || '')}</p>`;
    const hasPagePack = Boolean(pageLocaleTemplate());
    const translationLevel = pageTranslationLevel();
    const translationLabel = translationLevel === 'content'
      ? (labels.bilingual_content || labels.bilingual || '')
      : translationLevel === 'ui'
        ? (labels.bilingual_ui || labels.bilingual || '')
        : (labels.source_only || '');
    const directView = directViewContract();
    const directViewStatus = directView
      ? `<div class="panel direct-view-status"><span class="badge">${escapeHtml(labels.direct_view || 'Direct View')}</span><h3>${escapeHtml(labels.direct_view_kinds?.[directView.kind] || directView.kind)}</h3><p>${escapeHtml(labels.direct_view_boundary || '')}</p>${directView.localSnapshot ? `<p class="muted">${escapeHtml(labels.direct_view_snapshot_source || '')}</p>` : ''}${directView.verifiedAt ? `<p class="muted">${escapeHtml(labels.direct_view_verified || 'Verified')}: <b>${escapeHtml(directView.verifiedAt)}</b></p>` : ''}${directView.editable ? `<p class="muted">${escapeHtml(labels.direct_view_editable_note || '')}</p>` : ''}</div>`
      : '';
    this.shadowRoot.innerHTML = `
      <style>
        :host{display:block;min-height:100vh;background:#f5f6f8;color:#17191c;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
        *{box-sizing:border-box}button{font:inherit}a{color:inherit}.shell{display:grid;grid-template-columns:min(var(--lri-left-track,240px),42vw) minmax(0,1fr) min(var(--lri-right-track,44px),32vw);grid-template-rows:auto minmax(0,1fr) auto;min-height:100vh;gap:1px;background:#d9dde3}
        header{grid-column:1/-1;position:sticky;top:0;z-index:60;background:rgba(255,255,255,.96);backdrop-filter:blur(12px);border-bottom:1px solid #d9dde3;padding:10px 16px;display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:14px;align-items:center}
        .brand{display:flex;align-items:center;gap:10px;white-space:nowrap}.brand-mark{display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:#111827;color:#fff;font-weight:800}.brand b{display:block}.role{display:block;color:#687080;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase}
        .global{display:flex;gap:6px;overflow:auto;padding:2px}.global a{white-space:nowrap;text-decoration:none;border-radius:8px;padding:8px 10px;font-size:13px;font-weight:650}.global a:hover,.global a:focus-visible{background:#eef1f5;outline:none}.global a[aria-current="page"]{background:#111827;color:#fff}
        .header-actions{display:flex;align-items:center;justify-content:flex-end;gap:6px}.locale{display:flex;gap:4px}.locale button{border:1px solid #cfd5dd;background:#fff;border-radius:8px;padding:7px 9px;font-weight:750;cursor:pointer}.locale button[aria-pressed="true"]{background:#0f766e;color:#fff;border-color:#0f766e}
        .refresh-button{display:inline-grid;place-items:center;flex:0 0 auto;width:38px;height:38px;border:1px solid #cfd5dd;border-radius:10px;background:#fff;color:#273241;cursor:pointer}.refresh-button:hover,.refresh-button:focus-visible{background:#eef5f4;color:#0f5f58;outline:2px solid #77aaa5;outline-offset:1px}.refresh-button:disabled{cursor:wait;opacity:.72}.refresh-button svg{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.refresh-button[aria-busy="true"] svg{animation:lri-force-spin .7s linear infinite}.sr-only{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}@keyframes lri-force-spin{to{transform:rotate(360deg)}}
        .drawer-toggle,.drawer-close,.backdrop{border:0}.drawer-toggle{display:none;align-items:center;justify-content:center;width:38px;height:38px;border:1px solid #cfd5dd;border-radius:10px;background:#fff;color:#222a35;cursor:pointer}.drawer-toggle:hover,.drawer-toggle:focus-visible,.drawer-close:hover,.drawer-close:focus-visible{background:#eef5f4;color:#0f5f58;outline:2px solid #77aaa5;outline-offset:1px}.drawer-toggle svg{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
        aside,.content{background:#fff;min-width:0}.left,.right{padding:16px 14px;position:sticky;top:65px;height:calc(100vh - 65px);overflow:auto}.left{position:sticky}.content{padding:0;overflow:visible}
        .left-rail-controls,.right-rail-controls{display:flex;align-items:center;gap:4px;margin:-7px -5px 9px}.left-rail-controls{justify-content:flex-end}.right-rail-controls{justify-content:flex-start}.left-rail-button,.right-rail-button{display:grid;place-items:center;width:28px;height:28px;border:1px solid #d8dde4;border-radius:7px;background:#fff;color:#596372;cursor:pointer;font-weight:800;line-height:1}.left-rail-button:hover,.left-rail-button:focus-visible,.right-rail-button:hover,.right-rail-button:focus-visible{background:#eef5f4;color:#0f5f58;outline:2px solid #77aaa5;outline-offset:1px}.left-rail-reset{font-size:14px}.left-rail-toggle,.right-rail-toggle{font-size:21px}.left-resizer{position:absolute;top:0;right:0;width:9px;height:100%;cursor:col-resize;touch-action:none;z-index:5}.left-resizer::after{content:'';position:absolute;top:0;bottom:0;left:4px;width:1px;background:transparent}.left-resizer:hover::after,.left-resizer:focus-visible::after,:host([data-left-resizing="true"]) .left-resizer::after{background:#0f766e}.left-resizer:focus-visible{outline:none}
        .drawer-head{display:none;align-items:center;justify-content:space-between;gap:12px;min-height:54px;margin:-16px -14px 14px;padding:calc(10px + env(safe-area-inset-top,0px)) 14px 10px;border-bottom:1px solid #dfe3e8;background:#fff;position:sticky;top:-16px;z-index:2}.drawer-head b{font-size:14px}.drawer-close{display:grid;place-items:center;width:38px;height:38px;border-radius:10px;background:#f2f4f7;color:#313946;cursor:pointer;font-size:24px;line-height:1}
        .backdrop{display:none;position:fixed;inset:0;z-index:70;background:rgba(15,23,42,.46);backdrop-filter:blur(2px);cursor:pointer}
        .rail-title{font-size:12px;font-weight:800;color:#566070;letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px}.rail-group+.rail-group{margin-top:18px;padding-top:14px;border-top:1px solid #e2e6eb}.rail-group-title{margin:0 8px 7px;color:#707987;font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase}.workspace-block{margin-top:12px;padding-top:10px;border-top:1px solid #edf0f3}.workspace-block.featured{margin-top:14px;padding:11px 8px 8px;border:1px solid #cfe2df;border-radius:11px;background:#f4faf9}.workspace-group-title{margin:0 8px 6px;color:#4d5968;font-size:12px;font-weight:800}.workspace-block.featured .workspace-group-title{color:#0f5f58;font-size:14px;letter-spacing:.01em}.workspace-block.featured .path a{padding:9px 8px}.path{display:grid;gap:4px}.path a{display:grid;grid-template-columns:28px minmax(0,1fr);gap:6px;align-items:start;text-decoration:none;padding:8px;border-radius:8px;color:#333b48}.path a:hover,.path a:focus-visible,.path a.is-current,.path a[aria-current="page"]{background:#eef5f4;color:#0f5f58;outline:none}.path a[aria-current="page"]{box-shadow:inset 3px 0 #0f766e}.path b{font-size:11px;color:#7d8591;padding-top:2px}.path span{font-size:13px;font-weight:650;min-width:0;overflow:visible;text-overflow:clip;white-space:normal;overflow-wrap:anywhere;line-height:1.35}.section-path a[data-level="3"]{grid-template-columns:22px minmax(0,1fr);padding:6px 8px 6px 18px}.section-path a[data-level="3"] b{font-size:9px;color:#9aa1ab}.section-path a[data-level="3"] span{font-size:12px;font-weight:600;color:#596372}

        .section-group{min-width:0}.section-group>summary{display:grid;grid-template-columns:28px minmax(0,1fr) 14px;gap:6px;align-items:start;padding:8px;border-radius:8px;color:#333b48;cursor:pointer;list-style:none}.section-group>summary::-webkit-details-marker{display:none}.section-group>summary:hover,.section-group>summary:focus-visible{background:#eef5f4;color:#0f5f58;outline:2px solid #77aaa5;outline-offset:-2px}.section-group>summary i{font-style:normal;font-size:18px;line-height:1;transition:transform .15s}.section-group[open]>summary i{transform:rotate(90deg)}.section-children{display:grid;gap:4px;padding-top:4px}
        @media(min-width:761px){:host([data-left-collapsed="true"]) .left{padding:10px 7px;overflow:hidden}:host([data-left-collapsed="true"]) .left-rail-controls{justify-content:center;margin:0}:host([data-left-collapsed="true"]) .left-rail-reset,:host([data-left-collapsed="true"]) .left .rail-title,:host([data-left-collapsed="true"]) .left>slot[name="left"],:host([data-left-collapsed="true"]) .left-resizer{display:none}:host([data-left-resizing="true"]){cursor:col-resize;user-select:none}}
        @media(min-width:1051px){:host([data-right-collapsed="true"]:not([data-content-kind="session"]):not([data-content-kind="resource-registry"])) .right{padding:10px 7px;overflow:hidden}:host([data-right-collapsed="true"]:not([data-content-kind="session"]):not([data-content-kind="resource-registry"])) .right-rail-controls{justify-content:center;margin:0}:host([data-right-collapsed="true"]:not([data-content-kind="session"]):not([data-content-kind="resource-registry"])) .right .rail-title,:host([data-right-collapsed="true"]:not([data-content-kind="session"]):not([data-content-kind="resource-registry"])) .right .direct-view-status,:host([data-right-collapsed="true"]:not([data-content-kind="session"]):not([data-content-kind="resource-registry"])) .right>slot[name="right"]{display:none}}
        .panel{border:1px solid #dfe3e8;border-radius:10px;padding:12px;margin-bottom:10px}.panel h3{font-size:13px;margin:0 0 8px}.panel p,.panel li{font-size:12px;line-height:1.55}.panel ul{padding-left:18px;margin:0}.panel a{overflow-wrap:anywhere}.muted{color:#6c7480}.badge{display:inline-flex;border-radius:999px;background:#eef1f5;padding:4px 7px;font-size:11px;font-weight:750}
        footer{grid-column:1/-1;background:#fff;border-top:1px solid #d9dde3;padding:8px 16px;display:flex;gap:12px;flex-wrap:wrap;font-size:11px;color:#69717d;min-width:0;overflow:hidden}
        footer span{min-width:0;max-width:100%;overflow-wrap:anywhere}
        ::slotted([slot="content"]){display:block!important;position:static!important;width:100%!important;max-width:none!important;min-width:0!important;height:auto!important;overflow:visible!important;margin:0!important}
        :host([data-content-kind="topic"]) ::slotted([slot="content"]),:host([data-content-kind="report"]) ::slotted([slot="content"]),:host([data-content-kind="page"]) ::slotted([slot="content"]){max-width:1480px!important;margin-inline:auto!important}
        /* Topic workbenches lock document scrolling and therefore require the
           shell content slot itself to own vertical scrolling. Keep this
           contract inside the shadow tree so page CSS cannot be defeated by
           the generic slotted-content reset above. */
        :host([data-content-kind="topic"]){height:100vh;height:100dvh;min-height:0;overflow:hidden}
        :host([data-content-kind="topic"]) .shell{height:100vh;height:100dvh;min-height:0;overflow:hidden}
        :host([data-content-kind="topic"]) .content{min-height:0;overflow:hidden}
        :host([data-content-kind="topic"]) ::slotted([slot="content"]){height:100%!important;max-height:100%!important;overflow-x:hidden!important;overflow-y:auto!important;overscroll-behavior:contain}
        :host([data-content-kind="resource-registry"]){height:100vh;height:100dvh;min-height:0;overflow:hidden}
        :host([data-content-kind="resource-registry"]) .shell{grid-template-columns:min(var(--lri-left-track,220px),42vw) minmax(0,1fr);grid-template-rows:auto minmax(0,1fr);height:100vh;height:100dvh;min-height:0;overflow:hidden}
        :host([data-content-kind="resource-registry"]) .content{min-height:0;overflow:hidden}
        :host([data-content-kind="resource-registry"]) ::slotted([slot="content"]){display:grid!important;height:100%!important;max-height:100%!important;overflow:hidden!important}
        :host([data-content-kind="resource-registry"]) footer{display:none}
        ::slotted([slot="left"]),::slotted([slot="right"]){display:block!important;position:static!important;width:auto!important;height:auto!important;overflow:visible!important;border:0!important;background:transparent!important;padding:0!important}
        /* Session workbenches already own an in-content intelligence pane. Keep the global right rail as an on-demand inspector so the research IDE receives desktop width. */
        :host([data-content-kind="session"]) .shell{grid-template-columns:min(var(--lri-left-track,220px),42vw) minmax(0,1fr)}
        :host([data-content-kind="session"]) .right-toggle,:host([data-content-kind="resource-registry"]) .right-toggle{display:inline-flex}
        :host([data-content-kind="session"]) .right-rail-controls,:host([data-content-kind="resource-registry"]) .right-rail-controls{display:none}
        :host([data-content-kind="session"]) .right,:host([data-content-kind="resource-registry"]) .right{display:block;position:fixed;top:0;right:0;z-index:80;width:min(88vw,380px);max-width:100%;height:100vh;height:100dvh;padding:16px 14px calc(16px + env(safe-area-inset-bottom,0px));box-shadow:-18px 0 44px rgba(15,23,42,.22);transform:translateX(105%);transition:transform .24s ease;overscroll-behavior:contain;touch-action:pan-y}
        :host([data-content-kind="session"][data-context-right="off"]) .right-toggle,:host([data-content-kind="session"][data-context-right="off"]) .right{display:none!important}
        :host([data-content-kind="session"]) .right .drawer-head,:host([data-content-kind="resource-registry"]) .right .drawer-head{display:flex}
        :host([data-content-kind="session"][data-mobile-drawer="right"]) .right,:host([data-content-kind="resource-registry"][data-mobile-drawer="right"]) .right{transform:translateX(0)}
        :host([data-content-kind="session"][data-mobile-drawer="right"]) .backdrop,:host([data-content-kind="resource-registry"][data-mobile-drawer="right"]) .backdrop{display:block}
        @media(max-width:1050px){
          .shell{grid-template-columns:min(var(--lri-left-track,240px),42vw) minmax(0,1fr)}
          .right-toggle{display:inline-flex}
          .right-rail-controls{display:none}
          .right{display:block;position:fixed;top:0;right:0;z-index:80;width:min(88vw,360px);max-width:100%;height:100vh;height:100dvh;padding:16px 14px calc(16px + env(safe-area-inset-bottom,0px));box-shadow:-18px 0 44px rgba(15,23,42,.22);transform:translateX(105%);transition:transform .24s ease;overscroll-behavior:contain;touch-action:pan-y}
          .right .drawer-head{display:flex}
          :host([data-mobile-drawer="right"]) .right{transform:translateX(0)}
          :host([data-mobile-drawer="right"]) .backdrop{display:block}
        }
        @media(max-width:760px){
          :host{overflow-x:clip}.shell{display:block;min-width:0;overflow-x:clip}
          :host([data-content-kind="topic"]){height:auto;min-height:100vh;overflow:visible}
          :host([data-content-kind="topic"]) .shell{height:auto;min-height:100vh;overflow:visible}
          :host([data-content-kind="topic"]) .content{overflow:visible}
          :host([data-content-kind="topic"]) ::slotted([slot="content"]){height:auto!important;max-height:none!important;overflow:visible!important}
          :host([data-content-kind="resource-registry"]){height:100vh;height:100dvh;min-height:0;overflow:hidden}
          :host([data-content-kind="resource-registry"]) .shell{display:flex;flex-direction:column;height:100vh;height:100dvh;min-height:0;overflow:hidden}
          :host([data-content-kind="resource-registry"]) .content{flex:1 1 auto;min-height:0;overflow:hidden}
          :host([data-content-kind="resource-registry"]) ::slotted([slot="content"]){display:grid!important;height:100%!important;max-height:100%!important;overflow:hidden!important}
          header{position:sticky;top:0;grid-template-columns:auto minmax(0,1fr) auto;padding:calc(8px + env(safe-area-inset-top,0px)) 10px 8px;gap:8px}
          .left-toggle{display:inline-flex}.brand{min-width:0;justify-self:start}.brand span:last-child{min-width:0}.brand b{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.brand .role{display:none}.brand-mark{width:30px;height:30px;border-radius:8px;font-size:12px}
          .header-actions{min-width:0}.refresh-button{width:34px;height:34px;border-radius:9px}.refresh-button svg{width:18px;height:18px}.locale button{padding:6px 7px;font-size:12px}.global{grid-column:1/-1;order:3;margin:0 -2px;padding:4px 2px 1px;scrollbar-width:none;overscroll-behavior-x:contain;touch-action:pan-x}.global::-webkit-scrollbar{display:none}.global a{padding:7px 9px;font-size:12px}
          .left{display:block;position:fixed;top:0;left:0;z-index:80;width:min(86vw,340px);max-width:100%;height:100vh;height:100dvh;padding:16px 14px calc(16px + env(safe-area-inset-bottom,0px));box-shadow:18px 0 44px rgba(15,23,42,.22);transform:translateX(-105%);transition:transform .24s ease;overscroll-behavior:contain;touch-action:pan-y}
          .left-rail-controls,.right-rail-controls,.left-resizer{display:none}
          .left .drawer-head{display:flex}
          :host([data-mobile-drawer="left"]) .left{transform:translateX(0)}
          :host([data-mobile-drawer="left"]) .backdrop{display:block}
          .content{min-height:70vh;min-width:0}footer{display:none}
        }
        @media print{
          :host{display:block;min-height:0;background:#fff;overflow:visible}
          .shell{display:block;min-height:0;height:auto!important;background:#fff;overflow:visible!important}
          header,.left,.right,footer,.backdrop{display:none!important}
          .content{display:block!important;min-height:0!important;height:auto!important;overflow:visible!important;background:#fff}
          ::slotted([slot="content"]){display:block!important;position:static!important;width:100%!important;max-width:none!important;min-width:0!important;height:auto!important;max-height:none!important;overflow:visible!important;margin:0!important}
        }
        @media(prefers-reduced-motion:reduce){.left,.right{transition:none}}
        .cloud-core-header{display:flex;min-height:48px;padding:6px 16px;gap:12px}.cloud-core-header .header-actions{margin-left:auto}.cloud-core-header .brand-mark{background:#0f766e;font-size:12px}.cloud-core-header .brand b{font-size:16px}
        .cloud-primary-nav{display:flex;align-items:center;gap:6px;margin-left:24px;min-width:0;overflow:auto}.cloud-primary-nav a{padding:9px 16px;border-radius:9px;text-decoration:none;white-space:nowrap;font-size:14px;font-weight:650;color:#476071}.cloud-primary-nav a:hover{background:#edf6f7}.cloud-primary-nav a[aria-current="page"]{background:#e3f3f3;color:#086e78;box-shadow:inset 0 -2px #118893}.cloud-primary-nav a:focus-visible{outline:2px solid #118893;outline-offset:2px}@media(max-width:1050px){.cloud-primary-nav{display:none}}
        :host([data-cloud-no-outline]) .shell{grid-template-columns:minmax(0,1fr) min(var(--lri-right-track,44px),32vw)}:host([data-cloud-no-outline]) .left,:host([data-cloud-no-outline]) .left-toggle{display:none}.cloud-local-path{margin-top:12px}
      </style>
      <div class="shell">
        <header class="${location.pathname.startsWith('/business_insight/cloud_core/') ? 'cloud-core-header' : ''}">
          <button class="drawer-toggle left-toggle" type="button" data-drawer-open="left" aria-controls="lri-left-drawer" aria-expanded="false" aria-label="${escapeHtml(labels.open_path || '')}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h12M4 18h8"/></svg></button>
          <div class="brand"><span class="brand-mark">${location.pathname.startsWith('/business_insight/cloud_core/') ? '极智' : 'LRI'}</span><span><b>${location.pathname.startsWith('/business_insight/cloud_core/') ? (this.locale === 'en' ? 'Jizhi · AI Infra' : '极智 · AI Infra') : escapeHtml(labels.brand || 'LRI Insight')}</b>${location.pathname.startsWith('/business_insight/cloud_core/') ? '' : `<small class="role">${escapeHtml(labels.top_role || '')}</small>`}</span></div>
          ${location.pathname.startsWith('/business_insight/cloud_core/') ? `<nav class="cloud-primary-nav" aria-label="${this.locale === 'en' ? 'Insight navigation' : '洞察导航'}">${Array.from(document.querySelectorAll('.wb-view-tabs a')).map(a => `<a href="${escapeHtml(a.href)}" data-cloud-view="${escapeHtml(a.dataset.view || '')}" ${a.getAttribute('aria-current') === 'page' ? 'aria-current="page"' : ''}>${escapeHtml(a.textContent.trim())}</a>`).join('')}</nav>` : `<nav class="global" aria-label="${escapeHtml(labels.top_role || '')}">${navigation}</nav>`}
          <div class="header-actions"><button class="refresh-button" type="button" data-force-refresh aria-label="${escapeHtml(labels.force_refresh || 'Force refresh')}" title="${escapeHtml(labels.force_refresh || 'Force refresh')}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 11a8 8 0 1 0-2.34 5.66"/><path d="M20 4v7h-7"/></svg></button><span class="sr-only" data-refresh-status aria-live="polite"></span><div class="locale" aria-label="Language"><button type="button" data-locale="zh" aria-pressed="${this.locale === 'zh'}">中文</button><button type="button" data-locale="en" aria-pressed="${this.locale === 'en'}">EN</button></div><button class="drawer-toggle right-toggle" type="button" data-drawer-open="right" aria-controls="lri-right-drawer" aria-expanded="false" aria-label="${escapeHtml(labels.open_evidence || '')}"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 10v6M12 7h.01"/></svg></button></div>
        </header>
        <button class="backdrop" type="button" data-drawer-close aria-label="${escapeHtml(labels.close_drawer || '')}"></button>
        <aside class="left" id="lri-left-drawer"><div class="drawer-head"><b>${escapeHtml(labels.path_drawer || labels.left_role || '')}</b><button class="drawer-close" type="button" data-drawer-close aria-label="${escapeHtml(labels.close_drawer || '')}">×</button></div><div class="left-rail-controls"><button class="left-rail-button left-rail-reset" type="button" data-left-rail-reset aria-label="${escapeHtml(leftRailLabels.reset)}" title="${escapeHtml(leftRailLabels.reset)}">↺</button><button class="left-rail-button left-rail-toggle" type="button" data-left-rail-toggle aria-controls="lri-left-drawer" aria-expanded="${String(!this.leftRailCollapsed)}" aria-label="${escapeHtml(this.leftRailCollapsed ? leftRailLabels.expand : leftRailLabels.collapse)}" title="${escapeHtml(this.leftRailCollapsed ? leftRailLabels.expand : leftRailLabels.collapse)}">${this.leftRailCollapsed ? '›' : '‹'}</button></div><div class="rail-title">${cloudPage ? (this.locale === 'en' ? 'On this page' : '本页目录') : escapeHtml(labels.left_role || '')}</div><slot name="left">${leftNavigation}</slot><div class="left-resizer" data-left-rail-resizer role="separator" tabindex="0" aria-orientation="vertical" aria-label="${escapeHtml(leftRailLabels.resize)}" aria-valuemin="${leftRailMinWidth}" aria-valuemax="${leftRailMaxWidth}" aria-valuenow="${this.leftRailWidth}"></div></aside>
        <section class="content"><slot name="content"></slot></section>
        <aside class="right" id="lri-right-drawer"><div class="drawer-head"><b>${escapeHtml(labels.evidence_drawer || labels.right_role || '')}</b><button class="drawer-close" type="button" data-drawer-close aria-label="${escapeHtml(labels.close_drawer || '')}">×</button></div><div class="right-rail-controls"><button class="right-rail-button right-rail-toggle" type="button" data-right-rail-toggle aria-controls="lri-right-drawer" aria-expanded="${String(!this.rightRailCollapsed)}" aria-label="${escapeHtml(this.rightRailCollapsed ? rightRailLabels.expand : rightRailLabels.collapse)}" title="${escapeHtml(this.rightRailCollapsed ? rightRailLabels.expand : rightRailLabels.collapse)}">${this.rightRailCollapsed ? '‹' : '›'}</button></div><div class="rail-title">${escapeHtml(labels.right_role || '')}</div>${directViewStatus}<slot name="right"><div class="panel"><span class="badge">${escapeHtml(labels.current || '')}</span><h3>${escapeHtml(currentPageLabel)}</h3><p class="muted">${escapeHtml(document.location.pathname)}</p></div><div class="panel"><h3>${escapeHtml(labels.evidence || '')}</h3>${contextLinks}</div><div class="panel"><h3>${escapeHtml(labels.status || '')}</h3><p>${escapeHtml(labels.source_language || '')}: <b>${hasPagePack ? escapeHtml(translationLabel) : escapeHtml(labels.source_only || '')}</b></p></div></slot></aside>
        <footer><span>LRI Web Component Shell</span><span>locale=${escapeHtml(this.locale)}</span><span>path=${escapeHtml(document.location.pathname)}</span><span>component=assets/lri-shell.js</span></footer>
      </div>`;
  }

  bind() {
    this.shadowRoot.querySelectorAll('[data-cloud-domain]').forEach(link => link.addEventListener('click', event => {
      event.preventDefault(); document.querySelector('.wb-domain-tabs [data-domain="'+link.dataset.cloudDomain+'"]')?.click(); this.closeDrawer({restoreFocus:false}); this.refreshSections(); document.getElementById('channels-panel')?.scrollIntoView({block:'start'});
    }));
    this.shadowRoot.querySelectorAll('[data-cloud-view]').forEach(link => link.addEventListener('click', event => {
      const target = document.querySelector('.wb-view-tabs a[data-view="' + link.dataset.cloudView + '"]');
      if (target) { event.preventDefault(); target.click(); this.refreshSections(); }
    }));
    this.shadowRoot.querySelectorAll('[data-locale]').forEach((button) => {
      button.addEventListener('click', () => this.applyLocale(button.dataset.locale));
    });
    this.shadowRoot.querySelector('[data-force-refresh]')?.addEventListener('click', () => this.forceRefresh());
    this.shadowRoot.querySelectorAll('[data-shell-section]').forEach((anchor) => {
      anchor.addEventListener('click', () => {
        const id = anchor.dataset.shellSection;
        if (id === 'top') window.scrollTo({ top: 0, behavior: 'smooth' });
        this.closeDrawer({ restoreFocus: false });
      });
    });
    this.shadowRoot.querySelectorAll('[data-drawer-open]').forEach((button) => {
      button.addEventListener('click', () => this.openDrawer(button.dataset.drawerOpen, button));
    });
    this.shadowRoot.querySelectorAll('[data-drawer-close]').forEach((button) => {
      button.addEventListener('click', () => this.closeDrawer());
    });
    this.shadowRoot.querySelector('[data-left-rail-toggle]')?.addEventListener('click', () => this.setLeftRailCollapsed(!this.leftRailCollapsed));
    this.shadowRoot.querySelector('[data-right-rail-toggle]')?.addEventListener('click', () => this.setRightRailCollapsed(!this.rightRailCollapsed));
    const closeTechintelMobileNav = (event) => { if (matchMedia('(max-width: 760px)').matches && event.target.closest('.workspace-path a,.section-path a')) this.removeAttribute('data-mobile-drawer'); };
    this.shadowRoot.addEventListener('click', closeTechintelMobileNav);
    this.shadowRoot.querySelector('[data-left-rail-reset]')?.addEventListener('click', () => this.setLeftRailWidth(leftRailDefaultWidth));
    const leftResizer = this.shadowRoot.querySelector('[data-left-rail-resizer]');
    leftResizer?.addEventListener('pointerdown', (event) => this.beginLeftRailResize(event, leftResizer));
    leftResizer?.addEventListener('pointermove', (event) => this.moveLeftRailResize(event));
    leftResizer?.addEventListener('pointerup', (event) => this.finishLeftRailResize(event, leftResizer));
    leftResizer?.addEventListener('pointercancel', (event) => this.finishLeftRailResize(event, leftResizer));
    leftResizer?.addEventListener('keydown', (event) => this.adjustLeftRailFromKeyboard(event));
    leftResizer?.addEventListener('dblclick', () => this.setLeftRailWidth(leftRailDefaultWidth));
    this.syncLeftRailState();
    this.syncRightRailState();
  }

  refreshSections() {
    this.sections = collectPageSections(this.locale, this.labels());
    this.contextLinks = collectContextLinks(this.locale);
    if (!this.config) return;
    this.render();
    this.bind();
    this.updateDrawerState();
    this.observeSections();
  }


  async forceRefresh() {
    if (this.forceRefreshActive) return;
    this.forceRefreshActive = true;
    const labels = this.labels();
    const button = this.shadowRoot.querySelector('[data-force-refresh]');
    const status = this.shadowRoot.querySelector('[data-refresh-status]');
    if (button) {
      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      button.setAttribute('aria-label', labels.refreshing || labels.force_refresh || 'Refreshing');
      button.title = labels.refreshing || labels.force_refresh || 'Refreshing';
    }
    if (status) status.textContent = labels.refreshing || 'Refreshing';
    document.dispatchEvent(new CustomEvent('lri:force-refresh-start'));
    const next = new URL(document.location.href);
    next.searchParams.set(forceRefreshParam, Date.now().toString(36));
    const cleanup = Promise.allSettled([
      clearOriginCacheStorage(),
      resetOriginServiceWorkers()
    ]);
    await Promise.all([
      Promise.race([cleanup, delay(2200)]),
      delay(280)
    ]);
    document.dispatchEvent(new CustomEvent('lri:force-refresh-ready'));
    document.location.replace(next.href);
  }

  drawerMode(side) {
    return side === 'left'
      ? window.matchMedia('(max-width: 760px)').matches
      : this.dataset.contentKind === 'session'
        || this.dataset.contentKind === 'resource-registry'
        || window.matchMedia('(max-width: 1050px)').matches;
  }

  lockDocumentScroll() {
    if (document.documentElement.dataset.lriDrawerLocked === 'true') return;
    this.previousDocumentOverflow = document.documentElement.style.overflow;
    document.documentElement.style.overflow = 'hidden';
    document.documentElement.dataset.lriDrawerLocked = 'true';
  }

  unlockDocumentScroll() {
    if (document.documentElement.dataset.lriDrawerLocked !== 'true') return;
    document.documentElement.style.overflow = this.previousDocumentOverflow;
    delete document.documentElement.dataset.lriDrawerLocked;
  }

  openDrawer(side, trigger) {
    if (!this.drawerMode(side)) return;
    this.mobileDrawer = side;
    this.lastDrawerTrigger = trigger || null;
    this.setAttribute('data-mobile-drawer', side);
    this.lockDocumentScroll();
    this.updateDrawerState();
    requestAnimationFrame(() => this.shadowRoot.querySelector(`.${side} [data-drawer-close]`)?.focus());
  }

  closeDrawer({ restoreFocus = true } = {}) {
    const trigger = this.lastDrawerTrigger;
    this.mobileDrawer = null;
    this.lastDrawerTrigger = null;
    this.removeAttribute('data-mobile-drawer');
    this.unlockDocumentScroll();
    this.updateDrawerState();
    if (restoreFocus) requestAnimationFrame(() => trigger?.focus());
  }

  updateDrawerState() {
    const leftCompact = this.drawerMode('left');
    const rightCompact = this.drawerMode('right');
    const leftOpen = leftCompact && this.mobileDrawer === 'left';
    const rightOpen = rightCompact && this.mobileDrawer === 'right';
    const left = this.shadowRoot.querySelector('.left');
    const right = this.shadowRoot.querySelector('.right');
    const backdrop = this.shadowRoot.querySelector('.backdrop');
    const content = this.shadowRoot.querySelector('.content');
    const header = this.shadowRoot.querySelector('header');
    const footer = this.shadowRoot.querySelector('footer');
    const drawerOpen = leftOpen || rightOpen;
    if (left) left.setAttribute('aria-hidden', leftCompact && !leftOpen ? 'true' : 'false');
    if (right) right.setAttribute('aria-hidden', rightCompact && !rightOpen ? 'true' : 'false');
    if (left) {
      left.toggleAttribute('inert', leftCompact ? !leftOpen : rightOpen);
      if (leftOpen) { left.setAttribute('role', 'dialog'); left.setAttribute('aria-modal', 'true'); }
      else { left.removeAttribute('role'); left.removeAttribute('aria-modal'); }
    }
    if (right) {
      right.toggleAttribute('inert', rightCompact ? !rightOpen : leftOpen);
      if (rightOpen) { right.setAttribute('role', 'dialog'); right.setAttribute('aria-modal', 'true'); }
      else { right.removeAttribute('role'); right.removeAttribute('aria-modal'); }
    }
    content?.toggleAttribute('inert', drawerOpen);
    header?.toggleAttribute('inert', drawerOpen);
    footer?.toggleAttribute('inert', drawerOpen);
    this.shadowRoot.querySelector('[data-drawer-open="left"]')?.setAttribute('aria-expanded', String(leftOpen));
    this.shadowRoot.querySelector('[data-drawer-open="right"]')?.setAttribute('aria-expanded', String(rightOpen));
    if (backdrop) backdrop.setAttribute('aria-hidden', String(!(leftOpen || rightOpen)));
  }

  focusableInDrawer(side) {
    const drawer = this.shadowRoot.querySelector(`.${side}`);
    if (!drawer) return [];
    const selector = 'a[href],button:not([disabled]),[tabindex]:not([tabindex="-1"])';
    const result = Array.from(drawer.querySelectorAll(selector));
    drawer.querySelectorAll('slot').forEach((slot) => {
      slot.assignedElements({ flatten: true }).forEach((element) => {
        if (element.matches?.(selector)) result.push(element);
        result.push(...element.querySelectorAll?.(selector) || []);
      });
    });
    return result.filter((element) => element.getClientRects().length > 0);
  }

  onKeydown(event) {
    if (!this.mobileDrawer) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      this.closeDrawer();
      return;
    }
    if (event.key !== 'Tab') return;
    const focusable = this.focusableInDrawer(this.mobileDrawer);
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = event.composedPath()[0] || this.shadowRoot.activeElement || document.activeElement;
    if (event.shiftKey && active === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  }

  onResize() {
    if (this.mobileDrawer && !this.drawerMode(this.mobileDrawer)) this.closeDrawer({ restoreFocus: false });
    else this.updateDrawerState();
  }

  onLightDomClick(event) {
    if (!this.mobileDrawer) return;
    const anchor = event.composedPath().find((node) => node?.tagName === 'A');
    if (anchor) this.closeDrawer({ restoreFocus: false });
  }

  async applyPageLocale(locale, epoch) {
    const template = pageLocaleTemplate();
    if (!template) return false;
    const url = new URL(template.replace('{lang}', locale), document.location.href);
    const response = await fetch(url, { cache: 'no-store' });
    if (!response.ok) throw new Error(`page locale load failed: ${response.status} ${url}`);
    const pack = await response.json();
    if (epoch !== this.localeRequestEpoch) return false;
    if (pack.page_title) document.title = pack.page_title;
    Object.entries(pack.strings || {}).forEach(([key, value]) => {
      document.querySelectorAll(`[data-i18n-key="${CSS.escape(key)}"]`).forEach((node) => { node.textContent = value; });
    });
    Object.entries(pack.dom || {}).forEach(([selector, value]) => {
      document.querySelectorAll(selector).forEach((node) => {
        if (typeof value === 'string') node.textContent = value;
        else if (value && typeof value === 'object') {
          if (value.text != null) node.textContent = value.text;
          if (value.html != null) node.innerHTML = value.html;
          Object.entries(value.attrs || {}).forEach(([name, attrValue]) => node.setAttribute(name, attrValue));
        }
      });
    });
    return true;
  }

  async applyLocale(locale, { announce = true } = {}) {
    const epoch = ++this.localeRequestEpoch;
    this.closeDrawer({ restoreFocus: false });
    this.locale = normalizeLocale(locale);
    const shellLang = this.locale === 'en' ? 'en' : 'zh-CN';
    this.setAttribute('lang', shellLang);
    localStorage.setItem(localeStorageKey, this.locale);
    document.documentElement.lang = (pageTranslationLevel() === 'content' || document.documentElement.dataset.lriAutoTranslate === 'true') ? shellLang : this.sourceDocumentLang;
    this.sections = collectPageSections(this.locale, this.labels());
    this.contextLinks = collectContextLinks(this.locale);
    this.render();
    this.bind();
    this.updateDrawerState();
    this.observeSections();
    if (announce) document.dispatchEvent(new CustomEvent('lri:locale-change', { detail: { locale: this.locale } }));
    try {
      await this.applyPageLocale(this.locale, epoch);
    } catch (error) {
      console.warn('LRI page locale unavailable', error);
    }
    if (epoch === this.localeRequestEpoch && document.documentElement.dataset.lriAutoTranslate === 'true') {
      try {
        const runtime = await loadTranslationRuntime();
        await runtime.applyDocumentLocale(this.locale, { sourceLanguage: runtime.sourceLanguageForDocument(document) });
      } catch (error) {
        console.warn('LRI automatic translation unavailable', error);
      }
    }
    if (epoch !== this.localeRequestEpoch) return;
    if (window.InsightTopicI18n?.setLocale) {
      window.InsightTopicI18n.setLocale(this.locale).catch?.((error) => console.warn('topic locale switch failed', error));
    }
    this.sections = collectPageSections(this.locale, this.labels());
    this.contextLinks = collectContextLinks(this.locale);
    this.render();
    this.bind();
    this.updateDrawerState();
    this.observeSections();
  }

  observeSections() {
    this.observer?.disconnect();
    const links = new Map(Array.from(this.shadowRoot.querySelectorAll('[data-shell-section]')).map((node) => [node.dataset.shellSection, node]));
    const targets = this.sections.map(({ id }) => document.getElementById(id)).filter(Boolean);
    if (!targets.length || !('IntersectionObserver' in window)) return;
    this.observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible) return;
      links.forEach((node) => node.classList.remove('is-current'));
      const active = links.get(visible.target.id);
      if (active) active.classList.add('is-current');
    }, { rootMargin: '-20% 0px -65% 0px', threshold: [0, .2, .6] });
    targets.forEach((target) => this.observer.observe(target));
  }
}

customElements.define('lri-site-shell', LRISiteShell);

function applyContentAdapter(shell, node, kind) {
  const normalized = kind || 'generic';
  shell.dataset.contentKind = normalized;
  document.body.dataset.lriContentKind = normalized;
  if (!node) return;
  node.classList.add('lri-content-adapter', `lri-${normalized}-adapter`);
  node.dataset.lriContentKind = normalized;
}

function upgradePage() {
  if (document.body?.dataset?.lriShell === 'off' || document.querySelector('lri-site-shell')) return;
  const main = document.querySelector('body > main') || document.querySelector('main');
  if (!main) return;
  const shell = document.createElement('lri-site-shell');
  main.parentNode.insertBefore(shell, main);
  if (main.classList.contains('topic-shell')) {
    const left = main.querySelector(':scope > .topic-shell-left');
    const center = main.querySelector(':scope > .topic-shell-center');
    const right = main.querySelector(':scope > .topic-shell-right');
    if (left) { left.slot = 'left'; shell.appendChild(left); }
    if (center) { applyContentAdapter(shell, center, 'topic'); center.slot = 'content'; shell.appendChild(center); }
    else { applyContentAdapter(shell, main, 'topic'); main.slot = 'content'; shell.appendChild(main); return; }
    if (right) { right.slot = 'right'; shell.appendChild(right); }
    main.remove();
  } else if (main.classList.contains('session-ide-shell')) {
    const left = main.querySelector(':scope > .session-ide-left');
    const right = main.querySelector(':scope > .session-ide-right');
    if (left && right) {
      const legacyTop = main.querySelector(':scope > .session-ide-top');
      const legacyStatus = main.querySelector(':scope > .session-ide-status');
      const mobileShortcut = main.querySelector(':scope > .mobile-session-card-shortcut');
      [legacyTop, legacyStatus, mobileShortcut].filter(Boolean).forEach((node) => {
        node.hidden = true;
        node.classList.add('lri-shell-suppressed');
        node.setAttribute('aria-hidden', 'true');
      });
      // WWDC originally owned its own complete IDE shell. Keep the router/content
      // implementation, but let lri-site-shell own the page chrome.
      left.slot = 'left';
      right.slot = 'right';
      shell.appendChild(left);
      const contentHost = document.createElement('div');
      contentHost.className = 'lri-wwdc-content-host lri-session-adapted';
      applyContentAdapter(shell, contentHost, 'session');
      while (main.firstChild) {
        const node = main.firstChild;
        if (node === left || node === right || node === legacyTop || node === legacyStatus || node === mobileShortcut) {
          main.removeChild(node);
          continue;
        }
        contentHost.appendChild(node);
      }
      contentHost.slot = 'content';
      shell.appendChild(contentHost);
      shell.appendChild(right);
      main.remove();
    } else {
      applyContentAdapter(shell, main, 'session');
      main.slot = 'content';
      shell.appendChild(main);
    }
  } else {
    const declaredKind = document.body?.dataset?.lriContentKind;
    const allowedKinds = new Set(['generic', 'page', 'report', 'topic', 'session', 'resource-registry']);
    const kind = allowedKinds.has(declaredKind)
      ? declaredKind
      : main.classList.contains('report-brief')
        ? 'report'
        : main.classList.contains('page')
          ? 'page'
          : main.classList.contains('topic-workspace')
            ? 'report'
            : main.classList.contains('wrap')
            ? 'report'
            : 'generic';
    applyContentAdapter(shell, main, kind);
    main.slot = 'content';
    shell.appendChild(main);
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', upgradePage, { once: true });
else upgradePage();



