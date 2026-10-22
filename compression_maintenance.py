"""Revision-fenced local edits; publication is deliberately outside this module."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from compression_store import ROOT, DATA, manifest, records, content_version, clear_cache

def table_info(name):
    for t in manifest()['tables']:
        if t['name']==name:return t
    raise ValueError('Unknown content table')

def validate_updates(definition, old_row, updates):
    protected={definition['key_field'],'business_id','topic_id'}
    if not isinstance(updates,dict) or not updates:raise ValueError('No changed fields')
    for key,value in updates.items():
        if key in protected or key not in definition['fields']:raise ValueError('Field is protected or unknown: '+key)
        spec=definition['fields'][key];kind=spec['type']
        if spec.get('required') and value is None:raise ValueError('Required field: '+key)
        if value is None:continue
        if kind in ('text','string') and not isinstance(value,str):raise ValueError('Text required: '+key)
        if kind=='integer' and (not isinstance(value,int) or isinstance(value,bool)):raise ValueError('Integer required: '+key)
        if kind in ('number','float') and (not isinstance(value,(int,float)) or isinstance(value,bool)):raise ValueError('Number required: '+key)
        if kind=='boolean' and not isinstance(value,bool):raise ValueError('Boolean required: '+key)
        if isinstance(value,str) and re.search(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN .*PRIVATE KEY',value):raise ValueError('Credential-like content is not allowed')
    result=dict(old_row);result.update(updates)
    return result

def apply_change(table,key,updates,expected_version):
    lock=DATA/'.edit.lock'
    fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    path=None;original=None;written=False
    try:
        os.write(fd,str(os.getpid()).encode())
        if expected_version!=content_version():raise ValueError('Content changed. Reload the record before saving.')
        info=table_info(table);path=ROOT/info['rows_file']
        definition=json.loads((path.parent/'definition.json').read_text(encoding='utf-8'))
        original=path.read_bytes(); data=[json.loads(line) for line in original.decode('utf-8').splitlines() if line.strip()]
        record=next((r for r in data if r['key']==key),None)
        if record is None:raise ValueError('Record does not exist')
        record['row']=validate_updates(definition,record['row'],updates)
        new=''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in data).encode('utf-8')
        if new==original:return {'version':expected_version,'changed':False}
        change_id=str(uuid.uuid4()); backup=ROOT/'.maintenance/backups'/change_id
        backup.mkdir(parents=True);(backup/'rows.jsonl').write_bytes(original)
        temporary=path.with_suffix('.tmp');temporary.write_bytes(new);os.replace(temporary,path);written=True;clear_cache()
        result=subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/verify_tablegit_migration.py')],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        if result.returncode:raise ValueError('Content relationship validation failed; the edit was rolled back. '+result.stdout[-1500:])
        version=content_version()
        entry={'change_id':change_id,'time_unix':int(time.time()),'table':table,'key':key,'fields':list(updates),'before_version':expected_version,'after_version':version,'before_sha256':hashlib.sha256(original).hexdigest(),'after_sha256':hashlib.sha256(new).hexdigest()}
        history=ROOT/'.maintenance/changes.jsonl'
        with history.open('a',encoding='utf-8') as stream:stream.write(json.dumps(entry,ensure_ascii=False)+'\n')
        return {'changed':True,'version':version,'change_id':change_id,'needs_build':True}
    except Exception:
        if written and path is not None and original is not None:
            temporary=path.with_suffix('.restore');temporary.write_bytes(original);os.replace(temporary,path);clear_cache()
        raise
    finally:
        os.close(fd);lock.unlink(missing_ok=True)
