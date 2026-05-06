"""Run-state helpers for Dispatch Engine."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
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
from .protocol_resolutions import (
    event_protocol_violation,
    protocol_resolution_overlay,
    unique_protocol_violations,
)
from .runs import resolve_run_dir
from .supervisor import read_supervisors

TERMINAL_AGENT_STATUSES = frozenset({"completed", "completed_with_concerns", "failed", "cancelled"})
TERMINAL_RUN_STATUSES = frozenset({"completed", "failed", "cancelled"})
MATERIAL_STATUSES = frozenset({"completed", "failed", "blocked", "cancelled"})
RUNNING_AGENT_STATUSES = frozenset({"registered", "running"})
VALIDATION_EVIDENCE_ROLES = frozenset({"reviewer", "validator"})
PROVIDER_NATIVE_NO_REPORT_STALE_AFTER_SECONDS = 60 * 60
PROVIDER_NATIVE_LAUNCH_EVIDENCE_FIELDS = (
    "provider_native_agent_id",
    "provider_native_spawn_ref",
    "launch_evidence.spawn_agent_id",
    "launch_evidence.provider_native_spawn_ref",
    "provider_launch.evidence.provider_native_spawn_ref",
)
LAUNCH_EVIDENCE_FIELDS = (
    *PROVIDER_NATIVE_LAUNCH_EVIDENCE_FIELDS,
    "pid",
    "stdout_path",
    "stderr_path",
)
STDOUT_DECISION_PATTERNS = (
    "i need your decision",
    "decision before proceeding",
    "approve expanding",
)


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
    events = read_events(selected / "events.jsonl")
    agents = list_agents(selected)
    workstreams = _normalized_workstream_records(selected, data, events, agents=agents)
    counts = dict(Counter(item.get("status", "unknown") for item in workstreams))
    pending_decision_records = _pending_decision_records(selected, data)
    pending_decisions = len(pending_decision_records)
    unresolved_blockers = list_unresolved_blockers(selected)
    decision_blocker_validation = validate_decision_blocker_state(selected)
    autonomous_decisions = _autonomous_decision_summary(selected)
    agent_summary = _agent_observability(selected, workstreams, events, agents)
    lifecycle_diagnostics = _lifecycle_diagnostics(
        selected,
        run=data,
        agents=agent_summary["agents"],
        supervisors=agent_summary["supervisors"],
        events=events,
        pending_decisions=pending_decision_records,
    )
    next_actions = _next_actions(
        run_status=data.get("status"),
        pending_decision_records=pending_decision_records,
        unresolved_blockers=unresolved_blockers,
        protocol_violations=agent_summary["protocol_violations"],
        agents=agent_summary["agents"],
        lifecycle_diagnostics=lifecycle_diagnostics,
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
        "lifecycle_diagnostics": lifecycle_diagnostics,
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
    pending_decisions = _pending_decision_records(selected, data)
    unresolved_blockers = list_unresolved_blockers(selected)
    protocol_violations = _protocol_violation_summary(selected, events)
    supervisors = read_supervisors(selected)
    lifecycle_diagnostics = _lifecycle_diagnostics(
        selected,
        run=data,
        agents=agents,
        supervisors=supervisors,
        events=events,
        pending_decisions=pending_decisions,
    )
    alerts = _material_alerts(
        run_id=selected.name,
        run=data,
        pending_decisions=pending_decisions,
        unresolved_blockers=unresolved_blockers,
        protocol_violations=protocol_violations["unresolved"],
        agents=agents,
        lifecycle_diagnostics=lifecycle_diagnostics,
    )
    return {
        "kind": "alerts",
        "status": "ok",
        "summary": f"Run {selected.name} has {len(alerts)} material alert(s).",
        "run_id": selected.name,
        "state_dir": str(selected),
        "protocol_violation_resolutions": protocol_violations["resolution_summary"],
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


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _agent_observability(
    run_state_dir: Path,
    workstreams: list[dict[str, Any]],
    events: list[dict[str, Any]],
    agents: list[dict[str, Any]],
) -> dict[str, Any]:
    coordinator = _first_coordinator(agents)
    assignments = _workstream_assignments(agents, workstreams, events)
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
        "protocol_violation_resolutions": protocol_violations["resolution_summary"],
        "capability_profiles": _capability_profile_summary(
            run_state_dir,
            agents,
            protocol_violations.get("detected", []),
        ),
    }


def _pending_decision_records(run_state_dir: Path, run: dict[str, Any]) -> list[dict[str, Any]]:
    records = list_pending_decisions(run_state_dir)
    if not records and not (run_state_dir / "decisions.jsonl").exists():
        records = [
            item for item in run.get("decisions", []) if item.get("status", "pending") == "pending"
        ]
    return records


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
    lifecycle_diagnostics: list[dict[str, Any]],
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

    violation_count = protocol_violations.get("unresolved_count", protocol_violations.get("count", 0))
    report_schema_actions = _report_schema_repair_actions(
        protocol_violations.get("unresolved_detected", protocol_violations.get("detected", [])),
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

    lifecycle_actions = [
        diagnostic
        for diagnostic in lifecycle_diagnostics
        if diagnostic.get("type") in {
            "missing_agent_launch_evidence",
            "incomplete_validation_evidence",
            "orphaned_running_agent",
            "provider_native_spawn_without_report",
            "report_only_decision_request",
            "stale_detached_supervisor",
            "stale_validation_worker_without_report",
            "stdout_only_decision_request",
        }
    ]
    if lifecycle_actions:
        actions.append(
            {
                "type": "inspect_lifecycle_diagnostics",
                "count": len(lifecycle_actions),
                "diagnostic_types": sorted({str(item.get("type")) for item in lifecycle_actions}),
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


def _normalized_workstream_records(
    run_state_dir: Path,
    run: dict[str, Any],
    events: list[dict[str, Any]] | None = None,
    *,
    agents: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for item in run.get("workstreams", []):
        if isinstance(item, dict) and item.get("id"):
            records[str(item["id"])] = dict(item)

    workstream_dir = run_state_dir / "workstreams"
    if workstream_dir.is_dir():
        for path in sorted(workstream_dir.glob("*.json")):
            item = _read_json_object(path)
            if item and item.get("id"):
                records[str(item["id"])] = item

    event_assignments = _event_workstream_assignments(
        read_events(run_state_dir / "events.jsonl") if events is None else events
    )
    active_assignments = _active_agent_workstream_assignment_map(agents or [])
    normalized: list[dict[str, Any]] = []
    for workstream_id, item in records.items():
        record = dict(item)
        record["id"] = workstream_id
        active_assignment = active_assignments.get(workstream_id)
        record_assignment = _workstream_record_assignment(record)
        event_assignment = event_assignments.get(workstream_id)
        assignment = active_assignment or record_assignment or event_assignment
        status = _normalized_workstream_status(record, assignment)
        record["status"] = status
        if assignment and (
            record_assignment
            or not _is_terminal_workstream_status(status)
            or status == "cancelled"
        ):
            record.setdefault("assigned_agent", assignment.get("agent_id"))
            record.setdefault("assigned_role", assignment.get("role"))
        normalized.append(record)
    return sorted(normalized, key=lambda item: item["id"])


def _workstream_assignments(
    agents: list[dict[str, Any]],
    workstreams: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_workstream = _active_agent_workstream_assignment_map(agents)
    by_workstream = {workstream: dict(assignment) for workstream, assignment in by_workstream.items()}

    for item in workstreams:
        workstream_id = str(item.get("id") or "")
        if not workstream_id or workstream_id in by_workstream:
            continue
        status = str(item.get("status") or "unknown")
        assignment = _workstream_record_assignment(item)
        if assignment:
            by_workstream[workstream_id] = _assignment_record(
                workstream=workstream_id,
                agent_id=assignment.get("agent_id"),
                role=assignment.get("role"),
                status=status,
            )

    for workstream_id, assignment in _event_workstream_assignments(events).items():
        if workstream_id in by_workstream:
            continue
        workstream = next((item for item in workstreams if item.get("id") == workstream_id), {})
        status = str(workstream.get("status") or assignment.get("status") or "assigned")
        if _is_terminal_workstream_status(status) and status != "cancelled":
            continue
        by_workstream[workstream_id] = _assignment_record(
            workstream=workstream_id,
            agent_id=assignment.get("agent_id"),
            role=assignment.get("role"),
            status=status,
        )

    return sorted(by_workstream.values(), key=lambda item: (item["workstream"], item["agent_id"] or ""))


def _active_agent_workstream_assignment_map(agents: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    assignments: dict[str, dict[str, Any]] = {}
    for agent in agents:
        workstream = agent.get("workstream")
        if not workstream:
            continue
        status = agent.get("status", "unknown")
        if status in TERMINAL_AGENT_STATUSES:
            continue
        assignments[str(workstream)] = _assignment_record(
            workstream=str(workstream),
            agent_id=agent.get("agent_id"),
            role=agent.get("role"),
            status=status,
        )
    return assignments


def _workstream_record_assignment(item: dict[str, Any]) -> dict[str, Any] | None:
    agent_id = _first_string(item, "assigned_agent", "assigned_agent_id", "agent_id", "worker_id")
    if not agent_id:
        return None
    return {
        "agent_id": agent_id,
        "role": _first_string(item, "assigned_role", "role") or "worker",
        "status": str(item.get("status") or item.get("state") or "assigned"),
    }


def _event_workstream_assignments(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    assignments: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.get("type") != "workstream.assigned":
            continue
        workstream = event.get("workstream")
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        agent_id = payload.get("agent_id")
        if not isinstance(workstream, str) or not workstream or not isinstance(agent_id, str) or not agent_id:
            continue
        assignments[workstream] = {
            "agent_id": agent_id,
            "role": str(payload.get("role") or "worker"),
            "status": str(payload.get("status") or "assigned"),
        }
    return assignments


def _normalized_workstream_status(
    item: dict[str, Any],
    assignment: dict[str, Any] | None,
) -> str:
    raw_status = str(item.get("status") or item.get("state") or "").strip().lower()
    raw_state = str(item.get("state") or "").strip().lower()
    status = raw_status or raw_state or "planned"
    aliases = {
        "pending": "planned",
        "queued": "planned",
        "in_progress": "running",
        "in-progress": "running",
        "started": "running",
        "done": "completed",
        "complete": "completed",
        "errored": "failed",
        "error": "failed",
    }
    status = aliases.get(status, status)
    if status == "planned" and assignment:
        return str(assignment.get("status") or "assigned")
    if status in {"assigned", "registered", "unknown"} and assignment:
        assignment_status = str(assignment.get("status") or "assigned").strip().lower()
        if assignment_status not in TERMINAL_AGENT_STATUSES:
            return assignment_status
    return status


def _assignment_record(
    *,
    workstream: str,
    agent_id: Any,
    role: Any,
    status: Any,
) -> dict[str, Any]:
    return {
        "workstream": workstream,
        "agent_id": agent_id,
        "role": role or "worker",
        "status": str(status or "assigned"),
    }


def _first_string(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _is_terminal_workstream_status(status: str) -> bool:
    return status in {"completed", "completed_with_concerns", "failed", "blocked", "cancelled"}


def _heartbeat_summary(agents: list[dict[str, Any]]) -> dict[str, int]:
    with_heartbeat = sum(1 for agent in agents if agent.get("last_heartbeat_at"))
    return {
        "total_agents": len(agents),
        "with_heartbeat": with_heartbeat,
        "missing_heartbeat": len(agents) - with_heartbeat,
    }


def _lifecycle_diagnostics(
    run_state_dir: Path,
    *,
    run: dict[str, Any],
    agents: list[dict[str, Any]],
    supervisors: list[dict[str, Any]],
    events: list[dict[str, Any]],
    pending_decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    diagnostics.extend(_stale_supervisor_diagnostics(supervisors))
    diagnostics.extend(_missing_launch_evidence_diagnostics(run_state_dir, agents))
    diagnostics.extend(_provider_native_no_report_diagnostics(run_state_dir, agents))
    diagnostics.extend(_stale_validation_evidence_diagnostics(run_state_dir, run, agents))
    diagnostics.extend(_orphaned_running_agent_diagnostics(run, agents, supervisors))
    stdout_diagnostic = _stdout_only_decision_diagnostic(
        run_state_dir,
        agents=agents,
        events=events,
        pending_decisions=pending_decisions,
    )
    if stdout_diagnostic is not None:
        diagnostics.append(stdout_diagnostic)
    report_diagnostic = _report_only_decision_diagnostic(
        run_state_dir,
        agents=agents,
        events=events,
        pending_decisions=pending_decisions,
    )
    if report_diagnostic is not None:
        diagnostics.append(report_diagnostic)
    return sorted(diagnostics, key=lambda item: (str(item.get("type")), str(item.get("agent_id", ""))))


def _missing_launch_evidence_diagnostics(
    run_state_dir: Path,
    agents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    diagnostics = []
    for agent in agents:
        if agent.get("role") not in {"worker", "reviewer", "validator"}:
            continue
        if agent.get("status") not in RUNNING_AGENT_STATUSES:
            continue
        launch_evidence = _launch_evidence_items(run_state_dir, agent)
        if launch_evidence:
            continue
        missing_fields, missing_file_fields = _missing_launch_evidence_fields(run_state_dir, agent)
        diagnostics.append(
            {
                "type": "missing_agent_launch_evidence",
                "severity": "material",
                "agent_id": agent.get("agent_id"),
                "role": agent.get("role"),
                "status": agent.get("status"),
                "workstream": agent.get("workstream"),
                "accepted_evidence_fields": list(LAUNCH_EVIDENCE_FIELDS),
                "missing_evidence_fields": missing_fields,
                "missing_file_evidence_fields": missing_file_fields,
                "summary": (
                    f"{agent.get('role')} {agent.get('agent_id')} is {agent.get('status')} "
                    "but has no provider-native launch evidence, positive pid, or existing stdout/stderr log file."
                ),
            }
        )
    return diagnostics


def _has_launch_evidence(run_state_dir: Path, agent: dict[str, Any]) -> bool:
    return bool(_launch_evidence_items(run_state_dir, agent))


def _launch_evidence_items(run_state_dir: Path, agent: dict[str, Any]) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for field, value in _provider_native_evidence_values(agent):
        evidence.append({"field": field, "kind": "provider_native", "value": value})

    pid = agent.get("pid")
    if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0:
        evidence.append({"field": "pid", "kind": "process", "value": str(pid)})
    for field in ("stdout_path", "stderr_path"):
        resolved = _resolve_run_path(run_state_dir, agent.get(field))
        if resolved is not None and resolved.exists():
            evidence.append(
                {
                    "field": field,
                    "kind": "file",
                    "value": _run_relative_existing_path(run_state_dir, resolved),
                }
            )
    return evidence


def _provider_native_evidence_values(agent: dict[str, Any]) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for field in ("provider_native_agent_id", "provider_native_spawn_ref"):
        value = agent.get(field)
        if isinstance(value, str) and value.strip():
            values.append((field, value.strip()))

    launch_evidence = agent.get("launch_evidence")
    if isinstance(launch_evidence, dict):
        for field in ("spawn_agent_id", "provider_native_spawn_ref"):
            value = launch_evidence.get(field)
            if isinstance(value, str) and value.strip():
                values.append((f"launch_evidence.{field}", value.strip()))

    provider_launch = agent.get("provider_launch")
    if isinstance(provider_launch, dict):
        evidence = provider_launch.get("evidence")
        if isinstance(evidence, dict):
            value = evidence.get("provider_native_spawn_ref")
            if isinstance(value, str) and value.strip():
                values.append(("provider_launch.evidence.provider_native_spawn_ref", value.strip()))
    return values


def _missing_launch_evidence_fields(
    run_state_dir: Path,
    agent: dict[str, Any],
) -> tuple[list[str], list[str]]:
    missing_fields = []
    present_provider_fields = {field for field, _value in _provider_native_evidence_values(agent)}
    for field in PROVIDER_NATIVE_LAUNCH_EVIDENCE_FIELDS:
        if field not in present_provider_fields:
            missing_fields.append(field)

    pid = agent.get("pid")
    if not (isinstance(pid, int) and not isinstance(pid, bool) and pid > 0):
        missing_fields.append("pid")

    missing_file_fields = []
    for field in ("stdout_path", "stderr_path"):
        resolved = _resolve_run_path(run_state_dir, agent.get(field))
        if resolved is None or not resolved.exists():
            missing_file_fields.append(field)
    return missing_fields, missing_file_fields


def _provider_native_no_report_diagnostics(
    run_state_dir: Path,
    agents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    diagnostics = []
    for agent in agents:
        if agent.get("role") not in {"worker", "reviewer", "validator"}:
            continue
        if agent.get("status") not in RUNNING_AGENT_STATUSES:
            continue
        provider_evidence = _provider_native_evidence_values(agent)
        if not provider_evidence:
            continue
        report_path = _agent_report_path(run_state_dir, agent)
        if report_path.exists():
            continue
        stale = _stale_agent_timestamp(agent)
        if stale is None:
            continue
        field, value, age_seconds = stale
        diagnostics.append(
            {
                "type": "provider_native_spawn_without_report",
                "severity": "material",
                "agent_id": agent.get("agent_id"),
                "role": agent.get("role"),
                "status": agent.get("status"),
                "workstream": agent.get("workstream"),
                "report_path": _run_relative_existing_path(run_state_dir, report_path),
                "evidence_fields": [field for field, _value in provider_evidence],
                "stale_since_field": field,
                "stale_since": value,
                "stale_after_seconds": PROVIDER_NATIVE_NO_REPORT_STALE_AFTER_SECONDS,
                "age_seconds": age_seconds,
                "summary": (
                    f"{agent.get('role')} {agent.get('agent_id')} has provider-native spawn evidence "
                    f"but no role-specific report after {field} became stale."
                ),
            }
        )
    return diagnostics


def _stale_validation_evidence_diagnostics(
    run_state_dir: Path,
    run: dict[str, Any],
    agents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    diagnostics = []
    for agent in agents:
        if agent.get("role") not in VALIDATION_EVIDENCE_ROLES:
            continue
        report_path = _agent_report_path(run_state_dir, agent)
        if report_path.exists():
            continue
        if _validation_evidence_cancelled(run, agent):
            diagnostics.append(_incomplete_validation_evidence_diagnostic(run_state_dir, run, agent, report_path))
            continue
        if agent.get("status") not in RUNNING_AGENT_STATUSES:
            continue
        stale = _stale_agent_timestamp(agent)
        if stale is None:
            continue
        diagnostics.append(_stale_validation_evidence_diagnostic(run_state_dir, agent, report_path, stale))
    return diagnostics


def _validation_evidence_cancelled(run: dict[str, Any], agent: dict[str, Any]) -> bool:
    return run.get("status") == "cancelled" or agent.get("status") == "cancelled"


def _stale_validation_evidence_diagnostic(
    run_state_dir: Path,
    agent: dict[str, Any],
    report_path: Path,
    stale: tuple[str, str, int],
) -> dict[str, Any]:
    field, value, age_seconds = stale
    role = str(agent.get("role") or "validator")
    return {
        "type": "stale_validation_worker_without_report",
        "severity": "material",
        "agent_id": agent.get("agent_id"),
        "role": role,
        "status": agent.get("status"),
        "workstream": agent.get("workstream"),
        "report_path": _run_relative_existing_path(run_state_dir, report_path),
        "stale_since_field": field,
        "stale_since": value,
        "stale_after_seconds": PROVIDER_NATIVE_NO_REPORT_STALE_AFTER_SECONDS,
        "age_seconds": age_seconds,
        "suggested_next_action": "inspect_wait_cancel_or_rerun_validation",
        "summary": (
            f"{role} {agent.get('agent_id')} has no fresh heartbeat and no role-specific "
            "terminal report, so validation evidence is incomplete."
        ),
    }


def _incomplete_validation_evidence_diagnostic(
    run_state_dir: Path,
    run: dict[str, Any],
    agent: dict[str, Any],
    report_path: Path,
) -> dict[str, Any]:
    role = str(agent.get("role") or "validator")
    terminal_reason = (
        agent.get("cancellation_reason")
        or run.get("cancellation_reason")
        or agent.get("failure_reason")
        or run.get("failure_reason")
    )
    diagnostic = {
        "type": "incomplete_validation_evidence",
        "severity": "material",
        "agent_id": agent.get("agent_id"),
        "role": role,
        "status": agent.get("status"),
        "workstream": agent.get("workstream"),
        "report_path": _run_relative_existing_path(run_state_dir, report_path),
        "run_status": run.get("status"),
        "suggested_next_action": "rerun_validation_or_record_blocked_validator_report",
        "summary": (
            f"{role} {agent.get('agent_id')} reached {agent.get('status')} "
            "without a role-specific terminal report."
        ),
    }
    if terminal_reason:
        diagnostic["terminal_reason"] = terminal_reason
    return diagnostic


def _stale_agent_timestamp(agent: dict[str, Any]) -> tuple[str, str, int] | None:
    for field in ("last_heartbeat_at", "updated_at", "started_at", "created_at"):
        value = agent.get(field)
        if not isinstance(value, str) or not value:
            continue
        parsed = _parse_utc_timestamp(value)
        if parsed is None:
            continue
        age_seconds = int((datetime.now(timezone.utc) - parsed).total_seconds())
        if age_seconds >= PROVIDER_NATIVE_NO_REPORT_STALE_AFTER_SECONDS:
            return field, value, age_seconds
        return None
    return None


def _parse_utc_timestamp(value: str) -> datetime | None:
    normalized = value
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _stale_supervisor_diagnostics(supervisors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    diagnostics = []
    for supervisor in supervisors:
        if supervisor.get("status") != "stale":
            continue
        pid = supervisor.get("supervisor_pid")
        reason = supervisor.get("stale_reason") or "supervisor_not_alive"
        diagnostics.append(
            {
                "type": "stale_detached_supervisor",
                "severity": "material",
                "agent_id": supervisor.get("agent_id"),
                "supervisor_pid": pid,
                "reason": reason,
                "summary": f"Detached supervisor for {supervisor.get('agent_id')} is stale ({reason}).",
            }
        )
    return diagnostics


def _orphaned_running_agent_diagnostics(
    run: dict[str, Any],
    agents: list[dict[str, Any]],
    supervisors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    coordinator = _first_coordinator(agents)
    coordinator_terminal = bool(coordinator and coordinator.get("status") in TERMINAL_AGENT_STATUSES)
    run_terminal = run.get("status") in TERMINAL_RUN_STATUSES
    if not (coordinator_terminal or run_terminal):
        return []
    if _has_active_supervisor(supervisors):
        return []

    diagnostics = []
    for agent in agents:
        if agent.get("role") == "coordinator":
            continue
        if agent.get("status") not in RUNNING_AGENT_STATUSES:
            continue
        diagnostic = {
            "type": "orphaned_running_agent",
            "severity": "material",
            "agent_id": agent.get("agent_id"),
            "role": agent.get("role"),
            "status": agent.get("status"),
            "summary": (
                f"{agent.get('role')} {agent.get('agent_id')} is still {agent.get('status')} "
                "after the coordinator/run reached a terminal state."
            ),
        }
        if agent.get("workstream"):
            diagnostic["workstream"] = agent["workstream"]
        diagnostics.append(diagnostic)
    return diagnostics


def _has_active_supervisor(supervisors: list[dict[str, Any]]) -> bool:
    return any(
        supervisor.get("status") == "running" and supervisor.get("process_alive") is True
        for supervisor in supervisors
    )


def _stdout_only_decision_diagnostic(
    run_state_dir: Path,
    *,
    agents: list[dict[str, Any]],
    events: list[dict[str, Any]],
    pending_decisions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if _has_durable_decision_evidence(events, pending_decisions):
        return None

    coordinator = _first_coordinator(agents)
    stdout_path = _coordinator_stdout_path(run_state_dir, coordinator)
    if stdout_path is None or not stdout_path.exists():
        return None

    matched_text = _stdout_decision_match(stdout_path)
    if matched_text is None:
        return None
    return {
        "type": "stdout_only_decision_request",
        "severity": "material",
        "agent_id": coordinator.get("agent_id") if coordinator else "coordinator-001",
        "stdout_path": _run_relative_existing_path(run_state_dir, stdout_path),
        "matched_text": matched_text,
        "summary": "Coordinator stdout appears to request a user decision, but no pending decision record or decision.requested event exists.",
    }


def _report_only_decision_diagnostic(
    run_state_dir: Path,
    *,
    agents: list[dict[str, Any]],
    events: list[dict[str, Any]],
    pending_decisions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if _has_durable_decision_evidence(events, pending_decisions):
        return None

    coordinator = _first_coordinator(agents)
    report_path = _coordinator_report_path(run_state_dir, coordinator)
    if report_path is None or not report_path.exists():
        return None

    report = _read_json_object(report_path)
    if not report:
        return None

    decisions_required = _report_decisions_required(report)
    if not decisions_required:
        return None

    decision_ids = [
        item["decision_id"]
        for item in decisions_required
        if item.get("decision_id")
    ]
    questions = [
        item["question"]
        for item in decisions_required
        if item.get("question")
    ]
    workstreams = sorted(
        {
            item["workstream"]
            for item in decisions_required
            if item.get("workstream")
        }
    )
    return {
        "type": "report_only_decision_request",
        "severity": "material",
        "agent_id": coordinator.get("agent_id") if coordinator else "coordinator-001",
        "report_path": _run_relative_existing_path(run_state_dir, report_path),
        "decisions_required_count": len(decisions_required),
        "decision_ids": decision_ids,
        "questions": questions,
        "workstreams": workstreams,
        "summary": "Coordinator report lists decisions_required, but no pending decision record or decision.requested event exists.",
    }


def _has_durable_decision_evidence(
    events: list[dict[str, Any]],
    pending_decisions: list[dict[str, Any]],
) -> bool:
    return bool(pending_decisions or any(event.get("type") == "decision.requested" for event in events))


def _coordinator_report_path(run_state_dir: Path, coordinator: dict[str, Any] | None) -> Path | None:
    if coordinator:
        return _agent_report_path(run_state_dir, coordinator)
    return run_state_dir / "reports" / "coordinator-001.json"


def _report_decisions_required(report: dict[str, Any]) -> list[dict[str, str]]:
    raw_decisions = report.get("decisions_required")
    if isinstance(raw_decisions, dict):
        raw_decisions = [raw_decisions]
    if not isinstance(raw_decisions, list):
        return []

    decisions = []
    for item in raw_decisions:
        record = _report_decision_required_item(item)
        if record:
            decisions.append(record)
    return decisions


def _report_decision_required_item(item: Any) -> dict[str, str] | None:
    if isinstance(item, str):
        question = item.strip()
        return {"question": question} if question else None
    if not isinstance(item, dict):
        return None

    record = {}
    decision_id = _first_string(item, "decision_id", "id")
    question = _first_string(item, "question", "prompt", "summary")
    workstream = _first_string(item, "workstream", "workstream_id", "blocking_workstream")
    if decision_id:
        record["decision_id"] = decision_id
    if question:
        record["question"] = question
    if workstream:
        record["workstream"] = workstream
    return record or None


def _coordinator_stdout_path(run_state_dir: Path, coordinator: dict[str, Any] | None) -> Path | None:
    if coordinator:
        stdout_path = coordinator.get("stdout_path")
        resolved = _resolve_run_path(run_state_dir, stdout_path)
        if resolved is not None:
            return resolved
    default_path = run_state_dir / "logs" / "coordinator-001.stdout.log"
    return default_path


def _resolve_run_path(run_state_dir: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    prefix = f".dispatch/runs/{run_state_dir.name}/"
    if value.startswith(prefix):
        return run_state_dir / value.removeprefix(prefix)
    path = Path(value)
    if path.is_absolute():
        return path
    return run_state_dir / path


def _run_relative_existing_path(run_state_dir: Path, path: Path) -> str:
    try:
        return f".dispatch/runs/{run_state_dir.name}/{path.relative_to(run_state_dir)}"
    except ValueError:
        return str(path)


def _stdout_decision_match(stdout_path: Path) -> str | None:
    try:
        text = stdout_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        normalized = line.lower()
        if any(pattern in normalized for pattern in STDOUT_DECISION_PATTERNS):
            return line.strip()[:240]
    return None


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
    path = _agent_report_path(run_state_dir, agent)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _agent_report_path(run_state_dir: Path, agent: dict[str, Any]) -> Path:
    report_path = agent.get("report_path")
    prefix = f".dispatch/runs/{run_state_dir.name}/"
    if isinstance(report_path, str) and report_path.startswith(prefix):
        return run_state_dir / report_path.removeprefix(prefix)
    resolved = _resolve_run_path(run_state_dir, report_path)
    if resolved is not None:
        return resolved
    role = agent.get("role")
    directory = {"reviewer": "reviews", "validator": "validation"}.get(str(role), "reports")
    return run_state_dir / directory / f"{agent.get('agent_id')}.json"


def _workstream_progress(
    workstreams: list[dict[str, Any]],
    assignments: list[dict[str, Any]],
) -> dict[str, int]:
    assigned_workstreams = {item["workstream"] for item in assignments}
    statuses = Counter(str(item.get("status") or "unknown") for item in workstreams)
    unassigned = sum(
        1
        for item in workstreams
        if item.get("id") not in assigned_workstreams
        and item.get("status", "unknown") in {"planned", "queued", "unknown"}
    )
    return {
        "planned": statuses.get("planned", 0),
        "assigned": statuses.get("assigned", 0),
        "running": statuses.get("running", 0) + statuses.get("registered", 0),
        "completed": statuses.get("completed", 0),
        "failed": statuses.get("failed", 0),
        "blocked": statuses.get("blocked", 0),
        "cancelled": statuses.get("cancelled", 0),
        "unassigned": unassigned,
    }


def _protocol_violation_summary(run_state_dir: Path, events: list[dict[str, Any]]) -> dict[str, Any]:
    event_violations = [event_protocol_violation(event) for event in events if event.get("type") == "protocol.violation"]
    detected_violations = detect_protocol_violations(run_state_dir)
    unique = unique_protocol_violations([*event_violations, *detected_violations])
    overlay = protocol_resolution_overlay(run_state_dir, unique)
    unresolved_keys = {
        json.dumps(violation, sort_keys=True)
        for violation in overlay["unresolved"]
    }
    resolution_summary = {
        "count": overlay["count"],
        "matched_count": overlay["matched_count"],
        "records": overlay["records"],
        "unmatched": overlay["unmatched"],
    }
    return {
        "count": len(unique),
        "event_count": len(event_violations),
        "detected_count": len(detected_violations),
        "detected": detected_violations,
        "unresolved_detected": [
            violation
            for violation in detected_violations
            if json.dumps(violation, sort_keys=True) in unresolved_keys
        ],
        "resolved_count": overlay["resolved_count"],
        "unresolved_count": overlay["unresolved_count"],
        "resolved": overlay["resolved"],
        "unresolved": overlay["unresolved"],
        "resolution_summary": resolution_summary,
        "resolutions": overlay["records"],
    }


def _material_alerts(
    *,
    run_id: str,
    run: dict[str, Any],
    pending_decisions: list[dict[str, Any]],
    unresolved_blockers: list[dict[str, Any]],
    protocol_violations: list[dict[str, Any]],
    agents: list[dict[str, Any]],
    lifecycle_diagnostics: list[dict[str, Any]],
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

    for diagnostic in lifecycle_diagnostics:
        alert = {
            "type": diagnostic.get("type", "lifecycle_diagnostic"),
            "run_id": run_id,
            "severity": diagnostic.get("severity", "material"),
            "summary": diagnostic.get("summary", ""),
        }
        for field in (
            "agent_id",
            "role",
            "status",
            "workstream",
            "supervisor_pid",
            "reason",
            "stdout_path",
            "matched_text",
            "report_path",
            "decisions_required_count",
            "decision_ids",
            "questions",
            "workstreams",
            "evidence_fields",
            "stale_since_field",
            "stale_since",
            "stale_after_seconds",
            "run_status",
            "terminal_reason",
            "suggested_next_action",
        ):
            if diagnostic.get(field) is not None:
                alert[field] = diagnostic[field]
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
