#!/usr/bin/env python3
"""Generate and check the policy copies packaged with the standalone Sage skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SAGE_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = SAGE_ROOT.parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from sage.lib.common import atomic_write_bytes, atomic_write_json  # noqa: E402


SOURCES = {
    "policy/contracts.md": SAGE_ROOT / "policy/contracts.md",
    "policy/delegation.md": SAGE_ROOT / "policy/delegation.md",
    "policy/implementation.md": SAGE_ROOT / "policy/implementation.md",
    "policy/memory.md": SAGE_ROOT / "policy/memory.md",
    "policy/recovery.md": SAGE_ROOT / "policy/recovery.md",
    "policy/review.md": SAGE_ROOT / "policy/review.md",
    "policy/software-review.md": SAGE_ROOT / "policy/software-review.md",
    "policy/topologies.md": SAGE_ROOT / "policy/topologies.md",
    "docs/phase0/promotion-contract.md": SAGE_ROOT / "docs/phase0/promotion-contract.md",
}

PROMOTE_SOURCES = {
    "promotion-contract.md": SAGE_ROOT / "docs/phase0/promotion-contract.md",
}


def generated_bytes(source: Path) -> tuple[bytes, str]:
    content = source.read_bytes()
    source_sha256 = hashlib.sha256(content).hexdigest()
    header = f"<!-- generated from {source.relative_to(REPOSITORY_ROOT).as_posix()} sha256:{source_sha256}; do not edit -->\n\n".encode()
    return header + content, source_sha256


def expected_bundle() -> tuple[dict[Path, bytes], dict[str, object]]:
    reference_root = SAGE_ROOT / "skills/sage/references"
    outputs: dict[Path, bytes] = {}
    rows: list[dict[str, str]] = []
    for relative, source in sorted(SOURCES.items()):
        content, source_sha256 = generated_bytes(source)
        destination = reference_root / relative
        outputs[destination] = content
        rows.append(
            {
                "source": source.relative_to(REPOSITORY_ROOT).as_posix(),
                "source_sha256": source_sha256,
                "generated": destination.relative_to(SAGE_ROOT / "skills/sage").as_posix(),
                "generated_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    manifest = {"schema_version": "1.0", "generator": "generate-skill-bundle.py", "files": rows}
    return outputs, manifest


def expected_promote_bundle() -> tuple[dict[Path, bytes], dict[str, object]]:
    skill_root = SAGE_ROOT / "skills/sage-promote"
    reference_root = skill_root / "references"
    outputs: dict[Path, bytes] = {}
    rows: list[dict[str, str]] = []
    for relative, source in sorted(PROMOTE_SOURCES.items()):
        content, source_sha256 = generated_bytes(source)
        destination = reference_root / relative
        outputs[destination] = content
        rows.append(
            {
                "source": source.relative_to(REPOSITORY_ROOT).as_posix(),
                "source_sha256": source_sha256,
                "generated": destination.relative_to(skill_root).as_posix(),
                "generated_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    manifest = {"schema_version": "1.0", "generator": "generate-skill-bundle.py", "files": rows}
    return outputs, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs, manifest = expected_bundle()
    promote_outputs, promote_manifest = expected_promote_bundle()
    bundles = (
        (outputs, manifest, SAGE_ROOT / "skills/sage/references/source-manifest.json"),
        (promote_outputs, promote_manifest, SAGE_ROOT / "skills/sage-promote/references/source-manifest.json"),
    )
    if args.check:
        stale: list[str] = []
        for bundle_outputs, bundle_manifest, manifest_path in bundles:
            stale.extend(
                str(path)
                for path, content in bundle_outputs.items()
                if not path.is_file() or path.read_bytes() != content
            )
            expected_manifest = json.dumps(bundle_manifest, ensure_ascii=False, indent=2).encode() + b"\n"
            if not manifest_path.is_file() or manifest_path.read_bytes() != expected_manifest:
                stale.append(str(manifest_path))
        if stale:
            print("generated skill bundle is stale:", file=sys.stderr)
            for path in stale:
                print(f"  {path}", file=sys.stderr)
            return 1
        print("skill-bundle: ok")
        return 0
    total = 0
    for bundle_outputs, bundle_manifest, manifest_path in bundles:
        for path, content in bundle_outputs.items():
            atomic_write_bytes(path, content)
        atomic_write_json(manifest_path, bundle_manifest)
        total += len(bundle_outputs)
    print(f"generated {total} canonical references across {len(bundles)} skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
