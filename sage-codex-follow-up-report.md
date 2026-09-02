# Sage Codex follow-up implementation and parity report

Date: 2026-09-01

Run: `run-20260901-143726-f7bf7213`

Requested scope: `previous-conversation-1.md`

## Outcome

The explicitly approved changes were implemented. The Sage-Claude skill sources, custom-agent directories, previous-conversation files, and unrelated dirty-worktree bytes were not changed. No skill was installed or published, no real knowledge record was promoted, no custom-agent behavior was added, and no alternative-family adapter was implemented.

The implementation passed the repository's Phase 0 checks and all 44 Phase 1 tests in the writer's Git-backed live checkout. The final independent disposable frozen copy passed 43 of 44; its sole failure was the unchanged Pilot provenance check because that copy does not contain the original Git commit/corpus. Independent Standards and Spec/acceptance readers found and drove repairs for multi-candidate promotion, retirement compatibility, test quality, duplicated decisions, and process-crash recovery. Candidate 3's fresh-process recovery passed after every tested record/index commit boundary, and the final report review was blocker/major dry.

## Approved changes implemented

### 1. Structured handoff authority

What changed:

- `handoff.json` is now the mandatory, hash-bound recovery authority.
- It has a dedicated schema and generated TypeScript type.
- Resume rejects a missing, malformed, hash-invalid, stale, wrongly named, or wrongly typed JSON authority.
- `handoff.md` is optional and is generated or checked by `sage-light handoff-projection`; resume does not require it.
- The prior `handoff-state.json` name and dual-authority behavior were removed.

Why: the structured artifact contains the recovery state and can be validated deterministically. Independently authored Markdown duplicated state and made the less precise representation mandatory.

Primary evidence: `sage/scripts/sage-light.py`, `sage/artifacts/schemas/sage-handoff-v1.schema.json`, `sage/artifacts/generated/sage-handoff-v1.ts`, and the handoff tests in `sage/tests/test_phase1.py`.

### 2. Admission ceilings recalibrated

What changed:

- New planning artifacts no longer receive universal numeric defaults for units, attempts, concurrency, plan revisions, admission time, admitted agents, or no-progress revisions.
- Those rails begin explicitly uncommitted.
- A plan revision, worker brief, or attempt cannot be admitted until the policy actor commits finite task-specific non-spend bounds.
- The separate `estimate-multiple/baseline-v1` compatibility profile remains available only when its usage sensor is comparable.

Why: the former `4 / 2 / 3 / 3 / 6 / 3600` values were conservative but uncalibrated. Removing them avoids silently optimizing a quality-first workflow around arbitrary limits while retaining finite termination rails for every admitted run.

Primary evidence: `sage/scripts/sage-light.py`, the shared admission helpers and validation in `sage/scripts/check-phase0.py`, and `sage/policy/delegation.md`.

### 3. Root authority versus mechanical verification

What changed:

- Root explicitly owns baseline acceptance, criteria, writer leases, result adoption, finding dispositions, conflict settlement, plan revision, integration, and the completion claim.
- Substantial mutation normally uses one dedicated Writer.
- Baseline/reproduction, acceptance, Standards, Spec, and accepted-fix verification normally use independent read-only workers.
- Writer checks are feedback, not independent acceptance.
- Root directly implements only small tightly coupled work, unavailable-capability fallbacks, or work whose matching delegated retries are exhausted.

Why: policy authority and mechanical execution are different responsibilities. This keeps final judgment with root without making root a bottleneck or treating writer self-verification as independent evidence.

Primary evidence: `sage/policy/delegation.md`, `sage/policy/topologies.md`, and `sage/skills/sage/SKILL.md`.

### 4. Clean-code, testing, mocking, concurrency, and diff-review fidelity

What changed:

- Added canonical, progressively disclosed `sage/policy/implementation.md`.
- Ported the clean-code decision rules, testing and mocking rules, and code-level concurrency ownership/shutdown rules.
- Added canonical `sage/policy/software-review.md` with one frozen fixed point, separate Standards and Spec readers, root triage, reusable briefs, and all 17 review smells.
- Wired both references through the Sage skill and generated bundles.
- Replaced prose-fragile tests with structural ownership, manifest/hash, and smell-set checks.

