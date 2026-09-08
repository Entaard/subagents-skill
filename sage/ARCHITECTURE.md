# Codex Sage rebuild architecture

Status: all seven current module gates passed. The original live evaluation is complete: recovery passed, while six delivered reports and all four scored paired arms across two pairs failed their reporting gate; creative orchestration scored 7 and the six reports scored 7. Live-repairs-a1 rounds 1 and 2 failed; round 3 passed independent review at 8.5–9.0 in every dimension with zero open errors. LIVE-01 through LIVE-04 and DOC-01 are verified fixed. The assembled whole-skill final-a1 round 1 failed on one standalone-promotion documentation seam; round 2 passed at 8.5–9.0 in every dimension with zero open errors after its instruction-only repair. Historical live observations remain final and are not rescored by these repairs. See the [final handoff](docs/FINAL-REPORT.md) for verified results and limits.

### Final round-2 repair boundary

Round 1 found that architecture promised promotion its own plan and log, while the installed `$sage-promote` graph exposed only closed-source validation and knowledge-store operations. This was an instruction-integration failure, not an observed unsafe activation or missing helper capability.

The smallest seam is a promotion-specific coordinator procedure that explicitly reaches the installed sibling run, state, delegation, and recovery references. Its own append-only run records source/proposal/store baselines, assignments, checkpoints, and recovery decisions; selected source runs stay closed and read-only, and immutable knowledge generations stay store artifacts rather than coordinator task state. This adds no runtime, schema, implicit invocation of Main Sage, or ceremony to the zero-team `no_change` path.

### Live-repair boundaries

The first live repair wave changes existing seams rather than adding another framework:

- A delegated assignment whose native creation is known to have failed may record one evidence-bound `agent.not_created` fact. That fact releases no unknown effect: it is admissible only before any request for the assignment, requires observation evidence of the rejected creation, and permits only a truthful failed assignment result. The exhausted original creative plan can then close failed/stopped; a later genuinely successful bounded revision may still complete a run through the ordinary gates. Unknown creation, unknown effects, genuine handles, normal terminal observations, dependency gates, attempt limits, and revision limits retain their existing barriers.
- Reports distinguish an empty typed section from a claim of semantic absence. They render directly recorded unknown actor identity/effect fields and typed `unknown`/`untested` evidence; prose remains prose and is not semantically parsed. The operating instructions require material task unknowns and untested checks to be recorded before closure.
- The frozen result protocol v2 and its integer-exit rejection remain immutable. A successor v3 result encoding represents native lifecycle completion with bound evidence and a nullable unobserved native exit, while keeping actual subprocess exits in separate command records. At this public boundary, every v3 arm and its `execution` value are objects before nested access; `run_id`, `started_at`, and `finished_at` are nonblank strings. Timestamp syntax and ordering remain evaluator judgments rather than new parser policy. Round 1 incorrectly relied on truthiness for those strings and dereferenced `execution` before confirming its object shape. Historical records adapted to v3 are informed diagnostics, never retroactive trial passes.
- The installed state contract is the task-field and event-enum authority for operators. It names `note.recorded.category` as `assumption|decision` and includes a public-CLI example; source builders may additionally consult `docs/CONTRACTS.md`.

These decisions preserve the short skill entrypoints, append-only source history, deterministic public-CLI validation, and explicit honest-failure path. They add neither a portability layer nor automatic promotion.

Round 3 addresses the common cause left by the first two narrow repairs: shared v2-era validation dereferences nested records, tests identifiers by truthiness, and coerces references with `set()` before proving their types. A v3-only preflight validates the complete consumed object/array surface, nonblank text identifiers and string-array references before shared semantic/hash checks. Nullable unobserved effective identity and usage remain allowed; valid one-character evidence IDs remain valid. The v2 path, evidence-authenticity responsibility and timestamp-policy boundary remain unchanged. Public-CLI synthetic matrix tests and retained failure replays are the verification seams. The resumed session cannot create another builder thread, so root was the sole round-3 builder; the retained independent Astra critic remained separate.

## Outcome and boundary

Sage is a Codex-native orchestration skill that improves the quality of substantive work by making planning, delegation, verification, recovery, and reporting explicit. It spends extra agents only when their placement or independence is likely to improve the result. `sage-promote` is a separate skill that turns evidence from closed Sage runs into bounded, reviewed knowledge for later retrieval.

