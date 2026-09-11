#!/usr/bin/env python3
"""Critic-owned evidence runner; historical replays are informed diagnostics."""
import copy
import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAGE = HERE.parents[2]
ROOT = SAGE.parent
os.environ.update(PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(HERE / "tmp"), SAGE_EVALUATION_SANDBOX=str(HERE / "work"))
for child in (HERE / "tmp", HERE / "work"):
    child.mkdir(exist_ok=True)

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")

def call(args):
    p = subprocess.run([str(x) for x in args], cwd=ROOT, text=True, capture_output=True)
    return dict(command=[str(x) for x in args], exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inventory():
    # Never inspect browser profile contents, including hashing them.
    paths = []
    for base in [SAGE / "archive", SAGE / "skills", SAGE / "scripts", SAGE / "tests",
                 SAGE / "evaluation/sandboxes/live-evaluation", SAGE / "evaluation/sandboxes/live-repairs-a1-r1-builder"]:
        for current, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if not any(w in d.lower() for w in ("profile", "cache", "browser-attempt"))]
            paths.extend(Path(current) / f for f in files if not any(w in f.lower() for w in ("cookie", "session")))
    manifest = json.loads((SAGE / "evaluation/sandboxes/live-repairs-a1-r1-builder/candidate-manifest.json").read_text())
    for row in manifest["source"] + manifest["protected_source_guards"]:
        path = ROOT / row["path"]
        assert digest(path) == row["sha256"], path
        paths.append(path)
    paths += [SAGE / "docs/STATUS.json", SAGE / "evaluation/sandboxes/live-repairs-a1-r1-builder/candidate-manifest.json"]
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(set(paths)) if p.is_file()}

def history():
    source = SAGE / "evaluation/sandboxes/live-repairs-a1-r1-builder/run_informed_diagnostics.py"
    context = runpy.run_path(str(source), run_name="critic_inspected_replay")
    out = HERE / "historical-replay"
    out.mkdir()
    # Inspected helper functions use only OUT for writes; never call its old inventory/main.
    for key in ("replay_creative", "replay_reports", "replay_native_result"):
        context[key].__globals__["OUT"] = out
    result = {"classification": "informed_diagnostic_only", "reuse": "Inspected builder replay mechanics; independent boundary checks recorded separately.",
              "creative": context["replay_creative"](), "reports": context["replay_reports"](),
              "native": context["replay_native_result"]()}
    save(out / "summary.json", result)
    return {"historical_replay": "passed", "reports": len(result["reports"]["reports"])}

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "before":
        before = inventory(); save(HERE / "protected-before.json", before); print(json.dumps({"protected_files": len(before)}))
    elif mode == "after":
        after = inventory(); save(HERE / "protected-after.json", after)
        before = json.loads((HERE / "protected-before.json").read_text())
        result = {"unchanged": before == after, "protected_files": len(after), "changed": [k for k in before if before[k] != after.get(k)]}
        save(HERE / "preservation.json", result); print(json.dumps(result)); assert result["unchanged"]
    elif mode == "history":
        print(json.dumps(history()))
    elif mode == "offline":
        result = call([sys.executable, SAGE / "evaluation/run_verification.py", "--mode", "red", "--evidence-dir", HERE / "offline"])
        save(HERE / "offline-command.json", result); print(result["stdout"]); assert result["exit_code"] == 0, result
