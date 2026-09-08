#!/usr/bin/env python3
"""Bounded identifier/role/scorer primitives and reference-array probes."""
import copy
import json
import sys
from checks import HERE, SAGE, OLD, LIVE, call, save
control=json.loads((OLD / "historical-replay/paired-results-v3-adapted-informed-diagnostic.json").read_text())
A=["pairs",0,"treatment"]; E=A+["execution"]
dimension=next(iter(control["pairs"][0]["treatment"]["scores"]))
results=[]
def run(label,value,expected):
    p=HERE / "primitive-inputs" / (label+".json"); save(p,value)
    r=call([sys.executable,SAGE / "evaluation/pairing.py","validate-native",p,"--manifest",LIVE / "setup/frozen-pairs.json"])
    r.update(label=label,input=str(p),expected_exit=expected)
    try: structured=json.loads(r["stderr"]).get("ok") is False
    except (ValueError,AttributeError): structured=False
    r["matched"]=r["exit_code"]==expected and (expected!=2 or structured)
    results.append(r); save(HERE / "primitive-results.json",results)
targets=[("scorer-id",A+["scorer","id"]),("worker-role",A+["routing","workers",0,"role"]),
         ("worker-requested-model",A+["routing","workers",0,"requested_model"]),
         ("worker-effective-model",A+["routing","workers",0,"effective_model"]),
         ("root-effective-model",A+["routing","root_model_effective"]),
         ("evidence-id",E+["evidence",0,"id"]),("command-id",E+["commands",0,"id"])]
for label,path in targets:
    for suffix,value in (("bool",True),("number",1),("list",["text"]),("object",{"text":True})):
        modified=copy.deepcopy(control); parent=modified
        for key in path[:-1]: parent=parent[key]
        parent[path[-1]]=value; run(label+"-"+suffix,modified,2)
refs=[("completion",E+["completion","evidence_refs"]),("command",E+["commands",0,"evidence_refs"]),
      ("check",A+["checks",0,"evidence_refs"]),("score",A+["scores",dimension,"evidence_refs"]),
      ("scorer",A+["scorer","evidence_refs"]),("operational",A+["operational_evidence_refs"])]
for label,path in refs:
    modified=copy.deepcopy(control); ex=modified["pairs"][0]["treatment"]["execution"]
    alias=copy.deepcopy(next(e for e in ex["evidence"] if e["id"]=="outer")); alias["id"]="x"; ex["evidence"].append(alias)
    parent=modified
    for key in path[:-1]: parent=parent[key]
    parent[path[-1]]=["x"]; run(label+"-single-character-id-array-control",modified,0)
    parent[path[-1]]="x"; run(label+"-string-reference",modified,2)
modified=copy.deepcopy(control); arm=modified["pairs"][0]["treatment"]
alias=copy.deepcopy(next(e for e in arm["execution"]["evidence"] if e["id"]=="outer")); alias["id"]="x"; arm["execution"]["evidence"].append(alias)
arm["reported_tokens"]=1; arm["usage_evidence_refs"]=["x"]
run("usage-single-character-id-array-control",modified,0)
arm["usage_evidence_refs"]="x"; run("usage-string-reference",modified,2)
summary=dict(commands=len(results),targets=[dict(label=l,path=p) for l,p in targets],
             failures=[dict(label=r["label"],exit_code=r["exit_code"]) for r in results if not r["matched"]],
             scope="Non-string identifiers, worker role/model primitives and non-array evidence reference strings. Alias and usage controls are structural synthetic diagnostics, not new native evidence or usage claims.")
save(HERE / "primitive-summary.json",summary)
print(json.dumps(dict(commands=len(results),failures=summary["failures"])))
