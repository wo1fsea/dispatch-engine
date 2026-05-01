"""Dry-run workstream planning for Dispatch Engine."""

from __future__ import annotations

import json
from pathlib import Path

from .events import append_event, utc_timestamp
from .runs import initialize_run_dir, new_run_id, run_dir


def plan_objective(target: Path, objective: str, inspection: dict) -> dict:
    repo_root = target.resolve()
    run_id = new_run_id()
    state_dir = run_dir(repo_root, run_id)
    now = utc_timestamp()
    workstream = {
        "id": "01-implementation",
        "title": "Implement objective",
        "scope": objective,
        "files": [],
        "depends_on": [],
        "status": "planned",
        "validation": inspection.get("validation_hints", []),
        "created_at": now,
        "updated_at": now,
    }
    decisions = _pending_decisions(objective, now)
    plan = {
        "kind": "plan",
        "run_id": run_id,
        "repo_root": str(repo_root),
        "state_dir": str(state_dir),
        "objective": objective,
        "status": "planned",
        "created_at": now,
        "updated_at": now,
        "workstreams": [workstream],
        "decisions": decisions,
    }

    _write_plan(state_dir, plan)
    return plan


def _write_plan(state_dir: Path, plan: dict) -> None:
    initialize_run_dir(state_dir)
    (state_dir / "run.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    decisions_log = state_dir / "decisions.jsonl"
    for decision in plan["decisions"]:
        with decisions_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(decision, sort_keys=True) + "\n")
    for workstream in plan["workstreams"]:
        workstream_path = state_dir / "workstreams" / f"{workstream['id']}.json"
        workstream_path.write_text(json.dumps(workstream, indent=2, sort_keys=True) + "\n")
    event_log = state_dir / "events.jsonl"
    append_event(
        event_log,
        "run.created",
        payload={"objective": plan["objective"], "run_id": plan["run_id"]},
    )
    for workstream in plan["workstreams"]:
        append_event(
            event_log,
            "workstream.planned",
            workstream=workstream["id"],
            payload={"title": workstream["title"]},
        )
    for decision in plan["decisions"]:
        append_event(
            event_log,
            "decision.created",
            payload={"decision_id": decision["id"], "question": decision["question"]},
        )


def _pending_decisions(objective: str, timestamp: str) -> list[dict]:
    reason = _pending_decision_reason(objective)
    if reason is None:
        return []
    return [
        {
            "id": "decision-001",
            "question": "Confirm whether this objective should remain one workstream or be split before execution.",
            "reason": reason,
            "status": "pending",
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    ]


def _pending_decision_reason(objective: str) -> str | None:
    text = objective.lower()
    has_ui = any(term in text for term in ("ui", "frontend", "front-end", "interface", "flow"))
    has_backend = any(term in text for term in ("backend", "back-end", "api", "server", "database"))
    if has_ui and has_backend:
        return "Objective mentions backend API and UI work; confirm scope before splitting or execution."

    risky_terms = (
        "migration",
        "schema",
        "auth",
        "permission",
        "security",
        "billing",
        "worker adapter",
        "event protocol",
        "parallel agent",
        "parallel agents",
    )
    for term in risky_terms:
        if term in text:
            return f"Objective mentions {term}; confirm risk and execution boundary before proceeding."
    return None
