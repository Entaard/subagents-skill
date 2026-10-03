# Supervision and handoff

Read for overlapping workers, long-running operations, stalls, or transfer of ownership. Use the collaboration tools actually exposed by the host; these names describe the current native surface, not a separate scheduler.

## Observe useful progress

At dispatch, name the expected artifact or milestone, allowed effects and scratch location, dependencies, and a stop/escalation condition. Keep native handles and task revisions in the run. Reserve capacity for the next dependency or independent check; fill slots only with useful ready work.

While workers run, perform independent root work. Consume results as they arrive and unblock only consumers whose evidence is checked. When there is nothing useful to do, use `wait_agent` or the host's event wait, with a bounded timeout compatible with user-update obligations. Timeout means no event arrived; it does not prove a stall. Reconcile with `list_agents` at handoff, unexpected silence, or a lifecycle change, rather than repeatedly polling an unchanged roster.

For a long external command, prefer its process/session observation tool. A read-only watcher is worthwhile only when it can observe a named decision-changing signal (for example CI completion or a failing service check) while the root works elsewhere. Give it bounded scope, evidence to return, and a stop condition; charge it against available slots. A watcher has no authority to mutate, retry, cancel, or declare the task complete. Do not infer token use, context occupancy, or model identity from elapsed time.

## Diagnose before replacing

If progress is uncertain, request a concise checkpoint: completed artifact, current operation, last new evidence, blocker, outstanding effects, and next action. `send_message` steers an active turn; `followup_task` starts an idle worker's next assignment. An idle worker without the promised result is unfinished, not successful.

Use the evidence to distinguish a slow useful operation, blocked dependency, missing authority, wrong brief, tool failure, or capability gap. Fix the diagnosed cause before spending another attempt. Interrupt only when cancellation is warranted and allowed by the host/user; interruption is not proof of rollback or a released writer. If no safe distinct strategy remains within the run's limits, checkpoint the impasse honestly.

## Transfer through artifacts

Before a writer or measuring reviewer starts, establish a stable baseline or isolated copy. Readers inspecting a mutable candidate do not produce a frozen review. Stop shared source mutation while its reviewer measures it; isolated writers return diffs against named baselines for one integrator.

For handoff or context pressure, persist a packet with objective/current criteria, task/revision, exact input/output locators and hashes, decisions and rejected alternatives that still matter, checks actually run, unresolved findings/effects, and the next falsifiable action. Keep large evidence in artifacts, not copied transcripts. The successor reopens the packet and checks its load-bearing locators before work.

Ownership transfers only after the previous assignment's effects are reconciled under the [state contract](state.md). A missing, interrupted, or idle handle never authorizes a second shared writer. Follow [recovery](recovery.md) for unknown effects; retain the barrier while their status is unresolved. The root checks the successor's result before claiming the handoff succeeded.
