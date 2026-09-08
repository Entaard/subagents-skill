"""Bounded source-gate verification in fresh round-3 evidence paths."""
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SAGE=ROOT.parents[2]
REPO=SAGE.parent
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
os.environ["TMPDIR"]=str(ROOT / "tmp")
os.environ["SAGE_EVALUATION_SANDBOX"]=str(ROOT / "tests")
(ROOT / "tmp").mkdir(exist_ok=True)
assert not (ROOT / "results.json").exists(), "Never overwrite prior review evidence"
sys.path.insert(0,str(SAGE / "evaluation/tests"))
from support import complete_read_run,dump,record,write_log

def hashes(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file() and not p.is_symlink()}
old_roots=[ROOT.parent / "promotion-a1-r1-critic", ROOT.parent / "promotion-a1-r2-critic"]
old_hashes={str(p):hashes(p) for p in old_roots}
status=json.loads((SAGE / "docs/STATUS.json").read_text())
assert status["modules"]["promotion"]["pending_review"]["round"]==3
submission=next(r for r in reversed(status["history"]) if r.get("event")=="builder_repair_submitted" and r.get("module")=="promotion" and r.get("round")==3)
binding={relative:hashlib.sha256((REPO / relative).read_bytes()).hexdigest() for relative in submission["input_hashes"]}
assert binding==submission["input_hashes"]
dump(ROOT / "input-hashes.json",binding)

results=[];assertions=[]
def check(name,condition,detail=None):
    assertions.append({"name":name,"passed":bool(condition),"detail":detail})
