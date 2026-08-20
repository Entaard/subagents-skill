# Sage: what the self-learning loop never learns

Written 2026-08-20. Every number comes from a command run on this machine.

This document was refuted twice before you read it. Two adversarial agents attacked it: one re-derived every number, one attacked every proposal. **They broke my headline and killed four of my proposals.** Section 9 lists what they killed and why. The version below is the corrected one.

---

## 1. The short answer

You are right, and the exact shape of the problem is narrower and sharper than either of us guessed.

Sage's memory has a table called `## Rules`. Promotion reads it. The installer seeded it with 11 rows. Twelve runs later it still holds **exactly those 11 rows**.

That table does change. Counts rise, provenance gains `+ local run`, `Promoted` cells stamp `skill 2026-08-18`. Two new `Bands` rows were earned. The writers are consolidation and `/sage-promote`; an ordinary append is forbidden from touching it, which is correct. So the promotion machinery is not dead, and my first draft was wrong to say it was.

But:

> **No new rule has ever entered the rule set.** Sage gets better at counting the eleven things it already believed. It has never learned a twelfth.

Every new thing this machine observed in twelve runs, fourteen observations, sits in the `## Watch list`. The one route that could carry a watch row into the rule set is `/sage-promote` stage one, whose own text says: "Candidates: every `local.md` Rules row **and Watch-list row** whose `→ shared.md` trigger fired."

That trigger tests `Class` and `Promoted`. **The Watch list has neither column.** So no watch row can ever evaluate the trigger, and no watch row has ever graduated.

That is the whole defect. It is one missing column.

There is a second answer you did not ask for. I expected sage's record-keeping to have gone dead too. I sent an agent to prove it. **That agent refuted me.** The ledgers are largely honest and largely complete. So the diagnosis is not "sage is too complex":

> **Sage records well. Sage counts well. Sage cannot add a rule.**

---

## 2. The one number

| Table in `memory/local.md` | Seeded | Live | Change |
| --- | --- | --- | --- |
| `## Bands` | 6 | 8 | +2, both run-earned |
| **`## Rules`** | **11** | **11** | **+0 rows.** Counts, provenance and `Promoted` cells all moved. |
| `## Watch list` | 5 | 19 | +14 |
| `## Run log` | 6 | 18 | +12 |

Twelve runs. Fourteen new observations. Zero new rules.

The second number: `memory/shared.md` holds 11 portable rules. Ten are about dispatch cost, estimation, briefing or verification. One, "never report a mean", is about how you report a deliverable. **None is about handover, memory, promotion, the scripts, or the sub-skills.**

That is your blind spot, confirmed. It is not a bias in what gets promoted. Nothing gets promoted, because the gate has a broken lock.

---

## 3. Where you are right

| Your item | Verdict |
| --- | --- |
| 1. Handoff never promoted | **Confirmed.** The protocol ran end to end once, on 2026-08-20. `## Handover` has not been edited since 2026-08-18, the day it was written. The two lessons that run produced sit in the Watch list at count 1, where the broken trigger cannot reach them. |
| 2. The lessons-to-memory flow never promoted | **Confirmed, and it is the root cause.** See section 2. Also: `Kind` values `lesson`, `defect` and `gap` are named only in the data file. `references/memory.md` never names them, so nothing can key on them. |
| 3. `/sage-promote` never promoted | **Confirmed.** It has no stage that reads a defect row. Its "what it writes" list and its "never touched" list both omit `bin/*.sh`, so a defect in a shipped script has no owner. |
| 4. Sub-skills never promoted | **Half right.** No rule about them ever entered memory, which is your point. But three of the four are genuinely used and measured. See 4.1. |
| 5. Scripts in one environment and not another | **Confirmed for one script and one dependency. I reproduced it.** See D1. |
| "There may be more" | Yes. See sections 5 and 9. |

---

## 4. Where I fight you

### 4.1 "Maybe clean-code is not needed"

