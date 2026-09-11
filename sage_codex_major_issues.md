# Sage for Codex: current major issues

**Repository:** `Entaard/subagents-skill`  
**Reviewed revision:** `b10bab2921e15463dff87649a35213716fa4598a`  
**Audit date:** 11 September 2026  
**Product:** `sage/skills/sage` and `sage/skills/sage-promote`, together with their runtime helpers  
**Companion:** [Top five quality and token-efficiency improvements](sage_codex_top5_quality_token_improvements.md)

## Executive assessment

The Codex rebuild has a sound core direction: a small instruction spine, explicit separation between execution and promotion, immutable recorded history, bounded delegation, evidence-led completion, and reversible knowledge generations. It also deliberately avoids claiming that a structural validator can establish semantic truth, actual model identity, genuine reviewer independence, or a physical writer lease. Those boundaries are strengths, not defects. [Requirements][requirements] [Architecture][architecture]

Four major issues remain in the inspected paths. They concern requirements changes, continuation after an exhausted plan allowance, revalidation of previously loaded knowledge, and recovery after an abruptly terminated staging operation. None is presented as a demonstrated production incident. The implementation behavior is established by source inspection; the failure sequences below are reasoned reproductions, not CLI executions performed in this audit.

| ID | Severity | Issue | Primary affected path |
| --- | --- | --- | --- |
| M1 | Major | An amended objective cannot revise the run's acceptance-criterion set. | Main Sage; promotion's own coordinator run |
| M2 | Major | Exhausting the committed plan-revision limit also blocks the next materially different finite plan. | Persistence and cause-responsive recovery |
| M3 | Major | The knowledge interface cannot perform the required revalidation of every previously loaded record. | Main Sage retrieval, resume, and promotion feedback |
| M4 | Major | An abruptly abandoned staging directory blocks retained-generation validation and subsequent knowledge mutations. | `sage-promote` staging and recovery |

Here, **major** means a concrete, materially impaired advertised workflow under a plausible, valid sequence of operations. It does not mean every run fails. No critical or blocker designation is justified by the evidence examined.

## Scope and verification limits

The review inspected the active Codex entrypoints, their operational references and UI metadata, the state and knowledge helpers, the installation wrappers and lifecycle implementation, the current requirements/architecture/contracts, both focused Codex regression-test files, and selected evaluation and handoff documentation. The Claude comparison used its main skill, decomposition, dispatch, verification and memory instructions, verifier agent, and the main promotion workflow. Historical usage material was used as context, not as a measurement of the rebuilt package.

**This is not an exhaustive line-by-line review of every repository file.** The repository also contains substantial archived implementations, retained evaluation sandboxes, long historical proposals, and ancillary Claude skills and scripts. These were not all read in full. Accordingly, this report does not satisfy an exhaustive whole-repository coverage claim and should not be read as one.

GitHub connector reads supplied the source. Attempts to obtain a runnable checkout in the execution environment failed. The repository test suite, installation tests, and native Codex workflows were **not executed** here. Existing reports of passing tests are historical repository evidence, not new results from this audit. Each proposed regression below must be executed against the pinned revision and the fix. The existing test entrypoint is documented in the [evaluation guide][evaluation].

### Comparison baseline: what should and should not transfer from Claude

Claude's version has particularly useful explicit practices: requirement and quality verdicts are distinct; a post-fix review asks whether a fix invalidated an earlier passing criterion; findings are deduplicated across rounds; and task briefs identify authoritative artifacts rather than forwarding transcripts. Its promotion process also checks the landed artifact rather than trusting a bookkeeping cell. [Claude verification][claude-verify] [Claude dispatch][claude-dispatch] [Claude promotion][claude-promote]

That does **not** make the Claude implementation a correctness oracle. Much of its enforcement remains instruction-driven. Its larger corpus, count-derived confidence bands, source-text promotion, and host-specific instrumentation should not be copied into Codex by default. Codex intentionally uses separate immutable knowledge generations and qualitative evidence-class gates. Missing Claude feature parity is not, by itself, a major issue. [Codex requirements][requirements] [Claude promotion][claude-promote]

---

## M1. Objective amendments cannot amend acceptance criteria

