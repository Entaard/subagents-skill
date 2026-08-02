# Second-Round Review: A Reliable and Efficient Codex Subagent Workflow

Reviewed source: `codex-subagent-workflow-review.md`  
Review date: 2026-08-02  
Status: design discussion for a future skill; no skill is created yet

## Verdict

The first-round review is directionally strong. Its central principle—use agents to produce evidence rather than agreement—should remain the foundation.

It is not yet ready to become a skill, however. It describes good roles and quality gates, but it under-specifies the orchestration mechanics that make those roles safe and cost-effective in Codex:

- when delegation is worse than keeping work in the main thread;
- who owns the live workspace while an agent runs;
- how reviewers receive a stable implementation rather than a moving target;
- how context and decisions survive a new session;
- when a read-only reviewer cannot run meaningful verification;
- how to use follow-ups, concurrency slots, retries, and worktrees;
- how to distinguish accepted findings from reviewer assertions;
- how the workflow should degrade when an agent fails or is unavailable.

The first document optimizes a review pipeline. The future skill needs to control a stateful orchestration process.

## What should be preserved

Keep these ideas from the first round:

- Allocate model capability and reasoning effort according to uncertainty and blast radius.
- Use measurable acceptance criteria, tests, reproductions, profiling, and playable evidence.
- Keep one source-code writer at a time in a shared working tree.
- Use bounded review lenses instead of repeated generic reviews.
- Triage findings rather than applying all reviewer feedback automatically.
- Prefer targeted fix verification over another open-ended review.
- Treat human playtesting as necessary evidence for game feel and product judgment.
- Stop on an evidence-based quality gate, not when reviewers become silent.

These are sound. The changes below make them operational.

## Corrections and refinements to the first-round advice

| First-round advice | Criticism | Second-round change |
| --- | --- | --- |
| Use a plan critic before implementation | This adds a mandatory handoff even when the plan is small, reversible, or already well constrained. | Use a plan critic only when a risk trigger exists: an irreversible choice, unclear ownership, cross-system behavior, missing verification, or a large blast radius. |
| The original implementer fixes accepted findings | Continuity reduces handoff loss, but it can preserve the implementer's blind spots and assumes that the thread remains available. | Prefer a follow-up to the implementer when practical, but make this a preference rather than an invariant. The real invariant is one current writer with a complete handoff. |
| Keep reviewers read-only | A strict read-only sandbox can prevent tests, import steps, engine runs, screenshots, caches, or generated artifacts. | Separate “do not edit source” from operating-system sandbox mode. Use a strict read-only sandbox for static review; use an isolated writable environment with an explicit no-source-edit rule when verification must write. |
| Every finding must name the violated acceptance criterion | Valid findings can expose a missing criterion, implicit invariant, security rule, or integration contract. | Require the violated requirement, acceptance criterion, invariant, or risk boundary. A missing criterion may itself be the finding. |
| No blocking or important findings may remain | A reviewer can label a false positive “important,” making the gate depend on an unverified opinion. | No **accepted or evidence-backed** blocking/major finding may remain. Disputed findings must be resolved or explicitly dispositioned by the parent. |
| Run deterministic checks before review | Running an entire expensive suite before every review can waste time; running nothing wastes reviewer effort on obvious failures. | Stage checks: cheap and focused checks before review, broader checks after the candidate stabilizes, and final regression checks after fixes. |
| Use one implementation owner | Correct for a shared working tree, but unnecessarily absolute when isolated worktrees are available. | Allow parallel writers only in explicitly separate worktrees with disjoint deliverables and a named integration owner. Otherwise use one writer. |
| Use one or two review lenses | Reviewers can duplicate one another, anchor on the implementer's narrative, or inspect different states. | Give independent reviewers the same frozen diff and acceptance brief, hide the other reviewer's conclusions until both finish, then deduplicate by root cause. |
| Start each phase in a new session | A fresh session reduces context pollution but can discard decisions and repeat exploration. | Use one chat per coherent outcome. Start fresh only with a durable phase handoff that records decisions, state, constraints, and verification. |

## 1. Delegation must pass a gate

Invoking a subagent skill should not force the use of subagents. The efficient answer for a small or tightly coupled task may be zero subagents.

Delegate a task only when all of these are true:

1. It has a bounded deliverable.
2. It can make useful progress without frequent decisions from the parent or user.
3. Its required context can be packaged explicitly.
4. Its result can be checked or falsified.
5. Its workspace effects are either read-only, sequential, or isolated.

At least one of these benefits should also be material:

