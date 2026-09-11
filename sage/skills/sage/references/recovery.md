# Recovery, resume, and report

Read for `$sage resume`, `$sage report`, context loss, or unknown worker effects.

Use [runtime paths and discovery](runtime.md) to locate the requested run and pin its root. Use `--run-id ID --state-root ROOT`, or the user's explicit legacy `--run-dir`, for all recovery commands. Validate `events.jsonl`; it is authority. A valid log may regenerate a missing or stale hash-bound snapshot. An invalid log preserves existing derived files and blocks admission. Never recover from `report.md`.

On resume:

1. Read the validated snapshot, active skill spine, and only references named by the next action.
2. Recheck recorded task/artifact baselines against the workspace.
3. Call `list_agents` and reconcile every unreleased assignment. Map by returned ID or canonical name; append accepted `agent.observed` proposals before relying on them. Released assignment projections retain their terminal reconciliation; a new `agent.requested` binds future lifecycle to a new assignment.
4. Preserve an unknown-effect barrier for idle, missing, interrupted, or otherwise unreconciled effectful work. Before release, the newest lifecycle observation governs; an older terminal observation cannot override newer active/unknown evidence. A directly observed pre-creation rejection may use `agent.not_created`; absence from the inventory cannot. Establish absence or safe idempotence before retry.
5. Use `send_message` for an active turn and `followup_task` for an idle worker. Revise the plan if the recorded next action or dependency state is stale.

Normalize the current native `list_agents` response into the small `--agents` array; do not persist the host envelope. Map `agent_name` to `handle`, string `running` to `lifecycle: active`, and an object such as `{completed: ...}` to `lifecycle: completed`. Use JSON null for effective model/effort when the tool omits them. Lifecycle alone never proves an effect reconciled: omit `effect_status` (the helper treats it as unknown) or supply `reconciled` only from separate effect evidence.

```json
[{"handle":"/root/scout","lifecycle":"active","effective_model":null,"effective_effort":null}]
```

The helper’s `resume` command repairs only a derived snapshot and returns advisory observations; proposals become facts only through `append`, followed by a new snapshot. Effective model/effort absent from live output remains `unknown`.

For a report, validate the log/snapshot binding, run `report --write`, and present delivered observations separately from inference, unknowns, untested checks, open findings, next action, and human items. The report does not change run state.
