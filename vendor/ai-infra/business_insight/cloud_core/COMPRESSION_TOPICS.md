# 推理压缩专题与动态关联

专题 URL 为 `/business_insight/cloud_core/topic.html?topic=parameters-precision`；共用同一渲染器，每个专题内容来自 TableGit，无内置业务数据兜底。

| 原生表 | 用途 | 主键 / 关联 |
| --- | --- | --- |
| ic_compression_topics | 12 个矩阵专题与 4 个扩展专题；定义标题、研究问题和稳定 URL | compression_topic_id；target_term_id、method_term_id → ic_map_terms |
| ic_compression_topic_sections | 独立维护研究问题、机制、比较、边界、启示和持续关注 | section_id；compression_topic_id → 专题 |
| ic_compression_topic_events | 按月份和采集范围关联事件，保存归类依据与审阅状态 | link_id；scope_topic_key；evidence_id → ic_evidence_items；source_id → cloud_core_sources |

页面按同一 TableGit revision 读取所有表。地图的“本期关联事件”、专题动态与本期动态页面按同一 scope_id + compression_topic_id 关联集合计数；同一事件在一个专题只出现一次。跨专题计数不可相加。首投和修订是独立事件。

已登记原文审阅以 `primary_review` 标记；仅标题线索以 `title_candidate` 标记，不能作为已确认机制或效果结论。五字段总结继续引用 ic_paper_summaries 及关键词、事件关联表，并检查论文 observed_version。新版本不得使用旧版本的效果总结。

新增来源和事件时，先写 cloud_core_sources、ic_evidence_items、monthly_scopes 与原有采集关联，再通过 table.author 在同一事务补充 ic_compression_topic_events。保留 scope_id、period_id、原文依据 URL、归类说明和审阅状态。不能仅沿旧 7×6 标签机械映射：整 token KV 淘汰不归入 KV 通道剪枝；低秩误差补偿不自动证明权重部署已低秩化；使用激活校准不自动构成激活压缩；dataset distillation 不自动构成模型压缩。

核对原文后更新关联状态及归类说明，独立更新论文总结。新增研究分析写入相应 section 行，事实与分析分列。公开论文只保存原始 URL 与必要元数据/摘要性总结，不复制全文，不导入认证信息。

本次整理：16 专题、96 内容段落、622 范围限定关联，涉及 568 个去重事件；其中 77 条关联基于已有原文审阅，其余 545 条为待审阅线索。它们是现有资料中的严格子集，不是 2026 年全部领域文献。其余元数据继续保留在全局本期动态和原始资料库，待进一步审阅。

激活×蒸馏、激活×低秩、KV Cache×蒸馏目前缺少直接代表证据，保留研究问题、适用条件与检索入口，不填造性能数字。
