# Sage memory v3 — cortex and knowledge items

**Superseded in part (2026-08-28):** the cross-machine half of this design is revised by `2026-08-28-sage-memory-clone-model.md` in this directory. What changed: `memory/shared` is no longer a symlink into the repo — it is a per-machine clone of the repo's template, synced by the installer; the seed ships **no** stats sidecars; and no shared (template) KI file carries a `band:` field — the band is machine tracking, on the machine's own stats sidecar. Read the symlink and seed-sidecar text below as the dated 2026-08-27 design, not the live mechanism.

## The two problems, restated as requirements

1. **The run-time write path must be too dumb to fail.** Every documented memory corruption — the 2026-08-18 blank-line split, the 2026-08-19 glued rows, the six defects in `2026-08-27-local-md-repair-report.md` (report since removed from the tree; commit eb8c683 in git history holds it) — came from an LLM hand-editing strict-format markdown tables at Step 6 or during consolidation. The guard checks could only abort, never fix, so every incident ended in a by-hand repair. Requirement: a run appends plain lines to a journal and edits nothing else, so the corruption class (a table to break) does not exist on the run path.
2. **Knowledge must stop being a ratchet.** Rules only ever accrued: zero rules ever removed from `shared.md`, retirement reachable only through a lucky contradiction row, no record anywhere of whether a rule was read, applied, or helped. Requirement: every knowledge item carries usage statistics that a human-supervised pass reads, with disuse and misses as first-class retirement signals — not only fired falsifiers.

## Vocabulary

- **Cortex** — the hand-owned, rarely-changing protocol: `sage-claude/SKILL.md`, `references/`, `bin/`. Never touched by consolidation; edited only by `/sage-promote`'s gated stages (stage zero repair, stage two promotion, eviction's cut) or by build-authoring on the user's word. This is what the rough plan called "the most important things that can't be removed" — it already existed; v3 names it and keeps every existing gate on it.
- **Knowledge item (KI)** — one perishable unit of learned knowledge, one file each: a portable rule, a cost band, a lesson, a gap, a defect, a contradiction, a stats sidecar, the harness stamp. Plug = add a file; unplug = archive a file. Git history per KI for free.
- **Journal** — the only file a run writes. Append-only plain lines, no table structure.

## Layout

Repo (`sage-claude/memory/`):

```
shared/               one file per PORTABLE KI (rules today) — the one physical copy
  <slug>.md
archive/
  shared-v2.md        the retired v2 shared.md, verbatim
local-seed/           what the installer copies once onto a fresh machine
  journal.md          sentinel + grammar header + seed run lines
  local/              seed KI files (seed bands, seed lessons, stats sidecars for shared rules)
```

Installed (`~/.claude/skills/sage/memory/`):

```
shared -> <repo>/sage-claude/memory/shared/     directory symlink; one physical copy, git-visible
local/                this machine's KI files, one per KI
journal.md            append-only; line 1 is the v3 sentinel
archive/              drained journal segments, archived/retired local KIs, the v2 files
```

On this machine the v2 files (`local.md`, `local-archive.md`, the `.pre-*` backups) move into `archive/` verbatim — archived, never deleted.

## KI file format

Frontmatter between `---` fences, one `key: value` per line, then a markdown body. No tables anywhere.

Portable KI (`shared/<slug>.md`) — text only, nothing machine-specific, mirroring what v2 `shared.md` held per block:

```markdown
---
id: price-off-a-same-shape-row
kind: rule
class: portable
band: established
status: live
---

**Price a run off a same-shape logged row before reaching for band arithmetic, and name the row in the plan.**

- Qualifier: ...
- Recogniser: ...
- Falsifier: ...
```

Local KI (`local/<file>.md`). Five shapes, telling by `kind`:

| kind | file name | holds | v2 ancestor |
| --- | --- | --- | --- |
| `stats` | `<slug>.stats.md` | this machine's numbers for the shared KI named by `for:` — count, first, last, provenance, promoted history, uses, last-used, misses | a `## Rules` table row |
| `band` | `band-<slug>.md` | class of work, figure, qualifiers, evidence | a `## Bands` table row |
| `lesson` / `gap` / `defect` / `contradiction` | `<kind>-<slug>.md` | the observation, count, first, last, contradicts, class, promoted, status, uses/misses | a Watch-list row |
| `stamp` | `harness-stamp.md` | the harness version stamp line and its prose | `## Harness version stamp` |

Example stats sidecar:

