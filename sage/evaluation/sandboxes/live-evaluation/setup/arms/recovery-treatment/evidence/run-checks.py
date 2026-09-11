"""Scoped recovery evidence generation; no export or original-input writes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ARM = Path(__file__).resolve().parent.parent
RUN = ARM / "state/runs/catalog-export"
HELPER = ARM / "installed/sage/bin/sage_state.py"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = str(ARM / "tmp")


def helper(name, *args):
    command = [sys.executable, str(HELPER), name, "--run-dir", str(RUN), *args]
    result = subprocess.run(command, capture_output=True, text=True, env=os.environ)
    output = {"command": command, "exit_code": result.returncode,
              "stdout": result.stdout, "stderr": result.stderr}
    print(json.dumps(output))
    if result.returncode:
        raise RuntimeError(output)
    return output


def hashes():
    paths = ["inputs/baseline.json", "inputs/fixture-notes.txt", "inputs/observer.json",
             "work/export.csv", "work/export.draft.csv", "evidence/original-events.jsonl",
             "evidence/original-stale-snapshot.json"]
    return {p: hashlib.sha256((ARM / p).read_bytes()).hexdigest() for p in paths}


phase = sys.argv[1]
if phase == "resume":
    results = [helper("validate"),
               helper("resume", "--agents", str(ARM / "inputs/observer.json")),
               helper("resume", "--agents", str(ARM / "evidence/native-agents.json"))]
    report = {"phase": phase, "helper_results": results, "sha256": hashes()}
    (ARM / "evidence/resume-checks.json").write_text(json.dumps(report, indent=2) + "\n")
elif phase == "verify":
    initial = json.loads((ARM / "evidence/resume-checks.json").read_text())
    current = hashes()
    original = (ARM / "evidence/original-events.jsonl").read_bytes()
    log = (RUN / "events.jsonl").read_bytes()
    assert log.startswith(original), "Authoritative prefix changed"
    assert current == initial["sha256"], "Preserved source/artifact bytes changed"
    baseline = json.loads((ARM / "inputs/baseline.json").read_text())
    assert current[baseline["path"]] == baseline["sha256"], "Export baseline differs"
    snapshot = json.loads((RUN / "snapshot.json").read_text())
    assert snapshot["terminal"] is None, "Source run was closed"
    assert snapshot["events_sha256"] == hashlib.sha256(log).hexdigest(), "Snapshot binding stale"
    assert snapshot["next_action"].startswith("Pause export work"), "Unsafe next action"
    assert snapshot["agents"]["/controlled/catalog-export-writer"]["effect_status"] == "unknown"
    assert not any(json.loads(line)["type"] == "run.closed" for line in log.splitlines())
    results = [helper("validate"), helper("report", "--write")]
    report = {"phase": phase, "original_prefix_preserved": True,
              "preserved_sha256": current, "source_run_terminal": False,
              "export_baseline_matches": True, "helper_results": results}
    (ARM / "evidence/final-checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))
else:
    raise SystemExit("Use resume or verify")
