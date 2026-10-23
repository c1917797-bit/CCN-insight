"""Four decision outputs, normalized object/algorithm relations, and reading pages.

An editorial research framework, not an industry-standard taxonomy.
"""
import csv
from pathlib import Path
from html import escape as e

ROOT = Path(__file__).resolve().parent
BASE = '/business_insight/cloud_core/agent_orchestration/'


def read(name):
    with (ROOT / name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def decision_model():
    from direction_pages import directions
    decisions = read('scheduling-decisions.csv')
    links = read('decision-object-links.csv')
    algorithm_links = read('decision-algorithm-links.csv')
    objects, algorithms = directions()
    ids = {r['id'] for r in decisions}
    points = {r['point_id']: r for r in objects}
    assert ids == {'admission', 'ordering', 'dispatch', 'allocation'}
    assert len(decisions) == len(ids)
    assert all(r['decision_id'] in ids and r['point_id'] in points for r in links)
    assert len({(r['decision_id'], r['point_id']) for r in links}) == len(links)
    assert {r['point_id'] for r in links} == set(points)
    assert all(r['decision_id'] in ids and r['algorithm_id'] in algorithms for r in algorithm_links)
    assert {r['algorithm_id'] for r in algorithm_links} == set(algorithms)
    assert len({(r['decision_id'], r['algorithm_id']) for r in algorithm_links}) == len(algorithm_links)
    return decisions, links, points, algorithm_links, algorithms


def relation_links(point_id):
    decisions, links, _, _, _ = decision_model()
    names = {r['id']: r['title'] for r in decisions}
    return ''.join(f'<a class="decision-tag" href="{BASE}decision-{l["decision_id"]}.html" title="{e(l["relation"])}">{e(names[l["decision_id"]])}</a>' for l in links if l['point_id'] == point_id)


def bullets(text):
    return ''.join(f'<li>{e(x)}</li>' for x in text.split('；'))


def render_decisions():
    decisions, _, objects, _, _ = decision_model()
    map_rows = read('map-rows.csv')
    map_cells = read('map-cells.csv')
    questions = {'admission':'接不接？','ordering':'何时执行？','dispatch':'交给谁？','allocation':'用多少？'}
    rows = []
    for row in map_rows:
        cells = []
        for decision in decisions:
            cell = next(c for c in map_cells if c['row_id']==row['id'] and c['decision_id']==decision['id'])
            obj=objects[cell['point_id']]
            cells.append(f'<td><a class="matrix-cell" href="{BASE}{obj["key"]}.html#decision-{decision["id"]}" aria-label="{e(row["title"])} · {e(decision["title"])}：{e(cell["label"])}"><span>{e(cell["label"])}</span><small>查看专题 <span aria-hidden="true">↗</span></small></a></td>')
        topics=''.join(f'<a href="{BASE}{objects[p]["key"]}.html">{e(objects[p]["title"])} ↗</a>' for p in row['topics'].split('|'))
        rows.append(f'<tr><th scope="row"><strong>{e(row["title"])}</strong><small>{e(row["meaning"])}</small><div class="matrix-topic-links">{topics}</div></th>{"".join(cells)}</tr>')
    legacy = ''.join(f'<span id="{key}"></span>' for key in ('scheduling-roots', 'root-ordering', 'root-balancing', 'root-dependency', 'root-sharing', 'root-placement-root', 'root-adaptive'))
    return f'''{legacy}<section id="decision-scope" class="decision-map">
<p class="eyebrow">技术地图 / 一张表定位研究问题</p><h2>调度对象 × 调度决策</h2>
<p class="matrix-instruction">先选一行工作对象，再选一列决策。点击交叉点，进入专题中对应的决策说明。</p>
<span id="scheduling-directions"></span><div class="table-scroll unified-map" tabindex="0" role="region" aria-label="调度对象与决策矩阵，窄屏可横向滚动"><table><caption>各行表示不同层级的工作单元；同一用户任务可产生多个子任务与请求。各列区分决策结果，不表示决策彼此独立。这里是研究索引，非已实现能力清单。</caption><thead><tr><th scope="col">调度什么<small>工作所在层级</small></th>{''.join(f'<th scope="col" id="decision-{r["id"]}"><a href="{BASE}decision-{r["id"]}.html">{e(r["title"])}</a><small>{questions[r["id"]]}</small></th>' for r in decisions)}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="matrix-example"><strong>如何区分：</strong>接受一个请求＝准入；让它等待后在某时刻启动＝时序；指定实例2＝分派；给它多少token或并发预算＝资源分配。</p>
<p id="scheduling-feedback" class="matrix-feedback"><strong>运行重调度</strong>根据状态变化重新做上述决策，是贯穿矩阵的反馈过程。<a class="source-link" href="{BASE}runtime-rescheduling.html">查看反馈与恢复 →</a></p>
<details id="scheduling-dimensions" class="decision-matrix"><summary>分类边界与研究条件</summary><p>这张表按工作层级和决策结果组织阅读，不宣称为行业标准或数学上的独立分解。资源额度影响启动时机，实例选择也影响可用容量，具体算法可以联合求解。</p><dl class="dimension-list"><dt>约束条件</dt><dd>依赖、期限、容量、缓存亲和、成组要求和授权。</dd><dt>评价目标</dt><dd>任务完成时间、尾延迟、吞吐、成本与公平性。</dd><dt>求解方法</dt><dd>规则与启发式、数学优化、学习方法；它们不与工作对象并列。</dd></dl><p>依赖满足不等于接纳新任务；成组启动与并发许可属于启动或资源条件。令牌桶在不同实现中可用于入口拒绝或已接纳请求的等待，不能一概等同准入。</p><p class="note">统一目标是在质量、安全和资源约束下改善任务完成；各专题按挑战、方法、证据与适用条件展开。</p></details></section>'''


def decision_page(shell, r):
    _, links, objects, algorithm_links, algorithms = decision_model()
    object_cards = ''.join(f'<a class="decision-object" href="{BASE}{objects[l["point_id"]]["key"]}.html"><strong>{e(objects[l["point_id"]]["title"])}</strong><span>{e(l["relation"])}</span></a>' for l in links if l['decision_id'] == r['id'])
    candidates = ''.join(f'<li><strong>{e(l["algorithm_id"])} · {e(algorithms[l["algorithm_id"]]["name"])}</strong><p>{e(l["relation"])}</p></li>' for l in algorithm_links if l['decision_id'] == r['id'])
    extra = '<p class="note">原图没有单独列出公平份额算法。成组资源协调不能代替DRF等公平分配策略；多人并发只提供测试场景，并不自动实现公平。</p>' if r['id'] == 'allocation' else ''
    advice = {
        'admission': '先固定待处理集合的边界：入口决定接纳或拒绝，接纳后等待执行不算再次准入。以限长队列和过载拒绝为基线，再评估代价预测能否改善期限内完成率。',
        'ordering': '以FIFO为可解释基线；有期限再比较期限规则，有任务图再比较关键路径与HEFT。同步检查短任务收益和低优先级最长等待，避免只看平均值。',
        'dispatch': '先分开请求路由与部署放置。对固定副本池比较轮询、在途数与预计代价；只有缓存和拓扑信息可观测时，再引入对应策略并计入信息及迁移开销。',
        'allocation': '先定义份额单位、租户权重和服务目标，再比较均分、加权分配与多资源策略。同时记录完成时间和资源效率，避免把公平简单理解为每人同样多的请求。',
    }[r['id']]
    body = f'''<header class="hero topic-hero"><a class="back" href="{BASE}#decision-scope">← 返回调度决策辅助索引</a><p class="eyebrow">云核 / Agent端到端调度 / 决策研究</p><span class="badge">研究设计 · 私有草稿</span><h1>{e(r['title'])}</h1><p class="lead">{e(r['question'])}</p><p class="decision-output"><strong>决策结果</strong>{e(r['output'])}</p></header>
<section id="problem"><p class="eyebrow">01 / 问题与挑战</p><h2>为什么需要这个决策</h2><div class="card"><p>{e(r['principle'])}</p><h3>关键挑战</h3><p>{e(r['challenge'])}</p><h3>咖啡实例</h3><p>{e(r['coffee'])}</p></div></section>
<section id="routes"><p class="eyebrow">02 / 方法与依据</p><h2>有哪些候选技术路线</h2><div class="card"><ul>{bullets(r['methods'])}</ul><p><a class="source-link" href="{e(r['source_url'])}" target="_blank" rel="noopener noreferrer">原始依据 · {e(r['source_title'])} ↗</a></p><p class="note">来源支撑相关基础方法；不表示本文所有候选都由同一来源实现或验证。</p><details class="algorithm-index"><summary>算法参考 · 咖啡演示中的决策对应</summary><ul class="decision-candidates">{candidates}</ul>{extra}</details></div></section>
<section id="objects"><p class="eyebrow">03 / 执行层关联</p><h2>这个决策作用在哪里</h2><div class="decision-object-grid">{object_cards}</div></section>
<section id="evaluation"><p class="eyebrow">04 / 比较与边界</p><h2>怎样比较路线是否有效</h2><div class="card"><ul>{bullets(r['metrics'])}</ul><p>{e(r['boundary'])}</p><p>固定到达过程、任务质量、执行器能力与可用资源；分别测试平稳、突发及代价估计失准情形。当前没有真实系统性能结果。</p></div></section>
<section id="guidance"><p class="eyebrow">05 / 研究建议</p><h2>从可解释基线逐步推进</h2><div class="card"><p>{e(advice)}</p><p class="note">这是基于前述问题与边界提出的研究建议，尚待实际负载验证。</p><a class="source-link" href="{BASE}#agent-demo">在咖啡教学演示中定位执行过程 →</a></div></section>'''
    return shell(r['title'], body)
