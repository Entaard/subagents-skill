# Sage — build plan

Date: 2026-08-17. Basis: `ideas.md`, `sage-review.md`, the full `subagents-claude/` corpus, `claude-skills/agents-self-reflect/`, `install.sh`, and six parallel agents that verified the load-bearing claims on this machine.

This plan is written for you, in plain English. **The sage documents it describes are not.** They target a fresh model instance as the reader. Section 10 shows what that looks like.

---

## 1. What sage is

Sage is a new skill, installed beside `/subagents`, not a replacement for it. It keeps the machinery `/subagents` measured into place. It removes the two places that stop and wait for you.

Five departures. Everything else carries over.

| # | Departure | What replaces it |
| --- | --- | --- |
| D1 | No plan-approval gate | The plan is still written in full, to a file, before any dispatch. It is never presented. |
| D2 | No mandatory report | There is no report file. The ledger already holds everything a report would say. One line prints. It expands only on an anomaly. |
| D3 | Two memories, not one | A portable memory that travels to every machine, and a local memory for this machine's numbers. |
| D4 | Promotion is hinted, never taken | Sage detects that a lesson is ready, prints one line, and stops. You ask for the promotion. |
| D5 | Written for agents | No plain-English obligation. Precision and density are the only targets. |

Two organs get built that `/subagents` never had, because an unattended run needs them and an attended one does not:

- **A watchdog** that watches running agents from their live transcripts and can steer or recall one.
- **A handover** that writes the run's state to a file and stops before the parent's context collapses.

### The identity

The sage name earns its keep as an operating stance, not decoration. Four axioms, which become the preamble of `SKILL.md`:

1. **Not smarter than its model. Better spent.** Sage adds no intelligence. It adds placement, boundaries, and evidence.
2. **Every claim is checkable or it is a hypothesis.** Sage's own claims most of all. The parent's post-fix confidence is the most reliable place errors enter, at ×10 confirmations.
3. **Conflict is bought, not tolerated.** Disjoint mandates, adversarial refutation, and a command to settle a tie. Agreement is not evidence.
4. **Autonomy is legibility, recorded rather than shown.** Every run leaves a complete record. Silence is a display choice. It is never a data choice.

---

## 2. The decisions, and what each rests on

Each row is a decision I made from evidence, not preference. Where the evidence cut against your instruction, I say so and follow your instruction.

| # | Decision | Rests on |
| --- | --- | --- |
| 1 | **A new skill, not an evolution of `/subagents`.** | Your call. The review recommended evolving. You asked for an experiment with its own identity, and a separate directory keeps a working skill unharmed while sage is unproven. I follow you here. |
| 2 | **The plan is always written. It is never shown.** | `.claude/plans/2026-08-15-agents-self-reflect.md:35-46` records a plan drafted, saved, and never run — and the drafting alone caught two real defects, including an `install.sh` edit that would have misfired a notice on every install. The plan also produces the number the budget rail measures against (`SKILL.md:159`). Deleting the artifact costs both. Deleting the pause costs neither. |
| 3 | **Removing the gate is not contradicted by measurement.** | The repo's "plans change on contact with the human" claim traces to one unquantified sentence at `summon-teams-review.md:82`. No run-log row anywhere records a gate answer, an `adjust`, or a reversed gate call. Neither side of the argument has telemetry. Sage will produce it (§5.1, assumption log). |
| 4 | **One ledger, no report file. One line prints.** | `sage-review.md:119` is right that silence plus delegated writes is unrecoverable: `/rewind` does not undo subagent edits. But the recovery map is the *baseline and ledger* (`contracts.md:175`), not the report — so the report is a rendering of the ledger, not a second record. Writing both would repeat the duplicate-copy failure §2.7 exists to avoid. |
| 5 | **Hand-batched only. Sage drops the `Workflow` backend.** | A script takes no mid-run input. Steering, triage-on-arrival, and taking a unit inline are the levers an unattended parent can least afford to lose. Dropping it also deletes two of the four gate-dependent rails outright — the `acceptEdits` disclosure and the row-by-row backend test — because their subject is gone. Removes roughly 60 lines of corpus. |
| 6 | **The two memories hold disjoint content classes.** | The install-vs-repo calibration split has already forked in practice: the live header matches none of the 8 committed seed versions, in both directions, and can never converge. Giving each file a different *kind* of content removes the precedence question by construction instead of arbitrating it. |
| 7 | **The shared memory is one physical file, symlinked.** | Verified: the runtime agent has no path back to the repo, and `install.sh:135` runs `rsync --delete` with no excludes, so a runtime-written file under `~/.claude/skills/sage/` is deleted on the next install. A symlink makes "write the install dir" and "write the repo" the same act, with no second copy to diverge. |
| 8 | **Consolidation runs automatically. Promotion never does.** | Your instruction on promotion. On consolidation, the evidence supports automating: the one recorded corruption (`self-reflect-report.md:53-55`) happened *through* an approved human diff and was caught later by a check, not by the approval. A human gate that did not prevent the failure is not the safeguard. A machine invariant is (§5.3). |
| 9 | **Sage documents opt out of the house style.** | `output-styles/simplified-technical-english.md:15` defines its reader as "a working software engineer who reads English as a second language" — a human style. This repo's own working agent docs already run 2.5× its sentence-length cap and use the em-dash join it forbids. Your instruction and the measurement agree. |
| 10 | **Shortest is the wrong target. Minimal is the right one.** | Anthropic's context-engineering guidance, fetched 2026-08-17: "minimal does not necessarily mean short." A cut that changes what a fresh instance does is a spec change, not compression. §10 gives the floor. |
| 11 | **The budget ceiling is 4× the run's own estimate, not a fixed number.** | Your call, and it matches your stated principle that there is no limit on cost, only on efficiency. A fixed ~500k rail is tight against measured reality — a single agent's spend is p90 533k, p99 3.0M across 199 runs. A ceiling that scales with the plan lets sage escalate, retry, and re-route on its own, which is the whole point of removing the gate. §5.1 has the arithmetic and the one honest risk. |

