# Memory protocol

Your job here: read the knowledge items your task matches at Step 2, and append plain lines to the journal at Step 6 — nothing else. A run never edits a knowledge-item file, never bumps a count, never consolidates. Every structured write belongs to `/sage-promote`, on the user's word. Read this at Step 2 before estimating, and again at Step 6 before appending.

[The shape](#the-shape) · [Knowledge items](#knowledge-items) · [The journal](#the-journal) · [Read at Step 2](#read-at-step-2) · [Append at Step 6](#append-at-step-6) · [The hint](#the-hint) · [Promotion, consolidation, eviction](#promotion-consolidation-eviction) · [Structural invariants](#structural-invariants) · [The compression floor](#the-compression-floor)

This is the v3 protocol. v2 kept the machine's knowledge in two table-structured files that every run edited in place, and the record is unambiguous about how that ended: blank-line splits, glued rows, misfiled appends, a consolidation pass that could only abort — six distinct corruption classes across two machines, every one produced by an LLM hand-editing a strict-format table mid-run. v3 removes the failure class instead of guarding it: **a run's only write is an append of plain lines, and there is no table to break.** Design: the source repo's 2026-08-27 sage-memory-v3 design note.

## The shape

Two kinds of text, two ownership rules:

- **Cortex** — `../SKILL.md`, `references/`, `bin/`: the protocol itself. Hand-owned. Changed only by `/sage-promote`'s gated stages or by build-authoring on the user's explicit word. No run and no consolidation touches it.
- **Knowledge items and the journal** — everything under `memory/`. Perishable, modular, statistical. A run reads KIs and appends journal lines; `/sage-promote` does every other write.

The `memory/` layout, installed:

| Path | Holds | Written by |
| --- | --- | --- |
| `memory/shared/` → symlink into `<repo>/sage-claude/memory/shared/` | one file per **portable** KI — rules that hold on any machine, text and band only, nothing machine-specific | `/sage-promote` only |
| `memory/local/` | one file per **machine-local** KI: cost bands, stats sidecars for shared KIs, lessons, gaps, defects, contradictions, the harness stamp | `/sage-promote` only |
| `memory/journal.md` | append-only plain lines: run actuals, observations, KI usage | **every run**, at Step 6 — the only file a run writes |
| `memory/archive/` | drained journal segments, archived and retired KIs, superseded format versions | `/sage-promote` only |

**The split is by content class, and it is the v2 split preserved:** counts, dates, uses and absolute costs stay per-machine in `local/`; rule text, qualifiers, recognisers, falsifiers and the band stay in the one shared copy. A count in the shared copy would fork across machines — machine B, having seen less, would write the number back down in a clean edit no merge catches — which is exactly why v2 kept them apart and v3 does not reunite them.

**A dangling `memory/shared` symlink → run on `local/` and the journal alone and print one line saying so.** The repo moved or was deleted. Do not guess a repo path, and do not create a replacement directory: a second physical copy of portable knowledge is the fork this design exists to prevent.

**The editing test, for a fact that could sit in more than one place.** It governs every corpus file, not only `memory/`:

- **Skill text carries the clause and the anecdote that makes it recognisable** — never the arithmetic behind it, which is what `(calibration: <band>)` stands in for. A rule earns three homes in order, one content class each: the stats sidecar in `local/` holds its counts and dates, the shared KI holds the rule with its recogniser and falsifier, and skill text carries the clause tagged `(calibration: <band>)`. No home restates another home's bookkeeping.
- **Harness facts go to `harness.md`, with their measurement, their date and their population.** That file is the declared home for corpus statistics and is exempt from the rest of this test: its dates are deliberate, because a standing instruction to re-measure before quoting is only meaningful when a reader can see how old the figure is.
- **Counts, dates and absolute costs go to `local/` or the journal.**
- **A number survives in skill text only where the sentence's purpose is to stop a run using it.** An anti-band — one observation, warning a reader off pricing from it — loses its whole point once the provenance is stripped, so that sentence keeps its figure.

**And a pointer must resolve on the machine that reads it.** `local/` and the journal are per-machine, so skill text may point at the *shape* of what lives there — "append the run line, hits included" — and never at a specific KI, figure or date only the authoring machine ever had. `memory/shared/` and everything under `references/` are identical on every install and may be cited precisely. Cite a KI by its `id:`, never by a line number — promote moves files to `archive/` on its own schedule, and where a deliverable quotes one, say in the deliverable that these files are live.

## Knowledge items

One file per KI. Frontmatter between `---` fences — one `key: value` per line, no tables — then a markdown body. A malformed KI file quarantines that one KI (skip it, surface one line); it cannot damage its neighbours, which is the point of the one-file grain.

**Portable KI** (`shared/<slug>.md`): `id`, `kind: rule`, `class: portable`, `band` (`established` — six or more confirmations, `recurring` — three to five, `provisional` — below bar, carried only because its mechanism is structural), `status`. Body: the **rule** as a bold sentence, then `- Qualifier:`, `- Recogniser:`, `- Falsifier:` list items. No date, count or absolute cost anywhere in the file; ratios and discount factors yes, because the skill computes with them.

**Local KI** (`local/<file>.md`), seven kinds:

| `kind` | file name | records | ends when |
| --- | --- | --- | --- |
| `stats` | `<slug>.stats.md` | this machine's numbers for the shared KI its `for:` names — `count`, `first`, `last`, `provenance`, `promoted` (append-only ` · ` history), `uses`, `last-used`, `misses` | the shared KI retires or archives |
| `band` | `band-<slug>.md` | a cost band: class of work (`name:`), figure, qualifiers, evidence | superseded by a newer band, or retired on recorded misses — bands and the stamp are age-less by design, so the disuse signal never reaches them |
| `lesson` | `lesson-<slug>.md` | something a run learned that would change how a later run acts | promotion to `shared/` at three confirmations — the only `kind` the → shared signal accepts |
| `gap` | `gap-<slug>.md` | a task class, rate or behaviour with no coverage yet — a programme of work, never promotable | the measurement lands and promote settles it against the artifact |
| `defect` | `defect-<slug>.md` | a fault in sage's own corpus, scripts or protocol | `/sage-promote`'s corpus-repair stage fixes the corpus and settles it |
| `contradiction` | `contradiction-<slug>.md` | a local run cut against a shared KI, named in `contradicts:` | the retirement signal, on its second confirmation; it never overturns the rule on its own |
| `stamp` | `harness-stamp.md` | the `sage-harness-stamp:` line and its verification prose | never — re-dated by every promote pass |

**The field contract by kind — these are the fields the promotion signals read, so they are load-bearing, not decoration.** A `lesson`, `gap`, `defect` or `contradiction` file carries `class:` (`portable` or `local` — the → shared signal accepts only a portable lesson), `count:`, `first:`, `last:`, and `promoted:` (the append-only ` · ` history, `—` when empty); a `contradiction` also carries `contradicts:` naming the shared KI id. A `band` file carries `name:` — the class of work as verbatim prose, because a slug is not a name and a qualifier like "≤10k words" must survive somewhere live — with its figure, qualifiers and evidence in the body. **Usage fields** — `uses:`, `last-used:`, `misses:` — may appear on any **local** KI, never on a file under `shared/` (a shared KI's usage is machine-specific, so it lands on the stats sidecar): `/sage-promote`'s consolidation adds or bumps them from the journal's `use` lines, and an **absent usage field reads as zero-uses, never-used, zero-misses** — absence is the ordinary state of a KI no run has cited yet, not damage. `created:` is optional; where present it anchors the disuse signal's age test, and a KI whose age no field establishes (`created:` or `first:`) is exempt from disuse-archiving.

**When two `kind`s both fit, choose by what would close the KI, not by what it is about.** Closing it means editing sage's own corpus or scripts → `defect`; closing it means three confirmations and a promotion → `lesson`. The tiebreak is load-bearing: only `lesson` reaches `shared/`, so an observation filed `defect` when a rule was what travelled is a rule that can never graduate. One that genuinely needs both gets two KIs, each with its own closure.

`status` is machine-readable by its **first word**: `live`, `watching` (the filing default for lesson/gap/defect/contradiction), `settled → <artifact>`, `promoted → <shared KI id>`, `dropped → <reason>`, `retired → <observation>`, `archived → <reason>`. The rest of the value is free payload. The closure evidence rules are unchanged from v2 and live with their owner: `settled` requires the named artifact to **exist**, not to be intended — building the mechanism a KI complained about is not the same as settling it; the KI settles when the artifact the complaint asked for actually lands. Who may write each state: **a run writes none of them.** A run that settles a KI records a `settle` line in the journal (below); `/sage-promote`'s consolidation flips the status against that line's evidence.

`bin/sage-index.sh` prints one line per KI — `id | kind | class | band | status | <first words>` — from the frontmatter, on demand. There is no stored index file to go stale.

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

`/sage-promote` reads this file for three things and writes none of it: the KI shapes and journal grammar above, which tell it what to ingest and mint; `## Structural invariants`, which its preflight checks; and `## The compression floor`, which bounds what its corpus edits may remove. It writes `shared/`, `local/`, the journal's `mark` line, `archive/`, and — at its gated stages — sage's own corpus, `bin/*.sh`, and the model lineup's agent sources.

Its KI-review stage is the retirement path that v2 lacked in practice: disuse (`uses` at zero across passes) and recorded misses are first-class signals there, beside the fired falsifiers and contradictions v2 already recognised. A rule whose `Falsifier` fires still leaves `shared/` **with the observation attached**, and any skill text citing its band comes out with it.

## Structural invariants

The contract the checks test against — a check written from this section and nothing else is a complete check. The repo's `memory/local-seed/` satisfies every **file-level** marker below (the journal sentinel and the KI shapes), so it doubles as the worked example and the fixture for those; marker 4's directories and symlink exist only on an installed tree, where the installer creates them.

1. **The journal**: line 1 is exactly `<!-- sage-local-memory v3 -->` — the header sentinel the installer greps; absent, the file is not sage memory and every pass aborts before reading further. Every payload line matches `^<date> (run|obs|use|mark) ` in shape. A line that does not is surfaced by promote's consolidation as a question, never silently dropped and never "repaired".
2. **Every KI file**: opens with a `---` fence on line 1, closes the frontmatter with a second `---`, and carries at least `id:`, `kind:`, `status:`. `kind` is one of `rule`, `stats`, `band`, `lesson`, `gap`, `defect`, `contradiction`, `stamp`. A file under `shared/` carries `class: portable` and no `count`, `first`, `last`, `uses` or absolute cost; a `stats` file carries a `for:` naming an existing shared KI id; a `lesson`/`gap`/`defect`/`contradiction` file carries `class:` and `count:`; a `band` file carries `name:` (the field contract above lists the rest, and the usage fields are legal on any **local** KI only).
3. **The stamp KI** holds exactly one line matching `^sage-harness-stamp: ` — the lineup hint compares against it, so a rewrite that drops or reflows it disarms that hint with nothing to show for it.
4. **`memory/shared`** is a symlink whose target resolves; **`memory/local/`** and **`memory/archive/`** are real directories.

**On failure: quarantine, never repair.** A malformed KI is skipped and surfaced by name; a broken journal sentinel or symlink aborts the pass that found it. No writer repairs the shape it is validating against — a rewriter that does cannot detect damage it caused itself.

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
