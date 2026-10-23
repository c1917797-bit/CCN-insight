---
name: ccn-evidence-review
description: Review primary evidence and comparable technical claims for CCN insight pages. Use when adding papers, industry releases, numerical results, or changing a technical judgment; not for purely visual edits.
---

# CCN 证据与技术判断

研究问题先明确，业务条件用于后续检索；不因暂不适配就删除技术。新材料先去重、核实身份与版本，再分入长期基础、月度增量或候选线索。

## 从来源到结论

1. 优先论文原文、作者实现和官方版本说明。新闻用于发现线索。可用 `web-article-capture` 采集正文与原图；不可用时采用已有一手读取方式并记录限制。
2. 绑定source ID、URL/版本、日期、章节/表格。链接可读、摘要已读、指定章节已读、全文已读和独立复现分开。引用定位必须属于该来源。
3. 按挑战、机制、对照、条件、效果、边界记录作者结果；按新增能力、代价、替代路线和改变判断的证据写分析。
4. 新领域使用 [claim-contract.md](references/claim-contract.md)；已有压缩内容沿原表维护，不复制迁移。

## 比较边界

- 保留模型、测试集、硬件、运行栈、数值配置、负载、基线。前向或prefill耗时不能换名为服务TTFT；均值、P95、吞吐和峰值内存分开。
- 量化载荷、完整缓存、总峰值内存分母不同；理论节省单列。百分点和相对百分比区分。
- 组合整体收益不能归给单组件。跨卡数、并发、架构比较不包装成单因素因果。
- 论文结果、工具支持、格式导出、执行生效、业务验证逐级区分。单设备结果不证明另一设备支持。
- 新证据可支持、收窄、推翻或暂不改变判断；保留变更理由，不悄悄改成“始终如此”。

## 输出

不输出跨条件最优榜单。指出具体技术、值得比较的基线、原因及判定条件；证据不足标候选。新主题运行 `python scripts/insight_topic.py validate <topic.json>`，压缩内容运行既有校验。结构检查不能代替专家读原文。
