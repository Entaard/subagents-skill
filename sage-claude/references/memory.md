# Memory protocol

Your job here: read the knowledge items your task matches at Step 2, and append plain lines to the journal at Step 6 — nothing else. A run never edits a knowledge-item file, never bumps a count, never consolidates. Every structured write belongs to `/sage-promote`, on the user's word. Read this at Step 2 before estimating, and again at Step 6 before appending.

This is the v3 protocol; its design and history are in `~/.claude/skills/sage-promote/references/memory-contract.md`, which `/sage-promote` reads and a run never does.

[The boundary](#the-boundary) · [The journal](#the-journal) · [Read at Step 2](#read-at-step-2) · [Append at Step 6](#append-at-step-6) · [The hint](#the-hint)

## The boundary

| Text | A run reads it | A run writes it | Who writes it |
| --- | --- | --- | --- |
| The corpus: `../SKILL.md`, `references/`, `memory/shared/`, `memory/local/` | at Step 2 | never | `/sage-promote`, or build-authoring on the user's explicit word |
| The run's own ledger | the run, `/sage report`, `/sage resume`; never a later run | yes — the run's working record | the run |
| The journal, `memory/journal.md` | at Step 2, its `run` lines only | appended at Step 6, plain lines via `>>` | the run appends; `/sage-promote` drains |

The `run` read is the one exception to the rule that a run reads no log, and its reason is that a `run` line is an actual, not a lesson: `price-off-a-same-shape-row` (calibration: established) says the actual beats the band. Read exactly the `run` rows, so that an `obs` payload containing the word never matches: `awk '$2=="run"' memory/journal.md | tail -n 3`. Everything else in the journal is `/sage-promote`'s to read.

**A missing or empty `memory/shared/` → run on `local/` and the journal alone and print one line saying so.** The fix is `install.sh`, which syncs the clone from the template; do not hand-create files there.

## The journal

`memory/journal.md`. Line 1 is the sentinel `<!-- sage-local-memory v3 -->` — the installer greps it for format drift, so nothing may rewrite it. Then a short fixed header, then payload lines, append-only, newest last:

```
<date> run <session> | <task class> | agents=N est=X actual=Y wall=W model=<parent model> compact=<n> turns=<n> occ-sum=<tokens> saving-post-rung=<tokens> | <note>
<date> obs <session> | <kind> <class> | <observation> | falsifier: <...>
<date> obs <session> | confirm <ki-id> | <what happened>
<date> obs <session> | settle <ki-id> | artifact: <...>
<date> use <session> | <ki-id> hit | <ki-id> miss: <why>
<date> mark promote | drained through here by the <date> pass
```

Grammar: `date type session | payload`, types `run`, `obs`, `use`, `mark`. Write one line per fact and never reflow an existing line. A `|` inside payload is harmless — only the first three fields are positional. A malformed line is a question for the next `/sage-promote` pass, never damage.

The five fields after `wall=` come from `sage-watch.sh --status` read over the parent transcript at close (`record.md`): the parent's measured model, its compaction count, its deduplicated turn count, the sum of occupancy over those turns, and the most a fresh window after the checkpoint could have saved. Write `none` where the sensor could not run.

The `mark` line is promote's drain marker: everything after the last `mark` is what the next consolidation ingests, and the count of those lines is what the hint fires on. Promote's drain always leaves the newest three `run` lines in the live journal — they are Step 2's same-shape pricing rows.

## Read at Step 2

1. `bin/sage-index.sh` — the one-line-per-KI index.
2. Open the KI files the task matches: the band KIs for the unit shapes in the plan, the shared rules whose recogniser matches what is in front of you (with their stats sidecars for the counts), any watching lesson/gap/defect/contradiction KI touching the task's area. This is a judgment over the index, not a load-everything rule — the index is what makes selective loading possible, and the `use` line at Step 6 is what makes it honest.
3. The journal's newest `run` lines — the same-shape rows pricing wants first (`shared/price-off-a-same-shape-row.md`); the command is above.
4. Check the two hint conditions (`## The hint`).

**Remember what you loaded.** The Step 6 `use` line names the KIs this run actually read and whether each helped — that line is the entire usage-statistics instrument, and a run that skips it is invisible to the KI review stage that retires dead knowledge. Keep it to one line; ceremony here is how bookkeeping prose dies.

## Append at Step 6

Automatic, every run, to `memory/journal.md` only, via shell append (`>>`) — never by rewriting the file:

- **The `run` line, every run, hits included** — a band you can trust needs its hits recorded next to its misses. Write the note so Step 2 can act on it: "fetch-heavy research runs 70–120k per agent" is usable at plan time; "unit 3 was expensive" is not.
- **The `use` line** — every KI read at Step 2, `hit` or `miss: <why>`. A `miss` is the KI misleading the run, not the run not needing it; not-needed is simply absent from the line.
- **`obs` lines as earned** — a new lesson, gap, defect or contradiction, with kind and class named, and a falsifier for anything that could one day be a rule; `confirm <ki-id>` where this run re-observed an existing KI (that is what makes counts reach three and mean it); `settle <ki-id>` where this run produced the artifact that answers a KI, naming the artifact — `settled` requires the artifact to exist, not to be intended, because promote will flip the status on this line's word.

Then read the tail back — `tail -n 5 memory/journal.md` — and confirm your lines are there, whole, one line each. That is the entire post-append check: there is nothing an append can structurally break.

## The hint

Sage detects, prints one line, and stops. **Promotion is never automatic**; the user runs `/sage-promote`.

| Trigger | Condition |
| --- | --- |
| → `/sage-promote` | the journal holds **≥ 25 payload lines after the last `mark`** (`grep -c` after the last mark line; no mark → count all payload lines) |
| → model lineup | the `harness-stamp` KI's build is older than what `claude --version` reports |

Two, deliberately. The promotion, band-crossing and retirement triggers read aggregates that only `/sage-promote` acts on, so v3 computes them where they are consumed. Both hints are clearable by the action they call for, which is what makes a hint information rather than noise. The bar of 25 inherits v2's bar-of-10 economics: each run appends ~2–4 lines, so the hint re-fires within roughly eight to twelve runs even with nothing else accumulating. **Falsifier:** the hint fires on more than half of the next ten runs, or the journal sits past ~60 unmarked lines with the hint fired and no pass run — either reading means the bar is mis-sized; re-derive it from a measured pass, never by moving the number to make a hint go quiet.

The knowledge-item shapes, the field contract, the removal bar, the structural invariants and the compression floor are in `~/.claude/skills/sage-promote/references/memory-contract.md`. A run needs none of them; `bin/sage-index.sh` reads the frontmatter for it.
