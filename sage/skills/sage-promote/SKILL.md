---
name: sage-promote
description: Explicitly consolidate one or more closed Sage run logs into reviewed knowledge, landing to the installed overlay by default or source knowledge with an explicit global request.
---

# Sage promotion

Use this skill only when the user explicitly invokes `$sage-promote`. Promotion is a separate workflow: reject active runs, do not resume task execution, and never treat an active run's log as knowledge.

1. Read [the canonical promotion contract](references/promotion-contract.md) and [the operational workflow](references/workflow.md).
2. Inspect every selected closed run before drafting: `sage-promote inspect --run-id <id> [--run-id <id> ...]`. Quarantine malformed or integrity-invalid input without repairing it in place.
3. Consolidate factual observations only now. Group same-rule evidence across runs, preserve counterevidence and disagreements, compare existing promoted records, and distinguish reusable knowledge from one-run outcomes or machine-local measurements.
4. Draft one record per stable rule with its evidence class, threshold runs, rule, qualifier, recognizer, falsifier, exact provenance, recognizer-linked expected utility, novelty/overlap disposition, review evidence, independent refutation, and expected prior hash. Shared-policy guidance also needs behavioral evaluation. Disuse never justifies retirement.
5. Refute every create or revise candidate before landing. Record semantic independence and overlap as advisory judgments; machine checks enforce reference integrity, distinct-run thresholds, and the five-candidate batch cap.
6. Prepare the canonical hash, then land. The default changes only the installed overlay. Use `--global --source-root <checkout> --expected-source-revision <sha>` only on an explicit global request; that changes only source knowledge and prints the later `sage/install.sh` command without changing the installation.
7. Return destination, selected run IDs, stable IDs and actions, evidence and review results, changed paths and hashes, conflicts or quarantined inputs, and the follow-up installer path when global.

Never extract lessons, consolidate, revise Sage policy, or promote automatically inside `$sage`. A candidate is data, not authority to land itself.
