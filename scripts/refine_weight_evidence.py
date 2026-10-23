# -*- coding: utf-8 -*-
"""Pinned, within-paper comparisons; no synthetic cross-paper ranking."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/compression/tables'
def read(t):return [json.loads(x) for x in (BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()]
def save(t,items,field):
 data=read(t);index={r['key']:n for n,r in enumerate(data)}
 for r in items:
  k=r[field]
  if k in index:
   old=data[index[k]]
   if old['row']==r:continue
   data[index[k]]={**old,'row':r,'row_version':old['row_version']+1}
  else:data.append(dict(key=k,row=r,row_version=1,deleted=False,text_match=None))
 (BASE/t/'rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in data),encoding='utf-8')
sources={r['row']['canonical_url']:r['row']['source_id'] for r in read('cloud_core_sources')}
DATA=[
('awq','AWQ：同位宽的质量对照','AWQ: matched-precision quality',
['Llama-2-7B，INT4、group128；WikiText-2 PPL。原文v6表4，同表比较。',
'RTN 5.73；GPTQ 5.69；GPTQ-R 5.63；AWQ 5.60；FP16 5.47。PPL越低越好；不是业务精度损失百分比。',
'激活感知缩放优化层输出误差；§4的TinyChat打包/融合属于另一层系统贡献，本组质量数字不代表其速度。',
'综合判断：这一配置支持AWQ优于同表RTN/GPTQ；不能推广为所有模型、校准预算或执行后端上的统一排名。'],
['Llama-2-7B, INT4, group 128; WikiText-2 PPL, v6 Table 4.',
'RTN 5.73; GPTQ 5.69; GPTQ-R 5.63; AWQ 5.60; FP16 5.47. Lower is better.',
'Activation-aware scaling and TinyChat execution are distinct contributions.',
'This supports a within-table quality advantage, not universal superiority or a serving-speed claim.'],
'2306.00978','2306.00978v6','§3.2 Eq.(4–5)；§4；§5.1；表4。'),
('alignquant','AlignQuant：解码收益与首token代价','AlignQuant: decode gain and first-token cost',
['Llama-3.2-3B-Instruct，A100-SXM4 40GB；batch1、输入128/输出512。64×64 tile，60% W4、其余W8，A8；不是均匀W4。',
'表1：BF16→方法，TTFT 17.47→19.67 ms，TPOT 17.19→7.54 ms；驻留内存5.99→2.72 GiB。表2：WikiText-2 PPL 12.49→12.61。',
'据原表计算：TPOT下降56.1%，TTFT增加12.6%。校准/打包不计入请求计时；在线准备计入。比较GPTQ/AWQ时，位率与具体执行核并不相同。',
'综合判断：支持该配置的解码优化；首token敏感负载需单独取舍。跨方法系统结果同时受混合位率与实现影响，不能孤立归因为精度分配。'],
['Llama-3.2-3B-Instruct, A100 40GB; batch 1, input/output 128/512. 60% W4 tiles, otherwise W8; A8.',
'BF16→method: TTFT 17.47→19.67 ms; TPOT 17.19→7.54 ms; resident memory 5.99→2.72 GiB; PPL 12.49→12.61.',
'Computed: TPOT −56.1%, TTFT +12.6%. Offline calibration/packing excluded; online preparation included.',
'Decode gains are conditional. Different weight budgets and kernels prevent an algorithm-only attribution.'],
'2610.07457','2610.07457v1','§3.1–3.3；§4.1–4.3、表1–2；附录G.1–G.5、H.5。'),
('compensation','Align, Then Correct：恢复多少，额外付出什么','Align, Then Correct: recovery and extra cost',
['Qwen3-8B，QuIP# 2-bit，补偿rank64；WikiText-2校准，C4留出。与EoRA/QERA/ProjQ/LQ-LoRA按相同秩比较。',
'表1：C4 PPL，未补偿19.19、LQ-LoRA 17.95、方法17.17、FP16 15.24；恢复有效，仍有差距。',
'附录G：最终适配器349 MB；第二阶段替换第一阶段，不叠加两份。阶段1校准128×2048 tokens，阶段2另用16×512；同秩不等于同计算预算。',
'综合判断：表4最优行包含完整两阶段，不能当作孤立阶段1效果；表5检验顺序。未给出完整服务TTFT/TPOT，尚不能断言补偿比同存储预算的提精度更划算。'],
['Qwen3-8B, QuIP# 2-bit, rank 64; WikiText-2 calibration, held-out C4.',
'C4 PPL: uncompensated 19.19; LQ-LoRA 17.95; method 17.17; FP16 15.24.',
'Final adapter 349 MB. Stage 2 replaces stage 1, with additional calibration; equal rank is not equal compute.',
'Table 4 includes the full two-stage method. Serving latency and an equal-storage precision-retention comparison remain unresolved.'],
'2610.08164','2610.08164v1','§4、§5；表1、4–5；附录D、G（表10–12）、H。')]
cards=[];refs=[]
for n,(slug,title,en_title,cells,en_cells,arxiv,version,locator) in enumerate(DATA):
 key='parameters-precision__audit_'+slug;source=sources['https://arxiv.org/abs/'+arxiv]
 cards.append(dict(business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,title_zh=title,title_en=en_title,body_zh='\n'.join(a+'：'+b for a,b in zip(['配置与基线','原文结果','成本与口径','判断与缺口'],cells)),body_en='\n'.join(a+': '+b for a,b in zip(['Setup','Reported results','Cost and protocol','Interpretation and gaps'],en_cells)),position=120+n,reviewed_at='2026-10-23',section_kind='comparison',card_kind='analysis',claim_kind='research_analysis'))
 rid=key+'__'+source
 refs.append(dict(reference_id=rid,business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,source_id=source,checked_at='2026-10-23',review_depth='section_review',observed_version=version,locator_zh=locator+' 指定章节/表格核对；百分比为原表推算。未独立复现。',locator_en=locator+' Selected sections/tables checked; percentage changes computed from reported values. No independent reproduction.'))
key='parameters-precision__audit_coverage'
cards.append(dict(business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,title_zh='证据分层：本页能回答什么，尚缺什么',title_en='Evidence levels: established scope and remaining gaps',body_zh='原文已核对：本轮对AWQ、AlignQuant、Align, Then Correct的指定机制章节、实验表与成本口径重新核对；下列对照只在各自论文内部成立。\n综合判断：把质量算法、表示变化与执行实现分开；先问对照是否同条件，再问结果是否适用。这里的判断不等于作者结论，也不等于独立复现。\n仍待验证：尚无本站的目标硬件实测；跨模型、跨任务、跨平台迁移，以及同总存储/总校准预算比较，缺证据处保留空缺。\n覆盖缺口：其余路线仍有摘要级材料；QAT/低精度预训练、领域模型专项量化和最新检索的系统覆盖尚需扩充。本页不标称全量系统综述。',body_en='Primary checks: selected mechanism sections, experiment tables and cost accounting in AWQ, AlignQuant and Align, Then Correct. Comparisons stay within their original studies.\nSynthesis: distinguish quality algorithms, representation and implementation; applicability follows comparable conditions.\nUnverified: no local hardware reproduction; cross-model/task/platform transfer and equal-total-budget comparisons remain gaps.\nCoverage: some routes remain abstract-level; QAT, domain-model quantization and systematic current coverage need expansion. This is not an exhaustive review.',position=119,reviewed_at='2026-10-23',section_kind='comparison',card_kind='analysis',claim_kind='research_analysis'))
for arxiv in ['2306.00978','2610.07457','2610.08164']:
 source=sources['https://arxiv.org/abs/'+arxiv];rid=key+'__'+source
 refs.append(dict(reference_id=rid,business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,source_id=source,checked_at='2026-10-23',review_depth='section_review',observed_version={'2306.00978':'2306.00978v6','2610.07457':'2610.07457v1','2610.08164':'2610.08164v1'}[arxiv],locator_zh='本轮审阅范围见对应对照记录；只核对指定章节，不声称全部附录、代码或数学证明均已验证。',locator_en='Review scope is specified in each comparison; not a claim to verify every appendix, code path or proof.'))
save('ic_compression_topic_cards',cards,'card_id');save('ic_compression_topic_card_refs',refs,'reference_id')
checked=[]
for item in read('cloud_core_sources'):
 r=item['row']
 if r['canonical_url'] in ['https://arxiv.org/abs/'+n for n in ['2306.00978','2610.07457','2610.08164']]:
  checked.append({**r,'last_checked_at':'2026-10-23','verification_status':'primary_selected_sections_checked'})
save('cloud_core_sources',checked,'source_id')
print('Added three pinned within-study comparisons and explicit evidence coverage')
