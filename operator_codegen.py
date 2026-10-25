"""Hardware-bound operator generation insight; all text is visible without JS."""
from html import escape as e


def render_codegen(data, hardware, extra_a, extra_b, citations, hero, section, references, shell, brief):
    def p(text, cls=''):
        return '<p'+(' class="'+cls+'"' if cls else '')+'>'+e(text)+'</p>'

    all_rows=extra_a['evidence_rows']+extra_b['evidence']+data['evidence']
    source_ids=[]
    for rows in [hardware['platforms'],hardware['tools'],data['hardware_rows'],data['methods'],all_rows]:
        source_ids += [sid for row in rows for sid in row['source_ids']]
    body=hero('算子自动生成与调优',data['summary'],data['judgment'],'算子定制加速 / 横向效率技术',visual=False)
    body+=section('brief','01','速览与证据',brief)
    body+=section('background','02','研究背景',p(data['summary'])+p(data['scope'],'op-note'))
    platform_html='<div class="cg-platforms">'
    for i,row in enumerate(hardware['platforms']):
        platform_html+='<article class="cg-platform cg-platform--'+('gpu' if i==0 else 'npu')+'"><span class="cg-hardware-label">'+('GPU / CUDA' if i==0 else 'NPU / ASCEND')+'</span><h3>'+e(row['title'])+'</h3>'+p(row['subtitle'])+'<ol>'+''.join('<li><b>'+str(n).zfill(2)+'</b><span>'+e(v)+'</span></li>' for n,v in enumerate(row['nodes'],1))+'</ol>'+p(row['note'],'cg-platform-note')+citations(row['source_ids'])+'</article>'
    platform_html+='</div>'+p(hardware['scope'],'op-note')
    platform_html+='<div class="op-table-scroll"><table class="cg-hardware-table"><thead><tr><th>比较维度</th><th>GPU 研究关注什么</th><th>昇腾 NPU 研究关注什么</th><th>迁移时保留与重建什么</th></tr></thead><tbody>'
    for row in data['hardware_rows']:
        platform_html+='<tr><td data-label="比较维度">'+e(row['topic'])+'</td><td data-label="GPU研究">'+e(row['gpu'])+'</td><td data-label="昇腾NPU研究">'+e(row['npu'])+'</td><td data-label="迁移启示">'+e(row['implication'])+citations(row['source_ids'])+'</td></tr>'
    platform_html+='</tbody></table></div>'
    compare='<div class="op-table-scroll"><table class="cg-project-table"><thead><tr><th>系统 / 原始证据</th><th>技术区别</th><th>已报告硬件</th><th>值得吸收的部分</th><th>判断时保留的条件</th></tr></thead><tbody>'
    for row in data['project_comparisons']:
        compare+='<tr><td><a href="#evidence-'+row['evidence_id']+'">'+e(row['name'])+' ↓</a></td><td data-label="技术区别">'+e(row['method'])+'</td><td data-label="已报告硬件">'+e(row['hardware'])+'</td><td data-label="值得吸收">'+e(row['learn'])+'</td><td data-label="保留条件">'+e(row['limit'])+'</td></tr>'
    compare+='</tbody></table></div>'+p('这里比较方法与证据，不按不同实验的最大倍数排名。MTIA 是 Meta 自研加速器，不是昇腾；AVO 在此指 NVIDIA 的 Agentic Variation Operators。','op-note')
    methods='<div class="cg-methods">'
    for i,row in enumerate(data['methods'],1):
        methods+='<article><span>'+str(i).zfill(2)+'</span><div><h3>'+e(row['title'])+'</h3>'+p(row['mechanism'])+p(row['limit'],'op-note')+citations(row['source_ids'])+'</div></article>'
    methods+='</div>'+p('这些环节可以组合使用。语言/DSL决定如何表达候选，编译器负责转换与约束，搜索负责选择，LLM/Agent负责提出与修改候选；最终由独立执行评估作取舍。','op-boundary')
    body+=section('principles','03','基本原理',section('methods','方法','生成与调优的方法组成',methods,level=3))
    cards=''
    # The named-a records are paper-backed; author affiliation does not turn
    # a paper into an industry engineering report. Keep each record intact.
    groups=[('产业界 · 官方工程报告',[r for r in all_rows if r.get('kind','academic')=='industry']),('学术界 · 论文与预印本',[r for r in all_rows if r.get('kind','academic')!='industry'])]
    for label,rows in groups:
        cards+='<div class="cg-evidence-group"><h3>'+label+'</h3>'
        for row in rows:
            cards+='<article class="cg-evidence topic-dossier-card" id="evidence-'+row['id']+'"><div class="cg-evidence-header"><span>'+e(row['platform'])+'</span><small>'+e(row['date'])+'</small></div><h4>'+e(row['work'])+'</h4><div class="cg-mechanism"><b>关键技术</b>'+p(row['mechanism'])+'</div><div class="op-evidence-facts"><div><strong>硬件、任务、基线与预算</strong>'+p(row['conditions'])+'</div><div><strong>原始材料报告的效果</strong>'+p(row['result'])+'</div></div><div class="cg-evidence-limit"><b>结论边界</b>'+p(row['limit'])+'</div>'+citations(row['source_ids'])+'</article>'
        cards+='</div>'
    cards=p('按官方工程报告与论文/预印本区分证据类型，硬件、任务、基线与分母随每条结果保留。下面均为原作者材料；本页没有运行这些系统，也没有测得本地模型的 TTFT、TPOT 或质量变化。','op-note')+cards
    tool='<div class="op-table-scroll"><table class="cg-tool-table"><thead><tr><th>语言与编译路径</th><th>承担什么</th><th>版本与产品范围</th><th>对生成器的意义</th></tr></thead><tbody>'
    for row in hardware['tools']:
        tool+='<tr><td data-label="语言与编译路径">'+e(row['name'])+citations(row['source_ids'])+'</td><td data-label="承担什么">'+e(row['role'])+'</td><td data-label="版本与产品范围">'+e(row['support'])+'</td><td data-label="对生成器的意义">'+e(row['implication'])+'</td></tr>'
    tool+='</tbody></table></div>'+p('版本证据会更新。旧版本限制保留在历史记录，新版本以固定tag/产品表重新核对，不用采集工具的SoC枚举替代编译后端支持。','op-note')
    platform_html+=section('toolchain','工具链','语言、编译路径与版本资格',tool,level=3)
    body+=section('challenges','04','关键挑战',section('hardware','硬件','GPU/NPU与工具链',platform_html,level=3))
    body+=section('progress','05','技术进展',section('evidence','证据','产业与学术证据',cards,level=3))
    body+=section('comparison','06','比较判断',section('projects','系统比较','五个重点系统：技术区别与证据入口',compare,level=3))
    practice='<div class="cg-takeaways">'+''.join('<article><span>当前观察 / '+str(i).zfill(2)+'</span><h3><a href="'+row['target']+'">'+e(row['title'])+' ↑</a></h3>'+p(row['text'])+citations(row['source_ids'])+'</article>' for i,row in enumerate(data['takeaways'],1))+'</div>'
    practice+='<div class="cg-target-actions">'
    for row in hardware['implications']:
        practice+='<article><span>'+e(row['dimension'])+'</span><div><h3>'+e(row['title'])+'</h3>'+p(row['insight'])+'<h4>对工具能力演进的意义</h4>'+p(row['meaning'])+p(row['boundary'],'op-note')+citations(row['source_ids'])+'</div></article>'
        source_ids+=row['source_ids']
    practice+='</div>'+p(hardware['transfer_note'],'op-boundary')+'<div class="op-sibling-links"><a href="operators-1.html#cannbot">用 Add 案例理解 Host、Kernel 与缓冲 →</a><a href="operators.html#routes">回到加速根技术目录 →</a></div>'
    conclusion='<div class="cg-conclusions">'+''.join('<article><h4>'+e(row['title'])+'</h4>'+p(row['text'])+'</article>' for row in data['conclusions'])+'</div>'+citations(['ascendoptimizer-v2','kernelblaster-paper-named-a','kernelevolve-paper-named-a','avo-paper-named-a','cuda-agent-paper','ascendkernelgen'])
    conclusion+=p(data['update_principle'],'op-boundary')+p(data['scope'],'op-note')
    practice+=section('conclusion','结论','结论与后续跟踪',conclusion,level=3)
    body+=section('practice','07','研究结论',practice)
    body+=references(source_ids)
    outline=[('brief','01 速览与证据'),('background','02 研究背景'),('principles','03 基本原理'),('challenges','04 关键挑战'),('progress','05 技术进展'),('comparison','06 比较判断'),('practice','07 研究结论'),('references','资料依据')]
    return shell('算子自动生成与调优',body,outline,'compute')