---

## 3. File layout

### In the repo

```
sage-claude/
  SKILL.md                 the spine — steps, rails, axioms
  memory/
    shared.md              all-machine memory. Git-tracked. The only physical copy.
    local-seed.md          what a new machine's local memory starts as
  references/
    dispatch.md            brief contract, return schema, finding schema, ledger, handoff note
    topologies.md          the orchestration patterns
    harness.md             Claude Code mechanics, transcript layout, tier resolution
    memory.md              the memory protocol: append, consolidate, hint, promote
  bin/
    sage-watch.sh          the watchdog probe
```

### After install

```
~/.claude/skills/sage/
  SKILL.md
  references/*
  bin/sage-watch.sh
  memory/
    shared.md        -> symlink to <repo>/sage-claude/memory/shared.md
    local.md            real file, seeded once, never overwritten
    local-archive.md    created on first consolidation
```

The symlink is what makes your requirement work. Sage writes `~/.claude/skills/sage/memory/shared.md`. The bytes land in the repo. Git sees them. You commit and push. Another machine pulls and installs, and its own symlink points at its own clone. There is never a second copy to fork.

**Failure behavior.** If the symlink dangles, because the repo moved or was deleted, sage runs on local memory alone and prints one line saying so. It does not guess a repo path.

### Agents

Sage reuses the four existing saved agents. It does not fork them. One edit is needed: their descriptions read "dispatched by name from an approved orchestration plan" (`claude-agents/explorer.md:3` and the three siblings). Sage has a plan but no approval. Change "an approved orchestration plan" to "an orchestration plan" in all four. The sentence stays true for `/subagents`, and the load-bearing half of that description — "NOT a general-purpose agent" — is untouched.

---

## 4. Document specs

Budgets follow Anthropic's skill-authoring guidance, fetched 2026-08-17: body under 500 lines, references one level deep, a table of contents on any reference over 100 lines.