Wrong target. `clean-code` is the only satellite skill that is **mechanically binding**: `claude-agents/implementer.md` carries `skills: [clean-code]`, and that same agent has no `Skill` tool, so it can reach nothing else. Delete `clean-code` and every writer dispatch silently loses its standards with no error.

Fair caveat, from the refuter: the injection mechanism is asserted by the agent file's own prose, not measured here. The `tools:` absence of `Skill` is measured, and that half is what makes the binding structural.

Keep it. The deletion candidates are in section 6.

### 4.2 "Sage is too complex and defeats its targets"

Half true, and the half matters.

I tried to prove sage's ledger protocol had become dead prose. **The evidence refuted me** across six real ledgers:

- 25 assumption-log rows. **Zero** empty falsifier cells.
- 6 of 6 coordination checks answered. **One is negative**, and correctly so. That is sage's only self-falsifying line, and it fired honestly.
- `Awaiting human` present in 5 of 6.
- 37 of 42 unit rows carry an actual cost.
- Three of the five failures the round-3 audit named were closed.

That is a live protocol, not a dead one.

So the complexity charge does not hold against sage's dispatch and record core. It holds against two things:

1. **The learning layer.** Five triggers, two tables, strength bands, falsifiers, a compression floor, and a six-stage promotion skill with a degradation gate. Output after twelve runs: zero new rules, because of one missing column.
2. **The always-loaded text.** About **51,600 tokens** of sage prose is read per run, plus **10,400 tokens** of script headers if you follow "its header is its manual" literally. `SKILL.md` alone is 322 lines and 9,918 words.

Two honesty notes the refuters forced, and they matter:

- Those token figures are bytes divided by four. A word-based cross-check gives 44.1k instead of 51.6k for the same seven files. Read them as **45k to 52k, plus or minus 15%**, not as exact numbers.
- My first draft said my own context hit 139k "before the first agent was dispatched" and called that protocol overhead. That was wrong. Occupancy is the *whole* context: harness prompt, tool schemas, `CLAUDE.md`, memory, your task text. Sage's own corpus is at most about 37% of it. The honest version: **sage's corpus is the single largest thing a parent loads that a parent controls.**

Verdict: do not simplify the dispatch core. It pays, and the coordination checks prove it. Do fix the learning layer, which is one column.

### 4.3 "The scripts are fragile across environments"

Mostly wrong, and I checked by running them in a sandbox with binaries removed.

- **Zero** BSD-versus-GNU flag problems. No `date -d`, `stat -c`, `sed -i`, `readlink -f`, `find -printf`, `grep -P`. POSIX awk only.
- **Zero** bash-4 features. They run under this machine's bash 3.2.
- `sage-lint.sh` does **not** need `jq`, `bc` or `column`. I claimed it did. I was wrong. Output is byte-identical with all three removed.
- `install.sh` **does** check for `jq`. Twice.

Your `jq` warning is still real, but it is one guard clause in one script and the fix is one line. See D1. I also found two holes you did not name: D3 and D4.

### 4.4 "Sage costs more than subagents"

My first draft answered this from the last 12 rows of the subagents log and got the conclusion backwards. Corrected:

- `subagents`, **32** logged runs: actuals **21k to 7.12M**.
- `sage`, 12 logged runs: actuals **35k to 1.57M**.

**Subagents' ceiling is 4.5 times sage's.** Sage is not the expensive one. On comparable work the medians are close and both skills miss their estimates by about the same factor.

Sage does carry a fixed protocol overhead per run: reading its corpus, writing and linting a ledger, hosting a watchdog. That is real, and section 4.2 bounds it. It is not what makes a run big. What makes a run big is fleet size, and sage's own log says its worst overrun came from pricing two units by the size of their output instead of by the corpus their briefs named.

### 4.5 Two questions from your `ideas.md` nobody answered

