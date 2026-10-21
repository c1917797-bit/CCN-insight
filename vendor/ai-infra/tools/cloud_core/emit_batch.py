"""Stream audited transport batches to the host; never an authority JSON store."""
import argparse
import collections
import hashlib
import json
import sys
import uuid
from pathlib import Path
from model import SPECS, seeds
from build_migration import BATCH_ID, NOW
from prepare_sources import reasons

ROOT=Path(__file__).parent
STAGING=ROOT/'staging-v1'
PERSON='4aa9bd9b-d186-4313-b72b-d46b964d3224'


def plan():
    manifest=json.loads((STAGING/'manifest.json').read_text(encoding='utf-8'))
    groups=[]
    for name in ['cloud_core_folders','cloud_core_documents','cloud_core_sources','cloud_core_source_refs','cloud_core_links','cloud_core_import_issues']:
        chunks=[x for x in manifest['chunks'] if x['table']==name]
        step=1 if name == 'cloud_core_documents' else 5
        for start in range(0,len(chunks),step):
            groups.append(chunks[start:start+step])
    return manifest,groups


def payload(index):
    manifest,groups=plan()
    tables=collections.defaultdict(list)
    if index == -1:
        tables.update(seeds())
        tables['topic_workbench_profiles']=[{'topic_id':'cloud_core','schema_id':'lri.cloud-core-workbench/v1',
            'status':'governed_import_unverified','last_verified':'','updated_at':NOW,
            'source_boundary':'Obsidian-derived internal plans and URL-only public sources; not independently verified; Cloud Core flywheel and experiment rows are proposed designs.',
            'source_revision':'sha256:'+hashlib.sha256((STAGING/'manifest.json').read_bytes()).hexdigest(),
            'payload_zh':{'title':'云核业务洞察','summary':'以业务约束连接一手信源、洞察决策和联调验证。导入内容待核验，飞轮与实验为设计方案。'},
            'payload_en':{'title':'Cloud Core Business Insights','summary':'Connect business constraints, primary sources, decisions and integration tests. Imported claims remain unverified; the flywheel and experiments are proposed designs.'}}]
        a=manifest['audit'];c=manifest['table_counts']
        tables['cloud_core_import_runs']=[dict(batch_id=BATCH_ID,business_id='cloud-core',status='importing',source_policy='Public papers/news: URL only. Internal plans: reviewed text. Config, code, chat logs, assets and generated data remain local.',started_at=NOW,completed_at='',scanned_notes=a['markdown_seen'],document_count=c['cloud_core_documents'],source_count=c['cloud_core_sources'],reference_count=c['cloud_core_source_refs'],excluded_name_count=a['quarantined_name'],excluded_content_count=a['quarantined_content'],retained_local_count=a['excluded_config_tools_or_chat']+a['no_public_url_retained_locally']+a['excluded_root_nonbusiness'],payload_audit='pass_conservative_rules; quarantine indicators are not proof of actual credentials')]
    else:
        for item in groups[index]:
            tables[item['table']].extend(json.loads((STAGING/item['file']).read_text(encoding='utf-8')))
    transaction_id=str(uuid.uuid5(uuid.NAMESPACE_URL,BATCH_ID+':batch:'+str(index)))
    result=[]
    for table,rows in tables.items():
        key_field='topic_id' if table == 'topic_workbench_profiles' else SPECS[table.removeprefix('cloud_core_')][0]
        operations=[]
        for row in rows:
            # Controlled design/audit prose mentions governance terminology, not source secrets.
            if index != -1 and reasons(json.dumps(row,ensure_ascii=False)):
                raise ValueError('Sensitive payload blocked before transport')
            key=row[key_field]
            operations.append({'op':'insert','operation_id':str(uuid.uuid5(uuid.NAMESPACE_URL,transaction_id+':'+table+':'+key)), 'key':key,'row':row})
        result.append({'path':'data/tables/'+table,'operations':operations})
    return {'transaction_id':transaction_id,'idempotency_key':BATCH_ID+':batch:'+str(index),'actor':{'person_id':PERSON,'showname':'yinxiaoshuai'},'topic_id':'main','tables':result,'message':'feat: migrate governed Cloud Core batch '+str(index)}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--index',type=int)
    parser.add_argument('--count',action='store_true')
    args=parser.parse_args()
    if args.count:
        manifest,groups=plan()
        print(json.dumps({'batches':len(groups),'audit':manifest['audit'],'table_counts':manifest['table_counts']}))
    else:
        sys.stdout.reconfigure(encoding='utf-8')
        print(json.dumps(payload(args.index),ensure_ascii=False))
