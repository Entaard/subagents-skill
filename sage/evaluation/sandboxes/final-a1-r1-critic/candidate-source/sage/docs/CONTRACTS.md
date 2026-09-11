# Sage verification contracts

Status: implemented source contract plus the live-repairs-a1 round-1 candidate described below. A test may depend on this file; prose outside this file cannot silently widen the interface. The original live paired-result v2 protocol remains frozen and unchanged; its successor is explicitly versioned.

## Common CLI rules

Both Python helpers are dependency-free and are invoked with the repository interpreter. They accept UTF-8 JSON, reject duplicate object keys and non-finite numbers, resolve all supplied paths, and never infer a state root from the current task repository.

Success exits `0` and prints one JSON object to stdout. Contract/data rejection exits `2` and prints one JSON error object to stderr with `ok: false`, `code`, and `message`. Unexpected I/O failure exits `3`. No command writes outside an explicitly supplied directory. Sage-owned run, event, task, criterion, evidence, check, finding, request, generation, and knowledge IDs match `^[a-z0-9][a-z0-9._-]{0,63}$`. Native agent handles are different: persist the nonempty, control-free string returned by the collaboration tool exactly, up to 512 characters, so canonical names such as `/root/scout` can reconcile with `list_agents` without invented aliases.

## Run state helper

Invocation:

```text
python3 sage/scripts/sage_state.py init --run-dir RUN_DIR --run-id ID --objective TEXT --criteria CRITERIA_JSON
python3 sage/scripts/sage_state.py append --run-dir RUN_DIR (--event EVENT_JSON | --events EVENTS_JSONL)
python3 sage/scripts/sage_state.py validate --run-dir RUN_DIR [--terminal]
python3 sage/scripts/sage_state.py snapshot --run-dir RUN_DIR --write
python3 sage/scripts/sage_state.py resume --run-dir RUN_DIR --agents AGENTS_JSON
python3 sage/scripts/sage_state.py report --run-dir RUN_DIR --write
```

`RUN_DIR/events.jsonl` is authoritative. Every nonblank line is one object with exactly these common fields: `v` (`1`), `event_id`, `run_id`, `seq` (positive integer), `at` (RFC 3339 UTC), `actor`, `type`, and `payload`. Event IDs are unique, sequence starts at 1 and is contiguous, and every line uses the same run ID. Append order is history order. `snapshot.json` and `report.md` are derived and cannot repair or override the log.

`init` creates a new directory and its first `run.opened` event, failing if the directory already contains state. `append` validates the existing log plus the complete proposed batch before atomically replacing `events.jsonl`; a rejected batch leaves its bytes unchanged. Single events and batches use the same validation path. This is the supported durable write workflow; direct JSONL authorship is only a fixture mechanism.

The compact event vocabulary is:

| Type | Required payload |
| --- | --- |
| `run.opened` | `objective`, `criteria` (`[{id,text}]`), `constraints`, `next_action` |
| `run.amended` | `kind` (`objective` or `constraint`), `value`, `reason`, `corrects_event_id` or null |
| `note.recorded` | `category` (`assumption` or `decision`), `text`, `evidence_ids`, `corrects_event_id` or null |
| `user.decision` | `request_id`, `question`, `decision`, `received_at` |
| `plan.revised` | `revision`, `reason` (`initial`, `failure`, `user_amendment`, `evidence_change`), positive `attempt_limit`, positive `revision_limit`, `no_progress`, `trigger_event_ids`, `tasks` |
| `task.admitted` | `task_id`, `task_revision`, `plan_revision` |
| `agent.requested` | `task_id`, `handle`, `requested_model`, `requested_effort`, `fork_turns` |
| `agent.not_created` | `task_id`, `task_revision`, `reason`, nonempty `evidence_ids` |
| `agent.observed` | `handle`, `lifecycle` (`active`, `idle`, `completed`, `failed`, `interrupted`, `missing`), `effect_status` (`none`, `reconciled`, `unknown`), `effective_model`, `effective_effort` |
| `task.result` | `task_id`, `task_revision`, `outcome` (`passed`, `failed`, `unknown`), `effect_status` (`none`, `reconciled`, `unknown`), `evidence_ids` |
| `evidence.recorded` | `evidence_id`, `criterion_ids`, `kind` (`observation`, `inference`, `unknown`, `untested`), `locator`, `sha256` or null |
| `check.recorded` | `check_id`, `criterion_ids`, `outcome` (`passed`, `failed`, `not_tested`), `evidence_ids` |
| `finding.opened` | `finding_id`, `severity` (`blocker`, `major`, `minor`), `summary`, `evidence_ids` |
| `finding.dispositioned` | `finding_id`, `disposition` (`fixed`, `accepted`, `rejected`), `evidence_ids`, `verification_check_id` or null |
| `knowledge.selected` | `generation_id`, `cue_fingerprint`, `cues`, `matches` (`[{id,revision,status,reason}]`), `retrieval_status` (`matched`, `no_match`, `unchanged`) |
| `knowledge.feedback` | `id`, `revision`, `outcome` (`useful`, `neutral`, `misleading`, `not_exercised`), `evidence_ids`, `missed_recognizers` |
| `checkpoint.written` | `next_action`, `baselines`, `unresolved_user_items` |
| `run.closed` | `status` (`completed`, `failed`, `stopped`), `criterion_evidence`, `scope_reconciled`, `remaining_human_items` |

