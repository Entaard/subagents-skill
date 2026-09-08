# Codex Light-mode mapping

This reference maps the complete Sage workflow to native Codex collaboration. Re-probe the live callable schema at the start of a run; a missing field degrades only the capability it supplied.

## Native collaboration surface

| Portable operation | Native mapping | Evidence and fallback |
| --- | --- | --- |
| start a worker | `spawn_agent` | Record the returned agent handle and canonical task name. Reject admission if no native start tool is callable. |
| fresh worker context | `fork_turns: "none"` | Use only when that field is present. Otherwise record inherited context and revise the plan if freshness is required. |
| bounded context seed | a positive `fork_turns` value | Choose the smallest sufficient recent-turn count; use durable artifact pointers in the brief. |
| requested model/effort | `model` and `reasoning_effort` on a fresh or bounded fork | Preserve an explicit user model. If the result does not expose the effective identity, record it as `unknown`. |
| steer active work | `send_message` | It does not start an idle worker. Keep the message within the admitted brief. |
| continue an idle thread | `followup_task` | Use for one bounded repair or a newly revised brief; do not overwrite the prior attempt. |
| interrupt | `interrupt_agent` | Record the returned prior state. An interrupt signal is not proof of quiescence. |
| inspect handles | `list_agents` | Reconcile by recorded canonical task name or agent ID. A missing worker remains `unknown` unless absence is proved. |
| wait for updates | `wait_agent` | Prefer notification-aware waits measured in minutes; avoid tight polling. |

Keep baseline declaration/acceptance, writer-lease grants, criteria choice, result acceptance/adoption, finding disposition, synthesis, conflict adjudication, plan revision, human releases, and completion in the root policy-actor thread. Child reports are unprivileged claims. Codex's current start call does not select a named custom-agent profile, so encode the role contract in the brief instead of claiming a hidden profile was enforced.

## Role and placement profiles

Use the narrowest role that meets the unit's done-when criterion.

- **Scout:** map a bounded corpus, return locators and uncertainties, never synthesize beyond the brief.
- **Researcher:** answer a falsifiable question with primary evidence, counterevidence, confidence, and gaps.
- **Writer:** make the admitted mutation only, report exact files and verification, and stop at the unit boundary. It is the sole active writer.
- **Verifier:** independently test a frozen snapshot, report findings and negative evidence, and never repair what it reviews.
- **Successor:** resume only from the validated handoff and revalidated baselines; it inherits no unrecorded authority.

Resolve the live model catalog before dispatch and record requested and effective values separately.

- `gpt-5.6-luna` at low or medium effort: narrow, clear, repeatable, high-volume reads.
- `gpt-5.6-terra` at medium effort: repository exploration, bounded implementation, large-file scans, and balanced synthesis.
- `gpt-5.6-sol` at high effort: ambiguous architecture, conflict adjudication, difficult implementation, and adversarial review when the depth is justified.

These are versioned Codex profile entries, not portable tiers. A user's concrete model choice wins. If an override cannot be combined with inherited full context on the live schema, use a fresh or bounded fork or reject admission; never silently drop the request.

## Dispatch and topology mapping

Choose a topology from [the canonical topology policy](policy/topologies.md). Independent sweeps, competing hypotheses, quarantined deep reads, completeness critics, and blind behavioral lenses use parallel readers when their source and judgment boundaries are genuinely independent. Implement–review–fix, migration, bake-off, and loop-until-dry plans use explicit dependency gates.

For every admitted unit:

1. Commit its immutable plan and brief before dispatch. Include a classified, redacted objective, effect class, done-when, protected source locators and hashes, allowed resources/effects, exclusions, peer boundaries, dependencies, attempt bound, expected return fields, model/effort request, and escalation condition. Never copy a raw user prompt or raw tool payload into the artifact.
2. Call `spawn_agent` only when delegation has positive expected value and an available concurrency slot. The policy actor may work locally while independent units run.
3. Persist the returned handle immediately and append only a compact factual event to `facts.jsonl`.
4. Reconcile active and completed workers before follow-up or interruption. A malformed result receives at most one bounded mechanical repair; repeated failure returns to policy review.
5. Verify load-bearing claims from source state or an independent verifier. Settle conflict with evidence, not a vote.

## Mutation, review, and safety

In a shared workspace, the policy actor counts as a writer. Before any writer starts, prove there is no other active writer and capture the declared file/tree or revision baseline. Readers may run alongside a writer only when their allowed resources and effects cannot collide. Never ask two workers to edit the same shared checkout concurrently.

