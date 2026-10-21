"""Focused static regression checks for the compression page's reading order.

Reads the four edited UI files and an exact pre-edit UI baseline. No repository,
TableGit, schema, source, or page mutation is performed. These checks supplement
the native compression/monthly validators and browser interaction verification.
They do not treat a local preview as hosted production verification.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit


PRIMARY_ORDER = ("channels-panel", "map", "monthly", "insight-overview", "reports")
FUNNEL_LINKS = (
    ("funnel_sources", "#channels-panel"),
    ("funnel_relevance", "#map"),
    ("funnel_technology", "#monthly"),
    ("funnel_value", "#ascend"),
    ("funnel_report", "#insight-overview"),
)
EPOCHS = ("epoch", "periodEpoch", "scopeEpoch", "evidenceEpoch", "legacyEpoch", "detailEpoch", "listEpoch")
PROTECTED_FUNCTIONS = ("assertBusiness", "page", "small", "validateReviews", "scopeRows", "reviewRows")
READ_FUNCTIONS = ("loadEvidence", "loadScope", "loadPeriod", "loadLegacy", "loadDocuments", "openDocument")
DETAIL_CONTENT_IDS = ("task-cards", "flywheel-path", "flywheel-rules", "benchmark-contract")
VOID_ELEMENTS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent


class PageDOM(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self.stack = [self.root]
        self.nodes = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        node.parent.children.append(node)
        self.nodes.append(node)
        if tag not in VOID_ELEMENTS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack[-1].tag == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def ids(self):
        values = [node.attrs["id"] for node in self.nodes if "id" in node.attrs]
        require(len(values) == len(set(values)), "duplicate HTML IDs would break navigation/request targets")
        return {node.attrs["id"]: node for node in self.nodes if "id" in node.attrs}


def _inside(node, ancestor):
    return node is ancestor or ancestor in node.ancestors()


def _closed_details(node):
    return [ancestor for ancestor in node.ancestors() if ancestor.tag == "details" and "open" not in ancestor.attrs]


def _visible_text(node):
    """Count text actually exposed before expanding default-closed details."""
    if node.tag in {"script", "style"} or "hidden" in node.attrs:
        return ""
    children = node.children
    if node.tag == "details" and "open" not in node.attrs:
        children = [child for child in children if isinstance(child, Node) and child.tag == "summary"]
    return " ".join(child if isinstance(child, str) else _visible_text(child) for child in children)


def _scan_balanced(source, opening, close):
    """Find a balanced JS brace/parenthesis span, ignoring strings/comments."""
    opener = source[opening]
    depth, index = 1, opening + 1
    while index < len(source):
        char = source[index]
        if char in "'\"`":
            quote = char
            index += 1
            while index < len(source):
                if source[index] == "\\":
                    index += 2
                elif source[index] == quote:
                    index += 1
                    break
                else:
                    index += 1
            continue
        if source.startswith("//", index):
            newline = source.find("\n", index + 2)
            index = len(source) if newline < 0 else newline + 1
            continue
        if source.startswith("/*", index):
            ending = source.find("*/", index + 2)
            require(ending >= 0, "unterminated JS comment")
            index = ending + 2
            continue
        if char == opener:
            depth += 1
        elif char == close:
            depth -= 1
            if depth == 0:
                return source[opening:index + 1]
        index += 1
    raise AssertionError("cannot identify balanced JavaScript contract")


def _function(js, name):
    match = re.search(r"\bfunction\s+" + re.escape(name) + r"\s*\(", js)
    require(match is not None, "missing existing contract function: " + name)
    parameter_open = match.end() - 1
    parameters = _scan_balanced(js, parameter_open, ")")
    opening = js.find("{", parameter_open + len(parameters))
    require(opening >= 0, "missing function body: " + name)
    return _scan_balanced(js, opening, "}")


def _compact(value):
    # Protected data functions have no translated business/UI prose. Preserve
    # string content; formatting whitespace outside quotes is irrelevant.
    tokens = re.findall(r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`|[^\s]", value)
    return "".join(tokens)


def _read_calls(function):
    calls = []
    for match in re.finditer(r"\b(?:LRITableGit\.(?:loadRowsByKeys|loadTablePage|loadTopicWorkbench)|page|scopeRows|reviewRows)\s*\(", function):
        opening = function.find("(", match.start())
        calls.append(_compact(function[match.start():opening] + _scan_balanced(function, opening, ")")))
    return Counter(calls)


def validate_collapsible_shell(shell):
    """Check the opt-in directory default without forbidding restored open state."""
    require(re.search(r"function\s+renderSectionLinks\s*\(\s*items\s*,\s*openGroups\s*=\s*new\s+Set\s*\(\s*\)", shell),
            "shared directory must default to an empty set of expanded groups")
    renderer = _compact(_function(shell, "renderSectionLinks"))
    require("item.collapsible" in renderer and "data-shell-section-group=" in renderer
            and "<details" in renderer and "<summary" in renderer,
            "shared directory must render opt-in parents as native expandable groups")
    require(re.search(r"openGroups\.has\(item\.id\)\s*\?\s*(['\"])open\1\s*:\s*(['\"])\2", renderer),
            "shared directory must be default-closed; only previously expanded groups may reopen")
    templates = re.findall(r"<details\b[^>]*>", renderer)
    require(templates and all("open" not in node.attrs
                             for template in templates
                             for node in PageDOM(re.sub(r"\$\{[^}]*\}", "", template)).nodes
                             if node.tag == "details"),
            "shared directory must be default-closed; unconditional open markup was introduced")
    require("[data-shell-section-group][open]" in shell,
            "locale refresh must retain the reader's existing directory expansion state")
    return {"shared_directory_default": "closed", "shared_directory_opt_in": "pass"}


def validate_extended_reads(js):
    """Protect the two bounded pagination paths added to the existing reader."""
    start = _compact(_function(js, "start"))
    catalog_names = re.search(r"catalogNames=newSet\(\[([^\]]*)\]\)", start)
    expected_catalogs = {"channels", "source_categories", "channel_categories", "channel_provenance", "channel_checks"}
    require(catalog_names is not None and set(re.findall(r"'([^']+)'", catalog_names.group(1))) == expected_catalogs,
            "only the five source catalogs may use the larger bounded reader")
    require("names.map(name=>catalogNames.has(name)?loadCatalog(name,snapshot.revision):small(name,snapshot.revision))" in start
            and "validateEnrichment(collected)" in start and "validateResearch(collected)" in start,
            "catalog dispatch must retain bounded small reads and fail-closed relationships for other collections")
    catalog = _compact(_function(js, "loadCatalog"))
    catalog_keys = {"channels": "channel_id", "source_categories": "category_id",
                    "channel_categories": "membership_id", "channel_provenance": "provenance_id",
                    "channel_checks": "check_id"}
    require(all(name + ":'" + key + "'" in catalog for name, key in catalog_keys.items()),
            "each paginated source catalog must deduplicate its declared canonical identity field")
    require("page(name,'topic_id','cloud_core',revision,{offset,limit:100})" in catalog
            and "request!==state.epoch" in catalog and "validateEvidenceRevision(result,revision)" in catalog,
            "catalog pages must remain topic-owned, revision-pinned and stale-response protected")
    require(all(token in catalog for token in (
        "must(Boolean(key)", "Number.isSafeInteger(meta.total)", "meta.total<=2000", "result.records.length<=100",
        "total===meta.total", "meta.offset===offset", "!seen.has(row[key])", "records.length<=total",
        "result.records.length>0||total===0", "meta.truncated===(records.length<total)", "records.length===total",
        "Number.isSafeInteger(meta.nextOffset)", "meta.nextOffset===offset+result.records.length",
        "meta.nextOffset>offset", "meta.nextOffset<total")),
        "catalog pagination must enforce identity, stable totals, progress and its explicit 2000-record ceiling")
    research = _compact(_function(js, "validateResearch"))
    require("channels.has(row.channel_id)" in research and "categories.has(row.category_id)" in research
            and "proofs.get(row.provenance_id)?.channel_id===row.channel_id" in research
            and "channels.get(row.channel_id)?.source_id===row.source_id" in research,
            "catalog pagination cannot bypass channel/category/provenance/check foreign-key validation")
    related = _compact(_function(js, "loadRelatedEvidence"))
    require("page('monthly_evidence_cells','scope_id',scope,revision,{offset:cursor,limit:100})" in related
            and all(token in related for token in (
                "request===state.evidenceEpoch", "revision===state.revision", "scope===state.scope",
                "period===state.period", "object===state.object", "!state.cell&&state.scopeReady",
                "if(!active())return", "validateEvidenceRevision(result,revision)")),
            "scope-wide related evidence must retain scope/period/object/cell/revision/request boundaries")
    require(all(token in related for token in (
        "Number.isSafeInteger(meta.total)", "meta.total<=2000", "result.records.length<=100",
        "meta.total===total", "meta.offset===cursor", "validateEvidenceLink(link,scope,period)",
        "!seen.has(link.link_id)", "links.length<=total", "result.records.length>0||total===0",
        "meta.truncated===(links.length<total)", "links.length===total", "Number.isSafeInteger(meta.nextOffset)",
        "meta.nextOffset===cursor+result.records.length", "meta.nextOffset>cursor", "meta.nextOffset<total")),
        "related evidence must validate every placement and complete the bounded stable-total scan")
    require("state.relatedCache?.revision===revision" in related and "state.relatedCache.scope===scope" in related
            and "state.relatedCache.period===period" in related and "state.relatedCache=null" in _compact(_function(js, "clear")),
            "related-evidence cache must be pinned to the snapshot and actual sample scope")
    require("filter(event=>!object||event.placements.some(link=>state.data.cells.find(cell=>cell.cell_id===link.cell_id).object_id===object))" in related
            and "grouped.has(link.evidence_id)" in related and "grouped.get(link.evidence_id).placements.push(link)" in related
            and "events.slice(offset,offset+20)" in related and "limit:20" in related,
            "related evidence must filter canonical map objects and deduplicate events across cells before 20-event display")
    require(all(token in related for token in (
        "loadRowsByKeys('ic_evidence_items',ids,revision)", "assertBusiness(items.records)",
        "items.records.length===ids.length", "ids.includes(row.evidence_id)",
        "loadRowsByKeys('cloud_core_sources',sourceIds,revision", "sources.records.length===sourceIds.length",
        "sourceIds.includes(row.source_id)", "row.business_id==='cloud-core'", "safeUrl(source.canonical_url)",
        "if(fatal(error))fail(error)", "state.evidenceError=true")),
        "related evidence must fail closed on missing/cross-business/cross-revision item and source joins")
    placement = _compact(_function(js, "validateEvidenceLink"))
    require(all(token in placement for token in (
        "row.scope_id===scope", "row.period_id===period", "state.data.cells.some(cell=>cell.cell_id===row.cell_id)",
        "row.scope_cell_key===scope+'__'+row.cell_id", "!['training','training_only'].includes(row.stage)")),
        "scope evidence placement must match actual period, canonical cell and inference boundary")
    require("if(!state.cell)returnloadRelatedEvidence(offset)" in _compact(_function(js, "loadEvidence"))
            and "awaitloadEvidence(0)" in _compact(_function(js, "loadScope")),
            "the default sample reader must dispatch through the related-event path while preserving selected-cell reads")
    for target in ("object-filter", "reset-map"):
        match = re.search(r"\$\('" + re.escape(target) + r"'\)\.addEventListener\([^\n]*?=>\s*\{", js)
        require(match is not None, target + ": reader refresh handler is missing")
        handler = _compact(_scan_balanced(js, js.find("{", match.start()), "}"))
        require("state.cell=''" in handler and "resetEvidence()" in handler and "loadEvidence(0)" in handler,
                target + ": map selection changes must invalidate stale evidence and reload the scoped event view")
    default = _compact(_function(js, "chooseDefaultPeriod"))
    require("b.month.localeCompare(a.month)" in default and "template|uncollected" in default and "ongoing" not in default
            and "scopeRows(period.period_id,revision)" in default and "reviewRows(scope.scope_id,period.period_id,revision)" in default
            and "reviews.some(row=>row.sample_count>0)" in default and "request!==state.epoch" in default
            and "return{period:'',scope:''}" in default,
            "default period must choose the latest real sampled scope, including ongoing months, or leave the selection empty")
    return {"source_catalog_bounded_pagination": "pass", "scope_related_event_pagination": "pass",
            "related_event_display_limit": 20, "catalog_and_scope_record_limit": 2000,
            "default_period_requires_real_sample": "pass"}


def _public_url(url, context):
    parsed = urlsplit(url)
    require(parsed.scheme in {"http", "https"} and parsed.hostname and not parsed.username and not parsed.password,
            context + ": external source must be a public web URL without credentials")
    require(parsed.hostname not in {"localhost", "127.0.0.1", "::1"}, context + ": source cannot target a local host")
    for value in (parsed.query, parsed.fragment):
        for key, unused in parse_qsl(unquote(value), keep_blank_values=True):
            key = re.sub(r"[^a-z0-9]", "", key.lower())
            require(not any(term in key for term in ("token", "secret", "password", "credential", "apikey", "signature", "bearer")),
                    context + ": authentication/secret parameter in source URL")
            require(not key.startswith("auth") or key.startswith("author"), context + ": authentication parameter in source URL")


def validate_pyramid(page_root, baseline_page=None, max_validation_chars=360):
    page_root = Path(page_root)
    baseline_page = Path(baseline_page) if baseline_page is not None else None
    paths = ("index.html", "compression.js", "data/focus-ui.zh.json", "data/focus-ui.en.json")
    for root in (page_root,) + ((baseline_page,) if baseline_page is not None else ()):
        for path in paths:
            require((root / path).is_file(), "missing actual UI file: " + str(root / path))
    html = (page_root / "index.html").read_text(encoding="utf-8")
    js = (page_root / "compression.js").read_text(encoding="utf-8")
    shell = (page_root.parents[1] / "assets" / "lri-shell.js").read_text(encoding="utf-8")
    shell_result = validate_collapsible_shell(shell)
    original_html = (baseline_page / "index.html").read_text(encoding="utf-8") if baseline_page else None
    original_js = (baseline_page / "compression.js").read_text(encoding="utf-8") if baseline_page else None
    dom = PageDOM(html)
    ids = dom.ids()
    original_dom = PageDOM(original_html) if original_html is not None else None
    original_ids = original_dom.ids() if original_dom is not None else None
    if original_ids is not None:
        require(set(original_ids) <= set(ids), "existing DOM targets/anchors were removed: " + ", ".join(sorted(set(original_ids) - set(ids))))
    for name in PRIMARY_ORDER:
        require(name in ids and ids[name].tag == "section", "missing primary section: " + name)
        groups = [node.attrs.get("id") for node in ids[name].ancestors() if node.tag == "section"]
        expected_groups = ["judgment-basis"] if name in {"monthly", "map", "channels-panel"} else []
        require(groups == expected_groups, name + ": reading task has the wrong conclusion/evidence/accumulation parent")
    require([node.attrs.get("id") for node in dom.nodes if node.tag == "section" and node.attrs.get("id") in PRIMARY_ORDER] == list(PRIMARY_ORDER),
            "reading order must be source coverage -> object/method technology map -> related current facts -> analysis and conclusions -> archive")
    outline = (("judgment-basis", "01", "2"), ("channels-panel", "1.1", "3"),
               ("map", "1.2", "3"), ("monthly", "1.3", "3"),
               ("insight-overview", "02", "2"), ("reports", "03", "2"))
    require([node.attrs.get("id") for node in dom.nodes if node.tag == "section" and node.attrs.get("id")] == [item[0] for item in outline],
            "left outline must group facts/analysis before conclusions and accumulated insight")
    for target, number, level in outline:
        require(ids[target].attrs.get("data-section-number") == number
                and ids[target].attrs.get("data-section-level", "2") == level,
                target + ": explicit outline hierarchy/number is missing")
    require(ids["judgment-basis"].attrs.get("data-section-collapsible") == "true",
            "judgment-basis: its child directory must opt into default-closed shared-shell grouping")
    for target in ("knowledge", "ascend", "evidence", "validation"):
        require(ids[target].tag == "div", target + ": supporting material must not become another top-level outline task")
    funnel = [(node.attrs.get("data-i18n-key"), node.attrs.get("href")) for node in dom.nodes
              if node.tag == "a" and node.attrs.get("data-i18n-key") in dict(FUNNEL_LINKS)]
    require([key for key, unused in funnel] == [key for key, unused in FUNNEL_LINKS],
            "the five information-to-report stages need ordered, navigable anchors")
    require(all(isinstance(href, str) and href.startswith("#") and href[1:] in ids for unused, href in funnel),
            "funnel link points to a missing reading layer")
    for (key, href), (unused, expected) in zip(funnel, FUNNEL_LINKS):
        require(_inside(ids[href[1:]], ids[expected[1:]]), key + ": funnel destination belongs to the wrong reading layer")
    for target in DETAIL_CONTENT_IDS:
        require(target in ids and _inside(ids[target], ids["validation"]), target + ": detailed validation material escaped its suggestion layer")
        require(_closed_details(ids[target]), target + ": detailed task/flywheel/benchmark content must start collapsed")
    for target in ("reading-controls", "overview-context"):
        require(ids[target].tag == "details" and "open" not in ids[target].attrs,
                target + ": filters and collection provenance must start collapsed")
    require(ids["classification-panel"].tag == "div"
            and "hidden" not in ids["classification-panel"].attrs
            and _inside(ids["classification-panel"], ids["map"])
            and not _closed_details(ids["classification-panel"]),
            "object/method technology map must be the visible primary structure, not a collapsed appendix")
    for target in ("compact-map", "object-map"):
        require(_inside(ids[target], ids["classification-panel"])
                and "hidden" not in ids[target].attrs and not _closed_details(ids[target]),
                target + ": object/method map must be visible within the primary classification structure")
    validation_text = re.sub(r"\s+", " ", _visible_text(ids["validation"])).strip()
    require(len(validation_text) <= max_validation_chars, "validation's initially visible text is too long for brief suggestions")
    require(not any(node.tag in {"table", "textarea", "form"} and _inside(node, ids["validation"]) and not _closed_details(node) for node in dom.nodes),
            "validation must not expose an experiment workflow or full table by default")
    for target in ("source-panel", "document-detail"):
        require(_inside(ids[target], ids["view-reports"]), target + ": original material belongs in the report archive")
    for target in ("evidence-cards", "evidence-prev", "evidence-next", "evidence-retry"):
        require(_inside(ids[target], ids["monthly"]), target + ": monthly findings/evidence must live in the monthly layer")
    require(_inside(ids["cell-review"], ids["insight-overview"])
            and ids["cell-review"].attrs.get("data-reading-layer") == "analysis",
            "monthly research highlight belongs in analysis/conclusions, outside the objective fact reader")
    require(_closed_details(ids["monthly-rows"]), "legacy global statistics must remain a collapsed appendix")

    styles = [node.attrs.get("href", "").split("?")[0] for node in dom.nodes if node.tag == "link" and node.attrs.get("rel") == "stylesheet"]
    require(len(styles) == 1 and styles[0].endswith("insight-executive.css"), "new/private stylesheets are outside this UI rearrangement")
    if original_dom is not None:
        original_styles = [node.attrs.get("href", "").split("?")[0] for node in original_dom.nodes if node.tag == "link" and node.attrs.get("rel") == "stylesheet"]
        require(styles == original_styles, "stylesheet changed in a UI-only rearrangement")
    require(not any(node.tag == "style" or "style" in node.attrs for node in dom.nodes), "inline CSS is not allowed")
    require("innerHTML" not in js and "insertAdjacentHTML" not in js and "contenteditable" not in html, "source and evidence must render as inert text")
    require("lri-shell.js" in html and "lri-page-translation\" content=\"ui" in html, "shared shell/UI-only translation must remain")
    require(set(re.findall(r"\$\('([^']+)'\)", js)) <= set(ids), "JS refers to a missing DOM target")
    require(not re.search(r"[\"'](?:file|obsidian|javascript|data):", html + js, re.I), "local/executable source schemes were introduced")
    for node in dom.nodes:
        href = node.attrs.get("href", "")
        if href.startswith(("http:", "https:")):
            _public_url(href, "HTML link")
    for url in re.findall(r"https?://[^\s\"'<>`]+", js):
        _public_url(url, "JS link")
    require(not re.search(r"(?:C:[/\\\\]Users[/\\\\]|\b2[0-9]\d{2}\.\d{4,5}(?:v\d+)?\b|https?://(?:www\.)?arxiv\.org/abs/)", js),
            "paper identities/private paths must come from TableGit, not static JS")
    require(not any(name in js for name in ("staging-v1", "workbench.json", "seed.json")), "business data JSON cannot become runtime authority")

    packs = {lang: json.loads((page_root / "data" / ("focus-ui." + lang + ".json")).read_text(encoding="utf-8")) for lang in ("zh", "en")}
    require(set(packs["zh"].get("strings", {})) == set(packs["en"].get("strings", {})), "UI locale coverage differs")
    labels = {node.attrs["data-i18n-key"] for node in dom.nodes if "data-i18n-key" in node.attrs}
    labels |= set(re.findall(r"label\('([^']+)'\)", js))
    for lang, pack in packs.items():
        require(pack.get("coverage", {}).get("mode") == "ui", lang + ": UI pack claims source-content translation")
        require(set(pack) <= {"locale", "page_title", "coverage", "strings"}, lang + ": business collections were added to UI labels")
        require(labels <= set(pack["strings"]), lang + ": missing labels " + ", ".join(sorted(labels - set(pack["strings"]))))
        require(all(isinstance(key, str) and isinstance(value, str) for key, value in pack["strings"].items()), lang + ": UI strings contain structured business records")
        packed = json.dumps(pack["strings"], ensure_ascii=False)
        require(not re.search(r"\b2[0-9]\d{2}\.\d{4,5}(?:v\d+)?\b|https?://(?:www\.)?arxiv\.org/abs/|C:[/\\\\]Users[/\\\\]", packed),
                lang + ": source identities/private paths were hardcoded in UI strings")

    # Enriched small collections supplement the page; existing classification
    # and monthly/document query protocols remain protected.
    for name in PROTECTED_FUNCTIONS:
        actual = _function(js, name)
        if original_js is not None:
            require(_compact(actual) == _compact(_function(original_js, name)), name + ": authority/classification contract changed in a UI-only rearrangement")
    for name in READ_FUNCTIONS:
        actual = _function(js, name)
        if original_js is not None:
            require(_read_calls(actual) == _read_calls(_function(original_js, name)), name + ": existing scoped/exact-key reads changed")
    compact_js = re.sub(r"\s+", "", js)
    for epoch in EPOCHS:
        require("request!==state." + epoch in compact_js, epoch + ": stale responses can overwrite the current view")
    require("revision!==state.revision" in compact_js and "expectedRevision:revision" in compact_js, "revision pinning disappeared")
    require("loadTopicWorkbench('cloud_core')" in js and "state.revision=''" in compact_js and "controls(false)" in compact_js, "authority load/fail-closed behavior changed")
    require("objects.length===7" in compact_js and "methods.length===6" in compact_js and "cells.length===42" in compact_js,
            "canonical 7 x 6 taxonomy integrity guard disappeared")
    require("state.family" not in js and "familyMethods" not in js, "competing map/tracking dimensions were reintroduced")
    require("page('monthly_evidence_cells','scope_cell_key'" in compact_js and "limit:20" in compact_js,
            "selected-cell evidence must keep bounded 20-event pagination")
    require("loadRowsByKeys('ic_evidence_items',ids,revision)" in compact_js and "cloud_core_sources" in js,
            "evidence must still join canonical source identities at an exact revision")
    require("scope.coverage_note" in js and "sample_count" in js and "scope_cell_key" in js,
            "scope coverage and distinct-source counts must remain explicit")
    require("row.inference_scope!=='training_only'" in compact_js and "row.stage!=='training'" in compact_js,
            "training-only techniques escaped the inference boundary")
    start = _compact(_function(js, "start"))
    extended_reads = validate_extended_reads(js)
    require("snapshot.items" in start and "row.collection_key==='information_channels'" in start
            and "row.collection_key==='ascend_assessments'" in start,
            "information channels/Ascend assessments need canonical topic items")
    require("newSet([" in start and "channels.map(row=>row.payload_zh.source_id)" in start
            and "ascendAssessments.map(row=>row.payload_zh.source_id)" in start
            and "loadRowsByKeys('cloud_core_sources',sourceIds,snapshot.revision" in start,
            "channel/Ascend source identities must merge without duplicates and join at the pinned snapshot")
    require("collected.cells.some(cell=>cell.cell_id===zh.cell_id)" in start,
            "Ascend assessment must refer to a canonical compression cell")
    for name in ("renderChannels", "renderAscend"):
        body = _compact(_function(js, name))
        require(("primarySources.find(item=>item.source_id===payload.source_id)" in body or "sourceById(row.source_id)" in body)
                and ("source.canonical_url" in body or "sourceById(row.source_id).canonical_url" in body) and "external(" in body,
                name + ": source links must use the exact canonical source identity")
    enriched = "lineage-cards" in ids or "source-scan-cards" in ids
    if enriched:
        require("lineage-cards" in ids and "source-scan-cards" in ids, "enrichment views must be paired")
        require(_inside(ids["lineage-cards"], ids["map"]) and _inside(ids["source-scan-cards"], ids["channels-panel"]),
                "lineages/source screens escaped their reading layers")
        require(all(dom.nodes.index(ids[target]) < dom.nodes.index(ids["lineage-cards"])
                    for target in ("compact-map", "object-map")),
                "object/method matrix and object cards must precede representative technical routes")
        require(_closed_details(ids["lineage-cards"]),
                "representative technical routes must be a default-closed supplement to the technology map")
        for name in ("lineages", "lineage_nodes", "lineage_relations", "lineage_cells", "source_scans", "source_screenings"):
            require("'" + name + "'" in start, "missing bounded enrichment collection: " + name)
        require("names.map(name=>catalogNames.has(name)?loadCatalog(name,snapshot.revision):small(name,snapshot.revision))" in start
                and "validateEnrichment(collected)" in start,
                "enrichment must use bounded topic/revision reads and fail-closed associations")
        for name, field in (("lineage_nodes", "source_id"), ("lineage_relations", "source_id"),
                            ("source_screenings", "source_id"), ("source_scans", "channel_source_id")):
            require("collected." + name + ".map(row=>row." + field + ")" in start,
                    name + ": source identity is missing from the canonical exact-key join")
        require("['source_id','business_id','canonical_url','title','external_id']" in start,
                "representative node identity/title/URL must come from canonical sources")
        lineage = _compact(_function(js, "renderLineages"))
        require("source.title" in lineage and "technique.mechanism" in lineage and "node.first_submitted_on" in lineage
                and "node.observed_version" in lineage and "node.checked_at" in lineage
                and "relation.relation_kind" in lineage
                and ("element('details')" in lineage or "disclosure('lineage:'" in lineage),
                "route evidence requires canonical mechanism/title, original dates, explicit relations and collapsible details")
        require("state.period" not in _function(js, "visibleLineages"),
                "historical technical routes cannot become selected-month additions")
        require("source_scans" in _function(js, "renderSourceScans") and "title_not_matched_count" in _function(js, "renderSourceScans")
                and "screening_status" in _function(js, "renderSourceScans"),
                "actual source screening must retain counts and verdicts")
        cleared = _function(js, "clear")
        require("'lineage-cards'" in cleared and "'source-scan-cards'" in cleared,
                "failed/replaced snapshots must clear old enrichment claims and links")
        for pack in packs.values():
            require(all("relation_" + kind in pack["strings"] for kind in
                        ("extends", "generalizes", "addresses_limitation", "parallel", "analyst_comparison")),
                    "relationship categories need explicit bilingual labels")
    disclosure_result = validate_disclosure_content(js, html)
    return {
        "pyramid_static": "pass",
        "primary_order": list(PRIMARY_ORDER),
        "information_to_report_links": [href for unused, href in funnel],
        "baseline_regression": "pass" if original_ids is not None else "not_run",
        "preserved_old_ids": len(original_ids) if original_ids is not None else None,
        "unique_ids": len(ids),
        "collapsed_validation_targets": list(DETAIL_CONTENT_IDS),
        "initial_validation_characters": len(validation_text),
        "ui_locale_keys": len(labels),
        "request_fences": list(EPOCHS),
        "protected_classification_query_functions": len(PROTECTED_FUNCTIONS),
        "unchanged_scoped_read_functions": len(READ_FUNCTIONS) if original_js is not None else None,
        "enriched_lineage_source_views": "pass" if enriched else "not_present",
        "technology_map_primary_structure": "visible_object_method_matrix",
        "representative_lineages_default": "closed" if enriched else "not_present",
        "production_browser": "not_checked_by_static_script",
        **shell_result,
        **extended_reads,
        **disclosure_result,
    }



def validate_disclosure_content(js, html):
    """Folded content owns its real view and never relies on a blank second click."""
    owner = _compact(_function(js, "viewForTarget"))
    require("closest('[data-view-panel]')" in owner and "panel.dataset.viewPanel" in owner,
            "deep links must resolve the actual owning view")
    reveal = _compact(_function(js, "revealHashTarget"))
    require("showView(viewForTarget(id))" in reveal and "node.parentElement" in reveal
            and "node.tagName==='DETAILS'" in reveal and "node.open=true" in reveal
            and ".hidden=false" not in reveal,
            "deep links expand details ancestors without bypassing data-dependent hidden state")
    for target, loader in (("source-panel", "loadExpandedDocuments"), ("legacy-panel", "loadExpandedLegacy")):
        require("$('" + target + "').addEventListener('toggle'" in _compact(js)
                and loader in _function(js, "ensureOpenedDisclosuresLoaded"),
                target + ": expansion and data-ready must both trigger the scoped loader")
    docs = _compact(_function(js, "loadExpandedDocuments"))
    require("loadDocuments()" in docs and "state.documentPending.ticket===state.listEpoch" in docs
            and "pending.ticket===state.listEpoch" in docs and "key===documentContextKey()" in docs,
            "automatic note index requires single-flight and stale-context guards")
    require("['document_id','business_id','title','review_status','logical_path']" in _compact(_function(js, "loadDocuments")),
            "opening note index must not fetch document bodies")
    require("scope_empty_help" in _function(js, "renderScope") and "legacy_empty_help" in _function(js, "renderLegacy")
            and "$('legacy-table').hidden" in _function(js, "renderLegacy"),
            "missing scope and statistics must explain gaps instead of exposing blank content")
    require('id="reading-context"' in html and "renderReadingContext()" in _function(js, "render"),
            "current reading scope must be directly visible")
    return {"disclosure_owner_navigation": "pass", "disclosure_auto_metadata_loading": "pass",
            "disclosure_explicit_empty_states": "pass"}


def validate_pyramid_snapshot(path):
    """Check one-entity insight records and their canonical relationships."""
    fixture=json.loads(Path(path).read_text(encoding="utf8"))
    tables={name:[f["row"] for f in frames if not f.get("deleted")] for name,frames in fixture["tables"].items()}
    sources={r["source_id"]:r for r in tables["cloud_core_sources"]}
    cells={r["cell_id"] for r in tables["ic_cells"]}
    techniques={r["technique_id"] for r in tables["ic_techniques"]}
    selected=[r for r in tables["topic_workbench_items"] if r["collection_key"] in {"information_channels","ascend_assessments"}]
    seen=set()
    counts={"information_channels":0,"ascend_assessments":0}
    for row in selected:
        require(row["topic_id"]=="cloud_core" and row["collection_shape"]=="array" and row["locale_status"]=="bilingual","invalid insight item owner or locale")
        zh,en=row["payload_zh"],row["payload_en"]
        require(isinstance(zh,dict) and isinstance(en,dict) and set(zh)==set(en),"insight locale fields differ")
        require(all(isinstance(v,str) for p in (zh,en) for v in p.values()),"insight item must contain scalar strings, not page snapshots")
        key="channel_id" if row["collection_key"]=="information_channels" else "assessment_id"
        require((key,zh[key]) not in seen,"duplicate semantic insight identity")
        seen.add((key,zh[key]))
        for field in (key,"source_id","cell_id","technique_id","status"):
            if field in zh: require(zh[field]==en[field],"locale identity drift")
        require(zh["source_id"] in sources,"insight canonical source is missing")
        require(sources[zh["source_id"]]["business_id"]=="cloud-core","cross-business insight source")
        _public_url(sources[zh["source_id"]]["canonical_url"],"canonical insight source")
        require(not any("url" in k.lower() or "html" in k.lower() or "body" in k.lower() for k in zh),"source bytes/URL duplicated into insight item")
        if key=="assessment_id":
            require(zh["cell_id"] in cells,"unknown Ascend assessment cell")
            require(not zh["technique_id"] or zh["technique_id"] in techniques,"unknown Ascend assessment technique")
            require(zh["status"] in {"candidate_advice","reviewed_advice","not_applicable","evidence_gap"},"unknown assessment maturity")
            require(all(zh.get(f) and en.get(f) for f in ("finding","boundary","next_action")),"unbounded Ascend advice")
        counts[row["collection_key"]]+=1
    return {"insight_item_graph":"pass","insight_item_counts":counts}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page-root", type=Path, required=True)
    parser.add_argument("--baseline-page", type=Path, help="Exact pre-edit UI baseline for this change's regression comparison")
    parser.add_argument("--max-validation-chars", type=int, default=360)
    parser.add_argument("--snapshot", type=Path, help="Optional exact native snapshot for canonical insight/enrichment checks")
    args = parser.parse_args()
    try:
        result = validate_pyramid(args.page_root, args.baseline_page, args.max_validation_chars)
        if args.snapshot:
            result.update(validate_pyramid_snapshot(args.snapshot))
            if result["enriched_lineage_source_views"] == "pass":
                from validate_lineage import validate_lineage_snapshot
                result.update(validate_lineage_snapshot(args.snapshot))
    except (AssertionError, OSError, ValueError, KeyError) as error:
        print(json.dumps({"pyramid_static": "fail", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False))

