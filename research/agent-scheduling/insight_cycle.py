"""Reader-facing traceability from recurring sources to dated decision reviews."""
from html import escape as e
from urllib.parse import urlsplit
import re
from decision_map import read, BASE
from report_contract import CUTOFF

AREAS={'workflow':'依赖感知排程','mapping':'状态感知映射','sharing':'干扰感知分配'}

def covered_channels(provenance):
    """Count verified discovery chains without treating media as primary evidence."""
    accepted={r['id'] for r in read('research-publications.csv')}
    return {r['channel_id'] for r in provenance} | {r['channel_id'] for r in read('publication-discovery-links.csv') if r['publication_id'] in accepted}

def canonical(url):
    p=urlsplit(url)
    match=re.search(r'(\d{4}\.\d{4,5})(?:v\d+)?',p.path)
    if p.hostname and 'arxiv.org' in p.hostname and match:return 'arxiv:'+match[1]
    return (p.netloc.lower()+p.path.rstrip('/')).removesuffix('.html')

def collection_state():
    runs=read('collection-runs.csv')
    latest={r['feed_id']:r for r in runs}
    candidates=read('signal-candidates.csv')
    accepted={canonical(r['url']) for r in read('research-publications.csv')}
    pending=[r for r in candidates if canonical(r['url']) not in accepted and r['review_status']=='待原文审阅']
    return list(latest.values()),pending

def source_overview(channels,provenance):
    runs,pending=collection_state()
    populated=covered_channels(provenance)
    checks=read('source-checks-20261023.csv')
    checked={r['channel_id'] for r in checks}
    stats=[(f'{len(channels)}','持续信源','三类总表，按发布角色管理'),
           (f'{len(populated)}/{len(channels)}','已形成核验记录','含媒体线索追溯；事实以原文为准'),
           (f'{len(checked)}/{len(channels)}','本轮人工核查','包括失败记录；不代表全量扫读'),
           (f'{len(pending)}','机器筛选候选','标题与关键词命中，尚未成为事实')]
    cells=''.join(f'<div class="signal-stat"><strong>{value}</strong><span>{label}</span><small>{note}</small></div>' for value,label,note in stats)
    return f'''<details class="insight-loop"><summary>从信源到决策：这份目录如何使用</summary><p>优先看工作流与执行引擎，再按问题下钻模型服务和设备资源。信源代表发布角色；调度关联说明它能帮助回答什么。</p><ol><li><strong>持续来源</strong><span>稳定入口与更新渠道</span></li><li><strong>原文核验</strong><span>日期、机制、条件与边界</span></li><li><strong>研究归属</strong><span>排程、映射与资源分配</span></li><li><strong>决策复核</strong><span>改变什么，何时重新判断</span></li></ol><p class="source-health">本轮核查 {CUTOFF} · 支持按需抓取公开候选，当前未设置定时采集。采集成功不等于内容已核验；没有新条目也不代表没有进展。<a href="#source-monitor">查看覆盖与待补缺口 →</a></p></details><div class="coverage-strip">{cells}</div>'''

def source_health(channel_id,selected):
    runs,_=collection_state()
    checks=[r for r in read('source-checks-20261023.csv') if r['channel_id']==channel_id]
    feeds=[r for r in runs if r['channel_id']==channel_id]
    status='已有核验资料' if selected else '待筛选具体内容'
    collection=max((r['checked_at'][:10] for r in feeds),default='未接入候选采集')
    checks_html=''.join(f'<li><a href="{e(r["url"])}" target="_blank" rel="noopener noreferrer">{e(r["check_type"])} ↗</a> · {e(r["checked"])}<p>{e(r["result"])} {e(r["boundary"])}</p></li>' for r in checks)
    log='<ul class="source-check-log">'+checks_html+'</ul>' if checks else '<p>本轮未人工复核该来源；沿用其原有核对记录。</p>'
    return status,collection,log

