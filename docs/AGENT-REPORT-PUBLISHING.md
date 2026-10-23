# Agent 报告的源码与发布关系

统一主仓库：https://github.com/c1917797-bit/CCN-insight 。
既有只读站：https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/ 。

## 单一维护源

修改 `research/agent-scheduling/`，运行 `python scripts/build_agent_report.py` 和 `python scripts/verify_agent_report.py`。独立部署产物在 `research/agent-scheduling/outputs/isolated-preview/`；同一路径模块同时写入仓库 `dist/`，不替换 CCN 首页，不新增公开导航入口。

构建不需要凭据、原 LRIGIT 服务或旧工作区文件。没有复制个人密码、Git 凭据、运行日志、临时截图或浏览器状态。仅迁移 Agent 模块；不替代推理压缩的数据维护流程。

## 人工同步流程

1. 在主仓库修改、验证并推送，记录准确的 GitHub 提交。
2. 将独立部署产物同步到现有 Agent Sites 项目的 `dist/`；不要同步 CCN 全站或私有工作文件。
3. 在 Sites 发布镜像记录 GitHub 源提交，再按 Sites 工作流保存与发布版本。
4. 在部署记录中对应 GitHub 提交、Sites 提交、版本与验收结果。

GitHub 是维护源；Sites 自带源码仓库仅为发布镜像。没有建立 GitHub 到 Sites 的自动部署，推送并不等于线上更新。保留现有 public 访问方式与原网址；没有变更 CCN 正式站或旧 LRIGIT 站的发布状态。

报告页内链接仍在同一域名和路径下。数据是构建时生成的只读快照，不声称 TableGit 实时同步。
