"""Cross-page navigation, model and evidence contracts for the team report."""
from pathlib import Path
import re
from html import unescape
from decision_map import read,BASE
from literature_view import model,period_kind,CUTOFF
from team_strategy import capabilities
P=Path(__file__).parent
pages=list((P/'site'/BASE.lstrip('/')).glob('*.html'))
assert len(pages)==22
home=next(p for p in pages if p.name=='index.html').read_text(encoding='utf-8')
positions=[home.index(f'<section id="{k}"') for k in ('sources','map','updates','analysis','archive')]
assert positions==sorted(positions)
pubs,links,routes=model()
assert len(pubs)==19 and len(links)==35
week=read('weekly-selection.csv')
assert len(week)==4 and len({r['publication_id'] for r in week})==4
assert all('2026-10-17' <= pubs[r['publication_id']]['published'] <= '2026-10-23' for r in week)
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
    assert '架构编排 · 2026-10-23' in text and '动态证据截至 2026-10-23' in text
print('PASS: 22 page structures; 3 complete research contracts; 19 evidence records; 35 links; 4 verified weekly selections; period and metric boundaries.')
