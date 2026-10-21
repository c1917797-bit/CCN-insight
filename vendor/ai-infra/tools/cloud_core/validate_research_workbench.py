"""Read-only acceptance of the research workbench and an exact TableGit fixture.

The fixture is evidence for validation, never runtime authority. Eleven curation
tables contain scalar rows; public URL identity belongs to cloud_core_sources.
CLI: --root <deployment> --fixture <exact-native.json> [--negative-tests].
"""
from __future__ import annotations

import argparse
import copy
import importlib
import json
import math
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

from validate_monthly import _audit_date, _date, _safe_source_url
from validate_pyramid import PageDOM, _inside, _function, _compact, _scan_balanced, validate_collapsible_shell, validate_extended_reads


TABLE_NAMES = {
    "ic_findings", "ic_finding_evidence", "ic_finding_cells",
    "ic_finding_techniques", "ic_finding_keywords", "ic_source_categories",
    "ic_channels", "ic_channel_categories", "ic_channel_provenance",
    "ic_channel_checks", "ic_finding_scopes",
}
CATALOG_TABLES = {"ic_channels", "ic_source_categories", "ic_channel_categories", "ic_channel_provenance", "ic_channel_checks"}
KINDS = {"current_event", "foundational_review", "implementation_reference"}
FAMILIES = {"academic", "industry", "hotspot", "technical"}
VIEWS = {"home", "updates", "topics", "sources", "reports"}
SCALAR_TYPES = {"string", "text", "markdown", "integer", "number", "boolean"}
SCOPES = {
    "primary_abstract_and_submission_history",
    "primary_methods_and_selected_results",
    "official_documentation_notes_and_quantization_flow",
    "official_documentation_introduction_and_quantization_parameters",
    "official_documentation_install_requirements",
    "official_documentation_model_support_matrix_checked",
    "official_documentation_repository_readme",
    "official_author_repository_readme_checked",
}
SECRET_FIELD = re.compile(r"password|passwd|credential|secret|private_key|api_key|access_token", re.I)
SECRET_VALUE = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}|"
    r"(?i:(?:password|passwd|api[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?[^\s'\"]{8,})"
)
BODY_FIELDS = {"payload", "json_payload", "full_text", "fulltext", "article_body",
               "paper_body", "document_body", "content_html", "raw_html", "raw_response"}


class ResearchWorkbenchValidationError(AssertionError):
    """A snapshot or reader contract failed; missing evidence is not a pass."""


def require(condition, message):
    if not condition:
        raise ResearchWorkbenchValidationError(message)


def _definitions(definitions=None):
    result = definitions or importlib.import_module("research_workbench_schema").DEFINITIONS
    require(isinstance(result, dict) and set(result) == TABLE_NAMES,
            "research schema must define exactly the eleven scalar curation tables")
    return result


def _frames(fixture, name):
    require(name in fixture.get("tables", {}), f"missing required snapshot table: {name}")
    entry = fixture["tables"][name]
    if isinstance(entry, list):
        return entry, None
    require(isinstance(entry, dict) and isinstance(entry.get("rows"), list),
            f"{name}: invalid table envelope")
    if "revision" in entry:
        require(entry["revision"] == fixture["revision"], f"{name}: mixed snapshot revisions")
    return entry["rows"], entry.get("definition")


def _rows(fixture, name, expected=None):
    frames, actual = _frames(fixture, name)
    definition = actual or expected
    if expected:
        require(definition.get("key_field") == expected["key_field"], f"{name}: wrong key field")
        fields = definition.get("fields")
        require(isinstance(fields, dict), f"{name}: missing scalar field definition")
        require(all(isinstance(spec, dict) and spec.get("type") in SCALAR_TYPES
                    for spec in fields.values()), f"{name}: non-scalar schema")
        require(all(field in fields and fields[field].get("type") == spec["type"]
                    for field, spec in expected["fields"].items()), f"{name}: schema mismatch")
        require(set(fields) == set(expected["fields"]), f"{name}: unexpected parallel authority field")
        require(not any(SECRET_FIELD.search(field) or field.lower() in BODY_FIELDS
                        for field in fields), f"{name}: credential or full-text schema")
        require(not any(field.lower().endswith("url") for field in fields),
                f"{name}: URLs must join the canonical source table")
    rows, seen = [], set()
    for frame in frames:
        require(isinstance(frame, dict) and isinstance(frame.get("deleted", False), bool),
                f"{name}: invalid frame")
        if frame.get("deleted"):
            continue
        key, row, version = frame.get("key"), frame.get("row"), frame.get("row_version")
        require(isinstance(key, str) and key and key not in seen, f"{name}: duplicate/missing frame key")
        seen.add(key)
        require(isinstance(version, int) and not isinstance(version, bool) and version > 0,
                f"{name}: invalid row version")
        require(isinstance(row, dict), f"{name}: missing row")
        if expected:
            require(row.get(expected["key_field"]) == key, f"{name}: frame and row keys differ")
            require(row.get("business_id") == "cloud-core" and row.get("topic_id") == "cloud_core",
                    f"{name}: wrong business/topic")
            require(all(field in row and row[field] is not None for field in expected["required_fields"]),
                    f"{name}: required scalar missing")
            for field, value in row.items():
                require(field in definition["fields"], f"{name}: undeclared field {field}")
                require(not isinstance(value, (list, dict)), f"{name}.{field}: nested payload")
                if value is None:
                    continue
                kind = definition["fields"][field]["type"]
                valid = ((kind in {"string", "text", "markdown"} and isinstance(value, str)) or
                         (kind == "boolean" and isinstance(value, bool)) or
                         (kind == "integer" and isinstance(value, int) and not isinstance(value, bool)) or
                         (kind == "number" and isinstance(value, (int, float)) and not isinstance(value, bool)
                          and math.isfinite(value)))
                require(valid, f"{name}.{field}: incorrect scalar type")
                if isinstance(value, str):
                    require(not SECRET_VALUE.search(value), f"{name}.{field}: credential-like value")
                    require(len(value) <= 2500, f"{name}.{field}: exceeds minimal curated metadata scope")
                    require(not value.lstrip().startswith(("{", "[")), f"{name}.{field}: serialized payload")
        rows.append(row)
    if expected:
        limit = 2000 if name in CATALOG_TABLES else 100
        require(0 < len(rows) <= limit, f"{name}: empty or exceeds the bounded reader limit ({limit})")
    return rows


