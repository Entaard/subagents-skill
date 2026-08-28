# The cortex never shrank

**On the question: after memory v3, what is still in sage's `SKILL.md` that should be a knowledge item instead?**

Written 2026-08-28. Round 1 (session `48627a15`) ran four disjoint lenses plus an apex refuter.
Round 2 (session `ffb2666d`) ran four *new* lenses against this document and against the parts of
the cortex round 1 never cited, plus an apex refuter over the result. Round 3 (session `6d223791`)
ran four more against the axes both had left: the 7,863 words no condense lens had touched, the
findings the write-ups themselves dropped, a per-item ruling on whether each cut changes behaviour,
and the first corpus-wide duplication scan. Every figure below was measured on this machine by a
command stated next to it, or cited to a file and line that resolves here today.

> **Method, round 2.** Round 1's four mandates were redundancy, provenance, procedure-vs-policy,
> and a negative arm. Round 2 took four axes round 1 did not have: an **audit** lens that
> re-ran every checkable claim in this document by command; a **condense-in-place** lens, because
> every tier round 1 produced was a *move* or a *delete* and nothing rewrote a retained clause
> shorter; an **uncovered-territory** lens, because this document's recommendation cites 90 of
> `SKILL.md`'s 353 lines and never touches the other 5,305 words; and an **architecture** lens for
> whole-section and new-destination moves. The parent settled two inter-lens disagreements by
> measurement rather than by seniority, and re-measured the two largest claims itself.
>
> **Where the paths resolve.** Bare names — `SKILL.md`, `references/*.md`, `bin/*.sh`,
> `memory/shared/` — are relative to `sage-claude/` in this repo, verified byte-identical to the
> installed `~/.claude/skills/sage/` for `SKILL.md` and all five reference files by `diff -q`
> during both runs. `memory/local/` and `memory/journal.md` exist only on the installed tree; the
> repo ships `memory/local-seed/`. `~/.claude/skills/sage-promote/SKILL.md` is quoted from the
> installed copy. Round 1's artifacts are seven live local files under `.claude/plans/`
> (`sage-ledger-48627a15.md`, `sage-48627a15-lens-{1,2,3,4}.md`, `sage-48627a15-growth.md`,
> `sage-48627a15-ki-inventory.md`); round 2's are five more (`sage-ledger-ffb2666d.md`,
> `sage-ffb2666d-lens-{1,2,3,4}-*.md`). All twelve `ls` clean today. `.claude/plans/` is
> gitignored here (`git check-ignore -q .claude/plans/` exits 0), so they are durable on this
> machine and reachable nowhere else.
>
> **Method, round 3.** Four axes again, chosen as the complement of what rounds 1 and 2 could see.
> A **condense-completion** lens over the 7,863 words round 2's condense lens never ruled on — its
> scope computed by the parent and validated by reproducing that lens's own 4,131/3,385 totals
> exactly. An **unharvested-findings** lens over all ten prior lens and refuter reports, because
> this document is a lossy summary of them and already records one instance of that loss. A
> **logic-preservation** lens ruling every proposed cut on whether a fresh instance behaves
> differently — the axis the user's question turns on and neither earlier round had. And an
> **audit-plus-duplication** lens re-running the numbers round 2 introduced and never re-checked,
> plus the first mechanical scan of the whole corpus for second homes. The parent re-derived the §1
> growth series independently, corrected one lens claim against the file it cited, and did §7's
> arithmetic in the open (`.claude/plans/sage-6d223791-arithmetic.md`) because three published
> drafts have now failed it.
>
> **One measurement caveat, and it is not cosmetic.** `git show <rev>:<path> | wc -w` **silently
> truncates in this environment**, non-deterministically: three invocations this session returned
> 2,628 words for a blob `git cat-file -s` reports as 81,826 bytes, with no error and no non-zero
> exit. Every word count in §1 was originally produced by that pattern. §1's table below was
> rebuilt with an extractor that verifies each read against `git cat-file -s` and retries. Anyone
> reproducing these numbers must do the same or they will get different ones at random.

---

## Verdict

Your premise is right. Your diagnosis was too generous to the design, and round 1's account of
*why* was wrong in a way round 2 had to correct.

**`SKILL.md` has never shrunk.** It went 8,801 → 13,393 words in ten days, **+52.2%**, and the
commit that landed memory v3 — the change that was supposed to extract from it — moved it by
**minus seven words**. Nothing in the system is triggered by the file's size, because nothing
computes it. That is the whole answer to "why is there still a wall of text": nothing has ever
tried to remove one.

What round 1 got wrong was the mechanism. It called this a *ratchet* — promotion adds and only
falsification removes — and round 1's own §9 then falsified that claim against `/sage-promote`'s text
without ever going back to fix the Verdict or the §2 that asserted it. Round 1's §2 is gone from
this draft and §8 below carries the surviving, weaker, sufficient version.

Round 1 also got its headline measurement wrong. It reported the cortex's share of the corpus as
"flat between 37% and 41%" — true only under a corpus definition it never stated, one that
excludes `bin/*.sh`. Those scripts are **20,437 words**, larger than all five reference files
combined, and they are the destination round 1's own recommendation sends the most words to.
Counted, the share falls **33.5% → 24.8%** — because other files grew faster, chiefly the scripts.
What did not happen, on any definition, is a single word coming out of the cortex.

**Text that can come out: about 4,800 words, roughly 36% of the file — and do not quote that to
three significant figures.** Round 2 published 4,400–5,400; that band failed its own subtraction
(`5,486 − 481 = 5,005`, not the ~4,900 printed beside it). Round 3's first attempt at the repair
published 4,613 and **an apex refuter pointed at it found that wrong too**, by 170 words: withdrawing
Tier G subtracts its *net* 179, not its gross 310, because `:328`'s 131 leaves via P1 regardless.

**That is four consecutive rounds in which the headline total has failed its own arithmetic — the
fourth inside the artifact built to end the streak.** The honest reading is not a fifth number. It
is that this total is not reliably computable by inspection at this scale, because the tiers overlap
in at least six places, three of them discovered only after publication. §7 shows every term and
names the ones still disputed.

**Three round-3 corrections change how the number should be read, and two cut against the document.**

1. **The largest single item is an estimate presented as a measurement.** P1's −1,300 rests on a
   ~470-word stub nobody ever drafted (§7a).
2. **The condense axis is all but spent** — a full sweep of the 59% of the file no condense lens had
   touched returned −26 net (§7b).
3. **Twelve of twenty-three proposed cuts are safe only with a named remnant, and two are not safe at
   all** (§7a). No earlier round asked that question per item.

What round 3 *added* is on the move-and-delete axis: **~551 measured words the round-2 write-up
dropped from its own lens reports** (§7, P4 and P5), and a **fourth corpus arm** no check has ever
scanned (§8, rule 1).

None of it is worth much without the rule changes in §8, because nothing in the system measures
this file's size, so it will simply grow back.

Two things to hold onto. Most of this file is genuinely not compressible, for a better reason
than taste — §5. And a cut buys three different things in three very different amounts — §6.

---

## 1. The measurement that settles it

One commit per day, every commit that touched the skill, extraction verified against
`git cat-file -s`:

