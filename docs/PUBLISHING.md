# 主仓库与发布

## 权威来源

- 主仓库：`c1917797-bit/CCN-insight`，网站源码与内容修改首先在这里提交。
- 正式站：`https://ccn-insight-four.sunshinepmy.chatgpt.site/`。
- Sites 项目：`appgprj_6ad8b74cbb048191b7b6aaf46ad43a89`，只作为发布镜像。
- TableGit 与 LRIGIT works：外部资料来源及旧应用，不是 CCN 网站主仓库。

## 发布步骤

1. 修改主仓库源码、内容或样式。根技术原稿在 `research/ai-infra/`，正式导航与整合逻辑在 `publish_infra.py`。
2. 若改动原稿生成程序，先运行 `python research/ai-infra/build.py`。
3. 运行 `python scripts/build.py` 和 `python scripts/verify.py`，检查实际页面。
4. 提交并推送主仓库，记录提交 SHA。
5. 将构建产物 `dist/` 同步到已绑定的 Sites 发布工作区，保留其 `.openai/hosting.json` 身份配置。使用 Sites 支持的源码同步与部署流程。
6. 部署成功后记录 GitHub 提交、Sites 源码提交、版本号及部署状态。不能把 GitHub 推送成功等同于网站发布成功。

目前没有设置 GitHub 到 Sites 的自动同步。账号、令牌、浏览器会话与 `.openai` 身份文件不得提交到公开主仓库。Agent 与旧站月度内容仍使用外链。
