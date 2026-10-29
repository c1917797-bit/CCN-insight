"""Preserve local acquisition and actual review notes outside temporary storage.

Copies public source packages and model notes; does not publish or update topics.
Run after building the local reading desk, and repeat after further model reading.
"""
from pathlib import Path
import argparse,datetime as dt,hashlib,json

def snapshot(acquired,reviewed,coverage,out):
    sources={'arxiv':Path(acquired),'model-notes':Path(reviewed),'registered-sources':Path(coverage)}
    target=Path(out).resolve()/'original-records'
    records=[]
    for kind,folder in sources.items():
        assert folder.is_dir(),folder
        dest=target/kind;dest.mkdir(parents=True,exist_ok=True)
        files=sorted(folder.glob('*'))
        if kind=='model-notes':files=[p for p in files if p.name.endswith('-reviews.jsonl') or p.name in ['section-reviews.json','industry-reviews.json','curation-decisions.json','canonical-adoption-receipt.json','prepared-content-patch.json'] or p.suffix=='.md']
        for file in files:
            if not file.is_file():continue
            blob=file.read_bytes()
            (dest/file.name).write_bytes(blob)
            records.append({'path':str((dest/file.name).relative_to(target)).replace('\\','/'),'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
    receipt={'schema':'ccn.local-reading-snapshot.v1','created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'published':False,'files':records}
    target.mkdir(parents=True,exist_ok=True)
    (target/'manifest.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'files':len(records),'bytes':sum(r['bytes'] for r in records),'target':str(target)},ensure_ascii=False))
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['acquired','reviewed','coverage','out']:p.add_argument('--'+name,required=True)
    a=p.parse_args();snapshot(a.acquired,a.reviewed,a.coverage,a.out)
