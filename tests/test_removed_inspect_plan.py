from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.cli import build_parser, main


class RemovedInspectPlanTests(unittest.TestCase):
    def test_help_does_not_advertise_inspect_or_heuristic_plan_commands(self) -> None:
        parser = build_parser()
        commands = _subcommand_names(parser)
        help_text = parser.format_help()

        self.assertNotIn("inspect", commands)
        self.assertNotIn("plan", commands)
        self.assertNotIn("inspect", help_text)
        self.assertNotIn("plan --objective", help_text)
        self.assertIn("init", commands)
        self.assertIn("status", commands)
        self.assertIn("tail", commands)
        self.assertIn("version", commands)

    def test_removed_commands_fail_without_creating_dispatch_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as inspect_exit:
                main(["inspect", str(repo)])
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as plan_exit:
                main(["plan", str(repo), "--objective", "build from raw text"])

            self.assertEqual(inspect_exit.exception.code, 2)
            self.assertEqual(plan_exit.exception.code, 2)
            self.assertFalse((repo / ".dispatch").exists())
            self.assertIn("invalid choice", stderr.getvalue())

    def test_runtime_discovery_and_heuristic_planner_modules_are_removed(self) -> None:
        self.assertIsNone(importlib.util.find_spec("dispatch_engine.inspect"))
        self.assertIsNone(importlib.util.find_spec("dispatch_engine.planner"))


def _subcommand_names(parser) -> set[str]:
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if choices:
            return set(choices)
    return set()


if __name__ == "__main__":
    unittest.main()
