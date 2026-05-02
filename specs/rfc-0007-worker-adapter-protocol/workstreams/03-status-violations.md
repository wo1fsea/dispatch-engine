---
workstream_id: 03-status-violations
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: codex
branch: main
updated: 2026-05-02
depends_on:
  - 01-worker-state-report-protocol
---

# Status And Protocol Violations

## Scope

Extend status/protocol checks so worker execution evidence is visible and obvious contract failures are reported.

## Files

- `scripts/dispatch_engine/agents.py`
- `scripts/dispatch_engine/state.py`
- `scripts/dispatch_engine/events.py`
- `tests/test_worker_adapter_protocol.py`

## Requirements

- `de status` continues to report counts by role and status.
- `de status --json` includes workstream assignments for workers/reviewers/validators.
- Detect completed workers with missing reports.
- Detect malformed worker reports.
- Detect worker report changed files outside assigned files or allowed write roots.
- Detect implemented/completed workstreams without valid implementation-agent reports.
- Emit `protocol.violation` events when violations are recorded.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py status <temp-repo> --json
git diff --check
```

Evidence recorded on 2026-05-02:

- Worker report violations for missing reports, malformed reports, and out-of-scope changed files are implemented in helper tests.
- `de status` protocol violation summaries now include detected worker report violations.
- Added focused coverage that `record_protocol_violations` emits `protocol.violation` events for worker report failures.
- Coordinator review hardened allowed write root matching so roots match the path itself or descendants, not arbitrary sibling prefixes.
- Existing status JSON coverage confirms worker assignment and worker role/status counts are exposed.
- `PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol` passed, 7 tests.
