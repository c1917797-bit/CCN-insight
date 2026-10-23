"""Persistent publishing channels, distinct from dated publications and claims."""
from html import escape as e
from decision_map import read, BASE

CATEGORIES = [('news', '热点资讯', '发现产品与需求信号，再回到官方原文。'),
              ('industry', '产业界', '按执行层比较工程实现，用昇腾标签筛选落地相关对象。'),
              ('academic', '学术界', '从预印本发现新方法，用会议论文和原始实验核对依据。')]


def registry():
    rows = read('source-channels.csv')
    channels = {r['id']: r for r in rows}
    endpoints = read('source-endpoints.csv')
    provenance = read('publication-source-links.csv')
    coverage = read('source-area-links.csv')
    pubs = {p['id'] for p in read('research-publications.csv')}
    areas = {a['id'] for a in read('research-areas.csv')}
    assert len(channels) == len(rows)
    assert all(r['url'].startswith('https://') and r['category'] in dict((k, t) for k, t, _ in CATEGORIES) for r in rows)
    assert all(p['channel_id'] in channels for p in endpoints + provenance + coverage)
    assert {p['publication_id'] for p in provenance} == pubs
    assert len(provenance) == len(pubs), 'Each item has one primary publishing source'
    assert all(p['area_id'] in areas for p in coverage)
    assert all(c['priority'] in {'core','observe'} for c in rows)
    assert all(c['ecosystem'] in {'ascend','general'} if c['category']=='industry' else not c['ecosystem'] for c in rows)
    assert len({(r['channel_id'],r['url']) for r in endpoints})==len(endpoints)
    assert len({(r['channel_id'],r['area_id']) for r in coverage})==len(coverage)
    assert set(channels)=={r['channel_id'] for r in coverage}
    checks=read('source-coverage.csv')
    check_links=read('source-coverage-links.csv')
    assert all(r['channel_id'] in channels and r['coverage_id'] in {c['id'] for c in checks} for r in check_links)
    assert {r['coverage_id'] for r in check_links}=={c['id'] for c in checks}
    return channels, endpoints, provenance, coverage


def anchor(url, label):
    return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)} ↗</a>'


def origin(publication_id):
    channels, _, provenance, _ = registry()
    source = next(channels[p['channel_id']] for p in provenance if p['publication_id'] == publication_id)
    return f'<a href="{BASE}#channel-{source["id"]}">来源：{e(source["title"])} · 查看持续更新入口 →</a>'


def coverage_view(channels):
    links=read('source-coverage-links.csv')
    rows=[]
    for row in read('source-coverage.csv'):
        selected=[channels[l['channel_id']] for l in links if l['coverage_id']==row['id']]
        refs=' · '.join(f'<a href="#channel-{c["id"]}">{e(c["title"])}</a>' for c in selected)
        rows.append(f'<tr><th scope="row">{e(row["title"])}</th><td>{e(row["question"])}<small>{e(row["boundary"])}</small></td><td>{refs}</td></tr>')
    return '<div id="sources-coverage" class="source-coverage"><h3>先看覆盖：沿任务链路检查研究盲区</h3><p>下列是信源覆盖检查项，三个根技术方向保持不变。信源相互补充，论文按原始标识去重。</p><div class="table-scroll"><table><thead><tr><th scope="col">检查范围</th><th scope="col">要回答的问题</th><th scope="col">重点入口</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></div>'


def directory():
    from source_directory_view import directory as render_directory
    channels,endpoints,provenance,_=registry()
    return render_directory(channels,endpoints,provenance,coverage_view(channels))


def topic_sources(area_ids):
    channels, _, _, coverage = registry()
    chosen = [c for c in channels.values() if c['priority']=='core' and any(r['channel_id'] == c['id'] and r['area_id'] in area_ids for r in coverage)]
    # Keep sources concise here; descriptions live in the source directory.
    return '<div class="topic-source-links"><strong>核心信源</strong>' + ''.join(
        f'<a href="{BASE}#channel-{c["id"]}">{e(c["title"])}</a>' for c in chosen) + f'<a href="{BASE}#sources">全部信源与补充观察 →</a></div>'
