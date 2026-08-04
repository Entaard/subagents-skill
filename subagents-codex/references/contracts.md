# Contracts and templates

Copy these; don't improvise the structure. Fields may be trimmed when genuinely irrelevant, never renamed.

## Orchestration Plan (Step 3)

```text
TASK: <one line>
MODE: manual | auto | plan        RISK: low | medium | high (rubric below)
TOPOLOGY: <pattern name or custom> — <one-line why>
PARENT: <your model and effort> — does synthesis, triage, completion claim

| # | Unit (done when)            | R/W | Model (tier)             | Effort | Flow       | Isolation      | Est. tokens |
|---|-----------------------------|-----|--------------------------|--------|------------|----------------|-------------|
| 1 | ...                         | R   | gpt-5.6-luna (fast)      | low    | bg, batch1 | —              | ~20k        |
| 2 | ...                         | W   | gpt-5.6-terra (standard) | medium | bg, after1 | write lease    | ~80k        |
| 3 | review of #2 (lens: ...)    | R   | gpt-5.6 (frontier)       | high   | bg, after2 | frozen diff    | ~50k        |

Cap: <N> concurrent.  Budget: ~<total> tokens, ~<min> wall clock.
Risks: <top 1–3>.
Solo alternative: <what one strong agent inline would cost/miss — include when the call is close>.
Recommended: <the one-word default answer>.
```

**Model column:** the exact model you will name when spawning, with the tier in brackets. Not a tier alone. A tier is how you choose, but the user approving this plan can only audit a name, and "fast tier" does not say which model arrives. Resolve tier → model against the live session before writing the row (procedure in `codex.md`).

This matters more in Codex than in a tool-call harness. Delegation is natural language, so a dispatch that does not name a model silently inherits `default_subagent_model` from config. A plan written in tiers alone hides that entirely.

**Effort column:** a real per-spawn value in Codex, so give it a level rather than a dash. State the level you will actually pass, and remember the custom agent file's `model_reasoning_effort` overrides your spawn value if you spawn by name.

Estimating tokens: exploration/lookup ~15–40k; implementation ~40–150k; focused review ~30–80k per agent. These are coarse; report actuals afterward and calibrate.

## Task brief (Step 4) — every dispatch

```text
Role: <implementer | explorer | reviewer(lens) | verifier | judge>
Objective: <one sentence>
Inputs / source of truth: <file paths, briefs, diffs — the agent starts blank; no transcript>
Scope and relevant files: <explicit>
Allowed writes: <none | exact paths | worktree path>
Must not do: <boundaries, non-goals, no nested delegation unless granted>
Baseline / snapshot: <revision, diff, or file manifest being worked against>
Done when: <one falsifiable sentence>
Return format: the agent report below, ≤1–2k tokens; put bulk output in <scratch path>
Model / effort: <the exact model name and effort level you are passing, matching the approved plan row; tier in brackets>
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

1. **Baseline** — record starting revision, dirty files, task-owned files. Unrelated dirty changes are never the agent's work and must survive.
2. **Write lease** — one named writer; everyone else source-read-only.
3. **Stabilize** — writer finishes; run focused checks; capture the diff or changed-file manifest.
4. **Freeze** — no source changes while reviewers inspect the candidate.
5. **Triage** — merge and dedupe findings by root cause (not wording) before any fix.
6. **New lease** — one writer for accepted fixes (prefer the original; a fresh one needs the complete handoff).
7. **Verify** — targeted checks on fixes and regressions. A new full review only if design materially changed.

No manufactured commits just to make a snapshot — a stable diff or file-hash manifest is enough. Non-git projects: record the task-owned file list with before/after hashes.

## Ledger (scratch file, e.g. `<scratch>/subagents-ledger.md`)

```text
# Ledger: <task> — <date>
Mode/cap/budget: ...
Plan: <approved plan or pointer>
| id | unit | agent/thread | model + effort used | state | evidence | actual tokens |
Decisions & dropped disagreements: <every one, with reason — silent discard forbidden>
Plan amendments: <any change to an approved row — model, effort, scope, count — with the reason and when>
```

Update on every state change. After compaction or a new session, the ledger plus the repo — not memory of the conversation — is the source of continuity.

## Orchestration Report (Step 7)

```text
OUTCOME: <what the user asked for, answered first>
Topology: <pattern, N agents, why> (or "solo — gate failed: <reason>")
Agents: <one line each: unit → model + effort actually used → status → key evidence>
Cost: <N agents, ~tokens actual vs ~estimate, wall clock>
Plan deviations: <every row that ran with a different model, effort, count, or scope than approved, and why — or "none">
Findings: <accepted/rejected/deferred/user-decision counts + the ones that matter>
Verification: <checks run and outcomes>
Gaps: <anything bounded, sampled, skipped, or unverified — explicitly>
Awaiting human: <subjective/product checkpoints, if any>
```