Honor repository instructions and other explicitly invoked or automatically applicable skills inside each unit. Every mutation writer reads canonical [software implementation policy](policy/implementation.md) before editing; it reads that reference's testing/mocking or implementation-concurrency branch only when the brief triggers it. For substantial changes, dispatch dedicated baseline/reproduction, writer, Standards, Spec, and fix-verification seats. Writer checks stabilize the candidate and never substitute for independent acceptance. The root implements only small tightly coupled changes, unavailable-capability cases, or work whose matching delegated failures exhausted the admitted bound, and runs only narrow settling commands when dispatch costs more.

Every software implementation review and Sage code-review run reads [software fixed-point review](policy/software-review.md). Its Standards and Spec readers inspect one frozen merge-base diff or captured baseline/hash manifest, receive the reusable briefs, return separate evidence/verdicts, and leave triage to the root.

After the writer stops, reconcile its handle, record the changed paths, validate the baseline relationship, and freeze a review snapshot. Reviewers inspect that snapshot without mutation. Accepted fixes become a new bounded writer attempt and a new review snapshot. Never let a reviewer silently repair its own findings.

Apply canonical attempt, no-progress, fan-out, cost, time, destructive-operation, secret, network, and approval rails. Native sandbox and approval behavior is inherited from the parent and must be recorded as observed; a prose brief is not isolation. When authority or a required control is absent, use the inline alternative, revise the plan, or pause with a human item.

## Handover and resume

The policy threshold is 30 percent of the effective root context window. The native collaboration surface does not itself expose a trustworthy occupied-token numerator and effective-window denominator. Unless the live root supplies both from one supported sensor, record automatic threshold detection as unavailable and use explicit handover.

Before handover, stop admissions, reconcile workers as far as the native snapshot permits, validate current-run state, capture source baselines, and write authoritative `handoff.json`. It identifies the run and plan revision, attempts and handles, result IDs, next action, assumptions, gaps, findings, rails, human items, and content-hash/resource-identity baselines. `handoff.md` is optional and generated only with `sage-light handoff-projection <run-id>`; verify it with the same command plus `--check`.

Resume requires and verifies hash-bound `handoff.json`, its current-run bindings, source baselines, and unresolved handles before any new admission. Missing, malformed, hash-invalid, or stale JSON fails resume; Markdown is never required. At the next evidence-judgment boundary, pause at `AwaitingPolicy` unless policy authority was explicitly transferred.

## Artifact and memory commands

Locate installed commands with `command -v`. With default lifecycle paths, the wrappers are under `~/.local/bin` and the Python tools are under `~/.local/share/sage/scripts`; if neither is available, use the scripts from the Sage checkout. Preserve the installed wrapper's `SAGE_STATE_ROOT` when using custom lifecycle destinations.

```text
sage-light start --objective <text> --effect-class read_only|mutating
sage-light start --objective <text> --effect-class read_only|mutating --bootstrap
sage-light append-fact --run-id <id> --type <allowed-type> --classification public|internal|confidential --payload <json-object>
sage-light fact-types
sage-light baseline <path> [<path> ...]
sage-light validate <run.json>
sage-light commit-state --run-id <id> --candidate <run.json>
sage-light report <run-id>
sage-light report <run-id> --path-only
sage-light handover <run-id> --reason explicit --baseline <path>...
sage-light handoff-projection <run-id> [--check]
sage-light resume <run-id>
sage-light knowledge list
sage-light knowledge get <stable-id>...
```

`knowledge list` exposes only stable IDs, class, qualifier, recognizer, integrity, and protected location metadata. Match those cues to the current task, then use `knowledge get` only for selected stable IDs; listing must not preload every rule. Neither command can search closed-run logs. `append-fact` accepts only allowlisted current-run factual event types, an explicit persistable classification, and JSON-object payloads. Restricted and obvious credential/raw-payload fields are rejected. Confidential facts retain only a SHA-256, protected locator, purpose, and redaction note. Lesson extraction and promotion events are also rejected. Rendering reads structured state and never parses a transcript or a prior Markdown projection.

Author state changes in a separate candidate file, then use `commit-state`; never edit live `run.json` before monotonic and semantic checks run. A native handle, brief revision, result, finding, disposition, verification, plan revision, or completion claim is not recorded until the validated candidate commits and its compact factual event is appended. Close only after completion semantics pass; closing freezes the raw log for later explicit promotion.
