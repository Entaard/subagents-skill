from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from support import KNOWLEDGE_CLI, complete_read_run, cues, dump, invoke, output, record, sandbox, write_log


class KnowledgeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(KNOWLEDGE_CLI.is_file(), "future product missing: sage/scripts/sage_knowledge.py")

    def source(self, root: Path, terminal: bool = True, unknown_effect: bool = False) -> Path:
        run = root / "source-1"
        rows = complete_read_run("source-1")
        if not terminal:
            rows = rows[:-1]
        if unknown_effect:
            rows[4]["payload"]["effect_status"] = "unknown"
            rows[-1]["payload"]["status"] = "stopped"
        write_log(run, rows)
        return run

    def proposal(self, root: Path, item: dict | None = None, action: str = "create") -> Path:
        return dump(root / f"proposal-{action}.json", {
            "action": action, "proposer": "proposer", "reviewer": "reviewer",
            "source_runs": [str(self.source(root))], "record": item or record(),
        })

    def create_generation(self, root: Path, generation: str = "g-1") -> Path:
        store = root / "store"; proposal = self.proposal(root)
        staged = invoke(KNOWLEDGE_CLI, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", generation, "--expected-current", "none")
        self.assertEqual(staged.returncode, 0, staged.stderr)
        activated = invoke(KNOWLEDGE_CLI, "activate", "--store-dir", str(store), "--generation-id", generation, "--expected-current", "none")
        self.assertEqual(activated.returncode, 0, activated.stderr)
        return store

    def test_stage_activate_and_retrieve_match_exact_generation_revision_and_cues(self) -> None:
        with sandbox() as raw:
            root = Path(raw); store = self.create_generation(root)
            cue_file = dump(root / "cues.json", cues(operation=["resume"], failure=["stale-snapshot"], environment=["fixture sandbox"]))
            result = invoke(KNOWLEDGE_CLI, "retrieve", "--store-dir", str(store), "--cues", str(cue_file), "--limit", "3")
            self.assertEqual(result.returncode, 0, result.stderr); value = output(result)
            self.assertEqual(value["retrieval_status"], "matched"); self.assertEqual(value["generation_id"], "g-1")
            self.assertEqual((value["matches"][0]["id"], value["matches"][0]["revision"]), ("k-1", 1))
            blocked = dump(root / "blocked.json", cues(operation=["resume"], environment=["remote-managed"]))
            value = output(invoke(KNOWLEDGE_CLI, "retrieve", "--store-dir", str(store), "--cues", str(blocked), "--limit", "3"))
            self.assertEqual(value["retrieval_status"], "no_match"); self.assertEqual(value["matches"], [])

    def test_active_and_unknown_effect_sources_are_rejected_without_store_mutation(self) -> None:
        with sandbox() as raw:
            root = Path(raw)
            for name, terminal, unknown in (("active", False, False), ("unknown", True, True)):
                source = self.source(root / name, terminal=terminal, unknown_effect=unknown)
                proposal = dump(root / name / "proposal.json", {"action": "create", "proposer": "proposer", "reviewer": "reviewer", "source_runs": [str(source)], "record": record()})
                store = root / name / "store"
                result = invoke(KNOWLEDGE_CLI, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none")
                self.assertEqual(result.returncode, 2); self.assertFalse((store / "current.json").exists()); self.assertFalse((store / "generations/g-1").exists())

    def test_failed_unsupported_or_nonindependent_refutation_is_rejected(self) -> None:
        with sandbox() as raw:
            root = Path(raw)
            variants = [record(refutation_outcome="failed"), record(refutation_outcome="unsupported"), record()]
            variants[-1]["refutation"]["actor"] = "proposer"
            for index, item in enumerate(variants):
                case = root / str(index); proposal = self.proposal(case, item)
                result = invoke(KNOWLEDGE_CLI, "stage", "--store-dir", str(case / "store"), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none")
                self.assertEqual(result.returncode, 2)

    def test_correction_preserves_stable_id_history_and_rollback(self) -> None:
        with sandbox() as raw:
            root = Path(raw); store = self.create_generation(root)
            changed = record(revision=2, prior_revision=1); changed["rule"] = "Corrected bounded rule."; changed["counterevidence"] = ["source-1:source-1-e-4"]
            proposal = self.proposal(root / "correction", changed, "correct")
            staged = invoke(KNOWLEDGE_CLI, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", "g-2", "--expected-current", "g-1")
            self.assertEqual(staged.returncode, 0, staged.stderr)
            self.assertTrue((store / "generations/g-1/records/k-1.json").is_file())
            activated = invoke(KNOWLEDGE_CLI, "activate", "--store-dir", str(store), "--generation-id", "g-2", "--expected-current", "g-1")
            self.assertEqual(activated.returncode, 0, activated.stderr)
            current = json.loads((store / "current.json").read_text()); self.assertEqual(current["generation_id"], "g-2")
            latest = json.loads((store / "generations/g-2/records/k-1.json").read_text()); self.assertEqual((latest["id"], latest["revision"], latest["prior_revision"]), ("k-1", 2, 1))
            rolled = invoke(KNOWLEDGE_CLI, "rollback", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "g-2")
            self.assertEqual(rolled.returncode, 0, rolled.stderr); self.assertTrue((store / "generations/g-2/records/k-1.json").is_file())

    def test_stale_generation_and_partial_generation_cannot_change_pointer(self) -> None:
        with sandbox() as raw:
            root = Path(raw); store = self.create_generation(root); before = (store / "current.json").read_bytes()
            proposal = self.proposal(root / "stale", record("k-2"))
            stale = invoke(KNOWLEDGE_CLI, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", "g-2", "--expected-current", "g-0")
            self.assertEqual(stale.returncode, 2); self.assertEqual((store / "current.json").read_bytes(), before)
            partial = store / "generations/g-partial"; partial.mkdir(parents=True); (partial / "index.json").write_text("{}", encoding="utf-8")
            activate = invoke(KNOWLEDGE_CLI, "activate", "--store-dir", str(store), "--generation-id", "g-partial", "--expected-current", "g-1")
            self.assertEqual(activate.returncode, 2); self.assertEqual((store / "current.json").read_bytes(), before)

    def test_malformed_duplicate_and_nonfinite_store_data_is_rejected(self) -> None:
        with sandbox() as raw:
            root = Path(raw); store = self.create_generation(root); self.assertEqual(invoke(KNOWLEDGE_CLI, "validate", "--store-dir", str(store)).returncode, 0)
            control = json.dumps(json.loads((store / "current.json").read_text()), separators=(",", ":"))
            mutations = [control.replace('"v":1', '"v":1,"v":1', 1), control.replace('"v":1', '"v":NaN', 1), control[:-1]]
            for payload in mutations:
                (store / "current.json").write_text(payload, encoding="utf-8"); result = invoke(KNOWLEDGE_CLI, "validate", "--store-dir", str(store))
                self.assertEqual(result.returncode, 2); self.assertEqual(json.loads(result.stderr)["code"], "invalid_json")
            (store / "current.json").write_text(control, encoding="utf-8"); self.assertEqual(invoke(KNOWLEDGE_CLI, "validate", "--store-dir", str(store)).returncode, 0)

    def test_missing_source_evidence_reference_is_rejected(self) -> None:
        with sandbox() as raw:
            root = Path(raw); item = record(); item["provenance"][0]["locator"] = "events.jsonl#source-1-e-999"
            proposal = self.proposal(root, item)
            result = invoke(KNOWLEDGE_CLI, "stage", "--store-dir", str(root / "store"), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none")
            self.assertEqual(result.returncode, 2); self.assertFalse((root / "store/generations/g-1").exists())

    def test_transferable_and_causal_support_gates_have_isolated_controls(self) -> None:
        with sandbox() as raw:
            root = Path(raw)
            for index, evidence_class in enumerate(("transferable_heuristic", "causal_guidance")):
                case = root / str(index); valid_record = record(evidence_class=evidence_class); valid = self.proposal(case / "valid", valid_record)
                result = invoke(KNOWLEDGE_CLI, "stage", "--store-dir", str(case / "valid-store"), "--proposal", str(valid), "--generation-id", "g-1", "--expected-current", "none")
                self.assertEqual(result.returncode, 0, result.stderr)
                invalid_record = copy.deepcopy(valid_record)
                missing = "contexts" if evidence_class == "transferable_heuristic" else "alternative_cause_dispositions"
                invalid_record["gate_evidence"].pop(missing)
                invalid = self.proposal(case / "invalid", invalid_record)
                result = invoke(KNOWLEDGE_CLI, "stage", "--store-dir", str(case / "invalid-store"), "--proposal", str(invalid), "--generation-id", "g-1", "--expected-current", "none")
                self.assertEqual(result.returncode, 2)

    def test_contested_refuted_retired_retrieval_policy(self) -> None:
        with sandbox() as raw:
            root = Path(raw); store = root / "store"; current = "none"
            for index, status in enumerate(("supported", "contested", "refuted", "retired"), 1):
                item = record(f"k-{index}", status=status); proposal = self.proposal(root / f"p-{index}", item)
                generation = f"g-{index}"; staged = invoke(KNOWLEDGE_CLI, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", generation, "--expected-current", current)
                self.assertEqual(staged.returncode, 0, staged.stderr); activated = invoke(KNOWLEDGE_CLI, "activate", "--store-dir", str(store), "--generation-id", generation, "--expected-current", current)
                self.assertEqual(activated.returncode, 0, activated.stderr); current = generation
            ordinary = dump(root / "ordinary.json", cues(operation=["resume"])); matches = output(invoke(KNOWLEDGE_CLI, "retrieve", "--store-dir", str(store), "--cues", str(ordinary), "--limit", "10"))["matches"]
            self.assertEqual([item["id"] for item in matches], ["k-1"])
            extended = cues(operation=["resume"]); extended["include_non_supported"] = True; extended_path = dump(root / "extended.json", extended)
            matches = output(invoke(KNOWLEDGE_CLI, "retrieve", "--store-dir", str(store), "--cues", str(extended_path), "--limit", "10"))["matches"]
            self.assertEqual({item["id"] for item in matches}, {"k-1", "k-2"})

    def test_corrupted_prior_generation_cannot_be_rollback_target(self) -> None:
        with sandbox() as raw:
            root = Path(raw); store = self.create_generation(root)
            proposal = self.proposal(root / "second", record("k-2")); self.assertEqual(invoke(KNOWLEDGE_CLI, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", "g-2", "--expected-current", "g-1").returncode, 0)
            self.assertEqual(invoke(KNOWLEDGE_CLI, "activate", "--store-dir", str(store), "--generation-id", "g-2", "--expected-current", "g-1").returncode, 0)
            control = invoke(KNOWLEDGE_CLI, "rollback", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "g-2")
            self.assertEqual(control.returncode, 0, control.stderr); self.assertEqual(invoke(KNOWLEDGE_CLI, "activate", "--store-dir", str(store), "--generation-id", "g-2", "--expected-current", "g-1").returncode, 0)
            record_path = store / "generations/g-1/records/k-1.json"; valid_record = json.loads(record_path.read_text()); valid_record["rule"] += " tampered"
            record_path.write_text(json.dumps(valid_record), encoding="utf-8"); before = (store / "current.json").read_bytes()
            rollback = invoke(KNOWLEDGE_CLI, "rollback", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "g-2")
            self.assertEqual(rollback.returncode, 2); self.assertEqual(json.loads(rollback.stderr)["code"], "generation_hash_mismatch"); self.assertEqual((store / "current.json").read_bytes(), before)


if __name__ == "__main__": unittest.main()
