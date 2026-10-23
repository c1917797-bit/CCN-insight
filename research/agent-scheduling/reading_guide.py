"""Shared reading contract and contextual links for every research subpage."""
from html import escape as e
from decision_map import read, BASE
from source_registry import topic_sources
from report_contract import remit, CUTOFF
from architect_view import archive_entry

FLOW = [('sources','信息来源','持续看哪里'), ('map','技术地图','研究什么'),
        ('updates','本期动态','发生什么'), ('analysis','分析结论','如何取舍'),
        ('archive','洞察归档','判断如何积累')]


def overview():
    return '<nav class="reading-flow" aria-label="洞察阅读逻辑">'+''.join(
        f'<a href="{BASE}#{key}"><b><em>0{i} · </em>{title}</b><span>{hint}</span></a>'
        for i, (key,title,hint) in enumerate(FLOW,1))+'</nav>'


def profile(title):
    for a in read('research-areas.csv'):
        if a['title']==title:
            return '根技术专题', '理解长期问题、技术路线与适用边界；先读依据，再比较路线和形成研究建议。', [a['id']]
    for obj in read('research-directions.csv'):
        if obj['title']==title:
            areas=list(dict.fromkeys(r['area_id'] for r in read('area-object-links.csv') if r['point_id']==obj['point_id']))
            return '执行层专题', '说明这一层调度什么、受什么约束、如何选择候选策略；它是根技术的应用场景。', areas
    for d in read('scheduling-decisions.csv'):
        if d['title']==title:
            area={'admission':'sharing','ordering':'workflow','dispatch':'mapping','allocation':'sharing'}[d['id']]
            return '调度决策索引', '围绕一个决策输出梳理方法、适用对象与评价方式，帮助定位相应根技术。', [area]
    if title=='买咖啡的HEFT调度案例':
        return '算法教学案例', '从构造输入复算调度过程，帮助理解HEFT；模拟结果不作为真实系统的性能结论。', ['workflow','mapping']
    if title=='调度输入与验收边界':
        return '研究范围说明', '明确上游输入、完成条件与指标口径，为各调度专题提供共同约束。', []
    raise ValueError(f'Missing page purpose: {title}')


def context(title):
    role, purpose, areas=profile(title)
    return f'<div class="page-context" aria-label="专题位置与证据时点"><a href="{BASE}#map">技术地图</a><span aria-hidden="true"> / </span><strong>{e(role)}</strong><small>证据截至 {CUTOFF}</small></div>'


def related(title):
    _, _, areas=profile(title)
    names={a['id']:a['title'] for a in read('research-areas.csv')}
    links=''.join(f'<a href="{BASE}research-{a}.html">{e(names[a])} →</a>' for a in areas)
    # This is navigation by research area, not an assertion that every item applies to every execution layer.
    return f'''<section id="reading-connections" class="reading-connections"><h2>继续研究</h2>
<p>从本页方法出发，追踪原始资料与跨路线取舍。</p>
<div class="topic-source-links"><strong>关联根技术</strong>{links or f'<a href="{BASE}#north-star">任务达标完成率与统计口径 →</a>'}</div>
{topic_sources(areas) if areas else ''}<div class="reading-next"><a href="{BASE}#updates">查看本期动态与原始依据 →</a><a href="{BASE}#analysis">查看跨路线判断 →</a></div></section>'''


def archive():
    from source_registry import registry
    channels=registry()[0]
    pubs=read('research-publications.csv')
    academics=8  # Fixed historical count for the 2026-10-14 record, not today's collection.
    return f'''<section id="archive"><p class="eyebrow">05 / 洞察归档</p><h2>保留研究过程，追踪判断变化</h2>
<p>从2026年10月开始积累。正式报告、路线结论与整理记录分别标注，尚未定稿的工作不作为正式月报。</p>
{archive_entry()}<article class="archive-record"><span class="eyebrow">2026-10-15 · 团队研究体系</span><h3>围绕三项核心技术积累可复用竞争力</h3><p>统一依赖感知排程、状态感知映射与干扰感知分配；补充算法输入输出、方法、阶段验收和共用底座。新增 Murakkab 会议摘要级依据，保留既有资料核对日期。本版是研究规划，未宣称实现领先收益。</p><a href="#analysis">查看建设路径 →</a></article><article class="archive-record"><span class="eyebrow">2026-10-14 · 信源目录整理</span><h3>区分来源身份、执行层次与研究关联</h3><p>当前登记{len(channels)}个持续信源。补入元戎与InfoQ；产业界按四个执行层组织，跨层工程观察单列。每张卡说明定位、选择理由、关注内容与适用边界，昇腾相关作为独立筛选标签。</p><p>这是目录调整，未新增已核验的论文或发布事件。原有8篇论文与6项官方资料的证据归属保持不变。</p></article>
<article class="archive-record"><span class="eyebrow">2026-10-13 · 资料整理记录</span><h3>明确证据用途、时间窗口与路线决策条件</h3>
<dl><dt>当时范围</dt><dd>23个持续信源，8篇论文与6项官方实现资料，关联三个根技术方向。</dd><dt>当时调整</dt><dd>逐项标注14份资料的复核范围，说明28条路线关联，补充3个研究方向的继续与调整条件；统一22页的阅读目录和证据边界。</dd><dt>研究状态</dt><dd>新增信源待继续筛选内容，尚未形成正式月度报告，也没有云核实测路线结论。</dd></dl>
<p><a href="{BASE}#updates">查看当前证据集 →</a> · <a href="{BASE}#analysis">查看当前研究判断 →</a></p>
<p class="note">以上链接指向持续更新的工作页，并非历史快照。正式定稿后再保存固定版本与结论变更记录。</p></article></section>'''
