"""Validate compression view contracts and an optional exact native snapshot."""
import argparse, hashlib, json, re, sys
from pathlib import Path

MONTHLY_TABLE_CONTRACTS = {
    'ic_monthly_scopes': ('scope_id', {'period_id'}),
    'ic_evidence_items': ('evidence_id', {'source_id'}),
    'ic_monthly_evidence_cells': ('link_id', {'scope_cell_key', 'scope_id', 'period_id', 'evidence_id', 'cell_id'}),
    'ic_monthly_cell_reviews': ('review_id', {'scope_id', 'period_id', 'cell_id', 'scope_cell_key'}),
}

def validate_ui(root, page_root=None, archive_path=None, site_path=None):
    page=page_root or root/'business_insight/cloud_core' 
    html=(page/'index.html').read_text(encoding='utf-8')
    archive=(archive_path or page/'archive.html').read_text(encoding='utf-8')
    js=(page/'compression.js').read_text(encoding='utf-8')
    for text in [html,archive]:
        assert text.count('insight-executive.css')==1,'one shared stylesheet per view'
        assert not re.search(r'<style|\sstyle=',text,re.I),'inline style forbidden'
        assert 'lri-shell.js' in text and 'lri-page-translation' in text,'shared shell and UI translation'
    keys=set(re.findall(r'data-i18n-key="([^"]+)"',html))
    packs={lang:json.loads((page/'data'/f'focus-ui.{lang}.json').read_text(encoding='utf-8')) for lang in ['zh','en']}
    assert set(packs['zh']['strings'])==set(packs['en']['strings']),'matching locale coverage'
    for lang,pack in packs.items():
        assert keys<=pack['strings'].keys(),(lang,keys-pack['strings'].keys())
        assert pack['coverage']['mode']=='ui','source Chinese is not fake translated'
    assert "loadTopicWorkbench('cloud_core')" in js and 'expectedRevision:revision' in js
    # Each independently loaded view fences late responses at a pinned revision.
    compact_js=re.sub(r'\s+', '', js)
    epochs=['epoch','periodEpoch','scopeEpoch','evidenceEpoch','legacyEpoch','detailEpoch','listEpoch']
    for epoch in epochs:
        assert epoch in js and 'request!==state.'+epoch in compact_js,(epoch,'missing request fence')
    assert 'revision!==state.revision' in compact_js,'async replies must retain their pinned revision'
    assert "page('monthly_scopes','period_id'" in compact_js,'month-scoped collection ranges'
    assert "page('monthly_cell_reviews','scope_id'" in compact_js,'scope-scoped 42-cell reviews'
    assert "page('monthly_evidence_cells','scope_cell_key'" in compact_js and 'limit:20' in compact_js,'bounded selected-cell evidence'
    assert "loadRowsByKeys('ic_evidence_items',ids,revision)" in compact_js,'exact-key evidence joins'
    assert 'state.family' not in js and 'familyMethods' not in js,'one canonical object/method taxonomy'
    assert 'scope_cell_key' in js and 'sample_count' in js,'scoped samples retain canonical cell identities'
    assert 'scope.coverage_note' in js and 'monthly-status' in js,'monthly coverage must be visible'
    assert 'evidence-prev' in html and 'evidence-next' in html and 'evidence-retry' in html,'evidence paging and retry controls'
    assert re.search(r'<details\b[^>]*id="legacy-panel"',html),'global statistics remain a collapsed legacy view'
    ids=re.findall(r'\bid="([^\"]+)"',html)
    assert len(ids)==len(set(ids)),'unique DOM ids'
    assert set(re.findall(r"\$\('([^']+)'\)",js))<=set(ids),'JS references only declared DOM ids'
    literal_labels=set(re.findall(r"label\('([^']+)'\)",js))
    for lang,pack in packs.items():
        assert literal_labels<=pack['strings'].keys(),(lang,literal_labels-pack['strings'].keys())
    assert 'innerHTML' not in js and 'contenteditable' not in html,'source must be inert text'
    assert 'document.createTextNode' in js and "element('pre',row.body)" in js
    assert 'cloud_core_sources' in js and 'loadRowsByKeys' in js,'canonical exact-key source joins'
    assert 'staging-v1' not in js and 'workbench.json' not in js and 'seed.json' not in js
    assert "row.inference_scope!=='training_only'" in js and "row.stage!=='training'" in js
    assert 'state.revision=\'\'' in js and 'controls(false)' in js,'fail closed'
    assert "archive.html" in html and 'cloud-core.js' in archive
    site=json.loads((site_path or root/'.mcpgit/site.json').read_text(encoding='utf-8'))
    from compression_schema import DEFINITIONS
    for name,definition in DEFINITIONS.items():
        hosted=site['tables'][name]
        assert hosted['path']=='data/tables/'+name and hosted['writable'] is False
        assert {'topic_id','business_id',definition['key_field']}<=set(hosted['filter_fields'])
        assert all(f['type'] in {'string','integer','number','markdown','text'} for f in definition['fields'].values()),'scalar business schemas'
    for name,(key_field,query_filters) in MONTHLY_TABLE_CONTRACTS.items():
        hosted=site['tables'][name]
        assert hosted['path']=='data/tables/'+name and hosted['writable'] is False,(name,'read-only native table exposure')
        assert {'topic_id','business_id',key_field}|query_filters<=set(hosted['filter_fields']),(name,'missing bounded query filter')
    from validate_lineage import validate_lineage_site
    result={'ui':'pass','tables':len(DEFINITIONS),'monthly_readonly_tables':len(MONTHLY_TABLE_CONTRACTS),'locale_keys':len(keys|literal_labels),'request_fences':epochs}
    result.update(validate_lineage_site(site))
    from validate_research_workbench import validate_workbench_site
    result.update(validate_workbench_site(site))
    from validate_collection import validate_collection_site, validate_collection_ui
    result.update(validate_collection_site(site))
    result.update(validate_collection_ui(root))
    return result

