#!/usr/bin/env python3
"""Hash prior repair evidence and replay the original v2 rejection."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PRIOR = (
    ROOT / "sage/evaluation/sandboxes/live-repairs-a1-r1-builder",
    ROOT / "sage/evaluation/sandboxes/live-repairs-a1-r1-critic",
)
FROZEN = {
    "sage/evaluation/live-protocol.md": "8726a8fd00e48c074372609f90de562659012037a38461aefb91e1a958bf0c77",
    "sage/evaluation/rubric.json": "6abd4368dd443b8cd1cf10515638500bb849e59833764622348070382b2c8d16",
    "sage/evaluation/sandboxes/live-evaluation/setup/frozen-pairs.json": "50bd4d8693644aada5121ef6be5bfa6ce5c7e9ba53016cfbb9eb0e32b2e95a25",
    "sage/evaluation/sandboxes/live-evaluation/scoring-a1-r1/paired-results.json": "68efe28cbf510be2ff4cae31eb67df18d9c51c1fd89ebb2d96e217e62e307caf",
    "sage/docs/LIVE-RESULTS.md": "73bc34cd4ce190ebe43aafc7521536d3831768afee7322e6f248f7b01d73532b",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory() -> tuple[int, str]:
    rows = []
    for base in PRIOR:
        for path in sorted(base.rglob("*")):
            relative = str(path.relative_to(ROOT))
            if path.is_symlink():
                rows.append([relative, "symlink", os.readlink(path)])
            elif path.is_file():
                rows.append([relative, "file", sha256(path)])
    encoded = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode()
    return len(rows), hashlib.sha256(encoded).hexdigest()


def main() -> int:
    count, digest = inventory()
    guards = [{"path": path, "expected": expected, "actual": sha256(ROOT / path)}
              for path, expected in FROZEN.items()]
    command = [
        sys.executable,
        str(ROOT / "sage/evaluation/pairing.py"),
        "validate",
        str(ROOT / "sage/evaluation/sandboxes/live-evaluation/scoring-a1-r1/paired-results.json"),
        "--manifest",
        str(ROOT / "sage/evaluation/sandboxes/live-evaluation/setup/frozen-pairs.json"),
    ]
    checked = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    result = {
        "prior_evidence": {"entries": count, "inventory_sha256": digest},
        "frozen_guards": guards,
        "original_v2_replay": {
            "command": command,
            "exit_code": checked.returncode,
            "stdout": checked.stdout,
            "stderr": checked.stderr,
        },
    }
    print(json.dumps(result, indent=2))
    guards_match = all(row["actual"] == row["expected"] for row in guards)
    v2_preserved = checked.returncode == 2 and checked.stderr.startswith("{") and "lacks completed transcript evidence" in checked.stderr
    return 0 if guards_match and v2_preserved else 1


if __name__ == "__main__":
    raise SystemExit(main())
