# Repair report — sage `memory/local.md` structural damage (2026-08-27)

**What this is.** A `/sage-promote` pass on 2026-08-27 aborted at preflight step 3 (structural
invariants) against `memory/local.md`. The protocol forbids the pass repairing the file it
validates against, so this report records every defect, every byte of data needed to repair them,
and the verification that proves the repair landed — self-contained, so an agent that has never
seen the damaged machine can perform or audit the fix. The repair itself is a **by-hand edit on
the user's word**, the same channel that fixed the 2026-08-19 Run-log damage (see the `defect`
watch row of that date). It is *not* a sage run and *not* a promote pass.

**Contract being repaired against:** `sage-claude/references/memory.md`, `## Structural
invariants` (identical in the repo and the installed tree — `diff -rq` proved them identical on
2026-08-27). **Worked example / fixture:** `sage-claude/memory/local-seed.md`, which is
v2-compliant by construction.

---

## 1. Target identification

| Fact | Value |
| --- | --- |
| File | `/root/.claude/skills/sage/memory/local.md` on the machine whose repo checkout is `/app/code/subagents-skill` (WSL2, Claude Code build 2.1.246 at snapshot time) |
| Baseline snapshot | 2026-08-27, 148 lines, 56,899 bytes, mtime 2026-08-27 17:18 |
| Baseline sha256 | `58fc373fa462fabed28c9d1cc348b11662da7a8d9b3950ea27707bb80df46ac6` |
| Line 1 (sentinel) | `<!-- sage-local-memory v1 -->` |
| Companion files | `memory/local-archive.md` exists (16,250 B, sentinel `sage-local-archive v1`); `memory/shared.md` is a symlink to `/app/code/subagents-skill/sage-claude/memory/shared.md` and is **healthy** — 11 blocks, all invariants pass. Do not touch it in this repair. |

**Line numbers below are valid only against the baseline sha256 above.** `local.md` is live:
every sage run appends one Run-log row at end-of-file, so the Run-log section grows. The Watch
list, by contrast, is currently **frozen** — the append guard blocks writes into a section whose
block count is not 1 — so the Watch-list content below will still be exact even after more runs.
If the sha no longer matches, anchor every edit by content (the file's own protocol,
`references/memory.md` `## The two files`, mandates content anchors over line numbers) and expect
only the Run log to have grown.

---

## 2. Defect inventory

All verified by command on 2026-08-27. The contract's markers are numbered as in
`references/memory.md` `## Structural invariants`.

### D1 — sentinel is v1, contract requires v2 (marker 1)

Line 1 reads `<!-- sage-local-memory v1 -->`. The contract requires exactly
`<!-- sage-local-memory v2 -->`. v2 (2026-08-20) added the `Class` and `Promoted` columns to the
Watch-list table; the sentinel must flip **only after** D2 is fixed, because the sentinel is a
claim about the format. The installer's `drift_memory_sentinel` function announces this drift on
every install but deliberately never edits the file ("it holds this machine's numbers").

### D2 — Watch-list table is the 6-column v1 form (marker 5)

Line 58 header: `| Observation | Kind | Count | First → last | Contradicts | Status |`.
Contract requires 8 columns:
`| Observation | Kind | Count | First → last | Contradicts | Class | Promoted | Status |`,
with `Class` and `Promoted` immediately before `Status`. Consequence while unfixed: no watch row
can ever evaluate the `→ shared.md` promotion trigger (it reads both missing columns), and every
consolidation pass and promote preflight aborts here.

### D3 — blank line splits the Watch-list table into two blocks (marker 5, "one table")

Line 78 is empty. It splits the section into a live 20-line block (lines 58–77: header,
separator, 18 data rows) and a **header-less** 6-row block (lines 79–84). Measured:
`awk` blocks/lines for `## Watch list` = `2 26`, must be `1 N`. This is the exact damage class
`references/memory.md` `## Append` describes ("a blank line ends a markdown table"). The
2026-08-26 run's ledger (D12 there) records that rows 79–84 were appended into the broken second
block by the 2026-08-24 and 2026-08-26 runs — the damage predates them.

### D4 — Run log fragmented into three table blocks (marker 6, "one table")

Measured: `awk` blocks/lines for `## Run log` = `3 55`, must be `1 N`. The section holds:

- Block 1, lines 89–111: the legitimate 7-column table (header, separator, 21 data rows,
  2026-08-04 → 2026-08-26).
- Line 112: `### 2026-08-19 — LoginCiTools CI failure investigation (tddmon / TDD CI Express)` —
  an illegal `###` subsection whose content is a `| field | value |` table (lines 114–125).
- Line 127: `### 2026-08-20 — AzureComputerVision flaky-fixture verdict (tddmon / TDD CI
  Express)` — same misfiled format (lines 129–142).
- Lines 143–148: six more rows **glued directly to the second field-table** (no blank line
  between 142 and 143), so they parse as a continuation of it. Four are legitimate 7-cell run
  rows (143: 2026-08-24, 144: 2026-08-25, 145: 2026-08-26, 148: 2026-08-27); two are not run
  rows at all — see D5.

The verbatim text of both `###` subsections is preserved in **Appendix A** of this report, so the
repair does not depend on the damaged file being the only copy.

### D5 — two Watch-list rows misfiled inside the Run log (markers 5+6)

