#!/usr/bin/env python3
"""Inventory the bounded v3 result container/element surface, excluding frozen manifests."""
import copy
import json
import sys
from checks import HERE, SAGE, OLD, LIVE, call, save

control=json.loads((OLD / "historical-replay/paired-results-v3-adapted-informed-diagnostic.json").read_text())
A=["pairs",0,"treatment"]
E=A+["execution"]
dimension=next(iter(control["pairs"][0]["treatment"]["scores"]))
targets=[
    ("result",[],"object"),("pairs",["pairs"],"array"),("pair",["pairs",0],"object"),
    ("arm",A,"object"),("execution",E,"object"),("completion",E+["completion"],"object"),
    ("completion-refs",E+["completion","evidence_refs"],"array"),
    ("exit-refs",E+["completion","exit_evidence_refs"],"array"),
    ("commands",E+["commands"],"array"),("command",E+["commands",0],"object"),
    ("command-refs",E+["commands",0,"evidence_refs"],"array"),
    ("evidence",E+["evidence"],"array"),("evidence-item",E+["evidence",0],"object"),
    ("routing",A+["routing"],"object"),("workers",A+["routing","workers"],"array"),
    ("worker",A+["routing","workers",0],"object"),
    ("checks",A+["checks"],"array"),("check",A+["checks",0],"object"),
    ("check-refs",A+["checks",0,"evidence_refs"],"array"),
    ("scores",A+["scores"],"object"),("score",A+["scores",dimension],"object"),
    ("score-refs",A+["scores",dimension,"evidence_refs"],"array"),
    ("scorer",A+["scorer"],"object"),("scorer-refs",A+["scorer","evidence_refs"],"array"),
    ("operational-refs",A+["operational_evidence_refs"],"array")]
results=[]
def run(label,value,expected):
    p=HERE / "surface-inputs" / (label+".json"); save(p,value)
    r=call([sys.executable,SAGE / "evaluation/pairing.py","validate-native",p,"--manifest",LIVE / "setup/frozen-pairs.json"])
    r.update(label=label,expected_exit=expected,input=str(p))
    try: structured=json.loads(r["stderr"]).get("ok") is False
    except (ValueError,AttributeError): structured=False
    r["matched"]=r["exit_code"]==expected and (expected!=2 or structured)
    results.append(r); save(HERE / "surface-results.json",results)

for label,path,kind in targets:
    for suffix,value in (("null",None),("bool",True),("number",1),("string","not-a-container"),
                         ("opposite",[] if kind=="object" else {})):
        modified=copy.deepcopy(control)
        if not path: modified=value
        else:
            parent=modified
            for key in path[:-1]: parent=parent[key]
            parent[path[-1]]=value
        run(label+"-"+suffix,modified,2)

# A mapping with exactly the old reference keys is still not the documented refs array.
for label,path,kind in targets:
    if not label.endswith("refs") or label=="exit-refs": continue
    modified=copy.deepcopy(control); parent=modified
    for key in path[:-1]: parent=parent[key]
    refs=parent[path[-1]]; parent[path[-1]]={ref:True for ref in refs}
    run(label+"-mapping",modified,2)

# Non-null reported usage requires refs; explicitly exercise that optional branch.
usage=copy.deepcopy(control)
arm=usage["pairs"][0]["treatment"]
arm["reported_tokens"]=1
arm["usage_evidence_refs"]=["outer"]
run("usage-branch-structural-control",usage,0)
for suffix,value in (("bool",True),("number",1),("mapping",{"outer":True}),("element-object",[{}])):
    modified=copy.deepcopy(usage); modified["pairs"][0]["treatment"]["usage_evidence_refs"]=value
    run("usage-refs-"+suffix,modified,2)

summary=dict(targets=[dict(label=l,path=p,expected=k) for l,p,k in targets],commands=len(results),
             failures=[dict(label=r["label"],exit_code=r["exit_code"]) for r in results if not r["matched"]],
             scope="V3 scored-result container and element types; original frozen manifest unchanged. Usage branch is synthetic structural evidence only, not observed usage.")
save(HERE / "surface-summary.json",summary)
print(json.dumps(dict(commands=len(results),failures=summary["failures"])))
