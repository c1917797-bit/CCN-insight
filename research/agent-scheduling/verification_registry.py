"""Auditable source checks, separate from publication and decision evidence."""
from datetime import date
from functools import lru_cache
from html import escape as e
from urllib.parse import urlsplit
from decision_map import read
from report_contract import CUTOFF

ACCESS = {'readable': '可读', 'partial': '部分可读', 'blocked': '读取受阻'}
LEVEL = {'entry': '入口核对', 'list': '条目抽样', 'mechanism': '机制核对'}
FIELDS = ('id', 'channel_id', 'reviewed', 'entry_url', 'evidence_url', 'check_scope',
          'access_status', 'verification_level', 'observed_fact', 'scheduling_relevance',
          'limitations', 'next_action', 'next_review', 'publication_ids')

@lru_cache(maxsize=1)
def records():
    rows = read('source-verifications.csv')
    channels = {r['id'] for r in read('source-channels.csv')}
    pubs = {r['id'] for r in read('research-publications.csv')}
    assert rows and set(rows[0]) == set(FIELDS), 'Verification schema mismatch'
    assert len({r['id'] for r in rows}) == len(rows), 'Duplicate verification ID'
    for r in rows:
        assert all(r[k].strip() for k in FIELDS if k != 'publication_ids'), r['id']
        assert r['channel_id'] in channels, r['id']
        assert r['access_status'] in ACCESS and r['verification_level'] in LEVEL, r['id']
        assert date.fromisoformat(r['reviewed']) <= date.fromisoformat(CUTOFF), r['id']
        assert date.fromisoformat(r['next_review']) > date.fromisoformat(r['reviewed']), r['id']
        for key in ('entry_url', 'evidence_url'):
            u = urlsplit(r[key])
            assert u.scheme == 'https' and u.netloc and not u.username and not u.password, r['id']
        if r['publication_ids']:
            assert set(r['publication_ids'].split('|')) <= pubs, r['id']
    assert {r['channel_id'] for r in rows} == channels, 'Every registered source needs a verification record'
    return rows

def latest():
    # Stable sorting keeps appended same-day corrections as the latest record.
    return {r['channel_id']: r for r in sorted(records(), key=lambda r: r['reviewed'])}

def verification_cell(channel_id):
    r = latest()[channel_id]
    badge = f'<span class="verification-badge" data-access="{r["access_status"]}">{ACCESS[r["access_status"]]} · {LEVEL[r["verification_level"]]}</span>'
    summary = f'<div class="verification-preview">{badge}<small>核验 {r["reviewed"]}</small><p>{e(r["observed_fact"])}</p></div>'
    fields = [('核对范围', r['check_scope']), ('调度关联', r['scheduling_relevance']),
              ('尚未证明', r['limitations']), ('下一步核验', r['next_action'])]
    details = ''.join(f'<div><dt>{k}</dt><dd>{e(v)}</dd></div>' for k, v in fields)
    record = f'''<details class="verification-record" id="verification-{r['id']}"><summary>核对范围、研究价值与证据边界</summary>
<p class="verification-record-id">记录编号：{e(r['id'])} · <a href="#verification-{r['id']}">记录直达链接</a></p>
<p><a href="{e(r['entry_url'])}" target="_blank" rel="noopener noreferrer">检查的入口 ↗</a> · <a href="{e(r['evidence_url'])}" target="_blank" rel="noopener noreferrer">本次核对原文 ↗</a></p>
<dl>{details}</dl><p class="verification-deadline">建议复核：<time datetime="{r['next_review']}">{r['next_review']}</time>，出现版本／目录变化时提前。此日期是维护建议，未设置自动提醒。</p></details>'''
    return r, summary, record

def review_worklist(channels):
    rows = list(latest().values())
    problems = [r for r in rows if r['access_status'] != 'readable']
    due = sorted(rows, key=lambda r: (r['next_review'], r['channel_id']))
    chosen = problems + [r for r in due if r not in problems][:max(0, 3-len(problems))]
    cards = ''.join(f'''<li><a href="#verification-{r['id']}">{e(channels[r['channel_id']]['title'])} →</a><span>{ACCESS[r['access_status']]} · 建议 {r['next_review']} 复核</span><p>{e(r['next_action'])}</p></li>''' for r in chosen)
    counts = ' · '.join(f'{ACCESS[k]} {sum(r["access_status"] == k for r in rows)}' for k in ACCESS)
    return f'''<details class="verification-worklist"><summary>复核工作单 · {len(problems)} 个入口需跟进</summary><p>{counts}。每个来源有记录，但目录核验不等于全部文章已审阅。优先显示读取障碍，再显示最近建议复核项。</p><ul>{cards}</ul><p>新增或修改来源时必须补齐核验记录；已通过核验的历史记录保留，不覆盖失败尝试。具体论文／版本沿用独立的证据审阅记录，研究取舍另有决策复核条件。</p></details>'''
