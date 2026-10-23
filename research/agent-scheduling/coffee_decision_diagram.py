"""Follow one request through planning, ready steps and service scheduling."""
from html import escape as e


def diagram():
    def box(x, y, w, title, lines, steps, kind='', h=84):
        return (f'<g class="cs-node {kind}" data-cs-node="{steps}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/>'
                f'<text x="{x+16}" y="{y+29}" class="cs-node-title">{e(title)}</text>'
                + ''.join(f'<text x="{x+16}" y="{y+53+i*20}" class="cs-node-sub">{e(line)}</text>' for i,line in enumerate(lines)) + '</g>')

    def gate(x,y,w,marker,target,question,context,steps):
        return f'<a href="#coffee-scheduler-{target}" class="cs-scheduler-link"><g class="cs-node cs-gate" data-cs-node="{steps}"><path class="cs-gate-shape" d="M{x+13} {y}H{x+w-13}L{x+w} {y+51}L{x+w-13} {y+102}H{x+13}L{x} {y+51}Z"/><text x="{x+23}" y="{y+25}" class="cs-gate-kicker">{marker} / 这里需要调度 ↗</text><text x="{x+23}" y="{y+54}" class="cs-gate-question">{e(question)}</text><text x="{x+23}" y="{y+80}" class="cs-gate-context">{e(context)}</text></g></a>'

    def edge(d, steps, kind='flow'):
        return f'<path class="cs-edge cs-{kind}" data-cs-edge="{steps}" d="{d}" marker-end="url(#cs-arrow)"/>'

    parts=['''<svg class="cs-diagram cs-decision-diagram" viewBox="0 0 1100 1370" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="cs-title cs-desc">
<title id="cs-title">同一杯咖啡：从用户委托，到执行步骤，再到模型与工具</title>
<desc id="cs-desc">用户请求C01先经S1交给Agent。Agent依据用户目标与预设流程或规划形成步骤图：查菜单和优惠，比较方案，确认授权，下单核验，返回回执。这些步骤就是原任务的子任务。满足依赖的步骤经S2获得执行名额，由Agent运行时程序发起模型或工具调用并记录结果；不是交给另一个Agent。模型调用经S3选择副本，再经S4组批；工具调用经S5排队获得额度。结果写回同一任务，推动后续步骤。金色表示调度选择，紫色表示任务规划。</desc>
<defs><pattern id="cs-grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="#5e9ca9" stroke-opacity=".09"/></pattern><marker id="cs-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse"><path d="M0 0L7 3.5L0 7" fill="none" stroke="#71bdcf" stroke-width="1.2"/></marker></defs>
<rect width="1100" height="1370" fill="url(#cs-grid)"/>
<text x="40" y="32" class="cs-label">01 / 用户只提一个目标：帮我点一杯咖啡</text>
<rect class="cs-agent" x="35" y="198" width="1030" height="650" rx="20"/>
<text x="57" y="230" class="cs-label">02 / 同一个 Agent 内部：先把目标变成步骤，再安排执行</text>
<text x="260" y="382" class="cs-annotation">C01 的执行计划 · 箭头表示“做下一步前，需要什么结果”</text>
<text x="57" y="598" class="cs-plan-bridge">这些步骤都属于同一杯咖啡；系统把每个可独立执行的步骤称为“子任务”。</text>
<text x="57" y="626" class="cs-annotation">计划给出要做什么 → 依赖、输入和权限满足 → 进入可执行集合 → S2 决定何时开始</text>
<text x="57" y="805" class="cs-runtime-definition">“执行器”就是运行步骤的程序组件：读取输入 → 发起调用 → 保存结果与状态。</text>
<text x="57" y="829" class="cs-annotation">它属于 Agent 运行时，不是新 Agent；状态更新后，调度器再检查哪些后续步骤可以开始。</text>
<rect class="cs-agent" x="35" y="898" width="658" height="300" rx="18"/>
<rect class="cs-agent" x="715" y="898" width="350" height="300" rx="18"/>
<text x="57" y="928" class="cs-label">03 / “比较方案”要调用模型来判断</text>
<text x="737" y="928" class="cs-label">04 / “查询、下单”要调用工具</text>
''']
    parts += [
        edge('M300 108H370','0'), edge('M690 108H770','0'), edge('M915 150V258','0 1'),
        edge('M190 350V390H45V535H60','1 2'), edge('M190 390V400','1 2'),
        edge('M265 439H295V485H330','2 3'), edge('M265 533H295V485H330','2 3'),
        edge('M530 485H580','3 4'), edge('M770 485H820','4 5'),
        edge('M1010 527V550H975','5 6'),
        edge('M1040 315H1053V642H205V658','2 3 5'),
        edge('M350 703H385','2 3 5'), edge('M705 703H765','2 3 5'),
        edge('M880 760V875H200V952','3','call'), edge('M930 760V952','2 5','call'),
        edge('M200 1054V1110','3'), edge('M530 1054V1110','3'), edge('M890 1054V1110','2 5'),
        edge('M330 1152H362V1003H395','3'),
        edge('M530 1260V1194','3','support'), edge('M890 1260V1194','2 5','support'),
        box(40,66,260,'用户委托 · C01',['“帮我点一杯咖啡”','本例已选门店，预算与口味已给定'],'0','request'),
        gate(370,57,320,'S1','agent','这杯咖啡交给哪个 Agent？','从能力、权限匹配的实例中选择','0'),
        box(770,66,290,'Agent 接手 C01',['持续负责同一项委托','保存用户要求、执行计划和进度'],'0','receipt'),
        box(60,258,980,'把“点咖啡”拆成可执行的步骤',['Agent 依据目标与预设流程或规划，组织下面的计划；这一步确定“做什么”，属于任务规划。','示例任务 C01 → 查菜单 / 查优惠 → 比较方案 → 确认授权 → 下单核验 → 返回回执'],'1','planning',92),
        box(60,400,205,'C01.1 查菜单',['获取商品、价格与库存'],'1 2'),
        box(60,494,205,'C01.2 查优惠',['获取这笔订单可用的优惠'],'1 2'),
        box(330,443,200,'C01.3 比较方案',['等两项查询返回','选出符合要求的方案'],'1 3'),
        box(580,443,190,'C01.4 确认授权',['检查预算与购买授权','需要时等待用户确认'],'1 4'),
        box(820,443,190,'C01.5 下单核验',['获授权后提交订单','检查订单与扣款结果'],'1 5'),
        box(60,658,290,'当前能做哪些步骤？',['尚未生成执行计划','先把整项委托交给 Agent'],'2 3 5',h=102).replace('尚未生成执行计划','<tspan data-cs-ready>尚未生成执行计划</tspan>').replace('先把整项委托交给 Agent','<tspan data-cs-wait>先把整项委托交给 Agent</tspan>'),
        gate(385,652,320,'S2','ready','先做哪步，哪些能同时做？','有限名额下，选择能开始的步骤','2 3 5'),
        box(765,658,275,'执行当前步骤',['Agent 运行时程序启动该步骤','需要判断就调模型，需要操作就调工具'],'2 3 5',h=102),
        gate(60,952,270,'S3','replica','交给哪个模型副本？','多个可用副本之间选择','3'),
        gate(395,952,275,'S4','batch','本轮处理哪些请求？','选定副本内，容量有限要组批','3'),
        gate(740,952,300,'S5','tool','哪些调用现在可以发出？','菜单、优惠、下单接口各有额度','2 5'),
        box(60,1110,270,'选定的模型副本',['本次“比较方案”的请求','进入这个副本的等待队列'],'3','service'),
        box(395,1110,275,'模型推理引擎',['把选中的请求组成计算批次','计算结果返回给 C01.3'],'3','service'),
        box(740,1110,300,'工具调用程序 → 商家 API',['携带步骤输入，查询或提交订单','把响应写回 C01 对应步骤'],'2 5','service'),
    ]
    parts += ['''<text x="685" y="576" class="cs-result-label" data-cs-node="6">C01 完成 → 用户收到可核验回执</text>
<text x="57" y="1230" class="cs-annotation">服务结果写回同一任务 C01 → 解锁后续步骤；全流程核验后才向用户报告完成。</text>
<rect class="cs-resource" x="35" y="1260" width="1030" height="86" rx="12"/>
<text x="56" y="1290" class="cs-label">05 / 底层支撑：服务使用已有资源，不是每点一杯就重新部署</text>
<text x="56" y="1324" class="cs-resource-text">模型计算：GPU / NPU · 显存</text><text x="640" y="1324" class="cs-resource-text">工具调用：CPU · 网络 · 外部 API 额度</text>
</svg>''']
    return ''.join(parts)
