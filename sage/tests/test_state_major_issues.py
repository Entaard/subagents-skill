"""Regressions for acceptance-contract revision and bounded approach renewal."""
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


class StateMajorIssueTests(unittest.TestCase):
    def root(self, name: str) -> Path:
        base = Path(os.environ["SAGE_EVALUATION_SANDBOX"]).resolve() / "state-major-issues" / name
        base.mkdir(parents=True, exist_ok=True)
        return base

    def result(self, name: str, rows: list[dict], *args: str):
        run = self.root(name)
        write_log(run, rows)
        return run, invoke(STATE_CLI, *args, "--run-dir", str(run))

    @staticmethod
    def decision(sequence: int, *, hard_caps: dict | None = None) -> dict:
        payload = {
            "request_id": f"u-{sequence}", "question": "Continue with the revised bounded scope?",
            "decision": "yes", "received_at": f"2026-09-07T00:00:{sequence:02d}Z",
        }
        if hard_caps is not None:
            payload["hard_caps"] = hard_caps
        return event(sequence, "user.decision", payload)

    @staticmethod
    def criterion_revision(sequence: int, **changes) -> dict:
        payload = {
            "revision": 2, "authority_event_id": "e-2", "reason": "User changed the required format.",
            "added": [], "replaced": [], "retired": [],
        }
        payload.update(changes)
        return event(sequence, "criteria.revised", payload)

    @staticmethod
    def failed_initial(*, revision_limit: int = 1) -> tuple[list[dict], dict]:
        original = task("t-1")
        rows = [
            opened(),
            event(2, "plan.revised", {
                "revision": 1, "reason": "initial", "attempt_limit": 1,
                "revision_limit": revision_limit, "no_progress": "one bounded attempt",
                "trigger_event_ids": ["e-1"], "tasks": [original],
            }),
            event(3, "task.admitted", {"task_id": "t-1", "task_revision": 1, "plan_revision": 1}),
            event(4, "evidence.recorded", {
                "evidence_id": "ev-fail", "criterion_ids": ["c-1"], "kind": "observation",
                "locator": "checks/failure", "sha256": None,
            }),
            event(5, "task.result", {
                "task_id": "t-1", "task_revision": 1, "outcome": "failed",
                "effect_status": "none", "evidence_ids": ["ev-fail"],
            }),
        ]
        changed = copy.deepcopy(original)
        changed["revision"] = 2
        changed["inputs"] = ["different implementation"]
        return rows, changed

    @staticmethod
    def renewal(changed: dict, *, authority: str = "e-6", total_attempt_limit: int = 3,
                revision_limit: int = 3) -> dict:
        return {
            "revision": 2, "reason": "approach_renewal", "attempt_limit": 3,
            "revision_limit": revision_limit, "total_attempt_limit": total_attempt_limit,
            "no_progress": "stop after one indistinguishable renewed failure",
            "trigger_event_ids": ["e-5", authority], "tasks": [changed],
            "unmet_criterion": "c-1", "failure_evidence_ids": ["ev-fail"],
            "cause": "candidate_defect", "strategy_change": "replace the failing implementation",
            "authority_event_id": authority,
        }

    def test_criteria_add_replace_retire_preserve_history_and_change_closure(self) -> None:
        rows = [
            opened(["c-png", "c-doc"]), self.decision(2),
            self.criterion_revision(
                3,
                added=[{"id": "c-a11y", "text": "The SVG is accessible."}],
                replaced=[{"id": "c-svg", "text": "Deliver an SVG artifact.", "supersedes": "c-png"}],
                retired=["c-doc"],
            ),
            event(4, "evidence.recorded", {
                "evidence_id": "ev-old", "criterion_ids": ["c-png"], "kind": "observation",
                "locator": "artifact/old.png", "sha256": None,
            }),
            event(5, "evidence.recorded", {
                "evidence_id": "ev-svg", "criterion_ids": ["c-svg"], "kind": "observation",
                "locator": "artifact/new.svg", "sha256": None,
            }),
            event(6, "evidence.recorded", {
                "evidence_id": "ev-a11y", "criterion_ids": ["c-a11y"], "kind": "observation",
                "locator": "checks/a11y", "sha256": None,
            }),
            event(7, "check.recorded", {
                "check_id": "check-svg", "criterion_ids": ["c-svg"], "outcome": "passed",
                "evidence_ids": ["ev-svg"],
            }),
            event(8, "check.recorded", {
                "check_id": "check-a11y", "criterion_ids": ["c-a11y"], "outcome": "passed",
                "evidence_ids": ["ev-a11y"],
            }),
            event(9, "run.closed", {
                "status": "completed", "criterion_evidence": {
                    "c-svg": ["ev-svg"], "c-a11y": ["ev-a11y"],
                }, "scope_reconciled": True, "remaining_human_items": [],
            }),
        ]
        run, valid = self.result("criteria-revised", rows, "validate", "--terminal")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        snap = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
        self.assertEqual(snap.returncode, 0, snap.stderr)
        state = output(snap)
        self.assertEqual([item["id"] for item in state["criteria"]], ["c-svg", "c-a11y"])
        self.assertEqual(len(state["criteria_history"]), 2)
        self.assertEqual(state["criteria_history"][0]["criteria"][0]["id"], "c-png")
        self.assertIn("ev-old", state["evidence"])

        stale = copy.deepcopy(rows)
        stale[-1]["payload"]["criterion_evidence"] = {"c-svg": ["ev-old"], "c-a11y": ["ev-a11y"]}
        _, rejected = self.result("old-evidence-does-not-close-new", stale, "validate", "--terminal")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "incomplete_run")

        dangling = rows[:2] + [self.criterion_revision(3, authority_event_id="missing", retired=["c-doc"])]
        _, rejected = self.result("criteria-dangling-authority", dangling, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "invalid_reference")

        reused = rows[:3] + [event(4, "criteria.revised", {
            "revision": 3, "authority_event_id": "e-2", "reason": "invalid reuse",
            "added": [{"id": "c-png", "text": "Reuse retired identity."}],
            "replaced": [], "retired": [],
        })]
        _, rejected = self.result("criteria-id-reused", reused, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "immutable_history")

    def test_obsolete_task_disposition_requires_dependencies_and_reconciled_writer(self) -> None:
        obsolete = task("png", "write")
        dependent = task("publish", dependencies=["png"])
        rows = [
            opened(["c-png"]),
            event(2, "plan.revised", {
                "revision": 1, "reason": "initial", "attempt_limit": 2, "revision_limit": 2,
                "no_progress": "same failure twice", "trigger_event_ids": ["e-1"],
                "tasks": [obsolete, dependent],
            }),
            self.decision(3),
            self.criterion_revision(
                4, authority_event_id="e-3",
                replaced=[{"id": "c-svg", "text": "Deliver SVG.", "supersedes": "c-png"}],
            ),
            event(5, "task.dispositioned", {
                "task_id": "png", "task_revision": 1, "disposition": "superseded",
                "authority_event_id": "e-4", "reason": "PNG is no longer required.",
                "dependent_tasks": [{"task_id": "publish", "treatment": "replanned"}],
            }),
        ]
        publish_replanned = copy.deepcopy(dependent)
        publish_replanned["dependencies"] = []
        rows.append(event(6, "plan.revised", {
            "revision": 2, "reason": "user_amendment", "attempt_limit": 2, "revision_limit": 2,
            "no_progress": "same failure twice", "trigger_event_ids": ["e-4", "e-5"],
            "tasks": [publish_replanned],
        }))
        run, valid = self.result("task-disposition", rows, "snapshot", "--write")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        state = output(valid)
        self.assertEqual(list(state["tasks"]), ["publish"])
        self.assertEqual(state["task_dispositions"][0]["task_id"], "png")
        self.assertEqual(len(state["plan_history"]), 2)

        silent = copy.deepcopy(rows)
        silent[4]["payload"]["dependent_tasks"] = []
        _, rejected = self.result("task-dependent-silent", silent, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "invalid_dependency")

        unresolved = copy.deepcopy(rows[:4])
        unresolved += [
            event(5, "task.admitted", {"task_id": "png", "task_revision": 1, "plan_revision": 1}),
            event(6, "task.result", {
                "task_id": "png", "task_revision": 1, "outcome": "unknown",
                "effect_status": "unknown", "evidence_ids": [],
            }),
            event(7, "task.dispositioned", {
                "task_id": "png", "task_revision": 1, "disposition": "superseded",
                "authority_event_id": "e-4", "reason": "PNG is no longer required.",
                "dependent_tasks": [{"task_id": "publish", "treatment": "replanned"}],
            }),
        ]
        _, rejected = self.result("task-writer-unreconciled", unresolved, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "unknown_effect")

        resurrected = copy.deepcopy(rows)
        resurrected[5]["payload"]["revision_limit"] = 3
        resurrected += [
            event(7, "evidence.recorded", {
                "evidence_id": "ev-new", "criterion_ids": ["c-svg"], "kind": "observation",
                "locator": "scope/new", "sha256": None,
            }),
            event(8, "plan.revised", {
                "revision": 3, "reason": "evidence_change", "attempt_limit": 2, "revision_limit": 3,
                "no_progress": "same failure twice", "trigger_event_ids": ["e-7"],
                "tasks": [publish_replanned, obsolete],
            }),
        ]
        _, rejected = self.result("disposed-task-resurrection", resurrected, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "immutable_history")

    def test_exhausted_approach_can_renew_with_authority_and_global_attempt_history(self) -> None:
        rows, changed = self.failed_initial()
        rows += [
            self.decision(6, hard_caps={"total_attempt_limit": 3, "plan_revision_limit": 3}),
            event(7, "plan.revised", self.renewal(changed)),
        ]
        run, valid = self.result("approach-renewed", rows, "snapshot", "--write")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        state = output(valid)
        self.assertEqual(state["current_approach"], 2)
        self.assertEqual(len(state["approach_history"]), 2)
        self.assertEqual(len(state["attempt_history"]), 1)
        agents = dump(self.root("approach-renewed-agents") / "agents.json", [])
        resumed = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        resumed_state = json.loads((run / "snapshot.json").read_text())
        self.assertEqual(resumed_state["approach_history"][-1]["strategy_change"], "replace the failing implementation")

        completed = copy.deepcopy(rows) + [
            event(8, "task.admitted", {"task_id": "t-1", "task_revision": 2, "plan_revision": 2}),
            event(9, "evidence.recorded", {
                "evidence_id": "ev-pass", "criterion_ids": ["c-1"], "kind": "observation",
                "locator": "checks/pass", "sha256": None,
            }),
            event(10, "task.result", {
                "task_id": "t-1", "task_revision": 2, "outcome": "passed",
                "effect_status": "none", "evidence_ids": ["ev-pass"],
            }),
            event(11, "check.recorded", {
                "check_id": "check-pass", "criterion_ids": ["c-1"], "outcome": "passed",
                "evidence_ids": ["ev-pass"],
            }),
            event(12, "run.closed", {
                "status": "completed", "criterion_evidence": {"c-1": ["ev-pass"]},
                "scope_reconciled": True, "remaining_human_items": [],
            }),
        ]
        report_run, valid = self.result("approach-renewed-report", completed, "report", "--write")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        report = (report_run / "report.md").read_text()
        self.assertIn("Approach 1: plan revision 1 (initial)", report)
        self.assertIn("Approach 2: plan revision 2 (approach_renewal)", report)
        self.assertIn("t-1 revision 1: failed", report)

        missing = copy.deepcopy(rows)
        missing[-1]["payload"]["authority_event_id"] = "missing"
        _, rejected = self.result("renewal-dangling-authority", missing, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "invalid_reference")

        unchanged = copy.deepcopy(rows)
        unchanged[-1]["payload"]["tasks"] = [task("t-1")]
        _, rejected = self.result("renewal-numbers-only", unchanged, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "no_progress")

        rename_rows, _ = self.failed_initial()
        original = rename_rows[1]["payload"]["tasks"][0]
        renamed = copy.deepcopy(original); renamed["id"] = "renamed"
        rename_rows += [
            self.decision(6),
            event(7, "task.dispositioned", {
                "task_id": "t-1", "task_revision": 1, "disposition": "superseded",
                "authority_event_id": "e-6", "reason": "replace failed approach", "dependent_tasks": [],
            }),
            event(8, "plan.revised", {
                **self.renewal(renamed), "authority_event_id": "e-6",
                "trigger_event_ids": ["e-5", "e-6", "e-7"],
            }),
        ]
        _, rejected = self.result("renewal-id-only-rename", rename_rows, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "no_progress")

        expanded = copy.deepcopy(rows[:-1])
        expanded.append(event(7, "plan.revised", self.renewal(changed, revision_limit=3)))
        changed_again = copy.deepcopy(changed); changed_again["revision"] = 2; changed_again["inputs"] = ["third strategy"]
        expanded += [
            event(8, "evidence.recorded", {
                "evidence_id": "ev-new", "criterion_ids": ["c-1"], "kind": "observation",
                "locator": "checks/new-fact", "sha256": None,
            }),
            event(9, "plan.revised", {
                "revision": 3, "reason": "evidence_change", "attempt_limit": 3, "revision_limit": 4,
                "no_progress": "stop after new failure", "trigger_event_ids": ["e-8"], "tasks": [changed_again],
            }),
        ]
        _, rejected = self.result("renewal-allowance-silent-expansion", expanded, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "limit_exceeded")

    def test_renewal_cannot_override_hard_caps_or_rename_around_total_attempts(self) -> None:
        rows, changed = self.failed_initial()
        rows += [
            self.decision(6, hard_caps={"total_attempt_limit": 1, "plan_revision_limit": 1}),
            event(7, "plan.revised", self.renewal(changed)),
        ]
        _, rejected = self.result("renewal-hard-cap", rows, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "limit_exceeded")

        preserved, changed = self.failed_initial()
        preserved += [
            self.decision(6, hard_caps={"total_attempt_limit": 2, "plan_revision_limit": 2}),
            self.decision(7),
            event(8, "plan.revised", {
                **self.renewal(changed, authority="e-7", total_attempt_limit=3),
                "revision_limit": 2,
            }),
        ]
        _, rejected = self.result("renewal-hard-cap-not-erased", preserved, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "limit_exceeded")

        rows, changed = self.failed_initial()
        renamed = task("t-2")
        rows += [
            self.decision(6),
            event(7, "plan.revised", {
                **self.renewal(changed, total_attempt_limit=1),
                "tasks": [changed, renamed],
            }),
            event(8, "task.admitted", {"task_id": "t-2", "task_revision": 1, "plan_revision": 2}),
        ]
        _, rejected = self.result("renewal-global-attempt-cap", rows, "validate")
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "limit_exceeded")

    def test_old_v1_replans_and_two_selection_inventory_survive_resume(self) -> None:
        old = complete_read_run()
        _, valid = self.result("old-v1", old, "validate", "--terminal")
        self.assertEqual(valid.returncode, 0, valid.stderr)

        first = {
            "generation_id": "g-1", "cue_fingerprint": "one", "cues": {"operation": ["resume"]},
            "matches": [{"id": "k-1", "revision": 1, "status": "supported", "reason": "first"}],
            "retrieval_status": "matched",
        }
        second = {
            "generation_id": "g-2", "cue_fingerprint": "two", "cues": {"operation": ["retry"], "include_non_supported": True},
            "matches": [
                {"id": "k-1", "revision": 1, "status": "supported", "reason": "first"},
                {"id": "k-2", "revision": 3, "status": "contested", "reason": "second"},
            ], "retrieval_status": "matched",
        }
        rows = [opened(), event(2, "knowledge.selected", first), event(3, "knowledge.selected", second)]
        run, valid = self.result("selection-inventory", rows, "snapshot", "--write")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        agents = dump(self.root("selection-inventory-agents") / "agents.json", [])
        resumed = invoke(STATE_CLI, "resume", "--run-dir", str(run), "--agents", str(agents))
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        state = json.loads((run / "snapshot.json").read_text())
        self.assertEqual(state["knowledge_selection"], second)
        self.assertEqual(state["knowledge_selected_revisions"], [
            {"id": "k-1", "revision": 1, "generation_id": "g-1", "status": "supported", "reason": "first", "application": "unknown"},
            {"id": "k-1", "revision": 1, "generation_id": "g-2", "status": "supported", "reason": "first", "application": "unknown"},
            {"id": "k-2", "revision": 3, "generation_id": "g-2", "status": "contested", "reason": "second", "application": "unknown"},
        ])


if __name__ == "__main__":
    unittest.main()
