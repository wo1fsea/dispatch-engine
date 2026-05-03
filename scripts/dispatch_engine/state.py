"""Run-state helpers for Dispatch Engine."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

from .agents import (
    VALIDATOR_REPORT_SCHEMA_VIOLATIONS,
    capability_profile_high_risk_grants,
    detect_protocol_violations,
    list_agents,
)
from .decisions import (
    list_autonomous_decisions,
    list_pending_decisions,
    list_unresolved_blockers,
    validate_decision_blocker_state,
)
from .events import EventCursorError, read_events, read_events_with_ids
from .runs import resolve_run_dir
from .supervisor import read_supervisors

TERMINAL_AGENT_STATUSES = frozenset({"completed", "failed", "cancelled"})
TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "cancelled"})
MATERIAL_STATUSES = frozenset({"completed", "failed", "blocked", "cancelled"})


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
    autonomous_decisions = _autonomous_decision_summary(selected)
    events = read_events(selected / "events.jsonl")
    agent_summary = _agent_observability(selected, workstreams, events)
    next_actions = _next_actions(
        run_status=data.get("status"),
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
        "cancellation": _cancellation_summary(data),
        "workstream_counts": counts,
        "pending_decisions": pending_decisions,
        "unresolved_blockers": len(unresolved_blockers),
        "decision_blocker_validation": decision_blocker_validation,
        "autonomous_decisions": autonomous_decisions,
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
        "capability_profiles": _capability_profile_summary(
            run_state_dir,
            agents,
            protocol_violations.get("detected", []),
        ),
    }


def _autonomous_decision_summary(run_state_dir: Path) -> dict[str, Any]:
    records = []
    decisions = sorted(
        list_autonomous_decisions(run_state_dir),
        key=lambda item: _record_id(item, "decision_id"),
    )
    for decision in decisions:
        autonomous_decision = decision.get("autonomous_decision", {})
        if not isinstance(autonomous_decision, dict):
            autonomous_decision = {}
        records.append(
            {
                "decision_id": _record_id(decision, "decision_id"),
                "selected_option_id": decision.get("selected_option_id"),
                "resolved_at": decision.get("resolved_at"),
                "rationale": autonomous_decision.get("rationale", ""),
                "validation_expected": autonomous_decision.get("validation_expected", []),
            }
        )
    return {"count": len(records), "records": records}


def _next_actions(
    *,
    run_status: str | None = None,
    pending_decision_records: list[dict[str, Any]],
    unresolved_blockers: list[dict[str, Any]],
    protocol_violations: dict[str, Any],
    agents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if run_status in TERMINAL_RUN_STATUSES:
        return []

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
    report_schema_actions = _report_schema_repair_actions(
        protocol_violations.get("detected", []),
        agents,
    )
    actions.extend(report_schema_actions)
    if violation_count:
        fallback_count = max(violation_count - len(report_schema_actions), 0)
        if fallback_count:
            actions.append({"type": "repair_protocol_violations", "count": fallback_count})

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


def _report_schema_repair_actions(
    detected_violations: list[dict[str, Any]],
    agents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    agent_by_id = {
        agent.get("agent_id"): agent
        for agent in agents
        if agent.get("agent_id")
    }
    actions: list[dict[str, Any]] = []
    for violation in detected_violations:
        diagnostic = violation.get("violation")
        if diagnostic not in VALIDATOR_REPORT_SCHEMA_VIOLATIONS:
            continue
        agent_id = violation.get("agent_id")
        details = violation.get("details", {})
        agent = agent_by_id.get(agent_id, {})
        action: dict[str, Any] = {
            "type": "repair_report_schema",
            "agent_id": agent_id,
            "role": agent.get("role") or details.get("role") or "validator",
            "report_path": details.get("report_path"),
            "diagnostic": diagnostic,
        }
        suggested_status = details.get("suggested_status")
        if suggested_status:
            action["suggested_status"] = suggested_status
        actions.append(action)
    return actions


def _cancellation_summary(run: dict[str, Any]) -> dict[str, Any] | None:
    if run.get("status") != "cancelled" and "cancellation_reason" not in run:
        return None
    return {
        "reason": run.get("cancellation_reason"),
        "cancelled_at": run.get("cancelled_at"),
        "cancelled_by": run.get("cancelled_by"),
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


def _capability_profile_summary(
    run_state_dir: Path,
    agents: list[dict[str, Any]],
    protocol_violations: list[dict[str, Any]],
) -> dict[str, Any]:
    agent_records = []
    pending_escalations = _pending_capability_escalations(run_state_dir, agents)
    escalations_by_agent: dict[str, list[dict[str, Any]]] = {}
    for escalation in pending_escalations:
        agent_id = escalation.get("agent_id")
        if agent_id:
            escalations_by_agent.setdefault(agent_id, []).append(escalation)

    for agent in sorted(agents, key=lambda item: item.get("agent_id", "")):
        profile = agent.get("capability_profile")
        if not isinstance(profile, dict):
            continue
        agent_id = str(agent.get("agent_id") or "")
        agent_records.append(
            {
                "agent_id": agent_id,
                "role": agent.get("role"),
                "status": agent.get("status"),
                "workstream": agent.get("workstream"),
                "profile_id": profile.get("profile_id"),
                "high_risk_capabilities": capability_profile_high_risk_grants(profile),
                "pending_escalations": escalations_by_agent.get(agent_id, []),
            }
        )

    pending_decisions = []
    for decision in list_pending_decisions(run_state_dir):
        capability = decision.get("capability")
        requested_mode = decision.get("requested_mode")
        if not capability:
            escalation = decision.get("capability_escalation")
            if isinstance(escalation, dict):
                capability = escalation.get("capability")
                requested_mode = escalation.get("requested_mode")
        if not capability:
            continue
        record = {
            "decision_id": _record_id(decision, "decision_id"),
            "capability": capability,
            "requested_mode": requested_mode,
        }
        if decision.get("workstream"):
            record["workstream"] = decision["workstream"]
        pending_decisions.append(record)

    capability_violations = [
        violation
        for violation in protocol_violations
        if violation.get("violation") == "capability_overreach"
    ]
    return {
        "agents": agent_records,
        "pending_decisions": sorted(
            pending_decisions,
            key=lambda item: (str(item.get("decision_id")), str(item.get("capability"))),
        ),
        "pending_escalations": sorted(
            pending_escalations,
            key=lambda item: (str(item.get("agent_id")), str(item.get("capability"))),
        ),
        "violations": capability_violations,
    }


def _pending_capability_escalations(
    run_state_dir: Path,
    agents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    escalations: list[dict[str, Any]] = []
    for agent in agents:
        report = _read_agent_report(run_state_dir, agent)
        if not isinstance(report, dict):
            continue
        for item in report.get("capability_escalations", []):
            if not isinstance(item, dict):
                continue
            if item.get("status") not in {"blocked", "pending", "requested"}:
                continue
            record = {
                "agent_id": agent.get("agent_id"),
                "workstream": agent.get("workstream"),
                "capability": item.get("capability"),
                "requested_mode": item.get("requested_mode"),
                "status": item.get("status"),
            }
            if item.get("decision_id"):
                record["decision_id"] = item["decision_id"]
            if item.get("reason"):
                record["reason"] = item["reason"]
            escalations.append(record)
    return escalations


def _read_agent_report(run_state_dir: Path, agent: dict[str, Any]) -> dict[str, Any] | None:
    report_path = agent.get("report_path")
    prefix = f".dispatch/runs/{run_state_dir.name}/"
    path: Path
    if isinstance(report_path, str) and report_path.startswith(prefix):
        path = run_state_dir / report_path.removeprefix(prefix)
    else:
        role = agent.get("role")
        directory = {"reviewer": "reviews", "validator": "validation"}.get(str(role), "reports")
        path = run_state_dir / directory / f"{agent.get('agent_id')}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


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
        alert = {"type": f"run_{run_status}", "run_id": run_id, "status": run_status}
        if run_status == "cancelled":
            alert["reason"] = run.get("cancellation_reason")
            alert["cancelled_at"] = run.get("cancelled_at")
        alerts.append(alert)

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
