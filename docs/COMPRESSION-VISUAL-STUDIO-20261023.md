# 专题视觉修订 · 2026-10-23

用户反馈上一版不够美观。这轮调整推理压缩专题阅读器，保留唯一内容源、原有事实、引用、分类和七章结构；不修改算子研究源，不发布公网。

## 实际变更

- `original-reader/site/business_insight/cloud_core/topic-studio.css`：仅在 `topic.html` 载入。正文采用浅色阅读区域，紫蓝点缀；移除连续深色封面、重复横向目录和全文外框，统一标题、来源和案例层级。窄屏保留横向目录样式与减少动态偏好。
- `topic-tensor.svg`：页首装饰性张量插画，不承载论文结果或压缩比例。
- `compression.js`：KV 量化原理图明确采用 KIVI 示例，画出 K 按通道、V 按 token 及高精度 residual。图形布局不表示真实分组大小或压缩率，scale/zero-point 开销仍需查正文。下方其他路线保持独立。
- 权重量化页去掉与研究速览重复的页首判断；将证据导航保留在速览内，不另占侧栏一章。

## 浏览器检查与迭代

- 实测视口为 845×1102 和 1280×720，不宣称完成手机验收。
- 首轮图示发现残留区与说明重叠、非激活文字过暗；已移开标注、提高所有阶段文字对比度并放大图中文字。
- 两轮独立视觉复核：最终首屏及机制图未发现必须修复的重叠、裁切或不可读问题；不等于用户已经接受视觉方案。
- 宽屏实际抽查：权重量化、权重低秩、知识蒸馏、KV紧凑架构，均为七章、无关闭的专题折叠、无文档水平溢出。
- 实点 KV 基本原理目录，正确到达分镜；已有播放、暂停、四步正文和来源引用继续保留。

## 校验

整站构建通过，最终 bundle 重建及阅读器构建通过；`verify.py`、`verify_original_reader.py`、`verify_expert_topics.py`、`test_topic_reader_five_rounds.cjs`、`test_expert_navigation.cjs` 均通过。最终阅读器为166个源文件，91张本地表和182项登记资源。

截图位于 `.tmp/compression-studio-hero-845.png`、`.tmp/compression-studio-mechanism-final.png`、`.tmp/compression-studio-weight-final.png`。未提交、未推送、未发布；没有增加论文全读、设备实测或性能达标声明。
