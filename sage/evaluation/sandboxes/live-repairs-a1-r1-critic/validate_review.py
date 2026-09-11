#!/usr/bin/env python3
import sys
from checks import HERE, SAGE, save, call, digest
sys.path.insert(0, str(SAGE / "evaluation"))
from score_status import load_json, validate_review, append_review

review_path=SAGE / "docs/reviews/live-repairs-a1-r1.json"
status_path=SAGE / "docs/STATUS.json"
before=digest(status_path)
review=load_json(review_path)
validate_review(review,load_json(SAGE / "evaluation/rubric.json"))
projected=append_review(load_json(status_path),review)
assert digest(status_path)==before
assert projected["modules"]["live_repairs"]["open_errors"]==["LIVE-03"]
result=call([sys.executable,SAGE / "evaluation/score_status.py",review_path])
assert result["exit_code"]==0
save(HERE / "review-validation.json",dict(public_cli=result,status_transition_validated_in_memory=True,
     status_bytes_unchanged=True,projected_gate=projected["modules"]["live_repairs"]["gate"],review_sha256=digest(review_path)))
print("Review schema and next STATUS transition validate; STATUS unchanged.")
