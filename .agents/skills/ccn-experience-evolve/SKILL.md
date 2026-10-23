---
name: ccn-experience-evolve
description: Turn demonstrated CCN maintenance successes, failures and reader feedback into bounded lessons, regression cases and updated skills. Use after reusable findings or during maintainer handoff, not for logging every chat message.
---

# CCN 经验传承与受验证的进化

先读 `.agents/HANDOFF.md`、`.agents/skills.registry.json` 与相关经验，不重复发现已证实的问题。操作见 [evolution.md](references/evolution.md)。

## 经验准入

回答：何时触发、行为如何改变、适用边界、证据位置、如何发现规则失效。保留正例、失败或反例；一次模型失败不泛化为整条路线无效。

优先修改已有窄skill、验证案例、工具说明或模板；确有独立触发条件才新增skill。技术事实进内容源，操作经验进经验库，临时环境状态进交接。

## 闭环

真实反馈 → proposed经验 → 反例与回归 → 验证回执 → 维护者决策 → accepted/rejected → 更新最小资产 → 后续按条件复用。

`scripts/insight_learning.py` 管理经验状态。候选没有规则效力；回执绑定内容哈希，经验变更后旧回执失效。采用时记录资产、复用理由和回退方法。工具不自行改写skill、技术结论、权限或发布设置。

可自动运行已知校验、生成待审提案、检测证据变化；不得伪造维护者决策。没有授权就保留proposed。用户要求持续运行时再配置调度，本skill不创建定时任务。

## 交接与退役

交接写明本地/已发布、工作树状态、改动入口、实际检查、未完成项、下一步和恢复命令；不把未提交结果写成已合入或已交付。不存凭据和整段聊天。

规则失效须记录原因与替代者。审计发现先核实；误报也可作为反例保留，不能为通过审计修改本来正确的内容。
