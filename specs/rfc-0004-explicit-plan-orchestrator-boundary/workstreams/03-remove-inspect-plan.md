---
workstream_id: 03-remove-inspect-plan
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: Worker C
branch: main
updated: 2026-05-02
depends_on:
  - 02-plan-schema-init
---

# Remove Runtime Inspect And Heuristic Plan

## Scope

Remove or deprecate the runtime-owned repository discovery and heuristic planning commands.

## Files

- `scripts/dispatch_engine/cli.py`
- `scripts/dispatch_engine/inspect.py`
- `scripts/dispatch_engine/planner.py`
- `tests/test_inspect_plan.py`
- `tests/`

## Requirements

- Remove `inspect` and `plan --objective` from normal CLI help, or leave migration stubs that clearly fail with guidance to use explicit plan import.
- Delete or replace tests that assert runtime repository discovery and objective heuristics.
- Ensure no code path creates a plan from raw objective text.
- Preserve reusable run-state helpers needed by `init --plan`.

## Validation

```bash
python3 scripts/de.py --help
PYTHONPATH=scripts python3 -m unittest discover -s tests
```

Manual check: invoking old commands should not silently perform repository discovery or heuristic planning.

## Activity Log

- 2026-05-02 Worker C: claimed workstream 03 to remove runtime-owned inspect and heuristic plan behavior while preserving explicit plan import status/tail coverage.
- 2026-05-02 Worker C: implemented and validated removal of normal CLI `inspect`/heuristic `plan` paths and deleted the dead runtime discovery/planner modules. Evidence: `PYTHONPATH=scripts python3 -m unittest tests.test_removed_inspect_plan tests.test_runtime_state tests.test_status_tail`; `PYTHONPATH=scripts python3 -m unittest discover -s tests`; `python3 scripts/de.py --help`; `python3 scripts/de.py version`; `python3 scripts/de.py init . --plan .dispatch/plans/worker-c-smoke-plan.json`; `python3 scripts/de.py status .`; `python3 scripts/de.py tail .`; `python3 scripts/de.py inspect .` exits 2; `python3 scripts/de.py plan . --objective smoke` exits 2; `git diff --check`.
