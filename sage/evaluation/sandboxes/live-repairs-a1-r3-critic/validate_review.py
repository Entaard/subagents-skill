#!/usr/bin/env python3
import json
import shutil
import sys
from checks import HERE, SAGE, R2, save, call, sha
sys.path.insert(0,str(SAGE / "evaluation"))
from score_status import load_json, validate_review, append_review
review_path=SAGE / "docs/reviews/live-repairs-a1-r3.json"
status_path=SAGE / "docs/STATUS.json"; before=sha(status_path)
copy_path=HERE / "status-before-copy.json"; shutil.copy2(status_path,copy_path)
review=load_json(review_path)
validate_review(review,load_json(SAGE / "evaluation/rubric.json"))
projected=append_review(load_json(copy_path),review)
save(HERE / "status-projected-copy.json",projected)
assert sha(status_path)==before
assert projected["modules"]["live_repairs"]["open_errors"]==[]
assert projected["modules"]["live_repairs"]["gate"]=="passed"
rows=load_json(HERE / "inventory-replay.json")
required={x["input"] for x in load_json(R2 / "retained-failures.json")}
covered={x["command"][3] for x in rows if x["matched"] and x["expected_exit"]==2}
assert len(required)==42 and required<=covered
result=call([sys.executable,SAGE / "evaluation/score_status.py",review_path])
assert result["exit_code"]==0
save(HERE / "review-validation.json",dict(public_cli=result,status_transition_validated_on_own_copy=True,
     status_bytes_unchanged=True,projected_gate="passed",exact_failure_inputs_covered=42,review_sha256=sha(review_path)))
print("Review and STATUS-copy transition validate; actual STATUS unchanged; all 42 exact failures covered.")
