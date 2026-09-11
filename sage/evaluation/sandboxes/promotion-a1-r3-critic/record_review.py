"""Record the independently verified source pass while preserving downstream uncertainty."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parent
sage=root.parents[2]
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
os.environ["TMPDIR"]=str(root / "tmp")
status_path=sage / "docs/STATUS.json"
review_path=sage / "docs/reviews/promotion-a1-r3.json"
before=json.loads(status_path.read_text())
binding=json.loads((root / "input-hashes.json").read_text())
assert all(hashlib.sha256((sage.parent / p).read_bytes()).hexdigest()==v for p,v in binding.items())
assert not (root / "status-before-review.json").exists()
(root / "status-before-review.json").write_text(json.dumps(before,indent=2)+"\n")
prior={str(p.relative_to(sage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (sage / "docs/reviews").glob("*.json") if p!=review_path}
p=subprocess.run([sys.executable,str(sage / "evaluation/score_status.py"),str(review_path),"--status",str(status_path),"--output",str(status_path)],capture_output=True,text=True)
if p.returncode:
    (root / "status-record-error.txt").write_text(p.stderr)
    raise SystemExit(p.returncode)
after=json.loads(status_path.read_text())
assert after["history"][:-1]==before["history"]
assert after["modules"]["promotion"]["open_errors"]==[]
assert after["modules"]["promotion"]["gate"]=="passed"
assert after["active_module"]=="integration"
assert after["modules"]["integration"]==before["modules"]["integration"]
for relative,digest in prior.items():
    assert hashlib.sha256((sage / relative).read_bytes()).hexdigest()==digest
result={"ok":True,"review_id":"promotion-a1-r3","verdict":"pass","open_errors":[],"history_prefix_preserved":True,"prior_reviews_preserved":True,"integration_unchanged_and_unscored":True,"active_module":"integration","all_candidate_hashes_match":True}
(root / "status-record-result.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
