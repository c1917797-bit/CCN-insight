# CCN-insight 源码副本

本目录从 MCPGit 管理的 `works` 仓库复制，用于独立修改云核洞察站点。

## 来源

- 源版本：`44c5fdf1d15051ad017a484f0032c93fd8d429a5`
- 页面入口：`business_insight/cloud_core/index.html#view-topics`
- 原网页：https://c1b3ie6ayp-sworks-lrigit-tpc.ru.yxsbase.win/business_insight/cloud_core/index.html#view-topics
- 复制日期：2026-10-21

## 包含什么

- `business_insight/cloud_core/`：页面、交互、双语界面文字、SVG 动画、数据读取适配代码。
- `assets/`：共享样式、导航、阅读器、翻译与 TableGit 客户端。
- `tools/cloud_core/`：采集、筛选、表结构定义、构建与验证工具。

## 运行边界

这是应用源码副本，不是已部署的新站。没有复制 TableGit 数据、服务端 MCPGit 程序、账号凭据、Git 历史或报告二进制附件（PPT/PDF/位图）。原始源码引用这些附件的位置仍保留。

页面通过同源 `/mcp` 和 `/__mcpgit/tables/` 读取动态数据。直接用静态服务器或 GitHub Pages 打开只能加载界面；在配置兼容的 MCPGit 服务、权限和业务数据前，不能显示完整洞察内容。不要在浏览器代码中填写管理员凭据。

页面保留原来的业务标识 `cloud-core` / `cloud_core`。新部署可以在独立数据库中保留这些标识；若改名，需要同时更新查询条件与数据中的标识，不能只改页面标题。

## 后续独立部署

1. 配置可用的 MCPGit/TableGit 服务及新项目的数据空间。
2. 通过 TableGit 原生接口导入表结构和经过检查的数据，保留关联键。
3. 配置同源服务路由与只读访客权限，编辑权限单独授权。
4. 补齐报告附件及其它站点的导航目标。
5. 执行工具目录中的相关检查，再逐页检查实际数据加载。

共享导航包含原站其它专题的链接；它们不代表这些其它专题已一并复制。
