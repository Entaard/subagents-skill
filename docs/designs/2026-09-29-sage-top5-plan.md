# Sage (Claude): top five improvements — implementation plan

**Date:** 2026-09-29 · **Harness:** Claude Code 2.1.284 · **Parent model:** Opus 5.5
**Scope:** `sage-claude/`, `claude-skills/sage-promote/`, `claude-agents/`, `claude-agents-alt/`, `install.sh`. The Codex sage under `sage/` is out of scope.
**Evidence:** `docs/designs/2026-09-29-sage-top5-evidence/`. Every number in this plan comes from a file in that folder, unless it is marked **E** (estimate) or **O** (opinion).

---

## 0. Read this first (for the agent that will implement this plan)

You are a new session. You have none of the study context. This section tells you what you need.

### 0.1 What the sage is

`/sage <task>` is a skill. It runs an unattended multi-agent orchestration. The parent model plans, sends subagents, reviews their work with separate lenses and adversarial checkers, and writes everything to a ledger file (`.claude/plans/sage-ledger-<session>.md`). `/sage-promote` is a separate skill. It moves lessons from the sage's journal into memory files and into the sage's own text.

- Source: `sage-claude/SKILL.md` (the spine) and `sage-claude/references/*.md` (one file per step).
- Scripts: `sage-claude/bin/` — `sage-lint.sh` (ledger checker), `sage-watch.sh` (occupancy sensor), `sage-index.sh` (memory index), `sage-alt-guard.sh` (hook).
- Saved agents: `claude-agents/*.md` (explorer, verifier, web-researcher, implementer) and `claude-agents-alt/*.md.in` (templates for agents on non-Anthropic models, rendered by `install.sh` from `~/.claude/subagents-alt-models.conf`).
- Memory: repo seeds in `sage-claude/memory/`. The live copy is `~/.claude/skills/sage/memory/` (journal, `local/`, `shared/`, `archive/`).
- `install.sh` copies the repo into `~/.claude/`. **Never edit files under `~/.claude/` by hand, except memory data that a step below names.** Edit the repo, then run `./install.sh`.

### 0.2 The measured problem, in five lines

1. **It is slow.** The five slowest runs took 84–215 min (a total of 664 min). Serial review-and-fix rounds took 57% of that time. Parent generation with no agent running took 29%. About three quarters of that generation time went to hidden reasoning tokens (**E**, estimated from visible characters ÷ 4).
2. **About a fifth of the parent's work is bookkeeping.** In 9 sessions, turns that touched only the ledger, lint, sensor, journal or index took 18–54% of the parent's tool-turn time and 16–54% of its output tokens.
3. **Most of that machinery never fires.** 0 compactions in 13 of 13 measured sage sessions on a 1M window. The only session that compacted used a 200k window. The checkpoint rung never fired in real use. The whole-task budget rail never fired, even at 3.8× the estimate. `/sage report` was used 0 times.
4. **Quality escapes happen before and after the review phase, not inside it.** 7 of 17 late finds were framing errors: a wrong premise, the wrong scope, or an unmet purpose. The rest were defects in text the parent wrote, or behaviour that no reader could see. 63 checker units made 1,557 read calls but ran only 42 test or build commands.
5. **Promotion yields little.** Seven passes added two shared rules, and one was later archived. They minted about 50 local knowledge items (KIs); 73 of 95 local KIs have never been used. Stage three (the model-lineup refresh) took 41% of pass spend.

### 0.3 A live breakage you must fix first

On 2.1.284, the `sonnet` alias moved to Sonnet 5.5 (`CHANGELOG.md` 2.1.284: "Added Claude Sonnet 5.5 (`claude-sonnet-5-5`), now the default Sonnet model"). Today, one subagent dispatched with the `sonnet` alias failed with `HTTP 403 team not allowed to access model` on `claude-sonnet-5-5`. A probe two hours later ran on `claude-sonnet-5-5` without error. **Access is not stable.** `explorer`, `implementer` and `web-researcher` all use `model: sonnet`. Item 1 fixes this.

### 0.4 Constraints on how you work

- **Branch first.** You are on `main`. Create a branch per item, for example `sage-top5/1-lineup`.
- **Chesterton's Fence.** Before you delete a rule, find the evidence behind it (git log -S, the journal, the KI). If you cannot explain it, keep it or ask. Section 7 lists the rules that must stay.
- **One home per rule.** Before you add a sentence, grep the corpus for the same rule. `sage-lint.sh --corpus sage-claude` checks citations and word budgets.
- **Subagents cannot write report files on this build.** The harness blocks a subagent `Write` to a `report.md`-like path: "Subagents should return findings as text, not write report files". Other scratch writes (scripts, data) work. Tell units to return reports as text.
- **Do not commit or push without the user's word.** Deliver each item as a branch with a clean working tree diff, and ask.
- **Write prose in the repo's style** (Simplified Technical English, `output-styles/simplified-technical-english.md`).
- **Model and effort rule for your own session:** follow item 1's findings. Do not dispatch with `model: sonnet` until item 1 lands.

### 0.5 Order of work

| Order | Item | Why this order |
|---|---|---|
| 1 | Item 1 — lineup and effort | A live breakage, and it is small. |
| 2 | Item 2 — cut bookkeeping | It frees about half of the run-loaded words. Items 3 and 4 need that room. |
| 3 | Item 4 — faster verify loop | It builds on item 2's smaller ledger. |
| 4 | Item 3 — framing and executable evidence | It adds text, so it must come after the cuts. |
| 5 | Item 5 — sage-promote | Independent. It can run in parallel with items 3 and 4 in a separate worktree. |
| 6 | Section 8 — validation | Replays past tasks, before and after. |

---

## 1. Item 1 — Pin the lineup and set effort per role

### 1.1 Problem

