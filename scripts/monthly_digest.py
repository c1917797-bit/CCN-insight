"""Validate a dated monthly synthesis and export its public discovery ledger.

The ledger stores publication metadata and review decisions, never acquired
abstracts or a claim that a recommendation list is a field-wide paper census.
"""
from __future__ import annotations
import calendar
import csv
import datetime as dt
import io
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compression_store import rows, manifest

MATERIAL_TABLE = 'ic_monthly_materials'
ROOT_IDS = {'precision', 'selection', 'distillation', 'factorization'}


def date(value):
    if not isinstance(value, str) or dt.date.fromisoformat(value).isoformat() != value:
        raise ValueError('Invalid calendar date')
    return value


def validate_digest(scope, tables):
    d = json.loads(scope['digest_json'])
    if d.get('schema') != 'ccn.monthly-digest.v1':
        raise ValueError('Unknown monthly digest contract')
    period, cutoff = scope['period_id'], date(d['cutoff'])
    if d['period_id'] != period or d['scope_id'] != scope['scope_id']:
        raise ValueError('Digest does not belong to the scope')
    if d['window_start'] != period + '-01' or cutoff != scope['window_end'] or not cutoff.startswith(period):
        raise ValueError('Digest window mismatch')
    year, month = map(int, period.split('-'))
    if cutoff > f'{period}-{calendar.monthrange(year, month)[1]:02d}':
        raise ValueError('Digest extends outside its month')
    source_ids = set(d['source_ids'])
    if len(source_ids) != len(d['source_ids']):
        raise ValueError('Duplicate digest source')
    sources = {r['source_id']: r for r in tables['cloud_core_sources']}
    topics = {r['compression_topic_id'] for r in tables['ic_compression_topics']}
    for source_id in source_ids:
        source = sources[source_id]
        u = urlsplit(source['canonical_url'])
        if u.scheme != 'https' or not u.hostname or u.username or u.password:
            raise ValueError('Invalid primary-source URL')
    citation_ids = set()
    for citation in d['citations']:
        sid = citation['source_id']
        if sid not in source_ids or sid in citation_ids or not citation['locator']:
            raise ValueError('Missing or duplicate citation provenance')
        citation_ids.add(sid)
        if 'arxiv.org/abs/' in sources[sid]['canonical_url']:
            summary = next((r for r in tables['ic_paper_summaries'] if r['summary_id'] == sid + '__' + citation['observed_version']), None)
            if not summary or summary['evidence_url'] != citation['evidence_url']:
                raise ValueError('Digest paper citation version mismatch')
    if citation_ids != source_ids:
        raise ValueError('Digest source without a citation record')
    for field in ['title', 'thesis', 'coverage', 'method', 'limits']:
        if any(not d.get(field + '_' + lang, '').strip() for lang in ['zh', 'en']):
            raise ValueError('Incomplete monthly synthesis: ' + field)
    seen = set()
    for theme in d['themes']:
        if theme['id'] in seen or theme['status'] not in ['reviewed_evidence', 'coverage_gap']:
            raise ValueError('Invalid monthly theme')
        seen.add(theme['id'])
        if not set(theme['source_ids']) <= source_ids or not set(theme['topic_ids']) <= topics:
            raise ValueError('Unresolved monthly theme reference')
        if theme['status'] == 'reviewed_evidence' and not theme['source_ids']:
            raise ValueError('An evidence-backed theme needs a primary source')
        for field in ['title', 'change', 'judgment', 'boundary', 'next_check']:
            if any(not theme.get(field + '_' + lang, '').strip() for lang in ['zh', 'en']):
                raise ValueError('Incomplete theme: ' + field)
    if not ROOT_IDS <= seen:
        raise ValueError('The four root techniques must be accounted for, including explicit gaps')
    for item in d['comparisons']:
        if not set(item['source_ids']) <= source_ids:
            raise ValueError('Unresolved comparison source')
        for f in ['question_zh', 'question_en', 'answer_zh', 'answer_en']:
            if not item.get(f, '').strip():
                raise ValueError('Incomplete comparison')
    materials = [r for r in tables[MATERIAL_TABLE] if r['scope_id'] == scope['scope_id']]
    if len({r['paper_id'] for r in materials}) != len(materials):
        raise ValueError('Duplicate paper in the discovery ledger')
    for row in materials:
        if row['period_id'] != period or row['run_id'] != d['run_id']:
            raise ValueError('Material scope mismatch')
        dates = json.loads(row['discovery_dates_json'])
        if not dates or any(not period + '-01' <= date(x) <= cutoff for x in dates):
            raise ValueError('Material not discovered within the recorded window')
        if row['review_status'] not in ['discovery_only', 'primary_abstract_checked', 'method_results_checked']:
            raise ValueError('Unknown reading depth')
        if row['review_status'] != 'discovery_only':
            date(row['verified_first_published'])
            if not row['source_id'] or row['source_id'] not in sources or not row['review_locator']:
                raise ValueError('Reviewed material lacks original evidence')
        if row['selection_status'] in ['key_progress', 'technical_watch', 'boundary_case']:
            if row['review_status'] == 'discovery_only' or not row['verified_first_published'].startswith(period):
                raise ValueError('Unverified or earlier paper promoted to this month')
    stories = [r for r in tables['ic_monthly_route_insights'] if r['scope_id'] == scope['scope_id']]
    bindings = [r for r in tables['ic_monthly_route_evidence'] if r['scope_id'] == scope['scope_id']]
    selected = {r['source_id'] for r in bindings}
    eligible = [r for r in tables['ic_industry_updates'] if r['release_date'].startswith(period) and r['release_date'] <= cutoff]
    # Counts are independently recomputed; observations within one release do not
    # become additional publications, and list acquisition is not paper reading.
    expected = {
        'discovered': len(materials),
        'keyword_candidates': sum(r['keyword_candidate'] for r in materials),
        'primary_checked': sum(r['review_status'] != 'discovery_only' for r in materials),
        'section_checked': sum(r['review_status'] == 'method_results_checked' for r in materials),
        'curated_papers': len(selected),
        'industry_events': len({r['source_id'] for r in eligible}),
    }
    metrics = {m['key']: m['count'] for m in d['metrics']}
    for key, count in metrics.items():
        if key not in expected or type(count) is not int or count != expected[key]:
            raise ValueError(f'Unreconciled digest count: {key} = {count}, actual {expected.get(key)}')
    if len(stories) != len(selected):
        raise ValueError('The monthly selection must retain one story per reviewed paper')
    return {'period': period, 'scope': scope['scope_id'], **expected}


