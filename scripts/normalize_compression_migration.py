"""Convert revision-bound query pages into one editable JSONL file per table."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'compression'
manifest = json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))
archive = ROOT.parent / '.tmp' / ('tablegit-export-' + manifest['revision'])
archive.mkdir(parents=True, exist_ok=True)
for table in manifest['tables']:
    if 'parts' not in table:
        continue
    records, keys = [], set()
    for part in table['parts']:
        path = ROOT / part
        raw = path.read_bytes()
        page = json.loads(raw)
        assert page['revision'] == manifest['revision']
        assert page['row_count'] == table['exported_rows']
        for record in page['rows']:
            assert record['key'] not in keys
            assert record['key'] == record['row'][table['definition']['key_field']]
            assert not record.get('deleted')
            keys.add(record['key'])
            records.append(record)
        archived = archive / table['name'] / path.name
        archived.parent.mkdir(parents=True, exist_ok=True)
        archived.write_bytes(raw)
    assert len(records) == table['exported_rows']
    folder = DATA / 'tables' / table['name']
    encoded = ''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in sorted(records, key=lambda r: r['key']))
    destination = folder / 'rows.jsonl'
    destination.write_text(encoded, encoding='utf-8')
    (folder / 'definition.json').write_text(json.dumps(table.pop('definition'), ensure_ascii=False, indent=2), encoding='utf-8')
    table['rows_file'] = destination.relative_to(ROOT).as_posix()
    table['import_sha256'] = hashlib.sha256(destination.read_bytes()).hexdigest()
    table['key_field'] = json.loads((folder / 'definition.json').read_text(encoding='utf-8'))['key_field']
    for part in table.pop('parts'):
        (ROOT / part).unlink()
manifest['maintenance'] = 'Edit only data/compression/tables/*/rows.jsonl; imported copies and views are generated.'
(DATA / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print('Normalized', len(manifest['tables']), 'tables;', sum(t['exported_rows'] for t in manifest['tables']), 'records')
