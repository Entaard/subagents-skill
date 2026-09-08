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


def validate_scored_result(data: dict[str, Any], frozen: dict[str, Any], native_v3: bool) -> dict[str, Any]:
    validate_frozen(frozen)
    if data.get("frozen_manifest_sha256") != frozen["manifest_sha256"]:
        raise ValueError("result is not bound to this frozen manifest")
    pairs = data.get("pairs")
    if not isinstance(pairs, list) or (native_v3 and any(not isinstance(row, dict) for row in pairs)) or [row.get("case_id") for row in pairs] != [row["case_id"] for row in frozen["pairs"]]:
        raise ValueError("results must contain every frozen case in order")
    for actual, fixed in zip(pairs, frozen["pairs"]):
        if actual.get("order") != fixed["order"] or actual.get("case_binding_sha256") != fixed["case_binding_sha256"]:
            raise ValueError(f"{fixed['case_id']} pair identity changed")
        for arm_name in ("treatment", "baseline"):
            arm = actual.get(arm_name)
            if native_v3:
                if not isinstance(arm, dict) or not isinstance(arm.get("execution"), dict):
                    raise ValueError(f"{fixed['case_id']} {arm_name} needs a native execution object")
                evidence = arm["execution"].get("evidence")
            else:
                evidence = arm.get("execution", {}).get("evidence") if isinstance(arm, dict) else None
            if not isinstance(evidence, list) or not evidence:
                raise ValueError(f"{fixed['case_id']} {arm_name} needs execution evidence")
            evidence_ids: set[str] = set(); kinds: set[str] = set(); evidence_kinds: dict[str, str] = {}
            allowed_kinds = {"journal", "artifact", "scorecard", "usage", "native_observation"} if native_v3 else {"transcript", "artifact", "scorecard", "usage"}
            for item in evidence:
                invalid = (not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"] or item["id"] in evidence_ids or item.get("kind") not in allowed_kinds) if native_v3 else (item.get("id") in evidence_ids or item.get("kind") not in allowed_kinds)
                if invalid:
                    raise ValueError(f"{fixed['case_id']} {arm_name} invalid evidence entry")
                path = Path(item.get("path", "")); evidence_ids.add(item["id"]); kinds.add(item["kind"])
                evidence_kinds[item["id"]] = item["kind"]
                if not path.is_file() or sha256(path) != item.get("sha256"):
                    raise ValueError(f"{fixed['case_id']} {arm_name} evidence hash mismatch")
                if native_v3 and item["kind"] in {"journal", "native_observation"} and (not isinstance(item.get("provenance"), str) or not item["provenance"].strip()):
                    raise ValueError(f"{fixed['case_id']} {arm_name} {item['kind']} needs explicit provenance")
            execution = arm["execution"]
            if native_v3:
                identity = (execution.get("run_id"), execution.get("started_at"), execution.get("finished_at"))
                if set(execution) != {"mode", "run_id", "started_at", "finished_at", "completion", "commands", "evidence"} or execution.get("mode") != "native_collaboration" or any(not isinstance(value, str) or not value.strip() for value in identity) or not {"journal", "artifact", "native_observation"} <= kinds:
                    raise ValueError(f"{fixed['case_id']} {arm_name} has invalid native execution fields")
                completion = execution.get("completion")
                if not isinstance(completion, dict) or set(completion) != {"lifecycle", "native_exit_code", "evidence_refs", "exit_evidence_refs"}:
                    raise ValueError(f"{fixed['case_id']} {arm_name} lacks explicit native completion")
                completion_refs = completion.get("evidence_refs"); exit_refs = completion.get("exit_evidence_refs")
                if completion.get("lifecycle") != "completed" or not isinstance(completion_refs, list) or not completion_refs or not set(completion_refs) <= evidence_ids or any(evidence_kinds[x] != "native_observation" for x in completion_refs):
                    raise ValueError(f"{fixed['case_id']} {arm_name} lacks bound native lifecycle completion evidence")
                native_exit = completion.get("native_exit_code")
                if not isinstance(exit_refs, list) or not set(exit_refs) <= evidence_ids:
                    raise ValueError(f"{fixed['case_id']} {arm_name} invalid native exit evidence")
                if native_exit is None:
                    if exit_refs: raise ValueError(f"{fixed['case_id']} {arm_name} unobserved native exit cannot cite exit evidence")
                elif type(native_exit) is not int or not exit_refs or any(evidence_kinds[x] != "native_observation" for x in exit_refs):
                    raise ValueError(f"{fixed['case_id']} {arm_name} native exit needs direct bound evidence")
                commands = execution.get("commands")
                if not isinstance(commands, list):
                    raise ValueError(f"{fixed['case_id']} {arm_name} commands must be an array")
                command_ids: set[str] = set()
                for command in commands:
                    refs = command.get("evidence_refs") if isinstance(command, dict) else None
                    if not isinstance(command, dict) or set(command) != {"id", "exit_code", "evidence_refs"} or not isinstance(command.get("id"), str) or not command["id"] or command["id"] in command_ids or type(command.get("exit_code")) is not int or not isinstance(refs, list) or not refs or not set(refs) <= evidence_ids:
                        raise ValueError(f"{fixed['case_id']} {arm_name} invalid subprocess command evidence")
                    command_ids.add(command["id"])
            elif execution.get("status") != "completed" or type(execution.get("exit_code")) is not int or not execution.get("run_id") or not execution.get("started_at") or not execution.get("finished_at") or not {"transcript", "artifact"} <= kinds:
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
    scope = "hash-bound native lifecycle, command, schema, and evidence references; execution authenticity remains an independent-evaluator responsibility" if native_v3 else "hash-bound schema and evidence references; execution authenticity remains an independent-evaluator responsibility"
    return {"ok": True, "pair_count": len(pairs), "validation_scope": scope}


def validate_result(data: dict[str, Any], frozen: dict[str, Any]) -> dict[str, Any]:
    """Validate the frozen v2 result contract without changing its exit-code rule."""
    return validate_scored_result(data, frozen, False)


def validate_native_shape(data: Any) -> None:
    """Prove v3 nested types before shared validation dereferences or coerces them."""
    def object_value(value: Any, location: str) -> dict:
        if not isinstance(value, dict):
            raise ValueError(f"{location} must be an object")
        return value

    def array(value: Any, location: str) -> list:
        if not isinstance(value, list):
            raise ValueError(f"{location} must be an array")
        return value

    def text(value: Any, location: str, nullable: bool = False) -> None:
        if value is None and nullable:
            return
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{location} must be a nonblank string" + (" or null" if nullable else ""))

    def references(value: Any, location: str) -> None:
        for item in array(value, location):
            text(item, location + " entry")

    result = object_value(data, "result")
    for index, raw_pair in enumerate(array(result.get("pairs"), "pairs")):
        pair_location = f"pairs[{index}]"
        pair = object_value(raw_pair, pair_location)
        for arm_name in ("treatment", "baseline"):
            location = f"{pair_location}.{arm_name}"
            arm = object_value(pair.get(arm_name), location)
            execution = object_value(arm.get("execution"), location + ".execution")
            for name in ("run_id", "started_at", "finished_at"):
                text(execution.get(name), location + ".execution." + name)
            completion = object_value(execution.get("completion"), location + ".completion")
            for name in ("evidence_refs", "exit_evidence_refs"):
                references(completion.get(name), location + ".completion." + name)
            for raw_command in array(execution.get("commands"), location + ".commands"):
                command = object_value(raw_command, location + ".command")
                text(command.get("id"), location + ".command.id")
                references(command.get("evidence_refs"), location + ".command.evidence_refs")
            for raw_evidence in array(execution.get("evidence"), location + ".evidence"):
                evidence = object_value(raw_evidence, location + ".evidence entry")
                for name in ("id", "kind", "path", "sha256"):
                    text(evidence.get(name), location + ".evidence." + name)
                if evidence.get("kind") in ("journal", "native_observation"):
                    text(evidence.get("provenance"), location + ".evidence.provenance")
            routing = object_value(arm.get("routing"), location + ".routing")
            for name in ("root_model_requested", "eligible_worker_policy"):
                text(routing.get(name), location + ".routing." + name)
            text(routing.get("root_model_effective"), location + ".routing.root_model_effective", nullable=True)
            for raw_worker in array(routing.get("workers"), location + ".workers"):
                worker = object_value(raw_worker, location + ".worker")
                for name in ("role", "requested_model"):
                    text(worker.get(name), location + ".worker." + name)
                text(worker.get("effective_model"), location + ".worker.effective_model", nullable=True)
            for raw_check in array(arm.get("checks"), location + ".checks"):
                check = object_value(raw_check, location + ".check")
                for name in ("id", "outcome"):
                    text(check.get(name), location + ".check." + name)
                references(check.get("evidence_refs"), location + ".check.evidence_refs")
            scores = object_value(arm.get("scores"), location + ".scores")
            for dimension, raw_score in scores.items():
                score = object_value(raw_score, location + ".scores." + dimension)
                references(score.get("evidence_refs"), location + ".scores." + dimension + ".evidence_refs")
            scorer = object_value(arm.get("scorer"), location + ".scorer")
            text(scorer.get("id"), location + ".scorer.id")
            references(scorer.get("evidence_refs"), location + ".scorer.evidence_refs")
            references(arm.get("operational_evidence_refs"), location + ".operational_evidence_refs")
            if "usage_evidence_refs" in arm:
                references(arm["usage_evidence_refs"], location + ".usage_evidence_refs")


def validate_native_result(data: dict[str, Any], frozen: dict[str, Any]) -> dict[str, Any]:
    """Validate the explicit native-result v3 contract."""
    if not isinstance(data, dict):
        raise ValueError("native result must be an object")
    if data.get("schema_version") != "sage-live-native-scored-results-v3":
        raise ValueError("unsupported native result schema")
    validate_native_shape(data)
    return {**validate_scored_result(data, frozen, True), "result_schema": data["schema_version"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("prepare"); make.add_argument("selection", type=Path); make.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("validate"); check.add_argument("result", type=Path); check.add_argument("--manifest", type=Path, required=True)
    native = sub.add_parser("validate-native"); native.add_argument("result", type=Path); native.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.selection); args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        elif args.command == "validate":
            result = validate_result(strict_load(args.result), strict_load(args.manifest))
        else:
            result = validate_native_result(strict_load(args.result), strict_load(args.manifest))
        print(json.dumps(result, indent=2, allow_nan=False)); return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr); return 2


if __name__ == "__main__": raise SystemExit(main())
