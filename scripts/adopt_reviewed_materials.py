# -*- coding: utf-8 -*-
"""Apply explicit editorial decisions to the existing canonical compression tables.

Default is a local patch preview. --apply writes backed-up tables, validates joins,
and rolls back this operation if validation fails. Never publishes or pushes.
"""
from __future__ import annotations
import argparse,copy,datetime as dt,hashlib,json,re,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
BASE={'business_id':'cloud-core','topic_id':'cloud_core'}

def validate_selected_inputs(acquired,reviewed,decisions,today):
    """Bind every selected claim to its reviewed source before staging any rows.

    These checks also protect direct CLI callers that have not run the builder.
    Explicit errors remain active under python -O.
    """
    def require(condition,message,pid=''):
        if not condition:raise ValueError(message+(': '+pid if pid else ''))
    def text(row,field):
        return isinstance(row.get(field),str) and bool(row[field].strip())
    def bound_arxiv_url(url,path):
        parsed=urlsplit(url)
        return url==url.strip() and parsed.scheme=='https' and parsed.netloc=='arxiv.org' and not parsed.query and parsed.path in {path,path+'/'}
    choices=json.loads(Path(decisions).read_text(encoding='utf-8'))
    require(isinstance(choices,list) and bool(choices),'Expected a nonempty decisions list')
    selected=set()
    for decision in choices:
        require(isinstance(decision,dict) and text(decision,'paper_id'),'Decision needs a paper_id')
        pid=decision['paper_id']
        require(re.fullmatch(r'(?:\d{2}(?:0[1-9]|1[0-2])\.\d{4,5}|[A-Za-z][A-Za-z.-]*/\d{2}(?:0[1-9]|1[0-2])\d{3})',pid) is not None,'Invalid arXiv paper_id',pid)
        require(pid not in selected,'Duplicate selected paper',pid);selected.add(pid)
        require(decision.get('destination') in {'topic','topic_and_monthly_revision','monthly'},'Unknown destination',pid)
        if 'selection_tier' in decision:
            require(decision['selection_tier'] in {'key_progress','technical_watch','boundary_case'},'Unknown editorial tier',pid)
            for language in ['zh','en']:
                require(text(decision,'selection_reason_'+language),'Missing selection reason',pid)
        for lang in ['zh','en']:
            for field in ['title','background','mechanism','results','boundary','next']:
                require(text(decision,field+'_'+lang),'Missing decision text '+field+'_'+lang,pid)
        for field in ['topics','cells','keywords']:
            values=decision.get(field)
            require(isinstance(values,list) and bool(values) and all(isinstance(v,str) and v.strip() for v in values),'Invalid decision list '+field,pid)
            require(len(values)==len(set(values)),'Duplicate decision list item '+field,pid)
    papers={}
    for line in (Path(acquired)/'abstracts.jsonl').read_text(encoding='utf-8').splitlines():
        if not line.strip():continue
        paper=json.loads(line);pid=paper['paper_id']
        if pid not in selected:continue
        require(pid not in papers,'Duplicate acquired paper',pid)
        require(all(text(paper,k) for k in ['title','url','published','updated']),'Incomplete acquired source identity',pid)
        require(isinstance(paper.get('versioned_id'),str) and re.fullmatch(re.escape(pid)+r'v[1-9]\d*',paper['versioned_id']) is not None,'Invalid source version identity',pid)
        require(bound_arxiv_url(paper['url'],'/abs/'+paper['versioned_id']),'Acquired abstract version URL mismatch',pid)
        require(text(paper,'abstract'),'Missing original abstract',pid)
        require(hashlib.sha256(paper['abstract'].encode('utf-8')).hexdigest()==paper.get('abstract_sha256'),'Original abstract SHA256 mismatch',pid)
        papers[pid]=paper
    require(selected==set(papers),'Selected paper missing from acquired abstracts')
    notes={}
    for path in sorted(Path(reviewed).glob('*-reviews.jsonl')):
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip():continue
            note=json.loads(line);pid=note['paper_id']
            if pid not in selected:continue
            require(pid not in notes,'Duplicate model review',pid)
            require(note.get('review_status')=='model_abstract_reviewed','Model abstract review not completed',pid)
            require(note.get('relevance')=='direct','Selected paper is not directly relevant',pid)
            require(note.get('abstract_sha256')==papers[pid]['abstract_sha256'],'Model review abstract SHA256 mismatch',pid)
            for field in ['title','url','versioned_id']:
                require(field not in note or note[field]==papers[pid].get(field),'Model review source identity changed ('+field+')',pid)
            require(all(text(note,k) for k in ['problem_zh','mechanism_zh','reported_results_zh','limitations_zh','value_zh','next_read_zh']),'Incomplete model annotation',pid)
            routes=note.get('routes')
            require(isinstance(routes,list) and all(isinstance(v,str) and v in {'quantization','pruning','distillation','low_rank'} for v in routes),'Invalid model review routes',pid)
            notes[pid]=note
    require(selected==set(notes),'Selected paper missing a model abstract review')
    sections={};section_path=Path(reviewed)/'section-reviews.json'
    section_rows=json.loads(section_path.read_text(encoding='utf-8')) if section_path.exists() else []
    require(isinstance(section_rows,list),'Expected a section reviews list')
    for section in section_rows:
        pid=section['paper_id']
        if pid not in selected:continue
        require(pid not in sections,'Duplicate section review',pid)
        require(section.get('review_level')=='section_reviewed','Section review not completed',pid)
        require(all(text(section,k) for k in ['url','locations','finding_zh','conditions_zh','results_zh','judgment_zh']),'Incomplete section annotation',pid)
        require(bound_arxiv_url(section['url'],'/html/'+papers[pid]['versioned_id']),'Section review version URL mismatch',pid)
        for field in ['title','versioned_id','abstract_sha256']:
            require(field not in section or section[field]==papers[pid].get(field),'Section review source identity changed ('+field+')',pid)
        sections[pid]=section
    snapshot=dt.date.fromisoformat(today);start=snapshot.replace(day=1)
    for decision in choices:
        pid=decision['paper_id'];paper=papers[pid]
        first=dt.date.fromisoformat(paper['published'][:10]);updated=dt.date.fromisoformat(paper['updated'][:10])
        require(first<=updated<=snapshot,'Source dates unavailable at snapshot',pid)
        destination=decision['destination']
        valid=first<start if destination=='topic' else first<start<=updated if destination=='topic_and_monthly_revision' else start<=first
        require(valid,'Decision does not match calendar-month dates',pid)
    return papers,notes,sections,choices

