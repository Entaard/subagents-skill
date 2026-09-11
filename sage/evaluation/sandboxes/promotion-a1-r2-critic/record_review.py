"""Bind current repair submission and record review without losing prior history."""
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
review_path=sage / "docs/reviews/promotion-a1-r2.json"
before=json.loads(status_path.read_text())
submission=next(r for r in reversed(before["history"]) if r.get("event")=="builder_repair_submitted" and r.get("module")=="promotion" and r.get("round")==2)
binding={}
for relative,expected in submission["input_hashes"].items():
    actual=hashlib.sha256((sage.parent / relative).read_bytes()).hexdigest()
    binding[relative]={"expected":expected,"actual":actual,"matched":actual==expected}
assert all(r["matched"] for r in binding.values()), "Current candidate changed since round-2 submission"
actual_hashes=json.loads((root / "input-hashes.json").read_text())
assert all(binding[p]["actual"]==v for p,v in actual_hashes.items())
assert not (root / "status-before-review.json").exists()
(root / "submission-binding.json").write_text(json.dumps(binding,indent=2)+"\n")
(root / "status-before-review.json").write_text(json.dumps(before,indent=2)+"\n")
prior={str(p.relative_to(sage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (sage / "docs/reviews").glob("*.json") if p!=review_path}
p=subprocess.run([sys.executable,str(sage / "evaluation/score_status.py"),str(review_path),"--status",str(status_path),"--output",str(status_path)],capture_output=True,text=True)
if p.returncode:
    (root / "status-record-error.txt").write_text(p.stderr)
    raise SystemExit(p.returncode)
after=json.loads(status_path.read_text())
assert after["history"][:-1]==before["history"]
assert after["modules"]["promotion"]["open_errors"]==["PROMOTION-A1-R1-E3"]
assert after["modules"]["promotion"]["gate"]=="failed"
assert after["active_module"]=="promotion"
assert after["modules"]["integration"]==before["modules"]["integration"]
for relative,digest in prior.items():
    assert hashlib.sha256((sage / relative).read_bytes()).hexdigest()==digest
result={"ok":True,"review_id":"promotion-a1-r2","verdict":"fail","open_errors":["PROMOTION-A1-R1-E3"],"history_prefix_preserved":True,"prior_reviews_preserved":True,"integration_unchanged":True,"all_round2_submission_hashes_match":True}
(root / "status-record-result.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
