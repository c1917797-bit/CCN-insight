"""Scheduling research pages, normalized by a relation to scheduling-points.csv."""
import csv
from pathlib import Path
from html import escape as e

ROOT = Path(__file__).resolve().parent
BASE = '/business_insight/cloud_core/agent_orchestration/'
LAYERS = [('任务层','任务交给谁，哪些就绪节点先执行'),('服务层','模型请求、推理批次与工具额度分别调度'),('资源层','服务副本放在哪个节点或设备组'),('横向控制','负载和故障变化后如何调整原安排')]
ALIASES = {'intake':'agent-routing','planning':'workflow-scheduling','scheduling':'model-routing','coordination':'tool-scheduling','recovery':'runtime-rescheduling'}

def directions():
    from architecture_map import model
    points,algorithms = model()
    indexed = {p['id']:p for p in points}
    with (ROOT/'research-directions.csv').open(encoding='utf-8',newline='') as f:
        result = [dict(r,point=indexed[r['point_id']]) for r in csv.DictReader(f)]
    assert len(result)==7 and {r['point_id'] for r in result}==set(indexed)
    assert all(r['key']==r['point']['topic'] for r in result)
    return result, algorithms

def list_items(s):
    return ''.join(f'<li>{e(x)}</li>' for x in s.rstrip('。').split('；'))

def map_cards():
    from decision_map import relation_links
    items,_ = directions()
    grouped = []
    for layer, explanation in LAYERS:
        if layer == '横向控制':
            continue
        cards = ''.join(f'<article class="topic-card"><span class="number">{i:02d} / {e(layer)}</span><h3><a href="{BASE}{r["key"]}.html">{e(r["title"])}</a></h3><p>{e(r["intro"])}</p><div class="root-links">{relation_links(r["point_id"])}</div><a class="open" href="{BASE}{r["key"]}.html">进入对象专题 →</a></article>' for i,r in enumerate(items,1) if r['layer']==layer)
        count=sum(r['layer']==layer for r in items)
        grouped.append(f'<div class="direction-layer direction-count-{count}"><div class="direction-layer-heading"><h4>{e(layer)}</h4><p>{e(explanation)}</p></div><div class="topic-grid">{cards}</div></div>')
    return '<p class="note">卡片上的决策标签可进入相应研究专题。任务理解与计划生成提供输入；权限、状态和验收要求提供约束。</p>'+''.join(grouped)

def topic(shell,r,algorithms,legacy=False):
    p = r['point']
    # Scheduling points remain the single source for object/decision/carrier.
    contract = ''.join(f'<div><small>{label}</small><strong>{e(p[key])}</strong></div>' for label,key in [('调度对象','object'),('调度决策','decision'),('执行载体','carrier')])
    candidates = ''.join(f'<li><b>{a}</b> {e(algorithms[a]["name"])} <small>{e(algorithms[a]["kind"])}</small></li>' for a in p['algorithms'].split('|'))
    warning = f'<p class="alias-note">原入口已统一到本方向。<a class="source-link" href="{BASE}{r["key"]}.html">打开统一专题入口 →</a></p>' if legacy else ''
    from decision_map import decision_model
    decisions,links,_,_,_ = decision_model()
    decision_names={row['id']:row['title'] for row in decisions}
    root_links=''.join(f'<a id="decision-{link["decision_id"]}" class="decision-object" href="{BASE}decision-{link["decision_id"]}.html"><strong>{e(decision_names[link["decision_id"]])}</strong><span>{e(link["relation"])}</span></a>' for link in links if link['point_id']==r['point_id'])
    case = f'<a class="button secondary" href="{BASE}heft-coffee.html">HEFT：工作流任务调度教学案例 →</a>' if r['point_id']=='workflow' else f'<a class="button secondary" href="{BASE}#point-{r["point_id"]}">在演示图中定位这个调度点 →</a>'
    body = f'''<header class="hero topic-hero"><a class="back" href="{BASE}#map">← 返回调度技术地图</a><p class="eyebrow">云核 / Agent端到端调度 / {e(r['layer'])}</p><span class="badge">调度研究专题 · 私有草稿</span><h1>{e(r['title'])}</h1><p class="lead">{e(r['intro'])}</p>{warning}<div class="hero-actions"><a class="button" href="#decision">查看调度决策</a><a class="button secondary" href="#routes">查看研究路线</a></div></header>
<section id="decision"><p class="eyebrow">01 / 研究对象</p><h2>这个方向决定什么</h2><div class="point-contract">{contract}</div><article class="card"><h3>用咖啡场景理解调度问题</h3><p>{e(r['question'])}</p>{case}</article></section>
<section id="challenges"><p class="eyebrow">02 / 约束与挑战</p><h2>为什么简单分配还不够</h2><div class="topic-challenges"><article class="card"><h3>需要解决的困难</h3><p>{e(r['challenge'])}</p></article><article class="card"><h3>不能突破的条件</h3><ul>{list_items(r['constraints'])}</ul></article></div></section>
<section id="routes"><p class="eyebrow">03 / 调度路线</p><h2>针对约束比较不同决策机制</h2><article class="card"><h3>涉及哪些调度决策</h3><div class="decision-object-grid">{root_links}</div><h3>候选技术路线</h3><ol>{list_items(r['routes'])}</ol><details class="algorithm-index"><summary>算法参考 · 咖啡演示中的候选策略</summary><ul class="algorithm-list">{candidates}</ul></details><p class="note">路线是待研究的方案；索引沿用用户原图，不等同业界统一分类，也不表示来源框架已实现全部候选策略。</p></article></section>
<section id="evaluation"><p class="eyebrow">04 / 评价方法</p><h2>用同一负载比较调度效果</h2><article class="card"><ul>{list_items(r['metrics'])}</ul><p>固定任务输入、到达过程、执行器能力和可用资源；从简单基线开始比较，再分别改变负载与故障条件。任务质量和完成判定作为约束保留，避免用局部速度替代端到端成功。</p><p class="note">这些是拟采集的指标；当前未运行真实并发、压力或故障实验。</p></article></section>
<section id="scope"><p class="eyebrow">05 / 边界与来源</p><h2>与其他调度方向明确衔接</h2><article class="card"><p>{e(r['boundary'])}</p><p><a class="source-link" href="{e(p['source_url'])}" target="_blank" rel="noopener noreferrer">原始机制依据 · {e(p['source_title'])} ↗</a></p><p class="note">来源用于说明相关基础机制；本页的云核问题组织方式是研究设计，不是现成标准分类或已落地成果。</p></article></section>'''
    from research_map import area_backlinks
    from page_structure import object_guidance
    body += object_guidance(r['point_id'])
    body = body.replace('</header>', '</header>'+area_backlinks(r['point_id']),1)
    html = shell(r['title'], body)
    return html

