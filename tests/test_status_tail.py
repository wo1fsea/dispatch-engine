from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.plan_schema import import_dispatch_plan
from dispatch_engine.state import run_status, tail_events


class StatusTailTests(unittest.TestCase):
    def test_status_reports_latest_run_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="status objective")

            status = run_status(repo)

            self.assertEqual(status["kind"], "status")
            self.assertEqual(status["run_id"], plan["run_id"])
            self.assertEqual(status["objective"], "status objective")
            self.assertEqual(status["run_status"], "planned")
            self.assertEqual(status["workstream_counts"], {"planned": 1})
            self.assertEqual(status["pending_decisions"], 0)
            self.assertEqual(status["state_dir"], plan["state_dir"])

    def test_tail_reads_events_for_explicit_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = _import_plan(repo, objective="tail objective")

            tail = tail_events(repo, run_id=plan["run_id"])

            self.assertEqual(tail["kind"], "tail")
            self.assertEqual(tail["run_id"], plan["run_id"])
            self.assertEqual(
                [event["type"] for event in tail["events"]],
                ["run.created", "plan.imported", "workstream.planned"],
            )

    def test_status_and_tail_handle_missing_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            status = run_status(repo)
            tail = tail_events(repo)

            self.assertEqual(status["status"], "no_run")
            self.assertEqual(tail["status"], "no_run")
            self.assertIn("No Dispatch Engine runs found", status["summary"])
            self.assertIn("No Dispatch Engine runs found", tail["summary"])

    def test_explicit_missing_run_id_is_clear(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _import_plan(repo, objective="missing run objective")

            status = run_status(repo, run_id="missing")
            tail = tail_events(repo, run_id="missing")

            self.assertEqual(status["status"], "missing_run")
            self.assertEqual(tail["status"], "missing_run")
            self.assertIn("Run not found", status["summary"])
            self.assertIn("Run not found", tail["summary"])


def _import_plan(repo: Path, *, objective: str) -> dict:
    plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_text(json.dumps(_plan(objective)) + "\n")
    return import_dispatch_plan(repo, plan_path)


def _plan(objective: str) -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": objective,
        "workstreams": [
            {
                "id": "01-status-tail",
                "title": "Preserve status and tail readers",
                "mode": "serial",
                "scope": "Imported run fixture.",
                "files": ["scripts/dispatch_engine/state.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
            }
        ],
        "decisions": [],
    }


if __name__ == "__main__":
    unittest.main()
