from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.decisions import (
    list_decisions,
    list_unresolved_blockers,
    record_blocker,
    record_decision_request,
    resolve_blocker,
    resolve_decision,
    validate_decision_blocker_state,
)
from dispatch_engine.events import read_events
from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.state import run_status


class DecisionBlockerProtocolTests(unittest.TestCase):
    def test_records_and_resolves_decision_requests_in_dispatch_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = _import_plan(Path(tmp))

            requested = record_decision_request(
                state_dir,
                decision_id="decision-001",
                question="Can the worker broaden scope to tests?",
                reason="The implementation file depends on missing coverage.",
                workstream="01-decision-state",
                actor="coordinator-001",
            )
            resolved = resolve_decision(
                state_dir,
                "decision-001",
                resolution="Approved test-only scope expansion.",
                actor="operator",
            )

            self.assertEqual(requested["status"], "pending")
            self.assertEqual(resolved["status"], "resolved")
            self.assertEqual(resolved["resolution"], "Approved test-only scope expansion.")
            self.assertEqual([item["status"] for item in list_decisions(state_dir)], ["resolved"])

            events = read_events(state_dir / "events.jsonl")
            self.assertEqual(events[-2]["type"], "decision.requested")
            self.assertEqual(events[-2]["payload"]["decision_id"], "decision-001")
            self.assertEqual(events[-1]["type"], "decision.resolved")

    def test_records_queries_and_resolves_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            state_dir = _import_plan(repo)

            blocker = record_blocker(
                state_dir,
                blocker_id="blocker-001",
                summary="Worker needs product scope decision before editing.",
                workstream="01-decision-state",
                severity="blocking",
                actor="worker-001",
            )

            self.assertEqual(blocker["status"], "open")
            self.assertEqual(
                [item["blocker_id"] for item in list_unresolved_blockers(state_dir)],
                ["blocker-001"],
            )
            self.assertEqual(validate_decision_blocker_state(state_dir)["status"], "blocked")
            self.assertEqual(run_status(repo)["unresolved_blockers"], 1)

            resolved = resolve_blocker(
                state_dir,
                "blocker-001",
                resolution="Operator clarified scope; worker may continue.",
                actor="coordinator-001",
            )

            self.assertEqual(resolved["status"], "resolved")
            self.assertEqual(list_unresolved_blockers(state_dir), [])
            self.assertEqual(validate_decision_blocker_state(state_dir)["status"], "ok")
            self.assertEqual(run_status(repo)["unresolved_blockers"], 0)


def _import_plan(repo: Path) -> Path:
    plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(json.dumps(_plan()) + "\n")
    return Path(import_dispatch_plan(repo, plan_path)["state_dir"])


def _plan() -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": "decision blocker protocol objective",
        "workstreams": [
            {
                "id": "01-decision-state",
                "title": "Decision state protocol",
                "mode": "serial",
                "scope": "Add durable decision and blocker state.",
                "files": ["scripts/dispatch_engine/decisions.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
            }
        ],
        "decisions": [],
    }


if __name__ == "__main__":
    unittest.main()
