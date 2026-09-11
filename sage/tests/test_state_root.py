"""Public workflow regressions for shared runtime roots and historical discovery."""
from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SAGE / "evaluation/tests"))
from support import complete_read_run, cues, dump, event, opened, record, task, write_log


class StateRootTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.env = dict(os.environ, SAGE_STATE_ROOT=str(self.base / "central"))
        self.state = SAGE / "scripts/sage_state.py"
        self.knowledge = SAGE / "scripts/sage_knowledge.py"

    def cli(self, script, *args, code=0, cwd=None, env=None):
        p = subprocess.run([sys.executable, "-B", str(script), *map(str, args)],
                           cwd=cwd or self.base, env=env or self.env,
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, code, p.stderr or p.stdout)
        return json.loads(p.stdout if code == 0 else p.stderr)

    def test_two_projects_share_history_and_promotion_store(self):
        for name in ("project-a", "project-b"):
            project = self.base / name
            project.mkdir()
            criteria = dump(project / "criteria.json", [{"id": "c-1", "text": "check"}])
            value = self.cli(self.state, "init", "--run-id", name, "--objective", "check", "--criteria", criteria, cwd=project)
            self.assertEqual(Path(value["run_dir"]), self.base / "central/runs" / name)
            self.assertTrue(value["discoverable"])
            self.assertFalse((project / ".sage-state").exists())
            rows = complete_read_run()
            for row in rows: row["run_id"] = name
            wave = project / "wave.jsonl"
            wave.write_text("".join(json.dumps(row) + "\n" for row in rows[1:]))
            self.cli(self.state, "append", "--run-id", name, "--events", wave, cwd=project)
            self.cli(self.state, "snapshot", "--run-id", name, "--write", cwd=project)
            self.cli(self.state, "validate", "--run-id", name, "--terminal", cwd=project)
        listing = self.cli(self.state, "list-runs")
        self.assertEqual({x["run_id"] for x in listing["runs"]}, {"project-a", "project-b"})
        self.assertEqual({x["status"] for x in listing["runs"]}, {"completed"})
        self.assertTrue(all(x["eligible"] for x in listing["runs"]))
        cue = dump(self.base / "cues.json", cues())
        retrieval = self.cli(self.knowledge, "retrieve", "--cues", cue, "--limit", "3")
        self.assertEqual(Path(retrieval["store_dir"]), self.base / "central/knowledge")
        self.assertEqual(retrieval["retrieval_status"], "no_match")

    def test_legacy_target_is_visible_and_ambiguous_or_invalid_targets_reject(self):
        criteria = dump(self.base / "criteria.json", [{"id": "c-1", "text": "check"}])
        legacy = self.base / "isolated"
        value = self.cli(self.state, "init", "--run-dir", legacy, "--run-id", "old", "--objective", "check", "--criteria", criteria)
        self.assertFalse(value["discoverable"])
        self.assertIn("register", value["warning"])
        self.assertEqual(self.cli(self.state, "list-runs")["runs"], [])
        self.cli(self.state, "validate", "--run-dir", legacy, "--state-root", self.base / "central", code=2)
        self.cli(self.knowledge, "validate", "--store-dir", self.base / "store", "--state-root", self.base / "central", code=2)
        self.cli(self.state, "init", "--run-id", "../escape", "--objective", "check", "--criteria", criteria, code=2)
        bad_root = self.base / "not-directory"
        bad_root.write_text("keep")
        self.cli(self.state, "paths", "--state-root", bad_root, code=2)
        self.cli(self.state, "paths", "--state-root", "", code=2)
        self.assertEqual(bad_root.read_text(), "keep")

    def test_mismatched_or_duplicate_canonical_ids_fail_without_mutation(self):
        run = self.base / "central/runs/one"
        log = write_log(run, complete_read_run("two"))
        before = log.read_bytes()
        self.assertEqual(self.cli(self.state, "list-runs")["runs"][0]["status"], "quarantined")
        self.cli(self.state, "snapshot", "--run-id", "one", "--write", code=2)
        self.assertEqual(log.read_bytes(), before)
        self.assertFalse((run / "snapshot.json").exists())
        source = self.base / "legacy"
        write_log(source, complete_read_run("duplicate"))
        self.cli(self.state, "register", "--run-dir", source)
        write_log(self.base / "central/runs/duplicate", complete_read_run("duplicate"))
        duplicated = [x for x in self.cli(self.state, "list-runs")["runs"] if x["run_id"] == "duplicate"]
        self.assertEqual(len(duplicated), 2)
        self.assertTrue(all(x["status"] == "quarantined" for x in duplicated))

    def test_missing_or_malformed_legacy_references_are_visible(self):
        source = self.base / "legacy"
        log = write_log(source, complete_read_run("a"))
        self.cli(self.state, "register", "--run-dir", source)
        log.rename(source / "preserved-events.jsonl")
        refs = self.base / "central/run-references"
        dump(refs / "b.json", {"v": 1, "run_id": "b", "run_dir": [], "events_sha256": "x"})
        (refs / "c.json").symlink_to(refs / "missing.json")
        found = self.cli(self.state, "list-runs")["runs"]
        self.assertEqual(len(found), 3)
        self.assertTrue(all(x["status"] == "quarantined" for x in found))
        self.assertTrue((source / "preserved-events.jsonl").is_file())

    def test_resolution_precedence_and_empty_reads_do_not_create_state(self):
        env = dict(self.env, CODEX_HOME=str(self.base / "codex-config"))
        root = self.cli(self.state, "paths", env=env)
        self.assertEqual(root["state_root"], str(self.base / "central"))
        self.assertEqual(root["root_source"], "SAGE_STATE_ROOT")
        del env["SAGE_STATE_ROOT"]
        root = self.cli(self.state, "paths", env=env)
        self.assertEqual(root["state_root"], str(self.base / "codex-config/sage"))
        root = self.cli(self.state, "paths", "--state-root", self.base / "override", env=env)
        self.assertEqual(root["root_source"], "argument")
        listing = self.cli(self.state, "list-runs")
        self.assertEqual(listing["runs"], [])
        self.assertFalse(listing["root_exists"])
        self.assertFalse((self.base / "central").exists())
        env["SAGE_STATE_ROOT"] = "relative-root"
        self.cli(self.state, "paths", env=env, code=2)

    def test_legacy_registration_is_nondestructive_bound_and_idempotent(self):
        source = self.base / "reviews/old/run"
        log = write_log(source, complete_read_run("source-1"))
        before = log.read_bytes()
        registered = self.cli(self.state, "register", "--run-dir", source)
        self.assertEqual(registered["run_id"], "source-1")
        self.assertEqual(self.cli(self.state, "register", "--run-dir", source), registered)
        listing = self.cli(self.state, "list-runs")
        self.assertEqual(listing["runs"][0]["run_dir"], str(source))
        self.assertEqual(listing["runs"][0]["status"], "completed")
        self.assertTrue(listing["runs"][0]["eligible"])
        self.assertEqual(log.read_bytes(), before)
        self.cli(self.state, "validate", "--run-id", "source-1", "--terminal")
        log.write_bytes(before + b"\n")
        self.assertEqual(self.cli(self.state, "list-runs")["runs"][0]["status"], "quarantined")
        self.cli(self.state, "validate", "--run-id", "source-1", code=2)
        self.cli(self.state, "register", "--run-dir", source, code=2)

    def test_discovery_reports_invalid_active_missing_and_paginated_sources(self):
        root = self.base / "central/runs"
        write_log(root / "a", complete_read_run("a"))
        write_log(root / "b", complete_read_run("b")[:-1])
        bad = root / "c"
        bad.mkdir()
        (bad / "events.jsonl").write_text("not json")
        first = self.cli(self.state, "list-runs", "--limit", "2")
        self.assertEqual(len(first["runs"]), 2)
        self.assertEqual(first["next_offset"], 2)
        second = self.cli(self.state, "list-runs", "--limit", "2", "--offset", "2")
        self.assertIsNone(second["next_offset"])
        self.assertEqual(second["runs"][0]["status"], "quarantined")
        self.assertFalse(second["runs"][0]["eligible"])
        self.cli(self.state, "register", "--run-dir", root / "b", code=2)
        self.cli(self.state, "list-runs", "--limit", "0", code=2)
        self.cli(self.state, "list-runs", "--offset", "-1", code=2)

    def test_id_collision_never_hides_or_overwrites_history(self):
        source = self.base / "reviews/run"
        log = write_log(source, complete_read_run("same"))
        self.cli(self.state, "register", "--run-dir", source)
        duplicate = self.base / "other/run"
        write_log(duplicate, complete_read_run("same"))
        self.cli(self.state, "register", "--run-dir", duplicate, code=2)
        criteria = dump(self.base / "criteria.json", [{"id": "c-1", "text": "check"}])
        self.cli(self.state, "init", "--run-id", "same", "--objective", "check", "--criteria", criteria, code=2)
        self.assertFalse((self.base / "central/runs/same").exists())
        self.assertEqual(log.read_bytes(), (duplicate / "events.jsonl").read_bytes())

    def test_canonical_empty_reservation_rejects_and_explicit_canonical_metadata_agrees(self):
        criteria = dump(self.base / "criteria.json", [{"id": "c-1", "text": "check"}])
        reserved = self.base / "central/runs/reserved"
        reserved.mkdir(parents=True)
        self.cli(self.state, "init", "--run-id", "reserved", "--objective", "check", "--criteria", criteria, code=2)
        self.assertEqual(list(reserved.iterdir()), [])
        regular = reserved.parent / "regular"
        regular.write_text("keep")
        linked = reserved.parent / "linked"
        external = self.base / "external"
        external.mkdir()
        linked.symlink_to(external, target_is_directory=True)
        for target in (regular, linked):
            self.cli(self.state, "init", "--run-id", target.name, "--objective", "check", "--criteria", criteria, code=2)
            self.cli(self.state, "init", "--run-dir", target, "--run-id", target.name, "--objective", "check", "--criteria", criteria, code=2)
        self.assertEqual(regular.read_text(), "keep")
        self.assertEqual(list(external.iterdir()), [])
        value = self.cli(self.state, "init", "--run-dir", self.base / "central/runs/explicit", "--run-id", "explicit", "--objective", "check", "--criteria", criteria)
        self.assertTrue(value["discoverable"])
        self.assertNotIn("warning", value)
        self.assertTrue(any(x["run_id"] == "explicit" and x["status"] == "active" for x in self.cli(self.state, "list-runs")["runs"]))

    def test_symlinked_knowledge_namespace_rejects_before_access(self):
        root = self.base / "central"
        root.mkdir()
        external = self.base / "external"
        external.mkdir()
        (root / "knowledge").symlink_to(external, target_is_directory=True)
        cue = dump(self.base / "cues.json", cues())
        proposal = dump(self.base / "proposal.json", {})
        for args in (("validate",), ("retrieve", "--cues", cue, "--limit", "3"),
                     ("stage", "--proposal", proposal, "--generation-id", "g-1", "--expected-current", "none")):
            self.cli(self.knowledge, *args, code=2)
        self.cli(self.knowledge, "validate", "--store-dir", root / "knowledge", code=2)
        self.assertEqual(list(external.iterdir()), [])

    def test_root_stage_cannot_bypass_quarantined_reference_or_stale_selection(self):
        source = self.base / "legacy"
        rows = complete_read_run("source-1")
        write_log(source, rows)
        self.cli(self.state, "register", "--run-dir", source)
        selected = self.cli(self.state, "list-runs")["runs"][0]
        proposal = {"action": "create", "proposer": "proposer", "reviewer": "reviewer", "source_runs": [str(source)], "record": record()}
        rows[0]["payload"]["objective"] = "changed after review"
        write_log(source, rows)
        self.assertEqual(self.cli(self.state, "list-runs")["runs"][0]["status"], "quarantined")
        proposal_path = dump(self.base / "proposal.json", proposal)
        self.cli(self.knowledge, "stage", "--proposal", proposal_path, "--generation-id", "g-1", "--expected-current", "none", code=2)
        proposal["source_hashes"] = {"source-1": selected["events_sha256"]}
        dump(proposal_path, proposal)
        self.cli(self.knowledge, "stage", "--proposal", proposal_path, "--generation-id", "g-1", "--expected-current", "none", code=2)
        proposal["source_hashes"] = {"source-1": hashlib.sha256((source / "events.jsonl").read_bytes()).hexdigest()}
        dump(proposal_path, proposal)
        self.cli(self.knowledge, "stage", "--proposal", proposal_path, "--generation-id", "g-1", "--expected-current", "none", code=2)
        self.assertFalse((self.base / "central/knowledge").exists())

    def test_root_stage_binds_canonical_selection_and_rejects_unregistered_paths(self):
        source = self.base / "central/runs/source-1"
        rows = complete_read_run("source-1")
        write_log(source, rows)
        selected = self.cli(self.state, "list-runs")["runs"][0]
        proposal = {"action": "create", "proposer": "proposer", "reviewer": "reviewer", "source_runs": [str(source)], "record": record(), "source_hashes": {"source-1": selected["events_sha256"]}}
        path = dump(self.base / "proposal.json", proposal)
        rows[0]["payload"]["objective"] = "changed but still structurally valid"
        write_log(source, rows)
        self.cli(self.knowledge, "stage", "--proposal", path, "--generation-id", "g-1", "--expected-current", "none", code=2)
        self.assertFalse((self.base / "central/knowledge").exists())
        other = self.base / "unregistered"
        write_log(other, complete_read_run("source-1"))
        proposal["source_runs"] = [str(other)]
        dump(path, proposal)
        self.cli(self.knowledge, "stage", "--proposal", path, "--generation-id", "g-1", "--expected-current", "none", code=2)
        self.assertFalse((self.base / "central/knowledge").exists())

    def test_selection_rejects_impossible_helper_results_and_preserves_log(self):
        run = self.base / "selections"
        log = write_log(run, [opened()])
        before = log.read_bytes()
        good = {"generation_id": "g-1", "cue_fingerprint": "test", "cues": {"operation": ["resume"]}, "matches": [{"id": "k-1", "revision": 1, "status": "supported", "reason": "cue"}], "retrieval_status": "matched"}
        import copy
        variants = []
        for updates in ({"generation_id": "none"}, {"retrieval_status": "no_match"}, {"retrieval_status": "unchanged"}, {"matches": []}, {"cues": {}}, {"cues": {"made-up": []}}, {"cues": {"task": "text"}}, {"cues": {"include_non_supported": "yes"}}):
            item = copy.deepcopy(good); item.update(updates); variants.append(item)
        for status in ("invented", "refuted", "retired", "contested"):
            item = copy.deepcopy(good); item["matches"][0]["status"] = status; variants.append(item)
        item = copy.deepcopy(good); item["matches"] *= 2; variants.append(item)
        for item in variants:
            path = dump(self.base / "selection.json", event(2, "knowledge.selected", item))
            self.cli(self.state, "append", "--run-dir", run, "--event", path, code=2)
            self.assertEqual(log.read_bytes(), before)
        self.cli(self.state, "append", "--run-dir", run, "--event", dump(self.base / "selection.json", event(2, "knowledge.selected", good)))
        unchanged = {**good, "matches": [], "retrieval_status": "unchanged"}
        self.cli(self.state, "append", "--run-dir", run, "--event", dump(self.base / "selection.json", event(3, "knowledge.selected", unchanged)))
        changed = {**unchanged, "cue_fingerprint": "different"}
        self.cli(self.state, "append", "--run-dir", run, "--event", dump(self.base / "selection.json", event(4, "knowledge.selected", changed)), code=2)

    def test_released_assignment_projection_and_resume_stay_frozen_until_reuse(self):
        reader = task("t-1", owner="/root/reader")
        rows = complete_read_run()[:3]
        rows[1]["payload"]["tasks"] = [reader]
        rows += [event(4, "agent.requested", {"task_id": "t-1", "handle": reader["owner"], "requested_model": reader["requested_model"], "requested_effort": reader["requested_effort"], "fork_turns": "none"}),
                 event(5, "evidence.recorded", {"evidence_id": "ev-1", "criterion_ids": ["c-1"], "kind": "observation", "locator": "test", "sha256": None}),
                 event(6, "agent.observed", {"handle": reader["owner"], "lifecycle": "completed", "effect_status": "reconciled", "effective_model": None, "effective_effort": None}),
                 event(7, "task.result", {"task_id": "t-1", "task_revision": 1, "outcome": "passed", "effect_status": "none", "evidence_ids": ["ev-1"]}),
                 event(8, "agent.observed", {"handle": reader["owner"], "lifecycle": "missing", "effect_status": "unknown", "effective_model": None, "effective_effort": None})]
        run = self.base / "projection"
        write_log(run, rows)
        snapshot = self.cli(self.state, "snapshot", "--run-dir", run, "--write")
        self.assertEqual(snapshot["agents"][reader["owner"]]["lifecycle"], "completed")
        self.assertEqual(snapshot["agents"][reader["owner"]]["effect_status"], "reconciled")
        agents = dump(self.base / "agents.json", [])
        resumed = self.cli(self.state, "resume", "--run-dir", run, "--agents", agents)
        self.assertEqual(resumed["proposed_events"], [])

    def test_installed_discover_stage_retrieve_resume_and_uninstall(self):
        target = self.base / "installed"
        installed = subprocess.run(["bash", str(SAGE / "install.sh"), "--target-root", str(target)], capture_output=True, text=True)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.state = target / "sage/bin/sage_state.py"
        self.knowledge = target / "sage/bin/sage_knowledge.py"
        source = self.base / "legacy/run"
        write_log(source, complete_read_run("source-1"))
        self.cli(self.state, "register", "--run-dir", source)
        selected = self.cli(self.state, "list-runs")["runs"][0]
        proposal = dump(self.base / "proposal.json", {"action": "create", "proposer": "proposer", "reviewer": "reviewer", "source_runs": [selected["run_dir"]], "source_hashes": {selected["run_id"]: selected["events_sha256"]}, "record": record()})
        self.cli(self.knowledge, "stage", "--proposal", proposal, "--generation-id", "g-1", "--expected-current", "none")
        self.cli(self.knowledge, "activate", "--generation-id", "g-1", "--expected-current", "none")
        self.cli(self.knowledge, "validate")
        cue = dump(self.base / "cues.json", cues(operation=["resume"], failure=["stale-snapshot"]))
        value = self.cli(self.knowledge, "retrieve", "--cues", cue, "--limit", "3")
        self.assertEqual(value["matches"][0]["id"], "k-1")
        previous = dump(self.base / "previous.json", [{"id": "k-1", "revision": 1, "generation_id": "g-1"}])
        self.assertEqual(self.cli(self.knowledge, "revalidate", "--previous", previous, "--cues", cue)["diagnostics"][0]["diagnostic"], "unchanged_applicable")
        proposal2 = dump(self.base / "proposal2.json", {"action": "create", "proposer": "proposer", "reviewer": "reviewer", "source_runs": [selected["run_dir"]], "source_hashes": {selected["run_id"]: selected["events_sha256"]}, "record": record("k-2")})
        self.cli(self.knowledge, "stage", "--proposal", proposal2, "--generation-id", "g-2", "--expected-current", "g-1")
        self.cli(self.knowledge, "activate", "--generation-id", "g-2", "--expected-current", "g-1")
        self.cli(self.knowledge, "rollback", "--generation-id", "g-1", "--expected-current", "g-2")
        self.cli(self.state, "report", "--run-id", "source-1", "--write")
        agents = dump(self.base / "agents.json", [])
        self.cli(self.state, "resume", "--run-id", "source-1", "--agents", agents)
        removed = subprocess.run(["bash", str(SAGE / "uninstall.sh"), "--target-root", str(target)], capture_output=True, text=True)
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertTrue((self.base / "central/knowledge/current.json").is_file())
        self.assertTrue(source.is_dir())
        self.assertTrue((self.base / "central/run-references/source-1.json").is_file())


if __name__ == "__main__":
    unittest.main()
