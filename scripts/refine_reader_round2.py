"""Second editorial pass: executable plans and a focused source directory."""
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'original-reader/site/business_insight/cloud_core'
LABELS=['验证对象','对照方案','测量指标','继续条件','停止条件']
PLANS={
 'parameters-precision':[
  '以 LLM 的热点线性层为起点，验证 AWQ 的通道缩放或 GPTQ 的误差补偿是否值得接入低比特权重执行链。',
  '固定模型、校准样本和独立业务集，在共同支持的位宽、分组和格式下比较 RTN、AWQ、GPTQ；浮点模型作为质量参考。领域模型另用实际框架支持的 INT8 PTQ 对照。',
  '逐任务质量、权重实际字节、峰值内存；LLM 分开测 TTFT、TPOT 和吞吐，领域模型测逐帧或逐句时延。计入尺度、保留高精度层和反量化开销。',
  '业务质量损失低于约定的 1% 门槛，且容量、目标负载时延或时延约束下吞吐得到净改善，才扩大层覆盖。',
  '质量未过关时先做敏感层保留精度的消融；格式或算子不通时先解决执行链，不以量化文件大小推断提速。'],
 'parameters-selection':[
  '优先选择领域模型中占时明显的卷积块或 FFN，研究能改变实际尺寸的结构裁减。LLM 非结构化剪枝先确认稀疏执行支持。',
  '比较原结构、按计算量裁减和按目标设备实测时延裁减；使用相同恢复训练数据与预算，同步调整相邻层及导出图。',
  '导出后的张量尺寸、任务质量、恢复训练成本、峰值内存、P95 时延及目标时延下吞吐。',
  '质量损失低于约定的 1%，且目标设备上的执行图确实变小并带来业务收益，再扩大裁减范围。',
  '若只把权重置零、编译后仍执行原形状，暂停性能推广；若质量持续不达标，减小裁减比例或转向量化。'],
 'parameters-factorization':[
  '在允许改图的热点线性层，验证 ASVD 或 SVD-LLM 的输入感知校准是否优于普通截断 SVD。',
  '固定校准集与恢复预算，在相同参数预算下比较未分解、普通 SVD 与激活感知分解；逐步扫描候选秩。',
  '因子总字节、两段矩阵乘时延、额外中间张量、层输出误差、业务质量和整模型时延。',
  '业务质量损失低于约定的 1%，并且因子存储或整模型执行成本有净改善，再扩展到其他层。',
  '若两个小矩阵的启动与中间写回抵消节省，停止按该秩扩展；重建误差较小但任务退化时，以任务结果为准。'],
 'parameters-distillation':[
  '选择一个业务允许替换的小学生模型，验证教师监督能否在较低部署成本下保留所需能力。',
  '固定学生结构、训练数据和预算，对比仅任务标签训练与加入教师输出或表征监督；教师模型作为能力参考。',
  '逐任务质量、难例与分布变化、训练成本；学生的内存、P95 时延和时延约束下吞吐。',
  '学生质量损失低于约定的 1%，且目标设备部署成本下降，才增加业务覆盖。',
  '若质量不足，先判断学生容量和监督数据是否合适；若业务不允许替换或重训模型，不启动该路线。'],
 'activations-precision':[
  '验证 SmoothQuant 的等价缩放能否改善 W8A8 质量，并在目标执行栈中减少预填充或并发计算成本。',
  '相同模型与样本下比较浮点、普通 W8A8、SmoothQuant-W8A8，以及敏感层保留高精度的版本。',
  '逐层输出偏差、业务质量、缩放与转换耗时、峰值激活；LLM 测 TTFT、TPOT 与吞吐，领域模型测任务时延。',
  '质量损失低于约定的 1%，且低精度计算的收益覆盖在线变换成本，才增加量化层数。',
  '若普通 W8A8 已达标且平滑没有额外价值，不保留额外处理；若频繁转换抵消收益，先改融合与布局。'],
 'activations-selection':[
  '确认业务是否包含图像或视频输入；只有任务证据匹配时，才把 SparseVLM 等视觉 token 选择作为候选。',
  '在同一模型、输入尺寸和 token 预算下，比较不裁减、简单选择与候选方法；文本或音频业务另找对应机制证据。',
  '选择与索引耗时、实际跳过的计算、后续层时延、峰值内存和任务质量，重点检查细节丢失。',
  '对应业务质量损失低于约定的 1%，且包含选择成本的端到端时延或吞吐改善，才增加裁减预算。',
  '当前任务没有对应输入或方法证据时暂缓；若掩码没有减少实际执行工作，先修执行路径，不扩大 token 删除。'],
 'activations-merging':[
  '以 ToMe 为机制参考，验证在允许聚合的模型中，合并相近 token 是否比直接删除更好地保留信息。',
  '在相同保留预算与合并位置下，比较不压缩、token 剪枝和 token 合并；保持任务与输入尺寸一致。',
  '相似性匹配、聚合及 gather 开销，后续层计算时延、峰值内存、细粒度任务质量及位置约束。',
  '质量损失低于约定的 1%，且后续计算节省覆盖匹配与聚合成本，再增加合并层或输入规模。',
  '细节或位置信息受损时减少合并；因果文本和流式音频尚未验证时序约束前，不直接迁移视觉结论。'],
 'activations-factorization':[
  '先通过执行图确认长序列任务是否仍受注意力中间矩阵限制，再评估 Linformer 或 Nyströmformer。',
  '在一个允许结构改造的模块内比较精确注意力、序列投影或 landmark 近似，固定训练预算并扫描近似维度。',
  '因果或流式约束、任务质量、峰值工作区、额外投影或求逆耗时，以及完整模块时延。',
  '存在明确的中间量瓶颈，业务允许训练改造，且质量损失低于约定的 1% 并有净收益，才扩大到整模型。',
  '若现有融合实现已避免物化大矩阵，或训练与改核成本超出收益，暂缓架构替换。'],
 'activations-distillation':[
  '选择可重训的领域模型，研究 FitNets 式特征监督能否帮助更窄的学生保持质量。',
  '固定窄学生结构、数据和训练预算，比较无蒸馏与加入特征监督；TinyBERT、MobileBERT 仅作相应编码器的结构参考。',
  '推理图的中间张量尺寸、峰值激活与工作区、任务质量、逐帧或逐句时延，以及训练辅助分支是否已移除。',
  '质量损失低于约定的 1%，且实际中间张量和部署成本下降，再增加结构缩减。',
  '若业务不能重训或更换结构则暂缓；只有训练损失下降、推理张量未变小，不视为压缩成功。'],
 'kv_cache-precision':[
  '在长上下文或并发受 KV 容量限制的 LLM 中，比较 KIVI、KVQuant 的分组与异常值处理思路。',
  '固定模型和权重精度，以未压缩 KV 为基线，扫描目标栈可执行的 KV 位宽、分组与高精度近期窗口。',
  '长检索、多轮和长生成质量；含尺度与窗口的实际缓存字节、峰值内存、同并发 TTFT/TPOT，以及同延迟约束下吞吐。',
  '质量损失低于约定的 1%，且容量改善能换来更长有效上下文、更多并发或更低时延，再考虑更低位宽。',
  '若注意力核反复展开完整高精度缓存，先检查转换成本；质量长尾退化时，提高敏感层或近期窗口精度。'],
 'kv_cache-kv_eviction':[
  '研究 H2O、SnapKV 等预算选择机制，并先确认分页管理能够实际回收被淘汰的 KV 空间。',
  '相同模型与请求轨迹下，对照完整 KV、滑动窗口与一个候选策略；策略之间按相同物理缓存预算比较。',
  '实际占用页数与预算超限率、评分及回收耗时、长检索和多轮质量、TTFT、TPOT 和可服务并发。',
  '质量损失低于约定的 1%，物理占用确实下降，且评分回收开销不破坏时延门槛，才扩大采用范围。',
  '逻辑条目变少但物理页未释放时先修管理接口；误删关键历史信息时放宽预算，而非仅优化淘汰率。'],
 'kv_cache-selection':[
  '以 ThinK 的查询感知 Key 通道选择为参考，验证特征维压缩能否被目标注意力算子直接使用。',
  '从一个注意力层开始，对比完整特征与不同通道预算，明确 K/V 处理轴、RoPE 和查询依赖。',
  '选择耗时、缓存实际字节、布局转换与重建成本、长检索质量和整模型解码时延。',
  '质量损失低于约定的 1%，压缩布局可执行且总成本下降，再增加层覆盖。',
  '若每步必须完整恢复原布局，先核算重建与临时内存；净收益不成立时转向 KV 量化或页级预算。'],
 'kv_cache-factorization':[
  '以 AttSVD 为候选，研究注意力感知选秩能否在保留 token 的同时降低长上下文缓存占用。',
  '在同一模型与长文本请求中比较完整 KV、固定秩 SVD 与注意力感知选秩，分别扫描近期精确窗口。',
  '长检索与生成质量，因子、窗口和工作区总字节；分解计入 TTFT，持续压缩及重建计入 TPOT。',
  '质量损失低于约定的 1%，且同一时延门槛下可服务并发或有效上下文增加，再扩大验证。',
  '短输出不足以摊薄分解成本，或重建抵消容量收益时暂缓；无自回归 KV 的领域模型不安排此实验。'],
 'kv_cache-distillation':[
  '以 X-EcoMLA 为参考，验证已有模型转换为紧凑 KV 结构后，教师监督能恢复多少任务能力。',
  '固定紧凑学生结构，对比初始化转换、仅任务训练和加入教师监督，保持数据及训练预算可比。',
  '短任务与长检索质量、训练成本、潜在缓存与 RoPE 布局、目标设备峰值内存、TTFT/TPOT 和吞吐。',
  '业务允许训练改造，算子路径可实现，且质量损失低于约定的 1% 并有部署收益，才投入全量训练。',
  '缺少结构算子支持时先做模块原型；任务质量持续不足或恢复训练成本超出预算时暂缓转换。'],
 'kv_cache-sharing':[
  '验证 MHA 转为 GQA/MQA 时，共享 KV 头的比例如何影响缓存、质量和执行效率。',
  '允许模型转换时，固定学生结构选择规则和训练预算，扫描分组比例；已有 GQA 模型以自身实际头数为基线。',
  'Q/K/V 头数、缓存字节/token、转换训练成本、任务与长检索质量、注意力核工作量和解码时延。',
  '质量损失低于约定的 1%，且共享后的布局可直接执行并有容量或性能收益，才扩大使用。',
  '不允许改模型时不启动头数转换；避免把既有 GQA 自带的节省重复计作新压缩收益。'],
 'kv_cache-compact_architecture':[
  '从已有公开检查点与兼容执行实现入手，评估 MLA 等紧凑状态架构能否满足业务能力和部署约束。',
  '与业务能力相近的基线比较；原生架构部署和旧模型结构转换分别立项，不合并训练与适配成本。',
  '业务质量、缓存表示与字节、恢复计算、通信和维护成本；分别测 TTFT、TPOT 与时延约束下吞吐。',
  '检查点能力达到业务要求，执行链完整，且总成本有净改善，才增加业务覆盖。',
  '缓存虽小但能力不足、训练成本过高或执行支持缺失时暂缓，不按理论缓存比例直接替换已有服务。'],
}

