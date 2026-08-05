# Contracts and templates

Copy these; don't improvise the structure. Fields may be trimmed when genuinely irrelevant, never renamed.

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

Cap: <N> concurrent.  Budget: ~<total> tokens, ~<min> wall clock.
Backend: hand-batched | via Workflow — <which, and why; SKILL.md Step 3. Hand-batched unless the shape fits>.
Risks: <top 1–3. With any writer present, name the `/rewind` gap explicitly — checkpointing does not
        track subagent edits, so the manual baseline is the only recovery map (harness ref, Cautions)>.
Solo alternative: <what one strong agent inline would cost/miss — include when the call is close>.
Recommended: <the default answer. Name the option, not just "go", whenever the backend block puts two
              options behind that word>.
```

**Model column:** the exact value you will pass, tier in brackets. Not a tier alone — a tier hides whether that is `haiku` or `sonnet`, and the user is approving what runs. Resolve tier → model against the live session first (procedure in `claude-code.md`). Run that file's `CLAUDE_CODE_SUBAGENT_MODEL` check before writing this column: a set override outranks both the dispatch param and agent frontmatter, and makes every cell in it false.

**Effort column:** the level *and* the mechanism setting it. A saved-agent dispatch gets a real one — `low (explorer)`, `high (verifier)`, `medium (web-researcher)` — because effort is frontmatter there. Under the `Workflow` backend the mechanism is `agent({effort})`, real on *every* row — write `high (workflow)`. Write `— (no control)` only for a **hand-batched plain Agent call**, which is the one path with no lever. A bare `low` is a promise nothing keeps.

Estimating tokens: exploration/lookup ~15–40k; implementation ~40–150k; focused review ~30–80k per agent. **These bands are priors and known to run low — read `../calibration.md` first.** Web fetches and large-corpus reads have run 2–5× the band; that file's own correction factor is a different number, not a substitute for this one. Where a row covers the task class, quote its actuals instead of the band and name the row. Append this run's actuals at Step 7, hits included.

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
- **High**: bounded exploration; optional plan critic / independent test designer (each justified by a named trigger); one writer per isolated tree; staged checks; two independent reviewers on the same frozen diff; parent triage; targeted regression verification; human checkpoint for subjective criteria.

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

## Orchestration Report (Step 7)

```text
OUTCOME: <what the user asked for, answered first>
Topology: <pattern, N agents, why> (or "solo — gate failed: <reason>")
Agents: <one line each: unit → model actually used → status → key evidence>
Cost: <N agents, ~tokens actual vs ~estimate, wall clock — say so if no token counts were visible,
       in which case the agent-count and wall-clock rails were the ones in force>
Plan deviations: <every row that ran with a different model, effort, count, or scope than approved, and why — or "none">
Findings: <accepted/rejected/deferred/user-decision counts + the ones that matter>
Verification: <checks run and outcomes>
Coordination check: <what depended on the agents being independent — a disagreement, a refutation, a
                     cross-angle finding — or "nothing; one agent at this budget would likely have
                     matched it". Answer honestly; "the fan-out bought nothing" is a real result.>
Gaps: <anything bounded, sampled, skipped, or unverified — explicitly>
Awaiting human: <subjective/product checkpoints, if any>
```

Then append one row to `../calibration.md` — the run's actuals, whether or not the estimate held, plus the lesson a future run needs in the note column: a negative coordination verdict, a failure-ladder stall and what unstuck it, or a gate call you would reverse.
