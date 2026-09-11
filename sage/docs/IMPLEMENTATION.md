# Sage implementation log

This is an append-only build narrative. Statements in earlier sections that a helper, installer, promotion module, or broad gate is “future,” “missing,” or “unrun” describe that historical wave only; the current integration state is recorded in the final section and `STATUS.json`. Historical critic outcomes and evidence are not rewritten into current claims.

## sage-a1 round 1 — main Sage

Scope: main `sage` skill, its run-state helper, and focused regressions. The knowledge helper, `sage-promote` rewrite, installer/generator cutover, legacy quarantine, and live forward evaluation remain later dependency-ordered modules.

### Candidate

- `scripts/sage_state.py` implements the frozen dependency-free CLI: init, atomic validated single/batch append, validation, hash-bound projection, advisory resume, and derived report.
- `skills/sage/SKILL.md` is an explicit-only instruction spine. Its focused run, delegation, verification, recovery, and state references cover observable excellence criteria, adaptive zero-agent orchestration, current live collaboration semantics, capability-first routing priors, one-writer handling, independent review, cause-based replanning, honest closure, and installed helper resolution.
- `tests/test_state.py` records regressions found while reconciling recovery and immutable-history behavior.
- D-019 documents the one minimal post-freeze interface clarification: an unknown task result can be reconciled once by a later evidence-bearing result for the same task revision. Both events remain immutable.

The helper is intentionally several hundred lines rather than a framework: strict JSON parsing, the full event vocabulary, reference/transition validation, projection, and six CLI commands account for its size. It has no third-party dependencies and exposes no scheduler, semantic grader, authority engine, or physical lease claim.

### Observations and repairs

The first frozen state run passed 7 of 9 tests. It rejected a pre-admission task refinement that legitimately retained its revision, and it allowed a later plan to expand a previously reached revision bound. Both were repaired from frozen fixture evidence; the next run passed 9 of 9.

A read-only recovery audit then found and reproduced these additional issues before submission:

- snapshot repair compared only the event digest and could trust tampered projected fields;
- resume admission did not include an unresolved root-owned effectful task;
- completed historical readers could be over-conservatively treated as an active barrier;
- admission could name a stale plan;
- attempt allowance was present but unenforced;
- an old delegated handle could be reused across task revisions;
- plan projection reset carried task outcomes;
- closure could omit current-plan tasks never admitted;
- an unknown result had no append-only reconciliation path.

The implementation now compares a snapshot to the whole freshly derived projection, binds handles to task revision, requires current-plan admission, enforces the current committed attempt limit, carries only same-revision task state, checks every current-plan task at closure, distinguishes released historical readers during resume admission, and implements D-019. Five focused regressions pass.

### Evidence

Scoped command shape follows `evaluation/README.md`, with `PYTHONDONTWRITEBYTECODE`, `SAGE_EVALUATION_SANDBOX`, and `TMPDIR` all confined beneath `sage/evaluation/sandboxes/state-wave`.

- Frozen state contract: 9 tests passed, 0 failed, 0 errors.
- Focused recovery/transition regressions: 5 tests passed, 0 failed, 0 errors.
- The package-local tiny example executed all five phases successfully: init, seven-event atomic batch append, snapshot, terminal validation, and report.
- Dependency-free checks passed frontmatter shape, explicit-only metadata, nine local Markdown links, Python syntax, and STATUS JSON. The bundled `quick_validate.py` could not start because PyYAML is absent; this wave did not install it.
- No knowledge, installer, broad red-mode, installed-package, paired comparison, or live behavioral pass is claimed in this module.

### Deterministic limits

The state helper validates recorded syntax, references, lifecycle facts, immutable history, and completion preconditions. It cannot prove that evidence is persuasive, a criterion expresses the user’s true intent, a worker is independent, a model actually matches the requested identity when the tool omits it, an actor holds authority, or a filesystem writer lease exists. Root judgment and actual tool/artifact observations remain required.

Source execution uses `sage/scripts/sage_state.py`; the future installer must place it at `<target-root>/sage/bin/sage_state.py` and install only `<target-root>/skills/{sage,sage-promote}` plus the two helper paths declared in the frozen contract. This round does not call the legacy generator or installer and does not claim the installed layout works yet.

## sage-a1 round 2 — deterministic repair

The independent round-1 critic failed all dimensions except simplicity/context efficiency and retained six error groups in `docs/reviews/sage-a1-r1.json`. Its exact inputs and outputs remain unchanged under `evaluation/sandboxes/sage-a1-r1-critic/`. This repair used those failures as evidence; it does not overwrite their scores or claim they were independently closed.

### Reproduced round-1 failures

The critic observed: resume admitted a delegated writer without a terminal handle and a root writer with unknown effects; contradictory failed/unknown results had no reconciliation route; two handles could attach to one assignment; late old-revision results marked a current revision passed; malformed common/enum values escaped structured rejection; graph expansion failed while a later `initial` retry passed; amendment correction links bypassed validation; and reports omitted terminal status, untested evidence, failed checks, and accepted residuals.

### Repairs

