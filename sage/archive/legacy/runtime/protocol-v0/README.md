# Sage runtime protocol v0

Status: **provisional, single-production-adapter draft**.

This protocol is the minimum deterministic vocabulary needed to test a future managed slice. It is not a cross-harness contract, does not freeze the worker port, and may change incompatibly before a separately approved portability proof. Phase 0 implements no scheduler, store, driver, or privileged endpoint.

The JSON Schema is the wire contract. [`generated/runtime-envelope-v0.ts`](generated/runtime-envelope-v0.ts) is a deterministic language binding generated from it and checked for drift; it does not make TypeScript the protocol implementation language.

- [`schemas/runtime-envelope-v0.schema.json`](schemas/runtime-envelope-v0.schema.json) defines versioned request, transition, capability, observation, and approval record envelopes.
- [`state-model.md`](state-model.md) separates intent, accepted transition, and observed native fact.
- [`adapter-contract.md`](adapter-contract.md) describes provisional capability negotiation and worker/turn semantics.
- [`security-and-privacy.md`](security-and-privacy.md) defines authenticated principals, reachability boundaries, data classes, approvals, retention, and deletion.
- [`fixtures/`](fixtures/) contains sanitized valid and rejection cases.

JSON is the wire format. The implementation language and persistence engine are outside the contract.
