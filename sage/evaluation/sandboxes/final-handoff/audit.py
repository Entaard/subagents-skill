"""Final facts-only handoff audit, not another model evaluation."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SAGE = ROOT / "sage"
def read(path):
    return json.loads(path.read_text())
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

status = read(SAGE / "docs/STATUS.json")
assert all(row["gate"] == "passed" and not row["open_errors"] for row in status["modules"].values())
rounds = [row for module in status["modules"].values() for approach in module["approaches"] for row in approach["rounds"]]
assert len(rounds) == 18 and sum(row["verdict"] == "fail" for row in rounds) == 11
candidate = read(SAGE / "evaluation/sandboxes/final-a1-r2-builder/candidate-manifest.json")
facts_only = {"sage/ARCHITECTURE.md", "sage/docs/IMPLEMENTATION.md"}
unchanged = []
for item in candidate["source"]:
    if item["path"] not in facts_only:
        assert digest(ROOT / item["path"]) == item["sha256"], item["path"]
        unchanged.append(item["path"])
guards = read(SAGE / "evaluation/sandboxes/live-repairs-a1-r3-builder/candidate-manifest.json")["frozen_guards"]
for item in guards:
    assert digest(ROOT / item["path"]) == item["sha256"], item["path"]

links = []
for document in (SAGE / "docs/FINAL-REPORT.md", SAGE / "ARCHITECTURE.md", SAGE / "docs/IMPLEMENTATION.md"):
    for target in re.findall(r"\]\(([^)]+)\)", document.read_text()):
        if "://" in target or target.startswith("#"):
            continue
        target_path = document.parent / target.split("#", 1)[0]
        assert target_path.exists(), (str(document), target)
        links.append({"document": str(document.relative_to(ROOT)), "target": target})

archive = subprocess.run(["shasum", "-a", "256", "-c", "SHA256SUMS"],
                         cwd=SAGE / "archive/legacy", text=True, capture_output=True)
assert archive.returncode == 0, archive.stderr + archive.stdout
protected = subprocess.run(["git", "status", "--porcelain", "--", "sage-claude"],
                           cwd=ROOT, text=True, capture_output=True)
assert protected.returncode == 0 and protected.stdout == ""
diff = subprocess.run(["git", "diff", "--check", "--", "sage"], cwd=ROOT, text=True, capture_output=True)
assert diff.returncode == 0, diff.stdout + diff.stderr
result = {"ok": True, "module_gates_passed": 7, "critic_rounds": 18, "failed_rounds_retained": 11,
          "reviewed_source_unchanged_except_facts_only_docs": unchanged,
          "facts_only_documentation": sorted(facts_only), "frozen_guards": guards,
          "handoff_links": links, "archive_files_verified": archive.stdout.count(": OK"),
          "sage_claude_worktree_clean": True, "diff_check_passed": True,
          "native_live_trial": False, "cost_claim": None}
(OUT / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({key: value for key, value in result.items()
                  if key not in ("reviewed_source_unchanged_except_facts_only_docs", "frozen_guards", "handoff_links")}, indent=2))
