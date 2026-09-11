"""Final recovery integration checks; generated evidence is kept separate from old checks."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

arm = Path(__file__).resolve().parent.parent
run = arm / "state/runs/catalog-export"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = str(arm / "tmp")
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
expected = {
    "evidence/recovery-assessment.md": "f5e7409048402fe24c6f8235c9de7b4ea970acd052280408c501e54144069a90",
    "evidence/recovery-assessment-corrected.md": "3f9bb605067a18a042ec2bc78fef32aa573850d57bd189e1eefd88c8d0aff8cb",
    "evidence/independent-review.md": "341118f9d55c021e0b69078de144f8108eef104c115c2614b3e7a6cb246844ba",
    "evidence/independent-recheck.md": "a47dc229c3e0d8957da353c03d666dd1faa39475f76b78ac51648b89ce2a1f46",
    "evidence/outer-coordinator-dispatch-observation.json": "86dee3f79fbf54f7ab764cfe4daa3432f30c9c48fa090b6787c07a1092e6eca7",
    "evidence/resume-checks.json": "d6fb9b3600bf3d8b7fcc39df833282b090f8623a5fbbcfe6ad4ab2e1e09f5e43",
    "evidence/final-checks.json": "4922aacb22abbf03015020db2b02bbbab2ce4379658be94d8214f7add06d2e00",
}
expected.update(json.loads((arm / "evidence/resume-checks.json").read_text())["sha256"])
for relative, digest in expected.items():
    assert sha(arm / relative) == digest, relative
log = (run / "events.jsonl").read_bytes()
assert log.startswith((arm / "evidence/original-events.jsonl").read_bytes())
assert hashlib.sha256(b"".join(log.splitlines(keepends=True)[:20])).hexdigest() == "d78487fe428e5b667fbebe10dea4b555b560a735657dc1d8807b49e0507375d7"
snapshot = json.loads((run / "snapshot.json").read_text())
assert snapshot["events_sha256"] == hashlib.sha256(log).hexdigest()
assert snapshot["terminal"] is None and snapshot["last_seq"] == 28
assert snapshot["findings"]["routing-evidence"]["disposition"]["disposition"] == "fixed"
assert all(item["disposition"] is not None for item in snapshot["findings"].values())
assert snapshot["checks"]["routing-independent-recheck"]["outcome"] == "passed"
assert snapshot["checks"]["recovery-assessment-reviewed"]["outcome"] == "passed"
assert snapshot["next_action"].startswith("Pause export work")
assert snapshot["agents"]["/controlled/catalog-export-writer"]["effect_status"] == "unknown"
assert snapshot["tasks"]["observe"]["state"] == "admitted"
assert not any(json.loads(line)["type"] in ("task.result", "run.closed") for line in log.splitlines())
assert not any(json.loads(line)["type"] in ("task.admitted", "agent.requested") for line in log.splitlines()[8:])
for path in ("evidence/independent-review.md", "evidence/independent-recheck.md"):
    assert "RELEASE:" in (arm / path).read_text()
outputs = []
for command_name, args in (("validate", []), ("report", ["--write"])):
    command = [sys.executable, str(arm / "installed/sage/bin/sage_state.py"), command_name, "--run-dir", str(run), *args]
    result = subprocess.run(command, capture_output=True, text=True, env=os.environ)
    assert result.returncode == 0, result.stderr
    outputs.append({"command": command, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
artifact_paths = ["evidence/final-assessment.md", "evidence/review-lifecycle-observations.json",
                  "evidence/repair-checks.json", "state/runs/catalog-export/events.jsonl",
                  "state/runs/catalog-export/snapshot.json", "state/runs/catalog-export/report.md"]
report = {"outcome": "passed", "assessment_complete": True, "source_run_terminal": False,
          "source_effects": "unknown", "last_seq": snapshot["last_seq"],
          "original_8_event_prefix_preserved": True, "reviewed_20_event_prefix_preserved": True,
          "preserved_bytes_sha256": expected, "snapshot_binding_valid": True,
          "sole_finding_disposition": "fixed", "no_open_findings": True,
          "no_source_result_close_admission_or_retry_added": True,
          "explicit_reviewer_releases_present": True,
          "terminal_lifecycle_provenance": "Outer coordinator reported direct native observations; see review-lifecycle-observations.json",
          "helper_outputs": outputs,
          "final_artifact_sha256": {p: sha(arm / p) for p in artifact_paths}}
(arm / "evidence/final-integration-checks.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
