"""Rebuild delivery bundles and synchronize inline startup and cache hashes."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'original-reader/site/business_insight/cloud_core'

def sync():
    # The HTML loads reader-entry.js, not the individual source modules. Rebuild
    # that delivery path as part of every site build, without copy rewrites.
    from refine_reader_copy import rebuild
    rebuild()
    source=BASE/'reader-bootstrap.js';bootstrap=source.read_text(encoding='utf-8').strip()
    normalized=(bootstrap+'\n').encode('utf-8')
    if source.read_bytes()!=normalized:source.write_bytes(normalized)
    changed=[]
    for name in ['index.html','topic.html','monthly.html']:
        path=BASE/name;text=path.read_text(encoding='utf-8')
        result,count=re.subn(r'<script data-lri-reader-bootstrap>[\s\S]*?</script>',lambda _:'<script data-lri-reader-bootstrap>\n'+bootstrap+'\n</script>',text)
        assert count==1,('Startup marker missing or duplicated',name)
        blob=result.encode('utf-8')
        if path.read_bytes()!=blob:path.write_bytes(blob);changed.append(name)
    print('Synchronized startup source: '+str(len(changed))+' HTML copies')

if __name__=='__main__':sync()
