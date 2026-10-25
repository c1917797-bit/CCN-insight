"""Build the maintained reader sources with the offline content transport."""
from pathlib import Path
import hashlib,json,shutil,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT,DATA,manifest,records,content_version

def build():
    source=ROOT/'original-reader/site';target=ROOT/'dist';version=content_version();revision=hashlib.sha256(version.encode()).hexdigest()[:40]
    module=target/'business_insight/cloud_core';data=module/'local-content';data.mkdir(parents=True,exist_ok=True)
    inventory=[]
    for path in source.rglob('*'):
        if not path.is_file():continue
        relative=path.relative_to(source);destination=target/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        raw=path.read_bytes()
        if path.suffix=='.html' and relative.parts[:2]==('business_insight','cloud_core'):
            text=raw.decode('utf-8');text=text.replace('<head>','<head>\n<script src="local-content-adapter.js"></script>',1);raw=text.encode('utf-8')
        destination.write_bytes(raw)
        inventory.append({'path':relative.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'transport_injected':path.suffix=='.html'})
    shutil.copy2(ROOT/'content/original-content-adapter.js',module/'local-content-adapter.js')
    tables={}
    for table in manifest()['tables']:
        name=table['name'];values=records(name);destination=data/'tables'/(name+'.json');destination.parent.mkdir(exist_ok=True)
        destination.write_text(json.dumps(values,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
        definition=json.loads((ROOT/table['rows_file']).with_name('definition.json').read_text(encoding='utf-8'))
        t={'count':len(values),'definition':definition}
        if len(values)>1000:
            buckets={}
            for value in values:
                bucket=hashlib.sha256(value['key'].encode()).hexdigest()[:2];buckets.setdefault(bucket,[]).append(value)
            folder=data/'shards'/name;folder.mkdir(parents=True,exist_ok=True)
            for bucket,values in buckets.items():(folder/(bucket+'.json')).write_text(json.dumps(values,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
            t['shards']=sorted(buckets)
        tables[name]=t
    (data/'manifest.json').write_text(json.dumps({'content_version':version,'revision':revision,'import_revision':manifest()['revision'],'tables':tables},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    from scripts.build_expert_index import build as build_expert_index
    expert_index=build_expert_index(data)
    assert expert_index['revision']==revision,'Research index revision drift'
    from scripts.audit_compression_inventory import build as build_inventory_audit
    inventory_audit=build_inventory_audit(data)
    assert inventory_audit['revision']==revision,'Inventory audit revision drift'
    from scripts.build_source_records import build as build_source_records
    build_source_records(module)
    assets=json.loads((DATA/'assets.json').read_text(encoding='utf-8'))['assets']
    for asset in assets:
        destination=target/asset['source_path'].lstrip('/');destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/asset['local_path'],destination)
    (target/'original-reader-version.json').write_text(json.dumps({'content_version':version,'local_revision':revision,'original_code_revision':json.loads((ROOT/'original-reader/SOURCE-MANIFEST.json').read_text(encoding='utf-8'))['revision'],'files':inventory,'status':'local_preview_not_published'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Original reader generated:',len(inventory),'source files;',len(tables),'local tables;',len(assets),'verified assets')

if __name__=='__main__':build()
