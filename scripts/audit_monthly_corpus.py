"""Reconcile actual paper-ID sets and prior editorial choices; never sum cell counts."""
import argparse
from collections import Counter
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT, rows

ROOT_TOPICS={f'{target}-{method}' for target in ('parameters','activations','kv_cache') for method in ('precision','selection','distillation','factorization')}
EXTENSIONS={'activations-merging','kv_cache-kv_eviction','kv_cache-sharing','kv_cache-compact_architecture'}

def audit(snapshot_id, scope_id):
    snapshot=next(r for r in rows('ic_monthly_corpus_snapshots') if r['snapshot_id']==snapshot_id)
    corpus={r['paper_id']:r for r in rows('ic_monthly_paper_corpus') if r['snapshot_id']==snapshot_id}
    assert len(corpus)==snapshot['candidate_count']
    related={pid for pid,r in corpus.items() if r['classification_status']=='classified'}
    topic_sets={pid:set(json.loads(r['topic_ids_json'])) for pid,r in corpus.items()}
    root={pid for pid,topics in topic_sets.items() if topics&ROOT_TOPICS}
    ext={pid for pid,topics in topic_sets.items() if topics&EXTENSIONS}
    assert related==root|ext
    assert len(related)==len(root)+len(ext)-len(root&ext)
    stories=[r for r in rows('ic_monthly_route_insights') if r['scope_id']==scope_id]
    refs=[r for r in rows('ic_monthly_route_evidence') if r['scope_id']==scope_id]
    summaries={r['summary_id']:r for r in rows('ic_paper_summaries')}
    sources={r['source_id']:r for r in rows('cloud_core_sources')}
    choices=[]
    for story in sorted(stories,key=lambda r:r['position']):
        evidence=[r for r in refs if r['story_id']==story['story_id']]
        source_ids={r['source_id'] for r in evidence}
        assert len(source_ids)==1
        source=sources[next(iter(source_ids))]
        summary_ids={r['summary_id'] for r in evidence}
        assert len(summary_ids)==1
        summary=summaries[next(iter(summary_ids))]
        # Imported external_id can be blank or include v1; the original URL is authoritative.
        match=re.fullmatch(r'https://arxiv\.org/(?:abs|html|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?',summary['evidence_url'])
        assert match,(story['story_id'],'Missing canonical arXiv paper identity')
        pid=match.group(1)
        topics={r['compression_topic_id'] for r in evidence}
        if pid in corpus:
            assert corpus[pid]['classification_status']=='classified',(pid,'Selection and corpus conflict')
            assert topics==topic_sets[pid],(pid,'Selection and corpus topic sets disagree')
            assert corpus[pid]['versioned_id']==pid+summary['observed_version']
        choices.append({'paper_id':pid,'story_id':story['story_id'],'selection_tier':story['selection_tier'],'selection_reason_zh':story['selection_reason_zh'],'review_status':summary['review_status'],'reviewed_at':summary['reviewed_at'],'evidence_url':summary['evidence_url'],'evidence_locator':summary['evidence_locator'],'topics':sorted(topics),'in_first_publication_corpus':pid in corpus})
    selected={r['paper_id'] for r in choices}
    assert len(selected)==len(choices),'One editorial story per stable paper ID'
    return {
        'snapshot_id':snapshot_id,'acquired_at':snapshot['acquired_at'],'first_publication_cutoff':snapshot['cutoff'],'reviewed_at':snapshot['reviewed_at'],
        'candidate_count':len(corpus),'statuses':dict(Counter(r['classification_status'] for r in corpus.values())),
        'map_related_unique':len(related),'root_unique':len(root),'extension_unique':len(ext),'overlap_unique':len(root&ext),'extension_only_unique':len(ext-root),
        'reconciliation':f'{len(related)} = {len(root)} + {len(ext-root)} = {len(root)} + {len(ext)} - {len(root&ext)}',
        'extension_only_paper_ids':sorted(ext-root),'root_extension_overlap_paper_ids':sorted(root&ext),
        'prior_reading_collection':{'scope_id':scope_id,'paper_count':len(selected),'first_publication_corpus_overlap':len(selected&set(corpus)),'outside_first_publication_corpus':sorted(selected-set(corpus)),'tiers':dict(Counter(r['selection_tier'] for r in choices)),'review_depth':dict(Counter(r['review_status'] for r in choices)),'choices':choices},
        'related_papers_outside_prior_collection':len(related-selected),
        'full_corpus_final_selection_completed':False,
        'selection_boundary':'The prior reading collection was created to fill editorial coverage gaps before this corpus classification. It is not the top-ranked result of a systematic comparison of all corpus papers.',
        'count_boundary':'Unique stable paper IDs within the saved registered arXiv query and publication window; not all sources or the whole field. Related classification is not topic-prose adoption.'
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--snapshot',default='corpus-2026-10-arxiv-20261029-abstract-v1')
    parser.add_argument('--scope',default='ic-2026-10-model-reviewed-20261029-v1')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=audit(args.snapshot,args.scope)
    if args.output:args.output.write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
    compact={k:v for k,v in result.items() if k not in ('extension_only_paper_ids','root_extension_overlap_paper_ids','prior_reading_collection')}
    compact['prior_collection']={k:v for k,v in result['prior_reading_collection'].items() if k!='choices'}
    print(json.dumps(compact,ensure_ascii=False))

if __name__=='__main__':main()
