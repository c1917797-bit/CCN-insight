# 信息源更新核对 · 2026-10-23

本轮仅更新CCN统一维护源与本地预览，未推送、未发布，也未修改原Irigit站点。

## 已完成

- 全部332个登记入口重新进行公开HTTPS样本读取：293个可读，39个未完成。访问限制、网络失败与404分别标明；未将失败当作停更或无新增内容。
- 修正52个渠道的链接或入口身份。仓库更名、组织迁移、错误文档路径和年度论文入口均有更正清单。
- 全审17条既有arXiv静态参考身份：12条错链已替换，1条标题收窄错误已修订，4条身份正确。只核对原始身份/摘要，不冒称全文复核。
- 5个arXiv RSS按官方帮助规范为rss.arxiv.org；修复MLSys2026、ICML下载索引、OSDI2026议程等入口。
- 21个来源增加可见的本轮核对说明、日期和原始依据。保留长期定位，版本事实另列，不把候选版本称正式版，也不把主干变更当已交付能力。
- 每个登记入口保留独立核查状态，未覆盖来源的内容级更新不冒称完成。

## 关键改正

- vLLM-Ascend v0.30.0rc2：候选版，说明无代码变更，仅镜像/CANN依赖修复；不是新增量化能力。
- vLLM v0.32.0、SGLang v0.5.22：分别记录正式发版；TensorRT-LLM v1.4.0rc1明确是候选版。
- msModelSlim：GitHub消息、滚动文档与正式版本记录分开，未虚构10月正式发版。
- NeurIPS历史已出版论文集与2026会议分开；ICLR2027投稿/在审材料与2026已发表论文分开。
- ChatQA、RULER和Needle不能共用一篇论文；现有错链条目收窄为ChatQA/ChatRAG Bench。
- InfoBatch是训练数据剪选；LongRoPE是上下文扩展；vAttention是KV物理内存管理；Sarathi是组合调度。均不作为权重量化效果证明。
- BFCL官方榜单、llama.cpp版本标签、Agents SDK Python与当前tau2-bench入口分别归正；旧框架评分不能直接跨版本比较。

## 边界

入口可读只说明取回网页样本，未确认全部分页或全文。许多备用源仍处于定位待完善阶段；其入口核查不等于正式入选或完成内容审阅。此次没有宣称已全量采集各源最新事件。

## 可追溯文件

- `research/source-audits/2026-10-23/registry-corrections.json`：52条更正。
- `research/source-audits/2026-10-23/source-health-after-refresh.json`：逐入口读取结果。
- `data/compression/tables/ic_channel_checks/rows.jsonl`：新增332条有界检查记录，研究采集数量为0、性能验证为false。
- `scripts/verify_source_refresh.py`：核对链接绑定、全部入口状态及原始依据。

## 验收

构建、统一内容关联、入口更正绑定、静态读取适配和浏览器显示均检查；公开站点未发布。
