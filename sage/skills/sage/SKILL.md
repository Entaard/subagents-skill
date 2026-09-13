---
name: sage
description: Run a user-requested task with explicit quality criteria, adaptive Codex delegation, independent verification, durable evidence, and recovery. Invoke only when the user explicitly requests $sage.
---

# Sage

Use Sage only after explicit `$sage` invocation. Preserve the user’s scope, model choices, standing approvals, and effect boundaries. Continue routine in-scope work without ceremonial approval; ask only for essential user-only input or new authority.

Use GPT-5.6 or higher for all Sage-controlled reasoning work, including inline work, resumed workers, and nested delegation. Apply the [model eligibility policy](references/delegation.md#model-eligibility) before work or worker reuse, including on resume.

## Start or resume

For `report` or `resume`, read [recovery](references/recovery.md). For a new run:

1. Restate the bounded outcome. Define observable acceptance criteria and the task-specific excellence bar before building. Read [runtime paths](references/runtime.md), resolve and announce the shared root, and open a discoverable run for every work invocation, including inline work. Surface ambitious unsupported scope as staged milestones; do not weaken criteria or relabel a small demonstration as the full outcome.
2. Qualify the work as inline, orchestrated, or safety-paused. Keep tiny, coupled, cheaper-to-do work inline. For substantive work, build a dependency graph and reserve independent review, focused repair checks, and final integration. Read [run](references/run.md), then [delegation](references/delegation.md) before any dispatch.
3. Read [knowledge retrieval](references/knowledge.md) and query the helper from the same package and pinned root before final planning; refresh only after a changed cue, retrieval policy, or generation. An empty result is valid. A missing helper or rejected query is a reported installation/retrieval failure, not an empty result. Current evidence and user instruction win. Record exact selected revisions and later feedback. Ordinary task-time learning uses only promoted knowledge; inspection of closed runs or Sage policy edits requires that work to be in the user's explicit task scope. Promotion remains a separate explicit invocation.
4. Execute dependency-ready work. Gather cheap, decision-changing information before expensive choices; batch scouts that read the same corpus. Keep one active shared-workspace writer, including root. The root owns interpretation, risk, plan changes, adoption, finding disposition, integration, and completion.
5. Verify against [verification](references/verification.md). A substantial candidate receives independent review from the frozen artifact, original request, criteria, and minimum necessary environment—not the builder’s rationale. The root triages evidence rather than votes. Recheck fixes and final integration.
6. Checkpoint at stable boundaries and close only from observed criterion evidence. Generate the report from validated state. Return the deliverable first, then concise evidence, unknowns, and explicit human items.

Use the live collaboration-tool schema as authority. A full-history fork inherits the root’s model/effort and cannot override them; a fresh or bounded fork may request overrides. A fresh fork omits conversation history, not system, tool, repository, or sandbox context. `send_message` steers an active turn; `followup_task` wakes an idle worker. Reconcile with `list_agents`. Idle, missing, or interrupted is not completion.

The root model cannot be silently switched by this skill. It may request bounded Astra advice while retaining root decisions. Requested and effective model/effort are separate; absent effective observations remain `unknown`.

The state helper validates recorded facts, references, and transitions. It does not prove semantic quality, authority, independence, or a physical writer lease.
