"""Shared remit and classification boundaries, not a claimed industry standard."""
from decision_map import read

CONTEXT = read('report-context.csv')[0]
START, CUTOFF = CONTEXT['period_start'], CONTEXT['cutoff']


def remit():
    return f'''<aside class="report-remit" aria-label="研究范围与资料时点"><strong>本页要回答：有限资源下，怎样让Agent任务正确、按时、在预算内完成？</strong><p>研究任务进入系统后，从排队、分派到运行中调整的调度决策。任务规划提供待执行工作；模型质量和工具可靠性是约束，不能用调度替代。</p><p class="remit-meta">观察期 {START}—{CUTOFF} · 人工精选证据 · 尚无云核实测结论</p></aside>'''


def taxonomy():
    return '''<div class="taxonomy-contract"><h3>按“决策输出”分工，按“执行层”复用</h3><div class="table-scroll"><table><caption>三个主方向的边界；同一算法可联合优化多个输出</caption><thead><tr><th scope="col">主方向</th><th scope="col">输出什么</th><th scope="col">咖啡任务中的例子</th></tr></thead><tbody><tr><th scope="row">任务排程</th><td>就绪工作何时开始、先后次序</td><td>菜单与优惠可并行，比较方案等待两者返回</td></tr><tr><th scope="row">执行映射</th><td>工作交给哪个兼容实例或设备</td><td>模型调用交给哪个副本，部署时放在哪组卡</td></tr><tr><th scope="row">资源分配</th><td>任务或租户获得多少容量与份额</td><td>多人点单分别获得多少并发和工具额度</td></tr></tbody></table></div><p><strong>接纳是入口约束：</strong>决定接受、等待或拒绝；<strong>运行时是反馈闭环：</strong>记录执行状态并触发重新决策。二者贯穿三类输出，另设专题说明。</p><p class="note">这是便于组织研究的分解，不是“三类算法互斥”的承诺。例如HEFT同时涉及次序与映射，配额也会影响排队时间。Agent、模型、工具是应用层次，不再与算法方向并列。</p></div>'''
