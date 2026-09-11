# Review: commit df1e20e against items 1–3 of sage-learns-from-superpowers.md

Reviewed 2026-08-25. The commit is `df1e20e` ("implement first 3 items of ideas from superpowers", 2026-08-25, +58/−2 over 5 files) — written on another machine per the task description; the repo alone cannot confirm this, and this review machine's installed sage corpus already carries the shipped text, which is what lets the review test the commit against a live install. The plan is `sage-learns-from-superpowers.md`, items 1, 2 and 3 under "Do these first". The doc's own closing section confirms these are the intended three.

## Verdict

The commit is a faithful implementation of items 1 and 3, and half of item 2. It is not a transcription. The implementer re-derived each item against sage's own rules and deviated where the plan's text would have broken them. Of 30 planned change elements, 15 landed as planned, 13 landed adapted, and 2 were dropped. The commit also added 6 things the plan never asked for.

The deviations follow three consistent policies, and all three are defensible:

1. **One-home discipline.** Where the plan asked for the same clause in two files, the implementation put the rule in one place and a pointer in the other (item 1's promote-skill clause, item 3's two-file paragraph).
2. **Evidence downgrading.** Every number and tag the plan supplied got weakened or stripped: the micro-test figures, the 2-of-6 → 50-of-50 anchoring result, the file-level `(calibration: provisional)` tag, and the plan's claim that item 3 is "the strongest-evidenced item". Each downgrade carries its reasoning in the shipped text.
3. **Two reasoned inversions.** In two places the implementation ships the *opposite* of what the plan asked, with the argument attached (details below). Neither inversion is silent.

The problems are real but smaller than the successes. Two planned elements were dropped without any record. The new text introduced two dangling machine-local pointers, one internally inconsistent verdict rule, and one reachability gap — the same failure class the plan itself spent a section warning about. The findings list below has nine entries from the soundness review plus two from the compliance review; the five rated major matter.

## What each item asked, and what landed

### Item 1 — blind behavioural lens with a control arm

Substantially implemented. All four steps of "What to change" landed:

| Planned | Outcome |
| --- | --- |
| New pattern `## 12` in `references/topologies.md` | Landed, titled "Blind behavioural lens (two arms)", with the memory quote verbatim |
| Control-arm clause inside the pattern | Landed **adapted** — see inversion 1 below |
| Pointer from `SKILL.md` Step 5 to #12 | Landed, appended to the exact bullet the plan named |
| Clause in `sage-promote/SKILL.md` step 4 (the degradation gate) | Landed **adapted** — the gate got the null-effect argument plus a pointer to #12, not a duplicated clause |

Two adaptations beyond the plan:

- **The trigger was widened.** The plan scoped the lens to `/sage-promote` passes, arguing a sage run never writes the corpus. The implementation made the trigger "what the change does, never which skill is making it", and covers a run editing the corpus on the user's word. The shipped text justifies this concretely: a promotion-only trigger would not have fired on the very edits that created the pattern. This widening forced the commit's only meaning-changing edit to pre-existing text: the promote skill's writes-table cell for `<repo>/sage-claude/SKILL.md`, whose "never" column became "never **on its own trigger**" with the by-hand carve-out spelled out. (The commit's other rewritten line is the Step-5 bullet the plan asked to extend.)
- **The verdict machinery was strengthened.** The plan's single quoted clause became a stop rule, a repeat-count requirement (five or more per arm) taken from the source apparatus, an affordability statement, a `git show HEAD:<path>` mechanic for materialising the control text, and a third verdict state ("unresolved question").

**Inversion 1.** The plan's clause said: "Adopt the change only if the arms differ." The implementation refuses this and ships the opposite: "Never revert an edit on agreement at a single sample" — two arms that agree at one sample each may agree by noise, so adopt-only-if-differ converts noise into reverts of good edits. The refusal is correct, and it is less radical than it first reads: the plan's own Risk paragraph already hedged that "two arms at N=1 each is still not a measurement" and should be treated "as a weak signal, not a result". The implementer promoted that hedge from the plan's risk note into the pattern's operative rule, and deleted the clause that contradicted it.

The inversion is incomplete, though. The implementation kept the plan's *stop* rule ("a control arm that does not exhibit the failure means there is nothing to fix: stop") at a single sample, and justified it with "watching the failure happen is positive evidence". That rationale describes the observation that did **not** occur in the stop case. A silent control at n=1 is absence of evidence — exactly the noise the neighbouring sentence warns about. See finding F3.

### Item 2 — "Match the Form to the Failure"

Half implemented. The artifact landed; its application and its follow-up hook did not.

