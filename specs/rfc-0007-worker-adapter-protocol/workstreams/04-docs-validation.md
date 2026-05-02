---
workstream_id: 04-docs-validation
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: codex
branch: main
updated: 2026-05-02
depends_on:
  - 01-worker-state-report-protocol
  - 02-worker-prompt-template
  - 03-status-violations
---

# Docs And Validation

## Scope

Update operator and protocol documentation for the worker adapter baseline and record validation evidence.

## Files

- `README.md`
- `SKILL.md`
- `references/worker-protocol.md`
- `references/event-protocol.md`
- `references/orchestrator-loop.md`
- `specs/rfc-0007-worker-adapter-protocol/STATUS.md`
- `specs/README.md`

## Requirements

- Document worker registration, worker prompt snapshots, logs, reports, and heartbeat paths.
- Update `references/worker-protocol.md` so coordinator launch no longer says dry-run-only.
- Document that worker output is not valid without registration and a durable report.
- Document conservative protocol violations.
- Mark rfc-0007 ready-review or validated only after tests and docs checks pass.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py --help
python3 scripts/de.py version
rg "worker|worker-protocol|agent.spawned|workstream.assigned|protocol.violation|reports/" README.md SKILL.md references specs/rfc-0007-worker-adapter-protocol
git diff --check
```

Evidence recorded on 2026-05-02:

- Updated README, SKILL, worker protocol, event protocol, orchestrator loop, and spec index documentation for worker registration, prompt snapshots, logs, reports, heartbeat paths, durable report requirements, and conservative worker report violations.
- Updated `references/worker-protocol.md` so coordinator launch documents live foreground execution as well as dry-run rendering.
- Validation passed with focused worker adapter tests, full unittest discovery, CLI help/version smoke checks, documentation `rg`, and `git diff --check`.
