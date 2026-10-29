"""Build the portal and a standalone, searchable source directory."""
from pathlib import Path
import csv
import html
import io
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / 'data/compression/manifest.json').exists():
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/materialize_compression.py')], cwd=ROOT, check=True)
subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'build.py')], cwd=ROOT, check=True)
def rows(name):
    pack = json.loads((ROOT / 'data/directory' / (name + '.json')).read_text(encoding='utf-8'))
    return [x['row'] for x in pack['rows'] if not x.get('deleted')]

families = rows('ic_source_families')
channels = {x['channel_id']: x for x in rows('ic_channels')}
sources = {x['source_id']: x for x in rows('cloud_core_sources')}
members = rows('ic_channel_families')
scopes = {x['family_id']: x['ecosystem_id'] for x in rows('ic_industry_source_scopes')}
labels = {'academic': '学术界', 'industry': '产业界', 'hotspot': '热点资讯'}
matrix = [['分类', '生态', '信息源', '定位与选择理由', '采集入口', '链接', '优先级', '启用']]
body = []
for family in sorted(families, key=lambda x: (x['ui_group'], x['title_zh'])):
    links = []
    for member in sorted([m for m in members if m['family_id'] == family['family_id']], key=lambda m: m.get('position', 0)):
        channel = channels[member['channel_id']]
        source = sources[channel['source_id']]
        url = source['canonical_url']
        assert url.startswith(('https://', 'http://'))
        title = channel['title_zh']
        links.append('<a target="_blank" rel="noopener noreferrer" href="' + html.escape(url, quote=True) + '">' + html.escape(title) + '</a>')
        matrix.append([labels.get(family['ui_group'], family['ui_group']), scopes.get(family['family_id'], ''), family['title_zh'], family.get('summary_zh', ''), title, url, channel.get('priority', ''), str(channel.get('enabled', ''))])
    body.append('<tr><td>' + html.escape(labels.get(family['ui_group'], family['ui_group'])) + '</td><td><strong>' + html.escape(family['title_zh']) + '</strong></td><td>' + html.escape(family.get('summary_zh', '')) + '</td><td>' + '<br>'.join(links) + '</td></tr>')
out = ROOT / 'dist'
with (out / 'sources.csv').open('w', encoding='utf-8-sig', newline='') as stream:
    csv.writer(stream).writerows(matrix)
page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AI Infra 信息源表格</title><style>body{font:16px/1.7 system-ui;margin:30px auto;padding:0 20px;max-width:1400px;color:#173043;background:#f5f8fa}a{color:#087d79}input{padding:12px;width:min(90%,600px);margin:18px 0;border:1px solid #bdd0d8;border-radius:8px}table{border-collapse:collapse;background:white;width:100%}th,td{padding:16px;text-align:left;border-bottom:1px solid #dfe7eb;vertical-align:top}th{background:#e5f3f2}td:nth-child(3){width:40%}.scroll{overflow:auto}h1{margin-bottom:4px}</style><a href="index.html">← CCN 首页</a><h1>AI Infra 信息源</h1><p>同一信息源合并展示，旗下采集入口保留。目录快照不代表所有内容已核验。</p>'''
page += f'<p>{len(families)} 个信息源主体 · {len(channels)} 个采集入口 · <a href="sources.csv" download>下载完整 CSV 表格</a></p>'
page += '<input id="q" aria-label="搜索信息源" placeholder="搜索名称、分类或研究方向"><div class="scroll"><table><thead><tr><th>分类</th><th>信息源</th><th>定位与选择理由</th><th>入口链接</th></tr></thead><tbody>' + ''.join(body) + '</tbody></table></div><script>document.getElementById("q").addEventListener("input",e=>{const q=e.target.value.trim().toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))})</script></html>'
(out / 'sources.html').write_text(page, encoding='utf-8')
if (out / 'ai-infra').exists():
    local_page=page.replace('href="index.html"','href="compression.html"')
    (out / 'ai-infra/compression-sources.html').write_text(local_page,encoding='utf-8')
    (out / 'ai-infra/sources.csv').write_bytes((out/'sources.csv').read_bytes())
print(f'Built portal and source directory: {len(families)} families, {len(channels)} channels')
if (ROOT / 'data/compression/manifest.json').exists():
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'compression_migration_preview.py')], cwd=ROOT, check=True)
if (ROOT / 'original-reader/SOURCE-MANIFEST.json').exists():
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/sync_reader_bootstrap.py')], cwd=ROOT, check=True)
    subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/build_original_reader.py')], cwd=ROOT, check=True)

# Agent report shares this repository; existing public navigation stays unchanged.
subprocess.run([sys.executable, '-X', 'utf8', str(ROOT / 'scripts/build_agent_report.py')], cwd=ROOT, check=True)
