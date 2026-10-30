"""Offline safeguards for reimport after targeted source-section review."""
import copy
import unittest
from unittest.mock import patch

import import_monthly_paper_corpus as importer


class MonthlyCorpusImportTest(unittest.TestCase):
    def test_main_rejects_section_review_before_reading_or_writing_inputs(self):
        # Even the same source version/hash must not replace a later human decision.
        existing=[{'snapshot_id':'corpus-2026-10-arxiv-20261029-abstract-v1',
                   'paper_id':'2610.20303','versioned_id':'2610.20303v2',
                   'abstract_sha256':'a'*64,'review_basis':'original_sections',
                   'review_url':'https://arxiv.org/html/2610.20303v2',
                   'review_locator':'Test fixture: methods and selected table',
                   'reviewed_at':'2026-10-30'}]
        before=copy.deepcopy(existing)
        with patch.object(importer,'rows',return_value=existing), \
             patch.object(importer,'write_table') as write, \
             patch.object(importer.Path,'read_text') as read, \
             patch('sys.argv',['import_monthly_paper_corpus.py','--decisions','missing-decisions','--acquisition','missing-acquisition']):
            with self.assertRaisesRegex(RuntimeError,'original_sections reviews for 2610.20303'):
                importer.main()
            write.assert_not_called()
            read.assert_not_called()
        self.assertEqual(existing,before,'The guard must not mutate canonical rows')

    def test_other_snapshot_and_original_abstract_do_not_block_import(self):
        importer.guard_abstract_reimport([
            {'snapshot_id':'older','paper_id':'2609.00001','review_basis':'original_sections'},
            {'snapshot_id':'current','paper_id':'2610.00001','review_basis':'original_abstract'},
        ],'current')

    def test_decision_hash_binds_review_provenance_and_is_order_independent(self):
        row=dict.fromkeys(importer.DECISION_HASH_FIELDS,'')
        row.update(paper_id='2610.00001',abstract_sha256='a'*64,
                   classification_status='classified',topic_ids_json='["parameters-precision"]',
                   basis_zh='Test fixture only',review_basis='original_sections',
                   review_url='https://arxiv.org/html/2610.00001v2',
                   review_locator='Section 3; Table 1',reviewed_at='2026-10-30')
        base=importer.decision_hash([row])
        for field in ['review_basis','review_url','review_locator','reviewed_at']:
            with self.subTest(field=field):
                self.assertNotEqual(base,importer.decision_hash([{**row,field:row[field]+' changed'}]))
        other={**row,'paper_id':'2610.00002'}
        self.assertEqual(importer.decision_hash([row,other]),importer.decision_hash([other,row]))


if __name__=='__main__':
    unittest.main()
