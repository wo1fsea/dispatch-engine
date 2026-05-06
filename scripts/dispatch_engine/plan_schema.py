"""Explicit dispatch plan validation and import helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agents import AgentValidationError, normalize_capability_profile
from .events import append_event, utc_timestamp
from .runs import initialize_run_dir, new_run_id, plans_dir, run_dir

COORDINATED_OVERLAP = "shared-write-approved"
REQUIRED_PLAN_FIELDS = ("schema_version", "plan_id", "objective", "workstreams")
SERVICE_START_MARKERS = (
    "npm run dev",
    "npm start",
    "pnpm dev",
    "pnpm start",
    "yarn dev",
    "yarn start",
    "python -m http.server",
    "python3 -m http.server",
    "docker compose up",
    "docker-compose up",
)
NETWORK_ACCESS_MARKERS = ("http://", "https://", "curl ", "wget ")
ISSUE_EVIDENCE_MARKERS = (
    "gh issue view",
    "github issue evidence",
    "issue evidence",
    "github issues",
    "github issue",
)
SERIAL_MODES = ("serial",)


class PlanValidationError(ValueError):
    """Raised when an explicit dispatch plan is malformed."""


def load_dispatch_plan(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PlanValidationError(f"plan file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PlanValidationError(f"plan file is not valid JSON: {exc}") from exc
    return validate_dispatch_plan(raw)


def validate_dispatch_plan(plan: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise PlanValidationError("plan must be a JSON object")

    for field in REQUIRED_PLAN_FIELDS:
        if field not in plan:
            raise PlanValidationError(f"missing required field: {field}")
        if field not in ("schema_version", "workstreams") and not plan[field]:
            raise PlanValidationError(f"required field must not be empty: {field}")

    workstreams = plan["workstreams"]
    if not isinstance(workstreams, list) or not workstreams:
        raise PlanValidationError("plan must include non-empty workstreams")

    ids: set[str] = set()
    dependencies: dict[str, list[str]] = {}
    for index, workstream in enumerate(workstreams):
        if not isinstance(workstream, dict):
            raise PlanValidationError(f"workstream at index {index} must be an object")
        workstream_id = workstream.get("id")
        if not workstream_id:
            raise PlanValidationError(f"workstream at index {index} is missing id")
        if workstream_id in ids:
            raise PlanValidationError(f"duplicate workstream id: {workstream_id}")
        ids.add(workstream_id)
        depends_on = workstream.get("depends_on", [])
        if depends_on is None:
            depends_on = []
        if not isinstance(depends_on, list):
            raise PlanValidationError(f"workstream {workstream_id} depends_on must be a list")
        dependencies[workstream_id] = depends_on

    for workstream_id, depends_on in dependencies.items():
        for dependency in depends_on:
            if dependency not in ids:
                raise PlanValidationError(
                    f"workstream {workstream_id} has unknown dependency: {dependency}"
                )

    _validate_parallel_overlaps(workstreams, dependencies)
    for workstream in workstreams:
        _normalize_workstream_capability_profile(workstream)
    plan["plan_diagnostics"] = _plan_diagnostics(plan, dependencies)
    return plan


def import_dispatch_plan(target: Path, plan_path: Path) -> dict[str, Any]:
    repo_root = target.resolve()
    source_path = plan_path.resolve()
    plan = load_dispatch_plan(source_path)
    plans_dir(repo_root).mkdir(parents=True, exist_ok=True)

    run_id = new_run_id()
    state_dir = run_dir(repo_root, run_id)
    now = utc_timestamp()
    workstreams = [_planned_workstream(item, now) for item in plan["workstreams"]]
    decisions = [_planned_decision(item, now) for item in plan.get("decisions", [])]
    run = {
        "kind": "plan",
        "run_id": run_id,
        "repo_root": str(repo_root),
        "state_dir": str(state_dir),
        "objective": plan["objective"],
        "status": "planned",
        "created_at": now,
        "updated_at": now,
        "plan": {
            "schema_version": plan["schema_version"],
            "plan_id": plan["plan_id"],
            "source_path": str(source_path),
            "created_by": plan.get("created_by"),
            "created_at": plan.get("created_at"),
            "target_repo": plan.get("target_repo"),
            "diagnostics": plan.get("plan_diagnostics", []),
        },
        "repo_context": plan.get("repo_context", {}),
        "review": plan.get("review", {}),
        "workstreams": workstreams,
        "decisions": decisions,
    }

    _write_imported_run(state_dir, run)
    return {
        "kind": "plan_import",
        "run_id": run_id,
        "plan_id": plan["plan_id"],
        "objective": plan["objective"],
        "status": "planned",
        "state_dir": str(state_dir),
        "repo_root": str(repo_root),
        "plan_source": str(source_path),
        "workstream_count": len(workstreams),
        "decision_count": len(decisions),
        "plan_diagnostics": plan.get("plan_diagnostics", []),
    }


def _plan_diagnostics(
    plan: dict[str, Any],
    dependencies: dict[str, list[str]],
) -> list[dict[str, Any]]:
    workstreams = plan["workstreams"]
    diagnostics: list[dict[str, Any]] = []

    if (
        len(workstreams) > 1
        and all(_is_serial_workstream(workstream) for workstream in workstreams)
        and not _has_serial_rationale(plan)
        and not any(_has_serial_rationale(workstream) for workstream in workstreams)
    ):
        diagnostics.append(
            {
                "code": "serial_workstreams_without_serial_rationale",
                "severity": "warning",
                "message": (
                    "Multiple workstreams are marked serial without a plan-level or "
                    "workstream-level serial rationale."
                ),
                "workstreams": [str(workstream["id"]) for workstream in workstreams],
            }
        )

    missing_parallel_group = [
        str(workstream["id"])
        for workstream in workstreams
        if _has_independent_peer(workstream["id"], workstreams, dependencies)
        and not workstream.get("parallel_group")
    ]
    if missing_parallel_group and not _has_parallelism_metadata(plan):
        diagnostics.append(
            {
                "code": "independent_workstreams_missing_parallel_group",
                "severity": "warning",
                "message": (
                    "Independent workstreams do not declare parallel_group labels or "
                    "plan-level parallelism metadata."
                ),
                "workstreams": missing_parallel_group,
            }
        )

    return diagnostics


def _is_serial_workstream(workstream: dict[str, Any]) -> bool:
    return str(workstream.get("mode", "")).lower() in SERIAL_MODES


def _has_serial_rationale(item: dict[str, Any]) -> bool:
    for field in ("serial_rationale", "serial_reason", "serialized_rationale"):
        if item.get(field):
            return True
    parallelism = item.get("parallelism")
    if isinstance(parallelism, dict):
        return bool(
            parallelism.get("serial_rationale")
            or parallelism.get("serial_reason")
            or parallelism.get("serialized_rationale")
            or parallelism.get("intentional_serialization")
        )
    return False


def _has_parallelism_metadata(plan: dict[str, Any]) -> bool:
    parallelism = plan.get("parallelism")
    if not isinstance(parallelism, dict):
        return False
    return bool(
        parallelism.get("concurrency_budget")
        or parallelism.get("safe_batches")
        or parallelism.get("batches")
        or parallelism.get("parallel_groups")
    )


def _has_independent_peer(
    workstream_id: str,
    workstreams: list[dict[str, Any]],
    dependencies: dict[str, list[str]],
) -> bool:
    current = next(item for item in workstreams if item["id"] == workstream_id)
    current_files = _files(current)
    for peer in workstreams:
        peer_id = peer["id"]
        if peer_id == workstream_id:
            continue
        if _depends_on(workstream_id, peer_id, dependencies) or _depends_on(
            peer_id, workstream_id, dependencies
        ):
            continue
        if current_files & _files(peer):
            continue
        return True
    return False


def _validate_parallel_overlaps(
    workstreams: list[dict[str, Any]], dependencies: dict[str, list[str]]
) -> None:
    by_id = {item["id"]: item for item in workstreams}
    for left_index, left in enumerate(workstreams):
        for right in workstreams[left_index + 1 :]:
            shared_files = _files(left) & _files(right)
            if not shared_files:
                continue
            left_id = left["id"]
            right_id = right["id"]
            if _depends_on(left_id, right_id, dependencies) or _depends_on(
                right_id, left_id, dependencies
            ):
                continue
            if _coordinated_overlap(by_id[left_id]) and _coordinated_overlap(by_id[right_id]):
                continue
            files = ", ".join(sorted(shared_files))
            raise PlanValidationError(
                f"workstreams {left_id} and {right_id} have overlapping files without "
                f"dependency or coordination: {files}"
            )


def _files(workstream: dict[str, Any]) -> set[str]:
    files = workstream.get("files", [])
    if files is None:
        return set()
    if not isinstance(files, list):
        raise PlanValidationError(f"workstream {workstream.get('id')} files must be a list")
    return {str(item) for item in files}


def _depends_on(workstream_id: str, possible_dependency: str, dependencies: dict[str, list[str]]) -> bool:
    pending = list(dependencies.get(workstream_id, []))
    seen: set[str] = set()
    while pending:
        dependency = pending.pop()
        if dependency == possible_dependency:
            return True
        if dependency in seen:
            continue
        seen.add(dependency)
        pending.extend(dependencies.get(dependency, []))
    return False


def _coordinated_overlap(workstream: dict[str, Any]) -> bool:
    return workstream.get("coordination") == COORDINATED_OVERLAP


def _planned_workstream(workstream: dict[str, Any], timestamp: str) -> dict[str, Any]:
    planned = dict(workstream)
    planned.setdefault("depends_on", [])
    planned.setdefault("files", [])
    _normalize_workstream_capability_profile(planned)
    planned["status"] = "planned"
    planned["created_at"] = timestamp
    planned["updated_at"] = timestamp
    return planned


def _normalize_workstream_capability_profile(workstream: dict[str, Any]) -> None:
    validation_commands = _string_list(
        workstream.get("validation", []),
        field="validation",
        workstream=workstream,
    )
    try:
        workstream["capability_profile"] = normalize_capability_profile(
            workstream.get("capability_profile"),
            role="worker",
            assigned_files=_string_list(workstream.get("files", []), field="files", workstream=workstream),
            allowed_write_roots=_string_list(
                workstream.get("allowed_write_roots", []),
                field="allowed_write_roots",
                workstream=workstream,
            ),
            validation_commands=validation_commands,
        )
    except AgentValidationError as exc:
        raise PlanValidationError(f"workstream {workstream.get('id')} capability_profile invalid: {exc}") from exc
    warnings = _validation_capability_warnings(validation_commands, workstream["capability_profile"])
    issue_evidence_warning = _issue_evidence_capability_warning(
        workstream,
        validation_commands,
        workstream["capability_profile"],
    )
    if issue_evidence_warning:
        warnings.append(issue_evidence_warning)
    if warnings:
        workstream["validation_warnings"] = warnings


def _validation_capability_warnings(
    validation_commands: list[str],
    capability_profile: dict[str, Any],
) -> list[dict[str, str]]:
    capabilities = capability_profile.get("capabilities", {})
    if not isinstance(capabilities, dict):
        return []

    warnings: list[dict[str, str]] = []
    for command in validation_commands:
        lowered = command.lower()
        service_mode = _capability_mode(capabilities, "service_start")
        if service_mode == "deny" and _looks_like_service_start(lowered):
            warnings.append(
                {
                    "code": "validation_command_requires_service_start",
                    "capability": "service_start",
                    "granted_mode": service_mode,
                    "command": command,
                    "message": "Validation command appears to start a service but capability_profile.service_start is deny.",
                }
            )

        network_mode = _capability_mode(capabilities, "network_access")
        if network_mode == "none" and _looks_like_network_access(lowered):
            warnings.append(
                {
                    "code": "validation_command_requires_network_access",
                    "capability": "network_access",
                    "granted_mode": network_mode,
                    "command": command,
                    "message": "Validation command appears to access a network endpoint but capability_profile.network_access is none.",
                }
            )
    return warnings


def _capability_mode(capabilities: dict[str, Any], capability: str) -> str:
    value = capabilities.get(capability, {})
    if not isinstance(value, dict):
        return ""
    return str(value.get("mode", ""))


def _looks_like_service_start(lowered_command: str) -> bool:
    return any(marker in lowered_command for marker in SERVICE_START_MARKERS)


def _looks_like_network_access(lowered_command: str) -> bool:
    return any(marker in lowered_command for marker in NETWORK_ACCESS_MARKERS)


def _issue_evidence_capability_warning(
    workstream: dict[str, Any],
    validation_commands: list[str],
    capability_profile: dict[str, Any],
) -> dict[str, str] | None:
    capabilities = capability_profile.get("capabilities", {})
    if not isinstance(capabilities, dict):
        return None
    network_mode = _capability_mode(capabilities, "network_access")
    if network_mode != "none":
        return None
    if not _looks_like_issue_evidence(workstream, validation_commands):
        return None
    return {
        "code": "issue_evidence_requires_network_access",
        "capability": "network_access",
        "granted_mode": network_mode,
        "source": "title/scope/validation",
        "message": (
            "Workstream appears to require GitHub issue evidence but "
            "capability_profile.network_access is none. Grant explicit "
            "read-only network access, record a local-only evidence "
            "strategy, or block before dispatch."
        ),
    }


def _looks_like_issue_evidence(
    workstream: dict[str, Any],
    validation_commands: list[str],
) -> bool:
    text = " ".join(
        [
            str(workstream.get("title", "")),
            str(workstream.get("scope", "")),
            " ".join(validation_commands),
        ]
    ).lower()
    return any(marker in text for marker in ISSUE_EVIDENCE_MARKERS)


def _string_list(value: Any, *, field: str, workstream: dict[str, Any]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise PlanValidationError(f"workstream {workstream.get('id')} {field} must be a list")
    return [str(item) for item in value]


def _planned_decision(decision: dict[str, Any], timestamp: str) -> dict[str, Any]:
    planned = dict(decision)
    planned.setdefault("status", "pending")
    planned.setdefault("created_at", timestamp)
    planned["updated_at"] = timestamp
    return planned


def _write_imported_run(state_dir: Path, run: dict[str, Any]) -> None:
    initialize_run_dir(state_dir)
    (state_dir / "run.json").write_text(json.dumps(run, indent=2, sort_keys=True) + "\n")
    decisions_log = state_dir / "decisions.jsonl"
    for decision in run["decisions"]:
        with decisions_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(decision, sort_keys=True) + "\n")
    for workstream in run["workstreams"]:
        path = state_dir / "workstreams" / f"{workstream['id']}.json"
        path.write_text(json.dumps(workstream, indent=2, sort_keys=True) + "\n")

    event_log = state_dir / "events.jsonl"
    append_event(
        event_log,
        "run.created",
        payload={"objective": run["objective"], "run_id": run["run_id"]},
    )
    append_event(
        event_log,
        "plan.imported",
        payload={
            "plan_id": run["plan"]["plan_id"],
            "source_path": run["plan"]["source_path"],
            "workstream_count": len(run["workstreams"]),
        },
    )
    for workstream in run["workstreams"]:
        append_event(
            event_log,
            "workstream.planned",
            workstream=workstream["id"],
            payload={"title": workstream.get("title", workstream["id"])},
        )
