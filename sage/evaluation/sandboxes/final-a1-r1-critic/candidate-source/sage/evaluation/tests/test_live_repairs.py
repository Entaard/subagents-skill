from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from support import EVALUATION, SAGE, STATE_CLI, complete_read_run, dump, event, invoke, opened, sandbox, task, write_log


PAIRING = EVALUATION / "pairing.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LiveRepairStateTests(unittest.TestCase):
    def delegated(self, effect: str = "read") -> dict:
        return task("review", effect, owner="/root/reviewer")

    def base(self, item: dict | None = None, evidence_kind: str = "observation") -> list[dict]:
        assigned = item or self.delegated()
        return [
            opened(),
            event(2, "plan.revised", {
                "revision": 1, "reason": "initial", "attempt_limit": 1,
                "revision_limit": 1, "no_progress": "one bounded dispatch",
                "trigger_event_ids": ["e-1"], "tasks": [assigned],
            }),
            event(3, "task.admitted", {"task_id": assigned["id"], "task_revision": 1, "plan_revision": 1}),
            event(4, "evidence.recorded", {
                "evidence_id": "ev-dispatch", "criterion_ids": [], "kind": evidence_kind,
                "locator": "native-dispatch/rejection.json", "sha256": None,
            }),
        ]

    def not_created(self, sequence: int = 5) -> dict:
        return event(sequence, "agent.not_created", {
            "task_id": "review", "task_revision": 1,
            "reason": "native spawn rejected before returning a handle",
            "evidence_ids": ["ev-dispatch"],
        })

    def assert_rejected(self, root: Path, label: str, rows: list[dict], code: str) -> None:
        run = root / label
        write_log(run, rows)
        result = invoke(STATE_CLI, "validate", "--run-dir", str(run))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stderr)["code"], code)

    def test_known_precreation_failure_reconciles_append_only_history_without_invented_handle(self) -> None:
        with sandbox() as raw:
            run = Path(raw) / "precreation-failure"
            write_log(run, self.base())
            original = (run / "events.jsonl").read_bytes()
            rows = [
                event(5, "agent.not_created", {
                    "task_id": "review", "task_revision": 1,
                    "reason": "native thread-limit rejection returned no handle",
                    "evidence_ids": ["ev-dispatch"],
                }),
                event(6, "task.result", {
                    "task_id": "review", "task_revision": 1, "outcome": "failed",
                    "effect_status": "none", "evidence_ids": ["ev-dispatch"],
                }),
                event(7, "run.closed", {
                    "status": "stopped", "criterion_evidence": {}, "scope_reconciled": False,
                    "remaining_human_items": ["Independent review and integration were not completed in this run."],
                }),
            ]
            wave = run / "repair-wave.jsonl"
            wave.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
            appended = invoke(STATE_CLI, "append", "--run-dir", str(run), "--events", str(wave))
            self.assertEqual(appended.returncode, 0, appended.stderr)
            self.assertTrue((run / "events.jsonl").read_bytes().startswith(original))
            terminal = invoke(STATE_CLI, "validate", "--run-dir", str(run), "--terminal")
            self.assertEqual(terminal.returncode, 0, terminal.stderr)
            report = invoke(STATE_CLI, "report", "--run-dir", str(run), "--write")
            self.assertEqual(report.returncode, 0, report.stderr)
            rendered = (run / "report.md").read_text(encoding="utf-8")
            self.assertIn("Status: stopped", rendered)
            self.assertIn("review: failed", rendered)
            self.assertNotIn("review: passed", rendered)

    def test_no_creation_fact_requires_direct_observation_and_is_single_final_path(self) -> None:
        with sandbox() as raw:
            root = Path(raw)
            missing = self.base() + [self.not_created()]
            missing[-1]["payload"]["evidence_ids"] = ["missing"]
            self.assert_rejected(root, "missing-evidence", missing, "invalid_reference")

            invalid = self.base(evidence_kind="inference") + [self.not_created()]
            self.assert_rejected(root, "invalid-evidence", invalid, "invalid_reference")

            unknown = self.base() + [self.not_created(), event(6, "task.result", {
                "task_id": "review", "task_revision": 1, "outcome": "unknown",
                "effect_status": "unknown", "evidence_ids": ["ev-dispatch"],
            })]
            self.assert_rejected(root, "unknown-outcome", unknown, "invalid_transition")

            missing_result_evidence = self.base() + [self.not_created(), event(6, "task.result", {
                "task_id": "review", "task_revision": 1, "outcome": "failed",
                "effect_status": "none", "evidence_ids": [],
            })]
            self.assert_rejected(root, "missing-result-evidence", missing_result_evidence, "invalid_reference")

            duplicate = self.base() + [self.not_created(), self.not_created(6)]
            self.assert_rejected(root, "duplicate", duplicate, "invalid_transition")

            failed = self.base() + [self.not_created(), event(6, "task.result", {
                "task_id": "review", "task_revision": 1, "outcome": "failed",
                "effect_status": "none", "evidence_ids": ["ev-dispatch"],
            })]
            final = failed + [event(7, "task.result", {
                "task_id": "review", "task_revision": 1, "outcome": "passed",
                "effect_status": "none", "evidence_ids": ["ev-dispatch"],
            })]
            self.assert_rejected(root, "final-outcome", final, "invalid_transition")

            fake_complete = self.base()
            fake_complete[3]["payload"]["criterion_ids"] = ["c-1"]
            fake_complete += [self.not_created(), event(6, "task.result", {
                "task_id": "review", "task_revision": 1, "outcome": "failed",
                "effect_status": "none", "evidence_ids": ["ev-dispatch"],
            }), event(7, "check.recorded", {"check_id": "check-1", "criterion_ids": ["c-1"],
                  "outcome": "passed", "evidence_ids": ["ev-dispatch"]}),
                event(8, "run.closed", {"status": "completed", "criterion_evidence": {"c-1": ["ev-dispatch"]},
                      "scope_reconciled": True, "remaining_human_items": []})]
            self.assert_rejected(root, "fake-completed-run", fake_complete, "incomplete_run")

    def test_no_creation_cannot_bypass_real_assignments_root_ownership_or_bounds(self) -> None:
        with sandbox() as raw:
            root = Path(raw)
            requested = self.base() + [event(5, "agent.requested", {
                "task_id": "review", "handle": "/root/reviewer", "requested_model": "gpt-5.6-sol",
                "requested_effort": "high", "fork_turns": "none",
            }), self.not_created(6)]
            self.assert_rejected(root, "post-request", requested, "invalid_transition")

            root_task = task("review", owner="root")
            self.assert_rejected(root, "root-owner", self.base(root_task) + [self.not_created()], "invalid_transition")

            no_fact = self.base() + [event(5, "task.result", {
                "task_id": "review", "task_revision": 1, "outcome": "failed",
                "effect_status": "none", "evidence_ids": ["ev-dispatch"],
            })]
            self.assert_rejected(root, "unknown-creation", no_fact, "invalid_transition")

            failed = self.base() + [self.not_created(), event(6, "task.result", {
                "task_id": "review", "task_revision": 1, "outcome": "failed",
                "effect_status": "none", "evidence_ids": ["ev-dispatch"],
            })]
            revision = copy.deepcopy(failed[1]["payload"])
            revision.update({"revision": 2, "reason": "failure", "trigger_event_ids": ["e-4"],
                             "unmet_criterion": "c-1", "failure_evidence_ids": ["ev-dispatch"],
                             "cause": "environment_or_tool", "strategy_change": "use a distinct reviewer"})
            revision["tasks"][0]["revision"] = 2
            revision["tasks"][0]["owner"] = "/root/other-reviewer"
            self.assert_rejected(root, "revision-bound", failed + [event(7, "plan.revised", revision)], "limit_exceeded")

            dependent = task("integrate", dependencies=["review"])
            dependency_rows = self.base()
            dependency_rows[1]["payload"]["tasks"].append(dependent)
            dependency_rows += [self.not_created(), event(6, "task.result", {
                "task_id": "review", "task_revision": 1, "outcome": "failed",
                "effect_status": "none", "evidence_ids": ["ev-dispatch"],
            }), event(7, "task.admitted", {"task_id": "integrate", "task_revision": 1, "plan_revision": 1})]
            self.assert_rejected(root, "dependency-bound", dependency_rows, "dependency_blocked")

            attempt_rows = self.base()
            attempt_rows[1]["payload"]["revision_limit"] = 2
            attempt_rows += [self.not_created(), event(6, "task.result", {
                "task_id": "review", "task_revision": 1, "outcome": "failed",
                "effect_status": "none", "evidence_ids": ["ev-dispatch"],
            })]
            attempt_revision = copy.deepcopy(attempt_rows[1]["payload"])
            attempt_revision.update({"revision": 2, "reason": "failure", "trigger_event_ids": ["e-4"],
                                     "unmet_criterion": "c-1", "failure_evidence_ids": ["ev-dispatch"],
                                     "cause": "environment_or_tool", "strategy_change": "use a distinct reviewer"})
            attempt_revision["tasks"][0]["revision"] = 2
            attempt_revision["tasks"][0]["owner"] = "/root/other-reviewer"
            attempt_rows += [event(7, "plan.revised", attempt_revision),
                             event(8, "task.admitted", {"task_id": "review", "task_revision": 2, "plan_revision": 2})]
            self.assert_rejected(root, "attempt-bound", attempt_rows, "limit_exceeded")

    def test_later_bounded_revision_can_succeed_after_known_noncreation(self) -> None:
        rows = self.base()
        rows[1]["payload"].update({"attempt_limit": 2, "revision_limit": 2})
        rows += [self.not_created(), event(6, "task.result", {
            "task_id": "review", "task_revision": 1, "outcome": "failed",
            "effect_status": "none", "evidence_ids": ["ev-dispatch"],
        })]
        revised = copy.deepcopy(rows[1]["payload"])
        revised.update({"revision": 2, "reason": "failure", "trigger_event_ids": ["e-4"],
                        "unmet_criterion": "c-1", "failure_evidence_ids": ["ev-dispatch"],
                        "cause": "environment_or_tool", "strategy_change": "use a distinct available reviewer"})
        revised["tasks"][0].update({"revision": 2, "owner": "/root/reviewer-2"})
        rows += [
            event(7, "plan.revised", revised),
            event(8, "task.admitted", {"task_id": "review", "task_revision": 2, "plan_revision": 2}),
            event(9, "agent.requested", {"task_id": "review", "handle": "/root/reviewer-2",
                  "requested_model": "gpt-5.6-sol", "requested_effort": "high", "fork_turns": "none"}),
            event(10, "evidence.recorded", {"evidence_id": "ev-success", "criterion_ids": ["c-1"],
                  "kind": "observation", "locator": "review/success.md", "sha256": None}),
            event(11, "task.result", {"task_id": "review", "task_revision": 2, "outcome": "passed",
                  "effect_status": "none", "evidence_ids": ["ev-success"]}),
            event(12, "agent.observed", {"handle": "/root/reviewer-2", "lifecycle": "completed",
                  "effect_status": "reconciled", "effective_model": None, "effective_effort": None}),
            event(13, "check.recorded", {"check_id": "check-1", "criterion_ids": ["c-1"],
                  "outcome": "passed", "evidence_ids": ["ev-success"]}),
            event(14, "run.closed", {"status": "completed", "criterion_evidence": {"c-1": ["ev-success"]},
                  "scope_reconciled": True, "remaining_human_items": []}),
        ]
        with sandbox() as raw:
            run = Path(raw) / "bounded-recovery"
            write_log(run, rows)
            result = invoke(STATE_CLI, "validate", "--run-dir", str(run), "--terminal")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_report_qualifies_empty_sections_and_renders_stored_native_unknowns(self) -> None:
        assigned = self.delegated()
        rows = self.base(assigned)
        rows[3]["payload"]["criterion_ids"] = ["c-1"]
        rows += [
            event(5, "agent.requested", {
                "task_id": "review", "handle": "/root/reviewer", "requested_model": "gpt-5.6-sol",
                "requested_effort": "high", "fork_turns": "none",
            }),
            event(6, "task.result", {
                "task_id": "review", "task_revision": 1, "outcome": "passed",
                "effect_status": "none", "evidence_ids": ["ev-dispatch"],
            }),
            event(7, "agent.observed", {
                "handle": "/root/reviewer", "lifecycle": "completed", "effect_status": "reconciled",
                "effective_model": None, "effective_effort": None,
            }),
            event(8, "check.recorded", {
                "check_id": "check-1", "criterion_ids": ["c-1"], "outcome": "passed",
                "evidence_ids": ["ev-dispatch"],
            }),
            event(9, "run.closed", {
                "status": "completed", "criterion_evidence": {"c-1": ["ev-dispatch"]},
                "scope_reconciled": True, "remaining_human_items": [],
            }),
        ]
        with sandbox() as raw:
            run = Path(raw) / "native-unknowns"
            write_log(run, rows)
            result = invoke(STATE_CLI, "report", "--run-dir", str(run), "--write")
            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = (run / "report.md").read_text(encoding="utf-8")
            self.assertNotIn("## Unknowns\n\n- None", rendered)
            self.assertNotIn("## Untested evidence\n\n- None", rendered)
            self.assertIn("/root/reviewer: effective_model=unknown, effective_effort=unknown", rendered)
            self.assertIn("## Untested evidence\n\n- No entries recorded.", rendered)

    def test_report_renders_actual_typed_unknown_and_untested_entries(self) -> None:
        rows = complete_read_run()[:-1]
        rows += [
            event(8, "evidence.recorded", {
                "evidence_id": "ev-unknown", "criterion_ids": [], "kind": "unknown",
                "locator": "telemetry/effective-model-unobserved", "sha256": None,
            }),
            event(9, "evidence.recorded", {
                "evidence_id": "ev-untested", "criterion_ids": ["c-1"], "kind": "untested",
                "locator": "experience/screen-reader-not-tested", "sha256": None,
            }),
            event(10, "run.closed", {
                "status": "completed", "criterion_evidence": {"c-1": ["ev-1"]},
                "scope_reconciled": True, "remaining_human_items": [],
            }),
        ]
        with sandbox() as raw:
            run = Path(raw) / "typed-negative-evidence"
            write_log(run, rows)
            result = invoke(STATE_CLI, "report", "--run-dir", str(run), "--write")
            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = (run / "report.md").read_text(encoding="utf-8")
            self.assertIn("telemetry/effective-model-unobserved", rendered)
            self.assertIn("experience/screen-reader-not-tested", rendered)


