---
name: ccn-insight-build
description: Build or refine CCN expert insight topics, including new 极稳 domains, using reusable topic contracts and the existing reader. Use for insight websites and topic architecture, not standalone slides or model experiments.
---

# CCN 专家洞察构筑

先读根目录 AGENTS.md 和 `.agents/HANDOFF.md`，再按注册表选择窄 skill。

## 维护路径

- 现有推理压缩：唯一内容源为 `data/compression/tables/*/rows.jsonl`，界面在 `original-reader/site/business_insight/cloud_core/`。通过现有构建链生成，不另建“更漂亮”的内容副本。
- 新领域：`python scripts/insight_topic.py new --domain wen --slug <topic> --title <名称> --question <研究问题>` 生成 `content/insights/<domain>/<topic>/topic.json`。它是未发布起点，不自动接入导航或部署。
- 窄文案修正直接改维护源，不启动整套研究。

## 专家价值

用证据回答：研究什么、机制如何、相对哪条路线增加什么、效果何时成立、哪些新证据会改变判断。新领域先建挑战与路线，不把推理压缩的四条路线、硬件或业务门槛套给极稳。

每页先呈现核心判断，一跳抵达案例。事实、作者结果、编辑分析和假设分开；未报告指标保留空缺。证据核对使用 `ccn-evidence-review`。

长期专题保存机制与路线；本期动态记录有日期依据的增量；洞察报告解释如何改变判断。同一案例只维护一份，通过稳定ID关联。

## 阅读与验收

复用阅读器和组件。速览可增强视觉，正文须可选择、可搜索、可引用。动效说明变化；不把长文字烘焙进图，不用装饰代替技术图。保留焦点、降低动态偏好和图的文字解释。

按 [reader-and-content.md](references/reader-and-content.md) 选择检查，逐页核对加载、锚点、检索、引用、待读与长标题。构建通过不代表原文正确、已发布或业务成功。

交付说明证据、验证限制及部署状态，更新交接。仅在出现可复用经验时使用 `ccn-experience-evolve`，不要为每次措辞修改新增规则。

报告工具按 [report-tools.md](references/report-tools.md) 的已选策略：日常网站保留阅读器，滚动报告优先 Report，需要可编辑 PowerPoint 时选 ywqpptpro。实际使用外部 skill 时按完整流程执行，单纯借鉴不记为运行。
