"""Dated selection with coverage limits, linked to canonical evidence."""
from html import escape as e
from decision_map import read

def weekly_digest():
    pubs={r['id']:r for r in read('research-publications.csv')}
    findings={r['publication_id']:r for r in read('research-findings.csv')}
    cards=''.join(f'''<a class="week-card" href="#publication-{r['publication_id']}"><span>{e(r['category'])} · {pubs[r['publication_id']]['published']}</span><h4>{e(findings[r['publication_id']]['headline'])}</h4><p>{e(pubs[r['publication_id']]['status'])}</p><b>读事实与架构影响 →</b></a>''' for r in read('weekly-selection.csv'))
    checks=''.join(f'''<tr><th scope="row"><a href="{e(r['url'])}" target="_blank" rel="noopener noreferrer">{e(r['source'])} ↗</a></th><td>{e(r['result'])}</td><td>{e(r['boundary'])}</td></tr>''' for r in read('weekly-source-checks.csv'))
    return f'''<div id="updates-week" class="weekly-digest"><p class="eyebrow">近一周 / 2026-10-17—23</p><h3>本周新增4项：协作预算、入口负载与缓存正确性</h3><p>2篇预印本 + 2项正式版本。先定位关注点，再点击进入事实记录；历史资料另行折叠。论文仅核验摘要，性能结果尚无云核复现。</p><div class="week-grid">{cards}</div><details class="arch-evidence"><summary>查看本周覆盖范围与未纳入原因</summary><div class="table-scroll"><table><thead><tr><th>持续信源</th><th>本轮结果 · 10月23日核对</th><th>覆盖限制</th></tr></thead><tbody>{checks}</tbody></table></div><p>人工检索与原始页面核验，不代表所有入口已全量采集。发布时间按来源日期保留；核对时间不作为事件时间。热点资讯原文未核验完成，不纳入已确认事件。</p></details></div>'''

def weekly_decisions():
    return '''<div class="weekly-analysis"><p class="eyebrow">本周对研究优先级的影响 / 分析判断，待验证</p><h3>先守住正确性与任务预算，再区分各层拥塞</h3><div class="arch-three">
<article><h4>01 缓存路由：先验正确性</h4><p>若采用UCM与昇腾缓存搬运，先回归版本适配、恢复一致性与实例退出。缓存无效时必须退出亲和；正确性未通过，暂停性能比较。</p><a href="#publication-ucm-081">依据：UCM 0.8.1 →</a></article>
<article><h4>02 资源预算：先验协作价值</h4><p>增加Agent前，固定模型、任务与预算建立单Agent基线。ACTS提示通信结构可优化，但另一研究提醒收益依赖场景与实现；不能预设多Agent越多越好。</p><a href="#publication-acts">ACTS →</a> · <a href="#publication-dual-control-mas">同预算对照 →</a></article>
<article><h4>03 执行映射：先定位瓶颈</h4><p>为API入口与模型队列分别计时。若瓶颈在API worker，先验证入口负载均衡；模型副本路由研究仍需独立基线，不沿用前端测试收益。</p><a href="#publication-vllm-032">依据：vLLM 0.32.0 →</a></article>
</div><p class="arch-note">本周证据不支持改变三项根技术划分；应补强接口状态、预算口径和基线。ACTS作为协作层边界参照，不强行归类为资源调度算法。</p></div>'''