| File | Budget | Contents |
| --- | --- | --- |
| `SKILL.md` | ≤ 400 lines | Axioms. Step 1 decompose. Step 2 plan and record. Step 3 brief. Step 4 execute and watch. Step 5 verify. Step 6 record and surface. Rails. Stop rule. |
| `references/dispatch.md` | ≤ 200 lines | Task brief, agent report shape, finding schema, risk rubric, snapshot protocol, the **ledger** — which absorbs the plan template and the report template, since both are now sections of it — and the **handoff note** (new). |
| `references/topologies.md` | ≤ 90 lines | The patterns, carried over. Drop the gate-timed offer wording from the acceptance-suite pattern. |
| `references/harness.md` | ≤ 200 lines | Tier resolution, spawning, agent-file fields, cautions, **transcript layout and the token arithmetic** (new). Drop the entire gate-dialog section — 36 lines that delete cleanly. |
| `references/memory.md` | ≤ 120 lines | The two-tier protocol. Append, consolidate, the hint triggers, the promotion procedure, the invariant checks, eviction. |
| `memory/shared.md` | grows slowly | Portable rules only. One rule per block: rule, qualifier, recogniser, strength band, falsifier. No dates. No counts. No costs. |
| `memory/local.md` | grows fast | This machine's numbers. Run log, cost bands, confirmation counts and dates, watch list, harness version stamp. |

Expected total: roughly 60% of the current `/subagents` corpus. Two sources for that figure. The gate and report machinery deletes about 100 lines outright. Compressing one real rule to its floor cut it from 74 words to 45 — 39% — with behavior unchanged and every load-bearing part kept.

---

## 5. The mechanisms

### 5.1 Autonomous run — what replaces the gate

**Sage still does everything the gate forced.** It reads calibration before estimating. It builds the measurement harness first. It resolves every tier to a named model. It classifies every unit reader or writer. It writes the solo alternative and the risks. It prices off a same-shape row before reaching for band arithmetic. All of that was forced by having an audience, and all of it pays without one.

It then writes the plan to the ledger and dispatches. No question. No turn end.

**The assumption log.** This is the piece that makes the gate removal measurable rather than merely asserted. Every time sage resolves an ambiguity that the gate would have surfaced, it writes one row:

```
| assumption | what I chose | what else was plausible | how it would show if wrong |
```

The rows go in the ledger and one condensed line goes in the run record. If you later correct one, sage records the correction next to it. After a dozen runs you will know what the gate was actually worth, which nobody currently does.

**What still stops and asks.** These are safety rails, not planning gates, and they survive. Of the 21 rails in `/subagents`, 17 are enforced by agent-file frontmatter or by Step 4 and 5 procedure and are untouched by any of this. The four that stop:

1. Destructive, irreversible, or externally visible actions. Pushes, deletes, publishes, messages.
2. More than one writer without worktree isolation.
3. A writer wanting to touch a path outside its lease.
4. The budget rail, defined below. In-flight units finish. Nothing new launches.

**The budget rail — 4× the estimate, at two scopes.**

Sage does not carry a fixed token ceiling. It carries a multiplier, applied against the estimate it wrote itself:

| Scope | Ceiling | Floor |
| --- | --- | --- |
| Whole task | 4 × the plan's total estimate | 500k, so a badly under-estimated run is not throttled by its own bad estimate |
| One unit | 4 × that row's own estimate | 150k, just above the measured p50 of 124k |
| Agent count | 2 × the plan's agent count | 10, which is one full escalation for every planned unit |

The same constant at both scopes is deliberate. A per-task ceiling alone lets one runaway unit eat the whole budget before anything notices; a per-unit ceiling alone never sees the aggregate. The watchdog (§5.4) enforces the per-unit half continuously; the between-dispatch projection enforces the per-task half.

Three properties this needs to be safe:

- **Projection, not arrival.** Before each dispatch, add the pending unit's estimate plus everything in flight to what has already landed. A projection built from band midpoints is an *upper bound*, not a forecast, so sage says which kind of figure it is holding when it stops.
- **The estimate must stay honest.** Sage writes the estimate that sets its own ceiling, so the calibration row records estimate against actual on every run, hits included. A drift toward high estimates shows up as a widening gap and becomes a promotion candidate against itself.
- **Reaching the ceiling is a surfaced event, and so is landing well under it.** Both directions are information.

**Wall clock stops being a stop.** In `/subagents` it was bundled into the same rail, and its referent was ambiguous — `SKILL.md:23` attaches the ~25% to wall clock, `SKILL.md:159` to "the printed estimate" unqualified. In sage it becomes a surfaced event only, not a stop-and-ask. Two reasons: nobody is waiting in an unattended run, so elapsed time is not itself a harm; and the runaway it existed to catch is now caught per-agent and continuously by the watchdog, which the aggregate rail never could. This is my call, not your instruction — say if you want it kept as a stop.

