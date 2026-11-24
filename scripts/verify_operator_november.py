# -*- coding: utf-8 -*-
"""Validate the November event feed, cross-links, and rendered scope."""
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FEED = ROOT / 'research/ai-infra/operator-monthly-202611.json'
OUT = ROOT / 'dist/ai-infra'

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.tags = set(), [], []
        self.feed(path.read_text(encoding='utf-8'))
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        self.tags.append(tag)
        if 'id' in data:
            assert data['id'] not in self.ids, (self, data['id'])
            self.ids.add(data['id'])
        if tag == 'a': self.links.append(data.get('href',''))

def verify():
    data = json.loads(FEED.read_text(encoding='utf-8'))
    assert data['month'] == '2026-11' and data['reviewed_at'] == '2026-11-24'
    assert '定向' in data['scope'] and '全量' in data['scope']
    rows = data['events']
    assert len(rows) >= 12 and len({r['id'] for r in rows}) == len(rows)
    assert {'学术论文','产业版本','产业工程报告'} <= {r['kind'] for r in rows}
    page = Page(OUT / 'operators.html')
    assert {'view-updates','november-events','october-events','event-mooncake-v5'} <= page.ids
    assert 'details' not in page.tags
    for row in rows:
        assert row['date'].startswith('2026-11') and date.fromisoformat(row['date']) <= date.fromisoformat(data['reviewed_at'])
        assert row['priority'] in {'重点研读','跟踪'}
        for key in ['title','date_basis','platform','challenge','route','mechanism','result','insight','boundary','locator']:
            assert isinstance(row.get(key),str) and row[key].strip(), (row['id'],key)
        assert urlsplit(row['source']).scheme == 'https' and urlsplit(row['source']).netloc
        assert 'nov-event-' + row['id'] in page.ids
        assert row['source'] in page.links
        topic, _, anchor = row['topic'].partition('#')
        assert (OUT / topic).is_file(), row['topic']
        assert row['topic'] in page.links
        if anchor: assert anchor in Page(OUT / topic).ids, row['topic']
        if row.get('date_source'): assert urlsplit(row['date_source']).scheme == 'https'
    assert len(data['experiments']) >= 4
    for x in data['experiments']:
        assert all(x.get(k,'').strip() for k in ['title','compare','reason','success'])
    print('PASS: November feed: '+str(len(rows))+' dated events; original sources, technical-topic links, historic event and reader scope intact')

if __name__ == '__main__': verify()
