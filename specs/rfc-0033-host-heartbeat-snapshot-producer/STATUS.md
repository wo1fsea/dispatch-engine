---
spec_id: rfc-0033-host-heartbeat-snapshot-producer
language: en-US
audience: agent
doc_type: spec
status: ready-review
implementation: complete
validation: complete
issue: https://github.com/wo1fsea/dispatch-engine/issues/28
updated: 2026-05-06
---

# Status

## Summary

Implementation and assigned validation are complete for the host heartbeat
snapshot producer boundary, including the repair that blocks coordinator
synthetic heartbeat ids from writing real run-scoped snapshots.

## Workstreams

| ID | Scope | Status | Owner | Branch / PR | Depends on | Updated |
|---|---|---|---|---|---|---|
| 01 | Host heartbeat snapshot writer and guidance | validated | worker-001 |  |  | 2026-05-06 |

## Activity Log

- 2026-05-06 codex: confirmed `/api/host-heartbeat` returned
  `source: derived_terminal` with no run-scoped snapshot for dogfood run
  `20260505T182233983007Z`; filed issue #28 and created this spec.
- 2026-05-06 worker-003-host-heartbeat-snapshot: claimed workstream 01 for
  Dispatch Engine run `20260506T044226912184Z`.
- 2026-05-06 worker-003-host-heartbeat-snapshot: completed assigned
  implementation and validation for the run-scoped host heartbeat snapshot
  producer.
- 2026-05-06 worker-001: repaired the producer boundary for Dispatch Engine
  run `20260506T080338588542Z`; `record-host-heartbeat` now rejects reserved
  coordinator-synthetic `codex-thread-heartbeat-*` automation ids and guidance
  reserves real snapshots for the outer interactive Codex host heartbeat.
- 2026-05-06 worker-001: validated dashboard/control-surface tests, CLI help,
  search coverage, and whitespace checks for the boundary repair.
- 2026-05-06 worker-001: added the coordinator prompt contract and dry-run
  regression for Dispatch Engine run `20260506T083353174850Z`, forbidding
  coordinators from calling `record-host-heartbeat` or synthesizing real-run
  heartbeat automation ids.

## Spec Handoff

- Spec path: `specs/rfc-0033-host-heartbeat-snapshot-producer`
- Status: ready-review
- Spec type: Codex-facing CLI/runtime guidance
- Open questions: deriving next wakeup time when host does not provide it
- Workstreams: `01-implementation`
- Next owner: main-session review
- Validation expectation: dashboard/control-surface tests and CLI help
- Ready to implement: yes
