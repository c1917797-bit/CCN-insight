# CCN 维护交接 · 2026-10-23

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
