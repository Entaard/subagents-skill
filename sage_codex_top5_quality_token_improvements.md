# Sage for Codex: top five quality and token-efficiency improvements

**Repository:** `Entaard/subagents-skill`  
**Reviewed revision:** `b10bab2921e15463dff87649a35213716fa4598a`  
**Audit date:** 11 September 2026  
**Products:** `sage` and `sage-promote` under `sage/`  
**Companion:** [Current major issues and fixes](sage_codex_major_issues.md)

## Recommendation

Keep the small Codex architecture. Improve the amount of useful, verified work obtained from each model invocation rather than replacing it with Claude's much larger orchestration corpus or prescribing a cheaper model everywhere.

The current Codex package already endorses proportional delegation, fresh or bounded worker context, independent verification, cause-responsive retries, and selective knowledge loading. The highest-value next step is to make those principles easier to execute, cheaper to record, and empirically testable. These are **ranked engineering priorities, not measured performance rankings**. No percentage saving or universal quality improvement is established by this audit. [Codex spine][sage-spine] [Delegation][delegation] [Requirements][requirements]

| Rank | Improvement | Quality mechanism | Token-efficiency mechanism |
| --- | --- | --- | --- |
| 1 | Compact coordinator state and low-ceremony event authoring | Preserve the exact obligations and uncertainty needed for the next decision. | Stop repeatedly returning historical state and hand-authoring envelope metadata. |
| 2 | Evidence-grounded work packets and measured routing/reuse | Give each worker authoritative inputs, a narrow falsifiable objective, and the right review context. | Reduce rediscovery, redundant briefing, unnecessary forks, and avoidable retries. |
| 3 | Artifact-bound, risk-adaptive verification | Test the real requirement, separate compliance from quality, and recheck what fixes can invalidate. | Replace repeated broad model reviews with decisive checks and targeted independent follow-up. |
| 4 | Budgeted knowledge cards with exact revalidation | Make applicability, support limits, and invalidations visible at the decision point. | Use a payload budget, delta refresh, deduplication, and selective evidence drill-down. |
| 5 | Measured learning loop and coherent promotion batches | Promote lessons that survive counterexamples and forward evaluation. | Amortize promotion work and optimize total tokens per accepted result instead of isolated worker price. |

## Scope and evidence standard

This is a source-based design review of the active Codex paths and selected Claude/evaluation material, not an exhaustive line-by-line inspection of every historical file in the repository. The precise coverage and limitations are recorded in the companion report. No repository test suite, live Codex trial, or token benchmark was executed here.

The Claude implementation is used to identify mechanisms worth testing, not to import its measurements as Codex facts. Likewise, the repository's historical high-usage report predates the rebuilt package. It motivates attention to accumulated context and long autonomous loops, but cannot establish the rebuilt package's current cost distribution. [Historical usage investigation][historical-usage] [Rebuild handoff][handoff]

Fix the companion report's M1-M4 before treating the relevant amendment, persistence, knowledge-refresh, and interrupted-promotion paths as reliable foundations. The improvements below should retain the existing separation between execution and explicit promotion, immutable history, truthful unknowns, user overrides, and reconciled effects. [Requirements][requirements]

**All new commands, fields, and schemas below are proposed interfaces. They are not claims about commands already implemented in the repository.**

---

## 1. Compact coordinator state and low-ceremony event authoring

### Why this is first

The coordinator participates in planning, briefing, triage, integration, checkpointing and completion. Unnecessary text returned to that coordinator can influence many later decisions and model calls, not just the command that produced it.

The current `append` command already returns a small receipt. In contrast, `snapshot --write` returns the full projected snapshot, including accumulating evidence, checks, decisions and other history. Workflow references require checkpoints at numerous legitimate boundaries. Repeatedly returning the full projection creates avoidable output and context pressure even when the coordinator only needs to know that the checkpoint succeeded. [State helper][state] [Run procedure][run] [Recovery procedure][recovery]

This is not a claim that every run must create a large log: the architecture already permits lightweight inline work. It is a claim about the default interaction shape once a persisted run is in use.

### Areas reached

