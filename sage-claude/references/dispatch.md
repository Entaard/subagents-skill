# Plan, brief, and the ledger

Copy the shapes below. Trim a field only where it does not apply, and never rename one.

## Step 2 — Plan and record

Write the whole plan into the ledger before any dispatch. Never present it as a message.

1. **Read first.** `harness.md` for the agent roster. `alt-lane.md` only when an alt agent is in your live agent list. Then memory (`memory.md`).
2. **Create the ledger** with the helper (`## The ledger` below). It writes `Started:`, the section skeleton and your framing fields.
3. **Add one Plan row per unit** with `sage-ledger.sh unit`. Every row names its agent and model, reader or writer, a done-when sentence, and its flow.
4. **Plan the framing critic** at medium risk and above (`topologies.md`). It attacks the framing block and the criteria before the first writer.
5. **Build the measurement harness first** where the task turns on a number. Reproduce the central claim yourself before you brief anyone, and give every unit that reports the same metric one shared harness.
6. **Write the wall target**: `Wall target: <n> min`, from the same-shape rows in `runs.log` or from the task class. It is advisory. `bin/sage-clock.sh`, where installed, prints the elapsed time against it.
7. **Choose the acceptance suite**: `full`, `light` or `none`, with its deciding signal (`conditional.md`).
8. **A diff to be reviewed, with the `diff-review` skill installed:** put its Spec and Standards reader briefs into the plan verbatim as two reader rows. The Standards row carries that skill's smell baseline verbatim, because nothing else hands that reader the list.
9. **Record every resolved ambiguity** as an `assumption` row with `sage-ledger.sh decision`, when you resolve it. Its reason names what else was plausible and how a wrong choice would show. Ambiguity that changes the split is also a surfaced line at Step 6.

Where the call to fan out is close, write a `Solo alternative:` field: what one strong agent inline would cost or miss. Writing it is what keeps fan-out from being automatic.

The plan is complete when every unit has an agent, a reader/writer class and a done-when sentence. Step 3 begins in the same turn.

## Step 3 — Brief

Write every dispatch against the task brief below.

- **The agent starts with zero context.** Name the files, the boundaries, the output shape, and the decisions already made. Two units that decide one question differently is how coupled work fails.
- **Name the ground truth outright, and forbid re-deriving it**: exact files, line numbers, URLs, measured baselines, and the harness to measure with. Such briefs have run about 2–2.5× cheaper and failed less. A brief that named the payload but let the unit build its own decoder lost the discount.
- **A blind acceptance-suite author is the one exception to naming the decisions.** It gets the decisions' observable consequences, never the decisions (`conditional.md`).
- **Grep the claim before you brief it, and before you assert it.** A brief asserts that a file, symbol, number or state exists only after one command proved it. The rule reaches your own completion claim: `ls` every path the deliverable cites before you claim it. Prove a negative grep on a fixture that should match before you report a zero. Split tab-separated fields with `cut -f` or `awk -F'\t'`, never with `[^\t]`, which GNU grep reads as "not a backslash and not t".
- **A reader's structural claim is a lead, not ground truth.** Fetch the primary source yourself and grep it.
- **Hand off via artifacts, never via transcript.** Point at files and require summaries back.
- **Record each dispatch's `agentId` in its Plan row when it returns.** It is your only handle for `SendMessage` and `TaskStop`.
- **Scope the tools, not just the writes.** An agent that cannot write source but can fetch URLs and run shell is not contained. Only a saved agent file enforces a tool scope. **Give every unit that holds Bash a scratch path outside the repo**, and name it in the brief. A Bash-holding reviewer briefed "read-only" once wrote test files into the tree.
- **A unit's toolset comes from its agent file, not its self-report.** A unit without the Skill tool reaches guidance only through a path it can `Read`. Name the file path, never the slash command.
- **A repo's own `PreToolUse` hooks gate your units too.** Satisfy the gate yourself, once, before the wave. A gate you cannot satisfy blocks every unit whose only file reader is a tool the hook matches. Read the hook's matcher, and hand such a unit scratch `.txt` copies outside the repo, each with its source path and line numbers.
- **`maxTurns` in an agent file is the only per-unit turn cap.** Set it only where a role's shape is known, because a low cap truncates silently. A unit that hits it is `blocked`, not failed, and charges no rung.
- **Reviewers are read-only roles.** Nested delegation is off unless you grant a self-contained subtree.

Choose the agent from the unit's properties. The `model:` rule for a saved agent is in `harness.md`.

| Unit property | Agent |
| --- | --- |
| Search, bulk reading, mechanical enumeration | `explorer` |
| Outside sources | `web-researcher` |
| Standard implementation or integration | `implementer` |
| Ambiguous or long-horizon writing, or a handed-off parent row | `implementer-frontier` |
| Review, verification, refutation | `verifier`, or an alt checker (`alt-lane.md`) |
| Synthesis, triage, the completion claim | the parent |

**The unit's step count is a second axis.** A cheaper seat on multi-step work that must find its own path can take 2–3× the turns and cost more. A brief with exact paths and commands keeps the cheap seat cheap.

On a retry, take the rung the failure's signature earns (`execute.md`).

## Task brief

```text
Role: <explorer | implementer | reviewer(lens) | verifier | judge>
Objective: <one sentence>
Inputs / source of truth: <exact files, line numbers, URLs, the measured baseline, the harness to measure with — not to be re-derived>
Scope and relevant files: <explicit>
Allowed writes: <none | exact paths | worktree path>, plus <scratch path outside the repo> for any unit with Bash
Allowed tools: <"read + search only, no network, no shell" | "repo tools + Bash for <commands>" | "inherit">
Must not do: <boundaries, non-goals, no nested delegation unless granted>
Baseline / snapshot: <revision, diff, or file manifest>
Done when: <one falsifiable sentence>
Agent: <saved agent name — its file pins the model and effort>
Return format: the agent report below, ≤1–2k tokens for a conclusion; an enumeration returns one line per item plus a pointer to <scratch path>. As text: the harness blocks a subagent's report-file write
```

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