**The one honest risk.** You observed it yourself in `summon-teams-idea.md:47-49`: *"in recent sessions, I increased the ceiling x3 every time. The sessions always end up spending up-to the new ceiling."* A 4× ceiling will probably be used, not merely permitted. That is the intent — quality first, and a ceiling that is too low lowers the final result. But it means the multiplier is a knob to measure, not a setting to trust. After ten runs, `local.md` will show whether the spend above 1× bought anything the coordination check could name. If it did not, 4× is the first thing to retire.

Two rails that were gate-dependent get re-homed rather than dropped:

- **The pre-plan scout bound.** It existed as "the one dispatch that legally precedes the gate." In sage it is a plain Step 1 bound: `explorer` type only, at most two rounds, actual cost recorded.
- **Ambiguity that changes the decomposition** was a stop. In sage it becomes an assumption-log row plus a surfaced line — sage chooses, records both readings, and says so. This is the one rail where sage genuinely accepts more risk than `/subagents`, and the assumption log is how you audit it.

### 5.2 The quiet report

**There is one file, and it is the ledger.** It holds the plan, the per-unit table with models and actual costs, every failure and retry, every deviation, the assumption log, the finding dispositions, the diff pointer, the coordination check, and the lessons stored. A report is a *rendering* of that, produced on demand. It is never a second file.

**The ledger is not written for you.** It is written because auto-compact fires at ~1.006M tokens and discards 99.0% of context in one blocking event, mid-run, with agents still in flight. Four things read it back after that happens, and all four are sage: the budget rail needs the recorded estimate to compare against; the write lease and snapshot baseline are the only way back from a bad writer, since `/rewind` does not undo subagent edits; the failure ladder counts signatures across attempts; and handover reconstructs the run from it. Bring it current before launching a wave and after each integration.

**Always printed, every run — three things:**

1. The **Result**. The deliverable, in prose, standing alone. This is what you asked for and it never collapses to a pointer.
2. One **run line**: `sage: N agents · ~Xk · ~Y min · <ledger path>`.
3. Any **surfaced event** from the list below.

**Surfaced events — these print regardless of anything:**

- A rail fired, and whether the figure that fired it was a projection or an actual.
- A writer touched a path outside its lease.
- A security-shaped finding.
- A failed or abandoned unit, and every abandoned disagreement.
- An `Awaiting human` item.
- The coordination check came back negative — the fan-out bought nothing.
- A memory hint is due, promotion or consolidation.
- The watchdog fired, or could not run.
- The handover threshold was crossed.

**Expanded on request.** `sage report` renders the full block from the ledger. The ledger is the source, so the answer survives compaction, which "ask me later" does not.

### 5.3 Two-tier memory

**The split is by content class, not by precedence.** This is the design's load-bearing idea, and it comes from the observation that the existing seed/local split forked because both files held the same kind of thing.

| | `shared.md` — portable | `local.md` — this machine |
| --- | --- | --- |
| Holds | Rules that would hold on any machine. Topology lessons. Ratios and discount factors. Failure recognisers. | Absolute costs. Bands. Run rows. Confirmation counts and dates. Harness version stamp. Watch list. |
| Written by | Promotion only, and only when you ask | Every run, automatically |
| Read at | Step 2 | Step 2 |
| Carries | Rule, qualifier, recogniser, strength band, falsifier | Numbers, counts, dates, provenance |

Because the two never hold the same kind of claim, they cannot contradict each other on the same claim. The residual case: a local run contradicts a portable rule. That does **not** overturn the rule. It becomes a watch-list row in `local.md` that needs its own confirmations, and it appears in the next promotion hint as a **retirement candidate**.

**The three acts.**

1. **Append.** Automatic, every run, to `local.md`. One row: actuals, hits included, and the lesson a future run can act on. Anchor the append on the file's final characters, never on a date cell.
2. **Consolidate.** Automatic when a trigger holds, on `local.md` only, between runs. Rewrite rows into bands and rules, archive originals verbatim. Guarded by two checks, both of which must pass or the pass aborts and writes nothing:
   - The existing self-check: every pre-pass row survives verbatim in exactly one place, the count matches, every band cites a run, every rule carries a date, the result is smaller, both files parse.
   - A new **invariant check**: the file's structural markers — section order, header sentinel, table headers — still match the shape `references/memory.md` declares. This is the check that would have caught the one real corruption, which slipped through an approved human diff.
