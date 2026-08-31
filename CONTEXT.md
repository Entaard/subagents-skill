# Sage

Sage is an orchestration policy and optional managed runtime for coordinating agent work while preserving evidence, safety rails, and durable handover.

## Language

**Light mode**:
The Codex-native Sage experience in which the root model follows Sage policy and owns planning, dispatch, supervision, and bookkeeping. It has no external authoritative Sage scheduler.
_Avoid_: Text-only mode, unmanaged mode

**Managed mode**:
The Sage experience in which an external `sage-core` authoritatively owns deterministic coordination and durable run state while a policy actor retains judgment.
_Avoid_: Global mode, portable mode

**Run log**:
Append-only facts and evidence produced by a Sage run for later consolidation. A run writes its own log but does not mine raw logs from earlier runs.
_Avoid_: Knowledge, memory

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
