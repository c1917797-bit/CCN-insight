# 算子根技术洞察：本轮最终定位与验收

本记录优先于同日较早的方案记录。当前仅本地预览，未推送 GitHub、未发布 CCN、未修改原站或 TableGit。

## 面向读者的内容层次

- 主线是硬件约束、执行瓶颈、加速机制、产业与学术证据、研究判断。
- 保留计算算子加速、通信算子加速两类，以及四条计算机制、五条通信机制。
- 自动生成、编译、调优属于横向效率技术；在总览普通章节提供入口，不作为首页重点或新的根分类。
- 310P 项目报告、实现清单、缺口、任务、原 PPT 身份与哈希不进入阅读页面。历史地址仅跳转横向方法的研究启示。
- 310P 仅作为硬件适用性和知识转移判断的目标之一。生成工具相关内容解释所需能力及依据，不报告本地项目进展。

## 研究增量

九条机制保留背景、原理、挑战、产业/学术进展、路线比较、研究启示和结论。27个具名技术分支、29条机制证据记录；每项证据区分条件、效果与限制。

横向效率研究增加 KernelEvolve、KernelBlaster、AVO、CUDA Agent、AscendOptimizer 的对照，并保留12条具体证据，覆盖生成、已有实现优化、形状专门化、领域后训练与独立评测。GPU/多硬件、昇腾NPU分别陈述，不能跨表排名最大倍数。

关键勘误和边界：

- KernelEvolve的正确性覆盖与全部加速不同；MTIA不是昇腾。
- KernelBlaster的有效率与成功集合的速度并列，保留具体硬件和计量方式。
- AVO指NVIDIA的Agentic Variation Operators；B200前向注意力及七天搜索不能写成整模型TTFT/TPOT或一次生成。
- CUDA Agent按论文Table1说明正确率、更快率、正确解速度聚合与200轮轨迹；记录摘要/表格差异。
- AscendOptimizer锁定v2、101算子、910B2/CANN8.3与230次硬件评估；与v1及从零生成区分。
- Triton-Ascend更新至v3.6.0固定tag；PyPTO Tensor/Pro产品范围分开；新昇腾SIMT能力不外推310P。

CannBot用于Add概念教学，解释Host/Device、GM/UB、Tiling、缓冲生命周期、搬算流水和独立验证。教学数据和伪代码为重绘，未声称原模板已运行。源码审阅保留逐tile偏移和Host整除条件的待核查点，未把可疑模板直接当正确实现。Add+RMSNorm扩展保留完整归约依赖、dtype/舍入、必需残差和rstd输出。

## 内容维护入口

- `research/ai-infra/operator-routes.json`：根技术版图、机制正文、结论。
- `research/ai-infra/operator-sources.json`：共用原始来源注册表。
- `research/ai-infra/operator-cannbot-case.json`：教学概念和案例研究说明。
- `research/ai-infra/operator-codegen-insight.json`：横向方法、首屏判断、具名系统比较、结论。
- `research/ai-infra/operator-codegen-hardware.json`：硬件差异、工具链与能力演进启示。
- `research/ai-infra/operator-codegen-named-a.json`、`operator-codegen-named-b.json`：具名系统证据。
- `operator-310p-prior.json`：内部历史材料，仅作溯源审计，不渲染项目报告。

渲染由 `operator_research_site.py`、`operator_cannbot.py`、`operator_codegen.py`、`operator_visuals.py` 与本地 CSS/JS 完成。研究来源更新由 `scripts/integrate_operator_codegen.py` 按ID合并，保留引用顺序；不得手改生成页面。

本轮使用deep-research的事实核对方法与Sites的本地实现、设计和预览流程。CannBot作为研究对象读取，没有安装或执行其外部插件；没有NPU实验。

## 验收与限制

- 构建通过。
- 算子专用验证通过：8份研究数据、13个活跃阅读页、9项机制、5个具名系统、12条生成/调优证据、引用/内链/分类和默认展开。
- 13页均实际进入；九项机制均具备完整章节，无页面级横向溢出、无折叠、无310P报告入口。五个具名对照链接均直达正确证据，落点位于固定页头下方。
- 同源iframe按390、845、1440 CSS像素目视验收；手机案例、机制图、对照卡片与桌面表格可读。这是布局宽度验收，不是物理设备测试。
- 全站目录关联、推理压缩16专题/引用、四路线地图验证通过。
- 扩展的原阅读器逐字节一致性检查未通过：`current-synthesis.js`维护源与生成文件在`dataset.sectionOutline`等内容上存在差异。此文件不属于算子改动范围；未更改其内容或放宽检查，不能宣称该扩展检查通过。

点击记录见 `operator-expert-browser-qa-20261023.json`。公开网页未更新；原作者实验与本地验证不可混写。
