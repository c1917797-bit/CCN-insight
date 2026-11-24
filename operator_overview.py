"""Research hub: hierarchy, comparisons, canonical evidence and judgment revisions."""
from html import escape as e
from operator_platform import render_taxonomy, render_coupling, render_library, render_judgment_log


def render_overview(corpus, structure, guide, changes, index, citations, hero, section, references, shell, boundaries, sources, events, monthly=None):
    def p(text, cls=''):
        return '<p'+(' class="'+cls+'"' if cls else '')+'>'+e(text)+'</p>'
    routes={r['id']:r for b in corpus['branches'] for r in b['routes']}
    records={r['id']:r for r in index['records']}
    body='<header class="op-hub-heading"><p class="op-eyebrow">极智 · AI Infra</p><h1>算子定制加速洞察</h1></header>'
    panels={}
    intro=hero('从执行机制，到值得追踪的技术',corpus['overview']['summary'],corpus['overview']['judgment'],visual=True).replace('<h1>','<h2>').replace('</h1>','</h2>')
    intro+='<nav class="op-route-jumps" aria-label="技术地图直达"><a href="#compute-map">计算算子</a><a href="#communication-map">通信算子</a><a href="operators-codegen.html">自动生成与调优 · 横向方法 →</a></nav>'
    search='<div class="op-searchbar"><input type="search" data-operator-search aria-label="按名称或瓶颈查找算子机制" placeholder="查找机制与做法，例如：FA3、Split-K、缓冲"><span data-search-count aria-live="polite">9 / 9 项机制</span></div>'
    tree=search+'<div class="op-family-grid">'+''.join(render_taxonomy(b,structure['routes'],guide['routes']) for b in corpus['branches'])+'</div><p class="op-filter-empty" hidden>没有匹配的机制。可尝试“分块”“布局”或“等待”。</p>'
    panels['topics']=intro+section('routes','01','技术地图',p('两条根技术主线，九个机制专题。直接进入专题或具体做法；计算与通信的组合关系在专题内比较，自动生成作为横向效率方法。')+tree)
    costs=[('数据流量','重复输入读取、中间写回、表示转换与通信载荷。','减少不必要的字节，或提高一次加载的消费次数。'),('执行组织','独立工作量、归约协作、尾块与阶段流水。','有效计算增加时，同步与资源代价也要计入。'),('发起与准备','短核/小消息启动、打包、注册与缓冲建立。','聚合省固定成本，也可能增加就绪等待。'),('关键路径','数据何时可消费、阶段间依赖与资源争用。','更早推进消费者，不等于每个独立阶段都更快。')]
    compare='<div class="op-table-scroll"><table><thead><tr><th>比较坐标</th><th>具体观察什么</th><th>判断依据</th></tr></thead><tbody>'+''.join('<tr><td>'+a+'</td><td data-label="具体观察什么">'+b+'</td><td data-label="判断依据">'+c+'</td></tr>' for a,b,c in costs)+'</tbody></table></div>'
    compare+=p('下面三组关系解释复用、分块、消息组织与数据路径为什么不能按独立收益相加。','op-note')
    pairs=['memory-reuse','launch-granularity','collectives-topology']
    for rid in pairs:
        compare+='<div class="op-coupling-origin"><a href="operators-'+rid+'.html">'+e(routes[rid]['title'])+' →</a></div>'+render_coupling(structure['routes'][rid],routes,citations)
    panels['topics']+=section('principles','02','跨机制比较',compare)
    panels['topics']+=section('evidence-library','03','研究速查',p('完整资料在这里按机制、硬件、证据层级与指标查找；原始记录保留实验条件、结果和边界。经典文献和产业实现不会因本轮核对而成为本月新闻。')+render_library(index))
    current=''
    if monthly:
        current+='<div class="op-monthly-intro"><div><span class="op-kicker">2026 / 11 · 截至11月24日</span><h3>从本期资料中，找到值得验证的技术</h3>'+p(monthly['judgment'])+'</div><aside><b>本期范围</b>'+p(monthly['scope'])+'</aside></div>'
        current+='<nav class="op-route-jumps op-monthly-nav" aria-label="本期阅读直达"><a href="#november-priorities">本期判断</a><a href="#november-events">技术进展</a><a href="#november-actions">验证方向</a><a href="#october-events">10月动态</a></nav>'
        priority=[x for x in monthly['events'] if x['priority']=='重点研读']
        current+='<div id="november-priorities" class="op-monthly-highlights"><h3>优先关注</h3><div class="op-monthly-highlight-list">'+''.join('<a href="#nov-event-'+e(x['id'],quote=True)+'"><span>'+e(x['platform'].split(' · ')[0])+'</span><b>'+e(x['title'])+'</b><small>'+e(x['route'])+'</small></a>' for x in priority)+'</div></div>'
        current+='<div id="november-events" class="op-monthly-events"><div class="op-monthly-heading"><div><span class="op-kicker">TECHNOLOGY SIGNALS</span><h3>11月技术进展</h3></div><p>按来源保留事件、效果与适用边界；技术启示为本站分析。</p></div>'
        ordered=sorted(monthly['events'],key=lambda x:x['date'],reverse=True)
        for event in ordered:
            current+='<article class="op-monthly-card" id="nov-event-'+e(event['id'],quote=True)+'"><div class="op-evidence-meta"><b>'+e(event['kind'])+'</b><span>'+e(event['date'])+' · '+e(event['date_basis'])+'</span><span>'+e(event['priority'])+'</span></div><h4>'+e(event['title'])+'</h4><p class="op-monthly-route"><b>技术地图</b> '+e(event['route'])+' <span>·</span> '+e(event['challenge'])+'</p><p class="op-monthly-platform">'+e(event['platform'])+'</p><div class="op-monthly-facts"><div><b>关键技术</b>'+p(event['mechanism'])+'</div><div><b>原始结果 / 发布内容</b>'+p(event['result'])+'</div><div><b>研究判断</b>'+p(event['insight'])+'</div><div><b>适用边界</b>'+p(event['boundary'])+'</div></div><div class="op-route-jumps"><a href="'+e(event['topic'],quote=True)+'">'+e(event['topic_label'])+' →</a><a href="'+e(event['source'],quote=True)+'" target="_blank" rel="noopener noreferrer">原始资料 ↗</a>'
            if event.get('date_source'):
                current+='<a href="'+e(event['date_source'],quote=True)+'" target="_blank" rel="noopener noreferrer">日期依据 ↗</a>'
            current+='</div>'+p('核对范围：'+event['locator'],'op-note')+'</article>'
        current+='</div><div id="november-actions" class="op-monthly-actions"><div class="op-monthly-heading"><div><span class="op-kicker">RESEARCH DIRECTIONS</span><h3>接下来验证什么</h3></div><p>以下是研究方案，预期价值与实际设备结果分别判断。</p></div><div class="op-monthly-action-grid">'
        for x in monthly['experiments']:
            current+='<article><h4>'+e(x['title'])+'</h4><dl><div><dt>对照</dt><dd>'+e(x['compare'])+'</dd></div><div><dt>为什么</dt><dd>'+e(x['reason'])+'</dd></div><div><dt>判断依据</dt><dd>'+e(x['success'])+'</dd></div></dl></article>'
        current+='</div></div>'
    current+='<div id="october-events" class="op-monthly-archive"><h3>10月动态</h3>'+p(events['scope'],'op-note')
    for event in events['events']:
        record=records[event['record_id']]
        current+='<article class="op-progress-item" id="event-'+e(event['id'])+'"><div class="op-evidence-meta"><b>'+e(event['event_kind'])+'</b><span>'+e(event['event_on'])+' · '+e(event['version'])+'</span></div><h3>'+e(record['title'])+'</h3>'+p(event['delta'])+'<div class="op-view"><strong>对专题的启示</strong>'+p(event['implication'])+'</div><div class="op-route-jumps"><a href="'+e(record['url'])+'">'+e(record['route_title'])+' · 研究记录 →</a><a href="'+e(event['event_url'],quote=True)+'" target="_blank" rel="noopener noreferrer">原始版本记录 ↗</a></div>'+p('日期依据：'+event['date_locator'],'op-note')+'</article>'
    current+=p('10月产业界材料保留在长期专题中；当期尚无独立核对发布日期与版本变化的产业事件条目。','op-note')+'</div><a href="#evidence-library">查阅全部研究与产业实现 →</a>'
    panels['current']=section('current-events',monthly['month'] if monthly else events['month'],'本期动态',current)
    focus='<div class="op-frontier-grid">'
    for row in guide['frontier']:
        record=records[row['record_id']]
        focus+='<article><span class="op-kicker">观察与依据</span><h3><a href="'+record['url']+'">'+e(row['title'])+' →</a></h3><div class="op-fact"><b>原始记录</b>'+p(record['result'])+citations(record['source_ids'])+'</div><div class="op-view"><b>研究判断</b>'+p(row['view'])+'</div></article>'
    focus+='</div>'
    judgment='<div class="cg-conclusions">'+''.join('<article><h3>'+e(r['title'])+'</h3>'+p(r['text'])+citations(r['source_ids'])+'</article>' for r in corpus['overview']['conclusions'])+'</div>'
    judgment+=section('frontier','依据','哪些证据影响当前判断',focus,3)
    month_report=''
    if monthly:
        monthly_records={row['id']:row for row in monthly['events']}
        themes=[
            ('减少无效搜索','先用目标资源约束构造初始配置，再把设备评估留给困难形状；需比较同预算下的有效覆盖。','helion-heuristics'),
            ('在目标硬件重建融合策略','图表示可复用，切分、资源模型和后端执行需要按芯片重建；融合仍要对照强实现。','mirage-ascend'),
            ('通信策略随负载改变','小批量优先观察固定开销和缓冲组织，较大负载还要比较计算通信重叠。','nvlink-one-sided'),
        ]
        month_report='<div class="op-report-month"><span class="op-kicker">2026 / 11 · 定向筛选</span><h3>本期研究判断</h3>'+p(monthly['judgment'])+'<div class="op-report-month-grid">'
        for title,view,event_id in themes:
            if event_id not in monthly_records:
                continue
            row=monthly_records[event_id]
            month_report+='<article><h4>'+e(title)+'</h4>'+p(view)+'<a href="#nov-event-'+e(event_id,quote=True)+'">依据：'+e(row['title'])+'</a></article>'
        month_report+='</div><p class="op-note">截至'+e(monthly['reviewed_at'])+'的定向资料核对，不代表全信息源扫描或设备复现。</p><a href="#november-actions">查看本期具体验证方向 →</a></div>'
    panels['report']=section('conclusion','判断','洞察报告',month_report+p('综合解释哪些执行机制值得跟踪、收益在何种条件下成立，以及哪些证据会改变判断。具体实验条件与结果回到对应技术记录核对。')+judgment)
    panels['archive']=section('updates','记录','判断修订记录',p('当前保留的是有原始依据的编辑修订，尚未建立独立的月度报告版本归档。修订日期不作为论文或产品发布日期。','op-note')+p(changes['scope'])+render_judgment_log(changes,records,citations))
    appendix=section('hardware','硬件','GPU与昇腾NPU的实现边界',p('CUDA GPU的线程/warp、存储与异步指令，和具体昇腾SoC的Host Tiling、Vector/Cube、搬运与同步约束分别核对。部分新代际昇腾提供SIMT能力，不能把GPU/NPU标签当作完整支持矩阵。')+citations(['cuda-programming-model','ascend-3510-architecture'])+'<a href="operators-1.html#cannbot">从Add数据流看硬件映射 →</a>',3)
    appendix+=section('automatic','方法','横向方法：自动生成与调优',p('编译、参数搜索、经验检索和LLM/Agent帮助形成实现。开发效率与运行收益分别评价；它们承接加速机制，不另设为第三条加速主线。')+'<a class="op-text-link" href="operators-codegen.html">进入方法体系、GPU/NPU证据与能力判断 →</a>',3)
    appendix+=section('evaluation','评价','证据层级与评价范围','<div class="op-evaluation-grid"><article><h3>语义与数值</h3>'+p('固定完整输出和允许误差，覆盖shape、尾块与特殊值。业务质量目标不能替代内核正确性。')+'</article><article><h3>执行与模块</h3>'+p('完整计入转换、打包、同步、工作区与强基线；单核和完整模块分别比较。')+'</article><article><h3>模型与服务</h3>'+p('模型服务再比较质量、TTFT/TPOT和达标吞吐。热点倍数、前向阶段和服务指标不互换。')+'</article></div>',3)
    appendix+=section('boundaries','归属','与相邻根技术的关系',boundaries(),3)
    panels['topics']+=section('scope','附录','研究边界与方法',appendix)
    categories=[('昇腾 NPU · 官方生态',lambda r: 'ascend' in r['url'].lower() or 'cann' in r['url'].lower() or '昇腾' in r['title'] or 'CANN' in r['title']),('GPU 与跨平台 · 官方生态',lambda r:r['kind']!='primary_paper'),('学术界 · 原始论文',lambda r:True)]
    remaining=dict(sources);register=''
    for label,accept in categories:
        selected=[(sid,row) for sid,row in remaining.items() if row['kind']!='primary_paper' and accept(row)] if '学术界' not in label else list(remaining.items())
        if not selected:continue
        register+='<h3>'+label+'</h3><div class="op-table-scroll"><table class="op-source-register"><thead><tr><th>来源与原始链接</th><th>定位与核对范围</th><th>硬件与证据边界</th></tr></thead><tbody>'
        for sid,row in selected:
            remaining.pop(sid)
            register+='<tr><th scope="row"><a href="#source-'+e(sid)+'">'+e(row['title'])+'</a><a class="op-source-url" href="'+e(row['url'],quote=True)+'" target="_blank" rel="noopener noreferrer">'+e(row['url'])+' ↗</a></th><td data-label="定位与核对范围">'+e(row['review_scope'])+'</td><td data-label="硬件与证据边界">'+e(row['device_scope'])+'</td></tr>'
        register+='</tbody></table></div>'
    panels['sources']=section('sources-directory','目录','信息来源',p('查看采用了哪些原始来源、各自覆盖什么，以及哪些硬件和结果不能据此推断。表格链接进入原始入口；下方保留完整审阅范围与正文引用回链。')+register)+references(list(sources))
    aliases={'sources':'view-sources','topics':'view-topics','current':'view-updates','report':'view-home','archive':'view-reports'}
    for key in ['sources','topics','current','report','archive']:
        body+='<div id="'+aliases[key]+'" data-operator-view="'+key+'">'+panels[key]+'</div>'
    outline=[('sources-directory','来源目录'),('references','资料与证据范围'),('routes','01 技术地图'),('compute-map','计算算子'),('communication-map','通信算子'),('principles','02 跨机制比较'),('evidence-library','03 研究速查'),('scope','附录：范围与方法'),('current-events','本期动态'),('conclusion','研究判断'),('frontier','支撑判断的证据'),('updates','判断修订记录')]
    page=shell('算子定制加速',body,outline)
    # The hub combines materials with different review dates; each entry carries its own date.
    return page.replace('资料核对 2026-10-23','来源按各条记录核对')
