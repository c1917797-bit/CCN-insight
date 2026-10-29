// Exercise the reader's runtime contract with real canonical data, not a second schema.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
function rows(name){return fs.readFileSync(path.join(root,'data/compression/tables',name,'rows.jsonl'),'utf8').trim().split(/\r?\n/).map(JSON.parse).filter(r=>!r.deleted).map(r=>r.row);}
const context=vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(root,'original-reader/site/business_insight/cloud_core/industry-updates.js'),'utf8'),context);
const reader=context.LRIIndustryUpdates;
const snapshot={updates:rows('ic_industry_updates'),changes:rows('ic_industry_update_changes'),links:rows('ic_industry_change_topics'),assessments:rows('ic_industry_topic_assessments'),sources:rows('cloud_core_sources'),topics:rows('ic_compression_topics')};
const directory={source_families:rows('ic_source_families'),channels:rows('ic_channels'),channel_families:rows('ic_channel_families')};
reader.validate(snapshot,directory);
for(const link of reader.reviewedLinks(snapshot))assert(reader.forTopic(snapshot,link.compression_topic_id).some(x=>x.link.link_id===link.link_id),'Verified industry evidence must be reachable from its topic');
const invalid=JSON.parse(JSON.stringify(snapshot));invalid.assessments[0].review_method='unreviewed_import';
assert.throws(()=>reader.validate(invalid,directory),/assessment review/);
const current=snapshot.updates.filter(r=>r.release_date?.startsWith('2026-10')&&snapshot.assessments.some(a=>a.update_id===r.update_id&&a.review_status==='verified'));
console.log(`PASS: actual industry data satisfy reader contract; ${current.length} reviewed October releases; verified topic links reachable; unreviewed imports rejected`);
