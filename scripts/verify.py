"""Verify exported IDs, directory joins and independently built portal files."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
def load(name):
    return json.loads((ROOT / 'data/directory' / (name + '.json')).read_text(encoding='utf-8'))
def rows(name):
    return [x['row'] for x in load(name)['rows'] if not x.get('deleted')]
channels = rows('ic_channels')
families = rows('ic_source_families')
sources = rows('cloud_core_sources')
members = rows('ic_channel_families')
c = {r['channel_id'] for r in channels}
f = {r['family_id'] for r in families}
s = {r['source_id'] for r in sources}
assert len(c) == len(channels) and len(f) == len(families) and len(s) == len(sources)
assert all(r['source_id'] in s for r in channels)
assert all(r['channel_id'] in c and r['family_id'] in f for r in members)
assert {r['channel_id'] for r in members} == c
for name in ['ic_channels', 'ic_source_families', 'ic_channel_families', 'ic_industry_source_scopes']:
    pack = load(name)
    assert len(pack['rows']) == pack['row_count'], name
for name in ['index.html', 'home.css', 'home.js', 'sources.html', 'sources.csv']:
    assert (ROOT / 'dist' / name).stat().st_size > 0, name
count = 0
for folder in (ROOT / 'data/tables').iterdir():
    keys = set()
    for part in folder.glob('rows-*.jsonl'):
        for line in part.read_text(encoding='utf-8').splitlines():
            record = json.loads(line)
            assert record['key'] not in keys
            keys.add(record['key'])
            count += 1
assert count == 10953, count
print(f'PASS: {len(f)} families, {len(c)} channels, source joins, 10953 legacy rows, portal artifacts')