- it can run independently on the current critical path;
- it keeps noisy exploration, logs, or large documents out of the main context;
- it supplies a genuinely different evidence source or specialist lens;
- it is a large, cohesive implementation that benefits from a dedicated owner.

Keep the work in the main thread when it requires rapid back-and-forth judgment, changes the same files the parent is editing, is cheaper to perform than to explain, or cannot be verified independently.

This gate prevents “one agent per role” from becoming an expensive ritual.

## 2. The parent owns the state machine

The parent agent should retain responsibility for:

- the user's actual goal and non-goals;
- risk classification and delegation decisions;
- the workspace baseline and protection of pre-existing changes;
- task dependencies and concurrency;
- acceptance criteria and human-only decisions;
- triage of findings;
- final integration and verification;
- the completion claim made to the user.

These duties should not be delegated wholesale. A subagent may propose or inspect them, but the parent remains accountable for synthesis.

The parent does not always need to delegate implementation. A useful default is:

- small or tightly integrated change: parent implements;
- large but bounded increment: one worker implements;
- risky uncertainty: explorers investigate before any writer starts;
- independent review: reviewers inspect only after the implementation snapshot is stable.

While a worker owns the shared working tree, the parent should coordinate, inspect, or work on non-overlapping read-only tasks—not edit the same source concurrently.

## 3. Use an explicit phase contract

A plan is not a sufficient handoff. Before delegation, create a compact phase contract containing:

- objective and player-visible outcome;
- acceptance criteria;
- non-goals;
- relevant architecture and constraints;
- unresolved questions and who may decide them;
- starting revision or other baseline;
- pre-existing dirty files that must be preserved;
- allowed write scope;
- known dependencies and integration points;
- focused and full verification commands;
- human-only checks;
- expected output format.

If a new session is used, this contract—not the old conversation—is the source of continuity. The new parent must still compare it with the current repository and report stale assumptions.

Where the spawning surface exposes history controls, pass the smallest sufficient history plus this contract. Do not default every agent to the full conversation. Full-history forks can add irrelevant context and, on some current runtimes, constrain per-agent model or reasoning overrides. Use full history only when the delegated task truly depends on decisions that cannot be summarized safely.

## 4. Establish a workspace and snapshot protocol

Assume agents can observe the same local working tree unless the workflow explicitly creates isolated worktrees. A reviewer must not inspect a moving implementation.

Use this protocol:

1. **Baseline:** record the starting revision, working-tree status, existing changes, and task-owned files. Never treat unrelated dirty changes as the agent's work.
2. **Write lease:** name one writer for the shared tree. Other agents remain source-read-only until that writer finishes.
3. **Stabilize:** wait for the writer, run focused checks, and capture the resulting diff or changed-file manifest.
4. **Freeze:** do not modify source while independent reviewers inspect the candidate.
5. **Triage:** combine and deduplicate findings before starting fixes.
6. **New write lease:** assign one writer to accepted fixes.
7. **New snapshot:** run targeted verification against the changed candidate. Start a new full review only if the fixes materially changed behavior or design.

Do not create commits solely to manufacture a review snapshot unless committing is already authorized by the user's workflow. A stable diff, revision plus patch, or file-hash manifest is sufficient. In a non-Git project, record the task-owned file list and before/after hashes or equivalent evidence.

Parallel write-heavy work is acceptable only in separate worktrees or equivalent isolation. Each worker then needs a disjoint deliverable, an integration order, and one integration owner. “Different files” alone is not sufficient isolation because generated files, project metadata, shared registries, and tests can still collide.

## 5. Treat read-only as two different concepts

The first document uses “read-only reviewer” as if it were a single setting. It is important to distinguish:

- **Source-read-only role:** the reviewer is instructed not to modify product source.
- **Read-only sandbox:** the environment prevents writes.

Use both for static diff review. Use only the first when the reviewer must run a game engine, browser, compiler, test runner, profiler, screenshot capture, or import pipeline that writes caches and artifacts. In that case, give the reviewer an isolated writable location or worktree and prohibit source changes in the task contract.

The final skill should check what verification requires before selecting a sandbox. Otherwise, “reviewers must be read-only” can silently reduce review quality.

Set the parent turn's permission mode before spawning. Subagents inherit the parent runtime's permission and approval constraints, and live parent overrides may take precedence over defaults in a custom agent. In unattended or non-interactive runs, avoid delegating work that is likely to require a new approval; the action may fail instead of pausing for the user.

## 6. Control concurrency deliberately

Do not spawn as many agents as the runtime allows. Spawn as many **independent useful tasks** as exist.