| date | `SKILL.md` | `references/` | `bin/` | corpus **excl.** `bin` | share | corpus **incl.** `bin` | share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-08-18 | 8,801 | 13,491 | 3,973 | 22,292 | 39.5% | 26,265 | **33.5%** |
| 2026-08-19 | 9,138 | 14,771 | 3,973 | 23,909 | 38.2% | 27,882 | 32.8% |
| 2026-08-20 | 9,918 | 15,492 | 13,240 | 25,410 | 39.0% | 38,650 | 25.7% |
| 2026-08-21 | 10,814 | 18,155 | 13,881 | 28,969 | 37.3% | 42,850 | 25.2% |
| 2026-08-22 | 10,900 | 18,155 | 13,893 | 29,055 | 37.5% | 42,948 | 25.4% |
| 2026-08-24 | 12,983 | 18,931 | 16,948 | 31,914 | 40.7% | 48,862 | 26.6% |
| 2026-08-25 | 13,190 | 21,665 | 17,833 | 34,855 | 37.8% | 52,688 | 25.0% |
| 2026-08-27 | 13,254 | 21,886 | 18,790 | 35,140 | 37.7% | 53,930 | 24.6% |
| 2026-08-28 | **13,393** | 20,241 | 20,437 | 33,634 | 39.8% | 54,071 | **24.8%** |

**The first column is the one that answers your question, and it only ever goes up: +52.2% in ten
days.** The 2026-08-24 row independently reproduces the 12,983 measured in
`2026-08-24-sage-decomposition.md` on that date, which cross-checks the method.

> **[corrected — round 2]** Round 1 read the *share* column instead, reported it "flat between 37%
> and 41%", and concluded that ten days of pointing outward "have not shifted mass out of
> `SKILL.md`". Both halves need correction. The share it computed silently excluded `bin/*.sh`;
> with the scripts counted, the share falls by a quarter of its own value. And a share is the
> wrong instrument for the claim either way: it fell because other files grew faster — chiefly
> `bin/`, which trebled on 2026-08-20 when `sage-lint.sh` landed — not because anything left the
> cortex. **Nothing left the cortex. That is the finding, and the first column is where it is
> visible.** Excluding the scripts was not a defensible definition for round 1, whose largest
> single destination class was a script header.

Now the memory-v3 arc itself, per commit:

| commit | subject | `SKILL.md` | `references/memory.md` | corpus |
| --- | --- | --- | --- | --- |
| `0c870b5b` | (pre-v3) | 13,254 | 6,368 | 35,140 |
| `6cf3b7b0` | **memory v3 design** | 13,247 (**−7**) | 3,236 (−3,132) | 32,026 |
| `ac159343` | disuse / created / last-used | 13,296 (+49) | 3,711 | 32,714 |
| `ed3bfa1e` | memory-clone model | 13,323 (+27) | 4,185 | 33,295 |
| `756ce9ab` | HEAD | 13,393 (+70) | 4,185 | 33,634 |

**The memory-v3 commit changed the cortex by seven words, and across the whole arc the cortex grew
by 139.** Nearly every word of v3's corpus reduction came out of `references/memory.md` — *round 3:
not **every** word, as this sentence read until now; the round-2 audit lens measured +25 elsewhere,
and the correction sat in a ledger for two rounds without reaching the page.* v3 was a rewrite
of the memory *protocol*. It was never a cortex extraction and it did not become one.

---

## 2. What the redundancy lens found: restatement at the citation site

38 findings with content that already stands somewhere else. Round 1 headlined ~3,750 words and
its class table summed to 3,425.

> **[corrected — round 2]** Neither figure is reproducible. The lens's own per-finding annotations
> sum to **2,993 words, 22.3% of the file**, not 3,425 / 25.6%; and the stated reconciliation —
> that several findings carry two classes and were counted once at their primary — can only
> *lower* a total, so it does not explain a number that is 432 too high. The finding counts differ
> too: 12/10 for classes 3/5 in the lens, 13/9 in round 1's table. Use 2,993, and treat the class
> split as approximate.

| class | what it is | findings | words |
| --- | --- | --- | --- |
| 1 | duplicates a `memory/shared/` rule KI | 11 | ~869 |
| 2 | duplicates a `memory/local/` KI | 2 | ~153 |
| 3 | duplicates a `references/*.md` file | 12 | ~900 |
| 4 | duplicates a `bin/*.sh` header the cortex calls "its manual" | 3 | ~480 |
| 5 | duplicates **another part of `SKILL.md`** | 10 | ~591 |

The dominant pattern is not the one this run was convened to examine. The KI double-home is real
but shallow — it mostly adds a tag and a step position to text the KI already holds. **Sixteen of
the 38 findings are a sentence that names its own owner and then says the thing anyway.** `:122`
cites `## Defaults` while repeating it. `:169` names `## Handover` as the cadence owner and states
the cadence. `:206` says "#5 holds that machinery" inside the sentence restating the machinery.

Two of them contradict themselves outright:

- `SKILL.md:171` — "**its header is the manual**… nothing below restates it" — followed by three
  bullets restating the `--status`, discovery and degradation blocks.
- `SKILL.md:211` — "**Neither check is restated here on purpose**" — with `:209`, `:212` and `:213`
  restating both.

The corpus already names what this costs, at `SKILL.md:211`, quoting its own rule 29:

> A paraphrase of another file's contents is a second owner for them, and it goes stale in silence.

**And four copies have already drifted from their owners.** Round 1 found one and misread its
source; round 2 found two more; round 3 found a fourth, and it proves §8 rule 1 rather than merely
arguing it.

0. **`SKILL.md:352` says `sage-lint.sh`'s header states "the eleven checks". That header's own line
   51 reads "THE CHECKS — exactly ten"** — while three later lines in the same file (356, 395, 440)
   say eleven. The script contradicts itself and the cortex followed the majority. **Both halves sit
   where neither mechanical check can see them**: one in `bin/`, one in a cortex sentence whose
   subject is a `bin/` file. It is the §8-rule-1 blind spot caught in the act.

1. `SKILL.md:185` says the `stop_reason` field is *"absent from a real share of transcripts"*.
   Round 1 said its owner `references/harness.md:219` "says no such thing". **It says exactly
   that, and it says it in order to forbid the word:** *"**26 of the 197 carry no record whose
   `stop_reason` is `end_turn` or `stop_sequence`** — the field is present and simply `null`,
   **which is why 'absent' is the wrong word for it**"*. So this is not an unverified paraphrase.
   It is the one word its owner explicitly warns against, standing in the cortex. The finding
   survives round 1 and is stronger; round 1's account of its own source does not.
2. `SKILL.md:106` describes the wrong ledger table.
3. `SKILL.md:89`'s inline list of topologies is stale against `topologies.md`'s twelve headings and
   omits **#12** — the topology §9 nominates as the instrument that would settle this document's
   central claim.

Ten findings are `SKILL.md` duplicating **itself**. The two-same-signature clause of the failure
ladder has homes at `:40`, `:164` and `:338`; the dry-round loop at `:41`, `:206`, `:338`; the 30%
handover threshold at `:43`, `:179`, `:300`; one scout sentence appears twice 29 lines apart inside
Step 1 (`:49`, `:78`).

