---
workstream_id: 01-live-launch-process-supervision
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: Worker A
branch: main
updated: 2026-05-02
depends_on: []
claimed_at: 2026-05-02T01:23:01Z
lease_expires_at: 2026-05-02T03:23:01Z
---

# Live Launch Process Supervision

## Scope

Implement foreground live provider coordinator process launch for `de run` without `--dry-run`.

## Files

- `scripts/dispatch_engine/coordinators.py`
- `scripts/dispatch_engine/cli.py`
- `scripts/dispatch_engine/agents.py`
- `scripts/dispatch_engine/events.py`
- `scripts/dispatch_engine/runs.py`
- `tests/test_live_coordinator_supervision.py`

## Requirements

- Preserve existing `--dry-run` behavior.
- Launch Codex by default when provider is omitted.
- Launch explicit `--provider codex`.
- Launch explicit `--provider claude`.
- Write prompt snapshots under `.dispatch/runs/<run-id>/prompts/`.
- Capture stdout/stderr under `.dispatch/runs/<run-id>/logs/`.
- Register `coordinator-001` before launch.
- Emit `coordinator.started`.
- Mark coordinator completed/failed and emit matching events based on process exit code.
- Use fake provider executables in tests instead of real Codex or Claude.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_live_coordinator_supervision
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py --help
git diff --check
```

Evidence recorded by Worker A on 2026-05-02:

- `PYTHONPATH=scripts python3 -m unittest tests.test_live_coordinator_supervision` passed, 4 tests.
- `PYTHONPATH=scripts python3 -m unittest discover -s tests` passed, 35 tests.
- `python3 scripts/de.py --help` passed and printed CLI help.
- `git diff --check` passed.

## Activity Log

- 2026-05-02 Worker A: claimed workstream and added red live-supervision tests for fake provider launch, logs, prompt snapshots, agent state, events, and CLI JSON output.
- 2026-05-02 Worker A: implemented foreground live coordinator launch for Codex and Claude, including prompt snapshots, log capture, coordinator registry updates, lifecycle events, CLI payloads, and fake-provider tests.
- 2026-05-02 Worker A: validated workstream with narrow live-supervision tests, full unittest discovery, CLI help smoke test, and whitespace diff check.
