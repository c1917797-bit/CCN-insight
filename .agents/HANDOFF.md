## 线上发布源码服务故障已复核（2026-10-29）

用户要求完成线上更新。本轮确认账号为owner，站点public且最新已保存版本仍v22；GitHub主仓2da0546与远端一致，待发布2264个静态文件与已推送内容4f5cb35逐文件哈希一致。新凭据、官方打开流程、独立HTTP客户端均复现源码服务500；只读git-upload-pack / git-receive-pack握手错误请求编号a5216332a87ddbc9-FRA、a52163407f0e0db6-FRA。不是代码构建阶段的报错。

未伪造已推送SHA、未用旧源码SHA绑定新归档、未开始部署，现网仍保持v22。完整证据deployment/online-publish-diagnostics-20261029.json；待发布镜像本地0039c32与此前内容保留，服务恢复后核对远端再继续官方发布。凭据只在内存，不写Git或日志。

## 排序与来源页宽屏修订待上线（2026-10-29）

最新内容4f5cb35已推送：芯片表顺序910B/950PR/950DT/310P；技术进展先学术再业界（含格式对照表列顺序）；研究背景先芯片格式与算力、再研究范围、再容量收益。来源页宽屏双重居中已修复，1920宽浏览器实测左侧310px→32px；仅在云核无左目录的report页面解除Shell限宽，其他专题目录保留。构建与导航检查通过。

最新Sites镜像本地0039c32，远端仍2e147fd；官方推送依旧HTTP500，没有保存或部署未推送提交，现网仍v22。详见deployment/order-layout-publication-20261029.json。此前月度整理也包含于当前构建，后续从最新GitHub构建并统一发布，不能拿旧镜像覆盖新内容。

## 本期动态与芯片算力修订待上线（2026-10-29）

本期动态按本月速览、学术、产业、热点、补充资料重组；旧产业能力与本月发布分开，删除多专题重复正文，月度筛选不再途经地图启动器，论文冷加载不再显示无关摘要。权重量化两列硬件表补齐官网算力，950采用白皮书表3-1的Cube口径。主仓内容提交6822fdd已推送并通过检查、浏览器筛选归零/恢复及两列表验收。

Sites发布未完成：官方Git接收连续HTTP500，镜像本地60a4c2e尚未确认远端，重开读取的FETCH_HEAD仍为v22源2e147fd。没有保存或部署不匹配版本，现网仍v22。详见deployment/monthly-formats-publication-20261029.json。继续使用同一项目、同一镜像核对后续推送，禁止误称已上线。隔离本地预览端口8793为用户审阅暂留；若不再需要可停止此端口的自建Python服务。

# CCN 维护交接 · 2026-10-23

## CCN v19 门户标记已发布（2026-10-25）

推理压缩与算子统一使用data-research-status=detailed黄色标记；仅表示已有专题洞察。两个算子入口都为“查看专题洞察”，其他四类未升级。内容提交36439f43d9e221dbb90e0cf5a6d6e1e804e594e3、Sites源a772229975cfb5176c123834a228e50e2d0fb420，v19部署appgdep_6addcc5f9a688191b989f29fdb52ce75 succeeded。线上实际颜色完全一致，两入口进入对应七章专题。回执deployment/ccn-publication.json、docs/ccn-v19-atlas-qa-20261025.json；原TableGit未变。仍从隔离发布副本维护，保留共享旧工作目录未提交内容。


## CCN v18 已发布（2026-10-25）

用户授权更新Git并发布CCN；内容提交84acb546f3eba381ae219a4fa9b92e2411f8bd85已推送GitHub，官方Sites源b82f3e42a512cecdbd610b8c9687810a7ee6e4c1、v18部署appgdep_6addaaf920448191aada6aaa2113b3c0 succeeded。线上五栏目和十二专题、四项速览、共享CSS、锚点及筛选/检索实测通过；记录docs/ccn-v18-online-qa-20261025.json。以最新v17为基线选择合并，保留来源核对记录分离与Agent改动。原TableGit未变。共享主工作目录保留旧HEAD和未提交改动，不能拿它整体覆盖远端；发布使用local-releases/ccn-public-20261023隔离副本。回执deployment/ccn-publication.json。


