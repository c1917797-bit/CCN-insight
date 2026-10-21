# Cloud Core research intake

This runner maintains processing state for registered papers. A complete audit means every registered paper has a disposition, not that every paper is relevant, reviewed or covered by a collection schedule.

## Repeatable update cycle

1. Resolve current TableGit HEAD with `table_status`. Export the required tables at that exact revision, retaining row keys and row versions. For relations use each table's returned repository authority; aliases can differ. Reject truncated exports. Public source URLs and approved metadata only; no credentials or whole article bodies.
2. Run `python3 tools/cloud_core/source_pipeline.py audit --snapshot INPUT --output AUDIT`. This recomputes evidence and publication links as well as relevance candidates. Preserve prior pipeline rows in INPUT to obtain a minimal version-fenced mutation plan.
3. For a missing-metadata or due retry item, run `acquire --snapshot INPUT --source-id ID --adapter arxiv_metadata --run-id UNIQUE --allow-network --output FETCH`. Registered feeds and GitHub releases use their corresponding adapter; never assume an arbitrary repository is a registered channel. Use `--previous-output` to retain conditional request metadata and enforce retry time.
4. Run `plan-acquisition --snapshot INPUT --acquisition-output FETCH --output PLAN`. Submit its operations through native TableGit `worktree_table_batch_transaction` against the exact input revision. Failed acquisition still has attempt records; successful metadata is never promoted to scientific review. For channel adapters include collection tables and an explicit registered channel. Each response is bounded to 100 items; retain continuation information and do not claim exhaustive history.
5. Refresh the committed snapshot after metadata writes and run the audit again. For a multi-batch initial index, first insert a run with `status=indexing`, zero processed/stage counts, and an empty completion timestamp. Commit all state and candidate batches with real row-version fences. Mark the run `completed_audit_not_research_review` only after count conservation and native row verification. Never publish a completed denominator for a partial load.
6. Review direct and adjacent candidates against primary material. Write explicit relevance verdicts, versioned summaries, experiment conditions and locators. Preserve first publication, version revision and editorial review dates separately. Existing reviews with conflicting state go to reconciliation instead of disappearing or silently becoming full-text reviewed.
7. Run `python3 tools/cloud_core/test_source_pipeline.py` and the reader contract tests. Open the source queue, exercise filters/search/paging and open a reviewed paper in the normal browser session. Record the data revision and outcome.

## Invariants

- Paper stages sum to the paper denominator. Duplicate references are an orthogonal provenance count, not an extra stage.
- Titles only generate candidates. Unmatched titles and ambiguous terminology remain unresolved; explicit human exclusions are preserved.
- Adjacent serving/state/traffic optimizations remain discoverable outside the compression matrix.
- Source identity, relevance, review depth and reader placement are separate. No automatic model-performance or Ascend-support conclusions.
- A stale or conflicting input is re-exported before mutation. Never substitute row version 1 for an observed version.
- Native transactions are idempotent. Retain transaction receipts and retry the same transaction key after an uncertain response.
- The reader queries a bounded page at one committed revision. It does not download the whole corpus or replace authority with a static JSON copy.
- Network failures retain retry status. Respect Retry-After; no authentication bypass, credentials in artifacts, or unbounded retry loops.

## Operational boundary

This is an explicit operator-run workflow. No background scheduler is installed by this change. Metadata acquisition depends on permitted network access; a DNS failure is a recorded acquisition failure, not evidence that the paper does not exist. The corpus still requires progressive primary-source review.
