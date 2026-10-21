"""Scope checks for URL-first authority, locale coverage and source boundaries."""
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[2]/'business_insight/cloud_core'
html=(root/'archive.html').read_text(encoding='utf-8')
script=(root/'cloud-core.js').read_text(encoding='utf-8')
keys=set(re.findall(r'data-i18n-key="([^"]+)"',html))
dynamic=set(re.findall(r"(?:label|field|action)\([^\n]*?'([a-z_]+)'",script))
for lang in ['zh','en']:
    pack=json.loads((root/'data'/('ui.'+lang+'.json')).read_text(encoding='utf-8'))
    assert keys<=pack['strings'].keys(),(lang,keys-pack['strings'].keys())
assert html.count('insight-executive.css')==1
assert not re.search(r'<style|\sstyle=',html,re.I)
assert "loadTopicWorkbench('cloud_core')" in script
assert 'expectedRevision:state.revision' in script
assert 'source_kind' in script and 'limit:50' in script
assert 'innerHTML' not in script and 'contenteditable' not in html
assert 'workbench.json' not in script and 'staging-v1' not in script
assert "state.profile=null" in script and 'state.profile=snapshot.profile' in script
assert 'target_rule' in script and 'proposed' in script
from validate_compression import validate_ui
validate_ui(root.parents[1])
print(json.dumps({'ui_checks':'pass','html_locale_keys':len(keys),'public_source_page_limit':50,'authority':'TableGit'}))

