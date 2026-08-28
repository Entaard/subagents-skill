# Sage memory v3.1 — the template-and-clone model

Status: designed and implemented 2026-08-28, on the user's word, by the sage run whose ledger is `.claude/plans/sage-ledger-d8000479.md`. This revises the cross-machine half of the 2026-08-27 v3 design. The KI shapes, the journal, `local/`, the hint, and every promote stage's inner semantics are unchanged — except the band, below.

Revised the same day, on the user's word, by the run whose ledger is `.claude/plans/sage-ledger-d20b9a1f.md`: the first draft kept a `band:` field in the template under a highest-earned merge rule. The user cut the field instead — the template is the source of truth and carries no tracking of any kind; the band exists only on the machine. Sections below describe the final model; `### The band is machine tracking` records what replaced the merge rule.

## The problem, measured

v3 kept one physical copy of portable knowledge: `sage-claude/memory/shared/` in the repo, reached from every machine through a symlink. That design failed three ways, all recorded:

1. **The `band:` field had no owner.** Each machine's promote pass derived a band from its own counts and wrote it into the one shared file. Git history shows one rule's band flipping five times across two committer identities. Each pass was locally correct under its own reading (journal, run 1b65b7d5, 2026-08-28).
2. **The seed shipped another machine's tracking data.** `local-seed/local/*.stats.md` carried the design machine's counts. Every fresh install started with confirmation counts it never observed. The other machine's F1 finding (2026-08-28) traces four wrong bands to exactly this.
3. **Cross-machine findings were not portable.** A fix derived from one machine's counts was wrong on the next machine: F1 prescribed demoting a rule whose count on the receiving machine was 7. Per-machine numbers cannot govern a shared field.

The root cause is one sentence: **tracking data and shared truth lived in the same files, or fed the same fields, across machines that cannot see each other's evidence.**

## The model

Three rules replace the symlink:

1. **The repo is the template, and it carries no tracking.** `sage-claude/memory/shared/` holds the one authoritative copy of every portable KI: id, kind, class, status, and the rule body. No counts, no dates, no uses — that was already the v3 file format — and no `band:` either: the band is calibration a machine earns from its own counts, so it is tracking, and it lives on the machine's stats sidecar (the revision above; v3.1's first draft still carried it). The seed (`local-seed/`) ships knowledge priors only: cost-band KIs, lessons, gaps, the stamp. It no longer ships stats sidecars, because a sidecar is pure tracking.
2. **Every machine works on a clone.** The installer copies the template into `~/.claude/skills/sage/memory/shared/` as a real directory. Runs read the clone. All tracking for a shared KI — counts, uses, misses, promoted history — lives in that machine's `local/` sidecars, minted on the machine with zeroed stats the first time the KI is used or confirmed. A machine never edits its clone directly.
3. **`/sage-promote` is the only bridge back.** Consolidation, the KI review, and all bookkeeping update the machine's own files first. When a KI earns a template change — a new shared rule, a band raise, a prose repair, a retirement — promote writes the **repo template first**, then lands the same bytes on the clone, exactly as corpus edits already land in two copies. Git then carries the change to other machines; their installer sync applies it.

### The band is machine tracking

This is the ownership rule v3 lacked, and it is what stops the oscillation. The first draft answered it with a merge rule — the template's `band:` records the highest band any single machine earned, raises only. The user replaced that with the cleaner cut the root-cause sentence already implied:

**The template carries no `band:` at all.** A shared KI's strength band sits on its stats sidecar in `local/` — a stored, optional field: absent, it reads `provisional`, a band no pass has assessed yet, so the next pass's crossing (count-derived, thresholds 3–5 recurring, 6+ established) can fire and materialize it. The stage-one crossing rewrites the sidecar's `band:` line and appends to its `promoted:` history — a `local/` write with no landing step and no template byte. Upward only, because counts only accumulate; downward movement stays with eviction and the user's word.

One appearance of a band remains shared: the skill-text `(calibration: <band>)` tag, written at → skill landing. It records the highest band any single machine's counts have earned, and it inherits the merge rule's asymmetry: a machine whose own band sits below the tag has seen less — never a demotion signal.

Consequence for the four bands the F1 finding disputed: the dispute dissolves. Each machine's sidecar now answers for that machine alone — `settle-a-disagreement-with-a-command` reads `established` here (count 7) and whatever the other machine's counts earn there. No shared field exists to fight over.

## Layout

Repo (`sage-claude/memory/`) — the template:

```
shared/          one file per portable KI — the authoritative copy, no tracking fields
archive/         retired template KIs (moved here by eviction, observation attached), v2 relics
local-seed/      knowledge priors the installer copies once to a fresh machine:
  journal.md       sentinel + grammar header
  local/           band/lesson/gap/stamp KIs — figures kept, provenance marked; NO *.stats.md
```

