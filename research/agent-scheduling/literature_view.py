"""Render one normalized literature collection into updates, topics and recommendations."""
from html import escape as e
from datetime import date
from decision_map import read, BASE
from source_registry import directory, origin
from report_contract import CUTOFF, START
from research_gates import gate_fields
from team_strategy import evidence_index, portfolio
from architect_view import evidence_lens, updates_lens, decision_review
from weekly_view import weekly_digest, weekly_decisions


def period_kind(p):
    # A revised older paper is not a newly published paper. Partial dates stay partial.
    if any(p[k] and p[k] > CUTOFF for k in ('published','revised')):
        raise ValueError('Publication date exceeds report cutoff')
    if any(p[k] == START[:7] for k in ('published','revised')):
        return '日期待核'
    if p['published'] and START <= p['published'] <= CUTOFF:
        return '本期首发'
    if p['revised'] and START <= p['revised'] <= CUTOFF:
        return '本期修订'
    return '历史补录' if p['published'] or p['revised'] else '能力资料'


def review_note(key):
    r=next(r for r in read('evidence-reviews.csv') if r['publication_id']==key)
    r={k:v.rstrip('。') for k,v in r.items()}
    return f'<p class="review-note"><strong>本轮复核范围：</strong>{e(r["scope"])}。{e(r["finding"])}。<br><strong>复核限制：</strong>{e(r["limit"])}。</p>'


def model():
    pubs=read('research-publications.csv')
    facts=read('research-findings.csv')
    links=read('research-publication-links.csv')
    byid={r['id']:dict(r) for r in pubs}
    assert len(byid)==len(pubs) and len({f['publication_id'] for f in facts})==len(pubs)
    routes={r['id']:r for r in read('research-routes.csv')}
    for f in facts:
        assert f['publication_id'] in byid
        byid[f['publication_id']].update(f)
    for p in byid.values():
        assert p['url'].startswith('https://') and p['full_url'].startswith('https://')
        assert all(p[k] for k in ('summary','challenge','mechanism','result','boundary','insight','coffee','experiment','checked_sections'))
        for field in ('published','revised','checked'):
            if p[field]:
                assert p[field]<=CUTOFF,(p['id'],field)
                date.fromisoformat(p[field]+'-01' if len(p[field])==7 else p[field])
    for l in links:
        assert l['publication_id'] in byid and l['route_id'] in routes
        assert routes[l['route_id']]['area_id']==l['area_id']
        assert l['relevance'].strip()
    assert {l['publication_id'] for l in links}==set(byid)
    assert len({(l['publication_id'],l['area_id'],l['route_id']) for l in links})==len(links)
    return byid,links,routes


def external(url,label):
    return f'<a class="source-link" href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a>'


def date_label(p):
    dates=f'首发 {p["published"]}' if p['published'] else '发布日期未标注'
    if p['revised']: dates+=f' · 修订 {p["revised"]}'
    return f'{dates} · {p["version"]} · {p["status"]}'


def associations(key):
    _,links,routes=model()
    names={r['id']:r['title'] for r in read('research-areas.csv')}
    return '<div class="literature-tags">'+''.join(
        f'<a href="{BASE}research-{l["area_id"]}.html#route-{l["route_id"]}">{e(names[l["area_id"]])} · {e(routes[l["route_id"]]["title"])} / {e(l["role"])}</a>'
        for l in links if l['publication_id']==key)+'</div>'


def entry(p):
    area_ids=' '.join(dict.fromkeys(l['area_id'] for l in model()[1] if l['publication_id']==p['id']))
    facts=''.join(f'<dt>{label}</dt><dd>{e(p[field])}</dd>' for field,label in (
        ('challenge','背景与挑战'),('mechanism','技术与路线'),('result','效果与条件'),('boundary','证据边界')))
    judgment=''.join(f'<dt>{label}</dt><dd>{e(p[field])}</dd>' for field,label in (
        ('insight','云核启示'),('coffee','咖啡类比'),('experiment','建议验证')))
    return f'''<article class="literature-entry" id="publication-{p['id']}" data-update-areas="{area_ids}" data-update-current="{str(period_kind(p) in ('本期首发','本期修订')).lower()}">
<p class="literature-meta"><span class="evidence-tag">{period_kind(p)}</span> {e(date_label(p))}</p><h4>{e(p['headline'])}</h4>
<p class="literature-original">{external(p['url'],p['title'])}</p>
<p class="publication-origin">{origin(p['id'])}</p>
{associations(p['id'])}<p class="literature-summary"><strong>一句话总结：</strong>{e(p['summary'])}</p>
{evidence_lens(p["id"])}<details class="literature-details"><summary>阅读技术、效果与研究启示</summary><h5>原始证据</h5><dl>{facts}</dl>{relevance(p['id'])}
<p class="literature-check">核对：{e(p['checked'])} · {e(p['checked_sections'])} · {external(p['full_url'],'查看原文依据')}</p>
{review_note(p['id'])}
<h5>研究判断 · 本页分析，尚待验证</h5><dl>{judgment}</dl></details></article>'''


