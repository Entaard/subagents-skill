#!/usr/bin/env python3
"""Run Sage's harness-only or complete offline verification gate."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
SANDBOXES = HERE / "sandboxes"


def contained(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("harness", "red"), required=True)
    parser.add_argument("--evidence-dir", type=Path)
    args = parser.parse_args()
    evidence = (args.evidence_dir or SANDBOXES / f"last-{args.mode}").resolve()
    if not contained(evidence, SANDBOXES):
        parser.error("--evidence-dir must be beneath sage/evaluation/sandboxes")
    evidence.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "SAGE_EVALUATION_SANDBOX": str(evidence / "work"),
        "TMPDIR": str(evidence / "tmp"),
    })
    for child in (Path(env["SAGE_EVALUATION_SANDBOX"]), Path(env["TMPDIR"])):
        child.mkdir(parents=True, exist_ok=True)
    commands = [[sys.executable, "-m", "unittest", "discover", "-s", str(HERE / "tests"), "-p", "test_harness.py" if args.mode == "harness" else "test_*.py", "-v"]]
    if args.mode == "red":
        commands.append([sys.executable, "-m", "unittest", "discover", "-s", str(HERE.parent / "tests"), "-p", "test_*.py", "-v"])
    completed = [subprocess.run(command, cwd=HERE.parents[1], env=env, text=True, capture_output=True, check=False) for command in commands]
    stdout = "\n".join(item.stdout for item in completed); stderr = "\n".join(item.stderr for item in completed)
    (evidence / "stdout.txt").write_text(stdout, encoding="utf-8")
    (evidence / "stderr.txt").write_text(stderr, encoding="utf-8")
    tests = sum(int(match.group(1)) for match in re.finditer(r"Ran (\d+) tests?", stderr))
    failures = sum(int(match.group(1)) for match in re.finditer(r"failures=(\d+)", stderr))
    errors = sum(int(match.group(1)) for match in re.finditer(r"errors=(\d+)", stderr))
    skipped = sum(int(match.group(1)) for match in re.finditer(r"skipped=(\d+)", stderr))
    exit_code = next((item.returncode for item in completed if item.returncode != 0), 0)
    report = {
        "schema_version": "sage-verification-run-v1", "mode": args.mode,
        "started_and_finished_at": datetime.now(timezone.utc).isoformat(),
        "command": commands[0], "commands": commands, "exit_code": exit_code,
        "passed": exit_code == 0,
        "tests": tests, "failures": failures, "errors": errors, "skipped": skipped,
        "live_trials_run": False, "network_used": False,
        "stdout": "stdout.txt", "stderr": "stderr.txt",
    }
    (evidence / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**report, "evidence_dir": str(evidence)}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
