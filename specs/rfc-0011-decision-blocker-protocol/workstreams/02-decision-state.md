---
workstream_id: 02-decision-state
language: en-US
audience: agent
doc_type: workstream
status: completed
owner: codex-worker
branch: main
updated: 2026-05-02
depends_on:
  - 01-decision-guidance
---

# Decision State

Add minimal durable decision/blocker state helpers only where current state is insufficient.

## Result

Added `scripts/dispatch_engine/decisions.py`.

The helper records:

- Decision requests and resolutions in `.dispatch/runs/<run-id>/decisions.jsonl`.
- Blockers and resolutions in `.dispatch/runs/<run-id>/blockers.jsonl`.
- Tail events for `decision.requested`, `decision.resolved`, `blocker.recorded`, and `blocker.resolved`.

The helper queries:

- Latest folded decision state by decision id.
- Pending decisions.
- Latest folded blocker state by blocker id.
- Unresolved blockers.
- Mechanical validation status: `blocked` while unresolved blockers exist, otherwise `ok`.
