#!/usr/bin/env python3
"""Freeze real paired-case inputs and validate hash-bound comparison evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def strict_load(path: Path) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key in {path}: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite number: {value}")))


def artifact(base: Path, relative: str) -> dict[str, str]:
    path = (base / relative).resolve()
    if not path.is_file():
        raise ValueError(f"frozen artifact is missing: {relative}")
    return {"path": str(path), "sha256": sha256(path)}


def prepare(selection_path: Path) -> dict[str, Any]:
    selection_path = selection_path.resolve(); selection = strict_load(selection_path); base = selection_path.parent
    if selection.get("schema_version") != "sage-case-selection-v1":
        raise ValueError("unsupported case-selection schema")
    shared = {name: artifact(base, selection[name]) for name in ("rubric", "protocol", "environment")}
    rubric = strict_load(Path(shared["rubric"]["path"])); required_dimensions = set(rubric.get("required_case_dimensions", []))
    optional_by_kind = {"creative_interaction_smoke": {"artifact_experience"}, "recovery": {"recovery_behavior"}, "promotion": {"knowledge_behavior"}}
    known_case_dimensions = required_dimensions | {"artifact_experience", "recovery_behavior", "knowledge_behavior"}
    if not required_dimensions or not known_case_dimensions <= set(rubric.get("dimensions", {})):
        raise ValueError("frozen rubric lacks its declared case dimensions")
    if selection.get("root_model") != "gpt-6-astra" or selection.get("root_procedure") != "installed_sage":
        raise ValueError("both arms require the same Astra root and installed Sage procedure")
    rows: list[dict[str, Any]] = []; seen: set[str] = set()
    for index, case in enumerate(selection.get("cases", [])):
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ValueError("case IDs must be nonempty and unique")
        seen.add(case_id); prompt = artifact(base, case["prompt"]); inputs = [artifact(base, item) for item in case["inputs"]]
        checks = artifact(base, case["checks"]); check_data = strict_load(Path(checks["path"]))
        check_ids = [item.get("id") for item in check_data.get("checks", [])]; dimensions = check_data.get("dimensions")
        if not check_ids or len(check_ids) != len(set(check_ids)) or not dimensions or len(dimensions) != len(set(dimensions)):
            raise ValueError(f"{case_id} checks need unique IDs and dimensions")
        expected_dimensions = required_dimensions | optional_by_kind.get(case["kind"], set())
        if set(dimensions) != expected_dimensions:
            missing = sorted(expected_dimensions - set(dimensions)); unknown = sorted(set(dimensions) - known_case_dimensions); inapplicable = sorted((set(dimensions) & known_case_dimensions) - expected_dimensions)
            raise ValueError(f"{case_id} case dimensions differ; missing={missing}, unknown={unknown}, inapplicable={inapplicable}")
        not_applicable = check_data.get("not_applicable")
        expected_not_applicable = known_case_dimensions - expected_dimensions
        if not isinstance(not_applicable, dict) or set(not_applicable) != expected_not_applicable or any(not isinstance(reason, str) or not reason for reason in not_applicable.values()):
            raise ValueError(f"{case_id} must explain every non-applicable case dimension")
        binding = canonical({"prompt": prompt, "inputs": inputs, "checks": checks, "shared": shared})
        rows.append({"case_id": case_id, "kind": case["kind"], "case_binding_sha256": binding,
                     "prompt": prompt, "inputs": inputs, "checks_artifact": checks, "check_ids": check_ids,
                     "dimensions": dimensions, "order": ["treatment", "baseline"] if index % 2 == 0 else ["baseline", "treatment"]})
    if not rows:
        raise ValueError("at least one case is required")
    frozen = {"schema_version": "sage-pairs-v2", "selection": artifact(base, selection_path.name), "shared": shared,
              "root_model": "gpt-6-astra", "root_procedure": "installed_sage",
              "arms": {"treatment": {"eligible_worker_policy": "sage_routing"},
                       "baseline": {"eligible_worker_policy": "astra_for_every_eligible_worker"},
                       "routing_is_only_intended_difference": True}, "pairs": rows}
    frozen["manifest_sha256"] = canonical(frozen); return frozen


def validate_frozen(frozen: dict[str, Any]) -> None:
    body = {key: value for key, value in frozen.items() if key != "manifest_sha256"}
    if frozen.get("manifest_sha256") != canonical(body):
        raise ValueError("frozen manifest hash mismatch")
    artifacts = [frozen["selection"], *frozen["shared"].values()]
    for row in frozen["pairs"]:
        artifacts += [row["prompt"], row["checks_artifact"], *row["inputs"]]
    for item in artifacts:
        path = Path(item["path"])
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise ValueError(f"frozen artifact changed or disappeared: {path}")


def validate_result(data: dict[str, Any], frozen: dict[str, Any]) -> dict[str, Any]:
    validate_frozen(frozen)
    if data.get("frozen_manifest_sha256") != frozen["manifest_sha256"]:
        raise ValueError("result is not bound to this frozen manifest")
    pairs = data.get("pairs")
    if not isinstance(pairs, list) or [row.get("case_id") for row in pairs] != [row["case_id"] for row in frozen["pairs"]]:
        raise ValueError("results must contain every frozen case in order")
    for actual, fixed in zip(pairs, frozen["pairs"]):
        if actual.get("order") != fixed["order"] or actual.get("case_binding_sha256") != fixed["case_binding_sha256"]:
            raise ValueError(f"{fixed['case_id']} pair identity changed")
        for arm_name in ("treatment", "baseline"):
            arm = actual.get(arm_name); evidence = arm.get("execution", {}).get("evidence") if isinstance(arm, dict) else None
            if not isinstance(evidence, list) or not evidence:
                raise ValueError(f"{fixed['case_id']} {arm_name} needs execution evidence")
            evidence_ids: set[str] = set(); kinds: set[str] = set()
            for item in evidence:
                if item.get("id") in evidence_ids or item.get("kind") not in {"transcript", "artifact", "scorecard", "usage"}:
                    raise ValueError(f"{fixed['case_id']} {arm_name} invalid evidence entry")
                path = Path(item.get("path", "")); evidence_ids.add(item["id"]); kinds.add(item["kind"])
                if not path.is_file() or sha256(path) != item.get("sha256"):
                    raise ValueError(f"{fixed['case_id']} {arm_name} evidence hash mismatch")
            execution = arm["execution"]
            if execution.get("status") != "completed" or type(execution.get("exit_code")) is not int or not execution.get("run_id") or not execution.get("started_at") or not execution.get("finished_at") or not {"transcript", "artifact"} <= kinds:
                raise ValueError(f"{fixed['case_id']} {arm_name} lacks completed transcript evidence")
            routing = arm.get("routing", {})
            if routing.get("root_model_requested") != frozen["root_model"] or routing.get("eligible_worker_policy") != frozen["arms"][arm_name]["eligible_worker_policy"]:
                raise ValueError(f"{fixed['case_id']} {arm_name} routing differs from frozen arm")
            if routing.get("root_model_effective") is not None and not isinstance(routing.get("root_model_effective"), str):
                raise ValueError(f"{fixed['case_id']} {arm_name} effective root model must remain string or unknown")
            workers = routing.get("workers")
            if not isinstance(workers, list) or any(not item.get("role") or not item.get("requested_model") or (item.get("effective_model") is not None and not isinstance(item.get("effective_model"), str)) for item in workers):
                raise ValueError(f"{fixed['case_id']} {arm_name} worker routing observations are invalid")
            if arm_name == "baseline" and any(item["requested_model"] != "gpt-6-astra" for item in workers):
                raise ValueError(f"{fixed['case_id']} baseline did not request Astra for every eligible worker")
            checks = arm.get("checks")
            if not isinstance(checks, list) or [item.get("id") for item in checks] != fixed["check_ids"]:
                raise ValueError(f"{fixed['case_id']} {arm_name} check set differs")
            for check in checks:
                refs = check.get("evidence_refs")
                if check.get("outcome") not in {"passed", "failed", "not_tested"} or not refs or not set(refs) <= evidence_ids:
                    raise ValueError(f"{fixed['case_id']} {arm_name} check lacks bound evidence")
            scores = arm.get("scores")
            if not isinstance(scores, dict) or set(scores) != set(fixed["dimensions"]):
                raise ValueError(f"{fixed['case_id']} {arm_name} score dimensions differ")
            for dimension, scored in scores.items():
                value = scored.get("value") if isinstance(scored, dict) else None; refs = scored.get("evidence_refs") if isinstance(scored, dict) else None
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 10 or not refs or not set(refs) <= evidence_ids:
                    raise ValueError(f"{fixed['case_id']} {arm_name} invalid evidenced score: {dimension}")
            scorer = arm.get("scorer", {})
            if scorer.get("independent") is not True or not scorer.get("id") or not scorer.get("evidence_refs") or not set(scorer["evidence_refs"]) <= evidence_ids:
                raise ValueError(f"{fixed['case_id']} {arm_name} lacks independent scorer evidence")
            calls = arm.get("actor_calls"); wall = arm.get("wall_seconds"); operational_refs = arm.get("operational_evidence_refs")
            if type(calls) is not int or calls < 0 or isinstance(wall, bool) or not isinstance(wall, (int, float)) or not math.isfinite(wall) or wall < 0 or not operational_refs or not set(operational_refs) <= evidence_ids:
                raise ValueError(f"{fixed['case_id']} {arm_name} operational observations lack evidence")
            for metric in ("reported_tokens", "reported_money"):
                value = arm.get(metric)
                if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
                    raise ValueError(f"{fixed['case_id']} {arm_name} invalid {metric}")
                if value is not None and (not arm.get("usage_evidence_refs") or not set(arm["usage_evidence_refs"]) <= evidence_ids):
                    raise ValueError(f"{fixed['case_id']} {arm_name} measured usage lacks evidence")
    return {"ok": True, "pair_count": len(pairs), "validation_scope": "hash-bound schema and evidence references; execution authenticity remains an independent-evaluator responsibility"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("prepare"); make.add_argument("selection", type=Path); make.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("validate"); check.add_argument("result", type=Path); check.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.selection); args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        else:
            result = validate_result(strict_load(args.result), strict_load(args.manifest))
        print(json.dumps(result, indent=2, allow_nan=False)); return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr); return 2


if __name__ == "__main__": raise SystemExit(main())
