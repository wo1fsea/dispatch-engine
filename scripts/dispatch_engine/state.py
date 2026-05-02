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
from .events import EventCursorError, read_events, read_events_with_ids
from .runs import resolve_run_dir
from .supervisor import read_supervisors

TERMINAL_AGENT_STATUSES = frozenset({"completed", "failed", "cancelled"})
MATERIAL_STATUSES = frozenset({"completed", "failed", "blocked"})


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
    next_actions = _next_actions(
        pending_decision_records=pending_decision_records,
        unresolved_blockers=unresolved_blockers,
        protocol_violations=agent_summary["protocol_violations"],
        agents=agent_summary["agents"],
    )
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
        "next_actions": next_actions,
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


def run_events(target: Path, run_id: str | None = None, *, since: str | None = None) -> dict:
    root = target.resolve()
    selected = resolve_run_dir(root, run_id)
    if selected is None:
        result = _missing_run(run_id) if run_id else _no_run()
        result["kind"] = "events"
        result["events"] = []
        return result

    try:
        events = read_events_with_ids(selected / "events.jsonl", since=since)
    except EventCursorError as exc:
        return {
            "kind": "error",
            "status": "invalid_event_cursor",
            "summary": str(exc),
        }

    return {
        "kind": "events",
        "status": "ok",
        "summary": f"Run {selected.name} has {len(events)} matching event(s).",
        "run_id": selected.name,
        "state_dir": str(selected),
        "events": events,
    }


