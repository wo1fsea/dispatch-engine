"""Durable agent registry helpers for Dispatch Engine runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .events import agent_completed, agent_failed, agent_heartbeat, protocol_violation, utc_timestamp

AGENT_SCHEMA_VERSION = 1
ROLES = frozenset({"coordinator", "worker", "reviewer", "validator"})
PROVIDERS = frozenset({"codex", "claude"})
IMPLEMENTATION_ROLES = frozenset({"worker", "reviewer", "validator"})
IMPLEMENTED_WORKSTREAM_STATUSES = frozenset({"implemented", "completed"})
COORDINATOR_WRITE_ROOTS = [".dispatch/"]


class AgentValidationError(ValueError):
    """Raised when an agent registry record is invalid."""


def register_agent(
    run_state_dir: Path,
    *,
    agent_id: str,
    role: str,
    provider: str,
    profile: str,
    status: str = "registered",
    workstream: str | None = None,
    assigned_files: list[str] | None = None,
    allowed_write_roots: list[str] | None = None,
    created_at: str | None = None,
    started_at: str | None = None,
    last_heartbeat_at: str | None = None,
    completed_at: str | None = None,
    report_path: str | None = None,
    log_path: str | None = None,
) -> dict[str, Any]:
    """Write a durable agent registry record under agents/<agent-id>.json."""

    _validate_agent_id(agent_id)
    _validate_role(role)
    _validate_provider(provider)
    if role == "coordinator" and allowed_write_roots is None:
        allowed_write_roots = list(COORDINATOR_WRITE_ROOTS)

    now = utc_timestamp()
    created = created_at or now
    started = started_at or created
    record = {
        "schema_version": AGENT_SCHEMA_VERSION,
        "agent_id": agent_id,
        "role": role,
        "provider": provider,
        "profile": profile,
        "status": status,
        "run_id": run_state_dir.name,
        "workstream": workstream,
        "assigned_files": list(assigned_files or []),
        "allowed_write_roots": list(allowed_write_roots or []),
        "created_at": created,
        "started_at": started,
        "updated_at": now,
        "last_heartbeat_at": last_heartbeat_at,
        "completed_at": completed_at,
        "report_path": report_path or _run_relative_path(run_state_dir, "reports", agent_id, ".json"),
        "log_path": log_path or _run_relative_path(run_state_dir, "logs", agent_id, ".jsonl"),
    }
    _write_agent(run_state_dir, record)
    return record


def read_agent(run_state_dir: Path, agent_id: str) -> dict[str, Any] | None:
    path = _agent_path(run_state_dir, agent_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_agents(run_state_dir: Path) -> list[dict[str, Any]]:
    agents_dir = run_state_dir / "agents"
    if not agents_dir.exists():
        return []
    agents = []
    for path in sorted(agents_dir.glob("*.json")):
        agents.append(json.loads(path.read_text(encoding="utf-8")))
    return agents


def append_agent_heartbeat(
    run_state_dir: Path,
    agent_id: str,
    *,
    status: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    agent = _require_agent(run_state_dir, agent_id)
    now = utc_timestamp()
    heartbeat = {
        "ts": now,
        "agent_id": agent_id,
        "run_id": run_state_dir.name,
        "status": status or agent["status"],
        "payload": payload or {},
    }
    _ensure_runtime_dirs(run_state_dir)
    with (run_state_dir / "heartbeats" / f"{agent_id}.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(heartbeat, sort_keys=True) + "\n")
    agent["status"] = heartbeat["status"]
    agent["last_heartbeat_at"] = now
    agent["updated_at"] = now
    _write_agent(run_state_dir, agent)
    agent_heartbeat(
        run_state_dir / "events.jsonl",
        agent_id=agent_id,
        status=agent["status"],
        workstream=agent.get("workstream"),
    )
    return heartbeat


def complete_agent(
    run_state_dir: Path,
    agent_id: str,
    *,
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    agent = _require_agent(run_state_dir, agent_id)
    now = utc_timestamp()
    agent["status"] = "completed"
    agent["updated_at"] = now
    agent["completed_at"] = now
    _ensure_runtime_dirs(run_state_dir)
    if report is not None:
        report_record = dict(report)
        report_record.setdefault("agent_id", agent_id)
        report_record.setdefault("run_id", run_state_dir.name)
        report_record.setdefault("completed_at", now)
        (run_state_dir / "reports" / f"{agent_id}.json").write_text(
            json.dumps(report_record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    _write_agent(run_state_dir, agent)
    agent_completed(
        run_state_dir / "events.jsonl",
        agent_id=agent_id,
        report_path=agent.get("report_path"),
        workstream=agent.get("workstream"),
    )
    return agent


def fail_agent(run_state_dir: Path, agent_id: str, *, reason: str) -> dict[str, Any]:
    agent = _require_agent(run_state_dir, agent_id)
    now = utc_timestamp()
    agent["status"] = "failed"
    agent["updated_at"] = now
    agent["completed_at"] = now
    agent["failure_reason"] = reason
    _write_agent(run_state_dir, agent)
    agent_failed(
        run_state_dir / "events.jsonl",
        agent_id=agent_id,
        reason=reason,
        workstream=agent.get("workstream"),
    )
    return agent


def detect_protocol_violations(run_state_dir: Path) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    agents = list_agents(run_state_dir)
    for agent in agents:
        if agent.get("role") != "coordinator":
            continue
        assigned_files = list(agent.get("assigned_files", []))
        allowed_write_roots = list(agent.get("allowed_write_roots", []))
        if assigned_files or allowed_write_roots != COORDINATOR_WRITE_ROOTS:
            violations.append(
                {
                    "violation": "coordinator_project_file_scope",
                    "agent_id": agent.get("agent_id"),
                    "details": {
                        "assigned_files": assigned_files,
                        "allowed_write_roots": allowed_write_roots,
                    },
                }
            )

    implementation_workstreams = {
        agent.get("workstream")
        for agent in agents
        if agent.get("role") in IMPLEMENTATION_ROLES and agent.get("workstream")
    }
    for path in sorted((run_state_dir / "workstreams").glob("*.json")):
        workstream = json.loads(path.read_text(encoding="utf-8"))
        workstream_id = workstream.get("id", path.stem)
        if (
            workstream.get("status") in IMPLEMENTED_WORKSTREAM_STATUSES
            and workstream_id not in implementation_workstreams
        ):
            violations.append(
                {
                    "violation": "unregistered_implementation_completion",
                    "workstream": workstream_id,
                    "details": {"status": workstream.get("status")},
                }
            )
    return violations


def record_protocol_violations(run_state_dir: Path) -> list[dict[str, Any]]:
    violations = detect_protocol_violations(run_state_dir)
    event_log = run_state_dir / "events.jsonl"
    for violation in violations:
        protocol_violation(
            event_log,
            violation=violation["violation"],
            details=violation["details"],
            workstream=violation.get("workstream"),
        )
    return violations


def _write_agent(run_state_dir: Path, agent: dict[str, Any]) -> None:
    _ensure_runtime_dirs(run_state_dir)
    _agent_path(run_state_dir, agent["agent_id"]).write_text(
        json.dumps(agent, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _agent_path(run_state_dir: Path, agent_id: str) -> Path:
    return run_state_dir / "agents" / f"{agent_id}.json"


def _require_agent(run_state_dir: Path, agent_id: str) -> dict[str, Any]:
    agent = read_agent(run_state_dir, agent_id)
    if agent is None:
        raise AgentValidationError(f"agent not found: {agent_id}")
    return agent


def _ensure_runtime_dirs(run_state_dir: Path) -> None:
    for name in ("agents", "reports", "logs", "heartbeats"):
        (run_state_dir / name).mkdir(exist_ok=True)
    event_log = run_state_dir / "events.jsonl"
    if not event_log.exists():
        event_log.write_text("", encoding="utf-8")


def _run_relative_path(run_state_dir: Path, directory: str, agent_id: str, suffix: str) -> str:
    return f".dispatch/runs/{run_state_dir.name}/{directory}/{agent_id}{suffix}"


def _validate_agent_id(agent_id: str) -> None:
    if not agent_id or "/" in agent_id or "\\" in agent_id:
        raise AgentValidationError(f"invalid agent_id: {agent_id!r}")


def _validate_role(role: str) -> None:
    if role not in ROLES:
        raise AgentValidationError(f"unsupported role: {role}")


def _validate_provider(provider: str) -> None:
    if provider not in PROVIDERS:
        raise AgentValidationError(f"unsupported provider: {provider}")
