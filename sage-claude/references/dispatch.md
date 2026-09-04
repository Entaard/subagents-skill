# Dispatch contracts

Copy these shapes; do not improvise them. Trim a field only where it is irrelevant and never rename one. **The fenced blocks below are presentation, never content**: copy the shape *inside* the fence into the ledger as real headings and unfenced tables, never the fence markers — `bin/sage-lint.sh` blanks every fenced line, so a ledger that carried them reads as a Plan section holding no table (measured).

## Step 2 — Plan and record

The whole plan is written before any dispatch, as a ledger section, never as a message.

**Read before you estimate.** `harness.md` resolves tiers to the model names the plan must carry; `alt-lane.md` only when an alt agent is in your live agent list. Then read memory (`memory.md`, `## Read at Step 2`) and remember what you loaded, because Step 6's `use` line reports it; a run consolidates nothing. **Price off a same-shape row before reaching for band arithmetic** (calibration: established). Rules carry a strength band — `(calibration: established)`, `(recurring)`, `(provisional)` — which is what to weigh when budget forces a choice.

**Estimate from the corpus a unit must hold and the lenses it must apply — never from the deliverable's size or the role's name.** Add 60–150% where a unit reads widely before it reasons; a blind acceptance-suite author priced from its requirement's length has missed high by 1.6–1.7× (calibration: established).

**Price a review round and its fix-verification round as a pair, then the follow-up rounds the loop may still need.** The verify round has repeatedly cost more than the review; steering the same verifier thread for a narrow re-verdict runs ~4–7× cheaper than a fresh dispatch, so send the steer after that agent reports (calibration: established). The pair is a **floor**: budget at least one blocker/major-only follow-up, and write in the plan that the count is a condition (`verify.md`), not a number.

**Build the measurement harness first.** Where the task turns on a number, reproduce the central claim yourself before drafting and brief every unit against that baseline; where several units report one metric, mandate **one shared harness** (calibration: recurring).

Write the plan into the ledger (`## The ledger` below):

- `### Plan` in full, including the **solo alternative with its tradeoff** when the call is close — writing it is what keeps fan-out from being automatic; `### Unit table`; `### Resume state` with the snapshot baseline's hashes.
- **Resolve every tier to a concrete model at plan time**, and name every effort level with the control that sets it (Model and Effort columns, below).
- A **writer** unit plus checkable criteria extractable without inventing behaviour → plan a **blind acceptance suite**, `light`, `full`, or `none`; `topologies.md` #10 owns the decision. Record the choice, its deciding signal, and the criteria text verbatim in `### Plan`.
- A writer's diff to be reviewed, with the `diff-review` skill installed → its Spec and Standards reader briefs go into `### Unit table` verbatim as two reader rows, **the Standards row carrying that skill's smell baseline verbatim**, because nothing else hands that reader the list. `verify.md` owns the review.
- **Stamp `SAGE_WINDOW` into the ledger header line** — from your environment when knowable, else the sensor's default — and `SAGE_COMPACT_AT` where the user set `/autocompact <size>` or named a smaller model variant; the watchdog reads both back (`execute.md`). **The model id never carries the window.**

**The assumption log.** Every ambiguity you resolve that would otherwise need the user — scope, interpretation, a design fork with no evidence either way — is one row in `### Assumption log`, written **when you resolve it**, with a **falsifier** a later run could observe. Ambiguity that changes the decomposition is a surfaced line at Step 6.

The plan is complete when every unit has a named model, a reader/writer class, a done-when sentence, and an estimate; Step 3 begins in the same turn.

## Step 3 — Brief

Write every dispatch against the task brief contract (`## Task brief` below). Briefing rules:

