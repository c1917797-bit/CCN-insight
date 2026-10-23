"""Reader-facing overview computed from the same curated records as the report."""
from decision_map import read
from report_contract import START, CUTOFF

def report_header():
    from literature_view import model, period_kind
    from source_registry import registry
    pubs=model()[0]
    current=sum(period_kind(p) in ('本期首发','本期修订') for p in pubs.values())
    return f'''<header class="hero report-hero" id="report-top">
<div class="report-kicker"><span>云核 / 技术研究</span><span>研究预览 · 截至 {CUTOFF}</span></div>
<h1>Agent 调度研究报告</h1>
<p class="report-question">提升整任务有效吞吐，<br class="desktop-break">把排程、映射与分配做成可验证的技术能力。</p>
<p class="report-intro">面向 Agent 架构师与调度研究者，以<strong>依赖感知排程、状态感知映射、干扰感知分配</strong>连接任务、模型／工具服务与卡资源。先辨认关键等待和资源约束，再读机制、结果与代价，形成面向昇腾的研究取舍。</p>
<nav class="arch-hero-links" aria-label="架构师阅读入口"><a href="#architecture-boundaries">先看系统与职责</a><a href="#updates">再读事实与变化</a><a href="#architecture-decisions">最后看路线取舍</a></nav>
<div class="report-metadata"><a href="#sources"><b>{len(registry()[0])}</b> 持续信源</a><a href="#research-directions"><b>{len(read('research-areas.csv'))}</b> 核心技术</a><a href="#updates"><b>{len(pubs)}</b> 累计资料</a><a href="#updates-new"><b>{current}</b> 本期首发／修订</a></div>
<div class="report-opening"><small>研究快照 {CUTOFF} · 本期窗口 {START}—{CUTOFF} · 累计 {len(pubs)} 项论文与官方资料 · 人工精选，云核实验尚待开展。</small></div>
</header>'''
