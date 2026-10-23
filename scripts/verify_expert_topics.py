"""Guard the expert entry/citation boundary found during real reader review."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compression_store import rows

def main():
    cards={r['card_id']:r for r in rows('ic_compression_topic_cards')}
    sources={r['source_id']:r for r in rows('cloud_core_sources')}
    refs=rows('ic_compression_topic_card_refs')
    topics=rows('ic_compression_topics')
    for t in topics:
        cid=t['compression_topic_id']+'__expert_brief';assert cid in cards,'expert entry missing: '+cid
        card=cards[cid];assert card['claim_kind']=='research_analysis','analyst brief promoted to author result'
        links=[r for r in refs if r['card_id']==cid];assert links,'uncited entry'
        assert all(r['source_id'] in sources for r in links),'unresolved source'
    # Regression for an observed cross-source locator leak, not a generic keyword ban.
    for r in refs:
        if 'Flint：Model architecture' in r['locator_zh']:
            assert 'flint' in sources[r['source_id']]['canonical_url'].lower(),'Flint locator bound to another paper: '+r['reference_id']
    print(f'PASS: {len(topics)} cited expert entries; no analyst-to-author promotion or known cross-source locator leak')

if __name__=='__main__':main()
