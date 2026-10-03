# Sage Codex modernization plan

Date: 2026-10-03. Baseline: `1a2aa6714daeac3b1e324681ebec938ca49eac1c`.

## Outcome and scope

Make Sage better at delivering the user's intended result through effective teams, decisive verification, recoverable execution, and evidence-backed improvement. Quality is an observed outcome, not a guarantee inferred from model strength or reviewer agreement. Include both `$sage` and `$sage-promote`.

Change only the Codex package under `sage/`. Preserve `sage-claude/`, `claude-skills/`, `claude-agents/`, `.claude/`, `output-styles/`, `CLAUDE.md`, and the shared root installer/uninstaller byte-for-byte. A pre-edit SHA-256 manifest covers those paths. Leave real installed skills, user runtime history, Git staging, commits, and pushes untouched.

Implement only major-or-higher improvements and medium-or-higher bugs. Here **major improvement** means a material change to outcome correctness, independent error detection, or reliable team execution across substantive tasks. **Medium bug** means a reproducible failure of an advertised workflow or a plausible false completion/data-integrity result; cosmetic issues and speculative framework expansion are excluded. Existing state finding enums remain unchanged; these are audit priorities.

## What the comparison establishes

Claude Sage is a six-stage orchestration workflow: frame, plan, brief, execute, verify/integrate, record. Its active corpus combines Markdown guidance, saved role agents, shell ledger/lint helpers, optional Claude-specific monitoring/hooks, an optional Codex cross-family review lane, and a separate promotion workflow. The useful additions are explicit testing of the user's purpose and premises, a critic before consequential implementation, frozen review rounds with disjoint mandates, and an adversary directed at the parent's own fixes and completion claim.

Codex already has stronger deterministic state machinery: append-only run facts, bound artifact/check freshness, effect reconciliation, bounded retry/plan revision, compact recovery views, installed/source separation, and immutable reviewed knowledge generations. Keep these. Most Claude mechanisms do not need transplantation.

Do not port Claude's transcript watcher, hook names, fixed context thresholds, model-cost bands, automatic escalation ladder, same-model prohibition, or user-only cancellation rule. Its watcher measures occupancy; it does not prove worker health. Do not adopt a test rule that every acceptance test must fail the baseline, or that one negative experiment disproves a defect. Native tools and the task's evidence decide behavior.

Current local evidence: Codex CLI `0.160.0`; the session exposes native spawn/message/follow-up/list/wait/interrupt tools and newer Luna/Sol IDs. Baseline offline gate: **136 tests, zero failures/errors/skips**. Current official guidance supports focused delegation, inherited models, concise instructions, and conditional loading:

