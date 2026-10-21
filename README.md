# CCN Insight

极智、极稳、极简、极优的独立内容仓库。首页源码、内容快照与 AI Infra 迁移资料均在此维护。

**本仓库是 CCN 网站的主仓库。** 正式站：https://ccn-insight-four.sunshinepmy.chatgpt.site/ 。Sites 仅承担发布镜像与托管，当前为人工同步，不是自动部署。维护流程见 [发布说明](docs/PUBLISHING.md)。

## 快速运行

需要 Python 3.10 或以上，不需要安装额外依赖。

```sh
python scripts/build.py
python -m http.server 8781 --directory dist
```

打开 http://localhost:8781。信息源表格位于 `/sources.html`，可下载 CSV。

## 仓库内容

| 目录或文件 | 内容 |
|---|---|
| `build.py`、`home_design.py` | CCN 首页及四大板块生成程序 |
| `dist/` | 可直接托管的首页、样式、动画和信息源表格 |
| `content/` | 首页板块和入口的 TableGit 发布快照 |
| `data/directory/` | 信息源目录及关联入口数据 |
| `data/tables/` | 此前导出的 16 张业务数据表；原有审核状态保留 |
| `vendor/ai-infra/` | AI Infra 应用源码副本、资源与维护工具 |
| `docs/` | 迁移范围、数据审计和文件清单 |
| `scripts/` | 构建与完整性检查 |
| `.github/workflows/` | 自动构建、验证并保存静态站点构建产物 |

## 当前独立程度

**首页、信息源表格、AI Infra 根技术地图与静态研究专题能够独立运行。旧 AI Infra 动态应用尚未完成整体迁移。**

首页 AI Infra 入口指向本站 `/ai-infra/`。根技术源码在 `research/ai-infra/`，通过 `publish_infra.py` 生成正式页；其月度内容与 Agent 入口仍指向原网站。`vendor/ai-infra/` 中旧应用需要兼容数据接口。没有复制服务端 LRIGIT 程序、账号凭据和完整报告附件。详见 [迁移状态](docs/MIGRATION.md)。

## 如何维护

1. 修改首页板块和入口：编辑 `content/sections.json`、`content/entries.json` 中的 `rows[].row`，保留关联 ID。
2. 修改首页外观：编辑 `home_design.py`、`dist/home.css`、`dist/home.js`。
3. 修改信息源：编辑 `data/directory/`，同时保持 family、channel、source 关联键一致。
4. 运行 `python scripts/build.py` 和 `python scripts/verify.py`，检查结果再提交。
5. 在 GitHub 仓库 Settings → Collaborators 邀请协作者；建议通过 Pull Request 审核修改。

所有内容来自已有项目及数据导出，复制不代表重新验证了论文结论或来源可靠性。未附加新的开源许可证，沿用原文件中的版权与许可证声明。
