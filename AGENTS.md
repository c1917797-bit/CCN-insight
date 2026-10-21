# CCN 网站维护说明

## 用户目标

维护极智、极稳、极简、极优网站。优先减少导航重复、无效留白、层层跳转，提升阅读体验。保留原有内容和业务逻辑，不编造论文结论、实测数据或硬件支持。

## 两套环境

## 主仓库与发布规则（2026-10-21 起）

- `https://github.com/c1917797-bit/CCN-insight` 是用户指定的唯一网站主仓库。
- CCN 正式站 `https://ccn-insight-four.sunshinepmy.chatgpt.site/` 由 Sites 托管；Sites 源码仓库是发布镜像，不是主编辑位置。
- 所有网站修改先在本仓库完成、验证并推送，再同步到 Sites 发布。记录主仓库提交与发布版本的对应关系；不得声称已配置自动同步。
- `research/ai-infra/` 保存根技术研究源码和快照，`publish_infra.py` 将其整合为 `/ai-infra/`。不要只改生成后的 `dist/ai-infra/`。
- TableGit 是外部来源数据与旧应用的服务。修改原站必须有明确任务授权，不会因更新本仓库自动同步。
- 延续旧站的月度动态、报告、归档以及 Agent 仍为外部链接；不能宣称后端及附件已全部迁移。

- 本仓库 c1917797-bit/CCN-insight：独立首页、信息源表格与 AI Infra 迁移副本。先阅读 README.md、docs/MIGRATION.md。
- 用户当前 AI Infra 原站：https://c1b3ie6ayp-sworks-lrigit-tpc.ru.yxsbase.win/business_insight/cloud_core/index.html
- 原站由 Irigit MCP 管理的 works 仓库及 TableGit 提供。修改本地 vendor 副本不会自动更新原站；推送 GitHub 也不等于部署原站。

## Irigit MCP

OpenCode 用户配置已连接名为 irigit 的远程 MCP。开始时调用 service_metadata，之后 skill_list 查找能力，skill_get 读取具体 operation 的契约，再调用相应操作。读取后确认 revision，写入前按契约执行并遵守原仓库 AGENTS.md。

身份采用服务当前授权上下文；如果需要选择人员，通过服务发现和确认，不复制别的会话身份或凭据。不要把密码、token、Cookie 写入仓库。TableGit 数据通过原生表接口处理，不把表目录当普通文件修改。遇到权限拒绝明确报告，不绕过。

## 修改与验收

1. 明确本次目标是原站还是独立首页，再定位实际生效的文件。
2. 优先复用现有组件，保持内容事实、来源链接和分类关联完整。
3. 本仓库执行 python scripts/build.py 和 python scripts/verify.py。
4. 原站需要检查真实渲染、导航和数据加载；只读源码不能算页面验收通过。
5. 修改后说明改动、验证证据、部署状态和未完成项。没有实测不承诺首屏 2 秒以内；没有完整迁移不宣称已独立。

## 内容偏好

先给结论，再讲挑战、技术路线、证据与下一步验证。LLM 以 Qwen3.8-27B 为业务示例，还包含降噪、翻译等领域模型；不能写成只服务单个模型。硬件范围为 310P、910B、950（具体型号未确认）。业务目标是精度损失小于 1%、高吞吐、低时延；这些是目标，不是已有结果。
