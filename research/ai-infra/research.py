# -*- coding: utf-8 -*-
"""Curated research routes. Sources support mechanisms, not local device results."""
from html import escape as e

S={
'mlperf':('MLPerf Inference · 测试规则与工作负载','https://mlcommons.org/benchmarks/inference-datacenter/'),
'prof':('昇腾 msprof · 性能分析工具','https://github.com/Ascend/msprof'),
'mig':('NVIDIA MIG · 资源分区原理','https://docs.nvidia.com/datacenter/tesla/mig-user-guide/introduction.html'),
'prefix':('vLLM · Automatic Prefix Caching','https://docs.vllm.ai/en/latest/features/automatic_prefix_caching/'),
'spec':('Fast Inference from Transformers via Speculative Decoding','https://arxiv.org/abs/2211.17192'),
'sparse':('Deja Vu · Contextual Sparsity','https://arxiv.org/abs/2310.17157'),
'flash':('FlashAttention · IO-aware Exact Attention','https://arxiv.org/abs/2205.14135'),
'comm':('NCCL · 集合通信语义','https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html'),
'kueue':('Kueue · Resource Flavor','https://kueue.sigs.k8s.io/docs/concepts/resource_flavor/'),
'parallel':('PyTorch · 分布式技术总览','https://docs.pytorch.org/tutorials/beginner/dist_overview.html'),
'mega':('Megatron-LM · 模型并行','https://arxiv.org/abs/1909.08053'),
'tune':('vLLM · Optimization and Tuning','https://docs.vllm.ai/en/latest/configuration/optimization/'),
'dist':('DistServe · Prefill/Decode 分离','https://arxiv.org/abs/2401.09670'),
'ascend':('vLLM-Ascend · 官方实现','https://github.com/vllm-project/vllm-ascend'),
'release':('vLLM-Ascend · 版本说明','https://docs.vllm.ai/projects/ascend/en/latest/user_guide/release_notes.html'),
'slim':('msModelSlim · 官方压缩工具','https://github.com/Ascend/msModelSlim'),
'awq':('AWQ · 感知激活的权重量化','https://arxiv.org/abs/2306.00978'),
'prune':('SparseGPT · 一次性权重剪枝','https://arxiv.org/abs/2301.00774'),
'kd':('MiniLLM · 知识蒸馏','https://arxiv.org/abs/2306.08543'),
'svd':('SVD-LLM · 截断感知低秩分解','https://arxiv.org/abs/2403.07378')
}
# Route: name, challenge, mechanism, expected benefit/condition, source id.
R={
'硬件/模型性能评测':[
('受约束吞吐评测','吞吐高但响应超时，无法直接说明业务可用。','固定模型、数据集、精度和到达轨迹，在质量及延迟约束下寻找可承载的最大负载。','产出达标吞吐曲线；不能混用离线吞吐和在线请求吞吐。','mlperf'),
('执行时间线归因','端到端变慢，却不知道是计算、搬运还是等待。','从主机到设备对齐算子、拷贝和通信事件，定位关键路径与空闲区间。','先解释耗时最多的阶段，再选择优化；采集开销须与非采集运行分开。','prof'),
('并行扩展评测','加卡后吞吐上升，但单卡效率可能下降。','保持模型和精度不变，比较各并行配置的通信与执行时间。','区分容量刚需与性能扩展；不要用不同模型的结果推导扩展率。','parallel')],
'硬件增强':[
('存储容量与带宽匹配','模型能装下，并不表示读取权重足够快。','将常驻权重、KV 和工作区容量，与运行时字节搬运量分开建模；再用性能轨迹验证瓶颈。','容量决定能否运行，带宽影响访存阶段；提高算力峰值不能自动解决访存瓶颈。','prof'),
('计算与片上复用匹配','运算单元等待数据，理论算力无法利用。','利用片上存储反复使用数据块，减少访问外部内存；FlashAttention 提供软硬件协同例证。','采购与配置要看可用带宽、片上资源和实际算子，而不只看算力标签。','flash'),
('互连与拓扑匹配','跨卡数据交换占用关键路径。','按实际集合通信流量规划同机和跨机放置，再测不同消息大小的通信耗时。','先比较现有拓扑上的时间曲线；更高速互连的收益取决于通信占比。','comm')],
'虚拟化复用':[
('空间分区','小模型不能吃满一张卡，又需要隔离。','把物理资源划为独立实例；MIG 展示了硬件分区这一实现方式。','以部分容量换隔离和并行服务；MIG 的机制不能直接当作昇腾支持证据。','mig'),
('队列与配额复用','多个任务同时申请同一资源池。','通过资源类型、配额和准入控制分配运行机会，避免超额申请。','适合资源池治理；配额本身不提供设备内部的性能隔离。','kueue'),
('共享部署干扰评测','共卡吞吐提高但一个业务尾时延恶化。','逐步增加共卡负载，测各业务执行、排队和内存峰值。','只有每个业务都满足约束时才接受共卡；不能只报告汇总吞吐。','prof')],
'缓存代计算':[
('跨请求前缀缓存','相同长前缀被重复预填充。','按一致的 token 前缀复用已计算 KV，新请求只计算未命中的后缀。','主要减少重复 prefill，不能据此声称每个 decode token 都变快。','prefix'),
('缓存容量管理','缓存占满内存后，复用收益被驱逐抵消。','将命中收益与可用 KV 空间一起调节，观察高负载下驱逐和重计算。','命中率要与 TTFT、内存和达标吞吐同时报告。','tune'),
('前缀亲和路由','缓存分散在不同实例，请求被发到冷实例。','优先选择持有匹配前缀的实例，同时限制排队等待；这是基于缓存机制的系统设计建议。','当命中节省时间超过额外排队时才值得保留亲和。','prefix')],
'数据稀疏化':[
('上下文相关稀疏','每次都计算所有头和 MLP 单元。','Deja Vu 按输入上下文预测活跃部分，并配合稀疏执行跳过其余计算。','关键是预测成本和执行核共同成立；论文模型上的收益不能直接迁移。','sparse'),
('静态权重稀疏','参数矩阵中可删除部分仍参与计算。','SparseGPT 以层重构控制删权重后的误差；与推理压缩专题衔接。','若运行时仍调用稠密矩阵乘，零值更多并不会自动加速。','prune'),
('稀疏执行开销核算','索引、聚集和负载不均吞掉省下的运算。','对选择器、数据重排、稀疏核分别计时，再比较完整层的执行时间。','先验证目标 shape 上有净收益，再扩展到全模型。','prof')],
'迭代次数压缩':[
('草稿模型推测解码','自回归逐 token 串行执行成本高。','小模型产生多个候选，大模型批量验证；正确的接受与重采样规则保持目标分布。','收益取决于接受长度、草稿成本和验证效率，不能只看草稿准确率。','spec'),
('候选长度调优','候选太长浪费验证，太短收益有限。','在同一采样配置下扫描候选数，统计每轮接受 token 数与整轮耗时。','比较每个最终输出 token 的成本；低并发有效不代表高并发也有效。','spec'),
('运行时适配','论文算法可行，但具体推理栈缺少执行支持。','核对 vLLM-Ascend 对目标模型、版本和推测方法的支持，再选择可运行配置。','不以框架存在该功能推导全部昇腾设备均可用。','release')],
'计算算子加速':[
('Attention IO 优化','完整中间注意力矩阵带来大量搬运。','FlashAttention 用分块和在线 softmax 在片上推进计算，避免完整中间矩阵落外存。','数学上仍是精确注意力；这是访存优化，不是稀疏注意力。','flash'),
('融合与形状专门化','大量小算子启动、布局转换和中间写回占时。','依据热点形状合并相邻操作，并比较融合核与原执行图。','收益应覆盖真实 shape 分布；边界 shape 回退要单独记录。','prof'),
('低比特执行衔接','模型文件变小，但解包反量化开销过高。','核对量化格式与执行核，将压缩表示接入实际推理路径。','必须证明调用了目标内核；权重压缩率不能代替端到端加速。','ascend')],
'通信算子加速':[
('集合通信匹配','计算分片需要不同的数据汇集方式。','AllReduce 汇总并复制结果，AllGather 拼接分片，ReduceScatter 汇总后分发分片。','先确认计算需要的语义，再优化实现；不能为速度随意替换语义。','comm'),
('消息粒度与拓扑','小消息启动成本高，大消息受带宽约束。','按真实消息大小采样耗时，比较合并消息和不同设备放置。','避免只用大消息带宽评价逐层小消息通信。','comm'),
('计算通信重叠','串行等待让通信直接进入关键路径。','将没有数据依赖的计算与通信并发，检查时间线是否真正重叠。','异步接口不等于已隐藏开销；并发也可能争用带宽。','prof')],
'异构资源调度':[
('能力约束放置','不同设备不一定支持同一模型与精度路径。','用资源类型和节点约束描述设备能力，再过滤不可执行组合。','先保证可运行；不能将 310P、910B、950 按卡数等价处理。','kueue'),
('性能画像路由','可执行设备之间仍有明显速度差异。','测模型在各设备的排队与执行代价，按预计完成时间选择资源。','这是基于性能画像的设计建议；迁移与加载时间必须纳入代价。','prof'),
('容量与配额治理','低优先级任务挤占关键服务资源。','按业务池设置资源配额和准入条件，保留关键负载容量。','Kueue 提供资源准入机制参考，并非 LLM token 级调度器。','kueue')],
'单模型实例多卡调度':[
('张量并行 TP','单层矩阵容量或计算量超过单卡能力。','把同一层矩阵分块到多卡，按切分方式交换或归约中间结果。','可能减少单卡工作量，但引入逐层通信；Megatron 原文以训练为主，推理需另测。','mega'),
('流水线并行 PP','整个模型不能放入单卡。','将连续层分配到不同设备，用微批填充各阶段。','减少每卡驻留层数，但气泡和阶段不均衡会影响时延。','parallel'),
('并行配置协同','TP/PP 组合在不同负载下效率不同。','以实际部署引擎为准扫描可用配置，固定总卡预算与输入输出长度。','先满足内存，再比较 TTFT、TPOT 和每卡达标吞吐。','tune')],
'业务感知调度':[
('连续批处理','短请求完成后，静态批次仍等待长请求。','按生成迭代调整活跃请求集合，让新请求及时进入。','提高资源利用率，同时需要控制长请求等待。','tune'),
('分块预填充','长 prefill 挤占 decode，输出间隔抖动。','把长 prefill 拆成片段，与 decode 共同安排 token 预算。','TTFT 与 TPOT 存在取舍；需要扫描预算而非盲目开大。','tune'),
('过载准入与优先级','负载超过容量时，所有请求一起变慢。','按业务等级限制入队并记录拒绝，给关键请求保留可服务容量。','准入策略是设计建议；结果须同时列拒绝率和各类业务达标率。','kueue')],
'多模型实例多卡调度':[
('副本与资源池放置','模型冷热变化造成一边空闲、一边排队。','根据业务负载调整实例数量和设备放置，同时计入加载成本。','适合持续性变化；频繁伸缩可能被冷启动成本抵消。','kueue'),
('Prefill/Decode 分离','两阶段混跑产生干扰，资源需求又不相同。','DistServe 将两阶段放到不同实例，分别配置并行与资源。','需要支付 KV 传输成本；网络和负载决定是否值得拆分。','dist'),
('缓存与负载联合路由','最短队列可能是冷缓存，命中实例又可能拥塞。','联合估计等待和重计算时间，选择预计完成更快的实例。','由前缀缓存机制推导的候选策略；必须用混合业务轨迹对照。','prefix')],
'模型量化':[
('权重量化','常驻权重与解码时的读取流量较大。','用较少位数编码权重，再通过 scale 等参数重建近似值；AWQ 用激活信息保护重要通道。','主要关注容量与读取成本；只有执行核匹配才可能降低时延。','awq'),
('量化流程与误差控制','少比特表示引入舍入和截断误差。','使用校准数据选择量化配置，必要时保留敏感层高精度；以工具具体算法文档为准。','校准集要覆盖业务，不能只验证通用困惑度。','slim'),
('执行格式适配','生成的量化权重不能直接被目标运行时使用。','核对导出格式、位宽、分组方式和实际执行算子，完成导出到服务的闭环。','先验证工具、引擎和设备三方兼容；不预设 W4 比 W8 更快。','ascend')],
'模型小型化':[
('剪枝','模型中有可移除的参数或结构。','非结构化剪枝保留稀疏矩阵；结构化剪枝直接减少通道、头或层。','前者依赖稀疏核，后者改变结构并常需恢复质量；两者不能混报。','prune'),
('知识蒸馏','较小模型直接训练难以保留教师能力。','用教师输出分布或行为指导学生；MiniLLM 研究生成模型的蒸馏目标。','适合有稳定业务数据的模型；学生结构和训练成本需另外规划。','kd'),
('低秩分解','大矩阵可用较低秩结构近似。','将 W 近似为 A×B；SVD-LLM 用数据白化和参数更新控制截断误差。','只有 r(m+n) 小于 mn 才减少参数；两个小矩阵乘不保证比一个大矩阵乘快。','svd')]
}