- Validation, dependency admission, terminal closure, and resume now share the same `released` rule. A small `execution_facts` replay binds results, requests, observations, and current tasks by `(task_id, revision)`; projection uses those revision-specific facts rather than task labels alone.
- Each task revision has one assignment. A native handle is preserved exactly and can be reused after a fully released terminal assignment; the new request rebinds later observations, so an old completion cannot release the new work. D-021 separates opaque native handles such as `/root/scout` from Sage artifact IDs.
- Known outcomes with unknown effects are rejected at ingestion. An accepted `unknown/unknown` result can be reconciled once by an evidence-bearing known result. Result and terminal-observation order is immaterial.
- Resume checks only admitted effectful work. Merely planned root work and released historical readers do not invent a barrier; an admitted unreleased root/delegated effect does.
- Common version/sequence/timestamp and payload enum values are type-checked before use. Calendar-invalid UTC timestamps, unhashable enums, malformed live-agent rows, duplicate live handles, duplicate keys, and nonfinite numbers receive structured exit-2 errors. Existing derived bytes remain unchanged on rejection.
- Pure graph expansion is an operational change; only revision 1 may use `reason: initial`. Correction links are checked before type-specific transitions, including amendment links.
- D-020 allows truthful failed/stopped closure with safely never-admitted tasks still planned, while completed closure requires every current task's own result. Completed criterion evidence must be associated in the observation and a passed check must cite evidence. Differently named check supersession remains root judgment.
- Reports now show terminal outcome/scope, passed and unfinished tasks, observations, inferences, unknown and untested evidence, failed and untested checks, open findings, accepted limitations, human items, and a terminal next action.
- Focused tests resolve their output root from `SAGE_EVALUATION_SANDBOX`. Installed recovery guidance now includes the observed `list_agents` normalization (`agent_name`, running/completed status shape, null effective identity) without adding a host adapter.

### Round-2 evidence before independent review

- Frozen product-state slice: 9 tests passed, 0 failures, 0 errors.
- Normal focused regressions: 14 tests passed, 0 failures, 0 errors. These cover both writer fact orders, unknown reconciliation, root planned/released controls, assignment reuse, canonical `/root/...` handles, stale revisions, late old results and reconciliation, wrong input types, graph/retry transitions, correction links, stopped/completed scope, completion associations, and report contents.
- The unmodified round-1 critic probe source was executed with a synthetic `__file__` pointing to fresh `evaluation/sandboxes/state-wave-r2-critic/`, so it wrote no round-1 critic artifact. Its retained `results.json` shows the prior controls repaired: unreleased writer admission false; planned/released root admission true; two-assignment rejection; current revision planned after late old result; four malformed common cases exit 2; dangling correction rejected; graph addition accepted; later initial rejected; evidence associations rejected; negative report facts present; tiny example init/append successful.
- The critic's `failed/unknown` fixture now fails at the contradictory first result, as explicitly permitted by its expected outcome. A separate normal regression proves the supported `unknown/unknown` → evidence-bearing `failed/reconciled` append path.

No promotion helper, promotion skill, installer, broad product red gate, installed execution, paired comparison, or live task-quality pass is claimed. Fixture lifecycle checks still do not prove physical lease enforcement, actual authority, semantic evidence quality, or effective model identity when the tool omits it.

## sage-a1 round 3 — temporal release and UTF-8 boundary

The independent round-2 critic retained two error groups and its scores in `docs/reviews/sage-a1-r2.json`. Its exact failing inputs, stdout, stderr, snapshots, and append attempts remain unchanged under `evaluation/sandboxes/sage-a1-r2-critic/`. The supplemental `evaluation/sandboxes/sage-a1-r2-replay/` directory was later overwritten by a scratch replay and is not original round-2 evidence; `evaluation/sandboxes/sage-a1-r3-critic/evidence-retention.json` records that limitation and current hashes. No lost bytes are reconstructed. Round 2 independently verified E2, E4, E5, and E6 fixed and left E1/E3 open.

### Initial failures

The new focused assertions were first run against the round-2 helper. Sixteen tests ran with eight assertion failures: resume incorrectly allowed admission after each of `active`, `idle`, `interrupted`, and `missing` superseded an early terminal observation before the result; invalid UTF-8 criteria, event, and live-agent files exited 1 with tracebacks; and invalid UTF-8 in a derived snapshot prevented recovery. These observations agree with the retained round-2 critic evidence; they are not relabeled as a pass.

### Repairs

- D-022 defines the missing temporal boundary. Replay keeps the newest provisional assignment observation until a known reconciled result and terminal reconciled observation coexist. It then records immutable task-effect and native-assignment release facts separately, which preserves historical completed readers and permits safe same-handle reuse without borrowing an older assignment's completion.
- The shared `mark_release` and `record_observation` primitives drive incremental validation and the revision-specific execution replay. Dependency admission, one-writer admission, closure, handle reuse, and resume consume those replay facts rather than independently interpreting task labels or the first terminal lifecycle.
- `read_json` now reads bytes, converts file I/O failures to `io_error`, and converts only UTF-8 decoding failures to structured `invalid_json`. Existing JSON parser errors remain structured. `bound_snapshot` treats that contract error as a disposable projection failure and rebuilds from a valid authoritative log; `read_events` continues to reject a non-UTF-8 log before any snapshot write.
- Installed `state.md` and `recovery.md`, the source contract, architecture checkpoint, and D-022 all state the same conditional release and UTF-8 behavior. The 25-line instruction spine did not grow.

