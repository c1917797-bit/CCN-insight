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
    map_nav = '<p class="rail-note">技术地图</p><nav aria-label="技术地图阅读">'+''.join(f'<a href="{BASE}#{key}">{label}</a>' for key,label in [('research-directions','研究方向'),('research-comparison','比较口径'),('research-reading','重点深读'),('architecture-boundaries','系统边界'),('north-star','评价指标'),('coffee-task','咖啡全景')])+'</nav>'
    if page_nav: map_nav=page_nav
    body=body.replace('class="table-scroll"', 'class="table-scroll" tabindex="0" role="region" aria-label="横向滚动表格"')
    page_kind='index' if title=='Agent端到端调度' else 'topic'
    description = 'Agent调度技术研究：依赖感知排程、状态感知映射与干扰感知分配。原始证据、机制分析和昇腾落地研究分别说明。'
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{description}"><meta name="theme-color" content="#0c2538"><title>{escape(title)} · 云核研究预览</title><link rel="stylesheet" href="{BASE}draft.{css_version}.css"><script defer src="{BASE}draft.{js_version}.js"></script></head><body data-page-kind="{page_kind}"><a class="skip-link" href="#main-content">跳到正文</a><div class="reading-progress" aria-hidden="true"><span></span></div><aside class="rail"><a class="brand" href="{BASE}"><span class="brand-symbol" aria-hidden="true">◈</span> 云核 / 调度研究</a><p class="rail-note">AGENT SCHEDULING<br>任务 · 服务 · 资源</p><nav aria-label="阅读路径"><a data-nav-scope="primary" href="{BASE}#sources">01 信息来源</a><a data-nav-scope="primary" href="{BASE}#map">02 技术地图</a><a data-nav-scope="primary" href="{BASE}#updates">03 本期动态</a><a data-nav-scope="primary" href="{BASE}#analysis">04 分析结论</a><a data-nav-scope="primary" href="{BASE}#archive">05 洞察归档</a></nav>{map_nav}<div class="private-note"><strong>独立只读预览</strong><p>持链接者可访问，未加入首页导航。文献事实、研究判断与教学演示分别标注。</p></div></aside><main id="main-content" tabindex="-1">{body}</main><footer>架构编排 · 2026-10-23 · 动态证据截至 2026-10-23 · 人工整理与发布 · 尚无云核实测结论</footer></body></html>'''

def home():
    from report_redesign import report_header
    body = report_header()+source_directory()+f'<section id="map"><p class="eyebrow">02 / 技术地图</p>{render_research_map()}</section>'+updates()+analysis()+archive()
    return shell('Agent端到端调度', body)

if __name__ == '__main__':
    from sync_direction_model import sync
    sync()
    folder = ROOT / BASE.lstrip('/')
    folder.mkdir(parents=True, exist_ok=True)
    css_file = folder / 'draft.css'
    base_css = (HERE/'templates/base.css').read_text(encoding='utf-8')
    styles = [HERE/name for name in ('map-styles.css','map-animation-styles.css','map-console-styles.css','direction-styles.css','pyramid-styles.css','literature-styles.css','source-styles.css','page-structure-styles.css','compression-source-styles.css','coffee-scene.css','team-strategy.css','report-redesign.css','architect-view.css','source-table.css','expert-console.css')]
    css_file.write_text(base_css+'\n'+'\n'.join(p.read_text(encoding='utf-8') for p in styles), encoding='utf-8')
    js_file=folder/'draft.js'
    marker='/* Source directory controls: progressive enhancement of the complete HTML registry. */'
    js_file.write_text((HERE/'templates/base.js').read_text(encoding='utf-8')+'\n'+(HERE/'source-controls.js').read_text(encoding='utf-8')+'\n'+(HERE/'coffee-engine.js').read_text(encoding='utf-8')+'\n'+(HERE/'coffee-scene.js').read_text(encoding='utf-8'),encoding='utf-8')
    with js_file.open('a',encoding='utf-8') as js:
        js.write('\n'+(HERE/'report-navigation.js').read_text(encoding='utf-8'))
        js.write('\n'+(HERE/'expert-reading.js').read_text(encoding='utf-8'))
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
    from deep_readings import pages, ASSET_FILES
    for name in ASSET_FILES:
        dest=folder/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((HERE/name).read_bytes())
    for name, content in pages(shell).items():
        (folder/name).write_text(content,encoding='utf-8')
    print('Built 3 main research topics, retained all decision/object references and coffee case; 23 pages, selected primary-source reading included.')
