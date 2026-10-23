# 新领域证据契约

模板为 build skill 的 `assets/topic.template.json`。新主题的topic.json是唯一内容源；预览由它生成。现有压缩保持原表结构。

来源字段：id/url/title/version/review_depth/checked_at/locator。candidate不能成为已核实事实的唯一依据。

主张字段：id/kind/text/source_ids/metrics，kind为fact/analysis/hypothesis。观点须有依据，假设须有验证条件。摘要只能支持摘要实际报告的结果，不能因有数字就升级审阅深度。

指标状态：

- reported：原文有值，含metric/value/unit/scope/statistic/model/hardware/task/workload/baseline/locator。条件缺失时comparison_ready=false，并列missing_conditions。
- not_reported：value=null，显示未报告，不能填0。
- theoretical：提供formula，不作为实测或业务通过依据。

scope为kernel/forward/serving/training/storage。reported TTFT/TPOT必须为serving；prefill-only保留prefill指标。attribution为component/combined/configuration；组合整体结果不可标单组件归因。

极稳按课题定义故障恢复、可用性、错误率、尾时延等指标；交代窗口、故障模型、负载和统计口径。单组件可靠性不等于全服务可用性，不套用压缩固定指标。
