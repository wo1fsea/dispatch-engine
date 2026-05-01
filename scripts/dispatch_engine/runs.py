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


def initialize_run_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False)
    (path / "workstreams").mkdir()
    (path / "artifacts").mkdir()
    (path / "events.jsonl").write_text("")
    (path / "decisions.jsonl").write_text("")
