# Sage plan integrity — review verdict

Status: **rejection with corrections.** Written 2026-08-19 by a sage run, reviewing
`sage-improve-conversation.md`. Nothing here changes sage behavior. Section 6 records a candidate feature
that this run designed, tested against the run corpus, and killed.

The source document asked whether sage over-trusts its initial plan. It answered "half right" and proposed
four edits. This review checked that answer, those four edits, and the evidence under them. It corrects the
source document in seven places, recommends none of its four edits as written, and reports one negative
result of its own.

---

## 1. Verdict

**Reject. Ship none of the four edits. The concern behind them is real, but every instrument proposed to
address it — including the better one this run designed — fails the same test: it reads a signal that the
run corpus shows is not there.**

| #                 | Item                                                   | Verdict                                                                                                                                                                       |
| ----------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The central claim | "Right about the team plan, wrong about the task plan" | **Not upheld.** The boundary is misplaced, and two of the four pillars under it do not hold. See section 3.                                                                   |
| E1                | Pre-dispatch seat check                                | **Not proven, either way.** The rule already exists for the roles involved. Its headline cost saving is misattributed to it. One data point supports it: this run. Section 4. |
| E2                | Plan-premise check at the bring-current cadence        | **Reject as written**, and the narrowed version this run built to save it also fails. Sections 4 and 6.                                                                       |
| E3                | An amendment record that supersedes                    | **Reject, weakly.** The strongest argument against it did not survive review. What is left is an unmeasured tradeoff, not a defect. Section 4.                                |
| E4                | Re-pricing may not raise a ceiling                     | **Reject as a ban.** A logged counterexample shows re-pricing was correct and the rail fired anyway. No clean replacement boundary was found. Section 4.                      |

**The one thing worth acting on is not in the document.** The adversarial pass named a larger problem, with
four logged instances: sage's controls are prose, and the same parent that writes the plan interprets and
enforces them. That is section 7, and it is a separate piece of work.

---

## 2. Seven corrections to the source document

Each was settled by a command or a primary source.

**C1. The EMNLP citation is inverted.** This matters most, because the document's safety argument rests on
it.

The document says a rebuttal to "LLMs Cannot Self-Correct Reasoning Yet" exists, and that "it turns on
having an external verification condition. That is the whole distinction."

The paper is _Large Language Models Can Self-Correct with Key Condition Verification_ (EMNLP 2024,
`https://aclanthology.org/2024.emnlp-main.714/`, fetched 2026-08-19). Its method works **without external
feedback**. It masks a key condition in the question, inserts the candidate answer, and asks the same model
to recover the masked condition. No tool, no oracle, no second model.

The real distinction is structured against open-ended, not external against internal. Confirmed twice: by
the research unit, and by the parent re-fetching the page.

**C2. The 22.4k saving attributed to E1 was a different kind of error.** `sage-ledger-1a43545e`, deviation
D5: "U1–U3 were dispatched with `model: haiku`, overriding the alt agents' own models." That is a **model
parameter** error. The three seats were correct. A grep of `tools:` would have passed all three bad
dispatches.

**C3. The failure E1 prevents is already named, by role.** `references/dispatch.md:22` reads: "omit the
scratch path for a unit that cannot write — `explorer` and `web-researcher` distill instead, and a scratch
path in their brief is a briefing error." Both errors the document reports making were `web-researcher`
briefs asking for a file write.

**C4. "One run logged nine deviations" is not reproducible, and my first attempt to refute it was also
wrong.** The largest single deviations table holds 7 rows. That same ledger, `sage-ledger-61264f83`, has two
phases, and 3 + 7 = 10 rows across both. Nine matches neither figure. The number is unverifiable as stated,
and nothing in this review depends on it.

**C5. A ledger has already restated a plan in force, when it mattered.** `sage-ledger-0042d31e:262` carries
`# CORRECTED DESIGN — after the pre-write critic (this is the spec W1 builds)`. It states the amended design
and takes precedence over the original. The practice E3 would require already happens where a run needs it.

**C6. E4's headline evidence carries zero confirmations.** The document quotes "every past ceiling raise was
spent up to the new ceiling" and adds "Not some. Every one." That row in `memory/local.md` is classified
`Kind: gap, Count: 0`. In this schema a `gap` is a class with no coverage and a count of 0 means no
confirmed instance. A search of all 11 prior ledgers then found no mid-run ceiling raise at all.