Each task in `plan.revised.tasks` contains `id`, `revision`, `objective`, `completion`, `dependencies`, `owner`, `effect` (`read`, `write`, `external`, `unknown`), `scope`, `inputs`, `returns`, `risk`, `verification`, `requested_model`, `requested_effort`, and `fork_turns`. Dependencies refer to tasks in the same revision. A task is admitted only after every dependency has a passed result. At most one admitted, nonterminal `write` or `external` task exists; an `unknown` effect or an unknown prior effect holds the same barrier.

A task revision has exactly one owner: a delegated revision normally accepts one `agent.requested` whose native handle equals its plan owner; retries use a new task revision and assignment. If native creation is directly observed to fail before returning a handle, the admitted delegated revision instead accepts one `agent.not_created`. It must precede any result, cannot coexist with an `agent.requested`, and must reference one or more already recorded `observation` evidence entries. It permits only one final `task.result` with `outcome: failed` and `effect_status: none`, and that result cites at least one of the same no-creation evidence IDs. Unknown creation/effects, a missing inventory entry, and any genuine request retain the normal lifecycle barrier. A later task revision remains subject to dependency, attempt, revision, cause, strategy-change, and no-progress rules.

A native handle may be reused by `followup_task` only after its prior assignment has both a released result and a terminal reconciled observation. The new request binds later observations to the new task revision; the prior terminal fact cannot release new work. A synchronous root-owned write has no agent handle and releases when its result carries required evidence and `effect_status: reconciled`. A delegated write releases only when a reconciled result and the assignment's latest observation are simultaneously terminal and reconciled; order between those two facts is immaterial. Until that boundary is reached, each newer observation supersedes the prior lifecycle for release decisions, so `completed/reconciled` followed by `active/unknown` before the result still holds the barrier. Once both facts coexist, release is an immutable historical fact; a later native lifecycle belongs to a new assignment only after a new `agent.requested`. Idle, interrupted, missing, or `effect_status: unknown` preserves the barrier. Requested model/effort are never copied into effective fields: absent observations are represented by JSON null and project as `"unknown"`.

An `unknown` task result is an immutable observation, not a terminal result. Recovery may append exactly one later `task.result` for the same task revision whose outcome is `passed` or `failed`, whose effect is no longer unknown, and whose evidence references establish the reconciliation. The projection uses the later result while the log preserves both. A known outcome paired with `effect_status: unknown` is contradictory and rejected at ingestion; this keeps every accepted unknown-effect result append-only reconcilable. A known result cannot be replaced, and the task revision cannot be admitted again merely to reconcile it.

Every later plan revision names existing `trigger_event_ids` and changes an operational task field, allowance, no-progress bound, or evidence strategy; revision number, reason, and trigger IDs alone do not count. A `failure` revision additionally requires `unmet_criterion`, `failure_evidence_ids`, `cause`, and `strategy_change`; `cause` is one of `missing_input_or_authority`, `ambiguous_brief`, `decomposition`, `capability`, `environment_or_tool`, or `candidate_defect`. A `user_amendment` points to `run.amended` or `user.decision`; an `evidence_change` points to new evidence/decision facts. These two reasons require no fictitious failure. A repeated dispatch with no operational difference and revisions beyond the committed limit are rejected. The helper checks references and recorded difference; the root judges material adequacy.

