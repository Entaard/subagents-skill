#!/usr/bin/env python3
"""Validate and land an explicitly reviewed Sage promoted-knowledge candidate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SAGE_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_ROOT = SAGE_ROOT.parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from sage.lib.common import atomic_write_json, load_json  # noqa: E402
from sage.lib.knowledge import inspect_closed_runs, prepare_candidate, promote_batch, validate_record  # noqa: E402


def command_prepare(args: argparse.Namespace) -> int:
    source = Path(args.candidate).resolve()
    record = load_json(source)
    prepared = prepare_candidate(record)
    issues = validate_record(prepared, require_review=True)
    if issues:
        raise ValueError("candidate is incomplete:\n" + "\n".join(issues))
    output = Path(args.output).resolve() if args.output else source
    atomic_write_json(output, prepared)
    print(json.dumps({"candidate": str(output), "stored_integrity_sha256": prepared["stored_integrity_sha256"]}, indent=2))
    return 0


def command_promote(args: argparse.Namespace) -> int:
    source_root = Path(args.source_root).resolve() if args.global_promotion else None
    state = Path(args.state_root).resolve() if args.state_root else None
    result = promote_batch(
        [Path(value).resolve() for value in args.candidate],
        args.run_id,
        global_source_root=source_root,
        expected_source_revision=args.expected_source_revision,
        installed_state_root=state,
    )
    results = result["results"]
    if len(results) == 1:
        result = results[0]
    print(json.dumps(result, indent=2, ensure_ascii=False))
    follow_ups = sorted({row["follow_up_install"] for row in results if row.get("follow_up_install")})
    for follow_up in follow_ups:
        print(f"Install when ready: {follow_up}")
    return 0


def command_inspect(args: argparse.Namespace) -> int:
    state = Path(args.state_root).resolve() if args.state_root else None
    result = inspect_closed_runs(args.run_id, installed_state_root=state)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    prepare = subparsers.add_parser("prepare", help="recompute a candidate's canonical integrity hash")
    prepare.add_argument("--candidate", required=True)
    prepare.add_argument("--output")
    prepare.set_defaults(func=command_prepare)

    inspect = subparsers.add_parser(
        "inspect",
        help="validate closed runs and print their promotion-eligible facts and evidence",
    )
    inspect.add_argument("--run-id", action="append", required=True)
    inspect.add_argument("--state-root")
    inspect.set_defaults(func=command_inspect)

    parser.add_argument("--candidate", action="append")
    parser.add_argument("--run-id", action="append")
    parser.add_argument("--state-root")
    parser.add_argument("--global", dest="global_promotion", action="store_true", help="write only to the source repository")
    parser.add_argument("--source-root")
    parser.add_argument("--expected-source-revision")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if hasattr(args, "func"):
            return int(args.func(args))
        if not args.candidate or not args.run_id:
            parser.error("--candidate and --run-id are required")
        if args.global_promotion and not args.source_root:
            parser.error("--global requires --source-root")
        if not args.global_promotion and (args.source_root or args.expected_source_revision):
            parser.error("source options require --global")
        return command_promote(args)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"sage-promote: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
