# Findings from the 2026-08-28 `/sage-promote` pass

Written for another machine to act on. Every claim here carries the data behind it and a command
to re-check it. Nothing in this file is fixed yet.

Machine: Claude Code 2.1.250, GNU grep 3.8, repo at `/app/Storage/code/tools/subagents-skill`.
Installed sage at `~/.claude/skills/sage`. Pass date 2026-08-28.

**Read F1 first.** It is a repo defect that every install inherits, and three separate rules stop
any automated pass from fixing it.

---

## F1 — Four shared rules claim a band their counts do not support

### What is wrong

`memory/shared/` marks four rules `band: established`. The protocol defines `established` as six
or more confirmations (`sage-claude/references/memory.md:42`). All four sit below that bar. They
were promoted at `established` on 2026-08-17 without a count check, and the repo's install seed
ships that state, so **every fresh install starts with the same four wrong bands.**

### The data

Seed counts come from `sage-claude/memory/local-seed/local/*.stats.md`. The "this machine" column
is `~/.claude/skills/sage/memory/local/*.stats.md` after the 2026-08-28 reconciliation.

| Rule id | `band:` | seed count | this machine | derived band | skill-text citations to re-tag |
|---|---|---|---|---|---|
| `a-brief-that-names-its-ground-truth-runs-cheaper` | established | 5 | 5 | recurring | `SKILL.md:126` |
| `settle-a-disagreement-with-a-command` | established | 4 | 5 | recurring | `SKILL.md:203`, `SKILL.md:204`, `references/topologies.md:27` |
| `a-readers-structural-claim-is-a-lead` | established | 3 | 4 | recurring | `SKILL.md:129` |
| `price-off-a-same-shape-row` | established | 3 | 3 | recurring | `SKILL.md:95` |

The other seven rules are banded correctly and are the control:

| Rule id | `band:` | seed count | derived | agrees |
|---|---|---|---|---|
| `point-one-adversarial-pass-at-your-own-fixes` | established | 10 | established | yes |
| `review-and-verify-are-one-price` | established | 8 | established | yes |
| `estimate-from-the-corpus-and-the-lenses` | established | 7 | established | yes |
| `disjoint-mandates-produce-disjoint-find-sets` | established | 6 | established | yes |
| `a-checklist-prices-a-lens-only-when-every-item-settles-in-one-look` | recurring | 3 | recurring | yes |
| `when-the-target-is-a-range-never-report-a-mean` | recurring | 3 | recurring | yes |
| `a-scoped-agent-boots-3x-cheaper` | provisional | 1 | provisional | yes |

### A second, separate defect on two of them

On this machine, two sidecars record a demotion that never happened:

```
settle-a-disagreement-with-a-command.stats.md
  promoted: shared 2026-08-17 · band recurring 2026-08-20 · refused 2026-08-20
a-brief-that-names-its-ground-truth-runs-cheaper.stats.md
  promoted: shared 2026-08-17 · band recurring 2026-08-20
```

The 2026-08-20 pass wrote `band recurring 2026-08-20` into both histories. The shared files still
read `established`. **The demotion landed nowhere** — not in `shared/`, and not in skill text.
This is the false-cell failure that `/sage-promote`'s `## The cell rule` exists to prevent: the
history claims a write that no artifact carries.

The seed sidecars carry only `shared 2026-08-17`, with no band entry, so this half is local to
this machine. The wrong band itself is in the seed.

### Why no automated pass can fix it

Three independent locks, all in `~/.claude/skills/sage-promote/SKILL.md`:

1. **Line 152** — the band signal is upward-only: "a count below the standing band is a machine
   that has seen less, never a crossing". A count under the band produces no action.
2. **Line 139** — stage zero may repair a shared KI's prose fields but "may never ... touch a
   `band:` field".
3. **Line 31** — `memory/local-seed/` is on the never-touched list, so no pass may correct the
   seed even where it can see the fault.

Eviction does not reach it either: it qualifies only on a fired falsifier or a contradiction KI at
two confirmations. A band that is merely too high is neither.

**Only a hand edit to the repo fixes this.**

### What to do

1. In `sage-claude/memory/shared/`, set `band: recurring` on the four rules in the first table.
2. Re-tag their skill-text citations from `(calibration: established)` to `(calibration: recurring)`
   at the six sites named in that table's last column.
3. Note the prior blocker before step 2: `defect-settle-qualifier-cited-at-untaggable-sites`
   records that the 2026-08-20 pass tried exactly this re-tag for the Settle rule and its gate
   refuted it, because `references/topologies.md:27` carries the agreement-evidence claim with no
   shared rule of its own. Either give that claim its own shared KI, or re-tag all three Settle
   sites together as one edit.
4. Decide whether the upward-only rule should stay. It is defensible for cross-machine drift, but
   it leaves the corpus with no way to correct an over-promotion. A downward path gated on the
   user's word would close this class.

### How to verify

