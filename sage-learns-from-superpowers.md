# What sage can learn from superpowers

## What this document is

This document lists fifteen changes to make to the `sage` skill. Each one comes from studying the `superpowers` plugin. It also lists five ideas sage should refuse, and four it already has.

The owner of this repository wrote it. The study ran on 2026-08-21. Seven checking passes corrected it on 2026-08-22.

This document cites sage's memory files by line number. Those files are live. They are local to one machine. A periodic consolidation pass rewrites them and moves older detail into `memory/local-archive.md`. The line numbers here are correct as of 2026-08-22, and they will drift.

Read it to decide what to change in sage next. Every recommendation names the exact file and the exact section to edit, at the top, before any argument. If you disagree with the argument, you can still see the target.

Every recommendation uses the same fixed recipe of headings. That is deliberate. Superpowers measured that a positive recipe, which states what the output is and in what order, shapes the form of an output better than free prose does. This document applies that finding to itself.

## Words used in this document

| Term                   | Meaning                                                                                                                                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Claude Code            | A command-line program that runs an AI coding assistant in a terminal.                                                                                                                          |
| harness                | The program that runs the AI assistant. Claude Code is one harness. Other vendors have their own.                                                                                               |
| skill                  | A folder of written instructions that an assistant loads when a task matches it. A skill changes how the assistant works. It is text, not code that runs.                                       |
| plugin                 | A bundle that holds several skills, and can also hold scripts and hooks.                                                                                                                        |
| subagent               | A second copy of the assistant, started by the first one. It begins with no memory of the conversation. It gets only the instructions it is handed.                                             |
| dispatch               | To start a subagent and give it a task.                                                                                                                                                         |
| context window         | The total amount of text an assistant can hold at one time. Everything it reads and writes fills the window.                                                                                    |
| compaction             | What happens when the context window fills. The harness replaces most of the text with a summary, and detail is lost.                                                                           |
| token                  | The unit that text is measured and billed in. One token is roughly three quarters of a word.                                                                                                    |
| hook                   | A script the harness runs automatically at a set moment, such as the start of a session.                                                                                                        |
| ledger                 | A file that records what a run did, so the record survives compaction.                                                                                                                          |
| orchestration          | One assistant splitting work across several subagents and combining their results.                                                                                                              |
| superpowers            | The plugin studied here. Written by Jesse Vincent. Public and widely installed.                                                                                                                 |
| sage                   | The skill studied here. Written by the owner of this repository. Used on one machine.                                                                                                           |
| parent                 | In sage, the assistant that runs the task and dispatches every subagent. The same role as superpowers' controller.                                                                              |
| brief                  | In sage, the written instructions a parent hands to one subagent. Sage's brief has thirteen named fields.                                                                                       |
| lens                   | One reviewer subagent with one narrow job. Several lenses read the same work looking for different faults.                                                                                      |
| refuter                | A subagent told to attack a piece of work and prove it wrong, rather than to confirm it.                                                                                                        |
| rail                   | A condition that stops a sage run and asks the human. Sage has four today.                                                                                                                      |
| topology               | A named pattern for splitting work across subagents. For example, several subagents on one question, or a chain of subagents in order. Sage keeps eleven of them in `references/topologies.md`. |
| blind behavioural lens | A subagent told to perform a written procedure on a sandbox copy. It is never told the defect history or the author's intent. It shows what the text makes an agent do.                         |
| control arm            | A second run of the same test with the guidance removed. It shows what would have happened without the text.                                                                                    |
| compression floor      | Sage's list of eight things a cut may never remove from its own text.                                                                                                                           |
| calibration band       | A tag on a sage rule showing how well confirmed it is: `established`, `recurring` or `provisional`.                                                                                             |
| occupancy              | How much of the parent's context window is already full, measured in tokens or as a percentage.                                                                                                 |
| failure ladder         | Sage's fixed order of responses when a unit fails: sharpen the brief, then dispatch one tier up, then take the work inline.                                                                     |
| assumption log         | A table in the ledger. One row every time sage resolves an ambiguity a human would otherwise have been asked about.                                                                             |
| watch list             | A table in `memory/local.md` holding open gaps and suspected defects until a later run settles them.                                                                                            |
| opus, sonnet, haiku    | Names of three Claude models of different strength and price. `haiku` is the fastest and cheapest. `sonnet` is the middle one. `opus` is the strongest and the dearest.                         |
| N=5, N=1               | How many times a measurement was repeated. `N=5` means five repeats. `N=1` means one observation only, which is a hint and not a reliable average.                                              |
| worktree               | A second checked-out copy of a git repository. Work in one worktree does not disturb another.                                                                                                   |
| mandate                | The one job a reviewer is told to do. Two reviewers have disjoint mandates when their jobs do not overlap.                                                                                      |
| PreToolUse             | A kind of hook. The harness runs it just before a tool call, and it can block that call before it happens.                                                                                      |
| maxTurns               | A limit on how many steps a subagent may take before the harness stops it. It is the only per-unit budget limit a saved agent file can set.                                                     |
| micro-test             | A small experiment on one piece of wording. It runs the same prompt several times, with and without the wording, and counts the difference.                                                     |

## How each recommendation was screened

Sage's log records a failure mode for documents like this one: "asserting an absence after checking only one place." So every gap below was checked by `grep` against the installed corpus before it was written down. The corpus is `~/.claude/skills/sage/{SKILL.md,references/*.md,memory/*.md}` and `~/.claude/agents/*.md`.

That screening held. A later check re-ran all fifteen absence claims over a wider corpus. The wider corpus added `bin/*.sh`, `sage-promote/SKILL.md` and `memory/local-archive.md`. All fifteen absences still hold.

The screening had one blind spot, and it was serious. It checked whether sage **lacked** the idea. It never checked whether the **address** was right. Three obvious-looking addresses turned out not to exist in sage. There is no topology pattern for the blind behavioural lens. There is no "Return format" section in the file that carries the Task brief. There is no risk assessment in `SKILL.md` Step 1.

Every address below was re-checked with `grep -n "^## \|^### "` against the named file. Where a recommendation asks for a new file or a new section, the text says so.

---

## Do these first

### 1. Test sage's own wording against a control arm

**Change this file:** `references/topologies.md` → add a new section `## 12. Blind behavioural lens`. That section does not exist yet, and creating it is a precondition for the rest of this item.
**Also change:** `SKILL.md` → `## Step 5 — Verify and integrate`, because the behavioural-test rule already lives there, and nothing would read pattern #12 without a pointer from it.
**Also change:** `~/.claude/skills/sage-promote/SKILL.md` → `## The write machinery`, step 4 (line 84). That step is the degradation gate. All four corpus-writing stages run the write machinery, so a clause there reaches every one of them (`sage-promote/SKILL.md:75`). A narrower alternative is stage two, between steps 2 and 3 at `sage-promote/SKILL.md:158-159`, if the run wants the arm to cover promoted clauses only.

**What is wrong today.** Sage runs a blind behavioural lens and has no pattern entry for it. `references/topologies.md` holds eleven numbered patterns. Pattern #10 is "Blind acceptance suite", which is a different thing. The lens exists only as a cost band and a rule in `memory/local.md`, at lines 34 and 74, plus two run rows now in `memory/local-archive.md`, at lines 147 and 150. Sage also runs only one arm. Every blind-behavioural result in the log says "the actor did X with the new text". None answers "what would it have done with the old text, or with none?"

Sage has no vocabulary for the missing arm. `grep` finds no `no-guidance control`, no `control arm`, no `pressure scenario` and no `pressure test` anywhere in the corpus. `red-green` appears once, at `~/.claude/agents/implementer.md:17`, and it means the code test loop that the `clean-code` skill carries. It is not a test of sage's own wording.

**What to change.** Do three things, in order.

1. Write pattern #12 in `references/topologies.md`, describing the lens sage already runs. Sage's own memory already states its value, at `memory/local-archive.md:147`: "Reviewers rule on text; only an actor reveals what the text makes people do."
2. Put the control-arm clause inside that new pattern:

> When a `/sage-promote` pass writes behaviour-shaping text into sage's own corpus, dispatch this lens twice. Once against the pre-change text, taken from the frozen pre-edit corpus so the baseline is what actually shipped. Once against the change. Adopt the change only if the arms differ. If the control arm does not exhibit the failure, there is nothing to fix. Stop, and do not author the guidance.

