(() => {
  'use strict';
  // Presentation only. Editorial narratives and every fact are revisioned native rows.
  const cache = new Map();
  let current = null;
  const allowedReviews = new Set(['primary_abstract_checked', 'method_results_checked']);
  const check = (ok, message) => { if (!ok) throw new Error(message); };
  const pick = (row, field, locale) => row[field + '_' + locale] || row[field + '_zh'] || '';
  const t = (zh, en) => current?.locale === 'en' ? en : zh;
  const node = (tag, text = '', cls = '') => {
    const out = document.createElement(tag); out.textContent = text; if (cls) out.className = cls; return out;
  };
  function safeUrl(value) {
    const url = new URL(value); check(url.protocol === 'https:' && !url.username && !url.password, 'Unsafe source URL');
    return url.href;
  }
  function mount() {
    let root = document.getElementById('monthly-route-report');
    if (!root) {
      const evidence = document.getElementById('evidence-status');
      if (!evidence) return null;
      root = node('section', '', 'monthly-route-report'); root.id = 'monthly-route-report';
      evidence.parentNode.insertBefore(root, evidence.previousElementSibling);
    }
    return root;
  }
  function status(text, retry = false) {
    const root = mount(); if (!root) return; root.replaceChildren();
    const p = node('p', text, 'meta'); p.setAttribute('role', 'status'); root.append(p);
    if (retry) {
      const button = node('button', t('重试加载', 'Retry loading'), 'btn'); button.type = 'button';
      button.addEventListener('click', () => { if (current) refresh({...current}, true); }); root.append(button);
    }
  }
  function validateRevision(result, revision) {
    check(result.revision === revision || result.source?.revision === revision, 'Monthly route revision mismatch');
    check(Array.isArray(result.records), 'Invalid monthly route records'); return result.records;
  }
  function business(rows) {
    check(rows.every(r => r.business_id === 'cloud-core' && r.topic_id === 'cloud_core'), 'Cross-business route row'); return rows;
  }
  async function scoped(table, field, value, revision) {
    const rows = []; let offset = 0, total;
    for (;;) {
      const result = await LRITableGit.loadTablePage(table, {filterField:field,filterValue:value,offset,limit:100,expectedRevision:revision});
      const batch = business(validateRevision(result, revision)), meta = result.page;
      check(meta && Number.isSafeInteger(meta.total) && meta.total >= 0 && meta.total <= 2000, 'Unbounded monthly route scope');
      if (total == null) total = meta.total; check(total === meta.total, 'Changing monthly route total');
      rows.push(...batch);
      if (!meta.truncated) { check(rows.length === total, 'Incomplete monthly routes'); return rows; }
      check(batch.length && meta.nextOffset === offset + batch.length, 'Invalid monthly route cursor'); offset = meta.nextOffset;
    }
  }
  function validateModel(stories, refs, summaries, sources, context) {
    const storyIds = new Set(), refIds = new Set(), topics = new Set(context.topics.map(x => x.compression_topic_id));
    const reviewMap = new Map(summaries.map(x => [x.summary_id, x])), sourceMap = new Map(sources.map(x => [x.source_id, x]));
    for (const row of stories) {
      check(!storyIds.has(row.story_id), 'Duplicate monthly route'); storyIds.add(row.story_id);
      check(row.scope_id === context.scope && row.period_id === context.period && row.claim_status === 'analyst_synthesis', 'Wrong monthly narrative scope');
      for (const field of ['title','question','context','synthesis','viewpoint','boundary','implication']) check(pick(row, field, 'zh').trim(), 'Incomplete route narrative');
    }
    for (const row of refs) {
      check(!refIds.has(row.ref_id), 'Duplicate route evidence'); refIds.add(row.ref_id);
      check(storyIds.has(row.story_id) && topics.has(row.compression_topic_id), 'Unknown route/topic association');
      check(row.scope_id === context.scope && row.period_id === context.period, 'Wrong route evidence scope');
      check(context.associations.some(x => x.evidence_id === row.evidence_id && x.source_id === row.source_id &&
        x.compression_topic_id === row.compression_topic_id && x.period_id === context.period && x.scope_id === context.scope &&
        x.review_status === 'primary_review'), 'Unreviewed or unmapped route evidence');
      const summary = reviewMap.get(row.summary_id), source = sourceMap.get(row.source_id);
      check(summary && source && summary.source_id === row.source_id && summary.observed_version === row.observed_version &&
        row.summary_id === row.source_id + '__' + row.observed_version && /^v\d+$/.test(row.observed_version) &&
        allowedReviews.has(summary.review_status), 'Unbound paper version');
      check(summary.evidence_locator && summary.reviewed_at && summary.one_sentence_zh && summary.innovation_zh && summary.results_zh, 'Incomplete reviewed paper');
      const reviewed = safeUrl(summary.evidence_url), canonical = safeUrl(source.canonical_url);
      const id = canonical.match(/arxiv\.org\/(?:abs|html)\/(\d{4}\.\d{4,5})/);
      check(id && reviewed.includes('/' + id[1] + row.observed_version), 'Wrong canonical paper citation');
    }
    check(stories.every(x => refs.some(r => r.story_id === x.story_id)), 'Narrative without direct evidence');
    return {stories, refs, reviewMap, sourceMap};
  }
  async function load(context) {
    const [stories, refs] = await Promise.all([
      scoped('ic_monthly_route_insights', 'scope_id', context.scope, context.revision),
      scoped('ic_monthly_route_evidence', 'scope_id', context.scope, context.revision),
    ]);
    if (!stories.length) { check(!refs.length, 'Orphan route evidence'); return {stories:[],refs:[],reviewMap:new Map(),sourceMap:new Map()}; }
    const summaryIds = [...new Set(refs.map(x => x.summary_id))], sourceIds = [...new Set(refs.map(x => x.source_id))];
    const evidenceIds = [...new Set(refs.map(x => x.evidence_id))];
    const [summaryResult, sourceResult, bindingResult, eventResult] = await Promise.all([
      LRITableGit.loadRowsByKeys('ic_paper_summaries', summaryIds, context.revision),
      LRITableGit.loadRowsByKeys('cloud_core_sources', sourceIds, context.revision, ['source_id','business_id','title','canonical_url']),
      LRITableGit.loadRowsByKeys('ic_paper_summary_events', evidenceIds, context.revision),
      LRITableGit.loadRowsByKeys('ic_evidence_items', evidenceIds, context.revision),
    ]);
    const summaries = business(validateRevision(summaryResult, context.revision)), sources = validateRevision(sourceResult, context.revision);
    check(summaries.length === summaryIds.length && sources.length === sourceIds.length && sources.every(x => x.business_id === 'cloud-core'), 'Missing route evidence');
    const bindings = business(validateRevision(bindingResult, context.revision)), events = business(validateRevision(eventResult, context.revision));
    check(bindings.length === evidenceIds.length && events.length === evidenceIds.length, 'Missing route event version');
    for (const ref of refs) {
      const binding = bindings.find(x => x.evidence_id === ref.evidence_id), event = events.find(x => x.evidence_id === ref.evidence_id);
      check(binding && event && binding.summary_id === ref.summary_id && binding.observed_version === ref.observed_version &&
        binding.source_id === ref.source_id && binding.period_id === context.period && event.source_id === ref.source_id &&
        event.observed_version === ref.observed_version && event.event_date?.slice(0,7) === context.period, 'Wrong monthly event version');
    }
    const keywordIds=summaries.flatMap(row=>{check(Number.isSafeInteger(row.keyword_count)&&row.keyword_count>=1&&row.keyword_count<=8,'Invalid keyword contract');return Array.from({length:row.keyword_count},(_,i)=>row.summary_id+'__'+i);});
    const keywords=[];
    for(let i=0;i<keywordIds.length;i+=100){const result=await LRITableGit.loadRowsByKeys('ic_paper_summary_keywords',keywordIds.slice(i,i+100),context.revision);keywords.push(...business(validateRevision(result,context.revision)));}
    check(keywords.length===keywordIds.length&&new Set(keywords.map(r=>r.keyword_id)).size===keywordIds.length&&keywords.every(r=>keywordIds.includes(r.keyword_id)&&r.keyword_id===r.summary_id+'__'+r.position&&r.keyword_zh?.trim()),'Missing or mismatched paper keywords');
    return {...validateModel(stories, refs, summaries, sources, context), keywordMap:new Map(summaries.map(s=>[s.summary_id,keywords.filter(k=>k.summary_id===s.summary_id).sort((a,b)=>a.position-b.position)])),eventMap:new Map(events.map(x=>[x.evidence_id,x]))};
  }
  function citation(parent, summary, text) {
    const link = node('a', text, 'monthly-route-citation'); link.href = safeUrl(summary.evidence_url);
    link.target = '_blank'; link.rel = 'noopener noreferrer'; link.title = summary.evidence_locator;
    parent.append(document.createTextNode(' '), link);
  }
  function paragraph(parent, label, text, cls = '') {
    const p = node('p', '', cls); p.append(node('strong', label + '：'), document.createTextNode(text)); parent.append(p); return p;
  }
  function paperFields(parent, summary, model, id, {compact=false}={}) {
    const keywords=(model.keywordMap.get(id)||[]).map(k=>pick(k,'keyword',current.locale));
    const tags=node('div','','monthly-paper-keywords');tags.setAttribute('aria-label',t('关键词','Keywords'));
    tags.append(node('strong',t('关键词','Keywords')));for(const word of keywords)tags.append(node('span',word));parent.append(tags);
    const fields=node('dl','','monthly-paper-fields');
    const selected=compact?[['innovation','技术增量','Technical increment'],['results','原文结果与测试条件','Reported results and conditions']]:[['background','背景介绍','Background'],['innovation','技术和创新点','Technology and innovation'],['results','效果总结','Results and conditions']];
    for(const [field,zh,en] of selected){
      const block=node('div');block.dataset.summaryField=field;block.append(node('dt',t(zh,en)),node('dd',pick(summary,field,current.locale)));fields.append(block);
    }parent.append(fields);
  }
  function topicLink(id) {
    const topic = current.topics.find(x => x.compression_topic_id === id);
    const a = node('a', pick(topic || {}, 'name', current.locale) || pick(topic || {}, 'title', current.locale) || id, 'monthly-route-topic');
    const url = new URL('topic.html', location.href); url.searchParams.set('topic', id); url.searchParams.set('month', current.period); url.searchParams.set('scope', current.scope);
    url.hash = 'research-overview-solutions'; a.href = url.pathname + url.search + url.hash; a.dataset.monthlyTopic = id; return a;
  }


  function storyTopics(story, model) {
    const ids=new Set(model.refs.filter(ref=>ref.story_id===story.story_id).map(ref=>ref.compression_topic_id));
    return current.topics.filter(topic=>ids.has(topic.compression_topic_id)).sort((a,b)=>a.position-b.position||a.compression_topic_id.localeCompare(b.compression_topic_id));
  }
  function storyMapLabel(story, model) {
    const groups=new Map(),other=[];
    for(const topic of storyTopics(story,model)){
      const name=pick(topic,'name',current.locale)||pick(topic,'title',current.locale)||topic.compression_topic_id,parts=name.split(/\s*×\s*/);
      if(parts.length!==2){other.push(name);continue;}
      if(topic.catalog_kind!=='matrix'){const method=parts[1].startsWith(parts[0]+' ')?parts[1].slice(parts[0].length+1):parts[1];other.push(parts[0]+' × '+method+t('（扩展专题）',' (additional topic)'));continue;}
      if(!groups.has(parts[0]))groups.set(parts[0],[]);
      if(!groups.get(parts[0]).includes(parts[1]))groups.get(parts[0]).push(parts[1]);
    }
    return [...groups].map(([target,methods])=>target+' × '+methods.join(' / ')).concat(other).join('；');
  }
  function routeHeading(story,model,tag='h4') {
    const heading=node(tag),label=storyMapLabel(story,model);
    const annotation=node('span',t('（',' (')+label+t('）',')'),'monthly-route-map-label');
    const link=node('a',pick(story,'title',current.locale));link.href=readerUrl(story.story_id);link.dataset.monthlyReader='true';heading.append(link,annotation);
    return heading;
  }

  function readerUrl(story='',paper='') {
    const url=new URL('monthly.html',location.href);url.searchParams.set('month',current.period);url.searchParams.set('scope',current.scope);url.searchParams.set('v','58');if(current.topicId)url.searchParams.set('topic',current.topicId);
    if(story)url.searchParams.set('route',story);if(paper)url.searchParams.set('paper',paper);
    url.hash='monthly-route-report';return url.pathname+url.search+url.hash;
  }
  document.addEventListener('click',event=>{
    if(document.body.dataset.compressionMonthly!=='true')return;
    const link=(event.composedPath?.()||[event.target]).find(n=>n?.tagName==='A'&&n.dataset.monthlyReader);
    if(!link||!current)return;event.preventDefault();history.pushState(null,'',link.getAttribute('href'));refresh({...current});document.getElementById('monthly-route-report')?.scrollIntoView({block:'start'});
  });
  window.addEventListener('popstate',()=>{if(document.body.dataset.compressionMonthly==='true'&&current)refresh({...current});});
  function renderRouteDiagram(parent,story,dedup,model){
    const figure=node('figure','','monthly-evidence-diagram');figure.setAttribute('aria-label',t('本路线的方案、事实与边界','Methods, facts and boundaries for this route'));
    figure.append(node('h4',t('技术方案与实验结果','Methods and experimental results')));
    const problem=node('div','','monthly-diagram-problem');problem.append(node('strong',t('研究问题','Research question')),node('p',pick(story,'question',current.locale)));figure.append(problem);
    const methods=node('div','','monthly-diagram-methods');
    for(const ref of dedup.values()){
      const summary=model.reviewMap.get(ref.summary_id),source=model.sourceMap.get(ref.source_id),card=node('article');
      card.append(node('span',t('原文方案 · ','Published method · ')+ref.observed_version,'topic-dossier-type'),node('h5',source.title),node('p',pick(summary,'innovation',current.locale)));
      const proof=node('details');proof.append(node('summary',t('效果与实验条件','Results and experimental conditions')),node('p',pick(summary,'results',current.locale)));card.append(proof);
      citation(card,summary,t('原文依据 ↗','Primary source ↗'));methods.append(card);
    }figure.append(methods);
    const boundary=node('div','','monthly-diagram-boundary');boundary.append(node('strong',t('比较条件与局限','Comparison conditions and limitations')),node('p',pick(story,'boundary',current.locale)));figure.append(boundary);
    figure.append(node('figcaption',t('以下方案回答同一研究问题；尚未验证组合使用的效果。','These methods address the same research question; their combined effects have not been validated.')));parent.append(figure);
  }
  function chapter(tag,id,label,level=3,fold=false) {
    const el=node(tag); el.id=id;el.setAttribute('data-section-id',id);
    el.setAttribute('data-section-label',label);el.setAttribute('data-section-label-en',label);
    el.setAttribute('data-section-level',String(level));
    if(fold)el.setAttribute('data-section-collapsible','true');
    return el;
  }
  function notifyOutline() { document.dispatchEvent(new Event('lri:sections-changed')); }
  function render(model) {
    const root=mount();if(!root||!current)return;root.replaceChildren();
    root.setAttribute('data-section-label',t('学术进展','Academic updates'));
    root.setAttribute('data-section-label-en','Academic updates');root.setAttribute('data-section-level','3');
    const selectedRoute=new URLSearchParams(location.search).get('route'),selectedPaper=new URLSearchParams(location.search).get('paper'),detail=document.body.dataset.compressionMonthly==='true';
    const relevant=model.stories.filter(s=>(!current.topicId||model.refs.some(r=>r.story_id===s.story_id&&r.compression_topic_id===current.topicId))&&(!detail||(!selectedRoute||s.story_id===selectedRoute)&&(!selectedPaper||model.refs.some(r=>r.story_id===s.story_id&&r.summary_id===selectedPaper)))).sort((a,b)=>a.position-b.position||a.story_id.localeCompare(b.story_id));
    root.dataset.readerMode=detail?'detail':'overview';
    const activeTopic=current.topics.find(topic=>topic.compression_topic_id===current.topicId);
    root.append(node('h2',current.period+' · '+(activeTopic?(pick(activeTopic,'name',current.locale)||pick(activeTopic,'title',current.locale))+t(' · 本期动态',' · Current updates'):t('学术进展','Academic updates'))));
    root.append(node('p',t('按技术地图查看本月论文进展：解决了什么问题、采用什么方法、效果如何。点击动态标题阅读全文，点击专题标签查看基础原理与长期研究。','Follow this month’s papers by technology-map topic: the problem, the method and the results. Open an update for the full review, or a topic for foundations and ongoing research.'),'meta'));
    const path=node('ol','','insight-reading-chain');
    for(const [zh,en] of [['本月事件','Monthly events'],['技术增量','Technical increments'],['原文结果','Reported results'],['进入专题','Open the topic']])path.append(node('li',t(zh,en)));if(detail&&!selectedPaper)root.append(path);
    if(!detail){document.getElementById('monthly-key-changes')?.replaceChildren();const metric=document.getElementById('monthly-academic-metric');if(metric)metric.textContent='0';const cutoff=document.getElementById('monthly-review-cutoff');if(cutoff)cutoff.textContent=t('当前筛选范围暂无已研读路线。','No reviewed route matches the current filter.');}
    if(!relevant.length){root.append(node('p',t('当前范围暂无已审阅的路线分析。可查看下方候选论文，或切换月份与技术方向。','No reviewed route analyses match this scope. Browse the candidate papers below or change the month or topic.'),'meta'));notifyOutline();return;}
    if(detail){const back=node('a',t('← 本期动态总览','← Current updates overview'),'direction-back');back.href='index.html?month='+current.period+'&scope='+current.scope+'#view-updates';root.append(back);document.getElementById('topic-title').textContent=selectedPaper?model.sourceMap.get(model.reviewMap.get(selectedPaper)?.source_id)?.title||t('论文详读','Paper reader'):pick(relevant[0],'title',current.locale)+t('（',' (')+storyMapLabel(relevant[0],model)+t('）',')');document.title=document.getElementById('topic-title').textContent+' · '+current.period;}
    const refs=model.refs.filter(r=>relevant.some(s=>s.story_id===r.story_id)),unique=new Map();
    refs.forEach(r=>{if(!unique.has(r.summary_id))unique.set(r.summary_id,r)});
    const ids=new Map([...unique.keys()].map((id,i)=>[id,'E'+String(i+1).padStart(2,'0')]));
    const asOf=relevant.map(s=>s.checked_at).sort().at(-1);
    if(!detail){
      const metric=document.getElementById('monthly-academic-metric');if(metric)metric.textContent=String(unique.size);
      const cutoff=document.getElementById('monthly-review-cutoff');if(cutoff)cutoff.textContent=t(`原文研读更新至 ${asOf} · 当前范围 ${relevant.length} 条路线 · 不是全领域收录总量`,`Paper reviews through ${asOf} · ${relevant.length} routes in this scope · not a field-wide total`);
      const keyChanges=document.getElementById('monthly-key-changes');if(keyChanges){keyChanges.replaceChildren();for(const story of relevant){const a=node('a','','monthly-change-tile');a.href='#monthly-brief-'+story.story_id;a.append(node('strong',pick(story,'title',current.locale).split(/[：:]/)[0]),node('span',pick(story,'question',current.locale)));keyChanges.append(a);}}
    }

    const topicPaperIds=new Set(refs.filter(ref=>!current.topicId||ref.compression_topic_id===current.topicId).map(ref=>ref.summary_id)),contextPaperCount=unique.size-topicPaperIds.size;
    root.append(node('p',detail&&selectedPaper?t('论文详读 · 下文注明原文版本与实验条件','Paper review · Version and experimental conditions are listed below'):current.topicId?t(`截至 ${asOf} · ${relevant.length} 条相关路线 · ${topicPaperIds.size} 篇当前专题原文 · ${contextPaperCount} 篇关联背景原文`,`As of ${asOf} · ${relevant.length} relevant routes · ${topicPaperIds.size} topic papers · ${contextPaperCount} contextual papers`):t(`截至 ${asOf} · ${relevant.length} 条技术路线 · ${unique.size} 篇已审阅原文 · 当月截至目前的采集范围`,`As of ${asOf} · ${relevant.length} routes · ${unique.size} reviewed papers · collected month-to-date scope`),'meta'));
    if(current.topicId&&contextPaperCount)root.append(node('p',t('关联论文用于跨专题比较，单独列出，不计入当前专题的论文数量。','Related papers support comparisons across topics. They are listed separately and excluded from the selected topic’s paper count.'),'meta'));
    const cite=(parent,ref)=>{const a=node('a','['+ids.get(ref.summary_id)+']','monthly-route-citation');a.href=detail?'#monthly-evidence-'+ref.summary_id:readerUrl('',ref.summary_id);if(!detail)a.dataset.monthlyReader='true';
      a.addEventListener('click',()=>{if(!detail)return;const card=document.getElementById('monthly-evidence-'+ref.summary_id);if(card){card.open=true;card.focus?.();}});parent.append(document.createTextNode(' '),a);};
    const overview=chapter('section','monthly-fact-overview',t('本月进展概览','Monthly progress overview'),4);
    overview.dataset.sectionOutline='false';
    for(const story of relevant){
      const card=node('article','','monthly-direction-brief');card.dataset.monthlyBrief=story.story_id;card.id='monthly-brief-'+story.story_id;
      card.append(routeHeading(story,model));
      const routeRefs=refs.filter(r=>r.story_id===story.story_id).sort((a,b)=>a.position-b.position),papers=new Map();routeRefs.forEach(r=>{if(!papers.has(r.summary_id))papers.set(r.summary_id,r)});
      card.append(node('p',pick(story,'question',current.locale),'monthly-route-question'));
      const tags=node('div','','monthly-route-topics');tags.setAttribute('aria-label',t('对应技术地图专题','Linked technology-map topics'));[...new Set(routeRefs.map(r=>r.compression_topic_id))].forEach(id=>tags.append(topicLink(id)));card.append(tags);
      const list=node('ul','','monthly-brief-facts');
      for(const ref of papers.values()){const summary=model.reviewMap.get(ref.summary_id),source=model.sourceMap.get(ref.source_id),event=model.eventMap.get(ref.evidence_id),li=node('li');li.dataset.readingLayer='facts';
        const title=node('a',source.title);title.href=safeUrl(summary.evidence_url);title.target='_blank';title.rel='noopener noreferrer';const heading=node('h5');heading.append(title);li.append(heading);
        li.append(node('span',event.event_date+' · '+ref.observed_version+' · '+t(event.date_kind==='revision'?'修订':'首投',event.date_kind==='revision'?'Revision':'First submission'),'meta'),node('span',t(summary.review_status==='method_results_checked'?'方法与结果已核对':'仅摘要已核对',summary.review_status==='method_results_checked'?'Methods/results checked':'Abstract only'),'monthly-review-badge'));
        const primaryLink=node('p','','monthly-paper-links');cite(primaryLink,ref);const detailLink=node('a',t('原文笔记 →','Source notes →'));detailLink.href=readerUrl('',ref.summary_id);detailLink.dataset.monthlyReader='true';primaryLink.append(detailLink);li.append(primaryLink);const summaryDetails=node('div','','monthly-paper-details');paperFields(summaryDetails,summary,model,ref.summary_id,{compact:true});li.append(summaryDetails);if(current.topicId&&!topicPaperIds.has(ref.summary_id)){li.prepend(node('p',t('关联背景原文','Contextual source'),'meta'));li.dataset.topicRelation='context';}else li.dataset.topicRelation='direct';list.append(li);}
      card.append(list);

      const report=node('a',t('查看本期综合判断 →','Open this period’s synthesis →'),'monthly-synthesis-link');report.href='index.html?month='+current.period+'&scope='+current.scope+'#view-home';
      card.append(node('p',t(papers.size+' 篇原文 · 数字保留论文条件，不等于昇腾实测',papers.size+' primary papers · Results retain paper conditions, not Ascend measurements'),'meta'));
      const open=node('a',t('查看完整原文笔记 →','Read the full source notes →'),'monthly-story-open');open.href=readerUrl(story.story_id);open.dataset.monthlyReader='true';card.append(open);overview.append(card);
    }
    if(!detail)root.append(overview);
    if(detail){
      const storyDirectory=node('nav','','monthly-story-directory');storyDirectory.setAttribute('aria-label',t('本期路线详读','Current route reviews'));
      for(const story of model.stories.slice().sort((a,b)=>a.position-b.position)){
        const a=node('a',pick(story,'title',current.locale));a.href=readerUrl(story.story_id);a.dataset.monthlyReader='true';if(selectedRoute===story.story_id)a.setAttribute('aria-current','page');storyDirectory.append(a);
      }
      const switcher=node('details','','monthly-reader-switcher');switcher.append(node('summary',t('选择技术路线','Choose a research route')),storyDirectory);root.append(switcher);
    }
    if(detail||document.body.dataset.compressionView==='updates'){document.body.dataset.lriReaderNavigation=detail?'.monthly-story-directory':'.current-updates-navigation';document.body.dataset.lriReaderNavigationLabel=detail?t('本期动态 · 技术路线','Current updates · Research routes'):t('本期动态 · 三类进展','Current updates · Three streams');}
    const routes=chapter('section','monthly-technical-routes',t('技术方案与研究判断','Methods and research assessment'),4,true);
    routes.append(node('h3',t('技术方案与研究判断','Methods and research assessment')),node('p',t('比较各项方案解决的问题、技术做法和实验结果，再判断哪些思路值得在昇腾上验证。','Compare the problems, methods and results, then assess which ideas warrant validation on Ascend.')));
    relevant.forEach((story,i)=>{
      const title=pick(story,'title',current.locale)+t('（',' (')+storyMapLabel(story,model)+t('）',')'),article=chapter('article','monthly-route-'+story.story_id,title,5);
      article.className='monthly-route-story';article.dataset.monthlyStory=story.story_id;
      const open=node('a',t('阅读路线分析 →','Read route analysis →'),'monthly-story-open');open.href=readerUrl(story.story_id);if(!detail)article.append(open);
      article.append(node('p',String(i+1).padStart(2,'0')+' · '+t('技术路线','Technical route'),'eyebrow'),routeHeading(story,model,'h3'),node('p',pick(story,'question',current.locale),'monthly-route-question'));
      paragraph(article,t('背景介绍','Background'),pick(story,'context',current.locale));
      const routeRefs=refs.filter(r=>r.story_id===story.story_id).sort((a,b)=>a.position-b.position),dedup=new Map();routeRefs.forEach(r=>{if(!dedup.has(r.summary_id))dedup.set(r.summary_id,r)});
      const tags=node('div','','monthly-route-topics');[...new Set(routeRefs.map(r=>r.compression_topic_id))].forEach(id=>tags.append(topicLink(id)));article.append(tags);
      article.append(node('p',t(`${dedup.size} 篇直接原文 · ${[...dedup.values()].filter(r=>model.reviewMap.get(r.summary_id).review_status==='method_results_checked').length} 篇核对关键方法与结果 · 尚无本报告的独立复现实验`,`${dedup.size} primary papers; ${[...dedup.values()].filter(r=>model.reviewMap.get(r.summary_id).review_status==='method_results_checked').length} methods/results checks; no independent reproduction by this report`),'meta'));
      // Source facts precede cross-paper mechanisms and interpretation.
      const facts=chapter('section','monthly-facts-'+story.story_id,t('论文摘要与实验结果','Paper summaries and experimental results'),6);facts.className='monthly-route-facts';facts.dataset.readingLayer='facts';facts.append(node('h4',t('本月客观事实','Monthly progress overview')));
      const list=node('ol');
      for(const ref of dedup.values()){const summary=model.reviewMap.get(ref.summary_id),source=model.sourceMap.get(ref.source_id),event=model.eventMap.get(ref.evidence_id),li=node('li');li.dataset.routeSummary=ref.summary_id;
        const title=node('a',source.title);title.href=safeUrl(summary.evidence_url);title.target='_blank';title.rel='noopener noreferrer';const heading=node('h5');heading.append(title);li.append(heading,node('span',event.event_date+' · '+t(event.date_kind==='revision'?'修订':'首投',event.date_kind==='revision'?'Revised':'First submission')+' · '+ref.observed_version,'meta'));
        const p=paragraph(li,t('一句话总结','One-sentence summary'),pick(summary,'one_sentence',current.locale));cite(p,ref);
        paperFields(li,summary,model,ref.summary_id);
        const paperReader=node('a',t('打开论文详读 →','Open paper review →'));paperReader.href=readerUrl('',ref.summary_id);paperReader.dataset.monthlyReader='true';li.append(paperReader);if(current.topicId&&!topicPaperIds.has(ref.summary_id)){const background=node('details');background.append(node('summary',t('关联背景原文：','Contextual paper: ')+source.title),...li.childNodes);li.append(background);li.dataset.topicRelation='context';}else li.dataset.topicRelation='direct';list.append(li);}
      facts.append(list);article.append(facts);
      const mechanismDetails=node('details','','monthly-mechanism-detail');mechanismDetails.append(node('summary',t('比较各论文的技术方案与实验条件','Compare paper methods and experimental conditions')));renderRouteDiagram(mechanismDetails,story,dedup,model);article.append(mechanismDetails);
      const interpretation=chapter('section','monthly-analysis-'+story.story_id,t('方案比较与研究判断','Method comparison and assessment'),6);interpretation.className='monthly-route-interpretation';interpretation.dataset.readingLayer='analysis';interpretation.append(node('h4',t('综合解读','Synthesis')));
      const synthesis=paragraph(interpretation,t('方案比较','Method comparison'),pick(story,'synthesis',current.locale));for(const ref of dedup.values())cite(synthesis,ref);
      paragraph(interpretation,t('研究判断（待复核）','Research assessment (pending review)'),pick(story,'viewpoint',current.locale),'monthly-route-viewpoint');
      paragraph(interpretation,t('适用条件与待验证问题','Applicability and open questions'),pick(story,'boundary',current.locale));
      paragraph(interpretation,t('对昇腾研究的启示','Implications for Ascend research'),pick(story,'implication',current.locale));article.append(interpretation);routes.append(article);
    });if(detail&&!selectedPaper)root.append(routes);
    const evidence=chapter('section','monthly-evidence-index',t('参考论文与原文链接','References and primary sources'),4);
    evidence.append(node('h3',t('参考论文与原文链接','References and primary sources')),node('p',t('点击正文中的 [E##] 可查看论文版本、实验条件和原文链接；预印本的评审状态以发表记录为准。','Select [E##] in the text for the paper version, experimental conditions and source link. Check publication records for a preprint’s peer-review status.')));
    if(detail)for(const ref of unique.values()){if(detail&&selectedPaper&&ref.summary_id!==selectedPaper)continue;const summary=model.reviewMap.get(ref.summary_id),source=model.sourceMap.get(ref.source_id),event=model.eventMap.get(ref.evidence_id),card=node('details','','monthly-evidence-card');card.id='monthly-evidence-'+ref.summary_id;card.tabIndex=-1;
      card.append(node('summary','['+ids.get(ref.summary_id)+'] '+source.title),node('p',event.event_date+' · '+ref.observed_version+' · '+t(summary.review_status==='method_results_checked'?'关键方法/结果已审阅':'原始摘要已审阅',summary.review_status==='method_results_checked'?'Methods/results checked':'Primary abstract checked'),'meta'));
      paragraph(card,t('一句话总结','One-sentence summary'),pick(summary,'one_sentence',current.locale));
      const topics=[...new Set(refs.filter(r=>r.summary_id===ref.summary_id).map(r=>r.compression_topic_id))].map(id=>current.topics.find(t=>t.compression_topic_id===id)).filter(Boolean);
      paragraph(card,t('关键词','Keywords'),(model.keywordMap.get(ref.summary_id)||[]).map(k=>pick(k,'keyword',current.locale)).join(' · '));
      paragraph(card,t('相关研究专题','Related research topics'),topics.map(x=>pick(x,'name',current.locale)||pick(x,'title',current.locale)).join(' · '));
      paragraph(card,t('背景介绍','Background'),pick(summary,'background',current.locale));
      paragraph(card,t('技术和创新点','Technology and innovation'),pick(summary,'innovation',current.locale));
      paragraph(card,t('效果总结','Results and conditions'),pick(summary,'results',current.locale));
      paragraph(card,t('原文位置','Source location'),summary.evidence_locator+' · '+summary.reviewed_at,'meta');
      const original=node('a',t('打开已审阅版本原文 →','Open reviewed primary version →'));original.href=safeUrl(summary.evidence_url);original.target='_blank';original.rel='noopener noreferrer';card.append(original);if(detail&&selectedPaper)card.open=true;
      const tags=node('div','','monthly-route-topics');topics.forEach(x=>tags.append(topicLink(x.compression_topic_id)));card.append(tags);evidence.append(card);}
    if(detail)root.append(evidence);
    notifyOutline();if(model.stories.length){globalThis.LRICloudFirstRetire?.();performance.mark('cloud-core-monthly-content');}
  }
  function refresh(context, force = false) {
    if (!context.revision || !context.scope || !context.period) { reset(); return; }
    const key=[context.revision,context.period,context.scope].join('|'), previous=current;
    current={...context,key};
    if (force) cache.delete(key);
    let entry=cache.get(key);
    if (!entry) {
      entry={promise:load(context),model:null};cache.set(key,entry);
      if(cache.size>4)cache.delete(cache.keys().next().value);
      entry.promise.then(model=>{entry.model=model;if(current?.key===key&&cache.get(key)===entry)render(model);}).catch(error=>{
        console.error('Monthly route reader failed',error);
        const owned=cache.get(key)===entry;
        if(owned)cache.delete(key);
        if(owned&&current?.key===key)status(t('路线解读读取或关联校验失败；下方论文列表可独立阅读，请重试。','Route review failed to load or validate. The paper list remains independently readable; please retry.'),true);
      });
    }
    if(entry.model)render(entry.model);else if(!previous || previous.key!==key || previous.topicId!==context.topicId || force)status(t('正在加载本月技术路线…','Loading monthly research routes…'));
  }
  function reset() { current=null;mount()?.replaceChildren();if(document.body.dataset.lriReaderNavigation==='.monthly-story-directory'){delete document.body.dataset.lriReaderNavigation;delete document.body.dataset.lriReaderNavigationLabel;} }
  globalThis.LRICompressionMonthly=Object.freeze({refresh,reset});
})();