def updates():
    pubs,_,_=model()
    academic=[p for p in pubs.values() if p['kind']=='academic']
    industry=[p for p in pubs.values() if p['kind']=='industry']
    sort=lambda rows:sorted(rows,key=lambda p:p['revised'] or p['published'],reverse=True)
    current=[p for p in pubs.values() if period_kind(p) in ('本期首发','本期修订')]
    earlier=[p for p in academic if period_kind(p)=='历史补录']
    dated_industry=[p for p in industry if period_kind(p)=='历史补录']
    capabilities=[p for p in industry if period_kind(p)=='能力资料']
    groups=[('updates-new','本期发表与修订',current),('updates-recent','历史补录 · 学术论文',earlier),
            ('updates-industry','历史补录 · 产业进展',dated_industry),
            ('updates-ascend','能力资料 · 昇腾生态',[p for p in capabilities if p['ecosystem']=='昇腾生态']),
            ('updates-capabilities','能力资料 · 开源推理生态',[p for p in capabilities if p['ecosystem']!='昇腾生态'])]
    pending=[p for p in pubs.values() if period_kind(p)=='日期待核']
    if pending: groups.append(('updates-date-pending','日期待核 · 不计入本期事件',pending))
    tabs='<nav class="literature-jumps" aria-label="本期研究阅读">'+''.join(f'<a href="#{k}">{label} · {len(rows)}</a>' for k,label,rows in groups)+'</nav>'
    body=''
    for k,label,rows in groups:
        content=''.join(entry(p) for p in sort(rows)) or '<p class="note">本次筛选尚未收录符合此时间口径的资料，不代表该领域没有进展。</p>'
        if k=='updates-new':
            body+=f'<div id="{k}" class="literature-group" data-update-group><h3>{label}</h3><p data-update-group-empty hidden>所选方向本期尚未收录条目，可查看下方历史资料；这不代表该方向没有进展。</p>{content}</div>'
        else:
            body+=f'<details id="{k}" class="literature-group history-group" data-update-group><summary><span>{label}</span><small data-update-count>{len(rows)} 项 · 展开阅读</small></summary><p class="history-reminder">以下为既有证据和实现背景，不计入本期新增。</p>{content}</details>'
    filters='<div class="update-filter"><label for="update-area">只看我的研究方向</label><select id="update-area"><option value="">全部方向</option>'+''.join(f'<option value="{a["id"]}">{e(a["title"])}</option>' for a in read('research-areas.csv'))+f'</select><button type="button" id="update-reset">显示全部</button><p id="update-filter-status" role="status">本期 {len(current)} 项 · 累计 {len(pubs)} 项（含历史和能力资料）</p></div>'
    return f'''<section id="updates"><p class="eyebrow">03 / 本期动态</p><h2>本月有什么变化，影响哪条调度路线</h2>
<p>观察期 <strong>{START}—{CUTOFF}</strong>。当前证据集有{len(academic)}篇论文、{len(industry)}项官方资料；先读期内发表或修订，再查历史补录和能力文档。核对日期不等于发布日期。</p>
{weekly_digest()}{updates_lens()}<div class="period-summary"><div><strong>{len(current)} 项</strong><span>期内首发或修订</span></div><div><strong>{len(earlier)+len(dated_industry)} 项</strong><span>历史资料补录</span></div><div><strong>{len(capabilities)} 项</strong><span>无发布日期的能力资料</span></div></div>
<p class="note">这是本次人工筛选的相关资料，非全量覆盖或自动订阅。热点资讯已登记持续入口，本轮尚未收录核验后的新闻事件；已发布版本与无日期的能力资料分开展示。论文报告、工程说明和本页判断分开展示；本地尚无实测收益。</p>{filters}{tabs}
<details class="scope-index"><summary>读前小词典：KV、prefill、decode、TTFT、JCT</summary><p>KV缓存保存模型先前计算的上下文；prefill是处理输入，decode是逐步生成输出；TTFT是首个token的等待时间，JCT是整项任务从到达到完成的时间。本页最终看任务完成，不把首token变快等同于整单变快。</p></details>{body}{evidence_index()}</section>'''


