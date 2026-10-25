"""Typed research relationships and views derived from the maintained operator facts."""
from html import escape as e
import json

ROLE_LABELS = {
    'mechanism': '加速做法', 'application': '场景组织',
    'training_extension': '训练关联', 'crosscutting_method': '实现方法',
    'judgment': '研究判断', 'execution_contract': '执行约束',
}
HARDWARE_LABELS = {'gpu':'GPU', 'ascend':'昇腾 NPU', 'other':'其他加速器', 'unspecified':'未限定平台'}
LEVEL_LABELS = {'capability':'机制 / 接口', 'kernel':'算子实验', 'stage':'模型阶段', 'system':'系统 / 服务', 'training':'训练参考', 'generation':'生成与调优评测'}
METRIC_LABELS = {'time':'时延 / 性能', 'quality':'数值 / 任务质量', 'memory':'容量 / 内存', 'coverage':'正确率 / 覆盖', 'bandwidth':'通信带宽', 'mechanism':'机制 / 能力'}


def record_anchor(record_id):
    return 'record-'+record_id


def compile_index(corpus, codegen, named_a, named_b, structure, sources):
    """Each experiment/ability record has one maintained fact origin; all views project it."""
    records=[]
    approaches=[]
    mechanisms=[]
    routes=[]
    for branch in corpus['branches']:
        for route in branch['routes']:
            route_id=route['id']
            spec=structure['routes'][route_id]
            routes.append({'id':route_id,'title':route['title'],'branch':branch['id'], 'url':'operators-'+route_id+'.html'})
            for item in spec['catalog']:
                mechanisms.append({'id':item['id'],'route_id':route_id,'title':item['title'],'source_ids':item['source_ids'],
                                   'approach_ids':[route['expert']['branches'][i]['id'] for i in item['from_branch_indices']],
                                   'url':'operators-'+route_id+'.html#'+item['id']})
            for approach in route['expert']['branches']:
                approaches.append({'id':approach['id'],'route_id':route_id,'name':approach['name'],
                                   'role':approach['role'],'url':'operators-'+route_id+'.html#'+approach['id'],
                                   'source_ids':approach['evidence_ids']})
            for group in ['industry','academic']:
                for row in route[group]:
                    facets=structure['evidence_facets'][row['id']]
                    associated=[a['id'] for a in route['expert']['branches'] if set(a['evidence_ids'])&set(row['source_ids'])]
                    records.append({'id':row['id'], 'route_id':route_id,'route_title':route['title'],
                                    'title':row['title'],'kind':group,'date':row['date'],
                                    'mechanism':row['mechanism'],'conditions':row['conditions'],'result':row['result'],
                                    'limit':row.get('boundary',row.get('evidence_scope','')),
                                    'result_type':row['result_type'],'source_ids':row['source_ids'],
                                    'approach_ids':associated,'facets':facets,
                                    'url':'operators-'+route_id+'.html#'+record_anchor(row['id']),
                                    'canonical_origin':'operator-routes.json#/branches/'+branch['id']+'/routes/'+route_id+'/'+group+'/'+row['id']})
    for packet_name,rows in [('operator-codegen-named-a.json',named_a['evidence_rows']),
                             ('operator-codegen-named-b.json',named_b['evidence']),
                             ('operator-codegen-insight.json',codegen['evidence'])]:
        for row in rows:
            records.append({'id':row['id'],'route_id':'codegen','route_title':'自动生成与调优 · 横向方法',
                            'title':row['work'],'kind':row.get('kind','academic'),'date':row['date'],
                            'mechanism':row['mechanism'],'conditions':row['conditions'],'result':row['result'],
                            'limit':row['limit'],'result_type':'生成与调优评测','source_ids':row['source_ids'],
                            'approach_ids':[], 'facets':structure['evidence_facets'][row['id']],
                            'url':'operators-codegen.html#evidence-'+row['id'],
                            'canonical_origin':packet_name+'#/'+('evidence_rows' if packet_name=='operator-codegen-named-a.json' else 'evidence')+'/'+row['id']})
    ids=[r['id'] for r in records]
    assert len(set(ids))==len(ids), 'Duplicate research fact IDs'
    assert set(structure['evidence_facets'])==set(ids), 'Unjoined search metadata'
    edges=[]
    for item in mechanisms:
        edges.append({'from':item['route_id'],'relation':'contains_mechanism','to':item['id']})
        for approach_id in item['approach_ids']:
            edges.append({'from':approach_id,'relation':'explains','to':item['id']})
    for a in approaches:
        edges.append({'from':a['route_id'],'relation':'contains_'+a['role'],'to':a['id']})
    for record in records:
        edges.append({'from':record['id'],'relation':'belongs_to','to':record['route_id']})
        for approach_id in record['approach_ids']:
            edges.append({'from':record['id'],'relation':'associated_with','to':approach_id})
        for source_id in record['source_ids']:
            edges.append({'from':record['id'],'relation':'cites','to':source_id})
    return {'schema_version':1,'generated_from':'maintained operator research; do not edit this projection',
            'reviewed_at':structure['reviewed_at'],'routes':routes,'mechanisms':mechanisms,'approaches':approaches,'records':records,
            'relations':edges,'sources':[sources[k] for k in dict.fromkeys(s for r in records+approaches+mechanisms for s in r['source_ids'])]}


