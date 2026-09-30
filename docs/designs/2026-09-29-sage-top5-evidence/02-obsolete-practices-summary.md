The audit found that most of the sage's cost comes from its bookkeeping, not its engineering practices. In 9 recent sessions, turns that only touched the ledger, the lint, the sensor, the journal or the KI index took 18–54% of the parent's tool-turn time (4–16 min per run) and 16–54% of its output tokens (20k–130k). The review, refutation and briefing practices hold up on the evidence. The 12 cuts below would take roughly 9,900 of the ~20,500 run-loaded words out of the set (estimate).

The full inventory (about 90 practices) is at `/tmp/claude-0/-app-code-subagents-skill/490ef7e5-fac4-4973-aed3-a805887ce97f/scratchpad/obsolete/inventory.md`. The measuring scripts are in the same folder: `toolmix.py`, `bookcost.py`, `booktime.py`, `lintout.py`. I edited no file outside the scratchpad.

## Measured facts
- **Compaction never happened.** 0 compactions in 13 of 13 sage sessions on 1M-window parents; the parent peaked at 257k–589k against a rung of ~921k. The checkpoint rung never fired in real use. The one run that did compact (a58bd85c: 200k window, 15 compactions) never hosted the watchdog, and every unit report still arrived.
- **The lint mostly repeats itself mid-run.** It runs 5–41 times per run. Most mid-run output is the expected "section 'Run record' is missing" line: 12 of 12 lines in 54dd10c5, 13 of 19 in cf94c4c4.
- **The budget rail rarely fires and never changed an outcome.** Rail 4 fired twice in 42 ledgers, both times at unit scope in August. The whole-task rail never fired, even when a run hit 3.8× its estimate (61de7190). In 54dd10c5, unit 3a crossed its ceiling (281k against 240k) and nothing recorded it.
- **Estimates are loose.** Actual cost ran from 0.23× to 3.8× the estimate.
- **Report and resume are rarely used.** `/sage report` was used 0 times in 18 sessions; `/sage resume` once.
- **The acceptance-suite machinery is mostly idle.** Of 34 ledgers that record the choice, 28 chose `none` and 5 chose `light`. A blind suite author was dispatched once. The two-arm behavioural lens (#12) never ran.
- **Memory is mostly about the sage itself.** 81 of 129 journal `obs` lines are about the sage's own machinery.

## Ranked cuts (ranked by savings × confidence)
**1. Watchdog, occupancy sensor and checkpoint rung.** execute.md:17–33; SKILL.md:40–41, 65, 77, 112–116; dispatch.md:23, 140–146; harness.md:107–140; record.md:60–62, 71; sage-watch.sh run block. Class: BUREAUCRACY + HARNESS-NATIVE. The SessionStart(compact) hook already re-anchors after compaction, and background reports survive compaction.
- For keeping it: nothing from real runs. Its defects were found by reviewing the sensor itself (bc00ef0a).
- Against: see the compaction fact above.
- Change: move it out of the run-loaded set. Keep the hook and a minimal Resume state. Keep the script as an optional tool for measuring alt spend.
- About 2,300 words; per run, 3–20 calls, one Monitor task and every header restamp.
- Falsifier: a sage session that compacts and then loses its write lease or re-dispatches a unit.

**2. Lint at every bring-current point.** execute.md:11–13; SKILL.md:65, 77; verify.md:21–25. Class: BUREAUCRACY (the cadence, not the lint).
- For: its closure checks caught real gaps. c81599fd had a triage cell parked as "pending refutation by unit 4"; 056e20a8 and 61de7190 had orphan findings.
- Against: all of those are closure-time checks. execute.md:13 itself says the lint "reads legality, never liveness", so running it mid-run cannot enforce liveness either.
- Change: run it at Step 6 and before each commit only.
- About 350 words, and 4–35 calls per run (20k–47k characters of input).

**3. Ledger: 8 sections plus a restamp at every point.** dispatch.md:136–238; record.md:9–32. Class: OVER-SPECIFIED / BUREAUCRACY.
- For: Findings with triage, the decision rows (54dd10c5 D5, and the rail-1 authorisations D7–D9) and the baseline hashes are all read back.
- Against: the Plan and Unit tables duplicate each other. They need the lint's plan-unit and amend-tag checks to stay in sync, and those checks fired on cf35cb78 and cf94c4c4. The Assumption, Decisions and Open-questions tables are three of one kind. The run record re-renders the same file, and the header comment duplicates the hook.
- Change: 4 sections — one plan-and-units table, one Decisions table, Findings, and a 6-field run record. Write Resume state when a writer launches and at close only.
- About 1,000 words.

**4. Per-unit token estimates and the token budget rail.** SKILL.md:36, 88, 94–102; execute.md:35–45; dispatch.md:9–13, 163; alt-lane.md:31. Class: BUREAUCRACY. The user's `--max-budget-usd` and `maxTurns` are the real backstops.
- For: estimate misses are how the "ground truth first" lever was found. That lesson is already written into dispatch.md:33.
- Against: the budget-rail facts above. The texts also contradict each other: SKILL.md:92 says a firing rail ends the turn, while execute.md:37 says only that nothing new launches against that row. Under SKILL.md's reading, 54dd10c5 would have stopped before round 2 found the webhook-leak blocker (R2-01). 5 of the 12 shared KIs and all 9 band KIs exist only to calibrate these estimates.
- Change: delete the Est column, the token rail and the pricing prose. Keep the agent-count ceiling, plus one line: "surface a unit that ran far past what you expected".
- About 1,050 words.

**5. Memory read at Step 2.** memory.md (1,254 words); SKILL.md:53. Class: OVER-SPECIFIED.
- For: local domain lessons do get used (grep the symbol not the line number, zsh `path` clobbers PATH, a git recency check must name the ref).
- Against: the shared KIs restate rules already in verify.md and dispatch.md, so a "hit" on them measures nothing. 54dd10c5 and c81599fd read no KI at all. 9832cdf3 spent 20 calls on the index and KIs.
- Change: read only the local lesson and defect entries that match the task. Move the mechanics to memory-contract.md.
- About 900 words.

**6. #12 blind behavioural lens and the #10 suite procedure.** topologies.md:60–83; verify.md:9; dispatch.md:21, 34, 79, 173. Class: OVER-SPECIFIED (wrong home).
- For: the one blind suite (ff95b189) raised one real question.
- Against: #12 only triggers on edits to the sage's own corpus, which is maintainer work.
- Change: move both to a file read only when the case applies; leave a 1-line pointer.
- About 1,150 words.

**7. Spine restatements and rules with three homes.** SKILL.md:45–79, 120–137; the review-loop rule, stated in verify.md:20, 27–29 and topologies.md:29–34. Class: OVER-SPECIFIED.
- SKILL.md:12 already says nothing in the spine is at full strength. promote-pass-7 cut five second homes and passed its gate in one round.
- For contrast, the Codex sage's SKILL.md is 515 words.
- About 900 words.

**8. Restated harness behaviour.** execute.md:5, 7; harness.md:16–19, 32, 37–48, 91–105, 147, 155; alt-lane.md:11. Class: HARNESS-NATIVE.
- The Agent tool description in 2.1.284 already says to batch agents, run them in the background, and never fabricate a pending result.
- `sage-alt-guard.sh` already enforces "no `model` parameter" on alt dispatches.
- About 850 words.

**9. Tier, model and effort ritual.** dispatch.md:20, 38, 171; harness.md:50–81; alt-lane.md:15–21. Class: OVER-SPECIFIED.
- There are two tiers, and the agent files already bind model and effort.
- The env-var check came back "unset" every time it ran.
- 54dd10c5 wrote "—" in the Effort column, against the rule, with no effect.
- Change: a 4-line lineup. About 650 words.

**10. Calibration tags, build strings, anecdotes, grep trivia.** 25 tags and 14 version strings, for example dispatch.md:35 (GNU grep vs ugrep), dispatch.md:41 (hook scratch copies) and record.md:46 (Artifact URL). Class: BUREAUCRACY.
- No ledger records a tag deciding anything.
- Change: move them to harness-measurements.md or to KIs, which keeps the reason behind each rule off the run path.
- About 550 words.

**11. Failure ladder.** execute.md:10 (350 words). Class: MODEL-NATIVE (a hypothesis).
- The rungs are named in 2 of 42 ledgers.
- The clause that paid, "the same signature twice means reopen the plan", already lives at SKILL.md:106 (54dd10c5 D5).
- Change: 2 sentences. About 280 words.
- Falsifier: after the cut, a run steers an agent that failed on a wrong brief, and the retry fails the same way.

**12. Topologies #1–#9 prose.** topologies.md:5–58. Class: OVER-SPECIFIED.
- Change: a table of name and when to use it, plus the one non-obvious rule each carries. About 600 words.
- Lower confidence: plans cite this menu.

## Five practices that must stay
1. **An adversarial pass at the parent's own fixes and claims** (verify.md:14–16). 18 journal lines confirm it. In cf94c4c4 all 10 refuted items were the parent's own. In 54dd10c5 it found R2-01 after the parent thought the issue was closed. In d6ca31ad it caught a wrong safety knob that six same-family lenses had passed.
2. **Disjoint review lenses** (verify.md:11). In 87b40637, 15 of 17 findings came from a single lens. In 5f8bfa2d the lenses' findings did not overlap at all. In cc4a3413 only the Standards lens found the major.
3. **Settle with a command; treat a reader's claim as a lead; grep before asserting** (verify.md:18; dispatch.md:35–36). On 08-25 one git grep inverted a security finding. In 42dd56d4 a reader's 26 was really 13. In cf94c4c4 an `ls` loop caught a wrong path.
4. **Put the ground truth in the brief and forbid re-deriving it** (dispatch.md:15, 33). Runs came in at 25% (21c23a0e) and 62% (cf35cb78) of estimate. e4bebf20 came in at 140% where the same-shape run hit 380%. In a58bd85c, where re-derivation was allowed, units ran 2.1–2.3× over.
5. **Loop until dry with a narrowed mandate, and reopen after the same failure twice** (verify.md:20; SKILL.md:106). In e4bebf20 each of the 4 rounds caught the previous round's fix. In 5f8bfa2d 6 of 9 findings were in the parent's own fixes.

These should also stay, in shorter form: rail 1 and the snapshot baseline, the alt-lane probe and transcript model check, and tool scoping for reviewers that hold Bash (54dd10c5 D6).

## Estimates and opinions
- **Estimate:** cuts 1–5 would remove half to two-thirds of the bookkeeping turns. That is about 10–30% of parent output tokens and 3–10 minutes per run. Not measured.
- **Opinion:** the estimate and memory loops mostly feed each other. The journal calibrates estimates whose only consumer is a rail that does not bind.
- **Hypothesis (untested):** the Workflow tool could hold the unit state and resume for fixed topologies (#1 and #2). It needs the user to opt in and a trial run.
- **Not yet tested:** items 9, 11 and 12 rest on how Opus 5.5 behaves, which nobody has measured on these tasks. Before landing them, run the corpus's own #12 control-versus-change test on one or two past tasks.
