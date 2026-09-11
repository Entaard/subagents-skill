from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SAGE = Path(__file__).resolve().parents[1]
KNOWLEDGE = SAGE / "scripts/sage_knowledge.py"
STATE = SAGE / "scripts/sage_state.py"
sys.path.insert(0, str(SAGE / "evaluation/tests"))

from support import complete_read_run, dump, record, write_log  # noqa: E402


def invoke(script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *arguments],
        cwd=SAGE.parent,
        text=True,
        capture_output=True,
        check=False,
    )


class KnowledgeRegressionTests(unittest.TestCase):
    def sandbox(self) -> tempfile.TemporaryDirectory[str]:
        root = Path(os.environ["SAGE_EVALUATION_SANDBOX"])
        root.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(dir=root)

    def proposal(self, root: Path, item: dict, action: str = "create") -> Path:
        source = root / "source-1"
        write_log(source, complete_read_run("source-1"))
        return dump(
            root / f"proposal-{action}.json",
            {
                "action": action,
                "proposer": "/root/proposer",
                "reviewer": "/root/reviewer",
                "source_runs": [str(source)],
                "record": {**item, "refutation": {**item["refutation"], "actor": "/root/refuter"}, "review": {**item["review"], "actor": "/root/reviewer"}},
            },
        )

    def test_empty_retrieval_round_trips_through_run_state_and_reserves_none(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw)
            cues = root / "cues.json"
            cues.write_text(
                '{"task":[],"domain":[],"artifact":[],"environment":[],"risk":[],"operation":[],"failure":[]}\n',
                encoding="utf-8",
            )

            retrieved = invoke(
                KNOWLEDGE,
                "retrieve",
                "--store-dir",
                str(root / "empty-store"),
                "--cues",
                str(cues),
                "--limit",
                "3",
            )
            self.assertEqual(retrieved.returncode, 0, retrieved.stderr)
            selection = json.loads(retrieved.stdout)
            self.assertEqual(
                selection,
                {
                    "generation_id": "none",
                    "cue_fingerprint": "1457ea49514f62f34f3abc8fd6b76ddd29d889d89bc5935c389b46a949428db8",
                    "retrieval_status": "no_match",
                    "matches": [],
                },
            )

            criteria = root / "criteria.json"
            criteria.write_text('[{"id":"c-1","text":"empty retrieval is recoverable"}]\n', encoding="utf-8")
            run = root / "run"
            self.assertEqual(
                invoke(STATE, "init", "--run-dir", str(run), "--run-id", "empty-retrieval", "--objective", "record no match", "--criteria", str(criteria)).returncode,
                0,
            )
            event = root / "selection.json"
            event.write_text(
                json.dumps(
                    {
                        "v": 1,
                        "event_id": "e-2",
                        "run_id": "empty-retrieval",
                        "seq": 2,
                        "at": "2026-09-07T00:00:02Z",
                        "actor": "root",
                        "type": "knowledge.selected",
                        "payload": {
                            "generation_id": selection["generation_id"],
                            "cue_fingerprint": selection["cue_fingerprint"],
                            "cues": json.loads(cues.read_text(encoding="utf-8")),
                            "matches": selection["matches"],
                            "retrieval_status": selection["retrieval_status"],
                        },
                    },
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            appended = invoke(STATE, "append", "--run-dir", str(run), "--event", str(event))
            self.assertEqual(appended.returncode, 0, appended.stderr)
            snapshot = invoke(STATE, "snapshot", "--run-dir", str(run), "--write")
            self.assertEqual(snapshot.returncode, 0, snapshot.stderr)
            self.assertEqual(
                json.loads((run / "snapshot.json").read_text(encoding="utf-8"))["knowledge_selection"],
                event_payload := json.loads(event.read_text(encoding="utf-8"))["payload"],
            )
            self.assertEqual(event_payload["generation_id"], "none")

            inclusive_cues = root / "inclusive-cues.json"
            inclusive_cues.write_text(
                '{"task":[],"domain":[],"artifact":[],"environment":[],"risk":[],"operation":[],"failure":[],"include_non_supported":true}\n',
                encoding="utf-8",
            )
            inclusive = invoke(
                KNOWLEDGE,
                "retrieve",
                "--store-dir",
                str(root / "empty-store"),
                "--cues",
                str(inclusive_cues),
                "--limit",
                "3",
            )
            self.assertEqual(inclusive.returncode, 0, inclusive.stderr)
            self.assertEqual(
                json.loads(inclusive.stdout)["cue_fingerprint"],
                "d0d9dcc7d7011aeb4df2c57e36cdb892f3643a972d63a1da6cb2c845f981d81c",
            )
            self.assertNotEqual(json.loads(inclusive.stdout)["cue_fingerprint"], selection["cue_fingerprint"])

            reserved = invoke(
                KNOWLEDGE,
                "stage",
                "--store-dir",
                str(root / "empty-store"),
                "--proposal",
                str(root / "missing-proposal.json"),
                "--generation-id",
                "none",
                "--expected-current",
                "none",
            )
            self.assertEqual(reserved.returncode, 2)
            self.assertEqual(json.loads(reserved.stderr)["code"], "invalid_generation_id")

    def test_activation_rejects_generation_staged_from_a_different_base(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw); store = root / "store"
            first = self.proposal(root / "first", record("k-1"))
            second = self.proposal(root / "second", record("k-2"))
            self.assertEqual(
                invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(first), "--generation-id", "g-1", "--expected-current", "none").returncode,
                0,
            )
            self.assertEqual(
                invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(second), "--generation-id", "g-2", "--expected-current", "none").returncode,
                0,
            )
            self.assertEqual(
                invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-2", "--expected-current", "none").returncode,
                0,
            )
            before = (store / "current.json").read_bytes()

            stale = invoke(
                KNOWLEDGE,
                "activate",
                "--store-dir",
                str(store),
                "--generation-id",
                "g-1",
                "--expected-current",
                "g-2",
            )
            self.assertEqual(stale.returncode, 2, stale.stderr)
            self.assertEqual(json.loads(stale.stderr)["code"], "stale_generation")
            self.assertEqual((store / "current.json").read_bytes(), before)

    def test_correction_after_rollback_cannot_reuse_revision_for_different_bytes(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw); store = root / "store"
            created = self.proposal(root / "created", record("k-1"))
            self.assertEqual(invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(created), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            self.assertEqual(invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)

            revision_a = record("k-1", revision=2, prior_revision=1)
            revision_a["rule"] = "First correction."
            revision_a["counterevidence"] = ["source-1:source-1-e-4"]
            proposal_a = self.proposal(root / "revision-a", revision_a, "correct")
            self.assertEqual(invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(proposal_a), "--generation-id", "g-2", "--expected-current", "g-1").returncode, 0)
            self.assertEqual(invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-2", "--expected-current", "g-1").returncode, 0)
            self.assertEqual(invoke(KNOWLEDGE, "rollback", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "g-2").returncode, 0)

            revision_b = record("k-1", revision=2, prior_revision=1)
            revision_b["rule"] = "Different correction using the same revision."
            revision_b["counterevidence"] = ["source-1:source-1-e-4"]
            proposal_b = self.proposal(root / "revision-b", revision_b, "correct")
            collision = invoke(
                KNOWLEDGE,
                "stage",
                "--store-dir",
                str(store),
                "--proposal",
                str(proposal_b),
                "--generation-id",
                "g-3",
                "--expected-current",
                "g-1",
            )
            self.assertEqual(collision.returncode, 2, collision.stderr)
            self.assertEqual(json.loads(collision.stderr)["code"], "revision_conflict")
            self.assertFalse((store / "generations/g-3").exists())
            self.assertEqual(json.loads((store / "current.json").read_text(encoding="utf-8"))["generation_id"], "g-1")

            revision_c = record("k-1", revision=3, prior_revision=2)
            revision_c["rule"] = "Safe correction after rollback without reactivating revision two."
            revision_c["counterevidence"] = ["source-1:source-1-e-4"]
            proposal_c = self.proposal(root / "revision-c", revision_c, "correct")
            repaired = invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(proposal_c), "--generation-id", "g-3", "--expected-current", "g-1")
            self.assertEqual(repaired.returncode, 0, repaired.stderr)
            self.assertEqual(invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-3", "--expected-current", "g-1").returncode, 0)
            self.assertEqual(json.loads((store / "generations/g-3/records/k-1.json").read_text(encoding="utf-8"))["revision"], 3)
            self.assertTrue((store / "generations/g-2/records/k-1.json").is_file())

    def test_generation_validation_rejects_extra_empty_paths(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw); store = root / "store"
            proposal = self.proposal(root / "proposal", record("k-1"))
            self.assertEqual(invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            self.assertEqual(invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            (store / "generations/g-1/unlisted-empty-directory").mkdir()

            result = invoke(KNOWLEDGE, "validate", "--store-dir", str(store))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(json.loads(result.stderr)["code"], "invalid_generation")

    def test_cli_argument_rejection_is_structured_json(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw)
            cues = root / "cues.json"
            cues.write_text('{"operation":[]}\n', encoding="utf-8")
            for arguments in (
                ("retrieve", "--store-dir", str(root / "store"), "--cues", str(cues), "--limit", "many"),
                ("validate", "--unknown-option"),
            ):
                result = invoke(KNOWLEDGE, *arguments)
                self.assertEqual(result.returncode, 2)
                error = json.loads(result.stderr)
                self.assertFalse(error["ok"])
                self.assertIn(error["code"], {"invalid_arguments", "invalid_limit"})
                self.assertEqual(result.stdout, "")

    def test_failed_and_stopped_terminal_sources_are_eligible(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw)
            for status in ("failed", "stopped"):
                case = root / status; source = case / "source-1"
                rows = complete_read_run("source-1"); rows[-1]["payload"]["status"] = status
                write_log(source, rows)
                item = record(f"k-{status}")
                item["refutation"]["actor"] = "/root/refuter"
                item["review"]["actor"] = "/root/reviewer"
                proposal = dump(
                    case / "proposal.json",
                    {"action": "create", "proposer": "/root/proposer", "reviewer": "/root/reviewer", "source_runs": [str(source)], "record": item},
                )
                result = invoke(KNOWLEDGE, "stage", "--store-dir", str(case / "store"), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none")
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_every_revision_action_preserves_prior_generation_and_retrieval_policy(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw)
            cases = (
                ("correct", "supported"),
                ("contest", "contested"),
                ("refute", "refuted"),
                ("retire", "retired"),
            )
            for action, status in cases:
                case = root / action; store = case / "store"
                initial = self.proposal(case / "initial", record("k-1"))
                staged = invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(initial), "--generation-id", "g-1", "--expected-current", "none")
                self.assertEqual(staged.returncode, 0, staged.stderr)
                self.assertEqual(invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)

                revised = record("k-1", revision=2, prior_revision=1, status=status)
                revised["rule"] = f"{action} revision."
                if action != "retire": revised["counterevidence"] = ["source-1:source-1-e-4"]
                if action == "retire":
                    revised["review"]["retirement_basis"] = "scope_obsolete"
                    revised["review"]["retirement_reason"] = "The declared fixture scope no longer exists."
                proposal = self.proposal(case / "revised", revised, action)
                staged = invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", "g-2", "--expected-current", "g-1")
                self.assertEqual(staged.returncode, 0, staged.stderr)
                activated = invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-2", "--expected-current", "g-1")
                self.assertEqual(activated.returncode, 0, activated.stderr)
                self.assertTrue((store / "generations/g-1/records/k-1.json").is_file())

                cues_path = case / "cues.json"
                cues_path.write_text('{"operation":["resume"],"include_non_supported":true}\n', encoding="utf-8")
                retrieved = invoke(KNOWLEDGE, "retrieve", "--store-dir", str(store), "--cues", str(cues_path), "--limit", "2")
                self.assertEqual(retrieved.returncode, 0, retrieved.stderr)
                matches = json.loads(retrieved.stdout)["matches"]
                if status in {"refuted", "retired"}: self.assertEqual(matches, [])
                else: self.assertEqual((matches[0]["id"], matches[0]["revision"], matches[0]["status"]), ("k-1", 2, status))

    def test_disuse_is_not_an_accepted_retirement_basis(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw); store = root / "store"
            initial = self.proposal(root / "initial", record("k-1"))
            self.assertEqual(invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(initial), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            self.assertEqual(invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            retired = record("k-1", revision=2, prior_revision=1, status="retired")
            retired["review"]["retirement_basis"] = "disuse"
            retired["review"]["retirement_reason"] = "It was not selected recently."
            proposal = self.proposal(root / "retired", retired, "retire")
            result = invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", "g-2", "--expected-current", "g-1")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stderr)["code"], "invalid_record")
            self.assertFalse((store / "generations/g-2").exists())

    def test_activation_rejects_rehashed_generation_with_failed_refutation(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw); store = root / "store"
            proposal = self.proposal(root / "proposal", record("k-1"))
            self.assertEqual(invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            generation = store / "generations/g-1"
            record_path = generation / "records/k-1.json"
            item = json.loads(record_path.read_text(encoding="utf-8")); item["refutation"]["outcome"] = "failed"
            record_path.write_text(json.dumps(item, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            manifest_path = generation / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in manifest["files"]:
                if entry["path"] == "records/k-1.json": entry["sha256"] = hashlib.sha256(record_path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

            activated = invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "none")
            self.assertEqual(activated.returncode, 2, activated.stderr)
            self.assertEqual(json.loads(activated.stderr)["code"], "invalid_record")
            self.assertFalse((store / "current.json").exists())

    def test_store_validation_checks_global_lineage_and_parent_references(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw); store = root / "collision-store"
            initial = self.proposal(root / "initial", record("k-1"))
            self.assertEqual(invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(initial), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            self.assertEqual(invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            second = self.proposal(root / "second", record("k-2"))
            self.assertEqual(invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(second), "--generation-id", "g-2", "--expected-current", "g-1").returncode, 0)
            generation = store / "generations/g-2"; record_path = generation / "records/k-1.json"
            item = json.loads(record_path.read_text(encoding="utf-8")); item["rule"] = "Conflicting bytes for retained k-1 revision one."
            record_path.write_text(json.dumps(item, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            manifest_path = generation / "manifest.json"; manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in manifest["files"]:
                if entry["path"] == "records/k-1.json": entry["sha256"] = hashlib.sha256(record_path.read_bytes()).hexdigest()
            manifest_path.write_text(json.dumps(manifest, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            collision = invoke(KNOWLEDGE, "validate", "--store-dir", str(store))
            self.assertEqual(collision.returncode, 2, collision.stderr)
            self.assertEqual(json.loads(collision.stderr)["code"], "revision_conflict")

            dangling_store = root / "dangling-store"
            proposal = self.proposal(root / "dangling", record("k-3"))
            self.assertEqual(invoke(KNOWLEDGE, "stage", "--store-dir", str(dangling_store), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            dangling_manifest_path = dangling_store / "generations/g-1/manifest.json"
            dangling_manifest = json.loads(dangling_manifest_path.read_text(encoding="utf-8")); dangling_manifest["parent_generation_id"] = "g-missing"
            dangling_manifest_path.write_text(json.dumps(dangling_manifest, allow_nan=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            dangling = invoke(KNOWLEDGE, "validate", "--store-dir", str(dangling_store))
            self.assertEqual(dangling.returncode, 2, dangling.stderr)
            self.assertEqual(json.loads(dangling.stderr)["code"], "invalid_generation")

    def test_all_gate_references_and_exact_external_locators_are_closed(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw)

            missing = record("k-missing", evidence_class="transferable_heuristic")
            missing["gate_evidence"].pop("corroboration")
            missing["gate_evidence"]["comparison"] = ["source-1:missing-evidence"]
            missing_proposal = self.proposal(root / "missing-comparison", missing)
            rejected = invoke(
                KNOWLEDGE,
                "stage",
                "--store-dir",
                str(root / "missing-comparison/store"),
                "--proposal",
                str(missing_proposal),
                "--generation-id",
                "g-1",
                "--expected-current",
                "none",
            )
            self.assertEqual(rejected.returncode, 2, rejected.stderr)
            self.assertEqual(json.loads(rejected.stderr)["code"], "invalid_reference")
            self.assertFalse((root / "missing-comparison/store/generations/g-1").exists())

            for field in ("comparison", "corroboration"):
                item = record(f"k-valid-{field}", evidence_class="transferable_heuristic")
                item["gate_evidence"].pop("corroboration")
                item["gate_evidence"][field] = ["source-1:source-1-e-6"]
                proposal = self.proposal(root / f"valid-{field}", item)
                staged = invoke(
                    KNOWLEDGE,
                    "stage",
                    "--store-dir",
                    str(root / f"valid-{field}/store"),
                    "--proposal",
                    str(proposal),
                    "--generation-id",
                    "g-1",
                    "--expected-current",
                    "none",
                )
                self.assertEqual(staged.returncode, 0, staged.stderr)

            external_case = root / "external"; source = external_case / "source-1"
            rows = complete_read_run("source-1")
            recorded_locator = "https://recorded.invalid/report#section"
            rows[3]["payload"]["locator"] = recorded_locator
            rows[3]["payload"]["sha256"] = "a" * 64
            write_log(source, rows)
            valid_external = record("k-external")
            valid_external["provenance"] = [{"run_id": "source-1", "locator": recorded_locator}]
            valid_external["refutation"]["evidence"] = [f"source-1:{recorded_locator}"]
            valid_external["refutation"]["actor"] = "/root/refuter"
            valid_external["review"]["actor"] = "/root/reviewer"
            valid_proposal = dump(
                external_case / "valid.json",
                {"action": "create", "proposer": "/root/proposer", "reviewer": "/root/reviewer", "source_runs": [str(source)], "record": valid_external},
            )
            accepted = invoke(KNOWLEDGE, "stage", "--store-dir", str(external_case / "valid-store"), "--proposal", str(valid_proposal), "--generation-id", "g-1", "--expected-current", "none")
            self.assertEqual(accepted.returncode, 0, accepted.stderr)

            alias = record("k-alias")
            unrecorded = "https://unrecorded.invalid/report#source-1-e-6"
            alias["provenance"] = [{"run_id": "source-1", "locator": unrecorded}]
            alias["refutation"]["evidence"] = [f"source-1:{unrecorded}"]
            alias["refutation"]["actor"] = "/root/refuter"
            alias["review"]["actor"] = "/root/reviewer"
            alias_proposal = dump(
                external_case / "alias.json",
                {"action": "create", "proposer": "/root/proposer", "reviewer": "/root/reviewer", "source_runs": [str(source)], "record": alias},
            )
            rejected_alias = invoke(KNOWLEDGE, "stage", "--store-dir", str(external_case / "alias-store"), "--proposal", str(alias_proposal), "--generation-id", "g-1", "--expected-current", "none")
            self.assertEqual(rejected_alias.returncode, 2, rejected_alias.stderr)
            self.assertEqual(json.loads(rejected_alias.stderr)["code"], "invalid_reference")

    def test_correct_cannot_bypass_intentional_retirement_metadata(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw); store = root / "store"
            initial = self.proposal(root / "initial", record("k-1"))
            self.assertEqual(invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(initial), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)
            self.assertEqual(invoke(KNOWLEDGE, "activate", "--store-dir", str(store), "--generation-id", "g-1", "--expected-current", "none").returncode, 0)

            bypass = record("k-1", revision=2, prior_revision=1, status="retired")
            bypass["counterevidence"] = ["source-1:source-1-e-4"]
            bypass_proposal = self.proposal(root / "bypass", bypass, "correct")
            rejected = invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(bypass_proposal), "--generation-id", "g-2", "--expected-current", "g-1")
            self.assertEqual(rejected.returncode, 2, rejected.stderr)
            self.assertEqual(json.loads(rejected.stderr)["code"], "invalid_transition")
            self.assertFalse((store / "generations/g-2").exists())

            proper = record("k-1", revision=2, prior_revision=1, status="retired")
            proper["review"]["retirement_basis"] = "scope_obsolete"
            proper["review"]["retirement_reason"] = "The declared fixture scope no longer exists."
            proper_proposal = self.proposal(root / "proper", proper, "retire")
            accepted = invoke(KNOWLEDGE, "stage", "--store-dir", str(store), "--proposal", str(proper_proposal), "--generation-id", "g-2", "--expected-current", "g-1")
            self.assertEqual(accepted.returncode, 0, accepted.stderr)

            imported = record("k-historical", status="retired")
            imported_proposal = self.proposal(root / "imported", imported, "create")
            imported_stage = invoke(KNOWLEDGE, "stage", "--store-dir", str(root / "import-store"), "--proposal", str(imported_proposal), "--generation-id", "g-1", "--expected-current", "none")
            self.assertEqual(imported_stage.returncode, 0, imported_stage.stderr)

    def test_record_chronology_uses_parsed_utc_instants(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw)
            cases = (
                ("later-fraction", "2026-09-07T00:00:00Z", "2026-09-07T00:00:00.500Z", 0),
                ("earlier-fraction", "2026-09-07T00:00:00.500Z", "2026-09-07T00:00:00Z", 2),
                ("equal-fraction", "2026-09-07T00:00:00.5Z", "2026-09-07T00:00:00.500000Z", 0),
            )
            for name, created, reviewed, expected in cases:
                item = record(f"k-{name}")
                item["created_at"] = created; item["reviewed_at"] = reviewed
                proposal = self.proposal(root / name, item)
                result = invoke(KNOWLEDGE, "stage", "--store-dir", str(root / name / "store"), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none")
                self.assertEqual(result.returncode, expected, result.stderr)
                if expected == 2: self.assertEqual(json.loads(result.stderr)["code"], "invalid_record")

    def test_record_chronology_preserves_all_accepted_fraction_digits(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw)
            cases = (
                ("later-high-precision", "2026-09-07T00:00:00.5000001Z", "2026-09-07T00:00:00.5000002Z", 0),
                ("equal-high-precision", "2026-09-07T00:00:00.500000100Z", "2026-09-07T00:00:00.5000001Z", 0),
                ("earlier-high-precision", "2026-09-07T00:00:00.5000002Z", "2026-09-07T00:00:00.5000001Z", 2),
            )
            for name, created, reviewed, expected in cases:
                with self.subTest(name=name):
                    item = record(f"k-{name}")
                    item["created_at"] = created; item["reviewed_at"] = reviewed
                    proposal = self.proposal(root / name, item)
                    result = invoke(KNOWLEDGE, "stage", "--store-dir", str(root / name / "store"), "--proposal", str(proposal), "--generation-id", "g-1", "--expected-current", "none")
                    self.assertEqual(result.returncode, expected, result.stderr)
                    if expected == 2: self.assertEqual(json.loads(result.stderr)["code"], "invalid_record")

    def test_dangling_pointer_is_not_an_empty_store(self) -> None:
        with self.sandbox() as raw:
            root = Path(raw)
            empty = invoke(KNOWLEDGE, "validate", "--store-dir", str(root / "empty-store"))
            self.assertEqual(empty.returncode, 0, empty.stderr)
            self.assertEqual(json.loads(empty.stdout), {"current": "none", "generation_count": 0, "ok": True})

            store = root / "dangling-store"; store.mkdir()
            pointer = store / "current.json"; pointer.symlink_to("missing.json")
            rejected = invoke(KNOWLEDGE, "validate", "--store-dir", str(store))
            self.assertEqual(rejected.returncode, 2, rejected.stderr)
            self.assertEqual(json.loads(rejected.stderr)["code"], "invalid_store")
            self.assertTrue(pointer.is_symlink())


if __name__ == "__main__":
    unittest.main()
