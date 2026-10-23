# Agent 调度报告：唯一可编辑源

本模块于 2026-10-23 从原独立预览站的构建源迁入 CCN-insight。五段主线、22 页内容与咖啡动画保留；增加架构师阅读层。

## 维护

- CSV 文件分别保存信源、论文事实、路线关联、研究建议；不要把它们合并为一个大 JSON。
- `architecture-decisions.csv`：三项技术的架构接入契约。
- `architecture-evidence-links.csv`：19 项资料与架构决策的关联；分析不是原文事实。
- `architecture-references.csv`：另行核对的4项架构依据，不冒充本期新增事件。
- `source-profile.csv`：信源入口类型与证据用途；它不是可信度评分。主表展示来源身份、研究价值、关注重点与人工跟踪建议，默认保留全部来源；具体文章与论文继续进入动态。
- `source-groups.csv`：热点资讯、学术界、产业界各一张总表，严格3张；二级分类仅作为表内行组，来源必须匹配唯一分组。保留旧来源与分层锚点，兼容已有链接。
- `object-research-contracts.csv`：7个执行对象的触发、输入输出、对照、反例与官方机制；`route-baselines.csv`逐项定义11条路线的对照设计。
- `decision-research-contracts.csv`和`decision-methods.csv`：4类决策的研究契约与12项机制候选。研究方案不等于已有实现。
- `expert-console.css`与`expert-reading.js`：统一专家阅读样式、章节状态与进度；正文与SVG先生成，浏览器无需外部库即可读取内容。
- Python 文件负责渲染；CSS / JS 负责阅读体验与教学模拟；`templates/` 是基础模板。
- `site/`、`outputs/`、仓库 `dist/` 都是生成物，不能作为另一份手工编辑源。

运行：`python scripts/build_agent_report.py`，随后 `python scripts/verify_agent_report.py`。
动画检查：`node research/agent-scheduling/check_coffee_engine.cjs` 与 `node research/agent-scheduling/check_coffee_scene.cjs`。

内容窗口截至 2026-10-23；本次重点筛选 10月17—23日，新增4项。weekly-selection.csv 保存周选关联，weekly-source-checks.csv 记录采集限制。不是实时 TableGit 服务，也没有自动每日采集。

## 发布

见仓库 `docs/AGENT-REPORT-PUBLISHING.md`。不得重新从旧工作区 `.tmp` 生成发布文件；本目录已经成为维护源。
