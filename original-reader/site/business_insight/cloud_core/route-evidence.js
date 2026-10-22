/* Primary-paper route comparisons, bounded to one topic and one TableGit revision. */
(() => {
 'use strict';
 const check=(ok,message)=>{if(!ok)throw new Error('Route evidence: '+message);};
 const fields=['label','representation','preparation','conditions','result','runtime','boundary','decision','probe','figure_caption'];
 function validate(rows,dossier){
  check(dossier&&dossier.revision&&dossier.topic&&Array.isArray(rows)&&rows.length<=20,'invalid scoped snapshot');
  const seen=new Set(),routes=new Map(dossier.routes.map(r=>[r.route_id,r])),sources=new Map(dossier.sources.map(r=>[r.source_id,r]));
  for(const row of rows){
   const route=routes.get(row.route_id),source=sources.get(row.source_id);
   check(row.business_id==='cloud-core'&&row.topic_id==='cloud_core'&&row.compression_topic_id===dossier.topic&&!seen.has(row.assessment_id)&&row.assessment_id,'foreign or duplicate assessment');seen.add(row.assessment_id);
   check(route&&route.source_id===row.source_id&&source&&route.claim_status==='literature_mechanism','unbound primary route');
   check(row.review_status==='verified'&&row.review_depth==='section_review'&&row.claim_kind==='evidence_based_analysis'&&row.result_kind==='author_report','unqualified evidence');
   check(/^\d{4}-\d{2}-\d{2}$/.test(row.reviewed_at)&&Number.isSafeInteger(row.position)&&fields.every(k=>['zh','en'].every(l=>typeof row[k+'_'+l]==='string'&&row[k+'_'+l].trim())),'missing review or localization');
   const canonical=new URL(source.canonical_url),paper=new URL(row.paper_url),figure=new URL(row.figure_url);
   const id=canonical.pathname.match(/^\/abs\/(\d{4}\.\d{4,5})(?:v\d+)?$/)?.[1];
   check(id&&canonical.hostname==='arxiv.org'&&paper.protocol==='https:'&&paper.hostname===canonical.hostname&&paper.pathname==='/html/'+row.observed_version&&new RegExp('^'+id.replace('.','\\.')+'v[1-9]\\d*$').test(row.observed_version),'paper identity/version mismatch');
   check(figure.origin===paper.origin&&figure.pathname.startsWith(paper.pathname+'/')&&/\.(svg|png|jpg|jpeg|webp)$/.test(figure.pathname),'foreign figure');
   check([paper,figure].every(u=>!u.username&&!u.password&&!u.search&&!u.hash)&&[row.figure_locator,row.result_locator].every(v=>/^S\d+(?:\.\d+)*\.[FT]\d+$/.test(v)),'unsafe or missing passage locator');
  }
  return rows.slice().sort((a,b)=>a.position-b.position);
 }
 async function load(dossier,api){
  const result=await api.loadTablePage('ic_compression_route_assessments',{filterField:'compression_topic_id',filterValue:dossier.topic,expectedRevision:dossier.revision,offset:0,limit:20});
  check(result.revision===dossier.revision,'revision mismatch');
  check(result.page&&Number.isSafeInteger(result.page.total)&&result.page.total<=20&&result.page.total===result.records.length&&!result.page.truncated,'incomplete bounded read');
  return {revision:dossier.revision,topic:dossier.topic,rows:validate(result.records,dossier)};
 }
 globalThis.LRIRouteEvidence=Object.freeze({load,validate});
})();

