"""Fail when the Chinese map gains prose without a maintained English translation."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CJK = re.compile(r'[\u3400-\u9fff]')


class MapText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.texts = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        parent = self.stack[-1][1:] if self.stack else (False, False)
        scope = attrs.get('id') in ('map', 'report-top') or tag == 'footer' or bool(
            set(attrs.get('class', '').split()) & {'rail', 'reading-flow', 'skip-link'})
        active = scope or parent[0]
        control = 'data-language-control' in attrs or parent[1]
        if active and not control:
            self.texts.update(attrs[k].strip() for k in ('aria-label', 'title', 'alt')
                              if k in attrs and CJK.search(attrs[k]))
        if tag not in ('meta', 'link', 'img', 'input', 'br', 'hr', 'source', 'wbr'):
            self.stack.append((tag, active, control))

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, text):
        if self.stack and self.stack[-1][1] and not self.stack[-1][2] and CJK.search(text):
            self.texts.add(text.strip())


def main():
    source = ROOT / 'research/agent-scheduling'
    entries = json.loads((source/'map-en.json').read_text(encoding='utf-8'))
    assert all(k.strip() and v.strip() and not CJK.search(v) for k, v in entries.items())
    page = MapText()
    page.feed((source/'outputs/isolated-preview/business_insight/cloud_core/agent_orchestration/index.html').read_text(encoding='utf-8'))
    missing = page.texts - entries.keys()
    assert not missing, f'Map English translations missing: {sorted(missing)}'
    print(f'PASS: {len(page.texts)} map/shell Chinese text and accessibility strings have authored English translations; {len(entries)} total entries including runtime messages.')


if __name__ == '__main__':
    main()
