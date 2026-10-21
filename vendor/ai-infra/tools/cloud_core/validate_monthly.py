"""Fail-closed validation of an exact TableGit monthly-evidence snapshot.

The input is a read fixture, never a business authority or a synthetic substitute:
{revision, tables: {name: frames | {definition, rows: frames}}}. A frame has
{key, row, row_version, deleted}. Missing fixtures/tables never count as a pass.
Only Python's standard library is used. See ``validate_monthly_fixture`` for the
pure function; ``validate_monthly_snapshot`` is the existing validator adapter.
"""
from __future__ import annotations

import argparse
import datetime as dt
import importlib
import ipaddress
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit


BUSINESS_ID = "cloud-core"
TOPIC_ID = "cloud_core"
TABLE_KEYS = {
    "ic_monthly_scopes": "scope_id",
    "ic_evidence_items": "evidence_id",
    "ic_monthly_evidence_cells": "link_id",
    "ic_monthly_cell_reviews": "review_id",
}
SCALAR_TYPES = {"string", "text", "markdown", "integer", "number"}
STATUS_SCOPE = {"reviewed_sample", "vault_partial_catalog", "public_metadata_catalog"}
STATUS_EVIDENCE = {"primary_abstract_checked", "vault_title_candidate_unverified", "public_metadata_candidate"}
STATUS_REVIEW = {"reviewed_sample", "sample_gap", "title_candidate_review", "metadata_catalog_review"}
DATE_KINDS = {"first_submission", "revision", "source_declared_date"}
DATE_PRECISION = {"day", "month", "year"}
MONTH_BASIS = {"primary_event_date", "source_declared_publication_date"}
FORBIDDEN_QUERY_KEYS = {
    "token", "accesstoken", "refreshtoken", "idtoken", "authtoken",
    "auth", "authorization", "authentication", "password", "passwd",
    "pwd", "secret", "clientsecret", "apikey", "key", "credential",
    "credentials", "bearer", "signature", "sig", "jwt", "session",
    "sessionid", "sessiontoken", "xamzcredential", "xamzsignature",
    "xamzsecuritytoken",
}


class MonthlyValidationError(AssertionError):
    """A reviewable snapshot invariant failed; callers must not report pass."""


def require(condition, message):
    if not condition:
        raise MonthlyValidationError(message)


def _definitions():
    """Support both the deployed module name and the local authoring name."""
    for name in ("monthly_schema", "monthly_model"):
        try:
            module = importlib.import_module(name)
        except ModuleNotFoundError as error:
            if error.name != name:
                raise
            continue
        return module.DEFINITIONS
    raise MonthlyValidationError("monthly schema module is missing; validation was not run")


