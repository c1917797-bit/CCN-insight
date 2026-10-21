"""Validate normalized lineages and bounded source screens in an exact snapshot.

Reads {revision, tables: {name: frames | {definition, rows: frames}}}.
Historical lineage expectations remain configurable; source scans may grow.
The expectations are explicit CLI options; no source retrieval or writes occur.
Historical first-submission dates never become new monthly evidence by import.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from lineage_schema import DEFINITIONS
from validate_monthly import (
    _audit_date, _date, _index, _rows_and_definition, _safe_source_url,
)

BUSINESS_ID, TOPIC_ID = "cloud-core", "cloud_core"
RELATION_KINDS = {"extends", "generalizes", "addresses_limitation", "parallel", "analyst_comparison"}
SCREENING_KINDS = {"in_scope", "adjacent", "excluded", "pending"}
COUNT_FIELDS = (
    "requested_limit", "received_count", "title_candidate_count", "selected_count",
    "adjacent_count", "excluded_count", "pending_count", "title_not_matched_count",
)


class LineageValidationError(AssertionError):
    """The exact snapshot is incomplete or violates a reviewable invariant."""


def require(condition, message):
    if not condition:
        raise LineageValidationError(message)


def validate_lineage_site(site):
    """All six hosted tables expose bounded, read-only native queries."""
    require(isinstance(site, dict) and isinstance(site.get("tables"), dict), "missing hosted table configuration")
    for name, definition in DEFINITIONS.items():
        hosted = site["tables"].get(name)
        require(isinstance(hosted, dict), name + ": missing hosted binding")
        require(hosted.get("path") == "data/tables/" + name and hosted.get("writable") is False,
                name + ": native table must be read-only")
        # The six collections load by topic; no primary-key filter is queried.
        filters = {"topic_id", "business_id"}
        require(filters <= set(hosted.get("filter_fields", [])), name + ": missing bounded filter")
        require(isinstance(hosted.get("max_rows"), int) and 0 < hosted["max_rows"] <= 100,
                name + ": hosted small-collection limit is not bounded")
    return {"lineage_readonly_tables": len(DEFINITIONS)}


def _owned(row, context, topic=True):
    require(row.get("business_id") == BUSINESS_ID and (not topic or row.get("topic_id") == TOPIC_ID),
            context + ": cross-business/topic reference")


def _canonical(fixture, name, key):
    rows = _rows_and_definition(fixture, name)
    index = _index(rows, key, name)
    entry = fixture["tables"][name]
    frames = entry if isinstance(entry, list) else entry["rows"]
    for frame in frames:
        if not frame.get("deleted"):
            require(frame["row"].get(key) == frame["key"], name + ": row identity differs from frame key")
    return index


def _primary_paper(source, context):
    _owned(source, context, topic=False)
    parsed = _safe_source_url(source.get("canonical_url"), context)
    require(parsed.hostname in {"arxiv.org", "www.arxiv.org"} and parsed.path.startswith("/abs/"),
            context + ": representative evidence must use the original arXiv abstract URL")
    identifier = parsed.path.removeprefix("/abs/")
    require(re.fullmatch(r"\d{4}\.\d{4,5}", identifier), context + ": expected canonical unversioned paper identity")
    require(source.get("external_id") == identifier and source.get("provider") == "arxiv",
            context + ": source URL/provider/external identity drift")
    require(isinstance(source.get("title"), str) and source["title"].strip(), context + ": missing canonical title")
    return identifier


def validate_lineage_fixture(fixture, *, expected_lineages=9, expected_scans=None, expected_historical_sources=23):
    """Validate scalar schemas, canonical FKs, dates, graph and sample scope."""
    require(isinstance(fixture, dict) and re.fullmatch(r"[0-9a-f]{40}", str(fixture.get("revision", ""))),
            "snapshot needs an exact 40-character native revision")
    require(isinstance(fixture.get("tables"), dict), "snapshot tables are missing")
    tables, keys = {}, {}
    for name, definition in DEFINITIONS.items():
        rows = _rows_and_definition(fixture, name, definition)
        require(len(rows) <= 100, name + ": exceeds the UI bounded small-table contract")
        entry = fixture["tables"][name]
        actual = entry.get("definition", definition) if isinstance(entry, dict) else definition
        require(set(actual["fields"]) == set(definition["fields"]), name + ": unexpected schema field")
        require(set(definition["required_fields"]) <= set(actual.get("required_fields", [])),
                name + ": required schema fields drifted")
        for field, spec in definition["fields"].items():
            require(actual["fields"][field].get("required") is True, name + "." + field + ": must remain required")
            if spec["type"] in {"string", "text", "markdown"}:
                require(all(isinstance(row[field], str) and (row[field].strip() or (name == "ic_source_scans" and row.get("origin_kind") == "imported_corpus_regression_sample" and field in {"channel_source_id", "listing_date"})) for row in rows),
                        name + "." + field + ": empty required text")
        tables[name] = rows
        keys[name] = _index(rows, definition["key_field"], name)

    lineages, nodes = keys["ic_lineages"], keys["ic_lineage_nodes"]
    scans, screenings = keys["ic_source_scans"], keys["ic_source_screenings"]
    for actual, expected, label in (
        (len(lineages), expected_lineages, "routes"), (len(scans), expected_scans, "source scans"),
    ):
        require(expected is None or actual == expected, f"expected {expected} {label}; found {actual}")
    sources = _canonical(fixture, "cloud_core_sources", "source_id")
    techniques = _canonical(fixture, "ic_techniques", "technique_id")
    cells = _canonical(fixture, "ic_cells", "cell_id")
    placements = _canonical(fixture, "ic_placements", "placement_id")
    refs = _canonical(fixture, "ic_source_refs", "reference_id")
    require(len(cells) == 42, "lineages must retain the canonical 42-cell map")
    exact_refs = {(row["technique_id"], row["source_id"]): row for row in refs.values()}
    lineage_cells, lineage_nodes = defaultdict(set), defaultdict(list)
    for link in tables["ic_lineage_cells"]:
        require(link["lineage_id"] in lineages and link["cell_id"] in cells, "dangling route/canonical-cell link")
        _owned(cells[link["cell_id"]], "lineage cell")
        require(link["cell_id"] not in lineage_cells[link["lineage_id"]], "duplicate route-cell placement")
        lineage_cells[link["lineage_id"]].add(link["cell_id"])
    historical_sources = set()
    for node in nodes.values():
        require(node["lineage_id"] in lineages and node["technique_id"] in techniques and node["source_id"] in sources,
                "lineage node has a missing route/technique/source")
        technique = techniques[node["technique_id"]]
        _owned(technique, "lineage technique")
        require(technique.get("inference_scope") != "training_only", "training-only technique in inference lineage")
        require(isinstance(technique.get("mechanism"), str) and technique["mechanism"].strip(), "missing canonical mechanism")
        require(technique.get("verification_status") == "primary_mechanism_checked", "unchecked mechanism in checked lineage")
        identifier = _primary_paper(sources[node["source_id"]], "lineage source")
        submitted = _date(node["first_submitted_on"], "lineage first submission")
        checked = _audit_date(node["checked_at"], "lineage node check")
        require(submitted <= checked, "lineage check predates publication")
        # An announcement identifier can follow a late-month UTC submission.
        # It must not substitute for the explicitly checked first-submission date.
        identifier_month = (2000 + int(identifier[:2])) * 12 + int(identifier[2:4])
        submission_month = submitted.year * 12 + submitted.month
        require(identifier_month - submission_month in {0, 1}, "first-submission date differs from the original paper era")
        require(re.fullmatch(r"v[1-9]\d*", node["observed_version"]), "lineage requires an explicit checked arXiv version")
        ref = exact_refs.get((node["technique_id"], node["source_id"]))
        require(ref is not None, "lineage technique and source are not the same canonical reference")
        _owned(ref, "lineage source reference")
        require(ref.get("checked_scope") == "mechanism_only", "lineage reference claims an unreviewed evidence scope")
        require(node["position"] >= 0, "negative lineage node position")
        lineage_nodes[node["lineage_id"]].append(node)
        historical_sources.add(node["source_id"])
    require(expected_historical_sources is None or len(historical_sources) == expected_historical_sources,
            "historical representative source count differs from the reviewed import")
    for lineage in lineages.values():
        require(lineage_nodes[lineage["lineage_id"]] and lineage_cells[lineage["lineage_id"]], "route lacks representative nodes or cells")
        require(lineage["status"] == "primary_mechanism_checked" and lineage["position"] >= 0, "invalid route maturity/position")
        checked = _audit_date(lineage["checked_at"], "route check")
        require(all(_audit_date(node["checked_at"], "node check") <= checked for node in lineage_nodes[lineage["lineage_id"]]),
                "route check predates its node review")
        positions = [node["position"] for node in lineage_nodes[lineage["lineage_id"]]]
        require(len(positions) == len(set(positions)), "ambiguous route node order")
        node_techniques = {node["technique_id"] for node in lineage_nodes[lineage["lineage_id"]]}
        for placement in placements.values():
            if placement["technique_id"] in node_techniques and placement.get("stage") != "training" and placement.get("applicability") != "training_only":
                _owned(placement, "lineage technique placement")
                require(placement["cell_id"] in lineage_cells[lineage["lineage_id"]], "route omits a representative technique's actual inference cell")
    edge_keys = set()
    for edge in tables["ic_lineage_relations"]:
        require(edge["lineage_id"] in lineages and edge["from_node_id"] in nodes and edge["to_node_id"] in nodes,
                "relation has a dangling route/node endpoint")
        require(edge["from_node_id"] != edge["to_node_id"] and all(nodes[key]["lineage_id"] == edge["lineage_id"] for key in (edge["from_node_id"], edge["to_node_id"])),
                "self/cross-route lineage relation")
        require(edge["relation_kind"] in RELATION_KINDS, "relationship must be an explicit evidence or analyst category")
        require(edge["source_id"] in sources, "relation evidence source is missing")
        _primary_paper(sources[edge["source_id"]], "relation source")
        identity = (edge["lineage_id"], edge["from_node_id"], edge["to_node_id"], edge["relation_kind"])
        require(identity not in edge_keys, "duplicate semantic lineage relation")
        edge_keys.add(identity)

    selected_sources, screened_by_scan = set(), defaultdict(list)
    for row in screenings.values():
        require(row["scan_id"] in scans and row["source_id"] in sources, "screening has a missing scan/source")
        require(row["screening_status"] in SCREENING_KINDS, "unknown screening category")
        _primary_paper(sources[row["source_id"]], "screened paper")
        require(_audit_date(row["checked_at"], "screening check") >= _audit_date(scans[row["scan_id"]]["retrieved_at"], "scan retrieval"),
                "screening review predates retrieval")
        require(row["position"] >= 0, "negative screening position")
        screened_by_scan[row["scan_id"]].append(row)
        if row["screening_status"] == "in_scope" and scans[row["scan_id"]]["origin_kind"] == "arxiv_recent_first_page":
            selected_sources.add(row["source_id"])
    for scan in scans.values():
        require(scan["origin_kind"] in {"arxiv_recent_first_page", "imported_corpus_regression_sample"}, "unknown retrieval scope")
        if scan["origin_kind"] == "arxiv_recent_first_page":
            require(scan["channel_source_id"] in sources, "scan channel source is missing")
            _owned(sources[scan["channel_source_id"]], "scan channel", topic=False)
            _safe_source_url(sources[scan["channel_source_id"]]["canonical_url"], "scan channel URL")
            require(_date(scan["listing_date"], "listing date") <= _audit_date(scan["retrieved_at"], "retrieval date"), "listing date follows actual retrieval")
        else:
            require(scan["channel_source_id"] == "" and scan["listing_date"] == "", "imported samples must not invent a feed or listing date")
            _audit_date(scan["retrieved_at"], "imported sample review date")
        require(scan["scan_status"] in {"completed_bounded_screen", "partial", "incomplete", "pending", "failed"}, "unknown scan completion state")
        require(all(scan[field] >= 0 for field in COUNT_FIELDS) and scan["requested_limit"] > 0, "negative/empty scan count")
        require(scan["received_count"] <= scan["requested_limit"], "received more than the requested bounded page")
        require(scan["received_count"] == scan["title_candidate_count"] + scan["title_not_matched_count"], "title-hit/unmatched counts do not equal retrieved items")
        rows = screened_by_scan[scan["scan_id"]]
        require(len(rows) == scan["title_candidate_count"] and len({row["source_id"] for row in rows}) == len(rows),
                "candidate screening details are incomplete or duplicated")
        counts = Counter(row["screening_status"] for row in rows)
        for status, field in (("in_scope", "selected_count"), ("adjacent", "adjacent_count"), ("excluded", "excluded_count"), ("pending", "pending_count")):
            require(counts[status] == scan[field], "screening classifications differ from scan counts")
        require(sum(counts.values()) == scan["title_candidate_count"], "title-candidate classification total differs")
        zh, en = scan["boundary_zh"], scan["boundary_en"].lower()
        require("标题" in zh and "未" in zh and "摘要" in zh and any(word in zh for word in ("不能", "不代表", "未审核")),
                "unmatched titles must not be presented as full-content exclusions")
        require(re.search(r"non.?matching|unmatched", en) and re.search(r"not.{0,24}review|unreviewed", en),
                "English unmatched-title review boundary is missing")
        require(any(word in zh for word in ("非", "不表示", "不代表", "未取回")) and any(word in en for word in ("no complete", "not complete", "partial", "later pages")),
                "bounded retrieval cannot claim complete source/field coverage")

    # A newly screened submission becomes monthly evidence by its original
    # publication event, never by the listing or import/retrieval date.
    evidence = _canonical(fixture, "ic_evidence_items", "evidence_id")
    monthly_links = _canonical(fixture, "ic_monthly_evidence_cells", "link_id")
    scopes = _canonical(fixture, "ic_monthly_scopes", "scope_id")
    periods = _canonical(fixture, "ic_trend_periods", "period_id")
    fresh_scopes = set()
    for source_id in selected_sources:
        items = [item for item in evidence.values() if item["source_id"] == source_id and item["status"] == "primary_abstract_checked"]
        require(items, "in-scope screened source is missing monthly evidence")
        for item in items:
            _owned(item, "screened monthly event")
            links = [link for link in monthly_links.values() if link["evidence_id"] == item["evidence_id"]]
            require(links, "screened monthly event lacks canonical cell placement")
            require(item["date_kind"] in {"first_submission", "revision"}, "screened primary event needs submission/revision date semantics")
            event = _date(item["event_date"], "screened primary event")
            published = _date(item["publication_date"], "screened first publication")
            require(event >= published, "screened revision predates first publication")
            if item["date_kind"] == "first_submission":
                require(event == published and source_id not in historical_sources, "historical representative mislabeled as a new submission")
            for link in links:
                _owned(link, "screened monthly placement")
                require(link["scope_id"] in scopes and link["period_id"] in periods and link["cell_id"] in cells, "screened monthly placement has a dangling scope/period/cell")
                scope, period = scopes[link["scope_id"]], periods[link["period_id"]]
                _owned(scope, "screened monthly scope"); _owned(period, "screened month")
                require(scope["period_id"] == link["period_id"] and period["month"] == event.strftime("%Y-%m"), "screened event uses listing/import month instead of its event month")
                require(_date(scope["window_start"], "sample start") <= event <= _date(scope["window_end"], "sample end"), "screened event outside its sample window")
                fresh_scopes.add(scope["scope_id"])
    for link in monthly_links.values():
        if link["scope_id"] in fresh_scopes:
            require(evidence[link["evidence_id"]]["source_id"] in selected_sources, "historical/adjacent/excluded source contaminated the new screened sample")

    return {
        "lineage_snapshot": "pass", "lineage_revision": fixture["revision"],
        "lineage_row_counts": {name: len(rows) for name, rows in tables.items()},
        "historical_representative_sources": len(historical_sources),
        "screened_in_scope_sources": len(selected_sources),
        "screened_monthly_scopes": len(fresh_scopes),
        "historical_and_new_event_boundary": "pass",
        "title_unmatched_full_content_exclusions": False,
    }


def validate_lineage_snapshot(path, **kwargs):
    return validate_lineage_fixture(json.loads(Path(path).read_text(encoding="utf-8")), **kwargs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--site-config", type=Path)
    parser.add_argument("--expected-lineages", type=int, default=9)
    parser.add_argument("--expected-scans", type=int)
    parser.add_argument("--expected-historical-sources", type=int, default=23)
    args = parser.parse_args()
    try:
        result = validate_lineage_snapshot(args.snapshot, expected_lineages=args.expected_lineages,
                                          expected_scans=args.expected_scans,
                                          expected_historical_sources=args.expected_historical_sources)
        if args.site_config:
            result.update(validate_lineage_site(json.loads(args.site_config.read_text(encoding="utf-8"))))
    except (AssertionError, OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"lineage_snapshot": "fail", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))

