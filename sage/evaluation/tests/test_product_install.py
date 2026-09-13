from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
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
    shutil.copy2(SAGE / "scripts/sage-lifecycle.py", destination / "scripts/sage-lifecycle.py")
    shutil.copy2(SAGE / "install.sh", destination / "install.sh")
    shutil.copy2(SAGE / "uninstall.sh", destination / "uninstall.sh")


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

    def test_source_changes_ship_only_on_manual_update_across_targets(self) -> None:
        with sandbox() as raw:
            root = Path(raw); source = root / "checkout/sage"; copy_source(source)
            obsolete = "skills/sage/references/obsolete-fixture.md"
            replacement = "skills/sage/references/replacement-fixture.md"
            entrypoint = "skills/sage/SKILL.md"
            (source / obsolete).write_text("Fixture guidance awaiting retirement.\n", encoding="utf-8")
            initial = (source / entrypoint).read_text() + "\nFor fixture work, read [fixture guidance](references/obsolete-fixture.md).\n"
            (source / entrypoint).write_text(initial, encoding="utf-8")
            targets = [root / "machine-a/package", root / "docker-b/package"]
            inventories = []
            for target in targets:
                result = shell(source / "install.sh", target)
                self.assertEqual(result.returncode, 0, result.stderr)
                receipt = json.loads((target / "sage/receipt.json").read_text())
                self.assertEqual(Path(receipt["source_root"]), source)
                self.assertIn("skills/sage-promote/references/source.md", receipt["installed_files"])
                inventories.append({p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()})

            closed = root / "runtime/source-1"; write_log(closed, complete_read_run("source-1"))
            proposal = dump(root / "runtime/proposal.json", {"action": "create", "proposer": "proposer", "reviewer": "reviewer", "source_runs": [str(closed)], "record": record()})
            store = root / "runtime/knowledge"; helper = targets[0] / "sage/bin/sage_knowledge.py"
            self.assertEqual(invoke(helper, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            self.assertEqual(invoke(helper, "activate", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            runtime_before = {p.relative_to(root / "runtime"): p.read_bytes() for p in (root / "runtime").rglob("*") if p.is_file()}

            # Model a reviewed source patch; package bytes change only on later explicit install calls.
            (source / obsolete).unlink()
            (source / replacement).write_text("Replacement fixture guidance with its declared scope.\n", encoding="utf-8")
            revised = initial.replace("references/obsolete-fixture.md", "references/replacement-fixture.md")
            (source / entrypoint).write_text(revised, encoding="utf-8")
            note = source / "docs/promotions/fixture.md"; note.parent.mkdir(parents=True)
            note.write_text("Fixture retirement review; source evidence only.\n", encoding="utf-8")
            for target, before in zip(targets, inventories):
                self.assertEqual({p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}, before)
                user_file = target / "skills/sage/user-note.txt"; user_file.write_bytes(b"keep user data")
                updated = shell(source / "install.sh", target)
                self.assertEqual(updated.returncode, 0, updated.stderr)
                self.assertIn(obsolete, output(updated)["removed_retired"])
                self.assertFalse((target / obsolete).exists())
                self.assertEqual((target / replacement).read_bytes(), (source / replacement).read_bytes())
                self.assertEqual((target / entrypoint).read_text(), revised)
                self.assertEqual(user_file.read_bytes(), b"keep user data")
                self.assertFalse((target / "docs/promotions/fixture.md").exists())
                self.assertEqual(shell(source / "uninstall.sh", target).returncode, 0)
                self.assertEqual(user_file.read_bytes(), b"keep user data")
            self.assertEqual({p.relative_to(root / "runtime"): p.read_bytes() for p in (root / "runtime").rglob("*") if p.is_file()}, runtime_before)

    def test_missing_source_promotion_procedure_rejects_update_before_mutation(self) -> None:
        with sandbox() as raw:
            root = Path(raw); source = root / "source"; copy_source(source)
            target = root / "package"
            self.assertEqual(shell(source / "install.sh", target).returncode, 0)
            before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            (source / "skills/sage-promote/references/source.md").unlink()
            result = shell(source / "install.sh", target)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual({p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}, before)

    def test_update_and_reinstall_preserve_colocated_promoted_knowledge(self) -> None:
        with sandbox() as raw:
            root = Path(raw); source = root / "source"; copy_source(source)
            target = root / "package"; state = target / "sage"; store = state / "knowledge"
            environment = dict(os.environ, SAGE_STATE_ROOT=str(state), PYTHONDONTWRITEBYTECODE="1")

            def command(*args):
                result = subprocess.run(list(map(str, args)), env=environment, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                return output(result)

            def inventory():
                return {p.relative_to(state): p.read_bytes() for directory in (store, state / "runs") for p in directory.rglob("*") if p.is_file()}

            def knowledge(*args):
                return command(sys.executable, target / "sage/bin/sage_knowledge.py", *args)

            command("bash", source / "install.sh", "--target-root", target)
            closed = state / "runs/source-1"; write_log(closed, complete_read_run("source-1"))
            selected = command(sys.executable, target / "sage/bin/sage_state.py", "list-runs", "--limit", "20")["runs"][0]
            revisions = [(record(), "create"), (record(revision=2, prior_revision=1, status="retired"), "retire"), (record("k-provisional", status="provisional"), "create")]
            revisions[1][0]["review"].update(retirement_basis="superseded", retirement_reason="Replaced fixture guidance.")
            for index, (item, action) in enumerate(revisions, 1):
                proposal = dump(root / f"proposal-{index}.json", {"action": action, "proposer": "proposer", "reviewer": "reviewer", "source_runs": [str(closed)], "source_hashes": {selected["run_id"]: selected["events_sha256"]}, "record": item})
                parent = "none" if index == 1 else f"g-{index-1}"
                knowledge("stage", "--proposal", proposal, "--generation-id", f"g-{index}", "--expected-current", parent)
                knowledge("activate", "--generation-id", f"g-{index}", "--expected-current", parent)
            ordinary = dump(root / "ordinary.json", cues(operation=["resume"]))
            explicit = dump(root / "explicit.json", {**cues(operation=["resume"]), "include_non_supported": True})
            selections = [knowledge("retrieve", "--cues", path, "--limit", "3") for path in (ordinary, explicit)]
            self.assertEqual(selections[0]["matches"], [])
            self.assertEqual([item["id"] for item in selections[1]["matches"]], ["k-provisional"])
            before = inventory()
            updated_helper = source / "scripts/sage_knowledge.py"
            updated_helper.write_bytes(updated_helper.read_bytes() + b"\n# Source update fixture.\n")
            for cycle in range(2):
                with self.subTest(update=cycle):
                    self.assertEqual(command("bash", source / "install.sh", "--target-root", target)["operation"], "update")
                    self.assertEqual((target / "sage/bin/sage_knowledge.py").read_bytes(), updated_helper.read_bytes())
                    self.assertEqual(inventory(), before)
                    self.assertEqual(knowledge("validate")["generation_count"], 3)
                    self.assertEqual([knowledge("retrieve", "--cues", path, "--limit", "3") for path in (ordinary, explicit)], selections)
            command("bash", source / "uninstall.sh", "--target-root", target)
            self.assertEqual(inventory(), before)
            self.assertEqual(command("bash", source / "install.sh", "--target-root", target)["operation"], "install")
            self.assertEqual(inventory(), before)
            self.assertEqual(knowledge("validate")["current"], "g-3")
            knowledge("rollback", "--generation-id", "g-1", "--expected-current", "g-3")
            restored = knowledge("retrieve", "--cues", ordinary, "--limit", "3")
            self.assertEqual([(item["id"], item["revision"]) for item in restored["matches"]], [("k-1", 1)])
            self.assertTrue((store / "generations/g-3").is_dir())

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
        with sandbox() as raw:
            target = Path(raw) / "target"
            self.assertTrue(target.resolve().is_relative_to(SAGE.resolve()))
            result = shell(SAGE / "install.sh", target)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((target / "skills/sage/SKILL.md").is_file())
            self.assertEqual(shell(SAGE / "uninstall.sh", target).returncode, 0)

    def test_overlap_target_honors_caller_sandbox_and_preserves_prior_evidence(self) -> None:
        with sandbox() as raw:
            root = Path(raw); copied_sage = root / "source/sage"; copy_source(copied_sage)
            copied_tests = copied_sage / "evaluation/tests"; copied_tests.mkdir(parents=True)
            shutil.copy2(Path(__file__), copied_tests / "test_product_install.py")
            shutil.copy2(Path(__file__).with_name("support.py"), copied_tests / "support.py")
            old_target = copied_sage / "evaluation/sandboxes/integration-wave-r1-overlap-positive/target"
            old_target.mkdir(parents=True); sentinel = old_target / "prior-evidence.txt"; sentinel.write_bytes(b"preserve-me")
            caller = copied_sage / "evaluation/sandboxes/caller"; caller.mkdir(parents=True)
            environment = dict(os.environ); environment.update({"PYTHONDONTWRITEBYTECODE": "1", "SAGE_EVALUATION_SANDBOX": str(caller), "TMPDIR": str(caller)})
            result = subprocess.run(
                [sys.executable, "-m", "unittest", "test_product_install.InstallContractTests.test_default_source_allows_required_evaluation_sandbox_target", "-v"],
                cwd=copied_tests, env=environment, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(sentinel.read_bytes(), b"preserve-me")

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

    def test_uninstall_preflights_early_and_late_replaced_parents_before_removal(self) -> None:
        for parent_relative in ("skills/sage/references", "skills/sage/agents"):
            with self.subTest(parent=parent_relative), sandbox() as raw:
                root = Path(raw); target = root / "target"
                self.assertEqual(shell(SAGE / "install.sh", target).returncode, 0)
                receipt_path = target / "sage/receipt.json"; receipt_before = receipt_path.read_bytes(); receipt = json.loads(receipt_before)
                replaced = target / parent_relative; saved = root / parent_relative.replace("/", "-")
                replaced.rename(saved); replaced.write_bytes(b"user replacement")
                unchanged = {}
                for relative in receipt["installed_files"]:
                    candidate = target / relative
                    if candidate.is_file():
                        unchanged[relative] = candidate.read_bytes()
                result = shell(SAGE / "uninstall.sh", target)
                self.assertNotEqual(result.returncode, 0); self.assertEqual(result.stdout, "")
                self.assertFalse(json.loads(result.stderr)["ok"])
                self.assertEqual(receipt_path.read_bytes(), receipt_before)
                self.assertEqual(replaced.read_bytes(), b"user replacement")
                self.assertTrue(any(saved.rglob("*")))
                for relative, before in unchanged.items():
                    self.assertEqual((target / relative).read_bytes(), before, relative)

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
