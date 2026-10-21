"""Persistent scalar discovery-run metadata, separate from research verification.

Titles and public URLs belong only to cloud_core_sources. These three tables
retain acquisition relationships and counts, never article bodies or secrets.
"""

HISTORY_LIFECYCLE = "persistent"


def _table(key, description, strings, integers=(), indexes=()):
    fields = {name: {"type": "string", "required": True,
                     "role": "key" if name == key else "value"} for name in strings}
    fields.update({name: {"type": "integer", "required": True, "role": "value"}
                   for name in integers})
    return {"key_field": key, "description": description, "fields": fields,
            "required_fields": list(fields),
            "indexes": [{"name": "idx_" + name, "field": name}
                        for name in dict.fromkeys((key, "topic_id", "business_id", *indexes))]}


DEFINITIONS = {
    "ic_collection_runs": _table(
        "run_id", "Persistent bounded source acquisition run; completion is not primary-source review.",
        ("run_id", "topic_id", "business_id", "started_at", "cutoff_date", "completed_at", "status",
         "scope_note_zh", "scope_note_en"),
        ("requested_channels", "attempted_channels", "successful_channels", "failed_channels",
         "dated_entries", "undated_entries", "candidate_entries"),
        ("status", "cutoff_date")),
    "ic_channel_retrievals": _table(
        "retrieval_id", "One source-channel attempt in a run, with truthful acquisition outcome and counts.",
        ("retrieval_id", "run_id", "channel_id", "source_id", "topic_id", "business_id", "status",
         "method", "checked_at", "boundary_zh", "boundary_en", "failure_code"),
        ("http_status", "received_count", "dated_count", "undated_count", "candidate_count", "position"),
        ("run_id", "channel_id", "source_id", "status")),
    "ic_collection_entries": _table(
        "entry_id", "Listing-metadata relationship only: canonical source identity, date provenance and title screening.",
        ("entry_id", "run_id", "retrieval_id", "channel_id", "source_id", "topic_id", "business_id",
         "date_value", "date_kind", "observed_at", "locator", "review_status", "selection_status"),
        ("position",),
        ("run_id", "retrieval_id", "channel_id", "source_id", "date_kind", "review_status", "selection_status")),
}

