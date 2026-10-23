"""A bounded, reproducible teaching example; not a live purchasing agent."""
import csv
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent
BASE = '/business_insight/cloud_core/agent_orchestration/'
WORKERS = ('A', 'B')

def inputs():
    tasks = {}
    with (ROOT/'coffee-tasks.csv').open(encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            tasks[r['task_id']] = {'title':r['title'], 'cost':{'A':float(r['executor_a']), 'B':float(r['executor_b'])}}
    edges = []
    with (ROOT/'coffee-dependencies.csv').open(encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f):
            edges.append((r['predecessor'],r['successor'],float(r['transfer'])))
    return tasks,edges

def schedule(tasks, edges, policy='HEFT'):
    if policy not in ('HEFT','FIFO'):raise ValueError('Unknown policy')
    predecessors={k:[] for k in tasks};successors={k:[] for k in tasks}
    for p,c,cost in edges:
        if p not in tasks or c not in tasks or cost<0:raise ValueError('Invalid edge')
        predecessors[c].append((p,cost));successors[p].append((c,cost))
    ranks={};visiting=set()
    def rank(k):
        if k in ranks:return ranks[k]
        if k in visiting:raise ValueError('A cycle cannot be scheduled as a DAG')
        visiting.add(k)
        ranks[k]=sum(tasks[k]['cost'].values())/len(WORKERS)+max((c+rank(n) for n,c in successors[k]),default=0)
        visiting.remove(k);return ranks[k]
    for k in tasks:rank(k)
    calendar={w:[] for w in WORKERS};placed={};trace=[]
    order=list(tasks)
    while len(placed)<len(tasks):
        ready=[k for k in tasks if k not in placed and all(p in placed for p,c in predecessors[k])]
        if not ready:raise ValueError('Unresolved dependency')
        k=min(ready,key=lambda x:(-ranks[x],order.index(x))) if policy=='HEFT' else min(ready,key=order.index)
        candidates=[]
        for worker in WORKERS:
            duration=tasks[k]['cost'][worker]
            if duration<=0:raise ValueError('Nonpositive cost')
            data_ready=max((placed[p]['end']+(0 if placed[p]['worker']==worker else comm) for p,comm in predecessors[k]),default=0)
            start=data_ready
            for left,right,_ in sorted(calendar[worker]):
                if start+duration<=left:break
                start=max(start,right)
            candidates.append({'worker':worker,'ready':data_ready,'start':start,'end':start+duration})
        winner=min(candidates,key=lambda r:(r['end'],WORKERS.index(r['worker'])))
        placed[k]={**winner,'task':k};calendar[winner['worker']].append((winner['start'],winner['end'],k))
        trace.append({'task':k,'ranks':ranks,'candidates':candidates,'winner':winner})
    return {'placed':placed,'calendar':calendar,'trace':trace,'rank':ranks,'finish':max(r['end'] for r in placed.values())}

def validate(tasks,edges,result):
    assert len(result['placed'])==len(tasks)
    for worker,slots in result['calendar'].items():
        for i,(start,end,key) in enumerate(sorted(slots)):
            assert end-start==tasks[key]['cost'][worker]
            if i:assert start>=sorted(slots)[i-1][1]
    for p,c,comm in edges:
        before,after=result['placed'][p],result['placed'][c]
        assert after['start']>=before['end']+(0 if before['worker']==after['worker'] else comm)

def number(x):return str(int(x)) if float(x).is_integer() else f'{x:g}'

def graph():
    places={'T1':(25,115),'T2':(205,25),'T3':(205,205),'T4':(385,115),'T5':(565,115),'T6':(745,115),'T7':(925,115)}
    tasks,edges=inputs();s=['<div class="diagram-scroll"><svg class="coffee-dag" viewBox="0 0 1090 305" role="img" aria-labelledby="coffee-dag-title coffee-dag-desc"><title id="coffee-dag-title">买咖啡任务依赖图</title><desc id="coffee-dag-desc">查询门店后可以分别查询菜单和优惠，两者完成后才能比较商品，再提交订单、确认支付并验收回执。排程前假设必要授权已具备；图不代表已经购买。</desc><defs><marker id="coffee-arrow" markerWidth="9" markerHeight="9" refX="7" refY="4.5" orient="auto"><path d="M0 0L9 4.5L0 9" fill="#9caabd"/></marker></defs>']
    for p,c,_ in edges:
        x,y=places[p];xx,yy=places[c]
        s.append(f'<path d="M{x+145} {y+34} C{x+164} {y+34},{xx-18} {yy+34},{xx} {yy+34}" fill="none" stroke="#9caabd" stroke-width="2" marker-end="url(#coffee-arrow)"/>')
    for key,(x,y) in places.items():
        s.append(f'<g><rect class="dag-box {"parallel-node" if key=="T3" else ""}" x="{x}" y="{y}" width="145" height="68" rx="13"/><text class="dag-id" x="{x+16}" y="{y+24}">{key}</text><text class="dag-label" x="{x+16}" y="{y+48}">{escape(tasks[key]["title"])}</text></g>')
    s.append('<text class="dag-note" x="205" y="188">两项只读查询可以并行</text></svg></div>');return ''.join(s)

def gantt(result,name):
    scale=43;left=80;s=[f'<svg class="coffee-gantt" viewBox="0 0 820 205" role="img" aria-label="{name}的教学排程，总时长{number(result["finish"])}个模拟单位">']
    for t in range(18):
        x=left+t*scale;s.append(f'<line x1="{x}" y1="38" x2="{x}" y2="167" class="gantt-grid"/><text x="{x}" y="190" text-anchor="middle" class="gantt-time">{t}</text>')
    for i,w in enumerate(WORKERS):
        y=55+i*66;s.append(f'<text x="12" y="{y+25}" class="gantt-worker">执行器{w}</text>')
        for start,end,key in sorted(result['calendar'][w]):
            x=left+start*scale;width=(end-start)*scale
            s.append(f'<rect x="{x}" y="{y}" width="{width}" height="41" rx="5" class="gantt-block {"gantt-parallel" if key=="T3" else ""}"/><text x="{x+width/2}" y="{y+27}" text-anchor="middle" class="gantt-task">{key}</text>')
    return '<div class="diagram-scroll">'+''.join(s)+'</svg></div>'

def render(shell):
    tasks,edges=inputs();heft=schedule(tasks,edges);fifo=schedule(tasks,edges,'FIFO')
    validate(tasks,edges,heft);validate(tasks,edges,fifo)
    assert heft['finish']==14 and fifo['finish']==16
    duration_rows=''.join(f'<tr><th scope="row">{k} · {escape(tasks[k]["title"])}</th><td>{number(tasks[k]["cost"]["A"])}</td><td>{number(tasks[k]["cost"]["B"])}</td><td>{number(heft["rank"][k])}</td></tr>' for k in ('T1','T2','T3','T4','T5','T6','T7'))
    plans=[]
    for name,result in [('HEFT',heft),('FIFO',fifo)]:
        steps=[]
        for i,step in enumerate(result['trace'],1):
            k=step['task'];w=step['winner'];rows=''.join(f'<tr><td>执行器{c["worker"]}</td><td>{number(c["ready"])}</td><td>{number(c["start"])}</td><td>{number(c["end"])}</td></tr>' for c in step['candidates'])
            reason='按upward rank选取尚未排程的任务；本步骤的前驱均已排定。' if name=='HEFT' else '按示例的就绪入队顺序选择；本步骤的前驱均已排定。'
            steps.append(f'<details class="card coffee-step"><summary><span>{i:02d}</span> {k} · {escape(tasks[k]["title"])} → 执行器{w["worker"]} · {number(w["start"])}–{number(w["end"])}</summary><p>{reason}比较数据就绪、空闲时间段与执行时长，选择预计结束最早的可行位置。</p><div class="table-scroll"><table><thead><tr><th>候选执行器</th><th>数据就绪</th><th>最早开始EST</th><th>最早结束EFT</th></tr></thead><tbody>{rows}</tbody></table></div></details>')
        plans.append(f'<div data-coffee-plan="{name}" {"hidden" if name=="FIFO" else ""}><h3>{name}排程 · {number(result["finish"])}个模拟时间单位</h3>{gantt(result,name)}<p class="note">T1查询门店；T2查询菜单；T3查询优惠；T4比较商品；T5提交订单；T6确认支付；T7验收回执。横轴为教学时间单位。</p><div class="coffee-steps">'+''.join(steps)+'</div></div>')
    body=f'''<header class="hero"><a class="back" href="{BASE}scheduling.html">← 返回资源调度专题</a><p class="eyebrow">云核 / Agent任务编排与调度 / 调度算法案例</p><span class="badge">HEFT原算法 · 咖啡流程教学建模</span><h1>买一杯咖啡，<br>怎样安排任务才更早完成？</h1><p class="lead">HEFT先估计哪些任务影响后续完成，再为每个任务选择预计最早结束的执行器。本页用可复算的例子说明它在工作流调度层做什么。</p><div class="hero-actions"><a class="button" href="#coffee-simulation">查看逐步排程</a><a class="button secondary" href="#coffee-sources">查看原始论文</a></div></header>
<section id="coffee-contract"><p class="eyebrow">01 / 任务约定</p><h2>先明确买咖啡任务的范围与完成条件</h2><article class="card"><p><strong>场景来自：</strong>你另一个《润色文件》对话中的“买咖啡”调度旅程。以下任务图依据可读取的文字流程重新建模，未取得该对话中的原始图片。</p><p><strong>本例完成标准：</strong>用户已明确商品与购买约束，并授权相应操作；Agent拿到有效订单和支付确认回执。若目标是“咖啡实际到手”，还需加入制作、取餐／配送与到手确认，不能用订单回执代替。</p><p><strong>教学假设：</strong>任务图已知；两台执行器均能运行这些任务，每台同时运行一个任务；不可抢占；依赖数据在同执行器传递为0，跨执行器为1个单位。所有耗时、队列顺序与15单位预算均为本页构造，不是你的原话、论文实验或真实采购数据。</p><p class="note">这是排程演示，不会调用门店、下单或支付接口。授权等待、真实制作与配送时间未纳入下面的数字。</p></article></section>
<section id="coffee-position"><p class="eyebrow">02 / 调度位置</p><h2>它安排的是工作流子任务，不包办整条调度链</h2><div class="mapping-callout"><span>调度源</span><strong>已知DAG中的待排程任务</strong><b>→</b><span>调度器</span><strong>HEFT排序与执行器选择</strong><b>→</b><span>目的地</span><strong>执行器A／B的执行计划</strong></div><p>先生成排程，运行时再按依赖与授权解锁任务；前驱“已排定”不代表它已真实执行完成。</p>{graph()}<div class="table-scroll"><table><thead><tr><th>原对话中的层次</th><th>咖啡例子的对象</th><th>HEFT在这里的关系</th></tr></thead><tbody><tr><th>① 接入路由</th><td>用户请求 → Agent实例</td><td>前置入口，不由本例HEFT实现。</td></tr><tr class="selected-row"><th>② 工作流任务调度</th><td>查门店、菜单、优惠、比较与订单步骤 → 执行器</td><td>本例介绍的算法位置；需要已知依赖和代价估计。</td></tr><tr><th>④-A 推理请求路由</th><td>比较商品所发出的模型请求 → 推理实例</td><td>独立下层决策，其等待代价可以影响节点耗时估计。</td></tr><tr><th>③ 推理批次调度</th><td>实例内的模型请求 → 本轮执行批次</td><td>独立下层决策，不等同工作流排程。</td></tr><tr><th>④-B 硬件放置</th><td>模型服务实例／作业 → GPU或NPU设备组</td><td>部署与扩容时决定；不能每个咖啡请求都重新部署模型。</td></tr><tr><th>⑤ 运行时重调度</th><td>受阻或失败任务 → 新的执行安排</td><td>原始静态HEFT未解决动态分支、故障与重试，需要另外设计。</td></tr><tr><th>⑥ 工具调用调度</th><td>API请求 → 可用工具执行器与并发名额</td><td>资源与限流约束；工具队列变化会使原排程失准。</td></tr></tbody></table></div></section>
<section id="coffee-principle"><p class="eyebrow">03 / 算法原理</p><h2>两步启发式：排任务，再找最早完成的位置</h2><div class="three-grid"><article class="card"><h3>01 估计后续重要性</h3><p>从图的出口反向计算upward rank：当前任务的平均执行代价，加上后继路径中最大的“传输代价＋后继rank”。它反映平均代价下的剩余路径长度，不是任务的业务价值分数。</p><code class="formula">rankᵤ(i) = w̄(i) + maxⱼ∈succ(i)[c̄(i,j) + rankᵤ(j)]</code></article><article class="card"><h3>02 比较最早结束</h3><p>按rank从高到低排程。对每个候选执行器，先满足前驱数据就绪，再找足够长的空闲时间段，计算EST与EFT。</p><code class="formula">EFT(i,p) = EST(i,p) + w(i,p)</code></article><article class="card"><h3>03 插入可行空档</h3><p>选择EFT最小的执行器与时间段，更新日历。插入式排程可以利用已有任务之间的空档，而不只把新任务追加到队尾。</p><p class="note">HEFT是启发式算法，不保证全局最优，也不直接提供截止时间保证。</p></article></div><p class="note">原算法来自Topcuoglu、Hariri和Wu发表于IEEE TPDS的2002年论文。下面把异构处理器抽象为两台可兼容的执行器，是教学映射。</p></section>
<section id="coffee-simulation"><p class="eyebrow">04 / 排程演示</p><h2>为什么先排菜单查询，能让后续更早解锁？</h2><p>示例中优惠查询先进入FIFO队列，但菜单查询的剩余路径估计更长。HEFT先把菜单放到A，再让优惠使用B；两条只读分支可以重叠。两种策略使用相同的EFT选址规则，区别仅在任务优先顺序。</p><div class="table-scroll"><table><thead><tr><th>任务</th><th>A执行代价</th><th>B执行代价</th><th>upward rank</th></tr></thead><tbody>{duration_rows}</tbody></table></div><div class="policy-controls" role="group" aria-label="选择演示排程策略"><button type="button" data-coffee-policy="HEFT" aria-pressed="true">HEFT：剩余路径优先</button><button type="button" data-coffee-policy="FIFO" aria-pressed="false">FIFO对照：先排优惠</button><span class="note">点击策略比较甘特图；展开每步查看两台执行器的EST／EFT。</span></div>{''.join(plans)}<article class="card simulation-result"><h3>本例排程结果：14与16，均为构造仿真</h3><p>HEFT得到14个模拟单位，FIFO＋相同EFT选址得到16。以本页设定的15单位数字链路预算看，前者满足、后者超出。这只解释本组输入，不证明HEFT普遍优于FIFO，也不能用于预测真实门店、模型服务或昇腾性能。</p></article></section>
<section id="coffee-implications"><p class="eyebrow">05 / 落地启示</p><h2>云核需要把任务依赖和资源代价放到同一份状态里</h2><div class="three-grid"><article class="card"><h3>不要只看空闲</h3><p>执行器空闲不等于该任务最快结束。需要计入任务自身耗时、前驱结果传递，以及执行器上已安排的工作。</p></article><article class="card"><h3>先保证估计可信</h3><p>采集每类任务的排队、工具等待、模型推理和状态传递代价。如果预测误差很大，先修观测与预测，再增加算法复杂度。</p></article><article class="card"><h3>动态流程单独处理</h3><p>Agent临时加分支、工具超时或任务重试后，旧DAG与代价会变化。重排程、风险预算和公平性属于进一步设计，不能宣称是原始HEFT已有能力。</p></article></div><article class="card"><h3>建议把HEFT作为可解释基线</h3><p>用同一工作流、执行器能力与代价输入，对比FIFO＋EFT、HEFT和可行的小规模最优解；观察任务完成时间、超预算比例与调度开销。真实系统另行记录任务质量、外部操作状态及重试副作用。任何下单／支付步骤都保留原有授权条件，不因优先级提高而跳过。</p><p class="note">以上为面向云核的分析建议，尚未在真实Agent任务或昇腾系统中验证。</p></article></section>
<section id="coffee-sources"><p class="eyebrow">06 / 来源依据</p><h2>原算法、私人场景与教学输入分别可追溯</h2><article class="card"><h3>原始论文</h3><p>H. Topcuoglu, S. Hariri, M.-Y. Wu. <em>Performance-Effective and Low-Complexity Task Scheduling for Heterogeneous Computing.</em> IEEE Transactions on Parallel and Distributed Systems, 13(3), 260–274, 2002. DOI: 10.1109/71.993206.</p><div class="hero-actions"><a class="button secondary" href="https://ieeexplore.ieee.org/document/993206/" target="_blank" rel="noopener noreferrer">IEEE原始论文 ↗</a><a class="button secondary" href="https://disco.ethz.ch/courses/fs14/seminar/paper/Jochen/4.pdf" target="_blank" rel="noopener noreferrer">论文PDF · ETH课程托管 ↗</a></div><p>已核对IEEE摘要中的upward rank优先、最早完成执行器选择与插入式排程。原论文的硬件实验不作为本页咖啡流程的效果证据。</p></article><article class="card"><h3>场景与可复算数据</h3><p>场景依据：你的《润色文件》对话中“六层调度的源、目的地及买咖啡映射”的可读取文字。菜单／优惠并行分支、两台执行器、代价矩阵与预算均为本页补充的教学假设。</p><p>本地模型：coffee-tasks.csv（逐任务代价）、coffee-dependencies.csv（依赖与跨执行器传输），由coffee_heft.py计算rank、空档、EFT、排程与甘特图。没有读取账号、地址、支付资料或发起真实购买。</p></article></section>'''
    html=shell('买咖啡的HEFT调度案例',body)
    html=html.replace(BASE+'scheduling.html',BASE+'workflow-scheduling.html').replace('← 返回资源调度专题','← 返回工作流任务调度专题')
    html=html.replace('以下任务图依据可读取的文字流程重新建模，未取得该对话中的原始图片。','任务图结合你提供的最新版调度全景图截图重新建模；并行分支和执行器代价属于教学假设。')
    html=html.replace('<span>调度源</span>', '<span>调度对象</span>').replace('<span>目的地</span>', '<span>执行载体</span>')
    html=html.replace('你的《润色文件》对话中“六层调度的源、目的地及买咖啡映射”的可读取文字。','你的《润色文件》咖啡场景及本次提供的最新版全景图截图。')
    html=html.replace('<section id="coffee-position">', f'<article class="case-entry"><h2>演示实例，可以扩展为多人并发</h2><p>单人咖啡讲清流程；多人同时点咖啡可以构造分流、排队与公平性测试，继续加入负载和故障条件可以研究资源压力与恢复。本页仍是一个任务的HEFT教学排程，不代表已经完成并发测试。</p><a class="source-link" href="{BASE}#demo-coverage">查看多人咖啡的调度覆盖方案 →</a></article><section id="coffee-position">',1)
    return html.replace('结构草稿 v0.1 · 2026-10-13 · 尚未接入TableGit，尚未采集研究证据','案例草稿 v0.2 · 2026-10-13 · 文献原算法／教学仿真分开 · 尚未接入TableGit')

if __name__=='__main__':
    tasks,edges=inputs()
    for policy in ('HEFT','FIFO'):
        r=schedule(tasks,edges,policy);validate(tasks,edges,r)
        print(policy,number(r['finish']),[(k,v['worker'],v['start'],v['end']) for k,v in r['placed'].items()])
