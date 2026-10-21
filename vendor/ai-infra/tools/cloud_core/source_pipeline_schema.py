"""Normalized pipeline side tables; existing business tables remain unchanged."""

HISTORY_LIFECYCLE = "persistent"


def table(key, strings, integers=(), indexes=(), description=""):
    fields = {name: {"type": "string", "required": True, "role": "key" if name == key else "value"} for name in strings}
    fields.update({name: {"type": "integer", "required": True, "role": "value"} for name in integers})
    return {"key_field": key, "description": description, "fields": fields, "required_fields": list(fields),
            "indexes": [{"name": "idx_" + x, "field": x} for x in dict.fromkeys((key, *indexes))]}


DEFINITIONS = {
    "ic_pipeline_runs": table("run_id", ("run_id", "business_id", "topic_id", "source_revision", "rule_version", "started_at", "completed_at", "status"),
        ("total_sources", "processed_sources", "metadata_needed", "candidate_direct", "candidate_adjacent", "needs_relevance_review", "reviewed_visible", "reviewed_unpublished", "reconciliation_needed", "blocked_invalid", "duplicate_refs", "excluded_manual", "retryable_failure"),
        ("business_id", "topic_id", "completed_at", "status"),
        "Complete exact-revision audit of registered paper sources, not a count of relevant or reviewed papers. Stage counts conserve total_sources; duplicate_refs is orthogonal."),
    "ic_source_pipeline": table("source_id", ("source_id", "business_id", "topic_id", "run_id", "identity_key", "canonical_source_id", "source_fingerprint", "rule_version", "stage", "reason_code", "reason_zh", "reason_en", "next_action_zh", "next_action_en", "evidence_level", "updated_at"),
        ("priority",), ("business_id", "topic_id", "stage", "priority", "canonical_source_id", "reason_code"),
        "One current disposition per registered paper. Machine signals are candidates only; human screenings and source evidence remain separate authority. run_id is last changed run, not corpus membership."),
    "ic_source_route_candidates": table("match_id", ("match_id", "source_id", "business_id", "topic_id", "route_topic_id", "relation_kind", "match_basis", "rule_version", "run_id"),
        (), ("source_id", "business_id", "topic_id", "route_topic_id", "relation_kind"),
        "Machine title-level route hints requiring primary review; never authoritative technical-map placements."),
    "ic_source_acquisition_attempts": table("attempt_id", ("attempt_id", "run_id", "source_id", "adapter", "status", "error_code", "error_message", "attempted_at", "next_retry_at"),
        ("attempt", "http_status"), ("source_id", "run_id", "status", "next_retry_at"),
        "Bounded public metadata acquisition attempts, including retryable failures. No credentials, response bodies or research conclusions."),
}
