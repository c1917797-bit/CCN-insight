"""Architect reading layer. Decisions are proposals, references are separately dated."""
from html import escape as e
from decision_map import read, BASE

NAMES={'workflow':'依赖感知排程','mapping':'状态感知映射','sharing':'干扰感知分配'}

def rows():
    return read('architecture-decisions.csv')

def source_lens():
    return '''<aside class="architect-lens"><span class="eyebrow">架构师的信源筛选</span><h3>每类来源，回答一个不同的问题</h3><div class="arch-three"><div><b>热点资讯 · 需求变化</b><p>发现新的任务形态、产品约束与成本压力；回到原始发布核对。</p></div><div><b>学术界 · 方法与证据</b><p>读清决策变量、基线、负载和失效边界；再判断是否值得复现。</p></div><div><b>业界 · 工程可用性</b><p>核对版本、接口、部署条件与限制；区分路线参考与昇腾可用能力。</p></div></div><p class="arch-note">vLLM Ascend 是模型服务层的落地参照；元戎等分布式运行时回答任务执行问题。两者不能互相替代，也不单独代表完整 Agent 调度系统。</p></aside>'''

def architecture_overview():
    refs=''.join(f'<li><a href="{e(r["url"])}" target="_blank" rel="noopener noreferrer">{e(r["title"])} ↗</a><p>{e(r["fact"])}。</p><small>{e(r["limit"])}。核对 {r["checked"]}。</small></li>' for r in read('architecture-references.csv'))
    return '''<section id="architecture-boundaries" class="architecture-section"><p class="eyebrow">架构全景 / 先确认职责，再选择算法</p><h2>用任务上下文连接各层，用明确边界避免重复调度</h2><p>以下是本报告建议的职责划分，不是统一行业标准，也不是已经实现的云核系统。研究重点仍是调度；规划、持久化与工具语义是协作边界。</p>
<div class="arch-diagram-scroll" tabindex="0" role="region" aria-label="调度架构职责图，可横向滚动"><svg class="arch-diagram" viewBox="0 0 1120 530" role="img" aria-labelledby="arch-title arch-desc"><title id="arch-title">Agent任务的执行链与调度控制边界</title><desc id="arch-desc">任务约束进入Agent规划和运行时，运行时提交模型或工具调用。调度控制面输出排程、映射、分配。执行状态反馈给控制面，部署控制独立处理模型实例和卡资源。</desc>
<defs><marker id="arch-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#498092"/></marker></defs>
<rect x="12" y="12" width="1096" height="506" rx="20" fill="#f3f8fa" stroke="#d6e3e9"/>
<g fill="#fff" stroke="#bfd5df"><rect x="36" y="60" width="200" height="100" rx="12"/><rect x="284" y="60" width="250" height="100" rx="12"/><rect x="582" y="60" width="246" height="100" rx="12"/><rect x="876" y="60" width="208" height="100" rx="12"/></g>
<g class="arch-svg-title"><text x="54" y="91">任务约束</text><text x="302" y="91">Agent 规划与运行时</text><text x="600" y="91">模型 / 工具服务</text><text x="894" y="91">任务验收</text></g>
<g class="arch-svg-text"><text x="54" y="120">质量 · 期限 · 预算</text><text x="54" y="143">租户 · 权限 · 成功条件</text><text x="302" y="120">生成步骤与依赖，记录状态</text><text x="302" y="143">循环可展开为运行轨迹</text><text x="600" y="120">选择模型 → 副本 → 批次</text><text x="600" y="143">工具队列 → API → 回执</text><text x="894" y="120">结果与约束均达标</text><text x="894" y="143">失败／取消亦记录</text></g>
<g stroke="#498092" stroke-width="2" fill="none" marker-end="url(#arch-arrow)"><path d="M236 110H280"/><path d="M534 110H578"/><path d="M828 110H872"/><path d="M409 164V224"/><path d="M705 224V164"/></g>
<g class="arch-svg-small"><text x="302" y="198">就绪事件与任务约束 ↓</text><text x="727" y="198">执行动作 ↑</text></g>
<rect x="284" y="230" width="800" height="116" rx="14" fill="#173f54"/>
<text x="308" y="259" fill="#c0dde8" font-size="16">调度控制面 · 统一状态与策略边界</text>
<g fill="#fff" font-size="21" font-weight="650"><text x="308" y="297">① 排程：何时做</text><text x="560" y="297">② 映射：交给谁</text><text x="817" y="297">③ 分配：给多少</text></g>
<g fill="#b9d7e3" font-size="14"><text x="308" y="326">依赖与优先级 → 就绪工作</text><text x="560" y="326">资格与代价 → 模型／副本</text><text x="817" y="326">容量与公平 → 预算／额度</text></g>
<rect x="36" y="230" width="200" height="116" rx="12" fill="#e1f0ed" stroke="#abcfc6"/><text x="54" y="261" class="arch-svg-title">可观测与持久化</text><g class="arch-svg-text"><text x="54" y="291">任务／步骤／尝试身份</text><text x="54" y="317">检查点与执行事件</text></g>
<path d="M284 287H240" stroke="#498092" stroke-width="2" fill="none" marker-end="url(#arch-arrow)"/>
<rect x="36" y="404" width="1048" height="82" rx="12" fill="#eeeaf5" stroke="#cfc4e2"/><text x="56" y="434" class="arch-svg-title">部署与资源面</text><text x="56" y="464" class="arch-svg-text">模型实例 / 工具进程 → 节点与卡组 · 显存、算力、网络、CPU、接口配额各自计量</text>
<path d="M950 350V400" stroke="#806a9a" stroke-width="2" stroke-dasharray="6 5" fill="none" marker-end="url(#arch-arrow)"/><text x="672" y="381" class="arch-svg-small">部署 / 扩缩容按事件触发，并非每次请求重新放置</text>
</svg></div><p class="arch-note">上方为任务执行路径，中部为决策职责，底部为承载关系；箭头不表示三个策略必须串行运行。咖啡 DAG 是教学计划，真实 Agent 可能产生动态分支、循环和多 Agent 协作。</p>
<details class="arch-evidence"><summary>查看架构依据与适用边界 · 4 项原始资料</summary><ul>'''+refs+'''</ul></details></section>'''

