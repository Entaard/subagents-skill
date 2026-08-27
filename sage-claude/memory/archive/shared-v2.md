# Sage shared memory — portable rules

Your job here: read every rule at Step 2 before estimating and at Step 3 before briefing, and apply the ones whose **Recogniser** matches what is in front of you. These rules hold on any machine.

**What belongs here:** a claim that stays true on a different machine — a topology lesson, a ratio, a discount factor, a failure recogniser. **What does not:** an absolute cost, a band figure, a confirmation count, a date, a harness version. Those live in `local.md`, and a rule that needs one of them to be usable is not portable yet.

**This is the only physical copy.** Every install symlinks to it, so a write here lands in `<repo>/sage-claude/memory/shared.md` and shows up in `git status`. One rule per block, so two machines editing this file conflict inside one block rather than across the file.

Written by `/sage-promote` only, never by a run. Every block carries exactly five fields in this order: the **rule** in bold under its heading, then `Qualifier`, `Recogniser`, `Band`, `Falsifier`. `Band` is `established` (six or more confirmations), `recurring` (three to five), or `provisional` (below bar, carried only because its mechanism is structural); the counts and dates behind it live in `local.md`, so a new confirmation re-dates one file rather than two. Skill text citing a rule writes `(calibration: <band>)` and nothing more of this file's bookkeeping — the clause, its qualifier and its anecdote travel; counts, dates and falsifiers never do. A rule whose `Falsifier` fires is evicted to `local-archive.md` with the observation attached — `/sage-promote`, `## Eviction`.

## Price off a same-shape row

**Price a run off a same-shape logged row before reaching for band arithmetic, and name the row in the plan.**

- Qualifier: same unit topology and same corpus kind, or it is not the same shape and the band is the better prior.
- Recogniser: runs priced this way landed within ±6% of their core estimate, after a stretch of band-priced overruns.
- Band: established
- Falsifier: three consecutive same-shape-priced runs missing by more than band arithmetic missed on comparable work.

## Estimate from the corpus and the lenses

**Estimate from the corpus a unit must hold and the lenses it must apply — never from the deliverable's size or the role's name.** Add 60–150% where the unit reads widely before it reasons.

- Qualifier: governs a blind acceptance-suite author too, whose brief names a corpus that the deliverable's length hides.
- Recogniser: two runs missed high, by 1.6× and 1.7×, pricing a blind author from the requirement's length instead of from the corpus its brief named.
- Band: established
- Falsifier: a unit class whose cost tracks its output size across three runs while the corpus it holds varies.

## Review and verify are one price

**Price a review round and its fix-verification round as a pair, and where the review loop runs to a dry round rather than to a fixed count, price that pair as a floor rather than as the whole review figure.** The verify round has come back dry only under a mandate already cut to blocker and major, and it has repeatedly cost more than the review itself: a fresh or full-mandate continuation re-reads the whole corpus, so retained context makes the round cheaper to brief, not cheaper to run. A dry round is not a cheap round — it pays that read whether or not it finds anything.

- Qualifier: one measured exception — steering the same verifier thread for a narrow re-verdict on named fixes runs ~4–7× cheaper than a fresh dispatch, so the pair prices a full verify round, never a steered follow-up. A finished agent's handle continues with its context intact, so the steer need not be planned before that agent reports. The band belongs to the pair claim, which earned it. The floor half is carried on the loop's shape, and on adversarial gate rounds running past two wherever a batch changes observable behaviour rather than prose, never on a second cost measurement — so budget the follow-up as a margin and let the artifact decide whether it is spent.
- Recogniser: a plan carrying a review row and no verify row; a verify row priced as whatever is left over; or, under a dry-round loop, a plan pricing the pair as the whole review figure with nothing budgeted beyond it.
- Band: established
- Falsifier: three verify rounds each costing a small fraction of the review round they follow. Dryness alone does not fire it — a dry round still pays the corpus read, and under a loop that terminates on a dry round it is the designed ending rather than a fault. A loop that keeps stopping at the pair falsifies the floor half alone, which is a clause-level retirement with no written procedure yet: file it, do not evict the block.

## A checklist prices a lens only when every item settles in one look

**A claim checklist prices a review lens at its band's floor only when every item settles in one look; otherwise price the lens by its widest question.**

