# -*- coding: utf-8 -*-
"""Apply reviewed, bounded content patches without changing identities or citations."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/compression/tables'
files=['activations-topic-copy-20261023.json','kv-topic-copy-20261023.json','parameters-topic-copy-20261023.json']
patches=[]
for name in files:
 p=ROOT/'.tmp'/name
 if not p.exists():raise FileNotFoundError('Editorial patch not ready: '+name)
 patches.extend(json.loads(p.read_text(encoding='utf-8')))
allowed={'title_zh','title_en','heading_zh','heading_en','body_zh','body_en','why_zh','why_en','value_zh','value_en','challenge_zh','challenge_en','summary_zh','summary_en'}
tables={};seen=set();changed=0;topics=set()
for item in patches:
 t=item['table'];key=item['key'];patch=item['patch']
 assert t in ['ic_compression_topic_cards','ic_compression_topic_sections','ic_compression_research_frames','ic_compression_topic_concepts'],t
 assert set(patch)<=allowed,(t,key,set(patch)-allowed)
 assert (t,key) not in seen,(t,key);seen.add((t,key))
 if t not in tables:tables[t]=[json.loads(x) for x in (BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()]
 entry=next(x for x in tables[t] if x['key']==key and not x['deleted']);row=entry['row'];assert row.get('compression_topic_id')!='parameters-precision'
 assert set(patch)<=set(row),(t,key,'unknown content field')
 topics.add(row['compression_topic_id'])
 if any(row.get(k)!=v for k,v in patch.items()):row.update(patch);entry['row_version']+=1;changed+=1
for t,data in tables.items():(BASE/t/'rows.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in data),encoding='utf-8')
print('Editorial topics:',len(topics),'Changed records:',changed,'Identities and references unchanged')