The helper is 657 source lines after this targeted repair. Its size comes from the frozen full event vocabulary, strict transition/reference checks, atomic projection/append commands, and reports; the temporal repair adds two small replay primitives, not a scheduler or protocol framework.

### Round-3 evidence before independent review

- Frozen product-state slice: 9 tests passed, 0 failures, 0 errors under `evaluation/sandboxes/state-wave-r3/`.
- Normal focused regressions: 16 tests passed, 0 failures, 0 errors. The two additions cover all four terminal-then-unknown lifecycle orders, blocked resume and append, fresh terminal recovery, the already-correct result/observation orders and same-handle reuse, invalid UTF-8 for criteria/event/live-agent/log, derived snapshot repair, and byte preservation.
- The unmodified round-2 critic probe source was executed with a synthetic `__file__` rooted at fresh `evaluation/sandboxes/state-wave-r3-critic/`. Its retained `results.json`, `contracts.txt`, and `regressions.txt` show 9 frozen and 16 normal tests green. Twenty-two explicit post-run assertions checked all temporal, handle-reuse, and UTF-8 outcomes: each unsafe resume is false, each second-writer append returns `writer_busy`, the fresh terminal control validates, malformed JSON inputs return `invalid_json`/exit 2, and snapshot repair exits 0.
- The package-local executable example ran init, batch append, snapshot, terminal validation, and report with exit codes `[0,0,0,0,0]`; stdout/stderr and the report are retained under `evaluation/sandboxes/state-wave-r3/cli-example/`.
- Python syntax, STATUS JSON, eight active skill Markdown files, and all local links pass. `git diff --check -- sage` is clean. The bundled skill validator still cannot start because its external `yaml` module is absent; this source wave did not install a dependency or claim that validator passed.

No independent round-3 score or error closure is claimed. The deterministic fixtures do not prove semantic evidence quality, authority, physical lease enforcement, effective model identity, installed layout, live task outcomes, promotion behavior, or model/cost savings. Promotion, knowledge helper, and installer work remain deliberately outside this wave.

## promotion-a1 round 1 — immutable promotion and selective retrieval

This candidate adds only the frozen promotion module: the dependency-free `scripts/sage_knowledge.py` CLI, the explicit-only `sage-promote` skill and its package-local operating references, focused public-CLI regressions, and the narrow Main Sage retrieval reference. It does not change `sage_state.py`, install files, invoke a legacy generator, or claim an installed or live result.

### Observed failures before repair

The untouched frozen knowledge slice initially ran 10 tests with 10 errors because the contracted helper was absent; stdout and stderr are retained under `evaluation/sandboxes/promotion-wave-r1-red/`. Each added boundary was then observed failing through the public CLI before its repair: empty retrieval could not round-trip into `knowledge.selected`; retrieval-policy changes did not change the cue fingerprint; a stale staged snapshot could activate over a newer pointer; reused `(stable ID, revision)` bytes could conflict; a rollback made every later correction a dead end; an extra empty generation path escaped validation; argparse emitted non-JSON errors; a rehashed failed-refutation generation could activate; and global lineage conflicts or dangling parents could escape store validation. The corresponding `*-red/` and `*-green/` evidence directories are preserved under `evaluation/sandboxes/`.

### Helper behavior

- `validate`, `retrieve`, `stage`, `activate`, and `rollback` use strict UTF-8/JSON, explicit paths, structured errors, and the frozen state helper's native-handle and terminal-run primitives. The missing-pointer state is the reserved generation string `none`, so empty retrieval can be persisted unchanged into run state and cannot collide with a real generation.
- Retrieval normalizes and bounds cues, binds `include_non_supported` into the fingerprint, checks recognizer and qualifier data, returns actionable exact revisions, and excludes non-supported knowledge unless explicitly requested. Feedback and selection frequency are discovery inputs only; Main Sage never mines raw closed runs or promotes itself.
- Staging validates every completed, failed, or safely stopped source and each recorded reference. Active, malformed, non-UTF-8, unknown-effect, or missing-evidence inputs fail before generation publication. Passed role fields remain structural facts: the coordinator must observe three genuinely separate live behaviors.
- Supported scoped facts, transferable heuristics, and causal guidance have different recorded predicates. Repetition, approval, and confounded model-plus-prompt outcomes do not substitute for those predicates. Material unresolved counterevidence remains contested; correction, refutation, and intentional retirement preserve the stable ID and retained history; disuse is not a retirement basis.
- Each staged generation is a complete immutable directory whose manifest binds its parent, exact sorted paths and hashes, and role/action metadata. Normal activation requires both the target's staged parent and the live expected pointer to match. Rollback changes only the pointer. Across every retained generation, revision bytes are unique and the revision chain is contiguous: after rolling revision 2 back to a safe revision-1 snapshot, a repair can stage revision 3 from that snapshot without reactivating revision 2 or reusing its identity.