3. Add one pointer from `SKILL.md` Step 5 to pattern #12. Step 5 already carries the rule that a behavioural test measures a mechanic only if it performs the action the trigger names. That is the sentence the pointer belongs next to.
4. Add the same clause to `sage-promote/SKILL.md:84`, or to stage two at `:158-159`. Without this step the clause is unreachable, for the reason below.

**Why the trigger names the promotion skill.** The obvious trigger, "when a run modifies behaviour-shaping text in sage's own corpus", would be close to vacuous. A sage run does not write those files. The writes table at `sage-promote/SKILL.md:22` assigns `SKILL.md` and `references/` to stage zero, stage two, stage three and eviction, and assigns a sage run "never". The record agrees. Seven of the eight `skill <date>` cells at `memory/local.md:44-53` are tagged `(build-authored, SKILL.md)`, and no cell there names a sage run as the author. The skill corpus is written by `/sage-promote` and by hand.

**The proposed address in `topologies.md` does not reach the promotion skill on its own.** `grep -n "topologies" ~/.claude/skills/sage-promote/SKILL.md` returns nothing. The only sage reference files the promotion skill treats as authorities are `references/memory.md` and `references/harness.md`. A pattern written into `references/topologies.md` is therefore invisible to a promotion pass. This is a repeat, not a new risk. Pattern #11, the pre-write plan critic, is triggered by "high risk, or any change that alters a rule every future run reads — a skill corpus, a shared template, a convention file" (`references/topologies.md:71`). That trigger describes the promotion skill's exact situation, and the same grep shows #11 is unreachable from it. A pattern #12 would land in the same hole. This is the strongest reason to write the clause into `sage-promote/SKILL.md` as well as into the pattern.

**How this relates to the degradation gate sage already ships.** The promotion skill already runs one refuting checker over the frozen corpus diff, at `sage-promote/SKILL.md:84`, briefed to default to refuted. Its mandate is to "name a case the pre-edit corpus handled that the post-edit corpus handles worse, a second home for a rule, a lost floor item, or a behavior change wider than the edits claim". That gate already buys most of what a control arm buys: a pre-versus-post comparison of two corpus states, an adversarial default, maker and checker on different model families with the family claim measured (`:68`), empirical world-sampling when it is briefed for it, and a cheap failure path, because a refuted edit reverts by its draft. The briefing lesson at `:130` records that world-sampling is what does the work: "Brief that gate to re-measure the claim the field makes, not to read the diff. Both repairs this clause was written for were factually wrong, both passed all four whole-corpus checks, and both were killed only because the gate went and sampled the world instead."

What the gate does not buy is null-effect detection. All four of its targets are degradations. An edit whose post-edit corpus behaves exactly like the pre-edit corpus is not worse, adds no second home, loses no floor item, and changes nothing wider than claimed. It passes the gate cleanly and lands. The four whole-corpus checks do not catch it either, because none of them tests behaviour.

**Two things make this item weaker than it first reads, and a reader should have them.** First, half of a control arm's question is already answered upstream. A rule reaches stage two only on a `→ skill text` trigger that needs six confirmations from real runs (`sage-promote/SKILL.md:147`). So "does this rule matter in the field" is settled by run history before any arm runs. What stays untested is whether the distilled wording binds. Second, a promotion pass orchestrates no task, so there is no workload to run the arm against. Implementing the arm means importing superpowers' micro-test apparatus: five or more repeats, every flagged match read by hand, variance treated as a result (`skills/writing-skills/SKILL.md:575-585`). It does not mean running an existing test twice.

So the item's remaining claim is narrow and should be read as such: the degradation gate cannot see a null effect, and a control arm can. That is the whole of what this item buys over machinery sage already owns.

**Where the idea comes from.** Superpowers treats skill text as code that shapes behaviour, and refuses to change it without evidence. Its full cycle is at `skills/writing-skills/SKILL.md:552-573`. Run a pressure scenario without the text and record the failure word for word. Write text that answers exactly those failures. Find the new excuse the agent invents and close it. Below that sits a cheaper loop for wording alone, at `:575-585`: one fresh sample per call, the real surrounding context as the system prompt, always a no-guidance control, five or more repeats, every flagged match read by hand, and variance treated as a result in itself.

The measurement behind it is real, but the two versions of it disagree in strength. A design specification dated 2026-06-10 reports a dispatch-composition task scored on how many specification values got re-typed, where lower is better. A prohibition scored 4.4. The no-guidance control scored 3.6. A positive recipe scored 3.0 with zero variance. That flat claim, that the prohibition was worse than writing nothing, appears only in the design specification, at `docs/superpowers/specs/2026-06-10-positive-instruction-redesign-design.md:14`. The shipped skill hedges it. `skills/writing-skills/SKILL.md:470` says the prohibition arm "trended worse than even the no-guidance control", and claims fully separated distributions only against the recipe arm. Use the hedged version. The direction is sound. The size of the effect against the control is a trend at N=5.

**Cost.** One extra dispatch per corpus change. Price it off the upper half of sage's band, not the lower. `memory/local.md:34` splits the band: "21–32k against a sandbox fixture; **~138k where the brief names protocol sections it must hold**." A control arm on sage's own text is the second case. Budget about 140k per dispatch. Sage's log already records getting this wrong once. A corpus-facing behavioural lens estimated at 25k landed at 138k, "priced from the task's length, not from the two protocol sections it had to hold" (`memory/local.md:74`).

**Risk.** Two arms at N=1 each is still not a measurement. Superpowers' own rule is five repeats, and "Single samples lie." Sage should record that it is running N=1 and treat the arms as a weak signal, not a result. That is the same hedging the Bands table already does with its run-count column and its "Uncovered classes" line at `memory/local.md:36`.

---

### 2. Adopt "Match the Form to the Failure"

**Change this file:** create `references/authoring.md`. It does not exist yet. `references/` currently holds only `dispatch.md`, `harness.md`, `memory.md` and `topologies.md`.
**Also change:** `SKILL.md` → `## References` (line 319), adding one line for the new file, because sage's reference files are read only because that list names them. A new reference file with no entry is a file nothing opens.

**What is wrong today.** Sage has no rule about which shape a piece of guidance should take. `grep` finds no `positive recipe`, no `prohibition`, no `match the form` and no `nuance clause`. Sage does have a compression floor at `references/memory.md:168`. It lists eight things a cut may never remove, and the order in which a rule breaks when you cut past it. That is a better instrument than superpowers' word budget, but it governs what may be removed. It never governs which shape to use.

This matters because sage is almost entirely text. The corpus is 29,055 words across `SKILL.md` and the four reference files, measured 2026-08-22. The study that produced this document measured 28,969 words on 2026-08-21 at 22:01. Its whole job is making a fresh assistant act in a particular way. It is written almost entirely in one shape: a declarative rule with an anecdote that makes the rule recognisable. That shape maps to superpowers' "recognition table" category, which measures well.

But sage also carries many composition instructions. Examples: "Write the plan into the ledger" (`SKILL.md:103`), "The implementer's brief carries the criterion IDs and never the suite path" (`references/dispatch.md:25`), and "Return format: the agent report below, ≤1–2k tokens" (`references/dispatch.md:22`). Composition is exactly the category where superpowers measured prohibitions failing and recipes winning.

**What to change.** Create `references/authoring.md`. Give it three parts.

First, the four-row classifier, taken from `skills/writing-skills/SKILL.md:463-468`:

| Baseline failure                                                                         | Right form                                                                         | Wrong form                                          |
| ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------- |
| Skips or violates a rule under pressure (knows better, does it anyway)                   | Prohibition + rationalization table + red flags                                    | Soft guidance ("prefer…", "consider…")              |
| Complies, but output has the wrong shape (bloated prompt, buried verdict, restated spec) | Positive recipe or contract: state what the output IS — its parts, in order        | Prohibition list ("don't restate", "never narrate") |
| Omits a required element from something they already produce                             | Structural: a REQUIRED field or slot in the template they fill in                  | Prose reminders near the template                   |
| Behavior should depend on a condition                                                    | Conditional keyed to an observable predicate ("if the brief exists, reference it") | Unconditional rule + exemption clauses              |

Second, the two corollaries, quoted from `skills/writing-skills/SKILL.md:473-474`. Nuance clauses cost more than they buy: "appending a single nuance clause to a winning recipe degraded it from consistent to noisy". Exemption clauses do not scope: "'This limit doesn't apply to code blocks' still suppresses code blocks".

