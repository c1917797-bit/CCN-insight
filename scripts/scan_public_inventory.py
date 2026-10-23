# -*- coding: utf-8 -*-
"""Public entrypoint audit. Reachability is NOT literature/event coverage."""
import argparse, concurrent.futures, datetime, hashlib, html, json, re, urllib.error, urllib.request, urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/compression/tables'
def rows(t):
 return [j['row'] for j in map(json.loads,(BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()) if not j.get('deleted')]
sources={r['source_id']:r for r in rows('cloud_core_sources')}
channels=rows('ic_channels')
class PublicRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if urllib.parse.urlsplit(newurl).scheme!='https':raise urllib.error.HTTPError(newurl,code,'Non-HTTPS redirect not followed',headers,fp)
  if code==308:return urllib.request.Request(newurl,headers=dict(req.headers),method=req.get_method())
  return super().redirect_request(req,fp,code,msg,headers,newurl)
 http_error_308=urllib.request.HTTPRedirectHandler.http_error_301
opener=urllib.request.build_opener(PublicRedirect())
def fetch(url):
 try:
  p=urllib.parse.urlsplit(url)
  if p.scheme!='https' or p.username or p.password: return {'status':'skipped_non_public_https'}
  url=urllib.parse.quote(url,safe=':/?=&%#;+,@!$()*[]~-._')
  req=urllib.request.Request(url,headers={'User-Agent':'CCN-Insight-Source-Audit/1.0'})
  with opener.open(req,timeout=15) as response:
   body=response.read(700000)
   content=body.decode('utf-8','replace');title=re.search(r'<title[^>]*>(.*?)</title>',content,re.I|re.S)
   return dict(status='entrypoint_fetched',http_status=response.status,final_url=response.url,bytes_sampled=len(body),sample_sha256=hashlib.sha256(body).hexdigest(),content_type=response.headers.get('Content-Type',''),observed_title=html.unescape(' '.join(title.group(1).split()))[:240] if title else '',last_modified=response.headers.get('Last-Modified',''),coverage='entrypoint_sample_only; no pagination/date-window completeness')
 except Exception as e:return dict(status='fetch_failed',http_status=e.code if isinstance(e,urllib.error.HTTPError) else None,error=re.sub(r'[\x00-\x1f]',' ',str(e))[:220])
urls=sorted({sources.get(c.get('source_id'),{}).get('canonical_url','') for c in channels}-{''})
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
 results=dict(zip(urls,pool.map(fetch,urls)))
records=[dict(channel_id=c['channel_id'],title=c.get('title_zh'),source_id=c.get('source_id'),url=sources.get(c.get('source_id'),{}).get('canonical_url',''),**results.get(sources.get(c.get('source_id'),{}).get('canonical_url',''),{'status':'missing_source_url'})) for c in channels]
counts={k:sum(r['status']==k for r in records) for k in sorted({r['status'] for r in records})}
out=ROOT/'research/source-audits/2026-10-23';out.mkdir(parents=True,exist_ok=True)
args=argparse.ArgumentParser();args.add_argument('--output',default='entrypoints.json');args=args.parse_args()
if Path(args.output).name!=args.output:raise ValueError('Output must be a file name')
(out/args.output).write_text(json.dumps(dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),channels=len(channels),unique_urls=len(urls),counts=counts,boundary='All registered channel entrypoints attempted; not full event retrieval, not a full October census. Failures are not exclusions.',records=records),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(channels=len(channels),unique_urls=len(urls),counts=counts)))
