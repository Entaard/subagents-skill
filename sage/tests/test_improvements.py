"""Additive coordinator, binding, card, and accounting contracts."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

SAGE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SAGE / "scripts"), str(SAGE / "evaluation"), str(SAGE / "evaluation/tests")]
import sage_state as state
import sage_knowledge as knowledge
from usage import summarize
from support import complete_read_run, dump, event, invoke, opened, record, task, write_log


class Improvements(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ["SAGE_EVALUATION_SANDBOX"])
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def cli(self, script, *args, ok=True):
        result = invoke(SAGE / "scripts" / script, *map(str, args))
        self.assertEqual(result.returncode, 0 if ok else 2, result.stderr)
        return json.loads(result.stdout if ok else result.stderr)

    def append(self, rows, kind, payload):
        row = event(len(rows) + 1, kind, payload)
        row["at"] = "2026-09-11T00:00:00Z"
        rows.append(row)

    def artifact(self, rows, name="a", digest="a" * 64):
        self.append(rows, "artifact.recorded", {"v": 1, "artifact_id": name, "sha256": digest, "locator": "candidate/" + name})

    def obligation(self, rows, name="test", revision=1, criterion="c-1", artifact="a"):
        self.append(rows, "verification.required", {"v": 1, "obligation_id": name, "revision": revision,
                    "criterion_ids": [criterion], "artifact_ids": [artifact]})

    def bound_check(self, rows, name="test", attempt=1, digest="a" * 64, outcome="passed", revision=1):
        self.append(rows, "check.recorded", {"check_id": f"{name}-{attempt}", "criterion_ids": ["c-1"],
                    "outcome": outcome, "evidence_ids": ["ev-1"], "binding": {"v": 1, "obligation_id": name,
                    "obligation_revision": revision, "attempt": attempt, "artifacts": {"a": digest}}})

    def close(self, rows):
        self.append(rows, "run.closed", complete_read_run()[-1]["payload"])

    def test_summary_preserves_snapshot_bytes_and_bounds_output(self):
        rows = complete_read_run()[:-1]
        for i in range(300):
            self.append(rows, "evidence.recorded", {"evidence_id": f"historical-{i}", "criterion_ids": ["c-1"],
                        "kind": "observation", "locator": "resolved/" + "x" * 200, "sha256": None})
            rows[-1]["at"] = "2026-09-11T00:00:00Z"
        run = self.root / "run"; write_log(run, rows)
        full = self.cli("sage_state.py", "snapshot", "--run-dir", run, "--write")
        before = (run / "snapshot.json").read_bytes()
        receipt = self.cli("sage_state.py", "snapshot", "--run-dir", run, "--write", "--summary")
        self.assertEqual(before, (run / "snapshot.json").read_bytes())
        self.assertEqual(receipt["events_sha256"], full["events_sha256"])
        self.assertLess(len(json.dumps(receipt)), len(json.dumps(full)) / 20)
        view = self.cli("sage_state.py", "context", "--run-dir", run)
        self.assertLess(len(json.dumps(view)), len(json.dumps(full)) / 20)

    def test_payload_authoring_is_atomic_and_supplies_envelopes(self):
        run = self.root / "run"; write_log(run, [opened()])
        payload = {"type": "note.recorded", "payload": {"category": "decision", "text": "Use local inputs", "evidence_ids": [], "corrects_event_id": None}}
        source = dump(self.root / "payloads.json", [payload, payload])
        result = self.cli("sage_state.py", "append", "--run-dir", run, "--payloads", source)
        rows, before = state.read_events(run / "events.jsonl")
        self.assertEqual([r["event_id"] for r in rows[1:]], result["event_ids"])
        self.assertEqual(len(set(result["event_ids"])), 2)
        self.assertTrue(all(r["at"].endswith("Z") and r["seq"] == i for i, r in enumerate(rows, 1)))
        dump(source, [payload, {"type": "user.decision", "payload": {}}])
        self.cli("sage_state.py", "append", "--run-dir", run, "--payloads", source, ok=False)
        self.assertEqual(before, (run / "events.jsonl").read_bytes())
        dump(source, [{**payload, "as": "authority"}, {"type": "criteria.revised", "payload": {
            "revision": 2, "authority_event_id": {"$event": "authority"}, "reason": "additional criterion",
            "added": [{"id": "c-2", "text": "also verify integration"}], "replaced": [], "retired": []}}])
        result = self.cli("sage_state.py", "append", "--run-dir", run, "--payloads", source)
        rows, before = state.read_events(run / "events.jsonl")
        self.assertEqual(rows[-1]["payload"]["authority_event_id"], result["aliases"]["authority"])
        dump(source, [{**payload, "as": "authority", "payload": {**payload["payload"], "corrects_event_id": {"$event": "authority"}}}])
        self.cli("sage_state.py", "append", "--run-dir", run, "--payloads", source, ok=False)
        self.assertEqual(before, (run / "events.jsonl").read_bytes())

    def test_context_enumerates_writers_criteria_findings_and_stale_pages(self):
        rows = [opened(["c-1", "c-2"])]
        self.append(rows, "plan.revised", {**complete_read_run()[1]["payload"], "tasks": [task("w", "write")]})
        self.append(rows, "task.admitted", {"task_id": "w", "task_revision": 1, "plan_revision": 1})
        self.append(rows, "finding.opened", {"finding_id": "f", "severity": "major", "summary": "broken", "evidence_ids": []})
        run = self.root / "run"; write_log(run, rows)
        page = self.cli("sage_state.py", "context", "--run-dir", run, "--limit", 1)
        self.assertEqual(page["items"][0]["kind"], "unresolved_effect"); self.assertTrue(page["partial"])
        found = list(page["items"]); digest = page["events_sha256"]
        while page["next_offset"] is not None:
            page = self.cli("sage_state.py", "context", "--run-dir", run, "--limit", 1,
                            "--offset", page["next_offset"], "--events-sha256", digest)
            found.extend(page["items"])
        self.assertEqual({i["id"] for i in found if i["kind"] == "criterion"}, {"c-1", "c-2"})
        self.assertIn("f", [i["id"] for i in found if i["kind"] == "finding"])
        self.append(rows, "finding.opened", {"finding_id": "new-blocker", "severity": "blocker", "summary": "new defect", "evidence_ids": []})
        write_log(run, rows)
        self.cli("sage_state.py", "context", "--run-dir", run, "--offset", 1, ok=False)
        self.assertEqual(self.cli("sage_state.py", "context", "--run-dir", run, "--offset", 1, "--events-sha256", digest, ok=False)["code"], "stale_context")
        restarted = self.cli("sage_state.py", "context", "--run-dir", run)
        self.assertIn("new-blocker", [i["id"] for i in restarted["items"]])
        (run / "events.jsonl").write_bytes(b"broken")
        self.cli("sage_state.py", "context", "--run-dir", run, ok=False)

    def test_all_required_checks_must_pass_current_artifacts(self):
        rows = complete_read_run()[:-1]; self.artifact(rows)
        self.obligation(rows, "unit"); self.obligation(rows, "integration")
        self.bound_check(rows, "unit"); self.close(rows)
        with self.assertRaises(state.ContractError): state.validate(rows)
        rows.pop(); self.bound_check(rows, "integration"); self.close(rows); state.validate(rows)
        rows.pop(); self.artifact(rows, digest="b" * 64); self.close(rows)
        with self.assertRaises(state.ContractError): state.validate(rows)
        rows.pop(); self.bound_check(rows, "unit", 2, "b" * 64); self.bound_check(rows, "integration", 2, "b" * 64)
        self.close(rows); state.validate(rows)
        rows.pop(); self.bound_check(rows, "unit", 3, "b" * 64, "failed"); self.close(rows)
        with self.assertRaises(state.ContractError): state.validate(rows)

    def test_unrelated_artifact_preserves_check_and_revised_obligation_needs_new_attempt(self):
        rows = complete_read_run()[:-1]; self.artifact(rows); self.obligation(rows); self.bound_check(rows)
        self.artifact(rows, name="unrelated"); self.close(rows); state.validate(rows)
        rows.pop(); self.obligation(rows, revision=2); self.close(rows)
        with self.assertRaises(state.ContractError): state.validate(rows)
        rows.pop(); self.bound_check(rows, attempt=2, revision=2); self.close(rows); state.validate(rows)

    def test_bound_finding_fix_cannot_use_a_pre_finding_pass(self):
        rows = complete_read_run()[:-1]; self.artifact(rows); self.obligation(rows); self.bound_check(rows)
        self.append(rows, "finding.opened", {"finding_id": "f", "severity": "major", "summary": "defect", "evidence_ids": ["ev-1"]})
        disposition = {"finding_id": "f", "disposition": "fixed", "evidence_ids": ["ev-1"], "verification_check_id": "test-1"}
        self.append(rows, "finding.dispositioned", disposition)
        with self.assertRaises(state.ContractError): state.validate(rows)
        rows.pop(); self.bound_check(rows, attempt=2)
        self.append(rows, "finding.dispositioned", {**disposition, "verification_check_id": "test-2"})
        self.close(rows); state.validate(rows)

    def test_report_surfaces_stale_required_verification(self):
        rows = complete_read_run()[:-1]; self.artifact(rows); self.obligation(rows); self.bound_check(rows)
        self.artifact(rows, digest="b" * 64)
        run = self.root / "run"; write_log(run, rows)
        self.cli("sage_state.py", "report", "--run-dir", run, "--write")
        self.assertIn("test revision 1: active=True, satisfied=False", (run / "report.md").read_text())

    def test_application_requires_exact_selected_revision_and_real_target(self):
        rows = complete_read_run()[:-1]
        self.append(rows, "knowledge.selected", {"generation_id": "g-1", "cue_fingerprint": "fp", "cues": {"task": ["test"]},
                    "matches": [{"id": "k-1", "revision": 1, "status": "supported", "reason": "task"}], "retrieval_status": "matched"})
        applied = {"v": 1, "id": "k-1", "revision": 1, "generation_id": "g-1", "decision_event_id": "e-3", "evidence_ids": ["ev-1"]}
        self.append(rows, "knowledge.applied", applied)
        with self.assertRaises(state.ContractError): state.validate(rows)
        rows.pop()
        self.append(rows, "note.recorded", {"category": "decision", "text": "Use selected guidance for the next decision", "evidence_ids": ["ev-1"], "corrects_event_id": None})
        target = rows[-1]["event_id"]
        self.append(rows, "knowledge.selected", copy.deepcopy(rows[-2]["payload"]))
        self.append(rows, "knowledge.applied", {**applied, "decision_event_id": target})
        self.assertEqual(len(state.validate(rows)["knowledge_applications"]), 1)
        rows[-1]["payload"]["revision"] = 2
        with self.assertRaises(state.ContractError): state.validate(rows)

    def test_application_can_link_a_task_admitted_after_selection(self):
        rows = [opened()]
        self.append(rows, "knowledge.selected", {"generation_id": "g-1", "cue_fingerprint": "fp", "cues": {"task": ["test"]},
                    "matches": [{"id": "k-1", "revision": 1, "status": "supported", "reason": "task"}], "retrieval_status": "matched"})
        for original in complete_read_run()[1:-1]: self.append(rows, original["type"], copy.deepcopy(original["payload"]))
        self.append(rows, "knowledge.applied", {"v": 1, "id": "k-1", "revision": 1, "generation_id": "g-1", "decision_event_id": "e-4", "evidence_ids": ["ev-1"]})
        self.assertEqual(len(state.validate(rows)["knowledge_applications"]), 1)

    def test_superseded_failed_attempts_are_history_not_working_context(self):
        rows = complete_read_run()[:-1]; self.artifact(rows); self.obligation(rows)
        self.bound_check(rows)
        small = state.decision_items(state.validate(rows), rows)
        for attempt in range(2, 51): self.bound_check(rows, attempt=attempt, outcome="failed")
        self.bound_check(rows, attempt=51)
        projected = state.validate(rows); view = state.decision_items(projected, rows)
        self.assertEqual(len(view), len(small))
        self.assertFalse(any(i["kind"] == "check" for i in view))
        self.assertEqual(len(projected["checks"]), 52)
        run = self.root / "run"; write_log(run, rows)
        history = self.cli("sage_state.py", "context", "--run-dir", run, "--section", "checks", "--limit", 100)
        self.assertEqual(len(history["items"]), 52)
        self.bound_check(rows, attempt=52, outcome="failed")
        failed = [i for i in state.decision_items(state.validate(rows), rows) if i["kind"] == "check"]
        self.assertEqual([i["id"] for i in failed], ["test-52"])

    def test_complete_card_payload_budget_and_exact_revalidation(self):
        source = self.root / "source"; write_log(source, complete_read_run("source-1"))
        item = record(); proposal = dump(self.root / "proposal.json", {"action": "create", "proposer": "proposer", "reviewer": "reviewer", "source_runs": [str(source)], "record": item})
        store = self.root / "store"
        self.cli("sage_knowledge.py", "stage", "--store-dir", store, "--proposal", proposal, "--generation-id", "g-1", "--expected-current", "none")
        self.cli("sage_knowledge.py", "activate", "--store-dir", store, "--generation-id", "g-1", "--expected-current", "none")
        cues = dump(self.root / "cues.json", {"operation": ["resume"]})
        args = ("retrieve", "--store-dir", store, "--cues", cues, "--limit", 3)
        legacy = self.cli("sage_knowledge.py", *args)
        self.assertNotIn("card_version", legacy)
        cards = self.cli("sage_knowledge.py", *args, "--cards", "--max-bytes", 5000)
        card = cards["matches"][0]
        self.assertEqual(card["qualifier"], item["qualifier"])
        self.assertEqual(card["gate_evidence"], item["gate_evidence"])
        self.assertEqual(card["record_sha256"], hashlib.sha256(Path(card["record_locator"]).read_bytes()).hexdigest())
        small = self.cli("sage_knowledge.py", *args, "--cards", "--max-bytes", 1024, ok=False)
        self.assertEqual(small["code"], "budget_too_small")
        previous = dump(self.root / "previous.json", [{"id": "k-1", "revision": 1, "generation_id": "g-1"}])
        diag = self.cli("sage_knowledge.py", "revalidate", "--store-dir", store, "--previous", previous, "--cues", cues)
        self.assertEqual(diag["diagnostics"][0]["diagnostic"], "unchanged_applicable")
        self.cli("sage_knowledge.py", *args, "--max-bytes", 5000, ok=False)
        self.cli("sage_knowledge.py", *args, "--cards", "--record-id", "../invalid", ok=False)

    def usage(self):
        return {"schema_version": "sage-observed-usage-v1", "tasks": [{"id": "t", "accepted": True, "coverage": "complete", "artifact_sha256": "a" * 64}],
                "requests": [{"id": "r", "task_id": "t", "attempt": 1, "source": "telemetry/r", "model": None, "input_tokens": 100,
                              "cached_input_tokens": 50, "output_tokens": 20, "reasoning_tokens": 10, "reasoning_in_output": True, "wall_seconds": None, "kind": "leaf_request"}]}

    def test_usage_counts_failed_attempts_without_duplicate_reasoning(self):
        data = self.usage(); data["requests"].append({**data["requests"][0], "id": "repair", "attempt": 2})
        result = summarize(data)
        self.assertEqual(result["tokens_per_accepted_outcome"], 240)
        data["tasks"][0]["accepted"] = False
        result = summarize(data); self.assertEqual(result["total_tokens"], 240); self.assertIsNone(result["tokens_per_accepted_outcome"])

    def test_usage_unknown_and_duplicate_aggregates(self):
        data = self.usage(); data["requests"][0]["input_tokens"] = None
        self.assertIsNone(summarize(data)["total_tokens"])
        data = self.usage(); data["requests"].append(copy.deepcopy(data["requests"][0]))
        with self.assertRaises(ValueError): summarize(data)
        data = self.usage(); data["requests"][0]["kind"] = "parent_aggregate"
        with self.assertRaises(ValueError): summarize(data)


if __name__ == "__main__": unittest.main()
