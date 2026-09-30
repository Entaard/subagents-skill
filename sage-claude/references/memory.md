# Memory

A run reads memory at Step 2 and appends at Step 6. It never edits, reorders or deletes a memory file. Every other write belongs to `/sage-promote`, on the user's word. `<mem>` is `~/.claude/skills/sage/memory/`.

## Step 2

1. **Same-shape rows.** `grep -iE '<task words>' <mem>/runs.log | tail -5`. Price and pace from them before any band. None → read each file `grep -liE '<task words>' <mem>/archive/v3/local/band-*.md` lists.
2. **Lessons.** Read `<mem>/lessons.md` whole. A lesson that changes a decision goes on the run line as `changed-by: <id> <how>`.
3. **The hints.** Run `bin/sage-promote-prep.sh --pending` (the pending inbox count) and `bin/sage-lineup-check.sh`. Both write nothing.

A missing file is not an error: plan without it and print one line saying so.

## Step 6

Pass one run line and any observation lines to `sage-ledger.sh close` (`record.md`), which appends them with `>>`:

```text
<date> run <session> | <task class> | agents=<n> spend=<tokens|none> wall=<min> target=<min|none> effort=<parent effort> outcome=<done|partial|stopped> [changed-by: <id> <how>] | <note>
<date> obs <session> | <kind> <class> | <observation> | falsifier: <text>
```

- **Write the run line on every run, hits included.** Write its note so a later plan can act on it: "fetch-heavy research runs 70–120k per agent" is usable, "unit 3 was expensive" is not.
- **`kind`** is `lesson`, `gap`, `defect`, `contradiction`, `confirm` or `correction`. A `correction` starts its observation with the date and session of the line it corrects.
- **`class`** is `portable` or `local`, those two words only. Only `portable` can reach the lessons file.
- **A falsifier** goes on anything that could one day be a rule.

## The hints

Print one line for each and stop. Promotion is never automatic.

- The inbox holds 25 or more pending lines → `/sage-promote`.
- `sage-lineup-check.sh` printed any line → the lineup changed. `/sage-promote` studies it.
