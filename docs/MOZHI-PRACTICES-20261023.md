# Mozhi 工作区方法借鉴与实际使用 · 2026-10-23

本记录区分已执行、阅读借鉴、可用未执行与新编写。固定来源及证据路径见 [skill-provenance.json](../.agents/skill-provenance.json)。技能说明、测试目录或成品外观，都不能证明某份报告由哪个技能生成；本轮没有取得逐件运行清单。

保留 CCN 的「信息来源 → 技术地图 → 本期动态 → 洞察报告 → 洞察归档」及现有技术分类，优先迁移四项方法：

1. **先理解来源**：重点材料讲清对象、约束、机制、原图表与证据边界，再形成判断。摘要摘录保持摘要级；理论界限、厂商报告和本地实测分别表达。
2. **一份简报回答一个中心问题**：沿问题 → 方法 → 效果递进，结果保留基线、条件和限制，以自然语言提出建议。归档摘要写完整技术判断，包含对象、场景、已核实指标或状态及时间边界，避免只有关键词。
3. **叙事规划后独立审图**：长文按读者问题组织，关键图旁解释读法；结构检查、截图与独立视觉 QA 分别记录。借鉴 Report 流程，不把 PPT 固定 16:9、禁动画等约束套到网站。
4. **内容维护一次，再聚合发布**：单份材料保存来源、日期、版本和关联专题，月度报告引用并综合判断，归档固定版本。继续使用 CCN 唯一维护源，不复制对方的十三大类、五十分支，也不把静态报告替代网站数据层。

| 来源与固定版本 | 本轮状态与边界 | 证据或维护路径 |
| --- | --- | --- |
| [web-article-capture / b23243d](https://github.com/MozhiJiawei/web-article-capture/tree/b23243de458626bd53093e9114b4a6840234abde) | 已执行有限采集：三个 arXiv 摘要包；未全文深读 | `research/source-audits/20261023-expert/{kivi,sparsegpt,think}/source.md` |
| [ppt-deep-search / 7eb5758](https://github.com/MozhiJiawei/ppt-deep-search/tree/7eb5758f0ffeff933cbced7040b265c180c6a1da) | 已读借鉴；未完整执行来源理解审阅流程 | 本文；`docs/EXPERT-QUALITY-20261023.md` |
| [hw-ppt-gen-html / 0c79a8e](https://github.com/MozhiJiawei/hw-ppt-gen-html/tree/0c79a8e4823ffcb8b32e49783d9d7411d94006cd) | 已读借鉴；本轮未生成新 deck 或执行完整渲染流程 | 本文；`docs/expert-topics-browser-qa-20261023.json` |
| [grobid_pdf_skill / aa45aa2](https://github.com/MozhiJiawei/grobid_pdf_skill/tree/aa45aa2ca9499e2c8ae740b0e90443b54ad97d95) | 可用、已读；本轮未解析 PDF | 本文 |
| [单页报告 / c1c8b7a](https://github.com/Real-UtopiaNo/create-single-page-tech-report/tree/c1c8b7a06b7f5c61eb2abb94d53cd53f141a83a5) | 已读借鉴，未执行；作者为 Real-UtopiaNo | 本文 |
| [ccn-report / 0a02822](https://github.com/MozhiJiawei/ccn-report/tree/0a028222aeffa7752a56cdf805a3a719ab30e97e) | 已读归档规范；它是报告仓库，不是 skill | 本文 |

本轮还使用 Sites 的本地维护流程与 skill-creator 的窄范围编写方法，未发布网站。CCN 自有三项技能为新编写，结构及回归检查不能证明已成熟；候选经验仍按实际状态保留，后续用真实任务验证。网页的内容正确性、移动端可用性和论文复现各需独立证据。

当前工具选择见[报告工具策略](../.agents/skills/ccn-insight-build/references/report-tools.md)：网站保留现有阅读器；后续滚动报告优先hw-ppt-gen-html Report，可编辑PPT选ywqpptpro。此轮没有重新生成PPT，也不把这些工具当成全站替代框架。
