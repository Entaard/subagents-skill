---
id: harness-stamp
kind: stamp
class: local
status: live
---

## Harness version stamp

<!-- /sage-promote stage three must carry the `sage-harness-stamp:` line below through unchanged in shape, on one line, still matching ^sage-harness-stamp:. The run-side lineup hint compares against it, so a rewrite that drops or reflows it disarms that hint with nothing to show for it. The installer checks a different anchor — the `sage-local-memory` sentinel on line 1 of journal.md. -->

sage-harness-stamp: unset | verified unset

Set it on the first run: the Claude Code version this machine's harness facts were verified against, then the date. Shape once set: `sage-harness-stamp: 2.1.229 | verified 2026-08-17`. A version-bound claim anywhere in this file older than this stamp is stale; /sage-promote stage three re-verifies it.