- Qualifier: one item quantified over the corpus costs what an open mandate costs, whatever the other items cost.
- Recogniser: a checklist whose items read as counts or coverage — "how many", "everywhere", "all of" — priced at a floor drawn from single-look items.
- Band: recurring
- Falsifier: a lens carrying a corpus-quantified item landing at its band's floor three times.

## A reader's structural claim is a lead

**A reader's structural claim is a lead, not ground truth — fetch the primary source locally and grep it yourself before you build on it.**

- Qualifier: a summarising fetch tool generates leads, it does not settle facts; the rule reaches your own completion claims, not only your briefs.
- Recogniser: one reader described a data structure that does not exist; a researcher's headline version attribution was wrong, and the fix it implied would have introduced the defect it claimed to remove.
- Band: established
- Falsifier: ten consecutive reader structural claims that a grep confirms unchanged.

## Disjoint mandates produce disjoint find-sets

**Give every lens a mandate no other lens holds.** A second reviewer on the same mandate buys redundancy; a second reviewer on a different one buys coverage.

- Qualifier: this is the coordination check paying, and the standing argument against cutting a lens for budget — it is not an argument for adding a lens whose mandate you cannot state in one sentence.
- Recogniser: across the multi-lens runs logged each lens's find-set has been substantially its own — where two lenses did construct the same finding it was one or two out of a larger set, never the set itself. Both outcomes paid: repeatedly the decisive finding was invisible to every other lens, and where two lenses converged on one finding by different routes, that finding was the run's most certain.
- Band: established
- Falsifier: two multi-lens runs whose lenses return substantially the same find-set.

## A brief that names its ground truth runs cheaper

**Name a brief's ground truth outright — exact files, line numbers, URLs, measured baselines, and the harness to measure with.** ~2–2.5× cheaper than an open-ended brief, and it fails less often.

- Qualifier: brief style, not task class, sets this cost, and it holds across fetching, code and prose. One dispatch class is exempt: a blind acceptance-suite author receives the decisions' observable consequences, never the decisions.
- Recogniser: a brief whose Inputs read as a topic rather than as a path list.
- Band: established
- Falsifier: three ground-truth-named briefs costing what comparable open-ended briefs cost.

## Settle a disagreement with a command

**Settle a disagreement with a command, not by model tier and not by majority — buy the measurement.**

- Qualifier: agreement that nothing is wrong proves nothing; units independently constructing the same specific finding by different routes are the one kind of agreement that is evidence.
- Recogniser: the standard-tier checker has been right against the frontier one; and where reviewers agreed a mechanism claim was inconsistent but none of them could see the runtime, the repair direction they agreed on was backwards, and one small docs unit changed the fix.
- Band: established
- Falsifier: three disagreements no command could decide, where tier or majority then proved right.

## A scoped agent boots ~3× cheaper

**A saved agent with a `tools:` allow-list boots ~3× cheaper than a general-purpose dispatch, so several small lookups in one area are one scoped agent carrying a checklist, not N agents.**

- Qualifier: the ratio travels; the absolute floor does not, because it includes whatever files that machine always loads — read the figure from `local.md`'s Bands.
- Recogniser: a plan holding several one-question units pointed at the same area.
- Band: provisional
- Falsifier: a measured boot pair on any machine where the scoped agent costs within 1.5× of the general-purpose one.

## When the target is a range, never report a mean

**When the target is a range, chase the internal range and report minimums — never optimise or report a mean.**

- Qualifier: when the finding is aesthetic or perceptual, do not re-check it with the metric that misled you; ask what range the target has.
- Recogniser: one run made the mean-for-range error four times, walking a value straight through its minimum separation while every mean looked right.
- Band: recurring
- Falsifier: three range-targeted deliverables where the mean and the minimum select the same design.

## Point one adversarial pass at your own fixes

**Point an adversarial pass at your own fixes, your completion claim, and your recommendations — not only at the artifact you were handed.** At medium risk and above, plan that row from the start rather than adding it after.

- Qualifier: a refuter's "no defect found" on domain correctness is weak evidence, not a clearance — the pattern has broken the other way, with the parent catching a researcher's wrong headline finding. Vary the model across maker and checker, not just the instance.
- Recogniser: the mechanism has a name — a fix closing one finding silently un-passes a criterion already verified, because the diff readers ruled on a pre-fix freeze and the refuter is the only unit standing after it.
- Band: established
- Falsifier: a refuter aimed at the parent's own fixes returning nothing across five consecutive dispatches.
