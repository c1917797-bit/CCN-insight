"""Read an explicit note allowlist; quarantine secrets before any export.

No vault-wide export, original-note copy, credential value, or rejected line is
written to stdout/audit. This conservative check supplements source review.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

DENIED_PARTS = {'.obsidian', '.git', '.trash', 'node_modules', '.aws', '.ssh'}
DENIED_NAME = re.compile(r'密码|口令|凭据|密钥|私钥|账号|账户|password|credential|secret|token|account|\.env', re.I)
PATTERNS = {
    'credential_marker': re.compile(r'密码|口令|凭据|密钥|私钥|(?:password|passwd|pwd|api[_ -]?key|access[_ -]?token|refresh[_ -]?token|client[_ -]?secret|basic[_ -]?verify|authorization)\s*[:：=]|(?:bearer|basic)\s+[A-Za-z0-9+/=._-]{8,}', re.I),
    'private_key': re.compile(r'-----BEGIN (?:[A-Z ]*PRIVATE KEY|OPENSSH PRIVATE KEY)-----'),
    'known_token': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\b'),
    'url_credentials': re.compile(r'https?://[^\s/@:]+:[^\s/@]+@|[?&](?:token|key|password|secret|auth|signature|code)=[^\s&#]+', re.I),
    'login_pair': re.compile(r'(?:username|user|login|账号|用户名)\s*[:：=].{0,160}(?:password|密码|口令)', re.I | re.S),
}


def reasons(text):
    return [name for name, pattern in PATTERNS.items() if pattern.search(text)]


def prepare(vault, paths, output):
    vault = vault.resolve(strict=True)
    output.mkdir(parents=True, exist_ok=True)
    audit = {'schema': 'cloud-core-source-audit/v1', 'accepted': [], 'excluded': [],
             'policy': 'explicit_allowlist; whole-note quarantine on credential indicators; no attachments/config import'}
    for relative in paths:
        path = (vault / relative).resolve(strict=True)
        if not path.is_relative_to(vault):
            raise ValueError('Allowlist path escapes the selected vault')
        logical = path.relative_to(vault).as_posix()
        if any(part.lower() in DENIED_PARTS for part in path.relative_to(vault).parts) or DENIED_NAME.search(path.name):
            audit['excluded'].append({'source_id': hashlib.sha256(logical.encode()).hexdigest()[:20], 'reason_codes': ['excluded_path']})
            continue
        if path.suffix.lower() != '.md' or path.stat().st_size > 1024 * 1024:
            audit['excluded'].append({'source_id': hashlib.sha256(logical.encode()).hexdigest()[:20], 'reason_codes': ['unsupported_type_or_size']})
            continue
        body = path.read_text(encoding='utf-8-sig')
        rejected = reasons(body)
        if rejected:
            audit['excluded'].append({'source_id': hashlib.sha256(logical.encode()).hexdigest()[:20], 'reason_codes': rejected})
            continue
        digest = hashlib.sha256(body.encode('utf-8')).hexdigest()
        source_id = 'obsidian-' + hashlib.sha256(logical.encode()).hexdigest()[:20]
        destination = output / (source_id + '.md')
        destination.write_text(body, encoding='utf-8')
        audit['accepted'].append({'source_id': source_id, 'logical_path': logical, 'sha256': digest, 'bytes': len(body.encode('utf-8')), 'export': destination.name})
    (output / 'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    return audit


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--vault', type=Path, required=True)
    parser.add_argument('--allowlist', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit = prepare(args.vault, json.loads(args.allowlist.read_text(encoding='utf-8-sig')), args.output)
    print(json.dumps({'accepted': len(audit['accepted']), 'excluded': len(audit['excluded']), 'audit': str(args.output / 'audit.json')}, ensure_ascii=False))
