#!/usr/bin/env python3
"""Independent public-CLI boundary probes; never imports candidate logic."""
import copy
import json
import re
import sys
from pathlib import Path
from checks import HERE, ROOT, SAGE, call, save, digest

OUT = HERE / "independent"
OUT.mkdir(exist_ok=True)
rows = []

def observe(label, args, expected):
    result = call(args)
    result.update(label=label, expected_exit=expected, matched=result["exit_code"] == expected)
    rows.append(result)
    save(OUT / "results.json", rows)
    return result

def ev(seq, kind, payload):
    return dict(v=1, event_id=f"e-{seq}", run_id="tiny-1", seq=seq,
                at="2026-09-08T13:45:00Z", actor="root", type=kind, payload=payload)

target = OUT / "installed"
assert observe("install", ["bash", SAGE / "install.sh", "--target-root", target], 0)["matched"]
CLI = target / "sage/bin/sage_state.py"
contract = (target / "skills/sage/references/state.md").read_text()
assert "`assumption|decision`" in contract
examples = re.findall(r"```json\n(.*?)\n```", contract, re.S)
criteria = OUT / "criteria.json"; criteria.write_text(examples[0] + "\n")
note = json.loads(examples[-1])
tiny_wave = [json.loads(x) for x in re.search(r"```jsonl\n(.*?)\n```", contract, re.S)[1].splitlines()]
task = tiny_wave[0]["payload"]["tasks"][0]

def init(label):
    run = OUT / label
    assert observe(label + ":init", [sys.executable, CLI, "init", "--run-dir", run, "--run-id", "tiny-1", "--objective", "Critic boundary fixture", "--criteria", criteria], 0)["matched"]
    return run

def append(label, run, additions, expected=0):
    p = OUT / (label + ".jsonl")
    p.write_text("".join(json.dumps(x) + "\n" for x in additions))
    before = (run / "events.jsonl").read_bytes()
    result = observe(label, [sys.executable, CLI, "append", "--run-dir", run, "--events", p], expected)
    after = (run / "events.jsonl").read_bytes()
    result["atomic_rejection_or_preserved_prefix"] = before == after if expected == 2 else after.startswith(before)
    save(OUT / "results.json", rows)
    return result

run = init("published-note")
bad = copy.deepcopy(note); bad["payload"]["category"] = "finding-disposition"
append("published-note-invalid", run, [bad], 2)
append("published-note-valid", run, [note])
run = init("published-tiny"); append("published-tiny-wave", run, tiny_wave)
observe("published-tiny-terminal", [sys.executable, CLI, "validate", "--run-dir", run, "--terminal"], 0)

def base(label, effect="write", owner="/root/uncreated", kind="observation", bounds=2):
    run = init(label)
    primary = copy.deepcopy(task); primary.update(id="work", owner=owner, effect=effect)
    other = copy.deepcopy(task); other.update(id="other", effect="write")
    plan = dict(revision=1, reason="initial", attempt_limit=bounds, revision_limit=bounds,
                no_progress="stop if no distinct causal strategy", trigger_event_ids=["e-1"], tasks=[primary, other])
    prefix = [ev(2,"plan.revised",plan), ev(3,"task.admitted",dict(task_id="work",task_revision=1,plan_revision=1)),
              ev(4,"evidence.recorded",dict(evidence_id="dispatch",criterion_ids=[],kind=kind,locator="fixture/native-rejection",sha256=None))]
    assert append(label + "-base", run, prefix)["matched"]
    return run, plan

def no(seq=5, **updates):
    p=dict(task_id="work",task_revision=1,reason="Synthetic direct pre-creation refusal fixture",evidence_ids=["dispatch"]); p.update(updates)
    return ev(seq,"agent.not_created",p)
def result(seq=6, **updates):
    p=dict(task_id="work",task_revision=1,outcome="failed",effect_status="none",evidence_ids=["dispatch"]); p.update(updates)
    return ev(seq,"task.result",p)
