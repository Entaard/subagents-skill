# Codex Sage rebuild decisions

This is the architecture decision log. Later changes append a superseding decision; they do not silently edit the rationale for an implemented choice.

## D-001 — Codex-native product

**Decision:** Build for the live Codex collaboration surface only.

**Why:** The user wants high-quality Codex task execution now. The live tools already expose the needed agent lifecycle, and portability would introduce adapter and protocol work without improving the requested outcome.

**Consequence:** Host-neutral runtime envelopes and managed-mode guarantees are legacy inputs, not active architecture. Any future portability effort needs a new decision and evidence.

## D-002 — Two separate explicit responsibilities

**Decision:** Keep main orchestration in `skills/sage` and closed-run knowledge work in `skills/sage-promote`.

**Why:** An active task should optimize the requested deliverable, not rationalize its own observations into permanent policy. A later workflow can compare runs, solicit refutation, and preserve counterevidence.

**Consequence:** Main Sage records retrieval outcomes only. Promotion rejects active runs and cannot resume them.

## D-003 — Instruction-first, deterministic core only

**Decision:** Express planning, delegation, review, and escalation as concise agent instructions; add tiny dependency-free Python helpers only for state validation/projection and reversible knowledge generations.

**Why:** These decisions require judgment. Encoding them in thousands of lines of schema and lifecycle machinery makes the skill harder to load, maintain, and evaluate without making the judgment deterministic.

**Rejected:** Rebuild the legacy protocol/store/scheduler before testing ordinary Codex behavior.

## D-004 — Append-only facts plus one resume projection

**Decision:** Use `events.jsonl` as authority, `snapshot.json` as a validated hash-bound projection, and `report.md` as a derived view.

**Why:** It preserves history and recovery evidence with a small implementation surface. The snapshot keeps resume cheap without pretending Markdown is state.

**Consequence:** Helpers validate reference closure and transitions, while evidence quality and finding disposition remain root/critic judgments.

## D-005 — Live tool behavior outranks documentation

**Decision:** Inspect callable signatures and returned observations at execution time. Treat official docs as design evidence, not capability attestation.

**Why:** The observed tool currently permits model/effort override only with fresh or bounded history, distinguishes active messaging from idle follow-up, and may not report effective model or spend. Cached prose can drift.

**Consequence:** Requested and effective capabilities remain separate; unavailable observations are `unknown`.

## D-006 — Model choices begin as uncalibrated role priors

**Decision:** Start with Luna-high for bulk reading/search, Sol-high/xhigh for guided builds, Sol-xhigh for reviews, and Astra-high for ambiguity/adversarial criticism.

**Why:** These are useful placement hypotheses supplied for the rebuild, not benchmark results. Capability comes before cost, and full coordination cost matters.

**Rejected:** Hard-code provider prices, assert a cheapest model, or copy savings ratios from Claude harness history or research papers.

**Revisit when:** Reproducible Sage cases provide enough outcome and usage evidence to change one routing choice.

## D-007 — Adaptive orchestration, including zero agents

**Decision:** Qualify each task as inline, orchestrated, or safety-paused. Use delegation only for bounded units with positive placement or independence value.

**Why:** Agent overhead can make tiny tasks worse. Substantive work benefits from context isolation and review, but mandatory seats become ceremony.

**Consequence:** Review depth and evidence depend on risk and artifact type; zero delegation is a valid planned result.

Each runtime plan uses finite task-specific attempts, revisions, and a no-progress condition. A retry names the unmet criterion and causal hypothesis and changes the corresponding input, brief, graph, routing within user constraints, evidence strategy, or candidate. Persistence means continued bounded replanning while distinct safe strategies remain, not repeated identical dispatch.

## D-008 — One writer and evidence-independent review

**Decision:** Allow one active writer per shared workspace, counting the root. Freeze the candidate before a separate reviewer evaluates it; fixes receive targeted independent re-verification.

