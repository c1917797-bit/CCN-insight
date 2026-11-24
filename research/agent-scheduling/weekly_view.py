"""Dated selection with coverage limits, linked to canonical evidence."""
from html import escape as e
from decision_map import read

def weekly_digest():
    pubs={r['id']:r for r in read('research-publications.csv')}
    findings={r['publication_id']:r for r in read('research-findings.csv')}
    rows=read('weekly-selection.csv')
    cards=''.join(f'''<a class="week-card" href="#publication-{r['publication_id']}"><span>{e(r['category'])} · {pubs[r['publication_id']]['published']}</span><h4>{e(findings[r['publication_id']]['headline'])}</h4><p>{e(findings[r['publication_id']]['insight'])}</p><small>{e(pubs[r['publication_id']]['status'])}</small><b>查看机制、结果与研究问题</b></a>''' for r in rows)
    start,end=min(r['week_start'] for r in rows),max(r['week_end'] for r in rows)
    return f'''<details id="updates-week" class="weekly-digest"><summary>近七日精选 · {start}—{end} · {len(rows)}项</summary><p>该窗口是整月精选的子集。本轮仅纳入已核对的条目，不代表近七日只有这些进展；不将17日首发论文挪入18—24日窗口。</p><div class="week-grid">{cards}</div></details>'''
