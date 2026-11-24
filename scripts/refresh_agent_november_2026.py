"""Curated, primary-source November increment. Idempotent; preserves October records."""
from pathlib import Path
import csv
import io

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'research/agent-scheduling'
CHECKED = '2026-11-24'


def read(name):
    with (P/name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


def write(name, rows):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    (P/name).write_text(output.getvalue(), encoding='utf-8', newline='')


def append(name, rows, key):
    old = read(name)
    incoming = {r[key] for r in rows}
    write(name, [r for r in old if r[key] not in incoming] + rows)


def snapshot(name):
    target = P/'history/2026-10'/name
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((P/name).read_bytes())


for name in ('report-context.csv', 'analysis-recommendations.csv', 'decision-watchlist.csv',
             'weekly-selection.csv', 'research-publications.csv', 'research-publication-links.csv'):
    snapshot(name)

items = [
    dict(id='fairway', kind='academic', ecosystem='研究论文',
         title='Fairway: Load-Aware KV Cache Reuse for LLM Prefill Scheduling', short='Fairway',
         url='https://arxiv.org/abs/2611.02082', full_url='https://arxiv.org/html/2611.02082v1',
         published='2026-11-01', version='arXiv v1', status='预印本 · 指定章节核对',
         checked_sections='v1 摘要、§4 双队列机制、§5.1 平台与 §5.2—5.6 结果和限制', channel='arxiv',
         headline='Fairway：以未缓存工作量和相对等待排序，兼顾缓存收益与长请求尾延迟（干扰感知分配）',
         summary='针对缓存命中优先导致冷请求饥饿的问题，Fairway在vLLM等待队列上结合复用优先与公平通道；作者报告特定对照下P99 TTFT最高改善8.6倍。',
         challenge='相同请求数不代表相同prefill成本；长前缀命中请求不断插队会压住昂贵冷请求。',
         mechanism='用未缓存token估计工作量，用等待时间相对自身prefill时间刻画紧迫度；Fast/Fair两条虚拟通道共同选择准入请求。',
         result='Llama-3.1-8B、vLLM 0.16.0、单张48GB A6000；每请求仅生成1 token。对既有前缀感知策略，P99 TTFT最高降低8.6倍；负载突增时以接近FCFS的尾部获得更低中位数。',
         boundary='这是prefill节点的队列实验，非完整Agent任务加速；不改变驱逐、步长或跨副本路由，也不是昇腾已支持的调度插件。',
         insight='把复用收益与等待保护拆开记账。先检查冷长请求是否被热前缀持续压住，再决定是否引入双通道排序。',
         coffee='热菜单查询不能让新店铺的冷上下文请求无限等待；保护的是模型队列，不是业务授权。',
         experiment='固定模型、卡数和驱逐策略，对比FCFS、最长前缀优先与Fairway；扫描冷热混合和突发，报告长短请求P99及整任务达标率。',
         area='sharing', route='service', role='直接调度', relevance='成本与相对等待提供公平信号；算法动作是实例等待队列的准入次序，不是跨实例选址。',
         decision='缓存优先何时必须让位给等待保护？', impact='在模型实例队列加入成本和等待计量；热点吞吐与冷长请求的尾部同时验收。'),
    dict(id='prefix-metastability', kind='academic', ecosystem='研究论文',
         title='Bursts That Outlast Themselves: Persistent Degradation in Prefix-Cached Agent Serving', short='Prefix-cache metastability',
         url='https://arxiv.org/abs/2611.13412', full_url='https://arxiv.org/html/2611.13412v1',
         published='2026-11-10', version='arXiv v1', status='预印本 · 指定章节核对',
         checked_sections='v1 摘要、§3 对照设置、§4 反馈机制、§5—6 恢复控制及 §8 有效性威胁', channel='arxiv',
         headline='缓存亚稳态：突发退去仍持续重算，活跃会话预算比仅限新请求更关键（干扰感知分配）',
         summary='针对多轮会话缓存被并发挤穿后难以恢复的问题，论文以KV需求预算控制活跃会话；在指定恢复实验中恢复7/7次，仅限制新准入恢复1/7次。',
         challenge='服务变慢使更多会话驻留，工作集超过KV池后反复重算，又进一步拉低处理速度。',
         mechanism='估计活跃会话的驻留KV需求，超预算时暂停部分已接纳会话；把新任务接纳与活跃会话恢复分别控制。',
         result='单MI300X、vLLM/Qwen3-8B的12组配对中，9组仅突发侧持续退化；指定7组恢复对照中，工作集预算与会话上限均恢复7/7，仅限新准入恢复1/7。',
         boundary='另有32B与SGLang敏感性测试；轨迹形状回放不执行真实Agent，单副本、有限时长观测，不能推断生产可用性或NPU阈值。',
         insight='过载恢复需要控制已经占用缓存的活跃集合。只压低入口QPS，未必能排空存量重算；缓存命中恢复也不等于积压已清空。',
         coffee='一批点单在查优惠后返回模型，即使新用户减少，存量会话仍可能互相挤出缓存。',
         experiment='对同一到达流设置无突发/短突发配对，比较仅入口限流与活跃KV预算；观测恢复时间、积压斜率、重算token和被暂停任务的期限。',
         area='sharing', route='quota', role='直接调度', relevance='把并发预算从请求数推进到活跃会话工作集；恢复控制不能只作用于新到达流量。',
         decision='系统拥塞后，应限制新请求还是调整已接纳会话？', impact='准入控制增加活跃会话预算和可安全暂停接口；恢复目标同时包含缓存与任务积压。'),
    dict(id='caas', kind='academic', ecosystem='研究论文',
         title='Reducing Batch Makespan for LLM Agent Workloads through Inference–Environment Coordination', short='CAAS / inference–environment coordination',
         url='https://arxiv.org/abs/2611.16661', full_url='https://arxiv.org/html/2611.16661v1',
         published='2026-11-12', version='arXiv v1', status='预印本 · 指定章节核对',
         checked_sections='v1 §3 缓存/路由、§4 CAAS、§5.1 回放边界、§5.3 和 §5.4 Table 3', channel='arxiv',
         headline='CAAS：分开任务接纳与工具执行容量，以链进度缩短批任务长尾（依赖感知排程）',
         summary='面对Agent交替等待模型和外部环境造成的批任务长尾，CAAS在到达分组内优先推进已显露的深链；指定Ling-3.1/MCP-Atlas对照中，批完成时间由140.5降至128.5分钟。',
         challenge='工具执行名额有限时，将任务接纳量绑死在工具并发上会闲置模型；只顾短调用又可能留下很长的未完成轨迹。',
         mechanism='分离样本接纳上限与环境执行上限；CAAS按到达带、已完成推理轮数、粗粒度推理耗时及到达序排序工具动作。',
         result='Table 3中Ling-3.1-Flash三次各500任务MCP-Atlas平均：Opt-FCFS 140.5分钟、Opt-CAAS 128.5分钟，约降低8.5%；得分80.9/81.3。论文另报告整套组合优化收益，不能归给CAAS单项。',
         boundary='目标是离线批makespan，非在线P95保证；推理回放使用H20/TP4和固定环境响应，不验证语义质量；未知链深度只是启发式信号。',
         insight='工具排队也应感知整项任务进度。先分开接纳预算、模型预算和工具执行预算，再研究链推进规则，避免把所有拥塞归给推理后端。',
         coffee='同时接纳多项订单，但支付/门店API另有执行名额；已完成多轮核对的订单可参与长尾优先比较。',
         experiment='在有限工具并发下固定模型池和轨迹，对照容量耦合、容量解耦+FCFS、容量解耦+CAAS；报告批完成时间、在线任务P95与浅链等待。',
         area='workflow', route='list', role='直接调度', relevance='CAAS排序环境动作，以已观察轮数启发式推进长链；不是已知完整DAG的关键路径最优算法。',
         decision='工具队列是否应理解整项任务进度？', impact='任务接纳量与工具执行槽位分离；在环境动作队列传播任务身份和已完成轮数。'),
    dict(id='duru', kind='academic', ecosystem='研究论文',
         title='Towards Fair Resource Sharing in Agentic LLM Serving', short='Duru',
         url='https://arxiv.org/abs/2611.23558', full_url='https://arxiv.org/html/2611.23558v1',
         published='2026-11-17', version='arXiv v1', status='预印本 · 指定章节核对',
         checked_sections='v1 §3 公平定义、§5 跨层控制、§6 Table 2 和 §7 Figure 9/12；扩容结果区分模拟', channel='arxiv',
         headline='Duru：以Agent归一化慢化贯通准入与实例排序，防止公平损失跨层转移（干扰感知分配）',
         summary='面对路由、实例排程与硬件争用共同造成的Agent不公平，Duru在线估计相对公平份额的慢化并跨层控制；15种实测配置中P99归一化慢化几何均值降低44.4%。',
         challenge='单次请求或token级公平不能反映整项Agent多轮等待；入口少排队也可能只是把延迟推到实例内部。',
         mechanism='估计独占执行成本，以理想处理器共享为参照归一化慢化；路由与运行时用同一信号排序，配合防饥饿准入例外。',
         result='H100/MI300X上3模型与3类轨迹组成的15种配置中，相对指定Dynamo::ThunderAgent+FCFS基线，P99归一化慢化几何均值降低44.4%，吞吐为基线91.8%—127.4%。',
         boundary='归一化慢化不是原始任务时延；独占成本需估计。大规模与自动扩容另含DynoSim模拟；论文未提供昇腾验证，也不保证严格吞吐下界。',
         insight='公平应追踪到原始任务且覆盖入口等待。吞吐、长任务慢化和租户达标率共同决定策略是否值得采用，不能只看命中率。',
         coffee='长上下文订单不应持续拖慢短订单；公平比较应除去订单自身复杂度并保留工具/授权等待归因。',
         experiment='先离线标定独占服务成本；对比仅准入、仅实例排序、仅路由与联合策略，报告P99归一化慢化、有效吞吐和预测误差敏感性。',
         area='sharing', route='service', role='直接调度', relevance='公平对象从独立请求上移到Agent；归一化慢化统一路由、准入和实例排序的反馈。',
         decision='任务公平是否需要跨入口和实例共同记账？', impact='同一task_id贯通路由与实例，等待与服务量都计入任务账本；先校准独占成本。'),
    dict(id='llmd-trace-replay-nov', kind='industry', ecosystem='通用生态',
         title='From agent traces to replay', short='llm-d / traces to replay',
         url='https://llm-d.ai/blog/from-agent-traces-to-replay', full_url='https://llm-d.ai/blog/from-agent-traces-to-replay',
         published='2026-11-09', version='官方技术文章 · 核对2026-11-24页面', status='官方机制说明 · 非性能复现',
         checked_sections='What each dataset actually keeps；From a trace file to a running workload；So which combination do you actually want?', channel='llmd',
         headline='llm-d：区分依赖图回放、请求形状回放与模拟，避免调度基准测错对象（依赖感知排程）',
         summary='针对不同工具都称为Agent回放却保留不同因果信息的问题，llm-d梳理数据字段和回放机制；明确请求吞吐、端到端会话时延与模拟预测不可直接比较。',
         challenge='把相关请求拆成独立到达会抹掉前后依赖，也可能制造真实系统中不会出现的并发。',
         mechanism='按是否保留依赖、实时输出传递、工具等待和前缀共享选择轨迹与回放器；Inference-Perf的依赖图回放与DynoSim虚拟引擎分别标注。',
         result='这是方法对照与接入建议，没有统一加速倍率；文中说明工具结果可被回放但不执行实际外部动作。',
         boundary='同一轨迹在不同loader下语义可能不同；仍需固定版本和检查实际保留字段，性能回放不能代替任务质量验证。',
         insight='先建立因果完整的轨迹契约，再评价排程算法；独立请求压测只用于隔离服务层机制。',
         coffee='比较方案必须等待菜单与优惠的结果；回放不能把三次模型调用按独立时间戳直接并发发出。',
         experiment='对同一小DAG比较独立请求回放与依赖驱动回放，核对调用数、就绪时刻和分支汇合，再运行算法对比。',
         area='workflow', route='adaptive', role='研究基础', relevance='为动态依赖排程提供可回放的因果输入，不把压测器本身当作调度算法。',
         decision='我们比较的是完整任务还是孤立模型请求？', impact='评测入口声明保留的依赖和工具行为；轨迹回放、真实执行与模拟分开报告。'),
    dict(id='ascend-032rc1-nov', kind='industry', ecosystem='昇腾生态',
         title='vLLM Ascend v0.32.0rc1 release notes', short='vLLM Ascend 0.32.0rc1',
         url='https://github.com/vllm-project/vllm-ascend/releases/tag/v0.32.0rc1', full_url='https://github.com/vllm-project/vllm-ascend/releases/tag/v0.32.0rc1',
         published='2026-11-10', version='v0.32.0rc1 · tag 24487f4', status='预发布 RC · 版本说明核对',
         checked_sections='发布标签日期；模型/硬件矩阵；KV Cache and Transfer；Features；Dependencies；与反馈帖#19888区分', channel='ascend',
         headline='vLLM Ascend RC：增加Prefill会话亲和与混合缓存配套，路由实验先锁定版本（状态感知映射）',
         summary='11月10日发布的0.32.0rc1列出可选Prefill会话亲和及扩展的KV传输/缓存池支持，为昇腾多轮缓存路由提供工程候选；没有公布可直接套用的Agent吞吐收益。',
         challenge='混合注意力/循环状态与KV缓存需要正确恢复；只有命中指标而缺少版本兼容，不能安全做亲和路由。',
         mechanism='可选Prefill会话亲和；扩展Mooncake逐层、组件感知缓存传输与AscendStore混合缓存池。具体模型、硬件与并行配置遵循发布矩阵。',
         result='发布页标明RC和vLLM 0.32.0对齐，依赖列CANN 9.2.1、PyTorch/torch-npu 2.10.0/2.10.0.post7。本文未测安装、正确性或性能。',
         boundary='反馈帖列出的旧依赖与发布页不同，本记录以tag说明为准。配置指南存在不等于所有模型/950系列硬件已验证，更非已在云核落地。',
         insight='先回归会话恢复与故障回退，再对比亲和与过载退出；不要直接引入GPU论文的阈值或把缓存支持当成调度收益。',
         coffee='同一订单下一轮可尝试回到持有缓存的Prefill副本，若目标繁忙仍需比较等待与重载代价。',
         experiment='锁定镜像、模型、硬件与tag；验证跨轮缓存、实例退出及混合状态一致性，再扫描亲和/负载回退在冷热负载下的净收益。',
         area='mapping', route='cost', role='工程前提', relevance='Prefill亲和及KV传输改变副本复用的可用条件；发布页不是完整Agent调度策略或性能证明。',
         decision='昇腾缓存亲和实验可以基于哪一组明确版本？', impact='固定RC镜像及依赖矩阵，独立验证缓存恢复正确性，再研究路由代价。'),
    dict(id='llmd-async-qos-nov', kind='industry', ecosystem='通用生态',
         title='Multi-Tenant and Multi-Priority Model Serving with llm-d', short='llm-d Async / multi-tenant QoS',
         url='https://llm-d.ai/blog/multi-tenant-multi-priority-model-serving-llm-d', full_url='https://llm-d.ai/blog/multi-tenant-multi-priority-model-serving-llm-d',
         published='2026-11-16', version='官方技术文章 · 核对2026-11-24页面', status='官方机制说明 · 非性能复现',
         checked_sections='Four-Tier Architecture；Isolation Pillars 1—4；六优先级通道与饱和处理', channel='llmd',
         headline='llm-d Async：配额内外分流、优先级与背压联动，明确共享集群的过载行为（干扰感知分配）',
         summary='面对交互流量与后台批任务共享GPU的问题，llm-d Async以租户队列、配额门和六级优先通道联动路由背压，给出可配置的派发和饱和处置方案。',
         challenge='固定独占资源浪费容量，直接共享又会让批任务挤占交互流量；只限QPS不能表达配额内保障与空闲借用。',
         mechanism='配额门将请求分为reserved/overflow；结合interactive/async/batch形成六条严格优先通道，同通道队列轮询，按worker pool独立合并。',
         result='官方说明饱和时reserved等待、overflow交互返回429、overflow后台回队列退避；未提供可以据此宣称的统一性能提升。',
         boundary='严格优先级与配额规则不等于按实际成本保证Agent公平；低优先级持续过载下的等待需单独评估。',
         insight='将容量拒绝、排队与后台重试设计成显式策略。任务/租户身份应在入口与后端贯通，避免只把等待挪到另一个队列。',
         coffee='付费即时点单与批量预订可共享服务池，但配额内保障、超额借用和饱和时处理应预先规定。',
         experiment='混合交互/后台流量，固定卡数和租户配额，对照固定隔离、共享FCFS与六级通道；检查后台最长等待、429和重试放大。',
         area='sharing', route='quota', role='工程对照', relevance='提供租户预算、借用与背压的可解释基线；与Duru的任务慢化反馈属于不同控制方式。',
         decision='空闲容量如何借用，过载时谁等待、谁拒绝？', impact='为租户建立持久队列与分级准入，容量反馈贯穿派发器和推理网关。'),
    dict(id='llmd-sglang-tiered-nov', kind='industry', ecosystem='通用生态',
         title='Bringing First-Class SGLang Serving to llm-d', short='llm-d / SGLang tiered KV',
         url='https://llm-d.ai/blog/serving-glm-5-2-sglang-tiered-kv-cache-on-llm-d', full_url='https://llm-d.ai/blog/serving-glm-5-2-sglang-tiered-kv-cache-on-llm-d',
         published='2026-11-23', version='官方技术文章 · 核对2026-11-24页面', status='官方实验说明 · 未独立复现',
         checked_sections='§2 SGLang接入；§3 Host RAM与Shared L3；单/多副本条件；What is next中的规划边界', channel='llmd',
         headline='llm-d接入SGLang：L2缓解热缓存抖动，L3以稳态开销换故障恢复（状态感知映射）',
         summary='面对长Agent会话挤出HBM缓存的问题，llm-d展示SGLang分层KV缓存；16张H200指定配置并发128时，L2使中位TTFT由174.2降至20.1秒，L3则需权衡稳态开销。',
         challenge='缓存放在哪里既影响重算，也影响迁移和故障恢复；存储层越多并非稳态越快。',
         mechanism='以HBM L1、主机内存L2和共享存储L3分层承载KV；控制面保持引擎无关，按副本和故障场景组织缓存复用。',
         result='GLM-5.2、16×H200、1P1D、AgentX轨迹、142K上下文上限的900秒测试中，并发128中位TTFT由174.2降至20.1秒。相同单热pod的同步L3配置反而增加14%—33%中位TTFT。',
         boundary='32卡扩展和故障恢复属于另一组条件；结果不能叠加为同卡路由收益。精确块级事件感知仍列为后续工作，不是已完成能力。',
         insight='稳态复用先比较L1/L2；只有恢复价值足以覆盖存取成本时再加L3。路由代价模型应分别估计热命中、回载和故障重建。',
         coffee='常见订单上下文可留在主机内存；副本故障时从共享存储恢复另算收益，不能混为每次点单都加速。',
         experiment='在相同副本数下分别比较L1、L1+L2、L1+L2+L3，稳态和故障注入分开；记录TTFT、任务P95、网络流量和恢复耗时。',
         area='mapping', route='cost', role='工程对照', relevance='分层缓存改变副本命中与回载成本；不能只以命中率排名路由，也不能把扩卡收益记为算法收益。',
         decision='共享缓存是为稳态时延还是为故障恢复付费？', impact='将缓存层级、回载耗时和故障状态输入路由；固定卡数隔离存储策略收益。'),
    dict(id='kinference-launch-nov', kind='news', ecosystem='热点事件',
         title='Buoyant Announces Kinference: An Open Source Inference Serving Platform for Kubernetes', short='Kinference / official launch',
         url='https://www.buoyant.io/newsroom/buoyant-announces-kinference-an-open-source-inference-serving-platform-for-kubernetes', full_url='https://www.buoyant.io/blog/introducing-kinference',
         published='2026-11-04', version='官方发布公告与项目介绍', status='事件核对 · 厂商自述',
         checked_sections='官方公告日期、Availability和平台定位；Introducing Kinference项目说明；未核验基准实现', channel='buoyant',
         headline='Kinference发布：推理控制面开始强调跨模型、机器与租户策略，产品发布仍需性能核验（状态感知映射）',
         summary='Buoyant于11月4日发布Apache 2.0开源Kinference，以vLLM为基础提供Kubernetes推理控制面，面向多模型、多GPU和多机器的平台治理。',
         challenge='单模型引擎之外，还需要统一处理流量、租户和策略；平台功能与调度算法性能不是同一证据。',
         mechanism='项目将模型引擎与Kubernetes控制面分层，面向自托管推理提供平台策略与管理入口。',
         result='官方公告确认项目发布、开源许可证与平台定位。公告中的性能宣传未在本轮核验原始基准配置，故不转为量化技术结论。',
         boundary='这是需求和产品形态信号，不证明最佳算法、生产成熟度、NPU兼容或Agent端到端收益。',
         insight='可把平台层接口与策略分离作为架构观察对象；研究投入仍围绕可验证的排程、路由和资源份额问题。',
         coffee='点单Agent可复用统一模型服务入口；它不替代订单DAG、授权和外部工具恢复。',
         experiment='先审开源实现的路由输入、租户策略和可观测接口；若可重现实验，再与现有轮询/最少在途基线同条件比较。',
         area='mapping', route='cost', role='需求信号', relevance='表明模型服务控制面的产品化需求，不作为缓存路由或Agent调度性能的实证。',
         decision='是否需要可替换策略的推理控制面？', impact='对照平台职责与策略插件边界，性能结论等待原始基准和本地验证。'),
]

pub_fields = list(read('research-publications.csv')[0])
pubs = [{**{k:r.get(k,'') for k in pub_fields}, 'checked':CHECKED} for r in items]
append('research-publications.csv', pubs, 'id')
fact_fields = list(read('research-findings.csv')[0])
append('research-findings.csv', [{k:r['id'] if k=='publication_id' else r[k] for k in fact_fields} for r in items], 'publication_id')
append('research-publication-links.csv', [dict(publication_id=r['id'],area_id=r['area'],route_id=r['route'],role=r['role'],relevance=r['relevance']) for r in items], 'publication_id')
append('publication-source-links.csv', [dict(publication_id=r['id'], channel_id=r['channel']) for r in items], 'publication_id')
append('evidence-reviews.csv', [dict(publication_id=r['id'],reviewed=CHECKED,scope=r['checked_sections'],finding=r['result'],limit=r['boundary']) for r in items], 'publication_id')
append('architecture-evidence-links.csv', [dict(publication_id=r['id'],decision=r['decision'],impact=r['impact'],boundary=r['boundary']) for r in items], 'publication_id')

append('source-channels.csv', [dict(id='buoyant',category='industry',group='跨层工程实践',title='Buoyant / Kinference',url='https://www.buoyant.io/blog',description='Linkerd与Kinference维护方的官方技术博客和发布公告。',focus='推理控制面、Kubernetes集成与租户治理。',rationale='观察模型服务的平台化；官方发布可确认事件，性能宣传另核基准。',cadence='建议每周及版本发布后核对',boundary='厂商自述不是独立性能验证；不将平台发布等同完整Agent调度方案。',checked=CHECKED,priority='observe',ecosystem='general')], 'id')
append('source-profile.csv', [dict(channel_id='buoyant',entry_type='官方技术博客',evidence_role='项目一手资料 · 事件与机制分开核对',research_layer='跨层工程观察')], 'channel_id')
append('source-area-links.csv', [dict(channel_id='buoyant',area_id='mapping'),dict(channel_id='buoyant',area_id='sharing')], 'channel_id')
append('source-domain-links.csv', [dict(channel_id='buoyant',domain_id='mapping',relation='跟踪控制面如何绑定模型请求、实例和部署位置；性能结论需另有实验。'),dict(channel_id='buoyant',domain_id='sharing',relation='跟踪租户策略与共享容量；平台宣传不代替成本公平验证。')], 'channel_id')
audits=[]
for channel, ids, scope, fact in [
    ('arxiv','fairway|prefix-metastability|caas|duru','四篇论文的首发元数据及上述指定正文/实验章节','核对4篇11月首发预印本；Fairway是prefill TTFT，CAAS区分单项与组合，Duru区分实测与模拟。'),
    ('llmd','llmd-trace-replay-nov|llmd-async-qos-nov|llmd-sglang-tiered-nov','11月9/16/23日三篇官方文章与指定机制/实验段落','确认依赖回放边界、六级配额优先通道和分层缓存取舍；L3稳态可增加时延。'),
    ('ascend','ascend-032rc1-nov','v0.32.0rc1发布标签、Dependencies、KV/亲和特性；反馈帖对照','发布页列CANN 9.2.1等依赖，与反馈帖旧配置不同；以tag发布说明建立实验基线。'),
    ('buoyant','kinference-launch-nov','11月4日官方发布公告与Introducing Kinference','确认开源推理控制面发布与定位；未采用未经本轮基准核验的加速宣传。')]:
    original=next(r for r in items if r['id']==ids.split('|')[0])
    entry=next(r['url'] for r in read('source-channels.csv') if r['id']==channel)
    relevance={
        'arxiv':'四篇论文分别用于任务链排序、prefill公平、活跃KV预算和跨层任务公平；逐篇关联具体路线。',
        'llmd':'提供因果回放基座、租户预算/背压工程基线和缓存层级代价对照。',
        'ascend':'为状态感知映射提供Prefill亲和与缓存恢复的版本前提；尚不是性能验证。',
        'buoyant':'提供推理控制面与多租户平台化的需求信号；不作为依赖排程或性能算法的证据。',
    }[channel]
    audits.append(dict(id=f'audit-{channel}-20261124',channel_id=channel,reviewed=CHECKED,entry_url=entry,evidence_url=original['url'],check_scope=scope,access_status='readable',verification_level='mechanism',observed_fact=fact,scheduling_relevance=relevance,limitations='本次定点核对不等于该信源11月全量覆盖；未独立复现，未验证昇腾端到端收益。',next_action='跟踪版本/勘误，并以固定模型、轨迹、卡数的最小对照验证关键假设。',next_review='2026-12-01',publication_ids=ids))
append('source-verifications.csv',audits,'id')
write('report-context.csv',[dict(period_start='2026-11-01',cutoff=CHECKED,status='11月调度技术洞察 · 月内增量')])
write('weekly-selection.csv',[dict(publication_id='llmd-sglang-tiered-nov',week_start='2026-11-18',week_end=CHECKED,category='产业界',reading_order='1')])
write('monthly-selection.csv', [dict(publication_id=r['id'], period='2026-11', purpose=r['role'], question=r['decision']) for r in items])
write('analysis-recommendations.csv', [
    dict(area_id='workflow',route_id='list',title='任务与工具分开限并发，先验证链推进是否缩短批长尾',
         judgment='以CAAS作为本月排程穿刺对象。若模型与工具交替等待、工具并发构成瓶颈，先解除任务接纳量与工具执行槽位的绑定，再比较环境动作排序；不直接替换在线请求队列。',
         condition='有task_id和每轮就绪/完成事件；工具能独立限并发；能安全记录或回放工具响应；确认任务尾部主要来自多轮串行等待。',
         next_step='固定模型、卡数、轨迹和工具时延，对比容量耦合、解耦+FCFS、解耦+CAAS三组。用到达分组宽度做敏感性分析，同时报告makespan、浅链最长等待、在线P95与有效吞吐。',
         boundary='CAAS以已观察链深度启发式排序，不知道未来完整DAG。批makespan改善不能直接外推在线期限达标率；支付等副作用不得因回放或重试重复执行。',
         verification_subject='CAAS：§4 到达带与链进度排序，§5.4 Table 3 单项对照；llm-d依赖图回放：评测基座',publication_ids='caas|llmd-trace-replay-nov'),
    dict(area_id='mapping',route_id='cost',title='以回载和排队的净代价选副本，稳态与恢复分开验收',
         judgment='在昇腾RC的会话亲和/缓存功能上建立工程基线，再借鉴llm-d的L1/L2/L3对照。优先回答缓存在哪里、何时值得等、何时该退出热点，而不是先追求更多缓存层。',
         condition='锁定硬件、模型、镜像和发布tag；缓存恢复正确；队列、缓存层级与传输耗时可观测；不兼容模型和副本先被筛除。',
         next_step='同卡数对照轮询、最少在途、纯亲和及亲和+过载退出。分别测试L1与可用的主机缓存；故障注入独立一组，记录回载成本、稳态TTFT、任务P95和恢复耗时。',
         boundary='vLLM Ascend仍为RC且型号/模型范围有限。llm-d的16卡与32卡结果不合并计为路由收益；共享L3可能损伤稳态时延。',
         verification_subject='vLLM Ascend 0.32.0rc1：Prefill亲和/混合缓存；llm-d SGLang：§3 分层缓存及故障对照',publication_ids='ascend-032rc1-nov|llmd-sglang-tiered-nov'),
    dict(area_id='sharing',route_id='quota',title='先守住活跃KV预算，再用任务慢化约束公平损失',
         judgment='建议本月先穿刺缓存亚稳态论文的工作集预算，验证突发后是否能恢复；若基本稳定而长短任务不公仍明显，再用Duru的慢化计量与Fairway的实例队列规则做分层对照。',
         condition='可观测任务级活跃KV与等待；后端支持安全暂停/恢复或明确的活跃额度控制；有独占服务成本标定和租户公平护栏。',
         next_step='对同一到达流做突发配对：仅入口限流对照活跃KV预算。先看积压是否排空和恢复时间；再固定预算比较FCFS/Fairway/Duru相关机制，防止把入口等待隐藏到实例内。',
         boundary='活跃KV预算不等于随意抢占；暂停不一定释放显存。Duru的归一化慢化、Fairway的prefill TTFT和本地整任务达标率必须分别报告；不承诺GPU论文阈值可复用到昇腾。',
         verification_subject='缓存亚稳态论文：§5—6恢复与预防；Duru：§3/5慢化反馈；Fairway：§4/5；llm-d Async：可解释配额对照',publication_ids='prefix-metastability|duru|fairway|llmd-async-qos-nov'),
])
write('decision-watchlist.csv', [
    dict(id='nov-recovery',question='突发退去后，只限新请求能否恢复？',position='先限制活跃KV工作集，再评价恢复与长期稳定性。',change='本月论文提供配对退化和恢复反例，使入口QPS控制不足成为具体待检验假设。',trigger='相同稳态负载在突发后出现持续重算和积压增长。',reversal='若同条件下入口限流即可稳定排空，或活跃预算伤害期限达标率且无稳定性净收益，缩小使用范围。',review_trigger='完成突发配对；引擎驱逐/暂停语义变化',review_due='2026-12-01',reviewed=CHECKED,publication_ids='prefix-metastability|llmd-sglang-tiered-nov'),
    dict(id='nov-chain',question='是否值得把任务进度带入工具排程？',position='仅在环境并发与批长尾构成瓶颈时优先研究CAAS。',change='本月将任务接纳和环境容量分离，并给出CAAS相对Opt-FCFS的单项对照；不把组合收益算给排程。',trigger='批完成时间被少数多轮长链支配，且外部工具有有限槽位。',reversal='若深链启发式导致浅链超期，或工具外因主导且不可调度，则保留解耦预算、回退FCFS。',review_trigger='任务图或工具延迟分布变化；完成CAAS消融',review_due='2026-12-01',reviewed=CHECKED,publication_ids='caas|llmd-trace-replay-nov'),
    dict(id='nov-fairness',question='缓存效率提高后，谁承担了额外等待？',position='用任务账本同时观察吞吐与公平，先标定成本，再跨层协调。',change='Fairway与Duru分别在实例准入和跨层Agent公平给出新机制；llm-d Async提供配额/优先级工程基线。',trigger='冷长请求或受保护租户达标率随命中率上升反而下降。',reversal='若独占成本无法可靠估计，先保留配额与等待护栏；若跨层联合净收益不足，则采用较简单的单层策略。',review_trigger='公平对象或租户权重改变；完成分层对照',review_due='2026-12-01',reviewed=CHECKED,publication_ids='fairway|duru|llmd-async-qos-nov'),
])
print('Curated November increment: 9 dated items, 4 papers, 4 industry records, 1 launch event; 4 source checks. October snapshot preserved.')
