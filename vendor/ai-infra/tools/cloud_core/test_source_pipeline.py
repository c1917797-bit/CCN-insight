import copy
import unittest
import socket

from source_pipeline import audit, acquire, classify, identity, public_url, upsert_plan, plan_acquisition, fingerprint, REQUIRED_TABLES, STAGES
from source_pipeline_schema import DEFINITIONS

NOW = "2026-10-16T12:00:00+00:00"


def source(sid="s", title="Sliced-Wasserstein Distribution Alignment Loss Improves the Ultra-Low-Bit Quantization of Large Language Models", url="https://arxiv.org/abs/2601.07878"):
    return dict(source_id=sid, business_id="cloud-core", title=title, canonical_url=url, source_kind="paper", verification_status="not_checked", external_id="2601.07878")


def fixture(sources=None):
    data = {name: [] for name in REQUIRED_TABLES}
    data["cloud_core_sources"] = sources or [source()]
    data["ic_compression_topics"] = [dict(compression_topic_id=x) for x in ["parameters-precision", "parameters-factorization", "parameters-distillation", "parameters-selection", "kv_cache-kv_eviction", "kv_cache-precision"]]
    return dict(revision="a" * 40, tables=data)


def reviewed_fixture():
    f = fixture()
    f["tables"]["cloud_core_sources"][0]["verification_status"] = "primary_full_text_reviewed"
    summary = dict(summary_id="s__v1", source_id="s", observed_version="v1", review_status="method_results_checked", evidence_url="https://arxiv.org/html/2601.07878v1", evidence_locator="Table 4", one_sentence_zh="x", background_zh="x", innovation_zh="x", results_zh="x", reviewed_at="2026-10-16")
    event = dict(evidence_id="e", source_id="s", observed_version="v1", status="primary_text_checked", verified_at="2026-10-16", publication_date="2026-01-10", event_date="2026-01-10")
    f["tables"]["ic_paper_summaries"] = [summary]
    f["tables"]["ic_evidence_items"] = [event]
    return f


