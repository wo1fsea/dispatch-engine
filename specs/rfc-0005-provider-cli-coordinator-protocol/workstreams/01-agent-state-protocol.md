---
workstream_id: 01-agent-state-protocol
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: Worker A
branch: main
updated: 2026-05-02
depends_on: []
---

# Agent State Protocol

## Scope

Define and implement durable agent registry state for coordinators, workers, reviewers, and validators.

## Files

- `scripts/dispatch_engine/runs.py`
- `scripts/dispatch_engine/events.py`
- optional new module: `scripts/dispatch_engine/agents.py`
- `references/event-protocol.md`
- `tests/`

## Requirements

- Create `.dispatch/runs/<run-id>/agents/`, `reports/`, `logs/`, and `heartbeats/` for new runs.
- Preserve compatibility with legacy runs that do not yet have those directories.
- Add agent registry records with `agent_id`, `role`, `provider`, `profile`, `status`, `workstream`, file scope, timestamps, heartbeat, report path, and log path.
- Support coordinator provider values `codex` and `claude`; default provider selection is handled by the run launcher.
- Enforce role vocabulary: `coordinator`, `worker`, `reviewer`, `validator`.
- Record coordinator-only allowed writes as `.dispatch/`.
- Add event writers for `coordinator.started`, `agent.spawned`, `agent.heartbeat`, `workstream.assigned`, `agent.completed`, `agent.failed`, `protocol.violation`, and `decision.requested`.
- Add conservative protocol violation checks for coordinator project-file scope and unregistered implementation completion.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
git diff --check
```

## Activity Log

- 2026-05-02 Worker S: initialized workstream as ready.
- 2026-05-02 Worker A: claimed and implemented durable agent registry helpers in `scripts/dispatch_engine/agents.py`, new run supervision directories in `runs.py`, and state-protocol event helper writers in `events.py`.
- 2026-05-02 Worker A: validated with `PYTHONPATH=scripts python3 -m unittest discover -s tests` and `git diff --check`.
