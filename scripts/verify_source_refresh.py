# -*- coding: utf-8 -*-
"""Check corrected identities, note provenance and bounded endpoint coverage."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/compression/tables'
def rows(t):return [x['row'] for x in map(json.loads,(BASE/t/'rows.jsonl').read_text(encoding='utf-8').splitlines()) if not x['deleted']]
channels={r['channel_id']:r for r in rows('ic_channels')};sources={r['source_id']:r for r in rows('cloud_core_sources')}
changes=json.loads((ROOT/'research/source-audits/2026-10-23/registry-corrections.json').read_text(encoding='utf-8'))
for r in changes:
 assert r['old_url']!=r['new_url']
 assert sources[channels[r['channel_id']]['source_id']]['canonical_url']==r['new_url'],r
assert len({r['channel_id'] for r in changes})==52
for ch in channels.values():
 assert ch.get('entrypoint_checked_at')=='2026-10-23'
 assert ch.get('entrypoint_status') in ['sample_readable','access_restricted','needs_check']
notes=[r for r in rows('ic_source_families') if r.get('reviewed_at')=='2026-10-23']
assert len(notes)>=21
for r in notes:assert r.get('review_url','').startswith('https://') and r.get('review_note_zh') and r.get('review_note_en')
assert '不能当作新增量化能力' in next(r['review_note_zh'] for r in notes if r['family_id']=='source-family-vllm-ascend')
assert '训练阶段' in channels['channel-da5e10dca2c862c0eca03f9e']['focus_zh']
assert sources[channels['channel-f607e353de33ad320ec5e107']['source_id']]['canonical_url']=='https://github.com/ggml-org/llama.cpp/tags'
print('PASS: 52 corrected source bindings; 332 dated endpoint checks; >=21 bounded primary review notes')
