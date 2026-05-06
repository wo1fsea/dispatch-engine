---
spec_id: rfc-0030-repair-worker-report-contract
language: en-US
audience: agent
doc_type: spec
status: ready
implementation: not_started
validation: not_started
issue: https://github.com/wo1fsea/dispatch-engine/issues/25
updated: 2026-05-06
---

# Status

## Summary

Ready for implementation. The spec narrows issue #25 to canonical worker report
requirements for report-repair workers and regression coverage that prevents
repair loops.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Repair worker prompt, diagnostics, and regression tests | ready |  |  |  | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: triaged issue #25 as current enough to require a focused
  spec; existing worker report validation detects malformed output but the
  repair-worker prompt/fixture contract is not explicit enough.

## Spec Handoff

- Spec path: `specs/rfc-0030-repair-worker-report-contract`
- Status: ready
- Spec type: protocol/prompt/runtime regression
- Open questions: possible future `repair` role is non-blocking
- Workstreams: `01-implementation`
- Next owner: implementation agent
- Validation expectation: worker adapter/status tests plus `git diff --check`
- Ready to implement: yes
