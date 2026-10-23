"""Verify a generated expert index against canonical content and reader revision."""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_expert_index import DEFAULT_OUTPUT, build, card_hash, make_index, require


def verify_payload(payload: dict, manifest: dict | None = None) -> dict:
    expected = make_index()
    require(payload.get("schema_version") == 1, "unsupported schema")
    require(payload.get("content_version") == expected["content_version"] and payload.get("revision") == expected["revision"],
            "index is stale or bound to a different content revision")
    if manifest is not None:
        require(all(manifest.get(key) == payload[key] for key in ("content_version", "revision")),
                "reader manifest and index revision disagree")
    cards = payload.get("cards")
    require(isinstance(cards, list), "missing cards")
    require(len({card.get("id") for card in cards}) == len(cards), "duplicate indexed card")
    for card in cards:
        require(card.get("hash") == card_hash(card), "card hash mismatch: " + str(card.get("id")))
    # Exact comparison checks canonical source identities/URLs, each card's own
    # locators and review depth, visible anchors, omissions and factual counts.
    require(payload == expected, "index differs from canonical content or reader coverage")
    return {"topics": len(payload["topics"]), "cards": len(cards),
            "omitted": payload["coverage"]["omitted_cards"], "revision": payload["revision"]}


def verify(path: Path, manifest_path: Path | None = None) -> dict:
    path = Path(path)
    require(path.is_file(), "index file missing: " + str(path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if manifest_path is None:
        manifest_path = path.with_name("manifest.json")
    require(Path(manifest_path).is_file(), "reader manifest file missing: " + str(manifest_path))
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    return verify_payload(payload, manifest)


def rejected(payload: dict, manifest: dict | None = None) -> None:
    try:
        verify_payload(payload, manifest)
    except ValueError:
        return
    raise AssertionError("Corrupt expert index unexpectedly passed")


def self_test() -> dict:
    with tempfile.TemporaryDirectory(prefix="ccn-expert-index-") as folder:
        output = Path(folder)
        payload = build(output)
        manifest = {key: payload[key] for key in ("content_version", "revision")}
        (output / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = verify(output / "expert-index.json")
        require(set(p.name for p in output.iterdir()) == {"expert-index.json", "manifest.json"}, "unexpected generated files")
        broken = deepcopy(payload)
        broken["cards"][0]["body_zh"] += " fabricated result"
        rejected(broken)
        broken = deepcopy(payload)
        card = broken["cards"][0]
        card["sources"][0]["url"] = "https://example.com/unrelated-paper"
        card["hash"] = card_hash(card)
        rejected(broken)
        broken = deepcopy(payload)
        card = next(c for c in broken["cards"] if c["review_depth"] == "abstract")
        card["review_depth"] = "sections"
        card["hash"] = card_hash(card)
        rejected(broken)
        broken = deepcopy(payload)
        card = broken["cards"][0]
        card["anchor"] = "unrendered-destination"
        card["hash"] = card_hash(card)
        rejected(broken)
        broken = deepcopy(payload)
        broken["coverage"]["indexed_cards"] += 1
        rejected(broken)
        rejected(payload, {**manifest, "revision": "0" * 40})
        # Stable canonical cards produce byte-identical disposable indexes.
        before = (output / "expert-index.json").read_bytes()
        build(output)
        require(before == (output / "expert-index.json").read_bytes(), "nondeterministic index")
        require(all(c["anchor"] == "research-card-" + c["id"] for c in payload["cards"]
                    if c["id"].startswith("parameters-precision__progress_")), "progress anchors are not exact")
        require(not any(c["id"].startswith("parameters-precision__lesson_") or
                        c["id"] == "parameters-precision__expert_summary" for c in payload["cards"]),
                "invisible weight cards leaked into index")
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_OUTPUT / "expert-index.json")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    result = self_test() if args.self_test else verify(args.path, args.manifest)
    print(f"PASS: {result['topics']} topics; {result['cards']} visible cards; {result['omitted']} explicit omissions; "
          f"canonical sources, provenance, hashes and revision {result['revision']} verified")


if __name__ == "__main__":
    main()