def _rows_and_definition(fixture, name, expected=None):
    require(name in fixture["tables"], f"missing required snapshot table: {name}")
    entry = fixture["tables"][name]
    if isinstance(entry, list):
        frames, definition = entry, expected
    else:
        require(isinstance(entry, dict), f"{name}: invalid table envelope")
        frames = entry.get("rows")
        definition = entry.get("definition") or expected
    require(isinstance(frames, list), f"{name}: missing frame array")
    if expected:
        require(isinstance(definition, dict), f"{name}: missing table definition")
        require(definition.get("key_field") == expected["key_field"], f"{name}: wrong primary key field")
        fields = definition.get("fields")
        require(isinstance(fields, dict), f"{name}: invalid fields definition")
        for key, spec in expected["fields"].items():
            require(key in fields, f"{name}: required schema field missing: {key}")
            require(fields[key].get("type") == spec["type"], f"{name}.{key}: schema type mismatch")
        require(all(isinstance(spec, dict) and spec.get("type") in SCALAR_TYPES for spec in fields.values()),
                f"{name}: monthly business fields must be scalar")
    rows, frame_keys = [], set()
    key_field = expected["key_field"] if expected else None
    for index, frame in enumerate(frames):
        context = f"{name} frame {index}"
        require(isinstance(frame, dict), context + ": invalid frame")
        require(isinstance(frame.get("deleted", False), bool), context + ": deleted must be boolean")
        if frame.get("deleted"):
            continue
        key, row, version = frame.get("key"), frame.get("row"), frame.get("row_version")
        require(isinstance(key, str) and key, context + ": missing key")
        require(key not in frame_keys, f"{name}: duplicate active frame key {key}")
        frame_keys.add(key)
        require(isinstance(version, int) and not isinstance(version, bool) and version >= 1,
                context + ": invalid row version")
        require(isinstance(row, dict), context + ": missing row")
        if key_field:
            require(row.get(key_field) == key, context + ": row primary key differs from frame key")
            require(row.get("business_id") == BUSINESS_ID and row.get("topic_id") == TOPIC_ID,
                    context + ": wrong business/topic")
            for field in expected["required_fields"]:
                require(field in row and row[field] is not None, context + f": missing required {field}")
            for field, value in row.items():
                require(field in definition["fields"], context + f": unknown field {field}")
                if value is None:
                    continue
                kind = definition["fields"][field]["type"]
                if kind in {"string", "text", "markdown"}:
                    require(isinstance(value, str), context + f": {field} must be text")
                elif kind == "integer":
                    require(isinstance(value, int) and not isinstance(value, bool), context + f": {field} must be integer")
                elif kind == "number":
                    require(isinstance(value, (int, float)) and not isinstance(value, bool), context + f": {field} must be number")
        rows.append(row)
    return rows


def _index(rows, field, name):
    index = {}
    for row in rows:
        key = row.get(field)
        require(isinstance(key, str) and key, f"{name}: missing {field}")
        require(key not in index, f"{name}: duplicate {field} {key}")
        index[key] = row
    return index


def _date(value, context):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value),
            context + ": expected ISO calendar date YYYY-MM-DD")
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise MonthlyValidationError(context + ": invalid calendar date") from None


def _audit_date(value, context):
    """Audit timestamps may be an ISO date or an explicitly zoned ISO time."""
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return _date(value, context)
    require(isinstance(value, str), context + ": missing audit date")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise MonthlyValidationError(context + ": invalid ISO timestamp") from None
    require(parsed.tzinfo is not None, context + ": timestamp must include UTC offset")
    return parsed.astimezone(dt.timezone.utc).date()


def _event_range(value, precision, context):
    require(precision in DATE_PRECISION, context + ": unknown date precision")
    if precision == "day":
        date = _date(value, context)
        return date, date
    if precision == "month":
        require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?", value),
                context + ": month precision must preserve an ISO month")
        try:
            first = dt.date.fromisoformat(value[:7] + "-01")
            next_month = dt.date(first.year + (first.month == 12), first.month % 12 + 1, 1)
        except ValueError:
            raise MonthlyValidationError(context + ": invalid month") from None
        return first, next_month - dt.timedelta(days=1)
    require(isinstance(value, str) and re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?", value),
            context + ": year precision must preserve an ISO year")
    year = int(value[:4])
    try:
        return dt.date(year, 1, 1), dt.date(year, 12, 31)
    except ValueError:
        raise MonthlyValidationError(context + ": invalid year") from None


