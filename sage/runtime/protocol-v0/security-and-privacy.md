# Authority, privacy, and approval contract

## Authenticated principals

Authority is derived from the authenticated connection endpoint and its short-lived capability, never from a caller-supplied payload field.

| Principal | Permitted authority |
| --- | --- |
| operator | create, stop, resume, delete, and approve within authenticated scope |
| policy actor | propose plans, briefs, findings, verification, and dispositions |
| scheduler | internal admission, dispatch tickets, and run-local scheduling |
| adapter | report native facts only for handles assigned to its connection |
| approval channel | attest a human decision bound to an authenticated operator and exact action digest |
| worker | submit result or artifact only for its own attempt |

Use separate role-specific endpoints and unforgeable capabilities. Same-user operating-system credentials are supporting evidence, not sufficient separation. The policy actor and workers cannot reach the store, scheduler/adapter endpoints, resource-coordinator credentials, or approval credentials. Model-visible environment variables, files, arguments, logs, and tool output never contain privileged capabilities. If those reachability boundaries cannot be enforced, managed writer and unattended guarantees are unavailable.

Request authorization is deny-by-default. `operator` may create runs, interrupt attempts, begin drain, and close runs. `policy actor` may propose plan revisions, steer or interrupt attempts, record or disposition findings, accept results, record verification, and adopt artifacts; it cannot commit its own proposal. `scheduler` may validate and commit plan revisions, admit attempts, bind workers, grant or release leases, and begin drain. `approval channel` alone may record an approval. Adapters report observations on their assigned handles and workers submit results or artifacts for their assigned attempts through separate typed endpoints; neither may invoke a policy or scheduler request. Every overlap, including interruption and drain, is authorized against authenticated scope and current run state rather than role name alone. The machine-readable [`authority-matrix.json`](authority-matrix.json) is the Phase 0 oracle for these request families.

## Threat boundaries

Assume model prompts, worker results, tool output, fetched content, repository files, and displayed paths can be adversarial. Treat the policy actor as capable of shell execution where the host permits it. A role name or instruction is not isolation. A worktree separates version-control state but not credentials, processes, network, or the underlying filesystem.

Mutating resources require a canonical resource identity from the isolation provider and a deployment-wide coordinator. Leases use owner epochs and monotonic fencing tokens; a write guarantee exists only on a path that validates the current token or within a stronger isolation boundary. Loss of the coordinator rejects writer admission.

## Approval semantics

An approval record binds authenticated operator identity and approval-channel evidence to an `ActionDescriptor/v1`. That descriptor contains:

- run, unit, attempt, resource, lease, and fencing-token references;
- operation class and exact scope;
- the argument-descriptor and canonicalization versions, SHA-256 of the complete transient typed semantic arguments, and a complete intended-side-effect list;
- canonical working-directory identity, environment hash, and requested permission delta;
- native thread, turn, and item references where available, with absence represented as null;
- a one-shot nonce or an explicit bounded-reuse rule;
- an immutable reference to the user's authorization and SHA-256 of their exact words.

`ActionArguments/v1` is the exact semantic argument object presented by the authenticated native request and sent to the operation. It is not a display string or a selected subset. It permits only strings, integers, booleans, null, arrays, and objects. String values and object member names are Unicode NFC with newlines normalized to LF; normalization collisions between member names are invalid. Object keys are then sorted and arrays retain declared order. Serialize the complete argument object as UTF-8 JSON without insignificant whitespace using `sage-json-v1`; `arguments_sha256` is SHA-256 of those exact bytes.

The approval broker renders the exact transient arguments to the operator, computes the digest, and persists the digest rather than raw arguments. Raw arguments follow the ordinary confidential/restricted retention rules and require an explicit protected locator if retained. During compare-and-consume, the broker independently canonicalizes the matching authenticated native request's live arguments and requires the same digest. A model-supplied digest or display text is never sufficient.

