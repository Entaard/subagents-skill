# Promotion workflow

Read for every `$sage-promote` run. The root is the promotion coordinator: it selects scope, checks evidence, dispositions risk, and alone decides whether to land. Assess installed knowledge and Sage source improvements by default; the user may narrow the destinations. Follow [source promotion](source.md) for checkout discovery, patch review, and uncommitted delivery. The source tasks remain closed.

## Own coordination and recovery

Every invocation owns a separate coordinator run. Before planning, read the sibling [runtime paths](../../sage/references/runtime.md), [run procedure](../../sage/references/run.md) and [state contract](../../sage/references/state.md). Initialize the coordinator by unique ID in the pinned shared root, distinct from every selected source. Its own `events.jsonl` is append-only authority for promotion work. Source runs remain closed and read-only; validate them without appending, resuming, or repairing them. Knowledge generations are store artifacts, not the coordinator's task state.

Commit a bounded task graph that records source-run selection and candidate/attempt limits, requested destinations, user authority, proposal and expected-pointer/generation baselines, source checkout/diff baselines, actual role handles, and dependencies through each landing. Before dispatch or material rerouting, read [delegation](../../sage/references/delegation.md). Record each assignment's requested and effective model/effort separately, its context fork, scope/effect, evidence handling, and actual result. Judge placement using total delegation overhead: briefing, root context, review, integration, verification, and retry cost. A bounded `no_change` may instead use one root-owned inspection task and no candidate team; it requires no eligible change in either requested destination.

Checkpoint after plan commitment, before and after each delegation wave, after proposal/refutation/review, and before and after source integration, staging, or activation. Each checkpoint records the next action, unresolved authority, source-log/terminal hashes, proposal/patch hashes, source file preimages/postimages and application status, expected and actual pointer, generation/manifest hash when present, and landing authority. These are the coordinator's baselines; they never turn source logs or generations into its state. A source patch and runtime activation are separate effects; recovery must reconcile both.

Request `snapshot --write --summary` for checkpoint receipts; use the shared paginated context views for recovery.

Before context loss, resume, or any unknown actor/effect, read [recovery](../../sage/references/recovery.md). Validate the coordinator's own log and snapshot binding; rebuild only a stale projection from valid authority, while preserving a corrupt log and pausing admission. Reconcile every actual handle and unknown effect, retain the one-writer barrier, then recheck the actual source, proposal, current pointer, generation, and authority baselines. Before retrying an uncertain mutation, inspect the store and proposal bytes and establish the prior effect, absence, or safe idempotence. Append accepted observations, revise a stale next action or plan, confirm existing authority still covers it, and obtain new authority only when the action or scope requires it. Never use this procedure to resume or edit a source run.

Close the coordinator `completed` only after every criterion has observation evidence, required checks pass, every finding is dispositioned, admitted effects are reconciled, and both requested destinations have a delivered result or evidenced no-change reason. A verified uncommitted source patch is delivered; committing and real installation belong to the user. A missing checkout or unapplied patch is unfinished source work. Otherwise keep a truthful checkpointed open run or close `failed`/`stopped` with unfinished scope and human items explicit.

## Resolve and qualify

Use `list-runs --state-root ROOT --limit N --offset OFFSET` from the shared runtime procedure. It discovers canonical and explicitly registered legacy history and returns exact source paths. Bound pages and candidates before reading evidence; exclude the active coordinator. Pass eligible `run_dir` values unchanged as proposal `source_runs` and copy each selected `run_id` and `events_sha256` into its required `source_hashes` map. Source paths can be outside `ROOT/runs` for registered legacy history. Use the same `ROOT` for every knowledge command. Root-mode staging verifies these selected hashes and central ID/path bindings before mutation and again before publication; a valid-but-changed log or quarantined registration cannot bypass discovery by supplying its raw path.

Report a missing/empty root, active-only history, and quarantined sources distinctly. If the user expected old runs, recover supplied paths through registration or request their location; do not equate undiscovered history with evidence that yielded no reusable rule. A bounded empty-source inspection can close the coordinator with outcome `no_sources`, naming the root, pages and exclusions, without creating a generation. `no_change` means eligible evidence was actually reviewed and yielded no reusable candidate.

Run the state helper’s terminal validation for each selected source, then let `stage` revalidate it. Eligible status is `completed`, `failed`, or `stopped`; every admitted effect must be reconciled. Active, malformed, non-UTF-8, integrity-invalid, or unknown-effect runs are quarantined and reported without repair. Failed and safely stopped work can contain valuable negative evidence.

Before reading widely, cap the run set, candidate count, attempts, and stop condition. A heterogeneous batch that cannot receive one coherent review is split or stopped. If the bounded evidence yields no reusable, falsifiable rule, status change, or source improvement after comparison with both requested destinations, return `no_change` with the source IDs and per-destination reasons. This path needs no candidate team and writes no generation or source patch. Existing source defects or obsolete guidance remain candidates even with no retained knowledge records.

## Extract and reconcile

Treat run facts as observations. Extract candidate rule text, observable recognizer cues, exact applicability qualifier, a falsifier that can fire, direct evidence, counterevidence, alternative explanations, and exact provenance. Include `knowledge.feedback` and missed recognizers when deciding whether a cue, qualifier, index entry, or rule needs refinement. Frequency can prioritize examination; it cannot establish truth. Disuse is not falsehood.