def refine_plans():
 path=ROOT/'data/compression/tables/ic_compression_topic_cards/rows.jsonl'
 records=[json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()];changed=[]
 for item in records:
  r=item['row'];topic=r.get('compression_topic_id')
  if topic in PLANS and r['card_id']==topic+'__dossier_6' and r['claim_kind']=='research_analysis':
   body='\n'.join(label+'：'+value for label,value in zip(LABELS,PLANS[topic]))
   if r['body_zh']!=body:changed.append(item['key'])
   r['body_zh']=body
 path.write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in records),encoding='utf-8')
 return changed

def main():
 changed=refine_plans()
 p=BASE/'compression.js';text=p.read_text(encoding='utf-8')
 old="function refreshImportedPapers(){\n globalThis.LRIImportedPaperReview?.update("
 new="""function refreshImportedPapers(){
 const queue=document.getElementById('imported-paper-review'),reviewRequested=location.hash==='#imported-paper-review';
 if(queue)queue.hidden=state.view!=='sources'||!reviewRequested;
 globalThis.LRIImportedPaperReview?.update("""
 assert old in text or new in text
 text=text.replace(old,new)
 old="locale:state.locale,view:state.view,scope:state.scope||new URLSearchParams(location.search).get('scope')||'',strings:state.packs[state.locale]?.strings||{}});"
 new="locale:state.locale,view:state.view==='sources'&&!reviewRequested?'idle':state.view,scope:state.scope||new URLSearchParams(location.search).get('scope')||'',strings:state.packs[state.locale]?.strings||{}});"
 assert old in text or new in text
 text=text.replace(old,new)
 # Hide pagination when it cannot change the directory; retain the empty-state message.
 anchor="$('channel-prev').hidden=industry;$('channel-next').hidden=industry;"
 repl="$('channel-prev').hidden=industry||rows.length<=20;$('channel-next').hidden=industry||rows.length<=20;"
 text=text.replace(anchor,repl)
 if "$('channel-prev').parentElement.hidden=industry||rows.length<=20;" not in text:text=text.replace(repl,repl+"$('channel-prev').parentElement.hidden=industry||rows.length<=20;")
 text=text.replace("+' · '+mapText('按类别读取，采集状态按需展开','Loaded by category; expand collection status on demand');", ";")
 # Semantic plans carry all original proposed content, rather than hide it in another disclosure.
 old="else appendResearchText(card,textOf(row,'body'));"
 new="else if(row.section_kind==='watch'&&row.claim_kind==='research_analysis')renderValidationPlan(card,textOf(row,'body'));else appendResearchText(card,textOf(row,'body'));"
 assert old in text or new in text
 text=text.replace(old,new)
 if 'function renderValidationPlan(' not in text:
  helper="""function renderValidationPlan(parent,text){
 const lines=text.split(/\\n+/).filter(Boolean),pairs=lines.map(line=>/^([^：:]{1,24})[：:]\\s*(.+)$/.exec(line));
 if(pairs.some(pair=>!pair)||pairs.length<3){appendResearchText(parent,text);return;}
 const plan=element('dl','','validation-plan');
 for(const pair of pairs){const row=element('div','','validation-plan-row');row.append(element('dt',pair[1]),element('dd',pair[2]));plan.append(row);}
 parent.append(plan);
}
"""
  text=text.replace('function appendResearchText(parent,text,cls=',helper+'function appendResearchText(parent,text,cls=',1)
 text=text.replace("const row=element('div','','validation-plan-row');row.append", "const row=element('div','','validation-plan-row');row.dataset.validationRole=pair[1]==='继续条件'?'continue':pair[1]==='停止条件'?'stop':'content';row.append")
 marker="function appendResearchText(parent,text,cls='topic-dossier-body'){"
 guard="\n if(text.startsWith('验证对象：')&&text.includes('\\n停止条件：')){renderValidationPlan(parent,text);return;}"
 if guard not in text:text=text.replace(marker,marker+guard,1)
 p.write_text(text,encoding='utf-8')
 p=BASE/'paper-review.js';text=p.read_text(encoding='utf-8')
 anchor="root.replaceChildren(el('h3',ui('paper_pipeline_title')),el('p',ui('paper_pipeline_help'),'reader-note'));"
 repl=anchor+"\n const back=el('a',ctx.locale==='en'?'← Back to source directory':'← 返回信源目录','review-queue-back');back.href='#view-sources';root.prepend(back);"
 if 'review-queue-back' not in text:text=text.replace(anchor,repl,1)
 p.write_text(text,encoding='utf-8')
 for name in ['index.html','topic.html','monthly.html','foundations.html']:
  p=BASE/name;t=p.read_text(encoding='utf-8')
  if 'reader-refinement.css' not in t:t=t.replace('</head>','<link rel="stylesheet" href="reader-refinement.css?v=round2-20261022">\n</head>',1)
  p.write_text(t,encoding='utf-8')
 p=BASE/'data/focus-ui.zh.json';pack=json.loads(p.read_text(encoding='utf-8'))
 pack['strings'].update({'paper_review_entry':'资料处理工作台 →','paper_pipeline_help':'在这里查看候选筛选、资料补全和论文研读进度。候选列表服务于研究工作，不代表技术已经适用；成熟判断见研究专题与洞察报告。','source_search':'搜索项目、网站或研究方向','source_subcategory':'研究用途','source_display':'收录范围'})
 p.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (BASE/'reader-refinement.css').write_text(CSS,encoding='utf-8')
 spec=importlib.util.spec_from_file_location('reader_copy',ROOT/'scripts/refine_reader_copy.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);builder.rebuild()
 receipt={'date':'2026-10-22','status':'local_review_not_published','plans':len(PLANS),'plan_card_ids':[topic+'__dossier_6' for topic in PLANS],'changed_this_run':changed,'source_queue':'Explicit #imported-paper-review only; no candidate pipeline read on the default source directory.','result_values':'Unchanged; protocol cards are research proposals, not measured results.','public_sites_changed':False}
 (ROOT/'docs/editorial-round2-20261022.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Second pass:',len(PLANS),'structured plans; source directory and review queue separated')

CSS='''/* Round 2: clear reading hierarchy and practical experiment protocols. */
.compression-research-workbench #channels-panel{margin-top:16px}
.compression-research-workbench #channels-panel>.wb-filters{margin-top:16px;padding:14px 16px;border-radius:10px;background:#f7fafb}
.compression-research-workbench #channels-panel>.wb-filters label{font-size:12px;color:#536778;display:block;margin-bottom:6px}
.compression-research-workbench #channels-panel>.wb-filters input,.compression-research-workbench #channels-panel>.wb-filters select{min-height:42px;font-size:14px;border:1px solid #d8e2e7;border-radius:7px;box-sizing:border-box;background:#fff;width:100%}
.compression-research-workbench #channel-status{margin:12px 0 22px}
.compression-research-workbench #channel-cards>section>h4{margin-top:18px}
.compression-research-workbench .validation-plan{display:grid;margin:18px 0 10px;border:1px solid #dce7eb;border-radius:10px;overflow:hidden;background:white}
.compression-research-workbench .validation-plan-row{display:grid;grid-template-columns:100px minmax(0,1fr);margin:0;border-bottom:1px solid #e5edf0}
.compression-research-workbench .validation-plan-row:last-child{border-bottom:0}
.compression-research-workbench .validation-plan dt{padding:14px 16px;background:#f4f8f9;font-size:13px;color:#345469;font-weight:650;line-height:1.8}
.compression-research-workbench .validation-plan dd{margin:0;padding:14px 18px;line-height:1.9;font-size:15px;color:#273f50;overflow-wrap:anywhere}
.compression-research-workbench .validation-plan-row[data-validation-role="continue"] dt{color:#13665c;background:#edf7f3}
.compression-research-workbench .validation-plan-row[data-validation-role="stop"] dt{color:#8a4c26;background:#fbf6ef}
.compression-research-workbench .review-queue-back{display:inline-block;margin-bottom:16px;color:#087e81;font-weight:600}
.compression-research-workbench #imported-paper-review{border-top:1px solid #dce7eb;padding-top:28px;margin-top:32px}
@media(max-width:640px){.compression-research-workbench .validation-plan-row{grid-template-columns:1fr}.compression-research-workbench .validation-plan dt{padding:10px 14px}.compression-research-workbench .validation-plan dd{padding:10px 14px 16px}.compression-research-workbench #channels-panel>.wb-filters{padding:12px}}
'''

if __name__=='__main__':main()