These expected-pointer checks assume one cooperative promotion writer. They detect a changed pointer and stale staged base; they do not implement a physical filesystem lease or transactional defense against a hostile writer.

### Executable skill and example

The 19-line `sage-promote` spine is explicit-only and routes details to two installed references. It qualifies bounded terminal sources; permits a small no-change path without a ceremonial team; separates the candidate author, adversarial refuter, reviewer, and landing coordinator; explains the role-routing priors; applies evidence-class gates; and gives complete stage, validation, activation, rollback, and reporting instructions. The package includes a complete proposal and every nested schema needed after installation.

The documented proposal was exercised in `evaluation/sandboxes/promotion-wave-r1-doc-example/`: nine public commands validated an empty store, staged and activated generation `g-1`, retrieved one actionable match, staged and activated `g-2`, rolled back to `g-1`, and validated two retained generations. All nine exited 0; `results.json` contains argv, stdout, stderr, match assertions, the active rollback pointer, and retained-`g-2` assertion.

### Round-1 evidence before independent review

- Frozen product-knowledge slice: 10 tests passed, 0 failures, 0 errors under `evaluation/sandboxes/promotion-wave-r1-final/contracts/`.
- Focused public-CLI regressions: 10 tests passed, 0 failures, 0 errors under `evaluation/sandboxes/promotion-wave-r1-final/regressions/`. The suite covers empty selection and first activation, policy-sensitive fingerprints, stale-base activation, safe post-rollback revision 3 plus revision-collision rejection, exact path integrity, structured argument errors, failed/stopped sources, every revision action and retrieval status, non-disuse retirement, rehashed failed refutation, and global lineage/parent validation.
- Unchanged shared-state controls: the frozen state slice passed 9 tests and the focused state regressions passed 16 tests under `evaluation/sandboxes/promotion-wave-r1-final/state-contracts/` and `state-regressions/`.
- Dependency-free checks passed two Python source compilations, five JSON examples, eight local Markdown links, frontmatter, explicit-only metadata, and `git diff --check -- sage`; outputs are retained under `evaluation/sandboxes/promotion-wave-r1-final/static/`.
- The bundled skill `quick_validate.py` could not start because the environment has no `yaml` module. Its traceback is retained under `evaluation/sandboxes/promotion-wave-r1-final/validator/`; this wave installed no dependency and does not relabel that check as passed.

No independent promotion score, critic error closure, semantic evidence proof, actual actor independence, physical writer lease, installed-package behavior, model placement, token/cost saving, paired comparison, or live task-quality result is claimed.

## promotion-a1 round 2 — reference, transition, time, and pointer repair

The independent round-1 critic failed promotion with four retained error groups and scores in `docs/reviews/promotion-a1-r1.json`. Its scripts and evidence directories were not rerun or modified. Four new public-CLI methods first ran with four failures under `evaluation/sandboxes/promotion-wave-r2-red/`, reproducing each reported cause before repair.

### Narrow repairs

- Reference closure now checks supported `comparison` as well as `corroboration` and causal evidence. Bare event/evidence IDs and `events.jsonl#ID` are documented local forms; a URI resolves only when its exact locator was hash-bound in the selected source. An arbitrary URI fragment can no longer alias a local event.
- A retained record can enter `retired` only through the `retire` action and its intentional basis/reason. A revision-1 `create` may still import historical retired knowledge, preserving the frozen import behavior. The revision-link diagnostic now correctly names the greatest retained prior revision.
- Creation and review UTC strings are validated as before but compared as parsed instants. A later fractional review and equal instants with different fractional precision pass; an earlier fractional review fails without publication.
- `current.json` symlinks are rejected before the missing-path empty-store branch, so a dangling symlink is not mistaken for `none`. A truly absent pointer remains a valid empty store.

Round-1 suggestion S1 is documented without weakening immutable-history checks. Normal rollback handles an integrity-valid bad landing and retains both generations. If any retained bytes or the pointer are corrupt, every normal mutation fails unchanged; the operator preserves the evidence and needs a separately designed recovery. Promotion does not delete the damaged history or fabricate a repair.

### Round-2 evidence before independent review

- Targeted red: 4 tests ran with 4 failures at the four critic boundaries. Targeted green: the same 4 methods passed. Positive controls cover valid local comparison and corroboration, an exact hash-bound external locator, a proper retirement, a historical retired create, later/equal/earlier fractional chronology, and a true empty store.
- Frozen product knowledge: 10 tests passed, 0 failures, 0 errors under `evaluation/sandboxes/promotion-wave-r2-final/contracts/`.
- Focused public-CLI regressions: 14 tests passed, 0 failures, 0 errors under `evaluation/sandboxes/promotion-wave-r2-final/regressions/`.
- Unchanged shared state: 9 frozen tests and 16 focused regressions passed under `evaluation/sandboxes/promotion-wave-r2-final/state-contracts/` and `state-regressions/`.
- The documented promotion flow ran 9 commands in a fresh store under `evaluation/sandboxes/promotion-wave-r2-doc-example/`; all exited 0, returned the actionable revision-1 match, rolled back to `g-1`, and retained `g-2`.
- The offline harness passed 11 tests. Dependency-free checks passed Python syntax, five JSON examples, eight local links, frontmatter, explicit-only metadata, and diff whitespace. The bundled skill validator again could not start because PyYAML is absent; its fresh traceback is retained and is not called a pass.