Both skills' coordinator loops; event authoring; checkpoints; recovery after compaction; reporting; task/evidence lookup; and the root's ability to notice unresolved requirements instead of rereading administrative history.

### Detailed implementation

**A. Separate durable storage from model-visible output.** Keep the full authoritative JSONL log and full validated snapshot on disk. Add an explicit compact-output option, such as `snapshot --write --summary`, returning the run ID, last sequence, event digest, snapshot locator and pending-decision count. Update the installed workflow to request that option. Preserve the existing v1 default output for consumers and tests that parse the full projection; a receipt-by-default interface requires an explicit versioned migration, not a silent behavior change.

A proposed receipt could look like this:

```json
{
  "ok": true,
  "run_id": "run-17",
  "last_seq": 142,
  "events_sha256": "<actual digest>",
  "snapshot": "<explicit run directory>/snapshot.json",
  "pending_decisions": 2
}
```

This output is not a replacement for validating or writing the full snapshot. It changes what is returned to the model, not what is retained for recovery.

**B. Add a next-decision view.** A proposed `context --view next` operation should derive only the current objective and acceptance-contract revision, active constraints/user decisions, current plan and ownership, ready dependencies, unresolved effects, open major findings, knowledge invalidations, and the next action. Large evidence bodies remain at integrity-bound locators.

Provide targeted views such as `--task`, `--criterion`, `--finding`, or `--since-seq`. If relevant open state exceeds the output budget, report the omitted count and a continuation mechanism; never silently hide a blocker or drop part of an enumeration. A compact view must be sufficient to locate the missing facts, not pretend they do not exist.

**C. Let the helper generate mechanical envelope fields.** Add an authoring interface that accepts event type and payload while the helper supplies the version, run ID, next sequence, unique event ID and actual timestamp. Support a batch of payloads and return the assigned IDs. Continue running the same full validator before committing the batch.

Do not generate semantic facts automatically. A native handle must still come from an observation; a check outcome must still come from evidence; a user authorization must not be synthesized from convenience. This feature removes JSON bookkeeping, not the root's decision responsibility.

**D. Make recovery selective, not amnesic.** Reconstruct the complete snapshot from the log when required, but return a bounded recovery packet plus pointers to the exact evidence needed for outstanding decisions. Preserve criterion revisions, approach history, unresolved side effects and the cumulative knowledge-use inventory introduced by M1-M3. A summary that drops those facts would save tokens by breaking recovery.

**E. Keep the implementation small.** Implement these operations as projections and thin authoring helpers around the existing validator, not as a scheduler or an autonomous state machine. Centralize event-envelope generation and view rendering. Avoid adding a second competing state format.

### Why results should improve

Less irrelevant history competes with current constraints and failures. Mechanical IDs and sequencing become less error-prone, so fewer model calls are spent repairing event-shape mistakes. A focused next-decision packet also makes it harder to mistake an old passing check or a historical plan for the current obligation.

The Claude protocol's separation between detailed artifacts and short returns is useful here, but copying its full ledger prose is unnecessary. Codex already has the stronger basis for deterministic views: structured events. [Claude dispatch][claude-dispatch] [Codex state contract][contracts]

### How to establish the token benefit

Create synthetic persisted runs with progressively more **resolved historical** events but the same small unresolved working set. Measure full-snapshot output size, compact receipt size and next-decision-view size separately. Then measure model-visible input/output in actual paired workflows.

If each checkpoint adds a roughly constant amount of history and every checkpoint reprints all prior history, cumulative emitted history grows roughly quadratically in checkpoint count. That is a model of output growth, **not** a claim about billed tokens, cache behavior, or measured savings. The compact design should keep receipts nearly constant and working views proportional to relevant open state.

### Acceptance tests and guardrails

A compact-output checkpoint must produce exactly the same persisted state as the full-output path. Resume must identify every unresolved writer, current requirement and open major finding. Missing or malformed authoritative logs must still fail closed. Tests should prove that pagination is explicit and that a slim view cannot accidentally report completion while hiding unfinished scope.

**Main files:** `sage_state.py`, main `run.md`, `state.md`, `recovery.md`, and promotion's coordinator instructions; corresponding state and recovery tests.

---

## 2. Evidence-grounded work packets and measured routing/reuse

