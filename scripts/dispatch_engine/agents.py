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
    capability_profile_granted,
    capability_violation,
    protocol_violation,
    utc_timestamp,
    workstream_assigned,
)

AGENT_SCHEMA_VERSION = 1
ROLES = frozenset({"coordinator", "worker", "reviewer", "validator"})
PROVIDERS = frozenset({"codex", "claude"})
IMPLEMENTATION_ROLES = frozenset({"worker", "reviewer", "validator"})
COMPLETED_IMPLEMENTATION_AGENT_STATUSES = frozenset({"completed", "completed_with_concerns"})
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
WORKER_REPORT_LEGACY_ALIASES = {
    "files_changed": "changed_files",
    "checks": "validation",
    "validation_run": "validation",
    "conflicts_or_blockers": "blockers",
    "residual_risk": "risks",
    "open_questions": "questions",
    "capability_profile": "capability_profile_id",
    "capabilities_used": "capabilities_exercised",
}
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
        "artifacts",
    }
)
VALIDATOR_REPORT_STATUS_ORDER = ("passed", "failed", "blocked", "skipped")
VALIDATOR_REPORT_STATUSES = frozenset(VALIDATOR_REPORT_STATUS_ORDER)
VALIDATOR_REPORT_COMPAT_STATUS = "completed"
VALIDATOR_REPORT_SCHEMA_VIOLATIONS = frozenset(
    {
        "missing_validator_report",
        "malformed_validator_json",
        "missing_validator_fields",
        "invalid_validator_field_type",
        "invalid_validator_status",
        "missing_validation_evidence",
        "inconsistent_validation_evidence",
        "validator_identity_mismatch",
    }
)
REPORT_DIR_BY_ROLE = {
    "reviewer": "reviews",
    "validator": "validation",
}
CAPABILITY_PROFILE_SCHEMA_VERSION = 1
CAPABILITY_MODE_ORDER = {
    "network_access": ("none", "read-only-public", "allow-listed-hosts", "unrestricted"),
    "package_install": ("deny", "allow-dev-dependencies", "allow-project-manager", "unrestricted"),
    "dependency_resolution": ("deny", "allow-existing-lockfiles", "allow-lockfile-update", "unrestricted"),
    "docker_socket": ("deny", "read-only", "build", "unrestricted"),
    "service_start": ("deny", "local-only", "allow-listed", "unrestricted"),
    "test_execution": ("deny", "allow-listed", "allow-project-tests", "unrestricted"),
    "runtime_state_write": ("none", "report-only", "agent-heartbeat", "coordinator"),
    "github_issue_create": ("deny", "draft-only", "allow-dispatch-engine", "unrestricted"),
}
CAPABILITY_KEYS = frozenset(CAPABILITY_MODE_ORDER)
PROFILE_DEFAULT_BY_ROLE = {
    "coordinator": "coordinator-baseline",
    "worker": "worker-standard",
    "reviewer": "reviewer-standard",
    "validator": "validator-standard",
}
HIGH_RISK_CAPABILITIES = frozenset(
    {
        "network_access",
        "package_install",
        "dependency_resolution",
        "docker_socket",
        "service_start",
        "test_execution",
        "runtime_state_write",
        "github_issue_create",
    }
)


def _capabilities(
    *,
    network_access: str = "none",
    package_install: str = "deny",
    dependency_resolution: str = "allow-existing-lockfiles",
    docker_socket: str = "deny",
    service_start: str = "deny",
    test_execution: str = "allow-listed",
    runtime_state_write: str = "report-only",
    github_issue_create: str = "deny",
) -> dict[str, dict[str, Any]]:
    return {
        "network_access": {"mode": network_access, "allowlist": []},
        "package_install": {"mode": package_install, "managers": []},
        "dependency_resolution": {"mode": dependency_resolution},
        "docker_socket": {"mode": docker_socket},
        "service_start": {"mode": service_start, "allowlist": []},
        "test_execution": {"mode": test_execution, "commands": []},
        "runtime_state_write": {"mode": runtime_state_write},
        "github_issue_create": {"mode": github_issue_create, "repositories": []},
    }