`validate` checks syntax, references, immutable revisions, transitions, dependency admission, one-writer state, and (with `--terminal`) completion. Any admitted task must have a terminal, reconciled result before closure. A safely never-admitted task may remain visibly planned in a `failed` or `stopped` run because it created no task effect; `remaining_human_items` and the derived report preserve that unfinished scope. Terminal `completed` requires every task in the current plan to pass, each criterion to reference at least one `observation` whose recorded `criterion_ids` contains that criterion, and a passed check with recorded evidence. It also requires all material findings dispositioned, no accepted blocker/major finding, reconciled effects, reconciled scope, and explicit remaining-human items. Later failed checks do not have a deterministic supersession meaning unless the event contract states one; the report surfaces them and the root owns semantic disposition. `failed` and `stopped` remain valid terminal outcomes only when admitted effects are reconciled and uncertainty is reported.

`snapshot --write` validates the complete log first, computes SHA-256 over the exact `events.jsonl` bytes, and atomically replaces `snapshot.json` with the projection. The projection contains `v`, `run_id`, `events_sha256`, `last_seq`, `terminal`, objective/constraints, current plan/tasks/agents/findings/evidence/checks, assumptions/decisions with correction links, received user decisions, knowledge selection and feedback, baselines, next action, and unresolved user items. A missing, malformed, non-UTF-8, or stale snapshot is regenerated only from a valid log; an invalid or non-UTF-8 authoritative log is a structured data rejection and leaves the existing snapshot byte-for-byte unchanged.

`resume` first performs exactly the `snapshot --write` repair: it may create or replace only the derived snapshot when missing/stale, and rejects an invalid log without changing it. It then returns advisory `agent.observed` proposals plus `admission_allowed` and `recommended_next_action`; advisory observations do not mutate log or snapshot. The caller persists accepted observations with `append` and explicitly runs `snapshot --write` again. Idle, interrupted, and missing observations carry `effect_status: unknown`, never imply completion, preserve a delegated writer barrier, and force admission false. A stale admission next action recommends `revise_plan`.

`report --write` validates the log and snapshot binding and atomically replaces `report.md`. It labels delivered and failed tasks, observations, inferences, unknowns, untested checks, open findings, remaining human items, and the next action. Empty typed sections say that no entries were recorded rather than claiming semantic absence. The unknown section includes directly stored unknown effective model/effort, lifecycle, and effect fields as well as typed unknown evidence. It does not parse arbitrary prose for hidden facts. The report is never read as state.

## Knowledge helper

Invocation:

```text
python3 sage/scripts/sage_knowledge.py validate --store-dir STORE_DIR
python3 sage/scripts/sage_knowledge.py retrieve --store-dir STORE_DIR --cues CUES_JSON --limit N
python3 sage/scripts/sage_knowledge.py stage --store-dir STORE_DIR --proposal PROPOSAL_JSON --generation-id ID --expected-current ID_OR_NONE
python3 sage/scripts/sage_knowledge.py activate --store-dir STORE_DIR --generation-id ID --expected-current ID_OR_NONE
python3 sage/scripts/sage_knowledge.py rollback --store-dir STORE_DIR --generation-id ID --expected-current ID
```

The store layout is the one in `ARCHITECTURE.md`. `current.json` is `{v:1,generation_id,manifest_sha256}`. A truly absent pointer is the empty store; any present pointer path, including a dangling symlink, must be a regular file. A generation manifest lists every relative file and SHA-256; validation rejects missing, extra, malformed, duplicate-ID, hash-mismatched, path-escaping, or non-finite content. A structurally valid file whose bytes differ from its manifest entry is rejected with code `generation_hash_mismatch`, allowing integrity tests to distinguish it from schema rejection.

A record contains `v`, stable `id`, positive integer `revision`, `prior_revision` (null only at revision 1), `status`, `evidence_class`, `gate_rationale`, `gate_evidence`, `rule`, `recognizer` (cue object), `qualifier`, `falsifier`, `evidence_summary`, `provenance` (terminal run IDs and evidence locators), `alternative_explanations`, `counterevidence`, `refutation`, `review`, `created_at`, and `reviewed_at`. Valid UTC timestamps are compared as instants across every accepted fractional digit, with trailing zeros equivalent; review cannot precede creation. The proposer authors the candidate; the refuter independently searches for boundary failures and records outcome (`passed`, `failed`, `unsupported`), findings, and evidence; the reviewer owns every finding disposition and the evidence-class gate decision. Their actor IDs are all distinct. Create, correction, supported-status change, and retirement require a passed refutation, all findings dispositioned by the reviewer, and a passed review. An unsupported or failed refutation cannot be activated.

