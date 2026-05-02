"""Command-line interface for the bundled Dispatch Engine runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .coordinators import CoordinatorLaunchError, launch_run_coordinator, render_run_dry_run
from .plan_schema import PlanValidationError, import_dispatch_plan
from .state import run_status, tail_events
from .supervisor import launch_detached_coordinator


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

    run_parser = subparsers.add_parser("run", help="Render or launch a provider CLI coordinator.")
    run_parser.add_argument("target", help="Repository path containing .dispatch state.")
    run_parser.add_argument("--run-id", help="Use a specific run id instead of the latest run.")
    run_parser.add_argument("--provider", default="codex", help="Coordinator provider: codex or claude.")
    run_parser.add_argument("--dry-run", action="store_true", help="Render without launching a provider.")
    run_parser.add_argument("--detach", action="store_true", help="Start a background coordinator supervisor and return immediately.")
    _add_json_flag(run_parser)

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

    if args.command == "run":
        try:
            if args.dry_run and args.detach:
                raise CoordinatorLaunchError("--dry-run and --detach cannot be used together")
            if args.dry_run:
                result = render_run_dry_run(
                    Path(args.target),
                    run_id=args.run_id,
                    provider=args.provider,
                )
            elif args.detach:
                result = launch_detached_coordinator(
                    Path(args.target),
                    run_id=args.run_id,
                    provider=args.provider,
                )
            else:
                result = launch_run_coordinator(
                    Path(args.target),
                    run_id=args.run_id,
                    provider=args.provider,
                )
        except CoordinatorLaunchError as exc:
            return _print(
                {
                    "kind": "error",
                    "status": "coordinator_launch_error",
                    "summary": str(exc),
                },
                args.json,
            )
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
        if payload.get("kind") == "run_live":
            return 0 if payload.get("exit_code") == 0 else 1
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
            _print_agent_status(payload)
        return 0

    if kind == "tail":
        if payload.get("status") != "ok":
            print(payload["summary"])
            return 0
        for event in payload["events"]:
            workstream = f" [{event['workstream']}]" if "workstream" in event else ""
            print(f"{event['ts']} {event['type']}{workstream}")
        return 0

    if kind == "run_dry_run":
        print(f"Provider: {payload['provider']} ({payload['profile']})")
        print(f"Executable: {payload['executable']}")
        print(f"Run: {payload['run_id']}")
        print(f"Repo: {payload['repo_root']}")
        print(f"State: {payload['state_dir']}")
        print(f"Argv: {json.dumps(payload['argv'])}")
        print(f"Prompt: {payload['prompt_path']}")
        if payload.get("warnings"):
            print("Warnings:")
            for warning in payload["warnings"]:
                print(f"- {warning}")
        return 0

    if kind == "run_live":
        print(f"Provider: {payload['provider']} ({payload['profile']})")
        print(f"Run: {payload['run_id']}")
        print(f"State: {payload['state_dir']}")
        print(f"Exit: {payload['exit_code']}")
        print(f"Prompt: {payload['prompt_path']}")
        print(f"Stdout: {payload['stdout_path']}")
        print(f"Stderr: {payload['stderr_path']}")
        if payload.get("failure_reason"):
            print(f"Failure: {payload['failure_reason']}")
        return 0 if payload.get("exit_code") == 0 else 1

    if kind == "run_detached":
        print(f"Provider: {payload['provider']} ({payload['profile']})")
        print(f"Run: {payload['run_id']}")
        print(f"State: {payload['state_dir']}")
        print(f"Supervisor PID: {payload['supervisor_pid']}")
        print(f"Supervisor: {payload['supervisor_path']}")
        print(f"Prompt: {payload['prompt_path']}")
        print(f"Stdout: {payload['stdout_path']}")
        print(f"Stderr: {payload['stderr_path']}")
        return 0

    if "version" in payload:
        print(payload["version"])
        return 0

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _print_agent_status(payload: dict) -> None:
    agent_counts = payload.get("agent_counts", {})
    role_counts = agent_counts.get("by_role", {})
    status_counts = agent_counts.get("by_status", {})
    total_agents = sum(role_counts.values())
    supervisor_counts = payload.get("supervisor_counts", {}).get("by_status", {})
    if total_agents == 0:
        print("Agents: none")
        if supervisor_counts:
            print(f"Supervisors: {_format_counts(supervisor_counts)}")
        return

    role_text = _format_counts(role_counts)
    status_text = _format_counts(status_counts)
    print(f"Agents: total {total_agents}; roles {role_text}; statuses {status_text}")

    coordinator = payload.get("coordinator")
    if coordinator:
        heartbeat = coordinator.get("last_heartbeat_at") or "missing heartbeat"
        print(
            "Coordinator: "
            f"{coordinator.get('provider')}/{coordinator.get('profile')} "
            f"{coordinator.get('status')} ({heartbeat})"
        )

    heartbeat_summary = payload.get("heartbeat_summary", {})
    print(
        "Heartbeats: "
        f"{heartbeat_summary.get('with_heartbeat', 0)} present, "
        f"{heartbeat_summary.get('missing_heartbeat', 0)} missing"
    )
    if supervisor_counts:
        print(f"Supervisors: {_format_counts(supervisor_counts)}")

    assignments = payload.get("workstream_assignments", [])
    if assignments:
        rendered = [
            f"{item['workstream']} -> {item['agent_id']} ({item['role']} {item['status']})"
            for item in assignments
        ]
        print(f"Assignments: {'; '.join(rendered)}")

    violation_count = payload.get("protocol_violations", {}).get("count", 0)
    if violation_count:
        print(f"Protocol violations: {violation_count}")


def _format_counts(counts: dict) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{name}={count}" for name, count in sorted(counts.items()))
