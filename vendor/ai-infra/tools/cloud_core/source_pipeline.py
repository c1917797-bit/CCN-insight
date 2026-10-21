"""Bounded discovery maintenance, never automatic research qualification.

Input is an exact-revision TableGit export. Output is an audited transport plan,
not a second authority. Only the caller may apply it with native TableGit APIs.
No credentials, article bodies, model conclusions or performance claims are emitted.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import email.utils
import hashlib
import ipaddress
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

RULE_VERSION = "cloud-core-discovery-v2"
REQUIRED_TABLES = {"cloud_core_sources", "ic_paper_summaries", "ic_evidence_items", "ic_paper_summary_events", "ic_monthly_evidence_cells", "ic_monthly_scopes", "ic_paper_review_intakes", "ic_source_screenings", "ic_compression_topics"}
MAX_BYTES = 1024 * 1024
MAX_ITEMS = 100
REVIEWED = {"method_results_checked", "primary_full_text_reviewed", "full_text_reviewed"}
TRUSTED_EVIDENCE = {"primary_text_checked", "primary_full_text_reviewed", "method_results_checked", "full_text_reviewed", "primary_method_results_checked"}
STAGES = ("metadata_needed", "candidate_direct", "candidate_adjacent", "needs_relevance_review", "reviewed_visible", "reviewed_unpublished", "reconciliation_needed", "blocked_invalid", "excluded_manual", "retryable_failure")
AUTHORED = {"include", "exclude", "defer", "reviewed"}
DIRECT = re.compile(r"knowledge distill|quantiz|quantis|low[- ]bit|weight[- ]only|(?:model|llm|network).{0,30}(?:compress|prun|distill)|(?:compress|prun|distill).{0,30}(?:model|llm|network)|(?:low[- ]rank|svd).{0,35}(?:llm|compress)|kv.{0,12}(?:cache|evict|prun|compress|budget)|(?:cache|kv).{0,20}(?:quantiz|compress)|量化|低比特|模型压缩|知识蒸馏", re.I)
ADJACENT = re.compile(r"linear attention|recurrent state|delta.?net|deltalog|mamba|state.space|prefix cach|serving|decod.{0,25}(?:bandwidth|memory|traffic)|(?:memory|traffic).{0,25}decod|线性注意力|递归状态|调度|算子", re.I)
NEGATIVE_CONTEXT = re.compile(r"contextual bandit|smt solv|search.space|proof search|database|sql query|feature selection|training.{0,12}lora", re.I)
# Representation learning and data compression are not model-inference compression.
COLLISION = re.compile(r"latent concepts|concept discovery|random features|learning is forgetting|training as lossy compression|generative models as lossy compression|image compression|video compression|audio coding|source coding|vector.quantiz.{0,35}(?:tokeniz|codebook|representation)|quantum|quantization of gravity", re.I)
MODEL_TARGET = re.compile(r"\bllms?\b|language models?|neural networks?|transformers?|weight|activation|\bkv\b|key.value cache|speech|denois|translat|vision models?|spiking", re.I)
EXECUTION_TARGET = re.compile(r"inference|deploy|accelerat|efficient|low.bit|ultra.low.bit|weight|kv.{0,8}cache|key.value cache|model compression|compress.{0,25}(?:llm|network|transformer)|(?:llm|network|transformer).{0,25}compress|prun|post.training quant|quantization.aware", re.I)

SECRET_QUERY = re.compile(r"^(?:access_token|api_key|apikey|token|password|secret|auth|authorization|signature|cookie|key|code)$", re.I)
ARXIV = re.compile(r"^(\d{2})(0[1-9]|1[0-2])\.(\d{4,5})(v[1-9]\d*)?$", re.I)


def stable(prefix, *parts):
    return prefix + "-" + hashlib.sha256("\0".join(map(str, parts)).encode()).hexdigest()[:24]


def iso(value=None):
    if value is None:
        return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def public_url(value):
    p = urllib.parse.urlsplit(str(value))
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.port not in (None, 443):
        raise ValueError("unsafe_public_url")
    host = p.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith((".local", ".internal", ".localhost")):
        raise ValueError("unsafe_public_url")
    try:
        if not ipaddress.ip_address(host).is_global:
            raise ValueError("unsafe_public_url")
    except ValueError as error:
        if str(error) == "unsafe_public_url":
            raise
    if any(SECRET_QUERY.match(k) for k, _ in urllib.parse.parse_qsl(p.query)):
        raise ValueError("credential_query")
    return p


def identity(row):
    """Return a comparison key; never rewrite or merge source authority."""
    p = public_url(row.get("canonical_url", ""))
    host = p.hostname.lower().removeprefix("www.")
    path = p.path.rstrip("/")
    if host in {"arxiv.org", "export.arxiv.org"}:
        token = re.sub(r"^/(?:abs|pdf|html)/", "", path).removesuffix(".pdf")
        match = ARXIV.fullmatch(token)
        legacy = re.fullmatch(r"[a-z-]+(?:\.[A-Z]{2})?/\d{7}(v[1-9]\d*)?", token)
        if not match and not legacy:
            raise ValueError("invalid_arxiv_identifier")
        if match and len(match.group(3)) != (5 if int(match.group(1)) >= 15 else 4):
            raise ValueError("invalid_arxiv_identifier")
        return "arxiv:" + re.sub(r"v\d+$", "", token)
    if host in {"doi.org", "dx.doi.org"}:
        if not path.lower().startswith("/10."):
            raise ValueError("invalid_doi_identifier")
        return "doi:" + urllib.parse.unquote(path[1:]).lower()
    if host == "openreview.net":
        token = dict(urllib.parse.parse_qsl(p.query)).get("id", "")
        if token:
            return "openreview:" + token
    query = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not k.lower().startswith("utm_") and k.lower() not in {"ref", "fbclid", "gclid"}]
    return "url:" + urllib.parse.urlunsplit(("https", host, path or "/", urllib.parse.urlencode(sorted(query)), ""))


def title_missing(row):
    title = row.get("title", "").strip()
    return (len(title) < 10 or title.startswith(("https://", "http://"))
            or title == row.get("external_id", "") or bool(ARXIV.fullmatch(title)))


def fingerprint(row):
    fields = {k: row.get(k, "") for k in ("source_id", "canonical_url", "title", "source_kind", "external_id", "verification_status")}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def rows(snapshot, name):
    if "_row_cache" in snapshot and name in snapshot["_row_cache"]:
        return snapshot["_row_cache"][name]
    table = snapshot.get("tables", {}).get(name, [])
    if isinstance(table, dict):
        table = table.get("rows", [])
    return [r.get("row", r) for r in table if not r.get("deleted", False)]


def row_envelopes(snapshot, name):
    table = snapshot.get("tables", {}).get(name, [])
    if isinstance(table, dict):
        table = table.get("rows", [])
    return table


REASONS = {
    "reviewed_visible": ("已核验摘要、来源版本和可见入口关联。", "Reviewed summary, source version and reader association reconcile.", "保留既有研读；来源修订后重新核验变化。", "Retain the review and recheck changes when the source is revised."),
    "reviewed_unpublished": ("有原文核验摘要，但缺少有效页面入口关联。", "A primary-reviewed summary exists but lacks a valid reader association.", "核对研读月份和入口关联后发布，不改写发表日期。", "Reconcile review period and publication links without changing publication date."),
    "invalid_identifier": ("原始编号或公开地址异常，不能猜测替代来源。", "Original identifier or public URL is invalid; no replacement is inferred.", "从原始出处核对身份并修复链接。", "Verify identity against the original provenance and repair the link."),
    "missing_readable_title": ("只有编号、网址或过短标题，尚不能做相关性判断。", "Only an identifier, URL or insufficient title is available for screening.", "先获取官方标题、版本和日期，再筛选。", "Acquire official title, version and dates before screening."),
    "keyword_collision_needs_primary_review": ("标题含压缩同名词，但可能属于其他研究对象。", "Compression terms in the title may refer to a different research object.", "阅读原始摘要确认对象，不能据关键词自动排除或纳入。", "Read the primary abstract; keywords alone justify neither exclusion nor inclusion."),
    "adjacent_title_signal": ("标题提示推理系统邻接方向，尚未核验具体机制。", "The title suggests an adjacent inference-system topic; mechanism is unverified.", "核验摘要与方法，说明对访存、时延或吞吐的因果关系。", "Check abstract and method for causal relevance to traffic, latency or throughput."),
    "compression_title_signal": ("标题命中压缩候选规则；这不是相关性已确认或技术研读完成。", "The title matches a compression candidate rule, not confirmed relevance or completed review.", "核验对象、方法、推理阶段与实验条件后再写洞察。", "Verify object, method, inference stage and experimental conditions before synthesis."),
    "no_title_signal_not_an_exclusion": ("标题未命中规则，仍保留待筛，避免漏掉命名不同的技术。", "The title did not match; it remains pending to avoid missing differently named techniques.", "补充元数据或摘要后人工判断相关性。", "Inspect metadata or abstract before a relevance decision."),
    "manual_exclusion_preserved": ("保留此前原文筛选的排除判断。", "A prior primary-source exclusion decision is retained.", "仅在新版本或新证据改变判断时重新审阅。", "Revisit only when a new version or evidence changes the decision."),
    "manual_inclusion_preserved": ("保留此前人工摘要筛选判断，尚不能代替方法与结果研读。", "Prior abstract-screening relevance is retained; it does not replace method/results review.", "核验全文方法、效果与适用边界，补齐结构化摘要。", "Review full-text mechanism, results and limits, then complete a structured summary."),
    "review_marker_without_evidence": ("核验标记未与摘要和可信原文版本形成完整证据链。", "A review marker lacks a complete summary and primary-version evidence chain.", "核对摘要、证据状态与观察版本，完成前不宣称已研读。", "Reconcile summary, evidence status and observed version before calling it reviewed."),
    "summary_evidence_reconciliation": ("已有研读摘要，但来源或版本级证据状态尚未对齐；保留原研读，不自动升降级。", "An existing review has not reconciled source or version-level evidence status; the review is retained without automatic promotion or demotion.", "逐项核对原文版本、摘要、证据与页面关联，修复冲突后再推进。", "Reconcile source version, summary, evidence and reader association before advancing."),
    "acquisition_retry_due": ("最近一次官方元数据采集失败，保留来源并等待重试。", "The latest primary metadata acquisition failed; the source is retained for retry.", "按重试时间重跑同一来源；不重扫成功项目。", "Retry this source at the recorded time without rescanning successful items."),
}


def decision(stage, reason, evidence="title_only", manual=None):
    zh, en, next_zh, next_en = REASONS[reason]
    if manual:
        zh += " " + manual.get("reason_zh", "")
        en += " " + manual.get("reason_en", "")
    priorities = {"reconciliation_needed": 0, "reviewed_unpublished": 1, "metadata_needed": 20, "candidate_direct": 10, "candidate_adjacent": 15,
                  "needs_relevance_review": 40, "blocked_invalid": 60, "excluded_manual": 90, "reviewed_visible": 99, "retryable_failure": 25}
    return dict(stage=stage, priority=priorities[stage], reason_code=reason, reason_zh=zh, reason_en=en,
                next_action_zh=next_zh, next_action_en=next_en, evidence_level=evidence)


def valid_reviews(source, snapshot):
    sid = source["source_id"]
    evidence = rows(snapshot, "ic_evidence_items")
    good = []
    for summary in rows(snapshot, "ic_paper_summaries"):
        version = summary.get("observed_version")
        if (summary.get("source_id") != sid or summary.get("review_status") not in REVIEWED
                or not version or not summary.get("evidence_locator")
                or not all(summary.get(k, "").strip() for k in ("one_sentence_zh", "background_zh", "innovation_zh", "results_zh"))):
            continue
        try:
            public_url(summary.get("evidence_url", ""))
            if identity(source).startswith("arxiv:"):
                if identity({"canonical_url": summary["evidence_url"]}) != identity(source):
                    continue
                if not urllib.parse.urlsplit(summary["evidence_url"]).path.endswith(version):
                    continue
        except ValueError:
            continue
        events = [e for e in evidence if e.get("source_id") == sid and e.get("observed_version") == version
                  and e.get("status") in TRUSTED_EVIDENCE and e.get("verified_at") and day(e.get("publication_date", ""))]
        if events:
            good.append((summary, events))
    return good


def visible_review(summary, events, snapshot):
    sid, summary_id = summary["source_id"], summary["summary_id"]
    for intake in rows(snapshot, "ic_paper_review_intakes"):
        if (intake.get("source_id") == sid and intake.get("summary_id") == summary_id
                and intake.get("reviewed_at") == summary.get("reviewed_at")
                and intake.get("review_period_id") == summary.get("reviewed_at", "")[:7]
                and any(intake.get("publication_date") == e["publication_date"] for e in events)):
            return True
    scopes = {r["scope_id"]: r for r in rows(snapshot, "ic_monthly_scopes")}
    for association in rows(snapshot, "ic_paper_summary_events"):
        if (association.get("summary_id") != summary_id or association.get("source_id") != sid
                or association.get("observed_version") != summary["observed_version"]):
            continue
        event = next((e for e in events if e.get("evidence_id") == association.get("evidence_id")), None)
        if not event:
            continue
        for placement in rows(snapshot, "ic_monthly_evidence_cells"):
            scope = scopes.get(placement.get("scope_id"))
            if (placement.get("evidence_id") == event["evidence_id"] and placement.get("period_id") == association.get("period_id")
                    and scope and scope.get("period_id") == association.get("period_id")
                    and scope.get("window_start", "") <= event.get("event_date", "") <= scope.get("window_end", "")):
                return True
    return False


def classify(row, snapshot):
    """Independent evidence level and stage; title rules never qualify evidence."""
    sid = row["source_id"]
    reviews = valid_reviews(row, snapshot)
    summaries = [s for s in rows(snapshot, "ic_paper_summaries") if s.get("source_id") == sid]
    if summaries and (not reviews or row.get("verification_status") in {"not_checked", "invalid_identifier", "public_metadata_observed", ""}):
        return decision("reconciliation_needed", "summary_evidence_reconciliation", "existing_review_unreconciled")
    if reviews:
        stage = "reviewed_visible" if any(visible_review(s, e, snapshot) for s, e in reviews) else "reviewed_unpublished"
        return decision(stage, stage, "primary_method_results_reviewed")
    screenings = sorted([s for s in rows(snapshot, "ic_source_screenings") if s.get("source_id") == sid], key=lambda s: s.get("checked_at", ""), reverse=True)
    if screenings and screenings[0].get("screening_status") in {"in_scope", "adjacent", "excluded"}:
        manual = screenings[0]
        if manual["screening_status"] == "excluded":
            return decision("excluded_manual", "manual_exclusion_preserved", "primary_abstract_reviewed", manual)
        stage = "candidate_direct" if manual["screening_status"] == "in_scope" else "candidate_adjacent"
        return decision(stage, "manual_inclusion_preserved", "primary_abstract_reviewed", manual)
    attempts = sorted([a for a in rows(snapshot, "ic_source_acquisition_attempts") if a.get("source_id") == sid], key=lambda a: (a.get("attempted_at", ""), a.get("attempt", 0)), reverse=True)
    if attempts and attempts[0].get("status") == "retryable_failure" and attempts[0].get("attempted_at", "")[:10] >= row.get("last_checked_at", "")[:10]:
        result = decision("retryable_failure", "acquisition_retry_due", "metadata_acquisition_failed")
        if attempts[0].get("next_retry_at"):
            result["next_action_zh"] += " 下次重试：" + attempts[0]["next_retry_at"]
            result["next_action_en"] += " Next retry: " + attempts[0]["next_retry_at"]
        return result
    if row.get("verification_status") == "invalid_identifier":
        return decision("blocked_invalid", "invalid_identifier", "identity_unverified")
    if row.get("verification_status") in {"primary_full_text_reviewed", "full_text_reviewed"}:
        return decision("reconciliation_needed", "review_marker_without_evidence", "unreconciled_review_marker")
    if title_missing(row):
        return decision("metadata_needed", "missing_readable_title", "identity_only")
    title = row["title"]
    if NEGATIVE_CONTEXT.search(title) or COLLISION.search(title):
        return decision("needs_relevance_review", "keyword_collision_needs_primary_review")
    if ADJACENT.search(title) and (not DIRECT.search(title) or bool(re.search(r"prefix cach|state.{0,15}(?:write|materializ)|recurrent state", title, re.I))):
        return decision("candidate_adjacent", "adjacent_title_signal")
    if DIRECT.search(title):
        if MODEL_TARGET.search(title) and EXECUTION_TARGET.search(title):
            return decision("candidate_direct", "compression_title_signal")
        return decision("needs_relevance_review", "keyword_collision_needs_primary_review")
    return decision("needs_relevance_review", "no_title_signal_not_an_exclusion")


def audit(snapshot, now, rule_version=RULE_VERSION, run_id=None):
    revision = snapshot.get("revision", "")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("exact_tablegit_revision_required")
    missing = REQUIRED_TABLES - set(snapshot.get("tables", {}))
    if missing:
        raise ValueError("incomplete_audit_snapshot:" + ",".join(sorted(missing)))
    snapshot.pop("_row_cache", None)
    snapshot["_row_cache"] = {name: rows(snapshot, name) for name in snapshot["tables"]}
    sources = [r for r in rows(snapshot, "cloud_core_sources") if r.get("business_id") == "cloud-core" and r.get("source_kind") == "paper"]
    if len({r["source_id"] for r in sources}) != len(sources):
        raise ValueError("duplicate_source_primary_key")
    run_id = run_id or stable("pipeline-run", revision, rule_version, now)
    prior = {r["source_id"]: r for r in rows(snapshot, "ic_source_pipeline")}
    by_identity = collections.defaultdict(list)
    prepared = []
    for source in sorted(sources, key=lambda r: r["source_id"]):
        old = prior.get(source["source_id"], {})
        try:
            ident = identity(source)
            classification = classify(source, snapshot)
        except ValueError as error:
            ident = "invalid:" + source["source_id"]
            classification = decision("blocked_invalid", "invalid_identifier", "identity_unverified")
        row = dict(source_id=source["source_id"], business_id="cloud-core", topic_id="cloud_core", run_id=run_id, identity_key=ident,
                   source_fingerprint=fingerprint(source), rule_version=rule_version, updated_at=now, canonical_source_id=source["source_id"], **classification)
        prepared.append(row)
        by_identity[ident].append((source, row))
    duplicate_groups = 0
    for ident, group in by_identity.items():
        if len(group) < 2 or ident.startswith("invalid:"):
            continue
        duplicate_groups += 1
        ordered = sorted(group, key=lambda pair: (not pair[1]["stage"].startswith("reviewed_"), title_missing(pair[0]), pair[0]["source_id"]))
        canonical = ordered[0][0]["source_id"]
        for _, item in ordered[1:]:
            item["canonical_source_id"] = canonical
    stage_counts = dict(collections.Counter(r["stage"] for r in prepared))
    if sum(stage_counts.values()) != len(sources):
        raise AssertionError("coverage_conservation_failed")
    run = dict(run_id=run_id, business_id="cloud-core", topic_id="cloud_core", source_revision=revision, rule_version=rule_version,
               started_at=now, completed_at=now, status="completed_audit_not_research_review", total_sources=len(sources), processed_sources=len(prepared),
               duplicate_refs=sum(r["source_id"] != r["canonical_source_id"] for r in prepared), **{s: stage_counts.get(s, 0) for s in STAGES})
    matches = route_candidates(sources, prepared, run_id, rule_version, snapshot)
    return {"schema": "cloud-core-source-pipeline/audit-v1", "source_revision": revision, "rule_version": rule_version, "evaluated_at": now,
            "coverage": {"input_papers": len(sources), "accounted_papers": len(prepared), "unique_identities": len(by_identity), "duplicate_groups": duplicate_groups,
                         "stages": stage_counts}, "tables": {"ic_pipeline_runs": [run], "ic_source_pipeline": prepared,
                                                              "ic_source_route_candidates": matches, "ic_source_acquisition_attempts": []}}


def route_candidates(sources, pipeline, run_id, rule_version, snapshot):
    """Explicit object+method hints only; no conversion to scientific relations."""
    allowed = {r["compression_topic_id"] for r in rows(snapshot, "ic_compression_topics")}
    state = {r["source_id"]: r for r in pipeline}
    result = []
    for source in sources:
        if state[source["source_id"]]["stage"] not in {"candidate_direct", "candidate_adjacent"}:
            continue
        title = source["title"].lower()
        hints = []
        kv = bool(re.search(r"\bkv\b|key.value cach|proxykv|reasonalloc", title))
        weight = bool(re.search(r"weight|llm|language model|network", title))
        activation = bool(re.search(r"activation (?:quantiz|quantis|prun)|quantiz.{0,20}activation", title)) and "activation-aware" not in title
        if re.search(r"quantiz|quantis|low.bit", title):
            if kv:
                hints.append("kv_cache-precision")
            elif activation:
                hints.append("activations-precision")
            elif weight:
                hints.append("parameters-precision")
        if re.search(r"low.rank|svd", title) and weight and not re.search(r"\blora\b|fine.tun", title):
            hints.append("parameters-factorization")
        if kv and re.search(r"evict|budget|proxykv|reasonalloc|token.{0,15}prun", title):
            hints.append("kv_cache-kv_eviction")
        elif re.search(r"(?:weight|model|network|llm).{0,20}prun|prun.{0,20}(?:weight|model|network|llm)", title) and not kv:
            hints.append("parameters-selection")
        if re.search(r"distill", title) and weight and not kv:
            hints.append("parameters-distillation")
        for route in sorted(set(hints) & allowed):
            result.append(dict(match_id=stable("route-candidate", source["source_id"], route), source_id=source["source_id"], business_id="cloud-core", topic_id="cloud_core",
                               route_topic_id=route, relation_kind="machine_candidate_not_confirmed", match_basis="title_only_object_method_hint_requires_primary_review",
                               rule_version=rule_version, run_id=run_id))
    return result


def upsert_plan(proposed, envelopes, key_field, ignored=("updated_at", "run_id")):
    """Idempotent operations; preserve existing fields and use actual row versions."""
    existing = {r.get("key", r.get("row", r).get(key_field)): r for r in envelopes if not r.get("deleted", False)}
    result = []
    for row in proposed:
        key = row[key_field]
        env = existing.get(key)
        old = env.get("row", env) if env else None
        signature = hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        op_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "cloud-core-pipeline:" + key + ":" + signature))
        if old is None:
            result.append(dict(op="insert", key=key, row=row, operation_id=op_id))
        elif any(old.get(k) != v for k, v in row.items() if k not in ignored):
            if not isinstance(env.get("row_version"), int):
                raise ValueError("row_version_required_for_update:" + key)
            result.append(dict(op="update", key=key, expected_row_version=env["row_version"], set=row, operation_id=op_id))
    return result


def candidate_plan(proposed, envelopes, source_ids):
    result = upsert_plan(proposed, envelopes, "match_id")
    keep = {r["match_id"] for r in proposed}
    for env in envelopes:
        row = env.get("row", env)
        if (not env.get("deleted", False) and row.get("source_id") in source_ids and row.get("match_id") not in keep
                and row.get("relation_kind") == "machine_candidate_not_confirmed"):
            if not isinstance(env.get("row_version"), int):
                raise ValueError("row_version_required_for_candidate_retirement")
            result.append(dict(op="delete", key=row["match_id"], expected_row_version=env["row_version"],
                               operation_id=str(uuid.uuid5(uuid.NAMESPACE_URL, "cloud-core-retire-candidate:" + row["match_id"] + ":" + str(env["row_version"])))))
    return result


class StrictRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = public_url(newurl)
        if target.hostname != urllib.parse.urlsplit(req.full_url).hostname:
            raise ValueError("cross_host_redirect_requires_adapter_review")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def network_get(url, headers=None):
    p = public_url(url)
    addresses = socket.getaddrinfo(p.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(x[4][0]).is_global for x in addresses):
        raise ValueError("unsafe_resolved_address")
    safe_headers = {k: v for k, v in (headers or {}).items() if k in {"If-None-Match", "If-Modified-Since", "Accept"}}
    safe_headers["User-Agent"] = "CloudCoreResearchDiscovery/1.0 (public metadata only)"
    req = urllib.request.Request(url, headers=safe_headers)
    opener = urllib.request.build_opener(StrictRedirect())
    try:
        with opener.open(req, timeout=12) as response:
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError("response_limit_exceeded")
            return response.status, dict(response.headers.items()), data
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), b""


def text(node, name):
    child = node.find(name)
    return " ".join("".join(child.itertext()).split()) if child is not None else ""


def day(value):
    try:
        if re.match(r"^\d{4}-\d{2}-\d{2}", value):
            return dt.date.fromisoformat(value[:10]).isoformat()
        return email.utils.parsedate_to_datetime(value).date().isoformat()
    except (ValueError, TypeError, AttributeError):
        return ""


def parse_feed(data, expected_id=""):
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
        raise ValueError("xml_entities_disallowed")
    root = ET.fromstring(data)
    ns = "{http://www.w3.org/2005/Atom}"
    items = []
    for entry in root.findall(ns + "entry") + root.findall("./channel/item"):
        atom = entry.tag.startswith(ns)
        prefix = ns if atom else ""
        title = text(entry, prefix + "title")[:1000]
        links = entry.findall(prefix + "link")
        url = next((e.attrib.get("href", "") for e in links if e.attrib.get("rel", "alternate") == "alternate"), "") if atom else text(entry, "link")
        if not url:
            url = text(entry, prefix + "id")
        # arXiv feeds conventionally return http links; retain secure canonical equivalent.
        if urllib.parse.urlsplit(url).hostname in {"arxiv.org", "export.arxiv.org"}:
            url = "https:" + url.split(":", 1)[1]
        try:
            public_url(url)
        except ValueError:
            continue
        if expected_id and identity({"canonical_url": url}) != "arxiv:" + expected_id:
            continue
        version = (re.search(r"(v\d+)(?:\.pdf)?$", urllib.parse.urlsplit(url).path) or [""])[0]
        items.append({"canonical_url": url, "title": title, "publication_date": day(text(entry, prefix + ("published" if atom else "pubDate"))),
                      "updated_date": day(text(entry, prefix + "updated")) if atom else "", "observed_version": version})
        if len(items) >= MAX_ITEMS:
            break
    return items


def adapter_request(source, adapter):
    if adapter == "arxiv_metadata":
        ident = identity(source)
        if not ident.startswith("arxiv:"):
            raise ValueError("adapter_identity_mismatch")
        token = ident.split(":", 1)[1]
        return "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": token, "max_results": 1}), token
    if adapter == "github_releases":
        p = public_url(source["canonical_url"])
        parts = [x for x in p.path.split("/") if x]
        if p.hostname != "github.com" or len(parts) < 2 or not all(re.fullmatch(r"[A-Za-z0-9_.-]+", x) for x in parts[:2]):
            raise ValueError("adapter_identity_mismatch")
        return "https://api.github.com/repos/" + "/".join(parts[:2]) + "/releases?per_page=100&page=1", ""
    if adapter == "registered_feed":
        return urllib.parse.urlunsplit(public_url(source["canonical_url"])), ""
    raise ValueError("unsupported_adapter")


def retry_seconds(headers, now):
    normalized = {k.lower(): v for k, v in headers.items()}
    value = normalized.get("retry-after", "")
    if not value:
        return 0
    try:
        return max(0, int(value))
    except ValueError:
        try:
            return max(0, int((email.utils.parsedate_to_datetime(value) - dt.datetime.fromisoformat(now)).total_seconds()))
        except (ValueError, TypeError, OverflowError):
            return 60


def acquire(source, adapter, run_id, now, prior=None, get=network_get, sleep=time.sleep, max_attempts=3):
    """No whole-paper text or abstract retained. Every attempt has a terminal status."""
    prior = prior or {}
    if max_attempts not in (1, 2, 3):
        raise ValueError("attempt_limit_must_be_1_to_3")
    try:
        url, expected_id = adapter_request(source, adapter)
    except ValueError:
        return {"source_id": source["source_id"], "adapter": adapter, "status": "blocked", "items": [], "cache": {}, "attempts": [dict(
            attempt_id=stable("attempt", run_id, source["source_id"], adapter, 1), run_id=run_id, source_id=source["source_id"], adapter=adapter,
            attempt=1, attempted_at=now, status="blocked", http_status=0, error_code="invalid_source_or_adapter",
            error_message="Source identity or public URL does not match the selected adapter.", next_retry_at="")]}
    headers = {"Accept": "application/json" if adapter == "github_releases" else "application/atom+xml,application/rss+xml,application/xml"}
    if prior.get("etag"):
        headers["If-None-Match"] = prior["etag"]
    if prior.get("last_modified"):
        headers["If-Modified-Since"] = prior["last_modified"]
    attempts, output, continuation_url = [], [], ""
    cache = {}
    for number in range(1, max_attempts + 1):
        status, response_headers, data, error_code = 0, {}, b"", ""
        try:
            status, response_headers, data = get(url, headers)
            if status == 304:
                state = "not_modified"
            elif status == 200:
                if adapter == "github_releases":
                    raw = json.loads(data)
                    if not isinstance(raw, list):
                        raise ValueError("invalid_release_response")
                    output = [{"canonical_url": item["html_url"], "title": (item.get("name") or item.get("tag_name") or "")[:1000],
                               "publication_date": day(item.get("published_at", "")), "updated_date": "", "observed_version": item.get("tag_name", "")}
                              for item in raw[:MAX_ITEMS] if not item.get("draft")]
                    for item in output:
                        public_url(item["canonical_url"])
                    link_header = next((v for k, v in response_headers.items() if k.lower() == "link"), "")
                    match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
                    continuation_url = match.group(1) if match else ""
                else:
                    output = parse_feed(data, expected_id)
                if any(not item["title"].strip() for item in output):
                    raise ValueError("missing_readable_title")
                state = "metadata_ready" if output else "empty_response"
                if not output:
                    error_code = "no_usable_records"
            elif status in {408, 425, 429} or status >= 500:
                state, error_code = "retryable_failure", "http_" + str(status)
            else:
                state, error_code = "blocked", "http_" + str(status)
        except (TimeoutError, socket.timeout, socket.gaierror, urllib.error.URLError, ConnectionError):
            state, error_code = "retryable_failure", "network_or_timeout"
        except (ValueError, KeyError, TypeError, ET.ParseError):
            state, error_code = "blocked", "invalid_or_unsafe_response"
        normalized = {k.lower(): v for k, v in response_headers.items()}
        wait = retry_seconds(response_headers, now) if state == "retryable_failure" else 0
        next_retry = (dt.datetime.fromisoformat(now) + dt.timedelta(seconds=max(wait, 2 ** number))).isoformat(timespec="seconds") if state == "retryable_failure" else ""
        attempts.append(dict(attempt_id=stable("attempt", run_id, source["source_id"], adapter, number), run_id=run_id, source_id=source["source_id"], adapter=adapter,
                             attempt=number, attempted_at=now, status=state, http_status=status, error_code=error_code, next_retry_at=next_retry,
                             error_message="" if not error_code else "Public metadata acquisition failed; no response body or credentials retained."))
        cache = {"etag": normalized.get("etag", prior.get("etag", "")), "last_modified": normalized.get("last-modified", prior.get("last_modified", ""))}
        if state != "retryable_failure" or number == max_attempts or wait > 10:
            break
        sleep(max(wait, 2 ** number))
    return {"source_id": source["source_id"], "adapter": adapter, "attempts": attempts, "items": output, "cache": cache, "status": state,
            "continuation_url": continuation_url, "coverage_boundary": "Metadata only, not primary research review. Maximum 100 items per response; no annual or full-corpus coverage claim."}


def plan_acquisition(snapshot, output, channel_id=""):
    """Join acquired metadata to source identity; emit native, fenced operations."""
    if output.get("source_revision") != snapshot.get("revision") or not re.fullmatch(r"[0-9a-f]{40}", snapshot.get("revision", "")):
        raise ValueError("acquisition_snapshot_revision_mismatch")
    source_map = {r["source_id"]: r for r in rows(snapshot, "cloud_core_sources")}
    source = source_map.get(output.get("source_id"))
    if not source or output.get("source_fingerprint") != fingerprint(source):
        raise ValueError("acquisition_source_changed")
    attempts = output.get("attempts", [])
    if not attempts or any(a.get("source_id") != source["source_id"] or a.get("adapter") != output.get("adapter") for a in attempts):
        raise ValueError("invalid_attempt_identity")
    run_id = attempts[-1]["run_id"]
    changed_sources, new_sources, entries = [], [], []
    adapter = output["adapter"]
    items = output.get("items", [])
    if output.get("status") != "metadata_ready" and items:
        raise ValueError("failed_attempt_contains_metadata")
    if len(items) > MAX_ITEMS:
        raise ValueError("acquisition_item_limit_exceeded")
    if adapter == "arxiv_metadata":
        if len(items) > 1:
            raise ValueError("arxiv_identity_result_ambiguous")
        for item in items:
            if identity({"canonical_url": item.get("canonical_url", "")}) != identity(source) or not item.get("title", "").strip():
                raise ValueError("metadata_identity_or_title_mismatch")
            changes = {}
            if title_missing(source):
                changes["title"] = item["title"]
            if source.get("verification_status") in {"not_checked", "public_metadata_observed"}:
                changes.update(verification_status="public_metadata_observed", last_checked_at=attempts[-1]["attempted_at"][:10])
            if changes:
                changed_sources.append({**source, **changes})
    elif adapter in {"registered_feed", "github_releases"}:
        required = {"ic_channels", "ic_collection_runs", "ic_channel_retrievals", "ic_collection_entries"}
        if not required <= set(snapshot.get("tables", {})):
            raise ValueError("collection_snapshot_required")
        channels = [r for r in rows(snapshot, "ic_channels") if r.get("source_id") == source["source_id"] and r.get("enabled") and (not channel_id or r["channel_id"] == channel_id)]
        if len(channels) != 1:
            raise ValueError("one_explicit_registered_channel_required")
        channel_id = channels[0]["channel_id"]
        by_identity = {}
        for existing in source_map.values():
            try:
                by_identity.setdefault(identity(existing), existing)
            except ValueError:
                pass
        seen = set()
        for item in items:
            ident = identity({"canonical_url": item["canonical_url"]})
            if ident in seen:
                continue
            seen.add(ident)
            current = by_identity.get(ident)
            canonical = "https://arxiv.org/abs/" + ident.split(":", 1)[1] if ident.startswith("arxiv:") else item["canonical_url"]
            if current is None:
                sid = stable("source", canonical)
                if sid in source_map:
                    raise ValueError("source_key_identity_conflict")
                provider = ident.split(":", 1)[0] if ident.startswith(("arxiv:", "doi:", "openreview:")) else urllib.parse.urlsplit(canonical).hostname
                current = dict(source_id=sid, business_id="cloud-core", canonical_url=canonical, title=item["title"], source_kind="paper" if provider in {"arxiv", "doi", "openreview"} else "web",
                               provider=provider, external_id=ident.split(":", 1)[1] if provider in {"arxiv", "doi", "openreview"} else "", verification_status="public_metadata_observed",
                               update_policy="metadata_refresh_then_primary_review", last_checked_at=attempts[-1]["attempted_at"][:10], batch_id=run_id)
                new_sources.append(current)
                by_identity[ident] = current
            elif title_missing(current) and item.get("title", "").strip():
                changed_sources.append({**current, "title": item["title"]})
            date = item.get("publication_date", "")
            if date and (day(date) != date or date > attempts[-1]["attempted_at"][:10]):
                date = ""
            entries.append(dict(entry_id=stable("entry", run_id, channel_id, current["source_id"]), run_id=run_id, retrieval_id=stable("retrieval", run_id, channel_id),
                                channel_id=channel_id, source_id=current["source_id"], business_id="cloud-core", topic_id="cloud_core", date_value=date,
                                date_kind="published" if date else "unverified", observed_at=attempts[-1]["attempted_at"], locator="Official " + adapter + " listing metadata; original version: " + item.get("observed_version", ""),
                                review_status="listing_metadata_not_primary_review", selection_status="title_match_pending_review" if DIRECT.search(item["title"]) or ADJACENT.search(item["title"]) else "unmatched_title", position=len(entries)))
    else:
        raise ValueError("unsupported_adapter")
    tables = {"ic_source_acquisition_attempts": attempts, "cloud_core_sources": new_sources + changed_sources}
    if adapter != "arxiv_metadata":
        ready = output["status"] in {"metadata_ready", "not_modified", "empty_response"}
        dated = sum(bool(e["date_value"]) for e in entries)
        candidate = sum(e["selection_status"] == "title_match_pending_review" for e in entries)
        tables["ic_collection_entries"] = entries
        tables["ic_collection_runs"] = [dict(run_id=run_id, business_id="cloud-core", topic_id="cloud_core", started_at=attempts[0]["attempted_at"], completed_at=attempts[-1]["attempted_at"],
            cutoff_date=attempts[-1]["attempted_at"][:10], status="completed", requested_channels=1, attempted_channels=1, successful_channels=int(ready), failed_channels=int(not ready),
            dated_entries=dated, undated_entries=len(entries)-dated, candidate_entries=candidate,
            scope_note_zh="本轮仅一个已登记入口、最多100条公开列表元数据；不代表历史全量或原文研读。", scope_note_en="One registered entrypoint, up to 100 public listing records; not exhaustive history or primary review.")]
        tables["ic_channel_retrievals"] = [dict(retrieval_id=stable("retrieval", run_id, channel_id), run_id=run_id, channel_id=channel_id, source_id=source["source_id"], business_id="cloud-core", topic_id="cloud_core",
            status="success" if ready else "failed", method=adapter, checked_at=attempts[-1]["attempted_at"], boundary_zh="只核对列表标题/URL/日期，采集成功不表示科研审阅完成。", boundary_en="Listing title/URL/date metadata only; successful collection is not research review.",
            failure_code=attempts[-1]["error_code"], http_status=attempts[-1]["http_status"], received_count=len(entries), dated_count=dated, undated_count=len(entries)-dated, candidate_count=candidate, position=0)]
    keys = {"cloud_core_sources": "source_id", "ic_source_acquisition_attempts": "attempt_id", "ic_collection_runs": "run_id", "ic_channel_retrievals": "retrieval_id", "ic_collection_entries": "entry_id"}
    plans = [{"path": "data/tables/" + name, "operations": upsert_plan(values, row_envelopes(snapshot, name), keys[name], ignored=())} for name, values in tables.items()]
    return {"schema": "cloud-core-source-pipeline/acquisition-plan-v1", "source_revision": snapshot["revision"], "tables": tables, "operations": plans,
            "boundary": "Metadata and attempt state only. No source is promoted to primary technical review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["audit", "acquire", "plan-acquisition"])
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--now")
    parser.add_argument("--source-id")
    parser.add_argument("--adapter", choices=["arxiv_metadata", "registered_feed", "github_releases"])
    parser.add_argument("--run-id")
    parser.add_argument("--previous-output", type=Path)
    parser.add_argument("--acquisition-output", type=Path)
    parser.add_argument("--channel-id", default="")
    parser.add_argument("--attempt-limit", type=int, default=3)
    parser.add_argument("--allow-network", action="store_true")
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
    now = iso(args.now)
    if args.command == "audit":
        result = audit(snapshot, now, run_id=args.run_id)
        keys = {"ic_pipeline_runs": "run_id", "ic_source_pipeline": "source_id", "ic_source_route_candidates": "match_id", "ic_source_acquisition_attempts": "attempt_id"}
        result["operations"] = [{"path": "data/tables/" + table, "operations": upsert_plan(values, row_envelopes(snapshot, table), keys[table])}
                                for table, values in result["tables"].items()]
        for plan in result["operations"]:
            if plan["path"] == "data/tables/ic_source_route_candidates":
                plan["operations"] = candidate_plan(result["tables"]["ic_source_route_candidates"], row_envelopes(snapshot, "ic_source_route_candidates"), {r["source_id"] for r in result["tables"]["ic_source_pipeline"]})
    elif args.command == "plan-acquisition":
        if not args.acquisition_output:
            parser.error("plan-acquisition requires --acquisition-output")
        result = plan_acquisition(snapshot, json.loads(args.acquisition_output.read_text(encoding="utf-8-sig")), args.channel_id)
    else:
        if not args.allow_network or not args.source_id or not args.adapter or not args.run_id:
            parser.error("acquire requires --allow-network, --source-id, --adapter and --run-id")
        source = next((r for r in rows(snapshot, "cloud_core_sources") if r["source_id"] == args.source_id), None)
        if not source:
            parser.error("source_id is absent from exact-revision snapshot")
        previous = json.loads(args.previous_output.read_text(encoding="utf-8-sig")) if args.previous_output else {}
        if previous and (previous.get("source_id") != args.source_id or previous.get("adapter") != args.adapter):
            parser.error("previous output belongs to another source or adapter")
        last = previous.get("attempts", [{}])[-1]
        if last.get("next_retry_at") and iso(last["next_retry_at"]) > now:
            parser.error("previous attempt is not due; wait until next_retry_at")
        result = acquire(source, args.adapter, args.run_id, now, prior=previous.get("cache"), max_attempts=args.attempt_limit)
        result.update(source_revision=snapshot["revision"], source_fingerprint=fingerprint(source))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"command": args.command, "output": str(args.output), "coverage": result.get("coverage"), "operation_count": sum(len(p["operations"]) for p in result.get("operations", [])), "status": result.get("status")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

