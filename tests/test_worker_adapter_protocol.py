from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.agents import (
    AgentValidationError,
    complete_worker,
    detect_protocol_violations,
    fail_worker,
    read_agent,
    record_protocol_violations,
    register_agent,
    register_worker_agent,
    validate_worker_report,
    write_worker_report,
)
from dispatch_engine.events import read_events
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.prompts import render_worker_prompt, write_worker_prompt_snapshot
from dispatch_engine.state import run_status


class WorkerAdapterProtocolTests(unittest.TestCase):
    def test_register_worker_records_scope_paths_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)

            agent = register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=["tests/"],
                status="running",
            )

            self.assertEqual(agent["role"], "worker")
            self.assertEqual(agent["status"], "running")
            self.assertEqual(agent["workstream"], "01-worker-protocol")
            self.assertEqual(agent["assigned_files"], ["scripts/dispatch_engine/agents.py"])
            self.assertEqual(agent["allowed_write_roots"], ["tests/"])
            self.assertEqual(
                agent["prompt_path"],
                f".dispatch/runs/{state_dir.name}/prompts/worker-001.md",
            )
            self.assertEqual(
                agent["stdout_path"],
                f".dispatch/runs/{state_dir.name}/logs/worker-001.stdout.log",
            )
            self.assertEqual(
                agent["stderr_path"],
                f".dispatch/runs/{state_dir.name}/logs/worker-001.stderr.log",
            )
            self.assertEqual(read_agent(state_dir, "worker-001"), agent)
            self.assertEqual(
                [event["type"] for event in read_events(state_dir / "events.jsonl")[-2:]],
                ["agent.spawned", "workstream.assigned"],
            )

    def test_complete_worker_writes_report_and_satisfies_completed_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=["tests/"],
                status="running",
            )

            completed = complete_worker(
                state_dir,
                "worker-001",
                report=_worker_report(
                    changed_files=[
                        "scripts/dispatch_engine/agents.py",
                        "tests/test_worker_adapter_protocol.py",
                    ]
                ),
            )
            _mark_workstream_completed(state_dir)

            self.assertEqual(completed["status"], "completed")
            self.assertEqual(validate_worker_report(state_dir, "worker-001"), [])
            self.assertEqual(detect_protocol_violations(state_dir), [])
            report = json.loads((state_dir / "reports" / "worker-001.json").read_text())
            self.assertEqual(report["agent_id"], "worker-001")
            self.assertEqual(report["workstream"], "01-worker-protocol")

    def test_completed_with_concerns_worker_satisfies_completed_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=[],
                status="running",
            )
            complete_worker(
                state_dir,
                "worker-001",
                report=_worker_report(
                    changed_files=["scripts/dispatch_engine/agents.py"],
                    status="completed_with_concerns",
                ),
            )
            agent = read_agent(state_dir, "worker-001")
            assert agent is not None
            agent["status"] = "completed_with_concerns"
            (state_dir / "agents" / "worker-001.json").write_text(
                json.dumps(agent, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _mark_workstream_completed(state_dir)

            self.assertEqual(validate_worker_report(state_dir, "worker-001"), [])
            self.assertEqual(detect_protocol_violations(state_dir), [])
            self.assertEqual(run_status(repo)["workstream_assignments"], [])

    def test_worker_report_legacy_aliases_produce_precise_repair_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=[],
                status="running",
            )
            (state_dir / "reports" / "worker-001.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "agent_id": "worker-001",
                        "role": "worker",
                        "workstream": "01-worker-protocol",
                        "status": "completed",
                        "summary": "Legacy-ish shape from an older prompt.",
                        "files_changed": ["scripts/dispatch_engine/agents.py"],
                        "validation_run": [],
                        "open_questions": [],
                        "conflicts_or_blockers": [],
                        "residual_risk": [],
                        "capability_profile": "worker-standard",
                        "capabilities_used": ["test_execution"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            violations = validate_worker_report(state_dir, "worker-001")

            self.assertEqual([item["violation"] for item in violations], ["malformed_worker_report"])
            details = violations[0]["details"]
            self.assertEqual(
                details["legacy_aliases"],
                {
                    "files_changed": "changed_files",
                    "validation_run": "validation",
                    "conflicts_or_blockers": "blockers",
                    "residual_risk": "risks",
                    "open_questions": "questions",
                    "capability_profile": "capability_profile_id",
                    "capabilities_used": "capabilities_exercised",
                },
            )
            self.assertIn("changed_files", details["missing_fields"])
            self.assertIn("validation", details["missing_fields"])

    def test_missing_worker_report_is_a_protocol_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=[],
                status="running",
            )
            read_agent_before = read_agent(state_dir, "worker-001")
            assert read_agent_before is not None
            read_agent_before["status"] = "completed"
            (state_dir / "agents" / "worker-001.json").write_text(
                json.dumps(read_agent_before, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            _mark_workstream_completed(state_dir)

            violations = detect_protocol_violations(state_dir)

            self.assertIn("missing_worker_report", [item["violation"] for item in violations])
            self.assertIn("unregistered_implementation_completion", [item["violation"] for item in violations])

    def test_malformed_and_out_of_scope_worker_reports_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="claude",
                profile="claude-p",
                workstream="01-worker-protocol",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=["tests/"],
                status="running",
            )
            write_worker_report(
                state_dir,
                "worker-001",
                {
                    "status": "completed",
                    "summary": "changed too much",
                    "changed_files": ["README.md"],
                    "validation": [],
                    "questions": [],
                    "blockers": [],
                    "risks": [],
                },
            )
            complete_worker(state_dir, "worker-001", report=json.loads((state_dir / "reports" / "worker-001.json").read_text()))

            violations = validate_worker_report(state_dir, "worker-001")

            self.assertEqual([item["violation"] for item in violations], ["out_of_scope_changed_file"])
            self.assertEqual(violations[0]["details"]["changed_files"], ["README.md"])

    def test_allowed_write_root_does_not_match_sibling_prefixes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=[],
                allowed_write_roots=["src"],
                status="running",
            )
            complete_worker(
                state_dir,
                "worker-001",
                report=_worker_report(changed_files=["src/example.py", "srcology/readme.md"]),
            )

            violations = validate_worker_report(state_dir, "worker-001")

            self.assertEqual([item["violation"] for item in violations], ["out_of_scope_changed_file"])
            self.assertEqual(violations[0]["details"]["changed_files"], ["srcology/readme.md"])

    def test_worker_runtime_evidence_paths_are_allowed_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            agent = register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=[],
                allowed_write_roots=[],
                status="running",
            )
            complete_worker(
                state_dir,
                "worker-001",
                report=_worker_report(
                    changed_files=[
                        agent["report_path"],
                        agent["log_path"],
                        agent["stdout_path"],
                        agent["stderr_path"],
                        f".dispatch/runs/{state_dir.name}/heartbeats/worker-001.jsonl",
                    ],
                ),
            )

            self.assertEqual(validate_worker_report(state_dir, "worker-001"), [])

    def test_assigned_directory_allows_nested_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=["packages/protocol/"],
                allowed_write_roots=[],
                status="running",
            )
            complete_worker(
                state_dir,
                "worker-001",
                report=_worker_report(changed_files=["packages/protocol/src/index.ts"]),
            )

            self.assertEqual(validate_worker_report(state_dir, "worker-001"), [])

    def test_capabilities_exercised_string_shorthand_uses_granted_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=[],
                status="running",
            )
            complete_worker(
                state_dir,
                "worker-001",
                report=_worker_report(
                    changed_files=["scripts/dispatch_engine/agents.py"],
                    capabilities_exercised=["test_execution"],
                ),
            )

            self.assertEqual(validate_worker_report(state_dir, "worker-001"), [])

    def test_worker_report_helper_rejects_non_worker_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_agent(
                state_dir,
                agent_id="reviewer-001",
                role="reviewer",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-worker-protocol",
            )

            with self.assertRaisesRegex(AgentValidationError, "not a worker"):
                write_worker_report(state_dir, "reviewer-001", _worker_report(changed_files=[]))

            self.assertFalse((state_dir / "reviews" / "reviewer-001.json").exists())

    def test_status_json_exposes_worker_assignment_and_violation_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=[],
                status="running",
            )
            fail_worker(state_dir, "worker-001", reason="fixture failure")

            status = run_status(repo)

            self.assertEqual(status["agent_counts"]["by_role"]["worker"], 1)
            self.assertEqual(status["agent_counts"]["by_status"]["failed"], 1)
            self.assertEqual(status["protocol_violations"]["count"], 0)

    def test_render_worker_prompt_includes_protocol_scope_and_report_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            agent = register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=["tests/"],
                status="running",
            )
            run = json.loads((state_dir / "run.json").read_text(encoding="utf-8"))
            workstream = json.loads((state_dir / "workstreams" / "01-worker-protocol.json").read_text(encoding="utf-8"))

            prompt = render_worker_prompt(
                run,
                repo_root=repo,
                run_state_dir=state_dir,
                agent=agent,
                workstream=workstream,
            )

            expected_fragments = [
                str(repo),
                state_dir.name,
                str(state_dir),
                "01-worker-protocol",
                "Worker protocol",
                "Add worker adapter protocol.",
                "scripts/dispatch_engine/agents.py",
                "tests/",
                "PYTHONPATH=scripts python3 -m unittest discover -s tests",
                f".dispatch/runs/{state_dir.name}/reports/worker-001.json",
                "not alone in the codebase",
                "assigned files",
                "allowed write roots",
                '"changed_files"',
                '"validation"',
                '"capability_profile_id"',
                '"capabilities_exercised"',
                '"capability_escalations"',
                "Legacy aliases",
            ]
            for fragment in expected_fragments:
                self.assertIn(fragment, prompt)

            prompt_path = write_worker_prompt_snapshot(state_dir, agent, prompt)

            self.assertEqual(prompt_path, state_dir / "prompts" / "worker-001.md")
            self.assertEqual(prompt_path.read_text(encoding="utf-8"), prompt)

    def test_record_protocol_violations_emits_events_for_worker_report_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-worker-protocol",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=[],
                status="running",
            )
            read_agent_before = read_agent(state_dir, "worker-001")
            assert read_agent_before is not None
            read_agent_before["status"] = "completed"
            (state_dir / "agents" / "worker-001.json").write_text(
                json.dumps(read_agent_before, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            violations = record_protocol_violations(state_dir)

            self.assertIn("missing_worker_report", [item["violation"] for item in violations])
            violation_events = [
                event
                for event in read_events(state_dir / "events.jsonl")
                if event["type"] == "protocol.violation"
            ]
            self.assertIn(
                "missing_worker_report",
                [event["payload"]["violation"] for event in violation_events],
            )


def _import_plan(repo: Path) -> Path:
    plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(json.dumps(_plan()) + "\n", encoding="utf-8")
    return Path(import_dispatch_plan(repo, plan_path)["state_dir"])


def _plan() -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": "worker protocol objective",
        "workstreams": [
            {
                "id": "01-worker-protocol",
                "title": "Worker protocol",
                "mode": "serial",
                "scope": "Add worker adapter protocol.",
                "files": ["scripts/dispatch_engine/agents.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
            }
        ],
        "decisions": [],
    }


def _worker_report(
    changed_files: list[str],
    *,
    status: str = "completed",
    capabilities_exercised: list[str | dict] | None = None,
) -> dict:
    return {
        "status": status,
        "summary": "Implemented scoped worker protocol changes.",
        "changed_files": changed_files,
        "validation": [
            {
                "command": "PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol",
                "status": "passed",
                "summary": "Focused worker protocol tests passed.",
            }
        ],
        "questions": [],
        "blockers": [],
        "risks": [],
        "capabilities_exercised": list(capabilities_exercised or []),
    }


def _mark_workstream_completed(state_dir: Path) -> None:
    path = state_dir / "workstreams" / "01-worker-protocol.json"
    workstream = json.loads(path.read_text(encoding="utf-8"))
    workstream["status"] = "completed"
    path.write_text(json.dumps(workstream, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
