# Final-a1 round-2 builder release

RELEASE: the exclusive final-a1 round-2 source/new-sandbox writer lease is released. The candidate is frozen for the separate whole-skill critic. No builder process, native actor, mutation, or unknown effect remains pending.

## Candidate

- Manifest: `sage/evaluation/sandboxes/final-a1-r2-builder/candidate-manifest.json`
- Manifest SHA-256: `3f7f4c9e8ca6a8a76684ef2bbc34f7fd89dde29f5456c27b9ea6d47556a0fdde`
- Bound active source files: 42
- Prior round-1 manifest SHA-256: `c0767e686daa9ed9edc885b6335e441e143af9a526f8a9df9fbee49c4324f692`
- Retained round-1 candidate-source mismatches: 0

Exactly five active source files changed from round 1:

| Path | SHA-256 |
| --- | --- |
| `sage/ARCHITECTURE.md` | `601b82424629fb748afacc2c723feb770385e6f644ea4e1b2b6d77dec0575ad6` |
| `sage/docs/DECISIONS.md` | `b35bb3442ff3541c6d5a9c63686806b23fee83b3240016cc22e14b3a739a83d4` |
| `sage/docs/IMPLEMENTATION.md` | `9bf9e8a03350a3fe0b270e4c3f8f162290bc766553dd5bed9a87000647d76ccd` |
| `sage/skills/sage-promote/SKILL.md` | `ba2f0d5dbc5fa2fd1537bf18a53a7ce92006c93a346cb7c353e7a59bb2e93770` |
| `sage/skills/sage-promote/references/promotion.md` | `c605e9939d6f79cbc945f185e2e57c37110c3169b00337a97d3e0fefde54500f` |

No helper, schema, metadata/invocation policy, frozen protocol/rubric, original live result, review, retained source snapshot, or `sage-claude` file changed. `sage/docs/STATUS.json` still byte-matches the retained round-1 critic's `status-after-review.json`; the builder did not edit it. Full preservation details and retained evidence hashes are in `preservation.json`.

## Red, green, and normal gate

Pre-edit command (exit 1):

```text
SAGE_R2_PHASE=red PYTHONDONTWRITEBYTECODE=1 python3 sage/evaluation/sandboxes/final-a1-r2-builder/test_promotion_coordination.py
```

Six fresh-installed checks ran. Five existing main/helper and scripted-workflow controls passed; only standalone promotion's installed instruction graph failed because it reached no sibling run/state/delegation/recovery references. Evidence: `red/summary.json`.

The first post-edit `green/` retry retained one probe-only failure: its exact lowercase phrase check was case-sensitive against sentence-leading “Knowledge.” The product links and clause were present. The probe normalized case, then `green2/` passed. After the finish/continuing-authority wording refinement, the final focused command passed 6/6 (exit 0):

```text
SAGE_R2_PHASE=green3 PYTHONDONTWRITEBYTECODE=1 python3 sage/evaluation/sandboxes/final-a1-r2-builder/test_promotion_coordination.py
```

The informed scripted public-CLI scenario covers separate own-run authority, pre-dispatch stale projection, corrupt log preservation/blocking, requested versus unobserved effective identity, unknown actor/effect writer barrier, pre/post stage and activation checkpoints, changed proposal/pointer/authority replanning, unchanged source logs, and zero-team/no-generation `no_change`. Fixture actor IDs are not native observations.

The final complete normal offline gate passed 95 tests with zero failures, errors, or skips (exit 0):

```text
PYTHONDONTWRITEBYTECODE=1 python3 sage/evaluation/run_verification.py --mode red --evidence-dir sage/evaluation/sandboxes/final-a1-r2-builder/full4
```

It reports `live_trials_run: false` and `network_used: false`. `git diff --check -- sage` also passed.

## Scope and limits

The repair connects `$sage-promote` to existing installed shared seams and adds only promotion-specific ownership, baseline, checkpoint, recovery, and finish instructions. It does not claim an observed unsafe pre-fix activation, a runtime fix, native actor/model behavior, behavioral independence, semantic evidence quality, automatic home discovery, cost savings, or a new live result. Original final-a1 round-1 scores and finding remain retained until the independent critic adjudicates this frozen candidate.
