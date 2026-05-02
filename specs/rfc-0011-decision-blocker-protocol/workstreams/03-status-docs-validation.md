---
workstream_id: 03-status-docs-validation
language: en-US
audience: agent
doc_type: workstream
status: completed
owner: codex-worker
branch: main
updated: 2026-05-02
depends_on:
  - 01-decision-guidance
  - 02-decision-state
---

# Status Docs Validation

Validate decision visibility through docs, status, and events.

## Result

Added focused unit coverage in `tests/test_decision_blocker_protocol.py` for:

- Decision request, query, resolve, and emitted events.
- Blocker record, unresolved query, resolve, and validation signal.
- `run_status(...)` unresolved blocker visibility.

Status now includes:

- `pending_decisions`
- `unresolved_blockers`
- `decision_blocker_validation`
