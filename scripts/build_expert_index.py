"""Generate the reader's search index from canonical compression tables.

This is a disposable view, never a content maintenance source.  The index uses
the same content version and revision formula as build_original_reader.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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
