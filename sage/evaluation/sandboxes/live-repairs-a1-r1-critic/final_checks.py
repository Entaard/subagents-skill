#!/usr/bin/env python3
import copy
import json
import shutil
import sys
from checks import HERE, SAGE, ROOT, call, save, digest

manifest=json.loads((SAGE / "evaluation/sandboxes/live-repairs-a1-r1-builder/candidate-manifest.json").read_text())
index=[]
for row in manifest["source"]:
    retained=HERE / "without-history" / row["path"]
    assert digest(retained)==row["sha256"]
    index.append(dict(original=row["path"],retained=str(retained.relative_to(ROOT)),sha256=digest(retained)))
save(HERE / "retained-candidate-source.json",index)
commands=[]
validator=HERE / "without-history/sage/evaluation/pairing.py"
for label in ("native-run-id-bool","native-start-bool","native-finish-object","native-execution-null"):
    result=call([sys.executable,validator,"validate-native",HERE / f"independent/{label}.json","--manifest",SAGE / "evaluation/sandboxes/live-evaluation/setup/frozen-pairs.json"])
    result["label"]=label; commands.append(result)
save(HERE / "retained-validator-reproductions.json",commands)
assert [r["exit_code"] for r in commands]==[0,0,0,1]

# Independent closure attempt: a failed current task cannot become a completed run
# merely by adding otherwise valid criterion observations and checks.
source=HERE / "independent/bounded-1"
target=HERE / "failed-current-completion"; shutil.copytree(source,target)
before=(target / "events.jsonl").read_bytes()
def ev(n,kind,payload):
    return dict(v=1,event_id=f"e-{n}",run_id="tiny-1",seq=n,at="2026-09-08T13:46:00Z",actor="root",type=kind,payload=payload)
wave=[ev(7,"evidence.recorded",dict(evidence_id="claim",criterion_ids=["c-1"],kind="observation",locator="fixture/claim",sha256=None)),
      ev(8,"check.recorded",dict(check_id="claim-check",criterion_ids=["c-1"],outcome="passed",evidence_ids=["claim"])),
      ev(9,"task.admitted",dict(task_id="other",task_revision=1,plan_revision=1)),
      ev(10,"task.result",dict(task_id="other",task_revision=1,outcome="passed",effect_status="reconciled",evidence_ids=["claim"])),
      ev(11,"run.closed",dict(status="completed",criterion_evidence={"c-1":["claim"]},scope_reconciled=True,remaining_human_items=[]))]
p=HERE / "failed-current-completion-wave.jsonl"; p.write_text("".join(json.dumps(x)+"\n" for x in wave))
result=call([sys.executable,HERE / "independent/installed/sage/bin/sage_state.py","append","--run-dir",target,"--events",p])
result["atomic_rejection"]=(target / "events.jsonl").read_bytes()==before
save(HERE / "failed-current-completion-result.json",result)
assert result["exit_code"]==2 and result["atomic_rejection"] and "every task in a completed plan must pass" in result["stderr"]
print(json.dumps({"retained_source_files":len(index),"retained_failures_reproduced":4,"failed_current_completion_rejected":True}))
