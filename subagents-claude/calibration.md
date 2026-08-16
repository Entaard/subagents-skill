# Calibration log

What orchestration runs on this machine actually cost, against what was estimated — and what they
taught.

The contract:

- **Step 2** reads this file before writing a budget. Where a Bands line or a Run-log row covers
  the task class in hand, its figure beats the coarse bands in `references/contracts.md` — cite it
  in the plan.
- **Step 6** appends one row to the Run log at the end of this file — every run, including the runs
  where the estimate held. A band you can trust needs its hits recorded next to its misses. The
  `note` column is for lessons, not only costs: write each one so Step 2 can act on it.
  "Fetch-heavy research runs 70–120k per agent" is usable at plan time; "unit 3 was expensive" is not.
- **Consolidation is the user's act.** When a trigger holds — this file past ~10k tokens, 40+ rows,
  a lesson at three confirmations, two rows disagreeing on one band, structural damage, stale
  version-bound claims (this list mirrors the canonical one in the `agents-self-reflect` skill) —
  Step 6 prints `Consolidation due: <reason>`, and the user runs `/agents-self-reflect`. That pass
  rewrites this file into this shape and moves rows out of the log, verbatim (retired or
  compressed), into `calibration-archive.md` beside it — a file that first exists when that pass
  first runs (absent until then), never read at Step 2, greppable for provenance.
- Rows marked **(seed)** shipped with the skill: real runs, but from the author's machine, not this
  one. Untagged rows are local actuals and outrank them. This file is yours, not the skill's —
  the source repo's `install.sh` (not in this installed directory) seeds it once and never
  overwrites it.

## Bands: quote these at Step 2

Cost figures are machine-specific by nature — the seed figures below came from the author's
machine. The part of a band that travels (a ratio, a shape) is named in its Qualifiers.

| Class | Figure | Qualifiers | Evidence |
| --- | --- | --- | --- |
| Frontier review lens, prose corpus ≤10k words | 50–95k per agent | cost tracks the corpus the reviewer must hold, not the size of the change; blank-context critique lands in the same band | 3 runs, last 2026-08-06 (seed) |
| Web research, brief must find its sources | 70–120k per agent | multi-question briefs sit at the top; only valid for briefs that must discover their sources | 3 runs, last 2026-08-06 (seed) |
| Web research, brief names its target URLs | 14–34k per agent | the fetch-heavy band above does not apply | 1 run (2 agents), 2026-08-06 (seed) |
| Completeness critic over a large corpus | ~170k over ~25k words | cost tracks the corpus ingested, not the number of drafts reviewed | 1 run, 2026-08-04 (seed) |
| Dispatch floor | scoped agent ~5k; general-purpose ~16k | absolute numbers are machine-specific; the ~3× ratio is the durable fact | 1 run, 2026-08-05 (seed) |

## Rules: read once at Step 2, apply at the step named

### Step 2, estimating

- Estimate from the corpus a unit must hold and the lenses it must apply — never from the size of
  the deliverable or the name of the role. Add 60–150% where the unit reads widely before it
  reasons. Machine-independent. (×5, 2026-08-04 → 2026-08-07, seed + author's log; **promoted
  2026-08-15** — `references/contracts.md`, estimating note.)
- Price review and verify as a pair: the fix-verification round has never come back empty, and four
  times cost more than the review itself — a fresh or full-mandate continuation re-reads the whole
  corpus, so retained context makes the round cheaper to brief, not to run. Measured exception:
  steering the same verifier thread for a narrow re-verdict on named fixes ran ~5× cheaper than a
  fresh dispatch. Machine-independent. (×6, 2026-08-05 → 2026-08-15, author's log; **promoted
  2026-08-15** — `references/contracts.md`, estimating note.)
- A claim checklist prices a review lens at its band's floor only when every item settles in one
  look; an item quantified over the corpus costs an open mandate — price a lens by its widest
  question. Machine-independent. (×3, 2026-08-11 → 2026-08-12, author's log; **promoted
  2026-08-15** — `references/contracts.md`, estimating note.)
