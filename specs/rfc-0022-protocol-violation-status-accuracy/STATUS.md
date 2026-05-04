---
spec_id: rfc-0022-protocol-violation-status-accuracy
language: en-US
audience: agent
doc_type: spec
status: done
implementation: complete
validation: complete
issue: https://github.com/wo1fsea/dispatch-engine/issues/16
updated: 2026-05-04
---

# Status

## Summary

Done. Implementation, validation, and main-session review are complete. This
spec captures the current, corrected scope of #16 after dogfood issue triage:
misleading completion and historical event diagnostics, not the now-clean
worker-004 capability report.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Detected completion violation accuracy | merged | worker-b | main |  | 2026-05-04 |
| 02 | Event violation normalization and docs | merged | worker-b | main |  | 2026-05-04 |

## Activity Log

- 2026-05-04 codex: created spec from issue triage for the current scope of #16.
- 2026-05-04 worker-b: claimed workstreams 01 and 02; implementation active.
- 2026-05-04 worker-b: red tests added for rfc-0022 completion and event-normalization regressions.
- 2026-05-04 worker-b: implementation and validation complete; focused/full unit tests, CLI help, diff check, and dogfood status/alerts passed.
- 2026-05-04 codex: reviewed Worker B output, reran focused/full tests, CLI smoke, diff check, and dogfood status/alerts; accepted the implementation.

## Spec Handoff

- Spec path: `specs/rfc-0022-protocol-violation-status-accuracy`
- Status: done
- Spec type: compact runtime/status bugfix
- Open questions: whether run/workstream aggregate mismatch belongs here
- Workstreams: `01-completion-accuracy`, `02-event-normalization-docs`
- Next owner: none
- Validation expectation: focused protocol/status tests, full unittest
  discovery, CLI smoke, dogfood status/alerts
- Ready to implement: complete
