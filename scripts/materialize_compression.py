"""Generate legacy adapters; canonical content is data/compression only."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT, manifest, records, content_version

def build():
    meta = manifest()
    version = content_version()
    imported = ROOT / 'research/ai-infra/imported'
    names = [p.stem for p in imported.glob('*.json')]
    directory = ROOT / 'data/directory'
    targets = {p.stem:p for p in directory.glob('*.json')}
    for name in names:
        targets[name] = imported / (name+'.json')
    by_name = {t['name']:t for t in meta['tables']}
    for name, destination in targets.items():
        table_name = 'cloud_core_sources' if name=='compression_sources' else name
        if table_name not in by_name:
            continue
        table = by_name[table_name]
        definition = json.loads((ROOT/'data/compression/tables'/table_name/'definition.json').read_text(encoding='utf-8'))
        current = records(table_name)
        pack = {'revision':version,'import_revision':meta['revision'],'definition':definition,'row_count':len(current),'truncated':False,'rows':current,'generated_from':table['rows_file']}
        destination.write_text(json.dumps(pack,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    for filename, name in [('compression-topics.json','ic_compression_topics'),('compression-sections.json','ic_compression_topic_sections')]:
        source = imported/(name+'.json')
        (ROOT/'research/ai-infra'/filename).write_bytes(source.read_bytes())
    print('Generated compatibility views from canonical compression content')

if __name__=='__main__':
    build()
