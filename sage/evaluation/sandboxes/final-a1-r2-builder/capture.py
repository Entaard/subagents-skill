"""Freeze final-a1 round-2 active source and preservation evidence."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SAGE = ROOT / "sage"
OUT = Path(__file__).resolve().parent
PRIOR = SAGE / "evaluation/sandboxes/final-a1-r1-candidate/candidate-manifest.json"
CRITIC = SAGE / "evaluation/sandboxes/final-a1-r1-critic"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


paths = [SAGE / name for name in ("ARCHITECTURE.md", "README.md", "install.sh", "uninstall.sh")]
for directory in ("skills", "scripts", "tests"):
    paths.extend(path for path in (SAGE / directory).rglob("*") if path.is_file() and "__pycache__" not in path.parts)
paths.extend(path for path in (SAGE / "evaluation").glob("*") if path.is_file())
paths.extend(path for path in (SAGE / "evaluation/tests").rglob("*") if path.is_file() and "__pycache__" not in path.parts)
paths.extend(SAGE / "docs" / name for name in ("REQUIREMENTS.md", "CONTRACTS.md", "DECISIONS.md", "IMPLEMENTATION.md", "LIVE-RESULTS.md"))
bindings = [{"path": str(path.relative_to(ROOT)), "sha256": sha(path)} for path in sorted(set(paths))]
manifest = {
    "approach_id": "final-a1",
    "round": 2,
    "gate_type": "final",
    "source": bindings,
    "precondition": "Final-a1 round 1 retained one standalone-promotion documentation finding; dependency gates and historical live evidence remain unchanged.",
    "finding_target": "FINAL-A1-R1-E1",
    "release": "Builder candidate frozen; independent whole-skill critic pending.",
}
target = OUT / "candidate-manifest.json"
target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

prior = json.loads(PRIOR.read_text(encoding="utf-8"))
prior_by_path = {row["path"]: row["sha256"] for row in prior["source"]}
current_by_path = {row["path"]: row["sha256"] for row in bindings}
changed = sorted(path for path in prior_by_path if current_by_path.get(path) != prior_by_path[path])
allowed = sorted([
    "sage/ARCHITECTURE.md",
    "sage/docs/DECISIONS.md",
    "sage/docs/IMPLEMENTATION.md",
    "sage/skills/sage-promote/SKILL.md",
    "sage/skills/sage-promote/references/promotion.md",
])

protected = json.loads((CRITIC / "protected-before.json").read_text(encoding="utf-8"))
protected_changed = sorted(path for path, expected in protected.items() if not (ROOT / path).is_file() or sha(ROOT / path) != expected)
round1_status = CRITIC / "status-after-review.json"
expected_protected_changes = sorted(allowed + ["sage/docs/STATUS.json"])
retained_source = CRITIC / "candidate-source/sage"
retained_mismatches = []
for row in prior["source"]:
    path = retained_source / Path(row["path"]).relative_to("sage")
    if not path.is_file() or sha(path) != row["sha256"]:
        retained_mismatches.append(row["path"])

evidence_paths = [
    SAGE / "docs/LIVE-RESULTS.md",
    SAGE / "evaluation/native-result-protocol-v3.md",
    SAGE / "evaluation/rubric.json",
    PRIOR,
    SAGE / "docs/reviews/final-a1-r1.json",
    CRITIC / "standalone-promotion-contract.json",
    CRITIC / "instruction-reachability.json",
    CRITIC / "installed-audit.json",
]
preservation = {
    "prior_manifest_sha256": sha(PRIOR),
    "prior_candidate_source_files": len(prior["source"]),
    "prior_candidate_source_mismatches": retained_mismatches,
    "current_source_files": len(bindings),
    "intended_changed_source": allowed,
    "observed_changed_source": changed,
    "source_change_scope_matches": changed == allowed,
    "protected_baseline_files": len(protected),
    "protected_changes": protected_changed,
    "round1_status_matches_retained_review": sha(SAGE / "docs/STATUS.json") == sha(round1_status),
    "protected_changes_are_intended_source_plus_retained_round1_status": protected_changed == expected_protected_changes,
    "retained_evidence_sha256": {str(path.relative_to(ROOT)): sha(path) for path in evidence_paths},
}
(OUT / "preservation.json").write_text(json.dumps(preservation, indent=2) + "\n", encoding="utf-8")

print(json.dumps({
    "manifest": str(target.relative_to(ROOT)),
    "manifest_sha256": sha(target),
    "source_files": len(bindings),
    "changed_source": changed,
    "retained_candidate_mismatches": retained_mismatches,
    "protected_changes": protected_changed,
}))
