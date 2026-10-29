# 推理压缩唯一维护源

## 2026-10-29：两个入口已在线上共用同一份内容

原站和 CCN 的网站首页保持不变。原站的推理压缩 URL 现在会转到 CCN 唯一阅读器，保留月份、范围、课题和章节位置。已使用实际 c1b3ie6ayp 地址验证信息来源（有／无月份参数）、AWQ 案例、月度证据、基础原理、当前报告与报告归档。发布与范围见 `../deployment/compression-shared-entry-publication.json`，实测记录见 `shared-compression-entry-online-qa-20261029.json`。

日常只维护本仓 `data/compression/tables/*/rows.jsonl`、登记附件及 `original-reader/site/business_insight/cloud_core/` 阅读器。完成构建、验证并发布 CCN 后，两个入口使用同一份线上内容，无须再向原站复制正文、图片或报告。只提交 GitHub 而没有发布 CCN，线上内容不会自动更新。

原站七个转接文件由 `deployment/compression-entry.json` 和 `scripts/build_original_entry.py` 生成，原站只在入口规则变更时需要单独发布。`archive.html` 指向当前报告归档 `index.html#view-reports`；旧 CCN 资料库 archive 页面没有在本轮完整迁移，不作为推理压缩归档入口。两站其他栏目和旧 TableGit 历史数据未改动。

维护者批准了仅七文件的局部发布，接受已说明的原站既有全库校验失败；本轮没有关闭检查或改动权限。原站实际发布提交为 c85a4ef4c8f0d6400821c17b402eb69b6a29850c，原生同步检查确认 main 与 origin/main 一致。以下“未切换”段落属于历史记录，不能作为当前状态。

## 2026-10-28：统一内容源与线上入口的实际状态

唯一可编辑内容仍在 CCN-insight 的 `data/compression/tables/*/rows.jsonl`，阅读器在 `original-reader/site/business_insight/cloud_core/`。构建不从旧 TableGit 回填内容。GitHub 推送、CCN 部署和原站发布是三件不同的事。

原站目前仍保留旧入口，**尚不能声称两站线上已共源**。本轮准备的统一方式是：CCN 托管一份正式阅读器，原站的五个推理压缩入口直接转到这份阅读器。保留 month、scope、topic、lang 与正文锚点，不转发其他参数；不套 iframe，不把原站其他栏目或 Agent 页面重定向。

- 入口配置：`deployment/compression-entry.json`。
- 原站待发布入口：`python scripts/build_original_entry.py`，输出到 `.tmp/canonical-entry/`，绝不覆盖 CCN 的 `dist/`。
- CCN 构建标记：`/business_insight/cloud_core/compression-release.json`，分别记录内容、阅读器与界面版本。相同内容哈希不代表相同页面已部署。
- 验证：`node scripts/test_compression_entry.cjs`，覆盖五入口、参数与锚点保留、无关参数排除和循环跳转保护。

只有原站入口通过其完整校验、正式发布，并在用户实际使用的地址验收后，才形成“一次维护，两个入口使用同一阅读器”。在此之前，CCN 继续独立发布，原站保持线上版本。本轮原站候选、受限修复与剩余阻挡见 `COMPRESSION-DEMO-20261028.md`；最新成功的 CCN 版本以 `deployment/ccn-publication.json` 为准。

下面保留的双份静态模块方案是早期导出流程，仍可用于隔离预览和迁移；它不会自动更新两个公网网站，不再作为已实现共源的证明。

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

2026-10-22：用户已授权两个公开网站发布。CCN 第12版已成功上线，公开技术地图、权重量化专题、报告阅读器与封面图片已验证。原站尚未切换：既有全库样式校验存在34个缺少定义的类，涉及多个其他栏目；候选内容未合并到正式站。详见 compression-publication-20261022.json。

正式切换前需分别完成目标站发布、入口与缓存验证、共同版本核对，再停止对旧 TableGit 的课题编辑。两站发布不是跨服务原子操作；发布记录需分别保存目标站版本和状态，不能将本地哈希一致当成线上已切换。

## 校验与恢复

`python scripts/verify_tablegit_migration.py` 检查当前关联和附件，允许有意编辑后与导入哈希不同。

`python scripts/verify_tablegit_migration.py --check-import` 额外要求与原导入完全一致，仅用于初始迁移核验。

每次维护台保存都会备份整张受影响表到 `.maintenance/backups/<change_id>/rows.jsonl`，并记录前后内容版本。用备份恢复后须重新生成预览和两站文件。不要从旧 TableGit 静默覆盖已经维护过的本地内容。
