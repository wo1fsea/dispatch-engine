---
spec_id: rfc-0033-host-heartbeat-snapshot-producer
language: en-US
audience: agent
doc_type: spec
status: ready
implementation: not_started
validation: not_started
issue: https://github.com/wo1fsea/dispatch-engine/issues/28
updated: 2026-05-06
---

# Status

## Summary

Ready for implementation. The dashboard read side exists, but the host
heartbeat snapshot producer does not.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Host heartbeat snapshot writer and guidance | ready |  |  |  | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: confirmed `/api/host-heartbeat` returned
  `source: derived_terminal` with no run-scoped snapshot for dogfood run
  `20260505T182233983007Z`; filed issue #28 and created this spec.

## Spec Handoff

- Spec path: `specs/rfc-0033-host-heartbeat-snapshot-producer`
- Status: ready
- Spec type: Codex-facing CLI/runtime guidance
- Open questions: deriving next wakeup time when host does not provide it
- Workstreams: `01-implementation`
- Next owner: implementation agent
- Validation expectation: dashboard/control-surface tests and CLI help
- Ready to implement: yes
