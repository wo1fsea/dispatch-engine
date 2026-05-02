from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class SkillInstallE2ETests(unittest.TestCase):
    def test_copied_skill_cli_drives_clean_target_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            installed_skill = tmp_path / "skills" / "dispatch-engine"
            target_repo = tmp_path / "target-repo"
            target_repo.mkdir()
            _copy_skill(REPO_ROOT, installed_skill)

            de = installed_skill / "scripts" / "de.py"
            fixture_plan = installed_skill / "fixtures" / "dogfood-runbook" / "plan.json"

            version = _run_text(de, "version")
            imported = _run_json(de, "init", str(target_repo), "--plan", str(fixture_plan), "--json")
            run_id = imported["run_id"]
            state_dir = Path(imported["state_dir"])
            dry_run = _run_json(de, "run", str(target_repo), "--run-id", run_id, "--dry-run", "--json")

            with _fake_provider_env("codex") as env:
                live = _run_json(de, "run", str(target_repo), "--run-id", run_id, "--json", env=env)

            status = _run_json(de, "status", str(target_repo), "--run-id", run_id, "--json")
            tail = _run_json(de, "tail", str(target_repo), "--run-id", run_id, "--json")
            event_types = [event["type"] for event in tail["events"]]

            self.assertEqual(version.strip(), "0.1.0")
            self.assertEqual(imported["plan_id"], "dogfood-runbook-fixture")
            self.assertTrue(
                state_dir.resolve().is_relative_to(target_repo.resolve() / ".dispatch" / "runs")
            )
            self.assertFalse((installed_skill / ".dispatch").exists())
            self.assertEqual(dry_run["provider"], "codex")
            self.assertEqual(dry_run["profile"], "codex-exec")
            self.assertEqual(dry_run["state_writes"], [])
            self.assertIn("codex", dry_run["argv"][0])
            self.assertEqual(live["state"], "completed")
            self.assertEqual(live["exit_code"], 0)
            self.assertTrue((state_dir / "prompts" / "coordinator-001.md").is_file())
            self.assertTrue((state_dir / "logs" / "coordinator-001.stdout.log").is_file())
            self.assertEqual(status["agent_counts"]["by_role"]["coordinator"], 1)
            self.assertIn("coordinator.started", event_types)
            self.assertIn("coordinator.completed", event_types)


def _copy_skill(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            ".dispatch",
            "__pycache__",
            "*.pyc",
        ),
    )


def _run_json(de: Path, *args: str, env: dict[str, str] | None = None) -> dict:
    return json.loads(_run_text(de, *args, env=env))


def _run_text(de: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        [sys.executable, str(de), *args],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )
    return result.stdout


class _fake_provider_env:
    def __init__(self, executable_name: str) -> None:
        self.executable_name = executable_name
        self._tmp: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> dict[str, str]:
        self._tmp = tempfile.TemporaryDirectory()
        bin_dir = Path(self._tmp.name)
        executable = bin_dir / self.executable_name
        executable.write_text(
            "#!/bin/sh\nprintf 'fake copied-skill provider executed\\n'\nexit 0\n",
            encoding="utf-8",
        )
        executable.chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
        return env

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._tmp is not None:
            self._tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
