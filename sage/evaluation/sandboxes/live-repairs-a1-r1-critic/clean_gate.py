#!/usr/bin/env python3
"""Prove the normal offline gate is independent of retained live sandboxes."""
import json
import re
import shutil
import sys
from checks import HERE, SAGE, ROOT, call, save, digest

replica = HERE / "without-history" / "sage"
replica.mkdir(parents=True)
for name in ("skills", "scripts", "tests", "docs"):
    shutil.copytree(SAGE / name, replica / name, ignore=shutil.ignore_patterns("__pycache__", "reviews"))
shutil.copytree(SAGE / "evaluation", replica / "evaluation", ignore=shutil.ignore_patterns("sandboxes", "results", "__pycache__"))
for name in ("install.sh", "uninstall.sh", "README.md", "ARCHITECTURE.md"):
    shutil.copy2(SAGE / name, replica / name)
assert not (replica / "evaluation/sandboxes/live-evaluation").exists()
result = call([sys.executable, replica / "evaluation/run_verification.py", "--mode", "red", "--evidence-dir", replica / "evaluation/sandboxes/critic-offline"])
save(HERE / "without-history-command.json", result)
print(result["stdout"])
assert result["exit_code"] == 0, result["stderr"]

candidate = SAGE / "evaluation/sandboxes/live-repairs-a1-r1-builder/candidate-manifest.json"
assert digest(candidate) == "46f9c89edf0d39d0bab0c4853e326c0d1e43b41dfb0096415a16f65ba43f157d"
manifest = json.loads(candidate.read_text())
links=[]
for row in manifest["source"]:
    path=ROOT / row["path"]
    if path.suffix != ".md": continue
    for raw in re.findall(r"\[[^\]]*\]\(([^)]+)\)",path.read_text()):
        if re.match(r"[a-z]+://",raw) or raw.startswith("#"): continue
        dest=(path.parent / raw.split("#")[0]).resolve()
        links.append(dict(source=row["path"],target=raw,exists=dest.exists()))
save(HERE / "static.json", dict(candidate_hash=digest(candidate),local_links=links,missing_links=[x for x in links if not x["exists"]],
     spines={name:len((SAGE / f"skills/{name}/SKILL.md").read_text().splitlines()) for name in ("sage","sage-promote")},
     diff_check=call(["git","diff","--check","--","sage"])))