Third, the anchoring result, as a checklist row. Superpowers found that abstract guidance sitting next to concrete commands loses to the concrete commands. An abstract step that said "you know your own toolkit" passed 2 of 6 runs. Naming the candidate tools explicitly took it to 50 of 50 (`docs/superpowers/specs/2026-04-06-worktree-rototill-design.md:100`). Sage mostly already does this. Its briefs name exact paths and exact commands. So this row is a checklist item to hold the line, not a repair.

Tag the whole file `(calibration: provisional)` and name each row's provenance in the text. It cannot enter as `recurring`. Sage's bands are defined by confirmation counts held in `memory/local.md:44-54`, so an externally sourced band has no count and no falsifier behind it. `memory/local.md:69` already files untracked `(calibration:)` citations as a known gap. Enter the finding through a Watch-list row so the promotion path can raise it later.

Then run one pass over `SKILL.md` Step 3 and `references/dispatch.md`'s Task brief. Reclassify each instruction and convert composition prohibitions into recipes. Sage's Task brief block at `references/dispatch.md:9-23` is already a recipe, a list of thirteen named fields. That is evidence the shape works. Several Step 3 bullets are prohibitions about the same subject, such as `SKILL.md:130` ("Hand off via artifacts, **never** via transcript").

**Where the idea comes from.** Superpowers classifies the failure before it chooses the shape of the guidance. The evidence is uneven, and importing it needs per-row provenance rather than one citation.

- Row 2 and both corollaries come from the 2026-06-10 micro-test campaign, opus, N=5 per phrasing.
- Row 3's nearest support is a live-run anecdote, not a micro-test: prose guidance decayed mid-session once, inheriting the expensive model for 17 dispatches at about $5 (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:88-90`).
- Rows 1 and 4 are stated in `skills/writing-skills/SKILL.md` with no measurement cited anywhere in the repository.

There is also a five-clause classifier for negative instructions, at `docs/superpowers/specs/2026-06-10-positive-instruction-redesign-design.md:20-33`. Tripwires work. Recognition tables work. Prohibitions on a single discrete directive work. Prohibitions on composition backfire. Ties go to the shorter phrasing.

**Cost.** One authoring pass, plus the control-arm check from item 1.

**Risk.** The finding is external and has never been reproduced on sage's own corpus. Three of the four rows carry no measurement at all. It must enter as `provisional`, not as `established`. Item 1's control arm is the thing that would raise it.

---

### 3. Add turn count to model placement

**Change this file:** `SKILL.md` → `## Step 3 — Brief`, the tier table at lines 138-145.
**Also change:** `references/harness.md` → `## Models and effort` (line 57), because `SKILL.md:147` says harness.md "owns the placement and its reasons". A placement rule written only in `SKILL.md` contradicts that ownership sentence.

**What is wrong today.** Sage knows `maxTurns` only as a cap. `references/harness.md:184` calls it "the only per-unit budget rail the harness itself provides", and `:192` calls it "the gap worth closing first". Nowhere does sage treat turn count as a cost driver that changes which model a unit gets. Its tier table places purely by unit property: mechanical work to the fast tier, standard implementation to the standard tier, review to the frontier tier, ambiguous long-horizon work to the apex tier.

Sage's own evidence points the same way and sage has not noticed it. The two `explorer` rows in its run log came in at 0.67× and 1.02× of estimate (`memory/local-archive.md:149`). Only one of the two ran on haiku. The other was a logged sonnet override. Both were bulk reading, which is the single-pass case where a cheap model does pay. Sage has no logged row for a cheap model doing multi-step work, and its Bands table says so: "Uncovered classes… any substantial `haiku` run" (`memory/local.md:36`).

**What to change.** Add one paragraph under the tier table:

> Cross the tier choice with the unit's **step count**. A cheap model on single-pass work, such as reading, searching or extraction, is the cheapest thing in the fleet. A cheap model on multi-step work takes 2-3× the turns. Turns are what wall-clock and context cost track, so the cheap tier can cost more overall (calibration: provisional — external). Where a unit's brief names exact paths, exact commands and the decisions already made, the work is transcription and the cheap tier holds. Where the unit must discover its own path, floor it at standard.

**Where the idea comes from.** Superpowers ships this rule in a skill, not in a plan document, at `skills/subagent-driven-development/SKILL.md:208-214`:

> **Turn count beats token price.** Wall-clock and context cost scale with how many turns a subagent takes, and the cheapest models routinely take 2-3× the turns on multi-step work — costing more overall. Use a mid-tier model as the floor for reviewers and for implementers working from prose descriptions. When the task's plan text contains the complete code to write, the implementation is transcription plus testing: use the cheapest tier for that implementer. Single-file mechanical fixes also take the cheapest tier.

It has a measurement behind it. `docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:42-46` records "cheap models taking 2-3× the turns on multi-step work (678 of 1197 subagent turns were haiku)". This is the strongest-evidenced item in the document.

**Cost.** Nothing to run. It is one paragraph in each of two files.

**Risk.** Low, and the note names its own uncovered class. Sage's ground-truth rule already does most of the work: "a brief that names its ground truth has run ~2–2.5× cheaper than an open-ended one and failed less" (`SKILL.md:126`). This change says why that discount exists and when it stops applying.

---

## Worth doing

### 4. Add a judgment-collapse rail

**Change this file:** `SKILL.md` → `## Rails` (line 238).
**Also change:** `SKILL.md` → `## Stop rule` (line 311) and the failure-ladder bullet at `SKILL.md:161`, because both use the same "identical signature" test that the new rail uses. A precedence sentence written only inside the new rail is invisible to a run that arrives through the ladder or the Stop rule.

**What is wrong today.** Sage's four rails are all resource or blast-radius conditions (`SKILL.md:238-245`). Destructive, irreversible or externally visible actions. More than one writer without worktree isolation. A writer touching a path outside its lease. The budget rail. None of them fires when the task itself makes no sense.

The nearest thing is in the Stop rule at `SKILL.md:315`: "If a failure survives two fix attempts _with the same signature_, stop patching — reopen the assumptions, the reproduction, or the plan, and write what you reopened…". That is an instruction to re-plan, not an instruction to stop and ask. The failure ladder's last rung is "take it inline" (`SKILL.md:161`). That assumes the parent can finish the work, which is the one assumption that fails when a task is incoherent rather than merely hard.

Sage also has no upper bound on how much ambiguity one run may resolve on its own authority. `SKILL.md:112` and `references/dispatch.md:142` are the whole of the assumption-log rule, and neither states a count, a rate or a severity ceiling.

**What to change.** Add a fifth rail, and change the literal word "Four" at `SKILL.md:240` to "Five".

> 5. **The task as specified has no non-guessing path.** Not a hard unit. A unit whose requirements contradict each other, whose ground truth does not exist, or where every option is a coin flip with no evidence either way. The rail fires only after the parent has taken the unit inline **and** still cannot name a single assumption that would resolve it. Fire the rail, print what you tried and what you could not settle, and end the turn.

Then write the precedence sentence, and make it readable from all three sites. The ladder's skip-to-inline runs first, because it is cheap and often works. The rail fires only after that. Without this clause the rail would preempt the ladder and stop runs the ladder would have finished. Sage's compression floor requires this sentence: `references/memory.md:177` demands "A **precedence sentence** wherever two rules can both fire."

**Where the idea comes from.** Superpowers lists exactly four things that stop its controller, at `skills/subagent-driven-development/SKILL.md:27-31`. Three are resource or blast-radius conditions, like sage's. The fourth has no analogue in sage: "a plan so broken that every path forward is a guess". Everything else is a ruling, recorded and carried forward. The claim is clean and the enforcement is visible in the same file's flowchart.

This matters more for sage than for superpowers. Superpowers has a human at the design gate, so an incoherent plan usually dies before execution. Sage takes an arbitrary task with no gate at all, and its assumption log is the record of resolving ambiguity on its own authority.

**Cost.** One rail plus one precedence sentence. Sage's ask-the-user primitive already exists and rails 1 to 4 already exercise it (`SKILL.md:249`).

**Risk.** A rail that fires too easily turns sage back into a tool that needs a human present. The trigger above is deliberately narrow because it requires both conditions: the inline attempt has happened, and no assumption can be named. Sage's failure ladder already counts signatures rather than attempts, so the first half is already observable.

---