CAPABILITY_PROFILE_PRESETS = {
    "coordinator-baseline": {
        "schema_version": CAPABILITY_PROFILE_SCHEMA_VERSION,
        "profile_id": "coordinator-baseline",
        "summary": "High-permission coordinator for Dispatch Engine state, spawn, validation, and decisions; not a project-file implementation profile.",
        "repo_write_scope": {"assigned_files": [], "allowed_write_roots": list(COORDINATOR_WRITE_ROOTS)},
        "capabilities": _capabilities(
            network_access="unrestricted",
            package_install="unrestricted",
            dependency_resolution="unrestricted",
            docker_socket="unrestricted",
            service_start="unrestricted",
            test_execution="unrestricted",
            runtime_state_write="coordinator",
            github_issue_create="draft-only",
        ),
        "escalation_policy": {"mode": "decision-required", "allowed_autonomous_technical": False},
    },
    "worker-readonly": {
        "schema_version": CAPABILITY_PROFILE_SCHEMA_VERSION,
        "profile_id": "worker-readonly",
        "summary": "Read-only worker inspection and report evidence; no repository writes.",
        "repo_write_scope": {"assigned_files": [], "allowed_write_roots": []},
        "capabilities": _capabilities(test_execution="deny"),
        "escalation_policy": {"mode": "decision-required", "allowed_autonomous_technical": False},
    },
    "worker-standard": {
        "schema_version": CAPABILITY_PROFILE_SCHEMA_VERSION,
        "profile_id": "worker-standard",
        "summary": "Assigned project-file edits plus listed tests; no network, installs, Docker, services, or broad runtime writes.",
        "repo_write_scope": {"assigned_files": [], "allowed_write_roots": []},
        "capabilities": _capabilities(),
        "escalation_policy": {"mode": "decision-required", "allowed_autonomous_technical": False},
    },
    "worker-dependency": {
        "schema_version": CAPABILITY_PROFILE_SCHEMA_VERSION,
        "profile_id": "worker-dependency",
        "summary": "Assigned project-file edits plus plan-approved dependency manager actions.",
        "repo_write_scope": {"assigned_files": [], "allowed_write_roots": []},
        "capabilities": _capabilities(
            package_install="allow-project-manager",
            dependency_resolution="allow-lockfile-update",
        ),
        "escalation_policy": {"mode": "decision-required", "allowed_autonomous_technical": False},
    },
    "reviewer-standard": {
        "schema_version": CAPABILITY_PROFILE_SCHEMA_VERSION,
        "profile_id": "reviewer-standard",
        "summary": "Read-only review with review evidence writes under Dispatch Engine state.",
        "repo_write_scope": {"assigned_files": [], "allowed_write_roots": []},
        "capabilities": _capabilities(test_execution="deny"),
        "escalation_policy": {"mode": "decision-required", "allowed_autonomous_technical": False},
    },
    "validator-standard": {
        "schema_version": CAPABILITY_PROFILE_SCHEMA_VERSION,
        "profile_id": "validator-standard",
        "summary": "Read-only validation using listed commands with validation evidence writes under Dispatch Engine state.",
        "repo_write_scope": {"assigned_files": [], "allowed_write_roots": []},
        "capabilities": _capabilities(),
        "escalation_policy": {"mode": "decision-required", "allowed_autonomous_technical": False},
    },
    "issue-reporter": {
        "schema_version": CAPABILITY_PROFILE_SCHEMA_VERSION,
        "profile_id": "issue-reporter",
        "summary": "No project writes; may draft or create approved Dispatch Engine GitHub issues.",
        "repo_write_scope": {"assigned_files": [], "allowed_write_roots": []},
        "capabilities": _capabilities(
            test_execution="deny",
            github_issue_create="allow-dispatch-engine",
        ),
        "escalation_policy": {"mode": "decision-required", "allowed_autonomous_technical": False},
    },
}


class AgentValidationError(ValueError):
    """Raised when an agent registry record is invalid."""


