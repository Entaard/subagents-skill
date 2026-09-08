from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from support import KNOWLEDGE_CLI, SAGE, STATE_CLI, complete_read_run, cues, dump, invoke, output, record, sandbox, write_log


def shell(script: Path, target: Path, source: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = ["bash", str(script), "--target-root", str(target)]
    if source is not None: command += ["--source-root", str(source)]
    return subprocess.run(command, cwd=SAGE.parent, text=True, capture_output=True, check=False)


def copy_source(destination: Path) -> None:
    for skill in ("sage", "sage-promote"):
        shutil.copytree(SAGE / f"skills/{skill}", destination / f"skills/{skill}")
    (destination / "scripts").mkdir()
    shutil.copy2(STATE_CLI, destination / "scripts/sage_state.py")
    shutil.copy2(KNOWLEDGE_CLI, destination / "scripts/sage_knowledge.py")


class InstallContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(STATE_CLI.is_file(), "future product missing: sage/scripts/sage_state.py")
        self.assertTrue(KNOWLEDGE_CLI.is_file(), "future product missing: sage/scripts/sage_knowledge.py")

    def test_install_uses_only_the_new_allowlist(self) -> None:
        with sandbox() as raw:
            target = Path(raw) / "target"; result = shell(SAGE / "install.sh", target)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipt = json.loads((target / "sage/receipt.json").read_text())
            installed = set(receipt["installed_files"])
            self.assertIn("skills/sage/SKILL.md", installed); self.assertIn("skills/sage-promote/SKILL.md", installed)
            self.assertIn("sage/bin/sage_state.py", installed); self.assertIn("sage/bin/sage_knowledge.py", installed)
            forbidden = ("policy/", "runtime/", "artifacts/", "phase-1", "source-manifest.json")
            self.assertFalse(any(any(token in path for token in forbidden) for path in installed))
            actual = {path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()}
            expected = {"sage/receipt.json", "sage/bin/sage_state.py", "sage/bin/sage_knowledge.py"}
            for skill in ("sage", "sage-promote"):
                for source in (SAGE / f"skills/{skill}").rglob("*"):
                    if source.is_file() and source.name != "source-manifest.json" and "__pycache__" not in source.parts:
                        expected.add(f"skills/{skill}/{source.relative_to(SAGE / f'skills/{skill}').as_posix()}")
            self.assertEqual(actual, expected); self.assertEqual(installed | {"sage/receipt.json"}, expected)
            for relative in installed:
                source = STATE_CLI if relative == "sage/bin/sage_state.py" else KNOWLEDGE_CLI if relative == "sage/bin/sage_knowledge.py" else SAGE / relative
                self.assertEqual(hashlib.sha256((target / relative).read_bytes()).hexdigest(), hashlib.sha256(source.read_bytes()).hexdigest())

    def test_update_rejects_unowned_conflicts_and_preserves_new_files(self) -> None:
        with sandbox() as raw:
            target = Path(raw) / "target"; self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
            user_file = target / "skills/sage/user-note.txt"; user_file.write_text("mine", encoding="utf-8")
            owned = target / "skills/sage/SKILL.md"; owned.write_text("local edit", encoding="utf-8")
            update = shell(SAGE / "install.sh", target)
            self.assertNotEqual(update.returncode, 0); self.assertEqual(owned.read_text(), "local edit"); self.assertEqual(user_file.read_text(), "mine")

    def test_uninstall_removes_only_unchanged_owned_files(self) -> None:
        with sandbox() as raw:
            target = Path(raw) / "target"; self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
            unrelated = target / "unrelated.txt"; unrelated.write_text("keep", encoding="utf-8")
            user_note = target / "skills/sage/user-note.txt"; user_note.write_text("mine", encoding="utf-8")
            modified = target / "skills/sage/SKILL.md"; modified.write_text("local edit", encoding="utf-8")
            removed = shell(SAGE / "uninstall.sh", target)
            self.assertEqual(removed.returncode, 0, removed.stderr)
            self.assertTrue(unrelated.is_file()); self.assertEqual(modified.read_text(), "local edit"); self.assertEqual(user_note.read_text(), "mine")
            retained = {row["path"]: row["reason"] for row in json.loads(removed.stdout)["retained"]}
            self.assertEqual(retained["skills/sage/user-note.txt"], "unowned")
            self.assertEqual(retained["skills/sage/SKILL.md"], "modified_or_replaced")
            self.assertFalse((target / "skills/sage-promote/SKILL.md").exists())

    def test_incomplete_source_fails_before_target_mutation(self) -> None:
        with sandbox() as raw:
            root = Path(raw); target = root / "target"; source = root / "incomplete-source"
            shutil.copytree(SAGE / "skills", source / "skills")
            (source / "scripts").mkdir(); shutil.copy2(KNOWLEDGE_CLI, source / "scripts/sage_knowledge.py")
            result = shell(SAGE / "install.sh", target, source)
            self.assertNotEqual(result.returncode, 0); self.assertFalse(target.exists())

    def test_installed_helpers_execute_report_resume_and_promotion_paths(self) -> None:
        with sandbox() as raw:
            root = Path(raw); target = root / "target"; self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
            state_cli = target / "sage/bin/sage_state.py"; knowledge_cli = target / "sage/bin/sage_knowledge.py"
            run = root / "run"; criteria = dump(root / "criteria.json", [{"id": "c-1", "text": "criterion"}])
            self.assertEqual(invoke(state_cli, "init", "--run-dir", str(run), "--run-id", "installed-run", "--objective", "installed smoke", "--criteria", str(criteria)).returncode, 0)
            self.assertEqual(invoke(state_cli, "snapshot", "--run-dir", str(run), "--write").returncode, 0)
            self.assertEqual(invoke(state_cli, "report", "--run-dir", str(run), "--write").returncode, 0)
            agents = dump(root / "agents.json", []); self.assertEqual(invoke(state_cli, "resume", "--run-dir", str(run), "--agents", str(agents)).returncode, 0)
            source = root / "source-1"; write_log(source, complete_read_run("source-1")); proposal = dump(root / "proposal.json", {"action": "create", "proposer": "proposer", "reviewer": "reviewer", "source_runs": [str(source)], "record": record()})
            store = root / "store"; self.assertEqual(invoke(knowledge_cli, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            self.assertEqual(invoke(knowledge_cli, "activate", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            cue_file = dump(root / "cues.json", cues(operation=["resume"])); retrieved = invoke(knowledge_cli, "retrieve", "--store-dir", str(store), "--cues", str(cue_file), "--limit", "1")
            self.assertEqual(retrieved.returncode, 0, retrieved.stderr); self.assertEqual(output(retrieved)["matches"][0]["id"], "k-1")
            corrected = record(revision=2, prior_revision=1); corrected["rule"] += " Preserve exact bytes."; corrected["counterevidence"] = ["source-1:source-1-e-4"]
            proposal_2 = dump(root / "proposal-2.json", {"action": "correct", "proposer": "proposer-2", "reviewer": "reviewer", "source_runs": [str(source)], "record": corrected})
            staged = invoke(knowledge_cli, "stage", "--store-dir", str(store), "--proposal", str(proposal_2), "--generation-id", "g-2", "--expected-current", "g-1")
            self.assertEqual(staged.returncode, 0, staged.stderr)
            self.assertEqual(invoke(knowledge_cli, "activate", "--store-dir", str(store), "--generation-id", "g-2", "--expected-current", "g-1").returncode, 0)
            self.assertEqual(invoke(knowledge_cli, "rollback", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "g-2").returncode, 0)

    def test_receipt_hashes_source_installed_and_inherited_ownership(self) -> None:
        with sandbox() as raw:
            target = Path(raw) / "target"
            self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
            first = json.loads((target / "sage/receipt.json").read_text())
            row = first["files"]["skills/sage/SKILL.md"]
            self.assertEqual(row["source_sha256"], row["installed_sha256"])
            self.assertIsNone(row["inherited_installed_sha256"])
            self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
            second = json.loads((target / "sage/receipt.json").read_text())
            self.assertEqual(second["operation"], "update")
            self.assertEqual(
                second["files"]["skills/sage/SKILL.md"]["inherited_installed_sha256"],
                first["files"]["skills/sage/SKILL.md"]["installed_sha256"],
            )

    def test_unowned_destination_conflict_is_reported_before_mutation(self) -> None:
        with sandbox() as raw:
            target = Path(raw) / "target"
            conflict = target / "skills/sage/SKILL.md"
            conflict.parent.mkdir(parents=True); conflict.write_text("mine", encoding="utf-8")
            result = shell(SAGE / "install.sh", target)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(conflict.read_text(), "mine")
            self.assertFalse((target / "sage/receipt.json").exists())

    def test_source_symlink_and_target_symlink_are_rejected(self) -> None:
        with sandbox() as raw:
            root = Path(raw); source = root / "source"; copy_source(source)
            state = source / "scripts/sage_state.py"; state.unlink(); state.symlink_to(STATE_CLI)
            target = root / "target"
            result = shell(SAGE / "install.sh", target, source)
            self.assertNotEqual(result.returncode, 0); self.assertFalse(target.exists())

            real = root / "real-target"; real.mkdir(); target.symlink_to(real, target_is_directory=True)
            result = shell(SAGE / "install.sh", target)
            self.assertNotEqual(result.returncode, 0); self.assertEqual(list(real.iterdir()), [])

    def test_target_component_symlink_is_rejected_without_following_it(self) -> None:
        with sandbox() as raw:
            root = Path(raw); target = root / "target"; outside = root / "outside"
            target.mkdir(); outside.mkdir(); (target / "skills").symlink_to(outside, target_is_directory=True)
            result = shell(SAGE / "install.sh", target)
            self.assertNotEqual(result.returncode, 0); self.assertEqual(list(outside.iterdir()), [])

    def test_tampered_receipt_path_is_rejected_before_uninstall(self) -> None:
        with sandbox() as raw:
            root = Path(raw); target = root / "target"
            self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
            outside = root / "outside.txt"; outside.write_text("keep", encoding="utf-8")
            receipt_path = target / "sage/receipt.json"
            receipt = json.loads(receipt_path.read_text())
            receipt["installed_files"].append("../outside.txt")
            receipt["files"]["../outside.txt"] = {
                "source_sha256": "0" * 64,
                "installed_sha256": hashlib.sha256(b"keep").hexdigest(),
                "inherited_installed_sha256": None,
            }
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            result = shell(SAGE / "uninstall.sh", target)
            self.assertNotEqual(result.returncode, 0); self.assertEqual(outside.read_text(), "keep")
            self.assertTrue((target / "skills/sage/SKILL.md").is_file())

    def test_replaced_owned_file_symlink_is_retained_on_uninstall(self) -> None:
        with sandbox() as raw:
            root = Path(raw); target = root / "target"
            self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
            outside = root / "outside.txt"; outside.write_text("keep", encoding="utf-8")
            owned = target / "skills/sage/SKILL.md"; owned.unlink(); owned.symlink_to(outside)
            result = shell(SAGE / "uninstall.sh", target)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(owned.is_symlink()); self.assertEqual(outside.read_text(), "keep")

    def test_bad_source_and_tampered_update_receipt_preserve_existing_install(self) -> None:
        with sandbox() as raw:
            root = Path(raw); target = root / "target"
            self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
            owned = target / "skills/sage/SKILL.md"; before = owned.read_bytes()
            receipt_path = target / "sage/receipt.json"; receipt = json.loads(receipt_path.read_text())
            receipt["files"]["skills/sage/SKILL.md"]["installed_sha256"] = "0" * 64
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            result = shell(SAGE / "install.sh", target)
            self.assertNotEqual(result.returncode, 0); self.assertEqual(owned.read_bytes(), before)

            source = root / "source"; copy_source(source)
            (source / "skills/sage/SKILL.md").unlink()
            result = shell(SAGE / "install.sh", root / "new-target", source)
            self.assertNotEqual(result.returncode, 0); self.assertFalse((root / "new-target").exists())

    def test_default_source_allows_required_evaluation_sandbox_target(self) -> None:
        target = SAGE / "evaluation/sandboxes/integration-wave-r1-overlap-positive/target"
        if target.exists():
            shutil.rmtree(target)
        result = shell(SAGE / "install.sh", target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((target / "skills/sage/SKILL.md").is_file())
        self.assertEqual(shell(SAGE / "uninstall.sh", target).returncode, 0)

    def test_receipt_parent_symlink_and_malformed_index_reject_cleanly(self) -> None:
        with sandbox() as raw:
            root = Path(raw); target = root / "target"; target.mkdir(); outside = root / "outside"; outside.mkdir()
            (target / "sage").symlink_to(outside, target_is_directory=True)
            escaped = outside / "receipt.json"
            escaped.write_text(json.dumps({
                "schema_version": "sage-install-receipt-v1", "operation": "install",
                "source_root": str(SAGE), "target_root": str(target), "installed_files": [], "files": {},
            }), encoding="utf-8")
            result = shell(SAGE / "uninstall.sh", target)
            self.assertNotEqual(result.returncode, 0); self.assertTrue(escaped.is_file())

            (target / "sage").unlink(); (target / "sage").mkdir()
            receipt = json.loads(escaped.read_text()); receipt["installed_files"] = [{}]
            (target / "sage/receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
            result = shell(SAGE / "uninstall.sh", target)
            self.assertNotEqual(result.returncode, 0); self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(json.loads(result.stderr)["ok"])

    def test_uninstall_preserves_preexisting_empty_directories(self) -> None:
        with sandbox() as raw:
            target = Path(raw) / "target"; (target / "skills").mkdir(parents=True)
            self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
            self.assertEqual(shell(SAGE / "uninstall.sh", target).returncode, 0)
            self.assertTrue((target / "skills").is_dir())

    def test_installed_skill_links_resolve_without_source_docs(self) -> None:
        with sandbox() as raw:
            target = Path(raw) / "target"
            self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
            markdown = list((target / "skills/sage").rglob("*.md")) + list((target / "skills/sage-promote").rglob("*.md"))
            self.assertTrue(markdown)
            for document in markdown:
                for link in re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", document.read_text(encoding="utf-8")):
                    if "://" not in link:
                        self.assertTrue((document.parent / link).is_file(), f"broken installed link: {document}: {link}")


if __name__ == "__main__": unittest.main()
