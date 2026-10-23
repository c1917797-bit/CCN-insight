"""Fetch public candidate metadata, never promote it to reviewed report evidence.

Usage: python scripts/collect_agent_signals.py --start 2026-10-17 --end 2026-10-23
Public GET only; bounded retries and bytes; CSV dedupe preserves previous review state.
"""
from __future__ import annotations
import argparse
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'research/agent-scheduling'
FIELDS = ['id','channel_id','feed_id','source_key','title','url','published','revised','feed_date','version','matched_terms','first_seen','last_seen','review_status']
RUN_FIELDS = ['run_id','feed_id','channel_id','checked_at','window_start','window_end','status','fetched','in_window','matched','added','attempts','scope','error']
TERMS = {'scheduling':r'schedul', 'routing':r'rout(?:e|es|ed|ing|er)', 'agent':r'agent',
         'queue':r'queue|poller', 'cache':r'cache|caching', 'resource':r'resource|placement|autoscal',
         'fairness':r'fairness|priority|prioriti', 'workflow':r'workflow|checkpoint'}

def read(path):
    if not path.exists(): return []
    with path.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def write(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix+'.tmp')
    with temp.open('w', encoding='utf-8', newline='') as f:
        out = csv.DictWriter(f, fieldnames=fields); out.writeheader(); out.writerows(rows)
    temp.replace(path)

def safe_url(url):
    p=urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password:
        raise ValueError('Expected a public HTTPS source URL without credentials')
    return urlunsplit((p.scheme,p.netloc,p.path,p.query,''))

def identity(url):
    url=safe_url(url)
    p=urlsplit(url)
    # All arXiv revisions share one paper identity; retain revised/version fields.
    if p.hostname in {'arxiv.org','export.arxiv.org','rss.arxiv.org'}:
        paper=re.search(r'(\d{4}\.\d{4,5})(?:v\d+)?',p.path)
        if paper:return 'arxiv:'+paper[1]
    return urlunsplit((p.scheme,p.netloc.lower(),p.path.rstrip('/'),'',''))

def date_value(value):
    value=(value or '').strip()
    if not value:return ''
    try:return date.fromisoformat(value[:10]).isoformat()
    except ValueError:return ''

def parse(feed, payload):
    if feed['adapter']=='github':
        data=json.loads(payload)
        if not isinstance(data,list):raise ValueError('Expected a release list')
        return [dict(title=r.get('name') or r.get('tag_name',''),url=safe_url(r['html_url']),
                     published=date_value(r.get('published_at')),revised='',feed_date='',
                     version=('预发布 · ' if r.get('prerelease') else '正式发布 · ')+r.get('tag_name',''),
                     search=(r.get('name') or '')+' '+(r.get('body') or ''))
                for r in data if not r.get('draft')]
    if feed['adapter']=='atom':
        root=ET.fromstring(payload); ns={'a':'http://www.w3.org/2005/Atom'}; out=[]
        for entry in root.findall('a:entry',ns):
            title=entry.findtext('a:title','',ns).strip()
            links=entry.findall('a:link',ns)
            link=next((x.get('href') for x in links if x.get('rel','alternate')=='alternate'),entry.findtext('a:id','',ns))
            if link.startswith('http://arxiv.org/'):link=link.replace('http:','https:',1)
            # arXiv's RSS/Atom dates describe the announcement batch, including replacements.
            # Neither published nor updated here proves the paper's first submission/revision date.
            out.append(dict(title=title,url=safe_url(link),published='',revised='',
                            feed_date=date_value(entry.findtext('a:updated','',ns) or entry.findtext('a:published','',ns)),version='订阅公告 · 首发与修订日期待核',
                            search=title+' '+entry.findtext('a:summary','',ns)))
        return out
    raise ValueError('Unsupported feed adapter')

