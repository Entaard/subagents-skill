from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

EVALUATION = Path(__file__).resolve().parents[1]
SAGE = EVALUATION.parent
STATE_CLI = SAGE / "scripts/sage_state.py"
KNOWLEDGE_CLI = SAGE / "scripts/sage_knowledge.py"


def sandbox() -> tempfile.TemporaryDirectory[str]:
    root = Path(os.environ["SAGE_EVALUATION_SANDBOX"])
    root.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=root)


def dump(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return path


def write_log(run_dir: Path, events: list[dict[str, Any]]) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "events.jsonl"
    path.write_text("".join(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n" for row in events), encoding="utf-8")
    return path


def strict_json_loads(payload: str) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result
    return json.loads(payload, object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite number: {value}")))


def strict_event_mutations() -> tuple[str, dict[str, str]]:
    control = json.dumps(opened(), separators=(",", ":"))
    return control, {
        "duplicate": control.replace('"v":1', '"v":1,"v":1', 1),
        "nonfinite": control.replace('"constraints":[]', '"constraints":NaN', 1),
    }


def invoke(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *args], cwd=SAGE.parent, text=True, capture_output=True, check=False)


def output(process: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return json.loads(process.stdout)


def event(sequence: int, kind: str, payload: dict[str, Any], run_id: str = "run-1", actor: str = "root") -> dict[str, Any]:
    return {
        "v": 1, "event_id": f"e-{sequence}", "run_id": run_id, "seq": sequence,
        "at": f"2026-09-07T00:00:{sequence:02d}Z", "actor": actor, "type": kind, "payload": payload,
    }


def task(task_id: str, effect: str = "read", dependencies: list[str] | None = None, owner: str = "root") -> dict[str, Any]:
    return {
        "id": task_id, "revision": 1, "objective": f"complete {task_id}", "completion": "observable check passes",
        "dependencies": dependencies or [], "owner": owner, "effect": effect, "scope": [f"artifact/{task_id}"],
        "inputs": [], "returns": ["result", "evidence"], "risk": "low", "verification": "check-1",
        "requested_model": "gpt-5.6-sol", "requested_effort": "high", "fork_turns": "none",
    }


def opened(criteria: list[str] | None = None) -> dict[str, Any]:
    ids = criteria or ["c-1"]
    return event(1, "run.opened", {
        "objective": "verify one bounded outcome", "criteria": [{"id": item, "text": f"criterion {item}"} for item in ids],
        "constraints": [], "next_action": "plan",
    })


def complete_read_run(run_id: str = "run-1") -> list[dict[str, Any]]:
    rows = [opened()]
    rows.append(event(2, "plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 2, "revision_limit": 2, "no_progress": "same failure twice", "trigger_event_ids": ["e-1"], "tasks": [task("t-1")]}))
    rows.append(event(3, "task.admitted", {"task_id": "t-1", "task_revision": 1, "plan_revision": 1}))
    rows.append(event(4, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": ["c-1"], "kind": "observation", "locator": "artifact/result", "sha256": None}))
    rows.append(event(5, "task.result", {"task_id": "t-1", "task_revision": 1, "outcome": "passed", "effect_status": "none", "evidence_ids": ["ev-1"]}))
    rows.append(event(6, "check.recorded", {"check_id": "check-1", "criterion_ids": ["c-1"], "outcome": "passed", "evidence_ids": ["ev-1"]}))
    rows.append(event(7, "checkpoint.written", {"next_action": "close", "baselines": [], "unresolved_user_items": []}))
    rows.append(event(8, "run.closed", {"status": "completed", "criterion_evidence": {"c-1": ["ev-1"]}, "scope_reconciled": True, "remaining_human_items": []}))
    if run_id != "run-1":
        event_ids = {row["event_id"]: f"{run_id}-e-{index}" for index, row in enumerate(rows, 1)}
        for index, row in enumerate(rows, 1):
            row["run_id"] = run_id; row["event_id"] = event_ids[row["event_id"]]
            if "trigger_event_ids" in row["payload"]:
                row["payload"]["trigger_event_ids"] = [event_ids[item] for item in row["payload"]["trigger_event_ids"]]
            if row["payload"].get("corrects_event_id") is not None:
                row["payload"]["corrects_event_id"] = event_ids[row["payload"]["corrects_event_id"]]
    return rows


def event_reference_issues(rows: list[dict[str, Any]]) -> list[str]:
    ids = {row["event_id"] for row in rows}; issues: list[str] = []
    for row in rows:
        for reference in row["payload"].get("trigger_event_ids", []):
            if reference not in ids: issues.append(f"{row['event_id']} trigger {reference}")
        correction = row["payload"].get("corrects_event_id")
        if correction is not None and correction not in ids: issues.append(f"{row['event_id']} correction {correction}")
    return issues


def cues(**values: list[str]) -> dict[str, Any]:
    result = {key: [] for key in ("task", "domain", "artifact", "environment", "risk", "operation", "failure")}
    result.update(values)
    return result


def record(record_id: str = "k-1", revision: int = 1, prior_revision: int | None = None, status: str = "supported", refutation_outcome: str = "passed", evidence_class: str = "scoped_fact") -> dict[str, Any]:
    gates = {
        "scoped_fact": {"repeatable_check": "python3 -m unittest", "environment": "fixture sandbox"},
        "transferable_heuristic": {"contexts": ["fixture-a", "fixture-b"], "corroboration": ["source-1:source-1-e-6"], "confounder_dispositions": ["model held constant"], "counterexample_dispositions": ["none observed"]},
        "causal_guidance": {"method": "controlled", "evidence": ["source-1:source-1-e-6"], "alternative_cause_dispositions": ["input held constant"]},
    }
    return {
        "v": 1, "id": record_id, "revision": revision, "prior_revision": prior_revision, "status": status,
        "evidence_class": evidence_class, "gate_rationale": "class-specific evidence in the declared sandbox",
        "gate_evidence": gates[evidence_class],
        "rule": "Validate the authoritative log before regenerating its projection.",
        "recognizer": cues(operation=["resume"], failure=["stale-snapshot"]),
        "qualifier": {"all": cues(operation=["resume"]), "none": cues(environment=["remote-managed"])},
        "falsifier": "A corrupt log safely regenerates a snapshot.", "evidence_summary": "A local repeatable check passed.",
        "provenance": [{"run_id": "source-1", "locator": "events.jsonl#source-1-e-6"}],
        "alternative_explanations": [], "counterevidence": [],
        "refutation": {"actor": "refuter", "outcome": refutation_outcome, "findings": [], "evidence": ["source-1:source-1-e-6"]},
        "review": {"actor": "reviewer", "outcome": "passed", "dispositions": [], "gate_decision": "supported"},
        "created_at": "2026-09-07T00:00:00Z", "reviewed_at": "2026-09-07T00:01:00Z",
    }
