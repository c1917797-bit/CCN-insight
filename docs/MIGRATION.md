# 迁移状态（2026-10-21）

## 为什么此前仓库为空

CCN 首页此前在 Sites 托管环境构建发布，AI Infra 页面由 LRIGIT 的 works 仓库提供。GitHub 的 CCN-insight 只是创建了空仓库，二者没有配置同步。本次将本地保存的应用资料和最新信源目录显式提交到这个仓库。

## 已纳入

- 2026-10-21 后续同步：CCN 正式站根技术地图、14 个二级技术节点、16 个原压缩专题快照、研究方法页与正式导航。源码位于 `research/ai-infra/` 和 `publish_infra.py`。
- 主仓库现为本 GitHub 仓库；Sites 用作发布镜像，尚未配置自动同步。

- CCN 四大板块首页生成器、样式、动画及两张首页内容表快照。
- AI Infra 源码快照，原始版本记录在 vendor/ai-infra/SOURCE-MANIFEST.json；部分入口和导航文件另行更新，详见 source-overrides.json。原始 COPY-VERIFICATION.json 只描述当时复制，不能代表更新后的全树。
- 16 张已有业务表，共 10,953 条导出记录。保留 imported_unverified 等状态，它们不是 10,953 条已核验洞察。
- 本次从 TableGit 读取的信源主体、渠道、主体渠道关系、产业分类及渠道所引用的来源记录。cloud_core_sources 只导出渠道引用的 332 条，不是全表。
- 可独立阅读、搜索和下载 CSV 的信息源表格。

## 尚未完成

- 原 AI Infra 动态数据接口的独立替换与全量数据导入。
- PPT、PDF、视频等报告附件的完整迁移。
- Agent 报告已于2026-10-23迁入本仓库，原独立网址保留为发布镜像；详见文末补充。
- GitHub Pages 启用、自有域名绑定及全站部署验收。

本仓库不是 TableGit 服务端的完整副本，也未改变原网站发布或权限。

## 发布和权限

自动流程会检查并保存 dist 构建产物。启用 GitHub Pages 可选择从 main 的 /docs 发布（需要另行设置输出目录），或配置官方 Pages Actions 发布流程。本次不将研究文档 docs 误作为网站发布目录。

网站运行账号、服务端密钥、浏览器会话和原仓库 .git 历史不随复制公开。公开仓库允许所有人阅读，只有获授权协作者可以直接写入。


## Agent 报告迁移补充（2026-10-23）

Agent 调度报告22页与构建源已纳入 `research/agent-scheduling/`，由本仓库统一维护。下文此前对 Agent 未迁移的说明已由此项更新。原独立网址继续作为发布镜像，未改变CCN首页入口；没有迁移LRIGIT服务端，也没有配置自动发布。详见 [发布流程](AGENT-REPORT-PUBLISHING.md)。