def render_scope(spec):
    fields=[('研究对象',spec['research_object']),('保持不变','；'.join(spec['invariants'])),('直接改变',spec['direct_change'])]
    return '<dl class="op-definition">'+''.join('<div><dt>'+label+'</dt><dd>'+e(text)+'</dd></div>' for label,text in fields)+'</dl>'


def render_taxonomy(branch, specs, guides):
    html='<article id="'+branch['id']+'-map" class="op-family op-tree-family"><span class="op-kicker">'+('COMPUTE' if branch['id']=='compute' else 'COMMUNICATION')+'</span><h3><a href="operators-'+('1' if branch['id']=='compute' else '2')+'.html">'+e(branch['title'])+' →</a></h3><p>'+e(branch['summary'])+'</p><ol class="op-tech-tree">'
    for route in branch['routes']:
        terms=[route['title'],route['principle'],route['challenge']]+guides[route['id']]['search_terms']+[x['title']+' '+x['mechanism'] for group in ['industry','academic'] for x in route[group]]+[a['name'] for a in route['expert']['branches']]
        main=specs[route['id']]['catalog']
        html+='<li data-route-search="'+e(' '.join(terms),quote=True)+'"><div class="op-tree-node"><a href="operators-'+route['id']+'.html">'+e(route['title'])+' →</a><span>'+e(specs[route['id']].get('axis_label','执行机制'))+'</span></div><p class="op-map-judgment">'+e(route['expert']['brief'])+'</p><ul>'
        for a in main:
            html+='<li><a href="operators-'+route['id']+'.html#'+a['id']+'">'+e(a['title'])+'</a></li>'
        html+='</ul></li>'
    return html+'</ol></article>'


def render_approaches(route, spec, citations):
    questions={i:x for x in spec['subquestions'] for i in x['branch_indices']}
    html=''
    roles=list(dict.fromkeys(a['role'] for a in route['expert']['branches']))
    for role in roles:
        html+='<div class="op-approach-group"><h4>'+ROLE_LABELS[role]+'</h4><div class="op-table-scroll"><table class="op-comparison-table"><thead><tr><th>子问题与做法</th><th>怎样改变执行</th><th>代价与比较条件</th></tr></thead><tbody>'
        for i,a in enumerate(route['expert']['branches']):
            if a['role']!=role: continue
            q=questions.get(i)
            qhtml='<p class="op-subquestion">'+e(q['question'])+'</p>' if q else ''
            links=[]
            for group in ['industry','academic']:
                for record in route[group]:
                    if set(record['source_ids'])&set(a['evidence_ids']):
                        links.append('<a href="#'+record_anchor(record['id'])+'">'+e(record['title'])+' ↓</a>')
            html+='<tr id="'+a['id']+'" data-approach-role="'+role+'"><td data-label="子问题与做法"><span class="op-method-index">'+e(ROLE_LABELS[role])+'</span><strong>'+e(a['name'])+'</strong>'+qhtml+'</td><td data-label="怎样改变执行"><p>'+e(a['mechanism'])+'</p>'+citations(a['evidence_ids'])+'</td><td data-label="代价与比较条件"><p>'+e(a['tradeoff'])+'</p>'+(('<div class="op-related-evidence">关联工作：'+''.join(links)+'</div>') if links else '')+'</td></tr>'
        html+='</tbody></table></div></div>'
    return html


