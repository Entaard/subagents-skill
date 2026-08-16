# Contracts and templates

Copy these; don't improvise the structure. Fields may be trimmed when genuinely irrelevant, never renamed — the parent scans these shapes across many reports, and a renamed field reads as a missing one.

## Orchestration Plan (Step 2)

```text
TASK: <one line>
RISK: low | medium | high (rubric below)
TOPOLOGY: <pattern name or custom> — <one-line why>
PARENT: <the model you are running on> — does synthesis, triage, completion claim

| # | Unit (done when)            | R/W | Model (tier)      | Effort (via)        | Flow       | Isolation      | Est. tokens |
|---|-----------------------------|-----|-------------------|---------------------|------------|----------------|-------------|
| 1 | ...                         | R   | haiku (fast)      | low (explorer)      | bg, batch1 | —              | ~20k        |
| 2 | ...                         | W   | sonnet (standard) | medium (implementer)| bg, after1 | write lease    | ~80k        |
| 3 | review of #2 (lens: ...)    | R   | opus (frontier)   | high (verifier)     | bg, after2 | frozen diff    | ~50k        |

Cap: <N> concurrent.  Budget: ~<total> tokens, ~<min> wall clock — basis: <calibration row, or the band>.
Backend: hand-batched, except <row ids> via Workflow — <why, per row group; SKILL.md Step 2. Assign per
         ROW and record the split as a row-id list, never a per-row column. Hand-batched is the default
         for any row whose shape does not clearly favour a script. Write `hand-batched (all rows)`
         when none is scripted and `Workflow (all rows)` when every row is — both are legal splits
         when the rows call for them, and both still say why here. Name the mid-run
         rail each scripted row was sized to keep clear of; where a scripted row is a writer, add that
         its edits are auto-approved the moment the script runs; and print the ceiling the scripted
         GROUP was sized against, since no single row is ever in reach of a budget or wall-clock rail>.
Acceptance suite: light | full | none — recommended: <which>, because <one line>. <Omit this line and
         the next when the plan has no writer unit or nothing checkable; say which instead.
         `patterns.md` #10. Its cost is a guess, not a band — see the estimating note below>
         Criteria: R1 <text>; R2 <text>; ...
Scouting: <N explorer scouts, rounds where two, ~actual tokens — already spent before this plan
        printed (SKILL.md Step 1). Omit when none ran>.
Risks: <top 1–3. With any writer present, name the `/rewind` gap explicitly — checkpointing does not
        track subagent edits, so the manual baseline is the only recovery map (harness ref, Cautions)>.
Solo alternative: <what one strong agent inline would cost/miss — include when the call is close>.
Recommended: <the default answer, and one line of why — the user should be able to accept the whole
              plan with one word>.
```

**Model column:** the exact value you will pass, tier in brackets. Not a tier alone — a tier hides whether that is `haiku` or `sonnet`, and the user is approving what runs. Resolve tier → model against the live session first (procedure in `claude-code.md`), and run that file's `CLAUDE_CODE_SUBAGENT_MODEL` check before writing the column: a set override outranks both the dispatch param and agent frontmatter, and makes every cell in it false.

**Effort column:** the level _and_ the mechanism setting it. **Always write a level.** You picked one from the Step 3 tier table, and it stays in the cell whether or not a control can enforce it — the bracket says what enforces it. A saved-agent dispatch: `low (explorer)`, `high (verifier)`, `medium (web-researcher)`, `medium (implementer)` — effort is frontmatter there. A **scripted plain** row: `high (workflow)`, the mechanism being `agent({effort})`. A scripted row that _names a saved agent_ passes `agentType` alone, so its frontmatter still sets the effort and the bracket keeps the agent's name — `high (verifier)`, scripted or not: a script buys an enforced effort on the rows that had none, not a new mechanism on rows that already had one. A **hand-batched plain Agent call** has no lever, so the bracket says so: `medium (no control)` — written in full, never abbreviated or substituted.

A `(workflow)` bracket is legal **only on a plain row, and only while the `Backend:` line still lists it** — the one bracket that moves when the split does. An `adjust` that un-scripts a plain row drops it to `(no control)`; one that scripts a plain row raises it to `(workflow)`. Saved-agent rows never move either way: their frontmatter holds. Re-present every bracket that moved along with the new `Backend:` line, or the run uses a column the user never approved.

