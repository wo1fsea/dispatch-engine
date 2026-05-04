---
workstream_id: 01-completion-accuracy
status: merged
owner: worker-b
branch: local
claimed_at: 2026-05-04T10:53:19+08:00
lease_expires_at: 2026-05-04T12:53:19+08:00
updated: 2026-05-04
---

# Completion Violation Accuracy

## Scope

Refine detected completion violations so assigned but invalid implementation
agents are not mislabeled as unregistered.

## Files

- `scripts/dispatch_engine/agents.py`
- `tests/test_worker_adapter_protocol.py`

## Acceptance

- Truly unregistered completed workstreams still report
  `unregistered_implementation_completion`.
- Completed workstreams with assigned cancelled/failed/running agents report a
  targeted diagnostic with agent id and status.
- Completed workstreams with assigned completed agents but invalid reports keep
  report diagnostics and do not add the unregistered fallback.

## Activity Log

- 2026-05-04 worker-b: claimed workstream for completion violation accuracy.
- 2026-05-04 worker-b: red tests added for assigned missing, invalid-status, and invalid-report completion diagnostics.
- 2026-05-04 worker-b: implemented targeted assigned-agent completion diagnostics.
- 2026-05-04 worker-b: validated with focused/full unittest commands plus dogfood status check.
- 2026-05-04 codex: workstream created.
- 2026-05-04 codex: reviewed, reran validation, and accepted into main.
