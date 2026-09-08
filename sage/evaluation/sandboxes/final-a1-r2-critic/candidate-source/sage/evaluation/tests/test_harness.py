from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

EVALUATION = Path(__file__).resolve().parents[1]; SAGE = EVALUATION.parent
import sys
sys.path.insert(0, str(EVALUATION))
from pairing import prepare, sha256, validate_frozen, validate_result  # noqa: E402
from score_status import append_review, load_json, validate_review  # noqa: E402
from support import complete_read_run, event_reference_issues, strict_event_mutations, strict_json_loads  # noqa: E402


class HarnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rubric = load_json(EVALUATION / "rubric.json")

    def valid_review(self, verdict: str = "pass", round_number: int = 1) -> dict:
        scores = {name: 8.5 for name in self.rubric["required_status_dimensions"]}
        errors: list[str] = []
        if verdict == "fail": scores[next(iter(scores))] = 7; errors = ["E-1"]
        return {"module": "verification", "approach_id": "verification-a1", "round": round_number,
                "review_id": f"verification-a1-r{round_number}", "reviewed_at": f"2026-09-07T00:0{round_number}:00Z",
                "gate_type": "verification_design_and_harness", "verdict": verdict, "scores": scores,
                "score_evidence": {name: {"reason": "directly inspected", "evidence": ["sage/docs/CONTRACTS.md"]} for name in scores},
                "open_error_ids": errors}

    def status(self) -> dict:
        return {"updated_at": "", "active_module": "verification", "module_order": ["architecture", "verification", "sage", "promotion", "integration", "final"],
                "quality_gate": {"maximum_rounds_per_approach": 4}, "history": [],
                "modules": {"architecture": {"gate": "passed"},
                            "verification": {"depends_on": ["architecture"], "active_approach_id": "verification-a1", "status": "awaiting_review", "gate": "pending_review", "scores": None, "open_errors": [], "approaches": [{"approach_id": "verification-a1", "summary": "", "rounds": []}], "pending_review": {"approach_id": "verification-a1", "round": 1, "gate_type": "verification_design_and_harness"}},
                            "sage": {"depends_on": ["verification"], "gate": "not_evaluated"}, "promotion": {"depends_on": ["sage"], "gate": "not_evaluated"},
                            "integration": {"depends_on": ["promotion"], "gate": "not_evaluated"}, "final": {"depends_on": ["integration"], "gate": "not_evaluated"}}}

    def test_frozen_assets_and_trace_are_complete(self) -> None:
        cases = load_json(EVALUATION / "cases/development.json")["cases"]; self.assertEqual(len({row["id"] for row in cases}), len(cases))
        holdout = load_json(EVALUATION / "holdout-boundary.json"); self.assertTrue(holdout["frozen_before_product_outcomes"]); self.assertIn("expected answer", holdout["withheld_from_actor"])
        protocol = (EVALUATION / "live-protocol.md").read_text(encoding="utf-8"); self.assertIn("Worker routing is the only intended difference", protocol)
        requirements = (SAGE / "docs/REQUIREMENTS.md").read_text(encoding="utf-8"); trace = load_json(EVALUATION / "requirements-trace.json")
        for row in trace["executable"] + trace["live_only"]:
            self.assertIn(f"**{row['requirement']} ", requirements); self.assertTrue(row["evidence"])

    def test_score_validator_rejects_omitted_null_nonfinite_false_pass_and_missing_evidence(self) -> None:
        valid = self.valid_review(); validate_review(valid, self.rubric); mutations = []
        omitted = copy.deepcopy(valid); omitted["scores"].pop(next(iter(omitted["scores"]))); mutations.append(omitted)
        null = copy.deepcopy(valid); null["scores"][next(iter(null["scores"]))] = None; mutations.append(null)
        nan = copy.deepcopy(valid); nan["scores"][next(iter(nan["scores"]))] = float("nan"); mutations.append(nan)
        low = copy.deepcopy(valid); low["scores"][next(iter(low["scores"]))] = 8.4; mutations.append(low)
        no_evidence = copy.deepcopy(valid); no_evidence.pop("score_evidence"); mutations.append(no_evidence)
        for review in mutations:
            with self.subTest(review=review), self.assertRaises((ValueError, KeyError)): validate_review(review, self.rubric)

    def test_score_json_loader_rejects_duplicate_and_nonfinite_data(self) -> None:
        sandbox = Path(os.environ["SAGE_EVALUATION_SANDBOX"])
        with tempfile.TemporaryDirectory(dir=sandbox) as raw:
            for index, payload in enumerate(('{"scores":{},"scores":{}}', '{"scores":{"x":NaN}}')):
                path = Path(raw) / f"bad-{index}.json"; path.write_text(payload, encoding="utf-8")
                with self.assertRaises(ValueError): load_json(path)

    def test_strict_product_fixture_oracle_has_an_accepted_control_and_single_parser_mutations(self) -> None:
        control, mutations = strict_event_mutations(); parsed = strict_json_loads(control)
        self.assertEqual(parsed["type"], "run.opened"); self.assertEqual(set(mutations), {"duplicate", "nonfinite"})
        for payload in mutations.values():
            with self.assertRaises(ValueError): strict_json_loads(payload)

    def test_namespaced_positive_source_fixture_has_reference_closure(self) -> None:
        rows = complete_read_run("source-1"); self.assertEqual(event_reference_issues(rows), [])
        self.assertEqual(rows[1]["payload"]["trigger_event_ids"], ["source-1-e-1"])

    def test_fail_fail_pass_preserves_unresolved_then_closed_error_history(self) -> None:
        status = self.status(); failed = self.valid_review("fail", 1); updated = append_review(status, failed)
        self.assertEqual(updated["modules"]["verification"]["approaches"][0]["rounds"][0]["verdict"], "fail")
        updated["modules"]["verification"]["pending_review"] = {"approach_id": "verification-a1", "round": 2, "gate_type": "verification_design_and_harness"}
        failed_again = self.valid_review("fail", 2); failed_again["finding_dispositions"] = [{"id": "E-1", "status": "open", "evidence": ["sage/docs/CONTRACTS.md"]}]
        updated = append_review(updated, failed_again); self.assertEqual(updated["modules"]["verification"]["open_errors"], ["E-1"])
        updated["modules"]["verification"]["pending_review"] = {"approach_id": "verification-a1", "round": 3, "gate_type": "verification_design_and_harness"}
        passed = self.valid_review("pass", 3); passed["finding_dispositions"] = [{"id": "E-1", "status": "verified_fixed", "evidence": ["sage/docs/CONTRACTS.md"]}]
        final = append_review(updated, passed); rounds = final["modules"]["verification"]["approaches"][0]["rounds"]
        self.assertEqual([row["verdict"] for row in rounds], ["fail", "fail", "pass"]); self.assertIsNone(final["modules"]["verification"]["pending_review"])
        self.assertEqual(final["active_module"], "sage"); self.assertIn("Begin sage builder", final["next_action"])

    def test_disposition_consistency_duplicates_and_round_four_replan(self) -> None:
        base = append_review(self.status(), self.valid_review("fail", 1)); base["modules"]["verification"]["pending_review"] = {"approach_id": "verification-a1", "round": 2, "gate_type": "verification_design_and_harness"}
        inconsistent = self.valid_review("fail", 2); inconsistent["finding_dispositions"] = [{"id": "E-1", "status": "verified_fixed", "evidence": ["sage/docs/CONTRACTS.md"]}]
        with self.assertRaises(ValueError): append_review(base, inconsistent)
        duplicate = self.valid_review("fail", 2); duplicate["finding_dispositions"] = [{"id": "E-1", "status": "open", "evidence": ["sage/docs/CONTRACTS.md"]}] * 2
        with self.assertRaises(ValueError): append_review(base, duplicate)
        fourth = self.status(); target = fourth["modules"]["verification"]; target["approaches"][0]["rounds"] = [{"round": i, "review_id": f"old-{i}"} for i in range(1, 4)]; target["pending_review"]["round"] = 4
        result = append_review(fourth, self.valid_review("fail", 4)); self.assertIn("materially changed approach at round 1", result["next_action"])

    def test_status_gate_rejects_pending_dependencies_repeated_round_fifth_round_and_undispositioned_errors(self) -> None:
        repeated_status = self.status(); repeated_status["modules"]["verification"]["approaches"][0]["rounds"] = [{"round": 1, "review_id": "old"}]
        with self.assertRaises(ValueError): append_review(repeated_status, self.valid_review("pass", 1))
        fifth = self.status(); fifth["modules"]["verification"]["approaches"][0]["rounds"] = [{"round": i, "review_id": f"old-{i}"} for i in range(1, 5)]; fifth["modules"]["verification"]["pending_review"]["round"] = 5
        with self.assertRaises(ValueError): append_review(fifth, self.valid_review("pass", 5))
        pending = self.status(); pending["active_module"] = "final"; pending["modules"]["final"].update({"active_approach_id": "final-a1", "approaches": [{"approach_id": "final-a1", "rounds": []}], "pending_review": {"approach_id": "final-a1", "round": 1, "gate_type": "final"}})
        review = self.valid_review(); review.update({"module": "final", "approach_id": "final-a1", "gate_type": "final", "review_id": "final-r1"})
        with self.assertRaises(ValueError): append_review(pending, review)
        unresolved = self.status(); unresolved["modules"]["verification"]["open_errors"] = ["OLD"]
        with self.assertRaises(ValueError): append_review(unresolved, self.valid_review())

    def _unseen_selection(self, root: Path) -> Path:
        for name, content in (("prompt.txt", "Unseen bounded task"), ("input.txt", "raw input"), ("protocol.md", "same procedure")):
            (root / name).write_text(content, encoding="utf-8")
        (root / "rubric.json").write_text(json.dumps(self.rubric), encoding="utf-8"); (root / "environment.json").write_text('{}\n', encoding="utf-8")
        (root / "checks.json").write_text(json.dumps({"checks": [{"id": "check-1"}], "dimensions": self.rubric["required_case_dimensions"], "not_applicable": {"artifact_experience": "No perceptual artifact.", "recovery_behavior": "No recovery scenario.", "knowledge_behavior": "No promotion scenario."}}), encoding="utf-8")
        selection = {"schema_version": "sage-case-selection-v1", "rubric": "rubric.json", "protocol": "protocol.md", "environment": "environment.json", "root_model": "gpt-6-astra", "root_procedure": "installed_sage", "cases": [{"case_id": "UNSEEN-1", "kind": "code", "prompt": "prompt.txt", "inputs": ["input.txt"], "checks": "checks.json"}]}
        path = root / "selection.json"; path.write_text(json.dumps(selection), encoding="utf-8"); return path

    def _results(self, root: Path, frozen: dict) -> dict:
        pairs = []
        for fixed in frozen["pairs"]:
            arms = {}
            for arm_name in ("treatment", "baseline"):
                transcript = root / f"{fixed['case_id']}-{arm_name}-transcript.jsonl"; transcript.write_text('{"event":"completed"}\n', encoding="utf-8")
                scorecard = root / f"{fixed['case_id']}-{arm_name}-score.json"; scorecard.write_text('{"scored":true}\n', encoding="utf-8")
                artifact_path = root / f"{fixed['case_id']}-{arm_name}-artifact.txt"; artifact_path.write_text("candidate output", encoding="utf-8")
                evidence = [{"id": "transcript", "kind": "transcript", "path": str(transcript), "sha256": sha256(transcript)}, {"id": "artifact", "kind": "artifact", "path": str(artifact_path), "sha256": sha256(artifact_path)}, {"id": "scorecard", "kind": "scorecard", "path": str(scorecard), "sha256": sha256(scorecard)}]
                arms[arm_name] = {"execution": {"run_id": f"{fixed['case_id']}-{arm_name}", "status": "completed", "started_at": "2026-09-07T00:00:00Z", "finished_at": "2026-09-07T00:01:00Z", "exit_code": 0, "evidence": evidence}, "routing": {"root_model_requested": "gpt-6-astra", "root_model_effective": None, "eligible_worker_policy": frozen["arms"][arm_name]["eligible_worker_policy"], "workers": []}, "checks": [{"id": item, "outcome": "passed", "evidence_refs": ["transcript", "artifact"]} for item in fixed["check_ids"]], "scores": {name: {"value": 8.5, "evidence_refs": ["scorecard"]} for name in fixed["dimensions"]}, "scorer": {"id": "independent-scorer", "independent": True, "evidence_refs": ["scorecard"]}, "actor_calls": 1, "wall_seconds": 60.0, "operational_evidence_refs": ["transcript"], "reported_tokens": None, "reported_money": None}
            pairs.append({"case_id": fixed["case_id"], "case_binding_sha256": fixed["case_binding_sha256"], "order": fixed["order"], **arms})
        return {"frozen_manifest_sha256": frozen["manifest_sha256"], "pairs": pairs}

    def test_unseen_manifest_evidence_binding_tamper_rejection_and_unknown_cost(self) -> None:
        sandbox = Path(os.environ["SAGE_EVALUATION_SANDBOX"])
        with tempfile.TemporaryDirectory(dir=sandbox) as raw:
            root = Path(raw); selection = self._unseen_selection(root); frozen = prepare(selection); results = self._results(root, frozen)
            self.assertEqual(validate_result(results, frozen)["pair_count"], 1)
            score_only = copy.deepcopy(results); score_only["pairs"][0]["treatment"]["execution"]["evidence"] = []
            with self.assertRaises(ValueError): validate_result(score_only, frozen)
            (root / "prompt.txt").write_text("tampered", encoding="utf-8")
            with self.assertRaises(ValueError): validate_frozen(frozen)

    def test_real_rubric_dimension_omission_and_unknown_dimension_cannot_freeze(self) -> None:
        sandbox = Path(os.environ["SAGE_EVALUATION_SANDBOX"])
        with tempfile.TemporaryDirectory(dir=sandbox) as raw:
            root = Path(raw); selection = self._unseen_selection(root); checks_path = root / "checks.json"; valid = json.loads(checks_path.read_text())
            missing = copy.deepcopy(valid); missing["dimensions"].remove("task_completeness"); checks_path.write_text(json.dumps(missing), encoding="utf-8")
            with self.assertRaises(ValueError): prepare(selection)
            unknown = copy.deepcopy(valid); unknown["dimensions"].append("invented_quality"); checks_path.write_text(json.dumps(unknown), encoding="utf-8")
            with self.assertRaises(ValueError): prepare(selection)
            checks_path.write_text(json.dumps(valid), encoding="utf-8"); self.assertTrue(prepare(selection)["manifest_sha256"])

    def test_committed_development_selection_freezes_real_artifacts_and_counterbalances(self) -> None:
        frozen = prepare(EVALUATION / "cases/development-selection.json"); self.assertEqual(len(frozen["pairs"]), 3)
        self.assertEqual(frozen["pairs"][0]["order"], ["treatment", "baseline"]); self.assertEqual(frozen["pairs"][1]["order"], ["baseline", "treatment"])
        self.assertTrue(all(Path(row["prompt"]["path"]).is_file() for row in frozen["pairs"])); self.assertTrue(frozen["arms"]["routing_is_only_intended_difference"])


if __name__ == "__main__": unittest.main()