class NativeResultProtocolTests(unittest.TestCase):
    def invoke_pairing(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(PAIRING), *args], cwd=EVALUATION.parent.parent,
                              text=True, capture_output=True, check=False)

    def native_results(self, root: Path, frozen: dict) -> dict:
        pairs = []
        for fixed in frozen["pairs"]:
            arms = {}
            for arm_name in ("treatment", "baseline"):
                evidence = []
                for evidence_id, kind, content, provenance in (
                    ("journal", "journal", "Authored run journal.\n", "Actor-authored journal; not a raw transcript."),
                    ("artifact", "artifact", "candidate output\n", None),
                    ("scorecard", "scorecard", "scored output\n", None),
                    ("native", "native_observation", '{"lifecycle":"completed"}\n', "Direct normalized outer lifecycle observation."),
                    ("command", "artifact", "verification command exited 0\n", "Captured subprocess output."),
                ):
                    path = root / f"{fixed['case_id']}-{arm_name}-{evidence_id}.txt"
                    path.write_text(content, encoding="utf-8")
                    item = {"id": evidence_id, "kind": kind, "path": str(path), "sha256": sha256(path)}
                    if provenance is not None:
                        item["provenance"] = provenance
                    evidence.append(item)
                execution = {
                    "mode": "native_collaboration", "run_id": f"{fixed['case_id']}-{arm_name}",
                    "started_at": "2026-09-08T00:00:00Z", "finished_at": "2026-09-08T00:01:00Z",
                    "completion": {"lifecycle": "completed", "native_exit_code": None,
                                   "evidence_refs": ["native"], "exit_evidence_refs": []},
                    "commands": [{"id": "verification", "exit_code": 0, "evidence_refs": ["command"]}],
                    "evidence": evidence,
                }
                arms[arm_name] = {
                    "execution": execution,
                    "routing": {"root_model_requested": "gpt-6-astra", "root_model_effective": None,
                                "eligible_worker_policy": frozen["arms"][arm_name]["eligible_worker_policy"], "workers": []},
                    "checks": [{"id": check_id, "outcome": "passed", "evidence_refs": ["artifact"]}
                               for check_id in fixed["check_ids"]],
                    "scores": {name: {"value": 8.5, "evidence_refs": ["scorecard"]} for name in fixed["dimensions"]},
                    "scorer": {"id": "independent-scorer", "independent": True, "evidence_refs": ["scorecard"]},
                    "actor_calls": 1, "wall_seconds": 60.0, "operational_evidence_refs": ["native"],
                    "reported_tokens": None, "reported_money": None,
                }
            pairs.append({"case_id": fixed["case_id"], "case_binding_sha256": fixed["case_binding_sha256"],
                          "order": fixed["order"], **arms})
        return {"schema_version": "sage-live-native-scored-results-v3",
                "frozen_manifest_sha256": frozen["manifest_sha256"], "pairs": pairs}

    def test_public_cli_accepts_evidenced_native_completion_and_separate_command_exit(self) -> None:
        with sandbox() as raw:
            root = Path(raw); manifest = root / "manifest.json"
            prepared = self.invoke_pairing("prepare", str(EVALUATION / "cases/development-selection.json"),
                                           "--output", str(manifest))
            self.assertEqual(prepared.returncode, 0, prepared.stderr)
            frozen = json.loads(manifest.read_text(encoding="utf-8"))
            result_path = dump(root / "native-results.json", self.native_results(root, frozen))
            checked = self.invoke_pairing("validate-native", str(result_path), "--manifest", str(manifest))
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(json.loads(checked.stdout)["result_schema"], "sage-live-native-scored-results-v3")

    def test_public_cli_rejects_absent_invented_or_contradictory_native_completion(self) -> None:
        with sandbox() as raw:
            root = Path(raw); manifest = root / "manifest.json"
            self.assertEqual(self.invoke_pairing("prepare", str(EVALUATION / "cases/development-selection.json"),
                                                 "--output", str(manifest)).returncode, 0)
            frozen = json.loads(manifest.read_text(encoding="utf-8")); control = self.native_results(root, frozen)
            mutations = {}
            absent = copy.deepcopy(control); absent["pairs"][0]["treatment"]["execution"]["completion"]["evidence_refs"] = []
            mutations["absent"] = absent
            invented = copy.deepcopy(control); invented["pairs"][0]["treatment"]["execution"]["completion"]["native_exit_code"] = 0
            mutations["invented-exit"] = invented
            contradictory = copy.deepcopy(control); contradictory["pairs"][0]["treatment"]["execution"]["completion"]["lifecycle"] = "failed"
            mutations["contradictory"] = contradictory
            journal = copy.deepcopy(control); journal["pairs"][0]["treatment"]["execution"]["completion"]["evidence_refs"] = ["journal"]
            mutations["journal-is-not-native"] = journal
            for label, value in mutations.items():
                with self.subTest(label=label):
                    path = dump(root / f"{label}.json", value)
                    checked = self.invoke_pairing("validate-native", str(path), "--manifest", str(manifest))
                    self.assertEqual(checked.returncode, 2, checked.stderr)
                    self.assertTrue(checked.stderr.strip().startswith("{"), checked.stderr)

    def test_public_cli_rejects_invalid_native_execution_shape_and_identity_types(self) -> None:
        with sandbox() as raw:
            root = Path(raw); manifest = root / "manifest.json"
            self.assertEqual(self.invoke_pairing("prepare", str(EVALUATION / "cases/development-selection.json"),
                                                 "--output", str(manifest)).returncode, 0)
            frozen = json.loads(manifest.read_text(encoding="utf-8")); control = self.native_results(root, frozen)
            mutations = {}
            run_id = copy.deepcopy(control); run_id["pairs"][0]["treatment"]["execution"]["run_id"] = True
            mutations["run-id-bool"] = run_id
            started = copy.deepcopy(control); started["pairs"][0]["treatment"]["execution"]["started_at"] = True
            mutations["started-at-bool"] = started
            finished = copy.deepcopy(control); finished["pairs"][0]["treatment"]["execution"]["finished_at"] = {"unknown": True}
            mutations["finished-at-object"] = finished
            execution = copy.deepcopy(control); execution["pairs"][0]["treatment"]["execution"] = None
            mutations["execution-null"] = execution
            for label, value in mutations.items():
                with self.subTest(label=label):
                    path = dump(root / f"{label}.json", value)
                    checked = self.invoke_pairing("validate-native", str(path), "--manifest", str(manifest))
                    self.assertEqual(checked.returncode, 2, checked.stderr)
                    self.assertTrue(checked.stderr.strip().startswith("{"), checked.stderr)
                    self.assertNotIn("Traceback", checked.stderr)

    def test_public_cli_rejects_nonobject_native_result_pair_and_arm(self) -> None:
        with sandbox() as raw:
            root = Path(raw); manifest = root / "manifest.json"
            self.assertEqual(self.invoke_pairing("prepare", str(EVALUATION / "cases/development-selection.json"),
                                                 "--output", str(manifest)).returncode, 0)
            frozen = json.loads(manifest.read_text(encoding="utf-8")); control = self.native_results(root, frozen)
            pair = copy.deepcopy(control); pair["pairs"][0] = None
            arm = copy.deepcopy(control); arm["pairs"][0]["treatment"] = None
            for label, value in {"result-null": None, "pair-null": pair, "arm-null": arm}.items():
                with self.subTest(label=label):
                    path = dump(root / f"{label}.json", value)
                    checked = self.invoke_pairing("validate-native", str(path), "--manifest", str(manifest))
                    self.assertEqual(checked.returncode, 2, checked.stderr)
                    self.assertTrue(checked.stderr.strip().startswith("{"), checked.stderr)
                    self.assertNotIn("Traceback", checked.stderr)

    def test_public_cli_retains_native_numeric_provenance_and_reference_negatives(self) -> None:
        with sandbox() as raw:
            root = Path(raw); manifest = root / "manifest.json"
            self.assertEqual(self.invoke_pairing("prepare", str(EVALUATION / "cases/development-selection.json"),
                                                 "--output", str(manifest)).returncode, 0)
            frozen = json.loads(manifest.read_text(encoding="utf-8")); control = self.native_results(root, frozen)
            mutations = {}
            native_bool = copy.deepcopy(control)
            native_bool["pairs"][0]["treatment"]["execution"]["completion"].update(
                {"native_exit_code": True, "exit_evidence_refs": ["native"]})
            mutations["native-bool-exit"] = native_bool
            native_float = copy.deepcopy(control)
            native_float["pairs"][0]["treatment"]["execution"]["completion"].update(
                {"native_exit_code": 0.0, "exit_evidence_refs": ["native"]})
            mutations["native-float-exit"] = native_float
            command_bool = copy.deepcopy(control)
            command_bool["pairs"][0]["treatment"]["execution"]["commands"][0]["exit_code"] = True
            mutations["command-bool-exit"] = command_bool
            command_string = copy.deepcopy(control)
            command_string["pairs"][0]["treatment"]["execution"]["commands"][0]["exit_code"] = "0"
            mutations["command-string-exit"] = command_string
            provenance = copy.deepcopy(control)
            del provenance["pairs"][0]["treatment"]["execution"]["evidence"][3]["provenance"]
            mutations["native-missing-provenance"] = provenance
            dangling = copy.deepcopy(control)
            dangling["pairs"][0]["treatment"]["execution"]["commands"][0]["evidence_refs"] = ["missing"]
            mutations["command-dangling-evidence"] = dangling
            for label, value in mutations.items():
                with self.subTest(label=label):
                    path = dump(root / f"{label}.json", value)
                    checked = self.invoke_pairing("validate-native", str(path), "--manifest", str(manifest))
                    self.assertEqual(checked.returncode, 2, checked.stderr)
                    self.assertTrue(checked.stderr.strip().startswith("{"), checked.stderr)
                    self.assertNotIn("Traceback", checked.stderr)

    def test_frozen_v2_sources_and_original_validator_rejection_remain_unchanged(self) -> None:
        paths = {
            EVALUATION / "live-protocol.md": "8726a8fd00e48c074372609f90de562659012037a38461aefb91e1a958bf0c77",
            EVALUATION / "rubric.json": "6abd4368dd443b8cd1cf10515638500bb849e59833764622348070382b2c8d16",
        }
        for path, expected in paths.items():
            self.assertEqual(sha256(path), expected)
        with sandbox() as raw:
            root = Path(raw); manifest = root / "manifest.json"
            self.assertEqual(self.invoke_pairing("prepare", str(EVALUATION / "cases/development-selection.json"),
                                                 "--output", str(manifest)).returncode, 0)
            frozen = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(Path(frozen["shared"]["protocol"]["path"]).resolve(), (EVALUATION / "live-protocol.md").resolve())
            self.assertEqual(Path(frozen["shared"]["rubric"]["path"]).resolve(), (EVALUATION / "rubric.json").resolve())
            legacy = self.native_results(root, frozen)
            legacy["schema_version"] = "sage-live-native-scored-results-v1"
            for pair in legacy["pairs"]:
                for arm_name in ("treatment", "baseline"):
                    execution = pair[arm_name]["execution"]
                    execution.update({"status": "completed", "exit_code": None})
                    for evidence in execution["evidence"]:
                        if evidence["kind"] == "journal": evidence["kind"] = "transcript"
                        if evidence["kind"] == "native_observation": evidence["kind"] = "artifact"
            result_path = dump(root / "legacy-native-null.json", legacy)
            checked = self.invoke_pairing("validate", str(result_path), "--manifest", str(manifest))
            self.assertEqual(checked.returncode, 2)
            self.assertIn("lacks completed transcript evidence", checked.stderr)


