"""Canonical JSON, hashing, and atomic-file helpers shared by Sage tools."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import tempfile
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover - Sage Light lifecycle is POSIX-only.
    fcntl = None  # type: ignore[assignment]


class DuplicateKeyError(ValueError):
    """Raised when JSON contains two members with the same name."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"non-JSON numeric constant {value!r}")


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(
            handle,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite,
        )


def canonical_normalize(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    if isinstance(value, list):
        return [canonical_normalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for raw_key, child in value.items():
            key = unicodedata.normalize("NFC", raw_key.replace("\r\n", "\n").replace("\r", "\n"))
            if key in normalized:
                raise ValueError(f"canonical JSON keys collide after normalization: {key!r}")
            normalized[key] = canonical_normalize(child)
        return normalized
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("canonical JSON forbids non-finite numbers")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        canonical_normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(path: Path) -> str:
    """Hash a no-follow tree projection including path, type, mode, and content."""
    rows: list[dict[str, Any]] = []
    if path.is_symlink():
        rows.append({"path": ".", "type": "symlink", "target": os.readlink(path)})
    elif path.is_file():
        stat = path.lstat()
        rows.append({"path": ".", "type": "file", "mode": stat.st_mode & 0o7777, "sha256": sha256_file(path)})
    elif path.is_dir():
        for child in sorted(path.rglob("*"), key=lambda item: item.relative_to(path).as_posix()):
            relative = child.relative_to(path).as_posix()
            stat = child.lstat()
            if child.is_symlink():
                rows.append({"path": relative, "type": "symlink", "mode": stat.st_mode & 0o7777, "target": os.readlink(child)})
            elif child.is_file():
                rows.append({"path": relative, "type": "file", "mode": stat.st_mode & 0o7777, "sha256": sha256_file(child)})
            elif child.is_dir():
                rows.append({"path": relative, "type": "directory", "mode": stat.st_mode & 0o7777})
            else:
                rows.append({"path": relative, "type": "other", "mode": stat.st_mode & 0o7777})
    else:
        raise FileNotFoundError(path)
    return canonical_sha256(rows)


def atomic_write_bytes(path: Path, content: bytes, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        if temporary.exists() or temporary.is_symlink():
            temporary.unlink()


def atomic_write_json(path: Path, value: Any, mode: int | None = None) -> None:
    content = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False, allow_nan=False).encode("utf-8") + b"\n"
    atomic_write_bytes(path, content, mode)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def state_root() -> Path:
    configured = os.environ.get("SAGE_STATE_ROOT")
    return Path(configured).expanduser().resolve() if configured else (Path.home() / ".local/state/sage").resolve()


def source_root() -> Path:
    configured = os.environ.get("SAGE_SOURCE_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


@contextmanager
def sage_operation_lock() -> Iterator[None]:
    """Serialize lifecycle, run-open/close, and promotion boundary changes."""
    if fcntl is None:
        raise RuntimeError("Sage operation locking requires POSIX fcntl")
    lock_path = Path(tempfile.gettempdir()).resolve() / f"sage-lifecycle-{os.geteuid()}.lock"
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(lock_path, flags, 0o600)
    with os.fdopen(descriptor, "a+") as handle:
        observed = os.fstat(handle.fileno())
        if observed.st_uid != os.geteuid() or observed.st_nlink != 1 or not stat.S_ISREG(observed.st_mode):
            raise ValueError(f"Sage operation lock ownership or link state is unsafe: {lock_path}")
        os.fchmod(handle.fileno(), 0o600)
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def require_plain_directory(path: Path, label: str) -> None:
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink: {path}")
    if path.exists() and not path.is_dir():
        raise ValueError(f"{label} must be a directory: {path}")
