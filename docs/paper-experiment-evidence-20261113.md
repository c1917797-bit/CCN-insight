# 论文实验原文核对笔记 · 2026-11-13

本笔记仅说明本轮8条种子实验的原文定位、条件和核对边界。数据待由主任务注册进唯一维护表；`.tmp/paper-experiments-seed.json`是临时导入材料，不是第二维护源。本轮没有改动旧卡片、旧引用或来源阅读深度，没有进行模型复现、服务测试或设备实验。

按仓库[ccn-evidence-review](../.agents/skills/ccn-evidence-review/SKILL.md)核对。全部新记录标记为`section_review`：核对所列方法、设置、结果表和必要附录，均不表示全文审阅。SmoothQuant与QuaRot现有旧引用仍是`abstract_review`；本笔记和新实验记录不将旧记录整体升级。其余现有引用也保持原样。

## 数据语义

- `year`统一按论文首次arXiv年份，独立于本轮观察版本的年份。因此SmoothQuant为2022，KVQuant为2024；不能把这些值解释成v7/v6发布日期或会议年。
- `observed_version`绑定本次指定版本；同一行没有跨版本拼数。`source_url`绑定该版本的原文。
- 每行是一个可识别的实验协议。同一论文的质量、完整模型运行和内核微测分别保存；联合W/A/KV实验用多个既有专题ID关联，不重复计数或累加收益。
- `not_reported`只表示本行实验未报告该类指标，不表示整篇论文没有报告。`not_checked`表示未核实，`not_applicable`表示不适用；三者不可互换。空指标数组不是零。
- 质量指标的PPL差异不能换成准确率损失百分比。accuracy的单位为百分数，差异才是百分点。
- 未单列的W/A/K/V dtype在对应字段明确标注；不因“4位/8位/16位”自动补成INT或FP。AWQ沿论文W4A16写A16，但Table 4没有逐项列其浮点编码；KIVI残留区不补写未经该实验逐项确认的dtype。
- 本轮不是跨论文排名。模型、数据、协议、位率、运行实现不同，单个数值不能证明算法普遍优劣。

## E01 · AWQ质量

本地关联：`parameters-precision__audit_awq`，来源`source-9d933cbebef57745282c1b61`。

