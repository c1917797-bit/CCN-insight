"""Merge version-bound monthly reviews into the canonical content tables.

Inputs are reviewed annotations and acquisition receipts, never keyword-generated
technical conclusions. No write occurs until the complete monthly digest validates.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT, DATA, records, rows, manifest, clear_cache, content_version
from monthly_digest import validate_digest

BASE = {'business_id': 'cloud-core', 'topic_id': 'cloud_core'}
OBJECTS = {'parameters': 'W', 'activations': 'A', 'kv_cache': 'K'}
METHODS = {'precision': 'Q', 'selection': 'P', 'distillation': 'D', 'factorization': 'L',
           'merging': 'G', 'kv_eviction': 'S', 'sharing': 'G', 'compact_architecture': 'G'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def short(value):
    return hashlib.sha256(value.encode()).hexdigest()[:16]


class Changes:
    def __init__(self):
        self.metadata = manifest()
        self.definitions = {}
        self.created = set()
        self.changed = {}
        self.tables = {t['name']: {r['key']: r for r in records(t['name'])} for t in self.metadata['tables']}

    def key(self, name):
        return next(t['key_field'] for t in self.metadata['tables'] if t['name'] == name)

    def put(self, name, row):
        assert row.get('business_id') == 'cloud-core'
        assert row.get('topic_id', 'cloud_core') == 'cloud_core'
        key = row[self.key(name)]
        previous = self.tables[name].get(key)
        if previous and previous['row'] == row:
            return
        self.tables[name][key] = {'deleted': False, 'key': key, 'row': row,
                                  'row_version': previous['row_version'] + 1 if previous else 1,
                                  'text_match': None}
        self.changed[name] = True

    def register(self, name, key, sample):
        if name in self.tables:
            return
        fields = {k: {'projection': 'default', 'required': True, 'role': 'key' if k == key else 'value',
                      'source': None, 'type': 'boolean' if type(v) is bool else 'integer' if type(v) is int else 'text'}
                  for k, v in sample.items()}
        self.definitions[name] = {'schema': 'mcpgit.table.v2', 'description': 'Dated discovery metadata and explicit review decisions; recommendations are not first-publication or relevance decisions.',
                                  'key_field': key, 'fields': fields, 'required_fields': list(fields),
                                  'indexes': [{'field': k, 'name': 'idx_' + k} for k in ['period_id', 'scope_id', 'run_id']]}
        self.metadata['tables'].append({'name': name, 'path': 'data/tables/' + name,
            'revision': 'local-monthly-materials-v1', 'source_row_count': 0, 'exported_rows': 0,
            'filters': [], 'rows_file': f'data/compression/tables/{name}/rows.jsonl',
            'import_sha256': '', 'key_field': key, 'provenance_kind': 'local_registered_source_discovery_ledger'})
        self.tables[name] = {}
        self.created.add(name)

    def source(self, url, title, kind, checked, batch):
        stable = re.search(r'arxiv.org/(?:abs|html|pdf)/(\d{4}\.\d{4,5})', url)
        if stable:
            url = 'https://arxiv.org/abs/' + stable.group(1)
        existing = next((r['row'] for r in self.tables['cloud_core_sources'].values()
                         if r['row']['canonical_url'] == url), None)
        if existing:
            return existing['source_id']
        sid = 'source-monthly-' + short(url)
        self.put('cloud_core_sources', {'source_id': sid, 'business_id': 'cloud-core', 'batch_id': batch,
            'canonical_url': url, 'external_id': stable.group(1) if stable else '',
            'last_checked_at': checked, 'provider': url.split('/')[2], 'source_kind': kind,
            'title': title, 'update_policy': 'follow_original_url_record_versions',
            'verification_status': 'primary_abstract_checked' if kind == 'paper' else 'primary_text_checked'})
        return sid

    def values(self):
        return {name: [r['row'] for r in table.values() if not r.get('deleted')] for name, table in self.tables.items()}

    def write(self):
        # Definitions and complete rows are prepared before replacement. Restore
        # previous bytes if any replacement fails; do not leave half an import.
        files = {}
        for name in self.changed:
            path = DATA / 'tables' / name / 'rows.jsonl'
            payload = ''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n'
                              for _, r in sorted(self.tables[name].items())).encode()
            files[path] = payload
            if name in self.definitions:
                files[path.with_name('definition.json')] = (json.dumps(self.definitions[name], ensure_ascii=False, indent=2) + '\n').encode()
                if name in self.created:
                    entry = next(t for t in self.metadata['tables'] if t['name'] == name)
                    entry.update(source_row_count=len(self.tables[name]), exported_rows=len(self.tables[name]), import_sha256=hashlib.sha256(payload).hexdigest())
        files[DATA / 'manifest.json'] = (json.dumps(self.metadata, ensure_ascii=False, indent=2) + '\n').encode()
        before = {path: path.read_bytes() if path.exists() else None for path in files}
        try:
            for path, blob in files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(blob)
        except Exception:
            for path, blob in before.items():
                if blob is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(blob)
            raise
        clear_cache()


def cell_for(topic):
    target, method = topic.split('-', 1)
    return OBJECTS[target] + '_' + METHODS[method]


def prepare(args):
    c = Changes()
    period, cutoff = args.period, args.cutoff
    assert re.fullmatch(r'\d{4}-\d{2}', period) and cutoff.startswith(period)
    scope_id = f'ic-{period}-reviewed-{cutoff.replace("-", "")}-v1'
    run_id = f'collection-{cutoff.replace("-", "")}-monthly-core-v1'
    academic = read(args.academic)
    notes = read(args.english)
    discoveries = read(args.discoveries)
    candidates = {r['paper_id'] for r in read(args.candidates)}
    papers = academic['records'] + academic['observation_candidates']
    if args.supplement:
        extra = read(args.supplement)
        for raw in extra['records']:
            paper = dict(raw, first_published=raw['first_published_at'][:10], version=raw['observed_version'],
                         source_url=raw['evidence_url'], locator=raw['evidence_locator'],
                         question_zh=raw['abstract_summary_zh'], facts_zh=[raw['result_zh'], raw['conditions_zh']],
                         editorial_judgment_zh=raw['increment_zh'])
            paper['english'] = {'question_en': raw['abstract_summary_en'], 'mechanism_en': raw['mechanism_en'],
                'results_en': raw['result_en'], 'boundary_en': raw['boundary_en'],
                'judgment_en': raw.get('judgment_en', raw['boundary_en']),
                'selection_reason_zh': raw['map_reason_zh'], 'selection_reason_en': raw['abstract_summary_en']}
            papers.append(paper)
    assert len({r['paper_id'] for r in papers}) == len(papers)
    meta = {r['paper_id']: r for r in read(args.primary_metadata)}
    digest = read(args.digest)
    assert digest['scope_id'] == scope_id and digest['run_id'] == run_id
    identifiers = {}
    selected = {}
    reviewed = {}
    for position, paper in enumerate(papers):
        pid = paper['paper_id']
        published = paper['first_published']
        assert period + '-01' <= published <= cutoff
        version = paper.get('version', 'v1')
        if pid in meta:
            assert meta[pid]['status'] == 'fetched'
            assert meta[pid]['meta']['citation_date'][0].replace('/', '-') == published, 'Original publication-date mismatch'
            versions = [int(x) for x in re.findall(r'\[v(\d+)\]', ' '.join(meta[pid]['submission_history']))]
            version = 'v' + str(max(versions))
        assert re.fullmatch(r'v[1-9]\d*', version)
        sid = c.source('https://arxiv.org/abs/' + pid, paper['title'], 'paper', cutoff, run_id)
        identifiers[pid] = sid
        section = paper['review_status'] in ['specified_sections', 'method_results_checked', 'original_sections']
        level = 'method_results_checked' if section else 'primary_abstract_checked'
        locator = paper.get('locator') or 'Original abstract and submission history; methods and result tables not reviewed.'
        url = paper.get('source_url', 'https://arxiv.org/abs/' + pid)
        url = re.sub(r'(\d{4}\.\d{4,5})(?:v\d+)?$', r'\g<1>' + version, url)
        text_en = notes.get(pid, paper.get('english', {}))
        assert all(text_en.get(k) for k in ['question_en', 'mechanism_en', 'results_en', 'judgment_en', 'boundary_en'])
        facts = paper.get('facts_zh') or [paper.get('reason_zh', '')]
        question = paper.get('question_zh', paper.get('reason_zh', ''))
        mechanism = paper.get('mechanism_zh', paper.get('reason_zh', ''))
        judgment = paper.get('editorial_judgment_zh', paper.get('reason_zh', ''))
        boundary = paper.get('boundary_zh', paper.get('reason_zh', ''))
        summary_id = sid + '__' + version
        c.put('ic_paper_summaries', {**BASE, 'summary_id': summary_id, 'source_id': sid,
            'observed_version': version, 'background_zh': question, 'background_en': text_en['question_en'],
            'innovation_zh': mechanism, 'innovation_en': text_en['mechanism_en'],
            'one_sentence_zh': paper.get('title_zh', paper['title']), 'one_sentence_en': paper['title'],
            'results_zh': '\n\n'.join(facts), 'results_en': text_en['results_en'],
            'review_status': level, 'reviewed_at': cutoff, 'evidence_locator': locator,
            'evidence_url': url, 'keyword_count': max(1, min(4, len(paper['topic_ids'])))})
        reviewed[pid] = {'source_id': sid, 'observed_version': version, 'review_status': level,
                         'verified_first_published': published, 'review_locator': locator,
                         'evidence_url': url,
                         'decision_zh': text_en.get('selection_reason_zh', judgment)}
        if not paper['topic_ids']:
            c.put('ic_paper_summary_keywords', {**BASE, 'keyword_id': summary_id + '__0',
                'summary_id': summary_id, 'position': 0, 'keyword_zh': '邻接研究', 'keyword_en': 'Adjacent research'})
            reviewed[pid]['selection_status'] = 'adjacent_reviewed'
            continue
        tier = {'priority': 'key_progress', 'watch': 'technical_watch', 'boundary': 'boundary_case'}.get(paper.get('selection_tier'), 'technical_watch')
        reviewed[pid]['selection_status'] = tier
        selected[pid] = paper
        story_id, evidence_id = scope_id + '__' + pid.replace('.', '-'), 'evidence-' + period + '-' + pid + '-' + version
        c.put('ic_evidence_items', {**BASE, 'evidence_id': evidence_id, 'source_id': sid,
            'observed_version': version, 'date_kind': 'first_submission', 'date_precision': 'day',
            'publication_date': published, 'event_date': published, 'verified_at': cutoff,
            'provenance_kind': 'original_arxiv_page_and_recorded_review', 'source_revision': pid + version,
            'status': 'primary_methods_and_results_checked' if section else 'primary_abstract_checked'})
        c.put('ic_paper_summary_events', {**BASE, 'evidence_id': evidence_id, 'source_id': sid, 'summary_id': summary_id, 'observed_version': version, 'period_id': period})
        labels = {r['compression_topic_id']: r for r in c.values()['ic_compression_topics']}
        words = paper['topic_ids'][:4] or ['研究观察']
        for i in range(max(1, min(4, len(paper['topic_ids'])))):
            c.put('ic_paper_summary_keywords', {**BASE, 'keyword_id': summary_id + '__' + str(i), 'summary_id': summary_id, 'position': i, 'keyword_zh': labels[words[i]]['title_zh'], 'keyword_en': labels[words[i]]['title_en']})
        story = {**BASE, 'story_id': story_id, 'scope_id': scope_id, 'period_id': period,
                 'position': position, 'claim_status': 'analyst_synthesis', 'checked_at': cutoff, 'selection_tier': tier}
        for key, zh, en in [('title', paper.get('title_zh', paper['title']), paper['title']),
            ('question', question, text_en['question_en']), ('context', question, text_en['question_en']),
            ('synthesis', mechanism, text_en['mechanism_en']), ('viewpoint', judgment, text_en['judgment_en']),
            ('implication', text_en.get('pending_check_zh', judgment), text_en.get('next_check_en', text_en['judgment_en'])),
            ('boundary', boundary, text_en['boundary_en']),
            ('selection_reason', text_en.get('selection_reason_zh', judgment), text_en.get('selection_reason_en', text_en['judgment_en']))]:
            story[key + '_zh'], story[key + '_en'] = zh, en
        c.put('ic_monthly_route_insights', story)
        for i, topic in enumerate(paper['topic_ids']):
            c.put('ic_compression_topic_events', {**BASE, 'link_id': scope_id + '__' + topic + '__' + evidence_id,
                'scope_id': scope_id, 'period_id': period, 'compression_topic_id': topic, 'scope_topic_key': scope_id + '__' + topic,
                'evidence_id': evidence_id, 'source_id': sid, 'position': position, 'review_status': 'primary_review',
                'reviewed_at': cutoff, 'association_note': mechanism + ' ' + boundary, 'classification_basis': url + ' — ' + locator})
            c.put('ic_monthly_route_evidence', {**BASE, 'ref_id': story_id + '__' + topic, 'story_id': story_id,
                'scope_id': scope_id, 'period_id': period, 'source_id': sid, 'summary_id': summary_id,
                'observed_version': version, 'compression_topic_id': topic, 'evidence_id': evidence_id, 'position': position})
        for cell in {cell_for(t) for t in paper['topic_ids']}:
            c.put('ic_monthly_evidence_cells', {**BASE, 'link_id': scope_id + '__' + evidence_id + '__' + cell,
                'scope_id': scope_id, 'period_id': period, 'evidence_id': evidence_id, 'cell_id': cell,
                'scope_cell_key': scope_id + '__' + cell, 'position': position, 'role': 'direct_mechanism',
                'stage': 'inference_research_candidate', 'status': 'primary_methods_and_results_checked' if section else 'primary_abstract_checked',
                'mechanism_summary': mechanism, 'limitation': boundary, 'validation_question': judgment})
    return c, digest, identifiers, reviewed, selected, papers


def finish(args, c, digest, identifiers, reviewed, selected, papers):
    period, cutoff = args.period, args.cutoff
    scope_id, run_id = digest['scope_id'], digest['run_id']
    observations = read(args.industry)['records']
    notes = read(args.english)
    industry_en = read(args.industry_english)
    grouped = {}
    for observation in observations:
        grouped.setdefault(observation['event_key'], []).append(observation)
    for event, group in grouped.items():
        first = group[0]
        sid = c.source(event, first['source_name'] + ' · ' + first['observed_version'], 'official_release', cutoff, run_id)
        update_id = 'industry-' + period + '-' + short(event)
        meta = first.get('official_publication_metadata') or {}
        release_kind = 'candidate' if meta.get('prerelease') else 'stable' if meta.get('tag') else 'project_progress'
        eligible = first['date_verified'] and first['month_eligible']
        date_value = first['published_at'][:10] if eligible else ''
        change = {**BASE, 'update_id': update_id, 'source_id': sid, 'family_id': first['family_id'],
            'channel_id': first['channel_ids'][0], 'version_label': first['observed_version'],
            'checked_at': cutoff, 'date_locator': 'Official published_at and named release sections; ' + first['evidence_locator'],
            'platform_published_date': date_value, 'release_date': date_value,
            'release_date_kind': 'official_publication' if date_value else 'unknown',
            'release_kind': release_kind if date_value else 'version_documentation', 'review_status': 'primary_text_checked'}
        title_en = ' / '.join(industry_en[r['id']]['title_en'] for r in group)
        for key, zh, en in [('title', '；'.join(r['title_zh'] for r in group), title_en),
            ('summary', ' '.join(r['fact_summary_zh'] for r in group), ' '.join(industry_en[r['id']]['fact_en'] for r in group)),
            ('scope', ' '.join(r['mechanism_zh'] for r in group), ' '.join(industry_en[r['id']]['mechanism_en'] for r in group)),
            ('dependencies', ' '.join(r['conditions_zh'] for r in group), ' '.join(industry_en[r['id']]['conditions_en'] for r in group)),
            ('boundary', ' '.join(r['boundary_zh'] for r in group), ' '.join(industry_en[r['id']]['boundary_en'] for r in group))]:
            change[key + '_zh'], change[key + '_en'] = zh, en
        c.put('ic_industry_updates', change)
        for position, observation in enumerate(group):
            oid, translation = observation['id'], industry_en[observation['id']]
            identifiers['industry:' + oid] = sid
            change_id = update_id + '__' + oid
            c.put('ic_industry_update_changes', {**BASE, 'change_id': change_id, 'update_id': update_id,
                'source_id': sid, 'family_id': first['family_id'], 'position': position,
                'change_kind': observation['classification'], 'checked_at': cutoff,
                'title_zh': observation['title_zh'], 'title_en': translation['title_en'],
                'fact_zh': observation['fact_summary_zh'] + ' ' + observation['result_zh'],
                'fact_en': translation['fact_en'] + ' ' + translation['result_en'],
                'conditions_zh': observation['conditions_zh'], 'conditions_en': translation['conditions_en'],
                'locator': observation['evidence_locator']})
            # GQA/MQA is architectural K/V sharing, distinct from a distributed
            # cache pool, offloading, cache quotas, or service-cache eviction.
            topic_ids = [t for t in observation['suggested_topics'] if t != 'kv_cache-sharing']
            if oid in ['lmcache058-kv-identity', 'mori-nvme-kv', 'mooncake0314-pool', 'vllm34-extensible-kv']:
                topic_ids = []
            relation = 'compression_direct' if observation['classification'] == 'direct_compression' else 'deployment_adjacent'
            for topic in topic_ids:
                link_id = change_id + '__' + topic
                link = {**BASE, 'link_id': link_id, 'update_id': update_id, 'change_id': change_id,
                        'compression_topic_id': topic, 'relation_kind': relation}
                c.put('ic_industry_change_topics', link)
                assessment = {**link, 'source_id': sid, 'position': position, 'claim_kind': 'evidence_based_analysis',
                    'review_status': 'verified', 'review_method': 'primary_passage_topic_causality_review',
                    'reviewed_at': cutoff, 'source_locator': observation['evidence_locator']}
                for key, zh, en in [('title', observation['title_zh'], translation['title_en']),
                    ('fact_focus', observation['fact_summary_zh'], translation['fact_en']),
                    ('relevance', observation['editorial_judgment_zh'], translation['judgment_en']),
                    ('impact', observation['mechanism_zh'], translation['mechanism_en']),
                    ('boundary', observation['boundary_zh'], translation['boundary_en']),
                    ('check', observation['conditions_zh'], translation['conditions_en'])]:
                    assessment[key + '_zh'], assessment[key + '_en'] = zh, en
                c.put('ic_industry_topic_assessments', assessment)
    industry_definition = read(DATA / 'tables/ic_industry_updates/definition.json')
    industry_definition['fields']['review_status'] = {'projection': 'default', 'required': False, 'role': 'value', 'source': None, 'type': 'string'}
    c.definitions['ic_industry_updates'] = industry_definition
    materials = read(args.discoveries)
    candidates = {r['paper_id'] for r in read(args.candidates)}
    for material in materials:
        pid = material['paper_id']
        decision = reviewed.get(pid, {})
        row = {**BASE, 'material_id': scope_id + '__' + pid, 'scope_id': scope_id, 'run_id': run_id,
            'period_id': period, 'paper_id': pid, 'title': material['title'],
            'discovery_dates_json': json.dumps(material['community_dates'], separators=(',', ':')),
            'discovery_url': material['discovery_url'], 'canonical_url': material['canonical_url'],
            'mirror_first_published': material['first_published_mirror'],
            'verified_first_published': decision.get('verified_first_published', ''),
            'source_id': decision.get('source_id', ''), 'observed_version': decision.get('observed_version', ''),
            'keyword_candidate': pid in candidates, 'review_status': decision.get('review_status', 'discovery_only'),
            'selection_status': decision.get('selection_status', 'candidate_pending_primary_review' if pid in candidates else 'keyword_not_matched_not_reviewed'),
            'decision_zh': decision.get('decision_zh', '关键词命中，仅保留发现线索；技术相关性、原始首发日和版本尚未逐篇核实。' if pid in candidates else '未命中本轮关键词；未做原文审阅，不能作为技术排除结论。'),
            'review_locator': decision.get('review_locator', '')}
        c.register('ic_monthly_materials', 'material_id', row)
        c.put('ic_monthly_materials', row)
    assert set(reviewed) <= {r['paper_id'] for r in materials}, 'Reviewed paper missing from saved discovery pool'
    coverage = read(args.source_coverage)
    channels = c.values()['ic_channels']
    good = 0
    for position, entry in enumerate(coverage['records']):
        deferred = entry['status'] == 'handled_by_paged_arxiv_query'
        ok = entry['status'] == 'fetched'
        good += ok
        channel = next(r for r in channels if r['source_id'] == entry['source_id'])
        rid = run_id + '__' + short(entry['registered_url'])
        c.put('ic_channel_retrievals', {**BASE, 'retrieval_id': rid, 'run_id': run_id,
            'channel_id': channel['channel_id'], 'source_id': entry['source_id'], 'position': position,
            'checked_at': entry['fetched_at'], 'status': 'deferred' if deferred else 'success' if ok else 'failure',
            'failure_code': 'arxiv_batch_api_429' if deferred else entry.get('error', ''),
            'http_status': 429 if deferred else entry.get('http_status', 0),
            'method': 'deferred_to_rate_limited_official_batch_query' if deferred else entry['kind'],
            'received_count': entry.get('release_count') or 0, 'candidate_count': 0, 'dated_count': 0, 'undated_count': 0,
            'boundary_zh': '该登记入口未逐页获取；委托的arXiv联合查询返回429，不能计作论文数为零。' if deferred else '本次获取入口或首个官方发布列表；不等于整月内容完整或已经技术研读。必要的后续分页与具体正文另有核查记录。',
            'boundary_en': 'This entry was not paged; the delegated official arXiv query returned 429. This is not a zero-paper result.' if deferred else 'Index or first official-release-page acquisition only; full-month content and technical review are not implied. Follow-up pages and primary texts have separate records.'})
    c.put('ic_collection_runs', {**BASE, 'run_id': run_id, 'requested_channels': len(coverage['records']),
        'attempted_channels': sum(r['status'] != 'handled_by_paged_arxiv_query' for r in coverage['records']),
        'successful_channels': good, 'failed_channels': sum(r['status'] not in ['fetched', 'handled_by_paged_arxiv_query'] for r in coverage['records']),
        'candidate_entries': len(candidates), 'dated_entries': len(materials), 'undated_entries': 0,
        'started_at': min(r['fetched_at'] for r in coverage['records']), 'completed_at': max(r['fetched_at'] for r in coverage['records']),
        'cutoff_date': cutoff, 'status': 'completed_with_gaps', 'scope_note_zh': digest['coverage_zh'], 'scope_note_en': digest['coverage_en']})
    for theme in digest['themes']:
        theme['source_ids'] = list(dict.fromkeys(identifiers[key] for key in theme.pop('source_keys')))
    for comparison in digest['comparisons']:
        comparison['source_ids'] = list(dict.fromkeys(identifiers[key] for key in comparison.pop('source_keys')))
    digest['source_ids'] = list(dict.fromkeys(identifiers.values()))
    digest['citations'] = [{'source_id': r['source_id'], 'observed_version': r['observed_version'],
        'evidence_url': r['evidence_url'], 'locator': r['review_locator'],
        'publication_date': r['verified_first_published'], 'reviewed_at': cutoff} for r in reviewed.values()]
    digest['citations'] += [{'source_id': identifiers['industry:' + group[0]['id']],
        'observed_version': group[0]['observed_version'], 'evidence_url': event,
        'locator': '; '.join(r['evidence_locator'] for r in group),
        'publication_date': group[0]['published_at'][:10] if group[0]['date_verified'] else '',
        'reviewed_at': cutoff} for event, group in grouped.items()]
    digest['adjacent'] = [{'title_zh': p.get('title_zh', p['title']), 'title_en': p['title'],
        'summary_zh': p.get('editorial_judgment_zh', p.get('reason_zh', '')),
        'summary_en': notes.get(p['paper_id'], p.get('english', {}))['judgment_en'],
        'source_ids': [identifiers[p['paper_id']]]} for p in papers if not p['topic_ids']]
    summary = {**BASE, 'scope_id': scope_id, 'period_id': period, 'window_start': period + '-01', 'window_end': cutoff,
        'collected_at': cutoff, 'position': 0, 'status': 'reviewed_sample', 'source_pool': 'registered_core_sources_and_hf_daily_discovery',
        'source_revision': 'version_bound_monthly_review_' + cutoff, 'month_basis': 'verified_primary_event_date',
        'coverage_note': digest['coverage_zh'], 'dedup_rule': '论文按稳定arXiv ID去重；产业按原始发布URL去重；首发、修订、推荐列表日期及核查日期分开。',
        'selection_rule': digest['method_zh'], 'title_zh': period + ' 本月核查与洞察（截至' + cutoff + '）',
        'title_en': period + ' reviewed month-to-date insights (through ' + cutoff + ')',
        'digest_json': json.dumps(digest, ensure_ascii=False, separators=(',', ':'))}
    c.put('ic_monthly_scopes', summary)
    scope_definition = read(DATA / 'tables/ic_monthly_scopes/definition.json')
    scope_definition['fields']['digest_json'] = {'projection': 'default', 'required': False, 'role': 'value', 'source': None, 'type': 'text'}
    c.definitions['ic_monthly_scopes'] = scope_definition
    c.put('ic_trend_periods', {**BASE, 'period_id': period, 'month': period, 'title_zh': period + ' 推理压缩月内洞察',
        'title_en': period + ' month-to-date inference compression insights', 'counting_rule': digest['coverage_zh'],
        'review_status': 'primary_reviewed_month_to_date', 'reviewer_role': '原文摘要及指定章节审阅；非独立复现',
        'source_document_id': '', 'source_name': '已登记的学术、产业与热点信息源', 'source_status': 'ongoing'})
    placements = [r for r in c.values()['ic_monthly_evidence_cells'] if r['scope_id'] == scope_id]
    for cell in c.values()['ic_cells']:
        related = sorted((p for p in placements if p['cell_id'] == cell['cell_id']), key=lambda p: (p['position'], p['evidence_id']))
        c.put('ic_monthly_cell_reviews', {**BASE, 'review_id': scope_id + '__' + cell['cell_id'], 'scope_id': scope_id,
            'period_id': period, 'cell_id': cell['cell_id'], 'scope_cell_key': scope_id + '__' + cell['cell_id'],
            'position': cell['position'], 'reviewed_at': cutoff, 'sample_count': len({r['evidence_id'] for r in related}),
            'status': 'reviewed_sample' if related else 'sample_gap', 'direction': 'not_comparable',
            'change_kind': 'new_evidence' if related else 'collection_gap', 'comparison_scope_id': '',
            'highlight': '；'.join(r['mechanism_summary'] for r in related[:2]) if related else '本轮尚未取得可归入此组合的已核实进展；不表示领域没有成果。',
            'next_question': '回到原文核对模型、格式、恢复预算与真实执行条件；本期材料通过稳定引用关联专题。'})
    result = validate_digest(summary, c.values())
    if args.apply:
        c.write()
    return {'applied': args.apply, 'changed_tables': sorted(c.changed), **result}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['period', 'cutoff', 'academic', 'english', 'discoveries', 'candidates', 'primary-metadata', 'industry', 'industry-english', 'digest', 'source-coverage']:
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--supplement')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    before = content_version()
    changes, digest, identifiers, reviewed, selected, papers = prepare(args)
    if content_version() != before:
        raise SystemExit('Canonical content changed during preparation; refresh before applying')
    print(json.dumps(finish(args, changes, digest, identifiers, reviewed, selected, papers), ensure_ascii=False))