Why: Sage is used for both implementation and review. Depending only on repository-local instructions left a real clean-code gap, while describing two review lenses without reusable fixed-point briefs left inconsistent review behavior.

Primary evidence: `sage/policy/implementation.md`, `sage/policy/software-review.md`, `sage/docs/phase0/invariant-ownership.json`, and their packaged Sage references.

### 5. Promotion selectivity and transaction safety

What changed:

- Create/revise maturity is evidence-sensitive: one independently refuted run for a deterministic invariant, at least three independent runs for an empirical heuristic, and at least six independent runs plus behavioral evaluation for shared-policy guidance.
- Create/revise requires recognizer-bound positive expected utility, explicit novelty/overlap dispositions against every active record and active batch peer, advisory independence review, and required verification evidence.
- Promotion batches are deterministic, reject duplicates, and are capped at five candidates.
- A complete batch is preflighted against one pre-batch snapshot under one lifecycle lock.
- Caught failures restore the prior record/index bytes.
- A durable, fsynced write-ahead authority enables a fresh Sage process to validate and roll forward a batch interrupted after any record/index replacement, verify the complete next generation, and durably clear the authority.
- Retirement remains a separate legacy-compatible path and does not require create/revise maturity, utility, novelty, refutation, or behavioral-evaluation fields.
- Current-run facts can record a loaded rule as useful, neutral, misleading, or missed without promoting during the active run.

Why: explicit promotion alone did not prevent low-value, overlapping, single-observation records. Batch support also needed real all-or-none behavior across validation failures, exceptions, concurrency, and fresh-process recovery—not only a numeric cap.

Primary evidence: `sage/lib/knowledge.py`, `sage/scripts/sage-promote.py`, `sage/artifacts/schemas/knowledge-record-v1.schema.json`, `sage/docs/phase0/promotion-contract.md`, and promotion tests in `sage/tests/test_phase1.py`.

Durability boundary: recovery assumes POSIX-style atomic per-file `os.replace` and honored file/directory `fsync`. Raw filesystem readers that bypass Sage's lifecycle APIs are not serialized; Sage readers and promoters recover before exposing the affected state.

### 6. Custom agents

What changed: nothing.

Why: this was explicitly approved as a no-change item. The current Codex dispatch surface cannot prove selection of a named saved-agent profile or its tool allowlist. Sage continues to express Scout, Researcher, Writer, Verifier, and Successor roles through immutable per-attempt briefs.

Preservation evidence: `claude-agents`, `claude-agents-alt`, and the other protected Claude directories are byte-identical to the captured baseline.

### 7. Alternative AI-family roadmap

What changed:

- The former loosely deferred portability note is now an explicit post-Light milestone.
- Entry requires discovery of a genuinely available alternative-family capability and runtime proof of effective family identity.
- Exit requires matched role/tool/permission/sandbox probes, typed safe failure, no unsafe retry or silent fallback, and predeclared quality/reliability parity.
- Landing or enabling an adapter still requires separate approval.

Why: alternative-family verification can materially improve independence, but an unverified alias or a requested model name is not evidence that a different family actually ran.

Primary evidence: `2026-08-31-sage-codex-proposal.md`, “Post-Light milestone: alternative-family verification.”

## Review-driven corrections

The first frozen candidate passed 37 tests, but independent review found two major batch/retirement specification defects and three minor quality defects. Candidate 2 fixed those and passed 43 tests. Independent hidden acceptance then found that exception rollback did not recover from abrupt process death. Candidate 3 added durable recovery and passed 44 tests.