The skill should inspect the live concurrency limit when available rather than hardcode a number. Configuration and runtime surfaces may describe limits differently, and the useful fan-out is normally lower than the maximum.

Use waves:

- exploration wave: independent unknowns only;
- implementation wave: normally one writer per working tree;
- review wave: independent lenses against one frozen snapshot;
- verification wave: targeted checks after fixes.

Maintain a small internal task ledger with the task ID, owner/thread, dependencies, write scope, state, and expected evidence. This prevents duplicate work and gives follow-up instructions a stable target without exposing orchestration noise to the user.

The parent should own the delegation graph. Nested delegation should be off by default because it obscures cost, dependencies, and workspace ownership. Allow a child to spawn its own agents only when the parent explicitly delegates a self-contained subtree with its own concurrency and write boundaries.

If a task becomes blocked, steer the existing agent or send a focused follow-up before spawning a duplicate. Retry once with a narrower brief when the failure appears recoverable. Repeated failure is a signal to reassess the task or take it back into the parent thread, not to create an unbounded agent swarm.

## 7. Make every agent contract falsifiable

Use this task contract for every subagent:

```text
Role:
Objective:
Source of truth / inputs:
Scope and relevant files:
Allowed writes:
Must not do:
Dependencies and snapshot:
Done when:
Return format:
```

Every agent should return:

```text
Status: completed | partial | blocked
Result: concise conclusion or changes made
Evidence: file/symbol references, commands, reproductions, or measurements
Files changed: exact list, or none
Checks run: command and outcome
Uncertainty: unverified assumptions and remaining risks
Recommended next action: if any
```

The parent should validate material claims from repository state or tool output. A summary is a handoff, not proof.

## 8. Improve review independence and finding quality

For independent reviewers:

- give each the same acceptance brief and frozen diff;
- give each a distinct lens;
- do not show reviewer A's findings to reviewer B before B finishes;
- do not lead with the implementer's explanation of why the code is correct;
- explicitly allow “no findings” so the reviewer is not pressured to invent criticism;
- ask the parent to deduplicate findings by root cause, not wording.

A finding should use this schema:

```text
ID:
Severity: blocker | major | minor
Confidence: high | medium | low
Location: file and symbol or line
Failure mode / impact:
Evidence or reproduction:
Violated criterion, requirement, invariant, or risk boundary:
Suggested direction:
How to verify a fix:
```

Severity needs stable definitions:

- **Blocker:** accepting the change would create a crash, corruption, security failure, broken build, unusable core path, or failure of a mandatory acceptance criterion.
- **Major:** credible user-visible incorrectness, regression, serious performance problem, or maintainability risk likely to cause near-term failure.
- **Minor:** bounded improvement that does not prevent acceptance.

Low-confidence hypotheses are useful, but they are investigation leads rather than automatic blockers. Style-only preferences should remain omitted unless they cause a concrete maintenance or correctness risk.

## 9. Use staged verification and an independent oracle when warranted

Use three levels of checks:

1. **During implementation:** the smallest tests or runtime probes that shorten the feedback loop.
2. **Before review:** focused deterministic checks that prevent reviewers from spending effort on obvious failures.
3. **Before completion:** broad regression, performance, packaging, or platform checks appropriate to the risk.

For high-risk behavior, consider a read-only test designer before implementation. It derives edge cases and black-box scenarios from requirements without seeing the eventual implementation. The single writer then implements the tests and product code. This reduces the chance that tests merely restate the implementation's assumptions.

Do not add a test-design agent for routine changes. It is justified when the behavioral state space, compatibility boundary, or cost of escape is large.

## 10. Replace the stop rule with a disposition rule

The workflow may stop when:

- mandatory acceptance criteria have objective evidence;
- required focused and broad checks pass;
- no accepted or evidence-backed blocker/major finding remains unresolved;
- each review finding is marked accepted, rejected with evidence, deferred with owner/reason, or converted into a user decision;
- fixes have received targeted regression verification;
- performance budgets pass where applicable;
- human-only checkpoints are completed or clearly reported as awaiting the user;
- unrelated pre-existing changes remain preserved;
- the final diff stays inside the authorized scope.

Default to one review wave and one targeted fix-verification wave. Start another full review only when fixes materially changed the design, control flow, data model, public contract, or diff scope.

If the same class of failure survives two fix attempts, stop patching symptoms. Reopen the assumptions, reproduction, or implementation plan. A third generic review is unlikely to solve a misunderstood problem.

## 11. Preserve the human boundary in game development

Agents can verify that an animation triggers, a frame budget passes, inputs are recognized, and a state transition occurs. They cannot establish that combat is satisfying, pacing feels right, feedback is readable to the intended audience, or the game is fun.

