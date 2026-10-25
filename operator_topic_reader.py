"""Project maintained operator facts into the compression topic reading contract."""
from html import escape as e


def research_brief(title, judgment, methods, records, questions, sources, page):
    ids=list(dict.fromkeys(s for row in records for s in row['source_ids']))
    fields=[('核心判断',judgment),('代表路线','；'.join(methods)),
            ('证据现状',str(len(records))+'条研究记录，案例引用'+str(len(ids))+'项原始来源；页首另计全专题关联来源。原始结果保留硬件、任务、基线和预算，核对范围随来源列示。'),
            ('关键缺口','；'.join(questions))]
    html='<section class="expert-topic-entry"><header class="expert-entry-head"><span class="expert-kicker">研究速览</span><span class="expert-entry-axis">机制 · 对照 · 证据 · 缺口</span></header><h3>'+e(title)+'</h3><div class="expert-brief-grid">'
    for i,(label,text) in enumerate(fields,1):
        html+='<article><span class="expert-brief-number">'+str(i).zfill(2)+'</span><h4>'+label+'</h4><p>'+e(text)+'</p></article>'
    html+='</div></section><section class="expert-evidence-index" id="expert-evidence-index" data-topic-evidence><h3>证据导航</h3><div class="expert-evidence-controls"><select aria-label="证据导航显示范围"><option value="all">全部案例</option><option value="industry">产业界</option><option value="academic">学术界</option><option value="saved">本专题待读</option></select><span data-topic-evidence-count aria-live="polite">'+str(len(records))+'个案例</span></div><div class="expert-evidence-links">'
    for row in records:
        record_id='operator:'+row['id']
        anchor=row['url'].split('#',1)[1]
        scope='；'.join(sources[s]['review_scope'] for s in row['source_ids'])
        href='#'+anchor if row['url'].split('#',1)[0]==page else row['url']
        html+='<div class="expert-evidence-row" data-topic-record="'+e(record_id,quote=True)+'" data-kind="'+e(row['kind'],quote=True)+'"><a href="'+e(href,quote=True)+'">'+e(row['title'])+'</a><a class="expert-index-scope" href="#source-'+e(row['source_ids'][0])+'" title="'+e(scope,quote=True)+'">核对范围</a><button type="button" class="expert-save" data-save-card="'+e(record_id,quote=True)+'" aria-pressed="false">加入待读</button></div>'
    html+='</div><p data-topic-evidence-empty hidden>当前范围没有案例。可调整筛选，或先把案例加入待读。</p><p class="expert-index-note">待读仅保存在当前浏览器。核对范围不等于全文审阅或独立复现；GPU与NPU结果分别保留原始条件。</p></section>'
    html+='<section class="expert-retrieval"><h3>按技术或问题直接查找</h3><label for="operator-topic-query">检索本专题已展示的内容</label><input id="operator-topic-query" type="search" data-topic-query placeholder="输入技术、模型、指标或实验条件"><div data-topic-query-results aria-live="polite"></div></section>'
    return html