| Finding | Disposition | Repair |
|---|---|---|
| `STD-BATCH-ATOMICITY` | Accepted | One preflight, one lifecycle lock, one rollback transaction for the whole batch. |
| `SPEC-BATCH-VIABILITY` | Accepted | Novelty uses one pre-batch snapshot plus explicit peer dispositions. |
| `SPEC-RETIRE-GATES` | Accepted | Create/revise-only fields and gates no longer burden retirement. |
| `STD-TEST-WORDING` | Accepted | Replaced phrase checks with structural and public-behavior checks. |
| `STD-DUP-VERIFICATION` | Accepted | Centralized passing-verification reference resolution. |
| `STD-DUP-ADMISSION` | Accepted | Centralized uncommitted-bound and admission-state decisions. |
| `F-BATCH-CRASH-PARTIAL` | Accepted | Added a durable write-ahead authority and fresh-process roll-forward recovery tested after every commit boundary. |

## Exhaustive Sage-Claude versus Sage Codex difference inventory

This inventory covers 72 permitted non-memory Sage-Claude core files, the 11 assigned auxiliary Claude skill/source records, and 44 relevant Codex support files. The count evidence and source locators are recorded in results `R-PARITY-CORE` and `R-PARITY-AUX` in `/private/tmp/sage-subagents-skill-state/runs/active/run-20260901-143726-f7bf7213/run.json`. The inventory classifies deliberate adaptations as well as remaining report-only gaps. It does not treat a different filename or packaging choice as a defect when the behavior is preserved.