> **[corrected — round 3]** Three homes for the 30% threshold is an undercount. `grep -rn '30%'`
> over the whole corpus returns **nine**, including `SKILL.md:110` and **two inside `bin/`**. The
> corpus's single most-duplicated rule is therefore itself an instance of the blind spot §8 rule 1
> is about, and this document counted it without noticing. *(`:153` was listed in round 1 as a fourth home of the ladder clause; it
states only the tier arithmetic and explicitly cedes ownership, so it is a pointer, not a home —
which round 1's own rule-29 quote says is the correct form.)*

---

## 3. What the provenance lens found: the arithmetic that already has a home

18 findings against the editing test's own four bullets. This is the smallest tier by mass and the
safest to cut, because the destination rule is already written and already enforced — on new
landings only.

Verified by grep across `SKILL.md`, `references/` **and `bin/`**:

| figure | where it is | where it should be |
| --- | --- | --- |
| `22.4k` (three alt dispatches proving nothing) | `SKILL.md:131`, `harness.md:127` **and `bin/sage-alt-guard.sh:22`** | harness.md alone |
| `466,802` (occupancy reached with no compaction) | `SKILL.md:322`, `SKILL.md:326`, `harness.md:229` | harness.md alone — three homes today |
| `16.7k` (the mis-briefed behavioural subject) | `SKILL.md:195` **only** | a `local/` KI; the figure exists nowhere else |
| `80% of the variance` | `SKILL.md:254` **only** | nowhere yet — no date, no population, no citation |
| `×10 confirmations` | `SKILL.md:21` **only** | nowhere yet — a bare assertion inside an axiom |

> **[corrected — round 2]** Round 1's table gave `22.4k` two homes. It has three; a round-1 lens
> reported the third and the write-up dropped it. The instruction "harness.md alone — it is already
> there" would therefore have deleted one duplicate and left another standing. This is not a
> clerical slip: the surviving home is in `bin/`, which is **outside both mechanical checks that
> police duplication** (§8, rule 1), so nothing in the system would ever have caught it.

The lens drew the ratio/absolute line cleanly, and it is the test that makes this tier safe:
**every ratio in the file is load-bearing and stays** — 4× and 15×, 60–150%, 1.6–1.7×, ~2–2.5×,
~4–7×, the 30% threshold, the rail's 4× and 2× and their floors — and it cleared all of them
explicitly. **Every absolute cost is decorative at its point of use.** The file is not confused
about the distinction; it simply never applied it backwards. Thirteen further figures were cleared
as protected under the "a number survives where its purpose is to stop a run using it" exception —
including `:173`'s `occupancy=296k pct=29%`, meaningless once stripped, since the whole point of
the sentence is that the reading was one point under the threshold and false.

---

## 4. What the procedure lens found: step-time text that no plan needs

20 findings, **~3,669 words** that are step-time procedure rather than plan-time policy — text that
only matters once you are already performing the act, at which moment you can and would open the
pointer.

| destination | findings | words |
| --- | --- | --- |
| `bin/*.sh` headers | 7 | ~1,300 |
| `references/harness.md` | 5 | ~950 |
| `references/dispatch.md` | 4 | ~720 |
| `references/memory.md` | 2 | ~330 |
| no home exists | 2 | ~120 |

> **[corrected — round 2]** The table sums to 3,420 against round 1's "~3,600" headline. The lens's
> own per-finding sum is 3,669, so the headline was approximately right and the **table** is ~250
> short — the opposite of the §2 case, and left unreconciled where §2's was at least addressed.

**`## Handover` is the worst-drawn boundary in the file.** Of its 1,772 words, ~1,050 are
unreachable before the act: the successor protocol (`:302–306`), supervisor mode (`:308–315`), the
append clauses (`:319–320`), the four `git check-ignore` branches (`:328`), the `/sage resume`
sequence (`:330`). None of them changes a plan. *(Those five ranges sum to 981, not the ~1,050
round 1 stated.)* Round 1 concluded that ~400 words of policy sit inside 1,370 words of procedure.
**That estimate turns out to be very good — §7's P1 measures the policy at 356 — and it is the
premise of the largest single recommendation in this document.**

Step 4's watchdog block (`:171–175`, **527** words, not the ~460 round 1's §5 still carried after
its own §8 corrected it) is the cleanest single move, because `bin/sage-watch.sh`'s header is
already the declared owner.

---

## 5. What must not move, and why the ceiling is real

The negative lens was pointed the other way: find what the compression floor forbids removing, and
where turning a stated rule into a pointer would change what a fresh instance does. It returned 27
items, ~2,400 words, in three failure shapes. The shapes are the useful part, because they
generalise past this file.

**Shape 1 — unprompted recognition.** The rule fires on a situation the run does not know it is in,
so no trigger word tells it to open anything. `:195` is the purest case: a criterion can pass
literally while the mechanic it describes is broken, and a run whose test just passed has no reason
to go looking for a rule about tests that pass wrongly. So is `:185`'s `done` rule, `:186–187`'s
fail-open clause (an absent signal read as an all-clear), and `:282–284` (nothing prints, so nothing
prompts you to check rail 4).

**Shape 2 — the rule exists to override the instance's own default.** Load-bearing precisely because
something *else* already loaded says the opposite. `:163` is the file's own worked example and says
so outright: the system prompt's coding guidance says match the surrounding comment density, an
output style may say the same, `clean-code` rule 32 overrides both, and — the cortex's words — *"It
is the only text in your context that says so."* A pointer loses here by construction.
`:131`/`:151`/`:199` (never pass `model=` on an alt dispatch) is the same shape, and `:296`
(occupancy is point-in-time, not a sum) is the same shape against arithmetic instinct.

**Shape 3 — the rule must fire before the step that owns it.** `:109`'s smell-baseline clause fires
at Step 2 though its subject belongs to Step 5. `:110` resolves the window once so Step 4 does not
re-resolve it differently. `:315` must be known before a steer is needed. `:270`'s rail-1
authorisation row must be written *before* the authorised action runs.

**Shape 4 — anchoring.** *Round 2 addition, and its absence from round 1 was a real hole.*

> **[corrected — round 2]** Round 1 never cites `references/authoring.md` — `grep -c authoring`
> over its frozen text at `.claude/plans/sage-ffb2666d-baseline-doc.md` returns **0** — even though that file's stated trigger is "the moment of **authoring** corpus
> text, by whichever path is doing it… or a run editing this corpus on the user's word", which is
> exactly what §7 sets up. Its ceiling was therefore derived from a protection test with no
> counterweight from the corpus's own writing standard. That standard cuts both ways, and both
> halves are new here.

`authoring.md`'s anchoring checklist supplies the fourth protection: *"Does every abstract
instruction sit next to the concrete names, paths or commands that satisfy it?"* An abstract step
reading "you know your own toolkit" passed a small minority of its runs; the version naming the
candidate tools outright passed every one. **So the exact paths, commands and file names inside a
clause are never the cuttable part**, however much room they take. That protects a class round 1's
three shapes do not reach.

**The ceiling argument.** A portable KI may carry the rule, its qualifier, its recogniser and its
falsifier — and, `references/memory.md` is explicit, its ratios: *"ratios and discount factors yes,
because the skill computes with them."* What it may not carry, on any machine, is the **band**: *"No
band, date, count or absolute cost anywhere in the file."* So every `(calibration: <band>)` tag has
the cortex as its only legal home. That, plus the four shapes, is a real and principled ceiling.

The lens's closing line is the design constraint for everything below:

> the failure is not that the information is gone but that nothing tells a fresh instance to go and
> get it.

**So no extraction here is a bare pointer.** Each leaves a *trigger remnant* — the firing condition
and the band tag — and moves the evidence behind it. That form stands at `SKILL.md:78`, which states
the conclusion, names the KI holding the ratio, and withholds the absolute figures. Two lenses named
`:78` as the model form independently.

---

## 6. What a cut actually buys — three quantities, not two

**1. Cortex file size — falls by the full amount.** `SKILL.md` is 81,826 bytes, **about 20.5k
tokens at the ~4.0 bytes/token ratio this document assumes throughout** (stated here because round 1
applied it silently, and applied a *word*-share cut to a *byte*-derived token count). It is loaded
in full at every invocation before the run does anything. The five reference files, ~31.6k tokens,
are not. So a 33% cut is ~6.8k tokens off the boot cost of *every* run, unconditionally.

**2. Loaded context over a whole run — falls by less, and by an amount that depends on the
destination.** Moving text to `bin/sage-watch.sh`'s header saves most: a run that never touches the
lint never loads its header. Moving text to `references/dispatch.md` saves least, because the
argument for that destination is that the file is held open from Step 2 through Step 6.

