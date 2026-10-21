"""Prepare a normalized, URL-first migration. No raw vault/config exports."""
import argparse
import collections
import hashlib
import json
import re
import uuid
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, unquote
from prepare_sources import reasons, DENIED_NAME, DENIED_PARTS

ROOTS = ['0_Codex工作台', '1_AI情报溯源', '2_AI情报织网', '3_AI情报日历', '4_AI情报洞察', '5_学术研究织网']
MODULES = ['workbench', 'provenance', 'knowledge_graph', 'timeline', 'insights', 'academic']
NOW = '2026-10-02'
BATCH_ID = 'cloud-core-obsidian-20261002-v1'
URL_RE = re.compile(r'https?://[^\s<>\[\]"\x00-\x1f]+')
EXCLUDE_DIRS = DENIED_PARTS | {'skills', 'tools', '_scripts', '.github', 'venv', '.venv', '__pycache__', '对话日志', 'agentworkspace'}


def stable(prefix, value):
    return prefix + '-' + hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]


def canonical(raw):
    raw = raw.rstrip('.,;，。；')
    while raw.endswith(')') and raw.count(')') > raw.count('('):
        raw = raw[:-1]
    try:
        parts = urlsplit(raw)
        if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password:
            return None
        host = parts.hostname.lower()
        if host in {'localhost', '127.0.0.1'} or re.match(r'^(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)', host):
            return None
        if reasons(unquote(raw)):
            return None
        path = parts.path or '/'
        version, identifier, provider = '', '', host
        if host in {'arxiv.org', 'www.arxiv.org', 'export.arxiv.org'}:
            match = re.search(r'/(?:abs|pdf|html)/((?:\d{4}\.\d{4,5}|[a-z-]+/\d{7})(v\d+)?)(?:\.pdf)?', path, re.I)
            if match:
                observed = match.group(1)
                version = match.group(2) or ''
                identifier = observed[:-len(version)] if version else observed
                return ('https://arxiv.org/abs/' + identifier, raw, 'arxiv', identifier, version)
        if host in {'doi.org', 'dx.doi.org'} and path.startswith('/10.'):
            identifier = unquote(path[1:]).lower()
            return ('https://doi.org/' + identifier, raw, 'doi', identifier, '')
        # Preserve article query identity (e.g. ?id=), drop fragments only.
        normalized = urlunsplit((parts.scheme.lower(), host + ((':' + str(parts.port)) if parts.port else ''), path, parts.query, ''))
        return normalized, raw, provider, identifier, version
    except ValueError:
        return None


def scalar(text, key):
    match = re.search(r'^' + re.escape(key) + r'\s*:\s*([^\r\n]+)', text, re.M | re.I)
    return match.group(1).strip().strip('"\'')[:200] if match else ''


def title_of(text, path):
    front = text.split('---', 2)[1] if text.startswith('---') and text.count('---') >= 2 else ''
    value = scalar(front, 'title')
    heading = re.search(r'^#\s+(.+)$', text, re.M)
    return (value or (heading.group(1) if heading else path.stem)).strip()[:240]


def is_internal(logical):
    return any(x in logical for x in ['/方法论/', '/课题规划/', '/课题追踪/', '/12格追踪/', '/场景化创新/', '/规则/', '/质量看守/']) or logical in {'📋_目录导航.md'} or logical.startswith('0_Codex工作台/') and logical.count('/') == 1


def kind(logical):
    for segment, label in [('方法论', 'methodology'), ('课题规划', 'planning'), ('课题追踪', 'tracking'), ('12格追踪', 'tracking'), ('场景化创新', 'scenario_analysis'), ('规则', 'governance')]:
        if segment in logical:
            return label
    return 'guide'


