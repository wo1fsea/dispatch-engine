---
spec_id: rfc-0027-dashboard-observer-lifecycle
language: en-US
audience: agent
doc_type: spec
status: ready-review
implementation: complete
validation: complete
issue: https://github.com/wo1fsea/dispatch-engine/issues/23
updated: 2026-05-06
---

# Status

## Summary

Skill and operator-guidance implementation is complete. The docs now define
dashboard observer lifecycle for detached, terminal, cancelled, and superseded
runs while keeping host heartbeat as the mandatory wakeup mechanism. No runtime
metadata was added because existing `de dashboard --run-id`, `dashboard
--status --json`, and `.dispatch/runs/<run-id>/dashboard/server.json` metadata
are sufficient for the current operator contract.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Skill/operator dashboard lifecycle guidance | validated | worker-002 |  |  | 2026-05-06 |
| 02 | Runtime observer metadata, only if necessary | validated | worker-002 |  | 01 | 2026-05-06 |
| 03 | Validation and dogfood evidence | validated | worker-006 |  | 01, 02 | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: inspected issue #23 and confirmed the stale-dashboard
  lifecycle gap is real for cancelled/superseded dogfood runs.
- 2026-05-06 worker-002: implemented docs-only dashboard observer lifecycle
  guidance across the skill, README, operator flow, operator guide, and
  heartbeat guide; runtime metadata was not needed.
- 2026-05-06 worker-002: validated with the required docs grep and
  `git diff --check`.
- 2026-05-06 worker-006: validated the integrated issue #23 documentation with
  the full required command suite.

## Spec Handoff

- Spec path: `specs/rfc-0027-dashboard-observer-lifecycle`
- Ready to review: yes
- Validation expectation: docs grep; focused dashboard tests if runtime support
  is added.
