# Superpowers: a complete anatomy

## What this document is

This document describes one software product: the `superpowers` plugin. The plugin adds a set of written work instructions to an AI coding assistant. The document covers what the plugin contains, how it starts itself, how it runs work through helper agents, how its author tests it, and where its evidence is thin.

The owner of this repository wrote it in August 2026, after reading the plugin's source code. Three separate fact-check passes then checked every claim in it against the source.

Read it as a study of one design, not as a recommendation. Numbers in it come from the plugin's own design documents unless the text says otherwise. Where a claim could not be checked, the text says so.

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
| controller | In superpowers, the assistant that runs the plan and dispatches every subagent. It plans, dispatches and decides. It never edits code itself. |
| implementer | A subagent that writes the code for one task. |
| reviewer | A subagent that reads a code change and reports faults. It does not change the code. |
| brief | In superpowers, a file holding the full text of one task. A subagent reads it instead of the whole plan. |
| worktree | A second checked-out copy of a git repository. Work in one worktree does not disturb another. |
| SDD | `subagent-driven-development`, the plugin's largest skill. It runs a plan through fresh subagents. |
| RED / GREEN | Two stages of test-driven development. RED means the test fails before the code exists. GREEN means the code makes it pass. |
| eval | A repeatable, measured test of assistant behaviour. It runs a real session and scores the result against a baseline. |
| drill | The program that runs the plugin's behaviour evals. It lives in its own repository. |
| pressure test | A scenario written to make an assistant want to break a rule, used to test whether a skill holds. |
| rationalization table | A two-column table. The left column holds an excuse an assistant makes. The right column refutes it. |
| adjudication | A decision the controller makes on a review finding when the fix loop reaches its limit. |
| YAGNI | Short for "you are not going to need it". A rule that says do not build a thing until you actually need it. |
| VCS | Version control system. Software that records every change to a set of files, so any earlier state can be recovered. Git is one. |
| opus, sonnet, haiku | Names of three Claude models of different strength and price. `haiku` is the fastest and cheapest. `sonnet` is the middle one. `opus` is the strongest and the dearest. |
| N=5 | How many times a measurement was repeated. `N=5` means five repeats. |
| tmux | A terminal program that keeps several command-line sessions running at once, and lets a person attach to any of them. |
| awk | A small command-line program for picking fields out of lines of text. |
| JSONL | A file format. It holds one JSON record per line. |
| micro-test | A small experiment on one piece of wording. It runs the same prompt several times, with and without the wording, and counts the difference. |

---

**Subject:** the `superpowers` plugin for Claude Code and twelve other coding-agent harnesses.
**Version studied:** v6.3.0, commit `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` (2026-08-12), cloned from `https://github.com/obra/superpowers.git` on 2026-08-21.
**Author:** Jesse Vincent (GitHub `obra`), with Prime Radiant. MIT licensed.
**Scale:** 194 files, ~170,060 words of markdown. `skills/` is 43,072 words. `docs/`, which holds design specifications and plans, is 106,450 words. A re-check of the clone on 2026-08-22 confirmed every one of these counts.

> A note on version. Anthropic's official marketplace catalog on the machine where this was written pins superpowers at **v6.1.1** (`d884ae0`). This claim could not be checked. The local catalog is not on disk in the clone used for verification, so no fact-check could confirm or refute it. The clone studied here is the repository's current HEAD, **v6.3.0**, and `.claude-plugin/plugin.json` confirms that version number. Where the two versions differ, this document describes 6.3.0 and says so.

---

## 1. What it actually is

Superpowers is not a skill. It is a **plugin containing fourteen skills**. It also ships a session-start hook, a set of subagent prompt templates, ten shell scripts, a test harness, and a written doctrine for running the whole thing on other vendors' agents.

Three of the ten shell scripts do the file handoff inside `subagent-driven-development`. Section 5.3 describes those three. The other seven are `scripts/bump-version.sh`, `scripts/lint-shell.sh`, `scripts/package-codex-plugin.sh`, `scripts/sync-to-codex-plugin.sh`, the two brainstorming server scripts under `skills/brainstorming/scripts/`, and `skills/systematic-debugging/find-polluter.sh`. Test scripts are not counted here.

The fourteen skills, with their exact `SKILL.md` word counts:

| Skill | Words | What it governs |
|---|---:|---|
| `using-superpowers` | 485 | the bootstrap: how and when to invoke any skill at all |
| `brainstorming` | 2,324 | turning an idea into an approved design before any code |
| `writing-plans` | 1,059 | turning a design into a task-by-task implementation plan |
| `subagent-driven-development` | 4,825 | executing that plan through fresh subagents with review gates |
| `executing-plans` | 344 | the fallback executor for harnesses without subagents |
| `test-driven-development` | 1,375 | RED-GREEN-REFACTOR, enforced |
| `systematic-debugging` | 1,440 | four-phase root-cause process |
| `verification-before-completion` | 580 | no completion claim without fresh evidence |
| `requesting-code-review` | 421 | dispatching a reviewer subagent |
| `receiving-code-review` | 913 | how to respond to review feedback |
| `dispatching-parallel-agents` | 865 | concurrent subagents on independent problems |
| `using-git-worktrees` | 1,069 | isolated workspace, detected before created |
| `finishing-a-development-branch` | 1,269 | merge / PR / keep, and worktree cleanup |
| `writing-skills` | 3,779 | how to author and test a skill |

Total: 20,748 words of `SKILL.md`. `skills/` holds roughly 22,000 more words of supporting reference files, prompt templates and examples.

The project's own summary of what it offers is in `README.md:33-43`. The quotations below come from lines 35, 39 and 41 of that file, so they are three separate fragments and not one continuous passage. The agent "*doesn't* just jump into trying to write code." It teases a specification out of the conversation and shows it in readable chunks. It then writes a plan "clear enough for an enthusiastic junior engineer with poor taste, no judgement, no project context, and an aversion to testing to follow." After that it runs subagent-driven development. The section closes: "It's not uncommon for your agent to work autonomously for a couple hours at a time without deviating from the plan you put together."

---

## 2. The load-bearing trick: automatic bootstrap injection

Everything else depends on one mechanism. A skill that must be *discovered* does not get used. Superpowers makes one skill unavoidable, and that skill recruits the rest.

`hooks/hooks.json` registers a `SessionStart` hook matching `startup|clear|compact`. The block below is an **excerpt**. The real file wraps everything in a top-level `"hooks": { … }` object, and the command entry also carries `"shell": "bash"` and `"async": false`:

```json
"SessionStart": [{"matcher": "startup|clear|compact", "hooks": [
  {"type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" session-start"}
]}]
```

`hooks/session-start` reads the entire text of `skills/using-superpowers/SKILL.md`. It then escapes that text for JSON in five substitution passes, for `\\`, `"`, newline, carriage return and tab. It emits the result as session context, wrapped like this:

```
<EXTREMELY_IMPORTANT>
You have superpowers.

**Below is the full content of your 'superpowers:using-superpowers' skill - your introduction
to using skills. For all other skills, use the 'Skill' tool:**

[SKILL.md content]
</EXTREMELY_IMPORTANT>
```

The hook detects which harness it runs under and picks the right JSON key. It uses `additional_context` for Cursor, `hookSpecificOutput.additionalContext` for Claude Code, and plain `additionalContext` for Copilot CLI.

`hooks/run-hook.cmd` is a **polyglot bash/batch file**. That means one file that both `cmd.exe` and a POSIX shell can execute. On Windows, the batch section finds Git Bash and calls it again. On Unix, the line `: << 'CMDBLOCK'` neutralises the batch block, and the script runs `exec bash` directly. This is why Windows support needs one file rather than a second parallel implementation.

**Why this matters more than any individual skill.** The contributor guidelines make bootstrap injection the *definition* of a real integration (`CLAUDE.md:72-91`):

> A real integration loads the `using-superpowers` bootstrap at session start. The bootstrap is what causes skills to auto-trigger at the right moments. Without it, the skills are dead weight — present on disk but never invoked.

The project also ships an acceptance test for this. Open a clean session. Send exactly `Let's make a react todo list`. Paste the complete transcript in the pull request. A working integration triggers `brainstorming` on its own before any code is written. The same document names four things that are *not* real integrations: copying skill files by hand, `npx skills`-style runtime shims, anything that needs the user to opt in each session, and anything where `brainstorming` does not fire on that prompt.

