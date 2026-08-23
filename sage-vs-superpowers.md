# Sage vs Superpowers: a detailed comparison

## What this document is

This document compares two systems that direct AI coding agents. One is `superpowers`, a public plugin. The other is `sage`, a private skill built in this repository. The owner of this repository wrote the document. It was first written on 2026-08-21 and corrected on 2026-08-22 against both systems' source files. Read it to see where two independent designs agree, where they differ, and what each one measured. Every number carries the date it was measured. Where a claim could not be checked, the text says so.

This document cites sage's memory files by line number. Those files are live. They are local to one machine. A periodic consolidation pass rewrites them and moves older detail into `memory/local-archive.md`. The line numbers here are correct as of 2026-08-22, and they will drift.

## Words used in this document

| Term | Meaning |
|---|---|
| Claude Code | A command-line program that runs an AI coding assistant in a terminal. |
| harness | The program that runs the AI assistant. Claude Code is one harness. Other vendors have their own. |
| skill | A folder of written instructions that an assistant loads when a task matches it. A skill changes how the assistant works. It is text, not code that runs. |
| plugin | A bundle that holds several skills, and can also hold scripts and hooks. |
| subagent | A second copy of the assistant, started by the first one. It begins with no memory of the conversation. It gets only the instructions it is handed. |
| dispatch | To start a subagent and give it a task. |
| context window | The total amount of text an assistant can hold at one time. Everything it reads and writes fills the window. |
| compaction | What happens when the context window fills. The harness replaces most of the text with a summary, and detail is lost. |
| token | The unit that text is measured and billed in. One token is roughly three quarters of a word. |
| hook | A script the harness runs automatically at a set moment, such as the start of a session. |
| ledger | A file that records what a run did, so the record survives compaction. |
| orchestration | One assistant splitting work across several subagents and combining their results. |
| superpowers | The plugin studied here. Written by Jesse Vincent. Public and widely installed. |
| sage | The skill studied here. Written by the owner of this repository. Used on one machine. |
| controller | In superpowers, the assistant that runs the plan and dispatches every subagent. It plans, dispatches and decides. It never edits code itself. |
| parent | In sage, the assistant that runs the task and dispatches every subagent. The same role as superpowers' controller. |
| topology | A named pattern for splitting work across subagents. For example, several subagents on one question, or a chain of subagents in order. Sage keeps eleven of them in `references/topologies.md`. |
| lens | One reviewer subagent with one narrow job. Several lenses read the same work looking for different faults. |
| refuter | A subagent told to attack a piece of work and prove it wrong, rather than to confirm it. |
| mandate | The one job a reviewer is told to do. Two reviewers have disjoint mandates when their jobs do not overlap. |
| eval | A repeatable, measured test of assistant behaviour. It runs a real session and scores the result against a baseline. |
| worktree | A second checked-out copy of a git repository. Work in one worktree does not disturb another. |
| write lease | A list of file paths that one subagent is allowed to change. It may change nothing else. |
| band | In sage, a recorded cost range for a kind of work, with a count of how many runs support it. |
| falsifier | A written statement of what a later run would observe if a rule were wrong. |
| VCS | Version control system. Software that records every change to a set of files, so any earlier state can be recovered. Git is one. |
| opus, sonnet, haiku | Names of three Claude models of different strength and price. `haiku` is the fastest and cheapest. `sonnet` is the middle one. `opus` is the strongest and the dearest. |
| N=5 | How many times a measurement was repeated. `N=5` means five repeats. `N=1` means one observation only, which is a hint and not a reliable average. |
| tmux | A terminal program that keeps several command-line sessions running at once, and lets a person attach to any of them. |
| JSONL | A file format. It holds one JSON record per line. |
| PreToolUse | A kind of hook. The harness runs it just before a tool call, and it can block that call before it happens. |
| maxTurns | A limit on how many steps a subagent may take before the harness stops it. It is the only per-unit budget limit a saved agent file can set. |
| micro-test | A small experiment on one piece of wording. It runs the same prompt several times, with and without the wording, and counts the difference. |

---

**What is being compared.** The first system is `superpowers` v6.3.0, commit `b36e082`, released 2026-08-12 (`RELEASE-NOTES.md:3`). It is a fourteen-skill plugin by Jesse Vincent and Prime Radiant. Anthropic's official marketplace distributes it (`README.md:55`). It runs on thirteen coding-agent harnesses (`README.md:53-260`). The second system is `sage`. It is a single orchestration skill installed at `~/.claude/skills/sage/`. It was built in this repository and runs manually through the `/sage` command (`SKILL.md:14`). It ships five saved agent roles, three shell scripts, and a two-file memory (`SKILL.md:149`, `:327-329`).

**A warning about the frame.** These are not competitors. Superpowers is a *development workflow*. It decides how a human and an agent build software together, from idea to merged branch. Sage is an *orchestration engine*. It decides how one task gets split across models, checked against evidence, and recorded. Their overlap is real and instructive. That overlap covers subagents, review, context isolation, and cost. About half of each system has no counterpart in the other. Where a dimension is genuinely one-sided, this document says so. It does not invent a comparison.

---

## 1. At a glance

| | **superpowers** | **sage** |
|---|---|---|
| **Shape** | 14 skills + hook + templates + scripts + tests | 1 skill + 4 references + 5 agents + 3 shell scripts (2 probes and 1 hook) + 2 memory files |
| **Size** | 43,072 words in `skills/`; 170,060 words in all tracked Markdown. Measured at `b36e082`. | 43,256 words across `SKILL.md`, `references/`, `memory/` and the five agent files. 57,137 words with the three `bin/` scripts. Both measured 2026-08-21 22:01. Re-measured 2026-08-22: 47,506 and 61,399. |
| **Trigger** | automatic, on every session, through a `SessionStart` hook (`hooks/hooks.json:3`) | manual only. `disable-model-invocation: true` is set. It runs on `/sage`. (`SKILL.md:5`) |
| **Scope** | the whole software-development lifecycle | one task, split and dispatched |
| **Human role** | in the loop by design. A hard approval gate comes before any code. (`skills/brainstorming/SKILL.md:14-19`) | out of the loop by design. One invocation, then no further input. (`SKILL.md:10`) |
| **Primary artifact** | a finished branch plus its git history. The human chooses to merge it, open a pull request, or leave it in place (`skills/finishing-a-development-branch/SKILL.md:60-64`). The `progress.md` ledger is scratch and is deleted on success. | a `sage-ledger-<session>.md` file, and the deliverable in prose (`references/dispatch.md:89`) |
| **Topology** | one, executed extremely well: plan → per-task implement → review → fix → final review (`skills/subagent-driven-development/SKILL.md:8`) | eleven, chosen by risk: sweep, bake-off, pipeline, loop-until-dry, adversarial verification, blind suite, plan critic, and four more (`references/topologies.md:5-69`) |
| **Unit of work** | one plan task (`skills/writing-plans/SKILL.md:38`). Since v6.3.0, one dispatch may batch several small tasks of the same shape. | one unit that passes a five-part safety test and a four-part worth test (`SKILL.md:59-72`) |
| **Model policy** | "least powerful model that can handle each role" (`skills/subagent-driven-development/SKILL.md:186`); "turn count beats token price" | a tier table (fast, standard, frontier, apex) resolved to a named model at plan time (`SKILL.md:138-145`) |
| **Review** | two mandatory verdicts (spec and quality) from one reviewer per task (`skills/subagent-driven-development/SKILL.md:312`) | disjoint mandates across N lenses, plus a refuter pointed at the parent's own work (`SKILL.md:193`, `:196`) |
| **Cost control** | measured in dollars and minutes against a real eval harness | a 4× budget rail on the run's own estimate, at three scopes (`SKILL.md:253-257`) |
| **Learning** | eval campaigns, design specs, release notes | a per-run memory append, confirmation counts, promotion triggers, and a separate `/sage-promote` skill |
| **Portability** | thirteen harnesses, a porting doctrine, tool-name abstraction (`docs/porting-to-a-new-harness.md:59`) | Claude Code only. Its `harness.md` is full of Claude-Code-specific measurements. (`references/harness.md:1`) |
| **Audience** | reported at about 900,000 installs. This document could not verify that number. A public repository with a contribution policy. | one author, one machine. Its source is committed. Its machine memory is not in the repository, by design. |
| **Evidence** | real tmux sessions, an LLM verifier, N=5 minimum, blind-judged scores | 22 logged runs as of 2026-08-21, and 29 as of 2026-08-22. Each row carries estimate against actual. There is also a watch list and a shared rule set with bands. |

