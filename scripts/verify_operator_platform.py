# -*- coding: utf-8 -*-
"""Audit the operator knowledge graph against maintained facts and built entries.

This is independent of the renderer and the existing reader verifier. It checks
provenance and scope preservation, not scientific truth or device compatibility.
"""
import json
import re
import sys
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'research/ai-infra'
OUT = ROOT / 'dist/ai-infra'
ID = re.compile(r'^[a-z][a-z0-9-]*$')
ROLES = {'mechanism', 'application', 'training_extension', 'crosscutting_method', 'judgment', 'execution_contract'}
HARDWARE = {'gpu', 'ascend', 'other', 'unspecified'}
LEVELS = {'capability', 'kernel', 'stage', 'system', 'training', 'generation'}
METRICS = {'time', 'quality', 'memory', 'coverage', 'bandwidth', 'mechanism'}
BRANCHES = {'compute': ('计算算子加速', 4), 'communication': ('通信算子加速', 5)}
REVIEWED_HARDWARE_SCOPE = {
    # The coverage study spans three platforms; its separate convolution case is H100 only.
    'kernelevolve-coverage': {'gpu', 'other'},
    'kernelevolve-conv-case': {'gpu'},
    # These records explicitly discuss A2/A3/A5 or the reported 950DT stack.
    # This is the material's hardware family, never a claim of user-device adaptation.
    'collectives-topology--sgl-deepep-ascend-api': {'ascend'},
    'paths-buffers--deepseek-deepep-ascend': {'ascend'},
    'compute-communication-overlap--sgl-deepep-ascend-api': {'ascend'},
    'transfer-compression--deepseek-deepep-ascend': {'ascend'},
    'transfer-compression--sgl-deepep-ascend-api': {'ascend'},
}

# These are the five genuinely reviewed editorial changes, not invented history.
# New change types need an explicit scope review rather than keyword-based proof.
LOG_SCOPE = {
    'group-launch': ('受支持', '独立语义', 'pack/unpack'),
    'registration-pxn': ('互斥', '两个完整路径'),
    'fa4-baseline': ('B200', 'cuDNN9.13', '更新版'),
    'int4-consumption': ('Marlin', 'INT4', 'FP16', '不把'),
    'training-boundary': ('训练关联', 'KV', 'MoE', '分别'),
}


def require(value, message):
    if not value:
        raise AssertionError(message)


def load(name):
    path = SOURCE / name
    require(path.is_file(), 'Missing maintained file: ' + name)
    return json.loads(path.read_text(encoding='utf-8'))


def text_fields(row, fields, label):
    require(isinstance(row, dict), label + ': expected object')
    for key in fields:
        require(isinstance(row.get(key), str) and row[key].strip(), label + ': missing ' + key)


def strings(items, label, allowed=None):
    require(isinstance(items, list) and items, label + ': expected nonempty text list')
    require(all(isinstance(item, str) and item.strip() for item in items), label + ': invalid text item')
    require(len(items) == len(set(items)), label + ': duplicate item')
    if allowed is not None:
        require(set(items) <= set(allowed), label + ': unresolved/invalid value ' + repr(set(items) - set(allowed)))
    return set(items)


def keyed(rows, label):
    require(isinstance(rows, list), label + ': expected list')
    keys = [row.get('id') for row in rows]
    require(all(isinstance(key, str) and ID.fullmatch(key) for key in keys), label + ': invalid ID')
    require(len(keys) == len(set(keys)), label + ': duplicate ID')
    return {row['id']: row for row in rows}


def indices(values, size, label):
    require(isinstance(values, list) and values, label + ': expected branch-index list')
    require(all(type(item) is int and 0 <= item < size for item in values), label + ': invalid branch index')
    require(len(values) == len(set(values)), label + ': duplicate branch index')
    return values


def normalized(value):
    return re.sub(r'\s+', ' ', value).strip()


