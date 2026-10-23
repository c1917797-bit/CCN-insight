"""Offline regression checks for feed dating, dedupe, review preservation and retry."""
import json
import unittest
from unittest.mock import patch
import collect_agent_signals as collector

class CollectionContract(unittest.TestCase):
    def test_arxiv_announcement_is_not_first_publication(self):
        payload=b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/2605.19385v2</id><title>Scheduling</title><published>2026-10-23T00:00:00Z</published><updated>2026-10-23T00:00:00Z</updated><summary>agent scheduling</summary></entry></feed>'''
        row=collector.parse({'adapter':'atom'},payload)[0]
        self.assertEqual((row['published'],row['revised'],row['feed_date']),('','','2026-10-23'))
        self.assertEqual(collector.identity(row['url']),collector.identity('https://arxiv.org/abs/2605.19385v1'))

    def test_release_uses_published_not_created_and_preserves_prerelease(self):
        payload=json.dumps([{'html_url':'https://github.com/org/repo/releases/tag/v1','name':'Queue','tag_name':'v1','published_at':'2026-10-20T01:00:00Z','created_at':'2026-09-01T01:00:00Z','prerelease':True}]).encode()
        row=collector.parse({'adapter':'github'},payload)[0]
        self.assertEqual(row['published'],'2026-10-20')
        self.assertIn('预发布',row['version'])

    def test_duplicate_retains_human_review_and_first_seen(self):
        old={'id':'paper','first_seen':'earlier','last_seen':'earlier','published':'','revised':'','review_status':'已排除：不相关'}
        new={**old,'first_seen':'later','last_seen':'later','review_status':'待原文审阅'}
        rows,added=collector.merge([old],[new,new])
        self.assertEqual((len(rows),added),(1,0))
        self.assertEqual(rows[0]['first_seen'],'earlier')
        self.assertEqual(rows[0]['review_status'],old['review_status'])

    def test_failure_is_bounded_and_visible(self):
        with patch.object(collector,'urlopen',side_effect=TimeoutError('temporary')),patch.object(collector.time,'sleep'):
            rows,attempts,error=collector.retrieve({'url':'https://api.github.com/repos/ray-project/ray/releases','adapter':'github'})
        self.assertEqual((rows,attempts),([],3));self.assertIn('TimeoutError',error)

    def test_rejects_credentials_and_unreviewed_host(self):
        with self.assertRaises(ValueError):collector.safe_url('https://secret@example.com/private')
        with self.assertRaises(ValueError):collector.retrieve({'url':'https://example.com/feed','adapter':'atom'})

if __name__=='__main__':unittest.main()
