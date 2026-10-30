// Regress publication-vs-review date confusion and multi-topic duplication.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),base=path.join(root,'original-reader/site/business_insight/cloud_core');
const text=fs.readFileSync(path.join(base,'current-synthesis.js'),'utf8');
class Node{constructor(tag='',text=''){this.tagName=tag;this.textContent=text;this.children=[];this.dataset={};}append(...n){this.children.push(...n);}replaceChildren(...n){this.children=n;}}
const elements=new Map(['current-industry-cards','monthly-release-metric','current-industry-count'].map(id=>[id,new Node()]));
const updates=[['new','2026-10-03','2026-09-30'],['old','2026-09-24','2026-10-09'],['unknown','','2026-10-09'],['unreviewed','2026-10-04','2026-10-09']].map(([id,release,checked])=>({update_id:id,family_id:'f',source_id:'source',release_date:release,checked_at:checked,version_label:id,title_zh:id,summary_zh:'summary',scope_zh:'hardware',dependencies_zh:'dependencies',boundary_zh:'boundary'}));
const links=[['new','a'],['new','b'],['old','a'],['unknown','a'],['unreviewed','a']].map(([u,t],i)=>({link_id:'l'+i,update_id:u,compression_topic_id:t,change_id:'c'+u}));
const snapshot={updates,links,assessments:links.filter(l=>l.update_id!=='unreviewed').map(l=>({link_id:l.link_id,review_status:'verified'})),changes:updates.map(u=>({update_id:u.update_id,change_id:'c'+u.update_id,source_id:'source',title_zh:'change',fact_zh:'fact',position:0})),sources:[{source_id:'source',canonical_url:'https://example.test'}]};
const sandbox={current:{period:'2026-10',locale:'zh',topicId:''},document:{getElementById:id=>elements.get(id)},el:(tag,t)=>new Node(tag,t),pick:(r,k)=>r[k+'_zh']||'',field(){},primary(){},topics(){},check:assert,ui:k=>k,notify(){}};
vm.createContext(sandbox);vm.runInContext(text.slice(text.indexOf('function renderIndustry(reader){'),text.indexOf('function notify()')),sandbox);
const render=()=>sandbox.renderIndustry({snapshot,directory:{source_families:[{family_id:'f',title_zh:'project'}]}});
const flatten=n=>[n,...n.children.flatMap(flatten)];
render();let cards=flatten(elements.get('current-industry-cards')).filter(n=>n.dataset.industryKey);
assert.equal(cards.length,1,'Only verified publications from this calendar month render; multiple topic links do not duplicate one event');
assert.equal(cards.find(n=>n.dataset.industryKey==='new').dataset.releaseBucket,'published','Publication date, not review date, selects the new-release bucket');
for(const id of ['old','unknown'])assert(!cards.some(n=>n.dataset.industryKey===id),'Older or undated material belongs to source records, not this month’s updates');
assert.equal(elements.get('monthly-release-metric').textContent,'1');
sandbox.current.topicId='b';render();cards=flatten(elements.get('current-industry-cards')).filter(n=>n.dataset.industryKey);assert.deepEqual(cards.map(n=>n.dataset.industryKey),['new']);
sandbox.current.topicId='missing';render();assert.equal(elements.get('monthly-release-metric').textContent,'0','Filtering must reset summary counts');
const html=fs.readFileSync(path.join(base,'index.html'),'utf8');
const order=['id="current-streams"','id="monthly-route-report"','id="current-industry"','id="current-hotspots"','id="monthly-appendix"'].map(id=>html.indexOf('<section '+(id==='id="current-streams"'?'class="section current-month-overview" ':'')+id));
assert(order.every(n=>n>=0)&&order.every((n,i)=>!i||n>order[i-1]),'Keep one stable reading path');
console.log('PASS: release/review dates, verified scope, multi-topic deduplication, filter reset and monthly reading order');

// Selecting a monthly topic must never navigate through the technology-map reader.
const reader=fs.readFileSync(path.join(base,'compression.js'),'utf8'),calls=[];
const selection={state:{revision:'r',focusTarget:'',focusMechanism:''},selectScientificFocus(target,mechanism){this.state.focusTarget=target;this.state.focusMechanism=mechanism;return [{cell_id:'c',object_id:'o',method_id:'m'}];},must:assert,persistTopicScope(){calls.push('persist');}};
// Use closures rather than `this`: the production selector is an ordinary function.
selection.selectScientificFocus=(target,mechanism)=>{selection.state.focusTarget=target;selection.state.focusMechanism=mechanism;return [{cell_id:'c',object_id:'o',method_id:'m'}];};
for(const name of ['resetDetails','resetEvidence','renderSelectors','renderSelection','controls','renderEvidence','loadEvidence'])selection[name]=()=>{};
selection.showView=view=>calls.push(view);vm.createContext(selection);vm.runInContext(reader.slice(reader.indexOf('function selectMonthlyFocus('),reader.indexOf('function renderMonthlyDirections()')),selection);
selection.selectMonthlyFocus('parameters','distillation');assert.equal(selection.state.focusTarget,'parameters');assert.equal(selection.state.directionMode,false);assert.deepEqual(calls,['persist','updates']);
selection.selectMonthlyFocus();assert.equal(selection.state.focusTarget,'');assert.equal(selection.state.all,true);assert.deepEqual(calls,['persist','updates','persist','updates']);
console.log('PASS: monthly filter preserves the selected topic without entering the map reader; reset clears it');