def _index(rows, key, name):
    result = {}
    for row in rows:
        value = row.get(key)
        require(isinstance(value, str) and value and value not in result, f"{name}: duplicate/missing {key}")
        result[value] = row
    return result


def _nonempty(row, fields, context):
    require(all(isinstance(row.get(field), str) and row[field].strip() for field in fields),
            context + ": required reading/evidence text is blank")


def _unique(rows, fields, context):
    values = [tuple(row[field] for field in fields) for row in rows]
    require(len(set(values)) == len(values), context + ": duplicate relation")


def validate_research_workbench_fixture(fixture, definitions=None):
    """Validate exact-native frames; optional native-format DEFINITIONS supports embedding."""
    require(isinstance(fixture, dict) and re.fullmatch(r"[0-9a-f]{40}", fixture.get("revision", "")),
            "missing exact native revision; candidate dates are not a revision")
    definitions = _definitions(definitions)
    tables = {name: _rows(fixture, name, definitions[name]) for name in sorted(TABLE_NAMES)}
    sources = _index(_rows(fixture, "cloud_core_sources"), "source_id", "canonical sources")
    source_urls = set()
    for source in sources.values():
        require(source.get("business_id") == "cloud-core", "canonical source belongs to another business")
        _safe_source_url(source.get("canonical_url"), "canonical source " + source["source_id"])
        require(source["canonical_url"] not in source_urls, "duplicate exact canonical URL identity")
        source_urls.add(source["canonical_url"])
    cells = _index(_rows(fixture, "ic_cells"), "cell_id", "cells")
    techniques = _index(_rows(fixture, "ic_techniques"), "technique_id", "techniques")
    events = _rows(fixture, "ic_evidence_items")
    monthly_scopes = _index(_rows(fixture, "ic_monthly_scopes"), "scope_id", "monthly scopes")
    monthly_links = _rows(fixture, "ic_monthly_evidence_cells")
    lineages = _rows(fixture, "ic_lineage_nodes")
    scans = _rows(fixture, "ic_source_scans")
    known_publications = defaultdict(set)
    for row in events:
        if row.get("publication_date"):
            known_publications[row["source_id"]].add(row["publication_date"])
    for row in lineages:
        known_publications[row["source_id"]].add(row["first_submitted_on"])
    findings = _index(tables["ic_findings"], "finding_id", "findings")
    evidence = defaultdict(list)
    _unique(tables["ic_finding_evidence"], ("finding_id", "source_id", "evidence_role"), "finding evidence")
    for link in tables["ic_finding_evidence"]:
        require(link["finding_id"] in findings, "finding evidence has an orphan finding")
        require(link["source_id"] in sources, "finding evidence has an orphan canonical source")
        require(link["evidence_status"] == "checked_primary_source", "finding evidence overstates verification")
        require(link["checked_scope"] in SCOPES, "finding evidence lacks an audited abstract/document check scope")
        require(link["local_measurement"] is False, "initial curation cannot claim local measurements")
        _nonempty(link, ("supported_claim_zh", "supported_claim_en", "evidence_locator", "observed_version"), "finding evidence")
        checked = _audit_date(link["checked_at"], "finding evidence checked_at")
        source = sources[link["source_id"]]
        if source.get("source_kind") == "paper":
            require(link["checked_scope"] in {"primary_abstract_and_submission_history", "primary_methods_and_selected_results"}, "paper checked scope is not an audited primary review")
            if link["checked_scope"] == "primary_methods_and_selected_results":
                require(re.search(r"\b(?:table|section|figure|fig\.?|appendix|equation|eq\.?)\s*[A-Z]?\d|§\s*\d", link["evidence_locator"], re.I), "selected primary results lack a section/table locator")
            require(source.get("verification_status") in {"primary_metadata_and_abstract_checked", "primary_metadata_mechanism_checked"},
                    "paper source is not primary-checked")
            require(re.fullmatch(r"https://arxiv.org/abs/\d{4}\.\d{4,5}", source["canonical_url"]),
                    "paper evidence is not an unversioned original abstract URL")
            require(re.fullmatch(r"v[1-9]\d*", link["observed_version"]), "paper evidence lacks an observed version")
            published = _date(link["publication_date"], "paper first publication")
            require(published <= checked, "paper publication follows its check")
            require(link["publication_date"] in known_publications[link["source_id"]], "paper date disagrees with independent existing evidence")
        else:
            author_repository = link["checked_scope"] == "official_author_repository_readme_checked"
            require(link["checked_scope"].startswith("official_documentation_") or author_repository, "implementation evidence lacks official-document check scope")
            expected_status = "official_author_repository_checked" if author_repository else "official_documentation_checked"
            require(source.get("verification_status") == expected_status, "author repository source not checked" if author_repository else "documentation source not checked")
            if author_repository:
                require(link["evidence_role"] in {"official_author_repository_reference", "author_implementation_reference"}, "author repository cannot supply a direct paper/result evidence role")
                require(link["publication_date"] == "" and link["local_measurement"] is False and link["observed_version"].strip(), "author README claims publication or local reproduction")
                require(re.search(r"readme|repository", link["evidence_locator"], re.I), "author repository lacks an independent README locator")
                require(not re.search(r"\d+(?:\.\d+)?\s*(?:%|×|times\s+(?:faster|speedup)|x\s+(?:faster|speedup))", link["supported_claim_en"], re.I), "author repository reference cannot prove a quantitative performance effect")
            if link["publication_date"]:
                require(link["publication_date"] in known_publications[link["source_id"]], "unverified document publication date")
        evidence[link["finding_id"]].append(link)
    _unique(tables["ic_findings"], ("position",), "finding order")
    for finding_id, row in findings.items():
        require(row["kind"] in KINDS, "unknown finding kind")
        _nonempty(row, [f"{field}_{lang}" for field in ("summary", "implication", "background", "innovation", "results", "title", "ascend_boundary") for lang in ("zh", "en")], finding_id)
        require(len(row["summary_zh"]) <= 70 and len(row["summary_en"].split()) <= 25,
                finding_id + ": summary is too long for quick reading")
        require(row["relevance_label"] == "analyst_inference" and row["next_suggestion_label"] == "analyst_suggestion",
                finding_id + ": analyst interpretation is not independently labeled")
        require(row["change_label"] == "source_facts" and row["mechanism_label"] == "source_facts" and
                row["ascend_boundary_label"] == "reviewer_scope_and_compatibility_boundary",
                finding_id + ": source facts and Ascend review boundary are conflated")
        checked = _audit_date(row["checked_at"], finding_id + " checked_at")
        links = evidence[finding_id]
        require(links, finding_id + ": unsupported finding")
        require(all(_audit_date(link["checked_at"], "link checked_at") <= checked for link in links),
                finding_id + ": evidence checked after finding review")
        if row["kind"] == "current_event":
            require(row["recent_event_eligible"] is True and row["date_kind"] in {"first_submission", "revision", "source_declared_date"},
                    finding_id + ": current event lacks a genuine dated event")
            changed = _date(row["change_date"], finding_id + " change_date")
            published = _date(row["publication_date"], finding_id + " publication_date")
            require(published <= changed <= checked, finding_id + ": impossible event chronology")
            matches = [item for item in events if item.get("source_id") in {link["source_id"] for link in links}
                       and item.get("date_kind") == row["date_kind"] and item.get("event_date") == row["change_date"]
                       and item.get("publication_date") == row["publication_date"]
                       and item.get("status") == "primary_abstract_checked"]
            require(matches, finding_id + ": recent date is unsupported by independent primary event evidence")
            require(row["claim_status"] == "primary_abstract_checked", finding_id + ": current claim scope overstated")
        else:
            require(row["recent_event_eligible"] is False and row["change_date"] == "",
                    finding_id + ": historical/reference review mislabeled as new")
            if row["publication_date"]:
                publication_links = ([link for link in links if sources[link["source_id"]].get("source_kind") == "paper"]
                                     if row["kind"] == "foundational_review" and row["claim_status"] == "primary_methods_and_selected_results_checked" else links)
                require(publication_links and all(row["publication_date"] in known_publications[link["source_id"]] for link in publication_links),
                        finding_id + ": fabricated composite publication date")
            if row["kind"] == "foundational_review":
                if row["claim_status"] == "primary_methods_and_selected_results_checked":
                    paper_links = [link for link in links if sources[link["source_id"]].get("source_kind") == "paper"]
                    auxiliary_links = [link for link in links if sources[link["source_id"]].get("source_kind") != "paper"]
                    require(paper_links and all(link["checked_scope"] == "primary_methods_and_selected_results" for link in paper_links), finding_id + ": detailed review lacks selected primary mechanisms/results checks")
                    require(all(link["checked_scope"] == "official_author_repository_readme_checked"
                                and link["evidence_role"] in {"official_author_repository_reference", "author_implementation_reference"}
                                for link in auxiliary_links), finding_id + ": auxiliary reference cannot replace primary quantitative paper evidence")
                else:
                    require(len({link["source_id"] for link in links}) >= 2, finding_id + ": comparison needs two distinct sources")
                    require(row["claim_status"] == "curated_comparison_with_explicit_inference", finding_id + ": comparison inference not labeled")
            else:
                require(row["claim_status"] == "official_documentation_checked_not_deployment_validated", finding_id + ": documentation mistaken for deployment validation")
    _validate_finding_scopes(tables["ic_finding_scopes"], findings, evidence,
                             monthly_scopes, events, monthly_links)
    for table_name, foreign_field, foreign in (("ic_finding_cells", "cell_id", cells), ("ic_finding_techniques", "technique_id", techniques)):
        _unique(tables[table_name], ("finding_id", foreign_field), table_name)
        for row in tables[table_name]:
            require(row["finding_id"] in findings and row[foreign_field] in foreign, table_name + ": orphan relationship")
    keyword_groups = defaultdict(list)
    for row in tables["ic_finding_keywords"]:
        require(row["finding_id"] in findings, "orphan finding keyword")
        _nonempty(row, ("keyword_zh", "keyword_en"), "finding keyword")
        require(not any(mark in row["keyword_zh"] + row["keyword_en"] for mark in (";", "；", "\n", "|")),
                "keyword row contains a packed list")
        keyword_groups[row["finding_id"]].append(row)
    for finding_id in findings:
        require(any(row["finding_id"] == finding_id for row in tables["ic_finding_cells"]), "finding has no taxonomy placement")
        words = keyword_groups[finding_id]
        require(words and sorted(row["position"] for row in words) == list(range(1, len(words) + 1)), "finding keyword order is missing/duplicated")
        _unique(words, ("keyword_zh",), "Chinese keywords"); _unique(words, ("keyword_en",), "English keywords")
    source_result = _validate_channels(tables, sources, scans)
    return {"research_workbench_snapshot": "pass", "research_workbench_revision": fixture["revision"],
            "research_workbench_row_counts": {name: len(rows) for name, rows in tables.items()},
            "current_findings": sum(row["kind"] == "current_event" for row in findings.values()),
            "historical_reviews_counted_as_new": False, "local_performance_measurements": 0, **source_result}


