# Codex Sage rebuild requirements

These requirements are the acceptance source for the rebuild. “Must” is testable. Passing a design review does not imply the corresponding runtime or forward behavior has been observed.

## Product and scope

- **R-001 — Codex scope.** The active product must target the Codex collaboration surface only and must make no cross-host portability or managed-scheduler claim.
- **R-002 — Active entrypoints.** The active packages must remain `sage/skills/sage` and `sage/skills/sage-promote`, with consistent UI metadata and discriminating invocation descriptions.
- **R-003 — Separation.** Ordinary Main Sage task-time learning uses promoted knowledge, not closed-run logs or self-edited instructions. Explicit user requests to inspect history or maintain Sage authorize that bounded work; promotion remains a separate explicit invocation. Promotion must accept only closed runs and must not resume their tasks.
- **R-004 — Small architecture.** Operational judgment must live in concise skill/reference text. Dependency-free Python helpers are permitted only where deterministic behavior materially improves correctness. The rebuild must not reproduce a protocol bureaucracy approaching the legacy implementation’s size.
- **R-005 — Honest claims.** The product must not promise universal correctness, savings, isolation, exact model placement, token accounting, or evaluations that were not observed.

## Planning, task, and team

- **R-010 — Adaptive mode.** Sage must support a zero-delegation inline path for tiny or tightly coupled tasks and an orchestrated path for substantive, independently checkable work.
- **R-011 — Root authority.** The root must own objective interpretation, acceptance criteria, assumptions, plan revisions, risk decisions, result adoption, finding disposition, integration, and completion.
- **R-012 — Plan graph.** Before dispatch, every delegated task must have an ID/revision, bounded objective, falsifiable completion condition, dependencies, effect/scope, inputs, return contract, risk, verification method, and routing request.
- **R-013 — Immutable history.** A dispatched task, plan revision, result, finding, or decision must not be rewritten in place. Corrections and retries must append a new linked record.
- **R-014 — Delegation value.** Delegation must be used only when the unit is safe and likely to buy parallelism, context protection, independent evidence, or cohesive ownership. Work that is not delegated must remain represented and completed.
- **R-015 — Shared writes.** At most one actor, including the root, may write a shared workspace at once. A reviewer must not repair the candidate it reviews.
- **R-016 — Dependency waves.** A task must be admitted only after its dependencies pass. Parallelism is permitted only among independent read-only tasks or truly isolated writes.
- **R-017 — Proportional review.** Substantive or risky work must receive independent review and targeted fix verification; tiny low-risk work must not be forced through a ritual team.
- **R-018 — Artifact evidence.** Creative, game, UI, or other perceptual/interactive work must be assessed through actual scoped interaction and relevant visual, usability, and performance evidence. Build success alone is insufficient.

## Model routing and live tools

- **R-020 — Routing priors.** Luna-high for bulk reads/search, Sol-high/xhigh for guided building, Sol-xhigh for review, and Astra-high for ambiguity/adversarial work must be labeled uncalibrated starting priors rather than measured prices or guaranteed rankings.
- **R-021 — Capability first.** Sage must choose a model expected to satisfy the task before comparing cost, and cost reasoning must include root context, briefing, review, retries, and integration.
- **R-022 — User override.** An explicit user model or effort choice must be preserved unless unavailable, in which case the run must report the conflict instead of silently substituting.
- **R-023 — Requested versus effective.** Every assignment must record requested and effective model/effort separately. Missing effective observations must be `unknown`.
- **R-024 — Fork semantics.** The runtime instructions must reflect that full-history forks cannot override model/effort while fresh or bounded forks can, subject to the live schema.
- **R-025 — Lifecycle semantics.** Instructions must distinguish active steering (`send_message`) from waking an idle worker (`followup_task`), use `list_agents` for reconciliation, and never treat idle, interrupt acknowledgement, or a missing handle as task completion. A directly evidenced pre-creation rejection may close only that assignment as failed/no-effect; it cannot stand in for a real handle or unknown creation.
- **R-026 — Live authority.** The callable tool schema and returned observations must override cached docs. The official subagent document may inform design but cannot prove live behavior.
- **R-027 — Usage uncertainty.** Sage must not rely on a hard token meter or fabricate normalized spend. Unavailable cost/usage must remain `unknown`.

## Evidence, logging, reporting, and recovery

