#!/usr/bin/env python3
"""Bounded independent replay of integration round-1 errors on round-2 bytes."""
import hashlib
import json
import os
from pathlib import Path
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

def tree(path):
    return {str(p.relative_to(path)): ("symlink:" + os.readlink(p) if p.is_symlink() else sha(p)) for p in path.rglob("*") if p.is_file() or p.is_symlink()}

def call(name, args, cwd=REPO, env=None):
    result = subprocess.run([str(x) for x in args], cwd=cwd, env=env or os.environ, text=True, capture_output=True)
    ROWS.append({"name": name, "argv": [str(x) for x in args], "cwd": str(cwd), "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
    dump(HERE / "commands.json", ROWS)
    return result

def main():
    for name in ("tmp", "work"):
        (HERE / name).mkdir()
    os.environ.update(PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(HERE / "tmp"), SAGE_EVALUATION_SANDBOX=str(HERE / "work"))
    status = json.loads((SAGE / "docs/STATUS.json").read_text())
    dump(HERE / "status-before.json", status)
    frozen = status["history"][-1]["input_hashes"]
    assert all(sha(REPO / path) == value for path,value in frozen.items())
    dump(HERE / "input-hashes.json", frozen)
    prior_file = SAGE / "evaluation/sandboxes/integration-wave-r2-final/prior-evidence-hashes.txt"
    prior = {}
    for line in prior_file.read_text().splitlines():
        value, path = line.split("  ", 1)
        assert sha(REPO / path) == value, path
        prior[path] = value
    dump(HERE / "prior-evidence-before.json", prior)
    sys.path.insert(0, str(SAGE / "evaluation/tests"))
    import test_product_install
    # Exact copied source and test bytes bind the old sentinel path to this fresh sandbox.
    copied = HERE / "sentinel-source/sage"
    test_product_install.copy_source(copied)
    testdir = copied / "evaluation/tests"; testdir.mkdir(parents=True)
    for name in ("support.py", "test_product_install.py"):
        shutil.copy2(SAGE / "evaluation/tests" / name, testdir / name)
    old_target = copied / "evaluation/sandboxes/integration-wave-r1-overlap-positive/target"
    old_target.mkdir(parents=True)
    sentinel = old_target / "prior-evidence.txt"; sentinel.write_bytes(b"round-2 critic prior-evidence sentinel")
    sentinel_hash = sha(sentinel)
    sentinel_results = []
    for name in ("caller-1", "caller-2"):
        caller = copied / "evaluation/sandboxes" / name; caller.mkdir()
        env = dict(os.environ, SAGE_EVALUATION_SANDBOX=str(caller), TMPDIR=str(HERE / "tmp"))
        result = call(name, [sys.executable, "-B", "-m", "unittest", "test_product_install.InstallContractTests.test_default_source_allows_required_evaluation_sandbox_target", "-v"], cwd=testdir, env=env)
        assert result.returncode == 0 and sha(sentinel) == sentinel_hash
        sentinel_results.append({"caller": str(caller), "passed": True, "sentinel_unchanged": True})
    dump(HERE / "e1-replay.json", {"source_test_sha256": sha(SAGE / "evaluation/tests/test_product_install.py"), "copied_test_sha256": sha(testdir / "test_product_install.py"), "sentinel_sha256": sentinel_hash, "runs": sentinel_results})
    parents = []
    for name in ("references", "agents"):
        target = HERE / ("parent-" + name)
        result = call("install-parent-control", ["bash", SAGE / "install.sh", "--target-root", target]); assert result.returncode == 0
        receipt = json.loads((target / "sage/receipt.json").read_text()); assert len(receipt["installed_files"]) == 14
        parent = target / "skills/sage" / name
        saved = HERE / ("saved-" + name); parent.rename(saved); parent.write_bytes(b"user-owned parent replacement")
        (target / "unrelated.txt").write_bytes(b"user-owned unrelated file")
        before = tree(target); saved_before = tree(saved)
        result = call("uninstall-parent-conflict", ["bash", SAGE / "uninstall.sh", "--target-root", target])
        assert result.returncode == 2 and not result.stdout
        assert json.loads(result.stderr)["ok"] is False and "parent must be a directory" in result.stderr
        assert tree(target) == before and tree(saved) == saved_before
        parents.append({"parent": name, "exit_code": result.returncode, "target_bytes_unchanged": True, "saved_bytes_unchanged": True, "receipt_unchanged": True, "removed_files": []})
        # Remove only this probe's replacement, restore its saved parent, and verify normal uninstall.
        parent.unlink(); saved.rename(parent)
        result = call("uninstall-restored-positive", ["bash", SAGE / "uninstall.sh", "--target-root", target]); assert result.returncode == 0
        assert len(json.loads(result.stdout)["removed"]) == 14 and (target / "unrelated.txt").read_bytes() == b"user-owned unrelated file"
    dump(HERE / "e2-replay.json", {"cases": parents, "restored_positive_uninstalls": 2})
    # The reviewed test now allocates through support.sandbox; normal full-source run is safe.
    suite = call("full-offline-original-source", [sys.executable, SAGE / "evaluation/run_verification.py", "--mode", "red", "--evidence-dir", HERE / "full-suite"])
    assert suite.returncode == 0
    report = json.loads(suite.stdout)
    assert report["tests"] == 79 and report["failures"] == report["errors"] == report["skipped"] == 0
    preserved = {path: sha(REPO / path) == value for path,value in prior.items()}
    assert all(preserved.values())
    assert all(sha(REPO / path) == value for path,value in frozen.items())
    archive = SAGE / "archive/legacy"
    archive_checks = {}
    for line in (archive / "SHA256SUMS").read_text().splitlines():
        value,path = line.split("  ", 1)
        archive_checks[path] = sha(archive / path) == value
    assert len(archive_checks) == 186 and all(archive_checks.values())
    dump(HERE / "retention-and-hashes.json", {"prior_evidence_count": len(prior), "prior_evidence_matches": preserved, "candidate_hashes_unchanged": True, "archive_hash_matches": archive_checks})
    dump(HERE / "summary.json", {"passed": True, "full_suite": report, "e1_two_fresh_caller_sandboxes": True, "e2_early_late_parent_preservation": True, "positive_restored_uninstalls": 2, "prior_evidence_files_unchanged": len(prior), "archive_hashes_verified": 186, "candidate_hashes_verified": len(frozen), "live_trials_run": False})
    print(json.dumps({"tests":79,"failures":0,"errors":0,"skipped":0,"E1":"verified_fixed","E2":"verified_fixed","prior_files_unchanged":len(prior)},indent=2))

if __name__ == "__main__":
    main()