For `supported`, the helper checks structured gate evidence: a scoped fact names a repeatable check and environment; a transferable heuristic names materially different contexts plus comparison/corroboration and confounder/counterexample dispositions; causal guidance names controlled/counterfactual or direct-mechanism evidence plus alternative-cause dispositions. It validates presence, references, and role separation, not truth or persuasiveness. The independent reviewer makes the semantic R-049 gate judgment; the promotion coordinator decides whether to land the reviewed proposal. A material proposal change returns to the author and requires renewed independent refutation and review. Correction retains the stable ID, increments revision by one, names the prior revision, and preserves prior files/history in an immutable older generation.

## Paired native result v3

The frozen v2 paired-result validator and its integer `execution.exit_code` requirement remain unchanged. Native collaboration results use the explicit successor in `evaluation/native-result-protocol-v3.md` and the `pairing.py validate-native` public command. V3 binds `lifecycle: completed` to `native_observation` evidence, allows a null unobserved native exit, and stores actual subprocess integer exits only in separate command records. Authored journals are labeled `journal`, never raw transcripts. Adapted historical data is an informed diagnostic and does not change an original trial, score, gate, or acceptance criterion.

`retrieve` reads only the active generation. Cues are an object whose array values are normalized strings for `task`, `domain`, `artifact`, `environment`, `risk`, `operation`, and `failure`. A recognizer is the same cue object and matches when at least one listed value intersects. A qualifier is `{all: CUE_OBJECT, none: CUE_OBJECT}`: every nonempty `all` key must intersect and every `none` key must not intersect. Natural-language applicability remains in the rule for agent judgment, not deterministic filtering. The command returns `{generation_id,cue_fingerprint,retrieval_status,matches}`. Matches include exact ID/revision/status/reason and are deterministically ordered. Normal selection excludes refuted/retired; provisional/contested are returned only when the cue file sets `include_non_supported: true`. No match is successful.

`stage` accepts `{action,proposer,reviewer,source_runs,record}` where action is `create`, `correct`, `contest`, `refute`, or `retire`. An existing record enters `retired` only through `retire`, with its intentional basis and reason; `create` may import a new historical retired record at revision 1. Every source run directory must have a valid terminal state and reconciled effects; active, malformed, and unknown-effect sources are rejected unchanged. Before work and immediately before rename it requires `current.json` to equal `--expected-current` (`none` for an empty store). It copies that generation, applies the proposal into a new immutable generation using a sibling temporary directory, validates it, fsyncs durable files where supported, then renames the directory. It does not change `current.json`. Existing target IDs and partial generations are rejected.

Every provenance, refutation-evidence, finding, disposition, counterevidence, supported comparison/corroboration, causal-evidence, and source-run reference must resolve to a bare event/evidence ID or `events.jsonl#ID` in the named validated source run, or to the exact hash-bound external locator recorded there. A URI fragment cannot alias a local ID.

`activate` validates the target generation and compares the live pointer to `--expected-current` immediately before atomically replacing only `current.json`. A stale stage or simulated/interrupted stage therefore cannot replace a newer pointer or select a partial generation. `rollback` has the same compare-and-swap rule, accepts only a complete previously valid generation, and never deletes generations or records. All retained history must remain integrity-valid for either pointer mutation: rollback handles an integrity-valid bad landing, while detected byte corruption blocks normal mutation unchanged and requires a separately designed evidence-preserving recovery.

## Installer boundary

Later integration replaces the active shell scripts with:

```text
bash sage/install.sh --target-root TARGET_ROOT [--source-root SOURCE_ROOT]
bash sage/uninstall.sh --target-root TARGET_ROOT
```

`SOURCE_ROOT` defaults to the directory containing `install.sh`; its explicit form exists for sandbox cutover tests. Install/update owns only `skills/sage/**`, `skills/sage-promote/**`, `sage/bin/sage_state.py`, `sage/bin/sage_knowledge.py`, and `sage/receipt.json` beneath `TARGET_ROOT`. The receipt records source hashes, installed hashes, operation, and inherited ownership. Any legacy policy, schema, fixture, phase-1 evaluator, source manifest, or runtime protocol is excluded. A missing allowlisted source fails before mutation. New unowned paths or locally modified owned files are never overwritten; update fails with a conflict report. Uninstall removes only receipt-owned files whose hashes still match, retains modified/unowned files, reports them, and removes no unrelated directory.

## Role-policy boundary

The deterministic helpers validate recorded lifecycle facts; they do not claim to enforce whether an agent was well briefed, independent, or appropriately routed. Those semantics are evaluated by frozen live scenarios with the actor receiving only the task, installed skill, and minimum case input.