def _validate_channels(tables, sources, scans):
    categories = _index(tables["ic_source_categories"], "category_id", "source categories")
    channels = _index(tables["ic_channels"], "channel_id", "source channels")
    provenance = _index(tables["ic_channel_provenance"], "provenance_id", "channel provenance")
    roots = [row for row in categories.values() if not row["parent_category_id"]]
    require({row["family_id"] for row in roots} == FAMILIES and len(roots) == 4, "three source roots or technical fourth family were lost")
    require({row["family_id"] for row in roots if row["display_kind"] == "primary_group"} == FAMILIES - {"technical"},
            "reader groups must preserve academic/industry/hotspot roots")
    require(next(row for row in roots if row["family_id"] == "technical")["display_kind"] == "cross_tag",
            "technical family must remain a visible cross-category classification")
    for category_id, row in categories.items():
        require(row["family_id"] in FAMILIES and row["depth"] >= 0, "invalid source category family/depth")
        _nonempty(row, ("title_zh", "title_en", "original_heading_zh", "origin_note"), "source category")
        require(re.fullmatch(r"[0-9a-f]{64}", row["origin_sha256"]) and row["origin_line"] > 0, "source category lacks note identity/hash/line")
        seen, current = set(), row
        while current["parent_category_id"]:
            require(current["category_id"] not in seen, "source category cycle")
            seen.add(current["category_id"])
            parent = categories.get(current["parent_category_id"])
            require(parent and parent["family_id"] == current["family_id"] and parent["depth"] + 1 == current["depth"],
                    "source category parent is missing or inconsistent")
            current = parent
    for row in provenance.values():
        require(row["channel_id"] in channels, "orphan source provenance")
        if row["origin_kind"] == "vault_business_source_list":
            require(row["origin_note"] and row["origin_line"] > 0 and re.fullmatch(r"[0-9a-f]{64}", row["origin_sha256"]),
                    "restored source provenance lacks original note identity")
        elif row["origin_kind"] == "existing_information_channels":
            require(row["origin_record_id"] and re.fullmatch(r"[0-9a-f]{40}", row["origin_revision"]), "retained channel lacks native identity")
        else:
            require(False, "unknown source provenance origin")
    memberships = defaultdict(set)
    _unique(tables["ic_channel_categories"], ("channel_id", "category_id"), "source memberships")
    for row in tables["ic_channel_categories"]:
        require(row["channel_id"] in channels and row["category_id"] in categories and row["provenance_id"] in provenance,
                "orphan channel category/provenance")
        require(provenance[row["provenance_id"]]["channel_id"] == row["channel_id"], "membership provenance belongs to a different channel")
        memberships[row["channel_id"]].add(categories[row["category_id"]]["family_id"])
    require(any("technical" in families for families in memberships.values()), "technical original family has no membership")
    require(any(len(families) > 1 for families in memberships.values()), "many-to-many original source roles were flattened")
    checks = defaultdict(list)
    _unique(tables["ic_channel_checks"], ("channel_id", "checked_at"), "entrypoint checks")
    for row in tables["ic_channel_checks"]:
        require(row["channel_id"] in channels and row["source_id"] in sources, "orphan entrypoint check")
        require(channels[row["channel_id"]]["source_id"] == row["source_id"], "entrypoint check source differs from channel")
        _audit_date(row["checked_at"], "entrypoint check date")
        require(row["captured_research_items"] == 0 and row["performance_verified"] is False,
                "entrypoint identity check was counted as research retrieval or scientific validation")
        require((row["result"], row["verification_scope"]) in {
            ("checked", "identity_and_entrypoint"), ("pending", "retrieval_attempt_failed"),
            ("identity_only", "page_title_identity_only"), ("pending", "not_checked")}, "entrypoint check depth/status mismatch")
        if row["verification_scope"] == "not_checked":
            require(row["retrieval_method"] == "not_attempted", "unvisited source must be explicitly not attempted")
        else:
            require(isinstance(row.get("retrieval_method"), str) and row["retrieval_method"].strip()
                    and row["retrieval_method"] != "not_attempted",
                    "an unattempted source cannot claim a retrieval failure or successful identity check")
        checks[row["channel_id"]].append(row)
    scan_ids = {row["scan_id"] for row in scans}
    require(not scan_ids.intersection(row["check_id"] for row in tables["ic_channel_checks"]), "entrypoint checks reused as source scans")
    scanned_channels = 0
    for channel_id, row in channels.items():
        require(row["source_id"] in sources and row["ui_group"] in FAMILIES - {"technical"}, "channel has invalid source or reader group")
        require(memberships[channel_id] and checks[channel_id], "channel lacks original category or dated check")
        require(row["retention_policy"] == "public_url_plus_minimal_metadata", "source channel imports excessive content")
        actual = [scan for scan in scans if scan["channel_source_id"] == row["source_id"] and scan.get("received_count", 0) > 0]
        if row["scan_status"] == "scanned_partial":
            require(actual and row["verification_scope"] == "listing_metadata_and_selected_abstracts", "claimed channel scan has no actual bounded source scan")
            scanned_channels += 1
        else:
            require(row["scan_status"] == "not_scanned" and not actual, "channel scan status disagrees with actual retrieval")
            require(row["verification_scope"] in {"entrypoint_identity_only", "entrypoint_pending"}, "unscanned channel claims research verification")
    return {"restored_source_families": 4, "channels_with_actual_scans": scanned_channels,
            "registered_source_channels": len(channels),
            "source_checks_not_attempted": sum(row["verification_scope"] == "not_checked"
                                               for row in tables["ic_channel_checks"]),
            "entrypoint_checks_counted_as_research_items": 0}


