#!/usr/bin/env python3
"""Independent integration probes. All generated files stay beside this script."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SAGE = HERE.parents[2]
REPO = SAGE.parent
ROWS = []

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def call(name, args, cwd=REPO):
    p = subprocess.run([str(x) for x in args], cwd=cwd, env=os.environ, text=True, capture_output=True)
    row = {"name": name, "argv": [str(x) for x in args], "cwd": str(cwd), "exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    ROWS.append(row)
    dump(HERE / "commands.json", ROWS)
    return p

def install(target, source=None):
    args = ["bash", SAGE / "install.sh", "--target-root", target]
    if source is not None:
        args += ["--source-root", source]
    return call("install", args)

def uninstall(target):
    return call("uninstall", ["bash", SAGE / "uninstall.sh", "--target-root", target])

def copy_source(target):
    shutil.copytree(SAGE / "skills", target / "skills")
    (target / "scripts").mkdir()
    for file in ("sage_state.py", "sage_knowledge.py"):
        shutil.copy2(SAGE / "scripts" / file, target / "scripts" / file)

def snapshot(target):
    return {str(p.relative_to(target)): ("link:" + os.readlink(p) if p.is_symlink() else sha(p)) for p in target.rglob("*") if p.is_file() or p.is_symlink()}

def main():
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(HERE / "tmp"), SAGE_EVALUATION_SANDBOX=str(HERE / "work"))
    (HERE / "tmp").mkdir(); (HERE / "work").mkdir()
    frozen = {}
    for base in (SAGE / "scripts", SAGE / "skills", SAGE / "tests", SAGE / "evaluation/tests"):
        frozen.update({str(p.relative_to(SAGE)): sha(p) for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts})
    for raw in ("install.sh", "uninstall.sh", "README.md", "ARCHITECTURE.md", "docs/CONTRACTS.md", "docs/REQUIREMENTS.md", "docs/DECISIONS.md", "docs/IMPLEMENTATION.md", "docs/STATUS.json", "evaluation/run_verification.py", "evaluation/rubric.json", "evaluation/requirements-trace.json", "archive/legacy/SHA256SUMS"):
        frozen[raw] = sha(SAGE / raw)
    dump(HERE / "input-hashes.json", frozen)
    shutil.copy2(SAGE / "docs/STATUS.json", HERE / "status-before.json")
    # Exact source copy relocates the one destructive hard-coded test into new evidence.
    replica = HERE / "replica/sage"
    for folder in ("scripts", "skills", "tests", "docs"):
        shutil.copytree(SAGE / folder, replica / folder, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(SAGE / "evaluation", replica / "evaluation", ignore=shutil.ignore_patterns("sandboxes", "__pycache__", "results"))
    for file in ("install.sh", "uninstall.sh", "README.md", "ARCHITECTURE.md"):
        shutil.copy2(SAGE / file, replica / file)
    same = {k: sha(replica / k) == v for k,v in frozen.items() if (replica / k).is_file()}
    assert all(same.values())
    dump(HERE / "replica-byte-equivalence.json", same)
    # Sentinel is created by this probe solely to demonstrate a prior-result deletion.
    hardcoded = replica / "evaluation/sandboxes/integration-wave-r1-overlap-positive/target"
    hardcoded.mkdir(parents=True)
    sentinel = hardcoded / "prior-evidence.txt"
    sentinel.write_text("independent immutable earlier observation\n")
    before = sha(sentinel)
    result = call("full-offline-exact-source-copy", [sys.executable, replica / "evaluation/run_verification.py", "--mode", "red", "--evidence-dir", replica / "evaluation/sandboxes/fresh-critic-suite"])
    report = json.loads(result.stdout)
    dump(HERE / "full-suite.json", report)
    dump(HERE / "runner-isolation.json", {"code_bytes_unchanged": all(same.values()), "requested_evidence_dir": str(replica / "evaluation/sandboxes/fresh-critic-suite"), "earlier_evidence_path": str(sentinel), "earlier_evidence_sha256": before, "earlier_evidence_survived": sentinel.exists(), "suite_passed": report["passed"]})
    assert result.returncode == 0 and report["tests"] == 77
    results = {}
    target = HERE / "nested-positive-target"
    assert install(target).returncode == 0
    receipt = json.loads((target / "sage/receipt.json").read_text())
    results["default_source_nested_target"] = True
    results["installed_14_files"] = len(receipt["installed_files"]) == 14
    assert results["installed_14_files"]
    # Source-independent executable use from a separate CWD with source paths absent from sys.path.
    for file in ("sage_state.py", "sage_knowledge.py"):
        assert call("installed-help", [sys.executable, "-I", target / "sage/bin" / file, "--help"], cwd=HERE).returncode == 0
    links = []
    for p in (target / "skills").rglob("*.md"):
        for link in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", p.read_text()):
            if "://" not in link:
                links.append({"document": str(p.relative_to(target)), "link": link, "exists": (p.parent / link).is_file()})
    assert all(x["exists"] for x in links)
    dump(HERE / "installed-links.json", links)
    # Local edits and unowned data survive both conflict preflight and conservative uninstall.
    (target / "skills/sage/SKILL.md").write_text("local owned edit")
    (target / "skills/sage/private.txt").write_text("private-marker-never-report")
    (target / "untouched-empty").mkdir()
    (target / "runtime/runs").mkdir(parents=True)
    (target / "runtime/runs/fact").write_text("runtime-state")
    old = snapshot(target)
    bad = install(target)
    assert bad.returncode == 2 and snapshot(target) == old
    gone = uninstall(target); data = json.loads(gone.stdout)
    assert gone.returncode == 0 and "private-marker-never-report" not in gone.stdout
    assert {x["path"] for x in data["retained"]} == {"skills/sage/SKILL.md", "skills/sage/private.txt"}
    assert (target / "untouched-empty").is_dir() and (target / "runtime/runs/fact").read_text() == "runtime-state"
    results["modified_unowned_runtime_and_directories_preserved"] = True
    # Empty receipt does not authorize traversal through its own parent symlink.
    escape = HERE / "escape"; escape.mkdir()
    linktarget = HERE / "receipt-link"; linktarget.mkdir()
    (linktarget / "sage").symlink_to(escape, target_is_directory=True)
    empty = {**receipt, "target_root": str(linktarget), "installed_files": [], "files": {}}
    dump(escape / "receipt.json", empty)
    old = snapshot(escape)
    assert uninstall(linktarget).returncode == 2 and snapshot(escape) == old
    assert install(linktarget).returncode == 2 and snapshot(escape) == old
    results["empty_receipt_parent_symlink_rejected"] = True
    malformed = HERE / "malformed"; (malformed / "sage").mkdir(parents=True)
    for index, value in enumerate(([{}], [None], [42], "x", {}, ["../x"], ["skills/sage/x", "skills/sage/x"])):
        dump(malformed / "sage/receipt.json", {**empty, "target_root": str(malformed), "installed_files": value})
        old = snapshot(malformed)
        bad = uninstall(malformed)
        assert bad.returncode == 2 and "Traceback" not in bad.stderr and json.loads(bad.stderr)["ok"] is False and snapshot(malformed) == old
    results["malformed_receipts_rejected_without_mutation"] = 7
    # Completeness, legacy-manifest refusal, and source overlap are independently rechecked.
    source = HERE / "alternate-source"; copy_source(source)
    missing = source / "skills/sage/references/recovery.md"; missing.rename(missing.with_suffix(".held"))
    destination = HERE / "incomplete-target"
    assert install(destination, source).returncode == 2 and not destination.exists()
    missing.with_suffix(".held").rename(missing)
    dump(source / "skills/sage/source-manifest.json", {})
    assert install(destination, source).returncode == 2 and not destination.exists()
    (source / "skills/sage/source-manifest.json").unlink()
    assert install(source / "skills/nested", source).returncode == 2
    assert not (source / "skills/nested").exists()
    results["incomplete_manifest_overlap_rejections"] = True
    # Retired owned files are removed only on a matching receipt hash.
    extra = source / "skills/sage/references/extra.md"; extra.write_text("owned prior extension")
    update_target = HERE / "update-target"
    assert install(update_target, source).returncode == 0
    extra.unlink()
    assert install(update_target, source).returncode == 0
    assert not (update_target / "skills/sage/references/extra.md").exists()
    updated = json.loads((update_target / "sage/receipt.json").read_text())
    assert all(x["inherited_installed_sha256"] for x in updated["files"].values())
    results["retired_owned_removal_and_inherited_hashes"] = True
    # Replaced directory type: observe whether rejection really precedes all effects.
    replaced = HERE / "replaced-parent"
    assert install(replaced).returncode == 0
    parent = replaced / "skills/sage/references"
    parent.rename(replaced / "saved-original-references")
    parent.write_text("user-replacement")
    old = snapshot(replaced)
    partial = uninstall(replaced)
    now = snapshot(replaced)
    dump(HERE / "replaced-parent.json", {"exit_code": partial.returncode, "stdout": partial.stdout, "stderr": partial.stderr, "removed_before_rejection": sorted(set(old)-set(now)), "replacement_preserved": parent.read_text() == "user-replacement", "receipt_preserved": (replaced / "sage/receipt.json").is_file()})
    dump(HERE / "positive-negative-probes.json", results)
    # Archive inventory independently joins exact baseline Git bytes to every archived path.
    archive = SAGE / "archive/legacy"
    baseline = "c816a6250d0df74e6cbfa9b2a672a2fc15110deb"
    inventory = []
    for line in (archive / "SHA256SUMS").read_text().splitlines():
        expected, raw = line.split("  ", 1); relative = raw.removeprefix("./")
        git = subprocess.run(["git", "show", f"{baseline}:sage/{relative}"], cwd=REPO, capture_output=True, check=True)
        actual = sha(archive / relative)
        inventory.append({"path": relative, "inventory_match": actual == expected, "git_match": actual == hashlib.sha256(git.stdout).hexdigest(), "absent_active": not (SAGE / relative).exists()})
    baseline_paths = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", baseline, "--", "sage"], cwd=REPO, text=True).splitlines()
    residual = sorted(set(p.removeprefix("sage/") for p in baseline_paths) - {x["path"] for x in inventory})
    physical = {str(p.relative_to(archive)) for p in archive.rglob("*") if p.is_file()} - {"SHA256SUMS"}
    expected_paths = {x["path"] for x in inventory}
    dump(HERE / "archive-audit.json", {"baseline": baseline, "baseline_count": len(baseline_paths), "archive_count": len(inventory), "residual_active_entrypoints": residual, "exact_physical_inventory": physical == expected_paths, "entries": inventory})
    assert len(inventory) == 186 and len(baseline_paths) == 194 and len(residual) == 8
    assert physical == expected_paths and all(x["inventory_match"] and x["git_match"] and x["absent_active"] for x in inventory)
    syntax = []
    for base in (SAGE / "scripts", SAGE / "skills"):
        for p in base.rglob("*.py"):
            ast.parse(p.read_text()); syntax.append(str(p.relative_to(SAGE)))
    dump(HERE / "static.json", {"python_syntax": syntax, "active_skill_file_count": sum(p.is_file() for p in (SAGE / "skills").rglob("*")), "skill_metadata": {str(p.relative_to(SAGE)): p.read_text() for p in (SAGE / "skills").rglob("openai.yaml")}})
    assert all(sha(SAGE / k) == v for k,v in frozen.items())
    print(json.dumps({"full_suite": report, "independent_probes": results, "archive_files": len(inventory), "candidate_unchanged": True}, indent=2))

if __name__ == "__main__":
    main()
