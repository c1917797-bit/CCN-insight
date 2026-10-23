"""Team research strategy, kept separate from publication facts and demo behavior."""
from html import escape as e
from decision_map import read, BASE


def capabilities():
    rows=read('team-capabilities.csv')
    assert {r['area_id'] for r in rows}=={'workflow','mapping','sharing'}
    return rows


def pyramid():
    from research_depth import model_overview
    questions={'workflow':('什么时候做？','两个查询都已就绪，只有一个名额：先查菜单，还是先查优惠？'), 'mapping':('交给谁执行？','比较方案要调用模型：选择哪个符合质量要求的模型及其副本？'), 'sharing':('分到多少资源？','多人同时点单：每项任务能占几个名额，共卡模型各用多少预算？')}
    cards=''.join(f'''<a class="team-core" href="{BASE}research-{r['area_id']}.html"><span>核心技术 / 0{i}</span><h3>{e(r['title'])}</h3><p>{questions[r['area_id']][0]}</p><small>{e(r['decision'])}</small><div class="core-example"><span>放到咖啡任务里</span>{questions[r['area_id']][1]}</div><b>进入专题：问题 → 方法 → 证据 →</b></a>''' for i,r in enumerate(capabilities(),1))
    return f'''<div class="team-pyramid" id="team-strategy"><div class="team-target"><span>共同目标 · 研究定位</span><h2>同质量、同资源，让更多 Agent 任务按时完成</h2><p>以端到端任务有效吞吐衡量收益；质量、期限和成本共同定义“达标”，租户公平与长任务等待作为护栏。</p></div><svg class="team-connectors" viewBox="0 0 900 48" aria-hidden="true"><path d="M450 0 V16 M150 44 V16 H750 V44 M450 16 V44" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="150" cy="44" r="4"/><circle cx="450" cy="44" r="4"/><circle cx="750" cy="44" r="4"/></svg><div class="team-grid">{cards}</div><aside class="decision-boundary"><strong>怎样区分，又怎样配合？</strong><p><b>排程</b>在给定名额内决定启动哪些就绪步骤；<b>映射</b>确定这些工作由谁执行；<b>分配</b>调整可用名额、份额或容量。它们可以联合求解，不要求系统总按这个顺序运行。</p><p>例如：允许两项查询并行，是排程选择；提高可用并发额度，是分配选择。提高额度只有在底层有余量时才可能有效。</p></aside>{model_overview()}<div class="team-foundation"><strong>一个共用研究底座</strong><span>可回放的任务与评测</span><span>统一状态与代价模型</span><span>可插拔调度运行时</span></div><p class="team-boundary">三项方向按决策输出划分：启动时机与顺序、执行位置、资源份额。算法可跨方向联合求解；这是团队研究框架，文献中的具体方法与适用条件在各专题展开。</p></div>'''


def methods(area):
    from reader_learning import worked_example
    from research_depth import algorithm_contract
    r=next(r for r in capabilities() if r['area_id']==area)
    fields=[('算法输入','inputs'),('决策输出','outputs'),('规则与启发式','heuristic'),('优化求解','optimization'),('学习辅助','learning'),('必须计入的代价','cost')]
    return '<details class="scope-index"><summary>展开算法选型：基线、优化求解与学习增强</summary><article class="team-methods"><h3>同一问题，多种求解路线</h3><dl>'+''.join(f'<dt>{label}</dt><dd>{e(r[k])}</dd>' for label,k in fields)+'</dl><p class="note">先用可解释基线验证瓶颈与收益，再比较优化求解和学习增强；选择取决于状态是否可观测、动作是否可执行，以及在线开销能否回收。Agent 扩展为本报告研究设计。</p></article></details>'


def contract(area):
    r=next(r for r in capabilities() if r['area_id']==area)
    return f'''<article class="team-contract"><span class="eyebrow">待检验假设 / 团队构筑</span><h3>{e(r['hypothesis'])}</h3><dl><dt>对照基线</dt><dd>{e(r['baseline'])}</dd><dt>可复用资产</dt><dd>{e(r['asset'])}</dd><dt>继续投入条件</dt><dd>{e(r['acceptance'])}</dd><dt>调整或停止条件</dt><dd>{e(r['stop'])}</dd><dt>执行链位置</dt><dd>{e(r['gates'])} · <a href="{BASE}#coffee-task">在咖啡任务中定位 →</a></dd></dl><p class="note">当前产物：待实验的研究方案。下一阶段应交付真实接口、可回放轨迹、设备配置和对照结果。</p></article>'''


