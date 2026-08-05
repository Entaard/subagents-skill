# Calibration log

What orchestration runs on this machine actually cost, against what was estimated.

Read this at **Step 3**, before writing a budget: where a row covers the task class in hand, its
actuals beat the coarse bands in `contracts.md`. Append one row at **Step 7**, every run — including
the runs where the estimate held. A band you can trust needs its hits recorded next to its misses.

This file is yours, not the skill's. `install.sh` seeds it once and never overwrites it, so it
survives updates and grows with use.

| date | task class | agents | est | actual | wall clock | note |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-08-04 | web research sweep, agents fetching primary sources | 5 | 225k | 451k | ~25 min | **Fetch-heavy web research runs 70–120k per agent, not the 15–40k exploration band.** Off by 2–3×. |
| 2026-08-04 | completeness critic over ~25k words of notes + 4 skill files | 1 | 35k | 172k | ~10 min | **A critic's cost tracks the corpus it must read, not the number of drafts it reviews.** Off by 5×. Estimate from input size. |
| 2026-08-05 | 2 reviewers on a small prose diff, against a written spec | 2 | 120k | 193k | ~7 min | Off by 1.6× — and the diff was *small*. Reviewers still had to hold the whole 6.6k-word skill plus a 2.8k-word spec. **Review cost tracks the corpus the reviewer must hold, not the size of the change.** |

## How to read this

Three rows, three misses, all in the same direction: **the bands under-estimate whenever an agent must
ingest a large body of material before reasoning over it.** Web fetches, long document corpora, and a
small diff that still requires reading a whole document set all trip it. The third row is the sharpest
version — the *change* under review was tiny and the review still cost ~95k per agent.

Estimate from the corpus an agent must hold, not from the size of its deliverable or the name of its
role. On current evidence, add 60–150% to any band where the unit reads widely before it reasons.

Nothing here yet covers: implementation units, migrations, worktree-isolated writers, or any run using
`haiku`. Those still fall back to the `contracts.md` bands, and the bands are unproven there — say so
in the plan rather than implying the number has evidence behind it.
