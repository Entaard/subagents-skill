#!/usr/bin/env python3
"""Focused installed-interface checks for standalone promotion coordination.

The state/store cases are informed scripted scenarios. Actor strings are fixtures,
not claims about native model execution or behavioral independence.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
SAGE = HERE.parents[2]
PHASE = os.environ.get("SAGE_R2_PHASE", "local")
OUT = HERE / PHASE
INSTALLED = OUT / "installed"
WORK = OUT / "work"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return path


def invoke(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args], cwd=SAGE.parent,
        text=True, capture_output=True, check=False,
    )


def event(seq: int, kind: str, payload: dict[str, Any], run_id: str) -> dict[str, Any]:
    return {
        "v": 1,
        "event_id": f"{run_id}-e-{seq}",
        "run_id": run_id,
        "seq": seq,
        "at": f"2026-09-08T10:00:{seq:02d}Z",
        "actor": "root",
        "type": kind,
        "payload": payload,
    }


def opened(run_id: str, objective: str = "coordinate one bounded promotion") -> dict[str, Any]:
    return event(1, "run.opened", {
        "objective": objective,
        "criteria": [{"id": "c-1", "text": "the bounded promotion decision is evidenced"}],
        "constraints": ["closed source runs are read-only"],
        "next_action": "plan",
    }, run_id)


def task(task_id: str, effect: str, owner: str, dependencies: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": task_id,
        "revision": 1,
        "objective": f"complete {task_id}",
        "completion": f"{task_id} has an observed result",
        "dependencies": dependencies or [],
        "owner": owner,
        "effect": effect,
        "scope": [f"promotion/{task_id}"],
        "inputs": ["recorded baselines"],
        "returns": ["result", "evidence"],
        "risk": "low",
        "verification": f"check-{task_id}",
        "requested_model": "gpt-5.6-sol",
        "requested_effort": "high",
        "fork_turns": "none",
    }


def plan(run_id: str, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    return event(2, "plan.revised", {
        "revision": 1,
        "reason": "initial",
        "attempt_limit": 2,
        "revision_limit": 2,
        "no_progress": "stop after one unchanged retry",
        "trigger_event_ids": [f"{run_id}-e-1"],
        "tasks": tasks,
    }, run_id)


def write_log(run: Path, rows: list[dict[str, Any]]) -> None:
    run.mkdir(parents=True, exist_ok=True)
    (run / "events.jsonl").write_text(
        "".join(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def source_rows() -> list[dict[str, Any]]:
    run_id = "source-1"
    source_task = task("source-read", "read", "root")
    rows = [opened(run_id, "produce bounded source evidence"), plan(run_id, [source_task])]
    rows.extend([
        event(3, "task.admitted", {"task_id": "source-read", "task_revision": 1, "plan_revision": 1}, run_id),
        event(4, "evidence.recorded", {"evidence_id": "source-observation", "criterion_ids": ["c-1"], "kind": "observation", "locator": "artifact/source", "sha256": None}, run_id),
        event(5, "task.result", {"task_id": "source-read", "task_revision": 1, "outcome": "passed", "effect_status": "none", "evidence_ids": ["source-observation"]}, run_id),
        event(6, "check.recorded", {"check_id": "source-check", "criterion_ids": ["c-1"], "outcome": "passed", "evidence_ids": ["source-observation"]}, run_id),
        event(7, "checkpoint.written", {"next_action": "close", "baselines": [], "unresolved_user_items": []}, run_id),
        event(8, "run.closed", {"status": "completed", "criterion_evidence": {"c-1": ["source-observation"]}, "scope_reconciled": True, "remaining_human_items": []}, run_id),
    ])
    return rows


def cues(**values: list[str]) -> dict[str, Any]:
    result = {key: [] for key in ("task", "domain", "artifact", "environment", "risk", "operation", "failure")}
    result.update(values)
    return result


def record(record_id: str) -> dict[str, Any]:
    return {
        "v": 1,
        "id": record_id,
        "revision": 1,
        "prior_revision": None,
        "status": "supported",
        "evidence_class": "scoped_fact",
        "gate_rationale": "A repeatable fixture establishes this scoped fact.",
        "gate_evidence": {"repeatable_check": "python3 fixture", "environment": "scripted fixture sandbox"},
        "rule": "Validate the authoritative log before rebuilding its projection.",
        "recognizer": cues(operation=["resume"]),
        "qualifier": {"all": cues(operation=["resume"]), "none": cues(environment=["remote managed authority"])},
        "falsifier": "A corrupt authoritative log safely rebuilds the projection.",
        "evidence_summary": "The public CLI fixture rejected corrupt authority.",
        "provenance": [{"run_id": "source-1", "locator": "events.jsonl#source-1-e-6"}],
        "alternative_explanations": [],
        "counterevidence": [],
        "refutation": {"actor": "/synthetic/refuter", "outcome": "passed", "findings": [], "evidence": ["source-1:source-1-e-6"]},
        "review": {"actor": "/synthetic/reviewer", "outcome": "passed", "dispositions": [], "gate_decision": "supported"},
        "created_at": "2026-09-08T10:00:00Z",
        "reviewed_at": "2026-09-08T10:01:00Z",
    }


def proposal(path: Path, source: Path, record_id: str) -> Path:
    return dump(path, {
        "action": "create",
        "proposer": "/synthetic/author",
        "reviewer": "/synthetic/reviewer",
        "source_runs": [str(source)],
        "record": record(record_id),
    })


def markdown_graph(start: Path, root: Path) -> set[str]:
    pending = [start]
    seen: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", text):
            if "://" in target:
                continue
            linked = (path.parent / target).resolve()
            if linked.is_file() and root.resolve() in linked.parents:
                pending.append(linked)
    return {path.relative_to(root).as_posix() for path in seen}


class PromotionCoordinationAcceptance(unittest.TestCase):
    observations: dict[str, Any] = {
        "evidence_kind": "informed scripted public-CLI scenarios",
        "native_agents_or_models_observed": False,
    }

    @classmethod
    def setUpClass(cls) -> None:
        OUT.mkdir(parents=True, exist_ok=True)
        WORK.mkdir(parents=True, exist_ok=True)
        install = subprocess.run(
            ["bash", str(SAGE / "install.sh"), "--target-root", str(INSTALLED)],
            cwd=SAGE.parent, text=True, capture_output=True, check=False,
        )
        dump(OUT / "install.json", {
            "argv": install.args,
            "exit_code": install.returncode,
            "stdout": install.stdout,
            "stderr": install.stderr,
        })
        if install.returncode != 0:
            raise RuntimeError(install.stderr)
        cls.state = INSTALLED / "sage/bin/sage_state.py"
        cls.knowledge = INSTALLED / "sage/bin/sage_knowledge.py"

    def test_existing_main_graph_is_the_positive_shared_seam_control(self) -> None:
        graph = markdown_graph(INSTALLED / "skills/sage/SKILL.md", INSTALLED)
        expected = {
            "skills/sage/references/run.md",
            "skills/sage/references/state.md",
            "skills/sage/references/delegation.md",
            "skills/sage/references/recovery.md",
        }
        self.assertTrue(expected <= graph, graph)
        self.observations["main_shared_seam_control"] = "pass"

    def test_standalone_promotion_graph_defines_its_own_recoverable_run(self) -> None:
        graph = markdown_graph(INSTALLED / "skills/sage-promote/SKILL.md", INSTALLED)
        expected = {
            "skills/sage/references/run.md",
            "skills/sage/references/state.md",
            "skills/sage/references/delegation.md",
            "skills/sage/references/recovery.md",
        }
        self.assertTrue(expected <= graph, f"standalone promotion cannot reach shared coordinator contract: {sorted(graph)}")
        promotion = (INSTALLED / "skills/sage-promote/references/promotion.md").read_text(encoding="utf-8").casefold()
        clauses = {
            "separate authority": "separate coordinator run",
            "source/store separation": "knowledge generations are store artifacts",
            "bounded baselines": "proposal and expected-pointer/generation baselines",
            "identity accounting": "requested and effective model/effort",
            "full cost": "total delegation overhead",
            "checkpoint coverage": "before and after staging or activation",
            "recovery baseline check": "recheck the actual source, proposal, current pointer, generation, and authority baselines",
            "stale action": "revise a stale next action",
        }
        missing = {name: text for name, text in clauses.items() if text not in promotion}
        self.assertFalse(missing, f"reachable procedure is semantically incomplete: {missing}")
        self.observations["promotion_instruction_contract"] = "pass"

    def test_pre_dispatch_resume_repairs_only_stale_projection_and_preserves_corruption(self) -> None:
        case = WORK / "pre-dispatch"
        run_id = "promotion-pre-dispatch"
        roles = [
            task("author", "read", "/synthetic/author"),
            task("refute", "read", "/synthetic/refuter", ["author"]),
            task("review", "read", "/synthetic/reviewer", ["refute"]),
            task("stage", "write", "root", ["review"]),
            task("activate", "write", "root", ["stage"]),
        ]
        rows = [opened(run_id), plan(run_id, roles), event(3, "checkpoint.written", {
            "next_action": "revalidate authority and baselines, then dispatch author",
            "baselines": [
                {"kind": "authority", "value": "explicit promotion request"},
                {"kind": "sources", "value": ["source-1"]},
                {"kind": "proposal", "sha256": "none"},
                {"kind": "expected-current", "value": "none"},
                {"kind": "generation", "value": "unassigned"},
            ],
            "unresolved_user_items": [],
        }, run_id)]
        write_log(case, rows)
        snap = invoke(self.state, "snapshot", "--run-dir", str(case), "--write")
        self.assertEqual(snap.returncode, 0, snap.stderr)
        log_before = (case / "events.jsonl").read_bytes()
        stale = json.loads((case / "snapshot.json").read_text(encoding="utf-8"))
        stale["events_sha256"] = "0" * 64
        dump(case / "snapshot.json", stale)
        stale_snapshot = (case / "snapshot.json").read_bytes()
        agents = dump(case / "agents.json", [])
        resumed = invoke(self.state, "resume", "--run-dir", str(case), "--agents", str(agents))
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertEqual((case / "events.jsonl").read_bytes(), log_before)
        self.assertNotEqual((case / "snapshot.json").read_bytes(), stale_snapshot)
        self.assertTrue(json.loads(resumed.stdout)["admission_allowed"])

        corrupt = WORK / "corrupt-own-log"
        write_log(corrupt, rows)
        self.assertEqual(invoke(self.state, "snapshot", "--run-dir", str(corrupt), "--write").returncode, 0)
        (corrupt / "events.jsonl").write_bytes((corrupt / "events.jsonl").read_bytes() + b"{broken\n")
        corrupt_log = (corrupt / "events.jsonl").read_bytes()
        projection = (corrupt / "snapshot.json").read_bytes()
        agents = dump(corrupt / "agents.json", [])
        blocked = invoke(self.state, "resume", "--run-dir", str(corrupt), "--agents", str(agents))
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual((corrupt / "events.jsonl").read_bytes(), corrupt_log)
        self.assertEqual((corrupt / "snapshot.json").read_bytes(), projection)
        self.observations["pre_dispatch_recovery"] = {
            "stale_projection_rebuilt": True,
            "authoritative_log_unchanged": True,
            "corrupt_log_preserved_and_blocked": True,
        }

    def test_unknown_actor_effect_keeps_the_promotion_writer_barrier(self) -> None:
        case = WORK / "unknown-writer"
        run_id = "promotion-unknown-writer"
        rows = [
            opened(run_id),
            plan(run_id, [task("draft", "write", "/synthetic/author"), task("stage", "write", "root")]),
            event(3, "task.admitted", {"task_id": "draft", "task_revision": 1, "plan_revision": 1}, run_id),
            event(4, "agent.requested", {"task_id": "draft", "handle": "/synthetic/author", "requested_model": "gpt-5.6-sol", "requested_effort": "high", "fork_turns": "none"}, run_id),
            event(5, "checkpoint.written", {"next_action": "reconcile author before stage", "baselines": [], "unresolved_user_items": []}, run_id),
        ]
        write_log(case, rows)
        self.assertEqual(invoke(self.state, "snapshot", "--run-dir", str(case), "--write").returncode, 0)
        agents = dump(case / "agents.json", [{"handle": "/synthetic/author", "lifecycle": "completed", "effective_model": None, "effective_effort": None}])
        resumed = invoke(self.state, "resume", "--run-dir", str(case), "--agents", str(agents))
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        value = json.loads(resumed.stdout)
        self.assertFalse(value["admission_allowed"])
        self.assertEqual(value["proposed_events"][0]["payload"]["effect_status"], "unknown")
        second = dump(case / "second-writer.json", event(6, "task.admitted", {"task_id": "stage", "task_revision": 1, "plan_revision": 1}, run_id))
        rejected = invoke(self.state, "append", "--run-dir", str(case), "--event", str(second))
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(json.loads(rejected.stderr)["code"], "writer_busy")
        self.observations["unknown_actor_effect_writer_barrier"] = "pass"

    def test_pre_and_post_mutation_checkpoints_and_changed_baselines_choose_replan(self) -> None:
        case = WORK / "mutation-boundaries"
        source = case / "source-1"
        write_log(source, source_rows())
        source_before = (source / "events.jsonl").read_bytes()
        store = case / "store"
        candidate = proposal(case / "proposal.json", source, "k-primary")
        candidate_sha = sha(candidate)
        run_id = "promotion-mutation-boundaries"
        own = case / "own-run"
        rows = [
            opened(run_id),
            plan(run_id, [task("stage", "write", "root"), task("activate", "write", "root", ["stage"])]),
            event(3, "checkpoint.written", {"next_action": "stage g-1", "baselines": [{"proposal": candidate_sha}, {"expected-current": "none"}, {"generation": "g-1"}, {"authority": "granted"}], "unresolved_user_items": []}, run_id),
            event(4, "task.admitted", {"task_id": "stage", "task_revision": 1, "plan_revision": 1}, run_id),
        ]
        write_log(own, rows)
        staged = invoke(self.knowledge, "stage", "--store-dir", str(store), "--proposal", str(candidate), "--generation-id", "g-1", "--expected-current", "none")
        self.assertEqual(staged.returncode, 0, staged.stderr)
        stage_wave = [
            event(5, "evidence.recorded", {"evidence_id": "stage-observed", "criterion_ids": [], "kind": "observation", "locator": "store/generations/g-1/manifest.json", "sha256": sha(store / "generations/g-1/manifest.json")}, run_id),
            event(6, "task.result", {"task_id": "stage", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["stage-observed"]}, run_id),
            event(7, "checkpoint.written", {"next_action": "revalidate then activate g-1", "baselines": [{"proposal": candidate_sha}, {"expected-current": "none"}, {"generation": "g-1"}, {"authority": "granted"}], "unresolved_user_items": []}, run_id),
            event(8, "task.admitted", {"task_id": "activate", "task_revision": 1, "plan_revision": 1}, run_id),
        ]
        wave = case / "stage-wave.jsonl"
        wave.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in stage_wave), encoding="utf-8")
        appended = invoke(self.state, "append", "--run-dir", str(own), "--events", str(wave))
        self.assertEqual(appended.returncode, 0, appended.stderr)
        activated = invoke(self.knowledge, "activate", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "none")
        self.assertEqual(activated.returncode, 0, activated.stderr)
        activation_wave = [
            event(9, "evidence.recorded", {"evidence_id": "activation-observed", "criterion_ids": ["c-1"], "kind": "observation", "locator": "store/current.json", "sha256": sha(store / "current.json")}, run_id),
            event(10, "task.result", {"task_id": "activate", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["activation-observed"]}, run_id),
            event(11, "checkpoint.written", {"next_action": "validate and report", "baselines": [{"proposal": candidate_sha}, {"current": "g-1"}, {"generation": "g-1"}, {"authority": "granted"}], "unresolved_user_items": []}, run_id),
        ]
        wave = case / "activation-wave.jsonl"
        wave.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in activation_wave), encoding="utf-8")
        self.assertEqual(invoke(self.state, "append", "--run-dir", str(own), "--events", str(wave)).returncode, 0)
        self.assertEqual(invoke(self.state, "snapshot", "--run-dir", str(own), "--write").returncode, 0)
        self.assertEqual((source / "events.jsonl").read_bytes(), source_before)

        stale = WORK / "changed-baselines"
        stale_source = stale / "source-1"
        write_log(stale_source, source_rows())
        stale_source_before = (stale_source / "events.jsonl").read_bytes()
        stale_store = stale / "store"
        base = proposal(stale / "base.json", stale_source, "k-base")
        self.assertEqual(invoke(self.knowledge, "stage", "--store-dir", str(stale_store), "--proposal", str(base), "--generation-id", "g-base", "--expected-current", "none").returncode, 0)
        self.assertEqual(invoke(self.knowledge, "activate", "--store-dir", str(stale_store), "--generation-id", "g-base", "--expected-current", "none").returncode, 0)
        intended = proposal(stale / "intended.json", stale_source, "k-intended")
        recorded = {"source": sha(stale_source / "events.jsonl"), "proposal": sha(intended), "pointer": "g-base", "generation": "g-intended", "authority": "granted"}
        self.assertEqual(invoke(self.knowledge, "stage", "--store-dir", str(stale_store), "--proposal", str(intended), "--generation-id", "g-intended", "--expected-current", "g-base").returncode, 0)
        competing = proposal(stale / "competing.json", stale_source, "k-competing")
        self.assertEqual(invoke(self.knowledge, "stage", "--store-dir", str(stale_store), "--proposal", str(competing), "--generation-id", "g-competing", "--expected-current", "g-base").returncode, 0)
        self.assertEqual(invoke(self.knowledge, "activate", "--store-dir", str(stale_store), "--generation-id", "g-competing", "--expected-current", "g-base").returncode, 0)
        intended.write_text(intended.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        actual = {"source": sha(stale_source / "events.jsonl"), "proposal": sha(intended), "pointer": "g-competing", "generation": "g-intended", "authority": "revoked"}
        stale_activation = invoke(self.knowledge, "activate", "--store-dir", str(stale_store), "--generation-id", "g-intended", "--expected-current", "g-base")
        self.assertEqual(stale_activation.returncode, 2)
        changed = sorted(key for key in recorded if recorded[key] != actual[key])
        next_action = "revise_plan_and_reauthorize" if changed else "activate"
        self.assertEqual(changed, ["authority", "pointer", "proposal"])
        self.assertEqual(next_action, "revise_plan_and_reauthorize")
        self.assertEqual((stale_source / "events.jsonl").read_bytes(), stale_source_before)
        self.observations["mutation_boundaries"] = {
            "pre_stage": True,
            "post_stage_pre_activation": True,
            "post_activation": True,
            "changed_baselines": changed,
            "scripted_next_action": next_action,
            "source_logs_unchanged": True,
        }

    def test_inline_no_change_uses_no_team_and_writes_no_generation(self) -> None:
        case = WORK / "no-change"
        run_id = "promotion-no-change"
        root_task = task("inspect-bounded-corpus", "read", "root")
        rows = [
            opened(run_id, "decide whether the bounded corpus contains reusable knowledge"),
            plan(run_id, [root_task]),
            event(3, "task.admitted", {"task_id": root_task["id"], "task_revision": 1, "plan_revision": 1}, run_id),
            event(4, "evidence.recorded", {"evidence_id": "no-candidate", "criterion_ids": ["c-1"], "kind": "observation", "locator": "bounded-corpus#no-reusable-candidate", "sha256": None}, run_id),
            event(5, "task.result", {"task_id": root_task["id"], "task_revision": 1, "outcome": "passed", "effect_status": "none", "evidence_ids": ["no-candidate"]}, run_id),
            event(6, "check.recorded", {"check_id": "check-no-change", "criterion_ids": ["c-1"], "outcome": "passed", "evidence_ids": ["no-candidate"]}, run_id),
            event(7, "checkpoint.written", {"next_action": "report no_change", "baselines": [{"candidate-count": 0}, {"expected-current": "none"}], "unresolved_user_items": []}, run_id),
            event(8, "run.closed", {"status": "completed", "criterion_evidence": {"c-1": ["no-candidate"]}, "scope_reconciled": True, "remaining_human_items": []}, run_id),
        ]
        own = case / "own-run"
        write_log(own, rows)
        validated = invoke(self.state, "validate", "--run-dir", str(own), "--terminal")
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertFalse(any(row["type"].startswith("agent.") for row in rows))
        self.assertFalse((case / "store/current.json").exists())
        self.assertFalse((case / "store/generations").exists())
        self.observations["inline_no_change"] = {"agents": 0, "generation_writes": 0, "result": "no_change"}


def main() -> int:
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PromotionCoordinationAcceptance)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    summary = {
        "phase": PHASE,
        "kind": "informed scripted installed public-interface verification",
        "native_live_trial": False,
        "tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "passed": result.wasSuccessful(),
        "output": stream.getvalue(),
        "observations": PromotionCoordinationAcceptance.observations,
    }
    dump(OUT / "summary.json", summary)
    sys.stdout.write(stream.getvalue())
    sys.stdout.write(json.dumps({key: summary[key] for key in ("phase", "tests", "failures", "errors", "passed")}) + "\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