**Severity:** Major.  
**Confidence:** High in the representation limitation; its operational impact depends on whether the user changes an acceptance requirement rather than merely clarifying wording.  
**Location:** `sage_state.py`: `validate_payload`, `validate`, and `project`; the `run.amended` and completion contracts. [State helper][state] [Plan/criterion validation][state-plan] [Projection][state-project] [Contracts][contracts]

### What is wrong

The event contract supports `run.amended` with `kind: objective` or `kind: constraint`. It does not support adding, replacing, or retiring an acceptance criterion.

In validation, the allowed criterion IDs are initialized from `run.opened.criteria`. An amendment is recorded as an amendment trigger but does not update that set. In the projection, an objective amendment changes `state.objective`, while `state.criteria` remains the original opening payload. Evidence, failure diagnoses, checks, and completed closure continue to refer to the original criterion IDs. A second `run.opened` is rejected, so the opening criterion set cannot be legitimately replaced in the same log. [State helper][state] [Plan/criterion validation][state-plan] [Projection][state-project]

This creates two competing definitions of the task: the current objective and the old completion obligations. The problem is not that a helper cannot interpret natural language. The problem is that the root has no supported event with which to record its already-made, user-authorized criteria decision.

### Concrete failure sequence

1. A run opens with criterion `c-png`: deliver a PNG artifact.
2. Before completion, the user changes the requirement to SVG instead of PNG. Sage records the new objective and replans the work.
3. Correct execution now produces SVG, not PNG.
4. A new `c-svg` reference cannot be introduced through `run.amended`; recording evidence or checks against an undeclared criterion is rejected.
5. Closing against `c-png` either fails to describe the changed task or requires the root to mislabel the SVG evidence as satisfying the original PNG requirement.

The honest escape is to stop the original run and open a new one with the correct criteria, explicitly carrying forward the relevant state. That is a workaround, not an implemented in-run amendment path. The instructions do not provide a complete continuation procedure for this case.

**Boundary:** Many ordinary replans work correctly. An implementation strategy change that leaves the acceptance criteria intact does not encounter this issue. Adding tasks to satisfy existing criteria is also supported. The finding is specifically about a genuine change to the acceptance contract.

### Why this reaches major severity

The root is supposed to own objective interpretation and acceptance criteria, while completion must demonstrate the actual accepted scope. A legitimate user change can leave the durable state unable to express that scope without starting over or misrepresenting the old criterion. This matters especially after compaction, when the projected criteria are the obvious authority for a resumed coordinator. The same helper is used by promotion's own coordinator run. [R-011, R-030, R-031, R-034][requirements] [Promotion coordination][promotion]

Claude's editable ledger does not have this particular immutable-ID ceiling, although it relies more heavily on the coordinator to preserve an honest amendment history. The correct Codex fix is not to abandon immutable events; it is to make criterion revisions first-class.

### Suggested fix

Add an append-only acceptance-contract revision, for example `criteria.revised`. Give it a revision ID, a reference to the authorizing user decision or justified scope clarification, explicit added/replaced/retired criterion IDs, a rationale, and the effective current criterion set.

Keep the original text and evidence immutable. A changed criterion gets a new revision or a new stable ID with a `supersedes` relationship; it must not silently reuse an earlier criterion's meaning. Bind checks and evidence to the criterion version they evaluated. The projection should show current requirements separately from historical requirements, and completed closure should cover every current required criterion.

Handle obsolete work explicitly as part of this change. The current plan validator prohibits dropping tasks, and completed closure requires every current task to pass. Preserve task history, but distinguish a historical task from a current obligation. A cancelled or superseded task needs an authorized disposition; cancellation must never release an unknown writer or erase an admitted task's effects. Existing reconciliation rules must still run. [Plan validation][state-plan] [State contract][contracts]

For a smaller immediate repair, document and support a linked continuation-run procedure. Reconcile every admitted effect before closing the original; preserve its artifacts and evidence, initialize the revised acceptance contract, and link the successor to its predecessor. If an effect cannot yet be reconciled, keep the original open and preserve its barrier: starting a successor must not make the same workspace appear safe to mutate. Do not describe a successor as modifying the original run in place.

### Regression tests required

