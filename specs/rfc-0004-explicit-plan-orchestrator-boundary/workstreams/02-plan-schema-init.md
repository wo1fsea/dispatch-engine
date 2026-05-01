---
workstream_id: 02-plan-schema-init
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: Worker B
branch: main
updated: 2026-05-02
depends_on: []
claimed_at: 2026-05-02T00:00:00Z
lease_expires_at: 2026-05-03T00:00:00Z
---

# Plan Schema And Init

## Scope

Add the explicit dispatch plan contract and import command.

## Files

- `scripts/dispatch_engine/cli.py`
- `scripts/dispatch_engine/runs.py`
- `scripts/dispatch_engine/state.py`
- optional new module: `scripts/dispatch_engine/plan_schema.py`
- `references/event-protocol.md`
- `tests/`

## Requirements

- Add `python3 scripts/de.py init <repo> --plan <path>`.
- Validate required plan fields, unique workstream ids, dependencies, and unsafe parallel write-scope overlap.
- Create `.dispatch/runs/<run-id>/` from the explicit plan.
- Create `.dispatch/plans/` as the expected generated-plan location.
- Emit `plan.imported`.
- Keep `status` and `tail` working on imported runs.

## Validation

```bash
python3 scripts/de.py init . --plan .dispatch/plans/<plan-id>.json
python3 scripts/de.py init . --plan .dispatch/plans/<plan-id>.json --json
python3 scripts/de.py status .
python3 scripts/de.py tail .
PYTHONPATH=scripts python3 -m unittest discover -s tests
```

## Activity Log

- 2026-05-02 Worker B: claimed workstream 02 for explicit plan schema validation and `init --plan` runtime import.
- 2026-05-02 Worker B: implemented and validated `init --plan`, explicit plan schema checks, imported run state, and `status`/`tail` compatibility. Evidence: `PYTHONPATH=scripts python3 -m unittest discover -s tests`; `python3 scripts/de.py --help`; `python3 scripts/de.py version`; `python3 scripts/de.py init . --plan .dispatch/plans/codex-smoke-plan.json`; `python3 scripts/de.py init . --plan .dispatch/plans/codex-smoke-plan.json --json`; `python3 scripts/de.py status .`; `python3 scripts/de.py tail .`; `git diff --check`.
