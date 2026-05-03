---
spec_id: rfc-0020-run-cancel-control
language: en-US
audience: mixed
doc_type: spec
status: planned
created: 2026-05-03
updated: 2026-05-03
issue: https://github.com/wo1fsea/dispatch-engine/issues/3
---

# Run Cancel Control Product Spec

## Summary

Dispatch Engine can launch detached runs, expose status/events/alerts, observe
heartbeats, and represent terminal cancelled states, but interactive Codex has
no first-class command for user-requested stop/cancel. Operators need a stable
Codex-facing control that can cancel an active detached run, update durable
state, and tell the host heartbeat to shut down once cancellation is visible.

## Goals / Non-goals

- Goal: Add `de cancel <repo>` as the canonical Codex-facing command for
  user-requested run cancellation.
- Goal: Support `--run-id`, `--reason`, `--json`, and a `de stop <repo>` alias.
- Goal: Resolve the latest run by default and reject ambiguous or terminal
  cancellation targets clearly.
- Goal: Find active supervisor/coordinator process state, terminate gracefully,
  escalate if needed, and record the final process outcome.
- Goal: Mark the run, coordinator, supervisor, and active workers/reviewers/
  validators `cancelled` with a durable user-supplied or default reason.
- Goal: Emit append-only cancellation lifecycle events and make `status --json`
  report terminal `cancelled` state.
- Goal: Update heartbeat guidance so interactive Codex stops the host heartbeat
  after a cancelled run is reported.
- Non-goal: Add a long-running daemon, dashboard, scheduler, pause/resume, or
  restart manager.
- Non-goal: Force provider-specific worker cancellation APIs into Dispatch
  Engine before they are represented in durable agent state.
- Non-goal: Delete logs, prompts, reports, or other run evidence during cancel.
- Non-goal: Treat cancellation as failure; cancelled is its own terminal state.

## User Outcome

When the user asks interactive Codex to stop a detached Dispatch Engine run,
Codex can call:

```bash
python3 scripts/de.py cancel <repo> --run-id <run-id> --reason "User asked to stop" --json
```

Dispatch Engine records a durable terminal `cancelled` state, attempts to stop
the active supervisor/coordinator process, updates active agents with the same
reason, emits events, and returns JSON that Codex can summarize. The heartbeat
then reports the terminal cancelled state once and stops itself.

## Behavior Invariants

1. `cancel` is idempotent for already-cancelled runs and returns terminal state
   evidence rather than re-sending process signals.
2. `stop` is an alias for `cancel`; docs may mention it for natural language,
   but `cancel` remains canonical.
3. A run with status `completed`, `failed`, or `cancelled` is terminal.
4. Cancellation preserves all run evidence and never deletes `.dispatch/`
   files.
5. Missing process state does not block durable cancellation. The command
   records that no live process could be signalled and still marks active state
   cancelled.
6. Process signalling is best-effort and observable: graceful signal attempted
   first, escalation attempted only when the process remains alive after the
   grace period.
7. The cancellation reason is recorded in every updated run, supervisor, and
   active agent record.
8. `status --json` exposes `run_status: "cancelled"` and enough cancellation
   metadata for heartbeat shutdown and final user reporting.

## Acceptance

1. `python3 scripts/de.py cancel <repo> --json` cancels the latest active run.
2. `python3 scripts/de.py cancel <repo> --run-id <run-id> --reason <text> --json`
   cancels a selected run and records the reason.
3. `python3 scripts/de.py stop <repo> ...` behaves exactly like `cancel`.
4. Cancellation updates run, supervisor, coordinator, and active agent state to
   `cancelled` while preserving completed, failed, and already-cancelled agent
   records.
5. Cancellation emits durable events for requested, signal/escalation outcome,
   and completed cancellation.
6. `status --json`, `events --since --json`, and `alerts --json` expose the
   terminal cancelled state and cancellation reason.
7. Heartbeat guidance says to report the cancelled terminal state once and stop
   the host heartbeat.
8. Focused tests cover latest-run resolution, explicit `--run-id`,
   idempotency, missing process state, graceful termination, escalation, JSON
   output, and alias behavior.