No round-1 error is self-declared verified fixed. No independent round-2 score, installed integration, live role independence, semantic evidence judgment, corrupt-history recovery, model placement, usage, cost, or task-quality result is claimed.

## promotion-a1 round 3 — exact accepted-precision chronology

The independent round-2 critic verified E1, E2, and E4 fixed and retained only E3: Python's datetime conversion discarded accepted fractional digits beyond microseconds. Its review and evidence remain unchanged in `docs/reviews/promotion-a1-r2.json` and `evaluation/sandboxes/promotion-a1-r2-critic/`.

One new public-CLI regression first passed later `.5000001` → `.5000002` and numerically equal `.500000100` / `.5000001` controls, then failed because earlier `.5000002` → `.5000001` staged successfully. The red result is retained under `evaluation/sandboxes/promotion-wave-r3-red/`.

The repair removes only the lossy conversion from knowledge-record chronology. After the shared validator accepts each UTC timestamp, the helper compares its fixed-width whole-second portion and its arbitrary-length fractional digits with trailing zeros normalized. This preserves the accepted format, treats decimal-equivalent instants equally, and uses no float or bounded-precision conversion. The same three controls pass under `evaluation/sandboxes/promotion-wave-r3-green/`.

Final scoped evidence before independent review:

- Frozen knowledge: 10 tests passed; focused public-CLI knowledge regressions: 15 passed.
- Unchanged state: 9 frozen and 16 focused tests passed.
- The documented promotion flow again completed 9 of 9 commands with an actionable match, rollback to `g-1`, and retained `g-2`.
- The offline harness passed 11 tests. Python syntax, five JSON examples, eight local links, frontmatter, explicit-only metadata, and diff whitespace passed.
- The bundled validator again could not import absent PyYAML. Its fresh traceback is retained; no dependency was installed and no validator pass is claimed.

No prior finding is self-declared closed and no round-3 score, installed behavior, live independence, semantic evidence quality, model placement, usage, cost, or task-quality result is claimed.

## integration-a1 round 1 — installed package and legacy cutover

This candidate implements only the frozen integration boundary. The source-only `scripts/sage-lifecycle.py` backs `install.sh` and `uninstall.sh`; it does not become part of the installed package. Install accepts an explicit `--target-root` and optional `--source-root` defaulting to the `sage/` source directory. Uninstall accepts only the explicit target.

### Lifecycle behavior

- Source preflight requires both complete active skill packages and the two helper scripts. Source files, target roots/components, and the receipt must be regular, non-symlinked objects at canonical allowlisted paths.
- Before mutation, install validates the whole source set, target/receipt safety, every owned hash, every exact destination conflict, and retired owned paths. A target beneath `sage/evaluation/sandboxes` is intentionally valid; overlap is rejected only when it would contain the source root or collide with shipped `skills/` or `scripts/` paths.
- The receipt binds its exact target and records sorted ownership plus source, installed, and inherited installed SHA-256 values. Fresh unowned destinations and locally edited/replaced owned files cause a conflict without overwriting either.
- Update copies the new allowlist and removes a retired owned file only when its prior hash still matches. Uninstall removes only unchanged receipt-owned files, retains modified/replaced paths, reports both sets, removes the receipt, and leaves all directories and runtime state unowned.
- Installed helper modes were exercised through their public CLIs: state `init`, `snapshot`, `report`, and `resume`; knowledge `stage`, `activate`, `retrieve`, a revision-2 stage/activate, and rollback to the retained revision-1 generation. Installed Markdown links resolve entirely within the copied packages.

### Legacy migration audit

The selected legacy baseline is commit `c816a6250d0df74e6cbfa9b2a672a2fc15110deb`. A path-scoped `git archive` extraction preserved 186 original files beneath `archive/legacy/`; a second extraction compared equal before active removal, and `archive/legacy/SHA256SUMS` verifies all 186 bytes. The selection includes the old policies, runtime, artifacts, libraries, knowledge seed, phase documents/evaluation, scripts/tests, copied active references, and the baseline originals of the previously deleted `promotion-contract.md`, `source-manifest.json`, and `workflow.md`. Of 194 baseline Sage paths, the eight outside this selected archive are seven rewritten active entrypoints (`README.md`, both shell wrappers, both skill entrypoints, and both metadata files) plus the removed tracked `scripts/__pycache__/check-phase0.cpython-311.pyc`, which remains recoverable from Git. The original lifecycle helper is one of the 186 archived files and also has a rewritten active successor; it is not one of those eight.

Only those known legacy paths were removed from active locations. Mixed rebuilt directories remained in place. The archived generator and old lifecycle are inert: active wrappers invoke only `scripts/sage-lifecycle.py`, the active skill trees contain no source manifest or copied legacy policy, and the installer rejects such a manifest if reintroduced.

### Integration evidence before independent review

