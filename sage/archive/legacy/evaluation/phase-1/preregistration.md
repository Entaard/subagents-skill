# Phase 1 paired pilot preregistration

Status: Phase 0 evaluation design; hash-frozen before any Phase 1 outcome is observed.

## Question and arms

The pilot asks whether the extracted Sage policy improves read-only research and review in Codex, and whether residual failures justify a managed runtime.

- Control: ordinary Codex with no Sage policy loaded. Native subagents remain available if the root chooses them.
- Treatment: the Phase 1 explicit Light-mode Sage skill, using the same native surfaces and no external Sage scheduler.

Both arms receive the exact prompt and frozen corpus in [`tasks.json`](tasks.json). Use a fresh root thread per arm and no cross-arm transcript. Pair order is deterministic from the low bit of `SHA256(study_id + ":" + task_id)`: zero runs control first; one runs treatment first.

## Environment comparability

Before the first task, create a pre-execution manifest that hashes the completed treatment skill and policy bundle, control and treatment prompt templates, runner and scoring code, root-loss driver, harness binary/build, configuration, environment offer, model catalog, tool set, sandbox and network policy, context window, and normalized-token accounting method. This is a Phase 1 execution gate because the treatment does not exist in Phase 0. No outcome may be generated until the manifest is complete. Any later drift invalidates the affected pair; a deliberate protocol change requires a new study ID, never an in-place manifest edit.

Freeze one concrete root model and reasoning effort and one hard normalized-token cap for the entire pilot. Use the same root model/effort and capability set in both arms of every pair. A treatment child placement may differ only as Sage policy directs; the control retains access to the same catalog.

The per-arm hard cap is 250,000 normalized input-plus-output tokens. If the runtime cannot measure or enforce the same unit in both arms, do not start the pilot. Record requested and effective model, effort, permissions, isolation, and tool availability. Environment drift invalidates both arms of the affected pair before scoring; rerun that same pair once after restoring the frozen environment. Never replace a task after seeing its outcome.

Network is disabled for all twenty tasks. Read tracked corpus files at commit `6b657a99b799a93dab1897b349bd32c53b223190`.

## Measurements

Capture per arm:

- blinded deliverable and complete structured run artifact where the treatment emits one;
- normalized input, output, and total tokens with provider/runtime provenance;
- wall time from first model turn start to final deliverable;
- root-context occupancy at final synthesis and its maximum, from the same sensor in both arms;
- number of user/operator orchestration interventions after start;
- protocol failures, retries, plan revisions, and incomplete artifact duties;
- exact requested/effective model and capability snapshots.

An unavailable sensor is `unknown`, never zero. A metric with either arm unknown is excluded only from that metric; the pair remains in quality and safety analysis. Context occupancy is not reconstructed from text length. Normalized-token measurement is a start gate, so spend cannot be unknown for a run that enters the pilot.

## Blind scoring

Strip arm, orchestration, model, timing, and token identifiers from deliverables. Two independent judges score [`rubric.json`](rubric.json) against the frozen task and corpus. They do not see run artifacts unless evidence pointers in the deliverable require adjudication; then a neutral broker returns only the requested evidence.

A third judge adjudicates any mandatory-failure disagreement or total-score difference above 10 points. Otherwise use the mean of the two totals. Record dimension scores and rationales before unblinding. A task-level semantic regression is a mandatory failure unique to treatment, or treatment at least 5 points below control.

## Margins and policy-value gate

Safety is first: any treatment-only unsafe action, approval regression, corruption, fabricated evidence, or mandatory completion violation stops the program until independently explained and corrected. The original result remains in the dataset.

Quality and safety require all 20 frozen task pairs. An environment-invalid pair may be rerun once after restoring the frozen environment and before unblinding that pair; if it remains invalid, the pilot is inconclusive and no policy-value or managed-need gate passes. A missing or unusable deliverable caused by the arm is scored under the rubric rather than excluded. No task or pair may be replaced after any outcome is observed.

Quality is non-inferior only when treatment has no unexplained semantic regression and the arithmetic mean across all 20 paired score differences, treatment minus control, is at least -5 points.

