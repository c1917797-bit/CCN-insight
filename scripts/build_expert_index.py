"""Generate the reader's search index from canonical compression tables.

This is a disposable view, never a content maintenance source.  The index uses
the same content version and revision formula as build_original_reader.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import parse_qsl, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from compression_store import ROOT, clear_cache, content_version, rows


WEIGHT_TOPIC = "parameters-precision"
# renderWeightQuantizationTopic calls weightTopicCards for these individual
# cards. Landscape/progress rows and route evidence are rendered by their own
# loops. Do not index other weight cards just because they exist in the table.
WEIGHT_DIRECT = frozenset({
    "expert_brief", "principles_brief", "expert_updates",
    "refresh_data", "refresh_mtp", "refresh_ascend", "refresh_watch",
    "refresh_coverage", "industry_vllm", "msmodelslim_implementation",
    "industry_kernel", "industry_domain", "expert_evidence", "audit_coverage",
    "audit_awq", "audit_alignquant", "audit_compensation", "dossier_3",
    "dossier_4", "dossier_5", "dossier_6", "expert_questions",
    "hardware_nvidia", "hardware_ascend",
})
WEIGHT_PREFIXES = (WEIGHT_TOPIC + "__landscape_", WEIGHT_TOPIC + "__progress_")
DEFAULT_OUTPUT = ROOT / "dist/business_insight/cloud_core/local-content"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("Expert index: " + message)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def card_hash(card: dict) -> str:
    """Hash searchable content, links and provenance, excluding the hash itself."""
    return hashlib.sha256(canonical_json({k: v for k, v in card.items() if k != "hash"}).encode("utf-8")).hexdigest()


def unique_rows(table: str, key: str) -> dict[str, dict]:
    values = rows(table)
    result = {row[key]: row for row in values}
    require(len(result) == len(values), "duplicate " + table + " identity")
    return result


def source_url(value: str) -> str:
    require(isinstance(value, str), "missing canonical source URL")
    parsed = urlsplit(value)
    require(parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password,
            "unsafe canonical source URL")
    require(parsed.hostname not in {"localhost", "127.0.0.1", "::1"}, "local source URL")
    require(not any(re.search(r"token|password|secret|credential|api.?key|signature|bearer", key, re.I)
                    for key, _ in parse_qsl(parsed.query)), "credential parameter in source URL")
    return value


def omission_reason(card: dict, route_cards: set[str]) -> str | None:
    """Return why a card has no visible destination in the complete reader."""
    if card["compression_topic_id"] != WEIGHT_TOPIC:
        return None
    suffix = card["card_id"].removeprefix(WEIGHT_TOPIC + "__")
    if suffix in WEIGHT_DIRECT or card["card_id"].startswith(WEIGHT_PREFIXES) or card["card_id"] in route_cards:
        return None
    return "not_rendered_in_complete_weight_topic"


def anchor_for(card: dict) -> str:
    if card["card_id"].endswith("__expert_brief"):
        return "research-overview-brief"
    # Includes progress rows: renderWeightProgress assigns the same exact row ID.
    return "research-card-" + card["card_id"]


def paper_experiments(topics: dict, cards: dict, sources: dict,
                      by_card: dict[str, list[dict]], route_cards: set[str]) -> dict[str, list[dict]]:
    """Bind canonical experiments to existing, reachable cards without copying facts.

    An experiment may belong to several topics. Each projection must still cite
    that experiment's own source; another card's references cannot lend proof.
    Older source-less builds have no experimental supplement, rather than rows
    inferred from prose. Once the table exists, invalid records fail the build.
    """
    try:
        experiments = unique_rows("ic_paper_experiments", "experiment_id")
    except FileNotFoundError:
        return {}
    fields = ("config", "baseline", "dataset", "hardware", "runtime", "workload", "protocol", "locator")
    visible = {cid: card for cid, card in cards.items() if omission_reason(card, route_cards) is None}
    bound: dict[str, list[dict]] = {}
    for experiment in sorted(experiments.values(), key=lambda row: (row.get("position", 0), row["experiment_id"])):
        eid, sid, primary = experiment["experiment_id"], experiment.get("source_id"), experiment.get("card_id")
        require(isinstance(eid, str) and bool(eid.strip()), "missing experiment identity")
        require(experiment.get("business_id") == "cloud-core" and experiment.get("topic_id") == "cloud_core",
                "foreign paper experiment " + eid)
        require(sid in sources and primary in cards, "experiment has unknown source/card " + eid)
        require(any(ref["source_id"] == sid for ref in by_card[primary]), "experiment primary card cites another source " + eid)
        try:
            topic_ids = json.loads(experiment["topic_ids_json"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Expert index: invalid experiment topic list " + eid) from error
        require(isinstance(topic_ids, list) and bool(topic_ids) and all(isinstance(tid, str) and tid in topics for tid in topic_ids)
                and len(set(topic_ids)) == len(topic_ids), "unknown or repeated experiment topic " + eid)
        require(cards[primary]["compression_topic_id"] in topic_ids, "experiment omits its primary card topic " + eid)
        require(experiment.get("process_type") in {"PTQ", "QAT", "pruning", "distillation", "factorization", "other"}
                and experiment.get("experiment_kind") in {"quality", "system", "kernel", "memory"}, "unknown experiment type " + eid)
        require(type(experiment.get("year")) is int and type(experiment.get("position")) is int,
                "experiment year/order must be integers " + eid)
        require(all(isinstance(experiment.get(key), str) and experiment[key].strip()
                    for key in ("method", "model", "observed_version", "w_format", "a_format", "k_format", "v_format", "checked_at")),
                "missing experiment configuration/version " + eid)
        require(all(isinstance(experiment.get(field + "_" + language), str)
                    and experiment[field + "_" + language].strip()
                    for field in fields for language in ("zh", "en")), "incomplete localized experiment conditions " + eid)
        require(experiment.get("review_depth") == "section_review", "unqualified experiment evidence " + eid)
        source_url(experiment.get("source_url"))
        for family in ("quality", "performance", "memory"):
            try:
                metrics = json.loads(experiment[family + "_metrics_json"])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("Expert index: invalid experiment metrics " + eid) from error
            status = experiment.get(family + "_status")
            require(status in {"reported", "not_reported", "not_checked", "not_applicable"}
                    and isinstance(metrics, list) and bool(metrics) == (status == "reported"),
                    "experiment metric/status mismatch " + eid)
            for metric in metrics:
                require(isinstance(metric, dict) and metric.get("better") in {"lower", "higher"}
                        and all(isinstance(metric.get(key), str) and metric[key].strip()
                                for key in ("metric", "unit", "scope_zh", "scope_en"))
                        and all(type(metric.get(key)) in (int, float) and math.isfinite(metric[key])
                                for key in ("baseline", "result")), "invalid experiment metric contract " + eid)
        for tid in topic_ids:
            candidates = [card for cid, card in visible.items() if card["compression_topic_id"] == tid
                          and any(ref["source_id"] == sid for ref in by_card[cid])]
            require(bool(candidates), "experiment topic has no visible card citing its source " + eid + " / " + tid)
            preferred = next((card for card in candidates if card["card_id"] == primary), None)
            if preferred is None:
                preferred = min(candidates, key=lambda card: (card["card_kind"] != "case", card["position"], card["card_id"]))
            bound.setdefault(preferred["card_id"], []).append(experiment)
    return bound


def experiment_search_text(experiments: list[dict], language: str) -> str:
    """Project original values and metric scopes for retrieval, never infer wins."""
    lines = []
    for experiment in experiments:
        lines.append(" · ".join(str(experiment[key]) for key in (
            "method", "year", "process_type", "experiment_kind", "model", "observed_version")))
        lines.append(" · ".join(label + "=" + experiment[key] for label, key in (
            ("W", "w_format"), ("A", "a_format"), ("K", "k_format"), ("V", "v_format"))))
        lines.extend(experiment[field + "_" + language]
                     for field in ("config", "baseline", "dataset", "hardware", "runtime", "workload", "protocol", "locator"))
        for family in ("quality", "performance", "memory"):
            for metric in json.loads(experiment[family + "_metrics_json"]):
                lines.append(f"{metric['metric']} {str(metric['baseline'])} → {str(metric['result'])} {metric['unit']} · "
                             + metric["scope_" + language])
        lines.append(experiment["source_url"] + " · " + experiment["checked_at"])
    return "\n".join(dict.fromkeys(lines))


def make_index() -> dict:
    version = content_version()
    # Build hooks may be called repeatedly in one interpreter after table edits.
    clear_cache()
    topics = unique_rows("ic_compression_topics", "compression_topic_id")
    cards = unique_rows("ic_compression_topic_cards", "card_id")
    sources = unique_rows("cloud_core_sources", "source_id")
    routes = unique_rows("ic_compression_research_routes", "route_id")
    refs = unique_rows("ic_compression_topic_card_refs", "reference_id")
    by_card: dict[str, list[dict]] = {key: [] for key in cards}
    for ref in refs.values():
        require(ref["card_id"] in cards, "reference has unknown card " + ref["reference_id"])
        require(ref["source_id"] in sources, "reference has unknown source " + ref["reference_id"])
        require(ref["compression_topic_id"] == cards[ref["card_id"]]["compression_topic_id"],
                "reference belongs to another topic " + ref["reference_id"])
        require(ref["review_depth"] in {"section_review", "abstract_review"}, "unknown review depth")
        require(all(ref.get(key) for key in ("locator_zh", "locator_en", "checked_at")),
                "reference lacks provenance " + ref["reference_id"])
        by_card[ref["card_id"]].append(ref)
    route_cards: set[str] = set()
    for route in routes.values():
        require(route["supporting_card_id"] in cards, "route has unknown supporting card")
        require(cards[route["supporting_card_id"]]["compression_topic_id"] == route["compression_topic_id"],
                "route supporting card belongs to another topic")
        if route["compression_topic_id"] == WEIGHT_TOPIC:
            route_cards.add(route["supporting_card_id"])
    experiments_by_card = paper_experiments(topics, cards, sources, by_card, route_cards)
    indexed: list[dict] = []
    omitted: list[dict] = []
    for card in sorted(cards.values(), key=lambda c: (c["compression_topic_id"], c["position"], c["card_id"])):
        cid, tid = card["card_id"], card["compression_topic_id"]
        require(tid in topics and cid.startswith(tid + "__"), "unknown card topic or unstable identity " + cid)
        require(bool(by_card[cid]), "uncited card " + cid)
        require(all(isinstance(card.get(key), str) and card[key].strip()
                    for key in ("title_zh", "title_en", "body_zh", "body_en", "reviewed_at")),
                "missing searchable card fields " + cid)
        reason = omission_reason(card, route_cards)
        if reason:
            omitted.append({"id": cid, "reason": reason})
            continue
        linked = []
        for ref in sorted(by_card[cid], key=lambda r: (r["source_id"], r["reference_id"])):
            source = sources[ref["source_id"]]
            require(source.get("business_id") == "cloud-core" and source.get("title"), "invalid canonical source identity")
            linked.append({
                "id": source["source_id"], "title": source["title"], "url": source_url(source["canonical_url"]),
                "locator_zh": ref["locator_zh"], "locator_en": ref["locator_en"],
                "depth": ref["review_depth"], "checked_at": ref["checked_at"],
            })
        item = {
            "id": cid, "topic": tid,
            **{key: card[key] for key in ("title_zh", "title_en", "body_zh", "body_en")},
            "kind": card["card_kind"], "claim_kind": card["claim_kind"], "reviewed_at": card["reviewed_at"],
            "review_depth": "sections" if any(r["review_depth"] == "section_review" for r in by_card[cid]) else "abstract",
            "sources": linked, "anchor": anchor_for(card),
        }
        experiments = experiments_by_card.get(cid)
        if experiments:
            item.update({
                "search_text_zh": experiment_search_text(experiments, "zh"),
                "search_text_en": experiment_search_text(experiments, "en"),
                "experiment_ids": [experiment["experiment_id"] for experiment in experiments],
                "experiment_hash": hashlib.sha256(canonical_json(experiments).encode("utf-8")).hexdigest(),
            })
        item["hash"] = card_hash(item)
        indexed.append(item)
    require(content_version() == version, "canonical content changed during index generation; retry")
    return {
        "schema_version": 1, "content_version": version,
        "revision": hashlib.sha256(version.encode("utf-8")).hexdigest()[:40],
        "topics": [{"id": topic["compression_topic_id"], "title_zh": topic["title_zh"], "title_en": topic["title_en"],
                    "target": topic["target_term_id"], "method": topic["method_term_id"]}
                   for topic in sorted(topics.values(), key=lambda t: (t.get("position", 0), t["compression_topic_id"]))],
        "cards": indexed,
        "coverage": {"canonical_cards": len(cards), "indexed_cards": len(indexed), "omitted_cards": len(omitted),
                     "omitted": omitted, "basis": "Visible cards in the complete topic reader; source checks retain their recorded depth."},
    }


def build(output_dir: Path) -> dict:
    payload = make_index()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "expert-index.json").write_text(canonical_json(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build(args.output_dir)
    print(f"Expert index generated: {len(payload['topics'])} topics; {len(payload['cards'])} visible cards; "
          f"{payload['coverage']['omitted_cards']} unrendered cards omitted; revision {payload['revision']}")


if __name__ == "__main__":
    main()