Never write a bare level and never write a dash. A bare `low` is a promise nothing keeps. A dash is worse: it hides the target, so the user cannot see what scripting that row would buy. `medium (no control)` next to `medium (workflow)` states the trade in one cell — same target, one enforced.

**Flow column:** `bg, batch1` for a wave, `bg, after1` for a row consuming a whole prior wave, and `bg, per-item after <id>` for the pipeline-per-item flow Step 1 prefers. That third value is not decoration — it is what the backend rule reads to check whether a split straddles a pipeline, the case that silently turns a per-item flow into a barrier. (How a per-item stage over N items is numbered — one row or N — is still unsettled: write one row and put the item count in its `done when` clause. **A stage written as one row cannot be split across backends** — the `Backend:` line addresses rows, not the items inside one — so if part of it must be scripted, enumerate the rows instead and accept the wider table.)

**Acceptance suite line** (`patterns.md` #10): the criteria go in as **text, verbatim, not a count**. This line is where the user co-signs the expectations, and an invented expectation has to be readable to die at the gate. Phrase each criterion at the requirement's observable surface — no module names, no data stores, no mechanism choices — because a design noun inside a criterion carries the parent's design straight through the blind author's firewall.

**Print this block as message text immediately before the gate question**, then attach only a digest of it to the `AskUserQuestion` preview — the preview clips and printed text does not (mechanics and budgets: `claude-code.md`, "The gate dialog").

**On `plan-only`, this block is also the file** — saved and resumed per SKILL.md, "Saving and resuming a plan".

Estimating tokens: exploration/lookup ~15–40k; implementation ~40–150k; focused review ~30–80k per agent. An acceptance suite adds ~15–35k for the blind author (`light`), and ~30–60k more for the compile unit and its red-check (`full`) — both **guesses, not bands**: no calibration row covers either unit class yet, and the first figure is borrowed from the nearest measured shape, an anchored single-corpus brief. Say so at the gate rather than presenting them as evidence. **These bands are priors and known to run low — read `../calibration.md` first.** Web fetches and large-corpus reads have run 2–5× the band; that file's own correction factor is a different number, not a substitute for this one. Where a row covers the task class, quote its actuals instead of the band and name the row. Append this run's actuals at Step 6, hits included.

Three estimating rules have held across enough runs to be defaults (counts and dates in the calibration log): **estimate from the corpus a unit must hold and the lenses it must apply** — never from the deliverable's size or the role's name (5 confirmations). **Price review and verify as a pair** — the fix-verification round has never once come back empty, and four times cost more than the review itself, because a fresh or full-mandate continuation still re-reads the whole corpus: retained context makes the round cheaper to brief, not cheaper to run. One measured exception: steering the same verifier thread for a narrow re-verdict on named fixes ran ~5× cheaper than a fresh dispatch — the pair rule prices a full verify round, not a steered follow-up (6 confirmations). **A claim checklist prices a review lens at its band's floor only when every item settles in one look** — an item quantified over the corpus costs what an open mandate costs, so price a lens by its widest question (3 confirmations).

### Fitting the plan to the gate surface

Three rules shrink the block itself. Apply them before printing, because a shorter block also makes a better digest:

- **One physical line per row.** A cell holding a sentence turns one row into three or four lines. Keep a short unit name in the cell and move every `done when` clause to a numbered list under the table, keyed by row id.
- **A constant column is not a column.** Where every row shares a value, delete the column and state it once above the table: `All rows: background, read-only, wave 1.` Effort, Flow and Isolation collapse this way in most plans. A column that varies stays, however wide.
- **Keep in the table only what the user audits:** id, unit, R/W, model, effort, est. tokens. Anything that would not change the answer goes below the table.

Where the block still runs past ~30 lines, save it to the session scratchpad as well and put that path in the digest. An editor has no width or height budget at all.

The digest attached to the `go` option is a summary, not a second copy. Fit it to **12 lines and 60 columns**, and keep this order — a clipped reader then loses the rows, which are printed above in full, rather than the recommendation:

```text
# the preview on "go"
8 agents (5 parallel) · ~615k · ~55 min · cap 5
Recommended: go — the fix and its triage stay in hand
Backend: A1–A2 scripted; W, V1 and triage held
         A1–A2 run at high (workflow); W and V1 at no control
Top risk: the fix changes sync behaviour on every build
Full plan printed above ↑   (saved: <path>)

A1 R opus   ~90k  delivery + dedup audit
A2 R opus   ~80k  classifier precision audit
W  W opus     —   parent writes the fix inline
V1 R opus   ~90k  compliance review of the frozen diff
```

On an `adjust` re-ask the shape holds and the row list is the changed rows only; line 3 carries the split as re-derived, with every Effort bracket that moved with it.

**Identical rows may collapse to one digest line with a count** — `M1–M12 W haiku ~15k ea — transform`. That is the one collapse the digest permits, and it exists because a per-row backend split makes wide plans likelier: a 14-row plan cannot otherwise fit its rows in the twelve lines the box gives. Collapse only rows that are genuinely identical bar the id, and never collapse a row whose backend differs from its neighbours' — that is the difference the user is reading.

## Task brief (Step 3) — every dispatch

```text
Role: <implementer | explorer | reviewer(lens) | verifier | judge>
Objective: <one sentence>
Inputs / source of truth: <file paths, briefs, diffs — the agent starts blank; no transcript. Name the
                          exact ground truth: files, line numbers, URLs, the measured baseline, the
                          harness to measure with. A brief that must rediscover its ground truth costs
                          ~2× and fails more>
Scope and relevant files: <explicit>
Allowed writes: <none | exact paths | worktree path>
Allowed tools: <the tool scope this objective needs — e.g. "read + search only, no network, no shell"
               | "repo tools + Bash for the test command only" | "inherit". Reviewers and explorers:
               deny network and shell unless the objective names a use for them. Read-only writes plus
               open network access is not read-only.>
Per-unit caps: <`maxTurns` / `permissionMode` where a saved agent file sets them, else "none — plain
               dispatch". Unlike the two lines above, these BIND. A unit that hits `maxTurns` returns
               `blocked`, not failed, and charges no rung on the failure ladder.>
Must not do: <boundaries, non-goals, no nested delegation unless granted>
Baseline / snapshot: <revision, diff, or file manifest being worked against>
Done when: <one falsifiable sentence>
Return format: the agent report below, ≤1–2k tokens; put bulk output in <scratch path>
               (omit the scratch path for a unit that cannot write — `explorer` and
               `web-researcher` distill instead; a scratch path in their brief is a briefing error)
Model: <the exact value passed to this dispatch, matching the approved plan row; tier in brackets.
        On a saved-agent dispatch, its frontmatter model is that value unless you deliberately override>
Effort: <the level, always, plus the control setting it — agent-file frontmatter, Workflow `agent()`,
        or "no control" on a plain dispatch. Matches the approved plan row.>
```

**When an acceptance suite runs** (`patterns.md` #10), three briefs change shape. The blind author's
`Inputs` are the requirement text and the approved criteria, and nothing else — and it is the one
dispatch class exempt from "name the decisions already made" (SKILL.md Step 3): it receives the
decisions' observable consequences, never the decisions. The implementer's brief carries the criterion
IDs and never the suite path. The verifier's brief carries the suite path and the per-case verdict set,
pass / fail / `Awaiting human`, with evidence required on each.

## Agent report — required return shape

```text
Status: completed | partial | blocked
Result: <concise conclusion or changes made>
Evidence: <file:symbol refs, commands run, reproductions, measurements>
Files changed: <exact list, or none>
Checks run: <command → outcome>
Uncertainty: <unverified assumptions, remaining risks>
Recommended next action: <if any>
```

The parent validates material claims against repo state or tool output. A summary is a handoff, not proof.

## Finding schema (reviews)

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

## Risk rubric (pick topology by risk, not size)

Axes: failure impact; breadth of coupling; novelty/uncertainty; reversibility; strength of automated verification; external compatibility or human-decision dependencies.

**Hard triggers → treat as high risk regardless of other axes:** data/save migration, security or credentials, networking or deterministic simulation, public API compatibility, irreversible conversion, a core performance budget, behavior with no reliable test oracle. Reclassify mid-task if exploration reveals a different blast radius.

- **Low**: parent or one worker; focused checks; review only if behavior is non-obvious.
- **Medium**: ≤2 explorers for real unknowns; one writer; one lens-specific reviewer; targeted fix verification.
- **High**: bounded exploration; optional plan critic, and a blind acceptance suite (`patterns.md` #10 — offer it at the gate, never assume it); each justified by a named trigger; one writer per isolated tree; staged checks; two independent reviewers on the same frozen diff; parent triage; targeted regression verification; human checkpoint for subjective criteria. One hard trigger points the other way: "behavior with no reliable test oracle" recommends no suite, with verification routed to human checkpoints and the domain's other evidence.

## Shared-tree snapshot protocol (any writer present)

1. **Baseline** — record starting revision, dirty files, task-owned files. Unrelated dirty changes are never the agent's work and must survive. **This is the only recovery map for delegated writes.** `/rewind` checkpoints the tree before each user prompt but does not track subagent edits (harness reference, Cautions), so once a writer has run there is no automatic snapshot to fall back on. Baselining is the substitute, not a formality.
2. **Write lease** — one named writer; everyone else source-read-only.
3. **Stabilize** — writer finishes; run focused checks; capture the diff or changed-file manifest.
4. **Freeze** — no source changes while reviewers inspect the candidate.
5. **Triage** — merge and dedupe findings by root cause (not wording) before any fix.
6. **New lease** — one writer for accepted fixes (prefer the original; a fresh one needs the complete handoff).
7. **Verify** — targeted checks on fixes and regressions. A new full review only if design materially changed.

No manufactured commits just to make a snapshot — a stable diff or file-hash manifest is enough. Non-git projects: record the task-owned file list with before/after hashes.

Two lease cases the seven steps don't cover. If the parent takes a writer unit inline, the lease **moves to the parent** — it does not lapse, and no other writer starts. If the run pauses to ask the user, the lease **freezes** where it is. Log either in the ledger, because a lease whose holder is unrecorded is the same as no lease.

## Ledger (scratch file, e.g. `<scratch>/subagents-ledger.md`)

```text
# Ledger: <task> — <date>
Cap/budget/backend split: <cap, budget, and which row ids ran scripted vs hand-batched>
Plan: <approved plan or pointer>
| id | unit | agent/thread | model used | state | evidence | actual tokens |
Decisions & dropped disagreements: <every one, with reason — silent discard forbidden>
Plan amendments: <any change to an approved row — model, effort, scope, count — with the reason and when>
```

Update on every state change. After compaction or a new session, the ledger plus the repo — not memory of the conversation — is the source of continuity.

## Final message (Step 6) — Result first, then the Orchestration Report

Two parts, in this order. The order is structural, not a preference.

1. **Result** — the deliverable's own summary, in prose, standing on its own. What the user asked for,
   answered, at whatever length the answer needs. Someone who reads only the opening should have the
   answer in hand, not a pointer to one.
2. **The Orchestration Report block** below. It never opens the message.

The split exists because `OUTCOME:` is one line inside a template, and one line inside a template
compresses a deliverable into a pointer. Given a Result section above it, `OUTCOME:` may point up at
that section instead of restating it.

```text
OUTCOME: <one line, or a pointer up to the Result section — never a replacement for it>
Topology: <pattern, N agents, why> (or "solo — recommended and approved: <reason>")
Agents: <one line each: unit → model actually used → status → key evidence>
Cost: <N agents, ~tokens actual vs ~estimate, wall clock — say so if no token counts were visible,
       in which case the agent-count and wall-clock rails were the ones in force>
Plan deviations: <every row that ran with a different model, effort, count, or scope than approved, and why — or "none".
       A backend the USER chose at the gate is not a deviation: name which `go` option ran, and the
       Effort brackets it set or revoked, under `Topology:` instead>
Findings: <accepted/rejected/deferred/user-decision counts + the ones that matter>
Verification: <checks run and outcomes. Where an acceptance suite ran, separate MEASURED passes — a
                     command executed — from JUDGED passes, where a case was read and ruled on. A judged
                     pass is a reviewer's opinion with a case number on it. `Awaiting human` cases count
                     as neither, and any machine-verifiable case that downgraded is named here>
Coordination check: <what depended on the agents being independent — a disagreement, a refutation, a
                     cross-angle finding — or "nothing; one agent at this budget would likely have
                     matched it". Answer honestly; "the fan-out bought nothing" is a real result.>
Gaps: <anything bounded, sampled, skipped, or unverified — explicitly>
Awaiting human: <subjective/product checkpoints, if any>
```

Then append one row to `../calibration.md` — the run's actuals, whether or not the estimate held, plus the lesson a future run needs in the note column: a negative coordination verdict, a failure-ladder stall and what unstuck it, or a gate call you would reverse.
