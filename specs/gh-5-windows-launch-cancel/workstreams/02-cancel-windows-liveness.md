---
spec_id: gh-5-windows-launch-cancel
workstream_id: 02-cancel-windows-liveness
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-cancel
branch: codex/windows-adaptation-spec
claimed_at: 2026-05-04T00:00:00+08:00
lease_expires_at: 2026-05-04T02:00:00+08:00
created: 2026-05-04
updated: 2026-05-04
depends_on: []
files:
  - scripts/dispatch_engine/cancel.py
  - tests/test_run_cancel_control.py
---

# Cancel Windows Liveness

## Scope

Harden cancellation when Windows reports stale or invalid process state during
process liveness checks.

## Requirements

- Add a failing regression test for Windows-style stale PID handling. The test
  should prove cancellation succeeds and records `final_state: "not_running"`
  when the process controller reports the process is not alive after a Windows
  liveness error.
- Harden `DefaultProcessController.is_alive()` so `SystemError` from
  `os.kill(pid, 0)` is treated as not running.
- Do not hide permission errors as successful cancellation.
- Preserve existing graceful and escalation signal behavior.

## Acceptance

1. `tests.test_run_cancel_control` includes Windows stale PID coverage.
2. `DefaultProcessController.is_alive()` no longer lets the observed Windows
   `SystemError` crash `de cancel`.
3. Existing cancel behavior and payload shapes remain stable.

## Validation

```powershell
$env:PYTHONPATH='scripts'; python -m unittest tests.test_run_cancel_control -v
git diff --check
```

## Activity Log

- 2026-05-04: Claimed by coordinator for worker-cancel parallel
  implementation.
- 2026-05-04: Implemented and validated by worker-cancel. Main-session review
  confirmed the fix stays scoped to stale Windows liveness `SystemError`
  handling.
