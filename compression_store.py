"""Canonical local compression content. No TableGit request is made at runtime."""
from functools import lru_cache
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data' / 'compression'

@lru_cache(maxsize=None)
def records(name):
    path = DATA / 'tables' / name / 'rows.jsonl'
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]

def rows(name):
    return [r['row'] for r in records('cloud_core_sources' if name == 'compression_sources' else name) if not r.get('deleted')]

def manifest():
    return json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))

def content_version():
    """Identify actual editable content, independently of the import revision."""
    digest = hashlib.sha256()
    for table in sorted(manifest()['tables'], key=lambda t:t['name']):
        for filename in ('definition.json', 'rows.jsonl'):
            path = DATA / 'tables' / table['name'] / filename
            digest.update((table['name']+'/'+filename+'\n').encode())
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    digest.update((DATA/'assets.json').read_bytes())
    return 'compression-' + digest.hexdigest()[:20]

def clear_cache():
    records.cache_clear()
