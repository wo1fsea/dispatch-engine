from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dispatch_engine.agents import register_agent
from dispatch_engine.cli import main
from dispatch_engine.events import read_events
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.state import run_alerts, run_events, run_status


class RunCancelControlTests(unittest.TestCase):
    def test_cancel_latest_run_updates_durable_state_agents_status_alerts_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _import_plan(repo, plan_id="plan-a", objective="older objective")
            latest = _import_plan(repo, plan_id="plan-z", objective="latest objective")
            state_dir = Path(latest["state_dir"])
            reason = "User asked to stop the run."
            _write_supervisor(state_dir, status="running")
            _register_agents(state_dir)

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["cancel", str(repo), "--reason", reason, "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["kind"], "run_cancel")
            self.assertEqual(payload["status"], "cancelled")
            self.assertEqual(payload["run_id"], latest["run_id"])
            self.assertEqual(payload["reason"], reason)
            self.assertFalse(payload["already_terminal"])
            self.assertEqual(payload["updated_agents"], ["coordinator-001", "worker-001"])
            self.assertEqual(
                [signal["final_state"] for signal in payload["signals"]],
                ["missing_pid"],
            )

            run = _read_json(state_dir / "run.json")
            self.assertEqual(run["status"], "cancelled")
            self.assertEqual(run["cancelled_by"], "interactive-codex")
            self.assertEqual(run["cancellation_reason"], reason)
            self.assertIn("cancelled_at", run)

            supervisor = _read_json(state_dir / "supervisors" / "coordinator-001.json")
            self.assertEqual(supervisor["status"], "cancelled")
            self.assertEqual(supervisor["cancellation_reason"], reason)
            self.assertEqual(supervisor["cancel_signal"]["final_state"], "missing_pid")

            self.assertEqual(_read_json(state_dir / "agents" / "coordinator-001.json")["status"], "cancelled")
            self.assertEqual(_read_json(state_dir / "agents" / "worker-001.json")["status"], "cancelled")
            self.assertEqual(_read_json(state_dir / "agents" / "reviewer-001.json")["status"], "completed")
            self.assertEqual(_read_json(state_dir / "agents" / "validator-001.json")["status"], "failed")

            status = run_status(repo, run_id=latest["run_id"])
            self.assertEqual(status["run_status"], "cancelled")
            self.assertEqual(status["cancellation"]["reason"], reason)
            self.assertEqual(status["agent_counts"]["by_status"], {"cancelled": 2, "completed": 1, "failed": 1})
            self.assertEqual(status["supervisor_counts"]["by_status"], {"cancelled": 1})
            self.assertEqual(status["next_actions"], [])

            alerts = run_alerts(repo, run_id=latest["run_id"])
            self.assertEqual(alerts["alerts"][-1]["type"], "run_cancelled")
            self.assertEqual(alerts["alerts"][-1]["reason"], reason)

            events = run_events(repo, run_id=latest["run_id"], since="event-000003")
            self.assertEqual(
                [event["type"] for event in events["events"]],
                ["run.cancel.requested", "run.cancel.signal", "run.cancel.completed"],
            )

    def test_stop_alias_can_cancel_explicit_non_latest_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            selected = _import_plan(repo, plan_id="plan-a", objective="selected objective")
            latest = _import_plan(repo, plan_id="plan-z", objective="latest objective")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    [
                        "stop",
                        str(repo),
                        "--run-id",
                        selected["run_id"],
                        "--reason",
                        "Operator stop alias.",
                        "--json",
                    ]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["kind"], "run_cancel")
            self.assertEqual(payload["run_id"], selected["run_id"])
            self.assertEqual(_read_json(Path(selected["state_dir"]) / "run.json")["status"], "cancelled")
            self.assertEqual(_read_json(Path(latest["state_dir"]) / "run.json")["status"], "planned")

    def test_already_cancelled_run_is_idempotent_success_without_resignalling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            imported = _import_plan(repo, plan_id="plan-001", objective="idempotent objective")
            state_dir = Path(imported["state_dir"])
            _write_supervisor(state_dir, status="running", supervisor_pid=123)

            fake = _FakeProcessController(alive_after_graceful=False)
            from dispatch_engine.cancel import cancel_run

            first = cancel_run(repo, run_id=imported["run_id"], reason="Initial cancel.", process_controller=fake)
            events_after_first = read_events(state_dir / "events.jsonl")
            second = cancel_run(repo, run_id=imported["run_id"], reason="Second cancel.", process_controller=fake)

            self.assertFalse(first["already_terminal"])
            self.assertTrue(second["already_terminal"])
            self.assertEqual(second["reason"], "Initial cancel.")
            self.assertEqual(second["signals"], [])
            self.assertEqual(fake.graceful_calls, [123])
            self.assertEqual(fake.escalation_calls, [])
            self.assertEqual(_read_json(state_dir / "run.json")["cancellation_reason"], "Initial cancel.")
            self.assertEqual(
                [event["type"] for event in read_events(state_dir / "events.jsonl")[len(events_after_first) :]],
                ["run.cancel.requested", "run.cancel.completed"],
            )

    def test_cancel_errors_are_clear_for_missing_terminal_and_malformed_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            no_run = _cli_json(["cancel", str(repo), "--json"])
            self.assertEqual(no_run["exit_code"], 1)
            self.assertEqual(no_run["payload"]["status"], "no_run")

            imported = _import_plan(repo, plan_id="plan-001", objective="error objective")
            missing = _cli_json(["cancel", str(repo), "--run-id", "missing", "--json"])
            self.assertEqual(missing["exit_code"], 1)
            self.assertEqual(missing["payload"]["status"], "missing_run")

            state_dir = Path(imported["state_dir"])
            _update_run(state_dir, {"status": "completed"})
            completed = _cli_json(["cancel", str(repo), "--run-id", imported["run_id"], "--json"])
            self.assertEqual(completed["exit_code"], 1)
            self.assertEqual(completed["payload"]["status"], "run_already_terminal")

            _update_run(state_dir, {"status": "failed"})
            failed = _cli_json(["cancel", str(repo), "--run-id", imported["run_id"], "--json"])
            self.assertEqual(failed["exit_code"], 1)
            self.assertEqual(failed["payload"]["status"], "run_already_terminal")

            (state_dir / "run.json").write_text("{not valid json", encoding="utf-8")
            malformed = _cli_json(["cancel", str(repo), "--run-id", imported["run_id"], "--json"])
            self.assertEqual(malformed["exit_code"], 1)
            self.assertEqual(malformed["payload"]["status"], "cancel_state_error")

    def test_process_signal_outcomes_record_graceful_and_escalation_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            graceful_run = _import_plan(repo, plan_id="plan-graceful", objective="graceful objective")
            graceful_state = Path(graceful_run["state_dir"])
            _write_supervisor(graceful_state, status="running", supervisor_pid=111)

            from dispatch_engine.cancel import cancel_run

            graceful_fake = _FakeProcessController(alive_after_graceful=False)
            graceful = cancel_run(
                repo,
                run_id=graceful_run["run_id"],
                reason="Graceful.",
                process_controller=graceful_fake,
                grace_seconds=0,
            )

            self.assertEqual(graceful["signals"][0]["final_state"], "terminated")
            self.assertFalse(graceful["signals"][0]["escalated"])
            self.assertEqual(graceful_fake.graceful_calls, [111])
            self.assertEqual(graceful_fake.escalation_calls, [])

            escalation_run = _import_plan(repo, plan_id="plan-escalation", objective="escalation objective")
            escalation_state = Path(escalation_run["state_dir"])
            _write_supervisor(escalation_state, status="running", supervisor_pid=222)
            escalation_fake = _FakeProcessController(alive_after_graceful=True)

            escalated = cancel_run(
                repo,
                run_id=escalation_run["run_id"],
                reason="Escalate.",
                process_controller=escalation_fake,
                grace_seconds=0,
            )

            self.assertEqual(escalated["signals"][0]["final_state"], "terminated_after_escalation")
            self.assertTrue(escalated["signals"][0]["escalated"])
            self.assertEqual(escalation_fake.graceful_calls, [222])
            self.assertEqual(escalation_fake.escalation_calls, [222])
            supervisor = _read_json(escalation_state / "supervisors" / "coordinator-001.json")
            self.assertEqual(supervisor["cancel_signal"]["final_state"], "terminated_after_escalation")

    def test_windows_stale_pid_system_error_is_recorded_as_not_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            imported = _import_plan(repo, plan_id="plan-windows-stale", objective="windows stale pid objective")
            state_dir = Path(imported["state_dir"])
            _write_supervisor(state_dir, status="running", supervisor_pid=333)

            from dispatch_engine.cancel import cancel_run

            with patch("dispatch_engine.cancel.os.kill", side_effect=SystemError("stale Windows pid state")):
                payload = cancel_run(repo, run_id=imported["run_id"], reason="Cancel stale pid.", grace_seconds=0)

            self.assertEqual(payload["kind"], "run_cancel")
            self.assertEqual(payload["status"], "cancelled")
            self.assertEqual(payload["signals"][0]["final_state"], "not_running")
            supervisor = _read_json(state_dir / "supervisors" / "coordinator-001.json")
            self.assertEqual(supervisor["cancel_signal"]["final_state"], "not_running")


