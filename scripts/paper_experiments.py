"""Validate author-reported experiment comparisons, independently of the reader."""
from __future__ import annotations

from datetime import date
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT, rows

TABLE = 'ic_paper_experiments'
TEXT_FIELDS = '''experiment_id business_id topic_id source_id observed_version topic_ids_json
card_id method process_type experiment_kind model w_format a_format k_format v_format
config_zh config_en baseline_zh baseline_en dataset_zh dataset_en hardware_zh hardware_en
runtime_zh runtime_en workload_zh workload_en protocol_zh protocol_en quality_metrics_json
performance_metrics_json memory_metrics_json quality_status performance_status memory_status
source_url locator_zh locator_en review_depth checked_at'''.split()
FIELDS = TEXT_FIELDS + ['year', 'position']


def validate(experiments, sources, cards, topics, refs):
    """Fail closed on missing conditions, foreign identities, or ambiguous metrics."""
    source_map = {s['source_id']: s for s in sources}
    card_map = {c['card_id']: c for c in cards}
    topic_ids = {t['compression_topic_id'] for t in topics}
    bindings = {(r['compression_topic_id'], r['source_id']) for r in refs}
    seen = set()
    for row in experiments:
        key = row.get('experiment_id', '<missing>')
        def need(condition, message):
            if not condition:
                raise ValueError(f'Paper experiment {key}: {message}')
        need(set(row) == set(FIELDS), 'unknown or missing fields')
        need(all(isinstance(row[f], str) and row[f].strip() for f in TEXT_FIELDS), 'empty text field')
        need(re.fullmatch(r'[a-z0-9][a-z0-9_-]+', key) and key not in seen, 'invalid or duplicate experiment ID')
        seen.add(key)
        need(row['business_id'] == 'cloud-core' and row['topic_id'] == 'cloud_core', 'foreign scope')
        need(type(row['position']) is int and row['position'] >= 0, 'invalid position')
        need(type(row['year']) is int and 1990 <= row['year'] <= date.today().year, 'invalid first-publication year')
        need(row['process_type'] in {'PTQ', 'QAT', 'pruning', 'distillation', 'factorization', 'other'}, 'invalid process')
        need(row['experiment_kind'] in {'quality', 'system', 'kernel', 'memory'}, 'invalid measurement level')
        need(row['review_depth'] == 'section_review', 'numeric evidence requires a section review')
        need(date.fromisoformat(row['checked_at']) <= date.today(), 'future review date')
        linked = json.loads(row['topic_ids_json'])
        need(isinstance(linked, list) and linked and len(linked) == len(set(linked)), 'invalid topic list')
        need(all(t in topic_ids for t in linked), 'unknown topic')
        source_id = row['source_id']
        need(source_id in source_map and row['card_id'] in card_map, 'missing source or supporting card')
        need(card_map[row['card_id']]['compression_topic_id'] in linked, 'supporting card outside experiment topics')
        need(all((t, source_id) in bindings for t in linked), 'topic lacks an explicit source reference')
        need(any(r['source_id'] == source_id and r['card_id'] == row['card_id'] for r in refs), 'supporting card lacks this source')
        url = urlsplit(row['source_url'])
        need(url.scheme == 'https' and url.hostname == 'arxiv.org' and not url.username and not url.query, 'unsafe or unsupported primary URL')
        identity = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', url.path)
        canonical = re.search(r'(\d{4}\.\d{4,5})', source_map[source_id]['canonical_url'])
        need(identity and canonical and identity[1] == canonical[1], 'paper identity mismatch')
        need(identity[2] == row['observed_version'], 'URL does not pin the reviewed version')
        total = 0
        for family in ('quality', 'performance', 'memory'):
            metrics = json.loads(row[family + '_metrics_json'])
            status = row[family + '_status']
            need(isinstance(metrics, list), 'metrics must be a list')
            need(status in {'reported', 'not_reported', 'not_checked', 'not_applicable'}, 'invalid missing-data status')
            need((status == 'reported') == bool(metrics), 'reported status disagrees with numeric evidence')
            metric_ids = set()
            for metric in metrics:
                need(set(metric) == {'metric', 'baseline', 'result', 'unit', 'better', 'scope_zh', 'scope_en'}, 'invalid metric fields')
                need(all(isinstance(metric[f], str) and metric[f].strip() for f in ('metric', 'unit', 'scope_zh', 'scope_en')), 'metric lacks meaning, unit or scope')
                need(metric['metric'] not in metric_ids, 'duplicate metric')
                metric_ids.add(metric['metric'])
                need(metric['better'] in {'lower', 'higher'}, 'metric direction missing')
                need(all(type(metric[f]) in {int, float} and math.isfinite(metric[f]) and metric[f] >= 0 for f in ('baseline', 'result')), 'invalid number (missing is not zero)')
                if metric['unit'] == '%':
                    need(metric['baseline'] <= 100 and metric['result'] <= 100, 'percentage outside [0,100]')
                if 'perplexity' in metric['metric'].lower():
                    need(metric['unit'] == 'PPL' and metric['better'] == 'lower', 'PPL unit/direction mismatch')
                if row['experiment_kind'] == 'kernel':
                    need(not any(name in metric['metric'].upper() for name in ('TTFT', 'TPOT')), 'kernel result mislabeled as serving latency')
                total += 1
        need(total > 0, 'no quantitative comparison')
    return len(experiments)


def validate_canonical():
    return validate(rows(TABLE), rows('cloud_core_sources'), rows('ic_compression_topic_cards'),
                    rows('ic_compression_topics'), rows('ic_compression_topic_card_refs'))


if __name__ == '__main__':
    print(f'PASS: {validate_canonical()} traceable author-reported experiments')