def _validate_finding_scopes(links, findings, finding_evidence, scopes, event_rows, monthly_links):
    """A date match cannot substitute for membership in the actually retrieved sample."""
    events = _index(event_rows, "evidence_id", "primary events")
    _unique(links, ("finding_id", "scope_id", "evidence_id"), "finding sample scopes")
    bound = set()
    for link in links:
        finding_id, scope_id, evidence_id = link["finding_id"], link["scope_id"], link["evidence_id"]
        require(finding_id in findings and scope_id in scopes and evidence_id in events,
                "finding scope has an orphan finding/sample/evidence")
        finding, scope, event = findings[finding_id], scopes[scope_id], events[evidence_id]
        require(finding["kind"] == "current_event", "historical review was attached to a current source sample")
        require(scope.get("business_id") == "cloud-core" and scope.get("topic_id") == "cloud_core"
                and event.get("business_id") == "cloud-core" and event.get("topic_id") == "cloud_core",
                "finding scope joins another business/topic")
        require(event["source_id"] in {row["source_id"] for row in finding_evidence[finding_id]},
                "finding scope event belongs to an unrelated source")
        require(event["event_date"] == finding["change_date"] and event["date_kind"] == finding["date_kind"]
                and event["publication_date"] == finding["publication_date"]
                and event["status"] == "primary_abstract_checked",
                "finding scope event differs from the finding's checked event")
        require(any(row["scope_id"] == scope_id and row["evidence_id"] == evidence_id for row in monthly_links),
                "finding scope is not supported by an existing monthly sample placement")
        event_date = _date(event["event_date"], "scoped finding event")
        require(_date(scope["window_start"], "sample start") <= event_date <= _date(scope["window_end"], "sample end"),
                "finding event is outside the actual sample window")
        bound.add(finding_id)
    require({finding_id for finding_id, row in findings.items() if row["kind"] == "current_event"} == bound,
            "current finding has no explicit link to its actual source sample")


