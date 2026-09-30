# Quality-ceiling study (agent summary, saved by the parent; the harness blocked the agent's own file write)

F = fact counted by a command; E = estimate; O = opinion. Classifiers are regex-based; nothing is a controlled comparison. Scripts: sections2.py, briefs.py, usermsgs.py, tooluse2.py, findings.py, topo.py; per-agent tally in tooluse2.txt.

## Late-find classes (F, 17 late finds across 15 ledgers + journal)
1. Parent-authored orchestration text. `confirm point-one-adversarial-pass-at-your-own-fixes` = 18 journal confirms (most of any KI). cf94c4c4: 10 refuter majors, all in parent text, 6 in fixes. 21c23a0e F1: parent re-created a second home right after its one-home grep. cc4a3413: Result said "live from next session" — wrong, corrected after close.
2. Behaviour no reader can see. Seed run installer defect; bc00ef0a D1 rung fires 5/16 segments (found only by transcript replay); 54dd10c5 secret leak survived two sanitising fixes.
3. Framing (premise, scope, purpose, hypothesis): 7 of 17. a58bd85c G1 every criterion passed but purpose unmet; cf35cb78 wrong hypothesis briefed as ground truth; 61de7190 wrong corpus scope; c81599fd wrong premise; 42dd56d4 user: "I was surprise it doesn't have these suggestions" (session 92232e44).
4. Never run in the real environment: standing Gap in 54dd10c5, a58bd85c, d4096102, 9832cdf3, 61de7190, 056e20a8.
O: sage is strong at adversarial reading after the artifact exists; weak before it exists and at execution.

## Supporting facts (F)
- 63 checker units: 1,557 read calls vs 42 test/build commands (mostly in 2 sessions). 9/61 review units ran zero behavioural commands. Blocker/major evidence: ~45 executed, 44 read, 47 unclear.
- 42 ledgers: bake-off #4 never; #12 never; acceptance `full` never; blind author 3 dispatches, none since 08-24; plan critic #11 2 runs (08-18), both refuted the design before code; unused since.
- Parent held the pen in 8 of last 10 writing runs; topologies.md #10 "When: the plan carries a writer unit" then disqualifies the suite; 6 runs cite it.
- No framing step (SKILL.md:47 "The invocation settled…"); Plan field `TASK: <one line>` (dispatch.md:151). Loss of the verbatim goal found in bc00ef0a (B3), never fixed.
- Leash: verifier.md:84 "a silent brief is a denial"; diff-review caps reports at 400 words; round 2+ blocker/major only; e4bebf20 lens A "named two discriminating commands it was forbidden to run"; 54dd10c5 Standards reader went past its brief with -race runs and found a blocker (281k).
- Checker diversity: zero alt reviews of a plan or criteria; one refuter per claim (topology #6 says 2–3); alt checkers 6.6 behavioural commands/unit vs 10.9 in-family; no cross-family maker ever.
- Six quality lessons (purpose, scope-first, withhold diagnosis, refuter-after-evidence, vary the sample, mechanism-first) are count 1, uses 0, not in run-loaded text. E: ~10.7k of 20k run-loaded words are mechanics.

## Ranked changes
1. Framing gate before Step 2: Plan fields ASK (verbatim), PURPOSE, PREMISES (each with a testing command), DELIVERABLE, APPROACHES (≥2). Test premises before briefing. Medium+ risk: one framing critic (refuter-alt where cleared) refutes that plan + criteria answer the ask; never sees parent reasoning; ≥1 criterion at the PURPOSE surface. #11 default at medium+. Lint: missing ASK; RISK below high while text names a hard trigger (54dd10c5 marked a credential leak "medium"). Optional knob `Up-front question: off|once`, ≤3 questions, only for decomposition-changing ambiguity. Cost E 30–60k, 5–10 min. Test: `stage` column in Findings; share of blocker/major found at r2+ over next 10 runs.
2. Executable acceptance first, whoever writes: delete the writer-unit disqualifier in #10; `full` default where tests run; reproduce-first (failing test on baseline before any edit); mutation check (revert each blocker/major fix, confirm its test fails); hostile-input table tests for security/parsing/redaction written before the fix. Cost E author 25–55k, compile 50–100k, +10–20 min parallel. Test: replay 54dd10c5 from baseline c13301b, ≥3 samples/arm; fix attempts per blocker; MEASURED:JUDGED ratio.
3. Parent stops writing code by default: "Phases of one deliverable belong to one dispatched owner"; code → implementer (frontier, effort high, worktree) owning repro→fix→tests. Parent keeps frame, criteria, suite, triage, integration; keeps the pen only for whole-corpus prose edits, reason recorded. Cost E +100–250k per writer run. Test: `author` column in Findings.
4. Final end-to-end run in the real environment before the completion claim (installed copy, first dispatch of a new agent, live query, real binary; sandbox HOME or read-only; never rail 1). If impossible, the Result's first caveat names the settling command; unprobed runtime claims are JUDGED. Cost E 2–100k.
5. Bake-off on a same-signature failure: two fresh owners in separate worktrees, one cross-family (alt implementer or codex:codex-rescue), suite as judge. Hard-trigger unit may start as a bake-off. Cost E +100–200k + 30–50k judge, only when triggered.
6. Aim checker diversity earlier and unleash execution: two independent refuters of different families on the load-bearing claim; verifier/alt files: "where a command would settle a finding, run it in your scratch path or worktree, or name it as a blocked check — never argue it"; Spec verdict names the deciding command or says `judged`; refuters launch after evidence lands; bound cost with maxTurns.
7. Make room: move watchdog/telemetry/alt-measurement procedure out; promote the six count-1 quality lessons into verify.md/decompose.md.

## Validation (O)
Replay three tasks with known escapes, blind, 3–5 samples per arm, old vs new rules: 54dd10c5 (code), 42dd56d4 (study), d4096102 (corpus compression). Count whether each known escape is caught before round 2.
