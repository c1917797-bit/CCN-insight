# -*- coding: utf-8 -*-
"""Research-first weight-quantization dossier. Writes canonical content only."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/compression/tables'
def load(t):
    return [json.loads(s) for s in (BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()]
def write(t, records, key):
    rows=load(t); index={r['key']:n for n,r in enumerate(rows)}
    for record in records:
        k=record[key]
        if k in index:
            old=rows[index[k]]
            if old['row']==record:continue
            rows[index[k]]={**old,'row':record,'row_version':old['row_version']+1}
        else:rows.append(dict(key=k,row=record,row_version=1,deleted=False,text_match=None))
    (BASE/t/'rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')

SOURCES=[
('wq-current-msmodelslim','https://www.hiascend.com/document/detail/en/mindstudio/2610/TITools/msModelSlim/docs/en/user_guide/quantization_algorithms/README.md','msModelSlim 26.1.0 · Algorithm overview','official_documentation'),
('wq-current-ascend','https://docs.vllm.ai/projects/ascend/en/latest/user_guide/feature_guide/quantization.html','vLLM-Ascend · Quantization guide, including native FP8 execution','official_documentation'),
('wq-omniquant','https://arxiv.org/abs/2308.13137','OmniQuant: Omnidirectionally Calibrated Quantization for Large Language Models','paper'),
('wq-spqr','https://arxiv.org/abs/2306.03078','SpQR: A Sparse-Quantized Representation for Near-Lossless LLM Weight Compression','paper'),
('wq-squeezellm','https://arxiv.org/abs/2306.07629','SqueezeLLM: Dense-and-Sparse Quantization','paper'),
('wq-qtip','https://arxiv.org/abs/2406.11235','QTIP: Quantization with Trellises and Incoherence Processing','paper'),
('wq-flatquant','https://arxiv.org/abs/2410.09426','FlatQuant: Flatness Matters for LLM Quantization','paper'),
('wq-curvetq','https://arxiv.org/abs/2610.09212','CurveTQ: Rotation-Free Trellis Quantization of LLM Weights via Curvature-Weighted Search','paper')]
existing={x['row']['canonical_url']:x['row']['source_id'] for x in load('cloud_core_sources') if not x['deleted']}
new=[]
for key,url,title,kind in SOURCES:
    if url in existing:continue
    existing[url]=key
    new.append(dict(source_id=key,business_id='cloud-core',batch_id='research-first-20261023',canonical_url=url,external_id='',last_checked_at='2026-10-23',provider='arxiv.org' if kind=='paper' else url.split('/')[2],source_kind=kind,title=title,update_policy='follow_original_url_record_versions',verification_status='primary_abstract_checked' if kind=='paper' else 'primary_selected_sections_checked'))
write('cloud_core_sources',new,'source_id')
def sid(url):return existing[url]
def paper(arxiv):return sid('https://arxiv.org/abs/'+arxiv)
MS=sid(SOURCES[0][1]);ASC=sid(SOURCES[1][1])
cards={r['row']['card_id']:r['row'] for r in load('ic_compression_topic_cards') if not r['deleted']}
changed=[];refs=[]
def card(key,title,body,en_title,en_body,section='comparison',position=80,topic='parameters-precision',sources=()):
    row=cards.get(key,dict(business_id='cloud-core',topic_id='cloud_core',card_id=key,compression_topic_id=topic,card_kind='analysis',claim_kind='research_analysis',section_kind=section,position=position))
    row={**row,'title_zh':title,'title_en':en_title,'body_zh':body,'body_en':en_body,'reviewed_at':'2026-10-23'}
    changed.append(row)
    for source in sources:
        k=key+'__research-first__'+source
        refs.append(dict(reference_id=k,business_id='cloud-core',topic_id='cloud_core',compression_topic_id=topic,card_id=key,source_id=source,checked_at='2026-10-23',review_depth='abstract_review' if next(r['row']['source_kind'] for r in load('cloud_core_sources') if r['row']['source_id']==source)=='paper' else 'section_review',observed_version='primary abstract or specified documentation observed 2026-10-23',locator_zh='论文新增机制仅按摘要核对；工具能力见算法总览，执行能力见量化指南。分类、技术增量与适用条件为编辑分析，非目标设备实测。',locator_en='New paper mechanisms checked at abstract depth; tools from algorithm overview and execution from quantization guide. Taxonomy and applicability are editorial analysis, not target-device measurements.'))

SCOPE_ZH='研究对象：权重是模型长期保存的参数。主线是如何用更少位数表示权重、控制输出误差，并让压缩格式进入实际执行。覆盖范围不以某个模型、设备或当期业务门槛预先裁剪。\n专题分工：W4A16、W8A16以及AWQ/GPTQ等权重优化在本页主讲；W8A8、W4A4的激活离群值、在线尺度与联合计算由“激活 × 量化”主讲。使用激活统计不等于量化激活：AWQ仍是权重量化方法。\n联合方案：同一论文可以关联多个对象，但机制细读和完整实验结果只保留一个主讲位置；另一专题解释关联并链接。联合收益不可按权重、激活、KV三个标签重复相加。KV Cache因随序列/并发积累且有独立读取路径，继续单列。'
SCOPE_EN='Scope: study compact weight representations, output-error control and executable formats across models and devices; current business targets do not restrict collection.\nOwnership: this topic owns W4A16/W8A16 and weight optimizers such as AWQ/GPTQ. Activations × Quantization owns activation outliers, online scales and joint W8A8/W4A4 execution. Using activation statistics does not imply quantizing activations: AWQ is weight-only.\nJoint work: allow multiple tags but one primary explanation and one complete result record. Never add the same joint gain across W/A/KV tags. KV cache remains separate because its lifetime and sequence/concurrency scaling differ.'
card('parameters-precision__insight_scope','专题边界：按对象检索，按完整方案理解',SCOPE_ZH,'Topic boundaries: object-based retrieval, complete-scheme reasoning',SCOPE_EN,position=80,sources=[paper('2306.00978'),paper('2211.10438')])
card('activations-precision__insight_scope','专题边界：激活误差与权重—激活联合计算',SCOPE_ZH,'Topic boundaries: activation errors and joint W/A computation',SCOPE_EN,topic='activations-precision',position=80,sources=[paper('2306.00978'),paper('2211.10438')])

card('parameters-precision__dossier_5','研究结论：技术储备应覆盖多种压缩与执行路线',
'权重量化的技术主线，已从减少参数位数，扩展为误差控制、编码设计与执行协同；判断进展要同时看新增能力和新增代价。\n值得持续积累：整数PTQ与舍入优化、非均匀/稀疏旁路表示、向量码本与trellis编码、FP8/FP4尺度设计、混合精度与低秩补偿。W8A8/W4A4作为联合计算路线，与激活专题交叉检索。\n当前判断：AWQ、GPTQ、SmoothQuant已有工具实现，价值在理解适用差异与实现边界；ReQuant关注固定格式后的再优化，AlignQuant关注压缩与计算块的冲突，低秩补偿关注冻结量化主体后的质量恢复。三者解决的不是同一个问题。\n应用时再选择：容量、带宽、计算、质量、转换成本等需求发生变化时，从相应路线查找候选。Qwen、领域模型与昇腾是应用案例，不是收录范围。',
'Research conclusion: retain multiple compression and execution routes',
'Weight quantization now spans error control, representation and execution co-design, not just bit reduction. Judge new capabilities alongside new costs.\nRetain integer PTQ, nonuniform/sparse-side representations, vector and trellis codes, floating-point scales, mixed precision and low-rank compensation. Joint W/A execution cross-links to the activation topic.\nAWQ, GPTQ and SmoothQuant already have tooling. ReQuant targets fixed-format refinement, AlignQuant targets hardware-aligned execution, and low-rank compensation targets recovery on a frozen quantized backbone. These address different gaps.\nSelect applications later by capacity, bandwidth, compute, quality and conversion cost. Qwen, domain models and Ascend are examples, not collection filters.',sources=[MS,paper('2608.07019'),paper('2610.07457'),paper('2610.08164')])
card('parameters-precision__dossier_3','技术增量：区分参数优化、编码改造与执行改造',
'固定格式优化：AWQ、GPTQ、OmniQuant分别侧重通道尺度、误差补偿、可学习裁剪/等价变换；ReQuant（2026-08）在已有量化网格上继续优化整数分配。判断增量时保持格式和校准预算一致。\n改变表示方式：SpQR、SqueezeLLM将难量化部分单独处理；QuIP#、AQLM、QTIP改用向量/加性/trellis编码。质量潜力之外，需要计入码本、索引、旁路与解码，不能与普通INT4按标称位宽直接排名。\n改变执行分工：AlignQuant（2026-10）以计算块统一精度分配、打包与执行；它提供的是混合精度系统方案，不是“任意GPU的INT4加速系数”。\n增加补偿支路：Align, Then Correct（2026-10）冻结主体并加入低秩校正。适合研究同存储预算下补偿与保留高精度的取舍；支路计算与容量必须一并比较。\n跨对象变换：SmoothQuant、旋转及FlatQuant共同处理权重/激活分布；完整联合机制转到激活专题，本页关注它们对权重表示和执行的影响。',
'Technical increments: parameter refinement, representation and execution',
'Fixed-format refinement: compare AWQ scaling, GPTQ compensation, OmniQuant learned clipping/transforms and ReQuant fixed-grid updates at matched format and calibration budget.\nRepresentation changes: sparse side records and vector/additive/trellis codes introduce metadata and decoding costs; nominal bits are not a fair ranking by themselves.\nExecution changes: AlignQuant aligns allocation, packing and GPU tiles; it is a mixed-precision system, not a universal INT4 speedup.\nCompensation: Align, Then Correct adds low-rank corrections to a frozen quantized backbone. Compare adapters and precision retention at a matched storage budget.\nCross-object transforms: SmoothQuant, rotations and FlatQuant affect both W/A distributions; joint mechanisms are owned by the activation topic.',sources=[paper('2308.13137'),paper('2306.03078'),paper('2306.07629'),paper('2406.11235'),paper('2608.07019'),paper('2610.07457'),paper('2610.08164'),paper('2410.09426')])
card('parameters-precision__dossier_4','证据判断：算法有效、工程支持与实际收益分开',
'机制证据：明确改善的是权重重建、层输出、任务质量还是内核效率；误差更小与服务更快是两件事。\n结果证据：效果同时保留模型、数据集、位宽/格式、设备和负载；TTFT、TPOT、吞吐、权重载荷和峰值内存各自报告。不同论文的PPL和最高加速比不组成统一排行榜。\n实现证据：区分工具列出算法、能导出某格式、运行栈接受该格式、真实调用低精度核四个层次。FP8检查点被展开成BF16执行时，不再拥有原来的一字节权重驻留。\n应用证据：论文结论用于建立候选，不替代具体业务验收。质量允许损失、延时与吞吐目标属于应用条件，可随需求变化；不据此删除前沿技术储备。',
'Evidence: distinguish algorithmic validity, support and realized gains',
'Separate improvements in reconstruction, layer outputs, task quality and kernel efficiency.\nKeep model, dataset, precision/format, device and workload with every result. Report TTFT, TPOT, throughput, payload and peak memory separately; cross-paper headline numbers are not a leaderboard.\nDistinguish algorithm availability, export compatibility, runtime acceptance and actual low-precision kernel execution. Expanding an FP8 checkpoint into BF16 loses its one-byte weight residency.\nApplication thresholds belong to later selection, not to the collection filter.',sources=[ASC,paper('2306.00978'),paper('2610.07457')])
card('parameters-precision__dossier_6','应用索引：需求变化时如何调用技术储备',
'验证对象：按问题选择路线：容量/权重带宽查W4与编码；联合计算查W8A8/W4A4；固定格式质量不足查裁剪、舍入与ReQuant；主体冻结且允许支路查低秩补偿。\n对照方案：使用已有工具链的最佳可复现配置作为基线，而非只与简单RTN比较；同格式优化保持位宽、分组与校准预算一致，跨表示路线比较实际总字节。\n测量指标：按所选问题设置指标，保留质量、内存及执行代价；LLM区分TTFT/TPOT和吞吐，领域模型采用任务指标与端到端时延。\n继续条件：新方法相对已有能力有清楚增量，且在所选约束下成立，再进入适配或部署；允许对算法研究与工程落地作不同结论。\n停止条件：如果只复现工具已有能力而无新增认识，结束重复开发；如果缺少目标执行路径，转为离线算法研究并保留技术记录，不把它从知识库中删除。',
'Application index: select from the knowledge base when requirements change',
'验证对象：Choose by problem: W4/codes for capacity and weight traffic; joint W/A for compute; clipping, rounding and ReQuant for fixed-format quality; low-rank correction for frozen backbones.\n对照方案：Use the strongest reproducible existing toolkit baseline. Match precision, groups and calibration budgets; compare total bytes for different representations.\n测量指标：Use problem-specific quality, memory and execution costs. Separate LLM TTFT/TPOT and throughput; use end-to-end latency for domain models.\n继续条件：Proceed when the new work adds a clear capability under the selected constraints; algorithmic research and deployment can have different decisions.\n停止条件：Avoid reimplementing existing capability without new understanding. Missing execution support limits deployment, not inclusion in the knowledge base.',sources=[MS,ASC,paper('2608.07019'),paper('2610.08164')])
card('parameters-precision__msmodelslim_implementation','msModelSlim：已有算法能力是研究起点，不是新增贡献',
'官方算法总览已列AWQ、GPTQ、AutoRound、SmoothQuant及旋转等能力，另有敏感层分析和回退策略。先确认采用的具体版本与配方，再判断论文增量是否已被工具覆盖。\n能力边界：算法名称、可用位宽、模型适配、导出格式与消费格式的算子并非一一等价。总览不能证明所有算法在310P、910B、950或任意模型上都能运行。\n洞察意义：现有配方作为复现基线；固定格式改进、较低元数据的编码、减少在线变换或更好的质量—成本平衡，才构成继续研究的理由。',
'msModelSlim: existing algorithms form the baseline, not a new contribution',
'The official overview lists AWQ, GPTQ, AutoRound, SmoothQuant and rotations, plus sensitivity and fallback strategies. Establish the version and recipe before judging novelty.\nAlgorithm availability does not establish every bit width, model, export or device execution path.\nUse existing recipes as baselines; pursue fixed-format improvements, lower metadata, less online work or improved quality/cost trade-offs.',sources=[MS,ASC])

CATALOG=[
('calibration','尺度、裁剪与舍入优化','经典：RTN提供简单参考，AWQ用激活统计选择通道缩放，GPTQ补偿层输出误差，OmniQuant学习裁剪与等价变换。\n近期：ReQuant（2026-08）保持量化网格不变，迭代改进整数分配。\n判断：这组路线的价值是同格式下减少误差。应区分离线优化成本与推理开销，避免只与较弱初始配置比较。',[paper('2306.00978'),paper('2210.17323'),paper('2308.13137'),paper('2608.07019')]),
('representation','非均匀表示与稀疏旁路','经典：SpQR、SqueezeLLM保留难量化部分，并将主体压缩；表示方式、额外索引与执行方式共同决定代价。\n关联：这不是剪掉所有旁路权重，也不等于普通均匀INT4。\n判断：适合积累“少数异常值如何保护”的方法；需要比较主体、旁路、索引和尺度的总存储，而非只报告主体位数。',[paper('2306.03078'),paper('2306.07629')]),
('codes','向量码本与trellis编码','经典：QuIP/QuIP#使用非相干处理与低比特编码，AQLM学习加性码本，QTIP用trellis组织高维编码。\n近期：StagQ（2026-10）用基础流和细化平面支持多精度；XOR-Trellis（首投2026-09-30）和CurveTQ（2026-10-06）研究降低解码或旋转成本。\n判断：这一分支不仅追求2位质量，也在回答“高维表示能否高效还原”。码本与trellis需要独立执行路径，不能默认接到普通整数矩阵核。',[paper('2402.04396'),paper('2401.06118'),paper('2406.11235'),paper('2610.05977'),paper('2610.00432'),paper('2610.09212')]),
('float','FP8、FP4与块尺度设计','经典：FP8 Quantization研究指数分配；ZeroQuant-FP和LLM-FP4探索更低浮点精度及尺度。\n近期：2026年MXFP系统评测指出算法与格式的兼容性；OSFP4（2026-10）联合优化NVFP4平滑与块尺度。\n判断：格式和尺度本身就是技术变量。INT4、NF4、FP4及NVFP4/MXFP4不应混排为同一种4位表示；原始格式与运行时执行格式需要分别登记。',[paper('2208.09225'),paper('2307.09782'),paper('2310.16836'),paper('2601.09555'),paper('2610.08231'),ASC]),
('joint','权重—激活联合低精度','经典与演进：SmoothQuant用等价缩放，旋转路线分散离群值，FlatQuant学习仿射变换来平坦化分布。\n归属：完整的激活误差、在线转换及W8A8/W4A4联合机制在激活专题展开；本页保留权重侧影响和入口。\n判断：联合方案不是两个对象各自收益的相加。离线可折叠变换与在线仍需执行的变换要分开核算。',[paper('2211.10438'),paper('2410.09426')]),
('execution','混合精度与执行协同','近期：AlignQuant（2026-10）把精度分配、压缩存储和GPU二维计算块统一起来，缓解细粒度精度边界与规则计算单元不一致的问题。\n产业关联：工具支持与运行时格式消费之间仍有转换、分组、打包及融合边界；官方FP8加载说明展示了同一检查点在不同代设备上的执行差别。\n判断：这是独立于“量化误差更小”的系统贡献。比较时需要完整运行栈与实际负载，不能仅比较权重文件。',[paper('2610.07457'),ASC]),
('recovery','低秩补偿与联合压缩','近期：Align, Then Correct（2026-10）对冻结主体附加两阶段闭式低秩校正；Differentiable Bit-Widths（2026-10）把SVD分量裁减与位宽学习联合起来。\n区别：前者增加补偿，后者改变保留分量与精度分配；1.61位联合压缩设置不是原生INT2矩阵乘。\n判断：两者关联量化与低秩专题，完整方案只能计一次质量收益；补偿支路与恢复成本不应隐藏在“权重位数”之外。',[paper('2610.08164'),paper('2610.06026')])]
CATALOG_EN=[
'Foundational: RTN, AWQ, GPTQ and OmniQuant cover rounding, channel scales, error compensation and learned clipping/transforms. Recent: ReQuant refines assignments on a fixed grid. Interpretation: compare error reduction at matched format and calibration budget, separating offline cost from runtime.',
'SpQR and SqueezeLLM handle difficult weights separately from a compressed main representation. This is neither ordinary uniform INT4 nor deletion of all side weights. Count side records, indices and scales alongside the main payload.',
'QuIP/QuIP#, AQLM and QTIP develop vector, additive and trellis coding. Recent StagQ supplies precision prefixes; XOR-Trellis (first submitted 2026-09-30) and CurveTQ (2026-10-06) address decoding or rotation costs. Dedicated reconstruction paths remain part of the system.',
'FP8 Quantization, ZeroQuant-FP and LLM-FP4 establish format/scale research. The 2026 MXFP benchmark and October OSFP4 extend it. Distinguish INT4, NF4, FP4, NVFP4 and MXFP4, and record storage versus execution formats separately.',
'SmoothQuant, rotations and FlatQuant transform W/A distributions. Full joint W8A8/W4A4 treatment belongs to the activation topic. Count joint gains once and distinguish folded offline transforms from online work.',
'October AlignQuant unifies allocation, packing and GPU tiles. Runtime format consumption, grouping and fusion are separate from algorithmic error reduction. Native FP8 loading illustrates hardware-dependent execution; assess full-stack workloads.',
'October Align, Then Correct adds closed-form corrections to a frozen backbone; Differentiable Bit-Widths jointly learns SVD pruning and precision. These are different operations. Include side branches and recovery costs and do not call a 1.61-bit joint setting native INT2.'
]
for n,(slug,title,body,ids) in enumerate(CATALOG):
    card('parameters-precision__landscape_'+slug,title,body,['Scales, clipping and rounding','Nonuniform and sparse-side representations','Vector codebooks and trellis coding','FP8, FP4 and block scales','Joint low-precision W/A','Mixed precision and execution co-design','Low-rank recovery and joint compression'][n],CATALOG_EN[n],section='comparison',position=90+n,sources=ids)

# Replace deployment-first advice in the precision matrix with conditional research interpretation.
JUDGMENTS=[
'已有基础｜INT8已有完整方法与工具生态；SmoothQuant是基础能力，不应自动列为新增研究课题。 ⟂ 技术增量｜研究重点转向不同配方的质量差异、跨核数值一致性与联合执行成本。 ⟂ 适用条件｜需要较温和的压缩或低精度计算时查阅这一档；更强容量压缩需求继续查W4/编码，而不是反复开发已有INT8算法。',
'已有基础｜FP8/MXFP8提供另一种数值范围与尺度组织，不能把它当作INT8权重的直接替代文件。 ⟂ 技术增量｜尺度格式、块尺寸与硬件执行决定实际收益。官方指南列：950PR/DT把所支持块量化FP8转为MXFP8执行；其他代设备会展开为模型浮点类型。 ⟂ 适用条件｜当研究浮点动态范围或相关硬件能力时选此分支。文件能加载不等于保持一字节权重驻留；具体支持以版本和模型为准。',
'已有基础｜AWQ/GPTQ是权重量化工具基线，先理解其通道缩放和误差补偿差异。 ⟂ 技术增量｜ReQuant关注固定网格再优化；AlignQuant关注混合精度与计算块对齐，分别回答质量与执行问题。 ⟂ 适用条件｜容量、权重读取或边缘部署需要更强压缩时查W4；按真实总存储与执行核比较，不能只看算法PPL或4位标签。',
'已有基础｜早期FP4研究与NVFP4/MXFP4产业格式并非同一配置。 ⟂ 技术增量｜OSFP4改善NVFP4的平滑/尺度联合选择；MXFP评测揭示其他块格式的误差来源。 ⟂ 适用条件｜相关FP4硬件、格式研究及低精度联合计算可从这里选方案；没有执行支持时仍可保留算法认识，不把GPU结果改写成昇腾收益。',
'已有基础｜QuIP#、AQLM、QTIP提供极低比特表示，通常带有码本、变换或专用解码。 ⟂ 技术增量｜StagQ提供多精度前缀，CurveTQ/XOR-Trellis降低编码/重构复杂度，低秩补偿恢复冻结主体的质量。 ⟂ 适用条件｜极限容量、多精度分发或编码研究分别查相应路线；既不能因当前业务不用就删掉，也不能把研究质量改进当成已可部署。']
for n,slug in enumerate(['int8','fp8','int4','fp4','two']):
    row=cards['parameters-precision__progress_'+slug].copy()
    fields=row['body_zh'].splitlines();fields[4]='技术判断：'+JUDGMENTS[n];row['body_zh']='\n'.join(fields)
    # English stays substantive while preserving the shared five-field representation.
    e=row['body_en'].splitlines();e[4]='Interpretation: '+[
      'Established INT8 algorithms are baselines, not automatic new research. Study recipe differences, kernel consistency and joint-execution cost; consult W4/codes for stronger capacity compression.',
      'Separate floating-point range, block scales and actual execution. The Ascend guide documents MXFP8 execution for supported block FP8 on 950PR/DT and expansion to model floating-point dtype on other generations; loading a checkpoint does not guarantee one-byte residency.',
      'AWQ/GPTQ are baselines. ReQuant addresses fixed-grid quality; AlignQuant addresses mixed-precision execution. Select by capacity/traffic needs, comparing total bytes and real kernels.',
      'Early FP4 differs from NVFP4/MXFP4. OSFP4 targets smoothing/scales; retain the research even without a matching execution platform, but do not transfer GPU gains to Ascend.',
      'Track extreme compression, multi-precision prefixes, decoder complexity and compensation separately. Current business demand must not remove research coverage; research improvement is not deployment proof.'
    ][n];row['body_en']='\n'.join(e);row['reviewed_at']='2026-10-23';changed.append(row)
    if slug in ['int8','fp8']:card(row['card_id'],row['title_zh'],row['body_zh'],row['title_en'],row['body_en'],sources=[MS,ASC])

write('ic_compression_topic_cards',changed,'card_id')
write('ic_compression_topic_card_refs',refs,'reference_id')
frames=[]
for item in load('ic_compression_research_frames'):
    r=item['row']
    if r.get('compression_topic_id')!='parameters-precision':continue
    r['why_zh']='本专题先建立权重量化的技术全景，再讨论应用条件。研究覆盖数值表示、校准/舍入、非均匀与稀疏旁路、码本/trellis、混合精度、低秩补偿及实际执行。\n共同问题是：减少权重位数后，如何控制误差、处理额外元数据，并让压缩表示被高效消费？相同位宽并不代表相同存储或执行成本。\n经典方法用于理解问题如何被提出，近期工作说明仍有哪些缺口；模型、硬件、业务与质量门槛作为检索和选型条件，不预先限定收录范围。'
    r['why_en']='Build a technical landscape before selecting applications. Cover formats, calibration/rounding, nonuniform and sparse-side representations, codebooks/trellises, mixed precision, compensation and execution.\nThe shared question is how to control error and metadata while executing compact representations efficiently. Equal bit counts do not mean equal storage or execution cost.\nFoundational work explains the problem; recent work exposes remaining gaps. Model, hardware and business thresholds are later retrieval/selection conditions, not collection filters.'
    frames.append(r)
write('ic_compression_research_frames',frames,'frame_id')
concepts=[]
for item in load('ic_compression_topic_concepts'):
    r=item['row'];t=r.get('compression_topic_id')
    if t=='parameters-precision':r.update(summary_zh='研究权重的低比特表示、误差控制与压缩格式执行；联合W/A方案与激活专题交叉关联。',summary_en='Low-bit weight representations, error control and executable formats; cross-link joint W/A schemes to activations.')
    elif t=='activations-precision':r.update(summary_zh='研究激活离群值、动态范围与在线尺度，主讲W8A8/W4A4等权重—激活联合计算。',summary_en='Activation outliers, ranges and online scaling; primary home for joint W8A8/W4A4 execution.')
    else:continue
    concepts.append(r)
write('ic_compression_topic_concepts',concepts,'concept_id')
sections=[]
revised={c['card_id']:c for c in changed}
for item in load('ic_compression_topic_sections'):
    r=item['row']
    if r.get('compression_topic_id')!='parameters-precision':continue
    suffix={'comparison':'3','boundary':'4','implication':'5','watch':'6'}.get(r['section_kind'])
    if suffix:
        c=revised['parameters-precision__dossier_'+suffix]
        r.update(body_zh=c['body_zh'],body_en=c['body_en'],heading_zh=c['title_zh'],reviewed_at='2026-10-23')
        sections.append(r)
write('ic_compression_topic_sections',sections,'section_id')
print('Research-first dossier updated: seven technical branches, scope ownership, conditional interpretation')
