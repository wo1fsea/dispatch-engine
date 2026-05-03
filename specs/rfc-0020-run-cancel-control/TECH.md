---
spec_id: rfc-0020-run-cancel-control
language: en-US
audience: agent
doc_type: spec
status: planned
created: 2026-05-03
updated: 2026-05-03
issue: https://github.com/wo1fsea/dispatch-engine/issues/3
---

# Run Cancel Control Tech Spec

## Design Boundary

Cancellation is a runtime control surface because it must be durable,
queryable, resumable, and reflected through `de status`, `de events`, and
`.dispatch/` files. Interactive Codex owns the conversation with the user and
decides when to request cancellation. Dispatch Engine owns the mechanical
state transition and process signalling once Codex calls `de cancel`.

The host heartbeat remains outside the runtime. Runtime cancellation makes a
run terminal; the heartbeat must detect that terminal state and stop itself.

## CLI Contract

Add `de cancel <repo>` as the canonical command and `de stop <repo>` as its
alias. In the bundled runtime entrypoint, those resolve to:

```bash
python3 scripts/de.py cancel <repo> [--run-id <run-id>] [--reason <text>] [--json]
python3 scripts/de.py stop <repo> [--run-id <run-id>] [--reason <text>] [--json]
```

Defaults:

- `--run-id` omitted means the latest run under `.dispatch/runs/`.
- `--reason` omitted means `User requested cancellation.`
- `--json` follows the existing Codex-facing JSON contract.

Machine-readable success payload:

```json
{
  "kind": "run_cancel",
  "status": "cancelled",
  "run_id": "20260503T000000000000Z",
  "state_dir": "/repo/.dispatch/runs/20260503T000000000000Z",
  "reason": "User asked to stop.",
  "already_terminal": false,
  "signals": [
    {
      "target": "supervisor",
      "agent_id": "coordinator-001",
      "pid": 12345,
      "graceful_signal": "SIGTERM",
      "graceful_sent": true,
      "escalated": false,
      "final_state": "terminated"
    }
  ],
  "updated_agents": ["coordinator-001", "worker-001"],
  "events": ["run.cancel.requested", "run.cancel.completed"]
}
```

Errors should use the existing `kind: "error"` shape:

- `status: "missing_run"` when `--run-id` does not exist.
- `status: "no_run"` when there is no latest run.
- `status: "run_already_terminal"` only for completed or failed runs unless
  idempotent cancellation of an already-cancelled run returns success.
- `status: "cancel_state_error"` when state files are malformed and cannot be
  safely updated.

## Runtime Modules

Expected implementation surface:

- `scripts/dispatch_engine/cancel.py`: cancellation orchestration, run
  resolution, state updates, process signalling, and JSON payload assembly.
- `scripts/dispatch_engine/cli.py`: parser entries for `cancel` and `stop`.
- `scripts/dispatch_engine/events.py`: helper functions for cancellation event
  types.
- `scripts/dispatch_engine/state.py`: status/alerts exposure for cancelled run
  metadata where needed.
- `scripts/dispatch_engine/agents.py` and `supervisor.py`: narrow helpers if
  needed to update active agent or supervisor records consistently.
- Focused tests under `tests/`, likely `tests.test_run_cancel_control`.

## Run Resolution

The command uses the same run resolution rules as `status` and `run`:

1. Resolve target repo with `Path(target).resolve()`.
2. If `--run-id` is supplied, resolve that exact run directory.
3. Otherwise, select the latest run directory.
4. Read `run.json`; malformed or missing `run.json` is an error unless the
   implementation can still write a safe cancellation record without losing
   evidence.

Terminal statuses are:

```text
completed
failed
cancelled
```

`cancel` should be idempotent when `run.json` already has
`status: "cancelled"`. For `completed` and `failed`, return a clear terminal
error because no cancellation action is possible.

## Process Discovery And Signalling

Process state is discovered from run-scoped files, not from a global daemon:

```text
.dispatch/runs/<run-id>/supervisors/coordinator-001.json
.dispatch/runs/<run-id>/agents/coordinator-001.json
.dispatch/runs/<run-id>/agents/*.json
```

