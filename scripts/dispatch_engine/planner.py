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
        "decisions": [],
    }

    _write_plan(state_dir, plan)
    return plan


def _write_plan(state_dir: Path, plan: dict) -> None:
    initialize_run_dir(state_dir)
    (state_dir / "run.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
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
