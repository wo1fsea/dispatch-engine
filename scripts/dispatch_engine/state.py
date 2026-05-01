"""Run-state helpers for Dispatch Engine."""

from __future__ import annotations

import json
from pathlib import Path


def latest_run_summary(target: Path) -> dict:
    root = target.resolve()
    runs = root / ".dispatch" / "runs"
    if not runs.exists():
        return {"kind": "status", "summary": "No Dispatch Engine runs found."}

    run_dirs = sorted([p for p in runs.iterdir() if p.is_dir()])
    if not run_dirs:
        return {"kind": "status", "summary": "No Dispatch Engine runs found."}

    latest = run_dirs[-1]
    run_file = latest / "run.json"
    if not run_file.exists():
        return {"kind": "status", "summary": f"Latest run has no run.json: {latest}"}

    data = json.loads(run_file.read_text())
    workstreams = data.get("workstreams", [])
    return {
        "kind": "status",
        "summary": (
            f"Latest run {data.get('run_id')} has {len(workstreams)} workstream(s): "
            f"{data.get('objective')}"
        ),
    }
