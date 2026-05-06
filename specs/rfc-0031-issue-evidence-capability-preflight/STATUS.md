---
spec_id: rfc-0031-issue-evidence-capability-preflight
language: en-US
audience: agent
doc_type: spec
status: ready
implementation: not_started
validation: not_started
issue: https://github.com/wo1fsea/dispatch-engine/issues/26
updated: 2026-05-06
---

# Status

## Summary

Ready for implementation. Current code warns when validation commands appear
to require network access, but issue #26 needs a broader preflight for
GitHub-issue evidence workstreams.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Issue-evidence capability warning and guidance | ready |  |  |  | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: triaged issue #26 as still current. The previous
  validation-warning work is adjacent but does not cover issue-evidence scope
  that requires `gh issue view`.

## Spec Handoff

- Spec path: `specs/rfc-0031-issue-evidence-capability-preflight`
- Status: ready
- Spec type: plan diagnostic / prompt guidance
- Open questions: GitHub-specific first versus generic external tracker
- Workstreams: `01-implementation`
- Next owner: implementation agent
- Validation expectation: plan schema and capability-profile tests
- Ready to implement: yes