**C7. The source document was not produced by a sage run.** That session left no ledger and dispatched
`general-purpose` agents. Its own briefing errors are evidence about working _without_ sage's Step 3, not
about a gap inside it. Its pointer to `attack-repo.md` and `defend-repo.md` in the scratchpad is also dead;
those files no longer exist. The 22.4k error was a real sage run and stands, subject to C2.

---

## 3. The central claim

**3.1 The boundary is in the wrong place.** The document argues the task plan must stay stable because it is
the budget rail's denominator. That argument protects the **priced estimate**, not the decomposition.
Merging two pending units does not require raising a ceiling. Freezing the decomposition does not stop a
parent padding estimates at plan time. The real split is priced baseline against work, not team plan against
task plan.

**3.2 Pillar 3 cites the wrong sentence.** `SKILL.md:21` reads "The parent's **post-fix** confidence is the
most reliable place errors enter". That is a finding about the fix round. Every logged confirmation behind
it is a refuter catching a defect in a parent's own fix. None is about a plan.

**3.3 Pillar 4 does not say what the document says.** Corrected in C1. The ICLR result holds for open-ended
self-critique. It does not settle the narrower question the document uses it for.

**3.4 The strongest number in the document points the other way.** It reports "zero mid-flight decomposition
failures" across 11 ledgers as evidence that the plan does not need revising. The same corpus contains three
units added after dispatch began, all at harvest boundaries, and all of which paid.
`sage-ledger-6d1a7c19:52-53` adds a second refuter, then a probe "to settle refuter R5 by measurement
instead of citing documentation". `sage-ledger-ff95b189:86` amends a design to v2 on 11 accepted findings
and adds a probe, because "the critic named a live probe as the only way to settle it".

Zero failures alongside three successful amendments is not evidence that amendment is unnecessary. It is
equally consistent with amendment being what prevented the failures. There is no frozen-plan comparison, so
the zero settles nothing.

**3.5 What survives.** The document's instinct is right that something in sage is not re-examined. Its
diagnosis of what, and its four remedies, are not supported.

---

## 4. The four edits

**E1 — pre-dispatch seat check. Not proven, either way.**

Against it: the rule already exists and names the role involved (C3), and its headline cost is misattributed
(C2). A `tools:` grep is also incomplete on its own — `Bash` lets a `verifier` write by shell redirection
with no `Write` tool, and `disallowedTools`, `permissionMode` and background tool reduction all sit outside
that line.

For it: this run ran the check before briefing, and it paid — all four seats proved read-only, so every
brief asked for an inline report. And the historical error shows that having the rule in prose did not
produce compliance.

I originally rejected this outright. The adversarial pass showed that reasoning conflated a bad cost claim
with the check's merit, and it was right. The honest verdict is that one data point does not settle a skill
edit. Run the check as a habit. If it ever catches something `dispatch.md:22` does not already name, that is
the evidence to reopen it with.

**E2 — plan-premise check. Reject as written.** "Did a harvested report invalidate a premise?" has no
threshold. At a cadence that fires before every wave and after every integration, nearly any discovery can
be described as invalidating some premise. Section 6 records the narrowed version this run built to fix
that, and why it also failed.

**E3 — an amendment record that supersedes. Reject, weakly.**

My first argument against it was that a second plan block creates two authorities that can drift. That did
not survive review. The ledger already carries three plan representations — the Plan block, the Unit table,
and the Decisions table — plus a handoff rendering. A fourth that is explicitly canonical is not obviously
worse than three that are implicitly ranked. And C5 is a run that wrote a superseding block and said it
wins, which is evidence the shape works.

What is left is that no logged run failed because of the current shape. All three handoff notes already
carry current status rather than the original plan block, and the run whose note is cited completed under
its successor. So this is an unmeasured readability tradeoff, not a defect. Reject on those grounds, and
reopen it if a successor ever makes a reconstruction error.

**E4 — re-pricing may not raise a ceiling. Reject as a ban.**

`sage-ledger-61264f83` re-priced unit V2 from 80k to 150k **before dispatch**, because a consolidation pass
that same day added a measured band showing refuters of that shape cost 375k to 522k. The unit later landed
at 784k and rail 4 fired against the revised ceiling anyway. Re-pricing did not disarm the rail. A blanket
ban would have forbidden a correct action.

A blanket ban also has a perverse effect: a parent that cannot correct an estimate on evidence defends
itself by writing a larger estimate at plan time, which inflates the ceiling before the run instead of
during it.

