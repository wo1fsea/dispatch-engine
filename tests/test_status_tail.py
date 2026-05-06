from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from dispatch_engine.agents import register_agent, register_worker_agent
from dispatch_engine.cli import main
from dispatch_engine.events import append_event, protocol_violation
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.protocol_resolutions import resolve_protocol_violation
from dispatch_engine.state import run_alerts, run_status, tail_events


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

    def test_status_uses_durable_assigned_workstream_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="durable assignment objective")
            state_dir = Path(plan["state_dir"])
            _update_workstream(
                state_dir,
                "01-status-tail",
                {
                    "status": "assigned",
                    "state": "assigned",
                    "assigned_agent": "worker-001",
                    "updated_at": "2026-05-06T00:00:00Z",
                },
            )

            status = run_status(repo, run_id=plan["run_id"])

            self.assertEqual(status["workstream_counts"], {"assigned": 1})
            self.assertEqual(status["workstream_progress"]["unassigned"], 0)
            self.assertEqual(status["workstream_progress"]["assigned"], 1)
            self.assertEqual(
                status["workstream_assignments"],
                [
                    {
                        "workstream": "01-status-tail",
                        "agent_id": "worker-001",
                        "role": "worker",
                        "status": "assigned",
                    }
                ],
            )

    def test_status_preserves_terminal_workstream_file_assignment_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="terminal assignment objective")
            state_dir = Path(plan["state_dir"])
            _update_workstream(
                state_dir,
                "01-status-tail",
                {
                    "status": "completed",
                    "state": "completed",
                    "assigned_agent": "worker-001",
                    "updated_at": "2026-05-06T00:00:00Z",
                },
            )

            status = run_status(repo, run_id=plan["run_id"])

            self.assertEqual(status["workstream_counts"], {"completed": 1})
            self.assertEqual(status["workstream_progress"]["completed"], 1)
            self.assertEqual(status["workstream_progress"]["unassigned"], 0)
            self.assertEqual(
                status["workstream_assignments"],
                [
                    {
                        "workstream": "01-status-tail",
                        "agent_id": "worker-001",
                        "role": "worker",
                        "status": "completed",
                    }
                ],
            )

    def test_status_preserves_terminal_assignment_event_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="terminal event assignment objective")
            state_dir = Path(plan["state_dir"])
            append_event(
                state_dir / "events.jsonl",
                "workstream.assigned",
                workstream="01-status-tail",
                payload={"agent_id": "worker-002", "role": "worker"},
            )
            _update_workstream(
                state_dir,
                "01-status-tail",
                {
                    "status": "cancelled",
                    "state": "cancelled",
                    "updated_at": "2026-05-06T00:00:00Z",
                },
            )

            status = run_status(repo, run_id=plan["run_id"])

            self.assertEqual(status["workstream_counts"], {"cancelled": 1})
            self.assertEqual(status["workstream_progress"]["cancelled"], 1)
            self.assertEqual(status["workstream_progress"]["unassigned"], 0)
            self.assertEqual(
                status["workstream_assignments"],
                [
                    {
                        "workstream": "01-status-tail",
                        "agent_id": "worker-002",
                        "role": "worker",
                        "status": "cancelled",
                    }
                ],
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

    def test_status_and_alerts_surface_orphaned_running_child_after_terminal_coordinator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="orphaned child objective")
            state_dir = Path(plan["state_dir"])
            _set_run_status(state_dir, "completed")
            register_agent(
                state_dir,
                agent_id="coordinator-001",
                role="coordinator",
                provider="codex",
                profile="codex-exec",
                status="completed",
                completed_at="2026-05-03T00:00:00Z",
            )
            register_agent(
                state_dir,
                agent_id="validator-001",
                role="validator",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-status-tail",
            )

            status = run_status(repo, run_id=plan["run_id"])
            alerts = run_alerts(repo, run_id=plan["run_id"])

            diagnostics = status["lifecycle_diagnostics"]
            self.assertIn("orphaned_running_agent", [item["type"] for item in diagnostics])
            orphaned = [item for item in diagnostics if item["type"] == "orphaned_running_agent"][0]
            self.assertEqual(orphaned["agent_id"], "validator-001")
            self.assertEqual(status["next_actions"], [])
            self.assertIn(
                "orphaned_running_agent",
                [alert["type"] for alert in alerts["alerts"]],
            )

    def test_status_and_alerts_surface_running_agent_without_launch_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="missing launch evidence objective")
            state_dir = Path(plan["state_dir"])
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-status-tail",
                assigned_files=["scripts/dispatch_engine/state.py"],
                allowed_write_roots=[],
            )

            status = run_status(repo, run_id=plan["run_id"])
            alerts = run_alerts(repo, run_id=plan["run_id"])

            self.assertEqual(
                [item["type"] for item in status["lifecycle_diagnostics"]],
                ["missing_agent_launch_evidence"],
            )
            self.assertEqual(status["lifecycle_diagnostics"][0]["agent_id"], "worker-001")
            self.assertEqual(
                status["lifecycle_diagnostics"][0]["accepted_evidence_fields"],
                [
                    "provider_native_agent_id",
                    "provider_native_spawn_ref",
                    "launch_evidence.spawn_agent_id",
                    "launch_evidence.provider_native_spawn_ref",
                    "provider_launch.evidence.provider_native_spawn_ref",
                    "pid",
                    "stdout_path",
                    "stderr_path",
                ],
            )
            self.assertEqual(
                status["lifecycle_diagnostics"][0]["missing_evidence_fields"],
                [
                    "provider_native_agent_id",
                    "provider_native_spawn_ref",
                    "launch_evidence.spawn_agent_id",
                    "launch_evidence.provider_native_spawn_ref",
                    "provider_launch.evidence.provider_native_spawn_ref",
                    "pid",
                ],
            )
            self.assertEqual(
                status["lifecycle_diagnostics"][0]["missing_file_evidence_fields"],
                ["stdout_path", "stderr_path"],
            )
            self.assertIn(
                "missing_agent_launch_evidence",
                [alert["type"] for alert in alerts["alerts"]],
            )
            self.assertIn(
                "missing_agent_launch_evidence",
                status["next_actions"][0]["diagnostic_types"],
            )

    def test_running_agent_with_existing_log_file_has_launch_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="existing launch evidence objective")
            state_dir = Path(plan["state_dir"])
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-status-tail",
                assigned_files=["scripts/dispatch_engine/state.py"],
                allowed_write_roots=[],
            )
            stdout_path = state_dir / "logs" / "worker-001.stdout.log"
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text("", encoding="utf-8")

            status = run_status(repo, run_id=plan["run_id"])

            self.assertEqual(status["lifecycle_diagnostics"], [])

    def test_provider_native_launch_evidence_fields_prevent_missing_launch_diagnostic(self) -> None:
        evidence_cases = [
            {"provider_native_agent_id": "spawn-agent-001"},
            {"provider_native_spawn_ref": "spawn-ref-001"},
            {"launch_evidence": {"spawn_agent_id": "spawn-agent-002"}},
            {"launch_evidence": {"provider_native_spawn_ref": "spawn-ref-002"}},
            {"provider_launch": {"evidence": {"provider_native_spawn_ref": "spawn-ref-003"}}},
        ]
        for evidence in evidence_cases:
            with self.subTest(evidence=evidence):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    plan = _import_plan(repo, objective="provider launch evidence objective")
                    state_dir = Path(plan["state_dir"])
                    register_worker_agent(
                        state_dir,
                        agent_id="worker-001",
                        provider="codex",
                        profile="codex-exec",
                        status="running",
                        workstream="01-status-tail",
                        assigned_files=["scripts/dispatch_engine/state.py"],
                        allowed_write_roots=[],
                    )
                    _update_agent(state_dir, "worker-001", evidence)
                    _write_report(state_dir, "worker-001")

                    status = run_status(repo, run_id=plan["run_id"])

                    self.assertNotIn(
                        "missing_agent_launch_evidence",
                        [item["type"] for item in status["lifecycle_diagnostics"]],
                    )

    def test_active_provider_native_agent_without_report_after_staleness_surfaces_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="provider no report objective")
            state_dir = Path(plan["state_dir"])
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-status-tail",
                assigned_files=["scripts/dispatch_engine/state.py"],
                allowed_write_roots=[],
            )
            _update_agent(
                state_dir,
                "worker-001",
                {
                    "provider_native_agent_id": "spawn-agent-001",
                    "last_heartbeat_at": "2000-01-01T00:00:00Z",
                },
            )

            status = run_status(repo, run_id=plan["run_id"])
            alerts = run_alerts(repo, run_id=plan["run_id"])

            self.assertEqual(
                [item["type"] for item in status["lifecycle_diagnostics"]],
                ["provider_native_spawn_without_report"],
            )
            diagnostic = status["lifecycle_diagnostics"][0]
            self.assertEqual(diagnostic["agent_id"], "worker-001")
            self.assertEqual(diagnostic["evidence_fields"], ["provider_native_agent_id"])
            self.assertEqual(diagnostic["report_path"], f".dispatch/runs/{state_dir.name}/reports/worker-001.json")
            self.assertIn("last_heartbeat_at", diagnostic["stale_since_field"])
            self.assertIn(
                "provider_native_spawn_without_report",
                [alert["type"] for alert in alerts["alerts"]],
            )
            self.assertIn(
                "provider_native_spawn_without_report",
                status["next_actions"][0]["diagnostic_types"],
            )

    def test_fresh_provider_native_agent_without_report_does_not_surface_no_report_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="fresh provider no report objective")
            state_dir = Path(plan["state_dir"])
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-status-tail",
                assigned_files=["scripts/dispatch_engine/state.py"],
                allowed_write_roots=[],
            )
            _update_agent(
                state_dir,
                "worker-001",
                {
                    "provider_native_agent_id": "spawn-agent-001",
                    "last_heartbeat_at": "9999-01-01T00:00:00Z",
                },
            )

            status = run_status(repo, run_id=plan["run_id"])

            self.assertEqual(status["lifecycle_diagnostics"], [])

    def test_stale_validator_without_terminal_report_surfaces_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="stale validator objective")
            state_dir = Path(plan["state_dir"])
            register_agent(
                state_dir,
                agent_id="validator-001",
                role="validator",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-status-tail",
                stdout_path=f".dispatch/runs/{state_dir.name}/logs/validator-001.stdout.log",
                last_heartbeat_at="2000-01-01T00:00:00Z",
            )
            stdout_path = state_dir / "logs" / "validator-001.stdout.log"
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text("validator still running\n", encoding="utf-8")

            status = run_status(repo, run_id=plan["run_id"])
            alerts = run_alerts(repo, run_id=plan["run_id"])

            self.assertEqual(
                [item["type"] for item in status["lifecycle_diagnostics"]],
                ["stale_validation_worker_without_report"],
            )
            diagnostic = status["lifecycle_diagnostics"][0]
            self.assertEqual(diagnostic["agent_id"], "validator-001")
            self.assertEqual(diagnostic["role"], "validator")
            self.assertEqual(diagnostic["report_path"], f".dispatch/runs/{state_dir.name}/validation/validator-001.json")
            self.assertEqual(diagnostic["stale_since_field"], "last_heartbeat_at")
            self.assertEqual(diagnostic["suggested_next_action"], "inspect_wait_cancel_or_rerun_validation")
            self.assertIn(
                "stale_validation_worker_without_report",
                [alert["type"] for alert in alerts["alerts"]],
            )
            self.assertIn(
                "stale_validation_worker_without_report",
                status["next_actions"][0]["diagnostic_types"],
            )

    def test_cancelled_run_preserves_incomplete_validation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="cancelled validation objective")
            state_dir = Path(plan["state_dir"])
            _set_run_status(
                state_dir,
                "cancelled",
                {
                    "cancelled_at": "2026-05-03T00:00:00Z",
                    "cancellation_reason": "Operator cancelled stalled validation.",
                },
            )
            register_agent(
                state_dir,
                agent_id="validator-001",
                role="validator",
                provider="codex",
                profile="codex-exec",
                status="cancelled",
                workstream="01-status-tail",
                stdout_path=f".dispatch/runs/{state_dir.name}/logs/validator-001.stdout.log",
                last_heartbeat_at="2000-01-01T00:00:00Z",
            )
            _update_agent(
                state_dir,
                "validator-001",
                {"cancellation_reason": "Operator cancelled stalled validation."},
            )
            stdout_path = state_dir / "logs" / "validator-001.stdout.log"
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text("validation did not finish\n", encoding="utf-8")

            status = run_status(repo, run_id=plan["run_id"])
            alerts = run_alerts(repo, run_id=plan["run_id"])

            diagnostics = status["lifecycle_diagnostics"]
            self.assertEqual([item["type"] for item in diagnostics], ["incomplete_validation_evidence"])
            diagnostic = diagnostics[0]
            self.assertEqual(diagnostic["agent_id"], "validator-001")
            self.assertEqual(diagnostic["status"], "cancelled")
            self.assertEqual(diagnostic["report_path"], f".dispatch/runs/{state_dir.name}/validation/validator-001.json")
            self.assertEqual(diagnostic["terminal_reason"], "Operator cancelled stalled validation.")
            self.assertIn("incomplete_validation_evidence", [alert["type"] for alert in alerts["alerts"]])

    def test_status_and_alerts_surface_stdout_only_decision_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="stdout decision objective")
            state_dir = Path(plan["state_dir"])
            register_agent(
                state_dir,
                agent_id="coordinator-001",
                role="coordinator",
                provider="codex",
                profile="codex-exec",
                status="completed",
                stdout_path=f".dispatch/runs/{state_dir.name}/logs/coordinator-001.stdout.log",
            )
            stdout_path = state_dir / "logs" / "coordinator-001.stdout.log"
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text(
                "I need your decision before proceeding.\nApprove expanding the scope?\n",
                encoding="utf-8",
            )

            status = run_status(repo, run_id=plan["run_id"])
            alerts = run_alerts(repo, run_id=plan["run_id"])

            diagnostics = status["lifecycle_diagnostics"]
            self.assertEqual([item["type"] for item in diagnostics], ["stdout_only_decision_request"])
            self.assertIn("decision before proceeding", diagnostics[0]["matched_text"])
            self.assertIn(
                "stdout_only_decision_request",
                [alert["type"] for alert in alerts["alerts"]],
            )

    def test_status_and_alerts_surface_report_only_decision_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="report decision objective")
            state_dir = Path(plan["state_dir"])
            register_agent(
                state_dir,
                agent_id="coordinator-001",
                role="coordinator",
                provider="codex",
                profile="codex-exec",
                status="completed",
            )
            report_path = state_dir / "reports" / "coordinator-001.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "agent_id": "coordinator-001",
                        "role": "coordinator",
                        "status": "completed",
                        "summary": "Approval is required before continuing.",
                        "decisions_required": [
                            {
                                "decision_id": "decision-approve-expanded-scope",
                                "question": "Approve expanding worker scope?",
                                "workstream": "01-status-tail",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            status = run_status(repo, run_id=plan["run_id"])
            alerts = run_alerts(repo, run_id=plan["run_id"])

            diagnostics = status["lifecycle_diagnostics"]
            self.assertEqual([item["type"] for item in diagnostics], ["report_only_decision_request"])
            diagnostic = diagnostics[0]
            self.assertEqual(diagnostic["agent_id"], "coordinator-001")
            self.assertEqual(diagnostic["decision_ids"], ["decision-approve-expanded-scope"])
            self.assertEqual(diagnostic["questions"], ["Approve expanding worker scope?"])
            self.assertEqual(diagnostic["workstreams"], ["01-status-tail"])
            self.assertEqual(
                diagnostic["report_path"],
                f".dispatch/runs/{state_dir.name}/reports/coordinator-001.json",
            )
            self.assertIn(
                "report_only_decision_request",
                [alert["type"] for alert in alerts["alerts"]],
            )
            self.assertIn(
                "report_only_decision_request",
                status["next_actions"][0]["diagnostic_types"],
            )

    def test_alerts_normalize_legacy_capability_protocol_violation_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="legacy capability event objective")
            state_dir = Path(plan["state_dir"])
            append_event(
                state_dir / "events.jsonl",
                "protocol.violation",
                workstream="01-status-tail",
                payload={
                    "agent_id": "worker-001",
                    "capability": "test_execution",
                    "requested_mode": "unrestricted",
                    "granted_mode": "allow-listed",
                    "evidence": "legacy dogfood payload",
                },
            )

            alerts = run_alerts(repo, run_id=plan["run_id"])

            protocol_alerts = [
                alert for alert in alerts["alerts"] if alert["type"] == "protocol_violation"
            ]
            self.assertEqual([alert["violation"] for alert in protocol_alerts], ["capability_overreach"])
            self.assertEqual(protocol_alerts[0]["agent_id"], "worker-001")
            self.assertEqual(protocol_alerts[0]["details"]["source"], "legacy_protocol_violation_payload")
            self.assertEqual(protocol_alerts[0]["details"]["payload"]["capability"], "test_execution")

    def test_status_splits_resolved_and_unresolved_protocol_violations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="protocol resolution objective")
            state_dir = Path(plan["state_dir"])
            protocol_violation(
                state_dir / "events.jsonl",
                violation="missing_worker_report",
                details={"agent_id": "worker-001"},
                workstream="01-status-tail",
            )
            protocol_violation(
                state_dir / "events.jsonl",
                violation="out_of_scope_changed_file",
                details={"agent_id": "worker-002"},
                workstream="02-status-tail",
            )

            resolve_protocol_violation(
                state_dir,
                violation="missing_worker_report",
                resolution="accepted_with_concerns",
                rationale="The report was later reconstructed from validation evidence.",
                evidence="validation/validator-001.json",
                agent_id="worker-001",
                workstream="01-status-tail",
                actor="interactive-codex",
            )

            status = run_status(repo, run_id=plan["run_id"])

            protocol_status = status["protocol_violations"]
            self.assertEqual(protocol_status["count"], 2)
            self.assertEqual(protocol_status["resolved_count"], 1)
            self.assertEqual(protocol_status["unresolved_count"], 1)
            self.assertEqual(protocol_status["resolved"][0]["violation"], "missing_worker_report")
            self.assertEqual(protocol_status["unresolved"][0]["violation"], "out_of_scope_changed_file")
            self.assertEqual(status["protocol_violation_resolutions"]["count"], 1)
            self.assertEqual(
                [action for action in status["next_actions"] if action["type"] == "repair_protocol_violations"],
                [{"type": "repair_protocol_violations", "count": 1}],
            )

    def test_resolution_record_matches_original_violation_not_future_broad_selector_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="broad selector audit objective")
            state_dir = Path(plan["state_dir"])
            protocol_violation(
                state_dir / "events.jsonl",
                violation="missing_worker_report",
                details={"agent_id": "worker-001"},
                workstream="01-status-tail",
            )
            resolve_protocol_violation(
                state_dir,
                violation="missing_worker_report",
                resolution="acknowledged",
                rationale="Single current violation was reviewed.",
                evidence="Operator review note.",
                actor="interactive-codex",
            )
            protocol_violation(
                state_dir / "events.jsonl",
                violation="missing_worker_report",
                details={"agent_id": "worker-002"},
                workstream="02-status-tail",
            )

            status = run_status(repo, run_id=plan["run_id"])

            self.assertEqual(status["protocol_violations"]["resolved_count"], 1)
            self.assertEqual(status["protocol_violations"]["unresolved_count"], 1)
            self.assertEqual(status["protocol_violations"]["unresolved"][0]["agent_id"], "worker-002")

    def test_alerts_skip_resolved_protocol_violations_and_legacy_kind_normalizes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="resolved alerts objective")
            state_dir = Path(plan["state_dir"])
            append_event(
                state_dir / "events.jsonl",
                "protocol.violation",
                workstream="01-status-tail",
                payload={
                    "kind": "capability_overreach",
                    "agent_id": "worker-001",
                    "capability": "test_execution",
                    "requested_mode": "unrestricted",
                    "granted_mode": "allow-listed",
                    "evidence": "legacy kind payload",
                },
            )
            protocol_violation(
                state_dir / "events.jsonl",
                violation="missing_worker_report",
                details={"agent_id": "worker-002"},
                workstream="02-status-tail",
            )
            resolve_protocol_violation(
                state_dir,
                violation="capability_overreach",
                resolution="false_positive",
                rationale="The payload reflected an allowed validation command.",
                evidence="Operator reviewed the validator command list.",
                agent_id="worker-001",
                workstream="01-status-tail",
                actor="interactive-codex",
            )

            alerts = run_alerts(repo, run_id=plan["run_id"])

            protocol_alerts = [alert for alert in alerts["alerts"] if alert["type"] == "protocol_violation"]
            self.assertEqual([alert["violation"] for alert in protocol_alerts], ["missing_worker_report"])
            status = run_status(repo, run_id=plan["run_id"])
            self.assertEqual(status["protocol_violations"]["resolved"][0]["violation"], "capability_overreach")
            self.assertEqual(
                status["protocol_violations"]["resolved"][0]["details"]["payload"]["kind"],
                "capability_overreach",
            )


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


def _set_run_status(state_dir: Path, status: str, extra: dict | None = None) -> None:
    run_path = state_dir / "run.json"
    run = json.loads(run_path.read_text(encoding="utf-8"))
    run["status"] = status
    run["updated_at"] = "2026-05-03T00:00:00Z"
    if extra:
        run.update(extra)
    run_path.write_text(json.dumps(run, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _update_agent(state_dir: Path, agent_id: str, fields: dict) -> None:
    agent_path = state_dir / "agents" / f"{agent_id}.json"
    agent = json.loads(agent_path.read_text(encoding="utf-8"))
    agent.update(fields)
    agent_path.write_text(json.dumps(agent, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _update_workstream(state_dir: Path, workstream_id: str, fields: dict) -> None:
    workstream_path = state_dir / "workstreams" / f"{workstream_id}.json"
    workstream = json.loads(workstream_path.read_text(encoding="utf-8"))
    workstream.update(fields)
    workstream_path.write_text(json.dumps(workstream, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_report(state_dir: Path, agent_id: str) -> None:
    report_path = state_dir / "reports" / f"{agent_id}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("{}\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
