#!/usr/bin/env python3
"""Operate Sage Light-mode run artifacts, current-run logs, and handoffs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any

SAGE_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = SAGE_ROOT.parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from sage.lib.artifacts import (  # noqa: E402
    load_and_validate,
    render_run,
    validate_handoff_schema,
    validate_run,
    verify_render,
)
from sage.lib.common import (  # noqa: E402
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    load_json,
    sha256_bytes,
    state_root,
    tree_sha256,
    utc_now,
)
from sage.lib.knowledge import get_indexed, lifecycle_lock, list_indexed  # noqa: E402
from sage.lib.facts import INTERNAL_FACT_TYPES, USER_FACT_TYPES, validate_fact_payload  # noqa: E402


TERMINAL_RUN_STATUSES = {"completed", "stopped", "failed"}
COLLECTION_IDS = {
    "briefs": lambda row: (row["brief_id"], row["brief_revision"]),
    "attempts": lambda row: row["attempt_id"],
    "results": lambda row: row["result_id"],
    "artifacts": lambda row: row["artifact_id"],
    "assumptions": lambda row: row["assumption_id"],
    "gaps": lambda row: row["gap_id"],
    "findings": lambda row: row["finding_id"],
    "dispositions": lambda row: row["disposition_id"],
    "verifications": lambda row: row["verification_id"],
    "decisions": lambda row: row["decision_id"],
}


def _run_id() -> str:
    return f"run-{utc_now().replace('-', '').replace(':', '').replace('T', '-').replace('Z', '')}-{uuid.uuid4().hex[:8]}"


def _run_locations(run_id: str, root: Path) -> tuple[Path, Path]:
    return root / "runs/active" / run_id, root / "runs/closed" / run_id


def find_run(run_id: str, root: Path) -> tuple[Path, bool]:
    active, closed = _run_locations(run_id, root)
    if (active / "run.json").is_file():
        return active, False
    if (closed / "run.json").is_file():
        return closed, True
    raise FileNotFoundError(f"run {run_id!r} was not found under {root / 'runs'}")


def planning_run(
    objective: str,
    run_id: str,
    run_directory: Path,
    *,
    bootstrap: bool = False,
    task_effect_class: str = "read_only",
) -> dict[str, Any]:
    now = utc_now()
    record_path = run_directory / "run.md"
    zero = "0" * 64
    revision = 0 if bootstrap else 1
    revision_kind = "bootstrap" if bootstrap else "complete"
    unit_id = "U-SCOUT" if bootstrap else "U1"
    unit_owner = "worker" if bootstrap else "policy_actor"
    unit_effect_class = "read_only" if bootstrap else task_effect_class
    unit_objective = (
        f"Discover only the bounded source and dependency evidence needed to plan: {objective}"
        if bootstrap else objective
    )
    done_when = (
        "A bounded source map supports a complete plan revision, or an explicit gap blocks planning; no task execution is performed."
        if bootstrap else
        "Every requested claim has evidence or an explicit gap, and all required review lenses are settled."
    )
    return {
        "schema_version": "1.0",
        "artifact_kind": "sage.run-record",
        "run_id": run_id,
        "policy_version": "sage-policy/1.0-light",
        "status": "planning",
        "created_at": now,
        "updated_at": now,
        "objective": objective,
        "plan": {
            "plan_id": f"plan-{run_id}",
            "current_revision": revision,
            "revisions": [
                {
                    "revision": revision,
                    "kind": revision_kind,
                    "reason": (
                        "A bounded read-only discovery round is required before a complete plan can be committed."
                        if bootstrap else
                        "The task is sufficiently bounded for an initial complete Light-mode plan; zero delegation remains valid."
                    ),
                    "expected_prior_revision": None,
                    "created_at": now,
                    "admitted_at": None,
                    "admission_policy": {
                        "profile": "bounded-observed",
                        "profile_version": "1.0",
                        "control_strength": "advisory",
                        "usage_provenance": "unknown",
                        "sensor_id": "codex-light-no-comparable-spend-sensor",
                        "sensor_evidence": [
                            {
                                "kind": "observation",
                                "locator": "capability://codex-light/admission",
                                "detail": "Finite unit, attempt, revision, concurrency, and wall-clock bounds are advisory; comparable spend enforcement is unavailable.",
                            }
                        ],
                        "limit_authority": "policy_actor",
                        "compatibility_profile": None,
                        "estimate_multiple": None,
                    },
                    "bounds": {
                        "max_units": None,
                        "max_attempts_per_unit": None,
                        "max_concurrency": None,
                        "max_plan_revisions": None,
                        "max_admission_seconds": None,
                        "planned_agent_count": 1 if bootstrap else 0,
                        "max_admitted_agents": None,
                        "spend_limit": None,
                        "spend_unit": None,
                        "uncapped_attended": False,
                        "no_progress_revision_limit": None,
                    },
                    "units": [
                        {
                            "unit_id": unit_id,
                            "unit_spec_revision": 1,
                            "owner": unit_owner,
                            "objective": unit_objective,
                            "done_when": done_when,
                            "effect_class": unit_effect_class,
                            "dependencies": [],
                            "acceptance_criteria": [
                                {
                                    "criterion_id": "C1",
                                    "text": "The requested deliverable is complete, inside scope, and evidence-backed.",
                                    "evidence_class": "agent_observable",
                                    "required": True,
                                }
                            ],
                            "required_capabilities": (
                                ["workspace.read"]
                                if unit_effect_class == "read_only"
                                else ["workspace.write.scoped", "baseline.capture", "review.freeze"]
                            ),
                            "preferred_capabilities": [
                                {
                                    "predicate": "context.pressure.observable",
                                    "fallback": "record unavailable and use explicit durable handover",
                                }
                            ],
                            "placement_requirements": {
                                "corpus_size": "unknown",
                                "ambiguity": "medium",
                                "reasoning_steps": "many",
                                "tool_needs": (
                                    ["read", "search"]
                                    if unit_effect_class == "read_only"
                                    else ["read", "edit", "shell-test"]
                                ),
                                "latency_preference": "balanced",
                                "cost_ceiling": 1,
                                "independence_required": False,
                                "verification_criticality": "medium",
                            },
                            "estimated_spend": 0,
                        }
                    ],
                    "prior_units": [],
                }
            ],
        },
        "briefs": [],
        "attempts": [],
        "results": [],
        "artifacts": [
            {
                "artifact_id": "ART-RUN-RECORD",
                "kind": "rendered_run_record",
                "media_type": "text/markdown",
                "classification": "internal",
                "sha256": zero,
                "locator": str(record_path.resolve()),
                "produced_by_attempt": None,
                "adoption": "pending",
            }
        ],
        "assumptions": [],
        "gaps": [],
        "findings": [],
        "dispositions": [],
        "verifications": [],
        "decisions": [],
        "coordination_outcome": {
            "state": "open",
            "assessment": "Planning is open; coordination has not yet been judged.",
            "unique_contributions": [],
            "duplicated_work": [],
            "interventions": 0,
            "protocol_failures": 0,
            "critical_path_effect": "Unknown until the run settles.",
            "root_context_effect": "Automatic context occupancy measurement is unavailable unless a supported sensor supplies it.",
            "evidence": [],
        },
        "completion": {
            "state": "open",
            "criteria_status": "open",
            "checks_status": "open",
            "findings_status": "open",
            "scope_status": "open",
            "human_items": [],
            "claim": "",
            "claimed_at": None,
            "deliverable": "",
        },
        "rendered_run_record": {
            "artifact_id": "ART-RUN-RECORD",
            "media_type": "text/markdown",
            "generator_version": "pending",
            "source_state_sha256": zero,
        },
    }


def append_fact(
    run_directory: Path,
    fact_type: str,
    payload: Any,
    *,
    allow_terminal_close: bool = False,
    internal: bool = False,
    classification: str = "internal",
) -> dict[str, Any]:
    allowed = INTERNAL_FACT_TYPES if internal else USER_FACT_TYPES
    if fact_type not in allowed:
        if fact_type in INTERNAL_FACT_TYPES:
            raise ValueError(f"fact type {fact_type!r} is reserved for the Sage runtime")
        raise ValueError(
            f"fact type {fact_type!r} is not a factual current-run event; "
            "knowledge extraction and promotion belong to sage-promote"
        )
    payload_issues = validate_fact_payload(payload, classification)
    if fact_type == "knowledge.assessed":
        outcome = payload.get("outcome") if isinstance(payload, dict) else None
        if outcome not in {"useful", "neutral", "misleading", "missed"}:
            payload_issues.append("knowledge.assessed outcome must be useful, neutral, misleading, or missed")
        if outcome == "missed":
            if not isinstance(payload.get("recognizer"), str) or not payload["recognizer"].strip():
                payload_issues.append("a missed knowledge assessment requires the recognizer that should have loaded")
        elif not isinstance(payload.get("stable_id"), str) or not payload["stable_id"].startswith("sage-knowledge-v1:"):
            payload_issues.append("a loaded knowledge assessment requires its Sage stable ID")
        if not isinstance(payload.get("decision"), str) or not payload["decision"].strip():
            payload_issues.append("knowledge.assessed requires the affected decision")
    if payload_issues:
        raise ValueError("current-run fact rejected before persistence: " + "; ".join(payload_issues))
    run = load_json(run_directory / "run.json")
    if run.get("status") in TERMINAL_RUN_STATUSES and not (
        allow_terminal_close and fact_type in {"run.closed", "run.state_committed"}
    ):
        raise ValueError("the current-run log is closed; append is forbidden")
    log_path = run_directory / "facts.jsonl"
    sequence = 1
    if log_path.exists():
        with log_path.open(encoding="utf-8") as handle:
            for expected, line in enumerate(handle, start=1):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"malformed current-run fact at line {expected}: {error}") from error
                if row.get("sequence") != expected:
                    raise ValueError(f"non-contiguous current-run fact sequence at line {expected}")
                sequence = expected + 1
    fact = {
        "schema_version": "1.0",
        "memory_class": "current_run",
        "sequence": sequence,
        "recorded_at": utc_now(),
        "run_id": run["run_id"],
        "type": fact_type,
        "classification": classification,
        "payload": payload,
    }
    descriptor = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, canonical_json_bytes(fact) + b"\n")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return fact


def _command_start_locked(args: argparse.Namespace, root: Path) -> int:
    objective_issues = validate_fact_payload({"objective": args.objective}, "internal")
    if objective_issues:
        raise ValueError("run objective rejected before persistence: " + "; ".join(objective_issues))
    run_id = args.run_id or _run_id()
    active, closed = _run_locations(run_id, root)
    if active.exists() or closed.exists():
        raise ValueError(f"run ID already exists: {run_id}")
    active.mkdir(parents=True)
    run = planning_run(
        args.objective,
        run_id,
        active,
        bootstrap=args.bootstrap,
        task_effect_class=args.effect_class,
    )
    issues = validate_run(run, SAGE_ROOT)
    if issues:
        shutil.rmtree(active)
        raise ValueError("initial artifact failed validation:\n" + "\n".join(issues))
    atomic_write_json(active / "run.json", run, 0o600)
    append_fact(active, "run.created", {
        "objective": args.objective,
        "mode": "light",
        "effect_class": "read_only" if args.bootstrap else args.effect_class,
        "task_effect_class": args.effect_class,
        "initial_plan_kind": "bootstrap" if args.bootstrap else "complete",
    }, internal=True)
    print(json.dumps({"run_id": run_id, "run_path": str(active / "run.json"), "facts_path": str(active / "facts.jsonl")}, indent=2))
    return 0


def command_start(args: argparse.Namespace) -> int:
    root = Path(args.state_root).resolve() if args.state_root else state_root()
    with lifecycle_lock(root / "lifecycle"):
        return _command_start_locked(args, root)


def command_validate(args: argparse.Namespace) -> int:
    path = Path(args.run_json).resolve()
    run = load_json(path)
    issues = validate_run(run, SAGE_ROOT)
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    print(f"valid: {path}")
    return 0


RUN_TRANSITIONS = {
    "planning": {"planning", "running", "AwaitingHuman", "handed_over", "stopped", "failed", "completed"},
    "running": {"running", "AwaitingHuman", "handed_over", "stopped", "failed", "completed"},
    "AwaitingHuman": {"AwaitingHuman", "running", "handed_over", "stopped", "failed"},
    "handed_over": {"handed_over", "running", "AwaitingHuman", "stopped", "failed", "completed"},
    "stopped": {"stopped"},
    "failed": {"failed"},
    "completed": {"completed"},
}
ATTEMPT_TRANSITIONS = {
    "planned": {"planned", "admitted", "abandoned"},
    "admitted": {"admitted", "prepared", "running", "failed", "unknown", "abandoned"},
    "prepared": {"prepared", "running", "failed", "lost", "unknown", "abandoned"},
    "running": {"running", "idle", "completed", "interrupted", "failed", "lost", "unknown"},
    "idle": {"idle", "running", "completed", "interrupted", "failed", "lost", "unknown"},
    "unknown": {"unknown", "running", "idle", "completed", "failed", "lost", "abandoned"},
    "lost": {"lost", "abandoned"},
    "completed": {"completed"},
    "interrupted": {"interrupted"},
    "failed": {"failed"},
    "abandoned": {"abandoned"},
}


def _rows_by_id(rows: list[dict[str, Any]], identity: Any) -> dict[Any, dict[str, Any]]:
    return {identity(row): row for row in rows}


def _same(left: Any, right: Any) -> bool:
    return canonical_json_bytes(left) == canonical_json_bytes(right)


def _validate_monotonic_state(current: dict[str, Any], candidate: dict[str, Any]) -> None:
    if candidate["status"] not in RUN_TRANSITIONS[current["status"]]:
        raise ValueError(f"illegal run status transition {current['status']} -> {candidate['status']}")

    candidate_revisions = _rows_by_id(candidate["plan"]["revisions"], lambda row: row["revision"])
    attempt_revisions = {row["plan_revision"] for row in current["attempts"]}
    for prior in current["plan"]["revisions"]:
        revision = prior["revision"]
        frozen = (
            prior.get("admitted_at") is not None
            or revision in attempt_revisions
            or revision < candidate["plan"]["current_revision"]
        )
        if frozen and not _same(prior, candidate_revisions[revision]):
            raise ValueError(f"commit-state cannot rewrite immutable plan revision {revision}")

    for collection, identity in (
        ("briefs", lambda row: (row["brief_id"], row["brief_revision"])),
        ("findings", lambda row: row["finding_id"]),
        ("verifications", lambda row: row["verification_id"]),
        ("decisions", lambda row: row["decision_id"]),
    ):
        next_rows = _rows_by_id(candidate[collection], identity)
        for prior in current[collection]:
            if not _same(prior, next_rows[identity(prior)]):
                raise ValueError(f"commit-state cannot rewrite recorded {collection} row {identity(prior)!r}")

    next_attempts = _rows_by_id(candidate["attempts"], lambda row: row["attempt_id"])
    immutable_attempt_fields = (
        "attempt_id", "plan_revision", "unit_id", "unit_spec_revision", "brief_id",
        "brief_revision", "brief_hash", "side_effect_class", "effective_placement",
    )
    for prior in current["attempts"]:
        after = next_attempts[prior["attempt_id"]]
        for field in immutable_attempt_fields:
            if not _same(prior.get(field), after.get(field)):
                raise ValueError(f"commit-state cannot change {field} on attempt {prior['attempt_id']}")
        if after["state"] not in ATTEMPT_TRANSITIONS[prior["state"]]:
            raise ValueError(
                f"illegal attempt transition {prior['attempt_id']}: {prior['state']} -> {after['state']}"
            )
        for field in ("worker_ref", "turn_ref", "started_at", "ended_at", "result_id"):
            before_value = prior.get(field)
            after_value = after.get(field)
            if before_value is not None and after_value != before_value:
                raise ValueError(f"commit-state cannot rewrite {field} on attempt {prior['attempt_id']}")

    next_results = _rows_by_id(candidate["results"], lambda row: row["result_id"])
    for prior in current["results"]:
        after = next_results[prior["result_id"]]
        before_content = {key: value for key, value in prior.items() if key not in {"acceptance", "accepted_at"}}
        after_content = {key: value for key, value in after.items() if key not in {"acceptance", "accepted_at"}}
        if not _same(before_content, after_content):
            raise ValueError(f"commit-state cannot rewrite result content {prior['result_id']}")
        if prior["acceptance"] != "pending" and not _same(prior, after):
            raise ValueError(f"commit-state cannot rewrite final result decision {prior['result_id']}")
        if prior["acceptance"] == "pending" and after["acceptance"] not in {"pending", "accepted", "rejected"}:
            raise ValueError(f"illegal result acceptance for {prior['result_id']}")

    next_artifacts = _rows_by_id(candidate["artifacts"], lambda row: row["artifact_id"])
    for prior in current["artifacts"]:
        if prior["artifact_id"] == current["rendered_run_record"]["artifact_id"]:
            after = next_artifacts[prior["artifact_id"]]
            before_binding = {key: value for key, value in prior.items() if key not in {"sha256", "locator"}}
            after_binding = {key: value for key, value in after.items() if key not in {"sha256", "locator"}}
            if not _same(before_binding, after_binding):
                raise ValueError("commit-state cannot rewrite the rendered-record artifact contract")
            continue
        after = next_artifacts[prior["artifact_id"]]
        before_content = {key: value for key, value in prior.items() if key not in {"adoption", "adopted_under_plan_revision"}}
        after_content = {key: value for key, value in after.items() if key not in {"adoption", "adopted_under_plan_revision"}}
        if not _same(before_content, after_content):
            raise ValueError(f"commit-state cannot rewrite artifact content {prior['artifact_id']}")
        if prior["adoption"] != "pending" and not _same(prior, after):
            raise ValueError(f"commit-state cannot rewrite final artifact adoption {prior['artifact_id']}")

    next_dispositions = _rows_by_id(candidate["dispositions"], lambda row: row["disposition_id"])
    for prior in current["dispositions"]:
        after = next_dispositions[prior["disposition_id"]]
        if prior["status"] != "open" and not _same(prior, after):
            raise ValueError(f"commit-state cannot rewrite final disposition {prior['disposition_id']}")


def command_commit_state(args: argparse.Namespace) -> int:
    """Commit a complete policy-actor-authored state transition after validation."""
    root = Path(args.state_root).resolve() if args.state_root else state_root()
    run_directory, closed = find_run(args.run_id, root)
    if closed:
        raise ValueError("closed-run state is immutable")
    current_path = run_directory / "run.json"
    current = load_and_validate(current_path, SAGE_ROOT)
    candidate = load_and_validate(Path(args.candidate).resolve(), SAGE_ROOT)
    for field in ("schema_version", "artifact_kind", "run_id", "policy_version", "created_at", "objective"):
        if candidate.get(field) != current.get(field):
            raise ValueError(f"commit-state cannot change immutable run field {field}")
    if candidate["plan"]["plan_id"] != current["plan"]["plan_id"]:
        raise ValueError("commit-state cannot change the plan ID")
    if candidate["plan"]["current_revision"] < current["plan"]["current_revision"]:
        raise ValueError("commit-state cannot move the current plan revision backward")
    current_revision_ids = {row["revision"] for row in current["plan"]["revisions"]}
    candidate_revision_ids = {row["revision"] for row in candidate["plan"]["revisions"]}
    if not current_revision_ids.issubset(candidate_revision_ids):
        raise ValueError("commit-state cannot drop a recorded plan revision")
    for collection, identity in COLLECTION_IDS.items():
        prior_ids = {identity(row) for row in current[collection]}
        next_ids = {identity(row) for row in candidate[collection]}
        if not prior_ids.issubset(next_ids):
            raise ValueError(f"commit-state cannot drop recorded {collection}")
    _validate_monotonic_state(current, candidate)
    candidate["updated_at"] = utc_now()
    issues = validate_run(candidate, SAGE_ROOT)
    if issues:
        raise ValueError("candidate became invalid after commit timestamp:\n" + "\n".join(issues))
    atomic_write_json(current_path, candidate, 0o600)
    fact = append_fact(
        run_directory,
        "run.state_committed",
        {
            "candidate_sha256": sha256_bytes(canonical_json_bytes(candidate)),
            "plan_revision": candidate["plan"]["current_revision"],
            "attempt_count": len(candidate["attempts"]),
            "result_count": len(candidate["results"]),
            "finding_count": len(candidate["findings"]),
            "verification_count": len(candidate["verifications"]),
        },
        allow_terminal_close=True,
        internal=True,
    )
    print(json.dumps({"run_id": args.run_id, "run_path": str(current_path), "fact_sequence": fact["sequence"]}, indent=2))
    return 0


def command_append(args: argparse.Namespace) -> int:
    root = Path(args.state_root).resolve() if args.state_root else state_root()
    run_directory, closed = find_run(args.run_id, root)
    if closed:
        raise ValueError("closed-run logs are immutable")
    payload = json.loads(args.payload)
    fact = append_fact(run_directory, args.type, payload, classification=args.classification)
    print(json.dumps(fact, indent=2))
    return 0


def command_fact_types(_args: argparse.Namespace) -> int:
    print(json.dumps({
        "schema_version": "1.0",
        "memory_class": "current_run",
        "allowed_types": sorted(USER_FACT_TYPES),
        "reserved_runtime_types": sorted(INTERNAL_FACT_TYPES),
        "persistable_classifications": ["public", "internal", "confidential"],
        "confidential_payload": "SHA-256 plus protected locator metadata only",
        "forbidden_during_run": ["knowledge extraction", "lesson consolidation", "promotion"],
    }, indent=2))
    return 0


def command_render(args: argparse.Namespace) -> int:
    run_path = Path(args.run_json).resolve()
    output = Path(args.output).resolve() if args.output else run_path.with_name("run.md")
    state_hash, render_hash = render_run(run_path, output, SAGE_ROOT, update_state=not args.no_update)
    print(json.dumps({"run": str(run_path), "output": str(output), "source_state_sha256": state_hash, "render_sha256": render_hash}, indent=2))
    return 0


def command_verify_render(args: argparse.Namespace) -> int:
    issues = verify_render(Path(args.run_json).resolve(), Path(args.output).resolve(), SAGE_ROOT)
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    print("render verified")
    return 0


def command_report(args: argparse.Namespace) -> int:
    root = Path(args.state_root).resolve() if args.state_root else state_root()
    run_directory, closed = find_run(args.run_id, root)
    run_path = run_directory / "run.json"
    output = run_directory / "run.md"
    if closed:
        issues = verify_render(run_path, output, SAGE_ROOT)
        if issues:
            raise ValueError("closed run projection failed verification:\n" + "\n".join(issues))
    else:
        render_run(run_path, output, SAGE_ROOT)
    if args.path_only:
        print(output)
    else:
        sys.stdout.write(output.read_text(encoding="utf-8"))
    return 0


def _handoff_markdown(handoff: dict[str, Any]) -> bytes:
    lines = [
        f"# Sage handoff {handoff['run_id']}",
        "",
        f"Reason: {handoff['reason']}",
        "Observed context fraction: unavailable",
        f"Plan revision: {handoff['plan_revision']}",
        f"Objective: {handoff['objective']}",
        "",
        "## Baselines",
        "",
    ]
    for baseline in handoff["baselines"]:
        lines.append(f"- {baseline['path']}: `{baseline['sha256']}`")
    if not handoff["baselines"]:
        lines.append("- unavailable — resume may check an explicit PATH=SHA256, but admission remains blocked because handoff-time resource identity was not captured")
    lines.extend([
        "",
        "## Attempts and handles",
        "",
    ])
    for attempt in handoff["attempts"]:
        lines.append(
            f"- {attempt['attempt_id']}: {attempt['state']}; effect={attempt['side_effect_class']}; worker={attempt.get('worker_ref') or 'unknown'}; "
            f"turn={attempt.get('turn_ref') or 'unknown'}; result={attempt.get('result_id') or 'none'}"
        )
    if not handoff["attempts"]:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next action",
            "",
            handoff["next_action"],
            "",
            "## Rails and bounds",
            "",
            f"- {json.dumps(handoff['bounds'], sort_keys=True)}",
            "",
            "## Assumptions, gaps, and findings",
            "",
            f"- assumptions: {', '.join(handoff['assumption_ids']) or 'none'}",
            f"- gaps: {', '.join(handoff['gap_ids']) or 'none'}",
            f"- findings: {', '.join(handoff['finding_ids']) or 'none'}",
            f"- human items: {', '.join(handoff['human_items']) or 'none'}",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def _baseline_row(path: Path, expected: str | None = None) -> dict[str, Any]:
    absolute = Path(os.path.abspath(path))
    observed = tree_sha256(absolute)
    if expected is not None and observed != expected:
        raise ValueError(f"baseline hash mismatch for {absolute}: expected {expected}, found {observed}")
    stat_result = absolute.lstat()
    kind = "symlink" if absolute.is_symlink() else "file" if absolute.is_file() else "directory"
    return {
        "path": str(absolute),
        "sha256": observed,
        "kind": kind,
        "device": stat_result.st_dev,
        "inode": stat_result.st_ino,
        "mode": stat_result.st_mode & 0o7777,
    }


def _declared_baseline(value: str) -> dict[str, Any]:
    if "=" not in value:
        raise ValueError("--baseline must be PATH=SHA256")
    raw_path, expected = value.rsplit("=", 1)
    if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
        raise ValueError("--baseline must end in a lowercase SHA-256")
    return _baseline_row(Path(raw_path), expected)


def command_baseline(args: argparse.Namespace) -> int:
    rows = [_baseline_row(Path(value)) for value in args.path]
    print(json.dumps({"schema_version": "1.0", "baselines": rows}, indent=2))
    return 0


def command_handover(args: argparse.Namespace) -> int:
    root = Path(args.state_root).resolve() if args.state_root else state_root()
    run_directory, closed = find_run(args.run_id, root)
    if closed:
        raise ValueError("a closed run cannot hand over")
    occupied = args.occupied_tokens
    window = args.context_window
    if (occupied is None) != (window is None):
        raise ValueError("occupied tokens and context window must be supplied together")
    ratio: float | None = None
    if occupied is not None:
        raise ValueError(
            "automatic context-pressure handover is unavailable on the pinned Codex surface; "
            "caller-supplied token numbers are not a supported sensor. Use explicit handover."
        )
    run_path = run_directory / "run.json"
    run = load_and_validate(run_path, SAGE_ROOT)
    if ratio is None and not any(gap.get("gap_id") == "G-CONTEXT-SENSOR" for gap in run["gaps"]):
        run["gaps"].append(
            {
                "gap_id": "G-CONTEXT-SENSOR",
                "description": "Automatic 30-percent handover detection is unavailable because no supported sensor supplied both occupancy and effective context window.",
                "impact": "The policy actor must initiate explicit handover.",
                "evidence_checked": [
                    {
                        "kind": "observation",
                        "locator": "capability://codex-light/context-pressure",
                        "detail": "No trustworthy numerator and denominator were supplied.",
                    }
                ],
                "owner": "policy_actor",
                "next_action": "Use explicit handover and record any later supported sensor.",
                "status": "accepted_risk",
            }
        )
    baselines = [_baseline_row(Path(value)) for value in args.baseline]
    attempt_state = [
        {
            "attempt_id": attempt["attempt_id"],
            "state": attempt["state"],
            "side_effect_class": attempt["side_effect_class"],
            "worker_ref": attempt.get("worker_ref"),
            "turn_ref": attempt.get("turn_ref"),
            "result_id": attempt.get("result_id"),
        }
        for attempt in run["attempts"]
    ]
    current_revision = next(
        revision
        for revision in run["plan"]["revisions"]
        if revision["revision"] == run["plan"]["current_revision"]
    )
    handoff = {
        "schema_version": "1.0",
        "run_id": run["run_id"],
        "objective": run["objective"],
        "plan_revision": run["plan"]["current_revision"],
        "current_plan": current_revision,
        "reason": args.reason,
        "recorded_at": utc_now(),
        "baselines": baselines,
        "attempts": attempt_state,
        "result_ids": [result["result_id"] for result in run["results"]],
        "assumption_ids": [row["assumption_id"] for row in run["assumptions"]],
        "gap_ids": [row["gap_id"] for row in run["gaps"]],
        "finding_ids": [row["finding_id"] for row in run["findings"]],
        "human_items": list(run["completion"]["human_items"]),
        "bounds": current_revision["bounds"],
        "writer_control": {
            "mode": "advisory_one_writer",
            "external_lease": "unavailable_in_light_mode",
        },
        "next_action": "Reconcile every nonterminal or unknown attempt, verify every baseline, then resume at the next policy judgment.",
    }
    handoff_issues = validate_handoff_schema(handoff, SAGE_ROOT)
    if handoff_issues:
        raise ValueError("handoff.json failed schema validation:\n" + "\n".join(handoff_issues))
    handoff_path = run_directory / "handoff.json"
    handoff_content = canonical_json_bytes(handoff) + b"\n"
    digest = sha256_bytes(handoff_content)
    existing = next((item for item in run["artifacts"] if item["artifact_id"] == "ART-HANDOFF"), None)
    handoff_artifact = {
        "artifact_id": "ART-HANDOFF",
        "kind": "handoff",
        "media_type": "application/json",
        "classification": "confidential",
        "sha256": digest,
        "locator": str(handoff_path.resolve()),
        "produced_by_attempt": None,
        "adoption": "adopted",
        "adopted_under_plan_revision": run["plan"]["current_revision"],
    }
    if existing is None:
        run["artifacts"].append(handoff_artifact)
    else:
        existing.clear()
        existing.update(handoff_artifact)
    existing_decision_ids = {item["decision_id"] for item in run["decisions"]}
    decision_sequence = 1
    while f"D-HANDOVER-{decision_sequence}" in existing_decision_ids:
        decision_sequence += 1
    decision_id = f"D-HANDOVER-{decision_sequence}"
    run["decisions"].append(
        {
            "decision_id": decision_id,
            "kind": "other",
            "decision": "Stop admissions and transfer through ART-HANDOFF.",
            "reason": args.reason if ratio is None else f"{args.sensor_id} reported context fraction {ratio:.6f}.",
            "recorded_at": utc_now(),
            "affects": ["ART-HANDOFF"],
            "adoption": None,
        }
    )
    run["status"] = "handed_over"
    run["updated_at"] = utc_now()
    run["completion"]["deliverable"] = "A durable handoff; the requested task is not complete."
    run["coordination_outcome"]["root_context_effect"] = "State was transferred through a durable artifact; automatic occupancy may be unavailable."
    issues = validate_run(run, SAGE_ROOT)
    if issues:
        raise ValueError("handoff transition failed validation:\n" + "\n".join(issues))
    atomic_write_bytes(handoff_path, handoff_content, 0o600)
    atomic_write_json(run_path, run, 0o600)
    append_fact(
        run_directory,
        "run.handed_over",
        {
            "reason": args.reason,
            "sensor_id": args.sensor_id,
            "context_fraction": ratio,
            "handoff_sha256": digest,
        },
        internal=True,
    )
    print(json.dumps({
        "run_id": args.run_id,
        "handoff": str(handoff_path),
        "projection_command": f"sage-light handoff-projection {args.run_id}",
        "context_fraction": ratio,
        "threshold": 0.30,
    }, indent=2))
    return 0


def _load_valid_handoff(
    run: dict[str, Any],
    run_id: str,
    run_directory: Path,
) -> dict[str, Any]:
    artifact = next((item for item in run["artifacts"] if item["artifact_id"] == "ART-HANDOFF"), None)
    if artifact is None or artifact.get("media_type") != "application/json":
        raise ValueError("run has no authoritative JSON handoff artifact")
    path = Path(artifact["locator"])
    expected_path = (run_directory / "handoff.json").resolve()
    if path != expected_path or path.is_symlink():
        raise ValueError("handoff artifact does not name the run's plain handoff.json authority")
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
        raise ValueError("handoff.json is missing or failed integrity validation")
    handoff = load_json(path)
    schema_issues = validate_handoff_schema(handoff, SAGE_ROOT)
    if schema_issues:
        raise ValueError("handoff.json is malformed:\n" + "\n".join(schema_issues))
    required_fields = {
        "schema_version", "run_id", "objective", "plan_revision", "current_plan", "reason", "recorded_at",
        "baselines", "attempts", "result_ids", "assumption_ids", "gap_ids",
        "finding_ids", "human_items", "bounds", "writer_control", "next_action",
    }
    if (
        not isinstance(handoff, dict)
        or set(handoff) != required_fields
        or handoff.get("schema_version") != "1.0"
        or handoff.get("run_id") != run_id
        or handoff.get("plan_revision") != run["plan"]["current_revision"]
        or not isinstance(handoff.get("baselines"), list)
        or any(
            not isinstance(handoff.get(field), str) or not handoff[field].strip()
            for field in ("objective", "reason", "recorded_at", "next_action")
        )
        or any(
            not isinstance(handoff.get(field), list)
            or any(not isinstance(item, str) or not item for item in handoff[field])
            for field in ("result_ids", "assumption_ids", "gap_ids", "finding_ids", "human_items")
        )
    ):
        raise ValueError("handoff.json has an invalid identity or shape")
    stored_baselines: list[dict[str, Any]] = []
    for row in handoff["baselines"]:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "sha256", "kind", "device", "inode", "mode"}
            or not isinstance(row["path"], str)
            or not isinstance(row["sha256"], str)
            or len(row["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in row["sha256"])
            or row["kind"] not in {"file", "directory", "symlink"}
            or any(not isinstance(row[field], int) for field in ("device", "inode", "mode"))
        ):
            raise ValueError("handoff.json contains an invalid baseline")
        stored_baselines.append(row)
    current_revision = next(
        revision for revision in run["plan"]["revisions"]
        if revision["revision"] == run["plan"]["current_revision"]
    )
    expected_state = {
        "attempts": [{
            "attempt_id": attempt["attempt_id"],
            "state": attempt["state"],
            "side_effect_class": attempt["side_effect_class"],
            "worker_ref": attempt.get("worker_ref"),
            "turn_ref": attempt.get("turn_ref"),
            "result_id": attempt.get("result_id"),
        } for attempt in run["attempts"]],
        "objective": run["objective"],
        "current_plan": current_revision,
        "result_ids": [result["result_id"] for result in run["results"]],
        "assumption_ids": [row["assumption_id"] for row in run["assumptions"]],
        "gap_ids": [row["gap_id"] for row in run["gaps"]],
        "finding_ids": [row["finding_id"] for row in run["findings"]],
        "human_items": list(run["completion"]["human_items"]),
        "bounds": current_revision["bounds"],
        "writer_control": {"mode": "advisory_one_writer", "external_lease": "unavailable_in_light_mode"},
        "next_action": "Reconcile every nonterminal or unknown attempt, verify every baseline, then resume at the next policy judgment.",
    }
    for field, expected in expected_state.items():
        if not _same(handoff.get(field), expected):
            raise ValueError(f"handoff.json is stale for {field}")
    return handoff


def command_handoff_projection(args: argparse.Namespace) -> int:
    root = Path(args.state_root).resolve() if args.state_root else state_root()
    run_directory, _closed = find_run(args.run_id, root)
    run = load_and_validate(run_directory / "run.json", SAGE_ROOT)
    content = _handoff_markdown(_load_valid_handoff(run, args.run_id, run_directory))
    output = run_directory / "handoff.md"
    if args.check:
        if not output.is_file() or output.read_bytes() != content:
            raise ValueError("handoff.md is missing or stale; regenerate it from handoff.json")
        print(f"handoff projection verified: {output}")
    else:
        atomic_write_bytes(output, content, 0o600)
        print(output)
    return 0


def command_resume(args: argparse.Namespace) -> int:
    root = Path(args.state_root).resolve() if args.state_root else state_root()
    run_directory, closed = find_run(args.run_id, root)
    if closed:
        raise ValueError("closed runs are reportable and promotable, not resumable")
    run = load_and_validate(run_directory / "run.json", SAGE_ROOT)
    handoff = _load_valid_handoff(run, args.run_id, run_directory)
    stored_baselines = handoff["baselines"]
    declared = [_declared_baseline(value) for value in args.baseline]
    baseline_rows = {row["path"]: row for row in stored_baselines}
    stored_paths = set(baseline_rows)
    for row in declared:
        prior = baseline_rows.get(row["path"])
        if prior is not None and not _same(prior, row):
            raise ValueError(f"resume baseline cannot override the stored identity for {row['path']}")
        baseline_rows.setdefault(row["path"], row)
    baseline_checks: list[dict[str, Any]] = []
    for row in baseline_rows.values():
        path = Path(row["path"])
        expected = row["sha256"]
        try:
            observed_row = _baseline_row(path)
            identity_match = (
                all(observed_row[field] == row[field] for field in ("kind", "device", "inode", "mode"))
                if row["path"] in stored_paths
                else False
            )
            observed = observed_row["sha256"]
        except FileNotFoundError:
            identity_match = False
            observed = None
        baseline_checks.append({
            "path": str(path),
            "expected": expected,
            "observed": observed,
            "content_match": observed == expected,
            "identity_match": identity_match,
            "identity_bound_at_handoff": row["path"] in stored_paths,
            "match": observed == expected and identity_match,
        })
    unknown_attempts = [item["attempt_id"] for item in run["attempts"] if item["state"] in {"prepared", "running", "idle", "lost", "unknown"}]
    baseline_ready = bool(baseline_checks) and all(item["match"] for item in baseline_checks)
    ready = baseline_ready and not unknown_attempts
    result = {
        "run_id": args.run_id,
        "handoff_verified": True,
        "baseline_checks": baseline_checks,
        "unknown_attempts": unknown_attempts,
        "admission_ready": ready,
        "pause_state": "AwaitingPolicy",
        "next_action": "Reconcile unknown attempts and verify the baseline before a policy actor commits any new admission." if not ready else "Policy actor may review evidence and commit the next revision; no admission was made by resume.",
    }
    append_fact(run_directory, "run.resume_checked", result, internal=True)
    print(json.dumps(result, indent=2))
    return 0


def _command_close_locked(args: argparse.Namespace, root: Path) -> int:
    active, closed = _run_locations(args.run_id, root)
    run_directory = closed if closed.exists() else active
    run_path = run_directory / "run.json"
    run = load_and_validate(run_path, SAGE_ROOT)
    if run["run_id"] != args.run_id:
        raise ValueError("run directory and artifact IDs differ")
    if run["status"] not in TERMINAL_RUN_STATUSES:
        raise ValueError("run status is not terminal")
    if run["status"] == "completed" and run["completion"]["state"] != "closed":
        raise ValueError("completed run must have closed completion state")
    if run_directory == active:
        closed.parent.mkdir(parents=True, exist_ok=True)
        os.replace(active, closed)
    render_run(closed / "run.json", closed / "run.md", SAGE_ROOT)
    closing_facts: list[dict[str, Any]] = []
    facts_path = closed / "facts.jsonl"
    if facts_path.is_file():
        for line in facts_path.read_text(encoding="utf-8").splitlines():
            fact = json.loads(line)
            if fact.get("type") == "run.closed":
                closing_facts.append(fact)
    if not closing_facts:
        append_fact(
            closed,
            "run.closed",
            {"status": run["status"]},
            allow_terminal_close=True,
            internal=True,
        )
    elif len(closing_facts) != 1 or closing_facts[0].get("payload") != {"status": run["status"]}:
        raise ValueError("closed run contains duplicate or mismatched run.closed facts")
    for path in closed.rglob("*"):
        if path.is_file() and not path.is_symlink():
            path.chmod(0o400)
    print(closed)
    return 0


def command_close(args: argparse.Namespace) -> int:
    root = Path(args.state_root).resolve() if args.state_root else state_root()
    with lifecycle_lock(root / "lifecycle"):
        return _command_close_locked(args, root)


def command_knowledge_list(args: argparse.Namespace) -> int:
    root = Path(args.state_root).resolve() if args.state_root else state_root()
    print(json.dumps(list_indexed(root), indent=2, ensure_ascii=False))
    return 0


def command_knowledge_get(args: argparse.Namespace) -> int:
    root = Path(args.state_root).resolve() if args.state_root else state_root()
    print(json.dumps(get_indexed(args.stable_id, root), indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-root", help="override the installed Sage state root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="create a planning run and append-only current-run log")
    start.add_argument("--objective", required=True)
    start.add_argument("--run-id")
    start.add_argument("--bootstrap", action="store_true", help="commit a bounded read-only discovery revision 0")
    start.add_argument(
        "--effect-class",
        choices=("read_only", "mutating"),
        default="read_only",
        help="classify the requested task; a bootstrap revision remains read-only",
    )
    start.set_defaults(func=command_start)

    validate = subparsers.add_parser("validate", help="validate one portable run artifact")
    validate.add_argument("run_json")
    validate.set_defaults(func=command_validate)

    commit = subparsers.add_parser("commit-state", help="validate and atomically commit policy-actor-authored run state")
    commit.add_argument("--run-id", required=True)
    commit.add_argument("--candidate", required=True)
    commit.set_defaults(func=command_commit_state)

    append = subparsers.add_parser("append-fact", help="append one factual current-run row")
    append.add_argument("--run-id", required=True)
    append.add_argument("--type", required=True)
    append.add_argument("--classification", choices=("public", "internal", "confidential"), required=True)
    append.add_argument("--payload", required=True, help="one JSON object")
    append.set_defaults(func=command_append)

    fact_types = subparsers.add_parser("fact-types", help="list allowed factual current-run event types")
    fact_types.set_defaults(func=command_fact_types)

    baseline = subparsers.add_parser("baseline", help="hash and identify one or more source baselines")
    baseline.add_argument("path", nargs="+")
    baseline.set_defaults(func=command_baseline)

    render = subparsers.add_parser("render", help="render a deterministic Markdown projection")
    render.add_argument("run_json")
    render.add_argument("--output")
    render.add_argument("--no-update", action="store_true", help="render without updating binding fields in JSON")
    render.set_defaults(func=command_render)

    verify = subparsers.add_parser("verify-render", help="verify a projection and its state/hash bindings")
    verify.add_argument("run_json")
    verify.add_argument("output")
    verify.set_defaults(func=command_verify_render)

    report = subparsers.add_parser("report", help="validate and print a run's Markdown report")
    report.add_argument("run_id")
    report.add_argument("--path-only", action="store_true")
    report.set_defaults(func=command_report)

    handover = subparsers.add_parser("handover", help="write a durable explicit or sensor-triggered handoff")
    handover.add_argument("run_id")
    handover.add_argument("--reason", default="explicit")
    handover.add_argument("--occupied-tokens", type=int)
    handover.add_argument("--context-window", type=int)
    handover.add_argument("--sensor-id")
    handover.add_argument(
        "--baseline",
        action="append",
        default=[],
        metavar="PATH",
        help="hash and bind a source or artifact baseline into the durable handoff",
    )
    handover.set_defaults(func=command_handover)

    handoff_projection = subparsers.add_parser(
        "handoff-projection",
        help="generate or verify optional handoff.md from authoritative handoff.json",
    )
    handoff_projection.add_argument("run_id")
    handoff_projection.add_argument("--check", action="store_true")
    handoff_projection.set_defaults(func=command_handoff_projection)

    resume = subparsers.add_parser("resume", help="verify handoff, baseline, and unresolved attempts without admitting work")
    resume.add_argument("run_id")
    resume.add_argument("--baseline", action="append", default=[], metavar="PATH=SHA256")
    resume.set_defaults(func=command_resume)

    close = subparsers.add_parser("close", help="freeze a terminal run as a closed-run log")
    close.add_argument("run_id")
    close.set_defaults(func=command_close)

    knowledge = subparsers.add_parser("knowledge", help="read only the promoted-knowledge index")
    knowledge_subparsers = knowledge.add_subparsers(dest="knowledge_command", required=True)
    knowledge_list = knowledge_subparsers.add_parser("list")
    knowledge_list.set_defaults(func=command_knowledge_list)
    knowledge_get = knowledge_subparsers.add_parser("get")
    knowledge_get.add_argument("stable_id", nargs="+")
    knowledge_get.set_defaults(func=command_knowledge_get)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"sage-light: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
