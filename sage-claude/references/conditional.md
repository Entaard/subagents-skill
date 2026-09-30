# Conditional topologies

Read this file only when a plan names one of the two patterns below. `topologies.md` lists when each one triggers.

## Blind acceptance suite (the independent test designer)

**When:** checkable criteria can be extracted without inventing behaviour. One strong criterion qualifies. The writer can be a dispatched unit or the parent. A parent writer is the strongest reason for an independent suite, because nobody else reads the plan blind.

**Decide `light`, `full` or `none`, and record the choice, its deciding signal and the criteria text verbatim in `### Plan`.**

- **Where the repo can build and run tests, the default is `full`.** Where it cannot, `full` is unavailable.
- A risk-rubric **hard trigger** (`dispatch.md`) argues for a suite. "Behavior with no reliable test oracle" is the one trigger that argues for `none` and routes verification to `Awaiting human`.
- Repo **coverage** that already spans the criteria, and a **diff that fits one sentence**, argue down.
- Criteria that would **flake as asserts** argue `full` → `light`. They never argue for `none`.
- Precedence: a hard trigger outranks coverage, which outranks the one-sentence diff.
- Nothing checkable to extract → `none`, in one ledger line that says why. A close call is an `assumption` row in `### Decisions`.

**Artifact:** one scratch file of numbered cases, written cases and not test code. Each case has an ID, the criterion it traces to, steps, the expected observable outcome, and a check method tagged **machine-verifiable / agent-observable-but-subjective / human-only**.

**Flow, light:** one small standard-tier unit writes the suite in parallel with the writer, from the requirement text and the criteria only. It never sees the plan's design, the source or a diff. It writes one scratch file and touches no tree. Then: a parent traceability scan (an uncited case is an invented expectation) → the verifier's checklist → a coverage lens on the diff.

**Flow, full:** after the freeze, one compile unit turns each machine-verifiable case into a runnable test from the as-built interface: signatures only, never the diff, never a run against the candidate. Red-check every test against the baseline. Each one must fail there, and one that passes is vacuous: flag it. Then run the tests in the verification stage.

**Rules:**

- The author receives the decisions' observable consequences, never the decisions.
- An ambiguity the author cannot resolve comes back as a question, never as a case.
- The writer sees the criteria, never the suite. Fix leases exclude test paths. At fix time the writer gets the failed criterion and the observed behaviour, not the case text.
- Verdicts are pass / fail / `Awaiting human`. A failing case is a finding, not a verdict: triage decides (defect, case overreach, or user decision).
- A case the toolchain cannot express downgrades to agent-observable, recorded, never dropped.

## Blind behavioural lens (two arms)

**When:** a change to behaviour-shaping text in this ecosystem's own corpus (a skill file, a shared template, a convention file), where the question is what the text makes a fresh actor do. Reviewers rule on text. Only an actor shows what the text makes people do. The trigger is what the change does, never which skill makes it. `/sage-promote` reaches it through its gate. A run that edits this corpus on the user's word reaches it through `verify.md`.

**Flow:** one agent is told to **perform** a written procedure on a sandbox copy, never to read or critique it. It learns nothing of the defect history or the author's intent. Two arms: the **control arm** runs against the pre-change text, taken with `git show HEAD:<path>` into a scratch copy, so the baseline is what actually shipped. The **change arm** runs against the edit. Run the control first.

**The one verdict a single sample settles is the stop.** A control arm that does not show the failure means there is nothing to fix. Stop, and do not write the guidance. Watching the failure happen is positive evidence, so one observation is enough in that direction.

**The reverse does not hold at one sample.** Two arms that agree at one sample each may agree by noise. So "adopt only if the arms differ" turns noise into a revert of a good edit. A null verdict needs five or more samples per arm, every flagged match read by hand, and variance treated as a result. **Never revert an edit on agreement at a single sample.** Where the control shows the failure and the arms then agree at one sample each, record an unresolved question, not a null result.

**Only one direction is affordable at a run's budget, and saying so is part of the pattern.** The stop is one dispatch. The adopt-or-null direction needs the full repeat count on both arms, so plan it as its own programme, never as something a corpus edit picks up in passing. Price the lens from the corpus the actor must hold, never from the task's length.

**What it buys over the refuting gate is narrow.** The gate catches degradations: a lost floor item, a second home, a claim wider than its evidence. An edit that behaves exactly like the old text passes every one of those. Detecting that null effect is the whole of what this pattern adds.
