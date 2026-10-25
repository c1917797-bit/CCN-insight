# -*- coding: utf-8 -*-
"""Verify operator research contracts, evidence joins and built-page navigation."""
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'research/ai-infra'
DIST = ROOT / 'dist'
OUT = DIST / 'ai-infra'
PAGES = ['operators.html', 'operators-1.html', 'operators-2.html', 'operators-codegen.html']
BRANCHES = {'compute': ('计算算子加速', 4), 'communication': ('通信算子加速', 5)}
ROUTE_SECTIONS = ['brief', 'background', 'principles', 'challenges', 'progress', 'comparison', 'practice', 'conclusion']
PRIMARY_ROUTE_SECTIONS = ['brief', 'background', 'principles', 'challenges', 'progress', 'comparison', 'practice']
SUBORDINATE_ROUTE_SECTIONS = ['conclusion']
SOURCE_KINDS = {'primary_paper', 'official_documentation', 'official_historical_documentation', 'official_project_repository', 'official_repository', 'official_repository_documentation', 'official_project_documentation', 'official_project_repository_documentation'}
ID = re.compile(r'^[a-z][a-z0-9-]*$')


def require(test, message):
    if not test:
        raise AssertionError(message)


def text_fields(row, fields, label):
    require(isinstance(row, dict), label + ': expected object')
    for field in fields:
        require(isinstance(row.get(field), str) and row[field].strip(), label + ': missing ' + field)


def nonempty_list(value, label):
    require(isinstance(value, list) and value, label + ': expected nonempty list')
    require(all(isinstance(item, str) and item.strip() for item in value), label + ': empty/nontext item')
    require(len(value) == len(set(value)), label + ': duplicate item')


def unique(rows, field, label):
    values = [row.get(field) for row in rows]
    require(all(isinstance(value, str) and ID.fullmatch(value) for value in values), label + ': invalid ID')
    require(len(values) == len(set(values)), label + ': duplicate ID')
    return set(values)


def load(name):
    return json.loads((RESEARCH / name).read_text(encoding='utf-8'))


def normalized(text):
    return re.sub(r'\s+', ' ', text).strip()


def has_class(node, name):
    return name in node.attrs.get('class', '').split()


class Element:
    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs or [])
        self.children = []

    @property
    def text(self):
        return ' '.join(item.text if isinstance(item, Element) else item for item in self.children)

    def descendants(self):
        for child in self.children:
            if isinstance(child, Element):
                yield child
                yield from child.descendants()


class Page(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.raw = path.read_text(encoding='utf-8')
        self.root = Element('document')
        self.stack = [self.root]
        self.feed(self.raw)
        self.nodes = list(self.root.descendants())
        ids = [node.attrs['id'] for node in self.nodes if 'id' in node.attrs]
        repeated = [key for key, count in Counter(ids).items() if count > 1]
        require(not repeated, str(path.relative_to(DIST)) + ': duplicate IDs ' + repr(repeated))
        self.ids = {node.attrs['id']: node for node in self.nodes if 'id' in node.attrs}
        self.links = [node for node in self.nodes if node.tag == 'a' and node.attrs.get('href')]

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Element(tag, attrs))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)


