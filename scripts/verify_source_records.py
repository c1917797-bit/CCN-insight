"""Check that removing reader cards never loses provenance or reference entrypoints."""
from html.parser import HTMLParser
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT,rows


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__();self.ids=set();self.links=set();self.text=[];self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if 'id' in attrs:
            assert attrs['id'] not in self.ids,'Duplicate record anchor'
            self.ids.add(attrs['id'])
        if tag=='a':self.links.add(attrs.get('href',''))
    def handle_data(self, data):self.text.append(data)


page=Page((ROOT/'dist/business_insight/cloud_core/source-records.html').read_text(encoding='utf-8'))
text=''.join(page.text)
reviewed=[r for r in rows('ic_source_families') if r.get('reviewed_at') and r.get('review_note_zh')]
for family in reviewed:
    assert 'source-review-'+family['family_id'] in page.ids
    for field in ['review_note_zh','review_note_en']:
        assert not family.get(field) or family[field] in text,'Lost review text'
    assert not family.get('review_url') or family['review_url'] in page.links,'Lost review source'
channels={r['channel_id']:r for r in rows('ic_channels')}
sources={r['source_id']:r for r in rows('cloud_core_sources')}
papers=[r for r in rows('ic_channel_families') if r['entry_kind']=='paper_reference']
for member in papers:
    assert 'source-paper-entries-'+member['family_id'] in page.ids
    assert sources[channels[member['channel_id']]['source_id']]['canonical_url'] in page.links,'Lost paper URL'
source=(ROOT/'original-reader/site/business_insight/cloud_core/compression.js').read_text(encoding='utf-8')
render=source[source.index('function renderChannels(){'):source.index('function categoryPath(')]
assert 'source-register-notes' not in render and 'reviewNotes' not in render,'Inline review cards still rendered'
assert 'sourceRecordHref' in render and 'location.replace(sourceRecordHref(id))' in source
assert 'index.html#view-sources' in page.links
print('PASS:',len(reviewed),'review records and',len(papers),'paper links preserved; separate record anchors and reader return')
