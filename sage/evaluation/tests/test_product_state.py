from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from support import STATE_CLI, complete_read_run, dump, event, invoke, opened, output, sandbox, strict_event_mutations, task, write_log


class StateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(STATE_CLI.is_file(), "future product missing: sage/scripts/sage_state.py")

    def test_init_append_snapshot_report_and_stale_rebuild(self) -> None:
        with sandbox() as raw:
            root = Path(raw); run = root / "run"; criteria = dump(root / "criteria.json", [{"id": "c-1", "text": "criterion"}])
            created = invoke(STATE_CLI, "init", "--run-dir", str(run), "--run-id", "run-1", "--objective", "bounded objective", "--criteria", str(criteria))
            self.assertEqual(created.returncode, 0, created.stderr)
            additions = complete_read_run()[1:]
            batch = root / "batch.jsonl"; batch.write_text("".join(json.dumps(row) + "\n" for row in additions), encoding="utf-8")
            appended = invoke(STATE_CLI, "append", "--run-dir", str(run), "--events", str(batch))
            self.assertEqual(appended.returncode, 0, appended.stderr)
            snap = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
            self.assertEqual(snap.returncode, 0, snap.stderr)
            stale = json.loads((run / "snapshot.json").read_text()); stale["events_sha256"] = "0" * 64
            (run / "snapshot.json").write_text(json.dumps(stale), encoding="utf-8")
            rebuilt = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
            self.assertNotEqual(json.loads((run / "snapshot.json").read_text())["events_sha256"], "0" * 64)
            report = invoke(STATE_CLI, "report", "--run-dir", str(run), "--write")
            self.assertEqual(report.returncode, 0, report.stderr); self.assertTrue((run / "report.md").is_file())

    def test_malformed_duplicate_nonfinite_and_invalid_log_do_not_replace_snapshot(self) -> None:
        with sandbox() as raw:
            root = Path(raw); control, mutations = strict_event_mutations()
            accepted = root / "control"; accepted.mkdir(); (accepted / "events.jsonl").write_text(control + "\n", encoding="utf-8")
            self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(accepted)).returncode, 0)
            bad_lines = [*mutations.values(), control[:-1]]
            for index, line in enumerate(bad_lines):
                run = root / f"bad-{index}"; run.mkdir(); (run / "events.jsonl").write_text(line, encoding="utf-8")
                (run / "snapshot.json").write_bytes(b"preserve-me")
                result = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
                self.assertEqual(result.returncode, 2); self.assertEqual(json.loads(result.stderr)["code"], "invalid_json"); self.assertEqual((run / "snapshot.json").read_bytes(), b"preserve-me")

            run = root / "append"; write_log(run, complete_read_run()); before = (run / "events.jsonl").read_bytes()
            invalid = dump(root / "invalid-event.json", event(10, "checkpoint.written", {"next_action": "wrong sequence", "baselines": [], "unresolved_user_items": []}))
            appended = invoke(STATE_CLI, "append", "--run-dir", str(run), "--event", str(invalid))
            self.assertEqual(appended.returncode, 2); self.assertEqual((run / "events.jsonl").read_bytes(), before)

    def test_dependencies_one_writer_and_unknown_effect_hold_admission(self) -> None:
        with sandbox() as raw:
            root = Path(raw)
            rows = [opened(), event(2, "plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 2, "revision_limit": 2, "no_progress": "same failure twice", "trigger_event_ids": ["e-1"], "tasks": [task("write-1", "write", owner="agent-a"), task("write-2", "write", dependencies=["write-1"], owner="agent-b")]})]
            rows.append(event(3, "task.admitted", {"task_id": "write-2", "task_revision": 1, "plan_revision": 1}))
            run = root / "dependency"; write_log(run, rows)
            self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 2)

            rows[1]["payload"]["tasks"][1]["dependencies"] = []
            rows = rows[:2] + [event(3, "task.admitted", {"task_id": "write-1", "task_revision": 1, "plan_revision": 1}), event(4, "task.admitted", {"task_id": "write-2", "task_revision": 1, "plan_revision": 1})]
            run = root / "two-writers"; write_log(run, rows)
            self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 2)

            rows[1]["payload"]["tasks"][1]["dependencies"] = ["write-1"]
            rows = rows[:3]
            rows += [event(4, "agent.requested", {"task_id": "write-1", "handle": "agent-a", "requested_model": "gpt-5.6-sol", "requested_effort": "high", "fork_turns": "none"}), event(5, "agent.observed", {"handle": "agent-a", "lifecycle": "active", "effect_status": "unknown", "effective_model": None, "effective_effort": None}), event(6, "evidence.recorded", {"evidence_id": "ev-write", "criterion_ids": [], "kind": "observation", "locator": "artifact/write", "sha256": None}), event(7, "task.result", {"task_id": "write-1", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["ev-write"]}), event(8, "task.admitted", {"task_id": "write-2", "task_revision": 1, "plan_revision": 1})]
            run = root / "active-after-claim"; write_log(run, rows)
            self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 2)
            rows.insert(-1, event(8, "agent.observed", {"handle": "agent-a", "lifecycle": "completed", "effect_status": "reconciled", "effective_model": None, "effective_effort": None}))
            rows[-1]["seq"] = 9; rows[-1]["event_id"] = "e-9"; rows[-1]["at"] = "2026-09-07T00:00:09Z"
            run = root / "terminal-writer-released"; write_log(run, rows)
            self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 0)

    def test_terminal_rejects_incomplete_criteria_and_open_or_accepted_major_findings(self) -> None:
        with sandbox() as raw:
            root = Path(raw)
            incomplete = complete_read_run(); incomplete[-1]["payload"]["criterion_evidence"] = {}
            run = root / "incomplete"; write_log(run, incomplete)
            self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run), "--terminal").returncode, 2)
            for disposition in (None, "accepted"):
                rows = complete_read_run()[:-1]
                rows.insert(-1, event(7, "finding.opened", {"finding_id": "f-1", "severity": "major", "summary": "material issue", "evidence_ids": ["ev-1"]}))
                for seq, row in enumerate(rows, 1): row["seq"] = seq; row["event_id"] = f"e-{seq}"
                if disposition:
                    rows.append(event(len(rows) + 1, "finding.dispositioned", {"finding_id": "f-1", "disposition": disposition, "evidence_ids": ["ev-1"], "verification_check_id": None}))
                rows.append(event(len(rows) + 1, "run.closed", {"status": "completed", "criterion_evidence": {"c-1": ["ev-1"]}, "scope_reconciled": True, "remaining_human_items": []}))
                run = root / f"finding-{disposition}"; write_log(run, rows)
                self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run), "--terminal").returncode, 2)

    def test_requested_effective_unknown_and_resume_is_advisory(self) -> None:
        with sandbox() as raw:
            root = Path(raw); run = root / "run"
            rows = [opened(), event(2, "plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 1, "revision_limit": 1, "no_progress": "one failure", "trigger_event_ids": ["e-1"], "tasks": [task("write-1", "write", owner="agent-a")]}), event(3, "task.admitted", {"task_id": "write-1", "task_revision": 1, "plan_revision": 1}), event(4, "agent.requested", {"task_id": "write-1", "handle": "agent-a", "requested_model": "gpt-5.6-sol", "requested_effort": "high", "fork_turns": "none"})]
            write_log(run, rows); invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
            stale = json.loads((run / "snapshot.json").read_text()); stale["events_sha256"] = "0" * 64; (run / "snapshot.json").write_text(json.dumps(stale), encoding="utf-8")
            snapshot_before = (run / "snapshot.json").read_bytes(); log_before = (run / "events.jsonl").read_bytes()
            agents = dump(root / "agents.json", [{"handle": "agent-a", "lifecycle": "idle"}])
            resumed = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
            self.assertEqual(resumed.returncode, 0, resumed.stderr); value = output(resumed)
            self.assertFalse(value["admission_allowed"]); self.assertEqual(value["recommended_next_action"], "revise_plan")
            self.assertEqual(value["proposed_events"][0]["payload"]["effective_model"], None); self.assertEqual(value["proposed_events"][0]["payload"]["effect_status"], "unknown")
            self.assertEqual((run / "events.jsonl").read_bytes(), log_before); self.assertNotEqual((run / "snapshot.json").read_bytes(), snapshot_before)
            self.assertEqual(json.loads((run / "snapshot.json").read_text())["agents"]["agent-a"]["effective_model"], "unknown")
            proposed = dump(root / "observed.json", value["proposed_events"][0]); persisted = invoke(STATE_CLI, "append", "--run-dir", str(run), "--event", str(proposed))
            self.assertEqual(persisted.returncode, 0, persisted.stderr); self.assertEqual(invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write").returncode, 0)
            after_persist = output(invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))); self.assertFalse(after_persist["admission_allowed"])
            (run / "snapshot.json").unlink(); missing = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
            self.assertEqual(missing.returncode, 0, missing.stderr); self.assertTrue((run / "snapshot.json").is_file()); self.assertGreater(len((run / "events.jsonl").read_bytes()), len(log_before))

    def test_retry_requires_resolved_failure_evidence_cause_and_material_change(self) -> None:
        with sandbox() as raw:
            root = Path(raw); base_task = task("t-1")
            rows = [opened(), event(2, "plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 2, "revision_limit": 2, "no_progress": "same failure twice", "trigger_event_ids": ["e-1"], "tasks": [base_task]}), event(3, "task.admitted", {"task_id": "t-1", "task_revision": 1, "plan_revision": 1}), event(4, "evidence.recorded", {"evidence_id": "ev-fail", "criterion_ids": ["c-1"], "kind": "observation", "locator": "check/failure", "sha256": None}), event(5, "task.result", {"task_id": "t-1", "task_revision": 1, "outcome": "failed", "effect_status": "none", "evidence_ids": ["ev-fail"]})]
            changed = copy.deepcopy(base_task); changed["revision"] = 2; changed["inputs"] = ["bounded repair"]
            valid_payload = {"revision": 2, "reason": "failure", "attempt_limit": 2, "revision_limit": 2, "no_progress": "same failure twice", "trigger_event_ids": ["e-5"], "tasks": [changed], "unmet_criterion": "c-1", "failure_evidence_ids": ["ev-fail"], "cause": "candidate_defect", "strategy_change": "repair the candidate against ev-fail"}
            valid = copy.deepcopy(rows); valid.append(event(6, "plan.revised", valid_payload))
            run = root / "valid"; write_log(run, valid); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 0)
            missing = copy.deepcopy(rows); payload = copy.deepcopy(valid_payload); payload["failure_evidence_ids"] = ["missing"]; missing.append(event(6, "plan.revised", payload))
            run = root / "missing-evidence"; write_log(run, missing); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 2)
            unchanged = copy.deepcopy(rows); payload = copy.deepcopy(valid_payload); payload["tasks"] = [base_task]; unchanged.append(event(6, "plan.revised", payload))
            run = root / "unchanged"; write_log(run, unchanged); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 2)
            over_bound = copy.deepcopy(valid); over_bound[1]["payload"]["revision_limit"] = 1
            run = root / "over-bound"; write_log(run, over_bound); self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(run)).returncode, 2)

    def test_synchronous_root_write_releases_without_fabricated_agent(self) -> None:
        with sandbox() as raw:
            run = Path(raw) / "root-write"; root_task = task("write-1", "write", owner="root")
            rows = [opened(), event(2, "plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 1, "revision_limit": 1, "no_progress": "one bounded attempt", "trigger_event_ids": ["e-1"], "tasks": [root_task]}),
                    event(3, "task.admitted", {"task_id": "write-1", "task_revision": 1, "plan_revision": 1}),
                    event(4, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": ["c-1"], "kind": "observation", "locator": "artifact/write", "sha256": None}),
                    event(5, "task.result", {"task_id": "write-1", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["ev-1"]}),
                    event(6, "check.recorded", {"check_id": "check-1", "criterion_ids": ["c-1"], "outcome": "passed", "evidence_ids": ["ev-1"]}),
                    event(7, "run.closed", {"status": "completed", "criterion_evidence": {"c-1": ["ev-1"]}, "scope_reconciled": True, "remaining_human_items": []})]
            write_log(run, rows); result = invoke(STATE_CLI, "validate", "--run-dir", str(run), "--terminal")
            self.assertEqual(result.returncode, 0, result.stderr); self.assertFalse(any(row["type"].startswith("agent.") for row in rows))

    def test_amendments_corrected_notes_user_decision_and_retrieval_feedback_survive_projection(self) -> None:
        with sandbox() as raw:
            run = Path(raw) / "durable-notes"; original = task("t-1"); changed = copy.deepcopy(original); changed["inputs"] = ["expanded scope"]
            rows = [opened(),
                    event(2, "plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 2, "revision_limit": 2, "no_progress": "same outcome twice", "trigger_event_ids": ["e-1"], "tasks": [original]}),
                    event(3, "run.amended", {"kind": "objective", "value": "verify expanded bounded outcome", "reason": "user scope change", "corrects_event_id": None}),
                    event(4, "note.recorded", {"category": "assumption", "text": "first assumption", "evidence_ids": [], "corrects_event_id": None}),
                    event(5, "note.recorded", {"category": "assumption", "text": "corrected assumption", "evidence_ids": [], "corrects_event_id": "e-4"}),
                    event(6, "user.decision", {"request_id": "u-1", "question": "expand scope?", "decision": "yes", "received_at": "2026-09-07T00:00:06Z"}),
                    event(7, "plan.revised", {"revision": 2, "reason": "user_amendment", "attempt_limit": 2, "revision_limit": 2, "no_progress": "same outcome twice", "trigger_event_ids": ["e-3", "e-6"], "tasks": [changed]}),
                    event(8, "knowledge.selected", {"generation_id": "g-1", "cue_fingerprint": "abc", "cues": {"operation": ["resume"]}, "matches": [{"id": "k-1", "revision": 1, "status": "supported", "reason": "operation cue"}], "retrieval_status": "matched"}),
                    event(9, "knowledge.feedback", {"id": "k-1", "revision": 1, "outcome": "misleading", "evidence_ids": [], "missed_recognizers": ["environment"]})]
            write_log(run, rows); result = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
            self.assertEqual(result.returncode, 0, result.stderr); snapshot = json.loads((run / "snapshot.json").read_text())
            self.assertEqual(snapshot["objective"], "verify expanded bounded outcome"); self.assertEqual(snapshot["assumptions"][-1]["corrects_event_id"], "e-4")
            self.assertEqual(snapshot["user_decisions"][0]["request_id"], "u-1"); self.assertEqual(snapshot["knowledge_feedback"][0]["outcome"], "misleading")

    def test_knowledge_selection_preserves_status_cues_and_revision_identity(self) -> None:
        with sandbox() as raw:
            run = Path(raw) / "run"; rows = complete_read_run()[:-1]
            rows.append(event(8, "knowledge.selected", {"generation_id": "g-2", "cue_fingerprint": "abc", "cues": {"operation": ["resume"]}, "matches": [{"id": "k-1", "revision": 3, "status": "supported", "reason": "operation cue"}], "retrieval_status": "matched"}))
            rows.append(event(9, "run.closed", {"status": "completed", "criterion_evidence": {"c-1": ["ev-1"]}, "scope_reconciled": True, "remaining_human_items": []}))
            write_log(run, rows); result = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
            self.assertEqual(result.returncode, 0, result.stderr)
            selected = json.loads((run / "snapshot.json").read_text())["knowledge_selection"]
            self.assertEqual((selected["generation_id"], selected["matches"][0]["revision"]), ("g-2", 3))


if __name__ == "__main__": unittest.main()