- [Codex subagents](https://developers.openai.com/codex/multi-agent)
- [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)

The live host schema takes precedence over examples in either source. No new fixed model catalog or claim of improved model quality/cost will be inferred from documentation.

## Accepted work packages

| ID | Priority | Change and rationale | Acceptance evidence |
| --- | --- | --- | --- |
| I1 | Major improvement | Add purpose/premise framing and a pre-write critic for consequential ambiguity, broad coupling, weak oracles, or irreversible effects. The critic attacks whether passing the criteria would actually satisfy the request. Tiny obvious work stays inline. | Independent scenario with technically passing criteria that omit the stated purpose; corrected criteria before writing, without mandatory user approval. |
| I2 | Major improvement | Add native supervision and artifact-based handoff: verified inputs, scoped scratch, observable milestones, event-driven waits, diagnosis before steering/replacement, and release only after reconciled effects. Keep one writer per shared tree and freeze measuring/review inputs. | Scenarios covering a slow active reader, idle unfinished worker, unknown writer effects, context handoff, and capacity pressure. No timer-only cancellation or fabricated usage. |
| I3 | Major improvement | Require distinct compliance/quality review and a targeted adversary against risky changes, root-authored repairs, and the final completion claim. Bind findings to criteria and exact candidate evidence, honor review caps, and run the artifact through its real delivery boundary. | Independent final review plus fault-oriented tests; an installed-skill forward test exercises decisions rather than checking prose substrings. |
| I4 | Major improvement | Make promotion test the decision consequence of changed guidance and challenge source/runtime divergence. Keep author/refuter/reviewer separation, exact patch review, narrow transfer scope, and separate landing/recovery outcomes. | Source-only and knowledge-only scenarios, empty history, first activation/rollback, and changed-guidance forward tests. No live-source mutation during review. |
| B1 | Medium bug | Replace unavailable hard-coded dispatch IDs and permanent model/effort ladders with exact live capability discovery and role-based routing. Preserve the existing GPT-5.6 generation floor and Sol-class coding floor; inherit an established eligible parent by default. Missing effective telemetry remains unknown, not a reason to invent identity. | Current tool-schema check and routing scenario with retired IDs absent. Explicit user constraints still win; unavailable requested models are surfaced. |
| B2 | Medium bug | Prevent empty run inventory from prematurely skipping the default source assessment in promotion. `no_sources` is a knowledge-source observation; it is not proof that the source package needs no change. | Empty-history source assessment scenario distinguishes inspected/no-change, pending/unavailable, and a defect supported by a fresh repeatable source check. |
| B3 | Medium bug | Reject cyclic task plans before append; preserve existing authoritative bytes on rejection. | Two-node and longer cycles, valid diamond, out-of-order task declarations, public CLI rejection. |
| B4 | Medium bug | Invalidate downstream task results when their dependency revisions change. Require an explicit downstream revision/re-execution through the transitive dependency graph; preserve historical records and finite attempt limits. | A1→B1→C1 passes, A changes; stale B/C cannot certify completion. Fresh downstream work passes. Independent branches remain reusable. Historical log compatibility is checked explicitly. |
| B5 | Medium bug | Allow rollback of the first activated knowledge generation to the empty active state `none`, retaining all immutable history and stale-pointer/integrity checks. | First activation/empty rollback, stale expected pointer rejection, retained lineage after rollback, normal rollback unchanged. |
| B6 | Medium bug | Restore exact package preimages after caught installation/update I/O failure so retry does not reject partially written package files as user edits. Protect the old receipt, retired files, user files, and runtime data. | Fault injection on package write, retirement, receipt write, and fresh install; original bytes/modes restored and retry succeeds. Rollback failure is reported with recovery evidence. Abrupt process death remains explicitly non-atomic. |
| B7 | Medium bug | Keep interrupted knowledge-pointer writes in the recognized staging namespace. A killed activation currently leaves a top-level temporary file that makes the whole store invalid. | Inject interruption before pointer replacement; prior pointer and history remain valid, residue is isolated, and a later reviewed activation succeeds without adopting residue. |
| B8 | Medium bug | Apply the same store-layout validation to staging/activation/rollback as to `validate`. Mutations currently succeed in stores that their validator rejects. | Unexpected top-level files and unsafe paths reject every mutation without changing pointer, history, or unrecognized bytes; recognized interrupted staging remains usable. |

## Implementation boundaries

1. Root owns skill/reference edits, plan/report, integration, and completion. Code builders work in isolated temporary copies and return exact diffs with checks. No simultaneous mutations of the shared source tree.
2. Extend existing seams; no daemon, scheduler, new watcher script, universal model benchmark, or wholesale rewrite of the state engine. Conditional guidance stays in the existing references unless a distinct loading branch warrants a file.
3. State changes must preserve old valid logs and closed-run promotion. If dependency freshness requires stronger semantics than v1, opt new runs into a versioned policy and document legacy behavior; never silently rewrite old logs or reinterpret successful historical runs as new evidence.
4. The installer fix handles caught I/O failures, not arbitrary crash transactions. Retain conservative ownership checks; recovery cannot overwrite unrelated user edits. Do not claim filesystem atomicity or physical leases.
5. Preserve invocation policies and existing user authorization. No new ceremonial confirmation, paid external trials, production installation, or Claude edits.
6. With no eligible history, source-only corrections may use direct repeatable current-source/host evidence recorded in the coordinator and portable review note. Label the absence of historical provenance. The active coordinator is never a terminal source run, and runtime knowledge still requires valid closed-run provenance; do not fabricate history or relax its evidence gates.

## Review and verification budget

Use **at most three formal rounds total**, each with review and adversarial scrutiny. The initial read-only audits provide inputs, not an unbounded fix loop.

1. **Plan review:** auditors challenge completeness, benefit/severity, backward compatibility, failure cases, and unnecessary complexity. Root records accepted/rejected changes before implementation.
2. **Implementation review:** independent reviewers inspect the frozen final diff against this scope, with separate behavioral and adversarial mandates. Execute meaningful regressions and installed-package scenarios. Root dispositions every finding and repairs only qualifying issues.
3. **Final repair review, if needed:** check the changed artifact, affected regressions, and final integration. No fourth round. Any unresolved major issue or medium bug is reported honestly; review exhaustion is not completion evidence.

Verification includes focused public-CLI/fault-injection tests, the complete offline gate, both skill validators, isolated install/update/uninstall checks, link reachability, and an unchanged protected-corpus manifest. Instruction tests use blind scenario outcomes; exact wording assertions are not evidence of good agent decisions. Report actual tests and remaining limitations without extrapolating a universal quality or cost guarantee.

## Review decisions and execution record

Round 1 passed with bounded corrections from three auditors:

- Source-only evidence must not become fabricated historical knowledge provenance; accepted as boundary 6 and reflected in the source-note format.
- Enable dependency/cycle enforcement through immutable `run.opened.dependency_policy: revision-bound-v1` on new runs. Absent policy keeps historical replay semantics, explicitly exposed in projections. A dependency revision change requires a new admitted consumer revision, transitively; no new event family or history migration.
- Installer recovery restores only still-matching transaction outputs or untouched preimages. Divergent concurrent edits survive, with recovery evidence retained.
- Empty rollback removes only the active pointer and preserves lineage. Pointer-crash tests cover both sides of replacement. Strict regular-file legacy pointer residue is inert; arbitrary/symlinked paths remain invalid.

No extra improvement package was admitted. Implementation uses three isolated code builders and one root documentation/integration writer. Round 2 will assess the frozen assembled result.

Round 2: independent lifecycle/knowledge review and state/knowledge adversarial review passed, including public-CLI failure probes and a real baseline-to-candidate install/update. The installed-skill forward test found a medium B1 gap: inherited root model metadata may be unavailable, so insisting on exact configured identity blocks even a tiny authorized task. Accepted repair: preserve host/user root selection, record inherited requests and unknown compliance honestly, and require missing verification only when the user explicitly made it a prerequisite. The model defaults still govern choices Sage controls. Round 3 will repeat the actual installed task and challenge this authority/telemetry boundary; no code changed for this repair.

Round 3 passed: an independent adversary checked hidden/configured/effective identity, explicit verified-coding constraints, unavailable models, and observed conflicts. The installed task then delivered and independently checked the requested TSV, closed its run completed, and passed root terminal validation with identity unknowns preserved. All work packages are delivered; the final gate has 161 passing tests, both skills validate, and the protected 171-file corpus is unchanged. See the [implementation report](2026-10-03-modernization-report.md) for exact results and limits. The three-round budget is closed.
