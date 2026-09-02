# Follow-up questions from the previous conversation:

## Handoff notes:

- Does handover write both handoff.md and handoff-state.json? And will the successor read both, or only handoff-state.json? If handoff.md's purpose
    is only for human reader, it can be removed. A human can always ask an agent to translate handoff-state.json later.

## Current ceiling:

- Are these cap too limited?
    - 4 units: means 4 subagents at max? Why this number?
    - 2 attempts per unit: does this mean 1 more retry after a fail attempt, before delegating to another higher-level model agent?
    - 3 concurrent agents: max cap for every concurrency? Why this number?
    - 3 plan revisions: is this the revision when the initial plan is made, or everytime the plan is updated?
    - 6 total admitted agents: this sound more like subagents. Is this the cap of the subagents? Why this number?
    - 3,600 seconds of admission time: cap time to live of one subagent? Why is this number? What happens to a subagent working passed this threshold?

## Verification rules and agent ownership:

- "Before implementation - Baseline/reproduction, deterministic checks, optional blind acceptance suite or pre-write critic - Root plus optional independent worker"
    - Why root? I don't think root should do this, because root is having the sage context plus the requirement and the plan. Doing this is too much for root, similar to asking root to also do implementation.
        What about assigning subagent(s) to do this instead?
- "Implementation / Fix verification - writer/root" - when will root handle the implementation itself?

## Subskills:

- The sage-claude also have clean-code, concurrency, and diff-review subskills. Where are they in the new sage skill?

## How Sage decides what is worth promoting:

- There is no minimum run count or score. The judgement system assumes to be more accurate than the sage-claude, but still, my concern is, without the frequency, too many things would be promoted into the sage's knowledge, thus reduce the sage's efficiency. How does the sage solve this problem?

## Custom subagents:

- Currently, the sage codex doesn't use a similar custom agent format like claude. Is it the difference between the 2 harnesses, or it's just an implementation decision, and why this decision?

## Alternative AI families can be skipped now, but it should still exists in future's plan.

# Prev conversation

