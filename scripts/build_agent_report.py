"""Build the Agent module from its sole editable source; do not change portal navigation."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research/agent-scheduling'
BASE = Path('business_insight/cloud_core/agent_orchestration')
for script in ('build_draft.py', 'export_isolated_preview.py'):
    subprocess.run([sys.executable, '-X', 'utf8', str(SOURCE/script)], cwd=ROOT, check=True)
out = SOURCE / 'outputs/isolated-preview'
dest = ROOT / 'dist' / BASE
dest.mkdir(parents=True, exist_ok=True)
validation = json.loads((SOURCE/'outputs/isolated-preview-validation.json').read_text(encoding='utf-8'))
prefix = BASE.as_posix() + '/'
files = {name: digest for name, digest in validation['allowlist'].items() if name.startswith(prefix)}
assert files, 'Agent preview allowlist is empty'
for name, digest in sorted(files.items()):
    # Copy the current manifest recursively, including original evidence images.
    # Old generated hashes and unallowlisted PDFs are not publishing inputs.
    source = out/name
    relative = Path(name).relative_to(BASE)
    target = dest/relative
    assert source.resolve().is_relative_to(out.resolve()), name
    assert target.resolve().is_relative_to(dest.resolve()), name
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest, name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == digest, name
print('Agent report ready: dist/' + BASE.as_posix())
print('Standalone publishing artifact: research/agent-scheduling/outputs/isolated-preview')