### 5. Make a wrong finding cost something

**Change this file:** `references/dispatch.md` → `## Finding schema` (line 41), extending the bullet at line 58 that already reads "Low-confidence hypotheses are investigation leads, not blockers."
**Also change:** `SKILL.md:122`, the one-line mirror of the Task brief contract, because Step 3 reads that line rather than reading `dispatch.md`.

**What is wrong today.** Nothing in sage's generic brief makes a wrong finding cost anything. `grep` finds no `false positive`, no `confidently wrong` and no `counts negatively` in any brief-shaping text. The only nearby hits are about the watchdog script's own false-positive rate.

Sage states the problem clearly at `SKILL.md:194`: "Reviewers report what you ask them to look for. One told to find gaps will find some even when the work is sound. Scope the mandate to correctness and the stated criteria, and make 'no findings' explicitly valid." That removes the floor on finding count. It does not put a price on a wrong finding.

One qualification narrows this item considerably. The saved `verifier` agent already prices one, at `~/.claude/agents/verifier.md:32`: "manufacture a finding to look useful; a padded report costs the parent more than an empty one". So every `verifier`-typed dispatch already carries a version of the clause. The gap is only the generic contract, which governs plain dispatches and any reviewer row that is not a saved agent. This is an extension, not an invention.

Sage's log holds the failure this clause prevents. A prior-art `explorer` "showed systematic false-OPEN bias: it marked four proposals OPEN that one parent grep found LANDED, because its greps used the sibling skill's wording rather than sage's" (`memory/local-archive.md:149`). Nothing in that unit's brief made a wrong claim cost anything. Sage's triage then spends one command per false finding to reject it, and that cost lands on the parent, which is the most expensive seat.

**What to change.** Extend the `## Finding schema` bullet:

> Verify before you claim. Every finding names the command or the `file:line` that establishes it. A confidently-wrong finding costs more than a missed one, because the parent pays a command to reject it. Report uncertainty as uncertainty rather than as a finding. "No findings" remains a complete answer.

Do not put this in the `Return format:` field of the Task brief. `references/dispatch.md:3` says to copy those field shapes verbatim into every brief, and `SKILL.md:122` mirrors the field in compressed form. A clause added there would bloat every brief and the two copies would drift apart.

**Where the idea comes from.** The wording is borrowed. The evidence is not.

Superpowers' scoring rule reads: "Verify before claiming. If you assert 'X is broken', check on disk first. Confidently-wrong claims count negatively." That sentence sits at `docs/superpowers/plans/2026-05-06-lift-drill-into-evals.md:1250-1251`, inside a one-off dispatch prompt in an implementation plan dated 2026-05-06, written for superpowers' own repository. The same scoring rule recurs fourteen lines later, at `:1264`, where it is attributed to "the cross-platform PR pattern". So the rule is used twice, not once, and it is presented there as an existing practice. Both instances sit inside that one plan document. Neither is in a shipped prompt template. `implementer-prompt.md`, `task-reviewer-prompt.md`, `re-review-prompt.md` and `code-reviewer.md` all lack it. It carries no evaluation evidence anywhere.

So the external warrant is an untested rule that never left a plan document. The recommendation stands on sage's own evidence instead: the false-OPEN explorer, and the fact that the shipped `verifier` file already found the same clause worth carrying.

**Cost.** One extended bullet in one file, plus one mirrored line.

**Risk.** Over-application could silence genuine low-confidence leads. Sage's finding schema already handles that correctly, so the clause must route uncertainty into the existing channel rather than suppress it.

---

### 6. Ship one brief template, not five

**Change this file:** create `references/briefs/narrow-steer.md`. Neither the directory nor the file exists. `references/` holds only `dispatch.md`, `harness.md`, `memory.md` and `topologies.md`.
**Also change:** `SKILL.md` → `## References` (line 319), because a directory that nothing lists is a directory that nothing reads.

**What is wrong today.** `references/dispatch.md` carries one generic Task brief contract of thirteen named fields, plus a note at line 25 that three dispatch classes change shape. Those three are the blind suite author, the implementer and the verifier. That is a contract, not a template. Every run still composes its own brief, and every run composes it slightly differently.

Sage's memory records one measured cost of per-run composition, at `memory/local-archive.md:147`: "I called two re-verdicts 'narrow' and briefed them as full rounds (six named findings each, plus 'run a command to settle it'), and they priced at +45k and +52k against the ~7k narrow-steer band." The narrow band is corroborated at `memory/local.md:32`. That is a briefing error, not a model error, and it cost about 90k tokens in one run.

**What to change.** Write one file, `references/briefs/narrow-steer.md`. It carries the generic thirteen-field contract with the narrow-steer fields pre-filled, and a one-item mandate slot marked REQUIRED. Then add one line to `SKILL.md` `## References` so a run can find it.

**Why one file and not five.** Four other roles could each take a file: `explorer.md`, `verifier-lens.md`, `refuter.md` and `implementer.md`. None of the four has a measured incident behind it. Five new files also fight item 9's length ceiling directly. One file, backed by one measured incident, does not. If a second incident lands on a second role, write a second file then.

**Where the idea comes from.** Superpowers keeps prompt templates in the tree as versioned artifacts that the controller fills, rather than composing prose per run. The mechanism is weaker than it looks.

Six prompt templates exist, not four. Beyond `implementer-prompt.md`, `task-reviewer-prompt.md`, `re-review-prompt.md` and `code-reviewer.md`, there are also `skills/brainstorming/spec-document-reviewer-prompt.md` and `skills/writing-plans/plan-document-reviewer-prompt.md`.

All four of the named files have bracket slots and a stated return contract. Only two of the four add a Placeholders legend that marks which slots are REQUIRED: `task-reviewer-prompt.md:190-204` and `re-review-prompt.md:103-110`. `implementer-prompt.md` has no legend, but it does mark its single REQUIRED slot inline, at `implementer-prompt.md:8`. `code-reviewer.md:137-141` has a legend with no REQUIRED marking on any entry. So marking a slot REQUIRED is a superpowers convention, and three of the four files do it somewhere. Collecting those marks into a legend is not the convention, and that half is this document's own proposal.

Superpowers does hold the templates still. `CLAUDE.md:93-100` requires evaluation evidence before a behaviour-shaping file changes. That part transfers.

**Cost.** One authoring pass and one reference line. No per-run cost. Filling a template is cheaper than composing a brief.

**Risk.** Templates go stale. Superpowers manages that by requiring evaluation evidence to change one. Sage would manage it with item 1's control arm and its existing `(calibration:)` tags.

One nearby case does not support this item. Alt-lane dispatches once carried a `model` parameter the rule forbids, at a cost of "22.4k spent, three dispatches testing nothing" (`references/harness.md:123`). That case is now closed by something better than a template. `bin/sage-alt-guard.sh` is a `PreToolUse` hook that denies such a dispatch before it runs. A deterministic guard beats a slot a human might forget to fill. Rest this item on the narrow-steer incident alone, which nothing guards.

---

### 7. Test whether the saved agent descriptions do what they claim

**Change this file:** `memory/local.md` → `## Watch list` (line 56), adding one row for the result.
**Also change:** `references/harness.md:32`, but only if the test comes back positive, because that line asserts the control works on no measurement.

**What is wrong today.** `references/harness.md:32` states the exposure plainly: "`~/.claude/agents/` is **global**: Claude Code watches it and auto-delegates on the `description` field in every project… **Description wording is the whole of the soft control.**" Sage has never tested that control. `grep` for `auto-delegat` across `memory/local.md` and the reference files returns that one line only. No run row, band row or watch row records a test.

The descriptions themselves are already in the right shape. `explorer`'s reads in full: "Reader unit for orchestration skills (/subagents, /sage), dispatched by name from an orchestration plan. NOT a general-purpose search agent — for ordinary lookups and codebase questions, use the built-in Explore agent instead. Reports facts with file:line pointers from a fixed scope. Read and search only, no writes, no shell, no network." It leads with a triggering condition and a redirect, which is exactly what superpowers' rule prescribes. All five agent files read that way by deliberate design. So the rewrite half of this item is already satisfied. Only the measurement is missing.

**What to change.** Two parts, in order.

