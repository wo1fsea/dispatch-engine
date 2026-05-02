---
workstream_id: 01-worker-state-report-protocol
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: codex
branch: main
updated: 2026-05-02
depends_on: []
---

# Worker State Report Protocol

## Scope

Implement durable worker registration, worker report writing/reading, report validation, and lifecycle state helpers.

## Files

- `scripts/dispatch_engine/agents.py`
- `scripts/dispatch_engine/events.py`
- `scripts/dispatch_engine/runs.py`
- `tests/test_worker_adapter_protocol.py`

## Requirements

- Register worker/reviewer/validator agents with workstream, assigned files, allowed write roots, prompt path, report path, stdout path, stderr path, and log path.
- Support worker statuses `registered`, `running`, `blocked`, `completed`, and `failed`.
- Write worker reports under `.dispatch/runs/<run-id>/reports/<agent-id>.json`.
- Validate required worker report fields.
- Emit or reuse lifecycle events for worker spawn, assignment, completion, failure, and protocol violations.
- Keep runtime-generated non-project content under `.dispatch/`.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol
PYTHONPATH=scripts python3 -m unittest discover -s tests
git diff --check
```

Evidence recorded on 2026-05-02:

- `PYTHONPATH=scripts python3 -m unittest tests.test_worker_adapter_protocol` passed, 5 tests.
- `PYTHONPATH=scripts python3 -m unittest discover -s tests` passed, 40 tests.
- `python3 scripts/de.py --help` passed.
- `python3 scripts/de.py version` passed.
- `git diff --check` passed.

## Activity Log

- 2026-05-02 codex: implemented helper-first worker registration, report writing, completion/failure helpers, report validation, focused worker protocol tests, and conservative report-based implementation evidence checks.
