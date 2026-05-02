from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.agents import (
    detect_protocol_violations,
    register_agent,
    validate_review_validator_report,
    write_reviewer_report,
    write_validator_report,
)
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.prompts import (
    render_reviewer_prompt,
    render_validator_prompt,
    write_agent_prompt_snapshot,
)


class ReviewValidatorProtocolTests(unittest.TestCase):
    def test_valid_reviewer_and_validator_reports_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            reviewer = _register_reviewer(state_dir)
            validator = _register_validator(state_dir)

            reviewer_report = write_reviewer_report(
                state_dir,
                "reviewer-001",
                _reviewer_report(status="accepted"),
            )
            validator_report = write_validator_report(
                state_dir,
                "validator-001",
                _validator_report(status="passed"),
            )

            self.assertEqual(reviewer_report["role"], "reviewer")
            self.assertEqual(validator_report["role"], "validator")
            self.assertTrue((state_dir / "reviews" / "reviewer-001.json").is_file())
            self.assertTrue((state_dir / "validation" / "validator-001.json").is_file())
            self.assertEqual(validate_review_validator_report(state_dir, "reviewer-001"), [])
            self.assertEqual(validate_review_validator_report(state_dir, "validator-001"), [])
            self.assertEqual(detect_protocol_violations(state_dir), [])
            self.assertEqual(
                reviewer["report_path"],
                f".dispatch/runs/{state_dir.name}/reviews/reviewer-001.json",
            )
            self.assertEqual(
                validator["report_path"],
                f".dispatch/runs/{state_dir.name}/validation/validator-001.json",
            )

    def test_reviewer_report_rejects_illegal_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_reviewer(state_dir)
            write_reviewer_report(state_dir, "reviewer-001", _reviewer_report(status="completed"))

            violations = validate_review_validator_report(state_dir, "reviewer-001")

            self.assertEqual([item["violation"] for item in violations], ["malformed_reviewer_report"])
            self.assertEqual(violations[0]["details"]["status"], "completed")

    def test_validator_report_requires_evidence_for_non_skipped_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(state_dir)
            report = _validator_report(status="passed")
            report["artifacts"] = []
            report["output_summary"] = ""
            write_validator_report(state_dir, "validator-001", report)

            violations = validate_review_validator_report(state_dir, "validator-001")

            self.assertEqual([item["violation"] for item in violations], ["missing_validation_evidence"])
            self.assertEqual(violations[0]["details"]["missing_fields"], ["artifacts", "output_summary"])

    def test_completed_reviewer_without_report_is_status_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            agent = _register_reviewer(state_dir)
            agent["status"] = "completed"
            (state_dir / "agents" / "reviewer-001.json").write_text(
                json.dumps(agent, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            violations = detect_protocol_violations(state_dir)

            self.assertEqual([item["violation"] for item in violations], ["missing_reviewer_report"])

    def test_reviewer_and_validator_prompts_render_and_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            reviewer = _register_reviewer(state_dir)
            validator = _register_validator(state_dir)
            run = json.loads((state_dir / "run.json").read_text(encoding="utf-8"))
            workstream = json.loads((state_dir / "workstreams" / "01-review-validation.json").read_text(encoding="utf-8"))
            worker_report = {"agent_id": "worker-001", "status": "completed", "summary": "worker done"}

            reviewer_prompt = render_reviewer_prompt(
                run,
                repo_root=repo,
                run_state_dir=state_dir,
                agent=reviewer,
                workstream=workstream,
                worker_report=worker_report,
            )
            validator_prompt = render_validator_prompt(
                run,
                repo_root=repo,
                run_state_dir=state_dir,
                agent=validator,
                workstream=workstream,
                review_report={"agent_id": "reviewer-001", "status": "accepted"},
            )

            self.assertIn("Required Reviewer Report", reviewer_prompt)
            self.assertIn('"recommendation"', reviewer_prompt)
            self.assertIn(f".dispatch/runs/{state_dir.name}/reviews/reviewer-001.json", reviewer_prompt)
            self.assertIn("Required Validator Report", validator_prompt)
            self.assertIn('"artifacts"', validator_prompt)
            self.assertIn(f".dispatch/runs/{state_dir.name}/validation/validator-001.json", validator_prompt)
            self.assertEqual(write_agent_prompt_snapshot(state_dir, reviewer, reviewer_prompt).read_text(), reviewer_prompt)
            self.assertEqual(write_agent_prompt_snapshot(state_dir, validator, validator_prompt).read_text(), validator_prompt)


def _register_reviewer(state_dir: Path) -> dict:
    return register_agent(
        state_dir,
        agent_id="reviewer-001",
        role="reviewer",
        provider="codex",
        profile="codex-exec",
        status="completed",
        workstream="01-review-validation",
        assigned_files=["scripts/dispatch_engine/agents.py"],
        allowed_write_roots=["tests/"],
        prompt_path=f".dispatch/runs/{state_dir.name}/prompts/reviewer-001.md",
    )


def _register_validator(state_dir: Path) -> dict:
    return register_agent(
        state_dir,
        agent_id="validator-001",
        role="validator",
        provider="claude",
        profile="claude-p",
        status="completed",
        workstream="01-review-validation",
        allowed_write_roots=[],
        prompt_path=f".dispatch/runs/{state_dir.name}/prompts/validator-001.md",
    )


def _reviewer_report(*, status: str) -> dict:
    return {
        "schema_version": 1,
        "agent_id": "reviewer-001",
        "role": "reviewer",
        "workstream": "01-review-validation",
        "status": status,
        "summary": "reviewed implementation evidence",
        "findings": [],
        "risks": [],
        "requested_changes": [],
        "validation_gaps": [],
        "recommendation": "continue",
    }


def _validator_report(*, status: str) -> dict:
    return {
        "schema_version": 1,
        "agent_id": "validator-001",
        "role": "validator",
        "workstream": "01-review-validation",
        "status": status,
        "summary": "validation passed",
        "command": "PYTHONPATH=scripts python3 -m unittest discover -s tests",
        "output_summary": "all tests passed",
        "artifacts": [".dispatch/runs/run-001/validation/validator-001.stdout.log"],
        "not_run_reason": "",
    }


def _import_plan(repo: Path) -> Path:
    plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(json.dumps(_plan()) + "\n", encoding="utf-8")
    return Path(import_dispatch_plan(repo, plan_path)["state_dir"])


def _plan() -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": "review validator objective",
        "workstreams": [
            {
                "id": "01-review-validation",
                "title": "Review validation",
                "mode": "serial",
                "scope": "Add review validator protocol.",
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
