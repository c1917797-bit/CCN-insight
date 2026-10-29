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
