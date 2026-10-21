# CCN Insight

极智、极稳、极简、极优的独立内容仓库。首页源码、内容快照与 AI Infra 迁移资料均在此维护。

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

**首页和信息源表格能够独立运行。AI Infra 原应用尚未完成独立部署。**

首页的 AI Infra 和 Agent 入口仍指向现有网站。AI Infra 源码需要原有兼容数据接口，不能直接把它当作已经完成迁移的静态站。没有复制服务端 LRIGIT 程序、账号凭据和完整报告附件。详见 [迁移状态](docs/MIGRATION.md)。

## 如何维护

1. 修改首页板块和入口：编辑 `content/sections.json`、`content/entries.json` 中的 `rows[].row`，保留关联 ID。
2. 修改首页外观：编辑 `home_design.py`、`dist/home.css`、`dist/home.js`。
3. 修改信息源：编辑 `data/directory/`，同时保持 family、channel、source 关联键一致。
4. 运行 `python scripts/build.py` 和 `python scripts/verify.py`，检查结果再提交。
5. 在 GitHub 仓库 Settings → Collaborators 邀请协作者；建议通过 Pull Request 审核修改。

所有内容来自已有项目及数据导出，复制不代表重新验证了论文结论或来源可靠性。未附加新的开源许可证，沿用原文件中的版权与许可证声明。
