"""Collect original arXiv abstracts into a resumable, auditable review input.

This is acquisition, not model review. It never marks papers read, edits the
canonical research tables, or treats search matches as relevance decisions.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,time,urllib.parse,urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ATOM='{http://www.w3.org/2005/Atom}'
OPEN='{http://a9.com/-/spec/opensearch/1.1/}'
ARXIV='{http://arxiv.org/schemas/atom}'
CLASSICS=['1712.05877','2208.07339','2211.10438','2210.17323','2306.00978',
          '2402.04396','2404.00456','2405.16406','2402.02750','2301.00774',
          '2306.11695','2305.11627','1503.02531','1909.10351','1910.01108',
          '2306.08543','2403.07378','2312.05821']

def query(start,end):
    categories=' OR '.join('cat:'+c for c in ['cs.LG','cs.CL','cs.CV','cs.AI','cs.DC','cs.SD','eess.AS','stat.ML'])
    terms=' OR '.join('all:'+t for t in ['quantization','quantisation','pruning','distillation','"low-rank"','"sparse attention"','"KV cache"','"model compression"'])
    lo=start.replace('-','')+'0000';hi=end.replace('-','')+'2359'
    # The official API supports submittedDate as a search filter. lastUpdatedDate
    # is a sort key, not an independent date-range search field.
    return f'({categories}) AND ({terms}) AND submittedDate:[{lo} TO {hi}]'

def parse_feed(blob):
    if b'<!DOCTYPE' in blob.upper() or b'<!ENTITY' in blob.upper():raise ValueError('Unexpected XML entities')
    feed=ET.fromstring(blob)
    rows=[]
    clean=lambda e,k:' '.join(''.join(e.find(k).itertext()).split()) if e.find(k) is not None else ''
    for e in feed.findall(ATOM+'entry'):
        raw=clean(e,ATOM+'id')
        if '/abs/' not in raw:raise ValueError('arXiv returned an error entry: '+clean(e,ATOM+'title'))
        versioned=raw.split('/abs/',1)[1];paper_id=versioned.rsplit('v',1)[0] if versioned.rsplit('v',1)[-1].isdigit() else versioned
        abstract=clean(e,ATOM+'summary')
        if not abstract:raise ValueError('Missing original abstract: '+versioned)
        rows.append({'paper_id':paper_id,'versioned_id':versioned,'url':'https://arxiv.org/abs/'+versioned,
          'title':clean(e,ATOM+'title'),'authors':[clean(a,ATOM+'name') for a in e.findall(ATOM+'author')],
          'published':clean(e,ATOM+'published'),'updated':clean(e,ATOM+'updated'),
          'abstract':abstract,'abstract_sha256':hashlib.sha256(abstract.encode()).hexdigest(),
          'categories':[c.get('term') for c in e.findall(ATOM+'category')],
          'doi':clean(e,ARXIV+'doi'),'journal_ref':clean(e,ARXIV+'journal_ref'),
          'acquisition_status':'primary_abstract_acquired','model_review_status':'not_read'})
    return rows,int(feed.findtext(OPEN+'totalResults',default=str(len(rows))))

def acquire(params,path):
    url='https://export.arxiv.org/api/query?'+urllib.parse.urlencode(params)
    if path.exists():blob=path.read_bytes()
    else:
        error=None
        for attempt in range(3):
            try:
                request=urllib.request.Request(url,headers={'User-Agent':'CCN-Insight-Research/1.0 (public scholarly metadata)'})
                with urllib.request.urlopen(request,timeout=35) as response:blob=response.read(8*1024*1024+1)
                if len(blob)>8*1024*1024:raise ValueError('Response too large')
                parse_feed(blob);path.write_bytes(blob);break
            except Exception as exc:
                error=exc
                if attempt==2:raise
                print(json.dumps({'retry':attempt+1,'error':str(exc)[:200]}),flush=True);time.sleep(4*(attempt+1))
        else:raise error
        time.sleep(3.1)
    rows,total=parse_feed(blob)
    feed=ET.fromstring(blob)
    return rows,{'request_url':url,'response_file':path.name,'response_sha256':hashlib.sha256(blob).hexdigest(),'returned':len(rows),'reported_total':total,'returned_query_title':feed.findtext(ATOM+'title','')}

def collect(args):
    end=dt.date.fromisoformat(args.end);start=end-dt.timedelta(days=args.days-1)
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    search=query(start.isoformat(),end.isoformat())
    if (out/'receipt.json').exists():
        prior=json.loads((out/'receipt.json').read_text(encoding='utf-8'))
        if prior.get('query')!=search:raise ValueError('Use a new output directory when the query window changes; cached pages belong to the recorded query.')
    receipt={'schema':'ccn.abstract-acquisition.v1','source':'arXiv official API','source_is_live':True,
      'started_at':dt.datetime.now(dt.timezone.utc).isoformat(),'window_start':start.isoformat(),
      'window_end':end.isoformat(),'query':search,'pages':[],'errors':[],'classic_seed_ids':CLASSICS,
      'complete_for_arxiv_query':False,'complete_for_all_registered_sources':False,
      'reading_boundary':'Original abstracts acquired; no model reading or full-text review implied.'}
    entries={};offset=0;total=None
    try:
        while total is None or offset<total:
            if args.max_items and offset>=args.max_items:break
            limit=min(args.page_size,args.max_items-offset) if args.max_items else args.page_size
            params={'search_query':search,'start':offset,'max_results':limit,'sortBy':'lastUpdatedDate','sortOrder':'descending'}
            rows,page=acquire(params,out/f'recent-{offset:06d}.xml');receipt['pages'].append(page);total=page['reported_total']
            for row in rows:
                row['selection_cohort']='recent';row['original_query_offset']=offset;entries[row['paper_id']]=row
            print(json.dumps({'recent_fetched':offset+len(rows),'reported_total':total,'unique':len(entries)}),flush=True)
            if not rows:break
            offset+=len(rows)
        receipt['complete_for_arxiv_query']=total is not None and offset==total and len(entries)==total and len({p['reported_total'] for p in receipt['pages']})==1
        receipt['pagination_boundary']='Completeness is for this exact returned API query, not all compression literature or all newly revised older papers.'
        echoes=[p.get('returned_query_title','') for p in receipt['pages']]
        receipt['revision_window_verified']=all('lastUpdatedDate' in title for title in echoes)
        if not receipt['revision_window_verified']:receipt['date_filter_warning']='The API response query echo does not retain lastUpdatedDate; recent-submission retrieval is observed, but revision-only coverage is not established.'
        rows,page=acquire({'id_list':','.join(CLASSICS),'max_results':len(CLASSICS)},out/'classics.xml');receipt['pages'].append(page)
        if {r['paper_id'] for r in rows}!=set(CLASSICS):raise ValueError('Classic seed response is incomplete or contains unexpected identities')
        for row in rows:
            if row['paper_id'] in entries:entries[row['paper_id']]['also_classic_seed']=True
            else:row['selection_cohort']='classic_seed';entries[row['paper_id']]=row
    except Exception as exc:
        receipt['errors'].append({'offset':offset,'error':str(exc)[:500]});print(json.dumps(receipt['errors'][-1]),flush=True)
    finally:
        receipt.update({'completed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'unique_abstracts':len(entries),
          'recent_reported_total':total,'recent_rows_fetched':offset,'model_read':0,'full_text_read':0})
        (out/'abstracts.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in entries.values()),encoding='utf-8')
        (out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:receipt[k] for k in ['unique_abstracts','recent_reported_total','complete_for_arxiv_query','errors']}),flush=True)
    return 1 if receipt['errors'] else 0

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--end',required=True);p.add_argument('--days',type=int,default=90)
    p.add_argument('--out',required=True);p.add_argument('--page-size',type=int,default=200);p.add_argument('--max-items',type=int,default=0)
    a=p.parse_args()
    if not 1<=a.page_size<=200 or not 1<=a.days<=366:raise SystemExit('Invalid bounded query window or page size')
    raise SystemExit(collect(a))