The rebuild targets Codex only. The live collaboration tool schema is the authority for available behavior. Cross-host adapters, a managed scheduler, durable leases, transaction protocols, universal performance claims, and automatic self-modification are outside this version.

The repository-root `CONTEXT.md` remains historical project context, but its Light/Managed split, 30-percent handover threshold, and source-global promotion destination are superseded for this Codex-only product. Active Sage uses boundary checkpoints, an explicitly supplied state root, and one explicitly supplied knowledge store. It never edits source policy as a promotion destination.

The architecture favors a short instruction spine plus branch-specific references. Python helpers are justified only for deterministic validation, state projection, retrieval, or reversible knowledge updates. Human- or model-judgment rules stay in prose instead of becoming a large pseudo-runtime.

## Product shape

There are two active entrypoints:

- `sage/skills/sage/SKILL.md`: plan and complete a task, or report/resume a Sage run.
- `sage/skills/sage-promote/SKILL.md`: inspect closed runs and create, correct, contest, or retire reusable knowledge.

They share file formats and deterministic helpers, not an implicit lifecycle. A Sage run cannot promote its own observations. Promotion cannot resume or finish the source task.

### Target source layout

```text
sage/
|-- ARCHITECTURE.md
|-- docs/
|   |-- REQUIREMENTS.md
|   |-- DECISIONS.md
|   `-- STATUS.json
|-- skills/
|   |-- sage/
|   |   |-- SKILL.md
|   |   |-- agents/openai.yaml
|   |   `-- references/
|   |       |-- run.md
|   |       |-- delegation.md
|   |       |-- verification.md
|   |       `-- recovery.md
|   `-- sage-promote/
|       |-- SKILL.md
|       |-- agents/openai.yaml
|       `-- references/
|           |-- knowledge.md
|           `-- promotion.md
|-- scripts/
|   |-- sage_state.py
|   |-- sage_knowledge.py
|   `-- sage-lifecycle.py          # source-only install helper
|-- install.sh
|-- uninstall.sh
|-- tests/
|   |-- test_state.py
|   `-- test_knowledge.py
|-- evaluation/
|   |-- README.md
|   |-- rubric.json
|   |-- cases/
|   |-- results/
|   `-- sandboxes/
`-- archive/legacy/                 # inert hash-inventoried baseline history
```

The final file set may be smaller when two references remain easy to use as one. It must not be larger merely to mirror this tree. The entrypoints must point to every conditional reference and state when to read it. Tests, agent outputs, and live forward-test artifacts produced during this rebuild stay under `sage/evaluation/`; `sandboxes/` is disposable test data, not product knowledge.

### Installed state layout

The implementation resolves one explicit `state_root`; the standard default is the absolute expansion of `~/.codex/sage`, unless the installation supplies a configured override. The caller states and passes that resolved path rather than inferring state from the installed skill package or task repository. Tests override it with `sage/evaluation/sandboxes/<case>/state`.

```text
<state_root>/
|-- runs/<run-id>/
|   |-- events.jsonl               # authoritative append-only facts
|   |-- snapshot.json              # validated projection for fast resume
|   `-- report.md                  # derived, never resume authority
`-- knowledge/
    |-- current.json               # active generation pointer
    `-- generations/<generation-id>/
        |-- index.json
        |-- records/<stable-id>.json
        `-- manifest.json
```

The installed package root is separate from `state_root`. It contains only `skills/sage/**`, `skills/sage-promote/**`, `sage/bin/sage_state.py`, `sage/bin/sage_knowledge.py`, and `sage/receipt.json`. The receipt hashes copied source bytes, installed bytes, and inherited ownership for safe updates. Runtime state is neither receipt-owned nor removed by uninstall. The documented Codex user-skill root is `$HOME/.agents/skills`, making `$HOME/.agents` the recommended lifecycle target; arbitrary targets exist for sandbox verification or explicit loading and do not by themselves prove automatic Codex discovery.

The default is an operating convention, not installer-owned configuration. Callers still pass the resolved path to every helper command. No helper infers permission to edit the task repository merely because a run exists.

## Main Sage components

