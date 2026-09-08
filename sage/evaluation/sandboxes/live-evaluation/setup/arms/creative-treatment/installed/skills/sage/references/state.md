# State CLI contract

Read when creating event payloads, recovering state, or diagnosing a CLI rejection.

## Commands

```text
python3 SAGE_STATE init --run-dir RUN --run-id ID --objective TEXT --criteria CRITERIA_JSON
python3 SAGE_STATE append --run-dir RUN (--event EVENT_JSON | --events EVENTS_JSONL)
python3 SAGE_STATE validate --run-dir RUN [--terminal]
python3 SAGE_STATE snapshot --run-dir RUN --write
python3 SAGE_STATE resume --run-dir RUN --agents AGENTS_JSON
python3 SAGE_STATE report --run-dir RUN --write
```

Both paths are explicit: resolve `SAGE_STATE` as described in [run](run.md) and choose `RUN` beneath an explicit state root. Success emits one JSON object and exits 0. Contract/data rejection emits `{ok:false,code,message}` to stderr and exits 2; unexpected I/O exits 3. JSON is UTF-8, finite, and duplicate-key free. Sage-owned IDs match `^[a-z0-9][a-z0-9._-]{0,63}$`. Agent handles instead preserve the exact bounded, control-free native ID or canonical name returned by the tool; `/root/scout` is valid and must not be aliased.

Each JSONL event has exactly `v,event_id,run_id,seq,at,actor,type,payload`. Version is 1; sequence is contiguous from 1; time is RFC 3339 UTC. Required payload fields:

| Type | Fields |
| --- | --- |
| `run.opened` | `objective,criteria:[{id,text}],constraints,next_action` |
| `run.amended` | `kind,value,reason,corrects_event_id` |
| `note.recorded` | `category,text,evidence_ids,corrects_event_id` |
| `user.decision` | `request_id,question,decision,received_at` |
| `plan.revised` | `revision,reason,attempt_limit,revision_limit,no_progress,trigger_event_ids,tasks` |
| `task.admitted` | `task_id,task_revision,plan_revision` |
| `agent.requested` | `task_id,handle,requested_model,requested_effort,fork_turns` |
| `agent.observed` | `handle,lifecycle,effect_status,effective_model,effective_effort` |
| `task.result` | `task_id,task_revision,outcome,effect_status,evidence_ids` |
| `evidence.recorded` | `evidence_id,criterion_ids,kind,locator,sha256` |
| `check.recorded` | `check_id,criterion_ids,outcome,evidence_ids` |
| `finding.opened` | `finding_id,severity,summary,evidence_ids` |
| `finding.dispositioned` | `finding_id,disposition,evidence_ids,verification_check_id` |
| `knowledge.selected` | `generation_id,cue_fingerprint,cues,matches,retrieval_status` |
| `knowledge.feedback` | `id,revision,outcome,evidence_ids,missed_recognizers` |
| `checkpoint.written` | `next_action,baselines,unresolved_user_items` |
| `run.closed` | `status,criterion_evidence,scope_reconciled,remaining_human_items` |

A task has `id,revision,objective,completion,dependencies,owner,effect,scope,inputs,returns,risk,verification,requested_model,requested_effort,fork_turns`. Effects are `read`, `write`, `external`, or `unknown`. Plan reasons are `initial`, `failure`, `user_amendment`, or `evidence_change`; a failure revision also supplies `unmet_criterion,failure_evidence_ids,cause,strategy_change`. Causes are `missing_input_or_authority`, `ambiguous_brief`, `decomposition`, `capability`, `environment_or_tool`, or `candidate_defect`.

Each delegated task revision has one `agent.requested`; its native handle equals the plan owner. A delegated writer releases only when its reconciled result and that assignment's latest terminal reconciled observation coexist, in either order. Before that boundary, a newer lifecycle supersedes an earlier one: terminal then active/unknown before the result stays blocked until a fresh terminal reconciliation. After the boundary, release is historical and immutable. A released native handle may receive a new task revision through `followup_task` and a new request; later observations bind to that new assignment, so old completion cannot release it. A root writer releases from its reconciled result. Planned-but-unadmitted tasks and released historical readers do not hold the writer barrier.