For a substantive source set, freeze one bounded evidence catalog after source validation: selected IDs/log hashes, relevant observation and application/feedback IDs, unresolved contradictions, and exact evidence locators. Reuse its role-relevant portions in actor packets. Source hashes still require revalidation before staging; the catalog is a navigation artifact, not a new authority. Pre-screen exact unchanged candidates against retained records and explain exclusions without suppressing contrary evidence. A useful forward test exercises a new qualifying task and the rule's predicted decision consequence; correlated repetitions and confounded comparisons remain limited evidence.

Compare the candidate with active and retained records by stable ID and meaning:

- `create`: a new stable ID at revision 1;
- `correct`: preserve the ID, link the greatest retained revision, and record refuting/corrective evidence;
- `contest`: preserve the ID and history while excluding it from normal retrieval unless explicitly requested;
- `refute`: preserve the fired falsifier and history, and exclude the record from retrieval;
- `retire`: preserve history and give an intentional `explicit_decision`, `superseded`, or `scope_obsolete` basis. Recent disuse is not a basis.

Retained generations define the revision chain even after rollback. If revision 2 was rolled back, a repair is revision 3 with `prior_revision: 2`, staged from the safe active generation; revision 2 is not reactivated and cannot be reused for different bytes.

## Independent challenge

For any candidate that might land, record three distinct native actor IDs from live tool results:

- Candidate author: a guided Sol-high/xhigh worker that writes the proposal from bounded evidence.
- Refuter: an Astra-high worker for adversarial boundary, contradiction, confounding, and causality analysis.
- Reviewer: a separate Sol-xhigh worker that checks the frozen proposal and refutation, dispositions every finding, and applies the evidence-class gate.

An optional Luna-high scout may enumerate a large, bounded corpus first. Skip it when direct inspection is cheaper. Do not reuse the coordinator as proposer, refuter, or reviewer; do not invent handles. Give each actor only its role inputs and check its actual output. Pairwise-distinct strings satisfy the helper’s structural gate only; record the live context and behavior that establish genuine independence.

The refuter gets no desired verdict. Its `passed` outcome means the proposed action survived challenge. A failed or unsupported refutation blocks the action. The reviewer records one disposition for each finding, with evidence, and may recommend narrowing or downgrading. A material proposal change returns to the candidate author and receives renewed independent refutation and review; the reviewer does not silently author a changed candidate. Unresolved material counterevidence yields `contested` or no change.

## Evidence-class gate

- `scoped_fact` / `supported`: direct repeatable check plus the declared environment. The fact does not transfer beyond that scope.
- `transferable_heuristic` / `supported`: controlled comparison or independent corroboration across materially different qualifying contexts, with confounders and counterexamples resolved or bounded.
- `causal_guidance` / `supported`: controlled/counterfactual evidence or direct mechanism evidence, with material alternative causes dispositioned.

Independent refutation and review are necessary for all classes and sufficient for none. Approval counts and repeated correlated outcomes do not satisfy a predicate. A run where model and prompt both changed is confounded and remains `provisional` unless separate evidence isolates the claimed factor.

## Stage, land, and report

For each installed-knowledge action, read [knowledge CLI and schema](knowledge.md), prepare the complete proposal, and record the observed active generation (`none` for an empty store). Source patches follow the separate [source landing procedure](source.md#apply-recover-and-hand-off); they do not pass through the knowledge CLI. For runtime knowledge:

```text
python3 SAGE_KNOWLEDGE stage --state-root ROOT --proposal proposal.json --generation-id NEW --expected-current EXPECTED
python3 SAGE_KNOWLEDGE validate --state-root ROOT
python3 SAGE_KNOWLEDGE activate --state-root ROOT --generation-id NEW --expected-current EXPECTED
```

`stage` validates every source/reference, copies the active snapshot, checks retained lineage, writes and fsyncs a complete candidate beneath `.staging`, rechecks the pointer, and renames it into `generations` without activating it. Both parent directories are fsynced. `activate` validates all retained history, requires the target’s staged parent to equal the live expected pointer, and atomically changes only `current.json`. These are cooperative checks; maintain one live promotion writer.

After an abrupt staging exit, validate the store and inspect the intended generation before retrying. If publication did not happen, recognized partial `.staging` residue is safely isolated: preserve it as evidence and retry from the reviewed proposal with a fresh scratch directory after reconciling the prior writer. No automatic orphan adoption or deletion is provided. If the intended generation exists, validate its manifest, parent, exact record/proposal bytes and source bindings against the checkpoint, and recheck the current pointer before activation. Do not restage an already published revision or activate scratch. Unknown or symlinked scratch paths fail closed. Legacy abandoned dot directories under `generations` also remain rejected; preserve them for explicit evidence-preserving recovery rather than silently treating arbitrary committed-namespace paths as scratch.

Rollback is explicit and does not delete either generation:

```text
python3 SAGE_KNOWLEDGE rollback --state-root ROOT --generation-id PRIOR --expected-current CURRENT
```

This rollback handles an integrity-valid bad landing. Because every normal mutation validates all retained history, corrupt generation bytes or a malformed pointer block rollback unchanged. Preserve that evidence and stop for a separately designed recovery; do not delete history or weaken validation inside promotion.

Return each destination's no-change reason or actions, source-run IDs, quarantines, actor IDs and behavioral-independence evidence, findings/dispositions, evidence class and semantic gate decision, generation IDs/hashes, current pointer, source checkout and diff/review-note paths, exact changed paths, separate recovery targets, executed validation, failures, and unobserved claims. Source changes remain unstaged and uncommitted; real installed package bytes stay unchanged until the user runs `install.sh`.