**Why:** This prevents shared-tree races and protects review from builder context. Agent reports remain claims until checked.

**Consequence:** Parallel writers require real isolation and a named integrator, not merely different filenames.

## D-009 — Situation-driven promoted knowledge

**Decision:** Retrieve from a compact active index using task/domain/artifact/environment/risk/failure cues, then load a bounded set by stable ID with evidence status and counterevidence. Persist exact generation/revision identity and refresh only when observable cues or the active generation change before a material decision.

**Why:** Loading all memory consumes context and applies rules outside their evidence. Searching raw closed logs mixes observation with policy.

**Consequence:** No-match and unchanged-cue refresh are normal. Loaded revisions are deduplicated, prior qualifiers/status are rechecked, current evidence and user instructions outrank knowledge, and refuted/retired items are not offered normally.

## D-010 — Promotion is refutable and reversible

**Decision:** Every material promotion action gets independent refutation and counterevidence disposition. Land a validated immutable generation by one pointer change and retain previous generations.

**Why:** Knowledge is useful only if wrong rules can be challenged, withdrawn from retrieval, corrected without identity loss, and rolled back.

**Rejected:** In-place record edits, automatic lesson extraction, deletion on disuse, and candidates that approve themselves.

Evidence gates are qualitative and class-specific: direct repeatable checks support scoped facts; controlled or varied independent corroboration is required for transferable heuristics; causal guidance must isolate its proposed cause from material alternatives. Refutation/review is necessary but cannot turn a confounded observation into supported guidance. Fixed run counts await calibration.

## D-011 — Boundary checkpoints replace a numeric context trigger

**Decision:** Checkpoint after stable workflow transitions and host warnings; do not use a fixed window percentage.

**Why:** The live collaboration surface provides no guaranteed, comparable numerator/denominator for context pressure. Boundary checkpoints are observable and also help crash recovery.

**Consequence:** Resume validates state, baselines, and agent handles before new dispatch. A valid log may regenerate a missing/stale snapshot; an invalid log pauses admission. Unknown side effects block blind retry.

## D-012 — Verification architecture precedes behavior rewrite

**Decision:** Build functional tests, sandbox integration, negative cases, rubric, held-out boundary, and comparison procedure before rewriting the active skills and helpers.

**Why:** Evaluation written after outcomes can encode the implementation’s assumptions and miss the failure modes the rebuild is intended to remove.

**Consequence:** No module may claim empirical passage from architecture prose. Design, deterministic, integration, and live gates are recorded separately.

## D-013 — Per-dimension gate with persistent failure history

**Decision:** Each module needs a separate Astra critic, every applicable dimension at least 8.5, and zero open errors. Preserve all rounds in `STATUS.json`.

**Why:** An average can hide a critical weak axis, and overwritten failures prevent the next builder from resuming the weakest point.

**Consequence:** One approach is limited to four rounds. Continued work requires a materially different documented approach based on the failure cause.

## D-014 — Brute-force is an evaluation baseline, not a product mode claim

**Decision:** Compare a small Sage-routed treatment with a predeclared high-capability-everywhere baseline on identical cases and checks.

**Why:** Routing quality must be tested against a simple expensive alternative. The comparison is reproducible even when exact money/tokens are unavailable.

**Consequence:** Missing spend fields remain unknown; agent calls and wall time are only proxies. Conclusions are limited to the observed cases.

## D-015 — Creative and game evidence is experiential

**Decision:** When a case produces a creative, UI, or game artifact, acceptance includes actual interaction plus scoped visual, usability, and performance observations.

**Why:** Compilation validates structure, not the experience requested by the user.

**Consequence:** Evaluators declare platforms, flows, viewports, inputs, and performance scope; anything outside that scope is untested.

## D-016 — Allowlisted cutover with reversible legacy quarantine

**Decision:** Update the installer/generator to copy only rebuilt package files and required helpers. Keep old material inert in place or move it intact under `archive/legacy` after consumers are updated.

