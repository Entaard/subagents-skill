# Contracts and templates

Copy these; don't improvise the structure. Fields may be trimmed when genuinely irrelevant, never renamed — the parent scans these shapes across many reports, and a renamed field reads as a missing one.

## Orchestration Plan (Step 3)

```text
TASK: <one line>
MODE: manual | auto | plan        RISK: low | medium | high (rubric below)
TOPOLOGY: <pattern name or custom> — <one-line why>
PARENT: <the model you are running on> — does synthesis, triage, completion claim

| # | Unit (done when)            | R/W | Model (tier)      | Effort (via)     | Flow       | Isolation      | Est. tokens |
|---|-----------------------------|-----|-------------------|------------------|------------|----------------|-------------|
| 1 | ...                         | R   | haiku (fast)      | low (explorer)   | bg, batch1 | —              | ~20k        |
| 2 | ...                         | W   | sonnet (standard) | — (no control)   | bg, after1 | write lease    | ~80k        |
| 3 | review of #2 (lens: ...)    | R   | opus (frontier)   | high (verifier)  | bg, after2 | frozen diff    | ~50k        |

Cap: <N> concurrent.  Budget: ~<total> tokens, ~<min> wall clock — basis: <calibration row, or the band>.
Backend: hand-batched | via Workflow — <which, and why; SKILL.md Step 3. Both are offered whenever the
         Workflow tool exists; hand-batched is the default unless the shape favours a script>.
Acceptance suite: light | full | none — recommended: <which>, because <one line>. <Omit this line and
         the next when the plan has no writer unit or nothing checkable; say which instead.
         `patterns.md` #10. Its cost is a guess, not a band — see the estimating note below>
         Criteria: R1 <text>; R2 <text>; ...
Risks: <top 1–3. With any writer present, name the `/rewind` gap explicitly — checkpointing does not
        track subagent edits, so the manual baseline is the only recovery map (harness ref, Cautions)>.
Solo alternative: <what one strong agent inline would cost/miss — include when the call is close>.
Recommended: <the default answer. Name the option, not just "go", whenever the backend block puts two
              options behind that word>.
```

**Model column:** the exact value you will pass, tier in brackets. Not a tier alone — a tier hides whether that is `haiku` or `sonnet`, and the user is approving what runs. Resolve tier → model against the live session first (procedure in `claude-code.md`). Run that file's `CLAUDE_CODE_SUBAGENT_MODEL` check before writing this column: a set override outranks both the dispatch param and agent frontmatter, and makes every cell in it false.

**Effort column:** the level *and* the mechanism setting it. A saved-agent dispatch gets a real one — `low (explorer)`, `high (verifier)`, `medium (web-researcher)` — because effort is frontmatter there. Under the `Workflow` backend the mechanism is `agent({effort})`, real on *every* row — write `high (workflow)`. Write `— (no control)` only for a **hand-batched plain Agent call**, which is the one path with no lever. A bare `low` is a promise nothing keeps.

**Acceptance suite line** (`patterns.md` #10): the criteria go in as **text, verbatim, not a count**. This line is where the user co-signs the expectations, and an invented expectation has to be readable to die at the gate. Phrase each criterion at the requirement's observable surface — no module names, no data stores, no mechanism choices — because a design noun inside a criterion carries the parent's design straight through the blind author's firewall.

**Print this block as message text immediately before the gate question**, then attach only a digest of it to the `AskUserQuestion` preview. The preview box clips to `terminal rows − 26` lines and **drops the tail**, which is where `Risks:`, `Solo alternative:` and `Recommended:` live. Printed text does not clip. See `claude-code.md`, "The gate dialog", for the measured budgets.

Estimating tokens: exploration/lookup ~15–40k; implementation ~40–150k; focused review ~30–80k per agent. An acceptance suite adds ~15–35k for the blind author (`light`), and ~30–60k more for the compile unit and its red-check (`full`) — both **guesses, not bands**: no calibration row covers either unit class yet, and the first figure is borrowed from the nearest measured shape, an anchored single-corpus brief. Say so at the gate rather than presenting them as evidence. **These bands are priors and known to run low — read `../calibration.md` first.** Web fetches and large-corpus reads have run 2–5× the band; that file's own correction factor is a different number, not a substitute for this one. Where a row covers the task class, quote its actuals instead of the band and name the row. Append this run's actuals at Step 7, hits included.

### Fitting the plan to the gate surface

Three rules shrink the block itself. Apply them before printing, because a shorter block also makes a better digest:

- **One physical line per row.** A cell holding a sentence turns one row into three or four lines. Keep a short unit name in the cell and move every `done when` clause to a numbered list under the table, keyed by row id.
- **A constant column is not a column.** Where every row shares a value, delete the column and state it once above the table: `All rows: background, read-only, wave 1.` Effort, Flow and Isolation collapse this way in most plans. A column that varies stays, however wide.
- **Keep in the table only what the user audits:** id, unit, R/W, model, effort, est. tokens. Anything that would not change the answer goes below the table.

Where the block still runs past ~30 lines, save it to the session scratchpad as well and put that path in the digest. An editor has no width or height budget at all.

The digest attached to each `go` option is a summary, not a second copy. Fit it to **12 lines and 60 columns**, and keep this order. A clipped reader then loses the rows, which are printed above in full, rather than the recommendation:

```text
# the preview on "go — via Workflow", where the recommendation is the other option
8 agents (5 parallel) · ~615k · ~55 min · cap 5
Recommended: hand-batched — exploratory; steering beats saved context
This option: scripted. Real effort per row. No mid-run steering.
             Writer rows auto-accept their edits.
Top risk: the fix changes sync behaviour on every build
Full plan printed above ↑   (saved: <path>)

A1 R opus   ~90k  delivery + dedup audit
A2 R opus   ~80k  classifier precision audit
W  W opus     —   parent writes the fix inline
V1 R opus   ~90k  compliance review of the frozen diff
```

On an `adjust` re-ask the shape holds and the row list is the changed rows only. Where two `go` variants exist, line 3 is what differs between them, so it differs per option.

## Task brief (Step 4) — every dispatch

```text
Role: <implementer | explorer | reviewer(lens) | verifier | judge>
Objective: <one sentence>
Inputs / source of truth: <file paths, briefs, diffs — the agent starts blank; no transcript>
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
Effort: <level and the control setting it — agent-file frontmatter or Workflow `agent()` — or "not settable here">
```

**When an acceptance suite runs** (`patterns.md` #10), three briefs change shape. The blind author's
`Inputs` are the requirement text and the approved criteria, and nothing else — and it is the one
dispatch class exempt from "name the decisions already made" (SKILL.md Step 4): it receives the
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
Mode/cap/budget: ...
Plan: <approved plan or pointer>
| id | unit | agent/thread | model used | state | evidence | actual tokens |
Decisions & dropped disagreements: <every one, with reason — silent discard forbidden>
Plan amendments: <any change to an approved row — model, effort, scope, count — with the reason and when>
```

Update on every state change. After compaction or a new session, the ledger plus the repo — not memory of the conversation — is the source of continuity.

## Final message (Step 7) — Result first, then the Orchestration Report

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
Topology: <pattern, N agents, why> (or "solo — gate failed: <reason>")
Agents: <one line each: unit → model actually used → status → key evidence>
Cost: <N agents, ~tokens actual vs ~estimate, wall clock — say so if no token counts were visible,
       in which case the agent-count and wall-clock rails were the ones in force>
Plan deviations: <every row that ran with a different model, effort, count, or scope than approved, and why — or "none">
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
