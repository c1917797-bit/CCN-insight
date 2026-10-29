# -*- coding: utf-8 -*-
"""Date-routing fixtures test placement, not model semantic competence."""
import unittest
from route_reading_materials import placement

class RoutingTest(unittest.TestCase):
    def row(self,published,updated=None,relevance='direct'):
        return {'published':published,'updated':updated or published,'review':{'relevance':relevance}}
    def route(self,p):return placement(p,'2026-10','2026-10-29')
    def test_calendar_boundary_not_rolling_thirty_days(self):
        self.assertEqual(self.route(self.row('2026-09-30'))['route'],'topic')
        self.assertEqual(self.route(self.row('2026-10-01'))['route'],'monthly_new')
    def test_revision_keeps_original_date_and_topic_link(self):
        r=self.route(self.row('2026-09-05','2026-10-25'))
        self.assertEqual(r['route'],'monthly_revision');self.assertTrue(r['topic_eligible'])
        self.assertEqual(r['first_publication'],'2026-09-05')
    def test_unread_or_excluded_is_not_promoted_by_age(self):
        r=self.row('2024-01-01');r['review']=None
        self.assertEqual(self.route(r)['route'],'unread')
        self.assertEqual(self.route(self.row('2024-01-01',relevance='out_of_scope'))['route'],'excluded')
    def test_adjacent_is_observation_not_automatic_root_technique(self):
        r=self.route(self.row('2026-08-16',relevance='adjacent'))
        self.assertEqual(r['route'],'watch');self.assertEqual(r['suggested_time_route'],'topic')
    def test_future_is_not_monthly_event(self):
        self.assertEqual(self.route(self.row('2026-10-31'))['route'],'outside_month')
        self.assertEqual(self.route(self.row('2026-11-01'))['route'],'outside_month')
    def test_later_revision_cannot_backfill_frozen_month(self):
        r=placement(self.row('2026-10-05','2026-11-05'),'2026-10','2026-11-10')
        self.assertEqual(r['route'],'historical_version')
        r=placement(self.row('2026-10-05','2026-11-05'),'2026-10','2026-10-31')
        self.assertEqual(r['route'],'historical_version')

if __name__=='__main__':unittest.main()
