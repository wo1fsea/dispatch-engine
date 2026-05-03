from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from dispatch_engine.cli import main
from dispatch_engine.decisions import (
    AUTONOMOUS_TECHNICAL_ACTOR,
    AUTONOMOUS_TECHNICAL_MODE,
    AUTONOMOUS_TECHNICAL_TRIGGER,
    DecisionBlockerValidationError,
    list_decisions,
    resolve_decision,
)
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.state import run_status


class AutonomousDecisionRecordTests(unittest.TestCase):
    def test_resolve_decision_cli_records_autonomous_technical_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "resolve-decision",
                        str(repo),
                        "--id",
                        "decision-001",
                        "--option",
                        "minimal_adapter",
                        "--autonomous-technical",
                        "--unanswered-heartbeats",
                        "4",
                        "--first-seen-heartbeat-id",
                        "heartbeat-000012",
                        "--last-seen-heartbeat-id",
                        "heartbeat-000015",
                        "--autonomous-rationale",
                        "Minimal adapter keeps existing contracts and is reversible.",
                        "--validation-expected",
                        "PYTHONPATH=scripts python3 -m unittest discover -s tests",
                        "--json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            decision = payload["decision"]
            autonomous_decision = decision["autonomous_decision"]
            self.assertEqual(decision["resolution_mode"], AUTONOMOUS_TECHNICAL_MODE)
            self.assertEqual(decision["resolved_by"], AUTONOMOUS_TECHNICAL_ACTOR)
            self.assertEqual(decision["selected_option_id"], "minimal_adapter")
            self.assertEqual(autonomous_decision["trigger"], AUTONOMOUS_TECHNICAL_TRIGGER)
            self.assertEqual(autonomous_decision["unanswered_heartbeat_count"], 4)
            self.assertEqual(autonomous_decision["heartbeat_interval_minutes"], 15)
            self.assertEqual(autonomous_decision["first_seen_heartbeat_id"], "heartbeat-000012")
            self.assertEqual(autonomous_decision["last_seen_heartbeat_id"], "heartbeat-000015")
            self.assertEqual(
                autonomous_decision["validation_expected"],
                ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
            )
            self.assertEqual(list_decisions(state_dir)[0]["resolution_mode"], AUTONOMOUS_TECHNICAL_MODE)

    def test_autonomous_decision_validation_rejects_low_heartbeat_count_and_missing_rationale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = _import_plan(Path(tmp))

            with self.assertRaisesRegex(DecisionBlockerValidationError, "unanswered_heartbeat_count"):
                resolve_decision(
                    state_dir,
                    "decision-001",
                    option_id="minimal_adapter",
                    actor=AUTONOMOUS_TECHNICAL_ACTOR,
                    resolution_mode=AUTONOMOUS_TECHNICAL_MODE,
                    autonomous_decision=_autonomous_metadata(
                        unanswered_heartbeat_count=3,
                        rationale="Minimal adapter keeps existing contracts.",
                    ),
                )

            with self.assertRaisesRegex(DecisionBlockerValidationError, "rationale"):
                resolve_decision(
                    state_dir,
                    "decision-001",
                    option_id="minimal_adapter",
                    actor=AUTONOMOUS_TECHNICAL_ACTOR,
                    resolution_mode=AUTONOMOUS_TECHNICAL_MODE,
                    autonomous_decision=_autonomous_metadata(
                        unanswered_heartbeat_count=4,
                        rationale="",
                    ),
                )

            self.assertEqual(list_decisions(state_dir)[0]["status"], "pending")

    def test_autonomous_decision_validation_rejects_unsupported_modes_and_missing_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = _import_plan(Path(tmp))

            with self.assertRaisesRegex(DecisionBlockerValidationError, "unsupported"):
                resolve_decision(
                    state_dir,
                    "decision-001",
                    option_id="minimal_adapter",
                    resolution_mode="manual",
                )

            with self.assertRaisesRegex(DecisionBlockerValidationError, "requires autonomous_technical"):
                resolve_decision(
                    state_dir,
                    "decision-001",
                    option_id="minimal_adapter",
                    autonomous_decision=_autonomous_metadata(
                        unanswered_heartbeat_count=4,
                        rationale="Minimal adapter keeps existing contracts.",
                    ),
                )

            with self.assertRaisesRegex(DecisionBlockerValidationError, "validation_expected"):
                resolve_decision(
                    state_dir,
                    "decision-001",
                    option_id="minimal_adapter",
                    actor=AUTONOMOUS_TECHNICAL_ACTOR,
                    resolution_mode=AUTONOMOUS_TECHNICAL_MODE,
                    autonomous_decision={
                        **_autonomous_metadata(
                            unanswered_heartbeat_count=4,
                            rationale="Minimal adapter keeps existing contracts.",
                        ),
                        "validation_expected": [],
                    },
                )

            self.assertEqual(list_decisions(state_dir)[0]["status"], "pending")

    def test_autonomous_decision_cli_rejects_conflicting_actor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _import_plan(repo)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "resolve-decision",
                        str(repo),
                        "--id",
                        "decision-001",
                        "--option",
                        "minimal_adapter",
                        "--autonomous-technical",
                        "--actor",
                        "operator",
                        "--unanswered-heartbeats",
                        "4",
                        "--autonomous-rationale",
                        "Minimal adapter keeps existing contracts and is reversible.",
                        "--json",
                    ]
                )

            self.assertEqual(exit_code, 1)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "invalid_decision_resolution")
            self.assertIn(AUTONOMOUS_TECHNICAL_ACTOR, payload["summary"])

    def test_status_summarizes_autonomous_decision_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)
            resolve_decision(
                state_dir,
                "decision-001",
                option_id="minimal_adapter",
                actor=AUTONOMOUS_TECHNICAL_ACTOR,
                resolution_mode=AUTONOMOUS_TECHNICAL_MODE,
                autonomous_decision=_autonomous_metadata(
                    unanswered_heartbeat_count=4,
                    rationale="Minimal adapter keeps existing contracts and can be replaced later.",
                ),
            )

            status = run_status(repo)

            self.assertEqual(status["autonomous_decisions"]["count"], 1)
            self.assertEqual(
                status["autonomous_decisions"]["records"],
                [
                    {
                        "decision_id": "decision-001",
                        "selected_option_id": "minimal_adapter",
                        "resolved_at": list_decisions(state_dir)[0]["resolved_at"],
                        "rationale": "Minimal adapter keeps existing contracts and can be replaced later.",
                        "validation_expected": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
                    }
                ],
            )


