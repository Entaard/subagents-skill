from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SAGE_ROOT = REPOSITORY_ROOT / "sage"
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from sage.lib.artifacts import render_run, validate_receipt, validate_run  # noqa: E402
from sage.lib.common import sage_operation_lock, tree_sha256  # noqa: E402
from sage.lib.knowledge import (  # noqa: E402
    build_index,
    get_indexed,
    inspect_closed_runs,
    prepare_candidate,
    promote,
    promote_batch,
    reconcile_installed,
    record_filename,
    validate_record,
)
import sage.lib.lifecycle as lifecycle_module  # noqa: E402
from sage.lib.lifecycle import install, uninstall  # noqa: E402


def load_script(path: Path, name: str):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def run_light(state: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SAGE_ROOT / "scripts/sage-light.py"), "--state-root", str(state), *arguments],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_lifecycle(*arguments: str, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SAGE_ROOT / "scripts/sage-lifecycle.py"), *arguments],
        cwd=REPOSITORY_ROOT,
        env={**os.environ, **(environment or {})},
        text=True,
        capture_output=True,
        check=False,
    )


def create_closed_run(state: Path, run_id: str) -> Path:
    run = json.loads((SAGE_ROOT / "artifacts/fixtures/valid/zero-delegation.json").read_text())
    run["run_id"] = run_id
    run["plan"]["plan_id"] = f"plan-{run_id}"
    active = state / "runs/active" / run_id
    active.mkdir(parents=True)
    (active / "run.json").write_text(json.dumps(run), encoding="utf-8")
    closed = run_light(state, "close", run_id)
    if closed.returncode != 0:
        raise AssertionError(closed.stderr)
    return state / "runs/closed" / run_id


