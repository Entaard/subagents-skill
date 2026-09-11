"""Reproduce the single routing repair check and preserve generated output separately."""
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

arm = Path(__file__).resolve().parent.parent
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = str(arm / "tmp")
run = arm / "state/runs/catalog-export"
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
original = arm / "evidence/recovery-assessment.md"
corrected = arm / "evidence/recovery-assessment-corrected.md"
review = arm / "evidence/independent-review.md"
dispatch = json.loads((arm / "evidence/outer-coordinator-dispatch-observation.json").read_text())
assert sha(original) == "f5e7409048402fe24c6f8235c9de7b4ea970acd052280408c501e54144069a90"
assert sha(review) == "341118f9d55c021e0b69078de144f8108eef104c115c2614b3e7a6cb246844ba"
assert sha(arm / "evidence/resume-checks.json") == "d6fb9b3600bf3d8b7fcc39df833282b090f8623a5fbbcfe6ad4ab2e1e09f5e43"
assert sha(arm / "evidence/final-checks.json") == "4922aacb22abbf03015020db2b02bbbab2ce4379658be94d8214f7add06d2e00"
diff = list(difflib.ndiff(original.read_text().splitlines(), corrected.read_text().splitlines()))
changed = [line for line in diff if line.startswith(("- ", "+ "))]
assert len(changed) == 2 and all(line[2:].startswith("Known limits:") for line in changed)
assert dispatch["native_handle"] == "/root/live_recovery_treatment"
assert dispatch["spawn_result"]["task_name"] == dispatch["native_handle"]
assert dispatch["requested_model"] == "gpt-6-astra" and dispatch["requested_effort"] == "high"
assert dispatch["fork_turns"] == "none"
for key in ("effective_model", "effective_effort", "reported_tokens", "reported_money"):
    assert dispatch[key] is None
text = corrected.read_text()
for phrase in ("evidence/outer-coordinator-dispatch-observation.json",
               "`/root/live_recovery_treatment`", "requested model `gpt-6-astra`, effort `high`, and fork `none`",
               "not a raw native transcript or proof of effective identity",
               "effective model, effective effort, reported tokens and reported money are all null",
               "synthetic fixture writer's separate Astra/high request is not evidence"):
    assert phrase in text, phrase
initial = json.loads((arm / "evidence/resume-checks.json").read_text())
for relative, expected in initial["sha256"].items():
    assert sha(arm / relative) == expected, relative
log = (run / "events.jsonl").read_bytes()
assert log.startswith((arm / "evidence/original-events.jsonl").read_bytes())
snapshot = json.loads((run / "snapshot.json").read_text())
assert snapshot["events_sha256"] == hashlib.sha256(log).hexdigest()
assert snapshot["terminal"] is None
assert snapshot["next_action"].startswith("Pause export work")
assert snapshot["agents"]["/controlled/catalog-export-writer"]["effect_status"] == "unknown"
assert not any(json.loads(line)["type"] in ("task.result", "run.closed") for line in log.splitlines())
command = [sys.executable, str(arm / "installed/sage/bin/sage_state.py"), "validate", "--run-dir", str(run)]
result = subprocess.run(command, capture_output=True, text=True, env=os.environ)
assert result.returncode == 0, result.stderr
report = {"check": "routing-evidence-focused-repair", "outcome": "passed",
          "original_candidate_and_review_preserved": True, "old_check_outputs_preserved": True,
          "one_paragraph_changed": True, "dispatch_identity_matched": True,
          "effective_identity_and_usage_null": True, "original_log_prefix_preserved": True,
          "inputs_and_csv_bytes_preserved": True, "snapshot_bound": True, "source_run_terminal": False,
          "candidate_sha256": sha(corrected), "review_sha256": sha(review),
          "dispatch_sha256": sha(arm / "evidence/outer-coordinator-dispatch-observation.json"),
          "command": command, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
(arm / "evidence/repair-checks.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