def retrieve(feed):
    url=safe_url(feed['url']); allowed={'api.github.com','rss.arxiv.org'}
    if urlsplit(url).hostname not in allowed: raise ValueError('Feed host is outside the reviewed allowlist')
    error=''
    for attempt in range(1,4):
        try:
            request=Request(url,headers={'User-Agent':'CCN-Insight-Research/1.0','Accept':'application/json, application/atom+xml'})
            with urlopen(request,timeout=18) as response:
                if urlsplit(response.url).hostname not in allowed:raise ValueError('Unexpected redirect host')
                payload=response.read(4*1024*1024+1)
            if len(payload)>4*1024*1024:raise ValueError('Response exceeded 4 MiB')
            return parse(feed,payload),attempt,''
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc)[:140]
            if attempt<3:time.sleep(attempt*0.6)
    return [],3,error

def merge(existing, fresh):
    records={r['id']:dict(r) for r in existing}; added=0
    for row in fresh:
        old=records.get(row['id'])
        if old:
            # Observed updates must not erase manual review disposition or first-seen date.
            row={**row,'first_seen':old['first_seen'],'review_status':old['review_status']}
            row['published']=old.get('published') or row['published']
        else:added+=1
        records[row['id']]=row
    return sorted(records.values(),key=lambda r:(r['published'] or r['revised'],r['id']),reverse=True),added

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',required=True,type=date.fromisoformat)
    parser.add_argument('--end',required=True,type=date.fromisoformat)
    parser.add_argument('--feed',action='append',help='Limit to these configured feed IDs')
    parser.add_argument('--output-dir',type=Path,default=DATA)
    args=parser.parse_args()
    if args.start>args.end or args.end>date.today():parser.error('Expected a non-future ordered date window')
    feeds=read(DATA/'collection-feeds.csv')
    if args.feed:
        known={r['id'] for r in feeds}
        if set(args.feed)-known:parser.error('Unknown feed ID')
        feeds=[r for r in feeds if r['id'] in args.feed]
    checked=datetime.now(timezone.utc).isoformat(timespec='seconds')
    run_id=checked.replace(':','').replace('+','_')
    existing=read(args.output_dir/'signal-candidates.csv'); logs=[]
    with ThreadPoolExecutor(max_workers=4) as executor:
        for feed,(items,attempts,error) in zip(feeds,executor.map(retrieve,feeds)):
            selected=[]; in_window=0
            for item in items:
                dates=[d for d in (item['published'],item['revised'],item['feed_date']) if d]
                if not any(args.start.isoformat()<=d<=args.end.isoformat() for d in dates):continue
                in_window+=1
                terms=[k for k,p in TERMS.items() if re.search(p,item['search'],re.I)]
                if not terms:continue
                key=identity(item['url']); identifier=hashlib.sha256(key.encode()).hexdigest()[:16]
                selected.append(dict(id=identifier,channel_id=feed['channel_id'],feed_id=feed['id'],source_key=key,
                    title=item['title'],url=item['url'],published=item['published'],revised=item['revised'],feed_date=item['feed_date'],version=item['version'],
                    matched_terms='|'.join(terms),first_seen=checked,last_seen=checked,review_status='待原文审阅'))
            existing,added=merge(existing,selected)
            logs.append(dict(run_id=run_id,feed_id=feed['id'],channel_id=feed['channel_id'],checked_at=checked,
                window_start=args.start.isoformat(),window_end=args.end.isoformat(),status='失败' if error else '已读取有限列表',
                fetched=len(items),in_window=in_window,matched=len(selected),added=added,attempts=attempts,scope=feed['scope'],error=error))
            print(f'{feed["id"]}: {len(items)} received, {len(selected)} candidates, {added} new'+('; failed' if error else ''))
    write(args.output_dir/'signal-candidates.csv',existing,FIELDS)
    write(args.output_dir/'collection-runs.csv',read(args.output_dir/'collection-runs.csv')+logs,RUN_FIELDS)
    print('Candidate metadata only. No reviewed evidence or website was modified; failures remain visible.')

if __name__=='__main__':main()
