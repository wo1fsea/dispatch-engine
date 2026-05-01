from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.planner import plan_objective


class RuntimeStateTests(unittest.TestCase):
    def test_plan_writes_durable_run_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            inspection = {"validation_hints": ["none detected"]}

            plan = plan_objective(repo, "smoke test objective", inspection)

            state_dir = Path(plan["state_dir"])
            self.assertTrue((state_dir / "run.json").is_file())
            self.assertTrue((state_dir / "events.jsonl").is_file())
            self.assertTrue((state_dir / "decisions.jsonl").is_file())
            self.assertTrue((state_dir / "workstreams").is_dir())
            self.assertTrue((state_dir / "artifacts").is_dir())

            workstream_file = state_dir / "workstreams" / "01-implementation.json"
            self.assertTrue(workstream_file.is_file())

            run = json.loads((state_dir / "run.json").read_text())
            workstream = json.loads(workstream_file.read_text())
            events = [
                json.loads(line)
                for line in (state_dir / "events.jsonl").read_text().splitlines()
            ]

            self.assertEqual(run["status"], "planned")
            self.assertEqual(workstream["status"], "planned")
            self.assertEqual([event["type"] for event in events], ["run.created", "workstream.planned"])


if __name__ == "__main__":
    unittest.main()
