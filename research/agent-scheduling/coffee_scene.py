"""Vector teaching scene: task flow, service calls and resource support."""
from html import escape as e
import csv
from pathlib import Path

def decisions():
    with (Path(__file__).parent/'coffee-scheduling-decisions.csv').open(encoding='utf-8',newline='') as f:
        return list(csv.DictReader(f))

def decision_story(step):
    selected=[d for d in decisions() if str(step) in d['steps'].split()]
    if not selected:
        text = {1: '任务规划把用户目标变成步骤与依赖，为调度提供输入；它不是在多个就绪步骤之间做调度选择。', 4: '这是授权门槛：未获授权的下单步骤不能开始。授权到达后，再交给 S2 排程和 S5 工具调度。', 6: '这是任务验收：核对结果后结束原委托。只有执行失败或受阻需要恢复时，才重新触发相关调度决策。'}[step]
        return '<p class="cs-not-scheduler"><strong>此处是什么决策？</strong>'+text+'</p>'
    outputs={'agent':'一个被选中的 Agent 实例；整项任务进入它的运行环境。','ready':'从 C01 执行计划中选出本次能开始的步骤；运行时程序负责调用服务和记录结果。','replica':'一个被选中的模型副本；推理请求进入它的等待队列。','batch':'本轮推进的请求集合和分配给它们的 token 预算。','tool':'本次获准调用的工具请求；其余请求继续等待。'}
    return '<div class="cs-algorithm-explain">'+''.join(f'<article><h4>{d["marker"]} · {e(d["title"])}</h4><dl><dt>这里要决定</dt><dd>{e(d["question"])}</dd><dt>需要看什么</dt><dd>{e(d["inputs"])}</dd><dt>决定之后</dt><dd>{e(outputs[d["id"]])}</dd></dl><a href="#coffee-scheduler-{d["id"]}">进一步查看候选算法与例子 →</a></article>' for d in selected)+'</div>'

def decision_reference():
    rows=''.join(f'<tr id="coffee-scheduler-{d["id"]}" data-cs-decision="{d["steps"]}"><th scope="row"><span>{d["marker"]}</span><a href="{d["href"]}">{e(d["title"])}</a></th><td>{e(d["inputs"])}</td><td><strong>{e(d["policy"])}</strong><p>教学示例：{e(d["example"])}</p><p>{e(d["boundary"])}</p><a href="{d["source_url"]}" target="_blank" rel="noopener noreferrer">{e(d["source_title"])} ↗</a></td></tr>' for d in decisions())
    return '<section class="cs-decision-reference" id="coffee-scheduling-points"><h3>先看清决策位置，再研究怎么选</h3><p>当多人点单、执行名额有限或存在多个副本时，需要在这些关口作出选择。S1–S5 标记任务与服务调度位置；M1 补充模型选择，P1/P2 表示资源放置与共享。它们是不同层面的决策位置，不是八类互斥的根技术。</p><details class="scope-index"><summary>展开候选算法、教学示例与原始依据</summary><p>以下是可研究的策略，并非演示已执行的算法；示例数字均为假设。</p><div class="table-scroll"><table><caption>位置 → 输入状态 → 候选策略与适用边界</caption><thead><tr><th>调度位置</th><th>算法读取什么</th><th>怎样决策</th></tr></thead><tbody>'+rows+'</tbody></table></div></details><p class="cs-extra-scheduling"><strong>部署与故障时还有两类触发：</strong>新增服务副本时，<a href="resource-placement.html">资源放置</a>选择设备；失败或阻塞时，<a href="runtime-rescheduling.html">运行时管理</a>决定恢复与重新调度。它们按事件触发，不是每次点单都要经过的步骤。</p></section>'

STAGES = [
    ('接收委托', '同一杯咖啡，先交给一个 Agent 负责', '用户只提出一个目标。S1 从能力与权限匹配的实例中选择 Agent，整项委托编号为 C01；后面的所有步骤都在完成这一个目标。', '执行映射', 'research-mapping.html'),
    ('拆成步骤', '子任务从哪里来？就是点咖啡这件事的具体步骤', 'Agent 依据用户要求与预设流程或规划，形成 C01 的执行计划：查询菜单与优惠、比较方案、确认授权、下单核验。每个步骤带有输入、完成条件和依赖；图中的 C01.1、C01.2 都归属于原委托 C01。', '任务规划 · 提供调度输入', 'research-workflow.html'),
    ('查询信息', '先找出能做的步骤，再决定是否并行', '本例已确定门店，菜单与优惠查询互不依赖，均可进入待执行集合；比较方案还要等两份结果。S2 在执行名额允许时安排两项查询，运行时程序再通过 S5 获取各接口额度并发起调用。', '任务排程 · 工具额度', 'research-workflow.html'),
    ('比较方案', '查询结果齐了，比较方案才具备执行条件', '菜单与优惠返回后，C01.3 被解锁，经过 S2 排程获得执行名额。运行时程序把两份结果交给模型：先按语义与质量成本约束选择模型，再由 S3 选择该模型的副本，S4 决定该副本本轮处理哪些请求。判断结果仍归入同一任务 C01。', '任务排程 · 模型调度', 'research-mapping.html'),
    ('确认授权', '方案有了，仍需检查能不能下单', '核对口味、价格、预算和购买授权。缺少授权时等待用户确认，下单步骤保持等待；授权到达后才进入可执行集合。调度不能跳过业务约束。', '业务约束 · 不是调度算法', 'research-workflow.html'),
    ('下单核验', '只启动已获授权的步骤，并核验操作结果', 'C01.5 经 S2 获得执行名额，再由工具调用程序经 S5 取得商家接口额度。提交后核对订单与扣款；响应不确定时先查状态，避免重复下单。', '任务排程 · 工具调度', 'research-sharing.html'),
    ('返回回执', '把 C01 的核验结果交回最初的用户', 'Agent 汇总步骤状态，确认订单回执有效后，结束原始委托 C01。这里完成的是下单任务，不代表咖啡已经送达；若目标包括送达，还要新增交付确认步骤。', '任务验收', '#north-star'),
]
QUEUE_STATES = [
    ('尚未生成执行计划', '先把整项委托交给 Agent'),
    ('先明确步骤与依赖', '查菜单、查优惠彼此独立'),
    ('可开始：查菜单、查优惠', '比较方案仍等待两份结果'),
    ('可开始：比较方案', '菜单与优惠已返回，可提供输入'),
    ('等待：用户确认授权', '下单尚未获授权，不能开始'),
    ('可开始：下单并核验', '方案确定，购买操作已获授权'),
    ('已完成：订单回执已核验', '把结果交回原始委托 C01'),
]


from coffee_decision_diagram import diagram


def render():
    from coffee_live_scene import render as live_render
    return live_render(decision_reference)
