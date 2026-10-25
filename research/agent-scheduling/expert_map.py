"""Reading order: definition, concrete example, research questions, mechanisms and evidence."""
from html import escape as e
from decision_map import BASE, read, render_decisions
from architect_view import architecture_overview
from scheduling_basics import render_basics
from team_strategy import metrics
from coffee_research import render_case
from architecture_map import model, coverage


ENTRIES = {
    'workflow': {
        'focus': '减少整任务的关键等待',
        'challenge': '模型队列只看单次请求，容易忽略它对整项任务进度的影响；局部调用变快，任务未必更早完成。',
        'decision': '在已知依赖和就绪条件下，决定哪些步骤先运行、何时启动、哪些可以并行。',
        'routes': '就绪列表与关键路径 → 程序级服务量排序 → 动态反馈与学习辅助',
        'evidence': [('agentix', 'Agentix · 程序级调度'), ('production-trace', '生产工作流轨迹 · 负载依据')],
        'fixed': '执行位置、服务容量与任务质量要求',
        'measure': '整任务累计排队、尾部完成时延；同时检查长任务与低优先级租户是否退化。',
    },
    'mapping': {
        'focus': '把工作交给合适的位置',
        'challenge': '缓存命中可能节省计算，也可能把请求集中到热点；最少在途数不等于最短剩余工作量。',
        'decision': '在能力与权限满足的候选中选择模型、副本或设备；请求路由与部署放置分别建模。',
        'routes': '负载与代价感知路由 → 约束筛选与放置评分 → 匹配与联合优化',
        'evidence': [('llmd-routing', 'llm-d · 推理请求路由'), ('llmd-flow', 'llm-d · Flow 调度')],
        'fixed': '先固定模型、精度、副本池及批次策略，再比较路由；选模型和部署放置另设实验。',
        'measure': '缓存节省与排队、传输代价的净变化；检查状态过期与路由自身开销。',
    },
    'sharing': {
        'focus': '让有限资源支撑服务保障',
        'challenge': '按请求数均分不能反映实际服务成本；显存装得下也不能证明多个模型共卡运行达标。',
        'decision': '决定任务或租户获得多少执行额度、资源份额与服务容量，并根据干扰调整。',
        'routes': '服务成本计量与公平分配 → 共卡干扰与配置优化 → 容量预测与弹性控制',
        'evidence': [('justitia', 'Justitia · 服务公平'), ('murakkab', 'Murakkab · 资源编排与弹性')],
        'fixed': '任务到达轨迹、设备预算与服务保障；共卡实验另设独占对照。',
        'measure': '总体与分租户达标吞吐、共卡慢化、单位达标成本；包含失败和重配置开销。',
    },
}


def _directory():
    areas = read('research-areas.csv')
    items = []
    for i, area in enumerate(areas, 1):
        a = ENTRIES[area['id']]
        evidence = ' · '.join(f'<a href="{BASE}#publication-{key}">{e(label)}</a>' for key, label in a['evidence'])
        items.append(f'''<article class="research-entry"><div class="entry-heading"><span class="number">0{i}</span><h3><a href="{BASE}research-{area['id']}.html">{e(area['title'])} →</a></h3><p>{e(a['focus'])}</p></div><dl><dt>关键问题</dt><dd>{e(a['challenge'])}</dd><dt>调度决策</dt><dd>{e(a['decision'])}</dd><dt>候选路线</dt><dd>{e(a['routes'])}</dd><dt>代表资料</dt><dd>{evidence}</dd></dl></article>''')
    return '<section id="research-directions" class="research-story"><h2>三项研究方向，分别改变一种主要决策</h2><p>每个专题按研究问题、技术机制、原始依据、路线比较和研究建议展开。以下是团队的研究组织方式，边界由决策变量划分。</p><div class="research-directory">'+''.join(items)+'</div></section>'


