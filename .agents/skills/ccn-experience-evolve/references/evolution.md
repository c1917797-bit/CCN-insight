# 操作与参考

参考以下实际读取的model-tuning-lab规范，吸收经验分类、最小规则与交接分工，未复制其主机与推送流程：

- [经验入仓](https://github.com/c1917797-bit/model-tuning-lab/blob/main/.agents/skills/mst-experience-ingestion/SKILL.md)
- [Skill治理](https://github.com/c1917797-bit/model-tuning-lab/blob/main/.agents/skills/mst-skill-governor/SKILL.md)
- [维护者交接](https://github.com/c1917797-bit/model-tuning-lab/blob/main/.agents/skills/mst-maintainer-handoff/SKILL.md)

读取日期2026-10-23，仓库页当时显示main最新提交23ec33d；不表示远端永久一致。

经验在 `.agents/experience/*.json`。工具使用固定校验白名单，不运行经验中提供的任意shell：

```text
python scripts/insight_learning.py validate
python scripts/insight_learning.py verify <lesson-id>
python scripts/insight_learning.py decide <lesson-id> --decision <decision.json>
```

verify实际执行关联检查，回执在 `.agents/evals/receipts/<id>.json`，绑定经验内容哈希。失败不得采用。decide要求lesson_id、lesson_sha256、outcome(accepted/rejected)、reviewed_by、reason、authorization_reference；仅记录状态，不提交、不推送、不自动修改skill。

不得伪造维护者名字或授权。无决策保留proposed；当前用户授权只适用于明确范围，不推定未来永久批准。新反例可使旧规则superseded，改变已验经验必须重新验证。采用后更新最小skill段落和回归用例，不能把全部经验塞进SKILL.md。

接手顺序：AGENTS → HANDOFF → 注册表 → 当前窄skill → 相关经验/证据。技术内容保留自身版本。回退规则须同步引用和注册表，不能留下旧“通过”回执。
