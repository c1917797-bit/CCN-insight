"""Validate discovery metadata without upgrading it to verified research facts.

CLI: --root <deployment> [--fixture <exact-native.json>] [--negative-tests].
Stable APIs: validate_collection_fixture, validate_collection_site,
validate_collection_ui, validate_collection_negative_cases.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from collection_schema import DEFINITIONS
from validate_monthly import _audit_date, _safe_source_url
from validate_pyramid import PageDOM, _function, _compact
from validate_research_workbench import SECRET_FIELD, SECRET_VALUE, BODY_FIELDS

DATE_KINDS = {"published", "updated", "source_claimed_date", "unverified"}
SELECTIONS = {"title_match_pending_review", "unmatched_title", "reference"}
REVIEW_STATUS = "listing_metadata_not_primary_review"
RUN_STATUSES = {"running", "completed", "partial", "failed"}
RETRIEVAL_STATUSES = {"success", "failed", "not_attempted", "skipped"}
COLLECTION_UI_KEYS = {
    "collection_run", "collection_scope", "collection_run_none", "collection_run_cutoff",
    "collection_attempted", "collection_successful", "collection_failed", "collection_dated",
    "collection_undated", "collection_candidates", "collection_discovery_boundary", "collection_current",
    "collection_entries", "collection_entries_help", "collection_entries_loading", "collection_entries_empty",
    "collection_entries_failed", "collection_entries_range", "collection_source_not_attempted",
    "collection_received", "collection_page_date", "collection_locator", "collection_selection",
    "collection_result_success", "collection_result_failed", "collection_result_not_attempted",
    "collection_result_skipped", "collection_run_running", "collection_run_completed",
    "collection_run_partial", "collection_run_failed", "collection_date_published",
    "collection_date_updated", "collection_date_source_claimed_date", "collection_date_unverified",
    "collection_selection_title_match_pending_review", "collection_selection_unmatched_title",
    "collection_selection_reference", "collection_review_listing_metadata_not_primary_review",
    "depth_primary_methods_and_selected_results",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def _rows(fixture, name, definition=None):
    envelope = fixture.get("tables", {}).get(name)
    require(envelope is not None, "missing collection snapshot table: " + name)
    if isinstance(envelope, dict):
        require(envelope.get("revision", fixture["revision"]) == fixture["revision"], name + ": mixed revision")
        require(isinstance(envelope.get("rows"), list), name + ": missing row frames")
        if definition and envelope.get("definition"):
            actual = envelope["definition"]
            require(actual.get("key_field") == definition["key_field"]
                    and set(actual.get("fields", {})) == set(definition["fields"])
                    and set(actual.get("required_fields", [])) == set(definition["required_fields"]), name + ": schema mismatch")
            for field, expected in definition["fields"].items():
                spec = actual["fields"][field]
                require(all(spec.get(key) == expected[key] for key in ("type", "role", "required"))
                        and spec.get("projection", "default") == "default"
                        and spec.get("source") is None, name + ": altered scalar schema " + field)
            require(set(index["field"] for index in actual.get("indexes", [])) >=
                    set(index["field"] for index in definition["indexes"]), name + ": missing index")
        envelope = envelope["rows"]
    require(isinstance(envelope, list), name + ": invalid frame list")
    rows, seen = [], set()
    for frame in envelope:
        require(isinstance(frame, dict) and isinstance(frame.get("deleted", False), bool), name + ": invalid frame")
        if frame.get("deleted"):
            continue
        row, key, version = frame.get("row"), frame.get("key"), frame.get("row_version")
        require(isinstance(key, str) and key and key not in seen, name + ": duplicate/missing frame key")
        require(isinstance(version, int) and not isinstance(version, bool) and version > 0, name + ": invalid row version")
        require(isinstance(row, dict), name + ": missing row")
        seen.add(key)
        if definition:
            require(row.get(definition["key_field"]) == key, name + ": frame/row identity mismatch")
            require(row.get("topic_id") == "cloud_core" and row.get("business_id") == "cloud-core", name + ": wrong ownership")
            require(set(row) == set(definition["fields"]), name + ": undeclared or missing scalar fields")
            for field, spec in definition["fields"].items():
                value = row[field]
                require(not isinstance(value, (list, dict)), name + ": nested payload")
                require((spec["type"] == "integer" and isinstance(value, int) and not isinstance(value, bool))
                        or (spec["type"] == "string" and isinstance(value, str)), name + ": wrong scalar type")
                require(not SECRET_FIELD.search(field) and field not in BODY_FIELDS and not field.endswith("url")
                        and field not in {"title", "title_zh", "title_en"}, name + ": parallel body/title/URL/secret authority")
                if isinstance(value, str):
                    require(len(value) <= 2500 and not SECRET_VALUE.search(value)
                            and not value.lstrip().startswith(("{", "[")), name + ": unsafe or oversized metadata")
        rows.append(row)
    return rows


def _index(rows, key):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows) and all(isinstance(value, str) and value for value in result), "duplicate/missing " + key)
    return result


def _day(value, context):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), context + ": invalid date")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise AssertionError(context + ": invalid calendar date") from error


def validate_collection_fixture(fixture, definitions=None):
    """Validate exact frames, foreign identities, dates and run/count reconciliation."""
    require(re.fullmatch(r"[0-9a-f]{40}", fixture.get("revision", "")), "collection needs exact native revision")
    definitions = definitions or DEFINITIONS
    require(set(definitions) == set(DEFINITIONS), "collection needs exactly three normalized tables")
    tables = {name: _rows(fixture, name, definitions[name]) for name in definitions}
    runs = _index(tables["ic_collection_runs"], "run_id")
    retrievals = _index(tables["ic_channel_retrievals"], "retrieval_id")
    entries = _index(tables["ic_collection_entries"], "entry_id")
    channels = _index(_rows(fixture, "ic_channels"), "channel_id")
    sources = _index(_rows(fixture, "cloud_core_sources"), "source_id")
    require(len(runs) <= 2000, "collection run metadata exceeds reader ceiling")
    require(len({(row["run_id"], row["channel_id"]) for row in retrievals.values()}) == len(retrievals), "duplicate channel attempt in a run")
    for row in sources.values():
        require(row.get("business_id") == "cloud-core", "collection source belongs to another business")
        _safe_source_url(row.get("canonical_url"), "collection canonical source")
    for run in runs.values():
        started = _audit_date(run["started_at"], "collection started_at")
        cutoff = _day(run["cutoff_date"], "collection cutoff_date")
        require(cutoff <= started, "collection cutoff follows acquisition date")
        require(run["status"] in RUN_STATUSES and run["scope_note_zh"].strip() and run["scope_note_en"].strip(), "invalid collection run status or scope")
        if run["completed_at"]:
            require(_audit_date(run["completed_at"], "collection completed_at") >= started, "collection completes before start")
        require(run["status"] == "running" or bool(run["completed_at"]), "finished collection lacks completion timestamp")
        counts = [run[field] for field in ("requested_channels", "attempted_channels", "successful_channels", "failed_channels", "dated_entries", "undated_entries", "candidate_entries")]
        require(all(value >= 0 for value in counts), "negative collection count")
        require(run["attempted_channels"] <= run["requested_channels"] <= len(channels), "collection count exceeds registered channels")
        own = [row for row in retrievals.values() if row["run_id"] == run["run_id"]]
        require(len(own) <= 2000, "collection retrieval metadata exceeds reader ceiling")
        attempted = [row for row in own if row["status"] in {"success", "failed"}]
        require(run["attempted_channels"] == len(attempted)
                and run["successful_channels"] == sum(row["status"] == "success" for row in own)
                and run["failed_channels"] == sum(row["status"] == "failed" for row in own), "run/channel attempt counts disagree")
        require(run["dated_entries"] == sum(row["dated_count"] for row in own)
                and run["undated_entries"] == sum(row["undated_count"] for row in own)
                and run["candidate_entries"] == sum(row["candidate_count"] for row in own), "run/entry totals disagree")
        if run["status"] == "completed":
            require(run["attempted_channels"] == run["requested_channels"], "completed run has unattempted requested channels")
    for row in retrievals.values():
        require(row["run_id"] in runs and row["channel_id"] in channels and row["source_id"] in sources, "orphan collection retrieval")
        run = runs[row["run_id"]]
        require(channels[row["channel_id"]]["source_id"] == row["source_id"], "retrieval channel/source identity differs")
        require(row["status"] in RETRIEVAL_STATUSES and row["method"].strip()
                and row["boundary_zh"].strip() and row["boundary_en"].strip(), "retrieval lacks outcome/method/boundary")
        require(0 <= row["http_status"] <= 599 and row["position"] >= 0, "invalid HTTP status or retrieval position")
        require(_audit_date(row["checked_at"], "retrieval checked_at") >= _audit_date(run["started_at"], "run started_at"), "retrieval precedes run")
        counts = [row[field] for field in ("received_count", "dated_count", "undated_count", "candidate_count")]
        require(all(value >= 0 for value in counts) and row["received_count"] <= 2000, "invalid bounded retrieval count")
        require(row["received_count"] == row["dated_count"] + row["undated_count"]
                and row["candidate_count"] <= row["received_count"], "retrieval date/candidate counts disagree")
        require((row["status"] == "failed" and bool(row["failure_code"]))
                or (row["status"] != "failed" and not row["failure_code"]), "failure outcome/code disagree")
        if row["status"] in {"failed", "not_attempted", "skipped"}:
            require(row["received_count"] == 0, "failed/unattempted retrieval claims collected entries")
        own = [entry for entry in entries.values() if entry["retrieval_id"] == row["retrieval_id"]]
        require(len(own) == row["received_count"]
                and sum(entry["date_kind"] != "unverified" for entry in own) == row["dated_count"]
                and sum(entry["date_kind"] == "unverified" for entry in own) == row["undated_count"]
                and sum(entry["selection_status"] == "title_match_pending_review" for entry in own) == row["candidate_count"], "retrieval/entry relationship counts disagree")
    for row in entries.values():
        require(row["run_id"] in runs and row["retrieval_id"] in retrievals
                and row["channel_id"] in channels and row["source_id"] in sources, "orphan collection entry")
        parent = retrievals[row["retrieval_id"]]
        require(parent["run_id"] == row["run_id"] and parent["channel_id"] == row["channel_id"], "entry is attached to another run/channel")
        require(parent["status"] == "success", "entry is attached to an unsuccessful retrieval")
        require(row["review_status"] == REVIEW_STATUS and row["selection_status"] in SELECTIONS, "listing metadata upgraded to research evidence")
        require(row["date_kind"] in DATE_KINDS and row["position"] >= 0 and row["locator"].strip(), "entry lacks date provenance or locator")
        observed = _audit_date(row["observed_at"], "entry observed_at")
        require(observed >= _audit_date(runs[row["run_id"]]["started_at"], "run started_at"), "entry observation precedes run")
        if row["date_kind"] == "unverified":
            require(row["date_value"] == "", "undated entry invents a current date")
        else:
            require(_day(row["date_value"], "entry date") <= _day(runs[row["run_id"]]["cutoff_date"], "run cutoff"), "entry date exceeds cutoff")
    return {"collection_snapshot": "pass", "collection_revision": fixture["revision"],
            "collection_rows": {name: len(rows) for name, rows in tables.items()},
            "discovery_entries_counted_as_primary_evidence": 0}


def validate_collection_site(site, definitions=None):
    for name, definition in (definitions or DEFINITIONS).items():
        binding = site.get("tables", {}).get(name, {})
        require(binding.get("path") == "data/tables/" + name and binding.get("writable") is False,
                name + ": collection binding must be native/read-only")
        require(isinstance(binding.get("max_rows"), int) and 0 < binding["max_rows"] <= 100, name + ": unbounded binding")
        require({index["field"] for index in definition["indexes"]} <= set(binding.get("filter_fields", [])), name + ": missing exact/scoped filter")
    return {"collection_readonly_bindings": "pass"}


def validate_collection_ui(root):
    page = Path(root) / "business_insight" / "cloud_core"
    html = (page / "index.html").read_text(encoding="utf-8-sig")
    js = (page / "compression.js").read_text(encoding="utf-8-sig")
    dom = PageDOM(html)
    require("collection-summary" in dom.ids(), "missing directly visible acquisition-run summary")
    require(not any(node.tag == "details" for node in dom.ids()["collection-summary"].ancestors()), "acquisition coverage is hidden in a fold")
    reads = _compact(_function(js, "loadCollectionRows"))
    require("meta.total<=2000" in reads and "request!==state.epoch" in reads and "collectionPending" in reads
            and "collectionCache" in reads and "validateEvidenceRevision(result,revision)" in reads, "collection metadata lacks bounded single-flight/revision/epoch contract")
    entries = _compact(_function(js, "loadCollectionEntries"))
    require("page('collection_entries','retrieval_id',retrievalId,revision,{offset,limit:20})" in entries
            and "loadRowsByKeys('cloud_core_sources',ids,revision" in entries
            and "collectionEpoch" in entries and "collectionPending" in entries, "entry disclosure lacks lazy bounded exact-source joins or stale fencing")
    start = _function(js, "start")
    require("loadCollectionRows('collection_runs'" in start and "loadCollectionRows('channel_retrievals'" in start
            and "loadCollectionEntries(" not in start and "'collection_entries'" not in start, "startup eagerly reads listing entries")
    require("node.open&&node.dataset.collectionRetrieval" in _compact(js), "entry reading is not driven by opening the channel disclosure")
    for locale in ("zh", "en"):
        pack = json.loads((page / "data" / ("focus-ui." + locale + ".json")).read_text(encoding="utf-8-sig"))
        require(COLLECTION_UI_KEYS <= set(pack["strings"])
                and all(isinstance(pack["strings"][key], str) and pack["strings"][key].strip() for key in COLLECTION_UI_KEYS), locale + ": incomplete collection UI labels")
    return {"collection_ui": "pass", "collection_entries_lazy_page_limit": 20,
            "collection_metadata_reader_ceiling": 2000, "collection_ui_bilingual": "complete"}


def validate_collection_negative_cases(fixture, definitions=None):
    validate_collection_fixture(fixture, definitions)
    mutations = []
    def mutate(name, table, operation, expected):
        candidate = copy.deepcopy(fixture)
        envelope = candidate["tables"][table]
        frames = envelope if isinstance(envelope, list) else envelope["rows"]
        row = next(frame["row"] for frame in frames if not frame.get("deleted"))
        operation(row)
        mutations.append((name, candidate, expected))
    mutate("inflated_attempts", "ic_collection_runs", lambda row: row.update(attempted_channels=row["attempted_channels"] + 1), "count")
    mutate("foreign_entry_source", "ic_collection_entries", lambda row: row.update(source_id="missing-source"), "orphan")
    mutate("discovery_as_primary_review", "ic_collection_entries", lambda row: row.update(review_status="primary_abstract_checked"), "upgraded")
    mutate("invented_undated_recency", "ic_collection_entries", lambda row: row.update(date_value="2026-99-99"), "date")
    mutate("parallel_title_authority", "ic_collection_entries", lambda row: row.update(title="copied title"), "scalar fields")
    for name, candidate, expected in mutations:
        try:
            validate_collection_fixture(candidate, definitions)
        except AssertionError as error:
            require(expected in str(error), name + ": rejected for unrelated reason: " + str(error))
        else:
            require(False, name + ": discovery semantic regression accepted")
    return {"collection_negative_cases": [name for name, _, _ in mutations], "collection_negative_cases_status": "pass"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--negative-tests", action="store_true")
    args = parser.parse_args()
    try:
        result = validate_collection_site(json.loads((args.root / ".mcpgit" / "site.json").read_text(encoding="utf-8-sig")))
        result.update(validate_collection_ui(args.root))
        if args.fixture:
            fixture = json.loads(args.fixture.read_text(encoding="utf-8-sig"))
            result.update(validate_collection_fixture(fixture))
            if args.negative_tests:
                result.update(validate_collection_negative_cases(fixture))
    except (AssertionError, OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"collection": "fail", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))

