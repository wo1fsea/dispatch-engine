from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from dispatch_engine.agents import fail_agent, register_agent
from dispatch_engine.cli import main
from dispatch_engine.decisions import (
    list_decisions,
    record_blocker,
    record_decision_request,
)
from dispatch_engine.events import protocol_violation, read_events
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.state import run_status


class CodexFacingControlSurfaceTests(unittest.TestCase):
    def test_status_next_actions_reports_decisions_blockers_violations_and_failed_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _append_decision(
                state_dir,
                {
                    "id": "legacy-decision",
                    "status": "pending",
                    "question": "Should the worker expand scope?",
                    "workstream": "01-control-surface",
                    "options": [
                        {"id": "decline", "label": "Keep scope fixed"},
                        {"id": "approve", "label": "Approve scope expansion", "recommended": True},
                    ],
                },
            )
            record_blocker(
                state_dir,
                blocker_id="blocker-001",
                summary="Worker needs an operator decision.",
                workstream="01-control-surface",
            )
            protocol_violation(
                state_dir / "events.jsonl",
                violation="missing_worker_report",
                details={"agent_id": "worker-001"},
                workstream="01-control-surface",
            )
            register_agent(
                state_dir,
                agent_id="worker-001",
                role="worker",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-control-surface",
            )
            fail_agent(state_dir, "worker-001", reason="test failure")

            status = run_status(repo)

            self.assertEqual(
                status["next_actions"],
                [
                    {
                        "type": "decision_required",
                        "decision_id": "legacy-decision",
                        "question": "Should the worker expand scope?",
                        "workstream": "01-control-surface",
                        "recommended_option": "approve",
                    },
                    {
                        "type": "blocker_resolution_required",
                        "count": 1,
                        "blocker_ids": ["blocker-001"],
                    },
                    {
                        "type": "repair_protocol_violations",
                        "count": 1,
                    },
                    {
                        "type": "inspect_failed_agents",
                        "count": 1,
                        "agent_ids": ["worker-001"],
                    },
                ],
            )

    def test_events_command_generates_stable_ids_and_since_filters_later_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = import_dispatch_plan(repo, _plan_file(repo))

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "events",
                        str(repo),
                        "--run-id",
                        plan["run_id"],
                        "--since",
                        "event-000002",
                        "--json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["kind"], "events")
            self.assertEqual([event["id"] for event in payload["events"]], ["event-000003"])
            self.assertEqual([event["type"] for event in payload["events"]], ["workstream.planned"])

            numeric_stdout = io.StringIO()
            with redirect_stdout(numeric_stdout):
                numeric_exit = main(["events", str(repo), "--run-id", plan["run_id"], "--since", "2", "--json"])

            self.assertEqual(numeric_exit, 0)
            numeric_payload = json.loads(numeric_stdout.getvalue())
            self.assertEqual([event["id"] for event in numeric_payload["events"]], ["event-000003"])

    def test_alerts_command_returns_material_records_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            record_decision_request(
                state_dir,
                decision_id="decision-001",
                question="Can the run continue?",
                workstream="01-control-surface",
            )
            record_blocker(
                state_dir,
                blocker_id="blocker-001",
                summary="Blocked until the decision is made.",
                workstream="01-control-surface",
            )
            register_agent(
                state_dir,
                agent_id="worker-001",
                role="worker",
                provider="codex",
                profile="codex-exec",
                status="failed",
                workstream="01-control-surface",
            )
            _update_run_statuses(state_dir, run_status_value="blocked", workstream_status="blocked")
            before_events = (state_dir / "events.jsonl").read_text(encoding="utf-8")
            before_decisions = (state_dir / "decisions.jsonl").read_text(encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["alerts", str(repo), "--json"])

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(
                [alert["type"] for alert in payload["alerts"]],
                [
                    "pending_decision",
                    "unresolved_blocker",
                    "failed_agent",
                    "run_blocked",
                    "workstream_blocked",
                ],
            )
            self.assertEqual(before_events, (state_dir / "events.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(before_decisions, (state_dir / "decisions.jsonl").read_text(encoding="utf-8"))

    def test_resolve_decision_command_validates_option_before_recording_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _append_decision(
                state_dir,
                {
                    "id": "decision-001",
                    "status": "pending",
                    "question": "Which path should worker take?",
                    "options": [
                        {"id": "safe", "label": "Small safe change", "recommended": True},
                        {"id": "wide", "label": "Broaden the change"},
                    ],
                },
            )

            bad_stdout = io.StringIO()
            with redirect_stdout(bad_stdout):
                bad_exit = main(
                    [
                        "resolve-decision",
                        str(repo),
                        "--id",
                        "decision-001",
                        "--option",
                        "missing",
                        "--json",
                    ]
                )

            self.assertEqual(bad_exit, 1)
            bad_payload = json.loads(bad_stdout.getvalue())
            self.assertEqual(bad_payload["status"], "invalid_decision_resolution")
            self.assertIn("decision option not found", bad_payload["summary"])
            self.assertEqual(list_decisions(state_dir)[0]["status"], "pending")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "resolve-decision",
                        str(repo),
                        "--id",
                        "decision-001",
                        "--option",
                        "safe",
                        "--actor",
                        "operator",
                        "--resolution",
                        "User approved the small option.",
                        "--json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["kind"], "decision_resolution")
            self.assertEqual(payload["decision"]["status"], "resolved")
            self.assertEqual(payload["decision"]["selected_option_id"], "safe")
            self.assertEqual(payload["decision"]["resolution"], "User approved the small option.")
            self.assertEqual(list_decisions(state_dir)[0]["selected_option_id"], "safe")
            self.assertEqual(read_events(state_dir / "events.jsonl")[-1]["type"], "decision.resolved")
            self.assertEqual(read_events(state_dir / "events.jsonl")[-1]["payload"]["option_id"], "safe")

            second_stdout = io.StringIO()
            with redirect_stdout(second_stdout):
                second_exit = main(
                    [
                        "resolve-decision",
                        str(repo),
                        "--id",
                        "decision-001",
                        "--option",
                        "wide",
                        "--json",
                    ]
                )

            self.assertEqual(second_exit, 1)
            self.assertIn("not pending", json.loads(second_stdout.getvalue())["summary"])


def _import_plan(repo: Path) -> Path:
    return Path(import_dispatch_plan(repo, _plan_file(repo))["state_dir"])


def _plan_file(repo: Path) -> Path:
    plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(_plan()) + "\n", encoding="utf-8")
    return plan_path


def _plan() -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": "codex-facing control surface objective",
        "workstreams": [
            {
                "id": "01-control-surface",
                "title": "Codex-facing control surface",
                "mode": "serial",
                "scope": "Add runtime status actions and commands.",
                "files": ["scripts/dispatch_engine/state.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
            }
        ],
        "decisions": [],
    }


def _append_decision(state_dir: Path, record: dict) -> None:
    with (state_dir / "decisions.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _update_run_statuses(state_dir: Path, *, run_status_value: str, workstream_status: str) -> None:
    run_path = state_dir / "run.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    run["status"] = run_status_value
    run["workstreams"][0]["status"] = workstream_status
    run_path.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
