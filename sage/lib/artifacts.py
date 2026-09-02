"""Public validation and deterministic rendering for Sage artifact schema v1."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from .common import atomic_write_bytes, atomic_write_json, canonical_sha256, load_json, sha256_bytes


GENERATOR_VERSION = "sage-light-renderer/1.3"
CLASSIFICATION_ORDER = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}


def _load_phase0_checker(sage_root: Path) -> ModuleType:
    checker_path = sage_root / "scripts/check-phase0.py"
    spec = importlib.util.spec_from_file_location("sage_phase0_checker", checker_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load artifact checker from {checker_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_run(run: dict[str, Any], sage_root: Path) -> list[str]:
    checker = _load_phase0_checker(sage_root)
    schema = checker.load_json(sage_root / "artifacts/schemas/sage-artifact-v1.schema.json")
    issues = checker.validate_schema(run, schema)
    if not issues:
        issues.extend(checker.artifact_semantic_issues(run))
    return [issue.render() for issue in issues]


def load_and_validate(path: Path, sage_root: Path) -> dict[str, Any]:
    run = load_json(path)
    if not isinstance(run, dict):
        raise ValueError("run artifact must be one JSON object")
    issues = validate_run(run, sage_root)
    if issues:
        raise ValueError("invalid run artifact:\n" + "\n".join(issues))
    return run


def validate_knowledge_record_schema(record: Any, sage_root: Path) -> list[str]:
    """Validate the exact canonical representation of one promoted-knowledge record."""
    checker = _load_phase0_checker(sage_root)
    schema = checker.load_json(sage_root / "artifacts/schemas/knowledge-record-v1.schema.json")
    return [issue.render() for issue in checker.validate_schema(record, schema)]


def validate_handoff_schema(handoff: Any, sage_root: Path) -> list[str]:
    checker = _load_phase0_checker(sage_root)
    schema = checker.load_json(sage_root / "artifacts/schemas/sage-handoff-v1.schema.json")
    return [issue.render() for issue in checker.validate_schema(handoff, schema)]


def validate_receipt(
    receipt: dict[str, Any],
    sage_root: Path,
    prior_receipt: dict[str, Any] | None = None,
) -> list[str]:
    """Validate an ownership receipt against both schema and lifecycle semantics."""
    checker = _load_phase0_checker(sage_root)
    schema = checker.load_json(sage_root / "artifacts/schemas/ownership-receipt-v1.schema.json")
    issues = checker.validate_schema(receipt, schema)
    if not issues:
        issues.extend(checker.receipt_semantic_issues(receipt, prior_receipt))
    return [issue.render() for issue in issues]


def render_projection(run: dict[str, Any]) -> dict[str, Any]:
    """Return the non-circular state projection bound by rendered_run_record."""
    projection = copy.deepcopy(run)
    rendered = projection.get("rendered_run_record", {})
    rendered.pop("source_state_sha256", None)
    rendered.pop("generator_version", None)
    rendered_id = rendered.get("artifact_id")
    for artifact in projection.get("artifacts", []):
        if artifact.get("artifact_id") == rendered_id:
            artifact.pop("sha256", None)
            artifact.pop("locator", None)
    return projection


def _line_list(values: list[str], empty: str = "none") -> str:
    return ", ".join(values) if values else empty


def _render_bound(value: Any) -> str:
    return "uncommitted" if value is None else str(value)


def _render_classification(run: dict[str, Any]) -> str:
    rendered_id = run["rendered_run_record"]["artifact_id"]
    values = ["internal"]
    values.extend(
        artifact["classification"]
        for artifact in run["artifacts"]
        if artifact["artifact_id"] != rendered_id
    )
    values.extend(pointer["classification"] for brief in run["briefs"] for pointer in brief["inputs"])
    return max(values, key=CLASSIFICATION_ORDER.__getitem__)


def render_markdown(run: dict[str, Any], state_sha256: str) -> bytes:
    plan = run["plan"]
    current = next(item for item in plan["revisions"] if item["revision"] == plan["current_revision"])
    lines = [
        f"# Sage run {run['run_id']}",
        "",
        f"- Status: `{run['status']}`",
        f"- Objective: {run['objective']}",
        f"- Policy: `{run['policy_version']}`",
        f"- Current plan revision: `{plan['current_revision']}` ({current['kind']})",
        f"- Source-state SHA-256: `{state_sha256}`",
        "",
        "## Plan",
        "",
        f"Reason: {current['reason']}",
        f"Admission: `{current['admission_policy']['profile']}` / `{current['admission_policy']['control_strength']}`; usage `{current['admission_policy']['usage_provenance']}`.",
        "Bounds: "
        f"{_render_bound(current['bounds']['max_units'])} units, "
        f"{_render_bound(current['bounds']['max_attempts_per_unit'])} attempts/unit, "
        f"{_render_bound(current['bounds']['max_concurrency'])} concurrent, "
        f"{_render_bound(current['bounds']['max_plan_revisions'])} revisions, "
        f"{_render_bound(current['bounds']['max_admission_seconds'])} admission seconds, "
        f"{_render_bound(current['bounds']['max_admitted_agents'])} agents, "
        f"{_render_bound(current['bounds']['no_progress_revision_limit'])} no-progress revisions.",
        "",
    ]
    for unit in current["units"]:
        lines.extend(
            [
                f"### {unit['unit_id']} r{unit['unit_spec_revision']}",
                "",
                f"- Owner/effect: `{unit['owner']}` / `{unit['effect_class']}`",
                f"- Objective: {unit['objective']}",
                f"- Done when: {unit['done_when']}",
                f"- Dependencies: {_line_list(unit['dependencies'])}",
                f"- Required capabilities: {_line_list(unit['required_capabilities'])}",
                "- Criteria: " + _line_list([
                    f"{criterion['criterion_id']} ({criterion['evidence_class']}): {criterion['text']}"
                    for criterion in unit["acceptance_criteria"]
                ]),
                "",
            ]
        )
    lines.extend(["## Attempts and results", ""])
    if not run["attempts"]:
        lines.extend(["No attempts recorded.", ""])
    results = {item["result_id"]: item for item in run["results"]}
    for attempt in run["attempts"]:
        placement = attempt["effective_placement"]
        lines.append(
            f"- `{attempt['attempt_id']}`: `{attempt['state']}`; requested "
            f"`{placement['requested_model']}`/{placement['requested_effort']}, effective "
            f"`{placement['effective_model']}`/{placement['effective_effort']}."
        )
        if attempt.get("result_id") in results:
            result = results[attempt["result_id"]]
            lines.append(f"  Result (`{result['acceptance']}`): {result['result']}")
            lines.append(f"  Files changed: {_line_list(result['files_changed'])}.")

    lines.extend(["", "## Artifacts", ""])
    rendered_id = run["rendered_run_record"]["artifact_id"]
    for artifact in run["artifacts"]:
        if artifact["artifact_id"] == rendered_id:
            # The Markdown cannot contain its own content hash or final locator
            # without becoming circular. Both values remain bound in run.json.
            lines.append(
                f"- `{artifact['artifact_id']}` ({artifact['kind']}, `{artifact['adoption']}`): "
                "this deterministic projection; locator and SHA-256 are bound in structured state"
            )
        else:
            lines.append(
                f"- `{artifact['artifact_id']}` ({artifact['kind']}, `{artifact['adoption']}`): "
                f"{artifact['locator']} · `{artifact['sha256']}`"
            )
    if not run["artifacts"]:
        lines.append("None recorded.")

    lines.extend(["", "## Assumptions and decisions", ""])
    for assumption in run["assumptions"]:
        lines.append(
            f"- Assumption `{assumption['assumption_id']}` (`{assumption['status']}`): "
            f"{assumption['choice']} Falsifier: {assumption['falsifier']}"
        )
    for decision in run["decisions"]:
        lines.append(f"- Decision `{decision['decision_id']}` ({decision['kind']}): {decision['decision']} — {decision['reason']}")
    if not run["assumptions"] and not run["decisions"]:
        lines.append("None recorded.")

    lines.extend(["", "## Findings, dispositions, and gaps", ""])
    dispositions = {item["finding_id"]: item for item in run["dispositions"]}
    for finding in run["findings"]:
        disposition = dispositions.get(finding["finding_id"])
        disposition_text = (
            f"{disposition['decision']}/{disposition['status']}"
            if disposition is not None else "undispositioned"
        )
        lines.append(
            f"- Finding `{finding['finding_id']}` ({finding['severity']}, {finding['confidence']}; "
            f"{disposition_text}): {finding['failure_mode']}"
        )
    for gap in run["gaps"]:
        lines.append(f"- Gap `{gap['gap_id']}` (`{gap['status']}`): {gap['description']}")
    if not run["findings"] and not run["gaps"]:
        lines.append("None recorded.")

    lines.extend(["", "## Verification", ""])
    for verification in run["verifications"]:
        lines.append(
            f"- `{verification['verification_id']}`: `{verification['verdict']}` for "
            f"`{verification['subject_kind']}:{verification['subject_id']}` / `{verification['criterion_id']}` "
            f"by {verification['verified_by']} using {verification['method']}."
        )
    if not run["verifications"]:
        lines.append("No verification rows recorded.")
    coordination = run["coordination_outcome"]
    completion = run["completion"]
    lines.extend(
        [
            "",
            "## Coordination outcome",
            "",
            f"`{coordination['state']}` — {coordination['assessment']}",
            "",
            f"Interventions: {coordination['interventions']}; protocol failures: {coordination['protocol_failures']}.",
            f"Critical-path effect: {coordination['critical_path_effect']}",
            f"Root-context effect: {coordination['root_context_effect']}",
            "",
            "## Completion",
            "",
            f"State: `{completion['state']}`. {completion['claim']}",
            f"Criteria/checks/findings/scope: `{completion['criteria_status']}` / `{completion['checks_status']}` / `{completion['findings_status']}` / `{completion['scope_status']}`.",
            "",
            f"Deliverable: {completion['deliverable']}",
            "",
            f"Human items: {_line_list(completion['human_items'])}.",
            "",
            "## Complete structured projection",
            "",
            "The JSON below is the complete non-circular projection bound by the source-state hash above.",
            "",
            "```json",
            json.dumps(render_projection(run), ensure_ascii=False, sort_keys=True, indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def render_run(run_path: Path, output_path: Path, sage_root: Path, update_state: bool = True) -> tuple[str, str]:
    run = load_and_validate(run_path, sage_root)
    rendered = run["rendered_run_record"]
    rendered_id = rendered["artifact_id"]
    matches = [artifact for artifact in run["artifacts"] if artifact["artifact_id"] == rendered_id]
    if len(matches) != 1:
        raise ValueError(f"rendered artifact {rendered_id!r} must exist exactly once")
    matches[0]["classification"] = _render_classification(run)
    state_sha256 = canonical_sha256(render_projection(run))
    markdown = render_markdown(run, state_sha256)
    markdown_sha256 = sha256_bytes(markdown)
    rendered["generator_version"] = GENERATOR_VERSION
    rendered["source_state_sha256"] = state_sha256
    matches[0]["sha256"] = markdown_sha256
    matches[0]["locator"] = str(output_path.resolve())
    issues = validate_run(run, sage_root)
    if issues:
        raise ValueError("renderer produced invalid state:\n" + "\n".join(issues))
    atomic_write_bytes(output_path, markdown)
    if update_state:
        atomic_write_json(run_path, run)
    return state_sha256, markdown_sha256


def verify_render(run_path: Path, output_path: Path, sage_root: Path) -> list[str]:
    run = load_and_validate(run_path, sage_root)
    if not output_path.is_file():
        return [f"rendered record is missing: {output_path}"]
    state_sha256 = canonical_sha256(render_projection(run))
    expected = render_markdown(run, state_sha256)
    issues: list[str] = []
    if output_path.read_bytes() != expected:
        issues.append("rendered Markdown differs from the deterministic projection")
    if run["rendered_run_record"]["source_state_sha256"] != state_sha256:
        issues.append("rendered_run_record.source_state_sha256 is stale")
    rendered_id = run["rendered_run_record"]["artifact_id"]
    artifact = next((item for item in run["artifacts"] if item["artifact_id"] == rendered_id), None)
    if artifact is not None and artifact.get("classification") != _render_classification(run):
        issues.append("rendered artifact does not inherit the strictest contributing classification")
    if artifact is None or artifact["sha256"] != hashlib.sha256(expected).hexdigest():
        issues.append("rendered artifact SHA-256 is stale")
    if artifact is not None and artifact.get("locator") != str(output_path.resolve()):
        issues.append("rendered artifact locator does not resolve to the verified projection")
    return issues
