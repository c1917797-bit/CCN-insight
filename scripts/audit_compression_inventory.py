"""Read-only, reproducible inventory of maintained compression evidence.

Writes an audit report, never changes source tables. Counts from migration and
generated snapshots stay separate from canonical counts to avoid double counting.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qsl, unquote, urlencode, urlparse

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / 'data/compression/tables'


def read_rows(path: Path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():
            continue
        envelope = json.loads(line)
        if not envelope.get('deleted', False):
            rows.append(envelope.get('row', envelope))
    return rows


def histogram(rows, key):
    return dict(sorted(Counter(str(row.get(key, '<missing>')) for row in rows).items()))


def paper_identity(row):
    """Conservative identifier normalization; no title-fuzzy paper merging.

    arXiv versions/abs/html/pdf merge by eprint. Explicit DOI merges by DOI.
    Other declared paper records use normalized canonical URL. Repository and
    news URLs are not counted as papers merely because they are in source rows.
    """
    fields = [str(row.get(k, '')) for k in
              ('identity_key', 'external_id', 'canonical_url', 'evidence_url', 'observed_url', 'url')]
    for text in fields:
        found = re.search(r'(?:arxiv:|arxiv\.org/(?:abs|html|pdf)/|^)(\d{4}\.\d{4,5})(?:v\d+)?', text, re.I)
        if found:
            return 'arxiv:' + found.group(1)
        found = re.search(r'arxiv\.org/(?:abs|html|pdf)/([a-z.-]+/\d{7})(?:v\d+)?', text, re.I)
        if found:
            return 'arxiv:' + found.group(1).lower()
    for text in fields:
        found = re.search(r'(?:https?://(?:dx\.)?doi\.org/|doi:)(10\.\d{4,9}/\S+)', text, re.I)
        if found:
            return 'doi:' + unquote(found.group(1)).rstrip('.,;').lower()
    kind = str(row.get('source_kind', '')).lower()
    url = str(row.get('canonical_url') or row.get('url') or '')
    if kind not in {'paper', 'academic_paper', 'research_paper', 'preprint', 'conference_paper', 'journal_paper'}:
        return None
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        return None
    host = parsed.netloc.lower()
    query = dict(parse_qsl(parsed.query))
    if host in {'openreview.net', 'www.openreview.net'} and query.get('id') and parsed.path in {'/forum', '/pdf'}:
        return 'openreview:' + query['id']
    # ACL, OpenReview and proceedings identifiers remain distinct from arXiv.
    # There is no reliable cross-provider alias table in the maintained data.
    semantic_query = [(k, v) for k, v in parse_qsl(parsed.query) if not k.lower().startswith('utm_') and k.lower() not in {'fbclid', 'gclid'}]
    query_suffix = '?' + urlencode(sorted(semantic_query)) if semantic_query else ''
    return 'paper_url:' + host + parsed.path.rstrip('/') + query_suffix


def build_report(include_snapshots=True):
    tables = {path.parent.name: read_rows(path) for path in sorted(TABLES.glob('*/rows.jsonl'))}
    sources = tables['cloud_core_sources']
    source_by_id = {r['source_id']: r for r in sources}
    paper_by_source = {sid: identity for sid, r in source_by_id.items() if (identity := paper_identity(r))}

    def paper_keys(records, field='source_id'):
        return {paper_by_source[r[field]] for r in records if r.get(field) in paper_by_source}

    paper_groups = defaultdict(list)
    for sid, identity in paper_by_source.items():
        paper_groups[identity].append(sid)
    pipeline = tables.get('ic_source_pipeline', [])
    pipeline_groups = defaultdict(list)
    for row in pipeline:
        pipeline_groups[row.get('stage', '<missing>')].append(row)
    refs = tables.get('ic_compression_topic_card_refs', [])
    cards = tables.get('ic_compression_topic_cards', [])
    card_by_id = {r['card_id']: r for r in cards}
    case_ids = {r['card_id'] for r in cards if r.get('card_kind') == 'case'}
    case_refs = [r for r in refs if r.get('card_id') in case_ids]
    section = [r for r in refs if r.get('review_depth') == 'section_review']
    abstract = [r for r in refs if r.get('review_depth') == 'abstract_review']
    section_keys, abstract_keys = paper_keys(section), paper_keys(abstract)
    summaries = tables.get('ic_paper_summaries', [])
    screening = tables.get('ic_source_screenings', [])
    events = tables.get('ic_compression_topic_events', [])
    candidates = tables.get('ic_source_route_candidates', [])
    primary_events = [r for r in events if r.get('review_status') == 'primary_review']
    approved_screenings = [r for r in screening if r.get('screening_status') in {'selected', 'direct', 'included', 'in_scope'}]
    invalid_source_ids = {r['source_id'] for r in pipeline if r.get('stage') == 'blocked_invalid'}
    nonblocked_papers = {identity for sid, identity in paper_by_source.items() if sid not in invalid_source_ids}
    intake = tables.get('ic_paper_review_intakes', [])

    per_topic = []
    for topic in sorted(tables.get('ic_compression_topics', []), key=lambda r: r['compression_topic_id']):
        tid = topic['compression_topic_id']
        topic_cards = [r for r in cards if r.get('compression_topic_id') == tid]
        topic_refs = [r for r in refs if r.get('compression_topic_id') == tid]
        topic_case_refs = [r for r in topic_refs if r.get('card_id') in case_ids]
        related_candidates = [r for r in candidates if r.get('route_topic_id') == tid]
        per_topic.append({
            'topic_id': tid, 'cards': len(topic_cards),
            'case_cards': sum(r.get('card_kind') == 'case' for r in topic_cards),
            'cited_paper_identities': len(paper_keys(topic_refs)),
            'case_paper_identities': len(paper_keys(topic_case_refs)),
            'selected_section_paper_identities': len(paper_keys([r for r in topic_refs if r.get('review_depth') == 'section_review'])),
            'abstract_only_paper_identities': len(paper_keys([r for r in topic_refs if r.get('review_depth') == 'abstract_review']) - paper_keys([r for r in topic_refs if r.get('review_depth') == 'section_review'])),
            'machine_candidate_links': len(related_candidates),
            'machine_candidate_papers': len(paper_keys(related_candidates)),
            'machine_candidates_not_yet_cited_papers': len(paper_keys(related_candidates) - paper_keys(topic_refs)),
        })

    legacy = []
    migration_root = ROOT / 'data/tables'
    for folder in sorted(migration_root.iterdir()) if migration_root.exists() and include_snapshots else []:
        paths = sorted(folder.glob('rows-*.jsonl'))
        if not paths:
            continue
        legacy_rows = [r for path in paths for r in read_rows(path)]
        if 'source' in folder.name or 'paper' in folder.name or 'pipeline' in folder.name:
            own_papers = {p for r in legacy_rows if (p := paper_identity(r))}
            linked_papers = paper_keys(legacy_rows)
            legacy.append({'table': folder.name, 'rows': len(legacy_rows), 'files': len(paths),
                           'paper_identity_count_from_own_records': len(own_papers),
                           'paper_identity_count_linked_to_canonical_sources': len(linked_papers),
                           'own_paper_identities_not_in_canonical_sources': len(own_papers - set(paper_groups)),
                           'source_status': histogram(legacy_rows, 'source_status'),
                           'reference_kind': histogram(legacy_rows, 'reference_kind'),
                           'counting_policy': 'migration_provenance_not_an_additional_paper_corpus'})

    snapshots = []
    snapshot_paths = ('research/ai-infra/imported/cloud_core_sources.json', 'research/ai-infra/imported/compression_sources.json',
                      'research/source-audits/2026-10-23/candidate-queue.json', 'research/source-audits/2026-10-23/arxiv-recent.json')
    for rel in snapshot_paths if include_snapshots else ():
        path = ROOT / rel
        if not path.exists():
            continue
        raw = json.loads(path.read_text(encoding='utf-8-sig'))
        entry = {'path': rel, 'root_type': type(raw).__name__, 'root_count': len(raw),
                 'counting_policy': 'snapshot_only_not_added_to_canonical_total'}
        if isinstance(raw, dict):
            entry['declared_row_count'] = raw.get('row_count')
            entry['rows_count'] = len(raw.get('rows', []))
            entry['generated_from'] = raw.get('generated_from')
        elif 'candidate-queue' in rel:
            entry['status_rows'] = histogram(raw, 'status')
            entry['unique_arxiv_candidates'] = len({r['arxiv_id'] for r in raw if r.get('arxiv_id')})
        elif 'arxiv-recent' in rel:
            entry['received_entries_sum_not_deduplicated'] = sum(r.get('received_entries', 0) for r in raw)
            listed = [r for group in raw for r in group.get('candidates', [])]
            entry['candidate_entries'] = len(listed)
            entry['unique_arxiv_candidates'] = len({r['arxiv_id'] for r in listed if r.get('arxiv_id')})
        snapshots.append(entry)

    report = {
        'audit_date': '2026-10-23', 'basis': 'Current working-tree canonical rows; no fresh web or full-paper review is asserted.',
        'identity_policy': {
            'rules': ['arXiv eprint normalized across versions and abs/html/pdf URLs', 'Explicit DOI normalized', 'Other declared papers counted by canonical URL'],
            'limitation': 'Cross-provider aliases (e.g. same paper on arXiv and ACL/OpenReview) are not merged without an explicit alias. Counts are identifier-deduplicated, not guaranteed unique intellectual works.',
            'exclusions': 'Source/repository/news records without paper identifiers or declared paper kinds are not papers.',
        },
        'canonical': {
            'table_count': len(tables), 'active_rows_total': sum(len(r) for r in tables.values()),
            'table_rows': {n: len(r) for n, r in tables.items()},
            'source_rows': len(sources), 'paper_source_rows': len(paper_by_source),
            'deduplicated_paper_identities': len(paper_groups),
            'paper_identities_with_at_least_one_source_not_marked_invalid': len(nonblocked_papers),
            'paper_identities_only_marked_invalid': len(set(paper_groups) - nonblocked_papers),
            'paper_identity_duplicate_rows': len(paper_by_source) - len(paper_groups),
            'source_kind': histogram(sources, 'source_kind'),
            'source_provider': histogram(sources, 'provider'),
        },
        'discovery_funnel': {
            'pipeline_rows': len(pipeline), 'pipeline_papers': len(paper_keys(pipeline)),
            'stage_rows': {stage: len(rows) for stage, rows in sorted(pipeline_groups.items())},
            'stage_paper_identities': {stage: len(paper_keys(rows)) for stage, rows in sorted(pipeline_groups.items())},
            'evidence_level': histogram(pipeline, 'evidence_level'),
            'rule_version_rows': histogram(pipeline, 'rule_version'),
            'reason_code_rows': histogram(pipeline, 'reason_code'),
            'stored_runs': tables.get('ic_pipeline_runs', []),
            'machine_route_candidate_links': len(candidates), 'machine_route_candidate_papers': len(paper_keys(candidates)),
            'machine_route_candidate_papers_not_in_any_topic': len(paper_keys(candidates) - paper_keys(refs)),
            'primary_review_topic_event_papers': len(paper_keys(primary_events)),
            'manual_screening_status_rows': histogram(screening, 'screening_status'),
            'manual_selected_paper_identities': len(paper_keys(approved_screenings)),
            'warning': 'Title signals are candidates, not confirmed compression relevance. This funnel is a stale snapshot and not synchronized with all later topic references.',
        },
        'absorbed_into_topics': {
            'topic_count': len(per_topic), 'cards': len(cards), 'case_cards': len(case_ids),
            'citation_links': len(refs), 'cited_source_rows': len({r['source_id'] for r in refs}),
            'cited_paper_identities': len(paper_keys(refs)),
            'case_paper_identities': len(paper_keys(case_refs)),
            'selected_section_paper_identities': len(section_keys),
            'abstract_only_paper_identities': len(abstract_keys - section_keys),
            'reference_review_depth_rows': histogram(refs, 'review_depth'),
            'paper_summaries': len(summaries), 'summary_paper_identities': len(paper_keys(summaries)),
            'summary_papers_cited_in_topics': len(paper_keys(summaries) & paper_keys(refs)),
            'summary_papers_not_yet_cited_in_topics': len(paper_keys(summaries) - paper_keys(refs)),
            'explicit_review_intake_rows': len(intake), 'review_intake_papers': len(paper_keys(intake)),
            'paper_summary_review_status': histogram(summaries, 'review_status'),
            'explicit_full_paper_review_refs': sum(r.get('review_depth') in {'full_text_review', 'full_paper_review', 'full_review'} for r in refs),
            'independent_reproduction_claim': False,
            'per_topic': per_topic,
            'warning': 'Citations include background and boundary evidence; citation count is not a count of distinct algorithms or independently reproduced methods.',
        },
        'relationships': {
            'topic_refs_missing_source': sorted({r['source_id'] for r in refs if r.get('source_id') not in source_by_id}),
            'topic_refs_missing_card': sorted({r['card_id'] for r in refs if r.get('card_id') not in card_by_id}),
            'cited_papers_absent_from_discovery_pipeline': len(paper_keys(refs) - paper_keys(pipeline)),
            'cited_papers_absent_from_discovery_pipeline_identity_values': sorted(paper_keys(refs) - paper_keys(pipeline)),
            'pipeline_reviewed_visible_papers': len(paper_keys(pipeline_groups.get('reviewed_visible', []))),
            'paper_summaries_not_yet_cited_identity_values': sorted(paper_keys(summaries) - paper_keys(refs)),
            'cited_paper_identity_values': sorted(paper_keys(refs)),
            'candidate_paper_identity_values': sorted(paper_keys(candidates)),
        },
        'legacy_snapshots_separate': legacy,
        'research_snapshots_separate': snapshots,
        'reproduction': 'python -X utf8 scripts/audit_compression_inventory.py --output docs/compression-inventory-audit-20261023.json',
    }
    digest = hashlib.sha256()
    for path in sorted(TABLES.glob('*/rows.jsonl')):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    report['canonical']['table_files_sha256'] = digest.hexdigest()
    return report


def public_summary(report, version):
    """Public aggregate only: no titles, personal paths or source metadata."""
    canonical, funnel, topics, relations = (report[k] for k in
                                           ('canonical', 'discovery_funnel', 'absorbed_into_topics', 'relationships'))
    candidate_rows = sum(funnel['stage_rows'].get(k, 0) for k in ('candidate_direct', 'candidate_adjacent'))
    counts = {
        'source_records': canonical['source_rows'],
        'paper_source_records': canonical['paper_source_rows'],
        'paper_identities': canonical['deduplicated_paper_identities'],
        'paper_identities_not_only_invalid': canonical['paper_identities_with_at_least_one_source_not_marked_invalid'],
        'pipeline_records': funnel['pipeline_rows'],
        'title_candidate_records': candidate_rows,
        'direct_title_candidate_records': funnel['stage_rows'].get('candidate_direct', 0),
        'adjacent_title_candidate_records': funnel['stage_rows'].get('candidate_adjacent', 0),
        'needs_relevance_review_records': funnel['stage_rows'].get('needs_relevance_review', 0),
        'invalid_identity_records': funnel['stage_rows'].get('blocked_invalid', 0),
        'reviewed_summary_papers': topics['summary_paper_identities'],
        'summary_method_results_checked': topics['paper_summary_review_status'].get('method_results_checked', 0),
        'summary_abstract_checked': topics['paper_summary_review_status'].get('primary_abstract_checked', 0),
        'topic_cited_papers': topics['cited_paper_identities'],
        'topic_case_papers': topics['case_paper_identities'],
        'topic_section_checked_papers': topics['selected_section_paper_identities'],
        'topic_abstract_only_papers': topics['abstract_only_paper_identities'],
        'topic_count': topics['topic_count'], 'topic_cards': topics['cards'],
        'full_paper_review_refs': topics['explicit_full_paper_review_refs'],
    }
    return {
        'schema_version': 1, 'audit_date': report['audit_date'], 'content_version': version,
        'revision': hashlib.sha256(version.encode('utf-8')).hexdigest()[:40],
        'source_input_sha256': canonical['table_files_sha256'],
        'counts': counts,
        'gaps': {
            'cited_papers_missing_from_old_discovery_pipeline': relations['cited_papers_absent_from_discovery_pipeline'],
            'machine_candidate_papers_not_yet_cited': funnel['machine_route_candidate_papers_not_in_any_topic'],
            'summary_papers_not_yet_cited': topics['summary_papers_not_yet_cited_in_topics'],
            'old_pipeline_reviewed_visible_papers': relations['pipeline_reviewed_visible_papers'],
        },
        'funnel': [
            {'id': 'inventory', 'count': counts['paper_identities'], 'unit': 'paper_identifiers',
             'label_zh': '收录的论文编号', 'label_en': 'Paper identifier inventory',
             'note_zh': '按论文编号或链接去重；含待核对记录，还没逐篇确认是否属于推理压缩。',
             'note_en': 'Deduplicated by arXiv ID, DOI or paper URL; identities and compression relevance are not all verified.'},
            {'id': 'candidate', 'count': counts['title_candidate_records'], 'unit': 'candidate_source_records',
             'label_zh': '按标题筛出的候选', 'label_en': 'Title candidate records',
             'note_zh': '程序按标题筛出的直接相关或相邻工作；还需要读原文，不能当成已经读过。',
             'note_en': 'Direct plus adjacent candidates from an older machine batch; not confirmed relevant papers.'},
            {'id': 'review', 'count': counts['reviewed_summary_papers'], 'unit': 'paper_identifiers',
             'label_zh': '有阅读记录的论文', 'label_en': 'Papers with reviewed summaries',
             'note_zh': '有的读过摘要，有的核对过方法和实验；两者分开记录，不代表都读完全文或做过实验。',
             'note_en': 'Abstract and selected method/results checks retain their own scopes; not full-paper reviews or reproductions.'},
            {'id': 'topic', 'count': counts['topic_cited_papers'], 'unit': 'paper_identifiers',
             'label_zh': '进入专题的论文', 'label_en': 'Papers cited by topics',
             'note_zh': '已用于解释原理、比较方法或形成判断；引用论文不等于已经在业务中用起来。',
             'note_en': 'Includes classical, mechanism, context and boundary evidence; not a count of deployed algorithms.'},
        ],
        'limits_zh': [
            '这是已维护数据的库存盘点，不是全领域最新或完整覆盖声明。',
            '四个环节采用不同口径，且旧漏斗尚未与后续专题全部对账，不能直接相除当作转化率。',
            '同一论文的 arXiv 与会议版本缺少显式别名时仍可能分别计数；标识去重不等于作品级完全去重。',
            '没有独立复现或目标平台实测结论；章节核对不等于全文审阅。',
        ],
        'limits_en': [
            'This audits maintained inventory, not complete or current field coverage.',
            'Stages have different units and the old pipeline is not fully reconciled; do not interpret ratios as conversion rates.',
            'arXiv and conference aliases may remain distinct without explicit mappings; identifier deduplication is not work-level deduplication.',
            'No independent reproduction or target-platform measurement is asserted; selected-section checks are not full-paper reviews.',
        ],
    }


def build(output_dir: Path):
    """Build the reader's lightweight, aggregate-only audit view."""
    sys.path.insert(0, str(ROOT))
    from compression_store import clear_cache, content_version
    clear_cache()
    version = content_version()
    report = build_report(include_snapshots=False)
    if content_version() != version:
        raise ValueError('Canonical source changed during inventory audit; retry build.')
    payload = public_summary(report, version)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'inventory-audit.json').write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')), encoding='utf-8')
    return payload


