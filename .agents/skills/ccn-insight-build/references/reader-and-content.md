# 维护路径与验收

推理压缩表内容在 `data/compression/tables/`，界面在 `original-reader/site/business_insight/cloud_core/`。样式为 `reader-refinement.css`；语言为 `data/focus-ui.*.json`。不要直接修改 `dist/`、`data/directory/`、`research/ai-infra/imported/` 生成视图。

维护源改后更新bundle：

```text
python -X utf8 -c "import sys;sys.path.insert(0,'scripts');from refine_reader_copy import rebuild;rebuild()"
python -X utf8 scripts/build.py
python -X utf8 scripts/verify.py
python -X utf8 scripts/verify_compression.py
python -X utf8 scripts/verify_original_reader.py
node scripts/test_research_map.cjs
node scripts/test_reader_round2.cjs
python -X utf8 scripts/verify_expert_index.py --self-test
node scripts/test_report_reasoning.cjs
node scripts/test_expert_navigation.cjs
node scripts/test_topic_reader_five_rounds.cjs
python -X utf8 scripts/audit_compression_inventory.py --self-test
```

只调用 `rebuild`；旧日期化文案脚本可能覆盖修订。三类来源各一张表，同一主体一行，产业用生态列区分；默认核心与全部目录不可混淆。

新领域用 `insight_topic.py new` 生成未发布契约，`validate` 核对，`render --out .tmp/...html` 生成隔离预览。模板带问题、挑战、路线、来源、主张、判断和变更，不带压缩论文或虚构效果。分类确认后再最小化接入组件。

浏览器先确认本机服务仍监听、最新构建完成。检查真实加载、证据锚点、长标题/公式、检索/待读。视口测试记录实际innerWidth，请求成功不等于移动端已测。保存截图和检查结果。构建、推送、部署分别记录；当前迭代仅本地。

## 跨专题索引

`scripts/build_expert_index.py` 随原阅读器构建生成索引，内容仍来自唯一表源，不是第二个编辑入口。维护卡片渲染规则时同步检查索引的可见卡片筛选：未渲染内容明确列为 omitted，不生成无法抵达的链接。每条资料保留自己的来源、定位和审阅深度，不能借用相邻卡片的全文证据。

锚点验收要检查实际滚动位置，不能仅判断节点存在。抽取每个专题案例做冷启动定位；同时检查 hash 恢复、返回地图和固定页头遮挡。打开记录与待读只保存在当前浏览器；内容 hash 变化只表示资料修订，不能描述为新发表、已读完或研究结论发生变化。

论文盘点由 `audit_compression_inventory.py` 从唯一源重算，区分收录编号、标题候选、阅读摘要和专题引用；这些环节不是天然严格子集。旧筛选状态可能落后于后续引用。没有明确记录时，不把URL入库称为阅读，也不把指定章节核对称为全文阅读。

原理分镜仅使用已维护的steps，正文初始完整可读。没有直接步骤的主题保留待核对问题，不为了补齐视觉组件而编造原理。技术归属依靠实际机制，不因标题出现KV等关键词就自动归入量化。
