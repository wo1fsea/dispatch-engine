---
spec_id: rfc-0020-run-cancel-control
workstream_id: 02-state-events-status
language: en-US
audience: agent
doc_type: workstream
status: ready-for-implementation
owner: unassigned
created: 2026-05-03
updated: 2026-05-03
depends_on:
  - 01-cancel-command-runtime
---

# State Events Status

## Scope

Make cancellation durable and observable through the same `.dispatch/` and
Codex-facing JSON surfaces used by detached runs, events, alerts, and
heartbeat observation.

## Files

- `scripts/dispatch_engine/cancel.py`
- `scripts/dispatch_engine/events.py`
- `scripts/dispatch_engine/state.py`
- `scripts/dispatch_engine/agents.py`
- Focused tests under `tests/`

## Requirements

- Set `run.json` `status` to `cancelled`.
- Record `cancelled_at`, `cancelled_by`, and `cancellation_reason` in
  `run.json`.
- Mark active supervisor records `cancelled`, with signal outcome metadata.
- Mark active coordinator, worker, reviewer, and validator records
  `cancelled`.
- Preserve agents already in `completed`, `failed`, or `cancelled`.
- Emit append-only `run.cancel.requested`, `run.cancel.signal`, and
  `run.cancel.completed` events.
- Add `run.cancel.failed` only if needed for state errors that prevent durable
  cancellation.
- Ensure `status --json` exposes terminal cancelled state, cancellation
  metadata, and cancelled agent/supervisor counts.
- Ensure `events --since --json` returns cancellation events with stable event
  ids.
- Ensure `alerts --json` includes a terminal cancellation alert suitable for
  heartbeat reporting.

## Acceptance

1. After cancellation, `status --json` has `run_status: "cancelled"`.
2. Status includes the cancellation reason and timestamp.
3. Agent and supervisor counts include `cancelled`.
4. `events --since` can read cancellation events after an event cursor.
5. `alerts --json` reports cancellation as a material terminal alert.
6. Tests prove active agents are cancelled while completed and failed agents
   keep their prior terminal statuses.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_run_cancel_control
PYTHONPATH=scripts python3 -m unittest tests.test_codex_facing_control_surface
python3 scripts/de.py status --help
python3 scripts/de.py events --help
python3 scripts/de.py alerts --help
git diff --check
```