class PipelineTests(unittest.TestCase):
    def test_business_context_required_and_no_automatic_exclusion(self):
        for title in ["Vector Quantized Latent Concepts: A Scalable Alternative to Clustering-Based Concept Discovery", "Learning is Forgetting: LLM Training As Lossy Compression", "Few-step Generative Models as Lossy Compression", "One-Bit Quantization for Random Features Models"]:
            self.assertEqual(classify(source(title=title), fixture())["stage"], "needs_relevance_review")
        for title in ["SeVeDo: A Heterogeneous Transformer Accelerator for Low-Bit Inference", "Post-Training Quantization for Speech Denoising", "Efficient Knowledge Distillation for Neural Machine Translation"]:
            self.assertEqual(classify(source(title=title), fixture())["stage"], "candidate_direct")

    def test_input_complete_revision_required(self):
        for f in [dict(revision="main", tables={}), dict(revision="a" * 40, tables={})]:
            with self.assertRaises(ValueError):
                audit(f, NOW)

    def test_full_conservation_and_schema(self):
        f = fixture([source(), source("id", "2608.00573", "https://arxiv.org/abs/2608.00573"), source("invalid", "Good paper title", "https://arxiv.org/abs/bad")])
        result = audit(f, NOW)
        run = result["tables"]["ic_pipeline_runs"][0]
        self.assertEqual(sum(run[s] for s in STAGES), 3)
        self.assertEqual(run["processed_sources"], run["total_sources"])
        for name, values in result["tables"].items():
            for row in values:
                self.assertEqual(set(row), set(DEFINITIONS[name]["fields"]))
                self.assertTrue(all(isinstance(row[k], int if v["type"] == "integer" else str) for k, v in DEFINITIONS[name]["fields"].items()))

    def test_titles_never_reviewed_or_excluded(self):
        examples = [("Sliced-Wasserstein Distribution Alignment Loss Improves the Ultra-Low-Bit Quantization of Large Language Models", "candidate_direct"),
                    ("Swift-SVD: Theoretical Optimality Meets Practical Efficiency in Low-Rank LLM Compression", "candidate_direct"),
                    ("DeltaLog: Deferred Materialization of Recurrent States for Linear Attention Decoding", "candidate_adjacent"),
                    ("ShadowServe: Interference-Free KV Cache Fetching for Distributed Prefix Caching", "candidate_adjacent"),
                    ("Parallel SMT Solving via Dynamic Partitioning, Core-Guided Pruning, and Online Backbone Detection", "needs_relevance_review"),
                    ("Generalized Low-Rank Matrix Contextual Bandits with Graph Information", "needs_relevance_review"),
                    ("An Entirely Differently Named Paper", "needs_relevance_review")]
        for title, expected in examples:
            with self.subTest(title=title):
                self.assertEqual(classify(source(title=title), fixture())["stage"], expected)

    def test_manual_decision_not_overwritten(self):
        f = fixture()
        f["tables"]["ic_source_screenings"] = [dict(source_id="s", checked_at="2026-10-15", screening_status="excluded", reason_zh="不属推理", reason_en="Not inference")]
        result = audit(f, NOW)["tables"]["ic_source_pipeline"][0]
        self.assertEqual(result["stage"], "excluded_manual")
        self.assertIn("不属推理", result["reason_zh"])

    def test_reviewed_requires_evidence_and_publication_association(self):
        f = reviewed_fixture()
        self.assertEqual(classify(f["tables"]["cloud_core_sources"][0], f)["stage"], "reviewed_unpublished")
        f["tables"]["ic_paper_review_intakes"] = [dict(source_id="s", summary_id="s__v1", publication_date="2026-01-10", reviewed_at="2026-10-16", review_period_id="2026-10")]
        self.assertEqual(classify(f["tables"]["cloud_core_sources"][0], f)["stage"], "reviewed_visible")
        f["tables"]["ic_evidence_items"][0]["status"] = "candidate"
        self.assertEqual(classify(f["tables"]["cloud_core_sources"][0], f)["stage"], "reconciliation_needed")

    def test_not_checked_source_preserves_review_gap(self):
        f = reviewed_fixture()
        f["tables"]["cloud_core_sources"][0]["verification_status"] = "not_checked"
        self.assertEqual(classify(f["tables"]["cloud_core_sources"][0], f)["stage"], "reconciliation_needed")

    def test_unsafe_and_alias_identity(self):
        self.assertEqual(identity(source(url="https://arxiv.org/pdf/2601.07878v2.pdf")), identity(source()))
        self.assertEqual(identity(source(url="https://openreview.net/pdf?id=ABC")), identity(source(url="https://openreview.net/forum?id=ABC")))
        for url in ["https://127.0.0.1/x", "https://localhost/x", "https://example.com/?token=abc", "https://u:p@example.com/x"]:
            with self.assertRaises(ValueError):
                public_url(url)

    def test_duplicate_is_reference_not_deleted(self):
        f = fixture([source("a"), source("b", url="https://arxiv.org/pdf/2601.07878v2.pdf")])
        result = audit(f, NOW)
        self.assertEqual(len(result["tables"]["ic_source_pipeline"]), 2)
        self.assertEqual(result["tables"]["ic_pipeline_runs"][0]["duplicate_refs"], 1)

    def test_idempotent_noop_and_version_fence(self):
        values = audit(fixture(), NOW)["tables"]["ic_source_pipeline"]
        existing = [{"key": r["source_id"], "row": r, "row_version": 4} for r in values]
        self.assertEqual(upsert_plan(values, existing, "source_id"), [])
        newer = copy.deepcopy(values)
        newer[0]["stage"] = "metadata_needed"
        ops = upsert_plan(newer, existing, "source_id")
        self.assertEqual(ops[0]["expected_row_version"], 4)

    def test_route_hints_do_not_force_kv_eviction_to_channel_pruning(self):
        f = fixture([source(title="ProxyKV: Cross-Model Proxy Pruning for Efficient Long-Context LLM Inference")])
        matches = audit(f, NOW)["tables"]["ic_source_route_candidates"]
        self.assertEqual([m["route_topic_id"] for m in matches], ["kv_cache-kv_eviction"])
        self.assertTrue(all(m["relation_kind"] == "machine_candidate_not_confirmed" for m in matches))

    def test_retry_429_then_ready_and_long_retry_is_deferred(self):
        atom = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/2601.07878v1</id><title>Official Paper Title</title><published>2026-01-10T00:00:00Z</published></entry></feed>'
        responses = iter([(429, {"Retry-After": "0"}, b""), (200, {}, atom)])
        result = acquire(source(), "arxiv_metadata", "run", NOW, get=lambda *a: next(responses), sleep=lambda x: None)
        self.assertEqual([a["status"] for a in result["attempts"]], ["retryable_failure", "metadata_ready"])
        self.assertEqual(result["items"][0]["observed_version"], "v1")
        result = acquire(source(), "arxiv_metadata", "run", NOW, get=lambda *a: (429, {"Retry-After": "600"}, b""), sleep=lambda x: self.fail("must defer long backoff"))
        self.assertEqual(len(result["attempts"]), 1)
        self.assertTrue(result["attempts"][0]["next_retry_at"])

    def test_dns_failure_is_recorded_and_retried(self):
        def fail(*args):
            raise socket.gaierror('fixture DNS failure')
        result=acquire(source(), 'arxiv_metadata', 'run', NOW, get=fail, sleep=lambda x: None)
        self.assertEqual(len(result['attempts']),3)
        self.assertTrue(all(a['status']=='retryable_failure' for a in result['attempts']))
        self.assertEqual(result['items'],[])

    def test_acquisition_plan_preserves_review_and_fences_identity(self):
        f=fixture();f['tables']['cloud_core_sources']=[{'key':'s','row_version':7,'row':source(title='2601.07878')}]
        atom=b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/2601.07878v1</id><title>Official Quantization Paper</title><published>2026-01-10T00:00:00Z</published></entry></feed>'
        s=f['tables']['cloud_core_sources'][0]['row']
        out=acquire(s,'arxiv_metadata','run',NOW,get=lambda *a:(200,{},atom))
        out.update(source_revision=f['revision'],source_fingerprint=fingerprint(s))
        plan=plan_acquisition(f,out)
        updated=plan['tables']['cloud_core_sources'][0]
        self.assertEqual(updated['verification_status'],'public_metadata_observed')
        self.assertEqual(updated['title'],'Official Quantization Paper')
        self.assertEqual(plan['operations'][1]['operations'][0]['expected_row_version'],7)
        with self.assertRaises(ValueError):plan_acquisition(f,{**out,'source_revision':'b'*40})
        s['verification_status']='primary_text_checked';out['source_fingerprint']=fingerprint(s)
        self.assertEqual(plan_acquisition(f,out)['tables']['cloud_core_sources'][0]['verification_status'],'primary_text_checked')

    def test_failed_acquisition_enters_retry_queue(self):
        f=fixture();f['tables']['ic_source_acquisition_attempts']=[{'source_id':'s','attempt':1,'attempted_at':NOW,'next_retry_at':NOW,'status':'retryable_failure'}]
        self.assertEqual(classify(source(),f)['stage'],'retryable_failure')

    def test_304_and_404_do_not_fabricate_metadata(self):
        for status, expected in [(304, "not_modified"), (404, "blocked")]:
            result = acquire(source(), "arxiv_metadata", "run", NOW, get=lambda *a: (status, {}, b""))
            self.assertEqual(result["status"], expected)
            self.assertEqual(result["items"], [])
        for row in result["attempts"]:
            self.assertEqual(set(row), set(DEFINITIONS["ic_source_acquisition_attempts"]["fields"]))


if __name__ == "__main__":
    unittest.main()

