from __future__ import annotations

import contextlib
import io
import json
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from dispatch_engine.agents import (
    append_agent_heartbeat,
    register_agent,
    register_worker_agent,
    write_validator_report,
    write_worker_report,
)
from dispatch_engine.cli import main
from dispatch_engine.dashboard import _run_history, launch_dashboard
from dispatch_engine.events import append_event
from dispatch_engine.plan_schema import import_dispatch_plan


class DashboardObserverTests(unittest.TestCase):
    def test_detach_status_reuse_and_stop_lifecycle_records_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)

            first = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])

            self.assertEqual(first["kind"], "dashboard")
            self.assertEqual(first["status"], "running")
            self.assertEqual(first["run_id"], run["run_id"])
            self.assertEqual(first["state_dir"], run["state_dir"])
            self.assertTrue(first["url"].startswith("http://127.0.0.1:"))
            self.assertGreater(first["pid"], 0)

            metadata_path = Path(first["state_dir"]) / "dashboard" / "server.json"
            stdout_path = Path(first["state_dir"]) / "dashboard" / "server.stdout.log"
            stderr_path = Path(first["state_dir"]) / "dashboard" / "server.stderr.log"
            self.assertTrue(metadata_path.is_file())
            self.assertTrue(stdout_path.is_file())
            self.assertTrue(stderr_path.is_file())

            status_payload = _get_json(first["url"] + "/api/status")
            self.assertEqual(status_payload["kind"], "status")
            self.assertEqual(status_payload["run_id"], run["run_id"])

            second = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            self.assertEqual(second["status"], "reused")
            self.assertEqual(second["url"], first["url"])
            self.assertEqual(second["pid"], first["pid"])

            recorded = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--status", "--json"])
            self.assertEqual(recorded["kind"], "dashboard_status")
            self.assertEqual(recorded["status"], "running")
            self.assertTrue(recorded["alive"])
            self.assertEqual(recorded["url"], first["url"])

            stopped = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--stop", "--json"])
            self.assertEqual(stopped["kind"], "dashboard_stop")
            self.assertEqual(stopped["status"], "stopped")
            self.assertFalse(stopped["alive"])

            after_stop = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--status", "--json"])
            self.assertEqual(after_stop["status"], "stopped")
            self.assertFalse(after_stop["alive"])

    def test_api_errors_are_json_for_invalid_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            try:
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    urllib.request.urlopen(server["url"] + "/api/events?since=not-a-cursor", timeout=5)

                self.assertEqual(raised.exception.code, 400)
                payload = json.loads(raised.exception.read().decode("utf-8"))
                raised.exception.close()
                self.assertEqual(payload["kind"], "error")
                self.assertEqual(payload["status"], "invalid_event_cursor")
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_missing_run_and_asset_errors_are_codex_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            missing_run = _run_cli_json(["dashboard", str(repo), "--detach", "--json"], expected_exit=1)
            self.assertEqual(missing_run["kind"], "error")
            self.assertEqual(missing_run["status"], "no_run")

            run = _import_plan(repo)
            missing_asset = launch_dashboard(
                repo,
                run_id=run["run_id"],
                detach=True,
                dashboard_dir=repo / "does-not-exist",
            )
            self.assertEqual(missing_asset["kind"], "error")
            self.assertEqual(missing_asset["status"], "missing_dashboard_assets")
            self.assertIn("dashboard/index.html", missing_asset["summary"])

    def test_api_requests_do_not_mutate_run_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            (state_dir / "logs" / "coordinator-001.stdout.log").write_text("hello\n", encoding="utf-8")
            (state_dir / "logs" / "coordinator-001.stderr.log").write_text("warn\n", encoding="utf-8")
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                _get_json(server["url"] + "/api/status")
                _get_json(server["url"] + "/api/events")
                _get_json(server["url"] + "/api/alerts")
                _get_json(server["url"] + "/api/tail")
                logs = _get_json(server["url"] + "/api/logs/coordinator")
                history = _get_json(server["url"] + "/api/history")

                self.assertEqual(logs["stdout"], "hello\n")
                self.assertEqual(logs["stderr"], "warn\n")
                self.assertEqual(history["runs"][0]["run_id"], run["run_id"])
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_history_api_returns_stable_derived_fields_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            run_file = state_dir / "run.json"
            run_data = json.loads(run_file.read_text(encoding="utf-8"))
            run_data["status"] = "completed"
            run_data["started_at"] = "2026-05-05T01:00:00Z"
            run_data["completed_at"] = "2026-05-05T01:05:30Z"
            run_data["updated_at"] = "2026-05-05T01:05:30Z"
            run_file.write_text(json.dumps(run_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            register_worker_agent(
                state_dir,
                agent_id="worker-a",
                provider="codex",
                profile="codex-spawn-agent-worker",
                workstream="01-dashboard",
                assigned_files=["scripts/dispatch_engine/dashboard.py"],
                allowed_write_roots=["scripts/dispatch_engine/"],
                status="completed",
            )
            write_worker_report(
                state_dir,
                "worker-a",
                {
                    "status": "completed",
                    "changed_files": [
                        {"path": "scripts/dispatch_engine/dashboard.py", "status": "modified"},
                        {"path": "dashboard/app.js", "status": "modified"},
                    ],
                    "validation": [
                        {"command": "python3 scripts/de.py dashboard --help", "status": "passed"},
                        {"command": "git diff --check", "status": "passed"},
                    ],
                },
            )
            register_agent(
                state_dir,
                agent_id="validator-a",
                role="validator",
                provider="codex",
                profile="codex-spawn-agent-validator",
                status="completed",
            )
            write_validator_report(
                state_dir,
                "validator-a",
                {
                    "status": "passed",
                    "summary": "focused validation",
                    "artifacts": [],
                    "validation": [
                        {"command": "PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer", "status": "passed"},
                    ],
                },
            )
            (state_dir / "decisions.jsonl").write_text(
                json.dumps({"id": "decision-1", "status": "resolved"}) + "\n"
                + json.dumps({"id": "decision-2", "status": "pending"}) + "\n",
                encoding="utf-8",
            )
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                history = _get_json(server["url"] + "/api/history")

                self.assertEqual(history["kind"], "history")
                self.assertEqual(history["status"], "ok")
                self.assertEqual(history["run_count"], 1)
                row = history["runs"][0]
                self.assertEqual(row["run_id"], run["run_id"])
                self.assertEqual(row["short_id"], run["run_id"][:8])
                self.assertEqual(row["repo"], str(repo.resolve()))
                self.assertEqual(row["repo_name"], repo.resolve().name)
                self.assertEqual(row["plan_id"], "plan-001")
                self.assertEqual(row["objective"], "dashboard observer objective")
                self.assertEqual(row["status"], "completed")
                self.assertEqual(row["started_at"], "2026-05-05T01:00:00Z")
                self.assertEqual(row["completed_at"], "2026-05-05T01:05:30Z")
                self.assertEqual(row["duration_ms"], 330000)
                self.assertEqual(row["worker_count"], 1)
                self.assertEqual(row["agent_count"], 2)
                self.assertEqual(row["decision_count"], 2)
                self.assertEqual(row["pending_decision_count"], 1)
                self.assertEqual(row["files_changed_count"], 2)
                self.assertEqual(row["tests_passed"], 3)
                self.assertEqual(row["tests_total"], 3)
                self.assertEqual(row["terminal_reason"], None)
                self.assertIn("--run-id", row["dashboard_command_preview"])
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_history_api_empty_history_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            history = _run_history(repo)

            self.assertEqual(history["kind"], "history")
            self.assertEqual(history["status"], "ok")
            self.assertEqual(history["run_count"], 0)
            self.assertEqual(history["runs"], [])
            self.assertTrue(history["empty_states"]["runs"])

    def test_plan_api_returns_imported_plan_tree_and_dependency_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                payload = _get_json(server["url"] + "/api/plan")

                self.assertEqual(payload["kind"], "plan")
                self.assertEqual(payload["status"], "ok")
                self.assertEqual(payload["run_id"], run["run_id"])
                self.assertEqual(payload["plan_id"], "plan-001")
                self.assertEqual(payload["source_path"], str((repo / ".dispatch" / "plans" / "plan-001.json").resolve()))
                self.assertEqual(payload["tree"]["id"], "plan-001")
                self.assertEqual(payload["tree"]["type"], "plan")
                self.assertEqual(payload["tree"]["children"][0]["id"], "phase: serial")
                leaves = payload["tree"]["children"][0]["children"]
                self.assertEqual([leaf["id"] for leaf in leaves], ["01-dashboard", "02-agent-detail", "03-plan-explorer"])
                self.assertEqual(leaves[2]["depends_on"], ["02-agent-detail"])
                self.assertEqual(leaves[2]["dependency_labels"], ["02-agent-detail"])
                self.assertEqual(leaves[2]["file_count"], 2)
                self.assertEqual(leaves[2]["validation_count"], 1)
                self.assertEqual(payload["empty_states"]["plan"], False)
                self.assertEqual(payload["empty_states"]["workstreams"], False)
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_status_and_plan_apis_share_durable_workstream_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            _update_workstream(
                state_dir,
                "01-dashboard",
                {
                    "status": "assigned",
                    "state": "assigned",
                    "assigned_agent": "worker-a",
                    "updated_at": "2026-05-06T00:00:00Z",
                },
            )
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                status = _get_json(server["url"] + "/api/status")
                plan = _get_json(server["url"] + "/api/plan")

                self.assertEqual(status["workstream_counts"]["assigned"], 1)
                self.assertEqual(status["workstream_progress"]["assigned"], 1)
                self.assertEqual(status["workstream_progress"]["unassigned"], 2)
                self.assertEqual(
                    status["workstream_assignments"],
                    [
                        {
                            "workstream": "01-dashboard",
                            "agent_id": "worker-a",
                            "role": "worker",
                            "status": "assigned",
                        }
                    ],
                )
                dashboard_leaf = plan["tree"]["children"][0]["children"][0]
                self.assertEqual(dashboard_leaf["id"], "01-dashboard")
                self.assertEqual(dashboard_leaf["status"], "assigned")
                self.assertEqual(dashboard_leaf["agent_id"], "worker-a")
                self.assertEqual(plan["tree"]["status"], "running")
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_status_and_plan_apis_share_terminal_event_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            append_event(
                state_dir / "events.jsonl",
                "workstream.assigned",
                workstream="01-dashboard",
                payload={"agent_id": "worker-terminal", "role": "worker"},
            )
            _update_workstream(
                state_dir,
                "01-dashboard",
                {
                    "status": "cancelled",
                    "state": "cancelled",
                    "updated_at": "2026-05-06T00:00:00Z",
                },
            )
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                status = _get_json(server["url"] + "/api/status")
                plan = _get_json(server["url"] + "/api/plan")

                self.assertEqual(status["workstream_counts"]["cancelled"], 1)
                self.assertEqual(
                    status["workstream_assignments"],
                    [
                        {
                            "workstream": "01-dashboard",
                            "agent_id": "worker-terminal",
                            "role": "worker",
                            "status": "cancelled",
                        }
                    ],
                )
                dashboard_leaf = plan["tree"]["children"][0]["children"][0]
                self.assertEqual(dashboard_leaf["id"], "01-dashboard")
                self.assertEqual(dashboard_leaf["status"], "cancelled")
                self.assertEqual(dashboard_leaf["agent_id"], "worker-terminal")
                self.assertEqual(plan["tree"]["status"], "queued")
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_agent_detail_api_returns_logs_report_heartbeat_and_empty_states(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            register_worker_agent(
                state_dir,
                agent_id="worker-a",
                provider="codex",
                profile="codex-spawn-agent-worker",
                workstream="01-dashboard",
                assigned_files=["scripts/dispatch_engine/dashboard.py"],
                allowed_write_roots=["scripts/dispatch_engine/"],
                status="running",
            )
            append_agent_heartbeat(state_dir, "worker-a", status="running", payload={"note": "still active"})
            write_worker_report(
                state_dir,
                "worker-a",
                {
                    "status": "completed",
                    "changed_files": [{"path": "scripts/dispatch_engine/dashboard.py", "status": "modified"}],
                    "capabilities_exercised": [{"capability": "test_execution", "mode": "allow-listed"}],
                },
            )
            (state_dir / "logs" / "worker-a.stdout.log").write_text("stdout line\n", encoding="utf-8")
            (state_dir / "logs" / "worker-a.stderr.log").write_text("stderr line\n", encoding="utf-8")
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                detail = _get_json(server["url"] + "/api/agent/worker-a")

                self.assertEqual(detail["kind"], "agent_detail")
                self.assertEqual(detail["status"], "ok")
                self.assertEqual(detail["agent"]["agent_id"], "worker-a")
                self.assertEqual(detail["logs"]["stdout"], "stdout line\n")
                self.assertEqual(detail["logs"]["stderr"], "stderr line\n")
                self.assertEqual(detail["report"]["status"], "completed")
                self.assertEqual(detail["changed_files"][0]["path"], "scripts/dispatch_engine/dashboard.py")
                self.assertEqual(detail["heartbeat_samples"][0]["status"], "running")
                self.assertEqual(detail["capabilities_exercised"][0]["capability"], "test_execution")
                self.assertFalse(detail["empty_states"]["report"])
                self.assertFalse(detail["empty_states"]["changed_files"])
                self.assertFalse(detail["empty_states"]["heartbeat_samples"])
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_agent_detail_api_exposes_stale_validator_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            register_agent(
                state_dir,
                agent_id="validator-a",
                role="validator",
                provider="codex",
                profile="codex-spawn-agent-validator",
                status="running",
                workstream="01-dashboard",
                stdout_path=f".dispatch/runs/{state_dir.name}/logs/validator-a.stdout.log",
                last_heartbeat_at="2000-01-01T00:00:00Z",
            )
            stdout_path = state_dir / "logs" / "validator-a.stdout.log"
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text("validator started\n", encoding="utf-8")
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                detail = _get_json(server["url"] + "/api/agent/validator-a")

                self.assertEqual(detail["kind"], "agent_detail")
                self.assertEqual(detail["status"], "ok")
                self.assertEqual(detail["validation_evidence"]["expected_report_path"], str(state_dir / "validation" / "validator-a.json"))
                self.assertFalse(detail["validation_evidence"]["terminal_report_present"])
                self.assertEqual(
                    [item["type"] for item in detail["validation_evidence"]["lifecycle_diagnostics"]],
                    ["stale_validation_worker_without_report"],
                )
                self.assertTrue(detail["empty_states"]["report"])
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_agent_detail_api_exposes_validator_report_schema_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            register_agent(
                state_dir,
                agent_id="validator-a",
                role="validator",
                provider="codex",
                profile="codex-spawn-agent-validator",
                status="completed",
                workstream="01-dashboard",
            )
            write_validator_report(
                state_dir,
                "validator-a",
                {
                    "schema_version": 1,
                    "agent_id": "validator-a",
                    "role": "validator",
                    "workstream": "01-dashboard",
                    "status": "passed",
                    "summary": "Focused validation passed but artifacts are missing.",
                    "command": "PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer",
                    "output_summary": "tests passed",
                    "artifacts": [],
                    "not_run_reason": "",
                },
            )
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                detail = _get_json(server["url"] + "/api/agent/validator-a")

                diagnostics = detail["validation_evidence"]["report_schema_diagnostics"]
                self.assertEqual([item["violation"] for item in diagnostics], ["missing_validation_evidence"])
                self.assertEqual(diagnostics[0]["details"]["missing_fields"], ["artifacts"])
                self.assertEqual(
                    diagnostics[0]["details"]["repair_action"],
                    "add validator artifact references or change the report to skipped with not_run_reason",
                )
                self.assertFalse(detail["validation_evidence"]["empty_states"]["report_schema_diagnostics"])
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_agent_detail_api_reports_missing_detail_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    urllib.request.urlopen(server["url"] + "/api/agent/missing-agent", timeout=5)

                self.assertEqual(raised.exception.code, 404)
                payload = json.loads(raised.exception.read().decode("utf-8"))
                raised.exception.close()
                self.assertEqual(payload["kind"], "error")
                self.assertEqual(payload["status"], "agent_not_found")
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_host_heartbeat_api_reads_run_scoped_snapshot_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            heartbeat_path = state_dir / "host-heartbeat.json"
            heartbeat_path.write_text(
                json.dumps(
                    {
                        "automation_id": "dispatch-engine-test-heartbeat",
                        "owner": "interactive-codex",
                        "interval_seconds": 900,
                        "status": "active",
                        "last_wakeup_at": "2026-05-05T01:15:00Z",
                        "next_wakeup_at": "2026-05-05T01:30:00Z",
                        "last_observed_cursor": "event-000010",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                payload = _get_json(server["url"] + "/api/host-heartbeat")

                self.assertEqual(payload["kind"], "host_heartbeat")
                self.assertEqual(payload["status"], "ok")
                self.assertEqual(payload["source"], "record")
                self.assertEqual(payload["source_path"], str(heartbeat_path))
                self.assertEqual(payload["automation_id"], "dispatch-engine-test-heartbeat")
                self.assertEqual(payload["owner"], "interactive-codex")
                self.assertEqual(payload["interval_seconds"], 900)
                self.assertEqual(payload["heartbeat_status"], "active")
                self.assertEqual(payload["effective_status"], "active")
                self.assertTrue(payload["active"])
                self.assertEqual(payload["last_wakeup_at"], "2026-05-05T01:15:00Z")
                self.assertEqual(payload["next_wakeup_at"], "2026-05-05T01:30:00Z")
                self.assertEqual(payload["last_observed_cursor"], "event-000010")
                self.assertFalse(payload["empty_states"]["record"])
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_host_heartbeat_api_reads_snapshot_written_by_record_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            _run_cli_json(
                [
                    "record-host-heartbeat",
                    str(repo),
                    "--run-id",
                    run["run_id"],
                    "--automation-id",
                    "dispatch-engine-test-heartbeat",
                    "--owner",
                    "interactive-codex",
                    "--status",
                    "active",
                    "--interval-seconds",
                    "900",
                    "--last-wakeup-at",
                    "2026-05-05T01:15:00Z",
                    "--last-observed-cursor",
                    "event-000010",
                    "--json",
                ]
            )
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                payload = _get_json(server["url"] + "/api/host-heartbeat")

                self.assertEqual(payload["kind"], "host_heartbeat")
                self.assertEqual(payload["source"], "record")
                self.assertEqual(payload["source_path"], str(state_dir / "host-heartbeat.json"))
                self.assertEqual(payload["automation_id"], "dispatch-engine-test-heartbeat")
                self.assertEqual(payload["effective_status"], "active")
                self.assertEqual(payload["next_wakeup_at"], "2026-05-05T01:30:00Z")
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_host_heartbeat_api_ignores_non_run_scoped_snapshot_for_active_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            legacy_path = repo / ".dispatch" / "host-heartbeat.json"
            legacy_path.write_text(
                json.dumps(
                    {
                        "automation_id": "legacy-heartbeat",
                        "owner": "interactive-codex",
                        "interval_seconds": 900,
                        "status": "active",
                        "last_wakeup_at": "2026-05-05T01:15:00Z",
                        "next_wakeup_at": "2026-05-05T01:30:00Z",
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                payload = _get_json(server["url"] + "/api/host-heartbeat")

                self.assertEqual(payload["kind"], "host_heartbeat")
                self.assertEqual(payload["source"], "missing")
                self.assertEqual(payload["automation_id"], None)
                self.assertEqual(payload["effective_status"], "missing")
                self.assertEqual(payload["source_path"], None)
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_host_heartbeat_api_derives_terminal_stop_when_snapshot_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            state_dir = Path(run["state_dir"])
            run_file = state_dir / "run.json"
            run_data = json.loads(run_file.read_text(encoding="utf-8"))
            run_data["status"] = "completed"
            run_data["completed_at"] = "2026-05-05T01:45:00Z"
            run_data["updated_at"] = "2026-05-05T01:45:00Z"
            run_file.write_text(json.dumps(run_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            before = _evidence_snapshot(state_dir)
            try:
                payload = _get_json(server["url"] + "/api/host-heartbeat")

                self.assertEqual(payload["kind"], "host_heartbeat")
                self.assertEqual(payload["source"], "derived_terminal")
                self.assertEqual(payload["heartbeat_status"], "missing")
                self.assertEqual(payload["effective_status"], "stopped")
                self.assertFalse(payload["active"])
                self.assertEqual(payload["stopped_at"], "2026-05-05T01:45:00Z")
                self.assertEqual(payload["stop_reason"], "terminal run reached")
                self.assertTrue(payload["empty_states"]["record"])
                self.assertEqual(_evidence_snapshot(state_dir), before)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_static_dashboard_assets_are_served_from_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = _import_plan(repo)
            server = _run_cli_json(["dashboard", str(repo), "--run-id", run["run_id"], "--detach", "--json"])
            try:
                index = _get_text(server["url"])
                script = _get_text(server["url"] + "/app.js")
                styles = _get_text(server["url"] + "/styles.css")

                self.assertIn("Dispatch Engine Dashboard", index)
                self.assertIn("./styles.css", index)
                self.assertIn("./app.js", index)
                self.assertIn("/api/status", script)
                self.assertIn("/api/history", script)
                self.assertIn("/api/plan", script)
                self.assertIn("/api/host-heartbeat", script)
                self.assertIn("dispatch-engine.dashboard.theme", script)
                self.assertIn("Keyboard Shortcuts", script)
                self.assertIn("Plan & workstreams", script)
                self.assertIn("Plan tree", script)
                self.assertIn("Coordinator stdout / stderr", script)
                self.assertIn("No plan tree available", script)
                self.assertIn("[\"solar\", name: \"Solar\"", script.replace("{ id: ", "["))
                self.assertIn("data-theme", styles)
                self.assertIn(".settings-popover", styles)
                self.assertIn(".modal-bg", styles)
                self.assertIn("ui-zoomed", styles)
                self.assertIn(".plan-screen", styles)
                self.assertIn(".coord-terminal", styles)
                self.assertIn(".app-shell", styles)
                self.assertIn("/api/agent/", script)
                self.assertIn("Agent detail", script)
                self.assertIn("No report yet", script)
                self.assertIn("No heartbeat samples recorded", script)
                self.assertIn("Decision Preview", script)
                self.assertIn("Capability Review", script)
                self.assertIn("resolve-decision", script)
                self.assertIn("resolve-protocol-violation", script)
                self.assertIn("includeToolCalls", script)
                self.assertIn("keepArtifacts", script)
                self.assertIn("Audit note", script)
                self.assertIn("TTL", script)
                self.assertIn("Open Run Preview", script)
                self.assertIn("SCENARIO_IDS", script)
                self.assertIn("fixtureScenarioFromLocation", script)
                self.assertIn("violation-flash", script)
                self.assertIn("coordinator-dead", script)
                self.assertIn("Fixture mode", script)
                self.assertIn("No active run", script)
                self.assertIn("clock frozen", script)
                self.assertIn("Export CSV", script)
                self.assertIn("Select two rows to compare", script)
                self.assertIn("dashboard_command_preview", script)
                self.assertIn("filteredHistoryRows", script)
                self.assertIn(".run-switcher", styles)
                self.assertIn(".scenario-banner", styles)
                self.assertIn(".fixture-strip", styles)
                self.assertIn(".empty-dashboard", styles)
                self.assertIn(".run-hero.state-violation-flash", styles)
                self.assertIn(".history-toolbar", styles)
                self.assertIn(".rh-compare", styles)
                self.assertIn("modalContext", script)
                self.assertIn("command-actions", script)
                self.assertIn(".agent-detail", styles)
                self.assertIn(".hb-mini", styles)
                self.assertIn(".modal-footer", styles)
                self.assertIn(".impact-grid", styles)
                self.assertIn(".option-row", styles)
                self.assertIn(".command-actions", styles)
                self.assertIn("tailFilter", script)
                self.assertIn("renderTailFilters", script)
                self.assertIn("tailCollapsed", script)
                self.assertIn("tailHeight", script)
                self.assertIn("renderTailResizeHandle", script)
                self.assertIn("startTailResize", script)
                self.assertIn("compactLogTime", script)
                self.assertIn("log-message", script)
                self.assertIn("split-counts", script)
                self.assertIn(".split-counts", styles)
                self.assertIn(".tail-filters", styles)
                self.assertIn(".tail-toggle", styles)
                self.assertIn(".tail-resize", styles)
                self.assertIn(".footer-tail.collapsed", styles)
                self.assertIn(".event-message", styles)
                self.assertIn(".log-message", styles)
                self.assertIn("word-break: break-word", styles)
                self.assertIn("flex: 0 0 8px", styles)
                self.assertIn("padding: 12px 14px", styles)
                self.assertIn("scrollMemory", script)
                self.assertIn("rememberScrollPositions", script)
                self.assertIn("restoreScrollPositions", script)
                self.assertIn("data-scroll-key", script)
                self.assertIn("event-tail:", script)
                self.assertIn("modal-body:", script)
                self.assertIn("overview-command", script)
                self.assertIn("Host heartbeat", script)
                self.assertIn("Pending decisions", script)
                self.assertIn("updateLiveHeartbeatClocks", script)
                self.assertIn("data-heartbeat-interval", script)
                self.assertIn("data-heartbeat-active", script)
                self.assertIn("humanDuration", script)
                self.assertIn("Host heartbeat ", script)
                self.assertIn("hostHeartbeatState", script)
                self.assertIn("state unavailable", script)
                self.assertIn('DEFAULT_THEME = "carbon"', script)
                self.assertIn("DEFAULT_ZOOM = 0.9", script)
                self.assertIn("THEME_OPTIONS", script)
                self.assertIn("overview-run-header", styles)
                self.assertIn("overview-work-row", styles)
                self.assertIn("grid-template-rows: 30px 14px", styles)
                self.assertIn("overflow-wrap: anywhere", styles)
                self.assertIn(".hb-ring", styles)
                self.assertIn(".hb-ring.stopped", styles)
                self.assertIn(".hb-ring.missing", styles)
                self.assertIn("flex-direction: column", styles)
                self.assertIn(".hb-actions .btn-sm.icon", styles)
                self.assertIn("@media (max-width: 1280px)", styles)
                self.assertIn("@media (max-width: 680px)", styles)
                self.assertIn("flex: 0 0 auto", styles)
                self.assertIn("flex-direction: row", styles)
                self.assertIn("overflow-x: auto", styles)
                self.assertIn("scrollbar-width: none", styles)
                self.assertIn("min-height: 140px", styles)
                self.assertIn("flex: 0 0 auto", styles)
                self.assertIn("max-height: 260px", styles)
                self.assertIn(".footer-tail.collapsed", styles)
                self.assertIn("min-height: 0", styles)
                self.assertIn("order: 3", styles)
                self.assertIn(".topbar > *", styles)
                self.assertIn("overflow-y: hidden", styles)
                self.assertIn("min-width: max-content", styles)
            finally:
                _stop_dashboard(repo, run["run_id"])

    def test_prototype_parity_report_covers_required_worker_010_sections(self) -> None:
        parity_path = (
            Path(__file__).resolve().parents[1]
            / "specs"
            / "rfc-0024-dashboard-autostart-observer"
            / "PROTOTYPE_PARITY.md"
        )
        text = parity_path.read_text(encoding="utf-8")

        self.assertIn("## Workstream 10 Parity Matrix", text)
        self.assertIn("## Data Parity Report", text)
        self.assertIn("## Icon Audit", text)
        self.assertIn("coordinator-owned screenshot pending", text)
        self.assertIn("Iconography, icon-only controls, status marks, favicon, hit targets, tooltips", text)
        self.assertIn("Scenario catalog: empty, starting, running, waiting-input, violation-flash, disconnected, coordinator-dead, completed, cancelled, failed", text)
        self.assertIn("`RUN.id`, `short`, `repo`, `repoPath`, `plan`, `provider`, `mode`, `startedAt`, `status`, `coordinator`, `objective`", text)
        self.assertIn("`EVENT_TEMPLATES` streaming feed", text)
        self.assertIn("Fixture/demo scenario data", text)
        self.assertIn("Write-like actions: cancel, resolve decision, grant/deny capability, run switch", text)


def _run_cli_json(argv: list[str], *, expected_exit: int = 0) -> dict:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        exit_code = main(argv)
    payload = json.loads(stdout.getvalue())
    if exit_code != expected_exit:
        raise AssertionError(f"expected exit {expected_exit}, got {exit_code}: {payload}")
    return payload


def _get_json(url: str) -> dict:
    deadline = time.monotonic() + 5
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # pragma: no cover - assertion includes last error
            last_error = exc
            time.sleep(0.05)
    raise AssertionError(f"GET {url} did not return JSON: {last_error}")


def _get_text(url: str) -> str:
    deadline = time.monotonic() + 5
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return response.read().decode("utf-8")
        except Exception as exc:  # pragma: no cover - assertion includes last error
            last_error = exc
            time.sleep(0.05)
    raise AssertionError(f"GET {url} did not return text: {last_error}")


def _stop_dashboard(repo: Path, run_id: str) -> None:
    with contextlib.suppress(Exception):
        _run_cli_json(["dashboard", str(repo), "--run-id", run_id, "--stop", "--json"])


def _evidence_snapshot(state_dir: Path) -> dict[str, str]:
    return {
        name: (state_dir / name).read_text(encoding="utf-8") if (state_dir / name).exists() else "<missing>"
        for name in ("run.json", "events.jsonl", "decisions.jsonl", "host-heartbeat.json")
    }


def _import_plan(repo: Path) -> dict:
    plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(_plan()) + "\n", encoding="utf-8")
    return import_dispatch_plan(repo, plan_path)


def _update_workstream(state_dir: Path, workstream_id: str, fields: dict) -> None:
    workstream_path = state_dir / "workstreams" / f"{workstream_id}.json"
    workstream = json.loads(workstream_path.read_text(encoding="utf-8"))
    workstream.update(fields)
    workstream_path.write_text(json.dumps(workstream, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _plan() -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": "dashboard observer objective",
        "workstreams": [
            {
                "id": "01-dashboard",
                "title": "Dashboard observer",
                "mode": "serial",
                "scope": "Serve read-only dashboard state.",
                "files": ["scripts/dispatch_engine/dashboard.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest tests.test_dashboard_observer"],
            },
            {
                "id": "02-agent-detail",
                "title": "Agent detail",
                "mode": "serial",
                "scope": "Show read-only agent detail state.",
                "files": ["dashboard/app.js"],
                "depends_on": ["01-dashboard"],
                "parallel_group": None,
                "validation": [],
            },
            {
                "id": "03-plan-explorer",
                "title": "Plan explorer",
                "mode": "serial",
                "scope": "Show searchable plan tree and coordinator logs.",
                "files": ["dashboard/app.js", "dashboard/styles.css"],
                "depends_on": ["02-agent-detail"],
                "parallel_group": None,
                "validation": ["git diff --check"],
            }
        ],
        "decisions": [],
    }


if __name__ == "__main__":
    unittest.main()