## 算子专题格式发布准备（2026-10-25）

用户已授权更新Git并发布CCN。本次在最新main上选择性合入算子五栏目、十二专题七章、四项速览、证据导航/待读/检索及共用topic-studio.css；完整保留v17来源记录分离及Agent改动。维护入口和桌面验收见docs/OPERATOR-COMPRESSION-FORMAT-20261025.md和docs/OPERATOR-TOPIC-SHARED-FORMAT-20261025.md。部署结果以deployment/ccn-publication.json与后续发布回执为准，原TableGit不改。


## 当前状态

工作目录为CCN-insight，分支main，存在大量历史及本轮未提交改动；不能把工作树等同于已合入、已推送或已发布。用户要求当前迭代本地审阅。原站保留，未经新授权不发布。

## 已完成与入口

- 推理压缩平台继续全范围改造：见 `docs/COMPRESSION-EXPERT-PLATFORM-20261023.md`。16专题有三项判断/两项具体对照；15份挑战矩阵；8条空缺路线与17条同源案例绑定补齐。当前209卡、482有效引用、36路线、198索引条目。新增/复核材料为指定章节，未全量全文审阅；旧论证不相干/重复引用已软删除重绑。三表类型筛选、地图知识状态与30案例快捷入口、动态事实直显、报告三选择/六论证/紧凑原文索引、六版归档、基础速查均接通。浏览器记录在 `docs/compression-platform-browser-qa-20261023.json`；桌面截图独立复核。报告旧二维grid和点击冒泡重置已修复。PPT文件未重制，未推送/发布/回写原站。内容版本 `compression-6c9aee3faaebb982df29`，读取修订 `1f67815ded0b9185a001daad3270625b6af28073`。新回归 `test_compression_depth.cjs` / `test_report_archive.cjs` / `test_foundations_quickref.cjs`；`refine_reader_copy.rebuild()`现同时重建基础课bundle。后续仍先核对实际服务8787是否运行。

- 用户认为深色版不美观，本轮另做专题视觉修订：`topic-studio.css` 仅接入 `topic.html`，浅色阅读、紫蓝点缀、张量页首插画，取消正文与侧栏重复目录；权重页不再重复显示页首判断，并统一七章目录。KV 量化分镜明确标为 KIVI 示例，图示逐通道 K、逐 token V 与高精度 residual，未将 QJL 等路线拼接为一套流程。见 `docs/COMPRESSION-VISUAL-STUDIO-20261023.md`。仍仅本地、未推送或发布，视觉方向尚待用户反馈。
- 追加五轮推理压缩专题打磨（不是算子页）：`docs/COMPRESSION-FIVE-ROUNDS-20261023.md`。当前190卡、443引用、179个可定位检索条目。四张案例/工程卡由指定原文补强；DeltaLog作为状态写回的关联边界进入紧凑架构，没有归为量化或新架构。
- 论文盘点：16,148个按编号/链接去重的论文标识，含异常及尚未确认压缩相关记录；38篇有阅读摘要，61篇被专题引用（34含指定章节核对、27仅摘要）。这些来自不同维护记录，不是严格递减漏斗。不能说上万篇已吸收或全文读完。`scripts/audit_compression_inventory.py` 随reader构建输出公共汇总，完整本地审计见docs。
- 已有四步资料的11个通用专题增加SVG分镜，四步文字同时展示，带播放/暂停与步骤切换，尊重减少动态偏好。4个construction专题没有编造steps；权重量化继续使用共享基础课。深蓝/青色页首、清晰来源条、同页跳转及紧凑方法索引已接入。仍仅本地，未提交/推送/发布。
- 推理压缩唯一内容源：`data/compression/tables/`；阅读器：`original-reader/site/business_insight/cloud_core/`。
- 信息来源三张独立表，各自搜索/筛选，同主体多入口归一行。
- 16专题增加研究速览、证据导航与本浏览器待读；10条跨来源Flint定位修正。详见 `docs/EXPERT-QUALITY-20261023.md`。
- 仓库级skill入口：`.agents/skills.registry.json`，构筑/证据/经验三项。新领域模板和经验生命周期已加入，不需要复制个人skill库。
- 三条实践经验目前为proposed；自动验证不等于维护者接受。
- 技术地图新增跨16专题的资料检索，178条可定位资料；来源审阅范围、待读与打开后修订语义独立。索引由 `scripts/build_expert_index.py` 构建，不是编辑源。
- 洞察报告逐篇列出当前v6的三篇条件优先论文，六条论证及三份建议实验直接展示。保留原PPT与其他入选研究，不把借鉴技能记作已重做PPT。
- 方法借鉴与实际执行记录在 `docs/MOZHI-PRACTICES-20261023.md`、`.agents/skill-provenance.json`；网站Report与可编辑PPT的工具策略写入构筑skill参考。

