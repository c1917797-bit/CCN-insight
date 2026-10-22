"""Verify both staged modules still match the sole content source."""
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT, DATA, content_version

receipt=json.loads((DATA/'staged-release.json').read_text(encoding='utf-8'))
assert receipt['content_version']==content_version(),'Staged outputs are stale; rebuild first.'
versions=set();inventories=[]
for target,relative in receipt['targets'].items():
    root=ROOT/relative
    marker=json.loads((root/'compression-version.json').read_text(encoding='utf-8'))
    assert marker['target']==target and marker['status']=='staged_not_published'
    versions.add(marker['content_version']);inventories.append(marker['shared_files'])
    for path,sha in marker['shared_files'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==sha,(target,path)
    entry=(root/marker['entrypoint'].split('#')[0]).read_text(encoding='utf-8')
    assert 'local-content-adapter.js' in entry
    data=json.loads((root/'business_insight/cloud_core/local-content/manifest.json').read_text(encoding='utf-8'))
    assert data['content_version']==marker['content_version']
assert len(versions)==1 and inventories[0]==inventories[1]
assert receipt['online_sites_changed'] is False
print('PASS:',next(iter(versions)),len(inventories[0]),'identical shared files; both targets staged only')