- The original five installer contract tests and eleven added public regressions pass together: 16 tests, zero failures or errors under `evaluation/sandboxes/integration-wave-r1-green7/`. Earlier red and repair checkpoints remain separate and are not relabeled.
- The complete historically named `red` gate passed 77 tests with zero failures, errors, or skips under `evaluation/sandboxes/integration-wave-r1-final4/`: 46 evaluation/product tests plus the unchanged 16 state and 15 knowledge regressions. The runner records `live_trials_run: false` and `network_used: false`.
- Harness-only mode separately passed 11 tests under `evaluation/sandboxes/integration-wave-r1-harness/` before the final installed rollback/link additions; those same harness tests are included in the final 77-test gate.
- Dependency-free syntax, JSON, active local-link, explicit-only metadata, archive-hash, and active-legacy-absence checks are recorded under `evaluation/sandboxes/integration-wave-r1-static/`. The bundled `quick_validate.py` cannot import absent PyYAML; no dependency was installed and no validator pass is claimed.

This is deterministic and sandbox integration evidence only. It does not prove live task quality, semantic evidence judgment, actual role independence, effective model/effort, token usage, prices, cost savings, filesystem atomicity under every crash/race, or recovery from corrupt retained knowledge history. No live or paired trials ran, and no integration score is assigned by the builder.

## integration-a1 round 2 — sandbox isolation and uninstall preflight

The round-1 critic retained two errors in `docs/reviews/integration-a1-r1.json`. E1 showed that the overlap-positive test used a fixed prior evidence path and recursively deleted it. E2 showed that replacing the later-sorted `skills/sage/agents` parent with a regular user file let uninstall remove six earlier files before raising `NotADirectoryError` without a partial report.

Two public regressions went red together under `evaluation/sandboxes/integration-wave-r2-red3/`: an exact local source copy lost a sentinel at the old fixed target, and the late parent replacement lost earlier reference files. The first two `integration-wave-r2-red*` directories retain command-invocation mistakes and are not product evidence.

The overlap test now allocates its target only through `support.sandbox()`, asserts that the normal runner keeps it beneath the copied Sage source, and has a subprocess isolation control that preserves a sentinel at the former fixed path. The lifecycle preflight now rejects an existing non-directory parent while loading every receipt record, before unowned scanning or the first removal. One regression covers both the early `references` and late `agents` parent order and verifies the receipt, replacement, saved user tree, and every other installed byte remain unchanged.

Focused lifecycle tests passed 18 of 18 under `evaluation/sandboxes/integration-wave-r2-green/`. The full offline runner passed 79 of 79 with zero failures, errors, or skips under `evaluation/sandboxes/integration-wave-r2-final2/runner/`; it records no live trial and no network use. Before the first broad run, 646 round-1 critic and `integration-wave-r1-*` evidence files were hashed; all 646 verified unchanged after that run and again after the finalized-metadata run, with the latter record in `integration-wave-r2-final2/prior-evidence-verify.txt`.

This repair preflights the predictable parent/type state represented at invocation time, but the lifecycle remains a non-transactional multi-file operation. Unexpected I/O failures or concurrent filesystem changes can still interrupt it; no crash-atomicity or hostile-writer guarantee is claimed. The bundled validator remains unavailable because PyYAML is absent, so only the retained dependency-free metadata, link, JSON, syntax, and hash checks are claimed.

The repair covers predictable parent/type conflicts, not unexpected I/O after removals begin. Install/update/uninstall remain multi-file operations rather than a crash-atomic transaction; no broader transaction framework, hostile-writer guarantee, or partial-effect recovery protocol is claimed. E1 and E2 remain open until a separate critic verifies the frozen round-2 candidate. Scores remain null for this builder submission, and live quality/cost claims remain unrun.

## live-repairs-a1 round 1 — honest failure, reporting, native results, and contract drift

The original live evaluation remains frozen: its scores, failures, v2 protocol/rubric, selections, cases, setup, observations, scoring artifacts, and `docs/LIVE-RESULTS.md` were neither regenerated nor rescored. This repair changes the active source and runs known cases only as informed diagnostics on fresh copies beneath `evaluation/sandboxes/live-repairs-a1-r1-builder/`. A separate critic has not yet assessed this candidate.

### Architecture and contract decisions

- `agent.not_created` is the smallest append-only fact for a directly evidenced native rejection before handle creation. It cannot coexist with a request, must cite prior observation evidence, and admits only a final failed/no-effect assignment result. Missing/unknown creation, genuine handles, effects, dependencies, attempts, plan revisions, and no-progress conditions keep their prior gates. An in-budget revised assignment may later pass through normal lifecycle evidence; the exhausted original creative plan stops honestly.
- The derived report now says “No entries recorded” for an empty typed section, lists failed tasks, and renders directly stored unknown effective model/effort, lifecycle, and effect values. Instructions require material task unknowns and untested experience checks to become typed evidence before closure. The renderer deliberately does not infer facts from arbitrary prose.
- The frozen `pairing.py validate` v2 behavior is retained. `sage-live-native-scored-results-v3` uses the separate `validate-native` command, a bound `native_observation` completion record with nullable native exit, authored `journal` evidence, and separately evidenced subprocess command exits. The validator checks structure and hashes, not authenticity or semantics.
- Installed `state.md` names `note.recorded.category` as `assumption|decision` and includes an executable note append. `run.md` treats installed `state.md` as the operator's task-field authority and describes the shipped installer in the present tense. Promotion now names distinct candidate author, refuter, independent reviewer, and landing coordinator: a material change returns to the author for renewed challenge/review.

