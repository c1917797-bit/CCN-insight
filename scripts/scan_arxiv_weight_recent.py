# -*- coding: utf-8 -*-
"""Bounded recent-index discovery; hits remain candidates until primary review."""
import concurrent.futures, html, json, re, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/source-audits/2026-10-23'
def scan(cat):
 url='https://arxiv.org/list/'+cat+'/recent?skip=0&show=2000'
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CCN-Insight-Source-Audit/1.0'}),timeout=25) as r:text=r.read(8000000).decode('utf-8','replace')
  dt=re.findall(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>',text,re.S)
  candidates=[]
  for head,body in dt:
   match=re.search(r'/abs/([\d.]+)',head);title=re.search(r'list-title[^>]*>(.*?)</div>',body,re.S)
   if not match or not title:continue
   title=html.unescape(re.sub('<[^>]+>',' ',title.group(1)));title=' '.join(title.split()).removeprefix('Title:').strip()
   if re.search(r'quantiz|low.bit|low.precision|fp4|fp8|int4|int8|codebook|ternary|binary.weight',title,re.I):candidates.append(dict(arxiv_id=match.group(1),title=title,status='title_candidate_not_full_review'))
  return dict(category=cat,url=url,received_entries=len(dt),candidates=candidates,boundary='Recent multi-day index, up to 2000 entries; title filter is not abstract/full-text exclusion; not a complete October census.')
 except Exception as e:return dict(category=cat,url=url,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(scan,['cs.CL','cs.LG','cs.AI','cs.DC']))
(OUT/'arxiv-recent.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False))
