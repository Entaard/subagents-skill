# Proposal: build Sage for Codex with a portable seam

**Date:** 2026-08-31
**Decision horizon:** how to implement Sage for Codex now without making Codex the permanent definition of Sage
**Recommendation:** build Codex first, not Codex-only. Ship an explicit Codex skill in Light mode. If matched trials show that deterministic coordination is worth its cost, add one external `sage-core`, one store, and one Codex driver for Managed mode. Keep the driver seam and runtime protocol provisional while Codex is the only real adapter; do not pay for a second harness merely to prove an abstraction. Treat plugins and hooks as optional Codex UX and guard clients, never as a second control plane.

## Executive decision

The prior architecture's central decision is right:

> Keep judgment in Sage policy. Move machine-decidable coordination into code. Put harness APIs behind adapters.

For Codex, however, that should not become a big-bang runtime rewrite. Current Codex already supplies native skills, subagent threads, explicit child model and reasoning selection, steering and interruption, lifecycle hooks, worktrees, sandboxes, and programmatic thread control. Those primitives support a useful Sage implementation before an authoritative supervisor exists. They do not, by themselves, provide Sage's run graph, cross-run resource coordination, aggregate admission policy, recovery semantics, or evidence adjudication.

Build two operating modes from one policy source:

1. **Light mode:** Sage's control flow is fully Codex-native. The explicit Sage skill and its references tell the Codex root how to qualify, plan, dispatch native Codex subagents, supervise, verify, hand over, and emit run artifacts. Small validators, renderers, and append-only logging helpers are allowed, but there is no external Sage scheduler or authoritative run-state process. Because the parent model owns bookkeeping, coordination and recovery guarantees are advisory.
2. **Managed mode:** Sage keeps the same policy judgments, but one external `sage-core` owns admission, scheduling, durable run state, and deterministic recovery; one deployment-wide coordinator arbitrates mutable-resource leases. The first implementation has one Codex driver controlling persistent Codex threads through a capability-tested SDK or App Server integration. The skill, `sagectl`, MCP surface, plugin, and hooks are least-privilege clients of that same core; none owns another state machine.

Managed mode is conditional, not the assumed endpoint. Build it only if an early paired Codex trial first establishes Sage's policy value, then exposes residual coordination, recovery, or context-pressure failures attributable to mechanisms the core would own and costly enough to justify its operational burden.

The proposal is therefore not "translate the Claude skill to Codex" and not "put Sage into Codex core." It is:

> **Extract one portable Sage policy, make Codex the first complete experience, let measured Codex failures decide whether Managed mode exists, and make every stronger guarantee depend on an effective capability rather than on the harness name. Do not call the runtime seam cross-harness-stable until a second real adapter eventually proves it.**

## Design goals

1. **Codex-native now.** Use Codex's documented skill, subagent, hook, sandbox, worktree, SDK, and App Server surfaces, with maturity gates where required. Do not parse private transcript layouts when a supported event exists.
2. **Portable without speculative adapters.** Keep policy and artifacts free of Codex mechanics, but implement only Codex in this plan. With one production adapter, the cross-harness seam is hypothetical and the runtime protocol remains provisional. A second adapter is a later product decision, not a prerequisite for learning whether managed Codex is useful.
3. **One owner per rule.** Keep the six-step orchestration spine together and split conditional mechanisms by responsibility, not by phase. This follows the repository's prior decomposition finding ([`2026-08-24-sage-decomposition.md`](2026-08-24-sage-decomposition.md), especially `## 6`).
4. **Truthful guarantees.** Record availability, authority, scope, delivery, durability, and failure behavior for each relevant operation. Reject missing required predicates; never silently pretend an instruction is a sandbox or an ephemeral event stream is replayable.
5. **Deterministic predicates in code.** Dependency readiness, concurrency admission, event ordering, legal transitions, dispatch tickets, exclusive leases, and idempotency belong in `sage-core`.
6. **Judgment in policy.** Decomposition, model fit, topology, evidence lenses, triage, and memory promotion remain model or human decisions.
7. **Log only during a run.** Runtime retrieval reads canonical policy and already-promoted knowledge only. It does not scan raw journals, prior run ledgers, or closed-run logs for ad hoc lessons or same-shape precedents. Record the current run's observations and outcomes exactly, without consolidating them or turning them into lessons. A separate user-invoked promotion workflow later reads those logs, derives candidate knowledge, tests it, and promotes what survives.
8. **Useful without lowest-common-denominator design.** Rich adapters keep steering, durable sessions, approvals, usage, and event cursors where available. A weaker adapter declares the gap instead of reducing every worker to `prompt -> text`.
9. **One lifecycle entrypoint per action.** One repository-root `install.sh` installs or updates Sage, and one repository-root `uninstall.sh` removes the complete Sage-owned installation. Both modes use the same scripts and ownership manifest.

## Non-goals

- Reimplement Codex inside Sage.
- Make policy decisions deterministic merely because a state machine exists.
- Guarantee writer isolation with prompt text, command-string inspection, or a worktree alone.
- Automatically promote memory or edit Sage's own policy during a run.
- Build a custom progress UI before the native Codex thread UI and a generated Markdown report prove insufficient.
- Implement or schedule a second harness adapter in this plan.
- Claim that the managed runtime protocol is cross-harness-stable while Codex is its only production adapter.
- Enable the exploratory lower-tier lane in [`ideas.md`](ideas.md) by default. That is a later experiment with its own evaluation, not an architectural invariant.
- Promise autonomous recovery across a judgment boundary unless a durable policy-actor thread is explicitly configured.

## What Codex provides, and what it does not

### Supported primitives to use

Current Codex releases provide the following useful boundaries:

- Skills use progressive disclosure, support explicit `$skill-name` invocation, and can be distributed in plugins. Codex can disable implicit invocation through `agents/openai.yaml` while retaining explicit use ([official skill documentation](https://learn.chatgpt.com/docs/build-skills)).
- Subagent workflows can be requested by the user or by applicable skill instructions. Codex supports child model and reasoning selection, custom agents, configurable concurrency, inspection, steering, stopping, and follow-up work ([official subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)).
- Hooks cover `SessionStart`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, compaction, subagent start/stop, and root `Stop`. `PreToolUse` can see `spawn_agent` as `Agent` and can deny supported local tool calls before execution ([official hooks documentation](https://learn.chatgpt.com/docs/hooks)).
- Codex worktrees provide separate Git working copies. Sandboxes and approval policies separately control filesystem, network, and escalation behavior ([official worktree documentation](https://learn.chatgpt.com/docs/environments/git-worktrees), [official security documentation](https://learn.chatgpt.com/docs/agent-approvals-security)).
- The Codex App Server exposes a JSON-RPC 2.0 interface for thread start/resume/fork, turn start/steer/interrupt, approvals, persisted thread history, models, skills, hooks, usage events, diffs, and collaboration events. Generated schemas are specific to the Codex binary, and experimental fields require explicit client opt-in ([official App Server documentation](https://learn.chatgpt.com/docs/app-server)).
- The Codex SDK can start, continue, and resume local Codex threads and set sandbox policy per thread or turn ([official Codex SDK documentation](https://learn.chatgpt.com/docs/codex-sdk)).

### Boundaries not to overstate

Codex does not make Sage automatic:

1. A skill is instructions and resources, not an authoritative scheduler.
2. Native subagent calls are initiated by a model. Without a trusted gate, the model can omit a state update or launch outside the plan.
3. Project and plugin hooks can be skipped until the user trusts them. Tool hooks also do not cover every hosted or specialized tool path.
4. `SubagentStart` can inject context but cannot stop a child. Admission must happen before `Agent` execution, not at the start event.
5. `PostToolUse` observes an action after its side effects and cannot undo a write.
6. Child permission and sandbox behavior depends on the effective parent runtime and configuration. A role name such as `reader` is not proof of read-only isolation.
7. A worktree separates Git state; it is not an OS, credential, or network sandbox.
8. Codex thread goals and token telemetry are per-thread facilities, not Sage's aggregate run admission policy.
9. Native child completion does not by itself define crash recovery after the root supervisor disappears.
10. Hook `transcript_path` is convenient, but official documentation says the transcript format is not stable. It must not become Sage's primary protocol.
11. The current `codex app-server` command is documented as experimental and unsupported for production workloads. The SDK is the recommended automation path, but it does not automatically expose every App Server lifecycle operation.
12. Plugins are not available in every Codex surface, including the IDE extension. The standalone skill must remain usable without plugin packaging.

These limitations argue for progressive enforcement, not for discarding Codex's native experience.

## Proposed architecture

```text
                       canonical, harness-neutral

             +----------------------+  +----------------------+
             | sage-policy          |  | artifact schema v1   |
             | judgment + workflow  |  | briefs/results/runs   |
             +----------+-----------+  +-----------+----------+
                        |                          |
             +----------v--------------------------v----------+
             | host experience                                |
             | Codex skill                                    |
             +------------------------+------------------------+
                                      |
                    Light mode        |        Managed mode
             native workers,          |   policy requests only
             advisory ledger          |
                                      v
                         +------------+-------------+
                         | sage-core                 |
                         | sole run-state owner      |
                         | scheduler + reconciliation|
                         +------+-------------+------+
                                |             |
                      worker port|             |resource/isolation/approval
                +---------------+------------------------------+
                                |                              |
                        +-------v-------+               +------v-------+
                        | Codex driver  |               | test adapter |
                        | SDK/App Server|               | in-memory    |
                        +---------------+               +--------------+

        Codex plugin hooks and sagectl are optional clients/sensors.
        They never own a second database or scheduler.
```

The source dependency points inward:

- Policy depends first on the small portable artifact vocabulary, never on a harness tool name.
- Core depends on the provisional runtime interface exercised by the Codex driver, never on Codex packages directly.
- The Codex driver and the in-memory test adapter satisfy that interface. This makes the core testable; it does not prove cross-harness portability.
- Skills/plugins are experience layers. They may call a role-limited core API, but they do not own a second copy of policy or state.

### 1. `sage-policy`

Keep the following as canonical, harness-neutral text:

- the four Sage axioms;
- safe/worth delegation tests;
- decomposition by context boundary;
- topology selection;
- abstract model placement and evidence requirements;
- brief, report, finding, and disposition semantics;
- failure-signature diagnosis;
- verification, review, and conflict adjudication;
- assumptions, gaps, `AwaitingHuman`, and coordination-outcome semantics;
- completion and human-only criteria;
- the rule that promotion is a separate user action.

Remove these from canonical policy:

- host-specific tool names;
- transcript paths and environment-specific token arithmetic;
- concrete model aliases;
- harness concurrency defaults;
- hook payload layouts;
- installation or package-manager mechanics.

Those belong to adapter references. Portable policy describes task requirements rather than imposing a total cross-provider model ordering: corpus size, ambiguity, step count, tool needs, latency preference, cost ceiling, independence requirement, and verification criticality. Each harness owns a calibrated placement profile that resolves those requirements to an exact current model and effort, and records both requested and effective values. Familiar labels such as `fast` or `frontier` may exist inside one profile, but are not protocol semantics. A user-specified concrete model is preserved rather than reinterpreted.

### 2. Portable artifacts and a provisional runtime protocol

Do not freeze one large protocol from a single Codex implementation. Split it:

- **Artifact schema v1:** portable and intentionally small. It covers `RunPlan`, `PlanRevision`, `UnitSpecRevision`, briefs, results, artifacts, assumptions, gaps, findings, dispositions, verification evidence, coordination outcome, and the rendered run record. Light mode and Managed mode both emit it.
- **Runtime protocol v0 provisional:** commands, principals, worker/turn handles, capability offers and snapshots, normalized observations, approvals, leases, and recovery state. Derive only what the Codex managed slice and its fault tests need. It may become a stable Codex contract after those tests, but it is not called cross-harness v1 while Codex is the sole production adapter.

Publish JSON Schemas and generated language types. JSON is the wire format; the implementation language is not part of the contract. A later, separately approved second-harness project may revise v0 before declaring a portable v1; the current plan does not implement or review that adapter.

#### Plans are immutable revisions, not immutable forever

A single immutable `RunSpec` would conflict with Sage's legitimate re-planning, failure ladder, unknown-size discovery, and follow-up review rounds. Instead:

- an optional bounded bootstrap revision may contain only read-only discovery units needed to build the first complete plan;
- every admitted plan is an immutable numbered revision;
- changing dependencies, criteria, scope, or units creates `PlanRevision N+1` with a reason and expected prior revision;
- every logical unit has a stable ID and immutable `UnitSpecRevision`s;
- a later plan explicitly marks each prior unit revision `carried`, `superseded`, or `removed`;
- reuse of an earlier result requires a recorded adoption decision against the new criteria;
- admissions pause while a new revision commits;
- each attempt binds to the exact plan revision, unit-spec revision, and brief hash it received;
- an in-flight attempt is never silently redefined by a later plan;
- the transition audit retains every prior revision.

This keeps history auditable without freezing a plan that evidence has disproved.

#### Requests, transitions, and observations are different

Requests express intent and carry preconditions. State transitions and audit observations record what was accepted or observed. Privilege is determined by the authenticated connection principal, never by caller-supplied fields inside a payload.

Connection-scoped principals are:

- `operator`: may create, stop, resume, delete, and approve within explicit scope;
- `policy_actor`: may propose plans, briefs, findings, verification, and dispositions;
- `scheduler`: an internal core principal that alone admits attempts and grants run-local dispatch tickets;
- `adapter`: may report only native facts for handles that core assigned to that adapter connection;
- `approval_channel`: may attest a human decision after authenticating the operator and binding the exact action digest;
- `worker`: may submit a result or artifact for its own attempt and nothing privileged.

The local transport uses separate role-specific endpoints and unforgeable, short-lived capabilities. OS peer credentials are supporting evidence, not sufficient separation when every process runs as one user. The model calls a narrow MCP broker whose policy capability is held by the broker, not placed in model-visible environment variables, files, arguments, or tool output. The store, scheduler/adapter endpoints, and resource-coordinator credentials remain outside the policy actor's and workers' sandboxes. A separate approval broker owns operator authentication; its credentials never enter a model process. If the host cannot enforce those reachability boundaries, managed writer or unattended guarantees are unavailable.

The model-callable MCP or CLI surface exposes only `policy_actor` operations. It cannot call `GrantLease`, manufacture an approval, bind an arbitrary worker, or close a run as the operator. A shell-capable policy actor must not be able to open the privileged sockets, read the store, or obtain their tokens.

Examples of requests and internal transitions:

- `CreateRun`
- `ProposePlanRevision`
- `CommitPlanRevision` (core after validation)
- `AdmitAttempt`
- `BindWorker`
- `SteerAttempt`
- `InterruptAttempt`
- `RecordFinding`
- `DispositionFinding`
- `AcceptResult`
- `RecordVerification`
- `AdoptArtifact`
- `GrantLease`
- `ReleaseLease`
- `RecordApproval`
- `BeginDrain`
- `CloseRun`

Every mutating request includes `command_id`, `run_id`, a principal-bound idempotency key, and, except `CreateRun`, `expected_run_version`. Idempotency lookup happens before optimistic-version validation: the same key and canonical request hash returns the stored result, while the same key with a different body is rejected. `CreateRun` uses no prior version. The core either rejects the request with a typed reason or commits state and its audit records atomically. An adapter observation never bypasses transition validation by mutating state directly.

#### Normalized observation envelope

Every persisted native observation should carry at least:

```json
{
  "schema_version": "0.1",
  "event_id": "evt_...",
  "run_seq": 42,
  "occurred_at": "2026-08-31T00:00:00Z",
  "observed_at": "2026-08-31T00:00:01Z",
  "run_id": "run_...",
  "unit_id": "U3",
  "attempt_id": "U3-A2",
  "worker_ref": "opaque adapter-owned reference",
  "causation_id": null,
  "adapter": "codex",
  "adapter_version": "...",
  "source_event_id": "...",
  "source_epoch": "connection-or-session epoch",
  "source_seq": 7,
  "source_cursor": "...",
  "delivery": "snapshot-reconcilable",
  "type": "worker.completed",
  "payload": {}
}
```

`run_seq` orders ingestion into Sage; it does not claim causal order across workers. Use native per-source epoch/sequence where available, detect gaps explicitly, and treat timestamps as evidence rather than ordering. `causation_id`, source IDs, cursor, and sequence are nullable when the harness does not supply them. Each adapter declares delivery as `replayable`, `snapshot-reconcilable`, or `ephemeral`; Codex is snapshot-reconcilable unless a pinned live probe proves a stronger guarantee. Deduplicate only where the native identity is stable.

Canonical transition and observation types include:

- plan and admission events;
- worker accepted, started, idle, completed, interrupted, failed, lost, and unknown;
- turn and message lifecycle events;
- tool started/completed and approval requested/resolved;
- usage and context-pressure updates with provenance;
- artifact and result receipt;
- finding and disposition events;
- lease and approval events;
- compaction and recovery events.

`idle`, `turn.completed`, `result.received`, `result.accepted`, and `verification.recorded` are distinct. A unit completes only after a valid result is accepted, the worker reaches the required terminal condition, and the policy actor or operator records the required verification. `CloseRun` rejects any unit or finding without an explicit final state, including `AwaitingHuman` where policy requires the run to pause instead.

### 3. Capability negotiation

The core must not branch on `adapter == "codex"`. It evaluates operation-specific capability predicates.

An adapter first returns an **environment offer** for a concrete binary version, cwd, configuration, credentials, hook trust hash, and approval policy. Worker preparation and every turn then return an **effective capability snapshot**. A capability record separates:

- versioned semantic operation and availability;
- authority source and trust state;
- scope: run, worker, turn, tool family, resource, or workspace;
- control strength where relevant: `enforced`, `advisory`, or `none`;
- delivery: `replayable`, `snapshot-reconcilable`, or `ephemeral`;
- durability and restart boundary;
- failure behavior: `fail-closed`, `fail-open`, or `unknown`;
- evidence and known uncovered paths.

`resume`, for example, is a lifecycle semantic with a durability boundary, not something meaningfully called "enforced." A trusted `PreToolUse` denial can be enforced for its covered path while still being fail-open on hook error and incomplete for specialized tools.

Important capability families:

| Family | Examples |
| --- | --- |
| Lifecycle | start, durable resume, steer in flight, follow up, interrupt, inspect, event cursor |
| Model | list models, select model, select reasoning effort, observe resolved identity |
| Context | blank context, recent-turn seed, full-history seed, context pressure, compaction event |
| Control | pre-tool deny, input rewrite, structured result validation, interactive approval |
| Isolation | read-only sandbox, workspace sandbox, dedicated worktree, process/container isolation |
| Observability | lifecycle events, tool events, token usage, cost provenance, diff events |
| Topology | parent/child identity, concurrency control, background execution, nested delegation |

A plan declares predicates as `required` or `preferred`.

- A false `required` predicate rejects that attempt's admission or requires a new plan revision.
- A false `preferred` predicate invokes a named fallback, such as serial execution or parent-owned work.
- No adapter silently emulates `resume`, `read-only`, or `resolved_model` with prompt text.

Record the environment offer before planning and the effective snapshot beside every admission, approval, and control decision. Emit `capability.degraded` or `capability.restored` when configuration, hook trust, model, sandbox, or transport changes. The run summary is a projection of those facts, not one immutable startup label.

Degradation is a state-machine input, not telemetry alone. When a required predicate becomes false, stop new admissions. If it protects safety or side effects, quiesce or interrupt affected attempts; if quiescence cannot be proven, mark them `unknown`, freeze result acceptance and resource reuse, and require plan revision or human disposition. A non-safety preferred capability may take its pre-declared fallback. Restoration never retroactively validates work performed during the gap.

### 4. `sage-core`

The core owns only deterministic coordination:

- legal state transitions;
- dependency readiness and acyclic plan validation;
- concurrency and admission policy;
- attempt identity and retry history;
- dispatch tickets;
- deployment-coordinated resource leases and fencing tokens;
- adapter observation normalization and deduplication;
- worker reconciliation after restart;
- approval records;
- structured projections and report rendering.

The public domain model should include:

`Run`, `PlanRevision`, `Unit`, `UnitSpecRevision`, `BriefRevision`, `Attempt`, `Worker`, `Turn`, `Artifact`, `Assumption`, `Gap`, `Finding`, `Disposition`, `Verification`, `CoordinationOutcome`, `Decision`, `Resource`, `Lease`, `Approval`, and `CapabilitySnapshot`.

The core does not decide:

- whether a unit is worth delegation;
- whether a model is intelligent enough for an ambiguous task;
- which finding is true;
- whether evidence is persuasive;
- whether an observation is a reusable lesson.

Policy or a human decides those things. The core validates and records the decision's machine-checkable shape.

#### Transactional state and audit

Do not require full event sourcing before the pilot proves it necessary. Use one transactional store behind `RunStore`, initially SQLite in WAL mode, containing:

- authoritative current-state tables with optimistic versions;
- idempotency records and stored request results;
- an append-only transition audit;
- an outbox/inbox for external operations and native observations;
- resource identities plus cached coordinator lease references;
- disposable Markdown/UI projections.

A transition updates state and appends its audit/outbox records in one transaction. Recovery must be demonstrable from the authoritative state plus audit, but the pilot need not rebuild every byte of state from raw native events. Promote the audit to full replayable event sourcing only if a named recovery, migration, or compliance invariant cannot be met otherwise.

SQLite is an implementation choice, not part of the adapter protocol. Adapters never read tables directly. If multi-host scheduling or packaging outgrows it, replace `RunStore` without changing domain semantics.

Privacy is part of the schema, not a cleanup item. Classify fields before persistence, redact before writing, default to a hash plus protected locator instead of raw prompts/tool payloads, restrict store and artifact permissions, attach retention/deletion policy to each run, and require sanitized fixtures. Raw payload retention is opt-in when audit needs it; a hash alone is not represented as a retained raw record.

#### Recovery

After a supervisor restart:

1. Load authoritative state and verify the audit/outbox consistency checkpoint.
2. Reconcile every unresolved outbox intent, including `sent/unknown` operations with no returned handle, before reconciling nonterminal `WorkerRef` and `TurnRef` snapshots; fetch events after a stored cursor only where replay is actually supported.
3. Classify each as `prepared`, `running`, `idle`, `completed`, `failed`, `lost`, or `unknown`.
4. Validate result and artifact hashes before accepting a completion.
5. Never repeat a potentially side-effecting attempt or turn in `unknown` state until reconciliation or human disposition.
6. Create a new attempt rather than rewriting the old attempt's history.
7. Resume deterministic scheduling only after reconciliation closes every ambiguity.
8. At the next decomposition, triage, evidence, or replanning boundary, enter `AwaitingPolicy` unless a separately persisted policy-actor thread is configured and reconciled.

Managed recovery therefore means deterministic state and worker recovery, not automatic replacement of model judgment. In an ordinary interactive Codex session, `$sage resume <run-id>` supplies the next policy actor after a root loss.

#### Deployment-wide resources

Every mutable target has a canonical `ResourceId` derived by the isolation provider from the real workspace/worktree identity, not from a caller's display path. Lease authority lives in a `ResourceCoordinator` outside any one `RunStore`. Every core in a managed deployment must use the same coordinator. A local implementation may be a single coordinator daemon; it may use an OS lock for singleton election, but a raw OS lock provides mutual exclusion rather than authoritative epochs/fencing. Monotonic tokens and stale-owner rejection require a durable registry plus validating write paths. A distributed deployment needs a real consensus-backed lease service.

The coordinator atomically grants one owner epoch and monotonically increasing fencing token across runs and stores. It supports acquire, renew, quiesce, revoke, and release, and permits takeover only after the previous owner is confirmed quiescent or the isolation boundary is destroyed. A core that cannot reach or acquire the configured coordinator rejects writer admission. Two unrelated SQLite files are not coordination, and the proposal makes no universal claim about a separately configured Sage deployment that ignores the coordinator.

This guarantee covers Sage-managed actors in one configured deployment only. A user, editor, unrelated process, or misconfigured second deployment can still mutate the checkout. Fencing is authoritative only on a write path that validates the token; otherwise OS sandboxing or an isolated worktree is the boundary and the lease is coordination metadata.

### 5. Worker adapter ports

Do not model a worker as a process, session, or Codex subagent. Keep opaque worker and turn references:

```text
WorkerRef = {
  adapter,
  native_id,
  parent_ref?,
  durable,
  event_cursor?,
  requested_model,
  effective_model?,
  effective_permissions?,
  isolation_ref?
}

TurnRef = {
  worker_ref,
  native_turn_id,
  expected_worker_version,
  started_at,
  side_effect_class
}
```

The runtime v0 surface is semantic rather than a one-for-one wrapper of a host API, but it does not erase turn identity or ordering:

```text
offer(environment_request) -> EnvironmentOffer
prepare_worker(worker_request, dispatch_key) -> PreparedWorker
start_turn(worker_ref, input, expected_no_active_turn) -> TurnRef
steer_turn(turn_ref, expected_native_turn_id, input)        optional
start_follow_up(worker_ref, input, expected_idle_version)   optional
interrupt_turn(turn_ref, expected_native_turn_id)
reconcile(worker_ref) -> WorkerSnapshot
observe(worker_ref, checkpoint?) -> Observation stream      optional
dispose_worker(worker_ref)                                  optional
```

Unsupported operations return typed `unsupported` results. Each operation declares ordering and delivery semantics. In particular, an adapter must not call a queued-after-tool-round behavior equivalent to active-turn steering. An adapter may expose richer private helpers, but `sage-core` depends only on the proven semantic contract.

#### Crash-safe dispatch

Worker creation is an external transaction boundary. Use a durable protocol:

1. Commit `DispatchIntent` and an outbox operation.
2. Prepare a worker without starting a model turn where the harness supports it; do not assume preparation is side-effect-free.
3. Persist the returned `WorkerRef` and effective capability snapshot.
4. Commit `StartTurnIntent`, then invoke `start_turn` exactly once.
5. Persist `TurnRef`; on any ambiguous response, reconcile before issuing another turn.

For Codex App Server, `thread/start` can prepare the thread and `turn/start` can begin model work. Preparation can still initialize MCP servers or run session-start hooks, so it may have external effects. A crash between successful thread creation and persisting its server-generated ID leaves a `sent/unknown` intent because `thread/start` has no documented durable request idempotency or caller-supplied durable creation key. The JSON-RPC request ID correlates a response; it does not establish replay-safe creation. The adapter must discover the worker through a proven mechanism or pause for operator disposition; it must never retry the unknown start. Side-effecting unattended preparation requires a verified side-effect-free/idempotent startup profile or a discoverable native creation key.

A crash around `turn/start` is reconciled from the persisted worker and thread snapshot before any retry. Drivers that cannot split prepare from execute declare that limitation and are not admitted for side-effecting unattended work. Add fault points before and after every external and isolation operation, and make unresolved intents first-class recovery inputs even when no opaque handle was returned.

Separate execution concerns behind adjacent ports:

- `ResourceCoordinator`: acquire, renew, quiesce, revoke, and release deployment-wide resource ownership with an owner epoch and fencing token;
- `IsolationProvider`: identify and prepare a worktree/sandbox, then reconcile, quiesce, revoke, destroy, and report its effective boundary;
- `ApprovalChannel`: obtain and record human releases;
- `ArtifactStore`: allocate scratch paths, hash artifacts, and preserve reports;
- `UsageProvider`: normalize units without inventing cost when pricing or cache semantics are unknown.

Every side-effecting adjacent-port operation uses the same durable intent, idempotency-key, opaque-reference, and reconcile pattern as worker operations. An ambiguous isolation prepare or revoke is never retried or treated as quiescent without evidence. This keeps the worker adapter from becoming a second monolith while closing the same external transaction boundary for resources.

## Codex experience

### The skill is the policy front end

The primary user command is explicit:

```text
$sage <task>
$sage report <run-id>
$sage resume <run-id>
```

Sage is expensive and changes control flow, so the Codex skill should not activate implicitly. Use `agents/openai.yaml`:

```yaml
policy:
  allow_implicit_invocation: false
```

Explicit-only is a policy semantic, not a permanent Codex manifest field. The current build generates Codex metadata with `allow_implicit_invocation: false`; the canonical policy does not make that YAML key part of Sage's domain model. Any future harness project must supply its own explicit-invocation mapping then, not now.

The `SKILL.md` entrypoint should remain a short six-step spine:

1. qualify and decompose;
2. commit a bounded bootstrap or complete plan revision;
3. issue bounded briefs and dispatch admitted attempts;
4. supervise, reconcile, and revise on evidence;
5. verify, triage, and integrate;
6. close the run and render the result.

Keep conditional mechanisms behind precise pointers. Split by owner, not by `explore`, `plan`, `implement`, `verify`, and `report`. A target source layout is:

```text
sage/
  policy/
    delegation.md       safe/worth tests, placement, decomposition
    contracts.md        briefs, reports, findings, dispositions
    topologies.md       orchestration patterns and evidence menus
    review.md           freeze, review loop, triage, completion
    recovery.md         failure signatures, reconciliation, handover
    memory.md           log-only run behavior and promotion boundary

  skills/sage/
    SKILL.md             explicit router and six-step spine
    agents/openai.yaml
    references/
      codex.md           Codex-native tool and capability mapping
      guarantees.md      native vs managed guarantees

  artifacts/
    schemas/             stable briefs, results, plans, run records
    fixtures/

  runtime/
    protocol-v0/         provisional while Codex is the sole production adapter
    core/                state, store, scheduler, reconciliation, views

  adapters/
    codex/
    in-memory/           core tests only; not a portability claim

  plugins/codex-sage/
    .codex-plugin/plugin.json
    skills/sage/         generated from the canonical skill source
    hooks/
      hooks.json
      handlers/
    .mcp.json            optional role-limited managed-mode client
```

Packaging may copy canonical policy into a distribution archive, but generated files carry a source hash and the build fails on drift. Nobody hand-edits a packaged copy.

### Promotion targets and runtime retrieval

"Log only" governs both runtime learning and runtime retrieval:

- During a Sage run, load canonical policy and selectively load already-promoted knowledge through its index.
- Do not search the raw journal, prior ledgers, closed-run records, or archived observations for a lesson or a same-shape precedent. Those are promotion inputs, not run-time context.
- Append factual observations, decisions, outcomes, usage, and evidence pointers for the current run. Do not consolidate, count confirmations, extract a lesson, or edit policy.
- `sage-promote` is the manual workflow that reads closed-run logs, consolidates observations, tests candidate lessons and falsifiers, and decides what becomes promoted knowledge.

`sage-promote` has two destination modes:

1. **Installed promotion — default:** `sage-promote` writes only to an installed-only promoted-knowledge and policy overlay. Future runs on this installation can read it. The source repository is untouched.
2. **Global promotion — explicit:** `sage-promote --global` writes only to the Sage source repository after the same review and degradation gates. It does not update the installed tree. Its final report prints the exact repository-root `install.sh` command the user can run when ready.

The installed-only overlay is user state, not a generated distribution file. `install.sh` preserves it across every install/update. If a later global promotion creates the same stable knowledge ID, the next install makes the repository copy canonical and archives the duplicate overlay entry rather than loading both. Neither mode runs inside an active Sage task.

### Installation, update, and complete removal

The existing repository already demonstrates the right product shape with root `install.sh` and `uninstall.sh`, but the Codex plan must name them explicitly and extend their ownership model to both Sage modes.

One repository-root `install.sh` is the only install and update command:

- default to Light mode; add an explicit Managed-mode option only after Managed mode passes its release gate;
- preflight every hard dependency and destination before changing anything;
- stage generated files, verify source hashes and manifests, then replace atomically where the platform permits;
- keep a receipt containing every Sage-owned path and every structured config/hook entry;
- preserve run history and the installed-only promotion overlay on update;
- back up a conflicting pre-existing path rather than silently overwrite it;
- verify the installed skill, promotion workflow, hooks/plugin, and managed process health before reporting success;
- be idempotent: re-running the same version is a clean no-op, and running after a partial failure converges safely.

One repository-root `uninstall.sh` removes the complete Sage-owned installation recorded by that receipt:

- stop managed processes before removing their binaries or state;
- remove the Sage skill, `sage-promote`, plugin/hooks, exact structured config entries, binaries, stores, leases, caches, logs, run history, installed-only promoted knowledge, receipts, and installer-owned backup roots after any displaced user content has been restored or explicitly exported;
- require an explicit confirmation because complete removal includes learned knowledge and run history; offer `--keep-data` as the deliberate exception, not the default;
- remove only receipt-owned files or content carrying a verified Sage ownership marker; never delete a same-named user file on name alone;
- never delete the source checkout or user deliverables inside project workspaces, and never recursively hunt through unrelated projects;
- support `--dry-run` and report anything it could not prove was Sage-owned. If a backup contains displaced user data that cannot be restored safely, preserve and report that backup instead of deleting data merely to achieve a cosmetically empty uninstall.

Lifecycle tests cover fresh install, repeat install, update, interrupted update, update after installed-only promotion, changed user config, symlinks, paths with spaces, managed-process shutdown, dry-run, complete uninstall after every supported version, and proof that unrelated files remain byte-identical.

### Light mode: Codex-native execution

The first usable implementation should use Codex's collaboration tools through a thin mapping owned by `references/codex.md`:

| Portable operation | Codex-native mapping |
| --- | --- |
| request fresh worker context | use it only when the pinned native tool schema exposes a context/fork control; otherwise record context behavior as a capability |
| seed recent/full context | use the smallest explicit seed/fork supported by the current tool schema |
| set model/effort | pass explicit spawn values or use a versioned custom-agent/config mapping |
| steer active worker | send to the recorded agent handle |
| follow up after a result | continue the same worker thread when supported |
| interrupt | interrupt the recorded agent handle |
| inspect fleet | list active/done agents and reconcile handles |
| wait | use notification-aware waiting rather than tight polling |

The actual Codex tool names and argument schemas stay in the Codex reference and adapter tests, not in policy. The current callable surface includes spawn, message/follow-up, interrupt, list, and wait operations, but that is a runtime fact to probe, not a forever protocol.

Default native-mode rules:

- give independent workers fresh context and artifact pointers when the pinned tool schema proves that behavior; otherwise record the inherited-context limitation and use App Server `thread/start` when guaranteed fresh context is required;
- keep synthesis, triage, plan revision, and completion in the root thread;
- resolve the current model catalog first; the initial Codex placement profile may map narrow high-volume work to `gpt-5.6-luna`, balanced implementation/research to `gpt-5.6-terra`, and architecture or adversarial review to `gpt-5.6-sol` at a supported high effort;
- record requested and effective model/effort separately;
- run read-heavy fan-out first;
- permit at most one writer in the shared checkout;
- require a dedicated worktree and verified sandbox before claiming parallel-writer isolation;
- treat returned reports as unprivileged claims.

The model names above are provisional Codex placement-profile entries as of this proposal, not portable tiers or permanent policy. Resolve supported effort from the live model catalog and preserve a user's explicit model choice.

### Optional Codex plugin and hooks

Package a Codex plugin for surfaces that support it, but keep the standalone skill functional elsewhere. `sagectl` is a client of `sage-core`; it never opens its own run database. Hooks add recovery pointers, telemetry, and narrow defense-in-depth. They do not define a third mode or authorize the model.

Use synchronous hooks only for deterministic gates:

| Hook | Sage use | Limitation |
| --- | --- | --- |
| `SessionStart` | probe the role-limited `sagectl` client, locate an active run, inject a short recovery pointer | project/plugin hooks must be trusted |
| `PreToolUse(Agent)` | in Managed mode, deny direct native dispatch and point to the core; in Light mode, log or apply only proven local rules | only covers the supported tool path; hook failure may fail open |
| `SubagentStart` | inject a brief pointer and record telemetry | cannot block startup and cannot deterministically bind a dispatch ticket |
| `PostToolUse(Agent)` | bind a one-shot reservation to the returned agent ID if a pinned probe proves the response shape | runs after creation; otherwise require single-flight or remain advisory |
| `SubagentStop` | record terminal signal; reject an incomplete result as completion and allow at most one bounded repair | does not judge correctness and runs after worker execution |
| `PreToolUse(Bash/apply_patch/MCP)` | deny deterministic forbidden actions and validate a lease only when session, attempt, resource, and token can all be proven | cannot prove filesystem containment or reliably attribute every child path |
| `PermissionRequest` | deny an out-of-scope action; otherwise either consume a prior Sage grant as the Codex decision or decline so Codex prompts | an `allow` response suppresses the normal prompt; there are not two independent approvals |
| `PostToolUse` | submit observation and artifact metadata to the core or light-mode artifact | runs after side effects |
| `PreCompact` / `SessionStart(compact)` | checkpoint then restore the run pointer and current projection | not a replacement for worker recovery |

Do not make transcript parsing part of the gate. Do not use async hooks for admission or approvals. Do not let a `Stop` hook create an unbounded continuation loop; if used at all, it may continue once for a small set of mechanical open states such as an unreleased writer lease.

`PreToolUse` supplies the originating tool-call ID, but `SubagentStart` does not. Do not claim ticket-to-agent binding at `SubagentStart`. A live conformance probe must show that `PostToolUse(Agent)` returns a stable agent ID that can be matched to a one-shot reservation; otherwise native concurrent binding is unavailable.

Every run records hook hash, trust, coverage, and failure behavior. Missing, changed, skipped, or failed hooks degrade only the exact capability they supported. The Managed core remains authoritative for its own dispatches; Light mode remains advisory.

### Managed mode: external core

The managed driver must choose a concrete supported surface by capability, not treat the App Server and SDK as interchangeable. Start with two disposable probes:

- use the Codex SDK for the start/continue/resume and sandbox automation it documents;
- use a pinned App Server build where Managed mode requires explicit turn identity, active-turn steering, interruption, approvals, or richer events that the SDK does not expose.

The current `codex app-server` command is experimental and unsupported for production workloads. Internal version, fault, security, and upgrade gates cannot override that upstream status. Phase 3 must choose one of three truthful outcomes: use a production-supported SDK surface that satisfies the required predicates, keep Managed mode explicitly experimental behind informed per-install opt-in, or remain in Light mode. For an experimental App Server path, use:

- `thread/start`, `thread/resume`, and `thread/fork` for worker identity;
- `turn/start`, `turn/steer`, and `turn/interrupt` for lifecycle;
- streamed `thread/*`, `turn/*`, and `item/*` events for supported observability;
- approval requests through the client protocol;
- explicit model, cwd, and sandbox at the correct thread/turn boundary;
- generated schemas from the exact Codex binary used by the adapter;
- the documented default stdio transport first; experimental WebSocket transport is not required.

Map native IDs directly into opaque `WorkerRef`s. Do not derive them from transcript filenames. Pin the tested Codex version, record it on each run, and run conformance probes during adapter startup.

Managed mode may be exposed to the skill through a local MCP server or a small CLI. That surface exposes policy proposals and queries, not privileged scheduler, adapter, lease, or approval commands. If the core is unavailable and the user requested Managed mode, stop with a typed capability error. Do not silently fall back to Light mode.

#### Deployment topology

An ordinary `$sage` invocation does not gain control of its host process merely because an App Server API exists. In interactive Managed mode:

1. the active Codex root is the policy actor;
2. it submits plans, decisions, and verification through the role-limited MCP/CLI client;
3. the external core launches and owns separate managed Codex worker threads;
4. Sage records parentage itself; those workers need not appear as native collaboration children in the root UI;
5. if the root dies, the core reconciles workers and pauses at `AwaitingPolicy` until `$sage resume` or a separately managed policy-actor thread takes over.

A dedicated Sage client may later own both a durable policy-actor thread and worker threads through the same Codex interface. That is a different product surface from the ordinary skill and must be evaluated separately; the proposal does not smuggle it into the skill architecture.

Managed authority is scoped to core-managed actors. To claim complete mediation of a managed workspace, the policy-actor root must be read-only and unable to launch unmanaged writers, or it must run inside a separate sandbox from managed resources. A fail-open hook that discourages direct `Agent` or write tools is not sufficient. Otherwise the run reports that only managed worker actions are covered.

## Guarantee matrix

| Property | Light mode | Managed mode |
| --- | --- | --- |
| Decomposition and evidence policy | root-model judgment | policy-actor judgment |
| Runtime knowledge input | canonical policy plus selectively loaded promoted knowledge; raw prior-run logs excluded | same; core run state is used for coordination, not mined for lessons during the run |
| Portable run artifact | yes, model-maintained and validated | yes, rendered from authoritative state |
| Dispatch admission | advisory parent discipline | scheduler-owned transaction |
| Concurrency | parent-managed | core-owned |
| Model/effort recording | requested value plus whatever the host exposes | requested and effective adapter snapshot |
| Steering/interruption | native best effort | explicit `TurnRef` operation where capability passes |
| Aggregate admission policy | parent judgment | transactional reservation |
| Worker restart reconciliation | ledger and manual resume | snapshot/cursor reconciliation according to adapter delivery semantics |
| Root/policy-actor restart | manual `$sage resume` | deterministic state recovers, then `AwaitingPolicy` unless a durable policy actor is configured |
| Shared-tree writer safety | one-writer policy; no enforcement claim | coordinator-backed lease plus a proven sandbox/worktree boundary |
| Parallel writers | no claim | only with isolated resources and a tested isolation provider |
| Compaction recovery | re-read artifact; optional compact hook pointer | current-state reload plus adapter reconciliation |
| Semantic correctness | verification policy | verification policy |

Plugin hooks can strengthen or observe a named operation in either mode, but do not create a third guarantee column. No mode claims that code can decide semantic correctness, that a worktree is an OS sandbox, or that Sage controls writes by the user and unrelated processes.

## Safety model

### Reader and writer isolation

Use layered controls:

1. Give readers a verified read-only sandbox when available.
2. Permit one writer per working tree.
3. Give every parallel writer a dedicated worktree, cwd, and sandbox.
4. Issue an exclusive coordinator-backed `ResourceId` lease with scope, owner epoch, and fencing token before any writer starts.
5. Gate supported local write tools before execution.
6. Run untrusted or unattended writers in an OS policy sandbox, container, or stronger boundary.
7. Freeze the artifact before review and issue a new lease only after triage.

A Bash-capable worker can write through many routes. Tool-name restrictions and path matching are defense in depth. They do not replace an isolation boundary.

### Human release

Destructive, irreversible, or externally visible actions require a recorded `ApprovalGrant` before execution. It contains:

- actor and source;
- exact action class and scope;
- issued and expiry times;
- one-shot nonce or bounded reuse rule;
- run, unit, attempt, and lease references;
- native thread, turn, and item references where available;
- canonical action digest, cwd/environment, and requested permission delta;
- the user's words or an immutable reference to them.

Only the authenticated `ApprovalChannel` can create or revoke the grant. The worker and policy actor can request one but cannot attest that it exists. On replay, a consumed or revoked one-shot approval cannot fire again, and session-wide acceptance is prohibited unless the grant explicitly authorizes bounded reuse.

In Managed App Server flows, the core validates and consumes the Sage grant when responding to the native approval request; Codex remains the execution gate, but this is one bound human decision, not two independent approvals. In Light mode, the hook denies an out-of-scope request and otherwise declines to decide so the normal Codex prompt remains authoritative. If a hook ever returns `allow` from a prior grant, the report must state that it suppressed the normal prompt rather than claim both prompts occurred.

Native network approval can be coarser than semantic action approval. Codex may group concurrent requests by destination, so one response can release several queued connections and may expose only host/protocol. Sage must serialize those requests, deny an ambiguous group, or use an explicit destination-scoped grant that enumerates the complete known request set and bounded reuse. Permission to reach a host is never recorded as approval of the HTTP operation or its external effect.

### Dirty work and artifacts

- Capture the initial Git revision, dirty paths, staged paths, and task-owned paths.
- Hash immutable input artifacts and every review freeze.
- Preserve pre-existing changes explicitly in compose checks.
- Allocate scratch output outside source paths and expose it as an `ArtifactRef`.
- Never retry an unknown side-effecting attempt merely because its result was lost.

## Admission, cost, and context policy

The current Sage hard-codes a `4x` budget rail. The universal core should not.

Define an `AdmissionPolicy` interface with at least:

- `bounded-observed`: explicit finite caps for total admissions, attempts per unit, plan revisions, agents, and wall-clock admission, plus a token or cost ceiling where reliable telemetry exists;
- `fixed`: user or organization caps for attempts, agents, tokens, cost, and time;
- `estimate-multiple`: current Sage-style multiples with versioned floors;
- `uncapped-observed`: no Sage token/cost ceiling, but launches and usage are logged; allowed only as an explicit attended experiment under provider or organization hard limits;
- `custom`: organization or user policy.

The Codex-first profile is `bounded-observed`, but a new planning artifact carries uncommitted task-specific rails rather than universal numeric defaults. Before any revision, brief, or attempt is admitted, the policy actor commits finite unit, attempts-per-unit, concurrency, plan-revision, admission-time, agent, and no-progress bounds for that task. The distinct `estimate-multiple/baseline-v1` compatibility profile retains the current Sage `4x` task/unit and `2x` agent projections only where the adapter can measure comparable usage. If spend telemetry is unavailable, the committed non-spend limits still provide a termination boundary. Crossing a limit drains selected in-flight work, admits nothing new, records the exact sensor/provenance, and enters `AwaitingHuman`.

Every autonomous managed run retains:

- an explicit concurrency cap;
- dependency gates;
- same-signature failure stopping;
- dry-round termination;
- human-release gates;
- manual stop and draining semantics.

The `uncapped-observed` idea in [`ideas.md`](ideas.md) remains worth measuring, but brainstorming is not evidence for making it the safe default. It requires explicit per-run consent, an attended policy actor, a visible external hard ceiling, and the same finite no-progress/revision rules. It means spend alone is not Sage's stop condition; it does not mean recursive admission is unlimited or unattended.

Usage values carry provenance: `measured`, `provider-reported`, `estimated`, or `unknown`. Never convert tokens to cost without a versioned price source. Never sum incompatible context occupancy and billed-token metrics.

The orchestrator handover remains a first-class Sage policy in both modes:

- default threshold: parent context occupancy at **30 percent** of the effective context window;
- initial implementation may hard-code `0.30`; a later setting such as `handover.context_fraction` may override it without changing the handover protocol;
- Managed Codex uses supported usage/context events only when the driver proves both numerator and denominator;
- Light mode uses a supported Codex pressure signal when one exists and otherwise relies on mandatory hash-bound `handoff.json` plus compaction recovery; optional `handoff.md` is generated only from the JSON and is never resume authority;
- where no reliable pressure sensor exists, report automatic threshold detection as unavailable and expose an explicit handover/resume path. Resume fails for missing, malformed, hash-invalid, or stale JSON and does not require Markdown. Never invent a percentage from transcript size or unrelated token totals.

The policy is therefore always present; only its automatic sensor may be unavailable. A missing sensor is a recorded Light-mode limitation and potential evidence for Managed mode, not a reason to delete the 30 percent rule.

## Memory and reporting

Runtime knowledge and run evidence are different stores with different read rules. During a run, Sage may read canonical policy and selectively load promoted knowledge. It must not read raw prior-run logs, journal tails, old ledgers, or archived observations to improvise a lesson. The Managed core or Light-mode structured artifact records only current-run facts:

- plan revisions and decisions;
- estimates and actual usage with provenance;
- failures and retry signatures;
- findings and dispositions;
- observations with evidence pointers;
- adapter capabilities and degradations;
- artifacts and verification results.

It does not write a lesson, set a confidence band, consolidate observations, or change Sage policy. `sage-promote` remains the separate, explicit workflow that reads closed runs, groups observations, tests falsifiers, and asks the user before promotion. By default it promotes into the installed-only overlay; `sage-promote --global` promotes into the source repository and leaves installation to the user's later `install.sh` run.

The Markdown ledger becomes a projection of structured state/artifacts:

- generated from structured state;
- reproducible after restart;
- safe to delete and rebuild;
- never parsed back as the authoritative database.

The user-facing result remains first-class. A run does not end with only a pointer. It returns the deliverable, a concise run line, artifact paths, effective capability summary, and surfaced safety/human items.

## Portability posture

### Current plan: Codex only

Use native collaboration tools for Light interactive mode. Capability-test the SDK and pinned App Server separately for managed workers; do not infer that one exposes the other's operations. Generate App Server types from the pinned Codex build where used. Treat API maturity, plugin availability, hook trust, and tool coverage as capabilities.

Keep the core/driver seam small and semantic, with an in-memory adapter for core tests. This is a useful internal seam because production and tests need different adapters. It is not evidence that a second harness fits it. Do not add compatibility fields, abstract nouns, or lowest-common-denominator behavior for an adapter that is not being built.

### Post-Light milestone: alternative-family verification

After Light mode is complete, any cross-harness or cross-family claim requires one separately approved milestone; this plan does not implement it and current Sage exposes no such support. The milestone first discovers a genuinely available alternative-family capability and proves effective model-family identity from runtime evidence rather than an alias or requested value. It then runs matched role, tool, permission, and sandbox probes; verifies typed safe failure for missing identity, capability, isolation, and lifecycle evidence; and compares the alternative lane with Codex on predeclared, matched quality and reliability tasks.

Exit requires role/tool/sandbox parity for every claimed operation, no unsafe retry or silent fallback under injected failure, and quality/reliability results meeting the same declared acceptance thresholds as Codex. Any semantic difference revises runtime v0 before a portable v1 claim. Landing an adapter, enabling the lane, or declaring support requires explicit approval after those results are reviewed.

The eventual proof should standardize semantics rather than harness nouns:

- each harness-native thread or session is an opaque worker;
- `idle` has adapter-specific meaning and is never automatically `completed`;
- permission names are not portable capabilities;
- process isolation is not sandbox isolation;
- model aliases are not cross-provider tiers;
- ACP or another editor protocol may be a UI transport, not the Sage runtime protocol.

## Implementation phases

### Phase 0: extract ownership, artifacts, and evaluation

- Inventory every current Sage invariant and assign one owner: policy, artifact schema, runtime, Codex experience, adapter, or promotion workflow.
- Preserve the bounded scout-before-plan flow with an explicit bootstrap revision.
- Extract Claude-specific mechanics without deleting assumptions, gaps, `AwaitingHuman`, verification, coordination checks, safety rails, or completion duties.
- Draft artifact schema v1 and runtime protocol v0 provisional; do not freeze the worker port or call it cross-harness-stable.
- Define the three memory classes and their access rules: promoted knowledge is a runtime input, closed-run logs are promotion input, and current-run logs are append-only output.
- Specify `sage-promote`'s installed-default and explicit-global destinations, including stable-ID reconciliation on the next install.
- Specify the ownership receipt, update preservation rules, complete-removal scope, and failure recovery for the universal `install.sh` and `uninstall.sh`.
- Define authenticated principals, threat boundaries, data classification, redaction, retention, deletion, and approval semantics before persistence code.
- Capture representative current Sage runs and failures as fixtures.
- Pre-register the Phase 1 tasks, rubric, model/spend comparability rules, margins, and benefit thresholds.
- Add corpus checks for broken pointers, duplicated policy owners, and harness names leaking into canonical policy.

Exit criterion: every current safety, evidence, completion, promotion, installation, and removal obligation has one named owner; current runs fit the artifact schema without weakening behavior; authority and privacy reviews have no open blocker.

### Phase 1: Light reader-only Codex skill and managed-mode decision gate

- Create the explicit-only `$sage` skill and Codex reference.
- Implement research/review fan-out using native Codex subagents with explicit model/effort and fresh context only where the pinned tool schema exposes it.
- Validate and render portable run artifacts without transcript parsing as a required sensor.
- Read only promoted knowledge at runtime; append raw run facts without reading prior raw logs back into the task.
- Keep the 30 percent handover policy, test its automatic path where Codex exposes a valid pressure sensor, and test explicit handover/resume where it does not.
- Implement `sage-promote` with installed promotion as the default and `--global` as the source-repository destination.
- Deliver the root `install.sh` and `uninstall.sh` for a complete Light-mode install/update/removal and pass the lifecycle matrix.
- Test activation, non-activation, zero-agent decisions, bootstrap discovery, bounded briefs, conflict triage, and result synthesis.
- Keep the existing Claude Sage as a behavioral reference, but use ordinary Codex without Sage as the primary within-harness control.
- Run at least 20 paired, pre-registered reader/review tasks with comparable requirements, model access, and spend limits; blind artifact scoring where practical.
- Classify every miss independently as policy judgment, model capability, brief/specification, or deterministic coordination/bookkeeping.

The decision has three gates, in order:

1. **Safety:** any safety regression stops the program until understood and corrected.
2. **Policy value:** after independent causal adjudication, require no unexplained semantic regression and at least one pre-registered material signal, such as a rubric improvement on at least three tasks, 25 percent fewer orchestration interventions, 25 percent lower root-context occupancy, or 20 percent lower wall time for tasks with three or more independent units at comparable quality and spend.
3. **Managed need:** continue only when repeated residual failures belong to deterministic mechanisms `sage-core` would own.

A semantic miss preclassified as core-addressable gets one controlled rerun that changes only the failed bookkeeping/coordination mechanism. It counts as policy evidence only if that repair removes the regression, while the original miss still counts against the managed-need gate. Do not exclude or relabel an unexplained regression. Track artifact completeness separately; a missed mechanical record duty may be evidence for the core rather than evidence that the policy is worthless.

The managed-need threshold is at least three of 20 tasks requiring correction for admission, dependency state, handle tracking, boundedness, handover sensing, or another deterministic mechanism the core would own, or a deterministic root-loss fixture proving that a required recovery use case cannot be met. Pre-register the expected intervention/context cost of those failures. Light-mode success without such failures is evidence that a supervisor is unnecessary. If policy value fails, stop. If policy value passes but managed need does not, ship Light mode and stop the runtime program. Managed mode is justified by valuable policy plus costly deterministic residue, not by Light mode merely being "good."

The sample size and percentages are proposed pilot defaults, not truths about Sage. They may be changed before registration to match the available task corpus, but never tuned after results are visible.

### Phase 2: Codex managed-mode feasibility spike

- Build disposable reader-only vertical slices for the Codex SDK and pinned App Server.
- Exercise prepare/start, follow-up, active steering, interruption, result acceptance, approval, snapshot recovery, and each claimed delivery class.
- Inject crashes before and after worker creation and turn start.
- Execute the same artifact plan through Light mode and the disposable managed slice.
- Revise runtime v0 from observed Codex behavior; do not add a field for a hypothetical harness.
- Keep the external core interface small enough for the Codex driver and in-memory test adapter. Treat any proposed cross-harness generality as unproven.
- Record an ADR choosing between remaining Light-only and building the external managed core.
- Measure lost native UX, added round trips and latency, daemon/auth/store packaging, upgrade breakage, and how much deterministic bookkeeping leaves the root context.

Exit criterion: Codex completes one topology and every required recovery fixture; every ambiguous external start produces no duplicate active turn; required capabilities are supported by an upstream surface mature enough for the intended release; and the ADR selects Managed mode after counting its deployment, credential, latency, and upgrade costs. Otherwise ship Light mode.

### Phase 3: minimal managed core and Codex reader driver

- Implement one authenticated core, one `RunStore`, transactional state plus audit/outbox, bounded admission, and per-attempt capabilities.
- Implement crash-safe prepare/start and reconciliation using the selected Codex surface; pin binaries and generated schemas where applicable.
- Record the maturity branch explicitly: supported SDK, experimental App Server with informed opt-in, or no managed Codex release.
- Keep `sagectl`, MCP, plugin, and hooks as clients of the same core.
- Extend `install.sh` and `uninstall.sh` to install/update, health-check, stop, and completely remove managed-mode processes and state using the same receipt.
- Add fault injection for supervisor crash, adapter disconnect, duplicate/out-of-order observation, delivery gap, lost result, unknown side effect, malformed report, stuck worker, and capability degradation.
- Verify that malformed results are not accepted as completion and receive at most one bounded mechanical repair before failure/policy review.
- Re-run at least 20 paired orchestration-heavy tasks against Light mode under the same pre-registered rubric.

Exit criterion: every crash point reaches an explicit state; no duplicate active turn or automatic retry of an unknown side effect occurs; current state and audit agree after restart; all policy boundaries pause at `AwaitingPolicy`; upstream-unsupported interfaces remain labeled experimental. Managed mode is retained only if it reduces protocol failures/interventions or root-context occupancy by at least 25% without worse quality on more than one of 20 tasks and without cost above `1.25x` Light mode.

### Phase 4: Codex single-writer safety and lifecycle hardening

- Add the deployment-wide resource coordinator, isolated worktree/sandbox provider, one shared-tree writer, freeze/review/triage, and authenticated approval channel.
- Package the optional Codex plugin for supported surfaces, with `sagectl` as a core client.
- Probe `PostToolUse(Agent)` binding and degrade to single-flight/advisory if a stable native agent ID cannot be proven.
- Re-run the complete install/update/uninstall matrix with Light-only, managed, interrupted, locally promoted, and globally promoted installations.
- Attack symlinks, hardlinks, subprocesses, Git metadata, shell escapes, network side effects, stale fencing tokens, dirty-tree preservation, a second run, and a second core/store targeting the same resource; kill the lease owner during takeover tests.

Exit criterion: no shared-tree corruption; all Sage-managed accepted mutations use the current coordinator lease and strongest claimed isolation boundary; stale/off-lease attempts fail before crossing that boundary; malformed reports are rejected as completion; repeat updates preserve installed-only promoted knowledge; complete uninstall leaves no receipt-owned Sage path or config entry and changes no unrelated byte.

### Phase 5: Codex final trial and default decision

- Add parallel writers only in separately isolated resources with an explicit integration owner.
- Run at least 20 paired tasks stratified across research, review, implementation, recovery, model placement, handover, promotion, and lifecycle cases.
- Blind scoring where practical and pre-register non-inferiority and benefit thresholds.

Hard gates: no destructive-action approval regression; no shared-tree corruption; every deterministic crash point reaches the exact expected state; a stochastic restart may miss only by landing in safe `unknown`/`AwaitingHuman` with no duplicate effect, approval consumption, or concurrent lease; every usage/cost claim has provenance; every worker, finding, gap, and assumption reaches an explicit final state; quality is no worse than baseline on more than one task.

Adopt Managed mode as the default only for task classes where it also meets at least two material benefit gates: 25% fewer protocol failures/interventions, 20% lower wall time on three-plus independent units, 10% lower quality-adjusted cost, 50% lower root-context occupancy, or successful deterministic recovery that Light mode cannot provide. These are proposed decision rules, not performance predictions.

## Tests and evidence

### Core tests

- model-based state-machine tests for every legal and illegal transition;
- property tests for acyclic plans, dependency readiness, revision carry/supersession, and result adoption;
- idempotency lookup-before-version tests, same-key/different-body rejection, and stored-result replay;
- authorization tests proving that policy actors and workers cannot admit, lease, approve, bind, or operator-close;
- duplicate, missing, out-of-order, gap, and ephemeral-observation tests;
- cross-run and cross-store coordinator uniqueness, owner-death takeover, lease expiry, quiescence, revocation, and fencing tests;
- bounded-admission termination tests and explicit uncapped opt-in tests;
- schema migration, audit/state consistency, outbox recovery, redaction, retention, and deletion tests.

### Adapter contract suite

The Codex driver must pass these tests against the core interface; the in-memory adapter covers deterministic core cases without making a portability claim:

- environment offers, per-attempt snapshots, degradation-to-quiesced/unknown state, restoration without retroactive trust, and typed unsupported results;
- requested versus effective model, effort, permissions, and sandbox;
- prepare, turn start, result, follow-up, turn-scoped steer/interrupt, reconcile, and dispose;
- crash points before/after every external call, with no duplicate active turn and no silently orphaned side effect;
- replayable, snapshot-reconcilable, and ephemeral delivery behavior where claimed;
- lifecycle and usage normalization;
- approval digest binding, revocation, consumption, grouped-network denial/serialization, and native request round trips;
- partial/malformed output;
- disconnect and restart reconciliation.

Keep sanitized golden raw-event fixtures for every pinned harness version and run live smoke tests separately. A fixture proves parsing; a live smoke test proves the harness still emits that shape.

### Promotion and lifecycle tests

- a run reads promoted knowledge but never raw prior-run logs;
- the default promotion changes only the installed overlay;
- global promotion changes only repository sources and prints the follow-up install command;
- update preserves installed-only promotion and reconciles stable IDs already present globally;
- fresh, repeated, interrupted, and managed installs converge to a verified receipt;
- dry-run changes nothing;
- complete uninstall removes every receipt-owned Sage path and structured config entry, including runtime data, while leaving unrelated files and project deliverables unchanged.

### Skill behavior tests

- prompts that should and should not activate the skill;
- explicit invocation with no delegable unit;
- broad read-only sweep;
- competing hypotheses and adversarial review;
- one-writer implementation;
- a rail requiring human input;
- compaction/recovery;
- a control arm without Sage for matched outcome comparison.

Judge behavior and artifacts, not exact prose or heading names.

## Alternatives considered

### A. Directly port the Claude skill to Codex

Useful only as a short-lived compatibility baseline. It would preserve Claude tool names, transcript assumptions, and model-owned bookkeeping while hiding the difference behind Codex syntax.

### B. Build only a Codex skill

This gives fast value and should be Phase 1, but it cannot honestly claim authoritative scheduling, leases, or restart recovery. It is a valid endpoint when work is attended and the early trial shows that advisory coordination is sufficient.

### C. Put everything in Codex hooks or one plugin process

Reject. Hooks have trust and coverage limits, run concurrently, and cannot undo side effects. A plugin process should not own the only run state or become a Codex-specific monolith.

### D. Build the full external supervisor before using Sage on Codex

Reject as sequencing. It delays behavioral evidence and risks encoding the wrong policy/core seam. Define portable artifacts, ship and measure the native skill, then move only demonstrated deterministic failures into the managed runtime.

### E. Define a lowest-common-denominator universal adapter

Reject. `prompt -> wait -> text` would discard the exact steering, cancellation, usage, approval, and recovery capabilities that justify a runtime. Use negotiated capabilities instead.

### F. Build a second harness adapter before managed Codex

Reject for the current plan. A second adapter would test portability, but it would not answer the earlier question of whether Light Codex leaves enough deterministic pain to justify any managed runtime. If portability later becomes a release requirement, use the separately approved proof described above and let observed differences reshape v0 before calling it v1.

### G. Codex-first policy, two modes, and one conditional control plane

Recommended. It gets a real Codex skill early, validates value before infrastructure, gives managed work exactly one state owner, and keeps cross-harness portability explicitly unclaimed until a future adapter proves it.

## Main risks

1. **Policy drift across distributions.** Mitigate with one canonical policy source, generated bundles, source hashes, and corpus lint.
2. **False enforcement claims.** Mitigate with operation-specific effective snapshots and capability evidence.
3. **Adapter API churn and maturity.** Pin versions, generate schemas, classify experimental APIs, and run live conformance probes.
4. **Control-plane infrastructure without better outcomes.** Enforce early and repeated matched value gates; telemetry is not value by itself.
5. **Core rigidity.** Version plans and keep judgment outside deterministic transitions.
6. **Hook trust or coverage gaps.** Treat hooks as defense in depth and surface their status.
7. **Writer escape routes.** Require sandbox/worktree isolation before claiming enforcement.
8. **Unbounded go-wild runs.** Default to bounded admission; keep uncapped spend attended, explicit, externally limited, and finite on no-progress/revision dimensions.
9. **Supervisor complexity.** Keep Light mode viable; the Managed runtime must earn its maintenance cost.
10. **Persistent-state privacy and cleanup.** Classify and redact before persistence; default to hashes/protected locators and attach retention/deletion policy to each run.
11. **Split-brain resource ownership.** Require one deployment-wide coordinator with owner epochs and fencing; reject writer admission when it is unavailable and test independent cores/stores plus owner death.
12. **Policy-actor loss.** Reconcile deterministic state, then pause at `AwaitingPolicy` unless a durable policy-actor thread is explicitly managed.
13. **Installed/global promotion drift.** Use stable knowledge IDs, an installed-only overlay, source hashes, and installer reconciliation; never let an update silently discard local promotion or load duplicate rules.
14. **Incomplete uninstall.** Use an ownership receipt and structured config edits, test every supported upgrade path, and report rather than delete anything whose Sage ownership cannot be proved.

## Review reconciliation

The required whole-architecture and adversarial reviews were assessed against the current Sage source and primary harness documentation rather than applied mechanically.

Accepted because both reviews converged and the sources support them:

- remove the independent guarded tier and give Managed state exactly one owner;
- make bounded admission the default and uncapped spend explicit/attended;
- test value after the Light skill and again after the first Managed slice;
- keep runtime v0 provisional while Codex is its only production adapter;
- add authenticated principals, crash-safe prepare/start, deployment-wide resource coordination, per-attempt capabilities, explicit policy recovery, privacy controls, and quantitative exits;
- replace portable model tiers with task requirements plus calibrated host profiles.

Accepted with modification:

- the adversarial review called full event sourcing premature; this proposal keeps transactional state plus an append-only audit/outbox and defers full replayable event sourcing until a named invariant needs it;
- the adversarial review proposed making hooks only observability; this proposal also retains narrow deterministic denial where Codex documents a synchronous pre-hook, but never promotes hooks to a separate control plane or isolation boundary;
- the adversarial review proposed a deeper generic worker control call; this proposal keeps the port semantic but retains explicit `TurnRef` operations because Codex requires race-safe turn identity.
- the earlier proposal required a second harness before managed implementation; this revision defers that proof. One production adapter makes the cross-harness seam hypothetical, but that is a reason to avoid freezing it, not a reason to implement an unneeded harness.

Not accepted:

- implementing a second harness merely to legitimize the interface. Phase 2 first decides whether managed Codex is worth having; a later portability decision can still choose a different seam on evidence.
- treating all App Server events as cursor-replayable or the SDK and App Server as interchangeable. Primary documentation does not support either claim.

## Final recommendation

Build the Sage skill for Codex now, with these boundaries:

1. Extract a concise, explicit-only `$sage` skill from the existing policy.
2. Stabilize the portable artifact schema, but keep runtime protocol v0 provisional while Codex is its only production adapter.
3. Use native Codex subagents for the first reader-heavy Light mode and run the paired safety, policy-value, and managed-need gates immediately.
4. At runtime, read policy plus promoted knowledge only; write current-run facts without mining prior raw logs. Make `sage-promote` the manual consolidation and lesson-extraction workflow.
5. Make installed promotion the `sage-promote` default. Make `sage-promote --global` write the source repository only, followed by a user-run `install.sh` when the user wants to update the installation.
6. Ship one trustworthy repository-root `install.sh` for install/update and one receipt-driven `uninstall.sh` for complete Sage-owned removal, covering both modes.
7. Keep the 30 percent orchestrator handover as the default policy in both modes, configurable later if useful, and distinguish an unavailable sensor from a removed policy.
8. If Managed mode earns its cost, give one authenticated external `sage-core` sole ownership of run state, admission, and recovery, with one deployment-wide coordinator owning mutable-resource leases.
9. Split worker preparation from turn execution, keep explicit turn identity, reconcile ambiguity before retry, and pause at judgment boundaries after policy-actor loss.
10. Make plugin hooks and `sagectl` optional clients of the same core, with no separate database or guarantee tier. Default to bounded admission; expose uncapped-observed only as an explicit attended experiment under external limits.
11. Implement no second harness in this plan. If portable runtime v1 later becomes a real release requirement, run the separately approved portability proof.

Codex is the complete implementation and proving ground. It does not become the permanent definition of Sage, but portability also does not become infrastructure purchased before it has a user need.

## Evidence and limitations

This proposal is based on:

- the current Sage skill, dispatch/topology/harness/memory references, scripts, and decomposition analysis in this repository;
- current official OpenAI documentation for Codex skills, subagents, hooks, worktrees, security, SDK, and App Server;
- three independent lower-cost exploration passes covering Sage internals, Codex mechanics, and cross-harness portability;
- independent high-effort reviews of whole-architecture correctness and whether the proposed architecture was actually the best option;
- an additional factual/API/link audit of the draft.

No Sage Codex implementation, live App Server driver, fault-injection campaign, installer lifecycle matrix, promotion-target test, or matched quality trial was run for this proposal. App Server, hook, and model details must be re-probed against pinned versions during implementation. Every performance, quality, and maintenance benefit remains a hypothesis until the phased exits and paired trial establish it.