## 证据与限制

逐页浏览器记录：`docs/expert-topics-browser-qa-20261023.json`。16页的速览、七章与案例锚点已检查；保存、刷新保持、筛选、直达已操作。移动视口请求未实际生效，因此移动端未验收。来源包为摘要级复核，不代表全文复现。全量189张卡片仍需要逐来源持续审阅。

新增 `docs/expert-library-browser-qa-20261023.json` 记录178个索引锚点及16个专题案例的实际滚动位置；节点存在不能代替定位验收。189张canonical卡片中11张未被当前阅读器渲染，索引明确排除并记录。已修复通用专题卡片hash未滚动和连续视图切换后检索入口缺失。内容修订筛选不是发表监测，未通过虚构未来版本作浏览器演示。

本轮最终整站构建与关联校验通过；原阅读器164个源文件、91张本地表及182个已登记资源一致。报告冷深链采用有界两帧恢复，避免shell布局完成前定位；实际标题最终距视口顶部85px。原文链接增大并换行，最终检索/报告截图经独立复核。截图在 `.tmp/expert-{library,report}-20261023.png`；未提交、未推送、未发布。

## 接手与下一步

先读AGENTS和注册表，运行 `git status --short --branch`，辨认并保留其他工作，尤其算子专题。按任务读取窄skill；新极稳课题先确定挑战与路线，使用insight_topic脚手架生成草稿，不继承压缩分类。

可在授权范围内继续补全文证据与移动端验收。候选经验验证后，待真实维护者决策再采用；不得伪造reviewed_by。不要重跑旧日期化润色脚本覆盖现有内容。

## 验证与恢复

```text
python -X utf8 scripts/validate_insight_skills.py
python -X utf8 scripts/insight_topic.py self-test
python -X utf8 scripts/test_insight_workbench.py
python -X utf8 scripts/insight_learning.py validate
python -X utf8 scripts/verify_expert_topics.py
python -X utf8 scripts/verify_expert_index.py --self-test
python -X utf8 scripts/audit_compression_inventory.py --self-test
node scripts/test_topic_reader_five_rounds.cjs
node scripts/test_report_reasoning.cjs
node scripts/test_expert_navigation.cjs
```

页面维护源改动后按build skill中的bundle/build/verify流程重建。预览端口8787需先确认仍监听；服务终止不能以缓存页面作为最新验收依据。单纯本地http.server不提供维护与发布API。Git推送与公开部署均未执行。


## 算子五轮迭代（2026-10-23）

算子13页本地完成五轮内容/证据/判断/视觉/实点验收，详见 `docs/OPERATOR-FIVE-ROUNDS-20261023.md`。新增维护源 `research/ai-infra/operator-expert-guide.json`，source累计67项、机制证据33条，代码生成仍为横向方法。保留计算/通信两分支，不导入旧expert快照覆盖当前正文。CSS/JS已按内容散列版本；浏览器旧资源缓存曾影响初检，最终复查已确认新版本。整站构建及原阅读器/压缩/地图验证通过；后续算子增量构建也通过。未推送、未发布、未改原站、未执行设备实验。当前可用预览8787，重新接手仍需确认服务。

