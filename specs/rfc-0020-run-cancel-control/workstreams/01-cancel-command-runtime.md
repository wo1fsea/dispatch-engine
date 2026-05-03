---
spec_id: rfc-0020-run-cancel-control
workstream_id: 01-cancel-command-runtime
language: en-US
audience: agent
doc_type: workstream
status: ready-for-implementation
owner: unassigned
created: 2026-05-03
updated: 2026-05-03
depends_on:
  - rfc-0014-detached-coordinator-supervisor
  - rfc-0015-codex-heartbeat-observation
---

# Cancel Command Runtime

## Scope

Add the Codex-facing runtime command that interactive Codex can call when the
user asks to stop an active detached Dispatch Engine run.

## Files

- `scripts/dispatch_engine/cancel.py`
- `scripts/dispatch_engine/cli.py`
- `scripts/dispatch_engine/supervisor.py`
- Focused tests under `tests/`

## Requirements

- Add canonical `de cancel <repo>`.
- Add `de stop <repo>` as an alias that reuses the same implementation and
  output shape.
- Support `--run-id`, `--reason`, and `--json`.
- Resolve latest run when `--run-id` is omitted.
- Return clear JSON errors for no run, missing selected run, completed/failed
  terminal runs, and malformed state.
- Treat already-cancelled runs as idempotent success.
- Discover active supervisor/coordinator process state from run-scoped
  `.dispatch/` files.
- Gracefully terminate live process state first, then escalate after a bounded
  grace period if still alive.
- Do not require live pids for durable cancellation; missing pids should be
  reported in the payload.
- Never delete logs, prompts, reports, reviews, validation, events, or
  heartbeat records.

## Acceptance

1. `python3 scripts/de.py cancel <repo> --json` returns `kind: "run_cancel"`.
2. Explicit `--run-id` selects the requested run and refuses unknown run ids.
3. `--reason` is preserved exactly in returned JSON and later state updates.
4. `de stop` returns the same payload shape as `de cancel`.
5. Tests prove graceful signal, escalation, no-pid, and already-cancelled
   behavior.

## Validation

```bash
PYTHONPATH=scripts python3 -m unittest tests.test_run_cancel_control
python3 scripts/de.py cancel --help
python3 scripts/de.py stop --help
git diff --check
```