Two notes on the sage column. Sage calls its memory a two-file memory, and this table follows sage's own words. A third real file exists, `local-archive.md`. The consolidation pass writes it, and run-log rows cite it (`references/memory.md:89`). Also, the word counts above were exact when taken. The corpus grew over the following day.

---

## 2. Where they converge, and why that matters

Two systems were built independently, for different purposes. They reached the same conclusion on nine points. Convergence between independent designs is the strongest evidence either one offers. Neither copied the other.

**1. Subagents are context control first, parallelism second.** Superpowers says: "They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work." (`skills/dispatching-parallel-agents/SKILL.md:10`) Sage says: "It keeps noisy exploration, logs, or bulk reading out of your context" (`SKILL.md:70`). That is one of only four reasons sage counts delegation as *worth* it (`SKILL.md:69-72`). Sage's topology #7 is named "Quarantined deep read (context protection)" (`references/topologies.md:42`). Sage calls it "the purest use of subagents-as-context-control." (`references/topologies.md:46`)

**2. Hand off through files, never through the transcript.** Superpowers says: "Everything you paste into a dispatch prompt — and everything a subagent prints back — stays resident in your context for the rest of the session and is re-read on every later turn. Hand artifacts over as files." (`skills/subagent-driven-development/SKILL.md:231-233`) Sage says: "**Hand off via artifacts, never via transcript.** Everything you paste into a dispatch — and everything it prints back — stays resident in your context and is re-read every later turn, which is also what drives the parent toward `## Handover`." (`SKILL.md:130`) These two sentences are nearly identical. They were written independently.

**3. The reviewer's value is its clean context, not its capability.** Superpowers gives the reviewer only four things: the brief, the report, the diff, and the constraints (`skills/subagent-driven-development/SKILL.md:325-327`). It bans workers from spawning their own reviewers, so that the review seat stays clean (`skills/subagent-driven-development/task-reviewer-prompt.md:55-62`). Sage says: "A reviewer's value is its clean context, not the head count. It sees what the writer cannot precisely because it never saw the writer's reasoning — so never 'help' one with the rationale or the alternatives weighed." (`SKILL.md:192`)

**4. Never trust a subagent's report.** Superpowers' reviewer prompt says: "Treat the implementer's report as unverified claims about the code… a stated rationale never downgrades a finding's severity." (`skills/subagent-driven-development/task-reviewer-prompt.md:66-71`) Its verification skill carries a table row: "Agent completed → requires VCS diff shows changes → not sufficient: Agent reports 'success'." (`skills/verification-before-completion/SKILL.md:47`) Sage says: "A report is a **claim from an unprivileged source**… Verify load-bearing claims against repository state, tool output, or a second source before acting on them." (`SKILL.md:188`)