```markdown
---
id: price-off-a-same-shape-row.stats
kind: stats
for: price-off-a-same-shape-row
count: 6
first: 2026-08-15
last: 2026-08-24
provenance: author's log (seed)
promoted: shared 2026-08-17 · skill 2026-08-18 · band established 2026-08-25
uses: 0
last-used: —
misses: 0
status: live
---
```

The v2 cross-machine model is preserved exactly: counts, dates, uses and costs stay per-machine (`local/`), rule text and band stay in the one shared copy. Sage's own band-crossing prose documented why a count in the shared copy forks across machines; v3 does not reintroduce that.

`status` is `live`, `watching`, `settled → …`, `promoted → …`, `dropped → …`, `retired → …`, or `archived → …` — first word is the state, rest is payload, same reading rule as v2. `promoted` keeps the v2 append-only ` · ` history verbatim.

## The journal

Line 1: `<!-- sage-local-memory v3 -->`. Then a short header explaining the grammar. Then payload lines, append-only, newest last:

```
<date> run <session> | <task class> | agents=N est=X actual=Y wall=W | <note — the lesson a future run can act on>
<date> obs <session> | <kind> <class> | <observation> | falsifier: <...>          (kind: lesson|gap|defect|contradiction)
<date> obs <session> | confirm <ki-id> | <what happened>                          (a confirmation of an existing KI)
<date> obs <session> | settle <ki-id> | artifact: <...>                           (this run produced the artifact that settles it)
<date> use <session> | <ki-id> hit | <ki-id> hit | <ki-id> miss: <why>
<date> mark promote | drained through here by the <date> pass
```

Grammar: `date type session | payload`, fields `|`-separated only at the top level the first two fields fix. A malformed line is a question for the next `/sage-promote` pass, never damage — nothing downstream parses the journal except that pass and Step 2's human-shaped read of the tail. Appends go through `>>`; the read-back is `tail`.

**What a run writes, exhaustively:** one `run` line (every run, hits included), one `use` line naming the KIs it actually loaded and whether each helped, `obs` lines as earned. Nothing else. No count bumps, no status flips, no table edits, no consolidation. The `settle` line replaces v2's run-side closure act: the run *records* the settlement it produced; the flip itself is promote's.

**What a run reads at Step 2:** `bin/sage-index.sh` (one line per KI: id, kind, class, band, status, first words), then the KI files whose recogniser or kind matches the task, then the journal tail since the last `mark` line for same-shape pricing. The newest run lines are exactly the same-shape rows Step 2 prices off; promote's drain always leaves the newest three `run` lines in place, mirroring v2's newest-three rule.

**The hint, v3:** two run-side checks only. (1) ≥ 25 payload lines after the last `mark` → `sage: journal has N lines waiting. Run /sage-promote.` (2) the stamp KI's build older than `claude --version` → the lineup hint. Every other v2 trigger — → shared at 3 confirmations, → skill at 6, band crossings, retirement — moves into `/sage-promote`'s own slate-building, because those triggers read aggregates only the pass needs and their run-side versions were measured dead weight. Falsifier on the bar of 25, inherited from v2's bar-of-10 economics: if the hint fires on more than half of the next ten runs, or the journal sits past ~60 lines with the hint having fired and no pass run, the bar is mis-sized — re-derive from a measured pass.

## /sage-promote, v3

Stage order: **preflight → consolidation → stage zero (corpus repair) → KI review → stage one (→ shared) → stage two (→ skill) → stage three (lineup) → eviction**. Everything the pass always did survives; two stages are new.

**Consolidation (new, first).** Read the journal after the last `mark`. For each `obs` line: a new observation → mint a local KI file; a `confirm` → bump the named KI's `count`/`last` (and `provenance` where the confirmation is local); a `settle` → flip the named KI's `status` with the artifact, per the closure act's evidence rule. For each `use` line: bump `uses`/`last-used`, record misses. Then write the `mark` line, move the drained payload lines (all but the newest three `run` lines) verbatim into `archive/journal-<from>-<to>.md`, and truncate the live journal to header + the kept tail. Guards: every drained line survives verbatim in the archive (count in = count out), every touched KI file still parses (frontmatter check), abort writes nothing. This is v2's consolidation moved off the run path into the one human-invoked pass, exactly as the rough plan's item 3 asks.

**KI review (new — the anti-blindness stage).** For every KI, shared and local, read the stats and compute the slate:

