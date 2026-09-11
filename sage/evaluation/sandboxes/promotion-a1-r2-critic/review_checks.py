"""Replay prior public probes only into new round-2 paths, then test adjacent controls."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SAGE=ROOT.parents[2]
OLD=ROOT.parent / "promotion-a1-r1-critic"
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
os.environ["TMPDIR"]=str(ROOT / "tmp")
(ROOT / "tmp").mkdir(exist_ok=True)
assert not (ROOT / "results.json").exists(), "Do not overwrite earlier round-2 evidence"
def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file() and not p.is_symlink()}
old_hashes=hashes(OLD)
for script in ("review_checks.py","supplemental_checks.py"):
    source=(OLD / script).read_text()
    transformed=source.replace("promotion-a1-r1-critic","promotion-a1-r2-critic")
    transformed=transformed.replace('["round"] == 1','["round"] == 2')
    replay_path=ROOT / ("replayed-"+script)
    replay_path.write_text(transformed)
    context={"__file__":str(replay_path),"__name__":"__main__"}
    exec(compile(transformed,str(replay_path),"exec"),context)
assert hashes(OLD)==old_hashes, "Prior evidence changed"

sys.path.insert(0,str(SAGE / "evaluation/tests"))
from support import complete_read_run,dump,record,write_log
results=[]
assertions=[]
def check(name,condition,detail=None):
    assertions.append({"name":name,"passed":bool(condition),"detail":detail})
def cli(name,*args):
    argv=[sys.executable,str(SAGE / "scripts/sage_knowledge.py"),*map(str,args)]
    p=subprocess.run(argv,text=True,capture_output=True,cwd=SAGE.parent)
    results.append({"name":name,"argv":argv,"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr})
    return p
def stage(name,item,rows=None):
    root=ROOT / "controls" / name
    source=root / "source-1"; write_log(source,rows or complete_read_run("source-1"))
    proposal=dump(root / "proposal.json",{"action":"create","proposer":"proposer","reviewer":"reviewer","source_runs":[str(source)],"record":item})
    return cli(name,"stage","--store-dir",root / "store","--proposal",proposal,"--generation-id","g-1","--expected-current","none")

for name,created,reviewed,expected in (
    ("equal-precision",".5",".500000",0),
    ("earlier-nanosecond",".5000002",".5000001",2),
    ("later-nanosecond",".5000001",".5000002",0),
    ("equal-nanosecond",".5000001",".5000001000",0),
):
    item=record();item["created_at"]="2026-09-07T00:00:00"+created+"Z";item["reviewed_at"]="2026-09-07T00:00:00"+reviewed+"Z"
    p=stage(name,item);check(name,p.returncode==expected,{"expected":expected,"actual":p.returncode})

for field in ("comparison","corroboration"):
    item=record(evidence_class="transferable_heuristic")
    item["gate_evidence"].pop("corroboration");item["gate_evidence"][field]=["source-1:source-1-e-6"]
    p=stage("valid-"+field,item);check("valid-"+field,p.returncode==0)
for hashed in (True,False):
    name="external-hash-"+str(hashed).lower()
    rows=complete_read_run("source-1");locator="https://recorded.invalid/report#source-1-e-6"
    rows[3]["payload"].update(locator=locator,sha256="a"*64 if hashed else None)
    item=record();item["provenance"]=[{"run_id":"source-1","locator":locator}];item["refutation"]["evidence"]=["source-1:"+locator]
    p=stage(name,item,rows);check(name,p.returncode==(0 if hashed else 2))

root=ROOT / "supplemental/dangling-pointer"
pointer=root / "store/current.json";link=os.readlink(pointer)
cues=dump(ROOT / "controls/pointer-cues.json",{"operation":["resume"]})
p=cli("dangling-retrieve","retrieve","--store-dir",root / "store","--cues",cues,"--limit","3")
check("dangling-retrieve",p.returncode==2 and json.loads(p.stderr)["code"]=="invalid_store")
check("dangling-preserved",pointer.is_symlink() and os.readlink(pointer)==link)

# Finish the fresh documented example with a second valid generation and normal rollback.
root=ROOT / "documented-example"
proposal=json.loads((root / "proposal.json").read_text());proposal["record"]["id"]="second-record"
path=dump(root / "proposal-second.json",proposal)
for name,args in (
    ("docs-stage-second",["stage","--store-dir",root / "store","--proposal",path,"--generation-id","g-2","--expected-current","g-1"]),
    ("docs-activate-second",["activate","--store-dir",root / "store","--generation-id","g-2","--expected-current","g-1"]),
    ("docs-rollback",["rollback","--store-dir",root / "store","--generation-id","g-1","--expected-current","g-2"]),
    ("docs-validate-final",["validate","--store-dir",root / "store"]),
):
    p=cli(name,*args);check(name,p.returncode==0,p.stderr)
check("docs-retained-second",(root / "store/generations/g-2/records/second-record.json").is_file())
check("original-evidence-preserved",hashes(OLD)==old_hashes)
dump(ROOT / "original-evidence-hashes.json",old_hashes)
dump(ROOT / "control-results.json",results)
dump(ROOT / "control-assertions.json",assertions)
print(json.dumps({"control_commands":len(results),"control_assertions":len(assertions),"failed":[a["name"] for a in assertions if not a["passed"]]},indent=2))