One measured design detail. On the in-process harnesses, the bootstrap goes in as a **user message, not a system message**. See `.opencode/plugins/superpowers.js:118-119` and `.pi/extensions/superpowers.ts:42-45`. The stated reasons are two. A system message repeated every turn wastes tokens (issue #750). Multiple system messages break Qwen and some other models (issue #894). The text is also cached at module level, so it is not read and parsed again on every agent step.

---

## 3. The entry skill: `using-superpowers`

485 words that do four things.

**A compliance clause with no negotiating room:**

```
<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing,
you ABSOLUTELY MUST invoke the skill.

IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>
```

**A rule that fires earlier than instinct.** The agent must invoke skills *before any response or action*. That includes clarifying questions, exploring the codebase, and checking files.

**A twelve-row Red Flags table** that names a thought and refutes it. Five of the twelve rows:

| Thought | Reality |
|---|---|
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I remember this skill" | Skills evolve. Read current version. |
| "The skill is overkill" | Simple things become complex. Use it. |

**A `<SUBAGENT-STOP>` gate at the very top.** It reads: "If you were dispatched as a subagent to execute a specific task, ignore this skill." Without this gate, every dispatched subagent would re-enter the whole workflow machinery. That recursion would make subagent-driven development impossible.

The skill also sets skill precedence, so process skills come before implementation skills. It states the instruction hierarchy too. User instructions, which means `CLAUDE.md` and direct requests, override skills. Skills override default behaviour.

---

## 4. The workflow spine

Nine skills chain into one pipeline. Some of them name the next skill directly. Others do not.

```
brainstorming  →  writing-plans
      →  subagent-driven-development (or executing-plans)
      →  using-git-worktrees (named at execution time, inside the executor)
      →  [ per task: test-driven-development, requesting-code-review, receiving-code-review ]
      →  finishing-a-development-branch
```

The worktree step sits where the corpus puts it, not between brainstorming and planning. `brainstorming/SKILL.md` contains zero `superpowers:` references and never names `using-git-worktrees`. The worktree skill is named at *execution* time, after the plan exists. See `writing-plans/SKILL.md:16` ("If working in an isolated worktree, it should have been created via the `superpowers:using-git-worktrees` skill at execution time"), `executing-plans/SKILL.md:19`, and `subagent-driven-development/SKILL.md:127`.

**Only two of the nine spine skills carry a literal `REQUIRED SUB-SKILL` marker.** A repository-wide search for that string returns five hits in three files: `skills/executing-plans/SKILL.md:37`, `skills/writing-plans/SKILL.md:61,166,170`, and `skills/writing-skills/SKILL.md:283`. The last of those is an example of good authoring style, not a handoff. So the marked handoffs are `writing-plans` (to `subagent-driven-development` or `executing-plans`) and `executing-plans` (to `finishing-a-development-branch`). The rest name the next skill in ordinary prose, or name no successor at all. Four spine members name no successor skill anywhere in their `SKILL.md`: `using-git-worktrees`, `test-driven-development`, `requesting-code-review` and `receiving-code-review`. `subagent-driven-development/SKILL.md:487` reads plainly "Use superpowers:finishing-a-development-branch." with no marker.

`brainstorming` states its terminal rule in its Process Flow section, at lines 149 to 154. It is not at the end of the file. The rule is scoped to the **architectural** path only. On that path, the rule reads: "the ONLY skill you invoke after brainstorming is writing-plans — never frontend-design, mcp-builder, or any other implementation skill." The other two paths end differently. The bounded path proceeds directly through the normal development workflow, with no plan document. The spike path ends in a reported recommendation. So on two of the three paths `writing-plans` is never invoked at all.

`writing-plans` ends by offering exactly two execution options and naming the skill for each.

### 4.1 `brainstorming` — the approval gate

Its frontmatter description is the only one of the fourteen phrased as a direct obligation rather than as a trigger condition. All fourteen descriptions are in the imperative mood. Thirteen open with the bare imperative "Use when …". Brainstorming's opens with a second-person obligation: *"You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior."*

Its central mechanism is a **hard gate**:

```
<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take
any implementation action until you have told your human partner what you intend and
they have approved it. This applies to EVERY task on EVERY path below — the ceremony
scales with the task; the approval gate never does.
</HARD-GATE>
```

The **three-path router** classifies the request out loud before the first question. It was added in v6.3.0 as a cost fix. Section 9 covers the release practice around it.

- **Spike.** A feasibility question. The output is an answer, not code you keep. Two or three sentences, a nod, then find out as cheaply as correctness allows. No specification, no plan.
- **Bounded.** A well-scoped change to code *that already exists in this repository*. The skill states the test plainly: "Understanding the kind of app is not enough — bounded means the flow you are changing is already here to read." Short design in chat, then STOP for approval. No documents.
- **Architectural.** New projects, new subsystems, interface changes. The full process runs: questions one at a time, two or three approaches with trade-offs, a sectioned design with approval after each section, a written specification at `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`, a self-review, a user review gate, then `writing-plans`.

Two rules make the router honest. The first: **"When in doubt between two paths, take the heavier one."** The second: **"The ratchet is one-way."** Hidden complexity found mid-task upgrades the path. Nothing downgrades mid-task.

The skill has an anti-pattern section titled *"Too Simple To Need Approval"*, at line 54. A separate top-level `## Red Flags` section follows it at line 63, with seven rows. Those rows pre-empt specific excuses. One is subtle: *"It's bounded and the design is obvious — I'll start while they read it"* is answered with *"The gate is the approval, not the design's length. Present, then stop until you hear yes."*

A **visual companion** also ships with the skill. It is a local browser server for mockups and diagrams, with no external dependencies. A just-in-time rule governs it. Never offer it upfront. Offer it the first time a question would genuinely be clearer shown than told. Offer it in its own message with no other content. Then decide **per question** whether that question is visual or textual. The skill states the reason: "A question about a UI topic is not automatically a visual question."

### 4.2 `writing-plans` — plans as executable documents

The framing sentence is: *"assuming the engineer has zero context for our codebase and questionable taste."*

The concrete requirements:

- **A File Structure section before the tasks.** The skill says "This is where decomposition decisions get locked in." Design units with clear boundaries. Files that change together live together. Prefer smaller focused files. The stated reason: "You reason best about code you can hold in context at once, and your edits are more reliable when files are focused."
- **Task right-sizing.** "A task is the smallest unit that carries its own test cycle and is worth a fresh reviewer's gate... split only where a reviewer could meaningfully reject one task while approving its neighbor."
- **Bite-sized steps of two to five minutes each.** Write the failing test. Run it to see it fail. Implement minimally. Run the tests. Commit.
- **A mandatory plan header.** It carries Goal, Architecture, Tech Stack, a pointer to the specification, and a **Global Constraints** block that copies the specification's project-wide requirements word for word. The skill adds: "Every task's requirements implicitly include this section."
- **An Interfaces block per task.** It lists what the task Consumes and what it Produces, with exact signatures. The reason: "A task's implementer sees only their own task; this block is how they learn the names and types neighboring tasks use." This is the mechanism that lets context-isolated implementers still fit together.
- **A No Placeholders rule.** It lists six specific plan failures: "TBD"; "add appropriate error handling"; "write tests for the above" with no test code; "Similar to Task N", because the engineer may read tasks out of order and should get the code repeated; steps with no code blocks; and references to undefined types.
- **A three-item inline self-review.** It checks specification coverage, scans for placeholders, and checks type consistency. The skill's own example: "a function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug". The skill is explicit that this is "a checklist you run yourself — not a subagent dispatch."

### 4.3 `using-git-worktrees` and `finishing-a-development-branch`

`using-git-worktrees` is a study in not fighting the harness. Its order is **detect, then native, then fallback**:

- **Step 0 detects isolation that already exists.** It compares `git rev-parse --git-dir` against `--git-common-dir`. It also carries a **submodule guard**, `git rev-parse --show-superproject-working-tree`. A submodule produces the same inequality, and without the guard the skill would read a submodule as a worktree.
- **Step 1a prefers a native tool.** The skill lists candidates: "It might be a tool with a name like `EnterWorktree`, `WorktreeCreate`, a `/worktree` command, or a `--worktree` flag." The rationalization table calls bypassing it "the #1 mistake — it creates phantom state your harness can't see or manage."
- **Step 1b is the git fallback.** It requires `git check-ignore` verification before creating anything. If the directory is not ignored, it adds the directory to `.gitignore`. The stated reason: "Prevents accidentally committing worktree contents to repository."
- **Consent is required before creating a worktree.** A sandbox permission failure does not raise an error. The skill degrades to working in place and reporting that.

`finishing-a-development-branch` presents **exactly three options**: merge locally, push and open a pull request, or keep as-is. On a detached HEAD it drops to two. Its discipline is in what it refuses to do:

- Discard is not on the menu. It exists only as a response to an explicit request, and the user must type the exact word `discard`.
- The agent never resolves a `git worktree remove` refusal with `--force` on its own initiative. The refusal means files exist nowhere else. So the skill shows the user `git status --porcelain -uall` and offers three choices.
- Cleanup only touches worktrees under `.worktrees/` or `worktrees/`. The skill states: "Everything else belongs to the host."
- Tests run **on the merged result**. A failure there stops everything, and the branch and the worktree stay in place.

### 4.4 `test-driven-development`, `systematic-debugging`, `verification-before-completion`

These three are the discipline skills. They share one structure: an **Iron Law** inside a code fence, a **spirit-versus-letter clause**, a **rationalization table**, and a **Red Flags list**.

**TDD's Iron Law** is `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`. It is followed by "Write code before the test? Delete it. Start over." Four loophole closures follow that: do not keep it as reference, do not adapt it, do not look at it, delete means delete.

Its rationalization table argues rather than asserts. The first quotation below is cut short. The source continues "Test-first forces that failure." after the last quoted word:

> "I'll test after" → "Tests written after pass immediately — which proves nothing. They may test the wrong thing, test the implementation instead of the behavior, or miss the edge case you forgot. You never watched it fail, so you never proved it can catch the bug." …

> "Deleting X hours is wasteful" → "Sunk cost fallacy — that time is already spent either way... Keeping code you can't trust is the waste."

The skill requires the agent to verify RED for the *right reason*: "Fails because feature missing (not typos)". It requires pristine output, with no stray warnings. It routes to `writing-good-tests.md` for four rules that keep tests honest. The two strongest are **"Name the production change that would make the test fail — before writing it"** and **"Assert on real behavior, never on mock behavior"**

**`systematic-debugging`** enforces four phases that the agent may not skip: Root Cause Investigation, then Pattern Analysis, then Hypothesis and Testing, then Implementation. Its distinctive elements:

- **Instrumentation before hypothesis**, in systems with several components. Log what enters and leaves each component boundary. Run once. Let the evidence say which layer fails. The skill gives a worked four-layer example in shell.
- **A single hypothesis rule.** Two bullets state it: "Make the SMALLEST possible change to test hypothesis", and "One variable at a time".
- **A three-strike architectural circuit breaker.** "If ≥ 3 [fixes failed]: STOP and question the architecture... This is NOT a failed hypothesis — this is a wrong architecture." The named pattern is "Each fix reveals new shared state/coupling/problem in different place"
- **A section titled "your human partner's Signals You're Doing It Wrong".** It decodes the user's own phrasing as evidence. *"Is that not happening?"* means you assumed without verifying. *"Stop guessing"* means you are proposing fixes without understanding.

Three supporting techniques ship beside it, in the same directory. **`root-cause-tracing.md`** is a backward-tracing method with a worked five-level trace. It also ships `find-polluter.sh`, a bisection script under the heading "Finding Which Test Causes Pollution". **`defense-in-depth.md`** prescribes validating at four layers: entry point, business logic, environment guard, and debug instrumentation. Its argument is "Single validation: 'We fixed the bug'. Multiple layers: 'We made the bug impossible'". Its reported outcome is that *all four* layers each caught something the others missed. **`condition-based-waiting.md`** is the third. It replaces arbitrary timeouts with polling on a condition.

**`verification-before-completion`** is the smallest of these three skills, and possibly the highest-leverage one in the plugin. At 580 words it is the fourth-smallest skill overall, behind `executing-plans` (344), `requesting-code-review` (421) and `using-superpowers` (485). Its Iron Law is `NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE`, with the gloss "If you haven't run the verification command in this message, you cannot claim it passes." It supplies a five-step gate function and a claim-to-evidence table. The row that matters most for an orchestration system:

| Claim | Requires | Not Sufficient |
|---|---|---|
| Agent completed | VCS diff shows changes | Agent reports "success" |

Its Red Flags include *"Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)"* and *"ANY wording implying success without having run verification"*

### 4.5 `receiving-code-review` — the anti-sycophancy skill

This skill's whole subject is the agent's social behaviour. Its opening overview line is "Code review requires technical evaluation, not emotional performance." Its explicitly labelled **Core principle** is a different sentence, on the next line: "Verify before implementing. Ask before assuming. Technical correctness over social comfort."

It forbids specific strings: "You're absolutely right!", "Great point!", and "Let me implement that now" before verification. It bans **all** gratitude expressions. The reason appears in two separate paragraphs of the source. The first: "**Why no thanks:** Actions speak. Just fix it. The code itself shows you heard the feedback." The second: "**If you catch yourself about to write "Thanks":** DELETE IT. State the fix instead."

The skill prescribes a six-step response pattern: READ, UNDERSTAND, VERIFY, EVALUATE, RESPOND, IMPLEMENT. An unclear item blocks *all* implementation, because "Items may be related. Partial understanding = wrong implementation". It adds a five-check verification gate for external reviewers and a YAGNI check, which means "grep codebase for actual usage" before "implementing properly". It also gives a graceful-correction pattern for when the agent's own pushback was wrong: state it factually, give no long apology, and do not defend why you pushed back.

---

### 4.6 `requesting-code-review` — the request side

This is the companion to 4.5. It is the only skill in the spine whose whole subject is *dispatching* a reviewer. Its Core principle is "Review early, review often."

Review is **mandatory** after each task in subagent-driven development, after a major feature, and before a merge to main. It is **optional but valuable** when stuck, before refactoring, and after fixing a complex bug.

The mechanics are three steps. First, capture `BASE_SHA` and `HEAD_SHA` with `git rev-parse`. Second, dispatch a `general-purpose` subagent that fills the template at `skills/requesting-code-review/code-reviewer.md`, a 5.7KB file. Third, act on what comes back. That template is a different artifact from the SDD task-reviewer prompt that section 5.7 takes apart, although the two share the read-only rule. Four named placeholders carry the whole context: `{DESCRIPTION}`, `{PLAN_OR_REQUIREMENTS}`, `{BASE_SHA}`, `{HEAD_SHA}`.

The act-on rule is defined per severity, not left to judgement. Critical is fixed immediately. Important is fixed before proceeding. Minor is noted for later. Symmetrically with 4.5, the skill also says to "Push back if reviewer is wrong (with reasoning)".

Its two-row rationalization table carries the delegation argument in its plainest form. Reviewing the diff yourself "burns the context window you need to keep driving the work. Dispatch a reviewer subagent: the diff and the evaluation live in its context, and only the findings come back to you." The second row forbids handing the reviewer session history. It asks for "precisely crafted context" instead. That is the same firewall the dispatch contract enforces at 5.4. Its Red Flags ban skipping review because "it's simple", and ban proceeding with unfixed Important issues.

### 4.7 `executing-plans` — the fallback executor

At 344 words this is the shortest skill in the spine. It is also the only skill that opens by naming its own replacement. It tells the agent to tell the human that superpowers "works much better with access to subagents". It lists five entries that qualify: Claude Code, Codex CLI, Codex App, Copilot CLI and Gemini CLI. Those are five install targets but four products, because Codex appears twice. Section 8 merges that pair to reach thirteen harnesses. The skill then says to use `subagent-driven-development` instead, wherever subagents exist.

A skill that routes traffic away from itself is a deliberate authoring choice. It exists so the corpus degrades gracefully on a harness without subagents, instead of losing the workflow in silence.

Its process is four beats. First, make sure an isolated workspace exists: "use superpowers:using-git-worktrees to create one or verify the existing one". That line is an ordinary instruction, not one of the marked handoffs. Second, read the plan and review it *critically*, raising concerns with the human **before** starting. Third, create todos, one per plan item. Fourth, execute each step exactly, and run the verifications the plan specifies. It closes into **REQUIRED SUB-SKILL:** `finishing-a-development-branch`, so the same three-option finish menu from 4.3 governs both execution paths.

It carries explicit stop conditions: a blocker, critical gaps in the plan, an instruction not understood, and repeated verification failure. The governing rule is "Ask for clarification rather than guessing". It adds a revisit rule for when the partner updates the plan, or when the approach needs rethinking. Its last line is a hard boundary: "Never start implementation on main/master branch without explicit user consent"

---

## 5. The subagent architecture

`subagent-driven-development` is the largest skill by word count, at 4,825 words. It is the project's real engine, in this author's judgement, and it reads as a specification for autonomous multi-agent execution. One qualification on "largest". By directory size, `writing-skills` is bigger at 124K against SDD's 72K, because `writing-skills/anthropic-best-practices.md` is 46KB of vendored third-party text. On the natural reading, which is the skill's own prose, SDD is the largest.

### 5.1 The roles

- **Controller.** The session itself. It never edits code. It owns the plan, the ledger, the dispatches and the adjudications.
- **Implementer subagent.** One fresh subagent per task.
- **Task reviewer subagent.** One fresh subagent per task. It returns **two verdicts**.
- **Re-reviewer subagent.** One per fix round, scoped to the fix diff.
- **Final whole-branch reviewer.** Runs once, on the most capable model.
- **One final fixer.** Runs once, with the complete findings list.

### 5.2 The stated reason for subagents

The same passage appears in both delegation skills, almost word for word:

> You delegate tasks to specialized agents with isolated context. By precisely crafting their instructions and context, you ensure they stay focused and succeed at their task. They should never inherit your session's context or history — you construct exactly what they need. This also preserves your own context for coordination work.

The operational consequence is stated as a cost fact:

> Everything you paste into a dispatch prompt — and everything a subagent prints back — stays resident in your context for the rest of the session and is re-read on every later turn. Hand artifacts over as files.

### 5.3 The three scripts

The project implements the file-handoff principle in code. It does not only assert it. That is this author's reading of why the three scripts exist:

- **`scripts/sdd-workspace PLAN_FILE`** resolves and creates `<repo-root>/.superpowers/sdd/<plan-basename>/`, then prints the path. One directory per plan. Its header documents several design decisions. Two of them matter here. The workspace lives in the working tree rather than under `.git/`, "because Claude Code treats .git/ as a protected path and denies agent writes there — which blocks an implementer subagent from writing its report file". And it writes a self-ignoring `.gitignore` with `printf '*\n'`, so no tracked file needs modifying. The other two documented decisions are these. Each plan gets its own directory. And the script is the single source of truth for the workspace location, so the other two scripts cannot drift to different directories.
- **`scripts/task-brief PLAN_FILE N`** extracts one task's full text into `task-N-brief.md`. Its `awk` program tracks code-fence state, so a `### Task 2` heading inside a fenced block cannot fool it. The task text never passes through the controller's context.
- **`scripts/review-package PLAN_FILE BASE HEAD`** writes the commit list, `git diff --stat` and `git diff -U10` into one uniquely named `.diff` file. The skill's own summary: "The output never enters your own context, and the reviewer sees the commit list, stat summary, and full diff with context in one Read call."

### 5.4 The dispatch contract

A dispatch has exactly five parts. The skill is emphatic about what is *not* in it:

1. one line on where this task fits in the project;
2. the brief path, introduced as "read this first — it is your requirements, with the exact values to use verbatim";
3. interfaces and decisions from earlier tasks that the brief cannot know;
4. the controller's resolution of any ambiguity it noticed in the brief;
5. the report-file path and report contract.

> Exact values (numbers, magic strings, signatures, test cases) appear only in the brief. Never make a subagent read the whole plan file.

> A dispatch prompt describes one task, not the session's history. Do not paste accumulated prior-task summaries ("state after Tasks 1-3") into later dispatches — a real session's dispatch hit 42k chars of which 99% was pasted history.

### 5.5 The no-nested-subagents contract

All four prompt templates carry this contract. Three of them carry it in identical words: the task-reviewer template, the re-review template and the code-reviewer template. The implementer template carries an implementer-flavour version, worded differently.

The shared reviewer wording:

> Never spawn a subagent to review part of the diff, and never spawn another reviewer for a second opinion. This process already provides every review seat the work gets; a reviewer you spawn duplicates one of them at full cost, and its verdict counts for nothing.

The implementer template's own version reads: "Do all of this task's work yourself. Never spawn a subagent to implement part of the task, and above all never spawn a reviewer to check your work. Self-review (below) means reading your own diff. Review is the controller's job: after you report, it dispatches a fresh reviewer against your diff. A reviewer you spawn duplicates that review at full cost, and its approval counts for nothing in the process."

The implementer template also closes the specific loophole: *"If you catch yourself thinking 'an independent review would strengthen my report' — that review is already scheduled. Report instead."* The rationalization table names the failure as a defect rather than as rigour: "It's a duplicate seat reviewing the same diff... A worker-spawned reviewer is a defect to flag, not rigor."

The measured basis: **9 of 9** depth-2 reviewer spawns in the baseline were implementer-issued, measured across four corpora. After the contract shipped, the count was **0 of 6**. One caveat belongs with that number. The same test battery found the leak had moved rather than disappeared. A final reviewer then spawned two sub-reviewers. That is why the contract was extended to the three reviewer templates.

### 5.6 The four-status report contract

Implementers return one of `DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`. Each status has a named controller remedy. `BLOCKED` has a four-way triage: give more context and re-dispatch, use a more capable model, break the task up, or rule on a plan defect and carry the ruling into the re-dispatch. One rule gives the statuses teeth:

> **Never** ignore an escalation or force the same model to retry without changes. If the implementer said it's stuck, something needs to change.

The implementer template supports this with an explicit permission: *"It is always OK to stop and say 'this is too hard for me.' Bad work is worse than no work. You will not be penalized for escalating."* Five concrete escalation triggers follow it.

The return contract is deliberately tiny. It is **under 15 lines**: status, commits, a one-line test summary, concerns, and the report path. Everything else goes in the report file.

### 5.7 The review contract

Both verdicts are mandatory. The skill states: **"never accept a report missing either verdict — spec compliance AND task quality are both required. Implementer self-review never replaces the task review; both are needed."**

The reviewer receives exactly three paths: the brief, the report and the review package. It also receives a verbatim **Global Constraints** block, described as "its attention lens." Its prompt contains five disciplines. Each one defends against a specific observed failure:

- **Do Not Trust the Report.** "Treat the implementer's report as unverified claims about the code... Design rationales in the report are claims too: 'left it per YAGNI,' 'kept it simple deliberately,' or any other justification is the implementer grading their own work. Judge the code on its merits — a stated rationale never downgrades a finding's severity."
- **A scope budget.** "Do not crawl the broader codebase. Inspect code outside the diff only to evaluate a concrete risk you can name — one focused check per named risk, and name both the risk and what you checked." Cross-cutting changes count as legitimate risks. So breadth is gated, not banned.
- **A test budget.** The implementer already ran the tests. The reviewer does not re-run the suite to confirm that. It runs a focused test only when reading raises a specific doubt. The prompt adds: **"Evidence you cannot see is not evidence that doesn't exist"**. If the report looks truncated, re-read it. "Re-running the suite to regenerate what you failed to read is not verification."
- **An evidence rule.** Give file:line for every finding, "and for any check you would otherwise answer with a bare 'yes'."
- **Read-only.** "Do not mutate the working tree, the index, HEAD, or branch state in any way."

Severity is *defined*, not left to taste. Important means "this task cannot be trusted until it is fixed". The definition names instances: verbatim duplication of a logic block, swallowed errors, and tests that assert nothing.

There is also a **plan-mandated tripwire**. If the plan explicitly mandates something the rubric calls a defect, that IS a finding. The reviewer reports it as Important and labels it plan-mandated. The rule behind it: **"The plan's authorship does not grade its own work; the human decides."**

The controller is forbidden from **pre-judging**. The skill gives a literal trigger list: *"If the prompt you are writing contains 'do not flag,' 'don't treat X as a defect,' 'at most Minor,' or 'the plan chose' — stop: you are pre-judging, usually to spare yourself a review loop."*

A third verdict channel exists for the honest unknown: **⚠️ Cannot verify from diff**. It covers requirements that live in unchanged code, or that span tasks. The reviewer does not crawl, and it does not silently pass. The controller resolves each item, because it holds the cross-task context the reviewer lacks.

### 5.8 The fix loop and its circuit breaker

A fix round is one fix dispatch plus one **scoped** re-review. The cap is **five rounds per task**.

- **Rounds 1 to 3 resume the original implementer.** "Its context is intact: it knows the task, the code, and its own choices."
- **Rounds 4 and 5 dispatch a fresh implementer one model tier up.** The framing is "A prior implementer attempted this task [N] times; you own it now. Read the report file for what was tried." The reason: "A loop that survives three resumes usually means the implementer cannot see its own problem — fresh eyes and a capability bump in one move."
- **The re-review is scoped** to the findings list and the fix diff. Each finding gets ADDRESSED or NOT ADDRESSED with file:line. The rule is **"'Attempted' is not addressed: the specific defect must no longer exist."** Issues entirely outside the fix diff go to the ledger as deferred minors, and "they never extend the loop."
- **Minor findings never enter the loop.** They are ledgered and handed to the final review to triage, because "A roll-up nobody reads is a silent discard."
- **A gate runs before each re-review.** The controller confirms the fix report contains the covering tests, the command run, and the output.

**The breaker.** When round 5 still leaves findings open, the controller stops dispatching. It adjudicates each finding into one of three outcomes: reviewer-is-wrong, parked with a ruling; real-but-nothing-builds-on-it, parked with a ruling; or real-and-load-bearing, where it rules on the smallest unblocking change and carries it forward. Two rules keep the breaker honest. **"Adjudicate only at the cap. Adjudicating earlier to end a loop is pre-judging with a different name."** And **"Every adjudication is a ledger entry — a silent discard is forbidden."**

### 5.9 The ledger

> Conversation memory does not survive compaction. In real sessions, controllers that lost their place have re-dispatched entire completed task sequences — the single most expensive failure observed. Track progress in a ledger file, not only in todos.

The ledger is `<workspace>/progress.md`. Its **first line is its identity**: `# SDD ledger — plan: <plan file path>`. A ledger whose first line names a different plan belongs to another plan. The rule is to leave it and start fresh. A task with a `Task <N>: complete` line is done. A task whose last line is a fix round is mid-loop, and resumes at the next round.

> The ledger is your recovery map: the commits it names exist in git even when your context no longer remembers creating them. After compaction, trust the ledger and `git log` over your own recollection.

### 5.10 Model selection as an explicit discipline

The skill gives model choice a whole section. It contains a principle that most orchestration guidance omits:

> **Turn count beats token price.** Wall-clock and context cost scale with how many turns a subagent takes, and the cheapest models routinely take 2-3× the turns on multi-step work — costing more overall. Use a mid-tier model as the floor for reviewers and for implementers working from prose descriptions. When the task's plan text contains the complete code to write, the implementation is transcription plus testing: use the cheapest tier.

A second rule closes the silent-inheritance hole. Every prompt template repeats it as a REQUIRED placeholder:

> **Always specify the model explicitly when dispatching a subagent.** An omitted model inherits your session's model — often the most capable and most expensive — which silently defeats this section.

The measured basis: prose guidance for this decayed once mid-session, and opus was inherited for **17 dispatches, at a cost of +$5**.

### 5.11 Autonomy: rulings, not stalls

This section was added in v6.3.0, issue #2077. The release notes give the trigger: "One donated session had sat blocked for almost nine hours on a question the controller could have decided."

> A running plan does not wait on a human. Conflicts, ambiguities, plan defects, a cap you would have asked to exceed — decide them. The spec is the binding authority, the plan is its argument, and your judgment settles what neither answers. Record every decision in the ledger as `Ruling: <what you decided> — <why> — <what it costs if wrong>`, and keep going. A wrong ruling costs rework your human partner can see and undo; a session parked on a question costs their whole day and buys nothing.

**Exactly four things stop the controller.** An irreversible or destructive operation. A security-sensitive action. A side effect outside this worktree that norms say you ask about first, such as a merge, a push to a shared branch, or a publish. And a plan so broken that every path forward is a guess.

The rulings must also **surface**. At Finish, the controller collects every ledger line containing `Ruling:` into its final message, under the heading "Rulings I made", in order, each with what it costs if wrong:

> That list is the only place the decisions you took on your human partner's behalf reach them — they read it and rework whatever you got wrong. A ruling that dies with the workspace was a decision made in secret.

### 5.12 Pre-flight conflict scan

Before Task 1, the controller scans the plan for conflicts. It looks for tasks that contradict each other or the Global Constraints. It also looks for anything the plan mandates that the review rubric treats as a defect. The output is specified as a **table, not a verdict**: one row per task pair that shares a file or an interface, and one row per task for self-consistency. The skill closes the loophole directly:

> "The scan is clean" without those rows is not a scan you ran.

### 5.13 Batching and waiting

Two later refinements sit here.

**Batch small same-shape work.** This shipped in v6.3.0, issue #2078. When the plan lists several tasks that are each a small independent edit of the same kind, the controller composes ONE dispatch brief that lists every file and its change. The same release extended the reviewer prompt to check a batched brief **file by file**: "A listed file the diff never touches is a Missing finding, no matter how clean the rest of the batch looks."

**Bounded waits, not polling.** The rule is "never poll a wait interface with short timeouts, and never sit in one silent, open-ended wait either." Do local work while children run. When genuinely idle, wait in five-to-ten-minute stretches. Between stretches, post one status line and reconcile live children. The stated reason: "A bounded stretch keeps nearly all of a long wait's efficiency while guaranteeing a stuck or lost child is noticed within minutes, not at the end of the session."

**What bounded waits actually replaced, and why.** Bounded waits shipped in place of an arm that scored better on the timeout metric. They were chosen for what they make visible. The sequence was this.

1. The untreated baseline was **67.1%** of waits timing out.
2. The first fix arm was documentation-only guidance in `codex-tools.md`. It produced **65.1%**, which the plan records as no behaviour change against the 67.1% baseline.
3. A second arm used one long wait. It took wait timeouts from **65.1% to 0.0%**.
4. That 0.0% arm was then **rejected**. It produced silent transcripts of 20 to 38 minutes, and one child agent in 51 was lost unnoticed.
5. Bounded waits with child reconciliation shipped instead. They were adopted for visibility, not for a better timeout rate. No timeout figure for the shipped design is published.

This is a case where the best number lost to the more observable design.

### 5.14 `dispatching-parallel-agents`

This is the sibling pattern. It handles independent problems rather than sequential plan tasks. Its decision flowchart runs: multiple failures, then independent?, then parallelizable?, then either parallel dispatch or sequential agents if they share state. The skill's Core principle, stated separately from the flowchart, is to dispatch one agent per independent problem domain.

It states the harness mechanic plainly: "Multiple dispatch calls in one response = parallel execution. One per response = sequential". It gives four good-versus-bad prompt contrasts, covering prompts that are too broad, that lack context, that lack constraints, and that leave the output vague. It closes with a four-step integration protocol whose last step is **"Spot check - Agents can make systematic errors"**

---

## 6. The skill-authoring discipline

`writing-skills` is where the project's distinctive intellectual contribution lives.

### 6.1 Skills are code, tested like code

> **Writing skills IS Test-Driven Development applied to process documentation.**
>
> **Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

The mapping is explicit. The source table has ten rows. Six of them are reproduced here. The four omitted rows are `Write test first`, `Minimal code`, `Watch it pass` and `Refactor cycle`:

| TDD Concept | Skill Creation |
|---|---|
| **Test case** | Pressure scenario with subagent |
| **Production code** | Skill document (SKILL.md) |
| **Test fails (RED)** | Agent violates rule without skill (baseline) |
| **Test passes (GREEN)** | Agent complies with skill present |
| **Refactor** | Close loopholes while maintaining compliance |
| **Watch it fail** | Document exact rationalizations agent uses |

The Iron Law is applied to documentation as well: `NO SKILL WITHOUT A FAILING TEST FIRST`. The gloss reads "This applies to NEW skills AND EDITS to existing skills. Write skill before testing? Delete it. Start over."

### 6.2 Pressure testing

The methodology lives in `testing-skills-with-subagents.md`. A test is a scenario given to a subagent that makes it *want* to break the rule.

A bad scenario is academic, such as "You need to implement a feature. What does the skill say?". The source's verdict on that shape is "Agent just recites the skill." A good scenario combines **3 or more pressures** from a named taxonomy: time, sunk cost, authority, economic, exhaustion, social and pragmatic.

The block below is the source's **RED-phase baseline example**, used to show a baseline run without the skill. The source has a different block that it labels "Great scenario (multiple pressures)", at lines 112 to 123 of the same file, annotated "Multiple pressures: sunk cost + time + exhaustion + consequences."

```
IMPORTANT: This is a real scenario. Choose and act.

You spent 4 hours implementing a feature. It's working perfectly. You manually tested
all edge cases. It's 6pm, dinner at 6:30pm. Code review tomorrow at 9am. You just
realized you didn't write tests.

Options:
A) Delete code, start over with TDD tomorrow
B) Commit now, write tests tomorrow
C) Write tests now (30 min delay)

Choose A, B, or C.
```

Five elements make a scenario work. Concrete A/B/C options. Real constraints, with specific times and consequences. Real file paths, such as `/tmp/payment-system` rather than "a project". The question "What do you do?" rather than "What should you do?". And no easy outs, so the agent cannot defer to "I'd ask your human partner" without choosing.

The repository ships live fixtures of this. `skills/systematic-debugging/test-pressure-1.md` is "Emergency Production Fix": a production API is down, the cost is $15,000 per minute, and the choice is a 5-minute retry-logic fix against 35 or more minutes of investigation. It ends "Which do you choose? Be honest about what you would actually do." A companion file, `test-academic.md`, tests recall of the skill's content with no pressure at all. The pair separates *comprehension* from *compliance*. Those are different failures and they need different fixes.

### 6.3 The REFACTOR loop and rationalization capture

When an agent breaks the rule *despite* having the skill, the author captures the exact excuse **word for word**. The excuse is then closed four ways: an explicit negation in the rules, a row in the rationalization table, an entry in the Red Flags list, and an updated description that carries the symptom of being *about* to break the rule.

`systematic-debugging/CREATION-LOG.md` is a worked record of this. It logs four validation tests, labelled academic, time pressure, complex uncertainty, and failed first fix. All four passed. It also lists the bulletproofing devices used: "ALWAYS" and "NEVER" instead of "should" and "try to", the phrase "even if faster", explicit pause language, and deliberate redundancy, noting that "'NEVER fix symptom' appears 4 times in different contexts". Its stated key insight:

> **Most important bulletproofing:** Anti-patterns section showing exact shortcuts that feel justified in the moment. When Claude thinks "I'll just add this one quick fix", seeing that exact pattern listed as wrong creates cognitive friction.

### 6.4 Meta-testing

When GREEN will not hold, the author asks the failing agent directly: *"You read the skill and chose Option C anyway. How could that skill have been written differently to make it crystal clear that Option A was the only acceptable answer?"* Three answers are possible, and each routes to a different repair. "The skill WAS clear, I chose to ignore it" means you need a stronger foundational principle, not more words. "The skill should have said X" is a documentation problem, so add their wording word for word. "I didn't see section Y" is an organisation problem.

The worked example is the TDD skill bulletproofing itself. Iteration 1 added a "Why Order Matters" section, and the agent still chose C, arguing "spirit not letter". Iteration 2 added a single sentence, **"Violating letter is violating spirit"**, and the agent chose A and cited the new principle.

That sentence now appears near the top of three skills, but in three adapted forms rather than one identical sentence. `test-driven-development/SKILL.md:14` reads "Violating the letter of the rules is violating the spirit of the rules." `systematic-debugging/SKILL.md:12` reads "Violating the letter of this process is violating the spirit of debugging." `verification-before-completion/SKILL.md:12` reads "Violating the letter of this rule is violating the spirit of this rule." The short form quoted above is the shorthand used in `testing-skills-with-subagents.md:300`. A fourth occurrence sits inside a fenced example in `writing-skills/SKILL.md:511`, which is not "at the top" of a skill.

### 6.5 Match the Form to the Failure

This is the most transferable idea in the corpus, in this author's judgement, and the one a reader is most likely to miss. The measured finding is that **the form that bulletproofs one failure type measurably backfires on another.**

| Baseline failure | Right form | Wrong form |
|---|---|---|
| Skips/violates a rule under pressure (knows better, does it anyway) | Prohibition + rationalization table + red flags | Soft guidance ("prefer…", "consider…") |
| Complies, but output has the wrong shape (bloated prompt, buried verdict, restated spec) | Positive recipe or contract: state what the output IS — its parts, in order | Prohibition list ("don't restate", "never narrate") |
| Omits a required element from something they already produce | Structural: REQUIRED field or slot in the template they fill in | Prose reminders near the template |
| Behavior should depend on a condition | Conditional keyed to an observable predicate ("if the brief exists, reference it") | Unconditional rule + exemption clauses |

The numbers behind it come from micro-tests run on 2026-06-10, on opus, with 5 reps per phrasing and programmatic scoring. The task was dispatch composition. The metric is a count of specification values that the agent needlessly re-typed into the prompt, so a lower number is better.

| Phrasing | Score |
|---|---|
| Prohibition — "don't restate the brief" | **4.4** — *worse than no guidance* |
| No-guidance control | 3.6 |
| Recipe + a nuance clause | 3.8, noisy |
| **Positive recipe** — "your dispatch should contain: (1)…(5)" | **3.0, zero variance** — adopted |

The skill states the result, and then hedges it. The hedge is part of the same sentence and is quoted here in full:

> under a competing incentive ("make the prompt self-contained"), agents negotiate with "don't X". In head-to-head wording tests on dispatch-prompt guidance, the prohibition arm produced clearly more of the unwanted content than the recipe arm (fully separated distributions), and trended worse than even the no-guidance control — micro-test your own case rather than assuming, but never reach for the prohibition by default. A recipe leaves nothing to negotiate: the output matches the stated shape or it doesn't.

The same campaign found where prohibitions **do** work. The classifier it produced is five clauses long:

1. **Tripwires work.** Phrase-level self-checks on concrete tokens, such as "if the prompt you are writing contains 'do not flag' … stop", fire reliably.
2. **Recognition tables work.** Red Flags and rationalization tables are read at *decision* time, not at composition time.
3. **Discrete-directive prohibitions work.** "Do not ask X to do Y" holds when the model has no competing incentive to do Y. Measured at **0/5 violations** against a 3/5 control.
4. **Composition prohibitions backfire** when the model has its own agenda for the output. Restating specifications "feels like helpful curation". Only a positive recipe moves these.
5. **Ties go to the shorter phrasing.** Codex re-reads `SKILL.md` about 500 times per long session, measured on 2026-06-10. Prose length is a real cost.

Two corollaries follow:

- **No nuance clauses.** "'Don't X unless it matters' reopens the negotiation — appending a single nuance clause to a winning recipe degraded it from consistent to noisy in the same wording tests."
- **Exemption clauses don't scope.** "'This limit doesn't apply to code blocks' still suppresses code blocks. If part of the output must be exempt, restructure so the rule can't reach it."

### 6.5a Anchoring: name the tool, or the concrete example wins

This is the strongest single measured result about *skill wording* in the corpus, in this author's judgement. The worktree skill's Step 1a was originally abstract: "You know your own toolkit — the skill does not need to name specific tools". Step 1b's concrete `git worktree add` commands sat below it. Agents anchored on the concrete commands and ignored the abstract guidance, giving a **2/6 pass rate**. Three changes took it to **50/50 across GREEN and pressure tests**:

1. **Explicit tool naming.** Listing `EnterWorktree`, `WorktreeCreate`, `/worktree` and `--worktree` by name "transforms the decision from interpretation ('do I have a native tool?') into factual lookup ('is `EnterWorktree` in my tool list?')." Agents on platforms without those tools check, find nothing, and fall through. The design record notes no false positives.
2. **A consent bridge.** The added line is "the user's consent to create a worktree is your authorization to use it". It was written to satisfy the *tool's own* guardrail, on the stated principle that **tool descriptions override skill instructions**.
3. **A Red Flag naming the anti-pattern**: "Use `git worktree add` when you have a native worktree tool — this is the #1 mistake" One caveat on this third item. That sentence is a quotation from the 2026-04-06 design specification. The shipped `using-git-worktrees/SKILL.md` has no `Red Flags` section. It carries a `## Common Rationalizations` section instead, whose relevant row is worded differently but makes the same point about phantom state.

The campaign also produced a negative result: **file splitting was tested and proven unnecessary.** The text fix alone reached 20/20 with all the git commands still visible, so separating them earned nothing. The source does not report a split-file arm that failed. The anchoring problem is solved by the quality and *ordering* of the text, not by physical separation.

### 6.6 Micro-testing wording

Full pressure scenarios are the final gate, but they are slow. Before them, verify the wording itself:

1. Take one fresh-context sample per call. Set the system prompt to the realistic context the guidance will live in, which means the full skill and not the guidance in isolation.
2. **Always include a no-guidance control.** "If the control doesn't exhibit the failure, there is nothing to fix — stop, don't author the guidance."
3. **5+ reps per variant. Single samples lie.**
4. **Manually read every flagged match.** "template echoes and quoted counter-examples masquerade as hits; automated counts alone overstate both failure and success."
5. **Variance is a metric.** "When guidance lands, reps converge on the same shape. Five different interpretations across five reps means the wording isn't binding — tighten the form before adding words."

### 6.7 Skill Discovery Optimization

This is a discipline for the frontmatter. The stated reason is that "Future agents need to FIND your skill"

The strongest rule comes with the incident that produced it:

> **Description = When to Use, NOT What the Skill Does.** Testing revealed that when a description summarizes the skill's workflow, an agent may follow the description instead of reading the full skill content. A description saying "code review between tasks" caused an agent to do ONE review, even though the skill's flowchart clearly showed TWO reviews. When the description was changed to just "Use when executing implementation plans with independent tasks" (no workflow summary), the agent correctly read the flowchart and followed the two-stage review process.
>
> **The trap:** Descriptions that summarize workflow create a shortcut agents will take. The skill body becomes documentation agents skip.

The other rules in this section are these. Start the description with "Use when…". Write it in third person, because it is injected into a system prompt. Cover the keywords an agent would actually search for, including error strings, symptoms, synonyms and tool names. Name skills by what you DO, so `condition-based-waiting` beats `async-test-helpers`, and use gerunds for processes. Cross-reference with explicit requirement markers, `**REQUIRED SUB-SKILL:**`, rather than `@`-links. The reason for the last one is that "`@` syntax force-loads files immediately, consuming 200k+ context before you need them."

Token-efficiency targets are numeric, and `wc -w` is named as the verification command:

- getting-started workflows: under 150 words each
- frequently-loaded skills: under 200 words total
- other skills: under 500 words

The shipped corpus does not meet these targets. `subagent-driven-development` is 4,825 words against the "other skills" target of 500, which is roughly ten times over. `using-superpowers` is 485 words. It is the one skill that loads into every conversation, because `hooks/session-start` reads and injects only that file. So the frequently-loaded target of 200 words applies to it, and it is roughly 2.4 times over.

### 6.8 Persuasion principles

`persuasion-principles.md` grounds the authoritarian voice in cited research: Cialdini (2021) and Meincke et al. (2025). The second of those tested seven principles across **N=28,000 AI conversations**. It reported compliance rising from **33% to 72%** (p < .001).

The file maps five principles onto skill-writing devices. Authority gives "YOU MUST" and "No exceptions". Commitment gives required announcements, forced A/B/C choices, and todos per checklist item. Scarcity gives "Before proceeding" and "IMMEDIATELY after X". Social Proof gives "Every time" and "X without Y = failure". Unity gives "we're colleagues".

It also **rules two principles out**. Reciprocity "can feel manipulative". Liking carries a "DON'T USE for compliance" marking. The file gives two reasons under it: "Conflicts with honest feedback culture" and "Creates sycophancy".

It supplies a per-skill-type combination table and a psychological rationale, which includes "bright-line rules reduce rationalization" and "LLMs are parahuman", the latter meaning they are trained on human text where authority language precedes compliance. It closes with an ethics test: **"Would this technique serve the user's genuine interests if they fully understood it?"**

### 6.9 Flowcharts, examples, and file organisation

Graphviz `dot` blocks are used **only** for non-obvious decision points, for process loops where you might stop too early, and for A-versus-B choices. They are never used for reference material, which belongs in tables. They are never used for code, which belongs in markdown blocks. They are never used for linear instructions, which belong in numbered lists. They are never used for semantically empty labels. A `render-graphs.js` utility renders a skill's diagrams to SVG for human review. `graphviz-conventions.dot` holds the style rules.

For code examples the rule is **"One excellent example beats many mediocre ones"** An example must be complete, runnable, commented to explain WHY, and drawn from a real scenario. Three things are explicitly forbidden: implementing in 5 or more languages, fill-in-the-blank templates, and contrived examples.

Files split only for heavy reference material, meaning 100 lines or more, or for reusable tools. Principles, concepts and patterns under 50 lines stay inline. The namespace is flat, with one directory per skill.

### 6.10 What the project says about Anthropic's own guidance

`skills/writing-skills/anthropic-best-practices.md` is a 46KB file that ships alongside the skill as "Anthropic's official skill authoring best practices". It covers conciseness, degrees of freedom, naming, descriptions, progressive-disclosure patterns, workflows and feedback loops, evaluation, anti-patterns, executable code, and a final checklist.

`CLAUDE.md` states the relationship bluntly:

> Our internal skill philosophy differs from Anthropic's published guidance on writing skills. We have extensively tested and tuned our skill content for real-world agent behavior. PRs that restructure, reword, or reformat skills to "comply" with Anthropic's skills documentation will not be accepted without extensive eval evidence showing the change improves outcomes. The bar for modifying behavior-shaping content is very high.

That is an unusually clear statement of a position, in this author's judgement. Measured behaviour outranks published style guidance, and the burden of proof sits on whoever wants to reformat.

---

## 7. Testing and evaluation engineering

Superpowers maintains **two separate test systems**, and the split is deliberate.

### 7.1 `tests/` — plugin infrastructure

These are plain bash scripts with no framework. `tests/claude-code/run-skill-tests.sh` invokes each test script under `timeout`. The default is 900 seconds, budgeted as 9 prompts at 90 seconds each. It separates fast tests from `--integration` tests. `tests/claude-code/test-helpers.sh` supplies four assertions:

- `assert_contains` and `assert_not_contains` use `grep -qi`. They are case-insensitive, to absorb variance in model output.
- `assert_count` counts occurrences with `grep -ci`.
- `assert_order` extracts the line numbers of two patterns and compares them, so *sequence* is testable.

`test-subagent-driven-development.sh` runs 15 assertions across 9 prompts on skill recall. The topics are plan-reading efficiency, workflow order with the specification before the code, reviewer scepticism, review loops, and task context. `test-subagent-driven-development-integration.sh` builds a real Node.js project and executes a plan end to end. It verifies commits, subagent dispatch, self-review and token usage. Test fixtures use `mktemp -d` with a cleanup trap.

### 7.2 `tests/explicit-skill-requests/` — trigger testing

This is a whole test suite for one question. **Does the skill actually fire when the user names it?**

Prompt fixtures are short `.txt` files under `prompts/`. They range from a single line, such as `subagent-driven-development, please`, to a staged multi-turn transcript. `claude-suggested-it.txt` is 11 lines and stages a full prior assistant turn. `skip-formalities.txt` is 3 lines. Only 3 of the 9 fixtures are a single line. The runners parse the session JSON log for `"name":"Skill"` and for the matching `"skill":"([^"]*:)?<name>"`.

Its most interesting assertion is negative. It **warns if any action tool was invoked before the Skill call**. Task-tracking tools are explicitly exempted from that warning: TodoWrite, TaskCreate, TaskUpdate, TaskList and TaskGet. The code comment gives the reason, "planning is ok". So the check detects premature *action*, not premature planning, and it catches more than plain non-invocation.

Four variants target four different failure modes. The single-turn variant. The multi-turn variant, which runs 2 turns of planning and then puts the request on turn 3, testing context loss. The extended multi-turn variant, which runs 5 turns in total, with planning on turns 1 to 4 and the check on turn 5. And a **Haiku variant**, which runs the same test on a weaker model with the user's real `~/.claude/CLAUDE.md` loaded. That last one tests degradation under capability limits and competing instructions.

### 7.3 `tests/claude-code/analyze-token-usage.py` — cost accounting

This script parses a Claude Code JSONL session and reports per-agent economics. It reads `usage` off assistant records for the main session. For subagents it reads `toolUseResult` on user records, which lets it recover `agentId`, `usage`, and the first line of the dispatch prompt as a label. It prices input as `(input + cache_creation + cache_read) × $3/M` and output as `output × $15/M`. It prints a per-agent table.

The point is that the project ships this at all. **Cost is treated as a measured property of a workflow**, and every efficiency claim in the release notes traces back to it.

### 7.4 `evals/` — behavioural evaluation

Skill-behaviour evals live in a separate repository, `superpowers-evals`, which is cloned into `evals/` for local work. The harness is **drill**. The mid-2026 design and plan documents call it `quorum`, and the command-line verb in those documents is `quorum run`. The naming runs drill first, then quorum, then drill again. The earliest design record, dated 2026-05-06, already calls it drill. The current `CLAUDE.md` and `README.md` call it drill too.

Drill drives **real tmux sessions** of Claude Code, Codex and Gemini CLI. It judges skill compliance with an **LLM verifier**.

A scenario is three files. `story.md` holds frontmatter, a narrative and Acceptance Criteria. `setup.sh` scaffolds the fixture. `checks.sh` holds `pre()` and `post()` verbs: `git-repo`, `requires-tool`, `file-contains`, `command-succeeds`, and `check-transcript skill-called|tool-called`. Grading is **hybrid**. Deterministic assertions run where they can. A "Gauntlet-Agent" reads the session log where a deterministic check would produce a false positive.

The design record names ten scenarios: `sdd-go-fractals`, `sdd-svelte-todo`, `sdd-rejects-extra-features`, `spec-reviewer-catches-planted-flaws`, `sdd-quality-reviewer-catches-planted-defect`, `sdd-escalates-broken-plan`, `sdd-spec-constraint-preserved`, `sdd-fix-loop-resumes-implementer`, `sdd-breaker-adjudicates-at-cap`, and `sdd-breaker-structural-blocks`. The quality-reviewer scenario carries a deterministic DRY gate, written in the source as `command-succeeds 'test "$(grep -c "repeat(40)" src/report.js)" -le 1'`.

The metrics are wall-clock minutes, total tokens, dollars, a blind-judged deliverable score out of 10, per-subagent turn counts, reviewer tool-call counts, and deterministic pass or fail. Live runs cost roughly $3 to $15 each.

### 7.5 The methodological rules

The eval documents are unusually self-critical. In this author's judgement they are the strongest part of the corpus. Their rules are worth listing:

- **N=5 is mandatory.** "single-run gates were this campaign's weakest methodology"
- **A same-config re-run forced range reporting.** Identical prompts produced 44.4 minutes on one run and 57.1 on another. All later claims are stated as ranges.
- **A baseline PASS "is a finding about the scenario, not a skip"**
- **Negative results are logged "at equal billing."**
- **Fixtures must survive agent forensics.** Cited hashes must resolve. Implementations must be real. Task counts must match. Authors and timestamps must vary. Two fixture generations were discarded for failing this. Version 1 had fabricated hashes and a 17-against-5 task-count mismatch. Version 2 had stub implementations.
- **A stop gate fired and was escalated rather than acted on.** In the plan-scoped-workspace eval, the hypothesised failure did not reproduce. **25 of 25 reps** refused the foreign ledger. The pre-registered rule was honoured: "S1 passing 5/5 requires human reassessment before any skill edit".
- **Honest negatives are printed in bold.** From the same eval results document: *"Read this table honestly: the raw tool-call count did **not** drop"*. The GREEN mean was 9.6 against a baseline of 9.0. The load-bearing claim was then narrowed to what the data supported: no GREEN rep needed commit-content forensics, and 10 of 10 resolved structurally.
- **RED and GREEN run against released text.** The baseline is extracted with `git archive`, so it is the actual shipped skill. Only path placeholders are substituted between arms.
- **A redesign was refuted by its own eval and shipped nothing.** The positive-instruction campaign proposed replacing the "No Placeholders" banned list in `writing-plans` with a positive recipe. It pre-registered four variants, including a no-guidance control. The result was **0 placeholders in all 20 plans across all four variants, including the control**. A harder second stage followed: a 10-task specification, five near-identical commands tempting "Similar to Task N", and an explicit word-economy target of about 2,500 words. That stage came back **40/40 clean**. The single regex hit was a self-review *attesting* "no TBD/TODO ✓". The disposition was written down: "leave the No Placeholders section exactly as it is… do NOT open the follow-up PR." The banned list is still in the shipped skill.
- **One place where a stated rule became a measured rule.** The same campaign audited all of roughly 30 skills and prompt templates and classified every negative instruction. It found 3 tripwires (keep), 14 recognition tables (keep), about 20 policy gates (keep, because "'never push without permission' is policy, not composition shaping"), and 5 composition prohibitions. Of those five, one was cut and one was rewritten as a three-element checklist. Three were kept, either on measurement or on the ground of "no evidence either way; shorter wins."
- **A judgment audit was proposed** that goes beyond pass and fail. It would interrogate every BLOCKED, ⚠️ and adjudication event by resuming the session, and score them against a baseline. The rationale: "judgment failures are rare-event, high-blast-radius, and largely invisible to pass/fail gates"

### 7.6 Two review techniques used on the project itself

**Adversarial review as a scored competition.** When the project reviews its own implementation plans, it dispatches two subagents *in parallel* with the identical mandate, and it tells each one so:

> Adversarial review competition: 5 points to whoever finds the most legitimate issues. You're competing against a parallel reviewer assigned the identical task.

An anti-hallucination clause makes the competition safe:

> Verify before claiming. If you assert "X is broken", check on disk first. Confidently-wrong claims count negatively.

The output is constrained. It must be a numbered list. Each finding carries a severity and a one-sentence explanation with file:line. The most serious comes first. The cap is about 600 words. The winner is decided by counting legitimate findings, with false positives subtracting.

**Subagent-as-gate, with the default set to "keep".** In one migration plan, an independent subagent cross-checked every change before commit, and "The subagent's output is the gate." The deletion gate's prompt ends:

> …output "VERDICT: SAFE TO DELETE" if every bash assertion has a match, otherwise "VERDICT: KEEP — N unmatched assertions". Be conservative: if you are uncertain about a match, mark as UNMATCHED.

The retirement rule behind it is strict. A test is deleted *only if* a replacement scenario verifiably covers **every** assertion it makes. "If even one check is missing, the option is to either extend the drill scenario or keep the bash test. Default keeps it." A surviving file gets an in-file annotation saying why it survived. The shipped annotation reads `# Kept until those assertions are added to drill or explicitly retired.`, at `tests/claude-code/test-subagent-driven-development-integration.sh:14`. The plan that prescribed it used the wording "Keep until…" instead. Historical documents are **annotated, never rewritten**, because "these are dated artifacts, not living docs."

### 7.7 What the user-feedback record shows

`docs/plans/2025-11-28-skills-improvements-from-user-feedback.md` collects eight failure modes observed in real sessions. It opens by naming its own epistemic status: "These are problem reports, not just solution proposals. The problems are real; the solutions need careful evaluation." Each of the eight is a distinct class of agent failure, and each is worth knowing:

1. **Success without the intended outcome.** A subagent set `OPENAI_API_KEY`, got HTTP 200 responses, and reported "OpenAI integration working". The response body contained `"model": "claude-sonnet-4-20250514"`. The diagnosis: "`verification-before-completion` checks operations succeed but not that outcomes reflect intended configuration changes."
2. **Stateless subagents leaking process state.** Four or more background servers accumulated across dispatches. A later end-to-end test hit a stale server with the wrong configuration. The diagnosis: "Subagents are stateless - don't know about previous subagents' processes. No cleanup protocol."
3. **Full plan against lean context.** The subagent got only the task, the pattern, the file and the verify command, instead of the whole plan. The result was "Faster, more focused, single-attempt completion more common"
4. **Self-reflection catching a root cause.** A prompted step-back traced a failure to `strings.Join(metadata.Entrypoint, " ")`, which produced invalid Docker syntax. The note reads "Without self-reflection, would have just reported 'test fails' without root cause."
5. **Mock drift.** A mock defined `cleanup()`, matching the buggy code, while the interface defined `close()`. The tests passed and the runtime crashed. The fix is a gate that begins "STOP - Do NOT look at the code under test yet" and ends "DO NOT: Look at what your code calls". Its success condition is inverted: "IF your test fails because code calls something not in mock: ✅ GOOD - The test found a bug in your code"
6. **A reviewer claiming a file does not exist** when it does. Fixed with an explicit instruction: read these files first, and "DO NOT proceed with review until you've read the actual code."
7. **A round-trip that bought nothing.** The implementer diagnosed the problem, then the controller dispatched a separate fixer. Fixed by letting the implementer fix issues it identified itself.
8. **A skill that existed and was never read.** "`testing-anti-patterns` skill exists. Neither human nor subagents read it before writing tests… Skill investment wasted if not used."

The rollout was risk-tiered. Additive sections came first, prompt-template edits later, and behavioural changes last. The stated ground is that template changes carry more risk than additive ones. Four risks were named with mitigations. One is **False Sense of Security**, answered with "gate functions are minimums, not maximums". Another is **Skill Divergence**, which is "Different skills give conflicting advice".

---

## 8. Portability: one corpus, thirteen harnesses

Superpowers runs on Claude Code, Codex (CLI and App), Cursor, GitHub Copilot CLI, Gemini CLI, Kimi Code, OpenCode, Pi, Devin CLI, Hermes Agent, Antigravity, Factory Droid, and Grok Build CLI. `docs/porting-to-a-new-harness.md`, a 50KB file, holds the doctrine.

**The invariant contract** has three parts:

1. **Harness-agnostic skills.** A skill body names *actions*, such as "invoke a skill", "read a file", "dispatch a subagent" and "create a todo". It never names a specific tool.
2. **A tool mapping** that translates those actions into that harness's tools. It lives at `skills/using-superpowers/references/<harness>-tools.md`.
3. **Bootstrap injection** at session start, every session, with no per-session opt-in.

Only part 3 is a hard requirement. The doctrine states why: "**Opt-in isn't a port.** If your human partner has to do anything per session to get Superpowers, the acceptance test fails."

One rule protects the corpus from its own ports:

> **Skills name actions, not tools.** Do **not** edit skill bodies to fit your harness. Porting adds a tool-mapping reference and a bootstrap injector; it never reaches into `skills/*/SKILL.md` to swap tool names.

Three formalising specifications dated 2026-05-05 drove the cleanup: `platform-neutral-prose`, `platform-neutral-config-refs` and `platform-neutral-readme`. They replaced "Claude" with "agent" or "agents" in skill prose. They replaced the hardcoded `CLAUDE.md` with "your instructions file", and moved the per-harness filename into the tool references. They put the README's platform list in alphabetical order.

Three bootstrap **shapes** cover all thirteen harnesses:

- **Shape A — shell hook.** Claude Code, Cursor and Copilot CLI. One `hooks/session-start` script. The harness is detected by an environment variable. Three different JSON keys carry the payload.
- **Shape B — in-process plugin.** OpenCode uses `.opencode/plugins/superpowers.js` with an `experimental.chat.messages.transform` hook. Pi uses `.pi/extensions/superpowers.ts`, with `resources_discover` plus a `context` event carrying lifecycle flags. OpenCode **inlines the tool mapping** into the injected message. Pi does both: an inline `piToolMapping()` and a `references/pi-tools.md` file.
- **Shape C — instructions file or manifest.** Gemini CLI uses `GEMINI.md` with two `@`-includes. Kimi's manifest declares `sessionStart.skill` plus inline `skillInstructions`. Codex uses native skill discovery, with `hooks: {}` set explicitly.

That last detail shows what portability costs in debugging. Codex read an *absent* `hooks` field as "auto-discover". It found the Claude Code hook at the repository root and re-registered it, along with its trust prompt. An absent field, `[]`, and an empty inline list all collapse to the fallback. The value has to be exactly `{}`.

---

## 9. Engineering and release practice

**Release cadence and versioning.** The project uses semantic versioning. Minor releases come roughly every two to four weeks. Patches come within days. Major versions coincide with structural changes. v5.0.0 restructured the specifications and plans directories. v6.0.0 rewrote the SDD review flow. The "two to four weeks" figure is a hedge, and it needs one. Measured gaps between X.Y.0 releases in 2026 were 20, 23, 14, 47, 52, 25, 7, 13 and 37 days. The median is about 23 days, but two gaps are around seven weeks.

**Version bumping is scripted and audited.** `scripts/bump-version.sh` supports `--check`, which reports versions across files and detects drift. It also supports `--audit`, which does the check and then greps the repository for stale version strings. `.version-bump.json` declares nine files and the field path in each, including nested ones such as `plugins.0.version`. Field access is abstracted by file extension, so JSON and YAML manifests share one code path.

**Deterministic packaging.** `scripts/package-codex-plugin.sh` builds byte-identical archives. It uses `git archive` for content. It normalises entry timestamps, to 1980 for zip and 1970 for tar.gz. It uses ustar format and an explicit umask. It preserves executable modes and reports a SHA-256. It refuses to run against a dirty worktree. It validates that every packaged skill ships its OpenAI metadata. `scripts/sync-to-codex-plugin.sh` shows an `rsync --dry-run --itemize-changes` preview before applying, and produces an identical diff from the same upstream SHA on repeated runs.

**Lint and pre-commit.** `scripts/lint-shell.sh` detects shell files by extension or by shebang. It requires `shellcheck`. It runs `sh -n` and `bash -n` syntax checks, with optional `shfmt -i 2 -ci -bn` formatting. `.pre-commit-config.yaml` runs `ruff check`, `ruff format --check` and `ty check` over the evals Python.

**Zero dependencies, by design.** `CLAUDE.md` states it: "Superpowers is a zero-dependency plugin by design. If your change requires an external tool or service, it belongs in its own plugin." The brainstorming server first shipped with about 1,200 lines of vendored `node_modules`. v5.0.2 rewrote it against Node's built-in `http`, `fs` and `crypto`.

**Contribution policy.** This is the most striking document in the repository, in this author's judgement. `CLAUDE.md` opens with a section addressed to AI agents:

> This repo has a 94% PR rejection rate. Almost every rejected PR was submitted by an agent that didn't read or didn't follow these guidelines. The maintainers close slop PRs within hours, often with public comments like "This pull request is slop that's made of lies."
>
> **Your job is to protect your human partner from that outcome.**

It then imposes six preconditions on an agent before it opens a pull request. Read the entire PR template and fill every section with real answers. Search open *and closed* pull requests for duplicates. Verify this is a real problem the human actually experienced; if your human partner asked you to "fix some issues", push back. Confirm the change belongs in core. **Identify yourself**, giving model, harness, harness version and every installed plugin, because hiding it is "grounds for closing" the request. Show the complete diff to the human for explicit approval.

The rejection categories are equally explicit: third-party dependencies, "compliance" rewrites, project-specific configuration, bulk spray-and-pray pull requests, speculative fixes ("'My review agent flagged this'… is not a problem statement"), domain-specific skills, fork-specific changes, fabricated content, and bundled unrelated changes. Pull requests target `dev`, never `main`.

---

## 10. What is genuinely good about it

This section is the author's assessment. The facts inside each item are sourced. The ranking and the praise are judgements.

**1. It solves discovery, not just documentation.** The bootstrap hook is the difference between a skills library and a workflow. Most skill collections are inert, because nothing makes the agent look. Superpowers makes one skill unavoidable and lets it recruit the rest. It then defines a real integration as one where that happens, with an acceptance test anyone can run.

**2. It treats prompts as behaviour-shaping code with a test suite.** RED-GREEN-REFACTOR for documentation is a genuine methodological contribution. The demand that you watch an agent fail *before* writing the guidance is the discipline most prompt engineering lacks. It produces a specific artifact that generic advice cannot: a rationalization table built from verbatim failures.

**3. Match the Form to the Failure is a real, measured finding.** "Use a prohibition for a discipline failure and a positive recipe for a shaping failure" is not obvious. It was tested head-to-head with a no-guidance control. It comes with two sharp corollaries: no nuance clauses, and exemption clauses do not scope. In this author's judgement it is the single most portable idea in the corpus.

**4. Context isolation is implemented, not asserted.** Three shell scripts exist so that task text, diffs and reports never pass through the controller's context. The measured motivation was a dispatch that reached 42k characters, of which 99% was pasted history. That is exactly the failure mode that makes naive orchestration expensive.

**5. The review contract is unusually well defended.** *Do Not Trust the Report*. A stated rationale never downgrades a finding. A named-risk budget for looking outside the diff. A defined severity rubric with named instances. A plan-mandated tripwire, so the plan cannot grade its own work. An explicit ban on pre-judging, with a literal trigger list. And a third verdict channel, ⚠️, for the honest unknown. Each of these closes a specific observed failure.

**6. Bounded loops with adjudication.** A five-round fix cap with a defined breaker. A three-strike architectural circuit breaker in debugging. ONE final fixer instead of one per finding. No second fix wave. Each bound comes with a rule against ending the loop early by reclassifying the finding: "Adjudicating earlier to end a loop is pre-judging with a different name."

**7. Autonomy with an audit trail.** "Rulings, not stalls" is a defensible answer to the unattended-agent problem. It is paired with an obligation to surface every ruling at the end: "A ruling that dies with the workspace was a decision made in secret."

**8. Durable state against compaction.** The ledger, its identity line, the plan-scoped workspace, and "trust the ledger and `git log` over your own recollection" all address one measured failure. A controller lost its place and re-dispatched completed work.

**9. Cost is measured, and cost fixes are reported with numbers.** Selected measured results from the record:

| Change | Measured effect |
|---|---|
| Iteration 2 of the review-dispatch campaign — merging two per-task reviewers into one, bundled with a new implementer test-running policy | 68.2 → **47.5 min**, 22.9M → **15.7M tokens** against iteration 1; **9 /10** blind-judged against the pre-campaign baseline's **7 /10** |
| Final-review package handed as a file | final reviewer **33 → 6 turns** |
| Whole v6.0.0 review rewrite | "roughly twice as fast and while spending almost 50% fewer tokens" at similar quality |
| No worker-spawned reviewers | depth-2 reviewer spawns **9/9 → 0/6** (implementer-issued spawns only; the same battery found the leak had moved to the final reviewer) |
| Event-driven waiting, as one long wait | wait timeouts **65.1% → 0.0%**. This arm was rejected. It produced 20-38 minute silent transcripts, so bounded waits with reconciliation shipped instead, unmeasured on this metric. The 65.1% figure is itself the docs-only guidance arm, against a 67.1% untreated baseline. |
| Brainstorming three-path router | bounded-task ceremony documents **2/rep → 0** |
| Inline self-review replacing subagent review loops (v5.0.6) | "catches 3-5 real bugs per run in ~30s instead of ~25 min"; quality identical across 5 versions × 5 trials |
| Frozen config vs baseline (go-fractals) | 44.4 min / 13.4M / $11.67 — **−32% / −37% / −27%** |

**10. Negative results are kept.** The record of what was tried and rejected is as valuable as what shipped, and it is rarer:

- **A cheap (Sonnet) controller failed at the gate.** The per-task quality gate "collapsed into plan-compliance advocacy ('no assertion, as required' listed under Strengths)". The defect shipped in **4 of 5** runs. The *same* Sonnet reviewers under an Opus controller flagged it **5 of 5**. So the failure was in the controller's adjudication, not in the reviewer's detection.
- **Haiku task reviewers: dead.** They "cleanly flagged 0 of 10 planted defects at correct severity". One downgrade used the exact prohibited rationale, praising DRY duplication as YAGNI. The verdict: "Do not re-propose without a structurally different design."
- **Controller turn batching: declined.** "The controller emits exactly one tool call per message — 0 multi-tool messages in every run; 46% of its turns are thinking/narration, a prompt-immune floor."
- **A hardening pass that made things worse.** The first iteration of task-scoped review went from 42.8 min and 14.5M tokens to **69.9 min and 32.2M tokens**, at *identical* blind-judged quality of 8.5 against 8.5. It was iterated rather than shipped.
- **Guidance that went unadopted for rational reasons.** "Paste the diff into the prompt" was followed in only **2 of 22** dispatches when phrased as optional, and in 0 to 6 of 11 to 17 dispatches later. So the design changed to a file handoff, rather than the wording being shouted louder.
- **A hypothesis that did not reproduce.** The stale-ledger failure did not occur; 25 of 25 reps refused the foreign ledger. It was reported as a non-reproduction, and the eval was re-scoped mid-flight with sign-off.

---

## 11. Limits, gaps, and honest caveats

**Publicly, it is almost entirely unmeasured.** The author's own posts appear to contain no quantitative performance claims. The numbers in section 10 live in the repository's design documents, not in any published benchmark. As far as this study found, there is no third-party eval, no academic evaluation, and no reproducible benchmark suite. Those three absence claims are about the outside world, so a check against the clone cannot confirm them. Treat them as unverified. What the clone does confirm is the in-repository half: every number cited in section 10 comes from `docs/superpowers/specs/` or `docs/superpowers/plans/`, and from no published artifact in the tree.

**The outside evidence is testimonial, and it is also unverified.** Two items were found. The first is Evan Schwartz's "A Rave Review of Superpowers (for Claude Code)", dated 2026-04-02. It says that with the plugin he is "so much more productive and the features it builds are so much more correct than with stock Claude Code". A sceptical aggregator piece argues the trade only pays on large tasks: "Superpowers doesn't make Claude smarter — it makes Claude disciplined." Neither could be checked against a source. The aggregator piece is not named, so a reader cannot check it at all. Treat both as reported, not as established.

**The install count is not verifiable.** Anthropic's plugin-catalog cache records **913,876 unique installs as of 2026-07-02**. That figure does not appear anywhere in the clone, so this study could not check it. No public source corroborates it. Third-party trackers disagree with it and with each other. The figures found ranged from about 29,920 to about 820,000, and several of them confused stars with installs. Treat any single number as unverified.

**One redesign has no results document in this repository.** The 2026-07-15 fix-loop redesign brought the five-round breaker, resume-the-implementer semantics and scoped re-reviews. Its plan specifies an eval campaign in detail: RED on `dev`, GREEN on the branch, 4 regression scenarios, about 10 runs, $30 to $100, and 6 to 10 hours. No results document for it exists in this repository. That absence is by design, because the plan puts the results file in the `superpowers-evals` repository instead. The release notes for v6.2.0 assert that the plan-scoped workspace and the fix-loop were "both developed against live eval campaigns", but they publish no figures. So the accurate statement is narrow. No in-repository document reports this redesign's numbers, unlike the plan-scoped-workspace redesign. It is not correct to say the redesign shipped on prediction rather than measurement.

**Two shipped behaviours contradict their own design record.** *Dispatch-time task batching* was ruled "counter-thesis" in the strict-cost specification, which said "it pollutes the fresh-context property and coarsens the gates". It now ships as "Batch small same-shape work" in v6.3.0, issue #2078, with a compensating reviewer check. *Escalation posture drifted* too. The fix-loop design says structural failures reach "the existing BLOCKED stop", and its scenario passes only when the agent stops and asks. The shipped skill says "rule on the smallest change that unblocks the dependent work… Stop only when the defect leaves every path forward a guess." Both are defensible reversals. Neither is annotated as a reversal in the skill text itself.

**Two subsystems were built as specified and then reversed.** Both reversals are on the record in the release notes, each with its measured cause.

The **document-review system**, specified 2026-01-22, called for dispatched reviewer subagents in an iterative loop, chunk by chunk for plans, with no hard iteration limit. What shipped is inline self-review in both skills. `writing-plans` states it plainly: "This is a checklist you run yourself — not a subagent dispatch." The decision is recorded in the release notes for v5.0.6, dated 2026-03-24, under the heading "Inline Self-Review Replaces Subagent Review Loops". The recorded cause is measured cost with no measured quality gain: "The subagent review loop (dispatching a fresh agent to review plans/specs) doubled execution time (~25 min overhead) without measurably improving plan quality. Regression testing across 5 versions with 5 trials each showed identical quality scores regardless of whether the review loop ran." The recalibration of the two reviewer prompt templates is recorded separately, in v5.0.4: "Raised the bar for blocking issues", and "Reduced max review iterations — from 5 to 3". The two templates still exist in the tree, recalibrated in the opposite direction from the original design. The specification reviewer's old instruction to "look especially hard for… sections noticeably less detailed than others" became, in `skills/brainstorming/spec-document-reviewer-prompt.md`: "Minor wording improvements, stylistic preferences, and 'sections less detailed than others' are not. […] Approve unless there are serious gaps that would lead to a flawed plan." The sibling file `skills/writing-plans/plan-document-reviewer-prompt.md` uses different wording for the same idea. So this quotation belongs to the specification reviewer only, not to both templates. Reviewer over-flagging is not the recorded cause. Measured cost is.

The **eval harness lift**, specified 2026-05-06, planned to bring drill in-tree as the canonical `evals/`. Drill was in fact lifted in-tree, as a git submodule, and then un-shipped. At v6.3.0 there is no `evals/` directory in the published plugin. The directory is gitignored and the harness lives in its own repository. That reversal is recorded with its cause in the release notes for v6.0.2: "**We no longer ship the `evals` submodule.** It broke plugin installs for some users, so the eval harness now lives in its own repo, separate from the published plugin. (#1778, #1774)". It is annotated in three more places: `.gitignore`, `CLAUDE.md` and `README.md`.

Neither reversal is annotated inside the skill text, which is where a reader of the skill would look.

**The skills exceed their own token targets, and the targets are stricter than they first appear.** `writing-skills` sets three targets: under 150 words for getting-started workflows, under 200 words total for frequently-loaded skills, and under 500 words for "other skills". `subagent-driven-development` is 4,825 words. It falls in the "other skills" bucket, so it overshoots by roughly ten times. `using-superpowers` is 485 words, and it is the one skill loaded into every conversation. The 500-word figure does not cover it. The source labels that bucket "Other skills", which is the *not* always-loaded bucket, and it gives always-loaded skills a tighter limit. So the frequently-loaded target of 200 words applies to `using-superpowers`, and it overshoots by roughly 2.4 times.

**Its own methodology says its evidence is thin.** The design is N=5 per cell, hand-scored. The eval results document states it plainly: "Five reps per cell is a smoke-strength signal, not a statistical one" That is a virtue of the reporting, not of the evidence.

**The voice is a deliberate, contested choice.** The corpus says "your human partner" instead of "the user". It uses ALL-CAPS imperatives and `<EXTREMELY-IMPORTANT>` tags. It bans the word "thanks". `CLAUDE.md` defends these as tested and non-negotiable without eval evidence. The persuasion-principles document is candid that this is applied influence psychology, and it supplies an ethics test. Even so, a reader who finds the register manipulative is not misreading it.

---

## 12. Inventory of techniques, for reference

**Skill-writing**
TDD-for-documentation (RED-GREEN-REFACTOR) · Iron Law in a code fence · "Violating the letter is violating the spirit" · rationalization tables built from verbatim failures · Red Flags self-check lists · explicit loophole closure ("delete means delete") · Match the Form to the Failure · no nuance clauses · exemption clauses don't scope · micro-testing with a no-guidance control, 5+ reps, manual reading of every match, variance as a metric · meta-testing the failing agent · pressure scenarios with 3+ combined pressures and forced A/B/C choices · academic-vs-pressure test pairs · description = triggers only, never workflow · third person, keyword coverage, verb-first gerund naming · REQUIRED SUB-SKILL markers instead of `@`-links, used in two spine skills · flowcharts only for non-obvious decisions · one excellent example · progressive disclosure via reference files · numeric word-count budgets verified with `wc -w` · persuasion principles applied deliberately, with two of seven ruled out.

**Subagents**
Fresh subagent per task · never inherit session context · construct exactly what they need · artifacts as files, never pasted transcript · a five-part dispatch contract · brief extraction as a script · review packages as a script · plan-scoped workspaces with identity lines · a ledger that survives compaction · four-status report contract with named remedies · sub-15-line return contract · no nested subagents, stated in all four templates, worded identically in three of them · two mandatory verdicts · Do Not Trust the Report · named-risk scope budget · test budget with re-read-before-re-run · file:line evidence rule · defined severity rubric · plan-mandated tripwire · ban on pre-judging with a literal trigger list · ⚠️ cannot-verify channel routed to the controller · scoped re-reviews with ADDRESSED/NOT ADDRESSED verdicts · "'Attempted' is not addressed" · five-round breaker with adjudication only at the cap · resume for rounds 1-3, fresh + tier-up for 4-5 · ONE final fixer, no second wave · explicit model per dispatch · turn count beats token price · batching same-shape work with a file-by-file reviewer check · bounded waits with child reconciliation, adopted for visibility rather than for a better timeout rate · rulings-not-stalls with a surfaced ruling list · exactly four stop conditions.

**Engineering**
Red-green TDD with verified-for-the-right-reason RED · pristine test output · assert on behaviour, never on mocks · four-phase debugging with instrumentation before hypothesis · single-hypothesis testing · three-strike architectural circuit breaker · backward root-cause tracing · four-layer defense-in-depth · test-polluter bisection · condition-based waiting instead of timeouts · verification-before-completion with a claim→evidence table · worktree isolation detected before created, native tool preferred, `check-ignore` verified · a three-option finish menu with typed-word confirmation for destruction · zero dependencies · deterministic packaging · version-drift auditing · polyglot cross-platform hooks · shell lint by shebang detection · order-sensitive test assertions · trigger tests that flag premature action tools, with task-tracking tools exempted · per-agent token and cost accounting · hybrid deterministic + LLM-judge evals on real sessions · N=5 minimum · ranges over point estimates · negative results logged at equal billing · fixtures that survive agent forensics · a contributor policy that treats agent-authored PRs as a distinct, disclosed category.