| signal | threshold | candidate |
| --- | --- | --- |
| portable `lesson`, count ≥ 3, status `watching`, no later `refused` | v2's → shared trigger, unchanged | promote to `shared/` |
| stats count ≥ 6, no `skill`/`refused` in `promoted` | v2's → skill trigger, unchanged | promote into skill text |
| count-derived band exceeds the shared KI's `band:` | v2's crossing, upward only, unchanged | band raise |
| falsifier observed, or two contradicting confirmations | v2's → retirement, unchanged | eviction |
| `misses` ≥ 2 | new | repair (stage zero, as a minted defect) or retire — judged, with the miss notes as evidence |
| `uses` = 0 and `last-used` older than the last 3 promote passes and the KI older than its first pass | new | archive for disuse |
| `defect` KI, status `watching` | v2's stage-zero candidacy, unchanged | stage zero |

Archiving for disuse moves the file to `archive/` with `status: archived → disuse <date>`, reversible by moving it back — it is the mild end of eviction and takes no refuter, because nothing cited it (that is what `uses: 0` means; the run-side `use` line is what makes the claim measurable). A KI whose text is *cited by skill text* is never disuse-archived while the citation stands — the citation is a use.

**Stages zero through three and eviction** keep their v2 semantics with mechanical substitutions: a Watch-list row → a local KI file; a `shared.md` block → a `shared/<slug>.md` file; a `## Rules` row → a stats sidecar; the cell rule's read-backs become file reads (`awk` over one small file instead of one block of a big one); eviction's step 3 moves the shared file to `archive/` with the observation attached. The write machinery (draft/replace/whole-corpus check/degradation gate/two-copy landing) is unchanged — it guards cortex writes, which have not changed shape.

## The installer

