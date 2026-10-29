# 技术地图标题与芯片格式背景修订

日期：2026-10-29。范围：推理压缩技术地图标题；权重 × 量化专题的研究背景及格式对照标题。

## 阅读改进

- 地图主标题改为“推理压缩的四类核心技术”，说明分别解释数值位数、稀疏元素与结构、教师—学生知识迁移、矩阵因子化，避免用“值得追踪”代替地图用途。
- 研究背景新增英伟达、昇腾两张独立表。英伟达按 Ampere、Hopper、Blackwell 数据中心路线组织；昇腾按 310P、910B/A2、950PR、950DT 分列。
- 明确位宽不是数值格式：INT8/FP8，INT4/NVFP4/MXFP4，以及 FP8 E4M3/E5M2、HiF8/MXFP8 分别处理。
- 区分板卡规格、芯片路线公告、算子可接受的数据类型、实际算术路径和测量收益。尤其不将 WeightQuantBatchMatmulV3 的 FP4 权重输入自动写成原生 FP4 算术。
- 950 用户子型号仍未确认；不把公开支持矩阵写成用户设备验证结果。

## 唯一维护源

新事实与判断为 `ic_compression_topic_cards` 中两个 hardware 卡片；六个关联引用位于 `ic_compression_topic_card_refs`，来源在 `cloud_core_sources`。原阅读器仅投影这些记录，不新增事实副本。源条目按 URL 去重复用；CANN V3 URL 是可变 9.1.X 在线资料，保留各引用原有观察日期/版本。

采用的技能：仓库 ccn-insight-build、ccn-evidence-review；Sites 执行发布。没有运行 PPT 技能，没有更改 PPT、其他专题结论或原站首页。

## 一手依据与边界

- NVIDIA A100 数据手册：SYSTEM SPECIFICATIONS，INT8/INT4、FP16/BF16。
- NVIDIA Transformer Engine 2.20.2：FP8 E4M3/E5M2、MXFP8、NVFP4 的格式与缩放说明。
- OPi AI Studio 产品手册：1.2，310P 板卡 FP16/INT8 规格；厂商产品规格不能替代全部算子支持表。
- 华为 2025-09-18 官方路线公告：950 系列数据格式；路线不是设备实测或所有运行栈的部署证明。
- CANN WeightQuantBatchMatmulV3：Applicable Products、x/weight/antiquantScale 参数、产品脚注 1/2。当前读取日期 2026-10-29；不把 URL 路径 910 当作冻结内容。
- CANN 9.2.0 官方公告：2026-10-16 发布，950PR/DT 部分算子 8-bit/4-bit 计算。此次可读内容来自官方索引文本；其位宽描述不证明所有具体编码格式。

不加入跨芯片性能排名；不从峰值推算模型 TTFT/TPOT；未执行目标设备实验。

## 验证

构建、verify.py、verify_compression.py、verify_original_reader.py、test_research_map.cjs、test_reader_journey.cjs 通过。16 专题，211 卡片，488 引用，169 阅读器文件，91 表、182 已登记资源。

本地浏览器实测研究背景两张表分别渲染；3 行英伟达、4 行昇腾；中英切换保留两个独立表。1280px 视口无整页横向溢出；第一列调整为 150px。公开发布结果另记 deployment 回执。
