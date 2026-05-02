"""Append-only event helpers for Dispatch Engine."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_event(
    event_log: Path,
    event_type: str,
    *,
    actor: str = "dispatch-engine",
    workstream: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    event = {
        "ts": utc_timestamp(),
        "type": event_type,
        "actor": actor,
        "payload": payload or {},
    }
    if workstream:
        event["workstream"] = workstream
    with event_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def coordinator_started(
    event_log: Path,
    *,
    agent_id: str,
    provider: str,
    profile: str,
    actor: str = "dispatch-engine",
) -> None:
    append_event(
        event_log,
        "coordinator.started",
        actor=actor,
        payload={"agent_id": agent_id, "provider": provider, "profile": profile},
    )


def coordinator_completed(
    event_log: Path,
    *,
    agent_id: str,
    provider: str,
    profile: str,
    exit_code: int,
    stdout_path: str,
    stderr_path: str,
    actor: str = "dispatch-engine",
) -> None:
    append_event(
        event_log,
        "coordinator.completed",
        actor=actor,
        payload={
            "agent_id": agent_id,
            "provider": provider,
            "profile": profile,
            "exit_code": exit_code,
            "stdout_path": stdout_path,
            "stderr_path": stderr_path,
        },
    )


def coordinator_failed(
    event_log: Path,
    *,
    agent_id: str,
    provider: str,
    profile: str,
    exit_code: int | None,
    stdout_path: str,
    stderr_path: str,
    reason: str,
    actor: str = "dispatch-engine",
) -> None:
    append_event(
        event_log,
        "coordinator.failed",
        actor=actor,
        payload={
            "agent_id": agent_id,
            "provider": provider,
            "profile": profile,
            "exit_code": exit_code,
            "stdout_path": stdout_path,
            "stderr_path": stderr_path,
            "reason": reason,
        },
    )


def agent_spawned(
    event_log: Path,
    *,
    agent_id: str,
    role: str,
    provider: str,
    profile: str,
    workstream: str | None = None,
    actor: str = "dispatch-engine",
) -> None:
    append_event(
        event_log,
        "agent.spawned",
        actor=actor,
        workstream=workstream,
        payload={
            "agent_id": agent_id,
            "role": role,
            "provider": provider,
            "profile": profile,
        },
    )


def agent_heartbeat(
    event_log: Path,
    *,
    agent_id: str,
    status: str,
    workstream: str | None = None,
    actor: str = "dispatch-engine",
) -> None:
    append_event(
        event_log,
        "agent.heartbeat",
        actor=actor,
        workstream=workstream,
        payload={"agent_id": agent_id, "status": status},
    )


def workstream_assigned(
    event_log: Path,
    *,
    agent_id: str,
    workstream: str,
    actor: str = "dispatch-engine",
) -> None:
    append_event(
        event_log,
        "workstream.assigned",
        actor=actor,
        workstream=workstream,
        payload={"agent_id": agent_id},
    )


def agent_completed(
    event_log: Path,
    *,
    agent_id: str,
    report_path: str | None = None,
    workstream: str | None = None,
    actor: str = "dispatch-engine",
) -> None:
    payload = {"agent_id": agent_id}
    if report_path is not None:
        payload["report_path"] = report_path
    append_event(
        event_log,
        "agent.completed",
        actor=actor,
        workstream=workstream,
        payload=payload,
    )


def agent_failed(
    event_log: Path,
    *,
    agent_id: str,
    reason: str,
    workstream: str | None = None,
    actor: str = "dispatch-engine",
) -> None:
    append_event(
        event_log,
        "agent.failed",
        actor=actor,
        workstream=workstream,
        payload={"agent_id": agent_id, "reason": reason},
    )


def protocol_violation(
    event_log: Path,
    *,
    violation: str,
    details: dict[str, Any],
    workstream: str | None = None,
    actor: str = "dispatch-engine",
) -> None:
    append_event(
        event_log,
        "protocol.violation",
        actor=actor,
        workstream=workstream,
        payload={"violation": violation, "details": details},
    )


def decision_requested(
    event_log: Path,
    *,
    decision_id: str,
    question: str,
    reason: str | None = None,
    workstream: str | None = None,
    actor: str = "dispatch-engine",
) -> None:
    payload = {"decision_id": decision_id, "question": question}
    if reason is not None:
        payload["reason"] = reason
    append_event(
        event_log,
        "decision.requested",
        actor=actor,
        workstream=workstream,
        payload=payload,
    )


def read_events(event_log: Path) -> list[dict[str, Any]]:
    if not event_log.exists():
        return []
    events = []
    for line in event_log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        events.append(json.loads(line))
    return events