1. **Measure the soft control.** Run a handful of realistic prompts in a fresh session that should not capture a sage worker. Examples: "find where the retry logic lives", "review this diff", "look up the pricing page". Check whether any of the five agents was auto-delegated. The check is one `grep` of the session transcript for the agent type.
2. **Record the result as one Watch-list row, whichever way it goes.** This item is a measurement, not a text edit, so it needs somewhere to put the answer. A negative result is worth recording, because it closes an open gap that `references/harness.md:32` names. `references/memory.md:27` already makes writing that row mandatory at Step 6.

If capture does occur, then rewrite the descriptions to triggering conditions only. Move the capability summary into the agent file's body, where the dispatched unit still reads it but the delegation router does not.

**Where the idea comes from.** Superpowers has a whole test suite for one question: does the skill actually fire? `tests/explicit-skill-requests/` holds nine prompt fixtures and exactly four runners plus an aggregator. The runners cover single turn, multi-turn, extended multi-turn, and a haiku variant run against the user's real instructions file. `run-test.sh:97-121` also warns on premature tool use, meaning tools invoked before the skill was loaded.

Superpowers also carries a measured rule about description text, at `skills/writing-skills/SKILL.md:150-158`. A description that summarises the workflow becomes a shortcut agents take instead of reading the skill. Its recorded instance: a description saying "code review between tasks" caused an agent to do one review, when the flowchart showed two. Both halves are clean.

**Cost.** A handful of one-prompt sessions, plus one row.

**Risk.** Low. The finding is useful in both directions.

---

### 8. Risk-tier sage's changes to itself

**Change this file:** `references/dispatch.md` → `## Risk rubric` (line 61), adding three change-type tiers beside the existing "Hard triggers" list.
**Also change:** `references/topologies.md` → pattern `## 11. Pre-write plan critic` (line 69), its When clause, because the plan critic should fire from the tier rather than from a judgment call.

**What is wrong today.** Sage modifies its own corpus constantly. A majority of the runs in its log are self-modification, and it treats every edit alike. `grep` finds no `risk-tier`, no `staged rollout` and no `additive change`.

The change belongs in the risk rubric, not in Step 1. Sage's risk rubric lives at `references/dispatch.md:61`. `SKILL.md` `## Step 1 — Decompose` holds the scout rule, five split rules, the delegation tests, a fleet-scale table and a topology pointer. It holds no risk assessment. Its only contact with the rubric is the pointer at `SKILL.md:87`. A second risk classification in Step 1 would give sage two risk vocabularies. A run would read them at two different steps. That is exactly the condition `references/memory.md:177` forbids.

Sage's only gate today is topology #11, the pre-write plan critic. That gate is already keyed on change type. Its When clause reads "high risk, or any change that alters a rule every future run reads — a skill corpus, a shared template, a convention file" (`references/topologies.md:71`). So the trigger this item would add is largely shipped. What is absent is the tiering. Today one gate either fires or does not. There is no cheaper rung for an additive change, and no separate cross-corpus lens.

**What to change.** Add three tiers to the Risk rubric, keyed on what is being changed rather than on how much:

