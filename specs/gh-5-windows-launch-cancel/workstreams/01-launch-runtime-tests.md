---
spec_id: gh-5-windows-launch-cancel
workstream_id: 01-launch-runtime-tests
language: en-US
audience: agent
doc_type: workstream
status: validated
owner: worker-launch
branch: codex/windows-adaptation-spec
claimed_at: 2026-05-04T00:00:00+08:00
lease_expires_at: 2026-05-04T02:00:00+08:00
created: 2026-05-04
updated: 2026-05-04
depends_on: []
files:
  - scripts/dispatch_engine/coordinators.py
  - tests/test_live_coordinator_supervision.py
  - tests/test_detached_coordinator_supervision.py
  - tests/test_skill_install_e2e.py
---

# Launch Runtime Tests

## Scope

Fix foreground, detached, and copied-skill provider launch behavior on Windows
without changing the public dry-run or live payload command contract.

## Requirements

- Add a failing test or assertion proving live launch uses a resolved
  executable path while returned `argv` remains the rendered provider command.
- Use the resolved executable path in foreground `subprocess.run()`.
- Update fake provider helpers so Windows writes launchable `.cmd` wrappers and
  POSIX keeps executable shebang scripts.
- Preserve existing provider argument assertions.
- Keep dry-run state-write behavior unchanged.

## Acceptance

1. `tests.test_live_coordinator_supervision` passes on Windows.
2. `tests.test_detached_coordinator_supervision` passes on Windows.
3. `tests.test_skill_install_e2e` passes on Windows.
4. Returned live payload still reports `argv[0] == "codex"` or `"claude"`.
5. The provider receives the same argv after `argv[0]` as before.

## Validation

```powershell
$env:PYTHONPATH='scripts'; python -m unittest tests.test_live_coordinator_supervision -v
$env:PYTHONPATH='scripts'; python -m unittest tests.test_detached_coordinator_supervision -v
$env:PYTHONPATH='scripts'; python -m unittest tests.test_skill_install_e2e -v
git diff --check
```

## Activity Log

- 2026-05-04: Claimed by coordinator for worker-launch parallel
  implementation.
- 2026-05-04: Implemented and validated by worker-launch. Main-session review
  added the remaining dogfood fixture fake-provider portability coverage.
