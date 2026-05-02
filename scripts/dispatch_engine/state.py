"""Run-state helpers for Dispatch Engine."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

from .agents import detect_protocol_violations, list_agents
from .decisions import (
    list_pending_decisions,
    list_unresolved_blockers,
    validate_decision_blocker_state,
)
from .events import read_events
from .runs import resolve_run_dir

TERMINAL_AGENT_STATUSES = frozenset({"completed", "failed", "cancelled"})


def latest_run_summary(target: Path) -> dict:
    return run_status(target)


def run_status(target: Path, run_id: str | None = None) -> dict:
    root = target.resolve()
    selected = resolve_run_dir(root, run_id)
    if selected is None:
        if run_id:
            return _missing_run(run_id)
        return _no_run()

    run_file = selected / "run.json"
    if not run_file.exists():
        return {
            "kind": "status",
            "status": "missing_run_file",
            "summary": f"Run has no run.json: {selected}",
        }

    data = json.loads(run_file.read_text(encoding="utf-8"))
    workstreams = data.get("workstreams", [])
    counts = dict(Counter(item.get("status", "unknown") for item in workstreams))
    pending_decision_records = list_pending_decisions(selected)
    if not pending_decision_records and not (selected / "decisions.jsonl").exists():
        pending_decision_records = [
            item for item in data.get("decisions", []) if item.get("status", "pending") == "pending"
        ]
    pending_decisions = len(pending_decision_records)
    unresolved_blockers = list_unresolved_blockers(selected)
    decision_blocker_validation = validate_decision_blocker_state(selected)
    events = read_events(selected / "events.jsonl")
    agent_summary = _agent_observability(selected, workstreams, events)
    summary = (
        f"Run {data.get('run_id')} [{data.get('status', 'unknown')}] "
        f"has {len(workstreams)} workstream(s), {pending_decisions} pending decision(s), "
        f"{len(unresolved_blockers)} unresolved blocker(s): "
        f"{data.get('objective')}"
    )
    return {
        "kind": "status",
        "status": "ok",
        "summary": summary,
        "run_id": data.get("run_id"),
        "objective": data.get("objective"),
        "run_status": data.get("status"),
        "workstream_counts": counts,
        "pending_decisions": pending_decisions,
        "unresolved_blockers": len(unresolved_blockers),
        "decision_blocker_validation": decision_blocker_validation,
        "state_dir": str(selected),
        "last_event_at": events[-1].get("ts") if events else None,
        **agent_summary,
    }


def tail_events(target: Path, run_id: str | None = None) -> dict:
    root = target.resolve()
    selected = resolve_run_dir(root, run_id)
    if selected is None:
        if run_id:
            result = _missing_run(run_id)
            result["kind"] = "tail"
            result["events"] = []
            return result
        result = _no_run()
        result["kind"] = "tail"
        result["events"] = []
        return result

    events = read_events(selected / "events.jsonl")
    return {
        "kind": "tail",
        "status": "ok",
        "summary": f"Run {selected.name} has {len(events)} event(s).",
        "run_id": selected.name,
        "state_dir": str(selected),
        "events": events,
    }


def _no_run() -> dict:
    return {
        "kind": "status",
        "status": "no_run",
        "summary": "No Dispatch Engine runs found.",
    }


def _missing_run(run_id: str) -> dict:
    return {
        "kind": "status",
        "status": "missing_run",
        "summary": f"Run not found: {run_id}",
        "run_id": run_id,
    }


def _agent_observability(
    run_state_dir: Path,
    workstreams: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    agents = list_agents(run_state_dir)
    coordinator = _first_coordinator(agents)
    assignments = _active_workstream_assignments(agents)
    protocol_violations = _protocol_violation_summary(run_state_dir, events)
    return {
        "agents": agents,
        "coordinator": coordinator,
        "provider": coordinator.get("provider") if coordinator else None,
        "profile": coordinator.get("profile") if coordinator else None,
        "agent_counts": {
            "by_role": dict(Counter(agent.get("role", "unknown") for agent in agents)),
            "by_status": dict(Counter(agent.get("status", "unknown") for agent in agents)),
        },
        "workstream_assignments": assignments,
        "workstream_progress": _workstream_progress(workstreams, assignments),
        "heartbeat_summary": _heartbeat_summary(agents),
        "protocol_violations": protocol_violations,
    }


def _first_coordinator(agents: list[dict[str, Any]]) -> dict[str, Any] | None:
    for agent in agents:
        if agent.get("role") == "coordinator":
            return agent
    return None


def _active_workstream_assignments(agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assignments = []
    for agent in agents:
        workstream = agent.get("workstream")
        if not workstream:
            continue
        status = agent.get("status", "unknown")
        if status in TERMINAL_AGENT_STATUSES:
            continue
        assignments.append(
            {
                "workstream": workstream,
                "agent_id": agent.get("agent_id"),
                "role": agent.get("role"),
                "status": status,
            }
        )
    return sorted(assignments, key=lambda item: (item["workstream"], item["agent_id"] or ""))


def _heartbeat_summary(agents: list[dict[str, Any]]) -> dict[str, int]:
    with_heartbeat = sum(1 for agent in agents if agent.get("last_heartbeat_at"))
    return {
        "total_agents": len(agents),
        "with_heartbeat": with_heartbeat,
        "missing_heartbeat": len(agents) - with_heartbeat,
    }


def _workstream_progress(
    workstreams: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
) -> dict[str, int]:
    assigned_workstreams = {item["workstream"] for item in assignments}
    unassigned = sum(
        1
        for item in workstreams
        if item.get("id") not in assigned_workstreams
        and item.get("status", "unknown") not in {"completed", "failed", "blocked"}
    )
    return {
        "completed": sum(1 for item in workstreams if item.get("status") == "completed"),
        "failed": sum(1 for item in workstreams if item.get("status") == "failed"),
        "blocked": sum(1 for item in workstreams if item.get("status") == "blocked"),
        "unassigned": unassigned,
    }


def _protocol_violation_summary(run_state_dir: Path, events: list[dict[str, Any]]) -> dict[str, Any]:
    event_violations = [_event_protocol_violation(event) for event in events if event.get("type") == "protocol.violation"]
    detected_violations = detect_protocol_violations(run_state_dir)
    unique = {
        json.dumps(item, sort_keys=True)
        for item in [*event_violations, *detected_violations]
    }
    return {
        "count": len(unique),
        "event_count": len(event_violations),
        "detected_count": len(detected_violations),
        "detected": detected_violations,
    }


def _event_protocol_violation(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    violation = {
        "violation": payload.get("violation", "unknown"),
        "details": payload.get("details", {}),
    }
    if "workstream" in event:
        violation["workstream"] = event["workstream"]
    return violation
