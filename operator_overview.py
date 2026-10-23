"""Research hub: hierarchy, comparisons, canonical evidence and judgment revisions."""
from html import escape as e
from operator_platform import render_taxonomy, render_coupling, render_library, render_judgment_log


def render_overview(corpus, structure, guide, changes, index, citations, hero, section, references, shell, boundaries):
    def p(text, cls=''):
        return '<p'+(' class="'+cls+'"' if cls else '')+'>'+e(text)+'</p>'
    routes={r['id']:r for b in corpus['branches'] for r in b['routes']}
    records={r['id']:r for r in index['records']}
    body=hero('算子定制加速',corpus['overview']['summary'],corpus['overview']['judgment'],visual=True)
    body+='<nav class="op-route-jumps" aria-label="专题章节直达"><a href="#routes">技术体系</a><a href="#evidence-library">研究证据</a><a href="#updates">判断更新</a></nav>'
    search='<div class="op-searchbar"><input type="search" data-operator-search aria-label="按名称或瓶颈查找算子机制" placeholder="查找机制与做法，例如：FA3、Split-K、缓冲"><span data-search-count aria-live="polite">9 / 9 项机制</span></div>'
    tree=search+'<div class="op-family-grid">'+''.join(render_taxonomy(b,structure['routes'],guide['routes']) for b in corpus['branches'])+'</div><p class="op-filter-empty" hidden>没有匹配的机制。可尝试“分块”“布局”或“等待”。</p>'
    body+=section('routes','01','技术体系',p('研究对象分为计算与通信，再按直接改变的执行机制展开具体做法。应用案例、训练关联和生成工具在专题内另行标明，不混作同级根技术。')+tree)
    costs=[('数据流量','重复输入读取、中间写回、表示转换与通信载荷。','减少不必要的字节，或提高一次加载的消费次数。'),('执行组织','独立工作量、归约协作、尾块与阶段流水。','有效计算增加时，同步与资源代价也要计入。'),('发起与准备','短核/小消息启动、打包、注册与缓冲建立。','聚合省固定成本，也可能增加就绪等待。'),('关键路径','数据何时可消费、阶段间依赖与资源争用。','更早推进消费者，不等于每个独立阶段都更快。')]
    compare='<div class="op-table-scroll"><table><thead><tr><th>比较坐标</th><th>具体观察什么</th><th>判断依据</th></tr></thead><tbody>'+''.join('<tr><td>'+a+'</td><td data-label="具体观察什么">'+b+'</td><td data-label="判断依据">'+c+'</td></tr>' for a,b,c in costs)+'</tbody></table></div>'
    compare+=p('下面三组关系解释复用、分块、消息组织与数据路径为什么不能按独立收益相加。','op-note')
    pairs=['memory-reuse','launch-granularity','collectives-topology']
    for rid in pairs:
        compare+='<div class="op-coupling-origin"><a href="operators-'+rid+'.html">'+e(routes[rid]['title'])+' →</a></div>'+render_coupling(structure['routes'][rid],routes,citations)
    body+=section('principles','02','机制之间怎样取舍',compare)
    body+=section('evidence-library','03','研究证据检索',p('先按技术问题查资料，再按材料涉及的硬件、证据层级与关注指标缩小范围。结果直接进入专题中的完整记录；检索视图与正文由同一份事实生成。')+render_library(index))
    focus='<div class="op-frontier-grid">'
    for row in guide['frontier']:
        record=records[row['record_id']]
        focus+='<article><span class="op-kicker">观察与依据</span><h3><a href="'+record['url']+'">'+e(row['title'])+' →</a></h3><div class="op-fact"><b>原始记录</b>'+p(record['result'])+citations(record['source_ids'])+'</div><div class="op-view"><b>研究判断</b>'+p(row['view'])+'</div></article>'
    focus+='</div>'
    judgment='<div class="cg-conclusions">'+''.join('<article><h3>'+e(r['title'])+'</h3>'+p(r['text'])+citations(r['source_ids'])+'</article>' for r in corpus['overview']['conclusions'])+'</div>'
    judgment+=section('frontier','依据','哪些证据影响当前判断',focus,3)
    judgment+=section('updates','修订','判断怎样被证据更新',p(changes['scope'],'op-note')+render_judgment_log(changes,records,citations),3)
    body+=section('conclusion','04','研究判断与更新',judgment)
    appendix=section('hardware','硬件','GPU与昇腾NPU的实现边界',p('CUDA GPU的线程/warp、存储与异步指令，和具体昇腾SoC的Host Tiling、Vector/Cube、搬运与同步约束分别核对。部分新代际昇腾提供SIMT能力，不能把GPU/NPU标签当作完整支持矩阵。')+citations(['cuda-programming-model','ascend-3510-architecture'])+'<a href="operators-1.html#cannbot">从Add数据流看硬件映射 →</a>',3)
    appendix+=section('automatic','方法','横向方法：自动生成与调优',p('编译、参数搜索、经验检索和LLM/Agent帮助形成实现。开发效率与运行收益分别评价；它们承接加速机制，不另设为第三条加速主线。')+'<a class="op-text-link" href="operators-codegen.html">进入方法体系、GPU/NPU证据与能力判断 →</a>',3)
    appendix+=section('evaluation','评价','证据层级与评价范围','<div class="op-evaluation-grid"><article><h3>语义与数值</h3>'+p('固定完整输出和允许误差，覆盖shape、尾块与特殊值。业务质量目标不能替代内核正确性。')+'</article><article><h3>执行与模块</h3>'+p('完整计入转换、打包、同步、工作区与强基线；单核和完整模块分别比较。')+'</article><article><h3>模型与服务</h3>'+p('模型服务再比较质量、TTFT/TPOT和达标吞吐。热点倍数、前向阶段和服务指标不互换。')+'</article></div>',3)
    appendix+=section('boundaries','归属','与相邻根技术的关系',boundaries(),3)
    body+=section('scope','附录','研究边界与方法',appendix)
    used=['ascendc','msprof','hccl','nccl','nccl-tests','cuda-programming-model','ascend-3510-architecture']
    used+=[s for row in corpus['overview']['conclusions'] for s in row['source_ids']]
    used+=[s for row in guide['frontier'] for s in records[row['record_id']]['source_ids']]
    used+=[s for rid in pairs for s in structure['routes'][rid]['cross_route_condition']['source_ids']]
    used+=[s for row in changes['changes'] for rid in row['evidence_ids'] for s in records[rid]['source_ids']]
    body+=references(used)
    outline=[('routes','01 技术体系'),('principles','02 跨机制比较'),('evidence-library','03 研究证据检索'),('conclusion','04 研究判断'),('frontier','支撑判断的证据'),('updates','判断修订记录'),('scope','附录：范围与方法'),('hardware','硬件边界'),('automatic','横向效率方法'),('evaluation','证据层级'),('boundaries','相邻根技术'),('references','资料依据')]
    return shell('算子定制加速',body,outline)
