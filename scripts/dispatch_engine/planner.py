"""Dry-run workstream planning for Dispatch Engine."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def plan_objective(target: Path, objective: str, inspection: dict) -> dict:
    repo_root = target.resolve()
    run_id = _run_id()
    state_dir = repo_root / ".dispatch" / "runs" / run_id
    workstream = {
        "id": "01-implementation",
        "title": "Implement objective",
        "scope": objective,
        "files": [],
        "depends_on": [],
        "status": "planned",
        "validation": inspection.get("validation_hints", []),
    }
    plan = {
        "kind": "plan",
        "run_id": run_id,
        "repo_root": str(repo_root),
        "state_dir": str(state_dir),
        "objective": objective,
        "workstreams": [workstream],
        "decisions": [],
    }

    _write_plan(state_dir, plan)
    return plan


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_plan(state_dir: Path, plan: dict) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "run.json").write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    (state_dir / "events.jsonl").write_text(
        json.dumps(
            {
                "ts": plan["run_id"],
                "type": "plan.created",
                "actor": "dispatch-engine",
                "payload": {"objective": plan["objective"]},
            },
            sort_keys=True,
        )
        + "\n"
    )
