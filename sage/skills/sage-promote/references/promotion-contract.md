<!-- generated from sage/docs/phase0/promotion-contract.md sha256:5ff6538b3b6b0655b91bef58704fdb3225cad1b27f89c0feb856b97890a5c049; do not edit -->

# Promotion contract

Canonical owner: `promotion_workflow`

Promotion is an explicit user action over closed-run logs. It is never a stage of an active task and never silently edits canonical policy.

## Inputs and knowledge records

The workflow may read closed-run logs, promoted knowledge, their machine-local statistics, and source policy required to test a proposed edit. It groups factual observations, checks provenance, tests a candidate rule's recognizer and falsifier, and records disagreements. A malformed input is quarantined and reported; validation never repairs the material it is validating.

A promoted knowledge item has a stable ID, class, status, rule, qualifier, recognizer, falsifier, provenance, and integrity hash. Stable IDs are immutable opaque identifiers in the `sage-knowledge-v1` namespace; changing portable content never changes or silently reassigns an ID. Machine-local usage, dates, counts, and cost measurements remain local metadata rather than portable rule text. Disuse alone never removes knowledge. Retirement requires a fired falsifier or an explicit user decision for an unfixable item, with the observation retained.

## Selective create and revise gates

Every create or revise candidate declares one evidence class. A deterministic invariant needs at least one selected closed run; an empirical heuristic needs at least three distinct selected closed runs; shared-policy guidance needs at least six. Every class also needs a passing independent refutation. Shared-policy guidance additionally needs a passing behavioral evaluation that performs the behavior the recognizer is meant to trigger. Distinct run IDs and reference integrity are machine-checked. Whether runs or reviewers are semantically independent, and whether an overlap is material, remain explicit advisory judgments.

The candidate records recognizer-linked expected benefit, expected retrieval/application cost, and a positive net assessment. Its novelty review names every active stable ID in the pre-batch destination snapshot other than itself and dispositions the candidate as novel, a revision of an existing ID, or accepted overlap with rationale. It separately dispositions every active create/revise peer in the same batch as distinct or accepted overlap. A new stable ID may not evade an unresolved destination or batch-peer overlap.

Promotion rejects duplicate candidate stable IDs, sorts at most five candidates into canonical stable-ID order, and validates the whole batch against one closed-run set and one pre-batch active snapshot. Under one lifecycle lock it computes the complete post-batch record set and index before writing. Before the first data replacement, it atomically writes and fsyncs a write-ahead recovery authority plus its parent directory; the authority binds every canonical target locator to hashed prior and next bytes. Each record and the index then receives its own immediate atomic replacement rather than pretending that several filesystem replacements are one primitive.

A caught write failure restores and fsyncs the complete prior byte set before durably removing the authority. Process loss may leave immediate storage partially replaced, but a fresh reader or promoter consumes the authority under the lifecycle lock, accepts only a recorded prior/next version, idempotently completes the next generation, verifies every target, and durably removes the authority before exposing promotion state. Thus recovery yields the complete prior generation after a caught rollback or the complete next generation after process loss, never a mixed visible generation. Concurrent promotion commands cannot interleave. A request larger than five stops before landing and names every excess candidate.

Retirement is a distinct legacy-compatible action. It retains reviewed evidence, the exact prior projection hash, integrity validation, retired status, and a falsifier-fired or explicit-user-decision basis with reason. Evidence-class maturity thresholds, independent refutation, expected utility, novelty, independence review, peer dispositions, and behavioral evaluation apply only to create and revise.

### Portable projection and equivalence

`KnowledgeRecordProjection/v1` contains exactly `stable_id`, `class`, `status`, `rule`, `qualifier`, `recognizer`, `falsifier`, and `provenance`. It excludes the integrity hash and all machine-local usage, date, count, cost, cache, and landing metadata. Every string is Unicode NFC with CRLF and CR converted to LF; object keys are sorted; arrays retain their declared order except provenance, whose normalized entries are sorted by canonical bytes. The resulting value is serialized as UTF-8 JSON with no insignificant whitespace using `sage-json-v1`, then hashed with SHA-256.

The stored integrity hash is that projection hash. Readers recompute and compare it before indexing, loading, or reconciliation; a stale or malformed stored hash quarantines the record rather than being silently refreshed. Equivalent content means equal `KnowledgeRecordProjection/v1` bytes, not merely equal rendered text or equal stable ID. A duplicate stable ID with different projection bytes is a conflict even if a non-portable field makes the full records look similar. A projection-hash collision with unequal canonical bytes is a hard error and preserves both inputs for human disposition.

The runtime index contains only stable ID, class, status, qualifier, recognizer, projection hash, source class, and protected locator. It is bound to the exact ordered stable-ID/projection/source/locator input manifest hash. Listing the index supports selection without preloading every rule or falsifier; a runtime loads portable rule content only by explicitly selected stable ID.

## Installed promotion: default

The default command writes only to an installed-only policy and promoted-knowledge overlay. It does not change the source repository or generated distribution. Future runs on that installation may selectively load the overlay through the promoted-knowledge index.

The write is staged, validated, and atomically installed where supported. Its entry is registered in the ownership receipt as user state so an update preserves it and complete removal can identify it. An active run, open run store, or unclassified destination rejects the promotion.

## Global promotion: explicit

The explicit global option writes only to the Sage source repository after the same evidence, review, and degradation gates. It does not update an installed tree. Its final result prints the exact `sage/install.sh` command the user may run later.

Global promotion must preserve unrelated dirty work and may modify only declared source paths. A source-hash mismatch or ambiguous source repository pauses before mutation. Its follow-up command is the source checkout's `sage/install.sh`.

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

A promotion result names destination, stable IDs created/revised/retired, paths changed, source hashes, and the follow-up install command when global. Create/revise results additionally carry evidence class and threshold evidence, independent refutation, advisory independence and overlap judgments, recognizer-linked expected utility, and behavioral evaluation where required; retire results carry their reviewed evidence and exact prior hash. A result never reports an installed tree changed after a global-only write.

Complete uninstall removes the installed overlay only with the user's explicit complete-removal confirmation. The source repository and globally promoted source remain untouched. `--keep-data` preserves the overlay together with other runtime data and records that exception.