def _safe_source_url(value, context):
    require(isinstance(value, str) and value and value == value.strip(), context + ": missing/whitespace URL")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in value), context + ": control character in URL")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise MonthlyValidationError(context + ": malformed URL") from None
    require(parsed.scheme.lower() in {"https", "http"}, context + ": source must be an original public web URL")
    require(parsed.hostname and parsed.username is None and parsed.password is None,
            context + ": URL must not carry userinfo or credentials")
    host = parsed.hostname.lower().rstrip(".")
    require(host not in {"localhost", "localhost.localdomain"} and not host.endswith((".localhost", ".local")),
            context + ": local host is not a public source URL")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        require(address.is_global, context + ": nonpublic IP is not an original public source")
    for component in (parsed.query, parsed.fragment):
        decoded = unquote(component)
        for key, unused_value in parse_qsl(decoded, keep_blank_values=True):
            normalized = re.sub(r"[^a-z0-9]", "", key.lower())
            has_secret_name = any(term in normalized for term in ("token", "password", "passwd", "secret", "credential", "apikey", "bearer", "signature"))
            has_auth_name = normalized.startswith("auth") and not normalized.startswith("author")
            require(normalized not in FORBIDDEN_QUERY_KEYS and not has_secret_name and not has_auth_name,
                    context + ": URL carries an authentication/secret parameter")
        require(not re.search(r"(?:^|[&#;/])(?:bearer|authorization|access[_-]?token|auth[_-]?token|password|api[_-]?key)[:=/]", decoded, re.I),
                context + ": URL carries authentication material")
    require(not re.search(r"/(?:access[_-]?token|auth[_-]?token|api[_-]?key|password)/[^/]+", unquote(parsed.path), re.I),
            context + ": credentials embedded in URL path")
    return parsed