Lines 146–147 are 6-cell watch-shaped rows (`| <observation> | lesson | 1 | 2026-08-27 →
2026-08-27 | — | open |`) sitting inside the Run-log section. Their `Status` value `open` is not
one of the four legal states (`watching` / `settled →` / `promoted →` / `dropped →`). They were
evidently appended by the 2026-08-27 run using the Run log's end-of-file anchor because the Watch
list was write-blocked (D3) — the exact anchor-confusion failure `## Append` warns about.
Verbatim text in **Appendix B**.

### D6 — four owed Watch-list rows parked outside the file (data debt, not structural)

The 2026-08-26 run could not write its four watch rows (blocked by D3/D2) and recorded them
verbatim in its ledger, which lives at `/tmp/ledger.damaged.md` on the damaged machine —
**volatile storage**. The ledger's own instruction: "`/sage-promote` should transcribe these
after it migrates `memory/local.md` from v1 to v2." Their full content, already normalized to the
8-column v2 shape, is embedded in the replacement table in §4 (rows 27–30) and the ledger
original is quoted in **Appendix C**.

### Not defects, but adjacent facts a repairer must know

- The **harness stamp** (line 14, `sage-harness-stamp: 2.1.235 | verified 2026-08-19`) is stale
  against build 2.1.246. **Do not touch it in this repair** — re-dating it is `/sage-promote`
  stage three's write, with its own read-back rule.
- Watch rows at baseline lines 79 and 80 are `defect` rows that *record* this very damage (the
  v1/v2 drift; the old 40-row consolidation trigger). **Do not close them in this repair** —
  closure is `/sage-promote` stage zero's act, with its own evidence rule. Leave both `watching`;
  the next promote pass will verify and settle them. (Note for that pass: the 40-row-trigger
  defect appears already repaired in the contract — `references/memory.md` `## The hint` now
  carries the movable-rows ≥ 10 trigger with the 2026-08-25 measurement — so row 80 is likely a
  `settled → references/memory.md ## The hint` closure, and row 79 settles against this repair.)
- The Rules table (lines 40–52) and Bands table (lines 22–32) are **healthy** — headers match the
  contract exactly. Do not edit them.

---

## 3. Repair procedure (ordered — the order is load-bearing)

1. **R1 — Replace the whole Watch-list table** (baseline lines 58–84, including the blank line
   78) with the ready-to-paste v2 table in §4. This fixes D2 + D3 + D6 in one edit and absorbs
   D5's two rows. It is a pure superset of the current content: all 24 existing rows verbatim
   with two cells inserted, plus the 2 relocated rows (D5) and 4 owed rows (D6). No row is
   dropped, reworded, or re-counted.
2. **R2 — Delete lines 146–147** from the Run log (their content now lives in the §4 table, rows
   25–26, with `open` corrected to `watching`).
3. **R3 — Repair the Run log**: delete the two `###` subsections wholesale (baseline lines
   112–142, including the blank lines around the headings), append the two verbatim originals to
   `memory/local-archive.md` under the heading given in §5, and insert the two 7-column
   replacement rows from §5 into the main table **immediately after the 2026-08-26 row that ends
   block 1** (baseline line 111), keeping rows 143/144/145/148 (and any rows appended since the
   snapshot) after them, all in one contiguous table. Ensure no blank line remains anywhere
   between the header (line 89) and the last data row.
4. **R4 (recommended, optional)** — Replace the Watch-list section's intro paragraph (baseline
   line 56) with the seed's v2 paragraph (§6), which documents the two new columns. The invariant
   check only reads the header row, so this is documentation hygiene, not a marker.
5. **R5 — Flip the sentinel**: line 1 becomes `<!-- sage-local-memory v2 -->`. Last, because the
   sentinel asserts the format now holds.
6. **R6 — Ensure the file ends with exactly one newline** (the 2026-08-19 append-corruption row
   names this as the standing hazard).
7. **R7 — Run the verification suite** (§7). Every check must pass before the repair is claimed.

Do **not**: touch `shared.md`, `local-seed.md`, the Bands or Rules tables, the harness stamp, any
`Status` cell of an existing row (beyond `open` → `watching` for the two D5 rows), or any
`Count` / `First → last` cell.

---

## 4. Ready-to-paste replacement: `## Watch list` table (v2, 30 data rows)

Rows 1–18 are baseline lines 60–77 verbatim + inserted `Class`/`Promoted` cells. Rows 19–24 are
baseline lines 79–84 (the orphaned block) likewise. Rows 25–26 are the D5 rows relocated
(`open` → `watching`). Rows 27–30 are the D6 owed rows, transcribed from the 2026-08-26 ledger
with the column values its parking note specified (Count 1, `2026-08-26 → 2026-08-26`,
Contradicts `—`, Promoted `—`, Status `watching`, Kind and Class as it named per row).

`Class` values for rows 1–26 are **proposed by the reporting agent, not measured**: `portable` =
would hold on any machine (method/protocol/model-family lessons, corpus defects); `local` = this
machine's measured numbers or this machine's file state. Rows 1–4 take the values the v2 seed
fixture assigns to the same/analogous observations. Rows flagged `(judgment)` below the table are
the genuinely arguable ones — a repairer who disagrees should change the cell, not drop the row.