- **"Does sage have the explore-plan-implement-verify loop?"** Yes. Step 1 scouts, Step 2 plans, Steps 3 and 4 dispatch, Step 5 verifies. The gap is not the loop. It is that Step 6 records what the loop learned into a table nothing reads.
- **"Continue working with sage in the same session?"** No, and it breaks. See F6: the ledger path is keyed by session, not by run, so a second `/sage` in one session collides with the first. It has already happened once and the run invented an undocumented filename to escape.

---

## 5. Every improvement I can defend

`high` means I ran a command. `medium` means two units agreed. `low` means judgment.

### A. The learning loop

**A6. Add a `Class` column to the Watch list. This is the blocker. (blocker, high)**
`/sage-promote` stage one already accepts watch rows as candidates. The `→ shared.md` trigger tests `Class` and `Promoted`; the Watch list has neither. One column closes it. Cost: one line in the structural invariant, one in `local-seed.md`, one in the append rule, one in the existing 19 rows.
*This is the single highest-value change in this document.* My first draft ranked it fourth. The refuter was right.

**A7. Define the closure act. (blocker, high)**
Nothing anywhere moves a Watch row out of `watching`. Eighteen of nineteen rows are still `watching`. The one that left was set to `settled` by hand, with no rule authorising it. Every counter in this system accumulates and nothing decrements. Until closure is defined, every new trigger you add becomes permanent noise.

**A8. Fix the retirement under-count. (major, high)**
The `→ retirement` trigger needs "two confirmations contradict it". There is a live `contradiction` row against the rule "Review and verify are one price", and **its own text says the corpus records the measured opposite twice**. It sits at count 1. So a rule that should be retiring is not, because the row that contradicts it was under-counted by the run that filed it. Eleven shared rules, zero evictions, zero falsifier firings, and the one live candidate is mis-scored.

**A5. Make the consolidation trigger clearable. (major, high)**
The trigger is "40 rows". Consolidation compresses a row to a pointer, and a pointer is still a row. The count never falls. It is at 56 against a threshold of 40, so it fires every run and always will. Two separate runs already filed this. Nothing acted.
*Change: one word.* "40 rows" becomes "40 non-pointer data rows".

**A4. Name the `Kind` taxonomy in the protocol. (major, high)**
`lesson`, `contradiction`, `defect`, `gap` appear only in `local.md`'s own prose. A value no protocol names is a value no trigger can key on.

**A3-revised. Ship a defect-repair stage, not a defect trigger. (major, medium)**
My first draft proposed firing a hint on any `defect` row at count 1. **The refuter killed it and was right**: on today's file that fires on 8 of 19 rows, three of which are deliberate accumulators whose own text says "until ten runs of evidence sit in the Run log". It would manufacture an always-firing hint, which is exactly the defect A5 deletes.
The real gap is not the hint. You have run `/sage-promote` three times. The missing half is a **stage** that reads `defect` rows, repairs the corpus, and closes the row. Give it an owner and fold A9 into it.

**A9. Give `bin/*.sh` an owner. (minor, high)**
They are in neither `/sage-promote`'s "what it writes" list nor its "never touched" list.

**A10. Record the append measurement. (minor, high)**
`references/memory.md` orders a before-and-after `awk` check on every section touched. Nothing orders it recorded, and no trace of it exists. The only check guarding every memory write leaves no audit trail.

### B. Handover

**B1. `## Handover` has never been revised by the run that exercised it. (medium)** Written 2026-08-18, run 2026-08-20, unchanged. Its two lessons sit in the Watch list. This is A6 seen from the handover side.

**B2. Retire the unsourced note-cost band. (minor, high)** `references/harness.md` says a handoff note costs 15k to 30k. The one measurement is about 8k, 47% below the floor. No contradiction row exists, so nothing will ever retire it, and the handover slack arithmetic prices against it.

**B3. Update the stale "supervision cost is unmeasured" sentence. (minor, high)** `SKILL.md` still says it. The 2026-08-20 run measured it at about 15k. The instruction to record worked; the sentence describing the state of knowledge did not update. That is this whole document in one line.

