from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from dispatch_engine.agents import register_agent
from dispatch_engine.cli import main
from dispatch_engine.events import protocol_violation
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.state import run_status, tail_events


class StatusTailTests(unittest.TestCase):
    def test_status_reports_latest_run_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="status objective")

            status = run_status(repo)

            self.assertEqual(status["kind"], "status")
            self.assertEqual(status["run_id"], plan["run_id"])
            self.assertEqual(status["objective"], "status objective")
            self.assertEqual(status["run_status"], "planned")
            self.assertEqual(status["workstream_counts"], {"planned": 1})
            self.assertEqual(status["pending_decisions"], 0)
            self.assertEqual(status["state_dir"], plan["state_dir"])
            self.assertEqual(status["agents"], [])
            self.assertEqual(status["agent_counts"], {"by_role": {}, "by_status": {}})
            self.assertEqual(status["workstream_assignments"], [])
            self.assertEqual(
                status["heartbeat_summary"],
                {"total_agents": 0, "with_heartbeat": 0, "missing_heartbeat": 0},
            )
            self.assertEqual(status["protocol_violations"]["count"], 0)

    def test_status_reports_structured_agent_observability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="agent observability objective")
            state_dir = Path(plan["state_dir"])
            register_agent(
                state_dir,
                agent_id="coordinator-001",
                role="coordinator",
                provider="codex",
                profile="codex-exec",
                status="running",
                last_heartbeat_at="2026-05-02T00:00:00Z",
            )
            register_agent(
                state_dir,
                agent_id="worker-001",
                role="worker",
                provider="claude",
                profile="claude-p",
                status="running",
                workstream="01-status-tail",
                assigned_files=["scripts/dispatch_engine/state.py"],
                allowed_write_roots=["scripts/dispatch_engine/"],
                last_heartbeat_at="2026-05-02T00:01:00Z",
            )
            register_agent(
                state_dir,
                agent_id="reviewer-001",
                role="reviewer",
                provider="codex",
                profile="codex-exec",
                status="completed",
                workstream="01-status-tail",
            )
            protocol_violation(
                state_dir / "events.jsonl",
                violation="fixture_violation",
                details={"source": "test"},
                workstream="01-status-tail",
            )

            status = run_status(repo, run_id=plan["run_id"])

            self.assertEqual(status["coordinator"]["agent_id"], "coordinator-001")
            self.assertEqual(status["coordinator"]["provider"], "codex")
            self.assertEqual(status["coordinator"]["profile"], "codex-exec")
            self.assertEqual(status["coordinator"]["status"], "running")
            self.assertEqual(status["coordinator"]["last_heartbeat_at"], "2026-05-02T00:00:00Z")
            self.assertEqual(status["agent_counts"]["by_role"], {"coordinator": 1, "reviewer": 1, "worker": 1})
            self.assertEqual(status["agent_counts"]["by_status"], {"completed": 1, "running": 2})
            self.assertEqual(
                status["workstream_assignments"],
                [
                    {
                        "workstream": "01-status-tail",
                        "agent_id": "worker-001",
                        "role": "worker",
                        "status": "running",
                    }
                ],
            )
            self.assertEqual(
                status["heartbeat_summary"],
                {"total_agents": 3, "with_heartbeat": 2, "missing_heartbeat": 1},
            )
            self.assertEqual(status["protocol_violations"]["count"], 2)
            self.assertEqual(status["protocol_violations"]["event_count"], 1)
            self.assertEqual(status["protocol_violations"]["detected_count"], 1)
            self.assertEqual(
                status["protocol_violations"]["detected"][0]["violation"],
                "missing_reviewer_report",
            )

    def test_status_command_prints_concise_agent_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="human status objective")
            state_dir = Path(plan["state_dir"])
            register_agent(
                state_dir,
                agent_id="coordinator-001",
                role="coordinator",
                provider="codex",
                profile="codex-exec",
                status="running",
                last_heartbeat_at="2026-05-02T00:00:00Z",
            )
            register_agent(
                state_dir,
                agent_id="worker-001",
                role="worker",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-status-tail",
                last_heartbeat_at="2026-05-02T00:01:00Z",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["status", str(repo)])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("Agents: total 2", output)
            self.assertIn("Coordinator: codex/codex-exec running", output)
            self.assertIn("Assignments: 01-status-tail -> worker-001 (worker running)", output)

    def test_status_handles_legacy_runs_without_agents_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = repo / ".dispatch" / "runs" / "legacy-run"
            (state_dir / "workstreams").mkdir(parents=True)
            (state_dir / "events.jsonl").write_text("", encoding="utf-8")
            (state_dir / "run.json").write_text(
                json.dumps(
                    {
                        "run_id": "legacy-run",
                        "status": "planned",
                        "objective": "legacy objective",
                        "workstreams": [],
                        "decisions": [],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            status = run_status(repo)

            self.assertEqual(status["status"], "ok")
            self.assertEqual(status["agents"], [])
            self.assertEqual(status["agent_counts"], {"by_role": {}, "by_status": {}})
            self.assertEqual(status["workstream_assignments"], [])
            self.assertEqual(status["heartbeat_summary"]["missing_heartbeat"], 0)

    def test_tail_reads_events_for_explicit_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="tail objective")

            tail = tail_events(repo, run_id=plan["run_id"])

            self.assertEqual(tail["kind"], "tail")
            self.assertEqual(tail["run_id"], plan["run_id"])
            self.assertEqual(
                [event["type"] for event in tail["events"]],
                ["run.created", "plan.imported", "workstream.planned"],
            )

    def test_status_and_tail_handle_missing_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            status = run_status(repo)
            tail = tail_events(repo)

            self.assertEqual(status["status"], "no_run")
            self.assertEqual(tail["status"], "no_run")
            self.assertIn("No Dispatch Engine runs found", status["summary"])
            self.assertIn("No Dispatch Engine runs found", tail["summary"])

    def test_explicit_missing_run_id_is_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _import_plan(repo, objective="missing run objective")

            status = run_status(repo, run_id="missing")
            tail = tail_events(repo, run_id="missing")

            self.assertEqual(status["status"], "missing_run")
            self.assertEqual(tail["status"], "missing_run")
            self.assertIn("Run not found", status["summary"])
            self.assertIn("Run not found", tail["summary"])


def _import_plan(repo: Path, *, objective: str) -> dict:
    plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(json.dumps(_plan(objective)) + "\n")
    return import_dispatch_plan(repo, plan_path)


def _plan(objective: str) -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": objective,
        "workstreams": [
            {
                "id": "01-status-tail",
                "title": "Preserve status and tail readers",
                "mode": "serial",
                "scope": "Imported run fixture.",
                "files": ["scripts/dispatch_engine/state.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
            }
        ],
        "decisions": [],
    }


if __name__ == "__main__":
    unittest.main()
