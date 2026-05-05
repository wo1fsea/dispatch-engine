---
spec_id: rfc-0029-validation-worker-stall-terminalization
language: en-US
audience: agent
doc_type: spec
status: ready
implementation: not_started
validation: not_started
issue: https://github.com/wo1fsea/dispatch-engine/issues/20
updated: 2026-05-06
---

# Status

## Summary

Ready. Created from issue #20 after dogfood showed a validation worker could
remain running without a terminal report, leaving interactive Codex to notice
and recover manually.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Validation worker stale lifecycle diagnostics | ready |  |  |  | 2026-05-06 |
| 02 | Validator/coordinator report guidance | ready |  |  | 01 | 2026-05-06 |
| 03 | Dashboard/status validation evidence | ready |  |  | 01, 02 | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: inspected issue #20 and confirmed current cancelled-run
  status no longer preserves enough evidence about the original running
  validation worker.

## Spec Handoff

- Spec path: `specs/rfc-0029-validation-worker-stall-terminalization`
- Ready to implement: yes
- Validation expectation: lifecycle/status/dashboard tests and full unittest
  discovery.
