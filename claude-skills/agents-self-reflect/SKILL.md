---
name: agents-self-reflect
description: Consolidate the subagents skill's calibration log into bands and rules, archiving original rows verbatim, with the user approving the diff.
disable-model-invocation: true
---

# agents-self-reflect

One pass, on request: rewrite the live calibration log at `~/.claude/skills/subagents/calibration.md` into the consolidated shape below, and move every retired row, verbatim, into `calibration-archive.md` beside it. Three properties define the pass — **lossless** (the self-check counts rows), **approved** (the user sees the full diff before anything is written), and **idempotent** (a second run straight after proposes nothing).

Write scope: those two files, nothing else. Promotion candidates and skill defects come out as a report for the user to act on — the skill text, references, agent files, and installer stay untouched. The pass is solo work: do it inline, spawning nothing; for a very large fold the user may add one verifier over the rewritten file, and that is their call, never the default. Run the pass between orchestration runs only; during a run the subagents skill prints `Consolidation due: <reason>` and stops there.

The pass accepts any prior shape of the log. The first run on a machine is the migration.

## When a pass is due

This list is the canonical copy — the subagents skill points here, and the log's header mirrors it once a pass has consolidated it. Report which of these hold before starting. Any one makes the pass due, and the user may run it with none held:

1. The log is past ~10k tokens (~40KB).
2. 40 rows or more.
3. A lesson **not yet in the skill text** reaches three or more confirmations spread across rows, or a rule already promoted crosses a strength band (step 10). A promoted rule merely gaining another confirmation is **not** a trigger: the count lives in this log, and the skill text cites the band.
4. Two rows give different figures for one band, so a planner must read both to get the right number.
5. Structural damage: rows outside a table, or a summary contradicting rows below it.
6. A row asserts harness behavior from a version older than the one `references/claude-code.md` was last verified against.

## Target shape

The run log goes **last** — that ordering is the load-bearing choice, because "append one row at the end of the file" then stays correct by construction. The old shape broke exactly here: appends landed below the summary, and the summary went stale against the rows beneath it.

```markdown
# Calibration log

<the contract: what Step 2 reads, where Step 6 appends, the trigger list,
seed/local precedence, and the pointer to this skill and the archive>

## Bands: quote these at Step 2

| Class | Figure | Qualifiers | Evidence |
One line per unit class, newest confirmed figure. Evidence holds the run
count and the last-confirmed date. A losing figure survives as a qualifier.

## Rules: read once at Step 2, apply at the step named

### Step 2, estimating
### Step 3, briefing
### Step 4, execution
### Step 5, verification

One or two sentences per rule, with its confirmation count and dates, a
machine-independence mark, and the strength band the skill text cites —
derived here once, never re-derived at promotion time. A rule promoted into
the skill text is marked "promoted <date>", then archived on a later pass.

## Watch list

Lessons seen once, not yet rules. Skill defects that need a repo issue.
Task classes with no coverage.

## Run log (append new rows here)

| date | task class | agents | est | actual | wall clock | note |
Recent rows in full. Fully consolidated rows compress to one line with an
archive pointer.
```

`calibration-archive.md` holds, verbatim, every row that left the log, each tagged with the reason it left (retired or compressed). The subagents skill never reads it at Step 2; it exists so a rule's provenance can be settled with one grep.

## The pass, in order

1. Read the whole live log. Parse every row; split each note into segments: band data, rule, anti-lesson (a parent error to avoid repeating), skill defect, or one-off anecdote.
2. Merge duplicate lessons into one rule, keeping the confirmation count and the date list — the count is what makes a rule promotable.
3. Resolve contradictions: newer local data outranks older data, and both outrank seed data — the log's own precedence rule. The losing figure stays as one clause of the winning band's qualifiers; a recorded objection is kept.
4. Mark each rule **machine-independent** (would hold on any machine) or **machine-specific** (this machine's measured costs and versions); the mark rides the rule's own line. Band figures are machine-specific by nature, so mark only the exception — a ratio or shape that travels — in the band's Qualifiers cell.
5. Retire superseded seed rows and stale version-bound claims to the archive, tagged with the reason.
6. Order by weight: bands by evidence count, rules by confirmation count.
7. Compress each fully consolidated Run-log row to one line — date, class, agents, est vs actual, archive pointer — moving the row's full original text, verbatim, into the archive first. Keep the most recent rows in full.
8. If steps 1–7 produced no change, report "nothing to consolidate" and end the pass — asking nothing, writing nothing, skipping the checks below. Otherwise self-check, before showing anything. All of: every row present before the pass survives verbatim in exactly one place — the Run log (a row kept in full) or the archive — and the count of surviving originals equals the pre-pass row total (a compressed row's one-line summary is a pointer, not a survivor); every band cites at least one run; every rule carries at least one date; the rewritten log is smaller than the one it replaces; both files parse as markdown, the log in the target shape's section order with a header row on each table. A failed self-check stops the pass.
9. Show the user the full diff for both files. Write only after the user agrees; a declined diff ends the pass with nothing written.
10. Report, as output for the user to act on:
    - **Promotion candidates** — rules at three or more confirmations, each with its count and dates, proposed for the skill's own text. The machine-independent ones are also proposed for the repo seed (`subagents-claude/calibration.md`), approved per rule.

      **What a promotion writes: the rule and its strength band — never the count, never the dates.** Skill text cites `(calibration: established)` at six or more confirmations, `(calibration: recurring)` at three to five, and `(calibration: provisional)` for a below-bar fact carried only because its mechanism is structural. The arithmetic stays in this log, the one file every pass rewrites anyway. Inline it in the skill text as well and each later confirmation re-dates two files instead of one, building a changelog inside a guideline that no pass ever prunes — the skill text has no consolidation step, so anything dated that lands there is permanent.

      Two things are **not** tallies and travel intact. An **undated anecdote** — "one reader described a data structure that does not exist" — is what makes an abstract rule recognisable in the wild; keep it, drop only its date. A **figure the skill computes with** — a ratio, a token band, a boot cost, a discount factor — is a parameter, not evidence for a rule, and stays numeric wherever it appears or the instruction stops being usable. A date stays only on a claim about a system that drifts, where staleness is the signal: `references/claude-code.md`'s "verified against the changelog <date>, local install <version>" is the shape that earns one.

      A candidate whose only change is a higher count is **not** a promotion. Report it as "already carried, band unchanged" and propose no edit.
    - **Skill defects** that deserve a repo issue.

Done when: the user has answered on the diff, any approved write passed the self-check, and the report in step 10 is delivered.