### 1. Qualifier

The root first chooses the smallest adequate mode:

- **Inline:** tiny, tightly coupled, or cheaper to do than brief and verify. It may have zero delegated tasks and needs only a concise task record when persistence is useful.
- **Orchestrated:** substantive work with independently checkable units, useful parallel reads, a meaningful independent review, or context-heavy exploration.
- **Safety pause:** authority, essential inputs, or a safe effect boundary is missing.

The qualifier records why delegation is or is not useful. It does not force a minimum team size.

### 2. Planner and task graph

The root owns the objective, acceptance criteria, assumptions, risk, scope, plan revisions, integration, and completion claim. A plan is a small dependency graph, not a narrative transcript. Every task has:

- stable task ID and immutable revision;
- objective and falsifiable completion condition;
- dependencies and owner (`root` or one agent handle);
- read/write effect class and concrete scope;
- required inputs and expected return fields;
- verification method and risk level;
- requested model, effort, and context fork;
- state and links to evidence or findings.

Preserve old revisions and never redefine a dispatched task in place. Each plan commits finite, task-specific attempt and plan-revision allowances plus a no-progress condition; these are runtime bounds, separate from the rebuild review loop below.

Before a retry, record the unmet criterion, failure evidence, and a causal hypothesis: missing input/authority, ambiguous brief, wrong decomposition, inadequate model capability, tool/environment failure, or candidate defect. The response must address that cause by obtaining evidence, repairing the brief, changing the graph, changing routing within user constraints, or making a bounded candidate repair. An explicit user model choice is not silently escalated. A repeated failure with no discriminating evidence or material strategy change is no progress and cannot receive the same dispatch again.

When an allowance or no-progress bound fires, diagnose and materially revise the plan before more work. A persistence request authorizes further in-scope, finitely bounded replans while a distinct safe strategy remains; it does not authorize identical loops. Ask the user only for missing authority or an essential user-only input. If no materially different safe approach remains, stop with the impasse evidence instead of manufacturing progress.

### 3. Team and routing

The planner assigns a narrow role such as scout, researcher, builder, reviewer, interaction tester, or refuter. Roles are brief contracts rather than hidden agent profiles. Delegation is allowed only when the unit is bounded, sufficiently independent, packageable, falsifiable, and safe in its effect scope.

Initial routing priors are deliberately uncalibrated:

| Situation | Initial request | Status |
| --- | --- | --- |
| high-volume bounded reads/search | Luna, high effort | prior, not a measurement |
| guided implementation | Sol, high or xhigh effort | prior, not a measurement |
| exacting code/spec review | Sol, xhigh effort | prior, not a measurement |
| ambiguous architecture or adversarial criticism | Astra, high effort | prior, not a measurement |

The user’s explicit model choice wins. Capability to meet the criterion comes before cost. Cost includes root context, briefing, agent work, independent review, retries, and integration—not just the worker request. Current pricing may inform a run only when fetched from the current official source; the skill does not hard-code prices or transfer savings claims from other systems.

Each assignment records requested model/effort separately from effective model/effort. When the tool result does not report the effective values, they remain `unknown`.

### 4. Native orchestration

At run time, inspect the callable tool signatures rather than trusting cached documentation. The currently observed semantics to test and encode are:

| Need | Native operation | Contract |
| --- | --- | --- |
| start a worker | `spawn_agent` | accepts `model`, `reasoning_effort`, and `fork_turns`; record returned handle/name |
| control inherited context | `fork_turns` | `all` inherits full history but cannot override model/effort; `none` or a bounded count can override |
| steer active worker | `send_message` | delivery only; it does not wake an idle worker |
| continue idle worker | `followup_task` | starts another turn on the existing worker |
| reconcile handles | `list_agents` | source of current visible lifecycle state; idle is not completion |
| await updates | `wait_agent` | notification-aware wait, not state authority by itself |
| stop a turn | `interrupt_agent` | returned prior state is recorded; interruption alone is not proof of quiescence |

The root admits tasks only when dependencies are satisfied and a concurrency slot is useful. Read-only independent tasks may run in parallel. Shared-workspace mutation has one active writer, counting the root. Synchronous root writes close from their reconciled result/evidence; delegated writes additionally require a terminal handle observation. Reviewers never repair their own findings. Side-effecting work of unknown status is reconciled before retry.