class _ReaderDOM(HTMLParser):
    def __init__(self):
        super().__init__()
        self.views, self.panels, self.keys = [], [], set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-view" in attrs:
            self.views.append((attrs["data-view"], attrs.get("href"), attrs.get("aria-current")))
        if "data-view-panel" in attrs:
            self.panels.append((attrs["data-view-panel"], attrs.get("id"), "hidden" in attrs))
        if "data-i18n-key" in attrs:
            self.keys.add(attrs["data-i18n-key"])


def validate_research_workbench_site(site, definitions=None):
    for name in _definitions(definitions):
        binding = site.get("tables", {}).get(name)
        require(isinstance(binding, dict) and binding.get("writable") is False, name + ": reader binding must be read-only")
        require(binding.get("path") == "data/tables/" + name, name + ": wrong native table path")
        limit = binding.get("max_rows")
        require(isinstance(limit, int) and not isinstance(limit, bool) and 0 < limit <= 100, name + ": unbounded reader binding")
        require({"topic_id", "business_id"} <= set(binding.get("filter_fields", [])), name + ": missing ownership filters")
    return {"research_workbench_bindings": "pass"}


def _validate_fact_first_reader(html, js):
    """The fact reader cannot expose analyst conclusions, including inside details."""
    page = PageDOM(html)
    ids = page.ids()
    for target, layer in (("monthly", "facts"), ("channels-panel", "facts"),
                          ("map", "analysis"), ("insight-overview", "conclusion")):
        require(target in ids and ids[target].attrs.get("data-reading-layer") == layer,
                target + ": objective facts, analysis and conclusions lack separate reading layers")
    for node in page.nodes:
        require(not (any(_inside(node, ids[target]) for target in ("view-sources", "view-updates"))
                     and node.attrs.get("data-reading-layer") == "conclusion"),
                "objective fact view contains an analyst conclusion layer")
    require(ids["judgment-basis"].attrs.get("data-section-collapsible") == "true",
            "child directory is not opted into default-closed grouping")
    compact = _compact(js)
    require("view:'sources'" in compact and "||'sources'" in _compact(_function(js, "viewFromHash"))
            and "?view:'sources'" in _compact(_function(js, "showView")),
            "no-hash/invalid navigation must start with source coverage")
    source_targets = re.search(r"\bsources:\[([^\]]*)\]", compact)
    require(source_targets is not None and all("'" + target + "'" in source_targets.group(1)
                                               for target in ("judgment-basis", "channels-panel")),
            "the collapsed research-basis parent must open the source-coverage view")
    card = _function(js, "findingCard")
    guard = re.search(r"if\s*\(\s*layer\s*===\s*(['\"])conclusion\1\s*\)\s*\{", card)
    require(guard is not None, "finding conclusions must be guarded by an explicit conclusion mode")
    opening = card.find("{", guard.start())
    conclusion = _scan_balanced(card, opening, "}")
    outside_conclusion = card[:guard.start()] + card[opening + len(conclusion):]
    fields = ("summary", "implication", "relevance", "next_suggestion")
    require(not any(re.search(r"textOf\(\s*row\s*,\s*['\"]" + field + r"['\"]", outside_conclusion)
                    for field in fields),
            "objective fact mode renders an analyst summary, implication or suggestion")
    require(all(re.search(r"textOf\(\s*row\s*,\s*['\"]" + field + r"['\"]", conclusion)
                for field in ("summary", "implication", "next_suggestion")),
            "conclusion mode lost its summary, business implication or compact suggestion")
    marked = _compact(card)
    positions = [marked.find(".dataset.readingLayer='" + layer + "'")
                 for layer in ("facts", "analysis", "conclusion")]
    require(all(position >= 0 for position in positions) and positions == sorted(positions),
            "finding reader must present facts and detailed analysis before conclusions")
    require("card.append(conclusion)" in _compact(conclusion),
            "conclusion must be appended after the finding's facts and analysis")
    render = _compact(_function(js, "renderFindings"))
    require("updates.append(findingCard(row,'facts'))" in render
            and "updates.append(findingCard(row))" not in render
            and "updates.append(findingCard(row,'conclusion'))" not in render,
            "objective fact view must call finding cards in fact mode")
    next_links = (("view-sources", "next_topics", "#view-topics"),
                  ("view-topics", "next_updates", "#view-updates"),
                  ("view-updates", "next_insights", "#view-home"),
                  ("view-home", "next_archive", "#view-reports"))
    for panel_id, key, destination in next_links:
        links = [node for node in page.nodes if node.tag == "a" and node.attrs.get("data-i18n-key") == key]
        require(len(links) == 1 and _inside(links[0], ids[panel_id])
                and links[0].attrs.get("href") == destination,
                panel_id + ": next-reading link must follow sources, map, facts, analysis/conclusions, archive")
    return {"research_workbench_reading_order": "sources_technology_map_related_facts_analysis_conclusions_archive",
            "research_workbench_next_reading_links": "pass",
            "research_workbench_fact_view_excludes_conclusions": "pass",
            "research_workbench_initial_view": "sources"}


