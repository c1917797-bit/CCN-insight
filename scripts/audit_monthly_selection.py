"""Audit selected monthly papers against an explicitly supplied local reading snapshot.

Read-only: no candidate is adopted, no reading status is promoted and nothing is published.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rows(table):
    path = ROOT / "data/compression/tables" / table / "rows.jsonl"
    return [record["row"] for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not (record := json.loads(line)).get("deleted")]


def audit(review_dir, scope_id):
    scopes = [r for r in rows("ic_monthly_scopes") if r["scope_id"] == scope_id]
    if len(scopes) != 1:
        raise ValueError("Expected exactly one existing scope")
    scope = scopes[0]
    refs = [r for r in rows("ic_monthly_route_evidence") if r["scope_id"] == scope_id]
    summary_ids = {r["summary_id"] for r in refs}
    summaries = {r["summary_id"]: r for r in rows("ic_paper_summaries") if r["summary_id"] in summary_ids}
    if set(summaries) != summary_ids:
        raise ValueError("Missing selected-paper summary")
    sources = {r["source_id"]: r for r in rows("cloud_core_sources")}
    events = {r["evidence_id"]: r for r in rows("ic_evidence_items")}
    index_path = review_dir / "data/paper-index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    if len({p["paper_id"] for p in index}) != len(index):
        raise ValueError("Duplicate paper identities in review snapshot")
    month = scope["period_id"]
    candidates = [p for p in index if p["placement"]["month"] == month
                  and p["placement"]["route"] in ("monthly_new", "monthly_revision")]
    topic_counts = {}
    for topic in sorted({r["compression_topic_id"] for r in refs}):
        topic_counts[topic] = len({r["summary_id"] for r in refs if r["compression_topic_id"] == topic})
    selected = []
    for sid, summary in sorted(summaries.items()):
        ref = next(r for r in refs if r["summary_id"] == sid)
        event = events[ref["evidence_id"]]
        source = sources[ref["source_id"]]
        selected.append({"title": source["title"], "url": summary["evidence_url"],
                         "review_status": summary["review_status"], "locator": summary["evidence_locator"],
                         "event_date": event["event_date"], "date_kind": event["date_kind"]})
    examples = []
    for paper_id in ["2610.04490", "2610.09212", "2610.20303"]:
        paper = next(p for p in index if p["paper_id"] == paper_id)
        registered = [s for s in sources.values() if paper_id in s.get("canonical_url", "")]
        examples.append({"paper_id": paper_id, "title": paper["title"], "url": paper["url"],
                         "relevance_in_local_snapshot": paper["review"]["relevance"],
                         "primary_source_registered": bool(registered),
                         "selected_in_scope": any(paper_id in s["url"] for s in selected),
                         "evidence_level": "abstract notes in local snapshot; not a new full-paper review"})
    return {"scope": scope, "review_index_sha256": hashlib.sha256(index_path.read_bytes()).hexdigest(),
            "local_snapshot_records": len(index),
            "local_candidate_routes": dict(collections.Counter(p["placement"]["route"] for p in candidates)),
            "local_candidate_method_tags_overlapping": dict(collections.Counter(tag for p in candidates for tag in p["review"]["routes"])),
            "selected_papers": selected, "selected_topic_counts_overlapping": topic_counts,
            "selected_review_depth": dict(collections.Counter(p["review_status"] for p in selected)),
            "selected_date_kinds": dict(collections.Counter(p["date_kind"] for p in selected)),
            "unselected_examples": examples,
            "limits": ["Local relevance annotations are prior judgments, not independently validated precision/recall.",
                       "Revision dates alone do not prove a substantive change.",
                       "The snapshot covers an arXiv query, not every registered conference or industry source.",
                       "Selection is an editorial first batch; no field-wide representative ranking is recorded."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--scope", default="ic-2026-10-model-reviewed-20261029-v1")
    args = parser.parse_args()
    print(json.dumps(audit(args.review_dir, args.scope), ensure_ascii=False, indent=2))
