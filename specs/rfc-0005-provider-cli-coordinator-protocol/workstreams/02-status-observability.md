---
workstream_id: 02-status-observability
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: Worker B
branch: main
updated: 2026-05-02
depends_on:
  - 01-agent-state-protocol
---

# Status Observability

## Scope

Make `de status` and event readers report coordinator and subagent progress from durable state.

## Files

- `scripts/dispatch_engine/state.py`
- `scripts/dispatch_engine/cli.py`
- optional new module: `scripts/dispatch_engine/agents.py`
- `references/event-protocol.md`
- `tests/`

## Requirements

- Report selected provider and coordinator profile when present.
- Report coordinator status and heartbeat freshness.
- Report agent counts by role and status.
- Report active workstream assignments.
- Report completed, failed, blocked, and unassigned workstreams.
- Report pending decisions and protocol violation count.
- Include structured `agents`, `agent_counts`, `workstream_assignments`, `heartbeat_summary`, and `protocol_violations` in `de status --json`.
- Keep human `de status` concise and readable.
- Keep `de tail` compatible with new event types.

## Validation

```bash
python3 scripts/de.py status .
python3 scripts/de.py status . --json
python3 scripts/de.py tail .
PYTHONPATH=scripts python3 -m unittest discover -s tests
git diff --check
```

## Activity Log

- 2026-05-02 Worker B: implemented read-only status observability for registered agents, coordinator provider/profile/status, active workstream assignments, heartbeat counts, and protocol violation summaries; validated with focused status tests, full unittest discovery, temp-run human and JSON status smoke checks, and `git diff --check`.
- 2026-05-02 Worker S: initialized workstream as ready.