class _FakeProcessController:
    graceful_signal_name = "SIGTERM"
    escalation_signal_name = "SIGKILL"

    def __init__(self, *, alive_after_graceful: bool) -> None:
        self.alive_after_graceful = alive_after_graceful
        self.graceful_calls: list[int] = []
        self.escalation_calls: list[int] = []

    def is_alive(self, pid: int) -> bool:
        return True

    def graceful(self, pid: int) -> None:
        self.graceful_calls.append(pid)

    def is_alive_after_grace(self, pid: int, grace_seconds: float) -> bool:
        return self.alive_after_graceful

    def escalate(self, pid: int) -> None:
        self.escalation_calls.append(pid)


def _cli_json(argv: list[str]) -> dict:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = main(argv)
    return {"exit_code": exit_code, "payload": json.loads(stdout.getvalue())}


def _import_plan(repo: Path, *, plan_id: str, objective: str) -> dict:
    plan_path = repo / ".dispatch" / "plans" / f"{plan_id}.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(_plan(plan_id, objective)) + "\n", encoding="utf-8")
    with patch("dispatch_engine.plan_schema.new_run_id", return_value=f"{plan_id}-run"):
        return import_dispatch_plan(repo, plan_path)


def _plan(plan_id: str, objective: str) -> dict:
    return {
        "schema_version": 1,
        "plan_id": plan_id,
        "objective": objective,
        "workstreams": [
            {
                "id": "01-cancel-control",
                "title": "Cancel control",
                "mode": "serial",
                "scope": "Exercise run cancellation.",
                "files": ["scripts/dispatch_engine/cancel.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest tests.test_run_cancel_control"],
            }
        ],
        "decisions": [],
    }


