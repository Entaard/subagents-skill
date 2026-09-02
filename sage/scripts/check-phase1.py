#!/usr/bin/env python3
"""Run the standard-library Phase 1 implementation and behavior checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SAGE_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = SAGE_ROOT.parent


def main() -> int:
    commands = [
        [sys.executable, str(SAGE_ROOT / "scripts/check-phase0.py"), "--self-test"],
        [sys.executable, str(SAGE_ROOT / "scripts/generate-skill-bundle.py"), "--check"],
        [sys.executable, "-m", "unittest", "-v", "sage.tests.test_phase1"],
        [sys.executable, str(SAGE_ROOT / "evaluation/phase-1/pilot.py"), "verify-frozen"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=REPOSITORY_ROOT, check=False)
        if result.returncode != 0:
            return result.returncode
    print("phase1-check: implementation and frozen-gate checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