- Bands over-estimate too: a single lens over a corpus it need not cross-check against a second
  document runs below band. Machine-independent. (×1, 2026-08-05, seed.)

### Step 3, briefing

- Name a brief's ground truth outright — exact files, line numbers, URLs, measured baselines, and
  the harness to measure with. ~2–2.5× cheaper than an open-ended brief and fewer failures, across
  fetching, code, and prose; brief style, not task class, sets the cost. Machine-independent. (×5,
  2026-08-05 → 2026-08-12, seed + author's log; **promoted 2026-08-15** — SKILL.md Step 3 and the
  task-brief template. Supersedes the narrower "name a web brief's target URLs", ×1 seed.)
- Grep the claim before you brief it, and cite only what the named artifact contains — a pointer
  into a transcript the agent cannot read is a briefing error. Machine-independent. (×3,
  2026-08-07 → 2026-08-12, author's log; **promoted 2026-08-15** — SKILL.md Step 3.)

### Step 4, execution

- Isolation discipline covers every mutating unit and the parent itself: worktrees for
  mutation-probing reviewers, prove the worktree recipe before launch, prune changed worktrees each
  wave, snapshot the parent's own tree, commit explicit paths while agents run. Machine-independent.
  (×5, 2026-08-06 → 2026-08-08, author's log; **promoted 2026-08-15** — SKILL.md Step 4.)

### Step 5, verification

- Point an adversarial pass at the parent's own fixes, claims, and recommendations — the fix round
  is where unsourced confidence enters, and the refuter aimed there has paid on every dispatch.
  Machine-independent. (×7, 2026-08-06 → 2026-08-15, seed + author's log; **promoted 2026-08-15** —
  SKILL.md Step 5.)
- Units that independently construct the same specific finding by different routes are strong
  evidence for it; agreement that nothing is wrong proves nothing. Machine-independent. (×5
  instances, 2026-08-07 → 2026-08-13, author's log; **promoted 2026-08-15** — SKILL.md Step 5 and
  `references/patterns.md` #4.)
- Red-check a blind acceptance suite at baseline before believing it: write the test, prove it
  fails on the old code, then trust it. Machine-independent. (×4, 2026-08-07 → 2026-08-08, author's
  log; **promoted 2026-08-15** — already carried by `references/patterns.md` #10 and SKILL.md
  Step 5.)
- When the deliverable includes a file the installer treats specially, add an execute-the-installer
  check — snapshot, run, byte-compare; a reviewer reading the diff cannot see it.
  Machine-independent. (×3, 2026-08-05 → 2026-08-15, seed + author's log; **promoted 2026-08-15** —
  SKILL.md Step 5.)
- When the target is a range, never optimise or report a mean: chase the internal range, report
  minimums, and never re-check an aesthetic finding with the metric that misled you.
  Machine-independent. (×3, 2026-08-07, author's log; **promoted 2026-08-15** — SKILL.md Step 5.)
- Settle reviewer disagreements with a command, not by preferring the more senior model — the
  standard-tier checker has been right against the frontier one. Machine-independent. (×2,
  2026-08-06 → 2026-08-07, seed + author's log.)
- Budget one verification step for a standard-tier checker's counts: it overcounted once and a
  single grep settled it. Machine-independent. (×1, 2026-08-05, seed.)

## Watch list

- Uncovered classes: implementation units that write real code, migrations, worktree-isolated
  writers, any substantial `haiku` run. Those fall back to the `contracts.md` bands, which are
  unproven there — say so in the plan rather than implying the number has evidence.

## Run log (append new rows here)

Recent rows stay in full. The seed rows below also stay in full on purpose: they are the provenance
for the Bands and Rules above, until this machine's first consolidation pass — which may then
compress them to one line with an archive pointer. If a full row and the Bands or Rules ever
disagree, the Bands and Rules are the consolidated reading — treat the mismatch as structural
damage, a consolidation trigger.

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
