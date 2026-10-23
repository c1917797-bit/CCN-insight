# -*- coding: utf-8 -*-
from pathlib import Path
from html import escape as e
import json

def render(root):
    base=Path(root); out=base/'dist'
    packs=[json.loads((base/'content'/f'{name}.json').read_text(encoding='utf-8')) for name in ['sections','entries']]
    assert packs[0]['revision']==packs[1]['revision'] and all(not p['truncated'] for p in packs)
    sections=sorted([r['row'] for r in packs[0]['rows'] if not r['deleted']],key=lambda r:r['position'])
    entries=sorted([r['row'] for r in packs[1]['rows'] if not r['deleted']],key=lambda r:r['position'])
    # Formal CCN deployment override; retain the imported TableGit snapshot unchanged.
    entries=[dict(x, url='/ai-infra/', summary='根技术地图 · 研究专题 · 推理压缩') if x['id']=='ai-infra' else x for x in entries]
    assert all(x['section_id'] in {s['id'] for s in sections} and (x['url'].startswith('https://') or x['url']=='/ai-infra/') for x in entries)
    links=''.join(f'<a class="direct" href="{e(x["url"],quote=True)}"><span><b>{e(x["title"])}</b><small>{e(x["summary"])}</small></span><i>↗</i></a>' for x in entries)
    cards=''
    for s in sections:
        live=s['status']=='active'
        cards+=f'<article class="space {"live" if live else "planned"}" id="{s["id"]}" style="--accent:{s["accent"]}"><div class="space-meta"><span>0{s["position"]} / {s["id"].upper()}</span><span class="status">{"已接入" if live else "筹备中"}</span></div><div class="space-title"><h2>{s["title"]}</h2><span class="mini-orbit" aria-hidden="true"></span></div><p>{e(s["summary"])}</p>'+(links if live else '<div class="waiting">内容准备中<span>—</span></div>')+'</article>'
    nav=''.join(f'<a href="#{s["id"]}">{s["title"]}</a>' for s in sections)
    revision=packs[0]['revision']
    html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="CCN Insight：极智、极稳、极简、极优。直达 AI Infra 与 Agent 研究洞察。"><title>CCN Insight · 探索技术的下一步</title><link rel="stylesheet" href="home.css"></head><body><a class="skip" href="#spaces">跳到研究入口</a><header><a class="brand" href="/">CCN<span> INSIGHT</span><i></i></a><nav aria-label="四大板块">'''+nav+'''</nav><button id="motion" aria-pressed="false">暂停动效</button></header><main><section class="hero"><div class="hero-copy"><div class="eyebrow"><span></span> IDEAS INTO INSIGHT</div><h1>让探索，<br>走向<span>下一步。</span></h1><p>把分散的技术线索，连接成清晰的研究方向。<br>从 AI 基础设施到 Agent，直达你关心的洞察。</p><div class="hero-actions"><a class="primary" href="#zhi">进入极智 <span>↗</span></a><a class="secondary" href="#spaces">探索四大板块 ↓</a></div><div class="facts"><span><b>04</b> 内容板块</span><span><b>02</b> 研究入口</span><span class="fact-note">持续积累 · 独立思考</span></div></div><div class="universe" aria-label="四大板块连接图"><div class="halo"></div><svg class="orbital" viewBox="0 0 600 600" role="img" aria-label="四个板块围绕 CCN 洞察空间连接"><defs><linearGradient id="g"><stop stop-color="#a294ff"/><stop offset="1" stop-color="#5fddcb"/></linearGradient></defs><g fill="none" stroke="url(#g)"><circle class="outer" cx="300" cy="300" r="244"/><circle class="middle" cx="300" cy="300" r="192"/><ellipse class="ellipse" cx="300" cy="300" rx="244" ry="90"/><ellipse class="ellipse second" cx="300" cy="300" rx="244" ry="90"/><path class="signal" d="M300 56A244 244 0 1 1 299 56"/></g><g class="core"><circle cx="300" cy="300" r="86" fill="#151b32" stroke="#a69aff" stroke-opacity=".5"/><text x="300" y="299" text-anchor="middle" fill="#f4f4ff" font-size="38" font-weight="700">CCN</text><text x="300" y="326" text-anchor="middle" fill="#9aa7c8" font-size="10" letter-spacing="5">INSIGHT</text></g></svg><a class="node n1" href="#zhi"><b>极智</b><small>AI Infra / Agent</small></a><a class="node n2" href="#wen"><b>极稳</b><small>筹备中</small></a><a class="node n3" href="#jian"><b>极简</b><small>筹备中</small></a><a class="node n4" href="#you"><b>极优</b><small>筹备中</small></a><span class="orbit-caption">四个方向 · 一个持续生长的洞察空间</span></div></section><section id="spaces"><div class="section-heading"><div><span class="eyebrow">EXPLORE THE SPACE</span><h2>选择方向，直接开始。</h2></div><p>内容入口集中呈现，不再层层跳转。</p></div><div class="spaces">'''+cards+'''</div></section><section class="closing"><span>连接信息 · 形成判断 · 沉淀知识</span><p>让每一次阅读，都成为下一次探索的起点。</p></section></main><footer><b>CCN INSIGHT</b><span>研究入口目录 · <code>'''+revision[:8]+'''</code></span><a href="#" id="top">回到顶部 ↑</a></footer><script src="home.js"></script></body></html>'''
    (out/'index.html').write_text(html,encoding='utf-8')

if __name__=='__main__':render(Path(__file__).parent)
