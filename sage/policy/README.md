# Sage policy

This directory is the canonical, host-neutral source for Sage judgment and workflow. Exact JSON shapes live in [`../artifacts/schemas/`](../artifacts/schemas/), deterministic coordination lives in [`../runtime/protocol-v0/`](../runtime/protocol-v0/), and installation or promotion mechanics live in their Phase 0 contracts. A host profile may map these rules to concrete tools and models; it may not redefine them.

Each file declares one policy owner. The Phase 0 [invariant inventory](../docs/phase0/invariant-ownership.json) assigns every baseline obligation to exactly one canonical owner and preserves its source provenance.

- [`delegation.md`](delegation.md) — qualification, decomposition, placement, bounded planning, and estimation.
- [`contracts.md`](contracts.md) — briefs, results, assumptions, gaps, findings, decisions, and coordination outcomes.
- [`topologies.md`](topologies.md) — orchestration patterns and their stopping conditions.
- [`review.md`](review.md) — evidence, freeze/review/triage, behavior-shaping edits, and completion.
- [`recovery.md`](recovery.md) — failure signatures, rails, reconciliation, and handover.
- [`memory.md`](memory.md) — the three memory classes and the runtime/promotion access boundary.

The extraction preserves every baseline safety, evidence, and completion obligation. It also records proposal-mandated memory, promotion, artifact, and lifecycle deltas in [`../docs/phase0/baseline-deltas.md`](../docs/phase0/baseline-deltas.md); Phase 0 does not apply those deltas to the existing distribution. Generation and host packaging begin in a later phase.
