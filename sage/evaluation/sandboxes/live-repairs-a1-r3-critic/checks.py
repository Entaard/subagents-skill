#!/usr/bin/env python3
"""Independent round-3 source-bound review evidence, confined to this directory."""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; SAGE=HERE.parents[2]; ROOT=SAGE.parent
R1=SAGE / "evaluation/sandboxes/live-repairs-a1-r1-critic"
R2=SAGE / "evaluation/sandboxes/live-repairs-a1-r2-critic"
BUILDER=SAGE / "evaluation/sandboxes/live-repairs-a1-r3-builder"
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
    roots=[R1,R2,BUILDER,LIVE,SAGE / "archive"]
    roots += [SAGE / f"evaluation/sandboxes/live-repairs-a1-r{n}-builder" for n in (1,2)]
    for base in roots:
        for current,dirs,files in os.walk(base):
            dirs[:]=[d for d in dirs if not any(x in d.lower() for x in ("profile","cache","browser-attempt"))]
            paths += [Path(current)/f for f in files if not any(x in f.lower() for x in ("cookie","session"))]
    manifest=json.loads((BUILDER / "candidate-manifest.json").read_text())
    for name in ("source","preserved_round_1_repair_source","frozen_guards"):
        for row in manifest[name]:
            p=ROOT / row["path"]; assert sha(p)==row["sha256"]; paths.append(p)
    paths += [SAGE / "docs/STATUS.json"]+[SAGE / f"docs/reviews/live-repairs-a1-r{n}.json" for n in (1,2)]
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(set(paths)) if p.is_file()}
def record(label,args,expected,records):
    r=call(args); r.update(label=label,expected_exit=expected,matched=r["exit_code"]==expected)
    if expected==2:
        try: structured=json.loads(r["stderr"]).get("ok") is False
        except (ValueError,AttributeError): structured=False
        r["matched"] &= structured and not r["stdout"] and "Traceback" not in r["stderr"]
    records.append(r)
    return r
def replay():
    results=[]
    for name in ("probes.json","surface-results.json","primitive-results.json"):
        for prior in json.loads((R2 / name).read_text()):
            if prior["label"].startswith("retained-old:"): continue
            args=prior["command"][:]; args[1]=str(SAGE / "evaluation/pairing.py")
            record(name+":"+prior["label"],args,prior["expected_exit"],results)
    save(HERE / "inventory-replay.json",results)
    failed_inputs={row["input"] for row in json.loads((R2 / "retained-failures.json").read_text())}
    exact=[row for row in results if row["command"][3] in failed_inputs]
    save(HERE / "inventory-summary.json",dict(commands=len(results),unexpected=[r["label"] for r in results if not r["matched"]],
         distinct_round2_failure_inputs=len(failed_inputs),all_exact_failures_rejected=all(r["matched"] for r in exact),
         classification="Retained independent inventory replay; informed diagnostics, no live trial."))
    print((HERE / "inventory-summary.json").read_text())
def boundaries():
    control=json.loads((R1 / "historical-replay/paired-results-v3-adapted-informed-diagnostic.json").read_text())
    A=["pairs",1,"baseline"]; E=A+["execution"]; results=[]
    def run(label,modified,expected):
        p=HERE / "new-inputs" / (label+".json"); save(p,modified)
        record(label,[sys.executable,SAGE / "evaluation/pairing.py","validate-native",p,"--manifest",LIVE / "setup/frozen-pairs.json"],expected,results)
    # Exercise the final baseline arm, where incomplete preflights can accidentally stop early.
    negative=[("late-worker-object",A+["routing","workers",0],None),
              ("late-check-ref-element",A+["checks",0,"evidence_refs"],[{"outer":True}]),
              ("late-scorer-blank",A+["scorer","id"]," \t\n"),
              ("late-command-exit-bool",E+["commands",0,"exit_code"],True),
              ("late-evidence-path-number",E+["evidence",0,"path"],17),
              ("late-evidence-kind-object",E+["evidence",0,"kind"],{}),
              ("late-check-outcome-array",A+["checks",0,"outcome"],["passed"]),
              ("late-native-exit-bool",E+["completion","native_exit_code"],True)]
    for label,path,value in negative:
        modified=copy.deepcopy(control); parent=modified
        for key in path[:-1]: parent=parent[key]
        parent[path[-1]]=value; run(label,modified,2)
    # Omission of consumed required fields must reject, optional unknown observations remain valid.
    for label,path in [("missing-scorer-id",A+["scorer","id"]),("missing-check-refs",A+["checks",0,"evidence_refs"]),
                       ("missing-command-exit",E+["commands",0,"exit_code"]),("missing-completion-exit",E+["completion","native_exit_code"]),
                       ("missing-native-provenance",E+["evidence",2,"provenance"])]:
        modified=copy.deepcopy(control); parent=modified
        for key in path[:-1]: parent=parent[key]
        if label=="missing-native-provenance":
            parent=next(x for x in modified["pairs"][1]["baseline"]["execution"]["evidence"] if x["kind"]=="native_observation")
        parent.pop(path[-1]); run(label,modified,2)
    for label in ("null-unknowns","absent-effective-models","empty-workers-and-commands","noncalendar-text"):
        modified=copy.deepcopy(control)
        for pair in modified["pairs"]:
            for name in ("treatment","baseline"):
                arm=pair[name]
                if label=="null-unknowns":
                    arm.update(reported_tokens=None,reported_money=None,usage_evidence_refs=[])
                    arm["routing"]["root_model_effective"]=None
                    for worker in arm["routing"]["workers"]: worker["effective_model"]=None
                elif label=="absent-effective-models":
                    arm["routing"].pop("root_model_effective",None)
                    for worker in arm["routing"]["workers"]: worker.pop("effective_model",None)
                elif label=="empty-workers-and-commands":
                    arm["routing"]["workers"]=[]; arm["execution"]["commands"]=[]
                else: arm["execution"].update(started_at="unparsed text",finished_at="not ordered")
        run(label,modified,0)
    modified=copy.deepcopy(control); completion=modified["pairs"][1]["baseline"]["execution"]["completion"]
    completion.update(native_exit_code=0,exit_evidence_refs=["outer"])
    run("synthetic-native-integer-with-native-ref",modified,0)
    completion["exit_evidence_refs"]=["checks"]
    run("subprocess-evidence-cannot-prove-native-exit",modified,2)
    save(HERE / "new-boundaries.json",results)
    print(json.dumps({"new_boundary_commands":len(results),"unexpected":[r["label"] for r in results if not r["matched"]]}))

if __name__=="__main__":
    mode=sys.argv[1]
    if mode=="before":
        assert sha(BUILDER / "candidate-manifest.json")=="28efb2b997dbe487ae7aefc9479ec9559dfb091198f8cfbd7dbc95cc1242b883"
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
        r=call([sys.executable,SAGE / "evaluation/run_verification.py","--mode","red","--evidence-dir",HERE / "offline"])
        save(HERE / "offline-command.json",r); print(r["stdout"]); assert r["exit_code"]==0
    elif mode=="replay": replay()
    elif mode=="boundaries": boundaries()
