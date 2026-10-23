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

## 三张总表发布 · v30

按用户纠正，撤销v29的11张分表。信息来源严格只有3张总表：热点资讯2个来源、学术界9个、产业界15个。11个二级分类保留为总表内部的行组，每张总表仅出现一次列标题。覆盖检查改为说明列表，不增加第4张隐藏表。

- GitHub内容提交：`346c3f651d83964c8e6bdf6e883555793e90a9dd`
- Sites镜像提交：`26ae6863b2a48de3ce17727ac6dd6bc4b68b69ab`
- Sites版本：30；部署`appgdep_6adb5ff5143c8191b045c18d4b692838`，`succeeded`
- 入口：https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/?v=30#sources

整仓构建与校验、22页模块结构和1548条内部链接通过。浏览器核对本地及正式网址：信息来源DOM恰好3张表、26行来源、11个表内行组；三类分别只有1张表。搜索元戎、空结果提示、核心筛选、昇腾生态筛选、表内分类跳转通过。手机仅表格内部横向滚动，页面未横向溢出。发布前逐字节核对38个生成文件与镜像一致，确认GitHub内容提交和镜像溯源对应。原有资料与访问范围保持不变，仍为人工维护与发布。

## 专家研究阅读版 · v31

五段主线与三张来源总表保留。22页统一为深海军蓝目录／页首与浅色高对比正文；3个根技术补充SVG机制图，7个执行对象、4个决策专题明确输入输出、机制、对照与失效边界。19项资料收紧事实范围，分析页删除重复判断，关键继续／停止条件默认展开。完整内容与实读记录见 `AGENT-EXPERT-READING-QA.md` 及两份专项复核文档。

- GitHub内容提交：`1ebaa12618c6248b5ed71369acb39b503d5e75f3`
- Sites镜像提交：`ffbde3684675d28f5234d30c09a9a3606220e350`
- Sites版本：31；部署`appgdep_6adb6d4125788191add00d3d80d360b9`，`succeeded`
- 入口：https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/?v=31#map

整仓构建、整仓校验及22页／1491条模块内链接检查通过。桌面逐一打开21个子页；390px手机宽度逐页点击21个末级目录，均到达有正文的章节，五个主页面无页面横向溢出。咖啡4场景52状态与场景控制检查通过。正式网址核对新CSS哈希、机制SVG、6项专题目录、3份默认展开的路线条件、删除重复卡片、3张信源表及9个学术入口。发布前比对42个生成文件和主仓库溯源一致；访问范围及原网址不变。内容仍是人工维护的阅读快照，没有新增云核实测结论。

## 技术地图聚焦与原文深读 · v32

按专家的研究任务重排地图：研究对象与目标 → 三项根技术 → 控制变量的比较口径 → 重点论文深读。架构、完整指标、运行时基础、咖啡全景和应用索引作为可展开参考，保留原来的深链接。三根专题新增真实依赖图、时间线、路由代价和共卡干扰推演，同时说明竞争者代价及适用边界。

新增 Murakkab 独立深读页，包含六节目录、三张官方论文图表节选、原尺寸入口、实验条件与原文页码。示例假设、论文测量和研究判断分别标注；尚无云核实测。复用方法与具体整改见 [专家阅读审视](AGENT-MAP-EXPERT-REVIEW.md)。

- GitHub 内容提交：`d13242c08c9fdd8105d9f862de55a1489a8a0762`
- Sites 镜像提交：`b805e7c3fb08124e58611e00a3c5ff0bbbd96fb2`
- Sites 版本：`appgprj_6acf4d01d4a48191a167ab0a3ff7b192~appgver_79836fd0a0288191a0f2e0a47222e69f`（32）
- 部署：`appgdep_6adb7cd68a8881919f4c486472288cee`，`succeeded`
- 入口：https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/?v=32#map

整仓构建、整仓校验及 Agent 专项验证通过：23页、1553条模块内链接、19条证据关联、3张机制SVG和3张原图的字节一致性。本地实际点击五个主栏目、三根专题、深读目录及咖啡演示，检查桌面和390px手机宽度；图表截图另由独立审查者复核。本轮没有重新手动打开全部23页，全部页面链接由自动检查覆盖。正式域名实际验证新地图、深读目录和3张原图加载，控制台无错误；原网址与公开只读范围保留。

