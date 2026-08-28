# Memory protocol

Your job here: read the knowledge items your task matches at Step 2, and append plain lines to the journal at Step 6 — nothing else. A run never edits a knowledge-item file, never bumps a count, never consolidates. Every structured write belongs to `/sage-promote`, on the user's word. Read this at Step 2 before estimating, and again at Step 6 before appending.

[The shape](#the-shape) · [Knowledge items](#knowledge-items) · [The journal](#the-journal) · [Read at Step 2](#read-at-step-2) · [Append at Step 6](#append-at-step-6) · [The hint](#the-hint) · [Promotion, consolidation, eviction](#promotion-consolidation-eviction) · [Structural invariants](#structural-invariants) · [The compression floor](#the-compression-floor)

This is the v3 protocol. v2 kept the machine's knowledge in two table-structured files that every run edited in place, and the record is unambiguous about how that ended: blank-line splits, glued rows, misfiled appends, a consolidation pass that could only abort — six distinct corruption classes across two machines, every one produced by an LLM hand-editing a strict-format table mid-run. v3 removes the failure class instead of guarding it: **a run's only write is an append of plain lines, and there is no table to break.** Design: the source repo's design notes under `docs/designs/` — the 2026-08-27 sage-memory-v3 note, cross-machine half revised by the 2026-08-28 clone-model note.

## The shape

Two kinds of text, two ownership rules:

- **Cortex** — `../SKILL.md`, `references/`, `bin/`: the protocol itself. Hand-owned. Changed only by `/sage-promote`'s gated stages or by build-authoring on the user's explicit word. No run and no consolidation touches it.
- **Knowledge items and the journal** — everything under `memory/`. Perishable, modular, statistical. A run reads KIs and appends journal lines; `/sage-promote` does every other write.

The `memory/` layout, installed:

| Path | Holds | Written by |
| --- | --- | --- |
| `memory/shared/` | the **clone**: a real directory, one file per **portable** KI — rules that hold on any machine, rule text only, nothing machine-specific. The authoritative copy is the **template**, `<repo>/sage-claude/memory/shared/` | the installer's sync (template → clone) and `/sage-promote`'s landing step — nothing else, ever |
| `memory/source-repo` | one line: the absolute path of the repo the clone came from. `/sage-promote` resolves `<repo>` from it; a run never needs it | the installer, rewritten on every run |
| `memory/local/` | one file per **machine-local** KI: cost bands, stats sidecars for shared KIs, lessons, gaps, defects, contradictions, the harness stamp | `/sage-promote` only |
| `memory/journal.md` | append-only plain lines: run actuals, observations, KI usage | **every run**, at Step 6 — the only file a run writes |
| `memory/archive/` | drained journal segments, archived and retired KIs, superseded format versions, clone files the installer's sync retired | `/sage-promote`, plus the installer's sync when a template retirement removes a clone file |

**The split is by content class:** counts, dates, uses, absolute costs and the strength band stay per-machine in `local/`; rule text, qualifiers, recognisers and falsifiers live in the template and reach the machine as its clone. A count in a shared file would fork across machines — machine B, having seen less, would write the number back down in a clean edit no merge catches — which is why tracking never enters the template, and why the seed ships no stats sidecars: a sidecar is pure tracking, minted zeroed on the machine at first use.

**The template carries no `band:` — a band is calibration a machine earns, so it lives only on the machine.** A shared KI's strength band sits on its stats sidecar in `local/` (`band:`, optional; absent reads `provisional` until a pass writes it), raised by this machine's own counts through `/sage-promote`'s crossing — a `local/` write, no template byte, no landing step. The one place a band is shared is the skill-text `(calibration: <band>)` tag, and it records the highest band any single machine's counts have earned: raises only — a machine whose own band sits below the tag has seen less, which is never counter-evidence. Downward movement belongs to eviction and to the user, only. (Design: the clone-model note in `docs/designs/` — the recorded failure was one rule's shared band flipping five times across two machines, each pass locally correct under its own reading. The first fix kept a template `band:` under a highest-earned merge rule; the user cut the field instead: tracking never enters the template.)

**A missing or empty `memory/shared/` → run on `local/` and the journal alone and print one line saying so.** The fix is `install.sh`, which syncs the clone from the template; do not hand-create files there. The clone has exactly two writers — the installer's sync and `/sage-promote`'s landing step. Anything else that lands in it is overwritten, after a backup, at the next sync: the template always wins.

**The editing test, for a fact that could sit in more than one place.** It governs every corpus file, not only `memory/`:

- **Skill text carries the clause and the anecdote that makes it recognisable** — never the arithmetic behind it, which is what `(calibration: <band>)` stands in for. A rule earns three homes in order, one content class each: the stats sidecar in `local/` holds its counts, dates and this machine's band, the shared KI holds the rule with its recogniser and falsifier, and skill text carries the clause tagged `(calibration: <band>)`. No home restates another home's bookkeeping.
- **Harness facts go to `harness.md`, with their measurement, their date and their population.** That file is the declared home for corpus statistics and is exempt from the rest of this test: its dates are deliberate, because a standing instruction to re-measure before quoting is only meaningful when a reader can see how old the figure is.
- **Counts, dates and absolute costs go to `local/` or the journal.**
- **A number survives in skill text only where the sentence's purpose is to stop a run using it.** An anti-band — one observation, warning a reader off pricing from it — loses its whole point once the provenance is stripped, so that sentence keeps its figure.

**And a pointer must resolve on the machine that reads it.** `local/` and the journal are per-machine, so skill text may point at the *shape* of what lives there — "append the run line, hits included" — and never at a specific KI, figure or date only the authoring machine ever had. `memory/shared/` and everything under `references/` are identical on every install and may be cited precisely. Cite a KI by its `id:`, never by a line number — promote moves files to `archive/` on its own schedule, and where a deliverable quotes one, say in the deliverable that these files are live.

## Knowledge items

One file per KI. Frontmatter between `---` fences — one `key: value` per line, no tables — then a markdown body. A malformed KI file quarantines that one KI (skip it, surface one line); it cannot damage its neighbours, which is the point of the one-file grain.

**Portable KI** (`shared/<slug>.md`): `id`, `kind: rule`, `class: portable`, `status`. Body: the **rule** as a bold sentence, then `- Qualifier:`, `- Recogniser:`, `- Falsifier:` list items. No band, date, count or absolute cost anywhere in the file; ratios and discount factors yes, because the skill computes with them. The rule's strength band is machine tracking and lives on its stats sidecar (below).

**Local KI** (`local/<file>.md`), seven kinds:

| `kind` | file name | records | ends when |
| --- | --- | --- | --- |
| `stats` | `<slug>.stats.md` | this machine's numbers for the shared KI its `for:` names — `count`, `first`, `last`, `provenance`, `band` (this machine's strength band), `promoted` (append-only ` · ` history), `uses`, `last-used`, `misses` | the shared KI retires |
| `band` | `band-<slug>.md` | a cost band: class of work (`name:`), figure, qualifiers, evidence | superseded by a newer band, or retired on recorded misses |
| `lesson` | `lesson-<slug>.md` | something a run learned that would change how a later run acts | promotion to `shared/` at three confirmations — the only `kind` the → shared signal accepts |
| `gap` | `gap-<slug>.md` | a task class, rate or behaviour with no coverage yet — a programme of work, never promotable | the measurement lands and promote settles it against the artifact |
| `defect` | `defect-<slug>.md` | a fault in sage's own corpus, scripts or protocol | `/sage-promote`'s corpus-repair stage fixes the corpus and settles it |
| `contradiction` | `contradiction-<slug>.md` | a local run cut against a shared KI, named in `contradicts:` | the retirement signal, on its second confirmation; it never overturns the rule on its own |
| `stamp` | `harness-stamp.md` | the `sage-harness-stamp:` line and its verification prose | never — re-dated by every promote pass |

**The field contract by kind — these are the fields the promotion signals read, so they are load-bearing, not decoration.** A `lesson`, `gap`, `defect` or `contradiction` file carries `class:` (`portable` or `local` — the → shared signal accepts only a portable lesson), `count:`, `first:`, `last:`, and `promoted:` (the append-only ` · ` history, `—` when empty); a `contradiction` also carries `contradicts:` naming the shared KI id. A `stats` file may carry `band:` — this machine's strength band for the rule its `for:` names: `established` (six or more confirmations), `recurring` (three to five), `provisional` (below bar). The field is optional; **absent, it reads `provisional`** — a band no pass has assessed yet, whatever the count says, so the next pass's crossing can fire and materialize the field (a Step 2 reader weighing an unassessed rule reads the sidecar's `count:` directly). Only `/sage-promote` writes it — set from the count when stage one mints the sidecar at promotion; consolidation's lazy mint writes no band; the crossing rewrites it — and only upward: counts only accumulate, and downward movement is eviction's or the user's. A `band` file carries `name:` — the class of work as verbatim prose, because a slug is not a name and a qualifier like "≤10k words" must survive somewhere live — with its figure, qualifiers and evidence in the body. **Every local KI carries `created:` and `last-used:`**, in every `kind`, bands and the stamp included — the two dates the disuse notice reads (`/sage-promote`, `## The stale notice`). `created:` is the date the KI was filed and never moves again; `last-used:` is the date a run last cited it, `—` until one does. Neither is legal on a file under `shared/`, which carries no date at all: a shared KI's dates are machine-specific and live on its stats sidecar, the same fork the count split exists to prevent. **The two remaining usage fields — `uses:` and `misses:` — stay optional, and an absent one reads as zero**; `/sage-promote`'s consolidation bumps `uses:`, `misses:` and `last-used:` from the journal's `use` lines. It never touches `created:`, which is set once at filing. A KI filed before these fields existed carries `created: —`, which reads as *age unproven* and never as *old*. **`reconciled:` is the migration-debt stamp** — one date, written by `/sage-promote`'s consolidation step 2 to every local KI it has walked, whether or not the walk found anything. It is what stops a one-time archive reconciliation running twice and double-counting, so a KI carrying it is skipped there for ever. **A seeded KI carries its authoring date, not its install date**, so a fresh install more than three months old will see its whole seed corpus in the first stale notice — correct rather than noisy, since the notice removes nothing and clears itself as the machine starts citing them.

**Neither date can remove anything, and that is the point of recording them.** Age and disuse are reported, never acted on — the removal bar below is the whole of what takes a KI out of the corpus.

**When two `kind`s both fit, choose by what would close the KI, not by what it is about.** Closing it means editing sage's own corpus or scripts → `defect`; closing it means three confirmations and a promotion → `lesson`. The tiebreak is load-bearing: only `lesson` reaches `shared/`, so an observation filed `defect` when a rule was what travelled is a rule that can never graduate. One that genuinely needs both gets two KIs, each with its own closure.

`status` is machine-readable by its **first word**: `live`, `watching` (the filing default for lesson/gap/defect/contradiction), `settled → <artifact>`, `promoted → <shared KI id>`, `dropped → <reason>`, `retired → <observation>`, `archived → <reason>` — that last one written **only on the user's word**, after the manual check the removal bar below names, and never by a signal. The rest of the value is free payload. The closure evidence rules are unchanged from v2 and live with their owner: `settled` requires the named artifact to **exist**, not to be intended — building the mechanism a KI complained about is not the same as settling it; the KI settles when the artifact the complaint asked for actually lands. Who may write each state: **a run writes none of them.** A run that settles a KI records a `settle` line in the journal (below); `/sage-promote`'s consolidation flips the status against that line's evidence.

`bin/sage-index.sh` prints one line per KI — `id | kind | class | band | created | last-used | status | <first words>` — from the frontmatter, on demand. A shared row prints `—` in the band column by design: its band is machine tracking, printed on the sidecar's row once a promote pass has written it — `—` there too until one has, and the sidecar's `count:` is the signal in the meantime. `--stale [months]` re-reads the same walk and prints only the KIs unused for that long, oldest first, with a trailing `#` line naming any whose age no date proves. There is no stored index file to go stale.

### The removal bar

**A knowledge item leaves the corpus for exactly two reasons. Being unused is not one of them.**

1. **It was falsified** — its own `Falsifier` fired, or a `contradiction` KI naming it reached two confirmations. `/sage-promote`'s eviction owns this, and it is the only removal any signal may perform on its own.
2. **It records a defect that cannot be fixed, and the user has said so.** No signal reaches this: it takes the manual check in `/sage-promote`, `## The stale notice`, and the user's answer is what licenses the move.

Everything else is **reported and kept**. A KI nothing has cited in months is not evidence the KI is wrong — it is evidence about the runs, which may have solved no problem the KI covers, or may simply have failed to report the citation. The measured case: on 2026-08-28 every shared rule in this corpus read `uses: 0`, including rules at counts of 24, 13 and 12, because the counter had existed for one day. A disuse rule read literally would have archived the entire shared corpus on its first run. **Never lower this bar to give a pass something to write.**


## The journal

`memory/journal.md`. Line 1 is the sentinel `<!-- sage-local-memory v3 -->` — the installer greps it for format drift, so nothing may rewrite it. Then a short fixed header, then payload lines, append-only, newest last:

```
<date> run <session> | <task class> | agents=N est=X actual=Y wall=W | <note>
<date> obs <session> | <kind> <class> | <observation> | falsifier: <...>
<date> obs <session> | confirm <ki-id> | <what happened>
<date> obs <session> | settle <ki-id> | artifact: <...>
<date> use <session> | <ki-id> hit | <ki-id> miss: <why>
<date> mark promote | drained through here by the <date> pass
```

Grammar: `date type session | payload`, types `run`, `obs`, `use`, `mark`. Write one line per fact and never reflow an existing line. A `|` inside payload is harmless — only the first three fields are positional. A malformed line is a question for the next `/sage-promote` pass, never damage.

The `mark` line is promote's drain marker: everything after the last `mark` is what the next consolidation ingests, and the count of those lines is what the hint fires on. Promote's drain always leaves the newest three `run` lines in the live journal — they are Step 2's same-shape pricing rows, the v2 newest-three rule carried over.

## Read at Step 2

1. `bin/sage-index.sh` — the one-line-per-KI index.
2. Open the KI files the task matches: the band KIs for the unit shapes in the plan, the shared rules whose recogniser matches what is in front of you (with their stats sidecars for the counts), any watching lesson/gap/defect/contradiction KI touching the task's area. This is a judgment over the index, not a load-everything rule — the index is what makes selective loading possible, and the `use` line at Step 6 is what makes it honest.
3. The journal tail since the last `mark` — the newest run lines are the same-shape rows pricing wants first (`shared/price-off-a-same-shape-row.md`).
4. Check the two hint conditions (`## The hint`).

**Remember what you loaded.** The Step 6 `use` line names the KIs this run actually read and whether each helped — that line is the entire usage-statistics instrument, and a run that skips it is invisible to the KI review stage that retires dead knowledge. Keep it to one line; ceremony here is how bookkeeping prose dies.

## Append at Step 6

Automatic, every run, to `memory/journal.md` only, via shell append (`>>`) — never by rewriting the file:

- **The `run` line, every run, hits included** — a band you can trust needs its hits recorded next to its misses. Write the note so Step 2 can act on it: "fetch-heavy research runs 70–120k per agent" is usable at plan time; "unit 3 was expensive" is not. A run that handed over adds to this line's note: the handoff note's write cost, each generation's supervision cost, and the generation reached (`../SKILL.md`, `## Handover`).
- **The `use` line** — every KI read at Step 2, `hit` or `miss: <why>`. A `miss` is the KI misleading the run, not the run not needing it; not-needed is simply absent from the line.
- **`obs` lines as earned** — a new lesson, gap, defect or contradiction, with kind and class named, and a falsifier for anything that could one day be a rule; `confirm <ki-id>` where this run re-observed an existing KI (that is what makes counts reach three and mean it); `settle <ki-id>` where this run produced the artifact that answers a KI, naming the artifact — the closure evidence bar from `## Knowledge items` applies to the line, because promote will flip the status on its word.

Then read the tail back — `tail -n 5 memory/journal.md` — and confirm your lines are there, whole, one line each. That is the entire post-append check. There is no table arithmetic, no before-and-after block count, and no revert protocol, because there is nothing an append can structurally break: the failure modes those checks guarded died with the tables.

## The hint

Sage detects, prints one line, and stops. **Promotion is never automatic**; the user runs `/sage-promote`.

| Trigger | Condition |
| --- | --- |
| → `/sage-promote` | the journal holds **≥ 25 payload lines after the last `mark`** (`grep -c` after the last mark line; no mark → count all payload lines) |
| → model lineup | the `harness-stamp` KI's build is older than what `claude --version` reports |

Two, deliberately, where v2 ran five. The promotion, band-crossing and retirement triggers read aggregates — counts against thresholds across every KI — that only `/sage-promote` acts on, so v3 computes them where they are consumed: the pass builds its own slate (its KI-review stage). A run's whole duty is these two lines' worth of checks; both are clearable by the action they call for, which is what makes a hint information rather than noise.

The bar of 25 inherits v2's bar-of-10 economics: each run appends ~2–4 lines, so the hint re-fires within roughly eight to twelve runs even with nothing else accumulating. **Falsifier:** the hint fires on more than half of the next ten runs, or the journal sits past ~60 unmarked lines with the hint fired and no pass run — either reading means the bar is mis-sized; re-derive it from a measured pass, never by moving the number to make a hint go quiet.

## Promotion, consolidation, eviction

All three belong to **`/sage-promote`**, a separate skill, on the user's word only — consolidation included, which in v2 ran automatically at Step 2 and in v3 is the pass's first stage. A run never loads the procedures it will not run.

`/sage-promote` reads this file for three things and writes none of it: the KI shapes and journal grammar above, which tell it what to ingest and mint; `## Structural invariants`, which its preflight checks; and `## The compression floor`, which bounds what its corpus edits may remove. It writes the template (`<repo>/sage-claude/memory/shared/`, landed on the clone in the same pass), `local/`, the journal's `mark` line, `archive/`, and — at its gated stages — sage's own corpus, `bin/*.sh`, and the model lineup's agent sources.

Its KI-review stage is the retirement path that v2 lacked in practice: **recorded misses** are a first-class signal there, beside the fired falsifiers and contradictions v2 already recognised — a miss is the KI misleading a run, which is its falsifier firing in miniature. **Disuse is not on that list and never routes there** (`## Knowledge items`, the removal bar): it produces a notice for the user and nothing else. A rule whose `Falsifier` fires leaves `shared/` **with the observation attached**, and any skill text citing its band comes out with it.

## Structural invariants

The contract the checks test against — a check written from this section and nothing else is a complete check. The repo's `memory/local-seed/` satisfies every **file-level** marker below (the journal sentinel and the KI shapes), so it doubles as the worked example and the fixture for those; marker 4's directories and `source-repo` exist only on an installed tree, where the installer creates them.

1. **The journal**: line 1 is exactly `<!-- sage-local-memory v3 -->` — the header sentinel the installer greps; absent, the file is not sage memory and every pass aborts before reading further. Every payload line matches `^<date> (run|obs|use|mark) ` in shape. A line that does not is surfaced by promote's consolidation as a question, never silently dropped and never "repaired".
2. **Every KI file**: opens with a `---` fence on line 1, closes the frontmatter with a second `---`, and carries at least `id:`, `kind:`, `status:`. `kind` is one of `rule`, `stats`, `band`, `lesson`, `gap`, `defect`, `contradiction`, `stamp`. A file under `shared/` carries `class: portable` and no `band`, `count`, `first`, `last`, `created`, `last-used`, `uses` or absolute cost; a `stats` file carries a `for:` naming an existing shared KI id; a `lesson`/`gap`/`defect`/`contradiction` file carries `class:` and `count:`; a `band` file carries `name:`; and every file under `local/` carries `created:` and `last-used:` (the field contract above lists the rest, and those two fields plus `uses:`/`misses:` are legal on a **local** KI only).
3. **The stamp KI** holds exactly one line matching `^sage-harness-stamp: ` — the lineup hint compares against it, so a rewrite that drops or reflows it disarms that hint with nothing to show for it.
4. **`memory/shared/`**, **`memory/local/`** and **`memory/archive/`** are real directories, and **`memory/source-repo`** exists with a path that holds `sage-claude/memory/shared/`. Only `/sage-promote` needs that path to resolve; a run reads the clone and never the repo.

**On failure: quarantine, never repair.** A malformed KI is skipped and surfaced by name; a broken journal sentinel, or a `source-repo` that does not resolve, aborts the pass that found it. No writer repairs the shape it is validating against — a rewriter that does cannot detect damage it caused itself.

**The blind spot, stated so you compensate for it: these checks catch structural damage, never a wrong rule.** A perfectly shaped KI full of false claims passes every marker. Falsifiers, misses, and eviction are the only defence against that second failure, and they run on the user's word rather than on a check.

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