### 5. Log and report

`events.jsonl` is the compact source of truth. Each line is a versioned JSON object with event ID, run ID, sequence, type, timestamp, actor, plan/task revision when applicable, and a small typed payload. Required event families are:

- run opened, objective/constraint amended, plan revised;
- task admitted, agent requested or known not-created, agent observed, task result claimed;
- evidence recorded, check run, finding opened/dispositioned;
- decision or assumption recorded/corrected;
- context checkpoint written/recovered;
- user decision requested/received;
- run closed or stopped.

The deterministic helper validates syntax, references, legal transitions, terminal completeness, and snapshot/report derivation. It does not judge whether evidence is persuasive or a design is good. Large tool output and confidential content are referenced by path/hash with classification instead of copied into the log. Credentials and capability secrets are never persisted.

`snapshot.json` is a hash-bound projection containing objective/constraints, the current plan revision, task states, agent handles, findings, assumptions/decisions and corrections, received user decisions, evidence links, selected knowledge and retrieval feedback, baselines, next action, and unresolved user items. `report.md` is regenerated from validated state. A report clearly distinguishes delivered results, observed evidence, inference, unknowns, and work requiring the user.

### 6. Verification and completion

Checks are proportional to the task’s risk and artifact type:

- deterministic checks first where they can decide the question;
- independent review for substantive work, with the reviewer seeing the request and frozen artifact rather than the builder’s rationale;
- targeted re-checks after fixes and a final integration check;
- primary/current sources for load-bearing real-world claims, with counterevidence and recency recorded;
- actual interaction and visual/usability/performance evidence for scoped creative or game tasks—compilation alone is insufficient;
- explicit `not tested` or `unknown` when a required observation cannot be made.

A run completes only when its acceptance criteria have evidence, required checks pass, every material finding is dispositioned, no accepted blocker or major issue remains, scope is reconciled, and remaining human work is surfaced. Sage makes no universal perfection guarantee.

## Situation-specific knowledge retrieval

Main Sage can read only the active promoted index, never search raw closed runs. Selection first occurs after task qualification and before final planning:

1. Derive observable cues from the current situation: task/domain, artifact type, environment/tool, risk trigger, requested operation, and known failure signature.
2. Match cues against index recognizers and qualifiers. Record the candidate IDs and reasons.
3. Load only the bounded set whose expected decision value exceeds its context and application cost. Preserve an explicit no-match result.
4. Apply a loaded rule only inside its qualifier. Current task evidence and current user instruction outrank promoted knowledge.
5. Record each loaded item as useful, neutral, misleading, or not exercised, plus missed recognizers discovered during the run. These are observations for later promotion, not promotion actions.

An empty store has no `current.json`. Retrieval still succeeds with `generation_id: "none"`, `retrieval_status: "no_match"`, and an empty match list; `none` is reserved from real generation IDs and is the shared sentinel recorded by `knowledge.selected`, so the helper output and recoverable run state cannot disagree. A matched result carries the bounded actionable record fields needed to judge the rule and its qualifier without a second, undocumented interface. The caller always supplies both the knowledge store and run paths explicitly; neither helper derives them from the task repository.

Persist the selected knowledge generation and exact record revisions. Before a retry or material decision, compare the current active generation and cue fingerprint; refresh only when the generation changed or a changed constraint, plan, environment, risk, artifact type, tool result, or failure signature adds/removes a cue. Re-query the active index, deduplicate already-loaded revisions, and re-check the qualifiers and current status of previously applied records. Unchanged generation and cues do not reload knowledge; a changed generation or selection is appended to run state for recovery.

The cue fingerprint binds both normalized cue arrays and the `include_non_supported` retrieval policy. Switching between supported-only retrieval and explicitly exposing provisional/contested records is therefore a material selection change rather than an unchanged refresh.

Each knowledge record has a stable ID, revision, status, evidence class, gate rationale, concise rule, recognizer, qualifier, falsifier, evidence summary, provenance links, counterevidence, review result, and created/reviewed timestamps. Evidence class controls the support gate:

