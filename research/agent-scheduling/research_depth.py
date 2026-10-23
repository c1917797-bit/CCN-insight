"""Explicit research contracts; proposals are separate from verified literature."""
from html import escape as e
from decision_map import read, BASE


def object_contract(point_id):
    """A schedulable input/output contract, not a claim about an implemented API."""
    r=next(r for r in read('object-research-contracts.csv') if r['point_id']==point_id)
    return '<article class="research-spec object-spec"><h3>调度接口：何时触发，读什么，交付什么</h3><dl>'+''.join(
        f'<dt>{label}</dt><dd>{e(r[key])}</dd>' for label,key in [('触发时机','trigger'),('可观测输入','inputs'),('可执行输出','outputs')])+'</dl></article>'


def object_evaluation(point_id):
    r=next(r for r in read('object-research-contracts.csv') if r['point_id']==point_id)
    return '<article class="research-spec"><h3>最小可判定实验</h3><dl>'+''.join(
        f'<dt>{label}</dt><dd>{e(r[key])}</dd>' for label,key in [('比较基线','baseline'),('压力与反例','stress'),('采纳条件','decision_rule')])+'</dl><p class="note">以上是实验设计，尚未执行。固定原始任务到达、模型质量和总资源；拒绝、超时与失败保留在统计中，避免通过少接任务制造局部低延迟。</p></article>'


def object_evidence(point_id):
    r=next(r for r in read('object-research-contracts.csv') if r['point_id']==point_id)
    return f'<article class="research-spec"><span class="evidence-label">已核对的工程机制 · 2026-10-23</span><p>{e(r["evidence_fact"])}</p><a class="source-link" href="{e(r["source_url"])}" target="_blank" rel="noopener noreferrer">{e(r["source_label"])} · 官方原文 ↗</a><p class="note">核对文档中的机制与职责边界；未运行目标框架，也未确认所有机制均已适配昇腾。实验设计不视为来源框架的既有能力。</p></article>'


def mechanism_figure(area):
    """Decision semantics as a vector diagram; all labels are research design."""
    specs={
        'workflow': [('观测依赖','当前已知节点','完成状态与代价'),('筛选就绪','前驱与授权满足','容量允许启动'),('比较次序','FIFO／程序进度','关键路径作对照'),('更新状态','启动节点并计量','完成后解锁后继')],
        'mapping': [('接收工作','质量与能力要求','负载与状态快照'),('筛选候选','先满足硬约束','剔除不兼容位置'),('比较代价','排队＋执行','状态与传输成本'),('绑定并校准','输出模型／副本','用实测修正估计')],
        'sharing': [('计量服务','租户权重与消耗','资源与干扰画像'),('形成可行集','容量与服务下限','可执行的隔离接口'),('分配预算','服务份额／并发','容量另设慢周期'),('核验保障','等待、成本与慢化','越界回退或隔离')],
    }
    colors={'workflow':'#1b7f79','mapping':'#3265a8','sharing':'#7350a2'}
    nodes=specs[area]
    color=colors[area]
    blocks=[]
    for i,(title,line1,line2) in enumerate(nodes):
        x=12+i*228
        blocks.append(f'<rect x="{x}" y="18" width="204" height="130" rx="16" fill="#f7fafc" stroke="{color}" stroke-width="1.5"/><text x="{x+18}" y="50" fill="{color}" font-size="17" font-weight="700">0{i+1} / {title}</text><text x="{x+18}" y="85" fill="#163047" font-size="16">{line1}</text><text x="{x+18}" y="113" fill="#526477" font-size="15">{line2}</text>')
        if i<3:
            blocks.append(f'<path d="M{x+208} 83 H{x+222} m-6 -5 6 5 -6 5" fill="none" stroke="{color}" stroke-width="2"/>')
    return '<figure class="research-mechanism"><div class="table-scroll"><svg viewBox="0 0 912 174" width="100%" role="img" aria-label="观测、合法性筛选、调度决策与运行反馈的四步机制"><g font-family="system-ui, Microsoft YaHei, sans-serif">'+''.join(blocks)+'</g></svg></div><figcaption>机制示意 / 先保证动作合法，再比较收益；本图描述研究接口，未表示已有性能结果。</figcaption></figure>'


