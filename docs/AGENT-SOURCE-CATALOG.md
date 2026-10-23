# Agent 信息源目录的组织方式

采用长期信源目录与具体条目分开维护的方式。三列表头是本报告的阅读设计，不宣称统一行业标准。

| 阅读列 | 来源字段 | 用途 |
| --- | --- | --- |
| 信息源与入口 | title、url、entry_type、ecosystem、priority；source-endpoints | 名称直达主入口；相关渠道就近展开；同一项目只占一行 |
| 定位与研究价值 | description、rationale | 分别说明它是谁、为何值得本团队跟踪 |
| 关注内容与跟踪方式 | focus、cadence、evidence_role | 指明看什么、建议多久人工核对、如何使用这类证据 |

按热点资讯、学术界、业界排序，大类下面按二级分类分别输出表格。来源归属保存在source-channels.csv，分组定义、显示次序和旧锚点保存在source-groups.csv。生态标签单独筛选。默认全部26源，核心优先排序但不隐藏补充观察，保留NeurIPS、ICML、ICLR。

| 一级大类 | 二级分表 | 来源数 |
| --- | --- | --- |
| 热点资讯 | 产品与市场资讯；架构与工程资讯 | 2 |
| 学术界 | 预印本平台；系统与性能会议；机器学习会议；多智能体会议 | 9 |
| 业界 | 工作流运行时；分布式执行引擎；模型推理服务；集群资源调度；跨层工程实践 | 15 |

每张表有分组标题、用途说明和来源数量，统一三列表头。二级导航和下拉筛选使用同一分组数据。新锚点带sources前缀，旧source-layer-0至4仍可定位对应业界表格；新学术及新闻锚点会选择正确的大类。

来源事实保存在source-channels.csv；入口类型与证据用途保存在source-profile.csv；同源多入口保存在source-endpoints.csv。论文与事件通过publication-source-links.csv关联到持续来源，不把一篇论文当成一个信源。

维护状态展开显示入口最近核对、已收录条目与适用边界。建议节奏不是已运行的采集计划；本报告仍为人工维护。官方资料、会议原文、预印本与媒体线索是使用方式标签，不是可信度评分。

## 参考实践

- Feedly建议将原始信源与筛选后的AI Feed分开，按主题组织并定期审查失效或噪声来源：https://docs.feedly.com/article/768-follow-sources-in-feedly
- Zotero以持续订阅发现论文，再将需要保留的条目收入文献库：https://www.zotero.org/support/feeds
- Inoreader区分信源文件夹与文章标签：https://www.inoreader.com/features/folders-and-tags

只借鉴目录与条目分工，没有接入或宣称已运行这些服务的订阅、自动筛选或同步功能。
