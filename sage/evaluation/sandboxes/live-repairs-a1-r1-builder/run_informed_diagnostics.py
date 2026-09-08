#!/usr/bin/env python3
"""Replay known live findings on copies; never alter or rescore original trials."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SAGE = HERE.parents[2]
ROOT = SAGE.parent
LIVE = SAGE / "evaluation/sandboxes/live-evaluation"
STATE = SAGE / "scripts/sage_state.py"
PAIRING = SAGE / "evaluation/pairing.py"
OUT = HERE / "informed-diagnostics-final"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def command(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {"command": args, "exit_code": completed.returncode,
            "stdout": completed.stdout, "stderr": completed.stderr}


def protected_inventory() -> dict[str, str]:
    roots = [LIVE / "setup", LIVE / "observations", LIVE / "scoring-a1-r1"]
    paths = [SAGE / "evaluation/live-protocol.md", SAGE / "evaluation/rubric.json", SAGE / "docs/LIVE-RESULTS.md"]
    for root in roots:
        paths.extend(path for path in root.rglob("*") if path.is_file())
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(set(paths))}


def event(sequence: int, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {"v": 1, "event_id": f"repair-{sequence}", "run_id": "echo-steps", "seq": sequence,
            "at": f"2026-09-08T00:00:{sequence:02d}Z", "actor": "root", "type": kind, "payload": payload}


def replay_creative() -> dict[str, Any]:
    source = LIVE / "setup/arms/creative-treatment/state/runs/echo-steps"
    target = OUT / "creative-original-copy"
    shutil.copytree(source, target)
    original = (target / "events.jsonl").read_bytes()
    wave = [
        event(23, "agent.not_created", {"task_id": "review", "task_revision": 1,
              "reason": "recorded native thread-limit rejection returned no handle",
              "evidence_ids": ["dispatch-block"]}),
        event(24, "task.result", {"task_id": "review", "task_revision": 1, "outcome": "failed",
              "effect_status": "none", "evidence_ids": ["dispatch-block"]}),
        event(25, "run.closed", {"status": "stopped", "criterion_evidence": {},
              "scope_reconciled": False,
              "remaining_human_items": ["Independent review and integration were not completed in this original run."]}),
    ]
    wave_path = OUT / "creative-reconciliation-wave.jsonl"
    wave_path.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in wave), encoding="utf-8")
    append = command([sys.executable, str(STATE), "append", "--run-dir", str(target), "--events", str(wave_path)])
    validate = command([sys.executable, str(STATE), "validate", "--run-dir", str(target), "--terminal"])
    report = command([sys.executable, str(STATE), "report", "--run-dir", str(target), "--write"])
    rendered = (target / "report.md").read_text(encoding="utf-8")
    assertions = {
        "append_exit_zero": append["exit_code"] == 0,
        "terminal_exit_zero": validate["exit_code"] == 0,
        "report_exit_zero": report["exit_code"] == 0,
        "original_history_is_prefix": (target / "events.jsonl").read_bytes().startswith(original),
        "original_event_count": len(original.splitlines()) == 22,
        "stopped_not_passed": "Status: stopped" in rendered and "review: failed" in rendered and "review: passed" not in rendered,
        "no_invented_agent_request": not any(row["type"] == "agent.requested" for row in wave),
    }
    if not all(assertions.values()):
        raise RuntimeError(f"creative reconciliation failed: {assertions}")
    return {"classification": "informed_diagnostic", "source_run": str(source), "copy": str(target),
            "source_events_sha256": hashlib.sha256(original).hexdigest(), "wave": str(wave_path),
            "append": append, "terminal_validation": validate, "report": report, "assertions": assertions}


def replay_reports() -> dict[str, Any]:
    sources = {
        "data-treatment": "setup/arms/data-treatment/state/run",
        "promotion-treatment": "setup/arms/promotion-treatment/state/runs/promotion-live",
        "recovery-treatment": "setup/arms/recovery-treatment/state/runs/catalog-export",
        "creative-treatment": "setup/arms/creative-treatment/state/runs/echo-steps-continuation",
        "code-baseline": "setup/arms/code-baseline/state/decoder-run",
        "code-treatment": "setup/arms/code-treatment/state/run",
        "data-baseline": "setup/arms/data-baseline/state/run",
    }
    rows = []
    for label, relative in sources.items():
        source = LIVE / relative; target = OUT / "report-copies" / label
        shutil.copytree(source, target)
        before = sha(target / "events.jsonl")
        result = command([sys.executable, str(STATE), "report", "--run-dir", str(target), "--write"])
        rendered = (target / "report.md").read_text(encoding="utf-8")
        snapshot = json.loads((target / "snapshot.json").read_text(encoding="utf-8"))
        expected_unknown_handles = [handle for handle, agent in snapshot["agents"].items()
                                    if any(agent.get(field) == "unknown" for field in ("effective_model", "effective_effort", "lifecycle", "effect_status"))]
        assertions = {
            "report_exit_zero": result["exit_code"] == 0,
            "events_unchanged": sha(target / "events.jsonl") == before,
            "unknown_not_denied": "## Unknowns\n\n- None" not in rendered,
            "untested_not_denied": "## Untested evidence\n\n- None" not in rendered,
            "empty_is_qualified": "No entries recorded." in rendered,
            "stored_unknown_handles_rendered": all(handle in rendered for handle in expected_unknown_handles),
        }
        if not all(assertions.values()):
            raise RuntimeError(f"report replay failed for {label}: {assertions}")
        rows.append({"arm": label, "source": str(source), "copy": str(target), "command": result,
                     "report_sha256": sha(target / "report.md"), "unknown_handles": expected_unknown_handles,
                     "assertions": assertions})
    return {"classification": "informed_diagnostic", "reports": rows}


def exit_codes(value: Any) -> list[int]:
    found: list[int] = []
    if isinstance(value, dict):
        if type(value.get("exit_code")) is int:
            found.append(value["exit_code"])
        for child in value.values():
            found.extend(exit_codes(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(exit_codes(child))
    return found


def replay_native_result() -> dict[str, Any]:
    manifest_path = LIVE / "setup/frozen-pairs.json"
    original_path = LIVE / "scoring-a1-r1/paired-results.json"
    adapted = copy.deepcopy(json.loads(original_path.read_text(encoding="utf-8")))
    adapted["schema_version"] = "sage-live-native-scored-results-v3"
    adapted["diagnostic_classification"] = "informed_diagnostic_from_historical_result"
    adapted["source_result_sha256"] = sha(original_path)
    command_count = 0
    for pair in adapted["pairs"]:
        for arm_name in ("treatment", "baseline"):
            arm = pair[arm_name]; old = arm["execution"]
            for evidence in old["evidence"]:
                if evidence["id"] == "journal": evidence["kind"] = "journal"
                if evidence["id"] == "outer": evidence["kind"] = "native_observation"
            checks = next(item for item in old["evidence"] if item["id"] == "checks")
            captured = exit_codes(json.loads(Path(checks["path"]).read_text(encoding="utf-8")))
            commands = [{"id": f"captured-check-{index + 1}", "exit_code": code, "evidence_refs": ["checks"]}
                        for index, code in enumerate(captured)]
            command_count += len(commands)
            arm["execution"] = {
                "mode": "native_collaboration", "run_id": old["run_id"],
                "started_at": old["started_at"], "finished_at": old["finished_at"],
                "completion": {"lifecycle": "completed", "native_exit_code": None,
                               "evidence_refs": ["outer"], "exit_evidence_refs": []},
                "commands": commands, "evidence": old["evidence"],
            }
    adapted_path = OUT / "paired-results-v3-adapted-informed-diagnostic.json"
    save(adapted_path, adapted)
    legacy = command([sys.executable, str(PAIRING), "validate", str(original_path), "--manifest", str(manifest_path)])
    successor = command([sys.executable, str(PAIRING), "validate-native", str(adapted_path), "--manifest", str(manifest_path)])
    assertions = {
        "original_v2_still_rejected": legacy["exit_code"] == 2 and "lacks completed transcript evidence" in legacy["stderr"],
        "adapted_v3_diagnostic_validates": successor["exit_code"] == 0,
        "native_exits_remain_null": all(pair[arm]["execution"]["completion"]["native_exit_code"] is None
                                        for pair in adapted["pairs"] for arm in ("treatment", "baseline")),
        "actual_subprocess_exits_are_separate": command_count > 0,
        "journals_are_not_transcripts": all(next(item for item in pair[arm]["execution"]["evidence"] if item["id"] == "journal")["kind"] == "journal"
                                           for pair in adapted["pairs"] for arm in ("treatment", "baseline")),
    }
    if not all(assertions.values()):
        raise RuntimeError(f"native result replay failed: {assertions}")
    return {"classification": "informed_diagnostic", "source": str(original_path),
            "adapted": str(adapted_path), "legacy_validation": legacy,
            "successor_validation": successor, "captured_command_count": command_count, "assertions": assertions}


def main() -> int:
    if OUT.exists():
        raise RuntimeError(f"fresh output directory already exists: {OUT}")
    OUT.mkdir(parents=True)
    before = protected_inventory(); save(OUT / "protected-before.json", before)
    creative = replay_creative(); reports = replay_reports(); native = replay_native_result()
    after = protected_inventory(); save(OUT / "protected-after.json", after)
    guards = {"file_count": len(before), "unchanged": before == after,
              "inventory_sha256": hashlib.sha256(json.dumps(before, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
    if not guards["unchanged"]:
        raise RuntimeError("a protected original changed during diagnostics")
    result = {"classification": "informed_diagnostic_only", "historical_scores_changed": False,
              "creative": creative, "reports": reports, "native_result": native, "protected_guards": guards}
    save(OUT / "diagnostic-summary.json", result)
    print(json.dumps({"ok": True, "summary": str(OUT / "diagnostic-summary.json"), **guards}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