3. **Promote.** Never automatic. Sage detects and prints one line.

**The hint.** One line, in the surfaced-events class:

```
sage: 3 rules ready → shared, 1 → skill text, 1 retirement candidate. Run `sage promote`.
```

Triggers, all machine-checkable with no judgment:

| Target | Trigger |
| --- | --- |
| → `shared.md` | A rule reaches 3 confirmations, is marked machine-independent, and is not already in `shared.md` |
| → skill text | A rule in `shared.md` reaches 6 confirmations, or a promoted rule crosses a strength band |
| → retirement | A rule's falsifier condition was observed, or two confirmations contradict it |
| → consolidation | `local.md` past ~10k tokens, or 40 rows, or two rows disagree on one band, or structural damage, or a version-bound claim older than the recorded harness version |

**`sage promote` — what it does when you ask.** Read the candidates. For each, write the rule, its qualifier, its recogniser, its strength band, and its **falsifier** — the observation that would retire it. Falsifiers do not exist anywhere in the repo today; grep-verified. Then dispatch one refuting verifier over the whole batch, briefed to default to refuted. Survivors are written. Refuted ones go back to the watch list with the refutation attached. Then print the diff.

**Eviction.** Symmetric to promotion, and absent today. A rule whose falsifier fires is moved to the archive with the observation attached, not deleted.

**The compression floor — never removed under any "make it shorter":** the undated anecdote that makes a rule recognisable in the wild; any number the skill computes with; a rule's qualifier; the literal command that satisfies it; the completion criterion; a precedence sentence wherever two rules can both fire; the strength band; whether a constraint binds or is merely asked for.

### 5.4 The watchdog

Verified on this machine, live, while the survey ran. All numbers below are measured, not estimated.

**What it reads.** `~/.claude/projects/<cwd-slug>/<session-uuid>/subagents/agent-<id>.jsonl`, written incrementally within seconds — proven directly, by an agent locating its own in-flight transcript by grepping for a string from a command it had just run. The sidecar `agent-<id>.meta.json` carries `agentType`, `description`, `toolUseId`, `parentAgentId`, `spawnDepth`. The parent's own transcript is one level up at `<session-uuid>.jsonl`.

**The arithmetic, which is where this goes wrong if built naively.**

Assistant records are **streaming partials**: the same `message.id` is written many times. Measured on one real transcript: 31 records, 8 distinct ids. Summing without deduplication inflates spend **3.56×**, so a rail built the obvious way fires at 28% of real spend and recalls healthy agents constantly. Always `group_by(.message.id) | map(.[-1])` first.

Two formulas, and they differ on one term:

- **Spend** = Σ `input + cache_creation + output` over deduplicated records. **Exclude** `cache_read` — it is re-read context, not spend.
- **Occupancy** = `input + cache_creation + cache_read` on the **single most recent** assistant record. **Include** `cache_read` — those tokens are physically in the window. It is a point-in-time value, never a sum.

**Signals and their honest reliability**, thresholds calibrated from 28,370 real inter-record gaps across 199 completed runs:

| Signal | Reliability | Note |
| --- | --- | --- |
| `done` — any record with `stop_reason == "end_turn"` | Reliable | Gates every other alarm |
| Idle time | Reliable for liveness, noisy as a stall proxy | 40% of healthy runs contain a gap over 120s. Unusable below 300s. |
| Spend, deduplicated | Reliable | p50 124k, p90 533k, p99 3.0M |
| Repeated identical tool call | Reliable | p90 is 1, p99 is 5. Sharp distribution. |
| Repeated tool errors | Noisy | One expected error is common |

**The ladder. Nothing in it recalls an agent automatically.**

| Trigger | Action |
| --- | --- |
| Idle > 600s and not done | Log only. Fires on 7.5% of runs. |
| Idle > 1800s and not done | `SendMessage` asking for a one-line status. Fires on 2%. |
| Same tool call ≥ 4 times | `SendMessage` naming the repeated call |
| Spend > 2× this row's estimate and not done | Log only |
| Spend > 4× this row's estimate — the unit ceiling from §5.1 — and not done | `SendMessage`: report what you have now |
| Spend > 6× this row's estimate, or no reply 600s after two messages | Surface to you. `TaskStop` only on your word. |

