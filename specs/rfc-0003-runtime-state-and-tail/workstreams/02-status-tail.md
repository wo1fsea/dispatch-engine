---
id: 02-status-tail
language: en-US
audience: agent
doc_type: spec
status: ready
owner: unassigned
branch:
pr:
files:
  - scripts/dispatch_engine/cli.py
  - scripts/dispatch_engine/state.py
  - scripts/dispatch_engine/events.py
depends_on:
  - 01-runtime-state
claimed_at:
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

Not started.

## Validation

- `python scripts/de.py status .`
- `python scripts/de.py tail .`
- `python scripts/de.py status . --json`
- `python scripts/de.py tail . --json`
- Missing-run checks in a temporary empty directory.

## Blocked

Reason:
Unblock when:
Owner to unblock:

## Activity Log

- 2026-05-02 codex: workstream initialized.