**5. Name the model on every dispatch.** Superpowers says: "Always specify the model explicitly when dispatching a subagent. An omitted model inherits your session's model — often the most capable and most expensive — which silently defeats this section." (`skills/subagent-driven-development/SKILL.md:204-206`) Superpowers measured what the lapse costs. Seventeen dispatches inherited opus and added $5 (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:89-90`). Sage says: "**Name every dispatch, and name its model.**… Naming the model keeps a unit from silently inheriting the parent's." (`SKILL.md:131`) Sage goes further. It makes the model a required column in the ledger's unit table (`SKILL.md:106`).

**6. Silent discard is forbidden.** Superpowers says: "Every adjudication is a ledger entry — a silent discard is forbidden" (`skills/subagent-driven-development/SKILL.md:428`). It also says "A roll-up nobody reads is a silent discard" and "A ruling that dies with the workspace was a decision made in secret." (`skills/subagent-driven-development/SKILL.md:364` and `:479`) Sage says: "Log every abandoned disagreement in `### Decisions and deviations`; silent discard is forbidden, and an abandoned disagreement is a surfaced event at Step 6." (`SKILL.md:161`)

**7. Bound the fix loop, then adjudicate.** Do not hope for convergence. Superpowers allows five fix rounds per task (`skills/subagent-driven-development/SKILL.md:373`). Then a breaker fires, and the controller adjudicates each open finding (`skills/subagent-driven-development/SKILL.md:411-419`). Its debugging skill adds a second bound. Three failed fixes mean the architecture is wrong, not the hypothesis (`skills/systematic-debugging/SKILL.md:195`). Sage allows two delegated fix attempts, then the parent works inline (`SKILL.md:40`). Sage adds a rule: "Count signatures, not attempts." (`SKILL.md:161`) An identical failure signature means the loop is stuck, so sage skips straight to the last rung.

**8. State must survive compaction.** Superpowers says: "Conversation memory does not survive compaction. In real sessions, controllers that lost their place have re-dispatched entire completed task sequences — the single most expensive failure observed." (`skills/subagent-driven-development/SKILL.md:131-133`) Sage's ledger exists for the same reason: "A compaction lands mid-run with agents still in flight and discards nearly the whole window" (`references/dispatch.md:89`). Sage then names the five things that read the ledger back afterwards.

**9. Evidence you failed to read is not missing evidence.** Superpowers says: "Evidence you cannot see is not evidence that doesn't exist… Re-running the suite to regenerate what you failed to read is not verification." (`skills/subagent-driven-development/task-reviewer-prompt.md:87-92`) Sage reaches the same place from the other side (`SKILL.md:190`): "Before writing `Awaiting human`, check whether the case is settleable from a unit's **own transcript** […], because a verdict a command decides is measured and one a reviewer reasons to is judged." The bracketed cut removes a source citation only.

The convergence list is long enough to carry a conclusion. **The hard parts of agent orchestration are the same hard parts, whatever you are orchestrating.** Two independent designs found the same nine.

---

## 3. Dimension by dimension

### 3.1 How you get in

**Superpowers is ambient.** A `SessionStart` hook injects the full text of `using-superpowers/SKILL.md` into every session (`hooks/session-start:11`). The hook wraps that text in `<EXTREMELY_IMPORTANT>` (`hooks/session-start:27`). The user does nothing. The project treats this hook as the definition of a working install (`docs/porting-to-a-new-harness.md:53-55`), and ships an acceptance test for it. Send `Let's make a react todo list` in a clean session. The `brainstorming` skill must fire before any code (`CLAUDE.md:78-82`). The contributor guide names four things that are explicitly not integrations. One of them is "Anything that requires the user to opt in to skills per-session." (`CLAUDE.md:88`)

**Sage is deliberately not ambient.** Its frontmatter sets `disable-model-invocation: true` (`SKILL.md:5`). Sage runs only on `/sage` (`SKILL.md:12-16`). Its four saved worker agents *are* globally visible, so they could be auto-delegated to (`SKILL.md:149`). Their descriptions therefore push ordinary work away. The `explorer` description reads: "NOT a general-purpose search agent — for ordinary lookups and codebase questions, use the built-in Explore agent instead." (`~/.claude/agents/explorer.md:3`)

This is the sharpest difference in philosophy between the two systems. Superpowers bets that **a workflow nobody invokes is worthless**. So it makes the workflow unavoidable. It spends its word budget on stopping the agent from talking itself out of the process. Sage bets that **orchestration is expensive and often wrong**. So it makes the user ask for it. It spends its word budget on deciding whether to fan out at all.

Both bets follow from their scopes. Superpowers' workflow is what you want on nearly every coding task. Sage's fan-out is what you want on a minority of tasks. The two bets produce opposite pressures. Superpowers must fight the agent's tendency to skip the process. Sage must fight the agent's tendency to perform the process as ritual. Sage says so outright: "never fan out to look busy… A skill that must always delegate will delegate ritually." (`SKILL.md:29`) Sage also states that **zero subagents is a valid conclusion**. Superpowers has no equivalent escape hatch. It does not need one, because its process is cheap next to the cost of writing the code.

### 3.2 The unit of work, and who decides what a unit is

**Superpowers decides at plan time, by a criterion a human can read.** A task is "the smallest unit that carries its own test cycle and is worth a fresh reviewer's gate… split only where a reviewer could meaningfully reject one task while approving its neighbor." (`skills/writing-plans/SKILL.md:38-43`) The plan's File Structure section locks the split before any task exists (`skills/writing-plans/SKILL.md:25-27`). Each task then carries an **Interfaces block** with Consumes and Produces entries and exact signatures (`skills/writing-plans/SKILL.md:92-96`). That block is the mechanism that lets context-isolated implementers fit together without seeing each other's work.

**Sage decides at dispatch time, by a two-part test applied to each unit.** A unit is *safe* to delegate only if all five conditions hold. It has a bounded deliverable with a one-sentence "done when". It makes useful progress without frequent decisions. Its context can be packaged explicitly. Its result can be falsified from evidence. Its workspace effects are read-only, sequential, or isolated (`SKILL.md:61-65`). A unit is *worth* delegating only if at least one of four benefits is material. Parallelism shortens the real critical path. It keeps bulk reading out of the parent's context. It supplies a genuinely independent view. Or it is a large cohesive unit that deserves a dedicated owner (`SKILL.md:69-72`).

The two systems then split on one specific point. **Superpowers splits by task. Sage warns against exactly that** (`SKILL.md:54`).

> Split by context boundary, not by problem type — where context must not cross, and where you would want to inspect or intervene. The phases of one deliverable belong to one agent: slicing production work into sequential phases handed agent-to-agent loses fidelity at every handoff, and a ten-step job does not need ten units. […] Review and verification stages are the deliberate exception — they exist *because* the handoff drops the writer's context.

That last sentence matters to this comparison. Sage does not object to every handoff. It objects to handing production work along a chain. It treats review handoffs as the case where losing the writer's context is the point.

This is not really a contradiction. The two systems get different inputs. Superpowers' tasks come from a plan written to make them independent and independently testable, with interfaces declared. Sage receives an arbitrary task with no such plan, and has to find the seams itself. Superpowers also reached sage's position from the other direction in v6.3.0, when it added batching. Several small edits of the same shape become ONE dispatch. Superpowers writes: "Reserve one-dispatch-per-task for work that needs its own judgment, its own tests, or its own review surface." (`skills/subagent-driven-development/SKILL.md:228-229`) That is sage's rule, reached by measurement.

### 3.3 Review architecture

This is where the two designs differ most interestingly.

**Superpowers uses one reviewer, two verdicts, per task.** It got there by measurement. It once ran *two* per-task reviewers, one for spec and one for quality. It merged them into one reviewer that reads the diff once and returns both verdicts. On one scenario the merged arm took 47.5 minutes and 15.7M tokens (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:58`). The previous arm took 68.2 minutes and 22.9M tokens (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:48-53`). A blind judge scored the merged arm **9 out of 10** against the pre-campaign baseline's **7** (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:59`).

Two caveats belong with those numbers, and a summary usually loses them. First, 68.2 minutes is the *previous iteration* of the same campaign. It is not the untouched baseline. Second, the iteration that merged the reviewers also changed the implementer's test-running policy (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:54-57`). So the improvement belongs to the whole iteration, not to the merge alone.

The reviewer's discipline lives in `task-reviewer-prompt.md`. That file carries six things: a named-risk scope budget, a test budget, an evidence rule, a defined severity rubric, a plan-mandated tripwire, and a third verdict channel (⚠️ Cannot verify from diff) that routes back to the controller (`skills/subagent-driven-development/task-reviewer-prompt.md:45-169`). A seventh discipline is real but lives elsewhere. The ban on pre-judging findings, with its literal trigger list, is a rule in the controller's own skill text (`skills/subagent-driven-development/SKILL.md:339-344`). It constrains what the controller may write into the prompt. It does not constrain the reviewer.

**Sage uses N reviewers with disjoint mandates, plus a refuter aimed at the parent.** Its governing rule is the opposite trade: "**Disjoint mandates produce disjoint find-sets.** […] A second reviewer on the *same* mandate buys redundancy, a second reviewer on a *different* one buys coverage." (`SKILL.md:193`)

Sage's evidence supports that rule only in a narrow form. In every multi-lens run but one, each lens's find-set was substantially its own. The single overlap was two findings out of a larger set, not the whole set. Sage's own skill text now states the weaker claim, and the run of 2026-08-21 records the exception (`memory/local.md:120`). Sage also records that the decisive finding was repeatedly invisible to every other unit.

Are the two designs in conflict? Partly, and the difference is again a difference in scope. Superpowers merged *two mandates into one reviewer reading one diff*. That is one reading and two verdicts. It is not the same as cutting a lens. Sage's own plan does the same thing where the `diff-review` skill is installed. Its Spec reader and Standards reader become two rows (`SKILL.md:109`). But sage will happily field four to six lenses on a corpus where superpowers fields one reviewer on a diff. Sage's cost record shows why it can afford to. Its lenses read *documents*. Superpowers' evidence comes from tmux sessions.

Sage's own cost band puts a frontier review lens at 50,000 to 95,000 tokens. Two qualifiers belong with that band. It applies to a prose corpus of 10,000 words or less. Its evidence cell reads "3 runs, last 2026-08-06 (seed)", so it is a seed band and not a local measurement (`memory/local.md:25`). Superpowers' per-run dollar figures span $1.31 to $15.76 across the five frozen scenarios (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:69-72`).

Three things sage has that superpowers does not:

- **A refuter pointed at the parent's own work.** Sage says: "Point one adversarial pass at your own work — the fixes, the completion claim, the prose — not only at the artifact you were handed. The fix round is where unsourced confidence enters." (`SKILL.md:196`) Sage's log records this paying on **every dispatch logged**, which was 17 dispatches at the time this document was measured (`memory/local.md:120`). One run is worth naming. Two refuters with disjoint mandates killed the deliverable's headline mechanism, four of its proposals, and two backwards cost conclusions (`memory/local.md:118`).
- **Model diversity between maker and checker, as a stated requirement.** Sage says: "Vary the model across maker and checker, not just the instance — self-preference bias is documented, and a checker from the writer's own family skews positive." (`SKILL.md:195`) Sage defines an "alt lane" of three agent roles for exactly this (`references/harness.md:101`). A `PreToolUse` hook blocks any alt dispatch that carries a `model` parameter, because that parameter would silently defeat the lane (`SKILL.md:329`). One caveat matters. Sage's repository ships no model name for the alt lane. The machine is supposed to supply it (`references/harness.md:107`). The repository carries only `.in` templates whose frontmatter reads `model: __ALT_MODEL__`. Nothing is installed on this machine, and the run log records "no alt lane installed" three times (`memory/local-archive.md:152-157`).
- **A blind acceptance suite.** Its author receives the requirement's *observable consequences* and never the design decisions. Its cases therefore survive a design change. Sage says: "Told that sessions are cookie-based it writes a case asserting a cookie; told nothing it writes a case asserting the user stays signed in on the next page load — only the second survives a design change." (`SKILL.md:127`)

One thing superpowers has that sage mostly does not: **the review prompt is a file. It is versioned, tested, and reused word for word.** Sage states its review contract in prose and asks the parent to compose each brief. Superpowers' four templates are artifacts: `implementer-prompt.md`, `task-reviewer-prompt.md`, `re-review-prompt.md`, and `code-reviewer.md`. They change only under eval evidence, and they cannot drift from run to run (`CLAUDE.md:42`). Sage has one counter-instance. Where the `diff-review` skill is installed, sage prescribes copying its two reader briefs verbatim (`SKILL.md:190`). That is a versioned prompt artifact of exactly the kind sage otherwise lacks.

### 3.4 Verification philosophy

Both systems refuse to take an agent at its word. They differ in what they reach for instead.

**Superpowers reaches for a command.** Its `verification-before-completion` skill is built on one line: "If you haven't run the verification command in this message, you cannot claim it passes." (`skills/verification-before-completion/SKILL.md:20`) A claim-to-evidence table follows (`skills/verification-before-completion/SKILL.md:40-48`). Its test-driven-development skill demands that the RED failure be observed *for the right reason* (`skills/test-driven-development/SKILL.md:113-128`). Its eval system runs deterministic assertions first. It uses an LLM judge only where a deterministic check would produce a false positive (`docs/superpowers/plans/2026-07-15-sdd-fix-loop-redesign.md:1300-1315`).

**Sage reaches for a command too, and states it as a rule:** "**Settle a disagreement with a command, not by model tier and not by majority.**" Sage adds: "When two reports conflict, buy the measurement." (`SKILL.md:200`) Its evidence is a case where reviewers *agreed* that a mechanism claim was inconsistent, and the repair they agreed on was factually backwards. One small unit was sent to read the documentation, and it changed the fix.

Sage adds three refinements that superpowers does not state:

- **Consensus is not evidence, but independent construction is.** Sage says: "Units that independently construct the same specific finding by different routes are strong evidence for it… Agreement that nothing is wrong proves nothing, because two clean contexts can miss the same thing." (`SKILL.md:199`)
- **A criterion can pass literally while the mechanic it describes is broken.** Sage says: "Read each criterion twice: once for what it says, once for what a passing verdict would actually have demonstrated." (`SKILL.md:191`) Its logged instance is concrete. Two lenses measured "every action has >=1 joypad event" and passed it. Only a third asked whether the event actually *matches* (`memory/local.md:109`).
- **A behavioural probe beats a reading lens on protocol text.** A unit was told to *perform* the procedure on a sandbox copy. It caught two defects that no reading lens caught. It cost 21,000 to 32,000 tokens. The reading lenses on the same material cost 81,000 to 93,000 tokens and found neither defect (`memory/local.md:34`). One detail of this story could not be verified. The claim that the probe was "never told the defect history" appears in no band, watch row, or skill sentence. Sage's source says only that the unit was told to perform rather than to read.

Superpowers' equivalent instinct is its pressure test. Do not ask whether the agent understands the rule. Put the agent in a scenario where it wants to break the rule (`skills/writing-skills/testing-skills-with-subagents.md:140`). Sage's blind behavioural lens and superpowers' pressure scenario are the same idea, applied to different subjects. Both *measure the behaviour, not the comprehension*.

Where superpowers is clearly stronger: **it verifies its own skills.** It runs a RED-GREEN-REFACTOR cycle for documentation (`skills/writing-skills/SKILL.md:552-591`). It ships pressure fixtures in the repository. It runs trigger tests that check whether a skill fires at all (`tests/explicit-skill-requests/run-test.sh:5`). It runs micro-tests with a no-guidance control (`skills/writing-skills/SKILL.md:580`). Sage has no equivalent. Sage does audit its own corpus with reader lenses and refuters, genuinely and repeatedly. But it has never run a controlled experiment on its own wording, and it has no baseline arm.

Where sage is stronger: **it checks the parent.** Superpowers' controller is mostly unchecked, but the claim needs narrowing. Nothing reviews the controller's ⚠️ resolutions, its pre-flight rulings, or its final claim. Its parked findings and deferred minor findings *do* reach the final whole-branch reviewer. Superpowers points that reviewer at the ledger's parked and deferred lines "so it can triage which must be fixed before merge" (`skills/subagent-driven-development/SKILL.md:454-456`). Parked lines are exactly the breaker adjudications (`skills/subagent-driven-development/SKILL.md:415-419`). So the adjudicated findings are triaged by a fresh reader. Nothing audits the reasoning behind them. Sage's own log says the parent's fix round is where errors enter. Sage buys a refuter for it at medium risk and above, and has logged a payoff on every such dispatch (`SKILL.md:196`).

### 3.5 Cost

**Superpowers measures cost in dollars and wall-clock time, against real runs.** Its `analyze-token-usage.py` script parses a session and prices it per agent (`tests/claude-code/analyze-token-usage.py:12-70`). Its efficiency claims come with baselines. One scenario ran at 44.4 minutes, 13.4M tokens, and $11.67 against a named baseline (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:69-71`). Superpowers also kept its failures. A hardening pass went from 42.8 minutes to 69.9 minutes at the same judged quality (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:38-42`). It was iterated on rather than shipped.

One superpowers headline needs its full wording. The release notes read: "**While these numbers won't hold on every harness and for every workload**, in our evals, Claude Code and Codex produce similar high-quality results **roughly** twice as fast and while spending almost 50% fewer tokens." (`RELEASE-NOTES.md:127`) Two qualifiers in that sentence are load-bearing. One is the clause saying the numbers do not generalise. The other is the word "roughly". This is also the one efficiency claim in the list that carries no numeric baseline.

**The wait-timeout story runs in this sequence.** At baseline, 67.1% of waits timed out. The first fix arm was documentation-only guidance. It reached 65.1%, which is a null result against 67.1% (`docs/superpowers/plans/2026-07-30-codex-efficiency-fixes.md:663`). A second arm used long waits. It took the rate from 65.1% to 0.0%. That arm was then rejected. It produced silent transcripts of 20 to 38 minutes, which starve human readers and graders. One child agent out of 51 was lost unnoticed (`docs/superpowers/plans/2026-07-30-codex-efficiency-fixes.md:764-767`). Bounded waits with child reconciliation shipped instead (`docs/superpowers/plans/2026-07-30-codex-efficiency-fixes.md:773`). They were adopted for visibility, not for a better timeout rate. This is a case where the best number lost to the more observable design.

**Sage estimates cost before the run and rails against its own estimate.** The budget rail is 4× the plan's total, applied at three scopes: the whole task, one unit, and the agent count. The floors are 500,000 tokens, 150,000 tokens, and 10 agents (`SKILL.md:253-257`). The `memory/local.md` file records estimate against actual on every run (`SKILL.md:232`). It held 22 rows as of 2026-08-21 and 29 rows as of 2026-08-22. The drift is visible in the rows: 3.0× on the worst miss, then 0.82×, 0.94×, and 1.25× on recent ones (`memory/local.md:117-120`).

Each system has one genuine strength here.

Superpowers has **a cost model built from measured turns**. It states one principle sage lacks entirely (`skills/subagent-driven-development/SKILL.md:208-210`):

> **Turn count beats token price.** Wall-clock and context cost scale with how many turns a subagent takes, and the cheapest models routinely take 2-3× the turns on multi-step work — costing more overall.

Sage's tier table places a model by *unit property*. Mechanical work goes to fast, review goes to frontier (`SKILL.md:138-145`). The table never mentions turn count. Sage's own record contains evidence that turn count matters. Its two `explorer` rows came in at 0.67× and 1.02× of estimate while doing bulk reading (`memory/local.md:118`). Bulk reading is the case where a cheap model *does* pay. But only one of the two rows actually ran on haiku. The log records the other as a sonnet override. So the haiku half of this rests on a single row. Sage has never priced the multi-step case. That is the case where cheap models do not pay.

Sage has **a per-unit rail and a projection discipline** that superpowers lacks. Superpowers' cost bounds are all advisory scope limits. They are the five-round fix cap, the model ladder, the reviewer's test budget, the reviewer's named-risk scope budget, one omnibus final fixer, and no second fix wave (`skills/subagent-driven-development/SKILL.md:458-469`). None of them is a rail. Nothing stops a single runaway subagent, because no numeric turn, token, or dollar ceiling exists anywhere in the skills. Sage projects cost before each dispatch. It reads per-unit spend off a probe at every point that brings the ledger current (`SKILL.md:261`). It names which kind of figure it is holding: "A projection built from band midpoints is an **upper bound**, not a forecast" (`SKILL.md:265`).

### 3.6 Autonomy and the human gate

The two systems make opposite choices. Both choices are deliberate. Both systems have moved *toward* autonomy over time.

**Superpowers gates hard at design, then runs free.** The `brainstorming` skill's `<HARD-GATE>` forbids any implementation action until the human approves. It says: "the ceremony scales with the task; the approval gate never does." (`skills/brainstorming/SKILL.md:14-19`) After the gate, `subagent-driven-development` runs continuously: "Do not pause to check in with your human partner between tasks… 'Should I continue?' prompts and progress summaries waste their time." (`skills/subagent-driven-development/SKILL.md:17`)

Version 6.3.0 pushed further, after a measured failure. The rule is **"Rulings, not stalls."** (`skills/subagent-driven-development/SKILL.md:19`) The controller decides conflicts, ambiguities, and plan defects itself. It records `Ruling: <what you decided> — <why> — <what it costs if wrong>` and keeps going (`skills/subagent-driven-development/SKILL.md:23`). The trigger was a real session: "One donated session had sat blocked for almost nine hours on a question the controller could have decided." (`RELEASE-NOTES.md:17`)

**Sage has no gate at all, by construction.** Its rule is "no input after the invocation" (`SKILL.md:10`). It has four rails that *stop the run and ask*. They cover destructive, irreversible, or externally visible actions; more than one writer without worktree isolation; a writer touching a path outside its lease; and the budget rail (`SKILL.md:242-245`).

Compare the two stop lists directly (`skills/subagent-driven-development/SKILL.md:27-31`):

| superpowers' four stops | sage's four rails |
|---|---|
| an irreversible or destructive operation | destructive, irreversible, or externally visible actions |
| a security-sensitive action | *(no separate rail; a security-shaped finding is a surfaced event at Step 6)* |
| a side effect outside this worktree that norms say you ask about (merge, push, publish) | *(same rail as #1)* |
| a plan so broken that every path forward is a guess | *(sage rules and logs instead; its nearest equivalent is the failure ladder's last rung)* |
| — | more than one writer without worktree isolation |
| — | a writer wanting to touch a path outside its lease |
| — | the budget rail |

Superpowers stops on *judgment collapse*. Sage stops on *resource and blast-radius conditions*, and rules on judgment. Neither list dominates. Superpowers is right that a plan with no non-guessing path is a real stop condition. Sage has no equivalent. Sage's failure ladder ends with "the parent takes it inline" (`SKILL.md:161`), which assumes the parent can. Sage is right that two writers in one tree is a stop condition, whatever anyone's confidence. Superpowers handles that case only by convention: "Never dispatch multiple implementation subagents in parallel (conflicts)." (`skills/subagent-driven-development/SKILL.md:282`)

**Both systems record an autonomous decision, and the two mechanisms are nearly identical.** They were invented independently. Superpowers writes `Ruling: <what you decided> — <why> — <what it costs if wrong>`, and collects every ruling at Finish under "Rulings I made" (`skills/subagent-driven-development/SKILL.md:473-475`). Sage keeps an assumption log with four columns: `| assumption | what I chose | what else was plausible | how it would show if wrong |` (`references/dispatch.md:147`). Sage condenses that log to one line in the run record.

Sage's fourth column is stronger. It demands a **falsifier that a later run could observe**, not just a cost (`SKILL.md:112`).

Superpowers' delivery is stronger here. Its rulings are *printed to the human at the end*, unconditionally (`skills/subagent-driven-development/SKILL.md:473-480`). Sage's assumption log lives in the ledger. The condensed line goes into the ledger's `### Run record` (`SKILL.md:208`). It does not go to the user. Only one narrow class of assumption reaches the user. That class is an ambiguity that changed the decomposition. It appears as a surfaced line at Step 6 (`references/dispatch.md:150`). Everything else is readable only on `/sage report`.

### 3.7 State, recovery, and handover

**Superpowers' ledger is `<workspace>/progress.md`** (`skills/subagent-driven-development/SKILL.md:141`). Its first line names the plan file, which is how the controller identifies it (`skills/subagent-driven-development/SKILL.md:148-149`). Completion lines and fix-round lines are appended and never rewritten (`skills/subagent-driven-development/SKILL.md:405-406`). The recovery doctrine is one sentence: "After compaction, trust the ledger and `git log` over your own recollection." (`skills/subagent-driven-development/SKILL.md:152`) The workspace is scoped to one plan, at `.superpowers/sdd/<plan-basename>/` (`skills/subagent-driven-development/SKILL.md:137-138`). It is scoped that way because a shared workspace once accumulated 68 files across three plans and needed two cleanup commits (`docs/superpowers/specs/2026-07-06-sdd-plan-scoped-workspace.md:27-32`). The workspace is deleted when the plan completes: "the git history is the record now." (`skills/subagent-driven-development/SKILL.md:482-484`)

**Sage's ledger is one durable file** at `.claude/plans/sage-ledger-<session>.md` (`references/dispatch.md:89`). It has six sections: Plan, Unit table, Assumption log, Decisions and deviations, Findings and dispositions, and Run record (`references/dispatch.md:101-176`). Nothing prescribes deleting it. Sage states that it is "not written for the user". Five machine consumers read it back. The `/sage report` command renders it from a later session (`SKILL.md:15`).

Three things sage has here that superpowers does not:

- **A machine check on the record itself.** The `sage-lint.sh` script runs at every point that brings the ledger current, and once more at Step 6. A violation it still reports at Step 6 is a surfaced event (`SKILL.md:162`). The script exists because an audit found the safety prose obeyed and the bookkeeping prose dead: "every unit written once, post-hoc, as `reported`… dead dispatches that never entered the unit table." (`SKILL.md:164`)
- **An occupancy sensor and a handover protocol.** The `sage-watch.sh` script reads the parent's own transcript (`SKILL.md:327`). It computes occupancy as `input + cache_creation + cache_read` on the single most recent assistant record (`references/harness.md:209`). It fires one rung at 30% of the window (`SKILL.md:277`). At that point the parent writes a handoff note (`references/dispatch.md:199`). It spawns an `orchestrator` successor at depth 1, and becomes a supervisor (`SKILL.md:281`). Generations are uncapped. "**The budget rail is what bounds the run**." (`SKILL.md:301`)
- **A snapshot protocol with a write lease.** The steps are baseline, write lease, stabilize, freeze, review, triage, new lease, verify. It runs whenever any writer is present, including the parent. The reason is stated plainly: "**`/rewind` will not undo what a subagent wrote**." (`SKILL.md:160`)

Superpowers has none of these three. It does not obviously need the first two. Its controller's context is bounded by design, because task text and diffs never enter it (`skills/subagent-driven-development/SKILL.md:316-320`). Its recovery story is git plus a ledger. But superpowers has no answer at all to a controller that fills its window on a 30-task plan. Its guidance is to hand artifacts over as files, and then hope. Sage measured the number and built a successor mechanism.

Sage's handover is well attested. It has run end to end four times: on 2026-08-20, on 2026-08-21, and twice on 2026-08-22 (`memory/local.md:117-128`). The 2026-08-20 run crossed the threshold at 305,000 tokens. The successor completed 11 fix items and 2 self-initiated improvements at 258,000 tokens. It returned at 18.6% occupancy, having finished rather than run short (`memory/local.md:117`). The 2026-08-21 run reached generation 2, and its successor returned at 26.3% (`memory/local.md:122`).

Superpowers has one recovery idea sage lacks: **the artifact is git.** Its ledger names commits, and commits survive everything (`skills/subagent-driven-development/SKILL.md:434-439`). Sage's snapshot baseline is a recorded revision plus a list of dirty files. That is recovery by reconstruction, not recovery by checkout.

### 3.8 The learning loop, the largest asymmetry

Both systems try to get better over time. They use completely different instruments. This is the dimension where each is most clearly ahead of the other in one direction.

**Superpowers learns through eval campaigns.** A change to behaviour-shaping text requires evidence. The RED run uses the released text, extracted with `git archive` (`docs/superpowers/plans/2026-07-06-sdd-plan-scoped-workspace.md:925`). The GREEN run uses the branch. The minimum is N=5 runs (`docs/superpowers/specs/2026-06-10-strict-cost-sdd-design.md:8`). Scores are blind-judged (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:41`). Claims use ranges rather than point estimates once variance shows (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:79-81`). Negative results are "logged at equal billing" (`docs/superpowers/plans/2026-07-15-sdd-fix-loop-redesign.md:1628-1629`). The contributor policy refuses reformatting pull requests without eval evidence (`CLAUDE.md:42`). Design specs and plans hold 96,609 words. They record what was tried, what the numbers were, and what was rejected. The wider `docs/` tree holds 106,450 words, but that total includes porting guides and harness READMEs that are neither specs nor plans.

**Sage learns through a calibration memory.** Every run appends a row to `memory/local.md` (`SKILL.md:232`). The row carries the estimate, the actual, the agent count, the wall clock, and a lesson a future run can act on (`references/memory.md:160`). Watch-list rows accumulate confirmations. At three confirmations, a **Rules** row that is marked machine-independent becomes eligible for promotion into `memory/shared.md` as a portable rule (`references/memory.md:110`). That rule carries a Qualifier, a Recogniser, a Band, and a **Falsifier** (`references/memory.md:162`). At six confirmations it becomes eligible for skill text, tagged `(calibration: established)` (`references/memory.md:111`). Promotion is never automatic. A run prints a one-line hint and stops. The user runs `/sage-promote` (`references/memory.md:102`).

The asymmetry cuts both ways.

**Superpowers is ahead on measurement.** It runs controlled experiments with baselines and controls. Sage's evidence is observational: run rows, hand-written lessons, and confirmation counts. Sage has never run a no-guidance control on its own wording. It has never measured whether a rule it added changed behaviour. Its own watch list records the gap: "Running unattended is unmeasured against running with a human approving the plan first: no logged row anywhere records an approval answer, a requested change, or a reversed call." (`memory/local.md:66`)

**Sage is ahead on retention and falsifiability.** Superpowers' knowledge lives in prose: release notes, design specs, and skill text. No mechanism says *when a claim should be retired*. The one supersession in its corpus is a hand-struck line, edited manually (`docs/superpowers/specs/2026-06-09-sdd-task-scoped-review-dispatch-design.md:31`). Sage attaches a **Falsifier** to every portable rule. One reads: "three ground-truth-named briefs costing what comparable open-ended briefs cost." (`memory/shared.md:72`) Sage also attaches a **Band** that decays or strengthens with the count. It has an eviction path (`references/memory.md:144`). It has a consolidation pass with two checks, and both must pass or the pass aborts and writes nothing (`references/memory.md:93`). It has structural invariants on its own memory file (`references/memory.md:149-166`), with a checker tested against a red fixture (`memory/local-archive.md:146`).

Sage's loop also has a documented failure, and the failure is instructive. Its `## Rules` table "has never received a NEW row on this machine: seed 11 → live 11… Runs DO write to Rules (counts rise, provenance gains `+ local run`[…]), so the machinery is not dead — the rule SET is frozen." (`memory/local.md:76`) The bracketed cut removes ", `Promoted` cells stamp". The mechanism was repaired on 2026-08-20 (`references/memory.md:155`). The row is deliberately still open. Sage's own rule explains why: "**`settled` requires the artifact to exist, not to be intended.**… a row recording that some table has never gained an entry is settled when an entry lands, not when the code path that could produce one is written." (`references/memory.md:84`) A second pass on 2026-08-22 found the table still at 11 rows. Superpowers has no comparable self-instrumentation, and would have no way to notice the equivalent failure.

### 3.9 Skill-writing craft

Superpowers is a *manual* on this subject. Sage is a *practitioner* of it without a theory.

Superpowers' techniques are stated, tested, and cited. They include TDD for documentation, pressure scenarios that combine three or more pressures, rationalization tables built from verbatim failures, the Iron Law form, "violating the letter is violating the spirit", Red Flags self-checks, Match the Form to the Failure, no nuance clauses, exemption clauses don't scope, micro-testing with a no-guidance control, description-is-triggers-not-workflow, and meta-testing the failing agent (`skills/writing-skills/SKILL.md:135-645`, `skills/writing-skills/testing-skills-with-subagents.md:13-313`).

Sage shows two of these habits without naming them:

- Its compression floor is headed "Never removed under any 'make it shorter'" (`references/memory.md:168-170`). It lists eight things a cut may not remove: the undated anecdote, any number the skill computes with, a rule's qualifier, the literal command, the completion criterion, a precedence sentence, the strength band, and whether a constraint binds or is merely asked for (`references/memory.md:172-179`). It then names **the order in which a rule breaks** when you cut past the floor (`references/memory.md:181`). That is a more precise instrument than anything in superpowers' token-efficiency section, which gives target word counts and compression techniques but no order of breakage (`skills/writing-skills/SKILL.md:213-266`).
- Its `(calibration: established | recurring | provisional)` tags make the strength of every claim visible at the point of use (`SKILL.md:95`). Superpowers has nothing equivalent. Its skill text asserts uniformly.

Sage also keeps a recognising anecdote in its rules. Superpowers does not prescribe that. It lists the narrative anecdote as an anti-pattern (`skills/writing-skills/SKILL.md:595-597`). Section 5 writes this up as the fourth disagreement.

But sage never tests its wording. It has no baseline arm, no pressure scenario, and no trigger test. It has never checked whether a rule it wrote changes what an agent does. Its blind behavioural lens is the closest thing. An agent is told to *perform* a procedure on a sandbox copy. It found two defects that no reading lens found, on two separate runs (`memory/local.md:34`). That is superpowers' pressure test, reached independently. Sage uses it for review, not for authorship.

### 3.10 Distribution, portability, and audience

This is not a fair comparison. It does explain most of the remaining differences.

Superpowers is a public product. It has a 94% pull-request rejection rate (`CLAUDE.md:7`), a contributor policy addressed to AI agents (`CLAUDE.md:1-3`), a marketplace listing, a Discord server, and commercial support (`README.md:45-283`). Its install count is reported at about 900,000. This document could not verify that number. No install count appears anywhere in the repository, and the marketplace listing was outside the scope of this check. Superpowers runs on thirteen harnesses through a porting doctrine. That doctrine's central rule is that skills name **actions**, never tools (`docs/porting-to-a-new-harness.md:59`). Everything about superpowers must survive contact with strangers, weaker models, and harnesses it was not written for. That is why it has trigger tests, a Haiku-variant test (`tests/explicit-skill-requests/run-haiku-test.sh:55`), and platform-neutral prose specifications.

Sage is one author's tool on one machine. Its `harness.md` is a dossier of Claude-Code-specific measurements (`references/harness.md:1`). It records the transcript layout, the sidecar fields, the deduplication ratio distribution across 197 transcripts, the exact `model` enum, and `maxTurns` semantics (`references/harness.md:204`). Those measurements would be worthless on another harness. They are extremely valuable on this one. Sage can afford to be brittle in ways superpowers cannot. It buys precision with that brittleness.

One consequence is worth naming. **Sage's mechanisms are more sophisticated and less portable. Superpowers' are simpler and battle-tested.** Sage's watchdog reads a JSONL transcript layout that a Claude Code release could change tomorrow. Sage's own records already carry five defects in that probe: three invocation defects, one `jq`-portability defect, and one missing-guard defect, as of 2026-08-22 (`memory/local-archive.md:113-115`, `:129`). Four of the five were closed and moved to `memory/local-archive.md`. Superpowers' equivalent guidance is to "wait in bounded stretches […] and reconcile your live children" (`skills/subagent-driven-development/SKILL.md:239-243`). It works anywhere and needs no probe.

---

## 4. Where each is genuinely better

**Superpowers is better at:**

1. **Getting invoked.** The bootstrap hook plus the acceptance test solves the discovery problem. Sage's manual invocation is a deliberate choice. It also means sage never helps anyone who had not already decided to use it.
2. **Knowing whether a change to itself worked.** Real sessions, deterministic gates plus an LLM judge, N=5 minimum, a no-guidance control, blind-judged quality scores, ranges over point estimates, and kept negative results.
3. **Prompt artifacts as versioned files.** Four templates that cannot drift from run to run, and that change only under eval evidence.
4. **Cost measured in the units that bill.** Dollars, minutes, and turns, computed from a real session by a script. It also states one principle sage lacks: turn count beats token price.
5. **The end-to-end development lifecycle.** Brainstorm, worktree, plan, execute, review, finish. That is a complete workflow. Sage has no design phase, no plan format, and no branch-finishing story.
6. **Portability.** A stated contract, three bootstrap shapes, tool-name abstraction, and an acceptance test per harness.
7. **Surfacing decisions to the human.** "Rulings I made" is printed unconditionally at the end. Sage's assumption log stays in the ledger. It reaches the user only where an ambiguity changed the decomposition. Otherwise the user must run `/sage report`.

**Sage is better at:**

1. **Deciding whether to delegate at all.** The safe test and the worth test, the "zero subagents is a valid conclusion" clause (`SKILL.md:29`), and the coordination check that can falsify sage's own premise (`SKILL.md:231`). Superpowers assumes the topology and executes it.
2. **Checking the orchestrator.** The own-work refuter, the split-mandate refuter pair, and maker/checker model diversity. Superpowers reviews its controller only in one narrow way. The final whole-branch reviewer sees the parked and deferred findings and triages them. Nothing audits the controller's reasoning, its ⚠️ resolutions, its pre-flight rulings, or its final claim.
3. **Topology as a choice.** Eleven patterns, picked by risk. Three of them have no superpowers analogue: loop-until-dry for discovery of unknown size, the pre-write plan critic, and the blind acceptance suite (`references/topologies.md:29-69`).
4. **Cost rails rather than cost measurement.** A 4× projection rail at three scopes with floors, checked before every dispatch (`SKILL.md:265`). Superpowers can measure a run's cost afterwards. It cannot stop one.
5. **Context-limit management.** A measured occupancy formula, a sensor, a threshold, a handoff note, a successor protocol, and uncapped chained generations.
6. **Recording the run.** Six ledger sections, a lint that checks them, an assumption log with falsifiers, a residual-bias disclosure with a fixed address, and a rendering command that works from a later session.
7. **Retaining and retiring knowledge.** Bands, confirmation counts, falsifiers, promotion triggers, a consolidation pass that aborts on a failed check, and structural invariants on its own memory.
8. **Stating its own uncertainty.** Sage's corpus is unusually full of sentences like "one observation, not a band" (`SKILL.md:292`), and rules like "**`settled` requires the artifact to exist, not to be intended.**" (`references/memory.md:84`) Superpowers does this in its eval documents and not in its skills.

---

## 5. Four places they directly disagree

**1. Whether to split one deliverable across agents.** Superpowers splits a plan into tasks and gives each task a fresh implementer. Sage warns that "slicing production work into sequential phases handed agent-to-agent loses fidelity at every handoff." (`SKILL.md:54`) Superpowers answers that its tasks are not phases. They are independently testable increments, with declared interfaces and a reviewer gate between them. Sage answers that most tasks it receives have no such plan. **Both are right within their own inputs.** Superpowers' v6.3.0 batching rule shows it moving toward sage's caution where the tasks are small. Sage's own text names review and verification stages as the deliberate exception to its warning.

**2. How many reviewers.** Superpowers merged two reviewers into one and measured a large win. Sage fields four to six lenses with disjoint mandates. In every logged multi-lens run but one, each lens's find-set was substantially its own (`SKILL.md:193`). One run is the exception. Two disjoint lenses independently constructed the same two findings there, out of a larger set (`memory/local.md:120`). Sage read that as evidence in the useful direction rather than as waste. **The reconciliation is that superpowers merged two mandates onto one reading of one diff, while sage adds mandates that read different things.** The genuinely open question is whether sage's lens count would survive superpowers' kind of measurement. That would be a controlled run with lenses removed. Sage has never run it. Its coordination check asks the question honestly and answers it by judgment.

**3. Where the human belongs.** Superpowers puts a hard gate before implementation and nothing after it. Sage puts nothing before and four rails throughout. Superpowers' gate catches the most expensive error class at the cheapest moment. That class is building the wrong thing. Sage's rails catch blast-radius errors at the moment they would occur. **Sage's own watch list concedes the gap.** Whether running unattended is worse than running with an approved plan "is unmeasured" (`memory/local.md:66`). Sage nominates the assumption log as the instrument that would settle it.

**4. Whether a rule should carry a recognising anecdote.** The two systems disagree here.

Superpowers lists the narrative anecdote under `## Anti-Patterns` in its skill-writing skill. The entry reads (`skills/writing-skills/SKILL.md:595-597`):

> ### ❌ Narrative Example
>
> "In session 2025-10-03, we found empty projectDir caused..."
>
> **Why bad:** Too specific, not reusable

Sage makes the anecdote un-cuttable. Its compression floor is headed "Never removed under any 'make it shorter'", and its first item is (`references/memory.md:170-172`):

> The **undated anecdote** that makes a rule recognisable in the wild.

Sage then explains what the cut costs: "the anecdote goes, so the rule has no shape left to match against" (`references/memory.md:181`). That sentence belongs to sage. Superpowers' corpus does not contain it.

Both positions are defensible, and one word narrows the gap. Sage asks for an *undated* anecdote. Superpowers' anti-pattern example is a dated session narrative, and its stated objection is that such a narrative is too specific to reuse. So the two rules are closer than they look, but they still point in opposite directions. Superpowers' skill-writing text pushes the anecdote out. Sage's compression floor forbids removing it.

One more thing is worth stating for fairness. Superpowers' own *practice* uses anecdotes heavily. Its subagent-driven-development skill carries several (`skills/subagent-driven-development/SKILL.md:270`, `:461`). So the disagreement is between sage's rule and superpowers' rule, not between sage's rule and superpowers' behaviour.

---

## 6. Summary judgment

Superpowers is a **mature, publicly tested workflow product**. Its central achievements are three. It solved invocation. It treats prompts as tested code. Its execution loop was refined by measurement across the roughly 10 months of releases its notes record. Those releases run from v2.0.1 on 2025-10-12 to v6.3.0 on 2026-08-12 (`RELEASE-NOTES.md:3` and `:1160`). Its weaknesses are three as well. Its controller's reasoning is unaudited, although the final whole-branch reviewer does triage its parked and deferred findings. Its cost bounds are advisory scope limits, not rails. Its knowledge has no retirement mechanism.

Sage is a **research-grade orchestration engine**. Its central achievements are three. It decides whether to orchestrate at all. It verifies the orchestrator rather than only the work. Its memory loop carries falsifiers and bands. Its weaknesses are three as well. It has never measured itself the way superpowers measures itself. It runs on one harness. And several of its most interesting mechanisms have little or no evidence behind them. `/sage report` and `/sage resume` have no logged runs at all (`memory/local.md:80`). The alt lane is a sharper case. It has three logged dispatches and no valid result from any of them. All three passed a `model` parameter, which silently replaced the outside-family model the lane exists for, so 22.4k tokens bought three dispatches that tested nothing (`references/harness.md:121-124`). Handover is the exception: it now has four end-to-end runs, on 2026-08-20, 2026-08-21, and twice on 2026-08-22 (`memory/local.md:117-128`).

The most useful sentence in this comparison is probably this one. **The two systems' strongest ideas are almost perfectly complementary.** Superpowers knows how to find out whether a piece of agent-shaping text works. Sage knows how to decide what to delegate, and how to check the thing doing the delegating. Each has what the other lacks. Neither gap is intrinsic to its design.

The third document in this set is `sage-learns-from-superpowers.md`. It takes that conclusion seriously and proposes what sage should actually adopt.
