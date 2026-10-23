"""Question -> three research areas -> routes/evidence -> research recommendations."""
from html import escape as e
from literature_view import topic_recent, route_reading
from page_structure import route_challenge
from decision_map import read, BASE, render_decisions
from scheduling_basics import render_basics, area_context
from coffee_research import render_case, render_metric, case_detail, metric_contribution, CASES
from report_contract import taxonomy
from research_gates import gate_card
from team_strategy import pyramid, methods, contract, metrics
from research_depth import problem_contract, route_audit, experiment_card
from architect_view import architecture_overview, topic_contract


def research_model():
    from direction_pages import directions
    areas=read('research-areas.csv')
    routes=read('research-routes.csv')
    evidence={r['id']:r for r in read('research-evidence.csv')}
    links=read('area-object-links.csv')
    objects={r['point_id']:r for r in directions()[0]}
    assert len(areas)==3 and len({a['id'] for a in areas})==3
    assert len(routes)==len({r['id'] for r in routes})
    assert all(r['area_id'] in {a['id'] for a in areas} and r['evidence_id'] in evidence for r in routes)
    assert {r['area_id'] for r in routes}=={a['id'] for a in areas}
    assert all(l['area_id'] in {a['id'] for a in areas} and l['point_id'] in objects for l in links)
    assert all(s['url'].startswith('https://') for s in evidence.values())
    return areas,routes,evidence,links,objects


def items(text):
    return ''.join(f'<li>{e(s)}</li>' for s in text.rstrip('。').split('；'))


def area_backlinks(point_id):
    areas,_,_,links,_=research_model()
    names={a['id']:a['title'] for a in areas}
    return '<div class="area-backlinks"><span>所属研究方向</span>'+''.join(f'<a href="{BASE}research-{l["area_id"]}.html">{e(names[l["area_id"]])} · {e(l["role"])}</a>' for l in links if l['point_id']==point_id)+'</div>'


def render_research_map():
    jumps='<nav class="map-reading" aria-label="研究地图目录">'+''.join(f'<a href="#{key}">{label}</a>' for key,label in [('architecture-boundaries','架构全景'),('research-directions','核心技术'),('scheduling-essence','调度本质'),('north-star','目标指标'),('runtime-loop','共用底座'),('coffee-task','全景演示')])+'</nav>'
    return jumps+architecture_overview()+f'''<section id="scheduling-decisions" class="pyramid-map"><div id="research-directions"><p class="eyebrow">研究体系 / 一个目标 · 三项技术 · 一个底座</p>{pyramid()}</div>{render_basics()}{metrics()}<div id="runtime-loop" class="research-support"><h2>共用底座：让每次研究成为下一次研究的起点</h2><div class="feedback-steps"><span>任务与资源观测</span><b>→</b><span>代价模型校准</span><b>→</b><span>算法决策与执行</span><b>→</b><span>结果核验与回退</span></div><p>统一 task_id、资源计量和质量约束；模型状态、工具额度与卡资源分别记录。已有材料与演示不是已完成的运行时系统。</p><a class="source-link" href="{BASE}runtime-rescheduling.html">运行反馈与恢复专题 →</a></div>{render_case()}<p class="note">咖啡全景图用于解释三项技术的作用位置；它不是实测调度系统。经典策略、优化求解与学习辅助作为各专题的方法，不与 Agent、模型、工具、设备这些执行层并列。</p></section><details id="scope-index" class="scope-index"><summary>辅助索引 · 按执行对象和决策查找</summary><p>这些入口是核心技术的应用索引，不是额外的根技术。</p>{render_decisions()}</details>'''