Test replacement, addition, and removal of requirements after a legitimate user decision. Show that the resumed snapshot exposes the new contract and that old evidence does not automatically satisfy a changed requirement. Deterministic tests should reject missing or dangling authorization references and preserve historical records and writer barriers. Separately test the coordinator's refusal to weaken criteria without actual user authority: the helper can check a recorded authorization link, not prove that the real user authorized its contents.

Also keep a compatibility test proving that a strategy-only replan needs no criterion revision and continues to work with existing v1 logs.

---

## M2. Exhausting a plan allowance blocks the required finite replan

**Severity:** Major.  
**Confidence:** High in the rejection behavior and the mismatch with the persistence requirement.  
**Location:** `sage_state.py::validate`, the `plan.revised` branch; R-037 and R-038. [Plan validation][state-plan] [Requirements][requirements] [Run procedure][run]

### What is wrong

The validator requires contiguous global plan revisions. Before considering the new plan's cause, operational changes, or new allowance, it checks whether the incoming revision exceeds the **previous** plan's `revision_limit`. If it does, the event is rejected with `limit_exceeded`.

Consequently, once the previous committed limit is reached, a new plan cannot renew the allowance in that same run. Increasing `revision_limit` inside the proposed next plan does not help: the old limit is checked first. There is no separate supported approach-renewal event or plan epoch. [Plan validation][state-plan]

This correctly prevents an unexamined retry from bypassing its bound, but it also prevents the behavior R-038 explicitly requires: when a bound fires, diagnose the cause and continue through a new finite, in-scope plan while a distinct safe strategy remains and persistence is authorized. [Requirements][requirements]

### Concrete failure sequence

Open a valid run with an initial plan at revision 1, a revision limit of 1, and a finite task-attempt allowance. Admit a task and obtain a reconciled failure with observation evidence.

The coordinator then diagnoses a genuine candidate defect and proposes revision 2 with a changed task input or implementation strategy, the required failure evidence and cause fields, and a fresh finite allowance. The proposal is not an identical redispatch. Nevertheless, the validator rejects revision 2 because `2 > 1`, before its substantive change can establish a renewed approach.

The same boundary appears at any larger exhausted limit. Raising a limit in advance can avoid reaching it; that is not a recovery procedure for an allowance that has already fired.

**Boundary:** Ordinary failure replans inside the remaining revision allowance work. The finding does not say that all retries fail or that the limit should be removed.

### Why this reaches major severity

Cause-responsive persistence is an explicit product requirement, not an optional optimization. A legitimate next approach becomes structurally unrepresentable at precisely the boundary where the workflow says the coordinator should diagnose and replan. The likely workarounds are premature limit inflation, an undocumented run restart, or stopping despite a remaining safe strategy. Each weakens the intended relationship between finite bounds, evidence, and useful persistence. [R-037 and R-038][requirements]

Claude's failure-loop instructions distinguish repeated patching from reopening the assumptions, reproduction, plan, or definition of done. Codex already adopts the right cause-responsive philosophy; its state transition needs to express that philosophy without becoming an unbounded retry loop. [Claude verification][claude-verify] [Codex run procedure][run]

### Suggested fix

Represent the distinction between **a retry within an approach** and **a newly justified approach**. One implementation is an append-only `approach.started` or `plan.renewed` event with a stable predecessor link, the exhausted bound, failure evidence, diagnosed cause, concrete strategy change, applicable persistence authority, and new finite limits.

Keep global event and plan history monotonic. Enforce attempt and revision bounds within the declared approach, or use explicit bounded revision windows. Renewal must not pass merely because a number or `no_progress` string changed. At minimum it needs a referenced failure or material new fact and an actual operational change; the root still judges whether that change is adequate.

Preserve all existing effect reconciliation, dependency, user-model-override, and scope rules across renewal. A new approach must not turn an unknown prior writer into a free slot, erase prior spend, or pretend the failed approach never happened.

A documented, explicitly linked successor run is another valid design, provided it preserves these same invariants. Pick one supported procedure; do not leave the coordinator to invent one after the validator rejects the next event.

### Regression tests required

