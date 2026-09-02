# Proposal: evolve Sage beyond a skill without prematurely leaving Claude Code

**Date:** 2026-08-31  
**Decision horizon:** whether to migrate Sage, and possibly the daily coding workflow, from Claude Code to the open-source Pi agent harness  
**Recommendation:** keep Sage's policy as the source of truth, keep the Claude implementation working, and build a bounded Pi-backed control-plane pilot. Do not fully migrate or fork Pi yet.

## Executive decision

There is a real gain available in Pi, but it is not the gain implied by “Pi has subagents.” Pi deliberately does **not** ship first-class subagents or plan mode. Its official subagent implementation is an example extension that launches short-lived child Pi processes. Moving the existing Sage text into a Pi skill, or lightly wrapping that example, would mostly exchange one set of harness assumptions for another and would be a poor migration.

The material opportunity is to move the parts of Sage that have deterministic predicates out of model-followed prose and into a tested control plane:

- run state and legal transitions;
- concurrency and dependency scheduling;
- writer leases and worktree ownership;
- model identity, usage, and budget accounting;
- worker lifecycle, steering, cancellation, and recovery;
- durable event recording and report projection;
- hard safety gates whose inputs are machine-observable.

Keep the parts that require judgment in a harness-neutral Sage policy package:

- whether work is safe and worth delegating;
- how to decompose by context boundary;
- which topology and evidence lens fit the risk;
- how to write a falsifiable brief;
- how to adjudicate conflicting evidence;
- what deserves promotion into memory.

In short:

> **Do not migrate Sage from “skill” to “Pi core.” Extract a Sage runtime beneath the skill, implement Pi as its first rich adapter, and retain Claude as a supported adapter.**

This makes “no migration” the default production decision. A full switch to Pi becomes justified only if a matched trial proves that the new runtime materially improves recovery, protocol compliance, or cross-provider economics without degrading answer quality or safety.

## What Sage is today

Sage's differentiator is not a special worker model. It is a carefully calibrated operating policy: model placement, context boundaries, falsifiable contracts, disjoint review, evidence-based triage, durable records, and explicit stopping conditions. Its own axioms correctly say that the parent owns the state machine and that agreement is not evidence ([`sage-claude/SKILL.md`](sage-claude/SKILL.md), especially lines 18–29).

The current implementation has three layers:

| Layer                  | Current implementation                                                                                              | Assessment                                                                                  |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Orchestration judgment | `SKILL.md`, topology and dispatch references, memory rules                                                          | Strong and portable in principle, although the text contains many Claude-specific mechanics |
| Harness controls       | Claude saved-agent definitions, tool allow-lists, model/effort settings, Agent/SendMessage/Monitor calls, worktrees | Useful real controls, but coupled to Claude Code and partly dependent on model compliance   |
| Executable support     | watchdog, ledger linter, memory indexer, one narrow pre-tool guard                                                  | Valuable instrumentation, but not a scheduler or authoritative run state machine            |

The executable pieces are intentionally narrow:

- [`sage-watch.sh`](sage-claude/bin/sage-watch.sh) parses Claude transcript JSONL and reports occupancy/status. It is notify-only and cannot establish whether a fluent result is correct.
- [`sage-lint.sh`](sage-claude/bin/sage-lint.sh) validates ledger structure and internal bookkeeping. Sage explicitly notes that it reads legality, not liveness.
- [`sage-index.sh`](sage-claude/bin/sage-index.sh) indexes knowledge items; it does not consolidate or promote them.
- [`sage-alt-guard.sh`](sage-claude/bin/sage-alt-guard.sh) is the one deliberately hard-enforced rule: it blocks an alt-agent dispatch that would accidentally override the alternate model. Its own rationale says that it was chosen because the predicate is deterministic and exception-free.

That last point gives the right design rule for this proposal:

> If a rule can be decided from structured state and forgetting it is dangerous, enforce it in code. If it requires open-ended judgment or should improve from experience, keep it in policy. If it has both parts, let policy make the decision and let code enforce the recorded decision.

### Where skill scope is currently costing Sage

The local source is unusually candid about these limits:

1. **The state machine is advisory.** Decomposition, plan completeness, dependency ordering, retry signatures, review freezes, and termination are mostly transitions the parent model must remember.
2. **The ledger is a Markdown source of truth.** It is durable and thoughtful, but the parent must update it correctly and a linter can validate only representations it can parse.
3. **Budget rails have no actuator.** Sage derives them from transcript figures and asks the parent to stop launching. It does not own an authoritative scheduler that can reject the next launch.
4. **Several safety invariants are prose-only.** The one-writer rule, off-lease writes, and successor-depth invariant are not universally enforced. Some saved-agent tool restrictions are real; plain dispatch restrictions are instructions.
5. **Monitoring depends on Claude's transcript layout.** A change in private-ish JSONL shape can silently degrade the sensor.
6. **The parent is both reasoner and process supervisor.** Sage therefore needs a complex occupancy handover protocol when the parent context grows. A non-LLM supervisor would not consume a context window at all.

These are real architectural limits. They are also not evidence that Pi is already better.

## What Pi actually provides

This analysis resolves “Pi” to Mario Zechner's Pi Agent Harness, now at the canonical [`earendil-works/pi`](https://github.com/earendil-works/pi) repository. The inspected snapshot is `@earendil-works/pi-coding-agent` **0.84.4**, released 2026-08-28 ([package metadata](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/package.json), [changelog](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/CHANGELOG.md)). The project is MIT-licensed ([license](https://github.com/earendil-works/pi/blob/main/LICENSE)).

Pi is intentionally a minimal, extensible harness. Its own README says that it skips built-in subagents and plan mode and expects users to add them through extensions or packages ([coding-agent README](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/README.md)). The relevant primitives are nevertheless strong:

