"""Generate bounded informed replays and a hash-bound builder candidate."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text())

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n")

def binding(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

prior = read(ROOT / "sage/evaluation/sandboxes/live-repairs-a1-r2-builder/candidate-manifest.json")
preserved = prior["frozen_guards"] + prior["preserved_round_1_repair_source"]
for item in preserved:
    assert binding(ROOT / item["path"]) == item, item
write("preservation.json", {"checked": preserved, "unchanged": True})

failures = read(ROOT / "sage/evaluation/sandboxes/live-repairs-a1-r2-critic/retained-failures.json")
results = []
for old in failures:
    command = [sys.executable, str(ROOT / "sage/evaluation/pairing.py"), *old["command"][2:]]
    process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    results.append({"label": old["label"], "command": command, "prior_exit": old["exit_code"],
                    "exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr})
write("retained-green.json", results)
assert all(row["exit_code"] == 2 and json.loads(row["stderr"])["ok"] is False for row in results)

sources = [ROOT / row["path"] for row in prior["source"]]
sources.append(ROOT / "sage/evaluation/tests/test_native_shape.py")
manifest = {"approach": "live-repairs-a1", "round": 3, "builder": "/root",
            "routing_fallback": "Agent-thread limit prevented prior/fresh Sol builder; retained Astra critic is separate.",
            "source": [binding(path) for path in sources],
            "preserved_round_1_repair_source": prior["preserved_round_1_repair_source"],
            "frozen_guards": prior["frozen_guards"],
            "verification": {"red": "red/stderr.txt", "green": "green/stderr.txt",
                             "full": read(OUT / "full/report.json"), "retained_failures_rejected": len(results)},
            "critic_findings_self_closed": False, "historical_scores_changed": False,
            "limitations": ["Structural/informed checks, not new live trials or evidence authentication.",
                            "Timestamp syntax/order is outside this validator.",
                            "No new home installation or effective-model/usage telemetry."]}
write("candidate-manifest.json", manifest)
print(json.dumps({"candidate": binding(OUT / "candidate-manifest.json"), "retained_rejected": len(results),
                  "offline": manifest["verification"]["full"]}, indent=2))
