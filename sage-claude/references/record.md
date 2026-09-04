# Record and surface

Your job here: bring the ledger current, write its `### Run record`, print four things, and close four obligations. Everything is recorded; almost nothing is printed.

There is one file and it is the ledger — plan, unit table, failures and retries, deviations, assumption log, finding dispositions, diff pointer, coordination check, lessons stored. A report is a **rendering** of it, produced on demand. It is never a second file.

Bring the ledger fully current first, then write its `### Run record`: topology and why, one line per unit, actual cost against estimate, every deviation, finding dispositions, the diff pointer, evidence pointers, the journal append's count of lines appended and confirmed, explicit gaps and uncertainty, human-only items, and the condensed assumption-log line. If anything was bounded, sampled, or dropped, say so — silent truncation reads as full coverage.

## The run record

Rendered on demand by `/sage report`, from this section alone, so the answer survives compaction.

```text
OUTCOME: <one line, or a pointer to the Result — never a replacement for it>
Topology: <pattern, N agents, why> (or "solo — <reason>")
Agents: <one line each: unit → model actually used (measured from `--status`, or `asserted` where the sensor could not run) → status → key evidence>
Cost: <N agents, ~actual against ~estimate, wall clock — say so where no token counts were visible, in which case the agent-count rail was the one in force>
Deviations: <every row that ran with a different model, effort, count, or scope than planned, and why — or "none">
Findings: <accepted / rejected / deferred / user-decision counts, plus the ones that matter>
Verification: <checks run and outcomes. Separate MEASURED passes — a command executed — from JUDGED passes, where a case was read and ruled on. A judged pass is a reviewer's opinion with a case number on it. `Awaiting human` cases count as neither, and any machine-verifiable case that downgraded to judged is named here>
Diff: <pointer to the frozen diff — revision range or changed-file manifest, writer by writer, or "none">
Coordination check: <what depended on the agents being independent — a disagreement, a refutation, a cross-angle finding — or "nothing; one agent at this budget would likely have matched it". Answer honestly: "the fan-out bought nothing" is a real result>
Gaps: <anything bounded, sampled, skipped, or unverified — explicitly>
Awaiting human: <subjective or product checkpoints, if any>
Assumptions: <one condensed line from the assumption log — the calls that would change the answer if wrong>
Memory check: <the journal read-back after the append — the lines this run added, counted, as `journal: +N lines, tail verified` (`memory.md`, `## Append at Step 6`). "Ran it" is not an entry here — the count is. "none — nothing appended" is a legal value and says which>
Lessons: <the note from the `run` line appended to `../memory/journal.md` this run, mirrored verbatim — the lesson a future run can act on, or "none beyond the actuals". This file writes the line; this one is what makes it renderable>
```

The **Result** — the deliverable in prose, standing alone — is printed on every run and never lives only here. `OUTCOME:` is one line inside a template, and a template line compresses a deliverable into a pointer.

**`/sage report` resolves the ledger in this order:** this session's file; else, with no session named, the most recently modified `.claude/plans/sage-ledger-*.md` under the working directory, naming which one it read; else the scratchpad fallback. None of those → say so. A run record is rendered from a ledger or not at all, never reconstructed from memory.

## Print four things, every run

1. The **Result** — the deliverable, in prose, standing alone. What the user asked for, answered, at whatever length the answer needs. It never collapses to a pointer.
2. One **run line**: `sage: N agents · ~Xk · ~Y min · <ledger path>`.
3. An **artifacts block** — only the rows that exist:

   ```text
   artifacts:
     ledger   .claude/plans/sage-ledger-<session>.md
     diff     <revision range or changed-file manifest>
   ```

   Recording is not the same as reaching. The ledger path already rides the run line, but the diff pointer lives in `### Run record` where only `/sage report` renders it — so a clean run ends with an artifact the user has no way to open. **`ls` every path before you print it** — the citation rule in `dispatch.md` Step 3 reaches the run's own output, and a printed path that does not resolve is worse than one never printed.
4. Any **surfaced event** from the list below.

## Surfaced events

These print regardless of anything else:

- A rail fired, and whether the figure that fired it was a projection or an actual.
- A writer touched a path outside its lease.
- A security-shaped finding.
- A failed or abandoned unit, and every abandoned disagreement.
- An `Awaiting human` item.
- The coordination check came back negative — the fan-out bought nothing.
- A memory hint is due — the journal past its bar, or the lineup stamp stale.
- The watchdog fired, or could not run.
- The ledger lint still reports a violation at Step 6, or could not run.
- The checkpoint rung fired, or a compaction landed — on the parent, or on any unit whose `--status` line shows `compact=` above zero, because that unit reported from a summary of its own work.

## Four closing obligations

Cheap and easy to skip.

- **Coordination check.** Did any result depend on the agents being independent — a disagreement, a refutation, something visible only across angles — or would one agent at the same budget have matched it? In the one published analysis of this, token spend alone explained most of the variance in outcomes. This is the only line that can falsify sage's own premise, so answer honestly: "the fan-out bought nothing" is a real result, it goes in `### Run record`, and a negative answer is a surfaced event.
- **Append to `memory/journal.md`** — plain lines via `>>`, nothing else (`memory.md`, `## Append at Step 6`, owns the grammar): the `run` line always, hits included, with the lesson a future run can act on; the `use` line naming every KI this run read and whether each helped; `obs` lines as earned — a new observation, a `confirm <ki-id>` where the run re-observed an existing KI, a `settle <ki-id>` where it produced the artifact that answers one. The run flips no status and bumps no count — those are `/sage-promote`'s, applied from these lines. The `run` line's `model=`, `compact=`, `turns=`, `occ-sum=` and `saving-post-rung=` fields are measured, not estimated: read them from `../bin/sage-watch.sh --status` over the parent transcript at close, with `SAGE_CHECKPOINT_TURN=<n>` set from `### Resume state`'s `checkpoint:` field where one fired. Then `tail` the journal and confirm the lines landed whole — **record the count of lines this run appended and confirmed in `### Run record`**; the obligation is unconditional, because the estimate that set this run's budget ceiling is only honest if its actual is recorded. If the write does not land, say so under gaps and put the lines in the printed block instead. Then check the two hint conditions (`memory.md`, `## The hint`) — a due hint is one surfaced line and nothing more.
- **Run the lint once more, and mean it.** The ledger is final when `../bin/sage-lint.sh` is silent on it, or when every line it still prints is a surfaced event with a reason next to it. Step 6 is the last point at which a record check it fails is still cheap to fix.
- **Stop the watchdog.** The hosted `while true` loop outlives the run unless you end it, and a `Monitor` left running against a finished session's `subagents/` directory prices nothing and reports nothing useful. Where the harness gives no clean way to stop it, say so explicitly under gaps rather than leaving it running silently.

Anything beyond the four printed items is available on `/sage report`, which renders the full block from the ledger. The ledger is the source, so the answer survives compaction.
