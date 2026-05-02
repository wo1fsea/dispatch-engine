---
workstream_id: 01-detached-supervisor-runtime
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: codex
branch: main
updated: 2026-05-02
depends_on:
  - rfc-0013
---

# Detached Supervisor Runtime

Implemented `de run --detach`, `scripts/dispatch_engine/supervisor.py`,
`supervisors/` run-state files, and tests that prove detached launch returns
before a slow fake provider exits.