def problem_contract(area):
    r=next(r for r in read('research-depth-model.csv') if r['area_id']==area)
    fields=[('决策变量','variable'),('触发时机','trigger'),('可行条件','feasible'),('优化目标','objective'),('首轮控制变量','excluded')]
    return mechanism_figure(area)+'<article class="research-spec"><span class="eyebrow">研究定义 / 本报告的实验建模</span><h3>明确算法能改什么，不能改什么</h3><dl>'+''.join(f'<dt>{label}</dt><dd>{e(r[key])}</dd>' for label,key in fields)+'</dl><p class="note">在线输入只含决策时已知的信息。尚未生成的分支、未来到达与真实完成时间不可泄漏给在线策略；使用未来信息的离线解只作参照，未经证明不称上界或下界。</p></article>'


def model_overview():
    return '''<article class="research-spec" id="research-formulation"><span class="eyebrow">共同问题 / 有约束的在线决策</span><h3>面对不断到达的任务，决定何时做、由谁做、给多少资源</h3><p>给定当前可见的任务依赖、服务状态和资源容量，调度策略持续产生合法动作；用达标完成的整任务评价收益。任务规划提供待执行步骤，运行时执行动作并反馈结果。</p><div class="research-chain"><span>观测<br><b>已知任务与资源状态</b></span><i>→</i><span>决策<br><b>次序 · 绑定 · 份额</b></span><i>→</i><span>反馈<br><b>完成 · 等待 · 成本</b></span></div><p class="note">三个方向按决策输出区分，联合优化时会耦合。先固定其余两类变量研究单项因果，再检验联合收益；不把三类算法的收益简单相加。</p></article>'''


def algorithm_contract(area):
    r=next(r for r in read('research-method-contracts.csv') if r['area_id']==area)
    mechanism=''
    if area=='workflow':
        mechanism='''<aside class="route-audit"><span class="evidence-label">原文机制 / Agentix §4.2.1</span><p><strong>PLAS：p(新调用) = 同一程序此前已完成调用的执行时间之和。</strong>数值越小，优先级越高；用已经获得的服务量区分程序，而非预测未来调用总数。</p><p>并行程序另用 ATLAS：维护最长已观测累计服务链的估计，并处理并行调用的推进。它不是“剩余路径越长就越先执行”的静态关键路径策略。</p><a href="https://www.usenix.org/system/files/nsdi26-luo.pdf#page=8" target="_blank" rel="noopener noreferrer">核对原文公式与伪代码 ↗</a><small> · 2026-10-15 核对；论文实现还含优先级离散化与抢占机制。</small></aside>'''
    return f'''<article class="research-spec algorithm-spec"><span class="eyebrow">算法研究 / 可实现的首轮方案</span><h3>{e(r['title'])}</h3>{mechanism}<p><strong>对照方法：</strong>{e(r['baseline'])}</p><ol class="algorithm-steps">{''.join(f'<li>{e(r[k])}</li>' for k in ('step1','step2','step3','step4'))}</ol><dl><dt>开销怎么查</dt><dd>{e(r['overhead'])}</dd><dt>何时会失效</dt><dd>{e(r['failure'])}</dd></dl><p class="note">上述步骤是本报告的实验设计，不是原论文逐行复现。方法依据：<a href="{e(r['source_url'])}" target="_blank" rel="noopener noreferrer">{e(r['source_label'])} ↗</a>。</p></article>'''


