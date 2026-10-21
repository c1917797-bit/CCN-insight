from pathlib import Path
import json,re
from html import escape
root=Path(__file__).resolve().parents[1]; src=root/'research/ai-infra/imported'; out=root/'dist/ai-infra'
def rows(name): return [x['row'] for x in json.loads((src/(name+'.json')).read_text(encoding='utf-8'))['rows']]
topics=rows('ic_compression_topics'); cards=rows('ic_compression_topic_cards'); refs=rows('ic_compression_topic_card_refs')
sources={r['source_id'] for r in rows('compression_sources')}
for ref in refs: assert ref['source_id'] in sources, ref['source_id']
for t in topics:
    key=t['compression_topic_id']; html=(out/('topic-'+key+'.html')).read_text(encoding='utf-8')
    assert '<details' not in html
    for c in cards:
        if c['compression_topic_id']==key:
            assert escape(c['title_zh']) in html
            for line in c['body_zh'].splitlines():
                if line.strip(): assert escape(line) in html, c['card_id']
    for href in re.findall(r'href="([^"]+)"',html):
        if href.startswith('#'): assert 'id="'+href[1:]+'"' in html,href
for filename in ['compression.html','compression-foundations.html']:
    html=(out/filename).read_text(encoding='utf-8')
    for href in re.findall(r'(?:href|src)="([^"]+)"',html):
        if href.startswith(('http','/','#')): continue
        assert (out/href.split('#')[0]).exists(), href
assert sum(1 for x in topics)==16
print(f'PASS: {len(topics)} dossiers, {len(cards)} complete cards, {len(refs)} resolved citations; local lessons and navigation')
