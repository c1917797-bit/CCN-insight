'use strict';
const assert=require('node:assert/strict');
require('../../business_insight/cloud_core/industry-updates.js');
const domain={business_id:'cloud-core',topic_id:'cloud_core'};
const bilingual=keys=>Object.fromEntries(keys.flatMap(key=>[[key+'_zh','示例'],[key+'_en','Example']]));
const directory={source_families:[{family_id:'family'}],channels:[{channel_id:'channel'}],channel_families:[{family_id:'family',channel_id:'channel'}]};
const fixture={
 revision:'revision-one',
 updates:[{...domain,...bilingual(['title','summary','scope','dependencies','boundary']),update_id:'update',family_id:'family',channel_id:'channel',source_id:'source',release_kind:'candidate',release_date_kind:'month_only',release_date:'2026-09',platform_published_date:'',checked_at:'2026-10-07'}],
 changes:[{...domain,...bilingual(['title','fact','conditions']),change_id:'change',update_id:'update',family_id:'family',source_id:'source',position:1}],
 links:[{...domain,link_id:'link',change_id:'change',update_id:'update',compression_topic_id:'topic',relation_kind:'deployment_adjacent'}],
 assessments:[{...domain,...bilingual(['title','fact_focus','relevance','impact','boundary','check']),link_id:'link',change_id:'change',update_id:'update',compression_topic_id:'topic',relation_kind:'deployment_adjacent',source_id:'source',source_locator:'Deprecated interfaces / exact entry',reviewed_at:'2026-10-09',review_method:'primary_passage_topic_causality_review',review_status:'verified',claim_kind:'evidence_based_analysis',position:1}],
 sources:[{source_id:'source',canonical_url:'https://example.org/official'}],
 topics:[{compression_topic_id:'topic'}]
};
const clone=()=>structuredClone(fixture);
assert.equal(LRIIndustryUpdates.validate(clone(),directory).updates.length,1);
for(const [name,mutate] of [
 ['invented day for month-only evidence',s=>s.updates[0].release_date='2026-09-01'],
 ['unknown date presented as dated',s=>s.updates[0].release_date_kind='unknown'],
 ['orphan change',s=>s.changes[0].update_id='missing'],
 ['orphan topic',s=>s.links[0].compression_topic_id='missing'],
 ['cross-domain claim',s=>s.changes[0].topic_id='other'],
 ['unknown release status',s=>s.updates[0].release_kind='released_and_validated'],
 ['untranslated fact',s=>s.changes[0].fact_en=''],
 ['missing original source',s=>s.sources=[]],
 ['unreviewed topic mapping',s=>s.assessments=[]],
 ['wrong assessment topic',s=>s.assessments[0].compression_topic_id='another-topic'],
 ['wrong assessment change',s=>s.assessments[0].change_id='another-change'],
 ['wrong assessment source',s=>s.assessments[0].source_id='unrelated-source'],
 ['unsupported directness',s=>s.assessments[0].relation_kind='compression_direct'],
 ['missing passage locator',s=>s.assessments[0].source_locator=''],
 ['missing localized causal analysis',s=>s.assessments[0].impact_en=''],
 ['claim pretending local measurement',s=>s.assessments[0].claim_kind='locally_measured'],
 ['unknown review status',s=>s.assessments[0].review_status='approved_by_url_only']
]) { const value=clone();mutate(value);assert.throws(()=>LRIIndustryUpdates.validate(value,directory),undefined,name); }
for(const review_status of ['excluded','pending']){
 const snapshot=clone();snapshot.assessments[0].review_status=review_status;
 LRIIndustryUpdates.validate(snapshot,directory);
 assert.deepEqual(LRIIndustryUpdates.forTopic(snapshot,'topic'),[],review_status+' evidence must not enter a research topic');
 assert.deepEqual(LRIIndustryUpdates.reviewedLinks(snapshot),[],review_status+' evidence must not leak via source-catalogue links');
}
assert.equal(LRIIndustryUpdates.forTopic(clone(),'topic')[0].assessment.impact_en,'Example');
assert.deepEqual(LRIIndustryUpdates.forTopic(clone(),'unrelated-topic'),[]);
(async()=>{
 let calls=[];
 globalThis.LRITableGit={
  async loadTablePage(table,options){calls.push({table,options});const key={ic_industry_updates:'updates',ic_industry_update_changes:'changes',ic_industry_change_topics:'links',ic_industry_topic_assessments:'assessments'}[table];return{revision:options.expectedRevision,records:fixture[key],page:{total:fixture[key].length,truncated:false}};},
  async loadRowsByKeys(table,keys,revision){calls.push({table,keys,revision});return{revision,records:table==='cloud_core_sources'?fixture.sources:fixture.topics};}
 };
 const snapshot=await LRIIndustryUpdates.load('revision-one',directory);
 assert.equal(snapshot.changes.length,1);
 assert(calls.filter(c=>c.options).every(c=>c.options.filterField==='topic_id'&&c.options.filterValue==='cloud_core'&&c.options.expectedRevision==='revision-one'&&c.options.limit===100));
 assert(calls.filter(c=>c.keys).every(c=>c.keys.length===1&&c.revision==='revision-one'));
 LRITableGit.loadTablePage=async()=>({revision:'stale',records:[],page:{total:0,truncated:false}});
 await assert.rejects(()=>LRIIndustryUpdates.load('revision-one',directory),/revision/);
 console.log('Industry release contracts: primary provenance, causal-review coverage, exclusion/pending isolation, localization, bounded hydration and exact-revision checks passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
