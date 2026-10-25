# 信息来源目录优化

本轮仅改 CCN 阅读器的来源目录展示，不修改原 TableGit 站点、论文事实或报告文件。

- 热点资讯、产业界、学术界保留三张独立表，分别搜索、选择来源类型和核心/全部范围；产业表保留生态。
- 来源名称、原始入口放在同一列，定位与跟踪重点分列。完整说明保留，核对记录移至表后独立区域。
- 收紧页首说明和工具栏，限制正文宽度，放大来源名与正文；移动布局以带列名的分块展示。
- 新增每表独立重置筛选，默认状态禁用重置；保留原来源链接与核对日期口径。
- 新增 source-directory.css，主入口按内容散列加载，样式只作用于来源目录。

维护入口：original-reader/site/business_insight/cloud_core/compression.js、source-directory.css、index.html。改后调用 refine_reader_copy.rebuild()，不要运行旧日期化 main()；随后 build.py。

Chrome 实点已验证首轮的搜索、重置和核心/全部范围切换。最终字号与顶部收紧后，浏览器工具因无法确定网址停止；未再执行浏览器操作。最终视觉与移动端尚未复核。详细边界见 source-directory-qa-20261025.json。
