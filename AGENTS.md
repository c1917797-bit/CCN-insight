# CCN 网站维护说明

## 统一入口候选与展示修订（2026-10-28）

继续维护前先读 `docs/COMPRESSION-DEMO-20261028.md` 和 `docs/COMPRESSION-SOURCE.md` 顶部。原站五入口转到单一 CCN 阅读器的方案已准备，但被原站既有全局检查阻挡，尚未正式切换；不得声称两个公网网站已共源。原站候选仅包含推理压缩入口，以及用户逐项批准的 OCP 版本引用和一个 provider 测试样本修复。禁止上传私人校验数据、扩大到其他业务栏目的修复或绕过失败的发布检查。CCN 的实际成功版本以 deployment/ccn-publication.json 为准。

## 本地迁移保护（2026-10-22）

用户要求原样迁移推理压缩。默认阅读器是 original-reader/site/ 的原版页面，构建时只注入静态数据读取适配，默认预览为 /business_insight/cloud_core/index.html#view-topics。双站交付必须使用 renderer=original-reader，不再交付 compression-migration 的重新排版页作为正式替代。保持16专题正文与原版一致。详见 docs/ORIGINAL-READER-PARITY.md。

统一维护入口为 scripts/maintain_compression.py，读取层为 compression_store.py。内容修改只进入 data/compression/，随后 scripts/stage_compression.py 校验并生成两个站点的待发布静态模块。不得直接编辑生成视图；不得回写旧 TableGit 或以为生成两站文件等于线上已更新。编辑台本机服务不提供发布接口。详见 docs/COMPRESSION-SOURCE.md。

2026-10-22 用户明确授权将本批统一维护源推送 GitHub；随后用户明确授权两个公开网站发布更新。发布仍需逐站记录版本与验收结果。推理压缩唯一可编辑源为 data/compression/tables/*/rows.jsonl；research/ai-infra/imported 和 data/directory 是生成视图。先阅读 docs/TABLEGIT-MIGRATION.md。此条优先于下方一般的推送发布流程。

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

## 可复用洞察 Skill 与交接（2026-10-23）

新建或维护洞察时，先读 `.agents/HANDOFF.md` 与 `.agents/skills.registry.json`，再按任务读取对应 SKILL.md：页面构筑用 ccn-insight-build，证据与判断用 ccn-evidence-review，经验沉淀和交接用 ccn-experience-evolve。仓库内为唯一维护版本，不复制到个人目录另行维护。极稳等新领域可复用方法与模板，不继承推理压缩的具体技术分类或业务门槛。

经验候选须有触发、行为差异、适用范围、反例与验证证据；不能把反思直接当规则。结构校验不等于内容正确、技能行为已充分验证或网站已发布。当前页面打磨与技能沉淀保持本地，不自动推送或发布。
