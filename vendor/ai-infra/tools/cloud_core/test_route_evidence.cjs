'use strict';
const assert=require('node:assert/strict');
require('../../business_insight/cloud_core/route-evidence.js');
const fields=['label','representation','preparation','conditions','result','runtime','boundary','decision','probe','figure_caption'];
const row={assessment_id:'assessment',route_id:'route',source_id:'source',business_id:'cloud-core',topic_id:'cloud_core',compression_topic_id:'topic',review_status:'verified',review_depth:'section_review',reviewed_at:'2026-10-09',claim_kind:'evidence_based_analysis',result_kind:'author_report',position:0,observed_version:'2210.17323v2',paper_url:'https://arxiv.org/html/2210.17323v2',figure_url:'https://arxiv.org/html/2210.17323v2/gptq.svg',figure_locator:'S4.F2',result_locator:'S5.T6',...Object.fromEntries(fields.flatMap(f=>[[f+'_zh','正文'],[f+'_en','Reviewed text']]))};
const dossier={revision:'revision',topic:'topic',routes:[{route_id:'route',source_id:'source',claim_status:'literature_mechanism'}],sources:[{source_id:'source',canonical_url:'https://arxiv.org/abs/2210.17323'}]};
assert.equal(LRIRouteEvidence.validate([row],dossier).length,1);
for(const [name,change] of [
 ['foreign topic',r=>r.compression_topic_id='other'],
 ['orphan route',r=>r.route_id='other'],
 ['wrong source',r=>r.source_id='other'],
 ['unreviewed passage',r=>r.review_depth='abstract_review'],
 ['unverified',r=>r.review_status='pending'],
 ['pretended local gain',r=>r.result_kind='ascend_measurement'],
 ['missing conditions',r=>r.conditions_en=''],
 ['wrong paper',r=>r.paper_url='https://arxiv.org/html/2306.00978v6'],
 ['wrong version',r=>r.observed_version='2210.17323v3'],
 ['foreign figure',r=>r.figure_url='https://other.org/gptq.svg'],
 ['another version figure',r=>r.figure_url='https://arxiv.org/html/2210.17323v3/gptq.svg'],
 ['credential URL',r=>r.figure_url+='?token=secret'],
 ['missing locator',r=>r.result_locator=''],
]){const value=structuredClone(row);change(value);assert.throws(()=>LRIRouteEvidence.validate([value],dossier),undefined,name);}
assert.throws(()=>LRIRouteEvidence.validate([row,row],dossier),/duplicate/);
assert.deepEqual(LRIRouteEvidence.validate([],dossier),[]);
(async()=>{
 let calls=0;
 const api={async loadTablePage(table,options){calls++;assert.equal(table,'ic_compression_route_assessments');assert.deepEqual(options,{filterField:'compression_topic_id',filterValue:'topic',expectedRevision:'revision',offset:0,limit:20});return {revision:'revision',records:[row],page:{total:1,truncated:false}};}};
 assert.equal((await LRIRouteEvidence.load(dossier,api)).rows.length,1);assert.equal(calls,1);
 await assert.rejects(()=>LRIRouteEvidence.load(dossier,{loadTablePage:async()=>({revision:'stale',records:[row],page:{total:1,truncated:false}})}),/revision/);
 await assert.rejects(()=>LRIRouteEvidence.load(dossier,{loadTablePage:async()=>({revision:'revision',records:[row],page:{total:2,truncated:true}})}),/incomplete/);
 console.log('Primary route evidence: topic/source/version identity, passage review, result conditions, localization, safe original figures, bounded lazy read and fail-closed pagination passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
