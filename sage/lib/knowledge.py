"""Promoted-knowledge validation, indexing, promotion, and reconciliation."""

from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .common import (
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    canonical_normalize,
    load_json,
    sage_operation_lock,
    state_root,
    utc_now,
)
from .artifacts import load_and_validate, validate_knowledge_record_schema, verify_render
from .facts import ALL_FACT_TYPES, PERSISTABLE_CLASSIFICATIONS, validate_fact_payload


PORTABLE_FIELDS = (
    "stable_id",
    "class",
    "status",
    "rule",
    "qualifier",
    "recognizer",
    "falsifier",
    "provenance",
)
SAGE_ROOT = Path(__file__).resolve().parents[1]


def projection(record: dict[str, Any]) -> dict[str, Any]:
    value = {field: record.get(field) for field in PORTABLE_FIELDS}
    normalized = canonical_normalize(value)
    normalized["provenance"] = sorted(normalized.get("provenance", []), key=canonical_json_bytes)
    return normalized


def projection_bytes(record: dict[str, Any]) -> bytes:
    return canonical_json_bytes(projection(record))


def projection_sha256(record: dict[str, Any]) -> str:
    return hashlib.sha256(projection_bytes(record)).hexdigest()


def validate_record(record: Any, require_review: bool = False) -> list[str]:
    issues = validate_knowledge_record_schema(record, SAGE_ROOT)
    if not isinstance(record, dict):
        return issues or ["knowledge record must be one JSON object"]
    allowed = {
        "schema_version", *PORTABLE_FIELDS, "stored_integrity_sha256", "local", "promotion", "reconciliation"
    }
    unknown = sorted(set(record) - allowed)
    if unknown:
        issues.append(f"unknown fields: {', '.join(unknown)}")
    if record.get("schema_version") != "1.0":
        issues.append("schema_version must be '1.0'")
    stable_id = record.get("stable_id")
    if not isinstance(stable_id, str) or not stable_id.startswith("sage-knowledge-v1:"):
        issues.append("stable_id must use the sage-knowledge-v1 namespace")
    elif any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-:" for character in stable_id):
        issues.append("stable_id contains an unsupported character")
    for field in ("class", "rule", "qualifier", "recognizer", "falsifier"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            issues.append(f"{field} must be a non-empty string")
    if record.get("status") not in {"active", "retired"}:
        issues.append("status must be active or retired")
    provenance = record.get("provenance")
    if not isinstance(provenance, list) or not provenance or any(not isinstance(item, str) or not item for item in provenance):
        issues.append("provenance must be a non-empty string array")
    try:
        expected = projection_sha256(record)
    except (TypeError, ValueError) as error:
        issues.append(f"portable projection is invalid: {error}")
        expected = None
    stored = record.get("stored_integrity_sha256")
    if expected is not None and stored != expected:
        issues.append(f"stored_integrity_sha256 mismatch: expected {expected}")
    portable_privacy_issues = validate_fact_payload(
        {field: record.get(field) for field in PORTABLE_FIELDS},
        "internal",
    )
    issues.extend(f"portable knowledge privacy check: {issue}" for issue in portable_privacy_issues)
    if require_review:
        promotion = record.get("promotion")
        if not isinstance(promotion, dict):
            issues.append("promotion review metadata is required")
        else:
            action = promotion.get("action")
            if action not in {"create", "revise", "retire"}:
                issues.append("promotion.action must be create, revise, or retire")
            if promotion.get("reviewed") is not True:
                issues.append("promotion.reviewed must be true")
            evidence = promotion.get("review_evidence")
            if not isinstance(evidence, list) or not evidence or any(not isinstance(item, str) or not item for item in evidence):
                issues.append("promotion.review_evidence must be a non-empty string array")
            if action in {"create", "revise"}:
                evidence_class = promotion.get("evidence_class")
                if evidence_class not in {"deterministic_invariant", "empirical_heuristic", "shared_policy_guidance"}:
                    issues.append("promotion.evidence_class is invalid")
                if not isinstance(promotion.get("promotion_actor"), str) or not promotion["promotion_actor"].strip():
                    issues.append("promotion.promotion_actor must name the promotion actor")
                refutation = promotion.get("independent_refutation")
                if not isinstance(refutation, list) or not refutation or any(not isinstance(item, str) or not item for item in refutation):
                    issues.append("promotion.independent_refutation must be a non-empty string array")
                independence = promotion.get("independence_review")
                if not isinstance(independence, dict) or independence.get("judgment") != "independent":
                    issues.append("promotion.independence_review must record the advisory independence judgment")
                utility = promotion.get("expected_utility")
                if not isinstance(utility, dict) or utility.get("recognizer") != record.get("recognizer"):
                    issues.append("promotion.expected_utility must bind the candidate recognizer exactly")
                elif utility.get("net_assessment") != "positive":
                    issues.append("promotion expected utility must be positive")
                novelty = promotion.get("novelty_review")
                if not isinstance(novelty, dict):
                    issues.append("promotion.novelty_review is required")
                elif action == "revise" and novelty.get("disposition") != "revise_existing":
                    issues.append("revise requires novelty disposition revise_existing")
                elif action == "create" and novelty.get("disposition") == "revise_existing":
                    issues.append("create cannot use novelty disposition revise_existing")
                behavioral = promotion.get("behavioral_evaluation")
                if evidence_class == "shared_policy_guidance" and (not isinstance(behavioral, list) or not behavioral):
                    issues.append("shared-policy guidance requires behavioral evaluation evidence")
            prior = promotion.get("expected_prior_sha256")
            if prior is not None and (not isinstance(prior, str) or len(prior) != 64):
                issues.append("promotion.expected_prior_sha256 must be null or a SHA-256")
            if action == "retire":
                if record.get("status") != "retired":
                    issues.append("a retire action requires status retired")
                if promotion.get("retirement_basis") not in {"falsifier_fired", "user_decision"}:
                    issues.append("retirement requires a falsifier_fired or user_decision basis")
                if not isinstance(promotion.get("retirement_reason"), str) or not promotion["retirement_reason"].strip():
                    issues.append("retirement requires a reason")
    return issues


def prepare_candidate(record: dict[str, Any]) -> dict[str, Any]:
    prepared = copy.deepcopy(record)
    prepared.setdefault("schema_version", "1.0")
    prepared["stored_integrity_sha256"] = projection_sha256(prepared)
    return prepared


def record_filename(stable_id: str) -> str:
    return hashlib.sha256(stable_id.encode("utf-8")).hexdigest() + ".json"


def _load_records(directory: Path, *, stop_on_invalid: bool = True) -> tuple[dict[str, tuple[dict[str, Any], Path]], list[str]]:
    records: dict[str, tuple[dict[str, Any], Path]] = {}
    problems: list[str] = []
    if not directory.exists():
        return records, problems
    if directory.is_symlink() or not directory.is_dir():
        return records, [f"knowledge destination is not a plain directory: {directory}"]
    for path in sorted(directory.glob("*.json")):
        if path.is_symlink() or path.stat(follow_symlinks=False).st_nlink != 1:
            problems.append(f"knowledge record has unsafe link state: {path}")
            continue
        try:
            record = load_json(path)
            issues = validate_record(record)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            issues = [str(error)]
            record = None
        if issues:
            problems.append(f"{path}: {'; '.join(issues)}")
            if stop_on_invalid:
                continue
            continue
        stable_id = record["stable_id"]
        if stable_id in records:
            problems.append(f"duplicate stable_id {stable_id!r} in {records[stable_id][1]} and {path}")
            continue
        records[stable_id] = (record, path)
    return records, problems


def _index_entry(record: dict[str, Any], source: str, relative_locator: str) -> dict[str, Any]:
    return {
        "stable_id": record["stable_id"],
        "class": record["class"],
        "status": record["status"],
        "qualifier": record["qualifier"],
        "recognizer": record["recognizer"],
        "projection_sha256": projection_sha256(record),
        "source": source,
        "locator": relative_locator,
    }


def _index_manifest_sha256(entries: list[dict[str, Any]]) -> str:
    manifest = [
        {
            "stable_id": entry["stable_id"],
            "projection_sha256": entry["projection_sha256"],
            "source": entry["source"],
            "locator": entry["locator"],
        }
        for entry in entries
    ]
    return hashlib.sha256(canonical_json_bytes(manifest)).hexdigest()


def _compose_index(
    knowledge_root: Path,
    repository: dict[str, tuple[dict[str, Any], Path]],
    overlay: dict[str, tuple[dict[str, Any], Path]],
    previous: Any = None,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for stable_id, (record, path) in sorted(repository.items()):
        if path.name != record_filename(stable_id):
            raise ValueError(f"repository knowledge filename is not canonical for {stable_id!r}: {path.name}")
        relative = path.relative_to(knowledge_root).as_posix()
        entries.append(_index_entry(record, "repository", relative))
    for stable_id, (record, path) in sorted(overlay.items()):
        if stable_id in repository:
            raise ValueError(f"unreconciled duplicate stable_id {stable_id!r}")
        if path.name != record_filename(stable_id):
            raise ValueError(f"overlay knowledge filename is not canonical for {stable_id!r}: {path.name}")
        relative = path.relative_to(knowledge_root).as_posix()
        entries.append(_index_entry(record, "installed_overlay", relative))
    input_manifest_sha256 = _index_manifest_sha256(entries)
    if (
        isinstance(previous, dict)
        and set(previous) == {"schema_version", "generated_at", "input_manifest_sha256", "entries"}
        and previous.get("schema_version") == "1.0"
        and previous.get("input_manifest_sha256") == input_manifest_sha256
        and previous.get("entries") == entries
        and isinstance(previous.get("generated_at"), str)
    ):
        return previous
    return {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "input_manifest_sha256": input_manifest_sha256,
        "entries": entries,
    }


def build_index(knowledge_root: Path, *, source_only: bool = False) -> dict[str, Any]:
    if source_only:
        repository_dir = knowledge_root / "active"
        overlay_dir = None
        index_path = knowledge_root / "index.json"
    else:
        repository_dir = knowledge_root / "knowledge-repository/active"
        overlay_dir = knowledge_root / "promoted-overlay/active"
        index_path = knowledge_root / "promoted-index/index.json"
    if knowledge_root.is_symlink() or (knowledge_root.exists() and not knowledge_root.is_dir()):
        raise ValueError(f"knowledge root is not a plain directory: {knowledge_root}")
    if index_path.parent.is_symlink() or (index_path.parent.exists() and not index_path.parent.is_dir()):
        raise ValueError(f"promoted-knowledge index parent is not a plain directory: {index_path.parent}")
    if index_path.is_symlink():
        raise ValueError(f"promoted-knowledge index must not be a symlink: {index_path}")
    repository, repository_problems = _load_records(repository_dir)
    if repository_problems:
        raise ValueError("invalid repository knowledge:\n" + "\n".join(repository_problems))
    overlay: dict[str, tuple[dict[str, Any], Path]] = {}
    if overlay_dir is not None:
        overlay, overlay_problems = _load_records(overlay_dir)
        if overlay_problems:
            raise ValueError("invalid overlay knowledge:\n" + "\n".join(overlay_problems))
    previous = load_json(index_path) if index_path.is_file() else None
    index = _compose_index(knowledge_root, repository, overlay, previous)
    if index is previous:
        return previous
    atomic_write_json(index_path, index)
    return index


def _archive_overlay(record: dict[str, Any], archive_dir: Path, outcome: str) -> Path:
    archived = copy.deepcopy(record)
    archived["reconciliation"] = {
        "outcome": outcome,
        "canonical_ref": f"repository:{record['stable_id']}",
        "recorded_at": utc_now(),
    }
    name = f"{record_filename(record['stable_id'])[:-5]}-{projection_sha256(record)}-{outcome}.json"
    target = archive_dir / name
    if target.exists():
        existing = load_json(target)
        if projection_bytes(existing) != projection_bytes(archived):
            raise ValueError(f"archive collision at {target}")
        return target
    atomic_write_json(target, archived)
    return target


def reconcile_installed(source_knowledge_root: Path, installed_knowledge_root: Path) -> dict[str, Any]:
    """Mirror source records, preserve overlay-only records, and archive stable-ID twins."""
    source, problems = _load_records(source_knowledge_root / "active")
    if problems:
        raise ValueError("source knowledge failed validation:\n" + "\n".join(problems))
    overlay_dir = installed_knowledge_root / "promoted-overlay/active"
    archive_dir = installed_knowledge_root / "promoted-overlay/archive"
    quarantine_dir = installed_knowledge_root / "promoted-overlay/quarantine"
    repository_dir = installed_knowledge_root / "knowledge-repository/active"
    for directory in (overlay_dir, archive_dir, quarantine_dir, repository_dir):
        directory.mkdir(parents=True, exist_ok=True)
    overlay, overlay_problems = _load_records(overlay_dir)
    if overlay_problems:
        for problem in overlay_problems:
            raw_path = Path(problem.split(": ", 1)[0])
            if raw_path.exists() and raw_path.parent == overlay_dir:
                target = quarantine_dir / raw_path.name
                if target.exists():
                    target = quarantine_dir / f"{raw_path.stem}-{utc_now().replace(':', '')}{raw_path.suffix}"
                os.replace(raw_path, target)
        overlay, remaining = _load_records(overlay_dir)
        if remaining:
            raise ValueError("overlay quarantine did not settle invalid records")
    installed_repository, repository_problems = _load_records(repository_dir)
    repository_matches = not repository_problems and set(installed_repository) == set(source)
    if repository_matches:
        for stable_id, (source_record, _) in source.items():
            installed_record, installed_path = installed_repository[stable_id]
            if (
                canonical_json_bytes(source_record) != canonical_json_bytes(installed_record)
                or installed_path.name != record_filename(stable_id)
            ):
                repository_matches = False
                break
    if not repository_matches:
        stage = repository_dir.parent / f".active-stage-{os.getpid()}"
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir(parents=True)
        for record, _ in source.values():
            atomic_write_json(stage / record_filename(record["stable_id"]), record)
        previous = repository_dir.parent / f".active-previous-{os.getpid()}"
        if previous.exists():
            shutil.rmtree(previous)
        if repository_dir.exists():
            os.replace(repository_dir, previous)
        os.replace(stage, repository_dir)
        shutil.rmtree(previous, ignore_errors=True)
    archived: list[dict[str, str]] = []
    for stable_id, (overlay_record, overlay_path) in list(overlay.items()):
        source_row = source.get(stable_id)
        if source_row is None:
            continue
        source_record = source_row[0]
        left_bytes = projection_bytes(source_record)
        right_bytes = projection_bytes(overlay_record)
        left_hash = projection_sha256(source_record)
        right_hash = projection_sha256(overlay_record)
        if left_hash == right_hash and left_bytes != right_bytes:
            raise ValueError(f"projection hash collision for {stable_id}")
        outcome = "equivalent_archived" if left_bytes == right_bytes else "conflict_archived"
        archive_path = _archive_overlay(overlay_record, archive_dir, outcome)
        overlay_path.unlink()
        archived.append({"stable_id": stable_id, "outcome": outcome, "path": str(archive_path)})
    index = build_index(installed_knowledge_root)
    return {"archived": archived, "index_sha256": hashlib.sha256(canonical_json_bytes(index)).hexdigest()}


def _active_runs(root: Path) -> list[str]:
    active: list[str] = []
    directory = root / "runs/active"
    if not directory.exists():
        return active
    if directory.is_symlink() or not directory.is_dir():
        return [str(directory)]
    for entry in sorted(directory.iterdir(), key=lambda path: path.name):
        if entry.is_symlink() or not entry.is_dir():
            active.append(entry.name)
            continue
        run_path = entry / "run.json"
        if not run_path.is_file():
            active.append(entry.name)
            continue
        try:
            run = load_json(run_path)
        except (OSError, ValueError, json.JSONDecodeError):
            active.append(entry.name)
            continue
        active.append(str(run.get("run_id") or entry.name))
    return active


@contextmanager
def lifecycle_lock(root: Path) -> Iterator[None]:
    with sage_operation_lock():
        if root.is_symlink() or (root.exists() and not root.is_dir()):
            raise ValueError(f"Sage lifecycle state is not a plain directory: {root}")
        root.mkdir(parents=True, exist_ok=True)
        yield


def _closed_run_bundle(root: Path, run_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not run_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in run_id):
        raise ValueError("run ID contains unsupported path characters")
    path = root / "runs/closed" / run_id / "run.json"
    if not path.is_file():
        raise ValueError(f"closed run {run_id!r} was not found at {path}")
    sage_root = Path(__file__).resolve().parent.parent
    run = load_and_validate(path, sage_root)
    if run.get("run_id") != run_id:
        raise ValueError(f"closed run directory {run_id!r} contains artifact for {run.get('run_id')!r}")
    if run.get("status") not in {"completed", "stopped", "failed"}:
        raise ValueError(f"run {run_id!r} is not closed")
    render_issues = verify_render(path, path.with_name("run.md"), sage_root)
    if render_issues:
        raise ValueError("closed run projection failed verification:\n" + "\n".join(render_issues))
    facts_path = path.with_name("facts.jsonl")
    if not facts_path.is_file():
        raise ValueError(f"closed run {run_id!r} has no durable fact log")
    facts: list[dict[str, Any]] = []
    closing_facts: list[dict[str, Any]] = []
    with facts_path.open(encoding="utf-8") as handle:
        for expected_sequence, line in enumerate(handle, start=1):
            try:
                fact = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"closed run fact line {expected_sequence} is malformed: {error}") from error
            if not isinstance(fact, dict) or fact.get("sequence") != expected_sequence:
                raise ValueError(f"closed run fact sequence is not contiguous at line {expected_sequence}")
            if fact.get("schema_version") != "1.0" or fact.get("memory_class") != "current_run":
                raise ValueError(f"closed run fact line {expected_sequence} has invalid memory metadata")
            if fact.get("run_id") != run_id:
                raise ValueError(f"closed run fact line {expected_sequence} belongs to another run")
            if (
                fact.get("type") not in ALL_FACT_TYPES
                or fact.get("classification") not in PERSISTABLE_CLASSIFICATIONS
                or validate_fact_payload(fact.get("payload"), fact.get("classification"))
            ):
                raise ValueError(f"closed run fact line {expected_sequence} is not an allowlisted factual event")
            facts.append(fact)
            if fact.get("type") == "run.closed":
                closing_facts.append(fact)
    if (
        len(closing_facts) != 1
        or closing_facts[0].get("payload") != {"status": run["status"]}
        or closing_facts[0].get("sequence") != len(facts)
    ):
        raise ValueError(f"closed run {run_id!r} lacks one matching run.closed fact")
    return run, facts


def _normalize_run_ids(run_ids: str | list[str]) -> list[str]:
    values = [run_ids] if isinstance(run_ids, str) else list(run_ids)
    if not values:
        raise ValueError("promotion requires at least one closed run")
    if len(values) != len(set(values)):
        raise ValueError("promotion run IDs must be unique")
    return values


def inspect_closed_runs(
    run_ids: str | list[str],
    installed_state_root: Path | None = None,
) -> dict[str, Any]:
    """Return validated closed-run evidence for the explicit promotion workflow."""
    root = installed_state_root or state_root()
    selected = _normalize_run_ids(run_ids)
    with lifecycle_lock(root / "lifecycle"):
        active = _active_runs(root)
        if active:
            raise ValueError(f"promotion is unavailable while runs are active: {', '.join(active)}")
        rows: list[dict[str, Any]] = []
        for run_id in selected:
            run, facts = _closed_run_bundle(root, run_id)
            closed_directory = root / "runs/closed" / run_id
            rows.append({
                "run_id": run_id,
                "status": run["status"],
                "objective": run["objective"],
                "integrity": {
                    "run_json_sha256": hashlib.sha256((closed_directory / "run.json").read_bytes()).hexdigest(),
                    "facts_jsonl_sha256": hashlib.sha256((closed_directory / "facts.jsonl").read_bytes()).hexdigest(),
                    "run_markdown_sha256": hashlib.sha256((closed_directory / "run.md").read_bytes()).hexdigest(),
                },
                "facts": facts,
                "artifacts": run["artifacts"],
                "findings": run["findings"],
                "dispositions": run["dispositions"],
                "verifications": run["verifications"],
                "decisions": run["decisions"],
                "coordination_outcome": run["coordination_outcome"],
            })
        return {
            "schema_version": "1.0",
            "memory_class": "closed_run_promotion_input",
            "runs": rows,
        }


def _qualified_reference(
    reference: str,
    prefix: str,
    runs: dict[str, dict[str, Any]],
    collection: str,
    identity: str,
) -> tuple[str, str]:
    payload = reference[len(prefix):]
    if len(runs) == 1:
        only_run_id, only_run = next(iter(runs.items()))
        if any(row[identity] == payload for row in only_run[collection]):
            return only_run_id, payload
    for run_id in runs:
        marker = f"{run_id}:"
        if payload.startswith(marker):
            return run_id, payload[len(marker):]
    raise ValueError(f"unresolved or ambiguous {prefix[:-1]} reference: {reference}")


def _resolve_passing_verifications(
    references: list[str],
    runs: dict[str, dict[str, Any]],
    evidence_name: str,
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []
    for reference in references:
        if not reference.startswith("verification:"):
            raise ValueError(f"unsupported {evidence_name}: {reference}")
        run_id, verification_id = _qualified_reference(
            reference, "verification:", runs, "verifications", "verification_id"
        )
        verification = next(
            (row for row in runs[run_id]["verifications"] if row["verification_id"] == verification_id),
            None,
        )
        if verification is None or verification.get("verdict") != "pass":
            raise ValueError(f"unresolved passing {evidence_name}: {reference}")
        resolved.append(verification)
    return resolved


def _verify_promotion_evidence(candidate: dict[str, Any], runs: dict[str, dict[str, Any]]) -> None:
    selected_ids = set(runs)
    provenance_ids = {
        reference.split(":", 1)[1]
        for reference in candidate["provenance"]
        if reference.startswith("run:")
    }
    if provenance_ids != selected_ids:
        raise ValueError(
            "candidate run provenance must exactly match the selected closed runs: "
            f"expected {sorted(selected_ids)}, found {sorted(provenance_ids)}"
        )
    action = candidate["promotion"]["action"]
    if action in {"create", "revise"}:
        minimum_runs = {
            "deterministic_invariant": 1,
            "empirical_heuristic": 3,
            "shared_policy_guidance": 6,
        }[candidate["promotion"]["evidence_class"]]
        if len(selected_ids) < minimum_runs:
            raise ValueError(
                f"{candidate['promotion']['evidence_class']} requires at least {minimum_runs} independent closed runs; "
                f"found {len(selected_ids)}. Semantic independence remains an advisory reviewed judgment."
            )
    artifact_run_ids: set[str] = set()
    for reference in candidate["provenance"]:
        if reference.startswith("run:"):
            continue
        elif reference.startswith("artifact:"):
            run_id, artifact_id = _qualified_reference(
                reference, "artifact:", runs, "artifacts", "artifact_id"
            )
            artifact_run_ids.add(run_id)
            artifact = next(
                (row for row in runs[run_id]["artifacts"] if row["artifact_id"] == artifact_id),
                None,
            )
            if artifact is None or artifact.get("adoption") != "adopted":
                raise ValueError(f"unresolved promotion artifact provenance: {reference}")
        else:
            raise ValueError(f"unsupported promotion provenance reference: {reference}")
    if artifact_run_ids != selected_ids:
        raise ValueError(
            "candidate artifact provenance must cover every selected closed run: "
            f"expected {sorted(selected_ids)}, found {sorted(artifact_run_ids)}"
        )
    _resolve_passing_verifications(
        candidate["promotion"]["review_evidence"], runs, "promotion verification"
    )
    if action in {"create", "revise"}:
        refutations = _resolve_passing_verifications(
            candidate["promotion"]["independent_refutation"], runs, "independent refutation evidence"
        )
        promotion_actor = candidate["promotion"]["promotion_actor"]
        if any(row.get("verified_by") == promotion_actor for row in refutations):
            raise ValueError("independent refutation is not independent of the promotion actor")
        _resolve_passing_verifications(
            candidate["promotion"]["behavioral_evaluation"], runs, "behavioral evaluation evidence"
        )


def _verify_novelty_review(
    candidate: dict[str, Any],
    records: dict[str, tuple[dict[str, Any], Path]],
    peer_ids: set[str],
) -> None:
    expected = {stable_id for stable_id, (record, _path) in records.items() if record.get("status") == "active"}
    expected.discard(candidate["stable_id"])
    compared = set(candidate["promotion"]["novelty_review"]["compared_stable_ids"])
    if compared != expected:
        raise ValueError(
            "novelty review must name every other active stable ID exactly: "
            f"expected {sorted(expected)}, found {sorted(compared)}"
        )
    peer_rows = candidate["promotion"]["novelty_review"]["peer_dispositions"]
    reported_peer_ids = [row["stable_id"] for row in peer_rows]
    if len(reported_peer_ids) != len(set(reported_peer_ids)) or set(reported_peer_ids) != peer_ids:
        raise ValueError(
            "novelty review must disposition every active batch peer exactly once: "
            f"expected {sorted(peer_ids)}, found {sorted(reported_peer_ids)}"
        )


def _git_revision(repository: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"cannot resolve source revision: {result.stderr.strip()}")
    return result.stdout.strip()


def _promotion_result(
    candidate: dict[str, Any],
    run_ids: list[str],
    *,
    destination: str,
    record_changed: bool,
    index_changed: bool,
    target: Path,
    index_path: Path,
    index: dict[str, Any],
    record_file_bytes: bytes,
    source_revision: str | None = None,
    reconciliation: str | None = None,
) -> dict[str, Any]:
    action = candidate["promotion"]["action"]
    changed_paths = []
    if record_changed:
        changed_paths.append(str(target))
    if index_changed:
        changed_paths.append(str(index_path))
    result: dict[str, Any] = {
        "destination": destination,
        "selected_run_ids": run_ids,
        "stable_id": candidate["stable_id"],
        "action": action,
        "actions": [{"stable_id": candidate["stable_id"], "action": action, "changed": record_changed}],
        "changed": record_changed or index_changed,
        "record_changed": record_changed,
        "index_changed": index_changed,
        "path": str(target),
        "index_path": str(index_path),
        "changed_paths": changed_paths,
        "projection_sha256": projection_sha256(candidate),
        "source_hashes": {
            "record_file_sha256": hashlib.sha256(record_file_bytes).hexdigest(),
            "promoted_index_sha256": hashlib.sha256(canonical_json_bytes(index)).hexdigest(),
            "expected_prior_projection_sha256": candidate["promotion"].get("expected_prior_sha256"),
            "source_revision": source_revision,
        },
        "evidence": list(candidate["provenance"]),
        "review_result": {
            "reviewed": candidate["promotion"]["reviewed"],
            "evidence": list(candidate["promotion"]["review_evidence"]),
        },
        "index_entries": len(index["entries"]),
        "conflicts": [],
        "quarantined_inputs": [],
    }
    if reconciliation is not None:
        result["reconciliation"] = reconciliation
    if action in {"create", "revise"}:
        result["review_result"].update({
            "evidence_class": candidate["promotion"]["evidence_class"],
            "independent_refutation": list(candidate["promotion"]["independent_refutation"]),
            "independence_review": candidate["promotion"]["independence_review"],
            "expected_utility": candidate["promotion"]["expected_utility"],
            "novelty_review": candidate["promotion"]["novelty_review"],
            "behavioral_evaluation": list(candidate["promotion"]["behavioral_evaluation"]),
        })
    return result


def _json_file_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False, allow_nan=False).encode("utf-8") + b"\n"


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _durable_unlink(path: Path) -> None:
    path.unlink()
    _fsync_directory(path.parent)


def _transaction_authority_path(knowledge_root: Path) -> Path:
    return knowledge_root / ".promotion-transaction.json"


def _encoded_version(content: bytes | None) -> dict[str, Any]:
    return {
        "present": content is not None,
        "sha256": hashlib.sha256(content).hexdigest() if content is not None else None,
        "content_base64": base64.b64encode(content).decode("ascii") if content is not None else None,
    }


def _transaction_authority(
    knowledge_root: Path,
    changes: list[tuple[Path, bytes]],
    *,
    source_only: bool,
) -> dict[str, Any]:
    entries = []
    for target, next_content in changes:
        try:
            locator = target.relative_to(knowledge_root).as_posix()
        except ValueError as error:
            raise ValueError(f"promotion transaction target escapes its knowledge root: {target}") from error
        prior_content = target.read_bytes() if target.is_file() else None
        entries.append({
            "locator": locator,
            "prior": _encoded_version(prior_content),
            "next": _encoded_version(next_content),
        })
    payload = {
        "schema_version": "1.0",
        "mode": "global" if source_only else "installed",
        "recovery_policy": "roll_forward",
        "entries": entries,
    }
    return {
        **payload,
        "transaction_id": hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
    }


def _decode_transaction_version(version: Any, label: str) -> bytes | None:
    if not isinstance(version, dict) or set(version) != {"present", "sha256", "content_base64"}:
        raise ValueError(f"promotion transaction {label} version is malformed")
    present = version.get("present")
    encoded = version.get("content_base64")
    digest = version.get("sha256")
    if present is False and encoded is None and digest is None:
        return None
    if present is not True or not isinstance(encoded, str) or not isinstance(digest, str):
        raise ValueError(f"promotion transaction {label} version identity is malformed")
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as error:
        raise ValueError(f"promotion transaction {label} content is malformed") from error
    if hashlib.sha256(content).hexdigest() != digest:
        raise ValueError(f"promotion transaction {label} content hash is invalid")
    return content


def _load_transaction_authority(knowledge_root: Path) -> list[tuple[Path, bytes | None, bytes]] | None:
    authority_path = _transaction_authority_path(knowledge_root)
    if not authority_path.exists() and not authority_path.is_symlink():
        return None
    if authority_path.is_symlink() or not authority_path.is_file() or authority_path.stat(follow_symlinks=False).st_nlink != 1:
        raise ValueError(f"promotion transaction authority has unsafe link state: {authority_path}")
    authority = load_json(authority_path)
    if not isinstance(authority, dict) or set(authority) != {
        "schema_version", "mode", "recovery_policy", "entries", "transaction_id"
    }:
        raise ValueError("promotion transaction authority is malformed")
    if (
        authority.get("schema_version") != "1.0"
        or authority.get("mode") not in {"installed", "global"}
        or authority.get("recovery_policy") != "roll_forward"
        or not isinstance(authority.get("entries"), list)
        or not authority["entries"]
    ):
        raise ValueError("promotion transaction authority metadata is malformed")
    payload = {key: authority[key] for key in ("schema_version", "mode", "recovery_policy", "entries")}
    if authority.get("transaction_id") != hashlib.sha256(canonical_json_bytes(payload)).hexdigest():
        raise ValueError("promotion transaction authority identity is invalid")
    allowed_index = "index.json" if authority["mode"] == "global" else "promoted-index/index.json"
    allowed_record_prefix = ("active",) if authority["mode"] == "global" else ("promoted-overlay", "active")
    resolved: list[tuple[Path, bytes | None, bytes]] = []
    locators: set[str] = set()
    for entry in authority["entries"]:
        if not isinstance(entry, dict) or set(entry) != {"locator", "prior", "next"}:
            raise ValueError("promotion transaction entry is malformed")
        locator_value = entry.get("locator")
        locator = Path(locator_value) if isinstance(locator_value, str) else Path("/")
        record_locator = (
            len(locator.parts) == len(allowed_record_prefix) + 1
            and locator.parts[:len(allowed_record_prefix)] == allowed_record_prefix
            and len(locator.name) == 69
            and locator.name.endswith(".json")
            and all(character in "0123456789abcdef" for character in locator.stem)
        )
        if (
            not isinstance(locator_value, str)
            or locator.is_absolute()
            or ".." in locator.parts
            or locator_value in locators
            or (locator.as_posix() != allowed_index and not record_locator)
        ):
            raise ValueError(f"promotion transaction locator is unsafe: {locator_value!r}")
        locators.add(locator_value)
        prior = _decode_transaction_version(entry["prior"], f"{locator_value} prior")
        next_content = _decode_transaction_version(entry["next"], f"{locator_value} next")
        if next_content is None:
            raise ValueError(f"promotion transaction next version is absent: {locator_value}")
        resolved.append((knowledge_root / locator, prior, next_content))
    return resolved


def _recover_promotion_transaction(knowledge_root: Path) -> bool:
    entries = _load_transaction_authority(knowledge_root)
    if entries is None:
        return False
    for target, prior, next_content in entries:
        current = target.read_bytes() if target.is_file() else None
        if current not in {prior, next_content}:
            raise ValueError(f"promotion recovery found an unrecognized target version: {target}")
        if current != next_content:
            atomic_write_bytes(target, next_content, 0o600)
    for target, _prior, next_content in entries:
        if not target.is_file() or target.read_bytes() != next_content:
            raise RuntimeError(f"promotion recovery did not settle the next version: {target}")
    _durable_unlink(_transaction_authority_path(knowledge_root))
    return True


def _recover_pending_installed_transaction(root: Path) -> bool:
    authority_path = _transaction_authority_path(root)
    if not authority_path.exists() and not authority_path.is_symlink():
        return False
    with lifecycle_lock(root / "lifecycle"):
        return _recover_promotion_transaction(root)


def _commit_file_transaction(
    knowledge_root: Path,
    changes: list[tuple[Path, bytes]],
    *,
    source_only: bool,
) -> None:
    if not changes:
        return
    before = {path: path.read_bytes() if path.is_file() else None for path, _content in changes}
    authority_path = _transaction_authority_path(knowledge_root)
    if authority_path.exists() or authority_path.is_symlink():
        raise RuntimeError(f"unsettled promotion transaction exists: {authority_path}")
    atomic_write_json(
        authority_path,
        _transaction_authority(knowledge_root, changes, source_only=source_only),
        0o600,
    )
    committed: list[Path] = []
    try:
        for path, content in changes:
            committed.append(path)
            atomic_write_bytes(path, content, 0o600)
    except (OSError, ValueError, RuntimeError):
        rollback_errors: list[str] = []
        for path in reversed(committed):
            try:
                prior = before[path]
                if prior is None:
                    if path.is_file() and not path.is_symlink():
                        _durable_unlink(path)
                else:
                    atomic_write_bytes(path, prior, 0o600)
            except (OSError, ValueError, RuntimeError) as error:
                rollback_errors.append(f"{path}: {error}")
        if rollback_errors:
            raise RuntimeError("promotion rollback failed: " + "; ".join(rollback_errors))
        _durable_unlink(authority_path)
        raise
    _durable_unlink(authority_path)


def _validate_expected_prior(
    candidate: dict[str, Any],
    prior: tuple[dict[str, Any], Path] | None,
) -> None:
    action = candidate["promotion"]["action"]
    expected_prior = candidate["promotion"].get("expected_prior_sha256")
    if prior is None:
        if action != "create":
            raise ValueError(f"{action} requires an existing stable ID")
        if expected_prior is not None:
            raise ValueError("create must use a null expected prior hash")
        return
    prior_record = prior[0]
    prior_hash = projection_sha256(prior_record)
    identical_create_retry = (
        action == "create"
        and expected_prior is None
        and projection_bytes(prior_record) == projection_bytes(candidate)
    )
    if identical_create_retry:
        return
    if expected_prior != prior_hash:
        raise ValueError(f"expected prior hash {expected_prior!r}, found {prior_hash}")
    if action == "create":
        raise ValueError("create conflicts with an existing stable ID")


def _load_candidate_batch(candidate_paths: list[Path]) -> list[dict[str, Any]]:
    if not candidate_paths:
        raise ValueError("promotion requires at least one candidate")
    candidates = [load_json(path) for path in candidate_paths]
    for candidate in candidates:
        issues = validate_record(candidate, require_review=True)
        if issues:
            raise ValueError("candidate failed validation:\n" + "\n".join(issues))
    candidates.sort(key=lambda candidate: candidate["stable_id"].encode("utf-8"))
    stable_ids = [candidate["stable_id"] for candidate in candidates]
    if len(stable_ids) != len(set(stable_ids)):
        duplicates = sorted({stable_id for stable_id in stable_ids if stable_ids.count(stable_id) > 1})
        raise ValueError(f"promotion batch contains duplicate stable IDs: {', '.join(duplicates)}")
    if len(candidates) > 5:
        excess = [candidate["stable_id"] for candidate in candidates[5:]]
        raise ValueError(f"promotion batch is capped at five candidates; excess: {', '.join(excess)}")
    return candidates


def promote_batch(
    candidate_paths: list[Path],
    run_id: str | list[str],
    *,
    global_source_root: Path | None = None,
    expected_source_revision: str | None = None,
    installed_state_root: Path | None = None,
) -> dict[str, Any]:
    candidates = _load_candidate_batch(candidate_paths)
    run_ids = _normalize_run_ids(run_id)
    root = installed_state_root or state_root()
    with lifecycle_lock(root / "lifecycle"):
        active = _active_runs(root)
        if active:
            raise ValueError(f"promotion is unavailable while runs are active: {', '.join(active)}")
        closed_runs = {selected: _closed_run_bundle(root, selected)[0] for selected in run_ids}
        for candidate in candidates:
            _verify_promotion_evidence(candidate, closed_runs)

        actual_revision: str | None = None
        if global_source_root is None:
            knowledge_root = root
            _recover_promotion_transaction(knowledge_root)
            destination = knowledge_root / "promoted-overlay/active"
            repository_records, repository_problems = _load_records(knowledge_root / "knowledge-repository/active")
            existing, destination_problems = _load_records(destination)
            if repository_problems:
                raise ValueError("installed repository knowledge is invalid:\n" + "\n".join(repository_problems))
            if destination_problems:
                raise ValueError("installed overlay knowledge is invalid:\n" + "\n".join(destination_problems))
            collisions = set(repository_records) & set(existing)
            if collisions:
                raise ValueError(f"unreconciled duplicate stable IDs: {', '.join(sorted(collisions))}")
            active_snapshot = {**repository_records, **existing}
            index_path = knowledge_root / "promoted-index/index.json"
        else:
            repository = global_source_root.resolve()
            if expected_source_revision is None:
                raise ValueError("global promotion requires --expected-source-revision")
            actual_revision = _git_revision(repository)
            if actual_revision != expected_source_revision:
                raise ValueError(f"source revision changed: expected {expected_source_revision}, found {actual_revision}")
            if not (repository / "sage/install.sh").is_file() or not (repository / "sage/knowledge").is_dir():
                raise ValueError(f"not a Sage source repository: {repository}")
            knowledge_root = repository / "sage/knowledge"
            _recover_promotion_transaction(knowledge_root)
            destination = knowledge_root / "active"
            existing, destination_problems = _load_records(destination)
            if destination_problems:
                raise ValueError("destination knowledge is invalid:\n" + "\n".join(destination_problems))
            repository_records = {}
            active_snapshot = existing
            index_path = knowledge_root / "index.json"

        if knowledge_root.is_symlink() or (knowledge_root.exists() and not knowledge_root.is_dir()):
            raise ValueError(f"knowledge root is not a plain directory: {knowledge_root}")
        if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
            raise ValueError(f"promotion destination is not a plain directory: {destination}")
        if index_path.parent.is_symlink() or (index_path.parent.exists() and not index_path.parent.is_dir()):
            raise ValueError(f"promoted-knowledge index parent is not a plain directory: {index_path.parent}")
        if index_path.is_symlink():
            raise ValueError(f"promoted-knowledge index must not be a symlink: {index_path}")

        peer_ids = {
            candidate["stable_id"]
            for candidate in candidates
            if candidate["promotion"]["action"] in {"create", "revise"}
        }
        for candidate in candidates:
            if candidate["promotion"]["action"] in {"create", "revise"}:
                _verify_novelty_review(
                    candidate,
                    active_snapshot,
                    peer_ids - {candidate["stable_id"]},
                )

        prospective = dict(existing)
        plans: list[dict[str, Any]] = []
        for candidate in candidates:
            stable_id = candidate["stable_id"]
            reconciliation = None
            prior = existing.get(stable_id)
            if global_source_root is None and stable_id in repository_records:
                prior = repository_records[stable_id]
                _validate_expected_prior(candidate, prior)
                if projection_bytes(prior[0]) != projection_bytes(candidate):
                    raise ValueError(
                        "installed promotion cannot shadow a divergent repository stable ID; use explicit global promotion"
                    )
                target = prior[1]
                changed = False
                reconciliation = "already_canonical_in_repository"
            else:
                _validate_expected_prior(candidate, prior)
                target = destination / record_filename(stable_id)
                if target.is_symlink() or (target.exists() and target.stat(follow_symlinks=False).st_nlink != 1):
                    raise ValueError(f"promotion target has unsafe link state: {target}")
                changed = prior is None or projection_bytes(prior[0]) != projection_bytes(candidate)
                prospective[stable_id] = (candidate, target)
            plans.append({
                "candidate": candidate,
                "target": target,
                "record_changed": changed,
                "reconciliation": reconciliation,
                "record_file_bytes": _json_file_bytes(candidate) if changed else target.read_bytes(),
            })

        previous_index = load_json(index_path) if index_path.is_file() else None
        if global_source_root is None:
            index = _compose_index(knowledge_root, repository_records, prospective, previous_index)
        else:
            index = _compose_index(knowledge_root, prospective, {}, previous_index)
        prior_index_bytes = index_path.read_bytes() if index_path.is_file() else None
        index_bytes = _json_file_bytes(index)
        index_changed = prior_index_bytes != index_bytes
        changes = [
            (plan["target"], _json_file_bytes(plan["candidate"]))
            for plan in plans
            if plan["record_changed"]
        ]
        if index_changed:
            changes.append((index_path, index_bytes))
        results = []
        for plan in plans:
            result = _promotion_result(
                plan["candidate"],
                run_ids,
                destination="global" if global_source_root is not None else "installed",
                record_changed=plan["record_changed"],
                index_changed=index_changed,
                target=plan["target"],
                index_path=index_path,
                index=index,
                record_file_bytes=plan["record_file_bytes"],
                source_revision=actual_revision,
                reconciliation=plan["reconciliation"],
            )
            if global_source_root is not None:
                result["follow_up_install"] = str(global_source_root.resolve() / "sage/install.sh")
            results.append(result)
        _commit_file_transaction(
            knowledge_root,
            changes,
            source_only=global_source_root is not None,
        )
        return {
            "batch_size": len(results),
            "candidate_order": [candidate["stable_id"] for candidate in candidates],
            "excess": [],
            "changed": any(result["changed"] for result in results),
            "results": results,
        }


def promote(
    candidate_path: Path,
    run_id: str | list[str],
    *,
    global_source_root: Path | None = None,
    expected_source_revision: str | None = None,
    installed_state_root: Path | None = None,
) -> dict[str, Any]:
    batch = promote_batch(
        [candidate_path],
        run_id,
        global_source_root=global_source_root,
        expected_source_revision=expected_source_revision,
        installed_state_root=installed_state_root,
    )
    return batch["results"][0]


def _list_indexed_unlocked(root: Path) -> list[dict[str, Any]]:
    index_path = root / "promoted-index/index.json"
    index = load_json(index_path)
    if (
        not isinstance(index, dict)
        or set(index) != {"schema_version", "generated_at", "input_manifest_sha256", "entries"}
        or index.get("schema_version") != "1.0"
        or not isinstance(index.get("generated_at"), str)
        or not isinstance(index.get("input_manifest_sha256"), str)
        or len(index["input_manifest_sha256"]) != 64
        or not isinstance(index.get("entries"), list)
    ):
        raise ValueError(f"invalid promoted-knowledge index: {index_path}")
    seen: set[str] = set()
    active: list[dict[str, Any]] = []
    required = {
        "stable_id", "class", "status", "qualifier", "recognizer",
        "projection_sha256", "source", "locator",
    }
    for entry in index["entries"]:
        if not isinstance(entry, dict) or set(entry) != required:
            raise ValueError(f"invalid promoted-knowledge index entry: {entry!r}")
        stable_id = entry.get("stable_id")
        locator = Path(entry.get("locator", ""))
        expected_prefix = (
            Path("knowledge-repository/active")
            if entry.get("source") == "repository"
            else Path("promoted-overlay/active")
        )
        expected_locator = expected_prefix / record_filename(stable_id) if isinstance(stable_id, str) else None
        if (
            not isinstance(stable_id, str)
            or stable_id in seen
            or entry.get("status") not in {"active", "retired"}
            or entry.get("source") not in {"repository", "installed_overlay"}
            or not isinstance(entry.get("projection_sha256"), str)
            or len(entry["projection_sha256"]) != 64
            or locator.is_absolute()
            or not locator.parts
            or ".." in locator.parts
            or locator != expected_locator
        ):
            raise ValueError(f"unsafe promoted-knowledge index entry: {entry!r}")
        seen.add(stable_id)
        if entry["status"] == "active":
            active.append(entry)
    if index["input_manifest_sha256"] != _index_manifest_sha256(index["entries"]):
        raise ValueError(f"promoted-knowledge index manifest hash is stale: {index_path}")
    return active


def list_indexed(installed_state_root: Path | None = None) -> list[dict[str, Any]]:
    root = installed_state_root or state_root()
    _recover_pending_installed_transaction(root)
    return _list_indexed_unlocked(root)


def get_indexed(stable_ids: list[str], installed_state_root: Path | None = None) -> list[dict[str, Any]]:
    root = installed_state_root or state_root()
    index_path = root / "promoted-index/index.json"
    for _attempt in range(3):
        _recover_pending_installed_transaction(root)
        index_before = index_path.read_bytes()
        entries = {entry["stable_id"]: entry for entry in _list_indexed_unlocked(root)}
        records: list[dict[str, Any]] = []
        try:
            for stable_id in stable_ids:
                entry = entries.get(stable_id)
                if entry is None:
                    raise KeyError(f"promoted stable ID is not indexed: {stable_id}")
                locator = Path(entry["locator"])
                if locator.is_absolute() or ".." in locator.parts:
                    raise ValueError(f"unsafe knowledge locator for {stable_id}")
                path = root / locator
                current = root
                for component in locator.parts:
                    current = current / component
                    if current.is_symlink():
                        raise ValueError(f"knowledge locator traverses a symlink for {stable_id}: {current}")
                if not path.is_file():
                    raise ValueError(f"indexed knowledge record is missing: {stable_id}")
                record = load_json(path)
                issues = validate_record(record)
                if (
                    issues
                    or record.get("stable_id") != stable_id
                    or record.get("status") != "active"
                    or projection_sha256(record) != entry["projection_sha256"]
                    or any(record.get(field) != entry.get(field) for field in ("class", "status", "qualifier", "recognizer"))
                ):
                    raise ValueError(f"indexed record failed integrity validation: {stable_id}")
                records.append(record)
        except (KeyError, OSError, ValueError, json.JSONDecodeError):
            recovered = _recover_pending_installed_transaction(root)
            index_changed = index_path.is_file() and index_path.read_bytes() != index_before
            if recovered or index_changed:
                continue
            raise
        if _recover_pending_installed_transaction(root):
            continue
        if index_path.read_bytes() != index_before:
            continue
        return records
    raise RuntimeError("promoted knowledge changed repeatedly while it was being read")
