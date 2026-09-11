# Phase 0: ownership, artifacts, and evaluation

This directory records the extraction required by Phase 0 of the Sage Codex proposal. It defines contracts and fixtures without changing the production behavior of the existing distribution or implementing the later skill, driver, scheduler, or store.

## Deliverables

- [`invariant-ownership.json`](invariant-ownership.json) inventories the baseline corpus and assigns each invariant one owner.
- [`ownership-boundaries.md`](ownership-boundaries.md) defines the six owner classes and the extraction boundary.
- [`baseline-deltas.md`](baseline-deltas.md) names intentional contract changes that Phase 0 does not apply to the current distribution.
- [`promotion-contract.md`](promotion-contract.md) defines memory destinations and stable-ID reconciliation.
- [`lifecycle-contract.md`](lifecycle-contract.md) defines the universal installer receipt, update, recovery, and complete removal.
- [`../../policy/`](../../policy/) is the canonical host-neutral policy.
- [`../../artifacts/schemas/`](../../artifacts/schemas/), [`../../artifacts/generated/`](../../artifacts/generated/), and [`../../artifacts/fixtures/`](../../artifacts/fixtures/) define, generate language types for, and exercise artifact schema v1 and the lifecycle receipt.
- [`../../runtime/protocol-v0/`](../../runtime/protocol-v0/) drafts the explicitly provisional runtime envelopes and security model.
- [`../../evaluation/phase-1/`](../../evaluation/phase-1/) freezes the paired Phase 1 pilot before outcomes are visible.
- [`reviews/authority-privacy-review.json`](reviews/authority-privacy-review.json) records the independent exit-gate reviews, resolved findings, and challenged suggestions.
- [`../../scripts/check-phase0.py`](../../scripts/check-phase0.py) checks pointers, ownership, host leakage, schemas, generated type drift, fixtures, review status, and preregistration hashes.

Run `python3 sage/scripts/check-phase0.py --self-test` from the repository root to exercise the checker and every registered fixture.

## Exit gate

Phase 0 is complete only when all of the following are true:

1. Every baseline safety, evidence, completion, promotion, installation, and removal obligation has exactly one owner.
2. Sanitized representative runs validate against artifact schema v1 and the semantic checker rejects weakening cases.
3. The runtime contract remains provisional and contains no cross-host stability claim.
4. The authority/privacy review has no open blocker.
5. The Phase 1 task set, rubric, comparability rules, margins, and benefit gates are hash-frozen.
6. The Phase 0 checker and the existing baseline corpus checks pass.
