"""Task-scoped event generation; installed Sage remains state authority."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ARM = Path(__file__).resolve().parents[1]
RUN = ARM / "state" / "decoder-run"
HELPER = ARM / "installed" / "sage" / "bin" / "sage_state.py"
RUN_ID = "decoder-baseline"

def cli(*args):
    result = subprocess.run([sys.executable, str(HELPER), *args], text=True, capture_output=True)
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    result.check_returncode()
    return result.stdout

def append(items, name):
    seq = len((RUN / "events.jsonl").read_text().splitlines())
    events = []
    for kind, payload in items:
        seq += 1
        events.append({"v":1, "event_id":f"e-{seq}", "run_id":RUN_ID, "seq":seq,
                       "at":datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                       "actor":"root", "type":kind, "payload":payload})
    path = ARM / "evidence" / (name + ".jsonl")
    path.write_text("".join(json.dumps(event) + "\n" for event in events))
    cli("append", "--run-dir", str(RUN), "--events", str(path))
    cli("snapshot", "--run-dir", str(RUN), "--write")

def task(task_id, owner, deps, effect, objective, completion, inputs, returns, effort):
    return {"id":task_id, "revision":1, "objective":objective, "completion":completion,
            "dependencies":deps, "owner":owner, "effect":effect, "scope":[str(ARM / "work"), str(ARM / "evidence"), str(ARM / "state")],
            "inputs":inputs, "returns":returns, "risk":"low; framing correctness and bounded memory matter",
            "verification":"stdlib behavior checks and independent review",
            "requested_model":"gpt-6-astra", "requested_effort":effort, "fork_turns":"none"}

def evidence(eid, criteria, rel):
    path = ARM / rel
    return ("evidence.recorded", {"evidence_id":eid,"criterion_ids":criteria,"kind":"observation",
             "locator":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})

if __name__ == "__main__":
    if sys.argv[1] == "init":
        cli("init", "--run-dir", str(RUN), "--run-id", RUN_ID,
            "--objective", "Deliver a correct dependency-free Python byte-stream decoder with tests, README and independent review.",
            "--criteria", str(ARM / "evidence" / "criteria.json"))
        append([
          ("knowledge.selected", {"generation_id":"none", "cue_fingerprint":"72d8bc38b12a029a4927894c075bbbc79b18efed41be90ce61836b32c8afc78b", "cues":json.loads((ARM / "evidence" / "cues.json").read_text()),"matches":[],"retrieval_status":"no_match"}),
          ("plan.revised", {"revision":1,"reason":"initial","attempt_limit":1,"revision_limit":1,"no_progress":"Same failing criterion without new evidence or distinct strategy; at most one focused repair.","trigger_event_ids":["e-1"],"tasks":[
            task("build","root",[],"write","Implement exact framed byte stream protocol", "decoder.py, tests and README exist and tests pass", [str(ARM / "prompt.txt"), str(ARM / "inputs" / "vectors.json")],["decoder.py","test_decoder.py","README.md","build check output"],"high"),
            task("review","/root/live_code_baseline/review",["build"],"read","Independently review frozen decoder against original task", "Independent behavior checks and severity/evidence/fix checks returned; explicit release",[str(ARM / "prompt.txt"),str(ARM / "checks.json"),str(ARM / "inputs" / "vectors.json"),str(ARM / "work")],["review findings","independent check output","explicit release"],"xhigh"),
            task("integrate","root",["review"],"write","Disposition findings, verify final artifacts and close state", "All criteria evidenced, input hash unchanged, workers terminal and report persisted",["candidate","independent findings"],["final checks","hashes","Sage report"],"high")]}),
          ("task.admitted", {"task_id":"build","task_revision":1,"plan_revision":1}),
          ("checkpoint.written", {"next_action":"Implement bounded candidate", "baselines":["inputs/vectors.json sha256 717d86a57fe4cdd0af16ed2a2dd6fc3e0eb342fefdace082f2f3f0681847bebb"],"unresolved_user_items":[]})
        ], "plan-wave")
    elif sys.argv[1] == "build_done":
        append([
          evidence("build-check", ["wire-behavior","failure-and-reset","deliverables"], "evidence/build-check.txt"),
          ("task.result", {"task_id":"build","task_revision":1,"outcome":"passed","effect_status":"reconciled","evidence_ids":["build-check"]}),
          ("task.admitted", {"task_id":"review","task_revision":1,"plan_revision":1}),
          ("checkpoint.written", {"next_action":"Dispatch fresh read-only independent reviewer on frozen work files", "baselines":["Frozen candidate: work/decoder.py, work/test_decoder.py, work/README.md"],"unresolved_user_items":[]})
        ], "build-wave")
    elif sys.argv[1] == "review_started":
        append([
          ("agent.requested", {"task_id":"review","handle":"/root/live_code_baseline/review","requested_model":"gpt-6-astra","requested_effort":"xhigh","fork_turns":"none"}),
          ("agent.observed", {"handle":"/root/live_code_baseline/review","lifecycle":"active","effect_status":"none","effective_model":None,"effective_effort":None}),
          ("checkpoint.written", {"next_action":"Await read-only independent review while preserving candidate freeze","baselines":[],"unresolved_user_items":[]})
        ], "review-dispatch-wave")
    elif sys.argv[1] == "review_done":
        append([
          evidence("independent-review", ["wire-behavior","failure-and-reset","deliverables","live-procedure"], "evidence/independent-review.md"),
          ("agent.observed", {"handle":"/root/live_code_baseline/review","lifecycle":"completed","effect_status":"none","effective_model":None,"effective_effort":None}),
          ("task.result", {"task_id":"review","task_revision":1,"outcome":"passed","effect_status":"none","evidence_ids":["independent-review"]}),
          ("task.admitted", {"task_id":"integrate","task_revision":1,"plan_revision":1}),
          ("checkpoint.written", {"next_action":"Reconcile final evidence and close state; no findings or repair required","baselines":[],"unresolved_user_items":[]})
        ], "review-result-wave")
    elif sys.argv[1] == "close":
        criteria = ["wire-behavior","failure-and-reset","deliverables","live-procedure"]
        items = [
          evidence("final-check", criteria[:3], "evidence/final-check.txt"),
          evidence("review-reproduced", criteria[:3], "evidence/coordinator-review-check.txt"),
          evidence("journal", ["live-procedure"], "evidence/actor-journal.md"),
          evidence("candidate-hashes", ["deliverables"], "evidence/frozen-sha256.txt"),
          evidence("review-script", ["wire-behavior","failure-and-reset"], "evidence/independent_check.py"),
          ("note.recorded", {"category":"decision","text":"Complete from observed evidence: one bounded implementation and one independent read-only review. No findings or product repair. Requested coordinator gpt-6-astra/high and reviewer gpt-6-astra/xhigh. Observed effective identities, tokens and money remain null in actor records. Runtime observed Python 3.11.6; other versions untested. All effects reconciled; reviewer explicitly released and native completed observed.","evidence_ids":["journal","independent-review"],"corrects_event_id":None}),
          ("task.result", {"task_id":"integrate","task_revision":1,"outcome":"passed","effect_status":"reconciled","evidence_ids":["final-check","review-reproduced","journal","candidate-hashes"]})
        ]
        by_criterion = {
          "wire-behavior":["independent-review","review-reproduced","final-check"],
          "failure-and-reset":["independent-review","review-reproduced","final-check"],
          "deliverables":["final-check","candidate-hashes"],
          "live-procedure":["journal","independent-review"]
        }
        for criterion in criteria:
            items.append(("check.recorded", {"check_id":criterion,"criterion_ids":[criterion],"outcome":"passed","evidence_ids":by_criterion[criterion]}))
        items.extend([
          ("checkpoint.written", {"next_action":"Generate terminal validated report; release arm to outer coordinator","baselines":["All candidate and input hashes unchanged"],"unresolved_user_items":[]}),
          ("run.closed", {"status":"completed","criterion_evidence":by_criterion,"scope_reconciled":True,"remaining_human_items":[]})
        ])
        append(items, "closure-wave")
        validated = cli("validate", "--run-dir", str(RUN), "--terminal")
        (ARM / "evidence" / "state-validation.json").write_text(validated)
        reported = cli("report", "--run-dir", str(RUN), "--write")
        (ARM / "evidence" / "state-report-result.json").write_text(reported)
