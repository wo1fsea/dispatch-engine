"""Provider coordinator dry-run rendering for Dispatch Engine runs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .prompts import DRY_RUN_PROMPT_MARKER, render_coordinator_prompt
from .runs import resolve_run_dir

PROVIDER_PROFILES: dict[str, dict[str, str]] = {
    "codex": {
        "provider": "codex",
        "profile": "codex-exec",
        "executable": "codex",
        "provider_context": "Codex CLI launched with codex exec.",
    },
    "claude": {
        "provider": "claude",
        "profile": "claude-p",
        "executable": "claude",
        "provider_context": "Claude CLI launched with claude -p.",
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
    argv = _render_argv(profile, repo_root=repo_root, prompt_text=prompt_text)
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


def _provider_profile(provider: str) -> dict[str, str]:
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


def _render_argv(profile: dict[str, str], *, repo_root: Path, prompt_text: str) -> list[str]:
    provider = profile["provider"]
    if provider == "codex":
        return [
            profile["executable"],
            "exec",
            "--prompt-file",
            DRY_RUN_PROMPT_MARKER,
            "--cwd",
            str(repo_root),
        ]
    if provider == "claude":
        return [profile["executable"], "-p", prompt_text]
    raise CoordinatorLaunchError(f"malformed provider profile: {provider}")
