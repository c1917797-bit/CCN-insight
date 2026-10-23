# 信息源到调度决策：2026-10-23 定点核验

本次新增候选来自 3 个已有官方信息源：Temporal、Ray、openYuanrong。核对现有 19 条 research-publications 后去重。结果是 3 条机制依据、2 条本月版本依据；**没有把这 5 条计为 10 月 17—23 日新增事件**。现有 4 条本周精选不在本批改动范围内。

维护入口：candidate-evidence-20261023.csv 保存事实、日期和限制；candidate-decision-links-20261023.csv 保存研究判断、具体测试和停止条件。后者是面向本项目的推断，不是厂商承诺。没有执行这些产品的性能实验，没有测量昇腾收益。

## 1. Temporal：派发公平的计量对象

- [官方机制文档](https://docs.temporal.io/develop/task-queue-priority-fairness)：核对 Task Queue Priority、Choosing between Priority/Fairness/both、Limitations of Fairness。
- 定位短引文：`These rules apply within a Task Queue partition.`
- 关键区别：优先级在先，同层才按租户权重派发；其控制对象是待派发任务，不能把相同派发份额等同为相同运行服务成本。
- 分区倾斜、跨 Worker 版本与已派发执行均有明确边界。启用机制不能代替业务侧最长等待护栏。
- 文档没有独立发布日期。[GA 公告](https://temporal.io/changelog/priority-fairness-generally-available) 为 2026-05-05，仅作能力发布时间佐证。

## 2. Ray：软亲和的回退条件

- [官方 Scheduling 文档](https://docs.ray.io/en/latest/ray-core/scheduling/index.html)：核对 Resources、NodeAffinitySchedulingStrategy、Locality-Aware Scheduling。
- 定位短引文：`Locality-aware scheduling is only for tasks not actors.`
- 专家易误读处：目标节点“暂忙但可行”与“不存在或不可行”是两种状态。soft 标记只在后者允许其他节点，前者仍可能等待。
- 单独核对 [逻辑资源说明](https://docs.ray.io/en/latest/ray-core/scheduling/resources.html) 后才可以讨论真实隔离；文档版本标签为 Ray 2.59.0，路径 latest 仍是滚动入口。

## 3. 元戎：会话亲和与状态恢复

- [官方 AI Agent 会话与亲和性教程](https://docs.openyuanrong.org/zh-cn/latest/multi_language_function_programming_interface/advanced_tutorials/ai_agent_session.html)：核对会话调度机制、弱亲和性与持久化、SDK 使用说明。
- 定位短引文：`TTL`；`waitForNotify`；`notify`。
- 首次绑定、有效绑定复用与失效后重载是可分离的步骤。持久化会话历史并不意味着可迁移全部进程状态，也不证明工具副作用可以重复执行。
- 本页底部最后更新日期为 **2026-07-09**，页头横幅 **v0.9.0**。不能用同站首页的更高版本横幅覆盖这个子页的适用范围。

## 4. Temporal Go SDK 1.50.0：先定位拉取瓶颈

- [固定版本发布说明](https://github.com/temporalio/sdk-go/releases/tag/v1.50.0)：核对 Highlights / Added 的 poller groups autoscaling，以及 Changed 的 task queue priority 状态变更。
- 定位短引文：`sticky-backlog prioritization`。
- 发布页区分配置了 poller groups 的新行为与未配置时的既有行为；SimpleMaximum 保持不变。不能把 poller 数量误当为 Worker 执行容量。
- [GitHub 官方 API](https://api.github.com/repos/temporalio/sdk-go/releases/tags/v1.50.0) 本次只读核对：published_at=`2026-10-15T21:03:14Z`。属于本月版本，不属于本周新增。

## 5. Ray 2.59.0：把过载拒绝传到调用方

- [固定版本发布说明](https://github.com/ray-project/ray/releases/tag/ray-2.59.0)：核对 Ray Serve / New Features / Configurable backpressure responses。
- 定位短引文：`Defaults are unchanged`。
- [关联 PR #65193](https://github.com/ray-project/ray/pull/65193) 仅作原始实现入口；本次没有做代码差异审计。发布说明支持可配置 429 和 Retry-After，不能证明客户端已遵循退避。
- [GitHub 官方 API](https://api.github.com/repos/ray-project/ray/releases/tags/ray-2.59.0) 本次只读核对：published_at=`2026-10-02T07:04:37Z`。

## 有查到但未纳入的内容

- Ray [2.58.1](https://github.com/ray-project/ray/releases/tag/ray-2.58.1) 和 [2.57.1](https://github.com/ray-project/ray/releases/tag/ray-2.57.1) 的版本列表显示 10 月 21 日发布，但摘要主要涉及 Data callback 和基础镜像。没有充分调度决策增量，因此不为凑本周数量加入。
- Temporal 官方 10 月 5 日 Cloud Run Worker Public Preview 已找到；与本轮 poller 和队列机制有重复，暂不扩大本批条目数。
- 元戎论坛/转载关于吞吐提升、十万会话等数字未采用：本轮未取得可复核实验配置，不能据此写入竞争力判断。

## 后续维护门槛

每条新增资料必须区分发布日期、文档更新日和核对日；至少落到一项调度决策，给出机制边界与能推翻判断的反例。无数字的官方机制说明可以用于架构基线，不能包装为性能证据。相关性不足的最新版本允许不收录。