The spend rungs are relative to the row's own estimate, floored at 150k, so they hold at any task size. The absolute distribution behind that floor: p50 **124k**, p90 **533k**, p99 **3.0M** across 199 completed runs. A fixed threshold that works for a 40k explorer fires constantly on a 500k reviewer.

**What no signal detects, stated plainly because the skill must never claim otherwise:** the confident-wrong agent, which burns a normal budget and returns a fluent fabricated report; correct-but-irrelevant work; late-degrading reasoning; and machine sleep, which is indistinguishable from a stall. The verification layer stays the only defence for the first.

**Two corrections to the prior review, both verified:**

- `TaskStop` returns nothing usable — its schema carries no partial work. But **the transcript survives the kill**, complete up to the stop, so a wrong recall is recoverable by reading the file. That materially lowers the cost of a false positive, and it is the documented recovery path.
- `SendMessage` drains at the receiver's next tool round, so it cannot reach a genuinely hung agent. The ladder recovers the lost-but-active unit. Only `TaskStop` touches the hung one. Sage must not sell it as covering both.

**Build note.** Host it on `Monitor` with `persistent: true`; every stdout line becomes a notification, so silence must be the default. Measured cost: 0.5s for 7 agents over ~3MB, about 1% of one core at a 60s interval. **Dispatch every unit with an explicit name** — whether a bare `agentId` resolves for `TaskStop` is unverified, and a name is the only guaranteed handle.

**Degradation, in order.** Probe once at start; if the directory is missing or the first parse returns null, disable silently and write one ledger line. Never warn per sample. Never let a parse error on a partially written line fail the run. Fail open — an absent signal means no alarm, never recall. Keep the between-dispatch budget check, because the watchdog is an enhancement that can vanish when the layout changes.

### 5.5 Handover

Requested three times in this repo's history and never built. Sage needs it more than `/subagents` does, because removing the gate also removes the natural turn boundary that used to break long runs up.

**Trigger: parent occupancy ≥ 600,000 tokens.** Justified from measurement, not taste. The window is 1,006,380 tokens — from the single `auto` compaction event on this machine. Auto-compact discards 99.0% of context and blocks for 132 seconds. Measured parent burn with 7 agents in flight was ~7.7k tokens per minute. A good handoff note costs 15–30k. At 600k there are ~400k and roughly 50 minutes of headroom. A threshold below ~500k would fire on runs never in danger: 466,802 was reached in real use without auto-compact.

Advisory at 400k, log only.

`references/claude-code.md:191` currently says the parent "cannot read context usage." The first half is falsified — measured live, moving in real time. The second half, that it cannot compact itself, stands.

**The note contains:** the goal verbatim; the plan with per-row status; every finding harvested so far with `file:line` provenance; **the write lease and the snapshot baseline**, since `/rewind` misses delegated writes and the baseline is the only way back; every path touched; open questions and the current hypothesis; approaches discarded and why; and the `agentId → description` map plus the `subagents/` directory path, so a fresh session can mine the transcripts of agents whose reports were never absorbed.

**Where:** `.claude/plans/sage-handoff-<session>-<timestamp>.md`. Durable and gitignored.

**The honest constraint, and sage must state it in its own text.** Handover ends in a human action. A skill with no gate and no report has removed the actor its handover depends on — the note goes to a path nobody was told to read. So the handoff path is a surfaced event, unconditionally. This is the one place a quiet design must speak.

---

## 6. What carries over

| From `/subagents` | Into sage |
| --- | --- |
| Three principles, decomposition rules, safety and worth tests | Verbatim. This is the thesis and it is measured. |
| Tier → model → effort table, four saved agents | Verbatim. Reused, not forked. |
| Task brief contract, agent report shape, finding schema | Verbatim. |
| Snapshot protocol, write leases, ledger | Verbatim, and load-bearing harder than before — the ledger is now the whole recovery story, and it absorbs the plan and the report as sections rather than leaving them as separate files. |
| Failure ladder with signature counting | Verbatim. |
| Verification layer: disjoint mandates, adversarial refutation, self-directed refuter, settle-with-a-command | Verbatim. This is the defence against the one failure the watchdog cannot see. |
| Topologies | Verbatim, minus gate-timed offer wording. |
| Mid-run rails | Four kept as stops (§5.1). Two re-homed. |
| Coordination check | Kept, and promoted to a surfaced event when negative — it is the only line that can falsify the skill's own premise, and with the cost framing softened it is also the only remaining brake on ritual fan-out. |
| Plan gate | **Removed.** Plan written, never presented. |
| Report as final message | **Removed as a phase, and as a file.** It becomes a rendering of the ledger, printed as one line and expanded on anomaly or on `sage report`. |
| `Workflow` backend split | **Removed.** |
| Gate-dialog mechanics, digest template, preview budgets | **Deleted.** ~66 lines that delete cleanly rather than needing rewriting. |
| `plan-only` mode | **Removed.** Superseded by handover, which writes a richer note and triggers on a measurement. |

