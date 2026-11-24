"""Exercise consequential date, evidence, count and review-depth boundaries."""
import copy
import json
import unittest
from monthly_digest import canonical_tables, validate_digest, csv_text


class MonthlyDigestContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables = canonical_tables()
        cls.scope = next(r for r in cls.tables['ic_monthly_scopes'] if r.get('digest_json'))

    def check_mutation(self, mutate):
        scope, tables = copy.deepcopy(self.scope), copy.deepcopy(self.tables)
        digest = json.loads(scope['digest_json'])
        mutate(digest, tables)
        scope['digest_json'] = json.dumps(digest)
        with self.assertRaises((ValueError, KeyError)):
            validate_digest(scope, tables)

    def test_real_november_reconciliation(self):
        actual = validate_digest(self.scope, self.tables)
        self.assertEqual((actual['discovered'], actual['keyword_candidates'], actual['primary_checked']), (649, 147, 21))
        self.assertEqual((actual['section_checked'], actual['curated_papers'], actual['industry_events']), (12, 16, 15))
        # The old month is an independently preserved snapshot, not rewritten.
        old = [r for r in self.tables['ic_monthly_route_insights'] if r['scope_id'] == 'ic-2026-10-model-reviewed-20261029-v1']
        self.assertEqual(len(old), 16)

    def test_observations_do_not_become_additional_releases(self):
        self.check_mutation(lambda d, t: d['metrics'][-1].update(count=18))

    def test_cutoff_cannot_silently_become_month_end(self):
        self.check_mutation(lambda d, t: d.update(cutoff='2026-11-30'))

    def test_first_publication_cannot_use_a_discovery_date(self):
        def mutate(d, tables):
            row = next(r for r in tables['ic_monthly_materials'] if r['selection_status'] == 'key_progress')
            row['verified_first_published'] = '2026-10-31'
        self.check_mutation(mutate)

    def test_unreviewed_recommendation_cannot_be_promoted(self):
        def mutate(d, tables):
            row = next(r for r in tables['ic_monthly_materials'] if r['review_status'] == 'discovery_only')
            row['selection_status'] = 'key_progress'
        self.check_mutation(mutate)

    def test_versioned_citation_cannot_point_at_latest(self):
        def mutate(d, tables):
            citation = next(r for r in d['citations'] if 'arxiv.org' in r['evidence_url'])
            citation['evidence_url'] = 'https://arxiv.org/abs/2611.23388'
        self.check_mutation(mutate)

    def test_missing_weight_factorization_is_an_explicit_gap(self):
        d = json.loads(self.scope['digest_json'])
        lowrank = next(r for r in d['themes'] if r['id'] == 'factorization')
        self.assertEqual(lowrank['status'], 'coverage_gap')
        self.assertIn('权重', lowrank['title_zh'])

    def test_public_csv_keeps_external_titles_literal(self):
        self.assertIn("'=external()", csv_text([['=external()', 'ordinary title']]))


if __name__ == '__main__':
    unittest.main()
