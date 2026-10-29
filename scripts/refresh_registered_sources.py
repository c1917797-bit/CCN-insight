"""Read registered public source indexes and official release bodies for review.

An index fetched successfully is not full publication coverage or model reading.
Only public, enabled P0/P1 source URLs are fetched; no account/secret is used.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor,as_completed
from html.parser import HTMLParser
from pathlib import Path
import argparse,base64,datetime as dt,hashlib,ipaddress,json,re,socket,urllib.parse,urllib.request
ROOT=Path(__file__).resolve().parents[1]

def rows(name):
    return [x['row'] for x in map(json.loads,(ROOT/'data/compression/tables'/name/'rows.jsonl').read_text(encoding='utf-8').splitlines()) if not x.get('deleted')]

def registry():
    families={r['family_id']:r for r in rows('ic_source_families')};channels={r['channel_id']:r for r in rows('ic_channels')};sources={r['source_id']:r for r in rows('cloud_core_sources')};result={}
    for member in rows('ic_channel_families'):
        channel=channels[member['channel_id']]
        if not channel.get('enabled') or channel.get('priority') not in ['P0','P1']:continue
        f=families[member['family_id']];s=sources[channel['source_id']];url=s['canonical_url']
        if urllib.parse.urlsplit(url).scheme!='https':continue
        result.setdefault(url,{'registered_url':url,'source_id':s['source_id'],'family_id':f['family_id'],'source_name':f['title_zh'],'group':f['ui_group']})
    return list(result.values())

class Text(HTMLParser):
    def __init__(self):super().__init__();self.skip=0;self.parts=[];self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag in ['script','style','noscript']:self.skip+=1
        if tag=='a':
            href=dict(attrs).get('href','')
            if href:self.links.append(href)
    def handle_endtag(self,tag):
        if tag in ['script','style','noscript']:self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip and data.strip():self.parts.append(data.strip())

def public(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password:raise ValueError('Not a public HTTPS source')
    for a in socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM):
        if not ipaddress.ip_address(a[4][0]).is_global:raise ValueError('Nonpublic source address')

class Redirect(urllib.request.HTTPRedirectHandler):
    # Python 3.9 does not implement 308; these acquisitions only issue GET.
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        public(newurl)
        return super().redirect_request(req,fp,301 if code==308 and req.get_method()=='GET' else code,msg,headers,newurl)
    http_error_308=urllib.request.HTTPRedirectHandler.http_error_302

def fetch(entry,out):
    row={**entry,'fetched_at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'failed','model_read':False,'publication_window_complete':False}
    url=entry['registered_url'];p=urllib.parse.urlsplit(url);parts=p.path.strip('/').split('/')
    if p.hostname=='arxiv.org':
        row.update(status='handled_by_paged_arxiv_query',artifact='live-abstracts-20261029/receipt.json');return row
    if p.hostname=='github.com' and len(parts)>=2 and parts[0] not in ['trending','topics','collections','search'] and re.fullmatch(r'[\w.-]+',parts[0]) and re.fullmatch(r'[\w.-]+',parts[1]):
        page_size=entry.get('release_page_size',20)
        assert page_size in [1,20]
        url='https://api.github.com/repos/'+'/'.join(parts[:2])+'/releases?per_page='+str(page_size)+'&page=1';row['kind']='official_release_bodies_first_page'
    else:row['kind']='registered_source_index'
    row['request_url']=url;key=hashlib.sha256(url.encode()).hexdigest()[:20]
    try:
        public(url);req=urllib.request.Request(url,headers={'User-Agent':'CCN-Insight-Research/1.0','Accept':'application/json,text/html,application/atom+xml;q=0.9,*/*;q=0.5'})
        with urllib.request.build_opener(Redirect()).open(req,timeout=22) as response:
            blob=response.read(2*1024*1024+1);row.update(http_status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type',''))
        row['response_truncated']=len(blob)>2*1024*1024;blob=blob[:2*1024*1024]
        (out/(key+'.response')).write_bytes(blob);row.update(artifact=key+'.response',response_sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob),status='fetched')
        text=blob.decode('utf-8',errors='replace')
        if row['kind']=='official_release_bodies_first_page':
            releases=json.loads(text)
            if not isinstance(releases,list):raise ValueError('Unexpected GitHub release response')
            records=[{'title':r.get('name') or r.get('tag_name'),'tag':r.get('tag_name'),'url':r.get('html_url'),'published_at':r.get('published_at'),'prerelease':r.get('prerelease'),'body':r.get('body') or ''} for r in releases]
            row['release_count']=len(records);row['oldest_release']=records[-1]['published_at'] if records else None
            (out/(key+'.releases.json')).write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');row['extracted_artifact']=key+'.releases.json'
        else:
            parser=Text();parser.feed(text);(out/(key+'.text.txt')).write_text('\n'.join(parser.parts),encoding='utf-8');row['extracted_artifact']=key+'.text.txt'
            (out/(key+'.links.json')).write_text(json.dumps(sorted(set(urllib.parse.urljoin(row['final_url'],x) for x in parser.links if urllib.parse.urlsplit(urllib.parse.urljoin(row['final_url'],x)).scheme=='https')),ensure_ascii=False,indent=2),encoding='utf-8')
    except Exception as exc:
        row['error']=str(exc)[:400]
        row['status']='partial_unparsed' if row.get('artifact') else 'failed'
    return row

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True);p.add_argument('--retry-incomplete-json',action='store_true');p.add_argument('--retry-failed',action='store_true');args=p.parse_args();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    entries=registry();records=[];registered_count=len(entries);previous_by_url={}
    if args.retry_incomplete_json or args.retry_failed:
        previous=json.loads((out/'source-coverage.json').read_text(encoding='utf-8'))['records']
        previous_by_url={r['registered_url']:r for r in previous}
        retry={r['registered_url'] for r in previous if r.get('error') and (args.retry_failed or r.get('response_truncated'))}
        truncated={r['registered_url'] for r in previous if r.get('response_truncated') or 'ExLlamaV2' in r.get('source_name','')}
        entries=[dict(e,release_page_size=1) if e['registered_url'] in truncated else e for e in entries if e['registered_url'] in retry]
        records=[r for r in previous if r['registered_url'] not in retry]
        for r in records:
            if r.get('error'):r['status']='partial_unparsed' if r.get('artifact') else 'failed'
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs={pool.submit(fetch,x,out):x for x in entries}
        for future in as_completed(jobs):
            row=future.result();records.append(row);print(json.dumps({k:row.get(k) for k in ['source_name','status','http_status','release_count','error']},ensure_ascii=False),flush=True)
            old=previous_by_url.get(row['registered_url'])
            if old:row['previous_attempts']=old.get('previous_attempts',[])+[{k:v for k,v in old.items() if k!='previous_attempts'}]
            (out/'source-coverage.json').write_text(json.dumps({'registered_urls':registered_count,'processed_urls':len(records),'records':records,'coverage_boundary':'Index or first release page acquisition only; neither all publications nor model reading is implied.'},ensure_ascii=False,indent=2),encoding='utf-8')
