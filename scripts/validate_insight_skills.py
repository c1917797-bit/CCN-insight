"""Validate repository skills, bounded lesson links and unpublished topic contracts."""
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from insight_topic import validate_topic
from insight_learning import validate_lesson,receipt_valid

ROOT=Path(__file__).resolve().parents[1]

def main():
    registry=json.loads((ROOT/'.agents/skills.registry.json').read_text(encoding='utf-8'));ids=set()
    for skill in registry['skills']:
        sid=skill['id'];assert sid not in ids,'duplicate skill';ids.add(sid)
        path=(ROOT/skill['path']).resolve();assert ROOT in path.parents and path.is_file(),'missing skill'
        text=path.read_text(encoding='utf-8');front=re.match(r'^---\s*\n(.*?)\n---',text,re.S);assert front,'frontmatter missing'
        assert re.search(r'^name:\s*'+re.escape(sid)+r'\s*$',front[1],re.M),'skill name mismatch'
        assert re.search(r'^description:\s*\S',front[1],re.M),'description missing'
        assert not re.search(r'\bTODO\b|\[INSERT|\[FILL',text),'unfinished starter'
        assert re.fullmatch(r'\d+\.\d+\.\d+',skill['version']),'version missing'
        for ref in re.findall(r'\]\(([^)]+)\)',text):
            if '://' not in ref:assert (path.parent/ref).is_file(),'missing reference '+ref
    template=json.loads((ROOT/'.agents/skills/ccn-insight-build/assets/topic.template.json').read_text(encoding='utf-8'));assert not validate_topic(template)
    lessons=list((ROOT/'.agents/experience').glob('*.json'))
    for path in lessons:
        lesson=validate_lesson(json.loads(path.read_text(encoding='utf-8')));assert lesson['id']==path.stem
        if lesson['status']=='accepted':receipt_valid(lesson)
    topics=list((ROOT/'content/insights').glob('*/*/topic.json'))
    for path in topics:assert not validate_topic(json.loads(path.read_text(encoding='utf-8'))),str(path)
    print(f'PASS: {len(ids)} repo skills, {len(lessons)} bounded lessons, {len(topics)} draft topics; references resolve')

if __name__=='__main__':main()
