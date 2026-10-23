# 第五轮独立复核：实际剩余缺陷

2026-10-23。只读检查当前维护源、renderer、CSS/JS 和生成的 13 个活跃阅读页，并运行 `python -X utf8 scripts/verify_operator_research.py`。未修改产品或脚本；本报告不代表浏览器视觉验收通过，未执行设备实验。

验证结果：**PASS**。当前约束覆盖 9 份研究 JSON、13 页、9 机制、独立研究取舍与证据分类、5 个具名生成系统/12 条证据，以及内部 310P 报告不出现在前台。

本轮只保留下面两项可由现有源码或生成 DOM 确认的剩余问题。

## 1. 两个分支页侧栏目录仍保留旧顺序，与新正文顺序相反

**位置**：`operator_research_site.py` 分支页 `outline` 构造；生成页 `operators-1.html`、`operators-2.html`。

正文已改为“机制差异 → 技术路线（包含具体 route 文章）→ Add/通信机制讲解”，但目录仍先列 `principles` 和案例小节，再列 `route-*`。因此读者按目录向下阅读，点击具体机制会跳回案例之前。阅读高亮虽然已能识别嵌套目标，却会在目录上向下、再向上跳，层级仍不符合正文。

计算页当前目录局部顺序：

`#comparison → #routes → #principles → #cannbot-concepts → #cannbot-judgments → #cannbot-fusion → #route-memory-reuse → …`

正文实际顺序：

`#comparison → #routes → #route-memory-reuse → … → #principles → #cannbot-concepts → #cannbot-judgments → #cannbot-fusion`

通信页同样将 5 个 `#route-*` 排在 `#principles` 之后，而这些文章已在正文前面。

**建议**：把 route 子条目紧跟 `#routes`，再放 `#principles` 与案例子条目。无需改变正文或锚点。

**验收**：目录中同层与子层链接的目标 DOM 顺序整体不倒退；对应章节高亮、点击和向上滚动都保留。可用目录目标在 `main` 中的节点序号检查，无需依赖截图像素。

## 2. 系统减少动态效果时，“播放动效”按钮的状态与实际动画不一致

**位置**：`content/operators-research.js` 的 motion handler；CSS 的 `@media(prefers-reduced-motion:reduce)`。

脚本在系统偏好为 reduce 时将 `paused=true`，显示“播放动效”。用户点击后，脚本会移除 `op-motion-paused`、改成“暂停动效”、设置 `aria-pressed=false`。但 CSS 仍以媒体查询和 `animation:none!important` 强制停止所有动画。因此按钮宣告已经播放，实际仍未播放。

这是在该偏好设置下由脚本状态与 CSS 规则直接构成的不一致；本轮没有声称已用浏览器或辅助技术实测。

**建议二选一**：尊重系统偏好并将控件明确标为“已遵循系统减少动态效果”，不提供无效播放；或允许明确点击后的用户选择覆盖默认偏好，同时让按钮状态、类名和实际动画保持一致。不要只更新按钮文字。

**验收**：分别在 reduce 与 no-preference 环境下检查初始、点击暂停、点击播放后的可见文案/`aria-pressed`/动画实际 computed 状态；静态文字与机制图始终可读。切换系统偏好后也应明确采用固定初始值还是实时跟随。

---

上一轮其余重点未再次列为缺陷：机制目录已先于 Add；具名搜索已能命中所查七个词；嵌套目录观察目标已扩展；route hook 已指向完整案例；比较表缺失的 `data-label` 已补齐；所有检查到的角标均有返回链接；九机制均有独立研究取舍。窄屏排版、SVG 实际字号与控件遮挡仍以主任务浏览器验收为准，不因结构 PASS 自动视为视觉通过。
