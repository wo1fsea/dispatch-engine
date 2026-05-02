from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.agents import (
    append_agent_heartbeat,
    complete_agent,
    complete_worker,
    detect_protocol_violations,
    register_agent,
    register_worker_agent,
    write_reviewer_report,
    write_validator_report,
)
from dispatch_engine.coordinators import launch_run_coordinator, render_run_dry_run
from dispatch_engine.decisions import (
    list_pending_decisions,
    list_unresolved_blockers,
    record_blocker,
    record_decision_request,
    resolve_blocker,
    resolve_decision,
)
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.state import run_status, tail_events


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PLAN = REPO_ROOT / "fixtures" / "dogfood-runbook" / "plan.json"


class DogfoodRunbookFixtureTests(unittest.TestCase):
    def test_fixture_plan_runs_minimal_dogfood_evidence_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target_repo = Path(tmp) / "target-repo"
            target_repo.mkdir()

            imported = import_dispatch_plan(target_repo, FIXTURE_PLAN)
            run_id = imported["run_id"]
            state_dir = Path(imported["state_dir"])

            self.assertEqual(imported["plan_id"], "dogfood-runbook-fixture")
            self.assertEqual(imported["workstream_count"], 1)
            self.assertEqual(imported["decision_count"], 1)
            self.assertTrue(
                state_dir.is_relative_to(target_repo.resolve() / ".dispatch" / "runs")
            )
            self.assertFalse((FIXTURE_PLAN.parent / ".dispatch").exists())

            dry_run = render_run_dry_run(target_repo, run_id=run_id, provider="codex")

            self.assertEqual(dry_run["kind"], "run_dry_run")
            self.assertEqual(dry_run["state_writes"], [])
            self.assertEqual(dry_run["run_id"], run_id)
            self.assertIn("Coordinator-Only Behavior", dry_run["prompt_text"])

            with _fake_provider_path("codex"):
                live = launch_run_coordinator(target_repo, run_id=run_id, provider="codex")

            self.assertEqual(live["kind"], "run_live")
            self.assertEqual(live["state"], "completed")
            self.assertEqual(live["exit_code"], 0)
            self.assertTrue((state_dir / "prompts" / "coordinator-001.md").is_file())
            self.assertTrue((state_dir / "logs" / "coordinator-001.stdout.log").is_file())

            worker = register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-dogfood-evidence-loop",
                assigned_files=["references/dogfood-runbook.md"],
                allowed_write_roots=["fixtures/dogfood-runbook/", "tests/"],
            )
            append_agent_heartbeat(
                state_dir,
                "worker-001",
                status="running",
                payload={"step": "writing dogfood evidence"},
            )
            complete_worker(
                state_dir,
                "worker-001",
                report={
                    "schema_version": 1,
                    "agent_id": "worker-001",
                    "role": "worker",
                    "workstream": "01-dogfood-evidence-loop",
                    "status": "completed",
                    "summary": "Created deterministic dogfood runbook fixture evidence.",
                    "changed_files": [
                        "references/dogfood-runbook.md",
                        "fixtures/dogfood-runbook/plan.json",
                        "tests/test_dogfood_runbook_fixture.py",
                    ],
                    "validation": [
                        "PYTHONPATH=scripts python3 -m unittest tests.test_dogfood_runbook_fixture"
                    ],
                    "questions": [],
                    "blockers": [],
                    "risks": [],
                },
            )

            reviewer = register_agent(
                state_dir,
                agent_id="reviewer-001",
                role="reviewer",
                provider="codex",
                profile="codex-exec",
                status="running",
                workstream="01-dogfood-evidence-loop",
                assigned_files=["references/dogfood-runbook.md"],
                allowed_write_roots=[],
                prompt_path=f".dispatch/runs/{run_id}/prompts/reviewer-001.md",
            )
            append_agent_heartbeat(state_dir, "reviewer-001", status="running")
            write_reviewer_report(
                state_dir,
                "reviewer-001",
                {
                    "schema_version": 1,
                    "agent_id": "reviewer-001",
                    "role": "reviewer",
                    "workstream": "01-dogfood-evidence-loop",
                    "status": "accepted",
                    "summary": "Fixture evidence follows the review validator protocol.",
                    "findings": [],
                    "risks": [],
                    "requested_changes": [],
                    "validation_gaps": [],
                    "recommendation": "continue",
                },
            )
            complete_agent(state_dir, reviewer["agent_id"])

            validator = register_agent(
                state_dir,
                agent_id="validator-001",
                role="validator",
                provider="claude",
                profile="claude-p",
                status="running",
                workstream="01-dogfood-evidence-loop",
                allowed_write_roots=[],
                prompt_path=f".dispatch/runs/{run_id}/prompts/validator-001.md",
            )
            append_agent_heartbeat(state_dir, "validator-001", status="running")
            validation_artifact = state_dir / "validation" / "dogfood-smoke.stdout.log"
            validation_artifact.write_text("dogfood fixture smoke passed\n", encoding="utf-8")
            write_validator_report(
                state_dir,
                "validator-001",
                {
                    "schema_version": 1,
                    "agent_id": "validator-001",
                    "role": "validator",
                    "workstream": "01-dogfood-evidence-loop",
                    "status": "passed",
                    "summary": "Dogfood fixture smoke passed.",
                    "command": "PYTHONPATH=scripts python3 -m unittest tests.test_dogfood_runbook_fixture",
                    "output_summary": "dogfood fixture smoke passed",
                    "artifacts": [
                        f".dispatch/runs/{run_id}/validation/dogfood-smoke.stdout.log"
                    ],
                    "not_run_reason": "",
                },
            )
            complete_agent(state_dir, validator["agent_id"])

            decision = record_decision_request(
                state_dir,
                decision_id="decision-real-provider-or-fake",
                question="Use a real provider CLI or the deterministic fake provider shim?",
                reason="Dogfood smoke should stay deterministic.",
                workstream="01-dogfood-evidence-loop",
                actor="coordinator-001",
            )
            blocker = record_blocker(
                state_dir,
                blocker_id="blocker-real-provider-unavailable",
                summary="Real provider CLI is intentionally not required for the fixture smoke.",
                workstream="01-dogfood-evidence-loop",
                actor="validator-001",
            )

            blocked_status = run_status(target_repo, run_id=run_id)
            self.assertEqual(decision["status"], "pending")
            self.assertEqual(blocker["status"], "open")
            self.assertGreaterEqual(blocked_status["pending_decisions"], 2)
            self.assertEqual(blocked_status["unresolved_blockers"], 1)
            self.assertEqual(blocked_status["decision_blocker_validation"]["status"], "blocked")

            resolve_decision(
                state_dir,
                "decision-real-provider-or-fake",
                resolution="Use fake provider shim for deterministic fixture smoke.",
                actor="operator",
            )
            resolve_blocker(
                state_dir,
                "blocker-real-provider-unavailable",
                resolution="Fake provider shim produced live-form coordinator evidence.",
                actor="operator",
            )

            final_status = run_status(target_repo, run_id=run_id)
            final_tail = tail_events(target_repo, run_id=run_id)
            event_types = [event["type"] for event in final_tail["events"]]

            self.assertEqual(list_unresolved_blockers(state_dir), [])
            self.assertEqual(
                [item["decision_id"] for item in list_pending_decisions(state_dir)],
                ["decision-dogfood-provider"],
            )
            self.assertEqual(final_status["unresolved_blockers"], 0)
            self.assertEqual(final_status["agent_counts"]["by_role"]["coordinator"], 1)
            self.assertEqual(final_status["agent_counts"]["by_role"]["worker"], 1)
            self.assertEqual(final_status["agent_counts"]["by_role"]["reviewer"], 1)
            self.assertEqual(final_status["agent_counts"]["by_role"]["validator"], 1)
            self.assertEqual(final_status["heartbeat_summary"]["with_heartbeat"], 3)
            self.assertEqual(detect_protocol_violations(state_dir), [])
            self.assertIn("coordinator.started", event_types)
            self.assertIn("coordinator.completed", event_types)
            self.assertIn("agent.spawned", event_types)
            self.assertIn("agent.completed", event_types)
            self.assertIn("decision.requested", event_types)
            self.assertIn("decision.resolved", event_types)
            self.assertIn("blocker.recorded", event_types)
            self.assertIn("blocker.resolved", event_types)


class _fake_provider_path:
    def __init__(self, executable_name: str) -> None:
        self.executable_name = executable_name
        self._tmp: tempfile.TemporaryDirectory[str] | None = None
        self._old_path: str | None = None

    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        bin_dir = Path(self._tmp.name)
        executable = bin_dir / self.executable_name
        executable.write_text(
            "#!/bin/sh\nprintf 'fake provider executed\\n'\nexit 0\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
        self._old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{self._old_path}"
        return executable

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._old_path is not None:
            os.environ["PATH"] = self._old_path
        if self._tmp is not None:
            self._tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