### Red and green evidence

- LIVE-01: `red-live01/` ran 3 tests with 3 expected failures before `agent.not_created`; `green-live01/` passed the same 3.
- LIVE-02: `red-live02/` retained 7 failing original-report subcases; `green-live02/` passed the cumulative 5 state/report methods. Those historical dependencies were then removed from the normal test gate in favor of maintained synthetic fixtures.
- LIVE-03: `red-live03-self-contained/` ran 8 methods with the positive v3 case and four structured-negative subcases failing at the missing public command; `green-live03/` passed all 8 after the versioned implementation. The earlier `red-live03/` is retained as a superseded test draft because it depended on disposable historical sandboxes.
- LIVE-04: `red-live04/` ran 9 methods with the installed enum/example check failing; `green-live04/` passed all 9 after the installed reference changed.
- The finalized focused suite in `focused-final/` passed 10 tests, including missing/invalid evidence, unknown/duplicate/final outcomes, post-request and root bypasses, dependency/attempt/revision bounds, an in-budget successful later revision, typed unknown/untested rendering, native-result positives/negatives, v2 rejection, and installed-only note authoring.
- The fresh complete offline gate in `final-offline2/` passed 89 tests with zero failures, errors, or skips. Its machine report records `live_trials_run: false` and `network_used: false`; 79 are the prior gate and 10 are new live-repair regressions.

The informed diagnostic summary is `evaluation/sandboxes/live-repairs-a1-r1-builder/informed-diagnostics-final/diagnostic-summary.json`. It records: exact 22-event creative history preserved as the prefix of a stopped, terminal-valid copy with no invented request; seven copied original reports regenerated with event logs unchanged, qualified empty sections, and stored native unknowns; original v2 validation still exiting 2; and a historical v3 adaptation exiting 0 with null native exits, journals distinct from transcripts, and six captured subprocess exits in separate command records. Before/after inventories compare 2,239 protected files unchanged with inventory digest `4a61d7d9b779c5329adf4afcf1da90d9caf8116e209f701094fabb316955a1f4`.

Remaining limits are explicit. Evidence kind/reference validation cannot prove that a claimed native observation is authentic or semantically sufficient. Existing prose-only task limitations do not become typed evidence automatically. V3 is a successor encoding, not a revised historical trial or changed acceptance gate. The original creative run remains a stopped informed-diagnostic copy while its disclosed separate continuation remains historical. No final score, critic pass, closed finding, new live trial, model-placement proof, token/money measurement, portability claim, or broader transaction/lease guarantee is asserted here.

## live-repairs-a1 round 2 — native v3 shape and primitive boundary

Round-1 independent review failed with LIVE-03 still open; its eight recorded dimension scores remain 8, 8.5, 8, 9, 8.5, 9, 8, and 8.5. LIVE-01, LIVE-02, LIVE-04, and DOC-01 were independently verified fixed and their source and evidence remain unchanged except where this round's required architecture/status log describes that verdict.

The remaining cause was narrow: the v3 path used truthiness for `run_id`, `started_at`, and `finished_at`, and read `execution.evidence` before proving that `execution` was an object. The repair validates the result, pair, arm, and execution object shapes before their v3 nested access, then requires the three identity/time values to be nonblank strings. It adds neither timestamp parsing nor an exception blanket. The v2 branch retains its prior behavior.

Retained round-2 evidence separates product reds from test-fixture mistakes:

- `red-current/` exposed three product failures; its empty `finished_at` object was already rejected by old truthiness and therefore did not reproduce the critic's nonempty-object case. `red-exact/` corrected that fixture and ran 11 methods with all four required subcases red: three exit-0 false accepts and one exit-1 traceback.
- `retained-red/results.json` replays the four critic commands against the immutable retained round-1 validator. All outputs exactly match: three exit 0 and one `AttributeError` exit 1.
- `green-four/` passed the same 11 methods after the minimal execution/type guard. `red-surrounding/` then exposed two further tracebacks at the immediate result/pair object boundary; its arm-null control already returned structured exit 2. Explicit result/pair guards fixed that same root cause.
- `focused-final/` is retained as a test-fixture error: all product cases preceding it were green, but the new preservation test removed provenance from the wrong evidence entry and raised `KeyError`. The corrected fresh run in `focused-final2/` passed all 13 methods. It retains valid evidenced nullable completion, the four exact malformed inputs, result/pair/arm shapes, native and subprocess type rejection, provenance/reference rejection, the prior repairs, and v2 behavior.
- `retained-green/results.json` runs the active validator against the exact four critic fixtures; every case returns structured JSON exit 2 without a traceback.
- The fresh complete offline gate in `final-offline2/` passed 92 tests with zero failures, errors, or skips and records no live trial or network use.