| # | Difference | Status and reason | Current Codex design | Suggested change |
|---:|---|---|---|---|
| 1 | Authoritative run record | Deliberate; Codex benefits from validation and deterministic rendering. | JSON `sage.run-record` plus append-only current-run facts is authoritative; Markdown is a projection. | Keep. Do not parse Markdown back into state. |
| 2 | Handoff representation | Approved change; the Claude/historical Markdown-first shape was less precise. | Mandatory hash-bound `handoff.json`; optional generated `handoff.md`. | Keep implemented design. |
| 3 | Native worker/session mechanics | Deliberate harness adaptation. | Codex collaboration threads are opaque workers; native handles are recorded and `idle` is not equated with `completed`. | Keep semantic contract; add adapter-specific evidence only when a new surface is proven. |
| 4 | Named custom-agent profiles | Explicit no-change and current capability limit. | Roles are immutable briefs; model, effort, task, and context fork may be requested, but a saved profile/tool allowlist is not claimed. | Revisit only if Codex exposes a verifiable named-profile selector. |
| 5 | Enforceable role tool restrictions | Missing native parity follows from #4. | Briefs prohibit tools/effects as policy, but Light mode cannot prove a saved profile's allowlist enforced them. | Future capability probe; retain truthful advisory wording meanwhile. |
| 6 | Effective model-family identity | Current Codex surface reports the request, not dependable effective-family proof. | Effective model/family is recorded as unknown when unobservable; same-family residual risk is explicit. | Implement only through the approved alternative-family milestone. |
| 7 | Alternative-family verification lane | Missing today by explicit scope boundary. | No live adapter or silent fallback; a post-Light milestone now has identity, parity, safety, evaluation, and approval exits. | Roadmap item; do not enable before those exits pass. |
| 8 | Claude alternative explorer/web-agent lineup | Harness-specific and not natively selectable in current Codex. | Research uses available Codex tools and bounded briefs; independence does not claim another family. | Fold any future alternative research lane into milestone #7, not ad hoc aliases. |
| 9 | Automatic context-pressure/transcript watchdog | Capability gap. Claude-side hooks/helpers have no reliable Codex equivalent here. | A 30% policy remains, but automatic detection is unavailable without a supported numerator/denominator; explicit handover/resume and compaction recovery remain. | Add a sensor adapter only when the runtime proves both values. |
| 10 | Handover threshold configuration | Report-only gap. | The initial threshold remains `0.30`; protocol and artifact behavior are stable. | Add `handover.context_fraction` later, after a real sensor/config owner exists. |
| 11 | Light-mode writer lease enforcement | Deliberate truthful limitation. | Exactly-one-writer is policy discipline backed by briefs and snapshots, not an external lock over native collaboration. | Enforce in a future Managed driver; do not claim Light enforcement. |
| 12 | Scheduler/admission enforcement | Partial platform adaptation. | Schemas validate committed rails and counts; some elapsed/concurrency/agent enforcement remains advisory in Light mode. | Managed runtime should enforce the same semantic rails transactionally. |
| 13 | Managed protocol maturity | Deliberately provisional. | Typed protocol/schema design exists, but production Managed driver, durable scheduler, approval transactions, and enforced leases are not claimed complete. | Complete/evaluate as a separate approved phase. |
| 14 | Admission numbers and prior-run calibration | Approved change plus memory-boundary adaptation. | No universal numeric defaults; finite task-specific bounds are committed before admission. Comparable estimate-multiple behavior remains opt-in. | Gather calibration only through an explicit evaluation/promotion workflow, never active-run log mining. |
| 15 | Prior-run pricing/usage lookup | Deliberately absent during a run. | Usage stays measured/provider-reported/estimated/unknown; no token-to-cost conversion without a versioned source. | Add a versioned external price source only if required and reviewable. |
| 16 | Clean-code packaging | Structural difference, semantic gap now closed. | Clean-code/testing/mocking rules are canonical Sage references loaded on the mutation branch rather than a standalone subskill. | Keep the progressive-disclosure design; maintain semantic source attribution. |
| 17 | Concurrency packaging | Structural difference, semantic gap now closed. | Code concurrency lives in implementation policy; orchestration concurrency remains in delegation/topology policy. | Keep separation so threading rules do not blur worker scheduling. |
| 18 | Diff-review packaging and dispatch | Deliberate integration difference, semantic gap now closed. | Sage plan units run independent Standards and Spec readers against a captured Git or artifact fixed point; root triages both. | Keep. Standalone review may still use merge-base Git commands. |
| 19 | Review smell baseline | Previously missing; approved fix implemented. | All 17 smells are canonical and bundled. | Keep synchronized through generated manifests and structural tests. |
| 20 | Root versus worker verification | Previously ambiguous; approved fix implemented. | Root retains policy acts while independent workers normally perform substantial mechanical acceptance/fix verification. | Keep; add runtime enforcement only in Managed mode. |
| 21 | Claude shell helper/index/lint utilities | Deliberate implementation-language adaptation. | Codex uses structured Python commands, JSON schemas, generated types, and source manifests instead of mirroring shell helpers. | Keep unless a missing observable behavior is demonstrated. |
| 22 | Promotion destination | Deliberate safety design. | Promotion is explicit, forbidden during an active run, defaults to an installed overlay, and requires explicit `--global` source mutation; installation remains separate. | Keep. Do not let a run self-modify its active skill. |
| 23 | Promotion maturity/confidence | Approved deliberate adaptation. | Evidence classes use `1 / 3 / 6` independent-run gates, with refutation and behavioral evaluation requirements. | Recalibrate only from evaluated promotion outcomes, not intuition. |
| 24 | Novelty, utility, and batch budget | Previously missing; approved fix implemented. | Positive recognizer-bound utility, full active/peer overlap dispositions, deterministic ordering, maximum five, single-lock preflight, rollback, and crash recovery. | Keep; evaluate false-positive overlap and activation cost over closed runs. |
| 25 | Retirement and stable-ID reconciliation | Codex is equivalent or stricter. | Stable IDs, expected-prior hashes, retirement integrity, installed-overlay/source reconciliation, and index rebuilding are explicit. | Keep. Preserve retirement as easier than adding low-value knowledge. |
| 26 | Activation/usefulness feedback automation | Partially implemented, still report-only beyond recording. | Runs may record useful/neutral/misleading/missed facts, but no automatic score changes, retirement, or promotion occurs. | Later evaluate an explicit close-time analysis that proposes, never auto-applies, changes. |
| 27 | Automatic `/sage-promote` suggestion at close | Missing report-only convenience. | Promotion remains entirely user-invoked after the run closes. | Consider an opt-in close-time hint based only on validated closed state; never auto-promote. |
| 28 | Claude memory confidence/use/miss/stale machinery | Partly replaced by stricter memory classes and evidence-sensitive promotion. | Runtime reads only promoted records selected by recognizer; current-run facts and closed-run evidence stay separate. | Compare any remaining feedback semantics in a separately approved promotion audit. |
| 29 | Raw `sage-claude/memory/**` record contents | Intentionally unassessed under the active-run memory boundary. Twenty-nine files were inventoried but not read. | Codex forbids mining prior raw memories/logs during an active task. | If desired, authorize a separate closed-run/promotion audit; do not weaken this run's boundary. |
| 30 | Markdown ledger and historical memory mining | Deliberate safety difference. | Current-run facts are append-only evidence, not lessons; reusable knowledge is produced only by the separate promotion workflow. | Keep. |
| 31 | Automatic lesson consolidation/self-modification | Deliberately absent. | No active Sage run writes lessons, confidence bands, or policy into its own skill. | Keep explicit promotion and user approval. |
| 32 | Installation ownership/layout | Deliberate Codex packaging. | `sage/install.sh`, manifests, receipts, overlay state, and uninstall logic are owned by the Codex Sage source/install boundary. | Keep unless a portability phase demonstrates a semantic incompatibility. |
| 33 | Light-mode mutation breadth | Deliberate current design, broader than the earliest reader-only proposal stage. | Light mode supports bounded mutation with advisory leases, exact baselines, structured attempts, independent review, and recovery. | Keep while reporting advisory enforcement honestly; Managed remains the enforcement path. |
| 34 | Phase 1 causal pilot evidence | Validation gap, not fabricated success. | The pilot is blocked before outcomes because current Codex cannot prove one normalized hard arm budget or an external root-kill/restart oracle boundary. | Rerun when a pinned harness supplies both gates; do not relax the frozen experiment. |
| 35 | Cross-harness portability proof | Not yet performed. | Runtime protocol remains provisional and Codex-first; semantic capability fields are not evidence that another harness fits. | Execute only as the approved alternative-family/portability milestone. |
| 36 | Claude custom-agent and auxiliary source bytes | Explicit preservation boundary. | No changes were made to `sage-claude`, `claude-skills`, `claude-agents`, `claude-agents-alt`, or `.claude`. | Keep until the user approves a separately listed report-only item. |

