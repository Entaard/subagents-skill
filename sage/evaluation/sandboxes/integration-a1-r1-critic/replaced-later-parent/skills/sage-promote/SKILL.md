---
name: sage-promote
description: Review closed Sage runs and explicitly land bounded, refutable knowledge. Invoke only when the user explicitly requests $sage-promote.
---

# Sage promotion

Use only after explicit `$sage-promote` invocation. Promotion is a separate task over closed-run evidence: it never resumes a source task, mines an active run, or edits Main Sage. Preserve the user’s scope, authority, and explicit model choices.

1. Resolve the knowledge helper, store, and every run directory explicitly. Use `sage/scripts/sage_knowledge.py` in this checkout or the installed sibling `<target-root>/sage/bin/sage_knowledge.py`; never derive a state root from the task repository. Read [promotion](references/promotion.md) for qualification, roles, and landing.
2. Qualify each source as an integrity-valid terminal `completed`, `failed`, or `stopped` run with reconciled effects. Quarantine invalid inputs unchanged. Bound the run set and candidate count before extraction.
3. Extract candidate rules, cues, qualifiers, falsifiers, direct evidence, counterevidence, alternative explanations, and retrieval feedback. Reconcile each with the retained stable-ID lineage. A tiny pass with no reusable candidate reports `no_change` directly and spawns no ceremonial team.
4. For an actual create, correction, contest, refutation, or retirement, obtain three distinct live actors: a candidate author, adversarial refuter, and reviewer. The coordinator does not invent their IDs or fill one of those roles. Use an optional Luna-high scout for a worthwhile bounded corpus, Sol-high/xhigh for guided candidate authorship, Astra-high for ambiguous or causal refutation, and a separate Sol-xhigh reviewer. These are uncalibrated priors; capability and user choice win.
5. Give the refuter the proposal, declared class, source evidence, counterevidence, and relevant retained record, without a target verdict. `refutation.outcome: passed` means the proposed action survived that challenge; it never means a refuted earlier rule is true. The reviewer independently dispositions every finding and applies the class-specific evidence predicate. Structural identity separation is not evidence of behavioral independence.
6. Draft the exact proposal and use the public CLI in [knowledge](references/knowledge.md). Confounded transfer stays `provisional`; unresolved material contradiction stays `contested`; a fired falsifier may become `refuted`; intentional removal becomes `retired`. Review votes, repetition, selection frequency, and disuse cannot replace evidence.
7. Stage a complete generation against the observed current pointer, validate the store, then activate only if the target’s recorded parent and live expected pointer still match. The coordinator alone owns the final risk decision and landing. On a bad landing, validate and `rollback` to a retained generation; history remains.
8. Report source runs, quarantines, no-change reason or each stable-ID action, actors and live independence evidence, class gate and counterevidence dispositions, staged/active generation hashes, exact paths, rollback target, checks, and unknowns. Never claim installed behavior, cost, model placement, or semantic proof without direct observation.

The helper validates structure, reference closure, immutable generation integrity, and cooperative expected-pointer checks. It is neither a semantic grader nor a physical lease.
