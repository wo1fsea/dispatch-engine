---
spec_id: rfc-0030-repair-worker-report-contract
language: en-US
audience: agent
doc_type: spec
status: ready-review
implementation: complete
validation: complete
issue: https://github.com/wo1fsea/dispatch-engine/issues/25
updated: 2026-05-06
---

# Status

## Summary

Implementation and assigned validation are complete for workstream 01. The
spec narrows issue #25 to canonical worker report requirements for
report-repair workers and regression coverage that prevents repair loops.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Repair worker prompt, diagnostics, and regression tests | validated | worker-001-repair-report-contract |  |  | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: triaged issue #25 as current enough to require a focused
  spec; existing worker report validation detects malformed output but the
  repair-worker prompt/fixture contract is not explicit enough.
- 2026-05-06 worker-001-repair-report-contract: claimed workstream 01 and
  started TDD implementation.
- 2026-05-06 worker-001-repair-report-contract: completed repair-worker prompt,
  runtime next-action, and regression-test changes; assigned validation passed.

## Spec Handoff

- Spec path: `specs/rfc-0030-repair-worker-report-contract`
- Status: ready-review
- Spec type: protocol/prompt/runtime regression
- Open questions: possible future `repair` role is non-blocking
- Workstreams: `01-implementation`
- Next owner: main-session review
- Validation expectation: worker adapter/status tests plus `git diff --check`
- Ready to implement: yes