Start with an exhausted one-revision approach. Confirm that an evidenced, materially different, authorized finite continuation can proceed and survive snapshot/resume. Structurally reject an identical strategy, a numbers-only limit increase, and missing or dangling required authority references; keep unresolved effects from authorizing conflicting writes. Evaluate the truth and adequacy of the authority and causal explanation in coordinator behavior tests, not by assuming that a well-shaped event proves them.

Verify that ordinary within-limit retries retain their existing behavior and that the final report includes the failed approach, not just the successful successor.

---

## M3. Required knowledge revalidation is not available through the retrieval interface

**Severity:** Major.  
**Confidence:** High in the interface gap; whether a run actually follows stale guidance is not established by this static review.  
**Location:** main Sage's knowledge reference; `sage_knowledge.py::command_retrieve` and its CLI parser; `sage_state.py::project`. [Retrieval instructions][knowledge-main] [Retrieval implementation][knowledge-retrieve] [Knowledge CLI][knowledge-mutations] [Projection][state-project]

### What is wrong

Main Sage is instructed to read active immutable knowledge **through the helper**, refresh on generation/cue changes, deduplicate loaded revisions, and re-check **all prior statuses and qualifiers**. That last requirement is stronger than simply obtaining a new top-three recommendation list. [Retrieval instructions][knowledge-main] [R-040][requirements]

The exposed retrieval operation returns only the current bounded matches. It excludes `refuted` and `retired` records unconditionally and excludes provisional/contested records unless explicitly requested. A still-supported record may also be absent because its qualifier no longer matches or other candidates rank ahead of it. The CLI provides no lookup-by-ID, revalidation, invalidation, or selection-diff operation. `validate` reports store status, not per-record applicability. [Retrieval implementation][knowledge-retrieve] [Knowledge CLI][knowledge-mutations]

The current state projection adds a secondary difficulty: each `knowledge.selected` event replaces `state.knowledge_selection`. Earlier selections remain in the authoritative event log, so **this is not loss of the historical data**. But the last-selection snapshot alone is not a cumulative inventory of all knowledge revisions previously loaded or applied. [Projection][state-project]

### Concrete failure sequence

A run loads `k-1` revision 1 from generation `g-1` and uses it to choose an implementation strategy. An explicit promotion of other closed evidence activates `g-2`, where `k-1` revision 2 is refuted or its applicability has changed.

At the next material decision, the run performs the required refresh. `retrieve` returns no `k-1`. That absence does not tell the coordinator whether the rule was refuted, retired, made out-of-scope, or merely displaced from the bounded match list. Even `include_non_supported: true` cannot reveal a refuted or retired record. The focused knowledge tests explicitly preserve that exclusion policy. [Knowledge regressions][knowledge-tests]

The coordinator can conservatively abandon all old guidance, inspect record files directly, or invent an undocumented Python integration with the helper's internal record-loading functions. The latter possibilities mean that the information is not fundamentally inaccessible. However, none is the prescribed, supported CLI operation for re-checking every prior record and identifying which already-made decisions need reconsideration. The finding is an installed workflow/interface gap, not a claim that no custom code could recover the information.

### Why this reaches major severity

Promotion's negative feedback must be able to affect ongoing decisions. Excluding a bad record from **new recommendations** is necessary but is not equivalent to invalidating knowledge already in a coordinator's context or already used in its plan. The missing interface prevents a mandatory safety/quality operation from being performed unambiguously through the supported path. [R-040, R-042, R-043, R-047][requirements]

The issue is not that automatic promotion is missing; automatic promotion is intentionally forbidden. It is the connection between an explicitly changed knowledge generation and an active run that is incomplete.

### Suggested fix

Extend retrieval with an explicit previous-selection input, or add a bounded `revalidate` command. It should accept previously loaded IDs/revisions, their observed generation, and current observed cues. Resolve those exact IDs independently of recommendation ranking.

Return diagnostic results such as `unchanged_applicable`, `revised`, `out_of_scope`, `refuted`, `retired`, `not_present_in_active_generation`, and `unknown`, together with the current record revision, relevant qualifier, and a reason. Refuted/retired records belong in this diagnostic channel, **not** in normal usable matches. A rollback can legitimately make an older retained revision active, so do not equate every lower active revision with corruption.

