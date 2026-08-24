# Orchestration topologies

Pick the smallest pattern that fits the task, then compose patterns for larger work. Every pattern uses the contracts in `dispatch.md` and dispatches through `harness.md`.

## 1. Research / review sweep (fan-out, map–reduce)

**When:** a broad question answerable from many independent angles — codebase audit, doc or literature research, multi-dimension review.
**Flow:** decompose into 4–8 *non-overlapping* angles (by subsystem, by lens, by source type — never "agent 1 and agent 2 both research X"). Launch one batch, readers only, background. Parent synthesizes; conflicting claims go to verification, not a coin flip.
**Rules:** each brief names what the *other* agents cover so nobody duplicates; reports carry citations and file refs; the parent never pastes a full report onward — synthesize and drop. Disjoint mandates produce disjoint find-sets (`../SKILL.md` Step 5, calibration: established) — so cutting an *angle* to save budget loses the findings only that angle sees, while cutting a second agent off the *same* angle costs nothing.

## 2. Implement → review → fix (single increment)

**When:** one bounded implementation unit at medium or higher risk.
**Flow:** (optional ≤2 explorers for real unknowns) → one writer under lease (the `implementer` agent when delegated — it preloads `clean-code`; or the parent inline) → deterministic checks → freeze → 1–2 lens reviewers on the frozen diff (`diff-review`'s Spec and Standards axes where that skill is installed — see Rules; otherwise lenses drawn from the risk, e.g. behavioural correctness against integration and lifecycle) → parent triage → the original writer fixes accepted findings → targeted verification → re-freeze → follow-up rounds scoped to blocker and major only, until one comes back dry.
**Rules:** reviewers get the same brief and diff, cannot see each other, and may return "no findings". Spec compliance and quality are separate verdicts — and where `diff-review` is installed, its Spec and Standards reader briefs are those two reviewers' briefs, verbatim, entered as two plan rows — **and the Standards row carries that skill's smell baseline verbatim too**, because nothing else on this path hands its reader the list; the parent aggregates, `diff-review` does not. One full review round plus one targeted fix-verification round is where it starts, then follow-up rounds scoped to blocker and major only until a **dry round** — a condition, not a count (#5 below holds that machinery).

## 3. Migration / repo-wide transform (pipeline)

**When:** the same change across many sites — API migration, framework upgrade, mass rename with judgment.
**Flow:** a discovery agent produces the complete work-list (the parent spot-checks completeness — a missed site is silent scope loss) → pipeline each unit through transform → verify, concurrency-capped; parallel writers only via per-unit worktrees, with one integration owner merging in a defined order → compose check over the whole.
**Rules:** per-item pipeline, not waves — unit 12 gets verified while unit 40 transforms. Log every skipped or failed unit in the ledger.

## 4. Bake-off / judge panel

**When:** a wide solution space with a high cost of picking wrong — architecture, algorithm, API design.
**Flow:** N=2–3 independent attempts from *different declared angles* (simplest-possible, performance-first, compatibility-first) in isolated workspaces → independent judges score against written criteria → parent synthesizes from the winner, grafting runner-up ideas.
**Rules:** attempts never see each other; judges see all attempts but not authorship framing; criteria are written before results return. Read for convergence before scoring: entrants from opposite declared angles reaching the same root cause is stronger evidence than any one agent's assertion, and a losing arm — forbidden the winners' move by its own angle — can convert their shared inference into a measured fact. A bake-off's value is often the agreement, not the winner (calibration: established). Judges reach family diversity only when `verifier-alt` is in your live agent list. See `harness.md`, "The alt lane".

## 5. Loop-until-dry (unknown-size discovery)

**When:** finding *all* of something — bugs, dead code, inconsistencies — where a fixed agent count under-covers the tail.
**Flow:** rounds of small finder batches with distinct angles; dedupe new findings against **everything seen**, not just what was confirmed, or rejected findings resurface forever; stop after 2 consecutive dry rounds or at budget.
**Rules:** the budget rail applies (`../SKILL.md`); the record says "dry after N rounds", never "found everything".
**Not governed by the stop rule's round bound.** That bound covers re-reviewing one artifact. This is discovery over an unknown-size space and it terminates on dry rounds — a fixed count here is just an undercount of the tail.

## 6. Adversarial verification

**When:** high-stakes claims — security findings, root-cause diagnoses, "this is safe to delete".
**Flow:** per claim, 2–3 independent agents briefed to **refute** it ("default to refuted if uncertain"), or given distinct lenses (correctness / security / does-it-reproduce) where it can fail in different ways. Majority refutation kills the claim; survivors get acted on.
**Rules:** verifiers never see the finder's reasoning, only the claim and its evidence pointers. Verifiers reach family diversity only when `verifier-alt` is in your live agent list. See `harness.md`, "The alt lane".

## 7. Quarantined deep read (context protection)

**When:** something huge must be digested — a vendor SDK, a log dump, a legacy module — but only the conclusions matter.
**Flow:** one reader agent per corpus chunk; each returns a 1–2k-token distillation (facts, file:line pointers, gotchas) to a file; the parent reads distillations only.
**Rules:** this is the purest use of subagents-as-context-control; resist "just reading it myself" for anything that would eat more than 20–30% of your context.

## 8. Competing hypotheses (peer debate)

**When:** debugging or analysis where anchoring is the enemy — the first plausible theory tends to win regardless of truth.
**Flow:** one agent per hypothesis, each briefed to prove its own *and actively disprove the others'* from evidence. The parent adjudicates on evidence quality.
**Rules:** hierarchical subagents approximate this. True peer-to-peer agent teams are the native fit at meaningfully higher token cost, but they are an env-var opt-in set outside a running session, so that route is the user's standing configuration, not one sage can take mid-run (`harness.md`).

## 9. Completeness critic (final pass)

**When:** the end of any large orchestration.
**Flow:** one fresh agent asks only what is missing — an angle not swept, a claim unverified, a criterion without evidence, a file outside the diff scope. Its findings become quick follow-ups or explicit `Gaps:` lines in the ledger's run record.
**Rules:** the critic is cheap (fast or standard tier); it audits coverage, it does not redo the work.

## 10. Blind acceptance suite (the independent test designer)

**When:** the plan carries a writer unit *and* checkable criteria can be extracted without inventing behaviour (one strong criterion qualifies).
**Decide light / full / none yourself, and record the choice, its deciding signal, and the criteria text verbatim in the ledger's Plan section.** `full` needs a session that can build and run tests — where it cannot, `full` is unavailable, not merely unattractive. Four signals move the choice, and this is the only place the procedure lives — `../SKILL.md` Step 2 carries the trigger and points here, `dispatch.md`'s rubric supplies one input. The signals: a risk-rubric **hard trigger** (`dispatch.md`), which argues for a suite except for "behavior with no reliable test oracle", the one trigger that argues for `none` and routes verification to `Awaiting human` instead; repo **coverage** that already spans the criteria, arguing down; a **diff that fits one sentence**, arguing down; and criteria that would **flake as asserts**, arguing `full` → `light`. Precedence when they conflict: a hard trigger outranks existing coverage, which outranks the one-sentence-diff signal; flake-prone criteria only choose between `light` and `full` and never argue for `none`. No writer unit, or nothing checkable extractable, or no dispatched writer to author blind against → `none`, in one ledger line saying which. **A close call gets an assumption-log row**, since this is exactly the resolution a human would otherwise have made.
**Artifact:** one scratch file of numbered cases — written cases, not test code. Each carries an ID, the criterion it traces to, steps, the expected *observable* outcome, and a check method tagged **machine-verifiable / agent-observable-but-subjective / human-only** (the evidence-menu taxonomy below).
**Flow — light:** one small standard-tier unit authors the suite in parallel with the implementer, from the requirement text and the criteria only — never the plan's design, the source, or a diff (firewall: `../SKILL.md` Step 3). It writes one scratch file and touches no tree, so parallel is safe by construction. Then: parent traceability scan (an uncited case is an invented expectation) → verifier checklist → diff-reviewer coverage lens.
**Flow — full:** after freeze, one compile unit turns each machine-verifiable case into a runnable test from the as-built interface — signatures only, never the diff, never a run against the candidate → red-check all against the baseline (every one must fail there; one that passes is vacuous, flag it) → run in the existing verification stage.
**Rules:** an ambiguity the author cannot resolve returns as a **question**, never as a case. The implementer sees criteria, never the suite. Verdicts are pass / fail / `Awaiting human`; human-only cases route to the human checkpoint. A failing case is a finding, not a verdict — triage decides (defect / case overreach / user decision). A case the toolchain cannot express downgrades to agent-observable, recorded, never dropped. Fix leases exclude test paths, and at fix time the implementer gets the failed criterion and the observed behaviour, not the case text. **No new stage.**

## 11. Pre-write plan critic

**When:** high risk, or any change that alters a rule every future run reads — a skill corpus, a shared template, a convention file. Optional; the risk rubric's High row (`dispatch.md`) names it.
**Flow:** before any writer starts, one fresh agent reads the drafted plan or design sketch and is briefed to **refute its central justification**, not to improve it. Findings land before implementation, so a refuted design costs a re-plan rather than a rewrite.
**Rules:** the critic sees the plan and the evidence it cites, never the parent's reasoning behind it; standard or frontier tier; distinct from the completeness critic (#9), which audits coverage at the *end* — this one attacks the design at the *start*. One logged run: a critic spent before a line was written refuted the design's central claim, because the sketch had derived a rule from a false premise about how a harness call behaves, and the unit re-planned instead of rewriting (calibration: provisional).

## 12. Blind behavioural lens (two arms)

**When:** a change to behaviour-shaping text in this ecosystem's own corpus — a skill file, a shared template, a convention file — where the question is what the text *makes a fresh actor do*, not whether a reader agrees with it. Reviewers rule on text; only an actor reveals what the text makes people do. **The trigger is what the change does, never which skill is making it.** `/sage-promote` reaches it through its `## The write machinery`; a run editing this corpus on the user's word reaches it through `../SKILL.md` Step 5. Both paths are real and the run log carries rows of each — a trigger scoped to the promotion skill alone would not have fired on the edits that created this pattern, which a run took on the user's word.
**Flow:** one agent is told to **perform** a written procedure on a sandbox copy — never to read or critique it — and is told nothing of the defect history or the author's intent. Two arms: the **control arm** against the pre-change text, taken from the frozen pre-edit corpus so the baseline is what actually shipped, and the **change arm** against the edit. Run the control first.
**The one verdict a single sample settles is the stop.** A control arm that does not exhibit the failure means there is nothing to fix: stop, and do not author the guidance. That direction needs one observation, because watching the failure happen is positive evidence.
**Rules:** the reverse does not hold at one sample, and inverting it is the trap this pattern exists to flag. Two arms that *agree* at one sample each may agree by noise, so "adopt only if the arms differ" converts noise into a revert of a good edit. A null verdict needs the repeat count the source apparatus uses — five or more per variant, every flagged match read by hand, variance treated as a result — not two dispatches. **Never revert an edit on agreement at a single sample**; record the arms as a weak signal and say which kind of figure you are holding. The lens measures a mechanic only if it performs the action the trigger names — `../SKILL.md` Step 5 owns that rule and is its one home. Price it off the upper half of the blind-behavioural band, the half where the brief names protocol sections the actor must hold, never off the sandbox-fixture half: a corpus-facing lens priced from the task's length instead of from the corpus it holds has run several times over its estimate.
**Only one direction of this pattern is affordable at a run's budget, and saying so is part of it.** The stop is one dispatch and it is decisive. The adopt-or-null direction needs the source apparatus's repeat count on *both* arms at the same band, which no run here has ever budgeted — so plan it deliberately as its own programme, never as something a corpus edit picks up in passing. Two mechanics the pattern would be unrunnable without: materialise the control arm's text with `git show HEAD:<path>` into a scratch copy, so the baseline is what actually shipped rather than what the author remembers shipping; and where the control *does* show the failure and the two arms then agree at one sample each, that is **not** a null result — it is an unresolved question, and it is recorded as one rather than read as a licence to adopt or to revert.

**What it buys over the degradation gate is narrow, and saying so is part of the pattern.** That gate already compares a pre-edit and a post-edit corpus with an adversarial default, and the machinery around it catches the commonest null cases on its own — a citation already standing makes an edit a band-tag update and nothing more, and the one-home check catches a second home. But all four of the gate's targets are degradations, and the whole-corpus checks beside it do not test behaviour at all. An edit whose post-edit corpus behaves exactly like the pre-edit one is not worse, adds no second home, loses no floor item, and changes nothing wider than claimed: it passes cleanly and lands. Null-effect detection on that residue is the whole of what this pattern adds (calibration: provisional).

# Evidence menus by domain

"Done" requires evidence appropriate to the domain, not just green reviewers.

**Software (default):** compile, lint, typecheck; focused then full tests; a runnable reproduction per bug fix; a regression test per accepted finding; a perf measurement wherever a budget exists; a diff-scope check. For implementation work, add a requirement-level acceptance suite authored blind to the plan and the code (pattern 10), with its compiled subset red-checked against the baseline and run at verification.

**Every domain, before work starts:** mark each acceptance criterion **machine-verifiable / agent-observable-but-subjective / human-only**. A unit can be technically complete while explicitly awaiting a human judgment — record that as `Awaiting human`, which is a surfaced event, and never let a reviewer's silence stand in for it. Domain menus beyond these belong in a project-level reference.

**Research / writing:** every load-bearing claim carries a source fetched this run (marked fetched against snippet); conflicting sources surfaced, never averaged; recency checked against today's date; a completeness critic pass before delivery.

**Data / analysis:** input row and coverage counts stated; transformations spot-checked against raw records; numbers that will be quoted re-derived once independently; charts checked against the underlying table.
