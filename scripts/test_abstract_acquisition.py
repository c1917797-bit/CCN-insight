# -*- coding: utf-8 -*-
"""Offline regression tests; fixtures are not real research coverage."""
import hashlib,json,tempfile,unittest
from unittest.mock import patch
from urllib.request import Request
from pathlib import Path
from collect_compression_abstracts import parse_feed,query
from build_live_reading_review import build
from refresh_registered_sources import Redirect,public

class AcquisitionTest(unittest.TestCase):
    def feed(self,abstract='A student compresses a teacher.',pid='2610.00001v2'):
        return f'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:o="http://a9.com/-/spec/opensearch/1.1/"><o:totalResults>1</o:totalResults><entry><id>http://arxiv.org/abs/{pid}</id><title>Test only</title><summary>{abstract}</summary><published>2026-10-01T00:00:00Z</published><updated>2026-10-02T00:00:00Z</updated></entry></feed>'''.encode()
    def test_original_abstract_retained_not_promoted(self):
        rows,total=parse_feed(self.feed());r=rows[0]
        self.assertEqual((total,r['paper_id'],r['versioned_id']),(1,'2610.00001','2610.00001v2'))
        self.assertEqual(r['abstract'],'A student compresses a teacher.')
        self.assertEqual(r['abstract_sha256'],hashlib.sha256(r['abstract'].encode()).hexdigest())
        self.assertEqual(r['model_review_status'],'not_read')
    def test_missing_abstract_and_error_identity_fail(self):
        with self.assertRaises(ValueError):parse_feed(self.feed(''))
        with self.assertRaises(ValueError):parse_feed(self.feed().replace(b'/abs/2610.00001v2',b'/api/errors'))
    def test_external_xml_entities_fail(self):
        with self.assertRaises(ValueError):parse_feed(b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///no">]><feed/>')
    def test_query_has_fixed_publication_window(self):
        q=query('2026-08-01','2026-10-29')
        self.assertIn('submittedDate:[202608010000 TO 202610292359]',q)
        self.assertIn('cat:eess.AS',q)
        self.assertNotIn('lastUpdatedDate:',q)
    def test_permanent_redirect_keeps_public_https_validation(self):
        with patch('refresh_registered_sources.public') as check:
            result=Redirect().redirect_request(Request('https://example.org/'),None,308,'Moved',{},'https://example.com/')
            self.assertEqual(result.full_url,'https://example.com/')
            self.assertEqual(result.get_method(),'GET')
            check.assert_called_once_with('https://example.com/')
        with self.assertRaises(ValueError):
            Redirect().redirect_request(Request('https://example.org/'),None,308,'Moved',{},'http://127.0.0.1/private')
    def test_model_notes_are_version_bound(self):
        with tempfile.TemporaryDirectory(prefix='ccn-review-test-') as temp:
            root=Path(temp);a=root/'a';r=root/'r';c=root/'c'
            for p in [a,r,c]:p.mkdir()
            row=parse_feed(self.feed())[0][0];row['selection_cohort']='recent'
            (a/'abstracts.jsonl').write_text(json.dumps(row)+'\n',encoding='utf-8')
            (a/'receipt.json').write_text(json.dumps({'window_start':'2026-08-01','window_end':'2026-10-29','recent_reported_total':1,'complete_for_arxiv_query':True}),encoding='utf-8')
            (c/'source-coverage.json').write_text(json.dumps({'records':[],'processed_urls':0,'registered_urls':0}),encoding='utf-8')
            note={'paper_id':row['paper_id'],'abstract_sha256':row['abstract_sha256'],'review_status':'model_abstract_reviewed','relevance':'direct','routes':['distillation']}
            note.update({k:'Test annotation only' for k in ['problem_zh','mechanism_zh','reported_results_zh','limitations_zh','value_zh','next_read_zh']})
            f=r/'test-reviews.jsonl';f.write_text(json.dumps(note)+'\n',encoding='utf-8')
            result=build(a,r,c,root/'out');self.assertEqual(result['model_abstract_read'],1);self.assertEqual(result['full_text_read'],0)
            self.assertFalse(result['all_registered_sources_complete'])
            section={'paper_id':row['paper_id'],'review_level':'section_reviewed','url':'https://arxiv.org/html/2610.00001v1'}
            section.update({k:'Test section only' for k in ['locations','finding_zh','conditions_zh','results_zh','judgment_zh']})
            (r/'section-reviews.json').write_text(json.dumps([section]),encoding='utf-8')
            with self.assertRaises(AssertionError):build(a,r,c,root/'wrong-section-version')
            (r/'section-reviews.json').unlink()
            note['abstract_sha256']='wrong-version';f.write_text(json.dumps(note)+'\n',encoding='utf-8')
            with self.assertRaises(AssertionError):build(a,r,c,root/'bad-out')

if __name__=='__main__':unittest.main()