def canonical_tables():
    names = ['ic_monthly_scopes', 'cloud_core_sources', 'ic_compression_topics',
             'ic_monthly_route_insights', 'ic_monthly_route_evidence',
             'ic_industry_updates', 'ic_channel_retrievals', 'ic_paper_summaries']
    if any(t['name'] == MATERIAL_TABLE for t in manifest()['tables']):
        names.append(MATERIAL_TABLE)
    return {name: rows(name) for name in names}


def validate_canonical():
    tables = canonical_tables()
    return [validate_digest(scope, tables) for scope in tables['ic_monthly_scopes'] if scope.get('digest_json')]


def csv_text(matrix):
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    for values in matrix:
        writer.writerow(["'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@')) else v for v in values])
    return '\ufeff' + stream.getvalue()


def export_ledgers(output):
    tables = canonical_tables()
    for scope in tables['ic_monthly_scopes']:
        if not scope.get('digest_json'):
            continue
        validate_digest(scope, tables)
        digest = json.loads(scope['digest_json'])
        materials = [r for r in tables[MATERIAL_TABLE] if r['scope_id'] == scope['scope_id']]
        matrix = [['论文ID', '标题', '发现日期列表', '发现入口', '发现入口publishedAt（未核实原始首发）', '原文核实首发日期', '关键词命中', '阅读层级', '选择状态', '理由或核查边界', '原文', '版本', '核查定位']]
        for r in sorted(materials, key=lambda r: (not r['keyword_candidate'], r['paper_id'])):
            matrix.append([r['paper_id'], r['title'], '; '.join(json.loads(r['discovery_dates_json'])), r['discovery_url'], r['mirror_first_published'], r['verified_first_published'], r['keyword_candidate'], r['review_status'], r['selection_status'], r['decision_zh'], r['canonical_url'], r['observed_version'], r['review_locator']])
        coverage = [['信息入口', '状态', 'HTTP状态', '采集方式', '保留条目数', '核查时间', '覆盖边界']]
        sources = {r['source_id']: r for r in tables['cloud_core_sources']}
        for r in sorted((r for r in tables['ic_channel_retrievals'] if r['run_id'] == digest['run_id']), key=lambda r: r['position']):
            coverage.append([sources[r['source_id']]['canonical_url'], r['status'], r['http_status'], r['method'], r['received_count'], r['checked_at'], r['boundary_zh']])
        output = Path(output)
        output.mkdir(parents=True, exist_ok=True)
        for name, data in [('materials', matrix), ('coverage', coverage)]:
            (output / f'{scope["period_id"]}-{name}.csv').write_bytes(csv_text(data).encode('utf-8'))


if __name__ == '__main__':
    print(json.dumps(validate_canonical(), ensure_ascii=False))
