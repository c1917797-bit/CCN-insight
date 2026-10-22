"""Check generated internal links and ensure preview has no backend calls."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
ROOT=Path(__file__).resolve().parents[1]/'dist'
FOLDER=ROOT/'ai-infra/compression-migration'
class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:self.ids.add(attrs['id'])
        for name in ('href','src','data'):
            if attrs.get(name):self.links.append(attrs[name])
errors=[]
pages=list(FOLDER.glob('*.html'))
for page in pages:
    content=page.read_text(encoding='utf-8');parser=Links();parser.feed(content)
    assert '/mcp' not in content and '/__mcpgit/' not in content
    for link in parser.links:
        target=urlsplit(link)
        if target.scheme or target.netloc:continue
        path=(page.parent/unquote(target.path)).resolve() if target.path else page
        if not path.exists():errors.append((page.name,link,'missing file'))
        elif target.fragment and path.suffix=='.html':
            other=Links();other.feed(path.read_text(encoding='utf-8'))
            if unquote(target.fragment) not in other.ids:errors.append((page.name,link,'missing anchor'))
print({'preview_pages':len(pages),'broken_links':errors})
assert not errors
