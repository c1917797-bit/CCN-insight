# -*- coding: utf-8 -*-
"""Route actually read research by calendar month; never infer relevance by title.

Routing produces review candidates, not automatic publication or recommendation.
New revisions retain their original publication date and long-term topic link.
"""
from __future__ import annotations
import argparse,collections,csv,datetime as dt,json
from pathlib import Path

LABELS={'topic':'长期专题候选','monthly_new':'本月新论文候选','monthly_revision':'本月重要修订候选','watch':'邻接技术观察','uncertain':'待核验','unread':'尚未研读','excluded':'不纳入','outside_month':'不属于所选月份','historical_version':'需读取当月版本'}

def month_bounds(month):
    start=dt.date.fromisoformat(month+'-01')
    end=dt.date(start.year+1,1,1) if start.month==12 else dt.date(start.year,start.month+1,1)
    return start,end

def placement(paper,month,as_of):
    start,end=month_bounds(month);today=dt.date.fromisoformat(as_of[:10])
    published=dt.date.fromisoformat(paper['published'][:10]);updated=dt.date.fromisoformat(paper['updated'][:10])
    review=paper.get('review')
    result={'month':month,'basis':'calendar_month','first_publication':str(published),'version_updated':str(updated),'route':'unread','event_kind':'none','topic_eligible':False}
    if not review:return result
    if review['relevance'] in ['out_of_scope','uncertain']:
        result['route']='excluded' if review['relevance']=='out_of_scope' else 'uncertain';return result
    if published>today or published>=end:
        result['route']='outside_month';return result
    if updated>today or updated>=end:
        # A November revision must not supply evidence for an October snapshot.
        result['route']='historical_version';return result
    # Time determines destination only after model semantic review.
    result['topic_eligible']=published<start
    if start<=published<end:result.update(route='monthly_new',event_kind='first_submission')
    elif start<=updated<end:result.update(route='monthly_revision',event_kind='version_revision')
    else:result.update(route='topic',event_kind='historical_primary')
    # An adjacent execution/training mechanism is not automatically a root technique.
    if review['relevance']=='adjacent':result.update(suggested_time_route=result['route'],route='watch')
    return result

def route_index(index,month,as_of):
    return [{**p,'placement':placement(p,month,as_of)} for p in index]

def export(index,out,month,as_of):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    result=route_index(index,month,as_of)
    routing_rows=[{k:p[k] for k in ['paper_id','versioned_id','title','url','placement']} for p in result]
    (out/'reading-placements.json').write_text(json.dumps(routing_rows,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    with (out/'按自然月分流.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['论文编号','标题','首次公开','版本更新','研读后归属','事件类型','同时可吸收长期专题','根技术','理由与边界','来源'])
        for p in result:
            r=p.get('review') or {};a=p['placement']
            writer.writerow([p['paper_id'],p['title'],a['first_publication'],a['version_updated'],LABELS[a['route']],a['event_kind'],a['topic_eligible'],','.join(r.get('routes',[])),r.get('value_zh') or r.get('exclusion_reason_zh',''),p['url']])
    counts=collections.Counter(p['placement']['route'] for p in result)
    receipt={'month':month,'as_of':as_of,'policy':'calendar_month','stage':'semantic_review_then_calendar_routing_candidates','counts':dict(counts),'adoption_is_separate':True}
    (out/'routing-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False));return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--index',required=True);p.add_argument('--month',required=True);p.add_argument('--as-of',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();export(json.loads(Path(a.index).read_text(encoding='utf-8')),a.out,a.month,a.as_of)
