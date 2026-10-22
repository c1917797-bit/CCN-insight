"""Render the imported, revision-bound compression corpus without runtime TableGit."""
from pathlib import Path
import json,re,shutil
from html import escape as e

def build(root):
    out=root/'dist'/'ai-infra'
    from compression_store import rows
    topics=sorted(rows('ic_compression_topics'),key=lambda x:x['position'])
    cards=rows('ic_compression_topic_cards'); refs=rows('ic_compression_topic_card_refs')
    routes=rows('ic_compression_research_routes'); frames=rows('ic_compression_research_frames')
    industry=rows('ic_industry_topic_assessments'); assessments=rows('ic_compression_route_assessments')
    sections=rows('ic_compression_topic_sections'); steps=rows('ic_compression_mechanism_steps')
    sources={x['source_id']:x for x in rows('compression_sources')}
    template=(out/'compression.html').read_text(encoding='utf-8')
    groups=[('parameters','权重','模型参数的存储与读取','量化、剪枝、蒸馏与低秩分解'),('activations','激活','推理中间张量的计算与流转','低精度、稀疏选择与 Token 合并'),('kv_cache','KV Cache','生成过程中持续保留的历史状态','低精度、淘汰、共享与紧凑架构')]
    def paras(text): return ''.join('<p>'+e(p)+'</p>' for p in text.split('\n') if p.strip())
    def link(source_id):
        s=sources.get(source_id,{})
        return '<a class="source-link" href="'+e(s.get('canonical_url',''),quote=True)+'" target="_blank" rel="noopener">'+e(s.get('title',source_id))+' ↗</a>' if s.get('canonical_url') else ''
    def nav(items):
        return '<aside class="compression-side"><a class="return-map" href="index.html">← AI Infra 根技术地图</a><p class="eyebrow">推理压缩 · 阅读目录</p>'+''.join('<a href="'+e(url)+'">'+e(title)+'</a>' for title,url in items)+'</aside>'
    def page(title,body,items):
        html=re.sub(r'<main id="main">.*?</main>',lambda m:'<main id="main">'+body+'</main>',template,flags=re.S)
        html=re.sub(r'<aside\b.*?</aside>',lambda m:nav(items),html,flags=re.S)
        html=re.sub(r'<title>.*?</title>','<title>'+e(title)+' · CCN AI Infra</title>',html)
        html=html.replace('class="topic-page"','class="topic-page compression-reader"').replace('</head>','<link rel="stylesheet" href="compression-reader.css"></head>')
        return html
    def tile(t):
        key=t['compression_topic_id']; rr=[r for r in routes if r['compression_topic_id']==key]
        route_names=' · '.join(r['title_zh'].split('：')[0] for r in rr[:3])
        return '<a class="compression-tile" href="topic-'+key+'.html"><h3>'+e(t['title_zh'])+'</h3><p>'+e(t['question_zh'])+'</p>'+('<small>'+e(route_names)+'</small>' if route_names else '')+'<span>原理 · 路线 · 依据 →</span></a>'
    intro='<div class="compression-heading"><p class="eyebrow">AI INFRA / 推理压缩</p><h1>更少的资源，保留有用的能力。</h1><p>先分清压缩对象，再选择技术路线。权重、激活与 KV Cache 的瓶颈不同，文件变小也不等于服务变快。</p><div class="corpus-count"><span><b>3</b> 压缩对象</span><span><b>16</b> 研究专题</span><span><b>26</b> 技术路线</span><a href="compression-foundations.html">基础原理与动画 ↗</a></div></div>'
    body=intro+'<section id="compression-map"><h2>从瓶颈定位压缩对象</h2><div class="object-map">'
    for key,name,description,methods in groups:
        body+='<a href="#'+key+'"><span class="object-glyph">'+{'parameters':'W','activations':'X','kv_cache':'KV'}[key]+'</span><h3>'+name+'</h3><p>'+description+'</p><small>'+methods+'</small><b>浏览专题 ↓</b></a>'
    body+='</div></section><section id="foundations"><div class="section-line"><h2>压缩方法，改变了什么？</h2><a href="compression-foundations.html">观看完整原理动画 →</a></div><div class="foundation-summary">'
    methods=[('quantization','量化','用有限编码表示数值','降低每个数值的位数，控制舍入与裁剪误差。'),('pruning_sparsity','剪枝与稀疏','减少需要参与计算的部分','删去低贡献连接或结构；是否加速取决于执行方式。'),('distillation','知识蒸馏','让小模型学习大模型','学生结构决定资源规模，教师监督帮助保留能力。'),('low_rank','低秩分解','用更小的因子近似矩阵','以较低的秩表示主要信息，在近似误差与计算成本间取舍。')]
    for key,name,short,desc in methods: body+='<a href="compression-foundations.html#'+key+'"><h3>'+name+'</h3><strong>'+short+'</strong><p>'+desc+'</p><span>原理与演示 →</span></a>'
    body+='</div></section>'
    for key,name,desc,_ in groups:
        body+='<section id="'+key+'"><div class="section-line"><div><p class="eyebrow">'+desc+'</p><h2>'+name+'压缩</h2></div><span>'+str(sum(t['target_term_id']==key for t in topics))+' 个研究专题</span></div><div class="compression-grid">'+''.join(tile(t) for t in topics if t['target_term_id']==key)+'</div></section>'
    body+='<section id="validation"><h2>选择技术后，验证实际收益</h2><div class="validation-grid"><article><h3>质量门槛</h3><p>LLM 以 Qwen3.8-27B 为示例，同时覆盖降噪、翻译等领域模型。质量损失小于 1% 是目标，需先明确指标及相对下降或百分点口径。</p></article><article><h3>服务指标</h3><p>同模型、同负载记录权重大小、总内存、TTFT、TPOT 与达标吞吐；领域模型记录任务质量和端到端时延。</p></article><article><h3>执行条件</h3><p>分别核对 310P、910B 和 950（型号未确认）的工具链、导出格式及实际算子。原论文结果不直接等于昇腾收益。</p></article></div></section>'
    items=[('对象与方法','#compression-map'),('基础原理','#foundations')]+[(name+'压缩','#'+key) for key,name,_,_ in groups]+[('业务验证','#validation')]
    (out/'compression.html').write_text(page('推理压缩',body,items),encoding='utf-8')
    # Full dossiers: keep the imported claims and original evidence locations.
    for t in topics:
        key=t['compression_topic_id']; tc=sorted([c for c in cards if c['compression_topic_id']==key],key=lambda x:x['position'])
        ss=sorted([s for s in sections if s['compression_topic_id']==key],key=lambda x:x['position'])
        tr=sorted([r for r in routes if r['compression_topic_id']==key],key=lambda x:x['position'])
        tf=next((f for f in frames if f['compression_topic_id']==key),None)
        body='<a class="back" href="compression.html#'+t['target_term_id']+'">← 推理压缩</a><p class="eyebrow">研究专题</p><h1>'+e(t['title_zh'])+'</h1><p class="lead">'+e(t['question_zh'])+'</p>'
        body+='<section id="background"><h2>背景与挑战</h2>'
        if tf:
            for label,field in [('研究背景','why_zh'),('技术价值','value_zh'),('关键挑战','challenge_zh')]: body+='<h3>'+label+'</h3>'+paras(tf[field])
        else:
            for s in ss[:2]:body+='<h3>'+e(s['heading_zh'])+'</h3>'+paras(s['body_zh'])
        body+='</section><section id="mechanism"><h2>技术原理</h2><div class="mechanism-strip">'
        for s in sorted([s for s in steps if s['compression_topic_id']==key],key=lambda x:x['position']):body+='<article><h3>'+e(s['label_zh'])+'</h3>'+paras(s['body_zh'])+'</article>'
        body+='</div><a href="compression-foundations.html">查看共同基础与动画 →</a></section>'
        relevant=[r for r in industry if r['compression_topic_id']==key]
        if relevant:
            body+='<section id="industry"><h2>产业实现与部署条件</h2>'
            for r in sorted(relevant,key=lambda x:x['position']):
                body+='<article class="evidence-card"><h3>'+e(r['title_zh'])+'</h3>'
                for label,field in [('原始事实','fact_focus_zh'),('与本专题的关系','relevance_zh'),('实际影响','impact_zh'),('需要验证','check_zh'),('证据边界','boundary_zh')]:body+='<p><strong>'+label+'：</strong>'+e(r[field])+'</p>'
                body+=link(r['source_id'])+'<small class="evidence-ref">'+e(r['source_locator'])+'</small></article>'
            body+='</section>'
        if tr:
            body+='<section id="routes"><h2>技术路线</h2>'
            for r in tr:
                body+='<article class="evidence-card"><h3>'+e(r['title_zh'])+'</h3><p><strong>解决的问题：</strong>'+e(r['problem_zh'])+'</p>'+paras(r['principle_zh'])+'<ol>'+''.join('<li>'+e(r['step_'+str(i)+'_zh'])+'</li>' for i in range(1,4))+'</ol><p><strong>取舍：</strong>'+e(r['tradeoff_zh'])+'</p>'+link(r['source_id'])+'</article>'
            body+='</section>'
        kinds=[('mechanism','原理分析'),('papers','论文与关键效果'),('comparison','路线比较'),('boundary','适用边界'),('implication','落地启示'),('watch','下一步行动')]
        navitems=[('专题总览','compression.html'),('背景与挑战','#background'),('技术原理','#mechanism')]+([('产业实现','#industry')] if relevant else [])+([('技术路线','#routes')] if tr else [])
        comparisons=[r for r in assessments if r['compression_topic_id']==key]
        if comparisons:
            body+='<section id="assessments"><h2>关键效果与验证选择</h2>'
            navitems.append(('效果与验证','#assessments'))
            for r in sorted(comparisons,key=lambda x:x['position']):
                body+='<article class="evidence-card"><h3>'+e(r['label_zh'])+'</h3>'
                for label,field in [('技术表示','representation_zh'),('准备过程','preparation_zh'),('运行条件','runtime_zh'),('测试条件','conditions_zh'),('论文效果','result_zh'),('对比边界','boundary_zh'),('验证技术','probe_zh'),('选择建议','decision_zh')]:body+='<p><strong>'+label+'：</strong>'+e(r[field])+'</p>'
                body+='<a href="'+e(r['paper_url'])+'">论文原文 · '+e(r['result_locator'])+' ↗</a></article>'
            body+='</section>'
        for kind,title in kinds:
            subset=[c for c in tc if c['section_kind']==kind]
            if not subset:continue
            navitems.append((title,'#dossier-'+kind));body+='<section id="dossier-'+kind+'"><h2>'+title+'</h2>'
            for c in subset:
                body+='<article class="evidence-card"><span class="claim-kind">'+('论文报告结果' if c['claim_kind']=='author_result' else '研究分析与机制')+'</span><h3>'+e(c['title_zh'])+'</h3>'+paras(c['body_zh'])
                cr=[r for r in refs if r['card_id']==c['card_id']]
                for r in cr:body+='<div class="evidence-ref">'+link(r['source_id'])+'<small>'+e(r['locator_zh'])+' · '+e(r['observed_version'])+'</small></div>'
                body+='</article>'
            body+='</section>'
        body+='<section id="original-sections"><h2>研究补充</h2>'+''.join('<article class="evidence-card"><h3>'+e(s['heading_zh'])+'</h3>'+paras(s['body_zh'])+('<a class="source-link" href="'+e(s['evidence_url'],quote=True)+'">原始依据 ↗</a>' if s.get('evidence_url') else '')+'</article>' for s in ss)+'</section>'
        (out/('topic-'+key+'.html')).write_text(page(t['title_zh'],body,navitems),encoding='utf-8')
    # Existing teaching animations are preserved with local data and assets.
    foundation=rows('ic_compression_foundations'); lesson=rows('ic_foundation_lesson_steps'); values=rows('ic_foundation_lesson_values')
    urls=list(dict.fromkeys(r['source_url'] for r in foundation+lesson)); numbers={u:i+1 for i,u in enumerate(urls)}
    body='<a class="back" href="compression.html">← 推理压缩</a><h1>压缩基础</h1><p class="lead">看清改变的对象、编码和执行过程，再选择适合业务的路线。</p>'
    for key,name,_,_ in methods:
        body+='<section id="'+key+'"><h2>'+name+'</h2><lri-foundation-lesson data-method="'+key+'"></lri-foundation-lesson>'
        for f in sorted([f for f in foundation if f['method_id']==key],key=lambda x:x['position']):
            body+='<article class="evidence-card"><h3>'+e(f['title_zh'])+'</h3>'+paras(f['summary_zh'])+('<pre class="formula">'+e(f['formula'])+'</pre>' if f['formula'] else '')+paras(f['body_zh'])+'<a href="#foundation-ref-'+str(numbers[f['source_url']])+'">['+str(numbers[f['source_url']])+']</a></article>'
        body+='</section>'
    body+='<section><h2>参考资料</h2>'+''.join('<p id="foundation-ref-'+str(numbers[u])+'"><a href="'+e(u,quote=True)+'">['+str(numbers[u])+'] '+e(next(x['source_title'] for x in foundation+lesson if x['source_url']==u))+' ↗</a></p>' for u in urls)+'</section><script type="module" src="compression-lessons.js"></script>'
    (out/'compression-foundations.html').write_text(page('压缩基础',body,[(n,'#'+k) for k,n,_,_ in methods]),encoding='utf-8')
    vendor=root/'vendor'/'ai-infra'; player=vendor/'business_insight'/'cloud_core'
    for name in ['foundation-player.js','foundation-scenes.js']:
        text=(player/name).read_text(encoding='utf-8').replace('../../assets/lri-motion-scene.js','./lri-motion-scene.js')
        (out/name).write_text(text,encoding='utf-8')
    for name in ['lri-motion-scene.js','lri-selected-language.js']:shutil.copy2(vendor/'assets'/name,out/name)
    ui=json.loads((player/'data'/'foundations-ui.zh.json').read_text(encoding='utf-8'))['strings']
    (out/'compression-lessons.json').write_text(json.dumps(dict(steps=lesson,values=values,ui=ui,referenceNumbers=numbers),ensure_ascii=False),encoding='utf-8')
    shutil.copy2(root/'content'/'compression-reader.css',out/'compression-reader.css')
    shutil.copy2(root/'content'/'compression-lessons.js',out/'compression-lessons.js')