**F (facts):**
- The alias targets moved three times in four weeks: `fable` at 2.1.257, `opus` at 2.1.280, `sonnet` at 2.1.284 (`05-vendor-harness-facts.md` #2). Every move changed which model sage agents ran, and no one decided that.
- `sonnet` is now Sonnet 5.5. This account got HTTP 403 on it (section 0.3). Sonnet 5 is still served, as a legacy model, with retirement not sooner than 2027-06-30. Sonnet 5 and Sonnet 5.5 have the same price ($2/$10).
- A plain dispatch inherits the session effort (`docs/sub-agents.md:315`, "Default: inherits from session"). The user's session default is `xhigh`. This session's five study agents ran at `xhigh` on every record. `harness.md:87` says a plain dispatch has "no control" and records `medium (no control)`. That is wrong.
- The parent ran at `high` or `xhigh`. The Opus 5.5 prompting guide says: "Start at `medium`, the default on Claude Opus 5.5 ... Claude Opus 5.5 at `medium` matches or exceeds Claude Opus 5 at `high`" and "At a given level, Claude Opus 5.5 tends to think more per turn than Claude Opus 5, especially at `xhigh` and `max`." The parent's hidden reasoning share was about 70–92% of its output (**E**: output tokens minus visible characters ÷ 4, `00-facts.md`).
- The effort blog (2026-09-25): one build took 1.5 min at `low` and 67 min at `max`. Anthropic's own loop is "implementing on low effort, reviewing what it built, and then running verification on high effort".
- `harness.md:50–60` states the old model precedence. Since 2.1.251 (`CHANGELOG.md:1745`), the order is: per-dispatch `model` → frontmatter → `CLAUDE_CODE_SUBAGENT_MODEL` → main model. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` (2.1.257) forces one model.
- A saved agent file accepts a full model ID (`docs/sub-agents.md:306`: "a full model ID such as `claude-opus-5-5`"). A per-dispatch `model` value overrides the frontmatter, so passing `model: sonnet` to a pinned agent undoes the pin.
- `harness.md` has other stale facts, listed in `05-vendor-harness-facts.md` (a):
  - "Saved agent model edits apply next session" is wrong. The agents directory is watched.
  - `run_in_background` was removed in interactive fork mode.
  - `omitClaudeMd` exists.
  - `isolation: worktree` branches from the default branch, not HEAD, unless `worktree.baseRef: "head"` is set.
  - Monitor's `persistent` option was removed in 2.1.271, but `execute.md:21` still says `persistent: true`.
  - `SubagentHandback` exists.
  - `TaskStop` accepts an agent ID.

**O (opinion):** the parent's effort is the largest single wall-clock lever that the skill does not control. A skill can set it: skill frontmatter accepts `effort` ("Overrides the session effort level", `docs/skills.md:364`).

### 1.2 Changes

1. **Pin full model IDs in every saved agent file.**
   - `claude-agents/explorer.md`, `implementer.md`, `web-researcher.md`: `model: claude-sonnet-5`. First run the probe in step 6. If `claude-sonnet-5-5` is stable for this account, pin that instead, and record the choice.
   - `claude-agents/verifier.md`: `model: claude-opus-5-5`.
   - Leave the alt templates alone. They already carry full IDs from the conf file.
2. **Set effort per role in frontmatter.** Opus 5.5 at `medium` matches Opus 5 at `high`, so shift each role down:
   - `explorer` → `low` (no change).
   - `web-researcher` → `low`.
   - `implementer` → `medium` (no change).
   - `verifier` → `high` (no change). Adversarial checking is where effort pays.
3. **Stop plain dispatches from inheriting `xhigh`.** In `dispatch.md` and `harness.md`, state it once:
   - A plain dispatch runs at the session effort.
   - Every unit that does not need a specific role goes through a saved agent file.
   - The sage never passes `model:` to a saved agent. That would undo the pin.
   - Delete the `medium (no control)` cell value everywhere.
4. **Set the parent's effort in the sage skill frontmatter.** Add `effort: medium` to `sage-claude/SKILL.md`.
   - Add a Defaults row: `Parent effort | medium — set in this file's frontmatter; raise only for a task you name as long-horizon and ambiguous`.
   - **Validate it first** (section 8, test V1) and record the result. If V1 shows a quality loss, use `high`. Never use `xhigh` as the default.
5. **Rewrite `harness.md` `## Models and effort` and `## Spawning` against the current docs.**
   - Use the precedence order and the `_FORCE` variable.
   - Use `resolvedModel` / `modelsUsed` on the Agent result as the measured model (`docs/hooks.md:1754–1765`).
   - Record that `totalTokens` covers the final request only.
   - Fix every stale fact in 1.1. Delete `persistent: true` from `execute.md:21` and `sage-watch.sh:50`.
   - Keep the file under its current size. Delete old version trivia and move dated figures to `harness-measurements.md`.
6. **Add a lineup probe to `install.sh` (optional, low cost).** After installing agents, print one line per pinned model, with a note that a probe dispatch settles access. Do not dispatch from the installer. Print the command the user can run instead.

### 1.3 Acceptance criteria

- A1. `grep -h '^model:' ~/.claude/agents/{explorer,verifier,implementer,web-researcher}.md` prints full IDs only, after `./install.sh`.
- A2. One dispatch per role, with no `model` parameter, returns. Its transcript `message.model` equals the pinned ID, and its `effort` field equals the frontmatter value. Settle both by grep on the transcript.
- A3. `grep -rn 'no control' sage-claude/` returns nothing.
- A4. `sage-lint.sh --corpus sage-claude` is clean.
- A5. The sage run in V1 shows the chosen parent effort (`medium`, or `high` if V1 chose it) on parent records, and the Defaults row names the same level.

### 1.4 Risk

- A pinned ID retires. Sonnet 5 has a floor of 2027-06-30. The item 5 lineup check watches for this.
- `medium` parent effort misses a hard edge case. V1 measures this. Higher effort "does not fix when the model has the wrong approach" (effort blog), and item 3 targets the wrong-approach failure directly.

---

## 2. Item 2 — Cut the bookkeeping that never fires

### 2.1 Problem

**F (facts):**
- Bookkeeping-only turns took 18–54% of parent tool-turn time and 16–54% of parent output tokens (20k–130k per run) in 9 sessions (`02-obsolete-practices-inventory.md` §0).
- Ledger rewrites were 43 of the 52 bookkeeping minutes in the slow runs. The parent wrote them as hand-made Python replace heredocs of 1–13k characters (`01-perf-wall-clock.md`, sink 4).
- The ledger lint ran 5–41 times per run. Its mid-run output was mostly the expected "section 'Run record' is missing" line: 12 of 12 lines in 54dd10c5. All its real catches were closure checks: a parked triage cell and orphan findings.
- The watchdog and checkpoint rung produced 0 events in 7 of 7 measured runs. 13 of 13 measured 1M-window sessions never compacted. The one that did (a58bd85c, 200k window, 15 compactions) did not host the watchdog, and every unit report still arrived.
- The budget rail fired twice in 42 ledgers, both in August, at unit scope. The whole-task rail never fired, even at 3.8×. In 54dd10c5 a unit crossed its ceiling (281k against 240k), and nothing recorded it. The actual ranged from 0.23× to 3.8× the estimate.
- The two rail texts disagree. `SKILL.md:92` says that firing a rail ends the turn. `execute.md:37` says that in-flight units finish and only new launches against that row stop.
- `/sage report`: 0 uses in 18 sessions. `/sage resume`: 1 use (61de7190, after a 429), and it used the sha256 baseline.
- The Plan table and the Unit table duplicate each other. The lint's `plan-unit` and `amend-tag` checks exist only to keep them in sync.
- The run-loaded set is ~20,500 words (budget 20,000). The Codex sage's spine is 515 words.
- Anthropic "removed over 80% of Claude Code's system prompt for models like Claude Opus 5 and Claude Fable 5 with no measurable loss". It advises: rules → judgement; everything upfront → progressive disclosure; "Avoid making them [skills] overconstrained, except in highly important areas" (`05-vendor-harness-facts.md` (b)3).

### 2.2 Changes

Work from `02-obsolete-practices-inventory.md`. Its rows are keyed A1–J4 with file:line. Apply the cuts below. For every other row, apply the inventory's proposal only when its class is OVER-SPECIFIED and the evidence column shows nothing for it.

1. **Watchdog out of the run path.** Inventory rows E6, E7, E8, F2, C7, I7.
   - Delete from the run-loaded text: the three-step host procedure (`execute.md:17–33`), the checkpoint rung, the ledger header comment (`dispatch.md:140–146`), `SAGE_WINDOW`/`SAGE_COMPACT_AT` stamping, and the `compact=` surfaced event.
   - Keep `sage-watch.sh`, but only as a close-time measurer: one `--status` call at Step 6 for the run line and the alt-row spend.
   - Keep the `SessionStart(compact)` hook.
   - Add one rule: "On a parent window of 400k or less, host the watchdog (`bin/sage-watch.sh` header)." That keeps the only case where compaction happened.
2. **Lint at closure only.** Inventory rows E5, G15. Run `sage-lint.sh` at Step 6 and before each commit. Delete the "four acts at every bring-current point" rule (`execute.md:15`). Keep the lint's checks unchanged.
3. **A ledger helper script.** Add `sage-claude/bin/sage-ledger.sh` with five subcommands:
   - `init <path>` writes the section skeleton.
   - `unit <id> <field>=<value>...` upserts one row.
   - `finding <id> <severity> <location> <triage> <evidence>` upserts one row.
   - `decision <text>` appends one row with the next id.
   - `close` runs the lint, runs `sage-watch.sh --status` once, appends the journal lines given on stdin, and tails the journal.

   The parent calls the helper instead of hand-writing Python edits. Write it in bash + awk, like the other scripts, with a run block at the top. Add tests: a fixture ledger in `sage-claude/bin/tests/`, run by a `--self-test` flag.
4. **Four ledger sections, not eight.** Inventory rows F3–F9.
   - `### Plan`: the task fields (see item 3) plus **one** unit table. Its columns are id, unit and done-when, R/W, agent (model), flow, state, agentId, evidence.
   - `### Decisions`: one table for assumptions, deviations, dropped disagreements, discarded approaches and rail-1 authorisations. Each row has a `kind` column.
   - `### Findings`: unchanged schema.
   - `### Run record`: Outcome, Cost, Verification (MEASURED vs JUDGED), Coordination check, Gaps, Awaiting human.

   Keep `### Resume state` as a **small, current** record: step, next action, write lease, baseline and hashes. The installed `SessionStart(compact)` hook (`install.sh:1090`) tells every compacted session to read this section, and `dispatch.md:200` says a stale one is the same as none. So:
   - write it at Plan time, even on a read-only run;
   - update it at each wave launch and at each integration, by one `sage-ledger.sh restamp` call (a cheap helper call, not a hand edit);
   - drop only its `checkpoint:` and `watchdog:` lines.

   **Update `sage-lint.sh` for the new schema.** Retiring checks is not enough, because the kept checks find their tables by section name:
   - `state-enum` finds the unit table only under the heading `Unit table` (`sage-lint.sh:1371–1378`).
   - The triage checks find findings only under `Findings and dispositions` (`sage-lint.sh:1452–1459`).
   - Under the new headings, both checks go silent. The refuter proved this with fixtures: `state=banana` and `triage=pending` fail under the old headings and pass under the new ones.

   Changes to the lint:
   - Retire `plan-unit`, `amend-tag` and `header`.
   - Retarget `state-enum` to the state column of the `### Plan` unit table.
   - Retarget `triage-orphan`, `triage-state`, `findings-shape` and `disclosure-home` to `### Findings`.
   - Point `sections` at the new list.
   - Keep `secret-shape` and `splice`.
   - Add negative fixtures for every kept check under the new schema (a bad state word, a parked triage cell, an orphan finding id, a secret-shaped string). Each fixture must print its violation.
   - An old-format ledger may exit 3 with a one-line note. A ledger is never read by a later run.
5. **Replace the token budget rail with a simpler rule.** Inventory rows E9, J3, C2, C3, C4, H7.
   - Delete the Est column, the per-unit and whole-task token ceilings, the floors, the projection rule, and the review-pricing prose (`dispatch.md:9–13`).
   - Keep the agent-count ceiling (2× the planned count, floor 10).
   - Add one line: "A unit that runs far past what you expected is a surfaced event. Read its spend at harvest."
   - Keep an optional wall-clock target line in the Plan. Item 4 uses it.
   - This also removes the rail contradiction. Rail 4 no longer exists, so rails 1–3 are the only stops.
6. **Move conditional and maintainer content out of the run-loaded set.** Inventory rows B8, B10, C12–C14, D3, D8, I1, I5, I6, I8, I9, calibration tags.
   - Topologies #10 (blind suite) and #12 (two-arm lens): move to a new `references/conditional.md`. Read it only when a plan names one of them.
   - Memory mechanics: move to `memory-contract.md`.
   - Install-time and version facts: move to `harness-measurements.md`.
   - Strip the 25 `(calibration: ...)` tags from run-loaded text. They stay in the KI sidecars.
7. **Shrink the spine.** Inventory rows A1–A4. Cut each Step paragraph in `SKILL.md` to one or two lines plus its pointer. Cut the References list to the files a step does not name. Target: ≤1,000 words.
8. **Delete restated harness behaviour.** Inventory rows E1, E11, D6, D14. The tool descriptions already say it: batch agents in one message, background by default, never fabricate a pending result, how `SendMessage` works.
9. **Compress the failure ladder to three sentences.** Inventory row E4. "A wrong-brief failure gets a fresh agent with a corrected brief. A could-not-finish failure gets one steer, then a stronger tier. The same failure signature twice reopens the plan." Keep the stop rule in `SKILL.md`.
10. **Update the budgets.** Set the run-loaded budget to 12,000 words and the spine budget to 1,000 in `SKILL.md` Defaults and in the lint's corpus mode.

### 2.3 Acceptance criteria

- B1. `sage-lint.sh --corpus sage-claude` is clean, and it reports the run-loaded set at ≤12,000 words (**E** from the inventory: ~10,500).
- B2. `sage-ledger.sh --self-test` passes. It writes a ledger that `sage-lint.sh` accepts with no output. Each negative fixture from change 4 makes `sage-lint.sh` print its violation and exit 1.
- B2a. The hook text in `install.sh:1090` still names a section that every ledger has from Plan time on. Check this by grep on a read-only fixture ledger.
- B3. Every row in section 7 ("must stay") still has its rule at full strength in exactly one run-loaded file. Check this with a grep list that you write first and commit with the change.
- B4. `install.sh` into a sandbox `HOME` succeeds twice in a row, and a byte-compare shows no `.bak` clobbering. The installer is a known place for hidden defects (see the seed run on 08-05).
- B5. A cross-family gate reviews the diff with the verbatim section 7 list as its mandate: "did any cut remove a must-stay rule?" Use `refuter-alt` after a lane probe. The gate returns no unresolved blocker or major finding.

### 2.4 Risk

- **A cut removes a rule that was load-bearing.** Mitigations: B3, B5, and the V2 replay. Do not cut to paraphrase. The d4096102 run shows that whole-file paraphrase did not converge, and two regression lenses then found ~30 missing rules. **Delete whole sentences, or move them, by exact match.**
- **The ledger format changes, so old ledgers no longer lint.** That is acceptable, because a ledger is never read by a later run.

---

## 3. Item 3 — Frame the task, then buy executable evidence

### 3.1 Problem

**F (facts):**
- 7 of 17 late finds were framing errors (`03-quality-ceiling.md`):
  - a58bd85c G1: every criterion passed, but the user's purpose was not met.
  - cf35cb78: the parent's wrong hypothesis went into a brief as ground truth.
  - 61de7190: the wrong corpus scope.
  - c81599fd: a wrong premise.
  - After 42dd56d4 the user wrote: "I was surprise it doesn't have these suggestions".
- The skill has no framing step. `SKILL.md:47` says "The invocation settled…". The Plan field is `TASK: <one line>` (`dispatch.md:151`).
- The pre-write plan critic (#11) ran twice, both on 08-18, and both times it refuted the design before any code. It has not run since.
- 63 checker units: 1,557 read calls against 42 test or build commands. 9 of 61 review units ran no behavioural command. "Never run in the real environment" is a standing Gap in 6 run records.
- The blind acceptance suite (#10) triggers only when "the plan carries a writer unit" (`topologies.md:62`). The parent held the pen in 8 of the last 10 writing runs, so the suite was excluded. `full` was never chosen, in 42 ledgers.
- In 54dd10c5, the secret-leak fix failed twice by sanitising. A hostile-input test written before the fix would have shown it. The Standards reader that built its own `-race` repros found the blocker.
- `verifier.md:85` tells a reviewer to "treat a silent brief as a denial" for network use. Briefs forbade discriminating commands (e4bebf20 lens A "named two discriminating commands it was forbidden to run").
- The adversarial pass at the parent's own fixes is the best-evidenced practice: 18 journal confirms. Keep it.

**O (opinion):** the sage is strong at adversarial reading after the artifact exists. It is weak before the artifact exists (framing) and at execution. With frontier workers, the leverage has moved to those two ends.

### 3.2 Changes

1. **A framing block in the Plan.** In `dispatch.md`, replace `TASK: <one line>` with these fields:
   - `ASK:` the user's words, verbatim.
   - `PURPOSE:` what the user will do with the result, quoted if stated, else "not stated — inferred: …".
   - `PREMISES:` each load-bearing assumption, with the command that tests it.
   - `DELIVERABLE:`
   - `APPROACHES:` at least two, the chosen one, and why.

   Rule: **test every premise with its command before you write a brief.** A failed premise is a Decisions row and a re-plan.
2. **A framing critic by default at medium risk and above.** Merge #11 into this rule. Delete the separate #11 topology text.
   - Before the first writer or the first review wave, dispatch one critic. Use `refuter-alt` where it is cleared by the lane probe, else `verifier`.
   - It gets ASK, PURPOSE, PREMISES, DELIVERABLE and the acceptance criteria, but not the parent's reasoning.
   - Its mandate: "Refute that these criteria, if they pass, give the user what the ASK and PURPOSE need. Refute each premise you can test."
   - Add one criterion at the PURPOSE surface.
   - Cost **E**: 30–60k tokens, 5–10 min. It runs in parallel with the first scouts where possible.
3. **An optional up-front question.** Add a Defaults knob, `Up-front questions: off | once` (default `off`, to keep the run unattended).
   - With `once`: at most 3 questions, in one `AskUserQuestion` call, before Step 2.
   - Ask only about ambiguity that changes the decomposition and has no observable falsifier.
   - The user's organisation says interactivity belongs in planning. This knob lets the user opt in.
4. **Executable acceptance, whoever writes.** In `topologies.md` #10 (moved to `conditional.md` by item 2):
   - Delete the writer-unit precondition. A parent writer is the strongest reason for an independent suite.
   - Where the repo can build and run tests, the default is `full`.
   - Add three rules to `verify.md` and to `implementer.md`:
     - **Reproduce first.** A defect fix starts with a command or test that fails on the baseline. Record it as MEASURED.
     - **Hostile inputs first.** For a security, parsing, redaction or escaping criterion, write a table of hostile inputs before the fix.
     - **Mutation check.** For each blocker or major fix, revert the fix and confirm that its test fails. Record both runs.
5. **Let checkers execute.** In `verifier.md`, `verifier-alt.md.in` and `refuter-alt.md.in` (the three checker files; `explorer` has no shell), add: "Where a command would settle a finding, run it in your scratch path or a worktree, or name it as a blocked check. Never argue a point a command could settle."
   - Keep the no-write rule for the repo tree. The 54dd10c5 lesson is that a Bash reviewer wrote test files into the tree, so briefs name a scratch path outside the repo.
   - The Spec verdict names the command that decided each criterion, or says `judged`.
6. **A final end-to-end run.** In `verify.md`, before the completion claim, one unit (or the parent) runs the deliverable the way the user will: the installed copy, the first dispatch of a new agent, the real binary, the live query.
   - Use a sandbox `HOME` or read-only access. Never cross rail 1.
   - If it cannot run, the Result's first caveat names the command that would settle it.
   - `record.md`: a runtime claim that nothing ran is JUDGED.
7. **Two stage columns in Findings.**
   - `stage`: frame / plan / r1 / r2+ / final-run / post-close / user.
   - `author`: parent / unit / pre-existing.

   These columns make the effect of this item measurable over the next runs (section 8, M1).

### 3.3 Acceptance criteria

- C1. The Plan template has the five framing fields. `sage-lint.sh` flags a ledger with no `ASK:` line (a new check `frame`).
- C2. `grep -n 'writer unit' sage-claude/references/*.md` no longer shows the suite precondition.
- C3. The three checker files (`verifier.md`, `verifier-alt.md.in`, `refuter-alt.md.in`) carry the "run it or name it as blocked" rule once each.
- C4. V3 (section 8) shows that the framing critic or a premise test catches at least 2 of the 4 known framing escapes when their tasks are replayed.
- C5. The run-loaded set stays ≤12,000 words after this item.

### 3.4 Risk

- **Cost.** A framing critic and a suite add 50–150k tokens and 10–20 min, mostly in parallel (**E**). The hypothesis (**O**) is that item 4's savings cover it. Nothing has measured that yet, so watch the V2 and V3 wall clock.
- **A critic finds gaps in sound work.** "Reviewers report what you ask them to look for" (`verify.md:12`). Scope the critic's mandate to refutation, and pre-bless "no findings".
- **Executing checkers mutate the tree.** Mitigation: scratch paths, worktrees, and a sandbox `HOME`, as above.

---

## 4. Item 4 — Make the verify loop fast

### 4.1 Problem

**F (facts, `01-perf-wall-clock.md`):**
- Serial review-and-fix rounds took 380 min, 57% of the five slow runs. a58bd85c ran 5 review groups plus 5 re-verdict steers. e4bebf20 ran 5 groups, and 40 of its 68 loop minutes were the parent triaging and fixing inline between groups.
- Waiting on fix writers took 133 min, 20%.
  - In a58bd85c, two implementers ran for 40 and 53 min. 57 of their 65 tool minutes were `dotnet build`/`dotnet test`, with more than 20 test calls in a row at 1.1–2.7 min each.
  - In 61de7190, one writer took all 63 findings in one lease (233 API calls, a 429, a resume).
- Parent generation with no agent running took 191 min, 29%. In 54dd10c5, 175k of the 194k thinking tokens fell before the first dispatch. The parent diagnosed and fixed the bug itself for 75 min.
- The Opus 5.5 guide says an elapsed-time budget line made small agent teams finish "considerably sooner" with comparable quality ("elapsed 340s / 1200s"). A `PostToolBatch` hook can inject such a line once per batch (`docs/hooks.md:2180–2192`).
- Against a round cap: in e4bebf20, each round caught the previous round's fix. The adversarial pass at parent fixes has 18 confirms.

### 4.2 Changes

1. **Launch the fix-verification review and the refuter together.** In `verify.md`: after a fix round, send the blocker/major re-review and the adversarial pass at the parent's fixes as one parallel batch on the same freeze. Do not run them in series.
2. **A soft round cap, as an explicit partial stop.** Round 1 plus up to 2 more rounds. A 4th round runs only if round 3 found a blocker.
   - **Finding state still defines "done"** (`SKILL.md:106`, must-stay rule 5). The cap does not change that. It adds a second way to end the run: a **partial stop**.
   - A partial stop is not a completion. The Result says "partial" in its first line. Each open finding becomes `Awaiting human` with its evidence, and the Result lists them first. The run line records `outcome=partial`.
   - Example: round 3 finds a major and no blocker. No 4th round runs. The run stops as partial, and the major is `Awaiting human`.
   - Keep "the same signature twice reopens the plan". A reopen resets the round count.
   - Update the Defaults row `Review depth` and the `## Stop rule` together, so they say the same thing.
3. **Fix writers batch their checks.** In `implementer.md`: "Run one build and one filtered test run per group of related fixes, not one per edit. Run the full suite once, at the end." In `dispatch.md`:
   - Fewer than ~5 accepted findings → fix inline.
   - More than ~20 → split across two writers in separate worktrees, with disjoint files and a compose check (`verify.md` `## After the merge`).
   - Otherwise, one writer.
4. **The parent hands off long inline work.** In `decompose.md`: a parent-kept writing row whose work would take more than ~15 min of the parent's own turns becomes an `implementer` row.
   - It becomes a frontier-tier implementer (a new saved agent `implementer-frontier.md`, pinned to `claude-opus-5-5` at `medium`. Do not pass a `model` override to `implementer`: item 1 forbids overrides on saved agents). The parent triages and integrates.
   - Exception: whole-corpus prose edits, where the parent's context is the point. Record the reason in Decisions.
   - Do this together with item 3.2.4, because it also re-enables the blind suite.
5. **An elapsed-time line.** Add an optional `PostToolBatch` hook script, `sage-claude/bin/sage-clock.sh`.
   - It reads the active ledger's `wall target: <n> min` line and the time since the ledger was created.
   - It emits `additionalContext: "sage elapsed <m>m / <target>m"`. When no active ledger exists, it emits nothing.
   - `install.sh` offers it, as it offers the alt guard.
   - The Plan records the wall target, from the same-shape row or from the task class.
   - This is advisory. Nothing stops at the limit.
6. **Keep the lead working.** One line in `execute.md`: "While units run, do the next non-overlapping step: draft the triage, prepare the next brief, run the deterministic checks." (The Fable 5.1 guide: not waiting on each subagent "lowers average time to completion".)

### 4.3 Acceptance criteria

- D1. `verify.md` describes the parallel re-review + refuter batch and the soft cap. The Defaults row matches it. Check that both say the same thing.
- D2. `sage-clock.sh` has a self-test: a fixture ledger with a target produces the line, and no ledger produces nothing. It exits 0 in both cases and never blocks a tool.
- D3. V2 (section 8) shows a lower wall time on the replayed code task, with no known escape missed.

### 4.4 Risk

- **The cap ships a fix that a later round would have refuted.** Mitigation: the refuter runs in every round, in parallel, and the capped items surface as `Awaiting human` instead of being marked done.
- **Parallel writers collide.** Mitigation: disjoint files, worktrees, and the compose check. Note that `isolation: worktree` branches from the default branch, not HEAD, unless `worktree.baseRef: "head"` is set. Set it in the repo's `.claude/settings.json`, or brief the writer to check out the baseline.

---

## 5. Item 5 — Make sage-promote small and scripted

### 5.1 Problem

**F (facts, `04-sage-promote.md`):**
- Seven passes added two shared rules, and one was later archived. Stage two landed one band tag. Eviction and quarantine fired zero times.
- 73 of 95 local KIs have never been used: 43 of 56 lessons, 23 of 23 defects, 4 of 5 gaps, 2 of 9 bands, 1 of 1 contradiction. 49 lessons are at count 1. 34 of the 40 KIs created since 09-01 are unused (parent re-count; the agent's 74 and 42 included two sidecars).
- Use citations: 234 lines touch only 36 distinct KIs. 11 of 12 shared rules already stand in run-loaded text. **E:** of 83 hits that carry a note, 20 show a changed decision (same-shape run rows ×8, cost bands ×6), and 51 re-cite text the skill already says.
- Cost by stage over passes 3–7 ($116, **E**): stage three 41%, stage zero 21%, wrap-up 12%, consolidation 9%. About $28 went to text the gate then refuted.
- Stage three found 3 real lineup events in 7 passes, and all three were cheap to detect. Pass 5 found no change and still spent $7.14 on stage three. The build changes almost daily (2.1.250 → 2.1.284 in 32 days), so the build-based lineup hint fires on almost every run and clears nothing.
- Consolidation is a new throwaway 7–21k-character Python script in every pass. The pass-4 drain nearly lost three pricing rows.
- Correctness defects (details in `04-sage-promote.md`):
  - (a) `SKILL.md:214` cites a removed cell-rule line.
  - (b) the no-dates rule contradicts the stamp in `harness.md:3`.
  - (c) the byte-identical landing rule for `claude-agents*/*.md` misses the `.md.in` alt templates.
  - (d) the one-home grep leaves out the alt agents.
  - (e) the stale notice will print 102 lines on 2026-12-20, 23 of them closed defects.
  - (f) one lesson re-qualifies every pass.
  - (g) the journal has no correction line type.
  - (h) the journal header grammar lacks the five sensor fields.
  - Four open memory items from 9832cdf3: for example, `harness-stamp.md:19` still says "`explorer` haiku".
- The pass may not edit its own `SKILL.md`, so one escalation stayed open from 09-03 to 09-16. Its fixes needed separate `/sage` runs (21c23a0e, part of 9832cdf3).
- The repo's issue tracker is GitHub Issues (`CLAUDE.md`, `docs/agents/issue-tracker.md`).

### 5.2 Target shape

| Part | Today | Target |
|---|---|---|
| Run log | `journal.md` with drain marks and archive segments | `memory/runs.log`: run lines only, append-only, never drained |
| Observations | `obs`/`use` lines in the journal | `memory/inbox.log`: obs lines only; the `use` line is removed |
| Knowledge | 95 local KIs + sidecars, 12 shared KIs, 9 band KIs | `sage-claude/memory/lessons.md` in the repo, synced to the clone, cap ~1,500 words. One bullet per lesson or band: rule, when it applies, falsifier, run ids |
| Defects in the corpus | `defect-*` KIs | GitHub issues, label `sage-corpus` |
| Lineup | Stage three study + a 4,417-word stamp | `bin/sage-lineup-check.sh` prints a diff. A study runs only on a non-empty diff |
| Run Step 2 read | Index (~7k tokens) + matching KIs + newest three run lines | `grep -iE '<task words>' runs.log \| tail -5` + `lessons.md` whole |
| Run Step 6 write | run + use + obs lines | one run line (optional `changed-by: <lesson> <how>`) + obs lines |

### 5.3 Changes

1. **Migrate memory once, with a script.** Write `sage-claude/bin/sage-memory-migrate.sh`:
   - It copies every `run` line from `journal.md` and `archive/journal-*.md` into `runs.log`, sorted by date and deduplicated.
   - It copies the undrained `obs` lines into `inbox.log`.
   - It moves `local/`, `shared/` and `archive/` into `archive/v3/`. It deletes nothing.

   Draft `lessons.md` by hand from the KIs that meet either condition:
   - (a) a shared rule that is not already in run-loaded text;
   - (b) a local lesson or band with a `hit` that changed a decision (use `annotated-hits.txt` as the list).

   Close each defect KI: open an issue if it is still valid, and archive it if it is not. Close each gap KI the same way.

   **Chesterton's Fence:** the v2 → v3 design docs (`docs/designs/2026-08-27-sage-memory-v3-design.md`, `2026-08-28-sage-memory-clone-model.md`) give the reasons for the current structure. Keep two properties they fixed:
   - A run only appends.
   - The repo copy is the source of truth for shared text.
2. **Rewrite `sage-promote/SKILL.md` for the new shape.** Target ≤2,500 words, down from 8,546.
   - Step 1. Run a prep script, `bin/sage-promote-prep.sh`. It prints the inbox, the lineup diff, and the corpus lint.
   - Step 2. For each inbox line, pick exactly one action: merge into `lessons.md`, open an issue, fix the corpus directly, or drop it with a reason.
   - Step 3. One cross-family refuter reviews the combined diff. Its mandate is "claims more than its evidence" plus the one-home grep.
   - Step 4. Run the lineup study only on a non-empty diff. When the study has resolved every line, run `sage-lineup-check.sh --ack`. On an empty diff, run `--ack` to move the cursor.
   - Step 5. Print the diff. The user commits.

   Keep:
   - the refuting gate (it caught about 14 real errors in about 20 dispatches);
   - "gate a status write on its read-back's exit status";
   - "cut second homes before touching a home".

   Allow the pass to edit its own skill text, on the user's word at pass start, through the same gate.
3. **Write `bin/sage-lineup-check.sh`.** It keeps a snapshot in `memory/lineup.json`: the pinned model IDs, the alt models, the price ratio, and a **changelog cursor** (the last build it scanned). It compares the snapshot against:
   - the `model:` frontmatter lines in `claude-agents/*.md`;
   - the alt models in `~/.claude/subagents-alt-models.conf`. That file is `name=value` lines (for example `refuter-alt=api-plan-gpt-6-astra`), not `model:` lines. Parse it the way `install.sh:583–590` does;
   - the model names in changelog entries newer than the cursor, where network access exists.

   **A build change alone is not a difference.** The script prints a line only for a changed pinned model, a changed alt model, a changelog entry that names a model or an alias move, or a changed price ratio. Only such a line starts the lineup study.

   **Scanning is read-only. Only an acknowledgement writes.** Two modes:
   - `sage-lineup-check.sh` (the default) compares and prints. It never writes `lineup.json`. A sage run's hint uses this mode, so a run still only appends to memory. The hint fires on "diff non-empty", not on "build changed".
   - `sage-lineup-check.sh --ack` is for `/sage-promote` only, after the study resolves each printed line. It writes the new snapshot and moves the changelog cursor. When a build-only change has no actionable entry, `--ack` moves the cursor with nothing to review.
   - An interrupted study never calls `--ack`, so its changes stay pending and print again on the next check.

   Replace the stamp KI with `lineup.json`.
4. **Fix defects (a)–(h)** as part of the rewrite, or close them as not applicable to the new shape. Record which.
5. **Move the corpus lint's memory scope with the files.** Today the corpus lint scans only `memory/*.md` and `memory/*/*.md` for `secret-shape` (`sage-lint.sh:1173`), and scans for portability only under `memory/shared/` (`sage-lint.sh:1255`). With the new layout:
   - `inbox.log` and `runs.log` would escape the secret check. The refuter showed that a synthetic token in `inbox.md` fails, and the same token in `inbox.log` passes.
   - `lessons.md` would escape the portability check. A machine path failed in `shared/lesson.md` and passed in `memory/lessons.md`.

   Extend the secret check to `memory/*.log`, and point the portability check at `memory/lessons.md`. Repeat both negative tests on the new layout.
6. **Update the sage run's memory text.** In `sage-claude/references/memory.md`, describe the new Step 2 read and Step 6 append in ≤300 words. Update `install.sh`:
   - Change the memory sentinel to `sage-local-memory v4`.
   - Seed `runs.log`, `inbox.log` and `lessons.md`.
   - Handle a v3 machine by running `sage-memory-migrate.sh` once, with a backup first.

### 5.4 Acceptance criteria

- E1. `sage-memory-migrate.sh` run on a copy of the live memory produces `runs.log` with all 29+ run lines (`journal-run-lines.txt` is the check list) and loses no line. Check with a set difference.
- E2. `install.sh` into a sandbox `HOME`, seeded with a copy of the v3 memory, migrates once and is idempotent on a second run.
- E3. `sage-promote/SKILL.md` ≤2,500 words, and `memory.md` ≤300 words.
- E4. `sage-lineup-check.sh` prints nothing on an unchanged snapshot. It prints nothing when only the build changed and the changelog names no model. It prints one line after you edit a pinned model in a fixture, and one line after you edit one value in a fixture alt conf.
- E4b. A sequence test on fixtures:
  1. A normal-run check sees a changelog-only model announcement and prints it. `lineup.json` is byte-identical afterwards.
  2. A second check (promote prep) still prints it.
  3. A study that stops before `--ack` leaves it pending, and the next check prints it again.
  4. `--ack` clears it, and the next check prints nothing.
- E4a. After the migration, `sage-lint.sh --corpus` flags a secret-shaped string in a fixture `inbox.log`, and a machine path in a fixture `lessons.md`.
- E5. One real `/sage-promote` pass on the new shape finishes in ≤15 min with ≤2 agents when the inbox has fewer than 10 lines. This is a target, measured from `cost-state`.

### 5.5 Risk

- **Lost calibration.** The per-machine counts and bands go away. Mitigations: `runs.log` keeps every actual, the Step 2 grep finds same-shape rows better than "newest three" did (61de7190 was under-priced 3.8× because no same-shape row was in the window), and git keeps the history.
- **Migration damage.** Mitigations: the script only copies and moves. It runs after a backup. E1 checks it.

---

## 6. What was considered and not recommended

- **Move the sage onto the Workflow tool.** The Workflow tool (`agent()`/`parallel()`/`pipeline()`, resumable) is the first-party form of deterministic orchestration.
  - **History (F).** The predecessor skill, `subagents-claude`, had a per-row Workflow backend. It came in with `064208b` (2026-08-05) and changed shape in `2da8b5c` (2026-08-12). `b47d708` (2026-08-16) removed only the plan's approval options, and the backend text was still there after it. The backend left with the whole skill in `d103879` (2026-08-31, "remove subagents skill"). The sage was introduced in `46b9791` (2026-08-18) with no Workflow text at all. **No commit message records why the sage left it out.**
  - **The old text named these costs:**
    - a running script takes no mid-run input, so it loses the steering layer;
    - "a workflow's subagents always run in `acceptEdits`", so a scripted writer row auto-approved its edits;
    - a script's results land only when it returns, so a split can become a barrier.
  - **The current docs contradict the second cost.** `docs/workflows.md:123` says "the agents' tool calls receive the same permission checks and sandboxing as any other tool call in the session". Treat the `acceptEdits` fact as possibly obsolete, and re-verify it before you rely on it in either direction.
  - Workflows run only when the user asks for one, or in ultracode.

  **Recommendation (O):** do not rebuild a general backend in this plan. The steering-layer and barrier costs still apply to sage's triage-as-reports-land flow. If the user opts in later, a narrow trial is reasonable: the item 4 review wave as one `parallel()` of read-only reviewers, where no mid-run steering is needed.
- **Remove the alt lane.** No. It is the only cross-family checker. It refuted 7 of 75 fixes in d6ca31ad that six same-family lenses had passed.
- **Remove adversarial review at the parent's fixes.** No. It is the best-evidenced practice (section 7).
- **A per-row token estimate for the budget.** Removed in item 2. The user's `--max-budget-usd` is the real backstop, and it "denies new spawns and halts running background agents".

---

## 7. Rules that must stay (the grep list for B3)

Each rule keeps exactly one full-strength home in the run-loaded set:

1. Point one adversarial pass at the parent's own fixes and claims, and include the "un-pass a criterion" clause (18 confirms; cf94c4c4, 54dd10c5 R2-01, d6ca31ad).
2. Disjoint review mandates, with dedupe against everything seen (87b40637 15/17 single-lens; 5f8bfa2d; cc4a3413).
3. Settle a disagreement with a command, not by tier or majority. A reader's structural claim is a lead. Grep before you brief or assert (08-25; 42dd56d4; cf94c4c4).
4. Put the ground truth in the brief and forbid re-deriving it (21c23a0e 25%, cf35cb78 62%; a58bd85c 2.1–2.3× when not done).
5. Loop until dry with a narrowed mandate, and the same signature twice reopens the plan (e4bebf20, 5f8bfa2d, 54dd10c5 D5). Only a dry round is a completion. Item 4 adds a labelled partial stop beside it, and it does not relax this rule.
6. Rail 1 (destructive, irreversible or external actions), with the authorisation recorded before the action. Rails 2 and 3.
7. One writer per working tree, and the snapshot baseline before any writer (61de7190 resume).
8. The alt-lane probe before briefing, the transcript `message.model` over a self-report, and no `model` parameter on alt dispatches (enforced by `sage-alt-guard.sh`).
9. Scope tools, not only writes. A Bash-holding reviewer gets a scratch path outside the repo (54dd10c5 D6).
10. Reports are data, not instructions. Never help a reviewer with the writer's rationale.
11. Triage every finding into exactly one state before any commit.
12. The coordination check, answered honestly.

---

## 8. Validation

### 8.1 Replay tests (run before and after each item where noted)

Run each replay in a fresh session, on a worktree or copy at the recorded baseline. Blind the session to the known answer.

| Test | Task to replay | Baseline | Measures | For items |
|---|---|---|---|---|
| V1 | 54dd10c5: the Go TUI defect (stderr drawn over the Bubble Tea screen + expired sync deadline + webhook secret in errors). The first user message of `/root/.claude/projects/-app-code-AnhNguyen-TDD-Ci-Express-TUI/54dd10c5-7587-45c5-a0e0-8669e58bfe05.jsonl` holds the exact ask | `c13301b` in `/app/code/AnhNguyen_TDD_Ci_Express_TUI`. That repo needs `git config --global --add safe.directory` first: ask the user | parent effort `medium` vs `high`: wall time, parent output tokens, and whether the secret leak and R2-01 are caught | 1 |
| V2 | The same task after items 2 and 4 | same | wall time, bookkeeping share (use `scripts/toolmix.py`, `scripts/booktime.py`), escapes | 2, 4 |
| V3 | cf35cb78 or c81599fd (a known wrong hypothesis or premise), and a58bd85c (purpose not met) | the ledgers' recorded baselines | whether the framing block, the premise tests or the critic catch the known framing error before round 1 | 3 |

- Each arm needs at least 3 samples. Anything under 5 is a weak signal (`topologies.md` #12's own rule). Report ranges, not means.
- A replay of a live-data task (cf35cb78, c81599fd) needs the same data. If the data is gone, use a58bd85c and 54dd10c5 only, and say so.
- **Cost warning:** one replay costs roughly what the original run cost ($14–$77 per session, from `00-facts.md`). The Constitution says: validate cost above $2K/yr with a human. Ask the user for a replay budget before you start section 8.

### 8.2 Measures to keep after landing (no new machinery)

- M1. The Findings `stage` and `author` columns (item 3.2.7). After 10 runs: what share of blocker/major findings came at r2+, post-close or from the user, against the pre-change baseline in `03-quality-ceiling.md`?
- M2. The `runs.log` wall time and cost against the table in `00-facts.md`.
- M3. `/doctor prompt-audit` (2.1.283) on `sage-claude/`, `claude-skills/sage-promote/` and `claude-agents/`. Run it before and after item 2, and record what it flags.

---

## 9. Evidence index

| File | What it holds |
|---|---|
| `00-facts.md` | Session paths, per-session duration, API and cost, reasoning share, corpus word counts |
| `01-perf-wall-clock.md`, `01-perf-results.txt`, `scripts/analyze.py` | Wall-clock timeline per session, phases, sinks (`analyze.py --phases` / `--loop` / `--subagents`) |
| `02-obsolete-practices-summary.md`, `02-obsolete-practices-inventory.md`, `scripts/{toolmix,bookcost,booktime,lintout}.py` | ~90 practices with file:line, class, evidence for and against, proposal |
| `03-quality-ceiling.md` | Late-find classes, evidence mix, topology use, ranked quality changes |
| `04-sage-promote.md`, `ki-table.tsv`, `annotated-hits.txt`, `scripts/{stages,stagecost}.py` | Promote yield, KI use, cost by stage, defects (a)–(h) |
| `05-vendor-harness-facts.md` | Harness and model facts with sources, fetched 2026-09-29 |
| `journal-run-lines.txt` | Every journal `run` line, archived and live |

The raw vendor sources (changelog, docs pages, blog posts) were fetched into the session scratchpad and are not copied here. Re-fetch from the URLs in `05-vendor-harness-facts.md`.

---

## 10. How this plan was checked

- Five study agents on `claude-opus-5-5` (xhigh, inherited from the session) wrote the evidence files. The parent re-checked each load-bearing claim with a command: the rail contradiction, the compaction count, the blind-suite precondition, the KI counts, the report-file block, and the `done=` rule on hand-back units.
- A cross-family refuter (`refuter-alt`, transcript `message.model` = `api-plan-gpt-6-astra`) attacked the draft. Round 1 found 10 findings (F1–F10). Six were major: the Workflow history, lint retargeting, the lint memory scope, resume state under the kept hook, the round cap against rule 5, and build-only lineup triggers. All ten were fixed. Round 2 found one new major, F11 (the lineup cursor consumed changes before review, and a run wrote memory). It was fixed in §5.3 change 3 and E4b. F11's fix has not had its own re-check.
- Not checked: none of the proposed scripts exist, so every acceptance criterion is still a future test. The replay tests in section 8 are the only way to measure the quality and wall-time effects.
