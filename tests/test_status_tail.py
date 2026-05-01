from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from dispatch_engine.planner import plan_objective
from dispatch_engine.state import run_status, tail_events


class StatusTailTests(unittest.TestCase):
    def test_status_reports_latest_run_details(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = plan_objective(repo, "status objective", {"validation_hints": []})

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
            plan = plan_objective(repo, "tail objective", {"validation_hints": []})

            tail = tail_events(repo, run_id=plan["run_id"])

            self.assertEqual(tail["kind"], "tail")
            self.assertEqual(tail["run_id"], plan["run_id"])
            self.assertEqual([event["type"] for event in tail["events"]], ["run.created", "workstream.planned"])

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
            plan_objective(repo, "missing run objective", {"validation_hints": []})

            status = run_status(repo, run_id="missing")
            tail = tail_events(repo, run_id="missing")

            self.assertEqual(status["status"], "missing_run")
            self.assertEqual(tail["status"], "missing_run")
            self.assertIn("Run not found", status["summary"])
            self.assertIn("Run not found", tail["summary"])


if __name__ == "__main__":
    unittest.main()
