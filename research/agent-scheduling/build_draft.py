from pathlib import Path
from hashlib import sha256
from literature_view import updates, source_directory, analysis
from html import escape
from architecture_map import render as render_map
from direction_pages import directions, map_cards, topic, boundary_page, ALIASES
from decision_map import decision_model, decision_page
from research_map import render_research_map, research_model, research_page
from reading_guide import overview, context, related, archive
from page_structure import structure

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'site'
BASE = '/business_insight/cloud_core/agent_orchestration/'

def shell(title, body):
    assets = ROOT / BASE.lstrip('/')
    css_version = sha256((assets / 'draft.css').read_bytes()).hexdigest()[:12]
    js_version = sha256((assets / 'draft.js').read_bytes()).hexdigest()[:12]
    (assets / f'draft.{css_version}.css').write_bytes((assets / 'draft.css').read_bytes())
    (assets / f'draft.{js_version}.js').write_bytes((assets / 'draft.js').read_bytes())
    page_nav=''
    if title == 'Agent端到端调度':
        body = body.replace('</header>', '</header>'+overview(), 1)
    else:
        body,page_nav=structure(title,body)
        body = body.replace('</header>', '</header>'+context(title), 1)+related(title)
    map_nav = '<p class="rail-note">技术地图</p><nav aria-label="技术地图阅读">'+''.join(f'<a href="{BASE}#{key}">{label}</a>' for key,label in [('architecture-boundaries','架构全景'),('research-directions','核心技术'),('scheduling-essence','调度本质'),('north-star','目标指标'),('runtime-loop','共用底座'),('coffee-task','全景演示')])+'</nav>'
    if page_nav: map_nav=page_nav
    body=body.replace('class="table-scroll"', 'class="table-scroll" tabindex="0" role="region" aria-label="横向滚动表格"')
    page_kind='index' if title=='Agent端到端调度' else 'topic'
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · 云核私有草稿</title><link rel="stylesheet" href="{BASE}draft.{css_version}.css"><script defer src="{BASE}draft.{js_version}.js"></script></head><body data-page-kind="{page_kind}"><a class="skip-link" href="#main-content">跳到正文</a><aside class="rail"><a class="brand" href="{BASE}">云核 / 研究草稿</a><p class="rail-note">Agent端到端调度</p><nav aria-label="阅读路径"><a data-nav-scope="primary" href="{BASE}#sources">01 信息来源</a><a data-nav-scope="primary" href="{BASE}#map">02 技术地图</a><a data-nav-scope="primary" href="{BASE}#updates">03 本期动态</a><a data-nav-scope="primary" href="{BASE}#analysis">04 分析结论</a><a data-nav-scope="primary" href="{BASE}#archive">05 洞察归档</a></nav>{map_nav}<div class="private-note"><strong>本地私有预览</strong><p>仅监听127.0.0.1。调度研究草稿，未发布到线上。</p></div></aside><main id="main-content" tabindex="-1">{body}</main><footer>架构编排 · 2026-10-23 · 动态证据截至 2026-10-23 · 来源机制／设计建议／教学演示分别说明 · 尚未接入TableGit</footer></body></html>'''

def home():
    research = render_research_map()
    map_html = research + '<details id="demo-section" class="demo-disclosure"><summary>咖啡演示 · 看调度决策如何作用于实际流程</summary>'+render_map()+'</details>'
    body = f'''<header class="hero"><p class="eyebrow">业务洞察 / 云核 / Agent端到端调度</p><span class="badge">私有草稿 · 调度技术研究</span><h1>构筑可积累的根技术，<br>提升 Agent 调度竞争力。</h1><p class="lead">面向云核团队的长期研究：以昇腾为重点落地平台，构筑依赖感知排程、状态感知映射与干扰感知分配。以真实任务证据推动路线取舍。</p>