### Why this is second

The cheapest worker is not necessarily the cheapest way to obtain an accepted result. A weak brief can cause rediscovery, wrong assumptions, repeated root intervention and expensive verification even when the worker itself uses fewer tokens.

Codex already says to price total coordination cost and use fresh/bounded context where appropriate. Claude makes several operational details more explicit: a brief names the ground truth, an unverified reader claim remains a lead, artifacts replace transcript handoffs, and complete enumerations are not cut down merely to satisfy a summary budget. Borrow those mechanisms, not Claude-specific ratios or model-tier assumptions. [Codex delegation][delegation] [Claude decomposition][claude-decompose] [Claude dispatch][claude-dispatch]

### Areas reached

Planning, reconnaissance, model/effort selection, worker startup, context inheritance, result adoption, repair loops, reviewer independence and root synthesis.

### Detailed implementation

**A. Build a bounded evidence map once.** Before dispatch, assemble the authoritative request, criterion IDs/revisions, relevant files/symbols, actual baseline hashes, known commands, and outstanding unknowns. A scout may help locate this material, but the root must verify load-bearing structural claims before treating them as ground truth.

The map is not a repository dump. Large searches and complete enumerations belong in artifacts with counts and locators. The coordinator receives the important conclusions and access to the full result. In a tiny task, a few direct reads can be cheaper than creating the map through a new agent.

**B. Compile role-specific work packets from that map.** Give an implementation worker its objective, allowed effects, dependencies, exact source inputs, completion condition, verification instructions, and return contract. Give a reviewer the frozen artifact, original request, criteria and relevant standards, but not the builder's persuasive rationale.

A proposed packet shape is:

```text
Task and revision:
Objective / done when:
Acceptance criteria and versions:
Authoritative inputs and verified locators:
Baseline / artifact digest:
Allowed effects and workspace:
Known decisions relevant to this role:
Unknowns this task must resolve:
Requested model/effort and observable limitations:
Required evidence and return shape:
Stop/escalation condition:
```

For a blind acceptance-test author, omit implementation decisions and expose their required observable consequences instead. This is an information-separation policy, not a claim of enforced sandbox secrecy unless the runtime actually provides that enforcement.

**C. Standardize bounded returns.** Require status, conclusion, evidence locators, changed-file list, actual checks, uncertainty, and the recommended next action. Put detailed logs on disk. A proposed default conclusion budget can be tested locally, but a complete list of findings or migration targets must not be silently truncated: return counts, per-item identifiers and the full artifact location.

Treat returned code, documents and worker prose as untrusted data. A worker's recommendation does not gain authority to widen scope, run unrelated commands, change the root's model, or waive a required check. Claude's verifier makes this boundary unusually explicit. [Verifier agent][claude-verifier]

**D. Reuse the right context, not every context.** Continue with the original implementer for a focused repair when its state is still relevant. A verifier can handle a narrow post-fix recheck when it remains independent of the author and the mandate is unchanged. Use a fresh reviewer when the design changed materially, its previous context has become misleading, or a final adversarial judgment would otherwise inherit the argument it should challenge.

Follow the live lifecycle semantics: active steering and waking an idle worker are different operations. Do not use an old terminal observation to release new work. A fresh/bounded fork is also not literally free of system, tool or repository context. [Delegation][delegation] [State contract][contracts]

**E. Route using task shape and measured accepted outcomes.** Store task-shape descriptors such as corpus size, ambiguity, dependency coupling, novelty, verification strength and expected interaction count. Compare observed total tokens and repair rates for similar shapes before changing routing defaults.

Keep the current Luna/Sol/Astra placements as uncalibrated priors until measurements justify an update. Preserve explicit user model/effort choices. Unknown effective identity remains unknown, even if the requested model was recorded. Do not add imaginary enforcement controls to `agents/openai.yaml`; use only capabilities exposed by the current runtime.

### Why results should improve

Workers spend more of their reasoning on the actual problem instead of rebuilding the task map. Independent reviewers receive the information needed to falsify the work without inheriting the author's framing. Cohesive ownership reduces the mistakes caused by handing sequential fragments of one deliverable through many agents.

### How to establish the token benefit

