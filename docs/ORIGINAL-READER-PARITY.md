# 推理压缩原样迁移

2026-10-22 修正：之前的 compression-migration 阅读页重新组织了版式，不是原样迁移。该阅读页保留为辅助数据审阅，不再作为默认预览或双站交付入口。

## 默认入口

- 本地原样阅读：http://127.0.0.1:8784/business_insight/cloud_core/index.html#view-topics
- 维护台：http://127.0.0.1:8785/ ，预览链接也指向同一套原版界面。
- 原公开站与 CCN 公开站均未修改；没有推送本批文件。

## 保留的内容

原站当前 works 提交 `f05a5be81551fdfc98065080d08414121c70eacc` 中的 162 个页面、CSS、JS、JSON、SVG 文件存于 original-reader/site/。默认构建直接复制这些文件，仅在 HTML 中插入一条 local-content-adapter.js 的加载语句，不重写正文、导航、组件、布局或动画代码。

运行 scripts/verify_original_reader.py 会检查构建后的原版文件：HTML 去除该加载语句后，与存档完全一致；其他文件逐字节一致。

浏览器对照结果存于 docs/original-topic-parity.json：16 个专题在异步产业资料、代表技术与原文比较加载完成后，正文与原站一致。技术地图正文也已对照一致。此检查归一化空白字符，不等于所有浏览器上的逐像素截图一致。

## 本地数据读取

content/original-content-adapter.js 仅替换本页对 /mcp 的读取，使用同站 local-content/ 静态 JSON，不转发至远程 TableGit，不提供写入功能。原版读程序的三种固定关联读取计划由本地适配实现，其他任意查询不受支持。

源码仍可能显示原程序中的 TableGit 文案；保留该文案不表示运行时连接原服务。读取数据由 build_original_reader.py 从唯一维护源 data/compression/ 生成。大表另按键分片，避免专题为几十条引用读取整个来源库。

为运行原版界面，另迁入11张范围限定的配置／工作台支持表、63条记录。现在共有91张表、63,873条记录；原有80张研究相关表未改写业务事实，原有182个报告附件校验保持通过。

## 构建与两站交付

python scripts/build.py 包含原版阅读器生成；python scripts/stage_compression.py 生成双站原版静态模块。两个输出都使用 /business_insight/cloud_core/ 和 /assets/ 的原有路径，保留原站的 topic.html?topic=…、#view-topics 等深链接。

构建收据 data/compression/staged-release.json 的 renderer 为 original-reader。该模块是待发布文件，不是已上线状态。原站与 CCN 的正式发布与入口接入仍须用户明确确认。

维护台仍是唯一编辑入口；不要修改 original-reader/site/ 中的业务文案，正文应在 data/compression/tables/ 中维护。若确需调整交互或外观，可修改阅读器源码，但应明确记录与原站版式的差异。
