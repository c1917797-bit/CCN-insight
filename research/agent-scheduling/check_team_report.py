"""Cross-page navigation, model and evidence contracts for the team report."""
from pathlib import Path
import re
from html import unescape
from decision_map import read,BASE
from literature_view import model,period_kind,CUTOFF
from team_strategy import capabilities
P=Path(__file__).parent
pages=list((P/'site'/BASE.lstrip('/')).glob('*.html'))
assert len(pages)==23
home=next(p for p in pages if p.name=='index.html').read_text(encoding='utf-8')
positions=[home.index(f'<section id="{k}"') for k in ('sources','map','updates','analysis','archive')]
assert positions==sorted(positions)
pubs,links,routes=model()
assert len(pubs)==34 and len(links)==50
week=read('weekly-selection.csv')
assert len(week)==1 and len({r['publication_id'] for r in week})==1
assert all(r['week_start'] <= pubs[r['publication_id']]['published'] <= r['week_end'] for r in week)
assert period_kind(pubs['murakkab'])=='历史补录'
assert pubs['agentix']['checked']=='2026-10-13' # Migration must not fake re-review dates.
assert '尚无云核实测结论' in home
assert '主指标：端到端任务有效吞吐' in home
assert '同一到达批次' in home and '容量拒绝' in home
assert len({c['area_id'] for c in capabilities()})==3
for c in capabilities():
    text=(P/'site'/BASE.lstrip('/')/f'research-{c["area_id"]}.html').read_text(encoding='utf-8')
    for key in ('inputs','outputs','heuristic','optimization','learning','asset','acceptance','stop','gates'):
        assert c[key] in unescape(text),(c['area_id'],key)
    assert text.index('产业界：现有实现')<text.index('学术界：新方法')
sections=read('page-sections.csv')
for path in pages:
    text=path.read_text(encoding='utf-8');title=unescape(re.search(r'<title>(.*?) ·',text)[1])
    assert text.count('<h1')==1 and text.count('data-nav-scope="primary"')==5,path.name
    if path.name!='index.html':
        rows=[r for r in sections if r['page_title']==title]
        assert rows and '本页章节' in text,path.name
        pos=[text.index(f'<section id="{r["section_id"]}"') for r in rows]
        assert pos==sorted(pos)
    assert f'架构编排 · {CUTOFF}' in text and f'动态证据截至 {CUTOFF}' in text
assert pubs['strands-box-preview']['published']=='2026-10-07'
assert period_kind(pubs['temporal-queue-fairness'])=='能力资料'
assert period_kind(pubs['ray-node-affinity'])=='能力资料'
assert period_kind(pubs['yuanrong-session-affinity'])=='历史补录'
assert len(read('evidence-batch-20261023.csv'))==6
assert {r['publication_id'] for r in read('evidence-batch-20261023.csv')}<=set(pubs)
sources={r['id'] for r in read('source-channels.csv')}
from verification_registry import records, latest
audits=records()
assert set(latest())==sources, 'Missing source verification record'
assert home.count('class="verification-record"')==len(sources)
for audit in latest().values():
    assert f'id="verification-{audit["id"]}"' in home
    assert audit['observed_fact'] in unescape(home)
    assert audit['limitations'] in unescape(home)
    assert f'data-source-access="{audit["access_status"]}"' in home
assert 'channel-verification' in home
assert '信源核验留档' in home and '已收录研究依据' in home
assert len(sources)==28 and len(read('source-profile.csv'))==len(sources)
assert all(r['channel_id'] in sources for r in read('source-checks-20261023.csv'))
assert all(r['channel_id'] in sources and r['domain_id'] in {'workflow','mapping','sharing'} for r in read('source-domain-links.csv'))
assert {r['channel_id'] for r in read('source-domain-links.csv')}==sources
candidates=read('signal-candidates.csv')
assert len({r['id'] for r in candidates})==len(candidates)
assert all(not r['published'] and not r['revised'] for r in candidates if r['channel_id']=='arxiv'), 'Feed announcements cannot establish paper dates'
assert all(set(r['publication_ids'].split('|'))<=set(pubs) and r['review_due']>r['reviewed'] for r in read('decision-watchlist.csv'))
assert 'channel-area' in home and 'channel-evidence' in home and 'source-monitor' in home
assert len(read('monthly-selection.csv'))==9
assert all(period_kind(pubs[r['publication_id']])=='本期首发' for r in read('monthly-selection.csv'))
selected=[pubs[r['publication_id']] for r in read('monthly-selection.csv')]
assert {k:sum(p['kind']==k for p in selected) for k in ('academic','industry','news')}=={'academic':4,'industry':4,'news':1}
assert len(re.findall(r'<article[^>]+data-update-current="true"', home))==9
assert all(f'id="publication-{p["id"]}"' in home for p in pubs.values()), 'Historical items must remain reachable after the month changes'
assert '<a href="#month-reading">阅读本月新增依据</a>' in home
assert {r['channel_id'] for r in audits if r['reviewed']=='2026-11-24'}=={'arxiv','llmd','ascend','buoyant'}
assert 'id="november-insight"' in home and 'id="october-judgments"' in home
historical=read('history/2026-10/research-publications.csv')
assert len(historical)==25
assert all(all(pubs[r['id']][k]==v for k,v in r.items()) for r in historical), 'Do not relabel or rewrite prior evidence during a monthly refresh'
print(f'PASS: 23 page structures; 3 complete research contracts; {len(pubs)} evidence records; {len(links)} links; {len(week)} verified weekly selection; 9 November facts; preserved October evidence and judgment snapshot.')
