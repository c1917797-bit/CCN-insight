"""Build zero-fact original-site entry aliases, separate from CCN's real reader."""
from pathlib import Path
import hashlib,json,sys
from html import escape
ROOT=Path(__file__).resolve().parents[1]


def build(out, shell_version='lri-shell-v18-cloud-report-navigation', style_version='lri-content-contract-v13-style-audit'):
    config=json.loads((ROOT/'deployment/compression-entry.json').read_text(encoding='utf-8'))
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    js="""/* Canonical reader entry only. No research data or TableGit writes. */
(() => {
 'use strict';
 const config=CONFIG, file=location.pathname.split('/').pop()||'index.html';
 if(!config.entrypoints.includes(file))return;
 const route=config.routes?.[file]||{},target=new URL(route.file||file,config.canonical_reader),query=new URLSearchParams(location.search);
 for(const key of config.query_allowlist)if(query.has(key))target.searchParams.set(key,query.get(key));
 target.hash=location.hash||route.default_hash||(file==='index.html'?'#view-topics':'');
 const link=document.getElementById('canonical-reader-link');if(link)link.href=target.href;
 if(location.origin!==target.origin||location.pathname!==target.pathname)location.replace(target.href);
})();
""".replace('CONFIG',json.dumps(config,ensure_ascii=False,separators=(',',':')))
    digest=hashlib.sha256(js.encode()).hexdigest()[:16]
    (out/'canonical-reader.js').write_bytes(js.encode())
    for name in config['entrypoints']:
        route=config.get('routes',{}).get(name,{})
        target=config['canonical_reader']+route.get('file',name)+route.get('default_hash','')
        html='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>推理压缩洞察 · 统一阅读入口</title><meta name="lri-page-translation" content="ui"><meta name="lri-shell-version" content="SHELL">
<link rel="canonical" href="TARGET"><link rel="stylesheet" href="../../assets/insight-executive.css?v=STYLE"><script type="module" src="../../assets/lri-shell.js?v=SHELL"></script>
</head><body data-lri-shell="auto"><main><section class="hero"><h1>推理压缩洞察 / Inference Compression</h1><p>正在打开统一阅读页。两站入口使用同一份研究内容与阅读器。</p><p>Opening the shared reader. Both entrypoints use the same maintained research content.</p><p><a id="canonical-reader-link" href="TARGET">进入统一阅读页 / Open the shared reader →</a></p></section></main><script src="canonical-reader.js?v=DIGEST"></script></body></html>'''
        html=html.replace('SHELL',escape(shell_version,quote=True)).replace('STYLE',escape(style_version,quote=True)).replace('TARGET',escape(target,quote=True)).replace('DIGEST',digest)
        (out/name).write_bytes(html.encode())
    (out/'canonical-reader.json').write_bytes((json.dumps(config,ensure_ascii=False,indent=2)+'\n').encode())
    print(json.dumps({'output':str(out),'entrypoints':config['entrypoints'],'canonical_reader':config['canonical_reader'],'mode':'staged_not_published'},ensure_ascii=False))


if __name__=='__main__':
    build(sys.argv[1] if len(sys.argv)>1 else ROOT/'.tmp/canonical-entry')
