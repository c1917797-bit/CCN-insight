# -*- coding: utf-8 -*-
"""Publish the reviewed research snapshot under the formal CCN site."""
from pathlib import Path
import shutil
import re
import json
from html import escape

def integrate(root):
    source=root/'research'/'ai-infra'/'dist'
    target=root/'dist'/'ai-infra'
    target.mkdir(parents=True,exist_ok=True)
    original='https://c1b3ie6ayp-sworks-lrigit-tpc.ru.yxsbase.win/business_insight/cloud_core/index.html'
    navigation='<div class="infra-navigation"><nav class="infra-primary" aria-label="AI Infra 主导航"><a class="selected" href="index.html">技术地图</a><a href="'+original+'#view-updates" title="查看原推理压缩站点的本期动态">本期动态 ↗</a><a href="'+original+'#view-home" title="查看原推理压缩站点的洞察报告">洞察报告 ↗</a><a href="'+original+'#view-reports" title="查看原推理压缩站点的洞察归档">洞察归档 ↗</a></nav><nav class="infra-support" aria-label="研究辅助入口"><a href="'+original+'#view-sources" title="查看信息源目录">信息来源 ↗</a><a href="methods.html">研究方法</a></nav></div>'
    for f in source.iterdir():
        if f.is_file():
            shutil.copy2(f,target/f.name)
    for source_page in source.glob('*.html'):
        f=target/source_page.name
        text=f.read_text(encoding='utf-8')
        text=text.replace('AI Infra 研究预览','AI Infra 根技术')
        text=text.replace('<small>研究预览</small>','<small>根技术研究</small>')
        text=text.replace('<span class="draft">独立审阅稿 · 未替换对外版本</span>','<a class="draft" href="/">← CCN 首页</a>')
        text=text.replace('本预览','本专题').replace('到本预览','到本专题')
        text=text.replace('</header>','</header>'+navigation)
        text=text.replace('</head>','<link rel="stylesheet" href="funnel.css"></head>')
        if f.name=='index.html':
            text=text.replace('href="'+original+'#view-topics" target="_blank" rel="noopener noreferrer" title="打开原有完整推理压缩内容"','href="compression.html" title="查看推理压缩研究专题"')
            text=text.replace('点击一级标题「推理压缩」打开原有完整内容','点击一级标题「推理压缩」进入完整专题目录')
            workflow='''<section class="evidence-funnel" aria-labelledby="funnel-title"><p class="eyebrow">FROM SIGNALS TO INSIGHT</p><h2 id="funnel-title">信息筛选与内容沉淀</h2><p>广泛寻找线索，逐层核对，最终留下与业务问题相关、值得学习或验证的技术。</p><ol><li><b>01 · 广泛采集</b><span>从论文、官方文档、开源仓库与产业资讯中寻找线索。</span></li><li><b>02 · 去重与时间筛选</b><span>合并重复报道，区分首次发布、版本更新和历史资料。</span></li><li><b>03 · 按根技术归类</b><span>对应技术地图，说明它处理什么挑战、采用什么路线。</span></li><li><b>04 · 核对关键证据</b><span>回到原文核对模型、测试条件、指标与适用边界。</span></li><li><b>05 · 筛出业务价值</b><span>明确值得验证的具体技术、预期收益及下一步实验。</span></li></ol><div class="funnel-outcomes"><article><h3>研究专题 · 沉淀长期知识</h3><p>吸收经核对的基本原理、关键挑战、技术路线与适用条件。</p></article><article><h3>本期动态 · 记录当月变化</h3><p>收录当月新增论文、版本和产业进展，说明相对已有路线的新变化。</p></article><article><h3>洞察报告 · 形成取舍建议</h3><p>综合事实与业务约束，给出优先验证、继续跟踪或暂缓投入的判断。</p></article></div><p class="funnel-status">流程说明：这是后续采用的研究工作方式。目前内容来自定向选源与原文核查，尚未实现全部信息源的自动采集与筛选。</p></section>'''
            methods=re.sub(r'<main id="main">.*?</main>','<main id="main"><a href="index.html">← 技术地图</a>'+workflow+'</main>',text,flags=re.S)
            methods=methods.replace('<title>根技术地图','<title>研究方法').replace('class="selected" href="index.html"','href="index.html"').replace('href="methods.html">研究方法','class="selected" href="methods.html">研究方法')
            methods=methods.replace('<script src="app.js"></script>','')
            (target/'methods.html').write_text(methods,encoding='utf-8')
        f.write_text(text,encoding='utf-8')
    shutil.copy2(root/'content'/'funnel.css',target/'funnel.css')
    template=(target/'compression-quantization.html').read_text(encoding='utf-8')
    topics=json.loads((root/'research'/'ai-infra'/'compression-topics.json').read_text(encoding='utf-8'))['rows']
    body='<a class="back" href="index.html#compression">← 根技术地图</a><p class="eyebrow">AI INFRA / 推理压缩</p><h1>推理压缩</h1><p class="lead">从模型量化与模型小型化进入研究，再按权重、激活和 KV Cache 查看具体技术。以业务质量为约束，判断容量、时延和吞吐能否获得实际收益。</p><div class="grid"><a class="card" href="compression-quantization.html"><h3>模型量化</h3><p>通过低比特表示与误差控制，研究更低的存储和读取成本。</p><span class="more">进入专题 →</span></a><a class="card" href="compression-small.html"><h3>模型小型化</h3><p>通过剪枝、蒸馏与低秩分解，研究更紧凑的部署模型。</p><span class="more">进入专题 →</span></a></div><section class="prose"><h2>按压缩对象深入研究</h2><p>保留已有专题及证据。以下为内容快照，原站交互演示与报告附件仍可通过完整内容入口查看。</p><div class="grid">'
    for item in sorted(topics,key=lambda x:x['row']['position']):
        t=item['row']
        body+='<a class="card" href="topic-'+escape(t['compression_topic_id'])+'.html"><h3>'+escape(t['title_zh'])+'</h3><p>'+escape(t['question_zh'])+'</p><span class="more">阅读专题 →</span></a>'
    body+='</div></section><section class="prose"><a href="'+original+'#view-topics">原站完整内容与演示 ↗</a></section>'
    template=re.sub(r'<main id="main">.*?</main>','<main id="main">'+body+'</main>',template,flags=re.S).replace('<title>模型量化','<title>推理压缩')
    (target/'compression.html').write_text(template,encoding='utf-8')