def verify():
    evidence = load('operator-sources.json')
    routes = load('operator-routes.json')
    prior = load('operator-310p-prior.json') if (RESEARCH / 'operator-310p-prior.json').is_file() else None
    case = load('operator-cannbot-case.json')
    codegen = load('operator-codegen-insight.json')
    hardware = load('operator-codegen-hardware.json')
    named_a = load('operator-codegen-named-a.json')
    named_b = load('operator-codegen-named-b.json')
    guide = load('operator-expert-guide.json')
    for name, data, date_field in [('sources', evidence, 'reviewed_at'), ('routes', routes, 'updated_at')]:
        require(data.get('schema_version') == 1, name + ': unsupported schema')
        require(re.fullmatch(r'\d{4}-\d{2}-\d{2}', data.get(date_field, '')), name + ': missing review date')
    require(isinstance(evidence.get('sources'), list) and evidence['sources'], 'Missing operator sources')
    source_ids = unique(evidence['sources'], 'id', 'operator sources')
    sources = {row['id']: row for row in evidence['sources']}
    for row in sources.values():
        text_fields(row, ['title', 'url', 'kind', 'review_scope', 'device_scope', 'boundary'], row['id'])
        require(row['kind'] in SOURCE_KINDS, row['id'] + ': unsupported evidence kind')
        url = urlsplit(row['url'])
        require(url.scheme == 'https' and url.hostname and not url.username and not url.password, row['id'] + ': invalid public evidence URL')

    def check_evidence_joins(value, label):
        if isinstance(value, list):
            for index, item in enumerate(value):
                check_evidence_joins(item, label + '[' + str(index) + ']')
        elif isinstance(value, dict):
            for key, item in value.items():
                if key in {'source_ids', 'evidence_ids'}:
                    nonempty_list(item, label + '.' + key)
                    require(set(item) <= source_ids, label + ': unresolved maintained source')
                else:
                    check_evidence_joins(item, label + '.' + key)

    for label, data in [('CannBot case', case), ('codegen insight', codegen), ('hardware', hardware), ('named systems A', named_a), ('named systems B', named_b)]:
        require(isinstance(data, dict), label + ': expected maintained object')
        date = data.get('reviewed_at', data.get('updated_at', ''))
        require(re.fullmatch(r'\d{4}-\d{2}-\d{2}', date), label + ': missing review/update date')
        require(data.get('schema_version', 1) == 1, label + ': unsupported schema')
        check_evidence_joins(data, label)
        for field in ['source_additions', 'source_review_updates']:
            for source_row in data.get(field, []):
                key = source_row.get('id')
                require(key in sources, label + ': unmerged source ' + str(key))
                require(source_row.get('url') == sources[key]['url'] and source_row.get('kind') == sources[key]['kind'], label + ': source identity differs from maintained registry ' + key)
    text_fields(case, ['title', 'lead', 'scope', 'formula', 'contract', 'template_review'], 'CannBot case')
    require('教学' in case['scope'] and '没有' in case['scope'] and '测试' in case['scope'], 'CannBot teaching case lost its no-execution boundary')
    require(isinstance(case.get('concepts'), list) and len(case['concepts']) == 8, 'CannBot case requires eight explained concepts')
    unique(case['concepts'], 'id', 'CannBot concepts')
    for concept in case['concepts']:
        text_fields(concept, ['name', 'term', 'question', 'explanation', 'where'], 'CannBot concept')
    require(isinstance(case.get('route_links'), list) and len(case['route_links']) == 4, 'CannBot case must connect the four compute mechanisms')
    require(len({row.get('route_id') for row in case['route_links']}) == 4, 'CannBot case repeats a mechanism')
    for row in case['route_links']:
        text_fields(row, ['route_id', 'name', 'observation', 'action'], 'CannBot mechanism join')
    require(isinstance(case.get('judgments'), list) and case['judgments'], 'CannBot case missing mechanism judgments')
    for row in case['judgments']:
        text_fields(row, ['title', 'text'], 'CannBot judgment')
    text_fields(case.get('fusion'), ['title', 'formula', 'description', 'preserved_output', 'internal_only', 'precision'], 'CannBot fusion case')
    text_fields(case.get('engineering'), ['title', 'text', 'migration'], 'CannBot engineering boundary')
    for field, fields in [('hardware_rows', ['topic', 'gpu', 'npu', 'implication']), ('methods', ['id', 'title', 'mechanism', 'limit'])]:
        require(isinstance(codegen.get(field), list) and codegen[field], 'Codegen missing ' + field)
        for row in codegen[field]:
            text_fields(row, fields, 'Codegen ' + field)
    unique(codegen['methods'], 'id', 'Codegen methods')
    for field, fields in [('platforms', ['title', 'subtitle', 'note']), ('tools', ['name', 'role', 'support', 'implication']), ('implications', ['dimension', 'title', 'insight', 'meaning', 'boundary'])]:
        require(isinstance(hardware.get(field), list) and hardware[field], 'Hardware missing ' + field)
        for row in hardware[field]:
            text_fields(row, fields, 'Hardware ' + field)
            if field == 'platforms':
                nonempty_list(row.get('nodes'), 'Hardware platform nodes')
    codegen_rows = named_a.get('evidence_rows', []) + named_b.get('evidence', []) + codegen.get('evidence', [])
    require(codegen_rows and all(isinstance(row, dict) for row in codegen_rows), 'Codegen missing named-system evidence')
    unique(codegen_rows, 'id', 'Codegen evidence')
    for row in codegen_rows:
        text_fields(row, ['platform', 'work', 'date', 'mechanism', 'conditions', 'result', 'limit'], 'Codegen evidence ' + row['id'])
    require(len(codegen_rows) == 12, 'Generation insight must retain its twelve reviewed evidence records')
    projects = codegen.get('project_comparisons')
    require(isinstance(projects, list) and len(projects) == 5, 'Generation insight must retain its five named systems')
    require({row.get('name') for row in projects} == {'KernelEvolve', 'KernelBlaster', 'AVO', 'CUDA Agent', 'AscendOptimizer'}, 'Generation insight changed its reviewed named-system coverage')
    codegen_evidence_ids = {row['id'] for row in codegen_rows}
    for row in projects:
        text_fields(row, ['name', 'method', 'hardware', 'learn', 'limit', 'evidence_id'], 'Generation system comparison')
        require(row['evidence_id'] in codegen_evidence_ids, 'Generation system comparison has no reviewed evidence')
    text_fields(hardware, ['transfer_note'], 'Hardware implications')
    text_fields(codegen, ['summary', 'judgment', 'scope', 'update_principle'], 'Generation insight')
    require(isinstance(codegen.get('conclusions'), list) and codegen['conclusions'], 'Generation insight missing maintained conclusions')
    for row in codegen['conclusions']:
        text_fields(row, ['title', 'text'], 'Generation conclusion')

    require(isinstance(routes.get('branches'), list), 'Missing operator branches')
    branch_ids = unique(routes['branches'], 'id', 'operator branches')
    require(branch_ids == set(BRANCHES), 'Root split must remain compute/communication')
    all_routes = []
    for branch in routes['branches']:
        title, count = BRANCHES[branch['id']]
        text_fields(branch, ['title', 'summary', 'judgment'], branch['id'])
        require(branch['title'] == title, branch['id'] + ': changed confirmed second-level title')
        require(isinstance(branch.get('routes'), list) and len(branch['routes']) == count, title + ': wrong mechanism count')
        all_routes.extend(branch['routes'])
        for row in branch['routes']:
            text_fields(row, ['id', 'title', 'challenge', 'principle', 'boundary', 'judgment', 'principle_formula'], title)
            for field in ['actions', 'metrics', 'source_ids', 'research_questions']:
                nonempty_list(row.get(field), row['id'] + '.' + field)
            require(set(row['source_ids']) <= source_ids, row['id'] + ': unresolved evidence reference')
            selection = row.get('selection')
            require(isinstance(selection, dict), row['id'] + ': missing comparison conditions')
            for field in ['suitable', 'unsuitable']:
                nonempty_list(selection.get(field), row['id'] + '.selection.' + field)
            for group in ['industry', 'academic']:
                entries = row.get(group)
                require(isinstance(entries, list) and entries, row['id'] + ': missing ' + group + ' evidence')
                titles = []
                for entry in entries:
                    label = row['id'] + '.' + group
                    text_fields(entry, ['title', 'mechanism', 'date', 'conditions', 'result'], label)
                    require(any(isinstance(entry.get(field), str) and entry[field].strip() for field in ['boundary', 'evidence_scope']), label + ': missing applicability/review limit')
                    nonempty_list(entry.get('source_ids'), label + '.source_ids')
                    require(set(entry['source_ids']) <= source_ids, label + ': unresolved evidence reference')
                    titles.append(entry['title'])
                require(len(titles) == len(set(titles)), row['id'] + '.' + group + ': repeated entry title')
            expert = row.get('expert')
            text_fields(expert, ['id', 'title', 'brief', 'conclusion', 'bottleneck_signal'], row['id'] + '.expert')
            require(expert['id'] == row['id'] and expert['title'] == row['title'], row['id'] + ': expert content belongs to another mechanism')
            require(normalized(expert['conclusion']) != normalized(row['judgment']), row['id'] + ': conclusion must add a decision beyond the opening judgment')
            techniques = expert.get('branches')
            require(isinstance(techniques, list) and len(techniques) >= 2, row['id'] + ': require at least two named technical approaches')
            for technique in techniques:
                text_fields(technique, ['name', 'mechanism', 'tradeoff'], row['id'] + '.expert.branches')
                nonempty_list(technique.get('evidence_ids'), row['id'] + '.expert.branches.evidence_ids')
                require(set(technique['evidence_ids']) <= source_ids, row['id'] + ': unresolved technique evidence')
            require(len({normalized(item['name']) for item in techniques}) == len(techniques), row['id'] + ': repeated named approach')
            # Facts have one maintained home. The platform index derives its
            # evidence projection from industry/academic; retaining a second
            # copy here would reintroduce the drift this contract prevents.
            require('evidence_rows' not in expert, row['id'] + ': expert.evidence_rows is a forbidden duplicate of industry/academic facts')
            check_evidence_joins(expert, row['id'] + '.expert')
    unique(all_routes, 'id', 'mechanism routes')
    require(set(guide.get('routes', {})) == {row['id'] for row in all_routes}, 'Expert guide must cover the nine maintained mechanisms')
    check_evidence_joins(guide, 'expert guide')
    for route in all_routes:
        entry=guide['routes'][route['id']]
        text_fields(entry,['delta','tradeoff','priority','decision','reversal'],route['id']+'.guide')
        nonempty_list(entry.get('search_terms'),route['id']+'.search_terms')
        for row in route['industry']+route['academic']:
            text_fields(row,['result_type'],route['id']+'.evidence classification')
    compute_ids = {row['id'] for branch in routes['branches'] if branch['id'] == 'compute' for row in branch['routes']}
    require({row['route_id'] for row in case['route_links']} == compute_ids, 'CannBot route joins differ from the compute taxonomy')

    if prior is not None:
        text_fields(prior, ['title', 'summary'], '310P prior report')
        text_fields(prior.get('source'), ['filename', 'sha256', 'assessment', 'scope'], '310P source')
        source = prior['source']
        require('/' not in source['filename'] and '\\' not in source['filename'] and source['filename'].endswith('.pptx'), 'PPT trace must use its basename')
        require(re.fullmatch(r'[0-9a-f]{64}', source['sha256']), 'Invalid PPT SHA256')
        require('静态分析' in source['assessment'] and all(word in source['assessment'] for word in ['未执行', 'CANN', '仿真', '真机']), 'Static-review/no-execution boundary missing')
        require(isinstance(prior.get('capabilities'), list) and len(prior['capabilities']) == 6, 'Require six prior-report capabilities')
        unique(prior['capabilities'], 'id', '310P capabilities')
        for row in prior['capabilities']:
            text_fields(row, ['title', 'mechanism', 'current_state', 'limit'], row['id'])
            slides = row.get('slides')
            require(isinstance(slides, list) and slides and all(type(n) is int and 1 <= n <= 12 for n in slides), row['id'] + ': invalid slide reference')
            require(len(slides) == len(set(slides)), row['id'] + ': repeated slide')
            nonempty_list(row.get('locators'), row['id'] + '.locators')
            for locator in row['locators']:
                require(not locator.startswith(('/', '\\')) and not re.match(r'^[A-Za-z]:', locator) and '..' not in locator.split('/'), row['id'] + ': locator must remain relative to the source package')
        require(isinstance(prior.get('gaps'), list) and prior['gaps'], 'Missing prior-report gaps')
        for gap in prior['gaps']:
            text_fields(gap, ['title', 'why', 'action', 'acceptance'], '310P gap')
        require(len({gap['title'] for gap in prior['gaps']}) == len(prior['gaps']), 'Duplicate gap titles')
        notes = prior.get('evidence_notes')
        require(isinstance(notes, list) and len(notes) == 12, 'Require twelve slide notes')
        require({row.get('slide') for row in notes} == set(range(1, 13)), 'Incomplete/duplicate slide-note references')
        for row in notes:
            text_fields(row, ['title', 'summary'], 'slide note')
        if 'related_report' in prior:
            related = prior['related_report']
            text_fields(related, ['title', 'research_cutoff', 'scope', 'assessment', 'key_judgment'], 'related report')
            require(related['research_cutoff'] == '2026-10-04', 'Prior background-report date changed')
            require((related.get('paper_families'), related.get('engineering_material_families'), related.get('official_documents')) == (17, 2, 4), 'Prior coverage must retain its distinct evidence classes')

    cache = {}

    def page(path):
        resolved = path.resolve()
        require(resolved == DIST.resolve() or DIST.resolve() in resolved.parents, 'Internal link escapes dist: ' + str(path))
        require(resolved.is_file(), 'Missing internal target: ' + str(path))
        if resolved not in cache:
            cache[resolved] = Page(resolved)
        return cache[resolved]

    def static_asset(filename, href):
        parsed = urlsplit(href)
        require(not parsed.scheme and not parsed.netloc, filename + ': reader asset must remain local: ' + href)
        target_url = urlsplit(urljoin('/ai-infra/' + filename, href))
        target = (DIST / unquote(target_url.path.lstrip('/'))).resolve()
        require(DIST.resolve() in target.parents and target.is_file(), filename + ': missing static asset ' + href)
        require(target.stat().st_size > 0, filename + ': empty static asset ' + href)

    mechanism_pages = ['operators-' + row['id'] + '.html' for row in all_routes]
    require(len(mechanism_pages) == len(set(mechanism_pages)) == 9, 'Require nine independent mechanism pages')
    pages = PAGES + mechanism_pages
    for filename in pages:
        current = page(OUT / filename)
        require(not any(node.tag in {'details', 'summary'} for node in current.nodes), filename + ': research content must stay expanded')
        h1 = [normalized(node.text) for node in current.nodes if node.tag == 'h1']
        require(len(h1) == 1, filename + ': expected one page title')
        top_nav = [node for node in current.nodes if node.tag == 'nav' and node.attrs.get('aria-label') == '算子洞察导航']
        require(len(top_nav) == 1, filename + ': missing single operator navigation')
        top_links = [node for node in top_nav[0].descendants() if node.tag == 'a']
        require([node.attrs.get('href') for node in top_links] == ['operators.html#view-'+key for key in ['sources','topics','updates','home','reports']], filename + ': navigation must reuse the five compression reading responsibilities')
        require([normalized(node.text) for node in top_links] == ['信息来源','技术地图','本期动态','洞察报告','洞察归档'], filename + ': shared navigation labels drifted')
        require(not any('310P' in node.text for node in top_links), filename + ': 310P practice must not be a peer navigation item')
        require('Ascend310P_12_Page_Report' not in current.raw, filename + ': internal report must not be exposed')
        if prior is not None:
            require(source['filename'] not in current.raw and source['sha256'] not in current.raw, filename + ': internal PPT identity must not be exposed in the research reader')
        require(not any(has_class(node, 'op-prior-teaser') or node.attrs.get('id', '').startswith('prior-') for node in current.nodes), filename + ': internal project report leaked into the active research reader')
        for row in (prior or {}).get('capabilities', []):
            require(normalized(row['current_state']) not in normalized(current.root.text), filename + ': internal implementation audit leaked into the frontend')
        for gap in (prior or {}).get('gaps', []):
            require(normalized(gap['action']) not in normalized(current.root.text) and normalized(gap['acceptance']) not in normalized(current.root.text), filename + ': internal project tasks leaked into the frontend')
        styles = [node.attrs['href'] for node in current.nodes if node.tag == 'link' and 'stylesheet' in node.attrs.get('rel', '').split() and node.attrs.get('href')]
        scripts = [node.attrs['src'] for node in current.nodes if node.tag == 'script' and node.attrs.get('src')]
        require('operators-research.css' in [urlsplit(x).path for x in styles] and 'operators-research.js' in [urlsplit(x).path for x in scripts], filename + ': missing reader CSS/JS dependency')
        for href in styles + scripts:
            static_asset(filename, href)
        for anchor, record in current.ids.items():
            if not anchor.startswith('source-'):
                continue
            key = anchor[len('source-'):]
            require(key in sources, filename + ': unknown displayed evidence ' + key)
            urls = {node.attrs.get('href') for node in record.descendants() if node.tag == 'a'}
            require(sources[key]['url'] in urls, filename + ': evidence URL differs from maintained source ' + key)
        for link in current.links:
            href = link.attrs['href']
            parsed = urlsplit(href)
            require(not unquote(parsed.path).endswith('/operators-310p-codegen.html') and unquote(parsed.path) != 'operators-310p-codegen.html', filename + ': active reader must not link to the legacy project report')
            if parsed.scheme or parsed.netloc:
                continue
            target_url = urlsplit(urljoin('/ai-infra/' + filename, href))
            target = DIST / unquote(target_url.path.lstrip('/'))
            if target.is_dir():
                target = target / 'index.html'
            linked = page(target)
            if target_url.fragment:
                require(unquote(target_url.fragment) in linked.ids, filename + ': unresolved internal anchor ' + href)

    visual_signatures = set()
    for branch in routes['branches']:
        filename = 'operators-1.html' if branch['id'] == 'compute' else 'operators-2.html'
        built = page(OUT / filename)
        require(normalized(branch['title']) == next(normalized(n.text) for n in built.nodes if n.tag == 'h1'), filename + ': wrong branch title')
        for route in branch['routes']:
            anchor = 'route-' + route['id']
            require(anchor in built.ids, filename + ': missing mechanism ' + anchor)
            route_node = built.ids[anchor]
            require(normalized(route['title']) in normalized(route_node.text), anchor + ': title absent')
            expert = route['expert']
            require(normalized(expert['brief']) in normalized(route_node.text), anchor + ': concise expert judgment absent')
            destination = 'operators-' + route['id'] + '.html'
            require(any(n.attrs.get('href') == destination for n in route_node.descendants() if n.tag == 'a'), anchor + ': legacy branch anchor must lead directly to the detailed mechanism')
            detailed = page(OUT / destination)
            require(normalized(route['title']) == next(normalized(n.text) for n in detailed.nodes if n.tag == 'h1'), destination + ': wrong mechanism title')
            for section in ROUTE_SECTIONS + ['references']:
                require(section in detailed.ids and detailed.ids[section].tag == 'section', destination + ': missing chapter ' + section)
                chapter = detailed.ids[section]
                headings = [n for n in chapter.descendants() if n.tag in {'h2', 'h3'}]
                expected_level = 'h3' if section in SUBORDINATE_ROUTE_SECTIONS else 'h2'
                require(headings and headings[0].tag == expected_level and normalized(headings[0].text), destination + ': wrong/missing ' + expected_level + ' heading ' + section)
                require(any(n.tag in {'p', 'li'} and normalized(n.text) for n in chapter.descendants()), destination + ': empty chapter ' + section)
            main_headings = [n for n in detailed.nodes if n.tag == 'h2']
            expected_headings = [next(n for n in detailed.ids[key].descendants() if n.tag == 'h2') for key in PRIMARY_ROUTE_SECTIONS + ['references']]
            require(main_headings == expected_headings, destination + ': mechanism must follow the shared seven-chapter compression format plus references')
            expected_titles=['速览与证据','研究背景','基本原理','关键挑战','技术进展','比较判断','研究结论']
            require([normalized(h.text) for h in main_headings[:-1]]==expected_titles, destination + ': shared chapter names/order drifted')
            for child_id, parent_id in [('conclusion', 'practice')]:
                require(detailed.ids[child_id] in list(detailed.ids[parent_id].descendants()), destination + ': compatibility anchor must remain within its primary chapter: ' + child_id)
            require(normalized(expert['bottleneck_signal']) in normalized(detailed.ids['background'].text), destination + ': observable bottleneck signal absent')
            require(normalized(route['principle_formula']) in normalized(detailed.ids['principles'].text), destination + ': principle relation absent')
            require(normalized(expert['conclusion']) in normalized(detailed.ids['conclusion'].text), destination + ': expert conclusion absent')
            require(normalized(route['boundary']) in normalized(detailed.ids['conclusion'].text), destination + ': conclusion lost its applicability boundary')
            insight = guide['routes'][route['id']].get('insight')
            text_fields(insight, ['title'], route['id'] + '.guide.insight')
            nonempty_list(insight.get('paragraphs'), route['id'] + '.guide.insight.paragraphs')
            require(normalized(insight['title']) in normalized(detailed.ids['practice'].text), destination + ': research judgment lost its maintained insight title')
            for paragraph in insight['paragraphs']:
                require(normalized(paragraph) in normalized(detailed.ids['practice'].text), destination + ': research judgment lost a maintained insight paragraph')
            practice_refs = {node.attrs.get('href') for node in detailed.ids['practice'].descendants() if node.tag == 'a'}
            require({'#source-' + key for key in insight['source_ids']} <= practice_refs, destination + ': research judgment lost its insight evidence')
            for mode in ['wide', 'mobile']:
                visuals = [node for node in detailed.ids['principles'].descendants() if node.tag == 'svg' and has_class(node, 'op-mechanism-' + mode)]
                require(len(visuals) == 1, destination + ': missing/duplicated ' + mode + ' mechanism visual')
                visual = visuals[0]
                require(visual.attrs.get('role') == 'img' and visual.attrs.get('aria-label', '').strip(), destination + ': mechanism visual lacks accessible explanation')
                require(re.fullmatch(r'\s*-?\d+(?:\.\d+)?(?:[ ,]+-?\d+(?:\.\d+)?){3}\s*', visual.attrs.get('viewbox', '')), destination + ': invalid visual viewBox')
                labels = [normalized(node.text) for node in visual.descendants() if node.tag == 'text' and normalized(node.text)]
                require(len(set(labels)) >= 4 and any(node.tag in {'rect', 'path', 'circle', 'line', 'polygon'} for node in visual.descendants()), destination + ': visual must explain a mechanism rather than only label a placeholder')
                if mode == 'wide':
                    signature = tuple(labels)
                    require(signature not in visual_signatures, destination + ': reused explanation from another mechanism')
                    visual_signatures.add(signature)
            for question in route['research_questions']:
                require(normalized(question) in normalized(detailed.ids['challenges'].text), destination + ': missing research challenge')
            progress = detailed.ids['progress']
            groups = [node for node in progress.descendants() if 'op-progress-group' in node.attrs.get('class', '').split()]
            require(len(groups) == 2, destination + ': industry and academic evidence must share the technical-progress chapter')
            require('产业' in groups[0].text and '学术' in groups[1].text, destination + ': industry must precede academic evidence')
            used_sources = set(route['source_ids'])
            for technique in expert['branches']:
                comparison_rows = [node for node in detailed.ids['comparison'].descendants() if node.tag == 'tr' and normalized(technique['name']) in normalized(node.text)]
                require(len(comparison_rows) == 1, destination + ': missing/duplicated named comparison ' + technique['name'])
                comparison_row = comparison_rows[0]
                for field in ['mechanism', 'tradeoff']:
                    require(normalized(technique[field]) in normalized(comparison_row.text), destination + ': named comparison lost ' + field)
                refs = {node.attrs.get('href') for node in comparison_row.descendants() if node.tag == 'a'}
                require({'#source-' + key for key in technique['evidence_ids']} <= refs, destination + ': named comparison lost its evidence')
                used_sources.update(technique['evidence_ids'])
            for group, group_node in zip(['industry', 'academic'], groups):
                for entry in route[group]:
                    title = normalized(entry['title'])
                    entries = [node for node in group_node.descendants() if 'op-progress-item' in node.attrs.get('class', '').split() and any(n.tag == 'h4' and normalized(n.text) == title for n in node.descendants())]
                    require(len(entries) == 1, destination + ': missing/duplicated evidence entry ' + title)
                    for field in ['mechanism', 'date', 'conditions', 'result']:
                        require(normalized(entry[field]) in normalized(entries[0].text), destination + ': evidence entry lost ' + field + ': ' + title)
                    require(normalized(entry.get('boundary', entry.get('evidence_scope', ''))) in normalized(entries[0].text), destination + ': evidence entry lost its applicability/review limit: ' + title)
                    entry_refs = {n.attrs.get('href') for n in entries[0].descendants() if n.tag == 'a'}
                    require({'#source-' + key for key in entry['source_ids']} <= entry_refs, destination + ': unbound evidence entry ' + title)
                    used_sources.update(entry['source_ids'])
            refs = {node.attrs.get('href') for node in detailed.links}
            require({'#source-' + key for key in used_sources} <= refs, destination + ': missing visible citations')
            require({'source-' + key for key in used_sources} <= set(detailed.ids), destination + ': cited source lacks an expanded reference record')
            if branch['id'] == 'compute':
                require('operators-codegen.html#practice' in refs, destination + ': mechanism implications lost their horizontal-method connection')
                hook = next(row for row in case['route_links'] if row['route_id'] == route['id'])
                require(all(normalized(hook[field]) in normalized(detailed.ids['principles'].text) for field in ['observation', 'action']), destination + ': missing concrete-case mechanism hook')
                require('operators-1.html#cannbot' in refs, destination + ': concrete-case hook lost the full explanation')

    overview = page(OUT / 'operators.html')
    overview_routes = overview.ids.get('routes')
    require(overview_routes is not None, 'Operator overview lost the mechanism directory')
    destinations = {node.attrs.get('href') for node in overview_routes.descendants() if node.tag == 'a'}
    require(set(mechanism_pages) <= destinations, 'Overview must link directly to all nine mechanism pages')
    require(not any(url and re.match(r'operators-[12]\.html#route-', url) for url in destinations), 'Overview must not add a branch-page hop before mechanisms')
    compute = page(OUT / 'operators-1.html')
    require(any(node.attrs.get('href') == 'operators-codegen.html' for node in compute.links), 'Compute branch lost the hardware-bound generation insight')
    require('cannbot' in compute.ids and 'cannbot-fusion' in compute.ids, 'Compute branch lost the expanded Add/fusion case')
    case_node = compute.ids['cannbot']
    for field in ['title', 'lead', 'scope', 'formula', 'contract', 'template_review']:
        require(normalized(case[field]) in normalized(case_node.text), 'CannBot teaching case lost ' + field)
    require('不可直接编译' in case_node.text and 'offset = coreBase + k * tileSize' in case_node.text and 'count = min(tileSize, coreCount - k * tileSize)' in case_node.text, 'CannBot teaching pseudocode lost its illustrative status or tail/offset handling')
    for concept in case['concepts']:
        anchor = 'cannbot-' + concept['id']
        require(anchor in compute.ids, 'CannBot missing concept anchor ' + anchor)
        for field in ['name', 'term', 'question', 'explanation', 'where']:
            require(normalized(concept[field]) in normalized(compute.ids[anchor].text), 'CannBot concept lost ' + field + ': ' + concept['id'])
    for row in case['judgments']:
        require(normalized(row['title']) in normalized(case_node.text) and normalized(row['text']) in normalized(case_node.text), 'CannBot missing mechanism judgment')
    for field in ['title', 'formula', 'description', 'preserved_output', 'internal_only', 'precision']:
        require(normalized(case['fusion'][field]) in normalized(compute.ids['cannbot-fusion'].text), 'Add/RMSNorm case lost ' + field)
    for row in case['route_links']:
        require(all(normalized(row[field]) in normalized(compute.ids['cannbot-routes'].text) for field in ['name', 'observation', 'action']), 'CannBot route map lost its concrete explanation')

    generation = page(OUT / 'operators-codegen.html')
    for chapter_id in ['hardware', 'projects', 'methods', 'evidence', 'toolchain', 'practice', 'conclusion', 'references']:
        require(chapter_id in generation.ids and generation.ids[chapter_id].tag == 'section', 'Generation insight missing expanded chapter ' + chapter_id)
    for row in codegen_rows:
        anchor = 'evidence-' + row['id']
        require(anchor in generation.ids, 'Generation insight missing named evidence ' + row['id'])
        record = generation.ids[anchor]
        for field in ['platform', 'work', 'date', 'mechanism', 'conditions', 'result', 'limit']:
            require(normalized(row[field]) in normalized(record.text), 'Generation evidence lost ' + field + ': ' + row['id'])
        refs = {node.attrs.get('href') for node in record.descendants() if node.tag == 'a'}
        require({'#source-' + key for key in row['source_ids']} <= refs, 'Generation evidence lost source joins: ' + row['id'])
    for field in ['hardware_rows', 'methods']:
        chapter = generation.ids['hardware' if field == 'hardware_rows' else 'methods']
        for row in codegen[field]:
            for key, value in row.items():
                if isinstance(value, str) and key != 'id':
                    require(normalized(value) in normalized(chapter.text), 'Generation insight lost maintained ' + field + '.' + key)
    for field, chapter_id in [('platforms', 'hardware'), ('tools', 'toolchain'), ('implications', 'practice')]:
        for row in hardware[field]:
            for key, value in row.items():
                if isinstance(value, str):
                    require(normalized(value) in normalized(generation.ids[chapter_id].text), 'Generation insight lost hardware ' + field + '.' + key)
                elif key == 'nodes':
                    require(all(normalized(item) in normalized(generation.ids[chapter_id].text) for item in value), 'Generation insight lost platform execution model')
    require(normalized(hardware['scope']) in normalized(generation.ids['hardware'].text) and normalized(codegen['scope']) in normalized(generation.ids['conclusion'].text), 'Generation insight lost hardware/execution evidence boundaries')
    require(normalized(hardware['transfer_note']) in normalized(generation.ids['practice'].text), 'Generation implications lost their research-only boundary')
    for row in projects:
        require(all(normalized(row[field]) in normalized(generation.ids['projects'].text) for field in ['name', 'method', 'hardware', 'learn', 'limit']), 'Generation comparison lost a maintained system distinction')
        require('#evidence-' + row['evidence_id'] in {node.attrs.get('href') for node in generation.ids['projects'].descendants() if node.tag == 'a'}, 'Generation comparison lost its direct evidence link')
    for row in codegen['conclusions']:
        require(normalized(row['title']) in normalized(generation.ids['conclusion'].text) and normalized(row['text']) in normalized(generation.ids['conclusion'].text), 'Generation insight ignores a maintained conclusion')
    require(normalized(codegen['update_principle']) in normalized(generation.ids['conclusion'].text), 'Generation insight lost its maintained update principle')
    require('operators-codegen.html' in {node.attrs.get('href') for node in overview.links}, 'Operator overview lost its direct generation-insight entry')
    require(not any(has_class(node, 'op-codegen-entry') for node in overview.nodes), 'Generation efficiency method must not displace the root-technology overview')
    require('automatic' in overview.ids and has_class(overview.ids['automatic'], 'op-subsection'), 'Generation must remain a subordinate horizontal method')
    require(any('横向' in node.text for node in overview.ids['automatic'].descendants() if node.tag == 'h3'), 'Generation must remain a horizontal efficiency method below the main chapters')

    prior_page = page(OUT / 'operators-310p-codegen.html')
    require('Ascend310P_12_Page_Report' not in prior_page.raw and not any(key.startswith('prior-') for key in prior_page.ids), 'Legacy bookmark still exposes the internal project report')
    if prior is not None:
        require(source['filename'] not in prior_page.raw and source['sha256'] not in prior_page.raw, 'Legacy bookmark exposes the private audit identity')
    require(len(prior_page.links) == 1 and prior_page.links[0].attrs.get('href') == 'operators-codegen.html#practice', 'Legacy bookmark must lead only to research implications')
    require(any(node.tag == 'meta' and node.attrs.get('http-equiv', '').lower() == 'refresh' and re.fullmatch(r'0\s*;\s*url=operators-codegen\.html#practice', node.attrs.get('content', ''), re.I) for node in prior_page.nodes), 'Legacy bookmark lost its immediate redirect to research implications')
    for text in [prior_page.raw, unquote(prior_page.raw)]:
        require(not re.search(r'(?<![A-Za-z0-9])[A-Za-z]:[/\\]|/(?:Users|home|mnt/[a-z])/', text), '310P page exposes a local absolute path')
        require(not re.search(r'file:/', text, re.I), '310P page contains a local file URL')

    atlas = page(OUT / 'index.html')
    roots = {'evaluation': '性能评测', 'hardware': '硬件加速', 'compression': '推理压缩', 'iteration': '迭代算法加速', 'operators': '算子定制加速', 'scheduling': '组合调度加速'}
    for key, title in roots.items():
        require(key in atlas.ids and title in atlas.ids[key].text, 'Root classification missing: ' + title)
    group = atlas.ids['operators']
    headings = [normalized(n.text) for n in group.descendants() if n.tag == 'h3']
    require(headings == [BRANCHES['compute'][0], BRANCHES['communication'][0]], 'Operator root must preserve its two exact second-level titles')
    detailed={n.attrs.get('id') for n in atlas.nodes if n.attrs.get('data-research-status')=='detailed'}
    require(detailed=={'compression','operators'}, 'Detailed insight markers must include compression and operators without upgrading unfinished roots')
    operator_root=atlas.ids['operators']
    require('已有专题洞察' in operator_root.text and '研究建议 · 待验证' not in operator_root.text, 'Operator cards must show their current reading depth')
    marker_css=(OUT/'atlas.css').read_text(encoding='utf-8')
    require('[data-research-status=detailed]' in marker_css and '#compression' not in marker_css, 'Research-depth color must be generic, not hard-coded to compression')
    require(any(n.attrs.get('href') == 'operators-1.html' and normalized(n.text) for n in group.descendants() if n.tag == 'a'), 'Root map must retain the compute branch entry')
    for label in ['硬件/模型性能评测', '硬件增强', '虚拟化复用', '缓存代计算', '数据稀疏化', '迭代次数压缩', '异构资源调度', '单模型实例多卡调度', '业务感知调度', '多模型实例多卡调度']:
        require(label in atlas.root.text, 'Existing second-level classification lost: ' + label)
    require(len(visual_signatures) == 9, 'Require nine distinct mechanism explanations with wide/mobile versions')
    require(len(pages) == 13, 'Require thirteen active reading pages, excluding the legacy redirect')
    print('PASS: 9 operator research JSONs; 13 active research pages and 9 mechanism dossiers; expert mechanism tradeoffs and evidence classifications; horizontal generation efficiency with 5 named systems / 12 evidence records; internal 310P report absent, legacy redirect and taxonomy intact')


if __name__ == '__main__':
    verify()