```sh
for sf in sage-claude/memory/shared/*.md; do
  id=$(sed -n 's/^id: //p' "$sf" | head -1)
  b=$(sed -n 's/^band: //p' "$sf" | head -1)
  c=$(sed -n 's/^count: //p' "sage-claude/memory/local-seed/local/$id.stats.md" 2>/dev/null | head -1)
  [ -z "$c" ] && continue
  if [ "$c" -ge 6 ]; then d=established; elif [ "$c" -ge 3 ]; then d=recurring; else d=provisional; fi
  [ "$b" != "$d" ] && echo "MISMATCH $id: band=$b seedcount=$c derived=$d"
done
```

Expect four lines now, and none after the fix.

---

## F2 — `defect-bracket-expression-does-not-read-backslash-t` states a false consequence

### What is wrong

The KI's **mechanism** is right and its **consequence** is wrong. A repair built on the
consequence nearly reached skill text this pass. The degradation gate refuted the repair, but for
a wrong reason of its own, so both halves need correcting.

### The data

Measured on GNU grep 3.8, 2026-08-28.

| Test | Command | Result | Reads as |
|---|---|---|---|
| A tab-only line against the class | `printf '\t\n' > t; grep -Ec '[^\t]' t` | `1` | The class does **not** mean "not a tab". If it did, a tab-only line could not match. The KI's mechanism is confirmed: `[^\t]` means "not a backslash and not the letter `t`". |
| Field pattern, subject contains `t` | `printf 'cat\tX\n' > f; grep -Ec '^[^\t]+\t' f` | `1` | A path containing `t` **still matches**. `[^\t]+` takes `ca`, then the trailing `\t` matches the literal `t`. |
| Field pattern, subject has no `t` | `printf 'dog\tX\n' > f2; grep -Ec '^[^\t]+\t' f2` | `0` | The pattern fails on a line with no `t` at all. |

### Two corrections

1. **The KI is wrong.** `~/.claude/skills/sage/memory/local/defect-bracket-expression-does-not-read-backslash-t.md`
   says "any path containing a `t` fails to match, and every path under `XCortex` does". Test A
   and B disprove it. The real failure shape is a field pattern anchored on a run of `[^\t]`, and
   whether it matches depends on where the `t` sits, not on whether one is present. Restate the
   consequence before any future repair.
2. **The gate was wrong.** It reported that the installed grep treats `[^\t]` as "not a tab" and
   refuted the mechanism. Test A disproves that. A gate refutation is a lead, not a verdict; one
   command settles it. This pass filed that as an `obs` lesson line in the journal.

The repair still reverted, correctly, because correction 1 stands on its own.

---

## F3 — Sixteen migration strays are still unconverted, and one contradicts a live KI

### What is wrong

`~/.claude/skills/sage/memory/archive/strays-v1.md` holds 17 row-shaped observations that the v3
migration could not map to knowledge items. Its own header addresses them to this skill: "A
`/sage-promote` pass should read each one and either mint a knowledge item for it or drop it on
the record." No stage in `/sage-promote` mints a KI from archive prose, so they stayed.

They carry real observations dated 2026-08-24 to 2026-08-28. The file documents both column
layouts, so mapping them is no longer a guess:

- One row from `## Watch list`: `date | kind | area | observation | count | contradicts`.
- Sixteen from `## Run log`: `watch | date | kind | area | count | observation`.

### The one that matters most

The stray at `local.md:144` (2026-08-28, defect, tooling) contradicts a live KI:

> A read-only reader unit cannot satisfy this repo's Transverse KB hook ... The parent clearing
> the hook up-front does NOT help a subagent: hook state is per-agent.

`defect-repo-hook-degrades-a-subagent-unit` prescribes the opposite prevention:

> A parent dispatching readers into a hook-gated repo should satisfy the gate itself BEFORE the
> wave launches.

That KI records the prevention working once, on 2026-08-27, and its status reads "prevention
confirmed once; close after two more clean waves". If the stray is right that hook state is
per-agent, the 2026-08-27 clean wave had another cause and the prescribed prevention is wrong.
**Settle this with a measurement before either closes.**

### Other strays worth minting

- `local.md:122` and `local.md:126` (2026-08-24): two estimating bands, each with three
  observations behind it. `local.md:133` (2026-08-26) is a contradiction against the first.
- `local.md:142` (2026-08-28): `git stash push --keep-index` then `git stash pop` corrupts the
  tree when the index holds someone else's staged changes. Duplicated six test methods and broke
  the build.
- `local.md:143` (2026-08-28): a suite failure is not attributable until re-run against the
  pre-change tree, and in a flaky suite the identity of the failure moves.

---

## F4 — Vendor positioning moved under two unchanged model names

Fetched 2026-08-28 from Anthropic's own docs. No tier moved, and the lineup is unchanged:
`haiku` / `sonnet` / `opus` / `fable`, price ratio 1 : 2 : 5 : 10 for input and output alike,
windows 200K for Haiku 4.5 and 1M for the other three. Both facts re-confirmed.

Two things changed behind unchanged names. Neither is in the corpus.

