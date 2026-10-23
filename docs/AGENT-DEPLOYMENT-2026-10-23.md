# Agent 调度报告发布记录 · 2026-10-23

- 唯一维护仓库：https://github.com/c1917797-bit/CCN-insight
- 报告源提交：`ea424c6fc7520a53fc4f7d742dc34f384f8a5767`
- 发布镜像提交：`1177d497033e47948a1707ec1e9c98abc2cfe43f`
- Sites 项目：`appgprj_6acf4d01d4a48191a167ab0a3ff7b192`
- Sites 版本：25
- 部署：`appgdep_6adb54d7204c8191a72d78d33a0ce14a`，状态 `succeeded`
- 线上入口：https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/?v=25#updates-week

保留原网址、公开只读访问和五段主线，没有加入CCN首页导航。GitHub为维护源，Sites为人工同步的发布镜像，尚未配置自动发布。推理压缩源码及正式站未随本次发布改写。

## 本周增量

窗口为2026-10-17—23，新增4项：ACTS、Dual-control MAS两篇预印本，以及vLLM 0.32.0、UCM 0.8.1两个发布版本。论文只核验摘要与提交历史；工程条目核验正式发布说明。均保留来源、日期、研究关联与证据限制。非全量采集；未完成官方原文核验的新闻与元戎发布详情不列为本周已确认事件。

原有15项资料保留原复核日期；当前累计19项、35条路线关联。新增架构职责SVG、三项接入契约、逐条架构影响和本周路线判断。建议尚无云核实测验证。

## 验收

- 整仓构建与既有验证通过；Agent模块独立构建通过。
- 22页结构、1541条模块内链接、19条证据—架构关联与3项接入契约检查通过。
- 浏览器逐页打开21个专题，检查主页面五个页签、周选跳转、详情展开、信源切换和手机宽度布局。
- 咖啡模拟：4种场景、52个状态；依赖、并发、授权、单次提交及恢复检查通过。
- 正式域名可直接打开，4张周选卡片可见；UCM事实详情可打开并跳转至状态感知映射专题。
- 扫描迁移源与发布HTML，未发现凭据模式或本地路径泄漏。

Windows官方打包步骤失败后，按同一个已推送镜像提交打包；save/deploy返回版本25发布成功。没有把本地生成或GitHub推送本身当作线上部署成功。

## 信源目录迭代发布 · v28

用户要求表格展示，并进一步参考成熟的信息源管理实践。最终目录采用“信息源与入口 / 定位与研究价值 / 关注内容与跟踪方式”三列；名称直达主入口，同源其他渠道就近展开。人工建议频率与最近核对日期分开，证据用途不作为可信度评分。默认全部26源，保留三类、子类、生态、核心筛选与搜索；NeurIPS、ICML、ICLR默认可见。目录与具体论文、事件分开维护。

| 版本 | GitHub内容提交 | Sites镜像提交 | 结果 |
| --- | --- | --- | --- |
| 26 | b94fa8be433fa12cc46303ef0fd0bd7f3dcd9407 | 8bacd959ad57ba6f5434362d710d04cb57efcdd9 | succeeded |
| 27 | aac588a（表格宽度适配） | 69db2ac0fe76c6ea584e217733338d843d58efab | succeeded |
| 28 | fc65e41edbb324a14bf87815ef355d140f7065fc | 5cd2aaf0ba6c4b61e8237f54d312dabf2588bfee | succeeded |

最终部署：`appgdep_6adb59a7280081918b92d5e103f4bb31`；访问 https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/?v=28#sources 。

整仓构建与校验、22页模块结构与内部链接检查通过。浏览器验证三类切换、搜索及空结果、核心筛选、生态筛选、来源深链接、主入口与相关渠道、行内展开。窄桌面表格内容宽度与容器一致，手机在表内横向滚动。正式域名可见26条目录记录、三个新表头与默认9个学术信源；三大顶会均可见。整理实践的参考原文与字段契约见 `docs/AGENT-SOURCE-CATALOG.md`。仍为人工维护，未配置自动订阅。

## 三级分类发布 · v29

一级顺序统一为“热点资讯 → 学术界 → 业界”。二级分组分别为2、4、5组，每组独立成表；表格仍按来源身份、研究价值与跟踪方式三列阅读。26来源仅调整分组，原文资料、核对日期与关联保留。

- GitHub内容提交：`ace8b1e83ced71c0aee67d226aa1878554d75a89`
- Sites镜像提交：`2249a4c1060085014a638e30582b4bc62ccb5f69`
- Sites版本：29；部署`appgdep_6adb5d6dba488191bd9d8d3dd40eb829`，`succeeded`
- 入口：https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/?v=29#sources

整仓构建与校验、22页结构和1548条模块内部链接通过。浏览器逐一打开11组，新学术与新闻分组能切到正确类别，旧source-layer分层链接仍可用。核心筛选下点击仅有补充来源的分组会恢复全部来源，以确保目标表格可见。正式网址验证三类顺序，分别显示2/9/15条来源与2/4/5张表。发布前对照GitHub提交记录和镜像溯源，并核对37个产物文件一致。

## 三张总表发布 · v30（当前）

按用户纠正，撤销v29的11张分表。信息来源严格只有3张总表：热点资讯2个来源、学术界9个、产业界15个。11个二级分类保留为总表内部的行组，每张总表仅出现一次列标题。覆盖检查改为说明列表，不增加第4张隐藏表。

- GitHub内容提交：`346c3f651d83964c8e6bdf6e883555793e90a9dd`
- Sites镜像提交：`26ae6863b2a48de3ce17727ac6dd6bc4b68b69ab`
- Sites版本：30；部署`appgdep_6adb5ff5143c8191b045c18d4b692838`，`succeeded`
- 入口：https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/?v=30#sources

整仓构建与校验、22页模块结构和1548条内部链接通过。浏览器核对本地及正式网址：信息来源DOM恰好3张表、26行来源、11个表内行组；三类分别只有1张表。搜索元戎、空结果提示、核心筛选、昇腾生态筛选、表内分类跳转通过。手机仅表格内部横向滚动，页面未横向溢出。发布前逐字节核对38个生成文件与镜像一致，确认GitHub内容提交和镜像溯源对应。原有资料与访问范围保持不变，仍为人工维护与发布。
