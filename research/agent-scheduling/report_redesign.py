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
<p class="report-question">让架构选择有依据，<br class="desktop-break">让调度研究形成可复用能力。</p>
<p class="report-intro">面向 Agent 架构师，围绕<strong>任务如何推进、服务如何选择、资源如何共享</strong>组织证据与研究。以整任务达标完成为目标，回答改哪一层、为什么改、接入代价是什么，以及怎样验证；昇腾是重点落地平台。</p>
<nav class="arch-hero-links" aria-label="架构师阅读入口"><a href="#architecture-boundaries">先看系统与职责</a><a href="#updates">再读事实与变化</a><a href="#architecture-decisions">最后看路线取舍</a></nav>
<div class="report-metadata"><a href="#sources"><b>{len(registry()[0])}</b> 持续信源</a><a href="#research-directions"><b>{len(read('research-areas.csv'))}</b> 核心技术</a><a href="#updates"><b>{len(pubs)}</b> 累计资料</a><a href="#updates-new"><b>{current}</b> 本期首发／修订</a></div>
<div class="report-opening"><small>架构编排更新 2026-10-23 · 动态证据窗口 {START}—{CUTOFF} · {len(pubs)} 项为累计整理资料，包含本期条目；人工精选，未接入实测。</small></div>
</header>'''