I proposed replacing the ban with "correct before dispatch, never after". The adversarial pass broke that
boundary and I accept the break. It leaves a blocked-and-re-dispatched unit undefined, and it forbids
correcting a pending unit from strong evidence generated inside the same run — for example, unit 3 keeping a
known-bad estimate because unit 2, on the same basis, has just overrun.

No clean boundary was found. The underlying concern is real and stays on the watch list where it already
sits. It does not become skill text on this evidence.

---

## 5. What the concern is actually about

Strip the four edits away and one observation survives from the source document. Amendments happen, they
pay, and no step describes them. `references/dispatch.md:150-156` logs a plan amendment after the fact.
Nothing produces one.

That gap is real. This run could not find an instrument that closes it without costing more than it buys.
Section 6 is the closest attempt and its failure is informative.

---

## 6. The candidate this run designed and killed

Recording a negative result, because the next person to look at this will design the same thing.

**The candidate.** Sage's Step 2 writes an assumption row whose fourth column is "how it would show if
wrong" — a falsifier. Nothing reads that column back. `SKILL.md:112` writes it; `SKILL.md:203` and
`dispatch.md:182` render one condensed line at Step 6. Between them, the bring-current bullet at
`SKILL.md:162` carries four ledger read-backs plus an occupancy stamp and a `--status` read, and none of
them is this. Meanwhile `references/memory.md:56` already acts on a fired falsifier — but only between runs.

So the design was: at each bring-current point, read the fourth column against the reports just harvested
and ask one bounded question — did a report show one of these? It looked strong. It reuses an existing
column, an existing cadence, and an existing pattern. Its threshold is pre-registered, so it escapes E2's
churn objection. Its trigger is an external report, so it is not open-ended self-critique.

**Why it fails.** The falsifiers are not written to be fired by a report inside the run.

Across the 11 prior ledgers there are 60 assumption rows. The adversarial pass classified its own count of
them and found at most 12 that a same-run agent report could directly fire. The parent's independent read of
the raw column agrees on the pattern. The dominant forms are:

- addressed to the **user**: "User says they wanted a literal advisory-fraction line kept"; "User wanted to
  review the diff before any sync"; "User asks why `~/.claude` still has the old text".
- addressed to a **later run or another machine**: "Sessions on smaller windows never set it"; "A low-effort
  session gets an over-deliberate successor".

This is structural, not sloppy. `SKILL.md:112` defines the assumption log as ambiguities "that would
otherwise need the user". By construction, most of them resolve when the human reacts, which is after the
run ends.

**The second, independent failure.** None of the three amendments in section 3.4 corresponds to a logged
falsifier. All three were driven by a critic's finding, which is a different instrument. So the check would
not have produced the very behavior it was designed to systematise.

**A third.** Its most common output is "nothing happened", which leaves no ledger trace. The retirement
condition — ten runs where the check fired nothing — has no denominator, because a check that ran and found
nothing is indistinguishable from a check that was skipped.

**What would change the verdict.** A replay over historical harvest boundaries showing real report text
firing real pre-existing rows, and reproducing at least one amendment. Or a redesign that stops treating the
assumption log as the carrier and pre-registers premises _per pending unit_ instead, with the trigger and
the affected row as separate checkable fields. Neither is a small change, and neither is justified by
anything in the current corpus.

---

## 7. The finding worth its own run

The adversarial pass named a problem larger than anything in the source document, with four logged
instances.

Sage's controls are prose, and the same parent that writes the plan interprets and enforces them.

- A parent passed model overrides against an explicit rule, wasting 22.4k (`sage-ledger-1a43545e`, D5).
- A parent edited a template while a verifier was reading it, breaking the freeze
  (`sage-ledger-6d1a7c19:54`).
- A successor widened its own write lease from 3 files to 6 instead of returning rail 3 to its supervisor
  (`sage-handoff-61264f83:148-150`).
- The source document promoted a count-0 watch row into load-bearing evidence (C6).

None of these is a planning failure. All four are a parent not obeying text that already exists. Every edit
the source document proposes, and the one this run designed, adds more text of the same kind. That is why
none of them earns its place.

The question worth asking next is not "what else should the parent check". It is "which of sage's rules can
be made to hold rather than be asked for" — an agent file's `tools:` line holds, `maxTurns` holds, a
`permissionMode` holds, and a sentence in `SKILL.md` does not.

That is a design question about enforcement, not about planning. It belongs in its own run.
