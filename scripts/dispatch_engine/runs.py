"""Run-state filesystem helpers for Dispatch Engine."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def new_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def runs_dir(repo_root: Path) -> Path:
    return repo_root / ".dispatch" / "runs"


def run_dir(repo_root: Path, run_id: str) -> Path:
    return runs_dir(repo_root) / run_id


def latest_run_dir(repo_root: Path) -> Path | None:
    root = runs_dir(repo_root)
    if not root.exists():
        return None
    run_dirs = sorted([path for path in root.iterdir() if path.is_dir()])
    if not run_dirs:
        return None
    return run_dirs[-1]


def resolve_run_dir(repo_root: Path, run_id: str | None = None) -> Path | None:
    if run_id:
        path = run_dir(repo_root, run_id)
        return path if path.exists() else None
    return latest_run_dir(repo_root)


def initialize_run_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False)
    (path / "workstreams").mkdir()
    (path / "artifacts").mkdir()
    (path / "events.jsonl").write_text("")
    (path / "decisions.jsonl").write_text("")