The first supported target is the detached supervisor process because it owns
the foreground provider coordinator. If an agent record has a live `pid`, it
may also be signalled, but missing pids must not prevent durable cancellation.

Recommended sequence:

1. Emit `run.cancel.requested` with actor `interactive-codex`, run id, and
   reason.
2. Read supervisor record and active agent records.
3. Send graceful termination to live supervisor/coordinator pids.
4. Wait a short bounded grace period.
5. If a process is still alive, send escalation signal.
6. Record signal outcome in supervisor state and command JSON.
7. Mark run, supervisor, coordinator, and active agents cancelled.
8. Emit `run.cancel.completed`.

Signal names should be platform-aware. On POSIX, graceful is `SIGTERM` and
escalation is `SIGKILL`. On platforms without POSIX signals, use the closest
standard process termination primitive and record the method by name.

## State Updates

`run.json` should gain cancellation fields:

```json
{
  "status": "cancelled",
  "cancelled_at": "2026-05-03T00:00:00Z",
  "cancelled_by": "interactive-codex",
  "cancellation_reason": "User asked to stop."
}
```

Supervisor records should be updated when present:

```json
{
  "status": "cancelled",
  "updated_at": "2026-05-03T00:00:00Z",
  "completed_at": "2026-05-03T00:00:00Z",
  "cancellation_reason": "User asked to stop.",
  "cancel_signal": {
    "graceful_signal": "SIGTERM",
    "graceful_sent": true,
    "escalation_signal": null,
    "escalated": false,
    "final_state": "terminated"
  }
}
```

Active agent records should be updated to:

```json
{
  "status": "cancelled",
  "updated_at": "2026-05-03T00:00:00Z",
  "completed_at": "2026-05-03T00:00:00Z",
  "cancellation_reason": "User asked to stop."
}
```

Only active agents are changed. Agents already in `completed`, `failed`, or
`cancelled` keep their terminal status and evidence.

## Events

Add cancellation events to the append-only event log:

`run.cancel.requested`

- Written before signalling or state mutation.
- Payload includes `run_id`, `reason`, `requested_by`, and optional selected
  `run_id` source such as `latest` or `explicit`.

`run.cancel.signal`

- Written for each process signal attempt.
- Payload includes `target`, `agent_id`, `pid`, signal name, whether it was
  sent, escalation flag, and outcome.

`run.cancel.completed`

- Written after durable state is terminal.
- Payload includes `run_id`, `reason`, updated agent ids, signal summary, and
  `already_cancelled` when the command was idempotent.

Optional future event:

`run.cancel.failed`

- Reserved for malformed state or process-control errors that prevent durable
  cancellation from being recorded.

## Status, Alerts, And Heartbeat

`status --json` should expose:

- `run_status: "cancelled"`
- cancellation reason and timestamp
- supervisor count with `cancelled`
- agent count with `cancelled`
- no misleading next action to continue work

`alerts --json` should include a material terminal alert for cancellation until
the heartbeat reports it. `events --since --json` should include the new
cancellation events with generated event ids.

Heartbeat guidance should say:

1. If `status --json` reports `run_status: "cancelled"`, report the reason once.
2. Read `events --since` to include cancellation events when available.
3. Stop the host heartbeat after reporting the terminal cancelled state.

## Implementation Tasks

1. Add cancellation event helpers and tests for event shape.
2. Add `cancel.py` with latest/specified run resolution and state mutation.
3. Add process signalling with graceful and escalation paths.
4. Wire `cancel` and `stop` into the CLI with JSON output.
5. Update status/alerts to surface cancellation metadata and terminal state.
6. Update skill/reference docs and heartbeat guidance in a later docs lane.
7. Validate with focused unit tests, full unittest discovery, CLI help, and
   grep checks for documented command names.

## Validation

Focused implementation:

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_run_cancel_control
python3 scripts/de.py cancel --help
python3 scripts/de.py stop --help
```

Full runtime confidence:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s tests
python3 scripts/de.py status --help
python3 scripts/de.py events --help
python3 scripts/de.py alerts --help
git diff --check
```

Docs-lane checks:

```bash
rg "cancel|stop|run.cancel|cancelled|heartbeat" SKILL.md README.md references specs/rfc-0020-run-cancel-control
```
