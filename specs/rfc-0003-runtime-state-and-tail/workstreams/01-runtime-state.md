---
id: 01-runtime-state
language: en-US
audience: agent
doc_type: spec
status: ready
owner: unassigned
branch:
pr:
files:
  - scripts/dispatch_engine/planner.py
  - scripts/dispatch_engine/state.py
  - scripts/dispatch_engine/events.py
  - scripts/dispatch_engine/runs.py
depends_on: []
claimed_at:
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

Not started.

## Validation

- `python scripts/de.py plan . --objective "smoke test objective"`
- Confirm generated state layout exists.
- Confirm `.dispatch/` remains ignored by git.

## Blocked

Reason:
Unblock when:
Owner to unblock:

## Activity Log

- 2026-05-02 codex: workstream initialized.
