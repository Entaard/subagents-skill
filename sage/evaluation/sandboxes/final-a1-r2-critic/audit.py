#!/usr/bin/env python3
"""Independent final repair audit; every output lives beside this file."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD = ROOT / "sage/evaluation/sandboxes/final-a1-r1-critic"
BUILDER = ROOT / "sage/evaluation/sandboxes/final-a1-r2-builder"

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")

def command(name, args, cwd=ROOT):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(HERE / "tmp"), SAGE_EVALUATION_SANDBOX=str(HERE / "work"), SAGE_R2_PHASE="critic")
    p = subprocess.run([str(a) for a in args], cwd=cwd, env=env, text=True, capture_output=True)
    out = dict(args=[str(a) for a in args], exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)
    save(name + ".json", out)
    return out

def graph(start, root):
    todo, seen, links = [start.resolve()], set(), []
    while todo:
        p = todo.pop()
        if p in seen:
            continue
        seen.add(p)
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", p.read_text()):
            if "://" in target:
                continue
            q = (p.parent / target.split("#")[0]).resolve()
            links.append(dict(source=str(p.relative_to(root)), target=target, exists=q.exists(), inside=q.is_relative_to(root)))
            if q.exists() and q.suffix == ".md":
                todo.append(q)
    return dict(reachable=sorted(str(p.relative_to(root)) for p in seen), links=links)

def main():
    for folder in ("tmp", "work"):
        (HERE / folder).mkdir(exist_ok=True)
    manifest_path = BUILDER / "candidate-manifest.json"
    assert sha(manifest_path) == "3f7f4c9e8ca6a8a76684ef2bbc34f7fd89dde29f5456c27b9ea6d47556a0fdde"
    manifest = json.loads(manifest_path.read_text())
    prior_manifest = json.loads((ROOT / "sage/evaluation/sandboxes/final-a1-r1-candidate/candidate-manifest.json").read_text())
    old_hashes = {r["path"]:r["sha256"] for r in prior_manifest["source"]}
    protected = {r["path"]:r["sha256"] for r in manifest["source"]}
    protected["sage/docs/STATUS.json"] = sha(ROOT / "sage/docs/STATUS.json")
    for folder in (OLD, BUILDER, ROOT / "sage/docs/reviews", ROOT / "sage/evaluation/sandboxes/live-evaluation/scoring-a1-r1"):
        for p in folder.rglob("*"):
            if p.is_file() and not p.is_symlink():
                protected[str(p.relative_to(ROOT))] = sha(p)
    save("protected-before.json", protected)
    assert all(sha(ROOT / r["path"]) == r["sha256"] for r in manifest["source"])
    retained = HERE / "candidate-source"
    old_copy = HERE / "old-source"
    for row in manifest["source"]:
        p = retained / row["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / row["path"], p)
    for row in prior_manifest["source"]:
        origin = OLD / "candidate-source" / row["path"]
        assert sha(origin) == row["sha256"]
        p = old_copy / row["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, p)
    for p in (ROOT / "sage/evaluation").rglob("*"):
        rel = p.relative_to(ROOT / "sage/evaluation")
        if not p.is_file() or "sandboxes" in rel.parts or "__pycache__" in rel.parts:
            continue
        dest = retained / "sage/evaluation" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(p, dest)
    shutil.copy2(ROOT / "sage/docs/STATUS.json", HERE / "status-before.json")
    full = command("offline-command", [sys.executable, retained / "sage/evaluation/run_verification.py", "--mode", "red", "--evidence-dir", retained / "sage/evaluation/sandboxes/critic-offline"])
    focused = {}
    for name, copy_root in (("old", old_copy), ("current", retained)):
        script = copy_root / "sage/evaluation/sandboxes/coordination/test_promotion_coordination.py"
        script.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BUILDER / "test_promotion_coordination.py", script)
        assert sha(script) == sha(BUILDER / "test_promotion_coordination.py")
        result = command("focused-" + name, [sys.executable, script])
        focused[name] = json.loads((script.parent / "critic/summary.json").read_text())
        assert result["exit_code"] == (1 if name == "old" else 0), result
    installed = retained / "sage/evaluation/sandboxes/coordination/critic/installed"
    old_installed = old_copy / "sage/evaluation/sandboxes/coordination/critic/installed"
    instruction = {}
    for name, root in (("old", old_installed), ("current", installed)):
        instruction[name] = {skill:graph(root / "skills" / skill / "SKILL.md", root) for skill in ("sage", "sage-promote")}
    save("instruction-graphs.json", instruction)
    all_links = []
    for p in installed.rglob("*.md"):
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", p.read_text()):
            if "://" not in target:
                q = (p.parent / target.split("#")[0]).resolve()
                all_links.append(dict(source=str(p.relative_to(installed)), target=target, exists=q.exists(), inside=q.is_relative_to(installed)))
    installed_matches = []
    for p in installed.rglob("*"):
        if not p.is_file() or p.name == "receipt.json":
            continue
        rel = p.relative_to(installed)
        source = retained / "sage" / rel if rel.parts[0] == "skills" else retained / "sage/scripts" / p.name
        installed_matches.append(dict(path=str(rel), sha256=sha(p), source_match=sha(p)==sha(source)))
    save("installed-audit.json", dict(files_including_receipt=len(installed_matches)+1, matches=installed_matches, links=all_links))
    assert all(r["exists"] and r["inside"] for r in all_links)
    assert all(r["source_match"] for r in installed_matches)
    historical = json.loads((OLD / "historical-score-evidence.json").read_text())
    mismatches = [r["path"] for r in historical["bindings"] if sha(Path(r["path"])) != r["expected"]]
    save("historical-binding-check.json", dict(scorecards=len(historical["scorecards"]), bindings=len(historical["bindings"]), mismatches=mismatches, rescored=False))
    changed = [p for p,h in protected.items() if sha(ROOT / p) != h]
    save("preservation.json", dict(protected_files=len(protected), changed=changed))
    summary = dict(manifest_sha256=sha(manifest_path), source_count=len(manifest["source"]), changed_source=[r["path"] for r in manifest["source"] if r["sha256"] != old_hashes[r["path"]]], offline=json.loads((retained / "sage/evaluation/sandboxes/critic-offline/report.json").read_text()), focused={k:{field:v[field] for field in ("tests", "failures", "errors", "passed")} for k,v in focused.items()}, installed_links=len(all_links), historical_bindings=len(historical["bindings"]), historical_mismatches=mismatches, protected_files=len(protected), protected_changed=changed)
    save("summary.json", summary)
    print(json.dumps(summary))
    assert full["exit_code"] == 0
    assert not changed and not mismatches

if __name__ == "__main__":
    main()