Mark criteria as one of:

- machine-verifiable;
- agent-observable but subjective;
- human-only.

For subjective criteria, agents may prepare a test scene, capture, instrumentation, and checklist. They must not convert those artifacts into a claim of human approval. A phase can be technically complete while explicitly awaiting a human product checkpoint.

For important mechanics, derive review lenses from the feature rather than always using the same two:

- state and behavioral correctness;
- engine lifecycle and ownership;
- determinism, save compatibility, or multiplayer;
- frame time, memory, loading, and asset import;
- controls, accessibility, and input devices;
- visual readability, audio feedback, and player comprehension.

Use only the lenses relevant to the risk.

## 12. Separate the reusable core from Godot-specific guidance

The first document alternates between a general subagent workflow and a Godot-specific review prompt. That ambiguity should not be carried into the skill.

Recommended design:

- make the core skill engine- and repository-agnostic;
- put game-development evidence and human playtest rules in a reference file;
- put Godot lifecycle, scenes, resources, signals, import behavior, and engine-specific checks in an optional Godot reference;
- load those references only when the repository or request makes them relevant.

This keeps the delegation logic reusable without diluting the game-specific review quality.

## 13. Make risk classification reproducible

The first document names low-, medium-, and high-risk modes without defining how to select one. A skill will apply them inconsistently unless the rubric is explicit.

Assess at least these axes:

- failure impact and player/data consequences;
- breadth of affected systems and coupling;
- novelty and uncertainty in the repository or engine behavior;
- reversibility and rollback cost;
- strength of automated verification and observability;
- external compatibility, platform, or human-decision dependencies.

Treat a change as high risk when a single hard trigger warrants it; do not average a severe axis away. Typical hard triggers include save/data migration, security or credentials, networking or deterministic simulation, public compatibility, irreversible content conversion, a core performance budget, or behavior with no reliable test oracle.

A large mechanical change with strong verification may be lower risk than a one-line destructive migration. Reclassify during the task when exploration reveals a different blast radius or a weaker verification path than expected.

## Revised risk-based topology

### Trivial or tightly coupled task

- Parent handles the task.
- Run relevant checks.
- No subagent merely to satisfy the workflow.

### Low-risk bounded change

- Parent or one worker implements.
- Focused automated verification.
- One review only if behavior or integration is non-obvious.
- Targeted fix verification when a material finding exists.

### Medium-risk increment

- Up to two explorers only for independent unknowns.
- One writer in the working tree.
- Focused checks before review.
- One strong, lens-specific reviewer.
- Parent triages.
- Same writer receives a follow-up when practical.
- Targeted verifier checks accepted fixes and regressions.

### High-risk increment

- Independent exploration of the few critical unknowns.
- Optional plan critic and independent test-case designer, each justified by a risk trigger.
- One writer per isolated working tree.
- Staged automated checks and runtime evidence.
- Two independent reviewers against the same frozen candidate.
- Explicit parent triage and evidence gathering for disputes.
- One fix owner and targeted regression verification.
- Human checkpoint for product, usability, or game-feel claims.

Risk, not phase size alone, selects the topology.

## Revised orchestration instruction

```text
Use subagents only when the delegation gate passes. It is valid to use none.

1. Inspect the current repository and applicable instructions. Record the baseline,
   pre-existing changes, objective, non-goals, acceptance criteria, risks, and
   verification commands in a compact phase contract.
2. Classify the increment as low, medium, or high risk. Identify which tasks are
   genuinely independent now and check the live concurrency capacity.
3. Delegate only bounded tasks with explicit inputs, write permissions, done
   conditions, and return formats. Keep nested delegation disabled unless a child
   receives an explicitly isolated subtree.
4. Use read-only explorers for material unknowns. Add a plan critic or independent
   test designer only when a named risk justifies the cost.
5. Assign one source-code writer in a shared working tree. Do not let the parent or
   another agent edit overlapping source while that write lease is active. Use
   separate worktrees and an integration owner for any parallel writers.
6. Wait for the writer, run focused checks, capture the candidate diff, and freeze
   source changes during review.
7. Give independent, lens-specific reviewers the same acceptance brief and frozen
   diff. Do not expose one reviewer's conclusions to another before both finish.
8. Require evidence-backed findings with severity, confidence, location, failure
   mode, violated criterion/invariant, and fix verification. Allow no findings.
9. Triage every finding as accepted, rejected with evidence, deferred with reason,
   or requiring a user decision. Reviewer labels do not automatically control the
   completion gate.
10. Send accepted fixes to the existing writer when practical; otherwise appoint
    one new writer with the complete handoff. Verify the fixes and regressions.
11. Start another full review only if the fixes materially changed design or scope.
    If the same failure survives two attempts, reassess the assumptions or plan.
12. Finish only when acceptance evidence, required checks, finding dispositions,
    scope integrity, and any required human checkpoint are accounted for.

Return a concise final report containing the topology used, evidence, changed files,
checks, finding dispositions, remaining uncertainty, and any human action required.
```

