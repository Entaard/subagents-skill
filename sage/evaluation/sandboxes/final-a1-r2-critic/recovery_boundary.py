#!/usr/bin/env python3
"""Independent installed-CLI replay of a lost activation acknowledgement.

All source histories, role handles and changed-authority inputs are synthetic.
This checks existing public state/store controls and the instructed sequence;
it does not claim native compaction, semantic evidence or model behavior.
"""
import json
import os
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
audit = runpy.run_path(str(HERE / "audit.py"))
sha, save, command = (audit[k] for k in ("sha", "save", "command"))
copied_probe = HERE / "candidate-source/sage/evaluation/sandboxes/coordination/test_promotion_coordination.py"
fixtures = runpy.run_path(str(copied_probe))
installed = copied_probe.parent / "critic/installed"
STATE, KNOWLEDGE = (installed / "sage/bin" / name for name in ("sage_state.py", "sage_knowledge.py"))
WORK = HERE / "independent-boundary"
WORK.mkdir(exist_ok=True)
commands = []

def call(label, script, *args, expected=0):
    row = command("boundary-" + label, [sys.executable, script, *args])
    commands.append(dict(label=label, exit_code=row["exit_code"]))
    assert row["exit_code"] == expected, row
    return json.loads(row["stdout"] if expected == 0 else row["stderr"])

def dump(name, data):
    return fixtures["dump"](WORK / name, data)

source = WORK / "source-1"
fixtures["write_log"](source, fixtures["source_rows"]())
source_hash = sha(source / "events.jsonl")
store, own = WORK / "store", WORK / "coordinator"
base = fixtures["proposal"](WORK / "base.json", source, "k-base")
call("seed-stage", KNOWLEDGE, "stage", "--store-dir", store, "--proposal", base, "--generation-id", "g-base", "--expected-current", "none")
call("seed-activate", KNOWLEDGE, "activate", "--store-dir", store, "--generation-id", "g-base", "--expected-current", "none")
proposal = fixtures["proposal"](WORK / "reviewed.json", source, "k-next")
call("reviewed-stage", KNOWLEDGE, "stage", "--store-dir", store, "--proposal", proposal, "--generation-id", "g-next", "--expected-current", "g-base")
criteria = dump("criteria.json", [{"id":"c-1", "text":"the reviewed activation effect is reconciled"}])
call("init", STATE, "init", "--run-dir", own, "--run-id", "promotion-recovery", "--objective", "reconcile one reviewed promotion effect", "--criteria", criteria)
event = lambda seq,kind,payload: fixtures["event"](seq,kind,payload,"promotion-recovery")
planned = fixtures["plan"]("promotion-recovery", [fixtures["task"]("activate", "write", "root"), fixtures["task"]("follow-on", "write", "root")])
planned["payload"]["trigger_event_ids"] = ["e-1"]
baseline = [{"source_sha256":source_hash}, {"proposal_sha256":sha(proposal)}, {"pointer_sha256":sha(store/"current.json")}, {"expected":"g-base"}, {"generation":"g-next", "manifest_sha256":sha(store/"generations/g-next/manifest.json")}, {"authority":"synthetic fixture permits one activation"}]
rows = [planned, event(3,"checkpoint.written",{"next_action":"activate reviewed g-next once", "baselines":baseline,"unresolved_user_items":[]}), event(4,"task.admitted",{"task_id":"activate","task_revision":1,"plan_revision":1})]
wave = WORK / "initial-wave.jsonl"
wave.write_text("".join(json.dumps(r)+"\n" for r in rows))
call("initial-append", STATE, "append", "--run-dir", own, "--events", wave)
call("pre-effect-snapshot", STATE, "snapshot", "--run-dir", own, "--write")
call("activation-effect", KNOWLEDGE, "activate", "--store-dir", store, "--generation-id", "g-next", "--expected-current", "g-base")
# Deliberately omit the coordinator result: model a lost local acknowledgement.
log_before = sha(own/"events.jsonl")
agents = dump("agents.json", [])
resumed = call("uncertain-resume", STATE, "resume", "--run-dir", own, "--agents", agents)
assert resumed["admission_allowed"] is False
assert sha(own/"events.jsonl") == log_before
second = dump("second-writer.json",event(5,"task.admitted",{"task_id":"follow-on","task_revision":1,"plan_revision":1}))
blocked = call("blocked-second-writer",STATE,"append","--run-dir",own,"--event",second,expected=2)
assert blocked["code"] == "writer_busy"
call("observe-store", KNOWLEDGE, "validate", "--store-dir", store)
pointer = json.loads((store/"current.json").read_text())
assert pointer["generation_id"] == "g-next"
assert sha(source/"events.jsonl") == source_hash
pointer_hash = sha(store/"current.json")
reconciled = [
    event(5,"evidence.recorded",{"evidence_id":"pointer-observed","criterion_ids":["c-1"],"kind":"observation","locator":str(store/"current.json"),"sha256":pointer_hash}),
    event(6,"task.result",{"task_id":"activate","task_revision":1,"outcome":"passed","effect_status":"reconciled","evidence_ids":["pointer-observed"]}),
    event(7,"check.recorded",{"check_id":"pointer-check","criterion_ids":["c-1"],"outcome":"passed","evidence_ids":["pointer-observed"]}),
    event(8,"run.amended",{"kind":"constraint","value":"Synthetic new authority cancels further effects; preserve observed store.","reason":"changed fixture authority on resume","corrects_event_id":None}),
    event(9,"checkpoint.written",{"next_action":"stop; do not admit cancelled follow-on","baselines":[{"current":"g-next","pointer_sha256":pointer_hash},{"authority":"further writes cancelled"}],"unresolved_user_items":[]}),
    event(10,"run.closed",{"status":"stopped","criterion_evidence":{"c-1":["pointer-observed"]},"scope_reconciled":True,"remaining_human_items":["follow-on intentionally unadmitted after changed fixture authority"]})
]
wave = WORK / "reconciliation-wave.jsonl"
wave.write_text("".join(json.dumps(r)+"\n" for r in reconciled))
call("reconciled-stop",STATE,"append","--run-dir",own,"--events",wave)
call("terminal-validation",STATE,"validate","--run-dir",own,"--terminal")
call("report",STATE,"report","--run-dir",own,"--write")
assert sha(store/"current.json") == pointer_hash
assert sha(source/"events.jsonl") == source_hash
assert len([r for r in commands if r["label"]=="activation-effect"])==1
save("independent-boundary-summary.json",dict(kind="informed independent installed-CLI scenario", native_live_trial=False, synthetic_role_ids=True, synthetic_authority=True, commands=commands, lost_acknowledgement_blocks_admission=True, second_writer_error=blocked["code"], store_observed_before_result=True, activation_not_replayed=True, source_log_unchanged=True, authority_change_recorded=True, cancelled_follow_on_unadmitted=True, honest_terminal="stopped", final_pointer="g-next"))
print(json.dumps(dict(commands=len(commands), assertions="passed", terminal="stopped", native_live_trial=False)))
