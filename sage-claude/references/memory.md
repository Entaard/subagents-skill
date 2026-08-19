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

**The residual case.** A local run contradicting a portable rule does **not** overturn that rule. Write a watch-list row in `local.md` whose `Contradicts` cell names the rule; the row needs its own confirmations, and it appears in the next hint as a **retirement candidate**.

## Append

Automatic, every run, at Step 6, to `local.md` only. One Run-log row: date, task class, agents, est, actual, wall clock, note — **including the runs where the estimate held**, because a band you can trust needs its hits recorded next to its misses.

Write the note so Step 2 can act on it: "fetch-heavy research runs 70–120k per agent" is usable at plan time; "unit 3 was expensive" is not.

**Anchor the append on the file's final characters, never on a date cell.** The Run log is the last section by construction, so "append at the end of the file" stays correct however the file grows; an anchor on a date matches the wrong row the first time two runs share a day.

## Consolidate

Automatic when a trigger below holds, **at the start of a run, before `../SKILL.md` Step 2 reads memory**, on `local.md` only. That placement is the whole invoker — nothing else calls this pass, which is why a consolidation trigger raised at Step 6 clears at the next run's Step 2 instead of reprinting its hint forever, and why Step 2 never prices off unmerged rows. Rewrite Run-log rows into Bands and Rules, then move every consolidated original, verbatim, into `local-archive.md` beside it, each tagged with why it left — retired or compressed. That archive first exists when the first pass runs, and Step 2 never reads it; it exists so one grep settles a rule's provenance.

Two checks guard the write. **Both must pass, or the pass aborts and writes nothing** — no partial result, no question to the user. A human approving a diff is not this safeguard: the one recorded corruption on this machine landed *through* an approved diff and was found later by a check.

1. **Self-check.** Every pre-pass row survives verbatim in exactly one place — Run log or archive — and the count of survivors equals the pre-pass row total, since a compressed row's one-line summary is a pointer, not a survivor; every band cites at least one run; every rule carries at least one date; the result is smaller than what it replaces; both files parse as markdown.
2. **Structural invariant check**, against the section below.

A pass that produced no change reports `nothing to consolidate` and ends, writing nothing and running neither check — so a second pass straight after a first proposes nothing.

## The hint

Sage detects, prints one line, and stops. **Promotion is never automatic**; the user runs `/sage-promote`.

```
sage: 3 rules ready → shared, 1 → skill text, 1 retirement candidate. Run `/sage-promote`.
```

| Target | Trigger |
| --- | --- |
| → `shared.md` | A rule reaches 3 confirmations, is marked machine-independent, is not already in `shared.md`, and its `Promoted` cell either records no `retired` or the Rules row's last-confirmation date is newer than that `retired` date — a retired rule re-qualifies only on evidence dated after its retirement, never on its old count |
| → skill text | A rule in `shared.md` reaches 6 confirmations and its `Promoted` cell does not yet record `skill` or `refused`, or a rule's count-derived band (the thresholds in `shared.md`'s header) disagrees with its block's `- Band:` field — a crossing: `/sage-promote`'s stage one re-writes the field, its stage two re-tags wherever skill text cites it |
| → retirement | A rule's falsifier condition was observed, or two confirmations contradict it |
| → model lineup | The harness stamp in `local.md` is older than the build `claude --version` reports, or a Watch-list row records a `message.model` value absent from `harness.md`'s tier snapshot table |
| → consolidation | `local.md` past ~10k tokens, or 40 rows, or two rows disagree on one band, or structural damage, or a version-bound claim older than the recorded harness version |

Every trigger reads `local.md`'s Rules and Watch list tables — `Count`, `Class`, `Contradicts`, `Promoted`, and `Rule` matched by name against `shared.md`'s `##` headings — plus, for a band crossing, the matched block's `- Band:` field, and, for the lineup trigger alone, one `claude --version` read and one scan of Watch-list text for recorded `message.model` values against the snapshot table's names. All are machine-checkable with no judgment, so a hint that fires is a fact rather than an opinion. The lineup hint is deliberately best-effort — it sees a new build and a new name, never a price or window change behind an unchanged name; `/sage-promote` stage three's unconditional vendor-docs read is what covers that gap when it runs.

## Promotion and eviction

Both belong to **`/sage-promote`**, a separate skill, on the user's word only. A run never loads
the procedure it will not run: a run's whole duty is the hint above — detect, print one line, stop.

`/sage-promote` reads this file for three things and writes none of it: the triggers above, which
tell it what its candidates are; `## Structural invariants` below, which its preflight checks
`local.md` and `shared.md` against; and `## The compression floor` below, which bounds what its
corpus edits may remove. It writes `shared.md`; the `Promoted` cells, watch-list rows, harness stamp and one
run row in `local.md`; `local-archive.md`; and — at its second and third stages — sage's own
corpus and the model lineup's agent sources, repo and installed.

Eviction is the same skill's, for the same reason: a rule whose `Falsifier` fires leaves
`shared.md` **with the observation attached**, and any skill text citing its band comes out with
it. A falsifier firing surfaces as a hint line like any other. It never rewrites `shared.md` on
its own.

## Structural invariants

This section is the contract the invariant check tests against: a check written from this section and nothing else is a complete check. The repo's `../memory/local-seed.md` — what the installer copies once to create `local.md` — is a file that satisfies every marker below, so it doubles as the worked example and as the check's own fixture.

**`local.md`** — the sentinel, then these `##` sections in this order, none missing, none repeated, no other `##`:

1. Line 1 is exactly `<!-- sage-local-memory v1 -->` and line 2 is exactly `# Sage local memory`. This is the **header sentinel**; absent, the file is not sage local memory and the pass aborts before reading further. **The installer greps this line** — `sage-local-memory` — rather than diffing the header, so consolidation must carry it through verbatim. Comparing anything sage itself is licensed to rewrite would latch the drift notice on permanently; a sentinel that moves only when the format really moves lets the notice go quiet the moment the answer is yes.
2. `## Harness version stamp`, holding exactly one line matching `^sage-harness-stamp: `. Consolidation carries that line through unchanged and on one line, because the version-bound consolidation trigger above compares against it — a rewrite that drops or reflows it disarms that trigger with nothing to show for it.
3. `## Bands`, holding one table, header row exactly `| Class | Figure | Qualifiers | Evidence |`.
4. `## Rules`, holding one table, header row exactly `| Rule | Count | First → last | Provenance | Class | Promoted |`.
5. `## Watch list`, holding one table, header row exactly `| Observation | Kind | Count | First → last | Contradicts | Status |`.
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