def topic_contract(area):
    r=next(r for r in rows() if r['area_id']==area)
    fields=[('接入位置','placement'),('必须观测','state'),('允许动作','action'),('关键代价','tradeoff'),('失效回退','fallback'),('验收依据','acceptance')]
    return f'''<article class="architect-lens" id="architecture-contract"><span class="eyebrow">架构决策 / {NAMES[area]}</span><h3>{e(r['question'])}</h3><p><b>何时需要：</b>{e(r['signal'])}。</p><dl class="arch-fields">{''.join(f'<dt>{a}</dt><dd>{e(r[b])}。</dd>' for a,b in fields)}</dl><p class="arch-note">本报告建议：{e(r['priority'])}。下方技术路线解释如何实现，原始证据说明哪些条件已有依据。</p></article>'''

def page_lens(title,areas):
    links=''.join(f'<a href="{BASE}research-{a}.html#architecture-contract">{NAMES[a]}的架构接入 →</a>' for a in areas)
    return f'''<aside class="arch-page-lens"><strong>架构师读本页</strong><span>先明确本层的输入与输出，再比较方法、代价和回退条件；不把局部指标改善直接等同于整任务收益。</span><div>{links}<a href="{BASE}#architecture-boundaries">返回全局职责图 →</a></div></aside>'''

def evidence_lens(key):
    r=next(r for r in read('architecture-evidence-links.csv') if r['publication_id']==key)
    return f'''<aside class="arch-impact"><span>架构影响 · 本报告分析</span><h5>{e(r['decision'])}</h5><p>{e(r['impact'])}。</p><small>{e(r['boundary'])}。</small></aside>'''

def updates_lens():
    return '''<div class="architect-lens compact"><span class="eyebrow">读动态时，带走一个架构问题</span><h3>发生了什么 → 影响哪个决策 → 接入条件是什么</h3><p>每项资料保留原始事实和技术路线，新增“架构影响”解释改哪一层、需要什么条件。影响分析是本报告判断；选型优先级集中在“分析结论”，避免一篇论文直接变成采用建议。</p><p class="arch-note">本次更新覆盖2026-10-17—23日的重点筛选，共4条核验内容；论文仅完成摘要级核验，工程条目核对正式发布说明。既有资料保留原核验日期。</p></div>'''

