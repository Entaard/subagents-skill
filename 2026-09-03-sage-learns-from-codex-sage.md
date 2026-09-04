# Proposal: what sage-claude should take from Codex Sage

Date: 2026-09-03, revised 2026-09-04. Subject: `2026-08-31-sage-codex-proposal.md`, the `sage/` directory (Sage for Codex, Phase 0 and Phase 1), and the six root-level documents that describe and measure it. Target: `sage-claude/` in this repository.

The 2026-09-04 revision answers four questions the first draft did not ask. Can the self-improvement loop be simpler? Why is Codex Sage's text so much smaller, and what does that teach? Would JSON serve better than Markdown? Does the successor-orchestrator handover still earn its place? Part B holds those answers. Part A holds the first draft's items, re-ordered by the priority table below.

## Verdict in one paragraph

Codex Sage is a real implementation, not a paper design. Its Python library and its 44 tests run and pass on this machine once one portability defect is patched. Most of its policy is a port of sage-claude and brings nothing back. Its two large new mechanisms, the JSON run record with a Markdown projection and the receipt-bound installer, solve problems sage-claude has already solved another way, at a cost that no measurement justifies. What Codex Sage does show is shape: a router `SKILL.md` of 804 words, policy files with no dates and no anecdotes, and a memory boundary stated as one three-row table. The 2026-09-04 measurements add three facts. A sage-claude run loads 41,737 words against Codex Sage's 9,716. At least sixteen sage-claude rules stand in two or more homes. The successor handover fired twelve times, spawned a successor five times, did substantive work in four of those, and since 2026-08-27 has fired only at the end of a run. So the three highest-priority items are structural. B1 makes `SKILL.md` a router and cuts the run's reading load. B2 retires the sensor-triggered successor as an experiment with a measured gate. B3 states the memory boundary in one table and deletes two pieces of promote machinery the record has made dead. B4 rejects JSON for guidance. Eleven smaller items from the first draft follow, each a bounded change to a template, a script or one rule. One of them (A4) is absorbed into B2.

## Priority order

The rank follows two rules. First, the size of the effect on every run. Second, the strength of the evidence behind the item. Part B items come first because they change what every run loads and does. Part A items keep their first-draft ids so that cross-references inside them stay valid.

| Rank | Item | Why it sits here |
| --- | --- | --- |
| 1 | B1. Router `SKILL.md` and the reading-load cut | Touches every run and every reader. Measured: 41,737 run-loaded words, at least 16 duplicate homes, 3,088 words of `memory.md` a run never uses. The user's stated preference. |
| 2 | B2. Retire the successor handover, as an experiment | The largest single removal: about 3,500 words, an agent file, a recorded failure class. The problem half is measured: 7 of 12 firings were misfires, 6 of 6 since 2026-08-27. The solution half has no local observation yet, so B2 carries a gate and a reopen condition. It sits above B3 on effect size, not on evidence. |
| 3 | B3. Memory boundary in one table; delete dead promote machinery | Answers the first question. The design already holds; the text does not say so. Two steps are proven by one command that prints nothing. |
| 4 | A2. Measure the effective model from the transcript | Established evidence; a script change only. |
| 5 | A5. Secret-shape lint | Script only. The leak path into a user's git history is measured, and the consequence class is credentials. |
| 6 | A8. Two lint cell checks | Script only; the check shape already exists. |
| 7 | A1. Evidence class per criterion | Template plus lint; the run record already wants the distinction. |
| 8 | Two small adaptations: spend provenance word, host-leak corpus lint | One word and one grep each. |
| 9 | A3. Coordination state word | Argued, unmeasured. |
| 10 | A7. Novelty disposition at minting | A promote edit; cheap. |
| 11 | A6. Promotion bar split by evidence class | A promote edit; changes a threshold. |
| 12 | A9. Enforced-versus-advisory table | Folded into B1's harness run sheet. |
| 13 | A10. Missed recogniser clause | Argued, unmeasured. |
| 14 | B4. JSON for guidance | Rejected; no change. |
| 15 | A4. Handover response arithmetic | Absorbed into B2 step 3; its 30% rung does not survive. |
| 16 | A11. Pre-registered paired evaluation | Unscheduled by design. |

## How this study was done, and what it found about the corpus

Six read-only scouts enumerated the corpus on 2026-09-03 into one line per mechanism with a file:line pointer. The parent ran Codex Sage's own checks and read the primary files that each verdict below depends on.

On 2026-09-04 four more scouts ran, each on the cheapest model that could do its job. A handover-evidence scout read all 5 handoff notes, all 22 ledgers under `.claude/plans/`, the installed memory archive and six lesson KIs. It built one row per rung firing. A duplication scout measured `sage-claude/SKILL.md` section by section and listed every rule with two or more homes. A router scout mapped how Codex Sage's `SKILL.md` points at its references and how its bundle stays in sync. A web scout fetched primary sources on auto-compaction, the 1M window, the "20 to 30%" heuristic and cache-read pricing. The parent itself read `SKILL.md`, `references/memory.md`, `references/dispatch.md`, `references/harness.md` and `claude-skills/sage-promote/SKILL.md`, and re-ran every count quoted below. Two reviewers then checked the new text: one for logic, one for every pointer and figure. The scout reports live in this session's scratchpad and die with it. Every figure this document relies on is quoted here with the command or the file:line that reproduces it.

Three facts about the corpus shape every verdict that follows.

**The code works, and one line stops it from running here.** `python3 sage/scripts/check-phase0.py --self-test` passes. `python3 sage/scripts/check-phase1.py` fails as shipped: 40 of 44 tests raise `FileNotFoundError` because `sage/tests/test_phase1.py` hardcodes `dir="/private/tmp"`, a macOS-only path, in 40 places (first at line 141; the traceback shows line 382). With that string replaced by `/tmp` in a scratch clone, all 44 tests pass in 38 seconds and the Phase 1 gate reports "implementation and frozen-gate checks passed". The repository also commits `cpython-311` bytecode from the author's machine. The README's instruction to run the complete Phase 1 matrix is therefore true only on the author's platform. This is not a reason to distrust the design. It is a reason to treat every "tested" claim as tested on one machine.

**No Codex Sage design has outcome evidence.** The Phase 1 paired pilot that was meant to show the policy's value never started (`sage/README.md`, "Phase 1 pilot gate"; `sage/evaluation/phase-1/STATUS.md`). The Managed mode, the runtime protocol, the capability negotiation and the resource coordinator exist as schemas and prose only. `sage/knowledge/index.json` holds zero promoted records, so the promotion workflow has never landed a real record. Every adoption below therefore has to justify itself on sage-claude's own measurements. Where it cannot, it is rejected, however clean the Codex design reads.

**The effort that produced it was expensive.** `codex-massive-usage.md` lines 84 to 90 attribute 105.3M tokens to the proposal session group, 86.5M to the Phase 1 implementation, 98.1M to the later `$sage` instruction work, and 37.5M to the implementation review. The usage investigation (`codex-vs-claude-sage-usage-investigation.md`) traces the spend to a root model on maximum reasoning, thousands of tool cycles, repeated compaction and fan-out. None of that spend bought a single measured run of the skill itself. A design that consumed this much before its first evaluation is not evidence of value. It is evidence of scope.

## Part B. The four questions of 2026-09-04

Each item states the current design first, then the evidence, then the change. Word counts are `wc -w` on the committed files at `c442ee8`.

### B1. Make `SKILL.md` a router, and cut what a run has to read

**What "15 times less" measures.** Codex Sage's `SKILL.md` is 804 words. sage-claude's is 12,526. That is the ×15 (15.6×), and it compares one file with one file. A run does not load one file. sage-claude's `SKILL.md` tells a run to read four reference files and two script headers. The sum is 41,737 words: `SKILL.md` 12,526; `references/topologies.md` 2,647; `references/harness.md` 8,542; `references/dispatch.md` 4,247; `references/memory.md` 4,185; the `bin/sage-watch.sh` header 2,259; the `bin/sage-lint.sh` header about 7,300. Codex Sage's `SKILL.md` names eight policy files plus `codex.md` and `guarantees.md`. That sum is 9,716 words. The honest ratio is 4.3×, not 15×. The two promote skills compare at 8,357 words against 2,474, or 3.4×. Codex Sage also has no script headers to read, because its scripts are a Python library behind a CLI. Part of its text moved into code. That part is R1 and R5, and this proposal does not bring it back as prose.