Installed (`~/.claude/skills/sage/memory/`) — the working set:

```
shared/          real directory: the clone. Written only by the installer's sync and by
                 /sage-promote's landing step. Never edited by hand, never by a run.
source-repo      one line: the absolute path of the repo the clone came from.
                 Rewritten by every install. /sage-promote resolves <repo> from it.
local/           this machine's KIs and sidecars — the only tracked state, never synced
journal.md       append-only, one writer per line (runs), drained by promote
archive/         drained journal segments, retired local KIs, clone files removed by sync
```

## Sync semantics (installer)

One direction: template → clone. The template always wins. Per file:

| Clone state vs template | Installer action |
| --- | --- |
| identical | nothing |
| missing from clone | copy in |
| differs from template | back up the clone's copy once per run, then overwrite |
| a directory sits at a template filename | back up the whole clone once, remove the directory, copy the template's real file — `cp` onto a directory would nest the file inside it and the clone would never converge |
| present in clone, absent from template (file, link, or directory) | move to `memory/archive/` and print it — the KI was retired on another machine |
| `memory/shared` is the v3.0 symlink | capture its target with `readlink` for the migration notice, remove the symlink — a link carries no data — then create the directory and copy the template in |
| `memory/shared` is a plain file | back it up, remove it, create the directory, sync |
| `memory/shared` is a foreign real directory | back it up, then sync into it |
| a file inside the clone is itself a symlink | back the link up, remove it, copy the template's real file — never write through it |

A differing clone file is always unexpected — promote writes repo-first, so even an interrupted pass leaves the repo ahead, never the clone. The backup is the recovery path for a hand edit someone made in the wrong place.

The installer also writes `memory/source-repo` (the repo's absolute path) on every run, and prints a one-line summary of added / updated / archived files, or nothing when the clone was already current.

**The installer never writes the repo.** Seeding still runs exactly as before (fresh machine only, journal + `local/`), minus the deleted sidecars.

## /sage-promote changes

- **Preflight step 1 (resolve the ground)** no longer reads a symlink. It reads `<sage>/memory/source-repo`; the path must exist and `<path>/sage-claude/memory/shared/` must be a directory, else stop. Then it requires `diff -rq <repo>/sage-claude/memory/shared/ <sage>/memory/shared/` to be clean; a divergence means the machine has not run `install.sh` since the last pull — print that and stop.
- **Every shared-KI write takes the full two-copy landing**: repo template first, byte-copy to the clone, prove identical. The v3 exemption ("a shared-KI repair needs no landing copy — the directory is a symlink") is gone.
- **Eviction step 3** now moves the template file to `<repo>/sage-claude/memory/archive/` with the observation attached, and removes the clone's copy at the landing step. Other machines lose the file at their next installer sync, which archives their clone copy locally. v3 moved the one physical file into the *machine's* archive, which silently removed it from the repo — that defect dies with the symlink.
- **The band crossing leaves the template path entirely** (the revision above): it rewrites the sidecar's `band:` line in `local/` and appends to its `promoted:` history — no landing step, no refuter, under the cell rule. Raises only, because a lower local count is less evidence, not counter-evidence.

## What this does not change

- The journal, its grammar, the hint, and the run-side duties (read at Step 2, append at Step 6).
- KI file shapes, the field contract, the removal bar, the compression floor.
- Consolidation, the KI review, stages one to three, and eviction — except the landing and ground-resolution mechanics above.
- Lazy sidecar minting: consolidation already mints a zeroed sidecar the first time a `use` or `confirm` line names a shared KI without one. That mechanism is what makes shipping no sidecars safe.

## Migration

- **v3.0 machine (symlink):** automatic. Run `install.sh`; the sync table's symlink row applies. Nothing under `local/`, the journal, or `archive/` is touched.
- **Already-seeded foreign sidecars:** machines seeded under v3.0 hold `*.stats.md` whose counts came from the design machine (`provenance: author's log (seed)`). The installer does not remove them — it cannot tell a seed row from one the machine has since earned on top of it. If you want them gone, audit by provenance and remove by hand; a missing sidecar is re-minted zeroed on next use.
- **Band relocation:** automatic on pull + `install.sh` — the sync overwrites each clone KI with the bandless template copy. A machine's own band re-derives from its sidecar `count:` (the field is optional; the next promote pass's crossing writes it where a threshold is crossed). No skill-text `(calibration:)` tag moves.
- **Fresh machine:** nothing to migrate; the fresh-install path is the model.

## Rollback

The symlink model is restorable from git: revert the corpus commits, re-run the old installer (git history holds it), and the old preflight finds its symlink again. Machine-side, the clone directory can be deleted and the symlink recreated by hand; `local/` and the journal were never touched by this change.