Compare existing briefs with work packets on the same frozen tasks. Record total root and worker tokens, repeated file reads, briefing corrections, rejected outputs and repair tokens. A lower worker token count is not a win if root synthesis or verification becomes more expensive.

For reuse, compare a focused follow-up with a fresh re-brief while holding the artifact and mandate fixed. Retain fresh review where reuse measurably reduces independence or misses regressions; the goal is lower total cost at a maintained quality floor.

### Acceptance tests and guardrails

A packet must resolve every cited input, preserve current criteria and allowed effects, and never invent effective model identity. Test a poisoned worker report, stale baseline, large complete enumeration, and an explicit user routing restriction. Verify that the coordinator rejects authority-changing text and that artifact counts survive distillation.

**Main files:** `delegation.md`, `run.md`, a small set of role-packet templates, state metadata only where needed, and new paired briefing/routing cases under `evaluation/`.

---

## 3. Artifact-bound, risk-adaptive verification

### Why this is third

Better quality does not require repeatedly asking another model to review the entire artifact. It requires the right evidence for the requirement, an independent lens where judgment is necessary, and a reliable way to know which earlier conclusions a fix invalidated.

Codex already requires independent review for substantive/risky work and focused verification after fixes. Claude adds useful operational detail: compliance and quality are separate verdicts, deterministic checks run first, review lenses should be disjoint, and a final pass should challenge the coordinator's own fixes and completion claim. [Codex verification][verification] [Claude verification][claude-verify]

### Areas reached

Acceptance criteria, executable checks, research/source verification, creative and interactive work, independent review, finding disposition, final integration and completion reporting.

### Detailed implementation

**A. Bind every required check to a claim and artifact version.** Extend the evidence model with stable check identities and explicit attempts, the criterion version assessed, the relevant artifact digest or baseline, and whether the check is required for closure. Retain old attempts but distinguish current valid evidence from superseded or stale evidence.

Do not define a naive rule such as "the latest check mentioning a criterion wins." Several independent checks may be required for the same criterion. Define required check obligations explicitly, including how a newer attempt supersedes an older attempt of the same check.

This improves a documented boundary rather than pretending the existing validator already has semantic supersession. The helper can validate these relationships; it still cannot prove that a test is a good oracle or a citation actually supports a claim. [Contracts][contracts]

**B. Run the cheapest decisive checks before paid review.** For code, this often means a focused reproduction, relevant tests and the actual install/package path where applicable. For research, it means checking source support, dates and contradictory evidence before a broad prose review. For a visual or interactive artifact, exercise the behavior the criterion names; compilation alone is not evidence of usability or interaction quality. [R-018 and R-034][requirements]

A successful command is an observation, not automatic permission to mark every criterion passed. The root still maps observed outcomes to the acceptance contract.

**C. Separate compliance and quality without mandating two agents everywhere.** A single independent reviewer may return two explicit verdicts for medium-risk work. Use distinct lenses for high-risk or cross-system work when they examine genuinely different failure modes. Do not duplicate the same broad prompt merely to obtain agreement.

Predeclare the review mandate, allowed outcomes and evidence requirement. "No findings" is valid. Ambiguity or an unexecuted check must remain visible rather than being converted into a confident pass. On tasks where a blind acceptance suite has clear value, keep the test author separate from the implementation rationale and bind the suite to the frozen requirement, not to incidental implementation choices.

**D. Make fix verification impact-aware.** Record which files, interfaces, claims or dependencies each fix touches. Invalidate affected checks and criterion evidence, then run focused verification. When the impact cannot be bounded reliably, widen the verification scope rather than assuming unaffected status.

After integration, run the compose/integration check appropriate to the deliverable. Point the final adversarial pass at the final artifact, the fixes and the completion claim, not only at the original candidate. The review must use the new freeze. An old "no findings" result cannot certify a changed artifact.

**E. Bound review by information gain and user limits.** Start with the planned review and fix verification. Additional rounds require a changed artifact, new evidence, or a distinct unresolved risk. Deduplicate against rejected as well as accepted findings so the same disproved allegation does not keep returning.

