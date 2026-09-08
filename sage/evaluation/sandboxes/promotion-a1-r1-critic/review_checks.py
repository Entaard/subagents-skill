"""Independent public CLI review; every generated artifact stays beside this file."""
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAGE = ROOT.parents[2]
REPO = SAGE.parent
assert ROOT.name == "promotion-a1-r1-critic"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["SAGE_EVALUATION_SANDBOX"] = str(ROOT / "tests")
os.environ["TMPDIR"] = str(ROOT / "tmp")
(ROOT / "tmp").mkdir(exist_ok=True)
sys.path.insert(0, str(SAGE / "evaluation/tests"))
from support import complete_read_run, dump, record, write_log

results = []
assertions = []

def check(name, condition, detail=None):
    assertions.append({"name": name, "passed": bool(condition), "detail": detail})

def run(name, argv):
    process = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
    results.append({"name": name, "argv": argv, "exit_code": process.returncode,
                    "stdout": process.stdout, "stderr": process.stderr})
    return process

def cli(name, *args):
    return run(name, [sys.executable, str(SAGE / "scripts/sage_knowledge.py"), *map(str, args)])

def proposal(root, item=None, action="create"):
    source = root / "source-1"
    write_log(source, complete_read_run("source-1"))
    return dump(root / "proposal.json", {"action": action, "proposer": "/root/proposer", "reviewer": "reviewer", "source_runs": [str(source)], "record": item or record()})

def stage(root, item=None, action="create", generation="g-1", current="none"):
    path = proposal(root / generation, item, action)
    return cli(root.name + "-stage-" + generation, "stage", "--store-dir", root / "store", "--proposal", path, "--generation-id", generation, "--expected-current", current)

def activate(root, generation="g-1", current="none"):
    return cli(root.name + "-activate-" + generation, "activate", "--store-dir", root / "store", "--generation-id", generation, "--expected-current", current)

for name, folder, pattern in (("contracts", "evaluation/tests", "test_product_knowledge.py"), ("regressions", "tests", "test_knowledge.py"), ("state-contracts", "evaluation/tests", "test_product_state.py"), ("state-regressions", "tests", "test_state.py")):
    p = run(name, [sys.executable, "-m", "unittest", "discover", "-s", str(SAGE / folder), "-p", pattern, "-v"])
    (ROOT / (name + ".txt")).write_text(p.stdout + p.stderr)
    check(name, p.returncode == 0)

# Comparison and corroboration are the alternative reference-bearing transfer gates.
for kind in ("corroboration", "comparison"):
    case = ROOT / ("unresolved-" + kind)
    item = record(evidence_class="transferable_heuristic")
    item["gate_evidence"].pop("corroboration")
    item["gate_evidence"][kind] = ["source-1:missing-evidence"]
    p = stage(case, item)
    check("unresolved-" + kind + "-rejected", p.returncode == 2, p.stderr)
    if p.returncode == 0:
        p = activate(case)
        check("unresolved-" + kind + "-cannot-activate", p.returncode == 2, p.stdout)

# Explicit correction must not be a route around required intentional retirement metadata.
case = ROOT / "correct-to-retired"
check("retirement-control-stage", stage(case).returncode == 0)
check("retirement-control-activate", activate(case).returncode == 0)
item = record(revision=2, prior_revision=1, status="retired")
item["counterevidence"] = ["source-1:source-1-e-4"]
p = stage(case, item, "correct", "g-2", "g-1")
check("correct-to-retired-needs-retirement-basis", p.returncode == 2, p.stdout)

# A complete earlier generation must remain a usable rollback target if latest bytes corrupt.
case = ROOT / "corrupt-current-rollback"
check("rollback-control-stage", stage(case).returncode == 0)
check("rollback-control-activate", activate(case).returncode == 0)
check("rollback-second-stage", stage(case, record("k-2"), generation="g-2", current="g-1").returncode == 0)
check("rollback-second-activate", activate(case, "g-2", "g-1").returncode == 0)
target = case / "store/generations/g-2/records/k-2.json"
target.write_text(target.read_text().replace("Validate the authoritative", "Corrupt the authoritative"))
before = (case / "store/current.json").read_bytes()
p = cli("corrupt-current-rollback", "rollback", "--store-dir", case / "store", "--generation-id", "g-1", "--expected-current", "g-2")
check("valid-target-rollback-from-corrupt-current", p.returncode == 0, p.stderr)
check("rollback-failure-preserves-pointer", p.returncode == 0 or before == (case / "store/current.json").read_bytes())

# The literal documented proposal exercises the supported source path.
doc = (SAGE / "skills/sage-promote/references/knowledge.md").read_text()
blocks = re.findall(r"```json\n(.*?)\n```", doc, re.S)
case = ROOT / "documented-example"
item = json.loads(blocks[1]); source = case / "run-1"
write_log(source, complete_read_run("run-1")); item["source_runs"] = [str(source)]
path = dump(case / "proposal.json", item)
for name, args in (("validate-empty", ["validate", "--store-dir", case / "store"]), ("stage", ["stage", "--store-dir", case / "store", "--proposal", path, "--generation-id", "g-1", "--expected-current", "none"]), ("validate-staged", ["validate", "--store-dir", case / "store"]), ("activate", ["activate", "--store-dir", case / "store", "--generation-id", "g-1", "--expected-current", "none"]), ("retrieve", ["retrieve", "--store-dir", case / "store", "--cues", dump(case / "cues.json", json.loads(blocks[0])), "--limit", "3"])):
    p = cli("docs-" + name, *args)
    check("docs-" + name, p.returncode == 0, p.stderr)
    if name == "retrieve" and p.returncode == 0:
        check("docs-actionable-match", json.loads(p.stdout)["matches"][0]["rule"] == item["record"]["rule"])

status = json.loads((SAGE / "docs/STATUS.json").read_text())
check("frozen-pending-candidate", status["modules"]["promotion"]["pending_review"]["round"] == 1)
hashes = {}
submitted = next(row for row in reversed(status["history"]) if row.get("event") == "builder_candidate_submitted" and row.get("module") == "promotion")
for relative, expected in submitted["input_hashes"].items():
    hashes[relative] = hashlib.sha256((REPO / relative).read_bytes()).hexdigest()
    check("frozen:" + relative, hashes[relative] == expected)

dump(ROOT / "results.json", results)
dump(ROOT / "assertions.json", assertions)
dump(ROOT / "input-hashes.json", hashes)
print(json.dumps({"commands":len(results), "assertions":len(assertions), "failed":[a["name"] for a in assertions if not a["passed"]]}, indent=2))