## Implications for the future skill

The future skill should be a decision procedure, not a prompt that always spawns an implementer, reviewer, and fixer.

Recommended initial structure:

```text
efficient-subagents/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    ├── delegation-and-risk-rubric.md
    ├── task-and-finding-contracts.md
    ├── game-development-evidence.md
    └── godot-review-lenses.md
```

Start instruction-only. Add scripts only after repeated use reveals a deterministic operation worth automating. Keep custom agent TOML definitions separate and optional until stable roles have proved useful across several real tasks.

The skill should initially require explicit invocation. Subagent workflows cost more tokens and change execution topology, so broad implicit activation on ordinary coding requests would be surprising. Configure `policy.allow_implicit_invocation: false` in `agents/openai.yaml` at first; reconsider only after testing shows that the trigger is precise.

Do not hardcode model names in the core workflow. Model availability changes. Express routing in terms of task properties—fast exploration, demanding implementation, high-confidence review—and use explicit overrides only when they materially improve the task. Reusable custom agents may later pin models if measurements justify it.

The skill also needs permission to decide: “Subagents add overhead here; I will keep this in the main thread.” That is successful use of the skill, not a failure to use it.

## Skill validation scenarios

Before adopting the skill, test at least these cases:

1. A one-file mechanical edit where the correct topology is zero subagents.
2. An unfamiliar subsystem where one explorer reduces main-context pollution.
3. A medium-risk feature where one writer and one reviewer operate sequentially.
4. A high-risk cross-system feature where bounded exploration and independent review run in waves.
5. A dirty working tree containing unrelated user changes.
6. A reviewer that must write caches or screenshots while remaining source-read-only.
7. A subagent that blocks, returns weak evidence, or becomes unavailable for fixes.
8. A non-Git project where the workflow must create a stable changed-file manifest.
9. A game-feel criterion that must remain awaiting human judgment.
10. A prompt that should not activate the skill implicitly.

Measure more than whether the task eventually passes. Record, when the surface makes it available:

- agent count and topology;
- elapsed time;
- token or usage cost;
- accepted, rejected, and duplicate findings;
- rework caused by handoff loss;
- defects found by deterministic checks versus model review;
- defects discovered after the workflow declared completion.

Run a small pilot across several representative tasks before fixing defaults. Otherwise the “cost-efficient” policy is based on intuition rather than the user's actual projects.

## Decisions to finalize before creating the skill

1. **Scope:** General orchestration with optional game/Godot references is recommended over a Godot-only skill.
2. **Activation:** Explicit-only invocation is recommended for the first version.
3. **Implementation owner:** Adaptive parent-or-worker selection is recommended; retain the one-writer invariant.
4. **Fix ownership:** Prefer the existing writer, but allow a new writer after a complete handoff.
5. **Concurrency:** Discover live capacity and use dependency waves; do not hardcode an agent count.
6. **Artifacts:** Do not create permanent plan or review files by default. Use repository conventions when they exist, and ask before adding durable process artifacts.
7. **Custom agents:** Start with built-in/general agents and role-specific task contracts; add custom agents only after recurring roles stabilize.
8. **Human gates:** Permit a technically complete status that is explicitly awaiting human playtest; never claim subjective approval on the user's behalf.

## Updated central principle

Delegate only when doing so reduces critical-path time, protects the main context, or adds independently checkable expertise. Give one parent ownership of state and decisions, one writer ownership of each working tree, and every agent a bounded, falsifiable contract. Completion comes from verified evidence and explicit finding dispositions—not agent count, reviewer agreement, or exhausted review rounds.

## Current official references

- [OpenAI: Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [OpenAI: Codex best practices](https://learn.chatgpt.com/guides/best-practices)
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills)
- [OpenAI: Git worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)

The product-specific claims in this review were checked against the current Codex manual on 2026-08-02. In particular, current guidance says subagents add token cost; are best started with bounded, independent work; can be triggered by direct requests or applicable project/skill instructions; inherit parent runtime permissions and approval constraints; and should be used cautiously for parallel write-heavy work. Custom agents can define sandbox defaults, but live parent-turn overrides may still take precedence.