def validate_research_workbench_ui(root, definitions=None):
    root = Path(root)
    base = root / "business_insight" / "cloud_core"
    html = (base / "index.html").read_text(encoding="utf-8-sig")
    dom = _ReaderDOM(); dom.feed(html)
    require(len(dom.views) == 5 and {row[0] for row in dom.views} == VIEWS, "reader navigation does not have five independent views")
    require(len(dom.panels) == 5 and {row[0] for row in dom.panels} == VIEWS, "reader panels do not match navigation")
    require([view for view, _, _ in dom.views] == ["sources", "topics", "updates", "home", "reports"],
            "reader tabs must progress from source coverage to technology map, related current facts, analysis/conclusions and archive")
    require([view for view, _, _ in dom.panels] == ["sources", "topics", "updates", "home", "reports"],
            "reader panels must follow the same progressive order as navigation")
    require(all(href == "#view-" + view for view, href, _ in dom.views), "reader view links are inconsistent")
    require(all(panel_id == "view-" + view and hidden == (view != "sources") for view, panel_id, hidden in dom.panels),
            "initial reader must expose source coverage before findings and analyst conclusions")
    require([view for view, _, current in dom.views if current == "page"] == ["sources"], "initial source view is ambiguous")
    js = (base / "compression.js").read_text(encoding="utf-8-sig")
    reading_result = _validate_fact_first_reader(html, js)
    extended_reads = validate_extended_reads(js)
    shell_result = validate_collapsible_shell((root / "assets" / "lri-shell.js").read_text(encoding="utf-8-sig"))
    for name in _definitions(definitions):
        require(re.search(r"['\"]" + re.escape(name.removeprefix("ic_")) + r"['\"]", js), name + ": native reader table not loaded")
    reads = re.findall(r"loadTablePage\s*\([^;]+", js)
    require(reads and all("expectedRevision" in read and re.search(r"limit\s*:\s*100\b", read) for read in reads),
            "TableGit page reads lack bounded limits or expected revision")
    require(not re.search(r"LRITableGit\.(?:create|update|delete|write|upsert|insert)", js), "workbench reader attempts native mutation")
    reading_keys = {"one_sentence", "keywords", "business_implication", "background", "innovation", "results", "read_in_detail"}
    for language in ("zh", "en"):
        pack = json.loads((base / "data" / f"focus-ui.{language}.json").read_text(encoding="utf-8-sig"))
        locale = pack.get("strings", {})
        require(all(key in locale and isinstance(locale[key], str) and locale[key].strip() for key in dom.keys | reading_keys),
                language + ": missing reader/six-block translation")
    require(all(re.search(r"textOf\(row,\s*['\"]" + field + r"['\"]", js) for field in ("summary", "implication", "background", "innovation", "results")),
            "six-block reader does not consume scalar bilingual content")
    require("finding_keywords" in js and "read_in_detail" in js, "keywords or detailed reading affordance absent")
    return {"research_workbench_reader_views": 5, "research_workbench_six_block_reader": "pass",
            "research_workbench_bounded_revision_reads": "pass", **reading_result, **shell_result, **extended_reads}