When the user caps review rounds, honor that cap. If a major issue remains, report an incomplete outcome or invoke the explicitly authorized, finite continuation procedure; do not silently redefine a new round to evade the limit. Correcting M2 is a prerequisite for a sound continuation policy.

### Why results should improve

This directly targets the common gap between "the code or prose looks plausible" and "the user's actual requirement was demonstrated." It also prevents a repair from inheriting a pass that belonged to the pre-fix artifact. Separate review axes improve coverage without requiring a ritual team on every task.

### How to establish the token benefit

Use cases with a deterministic failure, a semantic/specification failure, a misleading but passing test, a post-fix regression, and an installer-only failure. Compare broad repeated review with the staged procedure. Count review and repair tokens together; track real defect detection, false-positive repairs and remaining major issues.

A narrower review is beneficial only if it preserves the required detection rate. When a test or dependency map cannot support a narrow scope, the cost of the wider check is justified.

### Acceptance tests and guardrails

Show that a changed criterion or artifact invalidates the correct evidence, while unrelated valid evidence can remain current. A fixed finding must reference verification of the repair, not any historical passing check. Test final-integration failure, accepted major findings, and untested subjective criteria. None may become completed solely because the event log is structurally valid.

**Main files:** `verification.md`, `state.md`, relevant fields/projections in `sage_state.py`, and focused verification/evaluation fixtures. Preserve the helper's explicit semantic limitations.

---

## 4. Budgeted knowledge cards with exact revalidation

### Why this is fourth

The current retrieval path already has valuable safeguards: immutable active generations, deterministic matching, explicit status, bounded match count, and no automatic mining of closed runs. However, limiting the **number** of records is not the same as limiting model-visible payload. The returned fields include potentially substantial counterevidence and other prose. The helper also returns a fresh bounded list rather than the exact revalidation operation identified in M3. [Retrieval implementation][knowledge] [Retrieval instructions][knowledge-main]

There is another useful design improvement: `gate_evidence` is retained in records but is not among the fields emitted by `command_retrieve`. For scoped facts, the declared check environment can be important context. Rather than assuming every author repeats it perfectly in a different field, make the usable card's applicability and support limits self-contained. This is an improvement to information completeness, not a claim that every current record is applied outside its scope.

### Areas reached

Planning, retry decisions, resumed runs, knowledge applicability, evidence drill-down, cache invalidation, feedback quality, and the quality of future promotion candidates.

### Detailed implementation

**A. Define a compact, self-contained decision card.** Include ID/revision, active generation and record digest, status, rule, machine-readable qualifier, supported scope, important exceptions, falsifier, concise evidence strength, and the strongest material counterevidence. Keep full provenance and source details at validated locators.

A useful distinction is:

```text
Applicability: conditions under which this rule may be used.
Observed support: environments/artifacts in which evidence was obtained.
Transfer limits: what has not been established beyond those observations.
```

For a scoped fact, do not silently imply transfer beyond the demonstrated scope. For a transferable heuristic, do not mistake one observed test environment for the complete intended qualifier. For causal guidance, expose the conditions under which the causal claim was actually isolated. These distinctions preserve the existing evidence-class model. [R-041, R-042 and R-049][requirements]

**B. Enforce a payload budget as well as a result count.** Add an output budget and deterministic selection policy. Initially a byte budget is easier to make reproducible than pretending an approximate tokenizer is an exact native billing meter. Record actual observed tokens separately when available.

Do not meet the budget by cutting a qualifier, contradiction or warning off the end of a record. Store a reviewed concise card and select fewer complete cards when necessary. Report withheld candidates and provide targeted drill-down. A long proof belongs behind a locator; a condition necessary to avoid misusing the rule belongs in the card.

**C. Return recommendation deltas and prior-record revalidation together.** Implement M3's explicit diagnostic channel. Accept the previous selection/use inventory and current observed cues. Return changed applicability/status for those exact records independently of top-N ranking, plus any newly recommended cards.

Use a versioned comparison token binding the validated active manifest, normalized cues, retrieval policy, card/normalizer version, result and payload budgets, and the prior-record inventory. Only when those inputs match a verified prior result may the operation return a short unchanged receipt. Otherwise recompute selection and revalidation, while avoiding resending record bodies whose digest and applicability remain unchanged. A refuted/retired result is an invalidation, not a usable recommendation.