def render_method_catalog(spec, citations):
    return '<div class="op-method-catalog">'+''.join('<article id="'+x['id']+'"><span class="op-method-index">核心机制 / '+str(i).zfill(2)+'</span><h3>'+e(x['title'])+'</h3><p>'+e(x['text'])+'</p>'+citations(x['source_ids'])+'</article>' for i,x in enumerate(spec['catalog'],1))+'</div>'


def render_coupling(spec, route_lookup, citations):
    link=spec['cross_route_condition']
    related=route_lookup[link['with_route_id']]
    return '<article class="op-coupling"><span class="op-kicker">与其他机制的关系</span><h3>'+e(link['relationship'])+'</h3><p>'+e(link['condition'])+'</p><p>'+e(link['implication'])+'</p>'+citations(link['source_ids'])+'<a class="op-text-link" href="operators-'+related['id']+'.html">关联专题：'+e(related['title'])+' →</a></article>'


def render_library(index):
    def select(name,label,items):
        return '<label>'+label+'<select data-library-filter="'+name+'" aria-label="'+label+'"><option value="">全部</option>'+''.join('<option value="'+e(k,quote=True)+'">'+e(v)+'</option>' for k,v in items)+'</select></label>'
    labels=[(r['id'],r['title']) for r in index['routes']]+[('codegen','自动生成与调优（横向方法）')]
    html='<div class="op-library-controls"><label class="op-library-query">查找技术、工作或实验条件<input data-library-query type="search" placeholder="例如：INT4、H100、MoE、Mistral" aria-label="查找研究证据"></label>'+select('route','所属机制',labels)+select('hardware','材料涉及硬件',HARDWARE_LABELS.items())+select('level','证据层级',LEVEL_LABELS.items())+select('metric','关注指标',METRIC_LABELS.items())+'<button data-library-reset type="button">重置筛选</button></div><p class="op-library-status" data-library-count aria-live="polite">'+str(len(index['records']))+' 条记录；范围标签不代表目标设备已适配。</p><div class="op-library-list">'
    for r in index['records']:
        f=r['facets']
        search=' '.join([r['title'],r['mechanism'],r['conditions'],r['result']])
        html+='<article class="op-library-record" data-library-record="'+r['id']+'" data-route="'+r['route_id']+'" data-hardware="'+e(' '.join(f['hardware_families']),quote=True)+'" data-level="'+e(f['level'],quote=True)+'" data-metric="'+e(' '.join(f['metrics']),quote=True)+'" data-search="'+e(search.lower(),quote=True)+'"><div class="op-library-facets"><span>'+e(r['route_title'])+'</span><span>'+e(LEVEL_LABELS[f['level']])+'</span><span>'+e(' / '.join(HARDWARE_LABELS[x] for x in f['hardware_families']))+'</span></div><h3><a href="'+r['url']+'">'+e(r['title'])+' →</a></h3><p>'+e(r['result'])+'</p><small>'+e(r['date'])+'</small></article>'
    return html+'</div><p class="op-library-empty" hidden>没有同时符合这些条件的记录。可放宽硬件、层级或指标；未收录不等于技术不存在。</p>'


def render_judgment_log(log, record_lookup, citations, route_id=None):
    changes=[x for x in log['changes'] if route_id is None or route_id in x['route_ids']]
    html='<div class="op-change-log">'
    for row in changes:
        records=[record_lookup[x] for x in row['evidence_ids']]
        html+='<article id="change-'+row['id']+'"><div class="op-evidence-meta"><b>'+e(row['change_type'])+'</b><span>'+e(row['date'])+' · '+e(row['trigger_type'])+'</span></div><h3>'+e(row['title'])+'</h3><dl><div><dt>原有表述 / 范围</dt><dd>'+e(row['before'])+'</dd></div><div><dt>当前判断</dt><dd>'+e(row['after'])+'</dd></div><div><dt>调整原因</dt><dd>'+e(row['reason'])+'</dd></div></dl><div class="op-change-evidence">'+''.join('<a href="'+r['url']+'">'+e(r['title'])+' →</a>' for r in records)+'</div>'+citations(list(dict.fromkeys(s for r in records for s in r['source_ids'])))+'</article>'
    return html+'</div>'
