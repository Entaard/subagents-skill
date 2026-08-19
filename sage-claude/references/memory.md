# Memory protocol

Your job here: put every fact sage learns in the one file whose content class it belongs to, append to local memory on every run, and run consolidation, the hint, promotion and eviction under checks that can fail. Read this at Step 2 before estimating, and again at Step 6 before appending.

[The two files](#the-two-files) · [Append](#append) · [Consolidate](#consolidate) · [The hint](#the-hint) · [Promote](#promote) · [Evict](#evict) · [Structural invariants](#structural-invariants) · [The compression floor](#the-compression-floor)

## The two files

**The split is by content class, not by precedence.** Because the two files never hold the same kind of claim, they cannot contradict each other on the same claim, and there is no arbitration rule to get wrong.

| | `../memory/shared.md` — portable | `../memory/local.md` — this machine |
| --- | --- | --- |
| Holds | rules that would hold on any machine: topology lessons, ratios, discount factors, failure recognisers | absolute costs, bands, run rows, confirmation counts and dates, harness version stamp, watch list |
| Carries per entry | rule, qualifier, recogniser, strength band, falsifier | numbers, counts, dates, provenance |
| Written by | `/sage promote`, on the user's word only | every run, automatically |
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

Sage detects, prints one line, and stops. **Promotion is never automatic**; the user runs `/sage promote`.

```
sage: 3 rules ready → shared, 1 → skill text, 1 retirement candidate. Run `/sage promote`.
```

| Target | Trigger |
| --- | --- |
| → `shared.md` | A rule reaches 3 confirmations, is marked machine-independent, and is not already in `shared.md` |
| → skill text | A rule in `shared.md` reaches 6 confirmations and its `Promoted` cell does not yet record `skill` or `refused`, or a rule's count-derived band (the thresholds in `shared.md`'s header) disagrees with its block's `- Band:` field — a crossing: stage one re-writes the field, stage two re-tags wherever skill text cites it |
| → retirement | A rule's falsifier condition was observed, or two confirmations contradict it |
| → model lineup | The harness stamp in `local.md` is older than the build `claude --version` reports, or a Watch-list row records a `message.model` value absent from `harness.md`'s tier snapshot table |
| → consolidation | `local.md` past ~10k tokens, or 40 rows, or two rows disagree on one band, or structural damage, or a version-bound claim older than the recorded harness version |

Every trigger reads `local.md`'s Rules and Watch list tables — `Count`, `Class`, `Contradicts`, `Promoted`, and `Rule` matched by name against `shared.md`'s `##` headings — plus, for a band crossing, the matched block's `- Band:` field, and, for the lineup trigger alone, one `claude --version` read and one scan of Watch-list text for recorded `message.model` values against the snapshot table's names. All are machine-checkable with no judgment, so a hint that fires is a fact rather than an opinion. The lineup hint is deliberately best-effort — it sees a new build and a new name, never a price or window change behind an unchanged name; stage three's unconditional vendor-docs read is what covers that gap when promote runs.

## Promote

`/sage promote`, on the user's word only. Three stages, shared first — the skill stage reads `shared.md` blocks the first stage may have just written, and the lineup stage runs last, on live-harness evidence rather than run rows. A stage with no candidates is skipped in one printed line.

**Stage one — → `shared.md`.**

1. Read the candidates: every `local.md` Rules row and Watch-list row whose trigger above fired.
2. For each, write the five fields in the order `shared.md` fixes — rule, qualifier, recogniser, band, **falsifier**. The falsifier is the observation that would retire the rule, stated concretely enough that a later run recognises it without re-reading the rule's history. Falsifiers are new machinery: none exists anywhere in `/subagents`, so write one rather than port one, and **a candidate whose falsifier you cannot state is not ready** — leave it on the watch list and say which one you could not write.
3. Dispatch **one refuting `verifier` over the whole batch, briefed to default to refuted**: a rule survives only on evidence the verifier can name. One dispatch for the batch, not one per rule — the batch is what pays the boot cost. A band crossing is arithmetic — count against `shared.md`'s own thresholds — not a claim, so it skips the refuter.
4. Write the survivors into `shared.md`, one `##` block each; a band crossing re-writes only its standing block's `- Band:` field. Then append `shared <date>` — or `band <new band> <date>` for a crossing — to that rule's `Promoted` cell in `local.md`. **The cell is a history: append with ` · `, never overwrite**, because the → skill text guard and Evict both read its earlier entries.
5. Send each refuted rule back to the watch list **with the refutation attached**, status `watching`. It is not written to `shared.md`.
6. Print the diff.

