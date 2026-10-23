# -*- coding: utf-8 -*-
"""Evidence-first entry for recurring expert reading; canonical data only."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/compression/tables'
def read(t):return [json.loads(s) for s in (BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()]
def upsert(t,records,field):
 data=read(t);index={r['key']:n for n,r in enumerate(data)}
 for r in records:
  k=r[field]
  if k in index:
   old=data[index[k]]
   if old['row']==r:continue
   data[index[k]]={**old,'row':r,'row_version':old['row_version']+1}
  else:data.append(dict(key=k,row=r,row_version=1,deleted=False,text_match=None))
 (BASE/t/'rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in data),encoding='utf-8')
url='https://vllm-project.github.io/2026/10/21/flint.html';flint='source-wq-flint-20261021'
upsert('cloud_core_sources',[dict(source_id=flint,business_id='cloud-core',batch_id='expert-entry-20261023',canonical_url=url,external_id='',last_checked_at='2026-10-23',provider='vllm-project.github.io',source_kind='official_documentation',title='Day-0 Support for Flint on vLLM · 2026-10-21',update_policy='follow_original_url_record_versions',verification_status='primary_selected_sections_checked')],'source_id')
sources={r['row']['canonical_url']:r['row']['source_id'] for r in read('cloud_core_sources')}
sid=lambda n:sources['https://arxiv.org/abs/'+n]
ms=sources['https://www.hiascend.com/document/detail/en/mindstudio/2610/TITools/msModelSlim/docs/en/user_guide/quantization_algorithms/README.md']
asc=sources['https://docs.vllm.ai/projects/ascend/en/latest/user_guide/feature_guide/quantization.html']
CARDS=[
('summary','先看三项判断：研究价值在哪里',
'成熟能力：AWQ、GPTQ、SmoothQuant等已有工具实现。新成果应与可复现的现有配方比较，明确新增的是质量、容量、校准效率还是执行收益。\n前沿变化：研究正同时推进更好的误差目标、更紧凑的编码与更匹配硬件的执行。ReQuant、码本/网格编码、低秩补偿和AlignQuant分别处理不同缺口，不能用一个位宽排行榜替代比较。\n应用价值：技术储备先保持完整，再按容量、带宽、计算、质量或迁移成本查找候选。真正支持业务决策的是“何时有效、付出什么、证据到哪里”，而非论文名或最高加速比。',
'Three judgments: where research adds value',
'Established capabilities: compare new work against reproducible AWQ/GPTQ/SmoothQuant recipes, identifying quality, capacity, calibration or execution gains.\nResearch directions: objective refinement, representation and hardware-aware execution address different gaps; a bit-width ranking is insufficient.\nApplication value: retain the knowledge landscape, then retrieve by capacity, bandwidth, compute, quality or migration cost. Conditions, costs and evidence boundaries support decisions.',
[ms,sid('2608.07019'),sid('2610.07457'),sid('2610.08164')]),
('updates','近期关注：什么变化值得更新认识',
'2026-10-21 · 产业实现：vLLM发布Flint支持说明。它的NVFP4检查点以W4A16运行，激活与KV保持BF16；说明格式名并不能单独确定联合量化配置。\n新增认识：这份实现把压缩权重与小批量内核、打包及融合一起优化，说明研究部署收益必须看到完整执行链。详细条件与耗时列在下方证据卡。\n2026-10 · 学术增量：AlignQuant处理精度边界与计算块冲突；Align, Then Correct在冻结主体上恢复输出质量；OSFP4优化NVFP4尺度。它们分别影响执行、质量恢复和校准，不是同一种改进。\n覆盖状态：本轮核对日期为2026-10-23，包含已核查的代表工作；这不表示10月新增论文已全部收齐，也不表示所有结果已独立复现。',
'Recent signals: changes worth incorporating',
'2026-10-21 · Industry: the Flint vLLM implementation runs its NVFP4 checkpoint as W4A16, retaining BF16 activations and KV cache. The format name alone does not define a joint quantization scheme.\nInterpretation: packing, small-batch kernels and fusion form part of the execution path; see the evidence card below.\nOctober research: AlignQuant targets tile alignment, Align, Then Correct targets frozen-backbone recovery, and OSFP4 targets NVFP4 scales. These are distinct contributions.\nCoverage: checked 2026-10-23; selected verified work, not a complete October census or independent reproduction.',
[flint,sid('2610.07457'),sid('2610.08164'),sid('2610.08231')]),
('evidence','关键证据：Flint的收益来自完整执行链',
'模型与配置：Flint，40B总参数、每token约2.5B激活参数；单GB200、batch=1、100K上下文。NVFP4权重以W4A16执行，激活和KV为BF16，检查点经过量化感知训练。\n报告效果：官方给出的NVFP4模型前向解码耗时由4.81降至1.78 ms；优化后完整服务逐token耗时为2.06 ms。前向与完整服务不是同一指标。\n比较边界：4.81→1.78 ms比较的是同一精度路径优化前后，不能当成NVFP4相对BF16的加速。该文未给出TTFT和可直接用于业务验收的质量分数；它报告与参考实现的评测一致性。\n技术意义：量化格式、特定负载内核及融合共同决定收益。此结果仅适用于文中配置，不证明其他模型、并发或昇腾设备具有相同表现。',
'Key evidence: Flint gains depend on the full execution path',
'Setup: Flint, 40B total / about 2.5B active parameters; one GB200, batch 1, 100K context. Its QAT NVFP4 checkpoint runs as W4A16 with BF16 activations and KV.\nReported: forward decode latency falls from 4.81 to 1.78 ms; optimized end-to-end service takes 2.06 ms/token.\nBoundary: this is before/after optimization of one precision path, not an NVFP4-versus-BF16 speedup. The post reports reference-evaluation consistency, not TTFT or numerical business-quality acceptance.\nInterpretation: format, workload-specific kernels and fusion jointly determine gains; not transferable performance proof for other models, loads or Ascend.',
[flint]),
('questions','开放问题：哪些证据会改变技术选择',
'质量恢复是否划算：在相同总字节和校准预算下，舍入优化、敏感层提精度、稀疏旁路或低秩补偿，哪种得到更好的任务质量？\n编码能否高效消费：码本或网格编码的读取节省，能否覆盖解码、索引及必要变换？需要完整执行路径，不能只靠理论位数。\n效果能否跨条件保持：模型结构、任务分布、输入长度和并发变化时，优势是否仍在？单个PPL或单批内核结果不足以回答。\n知识如何支撑应用：保留失败条件、复现配置与未报告指标；业务需求变化时从证据筛选，而不是重新堆一份推荐名单。',
'Open questions: evidence that can change selection',
'Recovery: at matched total bytes and calibration budgets, compare rounding, precision retention, side records and low-rank correction.\nExecution: can saved traffic cover codebook/trellis decoding, indexing and transforms?\nGeneralization: do gains persist across architectures, tasks, lengths and concurrency?\nApplication: retain failure conditions, reproducible configurations and missing metrics so later decisions can use evidence.',
[sid('2610.08164'),sid('2406.11235'),sid('2610.07457')])]
cards=[];refs=[]
for n,(slug,title,body,en_title,en_body,ids) in enumerate(CARDS):
 key='parameters-precision__expert_'+slug
 cards.append(dict(business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,title_zh=title,title_en=en_title,body_zh=body,body_en=en_body,position=110+n,reviewed_at='2026-10-23',section_kind='comparison',card_kind='analysis',claim_kind='research_analysis'))
 for source in ids:
  k=key+'__'+source
  refs.append(dict(reference_id=k,business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,source_id=source,checked_at='2026-10-23',review_depth='section_review' if source in [flint,ms,asc] else 'abstract_review',observed_version='primary material checked 2026-10-23',locator_zh='Flint：Model architecture、Optimizations、Usage notes；前向与完整服务分开。其余论文增量按已核查机制归纳。技术判断非独立复现。',locator_en='Flint: Model architecture, Optimizations and Usage notes; distinguish forward from serving. Other increments summarize reviewed mechanisms. Interpretation is not independent reproduction.'))
upsert('ic_compression_topic_cards',cards,'card_id');upsert('ic_compression_topic_card_refs',refs,'reference_id')
print('Expert entry: judgments, recent signals, conditioned evidence and open questions')
