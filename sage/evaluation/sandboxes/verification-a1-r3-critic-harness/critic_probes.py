import copy
import json
import sys
import tempfile
from pathlib import Path

EVALUATION = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(EVALUATION), str(EVALUATION / "tests")]
from test_harness import HarnessTests
from support import complete_read_run, dump
from score_status import append_review
from pairing import prepare, validate_result

case = HarnessTests()
case.setUp()
observations = {}
status = append_review(case.status(), case.valid_review("fail", 1))
status["modules"]["verification"]["pending_review"] = {"approach_id":"verification-a1","round":2,"gate_type":"verification_design_and_harness"}
second = case.valid_review("fail", 2)
second["finding_dispositions"] = [{"id":"E-1","status":"still_open","evidence":["sage/docs/CONTRACTS.md"]}]
updated = append_review(status, second)
observations["fail_then_fail_preserves_open_error"] = updated["modules"]["verification"]["open_errors"] == ["E-1"]
observations["failed_history_preserved"] = [row["verdict"] for row in updated["modules"]["verification"]["approaches"][0]["rounds"]] == ["fail","fail"]
rows = complete_read_run("source-1")
ids = {row["event_id"] for row in rows}
observations["source_fixture_dangling_trigger_ids"] = [value for row in rows for value in row["payload"].get("trigger_event_ids", []) if value not in ids]
with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
    root = Path(temporary)
    selection_path = case._unseen_selection(root)
    frozen = prepare(selection_path)
    results = case._results(root, frozen)
    observations["compliant_unknown_cost_pair"] = validate_result(results, frozen)["ok"]
    results["pairs"][0]["treatment"]["execution"]["evidence"] = []
    try:
        validate_result(results, frozen)
        observations["score_only_rejected"] = False
    except ValueError:
        observations["score_only_rejected"] = True
    checks_path = root / "checks.json"
    checks = json.loads(checks_path.read_text())
    original_checks = copy.deepcopy(checks)
    checks["dimensions"].remove("routing_efficiency")
    dump(checks_path, checks)
    try:
        prepare(selection_path)
        observations["required_dimension_omission_rejected"] = False
    except ValueError:
        observations["required_dimension_omission_rejected"] = True
    dump(checks_path, original_checks)
    selection = json.loads(selection_path.read_text())
    selection["cases"][0]["kind"] = "creative_interaction_smoke"
    dump(selection_path, selection)
    try:
        prepare(selection_path)
        observations["creative_experience_omission_rejected"] = False
    except ValueError:
        observations["creative_experience_omission_rejected"] = True
assert all(value is True for key,value in observations.items() if key != "source_fixture_dangling_trigger_ids")
assert observations["source_fixture_dangling_trigger_ids"] == []
print(json.dumps(observations, indent=2))
