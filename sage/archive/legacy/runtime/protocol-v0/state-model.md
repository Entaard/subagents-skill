# Provisional state model

## Three kinds of fact

A request expresses intent and preconditions. It never changes state by being sent. A transition records a request the core accepted after authorization and invariant checks. An observation records a native fact reported by an adapter and cannot mutate authoritative state directly.

Mutating requests carry a command ID, run ID except for creation, a connection-principal-scoped idempotency key, canonical payload hash, and expected run version except for creation. `payload_sha256` is SHA-256 over the payload after Unicode NFC/LF normalization and `sage-json-v1` UTF-8 serialization with sorted object keys, preserved array order, no non-finite number, and no insignificant whitespace. The idempotency request identity is operation, run ID, expected run version, and payload hash; command ID is correlation and does not change replay identity. Idempotency lookup precedes optimistic-version validation: the same authenticated connection principal, key, and request identity returns the stored result even if its expected version is now stale; the same scoped key with a different identity is rejected before version checking. The same key on another authenticated principal is a separate namespace.

The scheduler alone validates and commits a proposed plan revision, admits attempts, and grants dispatch tickets. Adapter observations are accepted only for handles bound to that adapter connection. Workers submit results or artifacts only for their own attempts. Policy actors propose plans, briefs, findings, verification, and dispositions but cannot commit their own proposals, bind workers, lease resources, manufacture approvals, or close as an operator.

## Lifecycle distinctions

`prepared`, `running`, `idle`, `turn.completed`, `result.received`, `result.accepted`, `verification.recorded`, and `unit.completed` are distinct. Idle never implies completion. A valid result does not complete a unit until the required terminal state and verification are also recorded.

Every attempt binds an immutable plan revision, unit-spec revision, brief revision, and brief hash. Retry creates a new attempt. A later plan never redefines an attempt in flight.

An observation receives a server-assigned `run_seq` when ingested. That sequence orders Sage ingestion only; native source epoch and sequence carry source-local evidence. Timestamps do not establish cross-worker causality. Each delivery claim is exactly one of replayable, snapshot-reconcilable, or ephemeral, with missing cursors and source IDs represented as null rather than invented.

## Reconciliation

On restart, validate the authoritative-state/audit checkpoint, then reconcile unresolved external intents before nonterminal worker and turn handles. An intent whose external effect may have happened but whose handle was not durably recorded is `sent_unknown`. It is discovered through a proven native key/snapshot or routed to operator disposition; it is never retried blindly.

Classify each worker and turn as prepared, running, idle, completed, failed, lost, or unknown. Validate result and artifact hashes before acceptance. Unknown side-effecting work freezes result acceptance and resource reuse. Resume deterministic scheduling only when every ambiguity is closed. Judgment boundaries enter `AwaitingPolicy` unless a durable policy actor was independently configured and reconciled.

## Provisional transition families

The schema enumerates the operations needed to make Phase 0 fixtures concrete: create run, propose or commit a plan revision, admit or bind an attempt, steer or interrupt, record and disposition findings, accept results, record verification, adopt artifacts, grant or release a lease, record approval, begin drain, and close run. Their names and payloads remain v0 and may be revised by the first managed feasibility slice.

The [`idempotency-sequence.json`](fixtures/sequences/idempotency-sequence.json) fixture exercises accepted, stale-version replay, same-key/different-body rejection, and separate-principal namespace behavior. It is a protocol oracle, not an implementation claim.
