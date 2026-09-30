# Sage (Claude) run-loaded corpus — practice inventory and obsolescence audit

Date: 2026-09-29. Scope: `sage-claude/SKILL.md`, `references/{decompose,topologies,dispatch,harness,memory,execute,verify,record,alt-lane}.md`, run blocks of `bin/sage-watch.sh` (1–38) and `bin/sage-lint.sh` (1–26). Run-loaded total by `LC_ALL=C wc -w`: 20,472 plus the two run blocks, 510, which comes to about 20,980. The lint's own count, which skips fenced text, is 19,990 (cc4a3413 ledger).

Classes: KEEP · MODEL-NATIVE · HARNESS-NATIVE · OVER-SPECIFIED · BUREAUCRACY. "Words" means words of run-loaded text the practice costs. "Calls" means parent tool calls per run.

## 0. Measured facts used below (the method is in scratch scripts `toolmix.py`, `lintout.py`, `bookcost.py`, `booktime.py` in this directory)

| Fact | Value | Source |
|---|---|---|
| Parent tool calls that touch only ledger/lint/watch/journal/index/sha/readlink ("bookkeeping-only" turns) | 18–47% of calls, 28–74% of tool-input chars, across 9 sessions | toolmix.py over 54dd10c5, cc4a3413, 9832cdf3, c81599fd, cf35cb78, 21c23a0e, cf94c4c4, b1457e61, 056e20a8 |
| Parent output tokens in bookkeeping-only messages | 16–54% (20k–130k tokens per run) | bookcost.py, same 9 sessions |
| Tool-turn wall time in bookkeeping-only turns | 18–54% (4–16 min per run) | booktime.py, same 9 sessions (idle gaps >30 min excluded) |
| Ledger-lint invocations per run | 5–41 (54dd10c5: 12, cc4a3413: 20, d4096102: 41) | lintout.py |
| What mid-run lint output says | mostly `section 'Run record' is missing`, which is expected until Step 6: 12 of 12 lines in 54dd10c5 and 13 of 19 in cf94c4c4. Substantive catches: a parked triage cell (c81599fd `pending refutation by unit 4`, cf94c4c4 `—`), plan-unit id drift, disclosure-home, findings-shape/triage-orphan (056e20a8, 61de7190) | lintout.py |
| Compactions on 1M-window parents | 0 in 13 of 13 measured sessions. The peak parent occupancy was 257k–589k against a rung of ~921k–927k | compact_boundary count + peak usage per transcript |
| Checkpoint rung fires in production | 0. The only compacting run, a58bd85c (15 boundaries, 200k window), did not host the watchdog. Ledgers say "never fired" (9832cdf3:79, d4096102:65, b1457e61:136, cf35cb78:81) | transcripts, ledgers |
| Older six per-unit watchdog rungs | 0 true positives over 193 transcripts, 37 units (`local/lesson-watchdog-rungs-zero-true-positives.md`) | KI |
| Budget rail 4 fired | 2 times, both unit scope, both 2026-08-18/19 (ledgers 61264f83, 1659a13e). Each time: steer sent, nothing stopped. The whole-task rail never fired, even at 3.8× (61de7190: 3.04M actual against a 3.2M ceiling) | ledger grep |
| Rail 4 crossed silently | 54dd10c5 unit 3a: 281k actual against a 60k estimate, over the 240k ceiling. The ledger does not record this as a rail event, because the watchdog was not hosted and `--status` was read once at close | ledger 54dd10c5:19,45,131 |
| Estimate accuracy (actual/est) | 0.23, 0.25, 0.62, 0.82, 0.92, 0.99, 1.07, 1.13, 1.21, 1.4, 3.8. Wall estimate off by up to 2× (42dd56d4, cf94c4c4, 61de7190) | run-lines.txt |
| Run-line sensor fields | `compact=0` and `saving-post-rung=0` on every run since 09-04 | run-lines.txt 12–29 |
| `/sage report` invocations | 0 of 18 sessions. `/sage resume`: 1, in natural language (61de7190, after an HTTP 429). It used the sha256 baseline, then re-steered the writer | invocation scan |
| Blind acceptance suite choice | 28 `none`, 5 `light`, 1 `none formal` across 42 ledgers. A blind author was dispatched once (ff95b189, 2026-08-18) | ledger grep |
| Blind behavioural lens (#12) | never run as a two-arm lens in 42 ledgers. It appears only as "skipped" or "not run" (21c23a0e D2, d4096102:43) | ledger grep |
| Coordination check | 31 lines. 30 are positive, 1 is "solo" | ledger grep |
| Obs lines about sage's own machinery (alt lane, sensor, corpus, promote, bands, lint, journal) | 81 of 129 | obs-lines.txt |
| Harness tool descriptions on 2.1.284 already say: batch agents in one message; background by default with notification; never fabricate a pending result; SendMessage continues with context; fork inherits context; worktree isolation param | yes (this session's Agent/SendMessage tool text) | live tool schema |
| Calibration tags in run-loaded text | 25 (15 established, 4 recurring, 6 provisional); 14 build-version strings; 18 pointers to `harness-measurements.md` | grep |

## 1. Inventory

### A. Spine and defaults (SKILL.md)

| # | Practice | file:line | What the parent does each run | Cost | Evidence it paid | Evidence it did not | Class | Proposal |
|---|---|---|---|---|---|---|---|---|
| A1 | Four axioms + "delegation is spending" (4×/15× figures) | SKILL.md:20–27 | reads; frames decisions | ~260 w | Coordination check lines show the parent does reason about solo vs fan-out | The figures are external aggregates and "never a conversion rate". Nothing computes with them | OVER-SPECIFIED | keep axioms 2–3 in one line each; drop the 4×/15× sentence |
| A2 | Defaults table (cap 4, rail, report size, fix rounds, review depth, watchdog, checkpoint, word budgets) | SKILL.md:29–43 | reads | 230 w | cap and report size are used | Watchdog/checkpoint rows go with E6. The two word-budget rows are maintainer knobs a run never acts on | OVER-SPECIFIED | keep 4 rows; move word budgets to authoring.md |
| A3 | Step 1–6 summary paragraphs that restate each step file ("nothing here is at full strength") | SKILL.md:45–79 | reads twice (spine, then step file) | ~1,050 w | — | self-declared second homes | OVER-SPECIFIED | cut each to 1–2 lines plus the pointer (Codex sage does the whole flow in ~350 w) |
| A4 | References list | SKILL.md:120–137 | reads | 306 w | — | duplicates the per-step "Read …" pointers | OVER-SPECIFIED | cut to the 3 conditional files (alt-lane, harness-measurements, authoring) |
| A5 | `/sage report` form | SKILL.md:17; record.md:32 | nothing unless invoked | ~80 w | — | never invoked in 18 sessions | BUREAUCRACY (cheap) | keep the form as one line; drop the resolution-order prose |

### B. Decompose and topologies

| # | Practice | file:line | What the parent does | Cost | Evidence for | Evidence against | Class | Proposal |
|---|---|---|---|---|---|---|---|---|
| B1 | Parent owns the state machine; zero agents is valid; every delegation is falsifiable | decompose.md:5–9 | frames plan | ~150 w | 1 "solo" ledger; 54dd10c5 parent kept all writes (coupled) | — | KEEP (compress) | 2 lines |
| B2 | Scouts before study (explorer, ≤2 rounds, actual cost recorded) | decompose.md:11 | decides scouts; records actuals | 142 w | 42dd56d4 6 scouts | 0 scouts in ~20 recent ledgers ("parent read directly") | MODEL-NATIVE | 1 line: "bulk reading goes to an explorer" |
| B3 | Split by independence/context boundary; one writer per tree | decompose.md:13–19 | shapes units | ~230 w | 54dd10c5 D1 correctly kept coupled fixes in one writer | — | KEEP | keep "one writer per tree" and "phases of one deliverable → one agent"; trim the rest |
| B4 | Five safe + four worth tests per unit | decompose.md:21–34 | tests each unit | ~180 w | — | no ledger records the tests being applied row by row | MODEL-NATIVE | 2 lines |
| B5 | Parent-kept code row loads clean-code, with an anecdote and an output-style argument | decompose.md:38; execute.md:9 | Skill call once | 175+45 w | "25 lines of doc comment" anecdote; 54dd10c5 loaded clean-code + concurrency | — | KEEP (compress) | 1 sentence plus "overrides match-the-file comment density"; drop the anecdote and the second home in execute.md |
| B6 | Fleet sizing table | decompose.md:40–47 | reads | ~110 w | band-dispatch-floor hits | — | KEEP | as is |
| B7 | Topologies #1–#9 prose menu | topologies.md:5–58 | reads at Step 1 | 1,044 w | #2 used in most code runs; #6/#9 used | frontier models know fan-out, bake-off, map-reduce | OVER-SPECIFIED | a table of name / when / the one non-obvious rule each (dedupe against everything seen; verifiers never see finder reasoning; per-item pipeline) at ~400 w |
| B8 | #10 Blind acceptance suite: light/full/none decision procedure with 4 signals and precedence | topologies.md:60–67; dispatch.md:21,34,79,173; verify.md:8 | decides every run, records choice + signal + verbatim criteria | 496 + ~200 w | ff95b189: 26 cases, 1 real question | 28/34 "none"; blind author dispatched once (Aug 18) | OVER-SPECIFIED | move to a conditional file read only when a dispatched writer exists; run-loaded keeps 1 line |
| B9 | #11 Pre-write plan critic | topologies.md:69–73 | optional dispatch | 164 w | one critic refuted a central claim before writing (C1, 80k) | declined in several ledgers | KEEP | as is |
| B10 | #12 Blind behavioural lens (two arms, repeat-count rules, pricing) | topologies.md:75–83; verify.md:9 | reads every run; decides "not run" on corpus edits | 719 w | — | never run as two-arm in 42 ledgers; the trigger is only "edits to this ecosystem's own corpus" | OVER-SPECIFIED (wrong home) | move to authoring.md / sage-promote; leave a 1-line pointer |
| B11 | Evidence menus + machine/agent/human criterion tags | topologies.md:85–95 | tags criteria | 193 w | record's MEASURED vs JUDGED split is used in every recent run record | — | KEEP | as is |

### C. Plan, estimate, memory read, model resolution (Step 2)

| # | Practice | file:line | What the parent does | Cost | Evidence for | Evidence against | Class | Proposal |
|---|---|---|---|---|---|---|---|---|
| C1 | Whole plan in the ledger before dispatch | dispatch.md:7,17–27 | writes Plan + unit table | ~250 w; 1–2 calls | legible record; used by this audit | — | KEEP | keep |
| C2 | Per-unit token estimates; "estimate from corpus and lenses" | dispatch.md:11; SKILL.md:53 | estimates every row | ~120 w + hidden reasoning | cf35cb78/c81599fd came within 8–38% | 16× spread (0.23–3.8); nothing but rail 4 consumes it | BUREAUCRACY | drop the per-row Est column; keep "solo alternative" as a qualitative line |
| C3 | Price review + verify as a pair, steer vs fresh pricing | dispatch.md:13 | prices rounds | ~140 w | 9832cdf3 D2: fresh dispatch over steering a corpus-reading thread (a real cost call) | review-and-verify miss lines (promote-pass-4, e4bebf20) | OVER-SPECIFIED | keep one heuristic: "a steer is cheap only while the thread's context is small"; drop the pricing |
| C4 | Price off a same-shape journal row before band arithmetic; read the band KIs | dispatch.md:9; memory.md:17,42–44 | awk the journal, open band KIs | ~120 w; 1–5 calls; band KIs 1,372 w when opened | many "hit" use lines | only feeds C2/rail 4; c81599fd skipped it and landed at 92% | BUREAUCRACY | drop with C2 |
| C5 | Build the measurement harness first / one shared harness | dispatch.md:15 | reproduces the claim before briefing | ~50 w | cf35cb78, e4bebf20, 21c23a0e: the parent gathering ground truth first → 25–62% of estimate | — | KEEP | keep |
| C6 | Calibration strength tags on rules, "weigh when budget forces a choice" | dispatch.md:9 + 25 tags corpus-wide | reads | ~120 w | — | no ledger records a tag deciding anything; they are promote's data, already in sidecars | BUREAUCRACY | strip from run-loaded text |
| C7 | Stamp `SAGE_WINDOW` / `SAGE_COMPACT_AT` into the ledger header | dispatch.md:23 | resolves window, stamps | ~60 w; 1 call | — | only feeds the watchdog (E6); cf35cb78 header even carries `window=unset rung=<n>` | BUREAUCRACY | drop with E6 |
| C8 | Assumption log with a falsifier per row, written when resolved | dispatch.md:25,202–208 | writes 0–7 rows | ~130 w | legibility; user correction written beside a row (1 case in 42 ledgers) | gap KI "unattended vs approved plan" still has no data | KEEP (merge) | merge into one Decisions table (see F4) |
| C9 | Resolve every tier to a named model; Model cell "exact value + tier"; Effort cell "level + control, never a dash" | dispatch.md:20,171; harness.md:62–81 | fills 2 columns per row | ~420 w | — | the tier map is 2 entries (sonnet/opus); agent files already fix model+effort | OVER-SPECIFIED | "explorer/implementer/web-researcher = sonnet; verifier = opus; effort only via agent file; fable parent-only" |
| C10 | `echo $CLAUDE_CODE_SUBAGENT_MODEL` check + availableModels caveat | harness.md:50–60 | 1 Bash call | ~180 w | — | 3 ledger mentions, all "unset" | OVER-SPECIFIED | 1 line |
| C11 | Read memory: index → matching KIs → journal run lines → check two hints | memory.md:40–47; SKILL.md:53 | sage-index (120 lines, ~4k w output) + KI reads | memory.md 1,254 w; 0–20 calls | domain lesson hits: teaching-corpus, grep-symbol, decisive-finding (d6ca31ad, e4bebf20) | 54dd10c5 and c81599fd made 0 index calls with no quality loss; the 12 shared KIs (1,837 w) restate verify/dispatch rules, which the corpus already carries | OVER-SPECIFIED | read the local lesson index only; stop reading shared/ at run time (a second home); drop bands with C2 |
| C12 | Memory boundary table, sentinel, drain-marker explanation | memory.md:9–38 | reads | ~450 w | — | a run needs only "append plain lines" | OVER-SPECIFIED | move to memory-contract.md |
| C13 | The hint (≥25 lines after the mark; lineup stamp older than build) + falsifier paragraph | memory.md:59–70; record.md:69 | counts lines, compares versions | 231 w; 2 calls | the hint fires | promote can compute its own trigger; the falsifier text is maintainer content | BUREAUCRACY | 1 line, or move to sage-promote |
| C14 | Docs-drift trigger, verified-on dates, version stamps | harness.md:3–5 + 14 version strings | compares versions | ~150 w | the harness-stamp miss was caught (b1457e61 use) | it is promote's stage three; a run never re-verifies tables | BUREAUCRACY | move to harness-measurements.md |

### D. Brief (Step 3)

| # | Practice | file:line | What the parent does | Cost | Evidence for | Evidence against | Class | Proposal |
|---|---|---|---|---|---|---|---|---|
| D1 | Zero-context brief naming ground truth + forbid re-deriving | dispatch.md:33 | writes briefs | ~110 w | cf35cb78 62%, 21c23a0e 25%, e4bebf20 140% vs 380%; a58bd85c 2.1–2.3× when re-derivation was allowed | — | KEEP | keep |
| D2 | Grep the claim before briefing/asserting it; `ls` every cited path | dispatch.md:35 | 1–3 calls | ~110 w (core) | a58bd85c "grep-before-you-brief refuted G3"; cf94c4c4 ls loop caught a wrong path | — | KEEP | keep core |
| D3 | GNU grep vs ugrep `[^\t]` trivia | dispatch.md:35 (second half) | reads | ~85 w | one false clearance | machine-local; the `cut -f` advice is enough | OVER-SPECIFIED | move to a lesson KI |
| D4 | A reader's structural claim is a lead | dispatch.md:36 | re-greps before accepting | ~25 w | 8 confirm obs (42dd56d4 26 vs 13; cf94c4c4 path; promote-pass-6 silence) | — | KEEP | keep |
| D5 | Hand off via artifacts, not transcript | dispatch.md:37 | points at files | ~40 w | 42dd56d4 `tail -c` truncation lesson | — | KEEP (compress) | 1 line |
| D6 | Record agentId at return | dispatch.md:38; harness.md:17 | fills a cell | ~90 w | needed for SendMessage to unnamed agents | the harness returns it in the result | OVER-SPECIFIED | 1 line |
| D7 | Scope tools, not only writes; only agent files enforce | dispatch.md:39–40; harness.md:89 | narrows briefs | ~200 w | 54dd10c5 D3/D6: a Bash-holding reviewer wrote into the tree despite a read-only brief | — | KEEP (compress) | one home, ~50 w, plus "give Bash reviewers a scratch path" |
| D8 | Repo PreToolUse hooks gate units; hand seats scratch .txt copies | dispatch.md:41 | reads hook matchers | 139 w | readers lost once to a Read-only hook | repo-specific (ol-foundation KB-cache hook) | OVER-SPECIFIED | move to a lesson KI |
| D9 | maxTurns as the only per-unit rail | dispatch.md:42; harness.md:97,105 | rarely sets it | ~90 w | — | no ledger sets it | OVER-SPECIFIED | fold into one frontmatter line |
| D10 | Tier table by unit property + step-count axis | dispatch.md:44–55; harness.md:77 | chooses tier | ~230 w | 54dd10c5: the sonnet reader on concurrency cost 281k (step count) | — | KEEP (compress) | keep table, drop the step-count essay |
| D11 | Task brief template (13 fields) | dispatch.md:61–79 | fills per dispatch | 349 w | briefs in ledgers follow it | Model/Effort/Per-unit caps fields restate C9/D9 | OVER-SPECIFIED | 8 fields |
| D12 | Agent report + finding schema + severity defs | dispatch.md:81–110 | parses reports | 184 w | triage uses the ids | the verifier agent file already carries the schema and severity verbatim (~/.claude/agents/verifier.md:41–60) | OVER-SPECIFIED (second home) | point at the agent file; keep the triage states |
| D13 | Risk rubric + hard triggers | dispatch.md:112–120 | classifies risk | 144 w | picks topology in every plan | — | KEEP | keep |
| D14 | Nested delegation off | dispatch.md:59; harness.md:48 | — | ~60 w | — | agent files omit Agent | HARNESS-NATIVE (agent file) | 1 line |

### E. Execute and watch (Step 4)

| # | Practice | file:line | What the parent does | Cost | Evidence for | Evidence against | Class | Proposal |
|---|---|---|---|---|---|---|---|---|
| E1 | Launch as one parallel batch; background; never poll or fabricate | execute.md:5,7; harness.md:16,18 | batches | ~150 w | — | the Agent tool description on 2.1.284 says all of this | HARNESS-NATIVE | delete |
| E2 | Dispatch the model the plan named; a change is a D&D row first | execute.md:6 | logs deviations | ~80 w | 54dd10c5 D1 | — | KEEP (compress) | 1 line |
| E3 | Snapshot protocol: baseline hashes, copy untracked, lease, freeze, own tree too, worktree recipe proof, prune worktrees | dispatch.md:122–134; execute.md:8; harness.md:145 | sha256 baseline, freeze | 197+157+60 w; 1–5 calls | /rewind misses subagent and Bash edits (docs); "the logged run that destroyed a working copy was the parent's"; 61de7190 resume used the sha256 baseline | 7 numbered steps restate the verify loop | KEEP (compress) | baseline + freeze + one writer, ~120 w |
| E4 | Failure ladder: specification vs capability signature, rung choice, count signatures not attempts | execute.md:10 | diagnoses failures | 350 w | the "two same-signature failures → reopen" clause paid: 54dd10c5 D5 (webhook leak) and others | rungs named in 2 of 42 ledgers; the reopen clause already lives in SKILL.md:106 | MODEL-NATIVE / OVER-SPECIFIED | 2 sentences: "wrong brief → fresh agent with corrected brief; can't finish → steer then tier up; same signature twice → reopen the plan" |
| E5 | Ledger lint at every bring-current point, read stderr, never disable; history paragraph | execute.md:11–13; SKILL.md:65; sage-lint run block | 5–41 calls/run | 257 + 206 w | catches parked triage (c81599fd, cf94c4c4), orphan ids (056e20a8, 61de7190) | mid-run output is mostly the expected "Run record missing"; the substantive checks are all closure checks | BUREAUCRACY (cadence) | run at Step 6 and before each commit only; ~50 w |
| E6 | Watchdog: readlink dir, confirm session id, probe, host on Monitor 60s, checkpoint rung, degradation rules, stop at close | execute.md:17–33; SKILL.md:40–41,65,77,112–114; record.md:71; sage-watch run block | 3–4 calls + a Monitor task + restamps | 975 + 304 + ~250 w | none in production | 0 fires on 13 1M-window sessions; 0 true positives on 6 older rungs; the compacting run didn't host it; the SessionStart(compact) hook already re-anchors; background reports survive compaction (lesson-background-unit-reports-survive-parent-compaction) | BUREAUCRACY + HARNESS-NATIVE | delete from run-loaded set; keep the script as an optional close-time measurer |
| E7 | Bring-current = lint + `--status` read + copy `model=` as measured + occupancy check + restamp header and Resume state | execute.md:15; dispatch.md:146,200 | 4 acts × each wave/integration | 232 w; 3–20 `--status` calls | 9832cdf3: explorer ran haiku after a mid-session agent-file edit, caught by grep | model swaps occur only on self-edit runs; occupancy never mattered | OVER-SPECIFIED | at integration: update the unit/finding rows. Measure model once, at harvest, for rows that claim family diversity |
| E8 | Unit `compact=` >0 → D&D row + surfaced event | SKILL.md:116; execute.md:15; record.md:62 | checks per unit | ~90 w (3 homes) | — | compact=0 on every unit in every recent ledger | BUREAUCRACY | delete |
| E9 | Budget rail reading: per-row spend vs 4× estimate, projection before each dispatch, both-direction surfacing | execute.md:35–45; SKILL.md:36,88,94–102 | reads spend, projects | 335 + ~200 w | fired twice in Aug; steer-and-continue | whole-task never fired even at 3.8×; silently crossed in 54dd10c5; SKILL.md:92 says a rail ends the turn, which would have stopped 54dd10c5 before round 2 found the R2-01 blocker; execute.md:37 says only "nothing new against that row", so the two texts disagree | BUREAUCRACY; HARNESS-NATIVE (`--max-budget-usd`, `maxTurns`) | keep an agent-count ceiling; replace the token rail with "surface any unit >4× what you expected"; the user's `--max-budget-usd` is the hard stop |
| E10 | "Wall clock is a surfaced event, not a stop" | execute.md:45; SKILL.md:102 | — | ~70 w | — | — | OVER-SPECIFIED | 1 clause |
| E11 | Nothing recalls an agent; SendMessage/TaskStop semantics | execute.md:29–31; harness.md:140 | — | ~180 w | a58bd85c transport failure lesson | — | OVER-SPECIFIED | 1 line |

### F. Ledger shape and record (dispatch.md ledger, record.md)

| # | Practice | file:line | What the parent does | Cost | Evidence for | Evidence against | Class | Proposal |
|---|---|---|---|---|---|---|---|---|
| F1 | One ledger file, durable, gitignore check with 4 exit-code branches | dispatch.md:138; harness.md:148–154 | 1 check-ignore call | 161 w | avoids leaking into the user's tree | a frontier model handles this in one line | OVER-SPECIFIED | "write to .claude/plans/; if git would track it, say so once" |
| F2 | Fixed header comment (occupancy duty, window, rung, last check), restamped each bring-current | dispatch.md:140–146 | rewrite line 1 each point | 87 w + calls | — | the hook text in settings.json already carries the post-compaction instruction | HARNESS-NATIVE (SessionStart hook) + BUREAUCRACY | delete |
| F3 | Plan block (TASK/RISK/TOPOLOGY/PARENT + 8-col table + Cap/Budget/Suite/Scouting/Risks/Solo) + compress rules | dispatch.md:148–175 | writes | 403 w | the record is readable | the Est, Effort(via), Isolation and Budget-basis columns serve C2/C9 | OVER-SPECIFIED | 5 columns: id, unit+done-when, R/W, agent/model, flow |
| F4 | 7 sections (Plan, Unit table, Resume state, Assumption log, D&D, Findings, Open questions) + Run record | dispatch.md:177–238 | maintains 8 sections | ~750 w | Findings + triage is the load-bearing section; D&D rows recorded real reopenings (54dd10c5 D5) | Plan and Unit table duplicate each other (the lint's plan-unit check exists only to keep them in sync); Assumption log, D&D and Open questions are three tables of the same kind | OVER-SPECIFIED | 4 sections: Plan+Units (one table), Decisions (assumptions/deviations/discarded), Findings, Run record |
| F5 | Amend tags on both halves ("2 superseded → D2"), D-ids in order | dispatch.md:218 | tags rows | ~70 w | — | exists to keep the Plan and Unit tables consistent, which the one-table form (F4) removes | BUREAUCRACY | delete with F4 |
| F6 | Unit table `model used` measured/asserted; `messages` cell with sent-at per SendMessage | dispatch.md:183; execute.md:29 | fills cells | ~120 w | the haiku swap (E7) | messages cells are mostly "—" | OVER-SPECIFIED | keep model on alt rows only |
| F7 | Resume state (step, next action, checkpoint, lease, watchdog, baseline + sha256, subagents dir, agentId map), restamped at every point | dispatch.md:185–200; SKILL.md:108–118 | restamps | 123 + 216 w | 61de7190 resume used it | 1 resume in 18 sessions; 0 compactions on 1M runs | OVER-SPECIFIED | write it when a writer launches and at close, not at every point; drop the checkpoint/watchdog lines |
| F8 | Residual same-family bias disclosure has its only home in Findings (lint-checked) | dispatch.md:228; verify.md:13 | writes disclosure | ~50 w | honest disclosure | the lint's disclosure-home check fired on 5 ledgers for placement only | OVER-SPECIFIED | keep the disclosure; drop the placement rule |
| F9 | Run record: 13 fields incl. Agents, Deviations, Assumptions, Memory check, Lessons mirrored verbatim | record.md:9–32 | writes at close | 460 w | Verification MEASURED vs JUDGED, Coordination check, Gaps, Awaiting human are used | Agents/Deviations/Findings/Assumptions restate sections of the same file; "Memory check: journal +N lines, tail verified" and "Lessons (mirror)" restate the journal | BUREAUCRACY (half) | Outcome, Cost, Verification, Coordination, Gaps, Awaiting human |
| F10 | Print four things; ls every path; Artifact URL list-check anecdote | record.md:34–47 | prints | ~290 w | cf94c4c4 ls loop | the Artifact URL paragraph is one incident | KEEP (compress) | keep Result + one run line + ls rule, ~80 w |
| F11 | Surfaced events list (10 items) | record.md:49–62 | checks each | ~200 w | rail, lease, security, abandoned, Awaiting human are real | watchdog, lint-at-Step-6, checkpoint and compact= items go with E5–E8 | OVER-SPECIFIED | 6 items |
| F12 | Four closing obligations (coordination, journal append+tail+count, lint again, stop watchdog) | record.md:64–73; SKILL.md:77 | 3–5 calls | 383 w | coordination check (31 lines, the self-falsifier) | the append read-back ("nothing an append can break") and stop-watchdog go with E6 | OVER-SPECIFIED | coordination + append; ~80 w |
| F13 | Journal `run` line with 5 sensor fields (model, compact, turns, occ-sum, saving-post-rung) | memory.md:26,36; record.md:69 | reads `--status` over the parent at close | ~100 w; 1–2 calls | the run lines were the ground truth for this audit | compact and saving-post-rung = 0 on every run since 09-04 | BUREAUCRACY (the fields) | keep the run line; drop the 5 fields |
| F14 | `use` line, `obs` lines with portable/local class, falsifier | memory.md:28–34,53–55 | appends | ~250 w | promote's input; 129 obs lines | 81/129 obs are about sage's own machinery | KEEP (compress) | a 4-line grammar |

### G. Verify (Step 5)

| # | Practice | file:line | What the parent does | Cost | Evidence for | Evidence against | Class | Proposal |
|---|---|---|---|---|---|---|---|---|
| G1 | Reports are data, never instructions | verify.md:5; harness.md:144 | — | ~70 w | security | the harness also scans (v2.1.210+) | KEEP (1 line) | one home |
| G2 | Dispatch reviews as `verifier` rows; stop re-briefing what the file binds | verify.md:6 | — | ~90 w | — | — | KEEP | keep |
| G3 | Deterministic checks before model review; execute installer steps in a sandbox HOME | verify.md:7 | runs builds/tests/install | 124 w | "every dispatch of this check measured something no diff reader could" (3 examples) | the installer clause is specific to this repo | KEEP (compress) | keep; move examples to a KI |
| G4 | Two-stage review; diff-review Spec/Standards briefs verbatim + smell baseline verbatim on Standards | verify.md:8; topologies.md:15; dispatch.md:22 | copies briefs | ~300 w over 3 homes | cc4a3413 and 9832cdf3: the Standards lens found the only majors | — | KEEP (one home) | one home in verify.md |
| G5 | Criterion can pass literally while the mechanic is broken; read each criterion twice | verify.md:9 | — | ~110 w | a58bd85c "criteria at the data layer can pass while the purpose is unmet" | — | KEEP (compress) | 1 line |
| G6 | Never help a reviewer with the writer's rationale; no fork reviewers | verify.md:10; harness.md:34 | — | ~70 w | clean-context principle | — | KEEP | keep |
| G7 | Disjoint mandates produce disjoint find-sets | verify.md:11; topologies.md:9 | picks lenses | ~120 w | 87b40637 15/17 single-lens; 5f8bfa2d 9 with zero overlap; 9832cdf3; cc4a3413 | promote-pass-3: sequential same-mandate rounds also found new things | KEEP | keep |
| G8 | Reviewers report what they are asked to look for; scope to correctness | verify.md:12 | — | ~50 w | — | — | MODEL-NATIVE (cheap) | keep 1 line |
| G9 | Cross-family checker; never the maker's model | verify.md:13 | picks checker seat | ~150 w | d6ca31ad: verifier-alt refuted 7/75 fixes that six same-family lenses had passed | the effect is not separated from "fresh adversarial pass" | KEEP | keep, compress |
| G10 | Point one adversarial pass at your own fixes and claims; un-passing clause | verify.md:14–16 | plans a refuter row | ~200 w | 18 confirm obs; cf94c4c4 10/10 problems parent-authored; b1457e61; 54dd10c5 R2-01; d6ca31ad XR-1 | — | KEEP | keep |
| G11 | Triage into exactly one state; two kinds of agreement | verify.md:17 | triages | ~120 w | the lint caught parked cells | — | KEEP | keep |
| G12 | Settle disagreement with a command | verify.md:18 | runs the measurement | ~100 w | 08-25 git grep inverted a security finding; a58bd85c; promote passes | — | KEEP | keep |
| G13 | Range target: never report a mean | verify.md:19 | — | ~100 w | 1 logged run (4 errors) | domain-specific; already a shared KI (second home) | OVER-SPECIFIED | KI only |
| G14 | Loop until dry: re-freeze, narrowed blocker/major mandate, un-pass question, dedupe against all seen, reopen after same signature twice | verify.md:20,27–29; topologies.md:29–34 | runs rounds | ~500 w over 3 homes | e4bebf20 4 rounds each caught the prior fix; 5f8bfa2d 6/9 findings in the parent's fixes; 54dd10c5 round 2 blocker | — | KEEP (one home) | ~200 w in verify.md |
| G15 | Commit triage gate = lint + read the triage column; read the lint header scopes first | verify.md:21–25 | lint + read | 203 w | c81599fd parked "pending" caught | "read all three checks' scopes in the script header first" costs a header read | OVER-SPECIFIED | "before any commit, every finding has one of the 4 states (lint checks it)" |
| G16 | Compose check after merging parallel work | verify.md:31–33 | runs the suite | ~30 w | — | — | KEEP | keep |

### H. Alt lane (conditional file, ~996 w, read on every run of this machine because alt agents are listed)

| # | Practice | file:line | What the parent does | Cost | Evidence for | Evidence against | Class | Proposal |
|---|---|---|---|---|---|---|---|---|
| H1 | Availability is the live agent list, not the filesystem | alt-lane.md:7 | — | ~80 w | 9832cdf3/cc4a3413 mid-session model edits | — | KEEP (1 line) | |
| H2 | Probe each alt role with a one-line brief before use | alt-lane.md:9 | 1–2 small dispatches | ~140 w; 3–5k tokens each | 404s on 4 consecutive runs (bc00ef0a, d4096102, promote-pass-4) cost one line instead of a full brief | the lane has been live since 09-07 | KEEP | keep |
| H3 | Alt dispatch passes no `model` parameter | alt-lane.md:11 | — | ~110 w | a ledger D5: parent passed `model: haiku` to U1–U3, destroying the lane | `sage-alt-guard.sh` (PreToolUse) now blocks it | HARNESS-NATIVE (own hook) | 1 line + "the guard enforces it" |
| H4 | Per-role benefit (refuter-alt vs verifier-alt split) | alt-lane.md:13 | picks seat | ~130 w | — | — | KEEP (compress) | |
| H5 | Fill Model cell via grep of agent file | alt-lane.md:15–21 | 1 grep | ~110 w | — | goes with C9 | OVER-SPECIFIED | delete |
| H6 | Settle family by transcript `message.model` over self-report | alt-lane.md:23–29 | 1 grep per alt checker | 195 w | self-report named the wrong vendor (promote-pass-6, promote-pass-5); "unknown" on gpt-6-astra (21c23a0e) | — | KEEP (compress) | 1 grep command + 1 sentence |
| H7 | Take alt spend from the transcript, not `subagent_tokens`; false-zero trap | alt-lane.md:31 | `--status` per alt row | 168 w | notification counter wrong in both directions | only matters for C2/E9 accounting | BUREAUCRACY (with C2) | move to harness-measurements.md |

### I. Harness mechanics (harness.md)

| # | Practice | file:line | What the parent does | Cost | Evidence for | Evidence against | Class | Proposal |
|---|---|---|---|---|---|---|---|---|
| I1 | Built-in types, agents dir discovery, global description rule | harness.md:19,32 | — | ~120 w | — | install-time facts, not run-time | OVER-SPECIFIED | move to authoring.md |
| I2 | Role table (4 roles, tools, scope) | harness.md:22–29 | reads | ~180 w | picks roles | agent descriptions are in the live agent list | KEEP (compress) | keep table |
| I3 | Tools column is an upper bound; verifier has no Glob/Grep | harness.md:30–31 | — | ~110 w | measured | — | OVER-SPECIFIED | 1 line |
| I4 | Boot cost, output_file skill grep | harness.md:33,35 | — | ~100 w | a-scoped-agent-boots-3x-cheaper | — | OVER-SPECIFIED | 1 line |
| I5 | Limits and knobs (concurrency 20, depth 3, removed spawn cap, --max-budget-usd) | harness.md:39–48 | — | 151 w | — | version trivia; the cap default lives in SKILL.md | OVER-SPECIFIED | move to measurements |
| I6 | Frontmatter beyond tools table | harness.md:91–105 | — | 253 w | — | authoring content | OVER-SPECIFIED | move to authoring.md |
| I7 | Transcripts + token arithmetic (layout, dedup, spend vs occupancy formulas, signals, sampling cadence, window) | harness.md:107–140 | — | 642 w | implements E6 | "the script implements this section and the two must agree", a designed second home | BUREAUCRACY (in run set) | move to the sage-watch manual |
| I8 | Compaction caution, install/memory sync | harness.md:147,155–156 | — | ~170 w | — | install-time | OVER-SPECIFIED | 1 line |
| I9 | Agent Teams env-var note | harness.md:37; topologies.md:52 | — | ~50 w | — | never usable mid-run | OVER-SPECIFIED | delete |
| I10 | Workflow tool (deterministic agent()/parallel()/pipeline(), resumable by run id) | not mentioned | — | — | — | could hold the unit-state machine and resume for fixed topologies (#2, #1) instead of the ledger's Unit table and Resume state | HARNESS-NATIVE (unused) | trial, unmeasured |

### J. Rails and stop

| # | Practice | file:line | What the parent does | Cost | Evidence for | Evidence against | Class | Proposal |
|---|---|---|---|---|---|---|---|---|
| J1 | Rail 1 irreversible/external actions; the authorisation is a D&D row | SKILL.md:85,90 | stops, asks | ~80 w | 54dd10c5 D7–D9 recorded three user-authorised pushes and deletes | — | KEEP | keep (Constitution non-negotiable) |
| J2 | Rails 2–3 writers without isolation / outside lease | SKILL.md:86–87,90 | — | ~60 w | lease widened in 3b4f59aa | — | KEEP | keep |
| J3 | Rail 4 budget (table + floors) | SKILL.md:88,94–102 | see E9 | ~120 w | see E9 | see E9 | BUREAUCRACY | agent-count ceiling only |
| J4 | Stop rule | SKILL.md:104–106 | checks at close | ~120 w | 54dd10c5 D5 reopen | — | KEEP | keep |

## 2. Rough word arithmetic for the proposed cuts (estimates; overlaps removed by hand)

| Cut | Words out of run-loaded set |
|---|---|
| E6+E7+E8+F2+C7+I7 watchdog/occupancy/sensor text | ~2,300 |
| E9+J3+C2+C3+C4+H7 estimation and token rail | ~1,050 |
| B10+B8 #12 and #10 out to conditional homes | ~1,150 |
| F3–F13 ledger and run-record slim-down | ~1,000 |
| C11–C14+F13-F14 memory protocol | ~900 |
| E1+I1+I3–I6+I8–I9 harness-native and install trivia | ~850 |
| C9+C10+H5+D9+D11 model/effort ritual | ~650 |
| C6+D3+D8+F10 anecdote+G13 tags, trivia, anecdotes | ~550 |
| A3+A4+G4/G14 second homes | ~900 |
| E4 failure ladder | ~280 |
| E5+G15 lint cadence text | ~350 |
| **Total** | **~9,900 (about 48%)**. The run-loaded set would fall from ~20.5k to ~10.5k words |