| Planned | Outcome |
| --- | --- |
| Create `references/authoring.md` with the four-row classifier, the two corollaries, the anchoring checklist | Landed, 37 lines, all three parts present; both corollaries quoted intact; the narrower five-clause classifier for negatives (which the plan kept in a provenance note) was promoted into the file body |
| One line in `SKILL.md ## References` | Landed |
| Tag the whole file `(calibration: provisional)` | **Inverted** — see inversion 2 below |
| Per-row provenance | Landed, and stronger than asked: each row states its own evidence class, and row 1 was re-graded from "no measurement" to "a worked bulletproofing record", a different reading than the plan's own map |
| Enter the finding through a Watch-list row | **Dropped** — no row in the commit, none on this review machine's installed memory; the implementing machine cannot be checked from here (finding SM-2) |
| Run a reclassification pass over `SKILL.md` Step 3 and `dispatch.md`'s Task brief, converting composition prohibitions into recipes | **Dropped, silently** — `dispatch.md` has no commit at or after `df1e20e`, and Step 3's negatives are untouched (finding SM-1) |

**Inversion 2.** The plan said to tag the whole file `provisional`. The shipped file carries no band at all and says the omission is the point: a band in this corpus counts *this* system's confirmations; the four rows do not share one evidence class, so one tag over the file would be false in both directions. This is the right call, and it is more consistent with the corpus's own band rules than the plan's instruction was — the plan itself conceded the tension ("an externally sourced band has no count and no falsifier behind it"). But one of the three citations the file recruits to defend the omission is wrong: it claims the compression floor "asks for a strength band per rule rather than per file", and the floor is a non-removal list that asks for nothing of the kind (finding F4).

The dropped reclassification pass is the one place the commit refuses plan work without recording the refusal anywhere. The shipped `authoring.md` does argue against the plan's single named conversion candidate — "hand off via artifacts, never via transcript" is a discrete directive, and converting a discrete directive is a loss, not a repair. That argument is sound and it removes the plan's only concrete example. It does not cancel the pass itself, which covered every composition prohibition in Step 3 and the Task brief. Either the pass should run as a follow-up, or its cancellation should be recorded with this reasoning.

### Item 3 — turn count in model placement

Fully implemented, with one structural improvement and one evidential improvement.

| Planned | Outcome |
| --- | --- |
| One paragraph under the tier table in `SKILL.md` Step 3 | Landed **adapted**: a two-sentence signpost, with the full rule placed in `harness.md` |
| The same rule in `harness.md ## Models and effort` | Landed adapted, at full strength — the operative clause ("where a unit's brief names exact paths, exact commands and the decisions already made…") verbatim, the surrounding text rewritten with the two additions below |

The plan asked for the same paragraph in both files and the implementation refused the duplication: `SKILL.md` got "Tier is one axis; the unit's step count is the other" plus a pointer, and `harness.md` got the whole rule. This honours the plan's own ownership argument (the plan noted `SKILL.md` already says `harness.md` "owns the placement and its reasons") better than the plan's instruction did.

Two substantive additions:

- **A carve-out for the scout seat.** The floor ("multi-step work floors at standard") explicitly does not reach an `explorer` briefed with a checklist and exact paths — that is single-pass lookup. The plan had no such carve-out; without it, the rule would have contradicted sage's cheapest working unit class.
- **The evidence was re-read downward.** The plan called item 3 "the strongest-evidenced item in the document", citing "678 of 1197 subagent turns were haiku". The shipped `harness.md` paragraph points out this is a composition statistic — what share of turns ran on the cheap tier — with no task denominator and no matched arm, so it is equally consistent with the cheap tier simply being dispatched more often. The rule therefore enters as `provisional` with an instruction to let the first covered cheap-tier run settle it. This re-reading is correct, and it is the best single piece of judgment in the commit.

One small loss: the plan's tag was `provisional — external`, and the shipped tag drops "— external" (the surrounding sentence still says the evidence is external). The `SKILL.md` copy carries no tag at all (finding F6, a judgment call — the sentence defers strength to `harness.md` explicitly).

## Findings

From two independent review lenses (compliance and soundness) plus parent verification. Severity is this review's own triage; where it differs from a lens's rating, the difference is stated.

