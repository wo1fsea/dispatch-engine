from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.inspect import inspect_repo
from dispatch_engine.planner import plan_objective


class InspectPlanTests(unittest.TestCase):
    def test_inspect_deduplicates_prioritizes_and_bounds_planning_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "specs" / "rfc-1").mkdir(parents=True)
            (repo / "specs" / "rfc-1" / "PRODUCT.md").write_text("product")
            (repo / "specs" / "rfc-1" / "TECH.md").write_text("tech")
            for index in range(12):
                path = repo / "docs" / f"guide-{index:02d}.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("guide")

            inspection = inspect_repo(repo)
            planning_sources = inspection["planning_sources"]

            self.assertEqual(planning_sources[:2], ["specs/rfc-1/PRODUCT.md", "specs/rfc-1/TECH.md"])
            self.assertEqual(len(planning_sources), 8)
            self.assertEqual(len(planning_sources), len(set(planning_sources)))

    def test_plan_keeps_one_workstream_for_simple_objective(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            plan = plan_objective(repo, "refresh README examples", {"validation_hints": []})

            self.assertEqual([item["id"] for item in plan["workstreams"]], ["01-implementation"])
            self.assertEqual(plan["decisions"], [])

    def test_plan_records_pending_decision_for_broad_multi_domain_objective(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            plan = plan_objective(repo, "update backend API and UI flow", {"validation_hints": []})

            self.assertEqual([item["id"] for item in plan["workstreams"]], ["01-implementation"])
            self.assertEqual(len(plan["decisions"]), 1)
            decision = plan["decisions"][0]
            self.assertEqual(decision["status"], "pending")
            self.assertIn("backend API and UI", decision["reason"])

            state_dir = Path(plan["state_dir"])
            persisted_decisions = [
                json.loads(line)
                for line in (state_dir / "decisions.jsonl").read_text().splitlines()
            ]
            events = [
                json.loads(line)
                for line in (state_dir / "events.jsonl").read_text().splitlines()
            ]

            self.assertEqual(persisted_decisions, [decision])
            self.assertIn("decision.created", [event["type"] for event in events])


if __name__ == "__main__":
    unittest.main()