def normalize_capability_profile(
    profile: dict[str, Any] | str | None,
    *,
    role: str = "worker",
    assigned_files: list[str] | None = None,
    allowed_write_roots: list[str] | None = None,
    validation_commands: list[str] | None = None,
) -> dict[str, Any]:
    """Return a normalized granted/requested capability profile."""

    profile_id = PROFILE_DEFAULT_BY_ROLE.get(role, "worker-standard")
    explicit = profile is not None
    if isinstance(profile, str):
        profile_id = profile
        profile_data: dict[str, Any] = {}
    elif isinstance(profile, dict):
        profile_id = str(profile.get("profile_id") or profile_id)
        profile_data = dict(profile)
    elif profile is None:
        profile_data = {}
    else:
        raise AgentValidationError("capability_profile must be an object, string preset, or null")

    if profile_id not in CAPABILITY_PROFILE_PRESETS and not isinstance(profile, dict):
        raise AgentValidationError(f"unknown capability profile preset: {profile_id}")

    if isinstance(profile, dict) and "repo_write_scope" not in profile:
        raise AgentValidationError("capability_profile repo_write_scope is required")

    base = _profile_copy(CAPABILITY_PROFILE_PRESETS.get(profile_id, CAPABILITY_PROFILE_PRESETS[PROFILE_DEFAULT_BY_ROLE.get(role, "worker-standard")]))
    base["profile_id"] = profile_id
    if "summary" in profile_data:
        base["summary"] = str(profile_data["summary"])
    if "schema_version" in profile_data:
        base["schema_version"] = profile_data["schema_version"]
    if base.get("schema_version") != CAPABILITY_PROFILE_SCHEMA_VERSION:
        raise AgentValidationError("capability_profile schema_version must be 1")

    if isinstance(profile, str):
        scope = {
            "assigned_files": list(assigned_files or []),
            "allowed_write_roots": list(allowed_write_roots or []),
        }
    elif explicit:
        scope = profile_data.get("repo_write_scope", {})
    else:
        scope = {
            "assigned_files": list(assigned_files or []),
            "allowed_write_roots": list(allowed_write_roots or []),
        }
    base["repo_write_scope"] = _normalize_repo_write_scope(scope)

    capabilities = _profile_copy(base.get("capabilities", {}))
    for capability, value in profile_data.get("capabilities", {}).items():
        if capability not in CAPABILITY_KEYS:
            raise AgentValidationError(f"unknown capability: {capability}")
        capabilities[capability] = _normalize_capability(capability, value)
    for capability in CAPABILITY_KEYS:
        capabilities[capability] = _normalize_capability(capability, capabilities[capability])

    commands = list(validation_commands or [])
    test_capability = capabilities["test_execution"]
    if test_capability.get("mode") == "allow-listed" and commands and not test_capability.get("commands"):
        test_capability["commands"] = commands
    base["capabilities"] = capabilities

    escalation_policy = profile_data.get("escalation_policy", base.get("escalation_policy", {}))
    if isinstance(escalation_policy, str):
        escalation_policy = {"mode": escalation_policy, "allowed_autonomous_technical": False}
    if not isinstance(escalation_policy, dict):
        raise AgentValidationError("capability_profile escalation_policy must be an object")
    escalation_policy = dict(escalation_policy)
    escalation_policy.setdefault("mode", "decision-required")
    escalation_policy.setdefault("allowed_autonomous_technical", False)
    base["escalation_policy"] = escalation_policy
    return base


def default_capability_profile_for_role(role: str) -> str:
    return PROFILE_DEFAULT_BY_ROLE.get(role, "worker-standard")


