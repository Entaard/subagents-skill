"""Focused regressions beyond the frozen public state contract."""
from __future__ import annotations

import copy
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation" / "tests"))
from support import STATE_CLI, complete_read_run, dump, event, invoke, opened, output, task, write_log  # noqa: E402


class StateRegressionTests(unittest.TestCase):
    def root(self, name: str) -> Path:
        sandbox_root = Path(os.environ["SAGE_EVALUATION_SANDBOX"]).resolve()
        base = sandbox_root / "state-regressions" / name
        base.mkdir(parents=True, exist_ok=True)
        return base

    def plan(self, tasks: list[dict], revision: int = 1, reason: str = "initial", triggers: list[str] | None = None) -> dict:
        return {"revision": revision, "reason": reason, "attempt_limit": 3, "revision_limit": 3,
                "no_progress": "same failure", "trigger_event_ids": triggers or ["e-1"], "tasks": tasks}

    def assert_rejected(self, name: str, rows: list[dict], command: str = "validate") -> dict:
        run = self.root(name); write_log(run, rows)
        args = ["--run-dir", str(run)] + (["--write"] if command == "snapshot" else [])
        result = invoke(STATE_CLI, command, *args)
        self.assertEqual(result.returncode, 2, result.stderr)
        error = json.loads(result.stderr); self.assertFalse(error["ok"]); self.assertIn("code", error)
        return error

    def test_snapshot_tamper_with_valid_digest_is_repaired(self) -> None:
        run = self.root("snapshot")
        rows = [opened()]
        write_log(run, rows); self.assertEqual(invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write").returncode, 0)
        snapshot = json.loads((run / "snapshot.json").read_text()); snapshot["objective"] = "tampered"
        (run / "snapshot.json").write_text(json.dumps(snapshot), encoding="utf-8")
        agents = dump(self.root("snapshot-agents") / "agents.json", [])
        self.assertEqual(invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents)).returncode, 0)
        self.assertEqual(json.loads((run / "snapshot.json").read_text())["objective"], "verify one bounded outcome")

    def test_unresolved_root_writer_blocks_resume_without_agents(self) -> None:
        run = self.root("root-writer"); root_task = task("w-1", "write", owner="root")
        rows = [opened(), event(2, "plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 1, "revision_limit": 1, "no_progress": "one attempt", "trigger_event_ids": ["e-1"], "tasks": [root_task]}), event(3, "task.admitted", {"task_id": "w-1", "task_revision": 1, "plan_revision": 1})]
        write_log(run, rows); agents = dump(self.root("root-writer-agents") / "agents.json", [])
        resumed = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
        self.assertEqual(resumed.returncode, 0, resumed.stderr); self.assertFalse(output(resumed)["admission_allowed"])

    def test_completed_reader_missing_from_live_list_does_not_hold_writer_barrier(self) -> None:
        run = self.root("reader"); reader = task("r-1", owner="agent-a")
        rows = [opened(), event(2, "plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 1, "revision_limit": 1, "no_progress": "one attempt", "trigger_event_ids": ["e-1"], "tasks": [reader]}),
                event(3, "task.admitted", {"task_id": "r-1", "task_revision": 1, "plan_revision": 1}),
                event(4, "agent.requested", {"task_id": "r-1", "handle": "agent-a", "requested_model": reader["requested_model"], "requested_effort": reader["requested_effort"], "fork_turns": reader["fork_turns"]}),
                event(5, "agent.observed", {"handle": "agent-a", "lifecycle": "completed", "effect_status": "reconciled", "effective_model": None, "effective_effort": None}),
                event(6, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": ["c-1"], "kind": "observation", "locator": "artifact/r", "sha256": None}),
                event(7, "task.result", {"task_id": "r-1", "task_revision": 1, "outcome": "passed", "effect_status": "none", "evidence_ids": ["ev-1"]})]
        write_log(run, rows); agents = dump(self.root("reader-agents") / "agents.json", [])
        resumed = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
        self.assertEqual(resumed.returncode, 0, resumed.stderr); self.assertTrue(output(resumed)["admission_allowed"])

    def test_stale_plan_attempt_limit_and_old_handle_reuse_are_rejected(self) -> None:
        first = task("w-1", "write", owner="agent-a"); second = task("w-2", "write", owner="agent-b")
        plan1 = {"revision": 1, "reason": "initial", "attempt_limit": 1, "revision_limit": 2, "no_progress": "one attempt", "trigger_event_ids": ["e-1"], "tasks": [first, second]}
        changed = copy.deepcopy(first); changed["revision"] = 2; changed["inputs"] = ["repair"]
        rows = [opened(), event(2, "plan.revised", plan1), event(3, "task.admitted", {"task_id": "w-1", "task_revision": 1, "plan_revision": 1}),
                event(4, "agent.requested", {"task_id": "w-1", "handle": "agent-a", "requested_model": first["requested_model"], "requested_effort": first["requested_effort"], "fork_turns": first["fork_turns"]}),
                event(5, "agent.observed", {"handle": "agent-a", "lifecycle": "completed", "effect_status": "reconciled", "effective_model": None, "effective_effort": None}),
                event(6, "evidence.recorded", {"evidence_id": "ev-f", "criterion_ids": ["c-1"], "kind": "observation", "locator": "failure", "sha256": None}),
                event(7, "task.result", {"task_id": "w-1", "task_revision": 1, "outcome": "failed", "effect_status": "reconciled", "evidence_ids": ["ev-f"]})]
        revised = {"revision": 2, "reason": "failure", "attempt_limit": 2, "revision_limit": 2, "no_progress": "new repair", "trigger_event_ids": ["e-7"], "tasks": [changed, second], "unmet_criterion": "c-1", "failure_evidence_ids": ["ev-f"], "cause": "candidate_defect", "strategy_change": "repair from evidence"}
        stale = rows + [event(8, "plan.revised", revised), event(9, "task.admitted", {"task_id": "w-2", "task_revision": 1, "plan_revision": 1})]
        run = self.root("stale-plan"); write_log(run, stale); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 2)
        over = copy.deepcopy(rows); bounded_revision = copy.deepcopy(revised); bounded_revision["attempt_limit"] = 1
        over += [event(8, "plan.revised", bounded_revision), event(9, "task.admitted", {"task_id": "w-1", "task_revision": 2, "plan_revision": 2})]
        run = self.root("attempt-limit"); write_log(run, over); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 2)

    def test_unknown_result_can_reconcile_once_and_terminal_scope_is_outcome_specific(self) -> None:
        run = self.root("unknown-reconcile"); item = task("r-1")
        rows = [opened(), event(2, "plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 1, "revision_limit": 1, "no_progress": "one attempt", "trigger_event_ids": ["e-1"], "tasks": [item]}),
                event(3, "task.admitted", {"task_id": "r-1", "task_revision": 1, "plan_revision": 1}),
                event(4, "task.result", {"task_id": "r-1", "task_revision": 1, "outcome": "unknown", "effect_status": "unknown", "evidence_ids": []}),
                event(5, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": ["c-1"], "kind": "observation", "locator": "artifact/reconciled", "sha256": None}),
                event(6, "task.result", {"task_id": "r-1", "task_revision": 1, "outcome": "passed", "effect_status": "none", "evidence_ids": ["ev-1"]})]
        write_log(run, rows); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 0)
        repeated = rows + [event(7, "task.result", {"task_id": "r-1", "task_revision": 1, "outcome": "failed", "effect_status": "none", "evidence_ids": ["ev-1"]})]
        run = self.root("known-replaced"); write_log(run, repeated); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 2)

        omitted = [opened(), event(2, "plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 1, "revision_limit": 1, "no_progress": "one attempt", "trigger_event_ids": ["e-1"], "tasks": [item]}),
                   event(3, "run.closed", {"status": "stopped", "criterion_evidence": {}, "scope_reconciled": False, "remaining_human_items": ["r-1 was not attempted"]})]
        run = self.root("unadmitted-stopped"); write_log(run, omitted); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run), "--terminal").returncode, 0)
        completed = copy.deepcopy(omitted); completed[-1]["payload"].update(status="completed", scope_reconciled=True, remaining_human_items=[])
        self.assert_rejected("unadmitted-completed", completed)

    def test_writer_release_resume_and_both_fact_orders_share_one_rule(self) -> None:
        writer = task("w-1", "write", owner="agent-a"); next_writer = task("w-2", "write")
        base = [opened(), event(2, "plan.revised", self.plan([writer, next_writer])),
                event(3, "task.admitted", {"task_id": "w-1", "task_revision": 1, "plan_revision": 1}),
                event(4, "agent.requested", {"task_id": "w-1", "handle": "agent-a", "requested_model": writer["requested_model"], "requested_effort": writer["requested_effort"], "fork_turns": writer["fork_turns"]}),
                event(5, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": ["c-1"], "kind": "observation", "locator": "artifact/w", "sha256": None})]
        claimed = base + [event(6, "task.result", {"task_id": "w-1", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["ev-1"]})]
        run = self.root("unreleased-resume"); write_log(run, claimed); agents = dump(self.root("unreleased-agents") / "agents.json", [])
        resumed = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
        self.assertEqual(resumed.returncode, 0, resumed.stderr); self.assertFalse(output(resumed)["admission_allowed"])

        for label, tail in (
            ("result-first", [event(6, "task.result", {"task_id": "w-1", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["ev-1"]}), event(7, "agent.observed", {"handle": "agent-a", "lifecycle": "completed", "effect_status": "reconciled", "effective_model": None, "effective_effort": None})]),
            ("observation-first", [event(6, "agent.observed", {"handle": "agent-a", "lifecycle": "completed", "effect_status": "reconciled", "effective_model": None, "effective_effort": None}), event(7, "task.result", {"task_id": "w-1", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["ev-1"]})]),
        ):
            rows = base + tail + [event(8, "task.admitted", {"task_id": "w-2", "task_revision": 1, "plan_revision": 1})]
            run = self.root(label); write_log(run, rows); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 0)

    def test_writer_release_requires_result_and_latest_terminal_observation_to_coexist(self) -> None:
        writer = task("w-1", "write", owner="/root/writer"); next_writer = task("w-2", "write")
        base = [opened(), event(2, "plan.revised", self.plan([writer, next_writer])),
                event(3, "task.admitted", {"task_id": "w-1", "task_revision": 1, "plan_revision": 1}),
                event(4, "agent.requested", {"task_id": "w-1", "handle": "/root/writer", "requested_model": writer["requested_model"], "requested_effort": writer["requested_effort"], "fork_turns": writer["fork_turns"]}),
                event(5, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": ["c-1"], "kind": "observation", "locator": "artifact/w", "sha256": None}),
                event(6, "agent.observed", {"handle": "/root/writer", "lifecycle": "completed", "effect_status": "reconciled", "effective_model": None, "effective_effort": None})]
        for lifecycle in ("active", "idle", "interrupted", "missing"):
            with self.subTest(lifecycle=lifecycle):
                rows = copy.deepcopy(base)
                rows += [event(7, "agent.observed", {"handle": "/root/writer", "lifecycle": lifecycle, "effect_status": "unknown", "effective_model": None, "effective_effort": None}),
                         event(8, "task.result", {"task_id": "w-1", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["ev-1"]})]
                run = self.root(f"terminal-then-{lifecycle}"); write_log(run, rows)
                agents = dump(run / "agents.json", [{"handle": "/root/writer", "lifecycle": lifecycle}])
                resumed = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
                self.assertEqual(resumed.returncode, 0, resumed.stderr); self.assertFalse(output(resumed)["admission_allowed"])
                admission = dump(run / "admission.json", event(9, "task.admitted", {"task_id": "w-2", "task_revision": 1, "plan_revision": 1}))
                rejected = invoke(STATE_CLI, "append", "--run-dir", str(run), "--event", str(admission))
                self.assertEqual(rejected.returncode, 2, rejected.stderr); self.assertEqual(json.loads(rejected.stderr)["code"], "writer_busy")
        resolved = copy.deepcopy(base)
        resolved += [event(7, "agent.observed", {"handle": "/root/writer", "lifecycle": "active", "effect_status": "unknown", "effective_model": None, "effective_effort": None}),
                     event(8, "task.result", {"task_id": "w-1", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["ev-1"]}),
                     event(9, "agent.observed", {"handle": "/root/writer", "lifecycle": "completed", "effect_status": "reconciled", "effective_model": None, "effective_effort": None}),
                     event(10, "task.admitted", {"task_id": "w-2", "task_revision": 1, "plan_revision": 1})]
        run = self.root("fresh-terminal-after-result"); write_log(run, resolved)
        self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 0)

    def test_planned_root_is_safe_released_root_is_safe_and_known_unknown_is_rejected(self) -> None:
        writer = task("w-1", "write")
        planned = [opened(), event(2, "plan.revised", self.plan([writer]))]
        run = self.root("planned-root"); write_log(run, planned); agents = dump(self.root("planned-root-agents") / "agents.json", [])
        self.assertTrue(output(invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents)))["admission_allowed"])
        bad = planned + [event(3, "task.admitted", {"task_id": "w-1", "task_revision": 1, "plan_revision": 1}), event(4, "task.result", {"task_id": "w-1", "task_revision": 1, "outcome": "failed", "effect_status": "unknown", "evidence_ids": []})]
        self.assert_rejected("known-unknown-effect", bad)
        reconciled = planned + [event(3, "task.admitted", {"task_id": "w-1", "task_revision": 1, "plan_revision": 1}), event(4, "task.result", {"task_id": "w-1", "task_revision": 1, "outcome": "unknown", "effect_status": "unknown", "evidence_ids": []}), event(5, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": [], "kind": "observation", "locator": "effect/reconciled", "sha256": None}), event(6, "task.result", {"task_id": "w-1", "task_revision": 1, "outcome": "failed", "effect_status": "reconciled", "evidence_ids": ["ev-1"]})]
        run = self.root("root-reconciled"); write_log(run, reconciled); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 0)
        self.assertTrue(output(invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents)))["admission_allowed"])

    def test_one_assignment_per_task_revision(self) -> None:
        writer = task("w-1", "write", owner="agent-a")
        rows = [opened(), event(2, "plan.revised", self.plan([writer])), event(3, "task.admitted", {"task_id": "w-1", "task_revision": 1, "plan_revision": 1}),
                event(4, "agent.requested", {"task_id": "w-1", "handle": "agent-a", "requested_model": writer["requested_model"], "requested_effort": writer["requested_effort"], "fork_turns": writer["fork_turns"]}),
                event(5, "agent.requested", {"task_id": "w-1", "handle": "agent-b", "requested_model": writer["requested_model"], "requested_effort": writer["requested_effort"], "fork_turns": writer["fork_turns"]})]
        self.assert_rejected("two-assignments", rows)

    def test_native_canonical_handle_round_trips_without_aliasing(self) -> None:
        handle = "/root/scout"; reader = task("r-1", owner=handle)
        rows = [opened(), event(2, "plan.revised", self.plan([reader])), event(3, "task.admitted", {"task_id": "r-1", "task_revision": 1, "plan_revision": 1}), event(4, "agent.requested", {"task_id": "r-1", "handle": handle, "requested_model": reader["requested_model"], "requested_effort": reader["requested_effort"], "fork_turns": reader["fork_turns"]})]
        run = self.root("canonical-handle"); write_log(run, rows); agents = dump(self.root("canonical-handle-input") / "agents.json", [{"handle": handle, "lifecycle": "active", "effective_model": None, "effective_effort": None}])
        result = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
        self.assertEqual(result.returncode, 0, result.stderr); self.assertEqual(output(result)["proposed_events"][0]["payload"]["handle"], handle)

    def test_released_native_handle_can_be_reassigned_without_reusing_old_completion(self) -> None:
        handle = "/root/scout"; first = task("r-1", owner=handle); second = task("w-2", "write", dependencies=["r-1"], owner=handle)
        rows = [opened(), event(2, "plan.revised", self.plan([first, second])), event(3, "task.admitted", {"task_id": "r-1", "task_revision": 1, "plan_revision": 1}), event(4, "agent.requested", {"task_id": "r-1", "handle": handle, "requested_model": first["requested_model"], "requested_effort": first["requested_effort"], "fork_turns": first["fork_turns"]}), event(5, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": ["c-1"], "kind": "observation", "locator": "artifact/first", "sha256": None}), event(6, "task.result", {"task_id": "r-1", "task_revision": 1, "outcome": "passed", "effect_status": "none", "evidence_ids": ["ev-1"]}), event(7, "agent.observed", {"handle": handle, "lifecycle": "completed", "effect_status": "reconciled", "effective_model": None, "effective_effort": None}), event(8, "task.admitted", {"task_id": "w-2", "task_revision": 1, "plan_revision": 1}), event(9, "agent.requested", {"task_id": "w-2", "handle": handle, "requested_model": second["requested_model"], "requested_effort": second["requested_effort"], "fork_turns": second["fork_turns"]})]
        run = self.root("handle-reassigned"); write_log(run, rows); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 0)
        agents = dump(self.root("handle-reassigned-input") / "agents.json", [])
        resumed = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
        self.assertEqual(resumed.returncode, 0, resumed.stderr); self.assertFalse(output(resumed)["admission_allowed"])

    def test_late_old_results_never_change_current_revision_projection(self) -> None:
        original = task("t-1"); changed = copy.deepcopy(original); changed["revision"] = 2; changed["inputs"] = ["new scope"]
        rows = [opened(), event(2, "plan.revised", self.plan([original])), event(3, "task.admitted", {"task_id": "t-1", "task_revision": 1, "plan_revision": 1}), event(4, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": ["c-1"], "kind": "observation", "locator": "artifact/old", "sha256": None}), event(5, "plan.revised", self.plan([changed], 2, "evidence_change", ["e-4"])), event(6, "task.result", {"task_id": "t-1", "task_revision": 1, "outcome": "passed", "effect_status": "none", "evidence_ids": ["ev-1"]})]
        run = self.root("late-old-result-r2"); write_log(run, rows); result = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
        self.assertEqual(result.returncode, 0, result.stderr); current = output(result)["tasks"]["t-1"]
        self.assertEqual((current["revision"], current["state"]), (2, "planned")); self.assertNotIn("result", current)
        unknown = copy.deepcopy(rows[:4]); unknown.append(event(5, "task.result", {"task_id": "t-1", "task_revision": 1, "outcome": "unknown", "effect_status": "unknown", "evidence_ids": []})); unknown.append(event(6, "plan.revised", self.plan([changed], 2, "evidence_change", ["e-4"]))); unknown.append(event(7, "task.result", {"task_id": "t-1", "task_revision": 1, "outcome": "failed", "effect_status": "none", "evidence_ids": ["ev-1"]}))
        run = self.root("late-old-reconciliation"); write_log(run, unknown); result = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
        self.assertEqual(result.returncode, 0, result.stderr); self.assertEqual(output(result)["tasks"]["t-1"]["state"], "planned")

    def test_malformed_types_are_structured_contract_errors(self) -> None:
        mutations = [("type", []), ("v", True), ("seq", 1.0), ("at", "2026-99-99T99:99:99Z")]
        for field, value in mutations:
            with self.subTest(field=field):
                row = opened(); row[field] = value; self.assert_rejected(f"malformed-{field}", [row])
        row = opened(); row["payload"]["constraints"] = None; self.assert_rejected("malformed-payload", [row])
        typed_logs = []
        rows = complete_read_run(); rows[1]["payload"]["reason"] = []; typed_logs.append(("plan-reason", rows))
        rows = complete_read_run(); rows[3]["payload"]["kind"] = {}; typed_logs.append(("evidence-kind", rows))
        rows = complete_read_run(); rows[4]["payload"]["outcome"] = None; typed_logs.append(("result-outcome", rows))
        rows = complete_read_run(); rows[5]["payload"]["outcome"] = []; typed_logs.append(("check-outcome", rows))
        rows = complete_read_run(); rows[-1]["payload"]["status"] = {}; typed_logs.append(("run-status", rows))
        for label, rows in typed_logs:
            with self.subTest(label=label): self.assert_rejected(f"malformed-{label}", rows)
        run = self.root("malformed-live"); write_log(run, [opened()]); bad_agents = dump(self.root("malformed-live-input") / "agents.json", [{"handle": "agent-a", "lifecycle": []}])
        result = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(bad_agents)); self.assertEqual(result.returncode, 2); self.assertFalse(json.loads(result.stderr)["ok"])
        run = self.root("typed-snapshot-preserve"); write_log(run, [dict(opened(), v=True)]); (run / "snapshot.json").write_bytes(b"preserve")
        result = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write"); self.assertEqual(result.returncode, 2); self.assertEqual((run / "snapshot.json").read_bytes(), b"preserve")

    def test_invalid_utf8_is_rejected_or_repaired_at_the_correct_boundary(self) -> None:
        run = self.root("utf8"); write_log(run, [opened()])
        baseline = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        log_bytes = (run / "events.jsonl").read_bytes(); bad = run / "invalid.json"; bad.write_bytes(b"\xff")
        commands = [
            ("append", "--run-dir", str(run), "--event", str(bad)),
            ("resume", "--run-dir", str(run), "--agents", str(bad)),
            ("init", "--run-dir", str(run / "new-run"), "--run-id", "new-run", "--objective", "bounded", "--criteria", str(bad)),
        ]
        for args in commands:
            with self.subTest(command=args[0]):
                result = invoke(STATE_CLI, *args)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(json.loads(result.stderr)["code"], "invalid_json")
                self.assertEqual((run / "events.jsonl").read_bytes(), log_bytes)
        (run / "snapshot.json").write_bytes(b"\xff"); agents = dump(run / "agents.json", [])
        repaired = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
        self.assertEqual(repaired.returncode, 0, repaired.stderr)
        self.assertNotEqual((run / "snapshot.json").read_bytes(), b"\xff"); self.assertEqual((run / "events.jsonl").read_bytes(), log_bytes)

        invalid_log = self.root("utf8-authoritative"); (invalid_log / "events.jsonl").write_bytes(b"\xff"); (invalid_log / "snapshot.json").write_bytes(b"preserve")
        result = invoke(STATE_CLI, "snapshot", "--run-dir", str(invalid_log), "--write")
        self.assertEqual(result.returncode, 2, result.stderr); self.assertEqual(json.loads(result.stderr)["code"], "invalid_json")
        self.assertEqual((invalid_log / "events.jsonl").read_bytes(), b"\xff"); self.assertEqual((invalid_log / "snapshot.json").read_bytes(), b"preserve")

    def test_plan_expansion_later_initial_and_correction_links(self) -> None:
        first = task("t-1"); second = task("t-2")
        expanded = [opened(), event(2, "plan.revised", self.plan([first])), event(3, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": [], "kind": "observation", "locator": "scope/new", "sha256": None}), event(4, "plan.revised", self.plan([first, second], 2, "evidence_change", ["e-3"]))]
        run = self.root("graph-expanded"); write_log(run, expanded); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 0)
        invalid = copy.deepcopy(expanded); invalid[-1]["payload"]["reason"] = "initial"; self.assert_rejected("later-initial", invalid)
        dangling = [opened(), event(2, "run.amended", {"kind": "objective", "value": "changed", "reason": "correction", "corrects_event_id": "missing"})]
        self.assert_rejected("dangling-amendment-r2", dangling, "snapshot")
        future = copy.deepcopy(dangling); future[-1]["payload"]["corrects_event_id"] = "e-3"; self.assert_rejected("future-amendment-r2", future)
        dangling[-1]["payload"]["corrects_event_id"] = "e-1"; run = self.root("valid-amendment-r2"); write_log(run, dangling); self.assertEqual(invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write").returncode, 0)

    def test_completion_associations_and_reports_preserve_negative_facts(self) -> None:
        unassociated = complete_read_run(); unassociated[3]["payload"]["criterion_ids"] = []; self.assert_rejected("unassociated-criterion", unassociated)
        empty_check = complete_read_run(); empty_check[5]["payload"]["evidence_ids"] = []; self.assert_rejected("empty-passed-check", empty_check)
        rows = complete_read_run()[:-1]; rows.append(event(8, "evidence.recorded", {"evidence_id": "ev-untested", "criterion_ids": ["c-1"], "kind": "untested", "locator": "mobile viewport not exercised", "sha256": None})); rows.append(event(9, "check.recorded", {"check_id": "final-integration", "criterion_ids": ["c-1"], "outcome": "failed", "evidence_ids": ["ev-1"]})); rows.append(event(10, "finding.opened", {"finding_id": "f-minor", "severity": "minor", "summary": "narrow-screen label overlap", "evidence_ids": ["ev-1"]})); rows.append(event(11, "finding.dispositioned", {"finding_id": "f-minor", "disposition": "accepted", "evidence_ids": ["ev-1"], "verification_check_id": None})); rows.append(event(12, "run.closed", {"status": "stopped", "criterion_evidence": {}, "scope_reconciled": False, "remaining_human_items": []}))
        run = self.root("truthful-report"); write_log(run, rows); result = invoke(STATE_CLI, "report", "--run-dir", str(run), "--write")
        self.assertEqual(result.returncode, 0, result.stderr); report = (run / "report.md").read_text()
        for expected in ("Status: stopped", "mobile viewport not exercised", "final-integration", "narrow-screen label overlap", "Run is terminal (stopped)"):
            self.assertIn(expected, report)


if __name__ == "__main__": unittest.main()