## Findings and triage

The finding schema and the blocker/major/minor definitions live in the `verifier` agent file. A review row dispatched as a plain agent must carry them in its brief. A finding id must match the shape the lint recognises (`bin/sage-lint.sh` header), or `triage-orphan` skips it.

Triage states: **accepted / rejected with evidence / deferred with owner / user decision.**

## Risk rubric

Axes: failure impact; breadth of coupling; novelty; reversibility; strength of automated verification; external or human-decision dependencies.

**Hard triggers, which make a task high risk whatever the other axes say:** data or save migration, security or credentials, networking or deterministic simulation, public API compatibility, irreversible conversion, a core performance budget, behavior with no reliable test oracle. Reclassify when exploration shows a different blast radius.

- **Low:** the parent or one worker; focused checks; review only if the behaviour is not obvious.
- **Medium:** ≤2 explorers for real unknowns; the framing critic; one writer; one lens-specific reviewer; targeted fix verification.
- **High:** everything in medium, plus the blind acceptance suite, one writer per isolated tree, staged checks, two independent reviewers on the same frozen diff, and a human checkpoint for subjective criteria.

## Snapshot protocol

It runs whenever any writer is present, the parent included.

1. **Baseline:** record the starting revision, dirty files and task-owned files, with `sage-ledger.sh restamp … -- <files>`. Unrelated dirty changes must survive. This is the only recovery map once a writer has run, so take it before the writer starts, not after something looks wrong. A name is not a recovery path: copy task-adjacent untracked files into the scratchpad now.
2. **Write lease:** one named writer. Everyone else is source-read-only.
3. **Stabilise:** the writer finishes, focused checks run, and you capture the diff.
4. **Freeze:** no source changes while reviewers inspect the candidate.
5. **Triage:** merge and dedupe findings by root cause before any fix.
6. **New lease:** one writer for the accepted fixes.
7. **Verify:** targeted checks on the fixes and regressions (`verify.md`).

No manufactured commits: a stable diff or a file-hash manifest is enough. The parent taking a writer row inline **moves the lease to the parent**. A rail that stops the run **freezes the lease**. Record either in the lease line of `### Resume state`.

## The ledger

One file, `.claude/plans/sage-ledger-<session-id>.md`, where the id is the one `../SKILL.md` Step 2 names. Never derive it from a path: the elapsed-time hook finds the ledger by the harness's own session id. Its readers are you after a compaction, `/sage resume`, `/sage report`, and the elapsed-time hook. It is not written for the user.

- **Where:** before the first write, run `git check-ignore -q .claude/plans/`. Exit 1 means the file is visible to `git status`: write there anyway and print one line naming the path and the fix (`.claude/plans/` in `.gitignore`). Never edit a user's `.gitignore` unasked. Use the session scratchpad only when `.claude/plans/` is not writable, and print the path.
- **How:** write it only through `bin/sage-ledger.sh`. Never hand-edit it with a Python or sed replace. Read the helper's run block once: `sed -n '1,/^# END RUN BLOCK/p' ~/.claude/skills/sage/bin/sage-ledger.sh`.

```sh
L=.claude/plans/sage-ledger-<session-id>.md
H=~/.claude/skills/sage/bin/sage-ledger.sh
printf '%s\n' "ASK: <verbatim>" "PURPOSE: ..." "PREMISES: ..." "DELIVERABLE: ..." "APPROACHES: ..." \
  "RISK: ..." "TOPOLOGY: ..." "PARENT: <your model>" "Wall target: <n> min" "Acceptance suite: ..." "Criteria: R1 ...; R2 ..." \
  | $H init "$L" "<one-line task>"
$H unit "$L" 1 unit="<unit>" done-when="<sentence>" rw=R agent="explorer (claude-sonnet-5-5)" flow="bg, batch1" state=planned
$H decision "$L" assumption "<what I chose>" "<what else was plausible; how it would show if wrong>"
$H restamp "$L" step="4 — execute.md" next="<one line>" lease="<holder|frozen|none>" baseline="<rev>" -- <task-owned files>
$H finding "$L" F1 severity=major stage=r1 author=parent location="<file:line>" evidence="<text>"
$H finding "$L" F1 triage="accepted"
```

The four working sections:

- **`### Plan`:** the framing fields, the run fields, and one unit table. Columns: id, unit, done-when, rw, agent (model), flow, state, agentId, evidence. State ∈ `planned | running | reported | blocked | failed | abandoned | inline`.
- **`### Decisions`:** one table for every assumption, deviation, dropped disagreement, discarded approach, open question, reopen and rail-1 authorisation, keyed by a `kind` column. A plan change is a `deviation` row, and you update the affected unit row in place. Silent discard is forbidden. A later user correction is a new row that names the row it corrects.
- **`### Findings`:** one row per finding, with a `stage` (frame, plan, r1, r2+, final-run, post-close, user) and an `author` (parent, unit, pre-existing). **The residual same-family maker/checker bias disclosure has its only home here**, wherever no cross-family checker was available (`verify.md`).
- **`### Run record`:** written at Step 6 (`record.md`).

**`### Resume state`** is small and current: step, next action, write lease, baseline, and the `sha256sum` lines of the task-owned files. The helper writes it at Plan time, even on a read-only run. Restamp it at each wave launch and each integration. The compaction hook sends every compacted session here, so a stale one is the same as none.
