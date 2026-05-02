"""Central prompt template loading and rendering for Dispatch Engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DRY_RUN_PROMPT_MARKER = "<dry-run-generated-coordinator-prompt>"
PROMPT_ROOT = Path(__file__).resolve().parents[2] / "references" / "prompts"
COORDINATOR_PROTOCOL_TEMPLATE = "coordinator-protocol.md"
WORKER_PROTOCOL_TEMPLATE = "worker-protocol.md"
REVIEWER_PROTOCOL_TEMPLATE = "reviewer-protocol.md"
VALIDATOR_PROTOCOL_TEMPLATE = "validator-protocol.md"
COORDINATOR_AGENT_ID = "coordinator-001"


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


def render_worker_prompt(
    run: dict[str, Any],
    *,
    repo_root: Path,
    run_state_dir: Path,
    agent: dict[str, Any],
    workstream: dict[str, Any],
) -> str:
    """Render the worker protocol prompt from the central template."""

    template = _load_prompt_template(WORKER_PROTOCOL_TEMPLATE)
    return template.format(
        repo_root=repo_root,
        run_id=run_state_dir.name,
        state_dir=run_state_dir,
        objective=run.get("objective", "(unknown)"),
        agent_id=agent.get("agent_id", "(unknown)"),
        provider=agent.get("provider", "(unknown)"),
        profile=agent.get("profile", "(unknown)"),
        workstream_id=workstream.get("id", agent.get("workstream", "(unknown)")),
        workstream_title=workstream.get("title", workstream.get("id", "(unknown)")),
        workstream_scope=workstream.get("scope", "(none)"),
        assigned_files=_render_list(agent.get("assigned_files", [])),
        allowed_write_roots=_render_list(agent.get("allowed_write_roots", [])),
        depends_on=_render_list(workstream.get("depends_on", [])),
        validation=_render_list(workstream.get("validation", [])),
        report_path=agent.get(
            "report_path",
            f".dispatch/runs/{run_state_dir.name}/reports/{agent.get('agent_id', 'worker')}.json",
        ),
    )


def render_reviewer_prompt(
    run: dict[str, Any],
    *,
    repo_root: Path,
    run_state_dir: Path,
    agent: dict[str, Any],
    workstream: dict[str, Any],
    worker_report: dict[str, Any] | None = None,
) -> str:
    """Render the reviewer protocol prompt from the central template."""

    template = _load_prompt_template(REVIEWER_PROTOCOL_TEMPLATE)
    return template.format(
        repo_root=repo_root,
        run_id=run_state_dir.name,
        state_dir=run_state_dir,
        objective=run.get("objective", "(unknown)"),
        agent_id=agent.get("agent_id", "(unknown)"),
        provider=agent.get("provider", "(unknown)"),
        profile=agent.get("profile", "(unknown)"),
        workstream_id=workstream.get("id", agent.get("workstream", "(unknown)")),
        workstream_title=workstream.get("title", workstream.get("id", "(unknown)")),
        workstream_scope=workstream.get("scope", "(none)"),
        assigned_files=_render_list(agent.get("assigned_files", [])),
        allowed_write_roots=_render_list(agent.get("allowed_write_roots", [])),
        validation=_render_list(workstream.get("validation", [])),
        worker_report=_render_json(worker_report or {}),
        report_path=agent.get(
            "report_path",
            f".dispatch/runs/{run_state_dir.name}/reviews/{agent.get('agent_id', 'reviewer')}.json",
        ),
    )


def render_validator_prompt(
    run: dict[str, Any],
    *,
    repo_root: Path,
    run_state_dir: Path,
    agent: dict[str, Any],
    workstream: dict[str, Any],
    review_report: dict[str, Any] | None = None,
) -> str:
    """Render the validator protocol prompt from the central template."""

    template = _load_prompt_template(VALIDATOR_PROTOCOL_TEMPLATE)
    return template.format(
        repo_root=repo_root,
        run_id=run_state_dir.name,
        state_dir=run_state_dir,
        objective=run.get("objective", "(unknown)"),
        agent_id=agent.get("agent_id", "(unknown)"),
        provider=agent.get("provider", "(unknown)"),
        profile=agent.get("profile", "(unknown)"),
        workstream_id=workstream.get("id", agent.get("workstream", "(unknown)")),
        workstream_title=workstream.get("title", workstream.get("id", "(unknown)")),
        workstream_scope=workstream.get("scope", "(none)"),
        validation=_render_list(workstream.get("validation", [])),
        review_report=_render_json(review_report or {}),
        report_path=agent.get(
            "report_path",
            f".dispatch/runs/{run_state_dir.name}/validation/{agent.get('agent_id', 'validator')}.json",
        ),
    )


def write_worker_prompt_snapshot(
    run_state_dir: Path,
    agent: dict[str, Any],
    prompt_text: str,
) -> Path:
    """Write a rendered worker prompt snapshot under the run state directory."""

    prompt_path = _agent_prompt_path(run_state_dir, agent)
    prompt_path.parent.mkdir(exist_ok=True)
    prompt_path.write_text(prompt_text, encoding="utf-8")
    return prompt_path


def write_agent_prompt_snapshot(
    run_state_dir: Path,
    agent: dict[str, Any],
    prompt_text: str,
) -> Path:
    """Write a rendered agent prompt snapshot under the run state directory."""

    return write_worker_prompt_snapshot(run_state_dir, agent, prompt_text)


def write_coordinator_prompt_snapshot(
    run_state_dir: Path,
    prompt_text: str,
) -> Path:
    """Write the rendered coordinator prompt snapshot under the run state directory."""

    prompt_path = run_state_dir / "prompts" / f"{COORDINATOR_AGENT_ID}.md"
    prompt_path.parent.mkdir(exist_ok=True)
    prompt_path.write_text(prompt_text, encoding="utf-8")
    return prompt_path


def coordinator_prompt_instruction(prompt_path: Path | str) -> str:
    """Return the short provider instruction that points to a coordinator prompt snapshot."""

    return (
        "Read and follow the Dispatch Engine coordinator instructions in this file: "
        f"{prompt_path}"
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


def _render_list(items: list[Any]) -> str:
    if not items:
        return "- (none)"
    return "\n".join(f"- {item}" for item in items)


def _render_json(data: dict[str, Any]) -> str:
    if not data:
        return "{}"
    return json.dumps(data, indent=2, sort_keys=True)


def _agent_prompt_path(run_state_dir: Path, agent: dict[str, Any]) -> Path:
    prompt_path = agent.get("prompt_path")
    prefix = f".dispatch/runs/{run_state_dir.name}/"
    if isinstance(prompt_path, str) and prompt_path.startswith(prefix):
        return run_state_dir / prompt_path.removeprefix(prefix)
    return run_state_dir / "prompts" / f"{agent.get('agent_id', 'worker')}.md"
