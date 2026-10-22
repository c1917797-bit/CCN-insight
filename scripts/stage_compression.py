"""Stage two sites from exactly one checked content version. Does not deploy."""
from pathlib import Path
from html import escape
import hashlib
import json
import shutil
import subprocess
import sys
import os
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT, manifest, content_version

def run(script):
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts'/script)],cwd=ROOT,check=True)

def stage_unlocked():
    before=content_version()
    run('verify_tablegit_migration.py')
    run('build.py')
    run('verify_compression.py')
    run('verify_migration_preview.py')
    run('verify_original_reader.py')
    if content_version()!=before:raise RuntimeError('Content changed during build; no release is accepted.')
    version=before
    source=ROOT/'dist'
    staging=ROOT/'local-releases'/version/'original-reader'
    target_roots={'ccn':staging/'ccn','lrigit':staging/'lrigit'}
    shared={}
    paths=[p for folder in [source/'assets',source/'business_insight/cloud_core'] for p in folder.rglob('*') if p.is_file()]
    for path in paths:
        relative=path.relative_to(source)
        data=path.read_bytes()
        shared[relative.as_posix()]=hashlib.sha256(data).hexdigest()
        for root in target_roots.values():
            destination=root/relative;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
    for target,root in target_roots.items():
        marker={'content_version':version,'import_revision':manifest()['revision'],'target':target,'status':'staged_not_published','entrypoint':'business_insight/cloud_core/index.html#view-topics','renderer':'original-reader','shared_files':shared}
        (root/'compression-version.json').write_text(json.dumps(marker,ensure_ascii=False,indent=2),encoding='utf-8')
    for relative,sha in shared.items():
        assert all(hashlib.sha256((r/relative).read_bytes()).hexdigest()==sha for r in target_roots.values()),relative
    if content_version()!=before:raise RuntimeError('Content changed while staging; no release is accepted.')
    receipt={'content_version':version,'status':'staged_not_published','renderer':'original-reader','entrypoint':'business_insight/cloud_core/index.html#view-topics','shared_file_count':len(shared),'targets':{name:path.relative_to(ROOT).as_posix() for name,path in target_roots.items()},'online_sites_changed':False}
    (ROOT/'data/compression/staged-release.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    (staging/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))
    return receipt

def stage():
    lock=ROOT/'data/compression/.edit.lock'
    fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(fd,str(os.getpid()).encode())
        return stage_unlocked()
    finally:
        os.close(fd);lock.unlink(missing_ok=True)

if __name__=='__main__':stage()
