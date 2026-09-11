"""Record the frozen critic verdict through the existing status gate."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
sage = root.parents[2]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = str(root / "tmp")
status_path = sage / "docs/STATUS.json"
review_path = sage / "docs/reviews/promotion-a1-r1.json"
before = json.loads(status_path.read_text())
prior_review_hashes = {str(path.relative_to(sage)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (sage / "docs/reviews").glob("*.json") if path != review_path}
evidence = root / "status-before-review.json"
assert not evidence.exists(), "Review recording must not overwrite original status evidence"
evidence.write_text(json.dumps(before,indent=2)+"\n")
p = subprocess.run([sys.executable,str(sage / "evaluation/score_status.py"),str(review_path),"--status",str(status_path),"--output",str(status_path)],text=True,capture_output=True)
if p.returncode:
    (root / "status-record-error.txt").write_text(p.stderr)
    raise SystemExit(p.returncode)
after = json.loads(status_path.read_text())
review = json.loads(review_path.read_text())
assert after["history"][:-1] == before["history"]
assert after["modules"]["promotion"]["scores"] == review["scores"]
assert after["modules"]["promotion"]["open_errors"] == review["open_error_ids"]
assert after["modules"]["promotion"]["gate"] == "failed"
assert after["active_module"] == "promotion"
assert after["modules"]["integration"] == before["modules"]["integration"]
for relative,digest in prior_review_hashes.items():
    assert hashlib.sha256((sage / relative).read_bytes()).hexdigest() == digest
result={"ok":True,"review_id":review["review_id"],"verdict":review["verdict"],"open_errors":len(review["open_error_ids"]),"history_prefix_preserved":True,"prior_reviews_preserved":True,"integration_unchanged":True,"status_next_action":after["next_action"],"review_next_action":review["next_action"],"prior_review_hashes":prior_review_hashes}
(root / "status-record-result.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
