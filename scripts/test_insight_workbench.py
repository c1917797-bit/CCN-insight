"""Behavior checks for reusable scaffolding and evidence-bound lesson transitions."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import insight_topic as topic
import insight_learning as learning

class WorkbenchTests(unittest.TestCase):
    def test_evidence_counterexamples(self):
        topic.self_test()

    def test_new_domain_and_safe_render(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with patch.object(topic,'ROOT',root),patch.object(sys,'argv',['topic','new','--domain','wen','--slug','service-resilience','--title','极稳：服务韧性','--question','故障下如何保持服务能力？']):
                topic.main()
            source=root/'content/insights/wen/service-resilience/topic.json'
            value=json.loads(source.read_text(encoding='utf-8'))
            self.assertEqual(topic.validate_topic(value),[])
            self.assertEqual(value['sources'],[]);self.assertEqual(value['claims'],[])
            value['title']='<script>alert(1)</script>'
            self.assertNotIn('<script>',topic.render(value))
            with patch.object(topic,'ROOT',root),patch.object(sys,'argv',['topic','new','--domain','wen','--slug','service-resilience','--title','duplicate','--question','duplicate']):
                with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):topic.main()

    def test_candidate_cannot_establish_fact(self):
        value=json.loads(topic.TEMPLATE.read_text(encoding='utf-8'))
        value['sources']=[{'id':'s','url':'https://example.org/paper','title':'Candidate','version':'v1','review_depth':'candidate'}]
        value['claims']=[{'id':'c','kind':'fact','text':'unverified effect','source_ids':['s'],'metrics':[]}]
        self.assertTrue(any('candidate-only' in e for e in topic.validate_topic(value)))

    def test_empty_draft_cannot_claim_reviewed(self):
        value=json.loads(topic.TEMPLATE.read_text(encoding='utf-8'));value['status']='reviewed'
        self.assertTrue(topic.validate_topic(value))

    def test_verification_is_not_approval_and_stale_receipt_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);lessons=root/'.agents/experience';receipts=root/'.agents/evals/receipts';lessons.mkdir(parents=True)
            (root/'evidence.txt').write_text('observed evidence',encoding='utf-8')
            (root/'skill.md').write_text('bounded rule',encoding='utf-8')
            (root/'gate.py').write_text('print("PASS: isolated fixture gate")',encoding='utf-8')
            value={'id':'fixture','status':'proposed','trigger':'test','changed_action':'test action','scope':'test only','counterexample':'test boundary','evidence':['evidence.txt'],'destination':'skill.md','checks':['fixture-check']}
            source=lessons/'fixture.json';source.write_text(json.dumps(value),encoding='utf-8')
            with patch.object(learning,'ROOT',root),patch.object(learning,'LESSONS',lessons),patch.object(learning,'RECEIPTS',receipts),patch.object(learning,'CHECKS',{'fixture-check':[sys.executable,'gate.py']}):
                with patch.object(sys,'argv',['learning','verify','fixture']):learning.main()
                self.assertEqual(json.loads(source.read_text())['status'],'proposed')
                with self.assertRaises(ValueError):learning.validate_lesson({**value,'status':'accepted'})
                learning.receipt_valid(value)
                changed={**value,'changed_action':'different action'}
                with self.assertRaises(ValueError):learning.receipt_valid(changed)
                # An isolated fixture can accept a fully bound decision; real lessons remain untouched.
                decision={'lesson_id':'fixture','lesson_sha256':learning.content_hash(value),'outcome':'accepted','reviewed_by':'test-fixture','reason':'state-machine test','authorization_reference':'isolated unit test only'}
                decision_path=root/'decision.json';decision_path.write_text(json.dumps(decision),encoding='utf-8')
                with patch.object(sys,'argv',['learning','decide','fixture','--decision',str(decision_path)]):learning.main()
                self.assertEqual(json.loads(source.read_text())['status'],'accepted')
                (root/'evidence.txt').write_text('changed evidence',encoding='utf-8')
                with self.assertRaises(ValueError):learning.receipt_valid(value)

if __name__=='__main__':unittest.main()
