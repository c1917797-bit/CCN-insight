"""Build a native, accessible architecture figure and its cited descriptions.

Small CSV relations hold scheduling points and candidate strategies. The SVG is
a proposed architecture, not a captured production implementation or benchmark.
"""
import csv
from pathlib import Path
from html import escape as e

ROOT = Path(__file__).resolve().parent
BASE = '/business_insight/cloud_core/agent_orchestration/'

def rows(name):
    with (ROOT / name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def model():
    points = rows('scheduling-points.csv')
    algorithms = {r['id']: r for r in rows('candidate-algorithms.csv')}
    assert len(points) == 7 and len({p['id'] for p in points}) == 7
    assert len(algorithms) == 14
    for p in points:
        assert set(p['algorithms'].split('|')) <= algorithms.keys()
        assert p['source_url'].startswith('https://')
    return points, algorithms

from diagram_v2 import diagram

STEPS = [
    ('接收任务', '准入与分派：用户明确商品、预算与完成条件，任务被接纳后交给Agent B。这里只展示接纳后的流转，不模拟容量拒绝或下单。', 'user access', 'intake agent-entry'),
    ('生成任务图', 'Agent建立任务状态：查门店后并行查询菜单与优惠；模型比较后等待用户授权。图中展示的是无环片段。', 'workflow shop menu offers compare confirm', 'dag-menu dag-offer menu-join offer-join compare-confirm dag-ready'),
    ('并行查询', '排序、分派与分配：菜单和优惠就绪后安排执行，交给工具执行器并取得并发额度；结果写回Agent状态。演示不比较真实排程性能。', 'workflow menu offers tools tool-worker cpu', 'tool-call tool-api tool-result cpu-tools'),
    ('模型比较', '分派、排序与分配：比较请求路由到实例2，在token及KV容量约束下安排推理，计算后返回候选方案。演示没有制造多请求批次。', 'compare model-route batch gpu workflow', 'model-call model-batch model-result gpu-support'),
    ('授权与操作', '用户授权后才能下单和支付；超时要核验订单与支付状态再决定重试。演示只展示流转，不调用真实接口。', 'confirm purchase tools tool-worker workflow feedback', 'authorize-effect tool-call tool-api tool-result feedback-agent'),
    ('核验与返回', 'Agent核验有效订单与支付回执，满足本例约定后向用户返回结果。如果目标是咖啡送达，必须继续加入制作、配送与到手核验。', 'workflow result', 'user-result'),
]

def coverage():
    cases = [
        ('工作流依赖与并行', '查询分支、汇合、授权与结果返回', '多份任务图同时推进，竞争Agent与工具名额', '不同商品、门店与约束；观察单任务和整体完成情况'),
        ('Agent与模型分流', '标出任务与推理请求的路由位置', '可比较分流、排队、优先级与租户公平性', '改变到达率、任务复杂度与实例容量，不能只增加用户图标'),
        ('推理批次与KV资源', '标出实例内批次调度位置', '模型请求重叠时可形成批次与容量竞争', '明确每任务的模型调用量、输入／输出长度与KV容量；多人不必然形成KV压力'),
        ('工具额度与副作用', '查询、支付授权、幂等与状态核验', '同一门店或支付接口的额度、并发与重复操作', '注入429、超时或不确定响应；核验业务状态与恢复时间'),
        ('放置与拓扑约束', '解释服务部署与请求路由的区别', '负载上升可用于设计扩容与副本放置测试', '要设置资源不足、异构设备或成组拓扑需求；人数增加不会自动产生这些约束'),
        ('长期恢复与验收', '订单与支付回执的简化验收', '部分任务失败、取消或重启后继续完成其他任务', '明确检查点、故障注入与长时等待；咖啡到手还需配送及到手核验'),
    ]
    lines = ''.join('<tr>'+''.join(f'<{tag}>{e(value)}</{tag}>' for tag,value in zip(('th','td','td','td'),r))+'</tr>' for r in cases)
    return f'''<section id="demo-coverage" class="coverage-section"><p class="eyebrow">场景扩展 / 单人流程 → 多人并发 → 故障恢复</p><h3>同一个咖啡场景，逐层覆盖调度问题</h3><p><strong>结论：</strong>多人同时点咖啡可以覆盖并发调度，不必为了讲并发另换业务。单人讲清执行链，多人引入资源竞争，再加入负载差异与故障解释调度取舍。需要区分“能构造这种测试”与“已经验证有效”：当前动画仍是单任务教学演示，下面的多人及故障扩展是设计方案。</p><div class="table-scroll"><table class="coverage-table"><caption>覆盖判断是设计分析；多人并发、压力与故障方案尚未实测。</caption><thead><tr><th>技术问题</th><th>单人咖啡演示</th><th>多人咖啡可以扩展什么</th><th>需要明确的测试条件</th></tr></thead><tbody>{lines}</tbody></table></div><div class="three-grid"><article class="card"><span class="number">01 / 单人执行</span><h3>讲清任务流程</h3><p>展示依赖、并行查询、模型与工具调用、授权和结果返回。当前六步演示已提供。</p></article><article class="card"><span class="number">02 / 多人并发</span><h3>讲清资源竞争</h3><p>拟让多人同时或突发点单，设定不同优先级、任务代价与预算；比较排队、公平性、完成时间和吞吐。</p></article><article class="card"><span class="number">03 / 故障扩展</span><h3>讲清恢复取舍</h3><p>拟加入接口限流、模型过载、执行器故障与用户取消；观察重试、幂等、降级与状态恢复。</p></article></div><p><strong>边界：</strong>并发人数增加不等于KV满载、拓扑受限或成组调度。它们需要对应的模型负载与资源约束。优先复用咖啡场景；只有当它无法合理体现实际研究负载时，再补充代码或资料任务。</p><p class="note">其他任务形态的可选参照：<a class="source-link" href="https://arxiv.org/abs/2310.06770" target="_blank" rel="noopener noreferrer">SWE-bench</a>与<a class="source-link" href="https://webarena.dev/static/paper.pdf" target="_blank" rel="noopener noreferrer">WebArena</a>。不是本页调度效果的证据，也不意味着必须改用这些场景。</p></section>'''

def render():
    points, algorithms = model()
    selector = ''.join(f'<button type="button" data-point-select="{p["id"]}" aria-controls="point-{p["id"]}" aria-pressed="false">{p["number"]} {p["title"]}</button>' for p in points)
    details = []
    for p in points:
        badges = ''.join(f'<li><b>{a}</b> {e(algorithms[a]["name"])} <small>{e(algorithms[a]["kind"])}</small></li>' for a in p['algorithms'].split('|'))
        opened = ' open' if p['id'] == 'workflow' else ''
        details.append(f'''<details id="point-{p['id']}" class="point-detail" data-point-detail="{p['id']}"{opened}><summary>{p['number']} {p['title']}<span>{e(p['object'])}</span></summary><div class="point-body"><div class="point-contract"><div><small>调度对象</small><strong>{e(p['object'])}</strong></div><div><small>调度决策</small><strong>{e(p['decision'])}</strong></div><div><small>执行载体</small><strong>{e(p['carrier'])}</strong></div></div><h4>作用与关联</h4><p>{e(p['description'])}</p><h4>候选算法／策略</h4><ul class="algorithm-list">{badges}</ul><p class="boundary"><strong>适用边界：</strong>{e(p['boundary'])}</p><div class="point-links"><a href="{BASE}{p['topic']}.html">进入对应研究方向 →</a><a href="{e(p['source_url'])}" target="_blank" rel="noopener noreferrer">原始依据 · {e(p['source_title'])} ↗</a></div></div></details>''')
    steps = ''.join(f'<li data-map-step="{i}" data-nodes="{nodes}" data-edges="{edges}"><strong>{i+1:02d} {e(title)}</strong><p>{e(body)}</p></li>' for i,(title,body,nodes,edges) in enumerate(STEPS))
    return f'''<div class="architecture-intro"><span class="badge">系统结构草稿 · 原图重绘</span><h2>看清一次任务，如何穿过整个系统</h2><p>任务先交给Agent实例；Agent运行时维护任务图与状态，子任务按需调用模型或工具；模型与工具使用不同的底层资源。部署和运行控制在侧边支撑这条执行链。</p></div><div class="map-frame" id="agent-demo"><div class="map-toolbar"><div><strong>Agent调度实体关系图</strong><p>咖啡仅是演示实例 · 点击节点查看调度说明</p></div><a class="source-link" href="#demo-coverage">查看演示覆盖边界 ↓</a></div><div class="map-legend"><span class="legend-call">实线 → 请求／任务流转</span><span class="legend-return">实线 → 结果写回</span><span class="legend-deploy">点线 → 部署支撑</span><span class="legend-feedback">虚线 → 状态反馈</span></div><div class="demo-player"><div class="demo-heading"><strong>咖啡任务 · 六步动画</strong><span>单任务演示 · 不调用真实接口</span></div><div class="player-controls"><button type="button" data-map-action="play" aria-pressed="false">播放演示</button><button type="button" data-map-action="previous">上一步</button><button type="button" data-map-action="next">下一步</button><button type="button" data-map-action="reset">重置</button><button type="button" data-map-action="zoom" aria-pressed="false">放大图</button><span data-map-progress aria-live="polite">系统结构 · 尚未播放</span></div><div class="demo-timeline" aria-label="六步演示"><button type="button" data-step-select="0" aria-pressed="false"><span>01</span>接入</button><button type="button" data-step-select="1" aria-pressed="false"><span>02</span>规划</button><button type="button" data-step-select="2" aria-pressed="false"><span>03</span>查询</button><button type="button" data-step-select="3" aria-pressed="false"><span>04</span>推理</button><button type="button" data-step-select="4" aria-pressed="false"><span>05</span>操作</button><button type="button" data-step-select="5" aria-pressed="false"><span>06</span>返回</button></div><p class="demo-message" data-map-message role="status">点击播放，沿移动光点看请求和结果如何流转。部署支撑保持静态；点击任一节点展开技术说明。</p><a class="source-link" href="{BASE}heft-coffee.html">深入一个算法：HEFT子任务排程与可复算对照 →</a></div><div class="map-scroll" tabindex="0" aria-label="实体关系图，窄屏可左右滚动">{diagram()}</div><details class="demo-transcript"><summary>阅读六步演示文字</summary><ol>{steps}</ol></details><p class="map-footnote">Agent框表示逻辑归属，不要求所有执行器同进程。一般任务图可以带循环；这里用咖啡DAG示意。下方候选索引A01–A13、L01沿用你的截图标识，属于候选策略索引，并非行业统一分类。</p></div><section class="map-details"><h3>七个调度点，各自解决不同决策</h3><p>先看对象与执行载体，再比较策略。以下是面向云核的设计建议；来源说明相关基础机制，不代表某个框架已经实现本图所有候选策略。</p><div class="point-selector" aria-label="调度点选择">{selector}</div><div class="point-details">{''.join(details)}</div><p class="note">图依据你提供的最新版全景图截图重新绘制。连续批处理属于机制，Filter–Score属于框架，令牌桶属于限流；三者与候选排程策略分别说明。</p></section>{coverage()}'''
