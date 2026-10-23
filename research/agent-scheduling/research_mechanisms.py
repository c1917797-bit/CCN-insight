"""Concrete, reproducible teaching models for the three root research topics.

The examples are explanatory constructions, not measurements or reproductions
of any paper.  Figures retain their own readable canvas on narrow screens.
"""
from html import escape as e
from decision_map import read


INK = '#17334a'
MUTED = '#536b7d'
TEAL = '#087f78'
BLUE = '#315c93'
AMBER = '#986007'
RED = '#ad2948'


def _text(x, y, value, size=18, fill=INK, weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}">{e(value)}</text>'


def _box(x, y, w, h, fill='#f3f7fa', stroke='#bacbd6', radius=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'


def _edge(d, area, color=TEAL, dashed=False):
    dash = ' stroke-dasharray="6 5"' if dashed else ''
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5"{dash} marker-end="url(#mechanism-arrow-{area})"/>'


def _figure(area, title, description, content, height, caption):
    return f'''<figure class="research-mechanism mechanism-example"><div class="table-scroll mechanism-canvas" tabindex="0" role="region" aria-label="{e(title)}，窄屏可横向查看"><svg class="mechanism-svg" viewBox="0 0 1120 {height}" width="100%" style="min-width:900px;display:block" role="img" aria-labelledby="mechanism-title-{area} mechanism-desc-{area}"><title id="mechanism-title-{area}">{e(title)}</title><desc id="mechanism-desc-{area}">{e(description)}</desc><defs><marker id="mechanism-arrow-{area}" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="context-stroke"/></marker></defs><rect width="1120" height="{height}" rx="18" fill="#fcfefe"/><g font-family="system-ui, Microsoft YaHei, sans-serif">{content}</g></svg></div><figcaption>{e(caption)}</figcaption></figure>'''


def _bar(x, y, width, label, color, height=32):
    return _box(x, y, width, height, color, color, 5) + _text(x + 10, y + 22, label, 17, '#ffffff', 650)


def _workflow_figure():
    s = _text(28, 36, '先区分依赖，再安排就绪工作', 23, INK, 750)
    s += _text(28, 65, 't₀ 已知图：A、B、X 均就绪；C 等待 A 与 B。时间单位 u 为教学假设。', 18, MUTED)
    s += _box(28, 86, 660, 254, '#f5fbfa', '#b7d9d5')
    s += _text(46, 117, '点单任务 C01：从查询推进到方案可用', 18, TEAL, 700)
    for x, y, title, sub in [(48, 139, 'A / 查菜单', '工具 · 4 u'), (48, 242, 'B / 查优惠', '工具 · 2 u'), (410, 190, 'C / 比较方案', '模型 · 2 u')]:
        s += _box(x, y, 220, 76, '#ffffff', '#6caaa4')
        s += _text(x + 16, y + 30, title, 20, TEAL, 700) + _text(x + 16, y + 57, sub, 17, MUTED)
    s += _edge('M268 177 H335 V214 H408', 'workflow')
    s += _edge('M268 280 H335 V242 H408', 'workflow')
    s += _text(290, 165, '结果依赖', 16, MUTED)
    s += _box(724, 86, 368, 254, '#f8f9fc', '#c6d0df')
    s += _text(744, 117, '另一任务 C02', 18, BLUE, 700)
    s += _box(744, 150, 328, 80, '#ffffff', '#8da6c4')
    s += _text(762, 183, 'X / 查询 · 工具 · 4 u', 20, BLUE, 700)
    s += _text(744, 270, 'X 与 A、B 没有依赖边，', 17, MUTED)
    s += _text(744, 299, '但竞争同一个查询执行名额。', 17, MUTED)
    s += _text(28, 374, '资源约束：工具名额 1 个；模型另有 1 个名额。C 可与 X 并行。', 18, INK, 650)
    left, scale = 260, 65
    for t in range(13):
        x = left + scale * t
        s += f'<path d="M{x} 411 V663" stroke="#e1e9ee"/>'
        s += _text(x - 5, 404, str(t), 16, MUTED)
    s += _text(28, 435, '对照 / FIFO', 19, BLUE, 750)
    s += _text(28, 464, '工具队列 A → X → B', 16, MUTED)
    s += _text(143, 493, '模型执行', 16, MUTED)
    for start, length, label, color in [(0, 4, 'A', TEAL), (4, 4, 'X', BLUE), (8, 2, 'B', TEAL)]:
        s += _bar(left + start * scale, 430, length * scale, label, color)
    s += _bar(left + 10 * scale, 478, 2 * scale, 'C', AMBER)
    s += _text(28, 570, '候选 / 先释放汇合', 19, TEAL, 750)
    s += _text(28, 599, '工具队列 A → B → X', 16, MUTED)
    s += _text(143, 648, '模型执行', 16, MUTED)
    for start, length, label, color in [(0, 4, 'A', TEAL), (4, 2, 'B', TEAL), (6, 4, 'X', BLUE)]:
        s += _bar(left + start * scale, 585, length * scale, label, color)
    s += _bar(left + 6 * scale, 633, 2 * scale, 'C', AMBER)
    s += _text(28, 704, 'C01 方案可用：12 → 8 u；代价是 C02 的 X 完成：8 → 10 u。', 20, INK, 700)
    return _figure('workflow', '真实依赖图与两种就绪次序的可复算时间线', 'A和B并列，均指向C；X属于另一任务。单工具名额下，FIFO次序A、X、B使C在12完成；次序A、B、X使C在8完成，但X从8延后到10。模型与工具使用不同名额。', s, 740,
                   '解释性重绘 · 全部耗时为构造假设，且本例假设估计与实际一致；只截取查询到方案可用的一段，不等于整单完成。箭头表示结果依赖，时间条表示资源占用。')


def _mapping_figure():
    s = _text(28, 36, '缓存命中值得保留，热点排队也必须付账', 23, INK, 750)
    s += _text(28, 66, '固定模型与质量；同一时刻的状态快照。所有时长为教学假设。', 18, MUTED)
    s += _box(28, 169, 216, 118, '#f2f8fb', '#97b8ce')
    s += _text(45, 204, '一个模型调用', 21, BLUE, 700)
    s += _text(45, 236, '同一模型 M', 18, MUTED)
    s += _text(45, 266, '先筛权限与兼容性', 17, MUTED)
    for y, color, dash in [(133, '#a8bac7', False), (266, TEAL, False), (393, '#a8bac7', True)]:
        s += _edge(f'M244 228 H285 V{y} H330', 'mapping', color, dash)
    configs = [(92, 'R1 / 有前缀缓存', '排队 9 u · 未缓存 prefill 1 u', False),
               (225, 'R2 / 无前缀缓存', '排队 1 u · 未缓存 prefill 5 u', True),
               (353, 'R3 / 不在授权域', '硬约束不满足，先剔除', False)]
    for y, title, sub, selected in configs:
        s += _box(332, y, 352, 88, '#e8f7f2' if selected else '#f7f9fb', TEAL if selected else '#c4d0da')
        s += _text(350, y + 32, title, 20, TEAL if selected else INK, 700)
        s += _text(350, y + 63, sub, 17, MUTED)
    for y, q, p in [(108, 9, 1), (241, 1, 5)]:
        x, unit = 730, 27
        s += _bar(x, y, q * unit, f'{q}', BLUE)
        s += _bar(x + q * unit, y, p * unit, f'{p}', TEAL)
    s += _text(730, 169, '9 + 1 + 0.2 = 10.2 u', 19, INK, 650)
    s += _text(730, 302, '1 + 5 + 0.2 = 6.2 u', 19, TEAL, 750)
    s += _text(730, 382, '不参与代价排名', 20, MUTED, 650)
    s += _text(730, 412, '可行性先于效率', 18, MUTED)
    s += _text(28, 489, '深蓝：预计排队  ·  青绿：未缓存 prefill  ·  另计公共路由开销 0.2 u', 18, MUTED)
    s += _box(28, 514, 1064, 107, '#edf7f4', '#9dc8bb')
    s += _text(48, 547, '动作：本次绑定 R2，更新其在途工作量；不迁移模型，不改变批次策略。', 19, TEAL, 700)
    s += _text(48, 578, '回执：记录真实排队、TTFT 与缓存节省，校准下一次估计。', 18, INK)
    s += _text(48, 605, 'R1 多等 8 u，只少算 4 u；本次退出亲和，但不永久放弃缓存。', 18, MUTED)
    return _figure('mapping', '硬约束筛选与缓存排队净代价比较', '固定模型M，R1有缓存但排队9单位、执行1单位，R2无缓存但排队1单位、执行5单位。加公共路由开销0.2后分别为10.2和6.2。R3权限不匹配被排除。本次选择R2并反馈真实结果。', s, 648,
                   '解释性重绘 · 预计首 token 等待 = 排队 + 未缓存 prefill + 状态/传输 + 路由开销。本例状态/传输项设为 0，实际系统必须单列；未将这组假设称作 llm-d 或昇腾的实验结果。')


def _sharing_figure():
    s = _text(28, 36, '显存装得下，不代表可以同时跑', 23, INK, 750)
    s += _text(28, 67, '假设：卡容量 24 GiB；在线 A 占 12，后台 B 占 8。两项工作在 t₀ 均未启动。', 18, MUTED)
    s += _box(28, 89, 1064, 98, '#f7f9fb', '#b9cbd6')
    s += _bar(48, 110, 492, 'A 驻留 · 12 GiB', BLUE, 42)
    s += _bar(540, 110, 328, 'B 驻留 · 8 GiB', TEAL, 42)
    s += _box(868, 110, 164, 42, '#e5ebef', '#d4dfe5', 5)
    s += _text(881, 138, '空余 4 GiB', 18, MUTED, 650)
    s += _text(48, 174, '驻留状态不变；本例只改变“是否允许 B 进入执行”，不增加卡数。', 17, MUTED)
    left, scale = 282, 230
    for t in [0, 1, 2, 3]:
        x = left + scale * t
        s += f'<path d="M{x} 219 V527" stroke="#e1e9ee"/>'
        s += _text(x - 5, 216, f'{t} u', 16, MUTED)
    s += _text(28, 249, '对照 / 同时执行', 20, BLUE, 750)
    s += _text(28, 280, '假设共卡剖面', 17, MUTED)
    s += _text(210, 270, 'A', 18, BLUE, 700)
    s += _text(210, 323, 'B', 18, TEAL, 700)
    s += _bar(left, 246, 1.8 * scale, 'A · 1.8 u', BLUE)
    s += _bar(left, 299, 2.2 * scale, 'B · 2.2 u', TEAL)
    s += _text(28, 423, '候选 / 暂缓启动 B', 20, TEAL, 750)
    s += _text(28, 454, '先保护 A 的关键阶段', 17, MUTED)
    s += _text(210, 444, 'A', 18, BLUE, 700)
    s += _text(210, 497, 'B', 18, TEAL, 700)
    s += _bar(left, 420, scale, 'A · 1 u', BLUE)
    s += _bar(left + scale, 473, 2 * scale, 'B · 2 u', TEAL)
    deadline = left + 1.5 * scale
    for y in [238, 412]:
        s += f'<path d="M{deadline} {y} V{y+50}" stroke="{RED}" stroke-width="2" stroke-dasharray="5 4"/>'
    s += _text(deadline + 8, 365, 'A 的时限：1.5 u', 18, RED, 700)
    s += _box(28, 550, 1064, 115, '#f6f7fb', '#c6c9dd')
    s += _text(48, 582, '假设 B 时限为 3.5 u：暂缓启动后，两项均达标；B 完成从 2.2 延后到 3 u。', 19, INK, 700)
    s += _text(48, 613, '输出：本轮并发额度 (A=1, B=0)；A 完成后释放额度并启动 B。', 18, TEAL)
    s += _text(48, 642, '这是启动前的额度决策，不是对正在执行的模型实施任意时刻抢占。', 17, MUTED)
    return _figure('sharing', '驻留容量与执行干扰分开判断的预算实例', '24GiB卡上A占12GiB、B占8GiB。假设隔离耗时A为1、B为2，共卡耗时A为1.8、B为2.2。A时限1.5、B时限3.5。暂缓未启动B，A先运行到1，B再运行到3，保护A但延迟B。', s, 690,
                   '解释性重绘 · 所有容量、耗时与时限均为教学构造；共卡剖面并非实测。显存占用只证明容量可行，条带只说明此例的执行时间，不表示真实卡利用率或吞吐提升。')


SPECS = {
    'workflow': {
        'title': '同样三个就绪节点，次序为何会改变整项任务的等待？',
        'lead': '以点单中的查询与比较为例，先由依赖产生合法就绪集合，再决定有限名额先给谁。调度器不创造业务步骤，也不能越过尚未返回的查询。',
        'steps': [
            ('输入与可行动作', 't₀ 可见 A、B、X；C 的两个前驱尚未完成。工具只有一个执行名额，模型有独立名额；调度动作仅改变 A、B、X 的启动次序。'),
            ('逐步推演', 'FIFO 先做 A、X、B，C 到 10 u 才就绪；把 B 移到 X 前，C 在 6 u 解锁并与 X 并行，方案在 8 u 可用。A、B 内部谁先做在这个特例中不影响汇合时间。'),
            ('反向核查', 'C01 这段链路提前 4 u，但 X 延后 2 u。若另一任务的期限不允许延后，候选次序就不可采纳；不能只汇报受益任务。'),
        ],
        'failure': '本例依赖图固定、耗时估计准确且执行不可抢占。真实 Agent 的新分支、循环、用户授权、工具限流与预测误差都可能改变就绪集合。保持模型和映射不变，先比较 FIFO，再增加程序进度或路径信息；不能把该例当作 HEFT、PLAS 或全局最优性的证明。',
        'bridge': '列表调度与 HEFT 提供依赖和代价建模参照；Agentix 的程序服务量排序是另一条机制，使用已获得的服务，而不是本例“先释放汇合”的规则。后文按原文分别比较。',
        'links': [('list', '就绪列表'), ('critical', '路径与异构排程'), ('adaptive', '动态更新')],
        'figure': _workflow_figure,
    },
    'mapping': {
        'title': '有缓存的副本为什么仍可能更慢？',
        'lead': '先固定所选模型与回答质量，再在相同模型的可行副本中比较剩余工作量和状态代价。设备放置属于另一个较慢周期，不能混进一次请求路由的收益。',
        'steps': [
            ('输入与候选', '同一快照含副本的权限、兼容性、预计排队、未缓存输入量和状态位置。R3 被硬约束剔除；缓存不能抵消权限或模型版本不匹配。'),
            ('逐步推演', 'R1 的前缀少算 4 u，却比 R2 多等 8 u。公共路由开销相同、状态代价为零时，R2 的预计首 token 等待短 4 u；据此本次退出缓存亲和。'),
            ('动作后的状态', '只向 R2 绑定新增请求，并立即更新其在途工作；真实排队与 TTFT 回来后校准预测。下一次必须重新比较，不能把一次选择固化成永久绑定。'),
        ],
        'failure': '静态在途数不是剩余工作量。快照过期、突发到达、缓存驱逐、远端 KV 传输和路由开销都会使估计失真；首 token 变快也不保证整任务更快。首轮固定批次和部署，在冷暖缓存、热点与状态延迟下对照轮询、最少在途和纯亲和。',
        'bridge': '本例用于解释 llm-d 的缓存亲和与饱和退出为什么要同时看负载；不是复现其 token-aware 评分公式。Kubernetes 的可行筛选与评分用于放置参照，不能据此推导副本路由的最优性。',
        'links': [('cost', '负载与代价分派'), ('placement', '约束放置'), ('flow', '匹配与联合优化')],
        'figure': _mapping_figure,
    },
    'sharing': {
        'title': '两模型能共卡，为什么还要控制谁先进入执行？',
        'lead': '驻留容量、执行干扰和服务份额是三本账。先确保模型放得下，再用隔离与共卡剖面判断并发是否可行，最后在服务护栏内分配额度；不能把显存利用率当成算力收益。',
        'steps': [
            ('输入与约束', 'A、B 已驻留且均未启动。观测显存容量、隔离/共卡耗时剖面、各自时限和已消费服务；本例固定放置，只比较是否同时放行。'),
            ('逐步推演', '同时启动能容纳 20 GiB 驻留，却使 A 的假设耗时从 1 增到 1.8 u，超过 1.5 u 时限。暂缓 B 启动可保护 A，随后 B 到 3 u 完成，仍满足其 3.5 u 时限。'),
            ('代价与账本', 'B 的完成延迟增加 0.8 u，必须记入其等待和服务账本。若 B 的服务下限或时限不允许等待，应换隔离配置或拒绝该并发组合，不能靠一直饿住 B 达标。'),
        ],
        'failure': '共卡慢化取决于模型、阶段、输入和并发，单一画像不能覆盖所有负载。若运行时不能安全控制额度，或 B 已运行而不可抢占，本例动作不可直接执行。服务成本公平另以固定总资源比较；不能把这个干扰例子说成 DRF/VTC 的公平性证明。',
        'bridge': 'DRF 与 VTC 分别提供资源份额和服务成本计量参照；AlpaServe、Murakkab 提供共享配置与跨层安排的研究背景。它们并不自动证明本文的干扰画像、并发额度或昇腾实现已经成立。',
        'links': [('quota', '配额与并发'), ('service', '服务成本公平'), ('interference', '共卡干扰'), ('elastic', '弹性容量')],
        'figure': _sharing_figure,
    },
}


def mechanism_walkthrough(area_id):
    """A concrete mechanism with observable inputs, legal actions and tradeoffs."""
    r = SPECS[area_id]
    steps = ''.join(f'<li><strong>{e(title)}</strong><p>{e(text)}</p></li>' for title, text in r['steps'])
    links = ''.join(f'<a href="#route-{e(key)}">{e(label)} →</a>' for key, label in r['links'])
    return f'''<article class="mechanism-walkthrough" id="mechanism-{e(area_id)}"><p class="eyebrow">机制推演 / 构造实例，不是性能实验</p><h3>{e(r['title'])}</h3><p class="mechanism-lead">{e(r['lead'])}</p>{r['figure']()}<ol class="mechanism-trace">{steps}</ol><aside class="mechanism-limit"><h4>这个例子何时不成立</h4><p>{e(r['failure'])}</p></aside><p class="mechanism-evidence-bridge">{e(r['bridge'])}</p><nav class="mechanism-route-links" aria-label="本例对应的研究路线">{links}</nav></article>'''


def decision_scope(area_id):
    """Keep the existing normalized contract without repeating the old four-box figure."""
    r = next(r for r in read('research-depth-model.csv') if r['area_id'] == area_id)
    fields = [('决策变量', 'variable'), ('触发时机', 'trigger'), ('可行条件', 'feasible'), ('优化目标', 'objective'), ('控制变量', 'excluded')]
    values = ''.join(f'<dt>{label}</dt><dd>{e(r[key])}</dd>' for label, key in fields)
    return f'''<details class="scope-index mechanism-scope"><summary>研究边界：变量、动作与不变条件</summary><dl class="structured-list">{values}</dl><p class="note">在线策略只读取当时已知状态；未来分支、未来到达和真实完成时间不能泄漏给它。以下教学例子为了解释机制，单独列出了构造假设。</p></details>'''
