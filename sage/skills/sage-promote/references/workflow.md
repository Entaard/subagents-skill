# Promotion workflow

Promotion is the only Sage workflow that converts raw run facts into reusable knowledge. It operates after task execution, never in the middle of a Sage run.

Resolve `sage-promote` from `PATH`; the default installation places its wrapper under `~/.local/bin` and its Python implementation under `~/.local/share/sage/scripts`. Custom installations must use their recorded binary and state roots.

## Preflight and consolidation

1. Resolve every selected run ID and call `sage-promote inspect --run-id <id>` with one flag per run. The command validates closed status, run schema, rendered projection, contiguous current-run facts, and the matching terminal fact. It rejects the entire pass if any run in that installation remains active.
2. Read the returned facts as observations, not lessons. Group observations that concern the same prospective rule; retain disagreements, failed attempts, negative evidence, scope, and source identity. Do not repair malformed input in place. Quarantine or report it.
3. Compare each group with active promoted records. Separate a genuinely reusable decision rule from a one-run outcome, preference, date, price, model name, or incidental implementation detail. Local usage, counts, dates, and costs never enter portable rule text.
4. Draft one candidate per stable rule. Similar observations may support one record; unrelated claims need separate records. Classify it as a deterministic invariant (at least one distinct closed run), empirical heuristic (at least three), or shared-policy guidance (at least six plus behavioral evaluation). Every class needs independent refutation. Record the evidence for the advisory judgment that the runs and refuter are semantically independent.
5. Compare every active stable ID in the pre-batch destination snapshot other than the candidate. Name them all in the novelty review and disposition the candidate as novel, a revision, or accepted overlap with rationale. For a multi-candidate batch, separately disposition every active create/revise peer as distinct or accepted overlap. Tie expected utility to the exact recognizer and require a positive net assessment.

Never promote credentials, privileged handles, raw prompts, raw tool payloads, user identity, private paths, or confidential content into portable text. Generalize only what the evidence supports and retain protected evidence through hashes and locators; if safe generalization would destroy the qualifier or falsifier, leave the observation unpromoted.

## Candidate shape

Use this JSON shape before `prepare` adds the canonical integrity hash:

```json
{
  "schema_version": "1.0",
  "stable_id": "sage-knowledge-v1:opaque.stable-name",
  "class": "workflow_rule",
  "status": "active",
  "rule": "The concise reusable instruction.",
  "qualifier": "The exact conditions in which the rule applies.",
  "recognizer": "The observable signal that should load the rule.",
  "falsifier": "The concrete observation that would disprove or retire it.",
  "provenance": ["run:<run-id>", "artifact:ART-RECORD"],
  "promotion": {
    "action": "create",
    "evidence_class": "deterministic_invariant",
    "promotion_actor": "promotion-actor-id",
    "reviewed": true,
    "review_evidence": ["verification:V1"],
    "independent_refutation": ["verification:V-REFUTE"],
    "independence_review": {"judgment": "independent", "evidence": "separate evidence path", "limitations": "semantic judgment"},
    "expected_utility": {"recognizer": "The observable signal that should load the rule.", "expected_benefit": "avoids the recorded failure", "expected_cost": "one indexed load", "net_assessment": "positive"},
    "novelty_review": {"compared_stable_ids": [], "peer_dispositions": [], "disposition": "novel", "rationale": "no active peers"},
    "behavioral_evaluation": [],
    "expected_prior_sha256": null
  }
}
```

For multiple runs, artifact and verification references must be qualified: `artifact:<run-id>:<artifact-id>` and `verification:<run-id>:<verification-id>`. `run:<run-id>` provenance must exactly equal the selected run set. Provenance artifacts must be adopted and review verifications must pass.

`create` requires no prior record and a null prior hash. `revise` requires the stable ID's current projection hash. The maturity, utility, novelty, independence, refutation, peer-disposition, and behavioral gates above apply only to those two actions. `retire` retains reviewed evidence and the current projection hash, and additionally requires `status: retired`, a concrete reason, and `retirement_basis: falsifier_fired|user_decision`. Disuse, age, and lack of citation are not retirement evidence.

## Review

Refute before landing for every create or revise candidate. Check that the rule is supported rather than merely plausible, its qualifier is no broader than the evidence, its recognizer is observable, its falsifier could actually fire, and it does not contradict stronger active knowledge. Use an independent verifier with a bounded, read-only, default-to-refute brief. Shared-policy guidance also receives a behavioral evaluation. A verifier report remains an unprivileged claim; the promotion actor records the decision and cites passing run verifications.

If a candidate conflicts with an existing stable ID, do not merge text or mint a new ID to evade the conflict. Report the conflict and choose revise, retire, or leave both unchanged. If the falsifier cannot be stated, leave the observation in the closed log; it is not ready for promotion.

## Prepare, land, and report

Prepare each reviewed candidate. One deterministic batch contains at most five unique stable IDs. Sage validates all candidates against one pre-batch destination snapshot, checks explicit peer dispositions, and sorts them into canonical stable-ID order. Under one lifecycle lock it durably records hashed prior/next bytes before the first per-file atomic replacement. A caught failure restores the prior generation; after process loss, a fresh reader or promoter completes and verifies the next generation under the lock before exposing it. Stop before landing and report all excess candidates when the request is larger.

```text
sage-promote prepare --candidate <draft.json> --output <candidate.json>
```

Land to this installation by default:

```text
sage-promote --candidate <candidate.json> --run-id <closed-run-id> [--run-id <closed-run-id> ...]
```

Use source-global promotion only when the user explicitly requests it. Resolve and pin the checkout's current revision immediately before landing:

```text
sage-promote --candidate <candidate.json> --run-id <closed-run-id> [--run-id <closed-run-id> ...] \
  --global --source-root <checkout> --expected-source-revision <git-sha>
```

Global promotion changes only declared source knowledge paths. It does not reinstall Sage and must print the checkout's `sage/install.sh` as the later installation command. Preserve unrelated dirty work.

Return one compact report naming selected runs, destination, stable IDs and actions, review evidence, changed paths, projection hashes, index result, conflicts, quarantined inputs, and the follow-up install command when global. Never claim an installed tree changed after a global-only write.
