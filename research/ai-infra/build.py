# -*- coding: utf-8 -*-
from pathlib import Path
from html import escape as e
import json
from research import enrich, R as research_routes
R=Path(__file__).parent; D=R/'dist'; D.mkdir(exist_ok=True)
groups=[('evaluation','性能评测','先定位瓶颈，再判断技术收益。'),('hardware','硬件加速','提高资源供给与复用能力。'),('compression','推理压缩','沿用已有对象 × 方法专题体系。'),('iteration','迭代算法加速','减少重复、无效与串行计算。'),('operators','算子定制加速','把算法收益转化为真实执行效率。'),('scheduling','组合调度加速','让模型、请求与资源更合理地配合。')]
# Each entry: exact title, problem, mechanism, candidate routes, experiment, boundary, original source.
data={
'evaluation':[
('硬件/模型性能评测','硬件峰值与模型服务性能之间存在差距，平均时延也会掩盖尾部请求。','先固定模型、精度、输入输出长度与到达负载，再分别测单算子、单实例和在线服务。','算子微基准；模型端到端压测；计算、访存、通信和排队归因。','LLM 记录 TTFT、TPOT、P95/P99 和达标吞吐；领域模型记录任务质量、端到端时延与样本吞吐。比较同一硬件预算下的基线。','精度损失小于 1% 是业务目标，需明确具体指标以及相对下降还是百分点下降；未经实测不填写收益。','MLPerf Inference','https://mlcommons.org/benchmarks/inference-datacenter/')],
'hardware':[
('硬件增强','模型计算、内存容量、访存带宽或互连能力可能形成硬约束。','围绕实际瓶颈选择计算单元、存储层级与互连配置；增加峰值算力不保证端到端加速。','计算与存储能力匹配；内存容量规划；多卡互连与数据通路优化。','在 310P、910B 与 950（型号待确认）分别建立能力表；固定模型与负载，比较容量、时延、吞吐及能耗。','这里讨论硬件能力与配置，不把软件算子调优重复归入；不预设具体设备的低精度支持。','MLPerf 硬件系统比较','https://mlcommons.org/benchmarks/inference-datacenter/'),
('虚拟化复用','独占部署可能浪费资源，共享部署又可能引入干扰。','通过资源分区、时间复用或进程并发提高利用率，并核对隔离与服务保障。','空间分区；时间复用；进程级共享及配额限制。','先比较两个领域模型独占和共卡的吞吐、内存峰值及最差时延，再加入 LLM 干扰负载。','MIG 是 NVIDIA 的实现参考，不代表昇腾具备同样接口；共享模式与故障隔离需要逐设备验证。','NVIDIA MIG 官方机制参考','https://docs.nvidia.com/datacenter/tesla/mig-user-guide/introduction.html')],
'iteration':[
('缓存代计算','重复前缀或重复中间状态导致相同计算反复发生。','保存可安全复用的计算结果，用查找与读取替代重新计算。','请求内 KV 复用；跨请求前缀缓存；分层缓存与缓存感知路由。','在固定模型下比较冷缓存与不同重复前缀比例，记录命中率、TTFT、内存及淘汰后的退化。','缓存复用与 KV 压缩分别维护；必须验证缓存键、模型版本与输入一致性，避免错误复用。','vLLM 前缀缓存','https://docs.vllm.ai/en/v0.7.0/design/automatic_prefix_caching.html'),
('数据稀疏化','部分 token、特征或连接对当前输出贡献较小，但筛选本身也有成本。','选择参与本轮计算的数据子集，使实际执行路径跳过低贡献部分。','Token 选择；激活稀疏；稀疏 Attention；结构化稀疏执行。','对输入长度和任务难度分组，比较稀疏比例、选择开销、质量下降和真实算子时间。','已有激活剪枝、权重剪枝专题负责压缩机制；本项重点看迭代中的数据选择和跳过执行。零值变多不等于运算变少。','原有激活剪枝专题','topic-activations-selection.html'),
('迭代次数压缩','自回归生成或迭代求解需要多次串行执行，形成时延下限。','让一次昂贵验证接受多个候选，或在满足任务质量条件时减少求解步数。','推测解码；多步候选验证；适用模型的提前退出与少步采样。','LLM 先对比无草稿与推测解码，记录接受长度、草稿开销、TPOT 和吞吐；高并发与低并发分别测。','推测解码不等于减少输出 token；保分布结论依赖正确验证算法。降噪模型是否迭代求解尚待确认，不默认套用扩散路线。','Speculative Decoding 原论文','https://arxiv.org/abs/2211.17192')],
'operators':[
('计算算子加速','低效访存、算子启动或数据布局会吞掉算法层的理论收益。','通过分块、数据复用、融合和流水减少搬运与启动开销，使算子更贴近硬件。','矩阵乘调优；Attention 融合；量化解包与计算融合；动态形状专门化。','先从 profiler 找到占时最高的算子，固定 shape 与精度进行替换；报告算子加速和端到端加速两项。','算子微基准不能代替业务测量；尺寸分布、数值误差和回退路径必须覆盖。','Apache TVM 编译与优化架构','https://tvm.apache.org/docs/arch/'),
('通信算子加速','多卡拆分后，集合通信与同步等待可能限制扩展。','按消息大小和拓扑选择通信算法，并将可并行的通信与计算重叠。','AllReduce / AllGather / ReduceScatter；All-to-All；拓扑感知与通信计算重叠。','按实际张量大小测试通信曲线，再放回模型比较通信占比、重叠率及端到端时延。','改变并行切分归入单模型实例多卡调度；本项优化已有切分下的数据交换实现。','PyTorch 分布式通信','https://docs.pytorch.org/docs/stable/distributed.html')],
'scheduling':[
('异构资源调度','不同设备的容量、算子支持与性能不同，按卡数均分往往失效。','建立任务到设备的可执行约束和代价模型，再选择放置与迁移策略。','能力感知放置；性能画像；异构资源配额；迁移成本约束。','对 LLM 与领域模型建立设备兼容矩阵，以最短队列为对照，比较排队、执行时间及失败率。','型号与软件栈未确认前不写已支持；跨设备迁移要计入模型加载和数据搬运。','Kueue 资源与准入机制','https://kueue.sigs.k8s.io/docs/overview/'),
('单模型实例多卡调度','单卡容量不足或性能受限，需要让一个模型实例跨卡执行。','把参数、计算或专家分配到多卡，并协调计算顺序与同步。','张量并行；流水线并行；专家并行；上下文并行与混合并行。','固定模型与精度，对比可运行的不同并行配置，记录内存、通信占比、TTFT、TPOT 及每卡有效吞吐。','更多卡不必然更快；张量并行的通信代价与流水线气泡分别分析。','PyTorch 分布式体系','https://docs.pytorch.org/tutorials/beginner/dist_overview.html'),
('业务感知调度','不同请求的长度、时限和优先级不同，统一排队容易伤害尾时延。','依据请求代价与服务目标进行排序、组批和准入，而非仅追求总 token 吞吐。','连续批处理；分块预填充；期限或优先级感知排程；过载准入控制。','用相同到达轨迹对比先来先服务与候选策略，记录各类业务达标率、拒绝率及长请求等待。','服务目标需要先定义；短请求收益不能掩盖长请求饥饿。Agent 工作流规划仍归极智-Agent。','Kueue 准入控制概念','https://kueue.sigs.k8s.io/docs/concepts/'),
('多模型实例多卡调度','多个模型或副本争用资源，冷启动、缓存冷热和负载失衡会降低服务能力。','在实例池与设备池之间协调副本数量、放置和请求路由，并计入重配置成本。','副本放置；负载均衡；缓存亲和路由；弹性伸缩；P/D 实例资源配比。','固定总卡数与业务混合比例，对比静态分配和动态策略，记录各业务达标吞吐、冷启动与资源闲置。','与单模型实例内部切分区分；P/D 分离涉及状态传输，不能忽略 KV 搬运与网络成本。','vLLM P/D 分离','https://docs.vllm.ai/en/v0.20.2/features/disagg_prefill/')]
}
topics=sorted([x['row'] for x in json.loads((R/'compression-topics.json').read_text(encoding='utf-8'))['rows']],key=lambda x:x['position'])
sections=[x['row'] for x in json.loads((R/'compression-sections.json').read_text(encoding='utf-8'))['rows']]
def shell(title,body,active=''):
    nav=''.join(f'<a class="{"active" if active==k else ""}" href="index.html#{k}"><span>0{i+1}</span>{n}</a>' for i,(k,n,_) in enumerate(groups))
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>'+e(title)+' · AI Infra 研究预览</title><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="atlas.css"></head><body class="'+('map-page' if not active else 'topic-page')+'"><a class="skip" href="#main">跳到正文</a><header><a class="brand" href="index.html"><b>极智</b><span>AI Infra <small>研究预览</small></span></a><span class="draft">独立审阅稿 · 未替换对外版本</span></header><aside><p class="eyebrow">研究目录</p>'+nav+'<div class="side-note">分类按已确认目录。<br>原理、证据与验证建议分开呈现。</div></aside><main id="main">'+body+'</main><footer>CCN · 2026-10-21 · 新增内容为研究建议，未宣称昇腾实测收益。</footer><script src="app.js"></script></body></html>'
def cite(label,url):return '<a class="citation" href="'+e(url,quote=True)+'"'+(' target="_blank" rel="noopener"' if url.startswith('http') else '')+'>'+e(label)+' ↗</a>'
def card(title,text,url,tag):return '<a class="card" href="'+url+'"><span class="tag">'+tag+'</span><h3>'+e(title)+'</h3><p>'+e(text)+'</p><span class="more">查看研究内容 <i>↗</i></span></a>'
intro='<section class="hero"><p class="eyebrow">AI INFRA / RESEARCH ATLAS</p><h1>从性能瓶颈，找到技术突破口。</h1><p class="lead">围绕评测、硬件、压缩、算法、算子与调度六个方向，连接技术原理、已有研究和下一步业务验证。</p><div class="hero-bottom"><span><b>06</b> 一级分类</span><span><b>12</b> 新增二级技术项</span><span><b>16</b> 保留压缩专题</span><a href="#map">浏览技术目录 ↓</a></div></section>'
intro+='<section class="reading"><strong>怎么读</strong><span>先定位瓶颈</span><i>→</i><span>选择根技术</span><i>→</i><span>查看路线与证据</span><i>→</i><span>明确验证任务</span></section><div class="toolbar" id="map"><h2>技术目录</h2><input id="search" type="search" placeholder="搜索技术、挑战或路线" aria-label="搜索技术"></div>'
intro='<section class="map-intro"><div><p class="eyebrow">AI INFRA / ROOT TECHNOLOGY MAP</p><h1>AI Infra 根技术地图</h1><p>从六个技术方向进入研究。连线表示分类归属，点击节点查看具体路线与验证建议。</p></div><div class="map-stats"><b>6</b><span>根技术分支</span><b>13</b><span>研究入口</span></div></section><div class="toolbar" id="map"><div class="map-legend"><span class="legend-dot"></span>一级分类 <span class="legend-node"></span>可点击研究节点 <span class="legacy-dot"></span>已有完整内容</div><input id="search" type="search" placeholder="定位技术、挑战或路线" aria-label="搜索技术"></div>'
content=intro+'<div class="map-scroll" role="region" aria-label="AI Infra 根技术层级地图" tabindex="0"><div class="map-root"><span>AI Infra</span><small>根技术体系</small></div><div class="atlas">'
for i,(key,title,summary) in enumerate(groups):
    content+=f'<section class="group" id="{key}"><div class="section-head"><span class="number">0{i+1}</span><div><h2>{title}</h2><p>{summary}</p></div></div><div class="grid">'
    if key=='compression':
        original='https://c1b3ie6ayp-sworks-lrigit-tpc.ru.yxsbase.win/business_insight/cloud_core/index.html#view-topics'
        content=content.replace('<h2>推理压缩</h2>','<h2><a class="full-compression" href="'+original+'" target="_blank" rel="noopener noreferrer" title="打开原有完整推理压缩内容">推理压缩</a></h2>')
        content+=card('模型量化','通过低比特表示减少权重、激活与 KV Cache 的存储和计算开销。','compression-quantization.html','已有专题索引')
        content+=card('模型小型化','通过剪枝、蒸馏和低秩分解研究更紧凑的部署模型。','compression-small.html','已有专题索引')
    else:
        for j,row in enumerate(data[key]):
            name,problem,mechanism,routes,experiment,boundary,label,url=row
            path=f'{key}-{j+1}.html';content+=card(name,problem,path,'研究建议 · 待验证')
            body=f'<a class="back" href="index.html#{key}">← {title}</a><p class="eyebrow">{title} / 研究专题</p><h1>{name}</h1><p class="lead">{problem}</p><section class="verdict"><span class="tag">核心判断</span><h2>{mechanism}</h2></section>'
            body+='<div class="flow"><span>业务瓶颈</span><b>→</b><span>技术介入</span><b>→</b><span>对照实验</span><b>→</b><span>收益与边界</span></div>'
            body+=enrich(name,problem,mechanism,experiment,boundary)
            (D/path).write_text(shell(name,body,key),encoding='utf-8')
    content+='</div></section>'