- Fresh machine: no `memory/journal.md` and no v2 `memory/local.md` → copy `local-seed/` contents once (`journal.md`, `local/`). Never overwritten after.
- v2 machine: `memory/local.md` exists, no `journal.md` → print a migration notice (the v2 drift notice's successor): the format moved to v3, the copy is untouched, migrate via the documented steps. Never auto-migrate — the file holds the machine's numbers.
- v3 machine: compare the journal's sentinel line to the seed's, same logic as v2's `drift_memory_sentinel`, pointed at the new carrier.
- `shared`: directory symlink to `<repo>/sage-claude/memory/shared/`, same guard ladder as the v2 file symlink (already-correct / directory-in-the-way / replace-with-backup).
- `memory/` stays excluded from `--delete` sync; `local-seed/` is read from the repo, never installed.

## bin/sage-index.sh

Read-only. Walks `shared/` and `local/`, parses frontmatter with awk, prints one line per KI: `id | kind | class | band | status | <first line of body, truncated>`. Runs call it at Step 2; promote calls it to build the review slate. No stored index file — nothing to go stale, nothing to corrupt. Degrades like the other bin scripts: missing tools → one stderr line, exit 2, callers fall back to `ls` + reading frontmatter directly.

## Migration procedure (any v2/v1 machine)

The reusable form of the migration, distilled from its two executions (the design machine below, and the 2026-08-28 run whose verifier findings shaped steps 2 and 5). It is an agent task, not a script: steps 2–3 need judgment over this machine's actual rows. The installer's v2 notice points here. `<mem>` = the installed `~/.claude/skills/sage/memory/`.

0. **Snapshot first.** `rsync -a <mem>/ <scratch>/mem-baseline/` — the only rollback, since no automatic snapshot covers these files. Precondition: the repo is pulled and `install.sh` has run (the v3 skill and the `shared` directory symlink are in place; the v2 notice is printing).
1. **Read the contract, not this section, for the shapes**: `sage-claude/references/memory.md` — `## Knowledge items` (per-kind frontmatter), `## The journal` (grammar, sentinel), `## Structural invariants` (markers 1–4). Structure exemplars: `sage-claude/memory/local-seed/` (never copy its numbers — they are another machine's).
2. **Map the source before converting.** Grep `<mem>/local.md` for its real section boundaries and row counts; do not trust remembered line numbers. Expect table damage — both executions found it (a blank line splitting a table, rows glued or stranded outside their table). Rows inside the tables convert; row-shaped strays elsewhere stay verbatim in the archive and are surfaced for the next `/sage-promote` pass to adjudicate — never guessed into KIs.
3. **Convert — each datum gets exactly one primary v3 home, numbers carried cell-verbatim:**
   - Rules row → `local/<shared-id>.stats.md` (`for:` the shared KI the rule sentence names; `count`/`first`/`last`/`promoted` from the row; provenance verbatim in the body; `uses: 0`, `misses: 0`, `last-used: —`, `created:` today).
   - Bands row → `local/band-<slug>.md` (`name:` = the class-of-work cell verbatim; figure/qualifiers/evidence in the body). Prose about uncovered classes → one `gap` KI.
   - Watch row → one KI of the row's `Kind`, status verbatim; a `contradiction` row gets `contradicts:` naming the shared id. v1/v2 tables carry no `Class` column, so assign `class:` — portable when the observation would hold on any machine running this harness, local when it depends on this machine's numbers, paths or corpus — and log every call with a one-line reason.
   - The stamp → `local/harness-stamp.md`, its `^sage-harness-stamp: ` line intact.
   - `journal.md`: the sentinel as line 1, a short header, then the newest three Run-log rows **by date** as `run` lines. Condense notes freely; **never invent an aggregate the source does not state** — restate the row's own figures, keeping a fleet/parent split explicit where the row keeps one.
4. **Archive and clean up**: `mv local.md archive/local-v2.md`, `mv local-archive.md archive/local-archive-v2.md` (plus any `.pre-*` snapshots), verbatim; `rm` the dangling `shared.md` symlink.
5. **Verify, all by command**: `cmp` both archived files against the step-0 snapshot; `bin/sage-index.sh <mem>` exits 0 with one line per KI and no warnings; `head -1 journal.md` is the exact sentinel; a frontmatter walk against invariant 2; rows-in = files-out reconciliation per section; and a **cell-level number check of every count, date and figure against its source row** — the one major defect a real execution produced was a fabricated aggregate that the structural and byte checks passed.
6. **Prove the exit state**: re-run `install.sh` — it must take the quiet v3 path (no migration or drift notice); `/sage-promote`'s preflight now qualifies.

Rollback: `rsync -a <scratch>/mem-baseline/ <mem>/`.

## Migration record (the design machine, done by the design run)

1. `shared.md` (11 rules) → 11 `shared/<slug>.md` files, five fields carried verbatim (one qualifier subsequently repaired in this run's review: the scoped-agent rule's pointer to v2 `local.md` now names the local band KIs); old file → repo `archive/shared-v2.md`; installed `shared.md` symlink **removed** (left in place it dangles, since its repo target moved) and replaced by the `shared` directory symlink.
2. `local.md` → per-row conversion: 12 Rules rows → 11 stats sidecars (`for:` a shared KI) plus 1 local-class rule as a local `lesson` KI holding its own text; 14 Bands rows → 14 `band-*.md`, each carrying `name:` with the v2 class-of-work cell verbatim; every Watch-list row (65) → one KI file of its `Kind`, status carried verbatim; the stamp section → `harness-stamp.md`; the Run log's newest three rows → journal `run` lines, all 43 older rows → `archive/journal-v2-runlog.md`.
3. `local.md`, `local-archive.md`, and the `.pre-*` snapshots → `archive/`, verbatim.
4. Count reconciliation: rows in = files + archived lines out, checked by command before the old files move.

## What stays true (the no-regression contract)

- Promotion, eviction, band raises, consolidation: on the user's word only, in `/sage-promote`. A run appends and reads; it restructures nothing — *stronger* than v2, which let runs consolidate.
- One physical copy of portable knowledge, symlinked, git-visible.
- Counts, dates, costs never enter shared or skill text; ratios and bands may. The three-homes rule survives with "stats sidecar" replacing "Rules row".
- Falsifiers, the compression floor, the write machinery, the cell rule (as a file-read rule), the closure act's evidence bar: all carried.
- Step 2 pricing still has bands (band KIs) and same-shape rows (journal tail).
- The structural check gets *smaller* per failure: one malformed KI file quarantines one KI, not the whole memory.

## Deferred, deliberately

- **Skill-text decomposition.** SKILL.md's `(calibration:)` clauses are KIs wearing skill-text costume, but ripping them out is a second, riskier project; the `(calibration:)` tag already joins them to their stats sidecars, so nothing is lost by waiting. When it happens, each clause becomes a shared KI cited from the step that needs it.
- **Relevance-loading beyond the index.** Step 2 loads KIs by kind/recogniser match against the task, by judgment over the index. If KI count grows past what an index read affords, add front-matter tags and a matcher then.
- **Cross-machine stats aggregation.** Each machine's sidecars stay local; promote reads only its own. A sync design is out of scope.

## Rollback

Every v2 file survives verbatim under `archive/` (and in git for repo files, plus this run's scratchpad baseline). Restoring v2 is: move the archived files back, re-point the `shared` symlink at `archive/shared-v2.md`'s restored copy, and revert the corpus commits. The run-side hint simplification is the only behavior with no v2 artifact to restore from — its v2 text is in git history of `references/memory.md`.
