# Murakkab 官方原文深读记录

- 核验日期：2026-10-23。
- 官方会议页：https://www.usenix.org/conference/osdi26/presentation/chaudhry
- 原始论文：https://www.usenix.org/system/files/osdi26-chaudhry.pdf
- 版本：OSDI 2026正式论文，22个PDF页面，含出版方封面；印刷页567–587。
- PDF SHA-256：`9c9aa888b675c7849467d5b594e640996fee57f32b79fc9cf443fb549587c0e0`。
- 本地核验副本：任务临时目录 `.tmp/murakkab-official-20261023/osdi26-chaudhry-retry.pdf`，不发布整份PDF。

## 实际执行的技能范围

使用 `pdf` 技能读取正式PDF：以PDF文本与浏览服务逐项查找机制、原表和实验条件，用Poppler渲染第9、11、14页，实际打开完整页及裁图检查。未执行GROBID/Docling解析、论文代码、求解器复现或硬件实验，不将这些未执行流程记为完成。

下载直接来自USENIX公开地址。最初下载残片无法解析，已弃用；最终重试文件通过22页解析、正文提取及原页渲染，不使用失败残片。原图源不来自MozhiJiawei成品；参考成品仅用于学习表达方法。

## 定点核验

- §3.2–3.4：执行器来自注册库；逻辑DAG与执行配置分离；两层画像；MILP输入、输出与约束；部署计划不规定逐请求派发；默认60分钟与短周期扩缩容分工。
- Figure 6：PDF第9页／印刷页574，四类输入及三层配置输出；正文另列路由比例。
- §4.1、Appendix A.4：Azure A100/H100、vLLM 0.9、90百分位token负载；24小时到达模式来自2024-05-15到2024-05-16的LLM服务轨迹，非原生Agent生产轨迹。
- §4.3、Table 2与Figure 9b：四组原值、70%／30%SLO混合、手工调优与同款扩缩容基线；LangGraph对照存在部分时延违约。
- §4.6、Figure 12：学生代码视频核对，两个子工作流并行；Gemma均为4张A100。6卡全GPU达标，4卡两个工具均在CPU违约，5卡仅Whisper在CPU达标；不读取图上未披露的精确延迟。
- §4.4、§4.7、§4.8：动态编码仅对应token—pass@1前沿；20分钟实例准备时间为敏感性分析假设；Math-500到MathEval只支持相似领域画像迁移例证。
- Appendix A.5只核对其完整优化式定位和求解说明；没有独立验证全部公式与实现。

## 需要保留的口径差异

- Table 2成本211.7÷47.2≈4.49，摘要写最多4.3倍；本页不替作者消除差异。
- 改为LangGraph＋Auto基线则112.3÷47.2≈2.38；不能继续引用固定基线的比值。
- GPU数保留论文原单位，不改称GPU·小时。
- 对照未全部满足同等SLO，结果不能包装为所有策略等价达标下的普适收益。
- 原图和重绘、论文事实和本地判断分别标明；本页没有云核或昇腾实测结论。

## 维护接口

- 正文与页面接口：`deep_readings.py`，`pages(shell)`返回`reading-murakkab.html`；`page_sections()`返回既有`page-sections.csv`兼容元数据；`murakkab_body()`可直接取得正文。
- 页面标题：`Murakkab：画像驱动的工作流与资源联合优化`。
- 事实索引：`deep-reading-murakkab-evidence.csv`；原表数值：`deep-reading-murakkab-results.csv`。
- 原图溯源、裁切坐标、原文件与图像SHA-256：`deep-reading-murakkab-assets.csv`。
- 三张必要原图共约373 KB，均为300dpi裁取的PNG。默认延迟载入，原尺寸链接可放大；构建器需原样复制相对路径。

事实核验层级为“官方PDF定点深读与关键原图核对”。不称全文每项结论已核验，不称已复现。
