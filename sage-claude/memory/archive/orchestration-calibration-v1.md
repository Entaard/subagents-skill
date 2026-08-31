# Orchestration calibration archive

Historical cost bands and run rows preserved from the retired orchestration package. This file is
provenance only; active Sage runs use `memory/local/`.

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

- Price review and verify as a pair: the fix-verification round has never come back empty, and four
  times cost more than the review itself — a fresh or full-mandate continuation re-reads the whole
  corpus, so retained context makes the round cheaper to brief, not to run. Machine-independent.
  (×8, established, 2026-08-05 → 2026-08-16, author's log; **promoted 2026-08-15** —
  `references/contracts.md`, estimating note.)
- Estimate from the corpus a unit must hold and the lenses it must apply — never from the size of
  the deliverable or the name of the role. Add 60–150% where the unit reads widely before it
  reasons. This governs blind acceptance-suite authors too: two runs missed high, by 1.6× and 1.7×,
  pricing the author from the requirement's length instead of from the corpus its brief named.
  Machine-independent. (×7, established, 2026-08-04 → 2026-08-16, seed + author's log; **promoted
  2026-08-15** — `references/contracts.md`, estimating note.)
- Steer the same verifier thread for a narrow re-verdict on named fixes; do not respawn. 11–20k
  steered against 78–112k fresh, a ~4–7× discount — so the pair rule above prices a full verify
  round, not a steered follow-up. Caveat: a completed agent's transcript may be unresumable, so plan
  the steer before the agent reports. Machine-independent. (×4, recurring, 2026-08-07 → 2026-08-16,
  author's log; **promoted 2026-08-15** as a clause of the pair rule — `references/contracts.md`.)
- Price a run off a same-shape logged row before reaching for band arithmetic — same unit topology,
  same corpus kind. Three consecutive runs priced this way landed within ±6% of their core estimate,
  after a stretch of band-priced overruns. Machine-independent. (×3, recurring, 2026-08-15 →
  2026-08-16, author's log; **promoted 2026-08-16** — `references/contracts.md`, estimating note,
  and SKILL.md Step 2.)
- A claim checklist prices a review lens at its band's floor only when every item settles in one
  look; an item quantified over the corpus costs an open mandate — price a lens by its widest
  question. Machine-independent. (×3, recurring, 2026-08-11 → 2026-08-12, author's log; **promoted
  2026-08-15** — `references/contracts.md`, estimating note.)
- Build the measurement harness before the gate: reproduce the central claims yourself, then brief
  every unit against named numbers with one shared harness. A gate question with a number in it is
  answerable; one without is a guess. Mandate the one shared harness where several units report the
  same metric — absolute numbers were not comparable across agents. Machine-independent. (×3,
  recurring, 2026-08-08 → 2026-08-16, author's log; **promoted 2026-08-16** — SKILL.md Step 2.)
- Bands over-estimate too: a single lens over a corpus it need not cross-check against a second
  document runs below band. Machine-independent. (×1, provisional, 2026-08-05, seed.)

### Step 3, briefing

- Name a brief's ground truth outright — exact files, line numbers, URLs, measured baselines, and
  the harness to measure with. ~2–2.5× cheaper than an open-ended brief and fewer failures, across
  fetching, code, and prose; brief style, not task class, sets the cost. Machine-independent. (×5,
  recurring, 2026-08-05 → 2026-08-12, seed + author's log; **promoted 2026-08-15** — SKILL.md Step 3
  and the task-brief template. Supersedes the narrower "name a web brief's target URLs", ×1 seed.)
- Grep the claim before you brief it — and before you assert it. Cite only what the named artifact
  contains; a pointer into a transcript the agent cannot read is a briefing error. The rule covers
  **completion claims**, not only briefs: one run asserted a precedent about a sibling skill without
  grepping it, and the file said the opposite. Machine-independent. (×4, recurring, 2026-08-07 →
  2026-08-16, author's log; **promoted 2026-08-15** — SKILL.md Step 3.)
- A unit's toolset comes from its agent file, not from its self-report — and a brief that points a
  unit at a skill must name a `Read`-able path unless that unit's `tools:` includes `Skill`. One
  lens downgraded its own confidence over tools its file grants; measured later, an `implementer`
  (no `Skill`) could reach guidance only through a readable path, while a subject that had `Skill`
  auto-invoked it. Machine-independent. (×3, recurring, 2026-08-11 → 2026-08-16, author's log;
  **promoted 2026-08-16** — SKILL.md Step 3 and `references/claude-code.md`.)
- Verify a reader's or researcher's structural claims by running them before building on them. One
  reader fabricated a data structure that does not exist; three recon claims in one run were wrong;
  a web researcher's headline version-attribution finding was wrong, and applying it would have
  introduced the defect it claimed to fix. Fetch the primary source locally and grep it yourself — a
  summarising fetch tool is a lead generator, not ground truth. Machine-independent. (×3, recurring,
  2026-08-06 → 2026-08-16, seed + author's log; **promoted 2026-08-16** — SKILL.md Step 3.)

### Step 4, execution

- Isolation discipline covers every mutating unit and the parent itself: worktrees for
  mutation-probing reviewers, a sandbox `HOME` for an installer-execution verifier for the same
  reason, prove the worktree recipe before launch, prune changed worktrees each wave, snapshot the
  parent's own tree, commit explicit paths while agents run, never edit a tree a measuring agent is
  reading. Machine-independent. (×7, established, 2026-08-06 → 2026-08-16, author's log; **promoted
  2026-08-15** — SKILL.md Step 4.)

### Step 5, verification

- Point an adversarial pass at the parent's own fixes, claims, and recommendations — the fix round
  is where unsourced confidence enters, and the refuter aimed there has paid on every dispatch, in
  ten consecutive runs. The mechanism: a fix closing one finding can silently un-pass a criterion
  already verified, because the diff readers ruled on a pre-fix freeze and the refuter is the only
  unit standing after it. Qualifier — the streak broke on 2026-08-16 in the other direction, when a
  researcher's headline finding was wrong and the parent caught it, so a refuter's "no defect found"
  on domain correctness is weak evidence. Machine-independent. (×10, established, 2026-08-06 →
  2026-08-16, seed + author's log; **promoted 2026-08-15** — SKILL.md Step 5.)
- Disjoint mandates produce disjoint find-sets — that is the coordination check paying, and it is
  the argument against cutting a lens for budget. Every multi-lens run since 2026-08-12 reported
  zero duplicate findings across its lenses; in three of them the decisive finding was invisible to
  every other unit. Machine-independent. (×6, established, 2026-08-12 → 2026-08-16, author's log;
  **promoted 2026-08-16** — SKILL.md Step 5 and `references/patterns.md` #1.)
- Units that independently construct the same specific finding by different routes are strong
  evidence for it; agreement that nothing is wrong proves nothing. Machine-independent. (×6
  instances across 5 runs, established, 2026-08-07 → 2026-08-16, author's log; **promoted
  2026-08-15** — SKILL.md Step 5 and `references/patterns.md` #4.)
- When the deliverable includes a file the installer treats specially, add an execute-the-installer
  check — snapshot, run, byte-compare, in sandbox `HOME`s; a reviewer reading the diff cannot see
  it. Every dispatch has measured something no diff reader could: a managed directory's deletion
  scope, a `.bak` clobbered on the second install, and a guard testing `[ -f ]` on a path that can
  be a directory, which then aborts the whole sync. Machine-independent. (×6, established,
  2026-08-05 → 2026-08-16, seed + author's log; **promoted 2026-08-15** — SKILL.md Step 5.)
- Red-check a blind acceptance suite at baseline before believing it: write the test, prove it fails
  on the old code, then trust it. Machine-independent. (×5, recurring, 2026-08-07 → 2026-08-16,
  author's log; **promoted 2026-08-15** — already carried by `references/patterns.md` #10 and
  SKILL.md Step 5.)
- Settle a disagreement with a command, not by model tier and not by majority. The standard-tier
  checker has been right against the frontier one; and where reviewers agreed a mechanism claim was
  inconsistent but none of them could see the runtime, the consensus repair direction was factually
  backwards — one small docs unit changed the fix. Routing a suspected sibling defect to a unit that
  measures did the same. Machine-independent. (×4, recurring, 2026-08-06 → 2026-08-16, seed +
  author's log; **promoted 2026-08-16** — SKILL.md Step 5.)
- A criterion can pass literally while the mechanic it describes is broken — only behavioural
  measurement catches that failure mode, and a behavioural test measures the mechanic only if it
  performs the action the trigger names: a subject briefed planning-only, against a trigger
  conditioned on making a change, proved nothing and cost 16.7k. Machine-independent. (×3,
  recurring, 2026-08-07 → 2026-08-16, author's log; **promoted 2026-08-16** — SKILL.md Step 5.)
- When the target is a range, never optimise or report a mean: chase the internal range, report
  minimums, and never re-check an aesthetic finding with the metric that misled you.
  Machine-independent. (×3, recurring, 2026-08-07, author's log; **promoted 2026-08-15** — SKILL.md
  Step 5.)
- Budget one verification step for a standard-tier checker's counts: it overcounted once and a
  single grep settled it. Machine-independent. (×1, provisional, 2026-08-05, seed.)

## Watch list

Lessons seen once, not yet rules:

- **A subagent's transcript is observable.** Each dispatch returns an `output_file` holding that
  unit's full JSONL, so grepping it measures what the agent actually invoked rather than what it
  reported. Never conclude a subagent is unobservable without checking the `output_file` the dispatch
  already handed you — one run converted six case verdicts from judged to measured that way
  (2026-08-16). Carried as a harness fact in `references/claude-code.md`, Spawning.
- A projection built from **band midpoints is an upper bound**, not a forecast — say which you are
  holding up when you stop at the overrun rail, or the user authorises headroom the run never needs
  (2026-08-16). Carried in SKILL.md's mid-run rails.

Closed defect in this skill, kept for its evidence:

- The ~25% overrun rail used to be sampled **between dispatches**, so it missed in both directions.
  Four runs overran on their final agent with nothing left to launch, leaving the rail able only to
  report (2026-08-12 ×2, 2026-08-13, 2026-08-16); once it fired early on a band-midpoint projection
  and the actual then landed under the printed ceiling (2026-08-16). **Closed 2026-08-18** by moving
  the sampling point rather than disclosing it again: a dispatch hands back a symlink to its unit's
  live transcript at launch, so per-unit spend is now read while the unit runs, and the rail gained a
  per-unit scope (4× the row's own estimate, floor 150k) whose lever — steer the unit, launch nothing
  more against that row, surface — still exists when nothing is left to dispatch. SKILL.md's mid-run
  rails carry the rule; `references/claude-code.md`, "Reading a running unit's spend", carries the
  mechanism and its measurements. The rows above are the evidence that motivated it, and the two
  disclosure sentences that preceded it are gone.
- Watch what the new sensor is worth: record, on the next few runs, whether the per-unit rail fired
  on anything the old between-dispatch check would have missed, and whether the measured actuals
  changed the estimate-vs-actual gap. A sensor that never fires is a cost, not a rail.

Uncovered classes:

- Implementation units that write real code, migrations, worktree-isolated writers, any substantial
  `haiku` run. Those fall back to the `contracts.md` bands, which are unproven there — say so in the
  plan rather than implying the number has evidence.
- **Scripted `Workflow` fan-outs since v2.1.229**, whose same-prefix stagger changes what a scripted
  wave costs against the same rows hand-batched. Every logged `Workflow` row predates it, so a
  `Backend:` line drawn from one is estimating on stale ground — say so at the gate.

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
