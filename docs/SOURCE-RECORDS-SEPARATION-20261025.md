# 来源核对记录分离（2026-10-25）

信息来源页只保留来源目录、入口核对日期及紧凑记录链接，不再显示审阅记录大卡片。核对记录和附属文献由 scripts/build_source_records.py 从原有 canonical 表生成 source-records.html，不建立第二份可编辑内容源。

21条维护核对记录和17个附属文献入口全部保留，附原始依据；不把核对日志直接升级为本期动态或专题事实。三类表、核心/全部范围、生态筛选和原始链接不变。记录页提供返回入口，读者查询参数保留；旧 source-review/source-paper-entries 锚点转至新页对应位置。

verify_source_records.py 检查原记录文字、引用URL和锚点完整性，并接入CI。记录的事实准确性沿用原维护源，本轮没有重新核查其外部内容。

验收：整站构建、verify.py、verify_original_reader.py、test_reader_journey.cjs、JS语法检查与verify_source_records.py全部通过。VM检查旧记录锚点重定向保留month/scope/lang。本机记录页HTTP返回200；浏览器在导航提交时因工具无法确认当前网址而停止，未继续浏览器操作；不声称已完成实点与视觉验收。

已发布CCN v17。内容提交0be38e919de94044e306d08087b50070a13bf671，Sites源提交e09ba9d533e7483fca9b69d38401a32f09ce1977，部署appgdep_6adda62f8ae8819194fe435df8fa39f1 succeeded。原TableGit站点未修改。
