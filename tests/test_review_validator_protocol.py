from __future__ import annotations

import json
import shutil
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
from dispatch_engine.state import run_status


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "validator_reports"


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

    def test_missing_validator_report_uses_report_schema_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(state_dir)

            violations = validate_review_validator_report(state_dir, "validator-001")

            self.assertEqual([item["violation"] for item in violations], ["missing_validator_report"])
            self.assertEqual(
                violations[0]["details"]["report_path"],
                f".dispatch/runs/{state_dir.name}/validation/validator-001.json",
            )

    def test_malformed_validator_json_uses_specific_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(state_dir)
            _validator_report_path(state_dir, "validator-001").write_text("{not-json", encoding="utf-8")

            violations = validate_review_validator_report(state_dir, "validator-001")

            self.assertEqual([item["violation"] for item in violations], ["malformed_validator_json"])
            self.assertEqual(violations[0]["details"]["field"], "$")

    def test_validator_missing_required_fields_uses_specific_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(state_dir)
            report = _validator_report(status="passed")
            report.pop("summary")
            write_validator_report(state_dir, "validator-001", report)

            violations = validate_review_validator_report(state_dir, "validator-001")

            self.assertEqual([item["violation"] for item in violations], ["missing_validator_fields"])
            self.assertEqual(violations[0]["details"]["missing_fields"], ["summary"])

    def test_validator_invalid_field_type_uses_specific_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(state_dir)
            report = _validator_report(status="passed")
            report["artifacts"] = ".dispatch/runs/run-001/validation/validator-001.stdout.log"
            write_validator_report(state_dir, "validator-001", report)

            violations = validate_review_validator_report(state_dir, "validator-001")

            self.assertEqual([item["violation"] for item in violations], ["invalid_validator_field_type"])
            self.assertEqual(violations[0]["details"]["field"], "artifacts")
            self.assertEqual(violations[0]["details"]["actual"], "str")
            self.assertEqual(violations[0]["details"]["expected"], "array")

    def test_validator_identity_mismatch_uses_specific_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(state_dir)
            report = _validator_report(status="passed")
            report["agent_id"] = "validator-999"
            write_validator_report(state_dir, "validator-001", report)

            violations = validate_review_validator_report(state_dir, "validator-001")

            self.assertEqual([item["violation"] for item in violations], ["validator_identity_mismatch"])
            self.assertEqual(violations[0]["details"]["field"], "agent_id")
            self.assertEqual(violations[0]["details"]["actual"], "validator-999")
            self.assertEqual(violations[0]["details"]["expected"], "validator-001")

    def test_useful_completed_validator_fixture_is_accepted_as_compatibility_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(
                state_dir,
                agent_id="validator-010",
                workstream="04-cli-run-loop-validation",
            )
            _copy_validator_fixture(state_dir, "validator-010", "validator-010-useful-completed.json")

            self.assertEqual(validate_review_validator_report(state_dir, "validator-010"), [])
            self.assertEqual(detect_protocol_violations(state_dir), [])

    def test_completed_validator_with_failed_structured_evidence_reports_inconsistent_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(
                state_dir,
                agent_id="validator-010",
                workstream="04-cli-run-loop-validation",
            )
            report = _load_validator_fixture("validator-010-useful-completed.json")
            report["validation"][0]["status"] = "failed"
            report["validation"][0]["evidence"] = "Unit tests failed."
            write_validator_report(state_dir, "validator-010", report)

            violations = validate_review_validator_report(state_dir, "validator-010")

            self.assertEqual([item["violation"] for item in violations], ["inconsistent_validation_evidence"])
            self.assertEqual(violations[0]["details"]["field"], "validation[0].status")
            self.assertEqual(violations[0]["details"]["actual"], "failed")
            self.assertEqual(violations[0]["details"]["suggested_status"], "failed")

    def test_passed_validator_with_failed_structured_evidence_reports_inconsistent_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(
                state_dir,
                agent_id="validator-010",
                workstream="04-cli-run-loop-validation",
            )
            report = _load_validator_fixture("validator-010-useful-completed.json")
            report["status"] = "passed"
            report["validation"][0]["status"] = "failed"
            write_validator_report(state_dir, "validator-010", report)

            violations = validate_review_validator_report(state_dir, "validator-010")

            self.assertEqual([item["violation"] for item in violations], ["inconsistent_validation_evidence"])
            self.assertEqual(violations[0]["details"]["field"], "validation[0].status")
            self.assertEqual(violations[0]["details"]["suggested_status"], "failed")

    def test_validator_with_unknown_status_reports_invalid_status_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(
                state_dir,
                agent_id="validator-010",
                workstream="04-cli-run-loop-validation",
            )
            report = _load_validator_fixture("validator-010-useful-completed.json")
            report["status"] = "complete"
            write_validator_report(state_dir, "validator-010", report)

            violations = validate_review_validator_report(state_dir, "validator-010")

            self.assertEqual([item["violation"] for item in violations], ["invalid_validator_status"])
            self.assertEqual(violations[0]["details"]["field"], "status")
            self.assertEqual(violations[0]["details"]["actual"], "complete")
            self.assertEqual(violations[0]["details"]["allowed"], ["passed", "failed", "blocked", "skipped"])
            self.assertEqual(violations[0]["details"]["suggested_status"], "passed")

    def test_validator_missing_aggregate_evidence_reports_exact_schema_repair(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(
                state_dir,
                agent_id="validator-010",
                workstream="04-cli-run-loop-validation",
            )
            report = _load_validator_fixture("validator-010-useful-completed.json")
            report.pop("output_summary")
            write_validator_report(state_dir, "validator-010", report)

            violations = validate_review_validator_report(state_dir, "validator-010")

            self.assertEqual([item["violation"] for item in violations], ["missing_validation_evidence"])
            self.assertEqual(violations[0]["details"]["missing_fields"], ["output_summary"])
            self.assertEqual(violations[0]["details"]["evidence_mode"], "non_skipped_validator")

    def test_validator_report_schema_failures_get_specific_status_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            _register_validator(
                state_dir,
                agent_id="validator-010",
                workstream="04-cli-run-loop-validation",
            )
            report = _load_validator_fixture("validator-010-useful-completed.json")
            report["status"] = "complete"
            write_validator_report(state_dir, "validator-010", report)

            status = run_status(repo)

            self.assertIn(
                {
                    "type": "repair_report_schema",
                    "agent_id": "validator-010",
                    "role": "validator",
                    "report_path": f".dispatch/runs/{state_dir.name}/validation/validator-010.json",
                    "diagnostic": "invalid_validator_status",
                    "suggested_status": "passed",
                },
                status["next_actions"],
            )
            self.assertNotIn({"type": "repair_protocol_violations", "count": 1}, status["next_actions"])

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

    def test_reviewer_validator_shared_protocol_requires_terminal_reports(self) -> None:
        prompt_path = Path(__file__).resolve().parents[1] / "references" / "prompts" / "reviewer-validator-protocol.md"

        text = prompt_path.read_text(encoding="utf-8")

        self.assertIn("terminal report", text)
        self.assertIn("stale_validation_worker_without_report", text)
        self.assertIn("incomplete_validation_evidence", text)


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


def _register_validator(
    state_dir: Path,
    *,
    agent_id: str = "validator-001",
    workstream: str = "01-review-validation",
) -> dict:
    return register_agent(
        state_dir,
        agent_id=agent_id,
        role="validator",
        provider="claude",
        profile="claude-p",
        status="completed",
        workstream=workstream,
        allowed_write_roots=[],
        prompt_path=f".dispatch/runs/{state_dir.name}/prompts/{agent_id}.md",
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


def _load_validator_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _copy_validator_fixture(state_dir: Path, agent_id: str, name: str) -> None:
    destination = state_dir / "validation" / f"{agent_id}.json"
    destination.parent.mkdir(exist_ok=True)
    shutil.copyfile(FIXTURES_DIR / name, destination)


def _validator_report_path(state_dir: Path, agent_id: str) -> Path:
    path = state_dir / "validation" / f"{agent_id}.json"
    path.parent.mkdir(exist_ok=True)
    return path


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