def route_audit(route_id):
    r=next(r for r in read('route-evidence-audit.csv') if r['route_id']==route_id)
    return f'''<div class="route-audit"><span class="evidence-label">{e(r['status'])}</span><p><strong>证据支持：</strong>{e(r['support'])}</p><p><strong>尚未证明：</strong>{e(r['gap'])}</p><small>核对范围：{e(r['scope'])} · {e(r['checked'])}</small></div>'''


def experiment_card(area):
    r=next(r for r in read('research-hypotheses.csv') if r['area_id']==area)
    fields=[('实验负载','workload'),('控制变量','controls'),('强对照组','baseline'),('干预变量','intervention'),('消融实验','ablation'),('观测指标','measure'),('否证与不确定性','reject'),('沉淀资产','artifact')]
    return f'''<article class="research-spec experiment-spec" id="experiment-{e(r['id'])}"><span class="eyebrow">{e(r['id'])} / 可检验的研究假设 · 尚未执行</span><h3>{e(r['question'])}</h3><dl>{''.join(f'<dt>{label}</dt><dd>{e(r[key])}</dd>' for label,key in fields)}</dl><a class="source-link" href="{BASE}#evaluation-protocol">统一实验协议与判定规则 →</a></article>'''


def evaluation_protocol():
    return '''<article class="research-spec" id="evaluation-protocol"><span class="eyebrow">实验协议 / 立项前冻结，运行后可复查</span><h3>如何证明是调度方法有效，而不是实验条件变了</h3><ol class="algorithm-steps"><li><b>先冻结验收。</b>记录任务成功判据、质量下限、期限、租户权重和成本边界。确定最小有意义收益 δ 与允许退化 ε；当前没有基线数据，二者均待评审确定。</li><li><b>再做配对比较。</b>同一到达轨迹、模型版本和资源预算运行各策略；建议至少 5 次独立重复并交错运行顺序，实际次数由方差决定。校准与测试负载分离，按完整工作流留出测试集。</li><li><b>分开回放与实跑。</b>固定 token／工具结果的因果回放用于隔离调度效应；后继请求须等待前驱实际完成后释放。它不能验证策略改变回答后的业务质量，需追加真实模型与工具沙箱闭环。</li><li><b>报告不确定性。</b>报告每次结果、配对差异及 95% 置信区间；任务有相关性时按运行或时间块重采样，不能把每个 token 当独立样本。区间过宽意味着证据不足。</li><li><b>满足护栏再谈领先。</b>收益置信区间下界超过预先约定的 δ，且各租户质量、尾延迟与失败率满足护栏，才进入下一阶段。报告最差负载和退化案例；小规模离线求解只作参照。</li></ol><p class="note">以上是建议实验协议，不是现有实验结果。实验日志只保留必要的匿名任务标识、耗时和资源统计；公开报告不发布用户内容、凭据或工具密钥。</p></article>'''


def research_agenda():
    names={'workflow':'依赖感知排程','mapping':'状态感知映射','sharing':'干扰感知分配'}
    cards=''.join(f'''<article class="agenda-item"><span class="eyebrow">{e(r['hypothesis'])} / {names[r['area_id']]}</span><h4>进入条件：{e(r['signal'])}</h4><dl><dt>先研究什么</dt><dd>{e(r['first_test'])}</dd><dt>何时继续</dt><dd>{e(r['decision'])}</dd><dt>暂缓什么</dt><dd>{e(r['defer'])}</dd></dl><a href="{BASE}research-{r['area_id']}.html#experiment-{r['hypothesis']}">打开假设、对照与消融 →</a></article>''' for r in read('research-agenda.csv'))
    return '<div class="research-agenda" id="research-agenda"><span class="eyebrow">研究取舍 / 用瓶颈证据决定优先级</span><h3>三个候选课题，先选择有真实瓶颈的一项</h3><p>现有文献说明这些方法值得验证，尚不能决定云核哪项收益最大。先采集同一批任务的等待归因，再选择下列入口；首个课题通过后才研究耦合。</p>'+cards+'</div>'