**Stage two — → skill text.** The highest-consequence write sage makes: it rewrites the corpus every future run boots from, so each step below exists to keep the edit minimal, checkable, and reversible. Candidates: every rule whose → skill text trigger holds when this stage begins — re-checked here, because stage one may have just written the qualifying block or moved the band.

1. **Find the rule's one home.** Grep `SKILL.md` and `references/` for the rule's subject. Exactly one location may carry the rule at full strength — the step whose instructions the rule changes; every other mention defers or points. A citation already standing → the edit is a band-tag update in place. Standing text that *contradicts* the rule → a conflict, not an edit: the older sentence is a retirement candidate needing eviction's evidence bar, so name the retiring observation in the diff, or leave both standing and put the conflict on the watch list.
2. **Resolve the ground, then draft, before any write.** `readlink ../memory/shared.md` — the installed symlink beside `local.md` — names the repo; then `diff -rq` the repo corpus against the installed one, `memory/` excluded. A dangling link, a non-symlink result, or a pre-existing divergence → stage two is off this run with zero bytes written, one surfaced line naming which. Then draft every edit — exact old text → exact new text, held in the promote diff. The reverse of the draft is the rollback; no draft, no write. Every edit lands in the repo copy, so the printed diff comes from git while the drafts stay the rollback — never `git checkout`, which cannot tell the batch's edits from pre-existing dirt in the tree.
3. **Write the fewest words that clear the compression floor** — the clause, its qualifier, the recognising anecdote where the floor demands one, `(calibration: <band>)` — and nothing of the other homes' classes: no count, date, cost, or falsifier. A rule that needs a paragraph is not distilled yet; it stays in `shared.md` unwritten, with one watch-list line saying why.
4. **Replace, never accrete.** Where the home already holds weaker or hedged text on the subject, the new clause replaces it. The corpus may grow by at most the clause itself; growth beyond that means something that should have been replaced was kept.
5. **Check the corpus as a whole, once, after the batch's last edit** — four checks, and a failing edit reverts by its draft:
   - **one home** — each promoted rule at full strength exactly once across `SKILL.md` and `references/`, verified by grep;
   - **no contradiction** — every grep hit on the edit's subject agrees with or defers to the new clause;
   - **floor audit** — everything the batch removed, item by item against the compression floor: replacement under step 4 and a retirement removal carrying its named observation (`## Evict`) are licensed; silent loss is not;
   - **class check** — no count, date, or absolute cost entered skill text.
6. **The degradation gate.** Dispatch one refuting `verifier` over the frozen corpus diff — one for the batch, as in stage one — briefed to default to refuted: name a case the pre-edit corpus handled that the post-edit corpus handles worse, a second home, a lost floor item, or a behavior change wider than the promoted rules. A refuted edit reverts by its draft, its rule keeps full standing in `shared.md`, the refutation goes to the watch list, and `refused <date>` is appended to the rule's `Promoted` cell — the entry the → skill text guard reads, so the hint stops offering it until a band crossing or the user's word reopens it.
7. **Land the survivors.** Byte-copy the edited files into the installed skill and prove the two trees identical again with step 2's `diff -rq`. A copy that fails to prove → surface and stop; never hand-edit the installed tree into agreement.
8. Append `skill <date>` to each landed rule's `Promoted` cell in `local.md` — the guard the → skill text trigger reads — and print the git diff.

**Stage three — model lineup refresh.** Same user word, same write machinery, different evidence: stages one and two promote what runs have proven; this stage re-checks what changed *underneath* them — the model lineup the tiers resolve to. It is how a newly released model (a Mythos-class tier above apex, a cheaper fast model) enters sage within one promote instead of waiting for failures to surface it, and how a shift among current models (the standard model besting the frontier one on the checker seat; the fast model falling behind and the standard one becoming the small model) moves the allocations rather than just a note. Nothing changed → print `lineup unchanged` and stop the stage — a determination only step 1's own enumeration can make. Stage three has no precomputed candidate list, so step 1 always runs when promote does: the hint (above) is only the prompt to run promote, never the gate on this stage.