This remains a structural and hash-binding validator. It does not authenticate observations or parse timestamp syntax/order. Exact critic fixtures and historical adaptations are informed diagnostics, not rescoring or fresh live trials. LIVE-03 remains open until separate independent review; no round-2 critic pass or changed historical score is claimed.

## Live-repairs round 3: complete native-v3 input boundary

The round-2 critic failed the candidate with scores 8, 8.5, 7.5, 9, 8, 9, 8, 8.5. Its original four reproductions were fixed, but the broader boundary retained 42 failures: 20 nested-object crashes, 12 truthy primitive accepts and 10 reference-coercion accepts. This history remains unchanged.

Root became the sole builder after the resumed session rejected both the unavailable prior builder's followup and a fresh Sol spawn with `agent thread limit reached`. The existing independent Astra critic successfully resumed and remains separate. No model override or cost improvement is inferred from this fallback.

Architecture was updated before tests or validator changes. Three self-contained public-CLI matrix tests then produced 51 failing subcases against the old validator. A v3-only preflight now checks every consumed nested record/collection, nonblank text and reference-array element before shared checks dereference records or create sets. The same three methods passed after the change. The additional red count includes blank-string and null-identifier cases beyond the critic's 42 retained fixtures; it is not a new live evaluation.

Evidence lives in `evaluation/sandboxes/live-repairs-a1-r3-builder/`: original `red/`, `green/`, complete offline `full/`, and exact retained-fixture replay outputs. Frozen v2 protocol/rubric and the original live scores remain unchanged. Current success is a builder result only until independent review.

The independent round-3 review subsequently passed with scores 9, 9, 9, 8.5, 8.5, 9, 9, 8.5 and zero open errors. It independently passed 95 tests, replayed 256 retained cases and 19 new controls, and reproduced 51 matrix failures on retained old code versus a pass on current code in portable source copies. All 2,178 protected entries matched. This closes LIVE-03 for the repair module, not the original failed live trial or the outstanding whole-skill gate.

## final-a1 round 2 — standalone promotion coordination seam

The whole-skill round-1 critic failed with one major finding and scores 7.5, 8, 8.5, 8.5, 8, 7, 8.5, and 8. Its retained installed graph proved that `$sage-promote` reached only its own entrypoint, promotion workflow, and knowledge contract, while Main Sage reached the already implemented run/state/delegation/recovery contract. This is a documentation-integration error, not an observed unsafe activation or helper failure.

D-031 records the smallest repair: promotion owns a separate coordinator run and explicitly reaches the installed sibling run, state, delegation, and recovery references. The promotion-specific text records source/proposal/pointer/generation/authority baselines, actual assignments and requested/effective identity, total delegation overhead, boundary checkpoints, writer/effect reconciliation, stale-next-action revision, and truthful completion. Closed source runs remain read-only, generations remain store artifacts, existing authority is reused when it still covers the action, and a root-only `no_change` writes no generation. No helper, schema, invocation policy, frozen protocol/rubric, or historical live result changed.

Focused installed verification is retained in `evaluation/sandboxes/final-a1-r2-builder/`. Before the instruction edit, `red/summary.json` ran six checks: five existing public-CLI/main-seam controls passed and the standalone instruction graph alone failed because it could not reach the four shared references. The first post-edit `green/` run retained a probe-only case-sensitive mismatch between sentence-leading “Knowledge” and a lowercase fixture; `green2/` passed after case normalization. After the explicit own-run finish and continuing-authority wording, final `green3/summary.json` passed all six checks. The scripted scenario covers pre-dispatch stale projection, corrupt own authority, unknown actor/effect writer barrier, pre/post stage and activation checkpoints, changed pointer/proposal/authority replanning, unchanged source logs, and zero-team/no-generation `no_change` through freshly installed public CLIs.

The unchanged complete offline gate passed 95 tests with zero failures, errors, or skips in `full/`, `full2/`, and `full3/`; `full3/` follows every installed instruction change and the finish/authority refinement. None used network access or a live trial. Fixture actor IDs and next-action decisions are explicitly informed scripted evidence, not native model execution, behavioral independence, semantic evidence proof, or a rescore of the original live evaluation. The round-2 candidate remains open pending a separate whole-skill critic.

The builder's final `full4/` gate also passed 95/95 before release. Subsequent independent whole-skill review [final-a1-r2](reviews/final-a1-r2.json) verified E1 fixed and passed with scores 8.5, 9, 8.5, 8.5, 8.5, 8.5, 9, 8.5 and zero open errors. It covered all 57 requirement IDs, passed a copied-source 95-test suite and six focused checks, retained the same checks' old-package documentation failure, and ran an additional 13-command installed lost-activation-acknowledgement scenario. All 15 installed links, 313 original scorecard evidence bindings and 1,089 protected files checked correctly. These are independent integration/informed recovery checks, not a new native compaction trial or a rescore of the original live work.

Final handoff: [FINAL-REPORT.md](FINAL-REPORT.md). All 18 critic rounds, including 11 failed rounds, remain in STATUS; every current module gate passes. Root subsequently changed only current-result documentation/status and added the handoff report. Reviewed installed skills and executable source remain unchanged. The final protected check confirmed all 46 tracked `sage-claude` files still match the original baseline, with no worktree changes there.
