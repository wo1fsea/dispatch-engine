"""Command-line interface for the bundled Dispatch Engine runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import __version__
from .cancel import cancel_run
from .coordinators import CoordinatorLaunchError, launch_run_coordinator, render_run_dry_run
from .dashboard import dashboard_status, launch_dashboard, serve_dashboard, stop_dashboard
from .decisions import (
    AUTONOMOUS_TECHNICAL_ACTOR,
    AUTONOMOUS_TECHNICAL_MODE,
    AUTONOMOUS_TECHNICAL_TRIGGER,
    DEFAULT_HEARTBEAT_INTERVAL_MINUTES,
    DecisionBlockerValidationError,
    STANDARD_AUTONOMOUS_EXCLUDED_CATEGORIES,
    resolve_decision,
)
from .plan_schema import PlanValidationError, import_dispatch_plan
from .protocol_resolutions import ProtocolResolutionValidationError, resolve_protocol_violation
from .state import run_alerts, run_events, run_status, tail_events
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

    events_parser = subparsers.add_parser("events", help="Read Dispatch Engine run events.")
    events_parser.add_argument("target", nargs="?", default=".", help="Repository path containing .dispatch state.")
    events_parser.add_argument("--run-id", help="Read a specific run id instead of the latest run.")
    events_parser.add_argument("--since", help="Return events after event id or numeric index.")
    _add_json_flag(events_parser)

    alerts_parser = subparsers.add_parser("alerts", help="Read material Dispatch Engine alerts.")
    alerts_parser.add_argument("target", nargs="?", default=".", help="Repository path containing .dispatch state.")
    alerts_parser.add_argument("--run-id", help="Read a specific run id instead of the latest run.")
    _add_json_flag(alerts_parser)

    dashboard_parser = subparsers.add_parser("dashboard", help="Start or report on a local dashboard observer.")
    dashboard_parser.add_argument("target", nargs="?", default=".", help="Repository path containing .dispatch state.")
    dashboard_parser.add_argument("--run-id", help="Use a specific run id instead of the latest run.")
    dashboard_parser.add_argument("--host", default="127.0.0.1", help="Dashboard bind host; defaults to 127.0.0.1.")
    dashboard_parser.add_argument("--port", type=int, default=0, help="Dashboard bind port; defaults to 0.")
    dashboard_parser.add_argument("--detach", action="store_true", help="Start or reuse a background dashboard service.")
    dashboard_parser.add_argument("--status", action="store_true", help="Report the recorded dashboard service state.")
    dashboard_parser.add_argument("--stop", action="store_true", help="Stop the recorded dashboard service.")
    dashboard_parser.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)
    _add_json_flag(dashboard_parser)

    for command, help_text in (
        ("cancel", "Cancel an active Dispatch Engine run."),
        ("stop", "Alias for cancel."),
    ):
        cancel_parser = subparsers.add_parser(command, help=help_text)
        cancel_parser.add_argument("target", help="Repository path containing .dispatch state.")
        cancel_parser.add_argument("--run-id", help="Cancel a specific run id instead of the latest run.")
        cancel_parser.add_argument(
            "--reason",
            default=None,
            help="Cancellation reason to record in durable run state.",
        )
        _add_json_flag(cancel_parser)

    resolve_parser = subparsers.add_parser("resolve-decision", help="Resolve a pending Dispatch Engine decision.")
    resolve_parser.add_argument("target", help="Repository path containing .dispatch state.")
    resolve_parser.add_argument("--id", required=True, help="Decision id to resolve.")
    resolve_parser.add_argument("--option", required=True, help="Selected option id.")
    resolve_parser.add_argument("--run-id", help="Resolve a specific run id instead of the latest run.")
    resolve_parser.add_argument("--actor", help="Actor recorded in decision state.")
    resolve_parser.add_argument("--resolution", help="Resolution text to record.")
    resolve_parser.add_argument(
        "--autonomous-technical",
        action="store_true",
        help="Record this as an autonomous technical decision after unanswered heartbeats.",
    )
    resolve_parser.add_argument("--unanswered-heartbeats", type=int, help="Unanswered heartbeat count.")
    resolve_parser.add_argument(
        "--heartbeat-interval-minutes",
        type=int,
        default=DEFAULT_HEARTBEAT_INTERVAL_MINUTES,
        help="Heartbeat interval used for autonomous decision observation.",
    )
    resolve_parser.add_argument("--first-seen-heartbeat-id", help="First unanswered heartbeat id.")
    resolve_parser.add_argument("--last-seen-heartbeat-id", help="Last unanswered heartbeat id.")
    resolve_parser.add_argument("--autonomous-rationale", help="Rationale for the autonomous technical decision.")
    resolve_parser.add_argument(
        "--validation-expected",
        action="append",
        default=[],
        help="Expected validation after the autonomous decision; repeatable.",
    )
    resolve_parser.add_argument(
        "--excluded-category",
        action="append",
        default=[],
        help="Excluded non-autonomous category asserted during autonomous decision review; repeatable.",
    )
    _add_json_flag(resolve_parser)

    protocol_resolution_parser = subparsers.add_parser(
        "resolve-protocol-violation",
        help="Record an audit resolution for a current protocol violation.",
    )
    protocol_resolution_parser.add_argument("target", help="Repository path containing .dispatch state.")
    protocol_resolution_parser.add_argument("--run-id", help="Resolve a specific run id instead of the latest run.")
    protocol_resolution_parser.add_argument("--violation", required=True, help="Protocol violation name to resolve.")
    protocol_resolution_parser.add_argument(
        "--resolution",
        required=True,
        help="Resolution kind: acknowledged, accepted_with_concerns, superseded_by_validation, or false_positive.",
    )
    protocol_resolution_parser.add_argument("--rationale", required=True, help="Why this resolution is valid.")
    protocol_resolution_parser.add_argument("--evidence", required=True, help="Evidence supporting the resolution.")
    protocol_resolution_parser.add_argument("--agent-id", help="Optional agent id selector.")
    protocol_resolution_parser.add_argument("--workstream", help="Optional workstream selector.")
    protocol_resolution_parser.add_argument("--actor", help="Actor recorded in resolution state.")
    _add_json_flag(protocol_resolution_parser)

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

    if args.command == "events":
        result = run_events(Path(args.target), run_id=args.run_id, since=args.since)
        return _print(result, args.json)

    if args.command == "alerts":
        result = run_alerts(Path(args.target), run_id=args.run_id)
        return _print(result, args.json)

    if args.command == "dashboard":
        selected_modes = [args.detach, args.status, args.stop, args.serve]
        if sum(1 for selected in selected_modes if selected) > 1:
            return _print(
                {
                    "kind": "error",
                    "status": "invalid_dashboard_mode",
                    "summary": "Use only one of --detach, --status, --stop, or --serve.",
                },
                args.json,
            )
        if args.status:
            result = dashboard_status(Path(args.target), run_id=args.run_id)
        elif args.stop:
            result = stop_dashboard(Path(args.target), run_id=args.run_id)
        elif args.serve:
            if args.run_id is None:
                result = launch_dashboard(Path(args.target), host=args.host, port=args.port, detach=False)
            else:
                result = serve_dashboard(Path(args.target), run_id=args.run_id, host=args.host, port=args.port)
        else:
            result = launch_dashboard(
                Path(args.target),
                run_id=args.run_id,
                host=args.host,
                port=args.port,
                detach=args.detach,
            )
        return _print(result, args.json)

    if args.command in {"cancel", "stop"}:
        result = cancel_run(Path(args.target), run_id=args.run_id, reason=args.reason)
        return _print(result, args.json)

    if args.command == "resolve-decision":
        result = _resolve_decision_command(
            Path(args.target),
            decision_id=args.id,
            option_id=args.option,
            run_id=args.run_id,
            actor=args.actor,
            resolution=args.resolution,
            autonomous_technical=args.autonomous_technical,
            unanswered_heartbeats=args.unanswered_heartbeats,
            heartbeat_interval_minutes=args.heartbeat_interval_minutes,
            first_seen_heartbeat_id=args.first_seen_heartbeat_id,
            last_seen_heartbeat_id=args.last_seen_heartbeat_id,
            autonomous_rationale=args.autonomous_rationale,
            validation_expected=args.validation_expected,
            excluded_categories=args.excluded_category,
        )
        return _print(result, args.json)

    if args.command == "resolve-protocol-violation":
        result = _resolve_protocol_violation_command(
            Path(args.target),
            run_id=args.run_id,
            violation=args.violation,
            resolution=args.resolution,
            rationale=args.rationale,
            evidence=args.evidence,
            agent_id=args.agent_id,
            workstream=args.workstream,
            actor=args.actor,
        )
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

    if kind == "events":
        if payload.get("status") != "ok":
            print(payload["summary"])
            return 0
        for event in payload["events"]:
            workstream = f" [{event['workstream']}]" if "workstream" in event else ""
            print(f"{event['id']} {event['ts']} {event['type']}{workstream}")
        return 0

    if kind == "alerts":
        if payload.get("status") != "ok":
            print(payload["summary"])
            return 0
        for alert in payload["alerts"]:
            print(f"{alert['id']} {alert['type']}")
        return 0

    if kind == "dashboard":
        print(f"Dashboard: {payload['status']}")
        print(f"Run: {payload['run_id']}")
        print(f"URL: {payload['url']}")
        print(f"State: {payload['state_dir']}")
        print(f"PID: {payload['pid']}")
        return 0

    if kind in {"dashboard_status", "dashboard_stop"}:
        print(payload["summary"])
        if payload.get("url"):
            print(f"URL: {payload['url']}")
        if payload.get("pid"):
            print(f"PID: {payload['pid']}")
        print(f"Alive: {payload.get('alive')}")
        return 0

    if kind == "decision_resolution":
        print(f"Resolved decision: {payload['decision_id']}")
        print(f"Option: {payload['selected_option_id']}")
        print(f"State: {payload['state_dir']}")
        return 0

    if kind == "protocol_violation_resolution":
        print(f"Resolved protocol violation: {payload['violation']}")
        print(f"Resolution: {payload['resolution']['resolution']}")
        print(f"State: {payload['state_dir']}")
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

    if kind == "run_cancel":
        print(f"Cancelled run: {payload['run_id']}")
        print(f"State: {payload['state_dir']}")
        print(f"Reason: {payload['reason']}")
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


def _resolve_decision_command(
    target: Path,
    *,
    decision_id: str,
    option_id: str,
    run_id: str | None,
    actor: str | None,
    resolution: str | None,
    autonomous_technical: bool = False,
    unanswered_heartbeats: int | None = None,
    heartbeat_interval_minutes: int = DEFAULT_HEARTBEAT_INTERVAL_MINUTES,
    first_seen_heartbeat_id: str | None = None,
    last_seen_heartbeat_id: str | None = None,
    autonomous_rationale: str | None = None,
    validation_expected: list[str] | None = None,
    excluded_categories: list[str] | None = None,
) -> dict:
    from .runs import resolve_run_dir

    root = target.resolve()
    selected = resolve_run_dir(root, run_id)
    if selected is None:
        result = {
            "kind": "error",
            "status": "missing_run" if run_id else "no_run",
            "summary": f"Run not found: {run_id}" if run_id else "No Dispatch Engine runs found.",
        }
        if run_id:
            result["run_id"] = run_id
        return result

    resolved_actor = actor or "dispatch-engine"
    resolution_mode = None
    autonomous_decision = None
    if autonomous_technical:
        if actor is not None and actor != AUTONOMOUS_TECHNICAL_ACTOR:
            return {
                "kind": "error",
                "status": "invalid_decision_resolution",
                "summary": f"--autonomous-technical requires --actor {AUTONOMOUS_TECHNICAL_ACTOR}",
                "run_id": selected.name,
                "state_dir": str(selected),
            }
        resolved_actor = AUTONOMOUS_TECHNICAL_ACTOR
        resolution_mode = AUTONOMOUS_TECHNICAL_MODE
        autonomous_decision = _autonomous_decision_metadata(
            unanswered_heartbeats=unanswered_heartbeats,
            heartbeat_interval_minutes=heartbeat_interval_minutes,
            first_seen_heartbeat_id=first_seen_heartbeat_id,
            last_seen_heartbeat_id=last_seen_heartbeat_id,
            autonomous_rationale=autonomous_rationale,
            validation_expected=validation_expected or [],
            excluded_categories=excluded_categories or [],
        )
        if resolution is None:
            resolution = (
                f"Autonomous technical choice after "
                f"{unanswered_heartbeats or 0} unanswered heartbeat checks."
            )

    try:
        decision = resolve_decision(
            selected,
            decision_id,
            option_id=option_id,
            resolution=resolution,
            actor=resolved_actor,
            resolution_mode=resolution_mode,
            autonomous_decision=autonomous_decision,
        )
    except DecisionBlockerValidationError as exc:
        return {
            "kind": "error",
            "status": "invalid_decision_resolution",
            "summary": str(exc),
            "run_id": selected.name,
            "state_dir": str(selected),
        }

    return {
        "kind": "decision_resolution",
        "status": "ok",
        "summary": f"Resolved decision {decision_id}.",
        "run_id": selected.name,
        "state_dir": str(selected),
        "decision_id": decision_id,
        "selected_option_id": option_id,
        "decision": decision,
    }


def _resolve_protocol_violation_command(
    target: Path,
    *,
    run_id: str | None,
    violation: str,
    resolution: str,
    rationale: str,
    evidence: str,
    agent_id: str | None,
    workstream: str | None,
    actor: str | None,
) -> dict:
    from .runs import resolve_run_dir

    root = target.resolve()
    selected = resolve_run_dir(root, run_id)
    if selected is None:
        result = {
            "kind": "error",
            "status": "missing_run" if run_id else "no_run",
            "summary": f"Run not found: {run_id}" if run_id else "No Dispatch Engine runs found.",
        }
        if run_id:
            result["run_id"] = run_id
        return result

    try:
        record = resolve_protocol_violation(
            selected,
            violation=violation,
            resolution=resolution,
            rationale=rationale,
            evidence=evidence,
            agent_id=agent_id,
            workstream=workstream,
            actor=actor or "dispatch-engine",
        )
    except ProtocolResolutionValidationError as exc:
        return {
            "kind": "error",
            "status": exc.status,
            "summary": str(exc),
            "run_id": selected.name,
            "state_dir": str(selected),
        }

    return {
        "kind": "protocol_violation_resolution",
        "status": "ok",
        "summary": f"Resolved protocol violation {violation}.",
        "run_id": selected.name,
        "state_dir": str(selected),
        "violation": violation,
        "matched_violation": record["matched_violation"],
        "resolution": record,
    }


def _autonomous_decision_metadata(
    *,
    unanswered_heartbeats: int | None,
    heartbeat_interval_minutes: int,
    first_seen_heartbeat_id: str | None,
    last_seen_heartbeat_id: str | None,
    autonomous_rationale: str | None,
    validation_expected: list[str],
    excluded_categories: list[str],
) -> dict:
    merged_excluded_categories = list(STANDARD_AUTONOMOUS_EXCLUDED_CATEGORIES)
    for category in excluded_categories:
        if category not in merged_excluded_categories:
            merged_excluded_categories.append(category)

    record = {
        "trigger": AUTONOMOUS_TECHNICAL_TRIGGER,
        "unanswered_heartbeat_count": unanswered_heartbeats,
        "heartbeat_interval_minutes": heartbeat_interval_minutes,
        "technical_scope": True,
        "conservative": True,
        "reversible": True,
        "inside_approved_objective": True,
        "excluded_categories": merged_excluded_categories,
        "rationale": autonomous_rationale,
        "validation_expected": validation_expected,
    }
    if first_seen_heartbeat_id is not None:
        record["first_seen_heartbeat_id"] = first_seen_heartbeat_id
    if last_seen_heartbeat_id is not None:
        record["last_seen_heartbeat_id"] = last_seen_heartbeat_id
    return record
