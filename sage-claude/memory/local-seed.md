<!-- sage-local-memory v1 -->
# Sage local memory

Your job here: read Bands and Rules at Step 2 before writing a budget, and append one Run-log row at Step 6 — every run, **hits included**, because a band you can trust needs its hits recorded next to its misses. This file holds this machine's numbers. The portable rules live in `shared.md`; skill text cites a strength band; every count and date behind that band lives here, so a new confirmation re-dates one file rather than two.

Seeded once by the installer and never overwritten. Entries marked **(seed)** shipped with the skill: real runs, from the author's machine, not this one. Untagged entries are this machine's actuals and **outrank them**. Consolidation rewrites this file automatically between runs under two checks that must both pass, and moves originals verbatim into `local-archive.md` beside it — `../references/memory.md`, Consolidate.

The sentinel above, the section order below, and every table header below are **structural invariants**. `../references/memory.md`, Structural invariants, declares them; the consolidation pass aborts and writes nothing rather than produce a file that breaks one.

## Harness version stamp

<!-- Consolidation must carry the `sage-harness-stamp:` line below through unchanged, on one line, still matching ^sage-harness-stamp:. The version-bound consolidation trigger compares against it, so a rewrite that drops or reflows it disarms that trigger with nothing to show for it. The installer checks a different anchor — the `sage-local-memory` sentinel on line 1 — which consolidation must carry through verbatim for the same reason. -->

sage-harness-stamp: unset | verified unset

Set it on the first run: the Claude Code version this machine's harness facts were verified against, then the date. Shape once set: `sage-harness-stamp: 2.1.229 | verified 2026-08-17`. A version-bound claim anywhere in this file older than this stamp is a consolidation trigger.

## Bands

Quote these at Step 2. Cost figures are machine-specific by nature; the part of a band that travels is a ratio or a shape, and it lives in `shared.md`, not here.

| Class | Figure | Qualifiers | Evidence |
| --- | --- | --- | --- |
| Any single agent, all classes | p50 133k, p90 498k, p99 3.0M | the whole local distribution, so it prices nothing on its own — it is what the 150k per-unit budget floor sits just above, and what makes a fixed absolute threshold useless across unit sizes | 204 done of 212 agent transcripts (`subagents/agent-*.jsonl`, non-recursive, `wf_*` excluded), 2026-08-18 |
| Frontier review lens, prose corpus ≤10k words | 50–95k per agent | cost tracks the corpus the reviewer must hold, not the size of the change; a blank-context critique lands in the same band | 3 runs, last 2026-08-06 (seed) |
| Web research, brief must find its sources | 70–120k per agent | multi-question briefs sit at the top; valid only for briefs that must discover their sources | 3 runs, last 2026-08-06 (seed) |
| Web research, brief names its target URLs | 14–34k per agent | the fetch-heavy band above does not apply | 1 run (2 agents), 2026-08-06 (seed) |
| Completeness critic over a large corpus | ~170k over ~25k words | cost tracks the corpus ingested, not the number of drafts reviewed | 1 run, 2026-08-04 (seed) |
| Dispatch floor | scoped agent ~5k; general-purpose ~16k | absolute numbers are machine-specific because they include this machine's always-loaded files; the ~3× ratio is the portable half and lives in `shared.md` | 1 run, 2026-08-05 (seed) |

Uncovered classes — say so in the plan rather than implying the figure has evidence: implementation units that write real code, migrations, worktree-isolated writers, any substantial `haiku` run.

## Rules

The arithmetic behind every rule in `shared.md`. `Rule` matches that file's `##` heading exactly — that name match is what makes the promotion and retirement triggers machine-checkable. `Class` is `portable` (would hold on any machine) or `local` (this machine's measured behavior). `Promoted` records where the rule was written and when; `—` means it lives only here.

| Rule | Count | First → last | Provenance | Class | Promoted |
| --- | --- | --- | --- | --- | --- |
| Point one adversarial pass at your own fixes | 10 | 2026-08-06 → 2026-08-16 | seed + author's log | portable | shared 2026-08-17 |
| Review and verify are one price | 8 | 2026-08-05 → 2026-08-16 | author's log (seed) | portable | shared 2026-08-17 |
| Estimate from the corpus and the lenses | 7 | 2026-08-04 → 2026-08-16 | seed + author's log | portable | shared 2026-08-17 |
| Disjoint mandates produce disjoint find-sets | 6 | 2026-08-12 → 2026-08-16 | author's log (seed) | portable | shared 2026-08-17 |
| A brief that names its ground truth runs cheaper | 5 | 2026-08-05 → 2026-08-12 | seed + author's log | portable | shared 2026-08-17 |
| Settle a disagreement with a command | 4 | 2026-08-06 → 2026-08-16 | seed + author's log | portable | shared 2026-08-17 |
| Price off a same-shape row | 3 | 2026-08-15 → 2026-08-16 | author's log (seed) | portable | shared 2026-08-17 |
| A checklist prices a lens only when every item settles in one look | 3 | 2026-08-11 → 2026-08-12 | author's log (seed) | portable | shared 2026-08-17 |
| A reader's structural claim is a lead | 3 | 2026-08-06 → 2026-08-16 | seed + author's log | portable | shared 2026-08-17 |
| When the target is a range, never report a mean | 3 | 2026-08-07 | author's log (seed) | portable | shared 2026-08-17 |
| A scoped agent boots ~3× cheaper | 1 | 2026-08-05 | seed | portable | shared 2026-08-17 |

