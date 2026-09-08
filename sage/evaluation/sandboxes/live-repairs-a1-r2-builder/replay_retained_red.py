#!/usr/bin/env python3
"""Replay the critic's four retained malformed v3 commands without changing inputs."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
REPRODUCTIONS = ROOT / "sage/evaluation/sandboxes/live-repairs-a1-r1-critic/retained-validator-reproductions.json"


def main() -> int:
    retained = json.loads(REPRODUCTIONS.read_text(encoding="utf-8"))
    results = []
    for row in retained:
        completed = subprocess.run(row["command"], cwd=ROOT, text=True, capture_output=True, check=False)
        results.append({
            "label": row["label"],
            "command": row["command"],
            "expected_retained_exit_code": row["exit_code"],
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "matches_retained": (
                completed.returncode == row["exit_code"]
                and completed.stdout == row["stdout"]
                and completed.stderr == row["stderr"]
            ),
        })
    print(json.dumps({"classification": "exact_retained_red_replay", "results": results}, indent=2))
    return 0 if all(row["matches_retained"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