**B4. The depth-1 chaining "invariant" is not enforced. (major, medium)** `orchestrator.md` grants the `Agent` tool, and the depth cap permits two levels. A successor reading `## Handover` finds step 3 saying "spawn the successor". Only prose in its own file says not to.
*Change:* scope step 3's language to generation 1. **Do not** take my first draft's other option of dropping the word "invariant" — that downgrades a safety property to a preference.

**B5. `resume` and `report` have never run. (high)** Across every transcript on this machine: **zero `resume`, zero `report`.** Two of the three documented invocation forms have never been exercised. My first draft also gave a precise invocation count; two counting methods disagree (14 versus 17) depending on whether subagent transcripts are excluded, so treat the count as "at least fourteen" and the two zeros as exact.

**B6. One condensed branch is wrong. (minor, high)** `SKILL.md` reduces `harness.md`'s four `git check-ignore` branches to a two-way test. In a directory that is not a git repository, the parent prints a spurious recommendation to edit a `.gitignore` git cannot see.

### C. Promotion

**C1.** Promotion works for rules that already exist, and only for those. Three passes ran, landed band crossings, and one correctly refuted its own edits at the gate. The machinery is sound. It has no input, because of A6.
**C2.** A `Promoted` cell is not evidence the write landed. Filed 2026-08-19, count 1, unactioned.
**C3.** The ground-truth-brief rule states two ratios in its own corpus: `dispatch.md` says about 2x, `SKILL.md` says 2 to 2.5x. Filed 2026-08-19, unactioned.

### D. Scripts and environments

**D1. No `jq` makes the watchdog silent, and sage then disables it for ever. (major, high, measured twice)**
Reproduced independently by two agents. With `jq` genuinely absent, `sage-watch.sh --status` exits 0 with empty stdout and empty stderr. That is byte-identical to a wrong path. A working control emits 1,298 bytes. `SKILL.md` then instructs the parent, verbatim: "Nothing back → it cannot run here; disable it, write one ledger line, and never warn again."

So on a machine without `jq`, the handover rail vanishes, and the parent is told never to mention it again.

Why you saw this elsewhere and not here: `jq` is **not** bundled with Claude Code. I checked the install directory. On this Mac it is `/usr/bin/jq`, shipped by the operating system. `sage-watch.sh` carries a hard-coded `/usr/bin/jq` fallback, which is a macOS-shaped assumption. So the watchdog is invisible-by-default on exactly the machines that are not macOS.

*Change, one line:* split the `[ ! -x "$JQ" ]` test out of the guard it shares with `! -d` and `! -r`. Give it a distinct exit code and one stderr line.
*Second change, one sentence:* `install.sh`'s two `jq` notes mention the hook. Neither mentions the watchdog.

**D2. `sage-watch.sh` has no `--selftest`. (minor, high)** It offers the parent no way to check its own health. Note the refuter's correction: `sage-alt-guard.sh --selftest` prints four `FAIL` lines with `jq` gone but never names `jq`, so it surfaces breakage, not the cause. Neither script diagnoses.

**D3. `sage-lint.sh` invents violations when a tool it shells to is missing. (minor, high)** With `sed` absent it printed **two** violations on a **valid** ledger, both invented, with empty stderr. `awk` absent returns exit 3, "not a ledger", which its own header says is not a degradation code. Both contradict the header's fail-quiet promise. (`grep` absent is noisy on stderr, so that case is visible.)
*Change:* a preflight for `awk`, `sed`, `grep`, `find`.

**D4. `install.sh` needs `rsync` and never checks. (minor, high)** Four call sites, under `set -euo pipefail` on line 4. Absent in Debian-slim and Alpine. The install aborts at exit 127 before copying anything. Wider than the `jq` hole and unguarded.

**D5. No bash-version check in `install.sh`. (low)** An unstated assumption, not a live defect.

### E. The satellite skills