def decision_review():
    cards=''.join(f'''<article class="arch-decision-card"><span class="eyebrow">{NAMES[r['area_id']]} / 候选方案</span><h3>{e(r['question'])}</h3><dl class="arch-fields"><dt>触发证据</dt><dd>{e(r['signal'])}。</dd><dt>建议次序</dt><dd>{e(r['priority'])}。</dd><dt>不成立时</dt><dd>{e(r['fallback'])}。</dd></dl><a href="{BASE}research-{r['area_id']}.html#architecture-contract">查看接口、代价与验收条件 →</a></article>''' for r in rows())
    return '''<div id="architecture-decisions"><div class="architect-verdict"><span class="eyebrow">当前判断 / 研究建议，尚待实测</span><h3>优先构筑任务级可观测与可插拔策略，再用真实瓶颈决定算法投入</h3><p>现有资料支持“任务上下文、执行状态、资源代价值得联动研究”；尚不足以证明云核应全面替换现有运行时，或同时实施三个方向。最先交付的应是可回放轨迹、统一任务身份和可比较的基线。</p><div class="arch-three"><div><b>现在构筑</b><p>端到端身份与事件、等待归因、SLO与成本口径。</p></div><div><b>有条件验证</b><p>排程、缓存感知路由、公平分配；每次只改明确变量。</p></div><div><b>暂缓扩大</b><p>无瓶颈依据的跨层联合优化，以及未证实收益的共卡策略。</p></div></div><a href="#architecture-diagnosis">按瓶颈选择研究入口 ↓</a></div>
<div id="architecture-diagnosis"><h3>先判断等待在哪里，再决定改哪个控制点</h3><div class="table-scroll"><table><thead><tr><th>观察到的现象</th><th>需要补的证据</th><th>研究入口</th></tr></thead><tbody>
<tr><td>同一任务多轮进入模型队列</td><td>逐步骤排队与服务时间、程序累计服务量；是否造成端到端关键等待</td><td><a href="#analysis-workflow">程序感知排程</a></td></tr>
<tr><td>请求集中到热缓存副本但排队更久</td><td>缓存节省与排队增加的净差、遥测时效、可替代副本状态</td><td><a href="#analysis-mapping">亲和与过载退出</a></td></tr>
<tr><td>并发增加后长任务或共卡时延恶化</td><td>按租户统计服务成本、资源占用、拒绝与尾延迟</td><td><a href="#analysis-sharing">成本公平与资源份额</a></td></tr>
<tr><td>大部分时间等待用户或外部工具</td><td>等待类型、额度、可取消性与结果不确定状态</td><td><a href="'''+BASE+'''runtime-rescheduling.html">运行时与工具控制</a>；不要先归因于卡调度</td></tr>
</tbody></table></div><p class="arch-note">并行步骤的耗时不能直接相加成端到端时延；依赖等待和前驱执行也不能重复计时。按事件重建关键等待链，并区分可优化等待与业务必需等待。</p></div><div class="arch-decision-grid">'''+cards+'''</div>
<details class="arch-evidence" id="architecture-readiness"><summary>昇腾落地前，需要补齐的工程条件</summary><div class="arch-three"><div><b>接入契约</b><p>任务与调用身份关联；提交、取消、完成与失败事件可对齐；记录运行时与接口版本。</p></div><div><b>后端能力</b><p>逐版本核对优先级、取消、抢占、KV管理、并行与计量接口。不能把GPU论文结果视为NPU支持。</p></div><div><b>故障闭环</b><p>外部动作明确幂等键和结果核对；超时未知不直接重试；权限、预算与取消向下传播。</p></div></div><p class="arch-note">这些是建议接入条件，不表示当前演示已实现。模型质量由业务验收负责；持久化不自动提供端到端恰好一次语义。</p></details></div>'''

def archive_entry():
    return '''<article class="archive-record"><span class="eyebrow">2026-10-23 · 架构师阅读版</span><h3>从方法资料集，整理为可讨论的架构决策</h3><p>保留五段主线与三项调度研究方向；补充系统职责图、专题接入契约、19 项资料的架构影响与瓶颈驱动的路线取舍。另核对4项架构依据，不将其计为本月新事件。</p><dl><dt>证据窗口</dt><dd>新增10月17—23日4条精选事实：2篇预印本、2项正式版本。不是全量覆盖；10月16日不在本周窗口中。</dd><dt>维护位置</dt><dd>CCN-insight 主仓库统一维护，原独立站作为发布镜像。尚未配置GitHub自动发布。</dd><dt>结论状态</dt><dd>架构建议与候选研究课题；无新增云核实测结果。</dd></dl><a href="#architecture-decisions">查看当前架构取舍 →</a></article>'''