Derive a cumulative knowledge-use inventory from the run log: exact loaded revisions, whether they were merely considered or actually applied, and the decisions/tasks they influenced. Keep the detailed history on disk; return only actionable changes. A newly refuted or out-of-scope rule should trigger review of the affected decisions, not an automatic destructive reversal of previously completed work.

Add a compact unchanged fast path, but bind its comparison token to the validated active manifest, normalized cues, retrieval policy and the prior-record inventory being revalidated. A changed policy or inventory requires a fresh check even if the generation ID and cues are unchanged. Preserve feedback for every loaded revision, including those later invalidated.

### Regression tests required

Exercise a supported-to-refuted change, supported-to-contested change, narrower qualifier, ranking displacement without a status change, and rollback to an older active generation. In each case, the result must distinguish the actual reason from an ordinary no-match.

Resume after two different selections and verify that the cumulative loaded/applied inventory is recoverable. Ensure that normal retrieval still excludes refuted/retired guidance, and that invalidation diagnostics cannot be mistaken for permission to apply it.

---

## M4. Abrupt staging termination can poison the retained-generation namespace

**Severity:** Major.  
**Confidence:** High in the deterministic failure path. No process-kill experiment was executed here.  
**Location:** `sage_knowledge.py::command_stage`, `validated_generations`, `command_validate`, `retained_lineage_prior`, and `replace_pointer`. [Generation validation][knowledge-generations] [Staging and pointer operations][knowledge-mutations] [Promotion recovery instructions][promotion]

### What is wrong

`command_stage` creates its temporary directory directly under `STORE/generations`, using a name such as `.g-2.<random>`. It writes and validates the candidate there, renames it to the committed generation name, and cleans the temporary directory in a `finally` block.

That cleanup works for ordinary exceptions that unwind through `finally`. It does not run after abrupt process termination such as `SIGKILL`, `os._exit`, or a host failure. A temporary directory can therefore remain beside committed generations. [Staging implementation][knowledge-mutations]

`validated_generations` enumerates **every** child in that directory and immediately passes each child name to `generation_id`. A leading-dot temporary name is not a valid generation ID. The leftover is consequently treated as invalid retained history even though it was never published as a generation. [Generation validation][knowledge-generations]

### Concrete failure sequence

Start with an intact active generation `g-1`. Begin staging `g-2` and terminate the helper after temporary-directory creation but before its rename/cleanup.

After restart:

- `validate` encounters the abandoned temporary name and rejects the store.
- A subsequent `stage` reaches `retained_lineage_prior`, which validates all retained generations and rejects the same name.
- `activate` and `rollback` call `replace_pointer`, which also validates all retained generations before changing the pointer.

The normal mutation and rollback paths are therefore blocked by an unpublished temporary artifact. The published `g-1` bytes and pointer need not have changed at all.

**Important limitation:** Ordinary `retrieve` validates the active generation through `current_pointer`; it does not enumerate all retained siblings. Retrieval of intact `g-1` can still work. This finding is not a claim that all reads fail, that current knowledge is corrupted, or that a normal caught exception leaks the directory. [Retrieval implementation][knowledge-retrieve] [Pointer implementation][knowledge-generations]

### Why this reaches major severity

Recoverability and reversible promotion are primary capabilities. An interrupted attempt can leave the coordinator unable to use the advertised validation, staging, activation, or rollback operations without an extra, unspecified filesystem-repair procedure.

Failing closed on a **corrupted committed generation** is intentional and should remain. The defect is the failure to distinguish that retained history from the helper's own unpublished scratch space. Fixing this distinction does not require a distributed transaction manager or a physical multi-writer lease. [R-036, R-048][requirements] [Promotion recovery][promotion]

### Suggested fix

Separate committed generations from owned staging state. For example, keep only published generations under `generations/` and use a dedicated sibling namespace such as `STORE/.staging/` for in-progress work. Update the store allowlist accordingly; merely creating this directory without updating validation would introduce a different rejection.

Keep staging and committed destinations on the same filesystem for the intended rename operation. Give each staging operation a small intent record: operation ID, intended generation, expected active pointer identity/hash, proposal digest, and source/evidence bindings. Recovery can then identify an abandoned operation without treating arbitrary filesystem contents as trustworthy.

