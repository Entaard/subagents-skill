import copy
import json
import sys
import tempfile
from pathlib import Path

EVALUATION = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(EVALUATION), str(EVALUATION / "tests")]
from test_harness import HarnessTests
from support import complete_read_run, dump
from score_status import append_review, validate_review
from pairing import prepare, validate_result

case = HarnessTests()
case.setUp()
observations = {}
review = case.valid_review()
missing_evidence = copy.deepcopy(review)
missing_evidence.pop("score_evidence")
try:
    validate_review(missing_evidence, case.rubric)
    observations["old_evidence_free_review"] = "accepted"
except ValueError:
    observations["old_evidence_free_review"] = "rejected"
status = append_review(case.status(), case.valid_review("fail", 1))
status["modules"]["verification"]["pending_review"] = {"approach_id":"verification-a1","round":2,"gate_type":"verification_design_and_harness"}
second_fail = case.valid_review("fail", 2)
second_fail["finding_dispositions"] = [{"id":"E-1","status":"still_open","evidence":["sage/docs/CONTRACTS.md"]}]
try:
    append_review(status, second_fail)
    observations["truthful_fail_then_fail"] = "accepted"
except ValueError as error:
    observations["truthful_fail_then_fail"] = {"result":"rejected","reason":str(error)}
rows = complete_read_run("source-1")
ids = {row["event_id"] for row in rows}
observations["valid_source_fixture_dangling_trigger_ids"] = [value for row in rows for value in row["payload"].get("trigger_event_ids", []) if value not in ids]
with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as temporary:
    root = Path(temporary)
    selection_path = case._unseen_selection(root)
    selection = json.loads(selection_path.read_text())
    selection["rubric"] = str(EVALUATION / "rubric.json")
    dump(selection_path, selection)
    frozen = prepare(selection_path)
    results = case._results(root, frozen)
    observations["paired_dimensions_with_real_rubric"] = frozen["pairs"][0]["dimensions"]
    observations["required_case_dimensions_omitted"] = sorted(set(case.rubric["required_case_dimensions"]) - set(frozen["pairs"][0]["dimensions"]))
    observations["reduced_dimension_result"] = validate_result(results, frozen)
    results["pairs"][0]["treatment"]["execution"]["evidence"] = []
    try:
        validate_result(results, frozen)
        observations["old_score_only_pair"] = "accepted"
    except ValueError:
        observations["old_score_only_pair"] = "rejected"
print(json.dumps(observations, indent=2))