<div class="objective-primary"><span>主指标 · 越高越好</span><strong>端到端任务有效吞吐</strong><p>观察窗口内质量、时限、成本同时达标的完成任务数 ÷ 窗口秒数</p><small>一个原始任务只计一次；超时、超预算、执行失败及容量拒绝均不能算达标。</small></div>
<div class="objective-metrics" aria-label="调度配套指标"><article><span>体验 · 秒</span><h2>P95 完成时延</h2><p>成功任务端到端耗时的第95百分位；超时率、失败率另报。</p></article><article><span>质量 · 百分比</span><h2>达标完成率</h2><p>同批次达标任务占比，计入容量拒绝、失败与超时。</p></article><article><span>效率 · 成本/任务</span><h2>单位达标成本</h2><p>同批次全部尝试成本 ÷ 达标任务数，包含失败与重试。</p></article></div>
<p class="objective-note">指标定义已明确，尚未接入实测；目标值需按业务SLO设定。<a href="#north-star">查看验收条件与统计口径 →</a></p><div class="hero-actions"><a class="button" href="#scheduling-decisions">查看调度技术地图</a><a class="button secondary" href="#updates">阅读近期论文与实现</a><a class="button secondary" href="#agent-demo">播放调度演示</a></div></header>
<details class="status-card draft-disclosure" id="draft-status"><summary>草稿状态与验证范围</summary><p>主地图突出三个研究方向，每个方向有独立专题、技术路线和原始依据。原决策矩阵及执行层专题保留为辅助索引；三个方向是研究组织框架，不宣称为行业标准。咖啡动画是教学演示，尚未完成真实并发和故障实验。</p><div class="status-grid"><span>业务归属 <strong>云核</strong></span><span>研究范围 <strong>任务全流程调度</strong></span><span>访问方式 <strong>本机私有预览</strong></span></div></details>
{source_directory()}
<section id="map"><p class="eyebrow">02 / 技术地图</p>{map_html}</section>
{updates()}
{analysis()}
{archive()}'''
    from report_redesign import report_header
    body=report_header()+body[body.index('</header>')+len('</header>'):]
    return shell('Agent端到端调度', body)

if __name__ == '__main__':
    from sync_direction_model import sync
    sync()
    folder = ROOT / BASE.lstrip('/')
    folder.mkdir(parents=True, exist_ok=True)
    css_file = folder / 'draft.css'
    base_css = (HERE/'templates/base.css').read_text(encoding='utf-8')
    styles = [HERE/name for name in ('map-styles.css','map-animation-styles.css','map-console-styles.css','direction-styles.css','pyramid-styles.css','literature-styles.css','source-styles.css','page-structure-styles.css','compression-source-styles.css','coffee-scene.css','team-strategy.css','report-redesign.css','architect-view.css','source-table.css')]
    css_file.write_text(base_css+'\n'+'\n'.join(p.read_text(encoding='utf-8') for p in styles), encoding='utf-8')
    js_file=folder/'draft.js'
    marker='/* Source directory controls: progressive enhancement of the complete HTML registry. */'
    js_file.write_text((HERE/'templates/base.js').read_text(encoding='utf-8')+'\n'+(HERE/'source-controls.js').read_text(encoding='utf-8')+'\n'+(HERE/'coffee-engine.js').read_text(encoding='utf-8')+'\n'+(HERE/'coffee-scene.js').read_text(encoding='utf-8'),encoding='utf-8')
    with js_file.open('a',encoding='utf-8') as js: js.write('\n'+(HERE/'report-navigation.js').read_text(encoding='utf-8'))
    (folder/'index.html').write_text(home(),encoding='utf-8')
    rows,algorithms = directions()
    by_key = {r['key']:r for r in rows}
    for row in rows:
        (folder/(row['key']+'.html')).write_text(topic(shell,row,algorithms),encoding='utf-8')
    for old,new in ALIASES.items():
        (folder/(old+'.html')).write_text(topic(shell,by_key[new],algorithms,legacy=True),encoding='utf-8')
    (folder/'acceptance.html').write_text(boundary_page(shell),encoding='utf-8')
    for decision in decision_model()[0]:
        (folder/('decision-'+decision['id']+'.html')).write_text(decision_page(shell,decision),encoding='utf-8')
    for area in research_model()[0]:
        (folder/('research-'+area['id']+'.html')).write_text(research_page(shell,area),encoding='utf-8')
    from coffee_heft import render
    (folder/'heft-coffee.html').write_text(render(shell),encoding='utf-8')
    print('Built 3 main research topics, retained all decision/object references and coffee case; 22 pages, private only.')
