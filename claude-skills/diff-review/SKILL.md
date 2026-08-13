---
name: diff-review
description: Two-axis review of the changes since a fixed git point — Standards (does the diff follow this repo's documented coding rules, or the baseline smell list below) and Spec (does the diff match what was asked for). This skill triggers only when the user invokes "diff-review" by name, or when the subagents orchestration skill uses it inside a run. It does not trigger on general requests like "review since X" or "review this branch".
---

# diff-review

diff-review checks the changes since a fixed git point along two separate axes:

- **Standards** — does the diff follow this repo's documented coding rules, and the smell baseline below?
- **Spec** — does the diff match what was asked for?

The two axes never merge. A change can pass one and fail the other, and the reader should see both results, not one blended score. See "Why two axes" at the end of this file.

## Step 1: Pin the fixed point

The fixed point is a commit, branch, or tag the user names — for example a SHA, `main`, or `HEAD~5`. If the user gave none, ask for one.

Build two commands, once, before anything else runs:

- The diff command: `git diff <fixed-point>...HEAD`. Use three dots. This compares against the merge-base, not against the raw tip of the fixed point.
- The commit list: `git log <fixed-point>..HEAD --oneline`.

Before you do anything else, check two things:

1. The fixed point resolves: run `git rev-parse <fixed-point>`.
2. The diff is not empty.

If either check fails, stop and report the failure. Do not let a bad ref or an empty diff reach the two reader steps below.

## Step 2: Find the spec

Look for the spec in this order. Stop at the first step that finds one.

1. **The current orchestration run's own artifacts**, if this diff-review runs inside a run: the approved acceptance criteria, the unit's "done when" clause, or the initial requirements recorded in the run's ledger or briefs.
2. **Issue references in the commit messages** (`#123`, `Closes #45`, and similar). Use this step only when the repo itself documents an issue-tracker workflow, for example in a `docs/agents/issue-tracker.md` file or an equivalent file the repo names. Never assume an issue-tracker workflow, and never install one from another repo to get this step to work.
3. **A path the user passed as an argument.**
4. **A spec file** under `docs/`, `specs/`, or `.scratch/` that matches the branch name or the feature.
5. **Ask the user.** If they say there is no spec, the Spec axis reports "no spec available" and step 4 below skips the Spec reader.

## Step 3: Find the standards sources

Look for anything the repo documents about how code should be written. Examples: `CODING_STANDARDS.md`, `CONTRIBUTING.md`, or a rules file that this ecosystem's clean-code skill may have added to the repo, such as `clean-code-rules.md`.

Whatever the repo documents, the Standards axis also always carries the smell baseline below. Two rules bind it:

- **A documented repo standard overrides the baseline.** Where the repo endorses something the baseline would flag, do not flag it.
- **Every baseline hit is a judgement call**, never a hard violation. Label it as one, for example "possible Feature Envy". Skip anything a linter, formatter, or type checker already enforces.

### Smell baseline

The first 12 entries come from Martin Fowler's *Refactoring*, chapter 3, as carried by the MIT-licensed source skill. The last 4 come from the Clean Code smells this ecosystem's research found missing from Fowler's list.

Each entry reads as *what it is* → *how to fix it*. Match each one against the diff.

1. **Mysterious Name** — a function, variable, or type whose name does not say what it does or holds. → Rename it. If no honest name comes to mind, the design itself is unclear.
2. **Duplicated Code** — the same logic shape appears in more than one hunk or file in the change. → Extract the shared shape. Call it from both places.
3. **Feature Envy** — a method reaches into another object's data more than its own. → Move the method onto the data it reaches for.
4. **Data Clumps** — the same few fields or parameters keep travelling together. → Bundle them into one type. Pass that type instead.
5. **Primitive Obsession** — a primitive or string stands in for a domain concept that deserves its own type. → Give the concept its own small type.
6. **Repeated Switches** — the same `switch` or `if`-cascade on the same type appears more than once in the change. → Replace it with polymorphism, or one shared lookup both sites use.
7. **Shotgun Surgery** — one logical change forces scattered edits across many files in the diff. → Gather what changes together into one module.
8. **Divergent Change** — one file or module is edited for several unrelated reasons. → Split it so each module changes for one reason only.
9. **Speculative Generality** — abstraction, parameters, or hooks added for a need the spec does not have. → Delete it. Inline the code back until a real need appears.
10. **Message Chains** — a long `a.b().c().d()` walk that the caller should not depend on. → Hide the walk behind one method on the first object.
11. **Middle Man** — a class or function that mostly just passes calls onward. → Remove it. Call the real target directly.
12. **Refused Bequest** — a subclass or implementer that ignores or overrides most of what it inherits. → Drop the inheritance. Use composition instead.
13. **Overridden safeties** — a disabled warning, an ignored failing test, or a swallowed error hides a real defect. → Re-enable the safety and fix the cause, not the symptom.
14. **Imprecise decision** — an approximate type, a missing boundary check, or a race-prone construct sits where the problem needs precision. → Make the decision exact.
15. **Convention where structure belongs** — a rule that only a naming convention or a comment enforces, where a type or a language construct could enforce it instead. → Move the rule into structure.
16. **Null in, null out** — the change passes or returns "nothing" that a caller can forget to check. → Use an empty collection, a typed absence, or a loud failure instead.

## Step 4: Two modes

There is no third mode. Pick the one that matches how this skill was invoked.

### Standalone

Use this mode when the user invoked diff-review directly, outside an orchestration run.

Spawn two readers yourself, in parallel: a Standards reader and a Spec reader. Give each reader:

- The diff command and the commit list from Step 1.
- Its own axis's sources: the Standards reader gets Step 3's sources plus the smell baseline pasted in full, since it has no other access to it. The Spec reader gets the spec found in Step 2, or the note that none exists.
- The matching brief below.

Each reader reports back in under 400 words.

### Inside an orchestration run

Use this mode when the subagents orchestration skill's Step 2 gate is building a plan and diff-review is one of its rows.

diff-review spawns nothing itself in this mode. The two axes become two rows in the approved plan, behind the gate. The two reader briefs below become those rows' briefs, written into the plan exactly as they read here. The orchestration skill's own Step 5 does the aggregating and the triage. diff-review does not aggregate in this mode.

## Reader briefs

Use these verbatim, whether you are writing a sub-agent prompt (standalone) or a plan row's brief (inside a run).

**Standards reader brief:**

> Report every place the diff violates a documented standard. Cite the standard: the file and the rule. Report every baseline smell you spot: name it, and quote the hunk. Give each finding a severity: blocker, major, or minor. Say whether the finding is a hard violation of a documented standard, or a judgement call against the baseline. Baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything a linter, formatter, or type checker already enforces. "No findings" is a valid, complete report. Stay under 400 words.

**Spec reader brief:**

> Report three things, each with a severity of blocker, major, or minor: (a) requirements the spec asked for that are missing or only partly done; (b) behavior in the diff that the spec did not ask for; (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. "No findings" is a valid, complete report. If no spec was found, report "no spec available" and stop. Stay under 400 words.

## Standalone aggregation

In standalone mode only, once both readers report, present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do not merge or rerank findings across the two headings. The "Why two axes" section at the end of this file explains why that separation matters.

End with a one-line summary: the count of findings per axis, and the worst severity found within each axis (if any). Do not pick one worst finding across both axes. That would rerank the two axes back together.

Inside an orchestration run, skip this section. The parent's own Step 5 aggregates and triages the two rows' reports.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what was asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting the two axes separately stops one axis from hiding the other's result.

---

Portions adapted from mattpocock/skills (github.com/mattpocock/skills), MIT license.
