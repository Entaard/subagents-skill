#!/usr/bin/env python3
"""Run the active v3 validator against the critic's exact four retained inputs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PAIRING = ROOT / "sage/evaluation/pairing.py"
INPUTS = ROOT / "sage/evaluation/sandboxes/live-repairs-a1-r1-critic/independent"
MANIFEST = ROOT / "sage/evaluation/sandboxes/live-evaluation/setup/frozen-pairs.json"
NAMES = (
    "native-run-id-bool.json",
    "native-start-bool.json",
    "native-finish-object.json",
    "native-execution-null.json",
)


def main() -> int:
    results = []
    for name in NAMES:
        command = [sys.executable, str(PAIRING), "validate-native", str(INPUTS / name), "--manifest", str(MANIFEST)]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        structured = completed.stderr.strip().startswith("{") and "Traceback" not in completed.stderr
        results.append({
            "label": name.removesuffix(".json"),
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "structured_rejection": completed.returncode == 2 and structured,
        })
    print(json.dumps({"classification": "exact_retained_fixed_replay", "results": results}, indent=2))
    return 0 if all(row["structured_rejection"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