**Why:** The current generator can overwrite active references from legacy manifests, and the current installer can serve the wrong generation. Destructive deletion is unnecessary.

**Consequence:** An incomplete new package fails installation rather than falling back. Sandbox install/update/uninstall proves the cutover before integration passes.

## D-017 — Two compact CLIs are the deterministic boundary

**Decision:** Freeze one event-log validator/projector CLI and one immutable-generation knowledge CLI in `docs/CONTRACTS.md`. Their JSON vocabulary covers only state, recovery, retrieval, staging, activation, and rollback invariants that deterministic code can decide.

**Why:** Later builders need exact behavior-level targets, while role quality and evidence persuasiveness remain live evaluation questions. A compact command boundary is implementable in a few hundred dependency-free lines per helper and avoids recreating the legacy protocol.

**Consequence:** Tests invoke public CLIs in sandboxes and do not import implementation internals. Unsupported lifecycle judgments remain scenario evidence, not pretended enforcement.

## D-018 — Comparisons freeze real artifacts and isolate worker routing

**Decision:** Build each paired manifest from evaluator-supplied prompt, input, check, rubric, environment, and protocol files. Both arms use the same installed Sage procedure and Astra root; only eligible worker routing differs. Accept results only with hash-bound execution, check, score, scorer, and measured-usage evidence.

**Why:** Descriptive case metadata and score-only JSON cannot establish execution or isolate a routing comparison. Exact artifact bindings allow unseen prompts without revealing them before the independent evaluator freezes the case.

**Consequence:** Null usage and money remain honest unknowns. Validation proves bindings and required evidence structure, not execution authenticity or general superiority.

## D-019 — Unknown results reconcile by append

**Decision:** Permit one later evidence-bearing `task.result` to resolve an earlier unknown result for the same task revision. The earlier result remains immutable; projection and release use the later fact.

**Why:** Recovery must preserve an uncertainty observation without making that uncertainty permanent or rewriting history. Re-admitting the task would misrepresent reconciliation as a new attempt.

**Consequence:** Known results remain final, unknown-to-unknown repetition is rejected, and an effectful task keeps the writer barrier until the appended result and any delegated terminal observation are reconciled.

## D-020 — Closure distinguishes untouched scope from completed scope

**Decision:** A failed or stopped run may close with safely never-admitted plan tasks recorded as unfinished; a completed run may not. Every admitted task must still reach a known, effect-reconciled result. Completed criterion evidence must be structurally associated with the criterion, and a passed check must cite evidence.

**Why:** Inventing a result for untouched work corrupts history, while treating omitted work as completed corrupts scope. The deterministic helper can validate associations and recorded effects, but cannot decide whether a later check semantically supersedes an earlier one.

**Consequence:** Reports show terminal outcome, unfinished planned tasks, untested evidence, failed checks, and accepted limitations. The root must disposition semantic conflicts rather than relying on the helper to infer test supersession.

## D-021 — Native handles remain opaque

**Decision:** Persist the bounded native agent ID or canonical name exactly as returned. Do not force it through the Sage-owned artifact-ID grammar or substitute a local alias.

**Why:** Current collaboration handles can contain `/`. Recovery must map stored identities back to `list_agents`; aliasing would discard the only authoritative join key.

**Consequence:** Run/task/evidence and other Sage IDs retain their narrow grammar. Native handles receive only nonempty length and control-character validation. A released handle can be assigned again through a new task-revision request, but old observations stay bound to the old assignment and cannot release the new one.

## D-022 — Release is a temporal reconciliation boundary

**Decision:** Before a delegated assignment releases, its newest lifecycle observation supersedes older observations for safety decisions. Release becomes an immutable historical fact only at the first event boundary where a known reconciled result and the then-latest terminal reconciled observation coexist.

**Why:** A terminal observation can be corrected by newer active or unknown evidence before the result arrives. Treating the first terminal lifecycle as absorbing releases effects that have never had both required facts at once; treating a fully released historical assignment as perpetually live prevents safe handle reuse.

