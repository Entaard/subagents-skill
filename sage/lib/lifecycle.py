"""Receipt-bound install, update, and complete removal for Sage Light mode."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import unicodedata
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from .artifacts import _load_phase0_checker, validate_receipt
from .common import (
    atomic_write_bytes,
    atomic_write_json,
    canonical_json_bytes,
    canonical_sha256,
    load_json,
    sage_operation_lock,
    sha256_file,
    tree_sha256,
    utc_now,
)
from .knowledge import reconcile_installed, record_filename, validate_record


INSTALLER_VERSION = "sage-light-lifecycle/1.1"
PRESERVATION_CLASSES = [
    "run_history",
    "current_run_recovery",
    "promoted_overlay",
    "retention_settings",
    "backups",
]


@dataclass
class EntryPlan:
    entry_id: str
    root_id: str
    target: Path
    stage: Path
    expected_type: str
    entry_class: str
    retention_class: str
    cleanup_order: int
    mutable: bool
    marker: str


def _path_hash(path: Path | str) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def _canonical_path(raw: str | Path) -> Path:
    text = unicodedata.normalize("NFC", str(Path(raw).expanduser()))
    path = Path(text)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = Path(os.path.abspath(path))
    if path == Path("/"):
        raise ValueError("/ is not an allowed Sage destination")
    _assert_no_symlink_chain(path, "path", include_target=True)
    return path


def _assert_no_symlink_chain(path: Path, label: str, *, include_target: bool = True) -> None:
    candidate = path if include_target else path.parent
    chain = list(reversed(candidate.parents)) + [candidate]
    for component in chain:
        if component == Path("/") or not (component.exists() or component.is_symlink()):
            continue
        if component.is_symlink():
            raise ValueError(f"{label} has a symlink ancestor or target: {component}")
        if component != candidate and not component.is_dir():
            raise ValueError(f"{label} has a non-directory ancestor: {component}")


def _ensure_root(path: Path, label: str) -> None:
    _assert_no_symlink_chain(path, label, include_target=True)
    if path.exists() and not path.is_dir():
        raise ValueError(f"{label} is not a directory: {path}")
    path.mkdir(parents=True, exist_ok=True)
    _assert_no_symlink_chain(path, label, include_target=True)


def _paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _ancestor_ids(path: Path) -> list[str]:
    result: list[str] = []
    for ancestor in list(reversed(path.parents)):
        if not ancestor.exists():
            continue
        observed = ancestor.stat(follow_symlinks=False)
        identity = f"{observed.st_dev}:{observed.st_ino}"
        if identity not in result:
            result.append(identity)
    return result


def _resource_identity(path: Path, canonical_path: Path | None = None) -> dict[str, Any]:
    observed = path.stat(follow_symlinks=False)
    canonical = canonical_path or path
    return {
        "provider": "posix",
        "volume_id": str(observed.st_dev),
        "object_id": f"{observed.st_dev}:{observed.st_ino}",
        "ancestor_object_ids": _ancestor_ids(path),
        "case_sensitivity": "sensitive",
        "unicode_normalization": "none",
        "resolved_path_sha256": _path_hash(canonical),
    }


def _project_resource_identity(source: Path, target: Path) -> dict[str, Any]:
    observed = source.stat(follow_symlinks=False)
    return {
        "provider": "posix",
        "volume_id": str(observed.st_dev),
        "object_id": f"{observed.st_dev}:{observed.st_ino}",
        "ancestor_object_ids": _ancestor_ids(target),
        "case_sensitivity": "sensitive",
        "unicode_normalization": "none",
        "resolved_path_sha256": _path_hash(target),
    }


def _fs_identity(path: Path, verified_at: str | None = None) -> dict[str, Any]:
    observed = path.stat(follow_symlinks=False)
    target_hash = hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest() if path.is_symlink() else None
    return {
        "device": observed.st_dev,
        "inode": observed.st_ino,
        "link_count": observed.st_nlink,
        "ancestor_chain_sha256": canonical_sha256(_ancestor_ids(path)),
        "symlink_target_sha256": target_hash,
        "verified_at": verified_at or utc_now(),
    }


def _project_fs_identity(source: Path, target: Path, verified_at: str | None = None) -> dict[str, Any]:
    observed = source.stat(follow_symlinks=False)
    target_hash = hashlib.sha256(os.readlink(source).encode("utf-8")).hexdigest() if source.is_symlink() else None
    return {
        "device": observed.st_dev,
        "inode": observed.st_ino,
        "link_count": observed.st_nlink,
        "ancestor_chain_sha256": canonical_sha256(_ancestor_ids(target)),
        "symlink_target_sha256": target_hash,
        "verified_at": verified_at or utc_now(),
    }


def _observed_type(path: Path) -> str:
    mode = path.lstat().st_mode
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISLNK(mode):
        return "symlink"
    raise ValueError(f"unsupported filesystem object: {path}")


def _content_sha256(path: Path) -> str:
    if path.is_symlink():
        return hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest()
    if path.is_file():
        return sha256_file(path)
    return tree_sha256(path)


def _copy_path(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_type = _observed_type(source)
    if source_type == "directory":
        shutil.copytree(source, destination, symlinks=True)
    elif source_type == "file":
        if source.lstat().st_nlink != 1:
            raise ValueError(f"refusing to copy hard-linked file as lifecycle state: {source}")
        shutil.copy2(source, destination, follow_symlinks=False)
    else:
        raise ValueError(f"refusing to own or displace a symlink: {source}")


def _move_path(source: Path, destination: Path) -> None:
    """Atomically move lifecycle state so rollback preserves its exact identity."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    source_parent = source.parent
    try:
        os.replace(source, destination)
    except OSError as error:
        raise ValueError(
            f"cannot atomically move {source} to {destination}; targets and backup root must share a filesystem: {error}"
        ) from error
    for parent in {source_parent, destination.parent}:
        if parent.is_dir():
            descriptor = os.open(parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def _marker_path(path: Path) -> Path:
    return path / ".sage-owner.json"


def _write_directory_marker(path: Path, marker: str) -> None:
    atomic_write_json(_marker_path(path), {"schema_version": "1.0", "marker": marker}, 0o600)


def _marker_matches(path: Path, expected_type: str, marker: str) -> bool:
    if expected_type == "directory":
        marker_path = _marker_path(path)
        try:
            value = load_json(marker_path)
        except (OSError, ValueError, json.JSONDecodeError):
            return False
        return value == {"schema_version": "1.0", "marker": marker}
    try:
        prefix = path.read_text(encoding="utf-8")[:4096]
    except (OSError, UnicodeDecodeError):
        return False
    return f"# {marker}\n" in prefix


def _source_manifest(repository: Path) -> tuple[str, list[dict[str, Any]]]:
    # Sage for Codex is self-contained under repository/sage.  The repository-root
    # scripts belong to the preserved sage-claude distribution and are deliberately
    # outside this install/update manifest.
    roots = [repository / "sage"]
    rows: list[dict[str, Any]] = []
    for root in roots:
        if not root.exists():
            raise ValueError(f"required source is missing: {root}")
        candidates = [root] if root.is_file() else sorted(root.rglob("*"))
        for path in candidates:
            relative = path.relative_to(repository).as_posix()
            if "__pycache__" in path.parts or path.suffix == ".pyc" or ".sage-stage-" in path.name:
                continue
            if path.is_symlink():
                raise ValueError(f"source distribution contains a symlink: {path}")
            if path.is_file():
                rows.append({
                    "path": relative,
                    "mode": path.lstat().st_mode & 0o7777,
                    "sha256": sha256_file(path),
                })
    return canonical_sha256(rows), rows


def _source_revision(repository: Path, manifest_sha256: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else f"tree:{manifest_sha256}"


def _copytree_source(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        symlinks=False,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )


def _wrapper(marker: str, state_root: Path, command: list[str]) -> bytes:
    quoted = " ".join(shlex.quote(value) for value in command)
    content = (
        "#!/bin/sh\n"
        f"# {marker}\n"
        f"export SAGE_STATE_ROOT={shlex.quote(str(state_root))}\n"
        "export PYTHONDONTWRITEBYTECODE=1\n"
        f"exec {quoted} \"$@\"\n"
    )
    return content.encode("utf-8")


def _stage_directory(parent: Path, operation_id: str, entry_id: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    path = parent / f".sage-stage-{operation_id}-{entry_id}"
    if path.exists() or path.is_symlink():
        raise ValueError(f"staging path already exists: {path}")
    return path


def _validated_source_knowledge(repository: Path) -> list[dict[str, Any]]:
    source_active = repository / "sage/knowledge/active"
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    if not source_active.is_dir():
        return records
    for source in sorted(source_active.glob("*.json")):
        record = load_json(source)
        issues = validate_record(record)
        if issues:
            raise ValueError(f"invalid source knowledge {source}: {'; '.join(issues)}")
        stable_id = record["stable_id"]
        if stable_id in seen:
            raise ValueError(f"duplicate source knowledge stable ID: {stable_id}")
        seen.add(stable_id)
        records.append(record)
    return sorted(records, key=lambda row: row["stable_id"])


def _make_plans(
    repository: Path,
    skills_root: Path,
    bin_root: Path,
    data_root: Path,
    state_root: Path,
    installation_id: str,
    operation_id: str,
) -> list[EntryPlan]:
    definitions = [
        ("skill.sage", "skills", skills_root / "sage", "directory", "created", "distribution", 70, False),
        ("skill.sage-promote", "skills", skills_root / "sage-promote", "directory", "created", "distribution", 70, False),
        ("bin.sage-light", "bin", bin_root / "sage-light", "file", "created", "distribution", 80, False),
        ("bin.sage-promote", "bin", bin_root / "sage-promote", "file", "created", "distribution", 80, False),
        ("bin.sage-uninstall", "bin", bin_root / "sage-uninstall", "file", "created", "distribution", 80, False),
        ("distribution.light", "distribution", data_root, "directory", "created", "distribution", 60, False),
        ("state.runs", "state", state_root / "runs", "directory", "runtime_data", "run_history", 30, True),
        ("state.promoted-overlay", "state", state_root / "promoted-overlay", "directory", "runtime_data", "promoted_overlay", 30, True),
        ("state.promoted-index", "state", state_root / "promoted-index", "directory", "runtime_data", "promoted_overlay", 31, True),
        ("state.settings", "state", state_root / "settings", "directory", "runtime_data", "secret_free_state", 32, True),
        ("state.knowledge-repository", "state", state_root / "knowledge-repository", "directory", "created", "distribution", 40, False),
        ("state.lifecycle", "state", state_root / "lifecycle", "directory", "receipt", "cache", 0, True),
    ]
    plans: list[EntryPlan] = []
    python = sys.executable or "python3"
    for entry_id, root_id, target, expected_type, entry_class, retention_class, cleanup, mutable in definitions:
        marker = f"sage-owned:{installation_id}:{entry_id}"
        stage = _stage_directory(target.parent, operation_id, entry_id)
        if expected_type == "file":
            if entry_id == "bin.sage-light":
                command = [python, str(data_root / "scripts/sage-light.py")]
            elif entry_id == "bin.sage-promote":
                command = [python, str(data_root / "scripts/sage-promote.py")]
            else:
                command = [
                    python,
                    str(data_root / "scripts/sage-lifecycle.py"),
                    "uninstall",
                    "--skills-root", str(skills_root),
                    "--bin-root", str(bin_root),
                    "--data-root", str(data_root),
                    "--state-root", str(state_root),
                ]
            atomic_write_bytes(stage, _wrapper(marker, state_root, command), 0o755)
        else:
            if entry_id == "distribution.light":
                _copytree_source(repository / "sage", stage)
            elif entry_id == "skill.sage":
                _copytree_source(repository / "sage/skills/sage", stage)
            elif entry_id == "skill.sage-promote":
                _copytree_source(repository / "sage/skills/sage-promote", stage)
            else:
                stage.mkdir()
                if entry_id == "state.runs":
                    (stage / "active").mkdir()
                    (stage / "closed").mkdir()
                elif entry_id == "state.promoted-overlay":
                    for name in ("active", "archive", "quarantine"):
                        (stage / name).mkdir()
                elif entry_id == "state.promoted-index":
                    entries = [
                        {
                            "stable_id": record["stable_id"],
                            "class": record["class"],
                            "status": record["status"],
                            "qualifier": record["qualifier"],
                            "recognizer": record["recognizer"],
                            "projection_sha256": record["stored_integrity_sha256"],
                            "source": "repository",
                            "locator": f"knowledge-repository/active/{record_filename(record['stable_id'])}",
                        }
                        for record in _validated_source_knowledge(repository)
                    ]
                    atomic_write_json(stage / "index.json", {
                        "schema_version": "1.0",
                        "generated_at": utc_now(),
                        "input_manifest_sha256": canonical_sha256([
                            {
                                "stable_id": entry["stable_id"],
                                "projection_sha256": entry["projection_sha256"],
                                "source": entry["source"],
                                "locator": entry["locator"],
                            }
                            for entry in entries
                        ]),
                        "entries": entries,
                    })
                elif entry_id == "state.settings":
                    atomic_write_json(stage / "retention.json", {
                        "schema_version": "1.0",
                        "owner": "user",
                        "run_history": "retain_until_complete_removal",
                        "promoted_overlay": "retain_until_complete_removal",
                    }, 0o600)
                elif entry_id == "state.lifecycle":
                    (stage / "receipts").mkdir()
                    (stage / "lifecycle.lock").touch(mode=0o600)
                elif entry_id == "state.knowledge-repository":
                    active = stage / "active"
                    active.mkdir()
                    for record in _validated_source_knowledge(repository):
                        atomic_write_json(active / record_filename(record["stable_id"]), record)
            _write_directory_marker(stage, marker)
        plans.append(EntryPlan(
            entry_id, root_id, target, stage, expected_type, entry_class,
            retention_class, cleanup, mutable, marker,
        ))
    return plans


def _preflight_install_targets(rows: list[dict[str, Any]]) -> None:
    """Reject ambiguous live targets before any staging path is created."""
    for row in rows:
        target = Path(row["target"])
        if not (target.exists() or target.is_symlink()):
            _assert_no_symlink_chain(target, row["entry_id"], include_target=False)
            continue
        _assert_no_symlink_chain(target, row["entry_id"], include_target=True)
        observed_type = _observed_type(target)
        if observed_type == "symlink":
            raise ValueError(f"refusing to replace a symlink: {target}")
        if observed_type == "file" and target.stat(follow_symlinks=False).st_nlink != 1:
            raise ValueError(f"refusing to replace a hard-linked file: {target}")


def _root_record(root_id: str, path: Path, now: str) -> dict[str, Any]:
    return {
        "root_id": root_id,
        "canonical_path": str(path),
        "canonical_path_sha256": _path_hash(path),
        "destination_policy_id": "sage-light-destination-v1",
        "resource_identity": _resource_identity(path),
        "identity": _fs_identity(path, now),
    }


def _protected_record(repository: Path) -> dict[str, Any]:
    return {
        "path_class": "source_checkout",
        "canonical_path": str(repository),
        "canonical_path_sha256": _path_hash(repository),
        "resource_identity": _resource_identity(repository),
    }


def _entry_record(plan: EntryPlan, roots: dict[str, Path], backup_ids: list[str], now: str) -> dict[str, Any]:
    parent = plan.target.parent
    record: dict[str, Any] = {
        "entry_id": plan.entry_id,
        "root_id": plan.root_id,
        "relative_path": plan.target.relative_to(roots[plan.root_id]).as_posix(),
        "entry_class": plan.entry_class,
        "expected_type": plan.expected_type,
        "ownership_marker": plan.marker,
        "resource_identity": _resource_identity(plan.target),
        "identity": _fs_identity(plan.target, now),
        "parent_resource_identity": _resource_identity(parent),
        "parent_identity": _fs_identity(parent, now),
        "cleanup_order": plan.cleanup_order,
        "retention_class": plan.retention_class,
        "backup_ids": backup_ids,
    }
    if not plan.mutable:
        record["content_sha256"] = _content_sha256(plan.target)
    return record


def _backup_record(
    backup_id: str,
    purpose: str,
    owner: EntryPlan,
    backup_root: Path,
    payload: Path,
    original_identity: dict[str, Any],
    original_resource: dict[str, Any],
    original_type: str,
    original_mode: int,
    digest: str,
    now: str,
) -> dict[str, Any]:
    return {
        "backup_id": backup_id,
        "purpose": purpose,
        "owner_kind": "entry",
        "owner_entry_id": owner.entry_id,
        "original_path": str(owner.target),
        "original_identity": original_identity,
        "original_resource_identity": original_resource,
        "backup_root_id": "backups",
        "backup_relative_path": payload.relative_to(backup_root).as_posix(),
        "backup_path": str(payload),
        "original_type": original_type,
        "mode": format(original_mode, "04o"),
        "sha256": digest,
        "backup_identity": _fs_identity(payload, now),
        "backup_resource_identity": _resource_identity(payload),
        "parent_identity": _fs_identity(payload.parent, now),
        "parent_resource_identity": _resource_identity(payload.parent),
        "restored": False,
    }


def _projected_backup_record(
    backup_id: str,
    purpose: str,
    owner: EntryPlan,
    backup_root: Path,
    payload: Path,
    original: dict[str, Any],
    original_identity: dict[str, Any],
    original_resource: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    parent_identity = _fs_identity(payload.parent, now)
    parent_identity["link_count"] += _directory_entry_link_delta(payload.parent, original["type"])
    return {
        "backup_id": backup_id,
        "purpose": purpose,
        "owner_kind": "entry",
        "owner_entry_id": owner.entry_id,
        "original_path": str(owner.target),
        "original_identity": copy.deepcopy(original_identity),
        "original_resource_identity": copy.deepcopy(original_resource),
        "backup_root_id": "backups",
        "backup_relative_path": payload.relative_to(backup_root).as_posix(),
        "backup_path": str(payload),
        "original_type": original["type"],
        "mode": format(original["mode"], "04o"),
        "sha256": original["sha256"],
        "backup_identity": _project_fs_identity(owner.target, payload, now),
        "backup_resource_identity": _project_resource_identity(owner.target, payload),
        "parent_identity": parent_identity,
        "parent_resource_identity": _resource_identity(payload.parent),
        "restored": False,
    }


def _directory_entry_link_delta(parent: Path, entry_type: str) -> int:
    probe = parent / f".sage-link-probe-{uuid.uuid4().hex}"
    before = parent.stat(follow_symlinks=False).st_nlink
    if entry_type == "directory":
        probe.mkdir()
    else:
        descriptor = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
    try:
        after = parent.stat(follow_symlinks=False).st_nlink
    finally:
        _remove_path(probe)
    return after - before


def _projected_install_receipt(
    *,
    repository: Path,
    revision: str,
    manifest_sha256: str,
    roots: dict[str, Path],
    plans: list[EntryPlan],
    recovery_rows: dict[str, dict[str, Any]],
    prior: dict[str, Any] | None,
    inherited_backups: list[dict[str, Any]],
    projected_backups: list[dict[str, Any]],
    installation_id: str,
    operation_id: str,
    kind: str,
    now: str,
) -> dict[str, Any]:
    prior_entries = {row["entry_id"]: row for row in prior.get("entries", [])} if prior else {}
    backups = inherited_backups + projected_backups
    backup_ids_by_owner: dict[str, list[str]] = {}
    for backup in backups:
        backup_ids_by_owner.setdefault(backup["owner_entry_id"], []).append(backup["backup_id"])

    parent_identities: dict[Path, dict[str, Any]] = {}
    for plan in plans:
        parent_identities.setdefault(plan.target.parent, _fs_identity(plan.target.parent, now))
    for plan in plans:
        row = recovery_rows[plan.entry_id]
        if row["replace"] and isinstance(row.get("original"), dict):
            parent_identities[plan.target.parent]["link_count"] -= _directory_entry_link_delta(
                plan.target.parent, row["original"]["type"],
            )

    prior_classes = {row["entry_id"]: row["entry_class"] for row in prior.get("entries", [])} if prior else {}
    entries: list[dict[str, Any]] = []
    for plan in plans:
        old = prior_entries.get(plan.entry_id)
        if old is not None and plan.mutable:
            preserved = copy.deepcopy(old)
            preserved["backup_ids"] = backup_ids_by_owner.get(plan.entry_id, [])
            entries.append(preserved)
            continue
        row = recovery_rows[plan.entry_id]
        installed = row["installed"]
        entry_class = prior_classes.get(plan.entry_id, plan.entry_class)
        if old is None and row["original"] is not None:
            entry_class = "replaced"
        entry: dict[str, Any] = {
            "entry_id": plan.entry_id,
            "root_id": plan.root_id,
            "relative_path": plan.target.relative_to(roots[plan.root_id]).as_posix(),
            "entry_class": entry_class,
            "expected_type": plan.expected_type,
            "ownership_marker": plan.marker,
            "resource_identity": copy.deepcopy(installed["resource_identity"]),
            "identity": copy.deepcopy(installed["identity"]),
            "parent_resource_identity": _resource_identity(plan.target.parent),
            "parent_identity": copy.deepcopy(parent_identities[plan.target.parent]),
            "cleanup_order": plan.cleanup_order,
            "retention_class": plan.retention_class,
            "backup_ids": backup_ids_by_owner.get(plan.entry_id, []),
        }
        if not plan.mutable:
            entry["content_sha256"] = installed["sha256"]
        entries.append(entry)

    root_rows: list[dict[str, Any]] = []
    for root_id, path in roots.items():
        root_row = _root_record(root_id, path, now)
        if path in parent_identities:
            root_row["identity"] = copy.deepcopy(parent_identities[path])
        root_rows.append(root_row)
    return {
        "receipt_version": "1.0",
        "installation_id": installation_id,
        "mode": "light",
        "installer_version": INSTALLER_VERSION,
        "source": {"repository": str(repository), "revision": revision, "manifest_sha256": manifest_sha256},
        "protected_paths": [_protected_record(repository)],
        "roots": root_rows,
        "entries": entries,
        "config_entries": [],
        "backups": backups,
        "retention_policies": _retention_policies(),
        "preservation": {
            "preserve_on_update": PRESERVATION_CLASSES,
            "keep_data": False,
            "keep_data_entry_ids": [],
            "retention_receipt_id": None,
        },
        "operation": {
            "operation_id": operation_id,
            "kind": kind,
            "state": "pending",
            "prior_receipt_sha256": canonical_sha256(prior) if prior else None,
            "intended_receipt_sha256": "0" * 64,
            "journal": [],
        },
    }


def _retention_policies() -> list[dict[str, Any]]:
    dispositions = {
        "distribution": "remove_on_complete_removal",
        "run_history": "retain_on_keep_data",
        "promoted_overlay": "retain_on_keep_data",
        "cache": "remove_on_complete_removal",
        "secret_free_state": "retain_on_keep_data",
    }
    return [
        {
            "policy_id": f"retention.{name}",
            "retention_class": name,
            "disposition": disposition,
            "expires_at": None,
            "legal_hold_ref": None,
            "export_owner": "user" if disposition == "retain_on_keep_data" else None,
        }
        for name, disposition in dispositions.items()
    ]


def _proof(operation_id: str, observed_at: str, subjects: list[dict[str, Any]] | None = None, backups: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "proof_version": "StateProof/v2",
        "operation_id": operation_id,
        "observed_at": observed_at,
        "subjects": subjects or [],
        "backup_subjects": backups or [],
    }


def _journal_row(
    sequence: int,
    phase: str,
    operation_id: str,
    recorded_at: str,
    entry_ids: list[str] | None = None,
    backup_ids: list[str] | None = None,
    pre_subjects: list[dict[str, Any]] | None = None,
    post_subjects: list[dict[str, Any]] | None = None,
    pre_backups: list[dict[str, Any]] | None = None,
    post_backups: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "phase": phase,
        "recorded_at": recorded_at,
        "operation_id": operation_id,
        "intended_receipt_sha256": "0" * 64,
        "prior_receipt_sha256": None,
        "entry_ids": entry_ids or [],
        "config_entry_ids": [],
        "backup_ids": backup_ids or [],
        "precondition": _proof(operation_id, recorded_at, pre_subjects, pre_backups),
        "precondition_sha256": "0" * 64,
        "postcondition": _proof(operation_id, recorded_at, post_subjects, post_backups),
        "postcondition_sha256": "0" * 64,
        "prior_journal_sha256": None,
        "journal_entry_sha256": "0" * 64,
    }


def _install_journal(
    receipt: dict[str, Any],
    prior: dict[str, Any] | None,
    changed_ids: list[str],
    new_backup_ids: list[str],
    now: str,
    checker: Any,
) -> list[dict[str, Any]]:
    operation_id = receipt["operation"]["operation_id"]
    entries = {entry["entry_id"]: entry for entry in receipt["entries"]}
    backups = {backup["backup_id"]: backup for backup in receipt["backups"]}
    prior_entries = {entry["entry_id"]: entry for entry in prior.get("entries", [])} if prior else {}
    prior_digest = canonical_sha256(prior) if prior else None
    rows: list[dict[str, Any]] = []

    def add(phase: str, **kwargs: Any) -> None:
        rows.append(_journal_row(len(rows) + 1, phase, operation_id, now, **kwargs))

    add("preflight_complete")
    if new_backup_ids:
        backup_rows = [backups[key] for key in new_backup_ids]
        owners = [row["owner_entry_id"] for row in backup_rows]
        pre_subjects: list[dict[str, Any]] = []
        for backup in backup_rows:
            owner_id = backup["owner_entry_id"]
            if prior and owner_id in prior_entries:
                pre_subjects.append(checker.entry_present_subject(prior_entries[owner_id], "prior_receipt", prior_digest))
            else:
                pre_subjects.append(checker.backup_original_subject(backup, entries[owner_id]))
        add(
            "backups_durable",
            entry_ids=owners,
            backup_ids=new_backup_ids,
            pre_subjects=pre_subjects,
            post_subjects=copy.deepcopy(pre_subjects),
            pre_backups=[checker.backup_absent_subject(row) for row in backup_rows],
            post_backups=[checker.backup_present_subject(row) for row in backup_rows],
        )
    add("stage_verified")
    if changed_ids:
        pre_subjects = []
        post_subjects = []
        for entry_id in changed_ids:
            current = entries[entry_id]
            if prior and entry_id in prior_entries:
                before = checker.entry_present_subject(prior_entries[entry_id], "prior_receipt", prior_digest)
            else:
                displaced = next((row for row in receipt["backups"] if row["owner_entry_id"] == entry_id and row["purpose"] == "displaced_user"), None)
                before = checker.backup_original_subject(displaced, current) if displaced else checker.entry_absent_subject(current)
            pre_subjects.append(before)
            post_subjects.append(checker.entry_present_subject(current, "intended_receipt"))
        add("replacement_applied", entry_ids=changed_ids, pre_subjects=pre_subjects, post_subjects=post_subjects)
    add("health_verified")
    add("receipt_committed")
    add("cleanup_complete")
    return rows


def _uninstall_journal(receipt: dict[str, Any], prior: dict[str, Any], now: str, checker: Any) -> list[dict[str, Any]]:
    operation_id = receipt["operation"]["operation_id"]
    prior_digest = canonical_sha256(prior)
    entries = {entry["entry_id"]: entry for entry in receipt["entries"]}
    backups = {backup["backup_id"]: backup for backup in receipt["backups"]}
    prior_backups = {backup["backup_id"]: backup for backup in prior["backups"]}
    retained = set(receipt["preservation"]["keep_data_entry_ids"])
    displaced = {
        row["owner_entry_id"]: row for row in prior["backups"] if row["purpose"] == "displaced_user"
    }
    removable = sorted(set(entries) - retained - set(displaced))
    rows: list[dict[str, Any]] = []

    def add(phase: str, **kwargs: Any) -> None:
        rows.append(_journal_row(len(rows) + 1, phase, operation_id, now, **kwargs))

    add("preflight_complete")
    add("admissions_stopped")
    add("processes_stopped")
    if displaced:
        owner_ids = sorted(displaced)
        backup_ids = [displaced[key]["backup_id"] for key in owner_ids]
        add(
            "user_content_restored",
            entry_ids=owner_ids,
            backup_ids=backup_ids,
            pre_subjects=[checker.entry_present_subject(entries[key], "prior_receipt", prior_digest) for key in owner_ids],
            post_subjects=[checker.backup_original_subject(displaced[key], entries[key]) for key in owner_ids],
            pre_backups=[checker.backup_present_subject(prior_backups[key]) for key in backup_ids],
            post_backups=[checker.backup_present_subject(prior_backups[key]) for key in backup_ids],
        )
    if removable:
        add(
            "owned_entry_removed",
            entry_ids=removable,
            pre_subjects=[checker.entry_present_subject(entries[key], "prior_receipt", prior_digest) for key in removable],
            post_subjects=[checker.entry_absent_subject(entries[key]) for key in removable],
        )
    if retained:
        add("retention_receipt_committed")
    add("removal_verified")
    add("ownership_receipt_removed")
    all_backup_ids = sorted(backups)
    add(
        "cleanup_complete",
        backup_ids=all_backup_ids,
        pre_backups=[checker.backup_present_subject(prior_backups[key]) for key in all_backup_ids],
        post_backups=[checker.backup_absent_subject(prior_backups[key]) for key in all_backup_ids],
    )
    return rows


def _receipt_predecessor(receipt: dict[str, Any], history_dir: Path) -> dict[str, Any] | None:
    wanted = receipt.get("operation", {}).get("prior_receipt_sha256")
    if wanted is None:
        return None
    for path in sorted(history_dir.glob("*.json")) if history_dir.is_dir() else []:
        candidate = load_json(path)
        if canonical_sha256(candidate) == wanted:
            return candidate
    raise ValueError(f"cannot resolve prior receipt {wanted} from {history_dir}")


def _validate_committed_receipt(receipt: dict[str, Any], sage_root: Path, history_dir: Path) -> None:
    predecessor = _receipt_predecessor(receipt, history_dir)
    issues = validate_receipt(receipt, sage_root, predecessor)
    if issues:
        raise ValueError("ownership receipt failed validation:\n" + "\n".join(issues))


def _entry_path(entry: dict[str, Any], roots: dict[str, Path]) -> Path:
    return roots[entry["root_id"]] / entry["relative_path"]


def _verify_entry(entry: dict[str, Any], roots: dict[str, Path]) -> None:
    path = _entry_path(entry, roots)
    _assert_no_symlink_chain(path, entry["entry_id"], include_target=True)
    if not path.exists() or _observed_type(path) != entry["expected_type"]:
        raise ValueError(f"owned entry is absent or changed type: {path}")
    identity = entry["identity"]
    observed = path.stat(follow_symlinks=False)
    observed_key = (observed.st_dev, observed.st_ino)
    expected_key = (identity["device"], identity["inode"])
    link_changed = entry["expected_type"] != "directory" and observed.st_nlink != identity["link_count"]
    if observed_key != expected_key or link_changed:
        raise ValueError(f"owned entry identity changed: {path}")
    if _resource_identity(path) != entry["resource_identity"]:
        raise ValueError(f"owned entry resource identity changed: {path}")
    parent = path.parent
    parent_identity = entry["parent_identity"]
    parent_observed = parent.stat(follow_symlinks=False)
    if (parent_observed.st_dev, parent_observed.st_ino) != (
        parent_identity["device"], parent_identity["inode"],
    ) or _resource_identity(parent) != entry["parent_resource_identity"]:
        raise ValueError(f"owned entry parent identity changed: {parent}")
    if not _marker_matches(path, entry["expected_type"], entry["ownership_marker"]):
        raise ValueError(f"owned entry marker changed: {path}")
    expected_digest = entry.get("content_sha256")
    if expected_digest is not None and _content_sha256(path) != expected_digest:
        raise ValueError(f"owned entry content changed: {path}")


def _verify_backup(backup: dict[str, Any]) -> None:
    path = Path(backup["backup_path"])
    _assert_no_symlink_chain(path, backup["backup_id"], include_target=False)
    if not path.exists() or _observed_type(path) != backup["original_type"]:
        raise ValueError(f"lifecycle backup is missing or changed type: {path}")
    observed = path.stat(follow_symlinks=False)
    identity = backup["backup_identity"]
    if (observed.st_dev, observed.st_ino, observed.st_nlink) != (
        identity["device"], identity["inode"], identity["link_count"],
    ) or _content_sha256(path) != backup["sha256"]:
        raise ValueError(f"lifecycle backup failed identity or digest verification: {path}")
    if _resource_identity(path) != backup["backup_resource_identity"]:
        raise ValueError(f"lifecycle backup resource identity changed: {path}")
    parent = path.parent
    parent_identity = backup["parent_identity"]
    parent_observed = parent.stat(follow_symlinks=False)
    if (parent_observed.st_dev, parent_observed.st_ino) != (
        parent_identity["device"], parent_identity["inode"],
    ) or _resource_identity(parent) != backup["parent_resource_identity"]:
        raise ValueError(f"lifecycle backup parent identity changed: {parent}")


def _verify_roots(receipt: dict[str, Any], roots: dict[str, Path]) -> None:
    recorded = {row["root_id"]: row for row in receipt["roots"]}
    if set(recorded) != set(roots):
        raise ValueError("committed receipt root set changed")
    for root_id, path in roots.items():
        row = recorded[root_id]
        if Path(row["canonical_path"]) != path or row["canonical_path_sha256"] != _path_hash(path):
            raise ValueError(f"committed root path changed: {root_id}")
        _assert_no_symlink_chain(path, root_id, include_target=True)
        if not path.is_dir():
            raise ValueError(f"committed root is missing: {path}")
        observed = path.stat(follow_symlinks=False)
        identity = row["identity"]
        if (observed.st_dev, observed.st_ino) != (identity["device"], identity["inode"]):
            raise ValueError(f"committed root identity changed: {path}")
        if _resource_identity(path) != row["resource_identity"]:
            raise ValueError(f"committed root resource identity changed: {path}")


def _capture_original(path: Path) -> dict[str, Any]:
    observed = path.stat(follow_symlinks=False)
    return {
        "type": _observed_type(path),
        "mode": observed.st_mode & 0o7777,
        "sha256": _content_sha256(path),
        "identity": _fs_identity(path),
        "resource_identity": _resource_identity(path),
    }


def _verify_original(path: Path, original: dict[str, Any], label: str) -> None:
    _assert_no_symlink_chain(path, label, include_target=True)
    if not path.exists() or _observed_type(path) != original["type"]:
        raise ValueError(f"{label} is missing or changed type: {path}")
    observed = path.stat(follow_symlinks=False)
    identity = original["identity"]
    if (observed.st_dev, observed.st_ino, observed.st_nlink) != (
        identity["device"], identity["inode"], identity["link_count"],
    ):
        raise ValueError(f"{label} identity changed: {path}")
    if _resource_identity(path) != original["resource_identity"]:
        raise ValueError(f"{label} resource identity changed: {path}")
    if (observed.st_mode & 0o7777) != original["mode"] or _content_sha256(path) != original["sha256"]:
        raise ValueError(f"{label} mode or content changed: {path}")


def _recovery_path(state_root: Path) -> Path:
    digest = hashlib.sha256(str(state_root).encode("utf-8")).hexdigest()[:20]
    return state_root.parent / f".sage-lifecycle-recovery-{digest}.json"


def _recovery_payload(record: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(record)
    payload.pop("integrity_sha256", None)
    return payload


def _write_recovery(path: Path, record: dict[str, Any]) -> None:
    sealed = _recovery_payload(record)
    sealed["integrity_sha256"] = canonical_sha256(sealed)
    atomic_write_json(path, sealed, 0o600)
    record.clear()
    record.update(sealed)


def _persist_recovery_journal(
    record: dict[str, Any],
    path: Path,
    rows: list[dict[str, Any]],
) -> None:
    intended = copy.deepcopy(record["intended_receipt"])
    intended["operation"]["journal"] = copy.deepcopy(rows)
    checker = _load_phase0_checker(Path(record["repository"]) / "sage")
    checker.refresh_receipt_fixture_integrity(intended)
    expected = record.get("intended_receipt_sha256")
    observed = intended["operation"]["intended_receipt_sha256"]
    if expected is not None and expected != observed:
        raise ValueError("lifecycle recovery intended receipt changed while journaling")
    record["intended_receipt_sha256"] = observed
    record["intended_receipt"] = intended
    record["durable_journal"] = copy.deepcopy(intended["operation"]["journal"])
    if isinstance(record.get("journal_plan"), list):
        tail = copy.deepcopy(record["journal_plan"][len(rows):])
        record["journal_plan"] = copy.deepcopy(record["durable_journal"]) + tail
        if isinstance(record.get("final_receipt"), dict):
            final_receipt = copy.deepcopy(record["final_receipt"])
            final_receipt["operation"]["journal"] = copy.deepcopy(record["journal_plan"])
            checker.refresh_receipt_fixture_integrity(final_receipt)
            if final_receipt["operation"]["intended_receipt_sha256"] != observed:
                raise ValueError("lifecycle final receipt changed while journaling")
            record["final_receipt"] = final_receipt
    _write_recovery(path, record)


def _stamp_journal_row(row: dict[str, Any], observed_at: str | None = None) -> None:
    observed_at = observed_at or utc_now()
    row["recorded_at"] = observed_at
    row["precondition"]["observed_at"] = observed_at
    row["postcondition"]["observed_at"] = observed_at


def _journal_phase_index(rows: list[dict[str, Any]], phase: str) -> int | None:
    matching = [index for index, row in enumerate(rows) if row["phase"] == phase]
    return matching[-1] if matching else None


def _persist_install_through(
    record: dict[str, Any],
    recovery_path: Path,
    phase: str,
    *,
    stamp: bool = True,
) -> None:
    plan = record.get("journal_plan")
    if not isinstance(plan, list):
        raise ValueError("install recovery is missing its journal plan")
    target_index = _journal_phase_index(plan, phase)
    if target_index is None:
        return
    while len(record["durable_journal"]) <= target_index:
        index = len(record["durable_journal"])
        if stamp:
            observed_at = utc_now()
            for row in record["journal_plan"][index:]:
                _stamp_journal_row(row, observed_at)
        _persist_recovery_journal(record, recovery_path, record["journal_plan"][:index + 1])
        _test_crash_at_phase(record["durable_journal"][index]["phase"])


def _load_recovery(path: Path, state_root: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    if path.is_symlink():
        raise ValueError(f"lifecycle recovery record must not be a symlink: {path}")
    record = load_json(path)
    if not isinstance(record, dict) or record.get("schema_version") != "1.0":
        raise ValueError(f"invalid lifecycle recovery record: {path}")
    integrity = record.get("integrity_sha256")
    if not isinstance(integrity, str) or integrity != canonical_sha256(_recovery_payload(record)):
        raise ValueError(f"lifecycle recovery integrity failed: {path}")
    if record.get("state_root") != str(state_root) or record.get("kind") not in {"install", "update", "uninstall"}:
        raise ValueError(f"lifecycle recovery scope is invalid: {path}")
    operation_id = record.get("operation_id")
    if (
        not isinstance(operation_id, str)
        or len(operation_id) != 35
        or not operation_id.startswith("op-")
        or any(character not in "0123456789abcdef" for character in operation_id[3:])
    ):
        raise ValueError(f"lifecycle recovery operation ID is invalid: {path}")
    return record


def _clear_directory_contents(path: Path) -> None:
    for child in list(path.iterdir()):
        _remove_path(child)


def _fsync_tree(path: Path) -> None:
    for child in sorted(path.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if child.is_symlink():
            continue
        descriptor = os.open(child, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _restore_snapshot(target: Path, snapshot: Path, expected_sha256: str, expected_mode: int) -> None:
    if not snapshot.is_dir() or tree_sha256(snapshot) != expected_sha256:
        raise ValueError(f"lifecycle recovery snapshot is missing or corrupt: {snapshot}")
    if not target.is_dir() or target.is_symlink():
        raise ValueError(f"mutable lifecycle target changed type during recovery: {target}")
    _clear_directory_contents(target)
    shutil.copytree(snapshot, target, dirs_exist_ok=True, symlinks=True)
    target.chmod(expected_mode)
    if tree_sha256(target) != expected_sha256:
        raise ValueError(f"mutable lifecycle snapshot did not restore exactly: {target}")


def _test_crash(counter_name: str, count: int) -> None:
    raw = os.environ.get(counter_name)
    if raw is not None and raw.isdigit() and count >= int(raw):
        os._exit(86)


def _test_crash_at_phase(phase: str) -> None:
    if os.environ.get("SAGE_TEST_CRASH_AT_PHASE") == phase:
        os._exit(86)


def _roots_from_paths(skills_root: Path, bin_root: Path, data_root: Path, state_root: Path, backup_root: Path) -> dict[str, Path]:
    return {
        "skills": skills_root,
        "bin": bin_root,
        "distribution": data_root.parent,
        "state": state_root,
        "backups": backup_root,
    }


def _check_root_separation(roots: dict[str, Path], repository: Path) -> None:
    values = list(roots.items())
    for index, (left_id, left) in enumerate(values):
        if _paths_overlap(left, repository):
            raise ValueError(f"destination root {left_id} overlaps the protected source checkout: {left}")
        for right_id, right in values[index + 1:]:
            if _paths_overlap(left, right):
                raise ValueError(f"destination roots overlap: {left_id}={left}, {right_id}={right}")


@contextmanager
def _operation_lock(state_root: Path, has_receipt: bool) -> Iterator[None]:
    del state_root, has_receipt  # The lock is stable and independent of mutable destinations.
    with sage_operation_lock():
        yield


def _health_check(data_root: Path, bin_root: Path, state_root: Path) -> None:
    commands = [
        ["bash", "-n", str(data_root / "install.sh")],
        ["bash", "-n", str(data_root / "uninstall.sh")],
        [sys.executable, str(data_root / "scripts/generate-skill-bundle.py"), "--check"],
        [str(bin_root / "sage-light"), "--help"],
        [str(bin_root / "sage-promote"), "--help"],
        [str(bin_root / "sage-light"), "validate", str(data_root / "artifacts/fixtures/valid/zero-delegation.json")],
        [str(bin_root / "sage-light"), "knowledge", "list"],
    ]
    for command in commands:
        result = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "SAGE_STATE_ROOT": str(state_root), "PYTHONDONTWRITEBYTECODE": "1"},
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise ValueError(f"installed health check failed ({' '.join(command)}): {detail}")
    for skill in ("sage", "sage-promote"):
        metadata = (data_root / f"skills/{skill}/agents/openai.yaml").read_text(encoding="utf-8")
        if "allow_implicit_invocation: false" not in metadata:
            raise ValueError(f"installed skill {skill} is not explicit-only")


def _install_recovery_entries(
    skills_root: Path,
    bin_root: Path,
    data_root: Path,
    state_root: Path,
    installation_id: str,
    operation_id: str,
) -> list[dict[str, Any]]:
    definitions = [
        ("skill.sage", skills_root / "sage", "directory", False),
        ("skill.sage-promote", skills_root / "sage-promote", "directory", False),
        ("bin.sage-light", bin_root / "sage-light", "file", False),
        ("bin.sage-promote", bin_root / "sage-promote", "file", False),
        ("bin.sage-uninstall", bin_root / "sage-uninstall", "file", False),
        ("distribution.light", data_root, "directory", False),
        ("state.runs", state_root / "runs", "directory", True),
        ("state.promoted-overlay", state_root / "promoted-overlay", "directory", True),
        ("state.promoted-index", state_root / "promoted-index", "directory", True),
        ("state.settings", state_root / "settings", "directory", True),
        ("state.knowledge-repository", state_root / "knowledge-repository", "directory", False),
        ("state.lifecycle", state_root / "lifecycle", "directory", True),
    ]
    return [
        {
            "entry_id": entry_id,
            "target": str(target),
            "stage": str(target.parent / f".sage-stage-{operation_id}-{entry_id}"),
            "expected_type": expected_type,
            "mutable": mutable,
            "marker": f"sage-owned:{installation_id}:{entry_id}",
            "replace": False,
            "original": None,
            "installed": None,
            "backup_id": None,
            "backup_path": None,
        }
        for entry_id, target, expected_type, mutable in definitions
    ]


def _validate_install_recovery(
    record: dict[str, Any],
    roots: dict[str, Path],
    data_root: Path,
) -> list[dict[str, Any]]:
    expected_roots = {key: str(value) for key, value in roots.items()}
    if record.get("roots") != expected_roots or record.get("data_root") != str(data_root):
        raise ValueError("pending lifecycle recovery belongs to different destination roots")
    installation_id = record.get("installation_id")
    if not isinstance(installation_id, str) or not installation_id.startswith("sage-"):
        raise ValueError("pending lifecycle recovery has an invalid installation ID")
    expected = _install_recovery_entries(
        roots["skills"], roots["bin"], data_root, roots["state"], installation_id, record["operation_id"],
    )
    rows = record.get("entries")
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise ValueError("pending lifecycle recovery has an invalid entry set")
    expected_by_id = {row["entry_id"]: row for row in expected}
    if {row.get("entry_id") for row in rows if isinstance(row, dict)} != set(expected_by_id):
        raise ValueError("pending lifecycle recovery entry IDs are invalid")
    for row in rows:
        template = expected_by_id[row["entry_id"]]
        for field in ("target", "stage", "expected_type", "mutable", "marker"):
            if row.get(field) != template[field]:
                raise ValueError(f"pending lifecycle recovery changed {row['entry_id']} {field}")
        if row.get("replace") not in {True, False}:
            raise ValueError(f"pending lifecycle recovery has invalid replace state for {row['entry_id']}")
        installed = row.get("installed")
        if row["replace"]:
            if not isinstance(installed, dict) or installed.get("type") != row["expected_type"]:
                raise ValueError(f"pending lifecycle recovery lacks installed identity for {row['entry_id']}")
            if installed.get("resource_identity", {}).get("resolved_path_sha256") != _path_hash(Path(row["target"])):
                raise ValueError(f"pending lifecycle recovery installed path escaped for {row['entry_id']}")
            if installed.get("stage_resource_identity", {}).get("resolved_path_sha256") != _path_hash(Path(row["stage"])):
                raise ValueError(f"pending lifecycle recovery stage path escaped for {row['entry_id']}")
            if not isinstance(installed.get("stage_identity"), dict):
                raise ValueError(f"pending lifecycle recovery stage identity is invalid for {row['entry_id']}")
        elif installed is not None:
            raise ValueError(f"pending lifecycle recovery has an unexpected installed identity for {row['entry_id']}")
        backup_id = row.get("backup_id")
        backup_path = row.get("backup_path")
        if backup_id is None:
            if backup_path is not None:
                raise ValueError("pending lifecycle recovery has a path without a backup ID")
        else:
            if not isinstance(backup_id, str) or not backup_id.startswith(f"backup-{record['operation_id']}-"):
                raise ValueError("pending lifecycle recovery backup ID is invalid")
            expected_path = roots["backups"] / backup_id / "payload"
            if backup_path != str(expected_path):
                raise ValueError("pending lifecycle recovery backup path escaped its root")
    created_roots = record.get("created_roots")
    allowed_roots = {str(path) for path in roots.values()}
    if (
        not isinstance(created_roots, list)
        or len(set(created_roots)) != len(created_roots)
        or any(path not in allowed_roots for path in created_roots)
    ):
        raise ValueError("pending lifecycle recovery created-root set is invalid")
    root_state = record.get("root_state")
    if not isinstance(root_state, list):
        raise ValueError("pending lifecycle recovery root state is invalid")
    if root_state:
        if {row.get("root_id") for row in root_state if isinstance(row, dict)} != set(roots):
            raise ValueError("pending lifecycle recovery root identity set is invalid")
        for row in root_state:
            root_id = row["root_id"]
            if row.get("canonical_path") != str(roots[root_id]) or row.get("canonical_path_sha256") != _path_hash(roots[root_id]):
                raise ValueError(f"pending lifecycle recovery root path changed: {root_id}")
    snapshots = record.get("snapshots")
    if not isinstance(snapshots, list):
        raise ValueError("pending lifecycle recovery snapshot set is invalid")
    snapshot_container_record = record.get("snapshot_container")
    allowed_snapshot_ids = {"state.promoted-overlay", "state.promoted-index"}
    snapshot_ids = [row.get("entry_id") for row in snapshots if isinstance(row, dict)]
    if len(snapshot_ids) != len(snapshots) or len(set(snapshot_ids)) != len(snapshot_ids) or not set(snapshot_ids) <= allowed_snapshot_ids:
        raise ValueError("pending lifecycle recovery snapshot IDs are invalid")
    rows_by_id = {row["entry_id"]: row for row in rows}
    snapshot_container = roots["backups"] / f".sage-recovery-{record['operation_id']}"
    if snapshot_container_record is None:
        if snapshots:
            raise ValueError("pending lifecycle snapshots lack a container identity")
    elif (
        not isinstance(snapshot_container_record, dict)
        or snapshot_container_record.get("path") != str(snapshot_container)
        or snapshot_container_record.get("resource_identity", {}).get("resolved_path_sha256") != _path_hash(snapshot_container)
        or not isinstance(snapshot_container_record.get("identity"), dict)
    ):
        raise ValueError("pending lifecycle snapshot container identity is invalid")
    for snapshot in snapshots:
        entry = rows_by_id[snapshot["entry_id"]]
        if (
            snapshot.get("target") != entry["target"]
            or snapshot.get("snapshot_path") != str(snapshot_container / snapshot["entry_id"])
            or snapshot.get("marker") != entry["marker"]
            or not isinstance(snapshot.get("sha256"), str)
            or len(snapshot["sha256"]) != 64
            or not isinstance(snapshot.get("mode"), int)
            or snapshot.get("resource_identity", {}).get("resolved_path_sha256") != _path_hash(Path(snapshot["snapshot_path"]))
            or not isinstance(snapshot.get("identity"), dict)
        ):
            raise ValueError(f"pending lifecycle recovery snapshot scope is invalid for {snapshot['entry_id']}")
    intended = record.get("intended_receipt")
    intended_hash = record.get("intended_receipt_sha256")
    durable_journal = record.get("durable_journal")
    journal_plan = record.get("journal_plan")
    final_receipt = record.get("final_receipt")
    checkpoint_hash = record.get("commit_checkpoint_sha256")
    if intended is None:
        if (
            intended_hash is not None
            or durable_journal != []
            or journal_plan is not None
            or final_receipt is not None
            or checkpoint_hash is not None
            or record.get("phase") != "staging"
        ):
            raise ValueError("pending lifecycle recovery is missing its pre-mutation receipt intent")
    elif (
        not isinstance(intended, dict)
        or not isinstance(intended_hash, str)
        or not isinstance(journal_plan, list)
        or not isinstance(durable_journal, list)
        or intended.get("operation", {}).get("operation_id") != record["operation_id"]
        or intended.get("operation", {}).get("intended_receipt_sha256") != intended_hash
        or intended.get("operation", {}).get("journal") != durable_journal
        or durable_journal != journal_plan[:len(durable_journal)]
    ):
        raise ValueError("pending lifecycle recovery receipt intent or durable journal is inconsistent")
    if final_receipt is None:
        if checkpoint_hash is not None:
            raise ValueError("pending lifecycle recovery has a checkpoint without a final receipt")
    elif (
        not isinstance(final_receipt, dict)
        or (checkpoint_hash is not None and not isinstance(checkpoint_hash, str))
        or final_receipt.get("operation", {}).get("operation_id") != record["operation_id"]
        or final_receipt.get("operation", {}).get("state") != "committed"
        or final_receipt.get("operation", {}).get("intended_receipt_sha256") != intended_hash
        or final_receipt.get("operation", {}).get("journal") != journal_plan
    ):
        raise ValueError("pending lifecycle final receipt or commit checkpoint is inconsistent")
    return rows


def _verify_original_payload(path: Path, original: dict[str, Any], label: str) -> None:
    _assert_no_symlink_chain(path, label, include_target=True)
    if not path.exists() or _observed_type(path) != original["type"]:
        raise ValueError(f"{label} is missing or changed type: {path}")
    observed = path.stat(follow_symlinks=False)
    identity = original["identity"]
    if (observed.st_dev, observed.st_ino, observed.st_nlink) != (
        identity["device"], identity["inode"], identity["link_count"],
    ) or (observed.st_mode & 0o7777) != original["mode"] or _content_sha256(path) != original["sha256"]:
        raise ValueError(f"{label} identity, mode, or content changed: {path}")


def _verify_installed_recovery_target(path: Path, row: dict[str, Any]) -> None:
    installed = row["installed"]
    _assert_no_symlink_chain(path, row["entry_id"], include_target=True)
    if not path.exists() or _observed_type(path) != installed["type"]:
        raise ValueError(f"installed recovery target is missing or changed type: {path}")
    observed = path.stat(follow_symlinks=False)
    identity = installed["identity"]
    link_changed = installed["type"] != "directory" and observed.st_nlink != identity["link_count"]
    if (observed.st_dev, observed.st_ino) != (identity["device"], identity["inode"]) or link_changed:
        raise ValueError(f"installed recovery target identity changed: {path}")
    if _resource_identity(path) != installed["resource_identity"]:
        raise ValueError(f"installed recovery target resource identity changed: {path}")
    if (observed.st_mode & 0o7777) != installed["mode"]:
        raise ValueError(f"installed recovery target mode changed: {path}")
    if not row["mutable"] and _content_sha256(path) != installed["sha256"]:
        raise ValueError(f"installed recovery target content changed: {path}")


def _verify_recovery_stage(path: Path, row: dict[str, Any], *, require_original_path: bool = True) -> None:
    installed = row.get("installed")
    if not row.get("replace") or not isinstance(installed, dict):
        raise ValueError(f"unproven lifecycle stage must be preserved for manual review: {path}")
    _assert_no_symlink_chain(path, f"recovery stage for {row['entry_id']}", include_target=True)
    if _observed_type(path) != installed["type"]:
        raise ValueError(f"lifecycle recovery stage changed type: {path}")
    observed = path.stat(follow_symlinks=False)
    identity = installed["stage_identity"]
    if (observed.st_dev, observed.st_ino, observed.st_nlink) != (
        identity["device"], identity["inode"], identity["link_count"],
    ):
        raise ValueError(f"lifecycle recovery stage identity changed: {path}")
    if require_original_path and _resource_identity(path) != installed["stage_resource_identity"]:
        raise ValueError(f"lifecycle recovery stage path changed: {path}")
    if (observed.st_mode & 0o7777) != installed["mode"] or _content_sha256(path) != installed["sha256"]:
        raise ValueError(f"lifecycle recovery stage content or path changed: {path}")


def _verify_recovery_snapshot_container(
    record: dict[str, Any],
    container: Path,
    *,
    require_original_path: bool = True,
) -> None:
    proof = record.get("snapshot_container")
    snapshots = record.get("snapshots", [])
    if not isinstance(proof, dict):
        raise ValueError(f"unproven lifecycle snapshot container must be preserved for manual review: {container}")
    _assert_no_symlink_chain(container, "lifecycle snapshot container", include_target=True)
    if not container.is_dir():
        raise ValueError(f"lifecycle snapshot container changed type: {container}")
    observed = container.stat(follow_symlinks=False)
    identity = proof["identity"]
    if (observed.st_dev, observed.st_ino, observed.st_nlink) != (
        identity["device"], identity["inode"], identity["link_count"],
    ) or (require_original_path and _resource_identity(container) != proof["resource_identity"]):
        raise ValueError(f"lifecycle snapshot container identity changed: {container}")
    expected_children = {
        Path(row["snapshot_path"])
        if require_original_path
        else container / Path(row["snapshot_path"]).name
        for row in snapshots
    }
    observed_children = set(container.iterdir())
    if observed_children != expected_children:
        raise ValueError(f"lifecycle snapshot container has ambiguous extra or missing content: {container}")
    for snapshot in snapshots:
        path = (
            Path(snapshot["snapshot_path"])
            if require_original_path
            else container / Path(snapshot["snapshot_path"]).name
        )
        _assert_no_symlink_chain(path, f"snapshot for {snapshot['entry_id']}", include_target=True)
        if not path.is_dir() or path.is_symlink():
            raise ValueError(f"lifecycle recovery snapshot changed type: {path}")
        item = path.stat(follow_symlinks=False)
        expected = snapshot["identity"]
        if (item.st_dev, item.st_ino, item.st_nlink) != (
            expected["device"], expected["inode"], expected["link_count"],
        ) or (require_original_path and _resource_identity(path) != snapshot["resource_identity"]):
            raise ValueError(f"lifecycle recovery snapshot identity changed: {path}")
        if (item.st_mode & 0o7777) != snapshot["mode"] or tree_sha256(path) != snapshot["sha256"]:
            raise ValueError(f"lifecycle recovery snapshot content changed: {path}")


def _remove_directory_contents_by_fd(directory_fd: int, display_path: Path) -> None:
    for entry in list(os.scandir(directory_fd)):
        child_path = display_path / entry.name
        observed = entry.stat(follow_symlinks=False)
        if stat.S_ISDIR(observed.st_mode):
            flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
            child_fd = os.open(entry.name, flags, dir_fd=directory_fd)
            try:
                if not os.path.samestat(observed, os.fstat(child_fd)):
                    raise ValueError(f"recovery cleanup child identity changed: {child_path}")
                _remove_directory_contents_by_fd(child_fd, child_path)
                current = os.stat(entry.name, dir_fd=directory_fd, follow_symlinks=False)
                if not os.path.samestat(current, os.fstat(child_fd)):
                    raise ValueError(f"recovery cleanup child was swapped: {child_path}")
            finally:
                os.close(child_fd)
            os.rmdir(entry.name, dir_fd=directory_fd)
        else:
            current = os.stat(entry.name, dir_fd=directory_fd, follow_symlinks=False)
            if not os.path.samestat(observed, current):
                raise ValueError(f"recovery cleanup child was swapped: {child_path}")
            os.unlink(entry.name, dir_fd=directory_fd)


def _remove_identity_pinned_capture(path: Path, verify: Any) -> None:
    """Delete through pinned descriptors after the contract's immediate live-state recheck.

    This closes pathname substitution by an independent filesystem actor. POSIX has no
    compare-and-unlink-by-inode call; arbitrary code executing inside this trusted
    lifecycle process would already hold the same direct deletion authority.
    """
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if nofollow == 0:
        raise RuntimeError("identity-pinned cleanup requires O_NOFOLLOW")
    parent_fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    target_fd: int | None = None
    try:
        before = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        flags = os.O_RDONLY | nofollow
        if stat.S_ISDIR(before.st_mode):
            flags |= getattr(os, "O_DIRECTORY", 0)
        target_fd = os.open(path.name, flags, dir_fd=parent_fd)
        pinned = os.fstat(target_fd)
        if not os.path.samestat(before, pinned):
            raise ValueError(f"recovery cleanup capture changed while opening: {path}")
        verify(path)
        current = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
        if not os.path.samestat(current, pinned):
            raise ValueError(f"recovery cleanup quarantine was swapped; preserving both states: {path}")
        if stat.S_ISDIR(pinned.st_mode):
            _remove_directory_contents_by_fd(target_fd, path)
            current = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
            if not os.path.samestat(current, os.fstat(target_fd)):
                raise ValueError(f"recovery cleanup quarantine was swapped; preserving it: {path}")
            os.close(target_fd)
            target_fd = None
            os.rmdir(path.name, dir_fd=parent_fd)
        else:
            os.unlink(path.name, dir_fd=parent_fd)
    finally:
        if target_fd is not None:
            os.close(target_fd)
        os.close(parent_fd)


def _cleanup_recovery_artifacts(record: dict[str, Any]) -> None:
    captures: list[tuple[Path, Path, Any]] = []
    for row in record.get("entries", []):
        stage = Path(row["stage"])
        quarantine = stage.parent / f".sage-cleanup-{record['operation_id']}-{row['entry_id']}"
        if stage.exists() or stage.is_symlink() or quarantine.exists() or quarantine.is_symlink():
            captures.append((
                stage,
                quarantine,
                lambda path, recovery_row=row: _verify_recovery_stage(
                    path, recovery_row, require_original_path=False,
                ),
            ))
    snapshot_container = Path(record["roots"]["backups"]) / f".sage-recovery-{record['operation_id']}"
    snapshot_quarantine = snapshot_container.parent / f".sage-cleanup-{record['operation_id']}-snapshots"
    if (
        snapshot_container.exists()
        or snapshot_container.is_symlink()
        or snapshot_quarantine.exists()
        or snapshot_quarantine.is_symlink()
    ):
        captures.append((
            snapshot_container,
            snapshot_quarantine,
            lambda path: _verify_recovery_snapshot_container(
                record, path, require_original_path=False,
            ),
        ))

    captured: list[tuple[Path, Path, Any]] = []
    for original, quarantine, verify in captures:
        original_present = original.exists() or original.is_symlink()
        quarantine_present = quarantine.exists() or quarantine.is_symlink()
        if original_present and quarantine_present:
            raise ValueError(
                f"lifecycle cleanup found both live and quarantined recovery artifacts; preserving both: {original}"
            )
        if original_present:
            _move_path(original, quarantine)
        try:
            verify(quarantine)
        except BaseException:
            if (quarantine.exists() or quarantine.is_symlink()) and not (original.exists() or original.is_symlink()):
                _move_path(quarantine, original)
            raise
        captured.append((original, quarantine, verify))

    # Recheck the captured inode/content immediately before deletion. Any path that
    # reappears at the public name or changes under quarantine makes cleanup ambiguous.
    for original, quarantine, verify in captured:
        if original.exists() or original.is_symlink():
            raise ValueError(f"lifecycle recovery artifact reappeared during cleanup; preserving it: {original}")
        _remove_identity_pinned_capture(quarantine, verify)


def _cleanup_recovery_paths(record: dict[str, Any], recovery_path: Path) -> None:
    _cleanup_recovery_artifacts(record)
    recovery_path.unlink(missing_ok=True)


def _install_commit_checkpoint(final_receipt: dict[str, Any], checker: Any) -> dict[str, Any]:
    rows = final_receipt["operation"]["journal"]
    index = _journal_phase_index(rows, "receipt_committed")
    if index is None:
        raise ValueError("install journal lacks receipt_committed")
    checkpoint = copy.deepcopy(final_receipt)
    checkpoint["operation"]["state"] = "pending"
    checkpoint["operation"]["journal"] = copy.deepcopy(rows[:index + 1])
    checker.refresh_receipt_fixture_integrity(checkpoint)
    return checkpoint


def _finish_install_commit(
    record: dict[str, Any],
    recovery_path: Path,
    roots: dict[str, Path],
    data_root: Path,
    repository: Path,
) -> None:
    final_receipt = record.get("final_receipt")
    if not isinstance(final_receipt, dict):
        raise ValueError("pending install has no verified final receipt")
    checker = _load_phase0_checker(repository / "sage")
    if record.get("commit_checkpoint_sha256") is None:
        receipt_index = _journal_phase_index(record["journal_plan"], "receipt_committed")
        if receipt_index is None or len(record["durable_journal"]) != receipt_index:
            raise ValueError("install journal is not ready to commit its receipt")
        observed_at = utc_now()
        for row in record["journal_plan"][receipt_index:]:
            _stamp_journal_row(row, observed_at)
        final_receipt = copy.deepcopy(final_receipt)
        final_receipt["operation"]["journal"] = copy.deepcopy(record["journal_plan"])
        checker.refresh_receipt_fixture_integrity(final_receipt)
        record["journal_plan"] = copy.deepcopy(final_receipt["operation"]["journal"])
        record["final_receipt"] = final_receipt
        checkpoint = _install_commit_checkpoint(final_receipt, checker)
        record["commit_checkpoint_sha256"] = canonical_sha256(checkpoint)
        _write_recovery(recovery_path, record)
    else:
        checkpoint = _install_commit_checkpoint(final_receipt, checker)
    predecessor = _receipt_predecessor(final_receipt, roots["state"] / "lifecycle/receipts")
    final_issues = validate_receipt(final_receipt, repository / "sage", predecessor)
    if final_issues:
        raise ValueError("pending install final receipt failed validation:\n" + "\n".join(final_issues))
    if canonical_sha256(checkpoint) != record.get("commit_checkpoint_sha256"):
        raise ValueError("pending install commit checkpoint changed")
    checkpoint_issues = validate_receipt(checkpoint, repository / "sage", predecessor)
    if checkpoint_issues:
        raise ValueError("pending install commit checkpoint failed validation:\n" + "\n".join(checkpoint_issues))

    _verify_roots(final_receipt, roots)
    for entry in final_receipt["entries"]:
        _verify_entry(entry, roots)
    for backup in final_receipt["backups"]:
        _verify_backup(backup)
    _health_check(data_root, roots["bin"], roots["state"])

    current_path = roots["state"] / "lifecycle/current.json"
    if current_path.is_file():
        current = load_json(current_path)
        if current.get("operation", {}).get("operation_id") == record["operation_id"]:
            if current.get("operation", {}).get("state") == "committed":
                if canonical_sha256(current) != canonical_sha256(record["final_receipt"]):
                    raise ValueError("committed install receipt differs from its recovery record")
                _validate_committed_receipt(current, repository / "sage", roots["state"] / "lifecycle/receipts")
                _cleanup_recovery_paths(record, recovery_path)
                return
            if canonical_sha256(current) != record["commit_checkpoint_sha256"]:
                raise ValueError("pending install current receipt differs from its commit checkpoint")
        else:
            expected_prior = record.get("prior_receipt_sha256")
            if expected_prior is None or canonical_sha256(current) != expected_prior:
                raise ValueError("current receipt changed before install commit")
            atomic_write_json(current_path, checkpoint, 0o600)
    else:
        if record.get("prior_receipt_sha256") is not None:
            raise ValueError("prior ownership receipt disappeared before install commit")
        atomic_write_json(current_path, checkpoint, 0o600)

    _persist_install_through(record, recovery_path, "receipt_committed", stamp=False)
    _cleanup_recovery_artifacts(record)
    _persist_install_through(record, recovery_path, "cleanup_complete")

    final_receipt = copy.deepcopy(record["final_receipt"])
    final_receipt["operation"]["journal"] = copy.deepcopy(record["journal_plan"])
    checker.refresh_receipt_fixture_integrity(final_receipt)
    if final_receipt["operation"]["intended_receipt_sha256"] != record["intended_receipt_sha256"]:
        raise ValueError("final install receipt diverged from its pre-mutation intent")
    final_issues = validate_receipt(final_receipt, repository / "sage", predecessor)
    if final_issues:
        raise ValueError("final install receipt failed validation:\n" + "\n".join(final_issues))
    record["final_receipt"] = copy.deepcopy(final_receipt)
    _write_recovery(recovery_path, record)
    history_path = roots["state"] / "lifecycle/receipts" / f"{record['operation_id']}.json"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(history_path, final_receipt, 0o600)
    atomic_write_json(current_path, final_receipt, 0o600)
    recovery_path.unlink()


def _recover_install_operation(
    record: dict[str, Any],
    recovery_path: Path,
    roots: dict[str, Path],
    data_root: Path,
    repository: Path,
) -> str:
    if record.get("repository") != str(repository):
        raise ValueError("pending lifecycle recovery belongs to a different source checkout")
    rows = _validate_install_recovery(record, roots, data_root)
    if isinstance(record.get("final_receipt"), dict):
        _finish_install_commit(record, recovery_path, roots, data_root, repository)
        return "committed"
    current_path = roots["state"] / "lifecycle/current.json"
    if current_path.is_file():
        current = load_json(current_path)
        if current.get("operation", {}).get("operation_id") == record["operation_id"]:
            _finish_install_commit(record, recovery_path, roots, data_root, repository)
            return "committed"
        expected_prior = record.get("prior_receipt_sha256")
        if expected_prior is None or canonical_sha256(current) != expected_prior:
            raise ValueError("current receipt changed while a lifecycle recovery was pending")
    elif record.get("prior_receipt_sha256") is not None:
        raise ValueError("prior ownership receipt disappeared during lifecycle recovery")

    if record.get("intended_receipt") is not None:
        predecessor = current if current_path.is_file() else None
        issues = validate_receipt(record["intended_receipt"], repository / "sage", predecessor)
        if issues:
            raise ValueError("pending lifecycle receipt intent failed validation:\n" + "\n".join(issues))

    phase = record.get("phase")
    if phase not in {"staging", "replacing", "reconciling"}:
        raise ValueError(f"pending lifecycle recovery has invalid phase {phase!r}")
    if record["root_state"]:
        for root_row in record["root_state"]:
            _verify_root_if_present(root_row)
            if not Path(root_row["canonical_path"]).is_dir():
                raise ValueError(f"lifecycle recovery root disappeared: {root_row['canonical_path']}")
    elif phase != "staging":
        raise ValueError("lifecycle recovery cannot mutate without recorded root identities")
    if phase != "staging":
        for row in reversed(rows):
            if not row["replace"]:
                continue
            target = Path(row["target"])
            original = row.get("original")
            backup_path = Path(row["backup_path"]) if row.get("backup_path") else None
            if original is None:
                if target.exists() or target.is_symlink():
                    if not _marker_matches(target, row["expected_type"], row["marker"]):
                        raise ValueError(f"refusing to remove an ambiguous recovery target: {target}")
                    _verify_installed_recovery_target(target, row)
                    _remove_path(target)
            elif backup_path is not None and backup_path.exists():
                _verify_original_payload(backup_path, original, f"recovery backup for {row['entry_id']}")
                if target.exists() or target.is_symlink():
                    if not _marker_matches(target, row["expected_type"], row["marker"]):
                        raise ValueError(f"refusing to overwrite an ambiguous recovery target: {target}")
                    _verify_installed_recovery_target(target, row)
                    _remove_path(target)
                _move_path(backup_path, target)
                _verify_original(target, original, f"restored original for {row['entry_id']}")
            else:
                _verify_original(target, original, f"unmoved original for {row['entry_id']}")

        for snapshot in record.get("snapshots", []):
            target = Path(snapshot["target"])
            if not _marker_matches(target, "directory", snapshot["marker"]):
                raise ValueError(f"mutable recovery target lost its ownership marker: {target}")
            _restore_snapshot(
                target,
                Path(snapshot["snapshot_path"]),
                snapshot["sha256"],
                snapshot["mode"],
            )

    history_path = roots["state"] / "lifecycle/receipts" / f"{record['operation_id']}.json"
    if history_path.is_file():
        orphan = load_json(history_path)
        if orphan.get("operation", {}).get("operation_id") != record["operation_id"]:
            raise ValueError(f"recovery history path contains an unrelated receipt: {history_path}")
        history_path.unlink()
    for row in rows:
        if row.get("backup_path"):
            container = Path(row["backup_path"]).parent
            if container.is_dir():
                if any(container.iterdir()):
                    raise ValueError(f"recovery backup container is unexpectedly nonempty: {container}")
                container.rmdir()
    _cleanup_recovery_paths(record, recovery_path)
    for raw_path in sorted(record.get("created_roots", []), key=lambda item: len(Path(item).parts), reverse=True):
        path = Path(raw_path)
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()
    return "rolled_back"


def install(
    *,
    repository: Path,
    skills_root: Path,
    bin_root: Path,
    data_root: Path,
    state_root: Path,
    backup_root: Path,
) -> dict[str, Any]:
    repository = _canonical_path(repository)
    skills_root = _canonical_path(skills_root)
    bin_root = _canonical_path(bin_root)
    data_root = _canonical_path(data_root)
    state_root = _canonical_path(state_root)
    backup_root = _canonical_path(backup_root)
    if not (repository / "sage/scripts/check-phase0.py").is_file():
        raise ValueError(f"not a Sage source checkout: {repository}")
    roots = _roots_from_paths(skills_root, bin_root, data_root, state_root, backup_root)
    _check_root_separation(roots, repository)
    current_path = state_root / "lifecycle/current.json"
    recovery_path = _recovery_path(state_root)
    with _operation_lock(state_root, current_path.is_file()):
        pending = _load_recovery(recovery_path, state_root)
        if pending is not None:
            if pending["kind"] == "uninstall":
                raise ValueError("an interrupted uninstall must be resumed with sage-uninstall before installing")
            recovery_outcome = _recover_install_operation(pending, recovery_path, roots, data_root, repository)
            if recovery_outcome == "committed":
                recovered_receipt = load_json(current_path)
                return {
                    "operation": pending["kind"],
                    "recovered": True,
                    "installation_id": recovered_receipt["installation_id"],
                    "receipt": str(current_path),
                    "history_receipt": str(
                        state_root / "lifecycle/receipts" / f"{pending['operation_id']}.json"
                    ),
                    "manifest_sha256": recovered_receipt["source"]["manifest_sha256"],
                }

        prior = load_json(current_path) if current_path.is_file() else None
        history_dir = state_root / "lifecycle/receipts"
        if prior is not None:
            _validate_committed_receipt(prior, repository / "sage", history_dir)
            prior_roots = {row["root_id"]: Path(row["canonical_path"]) for row in prior["roots"]}
            if prior_roots != roots:
                raise ValueError("update destinations differ from the committed receipt; uninstall before relocating")
            _verify_roots(prior, roots)
            for entry in prior["entries"]:
                _verify_entry(entry, roots)
            for backup in prior["backups"]:
                _verify_backup(backup)

        manifest_sha256, _ = _source_manifest(repository)
        revision = _source_revision(repository, manifest_sha256)
        if prior is not None and prior["source"]["manifest_sha256"] == manifest_sha256:
            return {
                "operation": "noop",
                "installation_id": prior["installation_id"],
                "receipt": str(current_path),
                "manifest_sha256": manifest_sha256,
            }

        installation_id = prior["installation_id"] if prior else f"sage-{uuid.uuid4().hex}"
        operation_id = f"op-{uuid.uuid4().hex}"
        kind = "update" if prior else "install"
        root_setup = (
            (skills_root, "skills root"), (bin_root, "bin root"),
            (data_root.parent, "distribution root"), (state_root, "state root"),
            (backup_root, "backup root"),
        )
        recovery: dict[str, Any] = {
            "schema_version": "1.0",
            "kind": kind,
            "phase": "staging",
            "operation_id": operation_id,
            "installation_id": installation_id,
            "repository": str(repository),
            "state_root": str(state_root),
            "data_root": str(data_root),
            "roots": {key: str(value) for key, value in roots.items()},
            "prior_receipt_sha256": canonical_sha256(prior) if prior else None,
            "created_roots": [str(path) for path, _ in root_setup if not path.exists()],
            "root_state": [],
            "entries": _install_recovery_entries(
                skills_root, bin_root, data_root, state_root, installation_id, operation_id,
            ),
            "snapshots": [],
            "snapshot_container": None,
            "intended_receipt_sha256": None,
            "intended_receipt": None,
            "journal_plan": None,
            "durable_journal": [],
            "final_receipt": None,
            "commit_checkpoint_sha256": None,
        }
        _write_recovery(recovery_path, recovery)
        plans: list[EntryPlan] = []
        prior_entries = {row["entry_id"]: row for row in prior.get("entries", [])} if prior else {}
        inherited_backups = copy.deepcopy(prior.get("backups", [])) if prior else []
        new_backups: list[dict[str, Any]] = []
        changed: list[EntryPlan] = []
        now = utc_now()
        try:
            for path, label in root_setup:
                _ensure_root(path, label)
            recovery["root_state"] = [_root_record(root_id, path, now) for root_id, path in roots.items()]
            _write_recovery(recovery_path, recovery)
            _preflight_install_targets(recovery["entries"])
            plans = _make_plans(repository, skills_root, bin_root, data_root, state_root, installation_id, operation_id)
            plan_by_id = {plan.entry_id: plan for plan in plans}
            recovery_by_id = {row["entry_id"]: row for row in recovery["entries"]}
            for entry_id, plan in plan_by_id.items():
                row = recovery_by_id[entry_id]
                if (str(plan.target), str(plan.stage), plan.expected_type, plan.mutable, plan.marker) != (
                    row["target"], row["stage"], row["expected_type"], row["mutable"], row["marker"],
                ):
                    raise ValueError(f"staged plan diverged from recovery scope for {entry_id}")

            backup_suffix = 0
            for plan in plans:
                old = prior_entries.get(plan.entry_id)
                if old is not None and plan.mutable:
                    _remove_path(plan.stage)
                    continue
                row = recovery_by_id[plan.entry_id]
                row["replace"] = True
                row["installed"] = {
                    "type": plan.expected_type,
                    "mode": plan.stage.stat(follow_symlinks=False).st_mode & 0o7777,
                    "sha256": _content_sha256(plan.stage),
                    "identity": _project_fs_identity(plan.stage, plan.target, now),
                    "resource_identity": _project_resource_identity(plan.stage, plan.target),
                    "stage_identity": _fs_identity(plan.stage, now),
                    "stage_resource_identity": _resource_identity(plan.stage),
                }
                if plan.target.exists() or plan.target.is_symlink():
                    _assert_no_symlink_chain(plan.target, plan.entry_id, include_target=True)
                    observed_type = _observed_type(plan.target)
                    if observed_type == "symlink":
                        raise ValueError(f"refusing to replace a symlink: {plan.target}")
                    if observed_type == "file" and plan.target.stat(follow_symlinks=False).st_nlink != 1:
                        raise ValueError(f"refusing to replace a hard-linked file: {plan.target}")
                    row["original"] = _capture_original(plan.target)
                    backup_suffix += 1
                    row["backup_id"] = f"backup-{operation_id}-{backup_suffix}"
                    row["backup_path"] = str(backup_root / row["backup_id"] / "payload")
            # Persist the complete target/backup scope before creating backup containers.
            _write_recovery(recovery_path, recovery)

            projected_backups: list[dict[str, Any]] = []
            for plan in plans:
                row = recovery_by_id[plan.entry_id]
                original = row["original"]
                if original is None:
                    continue
                payload = Path(row["backup_path"])
                if payload.parent.exists():
                    raise ValueError(f"backup container already exists: {payload.parent}")
                payload.parent.mkdir(parents=True)
                old = prior_entries.get(plan.entry_id)
                projected_backups.append(_projected_backup_record(
                    row["backup_id"],
                    "operation_rollback" if old is not None else "displaced_user",
                    plan,
                    backup_root,
                    payload,
                    original,
                    copy.deepcopy(old["identity"]) if old is not None else copy.deepcopy(original["identity"]),
                    copy.deepcopy(old["resource_identity"]) if old is not None else copy.deepcopy(original["resource_identity"]),
                    now,
                ))

            checker = _load_phase0_checker(repository / "sage")
            projected_receipt = _projected_install_receipt(
                repository=repository,
                revision=revision,
                manifest_sha256=manifest_sha256,
                roots=roots,
                plans=plans,
                recovery_rows=recovery_by_id,
                prior=prior,
                inherited_backups=inherited_backups,
                projected_backups=projected_backups,
                installation_id=installation_id,
                operation_id=operation_id,
                kind=kind,
                now=now,
            )
            journal_plan = _install_journal(
                projected_receipt,
                prior,
                [plan.entry_id for plan in plans if recovery_by_id[plan.entry_id]["replace"]],
                [row["backup_id"] for row in projected_backups],
                now,
                checker,
            )
            checker.refresh_receipt_fixture_integrity(projected_receipt)
            intended_hash = projected_receipt["operation"]["intended_receipt_sha256"]
            projected_receipt["operation"]["journal"] = []
            checker.refresh_receipt_fixture_integrity(projected_receipt)
            recovery["intended_receipt"] = projected_receipt
            recovery["intended_receipt_sha256"] = intended_hash
            recovery["journal_plan"] = copy.deepcopy(journal_plan)
            recovery["durable_journal"] = []
            recovery["phase"] = "replacing"
            _write_recovery(recovery_path, recovery)

            _persist_install_through(recovery, recovery_path, "preflight_complete")
            intent_issues = validate_receipt(recovery["intended_receipt"], repository / "sage", prior)
            if intent_issues:
                raise ValueError("pre-mutation ownership receipt intent failed validation:\n" + "\n".join(intent_issues))

            # Make every required backup durable before applying any live replacement.
            for plan in plans:
                row = recovery_by_id[plan.entry_id]
                if not row["replace"]:
                    continue
                old = prior_entries.get(plan.entry_id)
                original = row["original"]
                if original is not None:
                    _verify_original(plan.target, original, f"pre-replacement target for {plan.entry_id}")
                    payload = Path(row["backup_path"])
                    _move_path(plan.target, payload)
                    purpose = "operation_rollback" if old is not None else "displaced_user"
                    backup = _backup_record(
                        row["backup_id"], purpose, plan, backup_root, payload,
                        copy.deepcopy(old["identity"]) if old is not None else copy.deepcopy(original["identity"]),
                        copy.deepcopy(old["resource_identity"]) if old is not None else copy.deepcopy(original["resource_identity"]),
                        original["type"], original["mode"], original["sha256"], now,
                    )
                    _verify_backup(backup)
                    new_backups.append(backup)
            if new_backups:
                if canonical_json_bytes(new_backups) != canonical_json_bytes(projected_backups):
                    raise ValueError("live backup state differs from the pre-mutation receipt intent")
                _persist_install_through(recovery, recovery_path, "backups_durable")
            _persist_install_through(recovery, recovery_path, "stage_verified")

            replacement_count = 0
            for plan in plans:
                row = recovery_by_id[plan.entry_id]
                if not row["replace"]:
                    continue
                if plan.target.exists() or plan.target.is_symlink():
                    raise ValueError(f"target reappeared during replacement: {plan.target}")
                _move_path(plan.stage, plan.target)
                if plan.expected_type == "file":
                    plan.target.chmod(0o755)
                changed.append(plan)
                replacement_count += 1
                _test_crash("SAGE_TEST_CRASH_AFTER_REPLACEMENTS", replacement_count)
            _persist_install_through(recovery, recovery_path, "replacement_applied")

            snapshot_container = backup_root / f".sage-recovery-{operation_id}"
            snapshots: list[dict[str, Any]] = []
            for entry_id in ("state.promoted-overlay", "state.promoted-index"):
                old = prior_entries.get(entry_id)
                if old is None:
                    continue
                target = _entry_path(old, roots)
                _verify_entry(old, roots)
                snapshot = snapshot_container / entry_id
                _copy_path(target, snapshot)
                _fsync_tree(snapshot)
                snapshots.append({
                    "entry_id": entry_id,
                    "target": str(target),
                    "snapshot_path": str(snapshot),
                    "sha256": tree_sha256(snapshot),
                    "mode": target.stat(follow_symlinks=False).st_mode & 0o7777,
                    "marker": old["ownership_marker"],
                    "identity": _fs_identity(snapshot),
                    "resource_identity": _resource_identity(snapshot),
                })
            recovery["snapshots"] = snapshots
            recovery["snapshot_container"] = (
                {
                    "path": str(snapshot_container),
                    "identity": _fs_identity(snapshot_container),
                    "resource_identity": _resource_identity(snapshot_container),
                }
                if snapshot_container.is_dir()
                else None
            )
            recovery["phase"] = "reconciling"
            _write_recovery(recovery_path, recovery)

            reconcile_installed(repository / "sage/knowledge", state_root)
            _health_check(data_root, bin_root, state_root)
            _persist_install_through(recovery, recovery_path, "health_verified")

            backups = inherited_backups + new_backups
            backup_ids_by_owner: dict[str, list[str]] = {}
            for backup in backups:
                backup_ids_by_owner.setdefault(backup["owner_entry_id"], []).append(backup["backup_id"])
            prior_classes = {row["entry_id"]: row["entry_class"] for row in prior.get("entries", [])} if prior else {}
            entries: list[dict[str, Any]] = []
            for plan in plans:
                if plan.entry_id in prior_classes:
                    plan.entry_class = prior_classes[plan.entry_id]
                elif any(row["owner_entry_id"] == plan.entry_id and row["purpose"] == "displaced_user" for row in new_backups):
                    plan.entry_class = "replaced"
                if prior is not None and plan.mutable and plan.entry_id in prior_entries:
                    preserved = copy.deepcopy(prior_entries[plan.entry_id])
                    preserved["backup_ids"] = backup_ids_by_owner.get(plan.entry_id, [])
                    entries.append(preserved)
                else:
                    entries.append(_entry_record(plan, roots, backup_ids_by_owner.get(plan.entry_id, []), now))

            receipt: dict[str, Any] = {
                "receipt_version": "1.0",
                "installation_id": installation_id,
                "mode": "light",
                "installer_version": INSTALLER_VERSION,
                "source": {
                    "repository": str(repository),
                    "revision": revision,
                    "manifest_sha256": manifest_sha256,
                },
                "protected_paths": [_protected_record(repository)],
                # These identities describe the committed state after recovery-only snapshots
                # are removed; they were calculated and bound before live replacement.
                "roots": copy.deepcopy(projected_receipt["roots"]),
                "entries": entries,
                "config_entries": [],
                "backups": backups,
                "retention_policies": _retention_policies(),
                "preservation": {
                    "preserve_on_update": PRESERVATION_CLASSES,
                    "keep_data": False,
                    "keep_data_entry_ids": [],
                    "retention_receipt_id": None,
                },
                "operation": {
                    "operation_id": operation_id,
                    "kind": kind,
                    "state": "committed",
                    "prior_receipt_sha256": canonical_sha256(prior) if prior else None,
                    "intended_receipt_sha256": "0" * 64,
                    "journal": [],
                },
            }
            receipt["operation"]["journal"] = copy.deepcopy(recovery["journal_plan"])
            checker.refresh_receipt_fixture_integrity(receipt)
            if receipt["operation"]["intended_receipt_sha256"] != intended_hash:
                expected_projection = checker.receipt_intent_projection(recovery["intended_receipt"])
                observed_projection = checker.receipt_intent_projection(receipt)
                changed_sections = [
                    key for key in expected_projection
                    if canonical_json_bytes(expected_projection[key]) != canonical_json_bytes(observed_projection[key])
                ]
                if "entries" in changed_sections:
                    expected_entries = {row["entry_id"]: row for row in expected_projection["entries"]}
                    observed_entries = {row["entry_id"]: row for row in observed_projection["entries"]}
                    entry_changes = [
                        entry_id for entry_id in expected_entries
                        if canonical_json_bytes(expected_entries[entry_id]) != canonical_json_bytes(observed_entries[entry_id])
                    ]
                    changed_sections.append("entry_ids=" + ",".join(entry_changes))
                raise ValueError(
                    "live installation differs from the durable pre-mutation receipt intent in: "
                    + ", ".join(changed_sections)
                )
            issues = validate_receipt(receipt, repository / "sage", prior)
            if issues:
                raise ValueError("generated ownership receipt failed validation:\n" + "\n".join(issues))
            recovery["journal_plan"] = copy.deepcopy(receipt["operation"]["journal"])
            recovery["final_receipt"] = copy.deepcopy(receipt)
            _write_recovery(recovery_path, recovery)
            _finish_install_commit(recovery, recovery_path, roots, data_root, repository)
            history_path = history_dir / f"{operation_id}.json"
            return {
                "operation": kind,
                "installation_id": installation_id,
                "receipt": str(current_path),
                "history_receipt": str(history_path),
                "manifest_sha256": manifest_sha256,
                "changed_entries": [plan.entry_id for plan in changed],
                "preserved_entries": [plan.entry_id for plan in plans if plan not in changed],
            }
        except BaseException:
            pending = _load_recovery(recovery_path, state_root)
            if pending is not None:
                _recover_install_operation(pending, recovery_path, roots, data_root, repository)
            raise


def _receipt_roots(receipt: dict[str, Any]) -> dict[str, Path]:
    return {row["root_id"]: Path(row["canonical_path"]) for row in receipt["roots"]}


def _verify_root_if_present(row: dict[str, Any]) -> None:
    path = Path(row["canonical_path"])
    if not path.exists():
        return
    _assert_no_symlink_chain(path, row["root_id"], include_target=True)
    if not path.is_dir():
        raise ValueError(f"lifecycle root changed type: {path}")
    observed = path.stat(follow_symlinks=False)
    identity = row["identity"]
    if (observed.st_dev, observed.st_ino) != (identity["device"], identity["inode"]):
        raise ValueError(f"lifecycle root identity changed: {path}")
    if _resource_identity(path) != row["resource_identity"]:
        raise ValueError(f"lifecycle root resource identity changed: {path}")


def _verify_restored_backup(target: Path, backup: dict[str, Any]) -> None:
    _assert_no_symlink_chain(target, backup["backup_id"], include_target=True)
    if not target.exists() or _observed_type(target) != backup["original_type"]:
        raise ValueError(f"restored user content is missing or changed type: {target}")
    observed = target.stat(follow_symlinks=False)
    identity = backup["original_identity"]
    if (observed.st_dev, observed.st_ino, observed.st_nlink) != (
        identity["device"], identity["inode"], identity["link_count"],
    ) or (observed.st_mode & 0o7777) != int(backup["mode"], 8):
        raise ValueError(f"restored user content identity or mode changed: {target}")
    if _resource_identity(target) != backup["original_resource_identity"]:
        raise ValueError(f"restored user content resource identity changed: {target}")
    if _content_sha256(target) != backup["sha256"]:
        raise ValueError(f"restored user content digest changed: {target}")


def _retained_marker(entry: dict[str, Any], retention_id: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "marker": f"sage-retained:{retention_id}:{entry['entry_id']}",
        "export_owner": "user",
    }


def _verify_retained_entry(entry: dict[str, Any], roots: dict[str, Path], retention_id: str) -> bool:
    target = _entry_path(entry, roots)
    if not target.is_dir() or target.is_symlink():
        return False
    try:
        marker = load_json(_marker_path(target))
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    if marker != _retained_marker(entry, retention_id):
        return False
    observed = target.stat(follow_symlinks=False)
    identity = entry["identity"]
    return (
        (observed.st_dev, observed.st_ino) == (identity["device"], identity["inode"])
        and _resource_identity(target) == entry["resource_identity"]
    )


def _validate_uninstall_recovery(
    record: dict[str, Any],
    repository: Path,
    state_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Path]]:
    if record.get("repository") != str(repository):
        raise ValueError("pending uninstall belongs to a different source checkout")
    prior = record.get("prior_receipt")
    intended = record.get("intended_receipt")
    predecessor = record.get("prior_predecessor")
    if not isinstance(prior, dict) or not isinstance(intended, dict):
        raise ValueError("pending uninstall does not contain its receipt evidence")
    if canonical_sha256(prior) != record.get("prior_receipt_sha256"):
        raise ValueError("pending uninstall prior receipt digest changed")
    prior_issues = validate_receipt(prior, repository / "sage", predecessor)
    if prior_issues:
        raise ValueError("pending uninstall prior receipt failed validation:\n" + "\n".join(prior_issues))
    intent_issues = validate_receipt(intended, repository / "sage", prior)
    if intent_issues:
        raise ValueError("pending uninstall intended receipt failed validation:\n" + "\n".join(intent_issues))
    if intended["operation"]["operation_id"] != record["operation_id"]:
        raise ValueError("pending uninstall operation ID differs from its receipt")
    if (
        record.get("intended_receipt_sha256") != intended["operation"]["intended_receipt_sha256"]
        or not isinstance(record.get("durable_journal"), list)
        or record["durable_journal"] != record["journal_plan"][:len(record["durable_journal"])]
        or intended["operation"]["journal"] != record["durable_journal"]
    ):
        raise ValueError("pending uninstall receipt intent or durable journal is inconsistent")
    receipt = copy.deepcopy(intended)
    receipt["operation"]["state"] = "committed"
    receipt["operation"]["journal"] = copy.deepcopy(record["journal_plan"])
    checker = _load_phase0_checker(repository / "sage")
    checker.refresh_receipt_fixture_integrity(receipt)
    receipt_issues = validate_receipt(receipt, repository / "sage", prior)
    if receipt_issues:
        raise ValueError("pending uninstall final receipt plan failed validation:\n" + "\n".join(receipt_issues))
    roots = _receipt_roots(prior)
    if roots.get("state") != state_root:
        raise ValueError("pending uninstall state root differs from its receipt")
    _check_root_separation(roots, repository)
    if record.get("retained") != receipt["preservation"]["keep_data_entry_ids"]:
        raise ValueError("pending uninstall retained entry set changed")
    output = record.get("receipt_output")
    if output is not None:
        output_path = Path(output)
        if not output_path.is_absolute() or any(_paths_overlap(output_path, root) for root in roots.values()):
            raise ValueError("pending uninstall receipt output escaped its approved scope")
    return prior, receipt, roots


def _persist_uninstall_through(record: dict[str, Any], recovery_path: Path, phase: str) -> None:
    plan = record["journal_plan"]
    target_index = _journal_phase_index(plan, phase)
    if target_index is None:
        return
    while len(record["durable_journal"]) <= target_index:
        index = len(record["durable_journal"])
        observed_at = utc_now()
        for row in record["journal_plan"][index:]:
            _stamp_journal_row(row, observed_at)
        _persist_recovery_journal(record, recovery_path, record["journal_plan"][:index + 1])
        _test_crash_at_phase(record["durable_journal"][index]["phase"])


def _resume_uninstall(
    record: dict[str, Any],
    recovery_path: Path,
    repository: Path,
    state_root: Path,
) -> dict[str, Any]:
    prior, receipt, roots = _validate_uninstall_recovery(record, repository, state_root)
    current_path = state_root / "lifecycle/current.json"
    if current_path.is_file() and canonical_sha256(load_json(current_path)) != record["prior_receipt_sha256"]:
        raise ValueError("current receipt changed while uninstall recovery was pending")
    entries = {entry["entry_id"]: entry for entry in prior["entries"]}
    retained = set(record["retained"])
    retention_id = record.get("retention_id")
    displaced = {
        row["owner_entry_id"]: row for row in prior["backups"] if row["purpose"] == "displaced_user"
    }
    mutation_count = 0

    def mutated() -> None:
        nonlocal mutation_count
        mutation_count += 1
        _test_crash("SAGE_TEST_CRASH_AFTER_UNINSTALL_MUTATIONS", mutation_count)

    for entry_id, backup in sorted(displaced.items()):
        target = _entry_path(entries[entry_id], roots)
        payload = Path(backup["backup_path"])
        if payload.exists():
            _verify_backup(backup)
            if target.exists() or target.is_symlink():
                _verify_entry(entries[entry_id], roots)
                _remove_path(target)
                mutated()
            _move_path(payload, target)
            mutated()
        _verify_restored_backup(target, backup)
    _persist_uninstall_through(record, recovery_path, "user_content_restored")

    for entry in sorted(prior["entries"], key=lambda row: row["cleanup_order"], reverse=True):
        if entry["entry_id"] in retained or entry["entry_id"] in displaced:
            continue
        target = _entry_path(entry, roots)
        if target.exists() or target.is_symlink():
            _verify_entry(entry, roots)
            _remove_path(target)
            mutated()
    _persist_uninstall_through(record, recovery_path, "owned_entry_removed")

    retention_path: Path | None = None
    if retained:
        if not isinstance(retention_id, str) or not retention_id.startswith("retained-"):
            raise ValueError("pending uninstall retention ID is invalid")
        for entry_id in sorted(retained):
            entry = entries[entry_id]
            target = _entry_path(entry, roots)
            if not _verify_retained_entry(entry, roots, retention_id):
                _verify_entry(entry, roots)
                atomic_write_json(_marker_path(target), _retained_marker(entry, retention_id), 0o600)
                mutated()
        retention_path = state_root / "retention-receipt.json"
        atomic_write_json(retention_path, {
            "schema_version": "1.0",
            "retention_receipt_id": retention_id,
            "installation_id": prior["installation_id"],
            "recorded_at": record["recorded_at"],
            "export_owner": "user",
            "retained": [str(_entry_path(entries[key], roots)) for key in sorted(retained)],
        }, 0o600)
        _persist_uninstall_through(record, recovery_path, "retention_receipt_committed")

    _persist_uninstall_through(record, recovery_path, "removal_verified")
    _persist_uninstall_through(record, recovery_path, "ownership_receipt_removed")

    for backup in prior["backups"]:
        payload = Path(backup["backup_path"])
        container = payload.parent
        if payload.exists():
            _verify_backup(backup)
            _remove_path(payload)
            mutated()
        if container.is_dir():
            if any(container.iterdir()):
                raise ValueError(f"refusing to remove nonempty backup container: {container}")
            container.rmdir()
            mutated()

    root_records = {row["root_id"]: row for row in prior["roots"]}
    for root_id in ("backups", "skills", "bin", "distribution", "state"):
        path = roots[root_id]
        if path.is_dir() and not any(path.iterdir()):
            _verify_root_if_present(root_records[root_id])
            path.rmdir()
            mutated()

    _persist_uninstall_through(record, recovery_path, "cleanup_complete")
    if record.get("receipt_output") is not None:
        atomic_write_json(Path(record["receipt_output"]), receipt, 0o600)
    recovery_path.unlink()
    return {
        "operation": "uninstall",
        "keep_data": bool(retained),
        "actions": record["actions"],
        "retention_receipt": str(retention_path) if retention_path else None,
        "receipt_output": record.get("receipt_output"),
        "recovered": mutation_count == 0,
    }


def uninstall(
    *,
    repository: Path,
    state_root: Path,
    yes: bool,
    dry_run: bool,
    keep_data: bool,
    receipt_output: Path | None = None,
) -> dict[str, Any]:
    repository = _canonical_path(repository)
    state_root = _canonical_path(state_root)
    current_path = state_root / "lifecycle/current.json"
    recovery_path = _recovery_path(state_root)
    with _operation_lock(state_root, current_path.is_file()):
        pending = _load_recovery(recovery_path, state_root)
        if pending is not None:
            if pending["kind"] != "uninstall":
                raise ValueError("an interrupted install or update must be recovered by rerunning install")
            return _resume_uninstall(pending, recovery_path, repository, state_root)
        if not current_path.is_file():
            return {"operation": "noop", "message": "Sage Light is already uninstalled", "state_root": str(state_root)}
        if not yes:
            if not sys.stdin.isatty():
                raise ValueError("complete removal requires --yes when stdin is not interactive")
            answer = input("Remove the complete Sage Light installation and runtime data? [y/N] ").strip().lower()
            if answer not in {"y", "yes"}:
                return {"operation": "cancelled"}
        prior = load_json(current_path)
        history_dir = state_root / "lifecycle/receipts"
        _validate_committed_receipt(prior, repository / "sage", history_dir)
        roots = _receipt_roots(prior)
        _verify_roots(prior, roots)
        resolved_receipt_output = _canonical_path(receipt_output) if receipt_output is not None else None
        if resolved_receipt_output is not None and any(
            _paths_overlap(resolved_receipt_output, root) for root in roots.values()
        ):
            raise ValueError("--receipt-output must be outside every removed or retained root")
        for entry in prior["entries"]:
            _verify_entry(entry, roots)
        for backup in prior["backups"]:
            _verify_backup(backup)
        eligible = {
            entry["entry_id"] for entry in prior["entries"]
            if entry["retention_class"] in {"run_history", "promoted_overlay", "secret_free_state"}
        }
        retained = eligible if keep_data else set()
        retention_id = f"retained-{uuid.uuid4().hex}" if keep_data else None
        receipt = copy.deepcopy(prior)
        operation_id = f"op-{uuid.uuid4().hex}"
        receipt["installer_version"] = INSTALLER_VERSION
        receipt["preservation"] = {
            "preserve_on_update": PRESERVATION_CLASSES,
            "keep_data": keep_data,
            "keep_data_entry_ids": sorted(retained),
            "retention_receipt_id": retention_id,
        }
        for backup in receipt["backups"]:
            if backup["purpose"] in {"displaced_user", "config_prior"}:
                backup["restored"] = True
        receipt["operation"] = {
            "operation_id": operation_id,
            "kind": "uninstall",
            "state": "committed",
            "prior_receipt_sha256": canonical_sha256(prior),
            "intended_receipt_sha256": "0" * 64,
            "journal": [],
        }
        checker = _load_phase0_checker(repository / "sage")
        now = utc_now()
        receipt["operation"]["journal"] = _uninstall_journal(receipt, prior, now, checker)
        checker.refresh_receipt_fixture_integrity(receipt)
        issues = validate_receipt(receipt, repository / "sage", prior)
        if issues:
            raise ValueError("generated uninstall receipt failed validation:\n" + "\n".join(issues))

        entries = {entry["entry_id"]: entry for entry in prior["entries"]}
        displaced = {
            row["owner_entry_id"]: row for row in prior["backups"] if row["purpose"] == "displaced_user"
        }
        actions: list[dict[str, str]] = []
        for entry_id, backup in sorted(displaced.items()):
            actions.append({"action": "restore", "entry_id": entry_id, "path": str(_entry_path(entries[entry_id], roots))})
        for entry in sorted(prior["entries"], key=lambda row: row["cleanup_order"], reverse=True):
            if entry["entry_id"] not in retained and entry["entry_id"] not in displaced:
                actions.append({"action": "remove", "entry_id": entry["entry_id"], "path": str(_entry_path(entry, roots))})
        for entry_id in sorted(retained):
            actions.append({"action": "retain", "entry_id": entry_id, "path": str(_entry_path(entries[entry_id], roots))})
        if dry_run:
            return {"operation": "uninstall-dry-run", "keep_data": keep_data, "actions": actions, "receipt_valid": True}
        predecessor = _receipt_predecessor(prior, history_dir)
        journal_plan = copy.deepcopy(receipt["operation"]["journal"])
        intended_receipt = copy.deepcopy(receipt)
        intended_receipt["operation"]["state"] = "pending"
        intended_receipt["operation"]["journal"] = []
        checker.refresh_receipt_fixture_integrity(intended_receipt)
        recovery = {
            "schema_version": "1.0",
            "kind": "uninstall",
            "phase": "removing",
            "operation_id": operation_id,
            "repository": str(repository),
            "state_root": str(state_root),
            "prior_receipt_sha256": canonical_sha256(prior),
            "prior_receipt": prior,
            "prior_predecessor": predecessor,
            "intended_receipt": intended_receipt,
            "intended_receipt_sha256": intended_receipt["operation"]["intended_receipt_sha256"],
            "journal_plan": journal_plan,
            "durable_journal": [],
            "retained": sorted(retained),
            "retention_id": retention_id,
            "recorded_at": now,
            "receipt_output": str(resolved_receipt_output) if resolved_receipt_output else None,
            "actions": actions,
        }
        _write_recovery(recovery_path, recovery)
        _persist_uninstall_through(recovery, recovery_path, "processes_stopped")
        return _resume_uninstall(recovery, recovery_path, repository, state_root)