class InstalledStateContractTests(unittest.TestCase):
    def test_installed_note_enum_and_published_example_work_without_source_helper(self) -> None:
        with sandbox() as raw:
            root = Path(raw); target = root / "target"
            installed = subprocess.run(["bash", str(SAGE / "install.sh"), "--target-root", str(target)],
                                       cwd=SAGE.parent, text=True, capture_output=True, check=False)
            self.assertEqual(installed.returncode, 0, installed.stderr)
            contract_path = target / "skills/sage/references/state.md"
            contract = contract_path.read_text(encoding="utf-8")
            self.assertIn("`assumption|decision`", contract)
            self.assertIn("note-example.json", contract)

            state_cli = target / "sage/bin/sage_state.py"
            criteria = dump(root / "criteria.json", [{"id": "c-1", "text": "Record a bounded decision."}])
            run = root / "run"
            created = invoke(state_cli, "init", "--run-dir", str(run), "--run-id", "note-doc-example",
                             "--objective", "exercise the installed note contract", "--criteria", str(criteria))
            self.assertEqual(created.returncode, 0, created.stderr)
            before = (run / "events.jsonl").read_bytes()
            rejected_path = dump(root / "old-rejected-note.json", event(2, "note.recorded", {
                "category": "reconciliation", "text": "This historical category is outside the contract.",
                "evidence_ids": [], "corrects_event_id": None,
            }, run_id="note-doc-example"))
            rejected = invoke(state_cli, "append", "--run-dir", str(run), "--event", str(rejected_path))
            self.assertEqual(rejected.returncode, 2, rejected.stderr)
            self.assertEqual((run / "events.jsonl").read_bytes(), before)

            note_path = dump(root / "note-example.json", event(2, "note.recorded", {
                "category": "decision", "text": "Use the published event vocabulary.",
                "evidence_ids": [], "corrects_event_id": None,
            }, run_id="note-doc-example"))
            accepted = invoke(state_cli, "append", "--run-dir", str(run), "--event", str(note_path))
            self.assertEqual(accepted.returncode, 0, accepted.stderr)


if __name__ == "__main__":
    unittest.main()