| Evidence class | `supported` requires |
| --- | --- |
| `scoped_fact` | a direct, repeatable check establishes the fact/invariant for its declared artifact and environment; no transfer beyond that scope is implied |
| `transferable_heuristic` | a controlled comparison or independent corroboration across materially different qualifying contexts supports the same direction, while known confounders and counterexamples are resolved or bounded by the qualifier |
| `causal_guidance` | controlled/counterfactual evidence or equivalent direct mechanism evidence isolates the proposed cause from material alternative explanations |

Independent refutation and independent review are necessary for all three classes but cannot replace their evidence predicate. A confounded success, including a run where both model and prompt changed, stays `provisional`; unresolved material contradictory evidence is `contested`. The record persists the class-specific gate rationale and alternative explanations. Evidence status is one of:

- `provisional`: bounded evidence exists, but transfer is uncertain;
- `supported`: its class-specific evidence predicate, independent refutation, and review passed;
- `contested`: material counterevidence or scope disagreement is unresolved;
- `refuted`: its falsifier fired and the rule must not be used;
- `retired`: intentionally removed from normal retrieval with the reason retained.

Normal retrieval offers `supported` records. It may offer a highly relevant `provisional` or `contested` record only with its status and counterevidence attached. `refuted` and `retired` records remain auditable but are excluded.

Retrieval feedback may justify a later bounded recognizer, qualifier, cue-index, or rule refinement when its source evidence survives promotion review. Use and selection counts are discovery signals, not evidence that a rule is true; lack of use is not refutation. Exact revisions and feedback evidence stay in the source run so promotion can distinguish a missed cue from a false rule.

## `sage-promote` workflow

Promotion is an explicit, separately invoked workflow over terminal, integrity-valid runs whose effects are reconciled. Eligible terminal outcomes include successful, failed, and stopped runs; failure evidence is useful when its limits remain explicit. Active runs and runs with unknown effects are ineligible. Promotion has its own plan, log, and bounded team. The root promotion coordinator owns selection, synthesis, decisions, and landing.

1. **Qualify inputs.** Verify that every source run is closed, identify its scope and evidence, and quarantine malformed inputs without rewriting them.
2. **Extract.** A bounded reader or the root extracts candidate rules, applicability cues, falsifiers, direct evidence, counterevidence, and contradictions with existing records. One-run outcomes are not silently generalized.
3. **Compare.** Match candidates to stable IDs and active records. Choose create, correct, mark contested/refuted, retire, or no change. A correction keeps identity and history.
4. **Refute.** An independent refuter receives the candidate, its intended evidence class, source evidence, relevant existing record, and a mandate to find boundary failures, contradictory evidence, weak causality, or a better narrower qualifier. It does not receive a target approval verdict.
5. **Review.** An independent reviewer dispositions every refutation and counterexample and applies the declared evidence-class predicate above. Any material proposal change returns to its author and requires renewed independent refutation and review. Any unresolved material counterevidence yields `contested` or no landing, never `supported`.
6. **Stage and validate.** Build a complete new generation, validate stable references and hashes, and compare it with the prior generation. The active pointer has not changed yet.
7. **Land reversibly.** The promotion coordinator lands the independently reviewed proposal by atomically replacing only `current.json` after the generation is durable. Retain the prior generation. Rollback changes the pointer to a validated earlier generation; it never deletes audit history.
8. **Report.** Name source runs, record actions, evidence status, counterevidence, refutation dispositions, changed stable IDs, generation hashes, and rollback target.

Rollback is for an integrity-valid generation whose landed rule or status proves unsuitable. If any retained generation or pointer is structurally corrupt or hash-invalid, every normal mutation—including rollback—fails without changing the store. Preserve the corrupt bytes as evidence and use a separately designed recovery procedure; weakening history validation or deleting the damaged generation would make the audit trail untrustworthy.

A promotion batch is explicitly bounded in its plan. It stops or replans when evidence becomes heterogeneous enough that a single review cannot evaluate it coherently. Numerical evidence thresholds may be introduced only after calibration; they are not universal defaults.

Wrong knowledge is corrected promptly but reversibly. Strong direct counterevidence can first move an active record to `contested` or `refuted`, preventing normal retrieval. Correction creates a new revision with the same stable ID and points to the earlier revision and refuting evidence. Retirement is never deletion and disuse alone is not refutation.