1. **Enumerate the live lineup against the recorded one.** Three sources: the Agent tool schema's accepted `model` values in the live session; `claude --version` and the changelog against `local.md`'s harness stamp; the vendor's model docs — one `web-researcher` whose brief names the snapshot table's recorded facts as its ground truth. The first two see only names and builds; the vendor docs are the **only** source that can see a price, window, latency, or positioning change behind an unchanged name — so that fetch runs whenever the stage does, never as a tiebreaker. A brief that names its target pages keeps it cheap. Compare against two recorded surfaces: `harness.md`'s tier snapshot table, and every `model:` line in the repo's agent sources (`grep '^model:' <repo>/claude-agents*/*.md` — the repo `readlink` on the installed `shared.md` names). Collect three lists: new models, removed models, changed facts about current ones (price, window, latency, deprecation, capability order). All three empty → print `lineup unchanged`; the stage ends there.
2. **Study every new model before placing it.** Two measurements, never a headline: one no-op identity probe on a scoped saved agent, reading `message.model` from the returned transcript — the only field that establishes what ran — proving the name is dispatchable and what it resolves to; and one `web-researcher` fetch of the vendor's own pricing, window, latency, and positioning pages, URL and fetch date per claim. A reader's structural claim is a lead, not ground truth: the placement decision rests on the probe and the primary source, never on a summary.
3. **Place by role, not by name.** Fit each newcomer into the tier ladder — fast / standard / frontier / apex — by price ratio, window, latency, and where the vendor positions it, and write the **rejects** down with the same care as the placements: the seats it must not take, and why. A model above the current apex re-opens the parent-seat question itself. A rejection is a result — it goes in the diff so the next refresh does not re-buy the study.
4. **Re-derive allocations for changed current models.** A price cut, a window change, a deprecation, or a capability flip moves allocations, not just notes: the snapshot table's rows, the roles' `model:` frontmatter in the repo's agent sources, the parent-seat and checker-seat paragraphs, and any `SKILL.md` clause that names the ordering. A deprecated model's tier falls to the nearest surviving fit — if the fast model is retired, the cheapest survivor becomes fast, and every row that named the old model is rewritten, not annotated.
5. **Every edit goes through stage two's machinery** — its steps 2 and 4 through 7: resolve the ground, draft exact old→new, replace never accrete, the whole-corpus check, the degradation gate's refuter (briefed to default to refuted: name a dispatch the old lineup served that the new one serves worse), and the two-copy landing with `diff -rq` proof. Agent-source edits land the same way: the repo copy first, then the installed `~/.claude/agents/` copy, byte-identical. Absolute prices stay out of skill text — ratios only, per the class check. The probe transcripts and any placement lesson append to `local.md` as ordinary run evidence, and the refreshed lineup's facts re-date the harness stamp.

## Evict

Symmetric to promotion, and absent from `/subagents` entirely.

A rule whose `Falsifier` fires — the named observation happened, or two watch-list confirmations contradict it — moves out of `shared.md` into `local-archive.md` **with the observation attached, not deleted**, tagged `retired: <the observation>`, so one grep settles why a rule that used to be there is gone. Append `retired <date>` to that rule's `Promoted` cell in `local.md` — append, because the paragraph below still needs the cell's earlier `skill` entry — or its old count re-promotes it on the next hint.

**Retirement reaches skill text.** A rule whose `Promoted` cell records `skill` still stands in the corpus, citing a band that no longer exists — the worst false confidence the skill can carry. Grep the corpus for its clause and citation; remove the hit, or cut it back to whatever weaker statement the surviving evidence supports, under stage two's draft, whole-corpus check, degradation gate, and two-copy landing, with the retiring observation named in the diff. The compression floor does not shield it: the floor guards against cuts sold as shortening, and this is a spec change made on named evidence.

Eviction runs inside `/sage promote`, on the same user word. A falsifier firing surfaces as a hint line like any other; it never rewrites `shared.md` on its own.

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