def portfolio():
    from research_depth import evaluation_protocol
    cards=''.join(f'''<article class="team-stage"><span>阶段 0{i}</span><h3>{e(r['title'])}</h3><p>{e(r['work'])}</p><dl><dt>阶段产出</dt><dd>{e(r['deliverable'])}</dd><dt>进入下一阶段</dt><dd>{e(r['gate'])}</dd></dl></article>''' for i,r in enumerate(read('team-milestones.csv'),1))
    return f'''<div id="analysis-team" class="team-plan"><p class="eyebrow">团队研究规划 / 基于证据的建议</p><h3>先得到可复现的单项净收益，再验证联合优化增量</h3><p>建议先在固定模型与副本池上复现程序级排程；随后由等待归因决定是否加入缓存映射或成本公平。跨层方案与单项策略组合比较，只有额外收益覆盖观测、求解和重配置成本时继续扩展。研发节奏与目标值在基线测量后确定。</p><div class="team-grid">{cards}</div><div class="team-assets"><h3>每项研究都形成模型、算法、系统与证据四类资产</h3><p><b>模型</b>：可校准的时间、状态与干扰代价。<b>算法</b>：策略、复杂度与退化边界。<b>系统</b>：接口、反馈、回退与配置。<b>证据</b>：轨迹、强基线、消融实验与失败案例。</p><p>课题评审必须回答：优化哪个可观测瓶颈？与何种强基线比较？收益在哪些负载条件成立？失败后如何退回可用策略？</p></div><div class="table-scroll"><table><caption>竞争力验收设计 · 目标值须在基线测量后确定</caption><thead><tr><th>评价维度</th><th>比较方法</th><th>禁止混淆</th></tr></thead><tbody><tr><th>效果</th><td>固定质量、资源与到达负载，比较任务有效吞吐和 P95／P99</td><td>Token 吞吐、缓存命中率改善不等于任务收益</td></tr><tr><th>开销</th><td>计入预测、求解、状态采集、迁移和重配置耗时</td><td>离线最优解不等于在线可执行策略</td></tr><tr><th>稳健性</th><td>测试负载突发、预测误差、缓存冷热、异构资源与故障</td><td>均值改善不能掩盖饥饿、拒绝或尾延迟退化</td></tr><tr><th>可复用性</th><td>使用留出的工作流与模型测试，报告迁移后的校准成本</td><td>单一咖啡演示不等于真实业务覆盖</td></tr></tbody></table></div>{evaluation_protocol()}</div>'''


def evidence_index():
    links=read('research-publication-links.csv')
    cards=''.join(f'<a href="{BASE}research-{r["area_id"]}.html#evidence"><strong>{e(r["title"])}</strong><span>{len({l["publication_id"] for l in links if l["area_id"]==r["area_id"]})} 项关联资料 · {e(r["decision"])}</span></a>' for r in capabilities())
    return '<div class="team-evidence-index"><p><strong>按核心技术读动态：</strong>同一资料可以支撑多个方向。按决策输出定位路线，区分算法证据、工程实现、负载观察与评测方法；同一条证据只计一次。</p><div class="team-grid">'+cards+'</div></div>'


def metrics():
    return '''<section id="north-star" class="north-star"><p class="eyebrow">共同尺度 / 固定条件下比较</p><h2>主指标：端到端任务有效吞吐</h2><p class="metric-lead">观察窗口内，同时满足质量、时限与成本要求的完成任务数 ÷ 窗口秒数。用于衡量固定资源下系统交付有效任务的能力。</p><div class="team-grid"><article class="team-stage"><span>质量与成功</span><h3>任务达标完成率</h3><p>同一到达批次中达标任务数 ÷ 全部有效任务数。容量拒绝、超时、失败不能静默删除。</p></article><article class="team-stage"><span>体验与公平</span><h3>尾延迟与最长等待</h3><p>报告成功任务的 P95／P99，同时报告超时、失败与拒绝率；按租户和难度分组。</p></article><article class="team-stage"><span>资源与代价</span><h3>单位达标任务成本</h3><p>同批次全部尝试成本 ÷ 达标任务数，包含失败、重试、迁移与调度开销；分母为零时不可计算。</p></article></div><details class="scope-index"><summary>统计口径与实验边界</summary><ul><li>吞吐按完成时间计入固定窗口，注明预热、排空和窗口长度；完成率按到达批次等到评估期限届满后计算，两者分母不同。</li><li>固定模型质量、资源预算、任务组合和到达负载，并扫描多个负载水平。需求不足时吞吐受需求限制，不能据此宣称系统容量领先。</li><li>一个原始任务只计一次。取消与无效请求的规则事先确定；计入被容量拒绝的有效任务，防止挑选容易任务。</li><li>咖啡案例以核验订单回执为终点，不代表已送达。工具和用户等待保留在端到端时间中并单独归因。</li><li>当前无云核实测数据，不预设领先百分比；业务 SLO 与公平下限需在实验前约定。</li></ul></details><p class="note">指标口径为本报告研究建议。<a href="https://www.usenix.org/conference/osdi24/presentation/zhong-yinmin" target="_blank" rel="noopener noreferrer">DistServe</a>提供模型服务 goodput 的研究参照；这里扩展到任务验收，不直接套用其请求级结果。</p></section>'''
