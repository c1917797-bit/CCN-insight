"""Source identities, execution layers and research questions are separate axes."""
from html import escape as e
from urllib.parse import urlsplit
from decision_map import read, BASE
from architect_view import source_lens

CATEGORIES=[('news','热点资讯'),('industry','产业界'),('academic','学术界')]
INDUSTRY_GROUPS=['工作流层','分布式执行层','模型服务层','集群资源层','跨层工程观察']
GROUP_HELP={
 '工作流层':'依赖如何推进，长任务如何等待与恢复？',
 '分布式执行层':'任务和实例交给谁、放在哪里？',
 '模型服务层':'模型请求怎样路由、排队和组批？',
 '集群资源层':'哪些工作可以进入，服务部署到哪些设备？',
}
ROLES={
 'news':('发现变化','产品与工程报道帮助发现线索；形成技术判断前追溯原始发布。'),
 'industry':('核对实现','按执行层查看官方项目和文档；再用昇腾标签筛选落地相关对象。'),
 'academic':('研究方法','按研究社区查论文；区分预印本、同行评审与理论假设。'),
}
AREAS={'workflow':'依赖感知排程','mapping':'状态感知映射','sharing':'干扰感知分配'}

def directory(channels,endpoints,provenance,coverage_html):
    pubs={p['id']:p for p in read('research-publications.csv')}
    profiles={p['channel_id']:p for p in read('source-profile.csv')}
    assert set(profiles)==set(channels), 'Every source needs an entry type and evidence role'
    links=read('source-area-links.csv')
    tabs=''.join(f'<button type="button" role="tab" id="source-tab-{key}" data-source-tab="{key}" aria-controls="channel-cards" aria-selected="{str(key=="news").lower()}" tabindex="{0 if key=="news" else -1}">{label}</button>' for key,label in CATEGORIES)
    def row(c):
        profile=profiles[c['id']]
        selected=[pubs[l['publication_id']] for l in provenance if l['channel_id']==c['id']]
        extra=list({r['url']:r for r in endpoints if r['channel_id']==c['id'] and r['url']!=c['url']}.values())
        status=f'已收录内容 · {len(selected)} 项' if selected else '已登记入口 · 内容待筛选'
        checks=f'内容核对 {max(p["checked"] for p in selected)}' if selected else '内容筛选尚未完成；尚未筛选收录具体进展。'
        items='<details class="channel-items"><summary>已收录内容 · '+str(len(selected))+'</summary><ul>'+''.join(f'<li><a href="{BASE}#publication-{p["id"]}">{e(p["short"])} · {e(p["published"] or "能力文档")}</a></li>' for p in selected)+'</ul></details>' if selected else ''
        more='<details class="source-family-entries"><summary>相关关注入口 · '+str(len(extra))+'</summary><p class="source-family-links">'+''.join(f'<a href="{e(r["url"])}" target="_blank" rel="noopener noreferrer">{e(r["label"])} ↗</a>' for r in extra)+'</p></details>' if extra else ''
        related=''.join(f'<a href="{BASE}research-{r["area_id"]}.html">{AREAS[r["area_id"]]} →</a>' for r in links if r['channel_id']==c['id'])
        eco=c.get('ecosystem','')
        badge='昇腾相关' if eco=='ascend' else '生态对照' if eco=='general' else '媒体线索' if c['category']=='news' else '学术入口'
        search=' '.join(c[k] for k in ('title','url','description','focus','rationale','group'))+' '+badge+' '+profile['entry_type']+' '+profile['evidence_role']
        host=urlsplit(c['url']).netloc.removeprefix('www.')
        return f'''<tr class="source-table-row" id="channel-{c['id']}" data-source-priority="{c['priority']}" data-source-domain="{c['category']}" data-source-ecosystem="{eco}" data-source-category="{e(c['group'])}" data-source-search="{e(search)}" data-source-entry-count="{1+len(extra)}">
<th scope="row"><a class="source-table-name" href="{e(c['url'])}" target="_blank" rel="noopener noreferrer" aria-label="打开{e(c['title'])}的{e(profile['entry_type'])}入口" title="{e(c['url'])}">{e(c['title'])} ↗</a><small class="source-entry-caption">{e(profile['entry_type'])} · {e(host)}</small><span class="source-table-badge">{badge}</span><span class="source-table-badge {'source-core' if c['priority']=='core' else ''}">{'核心跟踪' if c['priority']=='core' else '补充观察'}</span>{more}</th>
<td class="source-table-position"><p>{e(c['description'])}</p><p class="source-research-value"><strong>研究价值：</strong>{e(c['rationale'])}</p></td>
<td class="source-table-tracking"><p class="source-watch-focus">{e(c['focus'])}</p><p class="source-tracking-cadence"><strong>人工跟踪建议：</strong>{e(c['cadence']).removeprefix('建议')}</p><p class="source-evidence-role">{e(profile['evidence_role'])}</p>
<details class="source-table-details"><summary>适用边界与收录记录</summary><p><strong>适用边界：</strong>{e(c['boundary'])}</p><div class="source-research-links"><span>对应调度研究</span>{related}</div><p class="source-table-status">{status}</p><p class="source-table-status">入口最近核对：{e(c['checked'])} · {e(checks)}。当前人工整理，未自动订阅；上方为建议节奏。</p>{items}</details></td></tr>'''
    panels=[]
    for key,label in CATEGORIES:
        rows=[c for c in channels.values() if c['category']==key]
        names=INDUSTRY_GROUPS if key=='industry' else list(dict.fromkeys(c['group'] for c in rows))
        body=''
        if key=='industry':
            body='<div class="source-layer-map" aria-label="产业界执行层次">'+''.join(f'<a href="#source-layer-{i}"><b>0{i+1} · {name}</b><span>{e(GROUP_HELP[name])}</span></a>' for i,name in enumerate(INDUSTRY_GROUPS[:4]))+'</div><p class="reader-note">按项目主要职责归组，一个信息源一行；能力跨层时通过研究关联表达。昇腾相关是应用生态标签，不与执行层并列。</p>'
        role,desc=ROLES[key]
        body=f'<div class="source-panel-intro"><strong>{label} · {role}</strong><p>{desc}</p></div>'+body
        for name in names:
            selected=sorted([c for c in rows if c['group']==name],key=lambda c:c['priority']!='core')
            group_id=f' id="source-layer-{INDUSTRY_GROUPS.index(name)}"' if key=='industry' else ''
            body+=f'<section{group_id} class="source-subcategory" data-source-subcategory="{e(name)}"><h3>{e(name)}</h3><div class="source-table-scroll" tabindex="0" role="region" aria-label="{e(name)}信息源表，可横向滚动"><table class="source-table"><caption>{label} / {e(name)}信息源</caption><colgroup><col class="source-col-identity"><col class="source-col-value"><col class="source-col-tracking"></colgroup><thead><tr><th scope="col">信息源与入口</th><th scope="col">定位与研究价值</th><th scope="col">关注内容与跟踪方式</th></tr></thead><tbody>'+''.join(row(c) for c in selected)+'</tbody></table></div></section>'
        panels.append(f'<div class="source-domain" id="sources-{key}" data-source-panel="{key}"'+(' hidden' if key!='news' else '')+'>'+body+'</div>')
    populated=len({l['channel_id'] for l in provenance})
    counts={key:sum(c['category']==key for c in channels.values()) for key,_ in CATEGORIES}
    summary=''.join(f'<a href="#sources-{key}"><span>{label} · {counts[key]} 个信源</span><strong>{ROLES[key][0]}</strong></a>' for key,label in CATEGORIES)
    return f'''<section id="sources"><div class="compression-sources" data-source-directory><p class="eyebrow">01 / 信息来源</p><h2>从持续信源，找到调度研究的有效依据</h2>
<p>先看它是什么、为什么值得跟踪，再明确看什么、多久核对。名称直达主入口，其他入口就近展开；具体论文和发布事件进入本期动态。</p>
<div class="wb-domain-tabs" role="tablist" aria-label="来源类别">{tabs}</div>
<details class="source-policy"><summary>目录管理与覆盖检查 · {len(channels)} 个持续信源</summary>{source_lens()}<nav class="source-role-map" aria-label="三类信源的用途">{summary}</nav><p>目录记录持续来源，动态记录具体文章、论文与版本。整理参考<a href="https://docs.feedly.com/article/768-follow-sources-in-feedly" target="_blank" rel="noopener noreferrer">Feedly信源整理</a>、<a href="https://www.zotero.org/support/feeds" target="_blank" rel="noopener noreferrer">Zotero订阅</a>及<a href="https://www.inoreader.com/features/folders-and-tags" target="_blank" rel="noopener noreferrer">Inoreader来源与条目分开管理</a>的实践；三列表头是本报告的阅读设计。</p><p>三个分类按发布角色组织：媒体报道、项目官方资料、学术出版。同一机构可承担多个角色，具体条目按原始发布类型归档。证据类型说明如何使用来源，不是可靠性评分；官方声明仍需核对条件，预印本仍需核对评审状态。</p><p>一个信息源一行。相同论文版本关联为同一研究，媒体转载与官方发布关联为同一事件。保留主入口和相关渠道，避免重复登记。</p><p>已登记{len(channels)}个持续信源，{populated} / {len(channels)} 个已有精选内容。默认显示全部，核心／补充按本研究相关性选择。核对日期与建议节奏分开；当前为人工管理，尚未自动订阅或每日采集。</p>{coverage_html}</details>
<div class="wb-filters"><div><label for="channel-category">执行层 / 信源子类</label><select id="channel-category"><option value="">全部子类</option></select></div><div id="channel-ecosystem-field" hidden><label for="channel-ecosystem">应用生态</label><select id="channel-ecosystem"><option value="">全部生态</option><option value="ascend">昇腾相关</option><option value="general">生态对照</option></select></div><div><label for="channel-priority">显示范围</label><select id="channel-priority"><option value="all">全部信源（默认）</option><option value="important">只看核心信源</option></select></div><div><label for="channel-query">搜索信源、网站或分类</label><input id="channel-query" type="search" autocomplete="off"></div></div>
<p id="channel-status" class="meta" role="status">热点资讯 · {counts['news']} 个信源</p><div id="channel-cards" class="wb-reading-list" role="tabpanel" aria-labelledby="source-tab-news">{''.join(panels)}<p id="channel-empty" class="meta" hidden>当前筛选条件下没有匹配的信息源。可清空搜索或切换为全部信源。</p></div>
<div class="source-pagination" id="channel-pagination"><button type="button" id="channel-prev" disabled>上一页</button><span id="channel-range"></span><button type="button" id="channel-next" disabled>下一页</button></div>
<div class="reading-next"><span>下一步 · 用研究问题筛选信息</span><a href="#map">进入技术地图 →</a></div></div></section>'''