def adopt(acquired,reviewed,decisions,out,apply=False):
    acquired,reviewed,out=map(Path,[acquired,reviewed,out])
    receipt=json.loads((acquired/'receipt.json').read_text(encoding='utf-8'))
    today=receipt['window_end']
    papers,notes,sections,choices=validate_selected_inputs(acquired,reviewed,decisions,today)
    out.mkdir(parents=True,exist_ok=True)
    month=today[:7];batch=today.replace('-','')
    scope='ic-'+month+'-model-reviewed-'+batch+'-v1'
    tables={};before={};changes=[];cell_papers={}
    def table(name):
        if name not in tables:
            path=ROOT/'data/compression/tables'/name/'rows.jsonl';before[name]=path.read_bytes()
            tables[name]={r['key']:r for r in map(json.loads,path.read_text(encoding='utf-8').splitlines())}
        return tables[name]
    def put(name,row):
        definition=json.loads((ROOT/'data/compression/tables'/name/'definition.json').read_text(encoding='utf-8'))
        assert all(k in row for k in definition['required_fields']),(name,'missing',set(definition['required_fields'])-set(row))
        key=row[definition['key_field']];old=table(name).get(key)
        if old and old['row']==row:return
        table(name)[key]={'key':key,'row':row,'row_version':old['row_version']+1 if old else 1,'deleted':False,'text_match':None}
        changes.append({'table':name,'key':key,'action':'update' if old else 'add'})
    def retire(name,key):
        old=table(name)[key]
        if old.get('deleted'):return
        table(name)[key]={**old,'deleted':True,'row_version':old['row_version']+1}
        changes.append({'table':name,'key':key,'action':'retire_duplicate_created_by_this_pipeline'})
    def event_identity(sid,version,kind,date,pid):
        matches=[r for r in table('ic_evidence_items').values() if not r.get('deleted') and all(r['row'].get(k)==v for k,v in [('source_id',sid),('observed_version',version),('date_kind',kind),('event_date',date)])]
        matches.sort(key=lambda r:(r['key'].startswith('ic-live-'),r['key']))
        eid=matches[0]['key'] if matches else 'ic-evidence-arxiv-'+pid+'-'+version+'-'+kind+'-'+date
        for duplicate in matches[1:]:
            old_id=duplicate['key']
            # Preserve historical catalog records. Only retire duplicates created
            # by this pipeline and redirect their dependent relations.
            if not old_id.startswith('ic-live-'):continue
            for name in ['ic_paper_summary_events','ic_compression_topic_events','ic_finding_scopes','ic_monthly_evidence_cells','ic_monthly_route_evidence']:
                definition=json.loads((ROOT/'data/compression/tables'/name/'definition.json').read_text(encoding='utf-8'));key_field=definition['key_field']
                for record in list(table(name).values()):
                    if record.get('deleted') or record['row'].get('evidence_id')!=old_id:continue
                    row=copy.deepcopy(record['row']);row['evidence_id']=eid;row[key_field]=row[key_field].replace(old_id,eid)
                    put(name,row)
                    if row[key_field]!=record['key']:retire(name,record['key'])
            retire('ic_evidence_items',old_id)
        return eid
    def source(p):
        found=[r['row'] for r in table('cloud_core_sources').values() if not r.get('deleted') and (r['row'].get('external_id')==p['paper_id'] or re.search(r'/(?:abs|html)/'+re.escape(p['paper_id'])+r'(?:v\d+)?(?:$|[?#])',r['row'].get('canonical_url','')))]
        assert len(found)<=1,('duplicate source identity',p['paper_id'])
        row=copy.deepcopy(found[0]) if found else {**BASE,'source_id':'source-live-arxiv-'+p['paper_id'].replace('.','-'),'canonical_url':'https://arxiv.org/abs/'+p['paper_id'],'external_id':p['paper_id'],'provider':'arxiv.org','source_kind':'paper','batch_id':'live-reading-'+batch,'title':p['title'],'update_policy':'follow_original_url_then_review_version; preserve_first_publication'}
        row['last_checked_at']=today
        if row.get('verification_status')!='primary_full_text_reviewed':row['verification_status']='primary_sections_reviewed' if p['paper_id'] in sections else 'primary_abstract_checked'
        put('cloud_core_sources',row);return row['source_id']
    monthly=[d for d in choices if 'monthly' in d['destination']]
    put('ic_monthly_scopes',{**BASE,'scope_id':scope,'period_id':month,'window_start':month+'-01','window_end':today,'collected_at':today,'position':-10,'title_zh':month+' 模型研读与重点核验精选','title_en':month+' selected model-reviewed and section-checked evidence','status':'reviewed_sample','month_basis':'primary_event_date','source_pool':'live_arxiv_model_abstract_reading','source_revision':'live-arxiv-'+batch+'; calendar-month-routing','selection_rule':'先读完整原始摘要，再由编辑逐项选择。首发与重要修订分别记录；长期专题吸收机制，月度动态记录新变化。','dedup_rule':'原始论文ID＋观察版本＋事件类别去重；一个成果关联多个方向但只形成一个月度事件。','coverage_note':f'本轮精选{len(monthly)}项论文事件；部分已核对指定章节，部分只读摘要并明确标注。未读、无关及证据矛盾项不自动采纳；这不是完整领域普查或本地实测。'})
    for decision_position,d in enumerate(choices):
        p=papers[d['paper_id']]
        first=p['published'][:10];updated=p['updated'][:10];version='v'+p['versioned_id'].rsplit('v',1)[1]
        sid=source(p);summary_id=sid+'__'+version;section=sections.get(p['paper_id']);locator=section['locations'] if section else 'Abstract; full methods and experiments not yet reviewed'
        evidence_url=section['url'] if section else p['url']
        put('ic_paper_summaries',{**BASE,'summary_id':summary_id,'source_id':sid,'observed_version':version,'background_zh':d['background_zh'],'innovation_zh':d['mechanism_zh'],'one_sentence_zh':d['title_zh'],'results_zh':d['results_zh']+' '+d['boundary_zh'],'review_status':'method_results_checked' if section else 'primary_abstract_checked','reviewed_at':today,'evidence_locator':locator,'evidence_url':evidence_url,'keyword_count':len(d['keywords'])})
        for i,word in enumerate(d['keywords']):put('ic_paper_summary_keywords',{**BASE,'keyword_id':summary_id+'__'+str(i),'summary_id':summary_id,'keyword_zh':word,'position':i})
        if d['destination'] in ['topic','topic_and_monthly_revision']:
            topic=d['topics'][0];card_id=topic+'__live_'+p['paper_id'].replace('.','_')
            # The lasting lesson is retained in the topic; October's version-specific
            # observations remain in its event, rather than duplicating that event.
            if d['destination']=='topic_and_monthly_revision':
                body='技术问题：量化文件可精确重建，是否就表示模型可用？\n机制与启示：文件一致性检查验证产物是否按同一配方生成；功能测试验证模型是否仍能完成任务。两者互不替代。对量化交付先做少量有代表性的功能筛查，再进入完整业务质量与服务性能测试。\n证据边界：此方法来自代码模型产物审计，筛查任务和阈值需要按翻译、降噪等实际任务重新设计。不能把文件哈希一致写成业务质量已达标。\n版本关联：原论文首次公开于2026-09，10月v2的重要结论修订单独列入本月动态。'
                body_en='File reproducibility and task functionality are separate checks. Screen representative functions before full quality and serving evaluation. The cited audit concerns coding artifacts; other tasks require their own tests and thresholds. The paper first appeared in September; its October v2 revision is recorded as a monthly revision event.'
            else:body='机制：'+d['mechanism_zh']+'\n作者结果：'+d['results_zh']+'\n适用边界：'+d['boundary_zh']+'\n研究判断：'+d['next_zh'];body_en=d['mechanism_en']+' '+d['results_en']+' '+d['boundary_en']
            put('ic_compression_topic_cards',{**BASE,'card_id':card_id,'compression_topic_id':topic,'title_zh':d['title_zh'],'title_en':d['title_en'],'body_zh':body,'body_en':body_en,'position':78,'section_kind':'papers','card_kind':'case','claim_kind':'research_analysis' if section else 'author_result','reviewed_at':today})
            ref=card_id+'__primary';put('ic_compression_topic_card_refs',{**BASE,'reference_id':ref,'card_id':card_id,'compression_topic_id':topic,'source_id':sid,'locator_zh':locator,'locator_en':locator,'observed_version':version,'review_depth':'section_review' if section else 'abstract_review','checked_at':today})
        if 'monthly' not in d['destination']:continue
        date=updated if d['destination']=='topic_and_monthly_revision' else first;kind='revision' if d['destination']=='topic_and_monthly_revision' else 'first_submission'
        eid=event_identity(sid,version,kind,date,p['paper_id'])
        put('ic_evidence_items',{**BASE,'evidence_id':eid,'source_id':sid,'observed_version':version,'date_kind':kind,'date_precision':'day','publication_date':first,'event_date':date,'verified_at':today,'provenance_kind':'arxiv_official_api_with_model_review','source_revision':'arxiv:'+p['versioned_id']+':'+p['abstract_sha256'],'status':'primary_methods_and_results_checked' if section else 'primary_abstract_checked'})
        put('ic_paper_summary_events',{**BASE,'evidence_id':eid,'source_id':sid,'summary_id':summary_id,'observed_version':version,'period_id':month})
        story_id=scope+'__'+p['paper_id'].replace('.','-')
        story={**BASE,'story_id':story_id,'scope_id':scope,'period_id':month,'position':decision_position,'claim_status':'analyst_synthesis','checked_at':today}
        if 'selection_tier' in d:
            for field in ['selection_tier','selection_reason_zh','selection_reason_en']:story[field]=d[field]
        for lang in ['zh','en']:
            story['title_'+lang]=d['title_'+lang]
            for key in ['question','context']:story[key+'_'+lang]=d['background_'+lang]
            story['synthesis_'+lang]=d['mechanism_'+lang]
            for key in ['viewpoint','implication']:story[key+'_'+lang]=d['next_'+lang]
            story['boundary_'+lang]=d['boundary_'+lang]
        put('ic_monthly_route_insights',story)
        for topic in d['topics']:
            key=scope+'__'+topic+'__'+eid;put('ic_compression_topic_events',{**BASE,'link_id':key,'scope_id':scope,'period_id':month,'compression_topic_id':topic,'scope_topic_key':scope+'__'+topic,'evidence_id':eid,'source_id':sid,'position':int(date.replace('-','')),'review_status':'primary_review','reviewed_at':today,'association_note':d['mechanism_zh']+' '+d['boundary_zh'],'classification_basis':evidence_url})
            ref_id=story_id+'__'+summary_id+'__'+topic
            put('ic_monthly_route_evidence',{**BASE,'ref_id':ref_id,'story_id':story_id,'scope_id':scope,'period_id':month,'source_id':sid,'summary_id':summary_id,'observed_version':version,'compression_topic_id':topic,'evidence_id':eid,'position':decision_position})
        fid='finding-live-'+p['paper_id'].replace('.','-')+'-'+version+'-'+kind+'-'+date
        f={**BASE,'finding_id':fid,'kind':'current_event','recent_event_eligible':True,'date_kind':kind,'publication_date':first,'change_date':date,'checked_at':today,'position':decision_position,'claim_status':'primary_text_checked' if section else 'primary_abstract_checked','title_zh':d['title_zh'],'title_en':d['title_en'],'mechanism_label':'source_facts','change_label':'source_facts','relevance_label':'analyst_inference','next_suggestion_label':'analyst_suggestion','ascend_boundary_label':'reviewer_scope_and_compatibility_boundary'}
        for lang in ['zh','en']:
            f['summary_'+lang]=d['title_'+lang];f['background_'+lang]=d['background_'+lang]
            for field in ['change','innovation','mechanism']:f[field+'_'+lang]=d['mechanism_'+lang]
            f['results_'+lang]=d['results_'+lang];f['ascend_boundary_'+lang]=d['boundary_'+lang]
            for field in ['implication','relevance','next_suggestion']:f[field+'_'+lang]=d['next_'+lang]
        put('ic_findings',f)
        put('ic_finding_evidence',{**BASE,'evidence_link_id':fid+'__'+sid,'finding_id':fid,'source_id':sid,'checked_at':today,'checked_scope':'primary_methods_and_selected_results' if section else 'primary_abstract_checked','evidence_locator':locator,'evidence_role':'direct_paper_result','evidence_status':'checked_primary_source','local_measurement':False,'observed_version':version,'publication_date':first,'supported_claim_zh':d['results_zh'],'supported_claim_en':d['results_en']})
        link=fid+'__'+scope+'__'+eid;put('ic_finding_scopes',{**BASE,'link_id':link,'finding_id':fid,'scope_id':scope,'evidence_id':eid})
        for cell in d['cells']:
            cell_papers.setdefault(cell,[]).append(d)
            put('ic_finding_cells',{**BASE,'link_id':fid+'__'+cell,'finding_id':fid,'cell_id':cell})
            link=scope+'__'+eid+'__'+cell;put('ic_monthly_evidence_cells',{**BASE,'link_id':link,'scope_id':scope,'period_id':month,'evidence_id':eid,'cell_id':cell,'scope_cell_key':scope+'__'+cell,'position':int(date.replace('-','')),'role':'direct_mechanism','stage':d.get('stage','inference_candidate'),'status':'primary_methods_and_results_checked' if section else 'primary_abstract_checked','mechanism_summary':d['mechanism_zh'],'limitation':d['boundary_zh'],'validation_question':d['next_zh']})
    for r in table('ic_cells').values():
        cell=r['row'];items=cell_papers.get(cell['cell_id'],[]);key=scope+'__'+cell['cell_id']
        put('ic_monthly_cell_reviews',{**BASE,'review_id':key,'scope_id':scope,'period_id':month,'cell_id':cell['cell_id'],'scope_cell_key':key,'position':cell['position'],'sample_count':len(items),'reviewed_at':today,'comparison_scope_id':'','direction':'not_comparable','status':'reviewed_sample' if items else 'sample_gap','change_kind':'new_evidence' if items else 'collection_gap','highlight':'本月精选'+str(len(items))+'个去重论文事件；原文条件与证据层级分别保留。' if items else '这轮精选未纳入该方向，不代表领域没有新研究。','next_question':'；'.join(d['next_zh'] for d in items) if items else '继续从信源读取相关摘要，再按机制与证据质量筛选。'})
    prepared_path=reviewed/'prepared-content-patch.json'
    prepared=json.loads(prepared_path.read_text(encoding='utf-8')) if prepared_path.exists() else []
    allowed_prepared={'cloud_core_sources','ic_compression_topic_cards','ic_compression_topic_card_refs','ic_industry_source_scopes','ic_industry_updates','ic_industry_update_changes','ic_industry_change_topics','ic_industry_topic_assessments'}
    for entry in prepared:
        name,row=entry['table'],entry['row'];assert name in allowed_prepared
        assert row.get('business_id')=='cloud-core' and row.get('topic_id','cloud_core')=='cloud_core'
        if name=='ic_industry_updates':assert row['release_date'].startswith(month) and row['release_date']<=today and row['release_date_kind']=='official_publication'
        if name=='ic_compression_topic_card_refs':
            summary=table('ic_paper_summaries')[row['source_id']+'__'+row['observed_version']]['row']
            assert summary['reviewed_at']==row['checked_at'] and summary['evidence_locator']==row['locator_zh']
        put(name,row)
    changed=sorted({r['table'] for r in changes})
    for name in changed:
        dest=out/'tables'/name;dest.mkdir(parents=True,exist_ok=True)
        (dest/'rows.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in sorted(tables[name].values(),key=lambda r:r['key'])),encoding='utf-8')
    receipt={'scope_id':scope,'month':month,'local_only':True,'applied':False,'curated_papers':len(choices),'monthly_events':len(monthly),'historical_topic_migrations':sum(e['table']=='ic_compression_topic_cards' for e in prepared),'industry_updates':sum(e['table']=='ic_industry_updates' for e in prepared),'changes':changes}
    if apply:
        backup=ROOT/'.maintenance/backups'/('live-reading-'+batch)
        for name in changed:
            dest=backup/name;dest.mkdir(parents=True,exist_ok=True)
            if not (dest/'rows.jsonl').exists():(dest/'rows.jsonl').write_bytes(before[name])
            (ROOT/'data/compression/tables'/name/'rows.jsonl').write_bytes((out/'tables'/name/'rows.jsonl').read_bytes())
        check=subprocess.run([sys.executable,str(ROOT/'scripts/verify_tablegit_migration.py')],capture_output=True,text=True,encoding='utf-8')
        (out/'validation.txt').write_text(check.stdout+check.stderr,encoding='utf-8')
        if check.returncode:
            for name in changed:(ROOT/'data/compression/tables'/name/'rows.jsonl').write_bytes(before[name])
            raise RuntimeError('Canonical validation failed; this operation was rolled back. See '+str(out/'validation.txt'))
        receipt['applied']=True
    (out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='changes'}|{'changed_tables':changed,'changed_rows':len(changes)},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['acquired','reviewed','decisions','out']:p.add_argument('--'+name,required=True)
    p.add_argument('--apply',action='store_true');a=p.parse_args();adopt(a.acquired,a.reviewed,a.decisions,a.out,a.apply)
