#!/usr/bin/env python3
"""Install, update, or uninstall the allowlisted Codex Sage package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

SAGE_ROOT = Path(__file__).resolve().parent.parent
RECEIPT = "sage/receipt.json"
HELPERS = {
    "sage/bin/sage_state.py": "scripts/sage_state.py",
    "sage/bin/sage_knowledge.py": "scripts/sage_knowledge.py",
}
REQUIRED = (
    "skills/sage/SKILL.md",
    "skills/sage/agents/openai.yaml",
    "skills/sage/references/run.md",
    "skills/sage/references/runtime.md",
    "skills/sage/references/delegation.md",
    "skills/sage/references/verification.md",
    "skills/sage/references/recovery.md",
    "skills/sage/references/state.md",
    "skills/sage/references/knowledge.md",
    "skills/sage-promote/SKILL.md",
    "skills/sage-promote/agents/openai.yaml",
    "skills/sage-promote/references/promotion.md",
    "skills/sage-promote/references/knowledge.md",
    *HELPERS.values(),
)


class LifecycleError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    return digest(path.read_bytes())


def strict_json(path: Path) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise LifecycleError(f"duplicate receipt key: {key}")
            result[key] = value
        return result

    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=unique,
        parse_constant=lambda value: (_ for _ in ()).throw(LifecycleError(f"non-finite receipt value: {value}")),
    )


def safe_relative(raw: str) -> str:
    if not isinstance(raw, str) or not raw or "\\" in raw or "\x00" in raw:
        raise LifecycleError("receipt contains an invalid path")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts) or path.as_posix() != raw:
        raise LifecycleError(f"receipt path escapes or is not canonical: {raw!r}")
    if raw == RECEIPT or not (raw.startswith("skills/sage/") or raw.startswith("skills/sage-promote/") or raw in HELPERS):
        raise LifecycleError(f"receipt path is outside the Sage allowlist: {raw!r}")
    return raw


def validate_root(path: Path, label: str, *, may_not_exist: bool) -> Path:
    absolute = path.absolute()
    if absolute.is_symlink():
        raise LifecycleError(f"{label} must not be a symlink: {absolute}")
    if absolute.exists() and not absolute.is_dir():
        raise LifecycleError(f"{label} must be a directory: {absolute}")
    if not absolute.exists() and not may_not_exist:
        raise LifecycleError(f"{label} does not exist: {absolute}")
    return absolute


def ensure_no_symlink_components(root: Path, relative: str, *, include_leaf: bool = True) -> None:
    current = root
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        if not include_leaf and index == len(parts) - 1:
            break
        if current.is_symlink():
            raise LifecycleError(f"symlink is not allowed at {current}")
        if index < len(parts) - 1 and current.exists() and not current.is_dir():
            raise LifecycleError(f"path parent must be a directory: {current}")


def source_files(source_root: Path) -> dict[str, tuple[Path, bytes]]:
    for relative in REQUIRED:
        path = source_root / relative
        ensure_no_symlink_components(source_root, relative)
        if not path.is_file():
            raise LifecycleError(f"required source file is missing: {relative}")

    result: dict[str, tuple[Path, bytes]] = {}
    for skill in ("sage", "sage-promote"):
        base = source_root / "skills" / skill
        for directory, directories, files in os.walk(base, followlinks=False):
            directory_path = Path(directory)
            for name in list(directories):
                candidate = directory_path / name
                if candidate.is_symlink():
                    raise LifecycleError(f"source symlink is not allowed: {candidate}")
                if name == "__pycache__":
                    directories.remove(name)
            for name in files:
                candidate = directory_path / name
                if candidate.is_symlink() or not candidate.is_file():
                    raise LifecycleError(f"source must contain regular files only: {candidate}")
                if name == "source-manifest.json" or name.endswith(".pyc"):
                    raise LifecycleError(f"legacy/generated source is not allowed in the active skill: {candidate}")
                relative = candidate.relative_to(source_root).as_posix()
                result[relative] = (candidate, candidate.read_bytes())
    for installed, source in HELPERS.items():
        candidate = source_root / source
        result[installed] = (candidate, candidate.read_bytes())
    return dict(sorted(result.items()))


def valid_sha(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def load_receipt(target_root: Path) -> dict[str, Any] | None:
    ensure_no_symlink_components(target_root, RECEIPT, include_leaf=False)
    path = target_root / RECEIPT
    if path.is_symlink():
        raise LifecycleError("receipt must be a regular file, not a symlink")
    if not path.exists():
        return None
    if not path.is_file():
        raise LifecycleError("receipt must be a regular file")
    receipt = strict_json(path)
    if not isinstance(receipt, dict) or receipt.get("schema_version") != "sage-install-receipt-v1":
        raise LifecycleError("receipt schema is missing or unsupported")
    if receipt.get("target_root") != str(target_root):
        raise LifecycleError("receipt target_root does not match the requested target")
    installed = receipt.get("installed_files"); files = receipt.get("files")
    if not isinstance(installed, list) or not all(isinstance(item, str) for item in installed) or not isinstance(files, dict):
        raise LifecycleError("receipt ownership index is malformed")
    if len(installed) != len(set(installed)):
        raise LifecycleError("receipt ownership index contains duplicates")
    normalized = [safe_relative(item) for item in installed]
    if normalized != sorted(normalized) or set(files) != set(normalized):
        raise LifecycleError("receipt ownership list and hash records disagree")
    for relative, row in files.items():
        if not isinstance(row, dict) or not valid_sha(row.get("source_sha256")) or not valid_sha(row.get("installed_sha256")):
            raise LifecycleError(f"receipt hash record is malformed: {relative}")
        if row["source_sha256"] != row["installed_sha256"]:
            raise LifecycleError(f"receipt source and installed hashes disagree: {relative}")
        inherited = row.get("inherited_installed_sha256")
        if inherited is not None and not valid_sha(inherited):
            raise LifecycleError(f"receipt inherited hash is malformed: {relative}")
        ensure_no_symlink_components(target_root, relative, include_leaf=False)
    return receipt


def classify_path(path: Path) -> tuple[str, str | None]:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return "absent", None
    if stat.S_ISREG(mode):
        return "file", file_digest(path)
    if stat.S_ISLNK(mode):
        return "symlink", None
    return "other", None


def atomic_write(path: Path, data: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.chmod(temporary, mode); os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def find_unowned_package_paths(target_root: Path, owned: set[str]) -> list[dict[str, str]]:
    retained: list[dict[str, str]] = []
    for relative_root in ("skills/sage", "skills/sage-promote", "sage/bin"):
        root = target_root / relative_root
        if root.is_symlink():
            retained.append({"path": relative_root, "reason": "unowned_replacement"})
            continue
        if not root.is_dir():
            continue
        for directory, directories, files in os.walk(root, followlinks=False):
            directory_path = Path(directory)
            for name in list(directories):
                candidate = directory_path / name
                if candidate.is_symlink():
                    relative = candidate.relative_to(target_root).as_posix()
                    if relative not in owned:
                        retained.append({"path": relative, "reason": "unowned"})
                    directories.remove(name)
            for name in files:
                relative = (directory_path / name).relative_to(target_root).as_posix()
                if relative not in owned:
                    retained.append({"path": relative, "reason": "unowned"})
    return retained


def install(source_root: Path, target_root: Path) -> dict[str, Any]:
    source_root = validate_root(source_root, "source root", may_not_exist=False)
    desired = source_files(source_root)
    target_existed = target_root.absolute().exists()
    target_root = validate_root(target_root, "target root", may_not_exist=True)
    source_physical = source_root.resolve(); target_physical = target_root.resolve()
    if source_physical == target_physical:
        raise LifecycleError("source root and target root must be different")
    try:
        source_physical.relative_to(target_physical)
    except ValueError:
        pass
    else:
        raise LifecycleError("source root must not be inside the target root")
    try:
        target_within_source = target_physical.relative_to(source_physical)
    except ValueError:
        target_within_source = None
    if target_within_source is not None and target_within_source.parts and target_within_source.parts[0] in {"skills", "scripts"}:
        raise LifecycleError("target root overlaps shipped source paths")
    receipt = load_receipt(target_root) if target_existed else None
    prior_files = receipt["files"] if receipt else {}
    conflicts: list[dict[str, str]] = []
    for relative in sorted(set(desired) | set(prior_files)):
        ensure_no_symlink_components(target_root, relative, include_leaf=False)
        kind, current_hash = classify_path(target_root / relative); prior = prior_files.get(relative)
        if relative in desired:
            if prior is None and kind != "absent":
                conflicts.append({"path": relative, "reason": f"unowned_{kind}"})
            elif prior is not None and (kind != "file" or current_hash != prior["installed_sha256"]):
                conflicts.append({"path": relative, "reason": "owned_path_modified_or_replaced"})
        elif prior is not None and kind != "absent" and (kind != "file" or current_hash != prior["installed_sha256"]):
            conflicts.append({"path": relative, "reason": "retired_owned_path_modified_or_replaced"})
    if conflicts:
        raise LifecycleError("install conflicts: " + json.dumps(conflicts, sort_keys=True))

    target_root.mkdir(parents=True, exist_ok=True)
    records: dict[str, dict[str, str | None]] = {}
    for relative, (source, data) in desired.items():
        installed_hash = digest(data); inherited = prior_files.get(relative, {}).get("installed_sha256")
        records[relative] = {"source_sha256": file_digest(source), "installed_sha256": installed_hash, "inherited_installed_sha256": inherited}
        atomic_write(target_root / relative, data, 0o755 if relative in HELPERS else 0o644)
    removed: list[str] = []
    for relative in sorted(set(prior_files) - set(desired), reverse=True):
        path = target_root / relative
        if path.exists():
            path.unlink(); removed.append(relative)
    operation = "update" if receipt else "install"
    receipt_data = {
        "schema_version": "sage-install-receipt-v1", "operation": operation,
        "source_root": str(source_root), "target_root": str(target_root),
        "installed_files": sorted(records), "files": records,
    }
    atomic_write(target_root / RECEIPT, (json.dumps(receipt_data, indent=2, sort_keys=True) + "\n").encode())
    return {"ok": True, "operation": operation, "installed": sorted(records), "removed_retired": removed, "receipt": RECEIPT}


def uninstall(target_root: Path) -> dict[str, Any]:
    target_root = validate_root(target_root, "target root", may_not_exist=False)
    receipt = load_receipt(target_root)
    if receipt is None:
        raise LifecycleError("no Sage receipt exists at the requested target")
    removed: list[str] = []; retained = find_unowned_package_paths(target_root, set(receipt["installed_files"]))
    for relative in reversed(receipt["installed_files"]):
        path = target_root / relative; ensure_no_symlink_components(target_root, relative, include_leaf=False)
        kind, current_hash = classify_path(path)
        if kind == "absent":
            continue
        if kind == "file" and current_hash == receipt["files"][relative]["installed_sha256"]:
            path.unlink(); removed.append(relative)
        else:
            retained.append({"path": relative, "reason": "modified_or_replaced"})
    (target_root / RECEIPT).unlink()
    return {"ok": True, "operation": "uninstall", "removed": sorted(removed), "retained": sorted(retained, key=lambda row: row["path"]), "runtime_state_removed": False}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest="command", required=True)
    install_parser = commands.add_parser("install"); install_parser.add_argument("--target-root", type=Path, required=True); install_parser.add_argument("--source-root", type=Path, default=SAGE_ROOT)
    uninstall_parser = commands.add_parser("uninstall"); uninstall_parser.add_argument("--target-root", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = install(args.source_root, args.target_root) if args.command == "install" else uninstall(args.target_root)
        print(json.dumps(result, indent=2, sort_keys=True)); return 0
    except (LifecycleError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "code": "lifecycle_rejected", "message": str(error)}, sort_keys=True), file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
