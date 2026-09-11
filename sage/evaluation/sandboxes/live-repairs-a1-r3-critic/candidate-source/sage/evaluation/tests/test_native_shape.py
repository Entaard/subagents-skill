"""Native-v3 public-boundary regressions; no historical sandbox inputs."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import test_live_repairs
from support import EVALUATION, dump, sandbox


class NativeShapeTests(unittest.TestCase):
    def fixture(self, root):
        helper = test_live_repairs.NativeResultProtocolTests()
        manifest = root / "manifest.json"
        prepared = helper.invoke_pairing("prepare", str(EVALUATION / "cases/development-selection.json"),
                                         "--output", str(manifest))
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        control = helper.native_results(root, json.loads(manifest.read_text()))
        arm = control["pairs"][0]["treatment"]
        arm["routing"]["workers"] = [{"role": "builder", "requested_model": "gpt-5.6-sol",
                                     "effective_model": None}]
        arm["execution"]["evidence"].append({**arm["execution"]["evidence"][3], "id": "x"})
        arm["reported_tokens"] = 1  # Synthetic structural control, not measured usage.
        arm["usage_evidence_refs"] = ["x"]
        return helper, manifest, control

    def check(self, helper, manifest, root, value, accepted=False):
        result = helper.invoke_pairing("validate-native", str(dump(root / "input.json", value)),
                                       "--manifest", str(manifest))
        self.assertEqual(result.returncode, 0 if accepted else 2, result.stdout + result.stderr)
        parsed = json.loads(result.stdout if accepted else result.stderr)
        self.assertIs(parsed["ok"], accepted)
        if not accepted:
            self.assertIsInstance(parsed["error"], str)
            self.assertEqual(result.stdout, "")

    @staticmethod
    def change(control, path, value):
        changed = copy.deepcopy(control)
        if not path:
            return value
        target = changed
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        return changed

    def test_all_consumed_container_and_element_shapes(self):
        with sandbox() as raw:
            root = Path(raw); helper, manifest, control = self.fixture(root)
            arm = ("pairs", 0, "treatment")
            execution = arm + ("execution",)
            dimension = next(iter(control["pairs"][0]["treatment"]["scores"]))
            objects = [(), ("pairs", 0), arm, execution, execution + ("completion",),
                       execution + ("commands", 0), execution + ("evidence", 0),
                       arm + ("routing",), arm + ("routing", "workers", 0),
                       arm + ("checks", 0), arm + ("scores",), arm + ("scores", dimension),
                       arm + ("scorer",)]
            arrays = [("pairs",), execution + ("commands",), execution + ("evidence",),
                      arm + ("routing", "workers"), arm + ("checks",)]
            self.check(helper, manifest, root, control, accepted=True)
            for paths, opposite in ((objects, []), (arrays, {})):
                for path in paths:
                    for value in (None, True, 1, "x", opposite):
                        with self.subTest(path=path, value=value):
                            self.check(helper, manifest, root, self.change(control, path, value))

    def test_nonblank_identifiers_and_nullable_effective_models(self):
        with sandbox() as raw:
            root = Path(raw); helper, manifest, control = self.fixture(root)
            arm = ("pairs", 0, "treatment")
            paths = [arm + ("scorer", "id"), arm + ("routing", "workers", 0, "role"),
                     arm + ("routing", "workers", 0, "requested_model"),
                     arm + ("execution", "evidence", 0, "id"),
                     arm + ("execution", "commands", 0, "id")]
            paths += [arm + ("execution", name) for name in ("run_id", "started_at", "finished_at")]
            nullable = [arm + ("routing", "root_model_effective"),
                        arm + ("routing", "workers", 0, "effective_model")]
            for path in paths + nullable:
                for value in (True, 1, ["x"], {"x": True}, "", "  "):
                    with self.subTest(path=path, value=value):
                        self.check(helper, manifest, root, self.change(control, path, value))
            for path in nullable:
                for value in (None, "observed-model"):
                    self.check(helper, manifest, root, self.change(control, path, value), accepted=True)
            for path in paths:
                self.check(helper, manifest, root, self.change(control, path, None))

    def test_every_reference_branch_requires_string_array(self):
        with sandbox() as raw:
            root = Path(raw); helper, manifest, control = self.fixture(root)
            arm = ("pairs", 0, "treatment")
            dimension = next(iter(control["pairs"][0]["treatment"]["scores"]))
            paths = [arm + ("execution", "completion", "evidence_refs"),
                     arm + ("execution", "completion", "exit_evidence_refs"),
                     arm + ("execution", "commands", 0, "evidence_refs"),
                     arm + ("checks", 0, "evidence_refs"),
                     arm + ("scores", dimension, "evidence_refs"),
                     arm + ("scorer", "evidence_refs"), arm + ("operational_evidence_refs",),
                     arm + ("usage_evidence_refs",)]
            control["pairs"][0]["treatment"]["execution"]["completion"]["native_exit_code"] = 0
            control["pairs"][0]["treatment"]["execution"]["completion"]["exit_evidence_refs"] = ["x"]
            for path in paths:
                self.check(helper, manifest, root, self.change(control, path, ["x"]), accepted=True)
                for value in (None, True, 1, "x", {"x": True}, [True], [1], [{}], [[]], [""], ["  "]):
                    with self.subTest(path=path, value=value):
                        self.check(helper, manifest, root, self.change(control, path, value))
            for name in ("reported_tokens", "reported_money"):
                control["pairs"][0]["treatment"][name] = None
            control["pairs"][0]["treatment"]["usage_evidence_refs"] = []
            self.check(helper, manifest, root, control, accepted=True)


if __name__ == "__main__":
    unittest.main()
