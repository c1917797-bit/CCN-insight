/* Monthly first-publication census of a saved, registered-source query.
   Evidence-backed classifications are canonical records, never inferred from titles here. */
(() => {
'use strict';
const ROOTS=['precision','selection','distillation','factorization'];
const TARGETS=['parameters','activations','kv_cache'];
const EXTENSIONS=['activations-merging','kv_cache-kv_eviction','kv_cache-sharing','kv_cache-compact_architecture'];
const TOPICS=new Set([...TARGETS.flatMap(t=>ROOTS.map(m=>t+'-'+m)),...EXTENSIONS]);
const STATUSES=['classified','related_unmapped','pending','excluded'];
const cache=new Map();let epoch=0,active='',context=null,model=null;
const must=(ok,msg)=>{if(!ok)throw Error(msg);};
const el=(tag,text='',cls='')=>{const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n;};
const en=()=>context?.locale==='en';
const text=(zh,english)=>en()?english:zh;
const labels={parameters:['权重','Weights'],activations:['激活','Activations'],kv_cache:['KV Cache','KV cache'],precision:['低比特量化','Low-bit quantization'],selection:['稀疏化与剪枝','Sparsity / pruning'],distillation:['知识蒸馏','Knowledge distillation'],factorization:['低秩分解','Low-rank factorization'],'activations-merging':['Token 合并','Token merging'],'kv_cache-kv_eviction':['KV Cache 淘汰','KV eviction'],'kv_cache-sharing':['GQA / MQA','GQA / MQA'],'kv_cache-compact_architecture':['高效架构设计','Compact cache architecture'],classified:['与技术地图相关','Map-related papers'],related_unmapped:['相关但未归类','Related, outside the map'],pending:['待核实','Needs verification'],excluded:['本轮不纳入','Outside this round']};
const name=id=>(labels[id]||[id,id])[en()?1:0];
const topicName=id=>EXTENSIONS.includes(id)?name(id):name(id.split('-')[0])+' × '+name(id.split('-').slice(1).join('-'));
function aggregate(rows,snapshot,registered){
 must(snapshot.business_id==='cloud-core'&&snapshot.topic_id==='cloud_core','Monthly snapshot scope mismatch');
 must(snapshot&&snapshot.month_basis==='first_publication'&&snapshot.diffusion_policy==='excluded','Invalid monthly count policy');
 must(/^\d{4}-\d{2}$/.test(snapshot.period_id)&&/^\d{4}-\d{2}-\d{2}$/.test(snapshot.cutoff)&&snapshot.cutoff.startsWith(snapshot.period_id)&&snapshot.window_start===snapshot.period_id+'-01'&&Number.isSafeInteger(snapshot.candidate_count)&&snapshot.candidate_count>=0,'Invalid monthly window');
 must(['abstract_snapshot_sha256','decisions_sha256'].every(k=>/^[a-f0-9]{64}$/.test(snapshot[k])),'Missing snapshot verification hashes');
 const families=JSON.parse(snapshot.source_family_ids_json);must(Array.isArray(families)&&families.length&&new Set(families).size===families.length&&families.every(id=>registered.has(id)),'Unregistered monthly source');
 const papers=new Map(),byTopic=new Map([...TOPICS].map(id=>[id,new Set()])),byStatus=new Map(STATUSES.map(id=>[id,new Set()])),byReviewBasis=new Map(['original_abstract','original_sections'].map(id=>[id,new Set()]));
 for(const row of rows){
  must(row.snapshot_id===snapshot.snapshot_id&&row.period_id===snapshot.period_id&&row.business_id==='cloud-core'&&row.topic_id==='cloud_core','Monthly corpus scope mismatch');
  must(/^\d{4}\.\d{4,5}$/.test(row.paper_id)&&row.canonical_url==='https://arxiv.org/abs/'+row.paper_id&&new RegExp('^'+row.paper_id.replace('.','\\.')+'v[1-9][0-9]*$').test(row.versioned_id),'Invalid paper identity');
  must(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(row.first_published)&&row.first_published.startsWith(snapshot.period_id)&&row.first_published.slice(0,10)<=snapshot.cutoff,'Revision or outside-month paper in first-publication corpus');
  must(families.includes(row.source_family_id)&&byReviewBasis.has(row.review_basis)&&/^[a-f0-9]{64}$/.test(row.abstract_sha256)&&row.basis_zh?.trim(),'Missing classification provenance');
  if(row.review_basis==='original_sections'){
   must(typeof row.review_locator==='string'&&row.review_locator.trim()&&typeof row.review_url==='string'&&new RegExp('^https://arxiv\\.org/(?:html|pdf)/'+row.versioned_id.replace('.','\\.')+'(?:\\.pdf)?(?:[?#].*)?$').test(row.review_url),'Missing or mismatched original-section locator / URL');
   must(typeof row.reviewed_at==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(row.reviewed_at)&&Number.isFinite(Date.parse(row.reviewed_at+'T00:00:00Z'))&&new Date(row.reviewed_at+'T00:00:00Z').toISOString().slice(0,10)===row.reviewed_at&&row.reviewed_at>=row.first_published.slice(0,10),'Invalid original-section review date');
  }
  must(STATUSES.includes(row.classification_status),'Unknown corpus classification');
  const ids=JSON.parse(row.topic_ids_json);must(Array.isArray(ids)&&new Set(ids).size===ids.length&&ids.every(id=>TOPICS.has(id)),'Unknown or duplicate topic assignment');
  must((row.classification_status==='classified')===(ids.length>0),'Unresolved papers must not enter cells');
  must(row.reason_code!=='diffusion_out_of_scope'||(row.classification_status==='excluded'&&!ids.length),'Diffusion cannot enter this matrix');
  const old=papers.get(row.paper_id);
  if(old){must(['abstract_sha256','topic_ids_json','classification_status','review_basis','review_locator','review_url','reviewed_at'].every(k=>(old[k]??'')===(row[k]??'')),'Conflicting versions of a paper');continue;}
  papers.set(row.paper_id,row);byStatus.get(row.classification_status).add(row.paper_id);byReviewBasis.get(row.review_basis).add(row.paper_id);for(const id of ids)byTopic.get(id).add(row.paper_id);
 }
 must(papers.size===snapshot.candidate_count,'Monthly snapshot count is incomplete');
 const rootUnion=new Set(),objectTotals=new Map();
 for(const target of TARGETS){const ids=new Set();for(const method of ROOTS)for(const id of byTopic.get(target+'-'+method)){ids.add(id);rootUnion.add(id);}objectTotals.set(target,ids);}
 const extensionUnion=new Set(EXTENSIONS.flatMap(id=>[...byTopic.get(id)]));
 const classifiedUnion=byStatus.get('classified'),mapUnion=new Set([...rootUnion,...extensionUnion]);
 const extensionOnly=new Set([...extensionUnion].filter(id=>!rootUnion.has(id))),rootOnly=new Set([...rootUnion].filter(id=>!extensionUnion.has(id))),rootExtensionOverlap=new Set([...rootUnion].filter(id=>extensionUnion.has(id)));
 must(classifiedUnion.size===mapUnion.size&&[...classifiedUnion].every(id=>mapUnion.has(id)),'Classified papers must equal the root / extension union');
 return {snapshot,papers,byTopic,byStatus,byReviewBasis,classifiedUnion,rootUnion,extensionUnion,extensionOnly,rootOnly,rootExtensionOverlap,objectTotals};
}
async function pages(table,field,value,revision,max){
 const rows=[];let offset=0,total=null;
 for(let i=0;i<Math.ceil(max/100)+1;i++){
  const page=await LRITableGit.loadTablePage(table,{filterField:field,filterValue:value,expectedRevision:revision,limit:100,offset});
  must(page.revision===revision&&page.page.offset===offset,'Monthly snapshot revision drift');
  if(total===null)total=page.page.total;must(Number.isSafeInteger(total)&&total<=max&&page.page.total===total,'Invalid monthly corpus total');
  rows.push(...page.records);must(rows.length<=total,'Duplicate monthly pages');
  if(!page.page.truncated){must(rows.length===total,'Incomplete monthly pages');return rows;}
  must(page.records.length>0&&page.page.nextOffset===offset+page.records.length,'Monthly page made no progress');offset=page.page.nextOffset;
 }
 throw Error('Monthly corpus exceeds the bounded reader budget');
}
async function read(c){
 const snapshots=await pages('ic_monthly_corpus_snapshots','period_id',c.period,c.revision,100);
 if(!snapshots.length)return null;
 const s=[...snapshots].sort((a,b)=>b.cutoff.localeCompare(a.cutoff)||b.snapshot_id.localeCompare(a.snapshot_id))[0];
 const ids=JSON.parse(s.source_family_ids_json),sources=await LRITableGit.loadRowsByKeys('ic_source_families',ids,c.revision,['family_id','business_id','topic_id','ui_group','title_zh','title_en']);
 must(sources.revision===c.revision&&sources.records.length===ids.length&&sources.records.every(r=>r.business_id==='cloud-core'&&r.topic_id==='cloud_core'&&r.ui_group==='academic'),'Monthly source registry mismatch');
 const rows=await pages('ic_monthly_paper_corpus','snapshot_id',s.snapshot_id,c.revision,10000);
 return aggregate(rows,s,new Set(sources.records.map(r=>r.family_id)));
}
function button(title,action,cls=''){const b=el('button',title,cls);b.type='button';b.addEventListener('click',action);return b;}
function countButton(count,label,ids){const b=button(String(count),()=>list(label,ids),'corpus-count');b.setAttribute('aria-label',label+' · '+count+text(' 篇，查看论文',' papers; view papers'));return b;}
function list(label,ids){
 const host=document.getElementById('monthly-corpus-papers');if(!host||!model)return;
 host.hidden=false;host.replaceChildren();host.dataset.selection=label;
 const head=el('div','','corpus-list-heading'),h=el('h3',label+' · '+ids.size+text(' 篇',' papers'));h.tabIndex=-1;
 head.append(h,button(text('收起列表','Close list'),()=>{host.hidden=true;document.querySelector('#monthly-paper-matrix h2')?.focus();},'corpus-close'));host.append(head);
 if(!ids.size){host.append(el('p',text('当前检索快照中没有确认归入此项的论文；这不代表全领域为零。','No papers are confirmed for this category in this query snapshot; this is not a field-wide zero.')));h.focus({preventScroll:true});return;}
 const input=el('input');input.type='search';input.placeholder=text('在这些论文中搜索标题或编号','Search these papers by title or ID');input.setAttribute('aria-label',input.placeholder);host.append(input);
 const result=el('div'),pager=el('div','','corpus-pager');host.append(result,pager);let page=0;
 const records=[...ids].map(id=>model.papers.get(id)).sort((a,b)=>b.first_published.localeCompare(a.first_published)||a.paper_id.localeCompare(b.paper_id));
 function draw(){
  const q=input.value.trim().toLowerCase(),matched=records.filter(r=>!q||(r.title+' '+r.paper_id).toLowerCase().includes(q));page=Math.min(page,Math.max(0,Math.ceil(matched.length/12)-1));result.replaceChildren();pager.replaceChildren();
  for(const row of matched.slice(page*12,page*12+12)){
   const card=el('article','','corpus-paper'),a=el('a',row.title+' ↗');a.href='https://arxiv.org/abs/'+row.versioned_id;a.target='_blank';a.rel='noopener noreferrer';const title=el('h4');title.append(a);
   card.append(title,el('p',row.paper_id+' · '+text('首发 ','First published ')+row.first_published.slice(0,10)+' · '+row.versioned_id,'meta'),el('p',row.basis_zh));
   if(row.uncertainties_zh)card.append(el('p',text('需进一步核对：','Needs further verification: ')+row.uncertainties_zh,'meta'));
   if(row.classification_status==='pending')card.append(el('p',text('原文核查队列：按上述缺口补读方法、模型/量化配置及实验表，必要时查作者代码；确认后更新归属并重算。原文仍不明确或无法取得时，保留待核及原因。','Full-text verification queue: inspect methods, model/quantization configurations and experiment tables for the stated gap, then author code if needed. Update classification and counts after verification; retain the unresolved status and reason if evidence remains unavailable or unclear.'),'meta'));
   const tags=JSON.parse(row.topic_ids_json).map(topicName);if(tags.length)card.append(el('p',tags.join(' · '),'corpus-paper-tags'));
   if(row.review_basis==='original_sections'){
    const evidence=el('p',text('依据：原文章节核对 · ','Basis: targeted paper-section review · ')+row.review_locator+' · '+row.reviewed_at+' · ','meta'),link=el('a',text('查看原文 ↗','Open original paper ↗'));link.href=row.review_url;link.target='_blank';link.rel='noopener noreferrer';evidence.append(link);card.append(evidence,el('p',text('已核对上述章节；不代表全文研读或独立复现。','The cited sections were checked; this is not a claim of complete-paper review or independent reproduction.'),'meta'));
   }else card.append(el('p',text('依据：arXiv 原始摘要；不等于全文研读或效果复现。','Basis: original arXiv abstract; not full-text review or independent reproduction.'),'meta'));result.append(card);
  }
  const prev=button(text('上一页','Previous'),()=>{page--;draw();}),next=button(text('下一页','Next'),()=>{page++;draw();});prev.disabled=page===0;next.disabled=(page+1)*12>=matched.length;
  pager.append(prev,el('span',matched.length?`${page*12+1}–${Math.min((page+1)*12,matched.length)} / ${matched.length}`:'0 / 0'),next);
 }
 input.addEventListener('input',()=>{page=0;draw();});draw();h.focus({preventScroll:true});host.scrollIntoView({block:'nearest',behavior:'auto'});
}
function render(host,m){
 model=m;host.replaceChildren();const head=el('header','','corpus-heading'),eyebrow=el('p',text('月内首发 · 按证据确认技术关联','First published this month · evidence-based map relevance'),'corpus-eyebrow'),h=el('h2',context.period+text(' · 论文数量矩阵',' · Paper-count matrix'));h.tabIndex=-1;head.append(eyebrow,h);host.append(head);
 if(!m){host.append(el('p',text('此月份尚未建立可核对的月内论文快照。下方精选数量不能代替本月论文总量。','No auditable monthly corpus snapshot is available for this month. Selected papers below are not a substitute for a monthly count.')));return;}
 const s=m.snapshot;head.append(el('p',`${s.window_start}—${s.cutoff} · `+text('已登记来源：arXiv；暂不含扩散模型。','Registered source: arXiv; generative diffusion models excluded.')));
 const metrics=el('div','','corpus-metrics');
 for(const status of ['classified','related_unmapped','pending']){const ids=m.byStatus.get(status),b=button('',()=>list(name(status),ids));b.append(el('strong',String(ids.size)),el('span',name(status)));metrics.append(b);}host.append(metrics);
 const reconciliation=el('div','','corpus-count-note');reconciliation.dataset.corpusReconciliation='true';reconciliation.append(el('strong',text(`统计范围：${TOPICS.size} 个专题 = ${ROOTS.length*TARGETS.length} 个根技术单元格 + ${EXTENSIONS.length} 个扩展机制`,`Count scopes: ${TOPICS.size} topics = ${ROOTS.length*TARGETS.length} root-technique cells + ${EXTENSIONS.length} additional mechanisms`)));
 const scopeButtons=el('div','','corpus-extensions');for(const [key,zh,english,ids] of [['all','全部相关','All map-related papers',m.classifiedUnion],['roots','四类根技术','Four root techniques',m.rootUnion],['extensions','扩展机制','Additional mechanisms',m.extensionUnion],['extension-only','仅扩展机制','Additional mechanisms only',m.extensionOnly],['overlap','两类均有','In both groups',m.rootExtensionOverlap]]){const label=text(zh,english),b=button(label+' · '+ids.size,()=>list(label,ids));b.dataset.corpusScope=key;scopeButtons.append(b);}reconciliation.append(scopeButtons,el('p',text(`${m.classifiedUnion.size} 篇相关论文 = ${m.rootUnion.size} 篇根技术论文 + ${m.extensionOnly.size} 篇仅扩展机制论文。${m.extensionUnion.size} 篇扩展机制论文中，${m.rootExtensionOverlap.size} 篇也属于根技术，不能重复相加。各组均按论文编号去重。`,`${m.classifiedUnion.size} map-related papers = ${m.rootUnion.size} root-technique papers + ${m.extensionOnly.size} additional-only papers. Of ${m.extensionUnion.size} papers covering additional mechanisms, ${m.rootExtensionOverlap.size} also cover root techniques and must not be added twice. Each group deduplicates paper IDs.`)));host.append(reconciliation);
 const scroll=el('div','','corpus-matrix-scroll');scroll.tabIndex=0;scroll.setAttribute('aria-label',text('对象与根技术的本月首发论文数量','Monthly first-publication papers by target and root technique'));const table=el('table','','corpus-matrix');const caption=el('caption',text('当前检索快照内的论文数；点击数字查看论文与归类理由。','Papers in this query snapshot. Select a count to inspect papers and classification reasons.'));table.append(caption);
 const thead=el('thead'),tr=el('tr');for(const id of ['target',...ROOTS,'total']){const th=el('th',id==='target'?text('压缩对象','Target'):id==='total'?text('去重合计','Unique total'):name(id));th.scope='col';tr.append(th);}thead.append(tr);table.append(thead);
 const tbody=el('tbody');for(const target of TARGETS){const row=el('tr'),th=el('th',name(target));th.scope='row';row.append(th);for(const method of ROOTS){const id=target+'-'+method,td=el('td');td.dataset.corpusCell=id;td.append(countButton(m.byTopic.get(id).size,name(target)+' × '+name(method),m.byTopic.get(id)));row.append(td);}const total=el('td','','corpus-total');total.append(countButton(m.objectTotals.get(target).size,name(target)+text(' · 四类根技术',' · Four root techniques'),m.objectTotals.get(target)));row.append(total);tbody.append(row);}table.append(tbody);
 const foot=el('tfoot'),fr=el('tr'),ft=el('th',text('四类根技术去重','Four root techniques · unique papers'));ft.colSpan=5;ft.scope='row';const val=el('td');val.append(countButton(m.rootUnion.size,text('四类根技术 · 全部论文','Four root techniques · all papers'),m.rootUnion));fr.append(ft,val);foot.append(fr);table.append(foot);scroll.append(table);host.append(scroll);
 host.append(el('p',text('一篇论文可关联多格；每格、每行及四类根技术分别按论文编号去重。单元格、行合计和扩展机制数量都不能直接相加。','A paper may enter multiple cells. Each cell, row and the four-root total deduplicates paper IDs. Do not add cell, row or additional-mechanism counts.'),'corpus-count-note'));
 const extra=el('div','','corpus-extensions');extra.append(el('strong',text('扩展机制','Additional mechanisms')));for(const id of EXTENSIONS){const ids=m.byTopic.get(id);extra.append(button(name(id)+' · '+ids.size,()=>list(name(id),ids)));}host.append(extra);
 const selection=el('details','','corpus-audit');selection.append(el('summary',text('从相关论文到重点精读、精选与专题证据','From relevant papers to priority reading, selections and topic evidence')));
 selection.append(el('p',text('与技术地图相关只代表摘要或已核对原文章节支持技术关联，不代表质量排名或已完成专题吸收。这轮新增候选尚未全部核对方法与实验，不能把下面既有研读集合当作从本轮候选中优选出的最终名单。','Map relevance is supported by the abstract or the cited paper sections; it is not a quality ranking or completed topic synthesis. Methods and experiments have not been checked for every new candidate; the previously reviewed collection below is not the final selection from this new corpus.')));
 const gates=el('ol');for(const [zh,english] of [
  ['重点精读：是否新增机制、突破边界、纠正既有判断，或补上重要知识空白；先与同路线已有工作对照。','Priority reading: a new mechanism, boundary breakthrough, correction of an existing view or important knowledge gap; compare against prior work in the same route.'],
  ['本期精选：核对原文方法与实验后，确认相对基线的增量、测试条件、结果及局限，再按同路线代表性取舍；失败结果与反例也可以入选。','Monthly selection: inspect original methods and experiments, verify the increment over baselines, test conditions, results and limitations, then choose representative work within each route. Negative results can qualify.'],
  ['纳入专题：能够补充原理、确立重要基线、改变路线判断或适用边界。仅是当月消息就留在动态；同一论文通过稳定引用关联，不复制成多份内容。','Topic evidence: adds a principle or important baseline, or changes a route assessment or applicability boundary. Date-specific news stays in current updates; reuse one stable reference.']])gates.append(el('li',text(zh,english)));selection.append(gates);
 selection.append(el('p',text('每次决定应保存：对照了谁、为何值得读、已读到哪里、支持或改变哪条判断。引用量、标题热度和单个最高加速数字不能代替这些依据。','Record the comparator, reason to read, review depth and assessment affected. Citation counts, headline popularity and a peak speedup cannot replace this evidence.'),'meta'));host.append(selection);
 const detail=el('details','','corpus-audit');detail.append(el('summary',text('统计口径与来源覆盖','Counting rules and source coverage')));
 const abstractCount=m.byReviewBasis.get('original_abstract').size,sectionCount=m.byReviewBasis.get('original_sections').size;
 detail.append(el('p',text(`本次检索命中 ${s.candidate_count} 篇本月首发候选；${abstractCount} 篇依据原始摘要判断，${sectionCount} 篇补充核对了原文章节，具体章节、链接和日期见论文记录。确认技术关联、相关但未归类、待核实及本轮不纳入均保留记录。全部相关论文覆盖 ${TOPICS.size} 个专题；根技术表只覆盖其中 ${ROOTS.length*TARGETS.length} 个单元格。`,`This query returned ${s.candidate_count} first-publication candidates: ${abstractCount} decisions use the original abstract and ${sectionCount} include targeted paper-section checks. Each section-reviewed record lists its locator, URL and review date. All decisions, including exclusions, are retained. All map-related papers cover ${TOPICS.size} topics; the root-technique table covers only ${ROOTS.length*TARGETS.length} cells.`)));
 detail.append(el('p',text('这不是全领域总量，也不代表其他已登记来源已完成月度统计。其他来源暂不计入，不能当作零篇。旧论文在本月的修订不进入首发矩阵；下方精选进展可另含修订。','This is not a field-wide census or a completed census of all registered sources. Sources not yet covered are not treated as zero. Revisions of older papers are excluded from the first-publication matrix; selected updates below may include revisions.')));
 const links=el('p');for(const [title,href] of [[text('研究与编辑原则','Research and editorial principles'),'index.html'+location.search+'#research-principles'],[text('来源目录','Source registry'),'#view-sources'],[text('arXiv 原始检索','Original arXiv query'),'https://export.arxiv.org/api/query?search_query='+encodeURIComponent(s.query)+'&start=0&max_results=1']]){const a=el('a',title+' ↗');a.href=href;if(href.startsWith('https:')){a.target='_blank';a.rel='noopener noreferrer';}links.append(a,document.createTextNode('  '));}detail.append(links);
 detail.append(el('p',text('采集完成：','Acquisition completed: ')+s.acquired_at+' · '+text('归类核对更新：','Classification review updated: ')+s.reviewed_at,'meta'));
 const excluded=m.byStatus.get('excluded'),diffusion=new Set([...excluded].filter(id=>m.papers.get(id).reason_code==='diffusion_out_of_scope'));detail.append(button(text('查看本轮不纳入','Inspect exclusions')+' · '+excluded.size,()=>list(name('excluded'),excluded)),button(text('其中扩散模型','Diffusion exclusions')+' · '+diffusion.size,()=>list(text('扩散模型 · 本轮不纳入','Diffusion models · excluded'),diffusion)));
 const hash=el('details');hash.append(el('summary',text('快照与校验信息','Snapshot and verification')),el('p',s.snapshot_id,'meta'),el('p','Abstract snapshot SHA-256: '+s.abstract_snapshot_sha256,'meta'),el('p','Decisions SHA-256: '+s.decisions_sha256,'meta'),el('p',s.query,'meta'));detail.append(hash);host.append(detail);
 const listHost=el('section','','corpus-paper-list');listHost.id='monthly-corpus-papers';listHost.hidden=true;listHost.dataset.sectionOutline='false';host.append(listHost);
 document.dispatchEvent(new Event('lri:sections-changed'));
 if(location.hash==='#monthly-paper-matrix'&&typeof requestAnimationFrame==='function')requestAnimationFrame(()=>{if(location.hash==='#monthly-paper-matrix'&&!host.hidden)host.scrollIntoView({block:'start',behavior:'auto'});});
}
async function refresh(c){
 const host=document.getElementById('monthly-paper-matrix');if(!host)return;
 const key=[c.revision,c.period,c.locale].join('|');if(key===active)return;const run=++epoch;active=key;context=c;model=null;host.hidden=false;host.replaceChildren(el('p',text('正在核对本月论文统计…','Checking the monthly paper corpus…'),'meta'));
 try{const readKey=[c.revision,c.period].join('|');if(!cache.has(readKey)){const promise=read(c).catch(e=>{cache.delete(readKey);throw e;});cache.set(readKey,promise);if(cache.size>4)cache.delete(cache.keys().next().value);}const m=await cache.get(readKey);if(run!==epoch)return;render(host,m);}
 catch(error){if(run!==epoch)return;active='';host.replaceChildren(el('h2',text('本月论文统计暂不可用','Monthly counts unavailable')),el('p',text('没有把读取失败显示为零篇，请重试。','A failed read is not shown as zero papers. Please retry.'),'meta'),button(text('重试统计','Retry counts'),()=>refresh(c)));console.error('Monthly corpus:',error);}
}
function reset(){epoch++;active='';context=null;model=null;const host=document.getElementById('monthly-paper-matrix');if(host){host.replaceChildren();host.hidden=true;}}
globalThis.LRICompressionMonthlyCorpus={refresh,reset,aggregate};
})();
