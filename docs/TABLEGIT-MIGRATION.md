# 推理压缩 TableGit 本地迁移

迁移日期：2026-10-22。状态：**用户已授权推送 GitHub；两个公开站点尚未发布更新。**

## 已迁入的范围

来自 TableGit 固定提交 `a3bc462ac420682111533e6877cb600f6d727b1a`，限定业务 `cloud-core`、专题 `cloud_core`：

- 91 张相关表，63,873 条活动记录；按原站当前页面和模块的数据依赖发现，不是整个 TableGit 实例的所有业务。
- 16 个压缩课题、145 张研究卡片、26 条技术路线、287 条卡片引用、622 条课题事件关联。
- 38 份论文总结及其版本绑定、5,029 个证据事件、产业动态、热点、路线判断、验证建议、采集与筛选记录。
- 6 个报告版本、182 个附件登记；全部附件已下载，逐件核对 SHA-256 和文件大小。旧版状态 superseded 原样保留。
- 所有查询固定同一个版本并完整分页；无未解析的 content_ref。原文事实、作者实验结果、分析建议、未审阅候选状态不变。

## 唯一维护位置

`data/compression/tables/<表名>/rows.jsonl` 是本地结构化内容的唯一维护处。

每行包含 `key`、`row_version`、`row` 等原始记录字段；修改内容编辑 `row`，保留原有 ID 和关联键。原有 row_version 是导入时 TableGit 的版本信息，不代表本地修改会回写 TableGit。本地后续修改由 Git 记录。

- `definition.json` 保留原表结构，供校验和理解字段。
- `manifest.json` 保留导出范围、行数、原始提交及导入时哈希。初次导入校验使用这些哈希；之后有意修改内容时，与导入哈希不同是预期现象，不能冒充仍与原站一致。
- `data/compression/assets/` 保存报告附件，文件名按内容哈希，避免重名覆盖。
- `data/compression/assets.json` 记录附件原始路径、本地路径及校验结果。
- `research/ai-infra/imported/`、两个专题快照和 `data/directory/` 为兼容旧构建程序的**生成视图**，不再作为另一份手工编辑源。运行 scripts/materialize_compression.py 可重新生成。

## 本地查看

```sh
python scripts/build.py
python scripts/verify.py
python scripts/verify_compression.py
python scripts/verify_tablegit_migration.py
python -m http.server 8781 --directory dist
```

默认打开 `/business_insight/cloud_core/index.html#view-topics`，使用原版界面与本地数据适配。辅助预览位于 `/ai-infra/compression-migration/`。此预览提供信息来源、课题地图、本期动态、洞察报告、归档五个入口；课题复用 CCN 静态课题页，报告文件和逐页图片均为本地文件。候选事件索引与已审阅总结分开展示，归档从2026年10月开始。

阅读和构建无需连接原 TableGit。外部论文、官方仓库链接仍作为原始出处保留；它们与原站运行依赖不同。所有原始数据迁移不等于重新核验其事实，也不等于已实现原站所有交互。

## 尚未发生的切换

- 未修改原站的表或代码。
- 本批文件已获准推送 GitHub；CCN 或 LRIGIT 公开站仍未更新。
- 现有正式导航仍可能指向原站；新内容先在本地迁移入口检查。
- 尚未建立双站自动发布。原站仍读原 TableGit；只有正式切换完成，才能停止原站的重复维护。不得在两边同时修改同一批课题后声称已同步。

## 校验与追溯

完整性报告：`docs/tablegit-migration-validation.json`。原始查询分页备份保存在仓库外的工作区 `.tmp/tablegit-export-<revision>/`，不参与发布。

若以后重新导入 TableGit，先生成另一批次并比较差异，不能直接覆盖本地已编辑数据。
