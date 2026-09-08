# Codex Sage rebuild handoff

Completed 2026-09-08. All seven current module gates pass; the independent whole-skill review has zero open errors and every dimension is at least 8.5. This is a bounded verified rebuild, not a guarantee of perfect future output or measured cost savings.

## What changed

The active product is Codex-only: a short [Sage entrypoint](../skills/sage/SKILL.md), a separate [sage-promote entrypoint](../skills/sage-promote/SKILL.md), focused conditional references, and two dependency-free state/knowledge helpers. Legacy material is quarantined under `archive/legacy/`, not served as an installation fallback. No portability framework or Claude changes were added.

Sage defines observable task-specific excellence, keeps small work inline, and assigns bounded work using capability-first routing and total coordination cost. Model/effort placements remain revisable priors, with requested and observed identity distinguished. Planning, evidence, independent review, cause-responsive retries, checkpoints and truthful completion share one durable run contract.

Promotion separately qualifies closed evidence, extracts bounded rules, challenges counterexamples, applies evidence-class gates, and stages reversible knowledge generations. It now explicitly owns its own coordinator plan/log and recovery workflow, separate from immutable source runs and knowledge-store artifacts. Actual knowledge changes require distinct author, refuter and reviewer roles; `no_change` retains a zero-team path.

Skill-authoring and writing-for-agents guidance kept the always-loaded instructions compact and the operational detail behind explicit pointers. TDD and module-design guidance kept verification at existing public interfaces instead of introducing another runtime.

## Current gates and preserved failures

| Module | Passing round | Lowest current score | Failed rounds retained |
| --- | ---: | ---: | ---: |
| Architecture | 2 | 8.6 | 1 |
| Verification | 3 | 8.5 | 2 |
| Sage | 3 | 8.5 | 2 |
| Promotion | 3 | 8.6 | 2 |
| Integration | 2 | 8.6 | 1 |
| Post-live repairs | 3 | 8.5 | 2 |
| Whole skill | 2 | 8.5 | 1 |

[STATUS.json](STATUS.json) retains all 18 critic rounds, including 11 failures, exact scores, finding dispositions and evidence pointers. No aggregate score compensates for a low dimension.

The [final independent review](reviews/final-a1-r2.json) scored:

| Standard | Score |
| --- | ---: |
| Requirements/spec fit | 8.5 |
| Architecture/coherence | 9 |
| Correctness/evidence | 8.5 |
| Simplicity/context efficiency | 8.5 |
| Orchestration/model routing | 8.5 |
| Safety/reversibility/recovery | 8.5 |
| Verification strength | 9 |
| Reporting/maintainability | 8.5 |

## What was verified

- All 57 requirement IDs assessed by the whole-skill critic.
- 95 normal offline tests passed independently from a source copy.
- Six focused installed promotion checks passed; the same checks retain the old package's documentation failure.
- An additional independent 13-command scenario checked recovery after a lost activation acknowledgement, observation before reconciliation, continued write barriers and honest stopped closure without replaying activation.
- Fresh sandbox installation and all 15 local links verified.
- Original scorecard evidence retained: 313 bindings checked unchanged.
- All 46 tracked `sage-claude` files match the original baseline; its worktree is unchanged.

The final reviewed candidate manifest is [here](../evaluation/sandboxes/final-a1-r2-builder/candidate-manifest.json), SHA256 `3f7f4c9e8ca6a8a76684ef2bbc34f7fd89dde29f5456c27b9ea6d47556a0fdde`. Only results/status documentation was updated after that review; installed skills and executable source were not changed.

## Original live results remain original

The [original live report](LIVE-RESULTS.md) covers seven arms: two paired code/data cases and three unpaired creative, recovery and promotion smokes. Recovery passed; six reporting scores and the creative orchestration score failed. Later repairs fixed the observed reporting, pre-creation reconciliation, native result encoding and event-documentation issues, then the final review found and fixed promotion's missing own coordination instructions.

Those repairs are informed follow-up evidence. They do not retroactively pass or rescore the original live trials. The frozen v2 rejection remains; the separate native-v3 encoding handles evidenced lifecycle completion without inventing a native OS exit.

## Limits and use

Effective model/effort, normalized token/money measurements and general cost savings remain unestablished. Routing is designed to be economical, but two paired cases cannot prove a universal cost-quality advantage. The small interactive case is not evidence of AAA-scale game delivery. Scripted promotion recovery does not establish native context-compaction behavior. Home automatic discovery was not tested; installation was confined to sandboxes.

State/knowledge helpers validate structure and recorded evidence, not semantic truth, user authority, behavioral independence or a physical writer lease. Knowledge rollback requires intact retained history. Installation is conservative, not crash-atomic against arbitrary I/O or concurrent filesystem changes. The bundled PyYAML-dependent validator was unavailable; no pass is claimed for it.

Use the [installation and invocation guide](../README.md). No home installation was performed. For design and change detail, read [ARCHITECTURE.md](../ARCHITECTURE.md), [IMPLEMENTATION.md](IMPLEMENTATION.md) and [DECISIONS.md](DECISIONS.md).
