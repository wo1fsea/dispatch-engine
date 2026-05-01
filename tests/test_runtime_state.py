from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.plan_schema import import_dispatch_plan


class RuntimeStateTests(unittest.TestCase):
    def test_imported_plan_writes_durable_run_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(json.dumps(_plan()) + "\n")

            plan = import_dispatch_plan(repo, plan_path)

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
            self.assertEqual(run["objective"], "smoke test objective")
            self.assertEqual(run["plan"]["plan_id"], "plan-001")
            self.assertEqual(workstream["status"], "planned")
            self.assertEqual(
                [event["type"] for event in events],
                ["run.created", "plan.imported", "workstream.planned"],
            )


def _plan() -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": "smoke test objective",
        "workstreams": [
            {
                "id": "01-implementation",
                "title": "Implement objective",
                "mode": "serial",
                "scope": "Imported workstream fixture.",
                "files": ["scripts/dispatch_engine/cli.py"],
                "depends_on": [],
                "parallel_group": None,
                "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
            }
        ],
        "decisions": [],
    }


if __name__ == "__main__":
    unittest.main()
