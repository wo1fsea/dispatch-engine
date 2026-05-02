from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.agents import (
    AgentValidationError,
    append_agent_heartbeat,
    complete_agent,
    detect_protocol_violations,
    fail_agent,
    list_agents,
    read_agent,
    record_protocol_violations,
    register_agent,
)
from dispatch_engine.events import (
    agent_failed,
    agent_spawned,
    coordinator_started,
    decision_requested,
    read_events,
    workstream_assigned,
)
from dispatch_engine.plan_schema import import_dispatch_plan


class AgentStateProtocolTests(unittest.TestCase):
    def test_registers_coordinator_with_dispatch_only_write_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = _import_plan(Path(tmp))

            agent = register_agent(
                state_dir,
                agent_id="coordinator-001",
                role="coordinator",
                provider="codex",
                profile="codex-exec",
                status="running",
            )

            self.assertEqual(agent["schema_version"], 1)
            self.assertEqual(agent["agent_id"], "coordinator-001")
            self.assertEqual(agent["role"], "coordinator")
            self.assertEqual(agent["provider"], "codex")
            self.assertEqual(agent["profile"], "codex-exec")
            self.assertEqual(agent["run_id"], state_dir.name)
            self.assertEqual(agent["status"], "running")
            self.assertEqual(agent["assigned_files"], [])
            self.assertEqual(agent["allowed_write_roots"], [".dispatch/"])
            self.assertIsNone(agent["workstream"])
            self.assertIsNone(agent["completed_at"])
            self.assertEqual(
                agent["report_path"],
                f".dispatch/runs/{state_dir.name}/reports/coordinator-001.json",
            )
            self.assertEqual(
                agent["log_path"],
                f".dispatch/runs/{state_dir.name}/logs/coordinator-001.jsonl",
            )
            self.assertTrue((state_dir / "agents" / "coordinator-001.json").is_file())
            self.assertEqual(read_agent(state_dir, "coordinator-001"), agent)
            self.assertEqual([item["agent_id"] for item in list_agents(state_dir)], ["coordinator-001"])

    def test_register_agent_validates_roles_and_providers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = _import_plan(Path(tmp))

            with self.assertRaisesRegex(AgentValidationError, "unsupported role"):
                register_agent(
                    state_dir,
                    agent_id="planner-001",
                    role="planner",
                    provider="codex",
                    profile="codex-exec",
                )

            with self.assertRaisesRegex(AgentValidationError, "unsupported provider"):
                register_agent(
                    state_dir,
                    agent_id="coordinator-001",
                    role="coordinator",
                    provider="other",
                    profile="other",
                )

    def test_updates_heartbeat_completion_and_failure_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = _import_plan(Path(tmp))
            register_agent(
                state_dir,
                agent_id="worker-001",
                role="worker",
                provider="claude",
                profile="claude-p",
                workstream="01-agent-state",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=["scripts/dispatch_engine/"],
                status="running",
            )

            heartbeat = append_agent_heartbeat(
                state_dir,
                "worker-001",
                payload={"message": "still working"},
            )
            completed = complete_agent(
                state_dir,
                "worker-001",
                report={"status": "completed", "changed_files": ["scripts/dispatch_engine/agents.py"]},
            )
            failed = fail_agent(state_dir, "worker-001", reason="post-completion fixture")

            self.assertEqual(heartbeat["agent_id"], "worker-001")
            self.assertEqual(heartbeat["payload"], {"message": "still working"})
            self.assertEqual(completed["status"], "completed")
            self.assertEqual(json.loads((state_dir / "reports" / "worker-001.json").read_text())["status"], "completed")
            self.assertEqual(failed["status"], "failed")
            self.assertEqual(failed["failure_reason"], "post-completion fixture")
            heartbeat_lines = (state_dir / "heartbeats" / "worker-001.jsonl").read_text().splitlines()
            self.assertEqual(len(heartbeat_lines), 1)
            self.assertEqual(json.loads(heartbeat_lines[0])["agent_id"], "worker-001")

    def test_event_helpers_write_state_protocol_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = _import_plan(Path(tmp))
            event_log = state_dir / "events.jsonl"

            coordinator_started(event_log, agent_id="coordinator-001", provider="codex", profile="codex-exec")
            agent_spawned(
                event_log,
                agent_id="worker-001",
                role="worker",
                provider="claude",
                profile="claude-p",
                workstream="01-agent-state",
            )
            workstream_assigned(event_log, agent_id="worker-001", workstream="01-agent-state")
            agent_failed(event_log, agent_id="worker-001", reason="timeout", workstream="01-agent-state")
            decision_requested(event_log, decision_id="decision-001", question="Proceed?")

            events = read_events(event_log)[3:]
            self.assertEqual(
                [event["type"] for event in events],
                [
                    "coordinator.started",
                    "agent.spawned",
                    "workstream.assigned",
                    "agent.failed",
                    "decision.requested",
                ],
            )
            self.assertEqual(events[0]["payload"]["provider"], "codex")
            self.assertEqual(events[1]["workstream"], "01-agent-state")
            self.assertEqual(events[4]["payload"]["decision_id"], "decision-001")

    def test_protocol_violations_detect_coordinator_scope_and_unregistered_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = _import_plan(Path(tmp))
            register_agent(
                state_dir,
                agent_id="coordinator-001",
                role="coordinator",
                provider="codex",
                profile="codex-exec",
                assigned_files=["scripts/dispatch_engine/runs.py"],
                allowed_write_roots=[".dispatch/", "scripts/"],
            )
            workstream_path = state_dir / "workstreams" / "01-agent-state.json"
            workstream = json.loads(workstream_path.read_text())
            workstream["status"] = "completed"
            workstream_path.write_text(json.dumps(workstream, indent=2, sort_keys=True) + "\n")

            violations = detect_protocol_violations(state_dir)
            recorded = record_protocol_violations(state_dir)

            self.assertEqual(
                [item["violation"] for item in violations],
                ["coordinator_project_file_scope", "unregistered_implementation_completion"],
            )
            self.assertEqual([item["violation"] for item in recorded], [item["violation"] for item in violations])
            self.assertEqual(
                [event["type"] for event in read_events(state_dir / "events.jsonl")[-2:]],
                ["protocol.violation", "protocol.violation"],
            )

    def test_accepted_workstream_without_registered_evidence_is_a_protocol_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = _import_plan(Path(tmp))
            workstream_path = state_dir / "workstreams" / "01-agent-state.json"
            workstream = json.loads(workstream_path.read_text())
            workstream["status"] = "accepted"
            workstream_path.write_text(json.dumps(workstream, indent=2, sort_keys=True) + "\n")

            violations = detect_protocol_violations(state_dir)

            self.assertEqual(
                [item["violation"] for item in violations],
                ["unregistered_implementation_completion"],
            )
            self.assertEqual(violations[0]["details"], {"status": "accepted"})

    def test_legacy_runs_without_agent_directories_are_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp) / ".dispatch" / "runs" / "legacy-run"
            state_dir.mkdir(parents=True)
            (state_dir / "events.jsonl").write_text("")

            self.assertEqual(list_agents(state_dir), [])
            self.assertIsNone(read_agent(state_dir, "missing"))
            self.assertEqual(detect_protocol_violations(state_dir), [])


def _import_plan(repo: Path) -> Path:
    plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(json.dumps(_plan()) + "\n")
    return Path(import_dispatch_plan(repo, plan_path)["state_dir"])


def _plan() -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": "state protocol objective",
        "workstreams": [
            {
                "id": "01-agent-state",
                "title": "Agent state protocol",
                "mode": "serial",
                "scope": "Add durable agent state.",
                "files": ["scripts/dispatch_engine/agents.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
            }
        ],
        "decisions": [],
    }


if __name__ == "__main__":
    unittest.main()
