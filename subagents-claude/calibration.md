# Calibration log

What orchestration runs on this machine actually cost, against what was estimated — and what they
taught.

Read this at **Step 2**, before writing a budget: where a row covers the task class in hand, its
actuals beat the coarse bands in `contracts.md`. Append one row at **Step 6**, every run — including
the runs where the estimate held. A band you can trust needs its hits recorded next to its misses.

The `note` column is for **lessons, not only costs**: a coordination check that came back negative, a
failure-ladder stall and what unstuck it, a gate call worth reversing. Write each one so Step 2 can act
on it. "Fetch-heavy research runs 70–120k per agent" is usable at plan time; "unit 3 was expensive" is
not.

This file is yours, not the skill's — `install.sh` seeds it once and never overwrites it. Rows marked
**(seed)** shipped with the skill: real runs, but from the author's machine, not this one. Untagged rows
are local actuals and outrank them. Past ~40 rows, propose folding the oldest into the summary below and
let the user approve the fold; that is the one sanctioned rewrite of this file.

| date | task class | agents | est | actual | wall clock | note |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-08-04 | web research sweep, agents fetching primary sources **(seed)** | 5 | 225k | 451k | ~25 min | **Fetch-heavy web research runs 70–120k per agent, not the 15–40k exploration band.** Off by 2–3×. |
| 2026-08-04 | completeness critic over ~25k words of notes + 4 skill files **(seed)** | 1 | 35k | 172k | ~10 min | **A critic's cost tracks the corpus it must read, not the number of drafts it reviews.** Off by 5×. Estimate from input size. |
| 2026-08-05 | 2 reviewers on a small prose diff, against a written spec **(seed)** | 2 | 120k | 193k | ~7 min | Off by 1.6× — and the diff was *small*. Reviewers still had to hold the whole 6.6k-word skill plus a 2.8k-word spec. **Review cost tracks the corpus the reviewer must hold, not the size of the change.** |
| 2026-08-05 | prose review of a ~8.5k-word skill corpus: blank-context critique + adversarial refutation of a draft, opus verifiers **(seed)** | 2 | 240k | 137k | ~4 + ~10 min | **First two-sided datum: 47k and 89k per agent, half the ~95k/agent row above.** For ≤10k-word doc corpora, estimate 50–95k per frontier verifier. Refuter killed 6 of 51 draft claims — the fan-out paid. |
| 2026-08-05 | docs fact-check via a docs-guide agent, 5 questions, fetch-heavy **(seed)** | 1 | 90k | 127k | ~4.5 min | Top of the 70–120k fetch band (25 tool uses). Band holds; plan at its top for multi-question briefs. |
| 2026-08-05 | no-op boot probes, haiku **(seed)** | 2 | 15k | 21k | <1 min | **Dispatch floor: explorer 4,962; general-purpose 16,036.** A `tools:` allow-list boots ~3× cheaper. Absolute numbers are machine-specific (they include local CLAUDE.md files); the ~3× ratio is the durable fact. |
| 2026-08-05 | implement a 45-item review across 8 skill files: 1 inline writer + 2 verifiers (opus compliance lens, sonnet consistency lens) over a frozen set **(seed)** | 2 | 140–200k | 161k (68k + 93k) | ~5 min, parallel | **Estimate held — first hit on the review band.** 80k/agent average against a 70–100k plan, so the 50–95k-per-frontier-verifier figure for ≤10k-word corpora is now confirmed twice: use it, not the coarse band. Coordination check: **paid, but partially.** The two lenses returned disjoint findings (a missed compression vs. a re-duplicated rule) and neither found the other's, so the second lens was not redundant. But the run's worst defect — `install.sh` excludes `calibration.md` from its sync, so structural edits to it never reach an already-installed copy — surfaced only from *running* the installer, not from either review. **Lesson: when the deliverable includes a file the installer treats specially, add an execute-the-installer check; a reviewer reading the diff cannot see it.** Also: the sonnet checker (the maker/checker diversity fallback) overcounted a duplication finding, 4 places against the real 3. One grep settled it, but budget a verification step for it. |
| 2026-08-06 | review + optimise this skill: 2 web researchers + 1 docs fact-check + 1 blind critic, then 2 verifiers on the frozen diff **(seed)** | 6 | 470k | 401k | ~35 min | **Brief style, not task class, sets web-research cost.** The two researchers were given their target URLs outright and came back at 13.7k and 33.7k — against a 70–120k "fetch-heavy" band drawn from open-ended briefs. That band is only valid for briefs that must *find* their sources. The blind critic (77k vs 80k) and the docs fact-check (111k vs 100k) both landed. **Coordination check: strongly positive, and the adversarial row was the whole margin.** A sonnet refuter dispatched against opus-authored prose refuted 4 claims, three of them defects introduced during the fix round — including a replacement cost figure that laundered a two-hop derivation into confident prose, and a wall-clock rail invented to close a reviewer's finding. The two verifiers also *disagreed*: one certified a deletion as safe that the other disproved with one grep. **Lesson: run the maker/checker diversity pass on your own edits, not only on the artifact you were given — and settle reviewer disagreements with a command, not by preferring the more senior model.** |

## How to read this

The bands **under-estimate whenever an agent must ingest a large body of material before reasoning over
it.** Web fetches, long document corpora, and a small diff that still requires reading a whole document
set all trip it. Row 3 is the sharpest version — the *change* under review was tiny and the review still
cost ~95k per agent.

**But "fetch-heavy" is not one band.** Row 8 splits it: a web-research brief that names its target URLs
costs a fraction of one that must discover them. Quote the band that matches the brief you are actually
about to write, and prefer naming the URLs — it is the cheapest single lever in this file.

They can **over-**estimate too, so this is no longer a one-directional log. Row 4 came in at half the
review band, and row 7 then landed inside a band drawn from row 4. The driver is not "review is
expensive."

Estimate from two things: the corpus an agent must hold, and the number of lenses it must apply to it.
Not the size of the deliverable, and not the name of the role. Add 60–150% to any band where the unit
reads widely before it reasons. Subtract where a single lens reads a corpus it does not have to
cross-check against a second document.

Still uncovered: implementation units that write real code, migrations, worktree-isolated writers, and
any substantial run on `haiku` (row 6 is a no-op probe, not work). Those fall back to the `contracts.md`
bands, which are unproven there — say so in the plan rather than implying the number has evidence.
