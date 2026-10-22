"""Render a local five-section migration preview from the canonical corpus."""
from pathlib import Path
from html import escape as e
import json
import re
import shutil
from compression_store import ROOT, DATA, rows, manifest, content_version

def build():
    out=ROOT/'dist/ai-infra/compression-migration'
    out.mkdir(parents=True,exist_ok=True)
    sources={r['source_id']:r for r in rows('cloud_core_sources')}
    topics={r['compression_topic_id']:r for r in rows('ic_compression_topics')}
    summaries={r['summary_id']:r for r in rows('ic_paper_summaries')}
    events={r['evidence_id']:r for r in rows('ic_evidence_items')}
    def text(value): return ''.join('<p>'+e(p)+'</p>' for p in str(value or '').splitlines() if p.strip())
    def field(label,value): return '<div class="field"><b>'+label+'</b>'+text(value)+'</div>' if value else ''
    def source(identifier):
        r=sources[identifier]; url=r['canonical_url']
        assert url.startswith(('https://','http://'))
        return '<a target="_blank" rel="noopener noreferrer" href="'+e(url,quote=True)+'">'+e(r['title'])+' ↗</a>'
    def topic_links(ids): return '<div class="tags">'+''.join('<a href="../topic-'+e(i,quote=True)+'.html">'+e(topics[i]['title_zh'])+'</a>' for i in sorted(set(ids)) if i in topics)+'</div>'
    nav=[('信息来源','../compression-sources.html'),('技术地图','../compression.html'),('本期动态','updates.html'),('洞察报告','insights.html'),('洞察归档','archive.html')]
    css='''body{margin:0;background:#f4f7f9;color:#172f43;font:16px/1.8 system-ui}header{background:#fff;border-bottom:1px solid #d7e3e9;padding:16px max(24px,calc((100% - 1160px)/2))}header a{margin-right:24px}main{max-width:1100px;padding:28px 24px 80px;margin:auto}a{color:#087f80;text-decoration:none}a:hover{text-decoration:underline}h1{font-size:32px;line-height:1.3}h2{margin-top:40px}article,.notice{background:white;padding:24px;margin:18px 0;border:1px solid #dce6ec;border-radius:14px}h3{margin-top:4px}.meta{font-size:14px;color:#62788b}.field{margin:14px 0}.field p{margin:5px 0}.tags{display:flex;gap:8px;flex-wrap:wrap}.tags a{font-size:14px;background:#e8f4f3;padding:3px 10px;border-radius:5px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}.grid img{width:100%;height:auto}object{width:100%;height:78vh;border:1px solid #dce6ec}ul{padding-left:20px}.review{border-left:4px solid #0d8f90}.badge{background:#edf3f8;padding:3px 9px;border-radius:4px;font-size:13px}footer{color:#677f91;margin-top:30px} @media(max-width:600px){main{padding:16px}header a{display:inline-block;margin-right:14px}article{padding:17px}h1{font-size:27px}}'''
    (out/'preview.css').write_text(css,encoding='utf-8')
    def page(filename,title,body):
        content='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="compression-version" content="'+content_version()+'"><title>'+e(title)+' · 推理压缩迁移预览</title><link rel="stylesheet" href="preview.css"></head><body><header><b>推理压缩</b> · 本地迁移预览<br>'+''.join('<a href="'+url+'">'+label+'</a>' for label,url in nav)+'</header><main><h1>'+e(title)+'</h1>'+body+'<footer>内容版本 '+content_version()+' · 保留原始审阅状态，迁移不代表新增核验。</footer></main></body></html>'
        (out/filename).write_text(content,encoding='utf-8')
    counts=manifest()
    overview='<div class="notice">'+str(len(counts['tables']))+' 张表、'+str(sum(t['exported_rows'] for t in counts['tables']))+' 条记录已迁入。页面由本地文件生成，阅读时不请求 TableGit。历史回溯候选保留在数据层；公开归档预览从2026年10月开始。</div><div class="grid">'
    for title,url in nav: overview+='<article><h3><a href="'+url+'">'+title+' →</a></h3></article>'
    overview+='</div>'
    page('index.html','推理压缩 · 内容迁移总览',overview)
    # Reviewed summaries retain publication time, review time and observed version.
    bindings=rows('ic_paper_summary_events')
    body='<div class="notice">本期动态记录论文、产业与热点事实；原文未给出的指标不补填。旧论文在本月复核时，分别保留发表时间与复核时间。</div><p><a href="#academic">学术进展</a> · <a href="#industry">产业进展</a> · <a href="#signals">热点资讯</a> · <a href="#candidates">候选资料</a></p><h2 id="academic">学术进展</h2>'
    seen=set()
    for binding in sorted(bindings,key=lambda x:(x['period_id'],x['summary_id']),reverse=True):
        if binding['period_id']<'2026-10' or binding['summary_id'] in seen: continue
        seen.add(binding['summary_id']); s=summaries[binding['summary_id']]; event=events[binding['evidence_id']]
        topic_ids=[r['compression_topic_id'] for r in rows('ic_compression_topic_events') if r['evidence_id']==binding['evidence_id']]
        body+='<article class="review" id="summary-'+e(s['summary_id'],quote=True)+'"><p class="meta">发表／事件日期 '+e(event['event_date'])+' · '+e(s['observed_version'])+' · 复核 '+e(s.get('reviewed_at',''))+' · '+e(s['review_status'])+'</p><h3>'+source(s['source_id'])+'</h3>'+topic_links(topic_ids)
        for label,key in [('一句话总结','one_sentence_zh'),('背景介绍','background_zh'),('技术和创新点','innovation_zh'),('效果总结','results_zh')]:body+=field(label,s.get(key))
        keywords=[r.get('keyword_zh',r.get('keyword','')) for r in rows('ic_paper_summary_keywords') if r.get('summary_id')==s['summary_id']]
        body+=field('关键词',' · '.join(x for x in keywords if x))+field('原文定位',s.get('evidence_locator'))+'</article>'
    body+='<h2 id="industry">产业进展</h2>'
    for update in rows('ic_industry_updates'):
        body+='<article id="industry-'+e(update['update_id'],quote=True)+'"><p class="meta">'+e(update.get('version_label',''))+' · 核对 '+e(update.get('checked_at',''))+' · 发布日期 '+e(update.get('release_date') or '未确认')+'</p><h3>'+e(update['title_zh'])+'</h3>'+source(update['source_id'])+field('原始记录',update.get('summary_zh'))
        changes=[x for x in rows('ic_industry_update_changes') if x['update_id']==update['update_id']]
        for change in sorted(changes,key=lambda x:x['position']):
            ids=[r['compression_topic_id'] for r in rows('ic_industry_change_topics') if r['change_id']==change['change_id']]
            body+='<h4>'+e(change['title_zh'])+'</h4>'+topic_links(ids)+field('具体变化',change.get('fact_zh'))+field('适用条件',change.get('conditions_zh'))
        body+=field('配套依赖',update.get('dependencies_zh'))+field('证据边界',update.get('boundary_zh'))+'</article>'
    body+='<h2 id="signals">热点资讯</h2>'
    for signal in rows('ic_current_signals'):
        ids=[r['compression_topic_id'] for r in rows('ic_signal_topics') if r['signal_id']==signal['signal_id']]
        body+='<article><p class="meta">'+e(signal['publication_date'])+' · '+e(signal['claim_status'])+'</p><h3>'+e(signal['title_zh'])+'</h3>'+topic_links(ids)+source(signal['source_id'])+field('客观事件',signal.get('fact_zh'))+field('研究影响与分析',signal.get('relevance_zh'))+field('边界',signal.get('boundary_zh'))+'</article>'
    candidates=[r for r in rows('ic_evidence_items') if r['event_date'][:7]>='2026-10' and r['evidence_id'] not in {b['evidence_id'] for b in bindings}]
    body+='<h2 id="candidates">待审阅与其他收录资料</h2><p>以下为原始事件索引，不等同于已完成原文审阅的论文总结。</p>'
    for start in range(0,len(candidates),100):
        name='candidates-'+str(start//100+1)+'.html'
        body+='<a href="'+name+'">资料 '+str(start+1)+'–'+str(min(start+100,len(candidates)))+'</a>　'
        listing='<p>保留来源状态，不自动生成机制或效果判断。</p>'
        for item in candidates[start:start+100]:listing+='<article><p class="meta">'+e(item['event_date'])+' · '+e(item['observed_version'])+' · '+e(item['status'])+'</p>'+source(item['source_id'])+'</article>'
        listing+='<a href="updates.html#candidates">← 本期动态</a>'
        page(name,'候选资料索引',listing)
    page('updates.html','本期动态',body)
    # Assets are addressed by their verified content hash, not by the original host.
    assets=json.loads((DATA/'assets.json').read_text(encoding='utf-8'))['assets'] if (DATA/'assets.json').exists() else []
    asset_map={r['asset_id']:r for r in assets}
    asset_out=out/'assets';asset_out.mkdir(exist_ok=True)
    def local_asset(asset):
        a=asset_map.get(asset['asset_id'])
        if not a or a['status']!='verified':return None
        p=ROOT/a['local_path'];dest=asset_out/p.name
        if not dest.exists() or dest.stat().st_size!=p.stat().st_size:shutil.copy2(p,dest)
        return 'assets/'+p.name
    reports=rows('ic_insight_reports')
    def report_card(report):
        return '<article><p class="meta">'+e(report['period_id'])+' · '+e(report['status'])+' · '+str(report['page_count'])+' 页</p><h3><a href="report-'+e(report['report_id'],quote=True)+'.html">'+e(report['title_zh'])+'</a></h3>'+text(report.get('summary_zh'))+'</article>'
    for report in reports:
        report_assets=[a for a in rows('ic_insight_report_assets') if a['report_id']==report['report_id']]
        rb=text(report.get('summary_zh'))
        for asset in report_assets:
            if asset['format'] in ('pdf','pptx'):
                path=local_asset(asset)
                rb+='<p>'+('<a href="'+path+'" download>下载 '+e(asset['format'].upper())+'</a>' if path else '附件尚未迁入：'+e(asset['format']))+'</p>'
                if path and asset['format']=='pdf':rb+='<object data="'+path+'" type="application/pdf"><a href="'+path+'">打开 PDF</a></object>'
        rb+='<h2>逐页阅读</h2><div class="grid">'
        for asset in sorted(report_assets,key=lambda a:a['format']):
            if not asset['format'].startswith('slide-'):continue
            path=local_asset(asset)
            if path:rb+='<a href="'+path+'" target="_blank"><img loading="lazy" src="'+path+'" alt="'+e(asset['format'])+'"><span>'+e(asset['format'])+' · 打开原图</span></a>'
        rb+='</div><h2>报告选题</h2>'
        for paper in sorted([x for x in rows('ic_insight_report_papers') if x['report_id']==report['report_id']],key=lambda x:x['position']):
            rb+='<article>'+source(paper['source_id'])+field('选择理由',paper.get('reason_zh'))+'<p class="meta">'+e(paper.get('selection_status',''))+' · '+e(paper.get('observed_version',''))+'</p></article>'
        page('report-'+report['report_id']+'.html',report['title_zh'],rb)
    body=''.join(report_card(r) for r in reports if r['status']=='published')+'<h2>路线取舍与业务验证</h2>'
    for story in sorted(rows('ic_monthly_route_insights'),key=lambda x:x['position']):
        refs=[x for x in rows('ic_monthly_route_evidence') if x['story_id']==story['story_id']]
        body+='<article><span class="badge">研究分析</span><h3>'+e(story['title_zh'])+'</h3>'+topic_links([r['compression_topic_id'] for r in refs])
        for label,key in [('研究问题','question_zh'),('背景','context_zh'),('综合判断','viewpoint_zh'),('技术比较','synthesis_zh'),('业务启示','implication_zh'),('证据边界','boundary_zh')]:body+=field(label,story.get(key))
        for assessment in [a for a in rows('ic_ascend_route_assessments') if a['story_id']==story['story_id']]:
            body+='<h4>'+e(assessment['title_zh'])+'</h4>'+field('判断依据',assessment.get('rationale_zh'))+field('建议验证',assessment.get('recommendation_zh'))
            for probe in [p for p in rows('ic_ascend_validation_probes') if p['assessment_id']==assessment['assessment_id']]:
                body+='<p class="meta">验证方案 · 尚未实测</p>'
                for label,key in [('技术假设','hypothesis_zh'),('实验设计','design_zh'),('测量指标','metrics_zh'),('继续或停止条件','decision_rule_zh')]:body+=field(label,probe.get(key))
        body+='<h4>原始依据</h4>'+''.join('<p>'+source(sid)+'</p>' for sid in sorted({r['source_id'] for r in refs}))+'</article>'
    page('insights.html','洞察报告',body)
    page('archive.html','洞察归档','<p>从2026年10月开始。保留版本状态，旧版不替代当前报告。</p>'+''.join(report_card(r) for r in reports if r['period_id']>='2026-10'))
    print('Built local migration preview:',out)

if __name__=='__main__':build()
