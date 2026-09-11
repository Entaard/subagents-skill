#!/usr/bin/env python3
"""Final bounded installed documentation, archive, and parent-type checks."""
import ast
import json
import os
from pathlib import Path
import re
import sys
import probe as p

p.ROWS[:] = json.loads((p.HERE / "commands.json").read_text())
os.environ.update(PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(p.HERE / "tmp"), SAGE_EVALUATION_SANDBOX=str(p.HERE / "work"))
target = p.HERE / "docs-install"
assert p.install(target).returncode == 0
state = target / "sage/bin/sage_state.py"
knowledge = target / "sage/bin/sage_knowledge.py"
doc = (target / "skills/sage/references/state.md").read_text()
criteria = json.loads(re.findall(r"```json\n(.*?)\n```", doc, re.S)[0])
wave = re.findall(r"```jsonl\n(.*?)\n```", doc, re.S)[0]
case = p.HERE / "installed-doc-examples"; case.mkdir()
p.dump(case / "criteria.json", criteria)
(case / "wave.jsonl").write_text(wave + "\n")
run = case / "tiny-1"
def cli(script, *args):
    result = p.call("installed-documented-cli", [sys.executable, "-B", script, *args], cwd=case)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)
cli(state, "init", "--run-dir", run, "--run-id", "tiny-1", "--objective", "Run the documented bounded read", "--criteria", case / "criteria.json")
cli(state, "append", "--run-dir", run, "--events", case / "wave.jsonl")
cli(state, "snapshot", "--run-dir", run, "--write")
cli(state, "validate", "--run-dir", run, "--terminal")
cli(state, "report", "--run-dir", run, "--write")
p.dump(case / "agents.json", [])
cli(state, "resume", "--run-dir", run, "--agents", case / "agents.json")
sys.path.insert(0, str(p.SAGE / "evaluation/tests"))
from support import complete_read_run, write_log
source = case / "source-run-1"; write_log(source, complete_read_run())
doc = (target / "skills/sage-promote/references/knowledge.md").read_text()
blocks = re.findall(r"```json\n(.*?)\n```", doc, re.S)
cue = json.loads(blocks[0]); proposal = json.loads(blocks[1])
proposal["source_runs"] = [str(source)]
p.dump(case / "cues.json", cue); p.dump(case / "proposal.json", proposal)
store = case / "knowledge"
cli(knowledge, "validate", "--store-dir", store)
cli(knowledge, "stage", "--store-dir", store, "--proposal", case / "proposal.json", "--generation-id", "g-1", "--expected-current", "none")
cli(knowledge, "activate", "--store-dir", store, "--generation-id", "g-1", "--expected-current", "none")
retrieved = cli(knowledge, "retrieve", "--store-dir", store, "--cues", case / "cues.json", "--limit", "3")
assert retrieved["matches"][0]["id"] == proposal["record"]["id"]
proposal["action"] = "correct"; proposal["record"]["revision"] = 2; proposal["record"]["prior_revision"] = 1
proposal["record"]["rule"] += " Preserve the invalid log bytes for evidence."
proposal["record"]["counterevidence"] = ["run-1:e-6"]
p.dump(case / "proposal-2.json", proposal)
cli(knowledge, "stage", "--store-dir", store, "--proposal", case / "proposal-2.json", "--generation-id", "g-2", "--expected-current", "g-1")
cli(knowledge, "activate", "--store-dir", store, "--generation-id", "g-2", "--expected-current", "g-1")
cli(knowledge, "rollback", "--store-dir", store, "--generation-id", "g-1", "--expected-current", "g-2")
cli(knowledge, "validate", "--store-dir", store)
assert (store / "generations/g-2").is_dir()
p.dump(case / "result.json", {"passed": True, "state_commands": 6, "knowledge_commands": 8, "matched_record": retrieved["matches"][0]["id"], "active_generation": json.loads((store / "current.json").read_text())["generation_id"], "g2_retained": True, "source_doc_consulted_by_installed_process": False})

replaced = p.HERE / "replaced-later-parent"
assert p.install(replaced).returncode == 0
parent = replaced / "skills/sage/agents"
parent.rename(replaced / "saved-original-agents")
parent.write_text("user-replacement")
old = p.snapshot(replaced); result = p.uninstall(replaced); now = p.snapshot(replaced)
p.dump(p.HERE / "replaced-later-parent.json", {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "removed_before_rejection": sorted(set(old)-set(now)), "replacement_preserved": parent.read_text() == "user-replacement", "receipt_preserved": (replaced / "sage/receipt.json").is_file()})

archive = json.loads((p.HERE / "archive-audit.json").read_text())
assert all(x["inventory_match"] and x["git_match"] for x in archive["entries"])
active_replacements = [x["path"] for x in archive["entries"] if not x["absent_active"]]
assert active_replacements == ["scripts/sage-lifecycle.py"]
assert p.sha(p.SAGE / active_replacements[0]) != p.sha(p.SAGE / "archive/legacy" / active_replacements[0])
untracked_archive_explanation = p.SAGE / "archive/legacy/README.md"
assert untracked_archive_explanation.is_file()
p.dump(p.HERE / "archive-conclusion.json", {"exact_baseline_matches": 186, "archive_metadata_outside_inventory": ["README.md", "SHA256SUMS"], "rewritten_active_path_also_archived": active_replacements, "nonarchived_baseline_paths": archive["residual_active_entrypoints"], "nonarchived_bytecode": "scripts/__pycache__/check-phase0.cpython-311.pyc", "note": "The parent's eight-entrypoint shorthand was inaccurate. Actual 186-file archive claims hold. The baseline bytecode remains recoverable in Git; no product-source omission is identified."})
syntax = []
for base in (p.SAGE / "scripts", p.SAGE / "skills"):
    for file in base.rglob("*.py"):
        ast.parse(file.read_text()); syntax.append(str(file.relative_to(p.SAGE)))
frozen = json.loads((p.HERE / "input-hashes.json").read_text())
assert all(p.sha(p.SAGE / k) == v for k,v in frozen.items())
status = json.loads((p.SAGE / "docs/STATUS.json").read_text())
submitted = next(row for row in reversed(status["history"]) if row.get("event") == "builder_submission")
submitted_hashes = submitted.get("candidate_hashes", submitted.get("source_hashes", {}))
p.dump(p.HERE / "final-static.json", {"python_syntax": syntax, "candidate_input_hashes_unchanged": True, "submitted_hashes": submitted_hashes, "active_skill_files": sum(x.is_file() for x in (p.SAGE / "skills").rglob("*")), "skill_metadata": {str(x.relative_to(p.SAGE)): x.read_text() for x in (p.SAGE / "skills").rglob("openai.yaml")}})
print(json.dumps({"documented_installed_examples": "14 commands passed", "archive": "186 exact baseline matches", "candidate_unchanged": True, "later_parent_type_exit": result.returncode, "later_parent_removed_count": len(set(old)-set(now))}, indent=2))
