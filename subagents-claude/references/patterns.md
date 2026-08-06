# Orchestration patterns

Pick the smallest pattern that fits; compose them for larger work. Every pattern uses the contracts in `contracts.md`.

## 1. Research / review sweep (fan-out, map–reduce)

**When:** broad question answerable from many independent angles — codebase audit, literature/doc research, multi-dimension code review.
**Flow:** decompose into 4–8 *non-overlapping* angles (by subsystem, by lens, by source type — never "agent 1 and agent 2 both research X"). Launch one batch, readers only, background. Parent synthesizes; conflicting claims go to verification, not a coin flip.
**Rules:** each brief names what the *other* agents cover so nobody duplicates; reports carry citations/file refs; parent never pastes full reports onward — synthesize and drop.

## 2. Implement → review → fix (single increment)

**When:** one bounded implementation unit at medium+ risk.
**Flow:** (optional ≤2 explorers for real unknowns) → one writer under lease → deterministic checks → freeze → 1–2 lens reviewers on the frozen diff (lenses from the risk, e.g. behavioral correctness vs. integration/lifecycle) → parent triage → original writer fixes accepted findings → targeted verification.
**Rules:** reviewers get the same brief and diff, can't see each other, may return "no findings." Spec-compliance and quality are separate verdicts. One review + one fix-verification pass by default.

## 3. Migration / repo-wide transform (pipeline)

**When:** same change across many sites (API migration, framework upgrade, mass rename with judgment).
**Flow:** discovery agent produces the complete work-list (the parent spot-checks completeness — a missed site is silent scope loss) → pipeline each unit through transform → verify, concurrency-capped; parallel writers only via per-unit worktrees, with one integration owner merging in a defined order → compose check over the whole.
**Rules:** per-item pipeline, not waves — unit 12 gets verified while unit 40 transforms. Log every skipped/failed unit in the ledger.

## 4. Bake-off / judge panel

**When:** wide solution space, high cost of picking wrong (architecture, algorithm, API design).
**Flow:** N=2–3 independent attempts from *different declared angles* (e.g. simplest-possible, performance-first, compatibility-first) in isolated workspaces → independent judge(s) score against written criteria → parent synthesizes from the winner, grafting runner-up ideas.
**Rules:** attempts never see each other; judges see all attempts but not authorship framing; criteria written before results return.

## 5. Loop-until-dry (unknown-size discovery)

**When:** finding *all* of something — bugs, dead code, inconsistencies — where a fixed agent count under-covers the tail.
**Flow:** rounds of small finder batches with distinct angles; dedupe new findings against **everything seen** (not just confirmed — else rejected findings resurface forever); stop after 2 consecutive dry rounds or at budget.
**Rules:** budget rail applies; report says "dry after N rounds," never "found everything."
**Not governed by the stop rule's round bound.** That bound covers re-reviewing one artifact. This is discovery over an unknown-size space, and it terminates on dry rounds — a fixed count here is just an undercount of the tail.

## 6. Adversarial verification

**When:** high-stakes claims — security findings, root-cause diagnoses, "this is safe to delete."
**Flow:** per claim, 2–3 independent agents briefed to **refute** it ("default to refuted if uncertain"), or given distinct lenses (correctness / security / does-it-reproduce) when it can fail in different ways. Majority refutation kills the claim; survivors get acted on.
**Rules:** verifiers never see the finder's reasoning, only the claim and the evidence pointers.

## 7. Quarantined deep read (context protection)

**When:** you must digest something huge — a vendor SDK, a log dump, a legacy module — but only conclusions matter.
**Flow:** one reader agent per corpus chunk; each returns a 1–2k-token distillation (facts, file:line pointers, gotchas) to files; parent reads distillations only.
**Rules:** this is the purest use of subagents-as-context-control; resist "just reading it myself" for anything that would eat >20–30% of your context.

## 8. Competing hypotheses (peer debate)

**When:** debugging or analysis where anchoring is the enemy — the first plausible theory tends to win regardless of truth.
**Flow:** one agent per hypothesis, each briefed to prove its own *and actively disprove the others'* from evidence. Parent adjudicates on evidence quality.
**Rules:** hierarchical subagents approximate this. True peer-to-peer agent teams are the native fit, at meaningfully higher token cost — but they are an env-var opt-in set outside a running session, so that route is a user decision, not one you can take mid-run (see harness reference).

## 9. Completeness critic (final pass)

**When:** end of any large orchestration.
**Flow:** one fresh agent asks only: what's missing — an angle not swept, a claim unverified, a criterion without evidence, a file outside the diff scope? Its findings become either quick follow-ups or explicit `Gaps:` lines in the report.
**Rules:** critic is cheap (fast/standard tier); it audits coverage, it does not redo the work.

## 10. Blind acceptance suite (the independent test designer)

**When:** the plan carries a writer unit *and* checkable criteria can be extracted without inventing behavior (one strong criterion qualifies). Offered at the gate as **light / full / none**; `full` needs a target that builds and runs tests in-session, and is the only option ever hidden. Coverage, diff size, scale and risk triggers move the "(Recommended)" tag, never the option list.
**Artifact:** one scratch file of numbered cases — written cases, not test code. Each carries an ID, the criterion it traces to, steps, the expected *observable* outcome, and a check method tagged **machine-verifiable / agent-observable-but-subjective / human-only** (the evidence-menu taxonomy below).
**Flow — light:** one small standard-tier unit authors the suite in parallel with the implementer, from the requirement text and approved criteria only — never the plan's design, the source, or a diff (firewall: SKILL.md Step 4). It writes one scratch file and touches no tree, so parallel is safe by construction. Then: parent traceability scan (an uncited case is an invented expectation) → verifier checklist → diff-reviewer coverage lens.
**Flow — full:** after freeze, one compile unit turns each machine-verifiable case into a runnable test from the as-built interface — signatures only, never the diff, never a run against the candidate → red-check all against the baseline (every one must fail there; one that passes is vacuous, flag it) → run in the existing verification stage.
**Rules:** an ambiguity the author cannot resolve returns as a **question**, never as a case. The implementer sees criteria, never the suite. Verdicts are pass / fail / `Awaiting human`; human-only cases route to the human checkpoint. A failing case is a finding, not a verdict — triage decides (defect / case overreach / user decision). A case the toolchain cannot express downgrades to agent-observable, recorded, never dropped. Fix leases exclude test paths, and at fix time the implementer gets the failed criterion and observed behavior, not the case text. **No new stage.**

---

# Evidence menus by domain

"Done" requires evidence appropriate to the domain, not just green reviewers.

**Software (default):** compile/lint/typecheck; focused then full tests; a runnable reproduction per bug fix; regression test per accepted finding; perf measurement where a budget exists; diff-scope check. For gated implementation work, add a requirement-level acceptance suite authored blind to the plan and the code (pattern 10), with its compiled subset red-checked against the baseline and run at verification.

**Every domain, before work starts:** mark each acceptance criterion **machine-verifiable / agent-observable-but-subjective / human-only**. A unit can be technically complete while explicitly awaiting a human judgment — report that as `Awaiting human`, and never let a reviewer's silence stand in for it. Domain menus beyond these belong in a project-level reference.

**Research / writing:** every load-bearing claim carries a source fetched this run (marked fetched vs. snippet); conflicting sources surfaced, not averaged; recency checked against today's date; a completeness critic pass before delivery.

**Data / analysis:** input row/coverage counts stated; transformations spot-checked against raw records; numbers that will be quoted re-derived once independently; charts checked against the underlying table.
