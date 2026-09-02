# Software fixed-point review

Policy owner: `policy.software-review`

Every Sage software implementation review uses two independent axes against one frozen fixed point. Standards asks whether the candidate follows documented repository rules plus the smell baseline below. Spec asks whether it implements the admitted request. Each reader returns its own evidence and verdict; the root triages both without blending them.

## Pin the fixed point

Inside Sage, prefer the captured baseline artifact and hash manifest when a dirty or untracked worktree makes a git reference inexact. Otherwise resolve the named git point, use `git diff <fixed-point>...HEAD` against its merge-base, and record `git log <fixed-point>..HEAD --oneline`. Standalone git review retains these merge-base semantics. Stop before review if the point cannot be resolved or the candidate diff is empty.

The Sage plan supplies the specification from its objective, acceptance criteria, done-when clauses, and accepted decisions. Outside a run, find it in documented issue references, a user-supplied path, or matching repository specs; report `no spec available` when none exists.

## Standards axis

Collect the repository's documented coding standards. A deliberate documented repository standard overrides the baseline. Baseline hits are judgment calls, never hard violations. Skip formatting, lint, and type issues already enforced by deterministic tooling. Match every one of these 17 smells against the fixed diff:

1. **Mysterious Name** — a name does not state what it does or holds. Rename it; inability to name it exposes unclear design.
2. **Duplicated Code** — one logic shape appears in multiple changed sites. Extract the shared shape when it must change together.
3. **Feature Envy** — behavior reaches into another object's data more than its own. Move it beside that data.
4. **Data Clumps** — the same fields or parameters travel together. Name one type for them.
5. **Primitive Obsession** — a primitive stands in for a domain concept. Give it a domain type.
6. **Repeated Switches** — repeated branching on the same type. Use polymorphism or one shared lookup.
7. **Shotgun Surgery** — one logical change forces scattered edits. Gather the decision into one module.
8. **Divergent Change** — one module changes for unrelated reasons. Split by reason to change.
9. **Speculative Generality** — abstractions, parameters, or hooks serve no admitted requirement. Delete or inline them until a real need exists.
10. **Message Chains** — a caller walks `a.b().c().d()`. Hide the walk behind the first owner.
11. **Middle Man** — a type mostly forwards calls. Remove it and call the real target.
12. **Refused Bequest** — a subtype ignores most of what it inherits. Prefer composition.
13. **Overridden safeties** — disabled warnings/tests or swallowed errors hide defects. Restore the safety and fix the cause.
14. **Imprecise decision** — approximate types, missing boundary checks, or race-prone constructs sit where exactness is required. Make the decision exact.
15. **Convention where structure belongs** — naming or comments enforce what a type or construct could enforce. Move the rule into structure.
16. **Null in, null out** — untyped absence is easy to forget. Use empty values, typed absence, or loud failure.
17. **Comment noise** — a comment restates code, narrates callers/history, asserts outside facts, is wrong, or overwhelms the code. Delete it first; retain only a short owned reason.

Reader brief:

> Report every place the fixed diff violates a documented standard, citing file and rule. Report every smell you spot by name and quote the hunk. Give each finding blocker, major, or minor severity and label it either a hard documented violation or a baseline judgment call. Repository standards override the baseline. Skip checks already enforced by formatter, linter, or type checker. “No findings” is a valid complete report. Stay under 400 words and return a separate Standards verdict with evidence.

## Spec axis

Reader brief:

> Report with blocker, major, or minor severity: requirements that are missing or partial; behavior the specification did not request; and implemented requirements whose behavior appears wrong. Quote the requirement for each finding. “No findings” is a valid complete report. If no specification exists, report “no spec available” and stop. Stay under 400 words and return a separate Spec verdict with evidence.

## Root triage

The readers do not repair or aggregate. The root preserves their separate reports, dispositions every finding, settles conflict with the narrowest reproduction or source check, grants accepted fixes to one writer, and assigns independent fix verification. A change can pass Standards and fail Spec or the reverse; report counts and worst severity per axis, never one combined score.

Sage deliberately adapts the standalone git-only fixed point to allow a captured baseline artifact and hash manifest when pre-existing dirty or untracked work makes a git ref inexact. Standalone review still uses the merge-base commands above. Sage also records the two readers as plan units rather than asking the review reference to spawn them; their briefs, evidence separation, verdicts, smells, and root triage are unchanged.

Completion criterion: both reader briefs ran against the same fixed point, Standards received repository sources and all 17 smells, Spec received the admitted requirements, each axis returned evidence and a verdict, and the root recorded every disposition.

Normative clauses are adapted from the MIT-licensed source skill named by the Phase 0 invariant inventory.
