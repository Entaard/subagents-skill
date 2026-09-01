# Promotion contract

Canonical owner: `promotion_workflow`

Promotion is an explicit user action over closed-run logs. It is never a stage of an active task and never silently edits canonical policy.

## Inputs and knowledge records

The workflow may read closed-run logs, promoted knowledge, their machine-local statistics, and source policy required to test a proposed edit. It groups factual observations, checks provenance, tests a candidate rule's recognizer and falsifier, and records disagreements. A malformed input is quarantined and reported; validation never repairs the material it is validating.

A promoted knowledge item has a stable ID, class, status, rule, qualifier, recognizer, falsifier, provenance, and integrity hash. Stable IDs are immutable opaque identifiers in the `sage-knowledge-v1` namespace; changing portable content never changes or silently reassigns an ID. Machine-local usage, dates, counts, and cost measurements remain local metadata rather than portable rule text. Disuse alone never removes knowledge. Retirement requires a fired falsifier or an explicit user decision for an unfixable item, with the observation retained.

### Portable projection and equivalence

`KnowledgeRecordProjection/v1` contains exactly `stable_id`, `class`, `status`, `rule`, `qualifier`, `recognizer`, `falsifier`, and `provenance`. It excludes the integrity hash and all machine-local usage, date, count, cost, cache, and landing metadata. Every string is Unicode NFC with CRLF and CR converted to LF; object keys are sorted; arrays retain their declared order except provenance, whose normalized entries are sorted by canonical bytes. The resulting value is serialized as UTF-8 JSON with no insignificant whitespace using `sage-json-v1`, then hashed with SHA-256.

The stored integrity hash is that projection hash. Readers recompute and compare it before indexing, loading, or reconciliation; a stale or malformed stored hash quarantines the record rather than being silently refreshed. Equivalent content means equal `KnowledgeRecordProjection/v1` bytes, not merely equal rendered text or equal stable ID. A duplicate stable ID with different projection bytes is a conflict even if a non-portable field makes the full records look similar. A projection-hash collision with unequal canonical bytes is a hard error and preserves both inputs for human disposition.

## Installed promotion: default

The default command writes only to an installed-only policy and promoted-knowledge overlay. It does not change the source repository or generated distribution. Future runs on that installation may selectively load the overlay through the promoted-knowledge index.

The write is staged, validated, and atomically installed where supported. Its entry is registered in the ownership receipt as user state so an update preserves it and complete removal can identify it. An active run, open run store, or unclassified destination rejects the promotion.

## Global promotion: explicit

The explicit global option writes only to the Sage source repository after the same evidence, review, and degradation gates. It does not update an installed tree. Its final result prints the exact repository-root install/update command the user may run later.

Global promotion must preserve unrelated dirty work and may modify only declared source paths. A source-hash mismatch or ambiguous source repository pauses before mutation.

## Stable-ID reconciliation

On install/update, reconcile repository knowledge against the installed overlay by stable ID:

1. A repository item with no overlay twin becomes canonical normally.
2. An overlay-only item remains installed-only and is preserved.
3. When both carry the same stable ID and equivalent content hash, load the repository item once and archive the redundant overlay record with a reconciliation pointer.
4. When both carry the same stable ID but differ, the repository copy becomes canonical only after the update records the conflict and archives the overlay copy intact; never merge rule text automatically.
5. Duplicate stable IDs within one source are an error and stop the update before replacement.

Reconciliation is idempotent. Re-running the same update neither reloads a duplicate nor loses the archived provenance. The archived overlay row retains its validated projection hash and a stable pointer to the canonical repository row; the second application produces the same canonical state hash as the first.

The cases in [`promotion-reconciliation-cases.json`](promotion-reconciliation-cases.json) freeze formatting-equivalence, divergent-content, collision/conflict, and idempotent rerun expectations for the Phase 1 implementation.

## Completion and removal

A promotion result names destination, stable IDs created/revised/retired, evidence and review results, paths changed, source hashes, and the follow-up install command when global. It never reports an installed tree changed after a global-only write.

Complete uninstall removes the installed overlay only with the user's explicit complete-removal confirmation. The source repository and globally promoted source remain untouched. `--keep-data` preserves the overlay together with other runtime data and records that exception.