def run_alerts(target: Path, run_id: str | None = None) -> dict:
    root = target.resolve()
    selected = resolve_run_dir(root, run_id)
    if selected is None:
        result = _missing_run(run_id) if run_id else _no_run()
        result["kind"] = "alerts"
        result["alerts"] = []
        return result

    run_file = selected / "run.json"
    if not run_file.exists():
        return {
            "kind": "alerts",
            "status": "missing_run_file",
            "summary": f"Run has no run.json: {selected}",
            "alerts": [],
        }

    data = json.loads(run_file.read_text(encoding="utf-8"))
    events = read_events(selected / "events.jsonl")
    agents = list_agents(selected)
    alerts = _material_alerts(
        run_id=selected.name,
        run=data,
        pending_decisions=list_pending_decisions(selected),
        unresolved_blockers=list_unresolved_blockers(selected),
        protocol_violations=_protocol_violations(selected, events),
        agents=agents,
    )
    return {
        "kind": "alerts",
        "status": "ok",
        "summary": f"Run {selected.name} has {len(alerts)} material alert(s).",
        "run_id": selected.name,
        "state_dir": str(selected),
        "alerts": _with_alert_ids(alerts),
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
    supervisors = read_supervisors(run_state_dir)
    return {
        "agents": agents,
        "supervisors": supervisors,
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
        "supervisor_counts": {
            "by_status": dict(Counter(item.get("status", "unknown") for item in supervisors)),
        },
        "protocol_violations": protocol_violations,
    }


def _next_actions(
    *,
    pending_decision_records: list[dict[str, Any]],
    unresolved_blockers: list[dict[str, Any]],
    protocol_violations: dict[str, Any],
    agents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for decision in sorted(pending_decision_records, key=lambda item: _record_id(item, "decision_id")):
        action: dict[str, Any] = {
            "type": "decision_required",
            "decision_id": _record_id(decision, "decision_id"),
            "question": decision.get("question", ""),
        }
        if decision.get("workstream"):
            action["workstream"] = decision["workstream"]
        recommended_option = _recommended_option_id(decision.get("options"))
        if recommended_option:
            action["recommended_option"] = recommended_option
        actions.append(action)

    if unresolved_blockers:
        actions.append(
            {
                "type": "blocker_resolution_required",
                "count": len(unresolved_blockers),
                "blocker_ids": sorted(_record_id(item, "blocker_id") for item in unresolved_blockers),
            }
        )

    violation_count = protocol_violations.get("count", 0)
    if violation_count:
        actions.append({"type": "repair_protocol_violations", "count": violation_count})

    failed_agents = sorted(
        agent.get("agent_id", "")
        for agent in agents
        if agent.get("status") == "failed" and agent.get("agent_id")
    )
    if failed_agents:
        actions.append(
            {
                "type": "inspect_failed_agents",
                "count": len(failed_agents),
                "agent_ids": failed_agents,
            }
        )

    return actions


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
    unique = _unique_protocol_violations([*event_violations, *detected_violations])
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


def _material_alerts(
    *,
    run_id: str,
    run: dict[str, Any],
    pending_decisions: list[dict[str, Any]],
    unresolved_blockers: list[dict[str, Any]],
    protocol_violations: list[dict[str, Any]],
    agents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for decision in sorted(pending_decisions, key=lambda item: _record_id(item, "decision_id")):
        alert: dict[str, Any] = {
            "type": "pending_decision",
            "run_id": run_id,
            "decision_id": _record_id(decision, "decision_id"),
            "question": decision.get("question", ""),
        }
        if decision.get("workstream"):
            alert["workstream"] = decision["workstream"]
        recommended_option = _recommended_option_id(decision.get("options"))
        if recommended_option:
            alert["recommended_option"] = recommended_option
        alerts.append(alert)

    for blocker in sorted(unresolved_blockers, key=lambda item: _record_id(item, "blocker_id")):
        alert = {
            "type": "unresolved_blocker",
            "run_id": run_id,
            "blocker_id": _record_id(blocker, "blocker_id"),
            "summary": blocker.get("summary", ""),
        }
        if blocker.get("workstream"):
            alert["workstream"] = blocker["workstream"]
        alerts.append(alert)

    for violation in protocol_violations:
        alert = {
            "type": "protocol_violation",
            "run_id": run_id,
            "violation": violation.get("violation", "unknown"),
            "details": violation.get("details", {}),
        }
        if violation.get("agent_id"):
            alert["agent_id"] = violation["agent_id"]
        if violation.get("workstream"):
            alert["workstream"] = violation["workstream"]
        alerts.append(alert)

    for agent in sorted(agents, key=lambda item: item.get("agent_id", "")):
        if agent.get("status") != "failed":
            continue
        alert = {
            "type": "failed_agent",
            "run_id": run_id,
            "agent_id": agent.get("agent_id"),
            "role": agent.get("role"),
        }
        if agent.get("workstream"):
            alert["workstream"] = agent["workstream"]
        if agent.get("failure_reason"):
            alert["reason"] = agent["failure_reason"]
        alerts.append(alert)

    run_status = run.get("status")
    if run_status in MATERIAL_STATUSES:
        alerts.append({"type": f"run_{run_status}", "run_id": run_id, "status": run_status})

    for workstream in sorted(run.get("workstreams", []), key=lambda item: item.get("id", "")):
        workstream_status = workstream.get("status")
        if workstream_status not in MATERIAL_STATUSES:
            continue
        alerts.append(
            {
                "type": f"workstream_{workstream_status}",
                "run_id": run_id,
                "workstream": workstream.get("id"),
                "status": workstream_status,
            }
        )
    return alerts


def _protocol_violations(run_state_dir: Path, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    event_violations = [_event_protocol_violation(event) for event in events if event.get("type") == "protocol.violation"]
    return _unique_protocol_violations([*event_violations, *detect_protocol_violations(run_state_dir)])


def _unique_protocol_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for violation in violations:
        key = json.dumps(violation, sort_keys=True)
        unique[key] = violation
    return [unique[key] for key in sorted(unique)]


def _with_alert_ids(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {**alert, "id": f"alert-{index:06d}"}
        for index, alert in enumerate(alerts, start=1)
    ]


def _record_id(record: dict[str, Any], field: str) -> str:
    return str(record.get(field) or record.get("id") or "")


def _recommended_option_id(options: Any) -> str | None:
    if not isinstance(options, list):
        return None
    for option in options:
        if not isinstance(option, dict):
            continue
        if option.get("recommended") is True or str(option.get("status", "")).lower() == "recommended":
            return str(option.get("option_id") or option.get("id") or "")
        if str(option.get("marker", "")).lower() == "recommended":
            return str(option.get("option_id") or option.get("id") or "")
    return None