**D. Improve matching only where measured misses justify it.** Start with controlled cue aliases, better candidate descriptions and diversity-aware selection so several near-duplicate rules do not consume the whole budget. Preserve deterministic behavior and explain why each card was selected.

The current `qualifier.all` semantics use an intersection within each populated category. Do not silently reinterpret old records as a different Boolean language. If real cases need conjunctions within a category, add a versioned representation with explicit `all_of`, `any_of` and exclusions, plus migration tests. Embedding search or a new retrieval service should come later, only if a simpler implementation cannot meet measured recall needs.

**E. Record application, not just loading.** Link applied rules to the actual decision or task they influenced. Distinguish loaded-but-unused, useful, misleading, and invalidated knowledge. Preserve missed recognizers without treating selection frequency as evidence of truth.

Do not retire a correct record merely because it was rarely selected. Claude's memory workflow explicitly recognizes that reported use is an imperfect instrument; Codex's own policy already rejects usage frequency as a truth test. [Claude memory][claude-memory] [Codex retrieval][knowledge-main]

### Why results should improve

The coordinator receives the conditions and counterevidence needed to make a responsible decision, not just a confident-looking rule. Negative promotion results can invalidate earlier assumptions. Better separation between a useful index cue, applicability and proof strength should also produce more informative feedback for `sage-promote`.

### How to establish the token benefit

Build cases with no matches, redundant matches, a long evidence trail, scoped facts, ambiguous cues, changed status and rollback. Measure card payload and all follow-up retrievals together. A tiny first response that forces several expensive follow-up calls is not necessarily better than one sufficient card.

Measure internal disk/hash work separately. The current helper reads and validates the active generation internally; that I/O is not automatically LLM token consumption. Do not weaken integrity validation to claim a token saving that came only from reducing Python-side work.

### Acceptance tests and guardrails

Verify exact qualifier preservation, complete invalidation reporting, payload budgeting without silent truncation, and explicit handling of omitted candidates. Change the policy, budget, card version and prior-record inventory independently while holding generation and cues fixed; none may reuse an incompatible unchanged receipt. Unknown environment cues must not be invented to force a match. A malicious instruction embedded in a rule or evidence artifact must not become authority to execute commands or change scope.

**Main files:** `sage_knowledge.py`, both knowledge references, the cumulative knowledge-use projection in `sage_state.py`, and retrieval/feedback tests.

---

## 5. Measured learning loop and coherent promotion batches

### Why this is fifth

The previous four changes need a way to tell whether they actually improved accepted outcomes at lower total cost. Promotion also needs to learn from reliable evidence without paying for a fresh miniature research project for every small record.

The repository already separates design, offline tests and live evidence. Its paired procedure holds the installed Sage workflow and Astra root fixed and varies worker routing. That is useful for routing comparisons, but it does not by itself isolate the total overhead of Sage versus direct Codex execution. The final handoff explicitly leaves generalized cost savings unestablished. [Evaluation guide][evaluation] [Handoff][handoff]

### Areas reached

Whole-run accounting, routing calibration, regression evaluation, promotion candidate selection, author/refuter/reviewer briefs, evidence-class decisions, generation staging and future knowledge quality.

### Detailed implementation

**A. Capture an observed usage vector, not a guessed price.** Where the runtime exposes trustworthy data, retain per-request or per-task input, cached input, output, reasoning accounting as defined by that source, wall time, model identity and call count. Bind measurements to the run/task/artifact version and preserve the telemetry source.

Prevent double counting across parent and child aggregates. Do not add reasoning tokens twice when the source already includes them in output. Distinguish exact measurements, estimates, partial lower bounds and unknowns. Missing usage is not zero. Do not infer subscription quota percentages or current prices from token totals alone.

Use existing telemetry or a small source-specific parser when available; do not build a speculative hard token meter. User model choices and unknown effective identity remain binding limitations. [R-005, R-023 and R-027][requirements]

