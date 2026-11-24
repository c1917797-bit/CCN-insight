# 月度洞察维护

月度报告回答“这个月新增的证据怎样改变判断”；长期专题继续解释原理、路线和经典工作。数据唯一源为 `data/compression/tables/`，不要改生成的 `dist/` 或复制回旧 TableGit。

## 本期入口与范围

2026 年 11 月使用 `ic-2026-11-reviewed-20261124-v1`，窗口 11 月 1—24 日。`ic_monthly_scopes.digest_json` 保存综合判断、原文版本、跨路线比较和覆盖限制；`ic_monthly_route_insights` 保存逐篇取舍，`ic_paper_summaries` 保存对应版本的事实笔记。相同论文跨 W/A/KV 引用同一份记录。

11 月是月内更新，不称整月终版。649 篇是 HF 推荐发现池，147 篇是关键词线索；21 篇回原文核查、12 篇核对指定章节，其中 16 篇进入主研读、5 篇保留邻接观察。产业按原始 URL 去重为 15 个当月来源事件。不要把这些数字相加或称为全领域总量。

## 更新步骤

1. 从登记的核心信源获取当月列表、官方发布说明与候选原文。`scripts/refresh_registered_sources.py` 保存每个入口的取得状态和原始响应哈希。失败、限流、只读首屏均记录覆盖缺口；不得转成零成果。
2. 推荐日期只用于发现。回原文确认首次提交、修订版本、发布日期与采集日期。预印本按稳定 ID 去重，产业按原始发布 URL 去重。候选未匹配关键词不代表原文已排除。
3. 分别写问题、机制、原文结果、编辑判断和边界。先核对格式、模型、硬件、负载、基线和恢复预算；只读摘要就保留摘要层级，取得 HTML 不等于阅读。无对应原文不补数。
4. 用新的截止日和 scope 固定一版材料与判断。`scripts/prepare_monthly_review.py` 合并经人工/代理逐条核对的注释文件；默认仅预演，`--apply` 才写唯一源。它校验整批后再替换，并保留旧月、旧 scope。它不负责自动理解原文或自动提升阅读层级。
5. 通过 `scripts/monthly_digest.py` 复算数量、版本关系与四根技术覆盖。`ic_monthly_materials` 保留发现、关键词命中和审阅状态；公开 CSV 仅导出元数据与决定，不发布取得的全文/摘要副本。
6. 执行构建和检查，再检查真实页面：默认月份、月内动态、完整报告、原文笔记、归档、旧月切换和窄屏。推送 GitHub 后按原 Sites 身份发布；成功部署回执才表示上线。

## 数量与证据边界

发现池、相关候选、原文核查、指定章节审阅和重点选择是不同阶段。被选为重点也不等于独立复现。每个数值与其精确版本及原文位置一起保存。

四根技术需要逐项说明本月证据或覆盖缺口。LowRAM 是 KV 低秩研究，不能用它填补权重低秩空白。跨请求缓存池、卸载和配额回收也不等于 GQA/MQA、数值量化或新的 token 淘汰算法。

本期 arXiv 批量查询受到 429 限流，HF 推荐不是其全量替代。llama.cpp 取得的发布首屏仅覆盖到 11 月 23 日；会议和资讯索引不构成全月穷尽检索。后续补查应增加新 scope 或明确修订记录，不抹掉这一版的限制。

审计：`monthly-acquisition-review-20261124.json`；本地验收：`monthly-insight-local-qa-20261124.json`。原始采集材料仅在被忽略的本机 `.tmp/monthly-2026-11-20261124/` 中，Git 不含该批全文。线上可下载发现清单与信源核查记录。

## 必要检查

```text
python scripts/build.py
python scripts/verify.py
python scripts/verify_compression.py
python scripts/verify_original_reader.py
python scripts/verify_tablegit_migration.py
python scripts/test_monthly_digest.py
node scripts/test_monthly_organization.cjs
node scripts/test_current_report_synthesis.cjs
node scripts/test_reader_journey.cjs
```

本期同时回归月度候选漏斗、10 月总表和论文效果对照。只有修改这些功能或出现相关失败时，才重复扩大检查。
