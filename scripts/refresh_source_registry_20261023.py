# -*- coding: utf-8 -*-
"""Correct source identities and record dated, bounded primary checks."""
import json
from urllib.parse import urlsplit
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/compression/tables';DAY='2026-10-23'
def read(t):return [json.loads(x) for x in (BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()]
def write(t,data):(BASE/t/'rows.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in data),encoding='utf-8')
def update(entry,patch):
 if any(entry['row'].get(k)!=v for k,v in patch.items()):entry['row'].update(patch);entry['row_version']+=1
def optional(t,fields):
 p=BASE/t/'definition.json';d=json.loads(p.read_text(encoding='utf-8'))
 for k in fields:d['fields'][k]=dict(projection='default',required=False,role='value',source=None,type='string')
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
channels=read('ic_channels');sources=read('cloud_core_sources');families=read('ic_source_families');members=read('ic_channel_families')
cb={x['row']['channel_id']:x for x in channels if not x['deleted']};sb={x['row']['source_id']:x for x in sources if not x['deleted']};fb={x['row']['family_id']:x for x in families if not x['deleted']}
log_path=ROOT/'research/source-audits/2026-10-23/registry-corrections.json'
log=json.loads(log_path.read_text(encoding='utf-8')) if log_path.exists() else []
def fix_url(old,new):
 if old==new:return
 for channel in cb.values():
  source=sb[channel['row']['source_id']]
  if source['row']['canonical_url']!=old:continue
  log.append(dict(channel_id=channel['row']['channel_id'],old_url=old,new_url=new,reason='official identity/redirect checked'))
  update(source,dict(canonical_url=new,provider=urlsplit(new).netloc,last_checked_at=DAY,verification_status='identity_and_entrypoint_checked'))
  update(channel,dict(updated_at=DAY))
CORRECTIONS={
 'https://github.com/frameworksai/graphiti':'https://github.com/getzep/graphiti',
 'https://github.com/hao-ai-lab/CacheBlend':'https://docs.lmcache.ai/kv_cache_optimizations/cacheblend.html',
 'https://microsoft.github.io/orleans':'https://learn.microsoft.com/en-us/dotnet/orleans/overview',
 'https://github.com/InfiniAI/InfiniGen':'https://github.com/snu-comparch/InfiniGen',
 'https://github.com/facebookresearch/DistServe':'https://github.com/LLMServe/DistServe',
 'https://github.com/DefiniteSoftware/llm-d':'https://github.com/llm-d/llm-d',
 'https://github.com/MoonshotAI/Mooncake':'https://github.com/kvcache-ai/Mooncake',
 'https://github.com/michael-wzhu/HippoRAG':'https://github.com/OSU-NLP-Group/HippoRAG',
 'https://github.com/argmaxinc/distilabel':'https://github.com/argilla-io/distilabel',
 'https://github.com/hao-ai-lab/LMCache':'https://github.com/LMCache/LMCache',
 'https://github.com/tau-bench/tau-bench':'https://github.com/sierra-research/tau2-bench',
 'https://github.com/openai/openai-agents':'https://github.com/openai/openai-agents-python',
 'https://github.com/google-research/google-research/tree/master/bfcl':'https://gorilla.cs.berkeley.edu/leaderboard.html',
 'https://docs.vllm.ai/en/latest/latest':'https://docs.vllm.ai/en/latest/',
 'https://github.com/ggerganov/llama.cpp/releases':'https://github.com/ggml-org/llama.cpp/releases',
 'https://github.com/ggerganov/llama.cpp/discussions':'https://github.com/ggml-org/llama.cpp/discussions',
 'https://github.com/ggerganov/llama.cpp/tags':'https://github.com/ggml-org/llama.cpp/tags',
 'https://github.com/ggerganov/llama.cpp/discussions/categories/quantization':'https://github.com/ggml-org/llama.cpp/discussions/categories/quantization',
 'https://github.com/ray-project/kuberay':'https://github.com/kuberay-project/kuberay',
 'https://github.com/volcengine/verl':'https://github.com/verl-project/verl',
 'https://github.com/princeton-nlp/SWE-bench':'https://github.com/SWE-bench/SWE-bench',
 'https://github.com/geekan/MetaGPT':'https://github.com/FoundationAgents/MetaGPT',
 'https://docs.modal.com':'https://modal.com/docs',
 'https://lmarena.ai':'https://arena.ai/',
 'https://epochai.org':'https://epoch.ai/',
 'https://yq.aliyun.com':'https://developer.aliyun.com/',
 'https://www.cerebras.net/blog':'https://www.cerebras.ai/blog',
 'https://blog.langchain.dev':'https://www.langchain.com/blog',
 'https://mlcommons.org/inference':'https://mlcommons.org/working-groups/benchmarks/inference/',
 'https://reinvent.awsevents.com':'https://aws.amazon.com/events/reinvent/',
 'https://pytorch.org/tutorials/recipes/recipes/profiler_recipe.html':'https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html',
}
for old,new in CORRECTIONS.items():fix_url(old,new)
for channel in cb.values():
 u=sb[channel['row']['source_id']]['row']['canonical_url']
 if u.startswith('https://export.arxiv.org/rss/'):fix_url(u,u.replace('export.arxiv.org','rss.arxiv.org'))
PAPERS={
 '1453f30341f34b85f5b64730':('2204.05862','Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback','HH-RLHF'),
 '2a0ad7b8a037b0b603459fde':('2402.02057','Break the Sequential Dependency of LLM Inference Using Lookahead Decoding','Lookahead Decoding'),
 '7b701548c89db20000572154':('2009.11462','RealToxicityPrompts: Evaluating Neural Toxic Degeneration in Language Models','RealToxicityPrompts'),
 '8136d37a5eaa2d2f7c2292e7':('2307.16789','ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs','ToolLLM / ToolBench'),
 'b105f8342a2bad9954adad30':('2401.10225','ChatQA: Surpassing GPT-4 on Conversational QA and RAG','ChatQA / ChatRAG Bench'),
 'b85752d936effd8c3c4832f5':('2307.13854','WebArena: A Realistic Web Environment for Building Autonomous Agents','WebArena'),
 'bcb4c35f36031714140889b3':('2306.07174','Augmenting Language Models with Long-Term Memory','LongMem'),
 'da5e10dca2c862c0eca03f9e':('2303.04947','InfoBatch: Lossless Training Speed Up by Unbiased Dynamic Data Pruning','InfoBatch · 训练数据剪选'),
 'dc9b9095a92a0fc2009a5950':('2405.04437','vAttention: Dynamic Memory Management for Serving LLMs without PagedAttention','vAttention'),
 'e81ae8ed1b192f1297025d81':('2402.13753','LongRoPE: Extending LLM Context Window Beyond 2 Million Tokens','LongRoPE'),
 'f40abee4efe3169267e3e8a7':('2305.20050',"Let's Verify Step by Step",'PRM800K · 过程监督'),
 'fa9c9fa548d9b02dbeff0030':('2308.16369','SARATHI: Efficient LLM Inference by Piggybacking Decodes with Chunked Prefills','Sarathi'),
 '57aa5398feafcb92877eb766':('2501.11223','Reasoning Language Models: A Blueprint','Reasoning Language Models: A Blueprint'),
}
for suffix,(aid,paper,label) in PAPERS.items():
 ch=cb['channel-'+suffix];src=sb[ch['row']['source_id']];old=src['row']['canonical_url'];new='https://arxiv.org/abs/'+aid
 if old!=new:log.append(dict(channel_id=ch['row']['channel_id'],old_url=old,new_url=new,reason='paper title/arXiv identity mismatch corrected',paper_title=paper))
 update(src,dict(canonical_url=new,title=paper,external_id=aid,last_checked_at=DAY,verification_status='primary_identity_and_abstract_checked'))
 update(ch,dict(title_zh=label,title_en=label,updated_at=DAY))
 if suffix=='da5e10dca2c862c0eca03f9e':update(ch,dict(focus_zh='训练阶段的动态数据剪选参考。它减少训练样本处理成本，不是推理权重剪枝、KV压缩或在线服务加速的效果证据。',focus_en='Dynamic training-data pruning reference; not evidence of inference weight pruning, KV compression or serving acceleration.'))
for cid,label in [('channel-f607e353de33ad320ec5e107','llama.cpp · 版本标签'),('channel-d27a60e2db84a73be402cc93','OpenAI Agents SDK · Python'),('channel-ced7758c4424826fd082146e','τ-Bench · 当前评测框架')]:
 if cid in cb:update(cb[cid],dict(title_zh=label,title_en=label,updated_at=DAY))
def channel_patch(cid,patch,url=None):
 ch=cb[cid]
 if url:fix_url(sb[ch['row']['source_id']]['row']['canonical_url'],url)
 update(ch,{**patch,'updated_at':DAY})
channel_patch('channel-876ad5cefce2633aa5486a8a',dict(focus_zh='ICML 2026官方可读下载索引；包括主会、研讨会等多类活动。按session类型筛出论文，不能把活动总数当作主会论文数。',focus_en='Official ICML 2026 download index, including main-conference and workshop events. Filter session types; event totals are not paper totals.'),'https://icml.cc/Downloads/2026')
channel_patch('channel-db2b2a5ac405cefde01e0d4b',dict(title_zh='MLSys · 2026论文集',title_en='MLSys · 2026 proceedings'),'https://proceedings.mlsys.org/paper_files/paper/2026')
channel_patch('channel-1221993f54a2c7199b18a2e1',dict(title_zh='OSDI · 2026技术议程与论文',title_en='OSDI · 2026 technical sessions'),'https://www.usenix.org/conference/osdi26/technical-sessions')
channel_patch('channel-9f1da1b4c8904073f8970358',dict(title_zh='EuroSys · 2026会议导航',title_en='EuroSys · 2026 conference',focus_zh='EuroSys 2026官方会议导航；用于定位议程、论文和系统实现材料，不把会议首页等同于论文已全量采集。',focus_en='Official EuroSys 2026 conference navigation; a homepage is not a complete paper collection.'),'https://2026.eurosys.org/')
channel_patch('channel-ddf4c0a194109a11422236e3',dict(title_zh='NeurIPS · 已出版论文集',title_en='NeurIPS · published proceedings',focus_zh='历史已出版论文集当前可见到2025；2026会议和OpenReview另行核对。不能将历史档案标为已覆盖2026完整论文。',focus_en='Published archive observed through 2025; check 2026 conference/OpenReview separately. Not a complete 2026 collection.'))
channel_patch('channel-959c84b158c3e1f548ead417',dict(focus_zh='历史ATC资料线索。当前链接返回USENIX会议总导航，尚未确认能持续定位ATC论文集，保留为待修复入口，不记作完成论文采集。',focus_en='Historical ATC lead. Current endpoint returns generic USENIX conference navigation; ATC-specific discovery remains unresolved.'))
channel_patch('channel-06616ad755a98aabbce8aabc',dict(focus_zh='CoRL 2026录用名单已于10月19日公告；名单采用动态嵌入，本轮未取回完整正文。录用名单与可读论文分开登记。',focus_en='CoRL 2026 accepted-paper list announced Oct 19; embedded contents were not fully retrieved. Acceptance and readable full text remain distinct.'))
for suffix,zh,en in [
 ('bcb4c35f36031714140889b3','长时记忆增强语言模型参考；不能将存取外部记忆本身等同于KV量化。','Long-term memory augmentation, not KV quantization.'),
 ('dc9b9095a92a0fc2009a5950','KV物理内存管理参考；通过虚拟内存管理改善分配，不是量化KV数值或减少模型逻辑KV状态。','KV physical-memory management, not numerical KV quantization or logical-state compression.'),
 ('e81ae8ed1b192f1297025d81','RoPE位置编码与长上下文窗口扩展参考；扩展长度不代表降低KV驻留容量。','RoPE/context-window extension; longer windows do not imply smaller KV storage.'),
 ('fa9c9fa548d9b02dbeff0030','Chunked Prefill与Decode组合调度参考；调度吞吐改善不能归因于权重量化。','Chunked-prefill/decode scheduling; scheduling gains are not weight-quantization gains.'),
 ('b105f8342a2bad9954adad30','ChatQA与ChatRAG Bench的对话问答/RAG评测参考；RULER和Needle需要各自独立来源，不能共用这篇论文。','Conversational QA/RAG evaluation; RULER and Needle require separate sources.'),
]:channel_patch('channel-'+suffix,dict(focus_zh=zh,focus_en=en))
NOTES={
 'source-family-vllm-ascend':('v0.30.0rc2 · 2026-10-13 · 候选版。发布说明明确无代码变化，仅修复Docker镜像构建与CANN依赖；不能当作新增量化能力。滚动文档与GitHub发布日期需分别核对。','v0.30.0rc2, Oct 13: release candidate with Docker/CANN dependency fixes and no code changes; not a new quantization capability.','https://github.com/vllm-project/vllm-ascend/releases'),
 'source-family-vllm':('v0.32.0 · 2026-10-18 · 正式发布。跟踪低精度后端、KV格式、模型适配与修复；量化算法支持和具体设备可执行性分开核对。','v0.32.0, Oct 18: stable release. Track quantized backends, KV formats, model support and fixes; algorithm availability is distinct from device execution.','https://github.com/vllm-project/vllm/releases'),
 'source-family-sglang-blog':('v0.5.22 · 2026-10-19 · 正式发布。关注HiSparse与EAGLE/MTP组合、上下文并行及推测解码正确性修复。博客本轮读取失败，发布页可用；性能需按对应负载核查。','v0.5.22, Oct 19: stable release; inspect HiSparse/MTP composition, context parallelism and speculative-decoding correctness. Blog fetch failed; release notes are available.','https://github.com/sgl-project/sglang/releases'),
 'source-family-tensorrtllm':('v1.4.0rc1 · 2026-10-22 · 候选版。包含NVFP4检查点适配与默认KV cache manager V2；注意破坏性变更和已知问题，不将候选版称为生产稳定版。','v1.4.0rc1, Oct 22: candidate with NVFP4 checkpoint support and KV cache manager V2 default; breaking changes and known issues still apply.','https://github.com/NVIDIA/TensorRT-LLM/releases'),
 'source-family-msmodelslim':('官方GitHub README消息到2026-09-03，含Step-3.7-Flash W8A8 MXFP8；滚动算法/模型文档与正式发版记录分开查看，未据此认定10月发布新正式版。','Official GitHub README news observed through Sep 3 includes Step-3.7-Flash W8A8 MXFP8. Rolling documentation is distinct from a stable release.','https://github.com/Ascend/msmodelslim'),
 'source-family-ascend-mindie':('官方运行时文档覆盖量化模型接入、服务配置与模型/设备约束。职责是部署和执行，与msModelSlim的量化权重生成区分；本轮未确认最新正式版本号。','Official runtime documentation covers quantized-model integration, serving configuration and model/device constraints; distinct from ModelSlim conversion. Latest stable version not verified.','https://mindie-llm-doc.readthedocs.io/zh-cn/latest/'),
 'source-family-ops-transformer':('主干可观察到GroupedMatmulActivation的A4W4/MXFP4实现及量化Attention测试变更；尚未确认对应发布标签。v9.1.1保留为历史固定入口。','Main-branch A4W4/MXFP4 GroupedMatmulActivation and quantized-attention test changes observed; shipping tag not confirmed. v9.1.1 remains a historical reference.','https://gitcode.com/cann/ops-transformer'),
 'source-family-cann-releases':('发布管理主干可读，用于查发布说明、驱动/算子包配套和废弃接口。发布计划或其他项目的CANN依赖，不等同于CANN正式发布证明。','Release-management tree provides release notes, compatibility and deprecations; a roadmap or another project dependency is not proof of a CANN stable release.','https://gitcode.com/cann/release-management/tree/master'),
 'source-family-channel-a64bce2b77a8a1faeca61346':('已改为Argilla官方仓库。README说明现由社区接手维护；修复还需核对develop分支，不再写为原作者团队持续维护。','Corrected to the official Argilla repository; README describes community-led maintenance and develop-branch fixes.','https://github.com/argilla-io/distilabel'),
 'source-family-channel-ced7758c4424826fd082146e':('旧tau-bench任务已标过时，当前入口改为tau2-bench。框架2.0与1.x结果不可直接比较；使用具体任务集、版本与计分口径。','Original tau-bench tasks are outdated; current framework is tau2-bench. Version 2.0 and 1.x scores are not directly comparable.','https://github.com/sierra-research/tau2-bench'),
 'source-family-channel-29c2808ed90e37ce0c1304fe':('官方README记录10月10日TensorRT-LLM KVCMv2连接器及10月6日TokenSpeed接入；本轮未逐项审核PR，不据此扩展为所有模型/设备均支持。','README records Oct 10 TensorRT-LLM KVCMv2 connector and Oct 6 TokenSpeed integration; individual PRs and universal support not verified.','https://github.com/kvcache-ai/Mooncake'),
 'source-family-arxiv':('5个recent分类本轮均可读；RSS地址按官方说明改为rss.arxiv.org。另核对17条既有arXiv参考，修正12条论文身份错链；这是入口/身份核对，不是所有论文全文审阅。','Five recent-category indexes readable; RSS URLs follow official rss.arxiv.org guidance. Twelve identity mismatches corrected among 17 paper references; not full-text review.','https://info.arxiv.org/help/rss.html'),
 'source-family-icml':('2026下载索引可读；虚拟论文页依赖动态加载。下载索引含多类活动，应区分主会与workshop，不能直接用event数量表示论文数。','2026 download index readable; virtual paper page is dynamic. Separate main-conference and workshop events.','https://icml.cc/Downloads/2026'),
 'source-family-iclr':('保留2026已发表论文；2027 OpenReview用于投稿/在审线索。截至10月23日，评审尚未按官方日程公开，不能写成已录用论文。','Retain published 2026 papers; 2027 OpenReview is a submission/review lead, not accepted-paper evidence as of Oct 23.','https://openreview.net/group?id=ICLR.cc/2027/Conference'),
 'source-family-channel-ddf4c0a194109a11422236e3':('已出版论文档案当前到2025；2026会议页面与OpenReview单独跟踪，动态页面壳不能算已取回完整论文集。','Published archive currently through 2025. Follow the 2026 conference/OpenReview separately; a dynamic shell is not complete ingestion.','https://neurips.cc/Conferences/2026'),
 'source-family-mlsys':('年度论文入口由2025更新为2026，来自官方会议主页所链论文集。','Annual proceedings endpoint advanced from 2025 to the officially linked 2026 collection.','https://proceedings.mlsys.org/paper_files/paper/2026'),
 'source-family-channel-8f61192ea8b511d6725a474f':('官方Anthology当前可见最高2025；保留长期入口，不声称已经覆盖2026完整论文集。','Official Anthology observed through 2025; do not claim a complete 2026 collection.','https://aclanthology.org/venues/emnlp/'),
 'source-family-channel-44a42cb3987df5094c5adc33':('官方Anthology已显示2026资料；长文、短文和行业轨道需分开筛选，避免把所有条目混为主会长文。','Official Anthology includes 2026 material; distinguish long/short papers and industry tracks.','https://aclanthology.org/venues/acl/'),
 'source-family-hf-daily-papers':('页面可见10月23日推荐；用于社区发现和遗漏补充，热度排序不是同行评审，也不替代原论文实验。','Oct 23 recommendations observed; community discovery, not peer review or primary experimental evidence.','https://huggingface.co/papers'),
 'source-family-the-batch':('复查已取回公开入口样本，但尚未核对最新一期全文；入口可读不等于当期文章已经完整采集。','Public endpoint sample retrieved on recheck; latest issue full text remains unreviewed. Reachability is not complete issue ingestion.','https://www.deeplearning.ai/the-batch/'),
 'source-family-jiqizhixin':('当前主页突出PRO会员通讯和专题入口，部分内容需登录或订阅；公开摘要可作线索，付费正文未取回时不声称已审阅。','Homepage foregrounds PRO newsletters and topic portals; some content requires login/subscription. Public summaries are leads, not reviewed paid full text.','https://www.jiqizhixin.com/'),
}
optional('ic_source_families',['reviewed_at','review_note_zh','review_note_en','review_url'])
for fid,(zh,en,url) in NOTES.items():
 if fid in fb:update(fb[fid],dict(reviewed_at=DAY,review_note_zh=zh,review_note_en=en,review_url=url,updated_at=DAY))
PROFILE={
 'source-family-channel-ced7758c4424826fd082146e':('τ-Bench · 当前评测框架','工具交互Agent评测框架。用于比较任务完成、规则遵循与交互鲁棒性；当前框架与历史任务版本需分别记录，属于邻近评测参考。','Agent tool-interaction evaluation; track task success, policy compliance and version-specific scoring.'),
 'source-family-channel-d27a60e2db84a73be402cc93':('OpenAI Agents SDK · Python','官方Python Agent开发框架。用于跟踪工具调用、交接、会话与追踪接口；作为Agent应用层参考，不作为推理压缩的性能证据。','Official Python Agents SDK; tools, handoffs, sessions and tracing. Adjacent application framework, not compression-performance evidence.'),
 'source-family-channel-a64bce2b77a8a1faeca61346':('distilabel · 社区维护','合成数据与模型评测流水线工具。用于研究数据构造和评测过程；当前按社区维护状态跟踪，不能把训练数据收益直接归为推理压缩。','Synthetic-data and evaluation pipelines under community-led maintenance; training-data benefits are distinct from inference compression.'),
 'source-family-channel-3c244d564c40286c35d4337e':('CacheBlend · LMCache技术文档','LMCache记录的非前缀KV复用机制。用于研究跨文档缓存复用与必要重计算；不把它描述为独立成熟服务平台或KV数值量化。','LMCache non-prefix KV reuse and selective recomputation; not a standalone serving platform or numerical KV quantization.'),
 'source-family-channel-6c6f1e0ec7a38df2e2e35561':('InfiniGen · 论文实现','OSDI 2024研究实现，研究动态KV选择、预取与卸载。用于核对论文机制与复现条件，和持续发布的生产推理框架区分。','OSDI 2024 research implementation for dynamic KV selection, prefetch and offload; not a continuously released production framework.'),
 'source-family-channel-6dc8bc88196635062dd41867':('DistServe · PD分离研究实现','Prefill与Decode分离的LLM服务系统。用于研究阶段隔离、资源分配与吞吐/时延取舍；不将调度收益记作量化收益。','Prefill/decode-disaggregated LLM serving research; resource allocation and throughput/latency trade-offs are distinct from quantization.'),
 'source-family-channel-796c482e11e634605c45cd89':('llm-d · 分布式推理','面向Kubernetes的分布式推理服务栈。关注路由、缓存、PD分离、弹性与流控，作为压缩技术接入服务系统的工程参考。','Kubernetes distributed inference stack: routing, caching, PD disaggregation, elasticity and flow control.'),
 'source-family-channel-b0658a590609b49f0bcb3ea9':('BFCL · 工具调用评测','Berkeley Function Calling Leaderboard官方榜与代码入口。比较工具调用能力需固定任务版本和评测协议，不用榜单名次替代量化后业务质量验收。','Official Berkeley Function Calling Leaderboard; compare fixed task versions and protocols, not ranks as compression acceptance.'),
}
for fid,(title,zh,en) in PROFILE.items():
 if fid in fb:update(fb[fid],dict(title_zh=title,title_en=title,summary_zh=zh,summary_en=en,updated_at=DAY))
FOCUS={
 'source-family-vllm':('量化后端、支持设备、KV格式与服务执行条件。','Quantized backends, supported devices, KV formats and serving conditions.'),
 'source-family-vllm-ascend':('昇腾插件的量化加载、算子/模型支持、设备限制与CANN版本配套。','Ascend-plugin quantized loading, operator/model support, hardware constraints and CANN compatibility.'),
 'source-family-msmodelslim':('量化算法、模型支持矩阵、精度恢复与导出格式；生成结果还需核对运行时可执行性。','Quantization algorithms, model support, quality recovery and export formats; runtime execution remains a separate check.'),
 'source-family-sglang-blog':('量化执行、缓存管理与推测解码的版本支持和正确性；性能比较固定负载。','Quantized execution, caching and speculative-decoding support/correctness; compare performance under fixed workloads.'),
 'source-family-tensorrtllm':('低精度检查点、KV管理与硬件矩阵；候选版本和稳定版本分别记录。','Low-precision checkpoints, KV management and hardware matrices; record candidate and stable releases separately.'),
}
roles={'homepage':('项目导航与公开技术文章。','Project navigation and public technical posts.'),'repository':('核对代码、默认分支及实现边界。','Inspect code, default branch and implementation boundaries.'),'documentation':('核对配置方法、支持矩阵与版本约束。','Inspect configuration, support matrices and version constraints.'),'releases':('核对正式版/候选版、发布日期、修复与已知问题。','Inspect release type/date, fixes and known issues.'),'blog':('从技术文章发现实现线索，再核对对应版本。','Discover implementation leads and verify their version bindings.')}
for member in members:
 r=member['row']
 if r['family_id'] not in FOCUS:continue
 zh,en=FOCUS[r['family_id']];rz,re=roles.get(r['entry_kind'],('按该入口的原始资料核对。','Inspect original material at this entrypoint.'))
 update(cb[r['channel_id']],dict(focus_zh=rz+zh,focus_en=re+' '+en,updated_at=DAY))
for item in log:
 ch=cb.get(item['channel_id'])
 if ch:
  src=sb[ch['row']['source_id']];update(src,dict(provider=urlsplit(src['row']['canonical_url']).netloc))
for t,data in [('ic_channels',channels),('cloud_core_sources',sources),('ic_source_families',families)]:write(t,data)
out=ROOT/'research/source-audits/2026-10-23';out.mkdir(parents=True,exist_ok=True)
log=list({(r['channel_id'],r['old_url'],r['new_url']):r for r in log if r['old_url']!=r['new_url']}.values())
(out/'registry-corrections.json').write_text(json.dumps(log,ensure_ascii=False,indent=2),encoding='utf-8')
print('Corrected links:',len(log),'Dated family notes:',len(NOTES))
