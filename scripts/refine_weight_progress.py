"""Canonical, source-linked weight precision landscape; local review only."""
import json
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/compression/tables'
def read(t):return [json.loads(x) for x in (BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()]
def save(t,items):
 p=BASE/t/'rows.jsonl';rows=read(t);index={r['key']:i for i,r in enumerate(rows)}
 for row in items:
  k=row[{'ic_compression_topic_cards':'card_id','ic_compression_topic_card_refs':'reference_id','cloud_core_sources':'source_id'}[t]]
  if k in index:
   old=rows[index[k]]
   if old['row']==row:continue
   rows[index[k]]={**old,'row':row,'row_version':old['row_version']+1}
  else:rows.append(dict(key=k,row=row,row_version=1,deleted=False,text_match=None))
 p.write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')
sources=read('cloud_core_sources')
def sid(url):return next(r['row']['source_id'] for r in sources if r['row']['canonical_url']==url)
extra=[('source-wq-progress-vllm-fp8','https://docs.vllm.ai/en/v0.30.0/features/quantization/fp8/','vLLM v0.30.0 · FP8 W8A8'),('source-wq-progress-trt','https://nvidia.github.io/TensorRT-LLM/latest/features/quantization.html','TensorRT-LLM · Quantization configurations')]
save('cloud_core_sources',[dict(source_id=i,business_id='cloud-core',batch_id='weight-progress-20261023',canonical_url=u,external_id='',last_checked_at='2026-10-23',provider=urlparse(u).netloc,source_kind='official_documentation',title=t,update_policy='follow_original_url_record_versions',verification_status='primary_selected_sections_checked') for i,u,t in extra])
rows=[
('int8','W8 · INT8',[
'整数网格；常见 W8A8，也可能 W8A16。W、A 分别表示权重和激活位宽，仍须查看真实数据类型。',
'已有模型级部署示例。vLLM-Ascend 为 Qwen3.8-27B 提供普通 W8A8 权重；领域模型需另核对自身算子与导出链。',
'基础方法：SmoothQuant（ICML 2023）用等价通道缩放缓解激活离群值，促成 INT8 W8A8；它不是本月新论文。',
'本专题既有教程记录：GPQA Diamond 90.40→89.90，下降0.50个百分点（相对约0.55%）；不能据此认定所有业务精度损失均小于1%。',
'优先复现匹配设备的 INT8 路径。固定业务集，比较浮点与 W8A8 的质量、TTFT、TPOT、吞吐和峰值内存。'],['source-wq-vllm-qwen38-27b',sid('https://arxiv.org/abs/2211.10438')]),
('fp8','W8 · FP8 / MXFP8',[
'浮点编码；FP8 的 E4M3、E5M2 指数/尾数分配不同。MXFP8 另规定分块共享尺度，不能与 INT8 权重直接互换。',
'vLLM 已有 FP8 W8A8 路径；部分较早 GPU 使用 W8A16 回退。昇腾教程另列 MXFP8 权重及950DT/PR要求。',
'研究重点是离群值、分块尺度和执行开销的平衡。本次核对了工程文档，未新增经原文核验的10月 FP8 专属论文；不将 INT8 论文当成 FP8 新进展。',
'位宽相同不代表精度或性能相同。普通 FP8、MXFP8 及不同块尺寸必须分别记录；KV Cache 支持 FP8 不等于矩阵乘采用 FP8。',
'950子型号确认后再选路径；310P、910B不沿用950的MXFP8结论。与 INT8 做同模型同负载比较，不能只比较量化文件大小。'],['source-wq-progress-vllm-fp8','source-wq-vllm-qwen38-27b']),
('int4','W4 · INT4',[
'4位整数权重；常见 W4A16 保留16位激活。AWQ、GPTQ 是误差控制算法，并非另一种数值格式。',
'TensorRT-LLM 列出 W4A16 AWQ/GPTQ 路径。分组大小、打包格式与后端决定能否执行；不能把GPU权重直接视为昇腾可用。',
'基础路线：AWQ 按激活重要性缩放通道，GPTQ 按近似二阶信息补偿误差。进一步研究应同时优化质量与核函数兼容性，而非只降低重建误差。',
'纯权重载荷相对16位理论减少75%，但尺度、零点、未量化层和运行内存另计；这不是整模型内存下降75%或提速4倍的实测结论。',
'当 INT8 容量收益不足时，先核对目标设备的INT4执行链，再比较 RTN/AWQ/GPTQ；记录分组、保留层和实际矩阵核。'],['source-wq-progress-trt',sid('https://arxiv.org/abs/2306.00978'),sid('https://arxiv.org/abs/2210.17323')]),
('fp4','W4 · FP4（区分 NVFP4 / MXFP4）',[
'4位浮点与块尺度配合；NVFP4、MXFP4 的尺度方案不同。W4标签本身不能说明激活为4位还是16位。',
'TensorRT-LLM 分别列出 NVFP4、MXFP4；支持取决于硬件、模型和后端。不能用其 NVIDIA 支持证明昇腾已有相同路径。',
'本月代表：OSFP4（2026-10-06）联合优化通道平滑与块尺度，直接减少 NVFP4 矩阵乘量化误差，回应低位宽下尺度选择难题。',
'论文摘要报告：在所测工作负载中保留厂商 NVFP4 预填充吞吐的约94–97%；不是相对BF16提速94–97%。摘要未给出TTFT、TPOT，本表不补写。',
'作为方法研究候选：学习联合优化目标；只有目标硬件/运行栈具备相应FP4路径时才启动部署验证。当前不列为昇腾即用方案。'],['source-wq-progress-trt',sid('https://arxiv.org/abs/2610.08231')]),
('two','W2 · 2-bit 编码 / 码本',[
'2位基础码不等于通用 INT2 算子。分组仿射、向量码本、稀疏旁路等方案有不同解码与元数据成本。',
'本次选取的工程依据不足以确认310P、910B或950已有这两篇方法的完整执行链；定位为容量受限时的研究候选。',
'基础方法 QuIP#：Hadamard变换＋向量码本＋恢复微调。本月 StagQ：2位分组仿射基础流＋1位细化平面，让同一份权重提供多个精度档。',
'StagQ在Llama-3.1-8B、Phi-4、OLMo-2-7B的2位设置，比所比多精度基线高3.1–7.0个MMLU点；其A100单批合成矩阵核实验不是端到端TTFT/TPOT。',
'只有W4仍放不下且允许转换/恢复成本时优先穿刺。先验证解码核，再测业务质量；码本、旁路和恢复训练计入成本，不承诺精度损失小于1%。'],[sid('https://arxiv.org/abs/2402.04396'),sid('https://arxiv.org/abs/2610.05977')])]
# Keep format research distinct from deployment support and label mixed precision explicitly.
fp8id='source-wq-progress-fp8-exponent'
save('cloud_core_sources',[dict(source_id=fp8id,business_id='cloud-core',batch_id='weight-progress-20261023',canonical_url='https://arxiv.org/abs/2208.09225',external_id='2208.09225',last_checked_at='2026-10-23',provider='arxiv.org',source_kind='paper',title='FP8 Quantization: The Power of the Exponent',update_policy='follow_original_url_record_versions',verification_status='primary_abstract_checked')])
rows[1][2][2]='基础研究《FP8 Quantization》解释如何按离群值分配指数/尾数位，并优化尺度。本期未纳入经原文核验的新增FP8专属论文；不以训练或KV量化论文充当权重量化进展。'
rows[1][3].append(fp8id)
rows[2][2][2]='AWQ 缩放重要通道，GPTQ 补偿层输出误差。10月相关进展 AlignQuant 将精度分配与GPU二维计算块对齐；它是混合精度方案，不能当成固定INT4。'
rows[2][3].append(sid('https://arxiv.org/abs/2610.07457'))
EN=[
['Integer grid; W8A8 and W8A16 differ in activation precision. Bit counts alone do not determine data types.','The Ascend Qwen3.8-27B tutorial supplies W8A8 weights. Domain models require their own operator and export checks.','Foundational: SmoothQuant (ICML 2023) uses equivalent channel scaling to mitigate activation outliers for INT8 W8A8; not an October paper.','Previously reviewed tutorial: GPQA Diamond 90.40 to 89.90, down 0.50 percentage points (about 0.55% relative). This does not establish business acceptance.','Reproduce the device-matched INT8 path; compare task quality, TTFT, TPOT, throughput and peak memory against floating point.'],
['FP8 E4M3 and E5M2 divide exponent and mantissa bits differently; MXFP8 adds block-shared scaling. These are not interchangeable INT8 checkpoints.','vLLM documents FP8 W8A8 and W8A16 fallback paths on selected GPUs. The Ascend tutorial lists MXFP8 on 950DT/PR.','Foundational FP8 Quantization studies exponent allocation and scale optimization. No newly verified October FP8-specific weight paper was added in this review.','Equal bit width does not imply equal quality or speed. Record format and block size; FP8 KV-cache support is not proof of FP8 GEMM execution.','Confirm the 950 subtype first. Do not extend its MXFP8 support to 310P or 910B. Compare against INT8 at matched workloads.'],
['4-bit integer weights; W4A16 retains 16-bit activations. AWQ and GPTQ are algorithms, not data formats.','TensorRT-LLM lists W4A16 AWQ/GPTQ paths. Group size, packing and backend determine compatibility; GPU checkpoints are not proof of Ascend support.','AWQ scales salient channels; GPTQ compensates output error. October AlignQuant aligns mixed precision with GPU tiles; it is not a fixed-INT4 result.','Uniform 4-bit raw weights are theoretically 75% smaller than 16-bit weights. Metadata, unquantized layers and runtime memory remain additional costs.','When INT8 capacity is insufficient, confirm INT4 execution first; then compare RTN, AWQ and GPTQ with matched groups and preserved layers.'],
['4-bit floating point with block scales; NVFP4 and MXFP4 have different scale schemes. W4 alone does not specify activation precision.','TensorRT-LLM lists NVFP4 and MXFP4 separately. Support depends on hardware, model and backend; NVIDIA support does not prove Ascend support.','October OSFP4 jointly optimizes smoothing and block scales to reduce NVFP4 matrix-product quantization error.','The abstract reports 94–97% of vendor NVFP4 prefill throughput on measured workloads, not a 94–97% gain over BF16. TTFT and TPOT are not given in the abstract.','Study the optimization objective; deployment testing requires a matching FP4 execution path. Not an immediately deployable Ascend recommendation.'],
['A 2-bit code is not proof of a generic INT2 operator. Affine groups, vector codebooks and sparse side records have different decoding costs.','The selected sources do not establish complete QuIP# or StagQ execution paths on 310P, 910B or 950. Treat them as research candidates.','QuIP# combines Hadamard transforms, vector codebooks and recovery fine-tuning. October StagQ uses a 2-bit affine base plus 1-bit refinement planes.','At 2 bits, StagQ gains 3.1–7.0 MMLU points over compared multi-precision baselines on Llama-3.1-8B, Phi-4 and OLMo-2-7B. Its synthetic A100 kernel test is not end-to-end TTFT/TPOT.','Prioritize only if W4 is still too large and conversion/recovery costs are acceptable. Validate decoding and quality; count codebook and side-record costs.']]
# Academic coverage: foundational mechanisms and dated recent research are both explicit.
PAPERS=[
('2208.07339','LLM.int8(): 8-bit Matrix Multiplication for Transformers at Scale'),
('2608.13756','The Integer Alibi: Localizing Cross-Kernel Divergence in INT8-Quantized LLM Inference'),
('2601.09555','Benchmarking Post-Training Quantization of Large Language Models under Microscaling Floating Point Formats'),
('2307.09782','ZeroQuant-FP: A Leap Forward in LLMs Post-Training W4A8 Quantization Using Floating-Point Formats'),
('2310.16836','LLM-FP4: 4-Bit Floating-Point Quantized Transformers'),
('2608.07019','ReQuant: Fixed-Grid Discrete Refinement for Post-Training Quantization'),
('2307.13304','QuIP: 2-Bit Quantization of Large Language Models With Guarantees'),
('2401.06118','Extreme Compression of Large Language Models via Additive Quantization'),
('2610.08164','Align, Then Correct: Training-Free Two-Stage Low-Rank Compensation for Extremely Quantized Large Language Models'),
('2610.06026','Differentiable Bit-Widths: Co-optimizing Pruning and Quantization via SVD for Ultra-Efficient LLM Compression')]
existing={r['row']['canonical_url']:r['row']['source_id'] for r in read('cloud_core_sources') if not r['deleted']}
new=[]
for arxiv,title in PAPERS:
 url='https://arxiv.org/abs/'+arxiv
 if url not in existing:
  i='source-wq-academic-'+arxiv.replace('.','-');existing[url]=i
  new.append(dict(source_id=i,business_id='cloud-core',batch_id='weight-academic-20261023',canonical_url=url,external_id=arxiv,last_checked_at='2026-10-23',provider='arxiv.org',source_kind='paper',title=title,update_policy='follow_original_url_record_versions',verification_status='primary_abstract_checked'))
save('cloud_core_sources',new)
def paper_id(arxiv):return existing['https://arxiv.org/abs/'+arxiv]
ACADEMIC_ZH=[
'经典方法｜LLM.int8()（2022）：将离群特征送入16位分支，其余用INT8；SmoothQuant（2023）：用等价缩放平滑激活离群值。 ⟂ 近期进展｜The Integer Alibi（2026-08）：定位跨核输出差异；AlignQuant（2026-10）：让混合位宽权重与计算块对齐，执行时展开为INT8配合8位激活。后者不是纯W8方案。',
'经典方法｜FP8 Quantization（2022）：研究指数/尾数分配与尺度；ZeroQuant-FP（2023）：研究FP8激活、FP4权重及尺度对齐，属于W4A8交叉路线。 ⟂ 近期进展｜MXFP PTQ Benchmark（2026-01）：覆盖7种以上算法、15个基准、3类LLM；所测MXFP8接近浮点质量，MXFP4更难。该研究不是10月新论文，也不保证任意模型无损。',
'经典方法｜GPTQ（2022）：用近似二阶信息补偿误差；AWQ（2023）：按激活重要性缩放通道，服务低比特权重部署。 ⟂ 近期进展｜ReQuant（2026-08）：保持原量化网格，反复优化整数分配；AlignQuant（2026-10）：统一混合精度分配、打包和GPU计算块，缓解“压得小却跑不快”。混合精度不等于固定INT4。',
'经典方法｜ZeroQuant-FP（2023）：探索FP4权重与FP8激活；LLM-FP4（2023）：搜索指数位/裁剪范围，并以重参数化处理通道尺度。早期FP4不等于NVFP4/MXFP4。 ⟂ 近期进展｜MXFP PTQ Benchmark（2026-01）指出MXFP4尺度误差；OSFP4（2026-10）联合优化平滑与NVFP4块尺度。二者格式不同，不能互换权重或实测结论。',
'经典方法｜QuIP（2023）：非相干变换与自适应舍入；QuIP#（2024）：Hadamard变换＋向量码本＋恢复微调；AQLM（2024）：输入感知加性码本与块级联合优化。 ⟂ 近期进展｜StagQ（2026-10）：2位基础流＋细化平面；Align, Then Correct（2026-10）：两阶段低秩补偿；Differentiable Bit-Widths（2026-10）：联合SVD裁减与位宽学习，1.61位是联合压缩设置，不是原生INT2。']
ACADEMIC_EN=[
'Foundational｜LLM.int8() (2022) isolates outlier features into a 16-bit branch; SmoothQuant (2023) smooths activation outliers with equivalent scaling. ⟂ Recent｜The Integer Alibi (Aug 2026) localizes cross-kernel divergence. AlignQuant (Oct 2026) aligns mixed-bit weights with compute tiles, expanding them for INT8 computation with 8-bit activations; it is not uniform W8.',
'Foundational｜FP8 Quantization (2022) studies exponent/mantissa allocation and scales. ZeroQuant-FP (2023) studies FP8 activations, FP4 weights and scale alignment: a cross-format W4A8 route. ⟂ Recent｜The MXFP PTQ Benchmark (Jan 2026) covers over 7 algorithms, 15 benchmarks and 3 LLM families. MXFP8 was near-lossless in its tests, whereas MXFP4 remained difficult. It is not an October paper or a universal guarantee.',
'Foundational｜GPTQ (2022) uses approximate second-order error compensation; AWQ (2023) scales salient channels for low-bit weight deployment. ⟂ Recent｜ReQuant (Aug 2026) refines integer assignments on the original grid. AlignQuant (Oct 2026) aligns mixed-precision allocation, packing and GPU tiles. Mixed precision is not fixed INT4.',
'Foundational｜ZeroQuant-FP (2023) explores FP4 weights with FP8 activations. LLM-FP4 (2023) searches exponent bits and clipping ranges and reparameterizes channel scales. These early formats are not NVFP4/MXFP4. ⟂ Recent｜The MXFP PTQ Benchmark (Jan 2026) identifies MXFP4 scale error. OSFP4 (Oct 2026) jointly optimizes smoothing and NVFP4 block scales. Their formats and results are not interchangeable.',
'Foundational｜QuIP (2023) combines incoherence processing and adaptive rounding; QuIP# (2024) adds Hadamard transforms, vector codebooks and recovery fine-tuning; AQLM (2024) learns input-adaptive additive codebooks. ⟂ Recent｜StagQ (Oct 2026) adds refinement planes to a 2-bit base. Align, Then Correct (Oct 2026) uses two-stage low-rank compensation. Differentiable Bit-Widths (Oct 2026) jointly learns SVD pruning and precision; its 1.61-bit setting is not native INT2.']
ADD_IDS=[['2208.07339','2608.13756','2610.07457'],['2307.09782','2601.09555'],['2608.07019'],['2307.09782','2310.16836','2601.09555'],['2307.13304','2401.06118','2610.08164','2610.06026']]
for n in range(5):
 rows[n][2][2]=ACADEMIC_ZH[n];EN[n][2]=ACADEMIC_EN[n]
 for arxiv in ADD_IDS[n]:
  url='https://arxiv.org/abs/'+arxiv
  i=existing.get(url) or sid(url)
  if i not in rows[n][3]:rows[n][3].append(i)
# Research significance is not a hardware-support claim.
rows[1][2][3]='2026年MXFP评测表明：量化算法与格式的兼容性会改变效果，不能照搬INT8配置。现有摘要不足以给出统一TTFT/TPOT提升率；MXFP8与FP8、块尺寸及设备仍须分别核对。'
EN[1][3]='The 2026 MXFP benchmark finds format compatibility matters. Do not copy an INT8 recipe unchanged. Its abstract does not establish a universal TTFT/TPOT gain; format, block size and device remain separate variables.'
rows[4][2][3]='StagQ在Llama-3.1-8B、Phi-4、OLMo-2-7B的2位设置，比所比多精度基线高3.1–7.0个MMLU点。Align, Then Correct在Qwen3-8B/QuIP# 2位上将WikiText-2 PPL由12.43降至10.26；仍不是昇腾业务验收结果。'
EN[4][3]='StagQ gains 3.1–7.0 MMLU points over compared multi-precision baselines at 2 bits on Llama-3.1-8B, Phi-4 and OLMo-2-7B. Align, Then Correct reduces Qwen3-8B / QuIP# 2-bit WikiText-2 PPL from 12.43 to 10.26. Neither result is Ascend business acceptance.'
ACTION_ZH=[
'试什么｜LLM先试SmoothQuant通道缩放，与直接舍入的W8A8比较；领域模型另比较逐通道与逐张量INT8权重尺度。 ⟂ 为什么｜分别减少激活离群值、通道尺度差异引起的误差，争取让8位执行通过质量门槛；收益首先是恢复质量，不是进一步缩小位宽。 ⟂ 如何取舍｜直接W8A8不达标、平滑后达标，才保留平滑；仍不达标则定位敏感层并保留高精度。确认实际使用低精度核后，再判断服务收益是否值得部署。',
'试什么｜确认950子型号支持后，在同一模型上比较INT8 W8A8与MXFP8 W8A8，分别采用匹配的尺度与导出格式。 ⟂ 为什么｜验证浮点动态范围能否缓解整数裁剪/舍入误差；MXFP评测提供了候选依据，未保证它一定优于INT8。 ⟂ 如何取舍｜INT8已达标且更快就保留INT8；只有MXFP8恢复业务质量或提高时延约束下吞吐才切换。设备型号未确认前，不启动这条部署实验。',
'试什么｜在相同LLM层、分组和W4A16格式下比较RTN、AWQ通道缩放、GPTQ误差补偿，先确认目标矩阵核能读取该格式。 ⟂ 为什么｜区分重要通道受损与舍入误差，寻找质量可接受且比W8更省容量的方案；纯权重载荷理论再减半。 ⟂ 如何取舍｜质量相近时选TPOT/容量和转换成本更优者；少数层拖累质量则试这些层回退8/16位。若不支持分组或重排开销过高，先停止部署，不盲目追求更低位宽。',
'试什么｜具备NVFP4执行环境后，同格式比较普通平滑与OSFP4的平滑/块尺度联合优化；昇腾先研究其校准目标，不直接套用GPU内核。 ⟂ 为什么｜检验FP4的质量损失有多少来自尺度选择；预期收益是在相同格式下恢复质量。 ⟂ 如何取舍｜同权重预算下质量提高且额外开销可接受才继续；只恢复精度却拖慢服务时，将其作为质量方案，不认定为性能优化。',
'试什么｜优先穿刺Align, Then Correct：在同一QuIP# 2位基础上，比较无补偿与不同秩的两阶段低秩补偿；多精度部署需求再单独试StagQ。 ⟂ 为什么｜已有Qwen3-8B困惑度恢复证据，具体要验证补偿能否在可接受的额外容量内救回业务质量。 ⟂ 如何取舍｜码本和补偿矩阵一并计费；只有质量损失低于1%且总体成本优于W4才继续。缺少解码/补偿执行核时，先限定为离线算法验证。']
ACTION_EN=[
'Try｜Test SmoothQuant channel scaling against directly rounded W8A8 for LLM linear layers. For domain models, compare per-channel and per-tensor INT8 weight scales. ⟂ Why｜Reduce activation-outlier or channel-scale error to recover quality at the same 8-bit precision. ⟂ Decision｜Retain smoothing if direct W8A8 fails quality and smoothing passes; otherwise locate sensitive layers and preserve higher precision. Confirm low-precision kernel execution before claiming serving value.',
'Try｜On a confirmed supported 950 variant, compare INT8 W8A8 with MXFP8 W8A8 using their correct scales and formats. ⟂ Why｜Test whether floating-point range mitigates integer clipping and rounding error; the MXFP study motivates a candidate, not guaranteed superiority. ⟂ Decision｜Keep INT8 if it passes and is faster. Switch only for recovered quality or improved throughput at the latency target. Confirm the device subtype first.',
'Try｜Compare RTN, AWQ scaling and GPTQ compensation at matched W4A16 layers and groups; first confirm executable format support. ⟂ Why｜Separate salient-channel sensitivity from rounding error, seeking acceptable quality with theoretically half the raw weight payload of W8. ⟂ Decision｜Among quality-matched candidates choose better measured TPOT/capacity and conversion cost. Try higher-precision fallback for sensitive layers; stop deployment if unsupported groups or repacking defeat gains.',
'Try｜With an NVFP4 execution environment, compare ordinary smoothing and OSFP4 joint smoothing/block-scale optimization at the same format. For Ascend, study the objective first. ⟂ Why｜Determine whether better scales recover FP4 quality at a matched format. ⟂ Decision｜Continue for improved quality and acceptable extra cost. Quality recovery with slower serving is not a performance win.',
'Try｜Prioritize Align, Then Correct on the same QuIP# 2-bit base, comparing no compensation and different adapter ranks. Test StagQ separately for multi-precision needs. ⟂ Why｜Qwen3-8B perplexity recovery motivates a concrete quality-recovery experiment within an extra-capacity budget. ⟂ Decision｜Include codebooks and adapters. Continue only if quality loss is below 1% and total cost beats W4. Without executable decode/adapter kernels, restrict the study to offline validation.']
for n in range(5):rows[n][2][4]=ACTION_ZH[n];EN[n][4]=ACTION_EN[n]
cards=[];refs=[]
labels=['格式与配置','产业应用','学术进展','效果与边界','昇腾下一步']
for n,(slug,name,cells,ids) in enumerate(rows):
 key='parameters-precision__progress_'+slug
 cards.append(dict(business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,section_kind='comparison',card_kind='analysis',claim_kind='research_analysis',title_zh=name,title_en=name,body_zh='\n'.join(a+'：'+b for a,b in zip(labels,cells)),body_en='\n'.join(a+': '+b for a,b in zip(['Representation','Deployment','Research','Evidence','Next experiment'],EN[n])),position=70+n,reviewed_at='2026-10-23'))
 for i in ids:
  k=key+'__'+i
  refs.append(dict(reference_id=k,business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,source_id=i,checked_at='2026-10-23',review_depth='section_review',observed_version='selected primary documentation / paper abstract; 2026-10-23',locator_zh='格式及部署能力见官方配置/硬件矩阵；论文机制与本表数字限摘要；旧有详细案例见下文。',locator_en='Official configuration/hardware matrices; paper mechanisms and new figures limited to abstracts; existing detailed cases below.'))
save('ic_compression_topic_cards',cards);save('ic_compression_topic_card_refs',refs)
print('Saved five source-linked progress rows')