For any pair or subset used to claim a benefit, spend is comparable only when every included pair has treatment normalized tokens at most 1.25 times control, the subset sum has the same 1.25 maximum ratio, and neither arm exceeds its cap. If control spend is zero, that pair is comparable only when treatment spend is also zero. The full pilot must independently satisfy the same aggregate 1.25 ratio. A task-level quality improvement counts only when its pair is spend-comparable. A speed, context, or intervention benefit is credited only at non-inferior quality and spend comparability for its exact contributing pairs; cheap tasks cannot cross-subsidize a claimed subset.

Policy value passes when safety and non-inferiority pass and at least one preregistered material signal occurs:

- treatment improves by at least 5 rubric points on at least 3 spend-comparable pairs;
- at least 25 percent fewer orchestration interventions across all pairs with known event logs and comparable spend, computed as `(sum(control) - sum(treatment)) / sum(control)`;
- at least 25 percent lower maximum root-context occupancy, computed over pairs with known comparable sensors and spend as treatment mean of per-arm `maximum_occupied_tokens / effective_context_window` at most `0.75` times the control mean; or
- at least 20 percent lower median paired wall time among frozen wall-time-eligible tasks, computed as median of `treatment_seconds / control_seconds` at most `0.80`.

An orchestration intervention is a post-start user/operator instruction or control action needed to correct or unblock decomposition, dispatch, supervision, integration, or recovery. Predeclared approvals and human-only scoring judgments are not interventions; environment repairs invalidate the pair rather than count as treatment behavior. Each event is logged before unblinding. If a control denominator above is zero, that benefit signal is unavailable, not infinite. Unknown metrics are excluded only under the measurement rule above.

Coverage is frozen before outcomes: the intervention signal requires complete comparable event logs for at least 16 of 20 pairs; the root-context signal requires the same comparable occupancy sensor in both arms for at least 16 of 20 pairs; and the wall-time signal requires valid timing for at least 16 of the 19 frozen eligible pairs. A signal below its minimum coverage is unavailable, even if the observed subset crosses its threshold. The contributing IDs and every exclusion are reported; no post-outcome substitution or favorable subset selection is allowed. Spend comparability still applies to every contributing pair and to its subset aggregate.

A unit is independent only when it is separately dispatchable from the same frozen inputs and has no data, control, or mutation dependency on another candidate unit before final synthesis. [`tasks.json`](tasks.json) records the justification and freezes the wall-time-eligible IDs. `P1-T20` is sequential and excluded; no eligibility label may change after timing is visible. Report every threshold, including near misses, rather than selecting the most favorable metric.

## Causal classification and managed-need gate

After blind quality scores are locked, two reviewers independently classify each treatment miss as exactly one primary cause: policy judgment, model capability, brief/specification, deterministic coordination/bookkeeping, environment, or unresolved. A third reviewer resolves disagreements from artifacts and event evidence, not arm preference.

Core-addressable failures are limited to admission, dependency state, plan/version bookkeeping, attempt/handle tracking, idempotency, boundedness, capability degradation, handover sensing, or deterministic restart reconciliation. Evidence selection, decomposition quality, model intelligence, and persuasive judgment are not relabeled core-addressable.

A semantic miss preclassified as core-addressable gets at most one controlled rerun that changes only the failed coordination mechanism. The original miss continues to count. The rerun may show policy value only if that isolated repair removes the regression.

Managed need passes only when policy value already passes and either at least 3 of 20 original treatment runs require correction for a core-addressable mechanism, or the separate executable [`root-loss-fixture.json`](root-loss-fixture.json) proves its required recovery outcome cannot be met safely in Light mode. `P1-T20` measures policy-quality reasoning only and cannot satisfy the shortcut. The root-loss run must use the pinned Phase 1 driver, actual permitted native capabilities, frozen durable initial state, declared kill point, and observed no-blind-retry outcome. A prose simulation is not a pass or failure. Estimate the intervention and root-context cost of each qualifying failure before a managed implementation begins.

If policy value fails, stop. If policy value passes and managed need fails, ship Light mode and stop the runtime program. No threshold may be tuned after any outcome is visible.

## Reporting

Publish all pair scores, exclusions, unknown sensors, causal labels, controlled reruns, cap events, pair/subset comparability rows, denominator handling, and raw calculations. Separate artifact completeness from semantic quality. Keep blinded judge records, Phase 0 design hashes, and the Phase 1 pre-execution manifest as evidence.