Windows 打包工具对中文输出路径报错，改用 ASCII 临时路径后官方打包器成功；发布包来自已推送的同一镜像提交。站点仍为人工维护快照，未增加自动采集或 TableGit 在线同步，也未证明首屏稳定低于两秒。


## 信息源到研究决策 · v33

保持原有五段主线与三根技术，信息来源仍严格三张总表，27来源按发布角色、执行层与研究方向分开管理。增加公开候选采集、日期去重、核查失败记录；本轮实际读取7个公开入口，得到64条关键词候选，60条仍待原文审阅。候选没有自动进入事实或自动发布。

新增6项核验资料：Temporal队列机制、Ray节点亲和、元戎会话机制、Temporal Go 1.50.0、Ray Serve 2.59.0、Strands Box工具准入。累计25项资料；原始发布日期、媒体日期与核验日期分开，本周4条精选未膨胀。新增亲和、公平和背压三项条件化判断。13/27来源已有核验链，包含媒体追溯；同一事件不重复计数。

- GitHub内容提交：`9a13a87424b24e7da3453dda9536805df0228630`
- Sites镜像提交：`7f59f393eced556a43dca9fbb855bf6a499269b3`
- Sites版本：`appgprj_6acf4d01d4a48191a167ab0a3ff7b192~appgver_cd9018e8c1dc8191861f1e50deb42ba7`（33）
- 部署：`appgdep_6adb9882e5308191ae4491c4bca93a17`，`succeeded`
- 入口：https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/?v=33#sources

验证：整仓构建及校验通过，Agent专项23页/1654条模块内部链接、25项证据关联、3张机制SVG与3张原图一致性通过；采集器5项测试通过，咖啡4场景52状态与场景控制通过。浏览器实际检查三类切换、方向/证据/生态筛选、搜索/空结果/重置、元戎核查与正文、三根专题新增依据、3项分析判断和归档；390px页面无横向溢出，640px表格在自身容器内滚动。此次没有重新手动打开全部23页，全部链接由专项检查覆盖。

发布前逐字节核对32个当前允许发布文件与镜像一致。正式网址核对27来源、3张表、6项新增资料和3项判断，实际点击学术类、产业分组、媒体追溯及元戎详情；控制台无错误。视觉采用深蓝导航、青色高亮和浅色正文，使用说明收起，保留可直接筛选的目录。十阶段整改见AGENT-SOURCE-DECISION-REVIEW.md。

沿用既有公开只读网址；主仓库和Sites依然人工同步。没有定时采集、自动全文核验或TableGit实时服务，未声称全量覆盖、昇腾实测收益或稳定两秒加载。未修改推理压缩内容和CCN首页导航。


## 全来源核验记录 · v34（当前）

27个持续来源逐项读取并形成结构化核验记录：21可读、6部分可读。部分可读保留原入口障碍、可读的官方替代材料、版本条件和复核动作。页面严格保持3张来源总表，新增具体核验发现、完整记录、记录直达链接、访问结果筛选及复核工作单。新增来源缺少记录会使构建失败。

入口核查与内容入库分开；25项资料、13/27来源的研究依据链、60条待审机器候选不因核验入口而膨胀。归档增加本轮核验范围。规范与独立复审记录见 AGENT-VERIFICATION-STANDARD.md。

- GitHub 内容提交：`e1bdfbf67b72cab0c12aab980d4659ce62e617dc`
- Sites 镜像提交：`fc214b49b1091fdac6aa1634cf6f642edc65b2f5`
- Sites 版本：`appgprj_6acf4d01d4a48191a167ab0a3ff7b192~appgver_7c8f446193d48191bbadbbe4e45be884`（34）
- 部署：`appgdep_6adb9e8503688191aee44ddfe2e6db89`，`succeeded`
- 入口：https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/?v=34#sources

整仓构建与校验通过；最终Agent专项23页/1688条内部链接、25项证据关联及图像一致性通过。本地逐条展开27个核验记录，三类切换、读取筛选、空结果、机制关键词搜索、MindIE记录深链接和390px布局通过。没有重新手动点击全部23个研究子页。正式网址验证27条记录、3张表、21/6读取统计，实际打开产业部分可读筛选与MindIE完整记录，控制台无错误。

发布前逐字节核对32个当前允许发布文件；镜像保留既有旧哈希资源以兼容已缓存页面。原有网址及公开只读访问范围不变，未增加后台自动采集、自动全文核验或自动复核提醒。仅Agent模块发布；未改推理压缩内容或CCN首页。
