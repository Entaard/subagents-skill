---
name: sage
description: Explicitly orchestrate a bounded Sage Light run in Codex, including research, implementation, review, migration, testing, recovery, durable evidence, and handover.
---

# Sage for Codex — Light mode

Use this skill only when the user explicitly invokes `$sage`. Light mode is the complete advisory Sage workflow on Codex: it may coordinate read-only or mutating work, but it must not claim Managed-mode enforcement that the live Codex surface cannot prove.

For `$sage report <run-id>`, validate and render that run through the artifact command. For `$sage resume <run-id>`, read [recovery policy](references/policy/recovery.md), then follow [the Codex resume mapping](references/codex.md#handover-and-resume). For a new task, run this six-step spine.

1. **Qualify and decompose.** Read [delegation policy](references/policy/delegation.md) and [artifact meanings](references/policy/contracts.md). List the promoted index, match only observable recognizers and qualifiers, then fetch only the matching stable IDs and record which were loaded. Keep tightly coupled judgment in the policy actor. Zero delegated units is valid. A bootstrap revision may discover scope, but must end in a complete plan or an explicit gap before effectful work.
2. **Commit a plan revision.** Choose the smallest fitting pattern from [topologies](references/policy/topologies.md). Planning fields may remain explicitly uncommitted, but before admission commit finite task-specific unit, attempt, concurrency, revision, admission-time, agent, and no-progress bounds. Record immutable unit revisions, dependencies, falsifiable criteria, effect class, requested capabilities, estimates, and the inline alternative.
3. **Brief and dispatch.** Read [the Codex mapping](references/codex.md). Mutation writers also read [software implementation policy](references/policy/implementation.md); its testing/mocking and concurrency branches load only when their observable triggers apply. Give every admitted worker a bounded role contract and explicit model/effort. Use fresh context only when the live tool schema proves it. Append a current-run dispatch fact after the handle is known.
4. **Supervise and revise.** Reconcile native handles, harvest safe results, enforce attempt and no-progress bounds, and create a new plan or brief revision when evidence changes the work. Apply [recovery policy](references/policy/recovery.md) to failures, ambiguity, mutation risk, and unavailable controls.
5. **Verify and integrate.** Read [review policy](references/policy/review.md). Every software implementation review also reads [software fixed-point review](references/policy/software-review.md) and runs its separate Standards and Spec briefs against one frozen candidate. Treat reports as claims, settle conflicts with the narrowest evidence, disposition every finding, and verify every required criterion. The root owns synthesis, adoption, and completion.
6. **Close and render.** Apply the [memory boundary](references/policy/memory.md): read only indexed promoted knowledge and this run's state, while appending only current-run facts. Validate the structured artifact, render its Markdown projection, and return the deliverable plus run ID, artifact paths, effective-capability summary, material gaps, and human items.

## Required operating rules

- Continue end to end after explicit invocation without presenting the internal plan for approval. Resolve ordinary ambiguity through recorded assumptions and pause only when a safety rail, missing authority, or genuinely user-only decision requires it.
- Admit only work whose required capabilities are present. Record requested and effective capabilities separately; `unknown` never means satisfied.
- For shared-workspace mutation, there is exactly one active writer, counting the policy actor. Readers and reviewers must not edit. Capture a baseline before mutation, freeze the review snapshot, and verify the final state after accepted fixes.
- For substantial mutation, use a dedicated writer and independent baseline/reproduction, acceptance, and fix-verification workers. Writer feedback checks do not count as independent acceptance. Root mutation is reserved for small tightly coupled edits, unavailable matching capability, or exhausted matching delegated failures; root settling commands stay narrow.
- Use immutable plan, brief, attempt, result, decision, finding, disposition, and verification records. Never rewrite an admitted revision or terminal attempt to make history look cleaner.
- Keep raw observations factual and local to the run. Do not extract lessons, consolidate knowledge, edit Sage policy, or auto-promote during a run. Only an explicit later `$sage-promote` may turn closed-run evidence into reusable knowledge.
- Classify and redact before persistence. Keep confidential content behind a protected locator plus hash, and never place credentials, privileged capabilities, raw prompts, or raw tool payloads in run state or facts.
- Respect attempt, no-progress, fan-out, cost, time, and mutation rails. Pause for required human authority instead of treating a worker report as approval.
- Hand over explicitly when requested. Trigger the 30-percent context rule automatically only when one supported sensor supplies both occupied tokens and the effective window.
- After using indexed knowledge, append whether each loaded stable ID was useful, neutral, or misleading, plus any recognizer that should have loaded but did not. These are current-run activation facts for later explicit promotion.
- Keep ordinary progress concise. The final response leads with the requested deliverable and one compact run line plus material assumptions, gaps, capability limits, and human items; print the complete record only for explicit report requests.

Read [Light-mode guarantees](references/guarantees.md) before claiming that a control, sensor, isolation property, or recovery guarantee was enforced. Use the commands in [the Codex mapping](references/codex.md#artifact-and-memory-commands); transcripts and rendered Markdown are never authoritative state.
