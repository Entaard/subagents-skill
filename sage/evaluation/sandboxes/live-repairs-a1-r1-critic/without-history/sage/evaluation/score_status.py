#!/usr/bin/env python3
"""Validate a critic review and append it without corrupting gate history."""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
GATE_TYPES = {"design", "verification_design_and_harness", "deterministic", "integration", "live", "final"}


def load_json(path: Path) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite number: {value}")))


def evidence_exists(reference: str) -> bool:
    raw = reference.rsplit(":", 1)[0] if reference.rsplit(":", 1)[-1].isdigit() else reference
    path = Path(raw); path = path if path.is_absolute() else REPOSITORY / path
    return path.exists()


def validate_review(review: dict[str, Any], rubric: dict[str, Any]) -> None:
    required = rubric["required_status_dimensions"]; scores = review.get("scores")
    if not isinstance(scores, dict) or set(scores) != set(required):
        raise ValueError("scores must contain exactly every required status dimension")
    for name in required:
        value = scores[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 10:
            raise ValueError(f"{name} must be a finite number in 0..10")
    score_evidence = review.get("score_evidence")
    if not isinstance(score_evidence, dict) or set(score_evidence) != set(required):
        raise ValueError("score_evidence must cover exactly every score dimension")
    for name, row in score_evidence.items():
        refs = row.get("evidence") if isinstance(row, dict) else None
        if not isinstance(row.get("reason"), str) or not row["reason"] or not isinstance(refs, list) or not refs:
            raise ValueError(f"{name} needs a reason and evidence")
        if any(not isinstance(ref, str) or not evidence_exists(ref) for ref in refs):
            raise ValueError(f"{name} has unresolved evidence")
    errors = review.get("open_error_ids")
    if not isinstance(errors, list) or len(errors) != len(set(errors)) or any(not isinstance(item, str) or not item for item in errors):
        raise ValueError("open_error_ids must be a unique string array")
    if review.get("gate_type") not in GATE_TYPES:
        raise ValueError("gate_type is missing or unsupported")
    verdict = review.get("verdict"); gate_pass = all(scores[name] >= rubric["gate"]["minimum_each"] for name in required) and not errors
    if verdict not in {"pass", "fail"} or (verdict == "pass") != gate_pass:
        raise ValueError("verdict contradicts the per-dimension/open-error gate")
    for field in ("module", "approach_id", "review_id", "reviewed_at"):
        if not isinstance(review.get(field), str) or not review[field]:
            raise ValueError(f"{field} is required")
    if type(review.get("round")) is not int or review["round"] < 1:
        raise ValueError("round must be a positive integer")


def _prior_error_ids(target: dict[str, Any]) -> set[str]:
    return {item["id"] if isinstance(item, dict) else item for item in target.get("open_errors", [])}


def _validate_status_transition(status: dict[str, Any], review: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    module = review["module"]
    if module not in status.get("modules", {}) or status.get("active_module") != module:
        raise ValueError("review must target the current known module")
    target = status["modules"][module]
    if any(status["modules"][dependency].get("gate") != "passed" for dependency in target.get("depends_on", [])):
        raise ValueError("module dependencies have not passed")
    if any(item.get("review_id") == review["review_id"] for item in status.get("history", [])) or any(
        row.get("review_id") == review["review_id"] for module_row in status["modules"].values()
        for approach_row in module_row.get("approaches", []) for row in approach_row.get("rounds", [])
    ):
        raise ValueError("review_id already exists")
    approaches = target.setdefault("approaches", []); approach = next((item for item in approaches if item["approach_id"] == review["approach_id"]), None)
    if approach is None:
        change = review.get("approach_change")
        if review["round"] != 1 or not isinstance(change, dict) or not change.get("cause") or not change.get("material_change"):
            raise ValueError("a new approach needs round 1 and a documented material change")
        approach = {"approach_id": review["approach_id"], "summary": review.get("summary", ""), "rounds": []}
    elif target.get("active_approach_id") != review["approach_id"]:
        raise ValueError("review does not target the active approach")
    expected_round = len(approach["rounds"]) + 1
    maximum = status["quality_gate"]["maximum_rounds_per_approach"]
    if review["round"] != expected_round or expected_round > maximum:
        raise ValueError("review round is not the next unique round or exceeds the approach bound")
    pending = target.get("pending_review")
    if not isinstance(pending, dict) or pending.get("approach_id") != review["approach_id"] or pending.get("round") != review["round"] or pending.get("gate_type") != review["gate_type"]:
        raise ValueError("review does not match the frozen pending candidate")
    prior_ids = _prior_error_ids(target); dispositions = review.get("finding_dispositions", [])
    disposition_ids = {item.get("id") for item in dispositions if isinstance(item, dict)}
    if len(dispositions) != len(disposition_ids) or disposition_ids != prior_ids:
        raise ValueError("every prior open error needs exactly one disposition")
    for item in dispositions:
        disposition = item.get("status"); remains_open = item["id"] in review["open_error_ids"]; unresolved = disposition in {"open", "unresolved", "still_open"}
        if disposition not in {"verified_fixed", "rejected_with_evidence", "open", "unresolved", "still_open"} or unresolved != remains_open or not item.get("evidence") or any(not evidence_exists(ref) for ref in item["evidence"]):
            raise ValueError("prior-error dispositions need status and resolvable evidence")
    return target, approach


def append_review(status: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    rubric = load_json(HERE / "rubric.json"); validate_review(review, rubric)
    result = copy.deepcopy(status); target, approach = _validate_status_transition(result, review)
    if approach not in target["approaches"]:
        target["approaches"].append(approach)
    prior_rounds = copy.deepcopy(approach["rounds"])
    round_record = {key: value for key, value in review.items() if key not in {"module", "summary", "finding_dispositions", "approach_change"}}
    approach["rounds"].append(round_record)
    if approach["rounds"][:-1] != prior_rounds:
        raise AssertionError("prior rounds changed")
    target.setdefault("finding_dispositions", []).extend(copy.deepcopy(review.get("finding_dispositions", [])))
    target.update({"active_approach_id": review["approach_id"], "status": "passed" if review["verdict"] == "pass" else "needs_repair",
                   "gate": "passed" if review["verdict"] == "pass" else "failed", "scores": copy.deepcopy(review["scores"]),
                   "open_errors": list(review["open_error_ids"]), "pending_review": None})
    result.setdefault("history", []).append({"event": "critic_review", **copy.deepcopy(review)})
    order = result["module_order"]; index = order.index(review["module"])
    if review["verdict"] == "pass" and index + 1 < len(order):
        next_module = order[index + 1]; result["active_module"] = next_module
        result["next_action"] = f"Begin {next_module} builder after confirming its dependencies; no downstream pass is implied."
    elif review["verdict"] == "pass":
        result["next_action"] = "All module gates passed; prepare final handoff without adding unobserved claims."
    else:
        maximum = result["quality_gate"]["maximum_rounds_per_approach"]
        if review["round"] >= maximum:
            result["next_action"] = f"Approach {review['approach_id']} exhausted {maximum} rounds; document the failure cause and start a materially changed approach at round 1."
        else:
            result["next_action"] = f"Repair {review['module']} {review['approach_id']} for round {review['round'] + 1}; preserve this failed round."
    result["updated_at"] = review["reviewed_at"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("review", type=Path)
    parser.add_argument("--status", type=Path); parser.add_argument("--output", type=Path); args = parser.parse_args()
    try:
        review = load_json(args.review); rubric = load_json(HERE / "rubric.json"); validate_review(review, rubric)
        result: dict[str, Any] = {"ok": True, "review_id": review["review_id"]}
        if args.status: result = append_review(load_json(args.status), review)
        payload = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.output: args.output.write_text(payload, encoding="utf-8")
        print(payload, end=""); return 0
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr); return 2


if __name__ == "__main__": raise SystemExit(main())