def validate_snapshot(path):
    from compression_schema import DEFINITIONS
    fixture=json.loads(path.read_text(encoding='utf-8')); assert re.fullmatch(r'[0-9a-f]{40}',fixture['revision'])
    tables={name:[frame['row'] for frame in frames if not frame.get('deleted')] for name,frames in fixture['tables'].items()}
    keys={}
    for name,d in DEFINITIONS.items():
        rows=tables[name]; keys[name]={row[d['key_field']] for row in rows}
        assert len(keys[name])==len(rows),(name,'duplicate key')
        for row in rows:
            assert row['business_id']=='cloud-core' and row['topic_id']=='cloud_core'
            for required in d['required_fields']: assert required in row and row[required] is not None,(name,required)
            for field,value in row.items():
                assert field in d['fields'],(name,'unknown',field)
                if value is None: continue
                kind=d['fields'][field]['type']
                assert not isinstance(value,(dict,list)),(name,'non-scalar',field)
                if kind in {'string','text','markdown'}: assert isinstance(value,str)
                if kind=='integer': assert isinstance(value,int) and not isinstance(value,bool)
                if kind=='number': assert isinstance(value,(int,float)) and not isinstance(value,bool)
    relations=[('ic_method_families','method_id','ic_methods'),('ic_method_families','family_id','ic_families'),
        ('ic_cells','object_id','ic_objects'),('ic_cells','method_id','ic_methods'),
        ('ic_placements','technique_id','ic_techniques'),('ic_placements','cell_id','ic_cells'),
        ('ic_trend_observations','period_id','ic_trend_periods'),('ic_trend_observations','cell_id','ic_cells'),
        ('ic_tasks','primary_cell_id','ic_cells'),('ic_measurements','task_id','ic_tasks'),
        ('ic_measurements','benchmark_id','ic_benchmarks'),('ic_decisions','task_id','ic_tasks'),
        ('ic_decisions','measurement_id','ic_measurements'),('ic_source_refs','technique_id','ic_techniques'),
        ('ic_flywheel_stages','next_stage_id','ic_flywheel_stages')]
    for name,field,target in relations:
        assert all(row[field] in keys[target] for row in tables[name]),(name,field,'dangling')
    docs={row['document_id']:row for row in tables['cloud_core_documents']}
    for name in DEFINITIONS:
        for row in tables[name]:
            if row.get('source_document_id'): assert row['source_document_id'] in docs,(name,'missing document')
    for row in docs.values():
        assert row['business_id']=='cloud-core' and isinstance(row['body'],str)
        assert hashlib.sha256(row['body'].encode()).hexdigest()==row['body_sha256'],('body hash',row['document_id'])
    assert {(r['object_id'],r['method_id']) for r in tables['ic_cells']}=={(o,m) for o in keys['ic_objects'] for m in keys['ic_methods']}
    observations=tables['ic_trend_observations']
    assert len({(r['period_id'],r['cell_id']) for r in observations})==len(observations)
    assert len([r for r in tables['ic_objects'] if r['scope']=='primary'])==4
    assert not any(r['method_id']=='G' for r in tables['ic_method_families'])
    sources={row['source_id']:row for row in tables['cloud_core_sources']}
    refs={row['technique_id']:row for row in tables['ic_source_refs']}
    for row in tables['ic_techniques']:
        assert not row['primary_url'],'URL authority stays in shared canonical sources'
        if row['verification_status']=='primary_mechanism_checked': assert row['technique_id'] in refs
    for ref in refs.values():
        assert ref['source_id'] in sources and ref['checked_scope']=='mechanism_only'
        assert sources[ref['source_id']]['canonical_url'].startswith('https://arxiv.org/abs/')
    for row in tables['ic_placements']:
        if row['applicability']=='training_only': assert row['stage']=='training'
    stages={r['stage_id']:r for r in tables['ic_flywheel_stages']}; visited=set(); current=min(stages,key=lambda k:stages[k]['position'])
    first=current
    while current not in visited:
        visited.add(current);current=stages[current]['next_stage_id']
    assert current==first and visited==set(stages),'flywheel must close across all stages'
    return {'snapshot':'pass','revision':fixture['revision'],'row_counts':{n:len(tables[n]) for n in DEFINITIONS},'relations':len(relations),'body_hashes':len(docs)}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path);parser.add_argument('--snapshot',type=Path)
    parser.add_argument('--page-root',type=Path);parser.add_argument('--archive',type=Path);parser.add_argument('--site-config',type=Path)
    parser.add_argument('--schema-file',type=Path,help='Optional read-only schema source for a split local preview.')
    args=parser.parse_args();root=args.root or Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(args.schema_file.parent if args.schema_file else root/'tools/cloud_core'))
    result=validate_ui(root,args.page_root,args.archive,args.site_config)
    from validate_pyramid import validate_pyramid, validate_pyramid_snapshot
    result.update(validate_pyramid(args.page_root or root/'business_insight/cloud_core'))
    if args.snapshot:
        result.update(validate_snapshot(args.snapshot))
        result.update(validate_pyramid_snapshot(args.snapshot))
        from validate_monthly import validate_monthly_snapshot
        result.update(validate_monthly_snapshot(args.snapshot))
        from validate_lineage import validate_lineage_snapshot
        result.update(validate_lineage_snapshot(args.snapshot))
        from validate_research_workbench import validate_workbench_fixture
        result.update(validate_workbench_fixture(json.loads(args.snapshot.read_text(encoding='utf-8'))))
        from validate_collection import validate_collection_fixture
        result.update(validate_collection_fixture(json.loads(args.snapshot.read_text(encoding='utf-8'))))
    print(json.dumps(result,ensure_ascii=False,indent=2))


