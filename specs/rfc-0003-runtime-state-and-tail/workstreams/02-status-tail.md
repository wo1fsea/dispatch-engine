---
id: 02-status-tail
language: en-US
audience: agent
doc_type: spec
status: validated
owner: codex
branch: main
pr:
files:
  - scripts/dispatch_engine/cli.py
  - scripts/dispatch_engine/state.py
  - scripts/dispatch_engine/events.py
depends_on:
  - 01-runtime-state
claimed_at: 2026-05-02T00:00:00+08:00
lease_expires_at:
updated: 2026-05-02
---

# Status And Tail Workstream

## Scope

Add operator-facing status and tail commands over the run-state files.

## Plan

1. Add `tail` command.
2. Add `--run-id` to `status` and `tail`.
3. Make `status` report run id, objective, run status, workstream counts, pending decisions, and state path.
4. Make `tail` print chronological events and exit.
5. Support no-run and missing-run messages.

## Progress

- Claimed by codex.
- Added structured `run_status` and `tail_events` state readers.
- Added `de tail`.
- Added `--run-id` to `status` and `tail`.
- Added subcommand-local `--json` support so `python scripts/de.py status . --json` works.
- Added status/tail unittest coverage for latest run, explicit run id, no-run, and missing-run cases.

## Validation

- `python scripts/de.py status .`
- `python scripts/de.py tail .`
- `python scripts/de.py status . --json`
- `python scripts/de.py tail . --json`
- Missing-run checks in a temporary empty directory.

## TDD Evidence

- Red: `PYTHONPATH=scripts python3 -m unittest tests.test_status_tail` failed because `run_status` and `tail_events` did not exist.
- Green: `PYTHONPATH=scripts python3 -m unittest tests.test_status_tail` passed.
- Broader validation:
  - `PYTHONPATH=scripts python3 -m unittest discover -s tests`
  - `python scripts/de.py plan . --objective "smoke test objective"`
  - `python scripts/de.py status .`
  - `python scripts/de.py tail .`
  - `python scripts/de.py status . --run-id "$latest" --json`
  - `python scripts/de.py tail . --run-id "$latest" --json`
  - `python scripts/de.py status /tmp --json`
  - `python scripts/de.py tail /tmp --json`
- Tests not run: no external worker or integration suite exists yet.

## Blocked

Reason:
Unblock when:
Owner to unblock:

## Activity Log

- 2026-05-02 codex: workstream initialized.
- 2026-05-02 codex: claimed workstream and started status/tail implementation.
- 2026-05-02 codex: implemented and validated status/tail CLI behavior.