**Where the 32,000 words come from.** Four sources, each measured this session.

1. **Duplicate homes.** At least sixteen rules stand at full strength in two or more places. The list from this study holds sixteen; `/sage-promote`'s own corpus scan found 28, eleven of them involving `bin/` (`claude-skills/sage-promote/SKILL.md:216`), so sixteen is a lower bound. The alt-lane rule "no `model` parameter" appears four times in `SKILL.md` alone (`SKILL.md:132`, `:153`, `:201`, `:353`), twice in `references/harness.md` (`:141`, `:197`) and once in `references/dispatch.md:20`. The guard script's own header says "`../SKILL.md` states the rule three times" (`bin/sage-alt-guard.sh:21`). The duty to bring the ledger current appears on eight lines of `SKILL.md` when the "bring-current point" phrasing is counted (`grep -n -i 'bring-current\|ledger current' sage-claude/SKILL.md`). The parent-kept writer's `clean-code` load rule is a near-identical paragraph twice in the same file (`SKILL.md:77` and `:165`). `SKILL.md:173` says of the watchdog header "read it there; nothing below restates it". `SKILL.md:175` then restates the whole directory-resolution procedure, anecdote included. The 30% threshold has six homes. The `git check-ignore` four-branch rule has three. Two rules are single-homed and show the pattern to copy: "grep the claim before you brief it" (`SKILL.md:129`) and the `superseded → D<n>` tag (`references/dispatch.md:162`).
2. **Text a run never uses.** `references/memory.md` is 4,185 words. 3,088 of them serve `/sage-promote` or a maintainer: the shape, the KI field contract, the structural invariants, the compression floor, the promotion section. About 1,100 serve a run, and 207 of those are the file's introduction and contents line. `references/harness.md` carries about 1,050 words of dated derivation that no run decision reads: the dedup percentiles, the sampling cost, the Mythos study, the occupancy arithmetic. The `bin/sage-lint.sh` header a run is told to read at Step 4 is about 7,300 words. Its `CORPUS MODE` section, about 2,050 words, documents a mode a run never invokes.
3. **Anecdote and rationale.** Steps 3, 4 and 5 hold 5,963 words, 48% of `SKILL.md`. The scout's read puts about 30% of those words in anecdote and measurement and 20 to 25% in rationale. Codex Sage's policy files carry zero dates, zero "one run" anecdotes and zero calibration tags. The word `measured` appears three times, each as a classification word. sage-claude's compression floor (`references/memory.md`, `## The compression floor`) protects the recognising anecdote on purpose, so this share cannot reach zero. It can go down. `/sage-promote`'s stage two already names the compressible form: "the third subordinate tail", the clause after the rule and after its one justification (`claude-skills/sage-promote/SKILL.md:216`). It also names two cuts that do not work. Cutting anecdotes fails because half of them are recognisers. Converting prose to tables measured at −11%.
4. **The handover apparatus.** About 3,500 words: `SKILL.md` `## Handover` (1,623), the handoff-note template (455), the harness paragraph on occupancy (382) and the `orchestrator` agent file (1,072). B2 owns that.

**What the router shape buys, honestly.** Moving a paragraph from `SKILL.md` into a reference file saves nothing by itself. A reference the run reads lands in the same window. Three things do pay. First, a run reads a step's file at that step. Step 5 and Step 6 text is then absent from the window during Steps 1 to 4, and a run that stops on a rail never loads it. Second, the one-home rule becomes mechanical. A router `SKILL.md` carries no rule at full strength, so every rule has exactly one file to live in, and the duplicates above have nowhere to grow back. Third, a person can read the spine in two minutes, and a person is the reader the user named. The saving comes from the cuts the router makes possible, not from the move. Codex Sage keeps its generated copies in sync with a hashed manifest (`sage/scripts/generate-skill-bundle.py --check`). sage-claude already has the equivalent in `/sage-promote`'s `diff -rq` between repo and installed tree, so nothing new is needed there.

**Verdict: adopt.** The design:

1. `SKILL.md` becomes a router of at most 2,500 words. Its contents, each with a word budget:
   - frontmatter, the job sentence and the three invocation forms: 200
   - the four axioms: 150
   - the Defaults table: 280
   - the six steps, at most 150 words each, each ending with the file to read at that step: 900
   - the Rails table with its NEVER clause: 250 (the rest of today's 645 moves to `references/execute.md`)
   - the stop rule, one paragraph: 100
   - B2's `## Compaction and resume`: 200
   - the references list, one line per file: 150

   That sums to 2,230. The Defaults table stays here because it is the one block the user edits. `## Compaction and resume` stays here because the compaction hook says "re-read `SKILL.md`", and a compaction can land during any step.
2. Step bodies move to one file per step, mirroring Codex Sage's eight policy files:
   - `references/decompose.md`: Step 1. It also becomes the home of the one-writer-per-tree rule, because Step 1 decides it.
   - `references/dispatch.md`: Steps 2 and 3, which it already half-owns.
   - `references/execute.md`: Step 4, the failure ladder, the watchdog hosting, the lint cadence.
   - `references/verify.md`: Step 5.
   - `references/record.md`: Step 6, the ledger shapes and the run record.

   `topologies.md` and `authoring.md` stay as they are.
3. `references/harness.md` splits in two. The run sheet keeps the tier table, spawn mechanics, the window, the alt-lane rules and A9's enforced-versus-advisory table, about 3,000 words. `references/harness-measurements.md` takes every dated figure, percentile and derivation. `/sage-promote` stage three and a maintainer read it; a run never does. The run sheet cites the measurements file wherever a figure has a date.
4. `references/memory.md` keeps the run's duties only: the boundary table B3 adds, read at Step 2, append at Step 6, the hint, the journal grammar. About 900 words. The KI field contract, the structural invariants and the compression floor move to `claude-skills/sage-promote/references/memory-contract.md`, because that skill is their only reader.
5. Each script header gains a run block of at most 300 words at the top, closed by a marker line. The step file tells the run to read up to the marker: `sed -n '1,/^# END RUN BLOCK/p' bin/sage-lint.sh`. The rest of the header stays for maintainers, unchanged.
6. The cut inside each step file has two passes. First, remove every duplicate the report lists: the owning file keeps the rule, and every other mention becomes a pointer or nothing. Second, apply stage two's third-subordinate-tail rule paragraph by paragraph, and keep every floor item. The `--corpus` lint's word-budget row in the Defaults table becomes two rows: `SKILL.md` at most 2,500 words, and the run-loaded total at most 20,000. The run-loaded total counts the files the router names plus the script run blocks. Both figures are targets. The second one is what measures the design.
7. Verification, per file. `references/topologies.md` #12's stop arm runs on the pre-cut corpus for any paragraph whose removal the author doubts. `/sage-promote`'s one-home grep runs over the whole corpus after the batch. `bin/sage-lint.sh --corpus` runs last. Land it as a `/sage` run on the user's word. Each step file is one writer unit under a write lease. A `verifier` per file gets the brief "name a run decision the old text settled and the new text does not".

**The arithmetic behind the 20,000 target, labelled an estimate.** The router (2,500), `topologies.md` (2,647), the harness run sheet (3,000), the run-facing `memory.md` (900) and two 300-word run blocks sum to 9,647. That leaves about 10,350 words for the five step files. Today the step bodies hold about 8,750 words and `dispatch.md` 4,247, about 13,000 together. So the step files need a cut of about 20% after deduplication. Falsifier: three runs after the cut record a `miss` or a deviation that the removed text would have prevented, or the run-loaded total lands above 25,000 because the step files grew back.

### B2. Retire the successor handover as an experiment; let the ledger and a configured compaction carry the run

**The two reasons for the 30% rung, re-examined.** The rung rests on two beliefs. The first is that a model's useful context is 20 to 30% of its window. On 2026-09-04 the web scout searched Anthropic's context-engineering post, the Claude Code docs, Chroma's Context Rot report, Lost in the Middle, NoLiMa and RULER. None states a 20 to 30% figure for any Claude model, and Anthropic publishes no numeric effective fraction. Those sources show that quality drops as *irrelevant* content grows. The remedy they name is a small set of high-signal tokens. Sage already does that with capped reports, artifact hand-off and scouts. Restarting the actor at 30% adds nothing to it. The second belief is that auto-compaction would lose the run. It has never fired here. Every compaction on this machine is `trigger:"manual"`, and 466,802 tokens of occupancy passed without one (`references/harness.md:248`). The state the rung protects has been durable in the ledger since the ledger header landed.

**What the record shows the successor did.** Twelve rungs fired on this machine between 2026-08-18 and 2026-09-03. Five spawned a successor: `0042d31e`, `61264f83`, `cfff08b5`, `683518a1`, and a `/teach` corpus run on 2026-08-26. Seven finished in place as a logged deviation, and every firing since 2026-08-27 was one of those seven (`lesson-occ-30pct-fires-with-nothing-to-launch`, count 8). The successors did substantive work in four of the five. One carried 1,346.9k of a run's spend through generation 2 (`~/.claude/skills/sage/memory/archive/local-v2.md:145`). One implemented 27 fix items across a five-file lease (`.claude/plans/sage-ledger-683518a1-fix.md:31`). The fifth, `cfff08b5`, ran only the Step 6 close, for about 65 to 70k tokens by its own report. That is the honest half: the mechanism carried the long runs of the first nine days.

**Why the later runs stayed small is not settled.** The runs since 2026-08-27 close between 14% and 33% (journal `run` lines, `a58bd85c` at 14.1% to `d20b9a1f` at 33%), and the rung fires only at Step 6. This is consistent with the briefing and report-size rules that landed in that period. It is also consistent with smaller tasks. No run since 2026-08-27 is as large as the smallest run that spawned a successor. The 2026-08-26 run spent 4,103.3k in total, 2,044.9k of it on the parent side over three generations (`~/.claude/skills/sage/memory/archive/local-v2.md:145`). `0042d31e` was projected at 740k to 770k. The later runs' fleets spent 61k to 560k (journal `run` lines). So the record cannot say whether a 16-unit run under today's rules would still cross 30% with work left. That is the strongest argument a defender of the successor can make, and it is why B2 is an experiment with a gate rather than a conclusion.

**What it costs.** In the corpus: about 2,460 words in every run's window, a 1,072-word agent file in the successor's window, and the `Generation` and `role` header fields with their lint check. Also the `SAGE_OCC_ACK` re-host, a steering relay because the successor has no `SendMessage`, and a one-writer split between ledger and note. And a chaining invariant that holds "in prose only" (`SKILL.md:326`). In the record: the parent's spot-check found reporting drift on every successor report (`SKILL.md:317`, calibration established). One successor widened its own write lease without returning the rail-3 event (`.claude/plans/sage-handoff-61264f83-e776-4c65-b248-185c2ea2d83b-20260818-180447.md:149`). One returned below its threshold with two checker units still in flight for the parent to harvest (`.claude/plans/sage-ledger-683518a1-fix.md:67`). Successors priced by occupancy understated their cost by 3.4 to 4.55× (`lesson-price-successor-by-spend-not-occupancy`; the 61264f83 successor spent 867,921 against 258,586 of occupancy). A duplicate-successor race after compaction needed the header fields to close it (`.claude/plans/sage-ledger-ff95b189-5174-4f7f-8371-de4f3e6b15e7.md:98`). And the supervisor's own occupancy keeps climbing. The one supervised run in this repository closed at 39.76% (`.claude/plans/sage-ledger-61264f83-e776-4c65-b248-185c2ea2d83b.md:90`). So the successor slows the parent's growth without bounding it.

**What the successor was for, and what does the same job.** A successor is a controlled rehydration: a fresh window that reads the ledger. Native compaction with a `SessionStart(compact)` hook is the same rehydration in the same window. The hook exists (`install.sh:1061`, `offer_compact_hook`), the docs say it fires only after a compaction, and the ledger header already re-teaches the occupancy duty from line 1. Supervisor mode already rides compaction (`SKILL.md:324`). That is a forced fallback for a role that dispatches nothing, so it does not settle the question for the parent. It does show that the design already accepts a compaction over durable state. The parent's extra exposure is the state written since its last bring-current point, and step 3's checkpoint rung exists to close that gap.

The compaction's trigger point was the unknown that made a successor necessary. The harness lets the user set it. `/autocompact <size>` takes an absolute token count from 100k to 1M. `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` takes 1 to 100 as a percentage of a model-tuned window that no document states, only lowers the threshold, and reaches every subagent at its own window. The absolute form is the knob to recommend, because it shares a denominator with `SAGE_WINDOW`.

**The cost question, stated as arithmetic the record cannot yet answer.** Every parent turn re-reads the whole window at the cache-read rate: 0.1× the input price on most models, 0.025× on Fable 5.1 and Mythos 5.1. A successor resets the working actor from about 300k to about 60k. That saves (300k − 60k) × the rate per turn: 24k input-equivalent tokens on Opus, 6k on Fable. Its fixed cost, in the same input-equivalent units, is the note plus the boot read. The note is 5 to 13k output tokens, at 5× the input price: 25 to 65k. The boot read is about 60 to 70k of cache creation, at 1.25×: 75 to 88k. The only measured boot is `cfff08b5`'s successor at 65 to 70k spend for a Step 6 close, so the range is an upper bound on a boot alone. The fixed cost is therefore about 100 to 150k. On those figures the successor breaks even inside four to six turns on Opus and seventeen to twenty-five on Fable. Against that saving stand the supervisor's own turns at 300k and above, which the record shows continuing to 39.76%. Neither actor's turn count is recorded anywhere, and the journal's `spend` formula excludes `cache_read` by definition (`references/harness.md:231`). So the cost of high occupancy has never been measured on this machine, in either design. Step 5 below adds the instrument. Until it reports, cost is not a ground for either keeping or retiring the successor.

Codex Sage, for comparison, never spawns a successor. It writes `handoff.json` and hands over explicitly, and it records automatic detection as unavailable (`sage/skills/sage/references/codex.md:65`).

**Verdict: adopt the user's proposal as an experiment, in this form.** The user's instinct is that notes plus the ledger are enough for one parent. The record supports that for every run since 2026-08-27 and cannot yet speak for a run the size of the early ones. The design:

1. **The ledger absorbs the note.** Two sections join the ledger. `### Resume state` holds the write lease, the snapshot baseline with one `sha256sum` line per task-owned file, and the next action. It also holds the `agentId → description` map with the `subagents/` directory path. `### Open questions and discarded approaches` holds the note's `Open questions` and `Discarded` fields. Both are restamped at every bring-current point, which is already a duty. The handoff note file and its template go. `/sage resume [ledger-path]` reads the ledger.
2. **Compaction is the designed recovery.** `install.sh` installs the `SessionStart(compact)` hook by default, where today it offers it. It also offers to add `/autocompact 600k` to the user's settings, with the caveat that any subagent reaching that occupancy compacts too. Whether any sage unit reaches 600k of occupancy is unmeasured; the record's per-unit figures are spend, not occupancy. The hook's message becomes: re-read `### Resume state`, then re-read `SKILL.md`; dispatch nothing until both are read. After a compaction the parent re-hosts the watchdog from the ledger's `subagents/` path. A filed Claude Code issue reports background task handles orphaned across the boundary. That is a report, not a documented behaviour, and the first compacted run checks it.
3. **The sensor stays; the rung changes.** `sage-watch.sh` keeps reading occupancy against `SAGE_WINDOW`, as today. Its one rung becomes a checkpoint rung with a defined value in both cases. With `/autocompact <size>` configured, it fires at `<size>` minus 5% of the window. With nothing configured, it fires at 41% of the window: the measured no-compaction lower bound of 466,802 tokens (46% of 1,006,380) minus five points. The rung's action is a checkpoint, not a handover. Bring the ledger current. Restamp `### Resume state`. Write one `### Decisions and deviations` row with A4's arithmetic (room remaining, work remaining, reserve). Surface it. That is the one useful thing a parent can do before a compaction.
4. **Delete** the `orchestrator` agent, supervisor mode, chaining, the `Generation` and `role` header fields and the lint check on them, `SAGE_OCC_ACK`, and `## Handover`. A `## Compaction and resume` section of about 200 words replaces it, in today's `SKILL.md` at the same position until B1 lands, then in the router (B1 item 1).
5. **Record what the design has never measured.** The `run` line gains four fields. `compact=<n>` counts compactions, each with occupancy before, tokens dropped, and what the parent re-read. `turns=<n>` counts the parent's deduplicated assistant records. `occ-sum=<tokens>` is the sum of occupancy over those turns, which is the cache-read cost the `spend` formula excludes. `saving-post-rung=<tokens>` is the sum, over the turns after the checkpoint rung fired, of (occupancy − 60k): the most a successor could have saved on this run, because it ignores the supervisor's own turns. The checkpoint row records the turn index at which the rung fired, so the split is exact. `sage-watch.sh --status` already reads the parent transcript and can print all four. The first five compactions are the design's first measurement, and the run record's Gaps line names anything the ledger did not hold.

**The gate and the reopen condition, stated now.** The experiment fails on any one of three observations. A post-compaction parent re-dispatched a unit the ledger showed as running. A post-compaction parent lost a finding the ledger should have held. Or `saving-post-rung`, priced at the cache-read rate, exceeds the successor's fixed cost of about 100 to 150k input-equivalent tokens. That comparison favours the successor, because `saving-post-rung` ignores the supervisor's own turns, so a gate that fires on it is conservative. If any fires, the design to reach for is a plan-time phase split, not a sensor. At Step 2, a plan whose shape predicts the parent past the checkpoint rung names the phase boundary where a fresh owner takes the remainder. The sensor-triggered successor does not return, because the record shows it fires at the wrong moment.

**What this supersedes.** A4's response arithmetic survives as step 3's row. A4's decision to keep the 30% rung does not. The "hash the task-owned files" adaptation in Part A is step 1's `sha256sum` line. R9's "no change" verdict on supervisor mode is superseded, because step 4 deletes supervisor mode.

### B3. State the memory boundary in one table; the run already obeys it

**The premise is one version out of date.** The question assumed a run tracks knowledge items, updates their band and consults them later. That was v2, retired on 2026-08-27. Under v3 (`references/memory.md:7`) a run's only write is an append of plain lines to the journal. It edits no KI, bumps no count, flips no status. Every structured write is `/sage-promote`'s. So the proposed model, corpus in, logs out, promote in between, is the design that shipped. Two things are not yet in that shape.

1. **The text does not say it in one place.** Codex Sage states the boundary as a three-row table (`sage/skills/sage/references/policy/memory.md:9`). The rows are promoted knowledge, current-run log and closed-run log. The columns are runtime read, runtime write and promotion access. sage-claude states it across 4,185 words, of which a run needs about 1,100. The other 3,088 describe what promote does with the files.
2. **One raw read remains.** Step 2 reads the journal tail since the last `mark` (`references/memory.md:100`). The read returns `obs` and `use` lines too, but the run uses only the `run` lines, as same-shape rows to price from. This is the only place a run reads a log rather than a KI. R3 defended it on 2026-09-03 against the Codex clause that forbids it.

**Verdict: adopt the table; keep the one read as a named exception.** The design:

1. `references/memory.md` opens with a three-class table in Codex Sage's form with sage-claude's names. Row one, the corpus (`SKILL.md`, `references/`, `memory/shared/`, `memory/local/`): read at Step 2, never written by a run, written by `/sage-promote`. Row two, the run's own ledger: read and written by the run, read by `/sage report` and `/sage resume`, never read by a later run. Row three, the journal: appended by the run at Step 6, drained by `/sage-promote`, read by a later run for its `run` lines only. The Step 2 read becomes `awk '$2=="run"' memory/journal.md | tail -n 3` so that the read matches the row. The type is the second positional field; a plain `grep ' run '` also matches `obs` payloads that contain the word. One sentence under the table names the exception and its reason: a `run` line is an actual, not a lesson, and `price-off-a-same-shape-row` (calibration: established) says the actual beats the band. The pure form is available if the user prefers it. `/sage-promote`'s drain writes the newest three `run` lines into the matching band KI's body, and the Step 2 journal read goes. Its cost: pricing data lags one promote pass, eight to twelve runs at the current hint bar. Promote must also keep those rows current in a KI body. The exception is the better trade.
2. The run-facing file keeps the table, the Step 2 read, the Step 6 append, the hint and the journal grammar. The rest moves to `claude-skills/sage-promote/references/memory-contract.md` (B1 item 4).
3. **Delete consolidation step 2.** All 72 files under `memory/local/` on this machine, 61 KIs and 11 stats sidecars, carry `reconciled:`. The archive reconciliation walk (`claude-skills/sage-promote/SKILL.md:126-133`, about 330 words) can therefore never find work again. The field stays on the files; the procedure goes. Reproduce with `for f in ~/.claude/skills/sage/memory/local/*.md; do grep -q '^reconciled:' "$f" || echo "$f"; done`, which prints nothing.
4. **Rename the strength band.** The word `band` means two things: a cost band KI (`band-dispatch-floor`) and a rule's strength (`band: established` on a stats sidecar). Rename the sidecar field and the KI review's row to `calibration:`, which is what the skill-text tag already says. That is one `sed` over `local/*.stats.md`, one edit to the KI review table and to the field contract, and one to `bin/sage-index.sh`'s column header.
5. **Give the strength band an instrument, then a falsifier.** Its stated purpose is to let Step 2 weigh two rules against each other when budget forces a choice (`SKILL.md:96`). No `use` line in the live journal or its three archives records such a weighing. The six `band` mentions on `use` lines are all cost-band KIs. But the `use` grammar has no slot for a weighing (`references/memory.md:88`), so that absence is the absence of an instrument, not evidence of disuse. First, add one token to the grammar: `weigh <ki-a> over <ki-b>: <why>`. Then file a `gap` KI with this falsifier: ten runs after the token lands write no `weigh`. If it fires, the three-level band collapses to the sidecar's `count:` and the `(calibration: …)` tags go. The crossing arithmetic, the upward-only rule and the cross-machine highest-earned rule go with them. That is about 600 words across `memory.md`, `sage-promote/SKILL.md` and the design notes. The compression floor lists the strength band as protected, so nothing moves until the falsifier fires.

### B4. JSON for guidance or state: rejected

Codex Sage's guidance is Markdown. Its JSON is elsewhere: schemas, fixtures, the run record, the knowledge index and the source manifest, each validated by a Python library. The question was whether agents act better on JSON rules. Nothing measured here says so. Claude Code's skill format is Markdown by contract. The ledger lint already parses Markdown tables. R1 rejected a JSON ledger for a reason that still holds: the measured failures were rows not written, and a format cannot make a model write a row. Keep Markdown everywhere. The one JSON mechanism worth naming is a source manifest with per-file hashes that `generate-skill-bundle.py --check` verifies. `install.sh` and `/sage-promote`'s `diff -rq` between repo and installed tree already do that job.

## Part A. Items to adopt or adapt, from the 2026-09-03 study

Each item names what Codex Sage does with a pointer, what sage-claude does today with a pointer, the verdict, the reason, and the design. The sections below stand in the priority table's order. Line references inside them point at the corpus as it stood on 2026-09-03; B1 moves several of those homes, and each item says where its text lands when it does.

### A2. Measure the effective model from the transcript instead of asserting it

**Codex Sage.** Placement records `requested_model` and `effective_model` separately, and `effective_model` may be `unknown` (`sage-artifact-v1.schema.json:353`; `sage/skills/sage/references/guarantees.md:14`). Codex cannot observe the effective model, so the design preserves the unknown instead of copying the request.

**sage-claude today.** The unit table's `model used` cell is filled by the parent from what it passed (`references/dispatch.md`, Unit table). `bin/sage-watch.sh --status` prints occupancy and spend per agent but no model (`grep -n model bin/sage-watch.sh` returns nothing). The alt lane already reaches for measurement: `references/harness.md`, "The alt lane", settles family identity by grepping the transcript.

**Verdict: adopt, and go further than Codex Sage can.**

**Reason.** Claude Code writes `message.model` on every assistant record of every agent transcript. Measured this run: all six explorer scouts show `claude-haiku-4-5-20251001` on every record. `references/harness.md`, "Models and effort", lists two paths that silently swap a requested model, the `CLAUDE_CODE_SUBAGENT_MODEL` override and the `availableModels` fallback, and says "either path turns every Model cell in the ledger into fiction". The transcript is the one place the fiction cannot reach. Codex Sage has the right column and no sensor. sage-claude has the sensor and no column.

**Design.**

1. `bin/sage-watch.sh --status` prints `model=<value>` per agent, taken from the latest assistant record's `message.model`, or `model=unknown` when no assistant record exists yet. About ten lines of `jq`, beside the fields it already prints.
2. The unit table's `model used` cell records that measured value, with the word `measured`, at the bring-current point where the parent reads `--status`. A cell the parent fills from its own dispatch says `asserted`.
3. A measured value whose family or tier differs from the Plan row is a `### Decisions and deviations` row, written when it is read, because it means a swap happened that the run did not order.
4. The Step 6 run record's Agents line carries the measured model, which is what makes the audit surface true after the fact.

Cost: one script edit and two template words. A lineup claim about which model ran becomes a grep, not a belief.

### A5. Add a secret-shape check to the ledger lint

**Codex Sage.** `sage/lib/facts.py:69-101` validates every fact appended to a run log: it rejects payloads over a size cap, requires a hash and locator for confidential facts, and rejects credential-shaped strings with the message "a current-run fact payload appears to contain restricted credential material" (`facts.py:101`). The skill's guarantees list "credential/payload rejection" as enforced (`guarantees.md:19`).

**sage-claude today.** The ledger is free text. Evidence cells quote command output. `references/harness.md:262` measured that `.claude/plans/` is not gitignored in a fresh repository, so a ledger can enter a user's history with one `git add -A`. Nothing scans it.

**Verdict: adopt, as a lint check.**

**Reason.** The write-time gate Codex Sage uses does not exist in a Markdown ledger, but the lint runs at every bring-current point, which is the same moment. The check is deterministic, costs a regex, and fails open on unknown formats, which is the lint's existing contract.

**Design.** `sage-lint.sh` gains `secret-shape`: one line per match of a small fixed pattern set on the whole file, outside fenced blocks: `AKIA[0-9A-Z]{16}`, `-----BEGIN [A-Z ]*PRIVATE KEY-----`, `ghp_[A-Za-z0-9]{36}`, `xox[baprs]-[A-Za-z0-9-]{10,}`, `Bearer [A-Za-z0-9._-]{20,}`, `sk-[A-Za-z0-9]{20,}`. The header states the blind spot: it knows these six shapes and nothing else. A hit at Step 6 is a surfaced event, like any other lint line. The same check runs in `--corpus` mode over `memory/`, because knowledge items are committed to the repository and `sage/skills/sage-promote/references/workflow.md:15` names the leak that matters there: credentials, private paths, user identity.

### A8. Two lint checks that Codex Sage's invalid fixtures name and the text lint can make

**Codex Sage.** `sage/artifacts/fixtures/invalid/` holds 63 fixtures. Two of them describe conditions a text lint can read: `accepted-finding-without-verification.json` and `unknown-spend-misrepresented.json`.

**sage-claude today.** `sage-lint.sh` has eleven checks. `triage-state` fires on an empty or illegal triage cell. Nothing fires on an `accepted` finding whose evidence cell is empty, or on a `reported` unit whose `actual tokens` cell is empty.

**Verdict: adopt both.**

**Reason.** Rail 4 is checked from `--status` in flight, but the `actual tokens` cell is what the run record, the journal `run` line and the next run's estimate read; an empty one hides spend from every later reader. An accepted finding with no evidence is the shape the commit gate's second half exists to catch by hand (`SKILL.md`, Step 5, "read the triage column yourself"). Both checks are cell-emptiness tests on labelled columns, which is exactly the shape `triage-state` already implements.

**Design.** `finding-evidence`: a Findings row whose triage cell reads `accepted` and whose evidence cell is empty. `unit-actual`: a Unit table row whose state cell reads `reported` and whose `actual tokens` cell is empty. Both state in the header what they cannot see: a non-empty but false cell.

### A1. Classify every acceptance criterion by evidence class at plan time

**Codex Sage.** Every criterion carries `evidence_class` with three values: `machine`, `agent_observable`, `human_only` (`sage/artifacts/schemas/sage-artifact-v1.schema.json:90`). `sage/policy/contracts.md:54` requires the classification before work starts. Every verification then records `verdict: pass | fail | AwaitingHuman` against a criterion (`schema:505`).

**sage-claude today.** Criteria go into `### Plan` as verbatim text (`references/dispatch.md`, Plan template). The split between a measured pass and a judged pass appears only in the run record at Step 6 (`references/dispatch.md:187`), where it asks to name "any machine-verifiable case that downgraded to judged". Nothing earlier in the run defines which cases were machine-verifiable, so that sentence has nothing to compare against.

**Verdict: adopt.**

**Reason.** The run record already wants the measured-versus-judged distinction. Without a plan-time class, a reviewer decides at Step 5 what kind of evidence a criterion needs, at the moment it is cheapest to decide "judged". sage-claude's own Step 5 warns that "a criterion can pass literally while the mechanic it describes is broken" and that a verifier with two words available "will guess". A class fixed before the work is what turns the downgrade into a checkable event.

**Design.**

1. In the Plan template, each criterion line starts with its class in brackets: `R1 [machine] <text>`, `R2 [agent] <text>`, `R3 [human] <text>`. Three words, matching the run record's existing vocabulary: `[machine]` passes only by a command whose output is recorded; `[agent]` passes by a clean-context reviewer's read; `[human]` is `Awaiting human` until a person rules.
2. Step 5 adds one sentence: a `[machine]` criterion reported as a judged pass is a downgrade, and the run record's Verification line names it.
3. `sage-lint.sh` gains a check `criterion-class`: every line matching `^\s*R[0-9]+ ` under the Plan's `Criteria:` label carries one of the three bracketed words. Blind spot, stated in the header: it reads the label, never whether the class is right.
4. The blind acceptance-suite author (`references/topologies.md` #10) receives the class with each criterion, because it decides whether a case is executable or a human checkpoint.

Cost: a template edit, one Step 5 sentence, roughly twenty lines of awk.

### Two small adaptations

The first of these three is absorbed into B2 step 1, where the `sha256sum` line becomes part of the ledger's `### Resume state`. The other two stand on their own.


**Hash the task-owned files into the handoff note.** Codex Sage's handoff carries `path, sha256, kind, device, inode` per baseline file and refuses to resume on drift (`sage-handoff-v1.schema.json:41`; `test_phase1.py:424`). sage-claude's `/sage resume` compares `git status` against Paths touched. That misses untracked and out-of-repo files, which the snapshot protocol already flags as unrecoverable. Add one `sha256sum` line per task-owned path to the note's Snapshot baseline field, and have `/sage resume` re-run it. One command each way.

**Name the spend figure's provenance in the cell.** Codex Sage tags every usage value `measured | provider-reported | estimated | unknown` (`2026-08-31-sage-codex-proposal.md:728`). sage-claude's journal already writes "transcript-measured" and "notif counters read zero" by hand. Make the `actual tokens` cell carry one of `probe`, `notif`, `projection`, so rail 4 knows which kind of figure it is comparing. This is the same move as A2 for spend.

**Check `shared/` for machine-local content.** `check-phase0.py` has `host_leak_issues`, a scan for host-specific names in portable text. sage-claude's memory records two of this machine's promote passes writing a shared band down (`defect-this-machine-wrote-shared-bands-down`, now dropped with its subject). A `--corpus` lint line that flags absolute paths, session ids and `k`-suffixed figures inside `memory/shared/` is the same idea at the cost of one grep.

### A3. Give the coordination check a fixed state word

**Codex Sage.** `CoordinationOutcome.state` is an enum: `open | beneficial | harmful | inconclusive | not_delegated`, with evidence fields beside it (`sage-artifact-v1.schema.json:550`; `sage/policy/contracts.md:60`).

**sage-claude today.** The coordination check is a prose line in the run record (`references/dispatch.md:189`) and a surfaced event when negative (`SKILL.md`, Step 6). It is the line that can falsify sage's own premise, and it cannot be counted across runs because it has no fixed vocabulary.

**Verdict: adopt the state word only.**

**Reason.** `/sage-promote` reads the journal to build its slate. A prose sentence per run is invisible to `grep -c`. The four words cost nothing, and they make "how often does the fan-out buy nothing" a number instead of a feeling. The extra Codex fields (`unique_contributions`, `duplicated_work`, `interventions`, `critical_path_effect`) duplicate what the run record's Agents and Deviations lines already hold, so they are not taken.

**Design.**

1. The run record line becomes `Coordination check: <beneficial | harmful | inconclusive | not-delegated> — <one clause of evidence>`. `harmful` is for a run where the fan-out cost the result something, for example a writer collision or a lost finding in a distillation. `inconclusive` replaces "nothing; one agent would likely have matched it".
2. The journal `run` line gains `coord=<state>` next to `agents=N`, so the slate can count it.
3. `sage-lint.sh` gains `coord-state`: the run record's Coordination line, when present, starts with one of the four words.
4. `harmful` and `inconclusive` both remain surfaced events, as the negative answer is today.

Evidence status: argued, unmeasured. No memory item records a run where the prose form blocked a count. Falsifier: the KI-review stage of `/sage-promote` runs three times without ever wanting the count.

### A7. Record a novelty disposition when a KI is minted

**Codex Sage.** Every create or revise candidate carries a `NoveltyReview`: the stable IDs it was compared against and one disposition, `novel | revise_existing | overlap_accepted` (`knowledge-record-v1.schema.json:96`; `promotion-contract.md:19`). The library rejects a review that did not name every other active record (`sage/lib/knowledge.py:604`, `_verify_novelty_review`).

**sage-claude today.** The minting step already requires the comparison: "where an existing KI already records the same observation, treat the line as a `confirm` of it instead" (`claude-skills/sage-promote/SKILL.md:120`). What it does not require is a record of the comparison's result. Nothing in a minted KI says which existing KIs it was weighed against or why it was judged new. The memory shows the cost of an unrecorded comparison: `defect-migrated-lesson-class-calls-inconsistent` records three lessons with same-shaped evidence and inconsistent class calls. (The separate "one home" check at `:76` covers the skill text, not the KI set.)

**Verdict: adapt, small.**

**Reason.** A comparison that leaves no record cannot be audited when two KIs later turn out to overlap. Recording three words at minting time is cheaper than the reconciliation the memory has already had to do once.

**Design.** Landed by hand (see "Order of work"). The minting step in sage-promote runs `bin/sage-index.sh`, names in the new KI's provenance the KI ids whose recogniser overlaps, and writes one of three words: `novel`, `revises <ki-id>`, `overlaps <ki-id> (accepted: <why>)`. `revises` routes the candidate into the existing KI as a confirmation or an edit instead of a new file. No script change: the index already exists, and the pass already reads it.

### A6. Split the promotion bar by evidence class

**Codex Sage.** Promotion thresholds depend on the record's class: a deterministic invariant needs one closed run plus a passing independent refutation; an empirical heuristic needs three distinct runs; shared-policy guidance needs six plus a behavioural evaluation (`sage/skills/sage-promote/references/promotion-contract.md:17`; enforced in `sage/lib/knowledge.py`, tested at `sage/tests/test_phase1.py:608`).

**sage-claude today.** One bar: three confirmations graduate a lesson to `shared/` (`SKILL.md`, Handover, "what closes such an observation is three confirmations"; `references/memory.md`). A deterministic fact about the harness, for example a transcript field's name, waits for the same three runs as a cost tendency does.

**Verdict: adapt the two-way split. Reject the number six.**

**Reason for the split.** A deterministic fact is settled by one reproduction, and sage-promote already owns the refuter that would test it (its degradation gate). Holding it for three runs delays knowledge the next run could use and costs nothing in safety, because the falsifier is a command. The distinction is the same one sage-claude's Step 5 draws between a measured and a judged pass.

**Reason against six.** The follow-up report itself says these numbers should be recalibrated "from outcomes not intuition" (`sage-codex-follow-up-report.md:154`), and no promotion has ever run under them. sage-claude already gates behaviour-shaping text with the two-arm behavioural lens (`references/topologies.md` #12), which is a stronger gate than a count.

**Design.** In `claude-skills/sage-promote/SKILL.md`, landed by hand as described under "Order of work" (that skill may not edit its own file), the minting stage classifies each candidate `deterministic` or `empirical` and writes the word into the KI's stats sidecar. `deterministic` may land in `shared/` after one run when the degradation gate's refuter reproduces the falsifier's command. `empirical` keeps the three-confirmation bar. The `references/memory.md` shape section names the field and its two values.

### A9. One table that says which controls are enforced and which are advisory

**Codex Sage.** `sage/skills/sage/references/guarantees.md:7-22` lists sixteen controls and states for each whether Codex Light enforces it, observes it, or only asks for it. The invariant `EXP-LIGHT-ADVISORY` requires that a control be reported advisory unless a boundary proves enforcement.

**sage-claude today.** The same facts exist, spread across `SKILL.md` Step 3 ("Only a saved agent file enforces this; on a plain dispatch the line is an instruction"), `references/harness.md` ("Frontmatter beyond tools"), `references/dispatch.md` (Per-unit caps "BIND") and the `sage-alt-guard.sh` header. A parent deciding whether a brief line is enough has to remember all four.

**Verdict: adopt as one reference table, no new rules.**

**Reason.** Axiom 2 says every claim is checkable; a brief line that reads as a control but binds nothing is the one claim the parent cannot check by reading the brief. Evidence status: argued, unmeasured. No memory item records a run that mistook an advisory line for an enforced one. Falsifier: three runs consult the table and none changes a brief because of it.

**Design.** A table in `references/harness.md` with one row per control: tool scope, `maxTurns`, model, nested delegation, alt no-model rule, write lease, occupancy threshold, budget rail, one-writer rule. Columns: enforced by what (agent file, hook, script, nothing), and the failure mode when only asked. Every row points at the section that owns the detail, so the table adds no second home. The `--corpus` lint mode already checks that citations resolve.

### A10. Record the recogniser that should have fired

**Codex Sage.** For each loaded knowledge id, the run appends whether it was useful, neutral or misleading, and separately "a missed recogniser and the affected decision" (`sage/policy/memory.md:15`; `sage/skills/sage/SKILL.md:30`).

**sage-claude today.** The `use` line records `hit` or `miss: <why>` for KIs read at Step 2 (`references/memory.md:88`). A KI that was not loaded but whose rule applied leaves no trace, so the KI-review stage cannot see that a recogniser is too narrow.

**Verdict: adopt one clause.**

**Reason.** The KI-review stage retires knowledge on recorded misses. A recogniser that is too narrow never gets loaded, so it never records a miss and can never be retired or widened. Evidence status: argued, unmeasured. The journal holds no instance of a KI that should have fired and did not, which is exactly what this clause would make visible. Falsifier: ten runs write the clause and none ever names a KI.

**Design.** The `use` grammar gains `<ki-id> missed: <what matched in hindsight>` for a KI not loaded at Step 2 whose rule the run needed. Step 6's Coordination and Gaps writing is the moment to ask the question. The KI-review stage treats `missed` as a recogniser defect, not a rule defect.

### A4. Make the handover response depend on remaining work, not only on occupancy

**Status after the 2026-09-04 revision: absorbed into B2.** The arithmetic below survives as B2 step 3, written at the checkpoint rung. The decision this item made to keep the 30% rung does not survive: B2 retires the successor the rung fed, and the rung moves to the configured compaction point. The text is kept as the record of the evidence behind the arithmetic.


**Codex Sage.** Recommendation 1 of the usage investigation (`codex-vs-claude-sage-usage-investigation.md:196-212`) replaces a fixed 30% rule with absolute headroom: `remaining = window - occupancy`, `required_headroom = max(p95_next_turn_growth, 2 * handoff_payload, recovery_reserve)`, prepare a checkpoint when `remaining <= required_headroom`, hand over at a clean phase boundary or at once when another substantive turn is required, and "record how every term was measured; if growth data is unavailable, use a conservative pilot value and label it estimated".

**sage-claude today.** A single rung: parent occupancy at 30% of the window fires `occ-30pct`, and `## Handover` runs (`SKILL.md`, Handover). The installed memory holds `lesson-occ-30pct-fires-with-nothing-to-launch` in `~/.claude/skills/sage/memory/local/`, at `count: 7` with the last two occurrences on 2026-08-28: the rung fires late in investigation-shaped and corpus-edit runs. Its fifth occurrence (2026-08-27) names the sharper predicate: the threshold was reached "with one unit in flight and the deliverable already durable on disk", so the carve-out is "nothing in flight and the deliverable durable", not "nothing left to launch". This run reached 23% with all scouts landed and the draft not yet written.

**Verdict: adapt.** Keep the sensor and the 30% rung. Change what the parent does when it fires.

**Reason.** The Codex recommendation was written for a 258k-token window where 30% is 77k and compaction was observed between 71% and 96% of the window. Those numbers do not port. What ports is the shape of the rule: the decision should compare the room that remains with the work that remains, not with a fixed fraction. sage-claude's own seven observations are the local evidence that the fixed fraction misfires. The honesty clause ports too: no auto-compaction has been observed on this machine, so the reserve is an estimate and must say so (`references/harness.md`, "Transcripts and the token arithmetic").

**Design.**

1. The rung stays as it is. `sage-watch.sh` changes nothing.
2. When it fires, the parent computes two figures at that bring-current point and writes them into one `### Decisions and deviations` row: `remaining = window - occupancy`, and `needed = reports still to land + fix rounds still planned + Step 6 record + reserve`. The reserve is the measured handoff write cost, 5 to 8k (`references/harness.md`), plus a compaction margin labelled `estimated`, because no local measurement places the auto-compact trigger.
3. `needed < remaining`, nothing in flight, and the deliverable already durable on disk: finish in place. The row records the arithmetic and the handover does not run. The rung is acknowledged with `SAGE_OCC_ACK=1` exactly as a supervisor does today.
4. Otherwise: run `## Handover` as written.
5. The journal `run` line records both figures when the rung fired, which is how the reserve gets a measured value after enough runs.

What this does not do: it does not move the threshold. Moving it needs a measurement of where compaction fires, and there is none. Recommendation 12 of the same document (`:294`) is the design for that measurement: a matched experiment, early handover against native compaction, with overlap and rehydration cost recorded. sage-claude has never observed an auto-compaction, so the experiment cannot run here until one does. Record it as the open measurement behind this item.

### A11. A pre-registered paired evaluation, scaled down

**Codex Sage.** `sage/evaluation/phase-1/` defines a frozen two-arm pilot: 20 paired tasks, control without the skill and treatment with it (`prompts/control.txt`, `prompts/treatment.txt`), a six-dimension rubric with mandatory-failure conditions (`rubric.json`), two blind judges and an adjudicator, a non-inferiority margin, a 1.25× spend-comparability bound, and a pre-registered definition of an operator intervention (`preregistration.md`, hashes in `PREREGISTRATION.sha256`). It never ran, because Codex exposes no hard per-arm token cap (`STATUS.md`).

**sage-claude today.** Two open gaps have no measurement path: `gap-unattended-vs-approved-plan-unmeasured` ("running unattended is unmeasured against running with a human approving the plan first") and the handover-versus-compaction question in A4. The two-arm behavioural lens (`references/topologies.md` #12) tests one text change, not a policy's value.

**Verdict: adapt the method, unscheduled.**

**Reason.** The method is sound and independent of the designs it was meant to evaluate. sage-claude has what Codex lacked: a per-unit spend read (`--status`) and a budget rail that can serve as the hard cap. The cost is real, so this is a design to keep, not work to start.

**Design.** Five to ten paired tasks, not twenty; arms are "plan approved by the user" against "unattended"; the cap is rail 4's per-unit figure; scoring by a clean-context `verifier` against the rubric's six dimensions with the mandatory failures kept verbatim; pre-registration is one file with its hash in the ledger before the first task runs. Run only when a gap KI has been open long enough that its cost exceeds the pilot's.

### The usage investigation's other six recommendations, one line each

The draft above weighs recommendations 1 (A4), 4 and 6 (R7), 5 (R8) and 8 (R9). The rest:

- **Rec 3, separate occupancy, spend and progress rails (`:219`).** Already separate in sage-claude: the occupancy rung, rail 4, and the failure ladder's same-signature stop. No change.
- **Rec 7, bound worker occupancy and return size (`:258`).** sage-claude bounds reports at 1–2k tokens and measured the handoff note at 5–8k. No change.
- **Rec 9, reuse a verifier thread only for a tight re-check (`:274`).** This is sage-claude's own rule, cited back from its memory. No change.
- **Rec 10, replace the blanket 4× with named cost profiles (`:280`).** Touches the open KI `gap-4x-budget-multiplier-may-be-consumed`, which records that every past ceiling raise was spent up to the new ceiling. A profile is a differently named ceiling and does not answer a consumption pattern. Rejected; the KI stays open, and the honest estimate-versus-actual journal line remains the instrument.
- **Rec 11, record quota before and after each phase (`:290`).** sage-claude records estimate against actual per run and per unit. Per-phase adds a duty with no reader. No change.
- **Rec 12, the matched handover experiment (`:294`).** Folded into A4 as the open measurement behind it.

## Items rejected, with reasons

### R1. JSON run record as authority, Markdown as a hash-bound projection

Codex Sage makes `run.json` plus an append-only `facts.jsonl` the authority and renders `run.md` from it (`sage/scripts/sage-light.py`: `start` 353, `commit-state` 486, `append-fact` 535, `render` 559; `sage/lib/artifacts.py`). Schema and semantic validation reject illegal states before they land.

Rejected for sage-claude. The ledger's measured failures were compliance failures: ledgers written once and post-hoc, dispatches never entered, findings parked in illegal states (`SKILL.md`, Step 4, the lint paragraph). A JSON authority moves the same duty from "write the row" to "call `commit-state`". A model that skips the row skips the call. The one thing JSON buys, semantic validation, is what A1, A3, A5 and A8 take piecemeal into the text lint, at the cost of a few awk lines each. What it would cost: every state change becomes a CLI round trip through the parent's context, the working record stops being readable by a person mid-run, and a compaction-time reader loses the header comment that today re-teaches the occupancy duty from line 1. No measurement shows the JSON path produces better-kept records, because no Codex Sage run has been kept.

### R2. Immutable plan revisions

Codex Sage forbids editing an admitted plan; a change is `PlanRevision N+1` with `prior_units` dispositions (`sage-artifact-v1.schema.json:252`; `sage/policy/contracts.md:9`).

Rejected. `references/dispatch.md`, Decisions and deviations, records the audit that produced the current rule: amendments were leaving the rows they amended untouched. The fix chosen was the `superseded → D<n>` tag on the amended row plus a Decisions row, with the sentence "a fifth representation of the plan cannot fix non-compliance with the four that already exist". A revision series is that fifth representation. No new evidence has arrived since the tag rule was written, and the lint already strips the tag when it compares Plan and Unit id sets.

### R3. A run may write facts only, never observations

Codex Sage forbids the active run from recording any lesson (`sage/policy/memory.md:10-13`; `test_phase1.py:287` rejects `lesson.extracted`). Only a later promotion pass may mine the closed log.

Rejected. sage-claude's `obs` lines are written at Step 6 by the parent that holds the run's whole context, with a falsifier attached, and they flip no status. The journal shows what they are worth: run `5f8bfa2d` recorded that six of nine review findings were defects the parent's own fixes introduced, a lesson no fact log without the parent's reasoning would carry. Codex Sage's promotion pass would have to reconstruct that from facts, and it has never run on a real closed log to show it can. The point where both designs agree, that the run consolidates nothing and promotes nothing, is already sage-claude's v3 rule.

The reading half of the same Codex rule is rejected too. `sage/policy/memory.md:13` forbids an active run from scanning "raw prior ledgers, journal tails, closed logs, archives for same-shape precedent". sage-claude's Step 2 requires exactly that read: the journal tail since the last `mark` is where same-shape run lines come from, and the live shared rule `price-off-a-same-shape-row` (calibration: established) says a same-shape logged row beats band arithmetic. Adopting the Codex clause would retire that rule with no measurement against it. The Codex rule protects a Codex weakness, a root that re-reads whole logs into a 258k window; sage-claude reads a few tail lines into a 1M window and records on the `use` line whether each read helped.

One adjacent field gets a verdict here rather than nowhere: Codex Sage's promotion candidate carries `expected_benefit`, `expected_cost` and a `net_assessment` (`promotion-contract.md:17`; `knowledge-record-v1.schema.json:85`). Rejected. sage-promote already gates every candidate with a falsifier and a refuting degradation gate; a self-declared net assessment is a field the author fills in its own favour and no later stage reads.

### R4. Capability negotiation, runtime protocol v0, `sage-core`, Managed mode

The proposal's architecture sections 2 to 5 and the `sage/runtime/protocol-v0/` schemas define principals, capability snapshots, observation envelopes, leases with fencing tokens and crash-safe dispatch.

Rejected for now. Claude Code exposes no scheduler, lease or approval surface for a core to own, and the proposal's own Phase 2 gate, which was to decide whether Managed mode is needed, never ran. The usage investigation's numbers show what building the design's first two phases cost without a single evaluated run. sage-claude's design already names its enforcement gaps honestly (`references/harness.md`, "Cautions"). Reopen only if a measured run shows a failure that a saved agent file, a hook or a script cannot close.

### R5. The receipt-bound installer

`sage/lib/lifecycle.py` (2,517 lines) and 13 tests in `LifecycleTests` implement an ownership receipt with journal phases, resource identities, backups and recovery from interruption at every phase.

Rejected as a port. `install.sh` already keeps timestamped backups outside the auto-discovered directories and writes manifests that `uninstall.sh` reads to decide what it owns (`install.sh:121-142`; `uninstall.sh:197-216`). The installer defects sage-claude has measured, a `.bak` clobbered on the second install and a guard testing `[ -f ]` on a directory, were found by the installer-execution verifier in Step 5 and fixed. No incident of an interrupted install or an unrecoverable uninstall exists locally. The receipt design solves a problem that has not occurred, in a language the installer does not use. Keep the execution-verifier check. Revisit if an uninstall ever removes something it did not own.

### R6. Placement by requirement vector instead of tier

Codex Sage records `corpus_size, ambiguity, reasoning_steps, tool_needs, latency_preference, cost_ceiling, independence_required, verification_criticality` per unit and resolves them through a host profile (`sage-artifact-v1.schema.json:171`; `sage/policy/delegation.md:72`).

Rejected. sage-claude's tier table is resolved against the live session at Step 2 and already crosses tier with step count (`references/harness.md`, "Models and effort"). The requirement vector has no calibration behind it, and it adds eight fields per unit that the parent fills by judgment, which is the same judgment the tier column records in one word.

### R7. Lower fan-out and the model-placement profile from the usage investigation

Recommendations 4 and 6 (`codex-vs-claude-sage-usage-investigation.md:231, 254`) cap fan-out at two concurrent children and three total, and move the root off the top model.

Rejected as Codex-specific. The spend pathology they answer is a root on maximum reasoning at twenty times the cheap model's cached rate, across thousands of cycles. sage-claude runs the parent on the apex model by a stated design decision (`references/harness.md`, "The parent is apex's real home"), caps at four, and prices every run against its own estimate. The evidence does not transfer. One mechanism in the recommendation is already in place: no child inherits the parent's model silently, because every dispatch names its model.

### R8. Cycle and compaction rails

Recommendation 5 adds rails at 25 root turns and 50 tool calls, and on compaction count.

Rejected. The numbers are unmeasured, and sage-claude's rails are multiples of the run's own estimate with floors (`SKILL.md`, Rails). The local analogue of runaway parent cost, run `87b40637` where the parent came in 60% over while the fleet came in under, was priced wrong, not counted wrong. B2 now owns the compaction side; A4 is absorbed into it.

### R9. Root and successor overlap

Recommendation 8 (`:270`) wants the old root to supervise only unresolved handles after handover and to stop substantive work, and to record the overlap cost.

No change. sage-claude's supervisor mode already limits the parent to steers, rails, the watchdog and one spot check (`SKILL.md`, Handover, "Supervisor mode"), and `## Handover` already orders every generation's supervision cost onto the `run` line. The recommendation describes the current design.

**Superseded on 2026-09-04.** B2 step 4 deletes supervisor mode, so this comparison no longer has a subject. The verdict stays as the record of what the two designs shared while both existed.

### Not adoptable because they are ports

Explicit-only activation, the six-step spine, the four axioms, the safe-and-worth tests, the topology catalogue, the failure ladder, the four rails, the snapshot protocol, one writer per tree, disjoint review lenses, the blind acceptance suite, the completeness critic, and the clean-code and diff-review policies in `sage/policy/implementation.md` and `software-review.md` are ports of sage-claude text. `sage/docs/phase1/equivalence.md` says so. Nothing comes back from them.

## Two things that look strong and are not

**The 63 invalid fixtures and 44 tests.** They prove that the Python library rejects the states its own schema forbids. They prove nothing about whether a Codex root model writes those states in a real run, because none has been recorded. The lint in sage-claude states the same limit about itself: it "reads legality, never liveness". Fixture count is not evidence of kept records.

**The sixteen-row guarantee table.** It reads as rigour, and A9 takes its form. But its content for Codex Light is mostly "advisory", "policy bookkeeping", "unknown unless supported". It is an honest inventory of what Codex Sage cannot enforce. It is not a list of things sage-claude lacks.

**The "15 times less text".** True for one file against one file. The router shape it points at is worth taking (B1). But a run loads its references. On that count the ratio is 4.3×, and 3.4× for the promote skills. About a third of the gap is text that Codex Sage moved into Python. R1 and R5 reject bringing that text back as prose, so it is not a saving available to sage-claude.

## What this proposal does not settle

- The checkpoint reserve in B2 step 3 (A4's arithmetic) has no measured value. It starts as an estimate labelled as such. Eight occurrences of the rung misfiring are evidence for changing the response, not for a number.
- A6 keeps three confirmations for empirical rules by inertia. No local evidence says three is right either. It says only that six has none.
- The Codex Sage test suite's portability defect was patched in a scratch clone for this study and not in the repository. Whether to fix it in `sage/tests/test_phase1.py` is a Codex Sage decision, outside this proposal's scope. It is one `sed` of `dir="/private/tmp"` to `dir="/tmp"`, or a `tempfile.gettempdir()` call.

- B2 makes native compaction the recovery path before one has been observed here. B2 steps 2 and 5 name what the first compacted run must check: whether the hosted watchdog survives the boundary, whether in-flight unit notifications arrive afterwards, and whether the summary leads the parent to re-dispatch a unit the ledger shows as running. Until five compactions are recorded, B2 is an experiment with a gate, not a result.
- B2's cost question has no data on either side. Neither actor's turn count is recorded, and the `spend` formula excludes cache reads. Step 5's four `run` line fields are the first instrument.
- B1's 20,000-word target is an estimate built from the duplicate list and the section shares. The measured figure is what the `--corpus` lint reports after the cut.
- B3 step 5 files a falsifier against the strength band, and only after the grammar gains a slot the falsifier can read. It removes nothing until that falsifier fires.

## Order of work, if adopted

1. **B2 first, as its own `/sage` run on the user's word.** It deletes text that B1 would otherwise have to move. Land the two ledger sections, the `install.sh` change, the rung change and the four new `--status` fields in `sage-watch.sh`, the `run` line fields, and the deletions. Verify with `references/topologies.md` #12's stop arm on the old `## Handover` and one `verifier` over the diff. The first run whose parent passes the checkpoint rung is the first real test. Step 5's record is what that run produces.
2. **B3 steps 3, 4 and the grammar token of step 5.** Delete consolidation step 2, rename the strength band, add `weigh` to the `use` grammar. `claude-skills/sage-promote/SKILL.md` may not edit itself, so this lands the way the memory's escalation did: a `/sage` run on the user's explicit word.
3. **B1, with B3 steps 1 and 2 and A9 inside it.** The router, the step files, the harness split, the memory split. One `/sage` run, one step file per writer unit under a write lease, a `verifier` per file, then the one-home grep and `bin/sage-lint.sh --corpus` over the result. That run's journal append files B3 step 5's `gap` KI.
4. **A2 and A8.** Script changes only, each testable against the ledgers already under `.claude/plans/`.
5. **A1, A5, the two surviving small adaptations, A3.** Template plus lint, one review round, into the step files B1 created.
6. **A10.** A grammar edit to the run-facing `memory.md`.
7. **A6 and A7.** Edits to `claude-skills/sage-promote/SKILL.md`, landed as in item 2.
8. **A11.** Unscheduled; a design kept against two open gap KIs.

Every item above is a corpus edit to behaviour-shaping text. `references/authoring.md` governs its form, and `references/topologies.md` #12 governs its verification.
