"""Build an allowlisted, standalone reading preview without the Works shell."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin, unquote
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).parent
BASE = 'business_insight/cloud_core/agent_orchestration/'
SOURCE = ROOT / 'site' / BASE
OUT = ROOT / 'outputs'
DEST = OUT / 'isolated-preview'

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links = set(), []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids, a['id']
            self.ids.add(a['id'])
        for key in ('href', 'src', 'poster'):
            if key in a:
                self.links.append(a[key])

def main():
    files = {}
    for path in sorted(SOURCE.glob('*.html')):
        text = path.read_text(encoding='utf-8')
        text = text.replace('云核私有草稿', '云核研究预览').replace('私有草稿 ·', '研究草稿 ·')
        text = text.replace('本地私有预览', '独立只读预览').replace('本机私有预览', '独立网址直达')
        text = text.replace('仅监听127.0.0.1。调度研究草稿，未发布到线上。', 'Agent 调度研究草稿的只读快照。持链接者可访问；不加入原站导航。')
        text = text.replace('<head>', '<head><meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer"><meta name="lri-preview-status" content="isolated-reading-snapshot">')
        files[BASE + path.name] = text
    for name in ('draft.css', 'draft.js'):
        content = (SOURCE / name).read_text(encoding='utf-8')
        files[BASE + name] = content
        stem, extension = name.split('.')
        version = hashlib.sha256((SOURCE / name).read_bytes()).hexdigest()[:12]
        files[BASE + f'{stem}.{version}.{extension}'] = content
    entry = '/' + BASE + 'index.html#coffee-task'
    files['index.html'] = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow,noarchive"><meta name="referrer" content="no-referrer"><meta http-equiv="refresh" content="0;url=' + entry + '"><title>Agent 调度研究预览</title></head><body><a href="' + entry + '">打开 Agent 调度研究预览</a></body></html>'
    files['robots.txt'] = 'User-agent: *\nDisallow: /\n'
    pages = {k: Page(v) for k, v in files.items() if k.endswith('.html')}
    link_count = 0
    for name, page in pages.items():
        for link in page.links:
            if urlsplit(link).scheme or link.startswith('//'):
                assert not link.startswith(('file:', 'javascript:')), (name, link)
                continue
            parsed = urlsplit(urljoin('https://preview.invalid/' + name, link))
            target = unquote(parsed.path).lstrip('/')
            if target.endswith('/') or not target:
                target += 'index.html'
            assert target in files, (name, target)
            if parsed.fragment:
                assert unquote(parsed.fragment) in pages[target].ids, (name, link)
            link_count += 1
    for name, text in files.items():
        assert not re.search(r'127\.0\.0\.1|C:[/\\]|PRIVATE KEY|Authorization\s*:|basic_verify\s*[:=]|password\s*[:=]', text, re.I), name
        dest = DEST / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding='utf-8')
    archive = OUT / 'agent-scheduling-isolated-preview.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name in files:
            z.write(DEST / name, name)
    report = {
        'deployment_status': 'built locally; publication tracked separately',
        'repository_id': 'c1917797-bit/CCN-insight',
        'research_pages': len(pages)-1, 'files': len(files), 'internal_links_checked': link_count,
        'archive_bytes': archive.stat().st_size,
        'content_mode': 'frozen reading snapshot, not a live TableGit data service',
        'access': 'existing public preview; access unchanged by this build',
        'allowlist': {name: hashlib.sha256(text.encode()).hexdigest() for name, text in files.items()},
    }
    (OUT / 'isolated-preview-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k != 'allowlist'}, ensure_ascii=False))

if __name__ == '__main__':
    main()