def _comparison():
    rows = ''.join(f'<tr><th scope="row"><a href="{BASE}research-{a["id"]}.html">{e(a["title"])}</a></th><td>{e(ENTRIES[a["id"]]["fixed"])}</td><td>{e(ENTRIES[a["id"]]["measure"])}</td></tr>' for a in read('research-areas.csv'))
    return f'''<section id="research-comparison"><h2>先隔离变量，再研究跨层协同</h2><p>排程、映射和分配会相互影响。首轮实验固定其他决策，识别单项机制的净收益；有了稳定基线，再比较联合策略。</p><div class="route-comparison" tabindex="0" role="region" aria-label="三项调度研究方向比较，可横向滚动"><table><caption>研究比较口径 · 尚非实测结果</caption><thead><tr><th scope="col">研究方向</th><th scope="col">首先固定什么</th><th scope="col">观察什么收益与代价</th></tr></thead><tbody>{rows}</tbody></table></div><p class="note">三项技术不等于完整 Agent 产品。规划、授权、幂等与业务结果核验提供输入或约束；调度负责在这些约束内安排执行。</p></section>'''


def _legacy_points():
    points, algorithms = model()
    items = []
    for p in points:
        names = '、'.join(algorithms[k]['name'] for k in p['algorithms'].split('|'))
        items.append(f'<article id="point-{p["id"]}"><h4><a href="{BASE}{p["topic"]}.html">{e(p["title"])} →</a></h4><p><strong>决策：</strong>{e(p["decision"])}</p><p><strong>候选方法：</strong>{e(names)}</p><p class="note">{e(p["boundary"])}</p></article>')
    return '<details class="map-reference"><summary>按执行层查找调度方法</summary><div class="map-reference-body">'+''.join(items)+'</div></details>'


def render():
    return f'''{render_basics()}
<details id="demo-section" class="map-reference" open><summary>咖啡样例 · 从完整工作流理解调度位置</summary><div class="map-reference-body" id="agent-demo">{render_case()}{_legacy_points()}<details class="map-reference"><summary>演示边界 · 单人、并发与故障分别覆盖什么</summary>{coverage()}</details></div></details>
<div id="scheduling-decisions" class="research-overview"><p class="eyebrow">从样例到研究 / 问题 → 机制 → 证据 → 取舍</p><h2>从任务瓶颈，定位三项调度研究</h2><p>咖啡样例展示了任务如何经过 Agent、模型与工具服务，最终使用设备资源。下面把其中的调度问题归为三项研究：工作<strong>何时执行、交给谁执行、获得多少资源</strong>。三项研究共同服务于整任务的完成效果。</p><div class="map-objective"><strong>共同目标：提高端到端任务有效吞吐</strong><span>固定资源预算和任务分布，统计单位时间内质量、时限与成本同时达标的完成任务数。<a href="#north-star">查看完整口径 →</a></span></div></div>
{_directory()}{_comparison()}
<section id="research-reading"><h2>沿着一个具体问题，读透一份代表研究</h2><article class="reading-entry"><span>重点深读 · 历史论文</span><h3>Murakkab：多模型工作流怎样减少资源需求？</h3><p>从任务分解、模型放置和弹性机制读起，再核对 Figure 6、Table 2 的比较条件。区分论文测量、作者解释与面向云核的研究判断。</p><a class="source-link" href="{BASE}reading-murakkab.html">阅读机制、原图与证据边界 →</a></article></section>
<details class="map-reference"><summary>系统边界 · 任务、Agent、服务与设备如何关联</summary><div class="map-reference-body">{architecture_overview()}</div></details>
<details class="map-reference"><summary>评价口径 · 怎样判断调度真正有效</summary><div class="map-reference-body">{metrics()}</div></details>
<details class="map-reference"><summary>共用基础 · 观测、决策、反馈与恢复</summary><div class="map-reference-body" id="runtime-loop"><h2>用同一条任务轨迹连接三项研究</h2><p>统一 task_id 与依赖事件，记录就绪、排队、执行和结果核验时间；将模型状态、工具额度与卡资源分开计量。决策后写回状态、校准代价估计，并记录失败与恢复成本。</p><p>这些是后续算法复用的工程基础。目前页面提供研究设计与教学演示，尚未接入真实运行时。</p><a class="source-link" href="{BASE}runtime-rescheduling.html">阅读运行反馈与恢复专题 →</a></div></details>
<details id="scope-index" class="map-reference"><summary>应用索引 · 按执行对象与决策查找</summary><div class="map-reference-body"><p>以下是三项研究的应用索引；执行层和决策类型分别组织，不增加新的根技术。</p>{render_decisions()}</div></details>'''
