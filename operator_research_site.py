"""Render the maintained operator research without changing the other Infra roots."""
from pathlib import Path
from html import escape
import json
import re
import shutil
from hashlib import sha256
from operator_visuals import hero_svg, route_svg
from operator_cannbot import render_case, route_hook
from operator_codegen import render_codegen
from operator_overview import render_overview
from operator_topic_reader import research_brief
from operator_platform import (compile_index, record_anchor, render_scope, render_taxonomy,
                               render_method_catalog, render_approaches, render_coupling,
                               render_library, render_judgment_log)


def build(root):
    source = root/'research/ai-infra'
    out = root/'dist/ai-infra'
    corpus = json.loads((source/'operator-routes.json').read_text(encoding='utf-8'))
    evidence = json.loads((source/'operator-sources.json').read_text(encoding='utf-8'))
    cannbot = json.loads((source/'operator-cannbot-case.json').read_text(encoding='utf-8'))
    codegen = json.loads((source/'operator-codegen-insight.json').read_text(encoding='utf-8'))
    hardware = json.loads((source/'operator-codegen-hardware.json').read_text(encoding='utf-8'))
    named_a = json.loads((source/'operator-codegen-named-a.json').read_text(encoding='utf-8'))
    named_b = json.loads((source/'operator-codegen-named-b.json').read_text(encoding='utf-8'))
    guide = json.loads((source/'operator-expert-guide.json').read_text(encoding='utf-8'))
    structure = json.loads((source/'operator-research-structure.json').read_text(encoding='utf-8'))
    changes = json.loads((source/'operator-judgment-log.json').read_text(encoding='utf-8'))
    events = json.loads((source/'operator-events.json').read_text(encoding='utf-8'))
    sources = {row['id']: row for row in evidence['sources']}
    branches = {row['id']: row for row in corpus['branches']}
    route_lookup={r['id']:r for b in corpus['branches'] for r in b['routes']}
    index=compile_index(corpus,codegen,named_a,named_b,structure,sources)
    record_lookup={r['id']:r for r in index['records']}
    (out/'operator-evidence-index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    source_kinds = {
        'primary_paper': '原始论文',
        'official_documentation': '官方文档',
        'official_historical_documentation': '官方历史文档',
        'official_project_repository': '官方项目仓库',
        'official_repository': '官方代码仓库',
        'official_repository_documentation': '官方工程文档',
        'official_project_documentation': '官方项目文档',
        'official_project_repository_documentation': '官方项目接口文档',
    }
    e = escape
    citation_serial=0
    citation_backlinks={}
    asset_versions={name:sha256((root/'content'/('operators-research.'+name)).read_bytes()).hexdigest()[:12] for name in ('css','js')}
    shared_topic_version=sha256((root/'original-reader/site/business_insight/cloud_core/topic-studio.css').read_bytes()).hexdigest()[:12]

    def p(text, cls=''):
        return '<p'+(' class="'+cls+'"' if cls else '')+'>'+e(str(text))+'</p>'

    def ul(items):
        return '<ul>'+''.join('<li>'+e(str(item))+'</li>' for item in items)+'</ul>'

    def citations(ids):
        nonlocal citation_serial
        for key in ids:
            assert key in sources, key
        links=[]
        for key in dict.fromkeys(ids):
            citation_serial+=1
            anchor='cite-'+str(citation_serial)
            citation_backlinks.setdefault(key,[]).append(anchor)
            links.append('<a id="'+anchor+'" href="#source-'+e(key)+'" title="'+e(sources[key]['title']+'；'+sources[key]['review_scope'],quote=True)+'">['+str(list(sources).index(key)+1)+']</a>')
        return '<span class="op-citations">'+''.join(links)+'</span>'

    def references(ids):
        html = '<section id="references" class="op-section"><div class="op-section-title"><span>依据</span><h2>资料与证据范围</h2></div><div class="op-source-list">'
        for key in dict.fromkeys(ids):
            row = sources[key]
            assert row['url'].startswith('https://'), key
            html += '<article id="source-'+e(key)+'"><span class="op-source-kind">'+e(source_kinds[row['kind']])+'</span><h3><a href="'+e(row['url'],quote=True)+'" target="_blank" rel="noopener noreferrer">['+str(list(sources).index(key)+1)+'] '+e(row['title'])+' ↗</a></h3>'
            html += p(row['review_scope'])+p('设备范围：'+row['device_scope'])+p(row['boundary'],'op-note')+'<div class="op-source-return">'+''.join('<a href="#'+a+'">返回引用'+str(i)+' ↑</a>' for i,a in enumerate(citation_backlinks.get(key,[]),1))+'</div></article>'
        return html+'</div></section>'

    def section(key, number, title, content, level=2):
        heading='h'+str(level)
        return '<section id="'+key+'" class="op-section'+(' op-subsection' if level>2 else ' research-overview-section')+'"><div class="op-section-title"><span>'+number+'</span><'+heading+'>'+title+'</'+heading+'></div>'+content+'</section>'

    def shell(title, body, outline, active='overview'):
        citation_backlinks.clear()
        targets=dict(outline)
        primary='progress' if 'progress' in targets else ('evidence' if 'evidence' in targets else ('routes' if 'routes' in targets else outline[0][0]))
        ending='practice' if 'practice' in targets else ('conclusion' if 'conclusion' in targets else 'research')
        nested=set(re.findall(r'<section id="([^"]+)" class="op-section op-subsection"',body))
        nested.update(key for key,_ in outline if key.startswith(('route-','cannbot-')))
        quick='<nav class="op-mobile-quick" aria-label="阅读直达"><a href="#'+primary+'">'+targets[primary]+' ↓</a><a href="#'+ending+'">研究判断 ↓</a><a href="#main">回到开篇 ↑</a></nav>'
        nav = [('sources','operators.html#view-sources','信息来源'),('topics','operators.html#view-topics','技术地图'),('current','operators.html#view-updates','本期动态'),('report','operators.html#view-home','洞察报告'),('archive','operators.html#view-reports','洞察归档')]
        nav_active='topics' if active!='overview' else ''
        shared_styles='<link rel="stylesheet" href="/business_insight/cloud_core/topic-studio.css?v='+shared_topic_version+'">' if active!='overview' else ''
        if active!='overview':
            count=len(re.findall(r'data-topic-record=',body))
            source_count=len(set(re.findall(r'href="#source-([^"]+)"',body)))
            meta='<div class="topic-report-meta"><div><strong>'+str(count)+'</strong><span>原文案例</span></div><div><strong>'+str(source_count)+'</strong><span>关联来源</span></div></div>'
            body=body.replace('<div class="op-meta-row">',meta+'<div class="op-meta-row">',1)
            body='<div class="structured-topic" data-operator-topic="true">'+body+'</div>'
        return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(title)+' · 极智 AI Infra</title><link rel="stylesheet" href="operators-research.css?v='+asset_versions['css']+'">'+shared_styles+'<script src="operators-research.js?v='+asset_versions['js']+'" defer></script></head><body class="operator-research"><a class="op-skip" href="#main">跳到正文</a><header class="op-header"><a class="op-brand" href="/ai-infra/"><b>极智</b><span>AI Infra <small>算子定制加速</small></span></a><nav aria-label="算子洞察导航">'+''.join('<a '+('aria-current="page" ' if key==nav_active else '')+'href="'+url+'">'+name+'</a>' for key,url,name in nav)+'</nav><button class="op-motion-toggle" data-motion-toggle aria-pressed="false">暂停动效</button><span class="op-reading-progress" aria-hidden="true"></span></header><aside class="op-outline"><a class="op-return" href="operators.html#view-topics">← 算子技术地图</a><p>本页目录</p><nav aria-label="本页目录">'+''.join('<a '+('class="op-outline-sub" ' if key in nested else '')+'href="#'+key+'">'+name+'</a>' for key,name in outline)+'</nav></aside><main id="main">'+body+'</main>'+quick+'<footer>极智 · AI Infra · 资料核对 2026-10-23 · 公开结果与编辑分析分别标示；未进行设备复现。</footer></body></html>'

    def hero(title, summary, judgment, eyebrow='算子定制加速 / 根技术研究', visual=False):
        meta='<div class="op-meta-row"><span>2026-10-23 核对</span><span>原理 · 技术进展 · 研究判断</span></div>'
        return '<div class="op-hero compression-topic-hero'+(' op-hero--overview' if visual else '')+'"><div class="op-hero-copy"><p class="op-eyebrow">'+e(eyebrow)+'</p><h1>'+e(title)+'</h1>'+p(summary,'op-lead direction-lead')+'</div>'+(hero_svg() if visual else '')+'<div class="op-judgment"><span>核心判断</span>'+p(judgment)+'</div>'+meta+'</div>'

    def route_index(branch, page):
        html = '<article class="op-family"><span class="op-kicker">'+('COMPUTE' if branch['id']=='compute' else 'COMMUNICATION')+'</span><h3><a href="'+page+'">'+e(branch['title'])+' →</a></h3>'+p(branch['summary'])+'<ol>'
        for route in branch['routes']:
            terms=[route['title'],route['challenge'],route['principle']]+[v['title']+' '+v['mechanism'] for group in ['industry','academic'] for v in route[group]]+[v['name'] for v in route['expert']['branches']]+guide['routes'][route['id']].get('search_terms',[])
            html += '<li data-route-search="'+e(' '.join(terms),quote=True)+'"><a href="operators-'+e(route['id'])+'.html">'+e(route['title'])+'</a></li>'
        return html+'</ol></article>'

    def route_cards(branch):
        html = ''
        for index, route in enumerate(branch['routes'],1):
            html += '<article class="op-route" id="route-'+e(route['id'])+'"><div class="op-route-heading"><span>'+str(index).zfill(2)+'</span><h3>'+e(route['title'])+'</h3></div><p class="op-challenge"><strong>解决什么问题</strong> '+e(route['challenge'])+'</p>'+p(route['principle'],'op-principle')
            html += p(route.get('expert',{}).get('brief',route['judgment']),'op-boundary')+'<a class="op-text-link" href="operators-'+e(route['id'])+'.html">原理与技术证据 →</a></article>'
        return html

    def mechanism_figure(kind):
        return route_svg('memory-reuse' if kind=='compute' else 'compute-communication-overlap')

    def expert_brief(route):
        row=guide['routes'][route['id']]
        return '<div class="op-expert-brief" aria-label="机制要点">'+''.join('<article><span>'+label+'</span>'+p(row[key])+'</article>' for key,label in [('delta','技术改变'),('tradeoff','核心取舍'),('priority','关注场景')])+'</div>'

    def branch_matrix(branch):
        html='<div class="op-table-scroll"><table class="op-branch-matrix"><thead><tr><th>根机制与具体做法</th><th>改变什么 / 主要代价</th><th>当前判断</th></tr></thead><tbody>'
        for r in branch['routes']:
            spec=structure['routes'][r['id']]
            links='<ul class="op-tree-links">'+''.join('<li><a href="operators-'+r['id']+'.html#'+a['id']+'">'+e(a['title'])+'</a></li>' for a in spec['catalog'])+'</ul>'
            html+='<tr id="route-'+r['id']+'"><th scope="row"><h3><a href="operators-'+r['id']+'.html">'+e(r['title'])+' →</a></h3>'+links+'</th><td data-label="改变什么 / 主要代价"><p>'+e(guide['routes'][r['id']]['delta'])+'</p><p class="op-note">'+e(guide['routes'][r['id']]['tradeoff'])+'</p></td><td data-label="当前判断">'+p(r['expert']['brief'])+'</td></tr>'
        return html+'</tbody></table></div>'

    def pipeline():
        stages = [('语义规格','固定 shape、dtype、布局与数值规则'),('目标核对','精确 SoC、工具链和 API'),('候选生成','工程模板、内核逻辑与分块'),('编译与正确性','当前制品、独立参考与边界输入'),('性能与集成','强基线、真实分布、回退与模型复测')]
        return '<ol class="op-pipeline">'+''.join('<li><span>'+str(i+1).zfill(2)+'</span><h3>'+title+'</h3>'+p(text)+'</li>' for i,(title,text) in enumerate(stages))+'</ol>'+p('编译通过、数值正确、单算子更快和模型净收益，是逐层检查的不同结果。生成器可以提出候选，验收需要独立参考与目标执行证据。','op-note')

    boundary_rows = [
        ('模型内部驻留或计算表示改变','推理压缩','权重、激活或状态采用低比特、稀疏、低秩表示。算子侧负责消费该表示并核算执行代价；仅在传输时编码压缩的消息仍归通信算子。','/business_insight/cloud_core/index.html?month=2026-10#map'),
        ('传输实现改变','通信算子加速','在固定并行划分下优化通信算法、启动、数据路径和同步。','operators-2.html'),
        ('并行划分或实例排程改变','组合调度加速','调整 TP/PP/EP、微批或实例放置；通过关联入口连接通信结果。','scheduling-2.html'),
        ('物理互连和资源供给改变','硬件加速','升级链路、带宽或硬件拓扑；软件如何利用既有链路留在算子与调度研究。','hardware-1.html'),
    ]
    def boundaries():
        return '<div class="op-table-scroll"><table><thead><tr><th>主要改变</th><th>主归属</th><th>与算子研究的关系</th></tr></thead><tbody>'+''.join('<tr><td data-label="主要改变">'+e(change)+'</td><td data-label="主归属"><a href="'+url+'">'+e(owner)+' →</a></td><td data-label="与算子研究的关系">'+e(explain)+'</td></tr>' for change,owner,explain,url in boundary_rows)+'</tbody></table></div>'

    def route_figure(route):
        return route_svg(route['id'])

    def progress_items(rows, label, route):
        html='<div class="op-progress-group"><h3>'+label+'</h3>'
        for row in rows:
            metadata='<div class="op-evidence-meta"><b>'+e(row['result_type'])+'</b><span>'+e(row.get('date','机制资料'))+'</span></div>'
            facts=''
            if row.get('conditions') or row.get('result'):
                facts='<div class="op-evidence-facts"><div><strong>对象与比较条件</strong>'+p(row.get('conditions','原始材料未提供可比实验条件'))+'</div><div><strong>原始材料报告的效果</strong>'+p(row.get('result','本条为机制或功能说明'))+'</div></div>'
            related=[a for a in route['expert']['branches'] if set(a['evidence_ids'])&set(row['source_ids'])]
            associations='<div class="op-work-relations"><span>关联研究：</span>'+''.join('<a href="#'+a['id']+'">'+e(a['name'])+' ↑</a>' for a in related)+'</div>' if related else p('本项用于机制背景或实现条件补充。','op-note')
            html+='<article id="'+record_anchor(row['id'])+'" class="op-progress-item topic-dossier-card" data-result-type="'+e(row['result_type'],quote=True)+'">'+metadata+'<h4>'+e(row['title'])+'</h4>'+associations+p(row['mechanism'])+facts+p(row.get('boundary',row.get('evidence_scope','')),'op-note')+citations(row['source_ids'])+'</article>'
        return html+'</div>'

    def branch_comparison(route):
        entries=route.get('expert',{}).get('branches',[])
        if not entries:
            return ''
        rows=''
        for row in entries:
            rows+='<tr><td data-label="具体做法">'+e(row['name'])+citations(row.get('evidence_ids',[]))+'</td><td data-label="节省来自哪里">'+e(row['mechanism'])+'</td><td data-label="新增代价与选用条件">'+e(row['tradeoff'])+'</td></tr>'
        return '<div class="op-table-scroll"><table class="op-comparison-table"><thead><tr><th>具体做法</th><th>节省来自哪里</th><th>新增代价与选用条件</th></tr></thead><tbody>'+rows+'</tbody></table></div>'

    def detailed_route(branch, route):
        expert=route['expert'];spec=structure['routes'][route['id']];reading=guide['routes'][route['id']]
        used=route['source_ids']+reading['source_ids']+spec['source_ids']+spec['cross_route_condition']['source_ids']
        used+=[sid for group in ['industry','academic'] for row in route[group] for sid in row['source_ids']]
        used+=[sid for row in expert['branches'] for sid in row['evidence_ids']]
        used+=[sid for row in spec['catalog'] for sid in row['source_ids']]
        body=hero(route['title'],route['challenge'],route['judgment'],'算子研究 / '+branch['title']+' / '+spec['axis_label'])
        outline=[('brief','01 速览与证据'),('background','02 研究背景'),('principles','03 基本原理'),('challenges','04 关键挑战'),('progress','05 技术进展'),('comparison','06 比较判断'),('practice','07 研究结论')]
        topic_records=[r for r in index['records'] if r['route_id']==route['id']]
        body+=section('brief','01','速览与证据',research_brief(reading['insight']['title'],route['judgment'],[a['title'] for a in spec['catalog']],topic_records,spec['unresolved_questions'][:2],sources,'operators-'+route['id']+'.html'))
        body+=section('background','02','研究背景',render_scope(spec)+p(expert['bottleneck_signal'],'op-boundary'))
        hook=''
        if branch['id']=='compute':
            hook=route_hook(cannbot,route,citations)
            used+=next(x for x in cannbot['route_links'] if x['route_id']==route['id'])['source_ids']
        decomposition=p(route['principle'],'op-principle')+p(spec['narrative'])
        decomposition+='<div class="op-formula"><span>成本关系 · 分析模型</span>'+p(route['principle_formula'])+'</div>'+citations(route['source_ids'])+route_figure(route)
        body+=section('principles','03','基本原理',decomposition+hook)
        body+=section('challenges','04','关键挑战',ul(route['research_questions'])+'<div class="op-open-questions"><h3>仍待回答的问题</h3>'+ul(spec['unresolved_questions'])+'</div>')
        body+=section('progress','05','技术进展',p('产业资料说明已有实现及其支持条件；学术材料说明机制和实验增量。每条记录保留对象、比较条件、结果与边界。','op-note')+progress_items(route['industry'],'产业界 · 实现与能力边界',route)+progress_items(route['academic'],'学术界 · 机制与实验结果',route))
        comparison=render_method_catalog(spec,citations)+p('具体做法、应用场景、训练关联和实现方法分别列示；它们并非全部互斥，不能只按论文峰值排名。','op-note')+render_approaches(route,spec,citations)+render_coupling(spec,route_lookup,citations)
        comparison+='<div class="op-evidence-grid op-conditions"><article><h3>更值得关注的条件</h3>'+ul(route['selection']['suitable'])+'</article><article><h3>容易失效的条件</h3>'+ul(route['selection']['unsuitable'])+'</article></div>'
        body+=section('comparison','06','比较判断',comparison)
        insight=reading['insight'];used+=insight['source_ids']
        judgment='<div class="op-research-insight"><span class="op-kicker">综合分析</span><h3>'+e(insight['title'])+'</h3>'+''.join(p(x) for x in insight['paragraphs'])+citations(insight['source_ids'])+'</div>'
        conclusion=p(expert['conclusion'],'op-principle')+p(route['boundary'],'op-note')+'<div class="op-reconsider"><strong>什么证据会改变这一判断</strong>'+p(reading['reversal'])+'</div>'
        judgment+=section('conclusion','结论','结论与适用边界',conclusion,3)
        if branch['id']=='compute':
            judgment+='<div class="op-sibling-links"><a href="operators-codegen.html#practice">横向关联：这些机制怎样进入自动生成与调优 →</a></div>'
        changed=[x for x in changes['changes'] if route['id'] in x['route_ids']]
        if changed:
            judgment+=section('updates','修订','本站判断如何更新',render_judgment_log(changes,record_lookup,citations,route['id']),3)
            outline.append(('updates','判断修订记录'))
            used+=[s for change in changed for rid in change['evidence_ids'] for s in record_lookup[rid]['source_ids']]
        judgment+='<div class="op-method-list"><h3>用哪些指标检验判断</h3>'+ul(route['metrics'])+'</div>'
        body+=section('practice','07','研究结论',judgment)
        body+='<div class="op-sibling-links"><span>同组机制</span>'+''.join('<a href="operators-'+r['id']+'.html">'+e(r['title'])+' →</a>' for r in branch['routes'] if r['id']!=route['id'])+'</div>'
        body+=references(used);outline.append(('references','资料依据'))
        return shell(route['title'],body,outline,branch['id'])

    overview=render_overview(corpus,structure,guide,changes,index,citations,hero,section,references,shell,boundaries,sources,events)
    (out/'operators.html').write_text(overview,encoding='utf-8')

    for key,filename in [('compute','operators-1.html'),('communication','operators-2.html')]:
        branch=branches[key]
        branch_route_ids={r['id'] for r in branch['routes']}
        branch_records=[r for r in index['records'] if r['route_id'] in branch_route_ids]
        body=hero(branch['title'],branch['summary'],branch['judgment'])
        body+=section('brief','01','速览与证据',research_brief(branch['title']+'：机制、实现与适用条件',branch['judgment'],[r['title'] for r in branch['routes']],branch_records,[structure['routes'][r['id']]['unresolved_questions'][0] for r in branch['routes']][:2],sources,filename))
        body+=section('background','02','研究背景',p(branch['summary'])+p('先固定计算语义、输出和目标硬件，再辨认主要执行开销。各专题保留具体的shape、dtype、版本与比较条件；单算子结果与模型服务结果分开判断。'))
        interactions=['memory-reuse','fusion-launch'] if key=='compute' else ['launch-granularity','paths-buffers']
        if key=='compute':
            body+=section('principles','03','基本原理',render_case(cannbot,citations))
        else:
            body+=section('principles','03','基本原理',mechanism_figure(key))
        challenge_rows=''.join('<tr><th scope="row"><a href="operators-'+e(r['id'])+'.html#challenges">'+e(r['title'])+'</a></th><td data-label="关键挑战">'+e(r['challenge'])+'</td><td data-label="尚待回答">'+e(structure['routes'][r['id']]['unresolved_questions'][0])+'</td></tr>' for r in branch['routes'])
        body+=section('challenges','04','关键挑战','<div class="op-table-scroll"><table><thead><tr><th>研究方向</th><th>关键挑战</th><th>尚待回答</th></tr></thead><tbody>'+challenge_rows+'</tbody></table></div>')
        body+=section('progress','05','技术进展',section('routes','目录','机制体系与具体做法',branch_matrix(branch),3))
        body+=section('comparison','06','比较判断',''.join(render_coupling(structure['routes'][rid],route_lookup,citations) for rid in interactions))
        used=list(dict.fromkeys(s for route in branch['routes'] for s in route['source_ids']))+[s for rid in interactions for s in structure['routes'][rid]['cross_route_condition']['source_ids']]+[sid for record in branch_records for sid in record['source_ids']]
        if key=='compute':
            used+=cannbot['source_ids']+[s for row in cannbot['concepts']+cannbot['route_links'] for s in row['source_ids']]+cannbot['fusion']['source_ids']
            extra=section('automatic','方法','横向方法：开发与调优效率',p('CannBot用于解释硬件映射中的具体概念。编译、自动调优和LLM/Agent进一步研究怎样更高效地找到合法、正确且有收益的实现；自动生成不替代前面四条加速根技术。')+'<a class="op-text-link" href="operators-codegen.html">自动生成与调优的原理、进展和研究启示 →</a>',3)
            used+=['msopgen','msot-quickstart','ascendkernelgen']
        else:
            extra=section('boundaries','归属','通信与相邻根技术的边界',p('本分支固定交换需求，研究路由、发起、路径、依赖和表示。改变TP/PP/EP、expert放置或请求排程属于调度；更换互连属于硬件。')+'<a href="operators.html#boundaries">查看统一的根技术归属说明 →</a>',3)
        judgments=guide['branch_conclusions'][key]
        conclusion='<div class="cg-conclusions">'+''.join('<article><h3>'+e(row['title'])+'</h3>'+p(row['text'])+citations(row['source_ids'])+'</article>' for row in judgments)+'</div>'
        body+=section('practice','07','研究结论',section('research','判断','结论与适用条件',conclusion,3)+extra)
        used+=[s for row in judgments for s in row['source_ids']]
        body+=references(used)
        outline=[('brief','01 速览与证据'),('background','02 研究背景'),('principles','03 基本原理'),('challenges','04 关键挑战'),('progress','05 技术进展'),('comparison','06 比较判断'),('practice','07 研究结论'),('references','资料依据')]
        (out/filename).write_text(shell(branch['title'],body,outline,key),encoding='utf-8')
        for route in branch['routes']:
            (out/('operators-'+route['id']+'.html')).write_text(detailed_route(branch,route),encoding='utf-8')

    codegen_brief=research_brief('生成方法的价值，取决于找到正确且更快实现的效率',codegen['judgment'],[r['title'] for r in codegen['methods']],[r for r in index['records'] if r['route_id']=='codegen'],codegen['nextwork'],sources,'operators-codegen.html')
    (out/'operators-codegen.html').write_text(render_codegen(codegen,hardware,named_a,named_b,citations,hero,section,references,shell,codegen_brief),encoding='utf-8')

    # Preserve old local bookmarks without exposing an internal project report.
    legacy='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=operators-codegen.html#practice"><title>算子生成研究</title><p>相关研究已整合至<a href="operators-codegen.html#practice">算子自动生成与调优 · 研究启示</a>。</p></html>'
    (out/'operators-310p-codegen.html').write_text(legacy,encoding='utf-8')
    shutil.copy2(root/'content/operators-research.css',out/'operators-research.css')
    shutil.copy2(root/'content/operators-research.js',out/'operators-research.js')
    map_file=out/'index.html'
    text=map_file.read_text(encoding='utf-8')
    # Keep the two exact second-level titles; emphasize root mechanisms.
    pattern=r'(<a class="card" href="operators-1.html"[^>]*>.*?<span class="more">).*?(</span></a>)'
    text,n=re.subn(pattern,lambda m:m[1]+'计算机制与技术进展 <i>→</i>'+m[2],text,count=1,flags=re.S)
    assert n==1,'Compute operator map entry missing'
    map_file.write_text(text,encoding='utf-8')
    print('Operator research generated: root-tech mainline, 2 exact branches, 9 mechanism dossiers and horizontal efficiency research')
