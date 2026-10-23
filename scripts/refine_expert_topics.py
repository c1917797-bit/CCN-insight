"""Curated expert entry points. Uses existing evidence, without upgrading review depth."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/compression/tables'

# Four questions, answered specifically for each research direction.
BRIEFS = {
 'parameters-precision': (
  '量化的分水岭：误差更小，还是执行更有效',
  ['技术增量：AWQ/GPTQ改善固定低比特表示的误差；码本编码改变表示能力；AlignQuant一类系统工作还改变精度分工和执行。三类贡献分别比较。',
   '关键对照：相同模型与总字节预算下，先比较质量，再核对低比特权重是否直接进入计算核。尺度、码本、补偿支路和恢复预算都计入成本。',
   '阅读重点：AWQ案例看质量归因，GPTQ案例看硬件与卡数差异，Flint案例看前向解码和完整服务的区别；INT4、FP4、INT8、FP8不可只按位数互换。',
   '待解问题：更好的重建目标能否转化为任务收益？收益能否覆盖反量化和补偿开销？尚未报告的TTFT、长尾质量与目标平台结果需要单独补证。'],
  'Quantization: better error control or better execution?',
  ['Contribution: distinguish fixed-format error control, richer encodings and precision-aware execution.', 'Comparison: match total bytes and quality; count scales, codebooks, correction branches and recovery work.', 'Read: AWQ for quality attribution, GPTQ for device-count differences, Flint for forward versus serving latency. Integer and floating formats are distinct.', 'Open: establish task gains and full-path costs; missing TTFT, tail quality and target-platform results remain unproven.']),
 'parameters-selection': (
  '剪掉权重之后，哪些计算真的消失了',
  ['技术增量：Wanda用权重与输入激活评分选择待删项；SparseGPT进一步补偿剪枝造成的层输出误差。前者准备轻，后者研究误差恢复。',
   '关键对照：先在相同稀疏率和粒度下比较质量，再把非结构化稀疏、N:M稀疏和结构化删维分开看；它们需要的存储与执行路径不同。',
   '阅读重点：SparseGPT的大模型结果证明稀疏可行性，不等于硬件已经跳过相同比例计算；实际需要看到非零布局、索引和对应稀疏核。',
   '待解问题：质量可接受的稀疏模式是否正好可被目标算子消费？相同总字节下，它相对低比特量化是否仍有价值？'],
  'After pruning, which work actually disappears?',
  ['Contribution: Wanda scores with weights and activations; SparseGPT also compensates layer-output error.', 'Comparison: match sparsity and granularity; separate unstructured, N:M and structural pruning.', 'Read: large-model sparsity establishes feasibility, not proportional hardware speedup. Inspect layout, indices and sparse kernels.', 'Open: can useful patterns execute efficiently, and do they beat quantization at matched total bytes?']),
 'parameters-distillation': (
  '蒸馏的贡献，要在同一个学生上识别',
  ['技术增量：蒸馏改变训练信号和能力迁移；学生的结构、参数量与执行方式决定推理成本。更小学生更快，不足以单独证明蒸馏有效。',
   '关键对照：固定学生、数据与训练预算，对比常规训练、教师输出监督和表征监督；现成小模型另作部署候选，不混为严格算法消融。',
   '阅读重点：MiniLLM关注生成分布与反向KL目标；特征监督关注教师与学生的表示对齐。白盒概率、黑盒响应和中间特征对应不同访问条件。',
   '待解问题：平均分改善是否掩盖长推理或难例退化？教师访问、数据生成和训练投入能否由学生的长期使用节省覆盖？'],
  'Measure distillation on the same student',
  ['Contribution: supervision transfers capability; student structure and execution determine inference cost.', 'Comparison: fix student, data and training budget. Keep off-the-shelf deployment alternatives separate from causal ablations.', 'Read: MiniLLM addresses generated distributions and reverse KL; feature supervision requires compatible representations and access.', 'Open: inspect reasoning tails and total teacher/data/training costs against long-term inference savings.']),
 'parameters-factorization': (
  '低秩压缩的关键，是保留哪些方向',
  ['技术增量：普通SVD最小化矩阵重建误差；ASVD与SVD-LLM把输入分布和层输出误差纳入分解。只保留最大的奇异值，不一定最有利于任务。',
   '关键对照：统一因子总字节、逐层秩和恢复预算，对比截断SVD、激活感知分解及恢复策略。低秩补偿支路与完整权重替换分开记账。',
   '阅读重点：W约为UV时，只有r(m+n)小于mn才减少因子参数；执行还增加中间张量和一次矩阵乘启动，参数减少不保证时延减少。',
   '待解问题：层间如何分配秩更稳健？因子形状与运行核是否匹配？校准分布变化后，质量优势还能保持多少？'],
  'Low rank: which directions should survive?',
  ['Contribution: activation-aware factorization targets output-relevant error rather than matrix error alone.', 'Comparison: match factor bytes, layer ranks and recovery work; separate replacement from correction branches.', 'Read: r(m+n) must be below mn for factor-parameter savings; two matrix products add intermediate and launch costs.', 'Open: validate rank allocation, executable factor shapes and calibration-shift robustness.']),
 'activations-precision': (
  '激活量化的难点，是输入变化时仍能控误差',
  ['技术增量：SmoothQuant迁移权重与激活间的量化难度；QuaRot用旋转分散离群值；SpinQuant进一步学习旋转。它们不是三个可直接按位宽排名的配置。',
   '关键对照：锁定W/A配置、粒度和敏感层精度，分别记录缩放、旋转与学习的质量增量，以及离线学习和在线变换成本。',
   '阅读重点：全精度等价变换不保证量化无损；联合W/A/KV结果不能拆成激活单项收益。动态尺度与旋转需要进入完整执行路径。',
   '待解问题：校准样本之外的离群分布是否稳定？长生成、低能量音频和不同语言的激活变化，会不会暴露平均分未覆盖的失效？'],
  'Activation quantization must handle changing inputs',
  ['Contribution: SmoothQuant rescales difficulty; QuaRot redistributes outliers; SpinQuant learns rotations.', 'Comparison: fix W/A precision, granularity and sensitive layers; measure offline and online transformation costs.', 'Read: full-precision equivalence does not imply quantized losslessness. Joint results do not isolate activation gains.', 'Open: test calibration shift, long generation and task-specific activation tails.']),
 'activations-selection': (
  'Token变少，必须同时保住信息并跳过计算',
  ['技术增量：按任务相关性保留token，可减少后续计算；评分、回收与紧缩序列决定是否能把逻辑删除变成实际执行缩减。',
   '关键对照：固定输入、选择层与token预算，对比直接删除和信息回收；质量、评分开销、重排开销与完整时延一起看。',
   '阅读重点：SparseVLM的视觉证据保留在视觉任务范围；精细OCR、小目标、计数和多图需求需要分别观察，不能外推为文本或音频帧可删。',
   '待解问题：评分会不会删掉后续任务真正需要的信息？掩码之后是否仍调用原尺寸稠密核？这两项分别决定质量与性能价值。'],
  'Fewer tokens must preserve information and skip work',
  ['Contribution: task-aware selection reduces downstream work only through executable compaction or sparsity.', 'Comparison: fix input, selection layer and budget; compare deletion with information recovery and all overheads.', 'Read: visual evidence is modality-specific; inspect OCR, small objects, counting and multiple images separately.', 'Open: test information lost for later tasks and whether masked tokens still consume dense computation.']),
 'activations-merging': (
  '合并比删除多保留了什么，代价又是多少',
  ['技术增量：合并把多个token的信息聚合到更少表示中；其价值应体现为同token预算下，相比直接删除保留更多任务相关信息。',
   '关键对照：固定合并位置与预算，分别比较删除、匹配聚合和回收策略；匹配、聚类、位置处理及后续算子均计入时延。',
   '阅读重点：PruMerge把选择与聚类信息结合。当前证据以摘要为主，具体匹配规则、输入分辨率、微调条件及细粒度失败尚需正文核对。',
   '待解问题：聚合是否破坏局部细节、位置与时序？在高分辨率、多图或视频中，质量保留能否覆盖匹配与聚合成本？'],
  'What does merging retain beyond deletion?',
  ['Contribution: aggregation should retain more useful information than deletion at the same token budget.', 'Comparison: fix merge positions and count selection, clustering, positional handling and downstream costs.', 'Read: PruMerge combines selection with clustering; current abstract-level evidence leaves important implementation conditions open.', 'Open: examine local detail, spatial/temporal order and net gains at higher resolution or multiple images.']),
 'activations-factorization': (
  '注意力近似，先回答近似了什么',
  ['技术增量：Linformer沿序列维投影K/V；Nyströmformer借助landmark近似注意力。这里改变注意力表示与计算，不是简单给中间张量降位宽。',
   '关键对照：扫描投影维度或landmark数，同时报告任务质量、完整模块时延与工作区；与融合精确注意力比较，而非只与显式大矩阵基线比较。',
   '阅读重点：已有代表证据主要来自编码器任务。因果解码需要额外解决可见性、增量更新和KV管理，不能把编码器结果当成冻结LLM替换方案。',
   '待解问题：近似预算能否随任务变化？精确融合核已经避免大矩阵物化时，近似方案还剩多少净优势？'],
  'Attention approximation: what is being approximated?',
  ['Contribution: sequence projections and landmark approximations alter attention representations and computation.', 'Comparison: sweep approximation budgets against fused exact attention; record task quality, full latency and workspace.', 'Read: encoder evidence does not establish causal decoding, incremental-state or frozen-LLM compatibility.', 'Open: quantify advantages remaining after exact fusion and robustness to task-dependent budgets.']),
 'activations-distillation': (
  '特征监督是恢复手段，紧凑结构才改变激活规模',
  ['技术增量：TinyBERT以浅窄学生和多阶段监督保留能力；MobileBERT以较深的窄瓶颈组织计算。结构缩小与监督贡献需要分开。',
   '关键对照：先固定学生结构比较不同监督，再扫描深度、宽度或瓶颈。记录实际中间张量与生命周期，不用层宽直接替代峰值激活内存。',
   '阅读重点：教师—学生隐藏维度不同时，对齐投影本身有成本；编码器NLU质量不能证明冻结自回归LLM的激活可无损缩小。',
   '待解问题：特征对齐比输出监督多保留哪些能力？训练期辅助投影是否移除？部署图与完整激活内存是否真正缩减？'],
  'Feature supervision recovers quality; structure shrinks states',
  ['Contribution: compact student architecture and supervision play different roles in TinyBERT and MobileBERT.', 'Comparison: fix the student before varying supervision; inspect actual tensors and lifetimes, not width alone.', 'Read: alignment projections have costs; encoder quality is not evidence for shrinking frozen autoregressive states.', 'Open: identify additional retained capabilities, removed training-only branches and measured deployment-state savings.']),
 'kv_cache-precision': (
  'KV低比特的价值，取决于如何写入和读取',
  ['技术增量：KIVI按K/V分布采用不同量化轴并保留高精度残留；QJL以Key sketch和内积估计探索另一种表示。一个缓存位宽不能描述完整配方。',
   '关键对照：固定总缓存字节和请求轨迹，记录K/V位宽、分组轴、scale、残留窗口与重建工作区；分别看同并发时延与扩大并发后的吞吐。',
   '阅读重点：KIVI的总峰值内存、可容纳batch和吞吐采用不同口径。QJL标题中的1-bit不代表整个K/V缓存及元数据都为1-bit。',
   '待解问题：压缩布局能否被注意力核直接读取？长检索与长生成是否稳定？每步全量展开缓存可能抵消带宽节省。'],
  'Low-bit KV depends on the read/write path',
  ['Contribution: KIVI uses distinct K/V axes and residuals; QJL explores key sketches and inner-product estimation.', 'Comparison: match total bytes and requests; count scales, residuals and workspace. Separate fixed-concurrency latency from scaled-batch throughput.', 'Read: peak model memory, batch capacity and throughput use different denominators. Key-sketch bits are not whole-cache bits.', 'Open: inspect direct compressed reads and long-context robustness; repeated full expansion can erase bandwidth gains.']),
 'kv_cache-kv_eviction': (
  '驱逐缓存，是对未来查询价值的一次押注',
  ['技术增量：H2O、SnapKV与PyramidKV在评分信号、选择时机和预算分配上不同；DuoAttention还按头区分需要完整历史的范围。',
   '关键对照：对齐实际物理缓存预算和相同后续请求，保留评分、gather、重排与页回收成本；逻辑token减少不代表物理内存已经释放。',
   '阅读重点：长检索、后续追问与长生成检验不同的信息需求。单针检索接近满分，不足以证明多事实整合和多轮对话也稳定。',
   '待解问题：未来查询能否恢复被驱逐的信息？预算在层与头之间如何分配更稳健？GQA下逐Query头预算是否产生重复计算或口径错误？'],
  'Eviction makes a prediction about future queries',
  ['Contribution: methods differ in scoring, timing, allocation and head-specific history requirements.', 'Comparison: match physical bytes and future requests; include scoring, gathers, reordering and page reclamation.', 'Read: retrieval, follow-up questions and long generation test distinct information needs; single-needle accuracy is insufficient.', 'Open: examine recoverability, robust layer/head allocation and budget consistency under GQA.']),
 'kv_cache-selection': (
  '剪KV通道，与删历史Token是两件事',
  ['技术增量：ThinK按查询相关性压缩Key的特征通道，保留近期完整Key；它改变的是特征维度，而非仅改变历史token数量。',
   '关键对照：分别锁定通道数、token数、位宽与近期窗口，对比单项剪枝、单项量化和组合；联合收益不能全部记在通道剪枝名下。',
   '阅读重点：ThinK+KIVI的峰值内存与batch容量是联合配置结果。压缩历史Key和完整近期Key并存，需要与两路布局相匹配的注意力实现。',
   '待解问题：观察窗口选出的通道能否服务后续查询？Key的选择规则能否迁移到Value？数据整理与掩码成本是否覆盖了节省？'],
  'Pruning KV channels is not deleting historical tokens',
  ['Contribution: ThinK prunes query-relevant key features while retaining complete recent keys.', 'Comparison: isolate channel count, token count, precision and recent windows; separate pruning, quantization and their combination.', 'Read: joint ThinK/KIVI capacity results do not isolate pruning gains; historical and recent layouts require compatible execution.', 'Open: test future-query robustness, value-cache applicability and data-layout overheads.']),
 'kv_cache-factorization': (
  '低维缓存，不能靠每步完整重建来评价',
  ['技术增量：事后低秩转换压缩已有投影或缓存；原生MLA从架构上缓存latent及解耦RoPE key。二者的训练需求和算子路径不同。',
   '关键对照：记录rank、latent、RoPE分支、近期完整段与临时张量，用相同总状态预算比较质量，再看能否在低维空间直接计算。',
   '阅读重点：ASVD的转换结果与DeepSeek-V2的原生MLA分别解读。DeepSeek-V2整模型吞吐还受MoE及系统优化影响，不能归因于低秩缓存一项。',
   '待解问题：RoPE、增量更新和直接消费因子能否兼容？rank变化时，质量收益与重建开销各自怎样变化？'],
  'Low-dimensional caches need a viable execution path',
  ['Contribution: post-hoc conversion and native MLA differ in training and execution requirements.', 'Comparison: count latent states, RoPE branches, recent windows and temporary tensors; test direct low-dimensional computation.', 'Read: separate ASVD conversion from native MLA. Whole-model DeepSeek-V2 throughput does not isolate cache factorization.', 'Open: check RoPE, incremental updates, rank-dependent quality and reconstruction overhead.']),
 'kv_cache-sharing': (
  'GQA/MQA是缓存基线，不是可重复计入的收益',
  ['技术增量：多个Query头共享较少KV头，降低每token状态及重复读取；共享越多并不自动保持相同模型质量。',
   '关键对照：先登记真实Query头、KV组与单头维度。已有GQA模型上的量化、淘汰等方案，只计算相对此基线的额外收益。',
   '阅读重点：GQA论文的MHA转化包含uptraining；直接部署原生检查点与转换已有模型，是不同的投入和质量问题。',
   '待解问题：更少KV组能否在质量门槛内获得净收益？缓存字节减少后，注意力核是否仍受其他访存或计算限制？'],
  'GQA/MQA define the baseline, not repeatable savings',
  ['Contribution: shared KV heads reduce state and repeated reads with a quality trade-off.', 'Comparison: record actual query heads, KV groups and head dimensions; measure extra compression against the existing architecture.', 'Read: MHA-to-GQA conversion includes uptraining and differs from deploying a native checkpoint.', 'Open: evaluate quality at fewer groups and identify remaining execution bottlenecks after state reduction.']),
 'kv_cache-compact_architecture': (
  '紧凑架构先定状态形态，后续压缩再算增量',
  ['技术增量：GQA/MQA减少KV头数；MLA改变缓存表示维度。它们决定原生状态结构，是运行期量化与淘汰的起点。',
   '关键对照：同时记录模型能力、每token状态元素、缓存精度和执行路径。不同原生模型之间可比较部署取舍，但不能声称是单模块严格消融。',
   '阅读重点：DeepSeek-V2的缓存与整模型性能结果有不同归因范围；共享结构、latent缓存和训练改变不能合成一条通用压缩倍数榜单。',
   '待解问题：原生紧凑检查点是否满足所需能力？若转换旧模型，质量恢复、RoPE兼容及新算子投入是否值得？'],
  'Compact architectures define states before runtime compression',
  ['Contribution: head sharing and latent caching set different native state structures.', 'Comparison: retain capability, state elements per token, precision and execution; cross-model trade-offs are not controlled module ablations.', 'Read: separate cache capacity from whole-model throughput and architectural/training changes.', 'Open: assess native checkpoint capability versus the recovery, RoPE and kernel costs of conversion.']),
 'kv_cache-distillation': (
  '先看学生的KV结构，再看蒸馏恢复了什么',
  ['技术增量：紧凑KV学生先通过结构减少状态，教师监督再恢复能力；蒸馏本身不决定缓存比例。',
   '关键对照：固定学生结构、缓存预算与训练数据，比较CE、KL及其他训练步骤；不同教师和训练量的结果不能直接相减。',
   '阅读重点：X-EcoMLA的整体结果与小数据消融采用不同设置。蒸馏、初始化、数据和DPO各自的贡献，应在对应表内辨认。',
   '待解问题：同状态预算下，监督比直接训练多保留哪些能力？收益是否覆盖教师与训练投入？新缓存结构是否有可用的执行路径？'],
  'Inspect student KV structure before recovery claims',
  ['Contribution: architecture sets state size; teacher supervision recovers capability.', 'Comparison: fix student, cache budget and data before comparing CE, KL and additional training stages.', 'Read: X-EcoMLA overall results and smaller-data ablations use different settings; keep their attributions separate.', 'Open: quantify extra retained capability, total training inputs and executable student-cache support.']),
}

def load(table):
 return [json.loads(x) for x in (BASE/table/'rows.jsonl').read_text(encoding='utf-8').splitlines()]

def save(table, records):
 (BASE/table/'rows.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in records),encoding='utf-8')

def main():
 cards, refs = load('ic_compression_topic_cards'), load('ic_compression_topic_card_refs')
 sources = {x['row']['source_id']:x['row'] for x in load('cloud_core_sources') if not x['deleted']}
 # Fix a known cross-source scope leak. Reuse a real source-specific locator only.
 fixed=0
 for entry in refs:
  r=entry['row']
  if entry['deleted'] or 'Flint：' not in r['locator_zh'] or 'flint' in sources[r['source_id']]['canonical_url'].lower():continue
  candidates=[x['row'] for x in refs if not x['deleted'] and x['row']['source_id']==r['source_id'] and 'Flint：' not in x['row']['locator_zh'] and x['row']['card_id'].startswith('parameters-precision__')]
  candidates.sort(key=lambda x:(x['review_depth']=='section_review','__case_' in x['card_id'] or '__audit_' in x['card_id'],x['checked_at']),reverse=True)
  if candidates:
   best=candidates[0]
   for k in ['locator_zh','locator_en','observed_version','checked_at','review_depth']:r[k]=best[k]
  else:
   r.update(review_depth='abstract_review',observed_version='current_abstract',locator_zh='摘要；综合判断为编辑分析，具体实验章节待核对。',locator_en='Abstract; editorial interpretation. Specific experimental sections remain to be checked.')
  entry['row_version']+=1;fixed+=1
 index={x['key']:x for x in cards}
 for topic,(zh,lines,en,enlines) in BRIEFS.items():
  key=topic+'__expert_brief'
  row=dict(business_id='cloud-core',topic_id='cloud_core',compression_topic_id=topic,card_id=key,title_zh=zh,title_en=en,body_zh='\n'.join(lines),body_en='\n'.join(enlines),position=108,reviewed_at='2026-10-23',section_kind='comparison',card_kind='analysis',claim_kind='research_analysis')
  if key in index:
   if index[key]['row']!=row:index[key]['row']=row;index[key]['row_version']+=1
  else:cards.append(dict(key=key,row=row,row_version=1,deleted=False,text_match=None))
  if not any(x['row']['card_id']==key for x in refs):
   bound=[x['row'] for x in refs if not x['deleted'] and x['row']['compression_topic_id']==topic and (x['row']['card_id'].endswith('__dossier_5') or '__case_' in x['row']['card_id'])]
   selected={}
   for r in bound:
    # Business example config is not evidence for a root-mechanism comparison.
    if 'qwen38-context' in r['reference_id']:continue
    old=selected.get(r['source_id'])
    if old is None or (r['review_depth']=='section_review' and old['review_depth']!='section_review'):selected[r['source_id']]=r
   assert selected,topic
   for sid,ref in selected.items():
    new={**ref,'card_id':key,'reference_id':key+'__'+sid}
    refs.append(dict(key=new['reference_id'],row=new,row_version=1,deleted=False,text_match=None))
 save('ic_compression_topic_cards',cards);save('ic_compression_topic_card_refs',refs)
 print(f'Expert briefs: {len(BRIEFS)} topics; corrected {fixed} cross-source locators. Existing review depths preserved.')

if __name__=='__main__':main()