**Consequence:** Result-first and observation-first completion both work. Terminal-then-active-before-result remains blocked until a fresh terminal reconciliation. Validation, recovery advice, dependency admission, and handle reuse consume the same replayed release fact. Invalid UTF-8 remains a structured input/log error, while invalid UTF-8 confined to a derived snapshot is discarded and rebuilt from a valid authoritative log.

## D-023 — Empty knowledge is an explicit recoverable selection

**Decision:** A missing active knowledge pointer is a valid empty store. `retrieve` returns the Sage-owned sentinel generation ID `none`, a cue fingerprint, `no_match`, and no records; Main Sage persists those same values in `knowledge.selected`.

**Why:** Empty installation state is normal. Returning JSON null would conflict with the frozen run-state event contract, while inventing a generation directory would create false history. A shared sentinel keeps retrieval and resume state directly comparable.

**Consequence:** `none` is reserved from real generation IDs. Store and run paths remain explicit. The cue fingerprint binds the normalized cues and whether non-supported records were requested, so changing retrieval policy cannot masquerade as an unchanged selection. Matched retrieval returns only a bounded selection but includes the rule, qualifier, falsifier, status, support rationale, and counterevidence needed for task-time judgment. Feedback may refine cues or wording only through a later promotion; frequency is never a truth gate and disuse is never a falsifier.

## D-024 — Promotion concurrency and independence stay honest

**Decision:** Stage, activation, and rollback use complete immutable generations plus an expected-current comparison directly before an atomic rename. Stored actor IDs preserve opaque bounded native names and must be pairwise distinct for proposer, refuter, and reviewer.

**Why:** This small deterministic boundary can reject stale conforming writers, partial generations, broken hashes, and role aliasing. It cannot create a physical lease, prove that actors behaved independently, or decide whether evidence establishes causality.

**Consequence:** Each manifest binds its staged parent. Normal activation must match that parent as well as the live expected pointer; `rollback` is the explicit path to an older generation. Retained valid generations define a monotonic per-ID lineage: an `(id, revision)` cannot be reused, and a post-rollback repair uses one plus the greatest retained revision while building on the safe active snapshot. This avoids reactivating a rejected generation merely to advance history. The independent reviewer applies the class-specific semantic gate; the promotion coordinator enforces one live writer, verifies actual role separation, decides risk, and owns landing. A material proposal change returns to its author and receives renewed refutation/review. The helper validates structure and references only. A `passed` refutation means the proposed action survived adversarial challenge; it does not assert that a challenged earlier rule remains true.

## D-025 — Receipt-bound install is a narrow copy operation

**Decision:** Install only the two active skill trees and two deterministic helpers beneath one explicit target root. Keep the lifecycle helper source-only. Record each copied source hash, installed hash, and inherited installed hash in one target-bound receipt.

**Why:** Codex needs a usable package, not the legacy policy/runtime tree. Hash-bound ownership makes updates and uninstall conservative without owning a runtime state directory or requiring a package manager.

**Consequence:** Complete-source, symlink, receipt, ownership, and destination-conflict checks finish before mutation. Update never replaces edited or unowned paths. Uninstall removes only unchanged receipt-owned files and retains edited/replaced files and unrelated directories.

## D-026 — Historical source is inert, exact, and recoverable

**Decision:** Extract the selected legacy paths exactly from baseline commit `c816a6250d0df74e6cbfa9b2a672a2fc15110deb` into `archive/legacy`, record their SHA-256 inventory, and remove those paths from the active product.

**Why:** The legacy generator and copied policy references could revive a conflicting product. Git-backed quarantine preserves auditability without serving a fallback or mixing rebuilt files into a wholesale directory copy.

**Consequence:** Active wrappers reach only the narrow lifecycle helper. The archived generator, policies, runtime, phase evaluators, scripts, tests, and original deleted promotion references remain readable but unimported and uninstalled.