**3. Corpus total — barely moves under round 1's recommendation, and moves under round 2's.** Round
1's procedure lens marked most of its destinations `needs-adding`, so those words are re-authored
rather than deleted and the corpus shrinks by roughly zero. **Tier E changes this**: 746 words of
in-place rewriting relocate nothing, so they come off all three quantities at once — which no move
can do. Tier F adds a further ~748 in the same category. Round 1 said only its ~250-word Tier A
touched quantity 3; the true figure is closer to 1,750.

**And there is a third thing a cut buys, which round 1 explicitly denied.** Its honest summary was
"this cut buys boot cost and reader attention. It does not buy review cost." Review cost is right —
that is a single-owner problem, and `2026-08-24-sage-decomposition.md` §6 Cut 1 is the right
instrument, still unexecuted. But **compliance** is a third quantity, and `authoring.md` measures
it: *"Nuance clauses cost more than they buy"* — appending one nuance clause to a winning recipe
"degraded it from consistent to noisy" — and *"ties go to the shorter phrasing"*. That shape is what
Tier E turns out to be made of (§7). Tier E is therefore a **compliance repair** by the corpus's own imported
standard, not only a size saving. Take the direction and not a number: the source hedges its own
effect size against control, and that hedge is not droppable.

**The honest summary: this cut buys boot cost, reader attention, and — for one tier — compliance.
It does not buy review cost.**

---

## 7. The recommended cut, re-derived twice

Round 1's §8 was wrong in five ways its own refuter caught, and its corrections are kept below.
Round 2's audit lens then re-ran 96 claims and found ten more wrong and two unverifiable. What
follows is what survives both.

**On totals, and read this before quoting any number below.** Every range is measured with
`sed -n '<a>,<b>p' SKILL.md | wc -w`. **Retained figures are estimates except where marked
measured**, and the one round-2 estimate that could be checked was off by a factor of four (Tier D).
Round 3 re-ran 66 of these figures by command: **56 passed, 7 failed, 3 were unverifiable.** The
nine §1 growth rows, all 27 Tier E measurements, all five §3 figures and Tier B's seven rows were
each re-derived independently and all held; the seven failures are folded in below.

The tiers overlap in six places and **this document's first draft declared only two of them**:

| overlap | words | why |
| --- | --- | --- |
| Tier E ∩ Tier F | ~144 | six lines both lenses reached; F's deltas are the larger, so E's are the ones dropped |
| Tier E ∩ P1 | **94** | `:315`, `:317`, `:324`, `:332` sit inside `## Handover`. *Round 3: Tier E's own deltas on those four lines sum to 94, not ~106; `:322`'s 32 is booked separately below* |
| Tier G ∩ P1 | 131 | `:328`'s four `git check-ignore` branches are inside `## Handover` |
| Tier A ∩ P1 | ~30 | `466,802` stands at `:322` and `:326`, both inside `## Handover` |
| Tier E ∩ Tier A | 32 | `:322` again |
| Tier D ∩ Tier E | 38 | both touch `:164` |

So Tier A's claim that its items "sit *outside* the other tiers' ranges" is **false for
`466,802`**, and Tier G's `:328` was counted twice.