**E1. `agents-self-reflect` is probably orphaned. (medium, and downstream of G3)** It consolidates `subagents/calibration.md`, whose last row is 2026-08-16. Sage does that job automatically now. It was invoked four times, all in the subagents era. **Do not delete it before you decide G3** — if `subagents` stays, its consolidator stays.

**E2. `diff-review` overlaps the built-in `code-review`, less than I first claimed. (medium)** Corrected by the refuter: `diff-review` carries **sixteen** smells, not twelve. The spec ladders differ in order and first entry, and `code-review` requires an issue tracker that `diff-review` explicitly refuses to assume. So it is not a near-duplicate.
What survives: sage never invokes it as a skill. It has never been called by name on this machine. Sage copies its two reader briefs verbatim into plan rows. So the file is a text container for two paragraphs.
*Weakened change:* cut the duplicated Fowler baseline and point at `code-review` for it. Keep the skill and its four added smells.

**E3. `clean-code` and `concurrency` stay. (high)** Both used, both measured. `concurrency` is reachable only through a pointer in `clean-code`, which matters because `implementer` has no `Skill` tool and must read the file directly.

**E4.** No rule about any sub-skill has ever entered memory. Correct, and it is A6 again.

### F. The ledger

**F1. Sage's own lint fails a spec-shaped ledger and passes a non-compliant one. (major, high, measured)**
I built a fixture exactly to `references/dispatch.md`'s `### Plan` block, which is a fenced `text` block. The lint reported two violations. This run's ledger, which ignores the template's shape, passes clean.

The refuter's correction, and it sharpens the point: `dispatch.md` never actually says whether the fence is presentation or content. **The spec is silent, and the lint decided.** That is the root of F2, F3 and F4 below, because a check that punishes compliance trains the parent to stop reading it.
*Change:* one line. Say which one it is.

**F2. State cells are never live. (major, medium)** No ledger ends with a current state table. Two backfill every row. One deleted the column. The lint says in its own header that it cannot see this.
**F3. Two dispatched units never entered a unit table. (major, high)** Round 3 found this. It recurred after the lint shipped.
**F4. The `messages` cell is empty against two recorded steers. (major, high)** No lint check reads that column.
**F5. About half the assumption-log falsifiers can only fire if you speak. (minor, medium)** For example "User asks for eval harness integration". That is a preference change, not a falsifier.
**F6. Two runs in one session collide on the ledger path. (minor, high)** Already happened: session `53c948dc` has two ledgers, the second with an undocumented `-append` suffix and a non-conforming header. Define the second run's path.
**F7. Two of six ledgers write `## Assumption log` where the spec says `### Assumption log`, and the lint is silent. (minor, high)**
**F8. The disclosure-home rule is violated in the newest ledger. (minor, medium)** The disclosure sits under `### Run record`. The lint stayed quiet only because an unrelated finding contained the keyword under the right heading.

### G. Size, cost, and the fork

**G1. Move pointer prose out of `SKILL.md`, not rules. (low, weakened)** My first draft argued for splitting the file on injection cost. That is the cost-first ordering you have already ruled out, and the refuter was right to flag it. Corrected: **do not move any rule that has already failed while always-loaded** — the alt-lane no-`model` rule cost a measured 22.4k, and the watchdog `SAGE_WINDOW` rule has its own defect. A rule in a reference the parent may not open can only be obeyed less.

**G2. `/sage report`: keep it. (reversed)** My first draft proposed deleting it on zero uses. The refuter killed the argument and I accept it: the feature's stated purpose is answering from a *later* session, three days in, and the identical metric would delete `/sage resume`, which cannot go because it is the only re-entry when a successor spawn fails. Zero uses does not discriminate here.

