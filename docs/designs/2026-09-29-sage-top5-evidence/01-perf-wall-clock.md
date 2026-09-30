# Wall-clock study (agent summary, saved by the parent; the harness blocked the agent's file write)
Scripts and raw data: analyze.py, results.txt, results.json, subagents.txt, phases.md, loopsplit.txt, table.md.
Run window: /sage call → end of the turn that appends the journal or stops the watchdog. Phases: P1 start→first dispatch; P2 →first round-1 report; P3 →last report; P4 close. Gen speed fit: 8.7–13 ms/token + 2–9 s/call. Hidden time = (out tokens − visible chars/4) × ms/token (estimate).

| session | model / effort | wall | parent gen (no agent running) | idle on agents | compaction | stall+human | P3 loop | review rounds | bookkeeping gen (share of out) |
|---|---|---|---|---|---|---|---|---|---|
| a58bd85c | opus-5 / high | 215 | 51 (33) | 100 | 39 | 0 | 134 | 5 | 10.7 (21%) |
| 61de7190 | fable-5.1 / medium | 143 | 31 (21) | 102 | 0 | 5 | 119 | 3 | 9.3 (33%) |
| e4bebf20 | opus-5 / xhigh | 101 | 58 (42) | 29 | 0 | 0 | 68 | 5 | 14.6 (25%) |
| 54dd10c5 | opus-5.5 / high | 120 | 51 (41) | 23 | 0 | 32 | 28 | 3 | 5.7 (11%) |
| d4096102 | fable-5.1 / high | 84 | 60 (53) | 20 | 0 | 0 | 30 | 3 | 11.7 (17%) |
| 9832cdf3 | opus-5.5 / xhigh | 29 | 20 (17) | 7 | 0 | 0 | 8 | 2 | 4.8 (25%) |
| c81599fd | opus-5 / xhigh | 30 | 21 (9) | 2 | 0 | 0 | 0 | 2 | 5.8 (27%) |

Ranked sinks (five slow runs, 664 min):
1. Serial review/fix rounds (P3): 380 min, 57%. Idle on post-round-1 reviews 85 min; round 1 45 min. e4bebf20 P3 = 40/68 min parent generation (inline triage+fix between 5 review groups). a58bd85c 5 review groups + 5 re-verdict steers. Cause: verify.md:20 loop-until-dry with re-freeze; SKILL.md:39 review depth; dispatch.md:13; verify.md:14 separate refuter. Change: fix-verification + refuter as one parallel batch on one freeze; after round 1 at most 2 more rounds, round 3 only if the previous found a blocker; cap reached without dry → Awaiting human. Saving E 15–45 min. Risk: e4bebf20 each round caught the previous fix.
2. Waiting on fix writers: 133 min, 20%. a58bd85c 75 min (two implementers 40 and 53 min; 57/65 tool minutes dotnet build/test; >20 test calls in a row at 1.1–2.7 min each; 10 min parent blocked on TaskOutput). 61de7190 68 min (one writer, 63 findings, 429, resume, 233 API calls). Change: one build + one filtered test run per fix group; split >~20 findings across two worktree writers with disjoint files; fix inline when <~5. Saving E 20–35 min.
3. Parent generation with no agent running: 191 min, 29% (~141 min hidden tokens, E). Hidden 54–88% of parent output. 54dd10c5 1,601 thinking tokens/call (3–5× others); 175k of 194k thinking in P1 where the parent diagnosed and fixed inline (75 min). d4096102 parent rewrite 46 min of P1. Hidden-time per run: a58bd85c 29, 61de7190 14, e4bebf20 29, 54dd10c5 42, d4096102 27, 9832cdf3 11, c81599fd 14 min. Change: parent row >~40% of plan → implementer row; record parent effort. Saving E 15–25 min. Risk high (coupled work).
4. Bookkeeping generation: 52 min, 8% of slow-run wall (18% in fast runs); 216k tokens, 19% of output. Ledger rewrites 43 of 52 min — hand-written python replace heredocs of 1–13k chars. Skill-file reads 3.9, journal 2.5, watchdog 2.1, lint 1.1. P4 close 3–4 min generation every run, 48–66% bookkeeping. Change: `sage-ledger.sh` helper (unit, finding, restamp, close); restamp at wave boundaries only. Saving E 5–7 min slow, ~3 min fast.
5. Watchdog: ~2 min gen/run, 0 events in 7/7. Peak occupancy 350–595k on 1M runs. a58bd85c (200k) compacted 15× (40 min); watchdog prevented none (first started with a wrong flag). Change: host only when SAGE_WINDOW ≤ 400k.
6. Harness stalls: 78 min, 12%, not skill-caused (compaction 40 min a58bd85c; 54dd10c5 dropped response 13 min + 19 min until user typed "resume"; 61de7190 rate limit 5 min).
Unmeasured: thinking time per work type; quality effect of a round cap or lower effort; subagent API queueing.
