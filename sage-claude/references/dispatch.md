# Dispatch contracts

Copy these shapes; do not improvise them. Trim a field only where it is genuinely irrelevant and never rename one — sage scans these shapes across many units, and a renamed field reads as a missing one.

**Contents** — [Task brief](#task-brief) · [Agent report](#agent-report) · [Finding schema](#finding-schema) · [Risk rubric](#risk-rubric) · [Snapshot protocol](#snapshot-protocol) · [The ledger](#the-ledger) (Plan · Unit table · Assumption log · Decisions and deviations · Findings and dispositions · Run record) · [The handoff note](#the-handoff-note)

## Task brief

```text
Role: <implementer | explorer | reviewer(lens) | verifier | judge>
Objective: <one sentence>
Inputs / source of truth: <file paths, briefs, diffs — the agent starts blank, with no transcript. Name the exact ground truth: files, line numbers, URLs, the measured baseline, the harness to measure with. A brief that must rediscover its ground truth costs ~2× and fails more>
Scope and relevant files: <explicit>
Allowed writes: <none | exact paths | worktree path>
Allowed tools: <the tool scope this objective needs — "read + search only, no network, no shell" | "repo tools + Bash for the test command only" | "inherit". Reviewers and explorers: deny network and shell unless the objective names a use for them. Read-only writes plus open network access is not read-only>
Per-unit caps: <`maxTurns` / `permissionMode` where a saved agent file sets them, else "none — plain dispatch". Unlike the two lines above, these BIND. A unit that hits `maxTurns` returns `blocked`, not failed, and charges no rung on the failure ladder>
Must not do: <boundaries, non-goals, no nested delegation unless granted>
Baseline / snapshot: <revision, diff, or file manifest being worked against>
Done when: <one falsifiable sentence>
Model: <the exact value passed to this dispatch, matching its ledger Plan row; tier in brackets. On a saved-agent dispatch its frontmatter model is that value unless you deliberately override>
Effort: <the level, always, plus the control setting it — agent-file frontmatter, or "no control" on a plain dispatch. Matches its ledger Plan row>
Return format: the agent report below, ≤1–2k tokens; bulk output to <scratch path> (omit the scratch path for a unit that cannot write — `explorer` and `web-researcher` distill instead, and a scratch path in their brief is a briefing error)
```

**Where an acceptance suite runs** (`topologies.md` #10), three briefs change shape. The blind author's `Inputs` are the requirement text and the criteria recorded in the ledger's Plan section, and nothing else — it is the one dispatch class exempt from naming the decisions already made (`../SKILL.md` Step 3): it receives the decisions' observable consequences, never the decisions. The implementer's brief carries the criterion IDs and never the suite path. The verifier's brief carries the suite path and the per-case verdict set — pass / fail / `Awaiting human`, with evidence required on each.

## Agent report

```text
Status: completed | partial | blocked
Result: <concise conclusion or changes made>
Evidence: <file:symbol refs, commands run, reproductions, measurements>
Files changed: <exact list, or none>
Checks run: <command → outcome>
Uncertainty: <unverified assumptions, remaining risks>
Recommended next action: <if any>
```

Validate material claims against repo state or tool output. A summary is a handoff, not proof.

## Finding schema

```text
ID:
Severity: blocker | major | minor
Confidence: high | medium | low
Location: file and symbol/line
Failure mode / impact:
Evidence or reproduction:
Violated criterion, requirement, invariant, or risk boundary: <a missing criterion may itself be the finding>
Suggested direction:
How to verify a fix:
```

- **Blocker**: crash, corruption, security failure, broken build, unusable core path, failed mandatory criterion.
- **Major**: credible user-visible incorrectness, regression, serious performance or near-term maintainability failure.
- **Minor**: bounded improvement; never blocks acceptance.
- Low-confidence hypotheses are investigation leads, not blockers. Style-only comments are omitted.
- Triage states: **accepted / rejected with evidence / deferred with owner / user decision.** Every finding gets exactly one.

## Risk rubric

Axes: failure impact; breadth of coupling; novelty/uncertainty; reversibility; strength of automated verification; external compatibility or human-decision dependencies.

**Hard triggers → treat as high risk regardless of other axes:** data/save migration, security or credentials, networking or deterministic simulation, public API compatibility, irreversible conversion, a core performance budget, behavior with no reliable test oracle. Reclassify mid-task if exploration reveals a different blast radius.

- **Low**: parent or one worker; focused checks; review only if behavior is non-obvious.
- **Medium**: ≤2 explorers for real unknowns; one writer; one lens-specific reviewer; targeted fix verification.
- **High**: bounded exploration; optional pre-write plan critic (`topologies.md` #11) and blind acceptance suite (`topologies.md` #10, which owns the light/full/none decision and consumes the hard-trigger list above as one of its four signals) — **sage decides both**, each justified by a named trigger. One writer per isolated tree; staged checks; two independent reviewers on the same frozen diff; parent triage; targeted regression verification; human checkpoint for subjective criteria (the `Awaiting human` route — `topologies.md`, evidence menus).

## Snapshot protocol

Runs whenever any writer is present, the parent included.

1. **Baseline** — record starting revision, dirty files, task-owned files. Unrelated dirty changes are never the agent's work and must survive. **This is the only recovery map once a writer has run**, because no automatic snapshot covers a delegated write (`harness.md`, Cautions). Baselining is the substitute, not a formality.
2. **Write lease** — one named writer; everyone else source-read-only.
3. **Stabilize** — writer finishes; run focused checks; capture the diff or changed-file manifest.
4. **Freeze** — no source changes while reviewers inspect the candidate.
5. **Triage** — merge and dedupe findings by root cause, not by wording, before any fix.
6. **New lease** — one writer for accepted fixes (prefer the original; a fresh one needs the complete handoff).
7. **Verify** — targeted checks on fixes and regressions. A new full review only if design materially changed.

No manufactured commits just to make a snapshot — a stable diff or file-hash manifest is enough. Non-git projects: record the task-owned file list with before/after hashes.

Two lease cases the seven steps do not cover. The parent taking a writer unit inline **moves the lease to the parent** — it does not lapse, and no other writer starts. A rail stopping the run (`../SKILL.md`, Rails) **freezes the lease** where it is. Log either in the ledger, because a lease whose holder is unrecorded is the same as no lease.

## The ledger

One file, `.claude/plans/sage-ledger-<session>.md` — durable; **gitignored only where that repo says so, which is a `git check-ignore -q .claude/plans/` test to run before the first write, never an assumption** (`harness.md`, Ledger location, for the four branches and what each one prints) — the session scratchpad only as a fallback where no durable path exists — and it is the only record of a run. **It is not written for the user.** Auto-compact lands mid-run with agents still in flight and discards nearly the whole window (`harness.md`, Transcripts). Five things read it back afterwards, and all five are sage: the budget rail needs the recorded estimate to measure against; the write lease and snapshot baseline are the only way back from a bad writer; the failure ladder counts signatures across attempts; handover reconstructs the run from it; and `/sage report` renders it — which is why it may not live where a session's end deletes it. **Bring it current before launching a wave and after each integration.** **`/sage report` resolves it in this order:** this session's file; else, with no session named, the most recently modified `.claude/plans/sage-ledger-*.md` under the working directory, naming which one it read; else the scratchpad fallback. None of those → say so. A run record is rendered from a ledger or not at all, never reconstructed from memory.

**The ledger's first line is a fixed header comment**, so the occupancy duty survives a compaction summary and a fresh reader re-learns it from the ledger alone rather than from anything the parent remembers:

```text
<!-- sage occupancy duty: at every bring-current point, read parent occupancy (input + cache_creation + cache_read on the latest assistant record of <parent-transcript-path>); at >= <threshold> (30% of the <window> window), stop launching and run SKILL.md ## Handover. Generation: <0|1|2|3>/3, role: <parent|supervisor>. Last check: <occ> (<pct>) at <when>. -->
```

Written at Plan time, restamped at every bring-current point. The `Generation` and `role` fields are what a post-compaction parent reads to know it is **already** supervising generation *n* — the chaining cap has no other durable sensor, and without these fields a compacted supervisor would re-run the handover and spawn a duplicate successor.

### Plan

Written at `../SKILL.md` Step 2, in full, before any dispatch. Estimating: read `../memory/shared.md` for the estimating rules and `../memory/local.md` for the bands.

```text
TASK: <one line>
RISK: low | medium | high (rubric above)
TOPOLOGY: <pattern number and name, or custom> — <one-line why>
PARENT: <the model you are running on> — synthesis, triage, completion claim

| # | Unit (done when)         | R/W | Model (tier)      | Effort (via)         | Flow       | Isolation   | Est. tokens |
|---|--------------------------|-----|-------------------|----------------------|------------|-------------|-------------|
| 1 | ...                      | R   | haiku (fast)      | low (explorer)       | bg, batch1 | —           | ~20k        |
| 2 | ...                      | W   | sonnet (standard) | medium (implementer) | bg, after1 | write lease | ~80k        |
| 3 | review of #2 (lens: ...) | R   | opus (frontier)   | high (verifier)      | bg, after2 | frozen diff | ~50k        |

Cap: <N> concurrent.
Budget: ~<total> tokens, ~<min> wall clock — basis: <the same-shape row you priced off, named, or the band>. The token figure sets the run's own ceiling, so estimate honestly in both directions (`../SKILL.md`, Rails).
Acceptance suite: light | full | none — chosen because <one line>.
        Criteria: R1 <text>; R2 <text>; ...
Scouting: <N explorer scouts, rounds where two, ~actual tokens — already spent (`../SKILL.md` Step 1)>.
Risks: <top 1–3. With any writer present, name the `/rewind` gap explicitly>.
Solo alternative: <what one strong agent inline would cost or miss>.
```

**Model and Effort columns** — the exact model value you will pass with its tier in brackets, never a tier alone; and the effort **level always**, with the control that sets it in brackets. `low (explorer)`, `high (verifier)`, `medium (web-researcher)`, `medium (implementer)` where frontmatter sets it; `medium (no control)`, written in full, on a plain dispatch, which has no lever. Never a bare level and never a dash: a bare `low` is a promise nothing keeps, and a dash hides the target. Resolve tier → model against the live session and run the `CLAUDE_CODE_SUBAGENT_MODEL` check before writing the Model column — `harness.md`, Models and effort, for what a set override does to every cell in it.

**Flow column** — `bg, batch1` for a wave, `bg, after1` for a row consuming a whole prior wave, `bg, per-item after <id>` for the pipeline-per-item flow Step 1 prefers. A per-item stage over N items is **one row**, with the item count in its `done when` clause. **Acceptance-suite criteria go in as text, verbatim, not as a count**, each phrased at the requirement's observable surface — no module names, no data stores, no mechanism choices, because the blind author's firewall depends on it (`../SKILL.md` Step 3).

**Compress the table before writing it.** Both rules still pay with a model reading this out of a file: a wrapped cell costs the row its alignment, and an invariant column costs attention on every row. **One physical line per row** — keep a short unit name in the cell and move every `done when` clause to a numbered list under the table, keyed by row id. **A constant column is not a column** — where every row shares a value, delete the column and state it once above the table (`All rows: background, read-only, wave 1.`); Effort, Flow and Isolation collapse this way in most plans, while a column that varies stays, however wide.

### Unit table

```text
| id | unit | agent/thread name | model used | state | messages | evidence | actual tokens |
```

The live per-unit state, updated on every state change. State ∈ `planned | running | reported | blocked | failed | abandoned | inline`. **Every unit is dispatched with an explicit name and that name is recorded here** — unrecorded, it is a unit the watchdog can neither steer nor recall (`harness.md`, Spawning, for why the name is the handle). This table is also what the watchdog's estimates file is built from (`../SKILL.md` Step 4).

**`messages`** holds every ladder `SendMessage` sent to this unit: the time each went out, and whether a reply landed. It is the only state behind the ladder's parent-tracked arm — *no reply 600s after two messages* — because the watchdog never saw the messages. An empty cell means none were sent, never that the unit answered.

### Assumption log

One row every time sage resolves an ambiguity a human would otherwise have been asked about — scope, decomposition, model, suite, topology, or the meaning of the task itself.

```text
| assumption | what I chose | what else was plausible | how it would show if wrong |
```

Ambiguity that changes the decomposition is the one place sage carries more risk than an attended run, so that case is always a row, never a judgment call. A later user correction is written **next to the row it corrects**, in that same row, never as a fresh row elsewhere. One condensed line goes in the run record.

### Decisions and deviations

```text
| when | decision, plan amendment, or dropped disagreement | reason |
```

Every plan amendment — model, effort, scope, count, topology, cap — with its reason and when it happened. **Every abandoned disagreement gets a row too**: what was dropped, which unit held it, and why it lost. Silent discard is forbidden.

### Findings and dispositions

```text
| id | severity | location | triage | evidence |
```

One row per finding from the schema above, each carrying exactly one triage state. A finding whose triage is still open is an unfinished run.

### Run record

Rendered on demand by `/sage report`, from this section alone, so the answer survives compaction.

```text
OUTCOME: <one line, or a pointer to the Result — never a replacement for it>
Topology: <pattern, N agents, why> (or "solo — <reason>")
Agents: <one line each: unit → model actually used → status → key evidence>
Cost: <N agents, ~actual against ~estimate, wall clock — say so where no token counts were visible, in which case the agent-count rail was the one in force>
Deviations: <every row that ran with a different model, effort, count, or scope than planned, and why — or "none">
Findings: <accepted / rejected / deferred / user-decision counts, plus the ones that matter>
Verification: <checks run and outcomes. Separate MEASURED passes — a command executed — from JUDGED passes, where a case was read and ruled on. A judged pass is a reviewer's opinion with a case number on it. `Awaiting human` cases count as neither, and any machine-verifiable case that downgraded to judged is named here>
Diff: <pointer to the frozen diff — revision range or changed-file manifest, writer by writer, or "none">
Coordination check: <what depended on the agents being independent — a disagreement, a refutation, a cross-angle finding — or "nothing; one agent at this budget would likely have matched it". Answer honestly: "the fan-out bought nothing" is a real result>
Gaps: <anything bounded, sampled, skipped, or unverified — explicitly>
Awaiting human: <subjective or product checkpoints, if any>
Assumptions: <one condensed line from the assumption log — the calls that would change the answer if wrong>
Lessons: <the note from the row appended to `../memory/local.md` this run, mirroring that column verbatim — the lesson a future run can act on, or "none beyond the actuals". `../SKILL.md` Step 6 writes the row; this line is what makes it renderable>
```

The **Result** — the deliverable in prose, standing alone — is printed by `../SKILL.md` Step 6 on every run and never lives only here. `OUTCOME:` is one line inside a template, and a template line compresses a deliverable into a pointer.

## The handoff note

Written to `.claude/plans/sage-handoff-<session>-<timestamp>.md` when parent occupancy crosses the handover threshold (`../SKILL.md`, Handover). Durable, beside the ledger — and it holds the whole run state, so it is the file the `git check-ignore -q .claude/plans/` test matters most for: check first, then name the path you wrote to (`harness.md`, Ledger location).

**The note is normally the successor's whole brief** — an `orchestrator` dispatch names only file paths, this one among them — which is why completeness here matters more than it once did: a gap the parent could once have filled in by memory is now a gap the successor starts blank against.

```text
# Sage handoff — <task> — <session> — <timestamp>
Goal: <the user's task, verbatim — not a paraphrase>
Generation: <n of max 3>
Ledger: <path to `.claude/plans/sage-ledger-<session>.md`, which this note summarises and does not replace>
Plan: <the ledger's Plan block, each row carrying its current status>
Findings so far: <every finding harvested, with file:line provenance and its triage state>
Write lease: <who holds it right now — an agent name, the parent, or "frozen">
Snapshot baseline: <revision, dirty files, task-owned files. `/rewind` does not undo subagent edits, so this is the only way back>
Paths touched: <every one, writer by writer>
Open questions: <each with the current hypothesis and what would settle it>
Discarded: <approaches tried and dropped, with why, so the next session does not re-buy them>
Transcripts: <path to this session's `subagents/` directory>
        <agentId → description, one line per agent dispatched — mine these for units whose reports were never absorbed>
Resume: <the next action a fresh session should take>
```

**The note's own blind spot, restated for the successor design.** The human path — a spawn that failed, an environment that blocked nesting, or a third generation exhausted with work remaining — is now the **terminal fallback**, not the default outcome, and on that path a skill that neither presents a plan nor writes a report has removed the actor the fallback depends on: the note lands at a path nobody was told to read. So on the human path, the printed note path stays a surfaced event, unconditionally (`../SKILL.md` Step 6) — this is the one place a quiet design speaks. On the successor path, the run does not stop: the handover event — generation, note path — is surfaced at Step 6 alongside everything else, and the note itself is read by the successor rather than by a person.
