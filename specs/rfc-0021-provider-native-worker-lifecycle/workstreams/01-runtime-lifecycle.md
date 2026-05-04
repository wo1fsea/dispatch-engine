---
workstream_id: 01-runtime-lifecycle
status: merged
owner: Worker A
branch: local
claimed_at: 2026-05-04
updated: 2026-05-04
---

# Runtime Lifecycle Diagnostics

## Scope

Implement provider-native launch evidence normalization and active
provider-native no-report lifecycle diagnostics.

## Files

- `scripts/dispatch_engine/state.py`
- `tests/test_status_tail.py`

## Acceptance

- Nested provider spawn evidence prevents false `missing_agent_launch_evidence`.
- Placeholder stdout/stderr paths without files do not count as launch evidence.
- Active provider-native agents without reports produce a targeted lifecycle
  diagnostic and alert after the chosen staleness threshold.
- Focused tests pass.

## Activity Log

- 2026-05-04 codex: workstream created.
- 2026-05-04 Worker A: claimed runtime lifecycle implementation and focused tests.
- 2026-05-04 Worker A: added focused lifecycle tests, observed red failures for ignored provider-native fields and missing no-report diagnostic, implemented launch evidence normalization and stale provider-native no-report diagnostics, and validated focused plus full unittest suites.
- 2026-05-04 codex: reviewed, reran validation, and accepted into main.
