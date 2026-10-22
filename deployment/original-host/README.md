# Original-host publication preparation

The CCN site is already live at Sites version 12. The original Irigit site has not been updated.

`release.py` is intended for the isolated Works authoring workspace via the revision-fenced Irigit `repo.author/exec` operation. It prepares a temporary copy, loads the pinned CCN reader and corpus, preserves the existing binary reports, normalizes shell metadata, and runs the full Works validation. It applies files to the authoring workspace only on a successful full validation; publication remains a separate native Irigit operation.

The style repair comes from `content/original-host-shared-style-repair.css`; the provider fixture correction is retained here for review. Existing runtime revision checks are unchanged, and tests now explicitly reject missing or mixed page revisions.

Five focused checks passed, covering 607 HTML pages and 65 configured Hosted Tables. Full validation is blocked because the controlled execution environment cannot access the separate TableGit repository. The attempted official HTTP read returned `authorization_failed` for Guest and requires the instance's Basic User and Basic Verify. Do not put credentials in this directory, script arguments, logs, or source files.

See `docs/original-host-release-preflight.json` for the actual check results. Do not mark the original site as published until validation, native publication, and public-page verification succeed.