## Watch list

Lessons seen once, contradictions against a `shared.md` rule, skill defects, and task classes with no coverage. `Kind` is `lesson`, `contradiction`, `defect` or `gap`. `Contradicts` names the `shared.md` rule a local run cut against, or `—`. A `contradiction` row does not overturn the rule it names; it needs its own confirmations and surfaces in the next hint as a **retirement candidate**.

| Observation | Kind | Count | First → last | Contradicts | Status |
| --- | --- | --- | --- | --- | --- |
| A subagent's transcript is observable: every dispatch returns an `output_file` holding that unit's full JSONL, so grepping it measures what the agent invoked rather than what it reported. One run converted six case verdicts from judged to measured that way. **(seed)** | lesson | 1 | 2026-08-16 | — | watching |
| A projection built from band midpoints is an upper bound, not a forecast — say which kind of figure you are holding up when a rail stops the run, or headroom gets authorised that the run never needed. **(seed)** | lesson | 1 | 2026-08-16 | — | watching |
| The watchdog's false-positive rate is unmeasured. Grant it no autonomous action beyond a `SendMessage` until ten runs of evidence sit in the Run log below. | gap | 0 | 2026-08-17 | — | watching |
| The 4× budget multiplier may be consumed rather than used: on this machine every past ceiling raise was spent up to the new ceiling. Retire it if ten runs land near 4× with coordination checks naming nothing the spend bought. | gap | 0 | 2026-08-17 | — | watching |
| Running unattended is unmeasured against running with a human approving the plan first: no logged row anywhere records an approval answer, a requested change, or a reversed call. The assumption log is the instrument — read the rows the user corrects. | gap | 0 | 2026-08-17 | — | watching |

## Run log

Append one row here, at the very end of the file, every run. Recent rows stay in full; a fully consolidated row compresses to one line with a pointer into `local-archive.md`. Seed rows below are already compressed to their lesson. Their full original text is at `subagents-claude/calibration.md` inside the source repo — resolve that repo with `readlink shared.md` beside this file, since a repo-relative path means nothing from the installed tree — and that is where a provenance grep goes until this machine's first archive exists. A dangling symlink → the note text below is the whole provenance. If a full row and the Bands or Rules ever disagree, the Bands and Rules are the consolidated reading: treat the mismatch as structural damage, a consolidation trigger.

| date | task class | agents | est | actual | wall clock | note |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-08-04 | web research sweep, agents fetching primary sources **(seed)** | 5 | 225k | 451k | ~25 min | Off by 2–3×. Fetch-heavy web research runs 70–120k per agent, not the 15–40k exploration band. |
| 2026-08-04 | completeness critic over ~25k words of notes plus 4 skill files **(seed)** | 1 | 35k | 172k | ~10 min | Off by 5×. A critic's cost tracks the corpus it must read, not the number of drafts it reviews. |
| 2026-08-05 | 2 reviewers on a small prose diff against a written spec **(seed)** | 2 | 120k | 193k | ~7 min | Off by 1.6× on a *small* diff — the reviewers still held a 6.6k-word skill plus a 2.8k-word spec. |
| 2026-08-05 | no-op boot probes, haiku **(seed)** | 2 | 15k | 21k | <1 min | Dispatch floor measured: scoped agent 4,962; general-purpose 16,036. The ~3× ratio is the portable half. |
| 2026-08-05 | 45-item review across 8 skill files: 1 inline writer, 2 verifiers on a frozen set **(seed)** | 2 | 140–200k | 161k (68k + 93k) | ~5 min | **Estimate held** — first hit on the review band. Coordination check paid partially: the two lenses returned disjoint findings, but the run's worst defect surfaced only from *running* the installer, which no diff reader could see. |
| 2026-08-06 | review and optimise a skill: 2 web researchers, 1 docs fact-check, 1 blind critic, then 2 verifiers on the frozen diff **(seed)** | 6 | 470k | 401k | ~35 min | Brief style, not task class, sets web-research cost: URL-named briefs came back at 13.7k and 33.7k against a 70–120k open-ended band. A sonnet refuter against opus-authored prose killed 4 claims, 3 of them defects introduced during the fix round. |