def research_page(shell,area):
    areas,routes,evidence,links,objects=research_model()
    selected=[r for r in routes if r['area_id']==area['id']]
    source_ids=list(dict.fromkeys(r['evidence_id'] for r in selected))
    baselines={r['route_id']:r['baseline'] for r in read('route-baselines.csv')}
    route_cards=''.join(f'''<article class="route-detail" id="route-{r['id']}"><span class="number">路线 {i:02d}</span><h3>{e(r['title'])}</h3>{route_challenge(r['id'])}<p><strong>如何应对：</strong>{e(r['mechanism'])}</p>{route_reading(r['id'])}{route_audit(r['id'])}<dl><dt>适用前提</dt><dd>{e(r['condition'])}</dd><dt>主要取舍</dt><dd>{e(r['tradeoff'])}</dd></dl><a class="source-link" href="#evidence-{r['evidence_id']}">相关原始依据 · {e(evidence[r['evidence_id']]['title'])} ↓</a></article>''' for i,r in enumerate(selected,1))
    source_cards=''.join(f'''<article class="evidence-detail" id="evidence-{key}"><span class="number">原文事实</span><h3><a href="{e(evidence[key]['url'])}" target="_blank" rel="noopener noreferrer">{e(evidence[key]['title'])} ↗</a></h3><p>{e(evidence[key]['fact'])}</p><p class="evidence-boundary"><strong>适用边界：</strong>{e(evidence[key]['limit'])}</p></article>''' for key in source_ids)
    comparison=''.join(f'<tr><th scope="row">{e(r["title"])}</th><td>{e(baselines[r["id"]])}</td><td>{e(r["condition"])}</td><td>{e(r["tradeoff"])}</td></tr>' for r in selected)
    applications=''.join(f'<a href="{BASE}{objects[l["point_id"]]["key"]}.html"><strong>{e(objects[l["point_id"]]["title"])}</strong><span>{e(l["role"])}</span></a>' for l in links if l['area_id']==area['id'])
    case={'workflow':'菜单与优惠查询具备并行条件，但比较方案要等待信息返回。研究重点是如何在有限执行名额下减少关键路径等待。','mapping':'点单先选择Agent实例，模型请求再选择已部署副本。只有部署或扩容时才选择设备；三处需要分别定义代价。','sharing':'多人同时点单会竞争模型服务和工具额度。需设置不同任务成本、租户权重和资源容量，才能比较服务份额与完成效果。'}[area['id']]
    body=f'''<header class="hero topic-hero"><a class="back" href="{BASE}#scheduling-decisions">← 返回根技术研究地图</a><p class="eyebrow">云核 / Agent调度 / {e(area['short'])}</p><h1>{e(area['title'])}</h1><p class="lead">{e(area['question'])}</p><p>{e(area['summary'])}</p></header>
<section id="problem"><p class="eyebrow">01 / 研究问题</p><h2>这个方向解决什么问题</h2>{topic_contract(area["id"])}<article class="card"><p>{e(area['background'])}</p>{case_detail(area['id'])}{area_context(area['id'])}<p class="note">{e(area['boundary'])}</p></article></section>
<section id="challenges"><p class="eyebrow">02 / 关键挑战</p><h2>从局部调度走向端到端完成</h2><div class="challenge-grid">{''.join(f'<article><span>挑战 {i:02d}</span><p>{e(text)}</p></article>' for i,text in enumerate(area['challenges'].rstrip('。').split('；'),1))}</div>{problem_contract(area['id'])}</section>
<section id="routes"><p class="eyebrow">03 / 技术路线</p><h2>从可解释基线逐步扩展</h2><p class="note">以下为候选研究路线。关联文献提供方法或问题背景，不表示原论文实现了本文所有Agent扩展。</p>{methods(area["id"])}<div class="research-route-list">{route_cards}</div></section>
<section id="evidence"><p class="eyebrow">04 / 原始证据</p><h2>哪些实现与研究支撑这些路线</h2><p>本节按专题汇集方法依据，保留适用条件；逐条发布动态和全文解读从条目链接进入。</p>{topic_recent(area['id'])}<details class="scope-index"><summary>经典方法与基础依据</summary>{source_cards}</details></section>
<section id="comparison"><p class="eyebrow">05 / 路线比较</p><h2>在相同约束下比较收益与代价</h2><div class="table-scroll"><table><caption>实验对照设计 / 对照机制、适用条件与代价同时固定</caption><thead><tr><th scope="col">候选路线</th><th scope="col">首轮比较基线</th><th scope="col">适用前提</th><th scope="col">主要取舍</th></tr></thead><tbody>{comparison}</tbody></table></div><article class="card">{metric_contribution(area['id'])}<h3>本方向的诊断指标</h3><ul>{items(area['metrics'])}</ul><p class="note">固定任务质量、到达过程和资源条件再比较。当前没有真实Agent系统的性能实验，未将文献结果当作本系统收益。</p></article></section>
<section id="guidance"><p class="eyebrow">06 / 研究建议</p><h2>云核应优先构筑什么</h2><article class="research-recommendation"><span>基于上述问题与证据的建议</span><p>{e(area['advice'])}</p><p class="note">建议须经实际工作负载验证后再形成路线取舍结论。</p></article>{experiment_card(area["id"])}<details class="scope-index"><summary>团队资产与阶段决策门槛</summary>{contract(area["id"])}{gate_card(area["id"])}</details><article class="card"><h3>用咖啡案例理解</h3><p>{e(case)}</p><a class="source-link" href="{BASE}#agent-demo">打开咖啡教学演示 →</a>{f'<p><a class="source-link" href="{BASE}heft-coffee.html">查看可复算的HEFT教学案例 →</a></p>' if area['id']=='workflow' else ''}</article><details class="scope-index"><summary>查看适用对象与执行层专题</summary><div class="application-links">{applications}</div></details></section>'''
    return shell(area['title'],body)