def other(seq):
    return ev(seq,"task.admitted",dict(task_id="other",task_revision=1,plan_revision=1))

for label, settings, additions in [
    ("missing-proof",{},[no(evidence_ids=[])]),
    ("dangling-proof",{},[no(evidence_ids=["absent"])]),
    ("inference-proof",{"kind":"inference"},[no()]),
    ("unknown-proof",{"kind":"unknown"},[no()]),
    ("root-owner",{"owner":"root"},[no()]),
    ("stale-no-creation",{},[no(task_revision=2)]),
    ("bool-revision",{},[no(task_revision=True)]),
    ("unknown-creation",{},[result(5)]),
    ("duplicate-fact",{},[no(),no(6)]),
    ("passed-no-creation",{},[no(),result(outcome="passed")]),
    ("unknown-no-creation",{},[no(),result(outcome="unknown",effect_status="unknown")]),
    ("missing-result-proof",{},[no(),result(evidence_ids=[])]),
    ("duplicate-result",{},[no(),result(),result(7)]),
    ("unreleased-no-creation",{},[no(),other(6)]),
]:
    run,_=base(label,**settings); append(label + "-rejection",run,additions,2)

run,_=base("released-no-creation")
append("failed-fact-releases-writer",run,[no(),result(),other(7)])
run,_=base("real-request")
request = ev(5,"agent.requested",dict(task_id="work",handle="/root/uncreated",requested_model=task["requested_model"],requested_effort=task["requested_effort"],fork_turns=task["fork_turns"]))
append("real-request-recorded",run,[request])
append("real-request-cannot-be-uncreated",run,[no(6)],2)
append("real-request-holds-writer",run,[other(6)],2)
run,_=base("request-after-no-creation")
append("no-creation-recorded",run,[no()]); request["seq"]=6; request["event_id"]="e-6"
append("cannot-request-after-no-creation",run,[request],2)

for limit in (1,2):
    run, plan=base(f"bounded-{limit}",bounds=limit)
    append(f"bounded-{limit}-failed",run,[no(),result()])
    revised=copy.deepcopy(plan); revised.update(revision=2,reason="failure",trigger_event_ids=["e-4"],unmet_criterion="c-1",failure_evidence_ids=["dispatch"],cause="environment_or_tool",strategy_change="Root independently performs unavailable worker task")
    revised["tasks"][0].update(revision=2,owner="root")
    append(f"bounded-{limit}-revision",run,[ev(7,"plan.revised",revised)],2 if limit==1 else 0)
    if limit==2:
        append("successful-bounded-recovery",run,[ev(8,"task.admitted",dict(task_id="work",task_revision=2,plan_revision=2)),
            ev(9,"evidence.recorded",dict(evidence_id="success",criterion_ids=["c-1"],kind="observation",locator="fixture/completed-output",sha256=None)),
            result(10,task_revision=2,outcome="passed",effect_status="reconciled",evidence_ids=["success"]),
            ev(11,"task.admitted",dict(task_id="other",task_revision=1,plan_revision=2)),
            result(12,task_id="other",outcome="passed",effect_status="reconciled",evidence_ids=["success"]),
            ev(13,"check.recorded",dict(check_id="checked",criterion_ids=["c-1"],outcome="passed",evidence_ids=["success"])),
            ev(14,"run.closed",dict(status="completed",criterion_evidence={"c-1":["success"]},scope_reconciled=True,remaining_human_items=[]))])
        observe("bounded-recovery-terminal",[sys.executable,CLI,"validate","--run-dir",run,"--terminal"],0)

run,_=base("typed-uncertainty")
append("typed-unknown-untested",run,[ev(5,"evidence.recorded",dict(evidence_id="missing-cell",criterion_ids=[],kind="unknown",locator="task/missing-cell-value",sha256=None)),
    ev(6,"evidence.recorded",dict(evidence_id="untested-input",criterion_ids=[],kind="untested",locator="task/touch-not-tested",sha256=None))])
