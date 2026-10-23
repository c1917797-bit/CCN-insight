"""Dated selection with coverage limits, linked to canonical evidence."""
from html import escape as e
from decision_map import read

def weekly_digest():
    pubs={r['id']:r for r in read('research-publications.csv')}
    findings={r['publication_id']:r for r in read('research-findings.csv')}
    angles={
        'acts':('协作边界','通信图改变调用与依赖，属于排程器的上游输入。先判断调用预算是否值得投入，再决定谁先执行。'),
        'dual-control-mas':('预算验收','同预算单 Agent 是必要对照。增加协作者前，先排除工具信息不对等和预算口径偏差。'),
        'vllm-032':('入口分派','API worker 负载均衡属于前端连接层；需要与模型副本排队分别计时，避免扩错层。'),
        'ucm-081':('缓存前提','缓存命中必须可正确恢复；搬运失败与实例退出需要回退信号，才能用于亲和路由。')}
    cards=''.join(f'''<a class="week-card" href="#publication-{r['publication_id']}"><span>{e(r['category'])} · {pubs[r['publication_id']]['published']} · {angles[r['publication_id']][0]}</span><h4>{e(findings[r['publication_id']]['headline'])}</h4><p>{angles[r['publication_id']][1]}</p><small>{e(pubs[r['publication_id']]['status'])}</small><b>查看机制、结果与研究问题 →</b></a>''' for r in read('weekly-selection.csv'))
    checks=''.join(f'''<tr><th scope="row"><a href="{e(r['url'])}" target="_blank" rel="noopener noreferrer">{e(r['source'])} ↗</a></th><td>{e(r['result'])}</td><td>{e(r['boundary'])}</td></tr>''' for r in read('weekly-source-checks.csv'))
    return f'''<div id="updates-week" class="weekly-digest"><p class="eyebrow">近一周 / 2026-10-17—23</p><h3>4 项变化：协作先核预算，路由先辨层次</h3><p>2 篇预印本回答协作是否值得、调用如何产生；2 项正式版本回答入口怎样分流、缓存是否可靠。它们分别改变上游工作量和下游可用条件，均不能直接证明云核端到端性能提升。</p><div class="week-grid">{cards}</div><details class="arch-evidence"><summary>查看本周覆盖范围与未纳入原因</summary><div class="table-scroll"><table><thead><tr><th>核查入口</th><th>本轮结果 · 10月23日</th><th>覆盖限制</th></tr></thead><tbody>{checks}</tbody></table></div><p>本周两篇论文保持摘要级核验；版本条目核对官方发布说明。下方事实记录保留各自核验范围，历史资料另行折叠。</p></details></div>'''

def weekly_decisions():
    return '''<div class="weekly-analysis"><p class="eyebrow">本周对研究优先级的影响 / 分析判断，待验证</p><h3>先确认可用条件，再决定哪项研究值得投入</h3><div class="arch-three">
<article><h4>01 缓存路由：先验证正确性</h4><p>若采用UCM与昇腾缓存搬运，先回归版本适配、恢复一致性与实例退出。缓存无效时必须退出亲和；正确性未通过，暂停性能比较。</p><a href="#publication-ucm-081">依据：UCM 0.8.1 →</a></article>
<article><h4>02 资源预算：先验证协作价值</h4><p>增加Agent前，固定模型、任务与预算建立单Agent基线。ACTS给出角色感知通信的候选机制；同预算对照研究提示收益受工具信息和协作实现影响。先验证协作增量，再调并发。</p><a href="#publication-acts">ACTS →</a> · <a href="#publication-dual-control-mas">同预算对照 →</a></article>
<article><h4>03 执行映射：先辨拥塞层</h4><p>为API入口与模型队列分别计时。若瓶颈在API worker，先验证入口负载均衡；模型副本路由研究仍需独立基线，不沿用前端测试收益。</p><a href="#publication-vllm-032">依据：vLLM 0.32.0 →</a></article>
</div><p class="arch-note">按问题选择入口：采用缓存搬运时先查正确性；扩展多Agent时先做同预算对照；遇到吞吐瓶颈时先定位拥塞层。三项面向不同前提，不构成统一投入顺序。</p></div>'''