def monitoring(channels,provenance):
    runs,pending=collection_state()
    reached=covered_channels(provenance)
    gaps=[c for c in channels.values() if c['priority']=='core' and c['id'] not in reached]
    latest=max((r['checked_at'] for r in runs),default='未运行')
    rows=''.join(f'<li><strong>{e(channels[r["channel_id"]]["title"])}</strong> · {e(r["status"])} · 读取 {r["fetched"]} 条，窗口内 {r["in_window"]} 条，关键词候选 {r["matched"]} 条<p>{e(r["scope"])}；尝试 {r["attempts"]} 次。{e(r["error"]) if r["error"] else "未做全文自动判断。"}</p></li>' for r in runs)
    gap_links=' · '.join(f'<a href="#channel-{c["id"]}">{e(c["title"])}</a>' for c in gaps)
    return f'''<details id="source-monitor" class="source-policy"><summary>持续跟踪与覆盖缺口 · {len(runs)} 个采集入口</summary><p>最近一轮 {e(latest)}（UTC）。公开列表仅用于发现候选，保留日期、版本和来源标识，按原始网址／论文标识去重。待审候选 {len(pending)} 条不计入已核验资料数。</p><ul class="collection-log">{rows}</ul><h4>核心来源仍待转化为具体研究依据</h4><p>{gap_links or "当前核心来源均有至少一条资料；仍不代表全面覆盖。"}</p><p>下一轮按缺口补读：先找会改变路线选择的机制、版本限制或反例。无法读取时保留失败原因，原文未确认时保持待审；不以转载或模型推测填空。</p><p>每次更新先审候选并核对原文，再关联专题和决策，最后构建发布。此页面是已发布的阅读快照；采集程序未自动发布，也未配置每日运行。</p></details>'''

def verified_additions():
    pubs={p['id']:p for p in read('research-publications.csv')}
    findings={p['publication_id']:p for p in read('research-findings.csv')}
    rows=read('evidence-batch-20261023.csv')
    cards=''.join(f'''<article class="signal-card"><span class="evidence-confidence" data-kind="fact">{e(r['label'])}</span><h4><a href="#publication-{r['publication_id']}">{e(findings[r['publication_id']]['headline'])}</a></h4><p>{e(r['decision_delta'])}</p><small>原文：{e(pubs[r['publication_id']]['published'] or '无明确发布日期')} · 本轮核验：{pubs[r['publication_id']]['checked']}</small><a href="#publication-{r['publication_id']}">读机制与适用条件 →</a></article>''' for r in rows)
    return f'''<div id="updates-verified" class="verified-batch"><p class="eyebrow">本轮补充核验 / {CUTOFF}</p><h3>把工作流、执行映射与工具准入的盲区补齐</h3><p>以下 {len(rows)} 项是本轮新核验的资料，不等于近一周新发布。日期按原始事件保留；无发布日期的机制文档单独标注。</p><div class="monitor-board">{cards}</div></div>'''

def decision_changes():
    rows=read('decision-watchlist.csv')
    pubs={p['id']:p for p in read('research-publications.csv')}
    cards=[]
    for r in rows:
        citations=' · '.join(f'<a href="{BASE}#publication-{k}">{e(pubs[k]["short"])}</a>' for k in r['publication_ids'].split('|'))
        cards.append(f'''<article class="decision-change" id="watch-{r['id']}"><span class="evidence-confidence" data-kind="inference">研究判断 · {r['reviewed']}</span><h4>{e(r['question'])}</h4><p><strong>当前取舍：</strong>{e(r['position'])}</p><dl><dt>这轮改变了什么</dt><dd>{e(r['change'])}</dd><dt>值得投入的条件</dt><dd>{e(r['trigger'])}</dd><dt>什么证据会推翻它</dt><dd>{e(r['reversal'])}</dd></dl><p>依据：{citations}</p><small>复核触发：{e(r['review_trigger'])}；最迟建议复核 {r['review_due']}。尚非已实施方案。</small></article>''')
    return '<section id="decision-watchlist" class="decision-brief"><p class="eyebrow">决策观察 / 事实之后给出取舍</p><h3>本轮哪些判断需要调整</h3><p>把新事实变成有条件的投入建议，并写清什么时候应改主意。优先级由业务瓶颈决定，不按论文名气或发布频率排序。</p>'+''.join(cards)+'</section>'

def discovery_note(key):
    rows=[r for r in read('publication-discovery-links.csv') if r['publication_id']==key]
    return ''.join(f'<p class="publication-discovery">发现线索：<a href="{e(r["url"])}" target="_blank" rel="noopener noreferrer">{e(r["channel_id"])} 报道 ↗</a> · {e(r["published"])}；事实依据以上方原始发布为准。</p>' for r in rows)

def archive_delta():
    return '''<article class="archive-record"><span class="eyebrow">2026-10-23 · 来源到决策闭环</span><h3>补齐执行层依据，记录何时需要改判断</h3><p>补充 Temporal、Ray、元戎和工具准入的官方依据；来源目录保持三张总表。新增按需公开候选采集、去重、失败记录与决策复核条件。本轮内容补录与原始事件日期分开，不计作全量覆盖。</p><a href="#updates-verified">本轮核验 →</a> · <a href="#decision-watchlist">判断变化 →</a></article>'''