**G3. `subagents` needs a decision, not a deletion. (low, softened)** Facts: its calibration log's last row is 2026-08-16; 164KB is installed; 26% of sage's paragraphs are near-duplicates of it, which an independent check put at 29.7% for `SKILL.md` alone.
The refuter's counter, which I accept: 26% duplication is the **predicted consequence** of a fork you chose deliberately, so citing it as a reason to undo the fork is circular. Worse, section 4.4 uses subagents' log as **the only control arm sage has**, and two of your `ideas.md` questions can only be answered with it. Deleting it destroys the instrument.
*So:* do not retire it. Either state plainly that it is the attended mode and give it a maintenance rule, or freeze it as a control and stop counting its staleness as rot.

**G4. The alt lane is infrastructure with nothing in it. (minor, high)** Prose in `SKILL.md`, a section in `harness.md`, three templates, and a `PreToolUse` hook registered **globally** that runs on every `Agent` dispatch from any skill. Measured at about 15 ms and it correctly fails open without `jq`, so it is cheap and safe. But there is no alt config and no alt agent installed, so the lane has never been usable here.
Your `ideas.md` experiment lane depends on it existing. Install it, or mark it unavailable in `SKILL.md` so a plan stops reasoning about it.

**G5. Killed. See section 9.**

---

## 6. Delete these

Shorter than my first draft, because the refuters removed three entries.

| # | Delete | Why | Confidence |
| --- | --- | --- | --- |
| 1 | `diff-review`'s duplicated Fowler baseline | Twelve of its sixteen smells restate the built-in `code-review`. Keep the skill and its four additions. | medium |
| 2 | `agents-self-reflect` | Consolidates a file dead since 2026-08-16. **Blocked on G3.** | medium, conditional |

**Do not delete:** `clean-code` (binding, measured), `concurrency` (measured), `/sage report` (see G2), `/subagents` (see G3), the `## Rules` table (see section 9), the watchdog, the adversarial-pass-at-your-own-fixes rule, and the coordination check.

---

## 7. What I deliberately do not propose

- **No plan-premise re-verification loop.** Round 3 measured it: of 22 assumption rows, only 6 could ever be fired by a same-run report.
- **No ban on mid-run re-pricing.** Never observed here.
- **No deterministic enforcement program.** Most of sage's rules have no deterministic predicate.
- **No autonomous model-roster changes**, per your own non-goal.
- **I am not arguing to delete sage.** Stated honestly, this refusal is the weakest claim in the document: it rests on coordination checks that sage grades itself, and G3 would remove the only external control. What I can say is that on this run six lenses returned zero duplicate findings and two of them broke my own work, which is the behaviour the design predicts.

---

## 8. If you only do four things

1. **A6.** Add `Class` to the Watch list. One column. Nothing else in this document promotes until it lands.
2. **A7 and A8.** Define the closure act, and fix the under-counted contradiction row. Without closure every counter you add becomes permanent noise.
3. **F1 and A5.** Two one-line fixes with outsized effects: decide whether the Plan template is fenced, and make consolidation able to clear its own trigger.
4. **D1.** Make a missing `jq` say so.

---

## 9. What the refuters killed

Recorded because a review that hides its own corrections is worth less than one that shows them.

