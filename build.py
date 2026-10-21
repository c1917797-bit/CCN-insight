# -*- coding: utf-8 -*-
from pathlib import Path
import json
p=Path(__file__).parent/'dist'; p.mkdir(exist_ok=True)
parts=[('zhi','极智','01','#405cf5'),('wen','极稳','02','#087d79'),('jian','极简','03','#b27324'),('you','极优','04','#8557b7')]
def art(i):
    shapes=['<path d="M80 170 180 60 280 170 180 280Z"/><path d="m80 170 200 0M180 60v220M130 115l100 110m0-110L130 225"/><circle cx="180" cy="170" r="60"/>','<rect x="95" y="85" width="170" height="170" rx="45"/><rect x="125" y="115" width="110" height="110" rx="24"/><path d="m145 170 23 24 45-50"/>','<circle cx="145" cy="170" r="75"/><circle cx="210" cy="170" r="75"/><path d="M100 170h160"/>','<path d="m180 65 25 70 75 35-75 30-25 75-30-75-70-30 70-35Z"/><circle cx="180" cy="170" r="97"/>']
    return '<svg viewBox="0 0 360 340" aria-hidden="true"><g>'+shapes[i]+'</g></svg>'
nav='<a class="brand" href="index.html"><b>CCN<span>·</span></b><small>INSIGHT</small></a><nav aria-label="主导航"><a href="index.html">总览</a>'+''.join(f'<a href="{k}.html">{n}</a>' for k,n,_,_ in parts)+'</nav>'
def shell(title,body):return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="CCN Insight：极智、极稳、极简、极优，四个独立的内容空间。"><title>'+title+' · CCN Insight</title><link rel="stylesheet" href="style.css"></head><body><a class="skip" href="#main">跳到正文</a><header>'+nav+'</header><main id="main">'+body+'</main><footer><b>CCN INSIGHT</b><span>极智 · 极稳 · 极简 · 极优</span><a href="index.html">返回总览 ↗</a></footer><script src="app.js"></script></body></html>'
cards=''.join(f'<a class="portal" href="{k}.html" style="--accent:{c}"><div class="cardtop"><span>SECTION / {num}</span><span>↗</span></div>{art(i)}<div class="cardbottom"><h2>{n}</h2><span>进入板块 →</span></div></a>' for i,(k,n,num,c) in enumerate(parts))
infra='https://c1b3ie6ayp-sworks-lrigit-tpc.ru.yxsbase.win/business_insight/cloud_core/index.html?month=2026-10&amp;scope=ic-2026-10-public-20261007-v1#view-sources'
agent='https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/#analysis'
zhi=f'<article class="portal portal-zhi" id="zhi" style="--accent:#405cf5"><div class="cardtop"><span>SECTION / 01</span><span>↗</span></div><h2>极智</h2><p class="zhi-intro">从研究方向，直接进入洞察。</p><div class="zhi-links"><a href="{infra}"><span class="zhi-link-top"><b>AI Infra</b><span>↗</span></span><small>推理压缩与 AI 基础设施</small></a><a href="{agent}"><span class="zhi-link-top"><b>Agent</b><span>↗</span></span><small>Agent 编排与调度</small></a></div></article>'
cards=zhi+cards[cards.index('</a>')+4:]
nav=nav.replace('href="zhi.html"','href="index.html#zhi"')
home='<section class="hero"><div class="eyebrow"><span class="dot"></span> CCN / INSIGHT SPACE</div><div class="herogrid"><h1>独立思考。<br><span>持续探索。</span></h1><div class="intro"><p>四个板块，持续探索。</p><p class="muted">极智聚合 AI Infra 与 Agent 洞察，<br>选择研究方向，即刻开始阅读。</p><a class="textlink" href="#explore">探索四个板块 <span>↓</span></a></div></div></section><section id="explore" aria-label="四个板块"><div class="sectionhead"><h2>选择一个方向</h2><span>FOUR SECTIONS / 01—04</span></div><div class="portals">'+cards+'</div></section><section class="about"><span class="eyebrow">持续生长的内容空间</span><h2>从一个问题开始，<br>把思考留在这里。</h2><p>极智已接入两个研究方向。其他板块将逐步补充。</p></section>'
(p/'index.html').write_text(shell('总览',home),encoding='utf-8')
for i,(k,n,num,c) in enumerate(parts):
 body=f'<section class="subhero" style="--accent:{c}"><a class="back" href="index.html">← 全部板块</a><div class="eyebrow">SECTION / {num}</div><div class="subgrid"><div><h1>{n}</h1><p class="muted">一个独立的内容空间。</p></div>{art(i)}</div></section><section class="workspace"><div class="sectionhead"><h2>板块内容</h2><span class="badge">筹备中</span></div><div class="empty"><span class="emptyicon">＋</span><h3>从第一篇内容开始</h3><p>这里将收录「{n}」的专题与文章。<br>板块定位确认后，再添加真实内容。</p></div></section><section class="others"><h2>继续探索</h2><div>'+''.join(f'<a href="{x}.html"><span>{y}</span> ↗</a>' for x,y,_,_ in parts if x!=k)+'</div></section>'
 if k=='zhi':
  start=body.index('<section class="workspace">'); end=body.index('<section class="others">')
  body=body[:start]+'''<section class="workspace"><div class="sectionhead"><h2>极智 · 两个研究方向</h2><span>AI INFRA / AGENT</span></div><div class="destinations"><a class="destination" href="https://c1b3ie6ayp-sworks-lrigit-tpc.ru.yxsbase.win/business_insight/cloud_core/index.html?month=2026-10&amp;scope=ic-2026-10-public-20261007-v1#view-sources" target="_blank" rel="noopener noreferrer"><div class="destination-meta">01 / AI INFRA <span>↗</span></div><h2>极智-AI infra</h2><p>推理压缩与 AI 基础设施</p><div class="destination-tags"><span>信息来源</span><span>技术地图</span><span>专题洞察</span></div><div class="destination-action">进入 AI infra 洞察 <span>新窗口打开 ↗</span></div></a><a class="destination agent" href="https://cloud-core-agent-scheduling-preview.sunshinepmy.chatgpt.site/business_insight/cloud_core/agent_orchestration/#analysis" target="_blank" rel="noopener noreferrer"><div class="destination-meta">02 / AGENT <span>↗</span></div><h2>极智-Agent</h2><p>Agent 编排与调度</p><div class="destination-tags"><span>Agent</span><span>编排调度</span><span>分析洞察</span></div><div class="destination-action">进入 Agent 洞察 <span>新窗口打开 ↗</span></div></a></div></section>'''+body[end:]
 if k=='zhi':
  body='<script>location.replace("index.html#zhi")</script><p>极智入口已移至首页。<a href="index.html#zhi">前往极智</a></p>'
 (p/(k+'.html')).write_text(shell(n,body).replace('href="zhi.html"','href="index.html#zhi"'),encoding='utf-8')
from home_design import render
render(Path(__file__).parent)
from publish_infra import integrate
integrate(Path(__file__).parent)
