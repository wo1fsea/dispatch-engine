"""Durable agent registry helpers for Dispatch Engine runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .events import (
    agent_completed,
    agent_failed,
    agent_heartbeat,
    agent_spawned,
    protocol_violation,
    utc_timestamp,
    workstream_assigned,
)

AGENT_SCHEMA_VERSION = 1
ROLES = frozenset({"coordinator", "worker", "reviewer", "validator"})
PROVIDERS = frozenset({"codex", "claude"})
IMPLEMENTATION_ROLES = frozenset({"worker", "reviewer", "validator"})
IMPLEMENTED_WORKSTREAM_STATUSES = frozenset({"implemented", "completed", "accepted"})
COORDINATOR_WRITE_ROOTS = [".dispatch/"]
WORKER_REPORT_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "agent_id",
        "role",
        "workstream",
        "status",
        "summary",
        "changed_files",
        "validation",
        "questions",
        "blockers",
        "risks",
    }
)
WORKER_REPORT_STATUSES = frozenset({"completed", "completed_with_concerns", "blocked", "failed"})
REVIEWER_REPORT_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "agent_id",
        "role",
        "workstream",
        "status",
        "summary",
        "findings",
        "risks",
        "requested_changes",
        "validation_gaps",
        "recommendation",
    }
)
REVIEWER_REPORT_STATUSES = frozenset({"accepted", "changes_requested", "blocked", "failed"})
VALIDATOR_REPORT_REQUIRED_FIELDS = frozenset(
    {
        "schema_version",
        "agent_id",
        "role",
        "workstream",
        "status",
        "summary",
        "command",
        "output_summary",
        "artifacts",
        "not_run_reason",
    }
)
VALIDATOR_REPORT_STATUSES = frozenset({"passed", "failed", "blocked", "skipped"})
REPORT_DIR_BY_ROLE = {
    "reviewer": "reviews",
    "validator": "validation",
}


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
    prompt_path: str | None = None,
    stdout_path: str | None = None,
    stderr_path: str | None = None,
    pid: int | None = None,
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
        "report_path": report_path or _run_relative_path(
            run_state_dir,
            _report_directory(role),
            agent_id,
            ".json",
        ),
        "log_path": log_path or _run_relative_path(run_state_dir, "logs", agent_id, ".jsonl"),
    }
    if prompt_path is not None:
        record["prompt_path"] = prompt_path
    if stdout_path is not None:
        record["stdout_path"] = stdout_path
    if stderr_path is not None:
        record["stderr_path"] = stderr_path
    if pid is not None:
        record["pid"] = pid
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


def register_worker_agent(
    run_state_dir: Path,
    *,
    agent_id: str,
    provider: str,
    profile: str,
    workstream: str,
    assigned_files: list[str] | None = None,
    allowed_write_roots: list[str] | None = None,
    status: str = "registered",
) -> dict[str, Any]:
    """Register a worker and emit assignment lifecycle events."""

    agent = register_agent(
        run_state_dir,
        agent_id=agent_id,
        role="worker",
        provider=provider,
        profile=profile,
        status=status,
        workstream=workstream,
        assigned_files=assigned_files,
        allowed_write_roots=allowed_write_roots,
        prompt_path=_run_relative_path(run_state_dir, "prompts", agent_id, ".md"),
        stdout_path=_run_relative_path(run_state_dir, "logs", agent_id, ".stdout.log"),
        stderr_path=_run_relative_path(run_state_dir, "logs", agent_id, ".stderr.log"),
    )
    agent_spawned(
        run_state_dir / "events.jsonl",
        agent_id=agent_id,
        role="worker",
        provider=provider,
        profile=profile,
        workstream=workstream,
    )
    workstream_assigned(run_state_dir / "events.jsonl", agent_id=agent_id, workstream=workstream)
    return agent


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
        report_record.setdefault("role", agent.get("role"))
        report_record.setdefault("run_id", run_state_dir.name)
        report_record.setdefault("completed_at", now)
        _report_path(run_state_dir, agent).write_text(
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


def write_worker_report(
    run_state_dir: Path,
    agent_id: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Write a worker report with stable runtime defaults."""

    agent = _require_agent(run_state_dir, agent_id)
    if agent.get("role") != "worker":
        raise AgentValidationError(f"agent is not a worker: {agent_id}")

    now = utc_timestamp()
    report_record = dict(report)
    report_record.setdefault("schema_version", AGENT_SCHEMA_VERSION)
    report_record.setdefault("agent_id", agent_id)
    report_record.setdefault("role", agent.get("role"))
    report_record.setdefault("run_id", run_state_dir.name)
    report_record.setdefault("workstream", agent.get("workstream"))
    report_record.setdefault("completed_at", now)
    _ensure_runtime_dirs(run_state_dir)
    _report_path(run_state_dir, agent).write_text(
        json.dumps(report_record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_record


def write_reviewer_report(
    run_state_dir: Path,
    agent_id: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Write a reviewer report with stable runtime defaults."""

    return _write_role_report(run_state_dir, agent_id, report, expected_role="reviewer")


def write_validator_report(
    run_state_dir: Path,
    agent_id: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Write a validator report with stable runtime defaults."""

    return _write_role_report(run_state_dir, agent_id, report, expected_role="validator")


def complete_worker(
    run_state_dir: Path,
    agent_id: str,
    *,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Write a worker report and mark the worker completed."""

    write_worker_report(run_state_dir, agent_id, report)
    return complete_agent(run_state_dir, agent_id)


def fail_worker(run_state_dir: Path, agent_id: str, *, reason: str) -> dict[str, Any]:
    """Mark a worker failed."""

    return fail_agent(run_state_dir, agent_id, reason=reason)


def validate_worker_report(run_state_dir: Path, agent_id: str) -> list[dict[str, Any]]:
    """Return protocol violations for a worker report, without mutating state."""

    agent = _require_agent(run_state_dir, agent_id)
    if agent.get("role") != "worker":
        return []

    report_path = _report_path(run_state_dir, agent)
    if not report_path.exists():
        return [
            _report_violation(
                "missing_worker_report",
                agent,
                {"report_path": agent.get("report_path")},
            )
        ]

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [
            _report_violation(
                "malformed_worker_report",
                agent,
                {"report_path": agent.get("report_path"), "reason": str(exc)},
            )
        ]

    violations: list[dict[str, Any]] = []
    missing = sorted(WORKER_REPORT_REQUIRED_FIELDS - set(report))
    malformed_details: dict[str, Any] = {}
    if missing:
        malformed_details["missing_fields"] = missing
    if report.get("agent_id") != agent_id:
        malformed_details["agent_id"] = report.get("agent_id")
    if report.get("role") != agent.get("role"):
        malformed_details["role"] = report.get("role")
    if report.get("workstream") != agent.get("workstream"):
        malformed_details["workstream"] = report.get("workstream")
    if report.get("status") not in WORKER_REPORT_STATUSES:
        malformed_details["status"] = report.get("status")
    for field in ("changed_files", "validation", "questions", "blockers", "risks"):
        if field in report and not isinstance(report[field], list):
            malformed_details[field] = type(report[field]).__name__
    if malformed_details:
        violations.append(_report_violation("malformed_worker_report", agent, malformed_details))

    changed_files = report.get("changed_files")
    if isinstance(changed_files, list):
        out_of_scope = [
            path
            for path in changed_files
            if isinstance(path, str) and not _path_allowed(path, agent)
        ]
        if out_of_scope:
            violations.append(
                _report_violation(
                    "out_of_scope_changed_file",
                    agent,
                    {
                        "changed_files": out_of_scope,
                        "assigned_files": agent.get("assigned_files", []),
                        "allowed_write_roots": agent.get("allowed_write_roots", []),
                    },
                )
            )
    return violations


def validate_review_validator_report(run_state_dir: Path, agent_id: str) -> list[dict[str, Any]]:
    """Return protocol violations for a reviewer or validator report."""

    agent = _require_agent(run_state_dir, agent_id)
    role = agent.get("role")
    if role == "reviewer":
        return _validate_role_report(
            run_state_dir,
            agent,
            required_fields=REVIEWER_REPORT_REQUIRED_FIELDS,
            allowed_statuses=REVIEWER_REPORT_STATUSES,
            list_fields=("findings", "risks", "requested_changes", "validation_gaps"),
        )
    if role == "validator":
        violations = _validate_role_report(
            run_state_dir,
            agent,
            required_fields=VALIDATOR_REPORT_REQUIRED_FIELDS,
            allowed_statuses=VALIDATOR_REPORT_STATUSES,
            list_fields=("artifacts",),
        )
        if violations:
            return violations
        report = json.loads(_report_path(run_state_dir, agent).read_text(encoding="utf-8"))
        missing_evidence = []
        status = report.get("status")
        if status == "skipped":
            if not _has_text(report.get("not_run_reason")):
                missing_evidence.append("not_run_reason")
        else:
            if not _has_text(report.get("command")):
                missing_evidence.append("command")
            if not _has_text(report.get("output_summary")):
                missing_evidence.append("output_summary")
            artifacts = report.get("artifacts")
            if not isinstance(artifacts, list) or not artifacts:
                missing_evidence.append("artifacts")
        if missing_evidence:
            return [
                _report_violation(
                    "missing_validation_evidence",
                    agent,
                    {"missing_fields": sorted(missing_evidence)},
                )
            ]
        return []
    return []


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

    valid_implementation_workstreams = set()
    for agent in agents:
        if agent.get("role") not in IMPLEMENTATION_ROLES:
            continue
        if agent.get("status") == "completed":
            if agent.get("role") == "worker":
                worker_violations = validate_worker_report(run_state_dir, agent["agent_id"])
            else:
                worker_violations = validate_review_validator_report(run_state_dir, agent["agent_id"])
            violations.extend(worker_violations)
            if not worker_violations and agent.get("workstream"):
                valid_implementation_workstreams.add(agent.get("workstream"))

    for path in sorted((run_state_dir / "workstreams").glob("*.json")):
        workstream = json.loads(path.read_text(encoding="utf-8"))
        workstream_id = workstream.get("id", path.stem)
        if (
            workstream.get("status") in IMPLEMENTED_WORKSTREAM_STATUSES
            and workstream_id not in valid_implementation_workstreams
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
    for name in ("agents", "reports", "reviews", "validation", "logs", "prompts", "heartbeats"):
        (run_state_dir / name).mkdir(exist_ok=True)
    event_log = run_state_dir / "events.jsonl"
    if not event_log.exists():
        event_log.write_text("", encoding="utf-8")


def _run_relative_path(run_state_dir: Path, directory: str, agent_id: str, suffix: str) -> str:
    return f".dispatch/runs/{run_state_dir.name}/{directory}/{agent_id}{suffix}"


def _report_directory(role: str | None) -> str:
    return REPORT_DIR_BY_ROLE.get(str(role), "reports")


def _report_path(run_state_dir: Path, agent: dict[str, Any]) -> Path:
    report_path = agent.get("report_path") or _run_relative_path(
        run_state_dir,
        _report_directory(agent.get("role")),
        agent["agent_id"],
        ".json",
    )
    prefix = f".dispatch/runs/{run_state_dir.name}/"
    if isinstance(report_path, str) and report_path.startswith(prefix):
        return run_state_dir / report_path.removeprefix(prefix)
    return run_state_dir / _report_directory(agent.get("role")) / f"{agent['agent_id']}.json"


def _write_role_report(
    run_state_dir: Path,
    agent_id: str,
    report: dict[str, Any],
    *,
    expected_role: str,
) -> dict[str, Any]:
    agent = _require_agent(run_state_dir, agent_id)
    if agent.get("role") != expected_role:
        raise AgentValidationError(f"agent is not a {expected_role}: {agent_id}")

    now = utc_timestamp()
    report_record = dict(report)
    report_record.setdefault("schema_version", AGENT_SCHEMA_VERSION)
    report_record.setdefault("agent_id", agent_id)
    report_record.setdefault("role", expected_role)
    report_record.setdefault("run_id", run_state_dir.name)
    report_record.setdefault("workstream", agent.get("workstream"))
    report_record.setdefault("completed_at", now)
    _ensure_runtime_dirs(run_state_dir)
    _report_path(run_state_dir, agent).write_text(
        json.dumps(report_record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report_record


def _validate_role_report(
    run_state_dir: Path,
    agent: dict[str, Any],
    *,
    required_fields: frozenset[str],
    allowed_statuses: frozenset[str],
    list_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    role = str(agent.get("role"))
    report_path = _report_path(run_state_dir, agent)
    if not report_path.exists():
        return [
            _report_violation(
                f"missing_{role}_report",
                agent,
                {"report_path": agent.get("report_path")},
            )
        ]

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [
            _report_violation(
                f"malformed_{role}_report",
                agent,
                {"report_path": agent.get("report_path"), "reason": str(exc)},
            )
        ]

    malformed_details: dict[str, Any] = {}
    missing = sorted(required_fields - set(report))
    if missing:
        malformed_details["missing_fields"] = missing
    if report.get("agent_id") != agent.get("agent_id"):
        malformed_details["agent_id"] = report.get("agent_id")
    if report.get("role") != role:
        malformed_details["role"] = report.get("role")
    if report.get("workstream") != agent.get("workstream"):
        malformed_details["workstream"] = report.get("workstream")
    if report.get("status") not in allowed_statuses:
        malformed_details["status"] = report.get("status")
    for field in list_fields:
        if field in report and not isinstance(report[field], list):
            malformed_details[field] = type(report[field]).__name__
    if malformed_details:
        return [_report_violation(f"malformed_{role}_report", agent, malformed_details)]
    return []


def _report_violation(
    violation: str,
    agent: dict[str, Any],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "violation": violation,
        "agent_id": agent.get("agent_id"),
        "workstream": agent.get("workstream"),
        "details": details,
    }


def _path_allowed(path: str, agent: dict[str, Any]) -> bool:
    normalized = path.removeprefix("./")
    assigned_files = {item.removeprefix("./") for item in agent.get("assigned_files", [])}
    if normalized in assigned_files:
        return True
    for root in agent.get("allowed_write_roots", []):
        normalized_root = root.removeprefix("./").rstrip("/")
        if normalized_root and (
            normalized == normalized_root or normalized.startswith(f"{normalized_root}/")
        ):
            return True
    return False


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_agent_id(agent_id: str) -> None:
    if not agent_id or "/" in agent_id or "\\" in agent_id:
        raise AgentValidationError(f"invalid agent_id: {agent_id!r}")


def _validate_role(role: str) -> None:
    if role not in ROLES:
        raise AgentValidationError(f"unsupported role: {role}")


def _validate_provider(provider: str) -> None:
    if provider not in PROVIDERS:
        raise AgentValidationError(f"unsupported provider: {provider}")