content+='</div></div><p class="map-help">地图根据屏幕宽度自动重排，光效可暂停。点击一级标题「推理压缩」打开原有完整内容；下方两个节点分别进入模型量化与模型小型化。</p>'
content+='<p id="empty" hidden>没有匹配项，请尝试其他关键词。</p><section class="prose"><h2>业务验证的共同约束</h2><p>覆盖 LLM（以 Qwen3.8-27B 为例）及降噪、翻译等领域模型。硬件为 310P、910B 与 950（具体型号待确认）。在明确任务质量指标后，以精度损失小于 1%、高吞吐、低时延为验证目标。</p><p class="note">本轮聚焦目录与技术内容预览，没有新增月度论文统计，也没有把建议写成已实现的效果。</p></section>'
(D/'index.html').write_text(shell('根技术地图',content),encoding='utf-8')
for t in topics:
    body='<a class="back" href="index.html#compression">← 推理压缩</a><p class="eyebrow">推理压缩 / 已有专题快照</p><h1>'+e(t['title_zh'])+'</h1><p class="lead">'+e(t['question_zh'])+'</p><div class="notice">保留原站专题名称与内容。此处为专题内容快照；原有动态、PPT 与交互演示未复制到本预览。</div>'
    for s in sorted([s for s in sections if s['compression_topic_id']==t['compression_topic_id']],key=lambda x:x['position']):
        body+='<section class="prose"><h2>'+e(s['heading_zh'])+'</h2><p style="white-space:pre-line">'+e(s['body_zh'])+'</p>'+ (cite('原文依据',s['evidence_url']) if s.get('evidence_url','').startswith(('https://','http://')) else '')+'</section>'
    body+='<section class="prose">'+cite('查看原站完整专题','https://c1b3ie6ayp-sworks-lrigit-tpc.ru.yxsbase.win/business_insight/cloud_core/'+t['route'])+'</section>'
    (D/('topic-'+t['compression_topic_id']+'.html')).write_text(shell(t['title_zh'],body,'compression'),encoding='utf-8')
