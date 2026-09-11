"""Fresh supplemental probes; does not replay or overwrite the primary runner."""
import ast
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
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = str(ROOT / "tmp")
sys.path.insert(0, str(SAGE / "evaluation/tests"))
from support import complete_read_run, dump, record, write_log

results = []
assertions = []
def check(name, passed, detail=None):
    assertions.append({"name": name, "passed": bool(passed), "detail": detail})
def cli(name, *args):
    argv = [sys.executable, str(SAGE / "scripts/sage_knowledge.py"), *map(str,args)]
    p = subprocess.run(argv, capture_output=True, text=True, cwd=REPO)
    results.append({"name":name,"argv":argv,"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr})
    return p
def stage(name, item):
    root = ROOT / "supplemental" / name
    source = root / "source-1"
    write_log(source, complete_read_run("source-1"))
    path = dump(root / "proposal.json", {"action":"create","proposer":"proposer","reviewer":"reviewer","source_runs":[str(source)],"record":item})
    return cli(name,"stage","--store-dir",root / "store","--proposal",path,"--generation-id","g-1","--expected-current","none")

for name, mutate in (
    ("unrecorded-external-provenance", lambda r:r["provenance"][0].update(locator="https://unrecorded.invalid/report#source-1-e-6")),
    ("unrecorded-external-refutation", lambda r:r["refutation"].update(evidence=["source-1:https://unrecorded.invalid/report#source-1-e-6"])),
    ("valid-fractional-review", lambda r:r.update(created_at="2026-09-07T00:00:00Z",reviewed_at="2026-09-07T00:00:00.500Z")),
    ("earlier-fractional-review", lambda r:r.update(created_at="2026-09-07T00:00:00.500Z",reviewed_at="2026-09-07T00:00:00Z")),
):
    item=record(); mutate(item); p=stage(name,item)
    expected = 0 if name == "valid-fractional-review" else 2
    check(name,p.returncode == expected,{"expected":expected,"actual":p.returncode})

root=ROOT / "supplemental/dangling-pointer"
(root / "store").mkdir(parents=True)
(root / "store/current.json").symlink_to(root / "absent-pointer.json")
p=cli("dangling-pointer","validate","--store-dir",root / "store")
check("dangling-pointer-rejected",p.returncode == 2)

for name,payload in (("invalid-utf8",b"\xff"),("overflow",b'{"operation":[],"include_non_supported":1e999}'),("duplicate",b'{"operation":[],"operation":[]}')):
    root=ROOT / "supplemental" / name; root.mkdir(parents=True)
    path=root / "cues.json"; path.write_bytes(payload)
    p=cli(name,"retrieve","--store-dir",root / "store","--cues",path,"--limit","3")
    check(name,p.returncode == 2 and json.loads(p.stderr)["code"] == "invalid_json")

files = [SAGE / "skills/sage-promote/SKILL.md", SAGE / "skills/sage-promote/references/promotion.md", SAGE / "skills/sage-promote/references/knowledge.md", SAGE / "skills/sage/SKILL.md", SAGE / "skills/sage/references/run.md", SAGE / "skills/sage/references/knowledge.md"]
for path in files:
    for href in re.findall(r"\]\(([^)]+)\)",path.read_text()):
        if "://" not in href:
            check("local-link:"+str(path.relative_to(SAGE))+":"+href,(path.parent / href.split("#")[0]).exists())
for relative in ("scripts/sage_knowledge.py","tests/test_knowledge.py"):
    ast.parse((SAGE / relative).read_text()); check("python-syntax:"+relative,True)
for path in (SAGE / "skills/sage-promote/SKILL.md",SAGE / "skills/sage/SKILL.md"):
    content=path.read_text(); front=content.split("---",2)[1]
    check("frontmatter:"+path.parent.name,"name: " + path.parent.name in front and "description: " in front)
check("explicit-only-promotion","allow_implicit_invocation: false" in (SAGE / "skills/sage-promote/agents/openai.yaml").read_text())
dump(ROOT / "supplemental-results.json",results)
dump(ROOT / "supplemental-assertions.json",assertions)
print(json.dumps({"commands":len(results),"assertions":len(assertions),"failed":[a["name"] for a in assertions if not a["passed"]]},indent=2))
