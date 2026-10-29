"""Import individually abstract-reviewed public papers into the single maintained source.

Inputs are review decisions, not a keyword classifier. The acquisition remains an
auditable saved query of a source already present in the source-family registry.
"""
from pathlib import Path
import argparse,hashlib,json,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT,DATA,rows,clear_cache

TOPICS={t+'-'+m for t in ['parameters','activations','kv_cache'] for m in ['precision','selection','distillation','factorization']}|{'activations-merging','kv_cache-kv_eviction','kv_cache-sharing','kv_cache-compact_architecture'}
STATUSES={'classified','related_unmapped','pending','excluded'}
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def jsonl(path):return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def write_table(name,key,values,description,integer_fields=()):
    folder=DATA/'tables'/name;folder.mkdir(exist_ok=True)
    fields=sorted(set().union(*(r.keys() for r in values)))
    assert all(set(r)==set(fields) for r in values),'Inconsistent row fields'
    definition={'schema':'mcpgit.table.v2','description':description,'key_field':key,'fields':{f:{'projection':'default','required':True,'role':'key' if f==key else 'value','source':None,'type':'integer' if f in integer_fields else 'text' if f in ['basis_zh','uncertainties_zh','query','topic_ids_json','source_family_ids_json'] else 'string'} for f in fields},'required_fields':fields,'indexes':[{'field':f,'name':'idx_'+f} for f in ['business_id','topic_id','period_id','snapshot_id'] if f in fields]}
    (folder/'definition.json').write_bytes((json.dumps(definition,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    (folder/'rows.jsonl').write_bytes(''.join(json.dumps({'deleted':False,'key':r[key],'row':r,'row_version':1,'text_match':None},ensure_ascii=False,separators=(',',':'))+'\n' for r in sorted(values,key=lambda r:r[key])).encode('utf-8'))
    path=DATA/'manifest.json';manifest=json.loads(path.read_text(encoding='utf-8'))
    entry={'name':name,'path':'data/tables/'+name,'revision':'local-abstract-corpus-20261029','source_row_count':len(values),'exported_rows':len(values),'filters':[{'field':'business_id','op':'eq','value':'cloud-core'},{'field':'topic_id','op':'eq','value':'cloud_core'}],'rows_file':f'data/compression/tables/{name}/rows.jsonl','import_sha256':digest(folder/'rows.jsonl'),'key_field':key,'provenance_kind':'local_registered_source_abstract_review'}
    manifest['tables']=[x for x in manifest['tables'] if x['name']!=name]+[entry]
    path.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--decisions',type=Path,required=True);parser.add_argument('--acquisition',type=Path,required=True);args=parser.parse_args()
    receipt_path=args.acquisition/'original-records/arxiv/receipt.json';receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
    abstract_path=args.acquisition/'original-records/arxiv/abstracts.jsonl';abstracts={r['paper_id']:r for r in jsonl(abstract_path)}
    period='2026-10';cutoff='2026-10-29';snapshot_id='corpus-2026-10-arxiv-20261029-abstract-v1'
    source_family='source-family-arxiv';family=next(r for r in rows('ic_source_families') if r['family_id']==source_family)
    assert family['ui_group']=='academic' and family['business_id']=='cloud-core'
    candidates={id:r for id,r in abstracts.items() if r['published'].startswith(period) and r['published'][:10]<=cutoff}
    assert len(candidates)==1728,'Unexpected acquisition; review a new snapshot explicitly'
    decisions=[]
    for path in sorted(args.decisions.glob('output-[0-9].jsonl')):decisions.extend(jsonl(path))
    assert len({r['paper_id'] for r in decisions})==len(decisions),'Duplicate review decisions'
    assert {r['paper_id'] for r in decisions}==set(candidates),'Every monthly query hit needs an explicit abstract decision'
    output=[]
    for d in sorted(decisions,key=lambda r:r['paper_id']):
        a=candidates[d['paper_id']];topics=d['topics'];status=d['status']
        assert re.fullmatch(r'\d{4}\.\d{4,5}',a['paper_id']) and re.fullmatch(re.escape(a['paper_id'])+r'v[1-9]\d*',a['versioned_id'])
        assert d['abstract_sha256']==a['abstract_sha256']==hashlib.sha256(a['abstract'].encode()).hexdigest(),'Abstract hash mismatch'
        assert status in STATUSES and isinstance(topics,list) and len(set(topics))==len(topics) and set(topics)<=TOPICS
        assert (status=='classified')==bool(topics),'Only confirmed abstract assignments enter the matrix'
        assert d['basis_zh'].strip() and isinstance(d.get('uncertainties_zh',''),str)
        reason=d.get('reason_code','')
        assert reason!='diffusion_out_of_scope' or (status=='excluded' and not topics)
        row={'corpus_id':snapshot_id+'__'+a['paper_id'],'snapshot_id':snapshot_id,'business_id':'cloud-core','topic_id':'cloud_core','period_id':period,'paper_id':a['paper_id'],'title':a['title'],'canonical_url':'https://arxiv.org/abs/'+a['paper_id'],'versioned_id':a['versioned_id'],'first_published':a['published'],'last_updated':a['updated'],'source_family_id':source_family,'abstract_sha256':a['abstract_sha256'],'review_basis':'original_abstract','reviewed_at':cutoff,'classification_status':status,'topic_ids_json':json.dumps(sorted(topics),ensure_ascii=False,separators=(',',':')),'basis_zh':d['basis_zh'],'uncertainties_zh':d.get('uncertainties_zh',''),'reason_code':reason}
        output.append(row)
    decision_fields=['paper_id','abstract_sha256','classification_status','topic_ids_json','basis_zh','uncertainties_zh','reason_code']
    decision_payload=[{k:r[k] for k in decision_fields} for r in sorted(output,key=lambda r:r['paper_id'])]
    decisions_hash=hashlib.sha256(json.dumps(decision_payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    snapshot={'snapshot_id':snapshot_id,'business_id':'cloud-core','topic_id':'cloud_core','period_id':period,'window_start':period+'-01','cutoff':cutoff,'month_basis':'first_publication','diffusion_policy':'excluded','source_family_ids_json':json.dumps([source_family]),'candidate_count':len(output),'acquired_at':receipt['completed_at'],'reviewed_at':cutoff,'query':receipt['query'],'abstract_snapshot_sha256':digest(abstract_path),'acquisition_receipt_sha256':digest(receipt_path),'decisions_sha256':decisions_hash,'coverage_status':'registered_arxiv_query_only','revision_coverage':'not_established','review_depth':'abstract_only'}
    # Keep previous months in the same canonical tables when a later snapshot is added.
    for name,key,new,description,ints in [('ic_monthly_paper_corpus','corpus_id',output,'Monthly first-publication candidates and individual original-abstract classification decisions; not a full-field census.',()),('ic_monthly_corpus_snapshots','snapshot_id',[snapshot],'Acquisition, date, source-registry and review boundaries of a monthly paper corpus.',('candidate_count',))]:
        try:prior=rows(name)
        except FileNotFoundError:prior=[]
        write_table(name,key,[r for r in prior if r['snapshot_id']!=snapshot_id]+new,description,ints)
    clear_cache()
    from collections import Counter
    print(json.dumps({'snapshot_id':snapshot_id,'total_candidates':len(output),'statuses':Counter(r['classification_status'] for r in output),'diffusion_excluded':sum(r['reason_code']=='diffusion_out_of_scope' for r in output)},ensure_ascii=False))
if __name__=='__main__':main()