- TypeScript extensions can register tools and commands, intercept and block tool calls, modify results, inject context, render UI, observe lifecycle events, and persist extension entries ([extension API](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md)).
- The SDK exposes `AgentSession`, model/thinking selection, event subscriptions, compaction, persistent or in-memory session managers, and runtime session replacement ([SDK](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/sdk.md)).
- RPC mode offers a process boundary and a structured JSONL protocol for prompting, steering, follow-ups, aborts, state, session statistics, model selection, and durable entry cursors ([RPC mode](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md)).
- `pi-ai` gives one provider-neutral tool/streaming API across OpenAI, Anthropic, Google, ZAI, Qwen plans, OpenAI-compatible endpoints, and many others ([provider list](https://github.com/earendil-works/pi/blob/main/packages/ai/README.md)). This is a concrete route to GPT, Qwen, GLM/ZAI, and local models under one worker protocol.
- Pi packages can distribute extensions, skills, prompts, and themes through pinned npm or git sources ([package system](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md)).

Pi's official [subagent example](https://github.com/earendil-works/pi/tree/main/packages/coding-agent/examples/extensions/subagent) is useful evidence of feasibility, not a production supervisor. It provides isolated child context, single/parallel/chain modes, streaming progress, usage collection, abort propagation, at most eight submitted tasks and four concurrent tasks. Its implementation launches `pi --mode json -p --no-session` for each child ([source](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/extensions/subagent/index.ts), [README](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/examples/extensions/subagent/README.md)). Consequently, it does not supply Sage's durable job graph, persistent worker handles, recovery, leases, scoped budget rails, retry semantics, or evidence adjudication.

Pi also has an important safety limitation: project trust is an input-loading decision, **not** a sandbox. Pi, its tools, and its extensions run with the invoking user's permissions. Its own guidance says unattended work needs a container, VM, micro-VM, or policy-controlled sandbox ([security](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/security.md), [containerization](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/containerization.md)). A separate Pi process provides failure and context isolation; it does not by itself provide filesystem, network, or credential isolation.

Finally, Pi is moving quickly. The inspected package is pre-1.0, and recent adjacent releases include public API and RPC event changes. Any Sage adapter should pin an exact Pi version and test the event/protocol contract at its boundary rather than importing Pi internals broadly.

## Which gains are real

| Question                                                        | Claude skill today                               | Pi skill only                               | Sage runtime with Pi adapter                                           |
| --------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------- | ---------------------------------------------------------------------- |
| Does orchestration judgment improve automatically?              | Baseline                                         | No                                          | No; policy/model quality still determines it                           |
| Can legal run transitions be enforced?                          | Mostly prose                                     | Mostly prose                                | Yes                                                                    |
| Can concurrency and dependencies be authoritative?              | Claude dispatch mechanics plus parent discipline | Example has only fixed modes                | Yes, in a scheduler                                                    |
| Can usage and liveness use supported APIs?                      | Transcript parsing                               | Better events, still ad hoc                 | Yes, normalized worker events and RPC/SDK stats                        |
| Can a run recover after supervisor restart?                     | Ledger plus model handover procedure             | No, not with the official ephemeral example | Yes, with an external event store and persistent child sessions        |
| Can the same roles use GPT, Qwen, GLM, Claude, or local models? | Possible but awkward and harness-specific        | Pi provider breadth helps                   | Yes, subject to per-provider capability tests                          |
| Is writer safety automatically better?                          | Some real Claude tool controls and worktrees     | No                                          | Only if the runtime adds worktrees and OS-level isolation              |
| Is the system easier to test?                                   | Prompt/behavior tests plus shell-script tests    | Slightly                                    | Substantially: scheduler and gates become ordinary deterministic tests |
| Is maintenance free because Pi is open source?                  | No                                               | No                                          | No; source access makes the build possible, not cheap                  |

The biggest gains are therefore **enforcement, recovery, observability, model portability, and testability**. Pi does not inherently improve decomposition, synthesis, evidence quality, or security.

## Options considered

### A. Keep Sage entirely as a Claude Code skill

This remains a valid answer and is the recommended production state during the experiment.

Choose it indefinitely when most runs are attended, use one model family, have only a few agents, and rarely fail because of missed transitions, transcript drift, or recovery. It preserves Claude Code's mature background subagents, steering, saved roles, and the calibration already encoded in Sage. It also avoids owning a TypeScript runtime and a fast-moving adapter.

Its cost is that deterministic obligations remain vulnerable to model omission and Claude-specific APIs remain embedded throughout the corpus.

### B. Port Sage to a Pi skill

Reject as the main strategy.

Pi can load Agent Skills, including paths from Claude Code and Codex ([Pi skills](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md)), but Sage's current text names Claude agents, Agent/Monitor/SendMessage semantics, transcript paths, environment variables, and hook payloads. Translating those names would make Sage run on Pi while preserving the very model-owned control plane that motivates this investigation.

This option is useful only as a cheap compatibility baseline for the later experiment.

### C. Put all of Sage into one Pi extension

Better, but not the preferred boundary.

An extension can enforce tool gates, persist state, show a good progress UI, and expose `/sage` commands. However, if the parent model invokes one blocking “subagent” tool and waits for it, the extension can become another large monolith coupled to one Pi session. A crash can still take the supervisor with the UI process, and worker restrictions still need external isolation.

Use an extension as the Pi **front end**, not as the only owner of the orchestration state machine.

### D. Build a harness-neutral Sage runtime with Pi and Claude adapters

Recommended pilot.

The runtime owns deterministic coordination. The Sage policy remains portable text and schemas. Pi supplies the first full-featured worker adapter and UI; the existing Claude skill remains usable while a thinner Claude adapter evolves.

This contains lock-in at a narrow protocol boundary. If Pi later stops fitting, the scheduler, ledger, memory events, and policies survive.

### E. Fork Pi or upstream Sage into Pi core

Reject for now.

Pi's extension, SDK, RPC, and package surfaces are already sufficient for a pilot. A fork would create continuous merge work without proving that Sage's opinionated semantics belong in Pi's deliberately minimal core. Upstream only generic primitives discovered by the pilot; keep Sage policy and its state machine in a separate package.

## Proposed architecture

```text
                         harness-neutral
                ┌────────────────────────────┐
                │ Sage policy + schemas      │
                │ topology, risk, evidence,  │
                │ briefs, triage, memory     │
                └──────────────┬─────────────┘
                               │ decisions / RunSpec
                ┌──────────────▼─────────────┐
                │ sage-core supervisor       │
                │ state machine · scheduler  │
                │ gates · event store        │
                │ budgets · leases · reports │
                └───────┬───────────┬────────┘
                        │           │
              ┌─────────▼───┐   ┌───▼────────────┐
              │ Pi adapter  │   │ Claude adapter │
              │ RPC / SDK   │   │ current skill  │
              └──────┬──────┘   │ + bridge later │
                     │          └────────────────┘
          ┌──────────▼──────────┐
          │ isolated workers    │
          │ worktree/container  │
          │ GPT/Qwen/GLM/Claude │
          └─────────────────────┘
```

### 1. `sage-policy`

Make the existing portable ideas the canonical specification, independent of tool names:

- unit qualification and decomposition rules;
- topology definitions;
- task brief, report, finding, and disposition schemas;
- risk/evidence menus;
- failure-signature policy;
- memory recognizers, falsifiers, and promotion gates.

Harness-specific model names, transcript layouts, commands, and tool availability move into adapters. The policy may still be delivered as a skill because progressive disclosure and model judgment are exactly what skills are good at.

### 2. `sage-core`

Implement a non-LLM supervisor with a small public state model:

- `Run`, `Unit`, `Attempt`, `Worker`, `Artifact`, `Finding`, `Decision`, and `Lease`;
- legal state transitions and dependency readiness;
- bounded concurrency and queue admission;
- graceful budget rails that reject new work while allowing selected in-flight work to settle;
- exclusive write leases and isolated-worktree allocation;
- worker event normalization, health, usage, and context pressure;
- steering, cancellation, retry, and failure-signature history;
- an append-only machine-readable event log, with the current Markdown ledger rendered as a human view rather than used as the database;
- crash recovery by replaying the event log and reconnecting to or classifying workers;
- Markdown report and memory-journal candidate generation.

Keep memory promotion user-gated. The runtime can record observations exactly; it should not decide that a lesson has earned promotion.

### 3. `sage-adapter-pi`

Use persistent Pi RPC worker processes first. RPC exposes the useful lifecycle operations directly and keeps each worker's context and failure domain separate. Each worker should have:

- a persistent named session and parent-run identifier;
- an explicit provider/model/thinking selection recorded after resolution;
- a role-specific active tool set;
- structured streaming events, session statistics, and a stable entry cursor;
- direct steer/follow-up/abort operations;
- a dedicated worktree or sandbox when it can write.

The Pi SDK is attractive for trusted, read-only pools or tests because it avoids subprocess overhead and exposes typed `AgentSession`s. It should not be confused with a security boundary. Use the RPC/process path for the initial production-shaped pilot because crash isolation and persistent child sessions matter more than a small startup saving.

Do **not** base recovery on the official example's `--no-session` behavior. Reuse its useful parsing, streaming, rendering, and abort ideas, then replace its dispatcher and persistence model.

### 4. `sage-ui-pi`

Ship a thin Pi extension/package that provides:

- `/sage`, `/sage status`, `/sage report`, `/sage resume`, and `/sage stop`;
- live unit cards and aggregate cost/context indicators;
- explicit user approval surfaces for destructive or external actions;
- tool-call gates for the Pi front-end process;
- links to worker sessions and artifacts.

The extension talks to `sage-core`; it does not own the only copy of run state.

### 5. Isolation and safety

Use layers rather than trusting tool names alone:

1. readers get no write or shell tools when possible;
2. one writer gets one worktree lease;
3. tool-call hooks block deterministic forbidden calls and validate recorded lease metadata;
4. writers run in a container, micro-VM, or policy sandbox when unmonitored or handling untrusted content;
5. destructive/external actions always require a human release recorded before execution.

A Bash-capable model can write by many routes, so string inspection of shell commands is not a complete lease boundary. OS/worktree isolation remains required.

## Phased experiment

### Phase 0 — extract the protocol without changing behavior

- Separate portable Sage policy from Claude mechanics.
- Define versioned JSON schemas for `RunSpec`, worker events, results, findings, and run records.
- Capture a representative set of existing Sage runs and known failure cases as replay fixtures.
- Keep the current Claude skill production-capable throughout.

Exit criterion: the existing Claude behavior can still be described by the new schemas without deleting any safety or evidence obligation.

### Phase 1 — reader-only Pi prototype

- Implement `sage-core` scheduling for independent read-only units.
- Add a persistent Pi RPC worker adapter with per-worker model selection, events, usage, steering, abort, and restart recovery.
- Render the current Markdown-style ledger from structured events.
- Exercise at least three provider families: one OpenAI/GPT model, one Qwen model, and one ZAI/GLM or Anthropic model.

Exit criterion: a research sweep can be killed and resumed without reconstructing state from model memory, and the same `RunSpec` works across the selected providers.

### Phase 2 — enforcement and fault injection

- Add admission budgets, failure signatures, retries, leases, and worktree allocation.
- Load the safety extension into every Pi worker, not only the root UI session.
- Test process crash, provider error, malformed report, over-budget launch, stuck worker, duplicate completion, and supervisor restart.

Exit criterion: illegal transitions are rejected, run replay is idempotent, and every injected failure has an explicit terminal or recoverable state.

### Phase 3 — writer safety

- Add one-writer and isolated-parallel-writer flows.
- Run off-lease write and destructive-command attacks in disposable repositories and containers.
- Add deterministic compose checks and preservation checks for pre-existing dirty work.

Exit criterion: no shared-tree corruption; all injected destructive and off-lease actions are blocked before mutation.

### Phase 4 — matched decision trial

Run at least 20 paired tasks through current Sage-on-Claude and the hybrid, stratified across research, review, implementation, long-running recovery, and model-diversity cases. Use the same requirements, acceptance rubric, and comparable model budgets. Score outcomes blind to the harness where practical.

Adopt the hybrid for orchestration-heavy work only if all hard gates pass:

- quality is no worse than one task out of 20 relative to the baseline;
- at least 19 of 20 forced-restart trials recover the exact run state;
- all injected destructive and off-lease mutations are blocked;
- no shared-tree corruption occurs;
- every quoted usage/cost figure reconciles with worker session statistics;
- one unchanged run specification executes across at least three provider families.

And at least two material benefit gates pass:

- at least 25% fewer protocol failures or human orchestration interventions;
- at least 20% lower wall time on tasks with three or more independent units at comparable quality and spend;
- at least 10% lower quality-adjusted cost;
- at least 50% lower parent/orchestrator token occupancy;
- successful recovery after supervisor restart without a model-authored handover.

Hold quality-adjusted cost below 1.25× the Claude baseline even if other gains are strong. During the trial, pin Pi and deliberately test upgrades; more than one adapter-breaking upgrade is a warning that the maintenance boundary is too broad.

These thresholds are proposed decision criteria, not measured predictions.

## Cost and risk

Order-of-magnitude engineering estimates, not measurements:

| Deliverable                                | Likely effort                    | Main risk                                                                |
| ------------------------------------------ | -------------------------------- | ------------------------------------------------------------------------ |
| Skill-only Pi translation                  | A few days                       | Produces little architectural gain and may look more complete than it is |
| Reader-only runtime/Pi spike               | Several focused engineering days | Provider and RPC semantics differ from docs under real load              |
| Production-shaped hybrid                   | Several weeks                    | Recovery, isolation, and adapter conformance are the real work           |
| Full behavioral parity plus full migration | Multiple months                  | Rebuilding calibrated edge cases while Pi APIs continue to move          |

The largest risks are:

- rebuilding Sage's accumulated judgment as rigid code and losing its adaptability;
- mistaking a Pi process boundary for a sandbox;
- letting provider breadth hide behavioral differences in tool use, context handling, and reasoning controls;
- coupling directly to Pi internals instead of the documented SDK/RPC/extension surfaces;
- measuring more telemetry without improving task outcomes;
- running two implementations long enough that their policies drift.

Mitigations are a single canonical policy package, generated adapter conformance tests, an exact Pi version pin, replay fixtures from real Sage failures, and a short trial with an explicit stop decision.

## Final recommendation

The answer to “should I migrate from Claude Code to Pi now for Sage?” is **no**.

The answer to “is there value in thinking outside skills?” is **yes**. Sage has reached the point where a skill is the right home for its judgment but the wrong home for its entire control plane. Pi is a good place to prototype the missing runtime because it is open source, MIT-licensed, provider-neutral, embeddable, and unusually extensible. It is not a reason to discard Claude Code, and its lack of a native supervisor means the gain has to be built and measured.

Proceed with option D as a bounded experiment:

1. preserve Sage policy and the current Claude implementation;
2. extract deterministic orchestration into `sage-core`;
3. build Pi as the first rich adapter and UI, without forking Pi;
4. run the paired trial;
5. keep Sage skill-only if the hard gates or benefit gates do not pass.

That path captures Pi's real advantage—programmable authority—without betting Sage's proven policy on an unproven rewrite.

## Evidence and limitations

This proposal is based on:

- a complete read of the current Sage skill plus its dispatch, topology, harness, memory, watchdog, linter, indexer, guard, and related design material;
- syntax checks of the four Sage shell scripts;
- a clean Sage corpus lint and passing alt-guard self-test;
- current primary Pi repository documentation and source, inspected on 2026-08-31 at package version 0.84.4;
- three independent research lenses: Sage internals, Pi capabilities, and an adversarial migration review.

No live Pi implementation or matched-task benchmark was run. Claims about expected productivity, portability, and quality gains therefore remain hypotheses until Phase 4. The recommendation deliberately keeps “stay with the Claude skill” as the outcome if those hypotheses fail.
