"""Read-only bootstrap and reading-contract gate for compression topic pages."""
from pathlib import Path
from html.parser import HTMLParser
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
class Head(HTMLParser):
    def __init__(self):
        super().__init__(); self.styles=[]; self.scripts=[]; self.inline=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=="link" and a.get("rel")=="stylesheet": self.styles.append(a.get("href",""))
        if tag=="script" and (a.get("src") or a.get("data-lri-reader")): self.scripts.append(a.get("src") or a["data-lri-reader"])
        if tag=="style" or "style" in a: self.inline+=1
def main():
    config=json.loads((ROOT/"assets/lri-shell.config.json").read_text())
    for name in ("index.html","topic.html","monthly.html"):
        html=(ROOT/"business_insight/cloud_core"/name).read_text(); parser=Head(); parser.feed(html)
        assert len(parser.styles)==1 and ("assets/insight-executive.css?v="+config["style_version"]) in parser.styles[0], "single canonical stylesheet"
        assert not parser.inline, "no inline styles"
        assert 'id="legacy-map-index"' not in html and 'id="compact-map"' not in html, "obsolete 7-by-6 map is removed"
        assert 'id="scientific-map"' in html, "scientific topic map remains"
        assert ('data-lri-shell="auto"') in html and ('assets/lri-shell.js?v='+config["version"]) in html, "canonical shell"
        entry="topic-entry.js" if name=="topic.html" else "reader-entry.js"
        assert sum(entry in v for v in parser.scripts)==1, "one generated reader entry"
        assert 'lri-page-translation" content="ui"' in html, "partial translation must remain explicit"
    transport=(ROOT/"business_insight/cloud_core/runtime/mcp-table-read.js").read_text()
    for table in ("ic_compression_topic_cards","ic_compression_topic_card_refs"):
        assert table in transport, "registered read-only table: "+table
    loader=(ROOT/"business_insight/cloud_core/topic-dossier.js").read_text()
    assert "filterField:'compression_topic_id'" in loader and "expectedRevision:revision" in loader and "loadRowsByKeys('cloud_core_sources'" in loader, "bounded exact-revision joins"
    js=(ROOT/"business_insight/cloud_core/compression.js").read_text()
    assert "card.dataset.claimKind=row.claim_kind" in js and "row.claim_kind==='author_result'" in js, "facts and analysis retain their provenance"
    assert "loadCompressionTopicEvidence(offset,true)" in js and "Cross-topic source mismatch" in js, "monthly union follows explicit topic relationships"
    assert "topic-monthly-coverage" in js and all(s in js for s in ("paper_one_sentence","paper_keywords","paper_background","paper_innovation","paper_results")), "monthly structured facts"
    for locale, expected in (("zh", ["信息来源","技术地图","本期动态","洞察报告","洞察归档"]), ("en", ["Information sources","Technology map","Current updates","Insight report","Insight archive"])):
        group=next(g for g in config["locales"][locale]["context_nav"] if g["id"]=="cloud-core-compression")
        assert [item["label"] for item in group["items"]]==expected, "five-step sidebar order"
        assert group["section_navigation"]=="folded" and group["preserve_query"]==["month","scope"], "topic chapters and scope preservation"
    shell=(ROOT/"assets/lri-shell.js").read_text()
    assert "data-shell-outline" in shell and "lriContextItem" in shell and "preserve_query" in shell, "shared sidebar contract"
    monthly=(ROOT/"business_insight/cloud_core/monthly-routes.js").read_text()
    assert "filterField:field" in monthly and "expectedRevision:revision" in monthly, "monthly routes use bounded exact-revision reads"
    assert all(name in transport for name in ("monthly_route_insights", "monthly_route_evidence")) and "tables.add('ic_' + name)" in transport, "monthly routes registered in read-only transport"
    assert all(s in monthly for s in ("ic_paper_summary_events", "ic_evidence_items", "Wrong monthly event version", "Unreviewed or unmapped route evidence")), "monthly route claims bind reviewed current events and versions"
    assert "readingLayer='facts'" in monthly and "readingLayer='analysis'" in monthly and "cache.get(key)===entry" in monthly, "facts precede viewpoints; retired requests cannot overwrite current routes"
    html=(ROOT/"business_insight/cloud_core/index.html").read_text()
    assert "monthly-route-report" in html and "current-paper-index" in html, "monthly reader retains route narrative and full evidence index"
    subprocess.run(["node","tools/cloud_core/test_research_priorities.cjs"],cwd=ROOT,check=True)
    subprocess.run(["python3","tools/cloud_core/build_reader_entry.py","--check"],cwd=ROOT,check=True)
    entry=(ROOT/"business_insight/cloud_core/reader-entry.js").read_text()
    assert entry.index("// Source: monthly-routes.js") < entry.index("// Source: compression.js"), "route loader precedes monthly application"
    topic_html=(ROOT/"business_insight/cloud_core/topic.html").read_text()
    assert "monthly-routes.js" not in (ROOT/"business_insight/cloud_core/topic-entry.js").read_text(), "research topic does not mount the period narrative loader"
    assert all(s in js for s in ("select(['scope','value','challenges'])", "select(['mechanism','routes'])", "select(['papers','sources'])", "select(['comparison','boundary','implications','watch'])")), "topic outline follows motivation, approach, facts and synthesis"
    assert "node.dataset.readingLayer=['comparison','boundary']" in js, "semantic topic evidence layers"
    assert all(t in loader for t in ("ic_compression_research_frames","ic_compression_research_routes","unbound research route","incomplete research framing")), "bounded evidence-linked motivation and route content"
    assert "renderResearchFraming(scope,'why')" in js and "renderResearchRoutes(routeSection)" in js, "topic motivation and concrete route explanations"
    topic_reader=js[js.index("function renderCompressionTopic("):js.index("function scientificLink(",js.index("function renderCompressionTopic("))]
    assert "section('updates')" not in topic_reader and "topicMonthly" not in topic_reader and "Monthly events" not in topic_reader, "research topics exclude period event content and counts"
    map_reader=js[js.index("function renderScientificMap("):js.index("function renderSelectors(")]
    assert "topicEventsFor(" not in map_reader and "研究专题" in map_reader, "matrix cells identify research topics without period counts"
    assert "literature-cell-concept" in map_reader and "textOf(concept,'summary')" in map_reader and "项代表技术" not in map_reader and "rows.slice(0,3).map(title)" not in map_reader, "map cards introduce concepts instead of catalog counts"
    assert "ic_compression_topic_concepts" in transport and "Incomplete topic conceptual definitions" in js, "all twelve bilingual definitions come from revision-pinned TableGit"
    assert "if(topicPage())return; // Period evidence belongs" in js and "timelineLink.dataset.compressionTopicTimeline='true'" in topic_reader, "period facts load only in the separate linked updates reader"
    for name in ("index.html","topic.html","monthly.html"):
        html=(ROOT/"business_insight/cloud_core"/name).read_text()
        assert "source_selection_policy" in html and "collection_health_details" in html, "source policy and collection health have distinct labels"
        if name == 'index.html':
            assert 'id="analysis-facts"' not in html and html.index('id="insight-report-presentation"') < html.index('id="ascend"'), "analysis retains the report before route decisions; facts stay in current updates"
        else:
            assert html.index('id="analysis-facts"') < html.index('id="finding-cards"') < html.index('id="ascend"'), "legacy hidden mounts retain their layer order"
    assert all(s in monthly for s in ("monthly-fact-overview","monthly-topic-directory","monthly-technical-routes","monthly-evidence-index","ic_paper_summary_keywords","notifyOutline()","monthly-evidence-")), "monthly report has fact overview, map directory, route chapters, evidence drilldown and indexed keywords"
    assert "[\'topic-only\',\'folded\'].includes" in shell, "shared Shell renders folded reading contents on every cloud-core tab"
    assert "ic_compression_mechanism_steps" in loader and "supporting_card_id" in loader, "mechanism figures must bind canonical research cards"
    assert all(token in js for token in ("researchNav(parent)","renderMechanismDiagram(mechanism)","applyResearchView(parent)","dataset.compressionMonthly","compressionResearchView")), "addressable research pages retain diagrams and view routing"
    assert all(token in monthly for token in ("readerUrl(story.story_id)","readerUrl('',ref.summary_id)","renderRouteDiagram(mechanismDetails","pick(summary,'background'","keywordMap.get(ref.summary_id)")), "monthly routes and five-field papers have dedicated readers"
    css=(ROOT/"assets/insight-executive.css").read_text()
    assert ".monthly-route-interpretation{background:var(--soft" not in css, "text-color tokens may not define analysis surfaces"
    assert 'data-compression-monthly="true"' in (ROOT/"business_insight/cloud_core/monthly.html").read_text(), "monthly reader owns a separate route"
    subprocess.run(["node", "tools/cloud_core/test_compression_foundations.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_foundation_lessons.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_weight_topic_structure.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_report_reader.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_report_organization.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_topic_continuous_reader.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_research_visuals.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_route_evidence.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_industry_updates.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_current_synthesis_lifecycle.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_current_update_relevance.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_current_topic_entry.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_reader_bootstrap.cjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "tools/cloud_core/test_reader_ui_cache.cjs"], cwd=ROOT, check=True)
    print(json.dumps({"pass":True,"pages":3,"canonical_shell":True,"single_stylesheet":True,"bootstrap_transport":True,"bounded_dynamic_reads":True,"translation":"ui-partial; dossier cards bilingual"}))
if __name__=="__main__": main()



