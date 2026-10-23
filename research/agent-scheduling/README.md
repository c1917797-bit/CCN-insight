# Agent 调度报告：唯一可编辑源

本模块于 2026-10-23 从原独立预览站的构建源迁入 CCN-insight。当前包含 23 个研究页面、25 项已登记并注明核验范围的资料，以及 27 个持续信息源。保留“信息来源 → 技术地图 → 本期动态 → 分析结论 → 洞察归档”五段主线与咖啡动画。

本轮整理和验收状态见 [来源到调度决策的十阶段审视](../../docs/AGENT-SOURCE-DECISION-REVIEW.md)。资料数量不代表全文均已深读；具体核验层次以每条记录为准。

## 维护

内容维护先参考 [成品学习与写作规范](../../docs/AGENT-REPORT-AUTHORING.md)：继承 MozhiJiawei CCN 成品的机制解释、原图证据、比较口径和适用边界，保持本模块五段主线。该文记录实际学习范围及当前差距，不代表完整技能流程已执行。

- CSV 文件分别保存信源、论文事实、路线关联、研究建议；不要把它们合并为一个大 JSON。
- `architecture-decisions.csv`：三项技术的架构接入契约。
- `architecture-evidence-links.csv`：25 项资料与架构决策的关联；分析不是原文事实。
- `architecture-references.csv`：另行核对的4项架构依据，不冒充本期新增事件。
- `source-profile.csv`：信源入口类型与证据用途；它不是可信度评分。主表展示来源身份、研究价值、关注重点与人工跟踪建议，默认保留全部来源；具体文章与论文继续进入动态。
- `source-groups.csv`：热点资讯、学术界、产业界各一张总表，严格3张；二级分类仅作为表内行组，来源必须匹配唯一分组。保留旧来源与分层锚点，兼容已有链接。
- `source-domain-links.csv`：来源与依赖感知排程、状态感知映射、干扰感知分配的关联。同一来源可以关联多个研究方向，但只在其所属大类总表出现一次。
- `source-checks-20261023.csv`：本轮人工核查的入口、结果和读取限制；失败记录也保留，不能将未读取写成没有更新。
- `source-verifications.csv`：27个信源逐项核验的累计记录；入口读取结果、核验深度和已收录研究依据分开。页面展示具体发现、原文、边界、下一步及建议复核日；旧访问记录继续保留。维护和准入规则见[核验规范](../../docs/AGENT-VERIFICATION-STANDARD.md)。
- `collection-feeds.csv`、`collection-runs.csv`和`signal-candidates.csv`：公开候选采集配置、运行记录与去重后的待审元数据；不直接生成已核验事实。
- `evidence-batch-20261023.csv`：本轮新核验的6项资料及其决策增量，区分本月版本、较早机制和媒体线索追溯，不等同近一周新发布。
- `publication-discovery-links.csv`：保留媒体发现路径；事实依据仍指向官方原始发布。
- `decision-watchlist.csv`：当前研究判断、投入条件、推翻条件与建议复核时间；没有配置自动提醒或自动执行验证。
- `object-research-contracts.csv`：7个执行对象的触发、输入输出、对照、反例与官方机制；`route-baselines.csv`逐项定义11条路线的对照设计。
- `decision-research-contracts.csv`和`decision-methods.csv`：4类决策的研究契约与12项机制候选。研究方案不等于已有实现。
- `expert-console.css`与`expert-reading.js`：统一专家阅读样式、章节状态与进度；正文与SVG先生成，浏览器无需外部库即可读取内容。
- Python 文件负责渲染；CSS / JS 负责阅读体验与教学模拟；`templates/` 是基础模板。
- `site/`、`outputs/`、仓库 `dist/` 都是生成物，不能作为另一份手工编辑源。

## 从候选到研究判断

以下命令均在仓库根目录运行。按需抓取公开元数据：

```text
python scripts/collect_agent_signals.py --start 2026-10-01 --end 2026-10-23
python scripts/test_agent_collection.py
```

采集器当前接入 7 个公开入口：Ray、LangGraph、Temporal Go SDK、vLLM、vLLM Ascend、UCM 的 GitHub 发布列表，以及 arXiv 的系统相关学科 Atom。可用 `--feed ray-releases` 等配置内 ID 限定重试范围；可用 `--output-dir .tmp/agent-signals-review` 先生成独立审阅结果。请求失败最多尝试3次，结果写入运行记录。

截至 2026-10-23，本轮机器关键词筛选得到 **64 条候选**。与已核验资料按网址／论文标识比对后，页面显示 **60 条仍待原文审阅**；4 条已存在于核验库，因此不重复计入待审数量。候选表中的默认审阅标记不能单独用于统计，应同时排除已关联的资料。

这不是自动订阅，也不是27个来源的全量最新内容。GitHub 每个入口仅读取最近40个发布项；arXiv 只返回当前公告批次，日期窗口参数不能补齐缺失的历史。arXiv 的 `feed_date` 是订阅公告日期，**不是论文首投日或修订日**，必须到论文提交历史核实。

每轮维护按以下顺序进行：

1. **候选筛选**：查看 `signal-candidates.csv` 和 `collection-runs.csv`。关键词命中只意味着值得审阅；记录不相关、重复或无法读取的原因。
2. **原文核验**：核对原始日期、版本、挑战、机制、实验条件与限制。事实进入 `research-publications.csv` 和 `research-findings.csv`；核验范围进入 `evidence-reviews.csv`。没有发布日期时留空，不能用核对日代替。
3. **关联专题**：通过 `publication-source-links.csv` 连接来源，通过 `research-publication-links.csv` 关联真实技术路线，写清直接支撑或边界对照。媒体发现另存发现链。
4. **形成判断**：在 `architecture-evidence-links.csv` 说明该资料改变哪项决策；在 `decision-watchlist.csv` 写投入前提、可推翻判断的反例和复核触发条件。建议验证不能冒充已完成实验。
5. **构建验收**：运行下列构建与检查；打开实际页面验证表格筛选、专题跳转、折叠内容、图示及移动布局。通过后推送主仓库，再按发布流程更新远端站。

```text
python scripts/build.py
python scripts/verify.py
python scripts/build_agent_report.py
python scripts/verify_agent_report.py
node research/agent-scheduling/check_coffee_engine.cjs
node research/agent-scheduling/check_coffee_scene.cjs
```

内容窗口截至 2026-10-23；`weekly-selection.csv` 保留10月17—23日的4项周选，`weekly-source-checks.csv`记录该周筛选限制。本轮补录不扩充为6条“本周新增”。网站是构建发布后的只读快照，不是实时 TableGit 服务；没有自动每日采集、自动原文核验或自动发布。

## 发布

见仓库 `docs/AGENT-REPORT-PUBLISHING.md`。不得重新从旧工作区 `.tmp` 生成发布文件；本目录已经成为维护源。

## 专家阅读改造

技术地图的整理依据、机制图、原文深读与实际验收记录见 [2026-10-23 专家阅读审视](../../docs/AGENT-MAP-EXPERT-REVIEW.md)。新增内容从 `expert_map.py`、`research_mechanisms.py` 和 `deep_readings.py` 维护；原图出处与实验数值分别保存在小型 CSV 中。
