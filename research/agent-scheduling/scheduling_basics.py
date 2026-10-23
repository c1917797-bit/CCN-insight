"""An explicit working definition and the object-resource-runtime control loop."""
from decision_map import BASE


def render_basics():
    return f'''<section id="scheduling-essence" class="scheduling-basics">
<p class="eyebrow">一句话理解调度</p><h2>把待办工作，安排给有限的执行资源</h2>
<p class="essence-definition">调度要决定：<strong>工作什么时候做、交给谁做、能用多少资源</strong>；执行中情况变化了，就重新调整安排。</p>
<div class="scheduling-glance"><a href="{BASE}#coffee-task"><span>看例子</span><strong>咖啡任务怎样完成</strong></a><a href="{BASE}#north-star"><span>定目标</span><strong>怎样才算完成得好</strong></a><a href="{BASE}#research-directions"><span>拆技术</span><strong>需要哪三类调度决策</strong></a></div>
<p class="essence-context"><strong>三个角色：</strong>规划确定“要做哪些步骤”；调度安排“这些步骤怎样执行”；运行时负责“执行并记录结果”。同一套Agent系统可以同时承担这些职责。</p>
<details class="scope-index"><summary>调度对象、调度资源与运行时的关系</summary><div class="essence-inputs"><article><span>输入一 / 调度对象</span><h3>待执行的工作</h3><p>用户任务、工作流子任务、模型请求、工具请求、部署作业。</p><small>携带依赖、状态、期限、优先级、资源需求和授权条件。</small></article><article><span>输入二 / 调度资源</span><h3>可用能力与容量</h3><p>可执行工作的Agent、模型与工具服务，以及其可用并发、CPU／GPU／NPU、内存和网络容量。</p><small>外部API额度是受限服务容量；硬件容量与服务额度不是同一种计量单位。</small></article></div>
<div class="essence-arrow" aria-hidden="true">↓</div><article class="essence-decision"><span>调度决策 / 把工作与资源联系起来</span><h3>何时执行 · 交给谁 · 用多少资源</h3><p>输出顺序、启动时机、执行归属和资源预算。依赖、权限与容量决定可行性，代价和服务目标决定如何取舍。</p></article>
<div class="essence-arrow" aria-hidden="true">↓</div><article class="essence-runtime"><span>运行时管理 / 执行安排并维护状态</span><h3>启动执行、记录进度、处理完成与异常</h3><p>运行时跟踪任务与调用状态，落实并发和资源限制；在具备相应能力时提供暂停、取消、检查点与恢复。观测到的耗时、容量和故障返回调度器，必要时触发重新调度。</p><a class="source-link" href="{BASE}runtime-rescheduling.html">查看运行反馈与恢复 →</a></article>
<p class="essence-feedback"><span aria-hidden="true">↺</span> 执行状态与资源变化 → 更新决策依据 → 必要时重新安排</p>
<div class="essence-boundary"><strong>对象、执行载体与资源，按所在层级区分。</strong><p>同一个Agent实例，接收用户任务时是执行载体；部署这个Agent服务时，待部署副本又成为调度对象。模型名称表示能力，模型服务副本承接请求，底层卡与内存提供容量，不能把这三者当作同一种资源。</p><p>任务规划产生或修改工作；调度安排工作如何执行；运行时管理落实安排并维护生命周期。它们在实现中可以位于同一个系统，但职责不同。运行时管理也不等于调度算法。</p></div>
<p class="note">本页采用面向Agent全流程的工作定义。工程参照：<a class="source-link" href="https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/" target="_blank" rel="noopener noreferrer">Kubernetes的Pod到节点调度</a>；<a class="source-link" href="https://docs.langchain.com/oss/python/langgraph/persistence" target="_blank" rel="noopener noreferrer">LangGraph的状态持久化与检查点</a>。两者分别说明位置决策与运行状态机制，不是统一Agent调度分类标准。</p>
</details></section>'''


def area_context(area_id):
    context={
        'workflow': ('有依赖的任务与子任务','可用执行名额及执行器能力','就绪任务顺序、并行推进与排程','节点完成、实际耗时及新生成的依赖'),
        'mapping': ('待分派请求或待部署服务','能力匹配的实例、节点及设备','请求归属或部署位置','实例负载、缓存状态及执行代价'),
        'sharing': ('竞争容量的任务或租户','计算、内存、并发及服务额度','资源份额、预算及并行度','实际消耗、等待情况及预算变化'),
    }[area_id]
    return '<div class="area-context"><a href="'+BASE+'#scheduling-essence">调度本质与概念关系 ↗</a><dl>'+''.join(f'<dt>{label}</dt><dd>{value}</dd>' for label,value in zip(('调度对象','调度资源','决策输出','运行反馈'),context))+'</dl></div>'