## D-027 — Known non-creation is an assignment fact

**Decision:** Represent a directly observed native spawn rejection before handle creation with one evidence-bound `agent.not_created` event and one final failed/no-effect task result.

**Why:** An admitted assignment must reconcile without inventing a handle, observation, or effect. A missing inventory entry alone does not establish that native creation never occurred.

**Consequence:** The path cannot follow a genuine request, cannot pass, cannot carry unknown effects, and cannot bypass dependency, attempt, revision, or no-progress bounds. A later genuinely successful bounded revision can still satisfy the overall run through ordinary completion gates.

## D-028 — Empty report sections state only recorded absence

**Decision:** Render empty typed sections as “No entries recorded” and add directly stored unknown native identity, lifecycle, and effect fields to the unknown section. Require operators to record material task unknowns and untested experience checks as typed evidence.

**Why:** An empty typed array proves only that no entry was recorded. Arbitrary prose cannot be parsed reliably into state, while already structured unknown fields need no interpretation.

**Consequence:** Reports preserve known telemetry/effect uncertainty without pretending semantic prose parsing. Historical logs remain unchanged; regenerated views may expose limitations the old renderer hid.

## D-029 — Native result completion is versioned separately from subprocess exit

**Decision:** Keep the frozen v2 validator unchanged and add a v3 native-result command whose completion object binds native lifecycle evidence, permits null for an unobserved native exit, and stores actual subprocess exits only in command records.

**Why:** Native collaboration exposes terminal lifecycle but not an OS exit code. Reusing a verifier exit or calling an authored journal a raw transcript would fabricate evidence.

**Consequence:** V2 rejection stays replayable. Journals and normalized outer native observations have distinct evidence kinds. Historical adaptation can test the successor schema only as an informed diagnostic and cannot change old trial identity, scores, or gates.

## D-030 — Native v3 validates shape before meaning

**Decision:** Require each v3 arm and `execution` value to be an object before nested access, and require nonblank string `run_id`, `started_at`, and `finished_at` values.

**Why:** Round-1 review found that truthy values of the wrong primitive type passed and `execution: null` escaped the public CLI's structured rejection path. These are schema-boundary defects, not evidence-authenticity questions.

**Consequence:** Malformed v3 shapes return JSON with exit 2 instead of validating or raising a traceback. Timestamp syntax and ordering remain outside this minimal structural check. The v2 validator follows its unchanged path.

## Source interpretation

### Live-repairs round 3: validate the whole consumed v3 shape

Round 2's independent critic retained 20 nested-container tracebacks and 22 false accepts in one LIVE-03 group. A v3-only preflight now proves object/array, nonblank identifier/text and string-array reference types before shared semantic validation. This addresses the common cause without modifying v2 or treating type checks as evidence authentication. Synthetic public-CLI tests cover the declared surface, nullable effective identity/usage and single-character references. Round-3 implementation is performed by root as sole builder because the resumed native session rejected both prior-builder followup and fresh Sol spawn with an agent-thread limit; the retained Astra critic remains independent. This is a disclosed routing fallback, not observed Sol implementation or cost savings.

- [Official Codex subagent configuration](https://learn.chatgpt.com/docs/agent-configuration/subagents) supports designing around model, effort, inheritance, and sandbox configuration; live tool signatures remain authoritative.
- [Official Codex pricing](https://learn.chatgpt.com/docs/pricing) supports evaluating full input/cache/output pricing and modifiers when current figures are needed; no figures are frozen here.
- [FrugalGPT](https://arxiv.org/abs/2305.05176) motivates measuring routed systems against stronger baselines; its savings do not transfer to Sage.
- [Lost in the Middle](https://arxiv.org/abs/2307.03172) motivates compact pointers and explicit recovery state; it does not justify a universal percentage trigger.
- [Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798) motivates independent evidence under the studied no-feedback conditions; it does not prove universal inability to self-correct.
