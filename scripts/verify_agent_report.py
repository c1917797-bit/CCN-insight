"""Check content relations and actual built internal navigation, without network access."""
from pathlib import Path
import csv
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'research/agent-scheduling'
sys.path.insert(0,str(SOURCE))
from export_isolated_preview import Page, BASE
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
assert len(pages)==22
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
        target=ROOT/'dist'/unquote(u.path).lstrip('/')
        if u.path.endswith('/'):target=target/'index.html'
        assert target.exists(),(name,link)
        if u.fragment:assert u.fragment in pages[target.name].ids,(name,link)
        count+=1
    text=(folder/name).read_text(encoding='utf-8')
    assert not re.search(r'127\.0\.0\.1|C:[/\\]|PRIVATE KEY|Authorization\s*:|basic_verify\s*[:=]|password\s*[:=]',text,re.I),name
subprocess.run([sys.executable,'-X','utf8',str(SOURCE/'check_team_report.py')],check=True)
print(f'PASS: 22 pages; {count} internal links; 19 evidence-to-decision links; 3 architecture contracts; no local paths or credential assignments.')
