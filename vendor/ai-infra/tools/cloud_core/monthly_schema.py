"""Normalized monthly evidence side tables; no paper bodies or runtime JSON."""
import json

def field(kind='string',required=False,key=False):
    return {'type':kind,'required':required,'role':'key' if key else 'value'}
def schema(key,description,fields,indexes):
    values={key:field(required=True,key=True),'business_id':field(required=True),'topic_id':field(required=True),**fields}
    return {'key_field':key,'description':description,'fields':values,'required_fields':[k for k,v in values.items() if v['required']], 'indexes':[{'name':'idx_'+k,'field':k} for k in dict.fromkeys(['business_id','topic_id',*indexes])]}
def text(*keys): return {k:field(required=True) for k in keys}
DEFINITIONS={
 'ic_monthly_scopes':schema('scope_id','Explicit monthly evidence collection scope; sample counts never mean global totals.',{
   **text('period_id','month_basis','window_start','window_end','source_pool','title_zh','title_en','selection_rule','dedup_rule','collected_at','status','coverage_note','source_revision'),
   'position':field('integer',True)},['period_id','status','source_pool']),
 'ic_evidence_items':schema('evidence_id','One dated evidence event pointing to canonical URL-only source identity.',{
   **text('source_id','publication_date','event_date','date_precision','date_kind','observed_version','verified_at','status','provenance_kind','source_revision'),
   'source_document_id':field()},['source_id','event_date','date_kind','status']),
 'ic_monthly_evidence_cells':schema('link_id','Evidence event to monthly scope and canonical compression cell; bounded scope-cell index.',{
   **text('scope_id','period_id','evidence_id','cell_id','scope_cell_key','stage','role','mechanism_summary','limitation','validation_question','status'),
   'position':field('integer',True)},['scope_id','period_id','evidence_id','cell_id','scope_cell_key','status']),
 'ic_monthly_cell_reviews':schema('review_id','Monthly interpretation per scope/cell; counts validated against distinct source identities.',{
   **text('scope_id','period_id','cell_id','scope_cell_key','highlight','change_kind','direction','comparison_scope_id','next_question','status','reviewed_at'),
   'sample_count':field('integer',True),'position':field('integer',True)},['scope_id','period_id','cell_id','scope_cell_key','status'])
}
if __name__=='__main__': print(json.dumps(DEFINITIONS,ensure_ascii=False))