def topic_recent(area_id):
    pubs,links,_=model()
    ids=list(dict.fromkeys(l['publication_id'] for l in links if l['area_id']==area_id))
    blocks=[]
    for kind,title in [('industry','产业界：现有实现与适用边界'),('academic','学术界：新方法与实验依据')]:
        selected=sorted((pubs[k] for k in ids if pubs[k]['kind']==kind),key=lambda p:p['revised'] or p['published'],reverse=True)
        cards=''.join(f'''<article class="recent-paper" id="recent-{p['id']}"><p class="literature-meta">{e(p['short'])} · {e(date_label(p))}</p><h4>{e(p['headline'])}</h4><p>{e(p['summary'])}</p>{relevance(p['id'],area_id)}<p class="recent-boundary"><strong>适用边界：</strong>{e(p['boundary'])}</p><a class="source-link" href="{BASE}#publication-{p['id']}">阅读原始事实、技术路线与研究启示 →</a></article>''' for p in selected)
        blocks.append(f'<div class="recent-group"><h3>{title}</h3>{cards}</div>')
    return f'<div id="recent-evidence" class="recent-evidence"><p class="note">更新核对：{CUTOFF}。先看工程落点，再看学术方法；经典算法另列为基础依据。</p>'+''.join(blocks)+'</div>'


def route_reading(route_id):
    pubs,links,_=model()
    selected=[l for l in links if l['route_id']==route_id]
    if not selected:
        return '<p class="note">本轮未收录该路线的近期直接证据，方法依据见下方经典原文。这是资料缺口，不代表方向没有进展。</p>'
    return '<div class="route-reading"><strong>关联资料与证据用途</strong>'+''.join(
        f'<a href="#recent-{l["publication_id"]}">{e(pubs[l["publication_id"]]["short"])} · {e(l["role"])} →</a>' for l in selected)+'</div>'


def relevance(key,area_id=None):
    _,links,routes=model()
    rows=[l for l in links if l['publication_id']==key and (area_id is None or l['area_id']==area_id)]
    return '<div class="evidence-relevance"><strong>与技术路线的关系 · 本页归纳</strong><ul>'+''.join(f'<li><b>{e(routes[l["route_id"]]["title"])} / {e(l["role"])}</b>：{e(l["relevance"])}</li>' for l in rows)+'</ul></div>'


def source_directory():
    return directory()


def cite(key,label):
    return f'<a class="source-link" href="{BASE}#publication-{key}">{e(label)} →</a>'


def analysis():
    from research_depth import research_agenda
    pubs,_,routes=model()
    areas={r['id']:r for r in read('research-areas.csv')}
    records=read('analysis-recommendations.csv')
    cards=[]
    for i,r in enumerate(records,1):
        assert routes[r['route_id']]['area_id']==r['area_id']
        citations=''.join(cite(key,pubs[key]['short']) for key in r['publication_ids'].split('|'))
        fields=''.join(f'<dt>{label}</dt><dd>{e(r[field])}</dd>' for label,field in [('路线判断','judgment'),('研究对象','verification_subject'),('建议实验','next_step')])
        conditions=''.join(f'<dt>{label}</dt><dd>{e(r[field])}</dd>' for label,field in [('成立条件','condition'),('适用边界','boundary')])+gate_fields(r['area_id'])
        cards.append(f'''<article id="analysis-{r['area_id']}" class="structured-advice"><p class="analysis-path">0{i} / <a href="{BASE}research-{r['area_id']}.html#route-{r['route_id']}">{e(areas[r['area_id']]['title'])} · {e(routes[r['route_id']]['title'])}</a></p><h3>{e(r['title'])}</h3><dl>{fields}</dl><details class="decision-conditions"><summary>适用条件与继续／停止标准</summary><dl>{conditions}</dl></details><div class="analysis-evidence"><strong>支撑判断的原始资料 · 详细事实见本期动态</strong>{citations}</div></article>''')
    overview='<nav class="analysis-overview" aria-label="按研究方向阅读判断">'+''.join(f'<a href="#analysis-{r["area_id"]}">{e(areas[r["area_id"]]["short"])}<small>{e(r["title"])}</small></a>' for r in records)+'</nav>'
    return f'''<section id="analysis"><p class="eyebrow">04 / 分析结论</p><h2>哪些能力值得构筑，什么条件下值得采用</h2><p>共同研究判断：调度需要看见整项任务的进度、执行代价和资源占用。以下由已收录证据归纳，按技术地图组织；属于研究建议，尚未在云核验证。</p>{weekly_decisions()}{decision_review()}{research_agenda()}<details class="scope-index"><summary>三项技术与判断总览</summary>{overview}</details><div class="analysis-cards">{''.join(cards)}</div>{portfolio()}<p class="note">共同验收以端到端任务有效吞吐为主，达标完成率为护栏，容量拒绝、超时、预算与质量损失纳入统计。存在在线／后台资源竞争时，再评估{cite('learnsched','LearnSched的实验边界')}。</p><div class="reading-next"><a href="#updates">回看本期事实与原文 →</a><a href="#archive">查看研究积累与归档状态 →</a></div></section>'''