After interruption, inspect before acting. An incomplete owned staging operation can be quarantined or removed under explicit recovery authority. A complete one may be adopted only after validating it and rechecking the expected active pointer and proposal bindings. Never activate an orphan solely because a directory exists, and never delete an unrecognized directory while claiming it is scratch.

Preserve strict validation of every committed generation, the retained-lineage checks, immutable revisions, and the one-coordinator-writer requirement. Do not solve this by ignoring every malformed child under `generations/`.

### Regression tests required

Use a child process and inject abrupt exit at several cut points: after temporary-directory creation, during a record write, after candidate validation but before rename, and after rename but before acknowledgement. Ordinary exception tests do not cover this behavior.

For pre-rename interruption, verify that the old active generation remains usable and that recovery handles the owned staging residue without weakening committed-history validation. For post-rename interruption, recognize the already-staged generation rather than duplicating its effects. Retain negative cases for a corrupt committed generation, an unknown/symlinked staging path, and an expected-pointer mismatch.

Run these tests only in temporary evaluation roots, never against a user's real knowledge store.

---

## Issues deliberately not asserted

This report does not resurrect the historical missing-promotion-coordinator finding: the current promotion reference explicitly owns a coordinator run, plan, checkpoints, recovery and closure. It also does not claim that unknown effective model/effort is a bug, that distinct actor IDs prove independence, or that the expected-pointer check is a physical concurrency lock. The product explicitly bounds those claims. [Promotion reference][promotion] [Requirements][requirements]

An old passing check can remain in the log beside a later differently named failed check. The contract explicitly assigns semantic supersession to the root and surfaces negative facts in reporting. Strengthening artifact/check bindings is valuable and is included in the companion report, but it is **not** misrepresented here as an undisclosed violation of the existing structural contract. [Contracts][contracts] [State regressions][state-tests]

The helper's qualifier behavior is also documented: every nonempty `all` category must intersect the current cues; it does not mean every string in one category is independently mandatory. A richer Boolean qualifier is an optional schema evolution, not a claim that the current implementation disobeys its stated rule. [Knowledge contract][knowledge-contract]

Finally, neither the repository's historical passing scores nor this static audit proves future quality or token savings. The rebuilt package's own handoff distinguishes design, offline tests, and limited live evidence. Preserve that distinction when validating the fixes. [Recorded handoff][handoff]

## Recommended repair sequence

Repair M4 before relying on unattended promotion recovery. Repair M1 and M2 as a coherent evolution of the run contract, with migration tests and explicit continuation semantics. Repair M3 before relying on long-running sessions to react correctly to knowledge changes. Then apply the companion report's efficiency work against measured, quality-controlled baselines.

Do not rerun a large model review after every individual helper edit. First run focused regressions, then the complete offline gate, then a frozen cross-module review and the relevant native workflow cases. A structural pass must never be reported as a live-behavior pass.

## Review record

This report and its companion received two bounded review passes followed by one adversarial self-review. The checks focused on source accuracy, major-or-higher severity, current-versus-historical behavior, feasible fixes, and claims about testing. No separate reviewer agent or independent native Codex trial was used. This review record is not a claim of exhaustive correctness.

[requirements]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/docs/REQUIREMENTS.md
[architecture]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/ARCHITECTURE.md
[contracts]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/docs/CONTRACTS.md
[state]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/scripts/sage_state.py
[state-plan]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/scripts/sage_state.py#L278-L351
[state-project]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/scripts/sage_state.py#L500-L555
[state-tests]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/tests/test_state.py
[run]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage/references/run.md
[promotion]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage-promote/references/promotion.md
[knowledge-main]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage/references/knowledge.md
[knowledge-contract]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage-promote/references/knowledge.md
[knowledge-retrieve]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/scripts/sage_knowledge.py#L462-L520
[knowledge-generations]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/scripts/sage_knowledge.py#L385-L427
[knowledge-mutations]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/scripts/sage_knowledge.py#L550-L659
[knowledge-tests]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/tests/test_knowledge.py
[evaluation]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/evaluation/README.md
[handoff]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/docs/FINAL-REPORT.md
[claude-verify]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage-claude/references/verify.md
[claude-dispatch]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage-claude/references/dispatch.md
[claude-promote]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/claude-skills/sage-promote/SKILL.md