class Node:
    def __init__(self, tag, attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    @property
    def text(self):
        return ' '.join(child.text if isinstance(child, Node) else child for child in self.children)

    def descendants(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.descendants()


class Page(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.root, self.path = Node('document'), path
        self.stack = [self.root]
        self.feed(path.read_text(encoding='utf-8'))
        self.nodes = list(self.root.descendants())
        ids = [node.attrs['id'] for node in self.nodes if 'id' in node.attrs]
        require(len(ids) == len(set(ids)), path.name + ': duplicate HTML ID')
        self.ids = {node.attrs['id']: node for node in self.nodes if 'id' in node.attrs}

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        for pos in range(len(self.stack) - 1, 0, -1):
            if self.stack[pos].tag == tag:
                del self.stack[pos:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def verify():
    corpus = load('operator-routes.json')
    structure = load('operator-research-structure.json')
    log = load('operator-judgment-log.json')
    registry = keyed(load('operator-sources.json')['sources'], 'source registry')
    require(structure.get('schema_version') == log.get('schema_version') == 1, 'Unsupported platform schema')
    text_fields(structure, ['reviewed_at', 'scope'], 'research structure')
    require(date.fromisoformat(structure['reviewed_at']) <= date.today(), 'Structure review date is in the future')
    branches = keyed(corpus['branches'], 'research branches')
    require(set(branches) == set(BRANCHES), 'Confirmed compute/communication split changed')
    routes, approaches, catalogs, facts = {}, {}, {}, {}
    question_ids = []

    def refs(row, field, label):
        return strings(row.get(field), label + '.' + field, registry)

    for branch_id, (title, count) in BRANCHES.items():
        branch = branches[branch_id]
        require(branch['title'] == title and len(branch['routes']) == count, 'Confirmed branch title/count changed: ' + branch_id)
        for route in branch['routes']:
            route_id = route['id']
            require(route_id not in routes and ID.fullmatch(route_id), 'Duplicate/invalid route: ' + route_id)
            routes[route_id] = (route, branch_id)
    require(set(structure.get('routes', {})) == set(routes), 'Structure must cover exactly the nine root mechanisms')
    require(set(structure.get('branch_frames', {})) == set(BRANCHES), 'Missing branch research frames')

    for route_id, (route, branch_id) in routes.items():
        expert, spec = route['expert'], structure['routes'][route_id]
        require('evidence_rows' not in expert, route_id + ': duplicated expert evidence facts must not return')
        local = keyed(expert['branches'], route_id + ' approaches')
        for item in local.values():
            text_fields(item, ['name', 'mechanism', 'tradeoff', 'role'], item['id'])
            require(item['role'] in ROLES, item['id'] + ': unknown knowledge role')
            refs(item, 'evidence_ids', item['id'])
            require(item['id'] not in approaches, 'Duplicate approach ID: ' + item['id'])
            approaches[item['id']] = (item, route_id)
        text_fields(spec, ['research_object', 'direct_change', 'axis_label', 'narrative'], route_id + ' scope')
        strings(spec.get('invariants'), route_id + '.invariants')
        refs(spec, 'source_ids', route_id)
        require(isinstance(spec.get('catalog'), list) and spec['catalog'], route_id + ': no concrete root-mechanism catalog')
        for item in keyed(spec['catalog'], route_id + ' catalog').values():
            text_fields(item, ['title', 'text'], item['id'])
            require(item['id'] not in catalogs, 'Duplicate catalog ID: ' + item['id'])
            refs(item, 'source_ids', item['id'])
            selected = indices(item.get('from_branch_indices'), len(expert['branches']), item['id'])
            require(all(expert['branches'][pos]['role'] == 'mechanism' for pos in selected), item['id'] + ': application/method/judgment must not become a root-catalog mechanism')
            catalogs[item['id']] = (item, route_id, [expert['branches'][pos]['id'] for pos in selected])
        questions = keyed(spec.get('subquestions'), route_id + ' subquestions')
        for item in questions.values():
            text_fields(item, ['title', 'question', 'explanation', 'compare'], item['id'])
            indices(item.get('branch_indices'), len(expert['branches']), item['id'])
            refs(item, 'source_ids', item['id'])
            question_ids.append(item['id'])
        coupling = spec.get('cross_route_condition')
        text_fields(coupling, ['with_route_id', 'relationship', 'condition', 'implication'], route_id + ' coupling')
        require(coupling['with_route_id'] in routes and coupling['with_route_id'] != route_id, route_id + ': invalid cross-mechanism relation')
        refs(coupling, 'source_ids', route_id + ' coupling')
        text_fields(spec.get('trusted_conclusion'), ['claim'], route_id + ' conclusion')
        refs(spec['trusted_conclusion'], 'source_ids', route_id + ' conclusion')
        strings(spec.get('unresolved_questions'), route_id + '.unresolved_questions')
        for group in ['industry', 'academic']:
            for item in keyed(route[group], route_id + ' ' + group).values():
                require(item['id'] not in facts, 'Duplicate maintained record: ' + item['id'])
                text_fields(item, ['title', 'date', 'mechanism', 'conditions', 'result', 'result_type'], item['id'])
                refs(item, 'source_ids', item['id'])
                limit = item.get('boundary', item.get('evidence_scope', ''))
                require(isinstance(limit, str) and limit.strip(), item['id'] + ': missing evidence boundary')
                origin = 'operator-routes.json#/branches/' + branch_id + '/routes/' + route_id + '/' + group + '/' + item['id']
                facts[item['id']] = {'row': item, 'route_id': route_id, 'kind': group, 'origin': origin, 'title': item['title'], 'limit': limit}
    require(len(facts) == 33, 'Expected 33 maintained mechanism evidence records')
    require(len(question_ids) == len(set(question_ids)), 'Duplicate research-subquestion ID')

    for filename, field in [('operator-codegen-named-a.json', 'evidence_rows'), ('operator-codegen-named-b.json', 'evidence'), ('operator-codegen-insight.json', 'evidence')]:
        for item in keyed(load(filename)[field], filename).values():
            require(item['id'] not in facts, 'Duplicate generation evidence ID: ' + item['id'])
            text_fields(item, ['work', 'date', 'mechanism', 'conditions', 'result', 'limit'], item['id'])
            refs(item, 'source_ids', item['id'])
            facts[item['id']] = {'row': item, 'route_id': 'codegen', 'kind': item.get('kind', 'academic'), 'origin': filename + '#/' + field + '/' + item['id'], 'title': item['work'], 'limit': item['limit']}
    require(len(facts) == 45, 'Expected 45 unique records: 33 mechanisms + 12 horizontal-generation records')
    facets = structure.get('evidence_facets')
    require(isinstance(facets, dict) and set(facets) == set(facts), 'Evidence facets contain missing/orphan records')
    for record_id, facet in facets.items():
        require(set(facet) == {'hardware_families', 'level', 'metrics', 'label_basis'}, record_id + ': facets must not silently introduce support assertions')
        strings(facet.get('hardware_families'), record_id + '.hardware_families', HARDWARE)
        strings(facet.get('metrics'), record_id + '.metrics', METRICS)
        require(facet.get('level') in LEVELS, record_id + ': invalid evidence level')
        text_fields(facet, ['label_basis'], record_id + ' facet')
        require(any(boundary in facet['label_basis'] for boundary in ['不表示适配支持', '非跨设备支持证明']), record_id + ': hardware labels must not promise device adaptation')
        if record_id in REVIEWED_HARDWARE_SCOPE:
            require(set(facet['hardware_families']) == REVIEWED_HARDWARE_SCOPE[record_id], record_id + ': hardware facet broadened beyond this reviewed experiment (do not inherit whole-work coverage)')
        if facts[record_id]['route_id'] == 'codegen':
            require(facet['level'] == 'generation', record_id + ': generation evaluation cannot become runtime/model evidence')

    changes = keyed(log.get('changes'), 'judgment revisions')
    require(set(changes) == set(LOG_SCOPE), 'Judgment revisions changed: add an explicit review of new revision scope guards')
    text_fields(log, ['scope'], 'judgment log')
    require('修订' in log['scope'] and '不是' in log['scope'], 'Editorial revisions must not masquerade as publication events')
    for change_id, change in changes.items():
        text_fields(change, ['date', 'trigger_type', 'change_type', 'title', 'before', 'after', 'reason'], change_id)
        require(date.fromisoformat(change['date']) <= date.today(), change_id + ': fabricated future revision')
        require(normalized(change['before']) != normalized(change['after']), change_id + ': revision does not change a judgment')
        strings(change.get('route_ids'), change_id + '.route_ids', set(routes) | {'codegen'})
        strings(change.get('evidence_ids'), change_id + '.evidence_ids', facts)
        require(any(facts[key]['route_id'] in change['route_ids'] for key in change['evidence_ids']), change_id + ': cited evidence is unrelated to all declared mechanisms')
        require(all(term in change['after'] for term in LOG_SCOPE[change_id]), change_id + ': reviewed boundary was removed from the current judgment')

    index_file = OUT / 'operator-evidence-index.json'
    require(index_file.is_file(), 'Build the operator platform before verification: missing ' + str(index_file.relative_to(ROOT)))
    index = json.loads(index_file.read_text(encoding='utf-8'))
    require(index.get('schema_version') == 1 and index.get('reviewed_at') == structure['reviewed_at'], 'Stale/unsupported evidence index version')
    require('do not edit' in index.get('generated_from', ''), 'Derived index must declare its maintained provenance')
    built_routes = keyed(index.get('routes'), 'index routes')
    built_approaches = keyed(index.get('approaches'), 'index approaches')
    built_catalogs = keyed(index.get('mechanisms'), 'index mechanisms')
    built_records = keyed(index.get('records'), 'index records')
    built_sources = keyed(index.get('sources'), 'index sources')
    require(set(built_routes) == set(routes) and set(built_approaches) == set(approaches) and set(built_catalogs) == set(catalogs) and set(built_records) == set(facts), 'Derived entity coverage differs from maintained entities')
    namespaces = list(routes) + list(approaches) + list(catalogs) + list(facts) + list(built_sources) + ['codegen']
    require(len(namespaces) == len(set(namespaces)), 'Entity IDs collide across graph roles')
    for key, row in built_sources.items():
        require(key in registry and row == registry[key], key + ': stale/unknown derived source')
    used_sources = set()
    expected_edges = set()
    for route_id, (route, branch_id) in routes.items():
        row = built_routes[route_id]
        require((row.get('title'), row.get('branch'), row.get('url')) == (route['title'], branch_id, 'operators-' + route_id + '.html'), route_id + ': stale route projection')
    for approach_id, (item, route_id) in approaches.items():
        row = built_approaches[approach_id]
        require((row.get('route_id'), row.get('name'), row.get('role'), row.get('source_ids'), row.get('url')) == (route_id, item['name'], item['role'], item['evidence_ids'], 'operators-' + route_id + '.html#' + approach_id), approach_id + ': stale/role-changing approach projection')
        used_sources.update(item['evidence_ids'])
        expected_edges.add((route_id, 'contains_' + item['role'], approach_id))
    for catalog_id, (item, route_id, parent_ids) in catalogs.items():
        row = built_catalogs[catalog_id]
        require((row.get('route_id'), row.get('title'), row.get('source_ids'), row.get('approach_ids'), row.get('url')) == (route_id, item['title'], item['source_ids'], parent_ids, 'operators-' + route_id + '.html#' + catalog_id), catalog_id + ': stale catalog projection')
        used_sources.update(item['source_ids'])
        expected_edges.add((route_id, 'contains_mechanism', catalog_id))
        expected_edges.update((key, 'explains', catalog_id) for key in parent_ids)
    urls, origins = [], []
    for record_id, fact in facts.items():
        row, original = built_records[record_id], fact['row']
        expected = {'route_id': fact['route_id'], 'title': fact['title'], 'kind': fact['kind'], 'date': original['date'], 'limit': fact['limit'], 'canonical_origin': fact['origin'], 'facets': facets[record_id], 'source_ids': original['source_ids']}
        expected.update({field: original[field] for field in ['mechanism', 'conditions', 'result']})
        expected['result_type'] = original['result_type'] if fact['route_id'] != 'codegen' else '生成与调优评测'
        expected['url'] = ('operators-codegen.html#evidence-' if fact['route_id'] == 'codegen' else 'operators-' + fact['route_id'] + '.html#record-') + record_id
        for field, value in expected.items():
            require(row.get(field) == value, record_id + ': projection changed maintained ' + field)
        associated = {key for key, (approach, route_id) in approaches.items() if route_id == fact['route_id'] and set(approach['evidence_ids']) & set(original['source_ids'])}
        require(isinstance(row.get('approach_ids'), list) and len(row['approach_ids']) == len(set(row['approach_ids'])) and set(row['approach_ids']) == associated, record_id + ': stale/invalid source association (not causal proof)')
        used_sources.update(original['source_ids'])
        urls.append(row['url'])
        origins.append(row['canonical_origin'])
        expected_edges.add((record_id, 'belongs_to', fact['route_id']))
        expected_edges.update((record_id, 'associated_with', key) for key in associated)
        expected_edges.update((record_id, 'cites', key) for key in original['source_ids'])
    require(len(urls) == len(set(urls)) and len(origins) == len(set(origins)), 'Each evidence record needs one distinct canonical entry and maintained origin')
    require(set(built_sources) == used_sources, 'Derived sources do not resolve all record/approach/catalog evidence')
    raw_edges = index.get('relations')
    require(isinstance(raw_edges, list), 'Missing typed relations')
    actual_edges = [(edge.get('from'), edge.get('relation'), edge.get('to')) for edge in raw_edges]
    require(len(actual_edges) == len(set(actual_edges)), 'Duplicate graph relation')
    require(set(actual_edges) == expected_edges, 'Typed graph has missing, stale or role-invalid relations')

    pages = {}

    def page_for(url, need_anchor=True):
        parsed = urlsplit(url)
        require(not parsed.scheme and not parsed.netloc and not parsed.query, 'Canonical entry must be a local static URL: ' + url)
        target = (OUT / unquote(parsed.path)).resolve()
        require(OUT.resolve() in target.parents and target.is_file() and target.suffix == '.html', 'Missing/escaping canonical page: ' + url)
        if target not in pages:
            pages[target] = Page(target)
        page = pages[target]
        if need_anchor:
            require(parsed.fragment and unquote(parsed.fragment) in page.ids, 'Missing canonical anchor: ' + url)
            return page.ids[unquote(parsed.fragment)]
        return page

    active_urls = ['operators.html', 'operators-1.html', 'operators-2.html', 'operators-codegen.html'] + [built_routes[key]['url'] for key in routes]
    require(len(set(active_urls)) == 13, 'Expected thirteen active research readers')
    for url in active_urls:
        page_for(url, False)
    for catalog_id, (item, route_id, _) in catalogs.items():
        node = page_for(built_catalogs[catalog_id]['url'])
        require(normalized(item['title']) in normalized(node.text) and normalized(item['text']) in normalized(node.text), catalog_id + ': catalog anchor lacks its maintained mechanism explanation')
    for approach_id, (item, _) in approaches.items():
        node = page_for(built_approaches[approach_id]['url'])
        require(node.attrs.get('data-approach-role') == item['role'], approach_id + ': rendered knowledge role differs from its maintained role')
        require(all(normalized(item[field]) in normalized(node.text) for field in ['name', 'mechanism', 'tradeoff']), approach_id + ': incomplete concrete-approach explanation')
    canonical_anchors = Counter()
    for page in pages.values():
        require(not any(node.tag in {'details', 'summary'} for node in page.nodes), page.path.name + ': knowledge must stay expanded')
        canonical_anchors.update(key for key in page.ids if key.startswith(('record-', 'evidence-')))
    for record_id, row in built_records.items():
        node = page_for(row['url'])
        anchor = unquote(urlsplit(row['url']).fragment)
        require(canonical_anchors[anchor] == 1, record_id + ': evidence must have exactly one full canonical HTML entry across active pages')
        require(all(normalized(row[field]) in normalized(node.text) for field in ['title', 'mechanism', 'conditions', 'result', 'limit']), record_id + ': canonical entry dropped facts or applicability boundaries')
    overview = page_for('operators.html', False)
    trees = [node for node in overview.nodes if 'op-tech-tree' in node.attrs.get('class', '').split()]
    leaf_links = [node.attrs.get('href') for tree in trees for node in tree.descendants() if node.tag == 'a' and urlsplit(node.attrs.get('href', '')).fragment]
    require(set(leaf_links) == {row['url'] for row in built_catalogs.values()}, 'Root taxonomy must contain catalog leaves only, not methods/applications/judgments')
    library = [node for node in overview.nodes if 'data-library-record' in node.attrs]
    require(len(library) == len(facts) and {node.attrs['data-library-record'] for node in library} == set(facts), 'Evidence library coverage is stale or duplicated')
    for node in library:
        row = built_records[node.attrs['data-library-record']]
        links = [child.attrs.get('href') for child in node.descendants() if child.tag == 'a']
        require(row['url'] in links and normalized(row['result']) in normalized(node.text), row['id'] + ': library must project and link to the canonical fact')
        require(node.attrs.get('data-route') == row['route_id'] and node.attrs.get('data-level') == row['facets']['level'], row['id'] + ': library filter metadata differs from maintained facets')
        require(set(node.attrs.get('data-hardware', '').split()) == set(row['facets']['hardware_families']) and set(node.attrs.get('data-metric', '').split()) == set(row['facets']['metrics']), row['id'] + ': stale hardware/metric filter facets')
    require('范围标签不代表目标设备已适配' in overview.root.text, 'Evidence filters must not imply device support')
    for change_id, change in changes.items():
        require('change-' + change_id in overview.ids, change_id + ': judgment revision missing from the overview')
        node = overview.ids['change-' + change_id]
        require(all(normalized(change[field]) in normalized(node.text) for field in ['before', 'after', 'reason', 'date', 'trigger_type']), change_id + ': rendered revision changes editorial history')
        links = {child.attrs.get('href') for child in node.descendants() if child.tag == 'a'}
        require({built_records[key]['url'] for key in change['evidence_ids']} <= links, change_id + ': judgment revision lacks its supporting canonical evidence')
    print('PASS: operator platform: 9 typed root routes; ' + str(len(catalogs)) + ' catalog leaves / ' + str(len(approaches)) + ' role-separated approaches; 45 canonical records (33+12); exact fact/index joins, unique entries, typed relations, five bounded editorial revisions and library projections')
    print('Scope: provenance/role/boundary checks only; no new hardware support or device-performance claim is established by this test.')


if __name__ == '__main__':
    try:
        verify()
    except (AssertionError, KeyError, TypeError, ValueError) as error:
        print('FAIL: operator platform: ' + str(error), file=sys.stderr)
        sys.exit(1)