def _register_agents(state_dir: Path) -> None:
    register_agent(
        state_dir,
        agent_id="coordinator-001",
        role="coordinator",
        provider="codex",
        profile="codex-exec",
        status="running",
    )
    register_agent(
        state_dir,
        agent_id="worker-001",
        role="worker",
        provider="codex",
        profile="codex-exec",
        status="running",
        workstream="01-cancel-control",
    )
    register_agent(
        state_dir,
        agent_id="reviewer-001",
        role="reviewer",
        provider="codex",
        profile="codex-exec",
        status="completed",
        workstream="01-cancel-control",
    )
    register_agent(
        state_dir,
        agent_id="validator-001",
        role="validator",
        provider="codex",
        profile="codex-exec",
        status="failed",
        workstream="01-cancel-control",
    )


def _write_supervisor(
    state_dir: Path,
    *,
    status: str,
    supervisor_pid: int | None = None,
) -> None:
    path = state_dir / "supervisors" / "coordinator-001.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "agent_id": "coordinator-001",
                "run_id": state_dir.name,
                "repo_root": str(state_dir.parents[2]),
                "provider": "codex",
                "profile": "codex-exec",
                "status": status,
                "supervisor_pid": supervisor_pid,
                "created_at": "2026-05-03T00:00:00Z",
                "updated_at": "2026-05-03T00:00:00Z",
                "completed_at": None,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _update_run(state_dir: Path, updates: dict) -> None:
    path = state_dir / "run.json"
    run = json.loads(path.read_text(encoding="utf-8"))
    run.update(updates)
    path.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
