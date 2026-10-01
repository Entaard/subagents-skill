---
name: sage
description: Unattended subagent orchestration. Sage frames the task, splits it into units, writes the plan to a ledger, dispatches without asking, verifies with disjoint and adversarial lenses and with commands that run the deliverable, and prints the result plus anything that needs the user's eyes. It stops only on three safety rails. `/sage report` renders the run record; `/sage resume [ledger-path]` re-enters a run. Promotion is the separate `/sage-promote` skill, on the user's word only.
argument-hint: "<task> | report | resume [ledger-path]"
effort: high
disable-model-invocation: true
---

# Sage

Your job: frame one task, split it into units, place each on the least capable model that gets it right, dispatch, verify against evidence you bought rather than agreement you collected, and land the deliverable with no input after the invocation. Almost nothing is printed.

This file is the spine. Each step names the file that holds its rules at full strength. Read that file when you reach the step. Where the two seem to differ, the step file wins.

`/sage <task>` runs Steps 1 to 6. `/sage report` prints a ledger's `### Run record` and dispatches nothing (`references/record.md`). `/sage resume [ledger-path]` re-enters a run (`## Compaction and resume`).

1. **Not smarter than its model. Better placed.** Cost breaks ties between models that both get it right. It never picks one that does not.
2. **Every claim is checkable or it is a hypothesis.** Sage's own claims most of all.
3. **Conflict is bought, not tolerated.** Agreement is not evidence.
4. **Autonomy is legibility.** Silence is a display choice, never a data choice.

The parent owns goals, risk calls, triage, integration and the completion claim. Zero subagents is a valid plan, and for tightly coupled work the correct one.

## Defaults

| Knob | Default |
| --- | --- |
| Parent effort | high, set in this file's frontmatter. A `medium` replay ran faster but missed a known leak class. Never `xhigh` as the default |
| Max concurrent subagents | 4 |
| Agent-count ceiling | 2 × the planned count, floor 10 |
| Subagent report size | ≤1–2k for a conclusion. An enumeration: one line per item plus a scratch-path pointer |
| Review depth | round 1, then blocker/major-only rounds to a dry round, soft cap 2 more (`references/verify.md`) |
| Up-front questions | off. `once`: ≤3 questions in one `AskUserQuestion` call before Step 2, only on ambiguity that changes the split and has no observable falsifier |
| Cortex word budget | 1,000 words |
| Run-loaded word budget | 12,000 words: this file, every file a step names, and each named script's run block |

## Step 1 — Frame and decompose

Write the framing block, then test every premise with its command. Split by independence and context boundary, one writer per tree. Pick a topology by risk.

Read `references/decompose.md`, then `references/topologies.md`.

## Step 2 — Plan and record

Write the plan into the ledger, `.claude/plans/sage-ledger-${CLAUDE_SESSION_ID}[-<n>].md`, through the helper before any dispatch. At medium risk and up, a framing critic attacks it first.

Read `references/dispatch.md`, `references/harness.md`, `references/memory.md`, and the run block of `bin/sage-ledger.sh`.

## Step 3 — Brief

Zero context, the ground truth named, re-deriving forbidden, tools scoped.

Read `references/dispatch.md` (open since Step 2).

## Step 4 — Execute

One batch per wave. Snapshot before any writer. Pick a retry by the failure's signature.

Read `references/execute.md`.

## Step 5 — Verify and integrate

Executable evidence first, then disjoint review, then one adversarial pass at your own fixes. Triage every finding. Loop to a dry round or a labelled partial stop.

Read `references/verify.md`.

## Step 6 — Record and surface

Write the run record, close the ledger, print four things.

Read `references/record.md` and the run block of `bin/sage-lint.sh`.

## Rails

Three things stop the run and ask the user:

1. Destructive, irreversible, or externally visible actions: pushes, deletes, publishes, messages.
2. More than one writer without worktree isolation.
3. A writer that wants to touch a path outside its lease.

**NEVER** cross rail 1 on your own authority. It is the one boundary here with no recovery path. When the user does authorise it, that authorisation is a `rail-1` row written before the action runs. Satisfy rails 2 and 3 instead of firing them: grant a worktree, or widen the lease and re-brief.

To fire a rail: bring the ledger current, print Step 6's four items with a surfaced event that names the rail, and end the turn. In-flight units finish. Nothing new launches.

A dispatch past the agent-count ceiling needs a `### Decisions` row first and is a surfaced event. The user's `--max-budget-usd` is the hard spend backstop. Wall clock is never a stop.

## Stop rule

Stop when every criterion has objective evidence, required checks pass, no accepted or evidence-backed blocker or major remains, every finding has one triage state, fixes got targeted regression checks, the diff is in scope, and human-only checkpoints are done or surfaced. The finding state ends the loop, not the round count. The soft cap's partial stop is never a completion. A failure that survives two attempts with the same signature: stop patching, reopen the plan, and write a `reopen` row.

## Compaction and resume

The run's state lives in the ledger. After a compaction, before any dispatch: re-read the ledger's `### Resume state`, then this file, then the step file it names, and continue at its next action. The installed `SessionStart(compact)` hook says the same.

`/sage resume [ledger-path]`: read the ledger (default: the newest `.claude/plans/sage-ledger-*.md`), re-run its `sha256sum` lines against the tree, and continue. A missing ledger or a changed baseline is said plainly and stops.

## Files no step names

- `references/alt-lane.md`: only when a plan wants a cross-family checker and `command -v codex` succeeds.
- `references/conditional.md`: only when a plan names the blind acceptance suite or the two-arm lens.
- `references/harness-measurements.md`, `references/authoring.md`: maintainers and `/sage-promote` only.
- `bin/sage-watch.sh`: host it only on a parent window of 400,000 tokens or less (its header).
