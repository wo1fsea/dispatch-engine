---
spec_id: rfc-0032-validator-artifact-evidence-gate
language: en-US
audience: agent
doc_type: spec
status: ready
implementation: not_started
validation: not_started
issue: https://github.com/wo1fsea/dispatch-engine/issues/27
updated: 2026-05-06
---

# Status

## Summary

Ready for implementation. Existing validator schema diagnostics are close, but
issue #27 needs explicit acceptance gating and regression evidence for
passed validators with missing artifacts.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Validator artifact evidence gate and regression tests | ready |  |  |  | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: triaged issue #27 as current. The runtime can detect
  missing artifacts, but clean acceptance/reporting behavior still needs a
  focused spec and validation.

## Spec Handoff

- Spec path: `specs/rfc-0032-validator-artifact-evidence-gate`
- Status: ready
- Spec type: validator protocol/status/dashboard regression
- Open questions: hard blocker versus visible protocol violation first
- Workstreams: `01-implementation`
- Next owner: implementation agent
- Validation expectation: review-validator/status/dashboard tests
- Ready to implement: yes