---

## 7. Installer changes

Five, and two of them must land together or they compound into data loss plus an unbounded backup loop.

1. **Refactor the primary-skill block into a function** taking source, destination, and a list of user-data paths to exclude. `install.sh:7-41` already contains a working version of every piece — exclusion from `--delete`, seed-once, drift notice. Call it twice rather than duplicating 35 lines.
2. **Create the shared-memory symlink** at install: `~/.claude/skills/sage/memory/shared.md` → the absolute path of `sage-claude/memory/shared.md` in the repo the installer ran from. Exclude `/memory/` from the rsync so `--delete` never touches it.
3. **Seed `local.md` once**, from `local-seed.md`, never overwriting.
4. **Fix the eco-skill loop, which is broken today for anyone.** `install.sh:135` runs `rsync --delete` with no excludes, and `install.sh:124` runs `diff -rq` that exits non-zero on an only-in-destination file. Both reproduced. A runtime-written file under an eco skill is deleted *and* triggers a full backup of that skill directory on every install, forever. These two fixes must ship together.
5. **Do not reuse the header drift notice.** Comparing bytes across a boundary that a sanctioned rewriter is licensed to cross latches on permanently and misattributes the cause — that is exactly the live bug. Sage's local memory carries a **version stamp** that the consolidation pass is instructed to preserve, and the installer compares that.

---

## 8. Build sequence

Six steps. Each is independently checkable, and steps 1–3 give a working skill.

| Step | Deliverable | Done when |
| --- | --- | --- |
| 1 | `SKILL.md` + the four references, gate and report machinery removed, axioms written, hand-batched only | A fresh session runs `/sage` on a real task end to end, no human input after invocation |
| 2 | `memory/shared.md`, `memory/local-seed.md`, `references/memory.md`; installer changes 1–3 and 5 | Install, run once, confirm the row lands in `local.md` and a write to `shared.md` shows in `git status` |
| 3 | The quiet report as a ledger rendering, the surfaced-event list, the assumption log | A run with a deliberate rail trip prints exactly the Result, the run line, and the rail — nothing else. `sage report` reproduces the full block from the ledger alone. |
| 4 | `bin/sage-watch.sh` and the `Monitor` wiring, notify-only | Runs against a live session, correctly classifies done vs stalled, fires on nothing healthy across ten runs |
| 5 | Handover: trigger, note template, resume path | A run driven past 600k writes a note a fresh session can resume from |
| 6 | The promotion path: falsifiers, the refuting verifier, eviction, invariant check; installer fix 4 | `sage promote` produces a diff you accept, and a second run straight after proposes nothing |

Do not grant the watchdog any autonomous action beyond a `SendMessage` until its false-positive rate has ten runs of evidence in `local.md`. That is the one place this design could make things worse rather than better.

---

## 9. What would falsify this design

Each of these is a real way sage could be worse than `/subagents`. Each has a check.

| Risk | How you would see it | What it costs to reverse |
| --- | --- | --- |
| The gate was load-bearing and the assumption log proves it | Assumption rows you keep correcting, especially on scope | Low. Add one stop at Step 2. The plan is already written. |
| Quiet reports let a wrong lesson compound | A `shared.md` rule you disagree with, dated back several runs | Medium. Falsifiers and eviction exist for this, but they are untested. |
| The watchdog recalls healthy agents | A recalled unit whose transcript shows normal work | Low. It is notify-only until step 4 passes, and the transcript survives. |
| Agent-targeted docs become unrepairable when they corrupt | A memory file you cannot read well enough to fix | This is the real cost of D5, and it is the one the review argued hardest against. The invariant check is the mitigation. It is not a guarantee. |
| Sage fans out ritually with no human to say "solo" | Coordination checks that keep coming back negative | Low. The check is surfaced when negative, exactly so this is visible. |
| Two machines edit `shared.md` and conflict | A git merge conflict | Low. One rule per block keeps conflicts local. |
| The 4× ceiling gets consumed rather than used | Actuals landing near 4× on runs whose coordination check names nothing the extra spend bought | Low, and it is measured by construction — `local.md` records estimate against actual every run. Retiring 4× is a one-line change. |

