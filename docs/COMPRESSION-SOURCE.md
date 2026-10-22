# 推理压缩唯一维护源

更新：默认预览和双站文件已改用原样阅读器，入口为 /business_insight/cloud_core/index.html#view-topics；原来重排版的 migration 阅读页不再作为默认交付。双站安装目标都保留 business_insight/cloud_core/ 与 assets/ 目录。见 ORIGINAL-READER-PARITY.md。

## 维护入口

启动：`python scripts/maintain_compression.py --port 8785`。

打开 http://127.0.0.1:8785/ 。维护台只能在本机访问，不是公网后台，也没有发布接口。

1. 选择研究课题与内容类型，打开一条记录。
2. 修改正文、标题、路线、引用等字段，点击“保存并校验”。记录 ID 和业务归属被保护；版本过期或引用检查失败时不接受修改，失败写入会恢复原文件。
3. 点击“生成预览与两站文件”。检查本地阅读预览，满意后再另行批准公开发布。

常用内容：课题卡片、课题章节、技术路线、背景挑战、文献引用、论文总结、产业动态、热点和报告目录。其他表保留在内容类型列表供维护关联关系。本版编辑器支持修改已有记录；新建／删除记录和上传新附件仍通过维护代码及完整关联校验完成，不提供未经校验的直接增删按钮。

## 唯一数据源与生成物

- **唯一内容源**：`data/compression/tables/*/rows.jsonl`；附件在 `data/compression/assets/`，登记在 `assets.json`。
- `compression_store.py` 是统一读取入口，构建过程不请求 TableGit。
- `research/ai-infra/imported/`、`data/directory/` 和专题快照是兼容生成视图，不手工编辑。
- `dist/` 是阅读页面；`local-releases/` 是两站待发布文件，也不手工编辑。
- `.maintenance/` 保存维护台的编辑备份和变更日志，不进入公开仓库。

TableGit 的导入提交仅用于追溯。新的 `compression-…` 内容版本由本地实际表结构、记录和附件登记计算；编辑后会改变，不能继续把新内容标成原始 TableGit 快照。

## 一次生成，两站使用

命令：`python scripts/stage_compression.py`。

输出在 `local-releases/<内容版本>/`：

| 输出 | 安装目标 |
|---|---|
| `original-reader/ccn/business_insight/cloud_core/` | CCN 网站的 AI Infra 模块 |
| `original-reader/lrigit/business_insight/cloud_core/` | 原网站的推理压缩模块 |

两份文件共用同一批内容与渲染器，分别适配安装路径；原站常用 `#view-home`、`#view-updates` 等链接有静态入口适配。每份都记录 `compression-version.json`；构建程序逐文件核对共享文件哈希。一份构建失败不能宣称两站同步完成。

这是**待发布静态模块**，不是原站整个后端的替代，保留原版界面及已适配的读取交互；静态适配器仅支持原阅读器使用的读取请求，不提供 TableGit 写入能力。现有页面的原文链接继续作为出处保留。原站的其他业务模块不在该输出范围。

## 当前公开状态

统一维护源、维护台、双站待发布文件已在本地建立。原公开站仍读取旧 TableGit，CCN 公开站也未更新；用户现已授权推送 GitHub，未授权部署公开网站。

正式切换前需分别完成目标站发布、入口与缓存验证、共同版本核对，再停止对旧 TableGit 的课题编辑。两站发布不是跨服务原子操作；发布记录需分别保存目标站版本和状态，不能将本地哈希一致当成线上已切换。

## 校验与恢复

`python scripts/verify_tablegit_migration.py` 检查当前关联和附件，允许有意编辑后与导入哈希不同。

`python scripts/verify_tablegit_migration.py --check-import` 额外要求与原导入完全一致，仅用于初始迁移核验。

每次维护台保存都会备份整张受影响表到 `.maintenance/backups/<change_id>/rows.jsonl`，并记录前后内容版本。用备份恢复后须重新生成预览和两站文件。不要从旧 TableGit 静默覆盖已经维护过的本地内容。