| ID | Severity | Finding |
| --- | --- | --- |
| SM-1 | major | Item 2's reclassification pass over Step 3 and the Task brief never ran, and no record cancels it |
| F8 | major | `authoring.md` is procedurally reachable only via `SKILL.md`'s References line. The primary authoring path, `/sage-promote`, never names it, and the claim "`topologies.md` #12 owns that trigger set" is false as written — #12 contains no authoring trigger and never mentions the file |
| F1 | major | #12's pricing clause cites "the blind-behavioural band", a memory row that exists on no machine checked — including this one, whose installed corpus runs the shipped text. The dangle is a proven live defect, not a hypothetical. The soundness lens rated this blocker; lowered to major here only because the pattern's core flow still runs without the pricing clause |
| F2 | major | The rewritten promote-skill writes-table cell cites `(build-authored, SKILL.md)` cells in `local.md`. No such cell exists on this machine, whose install runs the shipped text; whether the author's machine has one changes nothing, because `local.md` never travels |
| F3 | major | #12's stop rule ("control silent at one sample → stop") is justified by a rationale that supports the opposite direction, and its prescribed action ("do not author") is unavailable at both entry points the pattern names, which are post-authoring |
| SM-2 | minor | Item 2's Watch-list entry (the hook for ever raising the classifier's band) is absent from the commit and from this machine; unverifiable on the implementing machine |
| F4 | minor | `authoring.md` cites the compression floor for a requirement it does not state |
| F5 | minor | The null-effect argument is stated at full strength in both `sage-promote/SKILL.md` step 4 and #12 — a cross-skill second home, outside the one-home grep's scope |
| F6 | minor | `SKILL.md`'s step-count clause carries no calibration tag where its neighbours do; debatable, since it explicitly defers strength to `harness.md` |
| F7 | minor | #12 prescribes two arms but licenses no single-sample outcome in which the second arm changes a decision, and does not say whether a budget-constrained run stops after the control |
| F9 | minor | #12's `git show HEAD:<path>` mechanic recovers the pre-edit baseline only while the edit is uncommitted; the condition is unstated, and `df1e20e` itself is the counterexample on the run-edits-corpus path |

**The pattern behind F1, F2 and F8.** All three are the failure class the plan's screening section named as its own blind spot: an address that does not resolve. The implementer imported the plan's *evidence pointers* (machine-local memory rows, band names) into portable skill text, which breaks the corpus's own rule that skill text may point at the shape of what lives in per-machine memory, never at a specific row only the authoring machine has. And `authoring.md` repeats, one file over, the exact unreachability the plan documented for topologies patterns: the plan proved a pattern written into `topologies.md` is invisible to a promotion pass, and the commit then made the promotion pass's authoring guidance live behind a pointer chain the promotion pass never reads.

## Recommendations, ordered

1. **Fix the two dangling pointers (F1, F2).** In #12, state the pricing shape without naming a band row, or land the band row first. In the promote skill's writes-table cell, point at the shape (a `Promoted` cell tagged with its authoring path) rather than a literal cell string.
2. **Make `authoring.md` reachable from where authoring happens (F8).** One named step in `sage-promote`'s write machinery ("read `<sage>/references/authoring.md` before drafting") and the existing References line cover both declared paths. Drop or correct the "#12 owns that trigger set" delegation.
3. **Repair #12's stop rule (F3, F7).** Decide which single-sample verdict is decisive. The rationale as written supports "control *shows* the failure → the guidance addresses something real → proceed"; a silent control at one sample should be a weak signal, not a stop. State the action in terms available post-authoring (drop the edit / keep and record), and say explicitly whether a budget-constrained run stops after the control arm.
4. **Close item 2's open half (SM-1, SM-2).** Either run the reclassification pass over Step 3 and the Task brief — with `authoring.md`'s own "discrete directive vs composition instruction" test deciding each candidate — or record its cancellation and the reason. File the Watch-list row so the classifier's rows have a path to a real band.
5. **Dedupe the null-effect argument (F5)** — cut the promote-skill copy to trigger plus pointer — **and consider the two cosmetic tags (F6, and the dropped "— external")** in the same pass.

## What this review could not check

- **The superpowers sources.** The plan's citations into the superpowers repository are not in this repo and were not fetched. This review judges only whether the shipped text handles that evidence honestly (it does, and in two places more honestly than the plan), not whether the imported measurements are true.
- **The implementing machine's memory.** Item 2's Watch-list row, and the rows F1/F2 cite, may exist in that machine's installed `local.md`. From here: absent from the repo, absent from this machine — and since `local.md` is per-machine and this machine already runs the shipped corpus, F1/F2 stand as live defects here regardless of what that file holds elsewhere.
- **Behaviour.** #12 was read, not run. F3 and F7 are textual findings; a behavioural test of the pattern would be its own programme — as the pattern itself, to its credit, says.
- Line numbers cited here are against HEAD `171d565`. The sage memory files are live and rewritten between runs; the plan document says the same of its own citations.

## Method

Produced by a sage run on this machine: parent scouting of the commit history and plan text; two independent background review lenses with disjoint mandates (plan-vs-commit compliance; implemented-text soundness), each evidence-checked by grep against the repo and the installed corpus; parent triage of all 11 findings; one adversarial refute pass over this document's own claims before filing. That refute pass corrected six claims in the first draft — the element counts, an internal "four vs five" inconsistency, a "one edit" overstatement, a "verbatim" overstatement, the machine attribution, and the framing of inversion 1 — and the corrections are applied above. Both lenses ran on the same model family as this parent; the residual same-family bias is recorded in the run ledger (`.claude/plans/sage-ledger-0a757f2f-6c5a-4477-a74d-f3407bfb1e90.md`, gitignored, on this machine).
