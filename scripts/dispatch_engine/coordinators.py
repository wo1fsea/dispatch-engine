"""Provider coordinator rendering and live supervision for Dispatch Engine runs."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .agents import register_agent
from .events import coordinator_completed, coordinator_failed, coordinator_started, utc_timestamp
from .prompts import (
    DRY_RUN_PROMPT_MARKER,
    coordinator_prompt_instruction,
    render_coordinator_prompt,
    write_coordinator_prompt_snapshot,
)
from .runs import ensure_run_runtime_dirs, resolve_run_dir

COORDINATOR_AGENT_ID = "coordinator-001"

PROVIDER_PROFILES: dict[str, dict[str, Any]] = {
    "codex": {
        "provider": "codex",
        "profile": "codex-exec",
        "executable": "codex",
        "provider_context": "Codex CLI launched with codex exec --sandbox danger-full-access.",
        "coordinator_args": ["exec", "--sandbox", "danger-full-access"],
    },
    "claude": {
        "provider": "claude",
        "profile": "claude-p",
        "executable": "claude",
        "provider_context": (
            "Claude CLI launched with --dangerously-skip-permissions "
            "--permission-mode bypassPermissions -p."
        ),
        "coordinator_args": [
            "--dangerously-skip-permissions",
            "--permission-mode",
            "bypassPermissions",
            "-p",
        ],
    },
}


class CoordinatorLaunchError(ValueError):
    """Raised when a coordinator launch request cannot be rendered."""


def render_run_dry_run(
    target: Path,
    *,
    run_id: str | None = None,
    provider: str = "codex",
) -> dict[str, Any]:
    """Render a provider coordinator command without launching or writing state."""

    profile = _provider_profile(provider)
    repo_root = target.resolve()
    run_state_dir = resolve_run_dir(repo_root, run_id)
    if run_state_dir is None:
        if run_id:
            raise CoordinatorLaunchError(f"Run not found: {run_id}")
        raise CoordinatorLaunchError("No Dispatch Engine runs found.")

    run = _read_run(run_state_dir)
    prompt_text = render_coordinator_prompt(
        run,
        repo_root=repo_root,
        run_state_dir=run_state_dir,
        profile=profile,
    )
    argv = _render_argv(
        profile,
        repo_root=repo_root,
        prompt_path=DRY_RUN_PROMPT_MARKER,
    )
    executable_path = shutil.which(profile["executable"])
    warnings = []
    if executable_path is None:
        warnings.append(f"Executable not found on PATH: {profile['executable']}")

    return {
        "kind": "run_dry_run",
        "provider": profile["provider"],
        "profile": profile["profile"],
        "executable": profile["executable"],
        "executable_path": executable_path,
        "executable_found": executable_path is not None,
        "argv": argv,
        "run_id": run_state_dir.name,
        "state_dir": str(run_state_dir),
        "repo_root": str(repo_root),
        "prompt_path": DRY_RUN_PROMPT_MARKER,
        "prompt_preview": prompt_text,
        "prompt_text": prompt_text,
        "state_writes": [],
        "warnings": warnings,
    }


def launch_run_coordinator(
    target: Path,
    *,
    run_id: str | None = None,
    provider: str = "codex",
) -> dict[str, Any]:
    """Launch a provider coordinator in the foreground and record runtime state."""

    profile = _provider_profile(provider)
    repo_root = target.resolve()
    run_state_dir = resolve_run_dir(repo_root, run_id)
    if run_state_dir is None:
        if run_id:
            raise CoordinatorLaunchError(f"Run not found: {run_id}")
        raise CoordinatorLaunchError("No Dispatch Engine runs found.")

    ensure_run_runtime_dirs(run_state_dir)
    run = _read_run(run_state_dir)
    prompt_text = render_coordinator_prompt(
        run,
        repo_root=repo_root,
        run_state_dir=run_state_dir,
        profile=profile,
    )
    prompt_path = write_coordinator_prompt_snapshot(run_state_dir, prompt_text)
    stdout_path = run_state_dir / "logs" / f"{COORDINATOR_AGENT_ID}.stdout.log"
    stderr_path = run_state_dir / "logs" / f"{COORDINATOR_AGENT_ID}.stderr.log"
    stdout_path.write_text("", encoding="utf-8")
    stderr_path.write_text("", encoding="utf-8")

    argv = _render_argv(
        profile,
        repo_root=repo_root,
        prompt_path=str(prompt_path),
    )
    stdout_run_path = _run_relative_file(run_state_dir, stdout_path)
    stderr_run_path = _run_relative_file(run_state_dir, stderr_path)
    register_agent(
        run_state_dir,
        agent_id=COORDINATOR_AGENT_ID,
        role="coordinator",
        provider=profile["provider"],
        profile=profile["profile"],
        status="running",
        prompt_path=_run_relative_file(run_state_dir, prompt_path),
        stdout_path=stdout_run_path,
        stderr_path=stderr_run_path,
    )
    coordinator_started(
        run_state_dir / "events.jsonl",
        agent_id=COORDINATOR_AGENT_ID,
        provider=profile["provider"],
        profile=profile["profile"],
    )

    executable_path = shutil.which(profile["executable"])
    if executable_path is None:
        reason = f"Executable not found on PATH: {profile['executable']}"
        stderr_path.write_text(reason + "\n", encoding="utf-8")
        _mark_coordinator_finished(run_state_dir, status="failed", reason=reason)
        coordinator_failed(
            run_state_dir / "events.jsonl",
            agent_id=COORDINATOR_AGENT_ID,
            provider=profile["provider"],
            profile=profile["profile"],
            exit_code=None,
            stdout_path=stdout_run_path,
            stderr_path=stderr_run_path,
            reason=reason,
        )
        return _live_payload(
            profile,
            repo_root=repo_root,
            run_state_dir=run_state_dir,
            prompt_path=prompt_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            argv=argv,
            executable_path=None,
            exit_code=None,
            state="failed",
            failure_reason=reason,
        )

    try:
        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open(
            "w",
            encoding="utf-8",
        ) as stderr:
            completed = subprocess.run(
                argv,
                cwd=repo_root,
                stdout=stdout,
                stderr=stderr,
                check=False,
            )
        exit_code: int | None = completed.returncode
    except FileNotFoundError:
        reason = f"Executable not found on PATH: {profile['executable']}"
        stderr_path.write_text(reason + "\n", encoding="utf-8")
        exit_code = None
    except OSError as exc:
        reason = f"Failed to launch {profile['executable']}: {exc}"
        stderr_path.write_text(reason + "\n", encoding="utf-8")
        exit_code = None
    else:
        reason = f"Coordinator exited with exit code {exit_code}" if exit_code != 0 else None

    if exit_code == 0:
        _mark_coordinator_finished(run_state_dir, status="completed")
        coordinator_completed(
            run_state_dir / "events.jsonl",
            agent_id=COORDINATOR_AGENT_ID,
            provider=profile["provider"],
            profile=profile["profile"],
            exit_code=exit_code,
            stdout_path=stdout_run_path,
            stderr_path=stderr_run_path,
        )
        state = "completed"
    else:
        assert reason is not None
        _mark_coordinator_finished(run_state_dir, status="failed", reason=reason)
        coordinator_failed(
            run_state_dir / "events.jsonl",
            agent_id=COORDINATOR_AGENT_ID,
            provider=profile["provider"],
            profile=profile["profile"],
            exit_code=exit_code,
            stdout_path=stdout_run_path,
            stderr_path=stderr_run_path,
            reason=reason,
        )
        state = "failed"

    return _live_payload(
        profile,
        repo_root=repo_root,
        run_state_dir=run_state_dir,
        prompt_path=prompt_path,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        argv=argv,
        executable_path=executable_path,
        exit_code=exit_code,
        state=state,
        failure_reason=reason,
    )


def _provider_profile(provider: str) -> dict[str, Any]:
    try:
        return PROVIDER_PROFILES[provider]
    except KeyError as exc:
        supported = ", ".join(sorted(PROVIDER_PROFILES))
        raise CoordinatorLaunchError(
            f"unsupported provider: {provider}; supported providers: {supported}"
        ) from exc


def _read_run(run_state_dir: Path) -> dict[str, Any]:
    run_file = run_state_dir / "run.json"
    if not run_file.exists():
        raise CoordinatorLaunchError(f"Run has no run.json: {run_state_dir}")
    return json.loads(run_file.read_text(encoding="utf-8"))


def _render_argv(
    profile: dict[str, Any],
    *,
    repo_root: Path,
    prompt_path: str,
) -> list[str]:
    provider = profile["provider"]
    instruction = _provider_instruction(prompt_path)
    if provider == "codex":
        return [
            profile["executable"],
            *profile["coordinator_args"],
            "--cd",
            str(repo_root),
            instruction,
        ]
    if provider == "claude":
        return [profile["executable"], *profile["coordinator_args"], instruction]
    raise CoordinatorLaunchError(f"malformed provider profile: {provider}")


def _provider_instruction(prompt_path: str) -> str:
    return coordinator_prompt_instruction(prompt_path)


def _live_payload(
    profile: dict[str, Any],
    *,
    repo_root: Path,
    run_state_dir: Path,
    prompt_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    argv: list[str],
    executable_path: str | None,
    exit_code: int | None,
    state: str,
    failure_reason: str | None,
) -> dict[str, Any]:
    payload = {
        "kind": "run_live",
        "provider": profile["provider"],
        "profile": profile["profile"],
        "executable": profile["executable"],
        "executable_path": executable_path,
        "executable_found": executable_path is not None,
        "argv": argv,
        "run_id": run_state_dir.name,
        "state_dir": str(run_state_dir),
        "repo_root": str(repo_root),
        "state": state,
        "exit_code": exit_code,
        "prompt_path": str(prompt_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
    }
    if failure_reason is not None:
        payload["failure_reason"] = failure_reason
    return payload


def _mark_coordinator_finished(
    run_state_dir: Path,
    *,
    status: str,
    reason: str | None = None,
) -> None:
    path = run_state_dir / "agents" / f"{COORDINATOR_AGENT_ID}.json"
    agent = json.loads(path.read_text(encoding="utf-8"))
    now = utc_timestamp()
    agent["status"] = status
    agent["updated_at"] = now
    agent["completed_at"] = now
    if reason is not None:
        agent["failure_reason"] = reason
    elif "failure_reason" in agent:
        del agent["failure_reason"]
    path.write_text(json.dumps(agent, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _run_relative_file(run_state_dir: Path, path: Path) -> str:
    return f".dispatch/runs/{run_state_dir.name}/{path.relative_to(run_state_dir)}"
