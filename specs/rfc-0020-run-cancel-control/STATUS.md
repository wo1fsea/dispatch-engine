---
spec_id: rfc-0020-run-cancel-control
language: en-US
audience: agent
doc_type: status
status: implemented
implementation: complete
validation: passed
coordinator: dispatch-engine
created: 2026-05-03
updated: 2026-05-03
issue: https://github.com/wo1fsea/dispatch-engine/issues/3
---

# Status

## Summary

Implemented. Dispatch Engine now has the first-class Codex-facing cancellation
control for detached runs: `de cancel <repo>` with `--run-id`, `--reason`,
`--json`, and `de stop` as an alias. The runtime resolves the latest or
selected run, records durable terminal cancellation, attempts graceful
supervisor/coordinator process signalling before escalation, marks active
run/supervisor/agent state cancelled with a reason, emits cancellation events,
exposes cancelled status in JSON, and documents heartbeat shutdown.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01-cancel-command-runtime | CLI command, alias, run resolution, and process signalling | complete | codex | local | rfc-0014, rfc-0015 | 2026-05-03 |
| 02-state-events-status | Durable cancelled state, event vocabulary, status/events/alerts JSON | complete | codex | local | 01-cancel-command-runtime | 2026-05-03 |
| 03-docs-heartbeat-validation | Skill/reference docs, heartbeat shutdown guidance, validation and dogfood | complete | codex | local | 01-cancel-command-runtime, 02-state-events-status | 2026-05-03 |

## Acceptance Criteria

1. `de cancel <repo> --json` cancels the latest active run.
2. `de cancel <repo> --run-id <run-id> --reason <text> --json` cancels a
   selected run and records the reason.
3. `de stop <repo>` is an alias for `de cancel <repo>`.
4. Cancellation attempts graceful process termination and escalates only when
   the process remains live after the bounded grace period.
5. Missing supervisor or process pid state is recorded but does not prevent
   durable cancellation.
6. Run, supervisor, coordinator, and active agents become terminal
   `cancelled`; already-terminal completed/failed/cancelled agents are
   preserved.
7. `events --since --json` exposes cancellation lifecycle events.
8. `status --json` exposes terminal `run_status: "cancelled"`, cancellation
   reason, cancellation timestamp, cancelled supervisor counts, and cancelled
   agent counts.
9. `alerts --json` exposes cancellation as a material terminal alert.
10. Heartbeat docs instruct Codex to report cancelled state once and stop the
    host heartbeat.

## Validation Plan

- `PYTHONPATH=scripts python3 -m unittest tests.test_run_cancel_control`
- `PYTHONPATH=scripts python3 -m unittest discover -s tests`
- `python3 scripts/de.py cancel --help`
- `python3 scripts/de.py stop --help`
- `python3 scripts/de.py status --help`
- `python3 scripts/de.py events --help`
- `python3 scripts/de.py alerts --help`
- `rg "cancel|stop|run.cancel|cancelled|heartbeat" SKILL.md README.md references specs/rfc-0020-run-cancel-control`
- `git diff --check`

## Validation Evidence

- `PYTHONPATH=scripts python3 -m unittest tests.test_run_cancel_control`: passed, 5 tests.
- `PYTHONPATH=scripts python3 -m unittest discover -s tests`: passed, 71 tests.
- `python3 scripts/de.py cancel --help`: passed.
- `python3 scripts/de.py stop --help`: passed.
- `python3 scripts/de.py status --help`: passed.
- `python3 scripts/de.py events --help`: passed.
- `python3 scripts/de.py alerts --help`: passed.
- `rg "cancel|stop|run.cancel|cancelled|heartbeat" SKILL.md README.md references specs/rfc-0020-run-cancel-control`: passed.
- `git diff --check`: passed.

## Activity Log

- 2026-05-03: Created planned RFC from GitHub issue #3 context. Scoped to spec
  files only; runtime and broader docs are intentionally untouched.
- 2026-05-03: Implemented RFC-0020 runtime, state/event/status surfaces, tests,
  and operator/heartbeat docs. Validation passed with the commands listed
  above.