已读[v6 HTML](https://arxiv.org/html/2306.00978v6) §4、§5.1、Table 4。Llama-2-7B、INT4/group128，WikiText-2 PPL为FP16 5.47、AWQ 5.60；相同INT4分组对照RTN 5.73、GPTQ 5.69、GPTQ-R 5.63。Pile小校准集和alpha网格20见§5.1。PDF大文件读取未成功，本次不编造物理页码。质量表的设备、batch、序列长度和KV编码未补齐；TinyChat性能数字不挂到本行。

## E02与E07 · AlignQuant质量、系统分行

本地关联：`parameters-precision__audit_alignquant`，来源`source-eddb5dcff2f30874ab89a340`。

已读[v1 PDF](https://arxiv.org/pdf/2610.07457v1) §3.3、§4.1–4.3、Tables 1–2及Appendix G.1–G.7；并交叉核对[HTML](https://arxiv.org/html/2610.07457v1)。默认64×64 tile、60% W4其余W8、A8。质量行取[Table 2，物理第8页](https://arxiv.org/pdf/2610.07457v1#page=8)：WikiText-2 word-level PPL 12.49→12.61；不把系统输入输出长度充作PPL评测协议。

系统行取[Table 1，物理第7页](https://arxiv.org/pdf/2610.07457v1#page=7)：BF16→AlignQuant，TTFT 17.47→19.67ms、TPOT 17.19→7.54ms/token、吞吐58.18→132.28token/s、驻留内存5.99→2.72GiB、峰值6.09→2.72GiB。A100-SXM4 40GB、batch1、输入128/输出512；2次预热、5次计时取中位数。在线准备计入，离线候选构造/校准/打包排除；详见[G.5–G.7，物理第20页](https://arxiv.org/pdf/2610.07457v1#page=20)。KV配置匹配不代表dtype已单列。INT4载荷在片上展开成INT8操作数，不写成纯INT4执行。TTFT退化与解码改善同时保留。

## E03 · SmoothQuant质量

本地关联：`activations-precision__case_smoothquant`，来源`source-4deb705f0770cf0cea9b2e50`。

已读[v7 PDF](https://arxiv.org/pdf/2211.10438v7) §4、§5设置、Tables 2与7，并核对[HTML](https://arxiv.org/html/2211.10438v7)。本行仅取[Table 7，物理第7页](https://arxiv.org/pdf/2211.10438v7#page=7)：Llama-2-7B，WikiText-2序列2048，WINT8按通道/AINT8按token，alpha=0.85，PPL 5.474→5.515。它不是Table 2的O3 per-tensor静态配置。轻量算子的FP16激活与持久KV-cache dtype分开，后者未单列。摘要最高加速、其他OPT实验与本行不合并。

## E04 · QuaRot质量

本地关联：`activations-precision__case_quarot`，来源`source-50944e32342addf16b5ea70e`。

已读[v2 PDF](https://arxiv.org/pdf/2404.00456v2) §4 Stage 2a–2c、§5设置、Tables 1与4，并核对[HTML](https://arxiv.org/html/2404.00456v2)。主配置取[Table 1，物理第8页](https://arxiv.org/pdf/2404.00456v2#page=8)：Llama-2-70B，WikiText-2序列2048，FP16 3.32→QuaRot/GPTQ 3.79。W INT4按通道、A INT4按token、KV4/group128。GPTQ校准128×2048；A/KV裁剪0.9/0.95。查询与attention点积FP16、RMSNorm FP32，因此“W/A/KV4”不等于全部运算4位。QuaRot-128G、RTN变体及RTX3090单Transformer块性能是其他配置，不挂到本行。

## E05 · SparseGPT质量

本地关联：`parameters-selection__case_sparsegpt`，来源`source-ee93a091f506c0bbb2af4c05`。

已读[v3 PDF](https://arxiv.org/pdf/2301.00774v3) §4设置与Table 1、Appendix B，并核对[HTML](https://arxiv.org/html/2301.00774v3)。[Table 1，物理第6页](https://arxiv.org/pdf/2301.00774v3#page=6)：OPT-2.7B、50%非结构化稀疏，raw-WikiText2 PPL 12.47→13.48。校准C4 128×2048；评测非重叠2048-token段见Appendix B。A100 80GB是剪枝准备设备。未额外量化不等于已逐项确认所有W/A/KV dtype。Appendix E的CPU DeepSparse 1.82倍收益属于其他实验，本行不填速度/内存。

## E06 · KIVI质量

本地关联：`kv_cache-precision__case_kivi`，来源`source-3ab07c12f815b21f4a366f64`。

已读[v2 PDF](https://arxiv.org/pdf/2402.02750v2) §3.3、§4.1、§4.2.1–2与[Table 3，物理第8页](https://arxiv.org/pdf/2402.02750v2#page=8)，并核对[HTML](https://arxiv.org/html/2402.02750v2)。Llama-2-7B，K按通道、V按token，量化部分INT2，group32、residual128；GSM8K exact-match accuracy 13.50%→12.74%。高精度残留使“全部KV均2位”的描述不成立。该质量实验不附加A100、ShareGPT输入161/输出338、扩batch吞吐或总峰值内存；那些属于另组效率实验。

## E08 · KVQuant内核微测

本地关联：`kv_cache-precision__case_kvquant`，来源`source-2ad74528d39796a34a8dac3b`。

已读[v6 PDF](https://arxiv.org/pdf/2401.18079v6) §3.7、§4.4、[Table 6，物理第10页](https://arxiv.org/pdf/2401.18079v6#page=10)及[Appendix R/Table 22，物理第26页](https://arxiv.org/pdf/2401.18079v6#page=26)，并核对[HTML](https://arxiv.org/html/2401.18079v6)。A6000、LLaMA-2-7B-32K、batch1、16K、nuq4-1%：Key 219.4→126.3μs、Value 203.7→124.5μs。按层收集激活，每层1000次测量取平均；全算术FP16。量化方total已含packing、dense、sparse；FP16 Key基线还含新Key的RoPE。这是核微测，不是TTFT、TPOT或完整attention时延；对应任务质量和峰值内存未在本实验报告。没有并入另一模型的容量估算或PPL结果。

## 本地关联核验边界

源ID、主案例ID及专题ID均来自现有唯一维护表：`cloud_core_sources`、`ic_compression_topic_cards`、`ic_compression_topic_card_refs`与`ic_compression_topics`。研究路线中已有AWQ、SmoothQuant、QuaRot、SparseGPT、KIVI、KVQuant关联；未搜到AlignQuant专门研究路线，本轮没有虚构route ID。

种子仅供主任务注册和UI接入，不表示表结构已注册、页面已验证、主仓已提交或网站已发布。注册后需由主任务沿唯一维护流程核对读取与展示，特别保留空值解释、实验类型及完整条件。