def build(vault, output):
    tables = collections.defaultdict(list)
    audit = collections.Counter()
    issues = []
    documents, sources, folders, refs = {}, {}, {}, {}
    candidates = []
    for path in sorted(vault.rglob('*.md')):
        relative = path.relative_to(vault)
        logical = relative.as_posix()
        audit['markdown_seen'] += 1
        if any(p.lower() in EXCLUDE_DIRS for p in relative.parts):
            audit['excluded_config_tools_or_chat'] += 1
            continue
        if relative.parts[0] not in ROOTS and logical != '📋_目录导航.md':
            audit['excluded_root_nonbusiness'] += 1
            continue
        if DENIED_NAME.search(logical) or reasons(logical):
            audit['quarantined_name'] += 1
            continue
        if path.stat().st_size > 1024 * 1024:
            audit['oversize_manual_review'] += 1
            continue
        try:
            text = path.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError):
            audit['unreadable'] += 1
            continue
        codes = reasons(text)
        if codes:
            audit['quarantined_content'] += 1
            for code in codes:
                audit['rule_' + code] += 1
            # Opaque identifier only: no rejected file name, line or value leaves memory.
            issues.append({'issue_id': stable('issue', logical), 'business_id': 'cloud-core', 'batch_id': BATCH_ID,
                           'subject_id': stable('note', logical), 'issue_type': 'credential_review_required', 'status': 'excluded',
                           'description': '整篇笔记经敏感信息检查被隔离；正文与路径均未导出。'})
            continue
        module = MODULES[ROOTS.index(relative.parts[0])] if relative.parts[0] in ROOTS else 'workbench'
        title = title_of(text, path)
        primary = scalar(text[:8000], 'primary_source') or scalar(text[:8000], 'source_url') or scalar(text[:8000], 'url')
        urls = list(dict.fromkeys(([primary] if primary.startswith('http') else []) + URL_RE.findall(text)))
        valid = [value for raw in urls if (value := canonical(raw))]
        internal = is_internal(logical)
        if not internal and not valid:
            audit['no_public_url_retained_locally'] += 1
            continue
        audit['internal_documents' if internal else 'url_only_notes'] += 1
        observed = scalar(text[:8000], 'discovered') or scalar(text[:8000], 'date')
        if not re.match(r'^\d{4}-\d{2}-\d{2}', observed):
            observed = ''
        source_status = scalar(text[:8000], 'status')
        note_id = stable('note', logical)
        if internal:
            folder_path = relative.parent.as_posix()
            parent_parts = relative.parent.parts
            for i in range(1, len(parent_parts) + 1):
                fp = '/'.join(parent_parts[:i])
                fid = stable('folder', fp)
                folders[fid] = {'folder_id': fid, 'business_id': 'cloud-core', 'module_id': module,
                                'parent_id': stable('folder', '/'.join(parent_parts[:i-1])) if i > 1 else '',
                                'name': parent_parts[i-1], 'logical_path': fp}
            doc = {'document_id': note_id, 'business_id': 'cloud-core', 'module_id': module,
                   'folder_id': stable('folder', folder_path) if folder_path != '.' else '', 'title': title,
                   'document_kind': kind(logical), 'logical_path': logical, 'body': text,
                   'body_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(), 'source_date': observed,
                   'source_status': source_status, 'review_status': 'imported_unverified', 'batch_id': BATCH_ID}
            documents[note_id] = doc
            candidates.append((doc, text))
        # URL-only notes preserve compact provenance; no frontmatter blob or public body.
        for normalized, original, provider, external_id, version in valid:
            sid = stable('source', normalized)
            if sid not in sources:
                sources[sid] = {'source_id': sid, 'business_id': 'cloud-core', 'canonical_url': normalized,
                                'title': title if len(valid) <= 3 else external_id or normalized,
                                'source_kind': 'paper' if provider in {'arxiv', 'doi'} else 'web',
                                'provider': provider, 'external_id': external_id,
                                'verification_status': 'not_checked', 'update_policy': 'resolve_url_then_review_version',
                                'last_checked_at': '', 'batch_id': BATCH_ID}
            rid = stable('source-ref', logical + '\0' + original)
            refs[rid] = {'reference_id': rid, 'business_id': 'cloud-core', 'source_id': sid,
                         'document_id': note_id if internal else '', 'module_id': module,
                         'origin_note': logical, 'origin_title': title, 'observed_url': original,
                         'observed_version': version, 'discovered_at': observed, 'source_status': source_status,
                         'reference_kind': 'internal_citation' if internal else 'url_only', 'batch_id': BATCH_ID}
    lookup = collections.defaultdict(list)
    for doc in documents.values():
        lookup[doc['logical_path'][:-3]].append(doc['document_id'])
        lookup[Path(doc['logical_path']).stem].append(doc['document_id'])
    links = {}
    for doc, text in candidates:
        for match in re.finditer(r'(!?)\[\[([^\]\r\n]+)\]\]', text):
            target = match.group(2).split('|', 1)[0].split('#', 1)[0].strip()
            if not target or DENIED_NAME.search(target) or reasons(target):
                continue
            target = target.removesuffix('.md')
            resolved = list(dict.fromkeys(lookup.get(target, [])))
            lid = stable('link', doc['document_id'] + '\0' + target + match.group(1))
            links[lid] = {'link_id': lid, 'business_id': 'cloud-core', 'from_document_id': doc['document_id'],
                          'target_name': target, 'to_document_id': resolved[0] if len(resolved) == 1 else '',
                          'link_kind': 'embed' if match.group(1) else 'wikilink',
                          'resolution_status': 'resolved' if len(resolved) == 1 else 'ambiguous' if resolved else 'retained_locally',
                          'batch_id': BATCH_ID}
    for name, values in [('documents', documents), ('sources', sources), ('source_refs', refs), ('folders', folders), ('links', links)]:
        tables['cloud_core_' + name] = list(values.values())
    tables['cloud_core_import_issues'] = issues
    output.mkdir(parents=True, exist_ok=True)
    chunks = []
    for name, rows in tables.items():
        chunk, size, number = [], 0, 0
        for row in rows:
            serialized = json.dumps(row, ensure_ascii=False)
            if reasons(serialized):
                raise ValueError('Payload audit failed; no export completed')
            if chunk and (size + len(serialized.encode()) > 350000 or len(chunk) >= 200):
                filename = f'{name}-{number:04d}.json'
                (output / filename).write_text(json.dumps(chunk, ensure_ascii=False), encoding='utf-8')
                chunks.append({'table': name, 'file': filename, 'rows': len(chunk)})
                chunk, size, number = [], 0, number + 1
            chunk.append(row)
            size += len(serialized.encode())
        if chunk:
            filename = f'{name}-{number:04d}.json'
            (output / filename).write_text(json.dumps(chunk, ensure_ascii=False), encoding='utf-8')
            chunks.append({'table': name, 'file': filename, 'rows': len(chunk)})
    summary = {'schema': 'cloud-core-migration-manifest/v1', 'batch_id': BATCH_ID, 'audit': dict(audit),
               'table_counts': {name: len(rows) for name, rows in tables.items()}, 'chunks': chunks,
               'public_body_policy': 'URL only; source title/provenance retained; no PDFs/news bodies',
               'binary_and_generated_data_policy': 'retained locally; not migrated',
               'excluded_values_policy': 'no credential values or rejected paths exported'}
    (output / 'manifest.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in summary.items() if key != 'chunks'} | {'chunk_count': len(chunks)}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--vault', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.vault.resolve(strict=True), args.output)
