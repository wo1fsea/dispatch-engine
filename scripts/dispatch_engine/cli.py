"""Command-line interface for the bundled Dispatch Engine runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .plan_schema import PlanValidationError, import_dispatch_plan
from .state import run_status, tail_events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="de",
        description="Dispatch Engine: repo-native agent dispatch, with adult supervision.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("version", help="Print the bundled runtime version.")

    init_parser = subparsers.add_parser("init", help="Import an explicit dispatch plan.")
    init_parser.add_argument("target", help="Repository path to initialize.")
    init_parser.add_argument("--plan", required=True, help="Explicit dispatch plan JSON path.")
    _add_json_flag(init_parser)

    status_parser = subparsers.add_parser("status", help="Show latest Dispatch Engine run state.")
    status_parser.add_argument("target", nargs="?", default=".", help="Repository path containing .dispatch state.")
    status_parser.add_argument("--run-id", help="Read a specific run id instead of the latest run.")
    _add_json_flag(status_parser)

    tail_parser = subparsers.add_parser("tail", help="Print Dispatch Engine run events.")
    tail_parser.add_argument("target", nargs="?", default=".", help="Repository path containing .dispatch state.")
    tail_parser.add_argument("--run-id", help="Read a specific run id instead of the latest run.")
    _add_json_flag(tail_parser)

    return parser


def _add_json_flag(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Emit machine-readable JSON.",
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "version":
        return _print({"version": __version__}, args.json)

    if args.command == "init":
        try:
            result = import_dispatch_plan(Path(args.target), Path(args.plan))
        except PlanValidationError as exc:
            return _print({"kind": "error", "status": "invalid_plan", "summary": str(exc)}, args.json)
        return _print(result, args.json)

    if args.command == "status":
        result = run_status(Path(args.target), run_id=args.run_id)
        return _print(result, args.json)

    if args.command == "tail":
        result = tail_events(Path(args.target), run_id=args.run_id)
        return _print(result, args.json)

    parser.error(f"unknown command: {args.command}")
    return 2


def _print(payload: dict, as_json: bool) -> int:
    if payload.get("kind") == "error":
        if as_json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(payload["summary"])
        return 1

    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    kind = payload.get("kind")
    if kind == "plan_import":
        print(f"Imported plan: {payload['plan_id']}")
        print(f"Run: {payload['run_id']}")
        print(f"State: {payload['state_dir']}")
        print(f"Workstreams: {payload['workstream_count']}")
        return 0

    if kind == "status":
        print(payload["summary"])
        if payload.get("status") == "ok":
            print(f"State: {payload['state_dir']}")
            print("Workstreams:")
            for status, count in sorted(payload["workstream_counts"].items()):
                print(f"- {status}: {count}")
        return 0

    if kind == "tail":
        if payload.get("status") != "ok":
            print(payload["summary"])
            return 0
        for event in payload["events"]:
            workstream = f" [{event['workstream']}]" if "workstream" in event else ""
            print(f"{event['ts']} {event['type']}{workstream}")
        return 0

    if "version" in payload:
        print(payload["version"])
        return 0

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