// Overview must preserve technical notation and distinguish selection from coverage.
const monthly=fs.readFileSync(path.join(base,'monthly-routes.js'),'utf8');
const overviewNodes=new Map(['monthly-academic-metric','monthly-review-cutoff','monthly-selection-summary','monthly-object-coverage','monthly-key-changes'].map(id=>[id,new Node()]));
const overview={document:{getElementById:id=>overviewNodes.get(id)},detail:false,asOf:'2026-10-29',
 current:{locale:'zh'},priorCollection:true,unique:new Map([['p1',{}],['p2',{}]]),
 model:{reviewMap:new Map([['p1',{review_status:'method_results_checked'}],['p2',{review_status:'primary_abstract_checked'}]])},
 refs:[{summary_id:'p1',compression_topic_id:'parameters-precision'},{summary_id:'p1',compression_topic_id:'parameters-selection'},{summary_id:'p2',compression_topic_id:'kv_cache-precision'}],
 relevant:[{story_id:'s1',title_zh:'2:4与量化如何取舍：先算索引',question_zh:'question'},{story_id:'s2',title_zh:'ReCal：恢复质量',question_zh:'question'}],
 t:zh=>zh,pick:(r,k)=>r[k+'_zh'],node:(tag,text,cls)=>{const n=new Node(tag,text);n.className=cls;return n;}};
vm.createContext(overview);
vm.runInContext(monthly.slice(monthly.indexOf('    if(!detail){\n      const metric'),monthly.indexOf('    const topicPaperIds=')),overview);
assert.equal(overviewNodes.get('monthly-academic-metric').textContent,'2');
assert.match(overviewNodes.get('monthly-review-cutoff').textContent,/1 篇核对关键章节，1 篇仅摘要研读/);
assert.match(overviewNodes.get('monthly-object-coverage').textContent,/权重 1 · 激活 0 · KV Cache 1/,'Coverage deduplicates multiple methods on one object');
assert.equal(overviewNodes.get('monthly-key-changes').children[0].children[0].textContent,'2:4与量化如何取舍：先算索引');
assert.equal(overviewNodes.get('monthly-key-changes').children[1].children[0].textContent,'ReCal：恢复质量');
assert.equal((html.match(/id="scope-disclosure"/g)||[]).length,1);
assert(html.indexOf('id="scope-disclosure"')<html.indexOf('id="monthly-key-changes"'),'Selection boundary is accessible before the selected stories');
console.log('PASS: 2:4 notation, meaningful full titles, review-depth counts and visible selection explanation');

overview.relevant[0].selection_tier='key_progress';overview.relevant[0].selection_reason_zh='相同成本下比较稀疏与位宽';
overview.relevant[1].selection_tier='technical_watch';
overview.relevant.push({story_id:'s3',title_zh:'可重建但不可用',question_zh:'边界案例',selection_tier:'boundary_case'});
const overviewCode=monthly.slice(monthly.indexOf('    if(!detail){\n      const metric'),monthly.indexOf('    const topicPaperIds='));
vm.runInContext(overviewCode,overview);
assert.equal(overviewNodes.get('monthly-key-changes').children.length,1,'Watch and boundary items remain outside the headline selection');
assert.match(overviewNodes.get('monthly-selection-summary').textContent,/1 项重点进展 · 1 项技术观察 · 1 项边界案例/);
assert.equal(overviewNodes.get('monthly-key-changes').children[0].children[1].textContent,'相同成本下比较稀疏与位宽');
overview.relevant=overview.relevant.filter(s=>s.selection_tier==='technical_watch');
vm.runInContext(overviewCode,overview);
assert.equal(overviewNodes.get('monthly-key-changes').children.length,0,'A watch-only filter must not retain stale highlights');
assert.match(overviewNodes.get('monthly-selection-summary').textContent,/0 项重点进展 · 1 项技术观察 · 0 项边界案例/);
console.log('PASS: editorial tiers, selection rationale and filtered highlights remain consistent');

// Earlier editorial choices must not be presented as the result of full-corpus ranking.
assert.match(overviewNodes.get('monthly-selection-summary').textContent,/前期研读集合/);
assert.match(overviewNodes.get('monthly-selection-summary').textContent,/尚未完成与新增月度论文库的全面比较/);
const collectionRoot=new Node(),collection={...overview,root:collectionRoot,unique:new Map([['p1',{evidence_id:'e1'}],['p2',{evidence_id:'e2'}]]),
 model:{eventMap:new Map([['e1',{date_kind:'first_submission'}],['e2',{date_kind:'revision'}]])},
 node:(tag,text,cls)=>{const n=new Node(tag,text);n.className=cls;n.setAttribute=(key,value)=>{n[key]=value;};return n;}};
vm.createContext(collection);
const collectionCode=monthly.slice(monthly.indexOf('    if(priorCollection&&!detail){'),monthly.indexOf('    if(current.topicId&&contextPaperCount)'));
vm.runInContext(collectionCode,collection);
const words=n=>n.textContent+' '+n.children.map(words).join(' '),notice=collectionRoot.children[0];
assert.equal(notice.dataset.collectionOrigin,'prior-editorial');
assert.match(words(notice),/1 篇本月首发、1 篇旧文修订/);
assert.match(words(notice),/修订论文不计入本月首发矩阵/);
assert.match(words(notice),/相关性归类也不代表已优先阅读、核实入选或吸收到专题/);
assert.equal(flatten(notice).filter(n=>n.tagName==='li').length,4);
assert.match(words(notice),/每篇“入选理由”是编辑判断/);
assert.match(words(notice),/“阅读深度”来自该版本的原文核对记录/);
collection.priorCollection=false;collectionRoot.replaceChildren();vm.runInContext(collectionCode,collection);assert.equal(collectionRoot.children.length,0,'Do not mislabel other scopes as the prior collection');
console.log('PASS: prior editorial collection, independent curation stages and revision/first-submission boundary');
