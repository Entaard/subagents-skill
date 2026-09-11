# Provisional adapter contract

An adapter offers semantic capabilities for one concrete environment fingerprint. The core never grants a guarantee from an adapter name.

## Capability evidence

Before planning, the adapter returns an environment offer bound to its version, working directory identity, configuration hash, trust configuration, and approval-policy hash. Worker preparation and every turn return an effective capability snapshot.

Each capability record states operation and semantic version, availability, authority source and trust state, scope, control strength where meaningful, delivery, durability boundary, restart boundary, failure behavior, evidence, and known uncovered paths. A plan marks predicates required or preferred. A false required predicate rejects admission or requires a plan revision; a false preferred predicate uses the named fallback.

Record requested and effective model, effort, permissions, sandbox, and isolation separately. A prompt cannot emulate a missing resolved-model observation, read-only boundary, resume guarantee, or approval channel. Capability degradation stops affected admissions and triggers the safety behavior in policy; restoration has no retroactive effect.

## Opaque identities

`WorkerRef` and `TurnRef` are opaque to the core except for versioned lifecycle fields. A worker is not assumed to be a process, child, session, or thread. Turn identity remains explicit so steer and interrupt cannot race against a later turn.

## Candidate operations, not a frozen port

The first feasibility slice may need semantic operations equivalent to environment offer, prepare worker, start turn, steer active turn, follow up from idle, interrupt a named turn, reconcile a worker, observe from a checkpoint, and dispose. Unsupported operations return typed unsupported results.

This list is a hypothesis to test. Phase 0 does not require every operation, prescribe method signatures, or claim that one host's start/continue surface is equivalent to another host's explicit turn lifecycle.

## External transaction boundary

Worker preparation and turn start are external effects. Persist a dispatch intent and outbox record before preparation; persist the returned worker reference and effective capabilities before creating the start-turn intent. After any ambiguous response, reconcile before another call. A driver that cannot separate preparation from execution declares that limitation and is not admitted for unattended side-effecting work.

Resource coordination, isolation, approval, artifact storage, and usage normalization are adjacent semantic ports. Every side-effecting operation uses durable intent, idempotency key, opaque reference, and reconcile-before-retry. Unknown isolation prepare or revoke is never treated as quiescent without evidence.

## Deterministic adapter checks

Adapter checks publish a versioned predicate list, inputs, output shape, failure behavior, and known blind spots. A check that cannot run returns unavailable with evidence; it never returns pass.

The promoted-knowledge index reads only validated promoted-knowledge records. It validates each item's stable ID, portable projection, integrity hash, and status, orders accepted items deterministically by stable ID, and writes an index bound to the exact input manifest hash. A malformed, duplicate, or hash-invalid item is excluded and quarantined with a reason and protected locator. Index failure never falls back to a broad search of closed-run or current-run logs.

The rendered-record integrity check validates only its documented predicates, including required sections or structured fields, reference uniqueness and closure, allowed terminal states, and the projection/source-state binding supported by that checker version. Its report names every predicate evaluated, every known semantic blind spot, and whether the authoritative structured record was available. It does not make a judgment about evidence quality and it cannot promote a text projection into authoritative state.