Every generation manifest binds the active generation from which it was staged. Normal activation requires both the live expected-current value and the target's recorded parent to match; an intentionally older target uses `rollback` instead. Stable-record lineage is monotonic across all validated retained generations rather than derived only from the active snapshot: one stable ID/revision cannot acquire different bytes, and the next correction links to the greatest retained revision. A coordinator can therefore roll back an unsafe generation and stage revision N+1 directly from the safe active generation without temporarily reactivating unsafe revision N. These checks preserve linear revision meaning without deleting branches or inventing a transaction framework.

Generation staging and pointer changes use an expected-current comparison immediately before their one atomic rename. This is cooperative one-writer conflict detection, not a filesystem lease: it prevents a stale conforming promoter from landing over a changed pointer, but cannot prove semantic evidence quality, genuine actor independence, or exclude a nonconforming concurrent writer. Proposer, refuter, and reviewer IDs are structurally distinct and remain opaque native names; the coordinator must establish their live behavioral independence before landing.

## Context-loss and recovery protocol

There is no assumed reliable token meter and no numeric context threshold. The root checkpoints at stable, observable boundaries: after committing a plan, before and after a delegation wave, before a risky effect, after integrating results, after fixing findings, and whenever the host signals compaction or context pressure.

Before a planned handoff or pause:

1. stop new admissions;
2. use `list_agents` to record all known handles and reconcile completed/active/idle states;
3. record unknown side-effecting work as unknown and preserve the single-writer barrier;
4. validate the event log and write the hash-bound snapshot;
5. record the next action and the exact references required to continue.

After context loss or explicit resume:

1. locate and validate the authoritative event log and snapshot binding; rebuild a missing or stale snapshot from a valid log, but pause admission and preserve evidence when the log is invalid;
2. re-read the active skill spine and only the references named by the next action;
3. verify task/artifact baselines and re-run `list_agents`;
4. map handles by recorded agent ID or canonical name and append reconciliation evidence;
5. use `send_message` only for an active turn and `followup_task` for an idle worker;
6. do not retry unknown side-effecting work until absence or safe idempotence is proved;
7. revise the plan when the old next action is no longer valid.

Recovery preserves uncertainty. A rendered report, missing handle, idle worker, or interrupt acknowledgement cannot manufacture completion.

## Build and quality gates

The rebuild proceeds in dependency order:

```text
architecture -> verification -> sage -> promotion -> integration -> final
```

For each module, one builder produces a candidate and a separate Astra critic reviews that frozen candidate. A repair creates another round and the critic reviews again. Every applicable predeclared quality dimension must score at least 8.5/10 and the critic must report zero open errors; averages cannot hide a weak dimension. Every real score, failure, open issue, fix, and evidence pointer is appended to `docs/STATUS.json` history.

An approach receives at most four builder/critic rounds. Before another attempt, replan by naming the repeated failure cause and materially changing the approach, contract, decomposition, or evidence—not merely the wording or model. The new approach also has a four-round limit. Finite no-progress controls prevent blind looping while the user’s persistence request is honored by diagnosis and replanning. A final independent critic evaluates the assembled skill, not only module diffs.

The verification module is built before either skill is rewritten. It defines:

- functional unit tests for deterministic state and knowledge behavior;
- CLI integration tests in temporary `sage/evaluation/sandboxes` state roots;
- meaningful negative cases for malformed logs, illegal transitions, stale snapshots, wrong agent lifecycle assumptions, invalid knowledge, failed refutation, and unsafe rollback;
- held-out independent live forward tests whose prompts do not reveal the expected answer or earlier defects;
- calibrated 0–10 scoring with anchored dimensions and evidence for every score;
- a small reproducible comparison with a brute-force high-capability routing baseline on the same cases.

The comparison holds the task, inputs, checks, installed Sage procedure, and Astra root fixed; treatment uses Sage worker routing while baseline requests Astra for every eligible worker. Frozen manifests hash the real prompt/input/check/rubric/environment artifacts. The frozen v2 result validation retains its transcript/integer-exit rule. Native v3 validation instead requires hash-bound authored-journal, native lifecycle, artifact, check, and score evidence and keeps subprocess exits distinct. It reports every cost signal the live environment actually exposes. If normalized tokens or money are unavailable, they remain `unknown`; agent count, calls, wall time, and artifacts may be reported as limited proxies. A small case set supports only a bounded result about those cases, not a general savings or routing-causality claim. Design review passing is a **design gate**. Forward behavior passing is a later **empirical gate**. Neither substitutes for the other.

