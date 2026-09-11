#!/usr/bin/env python3
"""Final critic's isolated assembled-package evidence; no source repair."""
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
MANIFEST = ROOT / "sage/evaluation/sandboxes/final-a1-r1-candidate/candidate-manifest.json"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")

def command(label, args, cwd=ROOT):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(HERE / "tmp"), SAGE_EVALUATION_SANDBOX=str(HERE / "work"))
    result = subprocess.run([str(a) for a in args], cwd=cwd, env=env, text=True, capture_output=True)
    row = dict(label=label, args=[str(a) for a in args], exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr)
    save(label + ".json", row)
    return row

def main():
    for child in ("tmp", "work"):
        (HERE / child).mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    assert digest(MANIFEST) == "c0767e686daa9ed9edc885b6335e441e143af9a526f8a9df9fbee49c4324f692"
    assert all(digest(ROOT / row["path"]) == row["sha256"] for row in manifest["source"])
    protected = {row["path"]: row["sha256"] for row in manifest["source"]}
    for folder in ("sage/docs/reviews", "sage/evaluation/sandboxes/live-evaluation/scoring-a1-r1"):
        for p in (ROOT / folder).rglob("*"):
            if p.is_file() and not p.is_symlink():
                protected[str(p.relative_to(ROOT))] = digest(p)
    protected["sage/docs/STATUS.json"] = digest(ROOT / "sage/docs/STATUS.json")
    save("protected-before.json", protected)
    replica = HERE / "candidate-source"
    for row in manifest["source"]:
        target = replica / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / row["path"], target)
    # Maintained harness inputs are copied without disposable historical sandboxes.
    for p in (ROOT / "sage/evaluation").rglob("*"):
        rel = p.relative_to(ROOT / "sage/evaluation")
        if "sandboxes" in rel.parts or "__pycache__" in rel.parts or not p.is_file():
            continue
        target = replica / "sage/evaluation" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(p, target)
    shutil.copy2(ROOT / "sage/docs/STATUS.json", HERE / "status-before.json")
    suite = command("offline-command", [sys.executable, replica / "sage/evaluation/run_verification.py", "--mode", "red", "--evidence-dir", replica / "sage/evaluation/sandboxes/offline"])
    install = command("install", ["bash", replica / "sage/install.sh", "--target-root", HERE / "installed"])
    assert install["exit_code"] == 0, install
    installed = HERE / "installed"
    files = [p for p in installed.rglob("*") if p.is_file()]
    markdown = [p for p in files if p.suffix == ".md"]
    links = []
    for p in markdown:
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", p.read_text()):
            if "://" not in target:
                resolved = (p.parent / target.split("#", 1)[0]).resolve()
                links.append(dict(source=str(p.relative_to(installed)), target=target, exists=resolved.exists(), inside=resolved.is_relative_to(installed)))
    source_matches = []
    for p in files:
        rel = p.relative_to(installed)
        if rel.parts[0] == "skills":
            source = replica / "sage" / rel
        elif rel.parts[:2] == ("sage", "bin"):
            source = replica / "sage/scripts" / rel.name
        else:
            continue
        source_matches.append(dict(path=str(rel), sha256=digest(p), matches_source=digest(p) == digest(source)))
    save("installed-audit.json", dict(files=[str(p.relative_to(installed)) for p in files], links=links, source_matches=source_matches))
    assert all(row["exists"] and row["inside"] for row in links)
    assert all(row["matches_source"] for row in source_matches)
    # Reachability inventories are observations, not keyword-based semantic grading.
    packages = {}
    for skill in ("sage", "sage-promote"):
        root = installed / "skills" / skill
        pending = [root / "SKILL.md"]
        seen = set()
        while pending:
            p = pending.pop().resolve()
            if p in seen:
                continue
            seen.add(p)
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", p.read_text()):
                if "://" not in target:
                    q = (p.parent / target.split("#", 1)[0]).resolve()
                    if q.suffix == ".md" and q.exists():
                        pending.append(q)
        terms = {}
        for term in ("checkpoint", "snapshot", "events.jsonl", "plan.revised", "list_agents", "followup_task", "fork_turns", "effective", "root-context"):
            terms[term] = [{"file":str(p.relative_to(installed)), "line":n, "text":line} for p in sorted(seen) for n,line in enumerate(p.read_text().splitlines(),1) if term in line]
        packages[skill] = dict(reachable=[str(p.relative_to(installed)) for p in sorted(seen)], terms=terms)
    save("instruction-reachability.json", packages)
    save("candidate-retention.json", dict(manifest_sha256=digest(MANIFEST), file_count=len(manifest["source"]), all_copied_hashes_match=all(digest(replica / row["path"]) == row["sha256"] for row in manifest["source"])))
    changed = [p for p,h in protected.items() if digest(ROOT / p) != h]
    save("preservation.json", dict(protected_file_count=len(protected), changed=changed))
    report = json.loads((replica / "sage/evaluation/sandboxes/offline/report.json").read_text())
    save("summary.json", dict(offline=report, installed_file_count=len(files), local_links=len(links), protected_files=len(protected), changed=changed))
    print(json.dumps(dict(tests=report["tests"], suite_exit=suite["exit_code"], installed_files=len(files), links=len(links), protected_files=len(protected), changed=changed)))
    return int(bool(changed) or suite["exit_code"] != 0)

if __name__ == "__main__":
    raise SystemExit(main())
