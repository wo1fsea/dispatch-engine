"""Detached coordinator supervisor helpers."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from .coordinators import (
    COORDINATOR_AGENT_ID,
    CoordinatorLaunchError,
    PROVIDER_PROFILES,
    render_run_dry_run,
    launch_run_coordinator,
)
from .events import utc_timestamp
from .runs import ensure_run_runtime_dirs, resolve_run_dir


SUPERVISOR_SCHEMA_VERSION = 1


def launch_detached_coordinator(
    target: Path,
    *,
    run_id: str | None = None,
    provider: str = "codex",
) -> dict[str, Any]:
    """Start a background supervisor process and return without waiting for completion."""

    dry_run = render_run_dry_run(target, run_id=run_id, provider=provider)
    profile = PROVIDER_PROFILES[dry_run["provider"]]
    repo_root = Path(dry_run["repo_root"])
    run_state_dir = Path(dry_run["state_dir"])
    ensure_run_runtime_dirs(run_state_dir)

    supervisor_path = run_state_dir / "supervisors" / f"{COORDINATOR_AGENT_ID}.json"
    supervisor_stdout_path = run_state_dir / "logs" / f"{COORDINATOR_AGENT_ID}.supervisor.stdout.log"
    supervisor_stderr_path = run_state_dir / "logs" / f"{COORDINATOR_AGENT_ID}.supervisor.stderr.log"
    supervisor_stdout_path.write_text("", encoding="utf-8")
    supervisor_stderr_path.write_text("", encoding="utf-8")
    _write_supervisor(
        supervisor_path,
        _supervisor_record(
            run_state_dir,
            repo_root=repo_root,
            profile=profile,
            supervisor_pid=None,
            supervisor_path=supervisor_path,
            supervisor_stdout_path=supervisor_stdout_path,
            supervisor_stderr_path=supervisor_stderr_path,
            status="starting",
        ),
    )

    argv = [
        sys.executable,
        "-m",
        "dispatch_engine.supervisor",
        "--target",
        str(repo_root),
        "--run-id",
        run_state_dir.name,
        "--provider",
        profile["provider"],
        "--supervisor-path",
        str(supervisor_path),
    ]
    env = _detached_env()
    supervisor_pid = _spawn_detached(
        argv,
        cwd=repo_root,
        env=env,
        stdout_path=supervisor_stdout_path,
        stderr_path=supervisor_stderr_path,
    )

    record = json.loads(supervisor_path.read_text(encoding="utf-8"))
    record["supervisor_pid"] = supervisor_pid
    record["updated_at"] = utc_timestamp()
    if record.get("status") == "starting":
        record["status"] = "running"
    _write_supervisor(supervisor_path, record)

    return {
        "kind": "run_detached",
        "provider": profile["provider"],
        "profile": profile["profile"],
        "run_id": run_state_dir.name,
        "state_dir": str(run_state_dir),
        "repo_root": str(repo_root),
        "supervisor_pid": supervisor_pid,
        "supervisor_path": str(supervisor_path),
        "supervisor_stdout_path": str(supervisor_stdout_path),
        "supervisor_stderr_path": str(supervisor_stderr_path),
        "prompt_path": str(run_state_dir / "prompts" / f"{COORDINATOR_AGENT_ID}.md"),
        "stdout_path": str(run_state_dir / "logs" / f"{COORDINATOR_AGENT_ID}.stdout.log"),
        "stderr_path": str(run_state_dir / "logs" / f"{COORDINATOR_AGENT_ID}.stderr.log"),
    }


def run_supervisor(
    target: Path,
    *,
    run_id: str,
    provider: str,
    supervisor_path: Path,
) -> int:
    """Run the foreground coordinator from a detached supervisor process."""

    run_state_dir = resolve_run_dir(target.resolve(), run_id)
    if run_state_dir is None:
        _finish_supervisor(
            supervisor_path,
            status="failed",
            failure_reason=f"Run not found: {run_id}",
            exit_code=None,
        )
        return 1

    try:
        result = launch_run_coordinator(target, run_id=run_id, provider=provider)
    except CoordinatorLaunchError as exc:
        _finish_supervisor(supervisor_path, status="failed", failure_reason=str(exc), exit_code=None)
        return 1
    except Exception as exc:  # pragma: no cover - defensive supervisor boundary
        _finish_supervisor(
            supervisor_path,
            status="failed",
            failure_reason=f"Supervisor crashed: {exc}",
            exit_code=None,
        )
        raise

    state = result.get("state", "failed")
    exit_code = result.get("exit_code")
    failure_reason = result.get("failure_reason")
    _finish_supervisor(
        supervisor_path,
        status="completed" if state == "completed" else "failed",
        failure_reason=failure_reason,
        exit_code=exit_code,
    )
    return 0 if state == "completed" else 1


def read_supervisors(run_state_dir: Path) -> list[dict[str, Any]]:
    supervisors_dir = run_state_dir / "supervisors"
    if not supervisors_dir.exists():
        return []
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(supervisors_dir.glob("*.json"))
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dispatch Engine detached supervisor.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--supervisor-path", required=True)
    args = parser.parse_args(argv)
    return run_supervisor(
        Path(args.target),
        run_id=args.run_id,
        provider=args.provider,
        supervisor_path=Path(args.supervisor_path),
    )


def _detached_env() -> dict[str, str]:
    env = dict(os.environ)
    scripts_dir = Path(__file__).resolve().parents[1]
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(scripts_dir) if not current else f"{scripts_dir}{os.pathsep}{current}"
    return env


def _spawn_detached(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
) -> int:
    if hasattr(os, "posix_spawn"):
        file_actions = [
            (
                os.POSIX_SPAWN_OPEN,
                1,
                str(stdout_path),
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                0o666,
            ),
            (
                os.POSIX_SPAWN_OPEN,
                2,
                str(stderr_path),
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                0o666,
            ),
        ]
        old_cwd = Path.cwd()
        try:
            os.chdir(cwd)
            return os.posix_spawn(argv[0], argv, env, file_actions=file_actions, setsid=True)
        finally:
            os.chdir(old_cwd)

    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
        "w",
        encoding="utf-8",
    ) as stderr:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
            close_fds=True,
        )
    process._child_created = False  # type: ignore[attr-defined]
    return process.pid


def _supervisor_record(
    run_state_dir: Path,
    *,
    repo_root: Path,
    profile: dict[str, str],
    supervisor_pid: int | None,
    supervisor_path: Path,
    supervisor_stdout_path: Path,
    supervisor_stderr_path: Path,
    status: str,
) -> dict[str, Any]:
    now = utc_timestamp()
    return {
        "schema_version": SUPERVISOR_SCHEMA_VERSION,
        "agent_id": COORDINATOR_AGENT_ID,
        "run_id": run_state_dir.name,
        "repo_root": str(repo_root),
        "provider": profile["provider"],
        "profile": profile["profile"],
        "status": status,
        "supervisor_pid": supervisor_pid,
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "supervisor_path": _run_relative_file(run_state_dir, supervisor_path),
        "supervisor_stdout_path": _run_relative_file(run_state_dir, supervisor_stdout_path),
        "supervisor_stderr_path": _run_relative_file(run_state_dir, supervisor_stderr_path),
    }


def _finish_supervisor(
    supervisor_path: Path,
    *,
    status: str,
    failure_reason: str | None,
    exit_code: int | None,
) -> None:
    record = json.loads(supervisor_path.read_text(encoding="utf-8"))
    now = utc_timestamp()
    record["status"] = status
    record["updated_at"] = now
    record["completed_at"] = now
    record["exit_code"] = exit_code
    if failure_reason:
        record["failure_reason"] = failure_reason
    elif "failure_reason" in record:
        del record["failure_reason"]
    _write_supervisor(supervisor_path, record)


def _write_supervisor(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def _run_relative_file(run_state_dir: Path, path: Path) -> str:
    return f".dispatch/runs/{run_state_dir.name}/{path.relative_to(run_state_dir)}"


if __name__ == "__main__":
    raise SystemExit(main())
