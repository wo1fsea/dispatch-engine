from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from dispatch_engine.agents import read_agent
from dispatch_engine.cli import main
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.state import run_status
from dispatch_engine.supervisor import launch_detached_coordinator


class DetachedCoordinatorSupervisionTests(unittest.TestCase):
    def test_detached_codex_returns_before_provider_finishes_and_records_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            run = _import_plan(repo, plan_id="plan-001", objective="detached objective")
            bin_dir = root / "bin"
            record_dir = root / "records"
            _write_slow_fake_provider(bin_dir, "codex", exit_code=0, sleep_seconds=1.5)

            started_at = time.monotonic()
            with _fake_provider_env(bin_dir, record_dir):
                result = launch_detached_coordinator(repo, run_id=run["run_id"], provider="codex")
            elapsed = time.monotonic() - started_at

            state_dir = Path(run["state_dir"])
            self.assertEqual(result["kind"], "run_detached")
            self.assertLess(elapsed, 1.0)
            self.assertTrue((state_dir / "supervisors" / "coordinator-001.json").is_file())

            final_status = _wait_for_coordinator_status(repo, run["run_id"], "completed")
            supervisor = final_status["supervisors"][0]
            agent = read_agent(state_dir, "coordinator-001")

            self.assertEqual(supervisor["status"], "completed")
            self.assertEqual(supervisor["exit_code"], 0)
            self.assertIsNotNone(agent)
            assert agent is not None
            self.assertEqual(agent["status"], "completed")
            self.assertEqual((state_dir / "logs" / "coordinator-001.stdout.log").read_text(), "codex stdout\n")
            self.assertEqual((record_dir / "codex.cwd").read_text(encoding="utf-8"), str(repo.resolve()))

    def test_cli_detach_outputs_json_without_waiting_for_slow_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            run = _import_plan(repo, plan_id="plan-001", objective="cli detach objective")
            bin_dir = root / "bin"
            record_dir = root / "records"
            _write_slow_fake_provider(bin_dir, "codex", exit_code=0, sleep_seconds=1.5)

            stdout = io.StringIO()
            started_at = time.monotonic()
            with _fake_provider_env(bin_dir, record_dir), contextlib.redirect_stdout(stdout):
                exit_code = main(["run", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            elapsed = time.monotonic() - started_at

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["kind"], "run_detached")
            self.assertEqual(payload["provider"], "codex")
            self.assertLess(elapsed, 1.0)

            final_status = _wait_for_coordinator_status(repo, run["run_id"], "completed")
            self.assertEqual(final_status["supervisor_counts"]["by_status"], {"completed": 1})


def _wait_for_coordinator_status(repo: Path, run_id: str, expected: str) -> dict:
    deadline = time.monotonic() + 5
    last_status = {}
    while time.monotonic() < deadline:
        last_status = run_status(repo, run_id=run_id)
        coordinator = last_status.get("coordinator")
        if coordinator and coordinator.get("status") == expected:
            return last_status
        time.sleep(0.05)
    raise AssertionError(f"coordinator did not reach {expected}: {last_status}")


def _write_slow_fake_provider(
    bin_dir: Path,
    name: str,
    *,
    exit_code: int,
    sleep_seconds: float,
) -> None:
    bin_dir.mkdir(exist_ok=True)
    script_path = bin_dir / f"{name}.py" if os.name == "nt" else bin_dir / name
    script_path.write_text(
        textwrap.dedent(
            f"""\
            #!{sys.executable}
            import json
            import os
            import pathlib
            import sys
            import time

            record_dir = pathlib.Path(os.environ["FAKE_PROVIDER_RECORD_DIR"])
            record_dir.mkdir(parents=True, exist_ok=True)
            (record_dir / "{name}.argv.json").write_text(json.dumps(sys.argv[1:]), encoding="utf-8")
            (record_dir / "{name}.cwd").write_text(os.getcwd(), encoding="utf-8")
            time.sleep({sleep_seconds})
            print("{name} stdout")
            print("{name} stderr", file=sys.stderr)
            raise SystemExit({exit_code})
            """
        ),
        encoding="utf-8",
    )
    if os.name == "nt":
        wrapper_path = bin_dir / f"{name}.cmd"
        wrapper_path.write_text(
            f'@echo off\r\n"{sys.executable}" "%~dp0{name}.py" %*\r\nexit /b %ERRORLEVEL%\r\n',
            encoding="utf-8",
        )
    else:
        script_path.chmod(0o755)


@contextlib.contextmanager
def _fake_provider_env(bin_dir: Path, record_dir: Path):
    old_path = os.environ.get("PATH", "")
    old_record_dir = os.environ.get("FAKE_PROVIDER_RECORD_DIR")
    os.environ["PATH"] = f"{bin_dir}{os.pathsep}{old_path}"
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
                "id": "01-detached-launch",
                "title": "Detached coordinator launch",
                "mode": "serial",
                "scope": "Launch and supervise a provider coordinator in the background.",
                "files": ["scripts/dispatch_engine/supervisor.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": [
                    "PYTHONPATH=scripts python3 -m unittest tests.test_detached_coordinator_supervision"
                ],
            }
        ],
        "decisions": [],
    }


if __name__ == "__main__":
    unittest.main()