def _import_plan(repo: Path) -> Path:
    plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(_plan()) + "\n", encoding="utf-8")
    return Path(import_dispatch_plan(repo, plan_path)["state_dir"])


def _plan() -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": "autonomous decision record objective",
        "workstreams": [
            {
                "id": "01-runtime",
                "title": "Runtime schema and CLI",
                "mode": "serial",
                "scope": "Add autonomous decision record support.",
                "files": ["scripts/dispatch_engine/decisions.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
            }
        ],
        "decisions": [
            {
                "id": "decision-001",
                "decision_id": "decision-001",
                "status": "pending",
                "question": "Choose internal adapter shape.",
                "options": [
                    {"id": "minimal_adapter", "label": "Minimal adapter", "recommended": True},
                    {"id": "wide_adapter", "label": "Wider adapter"},
                ],
            }
        ],
    }


def _autonomous_metadata(*, unanswered_heartbeat_count: int, rationale: str) -> dict:
    return {
        "trigger": AUTONOMOUS_TECHNICAL_TRIGGER,
        "unanswered_heartbeat_count": unanswered_heartbeat_count,
        "technical_scope": True,
        "conservative": True,
        "reversible": True,
        "inside_approved_objective": True,
        "excluded_categories": [
            "product_behavior",
            "security_privacy",
            "deployment",
            "credentials",
            "destructive_data",
            "legal_financial",
            "business_scope",
        ],
        "rationale": rationale,
        "validation_expected": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
    }


if __name__ == "__main__":
    unittest.main()