| Killed | Why |
| --- | --- |
| **My headline**, "the promotion trigger reads a table runs never write to" | False. Runs do write to `## Rules`: counts, provenance, `Promoted` cells. The true claim is narrower: no *new* row has ever entered it. |
| **"No step is defined that moves a row into Rules"** | False. `memory.md` `## Consolidate` says "Rewrite Run-log rows into Bands **and Rules**". The route exists; it just does not read the Watch list. |
| **A1**, mint a Rules row from a watch row | Superseded by A6. A6 uses the path that already exists. A1 would have created a duplicate representation. |
| **A2**, merge the Rules table into the Watch list | Net-negative. The structural invariant names the exact table headers, and `memory.md` says a failed invariant means "abort, write nothing, do not repair the file". Changing the headers would make consolidation **and** promotion abort permanently on every installed `local.md`, with no sanctioned repair path — and `local-seed.md` is on promote's "never touched" list, so the seed could not be migrated either. |
| **A3**, fire a hint on any `defect` at count 1 | Would fire on 8 of 19 rows including three deliberate accumulators, creating an always-firing hint. That is the exact defect A5 removes. Replaced by A3-revised. |
| **G5**, a compliance reader at Step 6 | Self-defeating. It was sold as the cure for F2, F3 and F4 and catches at most one: a Step-6 reader sees only the finished artifact, and `SKILL.md` itself says a backfilled ledger and a live one read identically. I also priced it at 20k on a fast-tier agent for a mandate sage's own tier table assigns to frontier, which is the same pricing error this run's log warns about. And "so the next version of this document writes itself" was an incentive tell, not an argument. |
| **G2**, delete `/sage report` | The zero-uses metric does not discriminate: it would delete `/sage resume` too, and that cannot go. |
| **G3**, retire `/subagents` | Circular, and it destroys the only control arm sage has. |
| **21 invocations, 21.6k header tokens, "sage's ceiling grew"** | All three wrong. Corrected in B5, 4.2 and 4.4. The ceiling sentence was backwards: subagents' largest run is 4.5× sage's. |
| **"12 Fowler smells, near-duplicate"** for `diff-review` | Sixteen smells, different ladders. Weakened in E2. |
| **"protocol overhead eats half the distance to handover"** | Occupancy is the whole context, not sage's share. Corrected in 4.2. |

What they attacked hardest and could **not** break: the four table counts and the eleven frozen rule names; the twelve runs; D1; F1; F3; F4; A5; the 26% duplication, which an independent check raised to 29.7%; the `clean-code` binding; and the self-refutation in 4.2.

---

## Appendix: how each claim was checked

| Claim | Method |
| --- | --- |
| Seed vs live table counts and row bodies | `awk` block counter and a paste-diff over `sage-claude/memory/local-seed.md` and `~/.claude/skills/sage/memory/local.md` |
| Watch list lacks `Class` / `Promoted` | `references/memory.md` structural invariants, header row quoted verbatim |
| `/sage-promote` accepts watch rows | `grep -n 'Candidates:' claude-skills/sage-promote/SKILL.md` |
| Consolidation writes Rules | `grep -n 'Rewrite Run-log rows' references/memory.md` |
| 18 of 19 rows still `watching` | Field-4 extraction over the Watch-list table |
| 0 `report`, 0 `resume` | `grep -r '<command-name>/sage'` over `~/.claude/projects/`, two counting methods, both zero |
| Corpus 45k–52k tokens; headers ~10.4k | `wc -c` over the 7 always-read files; header extent found with `awk 'NR>1 && !/^#/ && NF{print NR-1; exit}'` |
| `jq` absence silences the watchdog | Stub-PATH sandbox with the `/usr/bin/jq` fallback defeated; output compared byte for byte against a wrong path and a working control |
| `jq` not bundled | `find` over the Claude Code install directory |
| `sed` absence invents violations | Same sandbox, valid ledger in, two invented lines out |
| `install.sh` needs `rsync` | `grep -n rsync install.sh`, 4 call sites, `set -euo pipefail` on line 4 |
| Spec template fails the lint | Fixture built to `dispatch.md`'s `### Plan` block, linted |
| 26% / 29.7% duplication | Jaccard ≥ 0.72 over 221 sage paragraphs against 169 subagents paragraphs, run twice by different agents |
| subagents 32 runs, 21k–7.12M | `grep -c '^| 2026-'` and column extraction over `calibration.md` |
| Ledger protocol mostly alive | Six ledgers read and linted; counts in 4.2 |
| Alt lane not installed, hook global, ~15 ms | `ls ~/.claude/agents/`, `~/.claude/settings.json`, 20 timed invocations |

The run ledger is at `.claude/plans/sage-ledger-b78feea9.md`. Agent detail files live in this session's scratchpad and die with the session, so everything load-bearing is restated above or reproducible from this table.
