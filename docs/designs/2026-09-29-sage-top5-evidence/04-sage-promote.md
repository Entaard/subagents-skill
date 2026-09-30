# /sage-promote study (agent summary, saved by the parent; the harness blocked the agent's file write)
Data: ki-table.tsv (frontmatter of 108 local KIs), annotated-hits.txt (83 hit citations with notes), traces/*.txt (passes 3–7), stages.py + stagecost.py (cost split), stale-2026-12-20.txt.
F = measured, E = estimate, O = opinion.

## Facts
- 7 passes minted ONE shared rule that still stands; stage two landed ONE band tag; eviction and quarantine fired ZERO times.
- Promotion commits ≈ 7% of churn in run-loaded text (123 of ~1,744 changed lines since 6cf3b7b); large edits came from user-asked builds (77695ae, fdb3e0d).
- 74 of 95 non-sidecar local KIs never used (`last-used: —`; parent re-counted): 43/56 lessons, 23/23 defects, 4/5 gaps; 49 lessons at count 1. 42 KIs created since 09-01, 34 unused. ~7 KIs minted per pass.
- 234 use citations: 209 hit, 23 miss, over only 36 distinct KIs. Bands: 15 hit, 11 miss. 11 of 12 shared rules already stand in run-loaded text with a calibration tag (e.g. verify.md:14, :18, dispatch.md:36).
- E (hand-classified 83 annotated hits): 20 show a changed decision (same-shape run rows ×8, cost bands ×6, a few lessons); 51 re-cite practices the skill text already states.
- 54dd10c5 (3.5 h) did no Step 2 memory read and wrote no use line, and landed at 0.99 of its estimate.
- E cost split passes 3–7 ($116): stage three 41% ($48), stage zero 21%, wrap-up 12%, consolidation 9%, preflight 5%, stage one 5%, stage two 4%, KI review 2%. ~25% (~$28) went to text the gate refuted or to gate rounds on fixes; pass 3 rounds 2–4 ≈ $12.
- Consolidation is a throwaway 7–21k-char Python script each pass; pass-4 drain nearly lost three pricing rows. The "one-time" reconciliation keeps running (45 KIs reconciled after 08-28; new mints carry no `reconciled:` field).
- Stage three: 3 real lineup events in 7 passes (Fable 5.1, gpt-6-astra, Opus 5.5), all cheaply visible (probe $0.02–0.15; changelog named Opus 5.5; conf is the user's file). Pass 5 found no change and spent $7.14 (55%) on stage three. Its prose goes to harness-measurements.md and a 4,417-word stamp that "no other stage and no run reads" (SKILL.md:226, :130). Write-ups refuted in passes 2, 4, 6, 7. Build moves ~daily (2.1.250 → 2.1.284 in 32 days), so the build-based lineup hint fires nearly every run.
- 23 defect KIs; ~half about memory/promote machinery (7 from v2→v3 migration, 5 promote faults). The pass may never edit its own SKILL.md (SKILL.md:31, :147); one escalation stayed open 09-03 → 09-16; fixes needed separate /sage runs 21c23a0e ($14) and part of 9832cdf3 ($30). Repo convention is GitHub Issues (CLAUDE.md).

## Correctness defects (agent-verified; parent re-checked a and c)
a. sage-promote SKILL.md:214 cites a cell-rule line removed at the v3 rewrite (stood at 8b6bc24:169; removed 6cf3b7b).
b. Class check (SKILL.md:86, no dates in skill text) contradicts the date stage three re-stamps into harness.md:3 every pass; two sessions stamping at once caused merge b10bab2.
c. SKILL.md:25 and :233 require byte-identical landing in ~/.claude/agents/; alt agents are `.md.in` templates the installer renders, and the glob `claude-agents*/*.md` misses them.
d. The one-home grep (SKILL.md:79–80) leaves out the four *-alt agents, including the MODEL-FAMILY rule at refuter-alt.md.in:29–36.
e. The stale notice walks closed KIs: on 2026-12-20 it prints 102 lines incl. 23 settled/dropped defects; SKILL.md:177 forbids trimming it.
f. lesson-alt-lane-notification-counter-reads-zero re-qualifies every pass (refused 08-28; same-lane confirms move `last` past that date, which SKILL.md:157 compares); its rule already stands at alt-lane.md:31.
g. Journal grammar has no correction type; journal.md:34 and :36 (cc4a3413) contradict each other; :29 (9832cdf3) same subject.
h. Run-line grammar in the journal header (journal.md:7) and the seed lacks the five sensor fields memory.md:26 requires; the drain rewrites the header verbatim.
Open in memory (from 9832cdf3): harness-stamp.md still says "explorer haiku"; a gap KI names a "haiku run" class; spot-check defect still "not acted on" though archived 09-23; `NO SUCH SHARED KI` tag after 12-16.

## Ranked improvements (O)
1. Replace KI tracking with one curated lessons file + a run log never drained: runs.log (run lines), inbox.log (obs lines), lessons.md in the repo synced to the clone, ~1,500-word cap, one bullet per lesson/band (rule, recogniser, falsifier, run ids). Delete sidecars, band field, status flips, promoted histories, cell rule, reconciliation, stale notice, drain marks, archive segments. Gain E: ~30% of pass spend; skill 11.8k → 2–3k words.
2. Stage three → scripted lineup-change check (bin/sage-lineup-check.sh): diff accepted Agent model values, `claude --version` + model-name grep over the changelog, agent-file and alt-conf `model:` lines, recorded price ratio. Only a non-empty diff triggers probes, one pricing fetch and a gated snapshot-table edit. One-line stamp; hint on "diff non-empty". Optional monthly pricing fetch. Gain E: no-change stage three $5–11 → <$1.
3. Step 2 read prices the plan: `grep -iE '<task-class words>' runs.log | tail -5`, then lessons.md whole (~2k tokens). Replace the use line with optional `changed-by: <lesson> <how>` on the run line. (c81599fd priced off bands because it read rows too late; 61de7190 under-priced 3.8× with no same-shape row in the newest-three window; KI index ≈ 7k tokens incl. 23 closed defects.)
4. Corpus defects → GitHub Issues (`gh issue create -l sage-corpus`); allow the pass to edit its own text on the user's word under the same cross-family gate (gate caught ~14 real errors in ~20 checker dispatches).
5. Fix defects a–h and the open memory items.

## Target shape (O)
Run Step 2: grep runs.log for same-shape rows, read lessons.md. Step 6: one run line (optional changed-by:), obs lines to inbox.log. Pass: prep script prints inbox, lineup diff, lint/budget status → user triages each line (merge into lessons.md, open issue, fix corpus, drop with reason) → one cross-family refuter on the combined diff → lineup study only on a non-empty diff → print the diff; user commits. Target: no-change pass ~10 min, 1–2 agents, <$8. Keep: append-only run path, repo copy as source of truth, refuting gate, one-home grep with scope fixed. Codex promote: 636 words + a Python helper; skips any team when nothing to change.
