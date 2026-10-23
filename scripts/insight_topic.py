"""Reusable, unpublished insight source scaffolding and evidence-contract validation."""
import argparse
import copy
import html
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT/'.agents/skills/ccn-insight-build/assets/topic.template.json'
DEPTHS = {'candidate','abstract','sections','full_text','independently_reproduced'}
CONDITIONS = ['model','hardware','task','workload','baseline']

def metric_errors(m):
    errors=[]
    status=m.get('status')
    if status not in {'reported','not_reported','theoretical'}:return ['invalid metric status']
    if not m.get('metric'):errors.append('metric name missing')
    if status=='not_reported':
        if m.get('value') is not None:errors.append('unreported value must be null, not zero')
        return errors
    if status=='theoretical':
        if not m.get('formula'):errors.append('theoretical metric requires formula')
        if m.get('comparison_ready'):errors.append('theory is not a reported comparison')
        return errors
    value=m.get('value')
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):errors.append('reported metric requires finite numeric value')
    for key in ['unit','scope','statistic','locator']:
        if not m.get(key):errors.append(key+' missing')
    if m.get('scope') not in {'kernel','forward','serving','training','storage'}:errors.append('invalid metric scope')
    if m.get('metric','').upper() in {'TTFT','TPOT'} and m.get('scope')!='serving':errors.append('TTFT/TPOT require serving evidence')
    missing=[k for k in CONDITIONS if not m.get(k)]
    if missing:
        if m.get('comparison_ready'):errors.append('comparison lacks '+','.join(missing))
        if not set(missing)<=set(m.get('missing_conditions',[])):errors.append('missing conditions must be explicit')
    if m.get('result_design')=='combined' and m.get('attribution')=='component':errors.append('combined result cannot establish component attribution')
    return errors

def validate_topic(topic):
    errors=[]
    for k in ['id','domain','title','question','status','sections','sources','claims','judgments','changes']:
        if k not in topic:errors.append('missing '+k)
    if errors:return errors
    if topic['status'] not in {'draft','reviewed'}:errors.append('topic status must be draft/reviewed; publishing is separate')
    for k in ['id','domain']:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',topic[k]):errors.append('unsafe '+k)
    for k in ['title','question']:
        if not isinstance(topic[k],str) or not topic[k].strip():errors.append('empty '+k)
    sources={}
    for s in topic['sources']:
        sid=s.get('id')
        if not sid or sid in sources:errors.append('source ID absent or duplicated')
        sources[sid]=s
        for k in ['url','title','version','review_depth']:
            if not s.get(k):errors.append(str(sid)+': missing '+k)
        from urllib.parse import urlsplit,parse_qs
        u=urlsplit(s.get('url',''))
        if u.scheme!='https' or not u.netloc or u.username or u.password:errors.append(str(sid)+': unsafe source URL')
        if any(re.search(r'token|password|secret|credential|signature|api.?key',k,re.I) for k in parse_qs(u.query)):errors.append(str(sid)+': URL contains secret-like parameter')
        if s.get('review_depth') not in DEPTHS:errors.append(str(sid)+': invalid review depth')
        if s.get('review_depth')!='candidate':
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',s.get('checked_at','')) or not s.get('locator'):errors.append(str(sid)+': reviewed source lacks date/locator')
    claims={}
    for c in topic['claims']:
        cid=c.get('id')
        if not cid or cid in claims:errors.append('claim ID absent or duplicated')
        claims[cid]=c
        if c.get('kind') not in {'fact','analysis','hypothesis'}:errors.append(str(cid)+': invalid claim kind')
        if not c.get('text'):errors.append(str(cid)+': empty claim')
        ids=c.get('source_ids',[])
        if not ids or any(sid not in sources for sid in ids):errors.append(str(cid)+': unresolved evidence')
        if c.get('kind')=='fact' and ids and all(sources.get(sid,{}).get('review_depth')=='candidate' for sid in ids):errors.append(str(cid)+': candidate-only evidence cannot establish fact')
        if c.get('kind')=='hypothesis' and not c.get('validation_condition'):errors.append(str(cid)+': hypothesis needs validation condition')
        for m in c.get('metrics',[]):errors.extend(str(cid)+': '+e for e in metric_errors(m))
    for j in topic['judgments']:
        if not j.get('text') or not j.get('claim_ids') or any(cid not in claims for cid in j.get('claim_ids',[])):errors.append('judgment needs resolved claims')
        if not j.get('would_change_if'):errors.append('judgment lacks change condition')
    if topic['status']=='reviewed':
        if not any(c.get('kind')=='fact' for c in topic['claims']) or not topic['judgments']:errors.append('reviewed topic needs facts and judgments')
        if not topic['sections'].get('challenges') or not topic['sections'].get('routes'):errors.append('reviewed topic needs challenges and routes')
    return errors

