---
workstream_id: 02-event-normalization-docs
status: merged
owner: worker-b
branch: local
claimed_at: 2026-05-04T10:53:19+08:00
lease_expires_at: 2026-05-04T12:53:19+08:00
updated: 2026-05-04
---

# Event Normalization And Docs

## Scope

Normalize legacy capability-shaped `protocol.violation` events and document
detected versus event-carried protocol violations.

## Files

- `scripts/dispatch_engine/state.py`
- `tests/test_status_tail.py`
- `references/event-protocol.md`
- `references/operator-guide.md` if operator guidance changes
- `specs/rfc-0022-protocol-violation-status-accuracy/STATUS.md`

## Acceptance

- Event payloads with `capability` but no `violation` no longer alert as
  `unknown`.
- Alert details preserve original event payload enough for audit.
- Docs describe the compatibility normalization.
- Dogfood #16 alerts no longer show `violation: "unknown"`.

## Activity Log

- 2026-05-04 worker-b: claimed workstream for event normalization and docs.
- 2026-05-04 worker-b: red test added for legacy capability-shaped protocol violation alerts.
- 2026-05-04 worker-b: implemented legacy capability event normalization and updated operator/event docs.
- 2026-05-04 worker-b: validated with focused/full unittest commands plus dogfood alerts check.
- 2026-05-04 codex: workstream created.
- 2026-05-04 codex: reviewed, reran validation, and accepted into main.
