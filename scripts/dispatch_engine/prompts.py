"""Central prompt template loading and rendering for Dispatch Engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

DRY_RUN_PROMPT_MARKER = "<dry-run-generated-coordinator-prompt>"
PROMPT_ROOT = Path(__file__).resolve().parents[2] / "references" / "prompts"
COORDINATOR_PROTOCOL_TEMPLATE = "coordinator-protocol.md"


def render_coordinator_prompt(
    run: dict[str, Any],
    *,
    repo_root: Path,
    run_state_dir: Path,
    profile: dict[str, str],
) -> str:
    """Render the provider coordinator protocol prompt from the central template."""

    template = _load_prompt_template(COORDINATOR_PROTOCOL_TEMPLATE)
    plan = run.get("plan", {})
    return template.format(
        provider=profile["provider"],
        profile=profile["profile"],
        provider_context=profile["provider_context"],
        repo_root=repo_root,
        run_id=run_state_dir.name,
        state_dir=run_state_dir,
        plan_source=plan.get("source_path", "(unknown)"),
        objective=run.get("objective", "(unknown)"),
        report_path=f".dispatch/runs/{run_state_dir.name}/reports/coordinator-001.json",
        workstreams=_render_workstreams(run.get("workstreams", [])),
    )


def prompt_template_path(name: str) -> Path:
    """Return a prompt template path without loading it."""

    path = PROMPT_ROOT / name
    if not path.is_file():
        raise FileNotFoundError(f"prompt template not found: {path}")
    return path


def _load_prompt_template(name: str) -> str:
    return prompt_template_path(name).read_text(encoding="utf-8")


def _render_workstreams(workstreams: list[dict[str, Any]]) -> str:
    if not workstreams:
        return "- (none)"
    lines = []
    for item in workstreams:
        lines.append(
            "- {id}: {title} [{status}] files={files} depends_on={depends_on}".format(
                id=item.get("id", "unknown"),
                title=item.get("title", item.get("id", "unknown")),
                status=item.get("status", "unknown"),
                files=", ".join(item.get("files", [])) or "(none)",
                depends_on=", ".join(item.get("depends_on", [])) or "(none)",
            )
        )
    return "\n".join(lines)
