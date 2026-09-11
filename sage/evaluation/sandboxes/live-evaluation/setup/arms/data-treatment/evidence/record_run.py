"""Generate validated Sage event batches and retain helper command results."""
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ARM = Path(__file__).resolve().parents[1]
RUN = ARM / "state/run"
HELPER = ARM / "installed/sage/bin/sage_state.py"


def call(*args):
    result = subprocess.run([sys.executable, str(HELPER), *args], text=True, capture_output=True)
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)
    return result.stdout


def append(payloads, label):
    history = [json.loads(line) for line in (RUN / "events.jsonl").read_text().splitlines()]
    events = []
    for kind, payload in payloads:
        seq = len(history) + len(events) + 1
        events.append({"v": 1, "event_id": f"e-{seq}", "run_id": "data-treatment", "seq": seq,
                       "at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                       "actor": "root", "type": kind, "payload": payload})
    path = ARM / "evidence" / f"{label}-events.jsonl"
    path.write_text("".join(json.dumps(event) + "\n" for event in events))
    output = call("append", "--run-dir", str(RUN), "--events", str(path))
    output += call("snapshot", "--run-dir", str(RUN), "--write")
    (ARM / "evidence" / f"{label}-state-output.txt").write_text(output)


def evidence(identifier, relative, criteria):
    path = ARM / relative
    return ("evidence.recorded", {"evidence_id": identifier, "criterion_ids": criteria,
            "kind": "observation", "locator": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})


def task(identifier, owner, dependencies, objective, effect, model, effort):
    return {"id": identifier, "revision": 1, "objective": objective,
            "completion": {"analysis": "Frozen memo, deterministic script and JSON with source hashes and successful checks exist.",
                           "review": "Independent recomputation and findings returned with explicit release and observed terminal lifecycle.",
                           "integration": "All findings dispositioned, final checks pass, and terminal state/report validate."}[identifier],
            "dependencies": dependencies, "owner": owner, "effect": effect,
            "scope": [str(ARM / "work"), str(ARM / "evidence"), str(ARM / "state")],
            "inputs": [str(ARM / "prompt.txt"), str(ARM / "checks.json"), str(ARM / "inputs")],
            "returns": ["artifact/check evidence"], "risk": "low; fictional observational analysis",
            "verification": "arithmetic, sensitivity, interpretation, deliverables and live-procedure checks",
            "requested_model": model, "requested_effort": effort, "fork_turns": "none"}


def plan():
    cues = json.loads((ARM / "evidence/cues.json").read_text())
    tasks = [task("analysis", "root", [], "Build and freeze the requested analysis and memo.", "write", "gpt-6-astra", "high"),
             task("review", "/root/live_data_treatment/numerical_review", ["analysis"], "Independently audit arithmetic, reproducibility and interpretation.", "read", "gpt-5.6-sol", "xhigh"),
             task("integration", "root", ["review"], "Disposition findings and verify final integrated deliverables.", "write", "gpt-6-astra", "high")]
    append([("knowledge.selected", {"generation_id": "none", "cue_fingerprint": "6ff80a95f355f396ed7300cb20b08fcf06c45c9f98d492369843f12c09175bc9", "cues": cues, "matches": [], "retrieval_status": "no_match"}),
            ("plan.revised", {"revision": 1, "reason": "initial", "attempt_limit": 1, "revision_limit": 1,
                              "no_progress": "No repeated unchanged failed criterion without a distinct safe focused correction; at most one repair.",
                              "trigger_event_ids": ["e-1"], "tasks": tasks}),
            ("task.admitted", {"task_id": "analysis", "task_revision": 1, "plan_revision": 1}),
            ("checkpoint.written", {"next_action": "Build one analysis wave; then release coordinator writer lease before independent review.", "baselines": [], "unresolved_user_items": []})], "plan")


def freeze():
    append([evidence("candidate-checks", "evidence/candidate-checks.json", ["arithmetic", "sensitivity", "deliverables"]),
            evidence("memo", "work/decision-memo.md", ["interpretation"]),
            evidence("analysis-script", "work/analysis.py", ["arithmetic", "sensitivity", "deliverables"]),
            evidence("summary", "work/summary.json", ["arithmetic", "sensitivity", "deliverables"]),
            ("task.result", {"task_id": "analysis", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["candidate-checks", "memo", "analysis-script", "summary"]}),
            ("task.admitted", {"task_id": "review", "task_revision": 1, "plan_revision": 1}),
            ("checkpoint.written", {"next_action": "Dispatch fresh Sol xhigh read-only independent review. Root writer released; candidate frozen.", "baselines": [], "unresolved_user_items": []})], "frozen")


def finish():
    reviewer = "/root/live_data_treatment/numerical_review"
    append([("agent.requested", {"task_id": "review", "handle": reviewer, "requested_model": "gpt-5.6-sol", "requested_effort": "xhigh", "fork_turns": "none"}),
            ("agent.observed", {"handle": reviewer, "lifecycle": "completed", "effect_status": "reconciled", "effective_model": None, "effective_effort": None}),
            evidence("independent-review", "evidence/independent-review.md", ["arithmetic", "sensitivity", "interpretation", "deliverables", "live-procedure"]),
            evidence("actor-journal", "evidence/actor-journal.md", ["live-procedure"]),
            ("task.result", {"task_id": "review", "task_revision": 1, "outcome": "passed", "effect_status": "none", "evidence_ids": ["independent-review"]}),
            ("checkpoint.written", {"next_action": "Integrate no-findings review; final candidate/source checks passed unchanged.", "baselines": [], "unresolved_user_items": []}),
            ("task.admitted", {"task_id": "integration", "task_revision": 1, "plan_revision": 1}),
            ("note.recorded", {"category": "decision", "text": "Agent request and terminal observation recorded after return to preserve coordinator no-write interval. Native requested handle matched planned owner. Reviewer reported explicit read-only release and zero writes; completed lifecycle observed. No findings; no artifact repairs. Effective identity, tokens and money remain null. Root rechecked frozen hashes and candidate reproducibility.", "evidence_ids": ["independent-review", "actor-journal", "candidate-checks"], "corrects_event_id": None}),
            ("check.recorded", {"check_id": "arithmetic-independent", "criterion_ids": ["arithmetic"], "outcome": "passed", "evidence_ids": ["independent-review", "candidate-checks", "summary"]}),
            ("check.recorded", {"check_id": "sensitivity-independent", "criterion_ids": ["sensitivity"], "outcome": "passed", "evidence_ids": ["independent-review", "candidate-checks", "summary"]}),
            ("check.recorded", {"check_id": "interpretation-independent", "criterion_ids": ["interpretation"], "outcome": "passed", "evidence_ids": ["independent-review", "memo"]}),
            ("check.recorded", {"check_id": "reproducibility-final", "criterion_ids": ["deliverables"], "outcome": "passed", "evidence_ids": ["candidate-checks", "independent-review", "analysis-script"]}),
            ("check.recorded", {"check_id": "procedure-reconciliation", "criterion_ids": ["live-procedure"], "outcome": "passed", "evidence_ids": ["actor-journal", "independent-review"]}),
            ("task.result", {"task_id": "integration", "task_revision": 1, "outcome": "passed", "effect_status": "reconciled", "evidence_ids": ["candidate-checks", "independent-review", "actor-journal"]}),
            ("checkpoint.written", {"next_action": "Validate terminal state and generate report; final deliverables unchanged and no outstanding worker or finding.", "baselines": [], "unresolved_user_items": []}),
            ("run.closed", {"status": "completed", "criterion_evidence": {"arithmetic": ["independent-review", "summary"], "sensitivity": ["independent-review", "summary"], "interpretation": ["independent-review", "memo"], "deliverables": ["candidate-checks", "analysis-script"], "live-procedure": ["actor-journal", "independent-review"]}, "scope_reconciled": True, "remaining_human_items": []})], "closure")
    output = call("validate", "--run-dir", str(RUN), "--terminal")
    output += call("report", "--run-dir", str(RUN), "--write")
    (ARM / "evidence/terminal-check-output.txt").write_text(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["plan", "freeze", "finish"])
    args = parser.parse_args()
    {"plan": plan, "freeze": freeze, "finish": finish}[args.stage]()