`ActionDescriptor/v1` uses the same value restrictions and canonicalization over the complete descriptor; `action_digest` is SHA-256 of those exact bytes. The record names descriptor, argument-descriptor, and canonicalization versions. Any implementation unable to reproduce either digest denies the action.

Changing any bound field requires a new approval. Expired, revoked, already-consumed, differently digested, or ambiguously grouped actions are denied. Network approvals are serialized unless the native surface proves one request maps to one action. An approval-channel record may either satisfy the native decision or decline so the host asks; it never pretends two independent approvals occurred when one allow response suppressed the other.

Validation of authenticated principal, descriptor digest, current lease and fencing token, native correlation, expiry, revocation, and remaining use count occurs in the same durable compare-and-consume transition that answers the matching native request. The transition appends the unique consumption ID before or atomically with the native allow response. A crash cannot leave an allow response that is safely replayable from an unconsumed record. `one_shot` means exactly one permitted consumption; `bounded` names a positive maximum and exact action scope, and every consumption is separately correlated. A deny record has no consumptions.

## Data classification

Classify before persistence and redact before writing.

| Class | Examples | Default persistence |
| --- | --- | --- |
| public | published sources, explicitly public artifacts | content may be retained with provenance |
| internal | run IDs, normalized state, non-secret handles, aggregate usage | retained under the run policy |
| confidential | prompts, results, diffs, paths, user content | hash plus protected locator; raw opt-in |
| restricted | credentials, capabilities, approval secrets, private keys | never persisted in run artifacts or fixtures |

Raw native events and tool payloads default to no retention. When audit requires raw content, the run policy names the fields, purpose, protected store, access scope, and expiry. A hash plus locator is represented honestly; it is not a retained raw record. Fixtures are sanitized and contain no live credential, user identity, absolute home path, or privileged handle.

## Retention and deletion

Every run binds a retention policy for structured state, audit metadata, artifacts, raw opt-in payloads, and backups created for that run. `forever` is not an implicit default. Legal hold is an explicit operator decision with scope and reason. Installation lifecycle backups that preserve displaced user or configuration content are owned by the installation receipt, not by any run; run retention and deletion cannot select them. They remain until their bound restoration succeeds or an explicit ownership-transfer receipt names a new owner and policy.

Append-only applies while an audit partition is retained: prior entries are never rewritten in place. Each run has a separately deletable audit partition whose immutable headers and protected payload envelopes are covered by the run retention policy. Payloads may use per-run encryption keys so expiry can crypto-shred content without falsifying the retained hash chain. A policy that retains a minimal audit header must enumerate its exact fields and expiry; no audit metadata is retained forever by implication.

On expiry or authorized deletion, remove protected payloads, artifacts, locators, per-run keys, secondary-index entries, unresolved outbox bodies, run-owned backups, caches, and declared replicas. Never remove an installation/displaced-user recovery backup through run deletion; only the lifecycle receipt's restoration or transfer rule can release it. Legal hold pauses only the named classes and records authority, reason, start, and review/expiry time. Export transfers require a new retention owner and receipt before the source is removed.

After processing the run partition, append a tombstone to the separate deletion audit containing only run ID, policy ID, deleted classes, requested and completed times, authorization-evidence hash, pre-deletion partition/proof hashes, replica completion states, and bounded partial-failure codes with their next owner/action. It contains no content locator, prompt, result, path, credential, or replayable raw payload. Partial deletion remains open and retries only the named uncompleted targets; it never reports full deletion. Destroying a complete expired partition is compatible with append-only because the deletion audit records destruction rather than rewriting its entries.

Logs and rendered projections are derived from classified state and inherit the strictest contributing class. Debug output cannot bypass redaction. Access to stores and artifacts is least privilege, and exported artifacts receive an explicit new retention owner.

The retention scenarios in [`fixtures/retention-deletion-cases.json`](fixtures/retention-deletion-cases.json) freeze expiry, legal-hold, complete-deletion, and partial-replica-failure outcomes for the first persistence implementation.
