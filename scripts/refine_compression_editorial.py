"""Apply the reviewed editorial revision to the canonical content, not generated pages."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / 'data/compression/tables'

SOURCE_COPY = {
 'source-family-vllm-ascend':'vLLM 的昇腾适配项目。重点跟踪量化格式、KV 缓存、模型适配和 Attention 算子的版本变化，用于判断压缩方案是否具备部署入口；与 vLLM 主项目的支持范围分别核对。',
 'source-family-msmodelslim':'昇腾模型压缩工具。重点跟踪量化校准、精度恢复、模型适配与导出格式，连接算法研究和部署执行。具体算法、位宽及模型支持以所用版本文档为准。',
 'source-family-ops-transformer':'CANN 的 Transformer 算子项目。重点查看量化矩阵乘、Attention、MoE 等算子的接口、数据布局与版本配套，用于定位压缩表示到实际计算之间的适配工作。',
 'source-family-ascend-mindie':'昇腾推理服务工具链。重点查看模型部署、量化配置与缓存管理资料，用于检查模型、硬件、CANN 与推理服务版本是否匹配。',
 'source-family-ascend-community':'昇腾官方开发者社区。作为平台文档、产品资料与开发动态的入口，重点查找目标设备的能力约束和压缩部署资料。',
 'source-family-vllm':'开源 LLM 推理服务项目。通过代码、文档与发布记录跟踪量化、分页 KV 缓存及服务调度实现，作为算法接入和端到端性能评估的工程参照。',
 'source-family-sglang-blog':'开源模型推理运行时。重点跟踪低精度执行、缓存管理、Attention 与服务性能的实现变化，核对实验配置及版本条件后再比较结果。',
 'source-family-iclr':'国际学习表征大会。通过官方论文与 OpenReview 评审记录跟踪量化、剪枝、蒸馏和缓存压缩，重点阅读方法假设、消融实验及评审争议。',
 'source-family-icml':'国际机器学习大会。重点查阅压缩算法、误差分析与效率评测的原始论文，判断方法解决了什么问题，以及质量与成本如何权衡。',
 'source-family-channel-ddf4c0a194109a11422236e3':'神经信息处理系统大会。通过官方论文集追踪模型压缩与高效推理研究，重点核对创新机制、适用模型、实验基线和质量代价。',
 'source-family-mlsys':'机器学习与计算系统会议。重点关注算法、内核与服务系统的协同设计，帮助判断论文中的存储或计算节省能否转化为真实推理收益。',
 'source-family-openreview':'公开论文、评审与版本记录平台。用于核对投稿、修订、作者回应和评审意见；论文是否录用及采用哪个版本，均按具体记录判断。',
 'source-family-hf-daily-papers':'论文发现与讨论社区。用于补充候选和发现遗漏；技术结论及实验数字回到论文原文和作者实现核实。',
 'source-family-jiqizhixin':'中文人工智能技术媒体。用于发现论文、模型和国内工程进展，再沿原文与官方实现链接筛选与推理压缩直接相关的内容。',
 'source-family-channel-efa84fcedb529eaf02e5e044':'中文人工智能科技媒体。用于补充模型发布与国内产业线索；涉及能力或性能的判断，以发布机构原文和实验条件为依据。',
 'source-family-techcrunch-ai':'科技新闻媒体的人工智能栏目。用于发现模型、芯片和商业部署变化，并判断它们是否改变压缩需求或落地条件。新闻报道本身不作为压缩效果的实验依据。',
 'source-family-the-batch':'DeepLearning.AI 的人工智能资讯周刊。用于补充研究和产业变化的周度线索，筛选模型效率与推理成本相关内容后回溯原始材料。',
 'source-family-import-ai':'人工智能研究趋势周刊。用于发现跨团队研究线索与趋势变化，关注其对模型效率、部署成本和技术选路的影响。',
 'source-family-channel-504ab131bf9a634afa68dc25':'GitHub 热门仓库发现入口。用于发现目录之外的压缩工具和实现，随后检查代码、文档与发布记录；社区热度仅帮助发现候选。',
 'source-family-channel-8c132669acb050f97048adf3':'科技与工程讨论社区。用于发现新工具、实现问题和使用反馈，争议与经验需要回到代码或可复现材料核实。',
 'source-family-channel-09b05ee8aefda7618b4dbbdf':'技术讨论社区的人工智能入口。用于补充工程实践和不同观点，帮助发现值得进一步查证的问题。',
}
WATCH_TITLES={
 'parameters-precision':'RTN、AWQ 与 GPTQ 的质量及执行对照',
 'parameters-selection':'通道裁减的质量与设备时延对照',
 'parameters-factorization':'热点线性层的秩与执行成本扫描',
 'parameters-distillation':'同一学生结构的蒸馏收益对照',
 'activations-precision':'SmoothQuant 与普通 W8A8 的对照',
 'activations-selection':'任务适用性与选择开销验证',
 'activations-merging':'相同 token 预算的合并与删除对照',
 'activations-factorization':'注意力近似的工作区与质量对照',
 'activations-distillation':'窄学生的特征监督与内存验证',
 'kv_cache-precision':'缓存位宽、任务质量与并发扫描',
 'kv_cache-kv_eviction':'同一物理预算下的缓存淘汰对照',
 'kv_cache-selection':'通道预算与注意力执行验证',
 'kv_cache-factorization':'固定秩与注意力感知选秩对照',
 'kv_cache-distillation':'紧凑结构的质量恢复与执行验证',
 'kv_cache-sharing':'KV 分组比例与任务质量对照',
 'kv_cache-compact_architecture':'已有检查点的能力与部署成本对照',
}

# Recommendations are proposals. No author-result field or measured number is changed.
TOPICS = {
 'parameters-precision': (
  '用更少的位数保存权重，如何兼顾模型质量、内存占用与推理速度？',
  '权重量化最直接的价值是减少参数存储和读取量。以 Qwen3.8-27B 为例说明实验设计，也适用于其他 LLM；降噪、翻译等领域模型则需要各自的校准数据与质量指标。权重、激活和 KV Cache 的压缩分别评估。',
  '先比较 RTN、AWQ 和 GPTQ 的质量，再为通过质量门槛的候选打通执行链。小批量解码若受权重带宽限制，重点评估低比特权重读取；预填充若受计算限制，则另评估权重与激活联合量化。两类实验分别计入反量化、布局转换和高精度保留层的成本。',
  '首轮实验：固定检查点、校准集与独立业务集，比较浮点基线、RTN-W4、AWQ-W4、GPTQ-W4；只采用目标工具链能够导出且目标算子能够读取的共同格式。记录任务质量、实际权重字节、峰值内存、TTFT、TPOT 和吞吐。质量损失低于约定的 1% 门槛后，再决定是否投入格式或内核适配。'),
 'parameters-selection': (
  '删除哪些权重或结构，才能让模型真正变小、执行更快？',
  '剪枝删除部分连接、通道、注意力头或层。非结构化剪枝保留原矩阵形状，结构化剪枝则改变实际尺寸；两者需要不同的执行支持。',
  '领域模型优先评估能够缩小执行图的通道或模块裁减；LLM 的非结构化剪枝则先确认稀疏格式和算子支持。SparseGPT、Wanda 可用于比较保留连接的质量，但能否减少执行时间取决于实际跳过了多少工作。',
  '首轮实验：选择领域模型中占时最高且允许修改的卷积块或 FFN，比较原结构、按计算量裁减和按目标设备实测时延裁减。保持恢复训练预算一致，检查导出后的张量形状、任务质量与 P95 时延。若仅置零而执行形状不变，转回结构裁减或量化路线。'),
 'parameters-factorization': (
  '用两个较小矩阵替代大权重矩阵，何时能节省存储和执行时间？',
  '低秩分解用较小的矩阵乘积近似原权重。较低的秩可以减少参数，但也会损失表达能力，并把一次运算拆成多次运算。',
  '先以普通截断 SVD 为基线，再比较 ASVD 的激活感知校准与 SVD-LLM 的白化、恢复机制。优先选择占时明显且允许改图的线性层；秩的选择同时受任务误差和目标设备矩阵效率约束。',
  '首轮实验：在一个热点线性层扫描候选秩，再比较普通 SVD 与激活感知分解。分别测量两个因子矩阵的存储、额外中间张量、层输出误差和整模型质量。只有总时延与质量同时达标，才扩大层覆盖；小矩阵启动成本抵消节省时停止扩展。'),
 'parameters-distillation': (
  '让小模型学会业务所需能力，能否降低部署成本？',
  '蒸馏利用教师模型的输出或中间表征训练学生模型。部署成本由学生结构决定，教师监督用于改善学生质量。适合能够更换或重新训练模型的业务。',
  '降噪、翻译等任务较明确的业务，可优先比较紧凑学生在有无蒸馏时的质量。LLM 则先确定必须保留的能力与学生规模，再选择响应、概率分布或推理轨迹监督。把学生缩小与蒸馏恢复的贡献分开。',
  '首轮实验：固定一个学生结构和训练预算，对比仅用任务标签训练与加入教师监督。以独立业务集检查质量、难例和分布变化，再到目标设备测时延、峰值内存和吞吐。学生质量未达标时先检查监督数据与容量，而非直接扩充部署范围。'),
 'activations-precision': (
  '降低中间激活的精度，如何控制离群值误差并获得计算收益？',
  '激活是输入经过网络各层时产生的中间数值。低精度表示可减少中间数据与计算开销，但激活范围随输入变化，校准需要覆盖真实业务。',
  '以普通 W8A8 为对照，评估 SmoothQuant 的等价缩放能否缓解激活离群值。先选择线性层或目标框架支持的算子；其他分支按实际模型结构逐项检查。降噪重点覆盖静音、低能量和瞬态，翻译重点覆盖语言对与句长。',
  '首轮实验：比较普通 W8A8、SmoothQuant-W8A8 与敏感层保留高精度三个配置，固定校准样本和业务集。记录逐层误差、前后转换耗时、预填充时延与服务吞吐。质量达标但转换频繁时，优先改进融合和数据布局，再考虑更低位宽。'),
 'activations-selection': (
  '减少参与计算的 token 或通道，怎样保留关键任务信息？',
  '动态选择根据当前输入跳过部分 token、通道或激活。它与提前删除固定参数不同：选择发生在运行时，也会引入评分、索引和数据整理成本。',
  '先按任务区分候选。SparseVLM、PruMerge 等视觉路线用于有图像输入的业务评估；文本 LLM、降噪和翻译需要对应的任务证据。动态稀疏只有在实际算子跳过计算，或数据压紧后减少后续稠密运算时才有性能价值。',
  '首轮实验：业务确有视觉输入时，在相同 token 预算下比较不裁减、简单选择与候选方法，计入评分及 gather 开销。纯文本或音频业务先保留信息完整的基线，不直接删除源词或语音帧；待找到对应方法与质量证据后再启动实验。'),
 'activations-merging': (
  '将相近 token 合并，能否比直接删除更好地保留信息？',
  'Token 合并把多个相似表示聚合成较少的表示，以减少后续层的输入长度。合并保留的是聚合信息，其效果取决于匹配、位置处理与合并时机。',
  '以 ToMe 为机制参考，优先在视觉或其他允许聚合的模型中研究。与 token 删除在相同保留预算下比较，关注合并能否保留局部细节，以及匹配成本能否被后续计算节省覆盖。',
  '首轮实验：选择一个可合并的中间层，对比不压缩、相同预算剪枝与相同预算合并。固定任务与输入尺寸，测量匹配耗时、后续层时延和细粒度任务质量。对因果文本或流式音频，先验证时序与位置信息约束，再考虑迁移。'),
 'activations-factorization': (
  '近似注意力中间矩阵，什么时候值得修改模型结构？',
  '显式注意力分数矩阵随序列长度平方增长。Linformer、Nyströmformer 等路线用投影或代表位置近似注意力关系，试图减少这部分计算和存储。',
  '先通过执行图与性能剖析确认瓶颈：融合注意力可能已经避免保存完整中间矩阵。只有长序列任务仍受该部分限制、且允许结构改造或训练时，才评估投影或 landmark 近似。',
  '首轮实验：在一个注意力模块中，对照精确实现、Linformer 投影或 Nyströmformer 近似，扫描近似维度。检查因果或流式约束、峰值工作区、任务质量及完整模块时延。若原实现不物化大矩阵，先评估现有融合核，不启动整模型替换。'),
 'activations-distillation': (
  '用教师监督训练更窄的学生，能否减少中间张量而保住质量？',
  '更窄或更浅的学生会产生较小的中间表示，但结构缩小也可能损害任务能力。特征蒸馏利用教师的中间表示辅助训练，帮助学生恢复质量。',
  '领域模型允许改结构时，可比较 FitNets 式特征监督；TinyBERT、MobileBERT 则作为相应编码器结构的参考。实际内存节省来自学生张量尺寸变化，特征匹配本身属于训练过程。',
  '首轮实验：固定窄学生结构，对比无蒸馏与加入特征监督两个版本，保持训练数据和预算一致。推理时去掉训练辅助分支，分别测任务质量、峰值激活、工作区与逐帧或逐句时延。若业务不允许重训或替换结构，暂缓该路线。'),
 'kv_cache-precision': (
  '降低 KV 缓存位宽，能否容纳更长上下文或更多并发？',
  '自回归模型会保存历史 token 的 Key 和 Value，供后续生成读取。KV 量化减少每个元素的表示位宽，适合缓存容量或读取量已经成为瓶颈的场景。',
  '先比较 KIVI、KVQuant 的分组与异常值处理思路，并确认注意力核如何读取低比特缓存。K 与 V 分别评估；高精度近期窗口、尺度元数据和反量化工作区一起计入容量。',
  '首轮实验：固定模型与权重精度，从未压缩 KV 起步扫描目标栈支持的缓存位宽与分组。比较相同并发的 TTFT、TPOT，以及相同时延约束下的最大吞吐；同时测试长检索、多轮和长生成质量。先守住质量，再决定是否采用更低位宽。'),
 'kv_cache-kv_eviction': (
  '缓存预算有限时，保留哪些历史 token 才不影响后续回答？',
  'KV 淘汰删除部分历史 token 的缓存条目，以减少持续保存的状态。删除后信息可能无法恢复，因此需要同时考虑重要性、决定时机与实际物理页回收。',
  'H2O、SnapKV、PyramidKV 提供不同的评分和预算分配思路。先验证分页布局能否真正回收内存，再比较复杂策略的质量；GQA 下需要检查共享 KV 头与逐头选择的实际预算。',
  '首轮实验：对照完整 KV、滑动窗口与一个候选策略，在相同物理缓存预算下重放真实长文本请求。记录实际占用页数、选择与回收耗时、检索质量和 TPOT。若只减少逻辑条目而未减少物理占用，先修复缓存管理；关键任务退化时放宽预算。'),
 'kv_cache-selection': (
  '裁减 KV 特征通道，能否减少每个 token 的缓存开销？',
  '通道裁减减少 Key 或 Value 的特征维度，保留的 token 数量可以不变。它与淘汰整个 token、降低数值位宽是不同的压缩方式。',
  '以 ThinK 的查询感知 Key 通道选择为参考，先明确被裁减的轴及其与 RoPE 的关系。关键是压缩布局能否被注意力算子直接使用，而不是仅在保存前缩小张量、计算前又完整展开。',
  '首轮实验：在一个可适配的注意力层中比较完整特征与候选通道预算，记录选择成本、实际缓存字节和检索质量，再扩展到整模型。若目标核必须恢复原布局，计入重建与临时内存；净收益不成立时转向 KV 量化或页级预算。'),
 'kv_cache-factorization': (
  '用低秩因子保存 KV，如何平衡容量节省与在线分解成本？',
  '低秩 KV 用较小的因子近似历史缓存，减少持续保存的状态。它既可能增加预填充分解成本，也可能增加解码重建成本，需要结合上下文和生成长度判断。',
  '优先比较保持既有模型的缓存分解，再单列需要结构改造的路线。以 AttSVD 为候选时，关注注意力加权选秩、近期精确窗口和后续增量压缩；权重投影分解及原生 MLA 另作对照。',
  '首轮实验：在长上下文 LLM 请求中比较完整 KV、固定秩 SVD 与注意力感知选秩，分别扫描近期高精度窗口。把分解计入 TTFT、重建计入 TPOT，统计因子、窗口与工作区的总内存。质量达标且容量收益能支持更多有效并发时再扩大覆盖。'),
 'kv_cache-distillation': (
  '把已有模型改成紧凑 KV 结构后，蒸馏能恢复多少任务能力？',
  '改变缓存结构可以减少持久状态，却也会改变注意力计算。蒸馏用教师监督恢复转换后模型的能力，代价是结构适配、训练和新的部署路径。',
  '以 X-EcoMLA 为结构转换与质量恢复的参考。先确认业务允许训练改造，再检查潜在缓存、RoPE 和注意力执行是否有可实现路径。缓存压缩与蒸馏贡献通过相同学生结构的对照实验区分。',
  '首轮实验：固定紧凑学生结构，比较初始化转换、仅任务训练和加入教师监督的质量，保持训练预算可比。先做短任务与长检索质量验证，再测目标设备缓存、TTFT、TPOT 和吞吐。若缺少结构算子支持，先做模块适配原型，不直接启动全量训练。'),
 'kv_cache-sharing': (
  '让查询头共享 KV，如何减少缓存而保留模型能力？',
  'MQA 让多个查询头共享一组 KV，GQA 则让查询头分组共享 KV。减少的是持久缓存的头数；共享比例由模型结构决定。',
  '已有 GQA 模型先检查真实 Q/K/V 头数及内核执行，避免重复计算结构本身带来的节省。将 MHA 转成 GQA 或 MQA 属于模型改造，需要单独考虑转换训练和质量恢复。',
  '首轮实验：若允许结构转换，固定学生结构与训练预算，比较候选分组比例的质量和缓存字节，再测解码性能。若不允许改模型，则只优化既有 GQA 的缓存布局与算子，不把减少 KV 头当作可直接启用的部署选项。'),
 'kv_cache-compact_architecture': (
  '从架构上缩小持久状态，需要付出哪些训练与部署代价？',
  '紧凑注意力架构通过潜在表示、共享或混合状态设计减少历史信息的保存成本。它改变的是模型计算结构，通常需要相应的训练与专用执行路径。',
  '优先从已有公开检查点及可用执行实现评估 MLA 等架构，比较相同业务质量下的总部署成本。结构转换项目与已有模型的推理期压缩分开立项，分别估算训练、算子及维护投入。',
  '首轮实验：选择已有检查点与兼容执行栈，建立质量和缓存基线，再分析潜在缓存布局、恢复计算与通信开销。与业务能力相近的基线比较容量、TTFT、TPOT 和吞吐；只有能力和执行路径都满足需求，才考虑扩大采用范围。'),
}

def main():
 changes=[]
 names=['ic_compression_topics','ic_compression_topic_sections','ic_compression_topic_cards','ic_compression_research_frames','ic_channels','ic_source_families','ic_insight_reports','ic_paper_summaries']
 for name in names:
  path=TABLES/name/'rows.jsonl'; records=[json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
  for item in records:
   r=item['row']; before=dict(r); topic=r.get('compression_topic_id'); config=TOPICS.get(topic)
   if config and name=='ic_compression_topics':r['question_zh']=config[0]
   if config and name=='ic_compression_research_frames':r['why_zh']=config[1]
   if config and name=='ic_compression_topic_sections':
    kind=r['section_kind']
    labels={'problem':'研究背景','mechanism':'技术原理','comparison':'路线比较','boundary':'适用条件','implication':'研究判断','watch':'验证计划'}
    r['heading_zh']=labels[kind]
    if kind in ['problem','implication','watch']:r['body_zh']=config[{'problem':1,'implication':2,'watch':3}[kind]]
   if name=='ic_compression_topic_cards' and config and r['claim_kind']=='research_analysis':
    # Replace action cards, not evidence cards. Retain IDs, source bindings and review history.
    if r['section_kind']=='watch' and r['card_id'].endswith('__dossier_6'):
     r['body_zh']=config[3]+'\n验收口径：业务质量损失小于 1% 是目标，需先约定主指标及相对或绝对变化的计算方式。310P、910B 分别实测；950 的完整型号与软件配套确认后再选择执行配置。'
     r['title_zh']='验证计划：'+WATCH_TITLES[topic]
    if r['section_kind']=='implication' and r['card_id'].endswith('__dossier_5'):r['body_zh']=config[2]
    if r['section_kind']=='implication' and topic=='parameters-precision' and r['card_id'].endswith('__dossier_5'):r['title_zh']='研究判断：根据瓶颈选择量化配置'
    # Drop unverified model architecture and support assertions from editorial guidance.
    for old,new in [
     ('Qwen3.8-27B已有官方W8A8部署与质量示例，可作为业务复现起点；','以 Qwen3.8-27B 为例，先确认检查点与当前工具链的兼容性，再建立浮点及可执行的 W8A8 基线；'),
     ('先复现官方W8A8部署与质量评测','先建立目标执行栈可支持的量化部署与质量基线'),
     ('当前msModelSlim GPTQ不应预设可导出INT4','msModelSlim GPTQ 的导出类型应按实际使用版本核对'),
    ]:r['body_zh']=r['body_zh'].replace(old,new)
   if name in ['ic_channels','ic_source_families']:
    field='focus_zh' if name=='ic_channels' else 'summary_zh';text=r.get(field,'')
    if ' 核心选择理由：' in text:
     lead,reason=text.split(' 核心选择理由：',1)
     r[field]=reason if lead.startswith('从该公开来源定位') else lead+' 重点关注'+reason
    else:r[field]=text.replace('选择理由：','本专题关注').replace('选择它来','用于').replace('重点选择它来','用于')
    if name=='ic_source_families' and r.get('family_id') in SOURCE_COPY:r[field]=SOURCE_COPY[r['family_id']]
   if name=='ic_insight_reports' and r.get('status')=='published':
    r['summary_zh']='围绕业务质量、容量、吞吐与时延比较压缩技术，提出值得验证的论文、适配工作和停止条件。先阅读报告结论与路线取舍，再按需要查阅方法、实验和原图。实验数字保留论文的模型、设备、数据集和基线；未报告的指标不作估算，昇腾收益仍需业务实测。'
   if name=='ic_paper_summaries' and '2610.02598' in r.get('evidence_url',''):
    r['one_sentence_zh']='SpAx 针对卸载权重的传输瓶颈，按激活大小选择读取原权重、压缩近似或跳过；作者报告 CPU 卸载 16-bit 权重时平均解码加速 3.86 倍，WikiText-2 困惑度增幅上限为 10%。这项质量条件不同于业务损失小于 1% 的目标。'
   if name=='ic_compression_topic_cards':
    # Remove unsupported assertions from both language versions, including retained method cards.
    replacements={
     'reproduce the official Qwen3.8-27B W8A8 example as a quality and serving baseline':'confirm checkpoint compatibility and establish a runnable floating-point and W8A8 baseline',
     'its official configuration has 16 full-attention layers and 48 Gated DeltaNet layers.':'inspect the actual checkpoint configuration and identify its persistent state types.',
     'Preserve the 48 Gated DeltaNet state, gating and convolution branches until their behavior is established':'Preserve any recurrent state, gating and convolution branches until their behavior is established',
     'Qwen already combines 16 full-attention layers and 48 recurrent-state layers':'The actual checkpoint architecture and execution graph must first be established',
     '复现官方Qwen3.8-27B W8A8示例':'确认检查点兼容性并建立可运行的 W8A8 基线',
     '复现官方 Qwen3.8-27B W8A8 示例':'确认检查点兼容性并建立可运行的 W8A8 基线',
     '复现官方W8A8':'建立实际运行栈支持的 W8A8 基线',
     'Qwen3.8-27B已有官方W8A8':'以 Qwen3.8-27B 为例，先确认当前版本的 W8A8',
    }
    for field in ['body_zh','body_en']:
     for old,new in replacements.items():r[field]=r[field].replace(old,new)
   fields=[k for k in r if k.endswith('_zh') and isinstance(r[k],str)]
   for field in fields:
    # Editorial typography only: never change source identifiers, experimental values or dates.
    for old,new in [('KV缓存','KV 缓存'),('CPU卸载','CPU 卸载'),('HBM常驻','HBM 常驻'),('TTFT和TPOT','TTFT 和 TPOT'),('TTFT/TPOT','TTFT / TPOT'),('prefill','预填充（prefill）'),('decode','解码（decode）')]:
     if old in ['prefill','decode']:continue
     r[field]=r[field].replace(old,new)
   if r!=before:changes.append({'table':name,'key':item['key'],'fields':[k for k in r if r[k]!=before.get(k)]})
  path.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in records),encoding='utf-8')
 # Report the complete revision against Git, even after an idempotent rerun.
 changes=[]
 for name in names:
  relative='data/compression/tables/'+name+'/rows.jsonl'
  baseline=subprocess.run(['git','show','HEAD:'+relative],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8')
  old={r['key']:r['row'] for r in map(json.loads,baseline.splitlines())}
  for item in map(json.loads,(ROOT/relative).read_text(encoding='utf-8').splitlines()):
   fields=[k for k,v in item['row'].items() if v!=old[item['key']].get(k)]
   if fields:changes.append({'table':name,'key':item['key'],'fields':fields})
 report={'date':'2026-10-22','status':'local_review_not_published','scope':'Reader-facing source descriptions, all 16 topic introductions and proposed actions; original result values and citations retained.','changed_records':len(changes),'changes':changes,'limitations':['English copy is retained; this editorial pass targets Chinese reading.','Existing author-reported results have not all been re-reviewed against full text.','PDF/PPT binary assets are unchanged.','Original website is unchanged.']}
 (ROOT/'docs/editorial-refinement-20261022.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Updated',len(changes),'canonical records')

if __name__=='__main__':main()