- **R-030 — Source of truth.** Every work invocation, including inline work and promotion coordination, must open a discoverable run with an append-only, versioned event log and validated boundary snapshots. A user instruction forbidding persistence is honored with explicit disclosure of the absent history. Markdown reports must be derived and must not be resume authority.
- **R-031 — Minimum state.** Persisted state must cover objective/constraints, plan/task revisions, assignments and handles, claims/evidence, checks, findings/dispositions, assumptions/decisions, baselines, user items, next action, and terminal status.
- **R-032 — Evidence labels.** Reports must distinguish observation, inference, unknown, and untested behavior. An empty typed section must describe the absence of recorded entries rather than assert no unknown exists, and directly stored unknown native identity/effect fields must render. Load-bearing real-world claims must carry current primary evidence where available and surface material counterevidence.
- **R-033 — Privacy.** Logs must be compact and classified. Large/raw/confidential content must use a protected locator plus integrity hash when retained; credentials and privileged capabilities must never enter state or fixtures.
- **R-034 — Completion.** Completion requires evidence for every acceptance criterion, passing required checks, disposition of every material finding, no accepted blocker/major issue, scope reconciliation, and explicit remaining human items.
- **R-035 — Checkpoints.** The root must checkpoint at observable workflow boundaries and host warnings, not an assumed context-window percentage.
- **R-036 — Recovery.** Resume must validate the authoritative log and its snapshot binding, rebuild a missing/stale snapshot only from a valid log, pause on an invalid log, re-check baselines, reconcile native handles, preserve unknown side effects and the writer barrier, and revise stale next actions before admission.
- **R-037 — Cause-responsive retry.** Each runtime plan must commit finite task-attempt and plan-revision allowances and a no-progress condition. Before retry, Sage must record the unmet criterion, evidence, and a causal hypothesis distinguishing missing input/authority, brief, decomposition, capability, environment/tool, and candidate failures; the next attempt must materially address that cause. An unchanged dispatch after repeated indistinguishable failure is invalid.
- **R-038 — Persistence.** When a runtime allowance or no-progress bound fires, Sage must diagnose and materially replan before more work. A persistence request continues through new finite in-scope plans while a distinct safe strategy remains, without overriding an explicit model choice; Sage asks the user only for missing authority/essential user-only input and reports an evidenced impasse when no safe distinct approach remains.

## Knowledge selection and promotion

- **R-040 — Selective retrieval.** Main Sage must select knowledge from an active index using observable task/domain/artifact/environment/risk/failure cues and load only a bounded, justified set. It must persist the generation and record revisions, refresh before a retry/material decision when the active generation or cues change, deduplicate loaded revisions, and re-check prior qualifiers/status. No match and an unchanged-generation/cue no-op must be valid.
- **R-041 — Evidence status.** Knowledge must record stable ID, revision, status, evidence class and gate rationale, rule, recognizer, qualifier, falsifier, evidence summary, provenance, alternative explanations, counterevidence, and review. Supported, provisional, contested, refuted, and retired states must remain distinct.
- **R-042 — Applicability.** Current user instruction and current task evidence must outrank promoted knowledge. A rule must be applied only inside its qualifier.
- **R-043 — Retrieval feedback.** A run must record whether loaded knowledge was useful, neutral, misleading, or not exercised, and may record missed recognizers, without promoting those observations.
- **R-044 — Closed inputs.** `sage-promote` may use successful, failed, or stopped terminal runs only when their integrity is valid and effects are reconciled. It must reject active/unknown-effect runs and quarantine malformed or integrity-invalid inputs without modifying them.
- **R-045 — Counterevidence.** Promotion must actively collect contradictions and counterexamples and preserve them in the candidate or record.
- **R-046 — Independent refutation.** Every create, correction, supported-status change, or retirement proposal must receive an independent refutation pass whose findings are explicitly dispositioned before landing.
- **R-047 — Correction.** Correcting knowledge must retain the stable ID, prior revision, refuting evidence, and reason. Strongly falsified knowledge must be excluded from normal retrieval without deleting its history.
- **R-048 — Reversible landing.** Installed-knowledge promotion must stage and validate a complete generation before changing one active pointer, retain the prior generation, and support verified rollback. Knowledge retirement must be a status change, not deletion. Source changes use the separate R-075 boundary.
- **R-049 — Qualitative support gate.** A scoped fact becomes supported only through a direct repeatable check within its declared environment. A transferable heuristic additionally needs a controlled comparison or independent corroboration across materially different qualifying contexts with confounders/counterexamples resolved or bounded. Causal guidance needs controlled/counterfactual or direct-mechanism evidence that isolates the proposed cause. Independent review is necessary but insufficient; confounded transfer remains provisional and unresolved material contradiction remains contested. Fixed universal run-count thresholds must not be invented before calibration.

## Rebuild process and empirical evaluation

