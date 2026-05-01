---
id: 01-runtime-state
language: en-US
audience: agent
doc_type: spec
status: validated
owner: codex
branch: main
pr:
files:
  - scripts/dispatch_engine/planner.py
  - scripts/dispatch_engine/state.py
  - scripts/dispatch_engine/events.py
  - scripts/dispatch_engine/runs.py
depends_on: []
claimed_at: 2026-05-02T00:00:00+08:00
lease_expires_at:
updated: 2026-05-02
---

# Runtime State Workstream

## Scope

Implement the durable `.dispatch/runs/<run-id>/` layout for dry-run planning.

## Plan

1. Add helpers for resolving run directories.
2. Write `run.json`, `events.jsonl`, `decisions.jsonl`, `workstreams/*.json`, and `artifacts/`.
3. Record `run.created` and `workstream.planned` events.
4. Preserve enough data for status and tail to read without recomputing plan context.

## Progress

- Claimed by codex.
- Added `events.py` for append-only event writes.
- Added `runs.py` for run id and run-directory helpers.
- Updated planner to write `run.json`, `events.jsonl`, `decisions.jsonl`, `workstreams/01-implementation.json`, and `artifacts/`.
- Added a unit test for durable run-state creation.

## Validation

- `python scripts/de.py plan . --objective "smoke test objective"`
- Confirm generated state layout exists.
- Confirm `.dispatch/` remains ignored by git.

## TDD Evidence

- Red: `PYTHONPATH=scripts python3 -m unittest tests.test_runtime_state` failed because `decisions.jsonl` was not created.
- Green: `PYTHONPATH=scripts python3 -m unittest tests.test_runtime_state` passed.
- Broader validation:
  - `python scripts/de.py plan . --objective "smoke test objective"`
  - `python scripts/de.py --help`
  - `python scripts/de.py version`
  - `python scripts/de.py inspect .`
  - `python scripts/de.py status .`
  - `git status --short --ignored .dispatch`
- Tests not run: full test suite is not available yet; this repo currently has only the targeted unittest.

## Blocked

Reason:
Unblock when:
Owner to unblock:

## Activity Log

- 2026-05-02 codex: workstream initialized.
- 2026-05-02 codex: claimed workstream and started runtime state implementation.
- 2026-05-02 codex: implemented durable run-state layout and validated targeted behavior.