## Verification record

| Gate | Result |
|---|---|
| Pre-mutation public suite | 34/34 passed. |
| Candidate 1 | 37/37 passed; independent review found batch and retirement defects. |
| Candidate 2 | 43/43 passed; all first-review fixes passed; hidden crash probe found partial state after abrupt death. |
| Candidate 3 writer checks | 44/44 passed; kill-after-record-1, record-2, and index boundaries recovered from a fresh process. |
| Phase 0 self-test | Passed on the final writer candidate. |
| Generated schema types | Current. |
| Generated skill bundles | Current. |
| Protected Claude/custom-agent directories | Byte-identical to baseline. |
| Optional skill-creator `quick_validate.py` | Not run: both local Python interpreters lack PyYAML. Sage's own schema, source-manifest, bundle, and behavior checks passed instead. |
| Final independent candidate-3 crash/report review | Passed: fresh-process recovery produced a complete valid next generation after all three commit boundaries; report review was blocker/major dry. |

## Scope and residual risks

- Semantic worker/refuter independence and overlap materiality remain reviewed judgments rather than mechanically provable facts.
- Light-mode one-writer and several admission controls remain policy obligations, not externally enforced scheduler capabilities.
- Effective model identity and model-family diversity were unavailable; all independence claims are same-family with disjoint briefs.
- Content-level parity for the 29 raw Sage-Claude memory files is deliberately not claimed.
- The durability claim depends on the POSIX assumptions stated in the promotion contract.
- The worktree was already dirty. Verification used an exact pre-mutation workspace copy rather than `HEAD`, so user-owned staged, modified, and untracked bytes were preserved.
