# 算子专题专家阅读优化

范围：算子总览、计算与通信分支、九项机制专题、310P工程实践，共13页。只更新本地预览，不推送或发布。

## 本轮使用的技能方法

- `deep-research`：采用fact-check模式，按已经明确的范围核对具体机制、实验条件与证据，不启动需要重新定义问题的完整研究管线。
- `sites`：复用本地源码与预览，按阅读目的组织页面，完成实际浏览器验收；保留用户的local-only限制。
- 图示直接使用代码维护的SVG，与现有网页构建衔接。没有把演示文稿生成技能或图片生成技能强行用于网页代码。

## 内容改动

九项机制补齐27个具名技术分支和29条结构化证据卡，来源库共41项原始论文或官方资料。每条证据分别记录做法、日期、适用/实验条件、原材料报告的结果、外推限制与出处。产业实现在前，学术研究在后。

计算侧包括FlashAttention 1/2/3/4、CATLASS、CANN具体算子、FlexAttention、Ansor与TensorIR。通信侧包括NCCL算法/分组/缓冲、TACCL、Mooncake、FLUX、CacheGen及两个不同的DeepEP-Ascend实现。

关键修正：

- 不将FA3固定shape的内核消融、合成输入RMSE写成完整模型TTFT/TPOT或业务精度。
- FA4的倍数保留旧cuDNN基线，注明后续实现已吸收相关技术。
- SGLang的部分A2/A3接口中use_fp8实际选择INT8；不与A5格式和另一DeepEP实现混写。
- CacheGen固定v6版本。Table1中622→176MB与accuracy1.00→0.98一起展示；取回并处理上下文的总延迟与完整请求TTFT/稳态TPOT分清。
- FLUX同时保留指定prefill/decode条件与H800 NVLink decode未加速的反例。
- 310P报告保留静态分析定位，正文改为自然语言，区分局部工具、Agent编排与运行证据；追溯路径完整保留。

## 视觉与交互

深色首屏和机制图配合浅色正文。九张图分别解释数据复用、分块流水、融合、布局、集合拓扑、消息聚合、缓冲路径、通信重叠和传输编码，不再更换四个框中的文字。

窄屏将前后两块图上下排列；宽屏左目录显示当前章节，移动端显示章节直达。新增瓶颈检索，正文仍静态生成且默认展开，脚本仅负责检索和阅读进度，不阻塞正文加载。

审查修正图示中的总工作量与依赖：Ring/Tree使用相同rank数；聚合前后保留相同载荷；流水同一资源不重叠，计算依赖先于消费；通信完成后的消费者位置与暴露等待分开。

## 维护位置

唯一实际渲染内容仍为 `operator-routes.json`、`operator-sources.json`、`operator-310p-prior.json`。两个`operator-expert-*.json`是本轮审阅输入快照；导入脚本可将审阅记录合入维护源，日常修改和编辑后的措辞以维护源为准。

`operator_visuals.py`维护机制SVG；`operator_research_site.py`负责页面；`content/operators-research.css/js`维护样式和渐进增强。dist为生成产物。

## 验收记录

浏览器记录保存到 `operator-expert-browser-qa-20261023.json`。结构验证使用 `scripts/verify_operator_research.py`；仓库原阅读器、推理压缩及技术地图校验照常保留。未做目标设备性能实验，未承诺线上2秒以内。
