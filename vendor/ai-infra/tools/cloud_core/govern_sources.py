"""Prepare version-fenced source classifications and identifier issues."""
import argparse
import json
import re
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from build_migration import BATCH_ID,stable

ROOT=Path(__file__).parent
PAPER_HOSTS={'openreview.net','aclanthology.org','openaccess.thecvf.com','proceedings.mlr.press','papers.nips.cc','papers.neurips.cc','dl.acm.org','ieeexplore.ieee.org'}


def operations():
    updates=[];issues=[]
    for file in sorted((ROOT/'staging-v1').glob('cloud_core_sources-*.json')):
        for row in json.loads(file.read_text(encoding='utf-8')):
            url=urlsplit(row['canonical_url']);changes={}
            if row['provider'] in PAPER_HOSTS:
                changes['source_kind']='paper'
            if url.hostname in {'arxiv.org','www.arxiv.org','export.arxiv.org'} and re.match(r'^/(abs|pdf|html)/',url.path):
                identifier=re.sub(r'^/(abs|pdf|html)/','',url.path).removesuffix('.pdf')
                match=re.fullmatch(r'(\d{2})(\d{2})\.(\d{4,5})(v[1-9]\d*)?',identifier)
                legacy=re.fullmatch(r'[a-z-]+(?:\.[A-Z]{2})?/\d{7}(?:v[1-9]\d*)?',identifier)
                valid=bool(legacy) or bool(match and 1<=int(match.group(2))<=12 and len(match.group(3))==(5 if int(match.group(1))>=15 else 4))
                if not valid:
                    changes.update(source_kind='paper',verification_status='invalid_identifier',update_policy='manual_identifier_review_before_refresh')
                    issue=dict(issue_id=stable('issue-url',row['source_id']),business_id='cloud-core',batch_id=BATCH_ID,subject_id=row['source_id'],issue_type='invalid_arxiv_identifier',status='needs_review',description='原始链接中的 arXiv 编号格式不符合官方编号规则；保留原链接及出处，不自动猜测替代地址。')
                    issues.append({'op':'insert','operation_id':str(uuid.uuid5(uuid.NAMESPACE_URL,BATCH_ID+':govern-issue:'+issue['issue_id'])),'key':issue['issue_id'],'row':issue})
            if changes:
                updates.append({'op':'update','operation_id':str(uuid.uuid5(uuid.NAMESPACE_URL,BATCH_ID+':govern:'+row['source_id'])),'key':row['source_id'],'expected_row_version':1,'set':changes})
    return updates,issues


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--index',type=int);parser.add_argument('--count',action='store_true');args=parser.parse_args()
    updates,issues=operations();all_ops=[('cloud_core_sources',x) for x in updates]+[('cloud_core_import_issues',x) for x in issues]
    count=(len(all_ops)+799)//800
    if args.count:
        print(json.dumps({'batches':count,'source_updates':len(updates),'invalid_identifiers':len(issues)}))
    else:
        selected=all_ops[args.index*800:(args.index+1)*800];tables={}
        for table,op in selected:tables.setdefault(table,[]).append(op)
        payload={'topic_id':'main','transaction_id':str(uuid.uuid5(uuid.NAMESPACE_URL,BATCH_ID+':govern-batch:'+str(args.index))), 'idempotency_key':BATCH_ID+':govern-batch:'+str(args.index),'actor':{'person_id':'4aa9bd9b-d186-4313-b72b-d46b964d3224'},'message':'fix: govern source types and invalid arXiv identifiers','tables':[{'path':'data/tables/'+t,'operations':ops} for t,ops in tables.items()]}
        print(json.dumps(payload,ensure_ascii=True))
