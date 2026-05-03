---
spec_id: rfc-0020-run-cancel-control
workstream_id: 03-docs-heartbeat-validation
language: en-US
audience: agent
doc_type: workstream
status: ready-for-implementation
owner: unassigned
created: 2026-05-03
updated: 2026-05-03
depends_on:
  - 01-cancel-command-runtime
  - 02-state-events-status
---

# Docs Heartbeat Validation

## Scope

Update operator-facing skill/reference guidance after runtime implementation so
interactive Codex knows when and how to call `de cancel`, how to explain
cancelled runs, and when to stop host heartbeat observation.

## Files

- `SKILL.md`
- `README.md`
- `references/heartbeat-observation.md`
- `references/operator-flow.md`
- `references/operator-guide.md`
- `references/event-protocol.md`
- `specs/README.md`
- `specs/rfc-0020-run-cancel-control/STATUS.md`

## Requirements

- Document `de cancel <repo> --run-id <run-id> --reason <text> --json`.
- Document `de stop` as a natural-language alias while keeping `cancel`
  canonical.
- Explain that cancellation is user-requested and distinct from failure.
- Explain that cancellation preserves run evidence.
- Update heartbeat guidance to report terminal cancelled state once and stop
  the heartbeat.
- Update event protocol with cancellation events.
- Update operator guidance to use `events --since`, `alerts --json`, and
  `status --json` after cancellation before summarizing to the user.
- Record validation evidence in `STATUS.md` only after implementation passes.

## Acceptance

1. Skill and README mention `cancel` and the optional `stop` alias.
2. Heartbeat runbook explicitly stops heartbeat after cancelled terminal state.
3. Event protocol lists cancellation event payloads.
4. Operator guidance explains the Codex-facing cancellation workflow.
5. `STATUS.md` remains planned until implementation validation completes, then
   records exact commands and outcomes.

## Validation

```bash
rg "cancel|stop|run.cancel|cancelled|heartbeat" SKILL.md README.md references specs/rfc-0020-run-cancel-control
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py cancel --help
python3 scripts/de.py stop --help
git diff --check
```
