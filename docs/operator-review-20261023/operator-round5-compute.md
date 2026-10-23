# 第5轮计算侧学术与教学核验

核验日期：2026-10-23。只读检查当前 canonical `operator-routes.json`、`operator-expert-guide.json`、`operator-cannbot-case.json` 与 dist 实际文字；未再次导入旧 `operator-expert-compute.json`，未扩展新研究、未修改产品。

## 结论

Stream-K、Marlin及融合修订已准确进入实际页面，未发现需要回滚的新事实错误。保留了一项应当立即调整的结构错置；另有一项可小幅收紧的教学边界，不影响例子的数学正确性。

## 1. P1：复用页把“优先研究”放进“容易失效的条件”

- 实际页：`dist/ai-infra/operators-memory-reuse.html`。
- canonical：`branches[id=compute].routes[id=memory-reuse].selection.unsuitable[0]`。
- 实际生效文字在“容易失效的条件”下，以“优先研究：同一输入块被多个输出反复读取……”开始，再接Add反例。
- 问题：同一列表项混合了成立条件和反例，且把明确的正向选型信号放在失效栏，会反转读者理解。这是合并位置问题，不是机制错误。
- 建议拆分：
  - `selection.suitable[0]`：“同一输入块被多个输出反复读取，或可消除一次中间张量写回及后继重读。”
  - `selection.unsuitable[0]`：“独立FP32 Add每个元素只读两个输入、写一个输出，理想流量已为12N字节；仅增大片或增加缓冲不会再减少这个理想数据量。达到这一数据流后，优先检查有效带宽、并行度与启动成本。”
- 理想流量的限定：每元素4字节、无额外副本；12N是数据量推导，不是实测流量、带宽或时间。
- 来源：`cannbot-add-template`、`ascendc`。第06章insight已正确表达该机制，可避免重写为第三份长说明。

## 2. P2：CannBot的RMSNorm反例建议补一句“教学手算”的范围

- 实际页：`dist/ai-infra/operators-1.html`，Add到RMSNorm的进一步例子。
- 当前数学正确：z=[1,3]、γ=[1,1]、ε=0时，mean(z²)=5，整体输出[1/√5,3/√5]；逐元素各自归一化得到[1,1]，足以证明列tile不能独立使用局部统计量。
- 当前也正确保留了z必需输出、rstd、片上容量以及dtype/舍入限制。
- 可改进处：前轮“这是机制推演、不是CannBot模板实测”的原句已被替换。页面其它位置说明教学范围，但这里加入短语更直接，也能避免读者把ε=0当成实际接口配置建议。
- 建议在 `fusion.description` 开头加：“下面用教学手算说明归约依赖，不是该模板的执行结果；实际测试沿用参考接口约定的ε。”
- 来源：`cann-add-rms-norm-expert`；该例为公式推导，不新增实测主张。
- 这是低成本边界补充，不需要给例子加新的长警告卡。

## 已通过的关键核验

1. **Stream-K**：实际页保留A100 108SM、400W/1005MHz、32,824形状、FP16输入/FP32累加与输出、128×128×32 tile、CUDA11.6 cuBLAS。表2Average1.13×、Min0.64×口径正确，没有改称几何平均；guide同时呈现退化，不将“填满设备”等同更快。输出tile并行、跨块Split-K、按MAC迭代分工三者已分清。[原论文v1](https://arxiv.org/html/2301.03598v1)

2. **FA2 split-K层级**：实际路线表已说明原FlashAttention的线程块内warp划分，与GEMM跨线程块Split-K不是同一层；没有把作者自己的split-K名称误判为错误，也没有把前向的低通信扩展到反向。[FA2原论文v1](https://arxiv.org/html/2307.08691v1)

3. **Marlin**：实际页明确静态INT4权重/scale预排布、核内解包反量化到FP16、FP16 Tensor Core消费，没有伪装原生INT4×INT4矩阵指令，也没有加入未逐实验核对的峰值、TTFT或TPOT。GPU和Ascend证据分开。[原论文v1 §3.3–3.4](https://arxiv.org/html/2408.11743v1)

4. **FA3正交变换**：Q/K乘同一个正交M时，量化前(QM)(KM)ᵀ=QKᵀ的公式准确；量化后误差与模型任务质量没有被混为一谈。[原论文v2 §3.3](https://arxiv.org/html/2407.08608v2)

5. **融合**：实际页已用“相邻Kernel经GM交接”替代“跨核传递”；Matmul逐元素尾处理与Add+RMSNorm整行归约分层，必需残差输出写回没有被删除。寄存器需求上升/并发驻留下降的方向已修正。

6. **CannBot位置输入测试**：x₁[i]=i、x₂[i]=1000+i、期望1000+2i的算术正确，保留“小规模、可精确表示、跨两片及尾片”限定。原模板逐片offset仍写为未连同Host复现的静态待核查点，未升级成已证实故障或已验证实现。

7. **维护关系**：新增事实在canonical、guide和实际dist中一致。Stream-K、Marlin source注册含版本、核对范围和设备范围。自动生成仍是寻找实现的横向方法，未吞并四条根机制，也未把310P内部项目带入前台。
