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
            _write_slow_fake_provider(bin_dir, "codex", exit_code=0, sleep_seconds=0.8)

            started_at = time.monotonic()
            with _fake_provider_env(bin_dir, record_dir):
                result = launch_detached_coordinator(repo, run_id=run["run_id"], provider="codex")
            elapsed = time.monotonic() - started_at

            state_dir = Path(run["state_dir"])
            self.assertEqual(result["kind"], "run_detached")
            self.assertLess(elapsed, 0.5)
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
            _write_slow_fake_provider(bin_dir, "codex", exit_code=0, sleep_seconds=0.8)

            stdout = io.StringIO()
            started_at = time.monotonic()
            with _fake_provider_env(bin_dir, record_dir), contextlib.redirect_stdout(stdout):
                exit_code = main(["run", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            elapsed = time.monotonic() - started_at

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["kind"], "run_detached")
            self.assertEqual(payload["provider"], "codex")
            self.assertLess(elapsed, 0.5)

            final_status = _wait_for_coordinator_status(repo, run["run_id"], "completed")
            self.assertEqual(final_status["supervisor_counts"]["by_status"], {"completed": 1})

    def test_status_reconciles_dead_running_supervisor_pid_as_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo, plan_id="plan-001", objective="stale supervisor objective")
            state_dir = Path(run["state_dir"])
            _write_supervisor_record(state_dir, status="running", supervisor_pid=999999)

            status = run_status(repo, run_id=run["run_id"])

            self.assertEqual(status["supervisors"][0]["status"], "stale")
            self.assertEqual(status["supervisor_counts"]["by_status"], {"stale": 1})
            self.assertEqual(status["lifecycle_diagnostics"][0]["type"], "stale_detached_supervisor")
            self.assertEqual(status["lifecycle_diagnostics"][0]["supervisor_pid"], 999999)

    def test_status_keeps_alive_running_supervisor_pid_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo, plan_id="plan-001", objective="alive supervisor objective")
            state_dir = Path(run["state_dir"])
            _write_supervisor_record(state_dir, status="running", supervisor_pid=os.getpid())

            status = run_status(repo, run_id=run["run_id"])

            self.assertEqual(status["supervisors"][0]["status"], "running")
            self.assertEqual(status["supervisor_counts"]["by_status"], {"running": 1})
            self.assertEqual(status["lifecycle_diagnostics"], [])


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
    path = bin_dir / name
    path.write_text(
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
    path.chmod(0o755)


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


def _write_supervisor_record(state_dir: Path, *, status: str, supervisor_pid: int | None) -> None:
    path = state_dir / "supervisors" / "coordinator-001.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "agent_id": "coordinator-001",
                "run_id": state_dir.name,
                "repo_root": str(state_dir.parent.parent.parent),
                "provider": "codex",
                "profile": "codex-exec",
                "status": status,
                "supervisor_pid": supervisor_pid,
                "created_at": "2026-05-03T00:00:00Z",
                "updated_at": "2026-05-03T00:00:00Z",
                "completed_at": None,
                "supervisor_path": f".dispatch/runs/{state_dir.name}/supervisors/coordinator-001.json",
                "supervisor_stdout_path": f".dispatch/runs/{state_dir.name}/logs/coordinator-001.supervisor.stdout.log",
                "supervisor_stderr_path": f".dispatch/runs/{state_dir.name}/logs/coordinator-001.supervisor.stderr.log",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


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