- The agent starts with **zero context**. Name files, boundaries, the output shape, and the **decisions already made**: two units deciding one question differently is how coupled work fails. Name line ranges only where the location is certain. **Name the ground truth outright: exact files, line numbers, URLs, measured baselines, and the harness to measure with** — such a brief has run ~2–2.5× cheaper and failed less (calibration: established).
- **One dispatch class is exempt from naming the decisions: a blind acceptance-suite author** (`topologies.md` #10). It receives the decisions' *observable consequences*, never the decisions, and its criteria are phrased at the requirement's observable surface for the same reason.
- **Grep the claim before you brief it — and before you assert it.** A brief asserts that a file, symbol, number, or state exists only after one command has proven it, and cites only what its named artifacts contain: a pointer into a transcript or report the agent cannot read is a briefing error. The rule reaches your own **completion claims** (calibration: recurring): where the deliverable cites artifacts, one `ls` loop over every path it names runs before the claim — either they resolve on the machine where the document is filed, or the document says where they resolve instead.
- **A reader's structural claim is a lead, not ground truth.** Fetch the primary source locally and grep it yourself (calibration: established).
- **Hand off via artifacts, never via transcript**: everything pasted into a dispatch, and everything it prints back, stays resident in your context. Point at files; require summaries back.
- **Record every dispatch's `agentId` in `### Unit table` the moment it returns, and name its model.** The `agentId` is the parent's only handle for `SendMessage` and `TaskStop`; the `description` is a label (`harness.md`, `## Spawning`). On a saved-agent dispatch the frontmatter model *is* the named value; override only as a logged deviation, and never on an alt agent (`alt-lane.md`). Set effort only through a control the harness exposes (`harness.md`, `## Models and effort`).
- **Scope the tools, not just the writes** — network, shell, MCP — to what the objective needs: an agent that cannot write source but can fetch URLs and run shell is not contained. Only a saved agent file *enforces* this; on a plain dispatch the line is an instruction. The shipped `verifier` keeps shell and network, so narrow it in the brief.
- **A unit's toolset comes from its agent file, not from its self-report.** A unit whose `tools:` omits `Skill` reaches guidance **only through a path it can `Read`**: name the file path, never the slash command (`harness.md`, `## Frontmatter beyond tools`; calibration: recurring).
- **A repo's own `PreToolUse` hooks gate your units too**, silently. Satisfy the repo's gate yourself, one call, **before** the wave launches.
- **`maxTurns` in a saved agent file is the only per-unit budget rail**; a plain dispatch has none. Set it where a role's shape is known, never as a guess, because a low cap truncates silently; a unit that hits it is `blocked`, not failed, and charges no rung. `harness.md`, `## Frontmatter beyond tools`, lists what else an agent file binds.

Choose the tier from the unit's properties, then resolve it to a model:

| Unit property | Tier | Target effort |
| --- | --- | --- |
| Mechanical, high-volume, search/exploration | fast | low–medium |
| Standard implementation, integration | standard | medium |
| Ambiguous, cross-system integration | standard→frontier | high |
| Correctness/security review, verification | frontier | high–max |
| Genuinely ambiguous, long-horizon, single-owner unit | apex | high–max |
| Synthesis, triage, completion claim | **the parent — you** | — |

Apex is an escalation and dedicated-owner tier, never a default seat. **Tier is one axis; the unit's step count is the other** — a cheap model on multi-step work can cost more than the tier above it (`harness.md`, Models and effort, owns both rules). Four saved agent files make the effort column real — **`explorer`**, **`verifier`**, **`web-researcher`**, **`implementer`** (`harness.md`, the role table) — and three optional alt twins place a reader outside this harness's model family (`alt-lane.md`).

- On a retry, escalate one tier rather than re-dispatching the same row; the ladder tops out at the highest tier the harness resolves (`execute.md`, the failure ladder).
- Reviewers: read-only *role* always; a writable *sandbox* only when verification must write, with a no-source-edit rule.
- Nested delegation off unless you grant a self-contained subtree; only a saved agent whose `tools:` omits the Agent tool enforces it — the spawn-depth cap bounds runaway recursion and does not implement "off".

## Task brief

```text
Role: <implementer | explorer | reviewer(lens) | verifier | judge>
Objective: <one sentence>
Inputs / source of truth: <file paths, briefs, diffs — the agent starts blank. Name the exact ground truth: files, line numbers, URLs, the measured baseline, the harness to measure with (Step 3 above carries the measured ratio)>
Scope and relevant files: <explicit>
Allowed writes: <none | exact paths | worktree path>
Allowed tools: <"read + search only, no network, no shell" | "repo tools + Bash for the test command only" | "inherit". Reviewers and explorers: deny network and shell unless the objective names a use for them. Read-only writes plus open network access is not read-only>
Per-unit caps: <`maxTurns` / `permissionMode` where a saved agent file sets them, else "none — plain dispatch". Unlike the two lines above, these BIND>
Must not do: <boundaries, non-goals, no nested delegation unless granted>
Baseline / snapshot: <revision, diff, or file manifest being worked against>
Done when: <one falsifiable sentence>
Model: <the exact value passed to this dispatch, matching its ledger Plan row; tier in brackets. On a saved-agent dispatch its frontmatter model is that value; an alt agent passes no `model` parameter and the cell records what its file sets (`alt-lane.md`)>
Effort: <the level, always, plus the control setting it — agent-file frontmatter, or "no control" on a plain dispatch. Matches its ledger Plan row>
Return format: the agent report below, ≤1–2k tokens where the unit returns a **conclusion**; where it returns an **enumeration**, one line per item plus a pointer to <scratch path>, which this brief must name (omit it for a unit that cannot write — `explorer` and `web-researcher` distill instead)
```

**Where an acceptance suite runs** (`topologies.md` #10): the blind author's `Inputs` are the requirement text and the criteria in the ledger's Plan section, nothing else; the implementer's brief carries the criterion IDs and never the suite path; the verifier's brief carries the suite path and the per-case verdict set — pass / fail / `Awaiting human`, with evidence on each.

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

- **`ID:` must match the id shape `bin/sage-lint.sh` recognises, or its `triage-orphan` check silently skips that id** — the grammar is in that script's header.
- **Blocker**: crash, corruption, security failure, broken build, unusable core path, failed mandatory criterion. **Major**: credible user-visible incorrectness, regression, serious performance or near-term maintainability failure. **Minor**: bounded improvement; never blocks acceptance.
- Low-confidence hypotheses are investigation leads, not blockers. Style-only comments are omitted.
- Triage states: **accepted / rejected with evidence / deferred with owner / user decision.** Every finding gets exactly one.

## Risk rubric

Axes: failure impact; breadth of coupling; novelty/uncertainty; reversibility; strength of automated verification; external compatibility or human-decision dependencies.

**Hard triggers → high risk regardless of other axes:** data/save migration, security or credentials, networking or deterministic simulation, public API compatibility, irreversible conversion, a core performance budget, behavior with no reliable test oracle. Reclassify mid-task if exploration reveals a different blast radius.

- **Low**: parent or one worker; focused checks; review only if behavior is non-obvious.
- **Medium**: ≤2 explorers for real unknowns; one writer; one lens-specific reviewer; targeted fix verification.
- **High**: bounded exploration; optional pre-write plan critic (`topologies.md` #11) and blind acceptance suite (`topologies.md` #10), **sage deciding both** on a named trigger; one writer per isolated tree; staged checks; two independent reviewers on the same frozen diff; parent triage; targeted regression verification; human checkpoint for subjective criteria (`Awaiting human`, `topologies.md`, evidence menus).

## Snapshot protocol

Runs whenever any writer is present, the parent included.

1. **Baseline** — record starting revision, dirty files, task-owned files; unrelated dirty changes must survive. **This is the only recovery map once a writer has run** (`harness.md`, Cautions), and **a name is not a recovery path**: copy task-adjacent untracked files into the scratchpad at baseline time.
2. **Write lease** — one named writer; everyone else source-read-only.
3. **Stabilize** — writer finishes; run focused checks; capture the diff or changed-file manifest.
4. **Freeze** — no source changes while reviewers inspect the candidate.
5. **Triage** — merge and dedupe findings by root cause, not by wording, before any fix.
6. **New lease** — one writer for accepted fixes (prefer the original; a fresh one needs the complete brief).
7. **Verify** — targeted checks on fixes and regressions. A new full review only if design materially changed.

No manufactured commits to make a snapshot — a stable diff or file-hash manifest is enough; non-git projects record the task-owned files with before/after hashes. The parent taking a writer unit inline **moves the lease to the parent**; a rail stopping the run (`../SKILL.md`, `## Rails`) **freezes the lease**. Log either.

## The ledger

One file, `.claude/plans/sage-ledger-<session>.md` — durable; **gitignored only where that repo says so, a `git check-ignore -q .claude/plans/` test run before the first write** (`harness.md`, Ledger location); the session scratchpad only where no durable path exists. It is the only record of a run and **it is not written for the user**: its readers are the budget rail, the snapshot baseline, the failure ladder, a post-compaction parent or `/sage resume`, and `/sage report` (`record.md`). **Bring it current before launching a wave and after each integration** (`execute.md`).

**The ledger's first line is a fixed header comment**, so the occupancy duty survives a compaction summary:

```text
<!-- sage occupancy duty: at every bring-current point, read parent occupancy from sage-watch.sh --status and restamp this line; window=<SAGE_WINDOW> compact-at=<n> (<measured|stated|assumed>) rung=<n>; at the rung, run the checkpoint in SKILL.md ## Compaction and resume. After a compaction: re-read ### Resume state, then SKILL.md, then the step file it names, before dispatching anything. Last check: <occ> (<pct>) at <when>. -->
```

Written at Plan time, restamped at every bring-current point.

### Plan

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
Budget: ~<total> tokens, ~<min> wall clock — basis: <the same-shape row you priced off, named, or the band>. The token figure sets the run's own ceiling, so estimate honestly in both directions (`../SKILL.md`, `## Rails`).
Acceptance suite: light | full | none — chosen because <one line>.
        Criteria: R1 <text>; R2 <text>; ...
Scouting: <N explorer scouts, rounds where two, ~actual tokens — already spent (`decompose.md`)>.
Risks: <top 1–3. With any writer present, name the `/rewind` gap explicitly>.
Solo alternative: <what one strong agent inline would cost or miss>.
```

**Model and Effort columns** — the exact model value you will pass with its tier in brackets, never a tier alone (an **alt** row passes no model and records the value its file sets, `alt-lane.md`); and the effort **level always**, with the control that sets it in brackets — `low (explorer)`, `high (verifier)`, or `medium (no control)` on a plain dispatch — never a bare level and never a dash. Run the `CLAUDE_CODE_SUBAGENT_MODEL` check first (`harness.md`, Models and effort).

**Flow column** — `bg, batch1` for a wave, `bg, after1` for a row consuming a whole prior wave, `bg, per-item after <id>` for the pipeline-per-item flow `decompose.md` prefers; a per-item stage over N items is **one row**, with the item count in its `done when` clause. **Acceptance-suite criteria go in as text, verbatim**, each at the requirement's observable surface — no module names, no data stores, no mechanism choices.

**Compress the table**: **one physical line per row**, `done when` clauses in a numbered list under it keyed by row id; **a constant column is not a column** — state a shared value once above the table.

### Unit table

```text
| id | unit | agent/thread name | model used | state | messages | evidence | actual tokens |
```

The live per-unit state, updated on every state change. State ∈ `planned | running | reported | blocked | failed | abandoned | inline`. **`agent/thread name`** is the `agentId` the dispatch returned, never the `description`, filled the moment the dispatch returns. **`model used`** is the value `sage-watch.sh --status` measured from the unit's transcript, marked `measured` (`execute.md`); a cell filled from your own dispatch says `asserted`, because the harness can swap a requested model in silence. **`messages`** holds every failure-ladder `SendMessage` you sent to this unit, when, and whether a reply landed; an empty cell means none were sent.

### Resume state

```text
### Resume state
step: <1–6> — <the step file to re-read>
next action: <one line>
checkpoint: <turn <n> | none>
write lease: <holder | frozen | none>
watchdog: <hosted on Monitor over <subagents-dir> | re-hosted after compaction at <when> | disabled: <reason>>
baseline: <revision>; dirty files: <list>
<sha256sum output, one line per task-owned file>
subagents: <path to this session's subagents/ directory>
<agentId> → <description>   (one line per agent dispatched)
```

Restamped at every bring-current point and at the checkpoint rung. The `sha256sum` lines are the baseline `/sage resume` re-runs — `git status` alone misses untracked and out-of-repo files. A post-compaction parent reads this section first (`../SKILL.md`, `## Compaction and resume`), so a stale one is the same as none.

### Assumption log

```text
| assumption | what I chose | what else was plausible | how it would show if wrong |
```

One row per ambiguity a human would otherwise have been asked about (Step 2 above). Ambiguity that changes the decomposition is always a row. A later user correction is written **next to the row it corrects**, never as a fresh row elsewhere.

### Decisions and deviations

```text
| id | when | decision, plan amendment, or dropped disagreement | reason |
```

Every plan amendment — model, effort, scope, count, topology, cap — with its reason and when, and **every abandoned disagreement**: what was dropped, which unit held it, and why it lost. Silent discard is forbidden.

**An amendment writes its row here *and* marks the rows it amends.** Every row carries an id — `D1`, `D2`, … in order written — and the affected `### Plan` and `### Unit table` rows are tagged in their own first cell, `2 superseded → D2`, so the plan in force reads off the table. Both halves or neither. `bin/sage-lint.sh` strips the tag before comparing the Plan and Unit id sets.

**A rail-1 authorisation is a row here too**, written before the authorised action runs (`../SKILL.md`, `## Rails`). It has no other home.

### Findings and dispositions

```text
| id | severity | location | triage | evidence |
```

One row per finding, each carrying exactly one triage state; an open triage is an unfinished run. **One disclosure has its only home here**: the **residual same-family maker/checker bias**, wherever no cross-family checker was available (`verify.md`).

### Open questions and discarded approaches

```text
| kind | item | current hypothesis, or why it was dropped | what would settle it |
```

`kind` is `open` or `discarded`. Written when the question opens or the approach is dropped, so the next session does not re-buy it; restamped with the rest at each bring-current point.

`### Run record` is `record.md`'s.
