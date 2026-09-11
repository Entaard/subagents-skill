# Promotion workflow

Read for every `$sage-promote` run. The root is the promotion coordinator: it selects scope, checks evidence, dispositions risk, and alone decides whether to land. The source tasks remain closed.

## Own coordination and recovery

Every invocation owns a separate coordinator run. Before planning, read the sibling [run procedure](../../sage/references/run.md) and [state contract](../../sage/references/state.md), resolve `SAGE_STATE` beside `SAGE_KNOWLEDGE`, and choose an explicit run directory distinct from every selected source. Its own `events.jsonl` is append-only authority for promotion work. Source runs remain closed and read-only; validate them without appending, resuming, or repairing them. Knowledge generations are store artifacts, not the coordinator's task state.

Commit a bounded task graph that records source selection and candidate/attempt limits, user authority, proposal and expected-pointer/generation baselines, actual role handles, and dependencies through landing. Before dispatch or material rerouting, read [delegation](../../sage/references/delegation.md). Record each assignment's requested and effective model/effort separately, its context fork, scope/effect, evidence handling, and actual result. Judge placement using total delegation overhead: briefing, root context, review, integration, verification, and retry cost. A bounded `no_change` may instead use one root-owned inspection task, no candidate team, and no generation write.

Checkpoint after plan commitment, before and after each delegation wave, after proposal/refutation/review, and before and after staging or activation. Each checkpoint records the next action, unresolved authority, and current source-log/terminal hashes, proposal hash, expected and actual pointer, generation/manifest hash when present, and landing authority. These are the coordinator's baselines; they never turn source logs or generations into its state.

Before context loss, resume, or any unknown actor/effect, read [recovery](../../sage/references/recovery.md). Validate the coordinator's own log and snapshot binding; rebuild only a stale projection from valid authority, while preserving a corrupt log and pausing admission. Reconcile every actual handle and unknown effect, retain the one-writer barrier, then recheck the actual source, proposal, current pointer, generation, and authority baselines. Before retrying an uncertain mutation, inspect the store and proposal bytes and establish the prior effect, absence, or safe idempotence. Append accepted observations, revise a stale next action or plan, and re-establish user authority before further mutation. Never use this procedure to resume or edit a source run.

## Resolve and qualify

Choose an explicit state root. Use the installation’s configured Codex state root; absent an override, resolve the standard `~/.codex/sage` path to an absolute path and state it before access. Set the knowledge store to `<state-root>/knowledge` and selected sources to explicit `<state-root>/runs/<run-id>` paths. Never infer either from the current repository. Resolve `SAGE_KNOWLEDGE` to the source helper in this checkout or its installed `sage/bin` sibling.

Run the state helper’s terminal validation for each selected source, then let `stage` revalidate it. Eligible status is `completed`, `failed`, or `stopped`; every admitted effect must be reconciled. Active, malformed, non-UTF-8, integrity-invalid, or unknown-effect runs are quarantined and reported without repair. Failed and safely stopped work can contain valuable negative evidence.

Before reading widely, cap the run set, candidate count, attempts, and stop condition. A heterogeneous batch that cannot receive one coherent review is split or stopped. If the bounded evidence yields no reusable, falsifiable rule or status change, return `no_change` with the source IDs and reason. This path needs no candidate team and writes no generation.

## Extract and reconcile

Treat run facts as observations. Extract candidate rule text, observable recognizer cues, exact applicability qualifier, a falsifier that can fire, direct evidence, counterevidence, alternative explanations, and exact provenance. Include `knowledge.feedback` and missed recognizers when deciding whether a cue, qualifier, index entry, or rule needs refinement. Frequency can prioritize examination; it cannot establish truth. Disuse is not falsehood.

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

Read [knowledge CLI and schema](knowledge.md), prepare the complete proposal, and record the observed active generation (`none` for an empty store). Then:

```text
python3 SAGE_KNOWLEDGE stage --store-dir STORE --proposal proposal.json --generation-id NEW --expected-current EXPECTED
python3 SAGE_KNOWLEDGE validate --store-dir STORE
python3 SAGE_KNOWLEDGE activate --store-dir STORE --generation-id NEW --expected-current EXPECTED
```

`stage` validates every source/reference, copies the active snapshot, checks retained lineage, writes and fsyncs a complete sibling generation, rechecks the pointer, and renames it without activating it. `activate` validates all retained history, requires the target’s staged parent to equal the live expected pointer, and atomically changes only `current.json`. These are cooperative checks; maintain one live promotion writer.

Rollback is explicit and does not delete either generation:

```text
python3 SAGE_KNOWLEDGE rollback --store-dir STORE --generation-id PRIOR --expected-current CURRENT
```

This rollback handles an integrity-valid bad landing. Because every normal mutation validates all retained history, corrupt generation bytes or a malformed pointer block rollback unchanged. Preserve that evidence and stop for a separately designed recovery; do not delete history or weaken validation inside promotion.

Return the no-change reason or all actions, source IDs, quarantines, actor IDs and behavioral-independence evidence, findings/dispositions, evidence class and semantic gate decision, generation IDs/hashes, current pointer, exact changed paths, rollback target, executed validation, failures, and unobserved claims.
