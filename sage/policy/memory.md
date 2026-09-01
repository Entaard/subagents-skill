# Memory boundary

Policy owner: `policy.memory`

Sage has three memory classes with non-overlapping access rules.

| Class | Runtime access | Runtime writes | Promotion access |
| --- | --- | --- | --- |
| Promoted knowledge | Selective input through its index | none | may create, revise, retire, or reconcile after review |
| Current-run log | Read only to coordinate or recover this run; never mined for a reusable lesson | append-only facts, decisions, outcomes, usage, and evidence pointers | becomes eligible only after the run closes |
| Closed-run log | no task-time search or lesson retrieval | none | input to an explicit promotion workflow |

Canonical policy is runtime input but is not memory. A current run may use its own structured state to plan, reconcile, verify, and render; it may not consolidate observations, count confirmations, infer a reusable lesson, or edit policy. It never scans raw prior ledgers, journal tails, closed logs, or archives for a same-shape precedent.

Current-run output records plan revisions, decisions, estimates and actual usage with provenance, failures and signatures, findings and dispositions, assumptions, gaps, effective capabilities and degradations, artifacts, verification, coordination outcome, and evidence pointers. Raw prompts or tool payloads follow the run's data classification and retention policy; facts are redacted before append.

Promotion is a separate, user-invoked action performed only on closed runs. It groups observations, tests candidate rules and falsifiers, and decides whether they become promoted knowledge. The [promotion contract](../docs/phase0/promotion-contract.md) owns destinations, stable-ID reconciliation, removal, and update behavior.

Completion criterion: each read or write names one of these classes. An implementation that cannot prove the class and access purpose rejects the operation rather than treating every persistent file as memory.
