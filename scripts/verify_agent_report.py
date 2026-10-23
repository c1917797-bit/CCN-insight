"""Check content relations and actual built internal navigation, without network access."""
from pathlib import Path
import csv
import hashlib
import json
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'research/agent-scheduling'
sys.path.insert(0,str(SOURCE))
from export_isolated_preview import Page, BASE, IMAGE_EXTENSIONS
from deep_readings import PAGE_FILE as DEEP_PAGE, ASSET_FILES, page_sections as deep_sections
from urllib.parse import urljoin, urlsplit, unquote

def read(name):
    with (SOURCE/name).open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))
pubs={r['id'] for r in read('research-publications.csv')}
links=read('architecture-evidence-links.csv')
assert len(links)==len(pubs) and {r['publication_id'] for r in links}==pubs
assert {r['area_id'] for r in read('architecture-decisions.csv')}=={'workflow','mapping','sharing'}
folder=ROOT/'dist'/BASE
pages={p.name:Page(p.read_text(encoding='utf-8')) for p in folder.glob('*.html')}
assert len(pages)==23, ('Expected 22 existing pages and one evidence deep reading',len(pages))
assert DEEP_PAGE in pages, ('Missing primary-source deep reading',DEEP_PAGE)
preview=SOURCE/'outputs/isolated-preview'
validation=json.loads((SOURCE/'outputs/isolated-preview-validation.json').read_text(encoding='utf-8'))
assert validation['research_pages']==len(pages)
allowlist=validation['allowlist']
image_files=validation['evidence_images']
expected_images={BASE+name for name in ASSET_FILES}
assert expected_images==set(image_files), ('Evidence image allowlist differs from declared readings',expected_images ^ set(image_files))
asset_sources={BASE+row['asset']:row for row in read('deep-reading-murakkab-assets.csv')}
assert set(asset_sources)==expected_images
deep_page=pages[DEEP_PAGE]
assert len(deep_page.images)==3 and {img['src'].lstrip('/') for img in deep_page.images}==expected_images
assert all(img['alt'].strip() for img in deep_page.images), 'Original figures need descriptive alt text'
assert all(deep_page.links.count('/'+name)>=2 for name in expected_images), 'Each figure must link to its full-size original'
assert {row['section_id'] for row in deep_sections()}.issubset(deep_page.ids)
for name,digest in allowlist.items():
    source_file=preview/name
    assert source_file.resolve().is_relative_to(preview.resolve()),name
    assert source_file.is_file() and hashlib.sha256(source_file.read_bytes()).hexdigest()==digest,name
    if not name.startswith(BASE):continue
    published=ROOT/'dist'/name
    assert published.resolve().is_relative_to(folder.resolve()),name
    assert published.is_file() and hashlib.sha256(published.read_bytes()).hexdigest()==digest,('Published bytes differ',name)
    assert not name.lower().endswith('.pdf'),('Paper PDF must not be published',name)
for name,metadata in image_files.items():
    assert name.startswith(BASE+'assets/evidence/') and Path(name).suffix.lower() in IMAGE_EXTENSIONS,name
    original=SOURCE/name.removeprefix(BASE)
    assert original.resolve().is_relative_to((SOURCE/'assets/evidence').resolve()),name
    assert len(original.read_bytes())==metadata['bytes'] and hashlib.sha256(original.read_bytes()).hexdigest()==metadata['sha256'],name
    assert allowlist[name]==metadata['sha256'],name
    if name in asset_sources:
        record=asset_sources[name]
        assert metadata['sha256']==record['sha256'], ('Image differs from primary-source crop record',name)
        assert record['source_url'].startswith('https://') and re.fullmatch(r'[0-9a-f]{64}',record['pdf_sha256'])
        width,height=struct.unpack('>II',original.read_bytes()[16:24])
        assert (width,height)==(int(record['width']),int(record['height'])), ('Image dimensions differ from crop record',name)
for area in ('workflow','mapping','sharing'):
    text=(folder/f'research-{area}.html').read_text(encoding='utf-8')
    assert f'id="mechanism-{area}"' in text,('Missing concrete root mechanism',area)
    diagram=re.search(r'<svg class="mechanism-svg".*?</svg>',text,re.S)
    assert diagram and 'role="img"' in diagram[0] and '<title ' in diagram[0] and '<desc ' in diagram[0],area
    ET.fromstring(diagram[0])
    assert '构造实例，不是性能实验' in text and '这个例子何时不成立' in text,area
home=(folder/'index.html').read_text(encoding='utf-8')
source_chapter=home[home.index('<section id="sources"'):home.index('<section id="map"')]
assert len(re.findall(r'<table\b',source_chapter))==3, 'Source directory must have exactly three category tables'
assert source_chapter.count('class="source-table-row"')==len(read('source-channels.csv'))
contracts=read('decision-research-contracts.csv')
assert {r['decision_id'] for r in contracts}=={'admission','ordering','dispatch','allocation'} and len(contracts)==4
methods=read('decision-methods.csv')
assert all(sum(m['decision_id']==r['decision_id'] for m in methods)==3 for r in contracts)
for row in contracts:
    decision_text=(folder/f'decision-{row["decision_id"]}.html').read_text(encoding='utf-8')
    assert row['baseline'] in decision_text and row['retreat'] in decision_text
count=0
for name,page in pages.items():
    for link in page.links:
        u=urlsplit(urljoin('https://example.invalid/'+BASE+name,link))
        if u.netloc!='example.invalid': continue
        relative=unquote(u.path).lstrip('/')
        target=ROOT/'dist'/relative
        if u.path.endswith('/'):target=target/'index.html'
        assert target.resolve().is_relative_to(folder.resolve()),(name,link)
        assert target.is_file() and target.relative_to(ROOT/'dist').as_posix() in allowlist,(name,link)
        if u.fragment and target.suffix=='.html':assert unquote(u.fragment) in pages[target.name].ids,(name,link)
        count+=1
    text=(folder/name).read_text(encoding='utf-8')
    assert not re.search(r'127\.0\.0\.1|C:[/\\]|PRIVATE KEY|Authorization\s*:|basic_verify\s*[:=]|password\s*[:=]',text,re.I),name
subprocess.run([sys.executable,'-X','utf8',str(SOURCE/'check_team_report.py')],check=True)
print(f'PASS: {len(pages)} pages; {count} internal links; {len(image_files)} original evidence images with source/preview/dist SHA-256 parity; 3 concrete mechanism SVGs; {len(links)} evidence-to-decision links; no local paths or credential assignments.')
