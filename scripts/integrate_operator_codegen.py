"""Merge reviewed operator-generation evidence into the shared source registry."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
research=root/'research/ai-infra'
path=research/'operator-sources.json'
registry=json.loads(path.read_text(encoding='utf8'))
index={row['id']:i for i,row in enumerate(registry['sources'])}
for name in ['operator-codegen-insight.json','operator-codegen-hardware.json','operator-codegen-named-a.json','operator-codegen-named-b.json']:
    packet=json.loads((research/name).read_text(encoding='utf8'))
    for row in packet.get('source_additions',[])+packet.get('source_review_updates',[]):
        if row['id'] in index:
            assert registry['sources'][index[row['id']]]['url']==row['url'],row['id']
            registry['sources'][index[row['id']]]=row
        else:
            index[row['id']]=len(registry['sources'])
            registry['sources'].append(row)
registry['reviewed_at']='2026-10-23'
path.write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Generation evidence merged:',len(index),'source records; citation order preserved')