1. **Opus 5 is no longer positioned as a reviewer/judge tier.** Current vendor copy says "complex
   agentic coding and enterprise work". `sage-claude/references/harness.md`'s snapshot table still
   describes `opus` as "hard review, judging; the default checker seat".
   Source: `https://platform.claude.com/docs/en/models/opus-5/overview`, fetched 2026-08-28.

   **This pass did not move the row, deliberately.** Sage's checker-seat choice rests on its own
   measurement — "the standard-tier checker has been right against the frontier one" — not on
   vendor copy. Change it only if a measurement, not a marketing page, says to.

2. **The Mythos/Fable migration guide now names `claude-fable-5` as a same-capability alternative
   that needs no access approval.** This strengthens the existing rejection of `mythos` in the
   snapshot table's "Studied and rejected" paragraph. The vendor also narrows Mythos 5's stated
   availability to defensive cybersecurity workflows; the recorded text says "cybersecurity and
   biology research".
   Sources: `https://platform.claude.com/docs/en/models/fable-5/migration-guide` and
   `https://platform.claude.com/docs/en/models/mythos-5/overview`, both fetched 2026-08-28.

Retirement dates the vendor now publishes, for whoever maintains the table: Haiku 4.5 2026-10-15,
Sonnet 5 2027-06-30, Fable 5 2027-06-09, Mythos 5 2027-06-09, Opus 5 2027-07-24.

---

## F5 — Four defect KIs stay open, each with a stated next step

The degradation gate refuted five of six repairs this pass. One reverted for a reason that was the
gate's error (F2). The other four reverted for reasons that were right, and each KI now carries a
`## Gate 2026-08-28` note and `refused 2026-08-28` in its history. All four are in
`~/.claude/skills/sage/memory/local/`.

| KI | What the gate found | What to write instead |
|---|---|---|
| `defect-alt-lane-reports-zero-tokens` | An alt unit's spend **is** measurable from its transcript. The gate measured one historical alt transcript at 217,669 tokens. "No actual to land" is too strong and weakens accounting. | "The returned `subagent_tokens` field reads 0; measure the transcript instead." Not "unmeasurable". Both alt dispatches this pass returned `subagent_tokens: 0` in result metadata, so the narrow fact holds. |
| `defect-orchestrator-successor-cannot-publish` | The tool fact is right — `~/.claude/agents/orchestrator.md:4` grants no Artifact and no Skill tool. The prohibition is wider than the evidence: handover leaves the original parent supervising and parent-signing Step 6, so the parent can publish after the successor returns. | A sequencing note, not a planning prohibition. The deliverable is not lost. |
| `defect-ledger-rewrite-anchor-must-not-be-quoted-text` | The anchor example was wrong. `sage-claude/references/dispatch.md` has `### Run record` at line 176 and zero `## Run record`. (The gate reported line 179; the true line is 176. Its substantive point stands.) A stronger home already exists at `sage-claude/bin/sage-lint.sh:325-340`, which requires anchor uniqueness before any replacement. | Check whether that lint rule already settles this KI before repairing again. |
| `defect-lint-duplicate-id-check-is-case-blind` | An uppercase initial is necessary but not sufficient. `sage-claude/bin/sage-lint.sh:877-879` accepts only a bare uppercase letter, or 1-4 uppercase letters plus optional hyphen, 1-3 digits and an optional lowercase suffix. `ABCDE-1`, `A-1234` and `M7-rej` all obey "starts uppercase" and still get no duplicate checking. | State the whole grammar, or widen the regex. Widening carries a false-positive risk this pass did not measure. |

---

## What this pass already did — do not redo it

- **Archive reconciliation ran and is stamped.** All 48 local KIs on this machine carry
  `reconciled: 2026-08-28`. The walk is one-time migration debt; a KI carrying that stamp is
  skipped for ever, and re-running it double-counts. Another machine has its own `local/` and must
  run its own walk.
- **One count was under-recorded and is now fixed.** `defect-alt-lane-reports-zero-tokens` read
  `count: 3`; `strays-v1.md` (from `local.md:129`) states "6th, 7th and 8th consecutive
  observations on 2026-08-26". Raised to 8, `last:` to 2026-08-26.
- **Ten KIs gained citation counts the migration never carried.** Each carries a `## Reconciled`
  section with the archive `file:line` behind every figure, so the arithmetic can be checked
  rather than repeated. Largest: `point-one-adversarial-pass-at-your-own-fixes` at 8 uses,
  `a-readers-structural-claim-is-a-lead` at 5.
- **One repair landed**, in `sage-claude/references/dispatch.md` `## Snapshot protocol` step 1: an
  untracked file is recorded by name, and a name is not a recovery path. The gate confirmed it by
  reproduction in a fresh repository.
- **The harness stamp is current**: `2.1.250 | verified 2026-08-28`, with the four facts actually
  verified live under that build listed beside it.

## What the pass could not see

The structural checks catch damage, never a wrong rule. F1 is the proof: four rules with perfect
frontmatter, correct shapes, and a band the evidence does not support. Every marker passed for
eleven days. Falsifiers, recorded misses and eviction are the only defence against that class, and
they all run on a human's word.