> **Additive** — a new section, a new row, a new file that nothing else reads yet. One review lens.
> **Mechanical** — an edit to a contract, a template, a script, or a trigger that other text depends on. Pre-write plan critic (#11) required, plus a cross-corpus lens checking every site that reads it.
> **Behavioural** — an edit to a rule that changes what a fresh instance does: a rail, a ladder rung, a threshold, a brief. Control arm required (item 1), plus the own-work refuter.

Then change pattern #11's When clause to fire from the Mechanical and Behavioural tiers, and add a precedence sentence there, because the tiers and the existing clause key on the same observable.

**What sage's own log shows.** Additive changes land cleanly. Edits to load-bearing mechanics produce the expensive failures. Three examples:

- The run where "one column closes it" did not close the path it named (`memory/local.md:78`).
- The run where a fix "introduced a defect at the seam between two of its own fixes" (`memory/local-archive.md:147`).
- The run where a `Class` value the column does not take, and a `Kind` whose closure path the protocol denies, were both prescribed. The implementing run caught the first and propagated the second (`memory/local.md:81`).

Each was caught by a different mechanism aimed at the parent's own work. The first by a pre-write plan critic. The second by a refuter. The third by two disjoint reading lenses on the parent's own diff. Three separate own-work mechanisms each caught one mechanical failure. That is a better argument for tiering than one mechanism catching three.

**Where the idea comes from.** The evidence is a draft, not shipped practice.

`docs/plans/2025-11-28-skills-improvements-from-user-feedback.md` is marked "Status: Draft". Its real headings are "### Phase 1: High-Impact, Low-Risk (Do First)", "### Phase 2: Moderate Changes (Test Carefully)" and "### Phase 3: Optimization (Validate First)". None names a change type. Phase 1 already contains a template change. Phase 2 holds three items and only one is a prompt-template edit.

What does support the idea is the per-item annotation inside those phases: "Clear addition, doesn't change existing content", "Changes prompt template (higher risk)", "Changes workflow (higher risk)". Risk by change type is real there. The clean three-tier taxonomy above is sage's own.

Superpowers does ship one hard rule of this family, at `CLAUDE.md:100`: "Do not modify carefully-tuned content (Red Flags tables, rationalization lists, 'human partner' language) without evidence the change is an improvement."

**Cost.** No new machinery. It routes existing topologies by a cheaper trigger than "the parent judged this high-risk."

**Risk.** Tier inflation, where everything becomes Behavioural. A tiebreak fixes that: if closing the change means editing something other text reads, it is at least Mechanical. That tiebreak is this document's own proposal. Superpowers has no such rule. Its only "tiebreak" is about phrasing length: "Ties go to the shorter phrasing."

---

## Small and cheap

### 9. Give sage a length ceiling, not only a floor

**Change this file:** `references/memory.md` → `## The compression floor` (line 168).

**What is wrong today.** Sage's compression floor points in one direction only. It lists eight things a cut may never remove and the order a rule breaks when you cut past it. A ceiling exists for the memory files: consolidation triggers past about 10k tokens, and the self-check requires the result to be smaller than what it replaces (`references/memory.md:114`, `:95`). Nothing of the kind governs the skill text, and that is where the growth is.

The corpus is 29,055 words across `SKILL.md` and the four reference files, measured 2026-08-22. The study that produced this document measured 28,969 words on 2026-08-21 at 22:01. `SKILL.md` alone is 10,900 words today, and was 10,814 words at the earlier measurement. That single file is more than twice the size of superpowers' largest skill.

This is a real cost, not a matter of taste. The run that produced this document recorded its parent occupancy at plan time as "plan starts at 15.3%" (`sage-ledger-1b3d9d73.md:43`). Cite that percentage, because it is the figure an artifact holds. No artifact records a token figure for it. The figure 154,123 is arithmetically consistent with 15.3% of the 1,006,380-token window, but consistency is not a record. Treat 154,123 as a reconstruction.

Fresher evidence points the same way. The run that produced this rewrite reached 24% of a 1,000,000-token window after seven reader units and before writing anything (2026-08-22). Reading sage's own corpus was a large part of that. Sage's handover threshold is 30% (`SKILL.md:176`). So most of the budget that decides when sage must hand itself over goes on sage reading sage.

**What to change.** Add a ceiling clause beside the compression floor:

> The floor says what a cut may not remove. The ceiling says a cut is owed. Sage's own corpus is loaded into the window that Step 1 decomposition, Step 5 triage and the handover threshold all draw on, so every thousand words here is a thousand words of parent capacity. Where two phrasings say the same thing and neither is evidenced, the shorter one ships. Where a rule's anecdote has been superseded by a shorter one that recognises the same failure, the older one goes. Where this clause and the compression floor disagree, the floor wins.

Then record the parent's pre-dispatch occupancy in the Run-log row's existing `note` cell, beside the peak figure the row already carries. `memory/local-archive.md:149` records "parent occupancy peaked ~285k = 28%" and `:151` records "peaked 249k = 24%". So this change adds a pre-dispatch figure to an existing habit rather than starting a new one.

The `note` cell is the right place because sage's memory file fixes the row at seven columns and already carries handover actuals there. `references/memory.md:31` ends with "The seven columns do not change", and the same paragraph already owes the `note` cell three handover figures. A new column would contradict a guarded invariant and buy nothing. `references/memory.md:149` `## Structural invariants` and `bin/sage-lint.sh` are what enforce the row's shape.

**Where the idea comes from.** Take the instrument. Do not take the endorsement.

The instrument is good: a numeric word budget checked by a literal command. Superpowers states its targets at `skills/writing-skills/SKILL.md:213-220`. Getting-started workflows aim for under 150 words each. Frequently-loaded skills aim for under 200 words total. Other skills aim for under 500 words. `:261-266` gives the check: `wc -w skills/path/SKILL.md`.

The endorsement does not hold. Superpowers does not meet its own budget. Its largest skill, `subagent-driven-development/SKILL.md`, is 4,825 words. The under-200-word target is the frequently-loaded case. The under-500-word target is the ordinary case. That skill misses the under-500 one by roughly ten times.

So superpowers' record is evidence that a stated numeric ceiling does not hold itself. That is an argument for tying sage's ceiling to something enforced, not an argument against having one.

Two supporting facts are clean. `docs/superpowers/specs/2026-06-10-positive-instruction-redesign-design.md:32-33` records "Codex re-reads SKILL.md ~500× per long session (measured 2026-06-10); prose length is a real cost." And `:44` gives the tiebreak for un-evidenced text: "no evidence either way; shorter wins."

**Cost.** One clause plus one figure per run.

**Risk.** This clause cuts against the compression floor, and someone could use it to justify removing exactly what the floor protects. That is why the precedence sentence is inside the proposed text, and why the clause belongs beside the floor rather than in `SKILL.md`.

One caveat the item does not remove. `references/memory.md:11-13` scopes that whole file to the two memory files, `local.md` and `shared.md`. The compression floor already reaches past that scope, and this ceiling clause reaches further, because its subject is the skill corpus. That mismatch is defensible but real. If a `references/authoring.md` lands from item 2, the ceiling may fit better there.

---

### 10. Record what a wrong assumption would cost

**Change this file:** `references/dispatch.md` → `### Assumption log` (line 142), adding a fifth column, "what it costs if wrong".
**Also change:** `SKILL.md` → `## Step 6 — Record and surface` (line 204), the list of surfaced events, so a high-cost assumption prints.

**What is wrong today.** Sage's assumption log has four columns: "assumption", "what I chose", "what else was plausible", "how it would show if wrong". The fourth is a falsifier. It tells a later run how to detect the error. It does not say what the error would cost. Those are different things, and only the second helps a reader decide what to check first.

The condensed assumption line also does not reach the user. `references/dispatch.md:150` says "One condensed line goes in the run record", meaning the ledger's `### Run record`. Only ambiguity that changes the decomposition is a mandatory row, and Step 6's printed block does not include the assumption line. So today, the record of what sage decided on its own authority stays inside a file the user may never open.

**What to change.** Add the fifth column to the row shape:

```text
| assumption | what I chose | what else was plausible | how it would show if wrong | what it costs if wrong |
```

Then add one surfaced event to Step 6's list: an assumption whose recorded cost is high prints, with its row.

**Where the idea comes from.** Superpowers records every autonomous decision in the same shape, at `skills/subagent-driven-development/SKILL.md:23`: `Ruling: <what you decided> — <why> — <what it costs if wrong>`. It then prints every one to the human at the end. `:475-479` requires collecting every ledger line containing `Ruling:` "into your final message under 'Rulings I made', in the order you made them, each with what it costs if wrong. The list is exhaustive". Its stated reason is at `:479`: "A ruling that dies with the workspace was a decision made in secret."

Superpowers ships this in a skill, and the enforcement is a stated obligation rather than a measurement. There is no evaluation evidence for the cost column specifically.

**Cost.** One column and one line in the surfaced-events list.

**Risk.** Sage prints almost nothing by design, and that design is correct. This item does not change it. It adds one column, and lets the recorded cost decide which rows are worth printing. If every row starts reporting a high cost, the column has stopped discriminating and the print rule should be dropped.

---

### 11. Give a worker explicit permission to stop

**Change this file:** `~/.claude/agents/implementer.md` → `## Rules` (line 29).
**Also change:** `~/.claude/agents/verifier.md` → `## Rules` (line 29), the same way.

**What is wrong today.** Sage's implementer file already says a `blocked` result is correct rather than a failure, but only for named causes. `~/.claude/agents/implementer.md:63` reads "A `blocked` on a scope or lease boundary is a correct result, not a failure — the parent fixes the brief." The file also covers size: `:43-44` reads "If the unit is too big for one focused session, that is a decomposition error — report it, don't work around it."

So two causes are already permitted, scope and size. What is missing is permission to stop when the unit is the right size and inside its lease, and the agent still cannot make progress. `~/.claude/agents/verifier.md` carries no equivalent permission of any kind, so the gap is wider there.

An agent with no such permission produces weak work instead of an honest stop. Weak work then costs the parent a full review round to detect, which is the most expensive way to learn that a unit was mis-sized.

**What to change.** Add a short paragraph to `## Rules` in both files. It says that stopping because the work is beyond the unit is a correct result, and names the conditions that trigger it. Suggested triggers, adapted from superpowers: the task needs an architecture decision with several valid answers; the unit needs code it was not given and cannot find; the unit has read file after file without progress.

**Why it fits sage's own machinery.** Sage's failure ladder charges a rung for a failure and charges none for `blocked`. `references/dispatch.md:16` states it: "A unit that hits `maxTurns` returns `blocked`, not failed, and charges no rung on the failure ladder." So an honest stop is already cheaper for the run than a bad result. The agent file just never tells the agent that.

**Where the idea comes from.** Superpowers' implementer template says it directly, at `skills/subagent-driven-development/implementer-prompt.md:77-78`: "It is always OK to stop and say 'this is too hard for me.' Bad work is worse than no work. You will not be penalized for escalating". Five concrete triggers follow at `:80-85`, and an escalation shape at `:87`.

The evidence is a shipped prompt template, not a measurement. No evaluation result in the repository tests this clause.

**Cost.** One paragraph in each of two files.

**Risk.** A worker that stops too readily wastes the dispatch. Naming concrete triggers is what keeps the permission narrow, so do not ship the permission sentence without them.

---

### 12. Give reviewers a scope budget

**Change this file:** `references/dispatch.md` → `## Task brief` (line 7), the `Scope and relevant files` field.

**What is wrong today.** The field reads `Scope and relevant files: <explicit>`. It names a scope. It does not bound how far a reviewer may read outside it.

Review is sage's most expensive unit class. `memory/local.md:25` prices a frontier review lens over a prose corpus at 50-95k per agent, and says the cost "tracks the corpus the reviewer must hold, not the size of the change". Reading lenses on one diff have run 81-93k (`memory/local.md:34`). An unbounded reading scope is therefore sage's largest uncontrolled cost, and nothing in the brief today controls it.

**What to change.** Extend the field so it bounds breadth without banning it:

> Inspect anything outside the named scope only to check a concrete risk you can name. One focused check per named risk. Name both the risk and what you checked, in your report.

**Where the idea comes from.** Superpowers' task-reviewer prompt carries the same rule almost word for word, at `skills/subagent-driven-development/task-reviewer-prompt.md:45-50`: "Do not crawl the broader codebase. Inspect code outside the diff only to evaluate a concrete risk you can name — one focused check per named risk, and name both the risk and what you checked in your report. Cross-cutting changes are legitimate named risks: if the diff changes lock ordering, a function or API contract, or shared mutable state, checking the call sites is the right method."

Two things about that wording are worth copying. It gates breadth rather than banning it. And it names cross-cutting change as a legitimate risk, so the rule cannot be read as "never look outside the diff".

The same file pairs the scope budget with a test budget, at `:75-82`: run a test only when reading the code raises a specific doubt that no existing run answers, and then a focused test. Sage could copy that too, but it is a separate change and it is not part of this item.

This is a shipped prompt template. It carries no evaluation evidence.

**Cost.** Three sentences in one field.

**Risk.** A reviewer that reads too little misses a cross-cutting defect. The "name the risk" form is what prevents that, because the reviewer can always name one. If sage's reviewers start reporting many named risks with shallow checks each, the budget has become a licence and should be tightened to a count.

---

### 13. Make batching and fix-verification safe with a per-item verdict

**Change this file:** `references/dispatch.md` → `## Agent report` (line 27), requiring one verdict per checklist item where a brief carries a checklist, and one verdict per finding in a fix-verification round.

Sage does have the batching instruction. It does not have the check that makes batching safe. Superpowers shipped both together. The same gap appears a second time, in the fix-verification round, and it takes the same repair at the same address.

**What is wrong today.** Sage tells the parent to batch. `SKILL.md:76` reads: "every dispatch pays a boot cost before it does any work… so several small lookups in one area are **one** explorer with a checklist, not N agents." The boot-cost figures are one pointer away, at `memory/local.md:30`.

Sage has no check that every checklist item was actually done. `references/dispatch.md:27-38` gives the agent report shape, and nothing in it is per item. A silently skipped item and a clean sweep produce the same report.

The fix-verification round has the same hole. `SKILL.md:315` binds three things about that round: a budget of one review round plus one fix-verification round, an escalation when "a failure survives two fix attempts _with the same signature_", and where to write what was reopened. It binds no report shape. A grep for `ADDRESSED` and `attempted is not` across `SKILL.md`, `references/`, `memory/local.md`, `~/.claude/agents/` and `sage-promote/SKILL.md` returns four hits and no contract. All four are the ordinary English word "addressed", at `SKILL.md:292`, `references/harness.md:37`, `~/.claude/agents/verifier.md:38` and `~/.claude/agents/web-researcher.md:39`. There are no hits for "attempted is not".

**Be precise about what is absent, because sage carries most of the surrounding obligations already.** `SKILL.md:313` requires that "every finding is dispositioned". `SKILL.md:199` sets the four-state triage. `SKILL.md:197` already names the hazard that a fix "can silently **un-pass a criterion already verified**", which is the same hazard as superpowers' New Breakage section. What sage lacks is the return contract, meaning the shape the fix-verification report must come back in. It has the duties and no format that forces a re-reviewer to discharge them one finding at a time. The clause "'Attempted' is not addressed" has no analogue anywhere in sage, and that part is a clean gap.

**What to change.** Add two lines to the `## Agent report` section.

1. Where the brief carries a checklist, the report carries one verdict per checklist item. An item the work never reached is reported as not done, not omitted.
2. Where the brief carries findings to verify, the report carries one verdict per finding, in the order given, each `ADDRESSED` or `NOT ADDRESSED` with `file:line` evidence. Attempted is not addressed: the specific defect must no longer exist. The report also carries one section for anything the fix itself broke, with severity and `file:line`, and says "None" when it is clean.

**Where the idea comes from.** Superpowers shipped batching and the check for it in the same release. The batching instruction is at `skills/subagent-driven-development/SKILL.md:223-229`. The check is at `skills/subagent-driven-development/task-reviewer-prompt.md:105-109`: "If the brief lists several files each with its own change (a batched dispatch), check the diff against that list file by file: every listed file must have its corresponding hunk. A listed file the diff never touches is a Missing finding, no matter how clean the rest of the batch looks."

Sage took the batching and left the check.

The fix-verification contract is at `skills/subagent-driven-development/re-review-prompt.md:82-90`. It requires, per finding: "**[finding one-liner]** — ADDRESSED | NOT ADDRESSED, with file:line evidence. \"Attempted\" is not addressed: the specific defect must no longer exist." The "New Breakage in the Fix Diff" section follows at `:87-90`, taking "Anything the fix itself broke or introduced, with severity (Critical/Important/Minor) and file:line. \"None\" if clean." The controller side binds it at `skills/subagent-driven-development/SKILL.md:396-403`: "The re-reviewer verdicts each finding ADDRESSED or NOT ADDRESSED and flags new breakage in the fix diff only."

Both are shipped skill text. Neither carries an evaluation result.

**Cost.** Two lines in the report shape. No new unit and no new dispatch.

**Risk.** Low. The failure mode is a longer report on a large checklist or a long findings list, which the existing 1-2k token return budget already bounds.

---

### 14. Match the form of a promoted clause to the failure it prevents

**Change this file:** `~/.claude/skills/sage-promote/SKILL.md` → `## Stage two — into skill text`, step 2 (line 158).

**What is wrong today.** Stage two step 2 decides how long a promoted clause may be and which content class it may carry. It never decides the clause's form. In full, at `sage-promote/SKILL.md:158`: "**Write the fewest words that clear the compression floor** — the clause, its qualifier, the recognising anecdote where the floor demands one, and `(calibration: <band>)`. Nothing of the other homes' content classes: no count, date, cost, or falsifier. **A rule that needs a paragraph is not distilled yet.**" That is a word count and a content class. It says nothing about whether the text should be a prohibition, a positive recipe, a required structural slot, or a conditional keyed to an observable predicate.

Nothing else in either skill decides that either. This command returns five hits, and none of them is about choosing a form:

```text
grep -rn -i "prohibition\|rationalization\|rationalisation\|recipe\|wording" \
    ~/.claude/skills/sage/SKILL.md ~/.claude/skills/sage/references/ \
    ~/.claude/skills/sage-promote/SKILL.md ~/.claude/skills/sage/memory/local.md
```

The five are `harness.md:32` on agent `description` wording, `local.md:64` on a row's own wording, `local.md:87` on a caller following an old recipe, `SKILL.md:160` on a "worktree recipe", and `dispatch.md:79` on deduplicating findings "by root cause, not by wording".

**What to change.** Add one clause to stage two step 2, before the word-count rule. It says: name the baseline failure the rule was confirmed against, then pick the clause's form from that failure. A rule an agent violates under pressure takes a prohibition. A rule an agent complies with but whose output comes back the wrong shape takes a positive recipe stating what the output is. A missing element takes a required slot in the template the agent already fills. A behaviour that should depend on a condition takes a conditional on an observable predicate. Add the no-nuance-clause rule with it, because a grep can check that one.

**Which rule wins where they fight.** A positive recipe is usually longer than the prohibition it replaces, so this item pushes against the very step it edits. The length rule is the floor and it wins. Form is chosen inside the word budget, not against it. A clause that can only take its right form by growing into a paragraph stays in `shared.md` unwritten, exactly as step 2 already orders. If the item cannot be taken on those terms, it is not worth taking.

**Where the idea comes from.** `skills/writing-skills/SKILL.md:459-474`, "Match the Form to the Failure", maps a baseline failure to the text shape that fixes it. The measured claim is at `:470`: "In head-to-head wording tests on dispatch-prompt guidance, the prohibition arm produced clearly more of the unwanted content than the recipe arm (fully separated distributions), and trended worse than even the no-guidance control". The corollary at `:473` reads: "**No nuance clauses.** \"Don't X unless it matters\" reopens the negotiation — appending a single nuance clause to a winning recipe degraded it from consistent to noisy in the same wording tests."

**Why it matters inside sage, which is the strongest part of this item.** Sage has already paid for this exact gap. `~/.claude/skills/sage/bin/sage-alt-guard.sh:21-22` records it in the script's own header: "`../SKILL.md` states the rule three times (\"pass no `model` at all\"). It has a measured failure anyway: one run spent 22.4k proving three alt dispatches that tested nothing, and no agent noticed." An absolute prohibition, promoted into skill text and stated three times, did not bind. The repair was a `PreToolUse` hook that denies the call. `memory/local.md:87` states the general lesson for a second defect of the same shape: "Closing it needs runtime logic, not prose." Three prohibitions failed. One structural guard held. That is a form failure, measured on sage's own corpus.

**How this differs from item 2.** Item 2 puts the classifier in a new authoring reference, so a human author choosing wording can read it. Item 14 puts the same choice inside the machinery that writes the clause. Item 2 tells an author which form to choose. Item 14 makes the promotion step choose one. They are one level apart, not duplicates.

**Cost.** A few words in one step. It costs no dispatch and adds no machinery. It is a drafting rule.

**Risk.** Medium-high confidence, and here is why it is not higher. The absence is proved by the grep above, the step it targets provably makes a form-free choice today, and sage's own corpus records the predicted failure as a measured incident. Against it: nobody has run the changed step, so nobody knows whether the clause changes what a promotion pass writes. That is item 1's question, and item 1 cannot answer it yet. Superpowers' measurement was also taken on dispatch-prompt guidance, not on skill-corpus clauses, so it transfers by analogy.

---

### 15. Extract a brief to a file with a script, rather than composing it per run

**Change this file:** `~/.claude/skills/sage/bin/` → add one new script. The directory holds three scripts today and none of them writes a file.
**Also change:** `references/dispatch.md` → `## Task brief` (line 7), to point at the script, because a tool nothing names is a tool nothing runs.

**What is wrong today.** Sage's `bin/` holds `sage-alt-guard.sh`, `sage-lint.sh` and `sage-watch.sh`. Each is a guard, a linter or a sensor, and each states in its own header that it never writes a file. `sage-alt-guard.sh:8` reads "It never writes a file, never touches a transcript, and denies nothing else." Nothing in sage composes a brief file or a review package. Every run pastes its brief together in the parent's own context instead.

**Be precise about the size of this gap. It is mechanisation, not doctrine.** Sage already states the principle, at `SKILL.md:130`: "**Hand off via artifacts, never via transcript.** Everything you paste into a dispatch — and everything it prints back — stays resident in your context and is re-read every later turn". That is near word-for-word `skills/subagent-driven-development/SKILL.md:231-233`: "Everything you paste into a dispatch prompt — and everything a subagent prints back — stays resident in your context for the rest of the session and is re-read on every later turn. Hand artifacts over as files." Both systems agree on what to do. Only one of them ships a tool that does it. Do not read this item as sage lacking the rule. It has the rule and no instrument.

**What to change.** Write one script in `sage/bin/` that takes a plan or ledger file and a unit identifier, extracts that unit's brief into its own file, and prints the path. Then name it in `references/dispatch.md` `## Task brief`, so the contract that defines the brief's thirteen fields also says how the file gets made.

**Where the idea comes from.** Superpowers ships three executables at `skills/subagent-driven-development/scripts/`, all of them small.

- `task-brief` extracts one task's text into a file. Its own purpose line, at `scripts/task-brief:2-4`, states the reason: "Extract one task's full text from an implementation plan into a file the implementer reads in one call, so the task text never has to be pasted through the controller's context."
- `review-package` writes the commit list, the stat summary and the diff into one file. At `scripts/review-package:2-5`: "Generate a review package: commit list, stat summary, and the net diff with extended context, written to a file the reviewer reads in one call." The skill binds the effect at `skills/subagent-driven-development/SKILL.md:320-322`: "The output never enters your own context, and the reviewer sees the commit list, stat summary, and full diff with context in one Read call."
- `sdd-workspace` resolves the plan-scoped directory the other two write into.

**How this differs from item 6.** Item 6 attacks the same problem with a prose template. A script enforces what a template only asks for. That is the same argument item 6 makes against itself, when it prefers `bin/sage-alt-guard.sh` to a written rule. The two items are not rivals. Item 6's template is what this script would fill in.

**One consequence to name.** Such a script would be the first file in `sage/bin/` that writes an artifact, so it changes what that directory is. New `bin/` files also fall under the promotion skill's stage zero, which now owns them: "**`bin/*.sh` is on the writes list above, and it was on neither list before.**… Stage zero owns them now." (`sage-promote/SKILL.md:32`).

**Cost.** One small script and one line in the Task brief contract. Superpowers' three scripts are 41, 46 and 40 lines. Expect the same order.

**Risk.** Medium-high confidence. The gap is real and the citations are exact. Against it: sage's brief is composed from a plan whose shape varies more than superpowers' numbered task list, so the extraction may be harder to make deterministic. A script that cannot find the unit must fail loudly rather than print an empty brief.

---

## What sage should decline

**Ambient invocation.** Superpowers' bootstrap hook is its single best idea and the wrong one for sage. Its `hooks/hooks.json` registers a `SessionStart` hook, and `CLAUDE.md:76` says the skills are "dead weight" without it. Superpowers' workflow costs little next to writing the code. Sage's fan-out costs 4-15× a chat turn by its own cited telemetry (`SKILL.md:25`). So `disable-model-invocation: true` is correct, and the worker descriptions that push ordinary work away are the right shape.

**One reviewer instead of N.** Superpowers merged two reviewers into one and measured a win. Two caveats change what that number means, and both must be carried.

The measured comparison is `docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:54-59`. Iteration 2 came in at 47.5 minutes against 68.2 minutes. But 68.2 minutes is the previous iteration of the same campaign, not an untouched baseline. And that same iteration also changed the implementer's test-running policy, so implementers ran the focused test while iterating and the full suite once before commit. The measured win belongs to the iteration as a whole, not to the reviewer merge alone.

Two further points stand on their own. Superpowers merged two mandates onto one reading of one diff. It did not merge two lenses on different corpora. And sage's disjoint-mandate rule has its own evidence: across every multi-lens run logged, each lens's find-set has been substantially its own. Where two lenses did construct the same finding, it was one or two findings out of a larger set, never the set itself (`SKILL.md:193`). No run count is given here, on purpose. Sage's own memory records that this count was stated wrongly and corrected twice (`memory/local-archive.md:128`, `:156`), so the rule is carried without one. The decisive finding was repeatedly visible to only one lens. Where two lenses did converge, sage read the convergence as its strongest available signal rather than as waste, and `SKILL.md:199` states that reading.

Do not import the merge. Do import the question. Sage has never run its coordination check as an experiment with a lens removed, and it should.

**Same-mandate competitive reviewers.** Superpowers dispatches two reviewers with the identical mandate and scores them against each other (`docs/superpowers/plans/2026-05-06-lift-drill-into-evals.md:1213-1220`). That contradicts sage's rule that a second reviewer on the same mandate buys redundancy while a second on a different mandate buys coverage (`SKILL.md:193`). Take the scoring clause from item 5 and leave the duplication. Note that this practice also lives in a plan document rather than in a shipped skill.

**Deleting the run's workspace at the end.** Superpowers deletes the plan workspace when the plan completes, "the git history is the record now" (`skills/subagent-driven-development/SKILL.md:482-485`). Sage's ledger must outlive its session. `/sage report` renders from a later session, the snapshot baseline has to survive, and the memory append reads the actuals back.

Superpowers does have a durability requirement. The paragraph immediately before the deletion, at `:473-480`, requires an exhaustive export of every ruling into the final message before anything is deleted. Superpowers satisfies durability with git plus that mandatory export, rather than by keeping the workspace. The decline still stands, because sage's ledger must be re-readable as a file. But the export is the transferable half of superpowers' practice, and item 10 is where it lands.

**The register.** ALL-CAPS imperatives, `<EXTREMELY-IMPORTANT>` tags, "your human partner", and banning the word "thanks" in review replies. All four are real and deliberate in superpowers. They are tuned for a corpus that must bind weaker models across about ten harness integrations with no author present. Sage's reader is one strong model on one harness. Sage's `(calibration: established | recurring | provisional)` tags do something the imperative register cannot: they let one rule be traded off against another under budget pressure (`SKILL.md:95`). Sage should keep its own voice.

---

## Already in sage — do not propose these again

This section exists so nobody spends a study round rediscovering these. Each item is a superpowers feature that sage already has, with the place it lives. If you are comparing the two systems again, check here first.

- **Per-agent cost accounting from the session transcript.** Superpowers has `tests/claude-code/analyze-token-usage.py`. Sage has `bin/sage-watch.sh --status`, which reads deduplicated per-unit spend and occupancy off the same transcripts. `SKILL.md:166` requires reading it at every bring-current point.
- **A ledger with an identity line that survives compaction.** Sage's ledger header comment carries the parent transcript path, the handover threshold, the generation and the role (`references/dispatch.md:93`). `bin/sage-lint.sh` checks the record's integrity at every bring-current point and again at Step 6.
- **A no-nested-subagents contract.** Sage enforces it rather than asking for it. Four of five saved agents omit the Agent tool from their `tools:` line, and `orchestrator` carries it only because it is the handover successor. Superpowers asks for the same thing in prompt text, at `skills/subagent-driven-development/SKILL.md:272-278`.

Batching is not on this list. Sage has the batching instruction but not the check that makes it safe, so it is item 13.

---

## If you only do three

Do items 1, 2 and 3: the control arm, the form classifier, and turn count in model placement.

They share one property the others do not. Each makes machinery sage already owns produce evidence it does not produce today. The blind behavioural lens becomes a measurement instead of an observation. The corpus gets a rule about its own shape, in a system that is almost entirely corpus. The tier table gets the second axis that its own run rows already hint at.

Item 3 is also the best-evidenced item here, and the cheapest. It is one paragraph in each of two files.

The other twelve are worth doing. None of them changes what sage can know about itself.

For scale, sage's most-confirmed mechanism is the refuter aimed at the parent's own work. It has paid on all eighteen logged dispatches (`memory/local-archive.md:153`, `:156`). `SKILL.md:196` already states it in that form, as paying on "every dispatch logged". Nothing on this list has evidence of that strength behind it, and no item above should be read as if it did.