def validate_monthly_fixture(fixture, definitions=None):
    """Validate actual four-table rows and their bounded canonical FK snapshot.

    Returns counts only after every invariant passes. Raises
    MonthlyValidationError on the first failure. No source fetching, mutations,
    substitute rows, default revision or missing-table success is performed.
    """
    require(isinstance(fixture, dict), "fixture must be a mapping")
    revision = fixture.get("revision")
    require(isinstance(revision, str) and re.fullmatch(r"[0-9a-f]{40}", revision), "missing exact TableGit revision")
    require(isinstance(fixture.get("tables"), dict), "fixture tables are missing")
    definitions = definitions or _definitions()
    tables = {}
    for name, key in TABLE_KEYS.items():
        require(name in definitions and definitions[name].get("key_field") == key, f"missing/wrong expected schema: {name}")
        tables[name] = _rows_and_definition(fixture, name, definitions[name])
    for name in ("ic_objects", "ic_methods", "ic_cells", "ic_trend_periods", "cloud_core_sources"):
        tables[name] = _rows_and_definition(fixture, name)
    objects = _index(tables["ic_objects"], "object_id", "ic_objects")
    methods = _index(tables["ic_methods"], "method_id", "ic_methods")
    cells = _index(tables["ic_cells"], "cell_id", "ic_cells")
    periods = _index(tables["ic_trend_periods"], "period_id", "ic_trend_periods")
    sources = _index(tables["cloud_core_sources"], "source_id", "cloud_core_sources")
    scopes = _index(tables["ic_monthly_scopes"], "scope_id", "ic_monthly_scopes")
    evidence = _index(tables["ic_evidence_items"], "evidence_id", "ic_evidence_items")
    require(scopes, "monthly scopes are empty; no collection scope was verified")
    require(set(objects) == set("WAKCMVS"), "object dictionary must contain exactly W/A/K/C/M/V/S")
    require(set(methods) == set("QLSPDG"), "method dictionary must contain exactly Q/L/S/P/D/G")
    require(len(cells) == 42 and set(cells) == {o + "_" + m for o in objects for m in methods},
            "canonical cell dictionary is not the complete 7 x 6 matrix")
    for key, cell in cells.items():
        require(cell.get("object_id") in objects and cell.get("method_id") in methods, f"{key}: dangling object/method")
        require(key == cell["object_id"] + "_" + cell["method_id"], f"{key}: inconsistent canonical cell identity")
    for source_id, source in sources.items():
        require(source.get("business_id") == BUSINESS_ID, f"source {source_id}: wrong business")
        _safe_source_url(source.get("canonical_url"), f"source {source_id}")
    documents = None
    if any(row.get("source_document_id") for row in evidence.values()):
        documents = _index(_rows_and_definition(fixture, "cloud_core_documents"), "document_id", "cloud_core_documents")

    scope_windows = {}
    for scope_id, scope in scopes.items():
        require(scope["status"] in STATUS_SCOPE, f"{scope_id}: unknown collection status")
        require(scope["month_basis"] in MONTH_BASIS, f"{scope_id}: unknown date basis")
        period = periods.get(scope["period_id"])
        require(period is not None, f"{scope_id}: dangling period")
        month = period.get("month")
        require(isinstance(month, str) and re.fullmatch(r"\d{4}-\d{2}", month), f"{scope_id}: invalid period month")
        start = _date(scope["window_start"], f"{scope_id}.window_start")
        end = _date(scope["window_end"], f"{scope_id}.window_end")
        require(start <= end and start.isoformat()[:7] == month and end.isoformat()[:7] == month,
                f"{scope_id}: collection window differs from period month")
        collected = _audit_date(scope["collected_at"], f"{scope_id}.collected_at")
        require(collected >= end, f"{scope_id}: a completed sample cannot end after its collection date")
        require(all(scope.get(field, "").strip() for field in ("selection_rule", "dedup_rule", "coverage_note", "source_pool", "source_revision")),
                f"{scope_id}: sampling/provenance boundary is empty")
        expected_basis = "primary_event_date" if scope["status"] == "reviewed_sample" else "source_declared_publication_date"
        require(scope["month_basis"] == expected_basis, f"{scope_id}: source status/date basis mismatch")
        scope_windows[scope_id] = start, end, collected

    event_source_identity = set()
    for evidence_id, item in evidence.items():
        require(item["source_id"] in sources, f"{evidence_id}: dangling canonical source")
        require(item["status"] in STATUS_EVIDENCE and item["date_kind"] in DATE_KINDS, f"{evidence_id}: unknown evidence/date status")
        event_start, event_end = _event_range(item["event_date"], item["date_precision"], f"{evidence_id}.event_date")
        publication_start, publication_end = _event_range(item["publication_date"], item["date_precision"], f"{evidence_id}.publication_date")
        require(publication_start <= event_start, f"{evidence_id}: event precedes source's declared first date")
        if item["status"] == "primary_abstract_checked":
            verified = _audit_date(item["verified_at"], f"{evidence_id}.verified_at")
            require(verified >= event_end, f"{evidence_id}: event occurs after verification")
            require(item["date_kind"] in {"first_submission", "revision"} and item["date_precision"] == "day",
                    f"{evidence_id}: primary event must preserve exact first/revision day")
            require(re.fullmatch(r"v[1-9]\d*", item["observed_version"]), f"{evidence_id}: invalid arXiv version")
            if item["date_kind"] == "first_submission":
                require(event_start == publication_start, f"{evidence_id}: first submission and event dates differ")
            else:
                require(int(item["observed_version"][1:]) >= 2, f"{evidence_id}: a revision cannot use v1")
            parsed = _safe_source_url(sources[item["source_id"]]["canonical_url"], f"{evidence_id}.url")
            require(parsed.hostname.lower() == "arxiv.org" and re.fullmatch(r"/abs/\d{4}\.\d{4,5}(?:v[1-9]\d*)?", parsed.path),
                    f"{evidence_id}: checked primary source must be original arXiv abstract URL")
            # The ID prefix is deliberately never used to derive submission month.
        elif item["status"] == "public_metadata_candidate":
            checked = _audit_date(item["verified_at"], f"{evidence_id}.metadata_checked_at")
            require(checked >= event_end and item["date_precision"] == "day", f"{evidence_id}: invalid public metadata date")
            require(item["provenance_kind"] in {"arxiv_official_api_metadata", "github_official_release_metadata", "public_listing_date_metadata"}, f"{evidence_id}: missing metadata provenance")
            if item["date_kind"] in {"first_submission", "revision"}:
                parsed = _safe_source_url(sources[item["source_id"]]["canonical_url"], f"{evidence_id}.url")
                require(item["provenance_kind"] == "arxiv_official_api_metadata" and parsed.hostname.lower() == "arxiv.org" and re.fullmatch(r"/abs/\d{4}\.\d{4,5}", parsed.path), f"{evidence_id}: non-arXiv event masquerades as submission")
                require(re.fullmatch(r"v[1-9]\d*", item["observed_version"]), f"{evidence_id}: missing observed arXiv version")
                require((item["date_kind"] == "first_submission" and event_start == publication_start) or (item["date_kind"] == "revision" and int(item["observed_version"][1:]) >= 2), f"{evidence_id}: invalid first/revision metadata")
            else:
                require(event_start == publication_start, f"{evidence_id}: public listing invents a first date")
        else:
            require(item["date_kind"] == "source_declared_date", f"{evidence_id}: a vault-title candidate cannot assert a verified submission/revision")
            require(item["verified_at"] == "" and item["observed_version"] == "",
                    f"{evidence_id}: unverified vault title must not claim a verification date or observed version")
            require(event_start == publication_start and event_end == publication_end,
                    f"{evidence_id}: local declared-date event differs from declared publication date")
        if item.get("source_document_id"):
            require(item["source_document_id"] in documents, f"{evidence_id}: dangling source document")
        identity = item["source_id"], item["date_kind"], item["event_date"], item["observed_version"]
        require(identity not in event_source_identity, f"{evidence_id}: duplicate canonical source event")
        event_source_identity.add(identity)

    evidence_sources_by_cell = defaultdict(set)
    linked_evidence, unique_links = set(), set()
    for row in tables["ic_monthly_evidence_cells"]:
        key = row["link_id"]
        scope_id, evidence_id, cell_id = row["scope_id"], row["evidence_id"], row["cell_id"]
        require(scope_id in scopes and evidence_id in evidence and cell_id in cells, f"{key}: dangling scope/evidence/cell")
        scope, item = scopes[scope_id], evidence[evidence_id]
        require(row["period_id"] == scope["period_id"], f"{key}: link period differs from scope")
        require(row["scope_cell_key"] == scope_id + "__" + cell_id, f"{key}: wrong scope-cell index")
        require(row["status"] == item["status"], f"{key}: link/evidence review status differs")
        expected_status = {"reviewed_sample": {"primary_abstract_checked"}, "vault_partial_catalog": {"vault_title_candidate_unverified"}, "public_metadata_catalog": {"public_metadata_candidate", "primary_abstract_checked"}}[scope["status"]]
        require(item["status"] in expected_status, f"{key}: evidence mixed into incompatible scope")
        require(all(row.get(field, "").strip() for field in ("stage", "role", "mechanism_summary", "limitation", "validation_question")),
                f"{key}: empty mechanism/condition/validation boundary")
        begin, finish = _event_range(item["event_date"], item["date_precision"], f"{key}.event_date")
        start, end, collected = scope_windows[scope_id]
        require(start <= begin and finish <= end, f"{key}: evidence event outside scope window")
        if item["status"] in {"primary_abstract_checked", "public_metadata_candidate"}:
            require(_audit_date(item["verified_at"], f"{key}.verified_at") <= collected,
                    f"{key}: evidence verified after snapshot collection")
        identity = scope_id, evidence_id, cell_id
        require(identity not in unique_links, f"{key}: duplicate scope/evidence/cell relation")
        unique_links.add(identity)
        linked_evidence.add(evidence_id)
        evidence_sources_by_cell[scope_id, cell_id].add(item["source_id"])
    require(linked_evidence == set(evidence), "evidence items without monthly cell placement")

    reviews_by_scope, unique_reviews = defaultdict(set), set()
    for row in tables["ic_monthly_cell_reviews"]:
        key = row["review_id"]
        scope_id, cell_id = row["scope_id"], row["cell_id"]
        require(scope_id in scopes and cell_id in cells, f"{key}: dangling review scope/cell")
        scope = scopes[scope_id]
        require(row["period_id"] == scope["period_id"] and row["scope_cell_key"] == scope_id + "__" + cell_id,
                f"{key}: wrong period or scope-cell index")
        require((scope_id, cell_id) not in unique_reviews, f"{key}: duplicate scope-cell review")
        unique_reviews.add((scope_id, cell_id))
        reviews_by_scope[scope_id].add(cell_id)
        actual_count = len(evidence_sources_by_cell[scope_id, cell_id])
        require(row["sample_count"] >= 0 and row["sample_count"] == actual_count,
                f"{key}: sample_count must equal distinct canonical source identities ({actual_count})")
        require(row["status"] in STATUS_REVIEW, f"{key}: unknown review status")
        if actual_count == 0:
            require(row["status"] == "sample_gap" and row["change_kind"] == "collection_gap",
                    f"{key}: zero reviewed samples must be a collection gap, not a universal zero")
        elif scope["status"] == "reviewed_sample":
            require(row["status"] == "reviewed_sample" and row["change_kind"] == "mechanism_watch", f"{key}: primary review status mismatch")
        elif scope["status"] == "public_metadata_catalog":
            require(row["status"] == "metadata_catalog_review" and row["change_kind"] == "metadata_candidate_watch", f"{key}: metadata catalog review status mismatch")
        else:
            require(row["status"] == "title_candidate_review" and row["change_kind"] == "title_candidate_watch", f"{key}: title-only review status mismatch")
        comparison = row["comparison_scope_id"]
        require(not comparison or comparison in scopes, f"{key}: missing comparison scope")
        # This refresh has no comparable repeated collection protocol. New titles,
        # revised papers and differing source pools cannot establish rise/fall.
        require(row["direction"] == "not_comparable", f"{key}: an unsupported comparison asserts a trend direction")
        require(not comparison, f"{key}: this non-comparable refresh must not imply a baseline scope")
        require(not re.search(r"上升|升温|走高|走低|激增|环比|同比|增速|增长率|[↑↓]|\b(?:rising|surging|warming)\b", row["highlight"], re.I),
                f"{key}: review highlight asserts growth without a comparable baseline")
        require(row["highlight"].strip() and row["next_question"].strip(), f"{key}: blank interpretation/action")
        require(_audit_date(row["reviewed_at"], f"{key}.reviewed_at") >= scope_windows[scope_id][2], f"{key}: review predates collection")
    for scope_id in scopes:
        require(reviews_by_scope[scope_id] == set(cells), f"{scope_id}: exactly 42 distinct cell reviews are required")

    return {
        "monthly_snapshot": "pass",
        "revision": revision,
        "monthly_table_rows": {name: len(tables[name]) for name in TABLE_KEYS},
        "monthly_scopes": len(scopes),
        "reviewed_cells_per_scope": {scope_id: len(reviews_by_scope[scope_id]) for scope_id in scopes},
        "distinct_sources_per_scope": {
            scope_id: len({evidence[row["evidence_id"]]["source_id"] for row in tables["ic_monthly_evidence_cells"] if row["scope_id"] == scope_id})
            for scope_id in scopes
        },
        "safe_source_urls": len(sources),
        "source_events": len(evidence),
    }


def validate_monthly_snapshot(path, definitions=None):
    """Read a supplied actual snapshot; missing files propagate as failure."""
    path = Path(path)
    require(path.is_file(), "snapshot file is missing; validation was not run: " + str(path))
    with path.open(encoding="utf-8") as handle:
        fixture = json.load(handle)
    return validate_monthly_fixture(fixture, definitions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True, help="Exact native TableGit snapshot fixture")
    args = parser.parse_args()
    try:
        result = validate_monthly_snapshot(args.snapshot)
    except (MonthlyValidationError, OSError, ValueError) as error:
        print(json.dumps({"monthly_snapshot": "fail", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False))
