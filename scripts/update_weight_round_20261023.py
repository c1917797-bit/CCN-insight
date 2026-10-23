# -*- coding: utf-8 -*-
"""Incremental, primary-grounded update; no publishing and no synthetic results."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/compression/tables'
def read(t):return [json.loads(x) for x in (BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()]
def save(t,items,field):
 data=read(t);idx={x['key']:i for i,x in enumerate(data)}
 for r in items:
  key=r[field]
  if key in idx:
   old=data[idx[key]]
   if old['row']!=r:data[idx[key]]={**old,'row':r,'row_version':old['row_version']+1}
  else:data.append(dict(key=key,row=r,row_version=1,deleted=False,text_match=None))
 (BASE/t/'rows.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in data),encoding='utf-8')
SOURCES=[
 ('source-wq-beyond4-261028537','https://arxiv.org/abs/2610.28537','Beyond 4 Bits: Data-Centric Post-Training Quantization and Recovery','2610.28537v1'),
 ('source-wq-bitmtp-261028500','https://arxiv.org/abs/2610.28500','BitMTP: When Multi-Token Prediction Meets Low-Bit Large Language Models','2610.28500v1'),
 ('source-wq-qwen38-ascend-20261023','https://github.com/vllm-project/vllm-ascend/blob/main/docs/source/tutorials/models/Qwen3.8-27B.md','vLLM Ascend · Qwen3.8-27B model tutorial','main observed 2026-10-23')]
save('cloud_core_sources',[dict(source_id=s,business_id='cloud-core',batch_id='weight-refresh-20261023',canonical_url=u,external_id=v,last_checked_at='2026-10-23',provider='arxiv.org' if 'arxiv.org' in u else 'github.com',source_kind='paper' if 'arxiv.org' in u else 'official_documentation',title=t,update_policy='follow_original_url_record_versions',verification_status='primary_selected_sections_checked') for s,u,t,v in SOURCES],'source_id')
existing={x['row']['canonical_url']:x['row']['source_id'] for x in read('cloud_core_sources')}
asc=existing['https://docs.vllm.ai/projects/ascend/en/latest/user_guide/feature_guide/quantization.html']
audit=json.loads((ROOT/'research/source-audits/2026-10-23/entrypoints.json').read_text(encoding='utf-8'))
status_labels={'entrypoint_fetched':'已取得入口样本','fetch_failed':'读取失败','missing_source_url':'缺少来源链接','skipped_non_public_https':'跳过非公开HTTPS入口'}
coverage='；'.join(status_labels.get(k,k)+' '+str(v)+' 个' for k,v in audit['counts'].items())
recent=json.loads((ROOT/'research/source-audits/2026-10-23/arxiv-recent.json').read_text(encoding='utf-8'))
recent_count=sum(r.get('received_entries',0) for r in recent)
candidate_count=len({c['arxiv_id'] for r in recent for c in r.get('candidates',[])})
DATA=[
 ('refresh_data','新证据挑战：2-bit恢复并非总能改善生成质量',
 '要解决的问题：超低比特下，换量化器、换校准数据与增加恢复训练，哪一个真正改变质量？\n技术做法：Beyond 4 Bits（2026-10-20）比较标量与向量量化，并交叉选择校准/恢复数据；恢复阶段仅更新码本，固定编码分配。\n关键反例：表1中Llama-3.1-8B采用数学数据校准时，AvgGen由不恢复的27.4，降至web恢复22.2、math恢复21.4；因此“增加恢复必然更好”不成立。\n修订判断：校准与恢复数据需联合选择；问答、生成与指令遵循分开观察。论文按反量化权重评测质量，打包容量是估算，不能据此推导TTFT、TPOT或昇腾收益。',
 'New evidence: recovery is not guaranteed to improve generation',
 'Question: what changes ultra-low-bit quality?\nMethod: Beyond 4 Bits crosses calibration/recovery data and updates codebooks with assignments fixed.\nCounterexample: Llama-3.1-8B math-calibrated AvgGen is 27.4 without recovery, 22.2 with web recovery and 21.4 with math recovery (Table 1).\nJudgment: choose data jointly and separate evaluation tasks. Dequantized evaluation and packed-size estimates are not serving-latency evidence.',
 [SOURCES[0][0]],'§3–4.2，表1–2；§4.6，表8；§6限制。'),
 ('refresh_mtp','交叉路线：低比特与多Token预测不能直接相乘',
 '要解决的问题：权重读取减少后，顺序解码仍受步数限制；但一次预测更多Token，也会增加计算与KV处理成本。\n技术做法：BitMTP（2026-10-20）联合训练下一Token和多Token目标，结合按宽度选择的低比特核、共享KV与图重放；属于训练与执行协同，不能直接套在任意PTQ检查点上。\n原文效果：H20、Bonsai-1.7B、D=8混合解码，相对同设备同后端SFT自回归基线，五任务平均解码吞吐为2.4倍。计时不含预填充和请求初始化，因此不能等同于端到端加速或TTFT改善。\n分类判断：在权重量化中保留执行协同入口；主要增量是低比特模型与解码策略的协同。这里不把它算作新的权重校准算法，也不承诺输出与原模型严格一致。',
 'Cross-route: low bits and multi-token prediction are not multiplicative by default',
 'Challenge: wider drafting adds computation and KV work.\nMethod: joint next-token/multi-token training, specialized low-bit kernels and shared-KV graph replay; not a drop-in PTQ option.\nEvidence: H20, Bonsai-1.7B, hybrid D=8 reaches 2.4x five-task mean decode throughput against matched SFT AR; excludes prefill and request initialization.\nOwnership: execution/decoding co-design, not another calibration algorithm or exact-output guarantee.',
 [SOURCES[1][0]],'§3.2–3.4；§4.1–4.2，表1；§5限制。'),
 ('refresh_ascend','产业核对：有适配示例，不等于已有性能结论',
 '观察到的实现：vLLM Ascend当前Qwen3.8-27B教程提供部署与评测入口，但§9.1明确说明性能调优结果尚未充分验证；文档配置不能替代测量数据。\n格式边界：原生block-FP8检查点在950PR/950DT可重组为MXFP8执行；其他代设备会展开为模型浮点类型。FP8文件可加载，不代表低比特权重一直驻留，也不能据此推断INT8路径。\n判断变化：产业信息应回答“哪个检查点、哪条加载/执行路径、什么硬件”，而非笼统写“支持W8”。950子型号未确认时，不把PR/DT能力直接归到用户设备。\n待补证据：固定软件版本、检查点及设备后，补齐任务质量、驻留内存、TTFT与TPOT；当前材料没有给出足以承诺业务收益的完整同条件结果。',
 'Industry check: deployment examples are not performance validation',
 'Implementation: the Qwen3.8-27B tutorial provides deployment/evaluation entrypoints; §9.1 says tuning results are not fully verified.\nFormat boundary: native block-FP8 checkpoints regroup to MXFP8 on 950PR/DT; other generations expand weights to model dtype.\nJudgment: track checkpoint, load/execution path and hardware, not W8 alone. Unknown 950 subtype is not evidence of PR/DT capabilities.\nGap: no complete matched quality, memory, TTFT and TPOT evidence for a business promise.',
 [SOURCES[2][0],asc],'模型教程§8–9.1；量化指南§3 Native FP8 checkpoints；main/latest观察于2026-10-23，非固定发布版。'),
 ('refresh_coverage','本轮采集边界：入口盘点与内容审阅分开记录',
 '执行范围：登记的332个渠道、332个不同URL均已尝试读取公开入口；结果为'+coverage+'。完整清单与错误保留在本地采集审计中。\n内容审阅：另经网页检索核对两篇10月20日论文的指定章节与表格，并核对vLLM Ascend模型教程、量化指南及msModelSlim仓库消息。不是332渠道的全部新增内容。\n仍有缺口：入口读取成功仅代表取到了网页样本；未完成所有分页、订阅源历史、会议全部论文和10月日期窗口的逐项去重审阅。失败入口保持待重试，不能算成没有新信息。\n入库规则：能改变技术判断的证据进入专题；当月事件保留日期和原文定位；跨路线材料标明归属。没有核查的速度、精度、内存数字不补写。',
 'Collection boundary: endpoint audit is distinct from content review',
 'Scope: attempted all 332 registered public entrypoints; results: '+coverage+'.\nContent review: separately checked selected sections/tables of two October 20 papers and official implementation documentation.\nGaps: endpoint samples do not cover every page, subscription history, conference paper or October event. Failed endpoints remain pending, not negative findings.\nInclusion: evidence that changes understanding enters the topic with dates, provenance and route ownership; unreported metrics stay unreported.',
 [SOURCES[0][0],SOURCES[1][0],SOURCES[2][0]],'采集覆盖属于本站过程记录；论文/实现事实分别见对应证据卡。本卡引用不证明信息源已全量采完。')]
cards=[];refs=[]
pending=[('2610.31412','SQuAT','2026-10-22','格形码本量化感知训练：分别优化权重方向与幅值，补充当前专题偏重PTQ的覆盖缺口。训练加速不等于推理加速。'),('2610.29378','Right On Q','2026-10-21','推理能力恢复：在量化学生自身生成前缀上蒸馏，使用Dynamic KL处理概率偏差；应与固定答案序列恢复分开比较。'),('2610.28947','Is 2:4 Sparsity Still Worth It?','2026-10-20','稀疏与量化的取舍：将稀疏元数据计入位率，比较继续降精度与叠加2:4；挑战“叠加两种压缩一定更好”的假设。'),('2610.31646','Low-Bit N-Gram Embeddings','2026-10-22','量化对象扩展到n-gram嵌入表；表内存节省不能当作整个模型的内存下降。')]
save('cloud_core_sources',[dict(source_id='source-wq-pending-'+n,business_id='cloud-core',batch_id='weight-refresh-20261023',canonical_url='https://arxiv.org/abs/'+n,external_id=n+'v1',last_checked_at='2026-10-23',provider='arxiv.org',source_kind='paper',title=t,update_policy='follow_original_url_record_versions',verification_status='abstract_reviewed') for n,t,d,b in pending],'source_id')
DATA.append(('refresh_watch','新发现待深审：四条可能改变路线的线索','\n'.join(d+' · '+t+'：'+b for n,t,d,b in pending)+'\n证据等级：以上仅核对原始摘要与身份，尚未审核实验表、完整成本和复现代码；暂不纳入已成立的效果对照或推荐排名。','New candidates awaiting section review','\n'.join(d+' · '+t+': original abstract reviewed; experimental tables, costs and code not yet audited.' for n,t,d,b in pending),['source-wq-pending-'+n for n,t,d,b in pending],'原始摘要及提交历史，v1；待审实验配置/表格/成本；不是全文核验。'))
for i,d in enumerate(DATA):
 if d[0]=='refresh_coverage':
  values=list(d);values[2]+='\n学术索引：另外取回cs.CL、cs.LG、cs.AI、cs.DC近期索引共'+str(recent_count)+'条分类记录（含跨类重复），标题规则命中后去重得到'+str(candidate_count)+'条候选。标题未命中不等于正文无关；除本页列明的材料外，其余候选尚未完成内容审阅。';DATA[i]=tuple(values)
for n,(slug,title,body,etitle,ebody,ids,locator) in enumerate(DATA):
 key='parameters-precision__'+slug
 cards.append(dict(business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,title_zh=title,title_en=etitle,body_zh=body,body_en=ebody,position=130+n,reviewed_at='2026-10-23',section_kind='comparison',card_kind='analysis',claim_kind='research_analysis'))
 for s in ids:
  rid=key+'__'+s
  refs.append(dict(reference_id=rid,business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id=key,source_id=s,checked_at='2026-10-23',review_depth='abstract_review' if 'pending-' in s else 'section_review',observed_version=next((x[3] for x in SOURCES if x[0]==s),'v1' if 'pending-' in s else 'latest observed 2026-10-23'),locator_zh=locator,locator_en='Review scope: '+locator+' No independent reproduction.'))
save('ic_compression_topic_cards',cards,'card_id');save('ic_compression_topic_card_refs',refs,'reference_id')
changes=[]
for x in read('ic_compression_topic_cards'):
 r=x['row'];cid=r.get('card_id','')
 if cid=='parameters-precision__expert_updates':
  changes.append({**r,'title_zh':'本轮更新：哪些判断被新证据改变','body_zh':'2026-10-23 · 更新结论：2-bit质量不能只按量化算法排名；校准/恢复数据的交互需要纳入比较。低比特与多Token预测也不是两项加速比直接相乘。\n证据位置：下方新增“新证据挑战”“交叉路线”和“产业核对”三组记录，保留问题、方法、效果与限制。\n覆盖说明：本轮登记入口均已尝试读取，但内容级全量采集尚未完成；具体失败与未覆盖范围见本轮采集边界。','body_en':'2026-10-23 update: compare calibration/recovery data interactions alongside algorithms. Low-bit and MTP speedups do not multiply by default.\nEvidence: new counterexample, cross-route and industry checks below.\nCoverage: all registered entrypoints attempted; complete content retrieval remains unfinished.','reviewed_at':'2026-10-23'})
 if cid=='parameters-precision__landscape_calibration':
  changes.append({**r,'body_zh':r['body_zh'].split('\n本轮修订：')[0]+'\n本轮修订：Beyond 4 Bits将校准数据与恢复数据交叉比较，提示数据分布不是固定背景条件。2-bit比较应同时登记两类数据与恢复预算，而非只更换算法名。','body_en':r['body_en'].split('\nUpdate:')[0]+'\nUpdate: Beyond 4 Bits motivates joint calibration/recovery data accounting at 2 bits; record data and recovery budget alongside the algorithm.'})
save('ic_compression_topic_cards',changes,'card_id')
key='parameters-precision__landscape_calibration__source-wq-beyond4-261028537'
save('ic_compression_topic_card_refs',[dict(reference_id=key,business_id='cloud-core',topic_id='cloud_core',compression_topic_id='parameters-precision',card_id='parameters-precision__landscape_calibration',source_id=SOURCES[0][0],checked_at='2026-10-23',review_depth='section_review',observed_version='2610.28537v1',locator_zh='§3–4.2，表1–2；数据交互局限见§6。',locator_en='Sections 3–4.2, Tables 1–2; interaction limitations in Section 6.')],'reference_id')
save('ic_compression_topic_card_refs',[{**r,'card_id':'parameters-precision__expert_updates','reference_id':'parameters-precision__expert_updates__'+r['source_id']} for r in refs if r['card_id'] in ['parameters-precision__refresh_data','parameters-precision__refresh_mtp']],'reference_id')
reviewed={'2610.28537':'selected_sections_reviewed','2610.28500':'selected_sections_reviewed',**{n:'abstract_reviewed_pending_sections' for n,t,d,b in pending}}
queue={c['arxiv_id']:{**c,'status':reviewed.get(c['arxiv_id'],'title_candidate_pending_abstract'),'url':'https://arxiv.org/abs/'+c['arxiv_id']} for r in recent for c in r.get('candidates',[])}
(ROOT/'research/source-audits/2026-10-23/candidate-queue.json').write_text(json.dumps(list(queue.values()),ensure_ascii=False,indent=2),encoding='utf-8')
doc='''# 权重量化信息更新与信息源阅读改版 · 2026-10-23

仅本地审核，未推送、未发布。内容写入统一维护源；UI从维护源码构建。

## 采集漏斗

- 332个登记渠道入口全部尝试读取；270个返回样本，62个失败。入口成功不等于全站事件采集成功。
- arXiv cs.CL/cs.LG/cs.AI/cs.DC近期索引：3,800条分类记录，包含跨类重复；标题规则命中去重36条候选。
- 两篇论文核对指定章节/表格；另四篇核对原始摘要，等待深审。剩余候选保持待审，不能解释为不相关。
- 产业资料核对vLLM Ascend模型教程、量化指南与msModelSlim仓库消息；没有将仓库首页或最新主干等同于发布版支持矩阵。
- 尚未完成所有登记源的日期窗口、历史分页和全文审核；没有宣称全量内容已收齐。

## 新证据怎样改变判断

1. Beyond 4 Bits：增加恢复不一定提升生成质量；校准和恢复数据需联合选择。质量评估用反量化权重，不代表低比特执行实测。
2. BitMTP：训练与运行时协同，不能当任意PTQ模型可直接叠加的解码开关；解码循环计时不等于端到端服务。
3. Ascend实现：有部署教程不代表已有完整调优结论；FP8检查点的文件格式、驻留类型、执行格式分别记录。
4. 待审：SQuAT、OnQ、2:4与量化取舍、低比特n-gram嵌入；只有摘要级认识，不进入已成立效果排名。

## 信息源页

默认显示四列表格：信息源/层级、原始链接、定位用途、跟踪重点。同源多入口合并；核心/补充由既有优先级推导，不新增虚构筛选结果。学术/产业/热点分类保留，当前筛选结果一次列出，减少翻页。版本变化和采集记录保留在后方。

审计文件：entrypoints.json、arxiv-recent.json、candidate-queue.json，均在research/source-audits/2026-10-23/。
'''
(ROOT/'docs/WEIGHT-REFRESH-SOURCE-DIRECTORY-20261023.md').write_text(doc,encoding='utf-8')
print('Added four visible update records, three sources and linked evidence; updated calibration judgment.')
