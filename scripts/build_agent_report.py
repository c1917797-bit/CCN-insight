"""Build the Agent module from its sole editable source; do not change portal navigation."""
from pathlib import Path
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
for source in (out/BASE).iterdir():
    if source.is_file():
        shutil.copy2(source, dest/source.name)
print('Agent report ready: dist/' + BASE.as_posix())
print('Standalone publishing artifact: research/agent-scheduling/outputs/isolated-preview')
