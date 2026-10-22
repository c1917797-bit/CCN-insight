"""Check pagination completeness, retained provenance, foreign keys and attachments."""
from pathlib import Path
import hashlib
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT, DATA, manifest, rows, records, content_version

metadata = manifest()
errors = []
drift = []
check_import = '--check-import' in sys.argv
for table in metadata['tables']:
    data = records(table['name'])
    key = table['key_field']
    if check_import and len(data) != table['exported_rows']:
        errors.append((table['name'], 'count', len(data), table['exported_rows']))
    if len({r['key'] for r in data}) != len(data):
        errors.append((table['name'], 'duplicate key'))
    for record in data:
        row = record['row']
        assert record['key'] == row[key], (table['name'], record['key'])
        assert row.get('business_id', 'cloud-core') == 'cloud-core'
        assert row.get('topic_id', 'cloud_core') == 'cloud_core'
    if hashlib.sha256((ROOT / table['rows_file']).read_bytes()).hexdigest() != table['import_sha256']:
        drift.append(table['name'])
        if check_import: errors.append((table['name'], 'differs from initial import'))

edges = [
 ('ic_compression_topic_card_refs','card_id','ic_compression_topic_cards','card_id'),
 ('ic_compression_topic_card_refs','source_id','cloud_core_sources','source_id'),
 ('ic_compression_topic_events','compression_topic_id','ic_compression_topics','compression_topic_id'),
 ('ic_compression_topic_events','evidence_id','ic_evidence_items','evidence_id'),
 ('ic_compression_topic_events','source_id','cloud_core_sources','source_id'),
 ('ic_compression_topic_sections','compression_topic_id','ic_compression_topics','compression_topic_id'),
 ('ic_compression_research_routes','source_id','cloud_core_sources','source_id'),
 ('ic_compression_research_routes','supporting_card_id','ic_compression_topic_cards','card_id'),
 ('ic_paper_summaries','source_id','cloud_core_sources','source_id'),
 ('ic_paper_summary_events','summary_id','ic_paper_summaries','summary_id'),
 ('ic_paper_summary_events','evidence_id','ic_evidence_items','evidence_id'),
 ('ic_monthly_route_evidence','story_id','ic_monthly_route_insights','story_id'),
 ('ic_monthly_route_evidence','summary_id','ic_paper_summaries','summary_id'),
 ('ic_monthly_route_evidence','compression_topic_id','ic_compression_topics','compression_topic_id'),
 ('ic_evidence_items','source_id','cloud_core_sources','source_id'),
 ('ic_industry_update_changes','update_id','ic_industry_updates','update_id'),
 ('ic_industry_topic_assessments','compression_topic_id','ic_compression_topics','compression_topic_id'),
 ('ic_insight_report_assets','report_id','ic_insight_reports','report_id'),
 ('ic_insight_report_papers','source_id','cloud_core_sources','source_id'),
 ('ic_insight_report_papers','report_id','ic_insight_reports','report_id'),
 ('ic_ascend_validation_probes','assessment_id','ic_ascend_route_assessments','assessment_id'),
 ('ic_channel_families','family_id','ic_source_families','family_id'),
 ('ic_channel_families','channel_id','ic_channels','channel_id'),
 ('ic_channels','source_id','cloud_core_sources','source_id'),
]
for src, field, dst, target in edges:
    ids = {r[target] for r in rows(dst)}
    for record in rows(src):
        if record[field] not in ids:
            errors.append((src, field, record[field], dst))
for binding in rows('ic_paper_summary_events'):
    summary = next(x for x in rows('ic_paper_summaries') if x['summary_id']==binding['summary_id'])
    event = next(x for x in rows('ic_evidence_items') if x['evidence_id']==binding['evidence_id'])
    if not (binding['source_id']==summary['source_id']==event['source_id'] and binding['observed_version']==summary['observed_version']==event['observed_version']):
        errors.append(('ic_paper_summary_events', 'version/source mismatch', binding['evidence_id']))
deferred = [str(p.relative_to(ROOT)) for p in DATA.rglob('rows.jsonl') if '"content_ref"' in p.read_text(encoding='utf-8')]
assert not deferred, deferred
assets = json.loads((DATA / 'assets.json').read_text(encoding='utf-8')) if (DATA / 'assets.json').exists() else {'assets':[]}
asset_errors = []
for asset in assets['assets']:
    path = ROOT / asset['local_path']
    if asset['status']!='verified' or not path.exists():
        asset_errors.append(asset['asset_id'])
    elif path.stat().st_size != asset['expected_bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=asset['sha256']:
        asset_errors.append(asset['asset_id'])
if len(assets['assets']) != len(rows('ic_insight_report_assets')):
    asset_errors.append('asset inventory incomplete')
report = {'revision':metadata['revision'],'content_version':content_version(),'changed_since_import':drift,'tables':len(metadata['tables']),'rows':sum(len(records(t['name'])) for t in metadata['tables']),'checked_relationships':len(edges),'errors':errors,'deferred_content':deferred,'assets':len(assets['assets']),'asset_errors':asset_errors}
(ROOT / 'docs/tablegit-migration-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
if errors or asset_errors:
    raise SystemExit(1)
