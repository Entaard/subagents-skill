#!/usr/bin/env python3
"""Round-2 independent checks; all output stays in this fresh critic root."""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
SAGE=HERE.parents[2]; ROOT=SAGE.parent
OLD=SAGE / "evaluation/sandboxes/live-repairs-a1-r1-critic"
BUILDER=SAGE / "evaluation/sandboxes/live-repairs-a1-r2-builder"
LIVE=SAGE / "evaluation/sandboxes/live-evaluation"
os.environ.update(PYTHONDONTWRITEBYTECODE="1",TMPDIR=str(HERE / "tmp"),SAGE_EVALUATION_SANDBOX=str(HERE / "work"))
for p in (HERE / "tmp",HERE / "work"): p.mkdir(exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2)+"\n")
def call(args):
    p=subprocess.run([str(x) for x in args],cwd=ROOT,text=True,capture_output=True)
    return dict(command=[str(x) for x in args],exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
def inventory():
    paths=[]
    for base in (OLD,BUILDER,LIVE,SAGE / "archive"):
        for current,dirs,files in os.walk(base):
            dirs[:]=[d for d in dirs if not any(x in d.lower() for x in ("profile","cache","browser-attempt"))]
            paths += [Path(current)/f for f in files if not any(x in f.lower() for x in ("cookie","session"))]
    manifest=json.loads((BUILDER / "candidate-manifest.json").read_text())
    for name in ("source","preserved_round_1_repair_source","frozen_guards"):
        for row in manifest[name]:
            p=ROOT / row["path"]; assert sha(p)==row["sha256"]; paths.append(p)
    paths += [SAGE / "docs/STATUS.json",SAGE / "docs/reviews/live-repairs-a1-r1.json"]
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths)) if p.is_file()}
def probes():
    evidence=[]
    current=SAGE / "evaluation/pairing.py"; old=OLD / "without-history/sage/evaluation/pairing.py"
    manifest=LIVE / "setup/frozen-pairs.json"
    def check(label,cli,p,expected):
        r=call([sys.executable,cli,"validate-native",p,"--manifest",manifest]); r.update(label=label,expected_exit=expected)
        r["matched"]=r["exit_code"]==expected
        if expected==2:
            try: r["structured_rejection"]=json.loads(r["stderr"]).get("ok") is False and "Traceback" not in r["stderr"]
            except (ValueError,AttributeError): r["structured_rejection"]=False
            r["matched"] &= r["structured_rejection"]
        evidence.append(r); save(HERE / "probes.json",evidence)
    exact=("native-run-id-bool","native-start-bool","native-finish-object","native-execution-null")
    for i,label in enumerate(exact):
        p=OLD / f"independent/{label}.json"
        check("retained-old:"+label,old,p,1 if i==3 else 0)
        check("current:"+label,current,p,2)
    control_path=OLD / "historical-replay/paired-results-v3-adapted-informed-diagnostic.json"
    control=json.loads(control_path.read_text()); check("valid-informed-native-control",current,control_path,0)
    v2=call([sys.executable,current,"validate",LIVE / "scoring-a1-r1/paired-results.json","--manifest",manifest])
    v2.update(label="original-v2-rejection",expected_exit=2,matched=v2["exit_code"]==2 and "lacks completed transcript evidence" in v2["stderr"]); evidence.append(v2)
    # Reuse all retained execution-negative fixtures unchanged, not old writer scripts.
    for p in sorted((OLD / "independent").glob("*.json")):
        if p.stem in exact or p.name in ("results.json","summary.json","criteria.json"): continue
        if p.stem.startswith(("native-","command-","commands-")):
            check("retained-negative:"+p.stem,current,p,2)
    mutations=[]
    for name in ("run_id","started_at","finished_at"):
        for label,value in (("blank"," \t\n"),("integer",123),("list",["observed"]),("null",None)):
            mutations.append((name+":"+label,["pairs",0,"treatment","execution",name],value))
    for label,path in (("result",[]),("pair",["pairs",0]),("arm",["pairs",0,"treatment"]),
                       ("execution",["pairs",0,"treatment","execution"]),
                       ("completion",["pairs",0,"treatment","execution","completion"]),
                       ("command",["pairs",0,"treatment","execution","commands",0]),
                       ("evidence-entry",["pairs",0,"treatment","execution","evidence",0])):
        for suffix,value in (("null",None),("list",[]),("bool",True),("string","invalid")):
            mutations.append((label+":"+suffix,path,value))
    for label,path,value in (
        ("completion-object-ref",["pairs",0,"treatment","execution","completion","evidence_refs"],[{}]),
        ("native-exit-object-ref",["pairs",0,"treatment","execution","completion","exit_evidence_refs"],[{}]),
        ("subprocess-object-ref",["pairs",0,"treatment","execution","commands",0,"evidence_refs"],[{}]),
        ("routing-null",["pairs",0,"treatment","routing"],None),
        ("worker-null",["pairs",0,"treatment","routing","workers",0],None),
        ("check-null",["pairs",0,"treatment","checks",0],None),
        ("scorer-null",["pairs",0,"treatment","scorer"],None)):
        mutations.append((label,path,value))
    for label,path,value in mutations:
        modified=copy.deepcopy(control)
        if not path: modified=value
        else:
            obj=modified
            for key in path[:-1]: obj=obj[key]
            obj[path[-1]]=value
        p=HERE / "inputs" / (label.replace(":","-")+".json"); save(p,modified); check(label,current,p,2)
    # Nonblank timestamp text is intentionally not a calendar/chronology claim.
    modified=copy.deepcopy(control)
    modified["pairs"][0]["treatment"]["execution"].update(started_at="not parsed",finished_at="not ordered")
    p=HERE / "inputs/noncalendar-text.json"; save(p,modified); check("documented-no-timestamp-parser",current,p,0)
    summary=dict(commands=len(evidence),unexpected=[r["label"] for r in evidence if not r["matched"]],classification="Independent public-CLI regression diagnostics; historical inputs informed, no live execution.")
    save(HERE / "probe-summary.json",summary); print(json.dumps(summary))

if __name__=="__main__":
    mode=sys.argv[1]
    if mode=="before":
        assert sha(BUILDER / "candidate-manifest.json")=="5744b40b326d72a750e1b3afbb295883eceaf405393c36fbf7600514321ffb29"
        inv=inventory(); save(HERE / "before.json",inv)
        manifest=json.loads((BUILDER / "candidate-manifest.json").read_text()); retained=[]
        for row in manifest["source"]:
            p=HERE / "candidate-source" / row["path"]; p.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT / row["path"],p)
            retained.append(dict(original=row["path"],retained=str(p.relative_to(ROOT)),sha256=sha(p)))
        save(HERE / "retained-source.json",retained); print(json.dumps({"protected_files":len(inv)}))
    elif mode=="after":
        after=inventory(); save(HERE / "after.json",after); before=json.loads((HERE / "before.json").read_text())
        result=dict(unchanged=before==after,protected_files=len(after),changed=[k for k in before if before[k]!=after.get(k)])
        save(HERE / "preservation.json",result); print(json.dumps(result)); assert result["unchanged"]
    elif mode=="offline":
        result=call([sys.executable,SAGE / "evaluation/run_verification.py","--mode","red","--evidence-dir",HERE / "offline"])
        save(HERE / "offline-command.json",result); print(result["stdout"]); assert result["exit_code"]==0
    elif mode=="probes": probes()
