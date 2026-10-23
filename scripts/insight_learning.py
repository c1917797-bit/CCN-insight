"""Evidence-bound lesson lifecycle. Never edits skills, publishes, or pushes Git."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
LESSONS=ROOT/'.agents/experience'
RECEIPTS=ROOT/'.agents/evals/receipts'
CHECKS={
 'skill-tree':[sys.executable,'-X','utf8','scripts/validate_insight_skills.py'],
 'evidence-contract':[sys.executable,'-X','utf8','scripts/insight_topic.py','self-test'],
 'citation-boundaries':[sys.executable,'-X','utf8','scripts/verify_expert_topics.py'],
 'compression-content':[sys.executable,'-X','utf8','scripts/verify_compression.py'],
}

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def content_hash(lesson):
    value={k:v for k,v in lesson.items() if k not in {'status','decision'}}
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def local_path(name):
    path=(ROOT/name).resolve()
    if ROOT.resolve() not in path.parents:raise ValueError('Evidence/destination must be within repository')
    return path
def validate_lesson(lesson):
    for k in ['id','trigger','changed_action','scope','counterexample','evidence','destination','checks','status']:
        if not lesson.get(k):raise ValueError('Lesson lacks '+k)
    if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',lesson['id']):raise ValueError('Invalid lesson ID')
    if lesson['status'] not in {'proposed','accepted','rejected','superseded'}:raise ValueError('Invalid lesson state')
    if not set(lesson['checks'])<=set(CHECKS):raise ValueError('Check is not allowlisted')
    for name in lesson['evidence']+[lesson['destination']]:
        if not local_path(name).is_file():raise ValueError('Missing local evidence/destination: '+name)
    if lesson['status']=='accepted':
        decision=lesson.get('decision',{})
        if any(not decision.get(k) for k in ['lesson_id','lesson_sha256','outcome','reviewed_by','reason','authorization_reference']):raise ValueError('Accepted lesson lacks maintainer decision metadata')
        if decision['outcome']!='accepted' or decision['lesson_id']!=lesson['id'] or decision['lesson_sha256']!=content_hash(lesson):raise ValueError('Accepted decision does not match current lesson')
    return lesson
def receipt_valid(lesson):
    receipt=read(RECEIPTS/(lesson['id']+'.json'))
    if receipt['lesson_sha256']!=content_hash(lesson) or not receipt.get('passed'):raise ValueError('Receipt failed or stale')
    if set(receipt['checks'])!=set(lesson['checks']):raise ValueError('Receipt check list changed')
    if set(receipt['files'])!=set(lesson['evidence']+[lesson['destination']]):raise ValueError('Receipt evidence file list changed')
    for name,expected in receipt['files'].items():
        if digest(local_path(name))!=expected:raise ValueError('Receipt evidence/destination changed: '+name)
    for name,expected in receipt.get('check_scripts',{}).items():
        if digest(local_path(name))!=expected:raise ValueError('Check implementation changed: '+name)
    for name,expected in receipt.get('logs',{}).items():
        if digest(local_path(name))!=expected:raise ValueError('Check log changed: '+name)
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);subs=p.add_subparsers(dest='command',required=True)
    subs.add_parser('validate')
    for cmd in ['verify','decide']:
        sub=subs.add_parser(cmd);sub.add_argument('lesson_id')
        if cmd=='decide':sub.add_argument('--decision',type=Path,required=True)
    a=p.parse_args()
    try:
        if a.command=='validate':
            found=list(LESSONS.glob('*.json'));seen=set()
            for path in found:
                lesson=validate_lesson(read(path))
                if lesson['id'] in seen or path.stem!=lesson['id']:raise ValueError('Lesson identity mismatch')
                seen.add(lesson['id'])
                if lesson['status']=='accepted':receipt_valid(lesson)
            print('PASS:',len(found),'bounded lessons; proposed lessons are not adopted rules');return
        if not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',a.lesson_id):raise ValueError('Invalid lesson ID')
        path=LESSONS/(a.lesson_id+'.json');lesson=validate_lesson(read(path))
        if a.command=='verify':
            if lesson['status']!='proposed':raise ValueError('Reopen as proposed before changing an adopted lesson')
            RECEIPTS.mkdir(parents=True,exist_ok=True)
            files={name:digest(local_path(name)) for name in lesson['evidence']+[lesson['destination']]}
            results={};logs={};scripts={}
            for check in lesson['checks']:
                command=CHECKS[check];run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=120)
                log=RECEIPTS/(lesson['id']+'--'+check+'.txt');log.write_text(run.stdout+run.stderr,encoding='utf-8')
                logs[log.relative_to(ROOT).as_posix()]=digest(log);scripts[command[-1] if check!='evidence-contract' else command[-2]]=digest(ROOT/(command[-1] if check!='evidence-contract' else command[-2]))
                results[check]=run.returncode==0
            # Freeze after checks too: a check must not mutate the content it certifies.
            if any(digest(local_path(name))!=value for name,value in files.items()):raise ValueError('Checked files changed during verification')
            receipt={'lesson_id':lesson['id'],'lesson_sha256':content_hash(lesson),'checked_at':datetime.now(timezone.utc).isoformat(),'passed':all(results.values()),'checks':results,'files':files,'check_scripts':scripts,'logs':logs}
            (RECEIPTS/(lesson['id']+'.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print(('PASS' if receipt['passed'] else 'FAIL')+': verification recorded; status remains proposed')
            if not receipt['passed']:sys.exit(1)
            return
        if lesson['status']!='proposed':raise ValueError('Only proposed lessons accept a new decision')
        decision=read(a.decision)
        for key in ['lesson_id','lesson_sha256','outcome','reviewed_by','reason','authorization_reference']:
            if not decision.get(key):raise ValueError('Decision missing '+key)
        if decision['lesson_id']!=lesson['id'] or decision['lesson_sha256']!=content_hash(lesson):raise ValueError('Decision refers to different lesson content')
        if decision['outcome'] not in {'accepted','rejected'}:raise ValueError('Invalid decision')
        if decision['outcome']=='accepted':receipt_valid(lesson)
        lesson['status']=decision['outcome'];lesson['decision']=decision
        path.write_text(json.dumps(lesson,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Decision recorded. No skill, Git or deployment mutation performed.')
    except (ValueError,KeyError,FileNotFoundError,subprocess.TimeoutExpired) as error:p.error(str(error))

if __name__=='__main__':main()
