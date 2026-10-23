"""An original, source-grounded teaching case. This never runs external skills."""
from html import escape as e


def vector(values, tone):
    return '<div class="cb-vector cb-vector--'+tone+'">'+''.join('<span>'+str(v)+'</span>' for v in values)+'</div>'


def render_case(case, citations):
    def p(value, cls=''):
        return '<p'+(' class="'+cls+'"' if cls else '')+'>'+e(value)+'</p>'

    output='<div id="cannbot" class="cb-case"><div class="cb-case-heading"><span class="op-kicker">CANNBOT · 源码线索与机制讲解</span><h3>'+e(case['title'])+'</h3>'+p(case['lead'])+'</div>'
    output+='<div class="cb-contract"><div><span>先固定计算语义</span><strong>'+e(case['formula'])+'</strong></div>'+p(case['contract'])+'</div>'
    output+='<div class="cb-host"><div><b>HOST · 制定执行计划</b><h4>输入描述 + 目标芯片 → 分块参数</h4>'+p('核数、每核范围、每片大小、最后一片的有效元素数。')+'</div><div class="cb-tiling"><span>核 0 · 数据区间 A</span><span>核 1 · 数据区间 B</span><span>核 … · 其余区间</span><small>区间不重叠，合起来覆盖全部输入</small></div></div>'
    output+='<div class="cb-host-device"><span>TilingData · 传递计划</span><span>↓</span></div>'
    output+='<div id="cannbot-execution" class="cb-device"><div class="cb-device-label"><b>DEVICE · 各核按片执行</b><span>下面只画同一片中的四个元素</span></div><div class="cb-stations">'
    output+='<article><span class="cb-step">01 / COPY IN</span><h4>把当前片搬入 UB</h4><div class="cb-array-label">GM 中的两个输入</div>'+vector([1,2,3,4],'blue')+vector([10,20,30,40],'teal')+'<div class="cb-stream"><i></i><i></i><i></i><span>GM → UB</span></div>'+p('CopyIn 搬当前 offset 对应的数据。队列交接后，计算才能使用。')+'</article>'
    output+='<article><span class="cb-step">02 / COMPUTE</span><h4>Vector 执行逐元素加法</h4>'+vector([1,2,3,4],'blue')+'<div class="cb-plus">+</div>'+vector([10,20,30,40],'teal')+'<div class="cb-equals">↓ Add</div>'+vector([11,22,33,44],'gold')+p('在片上计算这一片的结果。这里没有压缩，也没有减少加法次数。')+'</article>'
    output+='<article><span class="cb-step">03 / COPY OUT</span><h4>把结果写回对应位置</h4><div class="cb-array-label">UB 中的输出</div>'+vector([11,22,33,44],'gold')+'<div class="cb-stream cb-stream--out"><i></i><i></i><i></i><span>UB → GM</span></div><div class="cb-output">y 的当前输出片</div>'+p('CopyOut 写回同一 offset，释放缓冲后，下一片继续。')+'</article></div></div>'
    output+='<div class="cb-explanation"><article><h4>核间并行：不同核处理不同区间</h4>'+p('各核可以独立做 Add。它们的区间必须无遗漏、无重叠；尾部不足整块时，只读写有效元素。')+'</article><article><h4>核内流水：不同片才有重叠机会</h4>'+p('同一片依然先搬入、再计算、再写回。多个缓冲让下一片搬入与当前片计算有机会重叠；是否成立还取决于依赖和同步。')+'</article></div>'
    output+='<div class="cb-code"><div><b>分块访问必须带上位置</b><span>逻辑伪代码 · 不可直接编译为 Ascend C</span></div><pre><code>'+e('coreBase, coreCount = 本核的数据范围\nfor k in range(ceil_div(coreCount, tileSize)):\n    offset = coreBase + k * tileSize\n    count = min(tileSize, coreCount - k * tileSize)\n    CopyIn(offset, count)\n    Compute(count)\n    CopyOut(offset, count)')+'</code></pre></div>'
    output+=p(case['template_review'],'cb-review')+citations(['cannbot-add-template'])
    output+='<div id="cannbot-concepts" class="cb-subsection"><h3>八个关键概念，各回答一个问题</h3><div class="cb-concepts">'
    for i,row in enumerate(case['concepts'],1):
        output+='<article id="cannbot-'+row['id']+'"><div class="cb-concept-heading"><span>'+str(i).zfill(2)+'</span><h4>'+e(row['name'])+'</h4></div><p class="cb-term">'+e(row['term'])+'</p><h5>'+e(row['question'])+'</h5>'+p(row['explanation'])+'<div class="cb-source-locator">'+e(row['where'])+'</div>'+citations(row['source_ids'])+'</article>'
    output+='</div></div>'
    output+='<div id="cannbot-judgments" class="cb-subsection"><h3>理解这些概念后，能作出什么判断</h3><div class="cb-judgments">'
    for row in case['judgments']:
        output+='<article><h4>'+e(row['title'])+'</h4>'+p(row['text'])+'</article>'
    output+='</div>'+p('以上是计算量与数据流的分析，不是目标设备的性能测量；实际时延还受输入规模、访存效率、缓存与调用路径影响。','op-note')+'</div>'
    fusion=case['fusion']
    output+='<div id="cannbot-fusion" class="cb-subsection cb-fusion"><span class="op-kicker">从独立算子走向相邻操作</span><h3>'+e(fusion['title'])+'</h3><div class="cb-fusion-formula">'+e(fusion['formula'])+'</div>'+p(fusion['description'])+'<div class="cb-fusion-flow"><div><b>分开执行</b><span>Add → 写 z 到 GM → 重新读 z → RMSNorm</span></div><div><b>融合候选</b><span>Add → 在片上消费 z → RMSNorm</span><small>若 z 是必需输出，写回 z 的分支仍然保留</small></div></div><div class="cb-explanation"><article><h4>z 也要作为输出</h4>'+p(fusion['preserved_output'])+'</article><article><h4>z 只在内部使用</h4>'+p(fusion['internal_only'])+'</article></div>'+p(fusion['precision'],'op-note')+citations(fusion['source_ids'])+'</div>'
    output+='<div id="cannbot-routes" class="cb-subsection"><h3>同一案例，回到四条根技术路线</h3><div class="cb-route-mapping">'
    for row in case['route_links']:
        output+='<article><h4><a href="operators-'+row['route_id']+'.html">'+e(row['name'])+' →</a></h4>'+p(row['observation'])+'<div class="cb-next"><b>值得比较的改变</b>'+p(row['action'])+'</div>'+citations(row['source_ids'])+'</article>'
    output+='</div></div>'
    eng=case['engineering']
    output+='<div class="cb-subsection"><h3>'+e(eng['title'])+'</h3>'+p(eng['text'])+p(eng['migration'],'op-note')+citations(eng['source_ids'])+'</div>'+p(case['scope'],'op-note')+'</div>'
    return output


def route_hook(case, route, citations):
    entry=next(row for row in case['route_links'] if row['route_id']==route['id'])
    return '<div class="cb-route-hook"><span class="op-kicker">用 CANNBOT 的 ADD 案例理解本机制</span><p>'+e(entry['observation'])+'</p><p><strong>具体看什么：</strong>'+e(entry['action'])+'</p><a class="op-text-link" href="operators-1.html#cannbot">查看完整数据流与概念解释 →</a>'+citations(entry['source_ids'])+'</div>'