def validate_research_workbench_ui_negative_cases(root):
    """Reject a conclusion leaking into facts and a directory forced open on load."""
    root = Path(root)
    base = root / "business_insight" / "cloud_core"
    html = (base / "index.html").read_text(encoding="utf-8-sig")
    js = (base / "compression.js").read_text(encoding="utf-8-sig")
    shell = (root / "assets" / "lri-shell.js").read_text(encoding="utf-8-sig")
    _validate_fact_first_reader(html, js)
    validate_collapsible_shell(shell)
    leaked = re.sub(r'(<[^>]+id="view-updates"[^>]*>)',
                    r'\1<p data-reading-layer="conclusion">Analyst business implication</p>', html, count=1)
    require(leaked != html, "fact-view negative fixture could not identify the current panel")
    forced = re.sub(r"(openGroups\.has\(item\.id\)\s*\?\s*['\"]open['\"]\s*:\s*)['\"][ '\"]*['\"]",
                    r"\1'open'", shell, count=1)
    require(forced != shell, "directory negative fixture could not identify the closed default")
    checks = (("conclusion_in_fact_view", lambda: _validate_fact_first_reader(leaked, js),
               "objective fact view contains an analyst conclusion layer"),
              ("directory_forced_open", lambda: validate_collapsible_shell(forced),
               "shared directory must be default-closed"))
    for name, check, expected in checks:
        try:
            check()
        except AssertionError as error:
            require(expected in str(error), name + ": rejected for an unrelated reason")
        else:
            require(False, name + ": reader regression was accepted")
    return {"research_workbench_ui_negative_cases": [name for name, _, _ in checks],
            "research_workbench_ui_negative_cases_status": "pass"}


