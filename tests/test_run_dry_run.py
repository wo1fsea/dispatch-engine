from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.cli import main
from dispatch_engine.coordinators import CoordinatorLaunchError, render_run_dry_run
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.prompts import COORDINATOR_PROTOCOL_TEMPLATE, prompt_template_path


class RunDryRunTests(unittest.TestCase):
    def test_default_provider_renders_codex_for_latest_run_without_state_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            first = _import_plan(repo, plan_id="plan-001", objective="first objective")
            latest = _import_plan(repo, plan_id="plan-002", objective="latest objective")
            before = _state_snapshot(repo)

            rendered = render_run_dry_run(repo)

            self.assertEqual(rendered["kind"], "run_dry_run")
            self.assertEqual(rendered["provider"], "codex")
            self.assertEqual(rendered["profile"], "codex-exec")
            self.assertEqual(rendered["executable"], "codex")
            self.assertEqual(rendered["run_id"], latest["run_id"])
            self.assertNotEqual(rendered["run_id"], first["run_id"])
            self.assertEqual(rendered["repo_root"], str(repo.resolve()))
            self.assertEqual(rendered["state_dir"], latest["state_dir"])
            self.assertEqual(
                rendered["argv"],
                [
                    "codex",
                    "exec",
                    "--cd",
                    str(repo.resolve()),
                    "Read and follow the Dispatch Engine coordinator instructions in this file: "
                    "<dry-run-generated-coordinator-prompt>",
                ],
            )
            self.assertEqual(rendered["prompt_path"], "<dry-run-generated-coordinator-prompt>")
            self.assertIn("Coordinator-Only Behavior", rendered["prompt_preview"])
            self.assertIn("registered worker, reviewer, or validator", rendered["prompt_preview"])
            self.assertIn(".dispatch/", rendered["prompt_preview"])
            self.assertIn("Provider: codex", rendered["prompt_preview"])
            self.assertEqual(rendered["state_writes"], [])
            self.assertEqual(_state_snapshot(repo), before)

    def test_coordinator_prompt_template_is_centralized_under_references(self) -> None:
        template_path = prompt_template_path(COORDINATOR_PROTOCOL_TEMPLATE)

        self.assertEqual(template_path.name, "coordinator-protocol.md")
        self.assertIn("references/prompts", str(template_path))
        self.assertIn("Coordinator-Only Behavior", template_path.read_text(encoding="utf-8"))

    def test_explicit_codex_and_claude_render_expected_command_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo, plan_id="plan-001", objective="provider objective")

            codex = render_run_dry_run(repo, run_id=run["run_id"], provider="codex")
            claude = render_run_dry_run(repo, run_id=run["run_id"], provider="claude")

            self.assertEqual(codex["argv"][0:2], ["codex", "exec"])
            self.assertIn("<dry-run-generated-coordinator-prompt>", codex["argv"][-1])
            self.assertEqual(codex["profile"], "codex-exec")
            self.assertEqual(claude["argv"][0:2], ["claude", "-p"])
            self.assertEqual(claude["profile"], "claude-p")
            self.assertIn("<dry-run-generated-coordinator-prompt>", claude["argv"][2])
            self.assertNotEqual(claude["argv"][2], claude["prompt_text"])
            self.assertIn("Provider context: Claude CLI launched with claude -p.", claude["prompt_text"])

    def test_unsupported_provider_and_missing_run_fail_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _import_plan(repo, plan_id="plan-001", objective="error objective")

            with self.assertRaisesRegex(CoordinatorLaunchError, "unsupported provider: unknown"):
                render_run_dry_run(repo, provider="unknown")

            with self.assertRaisesRegex(CoordinatorLaunchError, "Run not found: missing"):
                render_run_dry_run(repo, run_id="missing")

    def test_cli_run_outputs_structured_json_and_errors_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo, plan_id="plan-001", objective="cli objective")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["run", str(repo), "--run-id", run["run_id"], "--dry-run", "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["kind"], "run_dry_run")
            self.assertEqual(payload["provider"], "codex")
            self.assertEqual(payload["run_id"], run["run_id"])

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["run", str(repo), "--provider", "unknown", "--dry-run", "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["kind"], "error")
            self.assertEqual(payload["status"], "coordinator_launch_error")
            self.assertIn("unsupported provider: unknown", payload["summary"])


def _import_plan(repo: Path, *, plan_id: str, objective: str) -> dict:
    plan_path = repo / ".dispatch" / "plans" / f"{plan_id}.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(_plan(plan_id, objective)) + "\n", encoding="utf-8")
    return import_dispatch_plan(repo, plan_path)


def _plan(plan_id: str, objective: str) -> dict:
    return {
        "schema_version": 1,
        "plan_id": plan_id,
        "objective": objective,
        "workstreams": [
            {
                "id": "01-run-launcher",
                "title": "Run launcher dry run",
                "mode": "serial",
                "scope": "Render provider coordinator command shapes.",
                "files": ["scripts/dispatch_engine/cli.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
            }
        ],
        "decisions": [],
    }


def _state_snapshot(repo: Path) -> dict[str, str]:
    root = repo / ".dispatch"
    return {
        str(path.relative_to(root)): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


if __name__ == "__main__":
    unittest.main()
