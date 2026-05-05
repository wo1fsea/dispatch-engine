---
spec_id: rfc-0027-dashboard-observer-lifecycle
language: en-US
audience: agent
doc_type: spec
status: ready
implementation: not_started
validation: not_started
issue: https://github.com/wo1fsea/dispatch-engine/issues/23
updated: 2026-05-06
---

# Status

## Summary

Ready. Created from issue #23 after dogfood showed that cancelled and
superseded runs can leave the operator looking at a stale dashboard.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Skill/operator dashboard lifecycle guidance | ready |  |  |  | 2026-05-06 |
| 02 | Runtime observer metadata, only if necessary | ready |  |  | 01 | 2026-05-06 |
| 03 | Validation and dogfood evidence | ready |  |  | 01, 02 | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: inspected issue #23 and confirmed the stale-dashboard
  lifecycle gap is real for cancelled/superseded dogfood runs.

## Spec Handoff

- Spec path: `specs/rfc-0027-dashboard-observer-lifecycle`
- Ready to implement: yes
- Validation expectation: docs grep; focused dashboard tests if runtime support
  is added.