## Legacy migration

The baseline tree contained a much larger Phase 0/1 protocol, generated schemas, fixtures, lifecycle implementation, pilot, and references. The completed cutover:

1. inventory callers and preserve useful invariants in the new requirements or focused references;
2. make only `skills/sage` and `skills/sage-promote` the active skill packages;
3. replace installer/generator behavior with an allowlist that installs exactly those active packages and required tiny helpers;
4. ensure old `source-manifest.json` files and generated references cannot overwrite or reintroduce the rebuilt entrypoints;
5. label retained old checks and docs legacy, or move them intact under `sage/archive/legacy/` after path consumers are updated;
6. verify install, update, report/resume, promotion, and uninstall in a sandbox before declaring the migration complete.

Legacy material is quarantined rather than served. It is not an active fallback: if the new package is incomplete, installation fails visibly rather than serving the old version.

## Evidence bounds used by this design

| Source | Supports | Does not establish |
| --- | --- | --- |
| [Codex subagent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents) | models, reasoning effort, inheritance, and sandbox are configurable concepts | the live callable schema or effective values in this session; the live tool remains authoritative |
| [Codex pricing](https://learn.chatgpt.com/docs/pricing) | current cost evaluation should include input, cached input, output, and applicable modifiers | a timeless price table or Sage savings |
| [FrugalGPT](https://arxiv.org/abs/2305.05176) | cascaded/routed systems merit empirical cost-quality comparison | that its reported savings transfer to Sage or these models |
| [Lost in the Middle](https://arxiv.org/abs/2307.03172) | long-context position can affect performance, motivating compact pointers and recovery state | a universal context percentage or compaction threshold |
| [Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798) | independent external evidence is worth testing when self-correction lacks feedback | that models never self-correct or that one reviewer guarantees correctness |

## Contracts for the next builders

The exact dependency-free CLI and data boundary is frozen in `docs/CONTRACTS.md`; later builders implement that small interface rather than reviving the legacy runtime protocol. The verification builder must consume `docs/REQUIREMENTS.md`, freeze the rubric and held-out case boundary before seeing treatment outcomes, and provide a single command that exercises deterministic tests without network access. It must not report live forward-test passes it did not run.

The Sage builder must keep `SKILL.md` short, route conditionally to focused references, use the live collaboration semantics above, and satisfy the state/recovery tests. It must treat routing priors as hypotheses and make zero delegation a first-class path.

The promotion builder must share only the minimal record/state primitives, implement evidence status and independent refutation, and make every landing reversible. It must not let main Sage mine closed runs or promote automatically.

The integration builder must cut over installer/generator behavior, prove the active installed files are the rebuilt packages, and preserve or quarantine legacy inputs without serving them.

The final critic must review the installed result and held-out behavior against every applicable requirement, including interaction evidence for any creative/game case, and must leave `STATUS.json` with real per-dimension scores and zero open errors before completion is claimed.

## Main Sage implementation checkpoint

The `sage-a1` candidate implements the frozen run-state CLI and replaces the active main Sage spine with focused references. Round-1 recovery review exposed divergence among validation, projection, resume, and reporting. Round 2 centralized revision-specific facts, made unknown effects append-only reconcilable, and distinguished untouched stopped scope from completed scope, but its independent critic found that an early terminal observation could become absorbing before the task result existed. Round 3 defines release as a temporal reconciliation boundary: replay updates the latest observation until result and terminal effect facts coexist, then preserves the historical release. The same replayed release set drives validation, dependency/writer admission, handle reuse, closure, and resume. JSON readers also reject invalid UTF-8 at the data boundary, while a non-UTF-8 derived snapshot is rebuilt only from a valid authoritative log. The helper remains a dependency-free structural validator/projector rather than an authority, semantic grader, or lease engine. Promotion, knowledge-helper implementation, installer cutover, and installed/live evaluation remain dependent later modules; legacy generators and installers are not called by this wave.
