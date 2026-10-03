"""Public-CLI regressions for versioned task dependency correctness."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evaluation" / "tests"))
from support import STATE_CLI, dump, event, invoke, opened, output, sandbox, task, write_log  # noqa: E402

POLICY = "revision-bound-v1"


class DependencyPolicyTests(unittest.TestCase):
    def start(self, guarded: bool = True) -> list[dict]:
        row = opened()
        if guarded: row["payload"]["dependency_policy"] = POLICY
        return [row]

    def add(self, rows: list[dict], kind: str, payload: dict) -> None:
        rows.append(event(len(rows) + 1, kind, payload))

    def plan(self, tasks: list[dict], revision: int = 1, attempt_limit: int = 3) -> dict:
        return {"revision": revision, "reason": "initial" if revision == 1 else "evidence_change",
                "attempt_limit": attempt_limit, "revision_limit": 4, "no_progress": "same failed outcome",
                "trigger_event_ids": ["e-1"] if revision == 1 else ["e-3"], "tasks": tasks}

    def observe(self, rows: list[dict], evidence_id: str = "ev-1") -> None:
        self.add(rows, "evidence.recorded", {"evidence_id": evidence_id, "criterion_ids": ["c-1"],
                 "kind": "observation", "locator": f"artifact/{evidence_id}", "sha256": None})

    def admit(self, rows: list[dict], item: dict, plan_revision: int = 1) -> None:
        self.add(rows, "task.admitted", {"task_id": item["id"], "task_revision": item["revision"], "plan_revision": plan_revision})

    def result(self, rows: list[dict], item: dict, evidence_id: str = "ev-1") -> None:
        self.add(rows, "task.result", {"task_id": item["id"], "task_revision": item["revision"],
                 "outcome": "passed", "effect_status": "none", "evidence_ids": [evidence_id]})

    def finish(self, rows: list[dict], item: dict, plan_revision: int = 1) -> None:
        self.admit(rows, item, plan_revision); self.result(rows, item)

    def close(self, rows: list[dict]) -> None:
        self.add(rows, "check.recorded", {"check_id": "final", "criterion_ids": ["c-1"], "outcome": "passed", "evidence_ids": ["ev-1"]})
        self.add(rows, "run.closed", {"status": "completed", "criterion_evidence": {"c-1": ["ev-1"]}, "scope_reconciled": True, "remaining_human_items": []})

    def append(self, run: Path, rows: list[dict], additions: list[dict]):
        path = dump(run.parent / "addition.json", [{"type": row["type"], "payload": row["payload"]} for row in additions])
        return invoke(STATE_CLI, "append", "--run-dir", str(run), "--payloads", str(path))

    def assert_rejected_without_mutation(self, run: Path, rows: list[dict], additions: list[dict], code: str) -> None:
        write_log(run, rows)
        before = (run / "events.jsonl").read_bytes()
        (run / "snapshot.json").write_bytes(b"retained snapshot")
        rejected = self.append(run, rows, additions)
        self.assertEqual(rejected.returncode, 2, rejected.stderr)
        self.assertEqual(json.loads(rejected.stderr)["code"], code)
        self.assertEqual((run / "events.jsonl").read_bytes(), before)
        self.assertEqual((run / "snapshot.json").read_bytes(), b"retained snapshot")

    def test_init_enables_guard_and_views_expose_policy(self) -> None:
        with sandbox() as raw:
            root = Path(raw); run = root / "run"
            criteria = dump(root / "criteria.json", [{"id": "c-1", "text": "observable outcome"}])
            result = invoke(STATE_CLI, "init", "--run-dir", str(run), "--run-id", "run-1", "--objective", "bounded", "--criteria", str(criteria))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((run / "events.jsonl").read_text())["payload"]["dependency_policy"], POLICY)
            for args in (("snapshot", "--write"), ("snapshot", "--write", "--summary"), ("context",)):
                actual = invoke(STATE_CLI, args[0], "--run-dir", str(run), *args[1:])
                self.assertEqual(actual.returncode, 0, actual.stderr)
                self.assertEqual(output(actual)["dependency_policy"], POLICY)

    def test_cycles_reject_atomically_and_valid_out_of_order_diamond_passes(self) -> None:
        cases = ([task("a", dependencies=["b"]), task("b", dependencies=["a"])],
                 [task("a", dependencies=["b"]), task("b", dependencies=["c"]), task("c", dependencies=["a"])])
        with sandbox() as raw:
            root = Path(raw)
            for index, tasks in enumerate(cases):
                with self.subTest(cycle=index):
                    self.assert_rejected_without_mutation(root / str(index), self.start(), [event(2, "plan.revised", self.plan(tasks))], "invalid_dependency")
            tasks = [task("d", dependencies=["b", "c"]), task("c", dependencies=["a"]), task("b", dependencies=["a"]), task("a")]
            run = root / "diamond"; rows = self.start(); self.add(rows, "plan.revised", self.plan(tasks)); write_log(run, rows)
            result = invoke(STATE_CLI, "validate", "--run-dir", str(run))
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_cycle_introduced_in_later_plan_rejects(self) -> None:
        with sandbox() as raw:
            a = task("a"); b = task("b", dependencies=["a"])
            rows = self.start(); self.add(rows, "plan.revised", self.plan([a, b])); self.observe(rows)
            changed = copy.deepcopy(a); changed["dependencies"] = ["b"]
            self.assert_rejected_without_mutation(Path(raw) / "run", rows, [event(4, "plan.revised", self.plan([changed, b], 2))], "invalid_dependency")

    def chain(self, guarded: bool = True):
        tasks = [task("a"), task("b", dependencies=["a"]), task("c", dependencies=["b"]), task("independent")]
        rows = self.start(guarded); self.add(rows, "plan.revised", self.plan(list(reversed(tasks)))); self.observe(rows)
        for item in tasks: self.finish(rows, item)
        return rows, tasks

    def test_dependency_revision_requires_transitive_reruns_and_preserves_other_branch(self) -> None:
        with sandbox() as raw:
            root = Path(raw); rows, tasks = self.chain()
            changed = copy.deepcopy(tasks); changed[0].update(revision=2, inputs=["new producer input"])
            for index in (1, 2):
                with self.subTest(stale=changed[index]["id"]):
                    self.assert_rejected_without_mutation(root / f"stale-{index}", rows,
                        [event(len(rows) + 1, "plan.revised", self.plan(list(reversed(changed)), 2))], "immutable_history")
                    changed[index]["revision"] = 2
            revised = copy.deepcopy(rows); self.add(revised, "plan.revised", self.plan(list(reversed(changed)), 2))
            run = root / "fixed"; write_log(run, revised)
            snapshot = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
            self.assertEqual(snapshot.returncode, 0, snapshot.stderr)
            actual = output(snapshot)["tasks"]
            self.assertEqual(actual["independent"]["state"], "passed")
            self.assertEqual([actual[key]["state"] for key in ("a", "b", "c")], ["planned"] * 3)
            for item in changed[:3]: self.finish(revised, item, 2)
            self.close(revised); write_log(run, revised)
            result = invoke(STATE_CLI, "validate", "--run-dir", str(run), "--terminal")
            self.assertEqual(result.returncode, 0, result.stderr)
            final = output(invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write"))
            self.assertEqual(len(final["attempt_history"]), 7)
            self.assertEqual(len(final["task_results"]), 7)

    def test_unadmitted_intermediates_need_no_fictitious_revision_bump(self) -> None:
        with sandbox() as raw:
            run = Path(raw) / "run"
            tasks = [task("a"), task("b", dependencies=["a"]), task("c", dependencies=["b"])]
            rows = self.start(); self.add(rows, "plan.revised", self.plan(tasks)); self.observe(rows); self.finish(rows, tasks[0])
            changed = copy.deepcopy(tasks); changed[0].update(revision=2, inputs=["changed source"])
            self.add(rows, "plan.revised", self.plan(changed, 2))
            for item in changed: self.finish(rows, item, 2)
            self.close(rows); write_log(run, rows)
            result = invoke(STATE_CLI, "validate", "--run-dir", str(run), "--terminal")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_late_result_from_inflight_producer_cannot_release_dependent(self) -> None:
        with sandbox() as raw:
            root = Path(raw); a = task("a"); b = task("b", dependencies=["a"])
            rows = self.start(); self.add(rows, "plan.revised", self.plan([a, b])); self.observe(rows); self.admit(rows, a)
            changed = copy.deepcopy(a); changed.update(revision=2, inputs=["changed source"])
            self.add(rows, "plan.revised", self.plan([changed, b], 2)); self.result(rows, a)
            admission = event(len(rows) + 1, "task.admitted", {"task_id": "b", "task_revision": 1, "plan_revision": 2})
            self.assert_rejected_without_mutation(root / "blocked", rows, [admission], "dependency_blocked")
            self.finish(rows, changed, 2); self.finish(rows, b, 2); self.close(rows)
            run = root / "fixed"; write_log(run, rows)
            result = invoke(STATE_CLI, "validate", "--run-dir", str(run), "--terminal")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_late_inflight_dependent_result_remains_historical(self) -> None:
        with sandbox() as raw:
            run = Path(raw) / "run"; a = task("a"); b = task("b", dependencies=["a"]); c = task("c", dependencies=["b"])
            rows = self.start(); self.add(rows, "plan.revised", self.plan([a, b, c])); self.observe(rows); self.finish(rows, a); self.admit(rows, b)
            a2 = copy.deepcopy(a); a2.update(revision=2, inputs=["changed input"])
            b2 = copy.deepcopy(b); b2["revision"] = 2
            self.add(rows, "plan.revised", self.plan([a2, b2, c], 2)); self.result(rows, b); self.finish(rows, a2, 2)
            self.assert_rejected_without_mutation(run, rows, [event(len(rows) + 1, "task.admitted", {"task_id": "c", "task_revision": 1, "plan_revision": 2})], "dependency_blocked")
            snapshot = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
            self.assertEqual(snapshot.returncode, 0, snapshot.stderr)
            self.assertEqual(output(snapshot)["tasks"]["b"]["state"], "planned")

    def test_dependency_refresh_still_obeys_cumulative_attempt_limit(self) -> None:
        with sandbox() as raw:
            run = Path(raw) / "run"; rows, tasks = self.chain()
            changed = copy.deepcopy(tasks); changed[0]["inputs"] = ["changed"]
            for item in changed[:3]: item["revision"] = 2
            self.add(rows, "plan.revised", self.plan(changed, 2, attempt_limit=1))
            self.assert_rejected_without_mutation(run, rows, [event(len(rows) + 1, "task.admitted", {"task_id": "a", "task_revision": 2, "plan_revision": 2})], "limit_exceeded")

    def test_legacy_logs_keep_prior_replay_and_terminal_semantics(self) -> None:
        with sandbox() as raw:
            root = Path(raw); rows, tasks = self.chain(guarded=False)
            changed = copy.deepcopy(tasks); changed[0].update(revision=2, inputs=["historical changed input"])
            self.add(rows, "plan.revised", self.plan(changed, 2)); self.finish(rows, changed[0], 2); self.close(rows)
            run = root / "closed"; write_log(run, rows); before = (run / "events.jsonl").read_bytes()
            for args in (("validate", "--terminal"), ("report", "--write"), ("snapshot", "--write"), ("context",)):
                result = invoke(STATE_CLI, args[0], "--run-dir", str(run), *args[1:])
                self.assertEqual(result.returncode, 0, result.stderr)
                if args[0] in {"snapshot", "context"}: self.assertEqual(output(result)["dependency_policy"], "legacy")
            self.assertEqual((run / "events.jsonl").read_bytes(), before)
            cycle = self.start(False); self.add(cycle, "plan.revised", self.plan([task("a", dependencies=["b"]), task("b", dependencies=["a"])]))
            write_log(root / "cycle", cycle)
            self.assertEqual(invoke(STATE_CLI, "validate", "--run-dir", str(root / "cycle")).returncode, 0)

    def test_unknown_or_malformed_policy_rejects_without_rewriting_projection(self) -> None:
        with sandbox() as raw:
            for index, value in enumerate(("revision-bound-v2", "legacy", None, True, {})):
                with self.subTest(policy=value):
                    rows = self.start(); rows[0]["payload"]["dependency_policy"] = value
                    run = Path(raw) / str(index); write_log(run, rows); (run / "snapshot.json").write_bytes(b"keep")
                    result = invoke(STATE_CLI, "snapshot", "--run-dir", str(run), "--write")
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(json.loads(result.stderr)["code"], "invalid_event")
                    self.assertEqual((run / "snapshot.json").read_bytes(), b"keep")


if __name__ == "__main__": unittest.main()
