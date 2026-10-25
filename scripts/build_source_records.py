"""Publish source-review provenance separately from the reader's source directory."""
from collections import defaultdict
from html import escape
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from urllib.parse import urlsplit

from compression_store import rows


def bilingual(zh, en):
    return '<span data-lang="zh">'+escape(zh)+'</span><span data-lang="en">'+escape(en or zh)+'</span>'


def link(url, label):
    if urlsplit(url).scheme not in ('https', 'http'):
        raise ValueError('Invalid source record URL')
    return '<a href="'+escape(url, quote=True)+'" target="_blank" rel="noopener noreferrer">'+label+' ↗</a>'


def build(target):
    families=rows('ic_source_families')
    channels={r['channel_id']:r for r in rows('ic_channels')}
    sources={r['source_id']:r for r in rows('cloud_core_sources')}
    papers=defaultdict(list)
    for member in rows('ic_channel_families'):
        if member['entry_kind']=='paper_reference':
            channel=channels[member['channel_id']]
            source=sources[channel['source_id']]
            papers[member['family_id']].append((channel, source))
    output=[]
    for family in sorted(families,key=lambda r:(r['ui_group'],r['title_zh'])):
        fid=family['family_id']
        reviewed=bool(family.get('reviewed_at') and family.get('review_note_zh'))
        if not reviewed and not papers[fid]:
            continue
        parts=['<article id="source-review-'+escape(fid,quote=True)+'"><header><h2>'+bilingual(family['title_zh'],family['title_en'])+'</h2>']
        if reviewed:
            parts.append('<time>'+escape(family['reviewed_at'])+'</time>')
        parts.append('</header>')
        if reviewed:
            parts.append('<p>'+bilingual(family['review_note_zh'],family.get('review_note_en'))+'</p>')
            if family.get('review_url'):
                parts.append(link(family['review_url'],bilingual('核对依据','Review source')))
        if papers[fid]:
            parts.append('<section id="source-paper-entries-'+escape(fid,quote=True)+'"><h3>'+bilingual('已登记的专题文献','Registered topic references')+'</h3><ul>')
            for channel,source in papers[fid]:
                parts.append('<li>'+link(source['canonical_url'],escape(source['title']))+'<p>'+bilingual(channel.get('focus_zh',''),channel.get('focus_en',''))+'</p></li>')
            parts.append('</ul></section>')
        parts.append('</article>')
        output.append(''.join(parts))
    page='''<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>来源核对记录 · 极智 AI Infra</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f5f7fa;color:#304357;font:15px/1.9 system-ui,-apple-system,"Segoe UI",sans-serif}main{max-width:980px;margin:0 auto;padding:30px 24px 70px}a{color:#226b7a;text-underline-offset:4px}h1{font-size:29px;margin:24px 0 8px;color:#203447}h2{font-size:18px;margin:0}h3{font-size:15px;margin:18px 0 8px}p{margin:10px 0}main>p{color:#67788a;max-width:80ch}article{background:white;padding:24px 28px;border:1px solid #e0e6ed;border-radius:10px;margin-top:20px;scroll-margin-top:24px}article header{display:flex;justify-content:space-between;align-items:baseline;gap:14px}time{font-size:12px;white-space:nowrap;color:#748598}li{margin:12px 0}li p{font-size:13px;color:#67788a;margin:4px 0}a:focus-visible{outline:2px solid #248797;outline-offset:4px}[data-lang="en"]{display:none}html[lang="en"] [data-lang="zh"]{display:none}html[lang="en"] [data-lang="en"]{display:inline}@media(max-width:600px){main{padding:20px 16px}article{padding:19px}article header{display:block}h1{font-size:25px}}:target{border-color:#7cabaf}
</style></head><body><main><a id="back" href="index.html#view-sources">'''+bilingual('← 返回信息来源','← Back to sources')+'</a><h1>'+bilingual('来源核对记录','Source review records')+'</h1><p>'+bilingual('这里保存核对范围、时间和原始依据，供需要追溯时查阅。它记录当时核对到的内容，不代表所有内容均已读取，也不代表已验证技术效果。','Review scope, dates and original evidence for traceability. These records describe what was checked at that time; they do not imply full coverage or validated technical performance.')+'</p>'+''.join(output)+'''</main><script>
const query=new URLSearchParams(location.search);if(query.get('lang')==='en'){document.documentElement.lang='en';document.title='Source review records · AI Infra';}document.getElementById('back').href='index.html'+location.search+'#view-sources';
</script></body></html>'''
    path=Path(target)/'source-records.html'
    path.write_bytes(page.encode('utf-8'))
    print('Source provenance records generated:',len(output),'families;',sum(map(len,papers.values())),'paper links')


if __name__=='__main__':
    from compression_store import ROOT
    build(ROOT/'dist/business_insight/cloud_core')
