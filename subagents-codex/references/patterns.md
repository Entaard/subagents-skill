# Orchestration patterns

Pick the smallest pattern that fits; compose them for larger work. Every pattern uses the contracts in `contracts.md`.

## 1. Research / review sweep (fan-out, map–reduce)

**When:** broad question answerable from many independent angles — codebase audit, literature/doc research, multi-dimension code review.
**Flow:** decompose into 3–8 *non-overlapping* angles (by subsystem, by lens, by source type — never "agent 1 and agent 2 both research X"). Launch one batch, readers only, background. Parent synthesizes; conflicting claims go to verification, not a coin flip.
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
**Rules:** hierarchical subagents approximate this; if the harness offers true peer-to-peer agent teams (see harness reference), that's the native fit — at meaningfully higher token cost.

## 9. Completeness critic (final pass)

**When:** end of any large orchestration.
**Flow:** one fresh agent asks only: what's missing — an angle not swept, a claim unverified, a criterion without evidence, a file outside the diff scope? Its findings become either quick follow-ups or explicit `Gaps:` lines in the report.
**Rules:** critic is cheap (fast/standard tier); it audits coverage, it does not redo the work.

---

# Evidence menus by domain

"Done" requires evidence appropriate to the domain, not just green reviewers.

**Software (default):** compile/lint/typecheck; focused then full tests; a runnable reproduction per bug fix; regression test per accepted finding; perf measurement where a budget exists; diff-scope check.

**Game development:** a playable scene or checkpoint per increment; expected player-visible behavior stated up front; frame-time/memory budget where relevant; screenshots or captures for visual work; input and edge-case checks; debug overlays for hard-to-observe state. Mark each criterion **machine-verifiable / agent-observable-but-subjective / human-only**. Agents may prepare playtest checklists and captures; *game feel, pacing, fun are human-only* — a phase can be technically complete while explicitly awaiting a human playtest. (Engine-specific review lenses — e.g. Godot lifecycle/signals/resources — belong in a separate project-level reference; keep this skill generic.)

**Research / writing:** every load-bearing claim carries a source fetched this run (marked fetched vs. snippet); conflicting sources surfaced, not averaged; recency checked against today's date; a completeness critic pass before delivery.

**Data / analysis:** input row/coverage counts stated; transformations spot-checked against raw records; numbers that will be quoted re-derived once independently; charts checked against the underlying table.
