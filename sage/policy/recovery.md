# Recovery and safety policy

Policy owner: `policy.recovery`

## Failure signatures

Diagnose the first failure by stable signature: affected subject, location, error class, and cause category.

- A specification failure means scope, context, or the question was wrong. Correct the brief and use a fresh worker at the same placement; retained mistaken context is not a discount.
- A capability failure means the approach was relevant but the worker could not finish. First sharpen the current attempt where safe, then assign a more capable full owner if the required capability exists.
- A blocked unit lacks scope, authority, or a tool. Repair or reroute the plan; greater model capability cannot grant authority.
- A different second signature receives the rung its new cause earns.

Two failures with the same signature end delegated retries. Move the work to the policy actor where possible and reopen the plan, assumption, reproduction, or completion criterion. Create a new attempt rather than rewriting history, and record every abandoned disagreement.

## Safety rails

Four conditions pause admission and require policy or human disposition:

1. A destructive, irreversible, externally visible, or human-identity action lacks a release bound to that exact action.
2. More than one writer could reach the same mutable resource without an effective isolation boundary.
3. A writer requests a path or resource outside its recorded lease.
4. Actual or projected admission exceeds a declared unit, attempt, concurrency, spend, or no-progress bound.

In-flight read-only work may be harvested. Side-effecting work is quiesced or interrupted where the effective capability proves that action; otherwise mark it unknown and freeze result acceptance and resource reuse. A paused run still records current state, returns the safe partial deliverable, and names what authorization or revision is required.

Human release is a recorded decision before the action, never inferred from prior momentum or a model message. Widening a lease or adding isolation is a plan revision, not an informal exception.

## Reconciliation

After interruption or loss of the policy actor, load the authoritative current-run state and reconcile every unresolved external intent before retrying. Distinguish prepared, running, idle, completed, failed, lost, and unknown. Validate artifact and result hashes before acceptance.

Never repeat a possibly side-effecting unknown operation. Resolve it from a proven native snapshot or require human disposition. Resume deterministic scheduling only after every ambiguity is classified. At the next judgment boundary, enter `AwaitingPolicy` unless an explicitly durable policy-actor thread has also been reconciled.

An unavailable or degraded capability is state, not mere telemetry. Stop new admissions when a required predicate becomes false. Restoration does not retroactively validate work performed during the gap.

## Context handover

The default handover threshold is 30 percent of the policy actor's effective context window. A versioned host capability supplies the window and occupancy evidence. An unavailable sensor is recorded as unavailable; it does not remove the policy, invent a reading, or claim automatic enforcement. Explicit handover remains available.

At the threshold, stop launching, harvest safe in-flight work, bring the current-run artifacts up to date, and write the mandatory hash-bound `handoff.json` authority, validated by `sage/artifacts/schemas/sage-handoff-v1.schema.json`. It contains the run pointer, current plan and attempts, next action, leases, baseline, assumptions, gaps, findings, rails, and worker-handle map. An optional `handoff.md` is only a deterministic projection regenerated from that JSON; resume never depends on Markdown. A successor receives artifact pointers rather than conversation history. The original policy actor retains human-release and completion authority unless an authenticated transfer says otherwise.

Each later generation updates the same logical handoff and remains bound by the original run limits. A successor loss returns to reconciliation. A handover without a durable destination pauses and surfaces the gap.

## Stop and resume

Stopping never erases obligations. Every unit, finding, assumption, gap, approval, and lease receives an explicit state; current-run facts remain append-only; unknown side effects remain unknown. Resume fails closed when `handoff.json` is missing, malformed, hash-invalid, or stale, then verifies baseline and resource identity before any new admission. It creates revisions or attempts rather than mutating history and does not require `handoff.md`.
