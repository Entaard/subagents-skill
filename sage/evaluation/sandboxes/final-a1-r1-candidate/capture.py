"""Bind the assembled active source for whole-skill review; no live evaluation."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SAGE = ROOT / "sage"
OUT = Path(__file__).resolve().parent
paths = [SAGE / name for name in ("ARCHITECTURE.md", "README.md", "install.sh", "uninstall.sh")]
for directory in ("skills", "scripts", "tests"):
    paths.extend(path for path in (SAGE / directory).rglob("*")
                 if path.is_file() and "__pycache__" not in path.parts)
paths.extend(path for path in (SAGE / "evaluation").glob("*") if path.is_file())
paths.extend(path for path in (SAGE / "evaluation/tests").rglob("*")
             if path.is_file() and "__pycache__" not in path.parts)
paths.extend(SAGE / "docs" / name for name in
             ("REQUIREMENTS.md", "CONTRACTS.md", "DECISIONS.md", "IMPLEMENTATION.md", "LIVE-RESULTS.md"))
bindings = [{"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(set(paths))]
result = {"approach_id": "final-a1", "round": 1, "gate_type": "final", "source": bindings,
          "precondition": "All dependency module gates passed; original live failures remain immutable.",
          "coverage_question": "sage/evaluation/sandboxes/final-whole-critic-coverage-question.json",
          "release": "Root assembly complete; source frozen for whole-skill critic."}
target = OUT / "candidate-manifest.json"
target.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"path": str(target.relative_to(ROOT)), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                  "files": len(bindings)}))
