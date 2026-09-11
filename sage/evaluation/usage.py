#!/usr/bin/env python3
"""Summarize explicitly observed leaf-request usage; never estimate native billing."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pairing import strict_load


def summarize(data: dict) -> dict:
    if not isinstance(data, dict) or data.get("schema_version") != "sage-observed-usage-v1":
        raise ValueError("expected sage-observed-usage-v1")
    tasks, requests = data.get("tasks"), data.get("requests")
    if not isinstance(tasks, list) or not tasks or not isinstance(requests, list):
        raise ValueError("tasks must be nonempty and requests an array")
    by_task = {}
    for task in tasks:
        if not isinstance(task, dict) or set(task) != {"id", "accepted", "coverage", "artifact_sha256"}:
            raise ValueError("task requires id, accepted, coverage and artifact_sha256")
        if not isinstance(task["id"], str) or not task["id"] or task["id"] in by_task:
            raise ValueError("task IDs must be unique nonempty strings")
        if type(task["accepted"]) is not bool or task["coverage"] not in {"complete", "partial", "unknown"}:
            raise ValueError("invalid task acceptance or coverage")
        digest = task["artifact_sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("task must bind its scored artifact digest")
        by_task[task["id"]] = {**task, "observed_tokens": 0, "requests": 0, "missing_usage": False}
    seen = set()
    for request in requests:
        required = {"id", "task_id", "attempt", "source", "model", "input_tokens", "cached_input_tokens",
                    "output_tokens", "reasoning_tokens", "reasoning_in_output", "wall_seconds", "kind"}
        if not isinstance(request, dict) or set(request) != required:
            raise ValueError("request fields differ from the observed-usage contract")
        if not isinstance(request["id"], str) or not request["id"] or request["id"] in seen:
            raise ValueError("duplicate or invalid request ID")
        seen.add(request["id"])
        if request["kind"] != "leaf_request":
            raise ValueError("only disjoint leaf requests may be summed; omit parent aggregates")
        if not isinstance(request["task_id"], str) or request["task_id"] not in by_task:
            raise ValueError("unknown request task")
        if type(request["attempt"]) is not int or request["attempt"] < 1:
            raise ValueError("attempt must be positive")
        if not isinstance(request["source"], str) or not request["source"]:
            raise ValueError("observed usage requires a telemetry source locator")
        if request["model"] is not None and not isinstance(request["model"], str):
            raise ValueError("effective model must be observed text or null")
        for field in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens"):
            if request[field] is not None and (type(request[field]) is not int or request[field] < 0):
                raise ValueError(f"{field} must be a nonnegative integer or null")
        if request["reasoning_in_output"] is not None and type(request["reasoning_in_output"]) is not bool:
            raise ValueError("reasoning_in_output must be boolean or null")
        wall = request["wall_seconds"]
        if wall is not None and (type(wall) not in {int, float} or not 0 <= wall < float("inf")):
            raise ValueError("invalid wall time")
        inp, cached, out, reasoning = (request[k] for k in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens"))
        if inp is not None and cached is not None and cached > inp:
            raise ValueError("cached input is a subset of input")
        if request["reasoning_in_output"] is True and out is not None and reasoning is not None and reasoning > out:
            raise ValueError("included reasoning cannot exceed output")
        item = by_task[request["task_id"]]; item["requests"] += 1
        item["observed_tokens"] += (inp or 0) + (out or 0)
        # Unknown counts remain partial, even when their numeric lower bound is zero.
        missing = inp is None or out is None or request["reasoning_in_output"] is None
        if request["reasoning_in_output"] is False:
            item["observed_tokens"] += reasoning or 0
            missing |= reasoning is None
        item["missing_usage"] |= missing
    complete = all(t["coverage"] == "complete" and t["requests"] and not t["missing_usage"] for t in by_task.values())
    accepted = sum(t["accepted"] for t in tasks)
    total = sum(t["observed_tokens"] for t in by_task.values())
    return {"schema_version": "sage-usage-summary-v1", "coverage": "complete" if complete else "partial_or_unknown",
            "observed_tokens_lower_bound": total, "total_tokens": total if complete else None,
            "accepted_tasks": accepted, "evaluated_tasks": len(tasks), "request_count": len(requests),
            "tokens_per_accepted_outcome": total / accepted if complete and accepted else None,
            "tasks": list(by_task.values()), "money": None}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("observations", type=Path)
    args = parser.parse_args()
    try: print(json.dumps(summarize(strict_load(args.observations)), allow_nan=False, sort_keys=True))
    except (ValueError, OSError, TypeError) as exc: parser.exit(2, f"{exc}\n")
