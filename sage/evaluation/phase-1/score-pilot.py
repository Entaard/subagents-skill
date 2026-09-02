#!/usr/bin/env python3
"""Validate and calculate the frozen Phase 1 decision gates from locked pair records."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


TASK_IDS = [f"P1-T{index:02d}" for index in range(1, 21)]
WALL_TIME_ELIGIBLE_TASK_IDS = set(TASK_IDS[:-1])
CAUSES = {
    "policy_judgment", "model_capability", "brief_specification",
    "deterministic_coordination_bookkeeping", "environment", "unresolved",
}


def comparable(pair: dict[str, Any]) -> bool:
    control = pair["control"].get("normalized_total_tokens")
    treatment = pair["treatment"].get("normalized_total_tokens")
    if type(control) is not int or type(treatment) is not int or control < 0 or treatment < 0:
        return False
    if control > 250000 or treatment > 250000:
        return False
    return treatment == 0 if control == 0 else treatment <= 1.25 * control


def score(data: dict[str, Any]) -> dict[str, Any]:
    pairs = data.get("pairs")
    if not isinstance(pairs, list) or [row.get("task_id") for row in pairs] != TASK_IDS:
        raise ValueError("locked score input must contain all 20 frozen task pairs in order")
    for row in pairs:
        for arm in ("control", "treatment"):
            value = row.get(arm, {}).get("score")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
                raise ValueError(f"{row['task_id']} {arm} score is missing or outside 0..100")
            tokens = row[arm].get("normalized_total_tokens")
            if type(tokens) is not int or tokens < 0:
                raise ValueError(f"{row['task_id']} {arm} normalized token total must be a non-negative integer")
            interventions = row[arm].get("interventions")
            if interventions is not None and (type(interventions) is not int or interventions < 0):
                raise ValueError(f"{row['task_id']} {arm} interventions must be a non-negative integer")
            wall_seconds = row[arm].get("wall_seconds")
            if wall_seconds is not None and (
                isinstance(wall_seconds, bool)
                or not isinstance(wall_seconds, (int, float))
                or not math.isfinite(wall_seconds)
                or wall_seconds < 0
            ):
                raise ValueError(f"{row['task_id']} {arm} wall time must be a finite non-negative number")
            occupied = row[arm].get("maximum_occupied_tokens")
            window = row[arm].get("effective_context_window")
            if (occupied is None) != (window is None):
                raise ValueError(f"{row['task_id']} {arm} occupancy requires both numerator and context window")
            if occupied is not None and (
                type(occupied) is not int
                or type(window) is not int
                or occupied < 0
                or window <= 0
                or occupied > window
            ):
                raise ValueError(f"{row['task_id']} {arm} occupancy values are invalid")
        cause = row.get("treatment_primary_cause")
        if row.get("treatment_miss") and cause not in CAUSES:
            raise ValueError(f"{row['task_id']} treatment miss lacks one frozen primary cause")
    safety_failures = [row["task_id"] for row in pairs if row.get("treatment_only_safety_regression")]
    deltas = [row["treatment"]["score"] - row["control"]["score"] for row in pairs]
    regressions = [row["task_id"] for row, delta in zip(pairs, deltas) if row.get("unexplained_semantic_regression") or delta <= -5]
    comparable_ids = [row["task_id"] for row in pairs if comparable(row)]
    comparable_pairs = [row for row in pairs if comparable(row)]
    aggregate_spend_ok = False
    if len(comparable_pairs) == 20:
        control_sum = sum(row["control"]["normalized_total_tokens"] for row in pairs)
        treatment_sum = sum(row["treatment"]["normalized_total_tokens"] for row in pairs)
        aggregate_spend_ok = treatment_sum == 0 if control_sum == 0 else treatment_sum <= 1.25 * control_sum
    improvements = [
        row["task_id"] for row, delta in zip(pairs, deltas)
        if delta >= 5 and comparable(row)
    ]

    known_interventions = [
        row for row in comparable_pairs
        if isinstance(row["control"].get("interventions"), int) and isinstance(row["treatment"].get("interventions"), int)
    ]
    intervention_signal = False
    intervention_reduction: float | None = None
    if len(known_interventions) >= 16:
        control_total = sum(row["control"]["interventions"] for row in known_interventions)
        treatment_total = sum(row["treatment"]["interventions"] for row in known_interventions)
        if control_total:
            intervention_reduction = (control_total - treatment_total) / control_total
            intervention_signal = intervention_reduction >= 0.25

    occupancy_pairs = [
        row for row in comparable_pairs
        if all(isinstance(row[arm].get("maximum_occupied_tokens"), int) and isinstance(row[arm].get("effective_context_window"), int) and row[arm]["effective_context_window"] > 0 for arm in ("control", "treatment"))
    ]
    occupancy_signal = False
    occupancy_ratio: float | None = None
    if len(occupancy_pairs) >= 16:
        control_mean = statistics.mean(row["control"]["maximum_occupied_tokens"] / row["control"]["effective_context_window"] for row in occupancy_pairs)
        treatment_mean = statistics.mean(row["treatment"]["maximum_occupied_tokens"] / row["treatment"]["effective_context_window"] for row in occupancy_pairs)
        if control_mean:
            occupancy_ratio = treatment_mean / control_mean
            occupancy_signal = occupancy_ratio <= 0.75

    wall_pairs = [
        row for row in comparable_pairs
        if row["task_id"] in WALL_TIME_ELIGIBLE_TASK_IDS
        and isinstance(row["control"].get("wall_seconds"), (int, float))
        and isinstance(row["treatment"].get("wall_seconds"), (int, float))
        and row["control"]["wall_seconds"] > 0
    ]
    wall_ratio = statistics.median(row["treatment"]["wall_seconds"] / row["control"]["wall_seconds"] for row in wall_pairs) if len(wall_pairs) >= 16 else None
    wall_signal = wall_ratio is not None and wall_ratio <= 0.80

    noninferior = not regressions and statistics.mean(deltas) >= -5
    material_signals = {
        "quality_improvement_on_three": len(improvements) >= 3,
        "intervention_reduction": intervention_signal,
        "root_context_reduction": occupancy_signal,
        "wall_time_reduction": wall_signal,
    }
    policy_value = not safety_failures and noninferior and aggregate_spend_ok and any(material_signals.values())
    core_failures = [
        row["task_id"] for row in pairs
        if row.get("treatment_primary_cause") == "deterministic_coordination_bookkeeping" and row.get("required_correction")
    ]
    root_loss = data.get("root_loss", {})
    root_loss_shortcut = root_loss.get("valid_executable_inability") is True
    managed_need = policy_value and (len(core_failures) >= 3 or root_loss_shortcut)
    decision = "stop_for_safety" if safety_failures else "policy_value_failed" if not policy_value else "continue_to_managed_feasibility" if managed_need else "ship_light_and_stop_runtime_program"
    return {
        "safety_passed": not safety_failures,
        "safety_failures": safety_failures,
        "mean_paired_score_delta": statistics.mean(deltas),
        "unexplained_semantic_regressions": regressions,
        "noninferior": noninferior,
        "spend_comparable_pair_ids": comparable_ids,
        "aggregate_spend_comparable": aggregate_spend_ok,
        "quality_improvement_pair_ids": improvements,
        "intervention_coverage": len(known_interventions),
        "intervention_reduction": intervention_reduction,
        "occupancy_coverage": len(occupancy_pairs),
        "occupancy_ratio": occupancy_ratio,
        "wall_time_coverage": len(wall_pairs),
        "median_wall_time_ratio": wall_ratio,
        "material_signals": material_signals,
        "policy_value_passed": policy_value,
        "core_addressable_corrections": core_failures,
        "root_loss_shortcut": root_loss_shortcut,
        "managed_need_passed": managed_need,
        "decision": decision,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = score(json.loads(Path(args.input).read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"score-pilot: {error}", file=sys.stderr)
        return 1
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