def capability_profile_high_risk_grants(profile: dict[str, Any] | None) -> list[dict[str, str]]:
    if not isinstance(profile, dict):
        return []
    grants = []
    capabilities = profile.get("capabilities", {})
    if not isinstance(capabilities, dict):
        return []
    for capability in sorted(HIGH_RISK_CAPABILITIES):
        value = capabilities.get(capability, {})
        if not isinstance(value, dict):
            continue
        mode = value.get("mode")
        if _is_high_risk_mode(capability, mode):
            grants.append({"capability": capability, "mode": str(mode)})
    return grants


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
    capability_profile: dict[str, Any] | str | None = None,
    capability_profile_source: str | None = None,
    capability_profile_decision_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Write a durable agent registry record under agents/<agent-id>.json."""

    _validate_agent_id(agent_id)
    _validate_role(role)
    _validate_provider(provider)
    if role == "coordinator" and allowed_write_roots is None:
        allowed_write_roots = list(COORDINATOR_WRITE_ROOTS)
    granted_profile = normalize_capability_profile(
        capability_profile,
        role=role,
        assigned_files=assigned_files,
        allowed_write_roots=allowed_write_roots,
    )
    if role in IMPLEMENTATION_ROLES:
        scope = granted_profile["repo_write_scope"]
        assigned_files = list(scope.get("assigned_files", []))
        allowed_write_roots = list(scope.get("allowed_write_roots", []))

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
        "capability_profile": granted_profile,
        "capability_profile_source": capability_profile_source or ("explicit" if capability_profile is not None else "default"),
        "capability_profile_decision_ids": list(capability_profile_decision_ids or []),
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
    capability_profile: dict[str, Any] | str | None = None,
    capability_profile_source: str = "workstream",
    capability_profile_decision_ids: list[str] | None = None,
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
        capability_profile=capability_profile,
        capability_profile_source=capability_profile_source,
        capability_profile_decision_ids=capability_profile_decision_ids,
        prompt_path=_run_relative_path(run_state_dir, "prompts", agent_id, ".md"),
        stdout_path=_run_relative_path(run_state_dir, "logs", agent_id, ".stdout.log"),
        stderr_path=_run_relative_path(run_state_dir, "logs", agent_id, ".stderr.log"),
    )
    capability_profile_granted(
        run_state_dir / "events.jsonl",
        agent_id=agent_id,
        role="worker",
        profile_id=agent["capability_profile"]["profile_id"],
        source=agent["capability_profile_source"],
        workstream=workstream,
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
    _set_capability_report_defaults(report_record, agent)
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
    legacy_aliases = {
        alias: canonical
        for alias, canonical in WORKER_REPORT_LEGACY_ALIASES.items()
        if alias in report and canonical not in report
    }
    if legacy_aliases:
        malformed_details["legacy_aliases"] = legacy_aliases
        malformed_details["repair_action"] = "rename legacy worker report aliases to canonical schema fields"
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
    violations.extend(_capability_report_violations(agent, report, report_path))
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
        return _validate_validator_report(run_state_dir, agent)
    return []


def detect_protocol_violations(run_state_dir: Path) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    agents = list_agents(run_state_dir)
    implementation_agents = [
        agent for agent in agents if agent.get("role") in IMPLEMENTATION_ROLES
    ]
    implementation_agent_by_id = {
        str(agent.get("agent_id")): agent
        for agent in implementation_agents
        if agent.get("agent_id")
    }
    implementation_agents_by_workstream: dict[str, list[dict[str, Any]]] = {}
    for agent in implementation_agents:
        workstream = agent.get("workstream")
        if isinstance(workstream, str) and workstream:
            implementation_agents_by_workstream.setdefault(workstream, []).append(agent)

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
    invalid_report_workstreams = set()
    for agent in implementation_agents:
        if agent.get("status") in COMPLETED_IMPLEMENTATION_AGENT_STATUSES:
            if agent.get("role") == "worker":
                worker_violations = validate_worker_report(run_state_dir, agent["agent_id"])
            else:
                worker_violations = validate_review_validator_report(run_state_dir, agent["agent_id"])
            violations.extend(worker_violations)
            workstream = agent.get("workstream")
            if worker_violations and workstream:
                invalid_report_workstreams.add(workstream)
            if not worker_violations and workstream:
                valid_implementation_workstreams.add(workstream)

    for path in sorted((run_state_dir / "workstreams").glob("*.json")):
        workstream = json.loads(path.read_text(encoding="utf-8"))
        workstream_id = workstream.get("id", path.stem)
        if workstream.get("status") not in IMPLEMENTED_WORKSTREAM_STATUSES:
            continue
        if workstream_id in valid_implementation_workstreams:
            continue
        assigned_agent_id = workstream.get("assigned_agent")
        if isinstance(assigned_agent_id, str) and assigned_agent_id:
            assigned_agent = implementation_agent_by_id.get(assigned_agent_id)
            if assigned_agent is None:
                violations.append(
                    {
                        "violation": "assigned_implementation_agent_missing",
                        "workstream": workstream_id,
                        "details": {
                            "status": workstream.get("status"),
                            "assigned_agent": assigned_agent_id,
                        },
                    }
                )
                continue
            if assigned_agent.get("status") not in COMPLETED_IMPLEMENTATION_AGENT_STATUSES:
                violations.append(
                    _assigned_agent_status_violation(workstream, assigned_agent)
                )
                continue
            continue

        assigned_agents = implementation_agents_by_workstream.get(str(workstream_id), [])
        if assigned_agents:
            invalid_status_agents = [
                agent
                for agent in assigned_agents
                if agent.get("status") not in COMPLETED_IMPLEMENTATION_AGENT_STATUSES
            ]
            if invalid_status_agents:
                violations.extend(
                    _assigned_agent_status_violation(workstream, agent)
                    for agent in invalid_status_agents
                )
            elif workstream_id in invalid_report_workstreams:
                continue
            continue

        violations.append(
            {
                "violation": "unregistered_implementation_completion",
                "workstream": workstream_id,
                "details": {"status": workstream.get("status")},
            }
        )
    return violations


def _assigned_agent_status_violation(
    workstream: dict[str, Any],
    agent: dict[str, Any],
) -> dict[str, Any]:
    return {
        "violation": "assigned_implementation_agent_invalid_status",
        "agent_id": agent.get("agent_id"),
        "workstream": workstream.get("id"),
        "details": {
            "status": workstream.get("status"),
            "assigned_agent": agent.get("agent_id"),
            "agent_status": agent.get("status"),
            "role": agent.get("role"),
            "expected_agent_statuses": sorted(COMPLETED_IMPLEMENTATION_AGENT_STATUSES),
        },
    }


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
        if violation["violation"] == "capability_overreach":
            details = violation.get("details", {})
            capability_violation(
                event_log,
                agent_id=str(violation.get("agent_id") or ""),
                capability=str(details.get("capability") or ""),
                requested_mode=str(details.get("requested_mode") or ""),
                granted_mode=details.get("granted_mode"),
                workstream=violation.get("workstream"),
            )
    return violations


def _profile_copy(profile: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(profile))


def _normalize_repo_write_scope(scope: Any) -> dict[str, list[str]]:
    if not isinstance(scope, dict):
        raise AgentValidationError("capability_profile repo_write_scope must be an object")
    for field in ("assigned_files", "allowed_write_roots"):
        if field not in scope:
            raise AgentValidationError(f"capability_profile repo_write_scope.{field} is required")
        if not isinstance(scope[field], list):
            raise AgentValidationError(f"capability_profile repo_write_scope.{field} must be a list")
    return {
        "assigned_files": [str(item) for item in scope.get("assigned_files", [])],
        "allowed_write_roots": [str(item) for item in scope.get("allowed_write_roots", [])],
    }


def _normalize_capability(capability: str, value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        normalized = {"mode": value}
    elif isinstance(value, dict):
        normalized = dict(value)
    else:
        raise AgentValidationError(f"capability {capability} must be a mode string or object")
    mode = normalized.get("mode")
    if mode not in CAPABILITY_MODE_ORDER[capability]:
        raise AgentValidationError(f"invalid mode for {capability}: {mode}")
    return normalized


def _set_capability_report_defaults(report: dict[str, Any], agent: dict[str, Any]) -> None:
    profile = agent.get("capability_profile")
    if isinstance(profile, dict):
        report.setdefault("capability_profile_id", profile.get("profile_id"))
    report.setdefault("capabilities_exercised", [])
    report.setdefault("capability_escalations", [])


def _capability_report_violations(
    agent: dict[str, Any],
    report: dict[str, Any],
    report_path: Path,
) -> list[dict[str, Any]]:
    profile = agent.get("capability_profile")
    if not isinstance(profile, dict):
        return []
    capabilities = report.get("capabilities_exercised", [])
    if capabilities in (None, []):
        return []
    if not isinstance(capabilities, list):
        return [
            _report_violation(
                "malformed_capability_report",
                agent,
                {
                    "report_path": agent.get("report_path"),
                    "field": "capabilities_exercised",
                    "actual": type(capabilities).__name__,
                    "expected": "array",
                },
            )
        ]

    violations: list[dict[str, Any]] = []
    for index, item in enumerate(capabilities):
        if isinstance(item, str):
            item = {
                "capability": item,
                "mode": _granted_capability_mode(profile, item),
            }
        if not isinstance(item, dict):
            violations.append(
                _report_violation(
                    "malformed_capability_report",
                    agent,
                    {
                        "report_path": agent.get("report_path"),
                        "field": f"capabilities_exercised[{index}]",
                        "actual": type(item).__name__,
                        "expected": "object",
                    },
                )
            )
            continue
        capability = str(item.get("capability") or "")
        requested_mode = str(item.get("mode") or item.get("requested_mode") or "")
        decision_id = item.get("decision_id")
        if decision_id:
            continue
        granted = profile.get("capabilities", {}).get(capability, {})
        granted_mode = granted.get("mode") if isinstance(granted, dict) else None
        if not _capability_use_within_grant(capability, requested_mode, item, granted):
            violations.append(
                _report_violation(
                    "capability_overreach",
                    agent,
                    {
                        "report_path": agent.get("report_path"),
                        "evidence_path": str(report_path),
                        "field": f"capabilities_exercised[{index}]",
                        "capability": capability,
                        "requested_mode": requested_mode,
                        "granted_mode": granted_mode,
                        "evidence": item.get("evidence"),
                    },
                )
            )
    return violations


def _capability_use_within_grant(
    capability: str,
    requested_mode: str,
    item: dict[str, Any],
    granted: Any,
) -> bool:
    if capability not in CAPABILITY_MODE_ORDER or requested_mode not in CAPABILITY_MODE_ORDER.get(capability, ()):
        return False
    if not isinstance(granted, dict):
        return False
    granted_mode = granted.get("mode")
    if granted_mode not in CAPABILITY_MODE_ORDER[capability]:
        return False
    modes = CAPABILITY_MODE_ORDER[capability]
    if modes.index(requested_mode) > modes.index(granted_mode):
        return False
    if capability == "test_execution" and granted_mode == "allow-listed":
        command = item.get("command")
        commands = granted.get("commands", [])
        if command and isinstance(commands, list) and commands and command not in commands:
            return False
    return True


def _granted_capability_mode(profile: dict[str, Any], capability: str) -> str:
    granted = profile.get("capabilities", {}).get(capability, {})
    if isinstance(granted, dict):
        mode = granted.get("mode")
        if isinstance(mode, str):
            return mode
    return ""


def _is_high_risk_mode(capability: str, mode: Any) -> bool:
    if capability == "test_execution":
        return mode == "unrestricted"
    if capability == "runtime_state_write":
        return mode in {"agent-heartbeat", "coordinator"}
    if capability == "dependency_resolution":
        return mode in {"allow-lockfile-update", "unrestricted"}
    return mode not in {None, "none", "deny", "report-only", "allow-listed", "allow-existing-lockfiles"}


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
    _set_capability_report_defaults(report_record, agent)
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
    return _capability_report_violations(agent, report, report_path)


def _validate_validator_report(run_state_dir: Path, agent: dict[str, Any]) -> list[dict[str, Any]]:
    report_path = _report_path(run_state_dir, agent)
    report_path_text = agent.get("report_path")
    if not report_path.exists():
        return [
            _report_violation(
                "missing_validator_report",
                agent,
                {"report_path": report_path_text},
            )
        ]

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [
            _report_violation(
                "malformed_validator_json",
                agent,
                {
                    "report_path": report_path_text,
                    "field": "$",
                    "actual": str(exc),
                    "expected": "valid JSON object",
                },
            )
        ]

    if not isinstance(report, dict):
        return [
            _report_violation(
                "invalid_validator_field_type",
                agent,
                {
                    "report_path": report_path_text,
                    "field": "$",
                    "actual": type(report).__name__,
                    "expected": "object",
                },
            )
        ]

    missing = sorted(VALIDATOR_REPORT_REQUIRED_FIELDS - set(report))
    if missing:
        return [
            _report_violation(
                "missing_validator_fields",
                agent,
                {
                    "report_path": report_path_text,
                    "missing_fields": missing,
                    "expected": sorted(VALIDATOR_REPORT_REQUIRED_FIELDS),
                },
            )
        ]

    type_violation = _validator_field_type_violation(agent, report, report_path_text)
    if type_violation:
        return [type_violation]

    identity_violation = _validator_identity_violation(agent, report, report_path_text)
    if identity_violation:
        return [identity_violation]

    status = report.get("status")
    if status not in VALIDATOR_REPORT_STATUSES and status != VALIDATOR_REPORT_COMPAT_STATUS:
        return [
            _report_violation(
                "invalid_validator_status",
                agent,
                {
                    "report_path": report_path_text,
                    "field": "status",
                    "actual": status,
                    "allowed": list(VALIDATOR_REPORT_STATUS_ORDER),
                    "suggested_status": _suggest_validator_status(report),
                    "compatibility_rule": "`completed` is accepted only for version 1 reports with complete successful evidence.",
                },
            )
        ]

    missing_evidence = _missing_validator_evidence(report)
    if missing_evidence:
        return [
            _report_violation(
                "missing_validation_evidence",
                agent,
                {
                    "report_path": report_path_text,
                    "missing_fields": missing_evidence,
                    "evidence_mode": (
                        "skipped_validator"
                        if report.get("status") == "skipped"
                        else "non_skipped_validator"
                    ),
                    "suggested_status": "skipped" if report.get("status") == "skipped" else _suggest_validator_status(report),
                },
            )
        ]

    inconsistent = _validator_evidence_inconsistency(report)
    if inconsistent:
        return [
            _report_violation(
                "inconsistent_validation_evidence",
                agent,
                {
                    "report_path": report_path_text,
                    **inconsistent,
                },
            )
        ]

    if status == VALIDATOR_REPORT_COMPAT_STATUS:
        if report.get("schema_version") != AGENT_SCHEMA_VERSION:
            return [
                _report_violation(
                    "inconsistent_validation_evidence",
                    agent,
                    {
                        "report_path": report_path_text,
                        "field": "schema_version",
                        "actual": report.get("schema_version"),
                        "expected": AGENT_SCHEMA_VERSION,
                        "compatibility_rule": "`completed` only normalizes for schema_version 1.",
                        "suggested_status": "passed",
                    },
                )
            ]
    return _capability_report_violations(agent, report, report_path)


def _validator_field_type_violation(
    agent: dict[str, Any],
    report: dict[str, Any],
    report_path: str | None,
) -> dict[str, Any] | None:
    expected_types = (
        ("schema_version", int, "integer"),
        ("agent_id", str, "string"),
        ("role", str, "string"),
        ("workstream", str, "string"),
        ("status", str, "string"),
        ("summary", str, "non-empty string"),
        ("artifacts", list, "array"),
        ("command", str, "string"),
        ("output_summary", str, "string"),
        ("not_run_reason", str, "string"),
        ("validated_agent_id", str, "string"),
        ("validation", list, "array"),
        ("scope_check", dict, "object"),
        ("risks", list, "array"),
        ("completed_at", str, "string"),
    )
    for field, expected_type, expected_label in expected_types:
        if field not in report:
            continue
        if field == "schema_version":
            valid = isinstance(report[field], int) and not isinstance(report[field], bool)
        elif field == "summary":
            valid = _has_text(report[field])
        else:
            valid = isinstance(report[field], expected_type)
        if not valid:
            return _report_violation(
                "invalid_validator_field_type",
                agent,
                {
                    "report_path": report_path,
                    "field": field,
                    "actual": type(report[field]).__name__,
                    "expected": expected_label,
                },
            )

    artifacts = report.get("artifacts")
    if isinstance(artifacts, list):
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, str):
                return _report_violation(
                    "invalid_validator_field_type",
                    agent,
                    {
                        "report_path": report_path,
                        "field": f"artifacts[{index}]",
                        "actual": type(artifact).__name__,
                        "expected": "string",
                    },
                )

    validation = report.get("validation")
    if isinstance(validation, list):
        for index, item in enumerate(validation):
            if not isinstance(item, dict):
                return _report_violation(
                    "invalid_validator_field_type",
                    agent,
                    {
                        "report_path": report_path,
                        "field": f"validation[{index}]",
                        "actual": type(item).__name__,
                        "expected": "object",
                    },
                )
            for field in ("command", "status", "evidence"):
                if field in item and not isinstance(item[field], str):
                    return _report_violation(
                        "invalid_validator_field_type",
                        agent,
                        {
                            "report_path": report_path,
                            "field": f"validation[{index}].{field}",
                            "actual": type(item[field]).__name__,
                            "expected": "string",
                        },
                    )

    scope_check = report.get("scope_check")
    if isinstance(scope_check, dict):
        violations = scope_check.get("violations")
        if violations is not None and not isinstance(violations, list):
            return _report_violation(
                "invalid_validator_field_type",
                agent,
                {
                    "report_path": report_path,
                    "field": "scope_check.violations",
                    "actual": type(violations).__name__,
                    "expected": "array",
                },
            )
    return None


def _validator_identity_violation(
    agent: dict[str, Any],
    report: dict[str, Any],
    report_path: str | None,
) -> dict[str, Any] | None:
    expected = {
        "agent_id": agent.get("agent_id"),
        "role": "validator",
        "workstream": agent.get("workstream"),
    }
    for field, expected_value in expected.items():
        if report.get(field) != expected_value:
            return _report_violation(
                "validator_identity_mismatch",
                agent,
                {
                    "report_path": report_path,
                    "field": field,
                    "actual": report.get(field),
                    "expected": expected_value,
                },
            )
    return None


def _missing_validator_evidence(report: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if report.get("status") == "skipped":
        if not _has_text(report.get("not_run_reason")):
            missing.append("not_run_reason")
        return sorted(missing)
    if not _has_text(report.get("command")):
        missing.append("command")
    if not _has_text(report.get("output_summary")):
        missing.append("output_summary")
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        missing.append("artifacts")
    return sorted(missing)


def _validator_evidence_inconsistency(report: dict[str, Any]) -> dict[str, Any] | None:
    validation = report.get("validation")
    if isinstance(validation, list):
        for index, item in enumerate(validation):
            if not isinstance(item, dict):
                continue
            status = item.get("status")
            if status not in VALIDATOR_REPORT_STATUSES:
                return {
                    "field": f"validation[{index}].status",
                    "actual": status,
                    "allowed": list(VALIDATOR_REPORT_STATUS_ORDER),
                    "suggested_status": _suggest_validator_status(report),
                }
            if not _has_text(item.get("command")) or not _has_text(item.get("evidence")):
                missing = []
                if not _has_text(item.get("command")):
                    missing.append("command")
                if not _has_text(item.get("evidence")):
                    missing.append("evidence")
                return {
                    "field": f"validation[{index}]",
                    "missing_fields": missing,
                    "evidence_mode": "structured_validation",
                    "suggested_status": _suggest_validator_status(report),
                }
            if report.get("status") in {"passed", VALIDATOR_REPORT_COMPAT_STATUS} and status in {"failed", "blocked"}:
                return {
                    "field": f"validation[{index}].status",
                    "actual": status,
                    "expected": "passed or skipped with evidence",
                    "compatibility_rule": "passed or normalized completed reports cannot include failed or blocked validation items.",
                    "suggested_status": status,
                }
            if report.get("status") == VALIDATOR_REPORT_COMPAT_STATUS and status == "skipped" and not _has_text(item.get("evidence")):
                return {
                    "field": f"validation[{index}].evidence",
                    "actual": item.get("evidence"),
                    "expected": "skip evidence",
                    "compatibility_rule": "`completed` only normalizes when skipped checks explain the skip.",
                    "suggested_status": "passed",
                }

    scope_check = report.get("scope_check")
    if isinstance(scope_check, dict):
        scope_status = scope_check.get("status")
        if scope_status is not None and scope_status not in VALIDATOR_REPORT_STATUSES:
            return {
                "field": "scope_check.status",
                "actual": scope_status,
                "allowed": list(VALIDATOR_REPORT_STATUS_ORDER),
                "suggested_status": _suggest_validator_status(report),
            }
        violations = scope_check.get("violations")
        if report.get("status") in {"passed", VALIDATOR_REPORT_COMPAT_STATUS} and isinstance(violations, list) and violations:
            return {
                "field": "scope_check.violations",
                "actual": violations,
                "expected": [],
                "compatibility_rule": "passed or normalized completed evidence cannot include scope violations.",
                "suggested_status": "failed",
            }
        if report.get("status") == VALIDATOR_REPORT_COMPAT_STATUS and scope_status not in {None, "passed"}:
            return {
                "field": "scope_check.status",
                "actual": scope_status,
                "expected": "passed",
                "compatibility_rule": "`completed` only normalizes when scope_check.status is absent or passed.",
                "suggested_status": scope_status or "failed",
            }
    return None


def _suggest_validator_status(report: dict[str, Any]) -> str:
    validation = report.get("validation")
    if isinstance(validation, list):
        statuses = [item.get("status") for item in validation if isinstance(item, dict)]
        if any(status == "blocked" for status in statuses):
            return "blocked"
        if any(status == "failed" for status in statuses):
            return "failed"
    scope_check = report.get("scope_check")
    if isinstance(scope_check, dict):
        scope_status = scope_check.get("status")
        if scope_status in {"failed", "blocked"}:
            return scope_status
        violations = scope_check.get("violations")
        if isinstance(violations, list) and violations:
            return "failed"
    if report.get("status") == "skipped" or _has_text(report.get("not_run_reason")) and not _has_text(report.get("command")):
        return "skipped"
    return "passed"


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
    for assigned in assigned_files:
        normalized_assigned = assigned.rstrip("/")
        if assigned.endswith("/") and normalized.startswith(f"{normalized_assigned}/"):
            return True
    if normalized in _agent_runtime_evidence_paths(agent):
        return True
    for root in agent.get("allowed_write_roots", []):
        normalized_root = root.removeprefix("./").rstrip("/")
        if normalized_root and (
            normalized == normalized_root or normalized.startswith(f"{normalized_root}/")
        ):
            return True
    return False


def _agent_runtime_evidence_paths(agent: dict[str, Any]) -> set[str]:
    paths = {
        value.removeprefix("./")
        for value in (
            agent.get("report_path"),
            agent.get("heartbeat_path"),
            agent.get("log_path"),
            agent.get("stdout_path"),
            agent.get("stderr_path"),
        )
        if isinstance(value, str) and value
    }
    agent_id = agent.get("agent_id")
    run_id = agent.get("run_id")
    if isinstance(agent_id, str) and agent_id and isinstance(run_id, str) and run_id:
        paths.add(f".dispatch/runs/{run_id}/heartbeats/{agent_id}.json")
        paths.add(f".dispatch/runs/{run_id}/heartbeats/{agent_id}.jsonl")
    return paths


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
