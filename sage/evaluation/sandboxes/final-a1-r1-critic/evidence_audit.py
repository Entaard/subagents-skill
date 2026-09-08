#!/usr/bin/env python3
"""Read-only historical score binding and final contract reachability checks."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2) + "\n")

def main():
    scored = ROOT / "sage/evaluation/sandboxes/live-evaluation/scoring-a1-r1"
    cards = []
    bindings = []
    for p in sorted(scored.glob("*-scorecard.json")):
        row = json.loads(p.read_text())
        cards.append({k:row[k] for k in ("arm", "scores", "checks", "open_errors", "gate")})
        for ev in row["evidence"]:
            path = Path(ev["path"])
            if not path.is_absolute():
                path = ROOT / path
            bindings.append(dict(arm=row["arm"], id=ev["id"], path=str(path), expected=ev["sha256"], observed=sha(path) if path.is_file() else None))
    save("historical-score-evidence.json", dict(scorecards=cards, bindings=bindings, mismatches=[r for r in bindings if r["expected"] != r["observed"]]))
    reach = json.loads((HERE / "instruction-reachability.json").read_text())
    # Narrow documentation-contract probe, deliberately not a simulated live trial.
    # The main entrypoint is a positive control for the existing shared seam.
    needed = ("events.jsonl", "plan.revised", "checkpoint", "list_agents", "followup_task")
    assessments = {skill:{term:bool(row["terms"][term]) for term in needed} for skill,row in reach.items()}
    result = dict(
        kind="installed-documentation-contract-probe",
        scenario="Invoke only $sage-promote. Lose conversation context after author review and staging, before deciding whether activation already happened. Resume from the promotion coordinator's own persisted authority, reconcile actors/effects and pointer/proposal baselines, then admit only the safe next action. Source runs must remain closed and unchanged.",
        oracle="R-030/R-031/R-035/R-036 plus ARCHITECTURE promotion-own-plan/log and context-loss protocol; semantic finding is based on complete manual reading, not term presence alone.",
        entrypoint_instruction_graph=reach,
        observations=assessments,
        positive_control_main_shared_contract_available=all(assessments["sage"].values()),
        promotion_own_workflow_sufficient=False,
        expected="A reachable own-run procedure specifies creation/authority, boundary checkpoint and safe resumed actor/effect/pointer reconciliation.",
        actual="Only source-run terminal validation is specified. The three reachable promotion Markdown files give no own coordinator run initialization, event log, checkpoint/snapshot or resumed-native reconciliation procedure. Knowledge generation snapshots represent stored records, not pending coordinator task/authority state.",
        not_claimed="No observed data loss, unsafe activation, failed native resume or live model behavior is inferred from this documentation omission.",
        fix_check="Install the repair freshly, start only sage-promote, and demonstrate a separate bounded own-run checkpoint/resume through existing public state seams at pre-dispatch and pre/post-stage or activation boundaries. Corrupt own log must pause; stale projection may rebuild only from valid authority; unknown actor/effects hold writes; changed pointer/proposal or user authority revises the next action. Source logs stay unchanged. Retain an inline no_change control without a ritual team.")
    save("standalone-promotion-contract.json", result)
    print(json.dumps(dict(scorecards=len(cards), evidence_bindings=len(bindings), historical_hash_mismatches=sum(r["expected"] != r["observed"] for r in bindings), main_control=result["positive_control_main_shared_contract_available"], promotion_contract="FAIL", evidence="standalone-promotion-contract.json")))
    return 1

if __name__ == "__main__":
    sys.exit(main())
