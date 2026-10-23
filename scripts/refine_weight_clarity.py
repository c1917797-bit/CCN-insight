# -*- coding: utf-8 -*-
"""Editorial clarity pass; no changes to author-result evidence."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/compression/tables'
def rows(t):return [json.loads(x) for x in (BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()]
def save(t,data):
 (BASE/t/'rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in data),encoding='utf-8')
def update(t,field,changes):
 data=rows(t)
 for entry in data:
  r=entry['row'];patch=changes.get(r.get(field))
  if patch and any(r.get(k)!=v for k,v in patch.items()):r.update(patch);entry['row_version']+=1
 save(t,data)

BODY={
'calibration':('尺度、裁剪与舍入：同样的位数，怎样少损失信息？','问题：固定只有16个INT4编码时，共享范围太大会让普通权重的刻度变粗；范围太小又会截断极端值。只逐个四舍五入，也没有考虑某个误差对层输出有多大影响。\n做法：AWQ根据校准输入识别重要通道，再通过等价缩放保护它们；GPTQ量化一列后，把造成的误差补偿到尚未量化的权重；OmniQuant进一步学习裁剪范围和等价变换。\n近期变化：ReQuant（2026-08）不改变已生成的量化网格，而是重新搜索整数分配。它研究的是“格式不变，还能不能更准”。\n研究判断：这条路线主要提高同格式下的质量。比较时要固定分组、校准数据与预算；不能把更多校准计算换来的改善，直接称作推理提速。'),
'representation':('非均匀与稀疏旁路：少数难量化权重如何处理？','问题：少数异常或敏感权重可能主导误差，让整组权重都使用高精度又浪费空间。\n做法：SpQR与SqueezeLLM把难处理部分单独表示，让主体采用较紧凑的编码；SqueezeLLM还研究按敏感度分配非均匀取值。这里的旁路用于保留信息，不等于把这些权重剪掉。\n路线区别：通道缩放仍尽量保留规则的稠密执行；稀疏旁路则显式引入例外记录，需要额外索引和执行处理。\n研究判断：适合研究“能否用少量例外换回质量”。代价必须包含主体、旁路、索引和尺度，才能与统一INT4或部分层保留高精度公平比较。'),
'codes':('向量与网格编码：每个权重必须独立编码吗？','问题：独立量化每个数，难以利用多个权重之间的联合分布；直接扩大向量码本，又会让码本随维度快速膨胀。\n做法：QuIP/QuIP#先改变数值分布以利于量化，QuIP#使用向量码本；AQLM用多个码本向量相加表示一组权重；QTIP用带状态的网格编码（trellis）组织高维表示，避免简单扩大完整码本。\n近期变化：StagQ（2026-10）用2位基础流和后续细化平面，服务多个精度档；XOR-Trellis（2026-09-30首投）、CurveTQ（2026-10-06）分别探索更便宜的重构或免旋转搜索。\n研究判断：这一分支解决的不只是“2位够不够准”，还包括多精度分发和解码复杂度。编码格式与解码核是一套系统，不能把它当成普通INT2矩阵乘。'),
'float':('浮点与块尺度：如何用有限位数分配数值范围？','问题：整数档位通常等间距；低位浮点用指数和尾数形成不同的数值间距。选择哪一种，取决于数值分布、尺度与执行硬件，而不是只看总位数。\n做法：FP8 Quantization研究指数位分配和尺度；ZeroQuant-FP与LLM-FP4探索更低浮点精度。块量化让一小组数共享尺度，以适应局部范围，但尺度本身也可能引入误差。\n近期变化：2026年MXFP评测指出算法与格式兼容性及尺度误差的重要性；OSFP4（2026-10）联合优化NVFP4的平滑变换与块尺度。\n研究判断：INT4、NF4和FP4不是同一种表示，NVFP4/MXFP4也有各自的尺度约定。存储格式、加载转换与实际计算格式应分别记录，不能用文件位宽推断执行收益。'),
'joint':('联合量化：为什么处理权重还要同时看激活？','问题：一层输出同时由权重和输入激活决定。只把权重分布处理好，激活离群值仍可能使W8A8或W4A4质量下降。\n做法：SmoothQuant把部分激活量化难度转移到权重；旋转方法分散离群值；FlatQuant学习更一般的仿射变换，调整权重与激活的分布。\n专题分工：本页说明这些变换怎样影响权重表示；激活专题主讲在线激活尺度、离群值和联合执行。AWQ使用激活统计优化权重，并不因此成为激活量化方法。\n研究判断：完整方案应同时计入质量、保留高精度部分和在线变换成本；同一套联合收益不能在权重、激活专题各算一次。'),
'execution':('执行协同：压缩后的权重怎样真正减少计算成本？','问题：精度分配越细，存储越灵活，却可能破坏矩阵核需要的规则布局。解包、反量化、重排和小核启动都可能吃掉节省的读写开销。\n做法：需要让压缩分组、数据打包和计算单元相匹配，并尽量融合转换。AlignQuant（2026-10）以二维计算块统一精度分配、存储和执行，直接处理这种边界冲突。\n产业观察：同一块量化FP8检查点，在官方说明支持的950路径可转为MXFP8执行，在其他代设备可能展开为浮点模型类型；能加载与保持低比特驻留是两个能力。\n研究判断：这是算法与系统共同设计的问题。内核加速、预填充吞吐、首token时延和逐token时延必须分别保留测试条件，不能相互替代。'),
'recovery':('低秩补偿：量化已经丢失的信息还能补多少？','问题：某些层在极低位宽下留下较大的输出残差。继续调整原量化器之外，还可以增加一个小的校正分支。\n做法：用低秩矩阵近似需要补偿的部分，主量化权重保持不变。Align, Then Correct（2026-10）先按非对称目标对齐输出，再依据补偿后的统计做第二阶段校正。\n另一条路线：Differentiable Bit-Widths（2026-10）联合学习SVD分量的保留与位宽，不是给原模型简单附加同一种支路。其1.61位是联合压缩设置，不是原生INT2执行。\n研究判断：补偿相当于用额外存储和计算换质量，必须与同预算下保留部分高精度权重比较。恢复困惑度不等于所有任务恢复，也不自动意味着服务变快。')}
patches={}
for slug,(title,body) in BODY.items():patches['parameters-precision__landscape_'+slug]={'title_zh':title,'body_zh':body}
patches['parameters-precision__insight_scope']={'title_zh':'研究范围：权重表示、误差控制与低比特执行','body_zh':'本专题研究三个相连的问题：怎样把权重存得更小，怎样减少近似带来的输出误差，以及怎样让紧凑表示被高效执行。不同位宽、模型和硬件用于交叉检索，不限定技术收录范围。\n权重与激活的边界：W4A16/W8A16和AWQ/GPTQ等权重优化在本页主讲；W8A8/W4A4的激活范围、在线尺度和联合计算由激活专题主讲。使用激活统计不等于量化激活。\n同一联合方案只保留一份完整机制与效果记录，通过多标签关联两个专题。KV Cache因有不同的生命周期及序列/并发容量特征，继续单列。'}
conclusion='权重量化的核心，是在总存储、模型质量和执行成本之间找到更好的折中；降低标称位数只是其中一个手段。\n判断一：成熟PTQ算法已构成工程基线。AWQ、GPTQ、SmoothQuant等已有工具支持，后续工作应说明相对已有配方改善了哪类误差、增加多少离线成本，以及能否保持原执行格式。仅优于简单舍入不足以证明普遍优势。\n判断二：更强压缩把问题从单个数的近似，推向编码与重构。码本、稀疏旁路、精度细化和低秩补偿提供更多质量恢复空间，也增加元数据、索引或支路成本。因此，W2与W4应比较真实总字节和完整执行代价，而非只比较标签。\n判断三：格式与硬件协同决定收益能否兑现。AlignQuant研究规则计算块与精度分配，浮点块格式研究局部尺度；它们表明执行约束应进入方法设计，而不是等量化结束后再处理。论文内核效果、完整服务效果和跨平台迁移仍需分别判断。\n持续跟踪：同格式下的质量恢复、低开销的高维解码、尺度与计算块协同、真实负载中的端到端收益。后续需求变化时，从这些能力中选择候选，而不是重新从论文名单开始。'
patches['parameters-precision__dossier_5']={'title_zh':'综合判断：从位数压缩走向表示、质量与执行协同','body_zh':conclusion,'title_en':'Synthesis: representation, quality and execution co-design','body_en':'Weight quantization trades total storage, model quality and execution cost; nominal bit width is one control variable.\nEstablished PTQ provides engineering baselines. New work should demonstrate improvement over reproducible recipes, including calibration cost and format compatibility. Beating simple rounding alone does not prove general superiority.\nStronger compression shifts attention toward coding and reconstruction. Codebooks, side records, refinement planes and low-rank corrections offer recovery at additional cost; compare actual total bytes and execution, not W2/W4 labels alone.\nFormat/hardware co-design determines realized gains. Tile alignment and block-scale design bring execution constraints into the method. Kernel, end-to-end service and cross-platform results remain separate evidence.\nTrack fixed-format quality recovery, low-cost high-dimensional decoding, scale/tile co-design and real-workload gains, selecting applications later.'}
update('ic_compression_topic_cards','card_id',patches)
update('ic_compression_topic_sections','section_id',{'parameters-precision__implication':{'heading_zh':patches['parameters-precision__dossier_5']['title_zh'],'body_zh':conclusion,'body_en':patches['parameters-precision__dossier_5']['body_en']}})

data=rows('ic_compression_topic_cards');template=next(r['row'] for r in data if r['row']['card_id']=='parameters-precision__insight_scope')
key='parameters-precision__principles_brief'
principles={**template,'card_id':key,'position':81,'section_kind':'mechanism','title_zh':'从短编码到模型输出：量化的基本逻辑','title_en':'From compact codes to model outputs: the basic logic',
'body_zh':'改变什么：量化改变参数的数值表示，通常不改变权重矩阵的形状。以仿射整数量化为例，保存短整数编码与共享参数，执行时解释为近似权重；浮点和码本方案使用不同编码规则。\n如何近似：q = clip(round(w/s)+z, q_min, q_max)，还原值 ŵ = s(q−z)。s是尺度，z是零点，q是保存的整数。较少编码意味着多个原值映射到同一近似值；舍入丢失细节，越界裁剪会增加误差。\n为何影响模型：若层输出为Y=WX，量化后为Ŷ=ŴX，则ΔY=(Ŵ−W)X。同样大小的权重误差会随输入方向产生不同输出影响，所以只最小化权重误差不一定最有利于任务质量。\n为何不一定加速：短编码能减少权重载荷，但尺度、索引、解码与转换都有代价。理论纯载荷缩小、设备峰值内存下降和实际执行加速，是三个需要分别证实的结果。',
'body_en':'What changes: quantization changes numerical representation, usually not matrix shape. Affine integer quantization stores compact integer codes plus shared parameters; floating-point and codebook schemes use different rules.\nApproximation: q = clip(round(w/s)+z, q_min, q_max), with reconstruction ŵ = s(q−z). Scale s and zero point z define the mapping. Rounding loses detail and clipping adds error outside the range.\nModel effect: for Y=WX and Ŷ=ŴX, ΔY=(Ŵ−W)X. The input determines how weight error affects outputs, so minimum weight error need not maximize task quality.\nExecution: codes reduce payload, but scales, indices, reconstruction and conversion cost extra. Payload, peak memory and speed are separate results.'}
found=False
for r in data:
 if r['key']==key:r['row']=principles;r['row_version']+=1;found=True
if not found:data.append(dict(key=key,row=principles,row_version=1,deleted=False,text_match=None))
save('ic_compression_topic_cards',data)
refs=rows('ic_compression_topic_card_refs');existing={r['key'] for r in refs}
sources={r['row']['canonical_url']:r['row']['source_id'] for r in rows('cloud_core_sources')}
for arxiv,loc in [('1712.05877','§2.1：仿射整数量化与零点；误差公式为线性层代数推导。'),('2306.00978','§3：用激活统计识别重要通道；本段解释为何权重误差与层输出误差不同。')]:
 source=sources['https://arxiv.org/abs/'+arxiv];rid=key+'__'+source
 if rid in existing:continue
 refs.append(dict(key=rid,row_version=1,deleted=False,text_match=None,row=dict(reference_id=rid,business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,source_id=source,checked_at='2026-10-23',review_depth='section_review',observed_version='previously reviewed sections; explanatory algebra',locator_zh=loc,locator_en='Previously reviewed affine representation / activation-aware weight quantization sections; linear error identity is explanatory algebra.')))
save('ic_compression_topic_card_refs',refs)

update('ic_compression_research_frames','frame_id',{'parameters-precision':{
'why_zh':'模型权重需要长期保存，并在推理中被读取和计算。降低表示位数，可以减少权重载荷，让相同设备容纳更大的模型，或减少读取权重的数据量。\n难点在于，近似表示会损失信息，紧凑编码也未必适合硬件直接计算。因此，权重量化研究需要同时解决三个问题：表示是否足够准确，额外存储是否可控，执行是否高效。\n本专题沿这三个问题梳理经典方法、近期进展和产业实现。业务需求用于后续查找适用路线，不作为收录前的筛选条件。',
'challenge_zh':'有限编码如何分配：共享范围过大会让普通权重的刻度变粗，过小则裁剪异常值。尺度、分组、裁剪和非均匀表示分别改变这一取舍。\n误差如何被控制：不同权重对层输出的影响不同，前层误差还会改变后层输入。通道保护、误差补偿、校准及低秩恢复分别处理不同环节。\n额外信息如何计量：尺度、零点、码本、索引、稀疏旁路和补偿矩阵都要占空间。标称位宽相同，不代表实际存储相同。\n压缩表示如何执行：紧凑分组可能不匹配计算块；解包、反量化与布局转换可能抵消访存收益。格式设计与内核实现必须一起讨论。'}})
print('Clarity pass: principles brief and seven problem–mechanism–judgment explanations')