def validate_research_workbench_negative_cases(fixture, definitions=None):
    """Reject invented recency, false joins/membership and fictional source attempts."""
    validate_research_workbench_fixture(fixture, definitions)
    historical = copy.deepcopy(fixture)
    frames, _ = _frames(historical, "ic_findings")
    row = next(frame["row"] for frame in frames if not frame.get("deleted") and frame["row"]["kind"] == "foundational_review")
    row.update(kind="current_event", recent_event_eligible=True, date_kind="first_submission",
               change_date=row["checked_at"][:10], publication_date=row["checked_at"][:10], claim_status="primary_abstract_checked")
    orphan = copy.deepcopy(fixture)
    frames, _ = _frames(orphan, "ic_finding_evidence")
    next(frame["row"] for frame in frames if not frame.get("deleted"))["source_id"] = "source-nonexistent-negative-fixture"
    wrong_sample = copy.deepcopy(fixture)
    frames, _ = _frames(wrong_sample, "ic_finding_scopes")
    sample_link = next(frame["row"] for frame in frames if not frame.get("deleted"))
    scope_frames, _ = _frames(wrong_sample, "ic_monthly_scopes")
    sample_link["scope_id"] = next(frame["row"]["scope_id"] for frame in scope_frames
                                   if not frame.get("deleted") and frame["row"]["scope_id"] != sample_link["scope_id"])
    unattempted_failure = copy.deepcopy(fixture)
    frames, _ = _frames(unattempted_failure, "ic_channel_checks")
    next(frame["row"] for frame in frames if not frame.get("deleted")).update(
        result="pending", verification_scope="retrieval_attempt_failed", retrieval_method="not_attempted")
    unvisited_with_method = copy.deepcopy(fixture)
    frames, _ = _frames(unvisited_with_method, "ic_channel_checks")
    next(frame["row"] for frame in frames if not frame.get("deleted")).update(
        result="pending", verification_scope="not_checked", retrieval_method="web_open")
    false_comparison = copy.deepcopy(fixture)
    finding_frames, _ = _frames(false_comparison, "ic_findings")
    comparison = next(frame["row"] for frame in finding_frames if not frame.get("deleted") and frame["row"]["kind"] == "foundational_review")
    comparison["claim_status"] = "curated_comparison_with_explicit_inference"
    evidence_frames, _ = _frames(false_comparison, "ic_finding_evidence")
    group = [frame for frame in evidence_frames if not frame.get("deleted") and frame["row"]["finding_id"] == comparison["finding_id"]]
    chosen_source = group[0]["row"]["source_id"]
    for frame in group:
        if frame["row"]["source_id"] != chosen_source:
            frame["deleted"] = True
    missing_locator = copy.deepcopy(fixture)
    evidence_frames, _ = _frames(missing_locator, "ic_finding_evidence")
    located = next((frame["row"] for frame in evidence_frames if not frame.get("deleted") and frame["row"]["checked_scope"] == "primary_methods_and_selected_results"), None)
    if located is None:
        located = next(frame["row"] for frame in evidence_frames if not frame.get("deleted"))
    located["evidence_locator"] = ""
    for name, mutated, expected in (("historical_review_as_recent", historical, "independent primary event evidence"),
                                    ("orphan_finding_evidence", orphan, "orphan canonical source"),
                                    ("false_existing_sample_membership", wrong_sample, "existing monthly sample placement"),
                                    ("unattempted_source_as_failed_retrieval", unattempted_failure, "an unattempted source cannot claim"),
                                    ("unvisited_source_claims_retrieval_method", unvisited_with_method, "unvisited source must be explicitly not attempted"),
                                    ("single_source_false_comparison", false_comparison, "comparison needs two distinct sources"),
                                    ("selected_results_without_locator", missing_locator, "required reading/evidence text is blank")):
        try:
            validate_research_workbench_fixture(mutated, definitions)
        except AssertionError as error:
            require(expected in str(error), name + ": rejected for an unrelated reason")
        else:
            require(False, name + ": semantic regression was accepted")
    return {"research_workbench_negative_cases": ["historical_review_as_recent", "orphan_finding_evidence", "false_existing_sample_membership",
                                                "unattempted_source_as_failed_retrieval", "unvisited_source_claims_retrieval_method", "single_source_false_comparison", "selected_results_without_locator"],
            "research_workbench_negative_cases_status": "pass"}


def validate_research_workbench_snapshot(path, definitions=None):
    return validate_research_workbench_fixture(json.loads(Path(path).read_text(encoding="utf-8-sig")), definitions)


# Stable embedding APIs used by the deployment's existing compression validator.
validate_workbench_fixture = validate_research_workbench_fixture
validate_workbench_site = validate_research_workbench_site


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--negative-tests", action="store_true")
    args = parser.parse_args()
    try:
        fixture = json.loads(args.fixture.read_text(encoding="utf-8-sig"))
        result = validate_research_workbench_fixture(fixture)
        result.update(validate_research_workbench_site(json.loads((args.root / ".mcpgit" / "site.json").read_text(encoding="utf-8-sig"))))
        result.update(validate_research_workbench_ui(args.root))
        if args.negative_tests:
            result.update(validate_research_workbench_negative_cases(fixture))
            result.update(validate_research_workbench_ui_negative_cases(args.root))
    except (AssertionError, OSError, ValueError, TypeError, KeyError, ModuleNotFoundError) as error:
        print(json.dumps({"research_workbench": "fail", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))

