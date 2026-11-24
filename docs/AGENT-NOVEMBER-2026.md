# 2026年11月 Agent 调度技术洞察

本轮窗口为 **2026-11-01—2026-11-24**，不是完整自然月或全网穷尽检索。沿用信息来源 → 技术地图 → 本期动态 → 分析结论 → 洞察归档。唯一维护源仍为 `research/agent-scheduling/`；不改推理压缩、首页导航或原站 TableGit。

新增9项：4篇预印本、4项官方工程资料、1项官方发布事件。均保存首发日期、版本、核对章节、机制、原文结果、边界、研究判断与最小对照。累计34项；既有25项的所有字段及核对日期保持。28个持续来源中，本轮仅追加 arXiv、llm-d、vLLM Ascend、Buoyant 4个核查记录，不能声称28个来源都于11月24日逐项复核。

| 日期 | 一手来源 | 研究用途与关键边界 |
|---|---|---|
| 11-01 | [Fairway v1](https://arxiv.org/html/2611.02082v1) | 实例prefill队列：未缓存工作量与相对等待。8.6倍为指定对照的P99 TTFT，单A6000、Llama-3.1-8B、生成1 token，非整任务收益。 |
| 11-04 | [Kinference官方发布](https://www.buoyant.io/newsroom/buoyant-announces-kinference-an-open-source-inference-serving-platform-for-kubernetes) | 推理控制面产品信号；不采用未核验原始基准的宣传倍数。 |
| 11-09 | [llm-d回放机制对照](https://llm-d.ai/blog/from-agent-traces-to-replay) | 依赖图、请求形状和模拟分别记录；工具响应回放不等于执行工具。 |
| 11-10 | [缓存亚稳态 v1](https://arxiv.org/html/2611.13412v1) | 突发后的存量会话/KV预算；指定恢复对照7/7与1/7，非生产保证。 |
| 11-10 | [vLLM Ascend 0.32.0rc1](https://github.com/vllm-project/vllm-ascend/releases/tag/v0.32.0rc1) | Prefill亲和和混合缓存的工程前提。发布tag依赖与反馈帖不同，以发布说明为准；尚未安装复现。 |
| 11-12 | [CAAS v1](https://arxiv.org/html/2611.16661v1) | 工具动作链推进；Table 3中140.5→128.5分钟为指定Opt-FCFS/Opt-CAAS比较，不能将组合收益归给CAAS。 |
| 11-16 | [llm-d Async多租户方案](https://llm-d.ai/blog/multi-tenant-multi-priority-model-serving-llm-d) | 配额、六级严格优先和背压；不等于基于成本的任务公平。 |
| 11-17 | [Duru v1](https://arxiv.org/html/2611.23558v1) | 任务级归一化慢化和跨层反馈。44.4%是15种实测配置的几何均值，不是原始任务时延；扩展研究含模拟。 |
| 11-23 | [llm-d/SGLang分层缓存](https://llm-d.ai/blog/serving-glm-5-2-sglang-tiered-kv-cache-on-llm-d) | L2稳态收益与L3恢复价值分开；16/32卡对照不叠加，L3可能增加稳态时延。 |

分析结论按三项根技术组织，建议以已观测瓶颈选择穿刺论文。优先假设是活跃KV预算能改善突发后的恢复；其次在工具受限批负载研究CAAS，再对稳定系统研究Duru/Fairway公平。所有顺序均为编辑判断，尚无云核实测结论。

10月的报告上下文、25项资料、41条关联、三项建议、观察单和周选表保存于 `history/2026-10/`。网页归档可展开当时三项判断；原有资料仍在动态的历史分组中阅读，不重标为11月首发。近七日窗口严格为11月18—24日，本轮仅选11月23日一项，不为补数量挪入17日论文。

维护数据可运行 `scripts/refresh_agent_november_2026.py`，它按稳定ID更新9条增量，并且只在历史快照不存在时保存10月原表。新月份应维护新选表和综合判断，不将当前CSV机械改期。中文地图和共用页头的新日期已补英文，仍无翻译接口或外部运行时请求。

验证：根构建与根校验通过；Agent校验覆盖23页、全部内部链接、三张信息源总表、9项当月/25项既有记录、来源审阅记录、原图哈希和中英文地图。浏览器实点动态分类、路线专题、方向筛选、11月综合判断、10月归档、来源核验展开和中英文切换；390px动态/综合判断无全页横向溢出。发布版本与线上复测另记部署回执。
