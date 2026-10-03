"""Caught install failures restore receipt-owned preimages without masking user edits."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
from unittest.mock import patch

SAGE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sage_lifecycle_recovery", SAGE / "scripts/sage-lifecycle.py")
lifecycle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lifecycle)


def inventory(root):
    return {str(path.relative_to(root)): (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
            for path in root.rglob("*") if path.is_file()}


class LifecycleRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("SAGE_EVALUATION_SANDBOX"))
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        shutil.copytree(SAGE / "skills", self.source / "skills")
        (self.source / "scripts").mkdir()
        for name in lifecycle.HELPERS.values():
            shutil.copy2(SAGE / name, self.source / name)
        self.target = self.root / "target"
        self.first = "sage/bin/sage_knowledge.py"
        self.second = "sage/bin/sage_state.py"

    def prepare_update(self):
        obsolete = self.source / "skills/sage/references/retired.md"
        obsolete.write_bytes(b"retired old bytes")
        lifecycle.install(self.source, self.target)
        for relative, mode in [(self.first, 0o700), (lifecycle.RECEIPT, 0o640),
                               ("skills/sage/references/retired.md", 0o600)]:
            (self.target / relative).chmod(mode)
        for relative in ["skills/sage/user-note.txt", "sage/knowledge/keep.json", "sage/runs/keep.jsonl"]:
            path = self.target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"unrelated user/runtime bytes")
        obsolete.unlink()
        for name in lifecycle.HELPERS.values():
            path = self.source / name
            path.write_bytes(path.read_bytes() + b"\n# changed fixture\n")
        return inventory(self.target)

    def failing_write(self, relative, *, after=False):
        original = lifecycle.atomic_write
        fired = False

        def write(path, data, mode=0o644):
            nonlocal fired
            if path == self.target / relative and not fired:
                fired = True
                if after:
                    original(path, data, mode)
                raise OSError("injected write failure")
            return original(path, data, mode)
        return write

    def assert_retry(self):
        result = lifecycle.install(self.source, self.target)
        self.assertTrue(result["ok"])
        receipt = lifecycle.load_receipt(self.target)
        for relative, (_, data) in lifecycle.source_files(self.source).items():
            self.assertEqual((self.target / relative).read_bytes(), data)
            self.assertEqual(receipt["files"][relative]["source_sha256"], lifecycle.digest(data))

    def test_update_write_failure_restores_bytes_modes_and_receipt_then_retries(self):
        before = self.prepare_update()
        with patch.object(lifecycle, "atomic_write", self.failing_write(self.second)):
            with self.assertRaisesRegex(OSError, "injected write failure"):
                lifecycle.install(self.source, self.target)
        self.assertEqual(inventory(self.target), before)
        self.assert_retry()

    def test_retirement_failure_restores_deleted_preimage_then_retries(self):
        before = self.prepare_update()
        retired = self.target / "skills/sage/references/retired.md"
        original = Path.unlink
        fired = False

        def unlink(path, *args, **kwargs):
            nonlocal fired
            result = original(path, *args, **kwargs)
            if path == retired and not fired:
                fired = True
                raise OSError("injected retirement failure")
            return result

        with patch.object(Path, "unlink", unlink):
            with self.assertRaisesRegex(OSError, "injected retirement failure"):
                lifecycle.install(self.source, self.target)
        self.assertEqual(inventory(self.target), before)
        self.assert_retry()

    def test_receipt_failure_after_replacement_restores_entire_package(self):
        before = self.prepare_update()
        with patch.object(lifecycle, "atomic_write", self.failing_write(lifecycle.RECEIPT, after=True)):
            with self.assertRaisesRegex(OSError, "injected write failure"):
                lifecycle.install(self.source, self.target)
        self.assertEqual(inventory(self.target), before)
        self.assert_retry()

    def test_fresh_install_failure_removes_its_created_files_and_directories(self):
        self.target = self.root / "new-parent" / "target"
        with patch.object(lifecycle, "atomic_write", self.failing_write(self.second)):
            with self.assertRaises(OSError):
                lifecycle.install(self.source, self.target)
        self.assertFalse((self.root / "new-parent").exists())
        self.assert_retry()

    def test_failed_install_preserves_existing_unowned_tree(self):
        note = self.target / "sage/knowledge/keep.json"
        note.parent.mkdir(parents=True)
        note.write_bytes(b"runtime")
        before = inventory(self.target)
        with patch.object(lifecycle, "atomic_write", self.failing_write(self.second)):
            with self.assertRaises(OSError):
                lifecycle.install(self.source, self.target)
        self.assertEqual(inventory(self.target), before)
        self.assert_retry()

    def test_source_change_after_capture_cannot_poison_receipt_hashes(self):
        original = lifecycle.source_files
        captured = {}

        def capture(root):
            result = original(root)
            captured.update(result)
            path = self.source / "scripts/sage_state.py"
            path.write_bytes(path.read_bytes() + b"\n# changed after capture\n")
            return result

        with patch.object(lifecycle, "source_files", capture):
            lifecycle.install(self.source, self.target)
        receipt = lifecycle.load_receipt(self.target)
        self.assertEqual((self.target / self.second).read_bytes(), captured[self.second][1])
        self.assertEqual(receipt["files"][self.second]["source_sha256"], lifecycle.digest(captured[self.second][1]))
        self.assert_retry()

    def test_rollback_failure_reports_retained_exact_preimages(self):
        before = self.prepare_update()
        original = lifecycle.atomic_write
        old_data = before[self.first][0]

        def write(path, data, mode=0o644):
            if path == self.target / self.second:
                raise OSError("forward failure")
            if path == self.target / self.first and data == old_data:
                raise OSError("rollback failure")
            return original(path, data, mode)

        stderr = io.StringIO()
        argv = ["sage-lifecycle.py", "install", "--source-root", str(self.source), "--target-root", str(self.target)]
        with patch.object(lifecycle, "atomic_write", write), patch("sys.argv", argv), contextlib.redirect_stderr(stderr):
            self.assertEqual(lifecycle.main(), 2)
        response = json.loads(stderr.getvalue())
        recovery = Path(response["recovery_dir"])
        self.addCleanup(shutil.rmtree, recovery)
        self.assertFalse(recovery.resolve().is_relative_to(self.target.resolve()))
        self.assertEqual(stat.S_IMODE(recovery.stat().st_mode), 0o700)
        manifest = json.loads((recovery / "manifest.json").read_text())
        for relative, row in manifest["files"].items():
            expected = before.get(relative)
            if expected is None:
                self.assertIsNone(row["before"])
            else:
                self.assertEqual((recovery / row["before"]["blob"]).read_bytes(), expected[0])
                self.assertEqual(row["before"]["mode"], expected[1])
                self.assertEqual(row["before"]["sha256"], lifecycle.digest(expected[0]))
        self.assertIn("rollback failure", response["message"])
        self.assertEqual((self.target / lifecycle.RECEIPT).read_bytes(), before[lifecycle.RECEIPT][0])

    def test_concurrent_user_edit_is_preserved_with_recovery_evidence(self):
        before = self.prepare_update()
        original = lifecycle.atomic_write

        def write(path, data, mode=0o644):
            if path == self.target / self.second:
                (self.target / self.first).write_bytes(b"concurrent user edit")
                raise OSError("forward failure after user edit")
            return original(path, data, mode)

        with patch.object(lifecycle, "atomic_write", write):
            with self.assertRaises(lifecycle.InstallRecoveryError) as caught:
                lifecycle.install(self.source, self.target)
        self.addCleanup(shutil.rmtree, caught.exception.recovery_dir)
        self.assertEqual((self.target / self.first).read_bytes(), b"concurrent user edit")
        self.assertIn("preserved divergent path", str(caught.exception))
        self.assertEqual((self.target / lifecycle.RECEIPT).read_bytes(), before[lifecycle.RECEIPT][0])

    def test_replaced_target_root_is_not_followed_during_recovery(self):
        self.prepare_update()
        original = lifecycle.atomic_write
        outside = self.root / "outside"
        shutil.copytree(self.target, outside)
        outside_before = inventory(outside)

        def write(path, data, mode=0o644):
            if path == self.target / self.second:
                self.target.rename(self.root / "moved-target")
                self.target.symlink_to(outside, target_is_directory=True)
                raise OSError("forward failure after root replacement")
            return original(path, data, mode)

        with patch.object(lifecycle, "atomic_write", write):
            with self.assertRaises(lifecycle.InstallRecoveryError) as caught:
                lifecycle.install(self.source, self.target)
        self.addCleanup(shutil.rmtree, caught.exception.recovery_dir)
        self.assertEqual(inventory(outside), outside_before)
        self.assertTrue(self.target.is_symlink())


if __name__ == "__main__":
    unittest.main()
