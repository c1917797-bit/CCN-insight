"""Verify route names, portal entry targets and retained legacy topic identities."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re

ROOT = Path(__file__).resolve().parents[1]
ROUTES = dict(zip(('precision','selection','distillation','factorization'),('低比特量化','稀疏化与剪枝','知识蒸馏','低秩分解')))


def rows(table):
    return [item['row'] for line in (ROOT/'data/compression/tables'/table/'rows.jsonl').read_text(encoding='utf-8').splitlines() if line.strip() and not (item := json.loads(line)).get('deleted')]


class Entries(HTMLParser):
    def __init__(self):
        super().__init__()
        self.routes = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'data-compression-route' in attrs:
            key = attrs['data-compression-route']
            assert key not in self.routes
            self.routes[key] = attrs['href']


terms = {row['term_id']:row for row in rows('ic_map_terms')}
assert {key:terms[key]['name_zh'] for key in ROUTES} == ROUTES
assert all('无损' not in terms[key]['name_zh'] for key in ROUTES)
topics = rows('ic_compression_topics')
assert len(topics) == 16
for target in ('parameters','activations','kv_cache'):
    for method in ROUTES:
        assert any(row['compression_topic_id'] == target+'-'+method and row['route'] == 'topic.html?topic='+target+'-'+method for row in topics)
assert next(row for row in topics if row['compression_topic_id'] == 'parameters-distillation')['title_zh'] == '知识蒸馏与紧凑学生模型'
for file in ('index.html','compression.html'):
    parser = Entries()
    parser.feed((ROOT/'dist/ai-infra'/file).read_text(encoding='utf-8'))
    assert parser.routes == {key:'/business_insight/cloud_core/index.html?month=2026-10#route-'+key for key in ROUTES}, file
base = ROOT/'original-reader/site/business_insight/cloud_core'
bootstrap = (base/'reader-bootstrap.js').read_text(encoding='utf-8').strip()
for file in ('index.html','topic.html','monthly.html'):
    match = re.search(r'<script data-lri-reader-bootstrap>\s*(.*?)\s*</script>',(base/file).read_text(encoding='utf-8'),re.S)
    assert match and match[1].strip() == bootstrap, file+' stale bootstrap'
print('PASS: four shared route names and direct portal links; 16 stable topic IDs; synchronized first-paint navigation')
