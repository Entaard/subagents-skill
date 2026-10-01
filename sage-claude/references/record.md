# Record and surface

Your job here: write the run record, close the ledger, print four things.

## The run record

Write it with `sage-ledger.sh record <ledger>`, body on stdin. `/sage report` renders this section alone.

```text
OUTCOME: <done | partial | stopped> — <one line>
Cost: <N agents; spend from `sage-watch.sh --status`, or "not measured"; Codex spend from the receipts; wall clock against the wall target>
Verification: MEASURED — <each command run and its outcome>. JUDGED — <each case a reviewer ruled on by reading>. A runtime claim that nothing ran is JUDGED. Name any machine-checkable case that fell back to judged
Coordination check: <what depended on the agents being independent — a disagreement, a refutation, a cross-angle finding — or "nothing; one agent at this budget would likely have matched it">
Alt lane: <per codex unit: seat, model= effort= outcome= spend= from its receipt, and what it contributed — finding ids with triage, refuted/survives per claim, a finding no other checker raised, or "nothing". A seat probed and dropped: its outcome. "not used" when no seat ran>
Gaps: <anything bounded, sampled, skipped, or unverified — explicitly>
Awaiting human: <subjective or product checkpoints, and every finding the partial stop left open>
```

**The coordination check.** Did any result depend on the agents being independent, or would one agent at the same budget have matched it? This is the only line that can falsify sage's own premise, so answer it honestly. "The fan-out bought nothing" is a real result, and a negative answer is a surfaced event.

**`/sage report`** reads this session's newest ledger, else the newest `.claude/plans/sage-ledger-*.md` under the working directory (naming which one). With neither, it says so. It never rebuilds a record from memory.

## Close

Pipe the memory lines (`memory.md`, `## Step 6`) into the helper:

```sh
printf '%s\n' "<run line>" "<obs line>" ... | ~/.claude/skills/sage/bin/sage-ledger.sh close <ledger> [<subagents-dir>]
```

It refuses a Run record that is still pending, runs the lint, reads `--status` once when you pass the subagents directory (pass it on every run that dispatched a unit), appends each line to its log, and prints each log's tail. Confirm your lines landed whole. **A dirty lint appends nothing and exits 1.** Fix the violation and close again. A violation that must stand is a surfaced event: name it in the run record with its reason, then `close --keep-lint`.

## Print four things, every run

1. The **Result**: the deliverable in prose, standing alone. It never collapses to a pointer. On a partial stop its first line says "partial".
2. One **run line**: `sage: N agents · ~Xk · ~Y min · <ledger path>`.
3. An **artifacts block**, with only the rows that exist:

   ```text
   artifacts:
     ledger   <ledger path>
     diff     <revision range or changed-file manifest>
   ```

   **`ls` every path before you print it.** A published artifact's URL is a path too: confirm it with a read-back before you print it.
4. Every **surfaced event** below.

## Surfaced events

- A rail fired.
- A writer touched a path outside its lease.
- A security-shaped finding.
- A failed or abandoned unit, and every abandoned disagreement.
- An `Awaiting human` item, or a partial stop.
- The coordination check came back negative.
- A unit ran far past what you expected, or the agent-count ceiling was crossed.
- A memory hint is due (`memory.md`).
- The ledger lint still reports a violation at close.
- A compaction landed on the parent, or a unit's `--status` line at close shows `compact=` above zero: that unit reported from a summary of its own work.
