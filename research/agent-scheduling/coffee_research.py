"""A teaching case that connects the shared outcome to three scheduling decisions."""
from decision_map import BASE, read
from html import escape as e


CASES = {
    'workflow': ('什么时候做', '已确定门店且两项查询互不依赖时，菜单与优惠可并行；比较方案要等查询完成，下单要等方案与授权。', '依赖满足后进入候选队列，再决定谁先开始、谁能并行。关键路径是影响整单完成时间的最长依赖链。', '减少关键路径上的等待，有望让更多任务按时完成。'),
    'mapping': ('交给谁执行', '任务先交给可用Agent；模型调用选择兼容副本；工具调用选择有权限的执行器。', '先筛选能力与权限，再比较排队、执行和传输代价；扩容时另做设备放置。', '执行与排队代价降低 → 更容易同时满足时限和成本。'),
    'sharing': ('分配多少资源', '多人同时点咖啡，共享模型容量、内存及查询／下单API额度。', '按资源需求与服务权重分配并发和预算，控制过载，避免长任务或小租户持续饥饿。', '拥塞与饥饿减少 → 在固定容量下保障更多用户达标完成。'),
}


def case_detail(area_id):
    question, example, action, effect = CASES[area_id]
    return f'<div class="coffee-decision"><span>咖啡案例 / {question}</span><p>{example}</p><dl><dt>调度动作</dt><dd>{action}</dd><dt>目标贡献</dt><dd>{effect}</dd></dl></div>'


def metric_contribution(area_id):
    return f'<p class="metric-contribution"><strong>对共同目标的贡献：</strong>{CASES[area_id][3]} <a href="{BASE}#north-star">查看北极星指标与统计口径 →</a></p>'


def render_case():
    from coffee_scene import render
    return render()


def metric_reference():
    rows=''.join('<tr><th scope="row">'+e(r['metric'])+'</th><td>'+e(r['unit'])+'</td><td>'+e(r['purpose'])+'</td><td>'+e(r['guardrail'])+'</td></tr>' for r in read('metric-definitions.csv'))
    return '<details class="scope-index"><summary>指标怎样分工：结果、护栏与诊断</summary><div class="table-scroll"><table><caption>本研究的建议计量口径，尚未接入实测</caption><thead><tr><th scope="col">指标</th><th scope="col">单位</th><th scope="col">回答的问题</th><th scope="col">使用边界</th></tr></thead><tbody>'+rows+'</tbody></table></div></details>'


def render_metric():
    return '''<section id="north-star" class="north-star"><p class="eyebrow">02 / 再明确什么叫做得好</p><h2>共同目标：让更多任务正确、按时、在预算内完成</h2><p class="metric-lead">北极星指标，也就是所有调度优化共同服务的首要结果：<strong>端到端任务达标完成率</strong>。</p>
<div class="metric-formula"><strong>达标完成率</strong><span aria-hidden="true">＝</span><div><span>同时满足质量、时限与成本要求的任务数</span><span>同一统计范围内全部有效任务数</span></div><span>× 100%</span></div><p class="metric-example"><strong>算例，不是实测：</strong>100个有效点单请求，90个同时达标，完成率就是90%。超时、超预算和容量不足被拒绝的请求，都不能算达标。</p>
<div class="metric-conditions"><article><b>结果正确</b><p>口味、价格等要求满足，订单及回执可核验，没有重复下单或扣款。</p></article><article><b>按时完成</b><p>从首次提交到结果返回，包含排队、重试与外部等待。</p></article><article><b>成本可控</b><p>模型、计算与工具调用总成本不超预算，计入失败尝试；咖啡价格另属业务约束。</p></article></div>
<p class="metric-status">当前为指标设计，尚未接入实测。具体时限、预算和目标值需结合业务要求确定。</p>
<details class="scope-index"><summary>统计口径与评价护栏</summary><ul>
<li>按首次提交时间选择任务批次，待该批次所有任务的约定评估期限届满后计算；未到期任务单列，不能只统计已完成任务。</li>
<li>容量不足或过载而拒绝的有效任务仍计入分母。无效请求、范围外任务及取消的处理规则事先约定并单列数量，禁止事后挑选样本。</li>
<li>一个原始任务只计一次，重试沿用任务标识。权限与质量要求是硬约束，不能靠降低验收标准提高完成率。</li>
<li>P95完成时延统计成功任务从首次提交到可核验结果的耗时，包含排队、模型与工具调用、重试及外部等待；它不代表所有请求的延迟，必须同时展示超时率和失败率。</li><li>达标吞吐按固定观察窗口内达标完成数除以窗口秒数计算，并注明窗口长度与到达负载。单位达标成本包含同批次全部任务的失败与重试成本；达标数为零时标记不可计算。</li><li>比较策略时固定任务类型、到达负载、模型质量与资源预算；分租户和任务难度报告结果，同时观察尾延迟、拒绝率、最长等待、单位达标成本及达标吞吐。</li>
<li>咖啡演示的终点是有效订单回执。若承诺“咖啡送达”，必须增加交付确认，并将交付耗时计入端到端指标。等待用户确认的时间单独归因，不能静默扣除。</li>
</ul></details><p class="note">参考<a class="source-link" href="https://sre.google/workbook/implementing-slos/" target="_blank" rel="noopener noreferrer">Google SRE的良好事件／全部事件指标方法</a>，结合本研究的任务验收要求设计；不是行业统一的Agent指标标准。</p>'''+metric_reference()+'</section>'