## 算子平台结构与证据检索（2026-10-23）

13页本地结构更新完成，详见 docs/OPERATOR-PLATFORM-20261023.md。新增维护源 operator-research-structure.json、operator-judgment-log.json；派生索引 operator-evidence-index.json 只由构建生成。45条事实单源维护，20做法入口、27角色条目、五项真实编辑修订。各机制四主章，旧锚点保留为H3；生成仍是横向方法。浏览器13页、20做法实点、五判断回链、筛选/重置/刷新、390/1440排版已验收，记录 operator-platform-browser-qa-20261023.json。

两项算子验证均PASS。完整构建已运行；门户和技术地图PASS。压缩兼容渲染新增challenges/industry两类已有卡片，曾通过209卡片/617引用校验；随后并行内容编辑使最新全站校验再次不一致（原阅读器content_version、parameters-factorization__dossier_2正文）。不得覆盖其他任务的维护源，也不得声称最新全站已验收。待并行编辑稳定后完整重建复核。未提交、未推送、未发布、未改变原站、未运行设备实验。

## CCN v13 已发布（2026-10-23）
用户明确授权发布。GitHub 内容提交 a7a2dfcb55876afa91dbbe921a2a74a08a5757c3，Sites v13 部署 succeeded。回执 deployment/ccn-publication.json；线上实测 docs/ccn-v13-online-qa-20261023.json。公开站九机制、20做法、45记录、五修订及 INT4/GPU 检索、原始记录直达已核实；原站保持不变。
为避免干扰并行编辑，本次从 local-releases/ccn-public-20261023 隔离副本基于最新 origin/main 构建和推送，保留远端 Agent 提交。共享工作区的旧 HEAD 与未提交改动未重置；后续先比较远端和现有工作，勿以旧 HEAD 覆盖 main。


## CCN 公开发布 · v14

用户已授权本次发布。GitHub 内容提交 `0b5c0d8d478bdebedc483267ddc216762f1c191f`；Sites 源码 `e7b46894c0e5bb568e4fd61d416e096eef24c2f5`；v14 部署 `appgdep_6adba809a1c48191b25bcb8040e126b9` 已成功。公开网址保持不变，原 TableGit 站点未修改。发布回执在 `deployment/ccn-publication.json`，线上验收在 `docs/ccn-v14-online-qa-20261023.json`。统一文本换行后内容版本为 `compression-0c13ebb37577a4899c82`。原主工作目录的未提交内容被保留，发布通过独立 worktree 完成，不要直接重置原工作目录。

## CCN v14 核验完成（2026-10-23）
本轮已将新增报告布局和审阅记录合并入 GitHub main，整合提交 e6058b4。官方 Sites 状态确认并行发布的 v14 succeeded，版本源码 e7b46894c0e5bb568e4fd61d416e096eef24c2f5，故未重复部署。线上三张研究选择和三条原始文献标题均实测 display:block、宽度等于标题容器，记录 docs/ccn-v14-online-qa-20261023.json。回执区分独立验证的 GitHub 整合提交和实际 Sites 版本来源，不声称生成缓存标签逐字节相同。
CCN-insight-site 保存未推送的镜像提交 4727fe9，远端已由并行流程推进到 e7b4689。保留本地提交，不强推或重置；后续请用官方 source helper 在干净目录打开当前源码，或按合并规则处理分歧。共享主工作区仍保留旧HEAD和并行未提交改动。原站未改动。


## CCN v15 阅读链路已修复并发布

用户要求修复点击与阅读主线。基于最新 main 的隔离 worktree `ccn-navigation-20261023` 完成；未重置旧 CCN-insight 工作目录。GitHub 内容提交 `1f2915f81f4adcd5a9c5d0e3e709d7551b084d5d`，Sites 源码 `bfd0f6f5ae023df05fe271f7e4407b5898202849`，v15 部署 `appgdep_6adbbe38ab9c8191a95e5d8dccf91c14` succeeded。

