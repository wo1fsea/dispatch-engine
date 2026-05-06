---
spec_id: rfc-0031-issue-evidence-capability-preflight
language: en-US
audience: agent
doc_type: spec
status: ready-review
implementation: complete
validation: complete
issue: https://github.com/wo1fsea/dispatch-engine/issues/26
updated: 2026-05-06
---

# Status

## Summary

Implementation is validated and ready for review. Dispatch plans now warn when
GitHub issue evidence appears to need network access denied by the worker
capability profile, and guidance requires an explicit read grant, local-only
evidence strategy, or blocker before dispatch.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Issue-evidence capability warning and guidance | validated | worker-002-issue-evidence-preflight |  |  | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: triaged issue #26 as still current. The previous
  validation-warning work is adjacent but does not cover issue-evidence scope
  that requires `gh issue view`.
- 2026-05-06 worker-002-issue-evidence-preflight: implemented and validated
  warning-only preflight diagnostics with focused unit tests, prompt guidance,
  grep coverage, and whitespace validation.

## Spec Handoff

- Spec path: `specs/rfc-0031-issue-evidence-capability-preflight`
- Status: ready-review
- Spec type: plan diagnostic / prompt guidance
- Open questions: GitHub-specific first versus generic external tracker
- Workstreams: `01-implementation`
- Next owner: main-session review
- Validation expectation: plan schema and capability-profile tests
- Ready to implement: yes
