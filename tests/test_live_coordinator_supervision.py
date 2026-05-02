from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from dispatch_engine.agents import read_agent
from dispatch_engine.cli import main
from dispatch_engine.coordinators import launch_run_coordinator
from dispatch_engine.events import read_events
from dispatch_engine.plan_schema import import_dispatch_plan


class LiveCoordinatorSupervisionTests(unittest.TestCase):
    def test_default_codex_launches_latest_run_and_records_completion_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            first = _import_plan(repo, plan_id="plan-001", objective="first objective")
            latest = _import_plan(repo, plan_id="plan-002", objective="latest objective")
            bin_dir = root / "bin"
            record_dir = root / "records"
            _write_fake_provider(bin_dir, "codex", exit_code=0)

            with _fake_provider_env(bin_dir, record_dir):
                result = launch_run_coordinator(repo)

            state_dir = Path(latest["state_dir"])
            prompt_path = state_dir / "prompts" / "coordinator-001.md"
            stdout_path = state_dir / "logs" / "coordinator-001.stdout.log"
            stderr_path = state_dir / "logs" / "coordinator-001.stderr.log"
            argv = json.loads((record_dir / "codex.argv.json").read_text(encoding="utf-8"))

            self.assertEqual(result["kind"], "run_live")
            self.assertEqual(result["provider"], "codex")
            self.assertEqual(result["profile"], "codex-exec")
            self.assertEqual(result["run_id"], latest["run_id"])
            self.assertNotEqual(result["run_id"], first["run_id"])
            self.assertEqual(result["state_dir"], str(state_dir))
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["prompt_path"], str(prompt_path))
            self.assertEqual(result["stdout_path"], str(stdout_path))
            self.assertEqual(result["stderr_path"], str(stderr_path))
            self.assertEqual(
                argv,
                [
                    "exec",
                    "--cd",
                    str(repo.resolve()),
                    "Read and follow the Dispatch Engine coordinator instructions in this file: "
                    f"{prompt_path}",
                ],
            )
            self.assertEqual((record_dir / "codex.cwd").read_text(encoding="utf-8"), str(repo.resolve()))
            self.assertEqual((record_dir / "codex.stdin").read_text(encoding="utf-8"), "")
            self.assertIn("Provider: codex", prompt_path.read_text(encoding="utf-8"))
            self.assertIn("latest objective", prompt_path.read_text(encoding="utf-8"))
            self.assertEqual(stdout_path.read_text(encoding="utf-8"), "codex stdout\n")
            self.assertEqual(stderr_path.read_text(encoding="utf-8"), "codex stderr\n")

            agent = read_agent(state_dir, "coordinator-001")
            self.assertIsNotNone(agent)
            assert agent is not None
            self.assertEqual(agent["role"], "coordinator")
            self.assertEqual(agent["provider"], "codex")
            self.assertEqual(agent["profile"], "codex-exec")
            self.assertEqual(agent["status"], "completed")
            self.assertEqual(agent["allowed_write_roots"], [".dispatch/"])
            self.assertEqual(agent["prompt_path"], f".dispatch/runs/{latest['run_id']}/prompts/coordinator-001.md")
            self.assertEqual(agent["stdout_path"], f".dispatch/runs/{latest['run_id']}/logs/coordinator-001.stdout.log")
            self.assertEqual(agent["stderr_path"], f".dispatch/runs/{latest['run_id']}/logs/coordinator-001.stderr.log")

            events = read_events(state_dir / "events.jsonl")
            self.assertEqual(events[-2]["type"], "coordinator.started")
            self.assertEqual(events[-1]["type"], "coordinator.completed")
            self.assertEqual(events[-1]["payload"]["exit_code"], 0)

    def test_explicit_claude_launch_uses_prompt_file_instruction_and_records_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            run = _import_plan(repo, plan_id="plan-001", objective="claude objective")
            bin_dir = root / "bin"
            record_dir = root / "records"
            _write_fake_provider(bin_dir, "claude", exit_code=7)

            with _fake_provider_env(bin_dir, record_dir):
                result = launch_run_coordinator(repo, run_id=run["run_id"], provider="claude")

            state_dir = Path(run["state_dir"])
            argv = json.loads((record_dir / "claude.argv.json").read_text(encoding="utf-8"))
            prompt_path = state_dir / "prompts" / "coordinator-001.md"
            self.assertEqual(result["provider"], "claude")
            self.assertEqual(result["profile"], "claude-p")
            self.assertEqual(result["exit_code"], 7)
            self.assertEqual(argv[0], "-p")
            self.assertIn(str(prompt_path), argv[1])
            self.assertNotIn("claude objective", argv[1])
            self.assertIn("Provider: claude", prompt_path.read_text(encoding="utf-8"))
            self.assertIn("claude objective", prompt_path.read_text(encoding="utf-8"))
            self.assertEqual((state_dir / "logs" / "coordinator-001.stdout.log").read_text(), "claude stdout\n")
            self.assertEqual((state_dir / "logs" / "coordinator-001.stderr.log").read_text(), "claude stderr\n")

            agent = read_agent(state_dir, "coordinator-001")
            self.assertIsNotNone(agent)
            assert agent is not None
            self.assertEqual(agent["status"], "failed")
            self.assertIn("exit code 7", agent["failure_reason"])
            events = read_events(state_dir / "events.jsonl")
            self.assertEqual(events[-2]["type"], "coordinator.started")
            self.assertEqual(events[-1]["type"], "coordinator.failed")
            self.assertEqual(events[-1]["payload"]["exit_code"], 7)

    def test_missing_provider_executable_records_failure_without_process_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            run = _import_plan(repo, plan_id="plan-001", objective="missing executable objective")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            record_dir = root / "records"

            with _fake_provider_env(bin_dir, record_dir):
                result = launch_run_coordinator(repo, provider="codex")

            state_dir = Path(run["state_dir"])
            self.assertEqual(result["state"], "failed")
            self.assertIsNone(result["exit_code"])
            self.assertIn("Executable not found on PATH: codex", result["failure_reason"])
            self.assertEqual((state_dir / "logs" / "coordinator-001.stdout.log").read_text(), "")
            self.assertIn("Executable not found on PATH: codex", (state_dir / "logs" / "coordinator-001.stderr.log").read_text())
            agent = read_agent(state_dir, "coordinator-001")
            self.assertIsNotNone(agent)
            assert agent is not None
            self.assertEqual(agent["status"], "failed")
            self.assertIn("Executable not found on PATH: codex", agent["failure_reason"])
            self.assertEqual(read_events(state_dir / "events.jsonl")[-1]["type"], "coordinator.failed")

    def test_cli_live_run_outputs_structured_payload_and_exit_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            run = _import_plan(repo, plan_id="plan-001", objective="cli objective")
            bin_dir = root / "bin"
            record_dir = root / "records"
            _write_fake_provider(bin_dir, "codex", exit_code=0)

            stdout = io.StringIO()
            with _fake_provider_env(bin_dir, record_dir), contextlib.redirect_stdout(stdout):
                exit_code = main(["run", str(repo), "--run-id", run["run_id"], "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["kind"], "run_live")
            self.assertEqual(payload["provider"], "codex")
            self.assertEqual(payload["exit_code"], 0)
            self.assertEqual(payload["run_id"], run["run_id"])
            self.assertTrue(Path(payload["prompt_path"]).is_file())
            self.assertTrue(Path(payload["stdout_path"]).is_file())
            self.assertTrue(Path(payload["stderr_path"]).is_file())


def _write_fake_provider(bin_dir: Path, name: str, *, exit_code: int) -> None:
    bin_dir.mkdir(exist_ok=True)
    path = bin_dir / name
    path.write_text(
        textwrap.dedent(
            f"""\
            #!{sys.executable}
            import json
            import os
            import pathlib
            import sys

            record_dir = pathlib.Path(os.environ["FAKE_PROVIDER_RECORD_DIR"])
            record_dir.mkdir(parents=True, exist_ok=True)
            (record_dir / "{name}.argv.json").write_text(json.dumps(sys.argv[1:]), encoding="utf-8")
            (record_dir / "{name}.cwd").write_text(os.getcwd(), encoding="utf-8")
            (record_dir / "{name}.stdin").write_text(sys.stdin.read(), encoding="utf-8")
            print("{name} stdout")
            print("{name} stderr", file=sys.stderr)
            raise SystemExit({exit_code})
            """
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)


@contextlib.contextmanager
def _fake_provider_env(bin_dir: Path, record_dir: Path):
    old_path = os.environ.get("PATH", "")
    old_record_dir = os.environ.get("FAKE_PROVIDER_RECORD_DIR")
    os.environ["PATH"] = str(bin_dir)
    os.environ["FAKE_PROVIDER_RECORD_DIR"] = str(record_dir)
    try:
        yield
    finally:
        os.environ["PATH"] = old_path
        if old_record_dir is None:
            os.environ.pop("FAKE_PROVIDER_RECORD_DIR", None)
        else:
            os.environ["FAKE_PROVIDER_RECORD_DIR"] = old_record_dir


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
                "id": "01-live-launch",
                "title": "Live coordinator launch",
                "mode": "serial",
                "scope": "Launch and supervise a provider coordinator process.",
                "files": ["scripts/dispatch_engine/coordinators.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest tests.test_live_coordinator_supervision"],
            }
        ],
        "decisions": [],
    }


if __name__ == "__main__":
    unittest.main()