**B. Add a workflow-overhead comparison alongside the existing routing pair.** Preserve the frozen original cases, results and protocol. For new evaluation cases, compare direct Codex execution with Sage under matched requests, inputs, initial artifacts, permitted tools and declared quality criteria. Separately compare Sage routing configurations while keeping the rest of the workflow fixed.

Include small tasks, ambiguous multi-file work, an evidence-heavy research task, a fix-induced regression, knowledge invalidation, and interrupted promotion. These cases test different ways efficiency can fail. Score final artifacts blindly where feasible, with correctness and major-error absence taking precedence over attractive prose or a low token count.

Evaluate the four proposed changes individually before combining them. A combined win does not identify which component helped; a combined loss can hide an excellent component behind an unrelated regression.

**C. Optimize tokens per accepted outcome, with failures included.** A useful aggregate is total observed tokens spent on the evaluated attempts divided by the number of tasks meeting the predeclared acceptance standard. Include failed attempts, repair, root synthesis, review and promotion overhead where it belongs. Report the underlying task-level outcomes and distributions as well; one aggregate can hide a severe failure on an important task class.

If usage coverage is incomplete, present a partial measurement or refrain from a total-token conclusion. Do not compare a fully observed arm with a partially observed arm as though their totals were equivalent. Keep latency, tool count, token volume and monetary cost separate.

**D. Build a reusable, bounded evidence catalog for promotion.** At explicit `$sage-promote` invocation, deterministically validate and index the selected closed sources once. Give the author the relevant observations, useful/misleading knowledge feedback, unresolved contradictions and evidence locators, rather than repeatedly loading whole logs into every actor.

Pre-screen exact duplicates and already-landed unchanged candidates without calling them new knowledge. Do not use that screen to exclude inconvenient counterevidence. A genuine no-change result remains valid and should keep the current zero-team path, with the coordinator's own required run record. [Promotion spine][promote-spine] [Promotion reference][promotion]

**E. Review coherent candidate batches while preserving all three roles.** Extend the current single-record proposal interface with a versioned batch form only when multiple candidates share a coherent evidence base. Keep a distinct live author, refuter and reviewer, with the coordinator separate from all three. Reuse one bounded team for the batch rather than minting nominally independent role names or removing a required seat to save tokens.

Each candidate needs its own stable ID/revision, action, relevant source bindings, evidence-class gate, counterexamples and dispositions. Do not force unrelated sources into every candidate's provenance merely because they were selected in the same invocation. Bind all verdicts to exact record digests and the frozen batch manifest. The refuter should challenge boundary cases and alternative causes, not just formatting.

Prefer all-or-nothing landing for a coherent batch initially. If a material candidate changes, renew the affected independent judgments and the final batch-level consistency check before landing. An unchanged earlier verdict must not certify a different final record. Stage one complete generation and activate one pointer after validation, retaining the previous generation and lineage. Fix M4's staging namespace first.

**F. Use forward evidence to improve rules, not to manufacture confidence.** Test an operational heuristic on a new task where its recognizer and qualifier actually apply. Look for the predicted decision improvement and for boundary failures. Repeated correlated runs are not independent corroboration, and a cheaper result caused by a different brief is not proof that a different model caused the saving.

Do not copy Claude's fixed confirmation-count thresholds into Codex. Retain Codex's qualitative scoped-fact, transfer and causal gates. A lesson can remain provisional while useful, and a contradicted one must not become supported because it was frequently selected. [R-045 through R-049][requirements] [Claude promotion][claude-promote]

### Why results should improve

This closes the loop between real outcomes, retrieval feedback and future policy. It rewards knowledge that makes a subsequent task more correct or easier to verify, not knowledge that merely sounds wise. Coherent batching amortizes repeated source qualification and role setup without giving up counterexample search or role separation.

### How to establish the token benefit

Report promotion tokens separately, then amortize them over a declared observation window of subsequent applicable tasks. Do not claim a positive return merely because a candidate was promoted. Compare the total cost of learning and applying the rule with the observed benefit on held-out or clearly labeled forward cases.

Batching's reduced filesystem copying is an I/O benefit, not automatically a token benefit. Measure whether shared evidence packets and reduced repeated briefing actually decrease model usage. Large heterogeneous batches can worsen both quality and cost; split them when cross-candidate context is not useful.

