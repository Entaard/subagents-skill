#!/usr/bin/env python3
"""Reproducible start-gate checker for the frozen Sage Phase 1 paired pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
SAGE_ROOT = HERE.parents[1]
REPOSITORY_ROOT = SAGE_ROOT.parent
FROZEN_FILES = ("preregistration.md", "root-loss-fixture.json", "rubric.json", "tasks.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        if "__pycache__" in child.parts or child.suffix == ".pyc":
            continue
        rows.append({"path": child.relative_to(path).as_posix(), "sha256": sha256_file(child)})
    return rows


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def expected_frozen_hashes() -> dict[str, str]:
    expected: dict[str, str] = {}
    for line in (HERE / "PREREGISTRATION.sha256").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        expected[name.strip()] = digest
    return expected


def verify_frozen() -> dict[str, Any]:
    expected = expected_frozen_hashes()
    observed = {name: sha256_file(HERE / name) for name in FROZEN_FILES}
    tasks = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))
    task_rows = tasks.get("tasks", [])
    task_ids = [row.get("task_id") for row in task_rows]
    baseline = tasks.get("baseline_revision")
    baseline_check = subprocess.run(
        ["git", "cat-file", "-e", f"{baseline}^{{commit}}"],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    missing_corpus: list[str] = []
    for paths in tasks.get("corpus_sets", {}).values():
        for relative in paths:
            check = subprocess.run(
                ["git", "cat-file", "-e", f"{baseline}:{relative}"],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            if check.returncode != 0:
                missing_corpus.append(relative)
    issues: list[str] = []
    if observed != expected:
        issues.append("one or more frozen preregistration hashes differ")
    if len(task_rows) != 20 or task_ids != [f"P1-T{index:02d}" for index in range(1, 21)]:
        issues.append("the task manifest is not the frozen contiguous set of 20 tasks")
    if baseline_check.returncode != 0:
        issues.append(f"baseline commit is unavailable: {baseline}")
    if missing_corpus:
        issues.append("baseline corpus paths are unavailable: " + ", ".join(sorted(set(missing_corpus))))
    return {
        "passed": not issues,
        "expected_sha256": expected,
        "observed_sha256": observed,
        "baseline_revision": baseline,
        "task_count": len(task_rows),
        "missing_corpus": sorted(set(missing_corpus)),
        "issues": issues,
    }


def generate_schema(output: Path) -> tuple[str, list[str]]:
    version = subprocess.run(["codex", "--version"], text=True, capture_output=True, check=False)
    version_text = version.stdout.strip()
    if version.returncode != 0:
        raise ValueError(f"cannot identify Codex build: {version.stderr.strip()}")
    generated = subprocess.run(
        ["codex", "app-server", "generate-json-schema", "--experimental", "--out", str(output)],
        text=True,
        capture_output=True,
        check=False,
    )
    if generated.returncode != 0:
        raise ValueError(f"cannot generate the pinned App Server schema: {generated.stderr.strip()}")
    return version_text, sorted(path.name for path in output.glob("*.json"))


def _load_schema(schema_dir: Path, relative: str) -> dict[str, Any] | None:
    path = schema_dir / relative
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def inspect_capabilities(schema_dir: Path) -> dict[str, Any]:
    goal = _load_schema(schema_dir, "v2/ThreadGoalSetParams.json")
    usage = _load_schema(schema_dir, "v2/ThreadTokenUsageUpdatedNotification.json")
    raw = _load_schema(schema_dir, "v2/RawResponseCompletedNotification.json")
    token_budget = (goal or {}).get("properties", {}).get("tokenBudget")
    usage_definitions = (usage or {}).get("definitions", {})
    breakdown = usage_definitions.get("TokenUsageBreakdown", {}).get("properties", {})
    thread_usage = usage_definitions.get("ThreadTokenUsage", {}).get("properties", {})
    telemetry_fields = sorted(set(breakdown) & {"inputTokens", "outputTokens", "totalTokens"})
    occupancy_names = {
        "occupiedTokens", "currentContextTokens", "contextOccupancy", "contextTokensUsed",
    }
    serialized = json.dumps(usage or {}, sort_keys=True)
    occupancy_fields = sorted(name for name in occupancy_names if f'"{name}"' in serialized)
    hard_cap_proved = bool(
        isinstance(token_budget, dict)
        and token_budget.get("x-hard-enforcement") is True
        and token_budget.get("x-accounting-unit") == "normalized_input_plus_output_tokens"
        and token_budget.get("x-scope") == "entire_arm_including_subagents"
    )
    return {
        "thread_goal_token_budget_schema": token_budget,
        "usage_telemetry_fields": telemetry_fields,
        "model_context_window_reported": "modelContextWindow" in thread_usage,
        "root_context_occupancy_fields": occupancy_fields,
        "raw_response_usage_available": raw is not None,
        "hard_250k_normalized_arm_cap_proved": hard_cap_proved,
        "hard_cap_reason": (
            "The schema exposes an unqualified integer tokenBudget and usage telemetry, but does not bind the budget "
            "to normalized input-plus-output tokens, hard enforcement, or aggregate root-and-subagent arm scope."
            if not hard_cap_proved else "The schema carries all frozen enforcement and accounting qualifiers."
        ),
        "occupancy_reason": (
            "modelContextWindow is a denominator; no current occupied-context numerator is exposed."
            if not occupancy_fields else "A candidate occupancy numerator is exposed and still requires semantic verification."
        ),
    }


def component_hashes(schema_dir: Path, codex_version: str) -> dict[str, Any]:
    skill_tree = SAGE_ROOT / "skills/sage"
    return {
        "treatment_skill_tree_sha256": canonical_sha256(tree_manifest(skill_tree)),
        "control_prompt_sha256": sha256_file(HERE / "prompts/control.txt"),
        "treatment_prompt_sha256": sha256_file(HERE / "prompts/treatment.txt"),
        "runner_sha256": sha256_file(HERE / "pilot.py"),
        "scorer_sha256": sha256_file(HERE / "score-pilot.py"),
        "root_loss_fixture_sha256": sha256_file(HERE / "root-loss-fixture.json"),
        "app_server_schema_tree_sha256": canonical_sha256(tree_manifest(schema_dir)),
        "codex_version": codex_version,
    }


def preflight(schema_dir: Path | None = None) -> dict[str, Any]:
    frozen = verify_frozen()
    temporary: tempfile.TemporaryDirectory[str] | None = None
    if schema_dir is None:
        temporary = tempfile.TemporaryDirectory(prefix="sage-phase1-schema-")
        schema_dir = Path(temporary.name)
        codex_version, schema_files = generate_schema(schema_dir)
    else:
        schema_dir = schema_dir.resolve()
        version = subprocess.run(["codex", "--version"], text=True, capture_output=True, check=False)
        codex_version = version.stdout.strip() if version.returncode == 0 else "unknown"
        schema_files = sorted(path.name for path in schema_dir.glob("*.json"))
    capabilities = inspect_capabilities(schema_dir)
    components = component_hashes(schema_dir, codex_version)
    failed: list[dict[str, str]] = []
    if not frozen["passed"]:
        failed.append({"gate": "frozen_inputs", "reason": "; ".join(frozen["issues"])})
    if not capabilities["hard_250k_normalized_arm_cap_proved"]:
        failed.append({"gate": "normalized_spend_cap", "reason": capabilities["hard_cap_reason"]})
    failed.append({
        "gate": "root_loss_driver",
        "reason": "No pinned external driver can kill and restart this root while controlling and hiding actual native start outcomes; a prose or simulated driver is forbidden by RL-01.",
    })
    report = {
        "schema_version": "1.0",
        "study_id": "sage-light-policy-value-pilot-v1",
        "status": "ready" if not failed else "blocked_before_outcomes",
        "outcomes_observed": False,
        "network_policy": "disabled_required_not_started",
        "per_arm_cap": {"value": 250000, "unit": "normalized_input_plus_output_tokens", "enforced": capabilities["hard_250k_normalized_arm_cap_proved"]},
        "frozen_inputs": frozen,
        "runtime_capabilities": capabilities,
        "component_hashes": components,
        "schema_files": schema_files,
        "failed_start_gates": failed,
        "decision": "Do not start any of the 20 pairs or the root-loss fixture while a start gate is failed.",
    }
    if temporary is not None:
        temporary.cleanup()
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify-frozen")
    verify.add_argument("--output")
    gate = subparsers.add_parser("preflight")
    gate.add_argument("--schema-dir")
    gate.add_argument("--output")
    run = subparsers.add_parser("run")
    run.add_argument("--schema-dir")
    run.add_argument("--output")
    return parser


def _emit(value: dict[str, Any], output: str | None) -> None:
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if output:
        Path(output).write_text(payload, encoding="utf-8")
    print(payload, end="")


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "verify-frozen":
        report = verify_frozen()
        _emit(report, args.output)
        return 0 if report["passed"] else 1
    report = preflight(Path(args.schema_dir) if args.schema_dir else None)
    _emit(report, args.output)
    if args.command == "run" and report["status"] != "ready":
        print("pilot: start gate failed; zero outcomes were generated", file=sys.stderr)
        return 2
    if args.command == "run":
        print("pilot: all start gates passed, but arm execution requires the pinned external harness", file=sys.stderr)
        return 3
    return 0 if report["status"] == "ready" else 2


if __name__ == "__main__":
    sys.exit(main())
