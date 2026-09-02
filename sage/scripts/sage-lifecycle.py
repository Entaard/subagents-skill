#!/usr/bin/env python3
"""Install, update, dry-run, or completely remove Sage Light mode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAGE_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = SAGE_ROOT.parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from sage.lib.lifecycle import install, uninstall  # noqa: E402


def _defaults() -> dict[str, str]:
    home = Path.home()
    return {
        "skills_root": str(home / ".agents/skills"),
        "bin_root": str(home / ".local/bin"),
        "data_root": str(home / ".local/share/sage"),
        "state_root": str(home / ".local/state/sage"),
    }


def _add_destinations(parser: argparse.ArgumentParser) -> None:
    defaults = _defaults()
    parser.add_argument("--skills-root", default=defaults["skills_root"])
    parser.add_argument("--bin-root", default=defaults["bin_root"])
    parser.add_argument("--data-root", default=defaults["data_root"])
    parser.add_argument("--state-root", default=defaults["state_root"])
    parser.add_argument("--backup-root")


def command_install(args: argparse.Namespace) -> int:
    state = Path(args.state_root)
    backup = Path(args.backup_root) if args.backup_root else state.parent / f"{state.name}-backups"
    result = install(
        repository=Path(args.source_root),
        skills_root=Path(args.skills_root),
        bin_root=Path(args.bin_root),
        data_root=Path(args.data_root),
        state_root=state,
        backup_root=backup,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def command_uninstall(args: argparse.Namespace) -> int:
    result = uninstall(
        repository=Path(args.source_root),
        state_root=Path(args.state_root),
        yes=args.yes,
        dry_run=args.dry_run,
        keep_data=args.keep_data,
        receipt_output=Path(args.receipt_output) if args.receipt_output else None,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    install_parser = subparsers.add_parser("install", help="install or receipt-bound update Sage Light")
    _add_destinations(install_parser)
    install_parser.add_argument("--source-root", default=str(REPOSITORY_ROOT))
    install_parser.set_defaults(func=command_install)

    uninstall_parser = subparsers.add_parser("uninstall", help="completely remove a receipt-bound Sage Light install")
    _add_destinations(uninstall_parser)
    uninstall_parser.add_argument("--source-root", default=str(REPOSITORY_ROOT))
    uninstall_parser.add_argument("--yes", "-y", action="store_true")
    uninstall_parser.add_argument("--dry-run", action="store_true")
    uninstall_parser.add_argument("--keep-data", action="store_true")
    uninstall_parser.add_argument("--receipt-output")
    uninstall_parser.set_defaults(func=command_uninstall)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"sage-lifecycle: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
