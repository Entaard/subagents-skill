"""Coordinator's checks; the independent reviewer separately recomputes results."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ARM = Path(__file__).resolve().parents[1]
expected_hashes = {"sessions.csv": "9439d6888763978eb42988154a8278f517ae6afdd6aea3384b4f40d923b171ee",
                   "notes.txt": "a79f4ce37b627d54c78861f8fc8ebfedd56f69514de90bc9521d3425164b3c14"}
before = {name: hashlib.sha256((ARM / "inputs" / name).read_bytes()).hexdigest() for name in expected_hashes}
assert before == expected_hashes
script = ARM / "work/analysis.py"
first = subprocess.run([sys.executable, str(script), "--output", "-"], cwd=ARM / "tmp", capture_output=True, text=True, check=True).stdout
second = subprocess.run([sys.executable, str(script), "--output", "-"], cwd=ARM / "work", capture_output=True, text=True, check=True).stdout
assert first == second == (ARM / "work/summary.json").read_text()
s = json.loads(first)
assert s["source_sha256"] == expected_hashes
assert s["audit"]["all_visitors"] == 810
assert s["audit"]["missing_rows"][0]["completed"] is None
assert s["observed_rows"]["overall"]["new"]["denominator"] == 380
assert s["observed_rows"]["overall"]["old"]["denominator"] == 410
assert s["missing_count_sensitivity"]["feasible_counts"] == list(range(21))
for scenario in s["missing_count_sensitivity"]["scenarios"]:
    k = scenario["M09_completed"]
    c = scenario["comparisons"]
    assert c["overall"]["new"]["completed"] == 229 + k
    assert c["overall"]["new"]["denominator"] == 400
    assert c["overall"]["difference_new_minus_old_pp"] < 0
    assert c["crowd_busy"]["difference_new_minus_old_pp"] > 0
    assert c["crowd_quiet"]["difference_new_minus_old_pp"] > 0
    assert c["week_2"]["difference_new_minus_old_pp"] < 0
    assert c["week_2_busy"]["difference_new_minus_old_pp"] > 0
after = {name: hashlib.sha256((ARM / "inputs" / name).read_bytes()).hexdigest() for name in expected_hashes}
assert before == after
result = {"status": "passed", "checks": ["source hashes match initial baseline", "two fresh processes from different working directories produce byte-identical JSON", "saved JSON equals regenerated JSON", "M09 remains null in source audit", "all 21 M09 integer scenarios preserve reported directions"],
          "command": "PYTHONDONTWRITEBYTECODE=1 TMPDIR=<arm>/tmp python3 evidence/check_candidate.py", "source_sha256": after,
          "artifact_sha256": {name: hashlib.sha256((ARM / "work" / name).read_bytes()).hexdigest() for name in ("analysis.py", "summary.json", "decision-memo.md")},
          "requested_model": "gpt-6-astra", "requested_effort": "high", "effective_model": None, "effective_effort": None, "tokens": None, "money": None}
(ARM / "evidence/candidate-checks.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