主栏目跨页、HTML/clean URL识别、并排目录高亮、七章编号、整张方法卡片锚点、五类进展子目录与原理返回上下文已修复。首页AI Infra使用本站相对路径，总地图导航明确压缩范围。`scripts/test_reader_journey.cjs` 已加入CI。rebuild现统一刷新内联启动脚本及shell/CSS散列并以LF写入，勿运行旧日期化文案脚本覆盖现有内容。详见 `docs/READER-JOURNEY-REPAIR-20261023.md` 与 `docs/reader-journey-online-qa-20261023.json`。数据仍为209卡/482引用，PPT与原TableGit未改。移动视口和2秒目标未实测；本次自首页实点到课题、AWQ、动态、报告、原理返回和刷新。

## CCN v16 信息来源目录优化（2026-10-25）

用户要求优化来源表格外观。本轮使用隔离 worktree ccn-sources-20261025，保留主工作目录和其他任务。GitHub 内容提交 d91397dd42dd01f1757fd6aa91cc4a5050f585c3，Sites 源码 cf2c82ade1fd30d359b866411d0acaa3cc5cad2c；v16 部署 appgdep_6adda14abd108191a5dc6c50728d27c6 succeeded。回执 deployment/ccn-publication.json。

保留热点/产业/学术三张独立表，来源和链接合列，定位与关注点分列；产业生态仍独立。新增每表重置、字号和宽度优化、紧凑顶部及响应式样式。正文和链接保留，核对记录仍可见。样式源 source-directory.css 通过 refine_reader_copy.rebuild 刷新散列，仅主入口加载；不要运行旧日期化 main。

Chrome 首轮实点搜索、重置、核心/全部来源均通过，另两表筛选未受影响。最终放大字号与收紧顶部后，Computer Use 刷新时因无法确认网址而停止；未继续浏览器操作。最终线上视觉、移动端和产业生态/类型筛选尚未实点复核，不得声称全页视觉验收。构建、verify.py、verify_original_reader.py、verify_compression.py、test_reader_scan_integrity.cjs、test_reader_journey.cjs及JS语法检查通过。详细边界见 docs/source-directory-qa-20261025.json。

推送前已合并远端最新 Agent v35 相关修改，保留其发布文件；本轮未改原 TableGit。官方 Sites helper 已完成提交/推送/远端HEAD校验，但本机打包仍报无详情错误，使用校验后的 manifest+dist tar 包完成保存与发布。仅使用 source-origin.json 记录主源，凭据未落盘。

## CCN v17 核对记录移出来源正文（2026-10-25）

用户批准按建议移走来源页大块核对卡片。renderChannels不再生成source-register-notes；sourceRecordHref保留month/scope/lang，旧source-review与source-paper-entries锚点跳转到source-records.html对应记录。完整21条核对记录与17条文献入口从同一canonical表源派生，由scripts/build_source_records.py随原阅读器构建生成，不建立第二可编辑源，不把日志直接当成动态或技术结论。核对日期及小记录链接仍在来源表。verify_source_records.py已加入CI，检查记录文字、原始链接和记录锚点完整；整站/原阅读器/阅读链校验和旧链接VM检查通过。

CCN v17部署appgdep_6adda62f8ae8819194fe435df8fa39f1 succeeded；GitHub内容0be38e919de94044e306d08087b50070a13bf671，Sites源e09ba9d533e7483fca9b69d38401a32f09ce1977。回执deployment/ccn-publication.json，详情docs/SOURCE-RECORDS-SEPARATION-20261025.md。原站未改。本机记录页HTTP200；Computer Use导航时再次因无法确认网址而中断，未继续浏览器操作，视觉与实点待复核。本轮预览29336已核对命令行并关闭。


## CCN v21：推理压缩展示与统一入口候选（2026-10-28）

