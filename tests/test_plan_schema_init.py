from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from dispatch_engine.cli import main
from dispatch_engine.events import read_events
from dispatch_engine.plan_schema import PlanValidationError, import_dispatch_plan, validate_dispatch_plan
from dispatch_engine.state import run_status, tail_events


class PlanSchemaInitTests(unittest.TestCase):
    def test_validate_rejects_missing_required_fields(self) -> None:
        with self.assertRaisesRegex(PlanValidationError, "schema_version"):
            validate_dispatch_plan(
                {
                    "plan_id": "plan-001",
                    "objective": "Ship an explicit plan",
                    "workstreams": [_workstream("01-runtime")],
                }
            )

    def test_validate_rejects_empty_duplicate_and_missing_dependencies(self) -> None:
        with self.assertRaisesRegex(PlanValidationError, "non-empty workstreams"):
            validate_dispatch_plan(
                {
                    "schema_version": 1,
                    "plan_id": "plan-001",
                    "objective": "Ship an explicit plan",
                    "workstreams": [],
                }
            )

        with self.assertRaisesRegex(PlanValidationError, "duplicate workstream id"):
            validate_dispatch_plan(
                _plan(
                    [
                        _workstream("01-runtime"),
                        _workstream("01-runtime", title="Duplicate runtime"),
                    ]
                )
            )

        with self.assertRaisesRegex(PlanValidationError, "unknown dependency"):
            validate_dispatch_plan(
                _plan([_workstream("02-tests", depends_on=["01-runtime"])])
            )

    def test_validate_rejects_uncoordinated_parallel_file_overlap(self) -> None:
        with self.assertRaisesRegex(PlanValidationError, "overlapping files"):
            validate_dispatch_plan(
                _plan(
                    [
                        _workstream(
                            "01-runtime",
                            files=["scripts/dispatch_engine/cli.py"],
                            parallel_group="runtime",
                        ),
                        _workstream(
                            "02-schema",
                            files=["scripts/dispatch_engine/cli.py"],
                            parallel_group="runtime",
                        ),
                    ]
                )
            )

    def test_validate_allows_coordinated_or_dependent_file_overlap(self) -> None:
        coordinated = validate_dispatch_plan(
            _plan(
                [
                    _workstream(
                        "01-runtime",
                        files=["scripts/dispatch_engine/cli.py"],
                        coordination="shared-write-approved",
                    ),
                    _workstream(
                        "02-schema",
                        files=["scripts/dispatch_engine/cli.py"],
                        coordination="shared-write-approved",
                    ),
                ]
            )
        )
        dependent = validate_dispatch_plan(
            _plan(
                [
                    _workstream("01-runtime", files=["scripts/dispatch_engine/cli.py"]),
                    _workstream(
                        "02-schema",
                        files=["scripts/dispatch_engine/cli.py"],
                        depends_on=["01-runtime"],
                    ),
                ]
            )
        )

        self.assertEqual(coordinated["plan_id"], "plan-001")
        self.assertEqual(dependent["plan_id"], "plan-001")

    def test_import_creates_run_state_from_plan_and_preserves_status_tail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(json.dumps(_plan([_workstream("01-runtime")])) + "\n")

            result = import_dispatch_plan(repo, plan_path)
            state_dir = Path(result["state_dir"])

            self.assertTrue((repo / ".dispatch" / "plans").is_dir())
            self.assertTrue((state_dir / "run.json").is_file())
            self.assertTrue((state_dir / "events.jsonl").is_file())
            self.assertTrue((state_dir / "decisions.jsonl").is_file())
            self.assertTrue((state_dir / "workstreams" / "01-runtime.json").is_file())
            self.assertTrue((state_dir / "artifacts").is_dir())
            self.assertTrue((state_dir / "reviews").is_dir())
            self.assertTrue((state_dir / "validation").is_dir())

            run = json.loads((state_dir / "run.json").read_text())
            workstream = json.loads((state_dir / "workstreams" / "01-runtime.json").read_text())
            events = read_events(state_dir / "events.jsonl")

            self.assertEqual(result["kind"], "plan_import")
            self.assertEqual(run["plan"]["plan_id"], "plan-001")
            self.assertEqual(run["plan"]["source_path"], str(plan_path.resolve()))
            self.assertEqual(workstream["status"], "planned")
            self.assertEqual(
                [event["type"] for event in events],
                ["run.created", "plan.imported", "workstream.planned"],
            )
            self.assertEqual(run_status(repo, run_id=result["run_id"])["run_status"], "planned")
            self.assertEqual(
                [event["type"] for event in tail_events(repo, run_id=result["run_id"])["events"]],
                ["run.created", "plan.imported", "workstream.planned"],
            )

    def test_import_external_plan_records_source_without_external_runtime_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            external = Path(tmp) / "outside" / "plan.json"
            repo.mkdir()
            external.parent.mkdir()
            external.write_text(json.dumps(_plan([_workstream("01-runtime")])) + "\n")

            result = import_dispatch_plan(repo, external)
            run = json.loads((Path(result["state_dir"]) / "run.json").read_text())

            self.assertEqual(run["plan"]["source_path"], str(external.resolve()))
            self.assertFalse((external.parent / ".dispatch").exists())
            self.assertTrue((repo / ".dispatch" / "runs" / result["run_id"]).is_dir())
            self.assertTrue((repo / ".dispatch" / "plans").is_dir())

    def test_cli_init_outputs_json_for_imported_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(json.dumps(_plan([_workstream("01-runtime")])) + "\n")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["init", str(repo), "--plan", str(plan_path), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["kind"], "plan_import")
            self.assertEqual(payload["plan_id"], "plan-001")
            self.assertEqual(payload["workstream_count"], 1)

    def test_cli_init_respects_global_json_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan_path = repo / ".dispatch" / "plans" / "plan-001.json"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(json.dumps(_plan([_workstream("01-runtime")])) + "\n")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["--json", "init", str(repo), "--plan", str(plan_path)])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["kind"], "plan_import")

    def test_cli_init_rejects_invalid_plan_with_nonzero_json_exit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan_path = repo / ".dispatch" / "plans" / "bad-plan.json"
            plan_path.parent.mkdir(parents=True)
            plan_path.write_text(json.dumps({"schema_version": 1}) + "\n")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["init", str(repo), "--plan", str(plan_path), "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(exit_code, 1)
            self.assertEqual(payload["kind"], "error")
            self.assertEqual(payload["status"], "invalid_plan")


def _plan(workstreams: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "plan_id": "plan-001",
        "objective": "Ship an explicit plan",
        "created_by": "test",
        "created_at": "2026-05-02T00:00:00Z",
        "target_repo": "/tmp/repo",
        "repo_context": {
            "instructions_read": ["AGENTS.md"],
            "planning_basis": "test plan",
            "validation_strategy": "unit tests",
        },
        "workstreams": workstreams,
        "decisions": [],
        "review": {"required": True, "strategy": "review test output"},
    }


def _workstream(
    workstream_id: str,
    *,
    title: str | None = None,
    files: list[str] | None = None,
    depends_on: list[str] | None = None,
    parallel_group: str | None = None,
    coordination: str | None = None,
) -> dict:
    workstream = {
        "id": workstream_id,
        "title": title or "Runtime import",
        "mode": "serial",
        "scope": "Import explicit plans into run state.",
        "files": files or ["scripts/dispatch_engine/runs.py"],
        "depends_on": depends_on or [],
        "parallel_group": parallel_group,
        "validation": ["PYTHONPATH=scripts python3 -m unittest discover -s tests"],
    }
    if coordination is not None:
        workstream["coordination"] = coordination
    return workstream


if __name__ == "__main__":
    unittest.main()