class SkillBehaviorTests(unittest.TestCase):
    def test_activation_is_explicit_and_full_light_orchestration_is_bounded(self) -> None:
        skill = (SAGE_ROOT / "skills/sage/SKILL.md").read_text(encoding="utf-8")
        metadata = (SAGE_ROOT / "skills/sage/agents/openai.yaml").read_text(encoding="utf-8")
        codex = (SAGE_ROOT / "skills/sage/references/codex.md").read_text(encoding="utf-8")
        topologies = (SAGE_ROOT / "policy/topologies.md").read_text(encoding="utf-8")
        promote_skill = (SAGE_ROOT / "skills/sage-promote/SKILL.md").read_text(encoding="utf-8")
        promote_metadata = (SAGE_ROOT / "skills/sage-promote/agents/openai.yaml").read_text(encoding="utf-8")
        self.assertIn("only when the user explicitly invokes `$sage`", skill)
        self.assertIn("allow_implicit_invocation: false", metadata)
        self.assertIn("only when the user explicitly invokes `$sage-promote`", promote_skill)
        self.assertIn("allow_implicit_invocation: false", promote_metadata)
        self.assertIn("one or more closed Sage run logs", promote_skill)
        self.assertIn("installed overlay", promote_skill)
        self.assertIn("explicit global request", promote_skill)
        for native_name in (
            "spawn_agent", "fork_turns", "send_message", "followup_task",
            "list_agents", "wait_agent", "interrupt_agent",
        ):
            self.assertIn(f"`{native_name}`", codex)
        for profile in ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"):
            self.assertIn(profile, codex)
        for role in ("Scout", "Researcher", "Writer", "Verifier", "Successor"):
            self.assertIn(f"**{role}:**", codex)
        for topology in (
            "Independent sweep", "Implement, review, fix", "Migration pipeline",
            "Bake-off and judge panel", "Loop until dry", "Adversarial verification",
            "Quarantined deep read", "Competing hypotheses", "Completeness critic",
            "Blind acceptance suite", "Pre-write plan critic", "Blind behavioral lens",
        ):
            self.assertIn(f"## {topology}", topologies)
        self.assertIn("Zero delegated units is valid", skill)
        self.assertIn("bounded role contract", skill)
        self.assertIn("settle conflicts", skill)
        self.assertIn("root owns synthesis", skill.lower())
        self.assertIn("exactly one active writer", skill)
        self.assertIn("Do not extract lessons", skill)
        self.assertIn("explicit later `$sage-promote`", skill)
        inventory = json.loads((SAGE_ROOT / "docs/phase0/invariant-ownership.json").read_text())
        invariants = {row["id"]: row for row in inventory["invariants"]}
        self.assertEqual(
            invariants["POL-SOFTWARE-IMPLEMENTATION"]["canonical"],
            "sage/policy/implementation.md#clean-code",
        )
        self.assertEqual(
            invariants["POL-SOFTWARE-FIXED-POINT-REVIEW"]["canonical"],
            "sage/policy/software-review.md#pin-the-fixed-point",
        )
        manifest = json.loads((SAGE_ROOT / "skills/sage/references/source-manifest.json").read_text())
        routed_sources = {row["source"]: row for row in manifest["files"]}
        for source in ("sage/policy/implementation.md", "sage/policy/software-review.md"):
            row = routed_sources[source]
            generated = SAGE_ROOT / "skills/sage" / row["generated"]
            self.assertEqual(hashlib.sha256(generated.read_bytes()).hexdigest(), row["generated_sha256"])
        review_lines = (SAGE_ROOT / "policy/software-review.md").read_text().splitlines()
        smell_rows = [line for line in review_lines if line.partition(".")[0].isdigit()]
        self.assertEqual([line.partition(".")[0] for line in smell_rows], [str(index) for index in range(1, 18)])

    def test_new_plans_validate_with_uncommitted_bounds_but_cannot_be_admitted(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            complete = run_light(state, "start", "--objective", "review one bounded file", "--run-id", "run-complete")
            self.assertEqual(complete.returncode, 0, complete.stderr)
            complete_run = json.loads((state / "runs/active/run-complete/run.json").read_text())
            revision = complete_run["plan"]["revisions"][0]
            self.assertEqual(revision["kind"], "complete")
            self.assertEqual(revision["bounds"]["planned_agent_count"], 0)
            for field in (
                "max_units", "max_attempts_per_unit", "max_concurrency",
                "max_plan_revisions", "max_admission_seconds",
                "max_admitted_agents", "no_progress_revision_limit",
            ):
                self.assertIsNone(revision["bounds"][field])
            self.assertEqual(validate_run(complete_run, SAGE_ROOT), [])

            prematurely_admitted = copy.deepcopy(complete_run)
            prematurely_admitted["plan"]["revisions"][0]["admitted_at"] = complete_run["created_at"]
            self.assertTrue(any(
                "ART-ADMISSION-UNCOMMITTED" in issue
                for issue in validate_run(prematurely_admitted, SAGE_ROOT)
            ))

            committed = copy.deepcopy(prematurely_admitted)
            committed_bounds = committed["plan"]["revisions"][0]["bounds"]
            committed_bounds.update({
                "max_units": 1,
                "max_attempts_per_unit": 1,
                "max_concurrency": 1,
                "max_plan_revisions": 1,
                "max_admission_seconds": 600,
                "max_admitted_agents": 1,
                "no_progress_revision_limit": 1,
            })
            self.assertEqual(validate_run(committed, SAGE_ROOT), [])

            dispatched_without_bounds = json.loads(
                (SAGE_ROOT / "artifacts/fixtures/valid/zero-delegation.json").read_text()
            )
            uncommitted = dispatched_without_bounds["plan"]["revisions"][0]["bounds"]
            for field in (
                "max_units", "max_attempts_per_unit", "max_concurrency",
                "max_plan_revisions", "max_admission_seconds",
                "max_admitted_agents", "no_progress_revision_limit",
            ):
                uncommitted[field] = None
                dispatched_without_bounds["briefs"][0]["caps"][field] = None
            dispatch_issues = validate_run(dispatched_without_bounds, SAGE_ROOT)
            self.assertTrue(any("ART-BRIEF-BEFORE-ADMISSION" in issue for issue in dispatch_issues))
            self.assertTrue(any("ART-ATTEMPT-BEFORE-ADMISSION" in issue for issue in dispatch_issues))

            bootstrap = run_light(
                state, "start", "--objective", "map an unknown bounded corpus",
                "--run-id", "run-bootstrap", "--bootstrap",
            )
            self.assertEqual(bootstrap.returncode, 0, bootstrap.stderr)
            bootstrap_run = json.loads((state / "runs/active/run-bootstrap/run.json").read_text())
            revision = bootstrap_run["plan"]["revisions"][0]
            self.assertEqual((revision["revision"], revision["kind"]), (0, "bootstrap"))
            self.assertEqual(revision["units"][0]["effect_class"], "read_only")
            self.assertIsNone(revision["bounds"]["max_attempts_per_unit"])
            self.assertEqual(validate_run(bootstrap_run, SAGE_ROOT), [])

            mutating = run_light(
                state, "start", "--objective", "implement a bounded change",
                "--run-id", "run-mutating", "--effect-class", "mutating",
            )
            self.assertEqual(mutating.returncode, 0, mutating.stderr)
            mutating_run = json.loads((state / "runs/active/run-mutating/run.json").read_text())
            mutating_unit = mutating_run["plan"]["revisions"][0]["units"][0]
            self.assertEqual(mutating_unit["effect_class"], "mutating")
            self.assertIn("workspace.write.scoped", mutating_unit["required_capabilities"])
            mutating_facts = [
                json.loads(line)
                for line in (state / "runs/active/run-mutating/facts.jsonl").read_text().splitlines()
            ]
            self.assertEqual(mutating_facts[0]["payload"]["task_effect_class"], "mutating")
            self.assertEqual(validate_run(mutating_run, SAGE_ROOT), [])

            unsafe = run_light(
                state, "start", "--objective", "use Bearer abcdefghijklmnopqrstuvwxyz",
                "--run-id", "run-unsafe-objective",
            )
            self.assertNotEqual(unsafe.returncode, 0)
            self.assertFalse((state / "runs/active/run-unsafe-objective").exists())

    def test_commit_state_and_reader_review_artifact_cover_fanout_synthesis(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary)
            state = root / "state"
            started = run_light(state, "start", "--objective", "review evidence", "--run-id", "run-commit")
            self.assertEqual(started.returncode, 0, started.stderr)
            live = state / "runs/active/run-commit/run.json"
            candidate = json.loads(live.read_text())
            candidate["gaps"].append({
                "gap_id": "G-NATIVE-EFFECTIVE-MODEL",
                "description": "The native result did not expose an effective model identity.",
                "impact": "Requested and effective placement cannot be equated.",
                "evidence_checked": [{"kind": "observation", "locator": "native://result", "detail": "No effective identity field."}],
                "owner": "policy_actor",
                "next_action": "Record effective identity as unknown.",
                "status": "accepted_risk",
            })
            candidate_path = root / "candidate.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            committed = run_light(state, "commit-state", "--run-id", "run-commit", "--candidate", str(candidate_path))
            self.assertEqual(committed.returncode, 0, committed.stderr)
            facts = [json.loads(line) for line in (live.parent / "facts.jsonl").read_text().splitlines()]
            self.assertEqual([row["type"] for row in facts], ["run.created", "run.state_committed"])

            mutating_review = json.loads((SAGE_ROOT / "artifacts/fixtures/valid/review-run.json").read_text())
            self.assertEqual(validate_run(mutating_review, SAGE_ROOT), [])
            self.assertEqual(
                [unit["unit_id"] for unit in mutating_review["plan"]["revisions"][0]["units"] if unit["effect_class"] == "mutating"],
                ["U-WRITE"],
            )
            self.assertEqual(mutating_review["briefs"][0]["role"], "writer")
            self.assertTrue(mutating_review["results"][0]["files_changed"])
            self.assertGreaterEqual(len({row["verified_by"] for row in mutating_review["verifications"]}), 2)
            self.assertTrue(all(row["verification_ids"] for row in mutating_review["dispositions"]))

            review = copy.deepcopy(mutating_review)
            for revision in review["plan"]["revisions"]:
                for unit in revision["units"]:
                    unit["effect_class"] = "read_only"
            for brief in review["briefs"]:
                brief["role"] = "reader-reviewer"
                brief["allowed_effects"] = ["read"]
                brief["allowed_resources"] = ["resource-bounded-corpus"]
                brief["required_tools"] = ["read", "search"]
                brief["must_not"] = ["mutate the corpus", "treat a peer report as verified evidence"]
            for attempt in review["attempts"]:
                attempt["side_effect_class"] = "read_only"
            for result in review["results"]:
                result["files_changed"] = []
            self.assertEqual(validate_run(review, SAGE_ROOT), [])
            self.assertTrue(all(attempt.get("worker_ref") for attempt in review["attempts"]))
            self.assertTrue(review["briefs"][0]["caps"]["max_attempts_per_unit"] > 0)
            self.assertTrue(review["results"] and review["findings"] and review["dispositions"])
            self.assertTrue(all(row["verification_ids"] for row in review["dispositions"]))
            review_path = root / "reader-review.json"
            report_path = root / "reader-review.md"
            review_path.write_text(json.dumps(review), encoding="utf-8")
            render_run(review_path, report_path, SAGE_ROOT)
            self.assertIn("## Coordination outcome", report_path.read_text())

    def test_current_run_log_accepts_facts_but_rejects_learning(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            started = run_light(state, "start", "--objective", "record evidence", "--run-id", "run-facts")
            self.assertEqual(started.returncode, 0, started.stderr)
            types = run_light(state, "fact-types")
            self.assertEqual(types.returncode, 0, types.stderr)
            self.assertIn("observation.recorded", json.loads(types.stdout)["allowed_types"])

            observation = run_light(
                state, "append-fact", "--run-id", "run-facts",
                "--type", "observation.recorded", "--classification", "internal",
                "--payload", '{"claim":"observed only"}',
            )
            self.assertEqual(observation.returncode, 0, observation.stderr)
            assessed = run_light(
                state, "append-fact", "--run-id", "run-facts",
                "--type", "knowledge.assessed", "--classification", "internal",
                "--payload", '{"stable_id":"sage-knowledge-v1:example","outcome":"useful","decision":"changed the admission check"}',
            )
            self.assertEqual(assessed.returncode, 0, assessed.stderr)
            missed = run_light(
                state, "append-fact", "--run-id", "run-facts",
                "--type", "knowledge.assessed", "--classification", "internal",
                "--payload", '{"recognizer":"mutation changes shared state","outcome":"missed","decision":"concurrency guidance was loaded late"}',
            )
            self.assertEqual(missed.returncode, 0, missed.stderr)
            confidential = run_light(
                state, "append-fact", "--run-id", "run-facts",
                "--type", "evidence.recorded", "--classification", "confidential",
                "--payload", '{"sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","locator":"protected://evidence/1","purpose":"review evidence"}',
            )
            self.assertEqual(confidential.returncode, 0, confidential.stderr)
            for forbidden in ("lesson.extracted", "knowledge.promoted"):
                rejected = run_light(
                    state, "append-fact", "--run-id", "run-facts",
                    "--type", forbidden, "--classification", "internal", "--payload", "{}",
                )
                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn("sage-promote", rejected.stderr)
            non_object = run_light(
                state, "append-fact", "--run-id", "run-facts",
                "--type", "observation.recorded", "--classification", "internal", "--payload", "[]",
            )
            self.assertNotEqual(non_object.returncode, 0)
            restricted = run_light(
                state, "append-fact", "--run-id", "run-facts",
                "--type", "observation.recorded", "--classification", "internal",
                "--payload", '{"secret":"must-not-land"}',
            )
            self.assertNotEqual(restricted.returncode, 0)
            facts = [
                json.loads(line)
                for line in (state / "runs/active/run-facts/facts.jsonl").read_text().splitlines()
            ]
            self.assertEqual(
                [row["type"] for row in facts],
                ["run.created", "observation.recorded", "knowledge.assessed", "knowledge.assessed", "evidence.recorded"],
            )
            self.assertEqual(
                [row["classification"] for row in facts],
                ["internal", "internal", "internal", "internal", "confidential"],
            )
            self.assertFalse((state / "promoted-overlay").exists())

    def test_commit_state_rejects_rewriting_admitted_plans_and_recorded_findings(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary)
            state = root / "state"
            run = json.loads((SAGE_ROOT / "artifacts/fixtures/valid/review-run.json").read_text())
            active = state / "runs/active" / run["run_id"]
            active.mkdir(parents=True)
            (active / "run.json").write_text(json.dumps(run), encoding="utf-8")

            changed_plan = copy.deepcopy(run)
            changed_plan["plan"]["revisions"][0]["reason"] = "rewrite admitted history"
            plan_candidate = root / "changed-plan.json"
            plan_candidate.write_text(json.dumps(changed_plan), encoding="utf-8")
            rejected_plan = run_light(
                state, "commit-state", "--run-id", run["run_id"], "--candidate", str(plan_candidate),
            )
            self.assertNotEqual(rejected_plan.returncode, 0)
            self.assertIn("immutable plan revision", rejected_plan.stderr)

            changed_finding = copy.deepcopy(run)
            changed_finding["findings"][0]["failure_mode"] = "rewritten finding"
            finding_candidate = root / "changed-finding.json"
            finding_candidate.write_text(json.dumps(changed_finding), encoding="utf-8")
            rejected_finding = run_light(
                state, "commit-state", "--run-id", run["run_id"], "--candidate", str(finding_candidate),
            )
            self.assertNotEqual(rejected_finding.returncode, 0)
            self.assertIn("cannot rewrite recorded findings", rejected_finding.stderr)

    def test_unavailable_automatic_sensor_explicit_fallback_resume_and_render(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            started = run_light(state, "start", "--objective", "review", "--run-id", "run-handoff")
            self.assertEqual(started.returncode, 0, started.stderr)
            simulated = run_light(
                state, "handover", "run-handoff", "--reason", "automatic",
                "--occupied-tokens", "30", "--context-window", "100", "--sensor-id", "caller-label",
            )
            self.assertNotEqual(simulated.returncode, 0)
            self.assertIn("not a supported sensor", simulated.stderr)
            reached = run_light(state, "handover", "run-handoff", "--reason", "explicit")
            self.assertEqual(reached.returncode, 0, reached.stderr)
            handoff_path = Path(json.loads(reached.stdout)["handoff"])
            self.assertEqual(handoff_path.name, "handoff.json")
            self.assertFalse(handoff_path.with_suffix(".md").exists())
            resumed = run_light(state, "resume", "run-handoff")
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertFalse(json.loads(resumed.stdout)["admission_ready"])
            report = run_light(state, "report", "run-handoff")
            self.assertEqual(report.returncode, 0, report.stderr)
            self.assertIn("# Sage run run-handoff", report.stdout)
            self.assertIn("## Coordination outcome", report.stdout)
            run_path = state / "runs/active/run-handoff/run.json"
            reported_run = json.loads(run_path.read_text())
            rendered_id = reported_run["rendered_run_record"]["artifact_id"]
            rendered_artifact = next(row for row in reported_run["artifacts"] if row["artifact_id"] == rendered_id)
            self.assertEqual(rendered_artifact["classification"], "confidential")
            markdown = state / "runs/active/run-handoff/run.md"
            first = markdown.read_bytes()
            rendered = run_light(state, "render", str(run_path), "--output", str(markdown))
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertEqual(markdown.read_bytes(), first)
            verified = run_light(state, "verify-render", str(run_path), str(markdown))
            self.assertEqual(verified.returncode, 0, verified.stderr)

            explicit = run_light(state, "start", "--objective", "review", "--run-id", "run-explicit")
            self.assertEqual(explicit.returncode, 0, explicit.stderr)
            handed = run_light(state, "handover", "run-explicit", "--reason", "explicit")
            self.assertEqual(handed.returncode, 0, handed.stderr)
            explicit_run = json.loads((state / "runs/active/run-explicit/run.json").read_text())
            self.assertTrue(any(row["gap_id"] == "G-CONTEXT-SENSOR" for row in explicit_run["gaps"]))

    def test_hash_bound_handoff_revalidates_the_recorded_baseline(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary)
            state = root / "state"
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "source.txt"
            source.write_text("before\n", encoding="utf-8")
            started = run_light(state, "start", "--objective", "resume safely", "--run-id", "run-bound")
            self.assertEqual(started.returncode, 0, started.stderr)
            baseline = run_light(state, "baseline", str(corpus))
            self.assertEqual(baseline.returncode, 0, baseline.stderr)
            captured = json.loads(baseline.stdout)["baselines"][0]

            handed = run_light(
                state, "handover", "run-bound", "--reason", "explicit", "--baseline", str(corpus),
            )
            self.assertEqual(handed.returncode, 0, handed.stderr)
            handoff_result = json.loads(handed.stdout)
            handoff_path = Path(handoff_result["handoff"])
            handoff = json.loads(handoff_path.read_text())
            self.assertEqual(handoff["baselines"], [captured])
            self.assertIn("bounds", handoff)
            self.assertIn("attempts", handoff)
            self.assertEqual(handoff["writer_control"]["external_lease"], "unavailable_in_light_mode")

            projected = run_light(state, "handoff-projection", "run-bound")
            self.assertEqual(projected.returncode, 0, projected.stderr)
            projection_path = handoff_path.with_suffix(".md")
            self.assertTrue(projection_path.is_file())
            checked = run_light(state, "handoff-projection", "run-bound", "--check")
            self.assertEqual(checked.returncode, 0, checked.stderr)
            projection_path.unlink()

            ready = run_light(state, "resume", "run-bound")
            self.assertEqual(ready.returncode, 0, ready.stderr)
            self.assertTrue(json.loads(ready.stdout)["admission_ready"])
            source.write_text("after\n", encoding="utf-8")
            stale = run_light(state, "resume", "run-bound")
            self.assertEqual(stale.returncode, 0, stale.stderr)
            self.assertFalse(json.loads(stale.stdout)["admission_ready"])

    def test_resume_fails_for_missing_malformed_hash_invalid_and_stale_handoff_json(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            started = run_light(state, "start", "--objective", "resume safely", "--run-id", "run-invalid-handoff")
            self.assertEqual(started.returncode, 0, started.stderr)
            handed = run_light(state, "handover", "run-invalid-handoff", "--reason", "explicit")
            self.assertEqual(handed.returncode, 0, handed.stderr)
            handoff_path = Path(json.loads(handed.stdout)["handoff"])
            run_path = handoff_path.with_name("run.json")
            original_handoff = handoff_path.read_bytes()
            original_run = run_path.read_bytes()

            handoff_path.unlink()
            missing = run_light(state, "resume", "run-invalid-handoff")
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("missing", missing.stderr)
            handoff_path.write_bytes(original_handoff)

            handoff_path.write_text("{", encoding="utf-8")
            malformed_run = json.loads(original_run)
            next(row for row in malformed_run["artifacts"] if row["artifact_id"] == "ART-HANDOFF")["sha256"] = hashlib.sha256(b"{").hexdigest()
            run_path.write_text(json.dumps(malformed_run), encoding="utf-8")
            malformed = run_light(state, "resume", "run-invalid-handoff")
            self.assertNotEqual(malformed.returncode, 0)
            self.assertIn("Expecting", malformed.stderr)

            run_path.write_bytes(original_run)
            handoff_path.write_text("tampered", encoding="utf-8")
            invalid_hash = run_light(state, "resume", "run-invalid-handoff")
            self.assertNotEqual(invalid_hash.returncode, 0)
            self.assertIn("integrity", invalid_hash.stderr)

            stale_handoff = json.loads(original_handoff)
            stale_handoff["bounds"]["max_units"] = 99
            stale_bytes = (json.dumps(stale_handoff, sort_keys=True, separators=(",", ":")) + "\n").encode()
            handoff_path.write_bytes(stale_bytes)
            stale_run = json.loads(original_run)
            next(row for row in stale_run["artifacts"] if row["artifact_id"] == "ART-HANDOFF")["sha256"] = hashlib.sha256(stale_bytes).hexdigest()
            run_path.write_text(json.dumps(stale_run), encoding="utf-8")
            stale = run_light(state, "resume", "run-invalid-handoff")
            self.assertNotEqual(stale.returncode, 0)
            self.assertIn("stale", stale.stderr)

    def test_terminal_close_appends_once_then_freezes_raw_log(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            run = json.loads((SAGE_ROOT / "artifacts/fixtures/valid/zero-delegation.json").read_text())
            active = state / f"runs/active/{run['run_id']}"
            active.mkdir(parents=True)
            (active / "run.json").write_text(json.dumps(run), encoding="utf-8")
            closed = run_light(state, "close", run["run_id"])
            self.assertEqual(closed.returncode, 0, closed.stderr)
            closed_dir = state / f"runs/closed/{run['run_id']}"
            facts = [json.loads(line) for line in (closed_dir / "facts.jsonl").read_text().splitlines()]
            self.assertEqual([row["type"] for row in facts], ["run.closed"])
            repeated = run_light(state, "close", run["run_id"])
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            repeated_facts = [json.loads(line) for line in (closed_dir / "facts.jsonl").read_text().splitlines()]
            self.assertEqual(repeated_facts, facts)
            rejected = run_light(
                state, "append-fact", "--run-id", run["run_id"],
                "--type", "late", "--classification", "internal", "--payload", "{}",
            )
            self.assertNotEqual(rejected.returncode, 0)


class PromotionTests(unittest.TestCase):
    def candidate(self, stable_id: str, run_id: str) -> dict[str, object]:
        return prepare_candidate({
            "schema_version": "1.0",
            "stable_id": stable_id,
            "class": "workflow_rule",
            "status": "active",
            "rule": "Verify a durable handoff before admitting resumed work.",
            "qualifier": "Sage Light runs",
            "recognizer": "A run is resumed from a handoff artifact.",
            "falsifier": "A supported native recovery transaction supersedes the handoff.",
            "provenance": [f"run:{run_id}", "artifact:ART-RECORD"],
            "promotion": {
                "action": "create",
                "evidence_class": "deterministic_invariant",
                "promotion_actor": "promotion-actor",
                "reviewed": True,
                "review_evidence": ["verification:V1"],
                "independent_refutation": ["verification:V1"],
                "independence_review": {
                    "judgment": "independent",
                    "evidence": "The selected run has a separately recorded refutation verification.",
                    "limitations": "Semantic independence is a reviewed judgment, not mechanically proved.",
                },
                "expected_utility": {
                    "recognizer": "A run is resumed from a handoff artifact.",
                    "expected_benefit": "Prevents unsafe resumed admission.",
                    "expected_cost": "One indexed lookup and verification.",
                    "net_assessment": "positive",
                },
                "novelty_review": {
                    "compared_stable_ids": [],
                    "peer_dispositions": [],
                    "disposition": "novel",
                    "rationale": "No other active stable IDs exist in this isolated fixture.",
                },
                "behavioral_evaluation": [],
                "expected_prior_sha256": None,
            },
        })

    def candidate_for_runs(
        self,
        stable_id: str,
        run_ids: list[str],
        evidence_class: str,
    ) -> dict[str, object]:
        candidate = self.candidate(stable_id, run_ids[0])
        candidate["provenance"] = [
            *(f"run:{run_id}" for run_id in run_ids),
            *(f"artifact:{run_id}:ART-RECORD" for run_id in run_ids),
        ]
        candidate["promotion"]["evidence_class"] = evidence_class
        candidate["promotion"]["review_evidence"] = [f"verification:{run_ids[0]}:V1"]
        candidate["promotion"]["independent_refutation"] = [f"verification:{run_ids[0]}:V1"]
        candidate["promotion"]["behavioral_evaluation"] = (
            [f"verification:{run_ids[-1]}:V1"]
            if evidence_class == "shared_policy_guidance"
            else []
        )
        return prepare_candidate(candidate)

    def set_batch_peers(self, candidates: list[dict[str, object]]) -> list[dict[str, object]]:
        stable_ids = [candidate["stable_id"] for candidate in candidates]
        for candidate in candidates:
            candidate["promotion"]["novelty_review"]["peer_dispositions"] = [
                {
                    "stable_id": stable_id,
                    "disposition": "distinct",
                    "rationale": "The peer has a separately scoped recognizer and rule.",
                }
                for stable_id in stable_ids
                if stable_id != candidate["stable_id"]
            ]
        return [prepare_candidate(candidate) for candidate in candidates]

    def test_promotion_evidence_class_boundaries_and_required_gates(self) -> None:
        cases = (
            ("deterministic_invariant", 1),
            ("empirical_heuristic", 3),
            ("shared_policy_guidance", 6),
        )
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary)
            for evidence_class, minimum in cases:
                state = root / f"at-{evidence_class}"
                run_ids = [f"{evidence_class}-{index}" for index in range(minimum)]
                for run_id in run_ids:
                    create_closed_run(state, run_id)
                candidate = self.candidate_for_runs(
                    f"sage-knowledge-v1:boundary.{evidence_class}", run_ids, evidence_class,
                )
                candidate_path = state / "candidate.json"
                candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
                landed = promote(candidate_path, run_ids, installed_state_root=state)
                self.assertTrue(landed["changed"])
                self.assertEqual(landed["review_result"]["evidence_class"], evidence_class)

                revise_state = root / f"revise-{evidence_class}"
                seed_run = f"seed-{evidence_class}"
                create_closed_run(revise_state, seed_run)
                stable_id = f"sage-knowledge-v1:revise.{evidence_class}"
                seed = self.candidate(stable_id, seed_run)
                seed_path = revise_state / "seed.json"
                seed_path.write_text(json.dumps(seed), encoding="utf-8")
                promote(seed_path, seed_run, installed_state_root=revise_state)
                revise_ids = [f"revise-{evidence_class}-{index}" for index in range(minimum)]
                for run_id in revise_ids:
                    create_closed_run(revise_state, run_id)
                revised = self.candidate_for_runs(stable_id, revise_ids, evidence_class)
                revised["rule"] = "Revised rule content supported at the evidence-class boundary."
                revised["promotion"]["action"] = "revise"
                revised["promotion"]["expected_prior_sha256"] = seed["stored_integrity_sha256"]
                revised["promotion"]["novelty_review"]["disposition"] = "revise_existing"
                revised = prepare_candidate(revised)
                revised_path = revise_state / "revised.json"
                revised_path.write_text(json.dumps(revised), encoding="utf-8")
                revised_result = promote(revised_path, revise_ids, installed_state_root=revise_state)
                self.assertTrue(revised_result["changed"])
                self.assertEqual(revised_result["action"], "revise")

                if minimum == 1:
                    with self.assertRaisesRegex(ValueError, "at least one closed run"):
                        promote(candidate_path, [], installed_state_root=state)
                    continue
                below_state = root / f"below-{evidence_class}"
                below_ids = [f"below-{evidence_class}-{index}" for index in range(minimum - 1)]
                for run_id in below_ids:
                    create_closed_run(below_state, run_id)
                below = self.candidate_for_runs(
                    f"sage-knowledge-v1:below.{evidence_class}", below_ids, evidence_class,
                )
                below_path = below_state / "candidate.json"
                below_path.write_text(json.dumps(below), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, f"requires at least {minimum}"):
                    promote(below_path, below_ids, installed_state_root=below_state)

            missing_refutation = self.candidate("sage-knowledge-v1:missing.refutation", "closed")
            missing_refutation["promotion"]["independent_refutation"] = []
            missing_refutation = prepare_candidate(missing_refutation)
            self.assertTrue(any(
                "independent_refutation" in issue
                for issue in validate_record(missing_refutation, require_review=True)
            ))

            missing_behavior = self.candidate("sage-knowledge-v1:missing.behavior", "closed")
            missing_behavior["promotion"]["evidence_class"] = "shared_policy_guidance"
            missing_behavior = prepare_candidate(missing_behavior)
            self.assertTrue(any(
                "behavioral evaluation" in issue
                for issue in validate_record(missing_behavior, require_review=True)
            ))

            utility_mismatch = self.candidate("sage-knowledge-v1:utility.mismatch", "closed")
            utility_mismatch["promotion"]["expected_utility"]["recognizer"] = "a different recognizer"
            utility_mismatch = prepare_candidate(utility_mismatch)
            self.assertTrue(any(
                "bind the candidate recognizer" in issue
                for issue in validate_record(utility_mismatch, require_review=True)
            ))

            novelty_state = root / "novelty"
            first_run = "novelty-first"
            second_run = "novelty-second"
            create_closed_run(novelty_state, first_run)
            create_closed_run(novelty_state, second_run)
            first = self.candidate("sage-knowledge-v1:novelty.first", first_run)
            first_path = novelty_state / "first.json"
            first_path.write_text(json.dumps(first), encoding="utf-8")
            promote(first_path, first_run, installed_state_root=novelty_state)
            omitted_overlap = self.candidate("sage-knowledge-v1:novelty.second", second_run)
            omitted_path = novelty_state / "omitted.json"
            omitted_path.write_text(json.dumps(omitted_overlap), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "name every other active stable ID"):
                promote(omitted_path, second_run, installed_state_root=novelty_state)

    def test_promotion_batch_cap_reports_excess_before_landing(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary)
            arguments: list[str] = []
            for index in range(6):
                candidate = self.candidate(f"sage-knowledge-v1:batch.{index}", "closed")
                path = root / f"candidate-{index}.json"
                path.write_text(json.dumps(candidate), encoding="utf-8")
                arguments.extend(["--candidate", str(path)])
            result = subprocess.run(
                [
                    sys.executable,
                    str(SAGE_ROOT / "scripts/sage-promote.py"),
                    *arguments,
                    "--run-id", "closed",
                    "--state-root", str(root / "state"),
                ],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("capped at five", result.stderr)
            self.assertIn("sage-knowledge-v1:batch.5", result.stderr)
            self.assertFalse((root / "state/promoted-overlay").exists())

    def test_promotion_batch_commits_two_candidates_in_canonical_order(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            run_id = "batch-success"
            create_closed_run(state, run_id)
            candidates = self.set_batch_peers([
                self.candidate("sage-knowledge-v1:batch.z", run_id),
                self.candidate("sage-knowledge-v1:batch.a", run_id),
            ])
            paths = []
            for index, candidate in enumerate(candidates):
                path = state / f"candidate-{index}.json"
                path.write_text(json.dumps(candidate), encoding="utf-8")
                paths.append(path)
            command = [sys.executable, str(SAGE_ROOT / "scripts/sage-promote.py")]
            for path in paths:
                command.extend(["--candidate", str(path)])
            command.extend(["--run-id", run_id, "--state-root", str(state)])
            completed = subprocess.run(
                command,
                cwd=REPOSITORY_ROOT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual(
                result["candidate_order"],
                ["sage-knowledge-v1:batch.a", "sage-knowledge-v1:batch.z"],
            )
            self.assertEqual(
                [row["stable_id"] for row in get_indexed(result["candidate_order"], state)],
                result["candidate_order"],
            )

    def test_promotion_batch_preflight_rejects_invalid_peer_and_late_candidate_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            reconcile_installed(SAGE_ROOT / "knowledge", state)
            prior_index = (state / "promoted-index/index.json").read_bytes()
            run_id = "batch-preflight"
            create_closed_run(state, run_id)
            peer_invalid = self.candidate("sage-knowledge-v1:batch.peer-a", run_id)
            peer_other = self.candidate("sage-knowledge-v1:batch.peer-b", run_id)
            peer_invalid["promotion"]["novelty_review"]["peer_dispositions"] = []
            peer_other["promotion"]["novelty_review"]["peer_dispositions"] = [{
                "stable_id": peer_invalid["stable_id"],
                "disposition": "distinct",
                "rationale": "Separate scope.",
            }]
            peer_paths = []
            for index, candidate in enumerate((prepare_candidate(peer_invalid), prepare_candidate(peer_other))):
                path = state / f"peer-{index}.json"
                path.write_text(json.dumps(candidate), encoding="utf-8")
                peer_paths.append(path)
            with self.assertRaisesRegex(ValueError, "batch peer"):
                promote_batch(peer_paths, run_id, installed_state_root=state)

            valid, late_invalid = self.set_batch_peers([
                self.candidate("sage-knowledge-v1:batch.late-a", run_id),
                self.candidate("sage-knowledge-v1:batch.late-z", run_id),
            ])
            late_invalid["promotion"]["action"] = "revise"
            late_invalid["promotion"]["novelty_review"]["disposition"] = "revise_existing"
            late_invalid["promotion"]["expected_prior_sha256"] = "0" * 64
            late_invalid = prepare_candidate(late_invalid)
            late_paths = []
            for index, candidate in enumerate((valid, late_invalid)):
                path = state / f"late-{index}.json"
                path.write_text(json.dumps(candidate), encoding="utf-8")
                late_paths.append(path)
            with self.assertRaisesRegex(ValueError, "requires an existing stable ID"):
                promote_batch(late_paths, run_id, installed_state_root=state)
            self.assertEqual((state / "promoted-index/index.json").read_bytes(), prior_index)
            self.assertEqual(list((state / "promoted-overlay/active").glob("*.json")), [])

    def test_promotion_batch_rejects_duplicate_ids_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            candidate = self.candidate("sage-knowledge-v1:batch.duplicate", "closed")
            paths = []
            for index in range(2):
                path = state / f"duplicate-{index}.json"
                path.write_text(json.dumps(candidate), encoding="utf-8")
                paths.append(path)
            with self.assertRaisesRegex(ValueError, "duplicate stable IDs"):
                promote_batch(paths, "closed", installed_state_root=state)
            self.assertFalse((state / "promoted-overlay").exists())

    def test_promotion_batch_rolls_back_record_bytes_when_commit_fails(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            reconcile_installed(SAGE_ROOT / "knowledge", state)
            prior_index = (state / "promoted-index/index.json").read_bytes()
            run_id = "batch-rollback"
            create_closed_run(state, run_id)
            candidates = self.set_batch_peers([
                self.candidate("sage-knowledge-v1:batch.rollback-a", run_id),
                self.candidate("sage-knowledge-v1:batch.rollback-b", run_id),
            ])
            paths = []
            for index, candidate in enumerate(candidates):
                path = state / f"rollback-{index}.json"
                path.write_text(json.dumps(candidate), encoding="utf-8")
                paths.append(path)
            original_replace = os.replace
            replacements = 0

            def fail_second_replace(source: str, target: str) -> None:
                nonlocal replacements
                replacements += 1
                if replacements == 2:
                    raise OSError("forced commit failure")
                original_replace(source, target)

            with mock.patch("sage.lib.common.os.replace", side_effect=fail_second_replace):
                with self.assertRaisesRegex(OSError, "forced commit failure"):
                    promote_batch(paths, run_id, installed_state_root=state)
            self.assertEqual((state / "promoted-index/index.json").read_bytes(), prior_index)
            self.assertEqual(list((state / "promoted-overlay/active").glob("*.json")), [])

    def test_fresh_process_recovers_every_killed_batch_commit_boundary(self) -> None:
        runner = """
import os
import sys
from pathlib import Path
import sage.lib.knowledge as knowledge

boundary = int(sys.argv[1])
state = Path(sys.argv[2])
run_id = sys.argv[3]
candidate_paths = [Path(value) for value in sys.argv[4:]]
original_write = knowledge.atomic_write_bytes
writes = 0

def kill_after_boundary(path, content, mode=None):
    global writes
    original_write(path, content, mode)
    writes += 1
    if writes == boundary:
        os._exit(77)

knowledge.atomic_write_bytes = kill_after_boundary
knowledge.promote_batch(candidate_paths, run_id, installed_state_root=state)
"""
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary)
            for boundary in range(1, 4):
                state = root / f"boundary-{boundary}"
                run_id = f"crash-boundary-{boundary}"
                create_closed_run(state, run_id)
                candidates = self.set_batch_peers([
                    self.candidate("sage-knowledge-v1:crash.a", run_id),
                    self.candidate("sage-knowledge-v1:crash.z", run_id),
                ])
                paths = []
                for index, candidate in enumerate(candidates):
                    path = state / f"candidate-{index}.json"
                    path.write_text(json.dumps(candidate), encoding="utf-8")
                    paths.append(path)
                killed = subprocess.run(
                    [
                        sys.executable, "-c", runner, str(boundary), str(state), run_id,
                        *(str(path) for path in paths),
                    ],
                    cwd=REPOSITORY_ROOT,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(killed.returncode, 77, killed.stderr)
                self.assertTrue((state / ".promotion-transaction.json").is_file())
                recovered = run_light(state, "knowledge", "list")
                self.assertEqual(recovered.returncode, 0, recovered.stderr)
                self.assertEqual(
                    [row["stable_id"] for row in json.loads(recovered.stdout)],
                    ["sage-knowledge-v1:crash.a", "sage-knowledge-v1:crash.z"],
                )
                self.assertFalse((state / ".promotion-transaction.json").exists())
                self.assertEqual(
                    [row["stable_id"] for row in get_indexed(
                        ["sage-knowledge-v1:crash.a", "sage-knowledge-v1:crash.z"], state
                    )],
                    ["sage-knowledge-v1:crash.a", "sage-knowledge-v1:crash.z"],
                )

    def test_promotion_cli_waits_for_the_lifecycle_lock(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            run_id = "batch-serialized"
            create_closed_run(state, run_id)
            candidate = self.candidate("sage-knowledge-v1:batch.serialized", run_id)
            path = state / "candidate.json"
            path.write_text(json.dumps(candidate), encoding="utf-8")
            command = [
                sys.executable,
                str(SAGE_ROOT / "scripts/sage-promote.py"),
                "--candidate", str(path),
                "--run-id", run_id,
                "--state-root", str(state),
            ]
            with sage_operation_lock():
                process = subprocess.Popen(
                    command,
                    cwd=REPOSITORY_ROOT,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                with self.assertRaises(subprocess.TimeoutExpired):
                    process.communicate(timeout=0.2)
                self.assertFalse((state / "promoted-overlay/active").exists())
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)["stable_id"], candidate["stable_id"])

    def test_retire_uses_legacy_review_and_prior_gates_only(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            run_id = "retire-legacy"
            create_closed_run(state, run_id)
            active = self.candidate("sage-knowledge-v1:retire.legacy", run_id)
            active_path = state / "active.json"
            active_path.write_text(json.dumps(active), encoding="utf-8")
            promote(active_path, run_id, installed_state_root=state)
            retired = copy.deepcopy(active)
            retired["status"] = "retired"
            retired["promotion"] = {
                "action": "retire",
                "reviewed": True,
                "review_evidence": ["verification:V1"],
                "expected_prior_sha256": active["stored_integrity_sha256"],
                "retirement_basis": "falsifier_fired",
                "retirement_reason": "The recorded falsifier fired.",
            }
            retired = prepare_candidate(retired)
            retired_path = state / "retired.json"
            retired_path.write_text(json.dumps(retired), encoding="utf-8")
            self.assertEqual(validate_record(retired, require_review=True), [])
            result = promote(retired_path, run_id, installed_state_root=state)
            self.assertEqual(result["action"], "retire")
            self.assertNotIn("evidence_class", result["review_result"])
            self.assertEqual(get_indexed([], state), [])

    def test_installed_promotion_is_default_indexed_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            reconcile_installed(SAGE_ROOT / "knowledge", state)
            run_id = "closed-promotion"
            create_closed_run(state, run_id)
            candidate = self.candidate("sage-knowledge-v1:handoff.verify", run_id)
            candidate_path = state / "candidate.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            first = promote(candidate_path, run_id, installed_state_root=state)
            self.assertEqual(first["destination"], "installed")
            self.assertTrue(first["changed"])
            self.assertEqual(first["selected_run_ids"], [run_id])
            self.assertEqual(first["review_result"]["reviewed"], True)
            self.assertIn(first["path"], first["changed_paths"])
            self.assertIn(first["index_path"], first["changed_paths"])
            self.assertEqual(len(first["source_hashes"]["record_file_sha256"]), 64)
            second = promote(candidate_path, run_id, installed_state_root=state)
            self.assertFalse(second["changed"])
            self.assertEqual(second["changed_paths"], [])
            indexed = get_indexed(["sage-knowledge-v1:handoff.verify"], state)
            self.assertEqual(indexed[0]["rule"], candidate["rule"])
            listed = run_light(state, "knowledge", "list")
            self.assertEqual(listed.returncode, 0, listed.stderr)
            list_entry = json.loads(listed.stdout)[0]
            self.assertNotIn("rule", list_entry)
            self.assertNotIn("falsifier", list_entry)
            self.assertEqual(list_entry["recognizer"], candidate["recognizer"])
            self.assertFalse((SAGE_ROOT / "knowledge/active").exists())

            active = state / "runs/active/still-running"
            active.mkdir(parents=True)
            (active / "run.json").write_text(json.dumps({"run_id": "still-running", "status": "running"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "runs are active"):
                promote(candidate_path, run_id, installed_state_root=state)

    def test_global_promotion_is_source_only_and_prints_follow_up(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "sage/knowledge").mkdir(parents=True)
            (source / "sage/install.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            for command in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "sage-test@example.invalid"],
                ["git", "config", "user.name", "Sage Test"],
                ["git", "add", "."],
                ["git", "commit", "-qm", "fixture"],
            ):
                result = subprocess.run(command, cwd=source, text=True, capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=source, text=True, capture_output=True, check=True,
            ).stdout.strip()
            state = root / "state"
            run_id = "global-closed"
            create_closed_run(state, run_id)
            candidate = self.candidate("sage-knowledge-v1:global.only", run_id)
            candidate_path = root / "candidate.json"
            candidate_path.write_text(json.dumps(candidate))
            result = promote(
                candidate_path,
                run_id,
                global_source_root=source,
                expected_source_revision=revision,
                installed_state_root=state,
            )
            self.assertEqual(result["destination"], "global")
            self.assertEqual(result["follow_up_install"], str(source / "sage/install.sh"))
            self.assertEqual(result["source_hashes"]["source_revision"], revision)
            self.assertTrue((source / "sage/knowledge/active").is_dir())
            self.assertFalse((state / "promoted-overlay").exists())

    def test_promotion_consolidates_multiple_closed_runs_only_after_explicit_inspection(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            first_run = "closed-one"
            second_run = "closed-two"
            create_closed_run(state, first_run)
            create_closed_run(state, second_run)
            inspected = inspect_closed_runs([first_run, second_run], installed_state_root=state)
            self.assertEqual(inspected["memory_class"], "closed_run_promotion_input")
            self.assertEqual([row["run_id"] for row in inspected["runs"]], [first_run, second_run])
            for row in inspected["runs"]:
                self.assertEqual(row["facts"][-1]["type"], "run.closed")
                self.assertTrue(all(len(value) == 64 for value in row["integrity"].values()))

            candidate = self.candidate("sage-knowledge-v1:multi.run", first_run)
            candidate["provenance"] = [
                f"run:{first_run}",
                f"run:{second_run}",
                f"artifact:{first_run}:ART-RECORD",
                f"artifact:{second_run}:ART-RECORD",
            ]
            candidate["promotion"]["review_evidence"] = [
                f"verification:{first_run}:V1",
                f"verification:{second_run}:V1",
            ]
            candidate["promotion"]["independent_refutation"] = [
                f"verification:{first_run}:V1",
            ]
            candidate = prepare_candidate(candidate)
            candidate_path = state / "multi-candidate.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            landed = promote(
                candidate_path,
                [first_run, second_run],
                installed_state_root=state,
            )
            self.assertEqual(landed["destination"], "installed")
            self.assertTrue(landed["changed"])
            self.assertEqual(get_indexed([candidate["stable_id"]], state)[0]["rule"], candidate["rule"])

            active = state / "runs/active/open-run"
            active.mkdir(parents=True)
            (active / "run.json").write_text(json.dumps({"run_id": "open-run", "status": "running"}))
            with self.assertRaisesRegex(ValueError, "runs are active"):
                inspect_closed_runs([first_run], installed_state_root=state)

    def test_promotion_rejects_forged_closed_state_and_terminal_active_state(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            run_id = "forged-closed"
            forged = state / "runs/closed" / run_id
            forged.mkdir(parents=True)
            (forged / "run.json").write_text(json.dumps({"run_id": run_id, "status": "completed"}))
            candidate_path = state / "candidate.json"
            candidate_path.write_text(json.dumps(self.candidate("sage-knowledge-v1:forged", run_id)))
            with self.assertRaisesRegex(ValueError, "invalid run artifact"):
                promote(candidate_path, run_id, installed_state_root=state)

            shutil.rmtree(forged)
            valid = json.loads((SAGE_ROOT / "artifacts/fixtures/valid/zero-delegation.json").read_text())
            valid["run_id"] = run_id
            active = state / "runs/active" / run_id
            active.mkdir(parents=True)
            (active / "run.json").write_text(json.dumps(valid))
            with self.assertRaisesRegex(ValueError, "runs are active"):
                promote(candidate_path, run_id, installed_state_root=state)

    def test_promotion_rejects_nonfactual_rows_in_a_closed_log(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            run_id = "closed-with-lesson"
            closed = create_closed_run(state, run_id)
            facts_path = closed / "facts.jsonl"
            facts_path.chmod(0o600)
            closing = json.loads(facts_path.read_text().strip())
            forged = {
                "schema_version": "1.0",
                "memory_class": "current_run",
                "sequence": 1,
                "recorded_at": closing["recorded_at"],
                "run_id": run_id,
                "type": "lesson.extracted",
                "classification": "internal",
                "payload": {"lesson": "must not exist during a run"},
            }
            closing["sequence"] = 2
            facts_path.write_text(
                json.dumps(forged) + "\n" + json.dumps(closing) + "\n",
                encoding="utf-8",
            )
            candidate = self.candidate("sage-knowledge-v1:forged.lesson", run_id)
            candidate_path = state / "candidate.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "allowlisted factual event"):
                promote(candidate_path, run_id, installed_state_root=state)

    def test_failed_promotion_restores_the_record_and_index(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            reconcile_installed(SAGE_ROOT / "knowledge", state)
            run_id = "closed-rollback"
            create_closed_run(state, run_id)
            candidate = self.candidate("sage-knowledge-v1:rollback.promotion", run_id)
            candidate_path = state / "candidate.json"
            candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
            target = state / "promoted-overlay/active" / record_filename(candidate["stable_id"])
            index_path = state / "promoted-index/index.json"
            prior_index = index_path.read_bytes()
            original_replace = os.replace
            replacements = 0

            def fail_index_replace(source: str, target_path: str) -> None:
                nonlocal replacements
                replacements += 1
                if replacements == 2:
                    raise OSError("forced index failure")
                original_replace(source, target_path)

            with mock.patch("sage.lib.common.os.replace", side_effect=fail_index_replace):
                with self.assertRaisesRegex(OSError, "forced index failure"):
                    promote(candidate_path, run_id, installed_state_root=state)
            self.assertFalse(target.exists())
            self.assertEqual(index_path.read_bytes(), prior_index)

    def test_equivalent_repository_promotion_is_a_noop_without_overlay_write(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            run_id = "already-canonical"
            create_closed_run(state, run_id)
            candidate = self.candidate("sage-knowledge-v1:already.canonical", run_id)
            repository = state / "knowledge-repository/active"
            repository.mkdir(parents=True)
            (repository / record_filename(candidate["stable_id"])).write_text(json.dumps(candidate))
            build_index(state)
            candidate_path = state / "candidate.json"
            candidate_path.write_text(json.dumps(candidate))
            result = promote(candidate_path, run_id, installed_state_root=state)
            self.assertFalse(result["changed"])
            self.assertEqual(result["reconciliation"], "already_canonical_in_repository")
            self.assertEqual(list((state / "promoted-overlay/active").glob("*.json")), [])

    def test_promotion_evidence_and_runtime_index_cannot_cross_memory_boundaries(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            state = Path(temporary)
            run_id = "evidence-bound"
            create_closed_run(state, run_id)
            forged = self.candidate("sage-knowledge-v1:unsupported.evidence", run_id)
            forged["provenance"] = [f"run:{run_id}", "artifact:DOES-NOT-EXIST"]
            forged["promotion"]["review_evidence"] = ["verification:FAKE"]
            forged = prepare_candidate(forged)
            candidate_path = state / "candidate.json"
            candidate_path.write_text(json.dumps(forged))
            with self.assertRaisesRegex(ValueError, "unresolved.*artifact"):
                promote(candidate_path, run_id, installed_state_root=state)

            record = self.candidate("sage-knowledge-v1:index.escape", run_id)
            escaped = state / "runs/closed/record.json"
            escaped.parent.mkdir(parents=True, exist_ok=True)
            escaped.write_text(json.dumps(record))
            index_dir = state / "promoted-index"
            index_dir.mkdir()
            (index_dir / "index.json").write_text(json.dumps({
                "schema_version": "1.0",
                "generated_at": "2026-09-01T00:00:00Z",
                "input_manifest_sha256": "0" * 64,
                "entries": [{
                    "stable_id": record["stable_id"],
                    "class": record["class"],
                    "status": record["status"],
                    "qualifier": record["qualifier"],
                    "recognizer": record["recognizer"],
                    "projection_sha256": record["stored_integrity_sha256"],
                    "source": "installed_overlay",
                    "locator": "runs/closed/record.json",
                }],
            }))
            with self.assertRaisesRegex(ValueError, "unsafe promoted-knowledge index entry"):
                get_indexed([record["stable_id"]], state)

    def test_knowledge_validation_matches_the_canonical_schema(self) -> None:
        base = self.candidate("sage-knowledge-v1:schema.bound", "closed")
        empty_suffix = copy.deepcopy(base)
        empty_suffix["stable_id"] = "sage-knowledge-v1:"
        empty_suffix = prepare_candidate(empty_suffix)
        self.assertTrue(validate_record(empty_suffix, require_review=True))

        invalid_local = copy.deepcopy(base)
        invalid_local["local"] = 7
        self.assertTrue(validate_record(invalid_local, require_review=True))

        missing_prior = copy.deepcopy(base)
        del missing_prior["promotion"]["expected_prior_sha256"]
        self.assertTrue(validate_record(missing_prior, require_review=True))

        leaked = copy.deepcopy(base)
        leaked["rule"] = "Persist Bearer abcdefghijklmnopqrstuvwxyz"
        leaked = prepare_candidate(leaked)
        self.assertTrue(any("privacy check" in issue for issue in validate_record(leaked, require_review=True)))

    def test_reconciliation_archives_equivalent_and_divergent_twins_idempotently(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary)
            source = root / "source-knowledge"
            active = source / "active"
            active.mkdir(parents=True)
            state = root / "state"
            overlay = state / "promoted-overlay/active"
            overlay.mkdir(parents=True)
            equivalent = self.candidate("sage-knowledge-v1:equivalent", "closed")
            canonical = self.candidate("sage-knowledge-v1:conflict", "closed")
            divergent = copy.deepcopy(canonical)
            divergent["rule"] = "Divergent installed-only rule retained for adjudication."
            divergent = prepare_candidate(divergent)
            (active / "equivalent.json").write_text(json.dumps(equivalent))
            (active / "conflict.json").write_text(json.dumps(canonical))
            (overlay / "equivalent.json").write_text(json.dumps(equivalent))
            (overlay / "conflict.json").write_text(json.dumps(divergent))
            first = reconcile_installed(source, state)
            self.assertEqual(
                {(row["stable_id"], row["outcome"]) for row in first["archived"]},
                {
                    ("sage-knowledge-v1:equivalent", "equivalent_archived"),
                    ("sage-knowledge-v1:conflict", "conflict_archived"),
                },
            )
            before = tree_sha256(state)
            second = reconcile_installed(source, state)
            self.assertEqual(second["archived"], [])
            self.assertEqual(tree_sha256(state), before)


class LifecycleTests(unittest.TestCase):
    def destinations(self, base: Path) -> dict[str, Path]:
        return {
            "skills_root": base / "skills",
            "bin_root": base / "bin",
            "data_root": base / "data/sage",
            "state_root": base / "state/sage",
            "backup_root": base / "backups",
        }

    def test_codex_lifecycle_entrypoints_live_under_sage_and_execute(self) -> None:
        for name in ("install.sh", "uninstall.sh"):
            wrapper = SAGE_ROOT / name
            self.assertTrue(os.access(wrapper, os.X_OK))
            self.assertIn("sage-lifecycle.py", wrapper.read_text(encoding="utf-8"))
        self.assertNotIn("sage-lifecycle.py", (REPOSITORY_ROOT / "install.sh").read_text(encoding="utf-8"))
        self.assertNotIn("sage-lifecycle.py", (REPOSITORY_ROOT / "uninstall.sh").read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            destinations = self.destinations(base)
            common = [
                "--skills-root", str(destinations["skills_root"]),
                "--bin-root", str(destinations["bin_root"]),
                "--data-root", str(destinations["data_root"]),
                "--state-root", str(destinations["state_root"]),
                "--backup-root", str(destinations["backup_root"]),
            ]
            installed = subprocess.run(
                [str(SAGE_ROOT / "install.sh"), *common],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(installed.returncode, 0, installed.stderr)
            removed = subprocess.run(
                [str(SAGE_ROOT / "uninstall.sh"), "--yes", *common],
                cwd=REPOSITORY_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(removed.returncode, 0, removed.stderr)

    def test_install_noop_dry_run_and_complete_restore(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            destinations = self.destinations(base)
            conflict = destinations["skills_root"] / "sage"
            conflict.mkdir(parents=True)
            original = conflict / "user.txt"
            original.write_bytes(b"unrelated-user-content\n")
            original_inode = conflict.stat().st_ino
            installed = install(repository=REPOSITORY_ROOT, **destinations)
            self.assertEqual(installed["operation"], "install")
            receipt = json.loads(Path(installed["receipt"]).read_text())
            self.assertEqual(validate_receipt(receipt, SAGE_ROOT), [])
            self.assertFalse(original.exists())
            installed_tree = tree_sha256(base)
            repeated = install(repository=REPOSITORY_ROOT, **destinations)
            self.assertEqual(repeated["operation"], "noop")
            self.assertEqual(tree_sha256(base), installed_tree)
            dry = uninstall(
                repository=REPOSITORY_ROOT,
                state_root=destinations["state_root"],
                yes=True,
                dry_run=True,
                keep_data=False,
            )
            self.assertEqual(dry["operation"], "uninstall-dry-run")
            self.assertEqual(tree_sha256(base), installed_tree)
            self.assertTrue(Path(installed["receipt"]).exists())
            output = base / "uninstall-receipt.json"
            removed = uninstall(
                repository=REPOSITORY_ROOT,
                state_root=destinations["state_root"],
                yes=True,
                dry_run=False,
                keep_data=False,
                receipt_output=output,
            )
            self.assertEqual(removed["operation"], "uninstall")
            self.assertEqual(original.read_bytes(), b"unrelated-user-content\n")
            self.assertEqual(conflict.stat().st_ino, original_inode)
            uninstall_receipt = json.loads(output.read_text())
            self.assertEqual(validate_receipt(uninstall_receipt, SAGE_ROOT, receipt), [])
            for path in (destinations["bin_root"] / "sage-light", destinations["data_root"], destinations["state_root"]):
                self.assertFalse(path.exists())

    def test_interrupted_install_recovers_displaced_user_content_before_retry(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            destinations = self.destinations(base)
            conflict = destinations["skills_root"] / "sage"
            conflict.mkdir(parents=True)
            user_file = conflict / "user.txt"
            user_file.write_bytes(b"irreplaceable\n")
            original_inode = conflict.stat().st_ino
            arguments = [
                "install", "--source-root", str(REPOSITORY_ROOT),
                "--skills-root", str(destinations["skills_root"]),
                "--bin-root", str(destinations["bin_root"]),
                "--data-root", str(destinations["data_root"]),
                "--state-root", str(destinations["state_root"]),
                "--backup-root", str(destinations["backup_root"]),
            ]
            crashed = run_lifecycle(*arguments, environment={"SAGE_TEST_CRASH_AFTER_REPLACEMENTS": "1"})
            self.assertEqual(crashed.returncode, 86, crashed.stderr)
            self.assertFalse(user_file.exists())
            recovery_path = next(destinations["state_root"].parent.glob(".sage-lifecycle-recovery-*.json"))
            recovery = json.loads(recovery_path.read_text())
            self.assertEqual(
                [row["phase"] for row in recovery["durable_journal"]],
                ["preflight_complete", "backups_durable", "stage_verified"],
            )
            self.assertEqual(
                recovery["intended_receipt_sha256"],
                recovery["intended_receipt"]["operation"]["intended_receipt_sha256"],
            )
            recovered = run_lifecycle(*arguments)
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            output = base / "uninstall-receipt.json"
            uninstall(
                repository=REPOSITORY_ROOT,
                state_root=destinations["state_root"],
                yes=True,
                dry_run=False,
                keep_data=False,
                receipt_output=output,
            )
            self.assertEqual(user_file.read_bytes(), b"irreplaceable\n")
            self.assertEqual(conflict.stat().st_ino, original_inode)

    def test_recovery_blocks_replaced_root_even_when_owner_marker_is_copied(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            destinations = self.destinations(base)
            arguments = [
                "install", "--source-root", str(REPOSITORY_ROOT),
                "--skills-root", str(destinations["skills_root"]),
                "--bin-root", str(destinations["bin_root"]),
                "--data-root", str(destinations["data_root"]),
                "--state-root", str(destinations["state_root"]),
                "--backup-root", str(destinations["backup_root"]),
            ]
            crashed = run_lifecycle(*arguments, environment={"SAGE_TEST_CRASH_AFTER_REPLACEMENTS": "1"})
            self.assertEqual(crashed.returncode, 86, crashed.stderr)
            recovery_path = next(destinations["state_root"].parent.glob(".sage-lifecycle-recovery-*.json"))
            recovery = json.loads(recovery_path.read_text())
            marker = next(row["marker"] for row in recovery["entries"] if row["entry_id"] == "skill.sage")
            original_root = destinations["skills_root"].with_name("skills-original")
            destinations["skills_root"].rename(original_root)
            forged = destinations["skills_root"] / "sage"
            forged.mkdir(parents=True)
            (forged / ".sage-owner.json").write_text(json.dumps({"schema_version": "1.0", "marker": marker}))
            valuable = forged / "valuable.txt"
            valuable.write_text("must survive")
            refused = run_lifecycle(*arguments)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("root identity changed", refused.stderr)
            self.assertEqual(valuable.read_text(), "must survive")

    def test_recovery_preserves_substituted_stage_and_snapshot_container(self) -> None:
        def install_arguments(destinations: dict[str, Path]) -> list[str]:
            return [
                "install", "--source-root", str(REPOSITORY_ROOT),
                "--skills-root", str(destinations["skills_root"]),
                "--bin-root", str(destinations["bin_root"]),
                "--data-root", str(destinations["data_root"]),
                "--state-root", str(destinations["state_root"]),
                "--backup-root", str(destinations["backup_root"]),
            ]

        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            stage_destinations = self.destinations(base / "stage")
            crashed = run_lifecycle(
                *install_arguments(stage_destinations),
                environment={"SAGE_TEST_CRASH_AT_PHASE": "preflight_complete"},
            )
            self.assertEqual(crashed.returncode, 86, crashed.stderr)
            recovery_path = next(stage_destinations["state_root"].parent.glob(".sage-lifecycle-recovery-*.json"))
            recovery = json.loads(recovery_path.read_text())
            stage = Path(next(row["stage"] for row in recovery["entries"] if row["entry_id"] == "skill.sage"))
            shutil.rmtree(stage)
            stage.mkdir()
            stage_value = stage / "user-data.txt"
            stage_value.write_text("preserve me")
            retried = run_lifecycle(*install_arguments(stage_destinations))
            self.assertNotEqual(retried.returncode, 0)
            self.assertTrue(stage_value.is_file())

            snapshot_destinations = self.destinations(base / "snapshot")
            crashed = run_lifecycle(
                *install_arguments(snapshot_destinations),
                environment={"SAGE_TEST_CRASH_AT_PHASE": "replacement_applied"},
            )
            self.assertEqual(crashed.returncode, 86, crashed.stderr)
            recovery_path = next(snapshot_destinations["state_root"].parent.glob(".sage-lifecycle-recovery-*.json"))
            recovery = json.loads(recovery_path.read_text())
            container = snapshot_destinations["backup_root"] / f".sage-recovery-{recovery['operation_id']}"
            container.mkdir()
            snapshot_value = container / "user-data.txt"
            snapshot_value.write_text("preserve me too")
            retried = run_lifecycle(*install_arguments(snapshot_destinations))
            self.assertNotEqual(retried.returncode, 0)
            self.assertTrue(snapshot_value.is_file())

    def test_recovery_cleanup_capture_blocks_verify_delete_races(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            stage_destinations = self.destinations(base / "stage-race")
            arguments = [
                "install", "--source-root", str(REPOSITORY_ROOT),
                "--skills-root", str(stage_destinations["skills_root"]),
                "--bin-root", str(stage_destinations["bin_root"]),
                "--data-root", str(stage_destinations["data_root"]),
                "--state-root", str(stage_destinations["state_root"]),
                "--backup-root", str(stage_destinations["backup_root"]),
            ]
            crashed = run_lifecycle(*arguments, environment={"SAGE_TEST_CRASH_AT_PHASE": "preflight_complete"})
            self.assertEqual(crashed.returncode, 86, crashed.stderr)
            real_stage_verify = lifecycle_module._verify_recovery_stage
            raced_stage: Path | None = None

            def race_stage(path: Path, row: dict[str, object], *, require_original_path: bool = True) -> None:
                nonlocal raced_stage
                real_stage_verify(path, row, require_original_path=require_original_path)
                if raced_stage is None and not require_original_path:
                    raced_stage = Path(str(row["stage"]))
                    raced_stage.mkdir()
                    (raced_stage / "raced-user-data.txt").write_text("must survive")

            with mock.patch("sage.lib.lifecycle._verify_recovery_stage", side_effect=race_stage):
                with self.assertRaisesRegex(ValueError, "reappeared during cleanup"):
                    install(repository=REPOSITORY_ROOT, **stage_destinations)
            self.assertIsNotNone(raced_stage)
            self.assertEqual((raced_stage / "raced-user-data.txt").read_text(), "must survive")

            quarantine_destinations = self.destinations(base / "quarantine-race")
            arguments = [
                "install", "--source-root", str(REPOSITORY_ROOT),
                "--skills-root", str(quarantine_destinations["skills_root"]),
                "--bin-root", str(quarantine_destinations["bin_root"]),
                "--data-root", str(quarantine_destinations["data_root"]),
                "--state-root", str(quarantine_destinations["state_root"]),
                "--backup-root", str(quarantine_destinations["backup_root"]),
            ]
            crashed = run_lifecycle(*arguments, environment={"SAGE_TEST_CRASH_AT_PHASE": "preflight_complete"})
            self.assertEqual(crashed.returncode, 86, crashed.stderr)
            verification_calls = 0
            raced_quarantine: Path | None = None

            def race_quarantine(path: Path, row: dict[str, object], *, require_original_path: bool = True) -> None:
                nonlocal verification_calls, raced_quarantine
                real_stage_verify(path, row, require_original_path=require_original_path)
                if not require_original_path and row["entry_id"] == "skill.sage":
                    verification_calls += 1
                    if verification_calls == 2:
                        aside = path.with_name(path.name + ".authentic-aside")
                        path.rename(aside)
                        path.mkdir()
                        (path / "raced-user-data.txt").write_text("must survive quarantine swap")
                        raced_quarantine = path

            with mock.patch("sage.lib.lifecycle._verify_recovery_stage", side_effect=race_quarantine):
                with self.assertRaisesRegex(ValueError, "quarantine was swapped"):
                    install(repository=REPOSITORY_ROOT, **quarantine_destinations)
            self.assertIsNotNone(raced_quarantine)
            self.assertEqual(
                (raced_quarantine / "raced-user-data.txt").read_text(),
                "must survive quarantine swap",
            )

            source = base / "source"
            shutil.copytree(SAGE_ROOT, source / "sage", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
            snapshot_destinations = self.destinations(base / "snapshot-race")
            install(repository=source, **snapshot_destinations)
            with (source / "sage/README.md").open("a", encoding="utf-8") as handle:
                handle.write("\nSnapshot cleanup race fixture.\n")
            arguments = [
                "install", "--source-root", str(source),
                "--skills-root", str(snapshot_destinations["skills_root"]),
                "--bin-root", str(snapshot_destinations["bin_root"]),
                "--data-root", str(snapshot_destinations["data_root"]),
                "--state-root", str(snapshot_destinations["state_root"]),
                "--backup-root", str(snapshot_destinations["backup_root"]),
            ]
            crashed = run_lifecycle(*arguments, environment={"SAGE_TEST_CRASH_AT_PHASE": "health_verified"})
            self.assertEqual(crashed.returncode, 86, crashed.stderr)
            recovery_path = next(snapshot_destinations["state_root"].parent.glob(".sage-lifecycle-recovery-*.json"))
            recovery = json.loads(recovery_path.read_text())
            public_container = snapshot_destinations["backup_root"] / f".sage-recovery-{recovery['operation_id']}"
            real_snapshot_verify = lifecycle_module._verify_recovery_snapshot_container
            raced_snapshot: Path | None = None

            def race_snapshot(path: Path, record: dict[str, object], *, require_original_path: bool = True) -> None:
                nonlocal raced_snapshot
                real_snapshot_verify(path, record, require_original_path=require_original_path)
                if raced_snapshot is None and not require_original_path:
                    raced_snapshot = public_container
                    raced_snapshot.mkdir()
                    (raced_snapshot / "raced-user-data.txt").write_text("must survive too")

            with mock.patch("sage.lib.lifecycle._verify_recovery_snapshot_container", side_effect=race_snapshot):
                with self.assertRaisesRegex(ValueError, "reappeared during cleanup"):
                    install(repository=source, **snapshot_destinations)
            self.assertIsNotNone(raced_snapshot)
            self.assertEqual((raced_snapshot / "raced-user-data.txt").read_text(), "must survive too")

    def test_interrupted_update_recovers_at_every_durable_journal_phase(self) -> None:
        phases = (
            "preflight_complete",
            "backups_durable",
            "stage_verified",
            "replacement_applied",
            "health_verified",
            "receipt_committed",
            "cleanup_complete",
        )
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            source = base / "source"
            shutil.copytree(SAGE_ROOT, source / "sage", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
            scenarios: list[tuple[str, dict[str, Path], bytes, Path]] = []
            for phase in phases:
                destinations = self.destinations(base / phase)
                installed = install(repository=source, **destinations)
                prior_bytes = Path(installed["receipt"]).read_bytes()
                preserved = destinations["state_root"] / "runs/active/preserved/facts.jsonl"
                preserved.parent.mkdir(parents=True)
                preserved.write_text('{"preserve":true}\n')
                scenarios.append((phase, destinations, prior_bytes, preserved))
            with (source / "sage/README.md").open("a", encoding="utf-8") as handle:
                handle.write("\nEvery-phase update fixture.\n")

            for phase, destinations, prior_bytes, preserved in scenarios:
                with self.subTest(phase=phase):
                    arguments = [
                        "install", "--source-root", str(source),
                        "--skills-root", str(destinations["skills_root"]),
                        "--bin-root", str(destinations["bin_root"]),
                        "--data-root", str(destinations["data_root"]),
                        "--state-root", str(destinations["state_root"]),
                        "--backup-root", str(destinations["backup_root"]),
                    ]
                    crashed = run_lifecycle(*arguments, environment={"SAGE_TEST_CRASH_AT_PHASE": phase})
                    self.assertEqual(crashed.returncode, 86, crashed.stderr)
                    current_path = destinations["state_root"] / "lifecycle/current.json"
                    recovery_path = next(destinations["state_root"].parent.glob(".sage-lifecycle-recovery-*.json"))
                    recovery = json.loads(recovery_path.read_text())
                    self.assertEqual(recovery["durable_journal"][-1]["phase"], phase)
                    if phase in {"receipt_committed", "cleanup_complete"}:
                        checkpoint = json.loads(current_path.read_text())
                        self.assertEqual(checkpoint["operation"]["operation_id"], recovery["operation_id"])
                        self.assertEqual(checkpoint["operation"]["state"], "pending")
                        self.assertEqual(checkpoint["operation"]["journal"][-1]["phase"], "receipt_committed")
                    else:
                        self.assertEqual(current_path.read_bytes(), prior_bytes)
                    retried = run_lifecycle(*arguments)
                    self.assertEqual(retried.returncode, 0, retried.stderr)
                    self.assertEqual(json.loads(retried.stdout)["operation"], "update")
                    self.assertEqual(preserved.read_text(), '{"preserve":true}\n')

    def test_paths_with_spaces_unrelated_bytes_repeated_uninstall_and_hardlink_refusal(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary) / "destinations with spaces"
            destinations = self.destinations(base)
            unrelated = destinations["skills_root"] / "unrelated.txt"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_bytes(b"byte-identical unrelated content\n")
            installed = install(repository=REPOSITORY_ROOT, **destinations)
            prior = json.loads(Path(installed["receipt"]).read_text())
            output = base.parent / "space-uninstall.json"
            removed = uninstall(
                repository=REPOSITORY_ROOT,
                state_root=destinations["state_root"],
                yes=True,
                dry_run=False,
                keep_data=False,
                receipt_output=output,
            )
            self.assertEqual(unrelated.read_bytes(), b"byte-identical unrelated content\n")
            receipt = json.loads(output.read_text())
            self.assertEqual(validate_receipt(receipt, SAGE_ROOT, prior), [])
            phases = [row["phase"] for row in receipt["operation"]["journal"]]
            self.assertIn("admissions_stopped", phases)
            self.assertIn("processes_stopped", phases)
            repeated = uninstall(
                repository=REPOSITORY_ROOT,
                state_root=destinations["state_root"],
                yes=True,
                dry_run=False,
                keep_data=False,
            )
            self.assertEqual(repeated["operation"], "noop")
            self.assertEqual(removed["operation"], "uninstall")

            hardlink_destinations = self.destinations(base.parent / "hardlink")
            hardlink_destinations["bin_root"].mkdir(parents=True)
            original = base.parent / "hardlink-user-file"
            original.write_text("shared inode")
            linked_target = hardlink_destinations["bin_root"] / "sage-light"
            os.link(original, linked_target)
            with self.assertRaisesRegex(ValueError, "hard-linked"):
                install(repository=REPOSITORY_ROOT, **hardlink_destinations)
            self.assertEqual(original.read_text(), "shared inode")
            self.assertEqual(linked_target.stat().st_ino, original.stat().st_ino)

    def test_interrupted_uninstall_resumes_from_external_recovery_record(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            destinations = self.destinations(base)
            conflict = destinations["skills_root"] / "sage"
            conflict.mkdir(parents=True)
            user_file = conflict / "user.txt"
            user_file.write_bytes(b"restore-on-resume\n")
            original_inode = conflict.stat().st_ino
            install(repository=REPOSITORY_ROOT, **destinations)
            output = base / "uninstall-receipt.json"
            arguments = [
                "uninstall", "--source-root", str(REPOSITORY_ROOT), "--yes",
                "--skills-root", str(destinations["skills_root"]),
                "--bin-root", str(destinations["bin_root"]),
                "--data-root", str(destinations["data_root"]),
                "--state-root", str(destinations["state_root"]),
                "--backup-root", str(destinations["backup_root"]),
                "--receipt-output", str(output),
            ]
            crashed = run_lifecycle(*arguments, environment={"SAGE_TEST_CRASH_AFTER_UNINSTALL_MUTATIONS": "1"})
            self.assertEqual(crashed.returncode, 86, crashed.stderr)
            self.assertFalse(conflict.exists())
            resumed = run_lifecycle(*arguments)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(user_file.read_bytes(), b"restore-on-resume\n")
            self.assertEqual(conflict.stat().st_ino, original_inode)
            self.assertTrue(output.is_file())

    def test_keep_data_exports_only_declared_runtime_classes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            destinations = self.destinations(base)
            installed = install(repository=REPOSITORY_ROOT, **destinations)
            prior = json.loads(Path(installed["receipt"]).read_text())
            run_fact = destinations["state_root"] / "runs/closed/preserved/facts.jsonl"
            run_fact.parent.mkdir(parents=True)
            run_fact.write_text('{"preserved":true}\n')
            retained_candidate = PromotionTests().candidate("sage-knowledge-v1:retained.local", "closed")
            overlay = destinations["state_root"] / "promoted-overlay/active" / record_filename(retained_candidate["stable_id"])
            overlay.write_text(json.dumps(retained_candidate))
            output = base / "keep-data-uninstall.json"
            removed = uninstall(
                repository=REPOSITORY_ROOT,
                state_root=destinations["state_root"],
                yes=True,
                dry_run=False,
                keep_data=True,
                receipt_output=output,
            )
            self.assertTrue(removed["keep_data"])
            self.assertTrue(run_fact.is_file())
            self.assertTrue(overlay.is_file())
            self.assertTrue((destinations["state_root"] / "retention-receipt.json").is_file())
            self.assertFalse((destinations["state_root"] / "lifecycle").exists())
            self.assertFalse((destinations["state_root"] / "knowledge-repository").exists())
            self.assertFalse(destinations["data_root"].exists())
            uninstall_receipt = json.loads(output.read_text())
            self.assertEqual(validate_receipt(uninstall_receipt, SAGE_ROOT, prior), [])
            roots = {row["root_id"]: Path(row["canonical_path"]) for row in uninstall_receipt["roots"]}
            for entry_id in uninstall_receipt["preservation"]["keep_data_entry_ids"]:
                entry = next(row for row in uninstall_receipt["entries"] if row["entry_id"] == entry_id)
                marker = json.loads((roots[entry["root_id"]] / entry["relative_path"] / ".sage-owner.json").read_text())
                self.assertEqual(marker["export_owner"], "user")

    def test_failed_update_restores_mutable_overlay_index_and_prior_receipt(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            source = base / "source"
            shutil.copytree(SAGE_ROOT, source / "sage", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
            destinations = self.destinations(base / "install")
            installed = install(repository=source, **destinations)
            current_path = Path(installed["receipt"])
            rollback_candidate = PromotionTests().candidate("sage-knowledge-v1:rollback.local", "closed")
            overlay = destinations["state_root"] / "promoted-overlay/active" / record_filename(rollback_candidate["stable_id"])
            overlay.write_text(json.dumps(rollback_candidate))
            reconcile_installed(source / "sage/knowledge", destinations["state_root"])
            prior_receipt = current_path.read_bytes()
            overlay_hash = tree_sha256(destinations["state_root"] / "promoted-overlay")
            index_hash = tree_sha256(destinations["state_root"] / "promoted-index")
            with (source / "sage/README.md").open("a", encoding="utf-8") as handle:
                handle.write("\nRollback fixture.\n")
            with mock.patch("sage.lib.lifecycle._health_check", side_effect=ValueError("forced post-reconcile failure")):
                with self.assertRaisesRegex(ValueError, "forced post-reconcile failure"):
                    install(repository=source, **destinations)
            self.assertEqual(current_path.read_bytes(), prior_receipt)
            self.assertEqual(tree_sha256(destinations["state_root"] / "promoted-overlay"), overlay_hash)
            self.assertEqual(tree_sha256(destinations["state_root"] / "promoted-index"), index_hash)
            retried = install(repository=source, **destinations)
            self.assertEqual(retried["operation"], "update")

    def test_symlink_destination_and_protected_source_child_are_rejected_without_writes(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            destinations = self.destinations(base / "destinations")
            real_skills = base / "real-skills"
            real_skills.mkdir()
            destinations["skills_root"].parent.mkdir(parents=True)
            destinations["skills_root"].symlink_to(real_skills, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                install(repository=REPOSITORY_ROOT, **destinations)
            self.assertEqual(list(real_skills.iterdir()), [])
            self.assertFalse(destinations["state_root"].exists())

            protected = REPOSITORY_ROOT / f".phase1-protected-{os.getpid()}"
            self.assertFalse(protected.exists())
            safe = self.destinations(base / "safe")
            safe["skills_root"] = protected
            with self.assertRaisesRegex(ValueError, "protected source checkout"):
                install(repository=REPOSITORY_ROOT, **safe)
            self.assertFalse(protected.exists())

    def test_update_preserves_current_state_and_installed_overlay(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            base = Path(temporary)
            source = base / "source"
            _copy_ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
            shutil.copytree(SAGE_ROOT, source / "sage", ignore=_copy_ignore)
            destinations = self.destinations(base / "install")
            first = install(repository=source, **destinations)
            prior = json.loads(Path(first["receipt"]).read_text())
            run_fact = destinations["state_root"] / "runs/active/preserved/facts.jsonl"
            run_fact.parent.mkdir(parents=True)
            run_fact.write_bytes(b'{"fact":"preserve"}\n')
            local_candidate = PromotionTests().candidate("sage-knowledge-v1:local.only", "closed")
            overlay = destinations["state_root"] / "promoted-overlay/active" / record_filename(local_candidate["stable_id"])
            overlay.write_text(json.dumps(local_candidate), encoding="utf-8")
            with (source / "sage/README.md").open("a", encoding="utf-8") as handle:
                handle.write("\nUpdate-fixture revision.\n")
            updated = install(repository=source, **destinations)
            self.assertEqual(updated["operation"], "update")
            self.assertEqual(run_fact.read_bytes(), b'{"fact":"preserve"}\n')
            self.assertTrue(overlay.exists())
            current = json.loads(Path(updated["receipt"]).read_text())
            self.assertEqual(validate_receipt(current, source / "sage", prior), [])
            output = base / "update-uninstall.json"
            removed = uninstall(
                repository=source,
                state_root=destinations["state_root"],
                yes=True,
                dry_run=False,
                keep_data=False,
                receipt_output=output,
            )
            self.assertEqual(removed["operation"], "uninstall")


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pilot = load_script(SAGE_ROOT / "evaluation/phase-1/pilot.py", "sage_phase1_pilot")
        cls.scorer = load_script(SAGE_ROOT / "evaluation/phase-1/score-pilot.py", "sage_phase1_scorer")

    def test_frozen_pilot_inputs_and_baseline_are_intact(self) -> None:
        report = self.pilot.verify_frozen()
        self.assertTrue(report["passed"], report["issues"])
        self.assertEqual(report["task_count"], 20)

    def test_unqualified_budget_and_usage_telemetry_do_not_pass_hard_cap(self) -> None:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary:
            root = Path(temporary) / "v2"
            root.mkdir(parents=True)
            (root / "ThreadGoalSetParams.json").write_text(json.dumps({
                "properties": {"tokenBudget": {"type": ["integer", "null"], "format": "int64"}},
            }))
            (root / "ThreadTokenUsageUpdatedNotification.json").write_text(json.dumps({
                "definitions": {
                    "TokenUsageBreakdown": {"properties": {"inputTokens": {}, "outputTokens": {}, "totalTokens": {}}},
                    "ThreadTokenUsage": {"properties": {"modelContextWindow": {}}},
                },
            }))
            capabilities = self.pilot.inspect_capabilities(Path(temporary))
            self.assertFalse(capabilities["hard_250k_normalized_arm_cap_proved"])
            self.assertEqual(capabilities["root_context_occupancy_fields"], [])

    def test_frozen_gate_calculator_uses_all_pairs(self) -> None:
        pairs = []
        for task_id in self.scorer.TASK_IDS:
            pairs.append({
                "task_id": task_id,
                "control": {"score": 90, "normalized_total_tokens": 1000, "interventions": 1, "wall_seconds": 10},
                "treatment": {"score": 90, "normalized_total_tokens": 1000, "interventions": 0, "wall_seconds": 10},
                "treatment_miss": False,
                "treatment_only_safety_regression": False,
                "unexplained_semantic_regression": False,
            })
        result = self.scorer.score({"pairs": pairs})
        self.assertTrue(result["policy_value_passed"])
        self.assertFalse(result["managed_need_passed"])
        self.assertEqual(result["decision"], "ship_light_and_stop_runtime_program")
        overridden = self.scorer.score({"pairs": pairs, "wall_time_eligible_task_ids": []})
        self.assertEqual(overridden["wall_time_coverage"], 19)
        invalid = copy.deepcopy(pairs)
        invalid[0]["control"]["normalized_total_tokens"] = -1
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            self.scorer.score({"pairs": invalid})


if __name__ == "__main__":
    unittest.main()