Lifecycle is `active,idle,completed,failed,interrupted,missing`; effect status is `none,reconciled,unknown`. Evidence kinds are `observation,inference,unknown,untested`. Check outcomes are `passed,failed,not_tested`. Findings use `blocker,major,minor` and dispositions `fixed,accepted,rejected`.

`resume --agents` consumes a normalized array, not the raw `list_agents` envelope. Each item has `handle,lifecycle` and may include `effect_status,effective_model,effective_effort`. Map native `agent_name` exactly to `handle`, `running` to `active`, and a completed status object to `completed`; omitted effective identity becomes null. Completion text is lifecycle evidence only, never effect-reconciliation evidence, so effect remains unknown until separately observed.

An unknown task result may be reconciled once by appending a known, evidence-bearing result for the same task revision. Both remain in the log; a known result is final. A known outcome with unknown effect is rejected so accepted uncertainty always has that reconciliation path.

The helper's completion gate is deliberately structural. Every admitted task must finish with reconciled effects. `completed` also requires every current-plan task result, criterion-associated observation evidence, and a passed evidence-bearing check. `failed` or `stopped` may retain safely never-admitted tasks as visibly unfinished. Reports surface later failed checks; the helper does not infer which differently named check semantically supersedes another, judge evidence persuasiveness, prove authority, or enforce a physical lease. Invalid UTF-8 in criteria, event, live-agent, or authoritative-log input is a structured data error; invalid UTF-8 confined to `snapshot.json` is disposable and rebuilt from a valid log.

## Executable tiny run

Set `SAGE_STATE` and `RUN`, create `criteria.json` containing:

```json
[{"id":"c-1","text":"The bounded read is observed and checked."}]
```

Run `init`, then create `wave.jsonl` with these complete lines:

```jsonl
{"v":1,"event_id":"e-2","run_id":"tiny-1","seq":2,"at":"2026-09-07T00:00:02Z","actor":"root","type":"plan.revised","payload":{"revision":1,"reason":"initial","attempt_limit":1,"revision_limit":1,"no_progress":"one bounded attempt","trigger_event_ids":["e-1"],"tasks":[{"id":"read-1","revision":1,"objective":"inspect the bounded input","completion":"one observation is recorded","dependencies":[],"owner":"root","effect":"read","scope":["input.txt"],"inputs":["input.txt"],"returns":["observation"],"risk":"low","verification":"check-1","requested_model":"gpt-5.6-sol","requested_effort":"high","fork_turns":"none"}]}}
{"v":1,"event_id":"e-3","run_id":"tiny-1","seq":3,"at":"2026-09-07T00:00:03Z","actor":"root","type":"task.admitted","payload":{"task_id":"read-1","task_revision":1,"plan_revision":1}}
{"v":1,"event_id":"e-4","run_id":"tiny-1","seq":4,"at":"2026-09-07T00:00:04Z","actor":"root","type":"evidence.recorded","payload":{"evidence_id":"ev-1","criterion_ids":["c-1"],"kind":"observation","locator":"input.txt#observation","sha256":null}}
{"v":1,"event_id":"e-5","run_id":"tiny-1","seq":5,"at":"2026-09-07T00:00:05Z","actor":"root","type":"task.result","payload":{"task_id":"read-1","task_revision":1,"outcome":"passed","effect_status":"none","evidence_ids":["ev-1"]}}
{"v":1,"event_id":"e-6","run_id":"tiny-1","seq":6,"at":"2026-09-07T00:00:06Z","actor":"root","type":"check.recorded","payload":{"check_id":"check-1","criterion_ids":["c-1"],"outcome":"passed","evidence_ids":["ev-1"]}}
{"v":1,"event_id":"e-7","run_id":"tiny-1","seq":7,"at":"2026-09-07T00:00:07Z","actor":"root","type":"checkpoint.written","payload":{"next_action":"close","baselines":[],"unresolved_user_items":[]}}
{"v":1,"event_id":"e-8","run_id":"tiny-1","seq":8,"at":"2026-09-07T00:00:08Z","actor":"root","type":"run.closed","payload":{"status":"completed","criterion_evidence":{"c-1":["ev-1"]},"scope_reconciled":true,"remaining_human_items":[]}}
```

Then run `append --events wave.jsonl`, `snapshot --write`, `validate --terminal`, and `report --write`. `append` validates the entire proposed history before atomic replacement; a rejection leaves the log unchanged.
