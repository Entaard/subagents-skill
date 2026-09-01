# Ownership boundaries

The invariant inventory uses six owner classes. An owner is the sole authority for a rule's semantics; other documents may point to it but may not restate it as a second authority.

## Policy

Owns judgments: delegation safety and value, decomposition, topology, task requirements for placement, evidence sufficiency, triage, assumptions, gaps, handover policy, completion, and the memory access boundary. Canonical sources are under [`../../policy/`](../../policy/).

## Artifact schema

Owns the portable representation of plans, unit revisions, briefs, results, evidence, findings, dispositions, verification, coordination outcome, and run records. It validates shape and cross-reference invariants but does not decide whether evidence is persuasive. Canonical sources are under [`../../artifacts/schemas/`](../../artifacts/schemas/).

## Runtime

Owns deterministic transition legality, authenticated roles, idempotency, dependency readiness, bounded admission, attempts, capability snapshots, observations, reconciliation, approvals, leases, retention, and deletion records. Phase 0 defines only the provisional protocol and threat model under [`../../runtime/protocol-v0/`](../../runtime/protocol-v0/); it implements no scheduler or store.

## Codex experience

Owns explicit invocation, the six-step user flow, native Light-mode interaction, report/resume presentation, and the repository-root installation lifecycle. Phase 0 defines the lifecycle contract but leaves the skill and native mapping to Phase 1.

## Adapter

Owns versioned host facts: concrete tool calls, worker and turn handles, model and effort resolution, sandbox and worktree mapping, event delivery, context sensors, approval round trips, and requested-versus-effective capability evidence. No host-specific mechanic belongs in canonical policy.

## Promotion workflow

Owns consolidation of closed-run facts into candidate knowledge, falsifier testing, stable knowledge IDs, destination choice, installed-overlay reconciliation, and retirement. Active runs never invoke this owner.

## Extraction rule

The existing distribution remains the behavioral baseline during Phase 0. A source pointer in the inventory proves where an obligation came from; it does not make that host-specific file canonical. When a baseline mechanism cannot be made portable, its policy intent moves to policy and its concrete implementation moves to the adapter or experience owner. Assumptions, gaps, `AwaitingHuman`, verification, coordination checks, rails, and completion duties are never discarded as mere mechanics.