def boundary_page(shell):
    return shell('调度输入与验收边界',f'''<header class="hero"><a class="back" href="{BASE}#map">← 返回调度技术地图</a><p class="eyebrow">研究范围 / 共同约束</p><h1>调度输入与验收边界</h1><p class="lead">先定义做什么、什么算完成，再讨论怎样调度。这是所有专题的共同约定。</p></header>
<section id="inputs"><h2>输入约定</h2><div class="three-grid"><article class="card"><h3>任务信息</h3><p>目标、已知依赖、质量要求、截止时间与成本预算。</p></article><article class="card"><h3>执行条件</h3><p>执行器能力、可用容量、服务版本、权限与外部接口限制。</p></article><article class="card"><h3>运行状态</h3><p>已完成步骤、等待原因、可恢复状态与外部操作回执。</p></article></div></section>
<section id="ownership"><h2>职责边界</h2><dl class="structured-list"><dt>规划与业务</dt><dd>定义任务目标和操作依赖，决定是否改变业务方案。</dd><dt>调度决策</dt><dd>在约束内决定何时执行、在哪里执行，以及分配多少资源。</dd><dt>运行时管理</dt><dd>执行安排、记录状态并反馈异常，提供恢复与取消能力。</dd><dt>结果验收</dt><dd>核验任务是否满足既定的正确性、时限与成本要求。</dd></dl></section>
<section id="acceptance"><h2>完成判定</h2><article class="card"><h3>本页咖啡演示：取得有效订单回执</h3><p>目标是完成数字点单链路；订单及支付状态需要一致，不能把接口返回成功等同于实物到手。</p><h3>若目标改为咖啡送达</h3><p>必须加入制作、配送与签收状态，并重定义端到端时间。不能沿用点单回执作为完成依据。</p><p class="note">以上是研究范围约定。咖啡教学演示没有执行真实下单、支付或配送。</p></article></section>
<section id="implications"><h2>研究约束</h2><article class="structured-advice"><h3>先固定验收口径，再比较候选策略</h3><dl><dt>共同目标</dt><dd>使用端到端任务达标完成率，同时记录质量、时限和成本。</dd><dt>比较条件</dt><dd>保持任务集合、到达过程与资源条件可比，统计容量拒绝、超时和未完成任务。</dd><dt>判断边界</dt><dd>只改善局部接口延迟，尚不足以证明整任务获益。</dd></dl><a class="source-link" href="{BASE}#north-star">查看北极星指标与统计口径 →</a></article></section>''')