def render(topic):
    e=lambda x:html.escape(str(x),quote=True)
    parts=[f'<header><small>{e(topic["domain"].upper())} / RESEARCH DRAFT</small><h1>{e(topic["title"])}</h1><p>{e(topic["question"])}</p><span class="tag">未发布 · 证据驱动的研究起点</span></header>']
    for key,label in [('background','背景与价值'),('principles','机制与原理'),('challenges','关键挑战'),('routes','技术路线')]:
        values=topic['sections'].get(key,[])
        body=''.join(f'<article><h3>{e(v.get("title",""))}</h3><p>{e(v.get("text",""))}</p></article>' for v in values)
        parts.append(f'<section><h2>{label}</h2>{body or "<p class=empty>尚未录入经核对内容，需按该领域建立研究问题与证据。</p>"}</section>')
    parts.append('<section><h2>证据与判断</h2>')
    for c in topic['claims']:
        parts.append(f'<article id="claim-{e(c["id"])}"><span class="tag">{e(c["kind"])}</span><p>{e(c["text"])}</p>')
        for m in c.get('metrics',[]):
            value='未报告' if m['status']=='not_reported' else '理论：'+str(m.get('formula','')) if m['status']=='theoretical' else str(m['value'])+' '+str(m['unit'])
            conditions=' · '.join(str(m.get(k,'未交代')) for k in CONDITIONS) if m['status']=='reported' else ''
            parts.append(f'<p><b>{e(m["metric"])}：{e(value)}</b><br><small>{e(conditions)}</small></p>')
        parts.append('</article>')
    if not topic['claims']:parts.append('<p class="empty">暂无已核实主张；模板不会自动生成技术结果。</p>')
    for j in topic['judgments']:parts.append(f'<article><h3>{e(j["text"])}</h3><p>改变判断的条件：{e(j["would_change_if"])}</p></article>')
    parts.append('</section><section><h2>原始来源</h2><ol>')
    for s in topic['sources']:parts.append(f'<li><a href="{e(s["url"])}" rel="noopener noreferrer">{e(s["title"])}</a> · {e(s["review_depth"])} · {e(s.get("locator","尚未审阅"))}</li>')
    parts.append('</ol></section>')
    style='body{margin:0;background:#edf3f7;color:#1a3c50;font:16px/1.85 system-ui,sans-serif}main{max-width:1040px;margin:auto;padding:32px 24px}header{padding:40px;background:radial-gradient(ellipse at top right,#21556b,#10283c);color:#e7f7fa;border-radius:18px}header h1{font-size:38px;line-height:1.3;letter-spacing:-.03em}header small{color:#8bdfd4;letter-spacing:.15em}section{margin:34px 0}h2{font-size:24px;border-bottom:1px solid #cddde5;padding-bottom:12px}article{padding:24px;background:white;border:1px solid #d8e5eb;border-radius:12px;margin:14px 0}p{max-width:78ch}.tag{display:inline-block;font-size:12px;border:1px solid #81aaa9;padding:3px 10px;border-radius:6px}.empty,small{color:#647f90}a{color:#087f8b}@media(max-width:600px){main{padding:16px}header{padding:24px}header h1{font-size:29px}article{padding:18px}}'
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(topic['title'])+' · CCN研究草稿</title><style>'+style+'</style><main>'+''.join(parts)+'</main></html>'

def self_test():
    valid={'metric':'TTFT','status':'reported','value':12,'unit':'ms','scope':'serving','statistic':'median','model':'model-a','hardware':'device-a','task':'task-a','workload':'batch=1','baseline':'same setup','locator':'Table 1','comparison_ready':True}
    cases=[('valid',valid,False),('kernel is not TTFT',{**valid,'scope':'kernel'},True),('prefill is not TTFT',{**valid,'scope':'forward'},True),('unknown is not zero',{'metric':'TPOT','status':'not_reported','value':0},True),('missing workload',{**valid,'workload':'','missing_conditions':[]},True),('combined attribution',{**valid,'result_design':'combined','attribution':'component'},True),('missing reported value',{**valid,'value':None},True),('theory is separate',{'metric':'weight bytes','status':'theoretical','formula':'P*b/8','comparison_ready':False},False)]
    for label,case,invalid in cases:
        assert bool(metric_errors(case))==invalid,label
    print('PASS: 8 evidence-contract cases; rejects metric relabeling, missing conditions and causal overclaim')

def main():
    p=argparse.ArgumentParser(description=__doc__);subs=p.add_subparsers(dest='command',required=True)
    n=subs.add_parser('new')
    for key in ['domain','slug','title','question']:n.add_argument('--'+key,required=True)
    for cmd in ['validate','render']:
        sub=subs.add_parser(cmd);sub.add_argument('topic',type=Path)
        if cmd=='render':sub.add_argument('--out',type=Path,required=True)
    subs.add_parser('self-test');a=p.parse_args()
    if a.command=='self-test':self_test();return
    if a.command=='new':
        for value in [a.domain,a.slug]:
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',value):p.error('domain/slug require lowercase hyphenated identifiers')
        target=ROOT/'content/insights'/a.domain/a.slug/'topic.json'
        if target.exists():p.error('topic already exists; edit the existing source')
        value=copy.deepcopy(json.loads(TEMPLATE.read_text(encoding='utf-8')));value.update(id=a.slug,domain=a.domain,title=a.title,question=a.question)
        errors=validate_topic(value)
        if errors:p.error('; '.join(errors))
        target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Created unpublished source:',target);return
    value=json.loads(a.topic.read_text(encoding='utf-8'));errors=validate_topic(value)
    if errors:p.error('; '.join(errors))
    if a.command=='validate':print('PASS: topic contract; not a factual or publication certification');return
    target=a.out.resolve()
    if not any(folder==target or folder in target.parents for folder in [(ROOT/'.tmp').resolve(),(ROOT/'dist/drafts').resolve()]):p.error('isolated preview output must be inside .tmp/ or dist/drafts/')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(render(value),encoding='utf-8');print('Rendered isolated, unpublished preview:',target)

if __name__=='__main__':main()
