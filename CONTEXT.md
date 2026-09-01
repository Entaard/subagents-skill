# Sage

Sage is an orchestration policy and optional managed runtime for coordinating agent work while preserving evidence, safety rails, and durable handover.

## Language

**Light mode**:
The Codex-native Sage experience in which the root model follows Sage policy and owns planning, dispatch, supervision, and bookkeeping. It has no external authoritative Sage scheduler.
_Avoid_: Text-only mode, unmanaged mode

**Managed mode**:
The Sage experience in which an external `sage-core` authoritatively owns deterministic coordination and durable run state while a policy actor retains judgment.
_Avoid_: Global mode, portable mode

**Current-run log**:
The active run's append-only facts and evidence. The active run may read it only for coordination and recovery, not to derive reusable guidance.
_Avoid_: Working memory, live knowledge

**Closed-run log**:
A completed or stopped run's immutable evidence record, available to promotion but unavailable as task-time knowledge.
_Avoid_: Historical knowledge, prior memory

**Promoted knowledge**:
Curated, tested guidance eligible for selective loading by a future Sage run.
_Avoid_: Raw memory, previous logs

**Installed promotion**:
The default promotion destination, scoped to the current Sage installation and invisible to the source repository.
_Avoid_: Local promotion

**Global promotion**:
An explicit promotion destination that changes the Sage source repository and reaches an installation only through a later install/update.
_Avoid_: Automatic update

**Handover threshold**:
The parent-context occupancy fraction at which orchestration transfers through a durable handoff. Its default is 30 percent in both Light and Managed modes.
_Avoid_: Compaction threshold

**Policy actor**:
The model or human that makes Sage's judgment calls: decomposition, placement, evidence adjudication, replanning, and completion.
_Avoid_: Scheduler, worker, supervisor process

**Plan revision**:
One immutable, numbered statement of admitted units, dependencies, criteria, and bounds. A changed plan is a new revision rather than an edit to history.
_Avoid_: Mutable plan, run spec

**Bootstrap revision**:
An optional bounded plan revision containing only read-only discovery needed to create the first complete plan.
_Avoid_: Exploration phase, provisional implementation plan

**AwaitingHuman**:
An explicit non-complete state for a criterion, finding, gap, or run that requires a human judgment or release.
_Avoid_: Blocked, failed, assumed pass

**Coordination outcome**:
The evidence-backed conclusion about whether delegation and orchestration helped, harmed, or were inconclusive for a run.
_Avoid_: Agent count, success status

**Ownership receipt**:
The installation record that proves which paths and structured configuration entries Sage owns and how displaced user content can be restored.
_Avoid_: File list, uninstall manifest