observe("typed-report",[sys.executable,CLI,"report","--run-dir",run,"--write"],0)
assert all(x in (run / "report.md").read_text() for x in ("task/missing-cell-value","task/touch-not-tested","No entries recorded."))

manifest=SAGE / "evaluation/sandboxes/live-evaluation/setup/frozen-pairs.json"
control=json.loads((HERE / "historical-replay/paired-results-v3-adapted-informed-diagnostic.json").read_text())
mutations=[
    ("native-bool-exit",["completion","native_exit_code"],True),
    ("native-float-exit",["completion","native_exit_code"],0.0),
    ("native-string-exit",["completion","native_exit_code"],"0"),
    ("native-invented-exit",["completion","native_exit_code"],0),
    ("native-failed-lifecycle",["completion","lifecycle"],"failed"),
    ("native-bool-lifecycle",["completion","lifecycle"],True),
    ("native-null-completion",["completion"],None),
    ("native-array-completion",["completion"],[]),
    ("native-journal-proof",["completion","evidence_refs"],["journal"]),
    ("native-missing-proof",["completion","evidence_refs"],[]),
    ("native-object-proof",["completion","evidence_refs"],[{}]),
    ("native-string-refs",["completion","evidence_refs"],"outer"),
    ("native-null-with-exit-proof",["completion","exit_evidence_refs"],["outer"]),
    ("commands-null",["commands"],None),
    ("command-bool",["commands"],[True]),
    ("command-bool-exit",["commands",0,"exit_code"],True),
    ("command-string-exit",["commands",0,"exit_code"],"0"),
    ("command-no-evidence",["commands",0,"evidence_refs"],[]),
    ("command-dangling-evidence",["commands",0,"evidence_refs"],["absent"]),
    ("native-run-id-bool",["run_id"],True),
    ("native-start-bool",["started_at"],True),
    ("native-finish-object",["finished_at"],{"unknown":True}),
]
for label, trail, value in mutations:
    modified=copy.deepcopy(control); obj=modified["pairs"][0]["treatment"]["execution"]
    for key in trail[:-1]: obj=obj[key]
    obj[trail[-1]]=value
    p=OUT/(label+".json"); save(p,modified)
    observe(label,[sys.executable,SAGE/"evaluation/pairing.py","validate-native",p,"--manifest",manifest],2)

for label, change in [
    ("native-missing-provenance",lambda e: e.pop("provenance",None)),
    ("native-bool-provenance",lambda e: e.update(provenance=True)),
    ("native-blank-provenance",lambda e: e.update(provenance="  ")),
    ("native-hash-contradiction",lambda e: e.update(sha256="0"*64)),
    ("native-evidence-kind-contradiction",lambda e: e.update(kind="artifact")),
]:
    modified=copy.deepcopy(control)
    native=next(e for e in modified["pairs"][0]["treatment"]["execution"]["evidence"] if e["id"]=="outer")
    change(native); p=OUT/(label+".json"); save(p,modified)
    observe(label,[sys.executable,SAGE/"evaluation/pairing.py","validate-native",p,"--manifest",manifest],2)
modified=copy.deepcopy(control); modified["pairs"][0]["treatment"]["execution"]=None
p=OUT/"native-execution-null.json"; save(p,modified)
observe("native-execution-null",[sys.executable,SAGE/"evaluation/pairing.py","validate-native",p,"--manifest",manifest],2)

save(OUT/"summary.json",dict(commands=len(rows),unexpected=[r["label"] for r in rows if not r["matched"]],
     non_atomic=[r["label"] for r in rows if not r.get("atomic_rejection_or_preserved_prefix",True)],
     classification="Independent synthetic boundary tests plus malformed informed historical v3 adaptations; no new live trial."))
print((OUT/"summary.json").read_text())