- **R-050 — Dependency order.** Work must proceed architecture, verification, Sage, promotion, integration, then final assessment. A downstream module cannot pass before its dependencies pass.
- **R-051 — Builder/critic separation.** Each module round must have one builder followed by a separate Astra critic reviewing a frozen candidate. The final assessment must review the assembled installed skill.
- **R-052 — Quality gate.** Every applicable predeclared dimension must score at least 8.5/10 and the review must have zero open errors. No mean or aggregate may compensate for a lower dimension.
- **R-053 — Round history.** `docs/STATUS.json` must preserve every real score, failure, open issue, disposition, evidence pointer, approach ID, and round. Unknown/unrun scores must remain null.
- **R-054 — Replan bound.** One approach may receive at most four builder/critic rounds. Further work requires a documented, materially changed approach based on the failure cause; the new approach receives its own four-round bound.
- **R-055 — Verification first.** Functional and integration tests, negative cases, rubric, held-out boundary, and baseline comparison procedure must be built before rewriting the active skill/runtime.
- **R-056 — Deterministic tests.** Tests must cover valid behavior and meaningful failures for state, recovery, lifecycle interpretation, retrieval, promotion, refutation, rollback, installer cutover, and legacy exclusion.
- **R-057 — Sandboxed integration.** CLI/install/update/uninstall and state tests must run in temporary roots under `sage/evaluation/sandboxes` during the rebuild and must not write test artifacts elsewhere in the repository.
- **R-058 — Held-out forward tests.** Independent live evaluation must use realistic requests without disclosing expected answers, suspected defects, fixes, or treatment results to the evaluator.
- **R-059 — Calibrated scoring.** The evaluation must predeclare 0–10 anchors for task correctness, completeness/spec fit, evidence, orchestration, routing efficiency, safety/reversibility, recovery, report quality, knowledge behavior, and artifact-specific experience where applicable. Every score needs evidence. A native result protocol must bind completion to native lifecycle evidence without inventing an OS exit; actual subprocess exits remain distinct.
- **R-060 — Brute-force comparison.** A small reproducible case set must compare Sage routing to a predeclared high-capability brute-force baseline under the same inputs, sandbox, and checks. Missing token/money data stays unknown; conclusions are limited to the cases run.
- **R-061 — Gate distinction.** Status and reports must distinguish static/design review from deterministic test results and live empirical forward-test results.

## Migration

- **R-070 — Active allowlist.** Installer and generator behavior must install only the rebuilt entrypoints and their required references/helpers. It must not regenerate them from legacy manifests or policies.
- **R-071 — Legacy quarantine.** Useful legacy material may be retained or moved intact under `sage/archive/legacy`, but it must be clearly inert and must not be served as a fallback.
- **R-072 — Reversible migration.** Migration must preserve unrelated work and avoid destructive deletion. Installation must fail clearly if the rebuilt package is incomplete.
- **R-073 — Cutover proof.** Sandbox integration must prove that install/update selects the rebuilt package, reports/resumes run through the new contract, promotion uses the new store, and uninstall removes only owned installed artifacts.
- **R-074 — Shared history.** Both helpers must resolve one cwd-independent runtime root, expose its exact paths, and support normal runs and every knowledge operation through it. New work must allocate canonical runs by ID. Bounded discovery must distinguish eligible, active, absent and quarantined history. Explicit legacy registration must preserve source bytes and locators, bind log hashes, and reject ID collisions. Tests must exercise two task directories and installed discovery through staging, retrieval, recovery and uninstall; missing discovery must not be reported as reviewed evidence yielding no change.
- **R-075 — Source promotion.** Explicit promotion must assess both installed knowledge and the Sage source checkout unless the user narrows destinations. It may add, correct, or remove source guidance and implementation with independent refutation/review, evidence for the declared scope, and relevant verification. It must preserve user changes and the Git index, leave source edits uncommitted/uninstalled, and report per-destination outcomes. Checkout discovery must distinguish source, package, and runtime paths, including missing or read-only checkouts. Source changes must distribute through manual install/update, including removal of obsolete owned files, without modifying runtime stores. A source improvement needs neither an existing runtime record nor a fabricated knowledge action.

## Review score anchors

These anchors apply to the rebuild gate; the verification module may sharpen them before any candidate is scored.

| Score | Meaning |
| --- | --- |
| 10 | Complete, directly evidenced, no material weakness found under adversarial review |
| 9 | Strong and evidenced; only immaterial polish remains |
| 8.5 | Acceptance boundary: complete and credible with no open error; bounded residual risk is explicit |
| 7 | Material weakness or insufficient evidence, but the approach remains viable |
| 5 | Partially works or is only plausibly specified; major requirements are unproved |
| 0 | Missing, contradicted, unsafe, or not assessable from supplied evidence |

An unrun dimension is `null`, not zero and not a pass. An **open error** is a critic finding that identifies a violated requirement, incorrect fact, unsafe behavior, broken test, ambiguous active contract, or unsupported completion claim and has not been rejected with evidence or verified fixed. Suggestions and optional polish are recorded separately and do not become errors by wording alone.
