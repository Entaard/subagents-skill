# Dispatch contracts

Copy these shapes; do not improvise them. Trim a field only where it is genuinely irrelevant and never rename one — sage scans these shapes across many units, and a renamed field reads as a missing one. **The fenced blocks below are presentation, never content.** Copy the shape *inside* the fence into the ledger — real headings, real unfenced tables — and never the fence markers with it: `bin/sage-lint.sh` blanks every line between a pair of fence markers by design, so a ledger that carried the fences across reads to that lint as a Plan section holding no table at all, and **fails for having complied** (measured on a purpose-built fixture).

**Contents** — [Step 2 — Plan and record](#step-2--plan-and-record) · [Step 3 — Brief](#step-3--brief) · [Task brief](#task-brief) · [Agent report](#agent-report) · [Finding schema](#finding-schema) · [Risk rubric](#risk-rubric) · [Snapshot protocol](#snapshot-protocol) · [The ledger](#the-ledger) (Plan · Unit table · Resume state · Assumption log · Decisions and deviations · Findings and dispositions · Open questions and discarded approaches)

## Step 2 — Plan and record

Sage writes the whole plan before it dispatches, then dispatches. The plan is a ledger section, not a message.

**Read before you estimate.** `harness.md` resolves tiers to the model names the plan must carry and lists the knobs this harness exposes. Then read memory the v3 way (`memory.md`, `## Read at Step 2`): `bin/sage-index.sh` for the KI index, the knowledge items the task matches with their stats sidecars, and the journal's newest `run` lines for same-shape pricing — those rows only, never the `obs` or `use` lines (`memory.md`, `## The boundary`). **A run consolidates nothing**: consolidation is `/sage-promote`'s first stage, and the only memory duty Step 2 has beyond reading is remembering what it loaded, because Step 6's `use` line reports exactly that. **Price off a same-shape row before reaching for band arithmetic**: same unit topology, same corpus kind beats a computed number (calibration: established). Rules throughout sage carry a strength band — `(calibration: established)`, `(recurring)`, `(provisional)` — which is what to weigh when budget forces a choice between them.

**Estimate from the corpus a unit must hold and the lenses it must apply — never from the deliverable's size or the role's name.** Add 60–150% where a unit reads widely before it reasons. It governs a blind acceptance-suite author too: pricing one from its requirement's length instead of from the corpus its brief names has missed high by 1.6–1.7× (calibration: established).

**Price a review round and its fix-verification round as a pair — then price the follow-up rounds the loop may still need.** The verify round has come back dry only under a mandate already cut to blocker and major, and it has repeatedly cost more than the review itself, because a fresh or full-mandate continuation re-reads the whole corpus. One exception — steering the same verifier thread for a narrow re-verdict on named fixes runs ~4–7× cheaper than a fresh dispatch, and a finished agent's handle continues with its context intact, so send the steer after that agent reports (calibration: established). The review loop runs until a round comes back dry (`verify.md`), so the pair is a **floor**: budget at least one blocker/major-only follow-up, which is narrower than a full round but still pays the corpus read, and write in the plan that the count is a condition rather than a number.

**Build the measurement harness first.** Where the task turns on a number — a cost, a rate, a count, a benchmark — reproduce the central claim yourself before drafting, then plan against that measured baseline and brief every unit against it — the budget rail measures against exactly this figure. Where several units will report the same metric, mandate **one shared harness** in their briefs: absolute numbers measured by different agents were not comparable across agents (calibration: recurring).

Write the plan into the ledger (`## The ledger` below — open it now; Steps 2 through 6 all use its shapes):

- `### Plan` — the shape below in full, including the **solo alternative with its tradeoff** when the call is close. Writing the solo alternative is what keeps fan-out from being automatic.
- `### Unit table` — the shape below, one row per unit; scout rows carry actuals from Step 1.
- `### Resume state` — the shape below, with the snapshot baseline's hashes. Its restamp duty is below too.
- **Resolve every tier to a concrete model at plan time**, and name every effort level with the control that sets it (`### Plan`, Model and Effort columns, below).
- Where the plan carries a **writer** unit *and* checkable criteria can be extracted without inventing behavior, plan a **blind acceptance suite**: `light`, `full`, or `none`. `topologies.md` #10 owns that decision — the four signals that move it and their precedence when they conflict — so decide it there, then record the choice, its deciding signal, and the criteria text verbatim in `### Plan`, because the criteria are what Step 5 rules against.
- Where a writer unit's diff will be reviewed and the `diff-review` skill is installed, its Spec and Standards reader briefs go into `### Unit table` verbatim as two reader rows — **and the Standards row carries that skill's smell baseline verbatim too**, because nothing else on this path hands that reader the list it rules against. `verify.md` owns the review itself.
- **Stamp `SAGE_WINDOW` into the ledger header line at plan time** — from your environment when it is knowable, else the default the sensor assumes — and stamp `SAGE_COMPACT_AT` as well where the user has set `/autocompact <size>` or told you the session runs on a smaller model variant. The watchdog reads both back, and its `--status` line reports the compaction point it expects with its source word — `measured`, `stated`, or `assumed` (`execute.md` owns how it reads them and the rung that fires off it). **The model id never carries the window**: the same id has run in a 200k and a 1M session on this machine.

**The assumption log.** Every time you resolve an ambiguity that would otherwise need the user — scope, interpretation, a design fork with no evidence either way — write one row to `### Assumption log` (its shape is below) and carry one condensed line into `### Run record`. Write the row **when you resolve the ambiguity**, not at the end from memory, because the alternative you rejected is unrecoverable an hour later; and name a **falsifier** in the "how it would show if wrong" column that a later run could actually observe. Ambiguity that changes the decomposition is the highest-value row in the log and also a surfaced line at Step 6.

Then dispatch. The plan is complete when every unit has a named model, a reader/writer class, a done-when sentence, and an estimate; at that point Step 3 begins in the same turn.

## Step 3 — Brief

Spawning, batching, and limit mechanics are in `harness.md`, `## Spawning` and `## Limits and knobs`, read at Step 2.

Write every dispatch against the task brief contract (full version below, `## Task brief`):

> Role · Objective · Inputs (file paths, never conversation history) · Scope · Allowed writes · **Allowed tools** · **Per-unit caps** · Must not do · Baseline/snapshot · Done when · **Model** · **Effort** · Return format (the agent report below, under the conclusion/enumeration rule the full contract states).

Briefing rules:

- The agent starts with **zero context**, and vague briefs are the number-one cause of duplicated and missed work. Name files, name boundaries, name the output shape, and name the **decisions already made**: two units deciding one question differently is how coupled work fails. Name line ranges only where the location is already certain — a wrong range, plus a reader's rule against widening its scope, silently truncates the answer. **Name the ground truth outright: the exact files, line numbers, URLs, measured baselines, and the harness to measure with.** Across fetching, code, and prose, a brief that names its ground truth has run ~2–2.5× cheaper than an open-ended one and failed less (calibration: established).
- **One dispatch class is exempt from naming the decisions: a blind acceptance-suite author** (`topologies.md` #10). It receives the decisions' *observable consequences*, never the decisions. Told that sessions are cookie-based it writes a case asserting a cookie; told nothing it writes a case asserting the user stays signed in on the next page load, and only the second survives a design change. The same firewall covers the criteria you hand it: phrase them at the requirement's observable surface, because a design noun inside a criterion carries the design straight through.
- **Grep the claim before you brief it — and before you assert it.** A brief may assert that a file, symbol, number, or state exists only after one command has proven it — `grep`, `ls`, `git -C <worktree> rev-parse HEAD` — and it may cite only what its named artifacts actually contain: a pointer into a transcript or report the agent cannot read is a briefing error. The rule reaches past briefs to your own **completion claims**: one run asserted a precedent about a sibling skill without grepping it, and the file said the opposite. Prevention costs one command (calibration: recurring). **And where the deliverable is itself a document that cites artifacts, the same command runs over its own paths before the completion claim** — one `ls` loop over every ledger, transcript, scratch file and report the document names. Either they resolve on the machine where the document is filed, or the document says where they resolve instead. Two rounds of one proposal failed this in opposite directions — scratch files dead with their session, then ledgers no reachable filesystem holds — the verdicts surviving and the evidence gone.
- **A reader's structural claim is a lead, not ground truth.** A researcher's headline version attribution was wrong, and the fix it implied would have introduced the defect it claimed to remove. Fetch the primary source locally and grep it yourself: a summarising fetch tool generates leads, it does not settle facts (calibration: established).
- **Hand off via artifacts, never via transcript.** Everything you paste into a dispatch — and everything it prints back — stays resident in your context and is re-read every later turn. Point at files; require summaries back.
- **Record every dispatch's `agentId`, and name its model.** The `agentId` the spawn result returns is the parent's only handle for a steer, `SendMessage`, and its only candidate for a stop, `TaskStop` — which is still unverified, so do not price a stop off a steer that resolved. The unit's `description` is a label, not an address (`harness.md`, `## Spawning`, for both measurements) — and it goes in `### Unit table` the moment the dispatch returns. Naming the model keeps a unit from silently inheriting the parent's; on a saved-agent dispatch the frontmatter model *is* the named value, and overriding it can invalidate that file's `effort` too, so do that only as a logged deviation — except an alt agent, which takes no `model` parameter (`harness.md`, The alt lane). Set reasoning effort only through a control the harness exposes (`harness.md`, `## Models and effort`).
- **Scope the tools, not just the writes.** `Allowed writes` bounds what a unit can change, not what it can *reach*. Name the tool scope — network, shell, MCP — and keep it to what the objective needs: an agent that cannot write source but can still fetch URLs and run shell is not contained. Only a saved agent file *enforces* this; on a plain dispatch the line is an instruction, so write it and treat it as one. The shipped `verifier` is the deliberate exception — it keeps shell and network because verification has to run and check things, so narrow it in the brief.
- **A unit's toolset comes from its agent file, not from its self-report.** The operative consequence: a unit whose `tools:` omits `Skill` can reach guidance **only through a path it can `Read`**, so name the file path, never the slash command, unless you have checked the list (`harness.md`, `## Frontmatter beyond tools`; calibration: recurring).
- **A repo's own hooks gate your units too, and a blocked unit reads it as a wall.** A project `PreToolUse` hook can degrade a subagent silently: a Transverse-KB gate blocked an `explorer-alt`'s file reads because that agent's toolset carries no MCP call able to satisfy it, and the unit returned `partial` for that reason. Satisfy the repo's gate yourself — one call — **before** the wave launches, not after a unit reports blocked.
- **Know what can actually cap a unit.** `maxTurns` in a saved agent file is the only per-unit budget rail that exists; a plain dispatch has none. Set it where a role's shape is known; leave it unset where it is not, because a cap guessed too low truncates an agent silently. A unit that hits its cap is `blocked`, not failed, and charges no rung on the failure ladder. `harness.md` lists what else an agent file binds — `permissionMode`, `skills`, `mcpServers`, `hooks` — and one of those is the right reach whenever a constraint has to hold rather than be asked for.

Choose the tier from the unit's properties, then resolve it to a model:

```text
| Unit property | Tier | Target effort |
| --- | --- | --- |
| Mechanical, high-volume, search/exploration | fast | low–medium |
| Standard implementation, integration | standard | medium |
| Ambiguous, cross-system integration | standard→frontier | high |
| Correctness/security review, verification | frontier | high–max |
| Genuinely ambiguous, long-horizon, single-owner unit | apex | high–max |
| Synthesis, triage, completion claim | **the parent — you** | — |
```

Apex is an escalation and dedicated-owner tier, never a default seat: it takes no reviewer, explorer, researcher, or implementer row on its own merits (`harness.md`, Models and effort, owns the placement and its reasons).

**Tier is one axis; the unit's step count is the other.** A cheap model on multi-step work can take enough extra turns to cost more than the tier above it, and what decides which case a unit is in is its brief rather than its role (`harness.md`, Models and effort, carries the rule at full strength and states how thin its evidence is).

Four saved agent files make the effort column real for the units that recur most — dispatch by agent type and the effort cell reads `low (explorer)` rather than `low (no control)`: **`explorer`**, **`verifier`**, **`web-researcher`**, and **`implementer`**, whose `skills:` preloads `clean-code`, so those rules bind every writer dispatch without re-briefing them (`harness.md`, the role table, for the tier, effort and tool scope each one binds). Three optional alt twins — `explorer-alt`, `verifier-alt`, `web-researcher-alt` — place a reader on a model outside this harness's family; each is dispatchable only after a new session, and `verifier-alt` buys a second family for the checker role while the other two buy price and window headroom, never diversity. `harness.md`, The alt lane, has the config format, the availability rule, how to fill the Model cell, their exact scopes, and the bar for adding another.

- On a retry, escalate one tier rather than re-dispatching the same row: above frontier the next tier is apex, and where the harness resolves none the ladder tops out at frontier (`execute.md`, the failure ladder, owns which rung a failure earns and when).
- Reviewers: read-only *role* always; a writable *sandbox* only when verification must write — caches, screenshots, builds — with a no-source-edit rule in the contract.
- Nested delegation off unless you grant a self-contained subtree. That is brief text only on a plain dispatch; a saved agent whose `tools:` omits the Agent tool enforces it. The spawn-depth cap bounds runaway recursion; it does not implement "off".

## Task brief

```text
Role: <implementer | explorer | reviewer(lens) | verifier | judge>
Objective: <one sentence>
Inputs / source of truth: <file paths, briefs, diffs — the agent starts blank, with no transcript. Name the exact ground truth: files, line numbers, URLs, the measured baseline, the harness to measure with. A brief that must rediscover its ground truth costs more and fails more — Step 3 above carries the measured ratio and is its one home>
Scope and relevant files: <explicit>
Allowed writes: <none | exact paths | worktree path>
Allowed tools: <the tool scope this objective needs — "read + search only, no network, no shell" | "repo tools + Bash for the test command only" | "inherit". Reviewers and explorers: deny network and shell unless the objective names a use for them. Read-only writes plus open network access is not read-only>
Per-unit caps: <`maxTurns` / `permissionMode` where a saved agent file sets them, else "none — plain dispatch". Unlike the two lines above, these BIND. A unit that hits `maxTurns` returns `blocked`, not failed, and charges no rung on the failure ladder>
Must not do: <boundaries, non-goals, no nested delegation unless granted>
Baseline / snapshot: <revision, diff, or file manifest being worked against>
Done when: <one falsifiable sentence>
Model: <the exact value passed to this dispatch, matching its ledger Plan row; tier in brackets. On a saved-agent dispatch its frontmatter model is that value unless you deliberately override — and on an **alt** agent you never do: that row passes no `model` parameter, and the cell records what its file sets (`harness.md`, The alt lane)>
Effort: <the level, always, plus the control setting it — agent-file frontmatter, or "no control" on a plain dispatch. Matches its ledger Plan row>
Return format: the agent report below, ≤1–2k tokens where the unit returns a **conclusion**; where it returns an **enumeration**, one line per item plus a pointer, and this brief must name the scratch path. Bulk output to <scratch path> (omit the scratch path for a unit that cannot write — `explorer` and `web-researcher` distill instead, and a scratch path in their brief is a briefing error)
```

**Where an acceptance suite runs** (`topologies.md` #10), three briefs change shape. The blind author's `Inputs` are the requirement text and the criteria recorded in the ledger's Plan section, and nothing else — the one dispatch class exempt from naming the decisions already made (Step 3 above). The implementer's brief carries the criterion IDs and never the suite path. The verifier's brief carries the suite path and the per-case verdict set — pass / fail / `Awaiting human`, with evidence required on each.

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

Validate material claims against repo state or tool output. A summary is a claim, not proof.

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

- **`ID:` must match the id shape `bin/sage-lint.sh` recognises, or its `triage-orphan` check silently skips that id** — that check's header comment in the script documents the grammar; read it there before inventing an id style. A duplicate `m7` once sat in the same table as a duplicate `O-1` and a duplicate `DIV-1` that the lint did catch, and it was found only by hand.

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
- **High**: bounded exploration; optional pre-write plan critic (`topologies.md` #11) and blind acceptance suite (`topologies.md` #10, which consumes the hard-trigger list above as one of its four signals) — **sage decides both**, each justified by a named trigger. One writer per isolated tree; staged checks; two independent reviewers on the same frozen diff; parent triage; targeted regression verification; human checkpoint for subjective criteria (the `Awaiting human` route — `topologies.md`, evidence menus).

## Snapshot protocol

Runs whenever any writer is present, the parent included.

1. **Baseline** — record starting revision, dirty files, task-owned files. Unrelated dirty changes are never the agent's work and must survive. **This is the only recovery map once a writer has run**, because no automatic snapshot covers a delegated write (`harness.md`, Cautions). **An untracked file is recorded by name, and a name is not a recovery path** — git holds no object for it and the baseline holds no content, so one that vanished mid-run was unrecoverable. Copy task-adjacent untracked files into the scratchpad at baseline time.
2. **Write lease** — one named writer; everyone else source-read-only.
3. **Stabilize** — writer finishes; run focused checks; capture the diff or changed-file manifest.
4. **Freeze** — no source changes while reviewers inspect the candidate.
5. **Triage** — merge and dedupe findings by root cause, not by wording, before any fix.
6. **New lease** — one writer for accepted fixes (prefer the original; a fresh one needs the complete brief).
7. **Verify** — targeted checks on fixes and regressions. A new full review only if design materially changed.

No manufactured commits just to make a snapshot — a stable diff or file-hash manifest is enough. Non-git projects: record the task-owned file list with before/after hashes.

Two lease cases the seven steps do not cover. The parent taking a writer unit inline **moves the lease to the parent** — it does not lapse, and no other writer starts. A rail stopping the run (`../SKILL.md`, `## Rails`) **freezes the lease** where it is. Log either in the ledger, because a lease whose holder is unrecorded is the same as no lease.

## The ledger

One file, `.claude/plans/sage-ledger-<session>.md` — durable; **gitignored only where that repo says so, which is a `git check-ignore -q .claude/plans/` test to run before the first write, never an assumption** (`harness.md`, Ledger location, for the four branches) — the session scratchpad only as a fallback where no durable path exists — and it is the only record of a run. **It is not written for the user.** A compaction lands mid-run with agents still in flight and discards nearly the whole window (`harness.md`, Transcripts). Five things read it back afterwards, and all five are sage: the budget rail's recorded estimate, the write lease and snapshot baseline, the failure ladder's signature count across attempts, a post-compaction parent or `/sage resume` reconstructing the run, and `/sage report` rendering it — which is why it may not live where a session's end deletes it. **Bring it current before launching a wave and after each integration** (`execute.md` owns that cadence and what each point does). `record.md` owns `/sage report` and its resolution order.

**The ledger's first line is a fixed header comment**, so the occupancy duty survives a compaction summary and a fresh reader re-learns it from the ledger alone:

```text
<!-- sage occupancy duty: at every bring-current point, read parent occupancy from sage-watch.sh --status and restamp this line; window=<SAGE_WINDOW> compact-at=<n> (<measured|stated|assumed>) rung=<n>; at the rung, run the checkpoint in SKILL.md ## Compaction and resume. After a compaction: re-read ### Resume state, then SKILL.md, then the step file it names, before dispatching anything. Last check: <occ> (<pct>) at <when>. -->
```

Written at Plan time, restamped at every bring-current point.

### Plan

Written at Step 2 above, in full, before any dispatch, and priced off the memory that step read (`../memory/shared/` for the estimating rules, `../memory/local/` and the journal tail for this machine's figures).

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

**Model and Effort columns** — the exact model value you will pass with its tier in brackets, never a tier alone, except on an **alt** row, where you pass no model at all and the cell records the value its file sets, read with one grep (`harness.md`, The alt lane); and the effort **level always**, with the control that sets it in brackets: `low (explorer)`, `high (verifier)` where frontmatter sets it, an alt row's the same way; `medium (no control)`, written in full, on a plain dispatch, which has no lever. Never a bare level and never a dash: a bare `low` is a promise nothing keeps. Resolve tier → model against the live session and run the `CLAUDE_CODE_SUBAGENT_MODEL` check before writing the Model column — `harness.md`, Models and effort, for what a set override does to every cell in it.

**Flow column** — `bg, batch1` for a wave, `bg, after1` for a row consuming a whole prior wave, `bg, per-item after <id>` for the pipeline-per-item flow `decompose.md` prefers. A per-item stage over N items is **one row**, with the item count in its `done when` clause. **Acceptance-suite criteria go in as text, verbatim, not as a count**, each phrased at the requirement's observable surface — no module names, no data stores, no mechanism choices — because the blind author's firewall depends on it (Step 3 above).

**Compress the table before writing it.** **One physical line per row**, because a wrapped cell costs the row its alignment — keep a short unit name in the cell and move every `done when` clause to a numbered list under the table, keyed by row id. **A constant column is not a column**, because an invariant column costs attention on every row — where every row shares a value, delete the column and state it once above the table (`All rows: background, read-only, wave 1.`); Effort, Flow and Isolation collapse this way in most plans, while a column that varies stays, however wide.

### Unit table

```text
| id | unit | agent/thread name | model used | state | messages | evidence | actual tokens |
```

The live per-unit state, updated on every state change. State ∈ `planned | running | reported | blocked | failed | abandoned | inline`. **The `agent/thread name` cell carries the `agentId` the dispatch returned, never the unit's `description`** — a `planned` row leaves it empty and fills it the moment the dispatch returns; left unfilled after that, it is a unit you can neither steer nor stop (`harness.md`, Spawning, for the measurement; Step 3 above states the duty).

**`model used`** records the value `sage-watch.sh --status` measured from the unit's own transcript, with the word `measured`, filled at the bring-current point where you read it (`execute.md`). A cell filled from your own dispatch says `asserted`, because the harness can swap a requested model in silence (`harness.md`, Models and effort); an asserted cell is a claim, a measured one is evidence.

**`messages`** holds every failure-ladder `SendMessage` you sent to this unit: the time each went out, and whether a reply landed. The watchdog sends nothing, so this cell is entirely your own record. An empty cell means none were sent, never that the unit answered.

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

Written at Step 2 above, restamped at every bring-current point and at the checkpoint rung. The `sha256sum` lines are the baseline `/sage resume` re-runs — `git status` alone misses untracked and out-of-repo files. This section is what a post-compaction parent reads first (`../SKILL.md`, `## Compaction and resume`), so a stale one is the same as none.

### Assumption log

One row every time sage resolves an ambiguity a human would otherwise have been asked about — scope, decomposition, model, suite, topology, or the meaning of the task itself.

```text
| assumption | what I chose | what else was plausible | how it would show if wrong |
```

Ambiguity that changes the decomposition is the one place sage carries more risk than an attended run, so that case is always a row, never a judgment call. A later user correction is written **next to the row it corrects**, in that same row, never as a fresh row elsewhere. One condensed line goes in the run record.

### Decisions and deviations

```text
| id | when | decision, plan amendment, or dropped disagreement | reason |
```

Every plan amendment — model, effort, scope, count, topology, cap — with its reason and when it happened. **Every abandoned disagreement gets a row too**: what was dropped, which unit held it, and why it lost. Silent discard is forbidden.

**An amendment writes its row here *and* marks the rows it amends.** Every row in this table carries an id in its first cell — `D1`, `D2`, … in the order written — because the mark on the amended row has to name something. Then tag the affected `### Plan` and `### Unit table` rows in their own first cell — `2 superseded → D2` — so the plan actually in force reads off the table without replaying this log. Both halves or neither: a Decisions row on its own leaves the Plan table asserting something that stopped being true; a tag on its own points at nothing.

**An amendment that leaves no mark is the measured failure** — a four-ledger audit found amendments leaving the rows they amend untouched, one run cutting a review mandate down and another adding a whole unit, with a reader of either Plan table unable to tell what was still in force. `bin/sage-lint.sh` strips the `superseded → D<n>` tag before it compares the Plan and Unit id sets, so obeying this rule never costs a ledger a violation for obeying it.

**A rail-1 authorisation is a row here too**, written before the authorised action runs (`../SKILL.md`, `## Rails`). It has no other home.

### Findings and dispositions

```text
| id | severity | location | triage | evidence |
```

One row per finding from the schema above, each carrying exactly one triage state. A finding whose triage is still open is an unfinished run.

**One disclosure has its only home here**, so that a reader knows where to look and a check can tell when it is missing: the **residual same-family maker/checker bias**, wherever no cross-family checker was available (`verify.md`). That one line has landed in five different sections across the ledgers on this machine, while another run that owed it recorded it nowhere at all. A duty with no fixed address is a duty nothing can check.

### Open questions and discarded approaches

```text
| kind | item | current hypothesis, or why it was dropped | what would settle it |
```

`kind` is `open` or `discarded`. Written when the question opens or the approach is dropped, so the next session does not re-buy it; restamped with the rest at each bring-current point.

`### Run record` is `record.md`'s.
