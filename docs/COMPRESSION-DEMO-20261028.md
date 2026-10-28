# 推理压缩展示与统一入口 · 2026-10-28

本轮使用仓库 ccn-insight-build、ccn-evidence-review 和 Sites 发布流程。保留原有十月报告资产、论文指标与 16 专题正文，没有重新制作 PPT，也没有新增设备实验。

## 阅读体验

报告首屏从当前采用报告的 canonical 摘要提取判断，随后展示三项论文选择的研究价值、继续条件和原文入口。卡片改为横向分栏条目，小屏自动纵向排列；报告正文、研究入口与详细论证可直接抵达。摘要和侧栏章号不再重复。技术地图去掉重复的 KV Cache 标签。

实点发现并修复两项时序问题：栏目切换不再沿用上一栏的滚动位置；后续证据加载不再把同一版本的研究判断覆盖成“报告摘要”。新月份、范围、语言或版本不会沿用旧判断。相关回归加入 test_reader_journey.cjs。

手机端原先一组较长的文献角标不换行，将权重量化页撑至 512px；现在角标组允许换行。固定页头的锚点间距按小屏调整。390px 实测下，报告、权重和 KV 量化页的文档宽度为 375px，没有整页横向溢出；大表格保持组件内部横向滚动。

## 验收范围

16 专题逐一在浏览器打开：七章正文均加载，无主内容关闭折叠、可见错误提示或桌面横向溢出。逐页记录在 compression-topics-browser-qa-20261028.json。这是加载与结构验收，不是对全部论文重新作全文审阅。

报告执行下一页、跳到第 4 页、放大、150% 缩放、技术原图与 Esc 退出。第 4 页技术原图加载成功，原始宽度 1921px。热点搜索及重置、产业生态筛选及重置通过；热点筛选未改变学术表。报告正文锚点最终位于桌面约 85px、手机约 180px，未被固定页头遮挡。

本次通过：整站构建、verify.py、verify_original_reader.py、verify_compression.py、verify_source_records.py、test_research_map.cjs、test_report_reasoning.cjs、test_reader_journey.cjs、test_compression_entry.cjs。发布后另记录公网验收；这些检查不等于已实现两秒首屏或本地昇腾收益。

## 原站候选与阻挡

原站候选 Topic：be5431cf-c315-4222-869c-1e6b94ca357b，当前候选提交 a74282fe3a94b066007883a6e1d4192d9c3294c0，未发布。推理压缩五入口与两个共享跳转文件仅作为候选；正文与数据仍由 CCN 单一维护。

用户明确授权的范围外必要修复只有：

1. conference_insights/ocp_2026/workbench.html 的 Shell 脚本版本由 v20 改为全站配置要求的 v18；会议正文不改。
2. academic_resources/scripts/test_lri_tablegit_provider.mjs 的四个模拟响应补 matched_count 3、3、0、1；运行代码和真实数据不改。

614 页样式与 Shell 覆盖检查、31 项任务阅读测试、65 表 provider 测试及学术资源静态边界检查通过。完整 validate-insight.sh 随后仍失败：`TableGit provider missing topic guard: function loadTopicWorkbench(topicId)`。未改动该额外校验或运行函数，也未绕过完整检查发布。主线原有版本上已单独复现此前的 matched_count 失败，说明它不是统一入口引入的回归。

用户禁止上传的私人校验数据没有传输。较宽目录写入曾被自动审批拒绝；随后只使用明确授权的具体文件范围处理，没有扩大目录权限。原站其他业务模块与 Agent 均保持线上状态。

## 明日展示建议

从 CCN 的“洞察报告”进入：先讲研究判断与三项选择，再打开报告第 4 页说明 AlignQuant 的方法、所测配置、TTFT 退化和 TPOT/显存收益；接着从“技术地图”打开权重量化或 KV 量化，展示路线比较及原文证据；最后回到研究取舍与验证条件。

报告材料和证据复核有各自日期，不描述为已覆盖至今日的全部新论文。论文结果、编辑建议与尚未执行的业务实验分开陈述。模型和卡型示例不等于已支持；950 的具体型号仍待确认。