› Some feedbacks for the current phase 1 implementation of 2026-08-31-sage-codex-proposal.md:
    Questions (answer only, don't change anything yet):
    1. Is it the full implementation of the sage for codex - aka the "Light mode"?
    2. Quick check list:
        - Is the handover implemented, and what is the handover threshold? And how to configure it?
        - Is handoff notes implemented?
        - What is the current token ceiling? How to configure a different value? It is 4x of the estimate tokens in the sage-claude skill.
        - Summarize the sage's full flow.
        - Does the sage have the implementation - review loop to fix all the major and higher issues?
        - Does the sage take notes / logs instead of "knowledge" as the previous sage-claude? If taking logs, does the sage use the logs as memories to apply to the next sessions?
        - Does auto consolitdation trigger in the middle of a session?
        - When and how does the sage suggest `/sage-promote`? Is the suggestion logic simple?
        - What does triggering `/sage-promote` do? Summarize its full flow.
        - Does `/sage-promote` have any modes? How to use a mode, and what does each mode do?
        - How does the sage verify any of its work? List all summary of all the verification rules / patterns. And does it use the same agent or different subagents?
        - Does the sage's initial plan evolve when working, or is it fixed?
        - How does the sage know which knowledge / log item that is worth promoting?
        - What is the current skill size in token that the agent has to load before doing any work? How is it vs the claude-sage skill?
        - Does the sage have custom subagents as the claude-sage? What are they?
        - Does the sage support alt custom agents (from other AI families)?
        - Does the sage manage each subagent's work (not responding, over-work, stopping, steering, escalating to higher models and efforts, etc)?
        - What is the sage's top target: quality or efficiency (token saving)?


• I audited the proposal, current skills, policies, scripts, schemas, and tests. The Phase 1 check passes all 34 implementation tests, but the paired quality pilot has not run.

  1. Is this the full Light-mode implementation?

  Yes, in the repository’s intended sense: it implements the complete advisory Light workflow—research, review, mutation, testing, handover, logs, promotion, and lifecycle. It is broader than the proposal’s original “reader-only Phase 1”
  wording; that widening is explicitly documented in sage/docs/phase1/equivalence.md:1.

  But it is not:

  - Managed mode or deterministically enforced orchestration.
  - A production-proven implementation: the 20-task paired pilot is blocked before outcomes because Codex cannot prove the required aggregate hard token cap or root-loss driver. See sage/evaluation/phase-1/STATUS.md:1.
  - Automatically enforced handover, token admission, leases, or worker recovery. Those remain root-agent discipline in Light mode.

  So: feature-complete advisory Light mode, but not fully validated or strongly enforced.

  2. Handover

  Implemented explicitly. The policy threshold is 30% of the root/policy actor’s effective context window.

  However, automatic threshold detection is currently unavailable because Codex does not expose both occupied-context tokens and effective window through one supported sensor. Caller-supplied numbers are deliberately rejected.

  Configuration:

  - Current threshold: hard-coded 0.30.
  - There is no config file or CLI option to change it.
  - The proposal mentions a future handover.context_fraction, but it is not implemented.
  - Explicit use: sage-light handover <run-id> --reason explicit.

  3. Handoff notes

  Yes. Handover writes:

  - handoff.md: human-readable note.
  - handoff-state.json: machine-readable state containing plan revision, attempts, worker handles, results, bounds, assumptions, gaps, findings, human items, baselines, and next action.

  Resume verifies hashes, resource identity, baselines, and unresolved attempts. Drift or unknown attempts blocks admission. See sage/skills/sage/references/codex.md:61.

  4. Current token ceiling

  The important correction: ordinary Codex Light runs currently have no effective token ceiling.

  The generated default is bounded-observed with spend_limit: null, because there is no comparable aggregate spend sensor. It does have advisory non-token bounds:

  - 4 units.
  - 2 attempts per unit.
  - 3 concurrent agents.
  - 3 plan revisions.
  - 6 total admitted agents.
  - 3,600 seconds of admission time.

  The Claude-compatible estimate-multiple/baseline-v1 profile exists, but is not the Codex default:

  - Task: max(4 × estimate, 500,000 normalized tokens).
  - Unit: max(4 × estimate, 150,000 normalized tokens).
  - Agent count: max(2 × planned agents, 10).

  To choose another ceiling, the policy actor must author the run/plan artifact with a fixed, custom, or suitably bounded profile and set bounds.spend_limit plus spend_unit, then validate and commit it. There is no friendly $sage --token-
  ceiling ... option yet. The baseline 4× multiplier itself is schema-locked; use fixed or custom rather than changing that profile.

  The pilot’s 250,000-token cap per arm is separate from runtime defaults.

  5. Full Sage flow

  The normal $sage flow is:

  1. Explicit invocation only.
  2. Start structured run state and append-only facts.
  3. Selectively load promoted knowledge whose recognizer and qualifier match.
  4. Qualify and decompose; zero delegated units is valid.
  5. Optionally run a bounded read-only bootstrap to discover enough scope.
  6. Commit an immutable complete plan revision with criteria, bounds, dependencies, placement, and estimates.
  7. Brief and dispatch bounded workers with explicit model/effort.
  8. Supervise through native snapshots, waiting, steering, continuation, interruption, and reconciliation.
  9. Revise the plan or brief when evidence changes the work.
  10. For mutation: capture baseline, allow one writer, run checks, freeze the candidate, and review it independently.
  11. Triage findings, fix accepted issues, and repeat blocker/major review until dry.
  12. Verify every required criterion and completion condition.
  13. Close the structured run, render the Markdown report, and freeze the factual log.
  14. Optionally, in a later explicit action, run $sage-promote over closed logs.
  15. Implementation–review–fix loop

  Yes, as a required Light-mode policy:

  - Deterministic checks first.
  - Freeze the reviewed snapshot.
  - Separate specification and quality verdicts.
  - Disposition every finding.
  - Return accepted fixes to the sole writer.
  - Re-run affected criteria.
  - Continue blocker/major follow-up reviews until one dry round.
  - Do not close with an unresolved blocker or major contradicting completion.

  It does not blindly fix every reported major issue: findings may be rejected with evidence, deferred with an owner, or routed to the user. The loop is advisory—there is no external scheduler forcing the root to comply. See sage/policy/
  review.md:5.

  7. Logs versus knowledge

  Sage uses both, but keeps them strictly separate:

  - Current-run log: factual, append-only, usable only to coordinate or recover that run.
  - Closed-run log: not available as task-time memory.
  - Promoted knowledge: reviewed reusable rules that future runs may selectively load.

  Therefore raw logs are not memories applied directly to later sessions. They influence future sessions only after explicit $sage-promote converts suitable evidence into indexed promoted knowledge.

  This is stricter than sage-claude, which reads recent journal rows for same-shape pricing. Codex Sage deliberately forbids that. See sage/policy/memory.md:1.

  8. Mid-session automatic consolidation

  No. Consolidation is forbidden during an active run. It happens only in a later explicit promotion pass, and promotion rejects execution while any run remains active.

  Codex host compaction is separate; Sage does not control it and relies on durable state/handoff recovery.

  9. When Sage suggests $sage-promote

  It currently does not suggest it automatically.

  There is no journal-size threshold, confirmation counter, age check, or close-time hint. The sage-light close command only freezes the run.

  This differs from sage-claude, which suggests promotion after at least 25 unmarked journal payload lines or a stale model-lineup stamp. The Codex implementation has no equivalent suggestion logic, simple or otherwise.

  10. $sage-promote flow

  When explicitly invoked:

  1. Reject if any Sage run remains active.
  2. Inspect and validate all selected closed runs.
  3. Verify run JSON, facts sequence, rendered report, integrity, and terminal close fact.
  4. Group related factual observations across runs.
  5. Preserve counterevidence and disagreements.
  6. Separate reusable rules from one-run outcomes, preferences, dates, prices, model names, and local implementation details.
  7. Compare against existing promoted records.
  8. Draft one candidate per rule with stable ID, qualifier, recognizer, falsifier, provenance, action, review evidence, and expected prior hash.
  9. Refute the candidate; use an independent read-only verifier when consequential or ambiguous.
  10. Prepare the canonical representation and integrity hash.
  11. Land atomically, rebuild the index, and roll back on failure.
  12. Report destination, actions, evidence, hashes, changed paths, conflicts, quarantines, and follow-up installation when applicable.

  Unlike Claude’s promotion, this does not repair Sage’s corpus, promote rules into SKILL.md, refresh model lineups, maintain confidence bands, or run corpus self-update stages.

  11. Promotion modes

  There is no general --mode selector, but there are two destination modes:

  - Installed, default: writes only to the installation’s promoted overlay. Future local Sage runs can load it.
  - Global: --global --source-root <checkout> --expected-source-revision <sha>. Writes only to sage/knowledge in the source checkout and prints the later sage/install.sh command. It does not update the installation automatically.

  Each candidate also has an action:

  - create: new stable ID.
  - revise: replace an existing stable ID using its expected prior hash.
  - retire: retire after a fired falsifier or explicit user decision. Disuse is insufficient.

  12. Verification rules and agent ownership

   Layer                    Verification pattern                                                                                                                    Who performs it
  ━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Before implementation    Baseline/reproduction, deterministic checks, optional blind acceptance suite or pre-write critic                                        Root plus optional independent worker
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   Implementation           Focused checks, build/lint/type/tests as applicable, diff-scope check                                                                   Writer/root
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   Review                   Separate specification and quality verdicts on one frozen snapshot                                                                      Reviewer subagents different from the writer
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   High stakes              At least two independent refuters, preferably model-family-diverse                                                                      Different verifier subagents
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   Medium+ risk             Adversarial pass against the root’s fixes and completion claim                                                                          Independent verifier
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   Conflict                 Narrowest command, reproduction, or source observation; never majority vote                                                             Root adjudicates evidence
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   Fix verification         Re-run finding check and every criterion the fix could regress                                                                          Root and/or verifier
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   Review stopping          One blocker/major dry round                                                                                                             Reviewers report; root decides
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   Completion               All units terminal, criteria verified, findings dispositioned, no contradictory blocker/major, scope preserved, human gates complete    Root owns final claim
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   Run artifacts            Schema and semantic validation, immutable histories, legal transitions, append-only facts, deterministic hash-bound rendering           Local deterministic tools
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   Handover                 Hash-bound handoff, resource identity, baseline and unresolved-attempt reconciliation                                                   Local tools plus successor/root
  ───────────────────────  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────  ───────────────────────────────────────────────────────
   Promotion                Closed-run integrity, exact provenance, adopted artifacts, passing verification references, candidate refutation, canonical hash        Promotion actor plus independent verifier when needed

  Domain evidence menus add:

  - Software: build, lint, type checks, focused/full tests, bug reproductions, regression checks, performance checks, packaging/install tests.
  - Research/writing: fetch load-bearing sources, distinguish fetched material from snippets, check recency/conflicts, completeness critic.
  - Data: coverage counts, raw-record spot checks, independent figure derivation, visualization/table correspondence.

  13. Does the plan evolve?

  Yes. It is not fixed.

  Each admitted revision is immutable, but evidence can create revision N+1. Changed units get new unit-spec revisions; old ones are explicitly carried, superseded, or removed. Existing results require a recorded adoption decision under the new
  criteria.

  A bootstrap revision is revision 0 and must terminate in either a complete plan or an explicit planning gap.

  14. How Sage decides what is worth promoting

  This is judgment-based, not threshold-based. A candidate should be:

  - A reusable decision/workflow rule, not merely a result.
  - Supported by exact closed-run provenance and adopted artifacts.
  - Appropriately qualified—no broader than the evidence.
  - Loadable through an observable recognizer.
  - Falsifiable through a concrete future observation.
  - Compatible with stronger active knowledge.
  - Safely generalizable without leaking private or machine-local data.
  - Able to survive refutation and cite passing verification evidence.

  There is no minimum run count or automated promotion score. If a falsifier cannot be written, the observation remains in the closed log.

  15. Skill size

  Approximate token counts, since the repository does not contain an exact Codex tokenizer:

  - Codex Sage entrypoint: 5,014 bytes / 669 words, roughly 1.2–1.5k tokens.
  - Claude Sage entrypoint: 76,253 bytes / 12,411 words, roughly 18–20k tokens.

  So the initial Codex entrypoint is about 13–15× smaller.

  Codex uses progressive disclosure:

  - Entry plus mandatory Step 1 delegation/contracts references: about 18.4KB, roughly 4.5–5k tokens.
  - Entire ordinary runtime reference set if every branch is needed: about 48.6KB, roughly 12–14k tokens.
  - Claude’s entrypoint plus its five references is about 203KB, roughly 48–52k tokens.

  16. Custom subagents

  Not as actual saved/custom Codex agent definitions.

  Current Sage has semantic roles encoded into immutable briefs:

  - Scout.
  - Researcher.
  - Writer.
  - Verifier.
  - Successor.

  The root is the policy actor. agents/openai.yaml is skill metadata, not a custom worker profile.

  Claude Sage has actual custom agent files such as explorer, implementer, verifier, web-researcher, and orchestrator, plus some alt variants.

  17. Alternative AI-family agents

  Not currently implemented.

  The policy says to prefer model-family diversity when effectively available, but the shipped Codex mapping only names GPT-5.6 Luna/Terra/Sol. There is no external-family adapter, alt-agent package, or second harness.

  A future portability proof mentions another harness, but it is explicitly outside the current plan.

  18. Subagent management

  Yes, but advisory and root-driven:

  - Persist returned handles.
  - Inspect the fleet and reconcile lifecycle state.
  - Wait using notifications rather than polling.
  - Steer active workers.
  - Continue idle worker threads with revised briefs.
  - Interrupt workers and record the prior state.
  - Mark missing/unproven workers unknown.
  - Permit at most one mechanical repair for malformed results.
  - Stop delegated retries after two failures with the same signature.
  - Specification failure: revise the brief and use fresh context at the same placement.
  - Capability failure: sharpen once, then escalate to a more capable owner/model.
  - Blocked work: repair authority/tools/scope; model escalation cannot solve it.
  - Enforce attempt, concurrency, wall-time, no-progress, and plan-revision bounds.
  - Pause rather than blindly retry an unknown side effect.

  What is absent is an external watchdog or scheduler that guarantees these actions. Token overwork cannot presently be detected or stopped reliably.

  19. Quality or efficiency?

  Quality, safety, and correctness are the primary target. Efficiency is secondary.

  The governing rule is: choose the least costly model that can still reach the correct answer; cost never excuses an incapable placement. Token savings, context protection, and parallel wall-time are benefits only after correctness and
  verification requirements are preserved.
