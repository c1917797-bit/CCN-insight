(function () {
  const root = document.documentElement;
  const body = document.body;
  const topicId = body?.dataset?.topicId || 'topic';
  const localeBase = body?.dataset?.i18nLocaleBase || 'data';
  const storageKey = body?.dataset?.i18nStorageKey || `${topicId}_locale`;
  const globalStorageKey = 'lri_locale';
  const defaultLocale = body?.dataset?.i18nDefaultLang || 'zh';
  const state = { locale: null, pack: null, facts: null, entities: null, dataKeys: null };
  const q = (sel) => document.querySelector(sel);
  const qa = (sel) => Array.from(document.querySelectorAll(sel));
  const esc = (v) => String(v == null ? '' : v).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const safeHref = (value) => {
    const href = String(value || '').trim();
    return /^(https?:\/\/|\/)/i.test(href) ? href : '';
  };
  const list = (items) => `<ul>${(items || []).map(x => `<li>${esc(x)}</li>`).join('')}</ul>`;
  const table = (headers, rows) => `<div class="table-wrap"><table><thead><tr>${headers.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${row.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  const card = (item, labelKey) => `<article class="card"><span class="label">${esc(item[labelKey] || item.tier || item.track || item.layer || '')}</span><h3>${esc(item.name || item.title || item.capability || item.risk || item.direction || item.gap || '')}</h3><p>${esc(item.description || item.summary || item.gap || item.next_action || '')}</p>${item.questions ? list(item.questions) : ''}</article>`;
  const compact = (value) => Array.isArray(value) ? value.join(' / ') : (value && typeof value === 'object' ? Object.entries(value).map(([k, v]) => `${k}: ${compact(v)}`).join(' · ') : String(value == null ? '' : value));
  const recordCard = (item, fallback) => {
    if (typeof item !== 'object' || item == null) return `<article class="callout"><p>${esc(item)}</p></article>`;
    const title = item.name || item.title || item.resource || item.direction || item.layer || item.id || item.priority || fallback;
    const label = item.tier || item.region || item.status || item.evidence_grade || item.type || '';
    const body = item.description || item.summary || item.rationale || item.why || item.fit || item.gap || item.next_action || item.boundary || '';
    const details = Object.entries(item).filter(([key, value]) => !['name','title','resource','direction','layer','id','priority','tier','region','status','evidence_grade','type','description','summary','rationale','why','fit','gap','next_action','boundary'].includes(key) && value != null && value !== '').slice(0, 4);
    return `<article class="card"><span class="label">${esc(label)}</span><h3>${esc(title)}</h3><p>${esc(body)}</p>${details.length ? `<p><small>${details.map(([k,v]) => `${esc(k)}: ${esc(compact(v))}`).join('<br>')}</small></p>` : ''}</article>`;
  };
  const renderCards = (selector, items, fallback) => {
    const target = q(selector);
    if (target) target.innerHTML = (items || []).map((item, i) => recordCard(item, `${fallback} ${i + 1}`)).join('');
  };
  const renderObject = (selector, value) => {
    const target = q(selector);
    if (!target) return;
    const entries = value && typeof value === 'object' ? Object.entries(value) : [];
    target.innerHTML = entries.length ? `<div class="stats">${entries.map(([key, item]) => `<div class="stat"><b>${esc(compact(item))}</b><span>${esc(key)}</span></div>`).join('')}</div>` : '';
  };
  const refIds = (item, kind) => Array.isArray(item?.$refs?.[kind]) ? item.$refs[kind] : [];
  const referenced = (item, kind) => refIds(item, kind).map(id => state.entities?.[kind]?.[id]).filter(Boolean);
  const capabilityView = item => {
    const capability = referenced(item, 'capabilities')[0];
    const resources = referenced(item, 'resources');
    const relations = referenced(item, 'resource_capabilities');
    return {
      name: capability?.name || item.capability || item.name || '',
      description: capability?.description || '',
      resources: resources.map(resource => resource.name || resource.display_name || resource.resource_id),
      evidence: relations.length ? relations.map(relation => relation.evidence_status).join(' / ') : (item.evidence_grade || 'candidate'),
    };
  };
  const resourceView = item => {
    const resource = referenced(item, 'resources')[0];
    return {
      name: resource?.name || item.name || item.resource || '',
      kind: resource?.resource_kind || item.type || '',
      summary: item.value || item.description || resource?.summary || '',
    };
  };
  const contentView = item => {
    const content = referenced(item, 'contents')[0];
    const primary = content?.locations?.find(location => location.is_primary) || content?.locations?.[0];
    return {
      title: content?.title || item.title || '',
      url: safeHref(primary?.url),
      language: content?.language || '',
      grade: item.grade || '',
      summary: item.summary || '',
    };
  };

  function setText(selector, value) {
    const el = q(selector);
    if (el && value != null) el.textContent = String(value);
  }
  function sectionTitle(id, title, desc) {
    const h = q(`#${id} .section-title h2`);
    const p = q(`#${id} .section-title p`);
    if (h && title) h.textContent = title;
    if (p && desc) p.textContent = desc;
  }
  function updateNav(pack) {
    const labels = pack.path_labels || {};
    qa('[data-section-id]').forEach(a => {
      const id = a.getAttribute('data-section-id');
      const no = a.getAttribute('data-section-index') || '';
      const label = labels[id];
      const b = a.querySelector('b');
      if (label && b) b.textContent = `${no} · ${label}`;
      if (label) a.setAttribute('data-section-label', label);
    });
    const nav = pack.nav || {};
    const top = qa('.topic-shell-global a');
    const keys = ['home', 'wwdc', 'russia', 'ai', 'games', 'intent'];
    top.forEach((a, i) => { if (nav[keys[i]]) a.textContent = nav[keys[i]]; });
  }
  async function loadTopicData() {
    if (!window.LRITableGit?.loadTopicWorkbench || !window.LRITableGit?.materializeTopicWorkbench) {
      throw new Error('canonical TableGit topic provider is unavailable');
    }
    const snapshot = await window.LRITableGit.loadTopicWorkbench(topicId);
    return window.LRITableGit.materializeTopicWorkbench(snapshot, state.locale);
  }
  function renderPack(pack) {
    state.pack = pack;
    root.lang = pack.locale === 'en' ? 'en' : 'zh-CN';
    document.title = pack.topic?.title || pack.page_title || document.title;
    setText('.topic-shell-brand b', pack.topic?.title);
    setText('.topic-shell-brand small', pack.topic?.subtitle);
    setText('#overview h1', pack.topic?.title);
    const leads = qa('#overview .lead');
    if (leads[0] && pack.topic?.goal) leads[0].textContent = pack.topic.goal;
    if (leads[1] && pack.topic?.scope_line) leads[1].textContent = pack.topic.scope_line;
    setText('[data-i18n-contract-note]', pack.topic?.contract_note);
    updateNav(pack);
    Object.entries(pack.sections || {}).forEach(([id, pair]) => sectionTitle(id, pair[0], pair[1]));
    const map = q('#map .topic-map');
    if (map && pack.overview_map) map.innerHTML = pack.overview_map.map(m => `<article class="topic-map-node"><span>${esc(m.layer)}</span><h3>${esc(m.title)}</h3><p>${esc(m.description)}</p></article>`).join('');
    const tracks = q('#tracks .grid-3');
    if (tracks && pack.tracks) tracks.innerHTML = pack.tracks.map(t => card(t, 'name')).join('');
    const architecture = q('[data-render="architecture_layers"]');
    if (architecture && pack.architecture_layers) architecture.innerHTML = pack.architecture_layers.map(x => `<article class="card"><span class="label">${esc(x.layer || 'Layer')}</span><h3>${esc(x.name || '')}</h3><p>${esc(x.description || '')}</p><p><b>Control:</b> ${esc(x.control || '')}</p></article>`).join('');
    const metrics = q('[data-render="metric_framework"]');
    if (metrics && pack.metric_framework) metrics.innerHTML = table(
      [pack.tables.dimension || 'Dimension', pack.tables.metric || 'Metric', pack.tables.definition || 'Definition', pack.tables.why || 'Why', pack.tables.direction || 'Direction'],
      pack.metric_framework.map(x => [x.dimension, x.metric, x.definition, x.why, x.direction])
    );
    const antiMetrics = q('[data-render="anti_metrics"]');
    if (antiMetrics && pack.anti_metrics) antiMetrics.innerHTML = pack.anti_metrics.map(x => `<article class="callout"><h3>${esc(x.name || '')}</h3><p>${esc(x.reason || '')}</p></article>`).join('');
    const maturity = q('[data-render="maturity_model"]');
    if (maturity && pack.maturity_model) maturity.innerHTML = pack.maturity_model.map(x => `<article class="card"><span class="label">${esc(x.level || '')}</span><h3>${esc(x.name || '')}</h3><p>${esc(x.description || '')}</p><p><b>Flow:</b> ${esc(x.control_flow || '')}</p><p><b>Exit:</b> ${esc(x.exit_criteria || '')}</p></article>`).join('');
    const calculations = q('[data-render="metric_calculation"]');
    if (calculations && pack.metric_calculation) calculations.innerHTML = table(
      [pack.tables.metric || 'Metric', pack.tables.formula || 'Formula', pack.tables.data_sources || 'Data sources', pack.tables.granularity || 'Granularity', pack.tables.caveat || 'Caveat'],
      pack.metric_calculation.map(x => [x.metric, x.formula, x.data_sources, x.granularity, x.caveat])
    );
    const rollout = q('[data-render="rollout_plan"]');
    if (rollout && pack.rollout_plan) rollout.innerHTML = pack.rollout_plan.map(x => `<article class="callout"><span class="label">${esc(x.phase || '')}</span><h3>${esc(x.name || '')}</h3><p>${esc(x.description || '')}</p><p><b>Gate:</b> ${esc(x.gate || '')}</p></article>`).join('');
    const tiers = q('#tiers .grid-4');
    if (tiers && pack.resource_tiers) tiers.innerHTML = pack.resource_tiers.map(t => card(t, 'tier')).join('');
    const caps = q('#capabilities [data-render="capabilities"]') || q('#capabilities .table-wrap');
    const capabilityRows = pack.capabilities || pack.capability_matrix || [];
    if (caps && capabilityRows.length) caps.innerHTML = table(
      [pack.tables.capability, pack.tables.track, pack.tables.resources, pack.tables.evidence, pack.tables.gap],
      capabilityRows.map(c => {
        const resolved = capabilityView(c);
        return [resolved.name, c.track, resolved.resources.length ? resolved.resources.join(' / ') : (c.primary_resources || []).join(' / '), resolved.evidence, c.gap || resolved.description];
      })
    );
    const collab = q('#collaboration .grid-2');
    if (collab && pack.collaboration_directions) collab.innerHTML = pack.collaboration_directions.map(x => `<article class="callout"><h3>${esc(x.direction)}</h3><p><b>${esc(x.geo_focus)}</b> · ${esc(x.region_scope)}</p><p>${esc(x.suitable_for)}</p><div class="grid-2"><div><h3>Resources</h3>${list(x.candidate_resources)}</div><div><h3>Forms</h3>${list(x.cooperation_forms)}</div></div><p><b>Boundary:</b> ${esc(x.boundary)}</p></article>`).join('');
    const gaps = q('#gaps .grid-4');
    if (gaps && pack.evidence_gaps) gaps.innerHTML = pack.evidence_gaps.map(g => `<article class="callout"><h3>${esc(g.severity)} · ${esc(g.gap)}</h3><p><b>${esc(g.owner_track)}</b></p><p>${esc(g.next_action)}</p></article>`).join('');
    const risks = q('#risks .grid-3');
    const riskRows = pack.risks || pack.risk_register || [];
    if (risks && riskRows.length) risks.innerHTML = riskRows.map(r => card(r, 'risk')).join('');
    const ev = q('#evidence [data-render="evidence_sources"]') || q('#evidence .table-wrap');
    if (ev && pack.evidence_sources) ev.innerHTML = `<div class="grid-3">${pack.evidence_sources.map(source => {
      const resolved = contentView(source);
      const title = resolved.url ? `<a href="${esc(resolved.url)}" target="_blank" rel="noopener">${esc(resolved.title)}</a>` : esc(resolved.title);
      return `<article class="card"><span class="label">${esc(resolved.grade)} · ${esc(resolved.language)}</span><h3>${title}</h3><p>${esc(resolved.summary)}</p></article>`;
    }).join('')}</div>`;
    const next = q('#next .grid-4');
    if (next && pack.next_steps) next.innerHTML = pack.next_steps.map((x, i) => `<div class="callout"><h3>${i+1}. ${esc(pack.path_labels?.next || 'Next')}</h3><p>${esc(compact(x))}</p></div>`).join('');
    qa('[data-lang]').forEach(btn => btn.setAttribute('aria-pressed', btn.dataset.lang === state.locale ? 'true' : 'false'));
    localStorage.setItem(storageKey, state.locale);
    localStorage.setItem(globalStorageKey, state.locale);
    document.dispatchEvent(new CustomEvent('topic-i18n:rendered', { detail: { topicId, locale: state.locale } }));
  }

  function renderIntentEngineeringSections(pack, facts) {
    const labels = pack.tables || {};
    const samples = facts.intent_tool_mcp_samples || [];
    const sampleWrap = q('[data-intent-tool-samples]');
    if (sampleWrap && samples.length) {
      const h = q('[data-intent-tool-samples-title] h3');
      const p = q('[data-intent-tool-samples-title] p');
      const pair = pack.sections?.['intent-tool-samples'];
      if (h && pair?.[0]) h.textContent = pair[0];
      if (p && pair?.[1]) p.textContent = pair[1];
      sampleWrap.innerHTML = table([labels.sample_id || 'Sample', labels.intent || 'Intent', labels.utterance || 'Utterance', labels.tool_schema || 'Tool schema', labels.mcp_route || 'MCP route', labels.permission_gate || 'Permission gate', labels.risk_boundary || 'Risk boundary'], samples.map(x => [x.sample_id, x.intent, pack.locale === 'en' ? x.user_utterance_en : x.user_utterance_zh, x.tool_schema, x.mcp_route, x.permission_gate, pack.locale === 'en' ? (x.risk_boundary_en || x.risk_boundary) : (x.risk_boundary_zh || x.risk_boundary)]));
    }
    const evals = facts.intent_evaluation_matrix || [];
    const evalWrap = q('[data-intent-eval-matrix]');
    if (evalWrap && evals.length) {
      const h = q('[data-intent-eval-matrix-title] h3');
      const p = q('[data-intent-eval-matrix-title] p');
      const pair = pack.sections?.['intent-eval-matrix'];
      if (h && pair?.[0]) h.textContent = pair[0];
      if (p && pair?.[1]) p.textContent = pair[1];
      evalWrap.innerHTML = table([labels.metric || 'Metric', labels.question || 'Question', labels.positive_signal || 'Positive signal', labels.failure_signal || 'Failure signal', labels.sample_refs || 'Sample refs'], evals.map(x => [x.metric, pack.locale === 'en' ? (x.question_en || x.question) : (x.question_zh || x.question), pack.locale === 'en' ? (x.positive_signal_en || x.positive_signal) : (x.positive_signal_zh || x.positive_signal), pack.locale === 'en' ? (x.failure_signal_en || x.failure_signal) : (x.failure_signal_zh || x.failure_signal), (x.sample_refs || []).join(' / ')]));
    }

    const contracts = facts.intent_contracts || [];
    const contractsWrap = q('[data-intent-contracts]');
    if (contractsWrap && contracts.length) {
      const h = q('[data-intent-contracts-title] h3');
      const p = q('[data-intent-contracts-title] p');
      const pair = pack.sections?.['intent-contracts'];
      if (h && pair?.[0]) h.textContent = pair[0];
      if (p && pair?.[1]) p.textContent = pair[1];
      contractsWrap.innerHTML = table([labels.intent_id || 'Intent ID', labels.user_goal || 'User goal', labels.required_slots || 'Required slots', labels.candidate_tools || 'Candidate tools', labels.permission_level || 'Permission level', labels.evidence_required || 'Required evidence', labels.rejection_policy || 'Reject/clarify policy'], contracts.map(x => [x.intent_id, pack.locale === 'en' ? x.user_goal_en : x.user_goal_zh, (x.required_slots || []).join(' / '), (x.candidate_tools || []).join(' / '), x.permission_level, (x.evidence_required || []).join(' / '), pack.locale === 'en' ? x.rejection_policy_en : x.rejection_policy_zh]));
    }
    const routes = facts.tool_routing_matrix || [];
    const routesWrap = q('[data-tool-routing]');
    if (routesWrap && routes.length) {
      const h = q('[data-tool-routing-title] h3');
      const p = q('[data-tool-routing-title] p');
      const pair = pack.sections?.['tool-routing'];
      if (h && pair?.[0]) h.textContent = pair[0];
      if (p && pair?.[1]) p.textContent = pair[1];
      routesWrap.innerHTML = table([labels.intent_id || 'Intent ID', labels.primary_tool || 'Primary tool', labels.fallback_tool || 'Fallback tool', labels.routing_reason || 'Routing reason'], routes.map(x => [x.intent_id, x.primary_tool, x.fallback_tool, pack.locale === 'en' ? x.routing_reason_en : x.routing_reason_zh]));
    }
    const gates = facts.permission_gate_matrix || [];
    const gatesWrap = q('[data-permission-gates]');
    if (gatesWrap && gates.length) {
      const h = q('[data-permission-gates-title] h3');
      const p = q('[data-permission-gates-title] p');
      const pair = pack.sections?.['permission-gates'];
      if (h && pair?.[0]) h.textContent = pair[0];
      if (p && pair?.[1]) p.textContent = pair[1];
      gatesWrap.innerHTML = table([labels.permission_level || 'Permission level', labels.allowed_actions || 'Allowed actions', labels.blocked_actions || 'Blocked actions', labels.confirmation_rule || 'Confirmation rule'], gates.map(x => [x.permission_level, (x.allowed_actions || []).join(' / '), (x.blocked_actions || []).join(' / '), pack.locale === 'en' ? x.confirmation_rule_en : x.confirmation_rule_zh]));
    }
    const logs = facts.evidence_log_matrix || [];
    const logsWrap = q('[data-evidence-logs]');
    if (logsWrap && logs.length) {
      const h = q('[data-evidence-logs-title] h3');
      const p = q('[data-evidence-logs-title] p');
      const pair = pack.sections?.['evidence-logs'];
      if (h && pair?.[0]) h.textContent = pair[0];
      if (p && pair?.[1]) p.textContent = pair[1];
      logsWrap.innerHTML = table([labels.log_type || 'Log type', labels.required_fields || 'Required fields', labels.used_by || 'Used by', labels.failure_if_missing || 'Failure if missing'], logs.map(x => [x.log_type, (x.required_fields || []).join(' / '), (x.used_by || []).join(' / '), pack.locale === 'en' ? x.failure_if_missing_en : x.failure_if_missing_zh]));
    }
  }

  function renderIntentResourceSections(pack) {
    const labels = pack.tables || {};
    const region = q('[data-render="region_scope"]');
    if (region) {
      const scope = pack.region_scope || {};
      region.innerHTML = `<div class="callout"><h3>${esc(scope.name || '')}</h3><p>${esc((scope.countries || []).join(' / '))}</p><p>${esc(scope.rule || '')}</p></div>`;
    }
    const tiers = q('[data-render="tier_taxonomy"]');
    if (tiers) tiers.innerHTML = (pack.tier_taxonomy || []).map(x => `<article class="card"><span class="label">${esc(x.tier)}</span><h3>${esc(x.scope)}</h3><p>${esc(x.definition)}</p><p><b>Rule:</b> ${esc(x.cooperation_rule)}</p></article>`).join('');
    const thesis = q('[data-render="thesis"]');
    if (thesis) thesis.innerHTML = (pack.thesis || []).map(x => `<article class="card"><span class="label">Insight</span><h3>${esc(x.claim)}</h3><p>${esc(x.summary)}</p><p><b>Evidence:</b> ${esc(x.evidence_grade)}</p></article>`).join('');
    const synthesis = q('[data-render="insight_synthesis"]');
    if (synthesis) synthesis.innerHTML = (pack.insight_synthesis || []).map((x, i) => `<div class="callout"><h3>Insight ${i + 1}</h3><p>${esc(x)}</p></div>`).join('');
    const assets = q('[data-render="assets"]');
    if (assets) {
      const rows = [
        ...(pack.research_assets || []).map(x => ({...x, kind: 'Research'})),
        ...(pack.commercial_assets || []).map(x => ({...x, kind: 'Commercial'})),
      ];
      assets.innerHTML = rows.map(x => `<article class="card"><span class="label">${esc(x.kind)}</span><h3>${esc(x.name)}</h3><p>${esc(x.description)}</p><p><b>Evidence:</b> ${esc(x.evidence_grade)}</p></article>`).join('');
    }
    const breadth = q('[data-render="resource_breadth_map"]');
    if (breadth) breadth.innerHTML = table(
      [labels.resource || 'Resource', labels.tier || 'Tier', labels.region || 'Region', labels.type || 'Type', labels.status || 'Status', labels.fit || 'Fit'],
      (pack.resource_breadth_map || []).map(x => [x.name, x.tier, x.region, x.asset_type, x.evidence_status, x.cooperation_fit])
    );
    const depth = q('[data-render="resource_depth_matrix"]');
    if (depth) depth.innerHTML = table(
      [labels.resource || 'Resource', labels.tier || 'Tier', labels.region || 'Region', labels.evidence || 'Evidence', labels.depth_status || 'Depth', labels.fit || 'Fit'],
      (pack.resource_depth_matrix || []).map(x => [x.resource, x.tier, x.region, x.evidence_strength, x.depth_level, x.cooperation_fit])
    );
    const profiles = q('[data-render="resource_profiles"]');
    if (profiles) profiles.innerHTML = (pack.resource_profiles || []).map(x => {
      const resolved = resourceView(x);
      return `<article class="card"><span class="label">${esc(x.depth || x.status || resolved.kind)}</span><h3>${esc(resolved.name)}</h3><p>${esc(x.track || '')} ${esc(x.tier || '')} ${esc(x.region || '')}</p><p>${esc(resolved.summary)}</p><p><b>Value chain:</b> ${esc((x.value_chain || []).join(' → '))}</p><p><b>Gap:</b> ${esc((x.gaps || []).join(' / '))}</p><p><b>Risk:</b> ${esc((x.risk_notes || []).join(' / '))}</p></article>`;
    }).join('');
    const scorecards = q('[data-render="resource_scorecards"]');
    if (scorecards) scorecards.innerHTML = (pack.resource_scorecards || []).map(x => `<article class="card"><span class="label">${esc(x.priority)}</span><h3>${esc(x.resource)}</h3><p>${esc(x.fit)}</p><p>${esc(x.rationale)}</p><div class="stats"><div class="stat"><b>${esc(x.evidence_strength)}</b><span>Evidence</span></div><div class="stat"><b>${esc(x.strategic_impact)}</b><span>Impact</span></div><div class="stat"><b>${esc(x.accessibility)}</b><span>Access</span></div><div class="stat"><b>${esc(x.risk_level)}</b><span>Risk</span></div></div></article>`).join('');
    const quick = q('[data-render="quick_tracks"]');
    if (quick) quick.innerHTML = (pack.tracks || []).map(x => `<a class="topic-path-link" href="#tracks"><b>${esc(x.name)}</b><span>${esc(x.description)}</span></a>`).join('');
    const sourceLinks = q('[data-render="right_sources"]');
    if (sourceLinks) sourceLinks.innerHTML = `<ul>${(pack.evidence_sources || []).slice(0, 4).map(x => {
      const resolved = contentView(x);
      return `<li>${esc(resolved.title)}<small>${esc(resolved.grade)} · ${esc(resolved.language)}</small></li>`;
    }).join('')}</ul>`;
    const rightRisks = q('[data-render="right_risks"]');
    if (rightRisks) rightRisks.innerHTML = list((pack.risks || pack.risk_register || []).slice(0, 4).map(x => x.risk || x.title || x.name));
    const status = q('[data-render="right_status"]');
    if (status) {
      const coverage = pack.resource_coverage_summary || {};
      status.innerHTML = `<p>schema: ${esc(state.facts?.schema || '—')}</p><p>last verified: ${esc(state.facts?.topic?.last_verified || '—')}</p><p>resource breadth: ${esc(coverage.breadth_count ?? '—')}</p><p>resource depth: ${esc(coverage.depth_count ?? '—')}</p><p><a href="/__mcpgit/tables/topic_workbench_items">TableGit</a></p>`;
    }
    renderCards('[data-render="resource_insight_layers"]', pack.resource_insight_layers, 'Insight layer');
    renderCards('[data-render="resource_whitespace_map"]', pack.resource_whitespace_map, 'Whitespace');
    renderCards('[data-render="resource_strategy_synthesis"]', pack.resource_strategy_synthesis, 'Strategy');
    renderCards('[data-render="resource_evidence_upgrade_queue"]', pack.resource_evidence_upgrade_queue, 'Evidence upgrade');
    renderCards('[data-render="resource_expansion_backlog"]', pack.resource_expansion_backlog, 'Expansion');
    renderCards('[data-render="resource_deep_dive_cards"]', pack.resource_deep_dive_cards, 'Deep dive');
    renderCards('[data-render="organization_mirrors"]', pack.organization_mirrors, 'Organization');
    renderObject('[data-render="resource_coverage_summary"]', pack.resource_coverage_summary);
    renderObject('[data-render="resource_portfolio_dashboard"]', pack.resource_portfolio_dashboard);
    const official = q('[data-render="official_sources"]');
    if (official && (pack.official_sources || []).length) official.innerHTML = table(
      [labels.source || 'Source', labels.grade || 'Grade', labels.summary || 'Use'],
      pack.official_sources.map(x => [x.title || x.name || x.url, x.grade || x.evidence_grade || 'Official', x.summary || x.description || x.url])
    );
  }

  const dedicatedCollections = new Set([
    'overview_map','tracks','resource_tiers','capability_matrix','capabilities','collaboration_directions',
    'evidence_gaps','risks','risk_register','evidence_sources','next_steps','tier_taxonomy','thesis',
    'insight_synthesis','research_assets','commercial_assets','resource_breadth_map','resource_depth_matrix',
    'resource_profiles','resource_scorecards','resource_insight_layers','resource_whitespace_map',
    'resource_strategy_synthesis','resource_evidence_upgrade_queue','resource_expansion_backlog',
    'resource_deep_dive_cards','organization_mirrors','official_sources','architecture_layers','metric_framework','anti_metrics','maturity_model','metric_calculation','rollout_plan'
  ]);
  function renderUnmappedData(pack) {
    const target = q('[data-render="unmapped_data"]');
    if (!target || !state.dataKeys) return;
    const blocks = [];
    for (const key of state.dataKeys.collections) {
      const rows = pack[key];
      if (dedicatedCollections.has(key) || !Array.isArray(rows) || !rows.length) continue;
      blocks.push(`<section class="callout"><h3>${esc(key.replaceAll('_', ' '))}</h3><div class="grid-2">${rows.map((row, i) => recordCard(row, `${key} ${i + 1}`)).join('')}</div></section>`);
    }
    for (const key of state.dataKeys.objects) {
      const value = pack[key];
      if (value == null || dedicatedCollections.has(key)) continue;
      blocks.push(`<section class="callout"><h3>${esc(key.replaceAll('_', ' '))}</h3>${recordCard(value, key)}</section>`);
    }
    target.innerHTML = blocks.join('');
  }

  async function setLocale(lang) {
    state.locale = lang === 'en' ? 'en' : 'zh';
    const res = await fetch(`${localeBase}/ui.${state.locale}.json`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`locale ${state.locale} load failed: ${res.status}`);
    const localePack = await res.json();
    if (document.body?.dataset.topicRuntimeState === 'scaffold-pending') {
      const pendingNote = q('[data-topic-pending-note] p')?.textContent?.trim() || '';
      const topic = {
        title: localePack.page_title || document.title,
        summary: pendingNote,
        contract_note: localePack.topic?.contract_note,
      };
      state.facts = {schema: 'lri.topic-scaffold/v1', status: 'pending_tablegit_population'};
      state.entities = {};
      state.dataKeys = {collections: [], objects: []};
      renderPack({...localePack, topic});
      return;
    }
    const topicData = await loadTopicData();
    const reservedUiKeys = new Set(['locale', 'page_title', 'topic', 'nav', 'path_labels', 'path_groups', 'sections', 'tables', 'buttons']);
    const collisions = [...Object.keys(topicData.collections), ...Object.keys(topicData.objects)].filter(key => reservedUiKeys.has(key));
    if (collisions.length) throw new Error(`topic business data collides with reserved UI keys: ${[...new Set(collisions)].sort().join(',')}`);
    const topic = {...topicData.topic, contract_note: localePack.topic?.contract_note};
    const pack = {...localePack, ...topicData.collections, ...topicData.objects, topic};
    state.facts = topicData.facts;
    state.entities = topicData.entities;
    state.dataKeys = {collections: Object.keys(topicData.collections), objects: Object.keys(topicData.objects)};
    renderPack(pack);
    renderIntentResourceSections(pack);
    renderIntentEngineeringSections(pack, pack);
    renderUnmappedData(pack);
  }
  function init() {
    qa('[data-lang]').forEach(btn => btn.addEventListener('click', () => setLocale(btn.dataset.lang).catch(err => console.error('topic i18n switch failed', err))));
    document.addEventListener('lri:locale-change', (event) => {
      const locale = event.detail?.locale;
      if (locale && locale !== state.locale) setLocale(locale).catch(err => console.error('topic i18n sync failed', err));
    });
    const requested = new URLSearchParams(location.search).get('lang');
    const saved = localStorage.getItem(globalStorageKey) || localStorage.getItem(storageKey);
    setLocale(requested === 'en' || requested === 'zh' ? requested : (saved || defaultLocale)).catch(err => console.error('topic i18n load failed', err));
  }
  window.InsightTopicI18n = { setLocale, state };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