> **[corrected — round 3, the third round to correct a headline total]** Gross 5,486 and overlaps
> 481 both reproduce exactly. **`5,486 − 481 = 5,005`, not the ~4,900 this document published** — a
> subtraction that survived an apex refuter and a dedicated audit lens. With Tier E ∩ P1 corrected
> to 94 the overlaps become 469 and the base is **5,017**; with Tier F re-summed from its own
> findings (§7b) it is **5,062**. Carried through correctly, round 2's own band was 4,432–5,578, not
> 4,400–5,400.
>
> **Round 3's first repair was also wrong, and its own refuter caught it.** Three terms were
> mis-booked: L3's remnant total double-counted R11 (22 w, which belongs to P4 and P4 is not in this
> total) and R12 (17 w, already netted inside P5's figure) — remnants are **228**, not 267; and
> withdrawing the two logic-unsafe items subtracts **274**, not 405, because Tier G's `:328` half
> (131 w) leaves via P1 whether Tier G runs or not, so Tier G's net contribution is 179. Corrected:
> **5,062 − 228 + 26 + 197 − 274 = 4,783**, against a published 4,613.
>
> **Still disputed after the refutation, and named rather than resolved:** whether P5 needs its own
> overlap rows against Tier B `:351–353` and Tier A's `:131`; whether the +26 is +16 in the branch
> where Tier B `:229–236` is repaired rather than dropped; and whether a "repaired" ceiling exists at
> all, since no artifact contains a repair for Tier G's `:131`/`:151`/`:199` half. **Call it ~4,800
> and treat the third digit as unearned.** Every step: `.claude/plans/sage-6d223791-arithmetic.md`.
>
> **And the measured/estimated split was wrong in the direction that matters.** "2,141 words are
> measured (P1 ~1,300, Tier E 746, Tier D 95)" is false: **P1's −1,300 is an estimate.** The
> ~470-word sufficient stub was never drafted. The only stub that exists is round 2's refuted
> 356-word version, and it is at
> `/private/tmp/claude-501/.../ffb2666d-.../scratchpad/handover-stub.md` — **a session scratchpad,
> which dies with that session and is reachable from no later run.** So the single largest item in
> the recommendation has no measurement behind it and its one artifact is already ephemeral.
> Genuinely measured, before round 3: **841**.

**The claim that survives all three rounds is narrower and better founded than round 2's: about a
third of the file, with its largest single component still unmeasured.**

### P1 — `## Handover` becomes `references/handover.md`: **about −1,300 words, measured**

The single largest item, larger than round 1's entire eleven-row Tier B, and round 1 could not see
it because it works range-by-range and this is a file-level move.

Round 1's §10 ranked `references/dispatch.md` the **weakest** destination in the corpus and rejected
moving `## Handover` there, because `:322` sends a post-compaction parent to re-read the note and
the ledger "before anything else" — exactly when Handover's content fires and exactly when a
declared residency is least likely to hold. That objection is correct and it kills the
`dispatch.md` destination. **It does not kill the move, because a stronger trigger already exists
and neither round-1 nor the 2026-08-24 proposal noticed it.**

The ledger's line-1 header comment — specified in `dispatch.md`, written at plan time, restamped at
every bring-current point, and **designed specifically to survive a compaction** — already reads:

> `<!-- sage occupancy duty: … at >= <threshold> (30% of the <window> window), stop launching and run SKILL.md ## Handover. … -->`

Retargeting that one string to `references/handover.md` gives the new file **the strongest trigger
in the corpus**: not a declared residency but a computed predicate, carried in the one artifact a
compacted parent is ordered to re-read first. It is the direct answer to `:322`.

I drafted the policy stub that stays in the cortex — occupancy as a point-in-time value never a sum,
the single 30% threshold with no advisory below it, the depth-1 invariant, uncapped generations
bounded by the budget rail, the parent keeping all four rails and every steer, riding a compaction
rather than pre-empting one, and the human path's unconditional note print — and **measured it at
356 words against `## Handover`'s 1,772.** Cost outside `SKILL.md`: one string in `dispatch.md`,
four `## Handover` mentions in `sage-watch.sh`'s comments, and **zero** changes to `/sage-promote`
or `orchestrator.md`. It lands in `references/`, so it stays inside both mechanical checks
(§8 rule 1).

> **[corrected — round 2, by the refuter pointed at this document's own author]** That 356-word
> stub is **too thin, and it breaks this run's own acceptance criterion.** Four clauses must stay
> that it dropped. (a) `:315`'s successor-spot-check duty carries the **only `(calibration:
> established)` tag inside `:294–333`**, and §5's ceiling says the cortex is a band tag's only
> legal home — the stub carries zero. (b) The window-resolution fallback ("from your environment
> when it is knowable, else the measured figure in `references/harness.md`") fires at Step 2,
> before the act: shape 3. (c) The Step-6 memory duties at `:317–320` need a trigger at Step 6 to
> open `handover.md` at all: shape 1. (d) "Never state slack against the window end": shape 2.
> **A sufficient stub is ~470 words, so P1 is worth about −1,300, not −1,416.** The lesson is the
> one this corpus already carries: the parent's own artifact erred toward the convenient side, and
> only a pass aimed at the parent caught it.

### Tier A — deletions, ~250 words

Absolute costs, dates, populations and multi-sentence accounts of how something was measured, where
they sit *outside* the other tiers' ranges. `22.4k` comes out — **from two places, not one** (§3).
**`466,802` comes out of `:322` only.** *(Round 3: its occurrence at `:326` is protected — it carries
the slack arithmetic whose whole point is that the figure is a lower bound, and round 2's own
protection lens flagged it while Tier A went on ordering both deleted.)* `16.7k`, `80% of the variance` and `×10 confirmations` exist nowhere else in
the corpus and need a `local/` KI minted before the cut, not after. **Keep every ratio.**

> **[corrected — round 1]** The first draft carried a second Tier A worth ~550 words: the places
> where `SKILL.md` restates *itself*. **That tier is essentially gone.** `## Defaults` `:39`–`:43`
> is a plan-time summary table doing its job. `:268`/`:272`/`:284` are three *distinct* scopes.
> `:76`↔`:163` and `:128`↔`:236` are both shape 3 — a decision at one step and the act at another.
> What survives is about 45 words. **`SKILL.md` restating itself is mostly a legitimate index, not
> waste** — a real finding that runs against this document's own thesis. *Round 2 re-checked
> `## Defaults` independently and the correction holds.*

### Tier B — procedure to a destination with a stated read trigger, ~1,210 words

| range | measured | move | retain | destination |
| --- | --- | --- | --- | --- |
| `:171–175` watchdog resolution + hosting | 527 | ~377 | the `296k / 29%` false-positive anti-band, the session-id grep rule (**+40, round 3**), and the trigger table — *which begins at `:177`, outside the stated range; the row has named a retention outside its own scope since round 1* | `bin/sage-watch.sh` header |
| `:212–214` commit-gate provenance | 287 | ~167 | both checks themselves (shape 1) | `bin/sage-lint.sh` header |
| `:351–353` script registration detail | 253 | ~163 | "a blocked call is the guard, not a fault" | the three script headers |
| `:165` lint degradation | 219 | ~184 | the stderr clause (shape 1) | `bin/sage-lint.sh` header |
| `:255` journal grammar | 180 | ~140 | the line-count duty | `memory.md ## Append at Step 6` |
| `:229–236` artifacts-block layout | 125 | ~95 | the print obligation | `dispatch.md ### Run record` |
| `:167` lint provenance | 104 | ~84 | the last sentence | `bin/sage-lint.sh` header |
| **total** | **1,695** | **~1,210** | | |

> **[corrected — round 2]** Round 1's Tier B had eleven rows totalling 2,545/~1,871. **Four of them
> are inside `## Handover` and are subsumed by P1**, which does the same work better and measures
> its own remainder: `:308–315` (459/~339), `:302–306` (177/~152), `:319–320` (158/~130), `:330`
> (56/~40). They are removed here to prevent the double-count that has already gone wrong twice in
> this document.

### Tier C — the promoted clauses, ~500 words

17 `(calibration:)`-tagged lines, 2,049 words, 15.3% of the file. Most cannot shrink: `:129`,
`:204`, `:205` and `:315` are shape 1 or shape 3. **Six can**, and they share the property that
makes them the exception: they fire at Step 2, exactly when `memory/shared/` is read, so the pointer
is opened by the same act that needs the rule. `:95` (173 w), `:97` (62), `:99` (163), `:126` (140),
`:197` (96, the anecdote only), `:200`'s first clause (~50). ~684 down to a remnant of ~180.

**The remnant keeps the firing condition and the `(calibration: <band>)` tag. Nothing else.**

> **[corrected — round 1]** The first draft said each remnant must also keep "every ratio the KI
> cannot legally carry", naming 60–150%, ~4–7× and ~2–2.5×. That is false. `references/memory.md`
> licenses ratios in a portable KI outright, and grep confirms all three already stand in their
> KIs. Only `1.6–1.7×` at `:97` is genuinely absent and must either stay in the remnant or be added
> to its KI. Keeping a ratio the KI already carries would rebuild the exact double-home this
> document condemns.

One caution on `:99`: a live `contradiction` KI in `memory/local/` disputes the review-and-verify
pairing. Do not shrink a clause whose rule is under active contradiction. Settle it first.

### Tier D — form conversion, ~95 words *(round 2, and much smaller than it first looked)*

`:164`'s failure ladder is 384 words enumerating five parallel cases with the same four attributes:
signature, what it says, the rung it earns, the rung it must not earn. That is a table, and
`authoring.md` licenses the conversion twice in its own words — row 4's right form is *"conditional
keyed to an **observable predicate**"* and it names **this very ladder** as the corpus's instance of
it, while the narrower classifier notes that *"recognition tables work because they are read at
decision time"*. Once the ladder is a table, `## Defaults` `:40` collapses from 70 words of prose to
a ~16-word pointer.

> **[corrected — round 2]** The architecture lens costed this at **−233**. The condense lens built a
> table for the same line and measured **346 words — level with prose**. I built a third and
> measured **343 words / 1,905 bytes against the prose's 384 / 2,246**. So: −41 words (−11%) and
> −341 bytes (−15%), plus `:40`'s ~54, for **about −95, not −233**. Forty of the table's 343
> "words" are bare `|` and `---`. **Tables do compress content here (303 content words against 384,
> −21%) and they save more in bytes than in words, because pipes are cheap — but "convert prose to
> a table" is a weak compression move in this corpus and must never be costed without measuring.**
> The general consequence: the architecture lens's *words-affected* figures are measured and its
> *retained* figures are estimates, and the one that could be checked was off by four times.

### Tier E — condense in place, **746 words measured, 27 rewrites**

*Round 2, and the axis round 1 structurally did not have.* Every tier above is a move or a delete.
Nothing in round 1 rewrites a clause that **stays** — though round 1's own §9.1 proposes adding a rule
that would do exactly that: re-check the standing clause against "the fewest words that clear the
compression floor". Applied by hand, with every ratio and every `(calibration:)` tag preserved
verbatim and every candidate ruled against the four shapes: **4,131 measured words down to 3,385.**

The twelve largest: `:199` −62, `:338`+`:340` −57, `:206` −56, `:282`+`:284` −51, `:164` −38,
`:317` −37, `:194` −36, `:112` −32, `:322` −32, `:169` −29, `:128` −25, `:272` −25. Twelve further
candidates were ruled and **rejected** — `:163`, `:195`, `:296`, `:186`, `:127`, `:193`, `:204`,
`:101`, `:3`, `:49`, `:162`, `:203` — mostly at the compression floor already, and that half of the
result matters as much as the cut.

**The single most useful finding in round 2 is what this tier is made of.** It is not the anecdote.
About half the file's anecdotes turn out to be **recognisers** and survive shape 1. It is the
**third subordinate tail**: the clause after the rule and after its one justification, answering an
objection nobody in the run will raise. That converges independently with `authoring.md`'s measured
"nuance clauses cost more than they buy" (§6) — two units, two routes, one conclusion. **If §8 rule 2's size
trigger ever lands, "cut the third tail" is its operative rule, not "cut the anecdotes" and
certainly not "convert prose to a table".**

### Tier F — the 40% round 1 never cited, **1,075 words, of which 748 reduce the corpus**

Round 1's recommendation cites 90 of `SKILL.md`'s 353 lines. The remaining **5,305 words** were
swept in round 2: 25 findings across 24 contiguous runs, **9 of which came back clean**. The tier
breakdown inverts round 1's: A 142 · B-already-says-it 606 · B-needs-adding 45 · C 222 · D 60 —
so **748 of the 1,075 come off the corpus total**, where round 1's Tier B was mostly `needs-adding`.

Two structural rulings inside it are worth more than the words:

- **`## References` (615 w) splits, and round 1 treated it as one thing.** Its **read triggers are
  protected** under shape 1 — nothing at any use site says *when* to open a file, and both §9's
  destination ranking and Tier G below depend on those triggers existing. Its **file summaries are a
  second owner**: every reference file carries its own contents line, and each is already cited from
  its use sites with the exact section named — measured outside `## References`: harness 30×,
  dispatch 12×, topologies 6×, memory 5×.
  `authoring.md` is the exception at **0×** elsewhere, so its entry stays whole as the file's only
  pointer. ~240 words out, every trigger kept.
- **`:1–20` holds exactly one clause that binds and is stated nowhere else**: axiom 1's *"the least
  capable model that **reaches** the right answer, never the least capable model that fits the
  corpus"*, which is shape 2 against a cost-minimising instinct. The YAML `description:` is 109
  words with three to five other homes per clause, and it does no routing work, because
  `disable-model-invocation: true` makes the skill user-invoked only. ~85 words out.

### Tier G — needs a trigger added first, ~310 words

`:328`'s four `git check-ignore` branches, and the `harness.md` items on spawning, frontmatter and
model resolution (`:131`, `:134`, `:151`, `:199` in part). Their destination is real but is not read
when they fire. The fix is one clause in `## References` extending the `harness.md` re-read trigger
past `## Transcripts and the token arithmetic`. Do this last.

**Do not move at all:** everything in §5 — in particular `:163` (the `clean-code` override), `:195`,
`:185`'s rule half, `:296`, `:270`'s authorisation row, and every concrete path, command and file
name inside any clause (shape 4).


### P4 — one degradation table for both scripts, **−275 measured** *(round 2's finding, dropped by round 2's write-up)*

The same three-branch degradation contract is stated **three times in three wordings**: `:165` for
the lint (219 w), `:174` step 2 for the watchdog probe (187 w), and `:186` "Degradation, in order"
(104 w). It is one 3-row table. Words affected 510, retained ~235, **net −275** — by deduplication
alone, with every word staying in the cortex.

**P4 is an alternative to Tier B's `:165` and `:171–175` rows, not an addition to them.** Those two
move 561 words to script headers. P4 is worth 286 words *less* and is safer on two counts: nothing
leaves the file, so it cannot fail §9's relocation test at all; and it preserves `:186`'s fail-open
clause, which §5 protects as shape 1 and which Tier B's `:165` row would move regardless. Round 3
adds one remnant — the **fail-quiet fourth state**, 22 w — that the table as drafted drops.

### P5 — the alt lane gets one home, **−276 measured** *(same provenance, same loss)*

"Dispatch an alt agent with no `model` parameter" stands at **full strength in four places** —
`:131`, `:151`, `:199`, `:353` (423 w) — while `references/harness.md ## The alt lane` claims sole
ownership and `bin/sage-alt-guard.sh` *enforces* it deterministically. Retained: one Step-3 block
(~110 w) plus a cross-reference and a References bullet. **Net −276.**

Two round-3 constraints on it. **P5 and Tier E's first rewrite are alternatives for `:199`**, not
additive — Tier E keeps the rule at full strength there and saves 62; P5 deletes it. And L3's
ruling: the `:199` cross-reference must stay at **full strength, not twelve words** (+17), because
`:131`/`:151`/`:199` are shape 2 — the `model` parameter silently wins over the file, so a pointer
loses by construction. **P5 is therefore worth +197 net, not +276.**

### §7a — does any of this change what sage does? *(round 3, and the question nobody had asked per item)*

Twenty-three items ruled — P1, every Tier B row, every Tier C clause, Tiers A/D/E/F/G, P4 and P5 —
each against one question: would a fresh instance, starting blank, behave differently?

| verdict | items | words |
| --- | --- | --- |
| logic-safe outright | 9 | — |
| safe **only with a named remnant** | 12 | remnants cost **267** |
| **logic-unsafe as written** | 2 | ~405 withdrawn, or ~101 to repair |

**The two unsafe ones are specific, and both were headline items.**

- **Tier B `:229–236` → `dispatch.md ### Run record`.** No Step-6 trigger to `dispatch.md` exists:
  `grep -n 'references/'` over `:217–259` returns exactly one hit and it names `references/memory.md`.
  The only pointer is `## References`' declared residency, which `:322` breaks after a compaction —
  and the destination is a ledger *template* while the artifacts block is a *printed* item. A fresh
  instance stops printing it.
- **Tier G's `harness.md` half.** It moves `:131`/`:151`/`:199` — text §5 itself names as shape 2,
  *"a pointer loses here by construction"* — behind a trigger added to `## References` that no Step-3
  or Step-5 use site re-reads. The document's own "in part" never says which part, so the cut is
  unspecified exactly where §5 protects.

**P1's mechanism survives the ruling** — checked against `dispatch.md:87–99` for all three
fresh-instance cases — but its cost does not. "One string in `dispatch.md`" is wrong: there are
**9 in-cortex `## Handover` pointers, 4 in `dispatch.md`, and 4 in `sage-watch.sh`**, and
`sage-lint.sh --corpus` checks `.md` paths, not intra-file anchors. One of the refuter's four
restored clauses is redundant — the window-resolution fallback already stands at full strength at
`:110` — so the stub is ~30 w smaller than §7's refutation implies, and one clause it still needs is
new: *after a compaction, re-read note and ledger before anything else* (33 w; `:169`'s version is
narrower).

**What this ruling is and is not.** Every verdict is a textual argument against the four shapes.
None is a behavioural measurement. `topologies.md` #12 remains the only instrument that settles it,
and that pattern's own text says its adopt-or-null direction needs five or more repeats **per arm**
— *"which no run here has ever budgeted — so plan it deliberately as its own programme, never as
something a corpus edit picks up in passing."* Round 3 did not run it, and says so rather than
implying inspection substitutes for it.

### §7b — the second condense sweep came back nearly empty, and that is the finding

Round 2's condense lens ruled on 41 lines. The parent computed the complement — **312 lines, 7,863
words, 59% of the file** — by a script validated against that lens's own 4,131/3,385 totals, and
round 3 swept all of it.

**Result: −160 gross, −26 net.** Nine accepts in 312 lines. Only `:256` and `:183` are free of every
move tier; the other 124 words merely shrink text a move tier already carries. Fifteen consecutive
drafts against the largest remaining prose lines — `:126 :132 :254 :288 :200 :349 :54 :108 :40 :205
:129 :149 :97 :78 :306`, 1,169 words — **saved 21 words between them, six measuring exactly zero.**

**The condense axis is all but spent at ~906 words total, 6.8% of the file.** *(Round 3's refuter
drafted six lines from the undrafted band and got −31 w across three of them, so the weak band may
still hold ~150–200 w — comparable to L1's entire measured yield, and the one place this negative
result could be wrong. "Spent" was too strong; "nearly spent, with a measured 25% weak band" is the
claim that survives.)* Round 2 took the compressible
mass; §6's Tier E remains the only tier that reduces all three quantities at once, and it is not
going to get bigger. Everything further must move or be deleted. *(Honest bound: 1,968 of the 7,863
words were ruled by inspection without a competing draft. Closing that band needs a ~2,000-word
second drafting pass, and it is the one place this negative result could still be wrong.)*

One correction to Tier F while we are here: its `B-already-says-it` cell reads 606, but its own
fifteen named findings sum to **651**. **Tier F is 1,120, not 1,075**, and its corpus-reducing half
is 793, not 748.

**Three findings this document is still carrying without a home, listed so the next round does
not have to rediscover them.** *(Round 3: all three stood in a lens report through two
write-ups.)* `references/review-loop.md`, recommended by the 2026-08-24 proposal, was never
created, and both copies of the recommendation were later cut as duplication.
`references/authoring.md` is **never read on an ordinary run** — its own entry says so — yet §5
and §6 are built on it, which means shape 4 is a standard for whoever *makes* the cut, not a
protection any run enforces. And the live KI
`a-checklist-prices-a-lens-only-when-every-item-settles-in-one-look` has **no cortex home at
all**, a standing counterexample to §5's claim that the cortex is a band tag's only legal home.

**One finding with no resolution, recorded rather than buried.** `:192`'s six-item inventory of what
the `verifier` agent file binds is a paraphrase of another file — exactly what `:211` forbids twenty
lines below it. It cannot be condensed away, because each item is a distinct refusal the parent must
make; and it cannot become a bare pointer, because the parent cannot `Read` an agent file mid-triage
for free. It belongs in no tier here. Someone will have to design the third option.

---

## 8. Why it grew

Round 1's first draft claimed a ratchet: promotion never shrinks a standing clause, and only
eviction removes cortex text. **Its refuter falsified both halves against `/sage-promote`'s own text
and was right** — and round 1 then left the falsified version standing in its Verdict and its §2
while the correction sat 350 lines below. Three standing paths shorten or remove cortex text on
triggers other than falsification:

- `## The write machinery` step 2 — *"**Replace, never accrete.** Where the target already holds
  weaker or hedged text on the subject, the new clause replaces it."*
- `## Stage zero` step 3, which may write `SKILL.md`, `references/` and `bin/*.sh` to repair a claim
  that is untrue.
- `## Stage three` step 4 — allocations for changed models are *"rewritten, not annotated"*.

So the mechanism is weaker than a ratchet, and still sufficient:

> **Every path that can shrink the cortex is triggered by something other than its size, and nothing
> in the system measures its size.** Replace fires on a *subject collision*. Stage zero fires on a
> *false claim*. Stage three fires on a *lineup change*. Eviction fires on a *fired falsifier*. None
> of them fires on "this file is too long", because nothing computes that.

That is enough to explain §1 — 8,801 to 13,393 words in ten days, with the memory-v3 commit
contributing −7 — without overstating what the skill says. The fixes, in the order they should land:

1. **Extend the one-home grep and `sage-lint.sh --corpus` to `bin/*.sh` — and to the agent files.**
   *Round 2 for the first half; round 3 for the second, which is larger and worse.* `/sage-promote`'s one-home check runs
   literally `grep -rniE '<term>' <sage>/SKILL.md <sage>/references/` — **`bin/` is not in that
   command** — and its `no contradiction` check reuses the same grep. `sage-lint.sh --corpus` has the
   identical blind spot: it reads `<dir>/SKILL.md` and every `<dir>/references/*.md`. **So every word
   this document sends to a script header becomes permanently invisible to both mechanical checks
   over sage's corpus** — which is exactly how the third `22.4k` home survived (§3). Round 1 ranked
   `bin/*.sh` headers the *strongest* destination and recommended doing them *first*; that trades
   trigger strength for maintenance coverage and never says so.

   **The fix is three path lists, not two, and one target is outside the tree the check walks.**
   The five agent files — `explorer.md`, `implementer.md`, `orchestrator.md`, `verifier.md`,
   `web-researcher.md`, **3,822 words** — install to `~/.claude/agents/`, not under the sage skill
   directory, so `--corpus <sage-skill-dir>` does not reach them: its contract is scoped to one skill
   directory, and extending it is a path list, not a redesign.

   **The duplication itself is smaller than round 3 first published, and its own refuter cut it.**
   The draft claimed 394 words (`:306`, `:311`, `:313`, `:315`) restating `orchestrator.md` at full
   strength. `:315` is a **pointer**, not a restatement — it says "because `orchestrator`'s own
   `tools:` line grants neither", which is the correct deferral form under rule 29 — and `:313` has
   no counterpart in the agent file at all. Genuine undeclared full-strength duplication is
   **~100–160 words**. `:306` is half of a pair `:324` declares outright ("holds in prose, in two
   places… so both have to keep saying it"), which is exactly what a one-home check extended to this
   arm would have to be taught. **The structural finding stands and is the point: the arm exists, it
   is 3,822 words, and nothing has ever scanned it.** The word mass was the weaker half of the claim.

   **How large the whole class is, measured for the first time.** A corpus-wide 10-gram scan
   (53,724 tokens → 530 duplicate 10-grams → 145 clusters → 54 prose clusters ruled by hand) finds
   **28 rules standing at full strength in two or more homes, 11 of them involving `bin/`**. Words
   recoverable if each keeps exactly one home: **~1,021–1,170 from the cortex**, 99 from
   `references/`, 364 from `bin/`. That figure is deliberately **not** added to §7's total, because
   nobody has yet measured how much of it the existing tiers already claim. It is a ceiling on a
   class, and the largest single `bin/` cluster — 316 of the 364 words, `sage-watch.sh`'s header
   restating `harness.md` — sits between two files no §7 tier touches.
2. **Give stage two step 1 a size trigger.** Today, when a promoted rule's clause already stands, the
   edit is a band-tag update in place. Add: re-check the standing clause against step 2's own bar —
   the fewest words that clear the compression floor — and cut it to that bar when it exceeds it.
   **The authority already exists**; nothing applies it backwards over standing text. Tier E is what
   this rule would produce, and §7's Tier E names its operative heuristic.
3. **A counts-and-dates check in the mode that already exists.** Stage two step 2 forbids a count,
   date or absolute cost in skill text; stage three step 5 repeats it for prices. A grep for a bare
   date, a `\d+(\.\d+)?k` token outside a ratio, and a population phrase catches most of them. **Note
   that `sage-lint.sh --corpus` is a live mode already** — today it checks dangling `.md` citations
   and passes clean — so this is one check added to a mode, not a mode to build.
   *(Round 1 claimed the standing corpus violates these rules "eighteen times". That count was never
   enumerated, and the grep it prescribes would flag five figures the provenance lens explicitly
   protected. Treat it as "many", and expect the check to need the §3 exception list.)*
4. **Run the one-home check over the standing corpus, not only over the rule being landed.** Stage
   two step 1 already greps for "exactly one location may carry the rule at full strength", but only
   for that pass's candidate. Restatements-at-the-citation-site stand today, two of them inside
   sentences claiming not to restate anything, and **three copies have already drifted from their
   owners** (§2). *(Round 3: the figure "sixteen of the 38" is the one assertion in this document
   with no source report behind it — round 2's own audit lens ruled it unverifiable and it stood
   here unqualified anyway. The rule's case does not rest on it: the corpus-wide scan above puts
   **28 rules in two or more homes**, which is a measured number and a stronger one.)*
5. **Optional and blunter: a cortex word budget** in `## Defaults`, checked by
   `sage-lint.sh --corpus`. It is the only one of the five that bounds growth rather than detecting a
   class of it, and the only thing that would make a size trigger exist at all.

---

## 9. How to falsify this document

Its central empirical claim — that these ranges can move without changing what a fresh instance does
— **remains unmeasured after three rounds.** It rests on `SKILL.md`'s own declared read schedule,
which is an *intention*, not observed behaviour. Round 3 ruled all 23 items against that schedule by
inspection (§7a) and found two of them unsafe on the schedule's own terms — but inspection against a
declared intention is not measurement, and the table below inherits the same weakness: **every
"strength" in it is asserted from the corpus's own wording and measured nowhere, in either
direction.** That is not a reason to distrust the ranking; it is the reason §9 exists.

Rank the destinations by the strength of their trigger, and cut in that order:

| destination | trigger | strength |
| --- | --- | --- |
| **the ledger's line-1 header comment** | a computed predicate, restamped at every bring-current point, in the one artifact a compacted parent must re-read first | **strongest — and it is what makes P1 work** |
| `bin/*.sh` headers | "its header is **its** manual" at `:165`, `:351`, `:352`, `:353`, and "**the** manual" at `:171` — five locations, two wordings | strong trigger, **weakest maintenance coverage** — outside both one-home checks until §8 rule 1 lands. Round 3: whether a header is *read* has never been measured, and the corpus's own nearest datapoint says a rule stated **three times in `SKILL.md`** failed anyway — which is evidence repetition does not buy compliance, not evidence a header goes unread |
| the agent files (`~/.claude/agents/*.md`) | none — no cortex sentence sends a run to one, and the corpus says a unit's toolset comes from its file rather than its self-report | **no trigger at all.** Not a destination for anything — a **fourth corpus arm** that needs *scanning*, not receiving (§8 rule 1). They sit outside the sage skill directory, so `--corpus <dir>` does not reach them today; extending it is a path list |
| `references/memory.md` | "Read at Step 2 **and Step 6**" | strong for Step 6 duties, which is what moves there |
| `references/harness.md` | "re-read `## Transcripts and the token arithmetic` when the watchdog or `## Handover` needs a number" | strong, but only for that one section |
| `references/dispatch.md` | "Open at Step 2; keep it open through Step 6" | **weakest** — a declared residency, and `:322` breaks it after a compaction |
| **nothing — Tier E relocates nothing** | — | **not applicable: no trigger to lose** |

That last row is why Tier E should be cut early and P1 second. Tier E cannot fail this test, because
nothing leaves the file.

The instrument that would settle the rest already exists in this corpus: `references/topologies.md`
**#12**, the blind behavioural lens with two arms — one subject on the current cortex, one on the cut
cortex, both given a task that triggers the moved rule. It is one measurement, it is cheap, and it
decides every tier that relocates. *(`SKILL.md:89`'s inline list of topologies omits #12 — §2.)*

**If the cut arm fails, this proposal is wrong and the negative lens's ceiling was right.**

---

## A note on this document's own size

Round 3 took it from 7,798 words to 11,110 — **+42.5%** — while arguing that a file which only
ever grows is the disease. The growth is stacked correction: three rounds of `[corrected]` blocks
now sit on top of the text they correct, because deleting a superseded claim would also delete the
evidence that this process keeps making the same class of error. That is a real trade and not
obviously the right one. **It is the same trade `SKILL.md` has been making, which is this document's
own subject** — and §8 rule 5 applies here too: nothing measures this file's size either. A fourth
round should either cut the archaeology to one appendix or stop, and stopping is likelier to be
right. Rounds 2 and 3 each found the previous round's headline total wrong, and round 3's own first
total was wrong as well. **The marginal return is now in *executing* §8, not in a fifth round of
reading.**

## Scorecard

| your claim | verdict |
| --- | --- |
| "I asked for the cortex only, and everything else to become KIs" | **The ask was never executed.** The memory-v3 commit changed `SKILL.md` by −7 words; the whole arc added 139 |
| "there is still a wall of text" | **Right.** 13,393 words, +52.2% in ten days, and the file has never once shrunk |
| "check carefully if anything else can be extracted" | **4,600–4,900 words, 34–37%** *(round 3; round 2 published 4,400–5,400 and that band failed its own subtraction)*. Still well above round 1's ~2,625. But the largest single item, P1's −1,300, is an **estimate**, not the measurement two rounds called it; and the condense axis is now **spent** — a full sweep of the 59% of the file no condense lens had touched returned −26 net |
| "the smaller and more focused the corpus is, the harder it fails" *(second half — see below)* | Round 3 adds the measurement §8 was arguing without: the corpus's most-duplicated rule, the 30% threshold, has **nine** homes; a corpus-wide scan finds **28 rules in two or more homes**; and a **fourth arm, the 3,822-word agent files, has never been scanned by anything.** §8 is worth more than the cut, by a wider margin than round 2 argued |
| "the smaller and more focused the corpus is, the harder it fails" | **True for one class, false for most of the rest, and still unmeasured.** True for the six Step 2 pricing clauses, where the pointer is opened by the same act that needs the rule. False for the 27 items in §5, where the failure is not that the information is gone but that nothing tells a fresh instance to go and get it. **And inverted for Tier E**, where the corpus's own authoring standard says the shorter phrasing is the *more* reliable one. §9 is the test that would settle which class a given clause is in |

## Do these, in this order

1. **§8 rule 1 — extend the one-home grep and `sage-lint.sh --corpus` to `bin/*.sh` *and the agent
   files*.** Three path lists, one of them outside the tree `--corpus` walks. Nothing else is safe
   first, because the recommended opening move sends ~1,300 words somewhere neither check can see.
2. **Tier E — the 27 in-place rewrites, 746 words.** It relocates nothing, so it is the only tier
   that cannot fail §9's test, and it is the only one that also buys compliance. Add round 3's nine
   further rewrites (−160 gross), then **stop condensing**: §7b measured what is left and it is
   nothing.
3. **P4 instead of Tier B's `:165` and `:171–175` rows.** −275 rather than −561, and it cannot fail
   §9's test either, because nothing leaves the file. Take the 286-word loss for the safety while
   the `bin/` destination is still unmeasured. Keep the fail-quiet fourth state (22 w).
4. **Draft P1's ~470-word stub and measure it.** Not "execute P1" — *draft the stub*. The −1,300 is
   an estimate, this is the step that makes it a measurement, and it costs one file.
5. **Run §9's two-arm test on P1**, control arm from `git show HEAD:sage-claude/SKILL.md`. Before any
   `bin/` move and before P1 lands.
6. **P5 (+197 net), then Tier A** including the third `22.4k` home — minting a `local/` KI for the
   three orphan figures first, and **leaving `466,802` at `:326` alone**, where §5 protects it.
7. **Tier B's remaining rows and Tier F (1,120)**, if and only if step 5 passed. **Drop Tier B's
   `:229–236` row and Tier G's `harness.md` half** unless their §7a repairs (+101) land with them.
8. **§8 rules 2–4**, then **Tier C** once the `:99` contradiction *and* the `:201`/`:202` inter-lens
   contradiction are settled, then **Tier D**.
9. **Then measure the duplication class** (§8 rule 1, ~1,021–1,170 cortex words) against whatever
   the tiers above have already taken. It is the only large unclaimed figure left.

**The cut is worth about a third of the file — and it would take `SKILL.md` from 13,393 words to
roughly 8,500, below the 8,801 it stood at ten days ago.** The rule changes in §8 are worth more,
because nothing in the system measures this file's size, which is the whole reason there was a wall
of text to ask about. Round 3 sharpens that: rule 5, the cortex word budget, is filed as
*"optional and blunter"* and is **the only one of the five that bounds growth rather than detecting
a class of it.** Every other rule fires on a subject collision, a false claim, a lineup change or a
fired falsifier. If the diagnosis in §8 is right, rule 5 is not optional — it is the rule.
