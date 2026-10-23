# 推理压缩专题 · 指定证据复核

2026-10-23，本轮修订四张现有卡片及其对应引用；随后从已研读库存中吸收 DeltaLog 为一张关联执行边界卡。内容源仍是 `data/compression/tables/`，没有回写原站，没有新增性能实测。

| 卡片 | 原有阅读问题 | 修订依据与处理 |
| --- | --- | --- |
| KIVI | 摘要倍数缺少负载与 batch 条件 | [v2原文](https://arxiv.org/html/2402.02750v2)，§3.3、§4.1、表3–4、§4.2.4/图5；拆开质量、容量与不同 batch 的吞吐结果。 |
| QJL | 容易把标题位宽理解为整个缓存位宽 | [v2原文](https://arxiv.org/html/2406.03482v2)，定义3.1、算法1、§3.2、§4/表1–2/图3；补充表示对象、范数与单注意力层计时范围。 |
| msModelSlim KV | 工程参考只有泛泛建议 | [官方词条](https://msmodelslim.readthedocs.io/zh-cn/latest/zh/knowledge_base/quantization_algorithms/kvcache_quant/term_kvcache_quant/)，§2.4/2.6；列出 INT8/per-channel、缓存 API 条件和伪量化内存限制。latest 页面未固定软件发布版本。 |
| ASVD KV | 摘要“无性能下降”不够精确 | [v5原文](https://arxiv.org/html/2312.05821v5)，§3.3–3.5、§4.3/表3；保留缓存比例，呈现实际困惑度差异。 |
| DeltaLog | 有摘要库存，但缺少长期知识归属 | [v1原文](https://arxiv.org/html/2608.15533v1)，§3–4、§5.1/5.3/5.5/5.6及§6；纳入紧凑架构的执行边界，明确写回优化不是低比特量化或新架构。 |

所有案例采用“技术方法—实测效果—测试条件—判断边界”。引用更新为指定章节审阅，日期是核对日期；没有标记全文阅读、理论证明复核或独立复现。

另外检查了 MiniLLM 的指定方法、主结果与消融段落，以及 msModelSlim 当前文档的模式和命令入口，未扩大卡片修改范围。msModelSlim 文档内源代码链接读取失败，不能据此称已审查实现代码。完整获取记录、明确排除项及来源版本见 [JSON记录](compression-topic-evidence-review-20261023.json)。

这次没有重扫全部信息来源，也没有证明所有专题都完成新近事实审查。质量、TTFT、TPOT、单层计时、缓存数据区和总峰值内存仍按各自口径解释。

DeltaLog 保留其 2026-08-16 发表身份，不列为10月新论文。新增卡片 `kv_cache-compact_architecture__boundary_deltalog` 只说明“紧凑状态并不自动消除执行访存”；没有创造新的根技术分类，也没有把写流量下降改写为缓存容量下降。数值容差与任务质量分开，未报告的指标保持未报告。
