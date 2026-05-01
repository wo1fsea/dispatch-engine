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