def ref(k):
    title,url=S[k]
    return f'<a class="paper-link" href="{url}" target="_blank" rel="noopener">{e(title)} ↗</a>'

def enrich(name,problem,mechanism,experiment,boundary):
    routes=R[name]
    out='<nav class="chapter-nav" aria-label="专题章节">'+''.join(f'<a href="#{i}">{t}</a>' for i,t in [('context','背景挑战'),('routes','技术路线'),('industry','产业实践'),('action','验证建议'),('references','资料依据')])+'</nav>'
    out+=f'<section class="prose" id="context"><p class="eyebrow">01 / CONTEXT</p><h2>从业务瓶颈出发</h2><p>{e(problem)}</p><p>{e(mechanism)}</p></section>'
    out+='<section class="prose" id="routes"><p class="eyebrow">02 / ROOT TECHNOLOGIES</p><h2>拆开机制，选择技术路线</h2><p class="note">以下按技术机制组织。预期价值用于判断是否值得验证，不是本地实测结果。</p><div class="route-stack">'
    for n,(title,challenge,method,value,source) in enumerate(routes,1):
        out+=f'<article class="route"><div class="route-top"><span>0{n}</span><h3>{e(title)}</h3></div><p class="challenge">{e(challenge)}</p><div class="mechanism"><span>介入方式</span><p>{e(method)}</p><span>收益条件</span><p>{e(value)}</p></div>{ref(source)}</article>'
    out+='</div></section>'
    impl='优先沿用当前可运行的软件栈，记录设备型号、驱动、CANN、框架和模型版本。对照官方资料确认接口与支持条件，再做单变量替换。'
    if name in ('模型量化','模型小型化'):impl='从 msModelSlim 与已有压缩专题确认导出和运行路径。模型量化重点验证位宽与执行格式；模型小型化重点验证结构变化后的导出、算子覆盖与业务质量。'
    elif name in ('缓存代计算','迭代次数压缩','业务感知调度','单模型实例多卡调度','多模型实例多卡调度'):impl='以 vLLM-Ascend 的当前安装版本为起点，对照版本说明核查候选功能。先保持模型与硬件不变，只改变缓存、调度或并行中的一个因素，避免无法解释收益来源。'
    out+='<section class="prose" id="industry"><p class="eyebrow">03 / ENGINEERING</p><h2>从机制到可运行实现</h2><p>'+impl+'</p>'+ref('slim' if name in ('模型量化','模型小型化') else 'ascend')+ref('prof')+'<p class="note">NVIDIA、PyTorch 等资料说明通用机制；不代表对应功能已在 310P、910B 或型号待确认的 950 上适配。</p></section>'
    out+='<section class="prose action-panel" id="action"><p class="eyebrow">04 / DECISION</p><h2>下一步验证什么</h2><p>'+e(experiment)+'</p><div class="decision-grid"><div><h3>对照保持一致</h3><p>相同模型、质量指标、业务样本、输入输出长度与到达负载。LLM 以 Qwen3.8-27B 为例，领域模型使用真实降噪或翻译任务。</p></div><div><h3>成功如何判断</h3><p>先明确“质量损失小于 1%”的计算口径；达标后比较 TTFT、TPOT、尾时延、吞吐与内存。只有目标负载下有净收益，才扩大适用范围。</p></div></div><p><strong>路线取舍：</strong>'+e(boundary)+'</p></section>'
    out+='<section class="prose" id="references"><p class="eyebrow">05 / EVIDENCE</p><h2>可追溯的资料依据</h2><p class="note">沿用现有信息源中的 vLLM、vLLM-Ascend、msModelSlim、MLPerf 与性能分析资料，并补充原始论文和官方机制文档。经典论文用于根技术学习，不充当本月新动态。</p>'
    out+=''.join(ref(k) for k in dict.fromkeys([r[4] for r in routes]))+'</section>'
    return out
