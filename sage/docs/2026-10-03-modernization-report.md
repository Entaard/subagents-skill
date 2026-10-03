# Sage Codex modernization report

Scope: Codex package only, based on `1a2aa6714daeac3b1e324681ebec938ca49eac1c`. See the [detailed plan and review decisions](2026-10-03-modernization-plan.md). This report records the pre-publication implementation handoff, when changes were unstaged and uncommitted and real installations/runtime history had not been modified. The user subsequently authorized publishing to `main` and updating their Codex installation.

Later user amendment: routing is now restricted to the exact [model allowlist](../skills/sage/references/delegation.md#model-eligibility). This supersedes the minimum-generation and unknown-configured-root defaults discussed below; effort selection remains adaptive. The original three-round review and hash receipts describe the preceding modernization candidate. The follow-up changes routing instructions and its example, not helper behavior or historical logs; both skill validators and whitespace checks pass.

## Core mechanism after the changes

Sage defines observable success around the user's purpose, checks the premises, and gives bounded work to the smallest useful team. Native supervision and artifact handoffs keep workers coordinated. Independent review, targeted adversarial checks, and observed delivery checks challenge the result. Append-only records, current artifact/dependency bindings, and reconciled effects support honest completion and recovery. Separately invoked promotion turns qualified evidence into reviewed runtime knowledge or verified source changes.

These mechanisms improve error detection and recoverability. They cannot guarantee semantic quality for every task, prove that an agent's evidence is truthful, or turn reviewer agreement into experimental evidence.

## What Claude has, and what transferred

| Active Claude mechanism | Codex comparison and decision |
| --- | --- |
| ASK/PURPOSE/PREMISES framing and a critic before consequential writing (`sage-claude/references/decompose.md`, `topologies.md`) | Added purpose/premise framing and a risk-triggered critic. Retained inline handling for obvious small work. |
| Scoped saved roles, snapshot/lease/freeze protocol, artifact briefs (`dispatch.md`, `execute.md`) | Retained Codex's stronger typed effect reconciliation; added concrete supervision, scratch/tool boundaries, capacity decisions, and handoff packets. |
| Disjoint review, executable acceptance, adversarial scrutiny of parent fixes (`verify.md`) | Added a distinct attack mandate for consequential repairs and completion, with current evidence bindings and a real delivery check. One reviewer can still return both compliance and quality verdicts. |
| Shell ledger/lint and compaction hooks | Retained Codex's append-only JSONL, validated projections, current artifact checks, and native lifecycle observations. No Claude hook or ledger port. |
| `sage-watch.sh` and advisory clock | The watcher is an occupancy sensor, not an autonomous repair scheduler. Added event-driven native observation and optional narrowly scoped watchers; no transcript parser, timer-based cancellation, or invented token telemetry. |
| Promotion reproduces defects, audits changed capabilities, and replaces conflicting rule homes (`claude-skills/sage-promote/`) | Added a bounded source-capability/obsolescence pass, preserved qualifiers during simplification, and tested changed decision consequences. Retained Codex's stronger evidence classes, three distinct actors, immutable generations, and separate source/runtime recovery. |

The audit also rejected nonportable Claude policies: fixed model prices/windows, fixed handoff timers, an automatic escalation ladder, same-model review bans, blanket extra approvals, requiring every preservation test to fail the baseline, and treating one negative experiment as proof that a defect does not exist.

## Major improvements delivered

1. **Purpose-level planning (I1).** The team tests whether its criteria actually serve the user's intended use before consequential implementation. Evidence and uncertainty are explicit, and a framing critic challenges costly assumptions.
2. **Native supervision and handoff (I2).** Workers receive observable milestones, scoped artifacts and scratch, and bounded escalation conditions. Waits, messages, idle follow-ups, watcher roles, and ownership transfers follow actual lifecycle/effect evidence.
3. **Adversarial verification (I3).** Consequential repairs and the root's completion claim receive a specific disconfirming check. Tests reach triggering behavior and the installed/exported delivery boundary, with user review caps preserved.
4. **Evidence-driven source maintenance (I4).** Promotion checks current capabilities and conflicting guidance, including on an empty history. Source-only evidence stays separate from historical knowledge provenance; changed instructions get independent decision scenarios.

## Bugs repaired

| ID | Severity | Old failure | Result |
| --- | --- | --- | --- |
| B1 | Medium | Retired dispatch IDs and fixed role/effort priors; unavailable inherited root metadata could stop a simple authorized task. | Select from live capabilities, honor host/user root selection, record unknown identity/eligibility honestly, and enforce explicit verification prerequisites only when actually required. |
| B2 | Medium | Empty closed-run history could end default promotion before source inspection. | Knowledge reports `no_sources`; source independently reports a reviewed patch, evidenced no-change, or pending access. No fabricated closed-run provenance. |
| B3 | Medium | Cyclic dependency graphs validated but could never admit their tasks. | New runs reject cycles before append, preserving existing bytes. |
| B4 | Medium | A changed producer could retain old successful downstream tests/reviews and complete. | New runs require affected admitted consumers to advance revisions and rerun transitively; unrelated branches remain reusable. |
| B5 | Medium | The first knowledge activation could not roll back to an empty active store. | `rollback --generation-id none` removes only the pointer and preserves all retained revision history. |
| B6 | Medium | Caught installation failures left partial files that failed ownership checks on retry. | Restore exact package/receipt preimages and modes when still matching; preserve concurrent edits and report retained recovery evidence when restoration cannot finish. Source/installed receipt hashes use the same captured bytes. |
| B7 | Medium | Interrupted pointer publication left scratch that made the entire knowledge store invalid. | New pointer scratch is isolated; narrowly recognized older regular-file residue remains inert. Recovery inspects the live pointer. |
| B8 | Medium | Stage/activate could mutate a store rejected by `validate`. | All store mutations apply the same layout/history validation before mutation. Unsafe or unknown paths reject unchanged. |

## Compatibility and limits

New runs opt into immutable `dependency_policy: revision-bound-v1`. Historical logs without that policy keep their original replay semantics and are labeled `legacy`; they are not rewritten or retroactively certified. Old unbound-check semantics remain unchanged. The root still checks real artifact freshness and truthfulness.

Existing knowledge schemas and immutable generation bytes are unchanged. Runtime stores remain outside installer ownership. Pointer checks and writer ownership are cooperative, not physical locks. Installer recovery covers caught failures; abrupt process death/power loss and arbitrary concurrent filesystem races are not a multi-file transaction guarantee.

Model IDs and defaults come from the live host, not a permanent catalog. The review used local Codex CLI `0.160.0`, the exposed collaboration schema, [current Codex subagent guidance](https://developers.openai.com/codex/multi-agent), and [current skill-authoring guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra). No model-quality, cost-saving, or cross-platform performance claim was inferred from those sources.

## Verification and bounded review

- Baseline offline gate: 136 tests passed. Final code gate: **161 tests passed, zero failures/errors/skips**. Twenty-five new regression methods include public-CLI checks and real process-death/fault injection.
- New dependency tests failed the original helper (13 failing subcases and two errors); the knowledge recovery tests exposed 16 failing original-helper subcases; the initial eight installer regressions failed the original implementation. Candidate tests pass.
- Both official skill validators pass. All installed Markdown file links resolve, including the newly required supervision reference.
- Independent implementation reviewer: 66 scoped tests, a 36-case before/after installation failure matrix, and actual baseline install → candidate update → installed helper validation/empty rollback/reactivation passed. Retained generation bytes were identical.
- Independent adversary: 57 scoped tests, 50 public-command probes across ten unsafe store layouts, and direct stale-consumer completion rejection passed.
- A SHA-256 inventory of **171 protected Claude-related files** found zero changes or additions, including both shared root lifecycle scripts.
- Round 1 reviewed and sharpened the plan. Round 2 reviewed the frozen implementation and exposed B1's missing-root-metadata instruction failure through an installed-skill trial. Round 3 passed the corrected installed behavior and final adversarial boundary check. Exactly three formal rounds were used; no qualifying finding remains open.
- Five independent decision scenarios covered purpose/criteria mismatch, unknown writer effects, empty-history source correction, unavailable source checkout, and absent effective model telemetry. The expected boundaries held. These were simulated decisions, not actual source promotions or worker replacements.
- The final installed `$sage` trial delivered a UTF-8 TSV with `A=12`, `B=7`, control total `19`, and exclusion of the paid `5`. Independent readback passed; its discoverable run closed `completed`, and the root separately validated the terminal log. Requested routing remained `inherit`; unobserved identity and eligibility stayed unknown. Artifact SHA-256: `eaf032fb93cfed678d3022367acc2b3fdac2033c7de536fb0d6417051814cb13`. Final event-log SHA-256: `0678ab784f88ac40d6d6e43cb9d14a5b085d26f6b1655ae9e1a145315b14fcc2`.

The offline harness does not run live comparative model trials. Independent scenario observations are scoped evidence, not a universal benchmark. Native Excel import and a complete live three-actor promotion were not exercised. The [verification receipt](reviews/2026-10-03-modernization-verification.json) binds these results to product hashes and records local evidence locators.

Reproduce the full deterministic gate from the repository root with `python3 sage/evaluation/run_verification.py --mode red`. The focused regressions are `sage/tests/test_dependency_policy.py`, `test_knowledge_recovery.py`, and `test_lifecycle_recovery.py`. They use disposable fixtures and do not touch real installations or runtime history.
