"""Protocol-violation resolution records for Dispatch Engine runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agents import detect_protocol_violations
from .events import read_events, utc_timestamp

PROTOCOL_RESOLUTION_SCHEMA_VERSION = 1
PROTOCOL_RESOLUTION_KINDS = frozenset(
    {
        "acknowledged",
        "accepted_with_concerns",
        "superseded_by_validation",
        "false_positive",
    }
)


class ProtocolResolutionValidationError(ValueError):
    """Raised when a protocol-violation resolution cannot be recorded."""

    def __init__(self, message: str, *, status: str = "invalid_protocol_violation_resolution") -> None:
        super().__init__(message)
        self.status = status


def resolve_protocol_violation(
    run_state_dir: Path,
    *,
    violation: str,
    resolution: str,
    rationale: str,
    evidence: str,
    agent_id: str | None = None,
    workstream: str | None = None,
    actor: str = "dispatch-engine",
) -> dict[str, Any]:
    """Append a durable resolution record after conservatively matching a violation."""

    selector = _validate_selector(
        violation=violation,
        agent_id=agent_id,
        workstream=workstream,
    )
    _validate_resolution_kind(resolution)
    rationale = _validate_text(rationale, "rationale")
    evidence = _validate_text(evidence, "evidence")
    actor = _validate_text(actor, "actor")

    current_violations = list_current_protocol_violations(run_state_dir)
    matches = [item for item in current_violations if violation_matches_selector(item, selector)]
    if not matches:
        raise ProtocolResolutionValidationError(
            "protocol violation selector did not match a current violation",
            status="protocol_violation_selector_not_found",
        )
    if len(matches) > 1:
        raise ProtocolResolutionValidationError(
            "protocol violation selector matched multiple current violations; add --agent-id or --workstream",
            status="ambiguous_protocol_violation_selector",
        )

    record = {
        "schema_version": PROTOCOL_RESOLUTION_SCHEMA_VERSION,
        "resolution_id": _next_resolution_id(run_state_dir),
        "resolved_at": utc_timestamp(),
        "actor": actor,
        "violation": violation,
        "resolution": resolution,
        "rationale": rationale,
        "evidence": evidence,
        "selector": selector,
        "matched_violation": matches[0],
    }
    _append_jsonl(_resolution_log(run_state_dir), record)
    return record


def list_protocol_resolutions(run_state_dir: Path) -> list[dict[str, Any]]:
    """Return append-only protocol resolution records."""

    path = _resolution_log(run_state_dir)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def list_current_protocol_violations(run_state_dir: Path, events: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if events is None:
        events = read_events(run_state_dir / "events.jsonl")
    event_violations = [
        event_protocol_violation(event)
        for event in events
        if event.get("type") == "protocol.violation"
    ]
    return unique_protocol_violations([*event_violations, *detect_protocol_violations(run_state_dir)])


def protocol_resolution_overlay(
    run_state_dir: Path,
    violations: list[dict[str, Any]],
) -> dict[str, Any]:
    records = list_protocol_resolutions(run_state_dir)
    resolved: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    matched_resolution_ids: set[str] = set()

    for violation in violations:
        matches = [
            record
            for record in records
            if _resolution_matches_violation(record, violation)
        ]
        if matches:
            item = dict(violation)
            item["resolutions"] = matches
            resolved.append(item)
            matched_resolution_ids.update(str(record.get("resolution_id")) for record in matches)
        else:
            unresolved.append(violation)

    return {
        "records": records,
        "count": len(records),
        "matched_count": len(matched_resolution_ids),
        "unmatched": [
            record
            for record in records
            if str(record.get("resolution_id")) not in matched_resolution_ids
        ],
        "resolved": resolved,
        "unresolved": unresolved,
        "resolved_count": len(resolved),
        "unresolved_count": len(unresolved),
    }


def event_protocol_violation(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    if not isinstance(payload, dict):
        payload = {}
    violation_name = payload.get("violation")
    details = payload.get("details", {})
    if not isinstance(details, dict):
        details = {"details": details}
    if not isinstance(violation_name, str) or not violation_name:
        violation_name, details = _normalize_legacy_protocol_violation_payload(payload, details)
    violation = {
        "violation": violation_name,
        "details": details,
    }
    agent_id = payload.get("agent_id")
    if not agent_id and isinstance(details, dict):
        agent_id = details.get("agent_id")
    if isinstance(agent_id, str) and agent_id:
        violation["agent_id"] = agent_id
    if "workstream" in event:
        violation["workstream"] = event["workstream"]
    return violation


def unique_protocol_violations(violations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for violation in violations:
        key = json.dumps(violation, sort_keys=True)
        unique[key] = violation
    return [unique[key] for key in sorted(unique)]


def violation_matches_selector(violation: dict[str, Any], selector: dict[str, str]) -> bool:
    if violation.get("violation") != selector.get("violation"):
        return False
    for field in ("agent_id", "workstream"):
        selected = selector.get(field)
        if selected is not None and violation.get(field) != selected:
            return False
    return True


def _normalize_legacy_protocol_violation_payload(
    payload: dict[str, Any],
    details: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if payload.get("kind") == "capability_overreach":
        normalized_details = {
            "source": "legacy_protocol_violation_payload",
            "payload": payload,
        }
        for field in ("capability", "requested_mode", "granted_mode", "evidence"):
            if field in payload:
                normalized_details[field] = payload[field]
        return "capability_overreach", normalized_details

    capability_payload = payload if "capability" in payload else details
    if "capability" in capability_payload:
        normalized_details = {
            "source": "legacy_protocol_violation_payload",
            "payload": payload,
        }
        for field in ("capability", "requested_mode", "granted_mode", "evidence"):
            if field in capability_payload:
                normalized_details[field] = capability_payload[field]
        return "capability_overreach", normalized_details
    return "unknown", details


def _resolution_matches_violation(record: dict[str, Any], violation: dict[str, Any]) -> bool:
    matched = record.get("matched_violation")
    if isinstance(matched, dict):
        return matched == violation
    selector = record.get("selector")
    if isinstance(selector, dict) and violation_matches_selector(violation, selector):
        return True
    return False


def _validate_selector(
    *,
    violation: str,
    agent_id: str | None,
    workstream: str | None,
) -> dict[str, str]:
    selector = {"violation": _validate_text(violation, "violation")}
    if agent_id is not None:
        selector["agent_id"] = _validate_text(agent_id, "agent_id")
    if workstream is not None:
        selector["workstream"] = _validate_text(workstream, "workstream")
    return selector


def _validate_resolution_kind(resolution: str) -> None:
    if resolution not in PROTOCOL_RESOLUTION_KINDS:
        raise ProtocolResolutionValidationError(
            "unsupported protocol violation resolution kind: "
            f"{resolution!r}; expected one of {', '.join(sorted(PROTOCOL_RESOLUTION_KINDS))}"
        )


def _validate_text(value: str | None, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProtocolResolutionValidationError(f"protocol violation resolution {field} must not be empty")
    return value.strip()


def _next_resolution_id(run_state_dir: Path) -> str:
    return f"protocol-resolution-{len(list_protocol_resolutions(run_state_dir)) + 1:06d}"


def _resolution_log(run_state_dir: Path) -> Path:
    return run_state_dir / "protocol-resolutions.jsonl"


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
