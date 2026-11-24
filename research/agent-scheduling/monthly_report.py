"""Monthly editorial synthesis over normalized primary-source records."""
from html import escape as e
from decision_map import read, BASE
from report_contract import START, CUTOFF


def selection():
    pubs = {r['id']: r for r in read('research-publications.csv')}
    rows = [r for r in read('monthly-selection.csv') if r['period'] == START[:7]]
    assert rows and len({r['publication_id'] for r in rows}) == len(rows)
    assert all(START <= pubs[r['publication_id']]['published'] <= CUTOFF for r in rows)
    return pubs, rows


def month_guide():
    pubs, rows = selection()
    counts = {k:sum(pubs[r['publication_id']]['kind']==k for r in rows) for k in ('academic','industry','news')}
    return f'''<div class="month-guide" id="month-reading"><span class="eyebrow">2026年11月 · 截至11月24日</span><h3>从任务链、缓存位置和活跃预算，读懂本月变化</h3>
<p>本轮精选 {len(rows)} 项：{counts['academic']} 篇预印本、{counts['industry']} 项官方工程进展、{counts['news']} 项官方发布事件。先读可核对的事实，再到分析结论判断研究优先级。</p>
<nav aria-label="十一月阅读目录"><a href="#updates-academic-current">学术方法 · 4篇</a><a href="#updates-industry-current">工程进展 · 4项</a><a href="#updates-news-current">热点事件 · 1项</a><a href="#november-insight">本月综合判断</a></nav>
<p class="note">这是截至24日的人工精选增量，不是11月完整月报，也不声称覆盖所有信源。4篇论文为预印本；原文指定章节已核对，未独立复现。来源目录中其余入口保留各自真实核验日期。</p></div>'''


def monthly_synthesis():
    return '''<div class="month-report" id="november-insight"><span class="eyebrow">2026年11月调度洞察 / 研究判断，待实验检验</span>
<h3>研究重点：从单次调用提速，推进到多轮任务的稳定完成</h3>
<p class="month-thesis">本月材料共同提示：调度器需要知道任务进度、可复用状态和活跃工作集。建议先建立任务级观测与回放，再用缓存预算守住稳定性，随后比较排程与公平策略的净收益。</p>
<div class="month-judgments">
<article><span>依赖感知排程</span><h4>工具槽位也要看整项任务</h4><p>CAAS把任务接纳和工具执行容量分开，在到达保护下推进已显露的长链。值得研究的是任务进度怎样跨模型与工具队列传递；在线业务仍需补测期限与浅链等待。</p><a href="#publication-caas">CAAS机制与单项对照</a></article>
<article><span>状态感知映射</span><h4>缓存更多，不等于净收益更大</h4><p>昇腾RC提供亲和与缓存配套候选，llm-d给出L2/L3不同取舍。应以排队、回载和恢复的净代价选副本，稳态性能与故障韧性分别付账。</p><a href="#publication-llmd-sglang-tiered-nov">分层缓存的正反证据</a></article>
<article><span>干扰感知分配</span><h4>先恢复稳定，再优化公平</h4><p>缓存亚稳态暴露“限新流量仍不恢复”的风险；Duru与Fairway进一步约束效率对长任务的伤害。先能控制活跃集合，再引入可信的公平信号，避免叠加多个未经归因的策略。</p><a href="#publication-prefix-metastability">过载恢复的对照依据</a></article>
</div>
<div class="month-priorities"><h4>建议的穿刺顺序 · 按已观测瓶颈选用</h4><ol>
<li><strong>先做工作集预算：</strong>若突发后缓存命中和积压不能恢复，优先验证缓存亚稳态论文；对照仅入口限流。</li>
<li><strong>再做任务链推进：</strong>若模型/工具交替等待主导批长尾，穿刺CAAS；容量解耦和排序分别消融。</li>
<li><strong>最后做跨层公平：</strong>若稳定后仍有长任务或租户明显受损，再研究Duru；Fairway作为实例队列对照，llm-d Async作为配额工程基线。</li>
</ol><p>以上是条件化研究顺序，不是论文质量排名。只有纯服务层排队问题时，可直接从Fairway开始；若瓶颈是工具不可用或用户授权，优先处理业务约束。</p></div>
<details class="month-boundaries"><summary>本月未形成结论的方向</summary><p>语义选模型、多模型共卡、跨设备放置仍保留在技术地图；本轮没有足够同条件的新证据更新其性能判断。元戎、工作流运行时及其他既有信源未完成11月逐项扫描，不把“本轮未入选”写成“本月没有进展”。</p><p>近七日精选与整月新增分开。厂商发布只确认事件或接口；GPU论文和项目基准均不能直接代表昇腾收益。所有本地性能建议仍需固定模型质量、轨迹、硬件和资源预算验收。</p></details></div>'''


def october_history():
    rows = read('history/2026-10/analysis-recommendations.csv')
    names = {'workflow':'依赖感知排程','mapping':'状态感知映射','sharing':'干扰感知分配'}
    cards = ''.join(f'<article><h4>{e(names[r["area_id"]])} · {e(r["title"])}</h4><p>{e(r["judgment"])}</p><p><strong>当时穿刺对象：</strong>{e(r["verification_subject"])}</p></article>' for r in rows)
    return f'''<article class="archive-record" id="november-archive"><span class="eyebrow">2026-11-24 · 11月增量 v1</span><h3>9项新证据，关联三项调度根技术</h3><p>4篇预印本、4项官方工程进展和1项发布事件；每项保留日期、版本、原文位置、结果条件和未核实边界。新增4个来源核查记录，其他来源沿用原日期。当前累计34项资料；11月剩余日期尚未发生，后续继续补充。</p><a href="#month-reading">阅读本月事实</a> · <a href="#november-insight">阅读综合判断</a></article>
<details class="archive-record" id="october-judgments"><summary>2026年10月 · 当时的三项研究判断</summary><p>以下从10月建议表保留，不因11月更新改写；不是11月结论，也不是已完成实验。完整源记录保存在主仓 history/2026-10。</p>{cards}</details>'''
