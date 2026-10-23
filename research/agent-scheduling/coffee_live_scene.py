from coffee_dag_diagram import diagram
from html import escape as esc
from pathlib import Path
import csv

def decision_focus():
    with (Path(__file__).parent/'coffee-gates.csv').open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    tabs=''.join('<button type="button" data-decision-select="'+r['id']+'" aria-pressed="'+str(r['id']=='S2').lower()+'" aria-controls="coffee-decision-focus">'+r['id']+' '+esc(r['title'])+'</button>' for r in rows)
    panels=''.join('<article data-decision-panel="'+r['id']+'"'+('' if r['id']=='S2' else ' hidden')+'><h3>'+r['id']+' · '+esc(r['question'])+'</h3><p><strong>约束条件：</strong>'+esc(r['trigger'])+'</p><dl><dt>决策输入</dt><dd>'+esc(r['inputs'])+'</dd><dt>决策输出</dt><dd>'+esc(r['output'])+'</dd></dl></article>' for r in rows)
    return '<aside class="cs-decision-focus" id="coffee-decision-focus"><div class="cs-decision-tabs" role="group" aria-label="查看调度关口">'+tabs+'</div>'+panels+'</aside>'


def render(reference):
    return '''<section id="coffee-task" class="coffee-task coffee-scene" data-coffee-scene>
<div class="cs-section-heading"><div><p class="eyebrow">从一杯咖啡看懂调度</p><h2>一张图，看全 Agent 任务如何完成。</h2></div><span class="cs-demo-label">可运行的教学模拟 · 非真实交易</span></div>
<p class="coffee-goal">用户只说“帮我点一杯咖啡”。Agent 先把目标变成有依赖的步骤；调度再决定<strong>哪一步现在能做、交给谁、用多少资源</strong>。沿着 C01 看下去，每一个结果都属于最初的这项委托。</p>
<div class="cs-console"><div class="cs-console-top"><div><span class="cs-live-dot" aria-hidden="true"></span><strong>COFFEE / 同一任务的运行现场</strong></div><span>用户 → Agent → 模型 / 工具 → 卡与资源</span></div>
<div class="cs-controls cs-controls-top"><div><button type="button" data-cs-action="play" aria-pressed="false">开始演示</button><button type="button" data-cs-action="next">推进一拍</button><button type="button" data-cs-action="reset">重新开始</button></div><label>执行名额 <select data-cs-slots aria-label="执行名额"><option value="2">2 个 · 可并行</option><option value="1">1 个 · 需排队</option></select></label><label><input type="checkbox" data-cs-slow>优惠返回更慢</label></div>
<div class="cs-live-summary" role="status" aria-live="polite" aria-atomic="true"><strong data-cs-caption>准备就绪：先把整项委托交给 Agent。</strong><span data-cs-progress>演示时钟 T+0 · 非实测时间</span></div>
<div class="cs-graph-heading"><div><strong>从任务分派到服务执行</strong><span>金色：调度决策　青色流动：请求　绿色流动：结果　点线：资源承载</span></div><div class="cs-view-tools"><button type="button" data-cs-action="overview" aria-pressed="false">查看全图</button><button type="button" data-cs-action="zoom" aria-pressed="false">放大细节</button><button type="button" data-cs-action="expand" aria-pressed="false">展开全景 ↗</button></div></div>
<div class="cs-viewport" tabindex="0" role="region" aria-label="Agent 调度全景图，默认按宽度阅读，可上下浏览；窄屏可横向滚动，也可切换全图或放大">'''+diagram()+'''</div>
<div class="cs-map-tools"><button type="button" data-cs-action="contention">演示：两项查询，一个名额</button><button type="button" data-cs-action="model-tour">演示：一次模型调用</button><span>全图包含用户、Agent 内部 DAG、模型副本、工具服务及卡资源。点击调度节点查看约束与决策；点击步骤查看等待原因。</span></div>
'''+decision_focus()+'''<p class="cs-runtime-boundary">架构依据：<a href="https://github.com/vllm-project/semantic-router" target="_blank" rel="noopener noreferrer">vLLM Semantic Router · 模型选择</a> · <a href="https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/rate_limiter.html" target="_blank" rel="noopener noreferrer">Triton · 跨模型执行资源管理</a>。<a href="https://docs.vllm.ai/en/v0.31.0/serving/parallelism_scaling/" target="_blank" rel="noopener noreferrer">vLLM · 多卡与多节点并行</a>。这些资料为实现参考，昇腾需核对对应运行时能力。</p><div class="cs-state-legend"><span>○ 等待依赖</span><span class="ready">● 就绪待排程</span><span class="running">● 执行中</span><span class="waiting">◇ 等待授权</span><span class="success">✓ 已完成</span></div>
<div class="cs-runtime"><div class="cs-ready-panel"><small>S2 · 就绪队列与执行名额</small><strong>依赖满足 ≠ 立即执行</strong><p data-ready-list>先生成执行计划，再找出就绪步骤。</p><p data-slot-state>执行名额：0 / 2</p></div><div class="cs-node-inspector"><small data-inspector-code>C01 · 整项委托</small><strong data-inspector-title>运行时负责把选中的步骤真正执行</strong><p data-inspector-body>它读取输入、调用模型或工具、记录结果；不是另一个替用户点单的 Agent。</p></div></div>
<div class="cs-authorization" hidden data-authorization><div><strong>方案已生成，现在等用户确认</strong><p>授权不是调度算法。未确认时，下单保持阻塞，等待不占执行名额。</p></div><button type="button" data-cs-action="authorize">模拟授权并继续</button></div>
<p class="cs-runtime-boundary">本例实际运行 DAG 依赖、就绪排程、名额限制与授权等待。模型调用按示意策略依次展示选模型 R、选副本 R1、排批次与卡上执行；不进行真实模型推理。多设备放置、多卡并行和共卡调度展示系统职责，不模拟硬件隔离、资源份额或性能收益。</p>
<details class="cs-event-log" open><summary>任务轨迹 · 最新在前，全部归属 C01</summary><ol data-cs-log><li>T+0 · 收到委托 C01：帮我点一杯咖啡。</li></ol></details></div>
<div class="cs-reading-note"><strong>试着改一个条件</strong><p>切换到 1 个执行名额，两项查询会排队；勾选“优惠返回更慢”，菜单先完成，比较方案仍要等待。每次调整会重置演示。模拟确认授权后，才会启动下单。所有时长仅用于教学，不能当作性能数据。</p></div>
'''+reference()+'''<details class="scope-index"><summary>演示假设与技术边界</summary><p>本例固定门店，菜单与优惠可独立查询；实际业务的依赖应以接口和规则为准。执行计划为一次正常路径的 DAG，真实 Agent 还可重新规划、循环或分支。示例就绪步骤按进入就绪集合的顺序选择，同拍按步骤编号；执行名额是运行时允许的在途步骤数，不等于 CPU 核或 GPU 张数。</p><p>授权等待不占执行名额；下单、核验分别建模。演示假设 API 正常返回。生产系统还需要超时、取消、幂等、状态持久化与故障恢复；响应不确定时应先查订单状态，不能盲目重试支付。回执核验完成仅表示下单任务完成，不表示咖啡送达。</p><p>服务通常已部署，模型依赖 GPU/NPU 单卡或兼容的多卡组，工具通常使用 CPU、网络和外部 API。这里按职责分层，不要求 Agent 与执行程序独立部署。</p><a href="#agent-demo">查看完整系统关系 →</a></details></section>'''
