"""Copy report assets named by TableGit; verify exact content hashes and sizes."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import Request, urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT, rows, manifest

DEST = ROOT / 'data/compression/assets'
DEST.mkdir(parents=True, exist_ok=True)
ASSETS = rows('ic_insight_report_assets')

def fetch(asset):
    sha = asset['content_sha256']
    suffix = Path(asset['public_path']).suffix
    target = DEST / (sha + suffix)
    entry = dict(asset_id=asset['asset_id'], report_id=asset['report_id'], source_path=asset['public_path'], sha256=sha, expected_bytes=asset['byte_count'], local_path=target.relative_to(ROOT).as_posix())
    try:
        data = target.read_bytes() if target.exists() else None
        if data is None:
            assert asset['public_path'].startswith('/business_insight/cloud_core/reports/')
            request = Request('https://c1b3ie6ayp-sworks-lrigit-tpc.ru.yxsbase.win' + asset['public_path'], headers={'User-Agent': 'CCN-insight-migration/1.0'})
            with urlopen(request, timeout=45) as response:
                data = response.read()
        assert len(data) == asset['byte_count'], 'byte_count mismatch'
        assert hashlib.sha256(data).hexdigest() == sha, 'sha256 mismatch'
        target.write_bytes(data)
        entry['status'] = 'verified'
    except Exception as error:
        entry['status'] = 'failed'
        entry['error'] = str(error)
    return entry

results = []
with ThreadPoolExecutor(max_workers=6) as pool:
    futures = [pool.submit(fetch, asset) for asset in ASSETS]
    for future in as_completed(futures):
        results.append(future.result())
index = {'source_revision': manifest()['revision'], 'assets': sorted(results, key=lambda r: r['asset_id'])}
(ROOT / 'data/compression/assets.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'verified': sum(x['status']=='verified' for x in results), 'failed': sum(x['status']!='verified' for x in results), 'errors': [x for x in results if x['status']!='verified'][:3]}))
if any(x['status'] != 'verified' for x in results):
    raise SystemExit(1)
