# -*- coding: utf-8 -*-
"""Direct-adoption regressions: reject invalid evidence before reading canonical tables."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import adopt_reviewed_materials as adoption


class AdoptionPreflightTest(unittest.TestCase):
    def fixture(self, root):
        acquired, reviewed = root/'acquired', root/'reviewed'
        acquired.mkdir(); reviewed.mkdir()
        papers, notes, choices = [], [], []
        for number in [1, 2]:
            pid = '2610.0000'+str(number)
            abstract = 'A smaller student preserves speech quality. 原始摘要。\nExact bytes matter.'
            paper = {'paper_id': pid, 'versioned_id': pid+'v2', 'title': 'Fixture only',
                     'url': 'https://arxiv.org/abs/'+pid+'v2', 'abstract': abstract,
                     'abstract_sha256': hashlib.sha256(abstract.encode('utf-8')).hexdigest(),
                     'published': '2026-10-01T00:00:00Z', 'updated': '2026-10-02T00:00:00Z'}
            note = {k: paper[k] for k in ['paper_id','versioned_id','title','url','abstract_sha256']}
            note.update(review_status='model_abstract_reviewed', relevance='direct', routes=['distillation'])
            note.update({k: 'Fixture annotation' for k in ['problem_zh','mechanism_zh','reported_results_zh','limitations_zh','value_zh','next_read_zh']})
            choice = {'paper_id': pid, 'destination': 'monthly', 'topics': ['parameters-distillation'],
                      'cells': ['W_D'], 'keywords': ['fixture']}
            choice.update({field+'_'+lang: 'Fixture decision' for lang in ['zh','en']
                           for field in ['title','background','mechanism','results','boundary','next']})
            papers.append(paper); notes.append(note); choices.append(choice)
        section = {'paper_id': papers[-1]['paper_id'], 'review_level': 'section_reviewed',
                   'url': 'https://arxiv.org/html/'+papers[-1]['versioned_id']}
        section.update({k: 'Fixture section' for k in ['locations','finding_zh','conditions_zh','results_zh','judgment_zh']})
        data = {'papers': papers, 'notes': notes, 'choices': choices, 'sections': [section], 'extra_notes': []}
        (acquired/'receipt.json').write_text(json.dumps({'window_end': '2026-10-29'}), encoding='utf-8')
        return acquired, reviewed, data

    def write(self, acquired, reviewed, data):
        for path, rows in [(acquired/'abstracts.jsonl', data['papers']),
                           (reviewed/'model-reviews.jsonl', data['notes']),
                           (reviewed/'extra-reviews.jsonl', data['extra_notes'])]:
            path.write_text(''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in rows), encoding='utf-8')
        (reviewed/'section-reviews.json').write_text(json.dumps(data['sections']), encoding='utf-8')
        decisions = reviewed/'decisions.json'
        decisions.write_text(json.dumps(data['choices']), encoding='utf-8')
        return decisions

    def rejects_before_staging(self, mutate, message):
        # Two selected papers ensure an invalid last paper cannot follow a staged first one.
        with tempfile.TemporaryDirectory(prefix='ccn-adoption-test-') as temp:
            root = Path(temp); acquired, reviewed, data = self.fixture(root)
            mutate(data); decisions = self.write(acquired, reviewed, data)
            out, canonical = root/'out', root/'canonical-must-not-be-accessed'
            with patch.object(adoption, 'ROOT', canonical), patch.object(adoption.subprocess, 'run') as command:
                with self.assertRaisesRegex(ValueError, message):
                    adoption.adopt(acquired, reviewed, decisions, out, apply=True)
                command.assert_not_called()
            self.assertFalse(out.exists(), 'Invalid evidence generated a preview/scope')
            self.assertFalse(canonical.exists(), 'Invalid evidence touched canonical or backups')

    def test_valid_unicode_abstract_and_versioned_section(self):
        for suffix in ['', '#S4', '/#S4']:
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); acquired, reviewed, data = self.fixture(root)
                data['sections'][0]['url'] += suffix
                decisions = self.write(acquired, reviewed, data)
                papers, notes, sections, choices = adoption.validate_selected_inputs(acquired, reviewed, decisions, '2026-10-29')
                self.assertEqual((len(papers),len(notes),len(sections),len(choices)), (2,2,1,2))

    def test_exact_section_version_and_origin_required_by_direct_adopter(self):
        for url in ['https://arxiv.org/html/2610.00002v1', 'https://arxiv.org/html/2610.00002v20',
                    'https://arxiv.org/abs/2610.00002v2', 'https://arxiv.org.evil/html/2610.00002v2',
                    'https://user@arxiv.org/html/2610.00002v2', 'https://arxiv.org:443/html/2610.00002v2',
                    'https://arxiv.org/html/2610.00002v2?version=v1', 'http://arxiv.org/html/2610.00002v2']:
            with self.subTest(url=url):
                self.rejects_before_staging(lambda d: d['sections'][0].update(url=url), 'Section review version URL mismatch')

    def test_original_and_model_abstract_hashes_both_checked(self):
        self.rejects_before_staging(lambda d: d['papers'][-1].update(abstract=d['papers'][-1]['abstract']+' '), 'Original abstract SHA256 mismatch')
        self.rejects_before_staging(lambda d: d['notes'][-1].update(abstract_sha256='stale'), 'Model review abstract SHA256 mismatch')

    def test_acquired_identity_checked_without_sections_or_optional_note_url(self):
        def wrong_source_url(data):
            data['sections'] = []
            data['notes'][-1].pop('url')
            data['papers'][-1]['url'] = 'https://arxiv.org/abs/2610.99999v2'
        self.rejects_before_staging(wrong_source_url, 'Acquired abstract version URL mismatch')
        def invalid_paper_id(data):
            for field in ['papers','notes','choices']:
                data[field][-1]['paper_id'] = 'garbage'
            data['papers'][-1]['versioned_id'] = 'garbagev2'
            data['papers'][-1]['url'] = 'https://arxiv.org/abs/garbagev2'
            data['sections'] = []
        self.rejects_before_staging(invalid_paper_id, 'Invalid arXiv paper_id')

    def test_duplicate_inputs_cannot_silently_overwrite(self):
        for field, message in [('papers','Duplicate acquired paper'), ('notes','Duplicate model review'),
                               ('sections','Duplicate section review'), ('choices','Duplicate selected paper')]:
            with self.subTest(field=field):
                self.rejects_before_staging(lambda d: d[field].append(copy.deepcopy(d[field][-1])), message)
        self.rejects_before_staging(lambda d: d['extra_notes'].append(copy.deepcopy(d['notes'][-1])), 'Duplicate model review')

    def test_review_completion_and_source_identity_required(self):
        cases = [('notes','review_status','not_read','Model abstract review not completed'),
                 ('notes','relevance','adjacent','not directly relevant'),
                 ('notes','versioned_id','2610.00002v1','Model review source identity changed'),
                 ('papers','versioned_id','2610.99999v2','Invalid source version identity'),
                 ('notes','problem_zh','  ','Incomplete model annotation'),
                 ('sections','review_level','full_text_reviewed','Section review not completed'),
                 ('sections','locations','  ','Incomplete section annotation')]
        for field, key, value, message in cases:
            with self.subTest(field=field, key=key):
                self.rejects_before_staging(lambda d: d[field][-1].update({key:value}), message)
        self.rejects_before_staging(lambda d: d['notes'].pop(), 'missing a model abstract review')

    def test_dates_and_decisions_validated_before_any_scope(self):
        self.rejects_before_staging(lambda d: d['papers'][-1].update(updated='2026-11-01'), 'unavailable at snapshot')
        self.rejects_before_staging(lambda d: d['choices'][-1].update(destination='typo'), 'Unknown destination')
        self.rejects_before_staging(lambda d: d['choices'][-1].update(destination='topic'), 'calendar-month dates')
        for choices in [[], {}]:
            with self.subTest(choices=choices):
                self.rejects_before_staging(lambda d: d.update(choices=choices), 'nonempty decisions list')

    def test_editorial_tier_requires_an_explicit_reason(self):
        self.rejects_before_staging(lambda d: d['choices'][-1].update(selection_tier='top_by_citations'), 'Unknown editorial tier')
        self.rejects_before_staging(lambda d: d['choices'][-1].update(selection_tier='key_progress'), 'Missing selection reason')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);acquired,reviewed,data=self.fixture(root)
            data['choices'][-1].update(selection_tier='technical_watch',selection_reason_zh='机制相关，实验条件尚需核对。',selection_reason_en='Relevant mechanism; experimental conditions need checking.')
            decisions=self.write(acquired,reviewed,data)
            _,_,_,choices=adoption.validate_selected_inputs(acquired,reviewed,decisions,'2026-10-29')
            self.assertEqual(choices[-1]['selection_tier'],'technical_watch')


if __name__ == '__main__':
    unittest.main()
