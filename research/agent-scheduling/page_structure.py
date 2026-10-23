"""One question per page, parallel section labels, explicit evidence-to-judgment order."""
import re
from html import escape as e
from decision_map import read


def sections(title):
    rows=[r for r in read('page-sections.csv') if r['page_title']==title]
    assert rows, f'No reading structure for {title}'
    return rows


def structure(title, body):
    rows=sections(title)
    for i,r in enumerate(rows,1):
        pattern=r'(<section id="'+re.escape(r['section_id'])+r'"[^>]*>)(?:<p class="eyebrow">.*?</p>)?<h2>.*?</h2>'
        header=f'<p class="eyebrow">{i:02d} / {e(r["label"])}</p><h2>{e(r["heading"])}</h2>'
        body,n=re.subn(pattern,lambda m:m[1]+header,body,count=1,flags=re.S)
        assert n==1,(title,r['section_id'])
    toc='<nav class="page-outline" aria-label="本页阅读提纲">'+''.join(
        f'<a href="#{r["section_id"]}"><span>{i:02d}</span><strong>{e(r["label"])}</strong><small>{e(r["heading"])}</small></a>' for i,r in enumerate(rows,1))+'</nav>'
    body=body.replace('</header>','</header>'+toc,1)
    nav='<p class="rail-note">本页目录</p><nav aria-label="本页章节">'+''.join(
        f'<a href="#{r["section_id"]}">{i:02d} {e(r["label"])}</a>' for i,r in enumerate(rows,1))+'</nav>'
    return body,nav


def object_guidance(key):
    row=next(r for r in read('object-recommendations.csv') if r['point_id']==key)
    values=''.join(f'<dt>{label}</dt><dd>{e(row[field])}</dd>' for label,field in [('先建基线','baseline'),('再做扩展','extension'),('判断依据','criterion'),('暂缓条件','defer')])
    return f'<section id="guidance"><p class="eyebrow">06 / 研究建议</p><h2>怎样分阶段推进本层研究</h2><article class="structured-advice"><p class="eyebrow">研究设计 · 尚待实测</p><h3>{e(row["conclusion"])}</h3><dl>{values}</dl></article></section>'


def route_challenge(route_id):
    row=next(r for r in read('route-challenges.csv') if r['route_id']==route_id)
    return f'<p class="route-problem"><strong>对应挑战：</strong>{e(row["challenge"])}</p>'
