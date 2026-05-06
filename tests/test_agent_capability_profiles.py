from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.agents import (
    AgentValidationError,
    complete_worker,
    register_agent,
    register_worker_agent,
    validate_worker_report,
)
from dispatch_engine.events import read_events
from dispatch_engine.plan_schema import PlanValidationError, import_dispatch_plan
from dispatch_engine.prompts import render_reviewer_prompt, render_validator_prompt, render_worker_prompt
from dispatch_engine.state import run_status


class AgentCapabilityProfilesTests(unittest.TestCase):
    def test_import_normalizes_omitted_workstream_profile_to_worker_standard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo, _plan())

            workstream = json.loads((state_dir / "workstreams" / "01-capabilities.json").read_text())
            profile = workstream["capability_profile"]

            self.assertEqual(profile["schema_version"], 1)
            self.assertEqual(profile["profile_id"], "worker-standard")
            self.assertEqual(
                profile["repo_write_scope"],
                {
                    "assigned_files": ["scripts/dispatch_engine/agents.py"],
                    "allowed_write_roots": ["tests/"],
                },
            )
            self.assertEqual(profile["capabilities"]["network_access"]["mode"], "none")
            self.assertEqual(profile["capabilities"]["package_install"]["mode"], "deny")
            self.assertEqual(profile["capabilities"]["test_execution"]["mode"], "allow-listed")
            self.assertEqual(
                profile["capabilities"]["test_execution"]["commands"],
                ["PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles"],
            )

    def test_import_rejects_unknown_capability_and_invalid_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _plan()
            plan["workstreams"][0]["capability_profile"] = {
                "profile_id": "worker-standard",
                "repo_write_scope": {"assigned_files": [], "allowed_write_roots": []},
                "capabilities": {"telepathy": {"mode": "unrestricted"}},
            }

            with self.assertRaisesRegex(PlanValidationError, "unknown capability"):
                _import_plan(repo, plan)

        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _plan()
            plan["workstreams"][0]["capability_profile"] = {
                "profile_id": "worker-standard",
                "repo_write_scope": {"assigned_files": [], "allowed_write_roots": []},
                "capabilities": {"network_access": {"mode": "maybe"}},
            }

            with self.assertRaisesRegex(PlanValidationError, "invalid mode"):
                _import_plan(repo, plan)

    def test_string_preset_keeps_workstream_write_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _plan()
            plan["workstreams"][0]["capability_profile"] = "worker-dependency"

            state_dir = _import_plan(repo, plan)
            workstream = json.loads((state_dir / "workstreams" / "01-capabilities.json").read_text())
            profile = workstream["capability_profile"]

            self.assertEqual(profile["profile_id"], "worker-dependency")
            self.assertEqual(
                profile["repo_write_scope"],
                {
                    "assigned_files": ["scripts/dispatch_engine/agents.py"],
                    "allowed_write_roots": ["tests/"],
                },
            )
            self.assertEqual(profile["capabilities"]["package_install"]["mode"], "allow-project-manager")

    def test_import_records_validation_capability_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _plan()
            plan["workstreams"][0]["validation"] = [
                "npm run dev",
                "curl http://127.0.0.1:3000/health",
            ]

            state_dir = _import_plan(repo, plan)
            workstream = json.loads((state_dir / "workstreams" / "01-capabilities.json").read_text())

            self.assertEqual(
                workstream.get("validation_warnings"),
                [
                    {
                        "code": "validation_command_requires_service_start",
                        "capability": "service_start",
                        "granted_mode": "deny",
                        "command": "npm run dev",
                        "message": "Validation command appears to start a service but capability_profile.service_start is deny.",
                    },
                    {
                        "code": "validation_command_requires_network_access",
                        "capability": "network_access",
                        "granted_mode": "none",
                        "command": "curl http://127.0.0.1:3000/health",
                        "message": "Validation command appears to access a network endpoint but capability_profile.network_access is none.",
                    },
                ],
            )

    def test_import_warns_when_github_issue_evidence_needs_denied_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _plan()
            plan["workstreams"][0]["title"] = "GitHub issue evidence review"
            plan["workstreams"][0]["scope"] = (
                "Inspect GitHub issues #20-#24 before closing the dogfood report."
            )
            plan["workstreams"][0]["validation"] = [
                "Record local validation without gh issue view."
            ]

            state_dir = _import_plan(repo, plan)
            workstream = json.loads((state_dir / "workstreams" / "01-capabilities.json").read_text())

            self.assertEqual(
                workstream.get("validation_warnings"),
                [
                    {
                        "code": "issue_evidence_requires_network_access",
                        "capability": "network_access",
                        "granted_mode": "none",
                        "source": "title/scope/validation",
                        "message": (
                            "Workstream appears to require GitHub issue evidence but "
                            "capability_profile.network_access is none. Grant explicit "
                            "read-only network access, record a local-only evidence "
                            "strategy, or block before dispatch."
                        ),
                    }
                ],
            )

    def test_import_does_not_warn_for_issue_evidence_with_read_network_grant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _plan()
            plan["workstreams"][0]["title"] = "GitHub issue evidence review"
            plan["workstreams"][0]["scope"] = (
                "Inspect GitHub issues #20-#24 before closing the dogfood report."
            )
            plan["workstreams"][0]["capability_profile"] = {
                "schema_version": 1,
                "profile_id": "worker-standard",
                "repo_write_scope": {
                    "assigned_files": ["scripts/dispatch_engine/agents.py"],
                    "allowed_write_roots": ["tests/"],
                },
                "capabilities": {
                    "network_access": {"mode": "read-only-public", "allowlist": []}
                },
            }

            state_dir = _import_plan(repo, plan)
            workstream = json.loads((state_dir / "workstreams" / "01-capabilities.json").read_text())

            self.assertNotIn("validation_warnings", workstream)

    def test_registration_grants_profiles_for_worker_reviewer_and_validator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo, _plan())
            worker = register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-capabilities",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=["tests/"],
            )
            reviewer = register_agent(
                state_dir,
                agent_id="reviewer-001",
                role="reviewer",
                provider="codex",
                profile="codex-exec",
                workstream="01-capabilities",
            )
            validator = register_agent(
                state_dir,
                agent_id="validator-001",
                role="validator",
                provider="codex",
                profile="codex-exec",
                workstream="01-capabilities",
            )

            self.assertEqual(worker["capability_profile"]["profile_id"], "worker-standard")
            self.assertEqual(worker["capability_profile_source"], "workstream")
            self.assertEqual(worker["capability_profile_decision_ids"], [])
            self.assertEqual(reviewer["capability_profile"]["profile_id"], "reviewer-standard")
            self.assertEqual(validator["capability_profile"]["profile_id"], "validator-standard")
            grant_events = [
                event
                for event in read_events(state_dir / "events.jsonl")
                if event["type"] == "capability.profile.granted"
            ]
            self.assertEqual([event["payload"]["agent_id"] for event in grant_events], ["worker-001"])

    def test_register_agent_rejects_invalid_capability_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo, _plan())

            with self.assertRaisesRegex(AgentValidationError, "repo_write_scope"):
                register_agent(
                    state_dir,
                    agent_id="worker-001",
                    role="worker",
                    provider="codex",
                    profile="codex-exec",
                    workstream="01-capabilities",
                    capability_profile={"profile_id": "worker-standard"},
                )

    def test_prompts_render_capability_profile_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo, _plan())
            run = json.loads((state_dir / "run.json").read_text())
            workstream = json.loads((state_dir / "workstreams" / "01-capabilities.json").read_text())
            worker = register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-capabilities",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=["tests/"],
            )
            reviewer = register_agent(
                state_dir,
                agent_id="reviewer-001",
                role="reviewer",
                provider="codex",
                profile="codex-exec",
                workstream="01-capabilities",
            )
            validator = register_agent(
                state_dir,
                agent_id="validator-001",
                role="validator",
                provider="codex",
                profile="codex-exec",
                workstream="01-capabilities",
            )

            worker_prompt = render_worker_prompt(run, repo_root=repo, run_state_dir=state_dir, agent=worker, workstream=workstream)
            reviewer_prompt = render_reviewer_prompt(run, repo_root=repo, run_state_dir=state_dir, agent=reviewer, workstream=workstream)
            validator_prompt = render_validator_prompt(run, repo_root=repo, run_state_dir=state_dir, agent=validator, workstream=workstream)

            for prompt in (worker_prompt, reviewer_prompt, validator_prompt):
                self.assertIn("## Capability Profile", prompt)
                self.assertIn("capability_profile", prompt)
                self.assertIn("network_access", prompt)
                self.assertIn("package_install", prompt)
                self.assertIn("Stop before using a denied capability", prompt)

    def test_report_overreach_without_decision_is_protocol_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo, _plan())
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-capabilities",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=["tests/"],
            )
            complete_worker(
                state_dir,
                "worker-001",
                report={
                    **_worker_report(["scripts/dispatch_engine/agents.py"]),
                    "capabilities_exercised": [
                        {
                            "capability": "network_access",
                            "mode": "read-only-public",
                            "evidence": "Read upstream docs.",
                        }
                    ],
                },
            )

            violations = validate_worker_report(state_dir, "worker-001")

            self.assertEqual([item["violation"] for item in violations], ["capability_overreach"])
            self.assertEqual(violations[0]["agent_id"], "worker-001")
            self.assertEqual(violations[0]["details"]["capability"], "network_access")
            self.assertEqual(violations[0]["details"]["requested_mode"], "read-only-public")
            self.assertEqual(violations[0]["details"]["granted_mode"], "none")

    def test_report_overreach_with_decision_id_is_allowed_and_status_summarizes_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo, _plan())
            register_worker_agent(
                state_dir,
                agent_id="worker-001",
                provider="codex",
                profile="codex-exec",
                workstream="01-capabilities",
                assigned_files=["scripts/dispatch_engine/agents.py"],
                allowed_write_roots=["tests/"],
                status="running",
            )
            complete_worker(
                state_dir,
                "worker-001",
                report={
                    **_worker_report(["scripts/dispatch_engine/agents.py"]),
                    "capabilities_exercised": [
                        {
                            "capability": "network_access",
                            "mode": "read-only-public",
                            "decision_id": "decision-002",
                            "evidence": "Approved public docs lookup.",
                        }
                    ],
                    "capability_escalations": [
                        {
                            "capability": "package_install",
                            "requested_mode": "allow-project-manager",
                            "status": "blocked",
                            "decision_id": "decision-003",
                            "reason": "Need npm install.",
                        }
                    ],
                },
            )
            _append_decision(
                state_dir,
                {
                    "id": "decision-003",
                    "status": "pending",
                    "question": "Allow package manager install?",
                    "capability": "package_install",
                    "requested_mode": "allow-project-manager",
                    "workstream": "01-capabilities",
                },
            )

            status = run_status(repo)

            self.assertEqual(status["protocol_violations"]["count"], 0)
            summary = status["capability_profiles"]
            self.assertEqual(summary["agents"][0]["agent_id"], "worker-001")
            self.assertEqual(summary["agents"][0]["profile_id"], "worker-standard")
            self.assertEqual(
                summary["pending_decisions"],
                [
                    {
                        "decision_id": "decision-003",
                        "capability": "package_install",
                        "requested_mode": "allow-project-manager",
                        "workstream": "01-capabilities",
                    }
                ],
            )
            self.assertEqual(summary["violations"], [])


def _import_plan(repo: Path, plan: dict) -> Path:
    plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan) + "\n", encoding="utf-8")
    return Path(import_dispatch_plan(repo, plan_path)["state_dir"])


def _append_decision(state_dir: Path, record: dict) -> None:
    with (state_dir / "decisions.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _plan() -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": "capability profile objective",
        "workstreams": [
            {
                "id": "01-capabilities",
                "title": "Capability profiles",
                "mode": "serial",
                "scope": "Add capability profile support.",
                "files": ["scripts/dispatch_engine/agents.py"],
                "allowed_write_roots": ["tests/"],
                "depends_on": [],
                "parallel_group": None,
                "validation": [
                    "PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles"
                ],
            }
        ],
        "decisions": [],
    }


def _worker_report(changed_files: list[str]) -> dict:
    return {
        "status": "completed",
        "summary": "Implemented capability profile support.",
        "changed_files": changed_files,
        "validation": [
            {
                "command": "PYTHONPATH=scripts python3 -m unittest tests.test_agent_capability_profiles",
                "status": "passed",
                "summary": "Focused capability profile tests passed.",
            }
        ],
        "questions": [],
        "blockers": [],
        "risks": [],
    }


if __name__ == "__main__":
    unittest.main()
