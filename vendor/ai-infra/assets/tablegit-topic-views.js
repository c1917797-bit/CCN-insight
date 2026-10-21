(() => {
  'use strict';

  const script = document.currentScript;
  const configUrl = new URL('tablegit-topic-views.json', script?.src || location.href);
  const topicId = document.body?.dataset?.topicId || '';
  const state = { config: null, view: '', locale: 'zh', query: '', deckIndex: 0 };
  const q = selector => document.querySelector(selector);
  const qa = selector => Array.from(document.querySelectorAll(selector));
  const esc = value => String(value == null ? '' : value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const compact = value => Array.isArray(value)
    ? value.map(compact).filter(Boolean).join(' / ')
    : value && typeof value === 'object'
      ? Object.entries(value).slice(0, 8).map(([key, item]) => `${key}: ${compact(item)}`).join(' · ')
      : String(value == null ? '' : value);
  const humanize = value => String(value || '').replaceAll('__', ' / ').replaceAll('_', ' ').replaceAll('-', ' ');
  const localized = value => value?.[state.locale] || value?.zh || value?.en || '';
  const rows = key => Array.isArray(window.InsightTopicI18n?.state?.pack?.[key]) ? window.InsightTopicI18n.state.pack[key] : [];
  const object = key => {
    const value = window.InsightTopicI18n?.state?.pack?.[key];
    return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
  };
  const refs = (row, kind) => Array.isArray(row?.$refs?.[kind]) ? row.$refs[kind] : [];
  const contentFor = row => refs(row, 'contents').map(id => window.InsightTopicI18n?.state?.entities?.contents?.[id]).find(Boolean);
  const safeHref = value => /^(?:https?:\/\/|\/)/i.test(String(value || '').trim()) ? String(value).trim() : '';
  const labels = () => state.locale === 'en' ? {
    records: 'records', collections: 'collections', revision: 'revision', filter: 'Filter this view', empty: 'No matching records', source: 'Open source', previous: 'Previous', next: 'Next', current: 'Focused views', judgement: 'Judgement', goal: 'Question', evidence: 'Evidence', decision: 'Decision / action', boundary: 'Boundary', speaker: 'Speaker note', visual: 'Visual grammar', section: 'Section', page: 'Page', deliverable: 'Deliverable', priority: 'Priority issues', nodes: 'Resource nodes', relations: 'Evidence relations', degree: 'Relations' 
  } : {
    records: '条记录', collections: '个集合', revision: '修订', filter: '筛选当前视图', empty: '没有匹配记录', source: '打开来源', previous: '上一页', next: '下一页', current: '专题视图', judgement: '核心判断', goal: '本页问题', evidence: '证据', decision: '决策 / 行动', boundary: '证据边界', speaker: '讲述逻辑', visual: '视觉语法', section: '章节', page: '页', deliverable: '预期产物', priority: 'P0 议题', nodes: '资源节点', relations: '证据关系', degree: '关系数' 
  };

  function searchable(row) {
    return JSON.stringify(row).toLocaleLowerCase();
  }

  function matchRow(row, config) {
    if (config.match && !Object.entries(config.match).every(([key, value]) => row?.[key] === value)) return false;
    return !state.query || searchable(row).includes(state.query.toLocaleLowerCase());
  }

  function recordCard(row, fallback) {
    if (!row || typeof row !== 'object') return `<article class="callout"><p>${esc(row)}</p></article>`;
    const content = contentFor(row);
    const primary = content?.locations?.find(item => item.is_primary) || content?.locations?.[0];
    const href = safeHref(primary?.url || row.url || row.source_url || row.paper_url || row.session_url);
    const title = row.title || row.name || row.claim || row.capability || row.resource || row.issue || row.id || row.slug || fallback;
    const body = row.summary || row.description || row.rationale || row.overview || row.goal || row.finding || row.gap || row.next_action || row.boundary || '';
    const label = row.status || row.evidence_grade || row.tier || row.priority || row.type || row.track || '';
    const hidden = new Set(['title','name','claim','capability','resource','issue','id','slug','summary','description','rationale','overview','goal','finding','gap','next_action','boundary','status','evidence_grade','tier','priority','type','track','$refs']);
    const details = Object.entries(row).filter(([key, value]) => !hidden.has(key) && value != null && value !== '').slice(0, 6);
    return `<article class="card tablegit-focused-card"><span class="label">${esc(label)}</span><h3>${esc(title)}</h3>${body ? `<p>${esc(body)}</p>` : ''}${details.length ? `<dl>${details.map(([key,value]) => `<div><dt>${esc(humanize(key))}</dt><dd>${esc(compact(value))}</dd></div>`).join('')}</dl>` : ''}${href ? `<p><a href="${esc(href)}" target="_blank" rel="noopener">${esc(content?.title || labels().source)} ↗</a></p>` : ''}</article>`;
  }

  function selectedRecords(config) {
    const entries = [];
    for (const key of config.collections || []) {
      for (const row of rows(key).filter(item => matchRow(item, config))) entries.push({key, row});
    }
    for (const key of config.objects || []) {
      const row = object(key);
      if (row && matchRow(row, config)) entries.push({key, row});
    }
    return entries;
  }

  function renderSections(config) {
    const blocks = [];
    for (const key of config.collections || []) {
      const items = rows(key).filter(row => matchRow(row, config));
      if (!items.length) continue;
      blocks.push(`<section class="callout tablegit-focused-block"><div class="section-title"><div><h3>${esc(humanize(key))}</h3><p>${items.length} ${esc(labels().records)}</p></div></div><div class="grid-2">${items.map((row,index) => recordCard(row, `${humanize(key)} ${index + 1}`)).join('')}</div></section>`);
    }
    for (const key of config.objects || []) {
      const value = object(key);
      if (!value || !matchRow(value, config)) continue;
      blocks.push(`<section class="callout tablegit-focused-block"><div class="section-title"><div><h3>${esc(humanize(key))}</h3><p>1 ${esc(labels().records)}</p></div></div>${recordCard(value, humanize(key))}</section>`);
    }
    return blocks.join('') || `<div class="callout"><p>${esc(labels().empty)}</p></div>`;
  }

  function valueFor(row, keys) {
    for (const key of keys) {
      const value = row?.[key];
      if (value != null && value !== '') return value;
    }
    return '';
  }

  function narrative(row, fallback = '') {
    return {
      title: valueFor(row, ['title','name','claim','issue','id']) || fallback,
      judgement: valueFor(row, ['judgement','judgement_zh','claim','finding','summary','description']),
      goal: valueFor(row, ['goal','goal_zh','question','overview']),
      evidence: valueFor(row, ['evidence','evidence_zh']),
      decision: valueFor(row, ['decision','decision_zh','action','action_zh','next_action']),
      boundary: valueFor(row, ['boundary','boundary_zh']),
      speaker: valueFor(row, ['speaker','speaker_zh']),
      visual: valueFor(row, ['visual','visual_zh']),
      status: valueFor(row, ['status','evidence_grade','tier','priority']),
      layout: valueFor(row, ['layout','type','track']),
      page: valueFor(row, ['page']),
      evidenceRefs: Array.isArray(row?.evidence_refs) ? row.evidence_refs : [],
    };
  }

  function narrativeField(label, value, cls = '') {
    if (value == null || value === '') return '';
    return `<article class="tablegit-narrative-field ${esc(cls)}"><span>${esc(label)}</span><p>${esc(compact(value))}</p></article>`;
  }

  function deckControls(position, total) {
    return `<div class="tablegit-focused-deck-controls"><button type="button" data-focused-prev aria-label="${esc(labels().previous)}" ${position <= 0 ? 'disabled' : ''}>←</button><b>${position + 1} / ${total}</b><button type="button" data-focused-next aria-label="${esc(labels().next)}" ${position >= total - 1 ? 'disabled' : ''}>→</button></div>`;
  }

  function renderDeck(config) {
    const entries = selectedRecords(config);
    if (!entries.length) return `<div class="callout"><p>${esc(labels().empty)}</p></div>`;
    state.deckIndex = Math.max(0, Math.min(state.deckIndex, entries.length - 1));
    const current = entries[state.deckIndex];
    return `${deckControls(state.deckIndex, entries.length)}<div class="tablegit-focused-slide"><span class="label">${esc(humanize(current.key))}</span>${recordCard(current.row, `${humanize(current.key)} ${state.deckIndex + 1}`)}</div>`;
  }

  function renderOutlineDeck(config) {
    const key = config.primary_collection || config.collections?.[0];
    const pages = rows(key).filter(row => matchRow(row, config)).sort((a,b) => Number(a.page || 0) - Number(b.page || 0));
    if (!pages.length) return `<div class="callout"><p>${esc(labels().empty)}</p></div>`;
    state.deckIndex = Math.max(0, Math.min(state.deckIndex, pages.length - 1));
    const row = pages[state.deckIndex];
    const story = narrative(row, `${labels().page} ${state.deckIndex + 1}`);
    const refs = story.evidenceRefs.length ? `<div class="tablegit-evidence-chips">${story.evidenceRefs.map(ref => `<span>${esc(ref)}</span>`).join('')}</div>` : '';
    return `${deckControls(state.deckIndex, pages.length)}<article class="tablegit-focused-slide tablegit-narrative-slide" data-layout="${esc(story.layout)}"><header><div class="eyebrow"><span class="pill good">${esc(String(story.page || state.deckIndex + 1).padStart(2,'0'))}</span>${story.layout ? `<span class="pill">${esc(humanize(story.layout))}</span>` : ''}${story.status ? `<span class="pill">${esc(story.status)}</span>` : ''}</div><h2>${esc(story.title)}</h2>${story.judgement ? `<p class="lead">${esc(story.judgement)}</p>` : ''}</header><div class="tablegit-narrative-grid">${narrativeField(labels().goal, story.goal, 'goal')}${narrativeField(labels().evidence, story.evidence, 'evidence')}${narrativeField(labels().decision, story.decision, 'decision')}${narrativeField(labels().boundary, story.boundary, 'boundary')}</div>${story.visual ? `<p class="tablegit-visual-note"><b>${esc(labels().visual)}</b> · ${esc(story.visual)}</p>` : ''}${refs}${story.speaker ? `<footer class="tablegit-speaker-note">${esc(story.speaker)}</footer>` : ''}</article>`;
  }

  function renderCollectionDeck(config) {
    const groups = [];
    for (const key of config.collections || []) {
      const items = rows(key).filter(row => matchRow(row, config));
      if (items.length) groups.push({key, items});
    }
    for (const key of config.objects || []) {
      const item = object(key);
      if (item && matchRow(item, config)) groups.push({key, items:[item]});
    }
    if (!groups.length) return `<div class="callout"><p>${esc(labels().empty)}</p></div>`;
    state.deckIndex = Math.max(0, Math.min(state.deckIndex, groups.length - 1));
    const group = groups[state.deckIndex];
    const preview = group.items.slice(0, 6);
    return `${deckControls(state.deckIndex, groups.length)}<article class="tablegit-focused-slide tablegit-collection-slide"><header><span class="label">${esc(labels().section)} ${String(state.deckIndex + 1).padStart(2,'0')}</span><h2>${esc(humanize(group.key))}</h2><p>${group.items.length} ${esc(labels().records)}</p></header><div class="grid-2 tablegit-collection-slide-grid">${preview.map((row,index) => recordCard(row, `${humanize(group.key)} ${index + 1}`)).join('')}</div>${group.items.length > preview.length ? `<p class="note">+${group.items.length - preview.length} ${esc(labels().records)}</p>` : ''}</article>`;
  }

  function renderInventory(config) {
    const entries = selectedRecords(config);
    if (!entries.length) return `<div class="callout"><p>${esc(labels().empty)}</p></div>`;
    return `<div class="tablegit-focused-inventory">${entries.map(({key,row},index) => `<div class="tablegit-inventory-row"><span class="tablegit-inventory-index">${String(index + 1).padStart(2,'0')}</span><div><span class="label">${esc(humanize(key))}</span>${recordCard(row, `${humanize(key)} ${index + 1}`)}</div></div>`).join('')}</div>`;
  }

  function renderOutline(config) {
    const key = config.primary_collection || config.collections?.[0];
    const pages = rows(key).filter(row => matchRow(row, config)).sort((a,b) => Number(a.page || 0) - Number(b.page || 0));
    if (!pages.length) return `<div class="callout"><p>${esc(labels().empty)}</p></div>`;
    return `<div class="tablegit-focused-outline">${pages.map((row,index) => { const story=narrative(row, `${labels().page} ${index + 1}`); return `<article><div class="tablegit-outline-number">${String(story.page || index + 1).padStart(2,'0')}</div><div><span class="label">${esc(humanize(story.layout || story.status))}</span><h3>${esc(story.title)}</h3>${story.goal ? `<p>${esc(story.goal)}</p>` : ''}${story.judgement ? `<p class="note"><b>${esc(labels().judgement)}:</b> ${esc(story.judgement)}</p>` : ''}${story.visual ? `<p class="note"><b>${esc(labels().visual)}:</b> ${esc(story.visual)}</p>` : ''}</div></article>`; }).join('')}</div>`;
  }

  function renderBriefing(config) {
    const blocks = [];
    let sectionIndex = 0;
    for (const key of config.collections || []) {
      const items = rows(key).filter(row => matchRow(row, config));
      if (!items.length) continue;
      sectionIndex += 1;
      const stories = items.map((row,index) => narrative(row, `${humanize(key)} ${index + 1}`));
      blocks.push(`<section class="tablegit-briefing-section"><header><span class="tablegit-section-number">${String(sectionIndex).padStart(2,'0')}</span><div><h3>${esc(humanize(key))}</h3><p>${items.length} ${esc(labels().records)}</p></div></header><div class="grid-2">${stories.map((story,index) => `<article class="card tablegit-briefing-card"><span class="label">${esc(story.status || story.layout)}</span><h3>${esc(story.title)}</h3>${story.judgement ? `<p class="tablegit-briefing-judgement">${esc(story.judgement)}</p>` : ''}${story.goal && story.goal !== story.judgement ? `<p>${esc(story.goal)}</p>` : ''}${story.evidence ? `<p class="note"><b>${esc(labels().evidence)}:</b> ${esc(story.evidence)}</p>` : ''}${story.decision ? `<p class="note"><b>${esc(labels().decision)}:</b> ${esc(story.decision)}</p>` : ''}${story.boundary ? `<p class="note"><b>${esc(labels().boundary)}:</b> ${esc(story.boundary)}</p>` : ''}${!story.judgement && !story.goal && !story.evidence && !story.decision && !story.boundary ? recordCard(items[index], story.title) : ''}</article>`).join('')}</div></section>`);
    }
    for (const key of config.objects || []) {
      const item=object(key);
      if (!item || !matchRow(item, config)) continue;
      blocks.push(`<section class="tablegit-briefing-section"><header><span class="tablegit-section-number">${String(++sectionIndex).padStart(2,'0')}</span><div><h3>${esc(humanize(key))}</h3></div></header>${recordCard(item, humanize(key))}</section>`);
    }
    return blocks.join('') || `<div class="callout"><p>${esc(labels().empty)}</p></div>`;
  }

  function renderIssueBoard(config) {
    const primary = config.primary_collection || config.collections?.[0];
    const priorities = rows(primary).filter(row => matchRow(row, config));
    const board = priorities.length ? `<section class="tablegit-issue-board"><header><span class="tablegit-section-number">P0</span><div><h3>${esc(labels().priority)}</h3><p>${priorities.length} ${esc(labels().records)}</p></div></header><div class="tablegit-issue-grid">${priorities.map((row,index) => `<article class="card tablegit-issue-card"><span class="tablegit-issue-number">${String(index+1).padStart(2,'0')}</span><h3>${esc(valueFor(row,['topic','title','name']) || `${labels().priority} ${index+1}`)}</h3>${valueFor(row,['deliverable','output','action']) ? `<p><b>${esc(labels().deliverable)}:</b> ${esc(compact(valueFor(row,['deliverable','output','action'])))}</p>` : ''}</article>`).join('')}</div></section>` : '';
    const rest = {...config, collections:(config.collections||[]).filter(key=>key!==primary)};
    return board + renderBriefing(rest);
  }

  function renderGraphMap(config) {
    const nodeKey=config.node_collection;
    const edgeKey=config.edge_collection;
    const nodes=rows(nodeKey).filter(row=>matchRow(row,config));
    const edges=rows(edgeKey).filter(row=>matchRow(row,config));
    if (!nodes.length) return `<div class="callout"><p>${esc(labels().empty)}</p></div>`;
    const degree=new Map();
    for (const edge of edges) {
      for (const id of [edge.source,edge.target]) if (id) degree.set(id,(degree.get(id)||0)+1);
    }
    const groups=new Map();
    for (const row of nodes) { const type=row.type||'other'; if(!groups.has(type)) groups.set(type,[]); groups.get(type).push(row); }
    const typeOrder=['control_plane','platform','standard','open_source','paper','project','claim','other'];
    const ordered=[...groups.entries()].sort((a,b)=>{const ai=typeOrder.indexOf(a[0]),bi=typeOrder.indexOf(b[0]); return (ai<0?99:ai)-(bi<0?99:bi)||a[0].localeCompare(b[0]);});
    const graph=`<section class="tablegit-graph-map"><header><span class="tablegit-section-number">01</span><div><h3>${esc(labels().nodes)}</h3><p>${nodes.length} ${esc(labels().records)} · ${edges.length} ${esc(labels().relations)}</p></div></header><div class="tablegit-node-groups">${ordered.map(([type,list])=>`<section><h4>${esc(humanize(type))}<span>${list.length}</span></h4><div>${list.map(row=>`<article class="tablegit-node-card" data-node-type="${esc(type)}"><b>${esc(row.name||row.id||humanize(type))}</b><small>${esc(row.id||'')}</small><span>${esc(labels().degree)} ${degree.get(row.id)||0}</span></article>`).join('')}</div></section>`).join('')}</div></section>`;
    const relations=edges.length ? `<section class="tablegit-graph-relations"><header><span class="tablegit-section-number">02</span><div><h3>${esc(labels().relations)}</h3><p>${edges.length} ${esc(labels().records)}</p></div></header><div class="tablegit-edge-ledger">${edges.map(edge=>`<article><span class="label">${esc(humanize(edge.type||'relation'))}</span><b>${esc(edge.source||'')}</b><span>→</span><b>${esc(edge.target||'')}</b>${edge.confidence?`<small>${esc(edge.confidence)}</small>`:''}</article>`).join('')}</div></section>` : '';
    const support={...config, collections:(config.collections||[]).filter(key=>key!==nodeKey&&key!==edgeKey)};
    return graph+relations+renderBriefing(support);
  }

  function renderContent(config) {
    if (config.mode === 'outline_deck') return renderOutlineDeck(config);
    if (config.mode === 'collection_deck') return renderCollectionDeck(config);
    if (config.mode === 'inventory') return renderInventory(config);
    if (config.mode === 'outline') return renderOutline(config);
    if (config.mode === 'briefing') return renderBriefing(config);
    if (config.mode === 'issue_board') return renderIssueBoard(config);
    if (config.mode === 'graph_map') return renderGraphMap(config);
    if (config.mode === 'deck') return renderDeck(config);
    return renderSections(config);
  }

  function ensureSection() {
    let section = q('[data-tablegit-focused-view]');
    if (section) return section;
    section = document.createElement('section');
    section.className = 'section tablegit-focused-view';
    section.id = 'focused';
    section.dataset.tablegitFocusedView = '';
    section.innerHTML = '<div class="section-title"><div><h2 data-focused-title></h2><p data-focused-description></p></div><span class="label good">TableGit live</span></div><div class="stats" data-focused-stats></div><div data-focused-toolbar></div><div data-focused-content></div>';
    q('.topic-workspace')?.append(section);
    return section;
  }

  function ensureNavigation(topic) {
    const rail = q('.topic-shell-left');
    if (!rail) return;
    let group = rail.querySelector('[data-tablegit-view-group]');
    if (!group) {
      group = document.createElement('div');
      group.className = 'topic-rail-card tablegit-view-group';
      group.dataset.tablegitViewGroup = '';
      rail.append(group);
    }
    group.innerHTML = `<h3>${esc(labels().current)}</h3><div>${Object.entries(topic.views).map(([id, config]) => `<a class="topic-path-link" href="?view=${encodeURIComponent(id)}#focused" data-focused-route="${esc(id)}"><b>${esc(localized(config.title))}</b></a>`).join('')}</div>`;
  }

  function render() {
    const topic = state.config?.topics?.[topicId];
    if (!topic || !window.InsightTopicI18n?.state?.pack) return;
    state.locale = window.InsightTopicI18n.state.locale || 'zh';
    const requested = new URLSearchParams(location.search).get('view') || '';
    state.view = topic.views[requested] ? requested : '';
    ensureNavigation(topic);
    qa('[data-focused-route]').forEach(link => {
      if (link.dataset.focusedRoute === state.view) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    qa('[data-section-id]').forEach(link => { link.hidden = Boolean(state.view); });
    const focused = ensureSection();
    const ordinary = qa('.topic-workspace > .section').filter(section => section !== focused);
    if (!state.view) {
      focused.hidden = true;
      ordinary.forEach(section => { section.hidden = false; });
      document.body.dataset.tablegitFocusedReady = 'overview';
      return;
    }
    const config = topic.views[state.view];
    focused.hidden = false;
    ordinary.forEach(section => { section.hidden = true; });
    q('[data-focused-title]').textContent = localized(config.title);
    q('[data-focused-description]').textContent = localized(config.description);
    document.title = `${localized(config.title)} · LRI Insight`;
    const entries = selectedRecords(config);
    const revision = window.LRITableGit?.source?.(`topic-workbench:${topicId}`)?.revision || '';
    q('[data-focused-stats]').innerHTML = `<div class="stat"><b>${entries.length}</b><span>${esc(labels().records)}</span></div><div class="stat"><b>${(config.collections || []).length + (config.objects || []).length}</b><span>${esc(labels().collections)}</span></div>${revision ? `<div class="stat"><b>${esc(revision.slice(0, 12))}</b><span>${esc(labels().revision)}</span></div>` : ''}`;
    const toolbar = q('[data-focused-toolbar]');
    toolbar.innerHTML = config.search ? `<label class="tablegit-focused-search"><span>${esc(labels().filter)}</span><input type="search" value="${esc(state.query)}" data-focused-search></label>` : '';
    const content = q('[data-focused-content]');
    content.innerHTML = renderContent(config);
    toolbar.querySelector('[data-focused-search]')?.addEventListener('input', event => {
      state.query = event.target.value;
      content.innerHTML = renderContent(config);
    });
    content.querySelector('[data-focused-prev]')?.addEventListener('click', () => { state.deckIndex -= 1; render(); });
    content.querySelector('[data-focused-next]')?.addEventListener('click', () => { state.deckIndex += 1; render(); });
    document.body.dataset.tablegitFocusedReady = state.view;
    document.dispatchEvent(new CustomEvent('tablegit-topic-view:rendered', {detail:{topicId, view:state.view, locale:state.locale, records:entries.length}}));
  }

  fetch(configUrl, {cache: 'no-store'}).then(response => {
    if (!response.ok) throw new Error(`topic view config load failed: ${response.status}`);
    return response.json();
  }).then(config => {
    state.config = config;
    render();
  }).catch(error => console.error(error));
  document.addEventListener('topic-i18n:rendered', render);
  window.addEventListener('popstate', render);
  window.TableGitTopicViews = {state, render};
})();
