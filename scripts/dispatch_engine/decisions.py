"""Decision and blocker state helpers for Dispatch Engine runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .events import append_event, decision_requested, utc_timestamp

DECISION_SCHEMA_VERSION = 1
OPEN_BLOCKER_STATUSES = frozenset({"open", "blocked"})


class DecisionBlockerValidationError(ValueError):
    """Raised when a decision or blocker record is invalid."""


def record_decision_request(
    run_state_dir: Path,
    *,
    decision_id: str,
    question: str,
    reason: str | None = None,
    workstream: str | None = None,
    actor: str = "dispatch-engine",
) -> dict[str, Any]:
    """Append a pending decision request and emit a decision event."""

    _validate_record_id(decision_id, "decision_id")
    if not question:
        raise DecisionBlockerValidationError("decision question must not be empty")

    now = utc_timestamp()
    record: dict[str, Any] = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "decision_id": decision_id,
        "id": decision_id,
        "status": "pending",
        "question": question,
        "created_at": now,
        "updated_at": now,
        "actor": actor,
    }
    if reason is not None:
        record["reason"] = reason
    if workstream is not None:
        record["workstream"] = workstream

    _append_jsonl(_decisions_log(run_state_dir), record)
    decision_requested(
        run_state_dir / "events.jsonl",
        decision_id=decision_id,
        question=question,
        reason=reason,
        workstream=workstream,
        actor=actor,
    )
    return record


def resolve_decision(
    run_state_dir: Path,
    decision_id: str,
    *,
    resolution: str,
    actor: str = "dispatch-engine",
) -> dict[str, Any]:
    """Append a decision resolution record."""

    _validate_record_id(decision_id, "decision_id")
    if not resolution:
        raise DecisionBlockerValidationError("decision resolution must not be empty")
    existing = _require_latest(list_decisions(run_state_dir), "decision_id", decision_id)

    now = utc_timestamp()
    record = {
        **existing,
        "status": "resolved",
        "resolution": resolution,
        "resolved_at": now,
        "updated_at": now,
        "resolved_by": actor,
    }
    _append_jsonl(_decisions_log(run_state_dir), record)
    append_event(
        run_state_dir / "events.jsonl",
        "decision.resolved",
        actor=actor,
        workstream=record.get("workstream"),
        payload={"decision_id": decision_id, "resolution": resolution},
    )
    return record


def list_decisions(run_state_dir: Path) -> list[dict[str, Any]]:
    """Return the latest record for each decision id."""

    return _latest_by_id(_read_jsonl(_decisions_log(run_state_dir), "decision_id"), "decision_id")


def list_pending_decisions(run_state_dir: Path) -> list[dict[str, Any]]:
    return [item for item in list_decisions(run_state_dir) if item.get("status") == "pending"]


def record_blocker(
    run_state_dir: Path,
    *,
    blocker_id: str,
    summary: str,
    workstream: str | None = None,
    severity: str = "blocking",
    actor: str = "dispatch-engine",
) -> dict[str, Any]:
    """Append an unresolved blocker record and emit a blocker event."""

    _validate_record_id(blocker_id, "blocker_id")
    if not summary:
        raise DecisionBlockerValidationError("blocker summary must not be empty")

    now = utc_timestamp()
    record: dict[str, Any] = {
        "schema_version": DECISION_SCHEMA_VERSION,
        "blocker_id": blocker_id,
        "id": blocker_id,
        "status": "open",
        "summary": summary,
        "severity": severity,
        "created_at": now,
        "updated_at": now,
        "actor": actor,
    }
    if workstream is not None:
        record["workstream"] = workstream

    _append_jsonl(_blockers_log(run_state_dir), record)
    append_event(
        run_state_dir / "events.jsonl",
        "blocker.recorded",
        actor=actor,
        workstream=workstream,
        payload={"blocker_id": blocker_id, "summary": summary, "severity": severity},
    )
    return record


def resolve_blocker(
    run_state_dir: Path,
    blocker_id: str,
    *,
    resolution: str,
    actor: str = "dispatch-engine",
) -> dict[str, Any]:
    """Append a blocker resolution record."""

    _validate_record_id(blocker_id, "blocker_id")
    if not resolution:
        raise DecisionBlockerValidationError("blocker resolution must not be empty")
    existing = _require_latest(list_blockers(run_state_dir), "blocker_id", blocker_id)

    now = utc_timestamp()
    record = {
        **existing,
        "status": "resolved",
        "resolution": resolution,
        "resolved_at": now,
        "updated_at": now,
        "resolved_by": actor,
    }
    _append_jsonl(_blockers_log(run_state_dir), record)
    append_event(
        run_state_dir / "events.jsonl",
        "blocker.resolved",
        actor=actor,
        workstream=record.get("workstream"),
        payload={"blocker_id": blocker_id, "resolution": resolution},
    )
    return record


def list_blockers(run_state_dir: Path) -> list[dict[str, Any]]:
    """Return the latest record for each blocker id."""

    return _latest_by_id(_read_jsonl(_blockers_log(run_state_dir), "blocker_id"), "blocker_id")


def list_unresolved_blockers(run_state_dir: Path) -> list[dict[str, Any]]:
    return [item for item in list_blockers(run_state_dir) if item.get("status") in OPEN_BLOCKER_STATUSES]


def validate_decision_blocker_state(run_state_dir: Path) -> dict[str, Any]:
    """Return a mechanical validation signal for unresolved blockers."""

    blockers = list_unresolved_blockers(run_state_dir)
    return {
        "status": "blocked" if blockers else "ok",
        "unresolved_blockers": len(blockers),
        "blockers": blockers,
    }


def _decisions_log(run_state_dir: Path) -> Path:
    return run_state_dir / "decisions.jsonl"


def _blockers_log(run_state_dir: Path) -> Path:
    return run_state_dir / "blockers.jsonl"


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _read_jsonl(path: Path, id_field: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            if id_field not in record and "id" in record:
                record[id_field] = record["id"]
            records.append(record)
    return records


def _latest_by_id(records: list[dict[str, Any]], id_field: str) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for record in records:
        record_id = record.get(id_field) or record.get("id")
        if not record_id:
            continue
        if record_id not in latest:
            order.append(record_id)
        latest[record_id] = record
    return [latest[record_id] for record_id in order]


def _require_latest(records: list[dict[str, Any]], id_field: str, record_id: str) -> dict[str, Any]:
    for record in records:
        if record.get(id_field) == record_id or record.get("id") == record_id:
            return record
    raise DecisionBlockerValidationError(f"record not found: {record_id}")


def _validate_record_id(record_id: str, field: str) -> None:
    if not record_id or "/" in record_id or "\\" in record_id:
        raise DecisionBlockerValidationError(f"invalid {field}: {record_id!r}")
