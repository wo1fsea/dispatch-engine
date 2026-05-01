"""Command-line interface for the bundled Dispatch Engine runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .inspect import inspect_repo
from .planner import plan_objective
from .state import latest_run_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="de",
        description="Dispatch Engine: repo-native agent dispatch, with adult supervision.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("version", help="Print the bundled runtime version.")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect a target repository.")
    inspect_parser.add_argument("target", nargs="?", default=".", help="Repository path to inspect.")

    plan_parser = subparsers.add_parser("plan", help="Create a dry-run workstream plan.")
    plan_parser.add_argument("target", nargs="?", default=".", help="Repository path to plan for.")
    plan_parser.add_argument("--objective", required=True, help="Work objective to plan.")

    status_parser = subparsers.add_parser("status", help="Show latest Dispatch Engine run state.")
    status_parser.add_argument("target", nargs="?", default=".", help="Repository path containing .dispatch state.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "version":
        return _print({"version": __version__}, args.json)

    if args.command == "inspect":
        result = inspect_repo(Path(args.target))
        return _print(result, args.json)

    if args.command == "plan":
        inspection = inspect_repo(Path(args.target))
        result = plan_objective(Path(args.target), args.objective, inspection)
        return _print(result, args.json)

    if args.command == "status":
        result = latest_run_summary(Path(args.target))
        return _print(result, args.json)

    parser.error(f"unknown command: {args.command}")
    return 2


def _print(payload: dict, as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    kind = payload.get("kind")
    if kind == "inspection":
        print(f"Repository: {payload['repo_root']}")
        print("Instructions:")
        for item in payload["instructions"]:
            print(f"- {item}")
        print("Planning sources:")
        for item in payload["planning_sources"]:
            print(f"- {item}")
        print("Validation hints:")
        for item in payload["validation_hints"]:
            print(f"- {item}")
        return 0

    if kind == "plan":
        print(f"Objective: {payload['objective']}")
        print(f"Run state: {payload['state_dir']}")
        print("Workstreams:")
        for item in payload["workstreams"]:
            print(f"- {item['id']}: {item['title']} ({item['status']})")
        if payload["decisions"]:
            print("Pending decisions:")
            for item in payload["decisions"]:
                print(f"- {item['id']}: {item['question']}")
        return 0

    if kind == "status":
        print(payload["summary"])
        return 0

    if "version" in payload:
        print(payload["version"])
        return 0

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0