---

## 10. What agent-targeted writing means here

Concretely, not as a slogan. From the style research, three sources: this repo's measured practice, the installed `writing-for-agents` skill, and Anthropic's published guidance fetched 2026-08-17.

**The target is minimal, not short.** A cut that changes what a fresh instance does is a spec change.

**The rules sage documents follow:** state the reader's job in the first two lines. One meaning, one place — never state a rule twice. Delete a sentence entirely if it does not change behavior against the model's default. Do not cache what one command answers. Prompt the positive; a bare prohibition makes the banned thing more available. Use leading words that recruit priors — *gate*, *lease*, *rail*, *ladder*, *band*, *lens*, *floor* — and repeat the token, never the definition. Attach every rule's trigger, action, and qualifier; never two of the three. Carry evidence as a strength band, never as a count or a date. Encode a binary condition as `condition → action`. Give each tier of a classification its whole recipe rather than making the model compose one. State exceptions inline with the rule, not in a later section. State the rule's own known blind spot, or the model will not compensate for it.

**No sentence-length cap.** Measured: this repo's working agent docs average 31.7 words per sentence against the house human style's 12.7, and they are the ones that work. A qualifier folded into the sentence carrying its rule costs fewer tokens and stays bound to it.

**One correction worth carrying.** The widely repeated claim that Anthropic flags all-caps `MUST`/`ALWAYS`/`NEVER` as an authoring problem could not be verified in primary sources — it traces to a third-party repository. The real guidance is narrower: dial back aggressive language when a skill *overtriggers*. `/subagents` uses one shouted hard stop, once, at its only irreversible boundary. Sage may keep that pattern.

**A worked example**, taken from `subagents-claude/SKILL.md:178`. As-is, 74 words:

> **A reader's structural claim is a lead, not ground truth — run it before you build on it.** One reader described a data structure that does not exist; three recon claims in another run were wrong; a researcher's headline version-attribution finding was wrong, and briefing the fix it implied would have introduced the defect it claimed to remove. Fetch the primary source locally and grep it yourself: a summarising fetch tool generates leads, it does not settle facts (calibration: recurring).

At the floor, 45 words — 39% shorter, behavior unchanged:

> **A reader's structural claim is a lead, not ground truth.** One reader described a data structure that does not exist; a researcher's headline version attribution was wrong, and the fix it implied would have introduced the defect it claimed to remove. Fetch the primary source locally and grep it yourself (calibration: recurring).

Cut further and it breaks in a specific order. "Verify subagent claims before use" is four words, still true, and useless: the trigger word *structural* is gone so it fires on everything or nothing; the literal command is gone so "verify" is satisfiable by asking a second model, which is the failure rather than the fix; the anecdote is gone so the rule has no shape to match against; and the band is gone so it cannot be traded off against anything.

---

## 11. Decisions I need from you

Everything else I will pick and record.

1. **Repo location.** `sage-claude/` at the root, matching `subagents-claude/`, with its own installer block. The alternative is `claude-skills/sage/`, which auto-installs with no installer edit but sits on the broken eco loop. I recommend the root, and fixing the eco loop separately since it bites anyone. -> agree
2. **Invocation.** `disable-model-invocation: true`, so `/sage` is manual like `/subagents`. Flipping it later is one line, and I would rather it earn that. -> agree
3. **The four shared agent files.** The one-word description edit touches `/subagents` too. Say if you would rather I fork them for sage instead — it costs a duplicate maintenance surface, which this repo has already paid for once. -> make the agents work for both subagents and sage skills.
4. **Build scope now.** Steps 1–3 give you a working sage. Steps 4–6 add the watchdog, handover, and promotion. I can build all six, or stop at 3 and let real runs shape the rest. -> build all