for slug,title,description,selected in [
 ('compression-quantization','模型量化','按实际压缩对象查看量化研究：权重、激活和 KV Cache。具体精度、算子支持与质量边界仍以各专题证据为准。',[t for t in topics if t['method_term_id']=='precision']),
 ('compression-small','模型小型化','先聚焦直接改变部署模型规模的剪枝、知识蒸馏与低秩分解。模型参数减少不必然带来时延下降，需要核对真实执行路径。',[t for t in topics if t['target_term_id']=='parameters' and t['method_term_id']!='precision'])]:
    body='<a class="back" href="index.html#compression">← 根技术地图</a><p class="eyebrow">推理压缩 / 二级技术</p><h1>'+title+'</h1><p class="lead">'+description+'</p><div class="grid">'
    body+=''.join(card(t['title_zh'],t['question_zh'],'topic-'+t['compression_topic_id']+'.html','已有研究专题') for t in selected)
    body+='</div>'
    if title=='模型量化':
        body+=enrich(title,'模型权重、激活和 KV 的容量及数据流量限制服务规模，但降低位宽也会引入数值误差。','量化将数值映射到有限编码，再通过尺度恢复近似数值；研究重点是误差控制与真实执行收益。','先在已有可运行基线上选择运行时明确支持的 W8 配置，再对照 W4 候选。分别记录权重占用、总内存、TTFT、TPOT 与业务质量，确认实际调用的量化核。','优先验证已有工具链支持的配置；低比特格式不兼容或反量化开销过高时，不应仅凭文件变小推进部署。')
    else:
        body+=enrich(title,'部署模型过大，带来容量、访存和计算成本；直接删减结构可能损失业务能力。','通过删去冗余结构、训练小型学生或低秩近似，减少部署模型的参数或计算。','领域模型先对比结构化剪枝或蒸馏的小模型；LLM 先做有限层的低秩或剪枝敏感性验证。分别报告参数量、总内存、任务质量和真实推理耗时。','质量预算严格时先做敏感性验证；非结构化稀疏缺少执行核时不作为加速首选。蒸馏需要计入数据与训练成本。')
    body+='<section class="prose">'+cite('查看原有完整推理压缩内容',original)+'</section>'
    (D/(slug+'.html')).write_text(shell(title,body,'compression'),encoding='utf-8')
# 14 second-level items; the original corpus remains reachable from its parent heading.
index=D/'index.html';index.write_text(index.read_text(encoding='utf-8').replace('<b>13</b><span>研究入口</span>','<b>14</b><span>二级技术节点</span>'),encoding='utf-8')
print('Built 31 pages with 14 second-level map nodes')
# Shared visual language across overview, research hubs and detailed snapshots.
for page in D.glob('*.html'):
    html=page.read_text(encoding='utf-8').replace('</head>','<link rel="stylesheet" href="research.css"></head>')
    if 'topic-page' in html:
        html=html.replace('<main id="main">','<main id="main"><div class="research-orbit" aria-hidden="true"><i></i><i></i><i></i><span>AI<br>INFRA</span></div>')
    page.write_text(html,encoding='utf-8')