CCN v21 已公开发布，GitHub 内容提交 912bb417705b4ab449261dfca10922b76baaceb9，Sites 源 cc29009eaf7116d15c9e0e66f9c30875a7e326a7，部署 appgdep_6ae2597abadc8191950c871ede107fb1 succeeded。回执 deployment/ccn-publication.json，公网记录 docs/ccn-v21-online-qa-20261028.json。报告首屏、三项论文选择、栏目滚动复位、异步标题与中英文摘要、手机角标换行和锚点遮挡已修复。16 专题逐页加载/结构通过；未重新审阅全部论文事实、未重做 PPT、未运行设备实验。浏览器实际下载的 PPTX SHA 与登记一致。

原站仍未切换，不得声称两个公网入口已共源。统一入口配置 deployment/compression-entry.json、生成 scripts/build_original_entry.py；原站候选 Topic be5431cf-c315-4222-869c-1e6b94ca357b，候选修订 a74282fe3a94b066007883a6e1d4192d9c3294c0。两项额外修复分别得到用户明确授权：OCP 单处 Shell 引用、provider 测试四处模拟响应 matched_count。完整全局检查之后仍失败于旧 topic guard 签名检查，未扩大范围或绕过发布门槛；禁止上传私人校验数据仍有效。详见 docs/COMPRESSION-DEMO-20261028.md、docs/COMPRESSION-SOURCE.md。下一次继续必须先读这些记录，保留原站现状。

Sites 的 source 参数是官方工具此前打开仓库的结果，不是将要部署的提交；工具会 saveSource 后返回新的镜像 SHA。曾因基准 SHA 被自动审批误判，检查官方代码和镜像逐文件哈希后同一官方流程获准继续。最终只部署新返回的保存版本，不用 GitHub 的 SHA 替换不同仓库的镜像 SHA。


## 两个入口线上共源已完成（2026-10-29）

用户明确批准：仅发布七个推理压缩入口文件，接受已说明的原站既有全库校验失败，其他栏目不改。原站 works 基于最新 main 137a198（保留另一维护者的会议栏目更新）通过原生、精确路径和 revision fence 应用七文件；发布提交 09f4807303bf872a3f0dd05442f9e45f6ce284a0，归档落点修正 c85a4ef4c8f0d6400821c17b402eb69b6a29850c。随后另一维护者新增 Topic 元数据使 main 前进到 388da58；原生同步检查确认本地/远端一致且干净，七文件内容仍匹配。未强推、未修改全局校验或权限、未上传私人 TableGit 数据。

两个网站首页地址保持不变；原站的推理压缩入口转到 CCN 唯一阅读器。实际 c1b3ie6ayp URL 的来源页（有/无 month/scope）、AWQ 案例、月度证据、基础原理和当前报告均已在浏览器验证；旧 archive.html 最初落到未迁移完整的资料库，现已在同一七文件范围内改为 index.html#view-reports 并实测当前报告/历史版本可见。旧 CCN archive 资料库本身没有在本轮迁移，不要误报已修好该独立旧页。

唯一维护源仍是本仓 data/compression/tables 与 original-reader/site；构建并发布 CCN 一次后两个入口复用同一内容，不再复制正文到旧 TableGit。原站入口配置 deployment/compression-entry.json（archive 映射在 routes），生成器 scripts/build_original_entry.py，回归 scripts/test_compression_entry.cjs。不要把生成的原站入口安装进 CCN dist。CCN 阅读器仍为 v21，本轮不需要重发同一阅读器。回执 deployment/compression-shared-entry-publication.json；浏览器记录 docs/shared-compression-entry-online-qa-20261029.json。

旧 Topic be5431cf-c315-4222-869c-1e6b94ca357b 已仅为清理未提交反向改动而保存为 436e1469f72cdf3b93ace12ed67fc27f48fa5d6c；没有发布这个旧分支，后续禁止误用它覆盖当前 main。上述已发布状态优先于下方/此前“尚未共源”的历史记录。