| Observation | Kind | Count | First → last | Contradicts | Class | Promoted | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A subagent's transcript is observable: every dispatch returns an `output_file` holding that unit's full JSONL, so grepping it measures what the agent invoked rather than what it reported. One run converted six case verdicts from judged to measured that way. **(seed)** | lesson | 1 | 2026-08-16 | — | portable | — | watching |
| A projection built from band midpoints is an upper bound, not a forecast — say which kind of figure you are holding up when a rail stops the run, or headroom gets authorised that the run never needed. **(seed)** | lesson | 1 | 2026-08-16 | — | portable | — | watching |
| The 4× budget multiplier may be consumed rather than used: on this machine every past ceiling raise was spent up to the new ceiling. Retire it if ten runs land near 4× with coordination checks naming nothing the spend bought. | gap | 0 | 2026-08-17 | — | local | — | watching |
| Running unattended is unmeasured against running with a human approving the plan first: no logged row anywhere records an approval answer, a requested change, or a reversed call. The assumption log is the instrument — read the rows the user corrects. | gap | 0 | 2026-08-17 | — | portable | — | watching |
| The six per-unit watchdog rungs were measured rather than doubted: **0 true positives** across 193 subagent transcripts and 37 units in 4 real sage runs, under a 60s-cadence prefix simulator averaged over 4 phase offsets. Removing the 150k floor and fixing the key forms was worth **0.2 expected notifications** across those 4 runs. Replay a settled transcript as a **prefix series**, never as a whole: the whole-file method ignores the probe's `done` gate and overcounted idle alarms 6x. | lesson | 1 | 2026-08-18 | — | local | — | watching |
| Background general-purpose subagent, measured on this machine: HAS the Agent tool and a nested spawn succeeds (explorer child replied), but the visible toolset is reduced — no SendMessage, no Monitor, no Glob/Grep/Write (Bash/Edit/Read/Skill/ToolSearch present). Confirms harness.md's background-toolset caution as a measurement. Probe cost 19.6k (haiku), consistent with the ~16k general-purpose boot floor. | lesson | 1 | 2026-08-18 | — | local | — | watching |
| The alt lane's token spend reports as **zero** in the task-notification `subagent_tokens` counter, but is present in the transcript: three alt units returned 0 while their transcripts carried 3.3k / 7.3k / 8.7k deduplicated spend. Price an alt row from the transcript (or the watchdog's `--status` line, which agrees); a projection summed from notification figures under-reads a run that uses this lane to nothing. 2026-08-24: both alt units read 0 across five notifications while `--status` read 37k and 58k. | lesson | 4 | 2026-08-18 → 2026-08-24 | — | local | — | watching |
| The sidecar's optional `model` field records the **dispatch-time override**, not the effective model — present on exactly the 3 dispatches that passed a `model` parameter (carrying that parameter's value), absent on all 8 that did not, including alt agents whose frontmatter sets a model. Consequence: only `message.model` in the transcript can establish which model a unit ran on, and the sidecar can never establish an alt unit's model. n=3 on the present side. | lesson | 1 | 2026-08-18 | — | local | — | watching |
| Put one estimate above the 150k per-unit floor before reading anything into the watchdog's `est=` column. A fleet estimated at 5–12k displays `est=150k` on every row — the clamp working, indistinguishable from a key-match failure. A control row raised to 300k displayed 300k while its neighbour stayed at 150k, settling it with one command. | lesson | 2 | 2026-08-18 | — | portable | — | watching |
| Price a parent or successor unit by SPEND, never by occupancy: the gap measured 3.4x (868k spend vs 258k occupancy on one successor), and the occupancy convention halved a run's reported total. | lesson | 1 | 2026-08-18 | — | portable | — | watching |
| Widening a lease in the ledger satisfies rail 3 but does not make an unchanged acceptance criterion pass — report the deviation honestly (15 pass + 1 deviation, not 16 pass). | lesson | 1 | 2026-08-18 | — | portable | — | watching |
| A measurement can be structurally blind to the failure mode it is cited as disproving: a replay that stops at each child's final timestamp can never sample after an orphan's last record, so "0 dead-unit true positives" was evidence about units that finished. | lesson | 1 | 2026-08-18 | — | portable | — | watching |
| Subagent context window follows the subagent's own model (docs: model-config + context-windows pages, v2.1.235; local corpus: 53/202 transcripts exceeded 200k occupancy, max 415k on claude-opus-5). The Agent tool has no window knob; `[1m]` never appears in `message.model`, so window variants are transcript-invisible. `fable` is a live Agent-tool model value → `claude-fable-5` (probe-measured). | lesson | 1 | 2026-08-19 | — | portable | — | watching |
| The bundled `claude-code-guide` agent runs on claude-haiku-4-5 (measured from message.model) — fine for docs relay, but do not assign it judgment work and do not record it as a standard-tier row. | lesson | 1 | 2026-08-19 | — | local | — | watching |
| The "Review and verify are one price" qualifier in shared.md hedges "a completed agent's transcript may be unresumable", but harness.md carries a measured resumption of a finished agent with context intact (2026-08-18). Promote's gate refuted the hedge entering skill text (finding F1, refuter verify command: `grep -rni "unresum" SKILL.md references/` stays empty). One of the two must retire: an observed failed resume confirms the hedge; further clean resumes retire it. Gate refuter was same-family (Opus 5) — residual bias recorded, though F1 was command-settled. | contradiction | 1 | 2026-08-19 | Review and verify are one price | portable | — | watching |
| A Run-log append can corrupt the table two ways: one row landed glued to the previous row's `|` terminator (no leading newline), another landed after a blank line, cutting it out of the table. The end-of-file anchor alone does not prevent either — an append must first ensure the file ends with exactly one newline. Caught by promote's preflight invariant check (marker 6), repaired by hand on the user's word. | defect | 1 | 2026-08-19 | — | portable | — | watching |
| On the gpt-5.6-sol family a unit's cost can be fully unmeasurable: the notification counter, the transcript's usage fields AND the watchdog's --status spend all read ~0 while the unit did real work (2026-08-20: 70 records, 37 tool uses, read 0 everywhere; 2026-08-19: a sol unit under-read at 5k). Record such units as "unmeasured", never as 0 and never as the notification figure — this is one step beyond the counter-zero row above, which assumed the transcript still carried the truth. | lesson | 2 | 2026-08-19 → 2026-08-20 | — | portable | — | watching |
| A checker's finding on a fixed file is not a regression until you run the OLD binary against the same probe. A cross-family refuter returned three defects on a fix diff; replaying its probes against the pre-fix committed script showed two were pre-existing gaps and only one was a true downgrade, which inverted the triage. The probe set costs one command to replay and it is the only thing that separates "the fix broke it" from "the fix did not close it". | lesson | 1 | 2026-08-20 | — | portable | — | watching |
| `local.md` on this machine is at sentinel **v1** while `references/memory.md` `## Structural invariants` requires **v2**: line 1 reads `<!-- sage-local-memory v1 -->` and the Watch-list table has 6 columns where the contract requires 8 (`Class` and `Promoted` missing). Every consolidation pass therefore aborts at marker 1 and marker 5, writing nothing, and the protocol forbids the pass repairing the file it validates. The installer's drift notice is the intended repair. Until it runs, the consolidation hint fires on every run and can never clear. | defect | 1 | 2026-08-24 | — | local | — | watching |
| The consolidation trigger at **40 non-pointer data rows** may be structurally unreachable. Bands (10) + Rules (11) + Watch list (18) already total 39 before a single Run-log row, and the Watch list's only drain is a row whose `Status` stops reading `watching` — none here ever has. A trigger that no legal pass can clear fires on every run for ever. Measured 2026-08-24: 72 rows, of which 39 are undrainable by consolidation alone. | defect | 1 | 2026-08-24 | — | portable | — | watching |
| **occ-30pct fires during Step 6 on investigation- and corpus-edit-shaped runs, with nothing left to launch.** Third machine-local occurrence: 302k (2026-08-19), 306k (2026-08-20), 302k (2026-08-24). Each time a successor would have had to re-read the note, the ledger and the corpus to perform a run record and a memory append, which costs more than the remainder. Three occurrences is a pattern, not an accident: either the protocol should name "Step 6 with an empty launch queue" as a legitimate no-successor branch, or the threshold is mis-sited for these run shapes. | lesson | 3 | 2026-08-19 → 2026-08-24 | — | local | — | watching |
| Reading a local_agent's `.output` file via TaskOutput/Read pastes the raw JSONL subagent transcript into the parent window — measured 2026-08-26 at ~22k tokens (8% of that run's occupancy) for zero usable information, on a fleet where `sage-watch --status` already reported liveness and per-unit spend. The Agent tool's own result text warns against it; the warning is easy to skip when a unit shows `done=yes` but its notification has not yet arrived. Waiting for the notification, or reading `--status`, is the whole fix. | defect | 1 | 2026-08-26 | — | portable | — | watching |
| The decisive finding of a multi-lens review can belong to no lens: on the 2026-08-26 /teach review two lenses each returned half of it (option-length measurements; the answer index being present in the DOM) and neither checked the answer's *position* distribution, which was the actual defect — 13 of 13 questions in 3 of 4 lessons had the correct answer at index 0, with no shuffling in the renderer. The composite was constructed at triage. Suggests the parent should run an explicit compose pass across lens reports, not just a merge-and-dedupe. | lesson | 1 | 2026-08-26 | — | portable | — | watching |
| A teaching/documentation corpus can carry its own wrong verification record: two NOTES.md entries stamped "Verified live (2026-08-25)" were both false (a base-services topology claim and a Helm chart-repo default), and each had propagated into a published lesson. When reviewing a corpus that documents its own fact-checking, treat that record as an artifact under review rather than as ground truth. | lesson | 1 | 2026-08-26 | — | portable | — | watching |
| A refuter scoped to ONE findings list prices at the frontier review-lens band, not the 375–800k multi-claim refuter band: 254k against a 250k estimate, over 9 attacked items spanning 2 corpora of evidence. The band's qualifier may be the breadth of the *mandate* rather than the number of corpora touched | lesson | 1 | 2026-08-27 → 2026-08-27 | — | portable | — | watching |
| Parent reached the 30% handover threshold with one unit in flight and the deliverable already fully durable on disk, and continued instead of spawning an `orchestrator` successor (logged as a deviation). Ran to completion at 33% with no compaction. Worth watching whether the single hard threshold wants a nothing-in-flight-and-durable carve-out, or whether this was luck | lesson | 1 | 2026-08-27 → 2026-08-27 | — | portable | — | watching |
| Price a negative-result mandate as a review lens, never as a fact lookup: three fact rows priced identically in shape and only the negative one blew out — U1 (positive: how accounts pick a level) 70k est → 85.9k occ = 1.23x; U2 (positive: one end-to-end trace) 95k est → 73.0k occ = 0.77x, under; U3 (negative: does `instanceRole` cause failover) 60k est → 146.3k occ / 192.6k spend = 2.44x / 3.21x. Same topology, same corpus, same agent type, same effort; the one difference is that proving a mechanism does NOT exist means exhausting the search space rather than stopping at the first confirming hit. U3 was priced as the narrowest of the three and was the widest by 2x. | lesson | 1 | 2026-08-26 → 2026-08-26 | — | portable | — | watching |
| On build 2.1.246 the Agent tool has no `name` parameter, so the agentId is the only steering handle. Verified from the tool schema that run was given: `Agent` accepts `description`, `isolation`, `model`, `prompt`, `subagent_type` and nothing else. SKILL.md Step 3 says "Name every dispatch, and name its model. The name is the parent's only handle for a steer or a stop" and `### Unit table` is told to carry that name — which a dispatch on this build cannot supply. Generation 2 additionally reports `SendMessage` to a name given inside a dispatch *prompt* failing outright, and `ListAgents` showing subagents by agentId only; that half is attributed to generation 2 and was not re-measured. `defect` rather than `lesson` because closing it means editing sage's own protocol text, not accumulating confirmations. | defect | 1 | 2026-08-26 → 2026-08-26 | — | local | — | watching |
| A single-file write lease is too tight for any unit that must measure exit codes or diff large dumps, and reader units break it silently: THREE of the four command-running reader units overran (U2 six scratch captures, U3 three, U9 six that no generation logged at all — found only by auditing the run's own record at Step 6). All were regenerable command captures in scratch — no repo touched, no mutating verb — and in U3's case load-bearing, since those captures proved the byte-identical-manifest negative result. The cheap fix is demonstrated: later rounds granted explicit prefixed scratch allowances and both units' captures landed inside their leases. Grant the allowance in the brief; do not make a reviewer choose between measuring and obeying. Correction to the briefed figure: "three of three fact units" is unsupported — the supported figure is three of the four command-running readers, one of which is a reviewer rather than a fact unit. | lesson | 1 | 2026-08-26 → 2026-08-26 | — | portable | — | watching |
| A sage successor can end up adjudicating its own rails, and nothing mechanical stops it: generation 2 crossed rail 3 twice — editing `lessons/0004` and `reference/glossary.html` outside every lease the run defined — and logged both as its OWN deviations instead of returning the rail to the parent as its brief required. The parent audited both diffs by command and ratified both edits while refusing to ratify the channel. Both calls were right, which is exactly what makes this a protocol defect rather than a bad outcome: the rail held only because the successor happened to be correct. `defect` because the successor role's instructions already forbid the crossing, so the gap is in enforcement, not in the rule. Generation 3 demonstrated the working channel: a two-file lease recorded in the ledger *before* the writer was dispatched. | defect | 1 | 2026-08-26 → 2026-08-26 | — | portable | — | watching |

**Judgment flags on proposed `Class` values** (change the cell if you disagree; the observation
text is the authority): the alt-counter-zero row and the sidecar-`model`-field row are marked
`local` because they are this machine's measurements, though the behaviour is plausibly
build-wide (`portable`); the gpt-5.6-sol-unmeasurable row and the subagent-window row are marked
`portable` because they describe model-family/harness behaviour that travels; the occ-30pct row
is marked `local` because its own text says "machine-local occurrence"; the est=150k-clamp row is
marked `portable` because it describes `sage-watch.sh`, which ships identically everywhere.

---

## 5. Run-log repair data

### 5a. Rows to insert into the main table (7 columns, immediately after the 2026-08-26 "author 3 HTML lessons" row)

These compress the two misfiled `###` subsections. The verbatim originals go to the archive (§5b)
— nothing is lost, matching the consolidation protocol's "every original survives verbatim in
exactly one place". Neither subsection recorded a wall clock, hence `—`.

```
| 2026-08-19 | CI-failure investigation (LoginCiTools, tddmon / TDD CI Express): 4-lens research sweep + 2-checker adversarial verification, HTML report deliverable; 6 agents, 3 parent-kept units | 6 | ~900k | ~1,168k (1.3x); rail 4 fired once per-unit (refuter 651k vs 600k ceiling) | — | Moved verbatim → `local-archive.md` (format repair 2026-08-27: original was a `###` field-table misfiled inside this table). Key lessons: a refuter aimed at a whole report is a multi-claim refuter — price from the 375–800k band, never from the artefact's size (landed 651k); run the control before claiming a cause — the cross-family refuter found the "trigger" present in PASSING builds too, reversing the headline, for the cost of one grep loop; a harness guard blocks subagents writing findings files, so a "write to a file, return 1–2k" brief silently becomes "return everything inline" — budget for the larger reply; a flat `spend=` between two `--status` reads is not a stalled unit — the probe's `done=` field is the liveness signal (a unit declared abandoned on spend-flatness ran on to 265k and returned the run's best finding). Coordination check positive and decisive. occ-30pct fired at 302k of a 1M window; no successor spawned (deviation recorded); run finished at ~335k. |
| 2026-08-20 | flaky-fixture verdict (AzureComputerVision, tddmon / TDD CI Express): parent-owned measurement first, then 1 source scout + 1 named-URL web lens + 1 test-isolation lens + 1 multi-claim adversarial refuter; 4 delegated, 2 parent-inline | 6 | 550k | ~1,480k (2.7x): fleet 265k dedup (u5 103k, u4 75k, u1 50k, u3 37k); parent spend proxy 1,217k (output 307k + cache_creation 911k), occupancy 312k at close; no rails fired | — | Moved verbatim → `local-archive.md` (format repair 2026-08-27: original was a `###` field-table misfiled inside this table). Key lessons: the same-shape row sat one entry above and was ignored — search prior rows by corpus and deliverable, not by agent graph (reading it would have priced within ~25%); a parent-inline unit in a data investigation prices as a spend curve over the run, never as unit rows (the entire 2.7x overrun was the parent's 1,217k); a NARROW refuter mandate beats the multi-claim band 3–5x — five named numeric claims over one code file and one DB landed at 75k, so the band's "across 2+ corpora" qualifier is load-bearing in the cheap direction too; ask which dimension you have not grouped by — grouping failures by CI agent pool moved the root cause from the code to the network path (all 11 stalls on one of two pools, 0 in 614 runs on the other); run controls on a refuter's causal claim too (two one-query controls sharpened it); a tight cluster of near-identical durations is a constant, not a distribution — it finds the mechanism without classifying the individual case. Coordination check positive and decisive. occ-30pct fired at 306k during Step 6 with zero units in flight — second machine-local instance of exactly this ending. |
```

### 5b. Block to append to `memory/local-archive.md`

Append at end of file, then paste the two verbatim subsections from **Appendix A** where marked:

```
## Repair 2026-08-27 — Run-log format repair, by hand on the user's word

Two run records had been filed as `###` field-value subsections inside `## Run log`, breaking
structural marker 6 (one table per section); two Watch-list rows and four run rows had been
appended after them into the same broken block. Each subsection below is verbatim as it stood in
`local.md`; its content now lives in one standard 7-column row in the Run log, tagged
"Moved verbatim → local-archive.md (format repair 2026-08-27)".

### moved: misfiled format — original of the 2026-08-19 LoginCiTools row

<paste Appendix A.1 verbatim here>

### moved: misfiled format — original of the 2026-08-20 AzureComputerVision row

<paste Appendix A.2 verbatim here>
```

---

## 6. Optional prose update (R4): Watch-list section intro

Replace the single paragraph under `## Watch list` (baseline line 56) with the v2 seed's
paragraph, verbatim:

> Lessons seen once, contradictions against a `shared.md` rule, skill defects, and task classes with no coverage. `Kind` is `lesson`, `contradiction`, `defect` or `gap`; `../references/memory.md`, `## Append`, says what each records and where it ends. `Contradicts` names the `shared.md` rule a local run cut against, or `—`. A `contradiction` row does not overturn the rule it names; it needs its own confirmations and surfaces in the next hint as a **retirement candidate**. `Class` is `portable` or `local` — the same test the Rules table above applies — and `Promoted` is the same append-only history joined with ` · `. **Those two columns are what let a row here become a rule at all**: the `→ shared.md` trigger reads both, and for twelve runs this table had neither, so nothing on it could ever evaluate the trigger and nothing ever graduated. `Status` is `watching`, `settled → …`, `promoted → …` or `dropped → …`, and **the state is the cell's first word** — the rest is payload. `../references/memory.md`, `### The closure act`, says who may write each state and what evidence it needs.

---

## 7. Verification suite (all must pass)

Run against the repaired file (`L=/root/.claude/skills/sage/memory/local.md`, or wherever the
repair was staged). Expected values assume the baseline snapshot; **if runs have appended Run-log
rows since (they land at end-of-file), add 1 line to the Run-log expectation per new row and
nothing else changes.**

```sh
# 1. Sentinel (marker 1)
head -1 "$L"                            # exactly: <!-- sage-local-memory v2 -->

# 2. Section order (whole-file shape)
grep -n '^## ' "$L"                     # exactly, in order: Harness version stamp, Bands, Rules, Watch list, Run log

# 3. Harness stamp untouched (marker 2 — repair must NOT have changed it)
grep -c '^sage-harness-stamp: 2\.1\.235 | verified 2026-08-19$' "$L"   # 1

# 4. Table headers (markers 3–6)
grep -c '^| Class | Figure | Qualifiers | Evidence |$' "$L"                                              # 1
grep -c '^| Rule | Count | First → last | Provenance | Class | Promoted |$' "$L"                          # 1
grep -c '^| Observation | Kind | Count | First → last | Contradicts | Class | Promoted | Status |$' "$L"  # 1
grep -c '^| date | task class | agents | est | actual | wall clock | note |$' "$L"                        # 1

# 5. Watch list: ONE block, 32 lines (header + separator + 30 data rows)
awk -v s='Watch list' '$0=="## "s{i=1;next} /^## /{i=0} i&&/^\|/{if(!b)n++;b=1;r++;next}{b=0} END{print n+0, r+0}' "$L"
# expected: 1 32

# 6. Run log: ONE block, 29 lines at baseline (header + separator + 27 data rows: 21 original + 2 converted + 4 relocated-in-place)
awk -v s='Run log' '$0=="## "s{i=1;next} /^## /{i=0} i&&/^\|/{if(!b)n++;b=1;r++;next}{b=0} END{print n+0, r+0}' "$L"
# expected: 1 29   (+1 line per run row appended after the 2026-08-27 baseline row)

# 7. No ### headings anywhere (the misfiled subsections are gone)
grep -c '^### ' "$L"                    # 0

# 8. No illegal Status values; every watch row's last cell starts with a legal state
grep -c '| open |$' "$L"                # 0

# 9. Every Watch-list data row has exactly 8 cells (9 pipes)
awk -v s='Watch list' '$0=="## "s{i=1;next} /^## /{i=0} i&&/^\|/{n=gsub(/\|/,"|"); if(n!=9) print "FLAGGED:", NR, substr($0,1,60)}' "$L"
# expected: EXACTLY ONE flagged line — the "A Run-log append can corrupt the table two ways" row,
# whose observation legitimately quotes a literal | inside backticks (10 pipes; verbatim from the
# original file — this is the residual case references/memory.md ## The hint names: awk cannot see
# markdown code spans). Any OTHER flagged line is a real defect.

# 10. File ends with exactly one newline
tail -c 2 "$L" | od -c                  # last byte \n, second-to-last NOT \n

# 11. Archive gained the two verbatim originals
grep -c '^## Repair 2026-08-27' /root/.claude/skills/sage/memory/local-archive.md   # 1
grep -c 'LoginCiTools' /root/.claude/skills/sage/memory/local-archive.md            # >= 1
grep -c 'AzureComputerVision' /root/.claude/skills/sage/memory/local-archive.md     # >= 1

# 12. Nothing else changed: shared.md still healthy and untouched by this repair
grep -c '^## ' /root/.claude/skills/sage/memory/shared.md    # 11
```

Content-preservation check (the self-check consolidation uses, adapted): every baseline data row
must survive verbatim in exactly one place — 24 watch rows and 4 run rows (2026-08-24/25/26/27)
in `local.md` (watch rows with two cells inserted), the 2 D5 rows in the Watch list with only
their `Status` cell changed, the 2 `###` subsections verbatim in the archive, and the 4 owed rows
newly present. Nothing deleted without an archive copy.

---

## 8. After the repair

1. **Re-run `/sage-promote` on the user's word.** Expected effects: preflight now passes; stage
   zero re-verifies the `defect` rows (the v1/v2 row and the 40-row-trigger row should close as
   `settled`; the append-newline, TaskOutput, Agent-name and successor-rails rows stay open or
   route per their text); stage one evaluates the `→ shared.md` trigger over watch rows that can
   finally carry `Class`/`Promoted` — note the alt-counter-zero row sits at Count 4 with 7
   narrated confirmations in Run-log notes, a promotion candidate the moment its count is
   reconciled; stage three re-dates the stale harness stamp (2.1.235 → the live build, 2.1.246 at
   snapshot time) with its vendor-docs fetch.
2. **Consolidation un-blocks**: the next sage run's Step-2 consolidation pass will finally run
   (it has aborted at markers 1/5 since at least 2026-08-24) — expect it to propose compressing
   older Run-log rows and to reconcile watch-row counts against Run-log narration.
3. The append guard's before-reading (`blocks must be 1`) will pass again, so future runs write
   their watch rows to the right table instead of parking them in ledgers or misfiling them at
   end-of-file.

---

## Appendix A — verbatim misfiled `###` subsections (for the archive move)

### A.1 — baseline lines 112–125

```
### 2026-08-19 — LoginCiTools CI failure investigation (tddmon / TDD CI Express)

| field | value |
| --- | --- |
| Task | Investigate SQL login failures in recent CI runs; deliver an HTML report |
| Topology | 4-lens research sweep + 2-checker adversarial verification; 6 agents, 3 parent-kept units |
| Estimate → actual | ~900k → ~1,168k (1.3x) |
| Rails | Rail 4 fired once, per-unit: refuter 651k vs 600k ceiling |
| Lesson (estimating) | **A refuter aimed at a whole report is a multi-claim refuter, not a review round.** I priced the row at 150k as a "review round" while this file's own band says 375–800k for an adversarial refuter on a multi-claim mandate across 2+ corpora. The row landed at 651k, inside that band. When the mandate is "attack every load-bearing claim in this artefact", price it from the band, never from the artefact's size. |
| Lesson (method) | **Run the control before claiming a cause.** The parent measured that every FAILING build showed the trigger, and concluded causation. The cross-family refuter measured PASSING builds and found the same trigger there — reversing the headline. Cost of the control: one grep loop over 7 build directories. A "the trigger is present in every failure" finding is worth nothing until the same command has been run against the non-failures. |
| Lesson (harness) | A harness guard blocks subagents from writing findings/report files. Two units hit it and returned full detail inline instead, losing nothing — but a brief that says "write your detail to a file and return 1-2k tokens" silently becomes "return everything inline". Budget for the larger reply, or have the parent create the file. |
| Lesson (watchdog) | **A flat `spend=` between two `--status` reads is not evidence of a stalled unit.** I declared a unit abandoned on that reading; it was mid-tool-call, ran on to 265k, and returned the single best finding of the run. A long tool call and a dead unit look identical in the spend column. The probe's own `done=` field is the liveness signal — it still read `no`. Never abandon on spend flatness alone. |
| Coordination check | POSITIVE and decisive — the cross-family refuter reversed the deliverable's conclusion; the code-path unit then supplied the mechanism that fits the refuter's control result; 3 lenses returned zero overlapping findings; the domain researcher killed the parent's opening hypothesis before it shipped. |
| Occupancy | occ-30pct fired at 302k of a 1M window; no successor spawned (deviation recorded), run finished at ~335k. |
```

### A.2 — baseline lines 127–142

```
### 2026-08-20 — AzureComputerVision flaky-fixture verdict (tddmon / TDD CI Express)

| field | value |
| --- | --- |
| Task | Decide whether a flaky alert on one test fixture is true, find the cause, recommend a fix, deliver a doc |
| Topology | Parent-owned measurement first, then 1 source scout + 1 named-URL web lens + 1 test-isolation lens + 1 multi-claim adversarial refuter; 4 delegated, 2 parent-inline |
| Estimate → actual | 550k → ~1,480k (2.7x). Fleet 265k dedup (u5 103k, u4 75k, u1 50k, u3 37k); parent spend proxy 1,217k (output 307k + cache_creation 911k), occupancy 312k at close. 4x ceiling (2,200k) not reached |
| Rails | None fired. Rail 4 stayed clear at both scopes |
| Lesson (estimating) | **The same-shape row was sitting one entry above mine and I priced off bands instead.** The 2026-08-19 LoginCiTools row is the same repo, the same store, the same investigate-then-report shape: 900k estimated, 1,168k actual. I wrote 550k from reader bands and landed 1,480k. Reading the previous row would have put me within ~25%. "Price off a same-shape row" fails when the row is filed under a *task* name and the next run searches by *topology* — look for the same corpus and deliverable, not the same agent graph. |
| Lesson (estimating, 2nd) | **A parent-inline unit in a data investigation is not priceable as a unit.** I gave units 2 and 6 (query the store, write the doc) 150k combined; the parent actually spent ~1,217k, and the entire overrun is there. When the parent holds the measurement loop, every turn re-reads a growing context — price it as a spend curve over the run, never as two rows. |
| Lesson (estimating, 3rd) | **A narrow refuter mandate beats the multi-claim band by 3-5x.** I deliberately trimmed 375-800k to 250k because the mandate was five named numeric claims over one code file and one DB rather than 2+ corpora; it landed at 75k. The band's qualifier ("across 2+ corpora") is load-bearing and worth trusting in the cheap direction, not just the expensive one. |
| Lesson (method) | **Ask which dimension you have not grouped by.** The parent proved a 100s timeout mechanism from durations, error text and source, and never grouped the failures by CI agent. The refuter did, and found all 11 stalls on one of two agent pools and none in 614 runs on the other — which moved the root cause from the code to the network path and reordered the whole fix list. The parent's evidence was correct and pointed at the wrong owner. |
| Lesson (method, 2nd) | **Run the control before adopting a refuter's causal claim, too.** The refuter's "the OLQ pool's egress is bad" needed two controls the refuter had not run: is that pool generally slow (no — 0.221% stall rate vs 0.399% on the other pool, across 560k executions), and does the other pool even make the Azure calls (yes — 38.6s vs 33.2s mean on the happy path). Both controls were one query each and both sharpened the finding instead of killing it. |
| Lesson (data) | **A tight cluster of near-identical durations is a constant, not a distribution.** Four failures inside a 1.41s spread at ~123s said "timeout" before any source was read. But duration detected the stall without predicting the outcome: 5 runs stalled and still passed, and two runs 5ms apart went opposite ways, because a stall inside a test asserting `False` passes. Cluster-spotting finds the mechanism; it does not classify the individual case. |
| Coordination check | POSITIVE and decisive. The refuter alone found the agent-pool confinement, the report's strongest finding; it also refuted the parent's wording on the duration argument and replaced one measured stall with three. The web lens settled the 100s constant against a directly-fetched Microsoft page and separately killed the rate-limit hypothesis (429 fails fast). Zero overlapping findings across the four mandates. A solo run at the same budget ships a correct diagnosis aimed at the wrong team. |
| Occupancy | occ-30pct fired at 306k of a 1M window during Step 6, with zero units in flight and nothing left to launch; handoff note written, no successor spawned (deviation D4). **Second machine-local instance of exactly this ending** — the 2026-08-19 LoginCiTools row records the same call at 302k. Two occurrences suggests the threshold lands mid-Step-6 on investigation-shaped runs as a rule, not as an accident. |
```

## Appendix B — verbatim misfiled watch rows (baseline lines 146–147)

```
| A refuter scoped to ONE findings list prices at the frontier review-lens band, not the 375–800k multi-claim refuter band: 254k against a 250k estimate, over 9 attacked items spanning 2 corpora of evidence. The band's qualifier may be the breadth of the *mandate* rather than the number of corpora touched | lesson | 1 | 2026-08-27 → 2026-08-27 | — | open |
| Parent reached the 30% handover threshold with one unit in flight and the deliverable already fully durable on disk, and continued instead of spawning an `orchestrator` successor (logged as a deviation). Ran to completion at 33% with no compaction. Worth watching whether the single hard threshold wants a nothing-in-flight-and-durable carve-out, or whether this was luck | lesson | 1 | 2026-08-27 → 2026-08-27 | — | open |
```

Both re-homed in §4 rows 25–26 with `Class`/`Promoted` inserted and `open` corrected to
`watching` (their only edit).

## Appendix C — provenance of the four owed rows (D6)

Source: the 2026-08-26 run's ledger, `### Watch-list rows owed`, found at
`/tmp/ledger.damaged.md` on the damaged machine (117,176 B, mtime 2026-08-26 18:06 — volatile;
this report supersedes it as the durable copy). Its parking note, verbatim:

> **Blocked by D12, recorded here verbatim so nothing is lost.** `/sage-promote` should transcribe these after it migrates `memory/local.md` from v1 to v2, since only that skill may repair the corpus. Column order when transcribed: Observation, Kind, Count, First → last, Contradicts, Class, Promoted, Status — the last three of which the current six-column table cannot hold, which is the whole reason these are here. All four: Count 1, First → last `2026-08-26 → 2026-08-26`, Contradicts `—`, Promoted `—`, Status `watching`.

The four bullets' full prose is preserved in §4 rows 27–30 with only bullet-to-table-cell
reflow (bold lead-ins folded into the observation text, internal cross-references like "(D5)",
"(G1)" dropped as ledger-local); Kind and Class are the ledger's own: `lesson`/`portable`,
`defect`/`local`, `lesson`/`portable`, `defect`/`portable`.