def run(name,argv):
    p=subprocess.run(argv,text=True,capture_output=True,cwd=REPO)
    results.append({"name":name,"argv":argv,"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr})
    return p
def cli(name,*args):
    return run(name,[sys.executable,str(SAGE / "scripts/sage_knowledge.py"),*map(str,args)])
def stage(name,item,action="create",store=None,current="none",generation="g-1"):
    root=ROOT / "probes" / name;source=root / "source-1"
    write_log(source,complete_read_run("source-1"))
    proposal=dump(root / "proposal.json",{"action":action,"proposer":"proposer","reviewer":"reviewer","source_runs":[str(source)],"record":item})
    return cli(name,"stage","--store-dir",store or root / "store","--proposal",proposal,"--generation-id",generation,"--expected-current",current)

for name,folder,pattern in (("contracts","evaluation/tests","test_product_knowledge.py"),("regressions","tests","test_knowledge.py"),("state-contracts","evaluation/tests","test_product_state.py"),("state-regressions","tests","test_state.py")):
    p=run(name,[sys.executable,"-m","unittest","discover","-s",str(SAGE / folder),"-p",pattern,"-v"])
    (ROOT / (name+".txt")).write_text(p.stdout+p.stderr)
    check(name,p.returncode==0)

# Exact numerical oracle is independent of the candidate's string-tuple comparator.
fractions=[("5000002","5000001"),("5000001","5000002"),("5000001000","5000001"),("5000001","5000001000"),("5","500000"),("500000","5"),("","000000000000000000000000"),("000000000000000000000000",""),("","5"),("5",""),("500000000000000000000000000002","500000000000000000000000000001"),("500000000000000000000000000001","500000000000000000000000000002"),("5","500000000000000000000000000001"),("500000000000000000000000000001","5"),("009","01"),("01","009"),("1","10"),("10","1")]
for index,(created,reviewed) in enumerate(fractions):
    item=record();whole="2026-09-07T00:00:00"
    item["created_at"]=whole+("."+created if created else "")+"Z"
    item["reviewed_at"]=whole+("."+reviewed if reviewed else "")+"Z"
    expected=0 if Fraction("0."+(reviewed or "0"))>=Fraction("0."+(created or "0")) else 2
    name=f"precision-{index:02d}"
    p=stage(name,item)
    check(name,p.returncode==expected,{"created":item["created_at"],"reviewed":item["reviewed_at"],"expected":expected,"actual":p.returncode})
    if expected==2:
        check(name+"-no-generation",not (ROOT / "probes" / name / "store/generations/g-1").exists())
        check(name+"-structured",p.returncode==2 and json.loads(p.stderr)["code"]=="invalid_record")
for name,created,reviewed,expected in (
    ("whole-second-later","2026-09-07T00:00:00.99999999999999999999Z","2026-09-07T00:00:01Z",0),
    ("whole-second-earlier","2026-09-07T00:00:01Z","2026-09-07T00:00:00.99999999999999999999Z",2),
    ("day-boundary-later","2026-09-07T23:59:59.999999999999999Z","2026-09-08T00:00:00Z",0),
    ("day-boundary-earlier","2026-09-08T00:00:00Z","2026-09-07T23:59:59.999999999999999Z",2),
):
    item=record();item.update(created_at=created,reviewed_at=reviewed)
    p=stage(name,item);check(name,p.returncode==expected)

# Independently retain original public error controls, with no old output script replay.
item=record(evidence_class="transferable_heuristic");item["gate_evidence"].pop("corroboration");item["gate_evidence"]["comparison"]=["source-1:missing-evidence"]
p=stage("missing-comparison",item);check("E1-missing-comparison",p.returncode==2 and json.loads(p.stderr)["code"]=="invalid_reference")
for field in ("provenance","refutation"):
    item=record();uri="https://unrecorded.invalid/report#source-1-e-6"
    if field=="provenance":item[field]=[{"run_id":"source-1","locator":uri}]
    else:item[field]["evidence"]=["source-1:"+uri]
    p=stage("external-"+field,item);check("E1-external-"+field,p.returncode==2 and json.loads(p.stderr)["code"]=="invalid_reference")
root=ROOT / "retirement";store=root / "store"
check("E2-control-stage",stage("retirement-control",record(),store=store).returncode==0)
p=cli("retirement-control-activate","activate","--store-dir",store,"--generation-id","g-1","--expected-current","none");check("E2-control-activate",p.returncode==0)
before=(store / "current.json").read_bytes()
item=record(revision=2,prior_revision=1,status="retired");item["counterevidence"]=["source-1:source-1-e-4"]
p=stage("retirement-bypass",item,action="correct",store=store,current="g-1",generation="g-2")
check("E2-bypass-rejected",p.returncode==2 and json.loads(p.stderr)["code"]=="invalid_transition")
check("E2-pointer-preserved",before==(store / "current.json").read_bytes())
root=ROOT / "dangling";root.mkdir();pointer=root / "current.json";pointer.symlink_to("missing.json")
p=cli("dangling-validate","validate","--store-dir",root);check("E4-dangling-rejected",p.returncode==2 and json.loads(p.stderr)["code"]=="invalid_store")
check("E4-pointer-preserved",pointer.is_symlink() and os.readlink(pointer)=="missing.json")

# Execute all nine documentation steps from the actual complete proposal.
doc=(SAGE / "skills/sage-promote/references/knowledge.md").read_text()
blocks=re.findall(r"```json\n(.*?)\n```",doc,re.S)
root=ROOT / "documentation";source=root / "run-1";write_log(source,complete_read_run("run-1"))
proposal=json.loads(blocks[1]);proposal["source_runs"]=[str(source)]
path=dump(root / "proposal.json",proposal);cues=dump(root / "cues.json",json.loads(blocks[0]));store=root / "store"
second=json.loads(json.dumps(proposal));second["record"]["id"]="second-record";second_path=dump(root / "second.json",second)
for name,args in (
    ("validate-empty",["validate","--store-dir",store]),
    ("stage",["stage","--store-dir",store,"--proposal",path,"--generation-id","g-1","--expected-current","none"]),
    ("validate-staged",["validate","--store-dir",store]),
    ("activate",["activate","--store-dir",store,"--generation-id","g-1","--expected-current","none"]),
    ("retrieve",["retrieve","--store-dir",store,"--cues",cues,"--limit","3"]),
    ("stage-second",["stage","--store-dir",store,"--proposal",second_path,"--generation-id","g-2","--expected-current","g-1"]),
    ("activate-second",["activate","--store-dir",store,"--generation-id","g-2","--expected-current","g-1"]),
    ("rollback",["rollback","--store-dir",store,"--generation-id","g-1","--expected-current","g-2"]),
    ("validate-final",["validate","--store-dir",store]),
):
    p=cli("docs-"+name,*args);check("docs-"+name,p.returncode==0,p.stderr)
    if name=="retrieve" and p.returncode==0:check("docs-actionable-match",json.loads(p.stdout)["matches"][0]["rule"]==proposal["record"]["rule"])
check("docs-history-retained",(store / "generations/g-2/records/second-record.json").is_file())
for relative in ("scripts/sage_knowledge.py","tests/test_knowledge.py"):
    ast.parse((SAGE / relative).read_text());check("syntax:"+relative,True)
for relative in ("skills/sage-promote/SKILL.md","skills/sage-promote/references/knowledge.md","skills/sage-promote/references/promotion.md","skills/sage/SKILL.md","skills/sage/references/knowledge.md","skills/sage/references/run.md"):
    path=SAGE / relative
    for href in re.findall(r"\]\(([^)]+)\)",path.read_text()):
        if "://" not in href:check("link:"+relative+":"+href,(path.parent / href.split("#")[0]).exists())
for path in old_roots:check("prior-evidence-preserved:"+path.name,hashes(path)==old_hashes[str(path)])
check("candidate-still-frozen",binding=={p:hashlib.sha256((REPO / p).read_bytes()).hexdigest() for p in binding})
dump(ROOT / "prior-evidence-hashes.json",old_hashes)
dump(ROOT / "results.json",results)
dump(ROOT / "assertions.json",assertions)
summary={"commands":len(results),"assertions":len(assertions),"failed":[a["name"] for a in assertions if not a["passed"]]}
dump(ROOT / "summary.json",summary);print(json.dumps(summary,indent=2))
raise SystemExit(bool(summary["failed"]))
