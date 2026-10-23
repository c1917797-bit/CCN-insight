"""Check maintained UI delivery, local corpus/shards and exact report assets."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT,DATA,records,content_version

source=ROOT/'original-reader/site';target=ROOT/'dist';module=target/'business_insight/cloud_core'
checked=0
for path in source.rglob('*'):
    if not path.is_file():continue
    relative=path.relative_to(source);actual=(target/relative).read_bytes();expected=path.read_bytes()
    if path.suffix=='.html' and relative.parts[:2]==('business_insight','cloud_core'):
        actual=actual.replace(b'\n<script src="local-content-adapter.js"></script>',b'',1)
    assert actual==expected,'Original UI changed: '+str(relative)
    checked+=1
meta=json.loads((module/'local-content/manifest.json').read_text(encoding='utf-8'))
assert meta['content_version']==content_version()
for name,table in meta['tables'].items():
    values=json.loads((module/'local-content/tables'/(name+'.json')).read_text(encoding='utf-8'))
    assert values==records(name) and len(values)==table['count'],name
    if table.get('shards'):
        sharded=[r for prefix in table['shards'] for r in json.loads((module/'local-content/shards'/name/(prefix+'.json')).read_text(encoding='utf-8'))]
        assert sorted(sharded,key=lambda r:r['key'])==sorted(values,key=lambda r:r['key']),name
        for prefix in table['shards']:
            for row in json.loads((module/'local-content/shards'/name/(prefix+'.json')).read_text(encoding='utf-8')):
                assert hashlib.sha256(row['key'].encode()).hexdigest().startswith(prefix)
assets=json.loads((DATA/'assets.json').read_text(encoding='utf-8'))['assets']
for asset in assets:
    assert hashlib.sha256((target/asset['source_path'].lstrip('/')).read_bytes()).hexdigest()==asset['sha256']
print('PASS:',checked,'reader source files delivered with transport injection;',len(meta['tables']),'tables;',len(assets),'matching report assets')
