# Memory protocol

Your job here: put every fact sage learns in the one file whose content class it belongs to, append to local memory on every run, and run consolidation and the hint under checks that can fail. Read this at Step 2 before estimating, and again at Step 6 before appending. Promotion and eviction are `/sage-promote`'s, never a run's.

[The two files](#the-two-files) · [Append](#append) · [Consolidate](#consolidate) · [The hint](#the-hint) · [Promotion and eviction](#promotion-and-eviction) · [Structural invariants](#structural-invariants) · [The compression floor](#the-compression-floor)

## The two files

**The split is by content class, not by precedence.** Because the two files never hold the same kind of claim, they cannot contradict each other on the same claim, and there is no arbitration rule to get wrong.

| | `../memory/shared.md` — portable | `../memory/local.md` — this machine |
| --- | --- | --- |
| Holds | rules that would hold on any machine: topology lessons, ratios, discount factors, failure recognisers | absolute costs, bands, run rows, confirmation counts and dates, harness version stamp, watch list |
| Carries per entry | rule, qualifier, recogniser, strength band, falsifier | numbers, counts, dates, provenance |
| Written by | `/sage-promote`, on the user's word only | every run, automatically |
| Read at | Step 2, before estimating | Step 2, before estimating |
| Physical form | one copy, in the repo, symlinked into every install — a write lands in `<repo>/sage-claude/memory/shared.md` and shows in `git status` | a real file on this machine, seeded once, never overwritten |

A rule earns three homes in order, one content class each: `local.md` holds its counts and dates, `shared.md` holds the rule with its recogniser and falsifier, and skill text carries the clause — with its qualifier and the recognising anecdote where the compression floor demands them — tagged `(calibration: <band>)`. No home restates another home's bookkeeping: counts and dates stay local, recogniser and falsifier stay in `shared.md`.

**A dangling `shared.md` symlink → run on `local.md` alone and print one line saying so.** The repo moved or was deleted. Do not guess a repo path, and do not write a replacement file: a second physical copy is the fork this design exists to prevent.

**The residual case.** A local run contradicting a portable rule does **not** overturn that rule. Write a watch-list row in `local.md` whose `Contradicts` cell names the rule (`## Append` below has its columns and its anchor — they are not the Run-log row's); the row needs its own confirmations, and it appears in the next hint as a **retirement candidate**.

## Append

Automatic, every run, at Step 6, to `local.md` only. A run touches the file in exactly four ways: the **Run-log row** it owes every time; a **new Watch-list row** when it has one — the residual case above orders one, and a lesson seen once, a skill defect, or a task class with no coverage are the others; and a **confirmation of a Watch-list row that already exists**, which raises that row's `Count` and extends its `First → last` in place — or, where the row was **under-counted when it was filed**, a *correction*, which is the same edit with a different justification and must say so in the cell: name the observations that were already in the row's own text and the date they were re-read. A correction may widen `First → last` **backwards**, because it is recording evidence that always existed rather than evidence a run just met. Both are the same act; conflating them is not, because a trigger firing on a corrected count is firing on a re-reading, and a reader is owed that distinction in the row rather than filing a second row for the same observation; and the **closure of a Watch-list row this run settled**, which `### The closure act` below defines and which is the only act that takes a row *out* of circulation. That third act is what makes the counts mean anything: `## The hint` fires on a count reaching three, so an observation filed as three separate `Count 1` rows fires nothing, ever — and the fourth is what stops the table growing for ever. Everything else in the file — Bands, Rules, `Promoted` cells, the harness stamp — changes through consolidation (`## Consolidate`) or `/sage-promote` (`## Promotion and eviction`), never through an append.

The two row kinds live in different sections and take **different anchors**. Using one kind's anchor for the other is the failure this section exists to prevent.

**The Run-log row** — date, task class, agents, est, actual, wall clock, note — **including the runs where the estimate held**, because a band you can trust needs its hits recorded next to its misses. Write the note so Step 2 can act on it: "fetch-heavy research runs 70–120k per agent" is usable at plan time; "unit 3 was expensive" is not.

**Anchor the Run-log row on the file's final characters, never on a date cell.** The Run log is the last section by construction, so "append at the end of the file" stays correct however the file grows; an anchor on a date matches the wrong row the first time two runs share a day.

**The Watch-list row** — observation, `Kind`, `Count`, `First → last`, `Contradicts`, `Class`, `Promoted`, `Status`, the eight columns `## Structural invariants` fixes. An empty `Contradicts` is written `—`, never blank and never "none", and an unpromoted row's `Promoted` is `—` the same way.

**`Class` and `Promoted` are on this table for one reason: without them a watch row can never become a rule.** They are the same two columns the Rules table carries, holding the same values and read by the same triggers — `Class` is `portable` (would hold on any machine) or `local` (this machine's measured behavior); `Promoted` is an append-only history joined with ` · `, never overwritten, exactly as `/sage-promote` already writes one. A row filed without them is filed outside the promotion path, which is the failure this table spent twelve runs demonstrating: the `→ shared.md` trigger tests both, the Watch list had neither, so no watch row could ever evaluate the trigger and none ever graduated. `Promoted` is also the only place a `refused <date>` can sit — a refusal recorded in `Status` instead would close the row, and a refused candidate is not closed, it is ineligible until newer evidence arrives.

**`Kind` is one of exactly four values, and the protocol names them here** because a value only the data file's own prose knows is a value no trigger can key on:

| `Kind` | The row records | Where it ends |
| --- | --- | --- |
| `lesson` | something a run learned that would change how a later run acts | the `→ shared.md` trigger, once it reaches three confirmations — the only `Kind` that trigger accepts |
| `contradiction` | a local run cut against a `shared.md` rule, named in `Contradicts` | the `→ retirement` trigger, on its second confirmation; it never overturns the rule on its own |
| `defect` | a fault in sage's own corpus, scripts, or protocol | `/sage-promote`'s corpus-repair stage, which fixes the corpus and closes the row |
| `gap` | a task class, a rate, or a behaviour with no coverage yet | the measurement lands and the row is closed against it — a `gap` is a programme of work, never a rule, so it is not promotable |

**When two `Kind`s both fit, choose by what would close the row, not by what it is about.** If closing it means editing sage's own corpus or scripts, it is a `defect`; if closing it means three confirmations and a promotion, it is a `lesson`. The tiebreak is load-bearing rather than tidy, because only `lesson` reaches `→ shared.md`: a row filed `defect` when a rule was what travelled is a rule that can never graduate, and one filed `lesson` when a repair was what was needed is a repair nobody owns. A row that genuinely needs both gets two rows, each with its own closure.

**Anchor it on the last row of the Watch-list table, as the very next line, with no blank line between.** Two ways to get this wrong, and neither is visible in the row you just wrote. The end-of-file anchor above belongs to the Run log **alone**: reach for it here and the row is filed as a run row, in the wrong table, under the wrong headers — and nothing complains, because `## Structural invariants` checks *header* rows and never data-row widths — a misfiled row of any width sits in the wrong table undetected. Do not read a column count as a safety net here: it never was one, and since the Watch-list row grew to eight cells against the Run log's seven, the two are no longer even different lengths in the direction that would make a stray row look odd to a human reader. The blank line is the other way: a blank line **ends** a markdown table, so a row set one line below becomes a second, header-less table, which breaks `## Structural invariants`' requirement that `## Watch list` hold exactly one table and halts the next consolidation pass. That one is not hypothetical — this machine's `local.md` was damaged exactly that way on 2026-08-18, and nothing noticed for a day, until a consolidation pass aborted on it.

**So measure every section you touch, before and after.** An append is not done when the row is in the file; it is done when the row is in the *table*. Take the before reading of every section you intend to write to **before you write anything** — one command, once per section per side:

```sh
awk -v s='Watch list' '$0=="## "s{i=1;next} /^## /{i=0} i&&/^\|/{if(!b)n++;b=1;r++;next}{b=0} END{print n+0, r+0}' ~/.claude/skills/sage/memory/local.md
```

It prints **blocks and lines** for that one section. Swap `Watch list` for `Run log` for the other. Read it this way:

- **Before you write, blocks must be `1`.** Anything else means the file is *already* damaged and your anchor does not exist — "the last row of the table" is undefined when there are two tables, and appending to the literal last row grows the damage instead of adding to it. Do not write to that section — and stop only on that section. The other section's row is still owed, so write it, and surface the damage as a Step 6 event (`../SKILL.md`, Step 6, surfaced events). Halting the whole append instead would cost the run its Run-log row, which the budget rail and every later estimate read back, so a damaged Watch list would quietly bleed the run log dry. Pre-existing damage is not an appender's to fix.
- **After you write, blocks must still be `1`, and the line count must have moved exactly as your acts predict, summed — `+1` per new row of either kind, and `0` for a confirmation, a correction, or a closure written in place.** Three of the four acts move no line at all, so a zero delta is the *expected* reading for all but a new row; the check that catches a lost in-place edit is the row's own content, not this count. Blocks `2` is the blank line. A new row that leaves the count unchanged never reached this table: look in the other section, and immediately below this one. A confirmation that moves the count is not a confirmation — you have added a row, and a duplicate row is the thing the third act exists to prevent.
- **`0` is never healthy and never means "the row missed the section".** A well-formed section always has a header and a separator, so an append cannot drive this to zero: `0` means the heading is not byte-for-byte `## <section>`, or the file has CRLF endings. Empty output with a non-zero exit is a different fault again, and the likeliest one: the path is wrong.

**Record both readings.** The check leaves no trace today, which is why no run on this machine can show it ever ran one — the only guard standing over every memory write has no audit trail at all. Write the pair for every section you touched into the run's ledger `### Run record`, one line per section, as `<section>: <blocks> <lines> → <blocks> <lines>`. Two readings and one line of arithmetic are the whole cost. A run that cannot show the pair did not run the check, and "I ran it" is not the evidence — the numbers are.

Where more than the append is in doubt, run the whole `## Structural invariants` check.

### The closure act

**Nothing used to take a row out of `watching`, and that is why every counter here only ever grew.** Eighteen of nineteen rows sat at `watching`; the one that had left was set by hand, with no rule authorising it. A trigger reading a table nothing ever drains fires forever, so closure is not tidiness — it is the half of the loop that makes the other half mean something.

`Status` holds one of four states. **The state is the first word of the cell**, which is what makes it machine-readable: the rest of the cell is free payload, and live rows already carry it (`watching (run 6/10: hosted ~60 min over 8 dispatches …)`). Never test the cell for equality; test its first word.

| `Status` | Means | Written by | Evidence it needs |
| --- | --- | --- | --- |
| `watching` | live and accumulating; the filing default | any run | none — this is where a row starts |
| `settled → <artifact>` | the question the row asked has an answer, **and that answer is recorded where a future run will read it** | a run, at Step 6, **only for a row that same run settled**; and `/sage-promote` stage zero, for a `defect` row its own repair closed | the cell names the artifact: a Bands row, a Rules row, a corpus file and section, or a `shared.md` rule |
| `promoted → Rules row "<name>"` | the row graduated into the rule set | `/sage-promote` stage one only | the named Rules row exists, and `Promoted` carries `shared <date>` |
| `dropped → <reason>` | no longer worth watching: its subject is gone, or another row supersedes it | `/sage-promote` only — stage zero for a `defect` row whose subject was removed, stage one for a candidate another row supersedes | the cell names the superseding row, or what was removed |

Three rules keep the act honest:

- **A run may only close what that run settled.** Closing a row on the strength of reading it is how a watch list gets emptied by a run that measured nothing. If you did not produce the artifact, the row stays `watching`.
- **`settled` requires the artifact to exist, not to be intended.** `settled → Bands row X` is a claim one grep checks, and the point of naming it is that a later reader can check it. **Building the mechanism a row complained about is not the same as settling the row**, and the difference is the whole of this rule: a row recording that some table has never gained an entry is settled when an entry lands, not when the code path that could produce one is written. Closing it early hides the only instrument that would have shown the path still does not work. This one is not hypothetical — the run that wrote this clause made exactly that mistake, closed such a row against a step that had never executed, and a refuter pointed at this sentence to overturn it.
- **A row whose state is not `watching` is invisible to every hint trigger**, and `## Consolidate` may move it to the archive. That is the decrement: closure marks a row dead, consolidation carries it out, and the row count finally falls. **A closed row still counts toward the consolidation trigger until that pass runs, and deliberately so** — the trigger firing is what causes the pass that drains it. Excluding closed rows from the count would let closure silence the trigger and leave every closed row in the table for ever, which is the failure this section exists to end, reintroduced one level up.

**If your own write is what broke it, revert it — do not repair it in place.** Restore the file to its pre-append state and append again correctly. That is deliberately narrower than repair, and the narrowness is the point: "Do not repair the file" in `## Structural invariants` is a rule about a writer that cannot be trusted to see damage it caused itself, and an appender holding a check with two known blind spots is exactly that writer. Undoing your own change needs no such judgment. If the check still fails after the revert, the damage predates you — surface it and stop.

## Consolidate

Automatic when a trigger below holds, **at the start of a run, before `../SKILL.md` Step 2 reads memory**, on `local.md` only. That placement is the whole invoker — nothing else calls this pass, which is why a consolidation trigger raised at Step 6 clears at the next run's Step 2 instead of reprinting its hint forever, and why Step 2 never prices off unmerged rows. Rewrite Run-log rows into Bands and Rules, and move out every Watch-list row whose `Status` no longer begins `watching` — settled, promoted or dropped, its work already recorded elsewhere by the act that closed it. Then move every consolidated original, verbatim, into `local-archive.md` beside it, each tagged with why it left — retired, compressed, or closed. **Closed watch rows are the Watch list's only drain**, and without this half the closure act above changes no count in this file. That archive first exists when the first pass runs, and Step 2 never reads it; it exists so one grep settles a rule's provenance.

Two checks guard the write. **Both must pass, or the pass aborts and writes nothing** — no partial result, no question to the user. A human approving a diff is not this safeguard: the one recorded corruption on this machine landed *through* an approved diff and was found later by a check.

1. **Self-check.** Every pre-pass row survives verbatim in exactly one place — **its own section or the archive** — and the count of survivors equals the pre-pass row total, since a compressed row's one-line summary is a pointer, not a survivor, and a closed watch row survives in the archive rather than in the Watch list; every band cites at least one run; every rule carries at least one date; the result is smaller than what it replaces; both files parse as markdown.
2. **Structural invariant check**, against the section below.

A pass that produced no change reports `nothing to consolidate` and ends, writing nothing and running neither check — so a second pass straight after a first proposes nothing.

## The hint

Sage detects, prints one line, and stops. **Promotion is never automatic**; the user runs `/sage-promote`.

```
sage: 3 rules ready → shared, 1 → skill text, 1 retirement candidate. Run `/sage-promote`.
```

| Target | Trigger |
| --- | --- |
| → `shared.md` | **A Rules row** reaches 3 confirmations, is marked machine-independent, is not already in `shared.md`, and its `Promoted` cell either records no `retired` or the Rules row's last-confirmation date is newer than that `retired` date — a retired rule re-qualifies only on evidence dated after its retirement, never on its old count. **A Watch-list row** qualifies on the same shape read from its own columns: `Kind` is `lesson`, `Count` reaches 3, `Class` is `portable`, `Status` begins `watching`, and `Promoted` records no `refused` dated later than the row's last confirmation |
| → skill text | A rule in `shared.md` reaches 6 confirmations and its `Promoted` cell does not yet record `skill` or `refused`, or a rule's count-derived band (the thresholds in `shared.md`'s header) disagrees with its block's `- Band:` field — a crossing: `/sage-promote`'s stage one re-writes the field, its stage two re-tags wherever skill text cites it |
| → retirement | A rule's falsifier condition was observed, or two confirmations contradict it |
| → model lineup | The harness stamp in `local.md` is older than the build `claude --version` reports, or a Watch-list row records a `message.model` value absent from `harness.md`'s tier snapshot table |
| → consolidation | `local.md` past ~10k tokens, or 40 **non-pointer data rows**, or two rows disagree on one band, or structural damage, or a version-bound claim older than the recorded harness version |

Every trigger reads `local.md`'s Rules and Watch list tables — `Count`, `Class`, `Contradicts`, `Promoted`, and `Rule` matched by name against `shared.md`'s `##` headings — plus, for a band crossing, the matched block's `- Band:` field, and, for the lineup trigger alone, one `claude --version` read and one scan of Watch-list text for recorded `message.model` values against the snapshot table's names. All are machine-checkable with no judgment, so a hint that fires is a fact rather than an opinion.

**The watch-row clause needs no name match, and that is deliberate.** A Rules row is matched against `shared.md` by name because it has one; a watch row holds an observation paragraph instead, so "is not already in `shared.md`" needs no test — a row still on the watch list is by definition not yet a rule. Naming it is judgment, and judgment belongs to `/sage-promote`, which mints the rule name when it promotes the row. **`Kind` must be `lesson`** because the other three are not rules: a `gap` is a programme of work, a `defect` is a repair job, and a `contradiction` routes to `→ retirement` instead. Dropping that condition is how a measurement programme gets promoted as though it were a lesson. The lineup hint is deliberately best-effort — it sees a new build and a new name, never a price or window change behind an unchanged name; `/sage-promote` stage three's unconditional vendor-docs read is what covers that gap when it runs.

**A pointer is not a data row, and that one word is what lets this count fall.** The compression act `## Consolidate` prescribes rewrites a Run-log row to a one-line pointer into `local-archive.md` — and a pointer counted as a row moves the total by zero, so a trigger reading "40 rows" re-fires on every run after the pass that was supposed to clear it. Measured here: a pass that archived six rows verbatim and left six pointers shrank the file 26,749 → 26,320 bytes and moved the row count by **nothing**, and two separate runs filed the observation before anything acted on it. A **pointer row** is a Run-log row whose `note` cell begins ``Compressed → `local-archive.md` ``; every other data row in any of the four tables counts, and header and separator rows never do. One command settles the number:

```sh
awk '/^## /{s=$0} /^\|/ && !/^\| *---/ && !/^\| (date|Class|Rule|Observation) \|/ {
  if (s=="## Run log" && /\| *Compressed → `local-archive\.md`/) next
  t++ } END{print t+0}' ~/.claude/skills/sage/memory/local.md
```

It matches a **cell that begins** with the pointer string, inside the **Run-log** section only — which is what the sentence above defines, and not the whole line: the looser test drops any row that merely *quotes* the pointer string, and the Watch list already holds a row discussing this very trigger. Measured on a fixture carrying one such row, the loose test returned 56 where the correct answer was 57 — under-counting, which is the direction that silently disarms the trigger this fix exists to arm. It matches on the cell boundary rather than splitting the row into fields, because a note cell may legitimately contain an inline `|` inside backticks and a field-index approach miscounts the moment one does. **The path here and in the append check above is the installed file; substitute it when working on a copy.**

Counting any other way does not make the trigger stricter, it makes it dead: a hint that fires on every run carries no information about any run. The threshold is deliberately not the only half that can move — closure plus archival is what drains the Watch list (`## Append`, the closure act, and `## Consolidate`), and without a falling count this trigger is a light with no switch.

## Promotion and eviction

Both belong to **`/sage-promote`**, a separate skill, on the user's word only. A run never loads
the procedure it will not run: a run's whole duty is the hint above — detect, print one line, stop.

`/sage-promote` reads this file for three things and writes none of it: the triggers above, which
tell it what its candidates are; `## Structural invariants` below, which its preflight checks
`local.md` and `shared.md` against; and `## The compression floor` below, which bounds what its
corpus edits may remove. It writes `shared.md`; the `Promoted` cells, watch-list rows, harness stamp and one
run row in `local.md`; `local-archive.md`; and — at its zeroth, second and third stages — sage's own
corpus, its `bin/*.sh` scripts, and the model lineup's agent sources, repo and installed.

Eviction is the same skill's, for the same reason: a rule whose `Falsifier` fires leaves
`shared.md` **with the observation attached**, and any skill text citing its band comes out with
it. A falsifier firing surfaces as a hint line like any other. It never rewrites `shared.md` on
its own.

## Structural invariants

This section is the contract the invariant check tests against: a check written from this section and nothing else is a complete check. The repo's `../memory/local-seed.md` — what the installer copies once to create `local.md` — is a file that satisfies every marker below, so it doubles as the worked example and as the check's own fixture.

**`local.md`** — the sentinel, then these `##` sections in this order, none missing, none repeated, no other `##`:

1. Line 1 is exactly `<!-- sage-local-memory v2 -->` and line 2 is exactly `# Sage local memory`. **v2 (2026-08-20) added `Class` and `Promoted` to the Watch-list table**; a `local.md` still reading `v1` has a six-column Watch list, fails marker 5 below, and must gain the two cells in every row before any pass will run on it — which is exactly what the installer's drift notice exists to announce, and why the sentinel had to move with the format rather than after it. This is the **header sentinel**; absent, the file is not sage local memory and the pass aborts before reading further. **The installer greps this line** — `sage-local-memory` — rather than diffing the header, so consolidation must carry it through verbatim. Comparing anything sage itself is licensed to rewrite would latch the drift notice on permanently; a sentinel that moves only when the format really moves lets the notice go quiet the moment the answer is yes.
2. `## Harness version stamp`, holding exactly one line matching `^sage-harness-stamp: `. Consolidation carries that line through unchanged and on one line, because the version-bound consolidation trigger above compares against it — a rewrite that drops or reflows it disarms that trigger with nothing to show for it.
3. `## Bands`, holding one table, header row exactly `| Class | Figure | Qualifiers | Evidence |`.
4. `## Rules`, holding one table, header row exactly `| Rule | Count | First → last | Provenance | Class | Promoted |`.
5. `## Watch list`, holding one table, header row exactly `| Observation | Kind | Count | First → last | Contradicts | Class | Promoted | Status |`. `Class` and `Promoted` sit in the same order they take in the Rules table above, immediately before this table's own state column, because the promotion triggers read the two tables with one rule and a column order that disagreed between them would be a second rule to keep in step.
6. `## Run log`, holding one table, header row exactly `| date | task class | agents | est | actual | wall clock | note |`, and it is the **last section in the file** — that is what makes the append's end-of-file anchor correct.

**`shared.md`** — a header block, then one rule per `##` block and nothing else at `##`. Every block carries exactly five fields in this order: the **rule** as a bold sentence on the first non-blank line under the heading, then four list items beginning `- Qualifier:`, `- Recogniser:`, `- Band:`, `- Falsifier:`. `Band` is one of `established`, `recurring`, `provisional`. No date, no confirmation count and no absolute cost appears anywhere in the file; ratios and discount factors do, because the skill computes with them.

**On failure: abort, write nothing, and surface one line** naming the marker that failed and the file it failed in. Do not repair the file — a rewriter that repairs the shape it is validating against cannot detect the damage it caused itself.

**Its blind spot, stated so you compensate for it: this check catches structural damage, never a wrong rule.** A perfectly shaped file full of false bands passes every marker above. Falsifiers and eviction are the only defence against that second failure, and they run on the user's word rather than on a check.

## The compression floor

Never removed under any "make it shorter". A cut that changes what a fresh instance does is a spec change, not compression.

- The **undated anecdote** that makes a rule recognisable in the wild.
- Any **number the skill computes with** — a ratio, a band, a boot cost, a discount factor.
- A rule's **qualifier**.
- The **literal command** that satisfies it.
- The **completion criterion**.
- A **precedence sentence** wherever two rules can both fire.
- The **strength band**.
- Whether a constraint **binds or is merely asked for**.

Cut past the floor and a rule breaks in a known order: the trigger word goes, so it fires on everything or on nothing; the literal command goes, so "verify" is satisfiable by asking a second model, which is the failure rather than the fix; the anecdote goes, so the rule has no shape left to match against; the band goes, so it can no longer be traded off against anything.