### Acceptance tests and guardrails

Retain original frozen results unchanged. Test duplicate telemetry and incomplete usage; verify that failed attempts contribute to the cost numerator while only accepted tasks contribute to the denominator. With zero accepted tasks, report the failure and an undefined tokens-per-accepted-outcome ratio rather than dividing by zero or implying efficiency. Also test mislabeled historical adaptations, candidate digest changes, conflicting rules, stale pointers and partial staging. Keep no-change invocation cheap and preserve strict closed-source qualification and effect reconciliation.

Add a bootstrap rollback design test as part of future lifecycle hardening: the current CLI requires a real target generation, so reverting the first activation to the original absent-pointer state is not the same operation as ordinary generation-to-generation rollback. Define any new empty-state representation explicitly; never classify a malformed or dangling pointer as an empty store. This is additional design work, not one of the companion report's retained major findings. [Knowledge helper][knowledge] [Knowledge regressions][knowledge-tests]

**Main files:** new evaluation cases/runner alongside existing `pairing.py`, minimal observed-usage metadata, `sage-promote` instructions, proposal schema/staging support in `sage_knowledge.py`, and promotion/evaluation tests. Do not mutate frozen v2/v3 historical outcomes to manufacture improvement.

---

## Implementation sequence and release gates

Establish the baseline measurements **before** changing the workflow. Implement the companion report's correctness fixes, then start with compact coordinator output and artifact-bound verification. Introduce work packets and routing/reuse experiments next, followed by knowledge-card/delta retrieval and coherent promotion batching. The measurement layer should accompany every step rather than arrive only at the end.

Each change should pass four distinct gates: focused deterministic regressions; the existing full offline verification gate; a frozen review of the assembled instructions and helper contracts; and the relevant live, task-level comparison. These are different forms of evidence. A passing JSON validator is not proof of better output quality; a lower token total is not proof of maintained correctness.

Keep rollout reversible. Version changed event, qualifier, proposal and pointer representations; retain read support or provide an explicit migration for existing state. Do not add experimental configuration fields to native tool calls unless the live schema exposes them.

## What not to do

Do not optimize by silently lowering the user's chosen model, cutting counterevidence, dropping required checks, skipping promotion's independent roles, or erasing failed attempts from accounting. Do not copy Claude's whole corpus, fixed confidence-count thresholds or historical cost ratios. Do not turn main Sage into an automatic memory curator. And do not equate a small-looking final answer with an inexpensive run: the relevant cost includes the whole route to the accepted result.

The intended outcome is a smaller **working context**, a more explicit **acceptance/evidence contract**, and a measured **learning loop**. The full audit trail and the ability to challenge a conclusion must remain intact.

## Review record

This report and its companion received two bounded review passes followed by one adversarial self-review, restricted to materially correct major-or-higher review corrections. No independent reviewer agent, live quality experiment or token-saving benchmark was run in this audit. The proposed benefits remain testable hypotheses until those experiments are performed.

[sage-spine]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage/SKILL.md
[promote-spine]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage-promote/SKILL.md
[requirements]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/docs/REQUIREMENTS.md
[contracts]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/docs/CONTRACTS.md
[state]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/scripts/sage_state.py
[knowledge]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/scripts/sage_knowledge.py
[knowledge-tests]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/tests/test_knowledge.py
[run]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage/references/run.md
[delegation]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage/references/delegation.md
[verification]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage/references/verification.md
[recovery]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage/references/recovery.md
[knowledge-main]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage/references/knowledge.md
[promotion]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/skills/sage-promote/references/promotion.md
[evaluation]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/evaluation/README.md
[handoff]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage/docs/FINAL-REPORT.md
[historical-usage]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/codex-massive-usage.md
[claude-decompose]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage-claude/references/decompose.md
[claude-dispatch]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage-claude/references/dispatch.md
[claude-verify]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage-claude/references/verify.md
[claude-verifier]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/claude-agents/verifier.md
[claude-memory]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/sage-claude/references/memory.md
[claude-promote]: https://github.com/Entaard/subagents-skill/blob/b10bab2921e15463dff87649a35213716fa4598a/claude-skills/sage-promote/SKILL.md
