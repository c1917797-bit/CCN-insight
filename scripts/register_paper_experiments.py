"""Register an explicitly reviewed batch; existing records stay revision-fenced."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compression_store import DATA, ROOT, rows, manifest
from paper_experiments import TABLE, FIELDS, TEXT_FIELDS, validate

def register(seed):
    values = json.loads(seed.read_text(encoding='utf-8'))
    if any(t['name'] == TABLE for t in manifest()['tables']):
        raise ValueError('Table already registered; edit existing records through compression_maintenance.apply_change.')
    validate(values, rows('cloud_core_sources'), rows('ic_compression_topic_cards'),
             rows('ic_compression_topics'), rows('ic_compression_topic_card_refs'))
    folder = DATA / 'tables' / TABLE
    folder.mkdir(parents=True, exist_ok=False)
    definition = {
        'schema': 'mcpgit.table.v2',
        'description': 'One reviewed author experiment per record. Joint W/A/KV results are linked to topics, never copied; different conditions remain separate.',
        'key_field': 'experiment_id',
        'fields': {f: {'projection': 'default', 'required': True,
                       'role': 'key' if f == 'experiment_id' else 'value', 'source': None,
                       'type': 'text' if f in TEXT_FIELDS else 'integer'} for f in FIELDS},
        'required_fields': FIELDS,
        'indexes': [{'field': 'source_id', 'name': 'idx_source_id'}],
    }
    (folder / 'definition.json').write_text(json.dumps(definition, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    payload = ''.join(json.dumps({'key': r['experiment_id'], 'row': r, 'deleted': False,
                                 'row_version': 1, 'text_match': None}, ensure_ascii=False, separators=(',', ':')) + '\n' for r in values)
    (folder / 'rows.jsonl').write_text(payload, encoding='utf-8', newline='\n')
    metadata = manifest()
    metadata['tables'].append({
        'name': TABLE, 'path': 'data/tables/' + TABLE, 'revision': 'local-primary-experiments-20261113',
        'source_row_count': len(values), 'exported_rows': len(values),
        'filters': [{'field': 'business_id', 'op': 'eq', 'value': 'cloud-core'}, {'field': 'topic_id', 'op': 'eq', 'value': 'cloud_core'}],
        'rows_file': f'data/compression/tables/{TABLE}/rows.jsonl',
        'import_sha256': hashlib.sha256((folder / 'rows.jsonl').read_bytes()).hexdigest(),
        'key_field': 'experiment_id', 'provenance_kind': 'local_primary_paper_section_review',
    })
    (DATA / 'manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Registered {len(values)} reviewed experiments in {TABLE}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('seed', type=Path)
    register(parser.parse_args().seed)
