# Orchestration topologies

Pick the smallest pattern that fits, then compose patterns for larger work. Every pattern uses the contracts in `dispatch.md`.

| # | Pattern | When | The rule that is easy to get wrong |
| --- | --- | --- | --- |
| 1 | Research or review sweep | a broad question with many independent angles | 4–8 **non-overlapping** angles. Each brief names what the other agents cover. The parent synthesises and never pastes a report onward |
| 2 | Implement → review → fix | one bounded implementation unit, medium risk or higher | one writer under lease, deterministic checks, freeze, 1–2 lens reviewers on the frozen diff, triage, fix, re-freeze, then the loop in `verify.md` |
| 3 | Migration pipeline | the same change across many sites | a discovery unit writes the complete work-list and the parent spot-checks it, because a missed site is silent scope loss. Pipeline per item, not waves. Log every skipped unit |
| 4 | Bake-off | a wide solution space with a high cost of picking wrong | two or three attempts from **different declared angles**, in isolated workspaces. Judges score against criteria written before the results. Read for convergence first: opposite angles that reach one root cause beat any one agent |
| 5 | Loop-until-dry | finding *all* of something | small finder batches with distinct angles, deduped as `verify.md` says. Stop after 2 consecutive dry rounds. The record says "dry after N rounds", never "found everything" |
| 6 | Adversarial verification | high-stakes claims: security, root cause, "safe to delete" | 2–3 agents briefed to **refute** each claim, defaulting to refuted when uncertain. Verifiers see the claim and its evidence pointers, never the finder's reasoning |
| 7 | Quarantined deep read | a huge corpus where only conclusions matter | one reader per chunk returns a 1–2k distillation. Use it for anything that would take more than 20–30% of your context |
| 8 | Competing hypotheses | debugging where anchoring is the enemy | one agent per hypothesis, each told to prove its own and disprove the others. Adjudicate on evidence quality |
| 9 | Completeness critic | the end of any large run | one fresh standard-tier agent asks only what is missing. Its findings become follow-ups or `Gaps:` lines |
| 10 | Framing critic | medium risk and above, before the first writer or review wave | see below |
| 11 | Blind acceptance suite | checkable criteria exist, whoever writes | `conditional.md`. The default is `full` where the repo can build and run tests |
| 12 | Blind behavioural lens | a change to this ecosystem's behaviour-shaping text, where the question is what the text makes an actor do | `conditional.md` |

Cutting an *angle* loses the findings only that angle sees, while cutting a second agent off the *same* angle costs nothing.

## The framing critic

**Dispatch one critic before the first writer or the first review wave**, at medium risk and above. It runs in parallel with the first scouts where it can. It takes the refuting seat: `alt-lane.md` names it where a codex seat is cleared, else the checker rule in `verify.md` picks it.

- It receives the ASK, PURPOSE, PREMISES and DELIVERABLE fields and the acceptance criteria, verbatim. It never receives your reasoning behind them.
- **Its mandate:** "Refute that these criteria, if they pass, give the user what the ASK and PURPOSE need. Refute each premise you can test with a command." Pre-bless "no findings".
- A refuted criterion or premise is a `reopen` row in `### Decisions` and a re-plan before any writer starts. A refuted design costs a re-plan, not a rewrite.

This is the pre-write plan critic of past runs, made a default. Both of its logged uses refuted the design before any code was written.

# Evidence menus by domain

"Done" needs evidence that fits the domain, not only green reviewers.

**Every domain, before work starts:** tag each acceptance criterion **machine-verifiable / agent-observable-but-subjective / human-only**. A unit can be technically complete while it waits on a human judgment. Record that as `Awaiting human`, which is a surfaced event. Never let a reviewer's silence stand in for it.

**Software:** compile, lint, typecheck; focused then full tests; a runnable reproduction per bug fix; a regression test per accepted finding; a perf measurement wherever a budget exists; a diff-scope check; the blind acceptance suite (#11).

**Research and writing:** every load-bearing claim carries a source fetched this run, marked fetched or snippet. Conflicting sources are surfaced, never averaged. Recency is checked against today's date. A completeness critic runs before delivery.

**Data and analysis:** state input row and coverage counts. Spot-check transformations against raw records. Re-derive once, independently, every number that will be quoted. Check charts against the underlying table.