def self_test():
    assert paper_identity({'canonical_url': 'https://arxiv.org/html/2306.00978v6'}) == 'arxiv:2306.00978'
    assert paper_identity({'canonical_url': 'https://arxiv.org/pdf/2306.00978v1.pdf'}) == 'arxiv:2306.00978'
    assert paper_identity({'canonical_url': 'https://doi.org/10.1145/ABC.123'}) == 'doi:10.1145/abc.123'
    assert paper_identity({'canonical_url': 'https://github.com/example/model', 'source_kind': 'repository'}) is None
    assert paper_identity({'canonical_url': 'https://example.org/conference', 'source_kind': 'web'}) is None
    assert paper_identity({'canonical_url': 'https://aclanthology.org/2020.findings-emnlp.372/', 'source_kind': 'paper'}) == 'paper_url:aclanthology.org/2020.findings-emnlp.372'
    assert paper_identity({'canonical_url': 'https://openreview.net/forum?id=PaperA', 'source_kind': 'paper'}) == 'openreview:PaperA'
    assert paper_identity({'canonical_url': 'https://openreview.net/pdf?id=PaperA', 'source_kind': 'paper'}) == 'openreview:PaperA'
    assert paper_identity({'canonical_url': 'https://openreview.net/forum?id=PaperB', 'source_kind': 'paper'}) != 'openreview:PaperA'
    report = build_report(include_snapshots=False)
    assert not report['relationships']['topic_refs_missing_source']
    assert not report['relationships']['topic_refs_missing_card']
    payload = public_summary(report, 'test-version')
    encoded = json.dumps(payload)
    for private_field in ('canonical_url', 'source_id', 'source_provider', 'title_zh', 'cited_paper_identity_values', 'C:\\Users'):
        assert private_field not in encoded
    assert payload['counts']['topic_section_checked_papers'] + payload['counts']['topic_abstract_only_papers'] == payload['counts']['topic_cited_papers']
    print('Inventory identity rules, source/card integrity and aggregate-only export checks passed.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    parser.add_argument('--public-output-dir', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.public_output_dir:
        payload = build(args.public_output_dir)
        print('Public inventory summary generated:', payload['revision'], payload['counts'])
        if not args.output:
            return
    report = build_report()
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        target = args.output if args.output.is_absolute() else ROOT / args.output
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded, encoding='utf-8')
    else:
        print(encoded)
    if args.output:
        print('Inventory audit written:', args.output)


if __name__ == '__main__':
    main()
